# 관계사 선행사 · 명사절 접속사 표시 데이터 스펙

대상: `passages/<파일>.json`. **어법칩(grammar[])에만** 필드를 추가/보완한다.
절대 수정 금지: `english`, `translation`, `id`, `chunks`, `overview`, `misreads`, `vocab`.
JSON 유효 유지. 기존 `tag`/`note`/`spans` 는 되도록 보존(정확하면 그대로).

목표(강사 요청): **각 관계사가 무엇을 꾸미는지(선행사)** 를 다 표시하고, **명사절 접속사인 것도 모두** 표시.

## 1) 관계사 칩에 `antecedent` 추가
관계대명사(주격/목적격/소유격 who/whom/whose/which/that), 관계부사(where/when/why/how),
전치사+관계대명사(in which, to which, at which …), 관계사 생략·목적격 관계대명사 생략 칩에:
- `"antecedent"`: 그 관계사가 **꾸미는 선행사** 를 **english 에 그대로 있는 최소 명사구**로. 예: `"forest gardening"`, `"the story"`, `"the reason"`, `"situations"`.
  - 여러 번 나오는 단어면 **관계사 바로 앞의 그 선행사**를 특정할 수 있도록 살짝 긴 구(예: `"the water"`, `"a small dot"`)로.
  - 생략 칩은 선행사(head noun)를 그대로 antecedent 로(그 명사가 spans 이기도 함).
- `spans` 는 **관계사 표지 단어**가 들어가야 함(that/which/who/where/in which…). 생략형은 선행사 단어를 span 으로(현행 유지).
- **관계대명사 what / what 관계대명사(선행사 포함)** 는 antecedent 를 넣지 말고 아래 `role` 로: `"role":"'~하는 것'(선행사 포함 명사절)"` (+가능하면 `주어절/목적어절` 명시).

## 2) 명사절 접속사 칩에 `role` 추가 + 누락분 모두 추가
명사절을 이끄는 접속사(that, whether, if[명사절], 의문사 what/how/why/who/where/when + 간접의문)를 **모두** 칩으로:
- `tag`: 예 `"명사절 접속사 that"`, `"명사절 whether"`, `"간접의문 how"`.
- `spans`: 그 접속사 단어(that/whether/how…). 생략된 that 은 that절을 이끄는 **동사**를 span(현행 유지).
- `"role"`: 그 명사절의 문장 내 기능 — `"<동사>의 목적어절"`, `"주어절"`, `"보어절"`, `"<명사>와 동격절"`(동격 that). 예: `"believe의 목적어절"`, `"주어절"`.
- 기존 `명사절 that` / `that절 나열` / `명사절 생략` / `동격 that` 칩에도 `role` 채우기.

## 3) 완결성(누락 스캔)
각 문장 english 를 훑어 **관계사·명사절 접속사인데 칩이 없는 것**을 찾아 칩 추가(1)·(2) 형식으로.
단, 진짜 관계사/명사절만. `조건 if`(부사절), 일반 접속사(when 시간, because 등)는 명사절 아님 → 건드리지 말 것.

## 검증
- `python3 -c "import json;json.load(open('passages/<파일>.json'))"` 통과.
- 추가한 `antecedent`/`role` 의 antecedent 문자열은 반드시 english 안에 그대로 존재.
- 관계사 칩엔 antecedent(또는 what은 role), 명사절 칩엔 role 이 있어야 함.
