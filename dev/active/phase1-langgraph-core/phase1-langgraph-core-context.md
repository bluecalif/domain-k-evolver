# Phase 1 Context — LangGraph Core Pipeline
> Last Updated: 2026-03-05
> Status: ✅ Complete

## 1. 핵심 파일

### 설계 문서 (필수 참조)

| 파일 | 내용 | 참조 시점 |
|------|------|-----------|
| `docs/design-v2.md` §10 | LangGraph 노드/엣지 설계, EvolverState 타입 초안 | 노드 구현 시 항상 |
| `docs/design-v2.md` §4 | Metrics 6개 공식 + 건강 임계치 | metrics.py 구현 시 |
| `docs/design-v2.md` §5 | Critique→Plan 컴파일 6규칙 | plan_modify_node 구현 시 |
| `docs/design-v2.md` §6 | Entity Resolution + Entity Hierarchy | integrate_node 구현 시 |
| `docs/design-v2.md` §7 | Inner Loop 6단계 Deliverable 계약 | 각 노드 입출력 계약 |
| `docs/design-v2.md` §8 | 5대 불변원칙 + 자동 검증 방법 | 테스트 작성 시 |
| `docs/design-v2.md` §9 | HITL Gate 설계 (Gate A~E) | hitl_gate_node 구현 시 |
| `docs/gu-bootstrap-spec.md` §1 | Bootstrap GU 생성 알고리즘 5단계 | seed_node 구현 시 |
| `docs/gu-bootstrap-spec.md` §2 | 동적 GU 발견 규칙 (Normal/Jump cap) | integrate_node 구현 시 |
| `docs/gu-bootstrap-spec.md` §2.5 | Axis Coverage Matrix 계산 | mode_node, critique_node |
| `docs/gu-bootstrap-spec.md` §2.6 | Quantum Jump Mode trigger/guardrail | mode_node 구현 시 |
| `docs/gu-bootstrap-spec.md` §5 | 수렴 조건 (C1~C5) | 엣지 라우팅(종료 조건) |
| `docs/gu-bootstrap-expansion-policy.md` | GU 확장 정책 v1.0 (전체) | mode_node, plan_node |
| `docs/draft.md` | 원본 설계 — 프레임워크 철학 | 설계 판단 시 참고 |

### JSON Schema (구현 대상)

| 파일 | 내용 | 사용처 |
|------|------|--------|
| `schemas/knowledge-unit.json` | KU Schema (8 required + 3 optional) | schema_validator.py, integrate_node |
| `schemas/evidence-unit.json` | EU Schema (5 required + 3 optional) | schema_validator.py, collect_node |
| `schemas/gap-unit.json` | GU Schema (5 required + 3 optional) | schema_validator.py, seed_node, integrate_node |
| `schemas/patch-unit.json` | PU Schema (6 required + 3 optional) | schema_validator.py, integrate_node |

### 벤치 데이터 (테스트 입력)

| 파일 | 내용 | 용도 |
|------|------|------|
| `bench/japan-travel/state/*.json` | Cycle 2 최종 State (5개 파일) | 노드 단위 테스트 입력 |
| `bench/japan-travel/cycle-0/seed-pack.md` | Seed Pack 원본 | seed_node 참조 |
| `bench/japan-travel/cycle-2/*.md` | Cycle 2 Deliverables | 노드 출력 검증 참조 |
| `bench/japan-travel/state-snapshots/` | Cycle 0, 1 스냅샷 | 회귀 테스트 |

### 템플릿

| 파일 | 용도 |
|------|------|
| `templates/seed-pack.md` | seed_node 출력 형식 참조 |
| `templates/collection-plan.md` | plan_node 출력 형식 참조 |
| `templates/evidence-claim-set.md` | collect_node 출력 형식 참조 |
| `templates/kb-patch.md` | integrate_node 출력 형식 참조 |
| `templates/critique-report.md` | critique_node 출력 형식 참조 |
| `templates/revised-plan.md` | plan_modify_node 출력 형식 참조 |

---

## 2. 데이터 인터페이스

### EvolverState (LangGraph 내부 — design-v2 §10 기반)

```python
class EvolverState(TypedDict):
    # Core State (K, G, P, M, D)
    knowledge_units: list[dict]        # K — KU[]
    gap_map: list[dict]                # G — GU[]
    policies: dict                      # P — 출처신뢰/TTL/교차검증/충돌해결
    metrics: dict                       # M — 6개 지표 + delta
    domain_skeleton: dict               # D — 카테고리/필드/관계/키규칙/axes/entity_hierarchy

    # Cycle 관리
    current_cycle: int
    current_plan: dict | None
    current_claims: list[dict] | None
    current_critique: dict | None

    # Mode 관리 (Phase 0C 추가)
    current_mode: dict | None          # {mode, cap, explore_budget, exploit_budget, trigger_set}
    axis_coverage: dict | None         # Axis Coverage Matrix
    jump_history: list[int]            # Jump Mode 진입 Cycle 번호

    # HITL
    hitl_pending: dict | None          # Gate 정보 (interrupt 시)
```

### JSON 파일 I/O 패턴

```
읽기: bench/{domain}/state/*.json → EvolverState 필드로 로드
쓰기: 노드 실행 후 → bench/{domain}/state/*.json 업데이트
스냅샷: Cycle 시작 전 → bench/{domain}/state-snapshots/cycle-{n}-snapshot/
검증: schemas/*.json (JSON Schema Draft 2020-12)
인코딩: encoding='utf-8' 명시 (항상)
```

### 노드 입출력 계약

| 노드 | 입력 (State 필드) | 출력 (State 변경) |
|------|-------------------|-------------------|
| seed_node | domain_skeleton, policies | knowledge_units, gap_map, metrics, current_cycle=0 |
| mode_node | gap_map, domain_skeleton.axes, metrics, jump_history | current_mode, axis_coverage |
| plan_node | gap_map, current_mode, metrics, current_critique | current_plan |
| collect_node | current_plan, policies | current_claims |
| integrate_node | current_claims, knowledge_units, gap_map, domain_skeleton | knowledge_units, gap_map, metrics |
| critique_node | knowledge_units, gap_map, metrics, current_mode | current_critique, axis_coverage, metrics |
| plan_modify_node | current_critique, current_plan, policies | current_plan (revised), policies |
| hitl_gate_node | (gate-specific) | hitl_pending (cleared on approve) |

---

## 3. 주요 결정사항

| # | 결정 | 대안 | 선택 근거 | 시점 |
|---|------|------|-----------|------|
| D-P1.1 | TypedDict + dict 기반 State | Pydantic BaseModel | LangGraph 공식 패턴, 런타임 유연성 | 계획 |
| D-P1.2 | 노드 함수 시그니처: `def node(state) -> dict` | class 기반 | LangGraph 표준 패턴, 변경 필드만 반환 | 계획 |
| D-P1.3 | Mock LLM으로 테스트 | 실제 LLM 호출 | 비용 절감, 결정론적 테스트 | 계획 |
| D-P1.4 | JSON 파일 I/O (현행 유지) | SQLite 전환 | Phase 0~0C와 동일, 디버깅 투명성 | project-overall D-01 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙 (자동 검증 대상)

- [ ] **Gap-driven**: plan_node — `Plan.target_gaps ⊆ G.open`
- [ ] **Claim→KU 착지성**: integrate_node — `count(claims) == count(adds + updates + rejected_with_reason)`
- [ ] **Evidence-first**: integrate_node — `all(len(ku.evidence_links) >= 1 for active KU)`
- [ ] **Conflict-preserving**: integrate_node — disputed KU 삭제 불가, hold/condition_split/coexist만
- [ ] **Prescription-compiled**: plan_modify_node — `all(rx.id in revised_plan.traceability)`

### Metrics 건강 임계치

| 지표 | 건강 | 주의 | 위험 |
|------|------|------|------|
| 근거율 | >= 0.95 | 0.80~0.94 | < 0.80 |
| 다중근거율 | >= 0.50 | 0.30~0.49 | < 0.30 |
| 충돌률 | <= 0.05 | 0.06~0.15 | > 0.15 |
| 평균 confidence | >= 0.85 | 0.70~0.84 | < 0.70 |
| 신선도 리스크 | 0 | 1~3 | > 3 |

### 코드 컨벤션

- **entity_key**: `{domain}:{category}:{slug}` (lowercase + hyphen)
- **ID 패턴**: `KU-NNNN`, `EU-NNNN`, `GU-NNNN`, `PU-NNNN`
- **노드 함수**: `def node_name(state: EvolverState) -> dict` (변경 필드만 반환)
- **인코딩**: JSON read/write `encoding='utf-8'`, `PYTHONUTF8=1`
- **커밋**: `[phase1] Step X.Y: 설명`
- **브랜치**: `feature/phase1-langgraph-core`

### Jump Mode 관련 (Phase 0C 확정)

- mode_node에서 5종 trigger 판정 로직 구현
- T1: `deficit_ratio > 0` (required 축)
- jump_cap: `min(max(10, ceil(open * 0.6)), 30)`
- base_cap: `min(max(4, ceil(open * 0.2)), 12)`
- explore 비율: 초기 60%, 중기 50%, 수렴 40%
- Guardrail 4종: Quality, Cost, Balance, Convergence

---

## 5. Stage C 구현 파일

### 신규 파일
| 파일 | 내용 |
|------|------|
| `src/graph.py` | StateGraph 빌드 + 엣지 라우팅 (13노드 등록, 조건부 엣지 4개) |
| `tests/test_graph.py` | Graph 통합 테스트 36개 (빌드, 라우팅, 헬퍼, stream 통합, 불변원칙) |

### Stage C 결정사항

| # | 결정 | 대안 | 선택 근거 | 시점 |
|---|------|------|-----------|------|
| D-C1 | HITL Gate를 gate별 개별 노드로 등록 (`hitl_a`~`hitl_e`) | 단일 hitl 노드 + 조건 분기 | 같은 `hitl_gate_node`를 `_make_hitl_node(gate)` 팩토리로 래핑, 그래프 토폴로지 명확 | Stage C |
| D-C2 | `cycle_increment_node` 별도 노드 | plan_modify 내부 처리 | plan_modify → cycle_inc → mode 순서 명시적 | Stage C |
| D-C3 | `build_graph(llm=, search_tool=, hitl_response=)` 팩토리 패턴 | 전역 설정 | 도구 바인딩을 그래프 빌드 시 주입, 테스트 용이 | Stage C |
| D-C4 | `functools.partial`로 노드에 llm/search_tool 바인딩 | 클로저/클래스 | 기존 노드 시그니처(`state, *, llm=`) 유지하면서 바인딩 | Stage C |
| D-C5 | 통합 테스트 `graph.stream()` + `_stream_until()` 헬퍼 | `graph.invoke()` | 무한 루프(GraphRecursionError) 방지, 1 Cycle만 검증 | Stage C |

### 테스트 현황 (최종)
- Stage A+B: 155 passed
- Stage C: 36 passed
- **전체: 191 passed, 0 failed**
