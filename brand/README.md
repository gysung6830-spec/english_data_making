# Ortica 블로그 브랜드 키트

네이버 블로그에 바로 올릴 이미지 44종과, 자료별 상세페이지 원고 초안 10편.
문구를 한 곳에서 고치고 명령 하나로 전부 다시 뽑을 수 있게 만들었습니다.

```
brand/
├─ catalog.py      자료·교재 문구와 가격 ← 고칠 곳은 대부분 여기
├─ ortica_brand.py 팔레트 · 타이포 · 각인 잎 마크
├─ build.py        레이아웃 정의 + CLI
├─ render.py       HTML → PNG (헤드리스 크로미움)
├─ fonts/          글꼴 (fetch_fonts.py 로 내려받음, 저장소에는 없음)
├─ assets/         결과 이미지 44종
├─ posts/          블로그 원고 초안 10편
├─ PRICING.md      가격 근거와 확인해야 할 것
└─ VOICE.md        "AI가 쓴 것 같다"는 말을 안 듣기 위한 문체 규칙
```

---

## 1. 톤

**먹빛 바탕 · 샴페인 골드 하이라인 · 세리프 · 넓은 여백.**

*Ortica* 는 이탈리아어로 쐐기풀입니다. 로고는 톱니가 살아 있는 쐐기풀 잎을
선으로만 그린 각인(engraving)입니다. 채워 그리면 친근해지고, 선으로 그리면
격이 올라갑니다.

| 이름 | 값 | 쓰임 |
| --- | --- | --- |
| Ink | `#0B100E` | 어두운 배경 |
| Forest | `#16261F` | 밝은 배경 위 글자 |
| Paper | `#F2EEE4` / `#FAF7EF` | 밝은 배경, 어두운 배경 위 글자 |
| Gold | `#BFA063` | 가는 선·작은 라벨에만. **면으로 칠하지 않습니다** |
| Sage / Stone | `#8B9A90` / `#6E6558` | 보조 설명 |

| 자리 | 글꼴 |
| --- | --- |
| ORTICA 워드마크, 숫자 | Playfair Display |
| 한글 제목 | 고운바탕 (명조) |
| 한글 본문·라벨 | Pretendard |

골드를 넓은 면에 칠하면 값싸 보입니다. 선과 작은 글자에만 씁니다.

## 2. 어디에 무엇을 올리나

### 네이버 블로그

| 위치 | 파일 | 크기 |
| --- | --- | --- |
| 프로필 이미지 | `profile-naver-161.png` | 161×161 |
| 프로필(고해상도) | `profile-400.png` | 400×400 |
| 블로그 타이틀 | `title-966x300-dark.png` | 966×300 |
| 블로그 타이틀(밝은) | `title-966x300-light.png` | 966×300 |
| 모바일 홈 커버 | `cover-mobile-1200x900.png` | 1200×900 |

타이틀 영역은 **가로 966px 고정**, 세로 50~600px입니다. 관리 → 꾸미기 설정 →
타이틀 → 직접등록. **'블로그 제목 표시'는 꺼 주세요.** 이미지 안에 제목이 이미
들어 있어서 켜면 글자가 겹칩니다.

모바일 커버는 기기마다 가장자리가 잘립니다. 글자는 전부 가운데 모아 뒀습니다.

### 그 밖

| 용도 | 파일 |
| --- | --- |
| 공유 미리보기(OG) | `thumb-og-1200x630-sample.png` |
| 파비콘 · 앱 아이콘 | `favicon-32/180/512.png` |
| 배경 투명 가로 로고 | `logo-horizontal-light-bg.png` / `-dark-bg.png` |

밝은 바탕에는 `light-bg`, 어두운 바탕에는 `dark-bg` 를 얹습니다.

### 상세페이지

자료 하나에 이미지 세 장 + 원고 한 편이 한 세트입니다.

```
detail-analysis-1-hero.png     표지 — 자료명과 한 줄 정의
detail-analysis-2-points.png   구성 — 무엇이 들어 있나
detail-analysis-3-spec.png     안내 — 형태·대상·가격
posts/02-analysis.md           본문 원고 초안
```

자료 6종(`one-line` `analysis` `workbook` `variation` `mock` `pilsaengbo`)과
교재 3종(`highlighter` `syntax` `voca`), 그리고 라인업 2장 + 가격표 1장.

원고를 그대로 올리지 마세요. `posts/*.md` 안에 **직접 채울 곳**을 주석으로
표시해 뒀습니다. 그 자리를 비우면 아무리 문장을 고쳐도 AI 티가 남습니다.
자세한 건 [VOICE.md](VOICE.md).

## 3. 고치고 다시 뽑기

```bash
pip install pillow                    # 최초 1회
python brand/fonts/fetch_fonts.py     # 최초 1회 (글꼴 내려받기)
python brand/build.py all             # 이미지 + 원고 전부 다시
```

| 고칠 것 | 고칠 파일 |
| --- | --- |
| 자료 이름·설명·구성·대상·가격 | `catalog.py` |
| 브랜드명·태그라인 | `build.py` 위쪽 `BRAND_KO`, `TAGLINE` |
| 색 | `ortica_brand.py` 의 `PALETTE` |
| 잎 모양(톱니 개수·깊이·잎 비율) | `ortica_brand.py` 의 `leaf_path`, `leaf_engraved` |

자료 하나만 다시 뽑을 때:

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
`<br>` 로 직접 끊는 편이 보기 좋습니다. 줄 수와 가장 긴 줄 길이를 보고 글자
크기가 자동으로 줄어듭니다.

## 4. 다른 PC 에서

렌더링은 헤드리스 크로미움을 그대로 부릅니다. 크롬을 못 찾으면 경로를 알려
주세요.

```bash
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  python brand/build.py all
```

글꼴은 `brand/fonts/` 안에서만 쓰고 시스템에는 설치하지 않습니다
(fontconfig 를 렌더링할 때만 끼워 넣습니다). 윈도우에서는 fontconfig 가 없어서
글꼴 세 개를 직접 설치해야 할 수 있습니다.
