# 자료 라이브러리 운영 규칙

> 몇 년 뒤 교습소를 열 때, 가장 값나가는 재산은 PDF 폴더가 아니라
> **다시 쓸 수 있게 정리된 분석 데이터**입니다. 이 문서는 그 데이터를
> 어떤 규칙으로 쌓을지 정해 둔 것입니다.

---

## 1. 왜 PDF 가 아니라 데이터로 쌓는가

PDF 는 결과물이지 자산이 아닙니다. 디자인을 바꾸거나, 여러 지문을 묶어
누적 시험지를 만들거나, 학생별로 다른 문제를 뽑으려면 **원본 분석 결과**가
있어야 합니다.

그래서 지문 하나를 분석할 때마다 아래 세 조각이 함께 저장됩니다.

```
library/passages/H1-MOCK-0007/
    meta.yaml      ← 레벨·유형·출처·어휘목록·사용이력
    report.json    ← 분석 결과 원본 (이게 진짜 자산)
    source.txt     ← 지문 원문 (검색·중복확인용)
```

`report.json` 이 있으면 **API 비용 0원으로** 언제든 PDF 를 다시 뽑고,
여러 지문을 묶어 새 자료를 만들 수 있습니다.

---

## 2. 자료 ID 규칙

```
H1 - MOCK - 0007
│    │      └─ 그 레벨·유형 안에서의 일련번호 (자동 부여)
│    └─ 자료 유형 코드
└─ 레벨 코드 (curriculum/levels.yaml)
```

| 유형 | 코드 | 무엇 |
|---|---|---|
| `textbook` | TXT | 학교 교과서 |
| `school` | SCH | 내신 기출·학교 프린트 |
| `mock` | MOCK | 모의고사 |
| `csat` | CSAT | 수능 기출 |
| `ebs` | EBS | EBS 연계교재 |
| `book` | BOOK | 시중 문제집·원서 |
| `custom` | CUS | 자체 제작 지문 |

ID 는 손으로 정하지 않습니다 — 등록할 때 자동으로 붙습니다.

---

## 3. 메타데이터 필드

`meta.yaml` 에서 **사람이 채우는 값**은 굵게 표시했습니다.
나머지는 분석 결과에서 자동으로 계산됩니다.

| 필드 | 설명 |
|---|---|
| `id` | 자료 ID (자동) |
| `title` / `theme_ko` | 제목 / 한글 주제 (자동) |
| **`level`** | 레벨 코드. 비우면 지문 길이로 추천값이 들어감 |
| **`category`** | 위 표의 자료 유형 |
| **`source`** | 출처 상세 — "2026 6월 모평 31번", "능률 김성곤 3과" |
| `item_no` | 원본 문항 번호 (자동) |
| `genre` | `logic`(논설) / `emotional`(문학) — 구조 분석에서 자동 판별 |
| **`tags`** | 자유 태그 — 주제·용도. 예: `환경`, `실험지문`, `내신단골` |
| **`status`** | `draft`(검토 전) / `ready`(수업 투입 가능) / `retired`(사용 중지) |
| `added` | 등록일 (자동) |
| `hash` | 지문 fingerprint — 같은 지문 두 번 등록 방지 (자동) |
| `stats` | 단어 수·문장 수·문장당 평균·어휘 수·문법 수 (자동) |
| `vocab` | 핵심 어휘 목록 — 누적 시험지·중복 점검에 쓰임 (자동) |
| `grammar_points` | 문법 포인트 목록 (자동) |
| `used_in` | 어느 반 몇 회차에 썼는지 (수업 기록 시 자동) |
| **`notes`** | 수업하며 알게 된 것 — "3번 문장에서 애들이 다 막힘" |

`notes` 를 성실히 쓰면 2년 뒤의 나에게 가장 고마운 필드가 됩니다.

---

## 4. 일상 워크플로

### 지문을 새로 분석할 때
`input/` 에 넣고 `python run.py` 를 돌리면 **자동으로 라이브러리에 등록**됩니다.
(`config.yaml` 의 `library.enabled: true`)

레벨을 미리 정해 두고 한 묶음씩 처리하면 정리가 훨씬 깔끔합니다.

```yaml
# config.yaml
library:
  default_level: "H1"       # 이번에 넣을 지문들의 레벨
  default_category: mock
```

### 이미 있는 분석 결과를 가져올 때
```bash
python manage.py library add path/to/report.json \
    --level H1 --category mock --source "2026 6월 모평 31번" --tags "환경,논설문"
```

### 등록 후 정리
```bash
python manage.py library list --level H1 --status draft   # 검토 대기 목록
python manage.py library set H1-MOCK-0007 --status ready --tags "환경,빈칸추론"
python manage.py library show H1-MOCK-0007                 # 상세 확인
python manage.py library dupes                             # 중복 등록 점검
python manage.py library index                             # CATALOG.md 갱신
```

---

## 5. 지켜야 할 세 가지

1. **`status: draft` 로 먼저 들어오게 하고, 눈으로 본 뒤 `ready` 로 올린다.**
   검수 안 된 자료가 수업에 들어가는 사고를 막는 유일한 장치입니다.
   (`config.yaml` 의 `library.default_status: draft` 로 바꾸면 기본이 됩니다)

2. **출처(`source`)를 반드시 남긴다.**
   저작권 문제가 생겼을 때, 어느 자료를 내려야 하는지 즉시 찾을 수 있어야 합니다.

3. **`library/` 는 백업 대상 1순위다.**
   git 에 커밋해 두면 그 자체가 백업입니다. 컴퓨터가 죽어도 자료는 남습니다.

---

## 6. 저작권에 대해

교과서·모의고사·시중 교재 지문은 저작권이 있는 저작물입니다.
분석 데이터를 개인 수업 준비용으로 보관하는 것과, 그것을 **배포·판매**하는 것은
전혀 다른 문제입니다. 개원 시점에는 아래를 확인해 두세요.

- 수업용 복제의 허용 범위 (학원·교습소는 학교와 기준이 다릅니다)
- 한국복제전송저작권협회(KORRA) 등의 이용 허락 절차
- 자체 제작 지문(`custom`) 비중을 늘려 두면 이 문제에서 자유로워집니다

`config.yaml` 의 `design.footer_note` 로 모든 산출물 하단에 출처 문구가 박힙니다.
