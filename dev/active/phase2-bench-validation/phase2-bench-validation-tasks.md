# Phase 2: Bench Integration & Real Self-Evolution — Tasks
> Last Updated: 2026-03-05
> Status: In Progress (11/16)

## Summary

| Stage | Total | S | M | L | Done |
|-------|-------|---|---|---|----|
| A': Smoke + 1 Cycle | 5 | 1 | 3 | 1 | 5/5 ✅ |
| B': 안정화 + 3 Cycle | 6 | 2 | 3 | 1 | 6/6 ✅ |
| C': 10+ Cycle | 5 | 2 | 2 | 1 | 0/5 |
| **합계** | **16** | **5** | **8** | **3** | **11/16** |

---

## Stage A': Smoke Test → Real 1 Cycle ✅

> Gate: Real API 1사이클 완주 + KU 1개 이상 추가 → **PASSED** (KU 28→34, +6)

- [x] **2.1** API 키 검증 + Smoke Test `[S]`
  - `.env` 파일 생성, `.gitignore`에 추가
  - `src/config.py` API 키 빈 문자열 ValueError
  - `tests/test_smoke_real.py` — OpenAI/Tavily 각 1회 호출 확인

- [x] **2.2** LLM 응답 파싱 강화 `[M]`
  - `src/utils/llm_parse.py` 신규 — `extract_json()` (markdown fence 제거)
  - `src/nodes/plan.py`, `src/nodes/collect.py`에서 사용

- [x] **2.3** collect_node 프롬프트 정교화 `[M]`
  - `_build_parse_prompt()` 강화 — 필수 필드 명시, 구조화된 입력
  - `src/nodes/collect.py`

- [x] **2.4** Orchestrator 정합성 수정 `[M]`
  - `graph.invoke()` 단순화, seed 스킵 (cycle > 1)
  - `src/orchestrator.py`, `src/graph.py`

- [x] **2.5** Real API 1 Cycle 실행 `[L]` ★★★
  - `scripts/run_one_cycle.py` 신규
  - config fallback 버그 수정 (gpt-4o-mini → gpt-4.1-mini)
  - jump target_count 상한 10, max_workers=5
  - 결과: KU 28→34 (+6), GU 39→52, Claims 22, ~2분

---

## Stage B': 안정화 + 3 Cycle ✅

> Gate: 3사이클 연속 에러 없이 완주 + 불변원칙 위반 0건 → **PASSED**

- [x] **2.6** 에러 핸들링 + Rate Limiting `[M]`
  - search_adapter: `_retry_with_backoff()` 지수 백오프 (1s→2s→4s), 호출 카운터
  - llm_adapter: `LLMCallCounter` 래퍼 (call_count, token tracking), `max_retries=3`
  - `src/adapters/llm_adapter.py`, `src/adapters/search_adapter.py`

- [x] **2.7** seed 일반화 + cycle>1 스킵 `[S]`
  - CORE_CATEGORIES 하드코딩 제거 → `skeleton["core_categories"]` 동적 추출
  - `src/nodes/seed.py`, `bench/japan-travel/state/domain-skeleton.json`

- [x] **2.8** plan_modify 실효성 + C3 수정 `[M]`
  - `_compile_prescription()` → 실제 plan target_gaps 추가 + gap_map priority 변경
  - critique C3 `net_gap_changes` 계산 + state 누적 + `_check_convergence`에 전달
  - `src/nodes/plan_modify.py`, `src/nodes/critique.py`, `src/state.py`

- [x] **2.9** 불변원칙 자동검증 `[S]`
  - `src/utils/invariant_checker.py` 신규 — I1~I5 5대 불변원칙 체크
  - `tests/test_invariant_checker.py` — 8 tests
  - `scripts/run_bench.py`에서 매 사이클 후 호출

- [x] **2.10** 비용/토큰 로깅 `[M]`
  - `LLMCallCounter`: usage_metadata → prompt/completion tokens 추적
  - `MetricsLogger.log()`: llm_calls, llm_tokens, search_calls, fetch_calls 필드 추가
  - `MetricsLogger.summary()`: 총 API 비용 합산
  - `scripts/run_one_cycle.py`: API 카운터 로깅 추가

- [x] **2.11** Real API 3 Cycle 실행 `[L]` ★★
  - `scripts/run_bench.py` 신규 (argparse --cycles, 불변원칙 검증, trajectory 저장)
  - 3 Cycle 연속 성공: KU 28→42, GU resolved 21→32, 불변원칙 위반 0회
  - API: LLM 17 calls (84,736 tokens), Search 42, Fetch 28
  - Trajectory: `bench/japan-travel-auto/trajectory/`

---

## Stage C': 10+ Cycle 자동화

> Gate: 10사이클 완주 (또는 plateau 조기 종료) + 결과 분석 리포트

- [ ] **2.12** Plateau Detection + 자동 종료 `[M]`
  - 연속 N사이클 KU/GU 변화 0 → plateau
  - `src/config.py`, `src/orchestrator.py`

- [ ] **2.13** Metrics Guard `[S]`
  - conflict_rate > 0.30, evidence_rate < 0.50 → 경고/중단
  - `src/orchestrator.py`

- [ ] **2.14** 10 Cycle Real 실행 `[L]` ★
  - `scripts/run_bench.py --cycles 10`
  - 최종 KU/GU, 사이클별 CSV, 비용, 불변원칙 로그

- [ ] **2.15** Bench Run CLI 정비 `[S]`
  - argparse: `--cycles`, `--domain`, `--dry-run`, `--resume`
  - `scripts/run_bench.py`

- [ ] **2.16** 결과 분석 + Snapshot Diff `[M]`
  - `scripts/analyze_trajectory.py` 신규
  - 사이클별 추이 + 카테고리 커버리지

---

## 삭제/연기된 기존 Tasks

| 기존 Task | 판정 | 이유 |
|-----------|------|------|
| 기존 2.1~2.6 (Stage A) | 완료 인정 | 코드 존재, 보완만 필요 |
| critique 실패모드 5/6 | 연기 | 결정론적 critique로 10사이클 가능 |
| critique T2/T5 | 연기 | Jump Mode 발동에만 영향 |
| integrate LLM비교 | 삭제 | str() 비교로 기본 충돌 감지 충분 |
| Realistic Mock(녹화/재생) | 삭제 | Real API 우선 |
| Trajectory Analyzer(시각화) | 축소→2.16 | 텍스트 테이블로 충분 |
| Stage D 전체 | 합병/삭제 | 불변원칙(2.9), plateau(2.12), diff(2.16)에 흡수 |
