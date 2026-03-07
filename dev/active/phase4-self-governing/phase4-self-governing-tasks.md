# Phase 4: Self-Governing Evolver — Tasks
> Last Updated: 2026-03-07
> Status: Suspended (11/11 tasks complete, Gate FAIL — VP1/VP2)

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A: Outer Loop Audit | 3 | 0 | 2 | 1 | 3/3 |
| B: Policy Evolution | 3 | 0 | 2 | 1 | 3/3 |
| C: Strategic Self-Tuning | 3 | 0 | 2 | 1 | 3/3 |
| D: Evolver Readiness Gate | 2 | 0 | 1 | 1 | 2/2 |
| **합계** | **11** | **0** | **7** | **4** | **11/11** |

**Gate 결과**: FAIL (VP1, VP2 실패 / VP3 PASS) — 보완 Phase 논의 필요

---

## Stage A: Outer Loop Audit

> Gate: Audit 노드가 5-cycle 주기로 자동 실행, AuditReport 생성 확인 ✅

- [x] **4.1** Executive Audit 프레임워크 구현 `[L]` — `cebd47e`
  - `src/nodes/audit.py` 신규 — run_audit() + 4개 분석 함수
  - AuditReport 타입: `src/state.py` (AuditFinding, PolicyPatch, AuditReport)
  - `src/config.py` — audit_interval 파라미터 (기본 5, 0=비활성)
  - `src/orchestrator.py` — _maybe_run_audit() + audit_reports + audit_history
  - 테스트 23개 (audit 단독) + 3개 (orchestrator 통합) = 26개 신규
  - 전체 327 tests passed

- [x] **4.2** 다축 교차 커버리지 진단 `[M]` — `cebd47e`
  - `_analyze_cross_axis_coverage()`: Shannon entropy 균등도 + 최소 KU 진단
  - category × geography 교차 blind_spot_ratio 계산
  - F-COV-01 (axis_imbalance), F-COV-GEO (blind spot), F-COV-{cat} (coverage_gap)

- [x] **4.3** KU Yield/Cost 효율 분석 `[M]` — `cebd47e`
  - `_analyze_yield_cost()`: cycle별 yield 계산 + 후반 체감 감지
  - `_analyze_quality_trends()`: confidence 하락, multi_evidence 정체
  - F-YIELD-01 (yield_decline), F-QUAL-01/02 (quality_issue)

---

## Stage B: Policy Evolution

> Gate: AuditReport.policy_patches → policies.json 자동 반영 확인 ✅

- [x] **4.4** Policy 스키마 + 버전 관리 `[M]` — `816fb2d`
  - `schemas/policy.json` 신규 생성
  - policies.version 필드 + change_history 배열
  - 정책 변경 전/후 diff 로깅

- [x] **4.5** Audit → Policy 자동 수정 경로 `[L]` — `816fb2d`
  - policy_patches 파싱 + policies.json 반영
  - 수정 가능 정책: TTL, min_sources, credibility_priors, cross_validation
  - Safety: 한 Audit당 최대 3 필드 변경
  - Rollback: 변경 후 1 cycle 성능 악화 → 자동 복원

- [x] **4.6** Source Credibility 학습 `[M]` — `816fb2d`
  - EU source_type별 conflict/stale 기여 추적
  - credibility_priors 자동 조정 (guardrail 범위 내)

---

## Stage C: Strategic Self-Tuning

> Gate: threshold 또는 explore/exploit 비율이 자동 변경된 cycle ≥ 1 ✅

- [x] **4.7** Explore/Exploit 비율 자동 조정 `[L]` — `31ef46d`
  - `_compute_audit_bias()`: Audit findings 기반 explore/exploit bias (±0.15 guardrail)
  - `_compute_budget()` audit_bias 파라미터 추가
  - coverage_gap → explore↑, yield_decline → exploit↑

- [x] **4.8** Jump Trigger 동적 관리 `[M]` — `31ef46d`
  - `_compute_trigger_t6_audit()`: Audit axis_imbalance → T6 trigger
  - mode_node에 T6:audit_axis_imbalance 연동

- [x] **4.9** Convergence 조건 고도화 `[M]` — `31ef46d`
  - `_check_convergence()` C7 조건: critical audit findings 시 수렴 유보
  - critique_node에서 audit_history 전달

---

## Stage D: Evolver Readiness Gate (필수 체크포인트)

> Gate: 3대 관점 판정 실행 완료 — **FAIL** (VP1, VP2)

- [x] **4.10** Readiness 벤치마크 실행 `[L]` — `62915de`
  - japan-travel 13 Cycle 실행 (plateau 조기 종료)
  - Audit 2회 + Policy 수정 2회 자동 발생 확인
  - 결과: `bench/japan-travel-readiness/`, 보고서: `docs/phase4-readiness-report.md`

- [x] **4.11** 3-Viewpoint Readiness 판정 `[M]` — `62915de`
  - `src/utils/readiness_gate.py`: VP1/VP2/VP3 평가 + evaluate_readiness()
  - VP1 FAIL (3/5): blind_spot=0.85, field_gini=0.518
  - VP2 FAIL (2/6): gap_resolution=0.844, min_ku=3, staleness=59
  - VP3 PASS (6/6): audit=2, policy_changes=2, closed_loop=1
  - D-47에 따라 보완 Phase 삽입 필요
