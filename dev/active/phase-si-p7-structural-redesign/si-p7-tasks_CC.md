# SI-P7 Structural Redesign — Tasks (_CC)

> 작성: 2026-04-21
> 단일 진실 소스: **`docs/structural-redesign-tasks_CC.md` v2** (task 상세)
> 본 문서는 착수 순서 + checklist + L1/L2 checkpoint 요약.
> 착수 순서는 baseline v2 §권장 착수 순서 (codex §5-7) 에 정렬.

---

## Step A — 제어 루프 복구 (S1 + S2-T1/T2)

### S1 — Target / Collect 자유화 (defer/queue)

- [ ] **S1-T1** `_UTILITY_ORDER`/`_RISK_ORDER` 제거, `_select_targets` 정렬 제거 (`src/nodes/plan.py`)
- [ ] **S1-T2** `_select_targets` 가 open_gus 전체 반환 (cycle cap 만 적용)
- [ ] **S1-T3** `mode_node` target_count 공식 → cycle cap 으로 대체 (`src/nodes/mode.py`)
- [ ] **S1-T4** collect.py utility skip 제거 + budget 초과 시 **drop 대신 `deferred_targets` 에 기록** (`src/nodes/collect.py:218-230`)
  - **L1**: `_calc_execution_queue()` 가 defer 반환
  - **L2**: `si-p7-s1-t4-smoke` — budget 낮춰 defer 유발 → `state.deferred_targets ≠ 0`, `metrics.deferred_count > 0`
- [ ] **S1-T5** `max_search_calls_per_cycle` config. **초과분은 drop 아니라 defer**
- [ ] **S1-T6** Budget 제거 smoke 5c — F1 결정 (완전 제거 시 비용/실패율/noise 측정)
- [ ] **S1-T7** regression guard: `target_count` cap 재도입 방지 테스트 (D-129)
- [ ] **S1-T8** `state.deferred_targets` 필드 + 다음 cycle plan **우선 소진**. 메트릭 `executed_targets`, `deferred_targets`, `defer_reason`

### S2-T1/T2 — integration_result 제어 입력화 (Step A 범위)

- [ ] **S2-T1** `integration_result` 분포 카운터 + **plan_modify/critique 입력으로 주입** (`src/utils/metrics.py`, `src/nodes/critique.py`, `src/nodes/plan.py`)
  - **L1**: `integration_result_distribution()` 정확 집계
  - **L2**: `si-p7-s2-t1-smoke --cycles 3` → `state.metrics.integration_distribution` 3-cycle window
- [ ] **S2-T2** `added_ratio<0.3×3c` + `conflict_hold 증가` + `condition_split 부재` **3종 trigger** → critique `rx_id=ku_stagnation:*`
  - **Plan reason code** 추가: `collect_defer_excess`, `integration_added_low`, `adjacent_yield_low`, `entity_discovery_insufficient`

### Step A L3 검증

- [ ] `bench/silver/japan-travel/p7-s1-on|off/` 15c A/B → **defer distribution, 실행 GU 수, API 호출 수, 다음 cycle 소진율**
- [ ] (선택) `p7-s2-control-on|off/` S2-T1/T2 단독 효과 측정

---

## Step B — KU/field 품질 개선 (S2-T5~T8 + S3 + S4)

### S2-T5~T8 — condition_split 재정의

- [ ] **S2-T3** 확정 (D-181 기록, 구현 불필요 — 설계 결정만)
- [ ] **S2-T4** F2 = α + β 구현 (α query 재작성 + β mode 전환). **β 는 S5a-T11 과 동반 구현** 필요
- [ ] **S2-T5** condition_split (a): parse prompt "조건어 추출"
- [ ] **S2-T6** condition_split (b) **재정의**: "값 구조 차이" (axis_tags/conditions/값 format) 감지 → 자동 split
  - **L1**: `_detect_value_shape_diff()` unit
  - **L2**: `si-p7-s2-t6-smoke` — 조건값 claim 주입 → `integration_result.condition_split` 출현
- [ ] **S2-T7** condition_split (c): `skeleton.fields[].condition_axes` 메타 + 누락 시 강제
- [ ] **S2-T8** axis_tags 차이 기반 condition_split (axis 공존 판정)

### S3 — adjacent rule engine

- [ ] **S3-T1** suppress → category 별 `mean × 1.5`
- [ ] **S3-T2** state `recent_conflict_fields` + blocklist 반영 (N=3 cycle)
- [ ] **S3-T3** `domain-skeleton.json` 에 `field_adjacency` rule engine seed (`{source_field: [next_fields]}` + category override)
- [ ] **S3-T4** `_generate_dynamic_gus` 가 rule engine 참조
  - **L1**: `field_adjacency` 참조 logic unit
  - **L2**: `si-p7-s3-t4-smoke` — 생성된 adj GU 의 field 가 seed 맵 내
- [ ] **S3-T5** `fields[].default_risk`, `default_utility` skeleton 추가
- [ ] **S3-T6** dynamic GU 가 skeleton default 사용, 고정 `medium/convenience` 제거
- [ ] **S3-T7** **rule yield tracker** — 낮은 yield rule 약화/중지
  - **L1**: yield 계산 unit
  - **L2**: `si-p7-s3-t7-smoke --cycles 5` → `state.metrics.adjacency_yield[rule_id]`
- [ ] **S3-T8** `recent_conflict_fields` N cycle 동안 source/next 양쪽 배제

### S4 — category_balance (virtual entity 즉시 제거)

- [ ] **S4-T1** virtual `balance-N` 생성 **전부 제거** (과도기 옵션 없음)
  - **L1**: `_generate_balance_gus` 가 virtual entity 생성 안 함
  - **L2**: `si-p7-s4-t1-smoke` → `state.gap_map` 에 `balance-*` 0건
- [ ] **S4-T2** `MIN_KU_PER_CAT` 제거 → `coverage_map.deficit_score` per-cat 계산
- [ ] **S4-T3** field 선택 → S3 `field_adjacency` 참조로 통일
- [ ] **S4-T4** S5a validated entity 대상으로만 balance GU 생성

### Step B L3 검증

- [ ] `p7-s2-on|off/`, `p7-s3-on|off/`, `p7-s4-on|off/` 15c A/B (또는 S2+S3+S4 묶음 on/off)
- [ ] **S2**: `added / updated / condition_split / conflict_hold` 분포
- [ ] **S3**: `adjacency_yield[rule_id]`, conflict field 재생성 = 0
- [ ] **S4**: category Gini, virtual entity = 0

---

## Step C — Entity Discovery (S5a 전체)

### S5a — C3-a 전체 범위

- [ ] **S5a-T1** `state.entity_candidates` 필드 + 스키마 (`first_seen_cycle`, `last_seen_cycle`, `status` 포함)
- [ ] **S5a-T2** `domain-skeleton.json` 에 `entity_frame` 스키마
- [ ] **S5a-T3** `src/nodes/entity_discovery.py` 신설 — **discovery target = `coverage_map.deficit_score` 공유 (D-184)**
- [ ] **S5a-T4** rule-based query template (`category+field+geo+source_hint`)
- [ ] **S5a-T5** LLM query 보강 (yield 낮을 때 또는 β mode 즉시 활성)
- [ ] **S5a-T6** search → entity 이름 추출 → **similarity≥0.85 pre-filter (D-186)** → candidate 적재
  - **L1**: candidate 적재 + pre-filter 분기
  - **L2**: `si-p7-s5a-t6-smoke --cycles 3` → `state.entity_candidates` 증가, 유사 candidate 는 alias 경로
- [ ] **S5a-T7** 승격 판정: `source_count≥2 AND distinct_domain≥2 AND category 적합`
  - **L2**: `si-p7-s5a-t7-smoke --cycles 5` → `state.domain_skeleton.entities` 신규 entry
- [ ] **S5a-T8** 승격 entity → skeleton 등록 + seed field GU 자동
- [ ] **S5a-T9** `src/graph.py` 에 entity_discovery 노드 삽입 — **위치 B (plan_modify → entity_discovery → plan)** (D-183)
- [ ] **S5a-T10** **candidate 수명 (D-185)**: `last_seen+5c → stale`, `+10c → purge`, 재등장 시 갱신
  - **L2**: `si-p7-s5a-t10-smoke --cycles 12` → `candidate.status` transitions
- [ ] **S5a-T11** **β aggressive mode 구현 (D-181)** — target 수 확장, LLM query, source_count≥1 임시 적재, GU 우선순위, trigger+2c
  - **L2**: `si-p7-s5a-t11-smoke` — β 강제 trigger → target 3-5 / source_count≥1
- [ ] **S5a-T12** 테스트 (승격 flow, candidate 누적, GU 생성, stale/purge, pre-filter, β)

### Step C L3 검증

- [ ] `p7-s5a-on|off/` 15c A/B
- [ ] **S5a**: validated entity 승격 수, 신규 파생 KU 수, candidate stale/purge 비율, pre-filter 차단 수, β mode trigger 통계

---

## 문서 / 부가 작업

- [ ] **D-T1** `docs/session-compact.md` trim (R1~R4 → S1~S5 교체)
- [ ] **D-T2** `docs/entity-acquisition-strategy-draft.md` → 확정본 (`-draft` 제거)
- [ ] **D-T3** Q12 Explore-Pivot note 한 줄 남김
- [ ] **D-T4** 축별 L3 15c A/B 완료 보고서
- [ ] **D-T5** phase 전체 Gate 판정 (`silver-phase-gate-check` 사용)

---

## Phase 종료 기준

1. Step A/B/C 의 모든 S<축>-T<번호> task L1 green
2. 각 축의 L2 checkpoint 통과
3. 각 축의 L3 15c A/B 에서 before/after metric 개선 확인 (baseline v2 §각 축 검증 지표)
4. `silver-phase-gate-check` skill 로 phase 전체 readiness-report **PASS**
5. `dev/active/phase-si-p7-structural-redesign/` → `dev/archive/` 로 이동, project-overall 동기화

---

## 다음 phase 후보 (본 phase 제외)

- S5b 전체 (`rapidfuzz` 의존성, auto-alias 0.90, auto-merge 0.95, `entity_fragmentation_report`, dispute_queue)
- Remodel 재설계 (D-167 exploit_budget shrinkage 해결)
- F1 확정 (S1-T6 smoke 결과 기반)
- F4 임계치 tuning (L3 결과 기반)
