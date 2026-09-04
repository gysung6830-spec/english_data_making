# 필생보 콘텐츠 리워크 규격 (올림포스 10-14강 + 고1 2026 적용)

기존 지문 JSON(p<item>.json)을 **부분 수정**한다. 새로 저작하지 말고, 아래 5가지만 바꾼다.
그대로 두는 것: `english`(원문), `misreads`(O/X/△·anchor·why·verdict 전부), `mistips`,
`overview`의 서술 필드(theme_ko·topic·stance·structure·restatement_chains·flow_blocks),
`grammar` 어법칩(tag·note·spans). ★위 항목은 **글자 하나도 바꾸지 말 것**.

## ① chunks 를 잘게(직독직해)  — ★가장 중요
- 조각당 **2~5단어**(구 단위). 기존보다 잘게 쪼갠다. 문장당 조각 수는 늘어나도 됨.
- en 을 순서대로 이으면(빈칸 [[ ]] 제거 후) 문장 `english` 와 **글자까지 정확히 동일**(구두점·따옴표 포함).
  첫 조각에 주어·(가능하면)동사 포함.
- **ko = 직독직해**: 영어 어순 그대로 끊어 옮긴다(자연스러운 의역 금지). 조사·연결은 최소.
  예) "the level of interactivity" → "그 수준을 / 상호작용성의" 식으로 어순대로.
- 빈칸 규칙(변경 없음): 통째 빈칸 = 오역 위험 큰 3단어↑ 조각 전체를 en·ko 모두 [[ ]](문장당 최대 2).
  단어 빈칸 = 핵심어 1개만 ko 에서 [[핵심어]](+조사는 밖). en·ko 의 [[ ]] 유무 짝 맞춤.
- ★빈칸 밀도: **문장당 대략 3~5개**(통째 0~2 + 단어빈칸 나머지 핵심). 모든 미세조각에 다 뚫지 말 것 —
  해석을 틀리기 쉬운 핵심어 위주로만. 말줄임표 금지.

## ② translation 필드 추가(문장마다)  — ③ 영어 한줄해석용
- 각 sentence 에 `"translation": "<자연스러운 한글 문장 번역>"` 추가.
- **자연스러운 한국어 완역**(직독직해 아님). 단, **과한 의역 금지** — 원문 정보를 빼거나 더하지 말 것.
- 빈칸([[ ]]) 없이 완성된 한 문장. chunks.ko(직독직해)와는 다른, 매끄러운 번역.

## ③ vocab 큐레이션(문장마다 0~4개)
- **초·중학 기초어 삭제**: 예) game, learn, use, need, help, make, important, goal, people, thing,
  work, find, give, show, part, way, many, much 등 누구나 아는 단어는 넣지 않는다.
- **남길 것**: 고1 이상 수준 어휘 + 숙어·구동사·고정표현(idiom/phrasal/collocation).
  예) instructional, interactivity, engagement, parameters, achievement, outcomes,
  "rather than", "make sure", "what we call".
- 문장에 실제 있는 표현만. 없으면 그 문장 vocab=[] 가능. word=표현 그대로, meaning=간결한 뜻.

## ④ key_grammar 재선정(point·source_sentence)
- point 는 **이 지문에서 서술형이 예상되는 문장** 기준으로 고른다:
  구조가 복잡하거나(도치·삽입·중첩수식·병렬·관계절 등) **영작이 어려운** 문장의 핵심 문법.
- source_sentence = 그 문장 원문 **그대로(verbatim)**. explanation 3~6개(chip+text) 그 문법 설명.
- example_analysis = 그 문장에서 무엇이 도치/생략/수식/병렬됐는지 한 줄.

## ⑤ drills = 지문 문장만(정확히 5개)
어법판단 3(밑줄형·네모형·오류찾기 각 1) + 영작 2.
- 어법판단 3형식: **이 지문에 실제 나온 문장만** 사용(새 예문 금지). 원문 verbatim, 틀린 보기는 한 곳만 최소 변형.
  - 밑줄형: [[번호|텍스트]] 정확히 5곳, 딱 1곳만 틀리게. answer="틀린 번호"(예 "④"), options=["① …",…5개], fix.
  - 네모형: [[옳은것/틀린것]] 2~3곳(옳은 것=지문 원문 단어 반드시 앞). answer="옳은것 / 옳은것 / …", options=[], words=[].
  - 오류찾기: options=지문 문장 5개(원문), 딱 1개만 최소 변형. answer=틀린 문장 그대로(변형본), fix. 틀린 위치 분산.
- ★영작 2개 **모두 `from_passage=true`** — 둘 다 **④에서 고른 핵심문법이 쓰인 지문 문장**을 복원하는 문제.
  (하나는 source_sentence, 다른 하나는 같은 핵심문법이 쓰인 이 지문의 다른 문장. 그런 문장이 없으면
   source_sentence 를 두 가지 제시어 구성으로.) **지어낸 문장(from_passage=false) 절대 금지.**
  question=한국어 뜻, answer=영어 원문 그대로, words=정답 단어 전부(단어단위·고정표현 묶음 OK), options=[].

## 출력
- 같은 파일 경로에 **완전한 JSON 하나**로 덮어쓴다(주석 금지). 위 '그대로 두는 것' 항목은 원본과 동일해야 함.
- 검증: chunks 재조립=english, source_sentence·drill sentence·anchor·span·restatement expressions 는 지문 원문과 그대로 일치.
