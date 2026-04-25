# Session Compact

> Generated: 2026-04-25
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 rebuild Stage B 계속 진행. S3 Axis (Stage B-1/B-2) 완료 → S3 Axis Gate PASS → Stage B-3 (S2-T3~T8) 착수 준비.

---

## Completed

### S3-T3: field_adjacency rule engine seed

- [x] `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json` 에 `field_adjacency` 추가
  - 11개 field → 2~3 next_fields (japan-travel 도메인 기반)
  - `price→[how_to_use,where_to_buy,tips]`, `policy→[eligibility,how_to_use,tips]`, `location→[hours,tips]` 등
  - commit `d9dad76`

### S3-T4: _generate_dynamic_gus rule engine 참조

- [x] `src/nodes/integrate.py`: `field_adjacency[claim.field]` 우선, `applicable_fields` 교집합으로 category 제약, fallback 기존 방식
- [x] **L1**: `TestFieldAdjacencyRuleEngine` 3 cases ✓
- [x] **L2**: `si-p7-s3-t4-smoke` (1c) — adj GU 5건 모두 field_adjacency 값 내, balance-* 0, KU 13→24
  - commit `d9dad76`

### S3-T5: fields[].default_risk / default_utility skeleton 추가

- [x] 11개 field에 `default_risk` / `default_utility` 추가
  - price/acceptance → financial/high | policy/eligibility → policy/high
  - how_to_use → convenience/high | tips/duration → informational/medium
  - hours/location/etiquette/where_to_buy → convenience/medium
  - commit `e38c01e`

### S3-T6: dynamic GU skeleton default 참조

- [x] `_generate_dynamic_gus`: `field_defaults` 맵으로 adj field별 default 조회
  - 기존 `"medium"/"convenience"` 하드코딩 제거
  - fallback: skeleton default 없으면 "medium"/"convenience" 유지
- [x] **L1**: `TestSkeletonFieldDefaults` 2 cases ✓ (843 passed)
  - commit `e38c01e`

### S3-T7: adjacency_yield 트래커

- [x] `src/state.py`: `adjacency_yield: list[dict]` 추가
- [x] `src/nodes/integrate.py`: `adj_yield = adj_resolved / max(adj_open_at_start, 1)` 매 cycle 누적 (최근 10c)
- [x] `src/utils/state_io.py`: `adjacency-yield.json` → `_OPTIONAL_LIST_FILES` 등록 (snapshot 포함)
- [x] `src/obs/telemetry.py`: `_latest_adj_yield()` + `adjacency_yield` 키 추가
- [x] `schemas/telemetry.v1.schema.json`: `adjacency_yield` 필드 추가
- [x] **L1**: `TestAdjacencyYieldTracker` 3 cases ✓
- [x] **L2**: S3 Axis Gate (5c) 와 합산 검증 — 5c avg=0.500 >> 0.05 ✓
  - commit `d381f9a`, `77c658d`

### S3-T8: blocklist source/next 양쪽 배제

- [x] `_generate_dynamic_gus`: `claim.field in blocklist_fields` → 즉시 `[]` 반환 (source 배제)
  - S3-T2(next 차단) + S3-T8(source 차단) 합산으로 conflict field 완전 억제
- [x] **L1**: `test_source_field_blocklisted_skips_all_adj` ✓ (847 passed)
  - commit `d381f9a`

### S3 Axis Gate (5c smoke) ✅ PASS

- [x] `bench/silver/japan-travel/p7-rebuild-s3-smoke/` (5c real API)
  - KU c5=79 (기준 ≥70 ✓)
  - GU_open c3=10 (기준 ≥5 ✓) — attempt-1 collapse 없음
  - target_count c5=2 (조건부 ✓ — GU 2개만 남아 수렴, not collapse)
  - conflict field 재생성=0, balance-*=0
  - adjacency_yield 5 entries, 5c avg=0.500 ✓
  - commit `77c658d`

---

## Current State

- **브랜치**: `feature/si-p7-rebuild`
- **최신 commit**: `77c658d`
- **테스트**: 847 passed, 3 skipped
- **Stage A**: 완료
- **Pre-Stage B (S4-T1)**: 완료
- **Stage B-1/B-2 (S3 전체)**: **완료** — S3 Axis Gate PASS
- **다음**: Stage B-3 (S2-T3~T8)

### Changed Files (this session)

| 파일 | 변경 |
|---|---|
| `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json` | field_adjacency + default_risk/utility 추가 |
| `src/nodes/integrate.py` | S3-T4(rule engine) + S3-T6(default) + S3-T7(yield tracker) + S3-T8(source blocklist) |
| `src/state.py` | `adjacency_yield: list[dict]` 추가 |
| `src/utils/state_io.py` | adjacency-yield.json → _OPTIONAL_LIST_FILES |
| `src/obs/telemetry.py` | adjacency_yield 추가 |
| `schemas/telemetry.v1.schema.json` | adjacency_yield 필드 추가 |
| `tests/test_nodes/test_integrate.py` | S3-T4/T6/T7/T8 테스트 추가 |
| `dev/active/phase-si-p7-structural-redesign/si-p7-tasks.md` | S3-T3~T8 + Gate 완료 마킹 |
| `bench/silver/japan-travel/p7-s3-t4-smoke/` | S3-T4 1c smoke 결과 |
| `bench/silver/japan-travel/p7-rebuild-s3-smoke/` | S3 Axis Gate 5c smoke 결과 |

---

## Remaining / TODO

### Stage B-3 (S2-T3~T8) — condition_split 재정의

> **사전 작업**: S2-T6 시작 직전 V-T11 cherry-pick — `git cherry-pick f61c864` (config.py + integrate.py + tests)

- [ ] **S2-T3** F2 = α + β 확정 (D-181 design only, 구현 불필요)
- [ ] **S2-T4** F2 구현 — α (query 재작성) + β (aggressive mode, S5a-T11 동반)
- [ ] **S2-T5** condition_split (a): parse prompt "조건어 추출"
- [ ] **S2-T6 (보수화)** "값 구조 차이" 감지 → condition_split (임계: ≥2 chars, set/range 변환 시 명시적 marker)
- [ ] **S2-T7 (보수화)** skeleton.fields[].condition_axes 강제 (임계: conditions 필드 비어있지 않을 때)
- [ ] **S2-T8 (보수화)** axis_tags 차이 → condition_split (임계: 단일 axis 차이만)

### S2 Axis Gate (5c smoke)

```
trial: bench/silver/japan-travel/p7-rebuild-s2-smoke/
PASS 기준:
- c1 ΔKU ≤ +35
- GU 양산 ≥ 65
- KU c5 ≥ 90
- adj_gen: c3+ 0 cycle 없음
FAIL 시: V-T11 토글로 narrowing
```

### Stage B-4 (S4-T2~T4)

- [ ] S4-T2: coverage_map.deficit_score 카테고리 결핍 계산
- [ ] S4-T3: field 선택 → S3 field_adjacency 통일
- [ ] S4-T4: S5a validated entity 대상만 balance GU

### Stage C (S5a), Stage D (15c L3)

---

## Key Decisions

### 이번 세션 확정

- **S3-T7 L2 합산**: S3-T7 5c smoke를 S3 Axis Gate와 합산 → API 비용 절감
- **field_adjacency 설계**: 11개 field → 2~3 next_fields, category constraint 교집합 필터 필수
- **adjacency_yield 저장**: _OPTIONAL_LIST_FILES 등록 + telemetry emit → 검증 가능성 확보
- **S3 Gate 판정**: c5 targets=2는 healthy convergence (GU 2개 남음), attempt-1 collapse(targets=0)와 구별 → 조건부 PASS

### 이전 세션에서 유지

- **Option B**: Pre-B(S4-T1) → S3 → S2 → S4-T2~T4 순서
- **D-129/F1**: target_count cap/budget 재도입 금지
- **S2-T6 V-T11**: `git cherry-pick f61c864` 사전 적용 필요

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### S2-T3~T8 설계 사전 정보

- **V-T11**: S2-T6 시작 전 cherry-pick 필요 (`git cherry-pick f61c864`)
  - config.py + integrate.py + tests — condition_split toggle 인프라
- **F2 = α + β**:
  - α: critique rx에서 plan으로 query 재작성 파라미터 전달
  - β: aggressive mode entity_discovery 파라미터 override (S5a-T11 동반 구현)
- **condition_split 보수화 임계**:
  - S2-T6: existing/claim 모두 ≥ 2 chars, set/range 변환 시 명시적 marker
  - S2-T7: claim.conditions 필드 비어있지 않을 때만
  - S2-T8: 단일 axis 차이만 (geography), 다중 axis 차이는 hold

### S3 Axis Gate 최종 비교

| trial | KU c5 | GU_open c3 | adj_yield avg | balance-* |
|---|---|---|---|---|
| p7-rebuild-s3-smoke | 79 | 10 | 0.500 | 0 ✓ |
| s3-attempt-1 (reference) | 61 | 0 (collapse) | N/A | N/A |

### 제약

- **D-129**: target_count cap 재도입 금지
- **D-34**: real API 필수
- **D-200**: per-axis 5c gate 통과 전 다음 axis 진입 금지
- **F1**: budget 재도입 금지

### 최근 commits

- `77c658d` [si-p7] S3 Axis Gate PASS + adjacency_yield 저장/telemetry
- `d381f9a` [si-p7] S3-T7/T8: adjacency_yield 트래커 + source/next blocklist
- `e38c01e` [si-p7] S3-T5/T6: field default_risk/default_utility + adj GU 적용
- `d9dad76` [si-p7] S3-T3/T4: field_adjacency rule engine seed + 참조 구현

---

## Next Action

**두 가지 작업을 병행 착수**:

### 1. Entity-Field Matrix 검증 (field coverage 확인)

`p7-rebuild-s3-smoke` 5c 결과를 기반으로 현재 KU 79개의 entity × field 매트릭스를 구성해 coverage 확인:

1. `bench/silver/japan-travel/p7-rebuild-s3-smoke/state-snapshots/cycle-5-snapshot/knowledge-units.json` 읽기
2. entity_key (category:slug) × field 매트릭스 출력
3. 빈 셀(gap) 확인 — 어떤 entity의 어떤 field가 아직 미수집인지
4. skeleton `field_adjacency` 설계와의 정합성 확인 (adj GU가 실제로 유용한 필드를 탐색했는지)

### 2. Stage B-3 S2-T3 착수

- S2-T3: F2 = α + β 확정 (design only)
  - `dev/active/phase-si-p7-structural-redesign/` 의 context 파일 확인
  - α/β 설계 결정사항 문서화
