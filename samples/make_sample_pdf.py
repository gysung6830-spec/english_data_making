"""테스트용 입력 지문 PDF 생성.

실행: python -m samples.make_sample_pdf
-> input/sample_passage.pdf 를 만든다 (문제/정답이 섞인 형태로, 전처리 테스트용).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SAMPLE = """The Value of Curiosity

Curiosity drives us to explore the unknown. It is a natural desire to learn
that has shaped human progress for thousands of years. Without it, we would
never have crossed oceans or reached the stars.

Studies show that curious students remember information longer and stay more
motivated. When we ask questions, our brains become more active, and learning
becomes easier and more enjoyable. Curiosity fuels learning and sparks creativity.

Therefore, education should encourage students to ask questions rather than
simply memorize answers. It is important to ask, because inquiry expands our
knowledge and helps us gain new insight.

1. What is the main idea of the passage?
   ① Memorizing answers is essential.
   ② Curiosity is valuable for learning.
   ③ Oceans are dangerous to cross.
   ④ Students dislike questions.
   ⑤ Creativity is unrelated to study.

정답: ②
해설: 글쓴이는 호기심이 학습의 원동력임을 주장하고 있다.
"""


def build(out: Path | None = None) -> Path:
    out = out or (ROOT / "input" / "sample_passage.pdf")
    out.parent.mkdir(parents=True, exist_ok=True)
    from weasyprint import HTML

    html = "<html><body style='font-family:serif;font-size:13px;white-space:pre-wrap;'>" \
           + SAMPLE.replace("&", "&amp;").replace("<", "&lt;") + "</body></html>"
    HTML(string=html).write_pdf(str(out))
    return out


if __name__ == "__main__":
    p = build()
    print(f"생성됨: {p}")
