---
name: silver-provider-fetch
description: Domain-K-Evolver Silver P3 (Acquisition Expansion) — SearchProvider 플러그인 (Tavily / DDG / Curated) + 공용 FetchPipeline + collect_node 3 단계 분리 (SEARCH/FETCH/PARSE) + provenance 필드 + 비용 가드 구현 가이드. masterplan v2 §13 verbatim. `src/adapters/providers/`, `src/adapters/fetch_pipeline.py`, `collect.py` 리팩터 작업이거나 "provider 플러그인", "tavily 분리", "ddg fallback", "curated source", "fetch pipeline", "robots.txt 처리", "domain entropy", "fetch 성공률", "provenance 필드", "비용 budget", "degrade 모드" 같은 P3 관련 요청이 나오면 반드시 사용한다. Bronze 의 `search_adapter.py` 를 그대로 쓰는 작업이나 P3 외 다른 Phase 작업에는 사용하지 않는다.
---

# Silver Provider & Fetch Pipeline

## 목적

Bronze 의 `search_adapter.py` 는 SEARCH 와 FETCH 가 한 클래스 안에 섞여 있어 (a) provider 다양화 불가, (b) robots/timeout 가드 산재, (c) provenance 추적 어려움 — 이 3 가지 문제가 P3 의 deliverable 모두에 영향을 준다.

P3 의 핵심은 "fetch 가 어느 provider 에 속한다" 는 v2 초안의 혼란을 정리하고, **collect 흐름을 3 단계로 명시 분리** 하는 것이다. 이 skill 은 그 분리 구조와 인터페이스 계약을 제공한다.

masterplan v2 §13 이 단일 진실 소스다.

## 언제 쓰는가

- P3-A 작업 (SearchProvider Protocol + 3 구현)
- P3-B 작업 (FetchPipeline)
- P3-C 작업 (collect.py 리팩터 + provenance + 비용 가드)
- P3-D 작업 (provider/fetch 테스트)
- "왜 fetch 를 provider 밖으로 빼나?" 라는 질문에 답할 때
- P3 gate 가 FAIL 났을 때 (`silver-phase-gate-check` 와 함께)

## 언제 쓰지 않는가

- Bronze `search_adapter.py` 를 그대로 사용하는 디버깅
- P0~P2, P4~P6 의 작업 (도메인이 다름)
- WebSearch/WebFetch 도구의 일반적인 사용법 (이건 `langgraph-dev`)
- skeleton 의 `preferred_sources` 데이터 작성 (이건 도메인 작업, P0/P6)

---

## 핵심 분리 — SEARCH / FETCH / PARSE

v2 초안은 "provider" 와 "fetch" 를 한 추상에 넣어 혼란을 유발했다. 실제 collect 흐름은 3 단계이며, **provider 는 Step 1 만 책임진다.**

```
Step 1. SEARCH  : query → [SearchResult]          (provider 의 책임)
Step 2. FETCH   : url → body                      (공용 FetchPipeline 의 책임)
Step 3. PARSE   : (results + bodies) → claims    (collect_node 의 책임)
```

이 분리는 다음을 가능하게 한다:
- provider 추가 시 fetch 정책 (robots/timeout/max_bytes) 을 한 곳에서 일관 적용
- `CuratedSourceProvider` 처럼 검색 안 하는 provider 도 같은 인터페이스 사용
- provenance 가 SEARCH/FETCH/PARSE 어느 단계에서 무엇을 했는지 분리 기록

**개명 근거**: v2 초안의 `FetchOnlyProvider` 라는 이름은 "provider 가 fetch 를 한다" 고 읽혀 Step 1/Step 2 경계를 흐린다. `CuratedSourceProvider` 는 "큐레이션된 소스 제공자 = 검색 안 하고 이미 알려진 URL 을 돌려준다" 는 의도가 명확하다. FetchPipeline 은 그 뒤에 공용 단계로 작동하므로 **어떤 provider 도 fetch 를 "소유" 하지 않는다.**

---

## SearchProvider 인터페이스 (§13.2 verbatim)

```python
from typing import Protocol
from dataclasses import dataclass

class SearchProvider(Protocol):
    provider_id: str  # "tavily" | "ddg" | "curated"

    def search(
        self,
        query: str,
        k: int,
        context: PlanContext,  # category, axis_tags, cycle
    ) -> list[SearchResult]: ...


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str       # 제공사 제공 요약 (없으면 "")
    score: float       # provider 고유 랭킹, 0~1 정규화
    provider_id: str
    trust_tier: str    # "primary" | "secondary" | "community"
```

이 Protocol 은 P0-X3 에서 **stub 로 미리 선언**된다 (P3/P5 인터페이스 동결). P3 에서 실제 구현을 채운다.

## 3 개 구현 (§13.3 verbatim)

| Provider | 동작 | 사용 트리거 | trust_tier 기본 | 비용 | Rate limit |
|----------|------|-------------|-----------------|------|------------|
| **TavilyProvider** (기본) | Tavily API, LLM 친화적 snippet, `search_adapter.py` 의 `_retry_with_backoff` 재사용 | 모든 cycle 기본 활성 | allowlist (gov/official → primary, 그 외 secondary) | 월 크레딧 유료 | 초·월 |
| **DuckDuckGoProvider** (optional) | `duckduckgo-search` 라이브러리, HTML scraping, API key 없음 | (a) Tavily 실패 fallback, (b) `domain_entropy < entropy_floor` 일 때 다양성 보강 | secondary | free | 엄격 (IP 기반), **기본 off** |
| **CuratedSourceProvider** (`FetchOnlyProvider` 개명) | **검색 안 함**. skeleton `preferred_sources` 중 `context.axis_tags`/`category` 매칭 URL 반환. `snippet="curated"`, `score=1.0` | `preferred_sources` 가 정의된 category 조회 시 항상 우선 | primary | free | 사실상 없음 (공식 사이트 ToS) |

**핵심 제약**:
- `tavily_provider.py` 는 fetch 를 **하지 않는다**. `search_adapter.py` 의 `fetch` 메소드는 P3-C2 에서 삭제되고 FetchPipeline 으로 이관된다.
- `ddg_provider.py` 는 `policy.enable_ddg_fallback` 이 true 이고 fallback 트리거가 발동했을 때만 호출. 기본 cycle 호출 금지.
- `curated_provider.py` 는 외부 호출 0 회 — skeleton 이 dict lookup 의 전부.

---

## FetchPipeline (§13.4 Step 5 + P3-B)

```python
class FetchPipeline:
    def fetch_many(
        self,
        urls: list[str],
        *,
        robots_check: bool,
        max_bytes: int,
        content_type_allowlist: set[str],
        timeout: float,
    ) -> list[FetchResult]: ...


@dataclass
class FetchResult:
    url: str
    fetch_ok: bool
    content_type: str          # "" if failed
    retrieved_at: str          # ISO8601
    bytes_read: int
    body: bytes | None         # None if failed or filtered
    trust_tier: str            # provider 가 정한 값을 그대로 운반
    failure_reason: str | None # "robots" | "content_type" | "timeout" | "http_5xx" | None
```

### 가드 계층 (P3-B3~B6)

| 가드 | 기본값 | 거부 처리 |
|------|--------|-----------|
| **Robots.txt** | `robots_check=True` | in-memory 캐시 (per-run), 거부 도메인 즉시 `fetch_ok=False, failure_reason="robots"` |
| **Content-type allowlist** | `{"text/html", "application/xhtml+xml"}` | 미허용 시 `failure_reason="content_type"` |
| **max_bytes** | `policy.max_bytes_per_url` | 초과 시 자르기. `failure_reason` 이 아니라 `bytes_read < total_size` 로 표현, `trust_tier` 유지 |
| **Timeout** | `config.search.request_timeout` | `failure_reason="timeout"` |
| **Rate-limit** | 도메인별 최소 간격 (config 값) | 간격 미달 시 대기 → 그래도 못 맞추면 fail |

**중요**: `max_bytes` 초과는 **failure 가 아니다** — 자른 본문도 PARSE 단계에서 사용 가능. failure 는 통신/정책 실패만.

---

## collect_node 호출 패턴 (§13.4 verbatim)

```python
def collect_node(state: EvolverState) -> dict:
    gu = state["current_gap"]
    ctx = PlanContext(
        category=gu["category"],
        axis_tags=gu.get("axis_tags", []),
        cycle=state["current_cycle"],
    )
    query = build_query(gu)

    # 1. Provider 선택 (policy 기반)
    providers: list[SearchProvider] = [CuratedSourceProvider(state["domain_skeleton"])]
    if policy.enable_tavily:
        providers.append(TavilyProvider(config.search))

    # 2. 검색 병렬 실행
    all_results: list[SearchResult] = []
    for p in providers:
        try:
            all_results.extend(p.search(query, k=policy.k_per_provider, context=ctx))
        except ProviderError as e:
            logger.warning("provider %s failed: %s", p.provider_id, e)

    # 3. 다양성 부족 시 DDG fallback
    if domain_entropy(all_results) < policy.entropy_floor and policy.enable_ddg_fallback:
        all_results.extend(
            DuckDuckGoProvider().search(query, k=3, context=ctx)
        )

    # 4. URL dedupe + top-N 선정
    urls = dedupe_and_rank(all_results, top_n=policy.fetch_top_n)

    # 5. FETCH 파이프라인 (provider 무관, 공용 단계)
    bodies = FetchPipeline().fetch_many(
        urls,
        robots_check=True,
        max_bytes=policy.max_bytes_per_url,
        content_type_allowlist={"text/html", "application/xhtml+xml"},
        timeout=config.search.request_timeout,
    )

    # 6. PARSE — claims 추출 + provenance 태깅
    claims = parse_claims(
        gu, all_results, bodies,
        provenance={
            "providers_used": [p.provider_id for p in providers],
            "fetch_ok_count": sum(1 for b in bodies if b.fetch_ok),
            "domain_set": sorted({urlparse(r.url).netloc for r in all_results}),
        },
    )
    return {"current_claims": claims}
```

이 패턴은 §13.4 verbatim. 변형 시 §13 과의 정합성을 먼저 확인할 것.

---

## Provenance 필드 (P3-C3)

Bronze 의 Claim/EU 에는 provenance 가 부분적으로만 있었다. Silver 에서 다음을 명시 필드로 추가:

```python
@dataclass
class Provenance:
    providers_used: list[str]    # ["tavily", "curated"]
    domain: str                  # "japan-guide.com"
    fetch_ok: bool
    fetch_depth: int             # 0 = snippet only, 1 = full page fetched
    content_type: str            # "text/html"
    retrieved_at: str            # ISO8601
    trust_tier: str              # "primary" | "secondary" | "community"
```

**P0-X3 의 역할**: P0 시점에 Claim/EU dataclass 에 `provenance: Provenance | None = None` 을 **optional 로 미리 선언**한다. P3 에서 실제 채운다. 스키마 역전 방지.

State save/load 왕복에서 provenance 가 보존되어야 한다 (P3 gate 항목).

---

## SearchConfig 확장 (P3-C4)

```python
@dataclass
class SearchConfig:
    # 기존
    request_timeout: float
    max_retries: int

    # Silver P3 신규
    enable_tavily: bool = True
    enable_ddg_fallback: bool = False
    fetch_top_n: int = 5
    max_bytes_per_url: int = 200_000
    entropy_floor: float = 1.5      # domain_entropy 이 이하일 때 fallback 발동
    k_per_provider: int = 5
    cycle_llm_token_budget: int = 100_000
    cycle_fetch_bytes_budget: int = 5_000_000
```

---

## 비용 가드 + Degrade 모드 (P3-C6, S9)

cycle 시작 시점에 비용 예산을 0 에서 시작, node 호출마다 누적. 임계 도달 시:

```python
def check_budget_and_degrade(state, config):
    tokens = state["metrics"]["llm_tokens_per_cycle"]
    bytes_ = state["metrics"]["fetch_bytes_per_cycle"]

    if tokens > config.cycle_llm_token_budget:
        state["cost_regression_flag"] = True
        # → silver-hitl-policy 의 HITL-E 트리거 후보
    if bytes_ > config.cycle_fetch_bytes_budget:
        # Degrade 모드: fetch_top_n 절반, max_bytes_per_url 절반
        config.search.fetch_top_n = max(1, config.search.fetch_top_n // 2)
        config.search.max_bytes_per_url //= 2
        logger.warning("budget exceeded, entering degrade mode")
```

**Degrade 는 cycle 내에서 즉시 적용**, 다음 cycle 시작 시 원복. 항구적 변경이 필요하면 audit/policy 경로로 (P4 이후).

S9 scenario 는 이 동작이 실제 일어나는지 검증한다 — `silver-phase-gate-check` 의 P3 항목.

---

## P3 추가 파일 (§13.6)

```
src/adapters/
├── search_adapter.py            # retry 유틸 제공자로 축소 (또는 deprecated wrapper)
├── llm_adapter.py               # 변경 없음
├── fetch_pipeline.py            # NEW
└── providers/
    ├── __init__.py              # NEW
    ├── base.py                  # NEW — SearchProvider Protocol + SearchResult
    ├── tavily_provider.py       # NEW — search_adapter.py 의 search 로직 이식
    ├── ddg_provider.py          # NEW — duckduckgo-search 사용
    └── curated_provider.py      # NEW — preferred_sources lookup
```

`pyproject.toml`:
- 추가: `duckduckgo-search` (optional)
- 유지: `tavily-python`

---

## 다이버시티 메트릭 (P3-C5)

cycle 별 emit:

```python
state["metrics"]["domain_entropy"]   = shannon_entropy([urlparse(r.url).netloc for r in all_results])
state["metrics"]["provider_entropy"] = shannon_entropy([r.provider_id for r in all_results])
state["metrics"]["fetch_failure_rate"] = sum(not b.fetch_ok for b in bodies) / max(1, len(bodies))
```

P3 gate 의 `domain_entropy ≥ 2.5 bits` 는 이 값을 본다.

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|------|------|------|
| `tavily_provider.py` 안에 fetch 호출 | SEARCH/FETCH 분리 위반 | fetch 는 FetchPipeline 으로만 |
| `CuratedSourceProvider` 가 외부 HTTP 호출 | "검색 안 함" 원칙 위반 | skeleton lookup 만 |
| `ddg_provider` 를 매 cycle 호출 | rate-limit 위반 + 비용 폭증 (R7) | `enable_ddg_fallback` + entropy_floor 게이팅 |
| robots 거부 도메인을 silently fail 처리 | S8 scenario fail, R2 리스크 | `failure_reason="robots"` 명시 + 메트릭 emit |
| `max_bytes` 초과를 failure 로 처리 | parse 단계에서 본문 못 씀 | `bytes_read` 로 표현, `fetch_ok=True` 유지 |
| provenance 를 dict 로 즉석 생성 | 스키마 깨짐, 라운드트립 손실 | `Provenance` dataclass + P0-X3 사전 선언 |
| Degrade 모드를 cycle 종료 후에도 유지 | 다음 cycle 의 비용 측정 무효화 | cycle 시작 시 원복 |
| `search_adapter.py` 를 그대로 import | 리팩터 의도 무력화 | provider 경유, search_adapter 는 retry 유틸만 |
| LLM 비용 추적 없이 budget 가드 작성 | budget 항상 0 → 발동 안 함 | `metrics_logger` 와 emit 계약 먼저 확정 |

---

## 관련

- **masterplan v2 §13** — 단일 진실 소스. 충돌 시 §13 가 옳다.
- **masterplan v2 §8 R1, R2, R7** — 비용/저작권/alt-provider rate-limit 리스크.
- **silver-implementation-tasks.md §7 P3** — 22 개 task (P3-A1~D5) 가 이 skill 의 직접 적용 대상.
- **silver-phase-gate-check** — P3 gate (fetch ≥ 80%, EU/claim ≥ 1.8, entropy ≥ 2.5, 비용 ≤ 2×) 채점.
- **silver-hitl-policy** — `cost_regression_flag` 가 HITL-E 트리거의 5 개 조건 중 하나.
- **`evolver-framework` skill** — Evidence-first 원칙 (provenance 가 EU 의 핵심 필드).
- **`langgraph-dev` skill** — collect_node 의 LangGraph 통합 패턴.
