# Silver P3: Acquisition Expansion — Tasks
> Last Updated: 2026-04-12
> Status: 0/22

---

## P3-A. Provider 플러그인 (SEARCH)

- [ ] **P3-A1** `base.py`: SearchProvider Protocol + SearchResult dataclass `[S]`
- [ ] **P3-A2** `tavily_provider.py`: Tavily 이식 (fetch 제거) `[M]`
- [ ] **P3-A3** `ddg_provider.py`: DDG optional fallback `[M]`
- [ ] **P3-A4** `curated_provider.py`: preferred_sources 매칭 `[M]`
- [ ] **P3-A5** `search_adapter.py` retry 유틸로 축소 `[M]`

## P3-B. FetchPipeline (FETCH)

- [ ] **P3-B1** `FetchPipeline.fetch_many` `[L]`
- [ ] **P3-B2** `FetchResult` dataclass `[S]`
- [ ] **P3-B3** Robots.txt 캐시 (S8) `[M]`
- [ ] **P3-B4** Content-type 필터 `[S]`
- [ ] **P3-B5** max_bytes 절단 `[S]`
- [ ] **P3-B6** 도메인별 rate-limit `[M]`

## P3-C. Collect 리팩터 + Provenance + 비용

- [ ] **P3-C1** collect.py 3단계 리팩터 (SEARCH→FETCH→PARSE) `[L]`
- [ ] **P3-C2** 기존 fetch 직접호출 삭제 `[S]`
- [ ] **P3-C3** Provenance 필드 채움 (7필드) `[M]`
- [ ] **P3-C4** SearchConfig 7필드 확장 `[S]`
- [ ] **P3-C5** domain_entropy / provider_entropy emit `[M]`
- [ ] **P3-C6** 비용 가드 + degrade 모드 (S9) `[M]`

## P3-D. 의존성 + 테스트

- [ ] **P3-D1** pyproject.toml DDG optional `[S]`
- [ ] **P3-D2** Provider 테스트 ≥ 12 `[M]`
- [ ] **P3-D3** FetchPipeline 테스트 ≥ 10 (S8) `[M]`
- [ ] **P3-D4** Collect 통합 테스트 ≥ 6 (S9) `[M]`
- [ ] **P3-D5** search_adapter mig test `[S]`

---

## Phase Gate Process (필수 순서)

> 각 Phase 를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — `bench/silver/japan-travel/p3-{date}-acquisition/` trial 실행 (`run_readiness --bench-root ...`)
2. **결과 자가평가** — 정량 기준 (fetch ≥ 80%, EU/claim ≥ 1.8, entropy ≥ 2.5, 비용 ≤ 2×) + S8/S9 blocking scenario 확인
3. **Debug 루프** — bench 에서 발견된 이슈는 gate 통과 전 fix, `debug-history.md` 기록
4. **dev-docs 반영** — Phase Gate Checklist 체크, E2E Bench Results 실측값, plan.md Status 업데이트
5. **Gate 판정 commit** — `[si-p3] Gate PASS/FAIL: {근거}` 로 기록

## Phase Gate Checklist

- [ ] fetch 성공률 ≥ 80% on japan-travel seed queries
- [ ] claim 당 평균 EU ≥ 1.8
- [ ] domain_entropy ≥ 2.5 bits on ref cycle
- [ ] cycle 당 LLM 비용 ≤ baseline × 2.0
- [ ] robots.txt 거부 차단 (S8) pass
- [ ] cost budget degrade (S9) pass
- [ ] provenance KU/EU 저장→load 왕복 보존
- [ ] 테스트 수 ≥ 579 (P1 544 + 35)

---

## E2E Bench Results (Phase 종료 시 기록)

> Stage D 완료 후 실측값을 아래 테이블에 채움. Gate 판정의 정량 근거.

### Trial: `p3-{YYYYMMDD}-acquisition`

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Trial path | `bench/silver/japan-travel/p3-*-acquisition/` | — | — |
| Cycles run | ≥ 5 | — | — |
| fetch 성공률 | ≥ 80% | — | — |
| EU/claim 평균 | ≥ 1.8 | — | — |
| domain_entropy | ≥ 2.5 bits | — | — |
| LLM 비용 | ≤ baseline × 2.0 | — | — |
| robots.txt 차단 (S8) | pass | — | — |
| cost degrade (S9) | pass | — | — |
| provenance 왕복 | pass | — | — |
| Total tests | ≥ 579 | — | — |

**Gate 판정**: (미실행)
