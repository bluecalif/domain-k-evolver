# Phase 2: Bench Integration & Real Self-Evolution — Tasks
> Last Updated: 2026-03-05
> Status: Not Started (0/25)

## Summary

| Stage | Total | S | M | L | XL | Done |
|-------|-------|---|---|---|----|----|
| A: 실행 인프라 | 6 | 2 | 3 | 1 | 0 | 0/6 |
| B: 코드 수정 + 노드 강화 | 8 | 3 | 3 | 2 | 0 | 0/8 |
| C: 10+ 사이클 검증 | 7 | 1 | 3 | 1 | 2 | 0/7 |
| D: 체크포인트 + 안정성 | 4 | 2 | 2 | 0 | 0 | 0/4 |
| **합계** | **25** | **8** | **11** | **4** | **2** | **0/25** |

---

## Stage A: 실행 인프라

- [ ] **2.1** LLM Adapter — OpenAI GPT 래퍼 `[M]`
  - `src/adapters/llm_adapter.py` 생성
  - langchain-openai ChatOpenAI 래핑
  - 테스트: Mock/Real 전환 가능

- [ ] **2.2** SearchTool Adapter — Tavily Search 래퍼 `[M]`
  - `src/adapters/search_adapter.py` 생성
  - tavily-python TavilySearchResults 래핑
  - 테스트: Mock/Real 전환 가능

- [ ] **2.3** Config — 환경 설정 `[S]`
  - `src/config.py` 생성
  - API 키, 모델명, 온도, max_tokens 등
  - `.env` 또는 환경변수에서 로딩

- [ ] **2.4** Orchestrator — 사이클 관리 `[L]`
  - `src/orchestrator.py` 생성
  - Graph 외부에서 multi-cycle 루프
  - 사이클 간 save/snapshot/invariant check
  - max_cycles, stop 조건 설정

- [ ] **2.5** State 전이 수정 `[M]`
  - 노드들의 llm=None fallback 제거
  - Real LLM 응답 파싱 로직
  - 기존 테스트 호환성 유지

- [ ] **2.6** Metrics Logger `[S]`
  - `src/utils/metrics_logger.py` 생성
  - 사이클별 6개 지표 + KU/GU 카운트 기록
  - CSV/JSON 출력

---

## Stage B: 코드 수정 + 노드 강화

- [ ] **2.7** seed 일반화 `[S]`
  - CORE_CATEGORIES japan-travel 하드코딩 제거
  - domain-skeleton에서 동적 로딩

- [ ] **2.8** critique 실패모드 5/6 `[M]`
  - Structural(5): 스키마 구조 검증
  - Integration(6): 통합 정합성 검증

- [ ] **2.9** critique T2/T5 설정 `[M]`
  - T2: spillover_count 계산 + 설정
  - T5: domain_shift_detected 로직

- [ ] **2.10** C3 수정 `[S]`
  - net_gap_changes 값 실제 전달
  - 항상 True 버그 수정

- [ ] **2.11** integrate LLM 비교 `[M]`
  - 충돌 감지: str() → LLM 의미 비교
  - 유사도 기반 충돌 판단

- [ ] **2.12** plan_modify 실제 효과 `[L]`
  - Gap Map 실제 변경 반영
  - Revised Plan → State 적용

- [ ] **2.13** collect 프롬프트 `[M]`
  - Real Search 결과 → LLM Claim 추출
  - 구조화 프롬프트 설계

- [ ] **2.14** plan 프롬프트 `[S]`
  - LLM 기반 Plan 생성
  - Gap Map → Collection Plan 변환 프롬프트

---

## Stage C: 10+ 사이클 검증

- [ ] **2.15** Realistic Mock `[M]`
  - LLM 응답 녹화/재생 모드
  - 테스트 재현성 보장

- [ ] **2.16** 불변원칙 자동검증 `[M]`
  - `src/utils/invariant_checker.py` 생성
  - 5대 불변원칙 매 사이클 자동 체크
  - 위반 시 상세 리포트

- [ ] **2.17** Metrics guard `[S]`
  - 임계치 위반 시 경고/중단
  - 근거율 < 0.80, 충돌률 > 0.15 등

- [ ] **2.18** 10-Cycle Test Mock `[XL]`
  - Mock 기반 10사이클 자동 실행
  - 불변원칙 + Metrics 전체 검증
  - KU/GU 추이 확인

- [ ] **2.19** 10-Cycle Test Real `[L]`
  - Real API 10사이클 실행
  - 비용/시간 모니터링
  - 결과 비교 분석

- [ ] **2.20** Trajectory Analyzer `[M]`
  - 사이클별 KU/GU/Metrics 추이
  - 시각화 (matplotlib/plotly)

- [ ] **2.21** Bench Run Script `[S]`
  - `scripts/bench_run.py`
  - 원커맨드 벤치 실행

---

## Stage D: 체크포인트 + 안정성

- [ ] **2.22** Gate D 강화 `[M]`
  - integrate 후 Schema 검증
  - 불변원칙 체크 자동 삽입

- [ ] **2.23** Plateau Detection `[M]`
  - 수렴 감지 (KU/GU 변화 < 임계치)
  - 자동 종료 조건

- [ ] **2.24** Snapshot Diff `[S]`
  - 사이클 간 State 변화 요약
  - 변경/추가/삭제된 KU/GU 리포트

- [ ] **2.25** Memory Guard `[S]`
  - 토큰/메모리 사용량 모니터링
  - State 크기 경고
