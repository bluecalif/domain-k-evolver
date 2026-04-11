# Domain-K-Evolver Silver Implementation Task List

> Status: Draft for execution
> Date: 2026-04-11
> Source of truth: `docs/silver-masterplan-v2.md`
> Purpose: turn the Silver masterplan into an executable, dependency-safe implementation backlog for this repository

---

## 1. Scope and execution assumptions

This document is stricter than the masterplan. Every task below is written against the current repository state as of 2026-04-11:

- `src/graph.py` still routes through `hitl_a/b/c/d/e` every cycle.
- `src/nodes/remodel.py` does not exist.
- `src/adapters/providers/` does not exist.
- `src/adapters/fetch_pipeline.py` does not exist.
- `src/obs/` does not exist.
- `schemas/` directory exists, but Silver schemas referenced by v2 are not yet present.
- `pyproject.toml` does not yet include dashboard/provider dependencies beyond current core packages.

Execution policy for this task list:

- A phase is not considered started unless its prerequisites are merged or intentionally stubbed in the phase itself.
- Every code task must name touched files before implementation starts.
- Every phase ends with code verification plus at least one artifact under `bench/silver/`.
- Dashboard work must follow telemetry contract finalization. UI-first work is out of order.
- Second-domain validation is an exit gate, not an optional appendix.

---

## 2. Phase dependency graph

| Phase | Name | Can start when | Blocks |
|------|------|----------------|--------|
| P0 | Foundation Hardening | immediately | all later phases |
| P1 | Entity Resolution and State Safety | P0 done | P2, P4, P6 |
| P2 | Outer-Loop Remodel | P0 and P1 done | P4, P6 |
| P3 | Acquisition Expansion | P0 done | P4, P5, P6 |
| P4 | Coverage Intelligence | P2 and P3 done | P5, P6 |
| P5 | Telemetry Contract and Dashboard | P0, P3, P4 done | P6, final signoff |
| P6 | Multi-Domain Validation | P1, P2, P3, P4, P5 done | Silver completion |

Parallelism rule:

- P1 and P3 may proceed in parallel after P0.
- P2 must wait for P1 because remodel output depends on entity/canonicalization semantics.
- P5 may begin with telemetry contract work after P3/P4 interfaces stabilize, but dashboard UI must wait until schema and emit path are merged.

---

## 3. Deliverable map

| Area | Existing base | New/changed artifacts required |
|------|---------------|-------------------------------|
| Bench | `bench/` | `bench/silver/`, `bench/silver/INDEX.md`, trial templates, per-trial state/telemetry/readiness outputs |
| Foundation | `src/nodes/collect.py`, `src/utils/state_io.py`, `src/config.py`, `src/adapters/search_adapter.py` | timeout/retry/failure hardening, bench-root isolation, HITL simplification |
| Resolution | `src/nodes/integrate.py`, `src/state.py` | `src/utils/entity_resolver.py`, conflict ledger persistence, alias/is_a validation |
| Remodel | `src/nodes/audit.py`, `src/graph.py`, `src/orchestrator.py` | `src/nodes/remodel.py`, remodel report schema, phase transition storage |
| Acquisition | `src/nodes/collect.py`, `src/adapters/search_adapter.py` | `src/adapters/providers/*`, `src/adapters/fetch_pipeline.py`, provenance fields, diversity metrics |
| Coverage | `src/nodes/plan.py`, `src/nodes/critique.py`, `src/utils/plateau_detector.py` | novelty utility, coverage map, reason codes, plateau-trigger integration |
| Observability | `src/utils/metrics_logger.py`, `src/utils/metrics_guard.py` | telemetry schema, telemetry emitter, `src/obs/*`, operator guide |

---

## 4. Execution backlog

## Phase P0. Foundation Hardening

Goal: remove silent failure, establish reproducible Silver bench structure, and simplify graph/HITL to the v2 model.

### P0-A. Bench scaffolding and templates

- [ ] **P0-A1** Create `bench/silver/INDEX.md` with registry columns from v2 section `12.4`. `[S]`
- [ ] **P0-A2** Create per-trial template set:
  - `templates/si-trial-card.md`
  - `templates/si-readiness-report.md`
  - `templates/si-index-row.md`
  `[S]`
- [ ] **P0-A3** Create first baseline path skeleton:
  - `bench/silver/japan-travel/p0-{YYYYMMDD}-baseline/`
  - child dirs: `state/`, `trajectory/`, `telemetry/`
  `[S]`
- [ ] **P0-A4** Extend state save/load entrypoints so a trial can run against an isolated root instead of writing into legacy `bench/japan-travel/`. `[M]`

Executable review:

- This must land before any Silver validation run, otherwise P0-P6 artifacts will mix with legacy bench outputs.
- `src/utils/state_io.py` and `src/orchestrator.py` are the correct integration points. No new runner should bypass them.

Definition of done:

- A dummy trial can be created and loaded without touching legacy bench directories.
- `INDEX.md` row format is fixed before first real Silver run.

### P0-B. Remediation backlog closure

- [ ] **P0-B1** Fix retry classification bug in `src/adapters/search_adapter.py` per active remediation plan. `[S]`
- [ ] **P0-B2** Add request timeout fields to `src/config.py`:
  - `LLMConfig.request_timeout`
  - `SearchConfig.request_timeout`
  `[S]`
- [ ] **P0-B3** Thread timeout wiring in `src/nodes/collect.py` and adapter calls. `[M]`
- [ ] **P0-B4** Replace silent search/fetch failure handling in `src/nodes/collect.py` with structured warning logs and failure counters. `[M]`
- [ ] **P0-B5** Replace `ValueError: pass` handling in `src/nodes/integrate.py` with logged preservation path. `[S]`
- [ ] **P0-B6** Harden `src/utils/state_io.py` for JSON decode failure, required-field validation, and recovery-from-backup path. `[M]`
- [ ] **P0-B7** Expand `tests/test_nodes/test_collect.py` and `tests/test_state_io.py` for timeout, malformed JSON, empty search result, duplicate claim, and corrupted-state scenarios. `[M]`

Executable review:

- These changes target real current failure points in `collect.py`, `integrate.py`, and `state_io.py`; no architecture work depends on speculative files.
- Recovery logic must not silently return empty state for corrupted JSON. That behavior is explicitly incompatible with Silver.

Definition of done:

- All eight remediation items from `dev/active/p0-p1-remediation-plan.md` are either completed here or explicitly handed to P1/P2.
- Touched tests pass locally.

### P0-C. HITL model reduction

- [ ] **P0-C1** Remove inline `hitl_a`, `hitl_b`, `hitl_c` routing from `src/graph.py`. `[M]`
- [ ] **P0-C2** Keep blocking gates only for seed/remodel and exception-based auto-pause:
  - `HITL-S`
  - `HITL-R`
  - `HITL-E`
  `[M]`
- [ ] **P0-C3** Refactor `src/nodes/hitl_gate.py` so it serves seed/remodel approval rather than per-cycle plan/collect/integrate approval. `[M]`
- [ ] **P0-C4** Extend `src/utils/metrics_guard.py` thresholds to Silver v2 exception triggers:
  - `collect_failure_rate`
  - `conflict_rate`
  - `fetch_failure_rate`
  - `cost_regression_flag`
  - `dispute_queue_size`
  `[M]`
- [ ] **P0-C5** Update graph tests to assert zero inline cycle HITL edges outside exception cases. `[M]`

Executable review:

- `src/graph.py` is the correct place to collapse old HITL-A/B/C behavior.
- Do not introduce remodel routing yet in this stage; keep P0 focused on removing obsolete graph structure and keeping tests green.

Phase gate:

- [ ] No critical path still uses `except Exception: pass`.
- [ ] Metrics logger emits `collect_failure_rate`, `timeout_count`, `retry_success_rate`.
- [ ] New/updated tests >= 20 and passing.
- [ ] A baseline trial directory exists under `bench/silver/japan-travel/`.
- [ ] Normal cycle execution does not route through approval gates except explicit exception path.

---

## Phase P1. Entity Resolution and State Safety

Goal: make canonical entity matching, hierarchy handling, and conflict preservation explicit and durable.

### P1-A. Resolver layer

- [ ] **P1-A1** Add `src/utils/entity_resolver.py` with:
  - `resolve_alias(entity_key, skeleton)`
  - `resolve_is_a(entity_key, skeleton)`
  - `canonicalize_entity_key(entity_key, skeleton)`
  `[M]`
- [ ] **P1-A2** Update `src/nodes/integrate.py` matching path to use resolver output instead of exact-match only. `[M]`
- [ ] **P1-A3** Extend domain skeleton validation so `aliases` and `is_a` fields are accepted and validated if present. `[M]`

### P1-B. Conflict durability

- [ ] **P1-B1** Introduce persistent conflict ledger artifact under bench trial state:
  - `state/conflict_ledger.json`
  `[M]`
- [ ] **P1-B2** Ensure disputed KUs remain queryable after auto-resolution attempts, with ledger references preserved. `[M]`
- [ ] **P1-B3** Add migration-safe behavior so absence of ledger file does not break legacy runs. `[S]`

### P1-C. Verification

- [ ] **P1-C1** Add unit tests for alias equivalence and is_a inheritance. `[S]`
- [ ] **P1-C2** Add integration test showing duplicate KU reduction in japan-travel rerun. `[M]`
- [ ] **P1-C3** Add persistence test verifying every dispute writes a ledger entry. `[S]`

Executable review:

- Resolver logic belongs in `src/utils/` because both integrate and future remodel logic will depend on it.
- Ledger must live in bench trial state, not only in-memory `EvolverState`, otherwise audit/dashboard cannot reliably consume it later.

Phase gate:

- [ ] Alias and is_a tests pass.
- [ ] Conflict ledger persists across save/load.
- [ ] Rerun on japan-travel shows duplicate KU count reduced versus P0 baseline.

---

## Phase P2. Outer-Loop Remodel Completion

Goal: turn existing audit findings into actual, reviewable structural change proposals and phase transitions.

### P2-A. Remodel node and schema

- [ ] **P2-A1** Add `src/nodes/remodel.py`. `[L]`
- [ ] **P2-A2** Add `schemas/remodel_report.schema.json`. `[S]`
- [ ] **P2-A3** Define remodel report payload fields:
  - merge proposals
  - split proposals
  - reclassify proposals
  - alias canonicalization proposals
  - source-policy changes
  - gap generation rule changes
  - rollback payload
  `[S]`

### P2-B. Graph/orchestrator integration

- [ ] **P2-B1** Route critical audit results into remodel path in `src/graph.py` or orchestrator-controlled phase boundary flow. `[M]`
- [ ] **P2-B2** Add `HITL-R` approval checkpoint after remodel proposal generation. `[M]`
- [ ] **P2-B3** Persist approved phase state into `state/phase_{N}/...` snapshot structure. `[M]`
- [ ] **P2-B4** Define rollback application path and validate that rejected remodel leaves active state unchanged. `[M]`

### P2-C. Verification

- [ ] **P2-C1** Add tests for merge scenario. `[S]`
- [ ] **P2-C2** Add tests for split scenario. `[S]`
- [ ] **P2-C3** Add tests for reclassify scenario. `[S]`
- [ ] **P2-C4** Add tests for rollback/no-op scenario. `[S]`

Executable review:

- The repository already has audit infrastructure in `src/nodes/audit.py` and policy evolution in orchestrator. Remodel must build on that, not duplicate it.
- Phase transition storage must be implemented here, otherwise later validation cannot prove remodel effects by phase.

Phase gate:

- [ ] Remodel report validates against schema.
- [ ] Approved remodel changes future run behavior.
- [ ] Rollback returns state to pre-remodel form.

---

## Phase P3. Acquisition Expansion

Goal: refactor collection into SEARCH -> FETCH -> PARSE, add provider abstraction, and track source provenance and diversity.

### P3-A. Provider abstraction

- [ ] **P3-A1** Create `src/adapters/providers/__init__.py`. `[S]`
- [ ] **P3-A2** Create `src/adapters/providers/base.py` with `SearchProvider` protocol and `SearchResult` dataclass. `[S]`
- [ ] **P3-A3** Extract current Tavily logic into `src/adapters/providers/tavily_provider.py`. `[M]`
- [ ] **P3-A4** Add `src/adapters/providers/ddg_provider.py` as optional fallback. `[M]`
- [ ] **P3-A5** Add `src/adapters/providers/curated_provider.py` backed by `preferred_sources` in skeleton. `[M]`

### P3-B. Shared fetch pipeline

- [ ] **P3-B1** Add `src/adapters/fetch_pipeline.py` with robots/content-type/max-bytes/timeout checks. `[L]`
- [ ] **P3-B2** Add fetch result structure that records:
  - `fetch_ok`
  - `content_type`
  - `retrieved_at`
  - `bytes_read`
  - `trust_tier`
  - failure reason
  `[M]`
- [ ] **P3-B3** Update `src/config.py` search settings with:
  - `enable_tavily`
  - `enable_ddg_fallback`
  - `fetch_top_n`
  - `max_bytes_per_url`
  - `entropy_floor`
  - `k_per_provider`
  `[S]`

### P3-C. Collect refactor

- [ ] **P3-C1** Refactor `src/nodes/collect.py` into explicit SEARCH -> FETCH -> PARSE steps without changing external node contract. `[L]`
- [ ] **P3-C2** Add provenance fields to claim evidence/state flow:
  - `providers_used`
  - `domain`
  - `fetch_ok`
  - `fetch_depth`
  - `content_type`
  - `retrieved_at`
  - `trust_tier`
  `[M]`
- [ ] **P3-C3** Add per-cycle diversity metrics:
  - `domain_entropy`
  - `provider_entropy`
  `[M]`
- [ ] **P3-C4** Add per-cycle cost guards:
  - `cycle_llm_token_budget`
  - `cycle_fetch_bytes_budget`
  `[M]`

### P3-D. Dependency and test work

- [ ] **P3-D1** Update `pyproject.toml` with any new provider/dashboard-adjacent dependencies actually used. `[S]`
- [ ] **P3-D2** Add provider tests with fallback behavior and entropy-triggered DDG enablement. `[M]`
- [ ] **P3-D3** Add fetch pipeline tests for robots refusal, content-type refusal, timeout, and truncation. `[M]`
- [ ] **P3-D4** Add collect integration tests covering mixed provider results and provenance output. `[M]`

Executable review:

- Current repo has only `src/adapters/search_adapter.py`; provider split is a real structural change and must be completed before provenance and diversity metrics can be trusted.
- `CuratedSourceProvider` must remain SEARCH-only. Fetch behavior belongs exclusively in `FetchPipeline`.

Phase gate:

- [ ] Fetch success rate >= target on japan-travel seed queries.
- [ ] Diversity metrics are emitted per cycle.
- [ ] Collection output contains provenance fields end-to-end.
- [ ] Budget guards can degrade behavior without crashing the cycle.

---

## Phase P4. Coverage Intelligence

Goal: make target selection and critique prescriptions traceable to novelty, overlap, and deficit metrics.

### P4-A. Metrics primitives

- [ ] **P4-A1** Add `src/utils/novelty.py` for cycle-to-cycle novelty and overlap computation. `[M]`
- [ ] **P4-A2** Add coverage map structure over category/geography/field/entity hierarchy. `[M]`
- [ ] **P4-A3** Extend state/metrics types if needed so novelty, overlap, and deficits have stable typed homes. `[S]`

### P4-B. Plan and critique integration

- [ ] **P4-B1** Update `src/nodes/plan.py` so each selected target carries a reason code. `[M]`
- [ ] **P4-B2** Update `src/nodes/critique.py` so prescriptions reference measured deficit/plateau/merge-pending causes. `[M]`
- [ ] **P4-B3** Integrate plateau detector with novelty-based trigger logic rather than only growth-rate heuristics. `[M]`
- [ ] **P4-B4** Ensure remodel pending state can influence planning reason codes. `[S]`

### P4-C. Verification

- [ ] **P4-C1** Add tests for novelty score calculation. `[S]`
- [ ] **P4-C2** Add tests for reason-code generation in plan output. `[S]`
- [ ] **P4-C3** Add repeated-seed plateau scenario that triggers audit/remodel path. `[M]`

Executable review:

- This phase must wait for P3 provenance because source overlap and diversity are now part of coverage logic.
- Do not bury reason codes inside free-text critique; they need machine-readable values for P5 and P6 evaluation.

Phase gate:

- [ ] Every target in plan output has a reason code.
- [ ] Plateau scenario is machine-detected.
- [ ] Novelty and overlap are available to telemetry emitters.

---

## Phase P5. Telemetry Contract and Dashboard

Goal: formalize telemetry first, then deliver a minimal operator dashboard that can inspect Silver without reading raw JSON.

### P5-A. Telemetry contract

- [ ] **P5-A1** Add `schemas/telemetry.v1.schema.json`. `[S]`
- [ ] **P5-A2** Add `src/obs/telemetry.py`. `[M]`
- [ ] **P5-A3** Add telemetry emit hook points in orchestrator/node boundary flow. `[M]`
- [ ] **P5-A4** Write telemetry to `state/telemetry/*.jsonl` within each trial root. `[S]`
- [ ] **P5-A5** Include at minimum:
  - `trial_id`
  - `phase`
  - `cycle`
  - `mode`
  - `metrics`
  - `gaps`
  - `failures`
  - `providers_used`
  - `audit_summary`
  - `hitl_queue`
  - `dispute_queue`
  `[S]`

### P5-B. Dashboard implementation

- [ ] **P5-B1** Add dashboard package under `src/obs/` with minimal web entrypoint. `[M]`
- [ ] **P5-B2** Use `FastAPI + htmx + Chart.js` as the default implementation target from v2. `[M]`
- [ ] **P5-B3** Update `pyproject.toml` with dashboard dependencies only when telemetry schema and backend route design are fixed. `[S]`
- [ ] **P5-B4** Implement views:
  - overview
  - cycle timeline
  - gap coverage map
  - source reliability
  - conflict ledger
  - HITL inbox
  - remodel review
  `[L]`
- [ ] **P5-B5** Add `docs/operator-guide.md`. `[M]`

### P5-C. Verification

- [ ] **P5-C1** Add schema validation tests for emitted telemetry. `[S]`
- [ ] **P5-C2** Add dashboard data-contract tests using fixture telemetry. `[M]`
- [ ] **P5-C3** Add one operator self-test scenario: diagnose slowdown from dashboard-only evidence within 3 minutes. `[M]`

Executable review:

- The repo currently has no dashboard stack, so this phase must include dependency management and a new runtime entrypoint.
- Keep dashboard backend and templates under `src/obs/`; do not spread UI files across unrelated modules.
- UI implementation must stay below the LOC budget in the masterplan. If complexity grows, cut scope before adding features.

Phase gate:

- [ ] Telemetry schema validates emitted data.
- [ ] Dashboard loads representative 100-cycle fixture data within target time.
- [ ] HITL/dispute/remodel views consume real telemetry/ledger artifacts, not stub-only data.

---

## Phase P6. Multi-Domain Validation

Goal: prove Silver is framework-level, not japan-travel-specific.

### P6-A. Domain selection and setup

- [ ] **P6-A1** Select one second domain using the v2 structural-difference rule:
  at least two of time horizon, hierarchy depth, or source language differ from japan-travel. `[S]`
- [ ] **P6-A2** Create second-domain skeleton, seed pack, and trial directory under `bench/silver/{domain}/`. `[M]`
- [ ] **P6-A3** Record domain-selection rationale in the trial card before implementation run. `[S]`

### P6-B. Smoke validation

- [ ] **P6-B1** Run minimum 10-cycle smoke under isolated Silver bench root. `[L]`
- [ ] **P6-B2** Produce readiness report against Silver gates. `[M]`
- [ ] **P6-B3** Produce framework-vs-domain delta memo:
  - framework changes required
  - domain-only configuration changes
  `[M]`

Executable review:

- This phase must consume finished P1-P5 artifacts. Running it earlier only produces noisy domain-specific breakage.
- Framework-level code changes discovered here should be small and explicitly counted. Large rewrites mean earlier phases were under-specified.

Phase gate:

- [ ] Second domain passes target smoke thresholds.
- [ ] Framework-level code changes required by second domain are within agreed cap.
- [ ] Final Silver readiness review references both domains.

---

## 5. Cross-phase control tasks

- [ ] **X1** After each phase, append row to `bench/silver/INDEX.md`. `[S]`
- [ ] **X2** Keep `dev/active/p0-p1-remediation-plan.md` marked as deprecated once P0/P1 tasks are migrated into active Silver execution docs. `[S]`
- [ ] **X3** For every new schema or contract, add at least one positive and one negative validation test. `[S]`
- [ ] **X4** For every new directory introduced in Silver, add a minimal `__init__.py` when Python package import is expected. `[S]`
- [ ] **X5** Any new operator-facing doc must point back to the canonical trial/readiness artifacts, not duplicate gate definitions. `[S]`

---

## 6. Recommended execution order inside the repo

1. P0-A through P0-C
2. P1-A through P1-C
3. P2-A through P2-C
4. P3-A through P3-D
5. P4-A through P4-C
6. P5-A before any P5-B work
7. P5-B through P5-C
8. P6-A through P6-B

Reasoning:

- P0 removes current architectural friction and creates isolated Silver artifacts.
- P1 and P2 establish structural correctness before broadening data acquisition.
- P3 changes the shape of evidence and provenance, which P4 and P5 depend on.
- P5 without P5-A first would recreate the v1 problem of a UI with no stable contract.
- P6 must be last because it validates the whole system, not one subsystem.

---

## 7. Silver completion checklist

- [ ] P0 gate passed and baseline trial created
- [ ] P1 gate passed and conflict ledger persistent
- [ ] P2 gate passed and remodel path executable
- [ ] P3 gate passed and provider/fetch/provenance path stable
- [ ] P4 gate passed and reason-coded planning active
- [ ] P5 gate passed and telemetry/dashboard/operator flow usable
- [ ] P6 gate passed on second domain
- [ ] Final Silver readiness report approved

---

## 8. Immediate next actions

- [ ] Create `dev/active/phase-si-p0-foundation/` and migrate P0 tasks into an active execution doc set. `[S]`
- [ ] Scaffold `bench/silver/` and templates before touching runtime logic. `[S]`
- [ ] Implement P0 remediation items in the order: retry bug -> collect logging -> timeout wiring -> integrate logging -> state I/O recovery -> collect/state tests -> HITL reduction. `[M]`
- [ ] Do not begin dashboard coding before `schemas/telemetry.v1.schema.json` and emit path are merged. `[S]`

