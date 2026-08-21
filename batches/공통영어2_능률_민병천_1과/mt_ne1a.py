# -*- coding: utf-8 -*-
MT = {
    ("1 · 속보와 조난 경위", 1): [
        "‘found safe’를 [[안전하게 찾았다]]로 읽으면 안 돼 — [[was found safe]]는 ‘무사한 상태로 발견되었다’, safe는 주격보어야."
    ],
    ("1 · 속보와 조난 경위", 2): [
        "‘It turns out that’의 It을 앞 문장을 가리키는 대명사로 읽으면 안 돼 — [[It turns out that]]은 ‘~로 밝혀지다’는 비인칭 구문이야."
    ],
    ("1 · 속보와 조난 경위", 6): [
        "‘an experienced hiker who knew the area well’을 문장의 술어로 읽으면 안 돼 — 콤마 사이는 [[Compean]]의 동격·삽입이고 본동사는 [[went]]야."
    ],
    ("1 · 속보와 조난 경위", 7): [
        "‘which’를 의문사로 읽으면 안 돼 — 콤마 뒤 [[which]]는 앞 문장 전체를 받는 계속적 용법이야."
    ],
    ("1 · 속보와 조난 경위", 8): [
        "‘in case’를 [[~한 경우에]]로만 읽으면 안 돼 — 여기선 [[in case]]가 ‘~할 때에 대비하여’라는 뜻이야."
    ],
    ("2 · 구조 요청과 수색의 난관", 2): [
        "‘To make matters worse’를 문장 주어로 읽으면 안 돼 — [[독립부정사]]로 ‘설상가상으로’라는 부사야."
    ],
    ("2 · 구조 요청과 수색의 난관", 8): [
        "‘the police were informed of’를 경찰이 알렸다로 읽으면 안 돼 — [[be informed of]]는 ‘~을 통보받다’는 수동이야."
    ],
    ("2 · 구조 요청과 수색의 난관", 9): [
        "‘Despite searching’을 그들이 수색을 막았다로 읽으면 안 돼 — [[Despite]]는 전치사, ‘밤새 수색했음에도’라는 양보야."
    ],
    ("2 · 구조 요청과 수색의 난관", 12): [
        "끝의 ‘and his location settings were turned off’를 주절로 읽으면 안 돼 — [[because]] 절에 병렬로 묶인 두 번째 이유야."
    ],
    ("3 · 제보자 Ben Kuo의 등장", 1): [
        "‘his spending a second night’의 his를 소유격 명사로 읽으면 안 돼 — [[his]]는 동명사 [[spending]]의 의미상 주어야."
    ],
    ("3 · 제보자 Ben Kuo의 등장", 4): [
        "‘The picture shared by the police’의 shared를 본동사로 읽으면 안 돼 — [[shared]]는 과거분사 후치수식이고 본동사는 [[was seen]]이야."
    ],
    ("3 · 제보자 Ben Kuo의 등장", 5): [
        "‘informing’을 앞의 track과 병렬로 읽으면 안 돼 — [[examining]]과 [[informing]]이 is의 보어로 병렬이야."
    ],
}

for _k, _v in MT.items():
    assert len(_v) <= 2, _k
    for _t in _v:
        assert len(_t) >= 12, _k
        assert "..." not in _t and "…" not in _t, _k
        assert _t.count("[[") == _t.count("]]"), _k

print("MTNE_NE1A OK — %d sentences tipped" % len(MT))
