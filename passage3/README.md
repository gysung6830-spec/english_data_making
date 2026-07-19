# 영어 지문 → 3형식 PDF 생성기

영어 지문(PDF·이미지·txt)을 넣으면 **한 지문당 최대 3형식**의 PDF를 만듭니다.
CLI와 **웹앱** 두 가지로 쓸 수 있습니다.

> 이 폴더(`passage3/`)는 저장소의 기존 "지문 분석 도구"와 **별개**의 독립
> 프로그램입니다. 서로 영향을 주지 않습니다. 아래 명령은 이 폴더 안에서
> 실행하세요 (`cd passage3`).

## 3가지 형식
| 형식 | 파일명 접미사 | 설명 |
|------|--------------|------|
| 한줄해석 | (지문명)_한줄해석.pdf | 영어 문장 + 회색박스 한글해석 |
| 한줄영어 | (지문명)_한줄영어.pdf | 영어 문장만 (해석 없음) |
| 좌지문 우해석 | (지문명)_좌지문우해석.pdf | 좌 영어 / 우 한글 2단 표 |

## 웹앱 (권장)
    pip install flask pdfplumber playwright anthropic pytesseract pdf2image pillow
    playwright install chromium
    cd passage3
    python webapp.py
    # 브라우저에서 http://localhost:5000

웹앱 화면에서:
1. 지문 파일 업로드 — PDF·이미지·txt (스캔/사진은 자동 OCR)
2. PDF 파일명(지문명) 입력 — 예: Alan Seeger → 아래에 최종 파일명 실시간 표시
3. 출력 형식 체크박스 — 한줄해석 / 한줄영어 / 좌지문우해석 중 원하는 만큼 선택
4. 상단 머리글(선택) — 학원명·자료명 등
5. 생성 & 다운로드 — 형식 1개면 PDF, 여러 개면 zip으로 묶어 다운로드

## CLI
    cd passage3
    python main.py 입력.pdf --out ./output --theme modern --header "OO학원"
    python main.py 사진.jpg --out ./output --formats ac
`--formats` 키: a=한줄해석, c=한줄영어, b=좌지문우해석

## 페이지 배치 규칙 (모던 테마, 3형식 공통)
- 한 지문 = 한 페이지: 들어가면 그 페이지에 담김
- 긴 지문 자동 맞춤: 살짝 넘치면 간격 자동 축소(auto-fit)로 1페이지에 맞춤
- 아주 긴 지문: 압축으로도 안 되면 2페이지+로 흐르되 문장/표 행이 경계에서 안 잘림
- 별개 지문은 항상 새 페이지에서 시작

auto-fit 강도는 main.py의 CALIB(기본 0.90)으로 조절.

### 미리 설치된 Chromium 사용(컨테이너 등)
`playwright install` 로 브라우저를 받을 수 없는 환경에서는 실행 파일 경로를
환경변수로 지정할 수 있습니다.

    export PLAYWRIGHT_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium-XXXX/chrome-linux/chrome

## 입력 처리 (OCR 자동)
- 디지털 PDF → pdfplumber 텍스트 추출
- 스캔 PDF / 사진 → OCR: ANTHROPIC_API_KEY 있으면 Claude 비전(권장), 없으면 Tesseract(kor 언어팩 필요)
- txt → 그대로

## 해석 처리
- PDF에 해석 있으면 그대로 사용
- 없는 문장만 ANTHROPIC_API_KEY 있을 때 Claude API 번역 (없으면 해석칸 비움)

## 파일 구성
- webapp.py  Flask 웹앱 (업로드·체크박스·파일명·다운로드)
- main.py    CLI 파이프라인 + auto-fit PDF 빌더
- parser.py  지문/문장 파싱
- ocr.py     스캔·사진 OCR
- translator.py  해석 번역(선택)
- themes.py  디자인 테마 (modern 기본)
- renderer.py    3형식 HTML 렌더링
