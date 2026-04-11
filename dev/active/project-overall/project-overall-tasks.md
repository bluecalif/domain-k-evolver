# Project Overall Tasks
> Last Updated: 2026-04-11
> Status: Bronze 세대 완료 (85/85) · Silver 세대 착수 대기 (0/119)

## Summary

### Bronze 세대 (Phase 0~5) ✅

| Phase | Total | Done | Gate | Commit |
|-------|-------|------|------|--------|
| Phase 0 (Cycle 0 수동) | — | ✅ | 수동 검증 PASS | — |
| Phase 0B (Cycle 1 수동) | 5 | 5/5 ✅ | 불변원칙 PASS | `0452dcc` |
| Phase 0C (GU 전략) | 6 | 6/6 ✅ | 정책 v1.0 확정 | `c338351` |
| Phase 1 (LangGraph Core) | 15 | 15/15 ✅ | 191 tests | `0be8221` |
| Phase 2 (Bench Integration) | 16 | 16/16 ✅ | 272 tests | — |
| Phase 3 (Cycle Remodeling) | 9 | 9/9 ✅ | 301 tests, conflict_rate 0 | `9a3c5f2` |
| Phase 4 (Self-Governing) | 11 | 11/11 ✅ | 420 tests, Gate FAIL | `62915de` |
| Phase 5 (Inner Loop Quality) | 23 | 23/23 ✅ | **468 tests, Gate #5 PASS** | `b122a23` |
| **Bronze 합계** | **85** | **85/85** | — | — |

### Silver 세대 (P0~P6 + X) — 대기

| Phase | Total | S | M | L | Done |
|-------|-------|---|---|---|------|
| P0 Foundation Hardening | 32 | 15 | 13 | 4 | 0/32 |
| P1 Entity Resolution | 12 | 3 | 9 | 0 | 0/12 |
| P2 Outer-Loop Remodel | 14 | 5 | 8 | 1 | 0/14 |
| P3 Acquisition Expansion | 22 | 7 | 13 | 2 | 0/22 |
| P4 Coverage Intelligence | 11 | 5 | 6 | 0 | 0/11 |
| P5 Telemetry & Dashboard | 14 | 3 | 10 | 1 | 0/14 |
| P6 Multi-Domain | 7 | 2 | 3 | 2 | 0/7 |
| X Cross-phase | 7 | 7 | 0 | 0 | 0/7 |
| **Silver 합계** | **119** | — | — | — | **0/119** |

**총계: Bronze 85 (완료) + Silver 119 (대기) = 204 tasks · 목표 테스트 수 ≥ 588**

참조 문서:
- 단일 진실 소스: `docs/silver-masterplan-v2.md` §4 Phase 표
- 실행 backlog: `docs/silver-implementation-tasks.md` §4~§12 (S1~S11 시나리오 포함)
- Phase 별 dev-docs: `dev/active/phase-si-{p0~p6}-{name}/` (예정)

---

# Bronze 세대 ✅

## Phase 0: Cycle 0 수동 검증 ✅

모두 완료. 상세는 `bench/japan-travel/cycle-0/` 및 `docs/design-v2.md` 참조.

---

## Phase 0B: Cycle 1 수동 검증 ✅

> **완료**: 2026-03-03 | Conflict-preserving 실전 검증 성공
> **결과**: KU 21 (active 19 + disputed 2), EU 33, GU 16 open / 15 resolved

- [x] **0B.1** Cycle 1 디렉토리 준비 → `3a73af9`
- [x] **0B.2** Collect — 24 Claims, 15 EU, 충돌 2건 감지 → `4e26acf`
- [x] **0B.3** Integrate — 7 add, 2 update, 2 disputed, 3 동적 GU → `1b7cd37`
- [x] **0B.4** Critique — 5대 불변원칙 전체 PASS, 처방 5개(RX-07~11) → `b44ce73`
- [x] **0B.5** Plan Modify — Revised Plan C2, design-v2 피드백 → `0452dcc`

---

## Phase 0C: GU 전략 재검토 ✅

> **완료**: 2026-03-04 | Axis Coverage Matrix + Jump Mode 실측 검증 + 정책 v1.0 확정
> **결과**: KU 28 (active 27 + disputed 1), EU 55, GU 21 open / 18 resolved / 39 total

- [x] **0C.1** 축 선언 보완 — skeleton axes 4축 추가
- [x] **0C.2** Axis Coverage Matrix 첫 계산 — geography/risk deficit 0.200
- [x] **0C.3** Cycle 2 준비 — T1 발동 → Jump Mode, jump_cap=10
- [x] **0C.4** Cycle 2 수동 실행 → `c338351`
- [x] **0C.5** 정책 확정 — expansion-policy v1.0
- [x] **0C.6** 설계 문서 통합 — design-v2 mode_node/entity hierarchy, spec v1.1

---

## Phase 1: LangGraph Core Pipeline ✅

> **완료**: 2026-03-05 | 191 tests passed | 14-node StateGraph

- [x] **1.1** 프로젝트 초기화 → `4c9d793`
- [x] **1.2** EvolverState 타입 정의 → `4c9d793`
- [x] **1.3** JSON 파일 I/O 유틸리티 → `4c9d793`
- [x] **1.4** Schema 검증 유틸리티 → `4c9d793`
- [x] **1.5** Metrics 계산 유틸리티 → `4c9d793`
- [x] **1.6** seed_node → `0be8221`
- [x] **1.7** plan_node → `0be8221`
- [x] **1.8** collect_node → `0be8221`
- [x] **1.9** integrate_node → `0be8221`
- [x] **1.10** critique_node → `0be8221`
- [x] **1.11** plan_modify_node → `0be8221`
- [x] **1.12** hitl_gate_node → `0be8221`
- [x] **1.13** StateGraph 빌드
- [x] **1.14** 엣지 라우팅 로직
- [x] **1.15** 단위 테스트 (36 tests)

---

## Phase 2: Bench Integration & Real Self-Evolution ✅

> **완료**: 272 tests | 10+ Cycle Real API 자동화 성공

### Stage A': Smoke Test → Real 1 Cycle ✅
- [x] **2.1** API 키 검증 + Smoke Test
- [x] **2.2** LLM 응답 파싱 강화
- [x] **2.3** collect_node 프롬프트 정교화
- [x] **2.4** Orchestrator 정합성 수정
- [x] **2.5** Real API 1 Cycle 실행 ★★★

### Stage B': 안정화 + 3 Cycle ✅
- [x] **2.6** 에러 핸들링 + Rate Limiting
- [x] **2.7** seed 일반화 + cycle>1 스킵
- [x] **2.8** plan_modify 실효성 + C3 수정
- [x] **2.9** 불변원칙 자동검증
- [x] **2.10** 비용/토큰 로깅
- [x] **2.11** Real API 3 Cycle 실행 ★★

### Stage C': 10+ Cycle 자동화 ✅
- [x] **2.12** Plateau Detection + 자동 종료
- [x] **2.13** Metrics Guard
- [x] **2.14** 10 Cycle Real 실행 ★
- [x] **2.15** Bench Run CLI 정비
- [x] **2.16** 결과 분석 + Snapshot Diff

---

## Phase 3: Cycle Quality Remodeling ✅

> **완료**: 2026-03-06 | 301 tests | Active 31→77 (+148%), conflict_rate 0.635→0.000

- [x] **3.1** `_detect_conflict()` LLM semantic 교체 → `6e27a65`
- [x] **3.2** 충돌 판정 테스트 + FP rate 측정
- [x] **3.3** 10 Cycle 재실행 → conflict_rate 0.234
- [x] **3.4** dispute resolution 설계 + 구현 → `c45b089`
- [x] **3.5** disputed→active 전환 경로 → `c45b089`
- [x] **3.6** critique dispute resolution workflow → `c45b089`
- [x] **3.7** C6 conflict_rate < 0.15 상한 → `9a3c5f2`
- [x] **3.8** early stopping 개선 → `9a3c5f2`
- [x] **3.9** 최종 10 Cycle + Phase 2 대비 개선 보고 → `9a3c5f2`

---

## Phase 4: Self-Governing Evolver ✅

> **완료**: 2026-03-07 | 420 tests, 11/11 tasks | Gate FAIL (VP1 3/5, VP2 2/6, VP3 5/6)
> **보고서**: `docs/archive/phase4-readiness-report.md`

### Stage A: Outer Loop Audit ✅
- [x] **4.1** Executive Audit 프레임워크 → `cebd47e`
- [x] **4.2** 다축 교차 커버리지 진단 → `cebd47e`
- [x] **4.3** KU Yield/Cost 효율 분석 → `cebd47e`

### Stage B: Policy Evolution ✅
- [x] **4.4** Policy 스키마 + 버전 관리 → `816fb2d`
- [x] **4.5** Audit → Policy 자동 수정 → `816fb2d`
- [x] **4.6** Source Credibility 학습 → `816fb2d`

### Stage C: Strategic Self-Tuning ✅
- [x] **4.7** Explore/Exploit 자동 조정 → `31ef46d`
- [x] **4.8** Jump Trigger 동적 관리 → `31ef46d`
- [x] **4.9** Convergence 조건 고도화 → `31ef46d`

### Stage D: Evolver Readiness Gate ✅ (FAIL)
- [x] **4.10** Readiness 벤치마크 실행 → `62915de`
- [x] **4.11** 3-Viewpoint Readiness 판정 → `62915de`

---

## Phase 5: Inner Loop Quality ✅

> **완료**: 2026-03-09 | 468 tests, 23/23 tasks | **Gate #5 PASS** (VP1 5/5, VP2 6/6, VP3 5/6)
> **commit**: `b122a23` | 상세: `dev/active/phase5-inner-loop-quality/`

### 선행: Gate 메트릭 수정 ✅
- [x] **5.0** VP1-R1 Shannon Entropy → Gini Coefficient 교체

### Stage A: Geography Axis-Tags 전파 ✅
- [x] **5.1** Integrate: GU→KU axis_tags 전파
- [x] **5.2** Integrate: KU 내용 기반 geography 추론
- [x] **5.3** Integrate/Plan: 동적 GU 생성 시 geography 부여
- [x] **5.4** Readiness Gate: blind_spot KU 기반 개선

### Stage B: Staleness 자동갱신 ✅
- [x] **5.5** Critique: Stale KU → Refresh GU 자동생성 (D-55)
- [x] **5.6** Integrate: Refresh 통합 시 KU 갱신

### Stage C: Category 균형 + Field 다양성 ✅
- [x] **5.7** Critique: 소수 카테고리 균형 GU (D-56)
- [x] **5.8** Integrate: Field 다양성 억제

### Stage D: GU Resolve Rate 개선 + bench 정리 ✅
- [x] **5.10a** bench/ 정리 — 더블 서픽스 버그 수정 (D-61)
- [x] **5.10b** Mode: target_count/cap 하드캡 제거 (D-60)

### Stage E: Staleness 메커니즘 개선 ✅
- [x] **5.12a** stale refresh observed_at 버그 수정 (D-62)
- [x] **5.12b** stale refresh confidence 가중 평균 (D-63)
- [x] **5.12c** Critique: Adaptive REFRESH_GU_CAP (D-64)
- [x] **5.12d** Mode: T7 Staleness Trigger (D-65)
- [x] **5.12e** Readiness Gate: Closed Loop 세분화 (D-66)

### Stage E-2: VP2 잔여 FAIL 해결 ✅
- [x] **5.14a** 신규/condition_split KU observed_at = today (D-67)
- [x] **5.14b** 일반 업데이트 observed_at = today (D-68)
- [x] **5.14c** evidence-count 가중 평균 (D-69)
- [x] **5.14d** multi-evidence confidence boost (D-70)

### 검증: Gate 재실행 ✅
- [x] **5.9** Gate 재실행 #1 — **FAIL** (VP1 3/5, VP2 2/6, VP3 5/6)
- [x] **5.11** Gate 재실행 #2/#3 (15 cycle) — **FAIL** (VP2 3/6→4/6)
- [x] **5.13** Gate 재실행 #4 — **FAIL** (VP2 4/6, staleness=3)
- [x] **5.15** Gate 재실행 #5 — **PASS** (VP1 5/5, VP2 6/6, VP3 5/6) ★

---

# Silver 세대 (P0~P6 + X) — 대기

> **단일 진실 소스**: `docs/silver-masterplan-v2.md` §4 Phase 표
> **실행 backlog**: `docs/silver-implementation-tasks.md` §4~§12
> **착수 규칙**: P0 은 scope-locked (8 remediation + 벤치 스캐폴딩 + HITL 축소 + 인터페이스 고정 외 금지)

## Phase P0: Foundation Hardening (32 tasks)

> **목표**: Silver 전체 의존 토대 — adapter 강건성, Silver bench 격리, HITL 축소, 인터페이스 동결
> **Gate**: bare-except 0, 신규 테스트 ≥ 20 (누적 ≥ 488), 48h soak pass, p0-baseline trial 재현, S1/S2/S3 scenario pass

### P0-A. Silver 벤치 스캐폴딩
- [ ] **P0-A1** `bench/silver/INDEX.md` 생성 `[S]`
- [ ] **P0-A2** 템플릿 3종 (`trial-card.md`, `readiness-report.md`, `config.snapshot.json`) `[S]`
- [ ] **P0-A3** 첫 baseline trial 경로 생성 `[S]`
- [ ] **P0-A4** `state_io.py`/`orchestrator.py` `--bench-root` 격리 `[M]`
- [ ] **P0-A5** `run_bench/run_one_cycle/run_readiness` 에 `--bench-root` 인자 `[S]`
- [ ] **P0-A6** `config.snapshot.json` 자동 작성 (dataclass + git HEAD + provider list) `[M]`

### P0-B. 기존 remediation 8건 (p0-p1-remediation-plan.md 흡수)
- [ ] **P0-B1** (P0-3) `search_adapter.py` retry 판정 정규표현화 `[S]`
- [ ] **P0-B2** (P0-2a) `config.py` request_timeout / max_retries `[S]`
- [ ] **P0-B3** (P0-2b) `llm_adapter.py` ChatOpenAI timeout 전달 `[S]`
- [ ] **P0-B4** (P0-2c) Tavily search/extract 명시적 timeout `[S]`
- [ ] **P0-B5** (P0-2d) `collect.py` ThreadPoolExecutor future timeout `[M]`
- [ ] **P0-B6** (P0-1) `collect.py` 이중 bare-except 제거 `[M]`
- [ ] **P0-B7** (P1-1) `integrate.py` `except ValueError: pass` 제거 `[M]`
- [ ] **P0-B8** (P1-4) `state_io.py` 복구 경로 `[M]`
- [ ] **P0-B9** (P1-3) 테스트 확장 `[M]`

### P0-C. HITL 정책 축소 (masterplan §14)
- [ ] **P0-C1** `graph.py` 에서 A/B/C edge 제거 `[M]`
- [ ] **P0-C2** `graph.py` 에 HITL-S edge 추가 `[M]`
- [ ] **P0-C3** `route_after_critique` 단순화 `[S]`
- [ ] **P0-C4** `route_after_any → hitl_e` 조건부 분기 공통 함수 `[M]`
- [ ] **P0-C5** `hitl_gate.py` 를 HITL-S/HITL-R/HITL-E 3케이스로 축소 `[M]`
- [ ] **P0-C6** `metrics_guard.py` 확장 — Silver v2 5개 임계치 `[M]`
- [ ] **P0-C7** `EvolverState.dispute_queue` 필드 추가 `[S]`
- [ ] **P0-C8** 테스트 (HITL-S/E trigger, auto-resume) `[M]`

### P0-D. Silver baseline trial 재현
- [ ] **P0-D1** P4·P5 스모크를 `bench/silver/japan-travel/p0-{date}-baseline/` 에 재실행 `[M]`
- [ ] **P0-D2** `readiness-report.md` 작성 — VP1 ≥ 4/5, VP2 ≥ 5/6 `[S]`
- [ ] **P0-D3** `INDEX.md` 첫 행 삽입 `[S]`

### P0-X. 인터페이스 고정 (R9 완화)
- [ ] **P0-X1** `integrate_node` I/O dict shape 동결 `[S]`
- [ ] **P0-X2** `collect_node` I/O dict shape 동결 `[S]`
- [ ] **P0-X3** `Claim`/`EU` provenance 필드 예약 (optional) `[S]`
- [ ] **P0-X4** `EvolverState` 5개 신규 필드 일괄 선언 `[S]`
- [ ] **P0-X5** `metrics_logger` key 전체 목록 동결 `[S]`
- [ ] **P0-X6** `tests/conftest.py` 공통 fixture 재정비 `[S]`

---

## Phase P1: Entity Resolution & State Safety (12 tasks)

> **목표**: Alias/is_a 해석 + conflict ledger 영속화
> **Gate**: 동의어/is_a 테스트 pass, 중복 KU ≥ 15% 감소, ledger 100% 보존, S4/S5/S6 pass, 테스트 ≥ 508

### P1-A. 해상도 계층
- [ ] **P1-A1** `src/utils/entity_resolver.py` 신규 (alias/is_a/canonicalize) `[M]`
- [ ] **P1-A2** `integrate.py._find_existing_ku` resolver 경유 `[M]`
- [ ] **P1-A3** skeleton validator 확장 (aliases/is_a) `[S]`
- [ ] **P1-A4** japan-travel skeleton 에 alias/is_a 예시 추가 `[S]`

### P1-B. Conflict ledger 영속화
- [ ] **P1-B1** `state/conflict_ledger.json` 포맷 정의 `[M]`
- [ ] **P1-B2** `integrate_node` ledger entry 생성 (resolve 후에도 유지) `[M]`
- [ ] **P1-B3** `state_io.py` save/load 에 ledger 포함 `[S]`
- [ ] **P1-B4** dispute_queue ↔ conflict_ledger 관계 명시 `[S]`

### P1-C. 검증
- [ ] **P1-C1** `test_entity_resolver.py` — 최소 8 테스트 `[M]`
- [ ] **P1-C2** `test_integrate.py` — S4/S5/S6 scenario `[M]`
- [ ] **P1-C3** `test_japan_travel_rerun.py` — 중복 KU 15% 감소 assert `[M]`
- [ ] **P1-C4** ledger 영속화 테스트 `[S]`

---

## Phase P2: Outer-Loop Remodel 완결 (14 tasks)

> **목표**: Phase 4 audit 위에 remodel/phase_bump/rollback 경로 추가
> **Gate**: remodel report schema validate, rollback state diff=∅, 30% 중복 합성 시나리오 탐지, S7 trigger pass

### P2-A. Remodel node + schema
- [ ] **P2-A1** `src/nodes/remodel.py` 신규 `[L]`
- [ ] **P2-A2** `schemas/remodel_report.schema.json` 필드 정의 `[M]`
- [ ] **P2-A3** `EvolverState.phase_number` + `phase_history` `[S]`
- [ ] **P2-A4** `state/phase_{N}/` 스냅샷 로직 `[M]`

### P2-B. Graph/orchestrator 통합
- [ ] **P2-B1** `graph.py` critique→audit→remodel→hitl_r→phase_bump 경로 `[M]`
- [ ] **P2-B2** `hitl_gate.py` HITL-R 핸들러 완성 `[M]`
- [ ] **P2-B3** `orchestrator.py` phase transition 핸들러 `[M]`
- [ ] **P2-B4** Rejection/rollback path `[M]`

### P2-C. 검증
- [ ] **P2-C1** merge 시나리오 테스트 `[S]`
- [ ] **P2-C2** split 시나리오 테스트 `[S]`
- [ ] **P2-C3** reclassify 시나리오 테스트 `[S]`
- [ ] **P2-C4** rollback 시나리오 테스트 `[S]`
- [ ] **P2-C5** S7 trigger 경로 테스트 `[M]`
- [ ] **P2-C6** schema 양방향 테스트 `[S]`

---

## Phase P3: Acquisition Expansion (22 tasks)

> **목표**: SEARCH/FETCH/PARSE 3단계 분리, provider 플러그인 3개, provenance, 비용 가드
> **Gate**: fetch ≥ 80%, EU/claim ≥ 1.8, domain_entropy ≥ 2.5 bits, 비용 ≤ baseline × 2, S8/S9 pass

### P3-A. Provider 플러그인 (SEARCH)
- [ ] **P3-A1** `base.py` SearchProvider Protocol + SearchResult dataclass `[S]`
- [ ] **P3-A2** `tavily_provider.py` (기존 로직 이식, fetch 제거) `[M]`
- [ ] **P3-A3** `ddg_provider.py` (optional, gated) `[M]`
- [ ] **P3-A4** `curated_provider.py` (검색 안 함, preferred_sources) `[M]`
- [ ] **P3-A5** `search_adapter.py` retry 유틸 제공자로 축소 `[M]`

### P3-B. FetchPipeline (FETCH)
- [ ] **P3-B1** `FetchPipeline.fetch_many` `[L]`
- [ ] **P3-B2** `FetchResult` 필드 정의 `[S]`
- [ ] **P3-B3** Robots.txt 캐시 `[M]`
- [ ] **P3-B4** Content-type 필터 `[S]`
- [ ] **P3-B5** max_bytes 처리 `[S]`
- [ ] **P3-B6** Rate-limit 도메인별 `[M]`

### P3-C. Collect 리팩터 + provenance + 비용
- [ ] **P3-C1** `collect.py` 리팩터 (provider → FetchPipeline → PARSE) `[L]`
- [ ] **P3-C2** 기존 `search_tool.fetch(url)` 제거 `[S]`
- [ ] **P3-C3** Claim/EU provenance 필드 추가 `[M]`
- [ ] **P3-C4** `SearchConfig` 확장 (fallback/entropy_floor/budget) `[M]`
- [ ] **P3-C5** 다이버시티 메트릭 per cycle `[M]`
- [ ] **P3-C6** 비용 가드 per cycle (token/byte budget + degrade) `[M]`

### P3-D. 의존성 + 테스트
- [ ] **P3-D1** `pyproject.toml` duckduckgo-search optional `[S]`
- [ ] **P3-D2** provider 테스트 ≥ 12 `[M]`
- [ ] **P3-D3** FetchPipeline 테스트 ≥ 10 (S8) `[M]`
- [ ] **P3-D4** collect 통합 테스트 ≥ 6 (S9) `[M]`
- [ ] **P3-D5** legacy search_adapter mig test `[S]`

---

## Phase P4: Coverage Intelligence (11 tasks)

> **목표**: novelty/coverage_map primitives + reason_code 체계 + plateau 고도화
> **Gate**: plan 100% reason_code, 10 cycle novelty 평균 ≥ 0.25, 인위 plateau → audit/remodel trigger, S7 pass

### P4-A. Metrics primitives
- [ ] **P4-A1** `novelty.py` (Jaccard/token/entity overlap) `[M]`
- [ ] **P4-A2** `coverage_map.py` (axis/bucket/deficit) `[M]`
- [ ] **P4-A3** `EvolverState.novelty_history` + `coverage_map` `[S]`

### P4-B. Plan/Critique/Plateau 통합
- [ ] **P4-B1** `plan.py` target 에 `reason_code` enum `[M]`
- [ ] **P4-B2** `critique.py` machine-readable rule `[M]`
- [ ] **P4-B3** `plateau_detector.py` novelty-based trigger `[M]`
- [ ] **P4-B4** remodel_pending → plan reason_code 영향 `[S]`

### P4-C. 검증
- [ ] **P4-C1** novelty 단위 테스트 `[S]`
- [ ] **P4-C2** reason-code 생성 테스트 (5 enum) `[S]`
- [ ] **P4-C3** S7 full scenario `[M]`
- [ ] **P4-C4** novelty/overlap telemetry 노출 `[S]`

---

## Phase P5: Telemetry Contract & Dashboard (14 tasks)

> **목표**: Telemetry schema v1 + FastAPI 운영 대시보드 (≤ 2000 LOC)
> **Gate**: schema validate, 100-cycle fixture 모든 view ≤ 10s, stub 금지, LOC 하드리밋, S10 pass, operator-guide 5+ 페이지
> **제약**: P5-A (telemetry schema) 가 P5-B (UI) **엄격 선행** (D-77)

### P5-A. Telemetry 계약
- [ ] **P5-A1** `schemas/telemetry.v1.schema.json` 필수 필드 `[M]`
- [ ] **P5-A2** `src/obs/telemetry.py` emitter (jsonl atomic) `[M]`
- [ ] **P5-A3** 노드 경계 emit hook (orchestrator 단일 call site) `[M]`
- [ ] **P5-A4** 출력 경로 `bench/silver/{domain}/{trial}/telemetry/cycles.jsonl` `[S]`
- [ ] **P5-A5** 스키마 계약 테스트 (positive/negative, S10) `[M]`

### P5-B. Dashboard
- [ ] **P5-B1** FastAPI bootstrap (localhost, no auth) `[M]`
- [ ] **P5-B2** 의존성 (fastapi/uvicorn/jinja2/htmx/chart.js) `[S]`
- [ ] **P5-B3** Views (masterplan §4 verbatim) `[L]`
- [ ] **P5-B4** Data source: 실제 artifact (stub 금지) `[M]`
- [ ] **P5-B5** `docs/operator-guide.md` 작성 `[M]`

### P5-C. 검증
- [ ] **P5-C1** schema 계약 재검증 `[S]`
- [ ] **P5-C2** 100-cycle fixture load ≤ 10s `[M]`
- [ ] **P5-C3** Self-test "slowdown" walkthrough `[M]`
- [ ] **P5-C4** LOC 하드 리밋 측정 (≤ 2000) `[S]`

---

## Phase P6: Multi-Domain Validation (7 tasks)

> **목표**: 2차 도메인 Smoke + framework-vs-domain delta memo
> **Gate**: 10 cycle Gate #5 동등 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6), framework 수정 ≤ 5, 한글 에러 0, S11 pass
> **선정 기준**: japan-travel 대비 {time horizon, hierarchy depth, source language} 3축 중 2축 이질 (D-80)

### P6-A. 도메인 선정
- [ ] **P6-A1** 후보 3 개 중 1 개 선택 `[S]`
- [ ] **P6-A2** `trial-card.md` 선정 rationale `[S]`
- [ ] **P6-A3** skeleton + seed pack 작성 `[M]`

### P6-B. Smoke validation
- [ ] **P6-B1** 10 cycle smoke run `[L]`
- [ ] **P6-B2** Readiness report (Gate #5 동등) `[M]`
- [ ] **P6-B3** Framework-vs-domain delta memo (≤ 5건) `[M]`

### P6-C. 검증 파일
- [ ] **P6-C1** `test_multidomain/test_smoke_run.py` (S11) `[M]`

---

## Cross-phase 제어 (X, 7 tasks)

- [ ] **X1** Phase 종료 시마다 `bench/silver/INDEX.md` append `[S]`
- [ ] **X2** `dev/active/p0-p1-remediation-plan.md` P0 완료 시 **deprecated** 표기 + v2 링크 (삭제 금지) `[S]`
- [ ] **X3** 신규 schema/contract 에 positive + negative 테스트 각 1 `[S]`
- [ ] **X4** 신규 디렉토리에 `__init__.py` 필수 `[S]`
- [ ] **X5** 운영자 문서는 canonical artifact 링크 (gate 정의 재진술 금지) `[S]`
- [ ] **X6** 각 Phase 종료 시 리스크 레지스터 (masterplan §8) 재평가 `[S]`
- [ ] **X7** LLM/비용 metrics (`llm_tokens_per_cycle`, `fetch_bytes_per_cycle`) P0 에서 stub emit 시작 `[S]`

---

## Silver 완료 체크리스트 (`silver-implementation-tasks.md` §14 거울)

- [ ] P0~P6 모든 phase gate 통과
- [ ] S1~S11 scenario 11 개 전부 pass
- [ ] 5 대 불변원칙 machine-check green
- [ ] Test 수 ≥ **588** (468 + P0 20 + P1 20 + P2 15 + P3 35 + P4 10 + P5 15 + P6 5)
- [ ] Cycle LLM 비용 regression 없음 (baseline 대비 ≤ 2.0×)
- [ ] 운영자 가이드 5 페이지 이상 walkthrough
- [ ] `bench/silver/INDEX.md` 에 P0 baseline + 2nd 도메인 smoke 행 존재
- [ ] Silver readiness 리포트 승인
