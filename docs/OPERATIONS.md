# 운영 루틴

개원 후 매주 반복되는 동작을 정리한 문서입니다.
지금은 "이렇게 굴러갈 것"을 미리 정해 두는 용도이고,
개원하면 그대로 쓰면 됩니다.

---

## 매 수업 전 (5분)

```bash
python manage.py class next H1A
```

나오는 것:
- 이번이 몇 회차·몇 주차인지
- 그 주의 문법 주제 (커리큘럼 자동 매칭)
- 아직 그 반에 쓰지 않은 같은 레벨 자료 후보
- 자료가 모자라면 경고

자료를 골랐으면 그대로 인쇄합니다.
분석지·어휘 리스트·어휘 시험지는 이미 `output/` 에 있거나,
`report.json` 에서 언제든 다시 뽑을 수 있습니다.

---

## 매 수업 후 (2분)

```bash
python manage.py class log H1A \
    --materials H1-MOCK-0007 \
    --grammar "관계사 심화" \
    --homework "어휘 1~20 암기" \
    --absent S002
```

이 한 줄이 하는 일:
- 회차·날짜·사용 자료·결석이 기록됨
- 그 자료에 "H1A/7회" 사용 이력이 남음 → 다음 추천에서 자동 제외
- 출석률이 학생 리포트에 반영됨

**밀리면 안 되는 유일한 기록입니다.** 나머지는 나중에 채워도 됩니다.

---

## 어휘 테스트 채점 후

```bash
python manage.py student score S001 \
    --score 16 --total 20 \
    --wrong "vital,abandon,retain" \
    --materials H1-MOCK-0007
```

`--wrong` 에 틀린 단어를 넣는 게 핵심입니다.
이게 쌓이면 **학생별 오답 시험지**가 자동으로 만들어집니다.

```bash
python manage.py pack personal S001
```

→ 그 학생이 틀린 단어만 모은 시험지 PDF. 만드는 데 API 비용이 들지 않습니다.

---

## 4주마다 — 누적 복습

```bash
python manage.py pack review --class H1A --last 8 --name "H1A_1분기"
```

한 번에 세 가지가 나옵니다.

| 자료 | 쓰임 |
|---|---|
| 누적 어휘 리스트 | 시험 전 배부 |
| 누적 어휘 시험지 | 4주 누적 테스트 (정답 포함) |
| 문법 누적 시트 | 반복된 문법 포인트 정리 — 4주간 뭐가 뼈대였는지 한눈에 |

숙제지가 필요하면:

```bash
python manage.py pack homework --class H1A --last 2
```

---

## 4주마다 — 학부모 소통

```bash
python manage.py student report S001
```

- 출석률
- 누적 테스트 성취율
- 자주 틀린 단어 TOP 10

상담에서 "열심히 합니다" 대신 숫자를 말할 수 있게 하는 게 목적입니다.
승급 기준(`syllabus.yaml` 의 `promotion`)과 나란히 놓고 보세요.

---

## 매달 — 자료 점검

```bash
python manage.py status              # 전체 현황
python manage.py curriculum gap      # 어느 레벨이 비었나
python manage.py library dupes       # 중복 등록 점검
python manage.py library index       # CATALOG.md 갱신
```

그리고 **git 커밋**. 이게 곧 백업입니다.

```bash
git add library/ && git commit -m "자료 N편 추가"
```

---

## 학기말 (16주)

- [ ] 학기 총괄 평가 (`pack review --class H1A` — 범위 지정 없이 전체)
- [ ] 학생별 리포트로 승급 여부 판단
- [ ] `classes.yaml` 재편성
- [ ] 안 쓴 자료 점검: `library list --unused --level H1`
- [ ] 실패한 자료는 `status: retired` 로 내리고 `notes` 에 이유를 남긴다

---

## 개인정보 취급

- 학생 실명은 `school/students.yaml` **한 파일에만** 존재합니다.
- 진도·성적 기록에는 학생코드(S001)만 들어갑니다.
- `school/students.yaml`·`classes.yaml`·`*.jsonl` 은 `.gitignore` 로 막혀 있어
  실수로 커밋되지 않습니다. 저장소에는 `*.example.yaml` 만 올라갑니다.
- 퇴원생은 지우지 말고 `active: false` 로 두세요 — 재등록·문의 대응에 필요합니다.
  단, 보관 기간이 지난 정보는 실제로 삭제해야 합니다.
