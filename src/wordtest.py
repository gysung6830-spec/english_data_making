"""단어 시험지(영→한 · 한→영) PDF 생성 — Ortica영어 하우스 서식.

단어 JSON( tools/extract_wordbook.py 로 만든 것 )을 넣으면
  1쪽: Ⅰ. 영단어 → 우리말 뜻 쓰기
  2쪽: Ⅱ. 우리말 뜻 → 영단어 쓰기 (첫 글자 힌트)
  3쪽: 정답
순서의 PDF 를 만든다.

사용 예)
    python -m src.wordtest data/wordbook/day03_04.json --out output/Day3-4_단어test.pdf
    python -m src.wordtest data/wordbook/*.json --out-dir output --seed 2
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"

FOOTER_NOTE = "©2026.Ortica영어.All rights reserved"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml", "j2"]),
)


def _rows(items: list[dict]) -> list[tuple]:
    """문항을 2열(왼쪽 위→아래, 오른쪽 위→아래)로 배치할 행 목록으로."""
    half = (len(items) + 1) // 2
    left, right = items[:half], items[half:]
    return [(left[i], right[i] if i < len(right) else None) for i in range(half)]


def _hint(word: str) -> str:
    """한→영 문항의 첫 글자 힌트: 'term' → 't' (원본 단어장 시험지와 같은 방식)."""
    w = word.strip()
    return w[0] if w else ""


def build_sections(words: list[dict], seed: int | None = 1, shuffle: bool = True,
                   hint: bool = True, split: int | None = None) -> list[dict]:
    """단어 목록을 '영→한' / '한→영' 두 섹션으로 나눈다.

    split: 앞에서 몇 개를 영→한 으로 쓸지(기본: 절반). 원본 시험지에서
           1~40번이 영→한, 41~80번이 한→영 이었으므로 기본은 **방향을 서로 바꿔**
           같은 단어를 반대 방향으로 다시 묻는다(뒤쪽 절반 → 영→한).
    """
    n = len(words)
    cut = n // 2 if split is None else split
    en2ko_src = words[cut:]     # 원본에서 '한→영' 이었던 단어들 → 이번엔 영→한
    ko2en_src = words[:cut]     # 원본에서 '영→한' 이었던 단어들 → 이번엔 한→영

    rng = random.Random(seed)
    if shuffle:
        en2ko_src = en2ko_src[:]
        ko2en_src = ko2en_src[:]
        rng.shuffle(en2ko_src)
        rng.shuffle(ko2en_src)

    en2ko = [{"qno": i + 1, "prompt": w["word"], "answer": w["meaning"], "hint": ""}
             for i, w in enumerate(en2ko_src)]
    ko2en = [{"qno": i + 1, "prompt": w["meaning"], "answer": w["word"],
              "hint": _hint(w["word"]) if hint else ""}
             for i, w in enumerate(ko2en_src)]

    sections = []
    if en2ko:
        sections.append({
            "no": "Ⅰ", "dir": "en2ko", "title": "영단어 → 우리말 뜻",
            "desc": f"다음 영단어의 우리말 뜻을 쓰세요. (총 {len(en2ko)}문항)",
            "questions": en2ko, "rows": _rows(en2ko),
        })
    if ko2en:
        sections.append({
            "no": "Ⅱ", "dir": "ko2en", "title": "우리말 뜻 → 영단어",
            "desc": ("다음 뜻에 해당하는 영단어를 쓰세요. (총 %d문항%s)"
                     % (len(ko2en), " · 첫 글자 힌트 제공" if hint else "")),
            "questions": ko2en, "rows": _rows(ko2en),
        })
    return sections


def render_wordtest_pdf(words: list[dict], out_path: str | Path, badge: str,
                        footer_note: str = FOOTER_NOTE, seed: int | None = 1,
                        shuffle: bool = True, hint: bool = True) -> Path:
    """단어 목록 → 시험지 PDF(문제 2쪽 + 정답 1쪽)."""
    from weasyprint import CSS, HTML

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sections = build_sections(words, seed=seed, shuffle=shuffle, hint=hint)
    html = _env.get_template("wordtest.html.j2").render(
        badge=badge, sections=sections, footer_note=footer_note)
    css = [CSS(filename=str(TEMPLATE_DIR / "styles.css")),      # 폰트 임베드
           CSS(filename=str(TEMPLATE_DIR / "wordtest.css"))]    # 하우스 서식(뒤가 우선)
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path), stylesheets=css)
    return out_path


def load_wordbook(path: str | Path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not data.get("words"):
        raise ValueError(f"{path}: 단어가 없습니다.")
    return data


def _badge(data: dict, override: str = "") -> str:
    if override:
        return override
    title = (data.get("title") or "").strip()
    source = (data.get("source") or "").strip()
    return f"어휘 TEST · {source} · {title}" if source else f"어휘 TEST · {title}"


def main() -> None:
    ap = argparse.ArgumentParser(description="단어 시험지(영→한·한→영) PDF 만들기")
    ap.add_argument("json", nargs="+", type=Path, help="단어 JSON 파일들")
    ap.add_argument("--out", type=Path, help="출력 PDF 경로(JSON 이 1개일 때)")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "output", help="출력 폴더")
    ap.add_argument("--badge", default="", help="상단 배지 문구(비우면 JSON 의 제목 사용)")
    ap.add_argument("--footer", default=FOOTER_NOTE, help="하단 저작권 문구")
    ap.add_argument("--seed", type=int, default=1, help="문항 순서 섞기 시드(회차마다 바꾸세요)")
    ap.add_argument("--no-shuffle", action="store_true", help="교재 순서 그대로 출제")
    ap.add_argument("--no-hint", action="store_true", help="한→영 첫 글자 힌트 없이")
    args = ap.parse_args()

    for jf in args.json:
        data = load_wordbook(jf)
        out = args.out if (args.out and len(args.json) == 1) else \
            args.out_dir / f"{jf.stem}_단어test.pdf"
        p = render_wordtest_pdf(
            data["words"], out, badge=_badge(data, args.badge), footer_note=args.footer,
            seed=args.seed, shuffle=not args.no_shuffle, hint=not args.no_hint)
        print(f"{p}  ({len(data['words'])}개 → 영→한/한→영 각 {len(data['words']) // 2}문항)")


if __name__ == "__main__":
    main()
