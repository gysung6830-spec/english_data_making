# 영어 지문 → 3형식 PDF 생성기

영어 지문 파일(PDF·이미지·txt)을 넣으면 **한 지문당 최대 3가지 형식**의 학습용
PDF를 자동 생성합니다. 복수 지문은 각 형식 PDF 안에 **지문 단위로 페이지가
분리되어** 순서대로 배치됩니다.

> 이 폴더(`passage3/`)는 저장소의 기존 "지문 분석 도구"와 **별개**의 독립
> 프로그램입니다. 서로 영향을 주지 않습니다.

## 3가지 출력 형식

| 키 | 형식명 | 파일명 접미사 | 내용 |
|----|--------|--------------|------|
| a | 한줄해석 | `(지문명)_한줄해석.pdf` | 영어 문장 + 바로 아래 회색박스 한글해석 |
| c | 한줄영어 | `(지문명)_한줄영어.pdf` | 영어 문장만 (해석 없음) |
| b | 좌지문 우해석 | `(지문명)_좌지문우해석.pdf` | 좌 영어 / 우 한글 2단 표 |

## 설치

```bash
pip install -r requirements.txt
playwright install chromium
# (선택) 한글 Tesseract 폴백: apt install tesseract-ocr-kor poppler-utils
# (선택) 자동 번역 / 비전 OCR:  export ANTHROPIC_API_KEY=sk-...
```

## 웹앱 (권장)

```bash
python webapp.py        # http://localhost:5000
```
브라우저에서 파일 업로드 → 형식 체크 → 파일명 입력 → 다운로드.
형식을 여러 개 고르면 `(지문명)_PDF.zip`, 하나면 PDF 그대로 받습니다.

## CLI

```bash
python main.py 입력.pdf  --out ./output --theme modern --header "OO학원"
python main.py 사진.jpg  --out ./output --formats ac        # 한줄해석+한줄영어
python main.py 입력.txt  --out ./output --no-translate      # 번역 끄기
python main.py 입력.pdf  --name "2026년 5월 모의고사"        # 출력 파일명 지정
```
`--formats` 키: `a`=한줄해석, `c`=한줄영어, `b`=좌지문우해석 (기본 `abc`).

## 입력 형식 규칙

- **지문 구분** = 문제 번호 헤더 한 줄
  예) `[고3] 2026년 5월 - 26번: 프랑스 군대에 자원하여 … Alan Seeger의 생애`
- **문장 구분** = 원문자 `①②③…⑳`
- **영어/한글 분리** = 줄 단위(한글 2자 이상 → 해석). 해석 없는 문장은
  `ANTHROPIC_API_KEY` 가 있으면 자동 번역, 없으면 빈 칸으로 진행.

## 모듈 구조

| 파일 | 역할 |
|------|------|
| `parser.py` | 텍스트 → 지문/문장 파싱 (`Passage`, `Sentence`) |
| `ocr.py` | 스캔 PDF·사진 → 텍스트 (Claude 비전 우선, Tesseract 폴백) |
| `translator.py` | 해석 없는 문장만 Claude API로 번역(선택) |
| `themes.py` | 디자인 테마 3종 CSS (기본 modern) + 페이지 규칙·auto-fit |
| `renderer.py` | 3형식 HTML 렌더링 (지문마다 `id="passage-N"`) |
| `main.py` | CLI + 입력 라우팅 + auto-fit PDF 빌더(`html_to_pdf`) |
| `webapp.py` | Flask 웹앱 |

## 페이지 배치 / auto-fit

- 한 지문 = 한 페이지 원칙. 별개 지문은 항상 새 페이지에서 시작.
- 한 페이지를 살짝 넘는 지문은 간격·글자크기를 단계적으로 축소
  (`compact` → `compact2`)해 1페이지에 맞춥니다.
- 그래도 안 되는 아주 긴 지문은 축소를 풀고 2페이지 이상으로 흐르며,
  문장(표의 행)이 페이지 경계에서 잘리지 않습니다.

auto-fit은 헤드리스 Chromium의 실측(`getBoundingClientRect`)에 의존합니다.

### 미리 설치된 Chromium 사용(컨테이너 등)

`playwright install` 로 브라우저를 받을 수 없는 환경에서는 실행 파일 경로를
환경변수로 지정할 수 있습니다.

```bash
export PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium-XXXX/chrome-linux/chrome
```

## 테스트

```bash
python tests/test_parser_render.py      # 파서·렌더러·테마 (무거운 의존성 불필요)
```

## 알려진 제약

- HWP 입력 미지원(PDF·이미지·txt만).
- 페이지 규칙·auto-fit CSS는 세 테마 모두에 포함(기본은 modern).
- 파서 헤더 형식은 `…N번: 제목` 고정. 다른 형식은 `parser.HEADER_RE` 확장 필요.
- 개발 서버(`app.run`)는 데모용. 실서비스는 gunicorn 등 WSGI 권장.
