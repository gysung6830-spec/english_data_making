"""정본(지문) 사전 점검 — API 를 쓰기 전에 '추출·정제가 깨끗한지' 확인한다.

원본 PDF/HWP 에서 뽑아낸 지문(bodies)만 보고, 생성(=API 비용) 전에 걸러야 할
구조적 문제를 찾는다. LLM 을 부르지 않으므로 비용이 들지 않는다.

여기서 잡는 것은 '정본 오염·추출 사고'다(실제 결과물에서 나왔던 유형):
  · 한줄해석(번역) 잔재 — 번역문에 든 영어 고유명사·연도가 원문 뒤에 붙는 경우
  · 한글 잔재 — 영어 지문에 한국어가 남은 경우
  · 워크시트 노이즈 — 머리글/꼬리말/출처가 지문에 섞인 경우
  · 문장 수·길이 이상 — 너무 짧거나(추출 실패) 한 문장뿐인 지문
  · 지문 중복 — 같은 지문이 두 번 들어온 경우
문항 '내용'의 타당성(정답·오답 근거)은 생성 후 검토메모가 담당한다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

_HANGUL = re.compile(r"[가-힣]")
# 워크시트/출처 노이즈가 정제 후에도 남았는지
_NOISE = re.compile(r"(\[EBS\]|\[Flow\s*Edu\]|flowedu|tistory|올림포스|한줄해석"
                    r"|WORKBOOK|좌지문|우해석)", re.IGNORECASE)
# 번역문에서 살아남은 영어 조각은 '동사가 없는' 고유명사·연도 나열이다.
# (예: '1968 The Population Bomb Paul R. Ehrlich.') 이런 낱말은 내용어로 치지 않는다.
_FUNCTION_WORDS = {"of", "the", "and", "a", "an", "in", "on", "at", "to", "for",
                   "by", "or", "de", "van", "von"}


@dataclass
class Issue:
    """지문 하나에서 발견한 문제 1건."""

    label: str          # 지문 라벨(10-3 등) 또는 '지문 2'
    kind: str           # 문제 종류(사람이 읽는 짧은 말)
    detail: str         # 근거(문제가 된 실제 텍스트 일부)

    def __str__(self) -> str:
        return f"[{self.label}] {self.kind}: {self.detail}"


@dataclass
class Report:
    """전체 사전 점검 결과."""

    issues: list[Issue] = field(default_factory=list)
    n_bodies: int = 0

    @property
    def ok(self) -> bool:
        return not self.issues

    def summary(self) -> str:
        if self.ok:
            return f"지문 {self.n_bodies}개 — 사전 점검 통과(정제 이상 없음)."
        return f"지문 {self.n_bodies}개 중 {len(self.issues)}건의 확인이 필요합니다."


def _split_sentences(body: str) -> list[str]:
    """대략적인 문장 분리(점검용). 정확한 분리는 분석기가 담당한다."""
    return [s for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]


# 편지의 인사말·맺음말 — 동사가 없어도 정상 본문이다.
_LETTER_EDGE = re.compile(
    r"^(Dear\b|(Sincerely|Regards|Best\s+regards|Yours\s+(sincerely|truly)|"
    r"Respectfully|Cordially|Warm\s+regards|Thank\s+you)\b)", re.IGNORECASE)


def _fragment_sentences(sents: list[str]) -> list[str]:
    """'번역 잔재'로 보이는 조각 문장들을 돌려준다(지문 어느 위치든).

    예: '... for decades.' 뒤에 붙은 '1968 The Population Bomb Paul R. Ehrlich.'
    정상 문장은 동사 등 '소문자 내용어'를 갖는다. 고유명사·연도만 2개 이상 나열되고
    소문자 내용어가 하나도 없으면 조각으로 본다(첫 낱말은 대문자이므로 판단에서 제외).
    """
    frags = []
    for s in sents:
        # 편지의 인사말·맺음말은 원래 동사가 없다 — 잔재가 아니라 본문이다.
        # (실제 원본 4지문에서 'Sincerely, Lisa'·'Dear Mrs.'·'Regards, Martin Williams'가
        #  모두 잔재로 걸렸다. 편지는 이 교재에서 한 단원을 통째로 차지한다.)
        if _LETTER_EDGE.match(s.strip()) and len(s.split()) <= 6:
            continue        # 'Regards, Martin Williams' 는 맞지만, 그 뒤에 잔재가
                            # 길게 붙은 줄은 걸러야 하므로 짧은 줄만 면제한다.
        words = [w for w in re.findall(r"[A-Za-z0-9.'’-]+", s) if w.strip(".'’-")]
        if len(words) < 2:
            continue
        rest = words[1:]                       # 문장 첫 낱말은 항상 대문자 → 제외
        lower = [w for w in rest if w[:1].islower() and w.lower() not in _FUNCTION_WORDS]
        if lower:
            continue                           # 소문자 내용어가 있으면 정상 문장
        caps = [w for w in words if w[:1].isupper() or w[:1].isdigit()]
        if len(caps) >= 2:
            frags.append(s.strip())
    return frags


def check_body(body: str, label: str = "") -> list[Issue]:
    """지문 1개를 점검해 문제 목록을 돌려준다(문제 없으면 빈 리스트)."""
    out: list[Issue] = []
    lb = label or "지문"
    text = (body or "").strip()
    if not text:
        return [Issue(lb, "빈 지문", "추출된 내용이 없습니다.")]

    kr = _HANGUL.findall(text)
    if kr:
        m = re.search(r"[가-힣][가-힣\s,·]{0,28}", text)
        out.append(Issue(lb, "한글 잔재",
                         f"영어 지문에 한국어가 남아 있습니다 — '{(m.group(0) if m else ''.join(kr[:12])).strip()}…'"))

    noise = _NOISE.search(text)
    if noise:
        out.append(Issue(lb, "워크시트 노이즈",
                         f"머리글·출처 표기가 지문에 섞였습니다 — '{noise.group(0)}'"))

    sents = _split_sentences(text)
    for frag in _fragment_sentences(sents):
        out.append(Issue(lb, "한줄해석 잔재 의심",
                         f"동사 없는 고유명사·연도 나열이 문장으로 섞였습니다 — '{frag}'"))

    if len(sents) < 3:
        out.append(Issue(lb, "문장 수 부족",
                         f"{len(sents)}문장만 추출됐습니다(순서·삽입 유형은 3문장 이상 필요)."))
    if len(text) < 200:
        out.append(Issue(lb, "지문이 너무 짧음", f"{len(text)}자 — 추출 실패일 수 있습니다."))
    return out


def precheck(bodies: list[str], labels: list[str] | None = None) -> Report:
    """지문들을 생성 전에 점검한다(API 미사용). 웹앱·CLI 공용."""
    rep = Report(n_bodies=len(bodies))
    seen: dict[str, str] = {}
    for i, body in enumerate(bodies):
        lb = (labels[i] if labels and i < len(labels) and labels[i] else f"지문 {i + 1}")
        rep.issues += check_body(body, lb)
        key = re.sub(r"[^a-z0-9]+", " ", (body or "").lower()).strip()[:200]
        if key and key in seen:
            rep.issues.append(Issue(lb, "지문 중복", f"'{seen[key]}'와 내용이 같습니다."))
        elif key:
            seen[key] = lb
    return rep
