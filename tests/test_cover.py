"""표지 겸 사용 설명서 오프라인 테스트.

실행: python -m tests.test_cover
"""
from __future__ import annotations

from src import cover_render as cr


def _check(name, cond):
    print(("PASS  " if cond else "FAIL  ") + name)
    assert cond, name


def test_sections_order_and_filter():
    # 있는 유형만, 카탈로그 순서대로 번호 재부여
    secs = cr.build_cover_sections(["blanks", "workbook", "writing"])
    _check("수록 유형만 노출", [s.key for s in secs] == ["workbook", "writing", "blanks"])
    _check("번호 1..n 재부여", [s.no for s in secs] == [1, 2, 3])


def test_full_catalog_order():
    secs = cr.build_cover_sections(cr._ORDER)
    _check("전체 순서(통합→어형→어법→어휘하→어휘상→지칭→영작→해석→빈칸)",
           [s.key for s in secs] ==
           ["workbook", "form", "grammar", "vocab_easy", "vocab", "ref",
            "writing", "translate", "blanks"])


def test_render_html():
    secs = cr.build_cover_sections(cr._ORDER)
    html = cr.render_cover_html(header="김은아영어연구소", title="샘플 지문",
                                version_label="한글 포함", n_passages=1, sections=secs)
    _check("브랜드/제목 노출", "김은아영어연구소" in html and "샘플 지문" in html)
    _check("버전 배지", "한글 포함" in html)
    _check("유형 이름 노출", "통합 카드" in html and "영작 워크북" in html and "빈칸 워크북" in html)
    _check("기호 안내 존재", "기호 안내" in html)
    _check("한글 포함/제외 활용 안내", "복습" in html and "시험 대비" in html)


def test_render_html_no_ko_version():
    secs = cr.build_cover_sections(cr._ORDER)
    html = cr.render_cover_html(header="김은아영어연구소", title="샘플",
                                version_label="한글 제외", n_passages=3, sections=secs)
    _check("한글 제외 버전 배지", "한글 제외" in html)
    _check("복수 지문 표기(외 N편)", "외 2편" in html)


if __name__ == "__main__":
    test_sections_order_and_filter()
    test_full_catalog_order()
    test_render_html()
    test_render_html_no_ko_version()
    print("\n표지·사용 설명서 오프라인 테스트 통과 ✅")
