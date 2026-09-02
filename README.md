# 영어 지문 자동 분석 자료 생성 도구

영어 지문 PDF를 넣으면 **분석지(6개 섹션)·어휘 리스트·영단어 시험지** 3종 PDF를 자동으로 만들어 주는 개인용 도구입니다.
지문 1000개도 순차 처리할 수 있습니다.

1. **내용 전체 요약 정리** — 전체 요약 + 문단별 요약
2. **직독직해** — 2단 표(왼쪽 원문+구문분석 / 오른쪽 직독직해+핵심단어)
3. **핵심 문법 TOP 10** — 지문 예문 + 설명
4. **핵심 어휘 · 유의어 · 반의어** — 지문 길이에 비례해 12~20개
5. **지문 구조 분석** — Logic Flow(논설문) / Emotional Flow(문학) 자동 분기
6. **내신 빈출 출제 포인트 체크리스트** — ③④와 일관성 있게 작성

---

## 🏫 교습소 자료·운영 시스템 (`manage.py`)

지문 1편을 자료 3종으로 바꾸는 게 `run.py` 라면, **쌓인 자료를 굴리는 일**은
`manage.py` 가 합니다. 몇 년에 걸쳐 자료를 모으고, 그걸 그대로 수업으로
연결하기 위한 층입니다.

```bash
python manage.py status                       # 전체 현황 한 장
python manage.py curriculum gap               # 어느 레벨 자료가 비었나
python manage.py class next H1A               # 다음 회차 준비물
python manage.py pack review --class H1A --last 8   # 4주 누적 복습 자료
```

### 네 개의 층

| 층 | 폴더 | 하는 일 |
|---|---|---|
| **자료 라이브러리** | `library/` | 분석 결과(`report.json`)를 메타데이터와 함께 보관. 중복 지문 자동 차단, 검색·통계·카탈로그 |
| **커리큘럼** | `curriculum/` | 레벨 9단계 + 문법 시퀀스. 주차 진도표와 자료 부족분을 **계산해서** 뽑아 줌 |
| **자료 팩** | `src/packs.py` | 여러 지문을 가로질러 누적 어휘 시험지·문법 시트·개인 오답 시험지 생성 (**API 비용 0원**) |
| **운영** | `school/` | 반·학생·진도·성적. 진도 기록이 다음 회차 자료 추천으로 이어짐 |

### 왜 이렇게 쌓는가

PDF 는 결과물이지 자산이 아닙니다. 지문을 분석할 때마다 **분석 결과 원본**이
`library/passages/<자료ID>/report.json` 으로 저장되므로, 나중에 디자인을 바꾸거나
여러 지문을 묶어 새 자료를 만들 때 **API 를 다시 태울 필요가 없습니다.**

`run.py` 를 돌리면 자동으로 등록됩니다 (`config.yaml` 의 `library.enabled`).

### 하루 루틴

```bash
python manage.py class next H1A                       # 수업 전: 준비물 확인
python manage.py class log H1A --materials H1-MOCK-0007 --absent S002   # 수업 후: 기록
python manage.py student score S001 --score 16 --total 20 --wrong "vital,retain"
python manage.py pack personal S001                   # 그 학생 오답만 모은 시험지
```

### 문서

| 문서 | 내용 |
|---|---|
| [docs/ROADMAP.md](docs/ROADMAP.md) | 개원까지 단계별 자료 구축 계획 (총 864편 · 페이스 계산 · 행정 체크리스트) |
| [docs/CURRICULUM.md](docs/CURRICULUM.md) | 레벨 9단계, 16주 진도, 90분 수업 구성, 승급 기준 |
| [docs/LIBRARY.md](docs/LIBRARY.md) | 자료 ID·메타데이터 규칙, 등록 워크플로, 저작권 |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | 수업 전/후, 4주, 학기말 루틴 + 개인정보 취급 |

> 학생 정보(`school/students.yaml` 등)는 `.gitignore` 로 막혀 있어 저장소에
> 올라가지 않습니다. 예시 파일(`*.example.yaml`)만 커밋됩니다.

---

## 🖼 결과물 미리보기 (API 키 없이)

API 키가 아직 없어도, 샘플 데이터로 **디자인을 미리 볼 수 있습니다.**

```bash
bash setup.sh                 # 최초 1회 설치
python -m samples.make_sample_pdf   # 테스트용 지문 PDF 생성
python run.py --mock          # 샘플 데이터로 output/에 미리보기 PDF 생성
```

→ `output/sample_passage_analysis.pdf` 가 만들어집니다.

---

## 🌐 웹앱으로 쓰기 (터미널 몰라도 OK, 추천)

브라우저에서 파일을 올리고 버튼만 누르면 되는 방식입니다.

```bash
bash setup.sh        # 최초 1회 설치 (flask 포함)
python webapp.py     # 웹 서버 실행
```

그다음 브라우저 주소창에 **http://localhost:5000** 입력 → 접속.

- 지문 **사진(JPG/PNG)·PDF·HWP를 끌어다 놓고** → API 키 입력(또는 '샘플 미리보기' 체크) → **분석 시작**
- 완료되면 결과 PDF를 **미리보기 / 다운로드**할 수 있습니다.
- API 키는 화면에서 입력하거나, `.env` 파일에 넣어두면 자동으로 쓰입니다.

> 종료하려면 실행한 터미널에서 `Ctrl + C`.

### 📱 아이패드·폰에서도 쓰려면?
아이패드에는 파이썬을 못 깔기 때문에, 웹앱을 **인터넷에 한 번 올려두면** 어느 기기에서든
링크로 접속해 쓸 수 있어요. 단계별 방법은 **[DEPLOY.md](DEPLOY.md)** 를 참고하세요.
(배포용 `Dockerfile` · `render.yaml` 포함, 접속 비밀번호 잠금 내장.)

---

## 🚀 터미널로 쓰기 (3단계)

### 1) 최초 1회 설치

```bash
bash setup.sh
```

- 파이썬 라이브러리 설치
- 한글 폰트(나눔고딕) 설치
- `.env` 파일 생성

### 2) API 키 입력

`.env` 파일을 열어 본인의 Anthropic API 키를 넣습니다.

```
ANTHROPIC_API_KEY=sk-ant-...여기에_본인_키...
```

> API 키는 https://console.anthropic.com 에서 발급받습니다.
> 키는 코드에 직접 쓰지 않고 항상 이 `.env` 파일로만 관리합니다.

### 3) 지문 넣고 실행

- `input/` 폴더에 분석할 지문 **PDF · 사진(JPG/PNG) · HWP(.hwp/.hwpx)를 넣습니다.** (여러 개, 섞어서 가능)
  - HWP는 '글자가 살아있는' 파일이면 원문 그대로 정확히 읽습니다(가장 저렴·정확). 지문이 이미지로 박힌 HWP는 PDF/사진으로 저장해 주세요.
  - 글자 PDF는 그대로, 사진/캡처는 Claude 비전이 지문을 읽어서 처리합니다.
- 아래를 실행합니다.

```bash
python run.py
```

- 진행 상황이 터미널에 표시됩니다. (예: `[342/1000] 완료: ...`)
- 완성된 분석 PDF는 `output/` 폴더에 저장됩니다.

---

## 📦 대량 처리(1000개 등)

비용을 아끼려면 Anthropic **Batch API** 모드를 씁니다.

```bash
python run.py --batch
```

- 요청을 한꺼번에 묶어 처리하므로 비용이 약 50% 저렴합니다.
- 시간은 더 걸릴 수 있습니다(보통 1시간 내, 최대 24시간).

---

## ⚙️ 설정 바꾸기 (`config.yaml`)

코딩을 몰라도 이 파일의 숫자/값만 바꾸면 됩니다.

| 항목 | 설명 |
|---|---|
| `extraction.pdf_mode` | PDF 읽는 방식: `vision`(이미지로 렌더해 비전으로 정확히 읽기·기본) / `text`(빠름·저렴) / `auto` |
| `vocab.min` / `vocab.max` | 어휘 개수 범위 (기본 12~20) |
| `processing.parallel_sections` | 6개 섹션을 동시에 요청(빠름) |
| `processing.max_retries` | 검증 실패 시 재요청 횟수 |
| `design.footer_note` | PDF 하단 출처 문구 |
| `design.one_pdf_per_passage` | `true`=지문별 PDF, `false`=하나로 합본 |
| `outputs.analysis` | 지문 분석지 생성 여부 |
| `outputs.wordlist` | 직독직해 핵심 어휘 리스트 생성 여부 |
| `outputs.quiz` | 영단어 시험지(정답 포함) 생성 여부 |

### 한 번에 나오는 3가지 자료

지문 하나를 분석하면 아래 3종 PDF가 함께 만들어집니다. (`config.yaml` 의 `outputs`, 웹앱의 체크박스로 선택)

1. **분석지** (`(지문명)_지문분석.pdf`) — 주제·요약문·구조 분석·출제 포인트·어휘·직독직해
2. **어휘 리스트** (`(지문명)_어휘리스트.pdf`) — 직독직해 오른쪽 열의 핵심 어휘를 모아 정리
3. **영단어 시험지** (`(지문명)_어휘test.pdf`) — 위 어휘를 무작위로 섞어 뜻을 적게 하는 시험지(맨 뒤에 정답)

> 웹앱에서는 **저장 파일명(지문명)** 을 직접 입력할 수 있습니다. 비우면 올린 파일 이름이 쓰입니다.

---

## 🧩 동작 방식 (내부 구조)

```
PDF → 텍스트 추출 → (전처리로 문제/정답 제거)
    → 본문 추출(1) → 6개 섹션 각각 개별 API 호출(2~7)
    → JSON 검증(+실패 시 1회 재요청) → HTML → PDF 조립
```

- **6개 섹션을 하나로 합치지 않고 각각 따로 요청**하여 품질을 안정화합니다.
- 각 응답은 자유 텍스트가 아니라 **구조화된 JSON**으로 받아 개수/필드 오류를 코드가 검증합니다.
  (예: 핵심 문법이 정확히 10개가 아니면 자동 재요청)
- 1000개 처리 중 일부가 실패해도 **전체가 멈추지 않고** 계속 진행합니다.
- 성공/실패 파일은 `logs/` 에 기록됩니다.
  - `logs/processed.jsonl` — 성공한 파일
  - `logs/failed.jsonl` — 실패한 파일 + 원인
  - `logs/run.log` — 전체 실행 로그

실패한 파일만 다시 처리하려면, `input/`에 해당 PDF만 남기고 `python run.py` 를 다시 실행하면 됩니다.

---

## 🎨 디자인 규칙

- 섹션별 통일된 컬러 스킴: **문법=파랑, 어휘=초록, 구조/감정=보라**, 요약=청록, 직독직해=주황, 출제=자주
- 표는 헤더 배경색 + 줄무늬(zebra), 강조 박스, 섹션 번호 배지
- 구조 분석은 지문 유형에 따라 **Logic / Emotional 템플릿 자동 분기**

---

## 📁 폴더 구조

```
input/       분석할 지문 PDF를 넣는 곳
output/      완성된 분석 PDF가 나오는 곳
logs/        처리 성공/실패 기록
library/     자료 라이브러리 — 분석 결과 원본 + 메타데이터 (자산)
curriculum/  레벨 정의 · 수업 운영 규격
school/      반·학생·진도·성적 (실데이터는 git 제외)
docs/        로드맵 · 커리큘럼 · 자료 규칙 · 운영 루틴
config.yaml  설정
.env         API 키 (직접 만들며 git에 올라가지 않음)
run.py       지문 분석 실행 진입점
manage.py    자료·운영 관리 CLI
src/         핵심 코드
templates/   PDF 디자인(HTML/CSS)
samples/     테스트용 샘플/목 데이터
tests/       오프라인 자동 테스트
```

---

## ❓ 자주 겪는 문제

- **한글이 깨져요** → 나눔고딕 폰트가 설치돼야 합니다. `setup.sh` 를 다시 실행하거나 나눔고딕을 직접 설치하세요.
- **`ANTHROPIC_API_KEY 가 설정되지 않았습니다`** → `.env` 파일에 키를 넣었는지 확인하세요. (키 없이 디자인만 보려면 `--mock`)
- **스캔한 이미지 PDF라 분석이 안 돼요** → 글자가 복사되지 않는 스캔본 PDF는 자동으로 못 읽습니다. 그 페이지를 **사진(JPG/PNG)으로 저장해서 넣으면** 비전으로 읽어 처리됩니다.

---

## 🧪 개발자용: 오프라인 테스트

```bash
python -m tests.test_offline    # 전처리 · 스키마 검증 · 재시도 · 렌더링
python -m tests.test_system     # 라이브러리 · 커리큘럼 · 운영 · 자료 팩
```

둘 다 API 키 없이 돌아갑니다. `test_system` 은 임시 폴더에서만 동작하므로
실제 `library/`·`school/` 데이터를 건드리지 않습니다.
