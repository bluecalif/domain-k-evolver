# Readiness Report: p0-20260412-baseline

> **Date**: 2026-04-12
> **Phase**: Silver P0 (Foundation Hardening)
> **Verdict**: **PASS**

## Trial Summary

| 항목 | 값 |
|------|-----|
| Trial ID | p0-20260412-baseline |
| Seed | `bench/japan-travel/state-snapshots/cycle-0-snapshot/` (13 KU, cycle 0) |
| Cycles | 15 (cycle 1~15) |
| Script | `run_readiness.py --bench-root` (Orchestrator, audit_interval=5) |
| Model | gpt-4.1-mini |
| Search | Tavily |
| KU growth | 42 → 127 (+85) |
| GU resolved | 12 → 95 |
| Jump cycles | 14/15 |
| Invariant violations | 0 |

---

## VP1: Expansion Variability — **5/5 PASS**

| 기준 | 임계치 | 실측 | PASS |
|------|--------|------|------|
| R1_category_gini | ≤ 0.45 (critical) | 0.1644 | O |
| R2_blind_spot | ≤ 0.40 | 0.000 | O |
| R3_late_discovery | ≥ 2 | 24 | O |
| R4_field_gini | ≤ 0.45 | 0.2863 | O |
| R5_explore_yield | ≥ 0.20 | 0.9333 | O |

## VP2: Completeness — **5/6 PASS**

| 기준 | 임계치 | 실측 | PASS |
|------|--------|------|------|
| R1_gap_resolution | ≥ 0.85 (critical) | 0.9314 | O |
| R2_min_ku_per_cat | ≥ 5 (critical) | 9 | O |
| R3_multi_evidence | ≥ 0.80 | 0.7165 | **X** |
| R4_avg_confidence | ≥ 0.82 | 0.8297 | O |
| R5_health_grade | ≥ 1.4 | 1.8 | O |
| R6_staleness | ≤ 2 | 0 | O |

> R3_multi_evidence (non-critical): 다중 증거 비율 71.6% — P1 Stability 에서 collect_node 의 multi-source 수집 강화로 개선 예상.

## VP3: Self-Governance — **5/6 PASS**

| 기준 | 임계치 | 실측 | PASS |
|------|--------|------|------|
| R1_audit_count | ≥ 2 (critical) | 3 | O |
| R2_policy_changes | ≥ 1 (critical) | 3 | O |
| R3_threshold_adapt | ≥ 1 | 3 | O |
| R4_adapted_ratio | ≥ 3 | 14 | O |
| R5_rollback | ≥ 0 | 0 | O |
| R6_closed_loop | ≥ 1 | 0 | **X** |

> R6_closed_loop (non-critical): audit finding → plan 반영 루프 미발동. P2 에서 plan_modify 와 audit 연계 강화로 개선 예상.

---

## Phase 5 대비 Delta

| 지표 | Phase 5 (b122a23) | P0 baseline | Delta |
|------|-------------------|-------------|-------|
| VP1 | 5/5 | 5/5 | = |
| VP2 | 6/6 | 5/6 | -1 (R3_multi_evidence) |
| VP3 | 5/6 | 5/6 | = |
| avg_confidence | 0.822 | 0.830 | +0.008 |
| conflict_rate | 0.000 | 0.000 | = |
| gap_resolution | 0.909 | 0.931 | +0.022 |
| Active KU | 77 | 127 | +50 |
| Tests | 468 | 510 | +42 |

> **Note**: Phase 5 는 Bronze seed (cycle 0~13, 13 cycle), P0 는 fresh seed (cycle 0~15, 15 cycle). 직접 비교는 참고용.
> VP2 R3 regression: Phase 5 에서는 Bronze 누적 데이터로 multi_evidence 가 높았으나, fresh seed 15 cycle 에서는 아직 축적 불충분. 구조적 문제 아님.

---

## Gate 판정

**PASS** — VP1 5/5, VP2 5/6, VP3 5/6. Critical FAIL 없음.

- 판정 일시: 2026-04-12
- Commit: (gate commit 후 기록)
