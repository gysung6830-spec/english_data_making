# 중등 기초 브릿지 학습지 (Bridge Worksheets)

**중학교 기초(단어·문법)가 안 된 고1 학생**이 혼자서도 따라올 수 있게 만든,
**하루 한 장(1일차·2일차 …)** 짜리 기초 브릿지 학습지 생성기입니다.
고1 2학기 내신 지문을 **밑바닥부터** 풀어 줍니다.

기존 `src/` 분석 도구(핵심어만 뽑는 6섹션 분석지)와 **별개**의, 초심자 전용 자료입니다.

## 한 장(하루)의 구성 — 5섹션

1. **오늘 배울 지문** — 문장 번호를 매긴 원문 (일단 소리 내어 읽기)
2. **단어 완전정복** — 핵심어만이 아니라 *모를 만한 단어 전부* (발음 한글표기·품사·뜻)
3. **오늘의 기초 문법** — 그날 지문의 **핵심 문법 1개**를 중학 수준부터. 어려운 건 "한 단계 위"로 분리
4. **끊어읽기 직독직해** — `/` 로 끊어 왼→오 순서대로 직역 (2단 표)
5. **연습문제** — 단어(영↔한)·문법 고르기·해석 + **정답·해설**

맨 위에 🎯 **오늘의 목표 문법** 배너, 맨 아래에 `ⓒ2026.김은아영어연구소.All rights reserved`.

## 생성 방법

```bash
# (최초 1회) 라이브러리·폰트가 없으면
pip install weasyprint jinja2 pypdf
sudo apt-get install -y fonts-nanum       # 한글 폰트
```

### ① 한 권짜리 '교재' (표지 + 전체요약 + 9일치) — 추천

```bash
python -m bridge.build_book        # 표지+요약+전체 → output/교재_브릿지_L1_전체.pdf
python -m bridge.build_book 1      # 표지+요약+1일차만 (샘플)
```

- 맨 앞에 **교재 표지**와 **글 전체 내용 한 페이지 요약**이 붙습니다.
- DAY 1 문법은 가장 쉬운 것(문장 뼈대→be동사→3인칭 -s)부터, 어려운 문법은 &lsquo;지금은 몰라도 OK&rsquo;로 표시.

### ② 일차별 낱장 학습지 (표지·요약 없이)

```bash
python -m bridge.build_bridge      # output/브릿지_L1_0N일차.pdf + 전체합본
python -m bridge.build_bridge 1 3  # 특정 일차만
```

(PDF는 `.gitignore` 대상이라 저장소에는 올라가지 않고, 스크립트로 언제든 다시 만듭니다.)

## Lesson 1 커리큘럼 (2022 개정 천재(강상구) 공통영어2)

| 일차 | 범위 | 오늘의 핵심 문법 |
|---|---|---|
| 1일차 | 본문 1–9 (모기가 문다) | be동사 & 일반동사 3인칭 -s |
| 2일차 | 본문 10–15 (모기가 찾는 법) | 관계대명사 that/which |
| 3일차 | 본문 16–20 (알을 낳다) | 가정법 과거 |
| 4일차 | 본문 21–28 (최악의 포식자) | 현재완료 have p.p. |
| 5일차 | 본문 29–34 (로마 제국) | 수동태 be+p.p. |
| 6일차 | 본문 35–40 (스코틀랜드) | 과거완료 had p.p. |
| 7일차 | 본문 41–45 (마무리) | 가정법 과거완료 |
| 8일차 | 무당벌레 1–6 | 최상급 the most ~ |
| 9일차 | 지렁이 7–12 | 동명사 by/at/about ~ing |

## 파일 구조

```
bridge/
  build_bridge.py     실행 진입점 (PDF 생성)
  lesson1_data.py     Lesson 1 학습지 내용(9일치 데이터)
  README.md           이 문서
templates/
  bridge_day.html.j2  일차별 학습지 디자인(HTML/CSS)
```

## 다른 지문(Lesson 2 등) 추가하기

1. `lesson1_data.py` 를 복사해 `lesson2_data.py` 를 만듭니다.
2. 각 `DAYX` 딕셔너리의 값(지문·단어·문법·직독직해·문제)을 새 지문에 맞게 채웁니다.
   - 한 딕셔너리 구조: `day_no, title, range_label, part_heading, goal_grammar, goal_sub,
     passage[], vocab[], grammar[], literal[], quiz_html, answer_html`
   - `literal` 의 영어/우리말은 `' / '` 로 끊어 주면 자동으로 `/` 표시가 붙습니다.
3. `build_bridge.py` 의 import 를 새 데이터로 바꾸거나, 인자로 데이터 모듈을 받도록 확장하면 됩니다.
