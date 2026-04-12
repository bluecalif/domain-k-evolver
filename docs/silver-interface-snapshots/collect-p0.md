# collect_node — I/O Interface Snapshot (Silver P0)

> **Frozen at**: Silver P0 (phase-si-p0-foundation), 2026-04-12
> **Source**: `src/nodes/collect.py::collect_node` (commit `6c7f28f` 기준)
> **Purpose**: P1/P3 병렬 착수 시 collect_node 의 입력·반환 shape 이 흔들리지 않도록 동결.

---

## 1. Signature

```python
def collect_node(
    state: EvolverState,
    *,
    search_tool: Any | None = None,
    llm: Any | None = None,
    max_workers: int = 5,
) -> dict:
    ...
```

- **state**: `EvolverState` (TypedDict, `src/state.py`)
- **search_tool**: `search(query)` + `fetch(url)` 인터페이스 구현체. `None` → `{"current_claims": []}` 즉시 반환
- **llm**: LLM 인스턴스. `None` → `_parse_claims_deterministic` fallback
- **max_workers**: 병렬 스레드 수 (기본 5, 실제 = `min(max_workers, len(tasks))`)
- **반환**: `dict` — 아래 §3 참조 (LangGraph partial-state update)

---

## 2. Input — state 에서 읽는 키

| 키 | 타입 | 역할 | 필수 | 기본값 |
|----|------|------|------|--------|
| `current_plan` | `dict` | plan_node 출력: `target_gaps`, `queries`, `budget` | ✓ | `{}` |
| `gap_map` | `list[dict]` | GU 전체 (ID 조회용) | ✓ | `[]` |
| `current_mode` | `dict` | mode decision (`{"mode": "normal"\|"jump"}`) | ✓ | `{}` |

### 2.1 current_plan 최소 shape

```python
{
    "target_gaps": list[str],        # GU ID 목록 (수집 대상)
    "queries": dict[str, list[str]], # gu_id → 검색 쿼리 목록
    "budget": int | None,            # 총 검색 호출 예산 (None → 자동 계산)
}
```

### 2.2 search_tool 프로토콜

```python
class SearchToolProtocol:
    def search(self, query: str) -> list[dict]:
        """검색 결과 반환. 각 dict: url, title, snippet"""
        ...
    def fetch(self, url: str) -> str:
        """URL 콘텐츠 텍스트 반환"""
        ...
```

---

## 3. Output — 반환 dict 키

```python
{
    "current_claims": list[dict],     # 수집된 Claim 배열
    "collect_failure_rate": float,    # 실패 GU 비율 (0.0~1.0, 소수점 3자리)
}
```

### 3.1 Claim shape (`current_claims[i]`)

```python
{
    "claim_id": str,              # "CL-{gu_num}-{seq:02d}"
    "entity_key": str,            # GU target 에서 복사
    "field": str,                 # GU target 에서 복사
    "value": str,                 # 수집된 사실 주장
    "source_gu_id": str,          # 원본 GU ID
    "evidence": {
        "eu_id": str,             # "EU-{gu_num}-{seq:02d}"
        "url": str,
        "title": str,
        "snippet": str,
        "observed_at": "YYYY-MM-DD",
        "credibility": float,     # 0.0~1.0 (결정론적 fallback: 0.7)
    },
    "risk_flag": bool,            # HIGH_RISK_LEVELS 소속 여부
}
```

> **Note**: LLM 파싱 경로에서도 동일 shape 을 강제한다 (`_build_parse_prompt` Output Format 참조). LLM 이 추가 키를 반환하면 integrate_node 가 무시하므로 downstream 안전.

### 3.2 collect_failure_rate

- `failed_gu_count / total_gu_count` (소수점 3자리 round)
- task 가 0개일 때 `0.0`
- search_tool 이 None → `{"current_claims": []}` 반환 (failure_rate 키 생략)

---

## 4. 핵심 동작 규칙

1. **Budget guard**: `_compute_search_budget(plan, mode)` — target_gaps × 2 (+ jump 시 +4). 예산 초과 시 low/medium utility GU 스킵.
2. **병렬 수집**: `ThreadPoolExecutor`, `as_completed(timeout=120)`, 개별 `future.result(timeout=60)`.
3. **실패 처리**: per-GU `try/except` → `failed_gu_count++`. claim 을 빈 배열로 처리 (exception 전파 안 함).
4. **결정론적 fallback**: `_parse_claims_deterministic` — 검색 결과 상위 2건으로 Claim 2개 생성, credibility 고정 0.7.

---

## 5. 외부 의존

- `src/utils/llm_parse.py::extract_json` — LLM 응답 파싱 (import 는 함수 내부)
- `src/state.py::EvolverState` — TypedDict 정의
- `datetime.date.today()` — evidence observed_at

---

## 6. 호출부

- `src/graph.py` — `collect_node` 노드 등록 (`plan→collect→integrate→critique` flow)
- `src/orchestrator.py` — graph 실행, 반환 partial state 병합
- `scripts/run_one_cycle.py`, `scripts/run_bench.py` — orchestrator 호출

---

## 7. 변경 금지 영역 (P1/P3 주의)

P1 (Stability) 과 P3 (Acquisition Expansion) 는 아래 키·shape 을 **변경·삭제 금지**:

1. 반환 dict 의 2개 키 이름 (`current_claims`, `collect_failure_rate`)
2. Claim 최소 shape (§3.1 전체 필드)
3. Evidence 하위 6 필드 (`eu_id`, `url`, `title`, `snippet`, `observed_at`, `credibility`)
4. `search_tool` 프로토콜의 `search`/`fetch` 메서드 시그니처
5. `collect_failure_rate` 계산식 (failed_gu / total_gu)

**허용되는 확장:**
- Claim 에 `provenance` optional 필드 추가 (P0-X3 에서 예약)
- Evidence 에 `source_type` 추가 (P3 provider 별 라벨)
- `search_tool` 프로토콜에 optional 메서드 추가 (기존 2개 유지 필수)
- `collect_failure_rate` 외 추가 metric 키 반환

---

## 8. 검증 테스트 (현행 테스트 기준)

- `tests/test_nodes/test_collect.py` — budget guard, 병렬 수집, 실패 처리, deterministic fallback, malformed JSON fallback, collect_failure_rate
- `tests/test_adapters.py` — search_tool timeout/retry (search_adapter 단위)
- `tests/test_graph.py` — collect→integrate 흐름 내 partial-state 병합

Silver P0 누적 500 passed (commit `6c7f28f`) 시점에서 이 스냅샷과 일치.
