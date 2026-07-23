"""기출 코퍼스 영구 적재 — input_corpus/ 의 기출 PDF에서 문장을 추출·태깅해
`data/corpus.jsonl` 에 '새 문장만' 누적한다(텍스트 해시로 중복 제거, 멱등).

핵심 아이디어
  - PDF는 저작권상 커밋하지 않지만, '추출된 기출 문장(사실 데이터)'은 커밋한다.
  - 그래서 PDF가 사라져도 코퍼스(교재의 '뇌')는 영구히 남는다.
  - 새 기출 PDF만 input_corpus/ 에 떨어뜨리고 다시 실행하면 → 새 문장만 쌓인다.

각 레코드(JSONL 한 줄):
  id            안정적 식별자(정규화 텍스트 해시)
  text          기출 문장 원문
  source        '2024 고3 11월 23번' 형태 출처
  year/grade/exam/item  출처 파싱값(item=문항번호, 없으면 null)
  codes         평가원 코드(인과·대조·동격 …) id 목록
  type          구문 유형(강조·도치·동격 …) id, 없으면 null
  difficulty    '중'/'고' 어림
  self_contained  select.passes() 통과 여부(앞 문장 없이 단독 출제 가능)

사용:
  python scripts/ingest_corpus.py            # 누적(기본)
  python scripts/ingest_corpus.py --stats    # 저장소 통계만
  python scripts/ingest_corpus.py --rebuild  # 저장소 비우고 처음부터 재적재
  python scripts/ingest_corpus.py --dir some_dir --out data/corpus.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from src.guide.codes import load_categories
from src.guide.corpus import collect_sourced, estimate_difficulty
from src.guide.select import passes
from src.guide.syntax import detect_type

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "input_corpus"
DEFAULT_OUT = ROOT / "data" / "corpus.jsonl"

_SRC = re.compile(r"(20\d\d)\s+(고\s*[123])\s+(\d{1,2})월(?:\s+(\d+)번)?")


def norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def make_id(text: str) -> str:
    return hashlib.sha1(norm_key(text).encode("utf-8")).hexdigest()[:12]


def parse_source(source: str) -> dict:
    m = _SRC.search(source)
    if not m:
        return {"year": None, "grade": None, "exam": None, "item": None}
    year, grade, month, item = m.groups()
    return {
        "year": int(year),
        "grade": grade.replace(" ", ""),
        "exam": f"{month}월",
        "item": int(item) if item else None,
    }


def detect_codes(sentence: str, categories) -> list[str]:
    hits: list[str] = []
    for cat in categories:
        for code in cat.codes:
            if code.matches(sentence):
                hits.append(cat.id)
                break
    return hits


def build_record(ss, categories) -> dict:
    text = ss.text.strip()
    meta = parse_source(ss.source)
    st = detect_type(text)
    return {
        "id": make_id(text),
        "text": text,
        "source": ss.source,
        **meta,
        "codes": detect_codes(text, categories),
        "type": st.id if st else None,
        "difficulty": estimate_difficulty(text),
        "self_contained": passes(text),
    }


def load_existing(out: Path) -> tuple[list[dict], set[str]]:
    records: list[dict] = []
    seen: set[str] = set()
    if out.exists():
        for line in out.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records.append(rec)
            seen.add(rec["id"])
    return records, seen


def write_all(out: Path, records: list[dict]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def print_stats(records: list[dict]) -> None:
    print(f"총 문장: {len(records)}")
    by_exam = Counter(f"{r['year']} {r['exam']}" if r["year"] else "미상" for r in records)
    print("시험별:")
    for k, v in sorted(by_exam.items()):
        print(f"  {k}: {v}")
    sc = sum(1 for r in records if r["self_contained"])
    print(f"자기완결(단독 출제 가능): {sc}  ({sc*100//max(len(records),1)}%)")
    code_ct = Counter(c for r in records for c in r["codes"])
    print("코드 분포:", dict(code_ct.most_common()))
    type_ct = Counter(r["type"] for r in records if r["type"])
    print("구문유형 분포:", dict(type_ct.most_common()))
    excl = sum(1 for r in records if r["item"] in {20, 25, 26, 27, 28, 29})
    print(f"제외대상(20·25~29번) 문항 문장: {excl} (생성 시 필터)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(DEFAULT_DIR), help="기출 PDF 디렉토리")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="코퍼스 저장소(JSONL)")
    ap.add_argument("--rebuild", action="store_true", help="저장소 비우고 재적재")
    ap.add_argument("--stats", action="store_true", help="저장소 통계만 출력")
    args = ap.parse_args()

    out = Path(args.out)

    if args.stats:
        records, _ = load_existing(out)
        print_stats(records)
        return

    records, seen = ([], set()) if args.rebuild else load_existing(out)
    before = len(records)

    categories = load_categories()
    sourced = collect_sourced(args.dir)
    added = 0
    for ss in sourced:
        rec = build_record(ss, categories)
        if rec["id"] in seen:
            continue
        seen.add(rec["id"])
        records.append(rec)
        added += 1

    write_all(out, records)
    print(f"적재 완료: 기존 {before} + 신규 {added} = {len(records)}  → {out}")
    print("-" * 48)
    print_stats(records)


if __name__ == "__main__":
    main()
