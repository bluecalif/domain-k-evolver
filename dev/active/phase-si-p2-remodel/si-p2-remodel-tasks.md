# Silver P2: Outer-Loop Remodel — Tasks
> Last Updated: 2026-04-12
> Status: 구현 완료 (14/14), Gate 대기

## Summary

| Stage | Tasks | Done | Status |
|-------|-------|------|--------|
| A. Remodel node + schema | 4 | 4/4 | ✅ 완료 |
| B. Graph/orchestrator 통합 | 4 | 4/4 | ✅ 완료 |
| C. 검증 | 6 | 6/6 | ✅ 완료 |
| **합계** | **14** | **14/14** | ✅ 구현 완료 |

**Size 분포**: S: 5 / M: 8 / L: 1

---

## Phase Gate Process (필수 순서)

> 각 Phase 를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — `bench/silver/japan-travel/p2-{date}-remodel/` trial 실행. 합성 시나리오 기반 (entity 중복률 30%+ 주입 → 10 cycle run → remodel 발동 확인)
2. **결과 자가평가** — 정량 기준 (remodel report schema validate, rollback diff=∅, 중복 탐지, S7 trigger) + blocking scenario 확인
3. **Debug 루프** — bench 에서 발견된 이슈는 gate 통과 전 fix, `debug-history.md` 기록
4. **dev-docs 반영** — Phase Gate Checklist 체크, E2E Bench Results 실측값, plan.md Status 업데이트
5. **Gate 판정 commit** — `[si-p2] Gate PASS/FAIL: {근거}` 로 기록

## Phase Gate Checklist

- [ ] Remodel report 가 `remodel_report.schema.json` validate
- [ ] 합성 시나리오: entity 중복률 30%+ → remodel merge proposal 생성
- [ ] HITL-R 승인 → 다음 cycle skeleton/state 에 실제 변경 반영
- [ ] Rollback: 거부 시 state diff = ∅
- [ ] S7 scenario (trigger 부분) pass — 저novelty 5 cycle → audit → remodel 제안
- [ ] 테스트 수 ≥ P1(544) + 15 = 559 (현재 608 기준 → ≥ 623)
- [ ] P3 Post-Gate deferred verification (V-A1, V-B3, V-B3a, V-C56) 동시 확인

## E2E Bench Results (Phase 종료 시 기록)

> Stage C 완료 후 실측값을 아래 테이블에 채움. Gate 판정의 정량 근거.

### Trial: `p2-{YYYYMMDD}-remodel`

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Trial path | `bench/silver/japan-travel/p2-*-remodel/` | — | — |
| Cycles run | ≥ 10 (remodel trigger = cycle % 10) | — | — |
| Remodel report schema | validate pass | — | — |
| Merge proposal 생성 | 중복률 30%+ → merge 제안 | — | — |
| HITL-R 승인 반영 | skeleton 실제 변경 | — | — |
| Rollback state diff | = ∅ | — | — |
| S7 trigger 경로 | 저novelty → audit → remodel | — | — |
| phase snapshot | `state/phase_{N}/` 존재 | — | — |
| Total tests | ≥ 623 | — | — |

**Gate 판정**: — (미실행)

---

### P3 Post-Gate Deferred Verification (동시 확인)

> P3 Gate 이후 추가된 개선사항 (Curated preferred_sources, robots 사전 필터링)의 E2E 효과를 P2 trial에서 동시 검증.

| ID | 검증 항목 | 예상 효과 | 측정 방법 |
|----|-----------|-----------|-----------|
| V-A1 | Curated preferred_sources 실제 기여 | curated provider 결과 ≥ 1건/cycle | trajectory provenance `provider_id="curated"` 카운트 |
| V-B3 | robots 사전 필터링 효과 | fetch 성공률 ≥ 85% | FetchResult failure_reason 분포 비교 |
| V-B3a | 차단 URL 대체 선택 | fetch_top_n 슬롯 = 허용 URL | fetch_many 인자 URL 수 확인 |
| V-C56 | Option C 필요성 재검증 | 차단률 추이 | 전체 fetch 대비 차단 비율 모니터링 |

---

## Stage A: Remodel node + schema

- [x] **P2-A1** `src/nodes/remodel.py` 신규 `[L]`
  - 입력: audit 결과 (4 분석함수 출력) + 현 state
  - 출력: `RemodelReport` (proposals 리스트)
  - Phase 4 `audit.py`의 4 분석함수 결과를 **소비만**, 중복 분석 금지
  - proposal types: merge / split / reclassify / alias_canonicalize / source_policy / gap_rule
  - 함수: `run_remodel()`, `remodel_node()`, `_propose_merges/splits/reclassify/from_audit_findings`

- [x] **P2-A2** `schemas/remodel_report.schema.json` 필드 정의 `[M]`
  - report_id, created_at, source_audit_id, proposals[], rollback_payload, approval
  - proposal: type (6종 enum), rationale, target_entities, params, expected_delta
  - approval: status (pending/approved/rejected), actor, at
  - JSON Schema Draft 2020-12, $defs 사용

- [x] **P2-A3** `EvolverState.phase_number: int` + `remodel_report: dict | None` 필드 추가 `[S]`
  - `src/state.py` — phase_number, remodel_report 추가
  - `src/utils/state_io.py` — load_state 초기화 (phase_number=0, remodel_report=None)

- [x] **P2-A4** `state/phase_{N}/` 스냅샷 저장 로직 `[M]`
  - `src/utils/state_io.py:snapshot_phase()` — phase bump 시 state/phase_{N}/ 로 복사
  - 기존 `snapshot_state()` 패턴과 동일, write guard 포함

---

## Stage B: Graph/orchestrator 통합

- [x] **P2-B1** `graph.py` remodel 경로 추가 `[M]`
  - remodel 노드 등록 (Orchestrator 관리, inner-loop edge 없음)
  - remodel_node import 추가, docstring 에 Remodel Flow 문서화
  - audit → remodel 트리거는 Orchestrator._maybe_run_remodel 에서 관리

- [x] **P2-B2** `hitl_gate.py` HITL-R 핸들러 완성 `[M]`
  - _build_gate_payload("R"): proposals_summary, report_id, proposal_count 표시
  - _handle_response: approve → approval.status="approved", reject → approval.status="rejected"
  - 자동 승인 (response=None) 지원

- [x] **P2-B3** `orchestrator.py` phase transition 핸들러 `[M]`
  - _maybe_run_remodel: audit has_critical + cycle % interval → remodel 트리거
  - _apply_remodel_proposals: merge/split/reclassify KU entity_key 변경
  - phase bump (+1) + snapshot_phase + phase_history 기록

- [x] **P2-B4** Rejection/rollback path `[M]`
  - _hitl_response = {"action": "reject"} → state 무변경 (phase_number, entity_key 불변)
  - remodel_report.approval.status = "rejected" 기록

---

## Stage C: 검증

- [x] **P2-C1** merge 시나리오 테스트 `[S]`
  - TestMergeProposal (3 tests) + TestPhaseTransition::test_merge (Stage B)

- [x] **P2-C2** split 시나리오 테스트 `[S]`
  - TestSplitProposal (2 tests) + TestPhaseTransition::test_split (Stage B)

- [x] **P2-C3** reclassify 시나리오 테스트 `[S]`
  - TestReclassifyProposal (2 tests) + TestPhaseTransition::test_reclassify (Stage B)

- [x] **P2-C4** rollback 시나리오 테스트 `[S]`
  - TestRollback (2 tests) — rejection → state diff = ∅, rollback_payload 검증

- [x] **P2-C5** S7 trigger 경로 테스트 `[M]`
  - TestS7TriggerPath (3 tests) — plateau→audit→remodel, critical 없으면 스킵, 전체 경로

- [x] **P2-C6** schema 양방향 테스트 `[S]`
  - TestSchemaValidation (5 tests) — valid pass, missing field fail, invalid type/status fail, run_remodel 출력 validate
