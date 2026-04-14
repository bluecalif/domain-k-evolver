# SI-P3R: Tasks

> Last Updated: 2026-04-14
> Progress: 7/8 (88%)

## T1. 제거 — Provider/Fetch/HTML 모듈 `[M]` ✅
- [x] `src/adapters/fetch_pipeline.py` 삭제
- [x] `src/utils/html_strip.py` 삭제
- [x] `src/adapters/providers/{base,ddg_provider,curated_provider,tavily_provider}.py` 삭제
- [x] `tests/test_fetch_pipeline.py`, `tests/test_html_strip.py`, `tests/test_providers.py`, `tests/test_collect_p3.py` 삭제
- [x] `pyproject.toml` beautifulsoup4 + ddg extras 제거
- [x] import/참조 잔재 grep 후 정리 (잔재 0)

## T2. Tavily search_tool 단순화 `[S]` ✅
- [x] `search_adapter.py` 에 snippet-only `TavilySearchAdapter` 단일화 (provider 계층 제거)
- [x] `fetch()`, `create_providers()`, `TavilySearchAdapter.fetch_calls` 제거
- [x] `SearchTool` Protocol 에서 `fetch` 제거, `MockSearchTool` 단순화

## T3. collect.py 2단계화 `[L]` ✅
- [x] `_fetch_phase` 삭제, `_collect_single_gu` 2단계(SEARCH→PARSE)
- [x] `_parse_claims_llm`: snippet 전용 prompt
- [x] `_build_parse_prompt`: `## Fetched Content` 섹션 제거
- [x] provenance 축소 `{provider, domain, retrieved_at, trust_tier}`
- [x] `_provider_entropy` 제거, `_domain_entropy` 유지

## T4. Config & Entry Point `[S]` ✅
- [x] `src/config.py` SearchConfig: fetch 관련 필드 7개 제거 → 6필드만 유지
- [x] `scripts/run_readiness.py`: providers/fetch_pipeline 제거
- [x] `src/graph.py`, `src/orchestrator.py`: providers/fetch_pipeline 파라미터 제거

## T5. 후속 Phase 참조 갱신 `[M]` ✅
- [x] `src/nodes/audit.py`: provider_entropy 미참조 확인
- [x] `src/utils/policy_manager.py`: providers_used 미참조 확인 (src/ grep 0)
- [x] integrate/dispute provenance 방어적 접근 확인
- [x] 전체 테스트 green: **608 passed, 3 skipped** (이전 694 → 608, -86개는 삭제된 provider/fetch/html 테스트)

## T6. Bench skeleton 정리 `[S]` ✅
- [x] `preferred_sources` 처리: **옵션 B 채택** — 코드/스키마 참조 0건 확인, Bronze read-only 유지, 필드 historical 보존
- [x] `bench/japan-travel-auto/` state: 구 provenance schema 혼재 → archive 처리 (P3R smoke부터는 clean root 사용)
- [x] `bench/silver/japan-travel/p3r-smoke/` trial namespace 규칙 문서화 (T7에서 실제 생성)

## T7. Smoke Trial `[M]` ✅
- [x] 1 cycle 실행 완료 (2026-04-14): `bench/silver/japan-travel/p3r-smoke/`
- [x] 실행 시간 **88.3초** (목표 < 2분 ✅)
- [x] KU 13→25 (+12), GU 28→54, **gu_resolved=10** → claims 생성 성공 (D-120 재발 없음)
- [x] `collect_failure_rate=0.0`, evidence_rate=1.0, avg_confidence=0.86, conflict_rate=0.2 (건강)
- [x] trajectory 저장 완료, readiness-report.json 기록

## T8. Gate Trial & 재판정 `[L]`
- [ ] 5 cycle trial: `--bench-root bench/silver/japan-travel/p3r-gate-trial`
- [ ] VP1/VP2/VP3 집계 → P3 Gate 판정
- [ ] P2 Gate 재판정 (P3R 완료 조건으로 연쇄 무효 해제)
- [ ] MEMORY.md D-120 해제, Phase Status 업데이트
