# Trial Card — p0-20260411-baseline

> Created: 2026-04-11
> Phase: p0
> Domain: japan-travel
> Status: planned

## Goal
P0 Foundation Hardening 완료 증명 — Phase 4·5 동등 스모크 재현

## Config Diff
baseline (no diff)

## 가설
- H1: P0 remediation (bare-except 제거, timeout, retry) 적용 후에도 VP1 ≥ 4/5 재현
- H2: P0 remediation 적용 후에도 VP2 ≥ 5/6 재현
- H3: HITL-A/B/C 제거 후 일반 cycle 에서 인라인 HITL 호출 0건

## 측정 대상
- VP1 (Variability): active_ku_count, category_count, avg_confidence, conflict_rate, gap_resolution_rate
- VP2 (Completeness): evidence_ratio, cross_validated_ratio, staleness_ratio, coverage, domain_entropy, cycle_growth_rate
- VP3 (Self-Governance): audit_compliance, policy_evolution_count, convergence_detected, explore_exploit_ratio, self_tune_count, readiness_gate_pass
- collect_failure_rate, timeout_count, retry_success_rate
- HITL-A/B/C 호출 횟수

## 실행 명령

```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p0-20260411-baseline \
  --cycles 15
```

## 상태
- [ ] config.snapshot.json 기록됨
- [ ] 실행 완료
- [ ] readiness-report.md 작성됨
- [ ] INDEX.md row 갱신
