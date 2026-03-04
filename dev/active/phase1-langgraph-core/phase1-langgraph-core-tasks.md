# Phase 1 Tasks — LangGraph Core Pipeline
> Last Updated: 2026-03-04
> Status: Planning

## Summary

| Stage | Task | Size | Status |
|-------|------|------|--------|
| A | 1.1 프로젝트 초기화 | S | |
| A | 1.2 EvolverState 타입 정의 | M | |
| A | 1.3 JSON 파일 I/O 유틸리티 | M | |
| A | 1.4 Schema 검증 유틸리티 | M | |
| A | 1.5 Metrics 계산 유틸리티 | M | |
| B | 1.6 seed_node | L | |
| B | 1.7 mode_node | L | |
| B | 1.8 plan_node | L | |
| B | 1.9 collect_node | XL | |
| B | 1.10 integrate_node | XL | |
| B | 1.11 critique_node | L | |
| B | 1.12 plan_modify_node | L | |
| B | 1.13 hitl_gate_node | M | |
| C | 1.14 StateGraph 빌드 | L | |
| C | 1.15 엣지 라우팅 로직 | L | |
| C | 1.16 단위 테스트 | M | |

**Size 분포**: S:1, M:6, L:7, XL:2 (총 16개)

---

## Stage A: 기반 구축 (State, I/O, Schema 검증)

### 1.1 프로젝트 초기화 `[S]`

**산출물**: `pyproject.toml`, `src/` 디렉토리 구조, `tests/` 디렉토리

**완료 조건**:
- [ ] pyproject.toml에 의존성 정의 (langgraph, langchain-core, langchain-anthropic, jsonschema, pydantic, pytest)
- [ ] `src/` 및 `tests/` 디렉토리 구조 생성 (plan.md §8 참조)
- [ ] `python -m pytest` 실행 가능 (빈 테스트라도)
- [ ] `.env.example` 생성 (ANTHROPIC_API_KEY 등)

---

### 1.2 EvolverState 타입 정의 `[M]`

**산출물**: `src/state.py`

**참조**: `docs/design-v2.md` §10 EvolverState TypedDict

**완료 조건**:
- [ ] EvolverState TypedDict 정의 (design-v2 §10과 1:1 대응)
- [ ] 핵심 필드: knowledge_units, gap_map, policies, metrics, domain_skeleton
- [ ] Cycle 관리: current_cycle, current_plan, current_claims, current_critique
- [ ] Mode 관리: current_mode, axis_coverage, jump_history
- [ ] 보조 타입 정의 (ModeDecision, AxisCoverageMatrix 등)
- [ ] 단위 테스트: State 생성/직렬화 확인

---

### 1.3 JSON 파일 I/O 유틸리티 `[M]`

**산출물**: `src/utils/state_io.py`

**완료 조건**:
- [ ] `load_state(domain_path) -> EvolverState` — 5개 JSON 파일 → State 로드
- [ ] `save_state(state, domain_path)` — State → 5개 JSON 파일 저장
- [ ] `snapshot_state(domain_path, cycle)` — state-snapshots/ 디렉토리에 스냅샷
- [ ] 인코딩: `encoding='utf-8'` 명시
- [ ] 단위 테스트: bench/japan-travel/state/ 로드/저장 라운드트립

---

### 1.4 Schema 검증 유틸리티 `[M]`

**산출물**: `src/utils/schema_validator.py`

**참조**: `schemas/*.json` (4종)

**완료 조건**:
- [ ] `validate_ku(ku_dict) -> bool` — knowledge-unit.json 스키마 검증
- [ ] `validate_eu(eu_dict) -> bool` — evidence-unit.json 스키마 검증
- [ ] `validate_gu(gu_dict) -> bool` — gap-unit.json 스키마 검증
- [ ] `validate_pu(pu_dict) -> bool` — patch-unit.json 스키마 검증
- [ ] `validate_state(state) -> list[ValidationError]` — 전체 State 검증
- [ ] 단위 테스트: 유효/무효 데이터 모두 검증

---

### 1.5 Metrics 계산 유틸리티 `[M]`

**산출물**: `src/utils/metrics.py`

**참조**: `docs/design-v2.md` §4 (6개 공식 + 건강 임계치)

**완료 조건**:
- [ ] 6개 Metrics 공식 구현: evidence_rate, multi_evidence_rate, gap_resolution_rate, conflict_rate, avg_confidence, staleness_risk
- [ ] `compute_metrics(state) -> dict` — State에서 전체 Metrics 계산
- [ ] `assess_health(metrics) -> dict` — 건강/주의/위험 판정
- [ ] Axis Coverage Matrix 계산: `compute_axis_coverage(gap_map, skeleton) -> dict`
- [ ] deficit_ratio 계산: `compute_deficit_ratios(axis_coverage, skeleton) -> dict`
- [ ] 단위 테스트: bench/japan-travel Cycle 2 수치와 대조 (evidence_rate=1.0, conflict_rate=0.036, avg_confidence=0.875)

---

## Stage B: 노드 구현

### 1.6 seed_node `[L]`

**산출물**: `src/nodes/seed.py`

**참조**: `docs/gu-bootstrap-spec.md` §1 (Bootstrap 알고리즘 5단계)

**완료 조건**:
- [ ] Seed Pack 입력 → State 초기화 (K, G, P, M, D)
- [ ] Bootstrap GU 생성: Category×Field 매트릭스 스캔 → GU 자동 생성
- [ ] 우선순위 산정 (§3 규칙): expected_utility, risk_level 결정론적 할당
- [ ] Scope 경계 판정 (§4): excludes 필터, boundary_rule 적용
- [ ] Bootstrap 완료 체크 (§6-A): GU >= 20, 전 카테고리 커버, critical/high >= 3
- [ ] 단위 테스트: japan-travel skeleton 입력 → GU 25개 수준 생성 확인

---

### 1.7 mode_node `[L]`

**산출물**: `src/nodes/mode.py`

**참조**: `docs/gu-bootstrap-expansion-policy.md` §5 + `docs/gu-bootstrap-spec.md` §2.6

**완료 조건**:
- [ ] 5종 trigger 판정 (T1~T5) 구현
- [ ] T1: Axis Coverage deficit_ratio > 0 (required 축)
- [ ] T2: Spillover >= 3건, T3: High-Risk Blindspot >= 2건, T4: Prescription >= 1건, T5: Domain Shift >= 1건
- [ ] Normal/Jump Mode 결정 (trigger 1개 이상 → Jump)
- [ ] base_cap / jump_cap 계산
- [ ] explore/exploit budget 배분 (Cycle 단계별: 초기 60%, 중기 50%, 수렴 40%)
- [ ] 출력: `{mode, cap, explore_budget, exploit_budget, trigger_set}`
- [ ] Convergence Guard: jump_history에서 연속 2 Cycle Jump 감지 → HITL 트리거
- [ ] 단위 테스트: Cycle 1 State → Jump (geography deficit), Cycle 2 State → Normal

---

### 1.8 plan_node `[L]`

**산출물**: `src/nodes/plan.py`

**참조**: `docs/design-v2.md` §7 (Plan Deliverable 계약), `templates/collection-plan.md`

**완료 조건**:
- [ ] Gap Map + Mode → Collection Plan 생성 (LLM 호출)
- [ ] Jump Mode: explore Target (deficit 축 기반) + exploit Target 선정
- [ ] Normal Mode: exploit Target만 선정
- [ ] Target Gap 우선순위 산정 (expected_utility + risk_level)
- [ ] Budget & Stop Rules 포함
- [ ] 불변원칙: Plan.target_gaps ⊆ G.open 검증
- [ ] 단위 테스트: mock LLM + bench 데이터

---

### 1.9 collect_node `[XL]`

**산출물**: `src/nodes/collect.py`, `src/tools/search.py`

**참조**: `docs/design-v2.md` §7 (Collect Deliverable 계약), `templates/evidence-claim-set.md`

**완료 조건**:
- [ ] Collection Plan → WebSearch/WebFetch 도구 호출
- [ ] 검색 결과 → Claim + EU 묶음 생성 (LLM 파싱)
- [ ] 중복/상충 후보 태깅
- [ ] Budget 준수: Normal `Target × 2`, Jump `Target × 2 + 4`
- [ ] 재시도 로직 (API 실패 시)
- [ ] 단위 테스트: mock WebSearch + mock LLM

---

### 1.10 integrate_node `[XL]`

**산출물**: `src/nodes/integrate.py`

**참조**: `docs/design-v2.md` §6~§7, `docs/gu-bootstrap-spec.md` §2

**완료 조건**:
- [ ] Claims → Entity Resolution (entity_key 매칭)
- [ ] Entity Hierarchy 적용: alias 자동 변환, is_a 상속
- [ ] KB Patch 생성 (adds/updates/deprecates)
- [ ] Conflict Handling: disputed → hold/condition_split/coexist
- [ ] 동적 GU 발견 (Trigger A/B/C): cap 준수 (Normal/Jump)
- [ ] 신규 GU에 axis_tags 할당
- [ ] Schema 검증: 모든 KU/EU/GU에 대해 validate
- [ ] 불변원칙: Claim→KU 착지성, Evidence-first, Conflict-preserving 검증
- [ ] 단위 테스트: mock LLM + bench 데이터, disputed KU 삭제 시도 → 거부 확인

---

### 1.11 critique_node `[L]`

**산출물**: `src/nodes/critique.py`

**참조**: `docs/design-v2.md` §4~§5, `templates/critique-report.md`

**완료 조건**:
- [ ] State → Metrics 계산 + 건강 판정
- [ ] 6대 실패모드 분석 (Epistemic/Temporal/Structural/Consistency/Planning/Integration)
- [ ] Structural Deficit Analysis: Axis Coverage Matrix 재계산
- [ ] Jump Mode 검증: high/critical >= 40%, deficit 감소 확인
- [ ] 처방(Prescription) 도출 (RX-NNNN)
- [ ] 수렴 조건 판정 (C1~C5, Cycle >= 5)
- [ ] 불변원칙: 5대 원칙 전체 검증 결과 포함
- [ ] 단위 테스트: bench Cycle 2 State → Critique 생성

---

### 1.12 plan_modify_node `[L]`

**산출물**: `src/nodes/plan_modify.py`

**참조**: `docs/design-v2.md` §5 (Critique→Plan 6규칙), `templates/revised-plan.md`

**완료 조건**:
- [ ] Critique 처방 → Revised Collection Plan 변환
- [ ] 6대 컴파일 규칙 적용 (Epistemic/Temporal/Structural/Consistency/Planning/Integration)
- [ ] 추적성 테이블: 모든 RX → Plan 변경 매핑
- [ ] 미반영 처방은 사유 기록 필수
- [ ] Policy Update 포함 (필요 시)
- [ ] 불변원칙: Prescription-compiled 검증
- [ ] 단위 테스트: mock LLM + Critique 입력 → 추적성 테이블 확인

---

### 1.13 hitl_gate_node `[M]`

**산출물**: `src/nodes/hitl_gate.py`

**참조**: `docs/design-v2.md` §9 (HITL Gate A~E)

**완료 조건**:
- [ ] LangGraph interrupt 기반 구현
- [ ] Gate A: Plan 승인 (경량, 매회)
- [ ] Gate B: High-risk Claims 검토 (safety/policy/financial)
- [ ] Gate C: Conflict Adjudication (disputed KU 존재 시)
- [ ] Gate D: Executive Audit (10 Cycle마다)
- [ ] Gate E: Convergence Guard (연속 2 Cycle Jump 시)
- [ ] 승인/거부/수정 응답 처리
- [ ] 단위 테스트: interrupt 발동 + 승인 시나리오

---

## Stage C: Graph 빌드 + 테스트

### 1.14 StateGraph 빌드 `[L]`

**산출물**: `src/graph.py`

**참조**: `docs/design-v2.md` §10 (엣지 정의)

**완료 조건**:
- [ ] StateGraph 생성 + 8개 노드 등록
- [ ] 엣지 연결: START → seed → mode → plan → hitl(A) → collect → hitl(B) → integrate → critique → plan_modify → mode → ...
- [ ] 종료 엣지: critique → END (수렴 조건)
- [ ] Convergence Guard 엣지: mode → hitl(E) (연속 Jump)
- [ ] Graph 컴파일 성공

---

### 1.15 엣지 라우팅 로직 `[L]`

**산출물**: `src/graph.py` (라우팅 함수)

**완료 조건**:
- [ ] `should_continue(state) -> str` — 수렴 판정 (END vs continue)
- [ ] `route_hitl(state) -> str` — Gate 유형별 분기 (approve/reject/modify)
- [ ] `route_mode(state) -> str` — Jump 연속 시 HITL(E) vs plan_node
- [ ] `has_high_risk_claims(state) -> str` — Gate B 발동 여부
- [ ] `has_disputes(state) -> str` — Gate C 발동 여부
- [ ] 단위 테스트: 각 라우팅 함수에 경계값 입력

---

### 1.16 단위 테스트 `[M]`

**산출물**: `tests/` 전체

**완료 조건**:
- [ ] Stage A 유틸리티 테스트: state_io, schema_validator, metrics
- [ ] Stage B 노드 테스트: 각 노드 독립 실행 (mock LLM)
- [ ] Stage C 그래프 테스트: 단일 Cycle 실행 (mock LLM + mock WebSearch)
- [ ] 5대 불변원칙 검증 테스트: 위반 시나리오 → 감지 확인
- [ ] `python -m pytest` 전체 통과
