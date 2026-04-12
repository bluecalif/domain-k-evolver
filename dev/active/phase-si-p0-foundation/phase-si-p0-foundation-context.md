# Silver P0: Foundation Hardening — Context
> Last Updated: 2026-04-12
> Status: **Complete** (32/32, 100%) — Gate PASS

## 1. 핵심 파일

### 이 Phase 에서 읽어야 할 기존 코드

| 파일 | 이유 | 핵심 라인 |
|------|------|-----------|
| `src/graph.py` | HITL-A/B/C edge 제거 대상, 라우팅 로직 | L165~L211 (hitl edge 정의) |
| `src/nodes/collect.py` | bare-except 제거, 실패 카운터, ThreadPoolExecutor timeout | L76~L97 (이중 except), L169 (executor) |
| `src/nodes/integrate.py` | ValueError pass 제거, dispute_queue append | L270~L288 (except ValueError) |
| `src/nodes/hitl_gate.py` | S/R/E 축소 대상, 기존 A~E 분기 | 전체 |
| `src/adapters/search_adapter.py` | retry 판정 버그, timeout 추가 | L39 (retry 판정) |
| `src/adapters/llm_adapter.py` | ChatOpenAI timeout 전달 | L69 (ChatOpenAI 생성) |
| `src/config.py` | request_timeout 추가, from_env 확장 | LLMConfig, SearchConfig dataclass |
| `src/utils/state_io.py` | 복구 경로, .bak rotation | L54~L56 (JSON decode) |
| `src/utils/metrics_guard.py` | Silver 임계치 확장, interrupt 연결 | 전체 |
| `src/utils/metrics_logger.py` | 신규 metric key emit 대상 | emit 함수 |
| `src/state.py` | dispute_queue 등 State 필드 추가 | EvolverState TypedDict |
| `src/orchestrator.py` | --bench-root 격리, collect_failure_rate 집계 | run_cycles 함수 |
| `scripts/run_bench.py` | --bench-root 인자 추가 | CLI argparse |
| `scripts/run_one_cycle.py` | --bench-root 인자 추가 | CLI argparse |
| `scripts/run_readiness.py` | --bench-root 인자 추가 | CLI argparse |

### 이 Phase 에서 읽어야 할 문서

| 파일 | 내용 |
|------|------|
| `docs/silver-masterplan-v2.md` §4 (P0 행) | Phase gate 정량 기준 (verbatim) |
| `docs/silver-masterplan-v2.md` §12 | Silver bench 관리 규칙 (trial_id 정규식, INDEX 컬럼) |
| `docs/silver-masterplan-v2.md` §14 | HITL 축소 정책 (S/R/D/E 정의, keep-criteria 3개) |
| `docs/silver-implementation-tasks.md` §4 | P0 task 상세 (touched files, executable review) |
| `docs/silver-implementation-tasks.md` §12 | P0-X 인터페이스 고정 6건 |
| `dev/active/p0-p1-remediation-plan.md` | P0-B 가 흡수하는 8건 원본 분석 |

### 이 Phase 에서 생성하는 파일

| 파일 | Stage |
|------|-------|
| `bench/silver/INDEX.md` | A1 |
| `bench/silver/japan-travel/p0-{date}-baseline/` | A3 |
| `templates/si-trial-card.md` | A2 |
| `templates/si-readiness-report.md` | A2 |
| `templates/si-index-row.md` | A2 |
| `docs/silver-interface-snapshots/integrate-p0.md` | X1 |
| `docs/silver-interface-snapshots/collect-p0.md` | X2 |
| `docs/silver-interface-snapshots/metrics-keys-p0.md` | X5 |
| `bench/silver/japan-travel/p0-20260412-baseline/readiness-report.md` | D2 |
| `bench/silver/japan-travel/p0-20260412-baseline/readiness-report.json` | D2 |
| `tests/conftest.py` | X6 |

### 이 Phase 에서 수정하는 파일

| 파일 | Stage | 변경 내용 |
|------|-------|-----------|
| `src/graph.py` | C1~C3 | A/B/C edge 제거, S edge 추가, critique 라우팅 단순화 |
| `src/nodes/collect.py` | B5, B6 | executor timeout, bare-except 제거, 실패 카운터 |
| `src/nodes/integrate.py` | B7 | ValueError pass → warning + 원문 보존 |
| `src/nodes/hitl_gate.py` | C5 | S/R/E 3케이스 축소 |
| `src/adapters/search_adapter.py` | B1, B4 | retry regex, timeout |
| `src/adapters/llm_adapter.py` | B3 | ChatOpenAI timeout |
| `src/config.py` | B2, A6 | request_timeout, config snapshot |
| `src/utils/state_io.py` | B8 | .bak rotation, 복구 경로 |
| `src/utils/metrics_guard.py` | C6 | Silver 5개 임계치 |
| `src/state.py` | C7, X3, X4 | dispute_queue + provenance + 5개 신규 필드 |
| `src/utils/metrics_logger.py` | X5 | collect_failure_rate emit |
| `src/nodes/integrate.py` | X3 | provenance passthrough |
| `src/nodes/collect.py` | X3 | provenance=None 기본값 |
| `src/orchestrator.py` | A4 | --bench-root 격리 |
| `scripts/run_bench.py` | A5 | --bench-root 인자 |
| `scripts/run_one_cycle.py` | A5 | --bench-root 인자 |
| `scripts/run_readiness.py` | A5 | --bench-root 인자 |
| `tests/conftest.py` | X6 | fixture 재정비 |

---

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
```
bench/japan-travel-readiness/   — Phase 4·5 baseline 비교 데이터 (read-only)
src/config.py                   — LLMConfig, SearchConfig (timeout 추가)
bench/silver/{domain}/{trial}/state/ — trial 별 state (신규 경로)
```

### 출력 (어디에 쓰는가)
```
bench/silver/INDEX.md                           — trial 인덱스
bench/silver/japan-travel/{trial_id}/state/      — trial state
bench/silver/japan-travel/{trial_id}/trial-card.md
bench/silver/japan-travel/{trial_id}/config.snapshot.json
bench/silver/japan-travel/{trial_id}/readiness-report.md
metrics_logger → collect_failure_rate, timeout_count, retry_success_rate
```

### State 확장 (P0-C7, P0-X4)
```python
# 신규 필드 (P0 에서 선언, 이후 Phase 에서 채움)
dispute_queue: list[dict]       # P0-C7: auto-resolve 실패 KU 큐 (휘발성)
conflict_ledger: list[dict]     # P1: 충돌 감사 로그 (영속)
phase_history: list[dict]       # P2: phase transition 스냅샷
coverage_map: dict              # P4: 축 × 엔티티 그리드
novelty_history: list[float]    # P4: cycle 별 novelty 점수
```

---

## 3. 주요 결정사항

### 기존 (P0 에 영향)
| # | 결정 | 영향 |
|---|------|------|
| D-72 | HITL 축소 — inline A/B/C 제거, S/R/D/E 4세트 | Stage C 전체 |
| D-75 | `bench/silver/{domain}/{trial_id}/` 격리 + trial-card/readiness-report 의무 | Stage A |
| D-76 | P0 scope-locked — 추가 발견은 P1 이관 | 범위 제한 |
| D-84 | HITL-D 는 graph node 아님, `state.dispute_queue` append 만 | C3, C7 |
| D-87 | 트리거 검증은 manual description-walkthrough 충분 | skill 사용 기준 |

### P0 진행 중 결정
| 후보 | 내용 | 시점 |
|------|------|------|
| D-88 | `collect_node` 반환값 shape 확정 (`current_claims` + `collect_failure_rate`) | ✅ B6 완료 (e73b136) |
| D-89 | HITL-E 임계치 5개 최종값: conflict>0.25, evidence<0.55, collect_fail>0.50, staleness>0.30, avg_conf<0.60 | ✅ C4/C6 완료 (83ce974) |
| D-90 | config.snapshot.json 필드: schema_version/timestamp/git_head/llm/search/orchestrator/providers/skeleton_path/skeleton_sha256 + api_key redact | ✅ A6 완료 (`6c7f28f`) |
| D-91 | integrate_node I/O shape 동결 (4-key dict: knowledge_units, gap_map, current_claims, dispute_queue) | ✅ X1 완료 (`f67cbf3`) |
| D-92 | collect_node I/O shape 동결 (2-key dict: current_claims, collect_failure_rate) | ✅ X2 완료 (`9258832`) |
| D-93 | Claim/KU provenance 필드 = optional dict, None 기본값 (P3 에서 채움) | ✅ X3 완료 (`f7a4123`) |
| D-94 | EvolverState 5개 신규 필드: conflict_ledger, phase_history, coverage_map, novelty_history (빈 컨테이너 기본값) | ✅ X4 완료 (`e3f5659`) |
| D-95 | D1 첫 시도 Bronze seed FAIL → fresh seed + 15 cycle + Orchestrator 로 재실행하여 PASS | ✅ D1~D3 완료 (`30946ac`) |

### Stage 완료 파일 전체 (2026-04-12)
- **Stage A (`2f9117a` + `6c7f28f`)**: `bench/silver/INDEX.md`, `templates/si-*.md` 3종, `bench/silver/japan-travel/p0-20260411-baseline/`, `src/config.py` (bench_root + config snapshot), `src/utils/state_io.py` (write guard), `src/orchestrator.py` (bench_root 우선), `scripts/run_*.py` 3종 (--bench-root 인자)
- **Stage B (`e73b136`)**: `src/adapters/search_adapter.py`, `src/adapters/llm_adapter.py`, `src/config.py`, `src/nodes/collect.py`, `src/nodes/integrate.py`, `src/utils/state_io.py`
- **Stage C (`83ce974`)**: `src/graph.py` (Silver flow), `src/nodes/hitl_gate.py` (S/R/E 재작성), `src/nodes/integrate.py` (dispute_queue append), `src/state.py` (dispute_queue 필드), `src/utils/metrics_guard.py` (should_auto_pause)
- **Tests (`f21a249`)**: `tests/test_nodes/test_collect.py` +10, `tests/test_state_io.py` +9, `tests/test_adapters.py` +6, `tests/test_graph.py` +4, `tests/test_nodes/test_hitl_gate.py` 전면 재작성
- **A6 (`6c7f28f`)**: `src/config.py` (`write_config_snapshot` + `_get_git_head` + `_redact`), `scripts/run_bench.py`·`scripts/run_one_cycle.py` (load_state 직후 snapshot 호출), `tests/test_config.py` +10. 500 passed.
- **Stage X (`f67cbf3`~`cdf0a96`)**: `docs/silver-interface-snapshots/integrate-p0.md`, `collect-p0.md`, `metrics-keys-p0.md`, `src/state.py` (provenance + 5필드), `src/nodes/integrate.py` (provenance passthrough), `src/nodes/collect.py` (provenance=None), `src/utils/state_io.py` (X4 기본값), `src/utils/metrics_logger.py` (collect_failure_rate), `tests/conftest.py` (공통 fixture). 510 passed.
- **Stage D (`30946ac`)**: `bench/silver/japan-travel/p0-20260412-baseline/` (readiness-report.md, readiness-report.json, trial-card.md, state/, trajectory/, state-snapshots/), `bench/silver/INDEX.md` 2행 삽입. Gate PASS.

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙 (P0 변경 후 재검증)
- [ ] **Gap-driven**: Plan 변경 없음 (P0 은 plan 노드 미수정) — PASS (자동)
- [ ] **Claim→KU 착지성**: integrate ValueError 수정이 claim 처리 흐름 보존하는지 확인 (B7)
- [ ] **Evidence-first**: collect 실패 카운터가 EU 생성 경로에 영향 주지 않는지 확인 (B6)
- [ ] **Conflict-preserving**: HITL-C 제거 후 dispute → `dispute_queue` 경로가 충돌 보존하는지 확인 (C7)
- [ ] **Prescription-compiled**: critique → plan_modify 경로 유지 확인 (C3)

### Metrics 건강 임계치 (P0 변경 후 유지 확인)
| 지표 | 건강 | P0 영향 |
|------|------|---------|
| 근거율 ≥ 0.95 | 유지 | collect 실패 시 EU 누락 가능 → B6 에서 실패 카운터로 감시 |
| 충돌률 ≤ 0.05 | 유지 | HITL 축소가 충돌률에 영향 주는지 D1 에서 검증 |
| 평균 confidence ≥ 0.85 | 유지 | 변경 없음 |

### Silver 신규 Metrics (P0 emit 대상)
- `collect_failure_rate` — B6 에서 구현
- `timeout_count` — B5 에서 구현
- `retry_success_rate` — B1 에서 구현

### Blocking Scenario (P0 담당)
| ID | 시나리오 | 테스트 파일 | Stage |
|----|----------|-------------|-------|
| S1 | search timeout (60s hang) → hang 없음 | `tests/test_adapters/test_search_adapter.py::test_timeout_metric_emitted` | B9 |
| S2 | malformed LLM JSON fallback | `tests/test_nodes/test_collect.py::test_malformed_llm_json_fallback` | B9 |
| S3 | corrupt state.json recovery | `tests/test_state_io.py::test_corrupt_state_recovery` | B9 |

### 인코딩
- JSON read/write: `encoding='utf-8'` 명시
- Python stdout: `PYTHONUTF8=1`

### Silver 커밋 컨벤션
- prefix: `[si-p0]`
- 예: `[si-p0] Step A.1: bench/silver/INDEX.md + 템플릿 3종`
