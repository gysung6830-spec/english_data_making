"""API 없이 레이아웃/디자인을 미리 보기 위한 목(mock) Analysis.

명세서 §11: '목업은 배관만 확인' — 실제 태깅 품질은 API 키로 검증.
이 데이터는 렌더러(A/B)가 모든 표현 요소(성분 라벨·오답형·하이라이트·포인트 박스·
미니 표)를 제대로 그리는지 확인할 수 있도록 대표 케이스를 담는다.
"""
from __future__ import annotations

from .models import Analysis, Point, Sentence, Token


def _T(text, role=None, note=None, kind="lbl", wrong=None, above=None,
       hl=None, underline=False, color=None) -> Token:
    return Token(text=text, role=role, note=note, note_kind=kind, wrong=wrong,
                 above=above, hl=hl, underline=underline, color=color)


def mock_analysis(title_en: str = "The Paradox of Choice",
                  lecture_label: str = "20", date: str = "2025년 09월") -> Analysis:
    s1 = Sentence(
        index=1,
        badge="주제",
        lines=[
            [
                _T("Researchers", role="S"),
                _T("have found", role="V", note="현재완료", kind="red"),
                _T("that people", role="O", note="that 명사절", kind="blue"),
            ],
            [
                _T("offered", note="과거분사(수동)", kind="red", wrong="offering(X)"),
                _T("more options", hl="y"),
                _T("often feel", note="지각 아님·본동사", kind="gray"),
                _T("less satisfied", role="C", note="비교급", kind="blue"),
            ],
        ],
        translation="연구자들은 더 많은 선택지가 주어진 사람들이 오히려 덜 만족한다는 것을 발견했다.",
        points=[
            Point(kind="reading", caption="1번 문장 독해 Point",
                  body_html="<b>주제문</b>: 선택지가 많을수록 만족은 <b>낮아진다</b>(역설). "
                            "이후 문장은 이 주장을 뒷받침한다."),
            Point(kind="grammar", caption="1번 문장 어법 Point",
                  body_html="<ul><li><b>offered</b> — 앞의 people 을 수식하는 <b>과거분사</b>"
                            "(사람이 '주어지는' 대상). 능동 <b>offering(X)</b> 함정.</li>"
                            "<li><b>that</b> — found 의 목적어절을 이끄는 <b>명사절 접속사</b>.</li></ul>"),
        ],
    )
    s2 = Sentence(
        index=2,
        badge="예시",
        lines=[
            [
                _T("When", note="시간 부사절", kind="blue"),
                _T("shoppers", role="S①"),
                _T("faced", role="V①", note="과거시제", kind="gray"),
                _T("a wall of jams"),
            ],
            [
                _T("which", note="주격 관계대명사", kind="red", wrong="that↔which"),
                _T("was displayed", role="V", note="수동태", kind="red", wrong="displayed(X)"),
                _T("attractively", above="it is 생략"),
            ],
            [
                _T("they", role="S②"),
                _T("bought", role="V②"),
                _T("less", role="O②", hl="g"),
            ],
        ],
        translation="쇼핑객들이 매력적으로 진열된 잼 진열대와 마주했을 때, 그들은 오히려 덜 샀다.",
        points=[
            Point(kind="grammar", caption="2번 문장 어법 Point",
                  body_html="<ul><li><b>which ~ was displayed</b> — 선행사 <b>a wall of jams</b> 를 "
                            "수식하는 <b>주격 관계대명사 + 수동태</b>. 관계사 자리 <b>that</b> 도 가능하나 "
                            "콤마 뒤라면 which 만.</li></ul>"
                            "<table><tr><th>구분</th><th>능동</th><th>수동</th></tr>"
                            "<tr><td>진열</td><td>displayed</td><td><b>was displayed</b></td></tr></table>"),
        ],
    )
    s3 = Sentence(
        index=3,
        badge="결론",
        lines=[
            [
                _T("To avoid", note="to-v(부사적, 목적)", kind="blue"),
                _T("this overload", note="= too many choices", kind="gray"),
                _T(",", ),
            ],
            [
                _T("experts", role="S"),
                _T("recommend", role="V", note="주어-동사 수일치", kind="red"),
                _T("limiting", role="O", note="동명사(목적어)", kind="blue", wrong="to limit(X)"),
                _T("the menu", underline=True),
            ],
        ],
        translation="이러한 과부하를 피하기 위해, 전문가들은 선택지를 제한할 것을 권한다.",
        points=[
            Point(kind="reading", caption="3번 문장 독해 Point",
                  body_html="<b>해결책 제시</b>: 문제(선택 과부하) ↔ 해결(<b>선택지 제한</b>) 대비 구조."),
            Point(kind="grammar", caption="3번 문장 어법 Point",
                  body_html="<b>recommend</b> 는 목적어로 <b>동명사(limiting)</b>. "
                            "to부정사 <b>to limit(X)</b> 는 오답."),
        ],
    )
    return Analysis(
        title_en=title_en,
        title_ko="선택의 역설 — 선택지가 많을수록 만족은 낮아진다",
        lecture_label=lecture_label,
        date=date,
        sentences=[s1, s2, s3],
    )
