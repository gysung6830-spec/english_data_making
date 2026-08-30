#!/usr/bin/env python3
"""결과 JSON 을 고쳐 API 없이 다시 뽑는다 (검증 → 수정 → 재조판).

오류 검증에서 나온 결함 중에는 '문항을 다시 만들 필요 없이 글자만 고치면 되는 것'이
많다. 지문 정제가 날짜를 먹었다거나(September 17. → September), 전화번호가 깨졌다거나,
해설에 오타가 있다거나. 그런 것 때문에 지문 하나를 통째로 다시 생성하면 API 값이 그대로
다시 든다.

결과 JSON 은 문항의 HTML 을 그대로 담고 있고 조판기는 그것을 읽어 PDF 를 만든다.
그러니 JSON 의 글자를 고치고 다시 조판하면 된다 — 호출 0회, 몇십 초.

사용:
    # 무엇이 바뀌는지 먼저 본다(파일은 건드리지 않는다)
    python tools/JSON수정.py 결과.json --바꾸기 "308 9847=>308-555-9847"

    # 정말 고치고 PDF 까지 뽑는다
    python tools/JSON수정.py 결과.json \\
        --바꾸기 "September I realize=>September 17. I realize" \\
        --바꾸기 "308 9847=>308-555-9847" \\
        --저장 수정본.json --조판 수정본.pdf

    # 특정 지문에서만 바꾼다(1부터 셈)
    python tools/JSON수정.py 결과.json --지문 2 --바꾸기 "낡은 말=>고친 말" --저장 out.json

바꾸기 전후로 검산(exam/audit)을 돌려 지적 수가 어떻게 달라졌는지 보여 준다.
'찾을 것'이 태그에 걸려 통째로는 못 찾은 자리가 있으면 경고한다 — 그런 자리는 밑줄이나
빈칸이 글자 사이에 끼어 있다는 뜻이라, 글자만 고쳐서는 안 되고 문항을 다시 만들어야 한다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam import audit, serialize  # noqa: E402


def _plain(html: str) -> str:
    """태그와 밑줄 기호를 지운 글 — '원래 지문의 글자'로 찾을 때 쓴다.

    기호(①~⑩·ⓐ~ⓔ)까지 지워야 한다. 밑줄이 어구 한가운데 있으면 HTML 은
    's <span…>①</span> <u>expected</u> party' 인데, 기호를 남기면 평문도
    's ① expected party' 가 되어 원래 글 's expected party' 를 못 찾는다.
    그러면 '밑줄에 걸려 못 고쳤다'는 경고가 뜨지 않고 조용히 넘어간다.
    """
    t = re.sub(r"<[^>]+>", " ", html or "")
    t = re.sub(r"[①-⑳ⓐ-ⓩ]", " ", t)
    return re.sub(r"\s+", " ", t)


def _count_bad(passages) -> int:
    total = 0
    for p in passages:
        rows, whole = audit.check_passage(p, 1)
        total += sum(1 for it in rows if it["bad"]) + len(whole)
    return total


def apply_edits(data: dict, edits: list[tuple[str, str]],
                only: int | None = None) -> tuple[int, list[str]]:
    """JSON 안의 문항 HTML 에 글자 치환을 적용한다.

    반환: (고친 자리 수, 태그에 걸려 못 고친 자리 설명들)
    """
    n = 0
    stuck: list[str] = []
    for part in data.get("parts", []):
        for pi, pg in enumerate(part.get("passages", []), 1):
            if only and pi != only:
                continue
            for find, repl in edits:
                for side in ("q", "a"):
                    for t, html in list(pg.get(side, {}).items()):
                        if find in html:
                            pg[side][t] = html.replace(find, repl)
                            n += 1
                        elif find in _plain(html):
                            # 보이는 글자에는 있는데 HTML 에는 통째로 없다
                            # = 밑줄·빈칸 태그가 글자 사이에 끼어 있다.
                            stuck.append(f"지문{pi} {side}:{t} — '{find}'")
    return n, stuck


def main() -> int:
    ap = argparse.ArgumentParser(description="결과 JSON 을 고쳐 API 없이 다시 조판")
    ap.add_argument("json", help="웹앱이 저장한 결과 JSON")
    ap.add_argument("--바꾸기", action="append", default=[], metavar="찾을것=>바꿀것",
                    help="글자 치환(여러 번 쓸 수 있음)")
    ap.add_argument("--지문", type=int, default=None, help="이 지문에서만 바꾼다(1부터)")
    ap.add_argument("--저장", default=None, help="고친 JSON 을 저장할 경로")
    ap.add_argument("--조판", default=None, help="PDF 로 뽑을 경로")
    ap.add_argument("--검토메모", default=None, help="검토 메모를 따로 저장할 경로")
    args = ap.parse_args()

    edits = []
    for spec in args.바꾸기:
        if "=>" not in spec:
            print(f"✗ '{spec}' — '찾을것=>바꿀것' 꼴로 적으세요.")
            return 2
        find, repl = spec.split("=>", 1)
        if not find:
            print("✗ 찾을 것이 비어 있습니다.")
            return 2
        edits.append((find, repl))

    data = json.loads(Path(args.json).read_text(encoding="utf-8"))
    parts, meta = serialize.load_parts(data)
    before = sum(_count_bad(p["passages"]) for p in parts)

    n, stuck = apply_edits(data, edits, only=args.지문)
    print(f"고친 자리: {n}곳" + (f" (지문 {args.지문}만)" if args.지문 else ""))
    if not n and edits:
        print("  ! 찾을 것이 어디에도 없습니다 — 글자가 정확한지 확인하세요.")
    for s in dict.fromkeys(stuck):
        print(f"  ! {s} — 밑줄·빈칸이 글자 사이에 끼어 있어 글자만으로는 못 고칩니다"
              " (그 문항은 다시 만들어야 합니다).")

    parts, meta = serialize.load_parts(data)
    after = sum(_count_bad(p["passages"]) for p in parts)
    print(f"검산: 지적 {before}건 → {after}건")

    if args.저장:
        Path(args.저장).write_text(json.dumps(data, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        print(f"JSON 저장: {args.저장}")
    if args.조판:
        from exam import renderer

        rev = renderer.render_pdf_multi(parts, args.조판, review_out=args.검토메모)
        print(f"PDF 조판: {args.조판}" + (f" · 검토메모: {rev}" if rev else ""))
    if not args.저장 and not args.조판:
        print("(미리보기만 했습니다 — 실제로 고치려면 --저장 / --조판 을 주세요)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
