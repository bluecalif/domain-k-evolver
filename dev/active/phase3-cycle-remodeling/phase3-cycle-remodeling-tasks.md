# Phase 3: Cycle Quality Remodeling — Tasks
> Created: 2026-03-06
> Status: Planning (0/9)

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A: Semantic Conflict Detection | 3 | 0 | 2 | 1 | 0/3 |
| B: Dispute Resolution | 3 | 0 | 2 | 1 | 0/3 |
| C: 수렴 개선 + 재검증 | 3 | 1 | 1 | 1 | 0/3 |
| **합계** | **9** | **1** | **5** | **3** | **0/9** |

---

## Stage A: Semantic Conflict Detection (R1)

> Gate: _detect_conflict FP rate < 30%

- [ ] **3.1** `_detect_conflict()` LLM semantic 비교로 교체 `[L]`
  - `src/nodes/integrate.py` — `_detect_conflict()` 함수 리팩터
  - LLM 프롬프트: "두 값이 의미적으로 충돌하는가?" 판정
  - hybrid 접근 고려: 동일 값 → skip, 숫자/날짜 → rule-based, 텍스트 → LLM
  - 기존 테스트 호환성 유지 (Mock LLM)

- [ ] **3.2** 충돌 판정 테스트 + FP rate 측정 `[M]`
  - disputed KU 54개 기반 gold standard 생성
  - 단위 테스트: true positive, false positive, edge case
  - FP rate 측정 스크립트

- [ ] **3.3** 10 Cycle 재실행 (Stage A 검증) `[M]`
  - `scripts/run_bench.py --cycles 10`
  - Phase 2 baseline 대비 active KU 성장률 비교
  - FP rate 변화 측정

---

## Stage B: Dispute Resolution (R2~R4)

> Gate: disputed→active 전환 경로 작동 확인

- [ ] **3.4** dispute resolution mechanism 설계 + 구현 `[L]`
  - 해소 전략 선택 (D-42): 다수결/최신우선/출처신뢰도
  - `src/nodes/integrate.py` 또는 신규 모듈
  - disputed KU → active 전환 함수

- [ ] **3.5** disputed→active 전환 경로 `[M]`
  - 자동 해소 조건: N개 이상 EU가 동일 주장 뒷받침
  - 수동 해소: HITL gate에서 disputed 목록 제시
  - State 업데이트 로직

- [ ] **3.6** critique 노드 dispute resolution workflow `[M]`
  - `src/nodes/critique.py`에 disputed KU 평가 섹션 추가
  - 해소 가능한 disputed KU → plan_modify에 처방 전달

---

## Stage C: 수렴 개선 + 재검증 (R5~R6)

> Gate: 10 Cycle 완주 시 Health Grade B 이상

- [ ] **3.7** 수렴 조건 C6: conflict_rate 상한 `[S]`
  - `src/nodes/critique.py` — `_check_convergence()`에 C6 조건 추가
  - conflict_rate > threshold → 경고 또는 mode 전환

- [ ] **3.8** early stopping 개선 `[M]`
  - plateau + conflict_rate 복합 조건
  - `src/utils/plateau_detector.py` 확장 또는 별도 모듈

- [ ] **3.9** 최종 10 Cycle + 개선 효과 보고 `[L]`
  - 전체 개선사항 반영 후 10 Cycle 실행
  - Phase 2 baseline 대비 정량 비교 보고서
  - Health Grade 측정
