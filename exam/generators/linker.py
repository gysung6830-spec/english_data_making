"""연결어 생성기 — 지문 두 곳을 (A)·(B) 빈칸으로 만들고 연결사 짝을 고르게 한다.

무관한 문장을 대신해 들어온 유형이다. 두 유형은 묻는 것이 다르다.
무관한 문장은 '이 문장이 논지에 기여하는가'를 묻고, 연결어는 '앞뒤 두 덩어리가 어떤
관계로 이어지는가'를 묻는다. 뒤엣것이 수능·내신 모두에서 훨씬 자주 나오고, 학생이
글의 뼈대(대조·예시·인과·부연)를 읽는 훈련에 곧바로 쓰인다.

만드는 법: 원문에서 연결어로 시작하는 문장 두 개를 골라 그 연결어를 지우고 빈칸을
놓는다. 원문에 연결어가 두 개 없으면, 관계가 뚜렷한 자리에 새로 빈칸을 놓는다.
"""
from __future__ import annotations

from .. import answer_spread, build2, review, shape
from ..llm import SYSTEM, ClaudeClient
from ..schemas import Analysis, LinkerOut
from .base import context

_PROMPT = """아래 '정본 지문'으로 '연결어' 문제를 만드세요. 발문은 '다음 빈칸 (A), (B)에 들어갈
말로 가장 적절한 것은?' 입니다. 지문을 새로 쓰지 말고, 빈칸 자리와 선지만 정하세요.

[빈칸 자리]
- blank_a_no / blank_b_no: 빈칸을 놓을 문장 번호(1-based). (A) < (B) 이고, (A) 는 2 이상
  이어야 합니다(첫 문장 앞에는 이어받을 글이 없습니다).
- remove_a / remove_b: 그 문장이 이미 연결어로 시작하면 그 연결어를 '문장에 있는 그대로'
  적으세요(쉼표까지. 예: "However," · "Rather," · "For example,"). 조판기가 그 말을 지우고
  빈칸을 놓습니다. 연결어로 시작하지 않는 문장이면 빈 문자열로 두세요.
- 되도록 '원문에 연결어가 있는 문장'을 고르세요. 원래 글이 그 자리에서 관계를 밝혔다는
  뜻이라 정답이 확실해집니다. 그런 문장이 둘 없으면, 앞뒤 관계가 뚜렷한 자리를 고르세요.
- 두 빈칸은 서로 '다른 관계'여야 합니다(둘 다 대조면 한 번만 알면 둘 다 풀립니다).

[선지] pairs 5개 — 각 항목은 a((A)에 들어갈 말), b((B)에 들어갈 말).
- answer_no 한 개만 두 자리 모두 맞습니다.
- 나머지 4개는 적어도 한 자리가 확실히 틀려야 합니다. 네 오답의 '틀린 자리'를 골고루
  섞으세요(A만 틀림 · B만 틀림 · 둘 다 틀림).
- 같은 짝이 두 번 나오면 안 됩니다. 낱말은 문장 첫머리 표기 그대로(첫 글자 대문자, 쉼표 없이).
- 흔히 쓰는 것: However · Nevertheless · In contrast · On the other hand(대조) /
  Therefore · Thus · As a result · Consequently(인과) / For example · For instance(예시) /
  In addition · Moreover · Furthermore · Similarly(부연·병렬) / Instead · Rather(정정) /
  In other words · That is(환언) / Meanwhile · In fact · Indeed.

[해설]
- reason: 두 자리가 각각 어떤 관계인지, 앞뒤 문장의 어느 말이 그 근거인지 한국어로.
- wrong_reasons: 오답마다 (A)·(B) 중 어느 자리가 왜 틀렸는지 콕 집어 한국어로.

[확실성] 정답 짝 하나만 두 자리를 모두 만족해야 합니다. 두 연결어가 서로 바꿔 써도
말이 되는 자리(예: Therefore 와 Thus)는 고르지 마세요 — 복수정답이 됩니다.

{ctx}
"""


def generate(client: ClaudeClient, analysis: Analysis, body: str,
             max_retries: int = 1, answer_pos: int | None = None,
             variant_hint: str = "") -> tuple[str, str, list[str]]:
    n = len(analysis.sentences)
    if n < 3:
        raise ValueError(f"연결어 문제에는 문장이 3개 이상 필요합니다(현재 {n}개).")

    def _chk(out: LinkerOut) -> None:
        if not (2 <= out.blank_a_no < out.blank_b_no <= n):
            raise ValueError(f"빈칸 자리는 2 이상 {n} 이하이고 (A) 가 (B) 보다 앞서야 "
                             f"합니다(현재 A={out.blank_a_no}, B={out.blank_b_no}).")
        for no, rm, letter in ((out.blank_a_no, out.remove_a, "A"),
                               (out.blank_b_no, out.remove_b, "B")):
            rm = (rm or "").strip()
            if rm and not analysis.sentences[no - 1].lower().startswith(rm.lower()):
                raise ValueError(
                    f"({letter}) 로 지목한 {no}번 문장은 '{rm}' 로 시작하지 않습니다: "
                    f"'{analysis.sentences[no - 1][:40]}…' — 지문에 있는 그대로 적으세요.")
        words = [w for p in out.pairs for w in (p.a, p.b)]
        bad = [w for w in words if not w.strip() or len(w.split()) > 4]
        if bad:
            raise ValueError(f"연결어가 아닌 것이 선지에 있습니다: {', '.join(bad[:3])}")

    out: LinkerOut = client.structured(
        system=SYSTEM,
        prompt=((variant_hint + "\n" if variant_hint else "")
                + _PROMPT.format(ctx=context(analysis))
                + f"\n[문장 수] 이 지문은 {n}개 문장입니다."),
        cache_prefix=context(analysis),
        model_cls=LinkerOut,
        max_tokens=2500,
        max_retries=max_retries,
        extra_validate=_chk,
    )
    pairs = [(p.a.strip(), p.b.strip()) for p in out.pairs]
    answer_no = out.answer_no
    wrong = {w.no: w.text for w in out.wrong_reasons}
    reason = out.reason
    if answer_pos:      # 정답 위치 분산(선지 재배열 — 정오 불변)
        mapping = answer_spread.perm_map(len(pairs), answer_no, answer_pos)
        pairs, answer_no, wrong = answer_spread.place_answer(
            pairs, answer_no, answer_pos, wrong)
        reason = answer_spread.relabel_choice_refs(reason, mapping)
        wrong = {no: answer_spread.relabel_choice_refs(t, mapping)
                 for no, t in (wrong or {}).items()}
    q, a = build2.make_linker(analysis.sentences, out.blank_a_no, out.blank_b_no,
                              out.remove_a, out.remove_b, pairs, answer_no,
                              reason, wrong)
    flags = review.weak_distractors(out.wrong_reasons)
    # 지문에 연결어가 두 번 남아 있으면(지우지 못했으면) 학생이 답을 그냥 읽는다.
    flags += shape.check_clean_sentence(analysis.sentences[out.blank_b_no - 1], "(B) 문장")
    return q, a, flags
