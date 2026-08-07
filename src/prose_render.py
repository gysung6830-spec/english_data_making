"""단일 유형 산문 워크시트 (어법 양자택일 / 어형 변형 / 어휘 양자택일).

지문 전체를 산문(번호 매긴 문장 목록)으로 두고, 한 가지 기능의 표기만 인라인으로 넣는다.
  - 어형 변형(form): (동사원형) + 쓰는 밑줄
  - 어법·어휘 양자택일(choice): [ A / B ] 박스
HTML → PDF 는 Playwright(Chromium).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from pydantic import BaseModel, Field

from .blanks_schemas import placeholders_in  # {{Pn}} 재사용
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER, _page_ready, _launch_chromium

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"


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


def _worksheet(llm: LLMProsePack, wtype: str, label: str, instr: str,
               write: bool, tkey: str, ikey: str) -> ProseWorksheet:
    sents: list[PSentence] = []
    for s in llm.sentences:
        template = getattr(s, tkey) or s.en
        items_src = getattr(s, ikey)
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
        pitems = [PItem(id=pid, display=src.display, answer=src.answer, write=write,
                        gloss=getattr(src, "gloss", ""))
                  for pid, src in _align(order, items_src)]
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
                template = s.en
                pitems = []
        sents.append(PSentence(no=s.no, template=template, ko=s.ko, items=pitems))
    return ProseWorksheet(wtype=wtype, label=label, instruction=instr, sentences=sents)


def build_prose_pack(llm: LLMProsePack, header: str, title: str, subtitle: str) -> ProsePack:
    """검증된 LLM 응답 -> 어법·어형·어휘·한글해석 4종 워크시트를 담은 ProsePack."""
    worksheets = [_worksheet(llm, *d) for d in _WORKSHEET_DEFS]
    # 한글 해석 연습: 표기 없이 원문 + 해석만
    translate = ProseWorksheet(
        wtype="translate", label="한글 해석 연습", instruction="주어진 영문을 해석하시오.",
        sentences=[PSentence(no=s.no, template=s.en, ko=s.ko, items=[]) for s in llm.sentences])
    worksheets.append(translate)
    return ProsePack(header=header, title=title or "", subtitle=subtitle or "",
                     worksheets=worksheets)


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
