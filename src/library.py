"""자료 라이브러리 — 분석한 지문을 '자산'으로 쌓아 두는 층.

교습소를 열 때 가장 값나가는 재산은 PDF 파일 더미가 아니라
**재사용 가능한 분석 데이터**다. PDF 는 언제든 다시 뽑을 수 있지만,
API 를 태워 만든 분석 결과(Report JSON)는 다시 만들면 돈과 시간이 든다.

그래서 이 모듈은 지문 하나를 아래 세 조각으로 보관한다.

    library/passages/<자료ID>/
        meta.yaml      메타데이터(레벨·유형·출처·어휘목록·사용이력)
        report.json    분석 결과 원본 → 언제든 PDF 재생성 가능
        source.txt     지문 원문(검색·중복확인용)

그리고 전체 목록을 `library/catalog.json`(기계용)과
`library/CATALOG.md`(사람용)로 자동 정리한다.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml
from pydantic import BaseModel, Field

from .config import ROOT
from .schemas import Report

LIBRARY_DIR = ROOT / "library"
PASSAGE_DIR = LIBRARY_DIR / "passages"
CATALOG_JSON = LIBRARY_DIR / "catalog.json"
CATALOG_MD = LIBRARY_DIR / "CATALOG.md"

# 자료 유형 코드 (자료ID 가운데 토막에 들어간다)
CATEGORIES: dict[str, str] = {
    "textbook": "TXT",    # 학교 교과서
    "school":   "SCH",    # 내신 기출/학교 프린트
    "mock":     "MOCK",   # 모의고사
    "csat":     "CSAT",   # 수능 기출
    "ebs":      "EBS",    # EBS 연계교재
    "book":     "BOOK",   # 시중 문제집·원서
    "custom":   "CUS",    # 자체 제작 지문
}

STATUSES = ("draft", "ready", "retired")


# ---------------------------------------------------------------------------
# 본문 지문(fingerprint) — 같은 지문을 두 번 사서 두 번 분석하는 사고를 막는다
# ---------------------------------------------------------------------------
def body_hash(text: str) -> str:
    """대소문자·공백·문장부호를 지운 영숫자만으로 지문 지문(fingerprint)을 만든다.

    숫자는 남긴다 — 연도·통계 수치만 다른 개정판 지문을 같은 지문으로 보면
    한쪽이 라이브러리에 등록되지 못한다.
    """
    norm = re.sub(r"[^a-z0-9]", "", (text or "").lower())
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]


def _slug(text: str, limit: int = 40) -> str:
    s = re.sub(r"[^0-9A-Za-z가-힣]+", "-", (text or "").strip()).strip("-")
    return s[:limit] or "passage"


# ---------------------------------------------------------------------------
# 메타데이터 스키마
# ---------------------------------------------------------------------------
class Stats(BaseModel):
    words: int = 0            # 본문 단어 수
    sentences: int = 0        # 문장 수
    avg_sentence: float = 0   # 문장당 평균 단어 수 (체감 난도의 1차 지표)
    vocab: int = 0            # 핵심 어휘 개수
    grammar: int = 0          # 문법 포인트 개수


class Material(BaseModel):
    """지문 자료 한 건의 메타데이터."""
    id: str
    title: str
    theme_ko: str = ""
    level: str = ""                       # curriculum/levels.yaml 의 레벨 코드
    category: str = "custom"              # CATEGORIES 의 키
    source: str = ""                      # 출처 상세(교재명·회차 등)
    item_no: str = ""                     # 원본 문항 번호
    genre: str = ""                       # logic | emotional
    tags: list[str] = Field(default_factory=list)
    status: str = "ready"
    added: str = ""
    hash: str = ""
    stats: Stats = Field(default_factory=Stats)
    vocab: list[str] = Field(default_factory=list)          # 핵심 어휘(누적 관리용)
    grammar_points: list[str] = Field(default_factory=list)
    used_in: list[str] = Field(default_factory=list)        # "반코드/회차" 사용 이력
    notes: str = ""

    @property
    def dir(self) -> Path:
        return PASSAGE_DIR / self.id

    @property
    def report_path(self) -> Path:
        return self.dir / "report.json"


# ---------------------------------------------------------------------------
# 라이브러리
# ---------------------------------------------------------------------------
class Library:
    """`library/` 폴더를 다루는 얇은 저장소 객체."""

    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root else LIBRARY_DIR
        self.passages = self.root / "passages"
        self.passages.mkdir(parents=True, exist_ok=True)

    # -- 읽기 --------------------------------------------------------------
    def all(self) -> list[Material]:
        """저장된 모든 자료의 메타데이터를 ID 순으로 반환."""
        out: list[Material] = []
        for meta in sorted(self.passages.glob("*/meta.yaml")):
            try:
                data = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
                out.append(Material.model_validate(data))
            except Exception:
                continue    # 손상된 한 건이 전체 조회를 막지 않게
        return out

    def get(self, material_id: str) -> Material | None:
        meta = self.passages / material_id / "meta.yaml"
        if not meta.exists():
            return None
        return Material.model_validate(
            yaml.safe_load(meta.read_text(encoding="utf-8")) or {})

    def load_report(self, material_id: str) -> Report:
        """저장해 둔 분석 결과를 그대로 되살린다(→ PDF 재생성 가능)."""
        path = self.passages / material_id / "report.json"
        if not path.exists():
            raise FileNotFoundError(f"분석 결과가 없습니다: {material_id}")
        return Report.model_validate_json(path.read_text(encoding="utf-8"))

    def load_reports(self, ids: Iterable[str]) -> list[Report]:
        return [self.load_report(i) for i in ids]

    def find_by_hash(self, h: str) -> Material | None:
        return next((m for m in self.all() if m.hash == h), None)

    # -- 쓰기 --------------------------------------------------------------
    def next_id(self, level: str, category: str) -> str:
        code = CATEGORIES.get(category, "CUS")
        level = (level or "NA").upper()
        prefix = f"{level}-{code}-"
        used = [int(p.name[len(prefix):]) for p in self.passages.iterdir()
                if p.is_dir() and p.name.startswith(prefix)
                and p.name[len(prefix):].isdigit()]
        return f"{prefix}{(max(used) + 1) if used else 1:04d}"

    def add(self, report: Report, *, level: str, category: str = "custom",
            source: str = "", tags: Iterable[str] | None = None,
            status: str = "ready", notes: str = "",
            body: str = "", allow_duplicate: bool = False) -> tuple[Material, bool]:
        """분석 결과 하나를 라이브러리에 등록한다.

        반환: (자료, 신규등록여부). 이미 같은 지문이 있으면 (기존자료, False).
        """
        if category not in CATEGORIES:
            raise ValueError(
                f"모르는 자료 유형입니다: {category} "
                f"(가능: {', '.join(CATEGORIES)})")
        if status not in STATUSES:
            raise ValueError(f"status 는 {STATUSES} 중 하나여야 합니다.")

        text = body or _report_body(report)
        h = body_hash(text)
        if not allow_duplicate:
            dup = self.find_by_hash(h)
            if dup:
                return dup, False

        mid = self.next_id(level, category)
        mat = Material(
            id=mid,
            title=(report.title or "Untitled").strip(),
            theme_ko=(report.summary.theme_ko or "").strip(),
            level=(level or "").upper(),
            category=category,
            source=source or report.source or "",
            item_no=report.item_no or "",
            genre=report.structure.flow_type,
            tags=sorted({t.strip() for t in (tags or []) if t and t.strip()}),
            status=status,
            added=date.today().isoformat(),
            hash=h,
            stats=_stats_of(report, text),
            vocab=[v.word.strip() for v in report.vocab.items if v.word.strip()],
            grammar_points=[g.point.strip() for g in report.grammar.items
                            if g.point.strip()],
            notes=notes,
        )
        d = self.passages / mid
        d.mkdir(parents=True, exist_ok=True)
        (d / "report.json").write_text(
            report.model_dump_json(indent=2), encoding="utf-8")
        (d / "source.txt").write_text(text, encoding="utf-8")
        self.save_meta(mat)
        return mat, True

    def save_meta(self, mat: Material) -> Path:
        path = self.passages / mat.id / "meta.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(mat.model_dump(), allow_unicode=True, sort_keys=False),
            encoding="utf-8")
        return path

    def update(self, material_id: str, **fields: Any) -> Material:
        mat = self.get(material_id)
        if mat is None:
            raise KeyError(f"자료를 찾을 수 없습니다: {material_id}")
        for k, v in fields.items():
            if not hasattr(mat, k):
                raise KeyError(f"없는 필드입니다: {k}")
            setattr(mat, k, v)
        self.save_meta(mat)
        return mat

    def mark_used(self, material_id: str, marker: str) -> Material:
        """수업에서 쓴 이력을 남긴다(같은 자료를 다른 반에 또 쓸 때 참고)."""
        mat = self.get(material_id)
        if mat is None:
            raise KeyError(f"자료를 찾을 수 없습니다: {material_id}")
        if marker not in mat.used_in:
            mat.used_in.append(marker)
            self.save_meta(mat)
        return mat

    # -- 검색 · 통계 -------------------------------------------------------
    def search(self, *, level: str = "", category: str = "", tag: str = "",
               status: str = "", genre: str = "", q: str = "",
               unused: bool = False) -> list[Material]:
        """조건에 맞는 자료를 고른다. 빈 조건은 무시된다."""
        res = self.all()
        if level:
            res = [m for m in res if m.level.upper() == level.upper()]
        if category:
            res = [m for m in res if m.category == category]
        if tag:
            res = [m for m in res if tag in m.tags]
        if status:
            res = [m for m in res if m.status == status]
        if genre:
            res = [m for m in res if m.genre == genre]
        if unused:
            res = [m for m in res if not m.used_in]
        if q:
            ql = q.lower()
            res = [m for m in res if ql in m.title.lower()
                   or ql in m.theme_ko.lower()
                   or ql in m.source.lower()
                   or any(ql in t.lower() for t in m.tags)
                   or any(ql == w.lower() for w in m.vocab)]
        return res

    def vocab_index(self) -> dict[str, list[str]]:
        """단어 → 그 단어가 나온 자료 ID 목록. 누적 시험지·중복 점검에 쓴다."""
        idx: dict[str, list[str]] = {}
        for m in self.all():
            for w in m.vocab:
                idx.setdefault(w.lower(), []).append(m.id)
        return idx

    def stats(self) -> dict:
        mats = self.all()
        by_level: dict[str, int] = {}
        by_category: dict[str, int] = {}
        by_status: dict[str, int] = {}
        for m in mats:
            by_level[m.level or "미지정"] = by_level.get(m.level or "미지정", 0) + 1
            by_category[m.category] = by_category.get(m.category, 0) + 1
            by_status[m.status] = by_status.get(m.status, 0) + 1
        vocab_idx = self.vocab_index()
        return {
            "total": len(mats),
            "by_level": dict(sorted(by_level.items())),
            "by_category": dict(sorted(by_category.items())),
            "by_status": dict(sorted(by_status.items())),
            "vocab_unique": len(vocab_idx),
            "vocab_total": sum(len(v) for v in vocab_idx.values()),
            "unused": sum(1 for m in mats if not m.used_in),
        }

    # -- 색인 --------------------------------------------------------------
    def rebuild_catalog(self) -> tuple[Path, Path]:
        """catalog.json(기계용) + CATALOG.md(사람용)를 다시 만든다."""
        mats = self.all()
        payload = {
            "generated": date.today().isoformat(),
            "count": len(mats),
            "stats": self.stats(),
            "materials": [m.model_dump() for m in mats],
        }
        cj = self.root / "catalog.json"
        cj.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                      encoding="utf-8")

        lines = ["# 자료 카탈로그", "",
                 f"자동 생성: {payload['generated']} · 총 **{len(mats)}건**", "",
                 "> `python manage.py library index` 로 갱신됩니다. 직접 고치지 마세요.", ""]
        st = payload["stats"]
        lines += ["## 요약", "",
                  "| 구분 | 값 |", "|---|---|",
                  f"| 총 자료 | {st['total']} |",
                  f"| 고유 어휘 | {st['vocab_unique']} |",
                  f"| 아직 수업에 안 쓴 자료 | {st['unused']} |", ""]
        if st["by_level"]:
            lines += ["### 레벨별", "", "| 레벨 | 자료 수 |", "|---|---|"]
            lines += [f"| {k} | {v} |" for k, v in st["by_level"].items()]
            lines.append("")
        if st["by_category"]:
            lines += ["### 유형별", "", "| 유형 | 자료 수 |", "|---|---|"]
            lines += [f"| {k} | {v} |" for k, v in st["by_category"].items()]
            lines.append("")

        lines += ["## 전체 목록", "",
                  "| ID | 레벨 | 유형 | 제목 | 주제 | 어휘 | 문장 | 상태 | 등록일 |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for m in mats:
            lines.append(
                f"| `{m.id}` | {m.level} | {m.category} | {_md(m.title)} | "
                f"{_md(m.theme_ko)} | {m.stats.vocab} | {m.stats.sentences} | "
                f"{m.status} | {m.added} |")
        lines.append("")
        cm = self.root / "CATALOG.md"
        cm.write_text("\n".join(lines), encoding="utf-8")
        return cj, cm


# ---------------------------------------------------------------------------
# 보조
# ---------------------------------------------------------------------------
def _md(text: str) -> str:
    """표 셀이 깨지지 않도록 파이프·줄바꿈을 정리."""
    return (text or "").replace("|", "/").replace("\n", " ").strip() or "—"


def passage_metrics(report: Report) -> tuple[str, Stats]:
    """분석 결과에서 본문과 기본 통계를 뽑는다(레벨 추천 등 라이브러리 밖에서도 쓴다)."""
    body = _report_body(report)
    return body, _stats_of(report, body)


def _report_body(report: Report) -> str:
    """분석 결과에서 원문 본문을 복원한다(문장 english 를 이어 붙임)."""
    parts = [s.english.strip() for s in report.literal.sentences if s.english.strip()]
    if parts:
        return " ".join(parts)
    # english 가 비어 있으면 chunk 를 이어 붙여 복원
    return " ".join(" ".join(c.english.strip() for c in s.chunks)
                    for s in report.literal.sentences).strip()


def _stats_of(report: Report, body: str) -> Stats:
    n_sent = len(report.literal.sentences) or 1
    n_words = len(re.findall(r"[A-Za-z][A-Za-z'-]*", body))
    return Stats(
        words=n_words,
        sentences=len(report.literal.sentences),
        avg_sentence=round(n_words / n_sent, 1),
        vocab=len(report.vocab.items),
        grammar=len(report.grammar.items),
    )
