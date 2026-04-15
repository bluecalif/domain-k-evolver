# Silver P4: Coverage Intelligence
> Last Updated: 2026-04-15
> Status: **Planning**

## 1. Summary (개요)

**목적**: plan 노드가 novelty/overlap/deficit **근거**로 target 을 선택하고, critique 가 metric 기반 처방을 내리며, Gini 불균형과 카테고리 부족을 **보수적으로** 감지·대응하는 Coverage Intelligence 체계를 구축한다.

**범위**:
- Metrics primitives (novelty, coverage_map, Gini tracking)
- Plan reason_code 체계 (모든 target 에 근거 코드 부여)
- Critique metric 기반 처방 (overlap/deficit → machine-readable rule)
- Plateau detector novelty 확장
- **Gini criteria → coverage 반영** (D-134 이행): category/field Gini 를 coverage 평가에 통합
- **Smart category addition**: 보수적 카테고리 추가 제안 (LLM 의미 판단, 최소 증거 임계치, HITL 승인)

**예상 결과물**:
- `src/utils/novelty.py` [NEW] — Jaccard / token / entity overlap
- `src/utils/coverage_map.py` [NEW] — axis × entity 그리드, deficit score, **Gini tracking**
- `src/nodes/plan.py` — reason_code 필드 추가
- `src/nodes/critique.py` — metric 기반 machine-readable 처방
- `src/utils/plateau_detector.py` — novelty 기반 trigger 확장
- `src/nodes/remodel.py` — **category_addition proposal** type 추가
- 15+ tasks, 테스트 ≥ 613 + 15 = 628

**단일 진실 소스**: `docs/silver-masterplan-v2.md` §4 P4, `docs/silver-implementation-tasks.md` §8

---

## 2. Current State (현재 상태)

### 이전 Phase 에서 넘어온 것
- **Bronze Phase 5**: `plateau_detector.py` 구현 (growth-rate 휴리스틱, conflict_rate 복합 조건)
- **Silver P0**: Metrics emit, `EvolverState` 에 `coverage_map: dict`, `novelty_history: list[float]` 필드 선언 (값 미채움)
- **Silver P1**: Entity Resolution 완료 — alias/canonicalize 정합성. category 구조 기반
- **Silver P2**: Remodel 완성 — Smart Criteria (D-132), merge min_overlap (D-133), **Gini criteria P4 연기 (D-134)**
- **Silver P3R**: Snippet-First Collect — provenance 필드 확정 (`provider`/`domain`/`retrieved_at`/`trust_tier`)
- **Gap-Res**: gap_resolution_rate 0.99 달성 (D-129) — target_count cap 없음

### 현재 자산
| 항목 | 상태 |
|------|------|
| `plateau_detector.py` | ✅ KU/GU 기반 plateau (Bronze P3) |
| `EvolverState.coverage_map` | 필드 선언, 값 미채움 |
| `EvolverState.novelty_history` | 필드 선언, 값 미채움 |
| `readiness_gate.py` `_gini_coefficient` | ✅ Gini 계산 함수 존재 (재사용 가능) |
| `critique.py` | ✅ 6대 실패모드 분석 + 처방 (자유 텍스트) |
| `plan.py` | deficit 축 기반 explore 로직 존재 (reason_code 미구현) |
| `remodel.py` | ✅ merge/split/reclassify/alias/source_policy/gap_rule 6종 |
| 테스트 | 613 passed |

---

## 3. Target State (목표 상태)

P4 완료 후:
1. **novelty.py**: cycle-to-cycle 신규성 측정 (Jaccard/token/entity). `novelty_history` 자동 기록
2. **coverage_map.py**: axis × bucket 그리드 + deficit score + **Gini 통합** (category_gini, field_gini 를 coverage 평가 시 함께 계산)
3. **plan.py reason_code**: 모든 target 에 `deficit:category=food`, `plateau:novelty<0.1`, `gini:category_imbalance`, `remodel:pending`, `seed:initial` 등 reason_code 부여
4. **critique.py machine-readable**: `overlap > 0.8` → jump, `coverage_deficit > 0.5` → explore 등 규칙 표현
5. **plateau_detector 확장**: novelty < 0.1 for 5 cycles → plateau trigger (기존 KU/GU 정체 + novelty 기반 통합)
6. **Gini → coverage 반영**: category/field Gini 가 coverage_map deficit 산정에 영향. Gini 불균형 → 탐색 우선순위 조정
7. **Smart category addition**: remodel 에 `category_addition` proposal 추가. **보수적 조건**:
   - ≥ 5 KU 가 기존 카테고리에 속하지 않는 패턴 참조
   - LLM 의미 판단으로 후보 생성 (단순 문자열 매칭 금지)
   - 사이클당 최대 1개 카테고리 추가 제안
   - HITL-R 승인 필수
8. **S7 full scenario**: plateau → audit → remodel → category/coverage 재편 전체 경로
9. **테스트 ≥ 628** (613 + 15)

---

## 4. Implementation Stages

### Stage A: Metrics Primitives + Gini 통합 (5 tasks)
- `novelty.py` 핵심 구현
- `coverage_map.py` + Gini tracking 통합
- `EvolverState` 필드 채움 로직
- plateau_detector novelty 확장

### Stage B: Plan/Critique 통합 (4 tasks)
- `plan.py` reason_code 체계
- `critique.py` machine-readable 처방
- remodel_pending → plan 영향
- Gini 불균형 → plan 우선순위

### Stage C: Smart Category Addition (3 tasks)
- `remodel.py` category_addition proposal type
- 보수적 트리거 조건 (evidence threshold + LLM 판단)
- HITL-R 연동 + skeleton 반영

### Stage D: 검증 (5 tasks)
- novelty 단위 테스트
- coverage_map + Gini 통합 테스트
- reason_code 생성 테스트
- S7 full scenario (plateau → audit → remodel → category)
- E2E bench trial

---

## 5. Task Breakdown

| ID | Task | Size | Stage | 의존성 |
|----|------|------|-------|--------|
| P4-A1 | `src/utils/novelty.py` 신규 — Jaccard/token/entity overlap | M | A | — |
| P4-A2 | `src/utils/coverage_map.py` 신규 — axis×bucket deficit + Gini tracking | M | A | — |
| P4-A3 | `EvolverState` novelty_history + coverage_map 채움 로직 (`orchestrator.py`) | S | A | A1, A2 |
| P4-A4 | `plateau_detector.py` novelty 확장 — novelty < 0.1 × 5c trigger | M | A | A1 |
| P4-A5 | Gini → deficit 반영 — coverage_map 산정 시 category/field Gini 가중 | M | A | A2 |
| P4-B1 | `plan.py` reason_code enum + 모든 target 에 코드 부여 | M | B | A2, A5 |
| P4-B2 | `critique.py` machine-readable 처방 규칙 (overlap/deficit/gini) | M | B | A2 |
| P4-B3 | `remodel_pending` → plan reason_code 영향 | S | B | B1 |
| P4-B4 | Gini 불균형 → plan target 우선순위 조정 | S | B | A5, B1 |
| P4-C1 | `remodel.py` category_addition proposal type 추가 | L | C | A2 |
| P4-C2 | Category addition 보수적 트리거 (≥5 KU + LLM 의미 판단) | M | C | C1 |
| P4-C3 | HITL-R category_addition 연동 + skeleton 반영 | M | C | C1 |
| P4-D1 | novelty 단위 테스트 (0/1/부분 overlap) | S | D | A1 |
| P4-D2 | coverage_map + Gini 통합 테스트 | S | D | A2, A5 |
| P4-D3 | reason_code 생성 테스트 (모든 enum) | S | D | B1 |
| P4-D4 | S7 full scenario (plateau → audit → remodel → category) | M | D | C3 |
| P4-D5 | category_addition 보수적 조건 테스트 (미달 시 미제안 확인) | S | D | C2 |

**Size 분포**: S: 7 / M: 8 / L: 1 / XL: 0 = **17 tasks**

---

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| R-P4-1 | Category addition 이 공격적 → skeleton 오염 | M | H | ≥5 KU 임계치 + 사이클당 1개 제한 + HITL 승인 필수 |
| R-P4-2 | Gini 가중이 deficit 왜곡 | L | M | Gini 기여도는 가중 계수로 조절 (기본 0.3), 별도 테스트 |
| R-P4-3 | novelty 계산이 비용 과다 (large state) | L | L | Jaccard 최적화 (set 연산), 필요 시 sampling |
| R-P4-4 | reason_code 100% 미달 | M | M | plan.py 에 default reason_code fallback (`seed:initial`) |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| `novelty.py` | `EvolverState` (knowledge_units, gap_map) |
| `coverage_map.py` | `readiness_gate.py:_gini_coefficient` (재사용), skeleton categories/axes |
| `plan.py` reason_code | `coverage_map.py`, `novelty.py` |
| `critique.py` 처방 | `coverage_map.py`, `novelty.py` |
| `remodel.py` category_add | `coverage_map.py`, LLM adapter |
| `plateau_detector.py` | `novelty.py` |

### 외부
| 패키지 | 용도 |
|--------|------|
| (추가 없음) | P4 는 외부 패키지 추가 불필요 |

### Phase 의존
- **선행**: P0 ✅, P1 ✅, P2 ✅ (remodel trigger), P3R ✅ (provenance)
- **후행**: P5 (telemetry — novelty/coverage 데이터 노출), P6 (multi-domain)

---

## P4 Phase Gate

### Gate Process (필수 순서)

1. **합성 E2E 테스트** — novelty/coverage/reason_code/category_addition 전체 경로
2. **실 벤치 trial** — 15c real API, before/after metrics (novelty 평균, coverage 분포, Gini)
3. **결과 자가평가** — 정량 기준 + S7 scenario 확인
4. **Debug 루프** — 이슈 fix → debug-history.md
5. **Gate 판정 commit** — `[si-p4] Gate PASS/FAIL: {근거}`

### Gate 정량 기준

| 항목 | 기준 |
|------|------|
| plan output 모든 target 에 reason_code 부여 | 100% |
| 10 cycle 연속 run 에서 novelty 평균 | ≥ 0.25 |
| 인위적 plateau (동일 seed 5 cycle) → audit/remodel trigger | 발동 확인 |
| S7 full scenario pass | pass |
| coverage_map deficit 계산 + Gini 통합 | 테스트 pass |
| category_addition 보수적 조건 (미달 시 미제안) | 테스트 pass |
| 테스트 수 | ≥ 628 (613 + 15) |
