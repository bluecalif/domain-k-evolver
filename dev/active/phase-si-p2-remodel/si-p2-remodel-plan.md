# Silver P2: Outer-Loop Remodel 완결
> Last Updated: 2026-04-12
> Status: 구현 완료 (14/14), Gate 대기

## 1. Summary (개요)

**목적**: Phase 4에서 구현한 audit 결과를 **구조 변경 제안** (merge/split/reclassify/policy/gap rule)으로 compile하고, HITL-R 승인 게이트를 거쳐 실제 skeleton/state에 반영하는 remodel 경로를 완성한다.

**범위**: remodel 노드 신규 + remodel_report 스키마 + graph/orchestrator 통합 + phase transition 저장 + rollback 경로

**예상 결과물**:
- `src/nodes/remodel.py` — audit 결과를 소비하여 RemodelReport 생성
- `schemas/remodel_report.schema.json` — 제안/승인/rollback 필드
- graph.py에 remodel→HITL-R→phase_bump 경로 추가
- phase transition 스냅샷 저장 (`state/phase_{N}/`)
- rollback 경로 (승인 거부 시 state 무변경 보장)
- 14 tasks, 테스트 ≥ 559 (P1 544 + 15)

**단일 진실 소스**: `docs/silver-masterplan-v2.md` §4 P2, `docs/silver-implementation-tasks.md` §6

---

## 2. Current State (현재 상태)

### 이전 Phase에서 넘어온 것
- **Bronze Phase 4**: `audit.py`에 4개 분석함수 구현 완료 (`_analyze_cross_axis_coverage`, `_analyze_yield_cost`, `_analyze_quality_trends`, `run_audit`)
- **Silver P0**: HITL-R stub 노드 등록 (`graph.py` line 167: `hitl_r`), `hitl_gate.py`에 gate="R" stub (description만, 로직 미구현)
- **Silver P1**: `entity_resolver.py` 완료 — alias/is_a/canonicalize. remodel의 merge/reclassify 제안 품질의 전제
- **Silver P3**: `collect.py` 3단계 분리 + provider 플러그인 완료 — P2와 직접 의존 없으나 P4가 P2+P3 모두 필요

### 현재 자산
| 항목 | 상태 |
|------|------|
| `audit.py` 4 분석함수 | ✅ 구현 완료 (Bronze P4) |
| `hitl_gate.py` HITL-R | ✅ 실구현 완료 (P2-B2) — approve/reject 처리, proposals_summary 표시 |
| `graph.py` remodel 노드 | ✅ 등록 완료 (P2-B1) — Orchestrator 관리 |
| `EvolverState.phase_history` | ✅ 필드 선언됨 (`state.py:224`) |
| `entity_resolver.py` | ✅ 완료 (P1) |
| `remodel.py` | ✅ 구현 완료 (P2-A1) |
| `remodel_report.schema.json` | ✅ 구현 완료 (P2-A2) |
| `EvolverState.phase_number` | ✅ 추가 (P2-A3) |
| `snapshot_phase()` | ✅ 구현 완료 (P2-A4) |
| `orchestrator.py` remodel | ✅ 구현 완료 (P2-B3/B4) — _maybe_run_remodel, _apply_remodel_proposals |
| 테스트 | 645 tests (605 + 40 P2 신규) |

---

## 3. Target State (목표 상태)

P2 완료 후:
1. **remodel 노드**: audit의 4 분석함수 결과를 입력받아 merge/split/reclassify/alias_canonicalize/source_policy/gap_rule 중 해당하는 제안을 `RemodelReport`로 생성
2. **graph 경로**: `critique → audit → remodel → hitl_r → (approve) phase_bump | (reject) plan_modify` 완성. 조건: `cycle > 0 and cycle % 10 == 0 and audit.has_critical`
3. **HITL-R 완성**: stub → 실구현 (remodel report 내용 표시 + 승인/거부 응답 처리)
4. **phase transition**: 승인 시 skeleton/state 실제 수정 + `state/phase_{N}/` 스냅샷 보존
5. **rollback**: 거부 시 state diff = ∅ 보장
6. **S7 trigger 경로**: 저novelty 5 cycle → audit 발동 → remodel 제안 (trigger 부분만, coverage 근거는 P4)
7. **테스트 ≥ P1 544 + 15 = 559** (현재 608 기준으로는 ≥ 623)

---

## 4. Implementation Stages

### Stage A: Remodel node + schema (4 tasks)
- `remodel.py` 핵심 로직 구현
- `remodel_report.schema.json` 정의
- `EvolverState` 에 `phase_number` 추가 (phase_history는 이미 선언)
- phase 스냅샷 저장 로직

### Stage B: Graph/orchestrator 통합 (4 tasks)
- `graph.py` 에 remodel→hitl_r→phase_bump 경로 추가
- `hitl_gate.py` HITL-R stub → 실구현 승격
- `orchestrator.py` phase transition 핸들러
- rejection/rollback path

### Stage C: 검증 (6 tasks)
- merge/split/reclassify 합성 시나리오 테스트
- rollback 시나리오 테스트
- S7 trigger 경로 테스트
- schema 양방향 테스트

---

## 5. Task Breakdown

| ID | Task | Size | Stage | 의존성 |
|----|------|------|-------|--------|
| P2-A1 | `src/nodes/remodel.py` 신규 — audit 4 분석함수 결과 소비, RemodelReport 출력 | L | A | — |
| P2-A2 | `schemas/remodel_report.schema.json` 필드 정의 | M | A | — |
| P2-A3 | `EvolverState.phase_number: int` 추가 | S | A | — |
| P2-A4 | `state/phase_{N}/` 스냅샷 저장 로직 | M | A | A3 |
| P2-B1 | `graph.py` critique→audit→remodel→hitl_r→phase_bump 경로 | M | B | A1 |
| P2-B2 | `hitl_gate.py` HITL-R 핸들러 완성 (stub→실구현) | M | B | A1, A2 |
| P2-B3 | `orchestrator.py` phase transition 핸들러 | M | B | A4, B1 |
| P2-B4 | Rejection/rollback path — rejected 시 state 무변경 | M | B | B3 |
| P2-C1 | merge 시나리오 테스트 (중복률 30%+) | S | C | A1 |
| P2-C2 | split 시나리오 테스트 (상반 axis_tag 2+) | S | C | A1 |
| P2-C3 | reclassify 시나리오 테스트 | S | C | A1 |
| P2-C4 | rollback 시나리오 테스트 (state diff=∅) | S | C | B4 |
| P2-C5 | S7 trigger 경로 테스트 (저novelty 5 cycle) | M | C | B1 |
| P2-C6 | schema 양방향 테스트 (valid pass, invalid fail) | S | C | A2 |

**Size 분포**: S: 5 / M: 8 / L: 1 / XL: 0 = **14 tasks**

---

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| R3 | remodel이 state 구조를 파괴 | M | H | phase transition 저장, HITL-R 승인, rollback 경로 (P2 Gate 포함) |
| R-P2-1 | audit 분석함수 출력 형식 변경 | L | M | audit.py 현행 출력 형태를 remodel 입력으로 고정, 인터페이스 테스트 |
| R-P2-2 | remodel 제안이 P1 entity_resolver와 충돌 | L | M | merge/alias_canonicalize 제안 시 entity_resolver 호출하여 일관성 검증 |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| `remodel.py` | `audit.py` (4 분석함수 출력), `entity_resolver.py` (P1), `state_io.py` |
| `graph.py` 경로 | `remodel.py`, `hitl_gate.py` HITL-R |
| `orchestrator.py` transition | `state_io.py`, `remodel_report.schema.json` |

### 외부
| 패키지 | 용도 |
|--------|------|
| jsonschema | remodel_report 스키마 검증 (기존) |
| (추가 없음) | P2는 외부 패키지 추가 불필요 |

### Phase 의존
- **선행**: P0 ✅, P1 ✅ (alias/canonicalize가 remodel 제안 품질의 전제)
- **후행**: P4 (remodel trigger + coverage), P5 (remodel review 대시보드), P6 (전체)

---

## P2 Phase Gate

### Gate Process (필수 순서)

> 각 Phase를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — `bench/silver/japan-travel/p2-{date}-remodel/` trial 실행 (합성 시나리오: 중복률 30%+ 주입, ≥ 10 cycle run → remodel 발동 확인)
2. **결과 자가평가** — 정량 기준 + S7 blocking scenario 확인
3. **Debug 루프** — bench 발견 이슈 fix → `debug-history.md` 기록
4. **dev-docs 반영** — Gate Checklist 체크, E2E Results 실측값, plan Status 업데이트
5. **Gate 판정 commit** — `[si-p2] Gate PASS/FAIL: {근거}`

### Gate 정량 기준

| 항목 | 기준 |
|------|------|
| Remodel report가 schema validate | pass |
| 승인된 remodel이 다음 cycle skeleton/state에 실제 반영 | pass |
| Rollback 경로가 승인 전 state로 완전 복귀 (state diff=∅) | pass |
| 합성 시나리오: entity 중복률 30%+ → remodel 탐지·제안 | pass |
| S7 scenario (trigger 부분) pass | pass |
| phase snapshot (`state/phase_{N}/`) 존재 | pass |
| P3 Post-Gate deferred items (V-A1, V-B3, V-B3a, V-C56) 동시 검증 | pass |
| 테스트 수 ≥ P1(544) + 15 = 559 | 현재 608 기준 → ≥ 623 |
