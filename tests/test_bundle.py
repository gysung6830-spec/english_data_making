"""분석 결과(JSON) 저장/복원 오프라인 테스트 (API 없이).

실행: python -m tests.test_bundle
검증: dump→json→load 왕복으로 타입·구조·라벨 보존, 제목만 변경, 형식 검증.
"""
from __future__ import annotations

import json

from src import bundle, pipeline
from src.config import load_config
from src.textutil import file_tag


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def _make():
    from pathlib import Path
    cfg = load_config()
    pdf = Path("올림포스 4강 3, 1번.pdf")
    wbs = [pipeline._mock_workbook_for_pdf(cfg, pdf)]
    packs = [pipeline._mock_prose_pack_for_pdf(cfg, pdf)]
    bsets = [pipeline._mock_blank_set_for_pdf(cfg, pdf, 1)]
    wpacks = [pipeline._mock_writing_pack_for_pdf(cfg, pdf)]
    pipeline.apply_q_numbers(wbs, packs, bsets, wpacks, tag=file_tag(pdf.name))
    return wbs, packs, bsets, wpacks, pdf.name


def test_roundtrip_preserves_structure():
    wbs, packs, bsets, wpacks, src = _make()
    data = bundle.dump_bundle(wbs, packs, bsets, wpacks, source_name=src)
    # JSON 직렬화 가능해야 함
    s = json.dumps(data, ensure_ascii=False)
    w2, p2, b2, wp2, src2 = bundle.load_bundle(json.loads(s))
    _check("타입 복원", type(w2[0]).__name__ == "Workbook" and type(p2[0]).__name__ == "ProsePack"
           and type(b2[0]).__name__ == "LLMBlankSet" and type(wp2[0]).__name__ == "WritingPack")
    _check("통합카드 문항수 보존", w2[0].total == wbs[0].total)
    _check("산문 워크시트 수 보존", len(p2[0].worksheets) == len(packs[0].worksheets))
    _check("라벨·출처 보존", w2[0].label == wbs[0].label and src2 == src)


def test_set_title_only():
    wbs, packs, bsets, wpacks, _ = _make()
    data = bundle.dump_bundle(wbs, packs, bsets, wpacks)
    w2, p2, b2, wp2, _ = bundle.load_bundle(json.loads(json.dumps(data, ensure_ascii=False)))
    before_total = w2[0].total
    bundle.set_passage_title(w2, p2, wp2, b2, 0, "새 제목")
    _check("제목이 모든 유형에 반영",
           w2[0].title == "새 제목" and p2[0].title == "새 제목"
           and wp2[0].title == "새 제목" and b2[0].title == "새 제목")
    _check("제목 변경이 분석 내용은 안 건드림", w2[0].total == before_total)


def test_rejects_foreign_json():
    raised = False
    try:
        bundle.load_bundle({"foo": "bar"})
    except ValueError:
        raised = True
    _check("ORTICA 형식 아니면 거부", raised)


if __name__ == "__main__":
    test_roundtrip_preserves_structure()
    test_set_title_only()
    test_rejects_foreign_json()
    print("\n분석 결과(JSON) 저장/복원 오프라인 테스트 통과 ✅")
