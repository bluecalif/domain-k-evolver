# Project Overall Tasks
> Last Updated: 2026-03-04 (Phase 0C 삽입 — GU 전략 재검토)
> Status: In Progress

## Summary

| Phase | Total | S | M | L | XL | Done |
|-------|-------|---|---|---|----|----|
| Phase 0 | — | — | — | — | — | ✅ Complete |
| Phase 0B | 5 | 1 | 2 | 2 | 0 | ✅ Complete (5/5) |
| Phase 0C | 6 | 0 | 3 | 2 | 1 | ✅ Complete (6/6) |
| Phase 1 | 15 | 2 | 5 | 6 | 2 | 0/15 |
| Phase 2 | 7 | 1 | 3 | 2 | 1 | 0/7 |
| Phase 3 | 7 | 0 | 2 | 3 | 2 | 0/7 |
| **총계** | **40** | **4** | **13** | **13** | **10** | **11/40** |

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
