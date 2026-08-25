# 올림포스 '이렇게 읽으면 오답'(O/X/△) + 어법 형광펜 저작 규격

입력: /tmp/.../scratchpad/ybm<N>_data.json (배정된 것) (19지문. 각 지문 item_no·title·theme_ko·structure·sentences[id,english,grammar[{tag,note}]])
출력: /tmp/.../scratchpad/ybm/ov<N>/ox_<라벨>.json  (배정된 지문만)
형식: {"misreads": { "<item_no>||<sid>": [ 오답객체... ] }, "spans": { "<item_no>||<sid>": [ [칩1 span들], [칩2 span들], ... ] }}

## A. misreads (문장별 1~2개, 최대 2개) — O/X/△ 내용 판별
오답객체 = {statement, verdict, trap_type, anchor, why, killer?, english?, integrative?}
- verdict: "O"(참) / "X"(틀림) / "△"(결론·방향은 맞지만 근거·이유가 틀림)
- O: statement(한국어)만. trap_type/anchor/why 는 넣지 마라(빈 문자열).
- X·△: trap_type + anchor + why 필수.
- statement: 한국어 한 줄(단, english=true면 짧고 쉬운 영어 한 문장).
- trap_type ∈ [주체대상, 인과조건, 지칭, 무관정보, 필자관점, 구조수식]  (딱 이 6개 문자열)
    · 주체대상=누가 누구에게/무엇을 뒤바꿈(수동↔능동,5형식 주체)
    · 인과조건=원인↔결과·조건 뒤집기, avoid를 권장으로, 시점·순서 오독
    · 지칭=대명사·대체어(it/its/this/these/those/they/them/ones/the other)가 가리키는 대상 오인
    · 무관정보=본문에 없는 정보·과장(완전히/전혀/항상/식수로 등) 삽입
    · 필자관점=요지·필자 태도 오독, 통념·타인 견해를 필자 주장으로 착각
    · 구조수식=관계절·병렬·부정범위(not A but B) 등 수식·연결 오독
- anchor: 그 오답을 반박하는 '본문 어구'를 해당 문장 english 에서 '그대로(대소문자·구두점 포함) 복사'.
    반드시 그 문장 english 의 '연속된 부분 문자열'이어야 함(글자 하나도 다르면 안 됨). 통합추론이면 다른 문장 어구도 허용.
- why: 한국어 한 줄(15자 이상). anchor 를 근거로 '어디가 결정적으로 틀렸는지' 한 곳만 콕. 장황 금지.
- killer: 지문 전체에서 정확히 1개만 true. '본문 문장을 거의 그대로 재활용하되 딱 한 군데(주체·대상·인과·지칭 등)만 비튼' 가장 정교한 오답에.
- english: 지문당 0~1개 true. 짧고 쉬운 영어 문장(2등급도 읽을 수준).
- integrative: 지문당 0~1개(선택). 두 문장 이상 종합해야 판별되면 true, why에 '문장 N·M 종합' 명시.

## B. 지문 단위 필수 조건 (반드시 지켜라)
- 참(O) 진술 '지문당 최소 2개' (여러 문장에 흩어서).
- 커버리지 쿼터: trap_type '지칭','무관정보','필자관점' 을 지문 전체에서 각각 최소 1개.
- 한 유형만 반복 금지(6종을 고르게).
- killer 정확히 1개, english 0~1개, △ 1개 권장.
- 문장마다 최소 1개 오답(O 포함) — 비는 문장 없게. 문장당 최대 2개.

## C. spans (어법 형광펜 — 강사용) : 문장의 grammar 칩 '순서대로' 각 칩의 최소 표지 어구
- 각 칩마다 그 어법이 '실제로 나타난' english 속 '딱 그 표지 부분'만 그대로 복사(연속 부분 문자열).
- 가능한 짧게: 관계사=that/which 한 단어 · 수동태=be+p.p.(was found) · 분사수식=분사구 머리(named ~, made by ~) ·
  to부정사=to-V · 동명사=-ing · 5형식=동사+보어 표지 함께(asked ... to evaluate → "asked","to evaluate") ·
  상관구조(not A but B)=표지어 각각("not","but"). 절·문장 전체 복사 금지.
- 칩이 문장에 여러 개면 spans 리스트도 칩 순서대로 같은 개수. 못 잡는 칩은 [] (빈 리스트).
- 제외: 정도·범위(some↔all), 수치 스왑, 화용·양상 미세구분(can↔당위), 과도한 함축.

## D. 난이도 = 내신·2등급(3등급 가능)
- '본문과 대조'하면 풀리게. 개념 쪼개기·화용 미세구분 금지.
- '한눈에 정반대로 뒤집은' 유치한 오답 금지 → 본문 어휘 재활용 + 한 군데만 어긋난 near-miss.

## 주의
- anchor·span 은 반드시 english 원문에 '그대로' 존재해야 함(verify가 원문 부분문자열인지 자동 검사, 없으면 ERROR).
- JSON 만 출력(주석 금지). 배정된 item_no 만.
