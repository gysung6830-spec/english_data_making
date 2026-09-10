# 고1 필생보 어법칩 보강 스펙 (관계사 선행사·명사절 역할·주격/목적격·빈 spans)

대상: `passages/<파일>.json`. **grammar[] 칩만** 수정. JSON 유효 유지.
절대 수정 금지: `english`, `translation`, `id`, `chunks`, `overview`, `misreads`, `vocab`.

## 1) 빈 spans 채우기 (형광펜 누락 방지)
spans 가 `[]` 인 생략 칩에 문장 `english` 에 **그대로 보이는 앵커**를 span 으로:
- 목적격 관계대명사 생략: 선행 명사(선행사)를 span. 예 `the story` 뒤 관대 생략 → `["story"]` 또는 선행사구.
- 명사절/접속사 that 생략: that절을 이끄는 **동사**를 span. 예 `believe (that)` → `["believe"]`, `feel (that)`→`["feel"]`.
span 문자열은 `english` 에 단어경계로 실재해야 함.

## 2) 관계사 선행사(antecedent) 추가
관계대명사(who/whom/whose/which/that)·전치사+관계대명사·관계부사(where/when/why/how)·생략형 관계사 칩에
`"antecedent"`: 그 관계사가 **꾸미는 선행사**를 `english` 에 그대로 있는 **최소 명사구**로.
- 여러 번 나오는 단어면 관계사 바로 앞 그 선행사를 특정할 수 있게 살짝 긴 구로(예 `the water`, `a small dot`).
- **관계대명사 what / 선행사 포함 what** 은 antecedent 넣지 말고 아래 role 로.

## 3) 명사절 역할(role) 추가
명사절 that·간접의문(의문사)·동격 that·명사절 생략 칩에 `"role"`:
- `"<동사>의 목적어절"`, `"주어절"`, `"보어절"`, `"<명사>와 동격절"` 등.
- 관계대명사 what 도 `"role":"'~하는 것'(선행사 포함 명사절)"`(+가능하면 주어절/목적어절).
- 명사절/동격 칩에는 **antecedent 를 넣지 말 것**(넣으면 관계사와 혼동 오류).

## 4) 주격/목적격 정확 라벨 (핵심)
관계대명사(that/which/who) 칩의 `tag` 를 격까지 명시:
- **주격 관계대명사 <word>** — 관계사가 절의 주어(관계사 바로 뒤에 동사). 예 "the one **that makes**".
- **목적격 관계대명사 <word>** — 관계사가 목적어(관계사 뒤에 새 주어 S+V). 예 "something **that you** want". whom 은 항상 목적격.
- 소유격 whose / 관계부사 where·when·why·how / 전치사+관계대명사 → 주격·목적격 표기하지 말 것.
- 관계사 뒤가 **동사**면 주격, **새 주어(명사/대명사)**면 목적격. 절을 직접 읽고 판단.

## 검증 (반드시 통과)
  cd <이 폴더>
  python3 verify_grammar.py     # ERRORS(0) 이어야 함(경고는 허용)
  python3 -c "import json; [json.load(open('passages/'+f)) for f in json.load(open('order.json'))]; print('JSON OK')"
verify_grammar 가 잡는 오류: span/선행사 문장에 없음, 명사절에 선행사 있음, 주격/목적격 모순(뒤가 조동사/대명사인 경우), 주격 생략(불가) 등.
