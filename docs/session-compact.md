# Session Compact

> Generated: 2026-04-22
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 S3 완료 → Step A/B L3 bench trial 실행 → 결과 분석 → 다음 액션 확정.

---

## Completed

- [x] **S3 integrate.py 마무리**: return dict에 `recent_conflict_fields`, `adjacency_yield` 추가; 중복 `cycle` 변수 제거
- [x] **S3 L1 테스트 19개**: `TestGetAdjacencyFields`(4), `TestGetFieldDefaults`(3), `TestGenerateDynamicGusS3`(7), `TestConflictBlocklistStateFlow`(3), `TestAdjacencyYieldStateFlow`(2) — 926 passed
- [x] **S3 커밋**: `2d252f3`
- [x] **step-update**: tasks_CC/plan_CC/context_CC/session-compact 동기화 — `ee93a11`, push
- [x] **L3 bench trial p7-ab-on** (15c): P7 A+B 전체 on — FAIL (GU 고갈 확인)
- [x] **L3 bench trial p7-ab-off** (15c): P7 이전 baseline — PASS
- [x] **D-189 확정**: S5a = critical path blocker. S4-T3 건너뛰고 S5a 우선 착수
- [x] **결과 커밋/푸시**: `2c54001` — INDEX.md + trial 데이터

---

## Current State

**브랜치**: `main` (최신 커밋 `2c54001`)
**테스트**: 926 passed, 3 skipped

### L3 비교 요약

| 지표 | ON (P7 A+B) | OFF (baseline) |
|------|-------------|----------------|
| gate | FAIL | PASS |
| KU@c15 | 82 (c3부터 정체) | 141 |
| GU open@c15 | 0 | 117 |
| late_discovery | 0 | 21 |
| min_ku_per_cat | 4 | 8 |
| gap_resolution | 1.0 (misleading) | 0.88 |

**Root cause (D-189)**: cycle 3 이후 `open=0` → `target_count=0` → collect 미실행 → c4~c15 idle spin.
- S4-T1(balance-* 제거): 탐색 GU 공급원 제거
- S3(field_adjacency 제한): adj GU 생성량 감소
- S5a 미구현: entity discovery 대체 경로 없음

### state.py 신규 필드 (이번 phase)

```python
deferred_targets: list[str]        # S1-T8
defer_reason: dict                  # S1-T8
integration_result_dist: dict       # S2-T1
ku_stagnation_signals: dict         # S2-T2
aggressive_mode_remaining: int      # S2-T4
recent_conflict_fields: list[dict]  # S3-T2
adjacency_yield: dict               # S3-T7
```

### 완료된 커밋 이력 (이번 phase)

| 커밋 | 내용 |
|------|------|
| `a6bc80e` | S1-T1~T3 |
| `97e2ef5` | S1-T4 |
| `defc3a0` | S1-T5 |
| `2db7448` | S1-T7 |
| `4e5988c` | S1-T8 |
| `6b8d9d2` | S1-T6 smoke |
| `7bd9f2b` | S2-T1 |
| `c6ba740` | S2-T2 |
| `87d7603` | S2-T4 |
| `f3a0be0` | S2-T5~T8 |
| `2631c38` | S4-T1/T2 |
| `2d252f3` | S3-T1~T8 |
| `ee93a11` | docs: Step A/B 완료 체크 |
| `2c54001` | L3 bench p7-ab-on/off |

---

## Remaining / TODO

### 즉시 착수 (다음 세션)

- [ ] **S5a-T1**: `state.py`에 `entity_candidates: list[dict]` 필드 추가
  - 스키마: `{candidate_id, entity_key, category, source_count, distinct_domain, first_seen_cycle, last_seen_cycle, status, queries}`
- [ ] **S5a-T2**: `domain-skeleton.json`에 `entity_frame` 스키마 추가
- [ ] **S5a-T3**: `src/nodes/entity_discovery.py` 본격 구현 (현재 stub: aggressive_mode_remaining 감소만)
  - discovery target = `coverage_map.deficit_score` 공유 (D-184)
- [ ] **S5a-T4**: rule-based query template (`category+field+geo+source_hint`)
- [ ] **S5a-T5**: LLM query 보강 (β mode 즉시 활성)
- [ ] **S5a-T6**: search → entity 이름 추출 → similarity≥0.85 pre-filter → candidate 적재
- [ ] **S5a-T7**: 승격 판정 (`source_count≥2 AND distinct_domain≥2 AND category 적합`)
- [ ] **S5a-T8**: 승격 → skeleton 등록 + seed GU 자동
- [ ] **S5a-T9**: `src/graph.py` entity_discovery 노드 삽입 (위치 B: plan_modify → entity_discovery → plan)
- [ ] **S5a-T10**: candidate 수명 (`last_seen+5c stale`, `+10c purge`)
- [ ] **S5a-T11**: β aggressive mode 전체 구현 (S2-T4 β와 연동)
- [ ] **S5a-T12**: 테스트 일체 (L1)

### 이후

- [ ] S5a L3 재시험: `p7-abc-on` (A+B+C 통합)
- [ ] S4-T3 (선택적): plan field selection → field_adjacency 참조
- [ ] S4-T4: S5a validated entity 대상 balance GU
- [ ] D-T1~T5: docs 정리 + phase gate

---

## Key Decisions

- **D-189**: S5a = critical path blocker. S4-T1+S3이 GU 공급원을 제거했으나 S5a 없이 대체 경로 없음. S4-T3 건너뛰고 S5a-T1~T12 우선 착수. S5a 완료 후 p7-abc-on 재시험.
- **S3 field_adjacency**: category override > _global fallback. 미정의 시 skeleton categories 기반 전체 applicable 사용 (fallback 존재)
- **S4 balance-* 완전 제거**: C1 502s 병목 원인 제거 → S5a validated entity로 대체
- **L3 trial 방식**: p7-ab-on/off 통합 1쌍 (비용 절감)

---

## Context

다음 세션에서는 한국어를 사용하세요.

### 진입점 — 읽기 우선순위

1. `docs/structural-redesign-tasks_CC.md` v2 — 단일 진실 소스 (S5a 스펙: Step C 섹션)
2. `dev/active/phase-si-p7-structural-redesign/si-p7-tasks_CC.md` — checklist
3. `src/nodes/entity_discovery.py` — 현재 stub 확인 후 본격 구현

### S5a 관련 코드 경로

- `src/nodes/entity_discovery.py` — stub (aggressive_mode_remaining 감소만 구현됨)
- `src/graph.py` — 위치 B (plan_modify → entity_discovery → plan) 삽입 필요
- `src/state.py` — `entity_candidates` 필드 추가 필요
- `bench/japan-travel/state/domain-skeleton.json` — `entity_frame` 스키마 추가 필요
- `src/utils/entity_resolver.py` — similarity 계산 (S5a-T6 pre-filter용)

### D-189 요약 (L3 결과)

```
ON (P7 A+B): GU open=0 at cycle3 → mode target_count=0 → collect skip → KU=82 정체 c4~c15
OFF (baseline): KU=141, GU=117 정상 성장
원인: S4-T1(balance-* 제거) + S3(adj 제한) → GU 고갈
해결: S5a Entity Discovery → 신규 concrete entity GU 지속 공급
```

---

## Next Action

**S5a-T1 착수**: `src/state.py`에 `entity_candidates: list[dict]` 필드 추가 후 S5a-T2 skeleton `entity_frame` → S5a-T3 entity_discovery.py 본격 구현 순서로 진행.

`src/nodes/entity_discovery.py` 현재 stub 먼저 읽고, `docs/structural-redesign-tasks_CC.md` Step C 섹션(S5a) 확인 후 T1부터 순서대로 구현 시작.
