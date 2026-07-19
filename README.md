# 동형모의고사 자동생성 (mockexam)

학교가 낸 실제 시험지를 학습해, **그 학교의** 유형·문항수·배치·배점·난이도 그대로
동형모의고사를 생성합니다. 명세 v2.0 구현.

> ⚠️ 학교마다 스펙이 전부 다릅니다. 진양고 blueprint를 다른 학교에 적용하지 않습니다.
> 미학습 학교는 진양고를 베끼지 않고 **학교급(중/고) 표준 골격**으로 생성하다가,
> 그 학교 시험지를 학습할수록 그 학교 스타일로 수렴합니다.

## 빠른 시작 (API 키 없이 미리보기)

```bash
pip install pydantic PyYAML python-dotenv        # 최소 의존성
python run.py schools                         # 등록 학교 목록
python run.py generate --school jinyang_hs --grade 1 --difficulty 중 \
    --input input/sample_passages.txt --out output --mock
```

→ `output/mock_form_A.html`(문제지+정답), `output/blueprint_A.json`(스펙) 생성.
`--mock` 은 API 키를 무시하고 **구조만 채운 미리보기**를 만듭니다(검증기까지 전 구간 확인용).
WeasyPrint가 설치되어 있으면 PDF도 함께 생성됩니다.

## 웹앱으로 쓰기 (터미널 몰라도 OK)

```bash
pip install -r requirements.txt
python webapp.py          # 또는 Windows: start.bat 더블클릭
```
→ 브라우저에서 **http://localhost:5000** 접속.
지문 파일 올리기 → 학교·학년·난이도 고르기 → **저장할 파일 이름** 입력 → 만들기.
API 키가 없으면 '미리보기'로 배치·검증·디자인까지 확인할 수 있고, 키를 넣으면 실제 문항이 생성됩니다.
(WeasyPrint가 없으면 HTML로 저장되며, 브라우저에서 Ctrl+P → PDF로 저장하면 됩니다.)

## 실제 문항 생성 (LLM)

`.env` 에 `ANTHROPIC_API_KEY` 를 넣으면 `--mock` 없이 실제 지문/선지/정답이 생성됩니다.

```bash
python run.py generate --school jinyang_hs --input input --out output
```

## 학습 (learn 모드)

학교 시험지에서 뽑은 blueprint(json)로 그 학교 프로파일을 누적합니다.

```bash
python run.py learn --school jinyang_hs --name 2026_2_final \
    --blueprint path/to/blueprint.json
```

- 같은 학교 재입력 → `profiles/<school>/profile.json` 에 **누적**.
- 다른 학교 → 별도 폴더로 **분리**(섞이지 않음).

## 파이프라인 (§0)

```
school_id + 지문들 + 난이도
  → [1] 프로파일 로드(profiles/<school>/profile.json, 미학습이면 표준 골격)
  → [2] blueprint 구성(그 학교 스펙)
  → [3] 지문 파싱 + 규칙기반 프로파일링
  → [4] 지문 자동배정(형식 유형 하드제약, 재사용 상한 3)
  → [5] 유형별 문항 생성(난이도 레버 적용)
  → [6] 검증(문항수·배점·배치·정답유일성·번호·밑줄·난이도) → 실패 문항 재생성
  → [7] 조판(좌우 2단 HTML/PDF, 문제지+정답해설지)
```

## 모듈 구조 (§4)

```
mockexam/
├── core/       models.py  llm.py  blueprint.py
├── ingest/     loader.py          # PDF/사진(OCR)/HWP/TXT → 지문 분리
├── corpus/     selector.py        # 규칙기반 프로파일링 + 적합도 + 배정
├── generators/ base.py engine.py grammar.py vocab.py reading.py dialogue.py essay.py
├── verify/     verifier.py        # 7개 검증
├── render/     exam.py            # 2단 HTML→PDF
├── school.py                      # 학교 프로파일 IO + 학교급 표준 골격
└── pipeline.py                    # generate/learn 오케스트레이션
profiles/                          # 학교별 프로파일(완전 분리)
├── schools.json
└── jinyang_hs/{profile.json, principles.md, exams/}
```

## 설정 (mock_config.yaml, §8.5.7)

```yaml
mode: generate        # learn | generate
school_id: jinyang_hs
grade: 1
difficulty: 중        # 상 | 중 | 하
passage_mode: assign  # 올린 지문만으로 자동배정(새 지문 생성 안 함)
answer_key: end       # end(맨 뒤) | separate(별도 파일)
num_forms: 1
```

## 테스트

```bash
python -m pytest tests/test_mockexam.py -q   # 오프라인 전 구간 검증
```
