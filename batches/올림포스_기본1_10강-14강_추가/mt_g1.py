# -*- coding: utf-8 -*-
MT = {
    ("Unit10-2", 2): [
        "‘though’를 ‘비록’으로 읽으면 안 돼 — 문장 중간에 삽입된 [[though]]는 ‘하지만’이라 “하지만 똑같이 강한 충동은”이야.",
        "‘the company’를 ‘회사’로 읽으면 안 돼 — [[seek the company of others]]는 ‘다른 사람들과 어울리기를 원하다’야.",
    ],
    ("Unit10-2", 4): [
        "‘사람들에게 제공할 필요가 있다’로 읽으면 안 돼 — [[need other people to provide]]는 ‘다른 사람들이 제공해 주기를 필요로 한다’라서 provide의 주체는 other people이야.",
    ],
    ("Unit10-2", 5): [
        "뒤의 that절들을 따로 떼서 읽으면 안 돼 — [[that we are there, that we exist, that we have an identity]]는 모두 confirm의 목적어라 ‘~임을 확인해 주기를’이야.",
    ],
    ("Unit10-2", 6): [
        "‘교제 없이 존재할 수 없다’로만 읽으면 안 돼 — [[cannot ~ without seeking]]은 이중부정이라 ‘교제를 구해야만 존재할 수 있다’는 뜻이야.",
    ],
    ("Unit10-3", 1): [
        "도치를 놓치면 안 돼 — [[At one end of the spectrum was the forest gardening]]에서 진짜 주어는 the forest gardening이야.",
        "‘that’이 New Guinea·Amazonia를 꾸민다고 읽으면 안 돼 — [[that mimicked natural growth]]는 the forest gardening을 꾸며.",
    ],
    ("Unit10-3", 5): [
        "‘So did’를 ‘그래서 했다’로 읽으면 안 돼 — [[So did other, unwanted species]]는 도치라 ‘다른 원치 않는 종들도 그랬다’야.",
    ],
    ("Unit10-3", 6): [
        "‘Crops that ripened or were stored’를 통째로 문장 끝까지 이어 읽으면 안 돼 — 이건 관계절 수식이고 주동사는 [[attracted]]라 ‘~한 작물이 쥐를 끌어들였다’야.",
    ],
    ("Unit11-ANALYSIS", 1): [
        "‘using social media’를 주동사로 읽으면 안 돼 — [[teenagers using social media]]는 ‘소셜미디어를 쓰는 십대들’이고 주동사는 have discovered야.",
        "‘that sets them apart’가 teenagers를 꾸민다고 읽으면 안 돼 — [[behaviour that sets them apart]]라서 that은 behaviour를 꾸며.",
    ],
    ("Unit11-ANALYSIS", 2): [
        "‘set’을 동사로 읽으면 안 돼 — [[a set amount of time]]는 ‘정해진 양의 시간’이야.",
    ],
    ("Unit11-ANALYSIS", 4): [
        "‘what they're sharing’을 의문사절로 읽으면 안 돼 — [[what they're sharing]]은 ‘그들이 공유하는 것’이라는 관계사절이야.",
    ],
    ("Unit11-ANALYSIS", 5): [
        "‘A보다 B를 겪는다’로 읽으면 안 돼 — [[would rather delete than suffer]]는 ‘겪느니 차라리 삭제한다’야.",
    ],
    ("Unit11-ANALYSIS", 6): [
        "‘Not getting a reaction’을 부사처럼 읽으면 안 돼 — [[Not getting a reaction]]은 동명사 주어라 ‘반응을 얻지 못하는 것이’야.",
    ],
    ("Unit11-1", 1): [
        "‘moving the goalposts’를 ‘골대를 옮기다’로 읽으면 안 돼 — [[move the goalposts]]는 ‘기준·목표를 슬쩍 바꾸다’야.",
    ],
    ("Unit11-1", 2): [
        "‘it doesn't’를 그냥 ‘아니다’로 읽으면 안 돼 — [[it doesn't]]는 대동사라 ‘세상이 끝나지 않으면’이라는 뜻이야.",
    ],
    ("Unit11-1", 6): [
        "‘had another go’를 ‘또 갔다’로 읽으면 안 돼 — [[have another go]]는 ‘또 한 번 시도하다’야.",
    ],
    ("Unit11-1", 8): [
        "‘push back’을 ‘뒤로 밀치다’로만 읽으면 안 돼 — [[push this deadline back]]은 ‘마감을 뒤로 미루다’야.",
    ],
    ("Unit11-2", 4): [
        "‘to which it relates’를 따로 떼어 읽으면 안 돼 — [[the item to which it relates]]는 ‘그것이 관련되는 항목’이라 relate to의 to가 앞으로 나온 거야.",
    ],
    ("Unit11-2", 5): [
        "‘to use’의 주체를 헷갈리면 안 돼 — [[required one to find and to use]]는 ‘~가 찾고 또 사용하도록 요구했다’는 병렬 구조야.",
        "‘so that’을 ‘너무 ~해서’로 읽으면 안 돼 — [[so that new events could be understood]]는 ‘~할 수 있도록’이라는 목적이야.",
    ],
    ("Unit11-2", 6): [
        "‘was being told’를 ‘말하고 있었다’로 읽으면 안 돼 — [[a story was being told]]는 진행 수동이라 ‘이야기되고 있을 때’야.",
        "‘the story he was about to hear’에서 관계사 생략을 놓치면 안 돼 — [[the story (that) he was about to hear]]는 ‘그가 막 들으려던 이야기’야.",
    ],
}

_n = sum(len(v) for v in MT.values())
_sent = len(MT)
# validate: no ellipsis, balanced [[ ]], min length
for k, tips in MT.items():
    for t in tips:
        assert "…" not in t and "..." not in t, ("ellipsis", k)
        assert t.count("[[") == t.count("]]") and t.count("[[") >= 1, ("brackets", k)
        assert len(t) >= 12, ("len", k)

print("MT_G1 OK — %d sentences tipped" % _sent)
