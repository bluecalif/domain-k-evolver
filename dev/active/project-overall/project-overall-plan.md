# Project Overall Plan
> Last Updated: 2026-03-04 (Phase 0C 삽입 — GU 전략 재검토)
> Status: In Progress

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
- JSON Schema 4종 확정 (KU, EU, GU, PU) → `schemas/`
- 6대 Deliverable 템플릿 확정 → `templates/`
- Metrics 6개 공식 + 건강 지표 임계치 확정
- 5대 불변원칙 + 자동 검증 방법 확정 (Conflict-preserving 실전 검증 포함)
- Critique→Plan 컴파일 6개 규칙 확정
- LangGraph 노드/엣지 설계 초안 완성 (design-v2.md §10)
- Claude Code 인프라 구축: CLAUDE.md, commands(3), hooks(1), skills(2)
- GU Bootstrap 명세 공식화 완료 → `docs/gu-bootstrap-spec.md`
- GU Expansion Policy 제안 → `docs/gu-bootstrap-expansion-policy.md` (v0.1 제안)

### 자산
```
schemas/          — 4종 JSON Schema (확정)
templates/        — 6대 Deliverable MD 템플릿 (확정)
bench/japan-travel/
  state/          — 5개 State JSON (Cycle 1 결과)
  cycle-0/        — 6개 Deliverable (수동 실행 결과)
  cycle-1/        — 5개 Deliverable (수동 실행 결과)
  state-snapshots/ — Cycle 0 스냅샷
docs/             — draft.md, design-v2.md, gu-bootstrap-spec.md, gu-bootstrap-expansion-policy.md
.claude/          — commands, hooks, skills (개발 인프라)
```

---

## 3. Target State (목표 상태)

프로젝트 완료 시:
- LangGraph 기반 자동 Inner Loop 동작 (Seed → Plan → Collect → Integrate → Critique → PM)
- HITL Gate A/B 작동 (LangGraph interrupt)
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

### Phase 0C: GU 전략 재검토 🔜 Next
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

### Phase 1: LangGraph Core Pipeline
- **전제**: Phase 0C 완료 (확정된 GU 전략 정책 + Axis Coverage Matrix 로직 포함)
- EvolverState 타입 정의 (axis coverage 포함)
- 6+1 노드 구현 (seed, plan, collect, integrate, critique, plan_modify, hitl_gate)
- plan_node에 explore/exploit budget 반영
- critique_node에 Structural Deficit Analysis 반영
- StateGraph 빌드 + 엣지 라우팅 (Jump Mode 조건부 분기 포함)
- JSON 파일 I/O 유틸리티
- Schema 검증 유틸리티
- Metrics 계산 유틸리티

### Phase 2: Bench Integration & Validation
- japan-travel 벤치 데이터 연결
- Cycle 1 자동 실행 + 결과 검증
- 5대 불변원칙 자동 검증 파이프라인
- HITL Gate 실전 테스트
- Metrics 임계치 기반 경고/중단 로직

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
| Phase 0C | A: 축 선언 + Matrix 계산 | M | 2 | 🔜 Next |
| Phase 0C | B: Cycle 2 Jump Mode 테스트 | L | 2 | |
| Phase 0C | C: 정책 확정 + 문서 통합 | M | 2 | |
| Phase 1 | A: 기반 (State, I/O, Schema) | M~L | 5 | |
| Phase 1 | B: 노드 구현 | L~XL | 7 | |
| Phase 1 | C: Graph 빌드 | M | 3 | |
| Phase 2 | A: 벤치 연결 | M | 3 | |
| Phase 2 | B: 검증 파이프라인 | M~L | 4 | |
| Phase 3 | A: 다중 도메인 | L | 3 | |
| Phase 3 | B: Outer Loop + 안정성 | L~XL | 4 | |
| **총계** | | | **40** | |

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
| langchain-anthropic | ChatAnthropic (Claude) | LLM 호출 |
| jsonschema | JSON Schema Draft 2020-12 검증 | Schema 정합성 |
| pydantic | 타입 정의 (선택) | EvolverState 보강 시 |
