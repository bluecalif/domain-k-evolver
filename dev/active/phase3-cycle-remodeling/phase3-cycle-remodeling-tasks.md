# Phase 3: Cycle Quality Remodeling — Tasks
> Last Updated: 2026-03-06
> Status: Complete (9/9)

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A: Semantic Conflict Detection | 3 | 0 | 2 | 1 | 3/3 |
| B: Dispute Resolution | 3 | 0 | 2 | 1 | 3/3 |
| C: 수렴 개선 + 재검증 | 3 | 1 | 1 | 1 | 3/3 |
| **합계** | **9** | **1** | **5** | **3** | **9/9** |

---

## Stage A: Semantic Conflict Detection (R1)

> Gate: _detect_conflict FP rate < 30% ✅ (conflict_rate 0.234)

- [x] **3.1** `_detect_conflict()` LLM semantic 비교로 교체 `[L]` → `6e27a65`
  - hybrid 접근 구현: 동일값→skip, conditions→split, 값차이→LLM semantic
  - LLM verdict: update/equivalent→충돌아님, conflict→hold
  - LLM 없으면 결정론적 fallback, 실패 시 hold fallback
  - 신규 테스트 6개, 전체 278 passed
  - D-41: hybrid conflict detection 확정

- [x] **3.2** 충돌 판정 테스트 + FP rate 측정 `[M]` → Stage A 10 Cycle로 검증
  - Stage A 10 Cycle: disputed 54→18, conflict_rate 0.635→0.234

- [x] **3.3** 10 Cycle 재실행 (Stage A 검증) `[M]` → Stage A 결과로 Gate 통과
  - Active 31→59, Disputed 54→18, Active 성장률 0.3→3.1/cycle

---

## Stage B: Dispute Resolution (R2~R4)

> Gate: disputed→active 전환 경로 작동 확인 ✅

- [x] **3.4** dispute resolution mechanism 설계 + 구현 `[L]` → `c45b089`
  - 신규 모듈 `src/nodes/dispute_resolver.py`
  - D-42: Evidence-weighted resolution 확정
  - 전략 1: evidence ≥ 2×disputes → 자동 resolve
  - 전략 2: LLM 중재 (비율 미달 시)
  - 전략 3: 해소 불가 → keep_disputed
  - Conflict-preserving: disputes 삭제 않고 resolved로 마킹

- [x] **3.5** disputed→active 전환 경로 `[M]` → `c45b089`
  - `resolve_dispute()`: status 변경 + disputes resolution 마킹
  - `resolve_disputes()`: 전체 KU 순회 + 로그 반환

- [x] **3.6** critique 노드 dispute resolution workflow `[M]` → `c45b089`
  - critique_node에서 실패모드 분석 전에 dispute resolution 실행
  - `dispute_resolved` 처방 타입 추가 (critique + plan_modify)
  - 신규 테스트 18개, 전체 296 passed

---

## Stage C: 수렴 개선 + 재검증 (R5~R6)

> Gate: 10 Cycle 완주 시 Health Grade B 이상 ✅

- [x] **3.7** 수렴 조건 C6: conflict_rate 상한 `[S]` → `9a3c5f2`
  - `_check_convergence()`에 C6 조건 추가: conflict_rate < 0.15
  - D-43: CONFLICT_RATE_THRESHOLD = 0.15 확정

- [x] **3.8** early stopping 개선 `[M]` → `9a3c5f2`
  - PlateauDetector에 conflict_rate 추적 + is_stuck()/plateau_reason() 추가
  - stuck (plateau + high conflict) vs converged (plateau + low conflict) 분류
  - Orchestrator: plateau reason 로깅

- [x] **3.9** 최종 10 Cycle + 개선 효과 보고 `[L]` → `9a3c5f2`
  - Phase 2 → Phase 3 최종 비교:
    - Active KU: 31 → 77 (+148%)
    - Disputed KU: 54 → 0 (-100%)
    - conflict_rate: 0.635 → 0.000
    - Active 성장률: 0.3 → 4.3/cycle (14.3x)
    - LLM calls: 69 → 238
  - 전체 301 passed
