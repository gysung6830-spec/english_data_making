"""평가원 코드 목록(codes.yaml) 로더 + 매칭용 정규식 빌더."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

CODES_PATH = Path(__file__).resolve().parent / "codes.yaml"


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
    from .schemas import Method, MethodDemo, Part0
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
    return Part0(title=data.get("title", "3단계 읽기 엔진"), intro=data.get("intro", ""),
                 spine=data.get("spine", ""), methods=methods, tools=data.get("tools", []))


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
        ))
    return cats
