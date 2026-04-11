# Domain-K-Evolver Gen-Silver Masterplan

> Status: Draft for implementation
> Date: 2026-04-11
> Based on: `docs/silver-masterplan-sketch.md`, `dev/active/p0-p1-remediation-plan.md`, `docs/design-v2.md`

## 1. Purpose

Silver is the generation that turns the current Bronze knowledge-evolution loop into a reliable, observable, extensible system.

Bronze established the core loop:

- seed
- mode
- plan
- collect
- integrate
- critique
- plan_modify
- HITL gates

Silver must make that loop production-grade in four ways:

1. Broader and richer knowledge acquisition.
2. Higher integrity and lower silent failure rates.
3. Stronger self-improvement through periodic global audit/remodeling.
4. Full observability through monitoring, dashboards, and operator guidance.

This document is the single overall implementation plan for the Silver project.

## 2. Silver Definition

### 2.1 Mission

Silver is complete when the system can:

- collect knowledge from search plus fetched page content, not search snippets only
- track non-overlap and coverage progression across cycles
- detect stagnation and trigger global audit/remodel decisions
- expose cycle, phase, quality, and bottleneck state through a dashboard
- run with explicit failure handling, timeout control, and recovery paths
- preserve knowledge integrity under aliasing, conflicts, stale refresh, and schema errors

### 2.2 Non-Goals

Silver does not yet aim to:

- optimize for business packaging or monetization
- support large-scale multi-tenant deployment
- replace HITL with full autonomy
- solve every domain-specific ontology problem

Those belong to Gold or later operational phases.

## 3. Current State Summary

### 3.1 What already exists

- LangGraph-based core loop in `src/graph.py`
- node implementations for seed/plan/collect/integrate/critique/plan_modify/mode/HITL/audit
- JSON state model and schema-based storage
- metrics, readiness gates, policy manager, and invariant checks
- tests for most nodes and utilities

### 3.2 Current weaknesses

From the Silver sketch and the remediation plan, the main gaps are:

- collection still depends too heavily on Tavily-style search results and shallow fetch handling
- collect/integrate/state I/O contain silent-failure paths
- request timeout and retry behavior are not robust enough
- alias/is_a entity resolution exists in design but is only partially implemented in code
- global remodel logic is specified conceptually but not implemented as a real outer-loop path
- monitoring exists mostly as logs/tests, not as an operator-facing dashboard
- coverage progression and cycle-to-cycle novelty are not explicit enough for steering search

### 3.3 Silver entry assumption

Bronze remediation is a prerequisite, not optional follow-up.

The P0/P1 items in `dev/active/p0-p1-remediation-plan.md` become the Silver Phase 0 baseline gate:

- P0-1 collect exception/logging hardening
- P0-2 request timeout hardening
- P0-3 retry classification bug fix
- P0-4 remodel node implementation
- P1-1 conflict evidence preservation
- P1-2 alias/is_a support
- P1-3 collect test expansion
- P1-4 state I/O validation and recovery

## 4. Product Principles

- Domain knowledge quality is determined by structure, evidence, and operator judgment, not LLM fluency.
- Silent failure is worse than explicit failure.
- Every critique prescription must compile into a plan change, policy change, or remodel action.
- Coverage expansion must be measurable, not assumed.
- High-risk claims require stricter evidence handling and visible review paths.
- Silver must remain domain-agnostic at the framework level.

## 5. Target Architecture

## 5.1 Inner Loop

The inner loop remains:

`seed -> mode -> plan -> HITL-A -> collect -> HITL-B -> integrate -> HITL-C -> critique -> plan_modify -> next cycle`

Silver strengthens this loop by adding:

- richer collection sources
- better timeout/retry/error accounting
- novelty and non-overlap accounting
- explicit coverage steering inputs
- stronger entity resolution
- safer state recovery

## 5.2 Outer Loop

Silver formalizes an outer loop on top of the inner loop:

- every N cycles, run a global audit of accumulated knowledge, gaps, policies, and metrics
- identify structural issues that the local cycle loop cannot fix
- produce remodel actions for entity hierarchy, category design, source strategy, policy thresholds, and gap-generation rules
- start a new phase after major remodels, preserving history

Recommended initial cadence:

- mini audit every 5 cycles
- full remodel audit every 10 cycles

## 5.3 Observability Layer

Silver adds an operator-facing observability layer containing:

- run status and current cycle/phase
- mode decision and jump triggers
- open/resolved/new gap counts
- evidence rate, multi-evidence rate, conflict rate, confidence, staleness risk, coverage
- collect failures, timeout counts, retry counts, parse failures, state recovery events
- gap distribution by category, geography, and other axes
- non-overlap and novelty trend across recent cycles
- pending HITL actions and unresolved disputes

## 6. Workstreams

Silver should be executed through six workstreams.

### WS1. Foundation Hardening

Goal: eliminate silent failure and make the Bronze base safe to build on.

Scope:

- implement all P0/P1 remediation items
- tighten logging, metrics, and error surfacing
- add timeout parameters for LLM and search
- add backup/recovery behavior for state loading
- close integrity holes in collect/integrate

Primary modules:

- `src/nodes/collect.py`
- `src/nodes/integrate.py`
- `src/utils/state_io.py`
- `src/adapters/search_adapter.py`
- `src/adapters/llm_adapter.py`
- `src/config.py`
- `src/graph.py`
- related tests

Exit criteria:

- no bare error-swallowing on critical paths
- timeout behavior is configurable and tested
- failure metrics are emitted
- remediation test scenarios are implemented and passing

### WS2. Knowledge Acquisition Expansion

Goal: improve information richness and collection breadth.

Scope:

- upgrade collect flow from search-snippet-first to search-plus-fetch-first
- support multiple retrieval strategies under one adapter interface
- evaluate additional search providers such as DuckDuckGo as optional/fallback backends
- normalize fetched page content for extraction quality
- track source diversity and duplicate-source suppression

Design additions:

- source provenance model: provider, domain, fetch success, fetch depth, content type
- per-cycle source diversity report
- source trust heuristics configurable in policy

Exit criteria:

- fetched content is routinely used in claim extraction
- source diversity metrics are visible
- collection plans can specify provider strategy and fetch depth

### WS3. Knowledge Integrity and Resolution

Goal: make integrated knowledge structurally safer and more reusable.

Scope:

- implement alias and is_a resolution as first-class integration behavior
- improve conflict preservation and adjudication traceability
- support stale refresh rules consistently
- validate required fields and schema recovery behavior
- ensure evidence-first invariant remains machine-checkable

Design additions:

- canonical entity resolver utility
- entity hierarchy validation
- conflict ledger for disputed KUs
- recovery/audit log for state repair operations

Exit criteria:

- alias/is_a resolution is active in integration
- disputed knowledge remains queryable and auditable
- malformed state cannot silently degrade into empty knowledge

### WS4. Coverage Steering and Non-Overlap Intelligence

Goal: let each cycle deliberately expand useful knowledge rather than drifting.

Scope:

- compute cycle-to-cycle novelty and overlap
- measure coverage by source, category, field, geography, and entity hierarchy
- feed deficits back into plan selection
- distinguish explore vs exploit outcomes, not only budgets
- strengthen plateau and stagnation detection

Design additions:

- novelty score per cycle
- overlap matrix across recent cycles
- deficit backlog grouped by axis
- reason codes for target selection

Exit criteria:

- each plan can explain why each target gap was selected
- recent-cycle novelty is measurable
- critique can prescribe concrete coverage corrections backed by metrics

### WS5. Outer-Loop Audit and Remodeling

Goal: escape local optima and evolve the domain model itself.

Scope:

- implement `remodel_node`
- add graph routing into remodel/audit path
- define remodel outputs and persistence model
- support phase transition after approved remodels
- add tests for merge/split/reclassify recommendations

Remodel outputs should include:

- entity merge proposals
- entity split proposals
- alias canonicalization updates
- category or field restructuring proposals
- source-policy changes
- gap-generation rule changes
- audit summary and rationale

Exit criteria:

- outer-loop remodel executes on schedule or trigger
- remodel outputs are reviewable and traceable
- approved remodels can update skeleton/policy without manual ad hoc edits

### WS6. Dashboard and Operator Experience

Goal: make Silver understandable and steerable by a human operator.

Scope:

- create a web dashboard for cycle, phase, quality, and bottleneck monitoring
- surface HITL queue and decision context
- expose drill-down views for GU/KU/conflict/source/failure analysis
- present actionable guidance, not raw counters only

Recommended dashboard views:

- overview
- cycle timeline
- gap coverage map
- source reliability panel
- conflict/dispute queue
- HITL approval inbox
- remodel audit report

Exit criteria:

- operator can identify why progress slowed
- operator can see what the system did this cycle
- operator can find which decisions need manual intervention

## 7. Delivery Phases

## Phase 0. Bronze Baseline Gate

Objective:

- finish P0/P1 remediation and re-establish a trustworthy baseline

Deliverables:

- code fixes for all remediation items
- expanded node and utility tests
- updated readiness gate definition for Silver entry

Gate:

- all remediation items merged
- test suite green for touched scope
- no critical silent-failure paths remaining in audited modules

## Phase 1. Silver Core Reliability

Objective:

- harden runtime behavior and observability plumbing

Deliverables:

- timeout/retry/failure metrics
- structured logging model
- state recovery and integrity reporting
- baseline dashboard data pipeline

Gate:

- runtime failures are visible and classifiable
- key health metrics available from one place

## Phase 2. Acquisition Expansion

Objective:

- improve evidence richness and source diversity

Deliverables:

- fetch-enriched collect pipeline
- optional provider abstraction/fallback
- source provenance fields and metrics

Gate:

- claim extraction quality improves on fetch-backed scenarios
- source diversity can be reported by cycle

## Phase 3. Coverage Intelligence

Objective:

- make planning responsive to novelty, overlap, and deficits

Deliverables:

- novelty/overlap metrics
- deficit-aware plan steering
- stronger plateau detection and plan rationale

Gate:

- plan target selection is explainable from metrics
- repeated low-value cycling is detectably reduced

## Phase 4. Outer-Loop Remodeling

Objective:

- introduce scheduled structural self-improvement

Deliverables:

- remodel node and graph path
- remodel artifact schema
- phase transition rules

Gate:

- at least one end-to-end remodel scenario is tested
- approved remodel can modify future cycle behavior predictably

## Phase 5. Operator Productization

Objective:

- deliver usable dashboard and human governance workflow

Deliverables:

- dashboard UI
- HITL workflow views
- audit/remodel review views
- operator guide

Gate:

- operator can monitor, diagnose, and intervene without reading raw JSON files

## 8. Deliverables by Artifact

### Code

- hardened adapters, nodes, utilities, and graph routing
- new `src/nodes/remodel.py`
- new entity resolution utility module
- observability and dashboard-serving modules as needed

### Data/Schema

- remodel report schema
- source provenance schema additions
- optional cycle telemetry snapshot schema
- dashboard-ready aggregate payload format

### Tests

- regression tests for all remediation items
- timeout/retry/fetch failure scenarios
- alias/is_a integration tests
- remodel recommendation tests
- dashboard data-contract tests

### Docs

- updated architecture doc
- operator dashboard guide
- remodel process guide
- Silver readiness checklist

## 9. Acceptance Criteria

Silver is considered complete when all of the following are true:

- Bronze remediation items are fully implemented and verified.
- Collect no longer loses critical failures silently.
- Runtime timeouts and retries are configurable, measurable, and tested.
- Alias/is_a entity resolution works in production flow.
- Coverage, novelty, and overlap metrics steer planning.
- Outer-loop audit/remodel runs through a real graph path.
- Dashboard exposes cycle, phase, metrics, failures, HITL, and remodel state.
- A human operator can inspect system health and intervene efficiently.
- At least one secondary domain beyond the current validation domain passes a Silver smoke run.

## 10. Validation Strategy

### 10.1 Test Pyramid

- unit tests for adapters, resolvers, metrics, and state recovery
- node tests for collect/integrate/critique/remodel
- graph tests for routing, scheduled audit, and phase transitions
- smoke tests with realistic provider mocks
- selective real-run tests for fetch/search behavior

### 10.2 Scenario Set

Required scenarios:

- search timeout and fetch timeout
- malformed LLM JSON
- missing or corrupt state file with recovery path
- duplicate entities through alias
- hierarchical inheritance through is_a
- conflicting claims preserved as dispute
- repeated low-novelty cycles triggering audit/remodel
- dashboard telemetry from one full cycle

### 10.3 Domain Validation

Silver should be validated on:

- current reference domain
- one structurally different domain, such as real estate or tech stack knowledge

The purpose is to ensure the framework stays domain-agnostic.

## 11. Metrics and Gates

Silver should continue the existing health metrics and add these project-level gates.

### Reliability

- collect failure rate
- fetch failure rate
- timeout rate by adapter
- retry success rate
- state recovery event count

### Knowledge Quality

- evidence rate
- multi-evidence rate
- conflict rate
- average confidence
- staleness risk

### Coverage Intelligence

- coverage by axis
- novelty score
- overlap score with recent cycles
- source diversity score
- unresolved deficit count

### Governance

- HITL pending count
- dispute aging
- remodel recommendation count
- remodel approval throughput

## 12. Risks and Mitigations

- Search/fetch complexity increases runtime cost.
  Mitigation: explicit budgets, provider policies, fetch-depth caps, telemetry.

- Better source expansion may increase noise.
  Mitigation: provenance scoring, duplicate suppression, stronger evidence policy.

- Remodel logic can destabilize state shape.
  Mitigation: phase boundaries, preview artifacts, approval gate before applying structural changes.

- Dashboard work can sprawl into a separate product.
  Mitigation: ship telemetry contracts first, UI second, keep Silver dashboard operational rather than decorative.

- Domain-specific edge cases may overfit the framework.
  Mitigation: validate on a second domain before Silver completion.

## 13. Recommended Execution Order

1. Complete Phase 0 remediation baseline.
2. Finish reliability and telemetry plumbing needed by later work.
3. Expand acquisition and provenance tracking.
4. Implement coverage intelligence and planning feedback.
5. Implement remodel node and outer-loop routing.
6. Build the dashboard on top of stabilized telemetry contracts.
7. Run secondary-domain validation and final Silver gate review.

## 14. Immediate Next Actions

- Create a Silver tracking checklist derived from WS1-WS6.
- Treat `dev/active/p0-p1-remediation-plan.md` as the execution backlog for Phase 0.
- Define the telemetry contract before dashboard UI work begins.
- Implement `remodel_node` early enough that outer-loop requirements do not remain theoretical.
- Add a dedicated Silver readiness report template for final gate review.

## 15. Completion Checklist

- [ ] Bronze remediation baseline complete
- [ ] Reliability metrics emitted
- [ ] Timeout/retry controls implemented
- [ ] Source expansion implemented
- [ ] Alias/is_a resolution implemented
- [ ] Coverage/non-overlap steering implemented
- [ ] Remodel outer loop implemented
- [ ] Dashboard operational
- [ ] Secondary-domain validation passed
- [ ] Silver readiness review approved
