# SI-P7 Structural Redesign — Tasks (rebuild)

> Last Updated: 2026-04-25
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
- [ ] **S3-T3** `domain-skeleton.json` 에 `field_adjacency` rule engine seed
- [ ] **S3-T4** `_generate_dynamic_gus` 가 rule engine 참조
  - **L2**: `si-p7-s3-t4-smoke` (1c) — adj GU field 가 seed 맵 내
- [ ] **S3-T5** `fields[].default_risk`, `default_utility` skeleton 추가
- [ ] **S3-T6** dynamic GU 가 skeleton default 사용
- [ ] **S3-T7 (보수화)** rule yield tracker — 약화 임계 5c 평균 < 0.05 (강한 신호만)
  - **L2**: `si-p7-s3-t7-smoke` (5c) — `state.adjacency_yield`
- [ ] **S3-T8** blocklist N cycle 동안 source/next 양쪽 배제

### S3 Axis Gate (5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s3-smoke/  (5c real API)
PASS 기준 (s3-attempt-1 대비):
- GU_open c3+ ≥ 5  (s3-attempt-1: 0 c3+ collapse)
- target_count c5 ≥ 3  (s3-attempt-1: 0)
- KU c5 ≥ 70  (s3-attempt-1: 61)
- conflict field 재생성 = 0
FAIL 시: suppress/blocklist/yield 임계 narrowing (보수화 강도 올림)
```

### Stage B-3 — condition_split 재정의 (S2-T3~T8, D-195 보수화)

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
| S | 8 | S1-T1/T2/T3/T7, S2-T1/T2/T3, S4-T1 |
| M | 14 | S1-T4/T5/T6 ~~T8/T9~~, S2-T4/T5/T6/T7/T8, S3-T1~T8 부분 |
| L | 9 | S5a-T3/T5/T6/T7/T8/T9/T10/T11/T12 |
| XL | 0 | (S5a 통합은 12 tasks 로 분해됨) |

**Total**: ~41 tasks (Stage A: 9, Stage B: 18, Stage C: 12, Stage D: 3) + 문서 3
_(T8/T9 DROP으로 -2)_
