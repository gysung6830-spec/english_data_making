"""평가원 코드 목록(codes.yaml) 로더 + 매칭용 정규식 빌더."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CODES_PATH = Path(__file__).resolve().parent / "codes.yaml"

# 교재에서 제외할 기출 문항 번호(출처의 'N번'). 20/25/26/27/28/29 = 주장·도표·일치·안내문·어법.
EXCLUDE_ITEM_NOS = {20, 25, 26, 27, 28, 29}


def keep_source(src: str) -> bool:
    """출처의 문항 번호가 제외 대상(EXCLUDE_ITEM_NOS)이면 False(교재에서 뺀다)."""
    if not src:
        return True
    m = re.search(r"(\d+)\s*번", src)
    return not (m and int(m.group(1)) in EXCLUDE_ITEM_NOS)


@dataclass
class Code:
    en: str                 # 코드 어구 (A/B 자리표시자 포함 가능)
    ko: str
    dir: str = ""
    group: str = ""         # 소분류 라벨(방향 등)
    strict: str = ""        # "comma" 면 담화표지로만 매칭(뒤에 쉼표 필요)
    pattern: re.Pattern = field(default=None, repr=False)

    def matches(self, sentence: str) -> str | None:
        """문장에서 이 코드 어구가 등장하면, 매칭된 실제 부분 문자열을 반환."""
        m = self.pattern.search(sentence)
        return m.group(0) if m else None


@dataclass
class Category:
    id: str
    title: str
    day: int
    signal: str
    misread: str
    tip: str
    codes: list[Code]
    core_tip: str = ""      # 문장 핵심을 잡는 구체적 tip
    infer_tip: str = ""     # 문장/단어 유추법


def _build_pattern(en: str, strict: str = "") -> re.Pattern:
    """'be attributable to' / 'prefer A to B' 같은 코드 어구를 유연 매칭하는 정규식.

    - A / B 자리표시자는 '단어 몇 개'로 대체(비탐욕적).
    - 단어 사이 공백은 여러 공백/줄바꿈 허용.
    - be 동사는 활용형(is/are/was/were/been/being/be) 허용.
    - strict=="comma": 담화표지(that is, namely 등)로만 매칭 — 뒤에 쉼표가 와야 함.
      (관계사절 'a business that is ...' 같은 오탐 방지)
    """
    tokens = en.split()
    parts: list[str] = []
    for tok in tokens:
        if tok in ("A", "B"):
            parts.append(r"(?:\w+[\s,]+){0,4}\w+")   # 자리표시자: 최대 5단어
        elif tok == "be":
            # be동사 + (선택) 부사 삽입 허용: "is largely / is partly / are directly ..."
            parts.append(r"(?:is|are|was|were|been|being|be|am)(?:\s+\w+ly){0,2}")
        else:
            parts.append(re.escape(tok))
    body = r"\s+".join(parts)
    if strict == "comma":
        # 앞: 문장 시작/쉼표/세미콜론/콜론 뒤,  뒤: 쉼표
        return re.compile(r"(?:^|(?<=[,;:(]))\s*" + body + r"\s*,", re.IGNORECASE)
    return re.compile(r"\b" + body + r"\b", re.IGNORECASE)


def load_part0(path: str | Path | None = None):
    """part0.yaml → Part0 객체(0부 고정 콘텐츠)."""
    from .schemas import DepthDemo, Method, MethodDemo, Part0
    p = Path(path) if path else (Path(__file__).resolve().parent / "part0.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    methods = []
    for m in data.get("methods", []):
        demo = m.get("demo")
        methods.append(Method(
            step=m.get("step", ""), title=m.get("title", ""), idea=m.get("idea", ""),
            rule=m.get("rule", ""), ms_point=m.get("ms_point", ""),
            demo=MethodDemo(**demo) if demo else None,
        ))
    depth = [DepthDemo(kind=d["kind"], source=d.get("source", ""), goal=d.get("goal", ""),
                       passage=d.get("passage", ""), read=d.get("read", ""))
             for d in data.get("depth_demos", [])]
    return Part0(title=data.get("title", "3단계 읽기 엔진"), intro=data.get("intro", ""),
                 spine=data.get("spine", ""), methods=methods, depth_demos=depth,
                 tools=data.get("tools", []))


def load_abstract(path: str | Path | None = None):
    """abstract.yaml → 추상→구체 파트(4가지 구체화의 길 + 표현·기출예문)."""
    from .schemas import AbstractChapter, AbstractPart, FormulaRow, WorkExample
    p = Path(path) if path else (Path(__file__).resolve().parent / "abstract.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    aprac = load_abstract_practice()
    chapters = []
    for c in data.get("chapters", []):
        chapters.append(AbstractChapter(
            id=c["id"], title=c["title"], point=c.get("point", ""),
            strategy=c.get("strategy", ""),
            exprs=[FormulaRow(en=e["en"], ko=e["ko"]) for e in c.get("exprs", [])],
            examples=[WorkExample(en=e["en"], src=e.get("src", ""), cut=e.get("cut", ""))
                      for e in c.get("examples", []) if keep_source(e.get("src", ""))],
            practice=aprac.get(c["id"], []),
        ))
    return AbstractPart(title=data.get("title", "추상 → 구체"),
                        intro=data.get("intro", ""), chapters=chapters)


def load_part2_workbook(path: str | Path | None = None):
    """syntax_formula.yaml + SYNTAX_TYPES → 3 PART로 묶인 워크북형 Part2(해석공식 시각화)."""
    from .schemas import (Diagram, FormulaRow, Part2, PracticeItem,
                          PracticeSolution, SyntaxChapter, SyntaxPartGroup,
                          TrainStep, VocabItem, WorkExample)
    from .syntax import SYNTAX_TYPES
    p = Path(path) if path else (Path(__file__).resolve().parent / "syntax_formula.yaml")
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    tmap = {st.id: st for st in SYNTAX_TYPES}
    formulas = data.get("formulas", {})
    sprac = load_syntax_practice()

    def make_chapter(tid: str) -> SyntaxChapter | None:
        st = tmap.get(tid)
        f = formulas.get(tid, {})
        if not st:
            return None
        dia = f.get("diagram")
        diagram = None
        if dia:
            diagram = Diagram(symbol=dia.get("symbol", ""),
                              rows=[FormulaRow(en=r["en"], ko=r["ko"]) for r in dia.get("rows", [])])
        examples = [WorkExample(en=e["en"], src=e.get("src", ""), cut=e.get("cut", ""),
                                ab=e.get("ab", ""))
                    for e in f.get("examples", []) if keep_source(e.get("src", ""))]
        training = [TrainStep(level=t.get("level", ""), en=t.get("en", ""), ko=t.get("ko", ""))
                    for t in f.get("training", [])]
        # 실전적용: syntax_practice.yaml 우선, 없으면 syntax_formula 인라인
        practice = sprac.get(tid) or []
        if not practice:
            mc_n = sh_n = 0
            for pr in f.get("practice", []):
                kind = pr.get("kind", "mc")
                if kind == "mc":
                    mc_n += 1; no = mc_n
                else:
                    sh_n += 1; no = sh_n
                sol = pr.get("solution")
                practice.append(PracticeItem(
                    no=no, kind=kind, sentence=pr["sentence"],
                    source=pr.get("source", ""), prompt=pr.get("prompt", ""),
                    options=pr.get("options", []), answer_index=pr.get("answer_index", 0),
                    answer=pr.get("answer", ""),
                    vocab=[VocabItem(**v) for v in pr.get("vocab", [])],
                    solution=PracticeSolution(**sol) if sol else None,
                ))
        return SyntaxChapter(id=st.id, title=st.title, signal=st.signal, how=st.formula,
                             point=f.get("point", ""), strategy=f.get("strategy", ""),
                             diagram=diagram, examples=examples, training=training,
                             practice=practice, combat_tip=st.combat)

    groups = []
    for part in data.get("parts", []):
        chs = [c for c in (make_chapter(t) for t in part.get("types", [])) if c]
        groups.append(SyntaxPartGroup(id=part["id"], title=part["title"],
                                      subtitle=part.get("subtitle", ""),
                                      strategy=part.get("strategy", ""), chapters=chs))
    return Part2(title="패턴으로 익히는 실전해석",
                 intro="구문 유형을 '실전 해석 동작'이 같은 것끼리 묶었다. "
                 "해석공식을 눈으로 익히고, 같은 전략을 반복 적용한다.", groups=groups)


def _load_practice_map(path: Path) -> dict:
    """practice YAML(공통) → {id: [PracticeItem …]}. kind별 번호(객1.. / 주1..)."""
    from .schemas import PracticeItem, PracticeSolution, VocabItem
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, list] = {}
    for cid, items in (data.get("practice") or {}).items():
        lst = []
        mc_n = sh_n = 0
        for pr in items or []:
            if not keep_source(pr.get("source", "")):
                continue
            kind = pr.get("kind", "mc")
            if kind == "mc":
                mc_n += 1; no = mc_n
            else:
                sh_n += 1; no = sh_n
            sol = pr.get("solution")
            lst.append(PracticeItem(
                no=no, kind=kind, sentence=pr["sentence"], source=pr.get("source", ""),
                prompt=pr.get("prompt", ""), options=pr.get("options", []),
                answer_index=pr.get("answer_index", 0), answer=pr.get("answer", ""),
                vocab=[VocabItem(**v) for v in pr.get("vocab", [])],
                solution=PracticeSolution(**sol) if sol else None,
            ))
        out[cid] = lst
    return out


def load_codes_practice(path: str | Path | None = None) -> dict:
    """codes_practice.yaml → {카테고리 id: [PracticeItem …]} (1부 문제↔해설)."""
    p = Path(path) if path else (Path(__file__).resolve().parent / "codes_practice.yaml")
    return _load_practice_map(p)


def load_syntax_practice(path: str | Path | None = None) -> dict:
    """syntax_practice.yaml → {구문 type id: [PracticeItem …]} (3부 문제↔해설)."""
    p = Path(path) if path else (Path(__file__).resolve().parent / "syntax_practice.yaml")
    return _load_practice_map(p)


def load_abstract_practice(path: str | Path | None = None) -> dict:
    """abstract_practice.yaml → {추상 chapter id: [PracticeItem …]}."""
    p = Path(path) if path else (Path(__file__).resolve().parent / "abstract_practice.yaml")
    return _load_practice_map(p)


def load_categories(path: str | Path | None = None) -> list[Category]:
    p = Path(path) if path else CODES_PATH
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    cats: list[Category] = []
    for c in data.get("categories", []):
        codes: list[Code] = []
        # groups 형태(권장) 또는 codes 직접 형태 모두 지원
        raw_groups = c.get("groups")
        if raw_groups:
            for g in raw_groups:
                label = g.get("label", "")
                for item in g.get("codes", []):
                    strict = item.get("strict", "")
                    codes.append(Code(en=item["en"], ko=item.get("ko", ""),
                                      dir=item.get("dir", ""), group=label, strict=strict,
                                      pattern=_build_pattern(item["en"], strict)))
        else:
            for item in c.get("codes", []):
                strict = item.get("strict", "")
                codes.append(Code(en=item["en"], ko=item.get("ko", ""),
                                  dir=item.get("dir", ""), strict=strict,
                                  pattern=_build_pattern(item["en"], strict)))
        cats.append(Category(
            id=c["id"], title=c["title"], day=int(c.get("day", 0)),
            signal=c.get("signal", ""), misread=c.get("misread", ""),
            tip=c.get("tip", ""), codes=codes,
            core_tip=c.get("core_tip", ""), infer_tip=c.get("infer_tip", ""),
        ))
    return cats
