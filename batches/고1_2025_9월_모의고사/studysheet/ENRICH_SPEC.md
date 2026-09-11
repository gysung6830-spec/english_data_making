# 고1 2025 어법칩 보강 스펙 (선행사·명사절 역할·주격/목적격·형광펜 정확도)

대상: `passages/<파일>.json` 의 **grammar[] 칩만** 수정. JSON 유효 유지.
절대 수정 금지: `english`, `theme`, `id`, `chunks`, `overview`, `misreads`, `vocab`.

검증기 `verify_grammar.py` 가 오류를 잡는다 — 작업 후 **반드시 ERRORS(0)** 이어야 한다.

## 1) 관계사 선행사(antecedent)
관계대명사(who/whom/whose/which/that)·전치사+관계대명사·관계부사(where/when/why/how)·생략형 관계사 칩에
`"antecedent"`: 그 관계사가 **꾸미는 선행사**를 `english`에 그대로 있는 **최소 명사구**로.
- 여러 번 나오는 단어면 관계사 바로 앞 선행사를 특정하도록 약간 길게.
- **관계대명사 what / that which(선행사 포함)** 은 antecedent 대신 아래 role.
- 계속적 용법 which/who 가 앞 '절 전체'를 받으면 antecedent 없이 두어도 됨(경고만).

## 2) 명사절 역할(role)
명사절 that·간접의문(의문사)·명사절 주어(whether)·가주어-진주어 that절·동격 that·관계대명사 what 칩에 `"role"`:
`"<동사>의 목적어절"` / `"주어절"` / `"보어절"` / `"진주어절"` / `"<명사>와 동격절"` / `"'~하는 것'(선행사 포함 명사절)"` 등.
명사절/동격 칩에는 **antecedent 를 넣지 말 것**.

## 3) 주격/목적격 라벨
관계대명사(that/which/who) 는 tag 에 격 명시: 관계사 뒤가 **동사=주격**, **새 주어=목적격**, whom=목적격.
소유격 whose·관계부사·전치사+관계대명사는 격 표기 안 함.

## 4) 형광펜 정확도(위치 유일성) — 중요
- 빈 `spans` 는 문장에 보이는 앵커로 채운다(생략형: 선행 명사 또는 that절 이끄는 동사).
- 어떤 칩의 **단일 span 이 문장에 여러 번 나오면(위치 모호)** 검증기가 오류로 막는다 →
  그 span 을 **문장에서 딱 한 번만 나오는 어구로 확장**(앞/뒤 한 단어 포함). 표지 의미는 유지.
- 한 문장에서 두 칩이 같은 단어(that 등)를 쓰면 각기 다른 유일 span 으로.

## 검증(반드시)
  cd <이 폴더>
  python3 verify_grammar.py     # ERRORS(0) 필수(경고는 허용: 계속적 which 등)
  python3 -c "import json; [json.load(open('passages/'+f)) for f in <담당파일들>]; print('JSON OK')"
