"""단일 유형 산문 워크시트 (어법 양자택일 / 어형 변형 / 어휘 양자택일).

지문 전체를 산문(번호 매긴 문장 목록)으로 두고, 한 가지 기능의 표기만 인라인으로 넣는다.
  - 어형 변형(form): (동사원형) + 쓰는 밑줄
  - 어법·어휘 양자택일(choice): [ A / B ] 박스
HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from pydantic import BaseModel, Field

from . import textutil
from .blanks_schemas import placeholders_in  # {{Pn}} 재사용
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER, _page_ready, _launch_chromium

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

# 문장당 출제 개수 규칙(어법·어휘 하/상): 최소 2 · 최대 5.
#   MAX 는 코드로 '확실히' 강제한다(초과분은 버리고 자리표시자를 정답/원문으로 복원).
#   MIN 은 프롬프트로 유도한다(문항을 새로 만들 수는 없으므로). 위반 시 진단 리포트로 알린다.
_MIN_PER_SENT = 2
_MAX_PER_SENT = 5
_COUNT_LIMITED = ("grammar", "vocab", "vocab_easy")
_COUNT_LABELS = {"grammar": "어법", "vocab_easy": "어휘(하)", "vocab": "어휘(상)"}


# ── 데이터 모델 ──────────────────────────────────────────────────────
@dataclass
class PItem:
    id: str            # "P1"
    display: str       # "(understand)" | "[ that / what ]"
    answer: str
    write: bool = False  # 어형 변형이면 쓰는 밑줄 표시
    gloss: str = ""    # 어휘 유형: 정답 단어의 한글 뜻(해설에 표기)


@dataclass
class PSentence:
    no: int
    template: str      # 인라인 {{P1}} 포함
    ko: str
    items: list[PItem] = field(default_factory=list)


@dataclass
class ProseWorksheet:
    wtype: str         # form | grammar | vocab
    label: str         # "어형 변형" 등
    instruction: str
    sentences: list[PSentence]


@dataclass
class ProsePack:
    header: str        # "[2026] 3월 모의고사 3학년 29번" 같은 상단 메타
    title: str
    subtitle: str
    worksheets: list[ProseWorksheet]
    label: str = ""    # 출처 기반 문항 라벨 (예: "[고1] 9월 30번")


# ── LLM 응답 계층 (pydantic) ─────────────────────────────────────────
class LLMProseItem(BaseModel):
    id: str            # "P1"
    display: str       # "[ that / what ]" | "(understand)"
    answer: str
    gloss: str = ""    # 어휘 유형에서만: 정답 단어의 한글 뜻


class LLMProseSentence(BaseModel):
    no: int
    en: str            # 자리표시자 없는 완전한 원문
    ko: str
    grammar_template: str = ""
    grammar_items: list[LLMProseItem] = Field(default_factory=list)
    form_template: str = ""
    form_items: list[LLMProseItem] = Field(default_factory=list)
    vocab_template: str = ""                      # 어휘 양자택일 (상: 난도 높음)
    vocab_items: list[LLMProseItem] = Field(default_factory=list)
    vocab_easy_template: str = ""                 # 어휘 양자택일 (하: 반의어 뚜렷)
    vocab_easy_items: list[LLMProseItem] = Field(default_factory=list)
    ref_template: str = ""                        # 대명사 지칭 선택
    ref_items: list[LLMProseItem] = Field(default_factory=list)


class LLMProsePack(BaseModel):
    title: str = ""
    subtitle: str = ""
    sentences: list[LLMProseSentence] = Field(default_factory=list)


# 워크시트 유형 정의. 어휘는 난도 상/하 두 종을 모두 낸다.
_WORKSHEET_DEFS = [
    ("grammar", "어법 양자택일", "둘 중 어법상 알맞은 것을 고르시오.", False,
     "grammar_template", "grammar_items"),
    ("form", "어형 변형", "각 빈칸에 괄호 안의 단어를 문맥에 맞게 알맞은 형태로 바꾸어 쓰시오. "
     "(어형 변화가 필요 없는 경우도 있음)", True, "form_template", "form_items"),
    ("vocab_easy", "어휘 양자택일 (하)", "둘 중 문맥상 알맞은 것을 고르시오. (난도 하)", False,
     "vocab_easy_template", "vocab_easy_items"),
    ("vocab", "어휘 (상)", "셋 중 문맥상 알맞은 것 '두 개'를 고르시오. (난도 상)", False,
     "vocab_template", "vocab_items"),
    ("ref", "대명사 (지칭 선택)", "밑줄 친 대명사·지시어가 가리키는 대상을 [ ]에서 고르시오.", False,
     "ref_template", "ref_items"),
]


def _ref_candidates(display: str) -> list[str]:
    """지칭 보기('= [ A / B / C ]')에서 후보 목록을 뽑는다."""
    inside = display.split("[", 1)[-1].rsplit("]", 1)[0] if "[" in display else display
    return [c.strip() for c in inside.split("/")]


def _ref_answer_in_display(answer: str, display: str) -> bool:
    """지칭 문항의 정답이 보기('= [ A / B / C ]') 안에 실제로 있는지 확인(출제 오류 방지)."""
    a = (answer or "").strip()
    if not a:
        return False
    return a in _ref_candidates(display)


import re as _re
_HANGUL = _re.compile(r"[가-힣]")
_REF_ALLOWED_KO = {"앞 문장", "앞 문장의 내용", "앞문장"}


def _ref_candidates_clean(display: str) -> bool:
    """지칭 보기가 규칙에 맞는지: 영어 명사구 또는 '앞 문장'만 허용(한글 보기 혼입 방지).

    대명사가 '행동·구'(예: '양쪽 살피기')를 가리켜 영어 명사구 보기가 없을 때 LLM 이 한글을
    보기에 끼워 넣는 출제오류를 막는다. 허용된 '앞 문장' 외에 한글이 든 보기가 있으면 False.
    """
    cands = _ref_candidates(display)
    if len(cands) < 2:
        return False
    for c in cands:
        if _HANGUL.search(c) and c not in _REF_ALLOWED_KO:
            return False
    return True


def _align(order: list[str], items: list[LLMProseItem]):
    """자리표시자(등장 순서) ↔ items 매핑. id 가 맞으면 그 매핑을, 아니면 순서대로."""
    by_id = {it.id: it for it in items}
    if set(order) == set(by_id) and len(order) == len(items):
        return [(pid, by_id[pid]) for pid in order]
    return list(zip(order, items))


def _vocab_template_lossy(en: str, template: str, items) -> bool:
    """어휘 template 이 원문(en)의 단어를 '잃어버렸는지' 검사한다.

    어휘 유형은 answer 의 '원문'(첫 항목)이 문장 속 실제 단어와 같아야 한다. 따라서
    'template 에서 {{Pn}} 을 뺀 단어들' + '각 정답의 원문 단어'를 합치면 en 의 내용어를 모두
    포함해야 한다. 그렇지 않으면(예: 보기 박스가 엉뚱한 자리에 놓여 원래 단어가 사라짐,
    또는 어떤 단어가 통째로 누락) '단어 소실'로 보고 True 를 돌려준다.
    보수적으로, '4글자 이상 내용어'가 하나라도 빠졌을 때만 소실로 판정한다.
    """
    import re
    words = lambda t: [w.lower() for w in re.findall(r"[A-Za-z]+", t)]
    have = set(words(re.sub(r"\{\{\s*\w+\s*\}\}", " ", template)))
    for it in items:
        have.update(words((it.answer or "").split("/")[0]))
    return any(len(w) >= 4 and w not in have for w in words(en))


def _ref_is_expletive(template: str, pid: str) -> bool:
    """지칭 대상이 없는 '가주어 it / 유도부사 there' 를 출제한 경우인지 판정(출제 오류).

    예: "It turns out that …", "It is important that …", "There is …" — it/there 는 특정 명사를
    가리키지 않으므로 지칭 문제로 낼 수 없다.
    """
    import re
    m = re.search(r"\b(it|there)\s*\{\{\s*" + re.escape(pid) + r"\s*\}\}\s*"
                  r"(turns\s+out|seems|appears|happens|follows|is|are|was|were|takes|took|matters)\b",
                  template, re.IGNORECASE)
    if not m:
        return False
    pron, verb = m.group(1).lower(), m.group(2).lower().split()[0]
    if pron == "there":
        return True                       # 유도부사 there
    if verb in ("turns", "seems", "appears", "happens", "follows"):
        return True                       # it turns out / seems / appears …
    # it is/was/takes … 는 뒤에 that/to 절이 이어지면 가주어(it is … that / it takes … to)
    tail = template[m.end():m.end() + 60]
    return bool(re.search(r"\b(that|to)\b", tail))


def _ref_template_lossy(en: str, template: str) -> bool:
    """지칭 template 은 원문(en)에 {{Pn}} 만 '삽입'하므로 en 의 모든 단어를 담아야 한다.

    대명사를 지우고 {{Pn}} 으로 대체했거나(대명사 소실), 명사(예: 'technologies')가 누락되는 등
    원문 단어가 사라지면 True. 지칭은 원문 그대로(어형 변화 없음)라 '3글자 이상' 단어가 사라졌을 때만
    소실로 본다(of/to/in 등 2글자 기능어 하나 누락으로 멀쩡한 문항을 버리지 않도록 보수적으로).
    """
    import re
    words = lambda t: [w.lower() for w in re.findall(r"[A-Za-z]+", t)]
    have = set(words(re.sub(r"\{\{\s*\w+\s*\}\}", " ", template)))
    return any(len(w) >= 3 and w not in have for w in words(en))


def renderable_ref_items(s: LLMProseSentence) -> list[LLMProseItem]:
    """이 문장에서 render 단계의 지칭 가드를 '통과해 실제로 출제될' ref 문항만 반환.

    _worksheet 의 ref 분기와 동일한 판정(자리표시자 손상·정답 보기 불일치·한글 혼입·
    가주어/there·원문 단어 소실)을 적용한다. 지칭이 '겉보기엔 있으나 전부 버려지는' 경우를
    _ensure_ref 가 감지해 재생성하도록, 실제 출제 가능한 문항 수를 세는 데 쓴다.
    """
    template = s.ref_template or s.en
    items_src = s.ref_items
    order = placeholders_in(template)
    if items_src and not order:          # template 손상 → 전부 버려짐
        return []
    surviving = [src for pid, src in _align(order, items_src)
                 if _ref_answer_in_display(src.answer, src.display)
                 and _ref_candidates_clean(src.display)
                 and not _ref_is_expletive(template, pid)]
    if surviving and _ref_template_lossy(s.en, template):   # 원문 단어 소실 → 버려짐
        return []
    return surviving


def renderable_ref_count(llm: LLMProsePack) -> int:
    """지문 전체에서 render 가드를 통과해 실제로 출제될 지칭 문항 수(추정)."""
    return sum(len(renderable_ref_items(s)) for s in llm.sentences)


# '주어 수일치만' 묻는 be/do/have 선택 → 난도가 낮아 출제 지양(프롬프트로 막아도 LLM 이 종종 냄).
#   is/are · does/do · has/have 는 '순수 수일치'라 렌더에서 드롭한다.
#   was/were 도 수일치이나 '가정법(if/as if/wish …)' 문맥이면 남긴다.
#   축약형(doesn't/don't·isn't/aren't·hasn't/haven't)도 순수 수일치라 함께 드롭한다.
_AGREEMENT_SETS = ({"is", "are"}, {"does", "do"}, {"has", "have"},
                   {"isn't", "aren't"}, {"doesn't", "don't"}, {"hasn't", "haven't"})
_WERE_SETS = ({"was", "were"}, {"wasn't", "weren't"})   # 가정법 소지 → 문맥 판단
_SUBJUNCTIVE = re.compile(r'\b(if|as if|as though|wish|wishe[sd]|wished|suppose|were to|rather)\b', re.I)


def _third_person_s(base: str, other: str) -> bool:
    """other 가 base 의 3인칭 단수형인지(run→runs, watch→watches, vary→varies)."""
    if other in (base + "s", base + "es"):
        return True
    if base.endswith("y") and len(base) >= 2 and base[-2] not in "aeiou" and other == base[:-1] + "ies":
        return True
    return False


def _grammar_template_lossy(en: str, template: str, items) -> bool:
    """어법 template 이 원문(en)의 '내용어'를 통째로 잃었는지 검사한다.

    template 의 각 {{Pn}} 을 '정답'으로 되돌린 '완성 문장'이 en 의 4자 이상 내용어를 모두
    포함해야 한다. 그렇지 않으면(예: 본동사 'appears' 가 통째로 누락) True — 렌더에서 원문으로
    되돌리고 그 문장의 어법 문항을 버린다(깨진 문장 노출 방지).
    """
    solved = template
    for it in items:
        solved = solved.replace("{{" + it.id + "}}", (it.answer or "").split("/")[0].strip())
    words = lambda t: [w.lower() for w in re.findall(r"[A-Za-z]+", t)]
    have = set(words(solved))
    return any(len(w) >= 4 and w not in have for w in words(en))


def _is_agreement_choice(display: str, template: str = "") -> bool:
    """어법 보기 '[ A / B ]' 가 순수 주어-수일치 쌍인지.

    - be/do/have 불규칙: is/are · does/do · has/have
    - was/were: 수일치이나 가정법(if/as if/wish/were to …) 문맥이면 남긴다.
    - 일반동사 3인칭 단수: 한쪽이 다른 쪽의 -s/-es/-ies 형(run/runs, vary/varies).
      단, 짧은 대명사 오탐(it/its) 방지를 위해 원형 길이 3 이상일 때만.
    """
    inside = display.split("[", 1)[-1].rsplit("]", 1)[0] if "[" in display else display
    # 아포스트로피 정규화(’ → ')로 축약형 비교를 일관되게 한다.
    opts = [c.strip().lower().replace("’", "'") for c in inside.split("/") if c.strip()]
    s = set(opts)
    if s in _AGREEMENT_SETS:
        return True
    if s in _WERE_SETS:                          # was/were·wasn't/weren't: 가정법 문맥이면 유지
        return not _SUBJUNCTIVE.search(template or "")
    if len(opts) == 2:
        a, b = sorted(opts, key=len)            # a = 더 짧은 쪽(원형)
        if len(a) >= 3 and _third_person_s(a, b):
            return True
    return False


def _worksheet(llm: LLMProsePack, wtype: str, label: str, instr: str,
               write: bool, tkey: str, ikey: str) -> ProseWorksheet:
    sents: list[PSentence] = []
    for s in llm.sentences:
        template = getattr(s, tkey) or s.en
        items_src = getattr(s, ikey)
        if write:
            # 어형: 자리표시자 옆에 정답 어형이 그대로 남아 중복되는 경우
            #   (예: "(change) changed", "(appear) (end) end")를 제거한다(통합카드와 동일 처리).
            #   + 정답과 무관하게 '(원형)의 활용형'이 남은 경우(복합수동 "comforted" 등)도 제거.
            for src in items_src:
                marker = "{{" + src.id + "}}"
                template = textutil.dedup_placeholder(template, marker, src.answer)
                base = (src.display or "").strip("() ").split()[0] if src.display else ""
                template = textutil.strip_form_leftover(template, marker, base)
        order = placeholders_in(template)
        # 안전장치: 문항(items)은 있는데 template 에 정상 자리표시자({{Pn}})가 하나도 없으면
        #   template 이 손상된 것(예: LLM 이 "P1}}" 같은 깨진 문자열 반환 → "P P1}}" 노출)이다.
        #   이 경우 깨진 template 대신 '원문(en)'을 보여 주고 문항은 버린다(문장은 온전히 보이게).
        if items_src and not order:
            template = s.en
        # 안전장치: 어휘 유형에서 보기 박스가 엉뚱한 자리에 놓이거나 단어가 누락돼 원문 단어가
        #   사라진 경우, 깨진 template 대신 원문(en)을 보여 주고 문항을 버린다.
        #   (예: "not able to their mood" — contain 소실 / "outside their part" — rational 소실.
        #    후자는 보기 박스도 없이 단어만 빠져 items 가 비므로, items 유무와 무관하게 검사한다.)
        elif wtype in ("vocab", "vocab_easy") and \
                _vocab_template_lossy(s.en, template, items_src):
            template = s.en
            items_src = []
        order = placeholders_in(template)
        # 자리표시자가 하나도 없으면(출제 없음/손상) 원문만 두고 items 는 비운다.
        # 선택형(어법·어휘·지칭)은 보기 순서를 섞어 정답 위치 쏠림을 없앤다(어형은 제외).
        pitems = [PItem(id=pid,
                        display=(src.display if write
                                 else textutil.shuffle_choices(src.display, f"{s.no}:{pid}:{src.display}")),
                        answer=src.answer, write=write, gloss=getattr(src, "gloss", ""))
                  for pid, src in _align(order, items_src)]
        if wtype == "grammar":
            # 수일치 지양: 순수 주어-수일치 쌍 문항을 버린다(was/were 는 가정법 문맥이면 유지).
            #   ★ 버린 문항의 {{Pn}} 은 '정답'으로 복원해 문장에 구멍(gap)이 생기지 않게 한다.
            kept = []
            for it in pitems:
                if _is_agreement_choice(it.display, template):
                    template = template.replace("{{" + it.id + "}}", it.answer)
                else:
                    kept.append(it)
            pitems = kept
            # LLM 이 원문 단어를 통째로 누락한 경우(예: 본동사 'appears' 소실) → 원문 복구 + 문항 버림
            if pitems and _grammar_template_lossy(s.en, template, pitems):
                template = s.en
                pitems = []
        if wtype == "ref":
            # 안전장치: 지칭 정답이 보기 안에 없거나(출제 오류) 보기에 한글이 섞이면
            #   (예: [ Vision / the street / 양쪽 살피기 ]) 그 문항을 버린다.
            #   남은 자리표시자는 렌더에서 제거되어 대명사가 든 문장은 그대로 보인다.
            pitems = [it for it in pitems
                      if _ref_answer_in_display(it.answer, it.display)
                      and _ref_candidates_clean(it.display)
                      and not _ref_is_expletive(template, it.id)]   # 가주어 it/there 제외
            # 안전장치: 지칭은 원문에 {{Pn}} 만 삽입해야 하는데 원문 단어가 사라졌으면
            #   (대명사 소실·명사 누락) 문항을 버리고 원문(en)을 그대로 보여 준다.
            if pitems and _ref_template_lossy(s.en, template):
                pitems = []
            # ★ 남은 지칭 문항이 하나도 없으면 template 을 원문(en)으로 되돌린다.
            #   LLM 이 원문에 없던 대명사(예: "our memories they are")를 삽입한 뒤 문항이 탈락하면
            #   그 잔여가 문장에 남는데, en 으로 복구해 깨끗한 문장을 보인다.
            if not pitems:
                template = s.en
        # ★ 문장당 출제 개수 상한(최대 4개) 강제 — 어법·어휘 하/상.
        #   프롬프트를 어겨 5개 이상 오면 읽기 순서로 앞 4개만 남기고, 버린 문항의 {{Pn}} 은
        #   '정답(어휘 상은 원문)'으로 복원해 문장에 구멍이 생기지 않게 한다.
        if wtype in _COUNT_LIMITED and len(pitems) > _MAX_PER_SENT:
            keep, drop = pitems[:_MAX_PER_SENT], pitems[_MAX_PER_SENT:]
            for it in drop:
                restore = (it.answer.split("/")[0].strip()
                           if wtype == "vocab" else it.answer)
                template = template.replace("{{" + it.id + "}}", restore)
            pitems = keep
        sents.append(PSentence(no=s.no, template=template, ko=s.ko, items=pitems))
    return ProseWorksheet(wtype=wtype, label=label, instruction=instr, sentences=sents)


def build_prose_pack(llm: LLMProsePack, header: str, title: str, subtitle: str) -> ProsePack:
    """검증된 LLM 응답 -> 어법·어형·어휘·한글해석 4종 워크시트를 담은 ProsePack."""
    # 안전장치: 본문(en)이 빈 문장은 모든 유형에서 '번호만 있는 빈 행'으로 렌더되므로 제외한다.
    llm.sentences = [s for s in llm.sentences if (s.en or "").strip()]
    # 안전장치: LLM 이 같은 문장을 중복 생성한 경우(예: 평문본 + 보기본) → 문항이 더 많은 쪽만 남긴다.
    def _n(s):
        return re.sub(r"\s+", " ", (s.en or "").strip().lower())

    def _cnt(s):
        return (len(s.grammar_items) + len(s.form_items) + len(s.vocab_items)
                + len(s.vocab_easy_items) + len(s.ref_items))
    best: dict = {}
    for s in llm.sentences:
        k = _n(s)
        if k not in best or _cnt(s) > _cnt(best[k]):
            best[k] = s
    llm.sentences = [s for s in llm.sentences if best.get(_n(s)) is s]
    worksheets = [_worksheet(llm, *d) for d in _WORKSHEET_DEFS]
    # 한글 해석 연습: 표기 없이 원문 + 해석만
    translate = ProseWorksheet(
        wtype="translate", label="한글 해석 연습", instruction="주어진 영문을 해석하시오.",
        sentences=[PSentence(no=s.no, template=s.en, ko=s.ko, items=[]) for s in llm.sentences])
    worksheets.append(translate)
    return ProsePack(header=header, title=title or "", subtitle=subtitle or "",
                     worksheets=worksheets)


def count_shortfalls(pack: ProsePack, min_per: int = _MIN_PER_SENT) -> dict:
    """문장당 최소 개수(min_per) 미달 진단.

    어법·어휘(하/상)에서 '문항 수 < min_per' 인 문장을 유형별로 모아 돌려준다.
    자동으로 고치지 않는다(없는 문항은 만들 수 없으므로) — 어느 문장이 부족한지 '알려' 주는 용도.
    반환: { "grammar": [(문장번호, 문항수), ...], ... }  (미달 없으면 빈 dict)
    """
    out: dict = {}
    for ws in pack.worksheets:
        if ws.wtype not in _COUNT_LIMITED:
            continue
        short = [(s.no, len(s.items)) for s in ws.sentences if len(s.items) < min_per]
        if short:
            out[ws.wtype] = short
    return out


def format_count_report(packs, min_per: int = _MIN_PER_SENT, max_per: int = _MAX_PER_SENT,
                        label: str = "") -> str:
    """여러 ProsePack 의 '문항 개수 점검' 리포트 문자열(사람이 읽는 요약)."""
    lines = []
    for idx, pk in enumerate(packs or [], start=1):
        sf = count_shortfalls(pk, min_per=min_per)
        tag = (pk.label or f"지문 {idx}") if hasattr(pk, "label") else f"지문 {idx}"
        if not sf:
            lines.append(f"  [{tag}] 문장당 {min_per}~{max_per}개 규칙 만족 ✔")
            continue
        for wtype, short in sf.items():
            name = _COUNT_LABELS.get(wtype, wtype)
            total = len(next(w for w in pk.worksheets if w.wtype == wtype).sentences)
            detail = ", ".join(f"S{no}={cnt}개" for no, cnt in short)
            lines.append(f"  [{tag}] {name}: {total}문장 중 {len(short)}문장 미달({min_per} 미만) — {detail}")
    head = f"[문항 개수 점검] 문장당 최소 {min_per}·최대 {max_per}개"
    if label:
        head += f" · {label}"
    return head + "\n" + ("\n".join(lines) if lines else "  (해당 유형 없음)")


def validate_llm_prose(llm: LLMProsePack, min_sentences: int = 1) -> None:
    """산문 워크시트 응답 검증. 자리표시자 수와 items 수가 달라도 build 가 '등장 순서'로
    가능한 만큼만 짝지어 렌더하므로 그 부분은 실패시키지 않는다.

    다만 '문장 자체'가 비었거나(0개) 지문 문장 수에 비해 지나치게 적으면(예: 6종 mega-call 이
    도중에 degenerate 하게 1문장만 반환) 모든 유형 워크시트가 통째로 비므로, min_sentences 미만이면
    실패로 보고 재요청(client 가 위반 피드백과 함께 재시도)한다.
    """
    if not llm.sentences:
        raise ValueError("산문 워크시트 문장이 비어 있습니다.")
    if len(llm.sentences) < min_sentences:
        raise ValueError(
            f"지문 문장 수에 비해 응답 문장이 너무 적습니다"
            f"(응답 {len(llm.sentences)}개 < 최소 {min_sentences}개). "
            f"지문의 '모든 문장'을 등장 순서대로 하나도 빠뜨리지 말고 포함하세요."
        )


# ── 렌더 ─────────────────────────────────────────────────────────────
_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)),
                   autoescape=select_autoescape(["html", "xml", "j2"]))

_WCLASS = {"form": "wf", "grammar": "wg", "vocab": "wv", "vocab_easy": "wv", "ref": "wr"}


def _item_html(it: PItem, wtype: str) -> str:
    if it.write:  # 어형 변형: (원형) + 쓰는 밑줄
        return (f'<span class="pf">{escape(it.display)}</span>'
                f'<span class="pw"></span>')
    # 양자택일: [ A / B ] 박스
    cls = _WCLASS.get(wtype, "wg")
    return f'<span class="pc {cls}">{escape(it.display)}</span>'


def render_prose(s: PSentence, wtype: str) -> Markup:
    import re
    html = str(escape(s.template))
    by_id = {it.id: it for it in s.items}
    for pid in placeholders_in(s.template):
        it = by_id.get(pid)
        if it:
            html = html.replace("{{" + pid + "}}", _item_html(it, wtype))
    # 짝이 없어 남은 자리표시자가 그대로 노출되지 않도록 제거
    html = re.sub(r"\{\{\s*\w+\s*\}\}", "", html)
    # 방어: 부분 손상으로 남은 조각(예: "P1}}", "{{P2")도 노출되지 않게 정리한다.
    #   중괄호에 붙은 자리표시자형 토큰(대문자+숫자)과 남은 낱개 중괄호만 제거(일반 본문은 건드리지 않음).
    html = re.sub(r"[A-Z]\d+\s*\}{1,2}", "", html)   # "P1}}", "P2}"
    html = re.sub(r"\{{1,2}\s*[A-Z]\d+", "", html)   # "{{P1", "{P2"
    html = html.replace("{{", "").replace("}}", "")
    return Markup(html)


_env.filters["render_prose"] = render_prose


def render_prose_html(pack: ProsePack, footer_note: str = "", show_ko: bool = True,
                      section: str = "all") -> str:
    from . import branding
    return _env.get_template("prose.html.j2").render(
        pack=pack, footer_note=footer_note, show_ko=show_ko, section=section,
        font_css=branding.font_face_css())


def render_prose_pdf(pack: ProsePack, out_path: str | Path, footer_note: str = "",
                     show_ko: bool = True, section: str = "all") -> Path:
    from playwright.sync_api import sync_playwright

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = render_prose_html(pack, footer_note, show_ko=show_ko, section=section)
    html_path = out_path.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")

    footer = footer_note.strip() if footer_note and footer_note.strip() else DEFAULT_FOOTER
    exe = _chromium_executable()
    launch_kw = {"executable_path": exe} if exe else {}
    with sync_playwright() as p:
        b = _launch_chromium(p, launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        _page_ready(pg)
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "12mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
