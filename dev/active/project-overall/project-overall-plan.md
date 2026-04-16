# Project Overall Plan
> Last Updated: 2026-04-16
> Status: Bronze 완료 → Silver P0/P1/P3R/P2/Gap-Res 완료 → **SI-P4 Stage E VP4 FAIL 진단 (D-147~D-150)** → VP4 fix + 재실행 대기

## 0. Refactor Pivot (2026-04-14)

**D-121**: Silver P3 (Provider/Fetch/Parse 3단계) 전면 폐기 → **SI-P3R** (snippet-first 2단계) 로 대체.
- 근거: D-120 `_parse_claims_llm` 0 claims, 단일 GU 진단에서 snippet-only 경로로 4 claims 성공
- 범위: `fetch_pipeline`, `html_strip`, `providers/{base,ddg,curated}` 제거. Tavily 직접 호출 + snippet → LLM 파싱
- dev-docs: `dev/active/phase-si-p3r-snippet-refactor/`

### Refactor 이후 Phase 실행 순서

```
SI-P3R 완료 (2026-04-14, D-125)
   │
   ▼  [현재] Gap-Resolution Investigation (D-126)
   │      - Stage A: 진단 로깅 + 정적 분석
   │      - Stage B: target_count cap 제거 (Primary fix)
   │      - Stage C: 재현 trial + 효과 검증
   │      - Stage D: Secondary 대응 결정 (D-129~D-131)
   │
   ▼  Silver P2 재판정 (remodel on/off 비교 실험, D-127) ✅ Gate PASS (D-132/133)
   │
   ▼  Silver P4 (Coverage Intelligence) ← 현재
   │      - Stage A~D: Internal Foundation (완료, 17/17, 669 tests)
   │      - Stage E: External Anchor (23/25, 793 tests) — E7-2 실 벤치 VP4 FAIL 진단
   │                  VP4 FAIL 근본 원인 4건 (D-147~D-150): budget/산식/조건/HITL
   │                  → VP4 fix + 재실행 후 Gate 판정 예정
   │
   ▼  Silver P5 (Telemetry & Dashboard)
   │
   ▼  Silver P6 (Multi-Domain Validation, Silver exit gate)
```

- **P2 재판정 조건**: P3R 실 벤치 trial 성공 + P2 remodel 코드 실 bench 재실행(before/after metrics)
- **P4 선결 조건**: P3R provenance 축소 필드 확정(`provider`/`domain`/`retrieved_at`/`trust_tier`) → novelty/coverage 계산 의존성 해소
- **Phase 6 재설계 메모**: `preferred_sources`(curated) 제거 → 도메인 확장 방식은 Tavily 쿼리 hint로 대체. multi-domain 착수 전 snippet-only 품질이 2차 도메인에서도 유지되는지 smoke로 검증

## 1. Summary (개요)

Domain-K-Evolver — 도메인 불문 자기확장 지식 Evolver 프레임워크.
부분적으로 알려진 지식에서 시작해 Gap-driven 계획 → 수집 → 통합 → 비평 → 계획수정 루프를 반복하며 지식을 자동 확장.

**목표 (Bronze → Silver)**: draft.md의 설계를 LangGraph 기반 자동화 파이프라인으로 구현하여(Bronze 완료) → 운영 가능 형태로 굳히고(Silver) → 2차 도메인에서 무관성 실증.

**범위**: Cycle 0/1 수동 검증 → GU 전략 재검토 → LangGraph 자동화 → Cycle 품질 리모델링 → Self-Governing (audit/policy/gate) → Inner Loop 품질 → **Silver: Foundation Hardening → Entity Resolution → Remodel → Acquisition Expansion → Coverage Intelligence → Telemetry/Dashboard → Multi-Domain Validation**.

---

## 2. Current State (현재 상태)

### Bronze 세대 완료 (Phase 0 ~ Phase 5)
- **Phase 0 / 0B / 0C**: Cycle 0·1 수동 검증 + GU 전략(v1.0) 확정, Axis Coverage Matrix + Jump Mode 실측 성공
- **Phase 1**: LangGraph Core Pipeline — StateGraph 14노드, 191 tests
- **Phase 2**: Bench Integration & Real Self-Evolution — OpenAI gpt-4.1-mini + Tavily, 10 Cycle 자동, 272 tests
- **Phase 3**: Cycle Quality Remodeling — Active 31→77, Disputed 54→0, conflict_rate 0.635→0.000, 301 tests
- **Phase 4**: Self-Governing Evolver — audit/policy/credibility/readiness-gate, 420 tests, **Gate FAIL** (VP1/VP2)
- **Phase 5**: Inner Loop Quality — axis_tags 전파, staleness refresh, adaptive cap, multi-evidence boost, **Gate #5 PASS** (VP1 5/5, VP2 6/6, VP3 5/6), **468 tests**, commit `b122a23`

### Silver P0 완료 (2026-04-12)
- **Silver P0 Gate PASS**: VP1 5/5, VP2 5/6, VP3 5/6 — 510 tests, commit `30946ac`
- **P0 성과**: bare-except 0, collect_failure_rate/timeout_count/retry_success_rate emit, HITL-A/B/C 제거, S1/S2/S3 pass
- **인터페이스 고정 완료**: integrate/collect I/O shape + provenance + EvolverState 5필드 + metrics keys → P1/P3 병렬 착수 가능
- **baseline trial**: `bench/silver/japan-travel/p0-20260412-baseline/` — 15 cycle, KU 42→127, gap_resolution 0.931
### Silver P1 완료 (2026-04-12)
- **Silver P1 Gate PASS**: S4/S5/S6 pass — 544 tests, commit `3bbde92`
- **P1 성과**: entity_resolver.py 신규, alias/is_a/canonicalize 해상도 계층, conflict_ledger 영속화, skeleton aliases/is_a 검증
- **비고**: dedicated bench trial 미실행 — 단위/통합 테스트 + scenario로 gate 판정
- **다음**: P2 (Outer-Loop Remodel 완결) 착수 — dev-docs 생성 완료

### Silver P3 REVOKED (2026-04-13) → SI-P3R 완료 (2026-04-14)
- **Gate 무효화 사유 (D-120)**: `_parse_claims_llm` 실 벤치에서 0 claims — curated 홈페이지 URL + raw HTML 노이즈. 기존 22 tasks는 deterministic fallback만 검증됨
- **Historical 증거 보존**: `bench/silver/japan-travel/p3-20260412-acquisition/`, `p3-20260413-llm-diag/`, `p3-20260413-llm-verify/` — 삭제 금지 (commit `15ce9d5`)
- **SI-P3R 완료**: 8/8 tasks, T8 Gate PASS (D-125, commit `981ffd6`) — 15c trial: VP1 5/5, VP2 4/6, VP3 6/6
- **gap_resolution 분리 조사**: P3R Gate는 acquisition 검증 기준 PASS. gap_res 0.517@15c 병목은 별도 Phase 착수 (D-126)

### Gap-Resolution Investigation Phase (착수, 2026-04-14)
- **계기 (D-126)**: SI-P3R 15c trial gap_resolution 0.517 — Bronze P5 0.909 대비 -42% 격차
- **확정 근본 원인 (Primary, B1)**: `b12545d` commit에서 target_count cap (=10)이 regression으로 재도입 → Phase 5에서 제거했던 공식이 무효화됨
- **Secondary 병목 (B2)**: target 10개 중 resolve 3-7개 = 52% conversion rate. LLM parse 수율 추정 원인
- **dev-docs**: `dev/active/phase-gap-resolution-investigation/`
- **Silver P2 재판정**: 본 Phase 종결 + Primary fix 효과 확인 후 착수 (D-131 예정)

### 자산 (현 commit 기준)
```
schemas/          — KU/EU/GU/PU/policy 5종 (remodel_report / telemetry.v1 추가 예정: Silver)
templates/        — 6대 Deliverable MD 템플릿 (Silver: si-trial-card / si-readiness-report / si-index-row 추가 예정)
bench/japan-travel/            — Bronze 수동 실행 원본 (read-only)
bench/japan-travel-auto/       — Phase 3 최종 10 Cycle 자동 실행
bench/japan-travel-readiness/  — Phase 4·5 Gate 벤치마크
(Silver: bench/silver/{domain}/{trial_id}/ 로 이전 예정)
src/nodes/        — seed, mode, plan, collect, integrate, critique, plan_modify, hitl_gate, audit, dispute_resolver
                     (Silver: remodel 신규)
src/adapters/     — llm_adapter.py, search_adapter.py
                     (Silver: providers/{base,tavily,ddg,curated}_provider.py + fetch_pipeline.py)
src/utils/        — state_io, schema_validator, metrics, invariant_checker, policy_manager, readiness_gate,
                     plateau_detector, metrics_logger, llm_parse
                     (Silver: entity_resolver, novelty, coverage_map 신규)
src/obs/          — 부재 (Silver P5 에서 telemetry + dashboard 신규)
```

---

## 3. Target State (목표 상태)

### Bronze (달성)
- LangGraph 기반 자동 Inner Loop 동작 (Seed → Plan → Collect → Integrate → Critique → PM) ✅
- HITL Gate 작동 (A~E) ✅
- japan-travel 벤치에서 Cycle 1+ 자동 실행 성공 ✅
- 5대 불변원칙 자동 검증 통과 ✅
- Outer Loop 자동 Audit + Policy 자동 재설계 ✅ (Phase 4)
- Inner Loop 품질 보완 ✅ (Phase 5)
- Evolver Readiness Gate 3/3 PASS ✅ (Phase 5 Gate #5)

### Silver (목표)
- **Foundation Hardening** — bare-except 0, timeout/retry/복구 정상화, collect_failure_rate 등 reliability 메트릭 emit
- **Entity Resolution** — alias/is_a 해상도, conflict ledger 영구 보존
- **Outer-Loop Remodel 완결** — audit 결과를 구조 변경 제안으로 compile, HITL-R 승인 게이트 + phase transition 저장
- **Acquisition Expansion** — SEARCH/FETCH/PARSE 3단계 분리, provider 플러그인, provenance + 소스 다양성 메트릭, 비용 예산 가드
- **Coverage Intelligence** — novelty/overlap/deficit 근거 기반 plan 선택, reason_code 100%
- **Telemetry & Dashboard** — telemetry.v1 계약 + 단일 운영자용 FastAPI+htmx 대시보드 (LOC ≤ 2,000)
- **Multi-Domain Validation** — 2차 도메인에서 10 cycle smoke, Gate #5 동등 기준 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6), framework 수정 ≤ 5건
- **HITL 축소** — 매 cycle HITL-A/B/C 제거, HITL-S/R/D/E 4세트 체제
- **S1~S11 시나리오 blocking test** 전부 pass
- **Silver readiness review (Gate #6)** 승인

---

## 4. Phase 구성

### Bronze 세대 Phases (완료)

#### Phase 0: Cycle 0 수동 검증 ✅
- design-v2.md 도출 완료

#### Phase 0B: Cycle 1 수동 검증 ✅
- Conflict-preserving 실전 검증 성공 (disputed 2건, condition_split + hold)

#### Phase 0C: GU 전략 재검토 ✅
- Axis Coverage Matrix + Jump Mode 실측, expansion-policy v1.0 확정

#### Phase 1: LangGraph Core Pipeline ✅
- 191 tests, 8노드 + 5 HITL Gate + cycle_inc = 14 노드 StateGraph

#### Phase 2: Bench Integration & Real Self-Evolution ✅
- 272 tests, 10 Cycle 자동 실행, D-29~D-39

#### Phase 3: Cycle Quality Remodeling ✅
- 301 tests, Active +148%, conflict_rate → 0, D-40~D-43

#### Phase 4: Self-Governing Evolver ✅ (Gate FAIL → Phase 5 삽입)
- 420 tests, Stage A~D (Audit / Policy / Self-Tuning / Readiness Gate)
- D-44~D-52
- **Gate FAIL**: VP1 3/5, VP2 2/6, VP3 6/6 → Phase 5 보완 삽입

#### Phase 5: Inner Loop Quality ✅
- **완료**: 2026-03-09 | 468 tests passed, 23/23 tasks, commit `b122a23`
- Stage A~D: axis_tags 전파, staleness 자동갱신, category 균형, GU resolve rate
- Stage E: staleness 메커니즘 개선 (D-62~D-66) — observed_at today, confidence 가중, adaptive cap, T7 trigger, closed_loop 세분화
- Stage E-2: VP2 잔여 FAIL 해결 (D-67~D-70) — 신규/업데이트 observed_at, evidence-count 가중, multi-evidence boost
- **Gate #5 PASS**: VP1 5/5, VP2 6/6, VP3 5/6
- avg_confidence 0.755→0.822, staleness 93→0, gap_resolution 0.780→0.909

---

### Silver 세대 Phases (단일 진실 소스: `docs/silver-masterplan-v2.md` §4)

#### Silver P0. Foundation Hardening ✅
- **완료**: 2026-04-12 | 32/32 tasks | **510 tests** | Gate PASS
- **결과**: VP1 5/5, VP2 5/6 (R3_multi_evidence non-critical FAIL), VP3 5/6 (R6_closed_loop non-critical FAIL)
- **성과**: bare-except 0, reliability 메트릭 3종 emit, HITL-S/R/E 체제, 인터페이스 6건 고정, baseline trial PASS
- **dev-docs**: `dev/active/phase-si-p0-foundation/`
- **커밋 체인**: `2f9117a` → `e73b136` → `83ce974` → `f21a249` → `6c7f28f` → `f67cbf3`~`cdf0a96` → `30946ac`

#### Silver P1. Entity Resolution & State Safety ✅
- **Goal**: 구조적 무결성 — alias / is_a / conflict ledger
- **Status**: **Complete** (12/12, 544 tests, S4/S5/S6 pass) | Commit `3bbde92`
- **Scope**:
  - `src/utils/entity_resolver.py` [NEW] — resolve_alias / resolve_is_a / canonicalize_entity_key
  - `integrate.py._find_matching_ku` resolver 연동
  - `state/conflict_ledger.json` 영구 보존 (append-only, 삭제 금지)
  - skeleton `aliases` / `is_a` validator (backward compat)
  - japan-travel skeleton alias/is_a 예시 추가
- **Stages**: A (해상도 계층, 4 tasks) → B (Conflict ledger, 4 tasks) → C (검증, 4 tasks)
- **Gate (정량)**:
  - 동의어 (JR-Pass / 재팬레일패스), is_a (shinkansen is_a train) 각 pass
  - japan-travel 재실행: 중복 KU ≥ 15% 감소 (P0 baseline 대비)
  - 충돌 KU 100% 가 ledger 에 영구 보존
  - S4/S5/S6 pass
  - 테스트 ≥ 530 (P0 510 + 20)
- **Depends on**: P0 (state_io 안전성, P0-X 인터페이스 고정) ✅
- **병렬 가능**: P3

#### Silver P2. Outer-Loop Remodel 완결 ✅
- **Goal**: audit 결과를 구조 변경 액션 (merge/split/reclassify/policy/gap rule)으로 compile
- **Status**: **Gate PASS** (14/14, 673 tests, E2E 28) | Commit `e8ccd77`, `2f6a2d8`
- **Scope**:
  - `src/nodes/remodel.py` [NEW]
  - `schemas/remodel_report.schema.json` [NEW]
  - `orchestrator.py` — `cycle % interval == 0 and audit.has_critical` → remodel → HITL-R → phase_bump
  - phase transition 저장 (`state/phase_{N}/...`)
  - Rollback 경로
  - SOURCE_POLICY: TTL 실제 연장 (1.5배, cap 365)
  - GAP_RULE: 빈 category에 우선순위 GU 주입 (최대 3건, critical)
- **Stages**: A (Remodel node + schema, 4 tasks) → B (Graph/orchestrator 통합, 4 tasks) → C (검증, 6 tasks)
- **Gate (정량)**:
  - Part A (프로세스): schema validate, merge 탐지, HITL 승인/거부, rollback diff=∅, S7 trigger
  - Part B (성능): before/after metrics — merge→entity_count↓, split→geo분리, reclassify→invalid↓, source_policy→TTL↑, gap_rule→GU↑
  - **주의**: 실 벤치 trial (real API, before/after 비교) 미실행 — 합성 E2E만 PASS
  - 테스트: 673 (E2E 28개)
- **Depends on**: P0 ✅, P1 ✅
- **dev-docs**: `dev/active/phase-si-p2-remodel/`

#### Silver P3. Acquisition Expansion
- **Goal**: snippet 의존 탈피, 소스 다양성 측정 가능화
- **Scope**:
  - Provider 플러그인 — `src/adapters/providers/{base,tavily,ddg,curated}_provider.py` [NEW]
  - `src/adapters/fetch_pipeline.py` [NEW] — robots / content-type / timeout / max_bytes / trust_tier
  - `collect.py` 를 SEARCH → FETCH → PARSE 3단계로 리팩터
  - Provenance 스키마 확장 (`providers_used`, `domain`, `fetch_ok`, `trust_tier`, 등)
  - `SearchConfig` 확장 (`enable_tavily`, `enable_ddg_fallback`, `fetch_top_n`, `max_bytes_per_url`, `entropy_floor`, `k_per_provider`)
  - Source diversity: `domain_entropy`, `provider_entropy`
  - 비용 가드: `cycle_llm_token_budget`, `cycle_fetch_bytes_budget` + degrade 모드
- **Gate (정량)**:
  - fetch 성공률 ≥ 80%
  - claim 당 평균 EU ≥ 1.8
  - `domain_entropy` ≥ 2.5 bits
  - cycle 당 LLM 비용 ≤ baseline × 2.0
  - robots.txt 차단 pass (S8)
  - 비용 budget degrade (S9)
  - 테스트 ≥ P1 종료 + 35
- **Depends on**: P0 (timeout/retry, P0-X 인터페이스 고정)
- **병렬 가능**: P1

#### Silver P4. Coverage Intelligence
- **Goal**: plan 이 novelty / overlap / deficit 근거로 target 선택 + **Gini 통합** + **Smart category addition**
- **Scope**:
  - `src/utils/novelty.py` [NEW] — Jaccard / token / entity overlap
  - `src/utils/coverage_map.py` [NEW] — axis × entity 그리드, deficit score, **Gini tracking 통합**
  - `plan.py` reason_code (`deficit:...`, `plateau:novelty<...`, `gini:category_imbalance`, `remodel:pending`, `seed:initial`)
  - `critique.py` metric 기반 machine-readable 처방 (`overlap > 0.8` → jump, `gini > 0.45` → diversify)
  - `plateau_detector.py` novelty trigger
  - `remodel.py` **category_addition** proposal type (보수적: ≥5 KU + LLM 판단 + 사이클당 1개 + HITL 승인)
- **Expanded from masterplan**: D-134 이행 (Gini → coverage), smart category addition
- **Gate (정량)**:
  - plan output 모든 target 이 reason_code 보유
  - 10 cycle 연속 run novelty 평균 ≥ 0.25
  - 인위적 plateau → audit/remodel trigger 발동
  - S7 full scenario pass
  - category_addition 보수적 조건 테스트 pass
- **Depends on**: P2 ✅ (remodel), P3R ✅ (provenance)
- **Dev-docs**: `dev/active/phase-si-p4-coverage/` (17 tasks, S:7/M:8/L:1)

#### Silver P5. Telemetry Contract & Dashboard
- **Goal**: 운영자가 JSON 파일 없이 상태 파악·개입
- **실행 순서**: P5-A (schema + emit) → P5-B (UI). UI-first 금지.
- **Scope**:
  - `schemas/telemetry.v1.schema.json` [NEW] — cycle 단위 snapshot
  - `src/obs/telemetry.py` [NEW] — jsonl append-only, atomic write
  - Dashboard: FastAPI + htmx + Chart.js, localhost only
  - Views: overview / cycle timeline / gap coverage map / source reliability / conflict ledger / HITL inbox (3탭) / remodel review
  - `docs/operator-guide.md` (≤ 20 페이지)
- **Gate (정량)**:
  - 100 cycle fixture: 모든 view 10s 이내 로드
  - telemetry schema contract 테스트 (positive + negative)
  - S10 scenario pass
  - 대시보드 LOC ≤ 2,000 (하드 리밋)
  - 운영자 가이드 ≥ 5페이지 walkthrough
- **Depends on**: P0 (metric emit), P3 (provenance), P4 (novelty)

#### Silver P6. Multi-Domain Validation (Silver 완료 exit gate)
- **Goal**: 프레임워크 도메인 무관성 실증
- **Scope**:
  - 2차 도메인 선정 (후보: 국내 부동산 / OSS LLM 생태계 / 한국 세법) — japan-travel 대비 time horizon / hierarchy depth / source language 3축 중 2축 이상 이질
  - Seed skeleton + seed pack, 10 cycle smoke run
  - Framework-vs-domain delta memo
- **Gate (정량)**:
  - 10 cycle 내 Gate #5 동등 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6)
  - framework 수정 ≤ 5건
  - 한글 출처 처리 에러 0
  - S11 scenario pass
- **Depends on**: P1 ~ P5 전부

---

### 의존성 그래프

```
P0 ✅ ── P1 ✅ ── P3R ── P2(재판정) ── P4 ── P5 ── P6
                  │
                  └── (P3 3단계는 REVOKED, 코드 제거 대상)
```

- **직렬화**: 리팩터 pivot 이후 병렬 여지 소멸. P3R → P2 재판정 → P4 → P5 → P6 순서
- **P5-A (telemetry schema)**: P3R provenance 축소 필드 확정 후 정의
- **P6 (multi-domain)**: curated 제거에 따른 도메인 확장 전략 재설계 포함

---

## 5. Task Breakdown (전체)

### Bronze (완료)

| Phase | Stage 개요 | Task 수 | Status |
|-------|-----------|---------|--------|
| Phase 0 | Cycle 0 수동 | — | ✅ Complete |
| Phase 0B | Cycle 1 수동 | 5 | ✅ Complete |
| Phase 0C | 축 선언 + Jump Mode + 정책 | 6 | ✅ Complete |
| Phase 1 | 기반 + 노드 + Graph 빌드 | 15 | ✅ Complete |
| Phase 2 | Real API 1/3/10 Cycle | 16 | ✅ Complete |
| Phase 3 | Conflict + Dispute + 수렴 | 9 | ✅ Complete |
| Phase 4 | Audit + Policy + Self-Tuning + Gate | 11 | ✅ Complete (Gate FAIL) |
| Phase 5 | 선행 + A~E + E-2 + Gate 재실행 ×4 | 23 | ✅ Complete (Gate #5 PASS) |
| **Bronze 합계** | | **85** | ✅ |

### Silver (계획)

| Phase | Name | Tasks | Status |
|-------|------|-------|--------|
| Silver P0 | Foundation Hardening | 32 (A:6 + B:9 + C:8 + D:3 + X:6) | ✅ Complete (Gate PASS) |
| Silver P1 | Entity Resolution & State Safety | 12 (A:4 + B:4 + C:4) | ✅ Complete (544 tests, S4/S5/S6 pass) |
| Silver P2 | Outer-Loop Remodel 완결 | 14 (A:4 + B:4 + C:6) | ✅ **Gate PASS** (D-132/133, 613 tests) |
| Silver P3 | Acquisition Expansion (3단계) | 22 (A:5 + B:6 + C:6 + D:5) | **REVOKED** (D-120, 2026-04-13) |
| Silver P3R | Snippet-First Refactor | 8 (T1~T8) | ✅ Complete (Gate PASS, D-125) |
| Gap-Res Investigation | Target cap regression + LLM parse yield | 12 (A:3 + B:3 + C:3 + D:3) | ✅ 완료 (D-129, 610 tests) |
| Silver P4 | Coverage Intelligence | 17 (A:5 + B:4 + C:3 + D:5) | **Planning** |
| Silver P5 | Telemetry Contract & Dashboard | 14 (A:5 + B:5 + C:4) | 대기 |
| Silver P6 | Multi-Domain Validation | 7 (A:3 + B:3 + C:1) | 대기 |
| Silver X | Cross-phase 제어 | 7 | 대기 |
| **Silver 합계** | | **119** | — |

**프로젝트 총계**: Bronze 85 + Silver 119 + Investigation 12 = **216 tasks**

Silver test 목표: **≥ 588 tests** (468 + P0 20 + P1 20 + P2 15 + P3 35 + P4 10 + P5 15 + P6 5 = 588)

---

## 6. Risks & Mitigation

### Silver 리스크 레지스터 (masterplan v2 §8)

| ID | 리스크 | L | I | 완화 | Owner |
|----|--------|---|---|------|-------|
| R1 | fetch 확장 → LLM 비용 3~5배 증가 | H | H | P3 cycle 비용 예산 + degrade 모드, baseline × 2.0 상한 | P3 |
| R2 | robots.txt / 저작권 위반 | M | H | robots 체크, content-type 필터, trust_tier 차등 | P3 |
| R3 | remodel 이 state 구조 파괴 | M | H | phase transition 저장, HITL-R 승인, rollback 경로 | P2 |
| R4 | 대시보드 스프롤 | M | M | LOC 2000 하드 리밋, htmx 단일 운영자, 인증/모바일 비범위 | P5 |
| R5 | 2차 도메인이 japan-travel 과 유사 | M | M | 3축 중 2축 이질 강제, framework 수정 ≤ 5건 | P6 |
| R6 | P0/P1 확장 → 다른 Phase 지연 | M | M | P0 scope-locked (8건+벤치+HITL), 추가 발견은 P1 이관 | P0 |
| R7 | DDG / alt-provider rate-limit 위반 | M | M | optional fallback 전용, 기본은 Tavily | P3 |
| R8 | 한글 출처 인코딩/형태소 이슈 | M | M | P6 에 utf-8 강제 + 한글 테스트 케이스 | P6 |
| R9 | Phase 병렬화 충돌 (P1 ∥ P3) | L | M | P0-X 인터페이스 고정 선행 | P0 |
| R10 | HITL-D 배치 큐 적체 | M | M | 대시보드 배치 뷰 Day 1, `dispute_queue > 20` → 자동 HITL-E | P5 |

### Bronze 잔류 리스크 (Silver에서 감시)
| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| JSON 파일 I/O 동시성 | Low | 단일 스레드 실행 유지 |
| Windows 인코딩 (한글) | Medium | utf-8 명시, PYTHONUTF8=1 |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| Silver P1 entity_resolver | P0 state_io 복구 + 인터페이스 고정 |
| Silver P2 remodel | P1 alias/canonicalize, P0-C HITL-R stub edge |
| Silver P3 providers / fetch_pipeline | P0 timeout/retry, SearchConfig 확장 |
| Silver P4 novelty / coverage_map | P2 remodel trigger, P3 provenance |
| Silver P5 telemetry / dashboard | P0 metric emit, P3 provenance 필드 확정, P4 reason_code |
| Silver P6 multi-domain | P1~P5 전체 + 한글 출처 인코딩 |

### 외부 (Python 패키지, Silver 추가분)
| 패키지 | 용도 | Phase |
|--------|------|-------|
| duckduckgo-search (optional) | DDG provider fallback | P3 |
| fastapi, uvicorn, jinja2 | Dashboard | P5 |
| htmx, chart.js (CDN or vendored) | Dashboard UI | P5 |
| (기존 유지) langgraph, langchain-openai, tavily-python, jsonschema | Bronze 전체 | — |

### Silver 잔여 작업 (Remaining — robots.txt 대응)

| ID | 항목 | 설명 | Phase |
|----|------|------|-------|
| C-5 | API Provider 플러그인 | Reddit API, Twitter/X API 등 공식 API를 통한 합법적 데이터 접근. robots.txt 우회 없이 구조화된 데이터 확보. 별도 SearchProvider 플러그인으로 구현. | Silver 잔여 (P3 후속) |
| C-6 | Archive/Cache fallback Provider | Google Cache, Wayback Machine을 fallback source로 활용. 원본 접근 불가 시 아카이브에서 스냅샷 취득. | Silver 잔여 (P3 후속) |

> **배경**: P3 Gate에서 67건 fetch 중 21건(31%)이 robots.txt 차단 (reddit, facebook, instagram 등). A-1 (Curated 강화) + B-3 (사전 필터링)으로 당장 효율을 개선했으나, SNS/커뮤니티 소스 접근은 근본��으로 API 기반 접근이 필요.

### Gold 세대 Must-Have (robots.txt 근본 대응)

| 항목 | 설명 | 근거 |
|------|------|------|
| API Provider 플러그인 (Reddit, Twitter/X 등) | 공식 API를 통한 구조화된 데이터 접근. SearchProvider 프로토콜 구현. | Silver P3에서 robots 차단률 31% — SNS 소스 접근 불가 |
| Archive/Cache fallback Provider (Wayback Machine, Google Cache) | 원본 접근 불가 시 아카이브 활용. FetchPipeline fallback 경로 추가. | 403/SSL 에러 + robots 차단 = 전체 fetch의 41% 손실 |

### 문서 의존성
- `docs/silver-masterplan-v2.md` — 단일 진실 소스 (Phase 표, HITL 정책, Provider 상세, 벤치 관리)
- `docs/silver-implementation-tasks.md` — 실행 backlog (touched files + 정량 gate + blocking scenario)
- `dev/active/p0-p1-remediation-plan.md` — P0 gate pass 시점에 deprecated 표기 + v2 링크 (X2)
