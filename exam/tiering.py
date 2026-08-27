"""비용은 줄이고 판단력은 지키는 두 가지 장치 — 유형별 추론 강도와 모델 승격.

① 유형별 추론 강도(effort)
   16문항이 다 같은 무게가 아니다. 정답이 유일한지 따져야 하는 유형(빈칸·삽입·순서·
   내용일치·함의·요약·무관한 문장)은 깊게 생각할 값어치가 있지만, 어휘·어법·제목처럼
   코드가 형식을 직접 검사하는 유형까지 같은 강도로 돌릴 이유가 없다. 사고 토큰은
   출력 요금으로 청구되므로, 여기서 아끼는 것이 곧 비용 절감이다.

② 모델 승격(escalation)
   전부를 값싼 모델로 만들고, **검수에 걸린 문항만** 좋은 모델로 다시 만든다.
   대부분의 문항은 한 번에 통과하므로 좋은 모델은 몇 문항에만 쓰인다.
   승격 대상은 '취향 문제'가 아니라 기계적으로 정해진다:
     · 생성 자체가 실패해 빠진 문항
     · 자기검증(LLM 검수)에 걸린 문항
     · 자동 보정이 필요했던 문항(삽입 위치 클램프 등)
   '오답 근거가 조금 짧다' 같은 참고용 표시는 승격하지 않는다(값만 든다).
"""
from __future__ import annotations

# 추론 강도 — 판단이 걸린 유형만 high, 나머지는 medium.
#   high  : 정답 유일성을 따져야 하고, 틀리면 복수정답·정답 없음이 되는 유형
#   medium: 코드가 형식을 검사해 주거나(어휘·제목), 구조가 단순한 유형
_HIGH = {"F", "insert", "order", "content", "B", "E",
         # 연결어는 두 자리가 '서로 바꿔 써도 되는' 관계면 곧바로 복수정답이 된다.
         "linker",
         # 어법 세 유형은 지문을 다시 써서 내므로(암기 방지) 판단 부담이 크다.
         # 다시 쓴 문장에 뜻하지 않은 오류가 남으면 정답이 여러 개가 된다.
         # 서술형은 '고칠 방법이 하나뿐인가'까지 따져야 해서 특히 그렇다.
         "grammar", "grammar_fix",
         # 짝짓기는 밑줄 5개 판정이 모두 맞아야 짝이 성립한다.
         "pair_odd"}
_MEDIUM = {"topic", "title", "vocab", "D", "short_answer"}

DEFAULT_EFFORT = "medium"
VERIFY_EFFORT = "high"      # 검수는 언제나 깊게 — 여기가 마지막 문지기다


def _base(type_key: str) -> str:
    import re
    return re.sub(r"_\d+$", "", type_key or "")


def effort_for(type_key: str) -> str:
    """이 유형을 어느 추론 강도로 만들지."""
    t = _base(type_key)
    if t in _HIGH:
        return "high"
    if t in _MEDIUM:
        return DEFAULT_EFFORT
    return DEFAULT_EFFORT


class EffortClient:
    """지정한 추론 강도로 호출을 대신 넘겨주는 얇은 껍데기.

    생성기 11개를 고치지 않고도 유형마다 다른 강도를 줄 수 있다.
    structured() 말고는 전부 원래 클라이언트에 그대로 넘긴다.
    """

    def __init__(self, inner, effort: str):
        self._inner = inner
        self._effort = effort

    def structured(self, *args, **kwargs):
        kwargs.setdefault("effort", self._effort)
        return self._inner.structured(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)


# ---------------------------------------------------------------------------
# 모델 승격 — 검수에 걸린 문항만 좋은 모델로 다시 만든다
# ---------------------------------------------------------------------------
# 이 말머리로 시작하는 사유는 '문항에 실제 결함이 의심된다'는 뜻이라 다시 만들 값어치가 있다.
# 승격 방아쇠가 되는 사유의 접두어.
#   자동검증: — 모델 자기검증(정답이 유일한가)
#   자동검사: — 코드 기계 검사(해설 위생·문항 간 겹침 등 '다시 만들면 고쳐지는 것')
# 값싼 모델로 생성하면 정답은 맞아도 해설·형식에서 흠이 나는데, 기계 검사가 방아쇠에
# 연결돼 있지 않으면 그 흠이 그대로 인쇄된다(실제 출력물에서 그렇게 됐다).
_ESCALATE_PREFIX = ("자동검증:", "자동검사:")


def needs_escalation(flags: list[str] | None) -> bool:
    """이 문항을 좋은 모델로 다시 만들어야 하는가."""
    if not flags:
        return False
    from . import review as _rv
    hard = {_rv.FIX_ORDER, _rv.FIX_INSERT, _rv.FIX_SNAP, _rv.FIX_AMBIG}
    for f in flags:
        if f in hard or any(f.startswith(p) for p in _ESCALATE_PREFIX):
            return True
    return False


def escalation_targets(passage, type_order) -> list[str]:
    """다시 만들 유형 목록 — 빠진 문항 + 검수에 걸린 문항."""
    out = []
    for t in type_order:
        if t not in passage.q or t not in passage.a:
            out.append(t)                       # 아예 못 만든 문항
        elif needs_escalation(passage.flags.get(t)):
            out.append(t)                       # 검수에 걸린 문항
    return out
