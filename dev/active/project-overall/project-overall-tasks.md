# Project Overall Tasks
> Last Updated: 2026-04-27
> Status: Bronze 완료 (85/85) · Silver P0 (32) · P1 (12) · P3R (8) · P2 (14) · Gap-Res (12) · P4 (42) · **P5 완료 (15/15, Gate PASS)** · **SI-P7 attempt 2 MERGED** (main `0d7ebb3`, 934 tests) · **P6 착수 예정**

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

### Silver 세대 (P0~P6 + X)

| Phase | Total | S | M | L | Done | Gate |
|-------|-------|---|---|---|------|------|
| P0 Foundation Hardening | 32 | 18 | 13 | 1 | **32/32** ✅ | PASS (VP1 5/5, VP2 5/6, VP3 5/6) |
| P1 Entity Resolution | 12 | 5 | 7 | 0 | **12/12** ✅ | PASS (544 tests, S4/S5/S6) |
| P2 Outer-Loop Remodel | 14 | 5 | 8 | 1 | **14/14** ✅ | **Gate PASS** (D-132/133, 613 tests) |
| P3 Acquisition Expansion | 22 | 7 | 13 | 2 | — | **REVOKED** (D-120) |
| P3R Snippet-First Refactor | 8 | — | — | — | **8/8** ✅ | PASS (D-125, 608 tests) |
| P4 Coverage Intelligence | **42** | 27 | 15 | 3 | **42/42** ✅ | **Gate PASS (VP4 4/5, D-147~D-150 해소, 797 tests)** |
| P5 Telemetry & Dashboard | 15 | 4 | 9 | 1 | **15/15** ✅ | **Gate PASS** (821 tests, S10 PASS, LOC 986) |
| P6 Consolidation & KB Release | TBD | — | — | — | 0 | 착수 예정 (A→B→C) |
| SI-P7 Structural Redesign (Attempt 1) | ~52 (Step A 10 / Step B 14 / Step V 11 / Step C 12 + V-T1~T11 instrumentation) | — | — | — | Step A/B + Step V 완료 | **Archived** (main `a33dfdb`, tag `si-p7-attempt-1`). v5 sequential ablation → D-194/195/196 |
| SI-P7 Structural Redesign (Attempt 2 rebuild) | ~47 | — | — | — | **MERGED** ✅ | **2026-04-27 main merge 완료** (`0d7ebb3`): Trial 1/2/3, KU 79→120 (+52%), 934 tests. branch 삭제됨. 잔여 FAIL → Stage B-3 / P6 동반 처리. |
| M1 Multi-Domain (suspended) | 7 | 2 | 3 | 2 | 0/7 | P6 완료 후 활성화 |
| X Cross-phase | 7 | 7 | 0 | 0 | 0/7 | — |
| **Silver 합계** | **134+** | — | — | — | **67/134+** | — |

### Investigation Phase (Gap-Resolution)

| Phase | Total | S | M | Done | Status |
|-------|-------|---|---|------|--------|
| Gap-Res Investigation | 12 | 8 | 4 | 12/12 | 완료 (D-131) |

**총계: Bronze 85 + Silver (P5 15 포함) 167+ + Investigation 12 = 264+ tasks · 현재 테스트 934**

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

# Silver 세대 (P0~P6 + X)

> **단일 진실 소스**: `docs/silver-masterplan-v2.md` §4 Phase 표
> **실행 backlog**: `docs/silver-implementation-tasks.md` §4~§12

## Phase P0: Foundation Hardening ✅ (32/32, Gate PASS)

> **완료**: 2026-04-12 | 510 tests, Gate PASS (VP1 5/5, VP2 5/6, VP3 5/6)
> **dev-docs**: `dev/active/phase-si-p0-foundation/`

### P0-A. Silver 벤치 스캐폴딩
- [x] **P0-A1** `bench/silver/INDEX.md` 생성 `[S]` — `2f9117a`
- [x] **P0-A2** 템플릿 3종 `[S]` — `2f9117a`
- [x] **P0-A3** 첫 baseline trial 경로 생성 `[S]` — `2f9117a`
- [x] **P0-A4** `state_io.py`/`orchestrator.py` `--bench-root` 격리 `[M]` — `2f9117a`
- [x] **P0-A5** `run_bench/run_one_cycle/run_readiness` 에 `--bench-root` 인자 `[S]` — `2f9117a`
- [x] **P0-A6** `config.snapshot.json` 자동 작성 `[M]` — `6c7f28f`

### P0-B. 기존 remediation 8건
- [x] **P0-B1** (P0-3) `search_adapter.py` retry 판정 정규표현화 `[S]` — `e73b136`
- [x] **P0-B2** (P0-2a) `config.py` request_timeout `[S]` — `e73b136`
- [x] **P0-B3** (P0-2b) `llm_adapter.py` ChatOpenAI timeout 전달 `[S]` — `e73b136`
- [x] **P0-B4** (P0-2c) Tavily search/extract 명시적 timeout `[S]` — `e73b136`
- [x] **P0-B5** (P0-2d) `collect.py` ThreadPoolExecutor future timeout `[M]` — `e73b136`
- [x] **P0-B6** (P0-1) `collect.py` 이중 bare-except 제거 `[M]` — `e73b136`
- [x] **P0-B7** (P1-1) `integrate.py` `except ValueError: pass` 제거 `[M]` — `e73b136`
- [x] **P0-B8** (P1-4) `state_io.py` 복구 경로 `[M]` — `e73b136`
- [x] **P0-B9** (P1-3) 테스트 확장 `[L]` — `f21a249`

### P0-C. HITL 정책 축소
- [x] **P0-C1** `graph.py` A/B/C edge 제거 `[M]` — `83ce974`
- [x] **P0-C2** `graph.py` HITL-S edge 추가 `[M]` — `83ce974`
- [x] **P0-C3** `route_after_critique` 단순화 `[S]` — `83ce974`
- [x] **P0-C4** `should_auto_pause()` 공통 함수 `[M]` — `83ce974`
- [x] **P0-C5** `hitl_gate.py` S/R/E 축소 `[M]` — `83ce974`
- [x] **P0-C6** `metrics_guard.py` 확장 `[M]` — `83ce974`
- [x] **P0-C7** `EvolverState.dispute_queue` 필드 추가 `[S]` — `83ce974`
- [x] **P0-C8** 테스트 `[M]` — `f21a249`

### P0-X. 인터페이스 고정
- [x] **P0-X1** `integrate_node` I/O dict shape 동결 `[S]` — `f67cbf3`
- [x] **P0-X2** `collect_node` I/O dict shape 동결 `[S]` — `9258832`
- [x] **P0-X3** `Claim`/`EU` provenance 필드 예약 `[S]` — `f7a4123`
- [x] **P0-X4** `EvolverState` 5개 신규 필드 일괄 선언 `[S]` — `e3f5659`
- [x] **P0-X5** `metrics_logger` key 전체 목록 동결 `[S]` — `28c436b`
- [x] **P0-X6** `tests/conftest.py` 공통 fixture 재정비 `[S]` — `cdf0a96`

### P0-D. Silver baseline trial 재현
- [x] **P0-D1** fresh seed + 15 cycle + Orchestrator 경유 재실행 `[M]` — `30946ac`
- [x] **P0-D2** `readiness-report.md` 작성 — VP1 5/5, VP2 5/6, VP3 5/6 `[S]` — `30946ac`
- [x] **P0-D3** `INDEX.md` 2행 삽입 `[S]` — `30946ac`

---

## Phase P1: Entity Resolution & State Safety ✅ (12/12, 544 tests, S4/S5/S6 pass)

> **완료**: 2026-04-12 | 544 tests, Gate PASS (S4/S5/S6 pass) | Commit `3bbde92`
> **Gate**: 동의어/is_a 테스트 pass, 중복 KU 감소, ledger 100% 보존, S4/S5/S6 pass, 테스트 544 ≥ 530
> **dev-docs**: `dev/active/phase-si-p1-entity-resolution/`
> **비고**: dedicated bench trial 미실행 — 단위/통합 테스트 + S4/S5/S6 scenario로 gate 판정. P3 이후 누적 bench trial 시 regression 확인 예정.

### P1-A. 해상도 계층
- [x] **P1-A1** `src/utils/entity_resolver.py` 신규 (alias/is_a/canonicalize) `[M]` — `3bbde92`
- [x] **P1-A2** `integrate.py._find_matching_ku` resolver 경유 `[M]` — `3bbde92`
- [x] **P1-A3** skeleton validator 확장 (aliases/is_a) `[S]` — `3bbde92`
- [x] **P1-A4** japan-travel skeleton 에 alias/is_a 예시 추가 `[S]` — `3bbde92`

### P1-B. Conflict ledger 영속화
- [x] **P1-B1** `state/conflict_ledger.json` 포맷 정의 `[M]` — `3bbde92`
- [x] **P1-B2** `integrate_node` ledger entry 생성 (resolve 후에도 유지) `[M]` — `3bbde92`
- [x] **P1-B3** `state_io.py` save/load 에 ledger 포함 `[S]` — `3bbde92`
- [x] **P1-B4** dispute_queue ↔ conflict_ledger 관계 명시 `[S]` — `3bbde92`

### P1-C. 검증
- [x] **P1-C1** `test_entity_resolver.py` (16건) `[M]` — `3bbde92`
- [x] **P1-C2** `test_integrate.py` — S4/S5/S6 scenario (8건) `[M]` — `3bbde92`
- [x] **P1-C3** `test_japan_travel_rerun.py` (3건: alias dedup) `[M]` — `3bbde92`
- [x] **P1-C4** ledger 영속화 테스트 (8건) `[S]` — `3bbde92`

---

## Phase P2: Outer-Loop Remodel 완결 (14 tasks)

> **목표**: Phase 4 audit 위에 remodel/phase_bump/rollback 경로 추가
> **Gate**: remodel report schema validate, rollback state diff=∅, 30% 중복 합성 시나리오 탐지, S7 trigger pass

### P2-A. Remodel node + schema
- [x] **P2-A1** `src/nodes/remodel.py` 신규 `[L]` — `4cb89da`
- [x] **P2-A2** `schemas/remodel_report.schema.json` 필드 정의 `[M]` — `4cb89da`
- [x] **P2-A3** `EvolverState.phase_number` + `phase_history` `[S]` — `4cb89da`
- [x] **P2-A4** `state/phase_{N}/` 스냅샷 로직 `[M]` — `4cb89da`

### P2-B. Graph/orchestrator 통합
- [x] **P2-B1** `graph.py` critique→audit→remodel→hitl_r→phase_bump 경로 `[M]` — `83f4f52`
- [x] **P2-B2** `hitl_gate.py` HITL-R 핸들러 완성 `[M]` — `83f4f52`
- [x] **P2-B3** `orchestrator.py` phase transition 핸들러 `[M]` — `83f4f52`
- [x] **P2-B4** Rejection/rollback path `[M]` — `83f4f52`

### P2-C. 검증
- [x] **P2-C1** merge 시나리오 테스트 `[S]` — `b97e287`
- [x] **P2-C2** split 시나리오 테스트 `[S]` — `b97e287`
- [x] **P2-C3** reclassify 시나리오 테스트 `[S]` — `b97e287`
- [x] **P2-C4** rollback 시나리오 테스트 `[S]` — `b97e287`
- [x] **P2-C5** S7 trigger 경로 테스트 `[M]` — `b97e287`
- [x] **P2-C6** schema 양방향 테스트 `[S]` — `b97e287`

---

## Phase P3: Acquisition Expansion ~~(22 tasks)~~ **REVOKED (D-120, 2026-04-13)**

> **상태**: LLM parse 경로 미검증, 실 벤치 0 claims → 전면 폐기 → **SI-P3R** 로 대체
> **원래 목표**: SEARCH/FETCH/PARSE 3단계 분리, provider 플러그인 3개, provenance, 비용 가드
> **후속**: P3R Snippet-First Refactor ✅ (8/8, Gate PASS)

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

## Phase P4: Coverage Intelligence (42 tasks: A~D Complete 17/17 · Stage E 23/25, VP4 FAIL 진단)

> **목표**: Internal Foundation (A~D) — novelty/coverage_map/reason_code/Gini/Smart category addition + External Anchor (E) — history-aware external_novelty + universe_probe + reach_ledger + exploration_pivot
> **Gate**: Stage A~D PASS (669 tests), Stage E VP4 FAIL (793 tests, D-147~D-150)
> **Dev-docs**: `dev/active/phase-si-p4-coverage/`
> **배경**: `mission-alignment-critique.md`, `mission-alignment-opinion.md`, `external-anchor-improvement-plan.md`

### P4-A. Metrics Primitives + Gini 통합 ✅
- [x] **P4-A1** `novelty.py` (Jaccard/token/entity overlap) `[M]` — `5e9d422`
- [x] **P4-A2** `coverage_map.py` (axis/bucket/deficit + Gini tracking) `[M]` — `5e9d422`
- [x] **P4-A3** `EvolverState` novelty/coverage 채움 로직 (orchestrator) `[S]` — `5e9d422`
- [x] **P4-A4** `plateau_detector.py` novelty 확장 (< 0.1 × 5c) `[M]` — `5e9d422`
- [x] **P4-A5** Gini → deficit 반영 (가중 0.3) `[M]` — `5e9d422`

### P4-B. Plan/Critique 통합 ✅
- [x] **P4-B1** `plan.py` reason_code enum + 모든 target 코드 부여 `[M]` — `e4f04b4`
- [x] **P4-B2** `critique.py` machine-readable 처방 규칙 `[M]` — `e4f04b4`
- [x] **P4-B3** remodel_pending → plan reason_code 영향 `[S]` — `e4f04b4`
- [x] **P4-B4** Gini 불균형 → plan target 우선순위 `[S]` — `e4f04b4`

### P4-C. Smart Category Addition ✅
- [x] **P4-C1** `remodel.py` category_addition proposal type `[L]` — `ceb7559`
- [x] **P4-C2** 보수적 트리거 (≥5 KU + LLM 판단 + 1/cycle) `[M]` — `ceb7559`
- [x] **P4-C3** HITL-R category_addition 연동 + skeleton 반영 `[M]` — `ceb7559`

### P4-D. 검증 ✅
- [x] **P4-D1** novelty 단위 테스트 `[S]` — `5e9d422`
- [x] **P4-D2** coverage_map + Gini 통합 테스트 `[S]` — `5e9d422`
- [x] **P4-D3** reason_code 생성 테스트 (모든 enum) `[S]` — `e4f04b4`
- [x] **P4-D4** S7 full scenario (plateau → audit → remodel → category) `[M]` — `273b961`
- [x] **P4-D5** category_addition 보수적 조건 테스트 `[S]` — `ceb7559`

### P4-R. Scope Reframe ✅
- [x] **P4-R1** readiness-report.json 에 reframe 근거 + Internal Foundation PASS `[S]`
- [x] **P4-R2** commit: `[si-p4] Scope reframe (D-135)` `[S]`

### P4-E. Stage E: External Anchor (25 tasks: 23/25 완료)

#### E0~E6: Code Complete ✅
- [x] E0-1/E0-2, E1 (4), E2 (5), E3 (4), E4 (3), E5 (2), E6 (3) — `df219e5`~`a4df15d`

#### E7. Validation
- [x] **E7-1** `a4df15d` Synthetic injection 테스트 `[M]`
- [x] **E7-2** `b2aafc5` Stage-E-on/off 15c 비교 bench — VP4 FAIL 2/5 (D-147~D-150) `[M]`
- [x] **E7-3** 비교 리포트 + VP4 fix 방안 (D-147~D-150 해소) `[S]`

#### E8. Stage E Gate ✅
- [x] **E8-1** `a4df15d` `readiness_gate.py` VP4_exploration_reach `[S]`
- [x] **E8-2** VP4 fix 후 재실행 + readiness-report 갱신 `[S]`
- [x] **E8-3** Gate 판정 commit — VP4 4/5 PASS `[S]`

---

## Phase P5: Telemetry Contract & Dashboard (15 tasks)

> **목표**: Telemetry schema v1 + FastAPI 운영 대시보드 (≤ 2000 LOC)
> **Gate**: **PASS** (2026-04-18) — schema 7/7, 100c load 1.49s, stub 0, LOC 986, S10 PASS, operator-guide 184줄, 821 tests
> **제약**: P5-A (telemetry schema) 가 P5-B (UI) **엄격 선행** (D-77)
> **Dev-docs**: `dev/active/phase-si-p5-telemetry-dashboard/` | `readiness-report.md` 완료

### P5-Prep. state.py TypedDict 보완 [Stage A 착수 전 필수]
- [x] **P5-Prep** `src/state.py` EvolverState에 `reach_history`, `probe_history`, `pivot_history` 3 필드 추가 `[S]`

### P5-A. Telemetry 계약
- [x] **P5-A1** `schemas/telemetry.v1.schema.json` 필수 필드 정의 `[M]`
- [x] **P5-A2** `src/obs/__init__.py` + `src/obs/telemetry.py` emitter (jsonl atomic write) `[M]`
- [x] **P5-A3** `orchestrator.py` 노드 경계 emit hook `[M]`
- [x] **P5-A4** 출력 경로 `bench/silver/{domain}/{trial}/telemetry/cycles.jsonl` `[S]`
- [x] **P5-A5** `tests/test_obs/test_telemetry_schema.py` 스키마 계약 테스트 (S10) `[M]`

### P5-B. Dashboard 구현
- [x] **P5-B1** `src/obs/dashboard/__init__.py` + `app.py` FastAPI bootstrap `[M]`
- [x] **P5-B2** `pyproject.toml` extras `[dashboard]` 의존성 `[S]`
- [x] **P5-B3** Views 7종 (overview/timeline/coverage/sources/conflicts/HITL inbox 3탭/remodel) `[L]`
- [x] **P5-B4** Data source: 실제 artifact 연결 `[M]`
- [x] **P5-B5** `docs/operator-guide.md` 작성 (184줄) `[M]`

### P5-C. 검증
- [x] **P5-C1** schema 계약 재검증 `[S]`
- [x] **P5-C2** `tests/test_obs/test_dashboard_load.py` 100-cycle fixture load 1.49s ≤ 10s `[M]`
- [x] **P5-C3** Self-test "slowdown" walkthrough `[M]`
- [x] **P5-C4** LOC 하드 리밋 측정: 986 ≤ 2,000 `[S]`

---

## Phase P6: Consolidation & Knowledge DB Release (착수 예정)

> **목표**: KU saturation 해소 + Performance 최적화 + japan-travel KB 외부 패키징
> **순서**: P6-A (Pain Point) → P6-B (Performance) → P6-C (KB Release)
> **Gate**: P6-A F-Gate (A12 50c 선행): 15c rerun Remodel ≥ 2회 + Pivot ≥ 1회 실발동, forecast c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회 (conf ≥ 0.6) / P6-A Gate: 50c rerun KU ≥ 250, gap_resolution ≥ 0.85 / P6-C: 외부 import e2e PASS
> **Dev-docs**: `dev/active/phase-si-p6-consolidation/`

### P6-A. Pain Point Resolution (Inside + Outside + Forecastability)

**Inside — Core Loop (KU sustained growth)**:
- [ ] **P6-A1** KU saturation 진단 — c11-15 정체 root cause + gap_map delta=0 cycle 수 측정 `[M]`
- [ ] **P6-A2** Plateau-driven re-seed — plateau 감지 시 LLM-driven new seed pack `[M]`
- [ ] **P6-A3** Field 다양화 강화 — 같은 entity_key 내 미충족 field 우선 GU 생성 `[M]`
- [ ] **P6-A4** Active KU 재해소 — disputed/stale KU → GU 재투입 `[M]`

**Outside — Stage E 보강**:
- [ ] **P6-A5** Universe probe slug 정규화 + 유사도 필터 (D-151, collision_active 반복 방지) `[M]`
- [ ] **P6-A6** Probe accept rate 튜닝 — 15c에 1개 → 5c당 1개 목표 `[S]`

**Forecastability — 메커니즘 발동 보장 (D-158 신규)**:
- [ ] **P6-A7** Smart Remodel 임계값 config 외부화 (`SmartRemodelConfig`, `src/orchestrator.py:454-503`) `[S]`
- [ ] **P6-A8** Exploration Pivot 임계값 config 외부화 (`ExternalAnchorConfig.novelty_*`, `src/nodes/exploration_pivot.py:25-26`) `[S]`
- [ ] **P6-A9** Pivot 발동 조건 단위 테스트 확장 — 15c 내 시나리오 5+ (synthetic `_stagnant_state` 패턴 재사용) `[S]`
- [ ] **P6-A10** Trigger telemetry 구조화 (`trigger_event` optional 필드 emit — Remodel/Pivot 발동 로그 JSON화) `[M]`
- [ ] **P6-A11** **F-Gate 판정** — stage-e-on 15c rerun (~$1) + forecast (선형/지수 projection + damping + bootstrap confidence) → Remodel ≥ 2회 + Pivot ≥ 1회 실발동 + forecast c16-c50 Remodel ≥ 4회 + Pivot ≥ 2회 + conf ≥ 0.6. 미달 시 A2~A6 재설계 루프 `[M]`

**검증 (P6-A gate, F-Gate PASS 이후)**:
- [ ] **P6-A12** stage-e-on-50c trial 생성 + 실행 → KU ≥ 250, gap_resolution ≥ 0.85. trial card에 forecast 예측 기입 `[L]`
- [ ] **P6-A13** COMPARISON-v2.md 작성 + forecast vs 실측 오차 분석 `[S]`

### P6-B. Performance Optimization

- [ ] **P6-B1** LLM 호출 batch (Claim별 단발 → 배치) `[M]`
- [ ] **P6-B2** state_io 증분 저장 (매 cycle 전체 rewrite → delta write) `[M]`
- [ ] **P6-B3** cycle wall_clock 측정 + 목표 설정 `[S]`

### P6-C. Knowledge DB Release

- [ ] **P6-C1** japan-travel state → external-consumable schema (read-only) `[M]`
- [ ] **P6-C2** 외부 프로젝트 import 가능 packaging (`evolver-kb-japan-travel`) `[M]`
- [ ] **P6-C3** minimal query API or static export (KU lookup, GU enumeration) `[M]`
- [ ] **P6-C4** Operator guide "외부 사용자용" 섹션 추가 `[S]`

---

## Phase M1: Multi-Domain Validation (suspended, 7 tasks)

> **상태**: P6 완료 후 별도 trigger 시 활성화 (D-135)
> **목표**: 2차 도메인 Smoke + framework-vs-domain delta memo
> **Gate**: 10 cycle Gate #5 동등 (VP1 ≥ 4/5, VP2 ≥ 5/6, VP3 ≥ 4/6), framework 수정 ≤ 5, 한글 에러 0, S11 pass
> **Dev-docs**: `dev/active/phase-m1-multidomain/` (phase-si-p6-multidomain 에서 rename)

### M1-A. 도메인 선정
- [ ] **M1-A1** 후보 3 개 중 1 개 선택 `[S]`
- [ ] **M1-A2** `trial-card.md` 선정 rationale `[S]`
- [ ] **M1-A3** skeleton + seed pack 작성 `[M]`

### M1-B. Smoke validation
- [ ] **M1-B1** 10 cycle smoke run `[L]`
- [ ] **M1-B2** Readiness report (Gate #5 동등) `[M]`
- [ ] **M1-B3** Framework-vs-domain delta memo (≤ 5건) `[M]`

### M1-C. 검증 파일
- [ ] **M1-C1** `test_multidomain/test_smoke_run.py` (S11) `[M]`

---

## Phase Gap-Res Investigation (12 tasks)

> **목표**: SI-P3R Gate PASS 후 발견된 gap_resolution 병목 (0.517@15c, Bronze P5 0.909 대비) 원인 특정 + 수정
> **Gate**: gap_resolution ≥ 0.85@15c, LLM 비용 ≤ baseline × 2.5, 608 테스트 유지
> **상세**: `dev/active/phase-gap-resolution-investigation/` (plan/context/tasks/debug-history)

### Stage A. 진단 로깅 + 기존 데이터 재분석
- [x] **GR-A1** `collect.py` parse_yield 로깅 `[S]`
- [x] **GR-A2** `integrate.py` integration_result 분포 로깅 `[S]`
- [x] **GR-A3** 기존 15c trial 정적 분석 스크립트 `[M]`

### Stage B. Primary Fix (target_count cap 제거, D-129)
- [x] **GR-B1** `mode.py` target_count cap 제거 (Phase 5 복원) `[S]` — `2a01197`
- [x] **GR-B2** `test_mode.py` target_count 공식 테스트 갱신 `[S]`
- [x] **GR-B3** 영향 받는 테스트 수정 `[M]`

### Stage C. 재현 Trial + 효과 검증
- [x] **GR-C1** gap-res-fix-trial 생성 + 실행 `[M]` — gap_resolution 0.517→0.99
- [x] **GR-C2** trajectory before/after 비교 `[M]`
- [x] **GR-C3** readiness-report 작성 `[S]`

### Stage D. Secondary 대응 결정
- [x] **GR-D1** B2 가설 H1~H4 확증 `[S]` — H1/H3 기각 (D-130)
- [x] **GR-D2** Secondary 수정안 결정 `[S]` — 추가 fix 불필요 (D-130)
- [x] **GR-D3** Decision 문서화 + Phase 종결 (D-129~D-131) `[S]`

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
