# Project Overall Plan
> Last Updated: 2026-03-05 (Phase 2 Stage A'+B' 완료)
> Status: In Progress — Phase 2 Stage C' 진행 예정

## 1. Summary (개요)

Domain-K-Evolver — 도메인 불문 자기확장 지식 Evolver 프레임워크.
부분적으로 알려진 지식에서 시작해 Gap-driven 계획 → 수집 → 통합 → 비평 → 계획수정 루프를 반복하며 지식을 자동 확장.

**목표**: draft.md의 설계를 LangGraph 기반 자동화 파이프라인으로 구현하여 실제 동작하는 Evolver 완성.

**범위**: Cycle 0 수동 검증(완료) → Cycle 1 수동 검증(완료) → GU 전략 재검토(Phase 0C) → LangGraph 자동화 → 벤치 검증 → 다중 도메인 확장.

---

## 2. Current State (현재 상태)

### 완료된 항목
- Cycle 0 수동 실행 완료 (japan-travel 벤치): KU 13, EU 18, Gap 21 open / 7 resolved
- Cycle 1 수동 실행 완료: KU 21 (active 19 + disputed 2), EU 33, Gap 16 open / 15 resolved
- Cycle 2 수동 실행 완료 (Jump Mode): KU 28, EU 55, Gap 21 open / 18 resolved
- Axis Coverage Matrix + Jump Mode 실측 검증 완료 (geography deficit 해소)
- expansion-policy v1.0 확정 (trigger 임계치, explore/exploit 비율, guardrail 수치)
- JSON Schema 4종 확정 (KU, EU, GU, PU) → `schemas/`
- 6대 Deliverable 템플릿 확정 → `templates/`
- Metrics 6개 공식 + 건강 지표 임계치 확정
- 5대 불변원칙 + 자동 검증 방법 확정 (Conflict-preserving 실전 검증 포함)
- Critique→Plan 컴파일 6개 규칙 확정
- LangGraph 노드/엣지 설계 초안 완성 (design-v2.md §10)
- Claude Code 인프라 구축: CLAUDE.md, commands(3), hooks(1), skills(5)
- GU Bootstrap 명세 공식화 완료 → `docs/gu-bootstrap-spec.md`
- GU Expansion Policy 확정 → `docs/gu-bootstrap-expansion-policy.md` (v1.0 확정)
- **Phase 1 완료**: LangGraph Core Pipeline — src/ 16파일, tests/ 10파일, 191 tests passed
  - StateGraph 14노드 (8 core + cycle_inc + 5 HITL gate)
  - 조건부 엣지 4개 (mode/collect/integrate/critique)
  - Mock LLM + 결정론적 fallback 기반 단위/통합 테스트
- **Phase 2 Stage A 인프라 코드 작성 완료**: config, adapters, orchestrator, metrics_logger
- **Phase 2 Stage A' 완료**: Real API 1 Cycle 성공 (KU 28→34, +6)
- **Phase 2 Stage B' 완료**: 3 Cycle 연속 성공, 불변원칙 위반 0건, 254 tests
  - KU 28→42, GU resolved 21→32
  - LLM 17 calls (84K tokens), Search 42, Fetch 28

### 자산
```
schemas/          — 4종 JSON Schema (확정)
templates/        — 6대 Deliverable MD 템플릿 (확정)
bench/japan-travel/
  state/          — 5개 State JSON (Cycle 2 결과)
  cycle-0/        — 6개 Deliverable (수동 실행 결과)
  cycle-1/        — 5개 Deliverable (수동 실행 결과)
  state-snapshots/ — Cycle 0, 1 스냅샷
docs/             — draft.md, design-v2.md, gu-bootstrap-spec.md, gu-bootstrap-expansion-policy.md
src/adapters/     — llm_adapter.py, search_adapter.py (Phase 2 인프라)
src/config.py     — 환경 설정 (API 키, 모델명 등)
src/orchestrator.py — 사이클 관리 Orchestrator
src/utils/metrics_logger.py — 사이클별 Metrics 기록
.claude/          — commands, hooks, skills (개발 인프라)
```

---

## 3. Target State (목표 상태)

프로젝트 완료 시:
- LangGraph 기반 자동 Inner Loop 동작 (Seed → Plan → Collect → Integrate → Critique → PM)
- HITL Gate A~E 작동 (LangGraph interrupt)
- japan-travel 벤치에서 Cycle 1+ 자동 실행 성공
- 5대 불변원칙 자동 검증 통과
- 새 도메인에서 Seed Pack만으로 Evolver 가동 가능

---

## 4. Phase 구성

### Phase 0: Cycle 0 수동 검증 ✅ Complete
- 수동으로 전체 Inner Loop 실행
- JSON Schema, Metrics, 불변원칙 검증
- design-v2.md 도출

### Phase 0B: Cycle 1 수동 검증 ✅ Complete
- Conflict-preserving 원칙 실전 검증 성공 (disputed 2건, condition_split + hold)
- 동적 GU 3개 발견 (GU-0029~0031), 상한 이내
- 5대 불변원칙 전체 PASS
- Cycle 1 Deliverables → `bench/japan-travel/cycle-1/`

### Phase 0C: GU 전략 재검토 ✅ Complete
- **목적**: 축(axis) 기반 커버리지 분석 + Quantum Jump 수동 테스트 + 정책 확정
- **근거**: gu-bootstrap-expansion-policy.md (v0.1)의 3가지 구조적 한계 지적
  1. 국소 최적화 편향 — 기존 open GU 주변만 반복 탐색
  2. 초기 스켈레톤 불완전성 — category 축만 관리, geography/condition/risk 축 미추적
  3. 상한 경직성 — 고정 20% 상한은 구조 결손 회복에 느림
- **입력**: Cycle 1 State + gu-bootstrap-expansion-policy.md (v0.1) + revised-plan-c2.md
- **산출물**:
  - japan-travel skeleton에 geography/condition/risk 축 명시 추가
  - Axis Coverage Matrix 첫 계산 (31 GU 다축 분류, 결손 정량화)
  - Cycle 2를 Jump Mode로 수동 실행, trigger/guardrail 검증
  - gu-bootstrap-expansion-policy v0.1 → v1.0 승격 (수치 임계치 확정)
  - design-v2 또는 design-v3로 정책 흡수
- **Phase 1 입력 조건**: Phase 0C 완료 + 확정된 GU 전략 정책

### Phase 1: LangGraph Core Pipeline ✅ Complete
- **완료**: 2026-03-05 | 191 tests passed
- **상세**: `dev/active/phase1-langgraph-core/` 참조
- **Stage A**: 기반 구축 — EvolverState 타입 + I/O + Schema 검증 + Metrics (5/5 ✅)
- **Stage B**: 노드 구현 — seed, mode, plan, collect, integrate, critique, plan_modify, hitl_gate (8/8 ✅)
- **Stage C**: Graph 빌드 — StateGraph + 엣지 라우팅 + 단위 테스트 (3/3 ✅)
- 총 16 tasks 완료 (S:1, M:6, L:7, XL:2)

### Phase 2: Bench Integration & Real Self-Evolution
- **목표**: 10+ 사이클 자동 실행, 자기확장 품질 향상 검증, 전체 자동화
- **기술**: OpenAI gpt-4.1-mini (LLM) + Tavily Search (검색) — D-29, D-30
- **재설계**: 25-task 4-Stage Mock 위주 → **16-task 3-Stage Real API First** (D-34, D-35)
- **Stage A'** (5 tasks, 2.1~2.5): Smoke Test → Real 1 Cycle — API 키 검증, LLM 파싱 강화, 프롬프트 정교화, Orchestrator 정합성, Real 1 Cycle 실행
  - **Gate**: japan-travel Real API 1사이클 완주 + KU 1개 이상 추가
- **Stage B'** (6 tasks, 2.6~2.11): 안정화 + 3 Cycle — 에러 핸들링, seed 일반화, plan_modify 실효성, 불변원칙 자동검증, 비용 로깅, Real 3 Cycle 실행
  - **Gate**: 3사이클 연속 에러 없이 완주 + 불변원칙 위반 0건
- **Stage C'** (5 tasks, 2.12~2.16): 10+ Cycle 자동화 — Plateau Detection, Metrics Guard, Real 10 Cycle 실행, CLI 정비, 결과 분석
  - **Gate**: 10사이클 완주 (또는 plateau 조기 종료) + 결과 분석 리포트
- **진행 방식**: Stage별 세션 분리 — D-33

### Phase 3: Multi-Domain & Robustness
- 새 도메인 Seed Pack 작성 + Evolver 가동
- Outer Loop (Executive Audit + Remodeling) 구현
- 에러 처리 + 복구 메커니즘
- 성능 최적화 (토큰/API 비용)

---

## 5. Task Breakdown (전체)

| Phase | Stage | Size | Task 수 | Status |
|-------|-------|------|---------|--------|
| Phase 0 | Cycle 0 수동 검증 | — | — | ✅ Complete |
| Phase 0B | Cycle 1 수동 검증 | S~L | 5 | ✅ Complete |
| Phase 0C | A~C: 축 선언 + Jump Mode + 정책 확정 | M~XL | 6 | ✅ Complete |
| Phase 1 | A: 기반 (State, I/O, Schema, Metrics) | S~M | 5 | ✅ Complete |
| Phase 1 | B: 노드 구현 (8개: seed~hitl_gate) | M~XL | 8 | ✅ Complete |
| Phase 1 | C: Graph 빌드 + 테스트 | M~L | 3 | ✅ Complete |
| Phase 2 | A': Smoke + 1 Cycle | S~L | 5 | ✅ Complete |
| Phase 2 | B': 안정화 + 3 Cycle | S~L | 6 | ✅ Complete |
| Phase 2 | C': 10+ Cycle 자동화 | S~L | 5 | |
| Phase 3 | A: 다중 도메인 | L | 3 | |
| Phase 3 | B: Outer Loop + 안정성 | L~XL | 4 | |
| **총계** | | | **49** | |

---

## 6. Risks & Mitigation

| 리스크 | 심각도 | 완화 전략 |
|--------|--------|-----------|
| LLM 토큰 비용 폭발 (collect/integrate) | High | Budget/Stop Rule 강제, 작은 벤치 데이터로 검증 |
| WebSearch/WebFetch 신뢰성 | Medium | 재시도 로직, 캐시, fallback 출처 |
| JSON 파일 I/O 동시성 (LangGraph) | Low | 단일 스레드 실행, 파일 락 불필요 |
| Cycle 간 State 불일치 | Medium | Schema 검증 + 불변원칙 자동 체크 매 노드 후 |
| Windows 인코딩 문제 (한글) | Medium | utf-8 명시, PYTHONUTF8=1 강제 |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| 노드 구현 | EvolverState 타입, JSON I/O |
| Graph 빌드 | 모든 노드 |
| 벤치 연결 | Graph + bench/state/ 데이터 |
| 불변원칙 검증 | Metrics 유틸 + Schema 검증 |

### 외부 (Python 패키지)
| 패키지 | 용도 | 비고 |
|--------|------|------|
| langgraph | StateGraph, 엣지 라우팅, interrupt | 핵심 |
| langchain-core | BaseTool, LLM 인터페이스 | LangGraph 의존 |
| langchain-openai | ChatOpenAI (GPT) | LLM 호출 (D-29) |
| tavily-python | TavilySearchResults | 웹 검색 (D-30) |
| jsonschema | JSON Schema Draft 2020-12 검증 | Schema 정합성 |
| pydantic | 타입 정의 (선택) | EvolverState 보강 시 |
