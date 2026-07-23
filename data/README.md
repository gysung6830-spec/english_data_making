# 영구 기출 코퍼스 (`data/corpus.jsonl`)

구문해석 실전서의 **"뇌"**. 기출 문장을 사실 데이터로 영구 저장해 두고, 교재
생성기가 여기서 재료를 뽑아 쓴다. PDF가 사라져도 이 파일이 있으면 코퍼스는 유지된다.

- **PDF 원본은 커밋하지 않는다**(저작권) → `input_corpus/*.pdf` 는 `.gitignore`.
- **추출된 문장(사실 데이터)은 커밋한다** → `data/corpus.jsonl` 은 버전관리.

## 레코드 형식 (JSONL 한 줄 = 한 문장)

```json
{"id":"a4cea8eb6c96","text":"...","source":"2024 고3 11월 23번",
 "year":2024,"grade":"고3","exam":"11월","item":23,
 "codes":["contrast"],"type":"apposition","difficulty":"고","self_contained":true}
```

| 필드 | 뜻 |
|------|-----|
| `id` | 정규화 텍스트 해시(중복 제거·재현용) |
| `source` | `2024 고3 11월 23번` 형태 출처 |
| `year/grade/exam/item` | 출처 파싱값(`item`=문항번호, 없으면 `null`) |
| `codes` | 평가원 코드 id 목록(인과·대조·동격 등) |
| `type` | 구문 유형 id(강조·도치·분사 등), 없으면 `null` |
| `difficulty` | `중`/`고` 어림 |
| `self_contained` | 앞 문장 없이 단독 출제 가능 여부 |

## 지속 적재 워크플로우

```bash
# 1) 새 기출 PDF를 input_corpus/ 에 넣는다 (파일명: 2025_고3_9월.pdf 형식)
# 2) 추출·태깅·중복제거 후 corpus.jsonl 에 '새 문장만' 누적 (멱등)
python scripts/ingest_corpus.py

# 저장소 통계만 보기
python scripts/ingest_corpus.py --stats

# 처음부터 다시 만들기
python scripts/ingest_corpus.py --rebuild
```

`ingest` 는 여러 번 돌려도 중복이 쌓이지 않는다(텍스트 해시로 판별).

## 교재 재료 뽑기 (생성기 연결)

```bash
# 챕터별로 지금 뽑을 수 있는 실제 기출 수 (얇은 챕터 파악)
python scripts/corpus_pick.py --coverage

# 특정 챕터의 실제 기출 후보 N개 (제외문항 20·25~29 자동 제외, 자기완결만)
python scripts/corpus_pick.py --type apposition -n 5
python scripts/corpus_pick.py --code contrast -n 5 --difficulty 고
```

뽑힌 문장을 교재 YAML(문제/카드)에 넣으면 된다. **코퍼스가 늘면 후보도 자동으로
늘어난다** — 새 기출을 ingest 하는 것만으로 교재가 채워질 재료가 확보된다.

프로그램에서 직접 쓰려면:

```python
from src.guide.corpus_store import pick, query, coverage
sents = pick(5, type="apposition")            # 동격 구문 실제 기출 5개
sents = query(code="causation", difficulty="고")
cov   = coverage()                            # 챕터별 후보 수
```

## 규칙 (교재와 동일)

- 제외 문항(**20·25·26·27·28·29번**) 문장은 조회에서 기본 제외.
- 기본은 `self_contained=true`(단독 출제 가능) 문장만.
