"""문장별 복합유형 통합 워크북 데이터 모델.

두 계층으로 나눈다.
  1) LLM 응답 계층 (pydantic) — client.structured 로 JSON 스키마를 강제/검증한다.
     LLMQuestion / LLMSentence / LLMWorkbook. num(전역 문항번호)·total 은 담지 않는다.
  2) 렌더 계층 (dataclass) — 코드가 전역 채번·total 집계를 마친 최종 구조.
     Question / Sentence / Workbook. 템플릿 렌더링에 그대로 쓴다.

LLM 은 문장/문제만 만들고, '전역 연속 번호'와 '총 문항 수(SCORE)'는 코드가 채운다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from . import textutil

# 출제 유형 (spec 1의 5유형 + 대명사 지칭 ref)
#   ref = 대명사가 가리키는 대상을 고르는 지칭 추론 (관계사·대명사와 같은 보라색 계열)
QTYPE = Literal["verb", "adj", "rel", "conj", "order", "ref"]

# 유형 → 위첨자 라벨 / CSS 클래스 (spec 4-4)
TYPE_LABEL = {"verb": "동사", "adj": "형·부", "rel": "관계사", "conj": "연결사",
              "order": "배열", "ref": "지칭"}
TYPE_CLASS = {"verb": "v", "adj": "a", "rel": "r", "conj": "c", "order": "o", "ref": "r"}
TYPE_COLOR = {
    "verb": "#2563a0", "adj": "#158060", "rel": "#7d3caf",
    "conj": "#c47510", "order": "#b83232", "ref": "#7d3caf",
}

# en_template 안의 자리표시자 패턴: {{Q1}}
_PLACEHOLDER = re.compile(r"\{\{\s*(Q\d+)\s*\}\}")


# ---------------------------------------------------------------------------
# 1) LLM 응답 계층 (pydantic)
# ---------------------------------------------------------------------------
class LLMQuestion(BaseModel):
    id: str                       # "Q1" (문서 전체에서 유일)
    type: QTYPE                   # verb | adj | rel | conj | order
    display: str                  # 문제지 표기: "(react)" / "[ a / b / c ]" / "〈 ... 〉"
    answer: str                   # 정답
    reason: str                   # 한 줄 해설


class LLMSentence(BaseModel):
    no: int                       # 문장 순번(1부터)
    en_template: str              # {{Q1}} 자리표시자를 포함한 영어 문장
    ko: str                       # 한국어 해석
    questions: list[LLMQuestion] = Field(default_factory=list)
    # 출제할 요소가 없는 문장(빈 questions)이 섞여 와도 전체를 거부하지 않는다.
    # 이런 문장은 build_workbook 에서 건너뛴다(spec: 출제할 요소가 없으면 넣지 않음).


class LLMWorkbook(BaseModel):
    sentences: list[LLMSentence] = Field(default_factory=list)

    @field_validator("sentences")
    @classmethod
    def _has_sentences(cls, v: list[LLMSentence]) -> list[LLMSentence]:
        if not v:
            raise ValueError("워크북 문장이 비어 있습니다.")
        return v


# ---------------------------------------------------------------------------
# 2) 렌더 계층 (dataclass, spec 4-1)
# ---------------------------------------------------------------------------
@dataclass
class Question:
    id: str            # "Q1"
    type: str          # verb | adj | rel | conj | order
    display: str       # 문제지에 보일 표기
    answer: str        # 정답
    reason: str        # 한 줄 해설
    num: int = 0       # 문서 전체 연속 문항번호 (코드가 채움)

    @property
    def label(self) -> str:
        return TYPE_LABEL.get(self.type, "")

    @property
    def css(self) -> str:
        return TYPE_CLASS.get(self.type, "")

    @property
    def color(self) -> str:
        return TYPE_COLOR.get(self.type, "#1c2e44")


@dataclass
class Sentence:
    no: int
    en_template: str   # {{Q1}} 자리표시자 포함
    ko: str
    questions: list[Question] = field(default_factory=list)


@dataclass
class Workbook:
    title: str
    subtitle: str
    sentences: list[Sentence] = field(default_factory=list)
    total: int = 0     # 총 문항 수 (SCORE 표시용)
    label: str = ""    # 출처 기반 문항 라벨 (예: "[고1] 9월 30번")

    @property
    def all_questions(self) -> list[Question]:
        return [q for s in self.sentences for q in s.questions]


# ---------------------------------------------------------------------------
# 검증 + 전역 채번 (spec 4-2 단계 4·5, spec 5 체크리스트)
# ---------------------------------------------------------------------------
def placeholders_in(template: str) -> list[str]:
    """en_template 에 등장하는 자리표시자 id 목록(등장 순서)."""
    return _PLACEHOLDER.findall(template)


def validate_llm_workbook(wb: LLMWorkbook) -> None:
    """LLM 응답의 정합성을 검증한다. 위반 시 ValueError.

    - 각 문장의 {{Qn}} 자리표시자가 questions 와 1:1 대응
    - 문항 id 가 문서 전체에서 유일
    - 특수구문(order) display 는 〈 … 〉 형태
    """
    total_q = 0
    for s in wb.sentences:
        # 출제할 요소가 없는 문장(빈 questions)은 build_workbook 에서 건너뛰므로 검증도 건너뛴다.
        if not s.questions:
            continue
        total_q += len(s.questions)
        # 자리표시자 수와 questions 수가 달라도(예: LLM 이 {{Qn}} 을 안 넣거나 더 넣음)
        # 전체를 실패시키지 않는다. build_workbook 이 '등장 순서'로 가능한 만큼만 짝지어
        # 채번하고, 남는 자리표시자/문항은 렌더에서 자연스럽게 정리한다.
        for q in s.questions:
            if q.type == "order":
                d = q.display.strip()
                if not (d.startswith("〈") and d.endswith("〉")):
                    raise ValueError(
                        f"문항 {q.id}: 특수구문(order) 표기는 〈 어구/어구 〉 형태여야 합니다(현재: {q.display!r})."
                    )
    # 모든 문장이 비어 출제 문항이 하나도 없으면 실패로 보고 재요청한다.
    if total_q == 0:
        raise ValueError("출제 문항이 하나도 없습니다(모든 문장의 questions 가 비어 있음).")


def _content_words(text: str) -> list[str]:
    return [w.lower() for w in re.findall(r"[A-Za-z]+", text)]


def _covered(w: str, pool: list[str]) -> bool:
    """단어 w 가 pool 안의 어떤 단어와 (어형 변화 허용) 대응되는가."""
    return any(x == w or (len(w) >= 4 and len(x) >= 4 and (x.startswith(w[:4]) or w.startswith(x[:4])))
               for x in pool)


def _best_match(solved_words: list[str], originals_words: list[list[str]]) -> tuple[int, float]:
    """solved 문장이 어떤 원문 문장과 가장 겹치는지(index, 겹침 비율)."""
    sset = set(solved_words)
    best, bi = 0.0, -1
    for i, ow in enumerate(originals_words):
        if not ow:
            continue
        ratio = len(sset & set(ow)) / max(1, len(set(ow)))
        if ratio > best:
            best, bi = ratio, i
    return bi, best


def _restore_misplaced(parsed: list[dict], originals: list[str]) -> None:
    """의미 오배치·단어 소실 후처리 검증.

    각 문장의 '정답을 채운 완성 문장'(solved)을 만들어 가장 잘 맞는 '원문 문장'과 대조한다.
    원문의 내용어(4글자 이상)가 완성 문장에서 사라졌으면(예: 보기 박스가 엉뚱한 자리에 놓여
    'seek' 이 없어지고 'remain' 이 대신 들어감), 그 문장은 문항을 버리고 원문으로 되돌린다
    (깨진 문항보다 온전한 문장이 낫다). 중복·자리표시자 손상은 앞 단계에서 이미 정리된다.
    """
    ow_list = [_content_words(o) for o in originals]
    for p in parsed:
        if not p["pairs"]:
            continue
        solved = p["en"]
        for pid, q in p["pairs"]:
            solved = solved.replace("{{" + pid + "}}", (q.answer or "").split("/")[0].strip())
        sw = _content_words(solved)
        bi, ratio = _best_match(sw, ow_list)
        if bi < 0 or ratio < 0.6:          # 확실히 대응되는 원문이 없으면 건드리지 않는다
            continue
        lost = [w for w in ow_list[bi] if len(w) >= 4 and not _covered(w, sw)]
        if lost:                            # 원문 내용어가 사라짐 → 오배치/소실로 보고 원문 복원
            p["en"] = originals[bi].strip()
            p["pairs"] = []


def build_workbook(llm: LLMWorkbook, title: str, subtitle: str,
                   originals: list[str] | None = None) -> Workbook:
    """검증된 LLM 응답에 전역 연속 번호를 채우고 total 을 집계해 렌더용 Workbook 생성.

    출제 원리(문장당 최소 3개·최대 5개, 어형변형 2개, 5유형 지문 전체 커버)는 프롬프트가 담당하며,
    이 함수는 응답을 그대로 채번한다(동사 비율 상한은 '어형변형 2개/문장' 원칙과 상충하므로 두지 않는다).
    originals(원문 문장 목록)를 주면 의미 오배치·단어 소실을 후처리로 검증해 되돌린다.
    """
    validate_llm_workbook(llm)
    # 0) 정크/중복 문장 제거: '소문자도 공백도 없는' 비정상 문장(예: 내부 마커 "__DUP__")과
    #   같은 en 이 반복되는 중복 문장을 걸러 카드에 이상 문장이 노출되지 않게 한다
    #   (중복은 문항 수가 더 많은 쪽을 남긴다). 정상 영어 문장은 소문자·공백을 반드시 가진다.
    def _is_junk(t: str) -> bool:
        # 소문자도·공백도·자리표시자({{)도 없는 문장은 정상 영어 문장이 아니다(예: "__DUP__").
        t = (t or "").strip()
        return bool(t) and not any(c.islower() for c in t) and " " not in t and "{{" not in t
    _clean: dict = {}
    _order: list = []
    for s in llm.sentences:
        if _is_junk(s.en_template):
            continue
        k = re.sub(r"\s+", " ", (s.en_template or "").strip().lower())
        if k not in _clean:
            _order.append(k)
            _clean[k] = s
        elif len(s.questions) > len(_clean[k].questions):
            _clean[k] = s
    if _clean:
        llm.sentences = [_clean[k] for k in _order]
    # 1) 문장별 (pid, src) 쌍 수집
    parsed: list[dict] = []
    for s in llm.sentences:
        order = placeholders_in(s.en_template)
        if not s.questions:
            parsed.append({"no": s.no, "en": s.en_template, "ko": s.ko, "pairs": []})
            continue
        by_id = {q.id: q for q in s.questions}
        if set(order) == set(by_id) and len(order) == len(s.questions):
            pairs = [(pid, by_id[pid]) for pid in order]
        else:
            pairs = list(zip(order, s.questions))
        # 정답 어구가 자리표시자 옆에 그대로 남아 중복되는 경우(예: "(run) run",
        #   "how long a resource {{Q}}")를 정리한다.
        en = s.en_template
        for pid, q in pairs:
            en = textutil.dedup_placeholder(en, "{{" + pid + "}}", q.answer)
        parsed.append({"no": s.no, "en": en, "ko": s.ko, "pairs": pairs})

    # 1-b) 의미 오배치·단어 소실 후처리(원문과 대조) — originals 가 있을 때만
    if originals:
        _restore_misplaced(parsed, originals)

    # 2) 전역 채번 + Sentence 생성
    sentences: list[Sentence] = []
    counter = 0
    for p in parsed:
        if not p["pairs"]:
            # 문항이 없고 자리표시자만 남아 렌더 불가한 경우만 건너뛴다(그 외엔 읽기용으로 싣는다).
            if placeholders_in(p["en"]):
                continue
            sentences.append(Sentence(no=p["no"], en_template=p["en"], ko=p["ko"], questions=[]))
            continue
        qs: list[Question] = []
        for pid, src in p["pairs"]:
            counter += 1
            # 선택형([ … ]·지칭 = [ … ])은 보기 순서를 섞어 정답 위치 쏠림 제거.
            #   순서배열(특수구문) '〈 … 〉' 은 LLM 이 정답순으로 낼 때가 있어 '정답 어순과 다르게' 재섞기.
            if src.display.strip().startswith("〈"):
                disp = textutil.shuffle_order_display(src.display, src.answer)
            else:
                disp = textutil.shuffle_choices(src.display, f"{p['no']}:{pid}:{src.display}")
            qs.append(Question(id=pid, type=src.type, display=disp,
                               answer=src.answer, reason=src.reason, num=counter))
        sentences.append(Sentence(no=p["no"], en_template=p["en"], ko=p["ko"], questions=qs))
    return Workbook(title=title, subtitle=subtitle, sentences=sentences, total=counter)
