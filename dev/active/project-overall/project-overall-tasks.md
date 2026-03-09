# Project Overall Tasks
> Last Updated: 2026-03-08 (Phase 5 Stage D)
> Status: In Progress — Phase 5 Stage D (GU Resolve Rate 개선)

## Summary

| Phase | Total | S | M | L | XL | Done |
|-------|-------|---|---|---|----|----|
| Phase 0 | — | — | — | — | — | ✅ Complete |
| Phase 0B | 5 | 1 | 2 | 2 | 0 | ✅ Complete (5/5) |
| Phase 0C | 6 | 0 | 3 | 2 | 1 | ✅ Complete (6/6) |
| Phase 1 | 15 | 2 | 5 | 6 | 2 | ✅ Complete (15/15) |
| Phase 2 | 16 | 5 | 8 | 3 | 0 | ✅ Complete (16/16) |
| Phase 3 | 9 | 1 | 5 | 3 | 0 | ✅ Complete (9/9) |
| Phase 4 | 11 | 0 | 7 | 4 | 0 | ✅ Complete (11/11, Gate FAIL) |
| Phase 5 | 13 | 3 | 7 | 3 | 0 | 10/13 |
| **총계** | **75** | — | — | — | — | **72/75** |

---

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

### Stage A: 축 선언 + Axis Coverage Matrix

- [x] **0C.1** 축 선언 보완 — skeleton axes 4축 추가 (category/geography/condition/risk)
- [x] **0C.2** Axis Coverage Matrix 첫 계산 — geography deficit 0.200, risk deficit 0.200

### Stage B: Cycle 2 Jump Mode 수동 테스트

- [x] **0C.3** Cycle 2 준비 — T1 발동 → Jump Mode, jump_cap=10, explore 5 + exploit 3
- [x] **0C.4** Cycle 2 수동 실행 — KU 7추가, GU 3해결 + 6신규, geography deficit 해소 → `c338351`

### Stage C: 정책 확정 + 문서 통합

- [x] **0C.5** 정책 확정 — expansion-policy v1.0 (trigger 임계치 + explore 비율 확정)
- [x] **0C.6** 설계 문서 통합 — design-v2 mode_node/entity hierarchy, spec v1.1, Phase 1 입력 체크리스트 11항 ✅

---

## Phase 1: LangGraph Core Pipeline ✅

> **완료**: 2026-03-05 | 191 tests passed, Graph 단일 Cycle stream 실행 성공
> **결과**: src/ 16파일 + tests/ 10파일, 8노드 + 5 HITL Gate + cycle_inc = 14 노드 StateGraph

### Stage A: 기반 구축 (State, I/O, Schema 검증)

- [x] **1.1** 프로젝트 초기화 — pyproject.toml, 의존성, 디렉토리 구조 → `4c9d793`
- [x] **1.2** EvolverState 타입 정의 — `src/state.py` → `4c9d793`
- [x] **1.3** JSON 파일 I/O 유틸리티 — `src/utils/state_io.py` → `4c9d793`
- [x] **1.4** Schema 검증 유틸리티 — `src/utils/schema_validator.py` → `4c9d793`
- [x] **1.5** Metrics 계산 유틸리티 — `src/utils/metrics.py` → `4c9d793`

### Stage B: 노드 구현

- [x] **1.6** seed_node — Seed Pack → State 초기화 → `0be8221`
- [x] **1.7** plan_node — Gap Map → Collection Plan 생성 → `0be8221`
- [x] **1.8** collect_node — Plan → Claims 수집 → `0be8221`
- [x] **1.9** integrate_node — Claims → KB Patch 적용 → `0be8221`
- [x] **1.10** critique_node — State → Critique Report → `0be8221`
- [x] **1.11** plan_modify_node — Critique → Revised Plan → `0be8221`
- [x] **1.12** hitl_gate_node — LangGraph interrupt 기반 HITL → `0be8221`

### Stage C: Graph 빌드

- [x] **1.13** StateGraph 빌드 — `src/graph.py` (13노드 등록 + 엣지)
- [x] **1.14** 엣지 라우팅 로직 — 조건부 엣지 4개 (mode/collect/integrate/critique)
- [x] **1.15** 단위 테스트 — 36 tests (빌드 + 라우팅 + stream 통합 + 불변원칙)

---

## Phase 2: Bench Integration & Real Self-Evolution

> **목표**: 10+ 사이클 자동 실행, 자기확장 품질 향상 검증, 전체 자동화
> **기술 스택**: OpenAI gpt-4.1-mini (LLM) + Tavily Search (검색)
> **재설계**: 25-task 4-Stage Mock 위주 → 16-task 3-Stage Real API First (D-34, D-35)

### Stage A': Smoke Test → Real 1 Cycle (5 tasks) ✅

> Gate: Real API 1사이클 완주 + KU 1개 이상 추가 → **PASSED**

- [x] **2.1** API 키 검증 + Smoke Test `[S]`
- [x] **2.2** LLM 응답 파싱 강화 `[M]`
- [x] **2.3** collect_node 프롬프트 정교화 `[M]`
- [x] **2.4** Orchestrator 정합성 수정 `[M]`
- [x] **2.5** Real API 1 Cycle 실행 `[L]` ★★★

### Stage B': 안정화 + 3 Cycle (6 tasks) ✅

> Gate: 3사이클 연속 에러 없이 완주 + 불변원칙 위반 0건 → **PASSED**

- [x] **2.6** 에러 핸들링 + Rate Limiting `[M]`
- [x] **2.7** seed 일반화 + cycle>1 스킵 `[S]`
- [x] **2.8** plan_modify 실효성 + C3 수정 `[M]`
- [x] **2.9** 불변원칙 자동검증 `[S]`
- [x] **2.10** 비용/토큰 로깅 `[M]`
- [x] **2.11** Real API 3 Cycle 실행 `[L]` ★★

### Stage C': 10+ Cycle 자동화 (5 tasks) ✅

> Gate: 10사이클 완주 + 결과 분석 리포트 → **PASSED**

- [x] **2.12** Plateau Detection + 자동 종료 `[M]`
- [x] **2.13** Metrics Guard `[S]`
- [x] **2.14** 10 Cycle Real 실행 `[L]` ★
- [x] **2.15** Bench Run CLI 정비 `[S]`
- [x] **2.16** 결과 분석 + Snapshot Diff `[M]`

---

## Phase 3: Cycle Quality Remodeling ✅

> **완료**: 2026-03-06 | 301 tests passed, 9/9 tasks
> **결과**: Active KU 31→77 (+148%), Disputed 54→0, conflict_rate 0.635→0.000, 성장률 14.3x
> **보고서**: `docs/phase3-analysis.md`

### Stage A: Semantic Conflict Detection (R1) ✅

- [x] **3.1** `_detect_conflict()` LLM semantic 비교로 교체 → `6e27a65`
- [x] **3.2** 충돌 판정 테스트 + FP rate 측정 → Stage A 10 Cycle 검증
- [x] **3.3** 10 Cycle 재실행으로 FP 감소 확인 → conflict_rate 0.234

### Stage B: Dispute Resolution (R2~R4) ✅

- [x] **3.4** dispute resolution mechanism 설계 + 구현 → `c45b089`
- [x] **3.5** disputed→active 전환 경로 → `c45b089`
- [x] **3.6** critique 노드에 dispute resolution workflow 추가 → `c45b089`

### Stage C: 수렴 개선 + 재검증 (R5~R6) ✅

- [x] **3.7** 수렴 조건 C6: conflict_rate < 0.15 상한 → `9a3c5f2`
- [x] **3.8** early stopping 개선 (plateau + conflict_rate 복합 조건) → `9a3c5f2`
- [x] **3.9** 최종 10 Cycle 실행 + Phase 2 대비 개선 효과 보고 → `9a3c5f2`

---

## Phase 4: Self-Governing Evolver ✅

> **완료**: 2026-03-07 | 420 tests passed, 11/11 tasks, Gate FAIL (VP1/VP2)
> **보고서**: `docs/phase4-readiness-report.md`

### Stage A: Outer Loop Audit ✅

- [x] **4.1** Executive Audit 프레임워크 구현 `[L]` — `cebd47e`
- [x] **4.2** 다축 교차 커버리지 진단 `[M]` — `cebd47e`
- [x] **4.3** KU Yield/Cost 효율 분석 `[M]` — `cebd47e`

### Stage B: Policy Evolution ✅

- [x] **4.4** Policy 스키마 + 버전 관리 `[M]` — `816fb2d`
- [x] **4.5** Audit → Policy 자동 수정 경로 `[L]` — `816fb2d`
- [x] **4.6** Source Credibility 학습 `[M]` — `816fb2d`

### Stage C: Strategic Self-Tuning ✅

- [x] **4.7** Explore/Exploit 비율 자동 조정 `[L]` — `31ef46d`
- [x] **4.8** Jump Trigger 동적 관리 `[M]` — `31ef46d`
- [x] **4.9** Convergence 조건 고도화 `[M]` — `31ef46d`

### Stage D: Evolver Readiness Gate ✅ (FAIL)

- [x] **4.10** Readiness 벤치마크 실행 `[L]` — `62915de`
- [x] **4.11** 3-Viewpoint Readiness 판정 `[M]` — `62915de`

---

## Phase 5: Inner Loop Quality

> **목표**: Phase 4 Gate FAIL의 Inner Loop 품질 문제 해결 → Gate 재실행 PASS
> **상세**: `dev/active/phase5-inner-loop-quality/`
> **테스트**: 437 tests passed

### 선행: Gate 메트릭 수정 ✅

- [x] **5.0** VP1-R1 Shannon Entropy → Gini Coefficient 교체 `[S]`

### Stage A: Geography Axis-Tags 전파 ✅

- [x] **5.1** Integrate: GU→KU axis_tags 전파 `[M]`
- [x] **5.2** Integrate: KU 내용 기반 geography 추론 `[M]`
- [x] **5.3** Integrate/Plan: 동적 GU 생성 시 geography 부여 `[M]`
- [x] **5.4** Readiness Gate: blind_spot KU 기반 개선 `[S]`

### Stage B: Staleness 자동갱신 ✅

- [x] **5.5** Critique: Stale KU → Refresh GU 자동생성 `[L]` (D-55)
- [x] **5.6** Integrate: Refresh 통합 시 KU 갱신 `[M]`

### Stage C: Category 균형 + Field 다양성 ✅

- [x] **5.7** Critique: 소수 카테고리 균형 GU 생성 `[M]` (D-56)
- [x] **5.8** Integrate: Field 다양성 억제 `[M]`

### Stage D: GU Resolve Rate 개선 + bench 정리

- [ ] **5.10a** bench/ 정리 — 더블 서픽스 버그 수정 + 아티팩트 삭제 `[S]` (D-61)
- [ ] **5.10b** Mode: target_count/cap 하드캡 제거 — 비례 스케일 `[M]` (D-60)

### 검증: Gate 재실행

- [x] **5.9** Gate 재실행 #1 `[L]` — **FAIL** (VP1 3/5, VP2 2/6, VP3 5/6)
- [ ] **5.11** Gate 재실행 #2 `[L]` — 5 cycle 검증 → 15 cycle 풀
