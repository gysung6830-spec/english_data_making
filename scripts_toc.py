"""목차 샘플 생성 — 새 4부 구조(0/1/2패러프레이징/3구문)의 표지+목차만 뽑는다."""
from pathlib import Path

import fitz  # PyMuPDF

from src.guide import render
from src.guide.codes import load_categories, load_part0
from src.guide.schemas import (Chapter, Guide, ParaphrasePart, Part2, SyntaxChapter)
from src.guide.syntax import SYNTAX_TYPES

# 1부: 평가원 코드 (제목만 필요 — 카드 비움)
chapters = [Chapter(id=c.id, title=c.title, signal=c.signal, misread=c.misread,
                    tip=c.tip, cards=[]) for c in load_categories()]

# 2부: 패러프레이징 (지문 단위)
paraphrase = ParaphrasePart(
    title="패러프레이징 — 같은 주제, 다른 표현",
    intro="지문 한 편을 통째로 읽고, 필자의 핵심주제가 어떻게 다른 표현으로 되풀이·전개되는지 추적한다.",
    passages=[])

# 3부: 구문해석 (새 목차 — SYNTAX_TYPES 순서)
part2 = Part2(title="이런 구조면 이렇게 해석",
              intro="구문 유형별로 '이런 구조면 → 이렇게 해석'을 반복 훈련한다.",
              chapters=[SyntaxChapter(id=st.id, title=st.title, signal=st.signal,
                                      how=st.formula, combat_tip=st.combat, cards=[])
                        for st in SYNTAX_TYPES])

guide = Guide(part0=load_part0(), chapters=chapters, paraphrase=paraphrase, part2=part2)

full = Path("output/_toc_full.pdf")
render.render_pdf(guide, full, sample=True)

# 표지(1) + 목차(2) 두 페이지만 추출
src = fitz.open(str(full))
doc = fitz.open()
doc.insert_pdf(src, from_page=0, to_page=1)
out = Path("output/구문해석_실전서_목차.pdf")
doc.save(str(out))
print("생성:", out, "| 전체 페이지:", src.page_count)
