# Phase 1 Plan — LangGraph Core Pipeline
> Last Updated: 2026-03-05
> Status: ✅ Complete

## 1. Summary (개요)

Phase 0~0C에서 수동 검증된 Inner Loop(Seed → Plan → Collect → Integrate → Critique → Plan Modify)를 LangGraph 기반 자동화 파이프라인으로 구현한다.

**목적**: 수동으로 3 Cycle(C0~C2) 실행한 프레임워크를 코드로 옮겨 자동 반복 가능한 Evolver 완성.
**범위**: EvolverState 타입 + 유틸리티(I/O, Schema, Metrics) + 8개 노드 + StateGraph 빌드 + 단위 테스트.
**예상 산출물**: `src/` 디렉토리에 실행 가능한 LangGraph 파이프라인.

---

## 2. Current State (현재 상태)

### Phase 0C 완료 시점의 자산

| 자산 | 상태 | 위치 |
|------|------|------|
| JSON Schema 4종 (KU/EU/GU/PU) | 확정 | `schemas/` |
| 6대 Deliverable 템플릿 | 확정 | `templates/` |
| Metrics 6개 공식 + 건강 임계치 | 확정 | `docs/design-v2.md` §4 |
| Critique→Plan 컴파일 6규칙 | 확정 | `docs/design-v2.md` §5 |
| 5대 불변원칙 + 자동 검증 방법 | 확정 | `docs/design-v2.md` §8 |
| LangGraph 노드/엣지 설계 | 초안 | `docs/design-v2.md` §10 |
| EvolverState 타입 | 초안 (TypedDict) | `docs/design-v2.md` §10 |
| Bootstrap 알고리즘 | 확정 | `docs/gu-bootstrap-spec.md` §1 |
| Axis Coverage Matrix | 확정 | `docs/gu-bootstrap-spec.md` §2.5 |
| Jump Mode trigger/guardrail | 확정 (v1.0) | `docs/gu-bootstrap-expansion-policy.md` |
| Entity Hierarchy 규칙 | 확정 | `docs/gu-bootstrap-expansion-policy.md` §7 |
| 벤치 데이터 (C0~C2) | 3 Cycle 수동 실행 완료 | `bench/japan-travel/` |

### Phase 1 입력 조건 체크리스트 (design-v2 §12 — 11항 전체 ✅)

모든 전제 조건 충족. Phase 1 진입 가능.

---

## 3. Target State (목표 상태)

Phase 1 완료 시:
- `src/` 에 LangGraph 기반 Evolver 파이프라인 코드
- `python -m pytest` 로 전 노드 + 그래프 단위 테스트 통과
- japan-travel 벤치에서 단일 Cycle 자동 실행 가능 (Graph invoke)
- Normal/Jump Mode 조건부 분기 작동
- HITL Gate(interrupt) 동작 확인
- 5대 불변원칙 자동 검증 코드 포함

---

## 4. Implementation Stages

### Stage A: 기반 구축 (State, I/O, Schema 검증)

**목적**: 모든 노드가 공유하는 기반 인프라 구축.

| Task | 내용 | Size |
|------|------|------|
| 1.1 | 프로젝트 초기화 (pyproject.toml, 의존성, src/ 구조) | S |
| 1.2 | EvolverState 타입 정의 (`src/state.py`) | M |
| 1.3 | JSON 파일 I/O 유틸리티 (`src/utils/state_io.py`) | M |
| 1.4 | Schema 검증 유틸리티 (`src/utils/schema_validator.py`) | M |
| 1.5 | Metrics 계산 유틸리티 (`src/utils/metrics.py`) | M |

**의존성**: 없음 (독립 시작)
**완료 조건**: State 로드/저장 + Schema 검증 + Metrics 계산이 bench 데이터로 동작

### Stage B: 노드 구현

**목적**: Inner Loop 6단계 + mode_node + hitl_gate 구현.

| Task | 내용 | Size | 의존 |
|------|------|------|------|
| 1.6 | seed_node — Seed Pack → State 초기화, Bootstrap GU 생성 | L | A |
| 1.7 | mode_node — Normal/Jump Mode 판정, budget 배분 | L | A |
| 1.8 | plan_node — Gap Map → Collection Plan (LLM) | L | A, 1.7 |
| 1.9 | collect_node — Plan → Claims 수집 (WebSearch/WebFetch + LLM) | XL | A |
| 1.10 | integrate_node — Claims → KB Patch (LLM + I/O), 동적 GU, Entity Hierarchy | XL | A, 1.4 |
| 1.11 | critique_node — State → Critique Report (LLM + Metrics), Axis Coverage | L | A, 1.5 |
| 1.12 | plan_modify_node — Critique → Revised Plan (LLM) | L | A |
| 1.13 | hitl_gate_node — LangGraph interrupt 기반 HITL (Gate A~E) | M | A |

**의존성**: Stage A 완료 필수
**완료 조건**: 각 노드가 bench 데이터 입력으로 독립 실행 가능 + 단위 테스트 통과

### Stage C: Graph 빌드 + 테스트

**목적**: 노드를 StateGraph로 조립, 전체 흐름 작동 확인.

| Task | 내용 | Size | 의존 |
|------|------|------|------|
| 1.14 | StateGraph 빌드 (`src/graph.py`) — 노드 등록 + 엣지 연결 | L | B |
| 1.15 | 엣지 라우팅 로직 — 조건부 엣지 (종료, HITL, Jump/Normal, Outer Loop) | L | 1.14 |
| 1.16 | 단위 테스트 — 각 노드 + 전체 그래프 (mock LLM) | M | 1.14, 1.15 |

**의존성**: Stage B 완료 필수
**완료 조건**: `python -m pytest` 전체 통과, Graph가 단일 Cycle 실행 가능

---

## 5. Task Breakdown

| # | Task | Stage | Size | 의존 | Status |
|---|------|-------|------|------|--------|
| 1.1 | 프로젝트 초기화 | A | S | — | ✅ `4c9d793` |
| 1.2 | EvolverState 타입 정의 | A | M | 1.1 | ✅ `4c9d793` |
| 1.3 | JSON 파일 I/O 유틸리티 | A | M | 1.1 | ✅ `4c9d793` |
| 1.4 | Schema 검증 유틸리티 | A | M | 1.1 | ✅ `4c9d793` |
| 1.5 | Metrics 계산 유틸리티 | A | M | 1.1 | ✅ `4c9d793` |
| 1.6 | seed_node | B | L | A | ✅ `0be8221` |
| 1.7 | mode_node | B | L | A | ✅ `0be8221` |
| 1.8 | plan_node | B | L | A, 1.7 | ✅ `0be8221` |
| 1.9 | collect_node | B | XL | A | ✅ `0be8221` |
| 1.10 | integrate_node | B | XL | A, 1.4 | ✅ `0be8221` |
| 1.11 | critique_node | B | L | A, 1.5 | ✅ `0be8221` |
| 1.12 | plan_modify_node | B | L | A | ✅ `0be8221` |
| 1.13 | hitl_gate_node | B | M | A | ✅ `0be8221` |
| 1.14 | StateGraph 빌드 | C | L | B | ✅ |
| 1.15 | 엣지 라우팅 로직 | C | L | 1.14 | ✅ |
| 1.16 | 단위 테스트 | C | M | 1.14, 1.15 | ✅ |

**Size 분포**: S:1, M:6, L:7, XL:2 (총 16개)

---

## 6. Risks & Mitigation

| 리스크 | 심각도 | 완화 전략 |
|--------|--------|-----------|
| LLM 토큰 비용 폭발 (collect/integrate 노드) | High | Budget/Stop Rule 강제, mock LLM으로 개발/테스트 |
| WebSearch/WebFetch API 불안정 | Medium | 재시도 로직, 캐시, fallback 출처 |
| LangGraph interrupt 동작 차이 | Medium | 공식 문서 기반 구현, 작은 예제로 선행 검증 |
| State 타입과 JSON Schema 불일치 | Medium | Pydantic 모델 + JSON Schema 양방향 검증 |
| Windows 인코딩 문제 (한글 JSON) | Medium | utf-8 명시, PYTHONUTF8=1 강제 |
| design-v2 설계와 실제 구현 간 간극 | Low | Stage A에서 타입 정의 시 design-v2와 1:1 대조 |

---

## 7. Dependencies

### 내부 의존성

| 모듈 | 의존 대상 |
|------|-----------|
| 모든 노드 | EvolverState (`src/state.py`), I/O (`src/utils/state_io.py`) |
| seed_node | Bootstrap 알고리즘 (gu-bootstrap-spec §1) |
| mode_node | Axis Coverage Matrix, Jump Mode trigger (expansion-policy v1.0) |
| plan_node | mode_node 출력 (Mode + budget) |
| integrate_node | Schema 검증 (`src/utils/schema_validator.py`), Entity Hierarchy |
| critique_node | Metrics 계산 (`src/utils/metrics.py`), Axis Coverage |
| Graph 빌드 | 모든 노드 |

### 외부 의존성 (Python 패키지)

| 패키지 | 용도 | 비고 |
|--------|------|------|
| langgraph | StateGraph, 엣지 라우팅, interrupt | 핵심 |
| langchain-core | BaseTool, LLM 인터페이스 | LangGraph 의존 |
| langchain-anthropic | ChatAnthropic (Claude) | LLM 호출 |
| jsonschema | JSON Schema Draft 2020-12 검증 | Schema 정합성 |
| pydantic | 타입 정의 (EvolverState 강화) | TypedDict → Pydantic 모델 |
| pytest | 테스트 프레임워크 | 개발 의존 |

---

## 8. 디렉토리 구조 (계획)

```
src/
├── __init__.py
├── state.py                    # EvolverState, 타입 정의
├── graph.py                    # StateGraph 빌드, 엣지 라우팅
├── nodes/
│   ├── __init__.py
│   ├── seed.py                 # seed_node
│   ├── mode.py                 # mode_node (Normal/Jump 판정)
│   ├── plan.py                 # plan_node
│   ├── collect.py              # collect_node
│   ├── integrate.py            # integrate_node
│   ├── critique.py             # critique_node
│   ├── plan_modify.py          # plan_modify_node
│   └── hitl_gate.py            # hitl_gate_node
├── utils/
│   ├── __init__.py
│   ├── state_io.py             # JSON 파일 I/O (load/save)
│   ├── schema_validator.py     # JSON Schema 검증
│   └── metrics.py              # Metrics 6개 공식 + 건강 판정
└── tools/
    ├── __init__.py
    └── search.py               # WebSearch/WebFetch 도구 래퍼
tests/
├── __init__.py
├── test_state.py
├── test_state_io.py
├── test_schema_validator.py
├── test_metrics.py
├── test_nodes/
│   ├── test_seed.py
│   ├── test_mode.py
│   ├── test_plan.py
│   ├── ...
│   └── test_hitl_gate.py
└── test_graph.py
```
