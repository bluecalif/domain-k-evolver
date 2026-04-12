# integrate_node — I/O Interface Snapshot (Silver P0)

> **Frozen at**: Silver P0 (phase-si-p0-foundation), 2026-04-12
> **Source**: `src/nodes/integrate.py::integrate_node` (commit `6c7f28f` 기준)
> **Purpose**: P1/P3 병렬 착수 시 integrate_node 의 입력·반환 shape 이 흔들리지 않도록 동결. 이 문서를 변경하려면 Silver P0 후속 task 로 명시적 decision 필요.

---

## 1. Signature

```python
def integrate_node(
    state: EvolverState,
    *,
    llm: Any | None = None,
) -> dict:
    ...
```

- **state**: `EvolverState` (TypedDict, `src/state.py`)
- **llm**: 선택적 LLM 인스턴스. `None` 이면 결정론적 fallback (`_detect_conflict` Rule-only)
- **반환**: `dict` — 아래 §3 참조 (LangGraph partial-state update)

---

## 2. Input — state 에서 읽는 키

| 키 | 타입 | 역할 | 필수 | 기본값 |
|----|------|------|------|--------|
| `current_claims` | `list[dict]` | 이번 cycle 에서 수집된 Claim 목록 | ✓ | `[]` |
| `knowledge_units` | `list[dict]` | 기존 KU 전체 | ✓ | `[]` |
| `gap_map` | `list[dict]` | 기존 GU 전체 | ✓ | `[]` |
| `domain_skeleton` | `dict` | 카테고리/필드/축 스키마 | ✓ | `{}` |
| `current_mode` | `dict` | mode decision (`{"mode": "normal"\|"jump", ...}`) | ✓ | `{}` |
| `dispute_queue` | `list[dict]` | Silver HITL-D 큐 (비블로킹 append 대상) | ✓ | `[]` |
| `policies` | `dict` | `ttl_defaults` 등 (stale refresh 시 사용) | - | `{}` |
| `current_cycle` | `int` | dispute_queue append 시 기록 | - | `0` |

### 2.1 Claim 최소 shape (`current_claims[i]`)

```python
{
    "claim_id": str,
    "entity_key": str,            # 정규화 전 (integrate 내부에서 lower+hyphen 처리)
    "field": str,
    "value": Any,                 # 주로 str
    "evidence": {
        "eu_id": str,
        "credibility": float,     # 0.0~1.0, 기본 0.7
        "source_type": str | None,
    },
    "source_gu_id": str,          # 해결 대상 GU (없으면 "")
    "conditions": dict | None,    # 있으면 condition_split 가능
}
```

통합 후 `claim["integration_result"]` 키가 추가된다:
`"added" | "updated" | "condition_split" | "conflict_hold" | "refreshed"`

### 2.2 KU 최소 shape (`knowledge_units[i]`)

```python
{
    "ku_id": "KU-####",           # 0-padded 4자리
    "entity_key": str,
    "field": str,
    "value": Any,
    "conditions": dict | None,
    "observed_at": "YYYY-MM-DD",
    "validity": {"ttl_days": int},
    "evidence_links": list[str],  # eu_id 목록
    "confidence": float,          # 0.0~0.95 (boost 상한)
    "status": "active" | "disputed",
    "disputes": list[dict] | None,
    "axis_tags": dict | None,     # 최소 {"geography": str}
    "source_type": str | None,
}
```

### 2.3 GU 최소 shape (`gap_map[i]`)

```python
{
    "gu_id": "GU-####",
    "gap_type": "missing" | "stale" | ...,
    "target": {"entity_key": str, "field": str},
    "expected_utility": str,
    "risk_level": str,
    "resolution_criteria": str,
    "status": "open" | "resolved",
    "trigger": str,               # 동적 GU 는 "A:adjacent_gap"
    "trigger_source": str,        # claim_id
    "created_at": "YYYY-MM-DD",
    "axis_tags": dict | None,
    "resolved_by": str | None,    # 해결한 claim_id
    "expansion_mode": "jump" | None,
}
```

---

## 3. Output — 반환 dict 키

```python
{
    "knowledge_units": list[dict],  # kus (in-place 수정 + 신규 append)
    "gap_map": list[dict],          # gap_map (resolved 마킹 + 동적 GU append)
    "current_claims": list[dict],   # integration_result 주입된 claims
    "dispute_queue": list[dict],    # conflict_hold 발생 시 append
}
```

**보장 사항 (불변):**
- 반환 dict 에는 위 4개 키만 존재. P0 시점 LangGraph partial-update 로 state 병합.
- `knowledge_units` 는 입력 대비 길이 ≥ 입력 (삭제 없음, Conflict-preserving)
- 신규 active KU 는 `evidence_links` 길이 ≥ 1 (Evidence-first, `assert` 로 강제)
- `dispute_queue` 는 append-only. 삭제는 외부 (dispute_resolver) 에서만.
- `current_claims` 의 개수는 입력과 동일. 각 element 에 `integration_result` 추가.

---

## 4. 외부 의존

- `src/utils/llm_parse.py::extract_json` — LLM 응답 파싱
- `src/state.py::EvolverState` — TypedDict 정의
- `datetime.date.today()` — observed_at/created_at 생성 (test 에서 freeze 필요 시 monkeypatch)

---

## 5. 호출부

- `src/graph.py` — `integrate_node` 노드 등록 (`plan→collect→integrate→critique` flow)
- `src/orchestrator.py` — graph 실행, 반환 partial state 병합
- `scripts/run_one_cycle.py`, `scripts/run_bench.py` — orchestrator 호출

---

## 6. 변경 금지 영역 (P1/P3 주의)

P1 (Stability) 과 P3 (Acquisition Expansion) 는 아래 키·shape 을 **변경·삭제 금지**:

1. 반환 dict 의 4개 키 이름
2. Claim `integration_result` 5-value enum
3. KU `ku_id` 포맷 (`KU-####`)
4. GU `gu_id` 포맷 (`GU-####`)
5. `dispute_queue` item 의 6 필드: `ku_id`, `claim_id`, `field`, `existing_value`, `new_value`, `cycle`

**허용되는 확장:**
- KU/GU shape 에 `provenance` optional 필드 추가 (P0-X3 에서 예약 예정)
- `axis_tags` 에 geography 외 축 추가
- `source_type` 확장 (P3 provider 별 라벨)

---

## 7. 검증 테스트 (현행 테스트 기준)

다음 테스트들이 이 인터페이스 보장을 간접 검증한다:

- `tests/test_nodes/test_integrate.py` — shape 보존 (adds/updates/rejects 경로)
- `tests/test_graph.py` — integrate 이후 partial-state 병합

> **Gap**: `dispute_queue` append-only 동작을 명시적으로 검증하는 테스트가 아직 없다.
> P0-X6 (conftest 재정비) 또는 P1 초기에 `test_integrate_dispute_queue.py` 추가 필요.

Silver P0 누적 500 passed (commit `6c7f28f`) 시점에서 이 스냅샷과 일치.
