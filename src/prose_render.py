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
from .workbook_render import _chromium_executable, _footer_template, DEFAULT_FOOTER, _page_ready

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
        #   사라진 경우(예: "not able to their mood" — contain 소실), 깨진 template 대신 원문(en)을
        #   보여 주고 문항을 버린다(잘못된 문항보다 온전한 문장이 낫다).
        elif wtype in ("vocab", "vocab_easy") and items_src and \
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
                      and _ref_candidates_clean(it.display)]
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


def validate_llm_prose(llm: LLMProsePack) -> None:
    """산문 워크시트 응답 검증. 자리표시자 수와 items 수가 달라도 build 가 '등장 순서'로
    가능한 만큼만 짝지어 렌더하므로 실패시키지 않는다(문장만 비어 있으면 재요청)."""
    if not llm.sentences:
        raise ValueError("산문 워크시트 문장이 비어 있습니다.")


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
        b = p.chromium.launch(**launch_kw)
        pg = b.new_page()
        pg.goto(f"file://{html_path.resolve()}")
        _page_ready(pg)
        pg.pdf(path=str(out_path), format="A4",
               margin={"top": "12mm", "bottom": "16mm", "left": "14mm", "right": "14mm"},
               print_background=True, display_header_footer=True,
               header_template="<span></span>", footer_template=_footer_template(footer))
        b.close()
    return out_path
