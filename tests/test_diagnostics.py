"""추출 마커 확장 + 품질 자가진단 + 환경 점검 오프라인 테스트.

실행: python -m tests.test_diagnostics
"""
from __future__ import annotations

from src import extract, envcheck


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_marker_expansion():
    raw = "\n".join([
        "Q1. This is the first full sentence of the passage about conservation practices.",
        "【2】 Here is the second complete sentence describing preservation methods clearly.",
        "가. The third sentence continues the discussion of restoration work in detail.",
        "[4] A short one.",     # 짧음 → 제거
        "- 14 -",                # 페이지 번호 → 제거
    ])
    cleaned = extract.clean_text(raw)
    _check("Q1. 문장 유지", "first full sentence of the passage" in cleaned)
    _check("【2】 문장 유지", "second complete sentence" in cleaned)
    _check("가. 문장 유지", "third sentence continues" in cleaned)
    _check("짧은 [4] 제거", "A short one" not in cleaned)
    _check("페이지 번호 제거", "- 14 -" not in cleaned)


def test_diagnose_levels():
    good = ("Conservation aims to keep an object in its present state. "
            "Restoration revives damaged objects for display. "
            "Preservationists act as protectors of the original object.")
    _check("정상 지문 → ok", extract.diagnose_extraction(good)["level"] == "ok")

    truncated = ("its present state, to protect it from change.\n"
                 "as protectors.\n"
                 "restorative aspects restoring instruments.\n"
                 "use rather than interfering with the object.")
    d = extract.diagnose_extraction(truncated)
    _check("잘린 지문 → warn(소문자 시작 다수)", d["level"] == "warn" and d["ok"])

    _check("빈 텍스트 → bad(API 호출 skip)", extract.diagnose_extraction("...")["level"] == "bad"
           and not extract.diagnose_extraction("...")["ok"])


def test_environment_check_shape():
    r = envcheck.check_environment()
    _check("환경 점검 항목 존재", isinstance(r["items"], list) and len(r["items"]) >= 5)
    _check("각 항목에 name/ok/detail", all({"name", "ok", "detail"} <= set(it) for it in r["items"]))
    _check("format_report 문자열", isinstance(envcheck.format_report(r), str))


if __name__ == "__main__":
    test_marker_expansion()
    test_diagnose_levels()
    test_environment_check_shape()
    print("\n진단/마커/환경 점검 오프라인 테스트 통과 ✅")
