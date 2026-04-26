# Session Compact

> Generated: 2026-04-26
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 Stage B-1 Extension S3-T9~T14 구현 완료 → L1 테스트 추가 → 847+N tests PASS → S3 GU Gate smoke trial 통과.

## Completed

- [x] `integrate.py` S3-T9 Bug A: `_generate_dynamic_gus` 시그니처 변경
  - `open_count` 제거, `canonical_entity_key: str | None = None` 추가
  - `entity_key = canonical_entity_key or claim.get("entity_key", "")`
- [x] `integrate.py` S3-T9 Bug B: `existing_ku_slots` 파라미터 추가 → `existing_slots |= existing_ku_slots`
- [x] `integrate.py` S3-T13: `field_adjacency` lookup 브랜치 삭제 → `adj_candidates = applicable_fields`
- [x] `integrate.py` S3-T14: `_compute_dynamic_gu_cap(mode)` 고정 (normal=8, jump=20), `open_count` 의존 제거
- [x] `integrate.py` S3-T10: post-cycle new-KU adj sweep 추가 (claim loop 이후 `adds` 기반)
- [x] `integrate.py` 호출부 업데이트: `canonical_entity_key=entity_key`, `existing_ku_slots=_ku_slots` 전달
- [x] `integrate.py` `from math import ceil` 제거 (불필요)
- [x] `integrate.py` `open_count = sum(...)` 변수 제거 (S3-T14로 불필요)
- [x] `seed.py` `WILDCARD_PARALLEL_FIELDS` 상수 추가 (S3-T11)
- [x] `seed.py` `_get_per_category_cap` 함수 삭제 (S3-T12)
- [x] `seed.py` `n_categories`, `per_cat_cap`, `cat_counts` 제거 (S3-T12)
- [x] `seed.py` entity-specific 브랜치에 wildcard 병행 생성 추가 (S3-T11)
- [x] `seed.py` capped 루프 삭제 → `deduped` 직접 사용, 최소 커버리지 `cats_covered` 기반으로 변경 (S3-T12)
- [x] `tests/test_nodes/test_seed.py`: `_get_per_category_cap` import 제거
- [x] `tests/test_nodes/test_integrate.py`: 모든 `_generate_dynamic_gus(..., "normal", 5)` → `(..., "normal")` 수정 (7군데)
- [x] `tests/test_nodes/test_integrate.py`: `TestFieldAdjacencyRuleEngine` 클래스 docstring 업데이트

## Current State

- **Branch**: `feature/si-p7-rebuild`
- **테스트**: 마지막 실행 직전 중단됨 — `open_count=5` 인자 수정 완료 직후
- **아직 미확인**: 전체 pytest 통과 여부
- **미완료 테스트 수정**: `TestFieldAdjacencyRuleEngine.test_uses_adjacency_map_when_present` 기대값 업데이트 필요

### Changed Files (this session)

- `src/nodes/integrate.py` — S3-T9/T10/T13/T14 모두 적용
- `src/nodes/seed.py` — S3-T11/T12 적용
- `tests/test_nodes/test_seed.py` — `_get_per_category_cap` import 제거
- `tests/test_nodes/test_integrate.py` — 호출부 + docstring 수정

### 주요 코드 위치

```
src/nodes/integrate.py
  line ~175: _generate_dynamic_gus (S3-T9 Bug A/B + S3-T13 적용)
  line ~279: _compute_dynamic_gu_cap (S3-T14 적용, mode만)
  line ~307: integrate_node (open_count 변수 제거)
  line ~556: 호출부 (canonical_entity_key, existing_ku_slots 전달)
  line ~570: S3-T10 sweep 블록

src/nodes/seed.py
  line ~38: WILDCARD_PARALLEL_FIELDS 상수
  line ~284: S3-T11 wildcard 병행 생성
  line ~328: S3-T12 최소 커버리지 (cats_covered 기반)
```

## Remaining / TODO

### 즉시 처리 (다음 액션)

- [ ] **테스트 수정**: `TestFieldAdjacencyRuleEngine.test_uses_adjacency_map_when_present` 기대값 업데이트
  - S3-T13 후 behavior: `field_adjacency` 무시 → applicable_fields 전체 사용
  - claim: `{entity_key: "d:transport:jr-pass", field: "price"}`
  - `_SKELETON_WITH_MAP` applicable fields (transport): `{price, tips, how_to_use, where_to_buy}`
  - price 제외 → adj GUs: `{tips, how_to_use, where_to_buy}`
  - 기존 기대: `fields == {"how_to_use", "tips"}` → 신규 기대: `fields == {"tips", "how_to_use", "where_to_buy"}`
- [ ] **전체 pytest 통과 확인** (`python -m pytest -q`)
- [ ] **L1 테스트 추가** (S3-T9~T14용 — `tests/test_nodes/test_integrate.py`, `tests/test_nodes/test_seed.py`)

### L1 테스트 목록 (추가 대상)

**test_integrate.py** (S3-T9, T10, T13, T14):
- `test_adj_gu_uses_canonical_entity_key` — canonical_entity_key 파라미터 사용 확인
- `test_adj_gu_skips_existing_ku_slot` — existing_ku_slots 병합으로 중복 방지
- `test_new_ku_sweep_creates_adj_gus` — adds 기반 sweep에서 adj GU 생성
- `test_sweep_respects_cap` — sweep이 dynamic_cap 공유
- `test_sweep_deduplicates` — 동일 entity 중복 sweep 방지
- `test_adj_gu_uses_all_applicable_fields_not_adjacency_list` — S3-T13: field_adjacency 무시
- `test_dynamic_cap_fixed_normal_8` — normal mode cap=8
- `test_dynamic_cap_fixed_jump_20` — jump mode cap=20
- `test_dynamic_cap_not_open_count_dependent` — open_count 변화 무관

**test_seed.py** (S3-T11, T12):
- `test_seed_also_creates_wildcard_for_entity_specific_fields` — entity-specific 시 wildcard 병행
- `test_seed_no_per_cat_cap_regulation_price_included` — per_cat_cap 제거로 regulation+price 모두 포함
- `test_seed_no_per_cat_cap_regression` — 기존 cap으로 누락됐던 슬롯이 이제 포함

### 이후

- [ ] S3 GU Gate smoke trial (`bench/silver/japan-travel/p7-rebuild-s3-gu-smoke/`)
  - G1: adj GU 생성 전 cycle 없음
  - G2: entity-specific adj GU ≥ 5 (5c 누계)
  - G3: c2/c3 adj_gen ≥ c1 (chain propagation)
  - G4: regulation GU ≥ 1, attraction ku_only ≥ 3
  - G5: conflict 재생성=0, balance-*=0, adj_yield avg ≥ 0.3, KU c5 ≥ 65
- [ ] step-update 커밋 (S3-T9~T14 완료)
- [ ] Stage B-3: S2-T3~T8 (condition_split 보수화)

## Key Decisions

- **D-203** S3-T9 Bug A: `_generate_dynamic_gus`에 `canonical_entity_key` 파라미터 추가 (기존 `open_count` 위치 인자 제거)
- **D-204** S3-T10: claim loop 이후 `adds` 기반 new-KU adj sweep (entity dedup 포함)
- **D-205** S3-T11: `WILDCARD_PARALLEL_FIELDS = {price, duration, how_to_use, acceptance, where_to_buy}` — entity-specific 후 wildcard 병행
- **D-206** S3-T12: `_get_per_category_cap` 삭제, `deduped` 직접 사용, 최소 커버리지만 유지
- **D-207** S3-T13: `field_adjacency` lookup 완전 제거 → `adj_candidates = applicable_fields`
- **D-208** S3-T14: `_compute_dynamic_gu_cap(mode)` 고정 (normal=8, jump=20)

## Context

### TestFieldAdjacencyRuleEngine 수정 상세

```python
# _SKELETON_WITH_MAP 기준
# claim: entity_key="d:transport:jr-pass", field="price"
# applicable_fields (transport): [price, tips, how_to_use, where_to_buy]
# adj_candidates = applicable_fields (S3-T13: field_adjacency 무시)
# price == claim.field → skip
# → GUs: {tips, how_to_use, where_to_buy}

# test_uses_adjacency_map_when_present 수정:
# OLD: assert fields == {"how_to_use", "tips"}
# NEW: assert fields == {"tips", "how_to_use", "where_to_buy"}
```

### 구현 순서 검증

S3-T9 → T13 → T14 → T10 (integrate.py) → T11 → T12 (seed.py) 순서 완료.

### 테스트 현황

중단 직전: 310 passed, 1 failed (`test_uses_adjacency_map_when_present` — open_count 수정 후 재확인 필요)
→ 실제 실패는 `test_uses_adjacency_map_when_present`의 기대값 불일치 (S3-T13 행동 변화)

다음 세션에서는 답변에 한국어를 사용하세요.

## Next Action

**즉시**: `TestFieldAdjacencyRuleEngine.test_uses_adjacency_map_when_present` 기대값 수정

```python
# 수정 위치: tests/test_nodes/test_integrate.py
# test_uses_adjacency_map_when_present 함수
# OLD:
assert fields == {"how_to_use", "tips"}, (
    f"field_adjacency['price'] 대로만 생성돼야 함, got {fields}"
)
assert "where_to_buy" not in fields, "adjacency map에 없는 where_to_buy는 생성되지 않아야 함"

# NEW (S3-T13 후: applicable_fields 전체 사용):
assert fields == {"tips", "how_to_use", "where_to_buy"}, (
    f"S3-T13 후 field_adjacency 제거 → applicable_fields 전체 사용, got {fields}"
)
```

그 후 `python -m pytest -q` 전체 통과 확인 → L1 테스트 추가 → pytest 재확인 → 커밋.
