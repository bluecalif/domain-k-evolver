# Silver P0: Foundation Hardening — Tasks
> Last Updated: 2026-04-12
> Status: In Progress (29/32, 91%)

## Summary

| Stage | Total | Done | Status |
|-------|-------|------|--------|
| A. 벤치 스캐폴딩 | 6 | 6/6 | ✅ 완료 |
| B. Remediation | 9 | 9/9 | ✅ 완료 |
| C. HITL 축소 | 8 | 8/8 | ✅ 완료 |
| X. 인터페이스 고정 | 6 | 6/6 | ✅ 완료 |
| D. Baseline trial | 3 | 0/3 | 대기 |
| **합계** | **32** | **29/32** | 91% |

테스트: 468 (baseline) → **510 passed** (목표 ≥ 488 ✅)

---

## Stage A: Silver 벤치 스캐폴딩

- [x] **P0-A1** `bench/silver/INDEX.md` 생성 (§12.4 verbatim 컬럼: trial_id | domain | phase | date | goal | status | readiness | notes) `[S]` — `2f9117a`
- [x] **P0-A2** 템플릿 3종 생성 `[S]` — `2f9117a`
  - `templates/si-trial-card.md` (goal / config diff / 가설)
  - `templates/si-readiness-report.md` (VP1/VP2/VP3 결과 + diff 해석)
  - `templates/si-index-row.md` (INDEX 한 줄 삽입 snippet)
- [x] **P0-A3** 첫 baseline trial 경로: `bench/silver/japan-travel/p0-20260411-baseline/` + 하위 `state/`, `trajectory/`, `telemetry/`, `trial-card.md` `[S]` — `2f9117a`
- [x] **P0-A4** `state_io.py`/`orchestrator.py` `--bench-root` 경로 격리 + legacy bench 쓰기 금지 `[M]` — `2f9117a`
- [x] **P0-A5** `run_bench.py`/`run_one_cycle.py`/`run_readiness.py` `--bench-root` 인자 전달 (기본값 없음) `[S]` — `2f9117a`
- [x] **P0-A6** `config.snapshot.json` 자동 작성 (dataclass 직렬화 + git HEAD + provider list + seed skeleton hash + api_key redact) `[M]` — `6c7f28f`

---

## Stage B: 기존 remediation 8건

- [x] **P0-B1** (P0-3) `search_adapter.py` L39 retry 판정 정규표현화: `re.search(r"429|5\d\d|rate", exc_str)` `[S]` — `e73b136`
- [x] **P0-B2** (P0-2a) `config.py` `LLMConfig.request_timeout=60`, `SearchConfig.request_timeout=30` + `from_env()` 확장 `[S]` — `e73b136`
- [x] **P0-B3** (P0-2b) `llm_adapter.py` L69 `ChatOpenAI(..., timeout=config.request_timeout)` `[S]` — `e73b136`
- [x] **P0-B4** (P0-2c) `search_adapter.py` Tavily `search`/`extract` 명시적 timeout `[S]` — `e73b136`
- [x] **P0-B5** (P0-2d) `collect.py` L169 `future.result(timeout=60)` + `as_completed(timeout=120)` + per-GU 실패 카운터 `[M]` — `e73b136`
- [x] **P0-B6** (P0-1) `collect.py` L76~L97 이중 bare-except 제거 + 로깅 + `collect_failure_rate` emit + **반환값 shape 변경** `[M]` — `e73b136`
- [x] **P0-B7** (P1-1) `integrate.py` L270~L288 `except ValueError: pass` → `logger.warning` `[S]` — `e73b136`
- [x] **P0-B8** (P1-4) `state_io.py` L54~L56 복구: JSON decode 실패 → `.bak` 시도 → `StateCorruptError` / save 전 `.bak` rotation `[M]` — `e73b136`
- [x] **P0-B9** (P1-3) 테스트 확장 `[L]` — `f21a249`
  - `test_collect.py` +10: S1 (timeout graceful), S2 (malformed JSON fallback), empty search, duplicate GU, failure_rate
  - `test_state_io.py` +9: S3 (corrupt JSON), .bak 복구, 필수필드, save rotation, write guard
  - `test_adapters.py` +6: 504/503/500 retry, Tavily timeout propagation

---

## Stage C: HITL 정책 축소

- [x] **P0-C1** `graph.py` edge 변경: `plan→hitl_a→collect` → `plan→collect`, `collect→integrate` 고정, `integrate→critique` 고정 `[M]` — `83ce974`
- [x] **P0-C2** `graph.py` HITL-S edge: `seed → (첫 cycle → hitl_s → mode, else → mode)` via `route_after_seed` `[M]` — `83ce974`
- [x] **P0-C3** `route_after_critique` 단순화: 10-cycle HITL-D 분기 제거, `converged → END, else → plan_modify` `[S]` — `83ce974`
- [x] **P0-C4** `should_auto_pause()` 공통 함수 (5개 임계치: conflict_rate>0.25, evidence_rate<0.55, collect_failure_rate>0.50, staleness_ratio>0.30, avg_confidence<0.60) `[M]` — `83ce974` (Stage B 선행분)
- [x] **P0-C5** `hitl_gate.py` → enum `"S"|"R"|"E"` 3케이스 축소 (A/B/C/D → DeprecationWarning + auto-approve) `[M]` — `83ce974`
- [x] **P0-C6** `metrics_guard.py` 확장: Silver `AUTO_PAUSE_THRESHOLDS` + `should_auto_pause` 통합, `route_after_mode` 에서 interrupt `[M]` — `83ce974`
- [x] **P0-C7** `EvolverState.dispute_queue: list[dict]` 추가 + `integrate_node` conflict_hold 시 append `[S]` — `83ce974`
- [x] **P0-C8** 테스트 `[M]` — `83ce974` + `f21a249`
  - `test_graph.py`: Bronze gate 제거, hitl_s 첫 cycle, auto-pause 5조건 완결, subsequent cycle skip
  - `test_hitl_gate.py`: S/R/E 8건 + DeprecationWarning 파라메트라이즈 4건
  - 누적 16개+

---

## Stage X: 인터페이스 고정

- [x] **P0-X1** `integrate_node` I/O dict shape 동결 → `docs/silver-interface-snapshots/integrate-p0.md` 기록 `[S]` — (커밋 대기)
- [x] **P0-X2** `collect_node` I/O dict shape 동결 → `docs/silver-interface-snapshots/collect-p0.md` 기록 `[S]` — (커밋 대기)
- [x] **P0-X3** `Claim`/`EU` provenance 필드 예약 (optional, None 기본값) — P3 에서 채움 `[S]` — (커밋 대기)
- [x] **P0-X4** `EvolverState` 5개 신규 필드 일괄 선언 (`dispute_queue`(기존), `conflict_ledger`, `phase_history`, `coverage_map`, `novelty_history`) — 기본값 빈 컨테이너 `[S]` — (커밋 대기)
- [x] **P0-X5** `metrics_logger` metric key 전체 목록 동결 문서화 + `collect_failure_rate` logger 반영 `[S]` — (커밋 대기)
- [x] **P0-X6** `tests/conftest.py` 공통 fixture 재정비 (P1/P3 충돌 방지) `[S]` — (커밋 대���)

---

## Stage D: Silver baseline trial 재현

- [ ] **P0-D1** Phase 4·5 스모크를 `bench/silver/japan-travel/p0-{date}-baseline/` 에 재실행 (same seed, same config) `[M]`
- [ ] **P0-D2** `readiness-report.md` 작성 — VP1 ≥ 4/5, VP2 ≥ 5/6 확인. 불일치 시 원인 분리 후 재실행 `[S]`
- [ ] **P0-D3** `INDEX.md` 첫 행 삽입 `[S]`

---

## Phase Gate Process (필수 순서)

> 각 Phase 를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — Stage D 의 baseline trial 을 실제 실행 (`run_bench --bench-root bench/silver/japan-travel/p0-{date}-baseline`)
2. **결과 자가평가** — VP1/VP2/VP3 정량 기준 + S1/S2/S3 시나리오 + HITL-A/B/C 0건 확인
3. **Debug 루프** — bench 에서 발견된 이슈는 gate 통과 전에 fix. 이력은 `debug-history.md` 에 기록
4. **dev-docs 반영** — 아래 Phase Gate Checklist 체크, E2E Bench Results 테이블 실측값 채움, plan.md Status 업데이트
5. **Gate 판정 commit** — `[si-p0] Gate PASS/FAIL: {근거}` 로 기록 후 다음 Phase 이동

## Phase Gate Checklist

- [ ] bare-except 0건
- [ ] `collect_failure_rate`, `timeout_count`, `retry_success_rate` emit
- [ ] 테스트 ≥ 488 (468 + 20)
- [ ] 48h soak: adapter kill → hang 없음
- [ ] baseline trial: VP1 ≥ 4/5, VP2 ≥ 5/6
- [ ] HITL-A/B/C 호출 0건
- [ ] HITL-S 첫 cycle 1회, HITL-E 예외시만
- [ ] S1/S2/S3 scenario pass

---

## E2E Bench Results (Phase 종료 시 기록)

> Stage D 완료 후 실측값을 아래 테이블에 채움. Gate 판정의 정량 근거.

### Trial: `p0-{date}-baseline`

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Trial path | `bench/silver/japan-travel/p0-*-baseline/` | — | — |
| Cycles run | ≥ 5 | — | — |
| **VP1 (Variability)** | ≥ 4/5 | —/5 | — |
| **VP2 (Completeness)** | ≥ 5/6 | —/6 | — |
| VP3 (Self-Governance) | 참고 | —/6 | — |
| Total tests | ≥ 488 | — | — |
| bare-except | 0 | — | — |
| collect_failure_rate emit | yes | — | — |
| timeout_count emit | yes | — | — |
| retry_success_rate emit | yes | — | — |
| HITL-A/B/C 호출 | 0 | — | — |
| S1 pass | yes | — | — |
| S2 pass | yes | — | — |
| S3 pass | yes | — | — |

### Regression vs Phase 5

| 지표 | Phase 5 (b122a23) | P0 baseline | Delta |
|------|-------------------|-------------|-------|
| VP1 | 5/5 | — | — |
| VP2 | 6/6 | — | — |
| VP3 | 5/6 | — | — |
| avg_confidence | 0.822 | — | — |
| conflict_rate | 0.000 | — | — |
| gap_resolution | 0.909 | — | — |
| Active KU | 77 | — | — |
| Tests | 468 | — | — |

**Gate 판정**: — (미판정)
**판정 일시**: —
**Commit**: —
