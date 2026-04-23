# SI-P7 Step V — V1 Signal Audit

> 작성: 2026-04-23
> 범위: Step A/B 각 item 의 L3 trial (`p7-ab-on` / `p7-ab-off`) 기간 신호 발현 여부 재파싱
> 근거 데이터: `bench/silver/japan-travel/p7-ab-on`, `p7-ab-off` 의 `state-snapshots/` + `telemetry/cycles.jsonl` + `run.log`
> 도구: `scripts/analyze_p7_ab_signals.py`

## 배경

`p7-ab-on` L3 trial 이 FAIL (cycle 3~15 KU 82 고정, GU 고갈) 하자 `balance-*` 제거 (S4-T1) 단독 원인으로 단정할 뻔함. 그러나 검증 매트릭스 17개 중 ~7개가 계측 부재로 확증 불가 (D-190). V1 는 **기존 snapshot + log 에서 추출 가능한 신호만** 으로 재판정한다 (read-only, API 비용 0). state 에만 존재하고 persist 되지 않는 필드는 V2 (계측 보강) 대상으로 분류.

---

## [A] Cycle × 신호 표

### p7-ab-on (KU 고정 FAIL)

| cycle | mode | KU | GU_open | GU_res | defer | adj_gen | tgt | rslv | cncr | wild | confl | gap_res |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | normal | 26 | 26 | 9 | **20** | 6 | 29 | 9 | 14 | 15 | 0.19 | 0.26 |
| 2 | jump | **82** | 2 | 35 | 0 | 2 | 28 | 26 | 16 | 12 | 0.15 | 0.95 |
| 3 | jump | 82 | **0** | 37 | 0 | 0 | 2 | 2 | 2 | 0 | 0.00 | 1.00 |
| 4~15 | jump | 82 | 0 | 37 | 0 | 0 | **0** | 0 | 0 | 0 | 0.00 | 1.00 |

**해석**:
- c1: 29 target 중 9 resolved + 20 defer → c2 로 이월
- c2: defer 소진으로 급등 (KU +56, resolved 26). adj_gen 2, wild 12
- c3~15: GU_open 0 → tgt 0 → 완전 정체. `gap_res=1.0`, `conflict_rate=0` 은 **GU 고갈에 의한 misleading 지표** (수렴 PASS 아님)

### p7-ab-off (baseline 건전)

| cycle | mode | KU | GU_open | adj_gen | tgt | rslv | gap_res |
|---|---|---|---|---|---|---|---|
| 1 | normal | 31 | 40 | 6 | 13 | 11 | 0.31 |
| 5 | jump | 68 | 39 | 1 | 13 | 7 | 0.55 |
| 8 | jump | **109** | 35 | **17** | 11 | 9 | 0.66 |
| 10 | jump | 126 | 28 | 0 | 8 | 3 | 0.75 |
| 15 | jump | **147** | 14 | 0 | 10 | 6 | **0.88** |

**해석**: c1~c15 점진 성장, c8 에서 entity 급증 + adj_gen 17 회 (건전 확장). c10 이후 adj_gen 0 이지만 tgt 꾸준, GU_open 14 로 종료.

---

## [B] run.log 키워드 빈도

| 키워드 | p7-ab-on | p7-ab-off | 비고 |
|---|---|---|---|
| `aggressive` / `aggressive_mode` | **0** | 0 | β mode 활성 흔적 **전무** |
| `ku_stagnation` (직접 문자열) | 0 | 0 | 로그 구문이 아닌 rx_id 로 emit |
| `growth_stagnation` | **3** (lines 491/546/601) | 0 | on 쪽 c3+ 정체 감지 |
| `exploration_drought` | 2 (lines 546/601) | 2 (lines 1132/1432) | 양쪽 모두 |
| `Remodel 트리거` | 3 | 2 | 자연 발동 양쪽 모두 |
| `query_rewrite` | **0** | 0 | S2-T4 α 흔적 **전무** |
| `entity_discovery` | 0 | 0 | Step C 대기 (정상) |
| `suppressed` / `adjacency_yield` / `recent_conflict_fields` / `conflict_blocklist` / `condition_split` / `axis_tags` / `integration_result` | 0 | 0 | **로그 계측 부재** |

---

## [C] Step A/B 항목별 재판정 (V1 완료 기준)

기호: ✓ 발현 확인 / ✗ 발현 실패 (의심 → 확정) / ~ 계측 부재

| 항목 | 판정 | 근거 |
|---|---|---|
| S1-T1~T3 `_select_targets` 자유화 | ✓ | c1 tgt=29 (priority sort 제거 확인) |
| S1-T4/T5/T8 defer/queue | ✓ | c1 defer=20, c2 defer=0 (FIFO 소진) |
| S1-T8 defer_reason telemetry | ✓ | `telemetry/cycles.jsonl` 에 `defer_reason` 존재 |
| S2-T1 `integration_result_dist` plan_modify 주입 | **~** | state 필드가 snapshot 에 persist 안 됨 — V2 계측 |
| S2-T2 `ku_stagnation` trigger | **✓** (V1 승격) | `growth_stagnation` 3회 + `exploration_drought` 2회 로그 확인 |
| S2-T4 α `query_rewrite` rx | **✗** (확정) | 로그 0회. stagnation 발동했는데 rewrite 흔적 부재 → 구현 버그 후보 |
| S2-T4 β `aggressive_mode_remaining` | **✗** (확정) | `aggressive` 키워드 0회. `critique.py:655` 에서 설정되지만 **entry/exit 로그 emit 부재** + state 미persist → 실제로 발동했는지 불명 |
| S2-T5~T8 `condition_split` 재정의 | ~ | 로그 0회. integration 내부 처리라 로그 안 남김 — V2 계측 |
| S3-T1 suppress threshold (`mean × 1.5`) | ~ | 로그 0회 — V2 계측 |
| S3-T2/T8 `recent_conflict_fields` blocklist | ~ | state 필드 snapshot 부재 — V2 계측 |
| S3-T3~T6 adjacent rule engine | ✓ | c1 adj_gen=6, c2 adj_gen=2, c8(off) adj_gen=17 (rule 발동 확인) |
| S3-T7 rule yield tracker | ~ | state 필드 snapshot 부재 — V2 계측 |
| S4-T1 virtual entity 제거 | ✓ | skeleton snapshot 에 `balance-*` entry 0 |
| S4-T2 `coverage_map.deficit_score` | ~ | state 필드 snapshot 부재 — V2 계측 |
| S4-T3/T4 | N/A | Step C 대기 |

### 최종 카운트

| 분류 | 수 | 이전 대비 |
|---|---|---|
| ✓ | **11** | +1 (S2-T2 승격) |
| ✗ (확정) | **2** | +1 (S2-T4 β 확정) |
| ~ (계측 부재) | **6** | -1 (S2-T2 해제) |
| N/A | 2 | 변동 없음 |

---

## [D] V2 계측 필요 항목 + emit 위치 제안

### 원칙

- **Option A (state snapshot)**: `src/utils/state_io.py` 의 `_FILE_MAP` 또는 `_OPTIONAL_LIST_FILES` 에 신규 파일 추가 (예: `si-p7-signals.json`)
- **Option B (telemetry)**: `src/obs/telemetry.py:_build_snapshot` 의 cycle snapshot dict 에 필드 추가 (현재 line 130 에 `deferred_targets` 카운트만 emit 중)
- **Option C (run.log)**: `logger.info` 로 구조화 문자열 emit (grep 가능한 prefix)

선택 기준: **cycle 단위 집계** → B, **cycle-snapshot 파일 디렉토리 소비** → A, **빈도만 확인** → C.

### 매핑

| 항목 | 제안 emit 경로 | 타입 |
|---|---|---|
| S2-T1 `integration_result_dist` | B: `cycles.jsonl` snapshot 에 `integration_result_counts: {added, updated, condition_split, conflict_hold, ...}` 추가 | dict |
| S2-T4 β `aggressive_mode_remaining` | C: `critique.py:655` 에서 `logger.info("aggressive_mode entry: rx=%s, remaining=3")` + `plan.py:345` 에서 exit 시 `logger.info("aggressive_mode tick: remaining=%d")` / B: cycle snapshot 에 `aggressive_mode_remaining` 필드 | scalar |
| S2-T4 α `query_rewrite` rx | C: rewrite 발동 시 `logger.info("query_rewrite: gu=%s, from=%s, to=%s")` | event |
| S2-T5~T8 `condition_split` | C: split 발동 시 `logger.info("condition_split: ku=%s, axis=%s, new_ku_count=%d")` / B: cycle snapshot `condition_split_count` | scalar+event |
| S3-T1 suppress threshold | C: suppress 발동 시 `logger.info("adjacency suppressed: cat=%s, threshold=%.2f, generated=%d")` | event |
| S3-T2/T8 `recent_conflict_fields` | A: `state-snapshots/cycle-N-snapshot/si-p7-signals.json` 에 `{recent_conflict_fields: [{field, since_cycle}, ...]}` / B: snapshot count | list |
| S3-T7 `adjacency_yield` tracker | A: same file, `{adjacency_yield: {rule_id: {gen, valid, yield}}}` / B: top3 rule yield 요약 | dict |
| S4-T2 `coverage_map.deficit_score` | A: same file, `{coverage_map: {cat: deficit_score}}` | dict |

### 구현 범위 (V-T4/T5)

최소 필요:
1. `src/utils/state_io.py` — `_OPTIONAL_LIST_FILES` 에 `si-p7-signals.json` 추가, state 필드 `si_p7_signals: dict` 새로 매핑
2. `src/state.py` — `si_p7_signals` TypedDict 엔트리 (`recent_conflict_fields`, `adjacency_yield`, `coverage_map`, `aggressive_mode_history`) 추가
3. `src/nodes/critique.py:655` 및 `src/nodes/plan.py:345` 근처 — aggressive mode entry/exit `logger.info`
4. `src/nodes/integrate.py` — `integration_result_counts` dict 누적 + telemetry emit
5. `src/nodes/plan.py` (query_rewrite 경로) — rewrite event `logger.info`
6. `src/obs/telemetry.py:_build_snapshot` — `integration_result_counts`, `aggressive_mode_remaining`, `condition_split_count` cycle snapshot 에 추가

**로직 변경 금지** (V-T5 원칙): 관찰만 추가. L1 테스트는 "emit 경로가 호출되면 해당 필드가 기록된다" 만 검증.

---

## [E] S2-T4 β aggressive mode 버그 가설

V1 결과로 **S2-T4 β 구현 결함** 이 root cause 중 하나일 가능성이 높아졌다.

### 증거

1. `critique.py:655` 에서 `rx_id=ku_stagnation:added_low` 발동 시 `aggressive_mode_remaining=3` 으로 설정하는 코드는 존재 (Grep 확인)
2. `plan.py:345` 에서 `aggressive_mode_remaining` 을 읽고 `_is_stagnation_active` 에 전달하는 경로도 존재
3. `p7-ab-on` 에서 `growth_stagnation` 로그 3회 발동 — 즉 **trigger 자체는 작동**
4. 그런데 `aggressive` 키워드 로그 0회 + state snapshot persist 부재 → **발동 후 실제로 상태가 유지되는지, target 확장 / source_count≥1 임시 적재 등 β mode 효과 경로가 작동하는지 증명 불가**

### 가설 (H5 구체화)

**H5a**: `critique.py:655` 의 설정 시점이 `plan.py:345` 에서 읽는 시점보다 뒤 (cycle 경계 문제) → 다음 cycle 에 반영 안 됨
**H5b**: `aggressive_mode_remaining>0` 이어도 `_is_stagnation_active` 의 다른 조건이 막음 (예: `gap_res<threshold` 동시 요구)
**H5c**: β mode 효과 (target 확장, source_count 완화 등) 가 S5a (entity_discovery) 에 의존 — **S5a 미구현이라 β 자체가 no-op** (D-181 의 β 정의가 S5a 와 coupled)

**H5c 가 가장 유력**: SI-P7 tasks 에서 S5a-T11 에 "β aggressive mode 구현 (D-181)" 이 배정되어 있음 (entity_discovery 의 LLM query + source_count≥1 임시 적재). 즉 **β mode state 는 존재하지만 효과 경로 (entity discovery) 가 미구현** → stagnation 감지해도 실질 행동 없음.

### 검증 방법 (V2 계측으로)

1. aggressive_mode_remaining 값이 cycle 별로 어떻게 변하는지 persist/emit
2. "β mode 진입 중인 cycle 에서 target 수 / source_count threshold / LLM query 호출 수" 를 별도 count
3. 3번 모두 0 이면 H5c 확정 → **S5a 착수 전까지 β 는 dead code**

---

## 판정 요약

- **✓ 11 / ✗ 2 / ~ 6** — `~` 가 여전히 6개 (6/17 = 35%). 판정 기준 `~` 과반 미만이라 root cause 일부 확정은 가능
- **확정 가능**: S2-T4 α `query_rewrite` 기능 부재, S2-T4 β aggressive mode no-op 가능성 (H5c)
- **여전히 불명**: S3 blocklist / yield tracker / S4 coverage_map 실제 동작 여부 — V2 계측 후 재판정

### `p7-ab-on` FAIL 의 원인 추정 (현 시점, V1 완료)

| 원인 후보 | 기여도 | 근거 |
|---|---|---|
| 초반 공격적 budget (c1 defer 20 + c2 소진 → KU 급등) | **높음** | c2 까지 모든 target 소진 |
| GU 고갈 (c3+ GU_open=0) | **높음** (결과적) | 초반 과처리의 후행 결과 |
| S2-T4 β aggressive mode no-op (H5c) | **중간** | stagnation 감지해도 복구 행동 부재 |
| S5a entity discovery 미구현 | **중간** | β mode 효과 경로 부재 + 새 entity 탐색 채널 없음 |
| `balance-*` 제거 (S4-T1) 단독 | **낮음** | virtual entity 제거는 S5a 로 대체하는 설계 (D-177), 단독 원인 아님 |

**D-190 유지 확정**: `balance-*` 제거 단독 원인 단정은 V1 증거로도 부적절. S5a 착수 + β mode 효과 경로 연결이 더 근본적.

---

## Next Step (V-T4 이후)

1. V-T4/T5: 위 [D] emit 매핑 구현 (로직 변경 없음, 관찰만)
2. V-T6: `--trial-id p7-v2-smoke --cycles 1` 로 emit 경로 작동 확인
3. V-T7: V2 smoke 결과로 `~6` 이 `✓/✗` 로 분류되는지 확인 → 남은 ~ 가 있을 때만 V3 ablation (D-191 8c trial)
4. V-T10: H5c 포함한 H1~H7 증거 집계 → D-192 root cause 확정
5. V-T11: S5a 착수 여부 + Step A/B item 수정 우선순위 결정

## 관련 결정

- D-189 (보류) / D-190 (Step V 삽입) / D-191 (V3 ablation 설계)
- D-181 (β mode 정의 — S5a coupled)
- D-177 (virtual entity = S5a 로 대체)
- Memory: `feedback_l3_trial_item_signal_audit.md`, `feedback_root_cause_extensive_view.md`
