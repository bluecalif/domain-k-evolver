# Phase 4: Self-Governing Evolver — Tasks
> Last Updated: 2026-03-07
> Status: In Progress (3/11)

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A: Outer Loop Audit | 3 | 0 | 2 | 1 | 3/3 |
| B: Policy Evolution | 3 | 0 | 2 | 1 | 0/3 |
| C: Strategic Self-Tuning | 3 | 0 | 2 | 1 | 0/3 |
| D: Evolver Readiness Gate | 2 | 0 | 1 | 1 | 0/2 |
| **합계** | **11** | **0** | **7** | **4** | **3/11** |

---

## Stage A: Outer Loop Audit

> Gate: Audit 노드가 5-cycle 주기로 자동 실행, AuditReport 생성 확인 ✅

- [x] **4.1** Executive Audit 프레임워크 구현 `[L]`
  - `src/nodes/audit.py` 신규 — run_audit() + 4개 분석 함수
  - AuditReport 타입: `src/state.py` (AuditFinding, PolicyPatch, AuditReport)
  - `src/config.py` — audit_interval 파라미터 (기본 5, 0=비활성)
  - `src/orchestrator.py` — _maybe_run_audit() + audit_reports + audit_history
  - 테스트 23개 (audit 단독) + 3개 (orchestrator 통합) = 26개 신규
  - 전체 327 tests passed

- [x] **4.2** 다축 교차 커버리지 진단 `[M]`
  - `_analyze_cross_axis_coverage()`: Shannon entropy 균등도 + 최소 KU 진단
  - category × geography 교차 blind_spot_ratio 계산
  - F-COV-01 (axis_imbalance), F-COV-GEO (blind spot), F-COV-{cat} (coverage_gap)

- [x] **4.3** KU Yield/Cost 효율 분석 `[M]`
  - `_analyze_yield_cost()`: cycle별 yield 계산 + 후반 체감 감지
  - `_analyze_quality_trends()`: confidence 하락, multi_evidence 정체
  - F-YIELD-01 (yield_decline), F-QUAL-01/02 (quality_issue)

---

## Stage B: Policy Evolution

> Gate: AuditReport.policy_patches → policies.json 자동 반영 확인

- [ ] **4.4** Policy 스키마 + 버전 관리 `[M]`
  - `schemas/policy.json` 신규 생성
  - policies.version 필드 + change_history 배열
  - 정책 변경 전/후 diff 로깅

- [ ] **4.5** Audit → Policy 자동 수정 경로 `[L]`
  - policy_patches 파싱 + policies.json 반영
  - 수정 가능 정책: TTL, min_sources, credibility_priors, cross_validation
  - Safety: 한 Audit당 최대 3 필드 변경
  - Rollback: 변경 후 1 cycle 성능 악화 → 자동 복원

- [ ] **4.6** Source Credibility 학습 `[M]`
  - EU source_type별 conflict/stale 기여 추적
  - credibility_priors 자동 조정 (guardrail 범위 내)

---

## Stage C: Strategic Self-Tuning

> Gate: threshold 또는 explore/exploit 비율이 자동 변경된 cycle ≥ 1

- [ ] **4.7** Threshold 적응 메커니즘 `[L]`
  - 대상: C6 threshold, guard limits, convergence conditions
  - 방법: 최근 N cycle 이동 평균 + 표준편차 기반
  - Guardrail: hard min/max 범위 제한

- [ ] **4.8** Explore/Exploit 비율 학습 `[M]`
  - explore/exploit별 KU yield 추적
  - 수확 체감 감지 → exploit 증가
  - 새 axis gap 발견 → explore 증가

- [ ] **4.9** Cost-Aware Budget 관리 `[M]`
  - cycle당 LLM call/token budget 설정
  - 초과 시 graceful degradation
  - KU/cost 효율 추적

---

## Stage D: Evolver Readiness Gate (필수 체크포인트)

> Gate: 3대 관점 전체 PASS → Phase X = Phase 5 확정

- [ ] **4.10** Readiness 벤치마크 실행 `[L]`
  - japan-travel 15 Cycle 재실행 (Phase 4 전체 기능 포함)
  - Audit 최소 2회 + Policy 수정 최소 1회 자동 발생 확인
  - 결과 데이터 수집 + 분석 보고서

- [ ] **4.11** 3-Viewpoint Readiness 판정 `[M]`
  - VP1: Expansion with Variability (Shannon entropy, blind_spot, entity discovery)
  - VP2: Completeness (gap_resolution ≥ 0.85, min KU/category ≥ 5, Health ≥ B)
  - VP3: Self-Governance (audit ≥ 2, policy change ≥ 1, closed loop ≥ 1)
  - 판정 결과:
    - 3/3 PASS → Phase X = Phase 5 확정
    - FAIL → 실패 관점별 보완 Phase 5 자동 설계 → Phase X = Phase 6
