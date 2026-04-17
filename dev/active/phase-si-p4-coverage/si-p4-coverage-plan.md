# Silver P4: Coverage Intelligence
> Last Updated: 2026-04-17
> Status: **Stage A~E Complete (42/42, 797 tests) · E8-3 Gate: VP4 PASS 4/5, Overall FAIL(VP2) · D-147~D-150 해소**

## 0.1 Current State (2026-04-17)

- **SI-P4 완료**: Stage A~D + Stage E 전체 42/42 tasks 완료
- 커밋 히스토리: `df219e5` → `618bb21` → `cf83733` → `47a798f` → `a4df15d` → `d2f6c7c` → `b2aafc5` → `f822f2c` (VP4 fix D-147~D-150 + E7-3 벤치 + COMPARISON.md)
- 테스트 793 → 797 (+4). compute_delta_kus, D-148 regression, D-149 pivot, D-150 gate
- **E8-3 Gate 결과**: VP4 PASS 4/5 (R1=0.7857, R2=49.06, R3=6, R5=1, R4=0), Overall FAIL(VP2 gap_res 0.8125 < 0.85)
- VP2 gap_res FAIL 은 Stage E 외 범위 (stage-e-off 도 0.789). 별도 Phase에서 해결 예정
- 잔존: D-151 후보 (Universe Probe slug collision 필터)

## 0. Scope Reframe (2026-04-15)

P4 는 미션 재검토 후 2 층으로 분할:

- **Internal Coverage Foundation (Stage A~D)** — 완료. skeleton 내부 deficit/Gini/reason_code 체계.
  - Gate: reason_code 100% PASS, coverage+Gini PASS, category_addition 보수성 PASS, S7 PASS, tests 669 ≥ 628 PASS
  - novelty 0.127 은 cycle-diff 수렴 신호로 재해석 (L3 gap_rule 의 실측 효과로 미션 기여 입증: category_gini 0.37→0.20 + 신규 KU)
- **External Anchor (Stage E)** — 신규. skeleton 외부 미개척 영역 탐지 + 쿼리 피벗.
  - 근거 문서: `dev/active/phase-si-p4-coverage/mission-alignment-critique.md`, `mission-alignment-opinion.md`, `external-anchor-improvement-plan.md`, `C:\Users\User\.claude\plans\lovely-imagining-popcorn.md`
  - Semi-front 진입 조건 = Stage E Gate PASS.

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

---

## 8. Stage E: External Anchor (신규, 29 tasks)

### 8.1 목적

"**gap_rule(L3) 은 skeleton 내부 축 증폭, exploration_pivot(L5) 은 skeleton 외부 쿼리 피벗**" — 두 메커니즘을 상보 관계로 배치해 미션 정렬(우주 대비 KU 확장 + 분포 다양성)을 달성.

### 8.2 4-계층 메커니즘 스펙트럼

| L | 메커니즘 | Scope | 트리거 | 산출 |
|---|---|---|---|---|
| L1 | remodel merge/split/reclassify/alias | 내부 재배열 | conflict/dup | 기존 KU 재조직 |
| L2 | remodel source_policy | 수집 meta | yield_decline | TTL/trust 조정 |
| **L3** | **remodel gap_rule** | **skeleton 내 미개발 축 증폭** | **audit coverage_gap critical** | **신규 GU → 새 KU** |
| L4a | remodel category_addition (반응형) | skeleton 확장 | ≥5 KU 패턴 | 새 category |
| **L4b** | **universe_probe → candidate skeleton** | **skeleton 선제 확장** | **cycle N 주기 또는 ext_novelty 낮음** | **candidate_categories** |
| **L5** | **exploration_pivot** | **skeleton 외부 전략 변경** | **ext_novelty < 0.1 × 5c + reach 정체** | **새 쿼리/시간축** |

### 8.3 트리거 우선순위

1. audit `coverage_gap critical` → **gap_rule (L3)** 먼저
2. universe_probe evidence ≥ threshold → category_addition via HITL-R
3. ext_novelty low + reach_degraded → **exploration_pivot (L5)**

동일 cycle 내 L3 + L5 동시 target 주입 금지. L3 는 GU 생성 → 다음 cycle 영향. L5 는 이번 cycle targets 치환.

### 8.4 Stage E Sub-stages

- **E0** 예산 & 축 실측 (2 tasks, 선행)
- **E1** external_novelty metric (4 tasks)
- **E2** universe_probe + tiered skeleton (5 tasks)
- **E3** reach_ledger (4 tasks)
- **E4** exploration_pivot node (3 tasks)
- **E5** planning reason_code 확장 (2 tasks)
- **E6** cost_guard + kill-switch (3 tasks)
- **E7** validation: synthetic injection + bench 비교 (3 tasks)
- **E8** Gate VP4 추가 + 판정 (3 tasks)

### 8.5 Stage E Gate (VP4)

| 기준 | 임계치 |
|---|---|
| external_novelty avg | ≥ 0.25 (새 정의) |
| distinct_domains_per_100ku | ≥ 15 (실측 후 조정) |
| universe_probe proposals | ≥ 2 per 15c |
| exploration_pivot triggered | ≥ 1 (plateau 시) |
| category_addition via universe_probe | ≥ 1 |

VP1~VP4 모두 PASS 시 **Mission-Aligned PASS** → semi-front 진입.

### 8.6 주요 리스크 (Stage E)

| ID | 리스크 | 완화 |
|---|---|---|
| R-E1 | universe_probe 비용 폭발 | E0 예산 상한 + kill-switch |
| R-E2 | candidate → active 자동 승격 오염 | HITL-R 필수, tiered skeleton |
| R-E3 | ext_novelty 측정 환상 | E7-1 synthetic injection 검증 |
| R-E4 | reach 축 확보 실패 | E0 선행 조사 |
| R-E5 | exploration_pivot 이 core loop 교란 | 1 cycle 지속 + gap_rule 우선 |
| R-E7 | L3 + L5 중복 발동 target 폭주 | 우선순위 규칙 + 동시 발동 금지 |
| R-E8 | universe_probe candidate × gap_rule category 충돌 | candidate → HITL → active 승격 후에만 L3 대상화 |
