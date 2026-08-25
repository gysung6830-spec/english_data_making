# 올림포스 10강–14강 · O/X/△ 오답 재작업 (2026-08)

기존 19지문 합본(batch #00)을 **새 '이렇게 읽으면 오답' 규격**으로 재작업한 산출물·소스 스냅샷.

## 무엇이 바뀌었나
- ③ 문장별 오답을 **O / X / △ 판별 + 틀린 것 고치기** 형식으로 전면 교체
- 내신·2등급 함정 유형 6종(주체대상·인과조건·지칭·무관정보·필자관점·구조수식) + 본문대조 앵커
- 지문당 🔥킬러 1 · EN 영어오답 1 · △ 1 · 참(O) 진술 ≥2 · 커버리지 쿼터(지칭·무관정보·필자관점)
- 어법 형광펜용 `spans`(강사용) 동시 저작
- 검증: `verify_passages` **ERROR 0** (WARN 6 = 미매칭 어법칩 spans 소수 + 기존 청크 빈칸 1)

## 파일
- `ol_data.json` — 19지문 원자료(문장·어법칩) 덤프 (`dump_ol.py` 산출)
- `SPEC.md` — 저작 규격(에이전트가 따른 규칙)
- `ox_g1.json`~`ox_g6.json` — 그룹별 오버레이 `{misreads, spans}` (key = `"<item_no>||<sid>"`)
- `apply_ox.py` — 오버레이 적용 → verify → 렌더 (합본 학생/강사 PDF)
- `src_snapshot/` — 배치 코어 소스(gen_ol·gen_u12·gen_u13·apply_chips·gen_add1/2·mt_g*·rechunk/·blanks/·_helpers_oladd) 백업

## 재빌드
`apply_ox.py`·`dump_ol.py` 는 세션 스크래치패드 경로(`SC=...`)를 참조합니다.
새 세션에서 돌리려면 `src_snapshot/` 를 스크래치패드로 복사하고 상단 `SC` 경로를 맞춘 뒤:
```
RENDER=1 PYTHONPATH=<repo> python3 apply_ox.py
```
(API 키 없이 동작 — 오답·형광펜은 오버레이에 저작돼 있음)
