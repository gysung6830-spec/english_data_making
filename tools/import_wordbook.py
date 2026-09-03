"""단어 시험지 PDF 묶음(폴더·ZIP)을 한 번에 읽어 교재별 단어 JSON 으로 저장.

사용 예)
    # ZIP 하나를 통째로 (Day 범위는 PDF 안의 'Day 1~2' 를 읽어 자동 인식)
    python tools/import_wordbook.py "[Vocab Test] 능률보카 어원편.zip" \
        --book neungyul_eowon --source "능률보카 어원편 고등"

    # 낱개 PDF 들 + 시험지 PDF 까지 바로 생성
    python tools/import_wordbook.py 시험지폴더/ --book wm_complete \
        --source "Word Master 고등 Complete" --make-pdf --pdf-prefix "WM Complete"

- 단어 JSON 은 data/wordbook/<book>/dayXX_YY.json 으로 저장된다.
- 각 파일마다 '문항 수 / 번호 연속 여부' 를 검사해 결과를 표로 출력한다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_wordbook import extract  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _collect_pdfs(paths: list[Path], workdir: Path) -> list[Path]:
    """폴더·ZIP·PDF 를 받아 PDF 목록으로 편다(ZIP 은 임시 폴더에 푼다)."""
    pdfs: list[Path] = []
    for p in paths:
        if p.is_dir():
            pdfs += sorted(p.rglob("*.pdf"))
        elif p.suffix.lower() == ".zip":
            dest = workdir / p.stem
            dest.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(p) as z:
                z.extractall(dest)
            pdfs += sorted(dest.rglob("*.pdf"))
        elif p.suffix.lower() == ".pdf":
            pdfs.append(p)
    return pdfs


def day_of(pdf: Path) -> tuple[int, int] | None:
    """PDF 본문(없으면 파일명)에서 'Day 1~2' 같은 범위를 찾는다."""
    import pymupdf

    text = pymupdf.open(str(pdf))[0].get_text()
    for source in (text, pdf.stem):
        m = re.search(r"Day\s*(\d+)\s*~\s*(\d+)", source)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"Day[ _](\d+)", source)
        if m:
            return int(m.group(1)), int(m.group(1))
    return None


def label(a: int, b: int) -> tuple[str, str]:
    """(제목, 파일명 stem) — 1강씩 교재는 'Day 7' 처럼 한 번호로 적는다."""
    if a == b:
        return f"Day {a}", f"day{a:02d}"
    return f"Day {a}~{b}", f"day{a:02d}_{b:02d}"


def main() -> None:
    ap = argparse.ArgumentParser(description="시험지 PDF 묶음 → 교재별 단어 JSON")
    ap.add_argument("paths", nargs="+", type=Path, help="PDF / 폴더 / ZIP")
    ap.add_argument("--book", required=True, help="교재 폴더 이름 (예: neungyul_eowon)")
    ap.add_argument("--source", required=True, help="배지에 넣을 교재 이름")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="기본: data/wordbook/<book>")
    ap.add_argument("--make-pdf", action="store_true", help="시험지 PDF 까지 생성")
    ap.add_argument("--pdf-dir", type=Path, default=ROOT / "output")
    ap.add_argument("--pdf-prefix", default="", help="시험지 파일명 앞에 붙일 말 (기본: 교재 이름)")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    out_dir = args.out_dir or ROOT / "data" / "wordbook" / args.book
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        pdfs = _collect_pdfs(args.paths, Path(tmp))
        rows, skipped = [], []
        for pdf in pdfs:
            rng = day_of(pdf)
            if not rng:
                skipped.append((pdf.name, "Day 범위를 못 찾음"))
                continue
            title, stem = label(*rng)
            words = extract(pdf)
            if not words:
                skipped.append((pdf.name, "단어를 못 읽음"))
                continue
            (out_dir / f"{stem}.json").write_text(json.dumps(
                {"title": title, "source": args.source, "words": words},
                ensure_ascii=False, indent=2), encoding="utf-8")
            nos = [w["no"] for w in words]
            rows.append((title, stem, len(words), nos == list(range(1, len(words) + 1))))

    rows.sort(key=lambda r: r[1])
    for title, stem, n, ok in rows:
        print(f"  {title:<10} {n:>3}개 {'' if ok else '← 번호가 이어지지 않음'}")
    print(f"{len(rows)}개 저장 → {out_dir}")
    for name, why in skipped:
        print(f"  건너뜀: {name} ({why})")

    if args.make_pdf:
        from src.wordtest import render_wordtest_pdf   # noqa: E402

        prefix = args.pdf_prefix or args.source
        args.pdf_dir.mkdir(parents=True, exist_ok=True)
        for title, stem, _n, _ok in rows:
            data = json.loads((out_dir / f"{stem}.json").read_text(encoding="utf-8"))
            out = args.pdf_dir / f"{prefix}_{title.replace(' ', '').replace('~', '-')}_단어test.pdf"
            render_wordtest_pdf(data["words"], out,
                                badge=f"어휘 TEST · {args.source} · {title}", seed=args.seed)
        print(f"시험지 PDF {len(rows)}개 → {args.pdf_dir}")


if __name__ == "__main__":
    main()
