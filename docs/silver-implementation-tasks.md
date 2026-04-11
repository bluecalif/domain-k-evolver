# Domain-K-Evolver Silver Implementation Tasks

> Status: Draft for execution
> Date: 2026-04-11
> Source of truth: `docs/silver-masterplan-v2.md` (Phase 표 §4, HITL 정책 §14, Provider 상세 §13, 벤치 관리 §12)
> Supersedes (as execution backlog): `docs/silver-implementation-task-list.md`
> Purpose: Silver masterplan v2 를 저장소 현재 상태에 정렬된 실행 가능 backlog 으로 변환

---

## 0. 이 문서의 규칙

1. **Phase 표 (masterplan §4) 가 진실**. 이 문서는 해당 표를 실행 항목 단위로 풀어낸 것이며, 표와 충돌이 생기면 masterplan 이 우선한다.
2. 모든 task 는 **touched files 를 이름 단위로** 지정한다. 없는 파일은 신규 표기 `[NEW]`.
3. 모든 phase gate 는 **정량 조건** 만 사용한다. "개선", "가시화" 등 정성 표현 금지.
4. 모든 phase 는 **blocking scenario test** (masterplan §7 의 S1~S11) 최소 1 개를 포함한다.
5. 한 task 가 2 개 이상 파일을 건드리면 파일별 substep 으로 쪼갠다.
6. Dashboard 작업은 **telemetry contract 가 merge 된 이후에만** 시작한다 (UI-first 금지).
7. 2 nd 도메인 검증 (P6) 은 "옵션 부록" 이 아니라 **Silver 완료의 exit gate**.
8. 규모 태그: `[S]` ≤ 50 LOC · `[M]` 50~200 LOC · `[L]` 200 LOC 초과. 테스트 LOC 별도.

---

## 1. 저장소 현재 상태 Δ (2026-04-11 snapshot)

실행 기준이 되는 사실. 아래와 충돌하는 가정으로 task 를 작성하면 안 된다.

- `src/graph.py` 는 매 cycle `hitl_a/b/c/d/e` 를 경유한다 (L165~L211).
- `src/nodes/remodel.py` 부재 — Phase 4 가 audit/policy/readiness 까지 끝냈으나 **구조 변경 제안 노드** 는 미구현.
- `src/adapters/providers/` 부재, `src/adapters/search_adapter.py` 단일 구현만 존재.
- `src/adapters/fetch_pipeline.py` 부재 — `collect.py` L88~L97 이 직접 `search_tool.fetch(url)` 로 top-2 URL 을 긁고 `except: pass` 로 무시.
- `src/adapters/search_adapter.py` L39 의 retry 판정이 `"5" in exc_str[:1]` — 5xx 대부분을 놓침 (P0-3).
- `src/utils/entity_resolver.py` 부재 — `integrate.py` `_find_existing_ku` 는 exact match (L28~L37).
- `src/obs/` 부재, telemetry schema 미정의.
- `bench/silver/` 부재. 기존 bench: `japan-travel/`, `japan-travel-auto/`, `japan-travel-auto-phase2-baseline/`, `japan-travel-readiness/` (4 개, 전부 legacy).
- `schemas/` 에는 KU/EU/GU/PU/policy 5 개뿐. `remodel_report` / `telemetry.v1` 없음.
- `pyproject.toml` 에 dashboard / DDG / provider 의존성 없음.
- 테스트 베이스라인: **468 tests green** (Phase 5 완료 시점). 이 문서의 모든 "테스트 수 증가" 표현은 468 기준이다.

---

## 2. Phase 의존성 및 병렬화

```
P0 ──┬── P1 ──┐
     │        ├── P2 ──┐
     ├── P3 ──┼────────┤
              └─ P4 ──┼── P5 ── P6
```

| Phase | Name | 시작 조건 | 차단 대상 | Risk owner (§8) |
|-------|------|-----------|-----------|-----------------|
| P0 | Foundation Hardening | 즉시 | 전부 | R6, R9 |
| P1 | Entity Resolution & State Safety | P0 gate pass | P2, P4, P6 | — |
| P2 | Outer-Loop Remodel 완결 | P0, P1 | P4, P6 | R3 |
| P3 | Acquisition Expansion | P0 (P1 과 병렬 가능) | P4, P5, P6 | R1, R2, R7 |
| P4 | Coverage Intelligence | P2, P3 | P5, P6 | — |
| P5 | Telemetry Contract & Dashboard | P0, P3 인터페이스 고정 후 (schema 먼저) | P6 | R4, R10 |
| P6 | Multi-Domain Validation | P1~P5 | Silver 완료 | R5, R8 |

병렬 규칙:

- **P1 ∥ P3** — P0 종료 직후 동시 착수 가능. 단, P0-X (§12) 의 **인터페이스 고정** 이 선결 조건.
- **P5-A (telemetry schema)** 는 P3 와 동시 정의 가능 (provenance 필드 공유). **P5-B (UI)** 는 P3/P4 merge 후.
- P2 는 P1 필요 — alias/canonicalize 가 remodel 제안 품질의 전제.

---

## 3. 시나리오 → Phase 매핑 (masterplan §7 의 S1~S11)

각 scenario 는 해당 Phase gate 의 **blocking test** 다. 미통과 시 phase 를 complete 로 선언하지 못한다.

| # | 시나리오 | 담당 Phase | 구현 위치 (테스트 파일) |
|---|----------|-----------|-------------------------|
| S1 | search timeout (60s hang) | P0 | `tests/test_adapters/test_search_adapter.py::test_timeout_metric_emitted` |
| S2 | malformed LLM JSON | P0 | `tests/test_nodes/test_collect.py::test_malformed_llm_json_fallback` |
| S3 | corrupt state.json | P0 | `tests/test_state_io.py::test_corrupt_state_recovery` |
| S4 | 동의어 2 개 (JR-Pass / 재팬레일패스) | P1 | `tests/test_utils/test_entity_resolver.py::test_alias_equivalence` |
| S5 | is_a (shinkansen → train) | P1 | `tests/test_utils/test_entity_resolver.py::test_is_a_inheritance` |
| S6 | conflict 보존 후 resolve | P1 | `tests/test_nodes/test_integrate.py::test_conflict_ledger_persistence` |
| S7 | 저novelty 5 cycle → audit/remodel trigger | P2 + P4 | `tests/test_nodes/test_remodel.py::test_plateau_triggers_remodel` |
| S8 | robots.txt 차단 도메인 | P3 | `tests/test_adapters/test_fetch_pipeline.py::test_robots_refusal` |
| S9 | 비용 예산 초과 → degrade | P3 | `tests/test_nodes/test_collect.py::test_cost_budget_degrade` |
| S10 | dashboard telemetry 1 cycle → schema validate | P5 | `tests/test_obs/test_telemetry_schema.py::test_cycle_emits_valid` |
| S11 | 2 nd 도메인 10 cycle → Gate #5 동등 | P6 | `tests/test_multidomain/test_smoke_run.py::test_second_domain_smoke` |

---

## 4. Phase P0. Foundation Hardening

**Goal**: silent failure 제거, Silver 벤치 격리 구조 확립, HITL 을 masterplan §14 의 4 세트 (HITL-S/R/D/E) 로 축소.

### P0-A. Silver 벤치 스캐폴딩

파일: `bench/silver/**` [NEW], `templates/si-*.md` [NEW], `src/utils/state_io.py`, `src/orchestrator.py`, `scripts/run_*.py`.

- [ ] **P0-A1** `bench/silver/INDEX.md` 생성. 컬럼: `trial_id | domain | phase | date | goal | status | readiness | notes` (masterplan §12.4 verbatim). `[S]`
- [ ] **P0-A2** 템플릿 3 종:
  - `templates/si-trial-card.md` — 실행 전: goal / config diff / 가설
  - `templates/si-readiness-report.md` — 실행 후: VP1/VP2/VP3 결과 + diff 해석
  - `templates/si-index-row.md` — INDEX 한 줄 삽입용 snippet
  `[S]`
- [ ] **P0-A3** 첫 baseline trial 경로 생성:
  - `bench/silver/japan-travel/p0-{YYYYMMDD}-baseline/`
  - 하위: `state/`, `trajectory/`, `telemetry/`, `trial-card.md`, `config.snapshot.json`
  `[S]`
- [ ] **P0-A4** `src/utils/state_io.py` 와 `src/orchestrator.py` 에 `--bench-root` 경로 격리 추가. 기존 `bench/japan-travel/` 경로에 대한 쓰기는 금지 (read-only). `[M]`
- [ ] **P0-A5** `scripts/run_bench.py`, `scripts/run_one_cycle.py`, `scripts/run_readiness.py` 에 `--bench-root` 인자 전달. 기본값 없음 (실수로 legacy bench 에 쓰는 것 방지). `[S]`
- [ ] **P0-A6** `config.snapshot.json` 자동 작성 — `src/config.py` dataclass 직렬화 + `git rev-parse HEAD` + 활성 provider list + seed skeleton hash. trial 실행 시작 시 record. `[M]`

**Executable review**: baseline trial 이 없으면 P0 gate 의 "Phase 4·5 동등 스모크" 검증 근거가 없다. 템플릿 미확정 상태에서 첫 실행을 하면 이후 trial 들과 diff 가 안 맞아 INDEX 오염. P0-A 는 runtime 로직 변경보다 **먼저** 처리한다.

### P0-B. 기존 remediation 8 건 정리

파일: `src/adapters/search_adapter.py`, `src/config.py`, `src/adapters/llm_adapter.py`, `src/nodes/collect.py`, `src/nodes/integrate.py`, `src/utils/state_io.py`, `tests/test_nodes/test_collect.py`, `tests/test_state_io.py`.

- [ ] **P0-B1** (P0-3) `search_adapter.py` L39 retry 판정 정규표현화:
  ```python
  import re
  is_retryable = bool(re.search(r"\b(429|5\d\d|rate[ _-]?limit)\b", exc_str))
  ```
  `[S]`
- [ ] **P0-B2** (P0-2a) `src/config.py`:
  - `LLMConfig.request_timeout: int = 60`
  - `SearchConfig.request_timeout: int = 30`
  - `from_env()` 에서 `LLM_REQUEST_TIMEOUT`, `SEARCH_REQUEST_TIMEOUT` 읽기
  `[S]`
- [ ] **P0-B3** (P0-2b) `src/adapters/llm_adapter.py` L69 `ChatOpenAI(..., timeout=config.request_timeout)`. `[S]`
- [ ] **P0-B4** (P0-2c) `search_adapter.py._retry_with_backoff` 에 timeout 파라미터 전달; Tavily `search`/`extract` 호출에 명시적 timeout. `[S]`
- [ ] **P0-B5** (P0-2d) `collect.py` L169 `ThreadPoolExecutor` future 수집 시 `future.result(timeout=overall_timeout)` 적용; timeout 시 per-GU 실패 카운터 증가. `[M]`
- [ ] **P0-B6** (P0-1) `collect.py` L76~L97 의 이중 bare-except 제거:
  - retry 실패 → `logger.warning("collect.search failed: query=%s exc=%s", query, exc)` 및 실패 카운터 +1
  - `search_tool.fetch(url)` 실패 → `logger.warning("collect.fetch failed: url=%s exc=%s", url, exc)` 및 실패 카운터 +1
  - `collect_failure_rate = failures / (failures + successes)` 반환값에 포함, metrics_logger 로 emit
  `[M]`
- [ ] **P0-B7** (P1-1) `integrate.py` L270~L288 의 `except ValueError: pass` 제거:
  ```python
  except ValueError as exc:
      logger.warning("integrate.conflict_evidence ID parse failed: %s", exc)
      preserved.append(raw_ref)  # 원문 보존
  ```
  `[S]`
- [ ] **P0-B8** (P1-4) `state_io.py` L54~L56 복구 경로:
  - JSON decode 실패 → `logger.error` + `{path}.bak` 존재 시 로드 시도 → 실패 시 `StateIOError` 발생 (**빈 state 로 조용히 시작 금지**)
  - 필수 필드 (`ku_id`, `entity_key`, `gu_id`) 누락 시 `logger.warning` + skip
  - save 전 기존 파일을 `.bak` 으로 회전
  `[M]`
- [ ] **P0-B9** (P1-3) 테스트 확장:
  - `tests/test_nodes/test_collect.py`: S1 (timeout), S2 (malformed JSON), empty search, duplicate claim — 최소 8 개 테스트 추가
  - `tests/test_state_io.py`: S3 (corrupt JSON), 필수필드 누락, `.bak` 복구, save 전 rotation — 최소 6 개 테스트 추가
  - `tests/test_adapters/test_search_adapter.py`: 504 retry, timeout metric, 최소 4 개 테스트 추가
  `[L]`

**Executable review**: 현재 `collect.py` 의 double-nested except 는 로깅뿐 아니라 **실패 카운터 반환 경로가 전혀 없다**. metric 만 추가하고 return shape 을 바꾸지 않으면 orchestrator 가 카운터를 집계할 수 없다. P0-B6 은 반드시 반환값까지 변경해야 한다.

### P0-C. HITL 정책 축소 (masterplan §14)

파일: `src/graph.py`, `src/nodes/hitl_gate.py`, `src/utils/metrics_guard.py`, `tests/test_graph.py`, `tests/test_nodes/test_hitl_gate.py`.

HITL 모델 전환:

| 구 (현재) | 신 (Silver v2) | 동작 |
|-----------|----------------|------|
| HITL-A (plan) | ❌ 제거 | `plan → collect` 직결 |
| HITL-B (collect) | ❌ 제거 → HITL-E 로 이관 | `collect → integrate` 직결 |
| HITL-C (integrate) | ❌ 제거 → HITL-D (배치) + HITL-E (예외) | `integrate → critique` 직결; dispute 는 `state.dispute_queue` append |
| HITL-D (audit) → HITL-D (Dispute batch, non-blocking) | 의미 전환 | 비블로킹 큐. 10-cycle audit 은 HITL-R 로 이동 |
| HITL-E (convergence warn) → HITL-E (Exception, auto-pause) | 의미 전환 | 임계치 위반 시만 `interrupt()` |
| — | ✅ HITL-S 신규 | phase 첫 cycle 1 회 seed 승인 |
| — | ✅ HITL-R 신규 (실제 구현은 P2) | remodel 제안 승인 gate |

- [ ] **P0-C1** `graph.py` 에서 edge 제거:
  - `plan → hitl_a → collect` → `plan → collect`
  - `collect` conditional edge (`route_after_collect`) → `collect → integrate` 고정 + HITL-E 분기 추가
  - `integrate` conditional edge (`route_after_integrate`) → `integrate → critique` 고정 + dispute append 는 `integrate_node` 내부에서
  `[M]`
- [ ] **P0-C2** `graph.py` 에 HITL-S edge 추가:
  - `seed → hitl_s` (phase 첫 cycle 만, `state.current_cycle == 1 and state.phase_just_started` 조건)
  - `hitl_s → mode`
  `[M]`
- [ ] **P0-C3** `route_after_critique` 단순화:
  - 10-cycle audit 은 P2 에서 remodel 경로로 대체될 것이므로 P0 에서는 `hitl_d` (audit) 호출을 **audit node 직접 호출** 로 바꿈
  - HITL-D (배치) 는 **graph edge 아님**, `dispute_queue` state 필드로만 존재
  `[M]`
- [ ] **P0-C4** `route_after_any → hitl_e` 조건부 분기 공통 함수 추가. 트리거:
  ```python
  def should_auto_pause(state) -> bool:
      g = state.get("metrics_guard", {})
      return any([
          g.get("collect_failure_rate", 0) > 0.3,
          g.get("conflict_rate", 0) > 0.4,
          g.get("fetch_failure_rate", 0) > 0.5,
          g.get("cost_regression_flag", False),
          len(state.get("dispute_queue", [])) > 20,
      ])
  ```
  각 주요 노드 후에 `should_auto_pause → hitl_e` or `→ next` 분기 적용. `[M]`
- [ ] **P0-C5** `src/nodes/hitl_gate.py` 를 HITL-S / HITL-R / HITL-E 3 케이스로 축소:
  - `gate` 파라미터 enum: `"S" | "R" | "E"` (A/B/C/D 제거, D 는 의미 전환이므로 삭제 후 HITL-R 로 흡수)
  - backward-compat: 기존 A/B/C/D 호출은 `DeprecationWarning` 1 회 + no-op
  `[M]`
- [ ] **P0-C6** `src/utils/metrics_guard.py` 확장 — Silver v2 5 개 임계치 field 추가 (위 should_auto_pause 목록과 동일). warning-only 가 아니라 `cost_regression_flag`, `dispute_queue_size` 는 실제 interrupt 로 연결. `[M]`
- [ ] **P0-C7** `EvolverState` 에 `dispute_queue: list[DisputeEntry]` 필드 추가 (`src/state.py`). `integrate_node` 에서 auto-resolve 실패 KU 는 여기에 append. `[S]`
- [ ] **P0-C8** 테스트:
  - `tests/test_graph.py`: 일반 cycle 이 inline HITL-A/B/C 를 0 회 호출함을 assert
  - `tests/test_graph.py`: HITL-S 가 phase 첫 cycle 에서만 호출됨
  - `tests/test_graph.py`: auto-pause 조건 5 개 각각이 HITL-E 로 라우팅됨
  - `tests/test_nodes/test_hitl_gate.py`: 축소된 enum 동작 + deprecation 경로
  최소 10 개 테스트.
  `[M]`

**Executable review**: P0-C 는 P2 의 `remodel_node` 를 **호출하지 않는다**. HITL-R 의 *edge* 는 P0 에서 graph 에 등록하되 payload 는 stub (empty proposal) 로 두고, 실제 remodel 로직은 P2 에서 채운다. 이렇게 나누지 않으면 P2 가 graph 를 다시 수정해야 하고 P0 테스트가 두 번 쓰러진다.

### P0-D. Silver baseline trial 재현

- [ ] **P0-D1** 기존 Phase 4·5 스모크를 `bench/silver/japan-travel/p0-{date}-baseline/` 에 재실행 (same seed, same config). `[M]`
- [ ] **P0-D2** `readiness-report.md` 작성 — VP1 ≥ 4/5, VP2 ≥ 5/6 (Phase 5 최종과 동등) 확인. 불일치 시 P0-B 변경이 정량 regression 을 일으킨 것이므로 원인 분리 후 재실행. `[S]`
- [ ] **P0-D3** `INDEX.md` 첫 행 삽입. `[S]`

### P0 phase gate (masterplan §4 정량 조건 verbatim)

- [ ] 대상 모듈 (`src/nodes/`, `src/adapters/`, `src/utils/state_io.py`) bare-except 0 건 (`grep "except Exception:" ...` 결과)
- [ ] `collect_failure_rate`, `timeout_count`, `retry_success_rate` 3 개 메트릭이 `metrics_logger` 로 emit
- [ ] 신규/수정 테스트 ≥ 20 건, 전체 green. **베이스라인 468 → ≥ 488**
- [ ] 48h soak: 임의 adapter kill 주입 → 그래프 hang 없음
- [ ] `bench/silver/japan-travel/p0-{date}-baseline/` 존재, Phase 4·5 동등 스모크 재현 (VP1 ≥ 4/5, VP2 ≥ 5/6)
- [ ] 일반 cycle 실행 시 인라인 HITL-A/B/C 호출 0 건 (graph edge 기준)
- [ ] HITL-S 는 phase 첫 cycle 1 회, HITL-E 는 trigger 조건 위반 시만 호출
- [ ] S1, S2, S3 scenario 테스트 pass

---

## 5. Phase P1. Entity Resolution & State Safety

**Goal**: canonical entity 매칭, 계층 처리, conflict 영구 보존.

**병렬 실행 주의**: P1 과 P3 는 `integrate.py` 와 `collect.py` 를 동시에 건드린다. P0-X (§12) 의 **인터페이스 고정** 이 반드시 선행돼야 conflict 없이 merge 된다.

### P1-A. 해상도 계층

파일: `src/utils/entity_resolver.py` [NEW], `src/nodes/integrate.py`, `schemas/` (skeleton validator).

- [ ] **P1-A1** `src/utils/entity_resolver.py` 신규:
  ```python
  def resolve_alias(entity_key: str, skeleton: dict) -> str: ...
  def resolve_is_a(entity_key: str, skeleton: dict) -> list[str]: ...  # parent chain
  def canonicalize_entity_key(entity_key: str, skeleton: dict) -> str: ...
  ```
  alias map 은 `skeleton["aliases"]: {canonical_key: [alias1, alias2, ...]}` 포맷. `[M]`
- [ ] **P1-A2** `integrate.py._find_existing_ku` 가 resolver 를 호출하도록 수정. 기존 exact match 경로는 resolver 뒤로 이동 (fallback). `[M]`
- [ ] **P1-A3** skeleton validator 확장 — `aliases`, `is_a` 필드가 있으면 schema validate, 없으면 통과 (backward compat). `[S]`
- [ ] **P1-A4** 기존 japan-travel skeleton 에 예시 alias/is_a 2 쌍 이상 추가 (`jr-pass` ↔ `재팬레일패스`, `shinkansen` is_a `train`). P1-C2 테스트가 이 데이터를 사용. `[S]`

### P1-B. Conflict ledger 영속화

파일: `src/state.py`, `src/nodes/integrate.py`, `src/nodes/dispute_resolver.py`, `src/utils/state_io.py`.

- [ ] **P1-B1** `state/conflict_ledger.json` 포맷 정의:
  ```json
  [{
    "ledger_id": "cl-001",
    "ku_id": "ku-...",
    "created_at": "2026-04-12T...",
    "status": "open" | "resolved",
    "conflicting_evidence": [...],
    "resolution": {"method": "evidence_weighted", "resolved_at": "...", "chosen_ku": "..."} | null
  }]
  ```
  `[S]`
- [ ] **P1-B2** `integrate_node` 에서 conflict 감지 시 ledger entry 생성, `dispute_resolver` 가 resolve 하더라도 ledger entry 는 `status=resolved` 로 유지 (**삭제 금지**). `[M]`
- [ ] **P1-B3** `state_io.py` save/load 에 ledger 포함 — 파일 부재는 빈 배열로 처리 (migration-safe). `[S]`
- [ ] **P1-B4** `dispute_queue` (P0-C7 에서 추가) 와 `conflict_ledger` 의 관계 명시: dispute_queue 는 휘발성 (auto-resolve 실패 큐), ledger 는 감사 로그. 두 구조 모두 동일 `ku_id` 를 참조할 수 있으나 독립. `[S]`

### P1-C. 검증

파일: `tests/test_utils/test_entity_resolver.py` [NEW], `tests/test_nodes/test_integrate.py`, `tests/integration/test_japan_travel_rerun.py` [NEW].

- [ ] **P1-C1** `test_entity_resolver.py`: alias 2 방향, is_a chain 2 단 이상, canonicalization idempotent, 누락 field 처리. 최소 8 테스트. `[M]`
- [ ] **P1-C2** `test_integrate.py`: S4, S5, S6 scenario (위 §3 참조). 이미 존재하는 파일에 추가. `[M]`
- [ ] **P1-C3** `test_japan_travel_rerun.py`: P0 baseline trial state 를 입력으로 재통합 → 중복 KU ≥ 15% 감소 assert. 감소 기준은 `unique entity_key` 수로 측정. `[M]`
- [ ] **P1-C4** ledger 영속화 테스트: 10 cycle run 후 모든 dispute 가 ledger 에 존재, resolved 전환 후에도 `ledger_id` 조회 가능. `[S]`

### P1 phase gate (masterplan §4)

- [ ] 단위 테스트: 동의어 (JR-Pass / 재팬레일패스), is_a (shinkansen is_a train) 각각 pass
- [ ] japan-travel 재실행: 중복 KU 수 **≥ 15% 감소** (P0 baseline 대비)
- [ ] 충돌 KU **100% 가 ledger 에 영구 보존** (resolve 후에도 감사 가능)
- [ ] S4, S5, S6 scenario pass
- [ ] 테스트 수 ≥ 488 + 20 (P1 신규)

---

## 6. Phase P2. Outer-Loop Remodel 완결

**Goal**: audit 결과를 구조 변경 제안 (merge/split/reclassify/policy/gap rule) 으로 compile 하고 phase transition 저장.

### P2-A. Remodel node + schema

파일: `src/nodes/remodel.py` [NEW], `schemas/remodel_report.schema.json` [NEW], `src/state.py`.

- [ ] **P2-A1** `src/nodes/remodel.py` 신규. 입력: audit 결과 + 현 state, 출력: `RemodelReport`. Phase 4 `audit.py` 의 4 분석함수 결과를 소비하며 **중복 분석 금지**. `[L]`
- [ ] **P2-A2** `schemas/remodel_report.schema.json` 필드:
  ```
  report_id, created_at, source_audit_id,
  proposals: [
    {type: "merge" | "split" | "reclassify" | "alias_canonicalize"
          | "source_policy" | "gap_rule",
     rationale: str, target_entities: [...], params: {...},
     expected_delta: {metric, before, after}}
  ],
  rollback_payload: {...},
  approval: {status: "pending" | "approved" | "rejected", actor, at}
  ```
  `[S]`
- [ ] **P2-A3** `EvolverState.phase_number: int` 및 `phase_history: list[PhaseSnapshot]` 필드 추가. `[S]`
- [ ] **P2-A4** `state/phase_{N}/` 디렉토리 생성 로직 — phase bump 시 현 state 스냅샷을 해당 경로로 복사. `[M]`

### P2-B. Graph/orchestrator 통합

파일: `src/graph.py`, `src/orchestrator.py`, `src/nodes/hitl_gate.py`.

- [ ] **P2-B1** `graph.py`: `critique → audit → remodel → hitl_r → (approve) phase_bump | (reject) plan_modify` 경로 추가. 조건: `cycle > 0 and cycle % 10 == 0 and audit.has_critical`. `[M]`
- [ ] **P2-B2** `hitl_gate.py` 에 HITL-R 핸들러 완성 (P0-C5 의 stub 를 구현으로 승격). `[M]`
- [ ] **P2-B3** `orchestrator.py` 에 phase transition 핸들러 — 승인된 report 를 실제 skeleton 수정으로 apply, 실패 시 rollback 경로 실행. `[M]`
- [ ] **P2-B4** Rejection/rollback path: report 가 `rejected` 로 종료되면 `active` state 는 변경 없음, `rollback_payload` 검증만 수행. `[M]`

### P2-C. 검증

파일: `tests/test_nodes/test_remodel.py` [NEW].

- [ ] **P2-C1** merge 시나리오: 엔티티 중복률 30%+ 합성 상황 → remodel 이 merge proposal 생성. `[S]`
- [ ] **P2-C2** split 시나리오: 하나의 entity_key 에 상반된 axis_tag 2 개 이상 → split proposal. `[S]`
- [ ] **P2-C3** reclassify 시나리오: 카테고리 부정합 → reclassify proposal. `[S]`
- [ ] **P2-C4** rollback 시나리오: 승인 거부 → `state` diff = ∅. `[S]`
- [ ] **P2-C5** S7 (저 novelty 5 cycle → audit/remodel trigger) — P4 와 공유되지만 여기서는 **trigger 경로** 만 assert. coverage 근거는 P4-C 에서. `[M]`
- [ ] **P2-C6** schema 양방향 테스트: 유효 report pass, 필수 필드 누락 report fail. `[S]`

### P2 phase gate

- [ ] Remodel report 가 schema 를 validate
- [ ] 승인된 remodel 이 다음 cycle 의 skeleton/state 에 실제 반영됨
- [ ] Rollback 경로가 승인 전 state 로 완전 복귀 (state diff = ∅)
- [ ] 합성 시나리오에서 entity 중복률 30%+ 를 remodel 이 탐지·제안
- [ ] S7 scenario (trigger 부분) pass
- [ ] 테스트 수 ≥ P1 종료 시점 + 15

---

## 7. Phase P3. Acquisition Expansion

**Goal**: `collect.py` 를 SEARCH → FETCH → PARSE 3 단계로 분리, provider 플러그인 구조 도입, 소스 provenance/diversity/cost 측정.

### P3-A. Provider 플러그인 (SEARCH 단계)

파일 (전부 [NEW]): `src/adapters/providers/__init__.py`, `.../base.py`, `.../tavily_provider.py`, `.../ddg_provider.py`, `.../curated_provider.py`.

- [ ] **P3-A1** `base.py`: `SearchProvider` Protocol + `SearchResult` dataclass (필드: `url, title, snippet, score, provider_id, trust_tier`). masterplan §13.2 verbatim. `[S]`
- [ ] **P3-A2** `tavily_provider.py`: 기존 `search_adapter.py` 의 `TavilySearchAdapter.search` 로직을 provider 로 이식. `_retry_with_backoff` 는 `search_adapter.py` 에 유지하고 import 재사용. **fetch 는 이 파일에서 제거** (FetchPipeline 로 이동). `[M]`
- [ ] **P3-A3** `ddg_provider.py`: `duckduckgo-search` 라이브러리 사용, API key 없음, `trust_tier="secondary"`. 호출은 `policy.enable_ddg_fallback` true 일 때만. `[M]`
- [ ] **P3-A4** `curated_provider.py`: **검색 안 함**, skeleton `preferred_sources` 중 `context.axis_tags`/`category` 매칭 URL 을 `SearchResult(snippet="curated", score=1.0, trust_tier="primary")` 로 반환. `[M]`
- [ ] **P3-A5** `src/adapters/search_adapter.py` 는 `TavilySearchAdapter` 단일 책임 → retry 유틸 제공자로 축소 혹은 deprecated wrapper 로 표시. 기존 테스트는 provider 경유로 점진 이동. `[M]`

### P3-B. FetchPipeline (FETCH 단계)

파일: `src/adapters/fetch_pipeline.py` [NEW].

- [ ] **P3-B1** `FetchPipeline.fetch_many(urls, *, robots_check, max_bytes, content_type_allowlist, timeout) -> list[FetchResult]`. `[L]`
- [ ] **P3-B2** `FetchResult` 필드: `url, fetch_ok, content_type, retrieved_at, bytes_read, trust_tier, failure_reason`. `[S]`
- [ ] **P3-B3** Robots.txt 캐시 (in-memory, per-run). 거부 도메인은 즉시 `fetch_ok=False, failure_reason="robots"`. `[M]`
- [ ] **P3-B4** Content-type 필터 기본값: `{"text/html", "application/xhtml+xml"}`. 거부 시 `failure_reason="content_type"`. `[S]`
- [ ] **P3-B5** `max_bytes` 초과 시 자르고 `failure_reason` 이 아닌 `bytes_read < total_size` 로 표현; `trust_tier` 유지. `[S]`
- [ ] **P3-B6** Rate-limit 인지: 도메인별 최소 간격 (config 값) 준수. P3-C4 와 연결. `[M]`

### P3-C. Collect 리팩터 + provenance + 비용

파일: `src/nodes/collect.py`, `src/config.py`, `src/state.py`.

- [ ] **P3-C1** `collect.py` 리팩터 — 외부 노드 인터페이스 보존:
  - Step 1. SEARCH: policy 에 따라 providers 구성 → 병렬 `search`
  - Step 2. FETCH: URL dedupe → top-N → `FetchPipeline.fetch_many`
  - Step 3. PARSE: provenance 태깅 포함 claim 추출
  `[L]`
- [ ] **P3-C2** 기존 `collect.py` L88~L97 의 직접 `search_tool.fetch(url)` 삭제 — 기능은 FetchPipeline 로 완전 이관. `[S]`
- [ ] **P3-C3** Claim/EU 구조에 provenance 필드 추가:
  ```
  providers_used: list[str]
  domain: str
  fetch_ok: bool
  fetch_depth: int
  content_type: str
  retrieved_at: str
  trust_tier: str
  ```
  P1 의 KU 저장 경로와 충돌 없음을 확인. `[M]`
- [ ] **P3-C4** `src/config.py SearchConfig` 확장:
  - `enable_tavily: bool = True`
  - `enable_ddg_fallback: bool = False`
  - `fetch_top_n: int = 5`
  - `max_bytes_per_url: int = 512_000`
  - `entropy_floor: float = 2.0`
  - `k_per_provider: int = 3`
  - `per_domain_min_interval_s: float = 1.0`
  `[S]`
- [ ] **P3-C5** 다이버시티 메트릭 per cycle:
  - `domain_entropy = H({netloc(url) for url in results})`
  - `provider_entropy = H({provider_id for result in results})`
  Shannon entropy, log2, bits 단위. metrics_logger 로 emit. `[M]`
- [ ] **P3-C6** 비용 가드 per cycle:
  - `cycle_llm_token_budget: int = 100_000`
  - `cycle_fetch_bytes_budget: int = 10_000_000`
  초과 시 `cost_regression_flag=True` → P0-C4 의 HITL-E trigger 와 직결. 초과 직전에 `fetch_top_n --`, `k_per_provider --` 로 **degrade 모드**. `[M]`

### P3-D. 의존성 + 테스트

파일: `pyproject.toml`, `tests/test_adapters/test_providers/**` [NEW], `tests/test_adapters/test_fetch_pipeline.py` [NEW], `tests/test_nodes/test_collect.py`.

- [ ] **P3-D1** `pyproject.toml` 의존성 추가: `duckduckgo-search` (optional), 기존 `tavily-python` 유지. Dashboard 의존성은 P5 로 미룸. `[S]`
- [ ] **P3-D2** provider 테스트: tavily happy path, tavily 실패 시 fallback, DDG gated (entropy_floor 아래에서만), curated 의 검색-없음 동작. 최소 12 테스트. `[M]`
- [ ] **P3-D3** FetchPipeline 테스트: robots 거부 (S8), content-type 거부, timeout, `max_bytes` 자르기, 도메인 rate-limit 간격. 최소 10 테스트. `[M]`
- [ ] **P3-D4** collect 통합 테스트: mixed provider 결과 + provenance end-to-end + S9 (비용 budget degrade). 최소 6 테스트. `[M]`
- [ ] **P3-D5** `search_adapter` 의 legacy 테스트 경로가 provider 리팩터에 의해 깨지지 않도록 mig test — 1 주 deprecation grace. `[S]`

**Executable review**: `CuratedSourceProvider` 는 SEARCH 만 한다. 과거 `FetchOnlyProvider` 이름을 그대로 쓰면 fetch 가 provider 안에 남아 Step 2 와 겹친다. P3-A4 의 rename 은 문서 변경이 아니라 **코드/테스트/문서 전부 일괄**. 이름이 흐려지면 P3-C1 리팩터가 반쯤만 되고 provenance 가 두 갈래에서 나온다.

### P3 phase gate (masterplan §4 정량 조건 verbatim)

- [ ] Fetch 성공률 **≥ 80%** on japan-travel seed queries
- [ ] Claim 당 평균 EU 수 **≥ 1.8** (baseline ≈ 1.0)
- [ ] `domain_entropy` **≥ 2.5 bits** on ref cycle (≥ 6 고유 도메인 평형 기여)
- [ ] Cycle 당 LLM 비용 **≤ baseline × 2.0** (cost regression 방지)
- [ ] Robots.txt 거부 도메인 차단 테스트 pass (S8)
- [ ] Cost budget 초과 시 degrade 모드 동작 (S9)
- [ ] Provenance 필드가 KU/EU 저장 → load 왕복 보존
- [ ] 테스트 수 ≥ P1 종료 + 35 (P2 와 병렬 착수 시 중복 집계 주의)

---

## 8. Phase P4. Coverage Intelligence

**Goal**: plan 이 novelty/overlap/deficit 근거로 target 선택, critique 가 metric 기반 처방.

### P4-A. Metrics primitives

파일: `src/utils/novelty.py` [NEW], `src/utils/coverage_map.py` [NEW], `src/state.py`.

- [ ] **P4-A1** `novelty.py`: cycle-to-cycle Jaccard (claims), token overlap, entity overlap. `[M]`
- [ ] **P4-A2** `coverage_map.py`: `{axis: {bucket: {ku_count, deficit_score}}}` 구조. deficit = 1 - min(1, ku_count / target_count). `[M]`
- [ ] **P4-A3** `EvolverState` 에 `novelty_history: list[float]`, `coverage_map: dict` 필드 추가. 저장/로드 확장. `[S]`

### P4-B. Plan/Critique/Plateau 통합

파일: `src/nodes/plan.py`, `src/nodes/critique.py`, `src/utils/plateau_detector.py`.

- [ ] **P4-B1** `plan.py`: 각 target 에 `reason_code` 필드. enum: `deficit:{axis}={bucket}`, `plateau:novelty<{thr}`, `audit:merge_pending`, `remodel:pending`, `seed:initial`. `[M]`
- [ ] **P4-B2** `critique.py`: 처방이 `overlap > 0.8` → `jump`, `coverage_deficit > 0.5` → `explore` 등 machine-readable rule 로 표현. 자유 텍스트 근거는 보조 필드. `[M]`
- [ ] **P4-B3** `plateau_detector.py`: 기존 growth-rate 휴리스틱 + novelty 기반 trigger (novelty < 0.1 for 5 cycles). `[M]`
- [ ] **P4-B4** `remodel_pending` state 가 plan reason_code 에 영향 (`reason_code="remodel:pending"` 로 목표 보수화). `[S]`

### P4-C. 검증

파일: `tests/test_utils/test_novelty.py` [NEW], `tests/test_utils/test_coverage_map.py` [NEW], `tests/test_nodes/test_plan.py`, `tests/test_integration/test_plateau_scenario.py` [NEW].

- [ ] **P4-C1** novelty 단위 테스트: 완전 겹침 → 0, 완전 새로 → 1, 부분. `[S]`
- [ ] **P4-C2** reason-code 생성 테스트: 5 개 enum 각각. `[S]`
- [ ] **P4-C3** S7 full scenario: 동일 seed 5 cycle 반복 → plateau detect → audit → remodel proposal 도달. P2-C5 의 trigger 테스트를 확장. `[M]`
- [ ] **P4-C4** novelty/overlap 값이 telemetry emit 경로에 노출됨 (P5-A 와 계약 확정). `[S]`

### P4 phase gate

- [ ] plan output 의 **모든** target 이 reason_code 보유
- [ ] 10 cycle 연속 run 에서 novelty 평균 **≥ 0.25**
- [ ] 인위적 plateau (동일 seed 5 cycle) → audit/remodel trigger 발동
- [ ] S7 scenario pass (P2 와 공동)
- [ ] novelty/overlap/coverage 가 telemetry 계약의 필드로 노출

---

## 9. Phase P5. Telemetry Contract & Dashboard

**Goal**: telemetry 계약을 먼저 고정하고, 그 위에 단일 운영자용 로컬 대시보드를 구축.

**실행 순서 필수**: P5-A (schema + emit) 완료 전 P5-B (UI) 착수 금지. V1 의 "UI 스프롤" 재발 방지.

### P5-A. Telemetry 계약

파일: `schemas/telemetry.v1.schema.json` [NEW], `src/obs/__init__.py` [NEW], `src/obs/telemetry.py` [NEW], `src/orchestrator.py`, 각 노드.

- [ ] **P5-A1** `schemas/telemetry.v1.schema.json` 필수 필드:
  ```
  trial_id, phase, cycle, mode, timestamp,
  metrics: {evidence_rate, conflict_rate, novelty, overlap,
            domain_entropy, provider_entropy,
            llm_tokens, fetch_bytes, wall_clock_s,
            collect_failure_rate, fetch_failure_rate, cost_regression_flag},
  gaps: {open, resolved, plateau},
  failures: [...],
  providers_used: [...],
  audit_summary: {...},
  hitl_queue: {seed, remodel, exception},
  dispute_queue: [...]
  ```
  masterplan §4 P5 및 §15 next-action 4 verbatim 포함. `[M]`
- [ ] **P5-A2** `src/obs/telemetry.py` — emitter 구현, jsonl append-only, atomic write (`*.jsonl.tmp → rename`). `[M]`
- [ ] **P5-A3** 노드 경계 emit hook — `orchestrator.py` 의 cycle 루프에 단일 call site (per-node hook 은 과설계). `[M]`
- [ ] **P5-A4** 출력 경로: `bench/silver/{domain}/{trial_id}/telemetry/cycles.jsonl` + 필요 시 `events.jsonl`. `[S]`
- [ ] **P5-A5** 스키마 계약 테스트: emit → validator pass (positive), 필수필드 누락 (negative). `tests/test_obs/test_telemetry_schema.py` [NEW]. S10 scenario. `[M]`

### P5-B. Dashboard 구현

전제: P5-A 완료 + P3/P4 interfaces merge.

파일 ([NEW]): `src/obs/dashboard/__init__.py`, `src/obs/dashboard/app.py`, `src/obs/dashboard/views/*.py`, `src/obs/dashboard/templates/*.html`, `src/obs/dashboard/static/*.js`.

- [ ] **P5-B1** FastAPI 앱 bootstrap. localhost 바인딩만, 인증 없음, 단일 운영자. `[M]`
- [ ] **P5-B2** 의존성: `fastapi`, `uvicorn`, `jinja2`, `htmx`(via CDN or vendored), `chart.js`(CDN). `pyproject.toml` extras: `[dashboard]`. `[S]`
- [ ] **P5-B3** Views (masterplan §4 P5 verbatim):
  - Overview
  - Cycle timeline
  - Gap coverage map
  - Source reliability
  - Conflict ledger
  - **HITL inbox (탭 3)**: `[Seed/Remodel 승인]` / `[Dispute 배치 검토]` / `[Exception 알림]` (masterplan §14.6)
  - Remodel review
  `[L]`
- [ ] **P5-B4** Data source: `bench/silver/**/telemetry/*.jsonl` + `state/conflict_ledger.json` + `state/phase_{N}/remodel_report.json`. Stub 데이터 금지 — 실제 artifact 를 읽는다. `[M]`
- [ ] **P5-B5** 운영자 가이드 `docs/operator-guide.md` 작성. ≤ 20 페이지, 기존 artifact 링크 위주, gate 정의 중복 금지. `[M]`

### P5-C. 검증

- [ ] **P5-C1** schema 계약 테스트 (P5-A5 와 동일, 재검증).
- [ ] **P5-C2** fixture telemetry (100 cycle) 로드 → 모든 view 가 **10 s 이내** 응답. `tests/test_obs/test_dashboard_load.py` [NEW]. `[M]`
- [ ] **P5-C3** Self-test scenario: 기록된 "slowdown" fixture 로 운영자가 **3 분 이내** 원인 식별 가능 (manual run, 결과는 `docs/operator-guide.md` 의 walkthrough 에 기록). `[M]`
- [ ] **P5-C4** LOC 하드 리밋 측정: `cloc src/obs/dashboard` **≤ 2000 LOC** (masterplan R4 리스크 완화). 초과 시 scope 컷. `[S]`

### P5 phase gate

- [ ] Telemetry schema 가 emit 데이터를 validate
- [ ] Dashboard 가 100-cycle fixture 를 모든 view 에서 10 s 이내 로드
- [ ] HITL/dispute/remodel view 가 **실제** telemetry/ledger artifact 를 소비 (stub 금지)
- [ ] Dashboard LOC ≤ 2000 (하드 리밋)
- [ ] S10 scenario pass
- [ ] `docs/operator-guide.md` 존재, 5 페이지 이상 walkthrough 포함

---

## 10. Phase P6. Multi-Domain Validation

**Goal**: Silver 가 japan-travel-specific 이 아님을 2 nd 도메인으로 실증.

### P6-A. 도메인 선정

- [ ] **P6-A1** 후보 3 개 중 1 개 선택 (masterplan §4 P6 후보: 국내 부동산 / 오픈소스 LLM 생태계 / 한국 세법). **선정 기준**: japan-travel 대비 {time horizon, hierarchy depth, source language} 3 축 중 **2 축 이상** 이질. `[S]`
- [ ] **P6-A2** 선정 rationale 을 `bench/silver/{domain}/trial-card.md` 에 작성. 선정 기준 매트릭스 포함. `[S]`
- [ ] **P6-A3** skeleton 작성 (`aliases`, `is_a`, `preferred_sources` 포함), seed pack 작성. `[M]`

### P6-B. Smoke validation

- [ ] **P6-B1** 10 cycle smoke run (isolated bench root). `[L]`
- [ ] **P6-B2** Readiness report: Gate #5 **동등 기준** (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6) 통과. `[M]`
- [ ] **P6-B3** Framework-vs-domain delta memo — framework 수정 ≤ **5 건** (초과 시 일반화 미흡으로 P1~P4 재방문). 한글 출처 처리 에러 0. `[M]`

### P6-C. 검증 파일

- [ ] **P6-C1** `tests/test_multidomain/test_smoke_run.py` — S11 scenario. 2 nd 도메인 smoke 를 CI 에서 1 cycle 만 돌리는 축소 버전. `[M]`

### P6 phase gate (masterplan §4)

- [ ] 2 nd 도메인 10 cycle 내 Gate #5 동등 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6) 통과
- [ ] 프레임워크 레벨 코드 수정 **≤ 5 건**
- [ ] 한글 출처 처리 에러 **0** (masterplan R8)
- [ ] S11 scenario pass
- [ ] Final Silver readiness 리포트 2 개 도메인 모두 참조

---

## 11. Cross-phase 제어 task

- [ ] **X1** Phase 가 끝날 때마다 `bench/silver/INDEX.md` 에 row 1 개 append (readiness 결과 포함). `[S]`
- [ ] **X2** `dev/active/p0-p1-remediation-plan.md` 는 P0 완료 시점에 **deprecated** 표기 + v2 로 링크. 삭제 금지 (감사 보존). `[S]`
- [ ] **X3** 신규 schema/contract 는 positive + negative validation 테스트 각 1 개 이상. `[S]`
- [ ] **X4** 신규 디렉토리에 Python import 가 필요하면 `__init__.py` 반드시 추가. `[S]`
- [ ] **X5** 신규 운영자 문서는 gate 정의를 재진술하지 말고 canonical artifact 로 링크. `[S]`
- [ ] **X6** 각 Phase 종료 시 리스크 레지스터 (masterplan §8) 재평가 — L/I 변경 시 masterplan 에 PR. `[S]`
- [ ] **X7** LLM/비용 metrics (`llm_tokens_per_cycle`, `fetch_bytes_per_cycle`) 는 P0 에서 **metric stub** 이라도 emit 시작 (값은 0). P3 에서 실제 값 주입. 스키마 계약 역전 방지. `[S]`

---

## 12. P0 종료 시점 인터페이스 고정 (P0-X, R9 완화)

P1/P3 병렬 착수 전 **반드시** merge 돼야 하는 인터페이스 고정 항목. 이 목록이 완료되기 전에는 P1/P3 branch 를 만들지 않는다.

- [ ] **P0-X1** `integrate_node` 의 입력/출력 dict shape 동결 — P1 resolver 추가는 내부 구현만 변경, 외부 키 유지. 스냅샷을 `docs/silver-interface-snapshots/integrate-p0.md` 에 기록.
- [ ] **P0-X2** `collect_node` 의 입력/출력 dict shape 동결 — P3 리팩터가 같은 외부 contract 를 유지. 스냅샷을 `docs/silver-interface-snapshots/collect-p0.md` 에 기록.
- [ ] **P0-X3** `Claim` / `EU` dataclass 의 **provenance 필드 미리 예약** — P0 에서 optional 로 필드만 선언하고 기본값 None. P3 에서 실제 채움. 스키마 역전 방지.
- [ ] **P0-X4** `EvolverState` 의 `dispute_queue`, `conflict_ledger`, `phase_history`, `coverage_map`, `novelty_history` **모든 필드 선언** 을 P0 에서 일괄 완료 (기본값 빈 컨테이너). P1~P4 가 값만 채운다. state_io save/load backward-compat 보장.
- [ ] **P0-X5** `metrics_logger` 의 metric key 전체 목록 동결 — 새 key 는 반드시 P0 문서 업데이트 후 추가.
- [ ] **P0-X6** `tests/conftest.py` 에 공통 fixture 재정비 — P1/P3 가 같은 fixture 이름을 다르게 쓰는 충돌 방지.

---

## 13. 권장 실행 순서 (저장소 내부)

```
1.  P0-A (벤치 스캐폴딩)
2.  P0-B1~B4 (retry 버그 + timeout)
3.  P0-B5~B9 (collect 로깅 + state IO 복구 + 테스트)
4.  P0-C (HITL 축소)
5.  P0-X (인터페이스 고정)
6.  P0-D (baseline trial 재현) + phase gate
7.  P1-A ∥ P3-A  (parallel, 공유 파일 없음)
8.  P1-B ∥ P3-B
9.  P1-C ∥ P3-C, P3-D
10. P2-A ~ P2-C (P1 완료 의존)
11. P4-A ~ P4-C (P2, P3 완료 의존)
12. P5-A (P3/P4 provenance·novelty 확정 후)
13. P5-B ~ P5-C
14. P6-A ~ P6-C
15. Silver readiness review
```

근거:
- **P0-A 가 최우선** — baseline 없이 P0 gate 판정 자체가 불가능.
- **P0-X 가 P1/P3 병렬의 전제** — 인터페이스 고정 없이 merge 하면 R9 발생.
- **P5-A 가 P5-B 를 엄격히 선행** — v1 의 UI-first 실패 재발 방지 (masterplan §11 비교).
- **P6 는 반드시 마지막** — P1~P5 가 모두 끝나지 않으면 framework 수정 건수가 폭증해 gate 의 "≤ 5 건" 을 넘는다.

---

## 14. Silver 완료 체크리스트

- [ ] P0 gate 전 항목 pass (§4 gate)
- [ ] P1 gate 전 항목 pass, conflict ledger 영구 보존 확인
- [ ] P2 gate 전 항목 pass, remodel 경로 실행 가능 + rollback 검증
- [ ] P3 gate 전 항목 pass (fetch ≥ 80%, domain_entropy ≥ 2.5 bits, 비용 ≤ 2×)
- [ ] P4 gate 전 항목 pass, reason_code 100% 커버
- [ ] P5 gate 전 항목 pass, dashboard LOC ≤ 2000
- [ ] P6 gate 전 항목 pass, framework 수정 ≤ 5 건, 한글 에러 0
- [ ] S1~S11 scenario 11 개 전부 pass
- [ ] 5 대 불변원칙 machine-check green
- [ ] Test 수 ≥ 468 + (P0 20 + P1 20 + P2 15 + P3 35 + P4 10 + P5 15 + P6 5) = **≥ 588**
- [ ] Cycle LLM 비용 regression 없음 (baseline 대비 ≤ 2.0×)
- [ ] 운영자 가이드 5 페이지 이상 walkthrough
- [ ] `bench/silver/INDEX.md` 에 P0 baseline + 2 nd 도메인 smoke 행 존재
- [ ] Silver readiness 리포트 승인

---

## 15. 즉시 착수 가능한 다음 액션

1. `dev/active/phase-si-p0-foundation/` 생성 (`-plan.md`, `-context.md`, `-tasks.md`, `debug-history.md` 4 종).
2. `bench/silver/` 스캐폴딩 + `INDEX.md` + 템플릿 3 종 작성 (**runtime 변경 전에**).
3. P0-B 실행 순서: P0-B1 (retry 버그) → P0-B6 (collect 로깅) → P0-B2~B5 (timeout wiring) → P0-B7 (integrate 로깅) → P0-B8 (state IO 복구) → P0-B9 (테스트).
4. P0-C (HITL 축소) 는 P0-B 와 독립적이므로 병렬 착수 가능, 단 merge 순서는 P0-B → P0-C (그래프 테스트 회귀 최소화).
5. P0-X 인터페이스 스냅샷은 P0-B/P0-C merge 직후, P1/P3 branch 분기 **직전**.
6. Telemetry schema 초안 (`schemas/telemetry.v1.schema.json`) 은 P3 실행 전에 **필드명만이라도** 합의 — P3 provenance 와 field 이름 동기화.
7. `dev/active/p0-p1-remediation-plan.md` 는 P0 gate pass 직후 deprecated 표기.
