# 소단원 authoring 규격 (YBM 공통영어2 박준언 1과 · Fake News)

너는 한국 고교 영어독해 교재("필생보" 스타일) 저자다. 배정된 **소단원**의 지문 문장들을 받아,
`LecturePassage` 데이터를 파이썬으로 작성한다. 아래 규칙을 **하나도 빠짐없이** 지킨다.
채점은 `verify.py`로 자동 검증되며, 특히 **끊어읽기 en 조각을 이으면 원문과 정확히 일치**해야 한다.

## 출력 계약
- 파일: 지정된 경로에 UTF-8, 첫 줄 `# -*- coding: utf-8 -*-`.
- 시작부:
  ```python
  # -*- coding: utf-8 -*-
  import sys; sys.path.insert(0, "/tmp/claude-0/-home-user-english-data-making/3e2ff8b7-89bb-5341-95ca-4062ce95757b/scratchpad/batches/공통영어2_YBM_박준언_1과")
  from _helpers import *
  ```
- 각 소단원마다 `r`(문장 리스트, 주어진 순서 그대로), `ov`(Overview), `items`(SentenceItem 리스트)를 만들고
  `Pxx = build("제목", "item_no", r, ov, items)` 로 조립.
- 모듈 마지막에 `PARTS = [P1, P2, ...]` (배정된 소단원들, 목차 순서대로). **finalize는 호출하지 마라**(상위 build.py가 처리).
- 주어진 문장 텍스트는 **한 글자도 바꾸지 마라**(대소문자·구두점·따옴표 포함). `r` 배열에 그대로 넣는다.

## 헬퍼(_helpers.py) 사용
- `S(r, i, grammar, vocab, chunks, misreads)` — i번째 문장(1-index). 각 인자는 튜플 리스트:
  - grammar = `[("칩라벨","한 줄 설명"), ...]`  (1~3개)
  - vocab   = `[("word","뜻"), ...]`
  - chunks  = `[("en 조각","ko 조각"), ...]`
  - misreads= `[("틀린 진술(X)","왜 틀렸나+바른 뜻"), ...]`  (1~2개)
- `GN("칩","설명")` — 핵심문법 설명 한 줄.
- `Overview(theme_ko=, key_grammar=KeyGrammar(...), topic=, stance=, stance_reason=, structure=, structure_reason=, restatement_chains=[...], flow_blocks=[...])`
- `build(title, no, r, ov, items)` — 조립(문장수 검증 포함).

## 값 제약(반드시 유효값)
- `stance` ∈ {"긍정적","부정적·비판적","중립적"}
- `structure` ∈ {"통념→반박(반전)","주장→근거·예시","문제→해결(방안)","비교·대조","시간·순서(나열)","예시→일반화(결론)"}

## ③ 끊어읽기(chunks) — 가장 중요
1. **원문 보존**: 각 문장의 en 조각을 순서대로 이으면 원문 문장과 **정확히 동일**해야 한다(단어 추가·삭제·철자·순서 변경 금지). `[[ ]]`는 이미 있는 텍스트를 **감싸기만** 한다.
2. **끊는 세기**: '절~큰 구' 수준, **문장당 2~4조각**. 긴 주어 뒤/전치사구·부정사구·분사구·관계사절·접속사절 앞에서 끊는다. 한 조각이 대략 12단어 넘으면 큰 구 경계에서 한 번 더 끊어 조각당 4~10단어.
3. **빈칸(중요)**: en·ko 짝으로 `[[ ]]`를 넣는다.
   - (통째 빈칸) 오역 위험 큰 조각은 **조각 전체**를 `[[ ]]`로. **문장당 최대 2개.**
   - (단어 빈칸) 나머지 조각은 **각 조각마다 핵심 단어 1개**를 `[[ ]]`로. en에 넣으면 ko의 대응 단어에도 반드시 넣는다(짝 필수).
   - **내용어(명사·동사·형용사·부사 등 뜻 있는 4글자+ 단어)가 든 조각은 빠짐없이 빈칸 1개.** 순전한 기능어(관사·전치사·접속사·대명사·be동사)만 있는 조각만 예외.
   - en의 `[[ ]]`와 ko의 `[[ ]]`는 유무가 **항상 같아야** 한다.

## 문장 문법칩(grammar)
- 문장당 1~3개. **다음 어법은 있으면 항상 표기**(개수 제한 없음): 도치·강조구문·동격 that·비교급/최상급·분사구문·수동태·가정법. 그리고 **생략된 어법**(병렬 공통요소 생략, 관계부사 생략 등)도 있으면 표기.
- 지문에 실제로 있는 것만. 용어 정확히(예: 감정 형용사 vs 부정사, 대명사 vs 대동사 혼동 금지).

## ④ 오답(misreads) — "오답만 읽어도 내용 이해되게"
- 모든 문장에 **최소 1개**, 최대 2개. **전부 '틀린(X) 진술'**(정답 진술 넣지 마라).
- 각 `why`는 **왜 틀렸는지 + 바른 뜻**을 쉬운 말로(최소 15자 이상, 보통 40~80자). 지문 근거(영어 표현 인용)를 넣으면 좋다.
- **단어 번역 실수(어휘·직역)는 넣지 마라** — 그건 빈칸 담당. 오답은 '의미/역할/함축/지칭'만 다룬다.
- 지시어(this/that/they/it/these 등)가 쓰인 문장에는 가능하면 **(지칭) 오답**을 하나 넣어 무엇을 가리키는지 바로잡는다.
- 반어·가정법·속뜻이 있는 문장에는 **(함축) 오답**을 넣는다.
- 소단원 전체로 볼 때 지칭·함축 층위가 최소 한 번씩은 등장하도록.

## ⑤ 핵심문법(key_grammar) — 소단원당 1개
- `point`: 이 소단원에서 가장 중요한 어법 1개(문장칩 규칙의 '항상 표기' 어법 중 택1 권장).
- `source_sentence`: 그 어법이 **실제로 나온 이 소단원 문장 원문**(r 안의 문장 그대로).
- `explanation`: `GN` 3~6개. 설명 안 핵심어를 `[[ ]]`로 감싸면 학생용 빈칸이 됨(각 줄 1~2개).
- `example_analysis`: 그 문장에서 무엇이 도치/생략/수식/시제됐는지 한 줄.
- `drills`: **정확히 5개 = 객관식 3 + 영작 2**.
  - 객관식: `GrammarDrill(kind="객관식", from_passage=True/False, question=, options=[3~4개], answer="정답 원문")` — answer는 options 중 하나와 정확히 일치. (정답 위치는 신경 쓰지 마라; 상위에서 분산 처리)
  - 영작: `GrammarDrill(kind="영작", from_passage=True/False, question="한국어 문장", answer="영어 정답")` — `words`는 넣지 마라(상위에서 자동 생성). 영작 2개 중 1개는 지문 문장 복원(from_passage=True), 1개는 응용(False).

## restatement_chains(재진술 사슬)
- 1~2개. 각 `expressions`는 **지문 문장에 실제로 나온 영어 표현 2개 이상**(원문의 부분 문자열 그대로, `…`/`...` 금지). 학생용에서 형광펜 매칭에 쓰이므로 반드시 verbatim.

## flow_blocks
- 2~6개. 소단원의 **모든 문장 id**를 `sentence_range`로 빠짐없이 덮는다(예 "1~2","3","4~5"). `summary` 한 줄(핵심어 `[[ ]]` 가능), `stage`는 도입/전개/사례/조건/전환/대조/확장/결론 등.

---
## 완성 예시(그대로 형식 참고 — 실제 8문장 소단원)
```python
r1=["You are on a camping trip with your family or friends.",
"After a long day of hiking, you take a quick shower, sit in your favorite camping chair, pick up a soda, and let out a deep, contented sigh.",
"Right at that moment, you hear that annoying and familiar buzzing sound."]
ov1=Overview(theme_ko="캠핑의 평화를 깨는 모기의 습격",
 key_grammar=KeyGrammar(point="분사구문 (동시동작: -ing로 부사절 축약)",
  source_sentence="Beating its wings as fast as 600 times per second, a mosquito sneaks in and pierces your skin with its straw-like mouthparts.",
  explanation=[GN("쉽게 말하면","콤마로 붙은 '-ing ~'는 '접속사+주어'를 지운 [[분사구문]]으로 '~하면서'라는 동시상황."),
   GN("복원","Beating its wings ~ = [[As it beats]] its wings ~."),
   GN("의미상 주어","분사의 주인은 주절 주어와 [[같아]] — 여기선 a mosquito.")],
  example_analysis="Beating its wings ~, a mosquito sneaks in = 분사구문(동시동작).",
  drills=[GrammarDrill(kind="객관식",from_passage=True,question="지문 'Beating its wings ~'의 기능은?",
    options=["동시상황을 나타내는 분사구문","관계사절","조건 부사절"],answer="동시상황을 나타내는 분사구문"),
   GrammarDrill(kind="객관식",from_passage=False,question="밑줄이 '분사구문'인 것은?",
    options=["Smiling brightly, she waved.","The girl smiling is my sister.","Her smiling face is lovely."],answer="Smiling brightly, she waved."),
   GrammarDrill(kind="객관식",from_passage=False,question="'____ the door, he went out.'(문을 닫으면서)",
    options=["Closing","Closed","To close"],answer="Closing"),
   GrammarDrill(kind="영작",from_passage=False,question="음악을 들으면서, 그녀는 저녁을 요리했다.",answer="Listening to music, she cooked dinner."),
   GrammarDrill(kind="영작",from_passage=True,question="(지문) 날갯짓을 하면서, 모기가 몰래 들어와 피부를 찌른다.",answer="Beating its wings, a mosquito sneaks in and pierces your skin.")]),
 topic="캠핑 중 모기가 다가와 피를 빠는 도입 장면.",
 stance="중립적",stance_reason="습격 장면을 묘사하는 도입부.",
 structure="시간·순서(나열)",structure_reason="쉬다가→소리→찌르는 시간 순서.",
 restatement_chains=[RestatementChain(label="성가신 존재",
   expressions=["annoying and familiar buzzing sound","how do mosquitoes find their victims"],
   variation="'성가신 소리' → '먹잇감 탐지'로 이어짐.")],
 flow_blocks=[FlowBlock(stage="도입",sentence_range="1~2",summary="가족·친구와 캠핑 중 편히 쉰다."),
  FlowBlock(stage="습격",sentence_range="3",summary="바로 그때 윙윙 소리가 들린다.")])
i1=[S(r1,1,[("be on a trip","'여행 중이다'")],
  [("camping trip","캠핑 여행")],
  [("You are [[on a camping trip]] with your family or friends.","당신은 가족·친구와 [[캠핑 여행 중이다]].")],
  [("이 문장은 모기의 생태를 설명한다.","'on a camping trip(캠핑 중)'으로 독자를 상황에 놓는 도입 문장이야.")]),
 S(r1,2,[("병렬 동사","take, sit, pick up, and let out 나열")],
  [("let out","(소리를) 내다"),("contented","만족한")],
  [("After a long day of hiking,","등산으로 긴 하루를 보낸 뒤,"),
   ("you [[take a quick shower, sit in your favorite camping chair, pick up a soda]],","당신은 [[샤워하고, 캠핑 의자에 앉고, 음료를 집어 들고]],"),
   ("and [[let out a deep, contented sigh]].","[[깊고 만족스러운 한숨을 내쉰다]].")],
  [("불편하게 쉬는 모습이다.","'contented sigh(만족한 한숨)'로 편안히 쉬는 장면 — 불편이 아니야.")]),
 S(r1,3,[("지시 that","'그 (익숙한)'")],
  [("annoying","성가신"),("buzzing","윙윙거리는")],
  [("Right at that moment, you hear","바로 그때, 당신은 듣는다"),
   ("that [[annoying and familiar buzzing sound]].","그 [[성가시고 익숙한 윙윙 소리]]를.")],
  [("즐거운 음악이 들린다는 내용이다.","'annoying buzzing sound(성가신 윙윙 소리)'야 — 즐거운 게 아니라 모기 소리.")])]
P1=build("Fake News (예시 소단원)","도입 · 0 (예시)",r1,ov1,i1)
PARTS=[P1]
```

---
## ★ 이 배치(뉴스 리포트) 추가 지침 — "An Unusual Rescue Effort"
- 이 지문은 **뉴스 리포트(앵커→기자 중계)** 형식의 사건 전개다. 대체로 설명문처럼 처리하되, 사건 사실 관계가 중요하다.
- **key_grammar 는 배정 JSON의 `key_grammar_hint` 로 지정된 어법을 그대로 사용**(소단원마다 다르게 배정 → 합본 중복 없음). source_sentence 는 그 어법이 실제로 든 이 소단원 beat 원문.
- **misreads(오답)**: 어휘 오역이 아니라 '**사건 사실(무엇이 원인·결과인지) / 인물 행동·의도 / 함축 / 지칭(it·this·they·those 등이 무엇을 가리키나)**'를 겨냥. 예: 산불이 표지판을 망가뜨려 길을 잃음(인과), the picture가 왜 도움이 안 됐나(화질·위치설정), Kuo가 남쪽이라 추론한 근거(식물·재), 'those'=green valleys(지칭). 각 소단원에 지칭·함축 최소 한 번씩.
- stance: 사건 보도 부분은 "중립적". 안전 당부(마무리)는 "부정적·비판적"(경고) 가능.
- structure: 시간순 사건 전개 → "시간·순서(나열)"가 자연스럽다.
