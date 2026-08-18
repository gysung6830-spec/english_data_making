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
        hints.append("to부정사 후보 존재 → 'to부정사(형용사적 용법/부사적 용법/명사적 용법)' 태그")

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
    "한글 해석은 교사가 직접 쓴 것처럼 자연스러운 시험 해석체로, 번역투·AI 상투어 없이 담백하게. "
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
        "절·구를 인위적으로 괄호 ( ) 로 감싸지 마세요(원문에 원래 있던 괄호가 아니면 넣지 않음).\n"
        "- ⚠️ 숫자·수치 절대 누락 금지: 퍼센트·연도·금액·수량(예: '60 percent','1961','$25','more than 100')의 "
        "'숫자'를 반드시 그대로 토큰에 포함하세요. 특히 도표(그래프) 지문은 수치가 핵심이므로 'over 60 percent' 를 "
        "'over percent' 처럼 숫자를 빠뜨리면 안 됩니다.\n"
        "- 안내문 제목·항목명(예: 'Notice','Participation Fee','When & Where')은 '명령문'이 아니라 "
        "명사구(제목)입니다. 동사로 오해해 '주목하라' 처럼 명령문으로 태깅하지 마세요(role 비우거나 명사구로).\n"
        "- ⚠️ 원문을 임의로 줄이거나 '...'(말줄임)로 생략하지 마세요. 주어진 '이 한 문장'만 태깅하고, "
        "여러 문장을 한 번에 합치지 마세요. (원문에 이미 '...'/'…' 생략부호가 있으면 그건 그대로 살립니다.)\n"
        "- color(본문 글씨 색):\n"
        "    🔴 red = '중요 어법' 어구에만(수동태·분사·관계사·도치·비교급·가정법·강조 등). 이 색은 항상 유지.\n"
        "    유의어/반의어 어휘는 '글씨색을 쓰지 말고'(color 빈 문자열) note/above 에 '= 유의어'/'↔ 반의어'만 "
        "답니다. 렌더러가 그 단어에 '파란 밑줄'을 자동으로 긋습니다.\n"
        "    → 어법이면서 유의어도 있으면: color='red'(빨간 글씨) + '= 유의어' 주석(자동 파란 밑줄).\n"
        "- 어법 요소(수동태·분사·관계사·도치·비교급·가정법·to부정사·5형식 등)는 해당 토큰에 "
        "note=어법 이름(짧게, 예 '주격 관계대명사','수동태','to부정사의 의미상 주어'), note_kind='red', "
        "color='red' 로 답니다. 인라인 번호((1)(2)…)와 오른쪽 어법 Point 박스는 코드가 자동으로 만듭니다.\n"
        "  · 관계대명사·관계부사는 note 에 '선행사'를 반드시 함께 적습니다(예: '주격 관계대명사(선행사: walls)', "
        "'관계부사 where(선행사: the place)'). 그래야 어법 Point 박스에 무엇을 수식하는지 표시됩니다.\n"
        "- 유의어/반의어 note 는 '= 유의어' 또는 '↔ 반의어'(note_kind='gray'); 단어엔 자동으로 파란 밑줄이 그어짐.\n"
        "  (렌더 규칙: 성분 라벨 role 은 단어 '위'에, 어법 번호·유의어/반의어는 단어 '아래'에 자동 배치됨)\n"
        "- 지칭(대명사·지시어)은 '본문 주석'이 아니라 refs 로 보냅니다: it, this, that, these, those, "
        "they, them, he, she, one, such 등은 refs 배열에 'it → the teabag' 형식으로 담고, "
        "토큰 note 에는 넣지 마세요.\n"
        "- role: 문장 성분 라벨. '모든 문장에 S·V·O·OC·C 를 빠짐없이' 답니다(복문은 'S①','V①','V②'…). "
        "필요하면 '가S','진S','OC','병렬','전' 등도 사용. 성분이 아닌 토큰만 빈 문자열.\n"
        "- 정확도: 어법(red)·유의어(=/↔) 태그는 그 요소가 걸리는 '정확한 단어'에만 다세요. "
        "여러 단어를 한 토큰으로 묶어 번호·밑줄이 엉뚱한 위치에 가지 않게 하세요.\n"
        "- note: 그 토큰의 문법/해석 주석(예: '현재분사','수동태','be p.p(수동태)', "
        "'선행사: walls', '~에게 다가가다'). 유의어는 '= 동의어', 반의어는 '↔ 반의어' 형식. 없으면 빈 문자열.\n"
        "  · ⚠️ to부정사는 'to-v'가 아니라 '**to부정사**'로 쓰고, 반드시 용법을 괄호로 병기하세요: "
        "'to부정사(명사적 용법)' / 'to부정사(형용사적 용법)' / 'to부정사(부사적 용법)'. "
        "(의미상 주어 등 특수 용법은 'to부정사의 의미상 주어'처럼 구체적으로.)\n"
        "- note_kind: '문법·어법을 설명하는 note 는 무조건 red' 로 하세요(분사·수동태·관계사·수일치·비교·"
        "부정사·동명사·도치·강조·가정법·병렬·형식·접속사·동격 등 모든 어법 용어). "
        "gray 는 '어법이 아닌 것'에만: 유의·반의(=,↔)·짧은 해석 힌트뿐입니다. "
        "성분 보조=‘blue’, 그 외=‘lbl’. ⚠️ 어법 설명을 gray 로 두면 회색 글자로 새어 나오니 반드시 red.\n"
        "- wrong: 실제 시험 함정이 되는 '틀린 형태'가 있을 때만 '틀린형(X)' 로(예: 'who(X)','designed(X)').\n"
        "  ⚠️ 오답형(X) 정확성 필수:\n"
        "    (1) 토큰 text 는 지문에 실제로 쓰인 '올바른 형태'여야 하고, wrong 은 그 자리에 넣으면 '틀리는' "
        "대안이어야 합니다(맞는 형태를 (X)로 표시하지 말 것).\n"
        "    (2) wrong 을 다는 토큰에는 '왜 그 형태가 맞는지' 설명하는 red 어법 note(note_kind='red')를 반드시 함께 "
        "다세요(예: '주격 관계대명사'+who(X), '수동태'+designed(X), '수일치'+are(X)).\n"
        "    (3) 실제 문법적 함정이 없으면 wrong 을 '지어내지 말고' 빈 문자열로 두세요.\n"
        "    (4) 전치사·by 뒤 동명사(by v-ing, in v-ing 등)는 'v-ing 가 정답'입니다. 이때 text 는 v-ing "
        "그대로 두고 wrong 은 원형·to부정사(예: 'provide(X)','to provide(X)')로 하세요 — v-ing 자체를 (X)로 "
        "표시하면 안 됩니다.\n"
        "    (5) 수일치는 '진짜 주어(핵심 명사)'에 맞추세요. 'A of B'(예: production of ... elements) 구조는 "
        "of 앞의 핵심명사 A(production, 단수)에 동사를 일치시킵니다. 이 경우 정답은 requires(단수)이고 wrong 은 "
        "require(X)입니다 — of 뒤 복수명사(elements)에 끌려 정답·오답을 뒤집지 마세요.\n"
        "- above: 단어 위에 띄울 짧은 메모(생략 복원 'it is 생략', 원문 '[원문] mingle with', "
        "유의/반의 '= infuse' · '↔ decline'). 없으면 빈 문자열.\n"
        "- ⚠️ 인라인 주석(note·above)은 '짧게'(대략 12자 이내: 어법명·유의어(=)·반의어(↔)·번호 정도). "
        "선행사 지정('선행사: an identity')이나 긴 문법 설명은 인라인에 넣지 말고 오른쪽 '어법 Point' 박스"
        "(point_builder)로 넘기세요. 긴 주석이 옆 단어와 겹칩니다.\n"
        "- hl: 담화표지(Similarly, In fact, However 등)는 'p'(라벤더); 빈칸(빈출) 문제로 나올 만한 핵심 어구나 "
        "주제문은 'y'(노랑 형광). 기본은 빈 문자열. (별도의 '빈' 뱃지는 쓰지 않고 노란 형광으로 대체)\n"
        "- underline: 특정 표현을 밑줄로 강조할 때만 true.\n"
        + _strength_rule(strength) +
        "- translation: 이 문장의 자연스러운 한국어 해석(직독직해체).\n"
        "- gloss_en / gloss_ko: 직역만으로는 뜻이 안 통하고 '맥락을 알아야 풀리는' 함축 문장일 때만, 그 함축 의미를 "
        "쉬운 영어 한 문장(gloss_en)과 한글 한 문장(gloss_ko)으로 '병기'. 아니면 둘 다 빈 문자열.\n"
        "- badge: 서술형 출제 후보면 '서'. (빈출은 뱃지 대신 노란 형광 hl='y' 로 표시)\n"
        "- 끊어읽기(직독직해): 영어와 한글의 '끊는 지점'이 정확히 1:1 이어야 합니다.\n"
        "    · slash 는 조각과 조각 '사이'에만 찍습니다. 즉 의미 단위의 마지막 토큰에 slash=true 를 표시하되, "
        "'문장 맨 끝' 토큰에는 slash 를 찍지 마세요(끝에는 경계가 없습니다). N개 조각 → slash 는 N-1개.\n"
        "    · reading_ko: '배열(list)'입니다. 영어 조각마다 정확히 한 개의 한글 직독직해를 같은 순서로 담으세요. "
        "즉 배열 길이 = 영어 조각 수 = slash 개수 + 1, i번째 원소 = i번째 영어 조각의 해석.\n"
        "    · ⚠️ 한글을 영어보다 '더 잘게' 쪼개지 마세요. 접속사·부사(그러나·왜냐하면·그래서·즉 등) 뒤에서 임의로 "
        "더 끊지 말고, 오직 영어 slash 경계에서만 끊습니다. 한 영어 조각 안의 접속사는 그 조각의 한글에 함께 넣으세요.\n"
        "    · 조각은 너무 잘게 쪼개지 말고 '의미 덩어리(주어부/동사구/목적어/전치사구/절)' 단위로, 한 문장에 3~6조각 정도가 "
        "자연스럽습니다. 각 한글 조각은 그 자체로 읽어서 뜻이 통하도록 자연스럽게 옮기세요(어색한 직역·토막 금지).\n"
        "      예: 영어 3조각 [\"Certain nomadic tribes don't have much,\", \"yet they are happy to share\", "
        "\"because it is in their interest to do so.\"] (slash 2개) → reading_ko(3개) "
        "[\"어떤 유목 부족들은 가진 것이 많지 않다\", \"그러나 그들은 기꺼이 나눈다\", \"왜냐하면 그렇게 하는 것이 그들에게 이익이기 때문이다\"].\n"
        "    · 제출 전, (영어 slash 개수 + 1)과 reading_ko 배열 길이가 같은지, 문장 끝에 slash 가 없는지 스스로 확인하세요.\n"
        "    · translation(온전한 해석)과 달리 reading_ko 는 어순대로 끊어 읽는 해석입니다.\n"
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
        slash=bool(getattr(spec, "slash", False)),
    )


# 앞 단어에 '공백 없이' 붙어야 하는 문장부호(마침표·쉼표·닫는 괄호/따옴표 등)
_TRAIL_PUNCT = set(".,;:!?…”’\")]}")


def _merge_trailing_punct(lines: list[list[Token]]) -> list[list[Token]]:
    """문장부호만 있는 토큰을 앞 토큰에 붙인다('protectors' + '.' → 'protectors.').

    LLM 이 마침표·쉼표를 별도 토큰으로 내보내면 렌더 시 'protectors .' 처럼 부호
    앞에 공백이 생긴다. 부호 토큰을 앞 단어에 병합해 그 공백을 없앤다(슬래시 등
    앞 토큰 속성은 유지, 부호 토큰의 slash 는 앞 토큰으로 넘긴다).
    """
    for line in lines:
        merged: list[Token] = []
        for t in line:
            txt = (t.text or "").strip()
            if (merged and txt and all(c in _TRAIL_PUNCT for c in txt)
                    and not t.role and not t.note and not t.wrong and not t.above):
                prev = merged[-1]
                prev.text = (prev.text or "") + txt
                prev.slash = prev.slash or bool(getattr(t, "slash", False))
            else:
                merged.append(t)
        line[:] = merged
    return lines


def _strip_trailing_slash(lines: list[list[Token]]) -> list[list[Token]]:
    """문장 '맨 끝' 토큰의 slash 를 제거한다.

    LLM 에게 '각 의미 단위의 마지막 토큰에 slash' 규칙을 주면 문장의 마지막 조각
    끝에도 slash 를 찍어 '...on taste /' 처럼 무의미한 끝 슬래시가 생긴다.
    끊어읽기 경계는 조각과 조각 '사이'에만 있어야 하므로(N조각 → N-1 경계)
    마지막 토큰의 slash 는 항상 잘라낸다. 이렇게 하면 영어 조각 수와 한글 조각
    수 계산도 두 관습(사이-only / 마지막-토큰) 모두에서 일관되게 맞아떨어진다.
    """
    toks = [t for ln in lines for t in ln]
    if toks and toks[-1].slash:
        toks[-1].slash = False
    return lines


def _english_chunk_count(lines: list[list[Token]]) -> int:
    """영어 끊어읽기 조각 수 = 조각 사이 slash 경계 수 + 1.

    (마지막 토큰의 slash 는 _strip_trailing_slash 로 이미 제거된 상태를 가정.)
    """
    toks = [t for ln in lines for t in ln]
    if not toks:
        return 0
    slashes = sum(1 for t in toks if t.slash)
    return slashes if toks[-1].slash else slashes + 1


def _english_chunk_sizes(lines: list[list[Token]]) -> list[int]:
    """영어 끊어읽기 조각별 '글자 수'(가중치). 조각 병합 시 긴 영어 조각에 한글을 더 많이
    배분해 경계가 자연스럽게 맞도록 하는 데 쓴다. 조각 수는 _english_chunk_count 와 동일."""
    toks = [t for ln in lines for t in ln]
    sizes: list[int] = []
    cur = 0
    for t in toks:
        cur += max(1, len((t.text or "").strip()))
        if getattr(t, "slash", False):
            sizes.append(cur)
            cur = 0
    if cur > 0 or not sizes:
        sizes.append(cur)
    return sizes


def _merge_ko_weighted(chunks: list[str], sizes: list[int]) -> list[str]:
    """한글 조각이 영어보다 '더 잘게' 쪼개졌을 때(과분할), 순서를 유지한 채 인접 조각을
    묶어 len(sizes)개로 줄인다. 각 영어 조각의 '길이 비율'만큼 한글 조각을 배분해(반올림)
    경계가 영어와 자연스럽게 대응되게 한다.
    (예: 영어 ['In fact,','they should expect them'](길이 8:22) + 한글 4개
         → 배분 [1,3] → ['사실,','그들은 예상해야 한다 그것들을'])."""
    E = len(sizes)
    K = len(chunks)
    if E <= 0 or K <= E:
        return chunks
    total = sum(sizes) or E
    counts = [max(1, round(K * s / total)) for s in sizes]   # 길이 비율 배분(각 최소 1)
    # 반올림 오차로 합이 K 와 달라지면, 비율이 가장 어긋난 조각부터 ±1 로 보정
    diff = K - sum(counts)
    while diff > 0:                                   # 부족 → 가장 '덜 받은'(size/count 큰) 조각에 +1
        j = max(range(E), key=lambda i: sizes[i] / counts[i])
        counts[j] += 1
        diff -= 1
    while diff < 0:                                   # 초과 → 가장 '많이 받은' 조각(단, >1)에서 -1
        cand = [i for i in range(E) if counts[i] > 1]
        if not cand:
            break
        j = min(cand, key=lambda i: sizes[i] / counts[i])
        counts[j] -= 1
        diff += 1
    out: list[str] = []
    idx = 0
    for c in counts:
        out.append(" ".join(chunks[idx:idx + c]))
        idx += c
    if idx < K:                                       # 보정 실패 시 잔여를 마지막 조각에 붙임
        out[-1] = (out[-1] + " " + " ".join(chunks[idx:])).strip()
    return out


def _reading_ko_aligned(lines: list[list[Token]], chunks: list[str]) -> str:
    """직독직해 표시 문자열을 만든다.

    - 각 한글 조각 안에 섞여 들어온 '/'(LLM 오류)는 제거해, 조각 수가 부풀지 않게 한다
      (그래야 렌더의 '/'와 검수(quality)의 조각 수 계산이 항상 일치한다).
    - 한글이 영어보다 '더 잘게' 쪼개졌으면(과분할), 영어 조각 수에 맞춰 인접 조각을 균등
      병합해 끊어읽기를 살린다(연속 표기로 뭉개지 않음).
    - 그래도 2개 이상 크게 어긋나면(한글이 오히려 부족한 경우 등) 정렬 실패로 보고 슬래시
      없이 이어 붙인다(어긋난 '/' 노출 방지). 1개 차이는 그대로 두어 가독성을 살린다."""
    chunks = [" ".join(c.replace("/", " ").split()) for c in (chunks or []) if c and c.strip()]
    chunks = [c for c in chunks if c]
    if not chunks:
        return ""
    e = _english_chunk_count(lines)
    if e >= 2 and len(chunks) > e:             # 한글 과분할 → 영어 조각 길이에 맞춰 병합
        sizes = _english_chunk_sizes(lines)
        if len(sizes) != e:                    # 방어: 조각 수 불일치 시 균등 가중
            sizes = [1] * e
        chunks = _merge_ko_weighted(chunks, sizes)
    if e >= 2 and abs(len(chunks) - e) >= 2:   # 여전히 크게 어긋남 → 연속 표기(슬래시 제거)
        return " ".join(chunks)
    return " / ".join(chunks)


def _to_sentence(index: int, sa: SentenceAnalysis) -> Sentence:
    # LLM 이 여러 줄로 쪼개 보내도 한 줄로 펼쳐 자연스럽게 흐르게(화면 폭에 맞춰 자동 줄바꿈).
    flat = [_tok(t) for ln in sa.lines for t in ln.tokens]
    lines = _merge_trailing_punct([flat]) if flat else []
    lines = _strip_trailing_slash(lines)   # 문장 끝의 무의미한 '/' 제거
    if not lines:  # LLM 이 lines 를 비우면 원문을 통째로 한 줄로
        lines = [[Token(text=sa.translation or "")]]
    reading = getattr(sa, "reading_ko", []) or []
    if isinstance(reading, str):         # 방어: 문자열이면 분해
        reading = [c for c in reading.split("/")]
    return Sentence(
        index=index,
        lines=lines,
        translation=sa.translation or "",
        reading_ko=_reading_ko_aligned(lines, reading),
        badge=sa.badge or None,
        gloss_en=sa.gloss_en or None,
        gloss_ko=sa.gloss_ko or None,
        refs=list(sa.refs or []),
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
