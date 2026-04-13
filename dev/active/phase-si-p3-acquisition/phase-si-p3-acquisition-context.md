# Silver P3: Acquisition Expansion — Context
> Last Updated: 2026-04-13
> Status: REVOKED (D-120 — LLM parse 0 claims)

---

## 0. Collect 파이프라인 실전 데이터 흐름

> 이 섹션은 D-120 근본 원인 분석을 위해 2026-04-13 실 벤치 1 cycle 결과를 기반으로 작성.
> **누구든 이 파이프라인의 실제 동작을 이해할 수 있도록** 가장 앞에 배치.

### 전체 흐름 (3단계)

```
Gap("JR Pass 가격이 빈칸이다")
         │
    ┌────▼─────────────────────────────┐
    │  STEP 1: SEARCH (Provider API)   │
    │  Tavily/DDG에 쿼리 전송           │
    │  → url + title + snippet 반환     │
    │  snippet = 검색엔진 요약 (1~2문장) │
    │  LLM 사용: ✗                      │
    └────┬─────────────────────────────┘
         │ SearchResult[] (보통 30건)
    ┌────▼─────────────────────────────┐
    │  STEP 2: FETCH (HTTP GET)        │
    │  상위 N개 URL에 순수 HTTP 요청     │
    │  → raw HTML body 반환 (최대 500KB)│
    │  robots.txt 체크 + rate-limit     │
    │  텍스트 추출 없음 — HTML 그대로    │
    │  LLM 사용: ✗                      │
    └────┬─────────────────────────────┘
         │ FetchResult[] (body = raw HTML)
    ┌────▼─────────────────────────────┐
    │  STEP 3: PARSE (LLM)            │
    │  LLM에게 전달:                    │
    │   - snippet (Sources, 상위 5개)   │
    │   - fetched_content[:3000]       │
    │  → "factual claims를 JSON으로"    │
    │  LLM 사용: ✓ (유일한 LLM 호출)    │
    └────┬─────────────────────────────┘
         │ Claim[] (구조화된 JSON)
         ▼
    integrate_node → KU 생성
```

### 실 벤치 데이터 (2026-04-13, 1 cycle)

| GU | fetched_len | snippet 수 | LLM resp_len | claims | 결과 |
|----|-------------|-----------|-------------|--------|------|
| GU-0001 | 552,538 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0002 | 552,538 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0003 | 681,126 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0004 | 552,538 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0005 | 681,126 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0006 | 552,538 | 30/30 | 2 (`[]`) | 0 | **실패** |
| GU-0007 | 261,498 | 30/30 | 1,768 | 6 | 성공 |
| GU-0008 | 161,959 | 30/30 | 1,697 | 6 | 성공 |
| GU-0009 | 147,159 | 30/30 | 2,107 | 7 | 성공 |
| GU-0010 | 147,159 | 30/30 | 2,137 | 7 | 성공 |

### D-120 근본 원인 (확정)

**이전 가설 (틀림)**: fetch body가 비어서 LLM이 claim을 못 뽑음.

**실제 원인**: fetch body는 정상 수신(550KB+)되지만, **raw HTML 그대로** 저장됨.
- `fetch_pipeline.py`에서 `raw.decode("utf-8")` → HTML 태그, CSS, JS 포함
- `_build_parse_prompt()`에서 `fetched_content[:3000]` 절단 → **`<html><head><script>...` 쓰레기**
- LLM이 이 HTML 쓰레기에서 factual claims를 못 뽑고 `[]` 반환
- 상대적으로 **짧고 깨끗한 HTML**(~160KB)을 가진 사이트는 claims 추출 성공

### 필요한 수정

**핵심**: FETCH → PARSE 사이에 **HTML → plain text 변환 단계** 추가.
- `BeautifulSoup`의 `get_text()` 또는 유사 lightweight 텍스트 추출
- `<script>`, `<style>`, `<nav>` 등 노이즈 태그 제거
- 변환 후 텍스트를 prompt에 전달 → LLM이 실제 콘텐츠 기반으로 claims 추출 가능

---

## 1. 핵심 파일

### 읽어야 할 기존 코드
| 파일 | 내용 | 참조 이유 |
|------|------|-----------|
| `src/nodes/collect.py` | Claims 수집 노드 | 3단계 리팩터 대상 (전면 수정) |
| `src/adapters/search_adapter.py` | TavilySearchAdapter + retry | provider 이식 원본 + retry 유틸 재사용 |
| `src/tools/search.py` | SearchTool Protocol | 기존 인터페이스 확인 |
| `src/config.py` | SearchConfig | 7필드 확장 대상 |
| `src/state.py` | EvolverState + KU provenance 타입 | provenance 필드 타입 확인 |
| `src/utils/metrics_logger.py` | 사이클별 메트릭 emit | diversity 메트릭 추가 위치 |
| `src/utils/metrics_guard.py` | HITL-E trigger | cost_regression_flag 연동 |

### 신규 작성 파일
| 파일 | 내용 |
|------|------|
| `src/adapters/providers/__init__.py` | 패키��� 초기화 |
| `src/adapters/providers/base.py` | SearchProvider Protocol + SearchResult |
| `src/adapters/providers/tavily_provider.py` | Tavily 구현체 |
| `src/adapters/providers/ddg_provider.py` | DuckDuckGo optional 구현체 |
| `src/adapters/providers/curated_provider.py` | Curated sources 구현체 |
| `src/adapters/fetch_pipeline.py` | FetchPipeline + FetchResult |
| `tests/test_adapters/test_providers/` | Provider 테스트 12+ 건 |
| `tests/test_adapters/test_fetch_pipeline.py` | FetchPipeline 테스트 10+ 건 |

### 수정 파일
| 파일 | 수정 내용 |
|------|-----------|
| `src/nodes/collect.py` | 3단계 리팩터 + **B-3 robots 사전 필터링** |
| `src/config.py` | SearchConfig 7필드 추가 |
| `src/adapters/search_adapter.py` | deprecated wrapper 로 축소 |
| `src/adapters/fetch_pipeline.py` | **B-3a `is_robots_allowed()` public 메서드 추가** |
| `src/utils/metrics_logger.py` | domain_entropy / provider_entropy emit |
| `pyproject.toml` | duckduckgo-search optional |
| `scripts/run_readiness.py` | **A-1a skeleton preferred_sources → create_providers 연결** |
| `bench/japan-travel/.../domain-skeleton.json` | **A-1 preferred_sources 8곳 등록** |
| `tests/test_nodes/test_collect.py` | 통합 테스트 추가 |

---

## 2. 데이터 인터페이스

### SEARCH 단계 (Provider → SearchResult)
```python
@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    score: float            # 0.0~1.0, provider 가 부여
    provider_id: str        # "tavily" | "ddg" | "curated"
    trust_tier: str         # "primary" | "secondary" | "tertiary"
```

### FETCH 단계 (FetchPipeline → FetchResult)
```python
@dataclass
class FetchResult:
    url: str
    fetch_ok: bool
    content_type: str       # "text/html" etc.
    retrieved_at: str       # ISO date
    bytes_read: int
    trust_tier: str
    failure_reason: str     # "" | "robots" | "content_type" | "timeout" | "error"
    body: str               # 실�� 콘텐츠 (max_bytes 절단 후)
```

### PARSE 단계 (collect_node 출력 — P0-X2 동결)
```python
{
    "current_claims": list[dict],      # 기존 shape 유지
    "collect_failure_rate": float,     # 기존 shape 유지
}
```

### Provenance 필드 (Claim/EU 내부)
```python
{
    "providers_used": ["tavily", "ddg"],
    "domain": "japan-travel.info",
    "fetch_ok": True,
    "fetch_depth": 1,
    "content_type": "text/html",
    "retrieved_at": "2026-04-12",
    "trust_tier": "primary",
}
```

### SearchConfig 확장 (P3-C4)
```python
@dataclass(frozen=True)
class SearchConfig:
    # 기존
    provider: str = "tavily"
    api_key: str = ""
    max_results: int = 5
    request_timeout: int = 30
    # P3 신규
    enable_tavily: bool = True
    enable_ddg_fallback: bool = False
    fetch_top_n: int = 5
    max_bytes_per_url: int = 512_000
    entropy_floor: float = 2.0
    k_per_provider: int = 3
    per_domain_min_interval_s: float = 1.0
```

### 비용 가드 (P3-C6)
```python
cycle_llm_token_budget: int = 100_000
cycle_fetch_bytes_budget: int = 10_000_000
```
초과 시: `fetch_top_n -= 1`, `k_per_provider -= 1` → `cost_regression_flag=True` → HITL-E trigger.

---

## 3. 주요 결정사항

| # | 결정 | 근거 |
|---|------|------|
| D-73 | Provider 3개: Tavily 기본 + DDG optional + Curated | masterplan §13 verbatim. DDG 는 entropy_floor 미달 시만 |
| D-74 | SEARCH / FETCH / PARSE 3단계 분리 | collect.py 에 인라인 fetch 제거, ���일 책임 분리 |
| D-78 | 비용 가드 — budget + degrade 모드 | R1 완화. baseline × 2.0 상한 |
| D-100 | FetchPipeline 은 `urllib.request` 기반 (httpx 미도입) | 외부 의존성 최소화, stdlib 충분 |
| D-101 | robots.txt 캐시는 per-run in-memory (파일 캐시 아님) | Silver 규모에서 충분, 복잡도 최소 |
| D-102 | CuratedSourceProvider 의 preferred_sources 는 skeleton 필드 | 도메인 설정 파일에 포함, 코드 변경 없이 도메인별 커스텀 |
| D-103 | collect_node 외부 인터페이스 보존 (P0-X2) | return dict shape 미변경, 내부만 리팩터 |
| D-112 | robots.txt 사전 필터링 (B-3) — fetch 전에 차단 URL 건너뛰기 | fetch 슬롯 낭비 방지, 대체 URL 선택으로 실질 성공률 개선 |
| D-113 | Option C (API Provider / Archive fallback) — Silver 잔여 + Gold must-have 기록 | robots 차단 31% 근본 대응은 API 접근 필요, 현 단계에서는 기록만 |

---

## 4. 컨벤션 체크리스트

### 5대 불변원칙
- [ ] **Gap-driven**: Plan.target_gaps 변경 없음 — collect 는 Plan 의 queries 를 소비할 뿐
- [ ] **Claim→KU 착지성**: provenance 추가되어도 claim → integrate 경로 불변
- [ ] **Evidence-first**: fetch 확장으로 EU 품질 개선 (fetch_ok + trust_tier 추적)
- [ ] **Conflict-preserving**: P3 변경 없음
- [ ] **Prescription-compiled**: P3 변경 없음

### Metrics 건강 임계치 (P3 신규)
| 지표 | 건강 | 주의 | 위험 |
|------|------|------|------|
| fetch 성공률 | ≥ 0.80 | 0.60~0.79 | < 0.60 |
| domain_entropy | ≥ 2.5 bits | 1.5~2.4 | < 1.5 |
| EU/claim | ≥ 1.8 | 1.2~1.7 | < 1.2 |
| cycle LLM 비용 | ≤ baseline × 2.0 | 2.0~3.0× | > 3.0× |

### Blocking Scenarios
- **S8**: robots.txt ���단 도메인 → fetch 스킵 + 로그, 다른 소스 대체 → `test_robots_refusal`
- **S9**: 비용 budget 초과 → degrade 모드 (fetch_top_n↓) → `test_cost_budget_degrade`

### 인코딩
- fetch 된 HTML body: `encoding='utf-8'` 강제 (charset 헤더 무시 시 fallback)
- provenance JSON: `encoding='utf-8'` 명시

### 코드 컨벤션
- Provider 는 Protocol 기반 (duck typing, ABC 아님)
- FetchResult/SearchResult 는 `@dataclass` (TypedDict 아님 — 내부 전용)
- collect_node 반환 shape 미변경 (P0-X2 동결)
