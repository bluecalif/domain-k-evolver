# Structural Redesign Tasks (SI-P7) — v2

> 작성: 2026-04-21 (v1) / 개정: 2026-04-21 (v2)
> Baseline: POR pain-point → 구조 설계 5축 (S1~S5) + F1~F4 + Q1~Q14 결정
> v2 개정 요지: (a) `docs/phase-next-refactor-task-review_codex.md` 통합, (b) 테스트 3-layer (L1/L2/L3), (c) Entity Discovery Node 구체화 (D-184~D-186), (d) β aggressive mode 정의 (D-181)
> 참고: `docs/session-compact.md`, `docs/core-pipeline-spec-v1.md`, `docs/entity-acquisition-strategy-draft.md`, `C:\Users\User\.claude\plans\ancient-seeking-sphinx.md`, `C:\Users\User\.claude\plans\ok-curious-naur.md`

## 설계 결정 요약 (Q1~Q14)

| ID | 결정 |
|---|---|
| Q1+Q2 | `target_count` 상한 제거, 정렬 제거. cycle upper cap (예: 100) 만 유지. budget 완전 제거 가능성 smoke 로 검증 |
| Q3 | `added_ratio<0.3×3c` 기본 trigger. **aggressive feedback = α + β(aggressive mode)** (D-181) |
| Q4 | condition_split (a) parse prompt + (b) value marker + (c) skeleton `condition_axes` **3중 모두 적용** |
| Q5 | adj risk/utility = **seed 의 category 별 field 의 risk/utility 그대로 재사용** |
| Q6 | `field_adjacency` 는 category 별로 **초기 수작업 seed** → rule engine 으로 운영 (D 참조) |
| Q7 | per-category min = `coverage_map.deficit_score` 동적 |
| Q8 | virtual entity **용어 자체 폐기**. S5 에 의존 |
| Q9 | entity discovery = **매 cycle 실행되는 기본 tool node** |
| Q10 | 승격 기준: `source_count ≥ 2` AND `distinct_domain_count ≥ 2` |
| Q11 | virtual balance-N → S5 로 **대체** |
| Q12 | Explore-Pivot / universe_probe = **계획에서 제거, note 만 남김** |
| Q13 | auto-alias = **자동 임계치** (HITL 없음) |
| Q14 | merge **일단 적용** (remodel 은 별도 재설계 예정, 독립) |

---

## 본 세션 확정 Decisions (D-181 ~ D-188)

### D-181 — F2 aggressive feedback 조합

**선택**: **α (plan query 재작성) + β (aggressive mode)**

- **α**: stagnation 감지 시 plan 의 query template 을 "new concrete entity" intent 로 재작성. LLM 호출 경미 증가, added_ku 증가 효과 큼.
- **β (aggressive mode)**: `added_ratio<0.3×3c` trigger 시 entity_discovery **mode 전환**. D-173 의 "매 cycle 실행" 과 구별되는 **동작 방식 전환**:

| 설정 | 정상 cycle | β aggressive |
|---|---|---|
| discovery target 수 | 1-2개 (deficit 상위) | **3-5개 확장** |
| query 생성 | rule-first template | **LLM-assisted 즉시 활성** |
| candidate 적재 임계 | source_count≥2 AND distinct_domain≥2 (승격 표준) | **source_count≥1 임시 적재** (승격은 표준 유지) |
| 후속 GU 우선순위 | 기본 | **상향** (다음 cycle plan 우선 소진) |
| 지속 기간 | N/A | trigger cycle + **다음 2c** |

**(γ) collect source_strategy 다양화** — Tavily 단일 provider 로 효과 제한, 보류
**(δ) skeleton field 재점검** — 수동 개입, 자동화 어려움, 보류
**(ε) mode upgrade 강화** — 기존 jump mode 중복 가능, 보류

### D-182 — S5a 이번 phase 범위 = **C3-a 전체**

candidate **적재 + 승격 + 후속 GU 자동 오픈** 모두 포함. codex §6 의 "승격 정책은 다음 phase" 제안 **기각**. 이유: S5a loop 미완성 시 F2 β 및 15c trial 측정 불가.

### D-183 — entity_discovery graph 삽입 위치 = **B**

`plan_modify → entity_discovery → plan` (다음 cycle plan 에 반영). candidate 적재 중심 설계에 자연스럽고, plan 이전에 candidate 승격/판정 완료.

### D-184 — discovery target 선정 신호 = **C1-a**

`coverage_map.deficit_score` 를 **S4 와 공유**. 'deficit 높은 category → entity 확장 방향' 으로 재해석. 중복 지표 구축 없음, 응집도 높음.

### D-185 — candidate 수명 정책 = **C2-a**

`candidate` 에 `first_seen_cycle`, `last_seen_cycle` 추가. `last_seen+5c → stale` mark, `+10c → purge`. 재등장 시 `last_seen` 갱신. 메모리 bloat 방지 + 재등장 기회 보장.

### D-186 — 유사 후보 alias pre-filter = **C4-a**

candidate 적재 직전 `entity_resolver.similarity` 검사. **similarity≥0.85 이면 candidate 차단 → alias 제안 경로 (S5b 진입)**. entity_resolver 재사용, S5a/S5b 경계 명확.

### D-187 — 테스트 3-layer + mock 금지

L1 (단위) / L2 (single-cycle e2e) / L3 (15c A/B). **fixture 는 real snapshot 만**, function stub/mock 금지. **L3 만 Gate 공식 판정 근거** (D-34 real-API-first 연장).

### D-188 — Skill 2종 신설

`silver-structural-redesign`, `silver-e2e-test-layering` — 본 plan 및 dev-docs 착수 전 등록.

---

## 파일 네이밍 규칙

- 본 설계 산출 task doc 은 모두 `_CC` suffix 로 끝낸다.
- 예: `structural-redesign-tasks_CC.md` (본 문서), `si-p7-plan_CC.md` 등.
- Commit prefix: `[si-p7] Step X.Y: description`

---

## 권장 착수 순서 (codex §5-7 반영)

```
Step A: S1 (defer/queue) + S2-T1/T2 (integration_result 제어 입력)
        → 제어 루프 복구. 이후 모든 축이 이 루프에 의존.
Step B: S2-T5~T8 (condition_split 재설계) + S3 (adjacent rule engine) + S4 (virtual 즉시 제거)
        → KU/field 품질 개선. low-quality expansion 억제.
Step C: S5a (candidate 적재 + 승격 + 후속 GU, graph 위치 B)
        → entity 유입 경로 개통. D-181 β 측정 가능 시점.
Step D (다음 phase 후보): S5b 전체 정교화 (auto-merge, fragmentation_report)
```

---

## S1 — Target / Collect 자유화 (defer/queue)

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S1-T1 | `_UTILITY_ORDER`/`_RISK_ORDER` 제거, `_select_targets` 정렬 제거 | `src/nodes/plan.py` | -50L |
| S1-T2 | `_select_targets` 가 open_gus 전체 반환 (cycle cap 만 적용) | `src/nodes/plan.py` | +10L |
| S1-T3 | `mode.py::mode_node` target_count 공식 → cycle cap 으로 대체 | `src/nodes/mode.py` | ±30L |
| S1-T4 | **collect.py utility skip 제거 + budget 초과 시 drop 대신 `deferred_targets` 에 기록 (codex §1.1, Draft A-2)** | `src/nodes/collect.py:218-230` | ±30L |
| S1-T5 | budget 재정의: `max_search_calls_per_cycle` config. **초과분은 drop 아니라 defer** | `src/config.py`, `src/nodes/collect.py` | +15L |
| S1-T6 | **Budget 제거 smoke (5c)** — 완전 제거 시 비용/실패율/noise 측정 → F1 결정 | `bench/silver/...` trial | - |
| S1-T7 | regression guard: `target_count` 상한 재도입 방지 테스트 (D-129) | `tests/` | +20L |
| S1-T8 | **신설**: `state.deferred_targets` 필드 + 다음 cycle plan 에서 **우선 소진** (선-FIFO). 메트릭: `executed_targets`, `deferred_targets`, `defer_reason` | `src/state.py`, `src/nodes/plan.py`, `src/utils/metrics.py` | +40L |

**검증 지표**: 실행 GU 수, defer 수 (0 목표 아님 — defer_reason 분포로 판단), API 호출 수, cycle 당 비용, 다음 cycle 에서 defer 소진율

**L2 checkpoint (S1-T4)**: `--cycles 1`, budget 을 고의 낮춰 defer 유발 → `state.deferred_targets` 비어있지 않고 `metrics.deferred_count > 0`.

---

## S2 — KU 병합 피드백 + condition_split 강화

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S2-T1 | **`metrics.py` integration_result 분포 카운터 (per-cycle + 누적) + plan_modify/critique 입력으로 주입 (codex §1.2, Draft B-1)** | `src/utils/metrics.py`, `src/nodes/critique.py`, `src/nodes/plan.py` | +70L |
| S2-T2 | **`added_ratio<0.3×3c` + `conflict_hold 증가` + `condition_split 부재` 3종 trigger → critique `rx_id=ku_stagnation:*`** (codex §7 우선순위 1, 2) | `src/nodes/critique.py` | +50L |
| S2-T3 | **확정 (D-181)**: F2 조합 = α + β(aggressive mode) | design | — |
| S2-T4 | S2-T3 확정안 구현: α query 재작성 (critique rx → plan) + β mode 전환 (entity_discovery 파라미터 override) | `src/nodes/critique.py`, `src/nodes/plan.py`, `src/nodes/entity_discovery.py` | +80L |
| S2-T5 | condition_split (a): parse prompt 에 "조건어 추출" 추가 | `src/nodes/collect.py::_build_parse_prompt` | +15L |
| S2-T6 | **condition_split (b) 재정의: "값 구조 차이" 감지 (axis_tags / conditions / 값 format 단일 vs 범위 vs 옵션셋 비교) → 자동 condition_split (codex §1.2 Phase 2-1)** | `src/nodes/integrate.py::_detect_conflict` | +60L |
| S2-T7 | condition_split (c): `skeleton.fields[].condition_axes` 메타 + 누락 시 강제 | `bench/japan-travel/state/domain-skeleton.json`, `src/nodes/integrate.py` | +40L |
| S2-T8 | **신설**: `existing_ku.axis_tags` vs `claim.axis_tags` 차이 감지 → axis 기반 공존 판정 (condition_split) | `src/nodes/integrate.py` | +40L |

**Plan reason code (codex Draft A-3)**: `collect_defer_excess`, `integration_added_low`, `adjacent_yield_low`, `entity_discovery_insufficient` 추가 → S1-T8, S2-T2, S3-T7, S5a-T7 연동.

**검증 의무**: 각 후보의 효과를 실제 `added_ku` 증가로 확인. 벤치 A/B 필수 (L3).

**L2 checkpoint**:
- S2-T1: `--cycles 3`, distribution 이 state 에 누적 → `state.metrics.integration_distribution` 3-cycle window 관찰
- S2-T6: `--cycles 1`, 조건값 claim 주입 → `integration_result` 에 `condition_split` 출현

---

## S3 — adjacent rule engine

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S3-T1 | `_generate_dynamic_gus` suppress → category 별 `mean × 1.5` | `src/nodes/integrate.py:215-225` | ±20L |
| S3-T2 | state 에 `recent_conflict_fields` 추가, integrate 에서 blocklist 반영 (N=3 cycle) | `src/state.py`, `src/nodes/integrate.py` | +50L |
| S3-T3 | **`domain-skeleton.json` 에 `field_adjacency` rule engine seed (category 별, `{source_field: [next_fields]}` + category override) (codex §1.3 Phase 2-2)** | `bench/japan-travel/state/domain-skeleton.json` | +100L |
| S3-T4 | `_generate_dynamic_gus` 가 `field_adjacency` rule engine 참조 | `src/nodes/integrate.py:231-251` | ±25L |
| S3-T5 | `fields[].default_risk`, `default_utility` (category-scoped) skeleton 추가 | `bench/japan-travel/state/domain-skeleton.json` | +50L |
| S3-T6 | dynamic GU 생성 시 skeleton default 사용, 고정 `medium/convenience` 제거 | `src/nodes/integrate.py:238-251` | ±10L |
| S3-T7 | **신설**: rule yield tracker — 각 adjacency rule 의 최근 N cycle `added` 기여도 집계, **낮은 rule 약화/중지** (codex §1.3 Phase 2-3) | `src/utils/metrics.py`, `src/nodes/integrate.py` | +60L |
| S3-T8 | **신설**: `recent_conflict_fields` 가 N cycle 유지되고, 그 기간 동안 해당 field 는 **source 로도, next 로도** adj 생성 안 함 | `src/nodes/integrate.py` | +30L |

**검증 지표**: conflict field 의 adj 재생성 = 0, suppress 의 category 분포 평탄화, adj 의 risk/utility 분포가 seed 와 일치, `adjacency_yield[rule_id]` 하위 분포 감소

**L2 checkpoint**:
- S3-T4: `--cycles 1`, suppress/allow 관찰 → 생성된 adj GU 의 field 가 seed 맵 내
- S3-T7: `--cycles 5`, 낮은 yield rule 약화 관찰 → `state.metrics.adjacency_yield[rule_id]`

---

## S4 — category_balance (virtual entity 즉시 제거)

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S4-T1 | **virtual `balance-N` entity 생성 전부 제거 (과도기 옵션 없음)** (codex §1.3 Phase 2-5) | `src/nodes/critique.py:249` 주변 | -30L |
| S4-T2 | `MIN_KU_PER_CAT` 상수 제거, `coverage_map.deficit_score` 기반 per-cat 계산 | `src/nodes/critique.py:226-228` | ±40L |
| S4-T3 | field 선택 로직 → S3 `field_adjacency` 참조로 통일 | `src/nodes/critique.py:230-243` | ±25L |
| S4-T4 | S5a entity discovery 결과 연동 — validated entity 대상으로만 balance GU 생성 | `src/nodes/critique.py` | +30L |

**S4-T5 제거** (v1 대비). virtual entity 과도기 skip 옵션은 S5a 가 같은 phase 에 들어오므로 불필요.

**검증 지표**: category 별 KU 분포 Gini 감소, virtual entity 생성 수 = 0

**L2 checkpoint (S4-T1)**: `--cycles 1`, balance GU 없음 확인 → `state.gap_map` 에 `balance-*` 0건.

---

## S5a — Entity Discovery Node (C3-a 전체 범위)

**범위 (D-182)**: candidate 적재 + 승격 + 후속 GU 자동 오픈 **모두 포함**.

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S5a-T1 | `src/state.py` 에 `entity_candidates` 필드 추가 (스키마 아래) | `src/state.py` | +20L |
| S5a-T2 | `domain-skeleton.json` 에 `entity_frame` 스키마 추가 | `bench/japan-travel/state/domain-skeleton.json` | +50L |
| S5a-T3 | **`src/nodes/entity_discovery.py` 신설** — discovery target 결정 (**D-184 `coverage_map.deficit_score` 공유 기준**) | 신규 파일 | +80L |
| S5a-T4 | rule-based query template 구현 (`category+field+geo+source_hint`) | `src/nodes/entity_discovery.py` | +60L |
| S5a-T5 | LLM query 보강 경로 (yield 낮을 때 또는 β mode 시 즉시 활성) | `src/nodes/entity_discovery.py` | +50L |
| S5a-T6 | search 결과 → entity 이름 추출 → **similarity≥0.85 pre-filter (D-186)** → candidate 적재 (그 외는 S5b alias 경로) | `src/nodes/entity_discovery.py`, `src/utils/entity_resolver.py` | +90L |
| S5a-T7 | 승격 판정: `source_count≥2 AND distinct_domain_count≥2 AND category 적합` (표준, β mode 에서도 불변) | `src/nodes/entity_discovery.py` | +60L |
| S5a-T8 | 승격 entity → skeleton.entities 등록 + seed field GU 자동 생성 | `src/nodes/entity_discovery.py`, `src/nodes/integrate.py` | +50L |
| S5a-T9 | **graph.py 에 entity_discovery 노드 삽입 (위치 B: `plan_modify → entity_discovery → plan`)** (D-183) | `src/graph.py` | +10L |
| S5a-T10 | **candidate 수명 정책 (D-185)**: `last_seen+5c → stale`, `+10c → purge`, 재등장 시 `last_seen` 갱신. 정기 scan job | `src/nodes/entity_discovery.py`, `src/utils/metrics.py` | +50L |
| S5a-T11 | **β aggressive mode 파라미터 override (D-181)** 구현 — target 수 확장, LLM query 활성, source_count≥1 임시 적재, GU 우선순위 상향, trigger+2c 지속 | `src/nodes/entity_discovery.py`, `src/nodes/critique.py` | +70L |
| S5a-T12 | 테스트 — 승격 flow, candidate 누적, GU 생성, stale/purge, similarity pre-filter, β mode 검증 | `tests/` | +200L |

**`entity_candidates` 스키마 (D-185 반영)**:

```json
{
  "candidate_id": "str",
  "name": "str",
  "proposed_slug": "str",
  "category": "str",
  "geography": "str | null",
  "candidate_type": "str",
  "source_count": "int",
  "supporting_sources": [{"url": "str", "domain": "str", "cycle": "int"}],
  "first_seen_cycle": "int",
  "last_seen_cycle": "int",
  "status": "active | stale | purged"
}
```

**Graph 삽입 위치 = B (D-183)**: `critique → plan_modify → entity_discovery → plan → collect → integrate`. candidate 적재/승격/수명 scan 이 plan 이전에 완료되어 다음 plan 에 반영.

**검증 지표**: validated entity 승격 수, 신규 entity 파생 KU 수, entity_candidates 누적 품질, stale/purge 비율, similarity pre-filter 차단 건수 (→ S5b alias 경로 진입)

**L2 checkpoint**:
- S5a-T6: `--cycles 3`, candidate 누적 → `state.entity_candidates` 크기 증가, 유사 candidate 는 alias 경로로 전환
- S5a-T7: `--cycles 5`, 2 이상 source candidate → `state.domain_skeleton.entities` 신규 entry
- S5a-T10: `--cycles 12`, 미승격 candidate 의 stale/purge transition 관찰
- S5a-T11: β mode 강제 트리거 후 `--cycles 3`, target 수 3-5 / source_count≥1 적재 확인

---

## S5b — Entity 정규화·통합 (자동, merge 포함)

| ID | Task | 파일 | 예상 변경 |
|---|---|---|---|
| S5b-T1 | `rapidfuzz` (또는 대체) 의존성 추가 | `requirements.txt` | +1L |
| S5b-T2 | `entity_resolver.py` similarity 기반 soft match 함수 + **S5a 와 공유되는 pre-filter API** (D-186) | `src/utils/entity_resolver.py` | +70L |
| S5b-T3 | integrate 중 신규 entity_key 등장 시 similarity 검사 → auto-alias | `src/nodes/integrate.py`, `src/utils/entity_resolver.py` | +50L |
| S5b-T4 | **Duplicate KU detector 강화**: 동일 `(entity, field)` 복수 KU 경고 + confidence merge + **`entity_fragmentation_signals` state 에 누적 → entity_reconcile 이 merge 후보로 평가** (codex §1.4, §2, Phase 4-1) | `src/nodes/integrate.py`, `src/state.py` | +70L |
| S5b-T5 | `src/nodes/entity_reconcile.py` 신설 — auto-merge (similarity≥0.95 AND (confidence gap≥0.2 OR evidence gap≥2)) | 신규 파일 | +100L |
| S5b-T6 | 애매 merge 후보 → dispute_queue 기록 (HITL 없이 다음 cycle 재평가) | `src/nodes/entity_reconcile.py` | +30L |
| S5b-T7 | 테스트 — alias 자동 추가, duplicate 감지, auto-merge, fragmentation 누적 시나리오 | `tests/` | +150L |
| S5b-T8 | **신설**: `entity_fragmentation_report` metric (duplicate / merge_candidate / similarity_dispute 건수) | `src/utils/metrics.py` | +30L |

**임계치 초기 제안 (F4 에서 실 벤치로 tuning)**:
- auto-alias: similarity ≥ 0.90 (S5a pre-filter 0.85 와 구분 — 0.85~0.90 구간은 suggest only)
- auto-merge: similarity ≥ 0.95 AND (confidence gap ≥ 0.2 OR evidence gap ≥ 2)
- dispute 기록: 0.80 ~ 0.89

**검증 지표**: auto-alias 추가 수, duplicate KU 감소, auto-merge 성공률 / 실패율, `fragmentation_report` 3-metric 추이

**L2 checkpoint (S5b-T3)**: `--cycles 1`, 유사 entity claim 주입 → `entity_resolver.aliases` 갱신.

---

## 문서 작업

| ID | Task |
|---|---|
| D-T1 | `docs/session-compact.md` trim (R1~R4 → S1~S5 교체, Explore-Pivot note 축약) |
| D-T2 | `docs/entity-acquisition-strategy-draft.md` → 확정본 승격 (파일명 `-draft` 제거) |
| D-T3 | Q12 반영 — Explore-Pivot note 한 줄만 남기고 제거 |
| D-T4 | 축별 벤치 trial (15c A/B, L3): S1/S2/S3/S4/S5a on-off 비교 — `bench/silver/japan-travel/p7-*` |
| D-T5 | Gate 판정 — 각 축별 effect 측정, D-34 real-API-first 규칙 준수, **L3 만 공식 Gate 근거** (D-187) |

---

## 검증 방식 — 테스트 3-layer (D-187)

**원칙**: **mock 금지** — fixture 는 real snapshot 만, function stub/mock 금지. 실 실행 경로를 검증하지 않는 테스트는 운영 경로 버그를 놓친다 (P3 교훈 / memory: `feedback_test_real_path`).

### 레이어 정의

| 레이어 | 실행 시점 | 목적 | Gate 근거 | mock 허용 |
|---|---|---|---|---|
| **L1 단위** | task 완료 즉시 | 단위 함수 로직 (숫자, 조건 분기) | ❌ | fixture real snapshot 만 (stub 금지) |
| **L2 single-cycle e2e** | task 묶음 완료 | task 가 파이프라인에서 의도한 state 변화 유발하는지 | ❌ | **real API 필수** (D-34) |
| **L3 15c A/B trial** | 축 전체 완료 | before/after metric 비교, 축별 효과 판정 | ✅ **공식 Gate** | **real API 필수** |

### L2 trial-id 규약

- **L2 smoke**: `scripts/run_readiness.py --cycles 1 --trial-id si-p7-<task-id>-smoke`
  - 예: `si-p7-s1-t4-smoke`, `si-p7-s2-t6-smoke`
- **L3 A/B**: `bench/silver/japan-travel/p7-<축>-on/` vs `p7-<축>-off/`
  - 예: `p7-s1-on/` vs `p7-s1-off/`
- 각 L2 는 **고유 trial_id 로 1회만 실행** (memory rule `feedback_api_cost_caution`), artifact 공유 — 중복 실행 금지

### Task 단위 Checkpoint (축별 L2 검증 포인트)

| Task | L1 (단위) | L2 (1c e2e) | 관찰할 artifact |
|---|---|---|---|
| **S1-T4** | `_calc_execution_queue()` defer 반환 | budget 낮춰 defer 유발 | `state.deferred_targets` 비어있지 않음, `metrics.deferred_count > 0` |
| **S2-T1** | `integration_result_distribution()` 정확 집계 | `--cycles 3`, distribution 누적 | `state.metrics.integration_distribution` 3-cycle window |
| **S2-T6** | `_detect_value_shape_diff()` unit | 조건값 claim 주입 | `integration_result` 에 `condition_split` 출현 |
| **S3-T4** | `_generate_dynamic_gus()` 가 `field_adjacency` 참조 | suppress/allow 관찰 | 생성된 adj GU 의 field 가 seed 맵 내 |
| **S3-T7** | rule yield tracker 계산 | `--cycles 5`, 낮은 yield rule 약화 | `state.metrics.adjacency_yield[rule_id]` |
| **S4-T1** | `_generate_balance_gus` 가 virtual entity 생성 안 함 | balance GU 없음 확인 | `state.gap_map` 에 `balance-*` 0건 |
| **S5a-T6** | `entity_candidates` 적재 + similarity pre-filter | `--cycles 3`, candidate 누적 | `state.entity_candidates` 크기 증가 |
| **S5a-T7** | 승격 판정 | `--cycles 5`, 2+ source candidate | `state.domain_skeleton.entities` 신규 entry |
| **S5a-T10** | stale/purge transition | `--cycles 12`, 미승격 candidate | `candidate.status` transitions |
| **S5a-T11** | β mode parameter override | β 강제 trigger + `--cycles 3` | target 수 3-5 / source_count≥1 적재 |
| **S5b-T3** | auto-alias 추가 | 유사 entity claim 주입 | `entity_resolver.aliases` 갱신 |

### Gate 판정 순서 (D-34 + D-187)

1. **L1** (task 완료 직후, 자동) — PR 에 포함, `pytest` 로 green 확인
2. **L2** (task 묶음 완료, 수동 trigger) — 논리 확인용. Gate 판정 **아님**
3. **L3** (축 완료, 15c A/B) — metric before/after 비교. **이것만 Gate 공식 판정 근거**

---

## Critical Files (전체)

### 기존 수정
- `src/nodes/plan.py` (S1, S2 reason code, S5a plan_modify 연동)
- `src/nodes/collect.py` (S1 defer/queue, S2-a parse prompt)
- `src/nodes/mode.py` (S1)
- `src/nodes/integrate.py` (S2 condition_split 재설계, S3 rule engine, S5b)
- `src/nodes/critique.py` (S2 feedback, S4 virtual 즉시 제거, S5a β mode 연동)
- `src/utils/entity_resolver.py` (S5a pre-filter + S5b alias/merge)
- `src/utils/metrics.py` (S2 distribution, S3 yield tracker, S5a candidate 수명, S5b fragmentation)
- `src/state.py` (S1 `deferred_targets`, S3 `recent_conflict_fields`, S5a `entity_candidates`, S5b `entity_fragmentation_signals`)
- `src/config.py` (S1 budget)
- `src/graph.py` (S5a 노드 삽입, 위치 B)
- `bench/japan-travel/state/domain-skeleton.json` (S2 `condition_axes`, S3 `field_adjacency` + `default_risk/utility`, S5a `entity_frame`)

### 신설
- `src/nodes/entity_discovery.py` (S5a)
- `src/nodes/entity_reconcile.py` (S5b)

### 문서
- `docs/session-compact.md` trim (D-T1)
- `docs/entity-acquisition-strategy-draft.md` → 확정본 (D-T2)
- `dev/active/phase-si-p7-structural-redesign/` 신설 (plan/context/tasks/debug-history, 전부 `_CC` suffix)

### Skill (D-188, 본 plan 에서 신설)
- `.claude/skills/silver-structural-redesign/SKILL.md`
- `.claude/skills/silver-e2e-test-layering/SKILL.md`
- `.claude/skills/skill-rules.json` 두 항목 추가

---

## F1~F4 해소 현황

| # | 주제 | 상태 | 비고 |
|---|---|---|---|
| F1 | S1 budget 완전 제거 | **구현 중 결정** | S1-T6 smoke 5c 후 판단 |
| F2 | S2 aggressive feedback | **확정 (D-181)** | α + β(aggressive mode) |
| F3 | S5a entity_discovery graph 위치 | **확정 (D-183)** | 위치 B |
| F4 | S5b auto-alias/merge 임계치 | **구현 중 결정** | 초기값 0.85 pre-filter / 0.90 alias / 0.95 merge, L3 tuning |

---

## 변경 이력

- **v1** (2026-04-21): 최초 작성. 5축 + F1~F4 + Q1~Q14 baseline.
- **v2** (2026-04-21): codex 검토 통합 (defer/queue, rule engine, 제어 입력화), 테스트 3-layer 명시, Entity Discovery 구체화 (D-181~D-188).
