# SI-P3R: Tasks

> Last Updated: 2026-04-14
> Progress: 0/8 (0%)

## T1. 제거 — Provider/Fetch/HTML 모듈 `[M]`
- [ ] `src/adapters/fetch_pipeline.py` 삭제
- [ ] `src/utils/html_strip.py` 삭제
- [ ] `src/adapters/providers/{base,ddg_provider,curated_provider}.py` 삭제
- [ ] `tests/test_fetch_pipeline.py`, `tests/test_html_strip.py`, `tests/test_providers_*.py` 삭제
- [ ] `pyproject.toml` beautifulsoup4 제거
- [ ] import/참조 잔재 grep 후 정리

## T2. Tavily search_tool 단순화 `[S]`
- [ ] `src/adapters/providers/tavily_provider.py` → `src/adapters/search_tool.py` 로 이관
- [ ] Protocol/trust_tier 제거, dict/SearchResult 최소화
- [ ] 단위 테스트 재작성

## T3. collect.py 2단계화 `[L]`
- [ ] `_fetch_phase` 삭제, `_collect_single_gu` 2단계(SEARCH→PARSE)로 축소
- [ ] `_parse_claims_llm`: snippet 전용 prompt. `fetched_content` 파라미터 제거
- [ ] `_build_parse_prompt`: `## Fetched Content` 섹션 제거, snippet 상위 N개만
- [ ] provenance: `{provider, domain, retrieved_at, trust_tier}` 축소
- [ ] `_provider_entropy` 제거, `_domain_entropy` 유지
- [ ] `tests/test_collect_p3.py` 재작성 (fetch 제거)

## T4. Config & Entry Point `[S]`
- [ ] `src/config.py` SearchConfig: `tavily_max_results`만 유지
- [ ] `scripts/run_readiness.py` L156-165: `providers=`/`fetch_pipeline=` 제거
- [ ] deprecated script(run_one_cycle/run_bench) 호환성 최종 확인

## T5. 후속 Phase 참조 갱신 `[M]`
- [ ] `src/nodes/audit.py`: `provider_entropy` 참조 제거
- [ ] `src/utils/policy_manager.py`: `providers_used` → `provider` 단일 참조
- [ ] `src/nodes/integrate.py`, `dispute_resolver.py`: provenance `.get()` 방어적 읽기 확인
- [ ] Phase 3~5 관련 테스트 green 확인

## T6. Bench skeleton 정리 `[S]`
- [ ] `bench/japan-travel/state-snapshots/cycle-0-snapshot/domain-skeleton.json` `preferred_sources` 필드 처리 방침 결정(제거 vs query-hint 재정의)
- [ ] `bench/japan-travel-auto/` state: archive 또는 무시 문서화
- [ ] `bench/silver/japan-travel/p3r-smoke/` 초기화

## T7. Smoke Trial `[M]`
- [ ] 1 cycle 실 벤치: `--bench-root bench/silver/japan-travel/p3r-smoke --cycles 1`
- [ ] 10/10 GU claims > 0 검증
- [ ] 실행 시간 < 2분 검증
- [ ] trajectory 분석 → Phase 5 baseline 대비 회귀 없음 확인

## T8. Gate Trial & 재판정 `[L]`
- [ ] 5 cycle trial: `--bench-root bench/silver/japan-travel/p3r-gate-trial`
- [ ] VP1/VP2/VP3 집계 → P3 Gate 판정
- [ ] P2 Gate 재판정 (P3R 완료 조건으로 연쇄 무효 해제)
- [ ] MEMORY.md D-120 해제, Phase Status 업데이트
