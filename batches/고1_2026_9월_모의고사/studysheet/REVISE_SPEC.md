# 최고난도문장 해석법 — 개정3 (형광펜/구어체 강화)

각 담당 item 에 대해 **두 파일**을 손본다.

기존 파일 위치:
- 문장 분석:  hard2/<item>.json  (기존 필드: mistrans{span,note}, parallel, prep_rel)
- 지문 설명:  explain/<item>.json (기존 필드: talk[])
대상 문장: hard/<item>.json 의 sentence_id → passage(../passages/p<item>.json).sentences 에서 찾음.
문장 영어 원문 = 그 sentence 의 "english".

---
## A) explain/<item>.json — talk 에 핵심어 형광펜 마킹 (모든 item)
- talk 의 각 문단에서 **문장별 핵심단어(제일 중요한 개념어) 위주로** `[[ ... ]]` 로 감싼다.
  렌더러가 `[[...]]` 를 형광펜으로 칠한다.
- 핵심어에는 **지문에 실제 나온 영어 단어를 괄호로 병기**한다. 괄호까지 형광펜 안에 넣는다.
  예:  `[[학습 게임(learning game)]]`, `[[상호작용성(interactivity)]]`
- 남발 금지: 한 문단에 1~3개 정도(진짜 핵심어만). 조사/서술어는 감싸지 말 것.
- 병기하는 영어는 **그 지문에 등장한 단어/표현**이어야 함(지어내지 말 것). 적절한 영어가
  없으면 한글만 `[[ ]]` 로 감싼다.
- 말투(구어체 존댓말)·순서·정확성은 기존 그대로 유지. 내용은 바꾸지 말고 마킹만 추가.

## B) hard2/<item>.json — 형광펜 span & 쉬운 설명 (해당되는 item만)
아래 필드를 **추가/수정**한다. 기존 mistrans 는 그대로 둔다.

1. **parallel 이 non-null 인 item**: `parallel_spans` 추가.
   - 병렬되는 **동사(구)들의 영어 조각 목록**(2개 이상). 각 조각은 문장 english 에 그대로 있고,
     문장에서 **유일하게** 잡혀야 함(안 그러면 앞뒤 단어 포함해 유일하게).
   - 이 조각들이 '같은 색' 형광펜으로 칠해져 병렬임을 보여줌.  예(20): ["are not creating","are creating"].
   - parallel(한글 설명)은 유지하되, 필요하면 조금 더 쉽게 다듬어도 됨.

2. **prep_rel 이 non-null 인 item**: `prep_rel` 을 **쉬운 '바꿔 읽기' 방식**으로 다시 쓰고,
   `prep_rel_spans` 추가.
   - prep_rel(쉬운 설명): "전치사+관계대명사"를 겁먹지 않게. 공식처럼:
     "in which = in + which(=선행사). which 를 선행사로 바꿔서 'in 선행사', 즉 '그 ~ 안에서'로
     읽으면 돼요" 식으로, **구체 예시로** 풀어 쓴다. 선행사가 무엇인지 꼭 밝힌다. 1~2문장.
   - `prep_rel_spans`: [전치사+관계대명사 표현, 선행사] 두 개. 각각 문장 english 에 그대로 있고
     문장에서 유일하게 잡혀야 함.  예(20): ["in which","a learning game"].

3. parallel/prep_rel 이 null 인 item 은 B 에서 손댈 것 없음(그대로).

---
## 자기검증(제출 전, python 으로 직접 확인)
- explain: JSON 유효, `[[`/`]]` 짝이 맞음, 병기 영어가 지문에 실재.
- hard2: parallel_spans·prep_rel_spans 의 **모든 조각이 문장 english 에 부분문자열로 정확히 1회** 등장.
  (0회거나 2회 이상이면 앞뒤 단어를 붙여 유일하게 고칠 것.)
- 모두 UTF-8(ensure_ascii=False).
