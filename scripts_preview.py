"""선별 미리보기 → output/선별_미리보기.md 생성 (검수용)."""
from pathlib import Path
from src.guide.select import preview, split_examples_problems

d = preview("input_corpus")
out = ["# 연습 문장 선별 미리보기\n",
       f"전체 기출 문장 **{d['total']}개** 중, 필터·점수로 챕터별 선별한 결과입니다.",
       "예시(중5·고5) + 문제 후보 순으로, 각 문장에 [난이도] 〔출처〕 점수를 표기했습니다.\n"]


def dump(title, chapters):
    out.append(f"\n## {title}\n")
    for cp in chapters:
        ex, pr = split_examples_problems(cp.picks, 10)
        out.append(f"\n### {cp.title} — 통과 {len(cp.picks)} "
                   f"(예시 {len(ex)}, 문제 {len(pr)}) · 필터탈락 {cp.filtered_out}\n")
        out.append("**예시(우선 수록):**\n")
        for p in ex:
            out.append(f"- [{p.difficulty}] 〔{p.source}〕 (pt {p.score}) {p.sentence}")
        if pr:
            out.append("\n**문제 후보(상위 8개만 표시):**\n")
            for p in pr[:8]:
                out.append(f"- [{p.difficulty}] 〔{p.source}〕 (pt {p.score}) {p.sentence}")


dump("1부 · 평가원 코드", d["code"])
dump("2부 · 구문 유형", d["syntax"])

Path("output/선별_미리보기.md").write_text("\n".join(out), encoding="utf-8")
print("생성: output/선별_미리보기.md")
print("총 통과(중복 포함):", sum(len(c.picks) for c in d["code"] + d["syntax"]))
