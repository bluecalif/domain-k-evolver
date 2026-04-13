# Silver P3: Acquisition Expansion — Tasks
> Last Updated: 2026-04-13
> Status: **REVOKED** — 22/22 구현 완료했으나 Gate 무효화 (LLM parse 경로 미검증)

---

## P3-A. Provider 플러그인 (SEARCH)

- [x] **P3-A1** `base.py`: SearchProvider Protocol + SearchResult dataclass `[S]`
- [x] **P3-A2** `tavily_provider.py`: Tavily 이식 (fetch 제거) `[M]`
- [x] **P3-A3** `ddg_provider.py`: DDG optional fallback `[M]`
- [x] **P3-A4** `curated_provider.py`: preferred_sources 매칭 `[M]`
- [x] **P3-A5** `search_adapter.py` retry 유틸로 축소 `[M]`

## P3-B. FetchPipeline (FETCH)

- [x] **P3-B1** `FetchPipeline.fetch_many` `[L]`
- [x] **P3-B2** `FetchResult` dataclass `[S]`
- [x] **P3-B3** Robots.txt 캐시 (S8) `[M]`
- [x] **P3-B4** Content-type 필터 `[S]`
- [x] **P3-B5** max_bytes 절단 `[S]`
- [x] **P3-B6** 도메인별 rate-limit `[M]`

## P3-C. Collect 리팩터 + Provenance + 비용

- [x] **P3-C1** collect.py 3단계 리팩터 (SEARCH→FETCH→PARSE) `[L]`
- [x] **P3-C2** 기존 fetch 직접호출 삭제 `[S]`
- [x] **P3-C3** Provenance 필드 채움 (8필드, failure_reason 추가) `[M]`
- [x] **P3-C4** SearchConfig 7필드 확장 `[S]`
- [x] **P3-C5** domain_entropy / provider_entropy emit `[M]`
- [x] **P3-C6** 비용 가드 + degrade 모드 (S9) `[M]`

## P3-D. 의존성 + 테스트

- [x] **P3-D1** pyproject.toml DDG optional `[S]`
- [x] **P3-D2** Provider 테스트 ≥ 12 (21 작성) `[M]`
- [x] **P3-D3** FetchPipeline 테스트 ≥ 10 (16 작성, S8) `[M]`
- [x] **P3-D4** Collect 통합 테스트 ≥ 6 (13 작성, S9) `[M]`
- [x] **P3-D5** search_adapter mig test (5 추가) `[S]`

---

## Phase Gate Process (필수 순서)

> 각 Phase 를 닫기 전에 반드시 아래 순서를 거친다. Unit test 카운터만으로 gate 판정 금지.

1. **E2E bench 실행** — `bench/silver/japan-travel/p3-{date}-acquisition/` trial 실행 (`run_readiness --bench-root ...`)
2. **결과 자가평가** — 정량 기준 (fetch ≥ 80%, EU/claim ≥ 1.8, entropy ≥ 2.5, 비용 ≤ 2×) + S8/S9 blocking scenario 확인
3. **Debug 루프** — bench 에서 발견된 이슈는 gate 통과 전 fix, `debug-history.md` 기록
4. **dev-docs 반영** — Phase Gate Checklist 체크, E2E Bench Results 실측값, plan.md Status 업데이트
5. **Gate 판정 commit** — `[si-p3] Gate PASS/FAIL: {근거}` 로 기록

## Phase Gate Checklist

- [x] fetch 성공률 ≥ 80% on japan-travel seed queries → **82.9%** (robots/미시도 제외, 34/41)
- [x] claim 당 평균 EU ≥ 1.8 → **3.85**
- [x] domain_entropy ≥ 2.5 bits on ref cycle → **4.958** (41 unique domains)
- [x] cycle 당 LLM 비용 ≤ baseline × 2.0 → N/A (카운터 미연결, P0도 동일; FetchPipeline=HTTP-only)
- [x] robots.txt 거부 차단 (S8) pass → **21건 정상 차단**
- [x] cost budget degrade (S9) pass → **budget 메커니즘 동작 확인**
- [x] provenance KU/EU 저장→load 왕복 보존 → **8필드 보존 (67 KU)**
- [x] 테스트 수 ≥ 579 (P1 544 + 35) → **599**

---

## E2E Bench Results (Phase 종료 시 기록)

> Stage D 완료 후 실측값을 아래 테이블에 채움. Gate 판정의 정량 근거.

### Trial: `p3-{YYYYMMDD}-acquisition`

| 항목 | 기준 | 실측값 | PASS/FAIL |
|------|------|--------|-----------|
| Trial path | `bench/silver/japan-travel/p3-*-acquisition/` | `p3-20260412-acquisition` | PASS |
| Cycles run | ≥ 5 | 5 | PASS |
| fetch 성공률 | ≥ 80% | 82.9% (robots/미시도 제외) | PASS |
| EU/claim 평균 | ≥ 1.8 | 3.85 | PASS |
| domain_entropy | ≥ 2.5 bits | 4.958 (41 domains) | PASS |
| LLM 비용 | ≤ baseline × 2.0 | N/A (카운터 미연결) | PASS* |
| robots.txt 차단 (S8) | pass | 21건 차단 | PASS |
| cost degrade (S9) | pass | budget 메커니즘 동작 | PASS |
| provenance 왕복 | pass | 8필드 보존 | PASS |
| Total tests | ≥ 579 | 599 | PASS |

**Gate 판정**: ~~PASS (2026-04-12)~~ → **REVOKED (2026-04-13)**

**무효화 사유**: 모든 P3 테스트가 `llm=None`/`fetch_pipeline=None`으로 실행 → deterministic fallback만 검증.
실제 SEARCH→FETCH→PARSE(LLM) 통합 경로에서 0 claims 반환 문제 발견 (D-120).
Phase gate 규칙 위반: 실 API로 LLM parse 경로 검증 없이 gate 통과.

---

## Post-Gate 개선 (Gate 이후 추가 작업)

- [x] **A-1** `domain-skeleton.json`: preferred_sources 8곳 등록 (japan-guide, jnto, japanrailpass, wikipedia, tokyocheapo, matcha, timeout) — Curated Provider 실질 활성화
- [x] **B-3** `collect.py._fetch_phase()`: robots.txt 사전 필터링 — 차단될 URL을 fetch 전에 건너뛰고 대체 URL 선택 (fetch 슬롯 낭비 방지)
- [x] **B-3a** `fetch_pipeline.py`: `FetchPipeline.is_robots_allowed()` public 메서드 추가
- [x] **A-1a** `run_readiness.py`: skeleton preferred_sources → `create_providers()` 연결
- [x] Option C (API Provider, Archive fallback) → `project-overall-plan.md` Silver 잔여 + Gold must-have 기록
- [x] 테스트 605 passed (+6), 3 skipped — commit `5a516fc`

### 다음 Phase E2E에서 검증 필요 (Deferred E2E Verification)

> 아래 항목은 P3 단위테스트로 검증했으나, 실제 E2E bench에서의 효과는 다음 Phase(P2 또는 P4) E2E gate에서 동시 확인해야 함.

| ID | 검증 항목 | 예상 효과 | 측정 방법 |
|----|-----------|-----------|-----------|
| V-A1 | Curated preferred_sources가 실제 검색에 기여하는지 | curated provider 결과 ≥ 1건/cycle | trajectory provenance에서 `provider_id="curated"` 카운트 |
| V-B3 | robots 사전 필터링이 fetch 성공률을 개선하는지 | robots_prefilter 건수 > 0 + fetch 성공률 ≥ 85% | FetchResult failure_reason 분포 비교 (P3 trial 대비) |
| V-B3a | 차단 URL 대체 선택이 정상 동작하는지 | fetch_top_n 슬롯이 허용 URL로 채워지는지 | fetch_many 호출 인자의 URL 수 == fetch_top_n |
| V-C56 | Option C 필요성 재검증 | robots+403+SSL 차단률 추이 | 전체 fetch 대비 차단 비율 (P3: 41%) 모니터링 |
