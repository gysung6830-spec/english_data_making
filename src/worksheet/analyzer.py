"""구문 분석기 (명세서 §5-3, §6).

하이브리드: 규칙기반 1차(관계사/수동태/분사/to-v/수일치)로 힌트 초안을 만들고,
LLM 이 성분 라벨·주석·오답형을 보정한다.

- analyze_sentence()      : LLM 로 문장 1개를 태깅 → models.Sentence
- rule_hints()            : 규칙기반으로 잡아낸 문법 힌트(프롬프트 주입용)
- rule_only_sentence()    : API 없이 규칙기반 초안만으로 Sentence 구성(오프라인/미리보기)
"""
from __future__ import annotations

import re

from ..client import ClaudeClient
from .llm_schemas import SentenceAnalysis
from .models import Sentence, Token

# 태깅 강도
STRENGTH_FULL = "full"     # 전체
STRENGTH_KEY = "key"       # 핵심만
STRENGTH_NONE = "none"     # 없음 (원문 + 해석만)


# ---------------------------------------------------------------------------
# 규칙기반 힌트 (명세서 §6 표)
# ---------------------------------------------------------------------------
_REL_PRONOUNS = {"who", "whom", "whose", "which", "that", "where", "when", "why"}
_BE = {"is", "are", "was", "were", "be", "been", "being", "am"}
_MODALS = {"will", "would", "can", "could", "shall", "should", "may", "might", "must"}
_TO_V = re.compile(r"\bto\s+[a-z]+", re.IGNORECASE)
_PASSIVE = re.compile(
    r"\b(is|are|was|were|be|been|being|am)\s+(\w+ed|written|done|made|given|taken|"
    r"seen|known|held|built|found|shown|led|kept|sent|drawn|brought|thought|caught)\b",
    re.IGNORECASE,
)
_PARTICIPLE_PRES = re.compile(r"\b(\w+ing)\b", re.IGNORECASE)
_PARTICIPLE_PAST = re.compile(r"\b(\w+ed)\b", re.IGNORECASE)


def rule_hints(text: str) -> list[str]:
    """문장에서 규칙기반으로 잡아낸 문법 요소를 한국어 힌트 문자열 목록으로.

    LLM 프롬프트에 '이런 요소가 보이니 태깅에 반영하라'고 주입하는 용도.
    정밀 태깅은 LLM 이 하므로 여기서는 재현율 위주로 넉넉히 뽑는다.
    """
    hints: list[str] = []
    low = text.lower()
    words = re.findall(r"[A-Za-z']+", low)
    wset = set(words)

    # 수동태
    m = _PASSIVE.search(text)
    if m:
        hints.append(f"수동태로 보이는 부분: '{m.group(0)}' → 'V 수동태' 태그, 능동형 오답(X) 병기 검토")

    # 관계사
    rels = wset & _REL_PRONOUNS
    if rels:
        hints.append(
            "관계사 후보: " + ", ".join(sorted(rels))
            + " → 주격/목적격 관계대명사 구분, that↔which 오답 병기 검토"
        )

    # to 부정사
    if _TO_V.search(text):
        hints.append("to부정사 후보 존재 → 'to-v (형용사/부사/명사)' 용법 태그")

    # 분사 (현재/과거)
    if _PARTICIPLE_PRES.search(text):
        hints.append("-ing 형태 존재 → 현재분사/동명사/진행 구분, 반대분사 오답(X) 검토")
    if _PARTICIPLE_PAST.search(text):
        hints.append("-ed 형태 존재 → 과거분사/과거시제 구분, 반대분사 오답(X) 검토")

    # 조동사
    if wset & _MODALS:
        hints.append("조동사 존재 → 뒤에 동사원형, 시제/태 결합 확인")

    # 접속/삽입 표지
    for marker, label in [
        ("as well as", "as well as (병렬 연결)"),
        ("while", "while (양보/동시) 부사절"),
        ("although", "although (양보) 부사절"),
        ("because", "because (이유) 부사절"),
        ("however", "however (연결 부사)"),
        ("that is", "that is (삽입, 부연)"),
    ]:
        if marker in low:
            hints.append(f"연결/삽입 표지: {label}")

    return hints


# ---------------------------------------------------------------------------
# LLM 시스템/프롬프트
# ---------------------------------------------------------------------------
SYSTEM = (
    "당신은 한국 고등학교 영어 내신·수능 대비 '구문 분석 학습지'를 만드는 전문 강사입니다. "
    "영어 문장을 성분(S/V/O/C)과 문법 요소(분사·관계사·수동태·준동사·삽입구 등)로 정밀하게 "
    "태깅하고, 시험에 자주 나오는 함정 형태를 오답형(X)으로 병기합니다. "
    "요청된 JSON 스키마에 정확히 맞는 값만 응답하세요."
)


def _strength_rule(strength: str) -> str:
    if strength == STRENGTH_NONE:
        return (
            "- 태깅 강도=없음: 성분/문법 주석을 붙이지 마세요(role·note·wrong·above 모두 빈 문자열, "
            "hl/underline/color 미사용). 원문을 의미 단위 토큰으로만 나누고 translation 만 정확히 채우세요.\n"
        )
    if strength == STRENGTH_KEY:
        return (
            "- 태깅 강도=핵심만: 문장의 주요 성분(S/V/O/C)과 가장 중요한 어법 1~2개만 태깅하세요. "
            "지엽적인 주석은 생략합니다.\n"
        )
    return (
        "- 태깅 강도=전체: 성분과 문법 요소를 빠짐없이 태깅하세요. 시험 함정은 오답형(X)으로 병기합니다.\n"
    )


def analyze_prompt(text: str, index: int, strength: str, hints: list[str]) -> str:
    hint_block = ""
    if hints:
        hint_block = "\n[규칙기반 힌트(참고용, 틀리면 무시)]\n- " + "\n- ".join(hints) + "\n"
    return (
        f"다음은 지문의 {index}번째 문장입니다. 이 문장을 구문 분석 학습지용으로 태깅하세요.\n\n"
        f"[문장]\n{text}\n"
        + hint_block +
        "\n[작성 규칙]\n"
        "- lines: 원칙적으로 '문장 전체'를 tokens 한 배열(=한 줄)에 담으세요. 화면 폭에 맞춰 "
        "자동으로 줄바꿈되므로 인위적으로 쪼개지 마세요(원문이 자연스럽게 이어져 읽혀야 함). "
        "아주 긴 복문에 한해 의미 단위로 최대 2줄까지만 나눌 수 있습니다.\n"
        "- 각 token 의 text 는 원문 단어/구를 '순서대로, 빠짐없이' 담아 이어붙이면 원문이 되어야 합니다. "
        "성분/주석을 붙일 단위로 묶으세요(예: 'the curious students' 를 한 토큰으로). "
        "절·구를 감싸는 괄호 ( ) 는 토큰 text 에 그대로 포함하세요.\n"
        "- color(색 원리 — 반드시 일관 적용): 🔴red='어법 포인트'(문장의 본동사), "
        "🔵blue='구조·의미'(대비·강조되는 핵심 형용사/명사). 그 외는 빈 문자열. "
        "성분 라벨(role)은 파랑, 어법 주석(분사·수동·관계사·수일치)은 빨강 계열로 통일합니다.\n"
        "- 지칭(대명사·지시어) 필수 표기: it, this, that, these, those, they, them, he, she, "
        "one, such 등이 나오면 note 에 '→ 가리키는 대상' 형식으로 반드시 무엇을 지칭하는지 적으세요 "
        "(예: it → the teabag, they → curious students). note_kind 는 'gray'.\n"
        "- role: 문장 성분 라벨. 기본형 'S','V','O','C'; 복문은 'S①','V①','V②'…; "
        "필요하면 '가S'(가주어),'진S'(진주어),'5V'(5형식 동사),'OC'(목적격보어),'목관대'(목적격 관계대명사),"
        "'주관대'(주격 관계대명사),'병렬','전'(전치사) 등도 사용. 성분이 아니면 빈 문자열.\n"
        "- note: 그 토큰의 문법/해석 주석(예: '현재분사','수동태','to-v(부사)','be p.p(수동태)', "
        "'선행사: walls', '~에게 다가가다'). 유의어는 '= 동의어', 반의어는 '↔ 반의어' 형식. 없으면 빈 문자열.\n"
        "- note_kind: 어법 강조(분사·수동태·관계사·수일치)=‘red’, 해석 힌트/유의·반의(=,↔)=‘gray’, "
        "성분 보조=‘blue’, 그 외=‘lbl’.\n"
        "- wrong: 시험 함정 오답형이 있으면 '틀린형(X)' 로(예: 'who(X)','designed(X)','absolutely(X)'). 없으면 빈 문자열.\n"
        "- above: 단어 위에 띄울 짧은 메모(생략 복원 'it is 생략', 원문 '[원문] mingle with', "
        "유의/반의 '= infuse' · '↔ decline'). 없으면 빈 문자열.\n"
        "- hl: 담화표지(Similarly, In fact, However 등)는 'p'(라벤더), 시험에 강조할 핵심 어구는 'y'(노랑), "
        "보조 강조는 'g'(연두). 기본은 빈 문자열.\n"
        "- underline: 특정 표현을 밑줄로 강조할 때만 true.\n"
        + _strength_rule(strength) +
        "- translation: 이 문장의 자연스러운 한국어 해석(직독직해체).\n"
        "- gloss_en: 직역만으로는 뜻이 안 통하고 '맥락을 알아야 풀리는' 함축 문장일 때만, 그 함축 의미를 "
        "쉬운 영어 한 문장으로. 아니면 빈 문자열.\n"
        "- badge: 빈출 포인트면 '빈', 서술형 출제 후보면 '서'. 아니면 빈 문자열.\n"
    )


# ---------------------------------------------------------------------------
# 변환
# ---------------------------------------------------------------------------
def _tok(spec) -> Token:
    return Token(
        text=spec.text,
        role=spec.role or None,
        note=spec.note or None,
        note_kind=spec.note_kind or "lbl",
        wrong=spec.wrong or None,
        above=spec.above or None,
        hl=spec.hl or None,
        underline=bool(spec.underline),
        color=spec.color or None,
    )


def _to_sentence(index: int, sa: SentenceAnalysis) -> Sentence:
    lines = [[_tok(t) for t in ln.tokens] for ln in sa.lines if ln.tokens]
    if not lines:  # LLM 이 lines 를 비우면 원문을 통째로 한 줄로
        lines = [[Token(text=sa.translation or "")]]
    return Sentence(
        index=index,
        lines=lines,
        translation=sa.translation or "",
        badge=sa.badge or None,
        gloss_en=sa.gloss_en or None,
    )


# ---------------------------------------------------------------------------
# 공개 API
# ---------------------------------------------------------------------------
def analyze_sentence(
    client: ClaudeClient,
    text: str,
    index: int,
    strength: str = STRENGTH_FULL,
    max_retries: int = 1,
) -> Sentence:
    """LLM 로 문장 1개를 태깅하여 Sentence 반환 (points 는 point_builder 가 채움).

    강도='없음'이어도 해석(translation)은 필요하므로 LLM 을 호출하되 태깅만 생략한다.
    (API 없이 배관만 볼 때는 pipeline.analyze_text_rule_only 를 쓴다.)
    """
    hints = rule_hints(text) if strength != STRENGTH_NONE else []
    sa = client.structured(
        system=SYSTEM,
        prompt=analyze_prompt(text, index, strength, hints),
        model_cls=SentenceAnalysis,
        max_tokens=4000,
        max_retries=max_retries,
    )
    return _to_sentence(index, sa)


def rule_only_sentence(text: str, index: int, tag: bool = True) -> Sentence:
    """API 없이 규칙기반만으로 Sentence 초안 구성.

    - tag=True  : 규칙으로 잡히는 어법에 간단한 red 주석을 붙인다(미리보기용).
    - tag=False : 태깅 없이 원문만(태깅 강도='없음').
    해석은 비운다(LLM 없이는 번역 불가). mock 은 별도 모듈에서 제공.
    """
    text = re.sub(r"\s+", " ", (text or "").strip())
    words = text.split(" ") if text else []
    toks = [Token(text=w) for w in words]
    if tag and toks:
        # 아주 러프한 데모 태깅: 첫 명사구를 S, 첫 be/조동사/일반동사를 V 로 가정.
        _mark_rough_svo(toks)
        for i, w in enumerate(words):
            lw = re.sub(r"[^a-z']", "", w.lower())
            if lw in _REL_PRONOUNS and i > 0:
                toks[i].note, toks[i].note_kind = "관계사", "red"
            elif lw in _BE and i + 1 < len(words) and re.search(r"(ed|en)$", words[i + 1].lower()):
                toks[i].note, toks[i].note_kind = "수동태", "red"
            elif re.search(r"ing$", lw) and len(lw) > 4:
                toks[i].note, toks[i].note_kind = "분사/동명사", "red"
    return Sentence(index=index, lines=[toks] if toks else [[Token(text="")]], translation="")


def _mark_rough_svo(toks: list[Token]) -> None:
    """데모용 아주 단순한 S/V 표시(정밀도 목적 아님, 배관 확인용)."""
    verb_like = re.compile(r"(s|ed|es|ing)$", re.IGNORECASE)
    marked_s = marked_v = False
    for i, t in enumerate(toks):
        lw = re.sub(r"[^a-z']", "", t.text.lower())
        if not marked_s and lw and lw not in {"the", "a", "an"}:
            t.role = "S"
            marked_s = True
            continue
        if marked_s and not marked_v and (lw in _BE or lw in _MODALS or verb_like.search(lw)):
            t.role = "V"
            marked_v = True
