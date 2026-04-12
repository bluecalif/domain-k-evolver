# Session Compact

> Generated: 2026-04-12
> Source: Conversation compaction via /compact-and-go

## Goal

P3 Acquisition Expansion 구현 (22 tasks) + E2E bench 실행 + Gate 판정

## Completed

- [x] P3 Stage A: Provider 플러그인 (A1~A5) — `src/adapters/providers/` 4파일 + `search_adapter.py` 확장
- [x] P3 Stage B: FetchPipeline (B1~B6) — `src/adapters/fetch_pipeline.py` (robots/ct/bytes/rate-limit)
- [x] P3 Stage C: Collect 리팩터 + Config + Provenance + Entropy (C1~C6)
- [x] P3 Stage D: 테스트 (D1~D5) — 55 신규 테스트 → **총 599 passed**
- [x] 커밋: `2bd4086 [si-p3] P3 Acquisition Expansion 구현 완료 (22/22, 599 tests)`
- [x] `build_graph` + `Orchestrator`에 providers/fetch_pipeline/search_config 파라미터 추가
- [x] `run_readiness.py`에 P3 인프라 연결 (create_providers + FetchPipeline)
- [x] P3 trial 디렉토리 생성: `bench/silver/japan-travel/p3-20260412-acquisition/` (state + trajectory 폴더)

## Current State

- **Git**: branch `main`, latest commit `2bd4086` (P3 구현 완료)
- **Tests**: 599 passed, 3 skipped
- **Uncommitted changes**: `graph.py`, `orchestrator.py`, `run_readiness.py` (P3 연결), trial 디렉토리
- **Silver 전체**: P0 32/32 ✅, P1 12/12 ✅, P3 22/22 ✅ (Gate 미실행)

### Changed Files (uncommitted)

- `src/graph.py` — build_graph에 providers/fetch_pipeline/search_config 파라미터 추가
- `src/orchestrator.py` — Orchestrator에 providers/fetch_pipeline 전달
- `scripts/run_readiness.py` — P3 providers + FetchPipeline 생성 코드 추가
- `bench/silver/japan-travel/p3-20260412-acquisition/` — trial 디렉토리 (신규, 빈 state/trajectory)

### Committed Files (commit `2bd4086`)

- `src/adapters/providers/__init__.py` (신규)
- `src/adapters/providers/base.py` (신규 — SearchProvider Protocol + SearchResult)
- `src/adapters/providers/tavily_provider.py` (신규 — Tavily provider)
- `src/adapters/providers/ddg_provider.py` (신규 — DDG optional fallback)
- `src/adapters/providers/curated_provider.py` (신규 — preferred_sources 매칭)
- `src/adapters/fetch_pipeline.py` (신규 — FetchPipeline + RobotsCache + RateLimiter)
- `src/adapters/search_adapter.py` (수정 — deprecated 마킹 + create_providers)
- `src/config.py` (수정 — SearchConfig 14필드 확장)
- `src/nodes/collect.py` (수정 — 3단계 SEARCH→FETCH→PARSE + provenance + entropy)
- `pyproject.toml` (수정 — duckduckgo-search optional)
- `tests/test_providers.py` (신규 — 21 tests)
- `tests/test_fetch_pipeline.py` (신규 — 16 tests)
- `tests/test_collect_p3.py` (신규 — 13 tests)
- `tests/test_adapters.py` (수정 — 5 tests 추가)
- `tests/test_nodes/test_collect.py` (수정 — P3 동작 반영)

## Remaining / TODO

### 즉시 해야 할 것

1. **trial-card.md 생성** — `bench/silver/japan-travel/p3-20260412-acquisition/trial-card.md`
2. **seed state 복사** — cycle-0-snapshot에서 trial state/ 로 복사
3. **E2E bench 실행** — `python scripts/run_readiness.py --bench-root bench/silver/japan-travel/p3-20260412-acquisition --cycles 5`
4. **결과 자가평가** — fetch ≥ 80%, EU/claim ≥ 1.8, entropy ≥ 2.5, 비용 ≤ 2×
5. **graph/orchestrator 변경 커밋** — P3 연결 코드 커밋
6. **dev-docs 업데이트** — tasks.md 체크, plan.md Status, E2E Bench Results 테이블 채움
7. **project-overall 동기화** — P3 완료 반영
8. **Gate 판정 커밋** — `[si-p3] Gate PASS/FAIL: {근거}`

### P3 Gate 정량 기준 (tasks.md §Phase Gate Checklist)

- [ ] fetch 성공률 ≥ 80%
- [ ] claim 당 평균 EU ≥ 1.8
- [ ] domain_entropy ≥ 2.5 bits
- [ ] cycle 당 LLM 비용 ≤ baseline × 2.0
- [ ] robots.txt 거부 차단 (S8) pass
- [ ] cost budget degrade (S9) pass
- [ ] provenance KU/EU 저장→load 왕복 보존
- [ ] 테스트 수 ≥ 579 (현재 599 ✅)

## Key Decisions

- **D-100**: FetchPipeline은 `urllib.request` 기반 (httpx 미도입)
- **D-101**: robots.txt 캐시 = per-run in-memory
- **D-102**: CuratedProvider의 preferred_sources = skeleton 필드 (빈 목록이면 0건 반환)
- **D-103**: collect_node 외부 인터페이스 보존 (P0-X2 동결 준수)
- **P3 provider 순서**: curated → tavily → ddg
- **SearchConfig 확장**: 기존 4필드 + 10 신규 = 14필드 (frozen dataclass 유지)
- **collect.py 3단계**: _search_phase → _fetch_phase → _parse_phase (deterministic or LLM)
- **provenance 7필드**: providers_used, domain, fetch_ok, fetch_depth, content_type, retrieved_at, trust_tier

## Context

다음 세션에서는 답변에 **한국어** 사용.

### 핵심 제약

- **Bash 절대경로 필수** (CLAUDE.md) — `cd` 금지, `git -C <abs_path>` 패턴 사용
- **Bronze 보호**: `bench/japan-travel/` read-only
- **커밋 prefix**: `[si-p{N}]`
- **인코딩**: `PYTHONUTF8=1`, `encoding='utf-8'` 명시

### E2E bench 실행 참조

- Seed state: `bench/japan-travel/state-snapshots/cycle-0-snapshot/` (13 KU, cycle 0)
- P0 baseline trial: `bench/silver/japan-travel/p0-20260412-baseline/` (결과 있음)
- 스크립트: `scripts/run_readiness.py --bench-root <trial-path> --cycles 5`
- Orchestrator가 providers/fetch_pipeline을 graph에 전달하도록 이미 연결됨

### 참조 파일

- P3 dev-docs: `dev/active/phase-si-p3-acquisition/`
- project-overall: `dev/active/project-overall/`
- Silver masterplan: `docs/silver-masterplan-v2.md`

## Next Action

1. trial-card.md 생성 + seed state 복사
2. `python scripts/run_readiness.py --bench-root bench/silver/japan-travel/p3-20260412-acquisition --cycles 5` 실행
3. 결과 분석 + Gate 판정
4. graph/orchestrator 변경 + dev-docs + project-overall 커밋
