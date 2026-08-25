# YBM 박준언 공통영어2 · O/X/△ 오답 재작업 (2026-08)
기존 소단원 분석(gen_gen*.py)에 새 '이렇게 읽으면 오답'(O/X/△ 판별) + 어법 형광펜(spans)을
오버레이로 얹어 재작업. API 키 없이 에이전트 저작 → verify → 렌더.
- ox_g*.json: 오버레이 {misreads, spans} (key="<item_no>||<sid>")
- apply_ybm.py: LESSON=1|2 로 실행 → 기존 gen 로드 + 오버레이 적용 → verify → 렌더
- 검증: 1과 E0·W2(지칭 트리거 없는 짧은 소단원 2곳), 2과 E0·W1
재빌드: `LESSON=1 RENDER=1 PYTHONPATH=<repo> python3 apply_ybm.py` (경로는 스크래치패드 기준)
