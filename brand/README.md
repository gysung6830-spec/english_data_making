# Ortica 블로그 브랜드 키트

네이버 블로그에 바로 올릴 이미지 43종과, 자료별 상세페이지 원고 초안 10편.
라인업·상세페이지에 들어가는 자료 예시는 **이 저장소의 생성기가 실제로 뽑은
출력물**입니다. 그림으로 흉내 낸 게 아닙니다.

```
brand/
├─ catalog.py       자료·교재 문구, 가격, 예시 이미지 연결 ← 고칠 곳은 대부분 여기
├─ ortica_brand.py  팔레트 · 잎 마크
├─ build.py         레이아웃 정의 + CLI
├─ sample_shots.py  저장소 생성기로 실제 자료 예시 이미지 뽑기
├─ render.py        HTML → PNG (헤드리스 크로미움)
├─ assets/          결과 이미지 (samples/ 는 실제 산출물, thumbs/ 는 목록용 썸네일)
├─ posts/           블로그 원고 초안 10편
├─ PRICING.md       가격 근거와 확인해야 할 것
└─ VOICE.md         "AI가 쓴 것 같다"는 말을 안 듣기 위한 문체 규칙
```

---

## 1. 브랜드

| 문구 | 값 |
| --- | --- |
| 이름 | Ortica · 오르티카 영어 |
| 콘셉트 | 필자의 생각이 보이는 영어 |
| 소개 | 고등 모의고사 · 내신 · 수능자료 제작 (글줄 없이 칩으로만) |

*Ortica* 는 이탈리아어로 쐐기풀입니다. 로고는 톱니가 살아 있는 잎 한 장.

| 이름 | 값 | 쓰임 |
| --- | --- | --- |
| Green 900 | `#10382C` | 어두운 배경 |
| Green 700 | `#1B5A46` | 밝은 배경 위 글자 |
| Leaf | `#8ACB5E` | 잎 · 강조 |
| Cream / Paper | `#F5F0E2` / `#FFFDF7` | 밝은 배경 |
| Gold | `#DCA945` | 아주 짧은 강조만 |
| Muted | `#7E9086` | 보조 설명 |

글꼴은 저장소에 이미 있는 **나눔스퀘어라운드**(`templates/fonts/`). 분석지 PDF와
같은 글꼴이라 블로그와 자료의 인상이 이어집니다.

## 2. 어디에 무엇을 올리나

### 네이버 블로그

**프로필** — 네이버에는 **`profile-mark-800.png`** 를 올리세요.

| 파일 | 크기 | 쓰는 곳 |
| --- | --- | --- |
| `profile-mark-800.png` | 800×800 | **네이버 권장.** 심볼만 |
| `profile-mark-400.png` | 400×400 | 같은 판, 작은 용량 |
| `profile-mark-light-800.png` | 800×800 | 밝은 배경, 심볼만 |
| `profile-light-1200.png` | 1200×1200 | 크림 바탕 + Ortica + 오르티카 영어 |
| `profile-light-800.png` | 800×800 | 위와 같음 |
| `profile-light-400.png` | 400×400 | 위와 같음 |
| `profile-name-800.png` | 800×800 | 크게 보이는 자리용(이름 포함) |
| `profile-name-400.png` | 400×400 | 위와 같음 |
| `profile-portrait-400x480.png` | 400×480 | 사이드바가 세로로 긴 스킨 |

**왜 심볼만인가.** 네이버 앱은 프로필을 지름 60px 남짓한 원으로 줄입니다.
그 크기에서 'Ortica 영어 / 오르티카 영어' 두 줄은 반드시 뭉개집니다. 글자를
빼고 잎을 키우면 44px 까지 줄어도 형태가 남습니다.

**올릴 때는 800px 판을 올리세요.** 161px 짜리를 올리면 네이버가 그걸 다시
늘렸다 줄이면서 더 흐려집니다. 큰 원본을 주고 축소를 네이버에 맡기는 편이
선명합니다.

**웹(PC)용 블로그 타이틀** — 가로 **966px 고정**, 세로 50~600px

| 파일 | 크기 | 성격 |
| --- | --- | --- |
| `title-966x550-dark.png` | 966×550 | 배너형. 브랜드가 먼저 읽힌다 |
| `title-966x550-light.png` | 966×550 | 배너형(밝은 배경) |
| `title-966x420-dark.png` | 966×420 | 배너형(조금 낮게) |
| `title-966x300-dark.png` | 966×300 | 가로형. 글 목록이 위로 올라온다 |
| `title-966x300-light.png` | 966×300 | 가로형(밝은 배경) |
| `title-966x200-dark.png` | 966×200 | 슬림 |

배너형(550)은 벤치마킹하는 블로그와 비슷한 비율입니다. 타이틀을 크게 쓰면
브랜드가 먼저 읽히고, 낮게 쓰면 글 목록이 위로 올라옵니다. 소개 칩은 콘셉트
아래에 놓입니다.

관리 → 꾸미기 설정 → 타이틀 → 직접등록. **'블로그 제목 표시'는 꺼 주세요.**
이미지 안에 제목이 이미 들어 있어서 켜면 글자가 겹칩니다.

**모바일 홈 커버** — 블로그앱 → 홈편집 → 커버 이미지

| 파일 | 크기 |
| --- | --- |
| `cover-backdrop-1600x1200.png` | 1600×1200 (기본) |
| `cover-backdrop-2400x1350.png` | 2400×1350 (가로가 넓은 기기) |
| `cover-backdrop-1080x1080.png` | 1080×1080 (정사각) |

**여기엔 글자가 없습니다. 일부러 뺐습니다.** 네이버가 이 이미지 **위에**
블로그 제목·프로필·이웃수·홈편집 버튼을 직접 그립니다. 이미지에 브랜드명을
넣으면 그 위에 네이버가 또 제목을 얹어서 글자가 겹칩니다.

기기마다 잘리는 자리도 다릅니다(아이패드는 가운데 가로 띠만 보입니다). 그래서
한 곳에 그림을 몰지 않고 잎을 흩어 놓았고, 아래쪽은 흰 글자가 얹히는 자리라
한 겹 어둡게 눌러 뒀습니다.

블로그 제목은 이미지가 아니라 **블로그 설정의 '블로그명'** 에 넣으세요.
지금 설정하신 "필자의 생각이 보이는 영어: Ortica 영어" 처럼요.

글자가 들어간 판(`cover-branded-1200x900.png`)은 위에 아무것도 안 얹히는
자리 — 공유 이미지나 배너 — 에만 쓰세요.

### 그 밖

| 용도 | 파일 |
| --- | --- |
| 공유 미리보기(OG) | `thumb-og-1200x630-sample.png` |
| 파비콘 · 앱 아이콘 | `favicon-32/180/512.png` |
| 가로 로고(배경 있음) | `logo-horizontal-solid-light.png` / `-solid-dark.png` |
| 가로 로고(배경 투명) | `logo-horizontal-on-light.png` / `-on-dark.png` |

**투명 PNG 주의.** `-on-light` / `-on-dark` 는 배경이 없는 판이라 다른 이미지
위에 얹을 때만 씁니다. 그냥 올리면 보는 쪽 배경색에 따라 글자가 안 보입니다
(`-on-dark` 는 밝은 글자라 흰 배경에서 안 보이고, `-on-light` 는 그 반대).
어디에 올릴지 모르겠으면 **`-solid-` 쪽을 쓰세요.**

## 3. 라인업과 상세페이지

```
lineup-materials-1.png         자료 01-03 — 실제 출력물 썸네일 + 특징 + 차별화 포인트
lineup-materials-2.png         자료 04-06
lineup-books.png               고3 교재 3종
detail-analysis-1-hero.png     표지 — 자료명과 한 줄 정의
detail-analysis-2-points.png   구성 + 실제 자료 예시 전체 이미지
detail-analysis-3-spec.png     안내 — 형태·대상 (가격을 넣으면 함께 표시)
posts/02-analysis.md           본문 원고 초안
```

### 실제 자료 예시

`python brand/sample_shots.py` 가 `src/render.py` 의 렌더 함수를 그대로 불러
실제 산출물 화면을 찍습니다. WeasyPrint 자리에 HTML 을 가로채는 껍데기를 끼워
넣는 방식이라, 실제 PDF 와 내용이 같습니다.

| 자료 | 예시 파일 |
| --- | --- |
| 한줄해석 | `samples/one-line.png` |
| 워크북 | `samples/vocabtest.png` |
| 평가원 VOCA | `samples/vocablist.png` |

**지문분석지**는 포인트박스 버전으로 최종 결정되어, 이 저장소의 6섹션
템플릿으로 뽑은 예시는 쓰지 않습니다. **변형문제 6종 · 동형모의고사 · 필생보 ·
형광펜 독해 · 구문독해**는 생성기가 없습니다. 모두 예시 자리를 비워 뒀습니다
(목록에 '예시 준비 중'으로 표시).
실물 화면 캡처를 `brand/assets/samples/` 에 넣고 `catalog.py` 의 해당 항목에
`sample="파일명"` 을 적으면 라인업과 상세페이지에 자동으로 들어갑니다.

### 라인업을 셋씩 나눈 이유

여섯 개를 한 장에 늘어놓으면 목록으로만 읽힙니다. 셋씩 끊으면 흐름이 생깁니다.

- **01–03 지문 한 장을 세 번 만납니다** — 읽고 · 분석하고 · 훈련한다
- **04–06 그 다음은 시험장입니다** — 문제로 · 실전으로 · 수업과 자습으로

각 묶음 아래에는 **'이 세 가지가 다른 점'** 카드 세 장이 붙습니다. 자료 설명이
아니라 "왜 다른 곳 자료가 아니라 이걸 쓰는가"에 대한 답만 적습니다. 문구는
`build.py` 위쪽의 `EDGE_READ`, `EDGE_EXAM`, `EDGE_BOOK` 에서 고칩니다.

### 전부 한눈에 보기

```bash
python brand/build.py index      # brand/assets/_index.png
```

결과물을 파일명·크기와 함께 한 장에 늘어놓습니다. 투명 PNG 는 흰 바탕 위에
얹혀 보이므로, 여기서 비어 보이는 파일이 곧 "배경이 투명한 파일"입니다.

## 4. 고치고 다시 뽑기

```bash
pip install pillow pydantic jinja2 pyyaml   # 최초 1회
python brand/sample_shots.py                # 실제 자료 예시
python brand/build.py all                   # 이미지 + 원고 전부
```

| 고칠 것 | 고칠 파일 |
| --- | --- |
| 자료 이름·설명·구성·대상·가격·예시 연결 | `catalog.py` |
| 브랜드명·콘셉트·소개 칩 | `build.py` 위쪽 `BRAND_KO`, `CONCEPT`, `KEYWORDS` |
| 색 | `ortica_brand.py` 의 `PALETTE` |
| 잎 모양(톱니 개수·깊이·비율) | `ortica_brand.py` 의 `leaf_path`, `logomark_svg` |

자료 하나만:

```bash
python brand/build.py item analysis
python brand/build.py posts          # 원고 초안만
```

포스트 썸네일:

```bash
python brand/build.py thumb \
  --title "빈칸추론이 안 풀리는<br>진짜 이유 세 가지" \
  --sub "지문 구조부터 다시 보는 독해법" \
  --tag "수능 독해" --number "No.01" \
  --out brand/assets/post-001.png
```

`--size 1200x630` 으로 공유용을, `--light` 로 밝은 배경을 뽑습니다. 제목은
`<br>` 로 직접 끊는 편이 보기 좋습니다.

## 5. 다른 PC 에서

렌더링은 헤드리스 크로미움을 그대로 부릅니다. 크롬을 못 찾으면 경로를 알려
주세요.

```bash
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  python brand/build.py all
```
