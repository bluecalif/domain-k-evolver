# Project Overall Tasks
> Last Updated: 2026-03-03 (GU Bootstrap 명세 반영)
> Status: In Progress

## Summary

| Phase | Total | S | M | L | XL | Done |
|-------|-------|---|---|---|----|----|
| Phase 0 | — | — | — | — | — | ✅ Complete |
| Phase 0B | 5 | 1 | 2 | 2 | 0 | 0/5 |
| Phase 1 | 15 | 2 | 5 | 6 | 2 | 0/15 |
| Phase 2 | 7 | 1 | 3 | 2 | 1 | 0/7 |
| Phase 3 | 7 | 0 | 2 | 3 | 2 | 0/7 |
| **총계** | **34** | **6** | **12** | **13** | **7** | **0/34** |

---

## Phase 0: Cycle 0 수동 검증 ✅

모두 완료. 상세는 `bench/japan-travel/cycle-0/` 및 `docs/design-v2.md` 참조.

---

## Phase 0B: Cycle 1 수동 검증

> **목적**: Conflict-preserving 원칙 검증 + Revised Plan C1 실행 (design-v2.md §12)
> **입력**: `bench/japan-travel/cycle-0/revised-plan-c1.md` (8 Target Gaps)

- [ ] **0B.1** Cycle 1 디렉토리 준비 — `bench/japan-travel/cycle-1/` 생성, State 스냅샷 `[S]`
- [ ] **0B.2** Collect — revised-plan-c1 기반 8개 Gap 수집, Evidence Claim Set 작성 `[L]`
- [ ] **0B.3** Integrate — Claims → KB Patch 적용, State 업데이트 (충돌 KU 의도적 포함 시도) + 동적 GU 발견 (gu-bootstrap-spec §2, 상한 4개) `[L]`
- [ ] **0B.4** Critique — Metrics delta 계산, Cycle 0 vs Cycle 1 비교, Conflict-preserving 검증 + 동적 GU 발견 체크 (§6-B) `[M]`
- [ ] **0B.5** Plan Modify — Critique 처방 기반 Revised Plan C2 작성, design-v2 피드백 반영 `[M]`

### Phase 0B 핵심 검증 포인트
- **Conflict-preserving**: Cycle 0에서 충돌 0건 → Cycle 1에서 의도적으로 충돌 상황 생성/검증
- **Prescription-compiled**: 모든 RX-NN이 Revised Plan에 추적 가능하게 반영되는지 재확인
- **Financial 교차검증 강화**: RX-01 반영 — financial KU의 min_eu ≥ 2 enforcement
- **카테고리 분포 보정**: RX-03 반영 — accommodation, dining, attraction 보충
- **동적 GU 발견 규칙 실용성 검증**: gu-bootstrap-spec §2 트리거 A/B/C + 상한(open의 20%) 첫 적용

---

## Phase 1: LangGraph Core Pipeline

### Stage A: 기반 구축 (State, I/O, Schema 검증)

- [ ] **1.1** 프로젝트 초기화 — pyproject.toml, 의존성, 디렉토리 구조 `[S]`
- [ ] **1.2** EvolverState 타입 정의 — `src/state.py` `[M]`
- [ ] **1.3** JSON 파일 I/O 유틸리티 — `src/utils/state_io.py` (load/save + encoding) `[M]`
- [ ] **1.4** Schema 검증 유틸리티 — `src/utils/schema_validator.py` (jsonschema) `[M]`
- [ ] **1.5** Metrics 계산 유틸리티 — `src/utils/metrics.py` (6개 공식 + 임계치) `[M]`

### Stage B: 노드 구현

- [ ] **1.6** seed_node — Seed Pack → State 초기화 `[L]`
- [ ] **1.7** plan_node — Gap Map → Collection Plan 생성 (LLM) `[L]`
- [ ] **1.8** collect_node — Plan → Claims 수집 (WebSearch/WebFetch + LLM) `[XL]`
- [ ] **1.9** integrate_node — Claims → KB Patch 적용 (LLM + I/O) `[XL]`
- [ ] **1.10** critique_node — State → Critique Report (LLM + Metrics) `[L]`
- [ ] **1.11** plan_modify_node — Critique → Revised Plan (LLM) `[L]`
- [ ] **1.12** hitl_gate_node — LangGraph interrupt 기반 HITL `[M]`

### Stage C: Graph 빌드

- [ ] **1.13** StateGraph 빌드 — `src/graph.py` (노드 등록 + 엣지) `[L]`
- [ ] **1.14** 엣지 라우팅 로직 — 조건부 엣지 (종료, HITL, Outer Loop) `[L]`
- [ ] **1.15** 단위 테스트 — 각 노드 + 전체 그래프 `[S]`

---

## Phase 2: Bench Integration & Validation

### Stage A: 벤치 연결

- [ ] **2.1** japan-travel State 로딩 + Graph 실행 연결 `[M]`
- [ ] **2.2** Cycle 1 자동 실행 + 결과 저장 `[L]`
- [ ] **2.3** Cycle 0 vs Cycle 1 결과 비교 검증 `[M]`

### Stage B: 검증 파이프라인

- [ ] **2.4** 5대 불변원칙 자동 검증 모듈 `[L]`
- [ ] **2.5** Metrics 임계치 기반 경고/중단 로직 `[M]`
- [ ] **2.6** HITL Gate 실전 테스트 (interrupt 동작 확인) `[S]`
- [ ] **2.7** 통합 테스트 — 전체 Cycle 자동 실행 + 검증 `[XL]`

---

## Phase 3: Multi-Domain & Robustness

### Stage A: 다중 도메인

- [ ] **3.1** 새 도메인 Seed Pack 작성 (예: 부동산/기술 스택) `[L]`
- [ ] **3.2** 새 도메인 Evolver 실행 + 결과 검증 `[L]`
- [ ] **3.3** 도메인 간 공통/차이 분석 + 프레임워크 일반화 `[M]`

### Stage B: Outer Loop + 안정성

- [ ] **3.4** Outer Loop 구현 — Executive Audit + Remodeling 노드 `[XL]`
- [ ] **3.5** 에러 처리 + 복구 메커니즘 (API 실패, 파싱 오류) `[L]`
- [ ] **3.6** 토큰/비용 최적화 `[M]`
- [ ] **3.7** 문서화 + 사용 가이드 `[XL]`
