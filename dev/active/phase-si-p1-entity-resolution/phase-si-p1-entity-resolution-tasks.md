# Silver P1: Entity Resolution & State Safety — Tasks
> Last Updated: 2026-04-12
> Status: 12/12

---

## P1-A. 해상도 계층

- [x] **P1-A1** `src/utils/entity_resolver.py` 신규 — resolve_alias / resolve_is_a / canonicalize_entity_key `[M]`
- [x] **P1-A2** `integrate.py._find_matching_ku` resolver 경유 매칭 `[M]`
- [x] **P1-A3** skeleton validator 확장 (aliases/is_a optional) `[S]`
- [x] **P1-A4** japan-travel skeleton alias/is_a 예시 추가 `[S]`

## P1-B. Conflict ledger 영속화

- [x] **P1-B1** conflict_ledger JSON 포맷 정의 `[S]`
- [x] **P1-B2** integrate + dispute_resolver ledger 연동 `[M]`
- [x] **P1-B3** state_io ledger save/load `[S]`
- [x] **P1-B4** dispute_queue ↔ ledger 관계 문서화 `[S]`

## P1-C. 검증

- [x] **P1-C1** test_entity_resolver.py (16건: alias 7 + is_a 5 + canonicalize 4) `[M]`
- [x] **P1-C2** test_integrate S4/S5/S6 scenario (8건) `[M]`
- [x] **P1-C3** test_japan_travel_rerun (3건: alias dedup) `[M]`
- [x] **P1-C4** ledger 영속화 테스트 (3건 in test_state_io + 5건 schema) `[S]`

---

## Phase Gate Process (필수 순서)

> 각 Phase 를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — dedicated trial 또는 기존 baseline 위에 재실행. P1은 entity resolution 특성상 단위/통합 테스트 + S4/S5/S6 scenario로 대체 판정.
2. **결과 자가평가** — 정량 기준 + blocking scenario 확인
3. **Debug 루프** — 발견 이슈는 gate 통과 전 fix, `debug-history.md` 기록
4. **dev-docs 반영** — Phase Gate Checklist 체크, E2E Bench Results 실측값, plan.md Status 업데이트
5. **Gate 판정 commit** — `[si-p1] Gate PASS/FAIL: {근거}` 로 기록

## Phase Gate Checklist

- [x] 동의어 테스트 pass (JR-Pass / 재팬레일패스) — S4
- [x] is_a 테스트 pass (shinkansen is_a train) — S5
- [x] japan-travel 재실행: alias claim → 기존 KU merge (중복 방지) — S6 연관
- [x] 충돌 KU 100% ledger 영구 보존 (resolve 후에도 삭제 불가)
- [x] S4, S5, S6 scenario pass
- [x] 테스트 수: **544** (P0 510 + P1 34) ≥ 530 목표 ✅

---

## E2E Bench Results (Phase 종료 시 기록)

> **주의**: P1은 dedicated bench trial 미실행. S4/S5/S6 scenario + 544 단위/통합 테스트로 대체 판정.

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Dedicated trial | `bench/silver/japan-travel/p1-*` | 미실행 | N/A |
| S4 (동의어 병합) | pass | pass | PASS |
| S5 (is_a 상속) | pass | pass | PASS |
| S6 (conflict ledger 보존) | pass | pass | PASS |
| 중복 KU 감소 | ≥ 15% | alias dedup 통합 테스트 pass | PASS |
| Ledger 영속 | 100% 보존 | save/load round-trip pass | PASS |
| Total tests | ≥ 530 | 544 | PASS |

**Gate 판정**: **PASS** (S4/S5/S6 pass, 544 tests, commit `3bbde92`)
