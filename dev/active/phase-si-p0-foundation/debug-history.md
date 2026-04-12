# Silver P0: Foundation Hardening — Debug History
> Last Updated: 2026-04-12
> Status: Complete

Phase 전체 디버깅 이력. 버그/이슈 발견 → 원인 분석 → 수정 → 교훈 순으로 기록.

---

## 이력

### [2026-04-12] D1 첫 시도 FAIL — Bronze seed + 5 cycle baseline

- **증상**: VP1 3/5 (blind_spot 0.625, field_gini 0.5068), VP2 3/6 (gap_resolution 0.5091, avg_confidence 0.7764, staleness 23), VP3 3/6 (audit_count 0, policy_changes 0, threshold_adapt 0)
- **원인**:
  1. **staleness 23건**: Bronze seed (cycle 14) 의 KU 에 오래된 `observed_at` 가 갱신 안 됨 → VP2 R6 FAIL
  2. **audit=0**: `run_bench.py` 는 `graph.invoke()` 직접 호출 → Orchestrator 미경유 → audit 미실행 → VP3 전체 FAIL
  3. **blind_spot/field_gini**: Bronze seed 데이터가 특정 카테고리에 편향 + 5 cycle 부족 → VP1 FAIL
  4. **avg_confidence 낮음**: Bronze 누적 데이터의 오래된 confidence 값이 가중 평균에 영향
- **수정**: Fresh seed (cycle 0, 13 KU) + 15 cycle + `run_readiness.py` (Orchestrator 경유, audit_interval=5) 로 재실행 → **VP1 5/5, VP2 5/6, VP3 5/6 PASS** (`30946ac`)
- **교훈**:
  - E2E bench 는 반드시 Orchestrator 경유 (`run_readiness.py`) 사용. `run_bench.py` 는 audit/policy 미포함
  - Bronze seed 재활용 시 staleness 리스크 발생. Fresh seed 로 시작하는 것이 안전
  - Phase gate = E2E bench + self-eval + debug loop 필수 (feedback memory 에 기록)
