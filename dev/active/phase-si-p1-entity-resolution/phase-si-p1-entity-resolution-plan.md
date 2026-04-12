# Silver P1: Entity Resolution & State Safety
> Last Updated: 2026-04-12
> Status: Complete (12/12, 544 tests, S4/S5/S6 pass)
> Source: `docs/silver-masterplan-v2.md` §4 P1, `docs/silver-implementation-tasks.md` §5

---

## 1. Summary (개요)

**목적**: 구조적 무결성 — alias/is_a 해상도 + conflict ledger 영구 보존.

현재 `integrate.py._find_matching_ku` 는 entity_key exact match 만 수행하므로, 동의어(`JR-Pass` / `재팬레일패스`) 나 is_a 계층(`shinkansen` is_a `train`) 을 인식하지 못해 중복 KU 가 생성된다. 또한 dispute 해결 후 conflict 이력이 사라져 감사가 불가능하다.

**범위**:
- `entity_resolver.py` [NEW] — alias/is_a/canonicalize 해석 계층
- `integrate.py` — resolver 경유 매칭으로 전환
- `conflict_ledger` 영속화 (state_io + integrate + dispute_resolver)
- skeleton `aliases`/`is_a` validator 확장
- japan-travel skeleton 에 alias/is_a 예시 추가

**예상 결과물**: P0 baseline 대비 중복 KU ≥ 15% 감소, conflict 100% ledger 보존, S4/S5/S6 scenario pass.

---

## 2. Current State (현재 상태)

### P0 완료 후 넘어온 것
- **510 tests**, Gate PASS (VP1 5/5, VP2 5/6, VP3 5/6)
- `EvolverState.conflict_ledger: list[dict]` 필드 선언 완료 (P0-X4, 빈 배열 기본값)
- `EvolverState.dispute_queue: list[dict]` 필드 존재 (P0-C7)
- integrate/collect I/O shape 동결 (P0-X1/X2)
- P0 baseline trial: `bench/silver/japan-travel/p0-20260412-baseline/` — KU 127, 15 cycle

### 현 코드 문제점
1. `integrate.py:28-37` `_find_matching_ku` — exact match only
2. `dispute_resolver.py` — resolve 후 conflict 이력 미보존
3. `state_io.py` — `conflict_ledger.json` 파일 미처리
4. skeleton 에 `aliases`/`is_a` 필드 부재

---

## 3. Target State (목표 상태)

- **entity_resolver.py** 가 skeleton `aliases`/`is_a` 기반으로 canonical entity_key 해석
- **integrate_node** 가 resolver 경유하여 중복 KU 생성 방지
- **conflict_ledger** 가 모든 conflict 의 이력을 영구 보존 (resolve 후에도 삭제 불가)
- **japan-travel 재실행**: 중복 KU ≥ 15% 감소 (unique entity_key 수 기준)
- **S4/S5/S6 blocking scenario** 전부 pass
- **테스트 ≥ 530** (P0 510 + P1 20)

---

## 4. Implementation Stages

### Stage A: 해상도 계층 (P1-A1 ~ P1-A4)

entity_resolver.py 신규 작성 + integrate.py 연동 + skeleton 확장.

1. **P1-A1** `src/utils/entity_resolver.py` [NEW] — `resolve_alias`, `resolve_is_a`, `canonicalize_entity_key` 3개 함수. alias map 은 `skeleton["aliases"]: {canonical_key: [alias1, ...]}`. `[M]`
2. **P1-A2** `integrate.py._find_matching_ku` 가 resolver 경유 매칭. 기존 exact match 는 resolver fallback 으로 이동. `[M]`
3. **P1-A3** skeleton validator (`schema_validator.py`) 확장 — `aliases`/`is_a` 필드 존재 시 schema validate, 없으면 통과 (backward compat). `[S]`
4. **P1-A4** japan-travel skeleton 에 alias/is_a 2쌍 이상 추가 (`jr-pass` ↔ `재팬레일패스`, `shinkansen` is_a `train`). `[S]`

### Stage B: Conflict ledger 영속화 (P1-B1 ~ P1-B4)

conflict 감사 로그 구조 정의 + integrate/dispute_resolver/state_io 연동.

1. **P1-B1** `conflict_ledger` JSON 포맷 정의 (`ledger_id`, `ku_id`, `created_at`, `status`, `conflicting_evidence`, `resolution`). `[S]`
2. **P1-B2** `integrate_node` 에서 conflict 감지 시 ledger entry 생성, `dispute_resolver` resolve 후에도 `status=resolved` 유지 (삭제 금지). `[M]`
3. **P1-B3** `state_io.py` save/load 에 `conflict_ledger.json` 포함 — 파일 부재 시 빈 배열 (migration-safe). `[S]`
4. **P1-B4** `dispute_queue` (휘발) ↔ `conflict_ledger` (영속 감사) 관계 명시. 동일 `ku_id` 참조 가능하나 독립. `[S]`

### Stage C: 검증 (P1-C1 ~ P1-C4)

단위/통합 테스트 + S4/S5/S6 scenario + japan-travel 재실행.

1. **P1-C1** `tests/test_utils/test_entity_resolver.py` [NEW] — alias 양방향, is_a 2단 chain, canonicalization idempotent, 누락 field 처리. 최소 8 테스트. `[M]`
2. **P1-C2** `tests/test_nodes/test_integrate.py` 에 S4/S5/S6 scenario 테스트 추가. `[M]`
3. **P1-C3** `tests/integration/test_japan_travel_rerun.py` [NEW] — P0 baseline state 입력 → 재통합 → 중복 KU ≥ 15% 감소 assert. `[M]`
4. **P1-C4** ledger 영속화 테스트 — dispute 전체가 ledger 존재, resolved 후 `ledger_id` 조회 가능. `[S]`

---

## 5. Task Breakdown

| ID | Task | Size | Stage | 의존성 |
|----|------|------|-------|--------|
| P1-A1 | entity_resolver.py 신규 | M | A | — |
| P1-A2 | integrate.py resolver 연동 | M | A | P1-A1 |
| P1-A3 | skeleton validator 확장 | S | A | P1-A1 |
| P1-A4 | japan-travel skeleton alias/is_a | S | A | — |
| P1-B1 | conflict_ledger 포맷 정의 | S | B | — |
| P1-B2 | integrate + dispute_resolver ledger 연동 | M | B | P1-B1 |
| P1-B3 | state_io ledger save/load | S | B | P1-B1 |
| P1-B4 | dispute_queue ↔ ledger 관계 문서화 | S | B | P1-B1 |
| P1-C1 | test_entity_resolver.py (≥ 8건) | M | C | P1-A1~A4 |
| P1-C2 | test_integrate S4/S5/S6 | M | C | P1-A2, P1-B2 |
| P1-C3 | test_japan_travel_rerun (중복 15%) | M | C | P1-A2 |
| P1-C4 | ledger 영속화 테스트 | S | C | P1-B2, P1-B3 |

**Size 분포**: S: 5, M: 7, L: 0 → 총 12 tasks

---

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| P1-R1 | alias 맵 불완전 → resolver false negative | M | M | skeleton alias 는 점진 추가, exact match fallback 유지 |
| P1-R2 | is_a chain 순환 → 무한루프 | L | H | depth limit + visited set 방어 |
| P1-R3 | resolver 가 integrate 성능 저하 | L | M | alias lookup O(1) dict, KU ≤ 200건 규모 |
| P1-R4 | conflict_ledger 비대화 (장기 운용) | L | L | Silver 범위에서는 수천 건 이내, Gold 에서 archival 고려 |
| P1-R5 | P3 와 integrate.py 동시 수정 충돌 | M | M | P0-X 인터페이스 고정으로 완화. P1-A2 는 `_find_matching_ku` 만 변경, P3 는 claim 파이프라인 변경 → 접점 최소 |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| `entity_resolver.py` | `DomainSkeleton` (skeleton.aliases, skeleton.is_a) |
| `integrate.py` 수정 | `entity_resolver.py` (P1-A1 선행) |
| `state_io.py` 수정 | `conflict_ledger` JSON 포맷 (P1-B1 선행) |
| `dispute_resolver.py` 수정 | `conflict_ledger` 연동 (P1-B1 선행) |

### 선행 Phase
- **P0 완료** (state_io 안전성, 인터페이스 고정) ✅

### 후속 Phase 영향
- **P2**: `entity_resolver.canonicalize_entity_key` 를 remodel 시 alias merge 판단에 활용
- **P4**: `conflict_ledger` 를 coverage deficit 분석 입력으로 활용 가능

### 외부 패키지
- 추가 없음 (순수 Python 표준 라이브러리)

---

## 8. Phase Gate (정량, masterplan §4 verbatim)

- [x] 단위 테스트: 동의어 (JR-Pass / 재팬레일패스) pass — S4
- [x] 단위 테스트: is_a (shinkansen is_a train) pass — S5
- [x] japan-travel 재실행: 중복 KU 감소 확인 (alias claim → 기존 KU merge)
- [x] 충돌 KU 100% ledger 영구 보존 (resolve 후에도 삭제 불가) — S6
- [x] S4/S5/S6 scenario pass
- [x] 테스트 ≥ 530 → **544 passed**

---

## 9. E2E Bench Results

> **주의**: P1은 dedicated bench trial 미실행. Gate 판정은 단위/통합 테스트(544건) + S4/S5/S6 scenario pass 기반.
> P0 baseline trial (`p0-20260412-baseline`, 127 KU) 대비 alias dedup 효과는 `test_japan_travel_rerun.py` 통합 테스트로 검증.
> 향후 P3 이후 누적 bench trial 시 P1 변경분 regression 재확인 필요.

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Dedicated trial | `bench/silver/japan-travel/p1-*` | **미실행** | N/A |
| S4 (동의어 병합) | pass | pass (test_entity_resolver) | PASS |
| S5 (is_a 상속) | pass | pass (test_entity_resolver) | PASS |
| S6 (conflict ledger 보존) | pass | pass (test_integrate S6) | PASS |
| 중복 KU 감소 | ≥ 15% | alias dedup 통합 테스트 pass | PASS |
| Ledger 영속 | 100% 보존 | save/load round-trip pass | PASS |
| Total tests | ≥ 530 | 544 | PASS |

### 판정

- **Gate 결과**: **PASS** (S4/S5/S6 pass, 544 tests. Dedicated bench trial 미실행 — P3 이후 누적 검증 예정)
- **판정 일시**: 2026-04-12
- **Commit**: `3bbde92`
- **비고**: P1은 entity resolution 계층 + ledger 영속화가 주 범위이므로, E2E cycle 실행보다 단위/통합 테스트 검증이 더 적합. 다만 향후 Phase에서 누적 bench trial 시 regression 확인 권장.
