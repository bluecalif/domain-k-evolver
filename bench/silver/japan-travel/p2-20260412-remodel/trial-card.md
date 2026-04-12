# Trial Card: p2-20260412-remodel

| 항목 | 값 |
|------|-----|
| trial_id | p2-20260412-remodel |
| domain | japan-travel |
| phase | si-p2-remodel |
| date | 2026-04-12 |
| goal | P2 Gate E2E — 합성 state + Orchestrator 10 cycle, remodel 전 경로 검증 |
| status | completed |

## Config

- **Seed**: 합성 state (transport entity 4 KU, 중복률 100%)
- **Model**: N/A (inner loop mock, outer loop 실제)
- **Search**: N/A (합성 E2E)
- **Cycles**: 10 (audit_interval=5 → cycle 5, 10에서 audit+remodel)
- **Orchestrator**: `tests/test_p2_gate_e2e.py` 기반 합성 E2E
- **Plateau**: disabled (plateau_window=100)

## Hypothesis

합성 state에서:
1. 중복률 100% entity → merge proposal 확실 발동
2. HITL-R 승인 → entity_key 통합 + phase bump
3. HITL-R 거부 → state diff = ∅
4. S7 trigger 경로 (audit → critical → remodel)
5. Remodel report → schema validate

## Results

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Cycles run | 10 | 10 | PASS |
| Remodel report schema | validate pass | validate pass | PASS |
| Merge proposal 생성 | 중복률 30%+ → merge 제안 | overlap 100% merge 생성 | PASS |
| HITL-R 승인 반영 | entity_key 통합 | item-01/02 → 1 key | PASS |
| Rollback state diff | = ∅ | diff = ∅ | PASS |
| S7 trigger 경로 | audit → remodel | cycle 5 audit → remodel | PASS |
| phase snapshot | phase_{N}/ 존재 | phase_1/ 존재 | PASS |
| Total tests | ≥ 623 | 660 | PASS |

**Gate 판정**: PASS (8/8 항목 통과)
