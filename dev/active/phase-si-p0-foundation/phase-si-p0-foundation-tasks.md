# Silver P0: Foundation Hardening — Tasks
> Last Updated: 2026-04-11
> Status: Planning (0/32)

## Summary

| Stage | Total | Done | Status |
|-------|-------|------|--------|
| A. 벤치 스캐폴딩 | 6 | 0/6 | 대기 |
| B. Remediation | 9 | 0/9 | 대기 |
| C. HITL 축소 | 8 | 0/8 | 대기 |
| X. 인터페이스 고정 | 6 | 0/6 | 대기 |
| D. Baseline trial | 3 | 0/3 | 대기 |
| **합계** | **32** | **0/32** | — |

테스트: 468 (baseline) → 목표 ≥ 488

---

## Stage A: Silver 벤치 스캐폴딩

- [ ] **P0-A1** `bench/silver/INDEX.md` 생성 (§12.4 verbatim 컬럼: trial_id | domain | phase | date | goal | status | readiness | notes) `[S]`
- [ ] **P0-A2** 템플릿 3종 생성 `[S]`
  - `templates/si-trial-card.md` (goal / config diff / 가설)
  - `templates/si-readiness-report.md` (VP1/VP2/VP3 결과 + diff 해석)
  - `templates/si-index-row.md` (INDEX 한 줄 삽입 snippet)
- [ ] **P0-A3** 첫 baseline trial 경로: `bench/silver/japan-travel/p0-{YYYYMMDD}-baseline/` + 하위 `state/`, `trajectory/`, `telemetry/`, `trial-card.md`, `config.snapshot.json` `[S]`
- [ ] **P0-A4** `state_io.py`/`orchestrator.py` `--bench-root` 경로 격리 + legacy bench 쓰기 금지 `[M]`
- [ ] **P0-A5** `run_bench.py`/`run_one_cycle.py`/`run_readiness.py` `--bench-root` 인자 전달 (기본값 없음) `[S]`
- [ ] **P0-A6** `config.snapshot.json` 자동 작성 (dataclass 직렬화 + git HEAD + provider list + seed skeleton hash) `[M]`

---

## Stage B: 기존 remediation 8건

- [ ] **P0-B1** (P0-3) `search_adapter.py` L39 retry 판정 정규표현화: `re.search(r"\b(429|5\d\d|rate[ _-]?limit)\b", exc_str)` `[S]`
- [ ] **P0-B2** (P0-2a) `config.py` `LLMConfig.request_timeout=60`, `SearchConfig.request_timeout=30` + `from_env()` 확장 `[S]`
- [ ] **P0-B3** (P0-2b) `llm_adapter.py` L69 `ChatOpenAI(..., timeout=config.request_timeout)` `[S]`
- [ ] **P0-B4** (P0-2c) `search_adapter.py` Tavily `search`/`extract` 명시적 timeout `[S]`
- [ ] **P0-B5** (P0-2d) `collect.py` L169 `future.result(timeout=overall_timeout)` + per-GU 실패 카운터 `[M]`
- [ ] **P0-B6** (P0-1) `collect.py` L76~L97 이중 bare-except 제거 + 로깅 + `collect_failure_rate` emit + **반환값 shape 변경** `[M]`
- [ ] **P0-B7** (P1-1) `integrate.py` L270~L288 `except ValueError: pass` → `logger.warning` + `preserved.append(raw_ref)` `[S]`
- [ ] **P0-B8** (P1-4) `state_io.py` L54~L56 복구: JSON decode 실패 → `.bak` 시도 → `StateIOError` / 필수필드 누락 → skip / save 전 `.bak` rotation `[M]`
- [ ] **P0-B9** (P1-3) 테스트 확장 `[L]`
  - `test_collect.py`: S1 (timeout), S2 (malformed JSON), empty search, duplicate claim — 최소 8개
  - `test_state_io.py`: S3 (corrupt JSON), 필수필드 누락, `.bak` 복구, save rotation — 최소 6개
  - `test_search_adapter.py`: 504 retry, timeout metric — 최소 4개

---

## Stage C: HITL 정책 축소

- [ ] **P0-C1** `graph.py` edge 변경: `plan→hitl_a→collect` → `plan→collect`, `collect→integrate` 고정 + HITL-E 분기, `integrate→critique` 고정 + dispute append `[M]`
- [ ] **P0-C2** `graph.py` HITL-S edge: `seed→hitl_s→mode` (조건: `current_cycle==1 and phase_just_started`) `[M]`
- [ ] **P0-C3** `route_after_critique` 단순화: HITL-D(audit) → audit 직접 호출로 전환 `[S]`
- [ ] **P0-C4** `should_auto_pause()` 공통 함수 (5개 임계치: collect_failure_rate>0.3, conflict_rate>0.4, fetch_failure_rate>0.5, cost_regression, dispute_queue>20) `[M]`
- [ ] **P0-C5** `hitl_gate.py` → enum `"S"|"R"|"E"` 3케이스 축소 (A/B/C/D 제거, deprecation 1회 warning + no-op) `[M]`
- [ ] **P0-C6** `metrics_guard.py` 확장: Silver 5개 임계치 + `cost_regression_flag`/`dispute_queue_size` 는 실제 interrupt `[M]`
- [ ] **P0-C7** `EvolverState.dispute_queue: list[DisputeEntry]` 추가 (`src/state.py`) + `integrate_node` auto-resolve 실패 append `[S]`
- [ ] **P0-C8** 테스트 `[M]`
  - `test_graph.py`: 일반 cycle HITL-A/B/C 0회 호출
  - `test_graph.py`: HITL-S phase 첫 cycle 에서만
  - `test_graph.py`: auto-pause 5조건 → HITL-E 라우팅
  - `test_hitl_gate.py`: 축소된 enum + deprecation 경로
  - 최소 10개

---

## Stage X: 인터페이스 고정

- [ ] **P0-X1** `integrate_node` I/O dict shape 동결 → `docs/silver-interface-snapshots/integrate-p0.md` 기록 `[S]`
- [ ] **P0-X2** `collect_node` I/O dict shape 동결 → `docs/silver-interface-snapshots/collect-p0.md` 기록 `[S]`
- [ ] **P0-X3** `Claim`/`EU` provenance 필드 예약 (optional, None 기본값) — P3 에서 채움 `[S]`
- [ ] **P0-X4** `EvolverState` 5개 신규 필드 일괄 선언 (`dispute_queue`, `conflict_ledger`, `phase_history`, `coverage_map`, `novelty_history`) — 기본값 빈 컨테이너 `[S]`
- [ ] **P0-X5** `metrics_logger` metric key 전체 목록 동결 문서화 `[S]`
- [ ] **P0-X6** `tests/conftest.py` 공통 fixture 재정비 (P1/P3 충돌 방지) `[S]`

---

## Stage D: Silver baseline trial 재현

- [ ] **P0-D1** Phase 4·5 스모크를 `bench/silver/japan-travel/p0-{date}-baseline/` 에 재실행 (same seed, same config) `[M]`
- [ ] **P0-D2** `readiness-report.md` 작성 — VP1 ≥ 4/5, VP2 ≥ 5/6 확인. 불일치 시 원인 분리 후 재실행 `[S]`
- [ ] **P0-D3** `INDEX.md` 첫 행 삽입 `[S]`

---

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
