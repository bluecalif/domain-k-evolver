# SI-P7 Structural Redesign — Tasks (rebuild)

> Last Updated: 2026-04-26
> Status: In Progress (Stage A)
> 단일 진실 소스: **`docs/structural-redesign-tasks_CC.md` v2** (task 상세)
> 본 문서: 착수 순서 + checklist + L1/L2/L3 checkpoint + axis-gate 통과 기준

---

## Phase Gate Architecture (D-200 신규)

각 axis 완료 시 5c L2 smoke 통과 의무 → 통과 시 다음 axis 진입. 실패 시 axis 내부 narrowing (V-T11 토글 패턴, S2-T5~T8 한정). Phase 전체 종료 시 15c L3 통합 trial 로 공식 Gate 판정.

```
Stage A → S1 5c gate → S2-T1/T2 1c gate → Pre-Stage B
Pre-Stage B → S4-T1 1c gate → Stage B-1/B-2 (S3)
Stage B-1/B-2 (S3) → S3 5c gate → Stage B-3 (S2)
Stage B-3 (S2) → S2 5c gate → Stage B-4 (S4-T2~T4)
Stage B-4 (S4-T2~T4) → S4 5c gate → Stage C
Stage C → S5a 5c gate → Stage D
Stage D → 15c L3 통합 trial → readiness-report (silver-phase-gate-check)
```

> **Gate 필수 선행 조건 (모든 5c/15c trial 공통)**
> trial 완료 직후 → Gate 판정 전 반드시 `entity-field-matrix.json` 생성. matrix 없이 Gate 선언 불가.
> ```bash
> python scripts/analyze_trajectory.py \
>   --bench-root bench/silver/japan-travel/{trial_id} \
>   --matrix
> ```
> vacant/ku_only/gu_open 분포 확인 후 Gate 기준 적용.

---

## Stage A — 제어 루프 복구 (S1 + S2-T1/T2)

### S1 — Target / Collect 자유화 + budget 제거 (F1)

- [x] **S1-T1** `_UTILITY_ORDER`/`_RISK_ORDER` 제거, `_select_targets` 정렬 제거 (`src/nodes/plan.py`)
- [x] **S1-T2** `_select_targets` 가 open_gus 전체 반환 (cycle cap 만 적용)
- [x] **S1-T3** `mode_node` target_count 공식 → cycle cap 으로 대체 (`src/nodes/mode.py`)
- [x] **S1-T4** `collect.py` utility skip 제거 + deferred_targets 기록 (→ F1에서 반전: budget 제거로 deferred 자체 삭제)
- [x] **S1-T5** `max_search_calls_per_cycle` config (→ F1에서 반전: config 필드 제거)
- [x] **S1-T6** **F1 번복 결정**: LLM-set budget 완전 제거. `gu_queries[:3]` hard-cap으로 대체. total calls = `cycle_cap × max 3` (결정론적). 5c smoke 기 완료.
- [ ] **S1-T7** regression guard: budget key 재도입 방지 + `target_count` cap 재도입 방지 (D-129)
  - `test_plan.py`: plan output에 `"budget"` / `"stop_rules"` key 없음
  - `test_collect.py`: `_calc_execution_queue` budget-free 동작 + `gu_queries[:3]` cap 적용
- ~~**S1-T8**~~ **[DROP — F1]** `state.deferred_targets` + FIFO/LIFO 소진: budget 제거로 deferred 발생 자체 없어짐
- ~~**S1-T9**~~ **[DROP — adj_gen=0 원인은 S3/S4]** adj_gen=0 감지 → critique rx: D-56 억제(S3-T1)·balance entity(S4-T1)가 근본 원인. S1 처방은 증상 대응에 불과

### S1 Axis Gate (5c re-smoke — budget 제거 후) ✅ 조건부 PASS

```
trial: bench/silver/japan-travel/p7-rebuild-s1-smoke/  (5c real API, commit a3032b4)
결과:
- KU c5: 104 (기준 60~85 초과 — balance-N entity 원인, S4 담당) ⚠️
- target_count: c5=12 > 0  ✓
- per-GU search ≤ 3: [:3] cap 코드+테스트 검증  ✓
- VP2 completeness 6/6 (gap_res=0.88)  ✓

판정: 조건부 PASS → S2 진입 (KU 초과는 S4 known issue)
```

### S2-T1/T2 — integration_result 제어 입력화 (Step A 범위)

- [x] **S2-T1** `integration_result_dist` state 누적 + plan_modify/critique 입력 주입
  - **L1**: integrate_node dist 누적 + TestIntegrationResultDist ✓
  - **L2**: `si-p7-s2-t1-smoke` (1c gate) → `state.integration_result_dist` 확인
- [x] **S2-T2** `added_ratio<0.3×3c` + `condition_split=0×3c` → critique `rx_id=ku_stagnation:*`
  - `_detect_ku_stagnation()` + TestKuStagnation 6 cases ✓
  - reason code: `integration_added_low`, `adjacent_yield_low`

### S2-T1/T2 Gate (1c smoke) ✅ PASS

```
PASS 기준:
- state.integration_result_dist 누적 확인  ✓ (cycle/added/added_ratio/conv_rate 등 모든 필드)
- ku_stagnation_signals state field 작동 확인  ✓ (1c → [], 3c 이상 시 신호 생성 확인)
```

---

## Stage B — KU/field 품질 개선 (Pre-B: S4-T1 → B-1/B-2: S3 → B-3: S2 → B-4: S4-T2~T4)

> **Option B (P2+P3) 적용**: 측정 오염원 먼저 제거(P3) → root cause 먼저(P2) → S2 보수화 → S4 잔여

### Pre-Stage B — 측정 오염원 제거 (S4-T1)

_P3: balance-N 양산이 S2/S3 5c gate KU 신호를 오염시킴. 모든 axis 5c gate 전에 선행._

- [x] **S4-T1** virtual `balance-N` 생성 전부 제거
  - **L1**: `TestBalanceGuRegression` — gap_map 에 `balance-*` GU 0건, `_generate_balance_gus` 부재, `MIN_KU_PER_CAT` 부재 ✓ (835 passed)
  - **L2**: `si-p7-s4-t1-smoke` (1c) — `state.gap_map` 에 `balance-*` 0건 ✓ (KU 13→24, GU 35, refresh 정상)

### Pre-Stage B Gate (1c smoke) ✅ PASS

```
trial: bench/silver/japan-travel/p7-s4-t1-smoke/  (1c real API)
결과:
- gap_map 내 balance-* GU = 0  ✓
- GU ID 연속 (GU-0001~GU-0035), max_gu_id 연속성 유지  ✓
- refresh_gus 정상 동작 (0건 — stale KU 없음)  ✓
- KU: 13 → 24 (active), cycle 정상 완료  ✓
판정: PASS → Stage B-1 (S3-T1) 진입 가능
```

### Stage B-1/B-2 — adjacent rule engine root cause (S3)

_P2: condition_split 보수화 전 D-56/blocklist root cause 먼저 해결_

- [x] **S3-T1** D-56 suppress 완전 제거 — field 포화 heuristic 제거. adj GU는 all applicable fields 대상. S3-T3 rule engine이 올바른 대체제
  - adj_gen=0 의 root cause 제거 (S1-T9 DROP 당시 진단: "root cause는 S3 D-56")
  - S3-T3 이전 과도기: `[:3]` cap(F1) + plan cycle_cap이 GU flooding 방지
  - **L1**: `TestSuppressRemovalRegression` 3 cases ✓ (838 passed after S3-T2)
- [x] **S3-T2** `recent_conflict_fields` state 필드 + blocklist window N=2 구현
  - conflict 발생 시 field 기록, 2 cycle window 트리밍, adjacent GU 생성 차단
  - **L1**: `TestRecentConflictFieldsBlocklist` 3 cases ✓ (838 passed)
  - **L2**: `si-p7-s3-t1t2-smoke` (1c) — adj GU 6건, price 포함 ✓, balance-* 0 ✓, KU 13→32
- [x] **S3-T3** `domain-skeleton.json` 에 `field_adjacency` rule engine seed
  - `cycle-0-snapshot/domain-skeleton.json`: 11개 field → 2~3 next_fields 매핑
  - 설계: `price→[how_to_use,where_to_buy,tips]`, `policy→[eligibility,how_to_use,tips]` 등
- [x] **S3-T4** `_generate_dynamic_gus` 가 rule engine 참조
  - `field_adjacency[field]` → `applicable_fields` 교집합; fallback: applicable_fields
  - **L1**: `TestFieldAdjacencyRuleEngine` 3 cases ✓ (841 passed)
  - **L2**: `si-p7-s3-t4-smoke` (1c) — adj GU 5건, 모두 field_adjacency 값 내 ✓, balance-* 0 ✓, KU 13→24
- [x] **S3-T5** `fields[].default_risk`, `default_utility` skeleton 추가
  - `cycle-0-snapshot/domain-skeleton.json`: 11개 field에 default_risk/default_utility 추가
  - 설계: price/acceptance→financial, policy/eligibility→policy, tips/duration→informational, 나머지→convenience
- [x] **S3-T6** dynamic GU 가 skeleton default 사용
  - `_generate_dynamic_gus`: `field_defaults` 맵 구축 → adj GU `risk_level`/`expected_utility` 에 적용
  - fallback: default 없으면 "medium"/"convenience" 유지
  - **L1**: `TestSkeletonFieldDefaults` 2 cases ✓ (843 passed)
- [x] **S3-T7 (보수화)** rule yield tracker — 약화 임계 5c 평균 < 0.05
  - `state.adjacency_yield: list[dict]` 추가, integrate_node 에서 매 cycle 누적 (최근 10c)
  - `adj_yield = adj_resolved / max(adj_open_at_start, 1)` per-cycle
  - **L1**: `TestAdjacencyYieldTracker` 3 cases ✓ (846 passed)
  - **L2**: S3 Axis Gate (5c `p7-rebuild-s3-smoke`) 와 합산 검증 (비용 절감)
- [x] **S3-T8** blocklist N cycle 동안 source/next 양쪽 배제
  - `_generate_dynamic_gus`: `claim.field in blocklist_fields` → 즉시 `[]` 반환
  - **L1**: `test_source_field_blocklisted_skips_all_adj` ✓ (847 passed)

### S3 Axis Gate (5c smoke) ✅ PASS

```
trial: bench/silver/japan-travel/p7-rebuild-s3-smoke/  (5c real API)
결과:
- GU_open c3=10, c4=2, c5=0 (c3+ ≥ 5 ✓ — no collapse)
- target_count c5=2 (조건부 ✓ — GU 2개만 남아 정상 수렴, attempt-1 collapse와 구별)
- KU c5=79 (≥ 70 ✓)
- conflict field 재생성=0 (overlap=∅ ✓)
- balance-*=0 ✓
- adjacency_yield 5 entries, 5c avg=0.500 (>> 0.05 ✓) [S3-T7 L2 합산 검증]
- adj GU fields: where_to_buy/how_to_use/price/eligibility/tips (field_adjacency 값 내 ✓)

판정: PASS → Stage B-1 Extension (S3-T9~T14) 진입
```

### Stage B-1 Extension — GU 생성 범위 확장 (S3-T9~T14)

_entity-field-matrix 분석으로 발견된 3가지 vacant 패턴 (P1/P2/P3) 수정. S3 Gate PASS 이후 추가 태스크. 결과 지표 후퇴 없음 (adj GU 증가 방향)._

> **Vacant 패턴 요약**
> - P1 (75 slots): wildcard-first 후 named entity adj GU 미생성 — Bug A (raw entity_key) + S3-T10 미구현
> - P2 (7 slots): entity-specific GU 생성 시 wildcard(\*) 슬롯 미생성 — seed.py:259 브랜치 구조
> - P3 (15 slots): per_cat_cap=4 (8 categories) → regulation 4 eligibility GU로 cap 소진 → price/tips 미등록
> - 추가: field_adjacency direct-pair 차단 효과 → applicable_fields 전체로 확장
> - 추가: dynamic_cap `open_count * 0.2` → open GU 감소 시 adj GU 생성 위축

- [x] **S3-T9** `_generate_dynamic_gus` Bug A/B 수정 (P1) — `src/nodes/integrate.py:193`
  - **Bug A**: 시그니처에 `canonical_entity_key` 파라미터 추가 → `entity_key = canonical_entity_key or claim.get("entity_key", "")`
  - **Bug B**: `existing_ku_slots` 파라미터 추가 → `existing_slots |= existing_ku_slots` (KU 슬롯 병합)
  - `integrate_node` 호출부 (~line 561): canonical entity_key 전달 + `existing_ku_slots` 계산 전달
  - **L1**: `test_adj_gu_uses_canonical_entity_key`, `test_adj_gu_skips_existing_ku_slot` ✓ (859 passed)

- [x] **S3-T10** post-cycle new-KU adj sweep (P1) — `src/nodes/integrate.py` (claim loop 이후)
  - `adds` 리스트 순회: 이번 cycle 신규 KU 각각에 대해 `_generate_dynamic_gus` 호출
  - `sweep_entity_seen` set으로 동일 entity 중복 방지
  - cap 내에서만 등록 (기존 `dynamic_cap` 공유)
  - **L1**: `test_new_ku_sweep_creates_adj_gus`, `test_sweep_respects_cap`, `test_sweep_deduplicates` ✓ (859 passed)

- [x] **S3-T11** seed.py wildcard GU 병행 생성 (P2) — `src/nodes/seed.py:284-296`
  - `WILDCARD_PARALLEL_FIELDS = {price, duration, how_to_use, acceptance, where_to_buy}`
  - entity-specific 브랜치에서 entity별 GU 생성 후 wildcard slot (`cat:*`) 추가 생성
  - **L1**: `test_seed_also_creates_wildcard_for_entity_specific_fields` ✓ (859 passed)

- [x] **S3-T12** per_cat_cap 제거 (P3) — `src/nodes/seed.py`
  - `_get_per_category_cap` 함수 제거 + cap 적용 루프 제거
  - `deduped` 직접 사용, 최소 커버리지(`cats_covered`) 기반으로 변경
  - **L1**: `test_seed_no_per_cat_cap_all_fields_present`, `test_seed_no_per_cat_cap_regression` ✓ (859 passed)
  - **수정**: `test_bootstrap_gu_count` 상한(40) 제거 (per_cat_cap 잔재)

- [x] **S3-T13** `_generate_dynamic_gus` field_adjacency 규칙 제거 — `src/nodes/integrate.py:224`
  - `field_adjacency` lookup 브랜치 삭제 → 항상 `adj_candidates = applicable_fields` 사용
  - **L1**: `test_adj_gu_uses_all_applicable_fields_not_adjacency_list` ✓ (859 passed)
  - **수정**: `test_uses_adjacency_map_when_present` 기대값 → `{"tips", "how_to_use", "where_to_buy"}`

- [x] **S3-T14** dynamic_cap 공식 수정 — `src/nodes/integrate.py:279-281`
  - `open_count * 0.2` 제거, 고정 cap: normal=`8`, jump=`20`
  - `_compute_dynamic_gu_cap(mode)` (인자 단순화)
  - **L1**: `test_dynamic_cap_fixed_normal_8`, `test_dynamic_cap_fixed_jump_20`, `test_dynamic_cap_not_open_count_dependent` ✓ (859 passed)

### S3 GU Gate (5c smoke) ❌ FAIL → Stage B-3 진입 보류

> ⚠️ **종전 narrative G1~G5 PASS 판정은 무효 (false PASS).** entity-field-matrix 정량 비교에서 attraction abandoned (v=77, open_gu=0), vacant 11% 만 감소, adj_yield 28% 후퇴 확인.
> 신 Gate: **M-Gate** (V/O composite + M1~M8 mechanistic). 의미론·임계값 근거 → `si-p7-gate-mechanistic.md`
> 구현: `scripts/check_s3_gu_gate.py` | 리포트: `bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/m-gate-report.json`

**baseline**: `p7-rebuild-s3-smoke` (commit fd83861) → **target**: `p7-rebuild-s3-gu-smoke` (commit fbbebbc)
**재판정 일자**: 2026-04-26

```
=== Primary (V/O composite) ===
V1  vacant_total_reduction        : Δ=11 (need ≥29 = P-zone 97×30%)            FAIL
V2  per_cat_vacant_no_regression  : attraction +5; connectivity +1             FAIL
V3  untouched_entity_bound        : target=0, baseline=0                       PASS
O1  active_frontier_existence     : abandoned: attraction(v=77,o=0)            FAIL
O2  open_gu_category_coverage     : KL(vacant_share || open_share) = ∞         FAIL
VxO frontier_health               : 7/8 cats healthy; attraction 단독 fail     FAIL

=== Mechanistic (T9~T14 검증) ===
M1  named_entity_adj_gu_count (T9)  : 14/13=1.08× (need ≥2× ∧ ≥12)             FAIL
M2  wildcard_parallel_pair    (T11) : 3/4=0.75 (need ≥0.7)                     PASS
M3  reg+pass_ticket_gu_count  (T12) : 31/12=2.58×                              PASS
M4  adj_gu_field_diversity    (T13) : 7 vs 5 (Δ=+2 ∧ ≥6)                       PASS
M5  late_cycle_adj_gen        (T14) : Δc4=0, Δc5=2 weak PASS / strict FAIL     PASS
M6  adj_yield_floor                 : 0.362/0.500=0.72 (need ≥0.9)             FAIL
M7  conflict_regen_zero             : violations=6 (정책 위반 신호)              FAIL
M8  ku_active_sanity                : 101/79=1.28                              PASS

Telemetry-deferred (NA, gate 통과 무관):
  M5b dynamic_cap_hit, M9 sweep_attribution, M10 created_cycle, M11 per_cycle_counts

VERDICT: FAIL  (exit=1, V/O FAIL: V1, V2, O1, O2, VxO)
```

**해석**:
- ✓ T11/T12/T13 작동 확인 (M2/M3/M4 PASS)
- ✗ **T9 거의 무작동** (M1 1.08×) → attraction abandoned root cause 후보
- ⚠ T14 부분 작동 (Δc4=0 ∧ Δc5=2) — c4 한 cycle drought 후 회복
- ? T10 검증 보류 (M9 telemetry 필요)
- 신규 발견: **V2 connectivity +1 regression**, **M7 conflict regen 6건** (정책 위반)

**다음 액션**: S3 Diagnosis 2-Trial Plan 진입 → Trial 2 PASS 후 Stage B-3/B-4 mechanistic 재정의.

### S3 Diagnosis 2-Trial Plan (확정 2026-04-26, Trial 3 F 폐기)

| Trial | Cumulative fix | 5c trial | M-Gate 목적 |
|-------|----------------|----------|-------------|
| **1** | A (DIAG-ATTRACTION) + B (DIAG-T10-T14 telemetry) | `p7-rebuild-s3-trial1-smoke` | T9 root cause fix 작동 검증 + strict 모드 활성화 |
| **2** | A+B + C (DIAG-YIELD) + D (DIAG-M7) + E (DIAG-CONNECTIVITY) | `p7-rebuild-s3-trial2-smoke` | 5개 fix 통합 효과 — V/O 모두 PASS 확인 (S3 closure) |

각 trial 종료 후 → `entity-field-matrix.json` 생성 → `python scripts/check_s3_gu_gate.py --baseline bench/silver/japan-travel/p7-rebuild-s3-smoke --target bench/silver/japan-travel/<trial> --json <trial>/m-gate-report.json [--strict]` → JSON 보존.

#### Trial 1 sub-tasks (구현 순서: B → A)

- [ ] **SI-P7-S3-DIAG-T10-T14** (Trial 1 의 B, 먼저) — telemetry M5b/M9/M10/M11 추가 + Gate 평가 함수 활성화
  - **M5b** `cap_hit_count` per cycle in trajectory — `src/nodes/integrate.py:280`, `src/state.py`, `scripts/run_readiness.py`
  - **M9** `gu['origin'] ∈ {claim_loop, post_cycle_sweep}` — `src/nodes/integrate.py:570-597`, `schemas/gap-unit.json`
  - **M10** `gu['created_cycle']: int` (ISO date 대체) — `src/state.py`, `src/nodes/integrate.py:255`, `src/nodes/seed.py`
  - **M11** trajectory row 에 `adj_gen_count`, `wildcard_gen_count` — `src/nodes/integrate.py`, `src/nodes/seed.py`, `scripts/run_readiness.py`
  - **Gate 활성화**: `scripts/check_s3_gu_gate.py` 의 `_na_result("M5b", ...)` 등 4개 → 실 평가 함수 교체
  - **L1**: telemetry emit + Gate 활성화 unit tests
- [ ] **SI-P7-S3-DIAG-ATTRACTION** (Trial 1 의 A, 두 번째) — attraction 카테고리 GU 생성 블로커 추적 (M1 1.08× 직접 원인 = T9 무작동)
  - telemetry 활용 (`gu['origin']`, `created_cycle`, `adj_gen_count`) 로 정밀 진단
  - 진입점: `src/nodes/integrate.py:_generate_dynamic_gus`, `src/nodes/seed.py:_get_initial_gus_for_entity`
  - root cause 가설 → fix 구현 → L1 unit test
- [ ] **Trial 1 실행** — `scripts/run_readiness.py --cycles 5 --trial-id si-p7-s3-trial1-smoke`
- [ ] **Trial 1 M-Gate 판정** — `--strict` 모드 활성화. PASS 시 Trial 2 진입, FAIL 시 root cause 재추적

#### Trial 2 sub-tasks (Trial 1 PASS 후, 누적 적용)

- [ ] **SI-P7-S3-DIAG-YIELD** (C) — M6 0.72 (adj_yield 28% 후퇴) 원인 추적 + dynamic_cap 8/15/20 ablation, 최적값 결정
- [ ] **SI-P7-S3-DIAG-M7** (D) — conflict 해소 field 에 adj GU 재생성 6건 정책 위반. seed/integrate 단계의 conflict_field 필터 추가
- [ ] **SI-P7-S3-DIAG-CONNECTIVITY** (E) — connectivity vacant +1 regression 원인 (cap 제거 후 wildcard 분배 변동 가능)
- [ ] **Trial 2 실행** — `scripts/run_readiness.py --cycles 5 --trial-id si-p7-s3-trial2-smoke`
- [ ] **Trial 2 M-Gate 판정** — V/O 6/6 PASS + M 8/8 PASS 목표. PASS → S3 closure → Stage B-3/B-4 reorg 진입

### Stage B-3 — condition_split 재정의 (S2-T3~T8, D-195 보수화)

> ⚠️ **Trial 2 PASS 후 mechanistic 기준으로 재정의 필요.** 현 task 정의는 narrative G1~G5 PASS 가정 기반. T9 fix 후 attraction adj GU 생성 패턴이 condition_split 로직과 충돌 가능성 있어 axis-gate 도 V/O + M criteria 패턴으로 재구성 예정.

**사전 작업**: S2-T6 시작 직전 V-T11 cherry-pick — `git cherry-pick f61c864` (config.py + integrate.py + tests)

- [ ] **S2-T3** F2 = α + β 확정 (D-181 design only, 구현 불필요)
- [ ] **S2-T4** F2 구현 — α (query 재작성, critique → plan) + β (aggressive mode entity_discovery 파라미터 override). **β 는 S5a-T11 동반 구현**
- [ ] **S2-T5** condition_split (a): parse prompt "조건어 추출"
- [ ] **S2-T6 (보수화)** "값 구조 차이" 감지 → condition_split. **임계: existing/claim 모두 ≥ 2 chars, set/range 변환 시 명시적 marker 필요**
  - **L1**: `_value_structure_type()` + 보수 임계 unit
  - **L2**: `si-p7-s2-t6-smoke` (1c) — 조건값 claim → split 출현
- [ ] **S2-T7 (보수화)** `skeleton.fields[].condition_axes` 강제. **임계: claim 의 conditions 필드 비어있지 않을 때만**
- [ ] **S2-T8 (보수화)** axis_tags 차이 → condition_split. **임계: 단일 axis 차이만 (geography 단일), 다중 axis 차이는 hold**

### S2 Axis Gate (5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s2-smoke/  (5c real API)
PASS 기준 (s2-attempt-1 대비):
- c1 ΔKU ≤ +35  (s2-attempt-1: +59)
- GU 양산 ≥ 65  (s2-attempt-1: 49)
- KU c5 ≥ 90  (s2-attempt-1: 88, 회복)
- adj_gen: c3+ 0 cycle 없음
FAIL 시: V-T11 토글로 narrowing (T6/T7/T8 개별 off → 어느 rule 이 폭증 원인)
```

### Stage B-4 — balance 대체 (S4-T2~T4)

> ⚠️ **Trial 2 PASS 후 mechanistic 기준으로 재정의 필요.** VxO frontier_health 7/8 healthy 기준 충족 시 balance 기준도 mechanistic 으로 재구성. virtual entity 0 + deficit_score 발동률 단독 PASS 는 narrative 가정.

- [ ] **S4-T2** `coverage_map.deficit_score` 기반 카테고리 결핍 계산
- [ ] **S4-T3** field 선택 → S3 `field_adjacency` 통일
- [ ] **S4-T4** S5a validated entity 대상으로만 balance GU

### S4 Axis Gate (5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s4-smoke/  (5c real API)
PASS 기준:
- virtual entity = 0
- deficit_score 발동률 ≥ 50%
- KU c5 ≥ 75  (s4-attempt-1: 78)
- cycle skip 없음
```

---

## Stage C — Entity Discovery (S5a 전체)

- [ ] **S5a-T1** `state.entity_candidates` 필드 + 스키마
- [ ] **S5a-T2** `domain-skeleton.json` 에 `entity_frame`
- [ ] **S5a-T3** `src/nodes/entity_discovery.py` 신설 — discovery target = `coverage_map.deficit_score` 공유
- [ ] **S5a-T4** rule-based query template
- [ ] **S5a-T5** LLM query 보강 (β mode 즉시 활성)
- [ ] **S5a-T6** similarity≥0.85 pre-filter → candidate 적재
  - **L2**: `si-p7-s5a-t6-smoke` (3c) → `state.entity_candidates` 증가
- [ ] **S5a-T7** 승격 판정 (`source_count≥2 AND distinct_domain≥2`)
  - **L2**: `si-p7-s5a-t7-smoke` (5c) → `state.domain_skeleton.entities` 신규
- [ ] **S5a-T8** 승격 entity → skeleton 등록 + seed field GU 자동
- [ ] **S5a-T9** `src/graph.py` 에 entity_discovery 노드 위치 B
- [ ] **S5a-T10** candidate 수명 (D-185)
  - **L2**: `si-p7-s5a-t10-smoke` (12c) → `candidate.status` transitions
- [ ] **S5a-T11** β aggressive mode 구현 — **logger.info 명시 + `aggressive_mode_remaining` snapshot persist 의무 (attempt 1 V1 audit H5c 회피)**
  - **L2**: `si-p7-s5a-t11-smoke` — β 강제 trigger 후 `state.aggressive_mode_remaining` snapshot 확인
- [ ] **S5a-T12** 테스트 (승격 flow, candidate 누적, GU 생성, stale/purge, pre-filter, β)

### S5a Axis Gate (5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s5a-smoke/  (5c real API)
PASS 기준:
- entity_candidates 누적 ≥ 5
- 승격 entity ≥ 1 (5c 내)
- β mode trigger 시 aggressive_mode_remaining snapshot 에 기록
- pre-filter 차단 건수 > 0 (similarity≥0.85)
```

---

## Stage D — Phase 전체 L3 (15c 통합 trial)

- [ ] **D-T1** `bench/silver/japan-travel/p7-rebuild-on/` 15c real API
- [ ] **D-T2** `bench/silver/japan-travel/p7-rebuild-off/` 15c real API (Pre-P7 baseline)
- [ ] **D-T3** `silver-phase-gate-check` skill → readiness-report 작성
  - VP1 expansion_variability ≥ 4/5
  - VP2 completeness ≥ 5/6
  - VP3 self_governance ≥ 4/6
  - critical FAIL 없음

---

## 문서 / 부가 작업

- [ ] **D-T4** v6 final report 작성 (`v6-rebuild-report.md`) — attempt 1 vs attempt 2 비교, axis-gate 효과 정리
- [ ] **D-T5** project-overall 동기화 (D-194/195/196/200/201/202 등록)
- [ ] **D-T6** `_CC` suffix scaffolding 4개 정리 (또는 archive)

---

## Phase 종료 기준

1. Step A/B/C 의 모든 axis 5c smoke gate **PASS**
2. Stage D 15c L3 trial readiness-report **PASS**
3. attempt 1 known-pitfall 회피 검증 (S1 oscillation 0, S2 c1 폭증 ≤ 30%, S3 GU pool 고갈 0, β dead code 0)
4. 누적 비용 ≤ ~$3.0 (예산 ~$2.8 + 여유)
5. `dev/active/phase-si-p7-structural-redesign/` → `dev/archive/`, project-overall 동기화

---

## Task Size 분포

| Size | Count | Tasks |
|---|---|---|
| S | 10 | S1-T1/T2/T3/T7, S2-T1/T2/T3, S4-T1, S3-T12/T13 |
| M | 18 | S1-T4/T5/T6 ~~T8/T9~~, S2-T4/T5/T6/T7/T8, S3-T1~T8 부분, S3-T9/T10/T11/T14 |
| L | 9 | S5a-T3/T5/T6/T7/T8/T9/T10/T11/T12 |
| XL | 0 | — |

**Total**: ~47 tasks (Stage A: 9, Stage B: 24 [+6 GU extension], Stage C: 12, Stage D: 3) + 문서 3
_(S3-T9~T14 신규 추가, T8/T9 DROP으로 -2)_
