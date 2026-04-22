# Session Compact

> Generated: 2026-04-22
> Source: step-update 후 갱신

## Goal

SI-P7 Step B 완료 → Step C (S5a Entity Discovery) 착수.

---

## Completed

### Step A — 제어 루프 복구

- [x] **S1-T1~T3**: target 자유화 (`_UTILITY_ORDER` 제거, cycle cap만 적용) — `a6bc80e`
- [x] **S1-T4**: collect utility skip 제거 + budget 초과 → `deferred_targets` 기록 — `97e2ef5`
- [x] **S1-T5**: `max_search_calls_per_cycle` config, 초과 defer — `defc3a0`
- [x] **S1-T6**: budget smoke 5c — F1=budget 유지 결정 — `6b8d9d2`
- [x] **S1-T7**: D-129 regression guard 테스트 — `2db7448`
- [x] **S1-T8**: `deferred_targets` FIFO 소진 + `defer_reason` telemetry — `4e5988c`
- [x] **S2-T1**: `integration_result_dist` state 승격 + critique/plan 제어 입력화 — `7bd9f2b`
- [x] **S2-T2**: `ku_stagnation_signals` + 3종 trigger (added_low, conflict_rising, no_condition_split) — `c6ba740`

### Step B — KU/field 품질 개선

- [x] **S2-T3**: D-181 설계 결정 확정 (구현 불필요)
- [x] **S2-T4**: F2 α+β (plan query 재작성 + `aggressive_mode_remaining`) — `87d7603`
- [x] **S2-T5~T8**: condition_split 강화 4경로 — `f3a0be0`
  - T5: parse prompt 조건어 추출
  - T6: 값 구조 차이 자동 split (`_value_structure_type`)
  - T7: `skeleton.condition_axes` 강제 split
  - T8: axis_tags geography 차이 → split
- [x] **S4-T1**: `_generate_balance_gus` → 항상 `[]` (virtual entity 완전 제거) — `2631c38`
- [x] **S4-T2**: `_identify_deficit_categories` (deficit_score > 0.5 기반) — `2631c38`
- [x] **S3-T1~T8**: adjacent rule engine 전면 재작성 — `2d252f3`
  - T1: category mean×1.5 suppress
  - T2/T8: conflict blocklist (N=3 cycle, source+next 양쪽)
  - T3: `field_adjacency` skeleton seed
  - T4: rule engine 참조
  - T5/T6: skeleton default_risk/default_utility
  - T7: `adjacency_yield` tracker (rule_id별 attempted/resolved)

---

## Current State

**브랜치**: `main` (모두 커밋됨)
**테스트**: 926 passed, 3 skipped
**최신 커밋**: `2d252f3`

### state.py 신규 필드 (이번 phase)

```python
deferred_targets: list[str]       # S1-T8: FIFO defer queue
defer_reason: dict                 # S1-T8: {reason: count}
integration_result_dist: dict      # S2-T1: per-cycle + history
ku_stagnation_signals: dict        # S2-T2: added/conflict_hold/condition_split history
aggressive_mode_remaining: int     # S2-T4: β mode countdown
recent_conflict_fields: list[dict] # S3-T2: [{field, since_cycle}]
adjacency_yield: dict              # S3-T7: {rule_id: [{cycle, attempted, resolved}]}
```

---

## Remaining / TODO

### 즉시 착수 (다음 세션)

- [ ] **S4-T3**: plan field 선택 → `field_adjacency` 참조로 통일
  - `src/nodes/plan.py` `_build_plan_from_targets` 에서 adjacent field 우선 선택
  - skeleton `field_adjacency` 참조

- [ ] **S5a-T1~T12**: Entity Discovery Node 전체 구현
  - T1: `state.entity_candidates` 필드 + 스키마
  - T2: `domain-skeleton.json` `entity_frame` 스키마
  - T3: `src/nodes/entity_discovery.py` 신설 (현재 stub 존재)
  - T4: rule-based query template
  - T5: LLM query 보강 (β mode 즉시 활성)
  - T6: search → entity 추출 → similarity≥0.85 pre-filter → candidate 적재
  - T7: 승격 판정 (source_count≥2, distinct_domain≥2)
  - T8: 승격 → skeleton 등록 + seed GU 자동
  - T9: `src/graph.py` entity_discovery 노드 삽입 (위치 B)
  - T10: candidate 수명 (last_seen+5c stale, +10c purge)
  - T11: β aggressive mode 전체 구현 (S2-T4 β와 연동)
  - T12: 테스트 일체

### 이후

- [ ] Step A/B L3 검증 (15c A/B bench trial)
- [ ] S4-T4: S5a validated entity 대상 balance GU
- [ ] D-T1~T5: docs 정리 + phase gate

---

## Key Decisions (이번 phase)

- **D-181**: F2 = α (query 재작성) + β (aggressive_mode_remaining=3, entity_discovery와 연동)
- **S3 field_adjacency**: category override > _global fallback. 미정의 시 skeleton categories 기반 전체 적용
- **S4 balance-* 완전 제거**: virtual entity GU가 C1 502s 병목의 원인 → 즉시 제거, S5a validated entity로 대체
- **S2 condition_split 4경로**: parse/구조차이/condition_axes/axis_tags 모두 합산

---

## Context

다음 세션에서는 한국어를 사용하세요.

### 진입점 — 읽기 우선순위

1. `docs/structural-redesign-tasks_CC.md` v2 — 단일 진실 소스
2. `dev/active/phase-si-p7-structural-redesign/si-p7-tasks_CC.md` — checklist
3. `src/nodes/entity_discovery.py` — 현재 stub (S5a 착수 전 확인)

### S4-T3 관련 코드 경로

- `src/nodes/plan.py` `_build_plan_from_targets` — field 선택 로직
- `bench/japan-travel/state/domain-skeleton.json` `field_adjacency` — 참조 대상

### S5a 관련 코드 경로

- `src/nodes/entity_discovery.py` — stub 존재 (aggressive_mode_remaining 감소만)
- `src/graph.py` — 위치 B (plan_modify → entity_discovery → plan) 삽입 필요
- `src/state.py` — `entity_candidates` 필드 추가 필요

## Next Action

1. S4-T3: `plan.py` field 선택에 `field_adjacency` 참조 추가 (skeleton에서 adjacent field 우선)
2. S5a-T1: `state.py`에 `entity_candidates` 필드 추가
3. S5a-T2: skeleton `entity_frame` 스키마 추가
4. S5a-T3~T12: entity_discovery.py 전체 구현
