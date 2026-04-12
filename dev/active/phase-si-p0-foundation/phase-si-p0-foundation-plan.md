# Silver P0: Foundation Hardening
> Last Updated: 2026-04-12
> Status: In Progress (23/32, 72%) — Stage A(+A6)/B/C 완료, Stage X/D 대기
> Current Step: P0-X1 (integrate_node I/O snapshot) → P0-X → P0-D

## 1. Summary (개요)

**목적**: Silver 세대 전체가 의존할 안전 기반 확보. silent failure 제거, Silver 벤치 격리 구조 확립, HITL 정책을 masterplan v2 §14 의 4세트(HITL-S/R/D/E)로 축소, P1/P3 병렬 착수를 위한 인터페이스 동결.

**범위 (scope-locked, D-76)**: 8 remediation + 벤치 스캐폴딩 + HITL 축소 + 인터페이스 고정 **외 추가 금지**.

**예상 결과물**:
- `bench/silver/` 디렉토리 + INDEX.md + 템플릿 3종 + baseline trial
- adapter 강건성 8건 (retry/timeout/bare-except 제거/state_io 복구)
- graph.py HITL-A/B/C 제거 → HITL-S/R/D/E 4세트 체제
- `--bench-root` 격리 플래그
- P1/P3 용 인터페이스 스냅샷 6건
- 신규 테스트 ≥ 20건 (누적 ≥ 488)

---

## 2. Current State (현재 상태)

### Bronze 완료 자산
- **468 tests** (baseline), commit `b122a23`, Gate #5 PASS (VP1 5/5, VP2 6/6, VP3 5/6)

### Silver P0 진행 (2026-04-12)
- **500 passed** (목표 ≥ 488 달성), 3 skipped
- 완료 커밋 체인:
  - `7bc2dc8` — dev-docs (P0 plan/context/tasks)
  - `2f9117a` — Stage A: 벤치 스캐폴딩 + `--bench-root` 격리 (A1~A5)
  - `e73b136` — Stage B: Remediation 8건 (B1~B8)
  - `83ce974` — Stage C: HITL 축소 Silver S/R/E (C1~C7)
  - `f21a249` — Stage B9+C8: 테스트 일괄 +29건
  - `6c7f28f` — Stage A6: config.snapshot.json 자동 작성 (+10 tests)
- `src/graph.py`: Silver flow — `seed → (첫cycle→hitl_s→mode, else→mode) → mode → (auto_pause→hitl_e→plan, else→plan) → plan → collect → integrate → critique → (converged→END, else→plan_modify→cycle_inc→END)`
- `src/nodes/hitl_gate.py`: S/R/E only, Bronze A/B/C/D → DeprecationWarning
- `src/utils/metrics_guard.py`: `should_auto_pause()` + `AUTO_PAUSE_THRESHOLDS` 5개 임계치
- `src/nodes/collect.py`: 구체 예외 로깅 + `collect_failure_rate` emit + future timeout 60s/120s
- `src/adapters/search_adapter.py`: retry regex `r"429|5\d\d|rate"` + Tavily timeout 명시
- `src/utils/state_io.py`: .bak rotation + recovery path + 필수필드 검증 + legacy write guard
- `src/state.py`: `dispute_queue: list[dict]` 필드 추가
- `bench/silver/japan-travel/p0-20260411-baseline/` 존재 (A3)

### 미완료
- **Stage A**: A6 (config.snapshot.json 자동 작성)
- **Stage X**: X1~X6 (인터페이스 고정 6건)
- **Stage D**: D1~D3 (baseline trial 재현 + gate)

---

## 3. Target State (목표 상태)

P0 완료 후:
- **bare-except 0건** (`src/nodes/`, `src/adapters/`, `src/utils/state_io.py`)
- **3개 reliability 메트릭 emit**: `collect_failure_rate`, `timeout_count`, `retry_success_rate`
- **graph edge**: 일반 cycle HITL-A/B/C 호출 0, HITL-S 는 phase 첫 cycle 1회, HITL-E 는 예외시만
- **bench 격리**: `bench/silver/japan-travel/p0-{date}-baseline/` 존재, legacy bench 쓰기 금지
- **baseline trial**: VP1 ≥ 4/5, VP2 ≥ 5/6 재현 (Phase 5 동등)
- **인터페이스 스냅샷 6건** 완료 → P1/P3 병렬 branch 가능
- **테스트 ≥ 488** (468 + 20)
- **S1/S2/S3 scenario** pass

---

## 4. Implementation Stages

### Stage A: Silver 벤치 스캐폴딩 (6 tasks)

`bench/silver/` 디렉토리 구조 + 템플릿 + `--bench-root` 격리.
runtime 로직 변경보다 **먼저** 처리 — baseline trial 이 없으면 P0 gate 검증 근거가 없다.

**파일**: `bench/silver/**` [NEW], `templates/si-*.md` [NEW], `src/utils/state_io.py`, `src/orchestrator.py`, `scripts/run_*.py`, `src/config.py`

| Task | 설명 | Size | 의존 |
|------|------|------|------|
| P0-A1 | `bench/silver/INDEX.md` 생성 (§12.4 verbatim 컬럼) | S | — |
| P0-A2 | 템플릿 3종 (si-trial-card, si-readiness-report, si-index-row) | S | — |
| P0-A3 | 첫 baseline trial 경로 생성 (`p0-{YYYYMMDD}-baseline/`) | S | A1 |
| P0-A4 | `state_io.py`/`orchestrator.py` `--bench-root` 경로 격리, legacy bench 쓰기 금지 | M | — |
| P0-A5 | `run_bench.py`/`run_one_cycle.py`/`run_readiness.py` `--bench-root` 인자 전달 | S | A4 |
| P0-A6 | `config.snapshot.json` 자동 작성 (dataclass 직렬화 + git HEAD + provider list) | M | A3 |

### Stage B: 기존 remediation 8건 (9 tasks)

`p0-p1-remediation-plan.md` 흡수. adapter/node 강건성 + 예외 로깅 + 실패 카운터.

**파일**: `src/adapters/search_adapter.py`, `src/config.py`, `src/adapters/llm_adapter.py`, `src/nodes/collect.py`, `src/nodes/integrate.py`, `src/utils/state_io.py`, `tests/`

| Task | 원본 | 설명 | Size | 의존 |
|------|------|------|------|------|
| P0-B1 | P0-3 | `search_adapter.py` retry 판정 정규표현화 (`429\|5\d\d\|rate`) | S | — |
| P0-B2 | P0-2a | `config.py` `request_timeout` (LLM 60s, Search 30s) | S | — |
| P0-B3 | P0-2b | `llm_adapter.py` ChatOpenAI timeout 전달 | S | B2 |
| P0-B4 | P0-2c | `search_adapter.py` Tavily timeout 명시 | S | B2 |
| P0-B5 | P0-2d | `collect.py` ThreadPoolExecutor future timeout | M | B2 |
| P0-B6 | P0-1 | `collect.py` 이중 bare-except 제거 + 실패 카운터 + `collect_failure_rate` emit | M | — |
| P0-B7 | P1-1 | `integrate.py` `except ValueError: pass` 제거 + 원문 보존 | S | — |
| P0-B8 | P1-4 | `state_io.py` 복구 경로 (.bak rotation, 필수필드 검증) | M | — |
| P0-B9 | P1-3 | 테스트 확장 (S1/S2/S3 scenario 포함, 최소 18개) | L | B1~B8 |

**주의**: P0-B6 은 `collect_failure_rate` 반환값까지 변경해야 orchestrator 가 집계 가능.

### Stage C: HITL 정책 축소 (8 tasks)

masterplan v2 §14 에 따라 inline HITL-A/B/C 제거, HITL-S/R/D/E 4세트 도입.

**파일**: `src/graph.py`, `src/nodes/hitl_gate.py`, `src/utils/metrics_guard.py`, `src/state.py`, `tests/`

**HITL 전환 모델**:
| 구 (Bronze) | 신 (Silver) | 동작 |
|-------------|-------------|------|
| HITL-A (plan) | 제거 | `plan → collect` 직결 |
| HITL-B (collect) | 제거 → HITL-E 이관 | `collect → integrate` 직결 |
| HITL-C (integrate) | 제거 → HITL-D/E 이관 | `integrate → critique` 직결; dispute → `state.dispute_queue` |
| HITL-D (audit) | 의미 전환: Dispute batch (비블로킹) | queue append only, graph edge 아님 |
| HITL-E (convergence) | 의미 전환: Exception auto-pause | 임계치 위반 시만 `interrupt()` |
| — | HITL-S 신규 | phase 첫 cycle 1회 seed 승인 |
| — | HITL-R 신규 (stub, 실구현 P2) | remodel 제안 승인 |

| Task | 설명 | Size | 의존 |
|------|------|------|------|
| P0-C1 | `graph.py` A/B/C edge 제거 + HITL-E 분기 추가 | M | — |
| P0-C2 | `graph.py` HITL-S edge 추가 (phase 첫 cycle 조건) | M | C1 |
| P0-C3 | `route_after_critique` 단순화 (HITL-D → audit 직접) | S | C1 |
| P0-C4 | `should_auto_pause()` 공통 함수 (5개 임계치) | M | B6 (collect_failure_rate 필요) |
| P0-C5 | `hitl_gate.py` → S/R/E 3케이스 축소 (A/B/C/D 제거, deprecation 경로) | M | C1 |
| P0-C6 | `metrics_guard.py` 확장 (Silver v2 5개 임계치, interrupt 연결) | M | C4 |
| P0-C7 | `EvolverState.dispute_queue` 필드 추가 + integrate auto-resolve 실패 append | S | — |
| P0-C8 | 테스트 (HITL 0호출, HITL-S 첫 cycle, HITL-E 5조건 라우팅, deprecated enum) — 최소 10개 | M | C1~C7 |

**P2 경계**: HITL-R edge 는 P0 에서 graph 에 등록하되 stub (empty proposal). 실 remodel 로직은 P2.

### Stage X: 인터페이스 고정 (6 tasks)

P1/P3 병렬 착수 전 반드시 완료. 인터페이스 스냅샷 기록 → P1/P3 branch 분기 가능.

**파일**: `src/nodes/integrate.py`, `src/nodes/collect.py`, `src/state.py`, `src/utils/metrics_logger.py`, `tests/conftest.py`, `docs/silver-interface-snapshots/` [NEW]

| Task | 설명 | Size | 의존 |
|------|------|------|------|
| P0-X1 | `integrate_node` I/O dict shape 동결 + 스냅샷 기록 | S | B7 |
| P0-X2 | `collect_node` I/O dict shape 동결 + 스냅샷 기록 | S | B6 |
| P0-X3 | `Claim`/`EU` provenance 필드 예약 (optional, None 기본값) | S | — |
| P0-X4 | `EvolverState` 5개 신규 필드 일괄 선언 (dispute_queue, conflict_ledger, phase_history, coverage_map, novelty_history) | S | C7 |
| P0-X5 | `metrics_logger` metric key 전체 목록 동결 문서화 | S | B6, C6 |
| P0-X6 | `tests/conftest.py` 공통 fixture 재정비 (P1/P3 충돌 방지) | S | — |

### Stage D: Silver baseline trial 재현 (3 tasks)

P0 변경분이 regression 을 일으키지 않았음을 정량 실증.

| Task | 설명 | Size | 의존 |
|------|------|------|------|
| P0-D1 | Phase 4·5 스모크를 `bench/silver/japan-travel/p0-{date}-baseline/` 에 재실행 | M | A3, A4, B 전체, C 전체 |
| P0-D2 | `readiness-report.md` 작성 (VP1 ≥ 4/5, VP2 ≥ 5/6 재현 확인) | S | D1 |
| P0-D3 | `INDEX.md` 첫 행 삽입 | S | D2 |

---

## 5. Task Breakdown (요약)

| Stage | Tasks | S | M | L |
|-------|-------|---|---|---|
| A. 벤치 스캐폴딩 | 6 | 4 | 2 | 0 |
| B. Remediation | 9 | 4 | 4 | 1 |
| C. HITL 축소 | 8 | 2 | 6 | 0 |
| X. 인터페이스 고정 | 6 | 6 | 0 | 0 |
| D. Baseline trial | 3 | 2 | 1 | 0 |
| **합계** | **32** | **18** | **13** | **1** |

---

## 6. 실행 순서 (권장)

```
1.  P0-A1~A3 (벤치 디렉토리/템플릿) — 가장 먼저, runtime 변경 전
2.  P0-A4~A5 (--bench-root 격리)
3.  P0-B1~B8 (remediation 8건 병렬 가능한 것끼리 동시)
4.  P0-C1~C7 (HITL 축소 — C4 는 B6 의 collect_failure_rate 필요)
5.  P0-B9 + P0-C8 (테스트 일괄)
6.  P0-A6 (config snapshot — B/C 변경 반영)
7.  P0-X1~X6 (인터페이스 고정 — B/C merge 직후)
8.  P0-D1~D3 (baseline trial 재현 + gate)
```

---

## 7. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| R6 | P0 scope creep → 다른 Phase 지연 | M | M | scope-locked (D-76): 추가 발견은 P1 이관 |
| R9 | P1/P3 병렬 충돌 | L | M | P0-X 인터페이스 고정 선행 |
| — | B6 collect 반환값 변경 → orchestrator regression | M | M | 반환 shape 변경을 테스트로 즉시 보호 |
| — | HITL 제거 시 기존 테스트 대량 실패 | H | M | C8 에서 assertion 갱신, deprecated 경로 1회 warning |
| — | baseline trial regression (VP 미달) | L | H | 원인 분리 후 B 변경 rollback + 재실행 |

---

## 8. Dependencies

### 내부 (P0 → 후속)
- P0-X → P1 branch, P3 branch 분기 전제
- P0-B6 `collect_failure_rate` → P0-C4 `should_auto_pause`
- P0-C7 `dispute_queue` → P0-X4 State 일괄 선언
- P0-A4 `--bench-root` → P0-D1 baseline trial

### 외부
- 없음 (P0 은 즉시 착수 가능, 신규 패키지 없음)

---

## 9. Phase Gate (정량, masterplan §4 verbatim)

- [ ] 대상 모듈 bare-except **0건** (`grep "except Exception:" src/nodes/ src/adapters/ src/utils/state_io.py`)
- [ ] `collect_failure_rate`, `timeout_count`, `retry_success_rate` 3개 메트릭 `metrics_logger` 에 emit
- [ ] 신규/수정 테스트 ≥ 20건, 전체 green (468 → **≥ 488**)
- [ ] 48h soak: 임의 adapter kill → 그래프 hang 없음
- [ ] `bench/silver/japan-travel/p0-{date}-baseline/` 존재, Phase 4·5 동등 스모크 재현 (**VP1 ≥ 4/5, VP2 ≥ 5/6**)
- [ ] 일반 cycle 실행 시 인라인 HITL-A/B/C 호출 **0건** (graph edge 기준)
- [ ] HITL-S: phase 첫 cycle 1회, HITL-E: trigger 조건 위반 시만
- [ ] **S1** (search timeout → hang 없음), **S2** (malformed LLM JSON), **S3** (corrupt state.json) scenario pass

---

## 10. E2E Bench Results

> Phase 완료 시 `bench/silver/japan-travel/p0-{date}-baseline/` 의 실제 실행 결과를 기록.
> Gate 판정의 정량 근거. 빈 칸은 미실행.

### Trial: `p0-{date}-baseline`

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Trial path | `bench/silver/japan-travel/p0-*-baseline/` | — | — |
| Seed | japan-travel (Phase 5 동일) | — | — |
| Config snapshot | `config.snapshot.json` 존재 | — | — |
| Cycles run | ≥ 5 | — | — |
| **VP1 (Variability)** | ≥ 4/5 | —/5 | — |
| **VP2 (Completeness)** | ≥ 5/6 | —/6 | — |
| VP3 (Self-Governance) | 참고 | —/6 | — |
| Total tests | ≥ 488 | — | — |
| bare-except count | 0 | — | — |
| collect_failure_rate emit | yes | — | — |
| timeout_count emit | yes | — | — |
| retry_success_rate emit | yes | — | — |
| HITL-A/B/C 호출 | 0 | — | — |
| S1 scenario | pass | — | — |
| S2 scenario | pass | — | — |
| S3 scenario | pass | — | — |

### Regression 비교 (Phase 5 baseline)

| 지표 | Phase 5 (b122a23) | P0 baseline | Delta |
|------|-------------------|-------------|-------|
| VP1 | 5/5 | — | — |
| VP2 | 6/6 | — | — |
| VP3 | 5/6 | — | — |
| avg_confidence | 0.822 | — | — |
| conflict_rate | 0.000 | — | — |
| gap_resolution | 0.909 | — | — |
| Active KU | 77 | — | — |
| Total tests | 468 | — | — |

### 판정

- **Gate 결과**: — (미판정)
- **판정 일시**: —
- **readiness-report.md**: `bench/silver/japan-travel/p0-{date}-baseline/readiness-report.md`
- **비고**: —
