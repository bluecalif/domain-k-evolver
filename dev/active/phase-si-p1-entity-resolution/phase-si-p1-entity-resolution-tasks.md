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

## Phase Gate (정량)

- [x] 동의어 테스트 pass (JR-Pass / 재팬레일패스) — S4
- [x] is_a 테스트 pass (shinkansen is_a train) — S5
- [x] japan-travel 재실행: alias claim → 기존 KU merge (중복 방지) — S6 연관
- [x] 충돌 KU 100% ledger 영구 보존 (resolve 후에도 삭제 불가)
- [x] S4, S5, S6 scenario pass
- [x] 테스트 수: **544** (P0 510 + P1 34) ≥ 530 목표 ✅
