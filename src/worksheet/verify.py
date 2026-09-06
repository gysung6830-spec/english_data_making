"""자동 오류검증 — 마스터 분석(Analysis)을 원문과 대조하고 내부 정합성을 점검한다.

지금까지 사람이 눈으로 하던 검증(원문 단어·숫자 누락, 직독직해 정렬, 해석 누락,
안내문 표 추출 누락 의심)을 코드로 옮긴 것. 원문 텍스트를 함께 주면 '원문 대조'까지,
없으면 '내부 정합성'만 검사한다.

반환: {"ok": bool, "findings": [{"level","where","msg"}], "counts": {...}}
  - level: "error"(내용 누락·정합 깨짐) | "warn"(의심·경미)
"""
from __future__ import annotations

import re

from .models import Analysis


def _words(s: str) -> list[str]:
    s = (s or "").replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("―", " ").replace("—", " ").replace("-", " ")
    return [w for w in re.sub(r"[^A-Za-z0-9'%$#]+", " ", s).lower().split() if w]


def _nums(s: str) -> list[str]:
    return sorted(re.findall(r"\d+", s or ""))


def _recon(a: Analysis) -> str:
    return " ".join(t.text for s in a.sentences for line in s.lines for t in line)


def _reading_chunks(sent) -> int:
    rk = getattr(sent, "reading_ko", "") or ""
    return len([c for c in rk.split(" / ") if c.strip()])


def _slash_chunks(sent) -> int:
    toks = [t for line in sent.lines for t in line]
    return sum(1 for t in toks if getattr(t, "slash", False)) + 1


def verify_analyses(analyses: list[Analysis], original_text: str = "") -> dict:
    """분석 결과를 검증한다. original_text 가 있으면 원문 대조까지 수행.

    - 원문 대조: 문제번호(라벨)로 원문을 쪼개 지문별로 '단어 회수율·숫자 누락'을 본다.
    - 내부 정합성: 직독직해 정렬(영어=한글 조각), 해석 누락, 인접 중복 토큰.
    """
    findings: list[dict] = []

    # ── 원문 대조(원문 텍스트가 있을 때만) ──
    spans: dict[str, str] = {}
    if original_text and original_text.strip():
        from .pipeline import _problem_spans          # 지연 임포트(무거움 회피)
        spans = {lbl: chunk for lbl, chunk in _problem_spans(original_text)}
        # 문제 경계를 못 찾고(<2) 지문이 하나뿐이면 원문 전체를 그 지문으로 대조.
        if not spans and len(analyses) == 1:
            spans = {(analyses[0].lecture_label or "").strip(): original_text}

    for a in analyses:
        lbl = (a.lecture_label or "").strip()
        where = f"{lbl}번" if lbl else "(무번호)"
        chunk = spans.get(lbl)
        if chunk:
            body = re.sub(r"^\[[^\]]*\]\s*", "", chunk)
            ow, rw = _words(body), set(_words(_recon(a)))
            # 연속 3단어+ 통째 누락 = 표/문장 통째 빠짐 의심
            run, runs = [], []
            for w in ow:
                if w not in rw:
                    run.append(w)
                else:
                    if len(run) >= 3:
                        runs.append(" ".join(run))
                    run = []
            if len(run) >= 3:
                runs.append(" ".join(run))
            if runs:
                findings.append({"level": "error", "where": where,
                                 "msg": f"원문 일부 누락 의심: '{runs[0][:50]}…' 등 {len(runs)}곳"})
            miss_num = [n for n in _nums(body) if n not in _nums(_recon(a))]
            if miss_num:
                findings.append({"level": "error", "where": where,
                                 "msg": f"숫자 누락: {miss_num}"})

        # ── 내부 정합성(원문 없어도) ──
        for s in a.sentences:
            if (getattr(s, "reading_ko", "") or "").strip():
                if _reading_chunks(s) != _slash_chunks(s):
                    findings.append({"level": "warn", "where": f"{where} {s.index}문장",
                                     "msg": f"직독직해 정렬 어긋남(영어 {_slash_chunks(s)} ≠ 한글 {_reading_chunks(s)})"})
            if not (getattr(s, "translation", "") or "").strip():
                findings.append({"level": "warn", "where": f"{where} {s.index}문장",
                                 "msg": "해석(translation) 비어있음"})
            tx = [t.text for line in s.lines for t in line]
            for i in range(1, len(tx)):
                cur = (tx[i] or "").strip()
                if cur and " " not in cur and tx[i - 1].split() \
                        and tx[i - 1].split()[-1].lower() == cur.lower():
                    findings.append({"level": "warn", "where": f"{where} {s.index}문장",
                                     "msg": f"인접 중복 토큰: '…{cur}'"})

    errors = sum(1 for f in findings if f["level"] == "error")
    warns = sum(1 for f in findings if f["level"] == "warn")
    return {"ok": errors == 0, "findings": findings,
            "counts": {"error": errors, "warn": warns},
            "checked_original": bool(spans)}
