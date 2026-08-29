"""오프라인 테스트: 파서 + 렌더러 + 테마 (무거운 의존성 불필요)."""
import sys
from pathlib import Path

# passage3 디렉터리를 import 경로에 추가
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parser import (Passage, Sentence, split_passages, circled_to_int,  # noqa: E402
                    Chunk, realign_chunks)
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


def test_pdfparse_helpers():
    """표 파서의 순수 함수(헤더 분리·셀 문장화) 검증."""
    from pdfparse import _split_header, _cell_sentences, _looks_like_header

    # 헤더 분리: 대괄호 없는 'Ch. .. N번: 제목' 형식도 처리
    label, title = _split_header("Ch. 04 Unit 10 - 2번: 자신의 존재와 정체성")
    assert label == "Ch. 04 Unit 10 - 2번"
    assert title == "자신의 존재와 정체성"
    # ANALYSIS 처럼 '번' 없는 헤더도 콜론 기준 분리
    label2, title2 = _split_header("Ch. 04 Unit 11 - 수능 대비 ANALYSIS: 소셜 미디어")
    assert label2.endswith("ANALYSIS") and title2 == "소셜 미디어"

    # 셀 → 문장(영어/한글 쌍)
    sents = _cell_sentences("① Although the wish to be alone is often strong.",
                            "혼자 있고 싶은 소망은 종종 강하다.")
    assert len(sents) == 1
    assert sents[0].num == 1
    assert sents[0].en == "Although the wish to be alone is often strong."
    assert sents[0].ko == "혼자 있고 싶은 소망은 종종 강하다."

    # 개행이 섞인 셀도 공백 정리
    s2 = _cell_sentences("① first line\nsecond line", "해석\n둘째 줄")[0]
    assert s2.en == "first line second line"
    assert s2.ko == "해석 둘째 줄"

    assert _looks_like_header(["Ch. 04 Unit 10 - 2번: 제목"]) is True
    assert _looks_like_header(["① This is a sentence."]) is False


def test_renumber_offset():
    """재입력(27·28 이미 제외) + 시작번호 지정 시 번호가 밀리지 않아야 함."""
    from main import renumber_passages, drop_practical_items, is_mock_exam
    labels = (["18번", "19번", "20번", "21번", "22번", "23번", "24번", "25번",
               "26번", "29번", "30번"] + ["41~42번", "43~45번"])
    ps = [Passage(label=l, title="",
                  sentences=[Sentence(num=1, en="a b c d e", ko="ㄱ")])
          for l in labels]
    ps = renumber_passages(ps, 18)          # 첫 지문 18 → offset 0
    assert [p.label for p in ps] == labels   # 그대로(밀림 없음)
    assert is_mock_exam(ps, "모의고사")
    # 27·28 은 애초에 없으니 제외해도 실제 지문이 사라지지 않음
    assert len(drop_practical_items(ps)) == len(labels)
    # 오프셋(+2): 간격·범위 보존
    ps2 = [Passage(label=l, title="", sentences=[]) for l in ["18번", "29번", "41~42번"]]
    ps2 = renumber_passages(ps2, 20)
    assert [p.label for p in ps2] == ["20번", "31번", "43~44번"]


def test_realign_chunks():
    """직독직해 청크를 원문에서 그대로 다시 잘라 100% 일치시키는지 검증."""
    en = ('A creature must get from the place it is born—often occupied by '
          'its parent—to a place where it can survive.')
    # AI가 대시 주변에 공백을 넣고 마지막 마침표를 흘린 청크(원문과 미세 불일치)
    chunks = [
        Chunk(en="A creature must get", ko="생물은 이동해야 한다"),
        Chunk(en="from the place it is born —often occupied by its parent—",
              ko="태어난 곳에서 (흔히 부모가 차지한)"),
        Chunk(en="to a place where it can survive", ko="살아남을 수 있는 곳으로"),
    ]
    out = realign_chunks(en, chunks)
    # 조각을 이어 붙이면(공백 join) 원문과 영숫자 순서가 정확히 일치
    from parser import _letters
    assert _letters(" ".join(c.en for c in out)) == _letters(en)
    # 마지막 조각이 끝 마침표를 포함
    assert out[-1].en.endswith("survive.")
    # 대시가 앞 조각 끝에 붙고 다음 조각은 'to'로 시작(원문 그대로)
    assert out[1].en.endswith("parent—")
    assert out[2].en.startswith("to a place")
    # 뜻(ko)은 보존
    assert out[0].ko == "생물은 이동해야 한다"
    # 청크가 원문과 글자 수준으로 다르면(단어 추가/누락) 원문을 규칙 기반으로
    # 다시 끊어 영어가 항상 원문과 일치하게 한다.
    bad = [Chunk(en="A creature must get that from the place", ko="x")]
    out2 = realign_chunks(en, bad)
    from parser import _letters as _L
    assert _L(" ".join(c.en for c in out2)) == _L(en)  # 원문과 100% 일치


def test_tidy_chunk_ko():
    """강제 '~다' 종결로 생긴 '다다' 중복만 하나로 줄이고 정상 텍스트는 보존."""
    from parser import tidy_chunk_ko
    assert tidy_chunk_ko("있는 고양이보다다") == "있는 고양이보다"
    assert tidy_chunk_ko("경험했다다.") == "경험했다."
    assert tidy_chunk_ko("여겨질 수 있다다") == "여겨질 수 있다"
    # 정상 한국어는 그대로
    assert tidy_chunk_ko("반대 의견을 지지한다고 한다") == "반대 의견을 지지한다고 한다"
    assert tidy_chunk_ko("고양이보다") == "고양이보다"
    assert tidy_chunk_ko("전문가가 자신이") == "전문가가 자신이"
    # 비술어 억지 종결('~에서다/있어서다') → 끝의 '다' 제거
    assert tidy_chunk_ko("여섯 나라 중에서다") == "여섯 나라 중에서"
    assert tidy_chunk_ko("그것의 정의에 있어서다") == "그것의 정의에 있어서"
    assert tidy_chunk_ko("무언가를 이루기 위해서다") == "무언가를 이루기 위해서"
    assert tidy_chunk_ko("보일 수 있는 전체에 의해서다") == "보일 수 있는 전체에 의해서"


def test_rough_sense_split():
    """규칙 기반 폴백 끊어읽기: 원문 보존 + 과도하게 길지 않게 분할."""
    from parser import rough_sense_split, _letters
    en = ("Those who have found deeper meaning in their careers find their days "
          "much more energizing and satisfying, and count their employment as one "
          "of their greatest sources of joy and pride.")
    pieces = rough_sense_split(en)
    assert len(pieces) >= 3
    # 원문 영숫자 순서 보존
    assert _letters(" ".join(pieces)) == _letters(en)
    # 한 조각이 지나치게 길지 않음
    assert max(len(p.split()) for p in pieces) <= 11
    # 짧은 문장은 그대로 한 조각
    assert rough_sense_split("Some snakes can detect heat.") == ["Some snakes can detect heat."]


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
