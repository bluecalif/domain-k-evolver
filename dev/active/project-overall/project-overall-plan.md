# Project Overall Plan
> Last Updated: 2026-03-03 (GU Bootstrap 명세 반영)
> Status: In Progress

## 1. Summary (개요)

Domain-K-Evolver — 도메인 불문 자기확장 지식 Evolver 프레임워크.
부분적으로 알려진 지식에서 시작해 Gap-driven 계획 → 수집 → 통합 → 비평 → 계획수정 루프를 반복하며 지식을 자동 확장.

**목표**: draft.md의 설계를 LangGraph 기반 자동화 파이프라인으로 구현하여 실제 동작하는 Evolver 완성.

**범위**: Cycle 0 수동 검증(완료) → Cycle 1 수동 검증(Conflict-preserving) → LangGraph 자동화 → 벤치 검증 → 다중 도메인 확장.

---

## 2. Current State (현재 상태)

### 완료된 항목
- Cycle 0 수동 실행 완료 (japan-travel 벤치): KU 13, EU 18, Gap 21 open / 7 resolved
- JSON Schema 4종 확정 (KU, EU, GU, PU) → `schemas/`
- 6대 Deliverable 템플릿 확정 → `templates/`
- Metrics 6개 공식 + 건강 지표 임계치 확정
- 5대 불변원칙 + 자동 검증 방법 확정
- Critique→Plan 컴파일 6개 규칙 확정
- LangGraph 노드/엣지 설계 초안 완성 (design-v2.md §10)
- Claude Code 인프라 구축: CLAUDE.md, commands(3), hooks(1), skills(2)
- GU Bootstrap 명세 공식화 완료 → `docs/gu-bootstrap-spec.md` (Bootstrap 알고리즘 5단계, 동적 발견 규칙, 수렴 조건)

### 자산
```
schemas/          — 4종 JSON Schema (확정)
templates/        — 6대 Deliverable MD 템플릿 (확정)
bench/japan-travel/
  state/          — 5개 State JSON (Cycle 0 결과)
  cycle-0/        — 6개 Deliverable (수동 실행 결과)
docs/             — draft.md, design-v2.md, gu-bootstrap-spec.md (설계 문서)
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

### Phase 0B: Cycle 1 수동 검증 🔜 Next
- **목적**: Cycle 0에서 미검증된 Conflict-preserving 원칙 검증 + Revised Plan C1 실행
- **근거**: design-v2.md §12 — "Revised Plan C1 기반으로 한 번 더 수동 실행하여 Conflict-preserving 원칙 검증"
- **입력**: `bench/japan-travel/cycle-0/revised-plan-c1.md` (8개 Target Gap, Source Strategy 강화)
- **GU 생성/확장 규약**: `docs/gu-bootstrap-spec.md` §2 동적 GU 발견 규칙 적용 (트리거 A/B/C + 상한 준수)
- 수동 Inner Loop 재실행: Collect → Integrate → Critique → Plan Modify
- State 파일 업데이트 (knowledge-units, gap-map, metrics)
- Cycle 1 Deliverable 저장 → `bench/japan-travel/cycle-1/`
- 충돌(disputed) KU 발생 시 Conflict-preserving 원칙 검증
- Cycle 0 → Cycle 1 Metrics delta 비교

### Phase 1: LangGraph Core Pipeline
- EvolverState 타입 정의
- 6+1 노드 구현 (seed, plan, collect, integrate, critique, plan_modify, hitl_gate)
- StateGraph 빌드 + 엣지 라우팅
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

| Phase | Stage | Size | Task 수 |
|-------|-------|------|---------|
| Phase 0B | A: 준비 | S | 1 |
| Phase 0B | B: 수집+통합 | L | 2 |
| Phase 0B | C: 비평+계획수정 | M | 2 |
| Phase 1 | A: 기반 (State, I/O, Schema) | M~L | 5 |
| Phase 1 | B: 노드 구현 | L~XL | 7 |
| Phase 1 | C: Graph 빌드 | M | 3 |
| Phase 2 | A: 벤치 연결 | M | 3 |
| Phase 2 | B: 검증 파이프라인 | M~L | 4 |
| Phase 3 | A: 다중 도메인 | L | 3 |
| Phase 3 | B: Outer Loop + 안정성 | L~XL | 4 |
| **총계** | | | **34** |

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
