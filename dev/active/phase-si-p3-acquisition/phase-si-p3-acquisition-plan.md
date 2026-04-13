# Silver P3: Acquisition Expansion
> Last Updated: 2026-04-13
> Status: **REVOKED — Gate 무효화 (LLM parse 경로 미검증, 실 벤치 0 claims 문제)**
> Source: `docs/silver-masterplan-v2.md` §4 P3 + §13, `docs/silver-implementation-tasks.md` §7

---

## 1. Summary (개요)

**목적**: snippet 의존 탈피, 소스 다양성 측정 가능화, 비용 가드.

현재 `collect.py` �� Tavily search → 상위 2 URL fetch (`search_tool.fetch`) → LLM 파싱 단일 경로.
문제:
1. Provider 가 Tavily 1개뿐 — fallback 없음, 소스 다양성 측정 불가
2. fetch 로직이 `collect.py` L88~L101 에 인라인 — robots.txt 미확인, content-type 미필터, max_bytes 미제한
3. provenance 스키마 없음 — 어떤 provider 에서 어떤 URL 을 가져왔는지 추적 불가
4. 비용 예산 개념 없음 — cycle 당 LLM/fetch 비용 제한 불가

**범위**:
- **Provider 플러그인** (`src/adapters/providers/`) — Tavily (기본) + DDG (optional fallback) + Curated (preferred_sources)
- **FetchPipeline** (`src/adapters/fetch_pipeline.py`) — robots.txt / content-type / max_bytes / trust_tier
- **collect.py 리팩터** — SEARCH → FETCH → PARSE 3단계 분리
- **Provenance 스키마** — provider/domain/fetch_ok/trust_tier 등 7개 필드
- **SearchConfig 확장** — 7개 신규 설정
- **다이버시티/비용 메트릭** — domain_entropy, provider_entropy, budget degrade

**예상 결과물**: fetch 80%+, EU/claim 1.8+, domain_entropy 2.5+ bits, 비용 ≤ baseline × 2.0, S8/S9 pass.

---

## 2. Current State (현재 상태)

### P0 + P1 완료 후 넘어온 것
- **544 tests**, P1 Gate PASS (S4/S5/S6)
- P0-X 인터페이스 고정: collect I/O shape (`current_claims`, `collect_failure_rate`), integrate I/O shape, provenance=None 예약
- `collect.py`: ThreadPoolExecutor 병렬, `_collect_single_gu` + `_parse_claims_deterministic`, search+fetch 인라인
- `search_adapter.py`: `TavilySearchAdapter` 단일 구현, `_retry_with_backoff`
- `SearchConfig`: provider/api_key/max_results/request_timeout 4필드
- Claim 에 `provenance: None` 필드 예약 (P0-X3)
- KU 에 `provenance: dict | None` 타입 선언 (state.py)

### 현 코드 문제점
1. `collect.py:88-101` — `search_tool.fetch(url)` 직접 호출, 상위 2 URL 만, 3000 chars 컷오프 없음
2. `src/adapters/providers/` — 디렉토리 부재
3. `src/adapters/fetch_pipeline.py` — 부재
4. robots.txt 체크 없음
5. 비용 예산 개념 없음
6. `domain_entropy` / `provider_entropy` 계산 없음

---

## 3. Target State (목표 상태)

- **3단계 수집 파이프라인**: SEARCH (providers) → FETCH (FetchPipeline) → PARSE (LLM/deterministic)
- **Provider 3개**: Tavily (기본) / DDG (optional, entropy_floor 미달 시) / Curated (preferred_sources)
- **FetchPipeline**: robots.txt 캐시, content-type 필터, max_bytes 절단, trust_tier 태깅, 도메인별 rate-limit
- **Provenance 완전 추적**: providers_used, domain, fetch_ok, fetch_depth, content_type, retrieved_at, trust_tier
- **비용 가드**: cycle_llm_token_budget + cycle_fetch_bytes_budget, 초과 시 degrade 모드
- **다이버시티 메트릭**: domain_entropy ≥ 2.5 bits, provider_entropy per cycle
- **S8/S9 scenario pass**
- **테스트 ≥ 579** (P1 544 + P3 35)

---

## 4. Implementation Stages

### Stage A: Provider 플러그인 — SEARCH 단계 (P3-A1 ~ P3-A5)

`src/adapters/providers/` 신설. SearchProvider Protocol + 3개 구현체 + search_adapter 축소.

1. **P3-A1** `base.py`: SearchProvider Protocol + SearchResult dataclass (`url, title, snippet, score, provider_id, trust_tier`). `[S]`
2. **P3-A2** `tavily_provider.py`: 기존 `TavilySearchAdapter.search` 이식, fetch 제거. `_retry_with_backoff` import 재사용. `[M]`
3. **P3-A3** `ddg_provider.py`: `duckduckgo-search` 사용, `trust_tier="secondary"`, `enable_ddg_fallback=True` 일 때만 호출. `[M]`
4. **P3-A4** `curated_provider.py`: 검색 안 함, skeleton `preferred_sources` 에서 axis_tags/category 매칭 URL 반환, `trust_tier="primary"`. `[M]`
5. **P3-A5** `search_adapter.py` → retry 유틸 제공자로 축소. 기존 `TavilySearchAdapter` 는 deprecated wrapper. `[M]`

### Stage B: FetchPipeline — FETCH 단계 (P3-B1 ~ P3-B6)

`src/adapters/fetch_pipeline.py` 신설. Provider 무관 공용 fetch 계층.

1. **P3-B1** `FetchPipeline.fetch_many(urls, *, robots_check, max_bytes, content_type_allowlist, timeout) -> list[FetchResult]`. `[L]`
2. **P3-B2** `FetchResult` dataclass: `url, fetch_ok, content_type, retrieved_at, bytes_read, trust_tier, failure_reason, body`. `[S]`
3. **P3-B3** Robots.txt 캐시 (in-memory, per-run). 거부 → `fetch_ok=False, failure_reason="robots"`. S8 핵심. `[M]`
4. **P3-B4** Content-type 필터: `{"text/html", "application/xhtml+xml"}`. 거부 → `failure_reason="content_type"`. `[S]`
5. **P3-B5** `max_bytes` 초과 시 자르기 (절단, `bytes_read < total_size`). `[S]`
6. **P3-B6** Rate-limit: 도메인별 최소 간격 (`per_domain_min_interval_s`). `[M]`

### Stage C: Collect 리팩터 + Provenance + 비용 (P3-C1 ~ P3-C6)

`collect.py` 3단계 분리 + provenance + diversity + cost guard.

1. **P3-C1** `collect.py` 리팩터: SEARCH (providers) → FETCH (FetchPipeline) → PARSE. 외부 인터페이스 (`current_claims`, `collect_failure_rate`) 보존. `[L]`
2. **P3-C2** 기존 `search_tool.fetch(url)` 직접 호출 삭제 — FetchPipeline 으로 완전 이관. `[S]`
3. **P3-C3** Claim/EU provenance 필드 채움: `{providers_used, domain, fetch_ok, fetch_depth, content_type, retrieved_at, trust_tier}`. `[M]`
4. **P3-C4** `SearchConfig` 7개 필드 확장: `enable_tavily`, `enable_ddg_fallback`, `fetch_top_n`, `max_bytes_per_url`, `entropy_floor`, `k_per_provider`, `per_domain_min_interval_s`. `[S]`
5. **P3-C5** 다이버시티 메트릭 per cycle: `domain_entropy`, `provider_entropy` (Shannon, log2, bits). metrics_logger emit. `[M]`
6. **P3-C6** 비용 가드: `cycle_llm_token_budget=100_000`, `cycle_fetch_bytes_budget=10_000_000`. 초과 시 `fetch_top_n--`, `k_per_provider--` degrade. S9 핵심. `[M]`

### Stage D: 의존성 + 테스트 (P3-D1 ~ P3-D5)

패키지 의존성 + 4개 테스트 모듈.

1. **P3-D1** `pyproject.toml` `duckduckgo-search` optional 의존성 추가. `[S]`
2. **P3-D2** Provider 테스트: tavily happy path, fallback, DDG gated, curated 동작. ≥ 12 테스트. `[M]`
3. **P3-D3** FetchPipeline 테스트: robots 거부 (S8), content-type, timeout, max_bytes, rate-limit. ≥ 10 테스트. `[M]`
4. **P3-D4** Collect 통합 테스트: mixed provider + provenance e2e + S9 (cost degrade). ≥ 6 테스트. `[M]`
5. **P3-D5** search_adapter legacy 테스트 경로 mig — provider 리팩터로 깨지지 않도록. `[S]`

---

## 5. Task Breakdown

| ID | Task | Size | Stage | 의존성 |
|----|------|------|-------|--------|
| P3-A1 | base.py Protocol + SearchResult | S | A | — |
| P3-A2 | tavily_provider.py | M | A | P3-A1 |
| P3-A3 | ddg_provider.py | M | A | P3-A1 |
| P3-A4 | curated_provider.py | M | A | P3-A1 |
| P3-A5 | search_adapter.py 축소 | M | A | P3-A2 |
| P3-B1 | FetchPipeline.fetch_many | L | B | — |
| P3-B2 | FetchResult dataclass | S | B | — |
| P3-B3 | Robots.txt 캐시 (S8) | M | B | P3-B1 |
| P3-B4 | Content-type 필터 | S | B | P3-B1 |
| P3-B5 | max_bytes 절단 | S | B | P3-B1 |
| P3-B6 | 도메인별 rate-limit | M | B | P3-B1 |
| P3-C1 | collect.py 3단계 리팩터 | L | C | P3-A2, P3-B1 |
| P3-C2 | 기존 fetch 직접호출 삭제 | S | C | P3-C1 |
| P3-C3 | Provenance 필드 채움 | M | C | P3-C1 |
| P3-C4 | SearchConfig 7필드 확장 | S | C | — |
| P3-C5 | domain_entropy / provider_entropy | M | C | P3-C1 |
| P3-C6 | 비용 가드 + degrade (S9) | M | C | P3-C4 |
| P3-D1 | pyproject.toml DDG optional | S | D | — |
| P3-D2 | Provider 테스트 ≥ 12 | M | D | P3-A1~A5 |
| P3-D3 | FetchPipeline 테스트 ≥ 10 (S8) | M | D | P3-B1~B6 |
| P3-D4 | Collect 통합 테스트 ≥ 6 (S9) | M | D | P3-C1~C6 |
| P3-D5 | search_adapter mig test | S | D | P3-A5 |

**Size 분포**: S: 7, M: 13, L: 2 → 총 22 tasks

---

## 6. Risks & Mitigation

| ID | 리스크 | L | I | 완화 |
|----|--------|---|---|------|
| R1 | fetch 확장 → LLM 비용 3~5× 증가 | H | H | cycle_llm_token_budget + cycle_fetch_bytes_budget + degrade 모드, baseline × 2.0 상한 |
| R2 | robots.txt / 저작권 위반 | M | H | robots.txt 캐시 체크, content-type 필터, trust_tier 차등, 공개 redistribute 금지 |
| R7 | DDG rate-limit / TOS 위반 | M | M | DDG 는 optional fallback 전용, 기본은 Tavily. gated by enable_ddg_fallback |
| P3-R1 | collect.py 리팩터 scope 커짐 | M | M | 외부 인터페이스 (return dict shape) 보존, P0-X2 동결 준수 |
| P3-R2 | FetchPipeline 네트워크 의존 테스트 불안정 | M | L | mock/fixture 기반 단위 테스트, real API 는 별도 smoke |
| P3-R3 | curated_provider skeleton preferred_sources ���재 | L | L | 빈 목록일 때 결과 0건 반환 (fallback safe) |

---

## 7. Dependencies

### 내부
| 모듈 | 의존 대상 |
|------|-----------|
| providers/*.py | `base.py` Protocol (P3-A1 선행) |
| `fetch_pipeline.py` | 독립 (P3-B2 FetchResult 만) |
| `collect.py` 리팩터 | providers + FetchPipeline (P3-A + P3-B 선행) |
| `SearchConfig` 확장 | `config.py` (독립) |
| 비용 가드 | `SearchConfig` (P3-C4 선행) + `metrics_guard.py` (P0-C4 HITL-E trigger) |

### 선행 Phase
- **P0 완료** (timeout/retry, P0-X 인터페이스 고정) ✅
- P1 과 병렬 가능 → P1 도 완료 ✅

### 후속 Phase 영향
- **P4**: provenance 필드 + domain_entropy 를 coverage deficit 분석에 활용
- **P5**: provenance + diversity 메��릭을 telemetry 스키마에 포함
- **P6**: multi-domain 에서 provider/fetch 동작 재검증

### 외부 패키지
| 패키지 | 용도 | 필수 |
|--------|------|------|
| `duckduckgo-search` | DDG provider | optional |
| `tavily-python` (기존) | Tavily provider | 기존 유지 |
| `urllib.robotparser` (stdlib) | robots.txt 파싱 | 표준 라이브러리 |
| `urllib.request` / `httpx` (후보) | FetchPipeline HTTP | 표준 or 기존 의존성 |

---

## 8. Phase Gate (정량, masterplan §4 verbatim)

- [x] fetch 성공률 ≥ 80% → **82.9%** (robots/미시도 제외)
- [ ] ~~claim 당 평균 EU ≥ 1.8 → **3.85**~~ **REVOKED** — deterministic fallback 결과이며 LLM parse 경로 미검증
- [x] `domain_entropy` ≥ 2.5 bits → **4.958** (41 domains)
- [ ] ~~cycle 당 LLM 비용 ≤ baseline × 2.0~~ **REVOKED** — 카운터 미연결 (D-111) + LLM parse 자체가 0 claims
- [x] robots.txt 거부 도메인 차단 테스트 pass → **21건 차단**
- [x] cost budget degrade 모드 동작 → **budget 메커니즘 확인**
- [x] provenance KU/EU 저장→load 왕복 보존 → **8필드 보존**
- [x] 테스트 ≥ 579 → **599**
- [ ] **[신규] LLM parse 경로 실제 API 검증** — SEARCH→FETCH→PARSE(LLM) 전체 경로에서 claims > 0 확인 필수

---

## 9. E2E Bench Results

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

### Regression vs P0 baseline

| 지표 | P0 baseline (p0-20260412, 15c) | P3 trial (5c) | 비고 |
|------|------|------|------|
| VP1 | 5/5 | 4/5 | R3_late_discovery (5 cycle 부족) |
| VP2 | 5/6 | 5/6 | R1_gap_resolution 미달 (5c vs 15c) |
| VP3 | 5/6 | 1/6 | audit 부족 (5c, interval=5→1회) |
| Active KU | 127 | 80 | 15c vs 5c 차이 |
| Tests | 544 | 599 | +55 (P3 신규) |

> VP regression은 5 cycle vs 15 cycle 차이에 의한 것. P3-specific gate 기준은 모두 PASS.

### 판정

- **Gate 결과**: ~~PASS~~ → **REVOKED** (2026-04-13)
- **원 판정 일시**: 2026-04-12
- **무효화 사유**: P2 실 벤치 trial에서 모든 GU에 대해 LLM parse 0 claims 반환 발견.
  P3 테스트가 전부 `llm=None`/`fetch_pipeline=None`으로 실행되어 deterministic fallback만 검증.
  실제 SEARCH→FETCH→PARSE(LLM) 통합 경로가 한 번도 검증되지 않았음.
  Phase gate 규칙 (실 데이터 E2E 검증 필수) 위반.
- **Debug**: D-110, D-111, **D-120 (LLM parse 0 claims — 아래 debug-history 참조)**
- **Gate Commit**: `1367df1` (무효)
- **Post-Gate 개선 Commit**: `5a516fc` (무효)
