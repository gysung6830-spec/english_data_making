# 고3 2025-09 모의고사 '필생보' 전체 저작 규격

입력: /.../scratchpad/moui1_prose.json (14지문. 각 item_no·theme·sentences[id,english,korean(공식 한줄해석 참고용)])
출력: 배정된 지문마다 /.../scratchpad/moui1/passages/p<item>.json  (한 지문 = 한 파일)
※ english 원문은 moui1_prose.json 그대로 사용(수정 금지). korean 은 참고용(직접 새로 써도 됨).

## 지문 JSON 구조
{
 "item_no": "29",              // 그대로
 "theme": "<moui_data의 theme>",
 "overview": {
   "theme_ko": "지문 제목용 한글 명사구",
   "topic": "🔎 소재 한 줄",
   "stance": "긍정적" | "부정적·비판적" | "중립적",
   "stance_reason": "근거 한 줄(지문 표현으로)",
   "structure": "통념→반박(반전)"|"주장→근거·예시"|"문제→해결(방안)"|"비교·대조"|"시간·순서(나열)"|"예시→일반화(결론)",
   "structure_reason": "근거 한 줄",
   "key_grammar": {
     "point": "이 지문 핵심 문법 1개(★지문마다 반드시 서로 달라야 함 — 배정표 참고)",
     "source_sentence": "그 문법이 나온 지문 원문 문장 전체(english 에서 그대로)",
     "explanation": [ {"chip":"쉽게 말하면","text":"..."}, ... 3~6개 ],  // 칩+설명 한 줄씩. text 핵심어는 [[ ]]로 빈칸 가능
     "example_analysis": "그 문장에서 무엇이 도치/생략/수식됐는지 한 줄",
     "drills": [  // 정확히 5개: 객관식 3 + 영작 2
       {"kind":"객관식","question":"...","options":["...","...","..."],"answer":"<options 중 하나 원문>","from_passage":true},
       {"kind":"객관식",...}, {"kind":"객관식",...},
       {"kind":"영작","question":"<한국어 문장>","words":["제시","어","...(반드시 제공)"],"answer":"<영어 정답>","from_passage":true},   // 1개는 지문 문장 복원
       {"kind":"영작","question":"<한국어>","words":[...],"answer":"<영어>","from_passage":false}                                  // 1개는 응용
     ]
   },
   "restatement_chains": [ {"label":"개념 한글名","expressions":["지문 속 영어표현1","표현2",...(2개↑)],"variation":"변주 한 줄"} ],  // 1~2개. expressions 는 반드시 english 에 '그대로' 존재. 핵심소재 위주, 최대 2개 사슬.
   "flow_blocks": [ {"stage":"도입/전개/사례/전환/결론 등","sentence_range":"1~2","summary":"한 줄(핵심어 [[ ]] 가능)","easy_example":"주제 관련 쉬운 비유 한 줄"} ]  // 2~6개, 전 문장 커버
 },
 "sentences": [ {
   "id": 1, "english": "<moui_data 그대로>",
   "grammar": [ {"tag":"짧은 어법명","note":"한 줄 설명","spans":["형광펜 표지 어구(english 그대로, 최소)"]} ],  // 1~3개. 아래 C 참고
   "vocab": [ {"word":"중고등 어휘/숙어","meaning":"뜻"} ],  // 2~5개. 초등 수준 단어 제외
   "chunks": [ {"en":"의미 조각","ko":"직독직해"} ],  // 아래 B(끊어읽기+빈칸) 규칙 필수
   "misreads": [ 오답객체 ],   // 아래 D(O/X/△) 규칙 필수
   "mistips": ["구문 오독 팁(0~2개, 없으면 생략)"]   // '~로 읽으면 안 돼 — (바르게는) ~', 핵심어 [[ ]]
 } ]
}

## B. 끊어읽기(chunks) + 빈칸 — ★가장 중요
- en 을 순서대로 이으면 그 문장 english 와 '정확히 같아야' 함(단어·구두점 다 포함; [[ ]]만 빼면 동일). 첫 조각에 주어·동사 포함.
- 세기: '구와 절의 중간'. 조각당 5~10단어, 3단어 이하 미세 조각(it always 등) 금지→인접에 병합. 문장당 2~4(길면 5)조각.
- 빈칸(ko 에 [[ ]]):
  · 통째 빈칸 = 오역 위험이 큰 '3단어 이상 구·절' 조각 전체를 en·ko 모두 [[ ]]. 문장당 최대 2개.
  · 단어 빈칸 = 나머지 조각은 각 조각의 '핵심 단어 1개'만 ko 에서 [[ ]](en 은 강조표시). ★내용어(명사·동사·형容사·부사)가 든 조각은 빠짐없이 빈칸 1개. 순전한 기능어(관사·전치사·접속사·대명사·be)만 있는 조각은 예외.
  · en 과 ko 의 [[ ]] 유무는 짝이 맞아야(같은 조각에 둘 다 있거나 둘 다 없거나).
  · 말줄임표(...·…) 금지.

## C. 어법 형광펜(spans) — 강사용
각 grammar 칩마다 그 어법의 '표지 부분만' english 에서 그대로 복사(최소). 관계사=that/which 한 단어·수동태=be+p.p.·분사=분사구 머리·to부정사=to-V·5형식=동사+보어 표지 각각·상관구조(not A but B)=not,but 각각. 못 잡으면 spans=[]. 절/문장 전체 복사 금지.

## D. 오답(misreads) = O/X/△ (문장당 1~2개, 최대 2) — 내신·2등급
오답객체={statement, verdict, trap_type, anchor, why, killer?, english?, integrative?}
- verdict: "O"(참)/"X"(틀림)/"△"(결론·방향 맞고 근거·이유 틀림). O는 statement(한국어)만.
- trap_type ∈ [주체대상, 인과조건, 지칭, 무관정보, 필자관점, 구조수식]. 트리거 있는 문장에만.
- anchor(X·△): 반박 근거를 그 문장 english 에서 '그대로 복사'(연속 부분문자열; 통합추론이면 다른 문장도 가능).
- why(X·△): 한국어 한 줄(15자↑), anchor 근거로 결정적 한 곳만.
- 지문 단위: 참(O) ≥2, 커버리지 쿼터(지칭·무관정보·필자관점 각 ≥1), killer 정확히 1(본문 문장 한 군데만 비튼 것), english 0~1(짧은 영어), △ ~1, 6유형 고루, 문장마다 최소 1개(빈 문장 없게).
- 제외: 정도·범위, 수치 스왑, 화용·양상 미세구분, 과도한 함축.

## E. 난이도·품질
- 2등급 기준(3등급 가능). '본문 대조'로 풀리게. 유치한 정반대 뒤집기 금지 → 본문 어휘 재활용 near-miss.
- 오답·설명·해석은 지문에 실제로 있는 내용·표현 기반(외부 배경지식 금지).

## 배정표 — key_grammar.point (지문마다 서로 다르게!)
각자 배정된 지문에 대해, '그 지문에 실제로 나온' 어법 중 아래 '지정 후보'를 우선 쓰되, 없으면 그 지문의 다른 뚜렷한 어법으로(단 다른 지문과 겹치지 않게). 너무 흔한 '관계사 that·단순 수동태·to부정사 부사적'만 단독으로 쓰지 말 것.
- 29 분사구문(Referred to as~) / 30 관계대명사 what / 31 병렬구조 / 32 가정법 / 33 가주어-진주어 it~to
- 34 관계부사 where / 35 동명사(주어/목적어) / 36 비교급·최상급 / 37 완료 수동태 / 38 분사 후치수식
- 39 계속적 용법 which / 40 상관접속사(not only~but also) / 41-42 the 비교급 the 비교급 / 43-45 과거완료·시제

## 출력
JSON만(주석 금지). 파일 1지문=1개 p<item>.json (예: p29.json, p41-42.json, p43-45.json).
anchor·span·source_sentence·restatement expressions·chunks 재조립은 반드시 english 원문과 '그대로' 일치해야 함(verify 자동검사).
