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


def test_bracket_enclosed_number_header():
    """'[고3 2024년 03월 – 18번]'처럼 번호가 대괄호 안에 있고 콜론·제목이 없는
    헤더도 지문 경계로 인식해야 한다(못 잡으면 전 지문이 한 덩어리로 뭉쳐
    같은 번호 문장끼리 뒤섞이던 심각한 파싱 실패 방지)."""
    raw = ("[고3] 2024년 3월 모의고사 – 한줄해석\n"
           "[Flow Edu] flowedu.tistory.com\n- 1 -\n"
           "[고3 2024년 03월 – 18번]\n"
           "① It has been a privilege to serve here.\n"
           "① 이곳에서 일한 것은 영광이었습니다.\n"
           "② My last day will be April 30th.\n"
           "② 제 마지막 날은 4월 30일입니다.\n"
           "[고3 2024년 03월 – 19번]\n"
           "① Anna held on to the wreckage.\n"
           "① Anna는 잔해에 매달렸다.\n"
           "[고3 2024년 03월 – 41~42번]\n"
           "① This is a long passage.\n"
           "① 이것은 장문이다.\n")
    ps = split_passages(raw)
    assert len(ps) == 3                       # 세 지문으로 분리(한 덩어리 방지)
    assert ps[0].label.endswith("18번")
    assert len(ps[0].sentences) == 2          # 번호 병합 없이 문장 2개
    assert ps[0].sentences[0].en == "It has been a privilege to serve here."
    assert ps[1].label.endswith("19번")
    assert ps[2].label.endswith("41~42번")    # 범위 라벨 정규화
    # 자료 머리글/라벨이 문장에 새지 않음
    assert all("고3 2024" not in s.ko and "번]" not in s.ko
               for p in ps for s in p.sentences)


def test_summary_label_split():
    """'[요약문]' 라벨(한글 포함)이 붙은 요약문 문항: 영어 요약문이 통째로 해석
    쪽으로 넘어가거나 '['만 영어로 잘려 나가면 안 된다(요약문/[Summary] 버그)."""
    raw = ("[고1] 2024년 06월 - 40번: 요약문 test\n"
           "⑥ [요약문] The needs of people have often been overlooked, which could\n"
           "be changed by adopting an inclusive design.\n"
           "⑥ [요약문] 장애가 있는 사람들의 요구는 종종 간과되어 왔으며, 변화될 수 있다.\n")
    p = split_passages(raw)[0]
    s = p.sentences[0]
    assert s.en == ("The needs of people have often been overlooked, "
                    "which could be changed by adopting an inclusive design.")
    assert s.en.lstrip()[0] != "["          # 라벨 대괄호 잔존 금지
    assert "needs of people" not in s.ko      # 영어가 해석에 섞이지 않음
    assert "요약문" not in s.ko and "요약문" not in s.en  # 라벨 제거됨
    assert s.ko.startswith("장애가")


def test_cid_glyph_token_stripped():
    """PDF 글리프 매핑 실패 토큰 '(cid:8796)'(원문자 ①② 등이 디코딩 안 된 것)이
    본문에 섞이면 지워야 한다. 남으면 문장 분리를 망가뜨려 en/해석이 어긋난다."""
    raw = ("[고3] 2025년 06월 - 43번: cid test\n"
           "① I bought some blueberries. (cid:8797) Would you like to come?\n"
           "① 나는 블루베리를 좀 샀어. 우리 집에 올래?\n")
    p = split_passages(raw)[0]
    joined_en = " ".join(s.en for s in p.sentences)
    assert "cid:" not in joined_en
    assert "(cid" not in joined_en


def test_proper_noun_josa_not_split():
    """해석이 '이름+조사'(Linda는/Sean이)로 시작하는 한글 문장에서, 앞의 라틴
    고유명사를 영어로 떼어내면 안 된다(해석이 '는…'으로 시작하고 이름이 영어
    쪽에 고아로 남아 en/해석 정렬이 깨지던 장문 43~45 버그)."""
    from parser import _split_mixed_line
    # 이름+조사 밀착 → 통째로 한글
    assert _split_mixed_line("Linda는 대답으로 고개를 끄덕였다.") == (
        "", "Linda는 대답으로 고개를 끄덕였다.")
    assert _split_mixed_line("Sean이 돌에 걸려 넘어졌다.") == (
        "", "Sean이 돌에 걸려 넘어졌다.")
    # 경칭 포함 다어절 이름('Ms. Blake는')도 통째로 한글
    assert _split_mixed_line("Ms. Blake는 단호하게 말했다.") == (
        "", "Ms. Blake는 단호하게 말했다.")
    # 진짜 영/한 혼합줄(영어 여러 단어 + 공백 후 한글)은 그대로 분리
    en, ko = _split_mixed_line("The weather was perfect 날씨는 완벽했다.")
    assert en == "The weather was perfect" and ko == "날씨는 완벽했다."
    # 영어 문장 뒤에 이름이 밀착해도(소문자 기능어 포함) 이름구 아님 → 정상 분리
    en, ko = _split_mixed_line("said firmly Ms. Blake는 단호하게 말했다.")
    assert en == "said firmly Ms. Blake" and ko.startswith("는")


def test_cid_marker_restored_from_pair():
    """영어줄의 원문자 문장 마커가 '(cid:NNNN)'로 디코딩 실패하면, 뒤따르는
    한글 짝줄의 번호로 마커를 복원해야 한다. 마커가 사라지면 그 영어 문장이 앞
    문장에 흡수돼 en/해석 정렬이 통째로 밀린다(장문 43~45 근본 버그)."""
    raw = (
        "[고2] 2025년 03월 - 43~45번: story\n"
        "⑳ Soccer isn't about perfection.\n"
        "⑳ 축구는 완벽함에 관한 것이 아니다.\n"
        "(cid:8796) And you've always had plenty of that.\n"
        "㉑ 그리고 너는 항상 그것을 많이 갖고 있었다.\n"
        "(cid:8797) Ms. Blake said firmly.\n"
        "㉒ Ms. Blake는 단호하게 말했다.\n"
    )
    p = split_passages(raw)[0]
    by = {s.num: s for s in p.sentences}
    # 21번 영어 문장이 20번에 흡수되지 않고 독립 + 정렬
    assert by[20].en == "Soccer isn't about perfection."
    assert by[21].en == "And you've always had plenty of that."
    assert by[21].ko.startswith("그리고")
    # 22번: 이름+조사 보존, 조사로 시작하지 않음
    assert by[22].en == "Ms. Blake said firmly."
    assert by[22].ko == "Ms. Blake는 단호하게 말했다."
    assert "cid" not in by[21].en and "cid" not in by[22].en


def test_fill_chunk_meanings():
    """뜻(ko)이 빈 청크를 조각 번역으로 채우는 보강 패스(긴 문장 직독직해 뜻
    누락 대비). 개수·순서가 맞으면 빈 곳만 채우고, 이미 있는 뜻은 보존한다."""
    import json as _json
    from chunker import _fill_chunk_meanings
    from parser import Chunk

    class _Blk:
        type = "text"
        def __init__(self, t): self.text = t
    class _Resp:
        def __init__(self, t): self.content = [_Blk(t)]
    class _Msgs:
        def create(self, **kw):
            return _Resp(_json.dumps({"ko": ["첫째 뜻", "둘째 뜻", "셋째 뜻"]}))
    class _Client:
        messages = _Msgs()

    chunks = [Chunk(en="A", ko=""), Chunk(en="B", ko="이미 있음"),
              Chunk(en="C", ko="")]
    out = _fill_chunk_meanings(_Client(), "m", chunks)
    assert out[0].ko == "첫째 뜻"          # 빈 곳 채움
    assert out[1].ko == "이미 있음"         # 기존 뜻 보존
    assert out[2].ko == "셋째 뜻"
    assert all(c.ko.strip() for c in out)  # 빈 뜻 없음


def test_fill_chunk_meanings_count_mismatch():
    """번역 배열 개수가 청크 수와 다르면 반영하지 않는다(잘못된 정렬 방지)."""
    import json as _json
    from chunker import _fill_chunk_meanings
    from parser import Chunk

    class _Blk:
        type = "text"
        def __init__(self, t): self.text = t
    class _Resp:
        def __init__(self, t): self.content = [_Blk(t)]
    class _Msgs:
        def create(self, **kw):
            return _Resp(_json.dumps({"ko": ["하나만"]}))  # 개수 불일치
    class _Client:
        messages = _Msgs()

    chunks = [Chunk(en="A", ko=""), Chunk(en="B", ko="")]
    out = _fill_chunk_meanings(_Client(), "m", chunks, attempts=1)
    assert out[0].ko == "" and out[1].ko == ""  # 개수 안 맞으면 그대로


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
    # AI가 여러 조각으로 나누고 조각마다 뜻을 달았지만 영어가 원문과 어긋난 경우:
    # 뜻(ko)은 보존하되 '영어는 원문 단어로 되돌려' 100% 일치시켜야 한다.
    # (1) 단어 치환: 'your'를 'our'로 바꿈 → 영어는 'your'로 복원, 뜻 보존.
    sub = [
        Chunk(en="We greatly appreciate", ko="우리는 감사하는데"),
        Chunk(en="our continued use", ko="여러분의 지속적인 이용에"),  # your→our 오류
        Chunk(en="of our sports center.", ko="스포츠 센터를"),
    ]
    o = realign_chunks("We greatly appreciate your continued use of our sports center.", sub)
    assert _L(" ".join(c.en for c in o)) == _L("We greatly appreciate your continued use of our sports center.")
    assert o[1].en == "your continued use"        # 원문 단어로 복원
    assert o[1].ko == "여러분의 지속적인 이용에"    # 뜻 보존
    # (2) 단어 삽입: 'that'을 끼워 넣음 → 영어에서 that 제거, 뜻 보존.
    ins = [
        Chunk(en="we intuitively assume", ko="우리는 직관적으로 가정한다"),
        Chunk(en="that it reflects an increase.", ko="그것이 증가를 반영한다고"),  # +that
    ]
    o2 = realign_chunks("we intuitively assume it reflects an increase.", ins)
    assert _L(" ".join(c.en for c in o2)) == _L("we intuitively assume it reflects an increase.")
    assert "that" not in o2[-1].en.split()          # 삽입된 that 제거됨
    assert o2[-1].ko == "그것이 증가를 반영한다고"    # 뜻 보존


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
