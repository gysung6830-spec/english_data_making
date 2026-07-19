"""오프라인 테스트: 파서 + 렌더러 + 테마 (무거운 의존성 불필요)."""
import sys
from pathlib import Path

# passage3 디렉터리를 import 경로에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parser import Passage, Sentence, split_passages, circled_to_int  # noqa: E402
from renderer import (render_format_a, render_format_b,  # noqa: E402
                      render_format_c)
from themes import get_css  # noqa: E402

SAMPLE = """[고3] 2026년 5월 - 26번: 프랑스 군대에 자원하여 싸운 Alan Seeger의 생애
① Alan Seeger was born in New York in 1888.
① Alan Seeger는 1888년 뉴욕에서 태어났다.
② He studied at Harvard University.
② 그는 하버드 대학교에서 공부했다.
③ He volunteered for the French army during World War I.
③ 그는 제1차 세계대전 중 프랑스 군대에 자원했다.

[고1] 2026년 6월 - 19번: 버스 고장으로 곤경에 처한 Daniel
① The bus broke down on the way to school.
① 학교 가는 길에 버스가 고장 났다.
② Daniel had to walk the rest of the way.
② Daniel은 남은 길을 걸어가야 했다.
"""


def test_circled():
    assert circled_to_int("①") == 1
    assert circled_to_int("⑳") == 20
    assert circled_to_int("A") == 0


def test_split_two_passages():
    passages = split_passages(SAMPLE)
    assert len(passages) == 2

    p1 = passages[0]
    assert p1.label == "[고3] 2026년 5월 - 26번"
    assert "Alan Seeger" in p1.title
    assert len(p1.sentences) == 3
    assert p1.sentences[0].num == 1
    assert p1.sentences[0].en == "Alan Seeger was born in New York in 1888."
    assert p1.sentences[0].ko == "Alan Seeger는 1888년 뉴욕에서 태어났다."

    p2 = passages[1]
    assert p2.label == "[고1] 2026년 6월 - 19번"
    assert len(p2.sentences) == 2


def test_missing_ko():
    """해석 없는 문장은 ko 가 빈 문자열."""
    raw = """[고2] 2026년 3월 - 20번: test
① This sentence has no translation.
② Neither does this one.
"""
    p = split_passages(raw)[0]
    assert len(p.sentences) == 2
    assert p.sentences[0].en == "This sentence has no translation."
    assert p.sentences[0].ko == ""


def test_mixed_line_split():
    """한 줄에 영/한이 섞이면 한글 첫 등장 위치에서 분리."""
    raw = "[고3] 2026년 5월 - 1번: mix\n① Hello world 안녕 세계입니다\n"
    p = split_passages(raw)[0]
    s = p.sentences[0]
    assert s.en == "Hello world"
    assert "안녕" in s.ko


def test_renderers_produce_html():
    passages = split_passages(SAMPLE)
    for fn in (render_format_a, render_format_c, render_format_b):
        html = fn(passages, header_text="OO학원", theme="modern")
        assert "<!DOCTYPE html>" in html
        assert 'id="passage-1"' in html
        assert 'id="passage-2"' in html
        assert "OO학원" in html

    # a 형식엔 해석 박스가, c 형식엔 없음
    a = render_format_a(passages)
    assert 'class="ko"' in a
    c = render_format_c(passages)
    assert "1888년 뉴욕" not in c  # 한줄영어엔 해석 미포함
    # b 형식엔 2단 표
    b = render_format_b(passages)
    assert 'class="two-col"' in b


def test_themes():
    for t in ("modern", "textbook", "middle", "", "unknown"):
        css = get_css(t)
        assert "break-before: page" in css
        assert "compact2" in css


def test_filename_safe():
    from main import safe_filename
    assert safe_filename('a/b:c*?"<>|d') == "a_b_c______d"
    assert safe_filename("  ") == "지문"


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
    sys.exit(0 if passed == len(fns) else 1)
