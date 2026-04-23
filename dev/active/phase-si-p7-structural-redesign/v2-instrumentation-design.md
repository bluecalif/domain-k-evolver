# SI-P7 Step V — V2 Instrumentation Design (V-T4)

> 작성: 2026-04-23
> 목표: V1 에서 `~ 계측 부재` 로 남은 6 항목을 재파싱 가능하게 만듦. 로직 변경 금지, 관찰만 추가.
> 근거: `v1-signal-audit.md` [D] emit 매핑 + H5c 가설 검증 요구사항

## 원칙

1. **로직 변경 금지** — 기존 분기/계산 조건을 건드리지 않음. 관찰 코드만 추가.
2. **Append-only** — state 신규 list 는 append 만, 삭제·수정 없음 (재현성 보장)
3. **Real-path emit only** — fixture mock 금지. emit 경로는 실 trial 에서 작동해야 함 (D-187)
4. **Cycle-stamp 모든 event** — 각 event 에 `cycle` 필드 필수 (사후 재파싱 용)

---

## 1. Data Model (state.py)

### 기존 필드 재사용 (변경 없음)

이미 정의되어 있으나 persist/emit 되지 않는 필드:

```python
integration_result_dist: dict         # line 243, S2-T1
ku_stagnation_signals: dict           # line 249, S2-T2
aggressive_mode_remaining: int        # line 253, S2-T4 β
recent_conflict_fields: list[dict]    # line 257, S3-T2
adjacency_yield: dict                 # line 261, S3-T7
coverage_map: dict                    # line 227, S4-T2 (P4용으로 예약됨, SI-P7 에서 활용)
```

→ **persist 만 추가** (data model 변경 없음)

### 신규 event-log 필드 추가

다음 4개 list 를 `state.py` 에 추가 (cycle-stamp event append):

```python
# SI-P7 V2 계측: event-log 필드 (관찰 전용, append-only)
aggressive_mode_history: list[dict]
    # [{"cycle": int, "remaining": int, "event": "entered"|"tick"|"exited", "rx_id": str|None}]

query_rewrite_rx_log: list[dict]
    # [{"cycle": int, "gu_id": str, "slug": str, "field": str, "rewritten_queries": list[str]}]

condition_split_events: list[dict]
    # [{"cycle": int, "ku_id": str|None, "claim_entity": str, "field": str,
    #   "reason": "conditions"|"value_shape"|"condition_axes"|"axis_tags"}]

suppress_event_log: list[dict]
    # [{"cycle": int, "category": str, "threshold": float,
    #   "suppressed_fields": list[str], "field_counts": dict}]
```

**Bool/int 전용 필드는 추가 불요**: cycle 별 scalar 는 telemetry 로 emit (state append 는 overhead).

---

## 2. Persistence (state_io.py)

### 신규 파일: `si-p7-signals.json`

하나의 JSON object 에 10개 필드 (기존 6 + 신규 4) 묶어서 저장:

```json
{
  "integration_result_dist": {...},
  "ku_stagnation_signals": {...},
  "aggressive_mode_remaining": 0,
  "recent_conflict_fields": [...],
  "adjacency_yield": {...},
  "coverage_map": {...},
  "aggressive_mode_history": [...],
  "query_rewrite_rx_log": [...],
  "condition_split_events": [...],
  "suppress_event_log": [...]
}
```

### `state_io.py` 변경

**1) 신규 상수 (파일 상단)**:

```python
_SI_P7_SIGNALS_FILE = "si-p7-signals.json"
_SI_P7_SIGNAL_FIELDS: tuple[str, ...] = (
    "integration_result_dist",
    "ku_stagnation_signals",
    "aggressive_mode_remaining",
    "recent_conflict_fields",
    "adjacency_yield",
    "coverage_map",
    "aggressive_mode_history",
    "query_rewrite_rx_log",
    "condition_split_events",
    "suppress_event_log",
)
```

**2) `save_state`**: external-anchor 저장 블록 아래에 추가

```python
# SI-P7 V2: si-p7-signals.json (비어 있지 않은 필드만 직렬화)
payload = {f: state.get(f) for f in _SI_P7_SIGNAL_FIELDS if state.get(f) not in (None, {}, [], 0)}
if payload:
    target = state_dir / _SI_P7_SIGNALS_FILE
    if target.exists():
        shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
    _write_json(target, payload)
```

**3) `snapshot_state`**: 기존 copy 목록에 `_SI_P7_SIGNALS_FILE` 추가

```python
for filename in list(_FILE_MAP) + list(_OPTIONAL_LIST_FILES) + [_EXTERNAL_ANCHOR_FILE, _SI_P7_SIGNALS_FILE]:
    src = state_dir / filename
    if src.exists():
        shutil.copy2(src, snapshot_dir / filename)
```

**4) `load_state`**: `si-p7-signals.json` 존재 시 10개 필드 populate (파일 부재 시 기본값)

```python
# SI-P7 V2: si-p7-signals.json 로드 (optional, migration-safe)
signals_path = state_dir / _SI_P7_SIGNALS_FILE
if signals_path.exists():
    signals_data = _read_json(signals_path)
    for field in _SI_P7_SIGNAL_FIELDS:
        if field in signals_data:
            state[field] = signals_data[field]
```

---

## 3. Telemetry (obs/telemetry.py)

### cycle snapshot dict 확장

`_build_snapshot` 의 return dict 에 `si_p7` sub-dict 추가:

```python
"si_p7": {
    "aggressive_mode_remaining": int(state.get("aggressive_mode_remaining", 0)),
    "integration_result_cycle": _extract_integration_cycle(state, cycle_num),
    "condition_split_count_cycle": _count_events_in_cycle(state.get("condition_split_events"), cycle_num),
    "suppress_count_cycle": _count_events_in_cycle(state.get("suppress_event_log"), cycle_num),
    "query_rewrite_count_cycle": _count_events_in_cycle(state.get("query_rewrite_rx_log"), cycle_num),
    "recent_conflict_fields_count": len(state.get("recent_conflict_fields") or []),
    "adjacency_yield_top3": _top_n_rules(state.get("adjacency_yield"), n=3),
    "coverage_deficit_top3": _top_n_deficit(state.get("coverage_map"), n=3),
}
```

Helper 함수 3개 (telemetry.py 내부):
- `_extract_integration_cycle(state, cycle_num)` — `integration_result_dist.cycle_history` 중 해당 cycle 항목 반환
- `_count_events_in_cycle(events_list, cycle_num)` — cycle 필드 매칭 카운트
- `_top_n_rules / _top_n_deficit` — 상위 N개 정렬 후 slice

이 helpers 는 모두 **read-only pure function**. state 변형 금지.

---

## 4. Event Log Emission Points

로직 변경 없이, 기존 분기 직후에 append + logger.info 삽입.

### 4.1 Aggressive mode — `critique.py:655`

**현재 코드 (확인됨)**:
```python
if prev_remaining == 0:
    result["aggressive_mode_remaining"] = 3
```

**변경 후** (bracket 한 블록만 추가):
```python
if prev_remaining == 0:
    result["aggressive_mode_remaining"] = 3
    # SI-P7 V2 계측
    cycle = state.get("cycle_count", 0)
    history = list(state.get("aggressive_mode_history") or [])
    history.append({
        "cycle": cycle,
        "remaining": 3,
        "event": "entered",
        "rx_id": rx_entry.get("type"),  # e.g. "ku_stagnation:added_low"
    })
    result["aggressive_mode_history"] = history
    logger.info("[si-p7] β aggressive_mode entered: cycle=%d rx=%s remaining=3",
                cycle, rx_entry.get("type"))
```

**tick/exit emit** — `aggressive_mode_remaining` 가 감소 / 0 리셋되는 지점을 찾아 동일 패턴:
- 현재 감소 로직 위치: **미구현** (S5a-T11 에 배정)
- V2 는 entry 만 우선 emit. tick/exit 는 S5a 구현 후 추가 (지금은 기록할 event 가 없음 — dead code 여부 확인 목적)

### 4.2 Query rewrite — `plan.py:294-295` / `plan.py:411`

**현재 코드**:
```python
if is_stagnation:
    queries[gu_id] = _rewrite_query_stagnation(slug, field, domain)
```

**변경 후**:
```python
if is_stagnation:
    rewritten = _rewrite_query_stagnation(slug, field, domain)
    queries[gu_id] = rewritten
    # SI-P7 V2 계측
    cycle = state.get("cycle_count", 0)
    plan.setdefault("_si_p7_rewrite_events", []).append({
        "cycle": cycle, "gu_id": gu_id, "slug": slug,
        "field": field, "rewritten_queries": list(rewritten),
    })
    logger.info("[si-p7] query_rewrite: cycle=%d gu=%s slug=%s field=%s n_queries=%d",
                cycle, gu_id, slug, field, len(rewritten))
```

그리고 plan 반환 직전 `state["query_rewrite_rx_log"]` 에 extend:
```python
if "_si_p7_rewrite_events" in plan:
    existing = list(state.get("query_rewrite_rx_log") or [])
    existing.extend(plan.pop("_si_p7_rewrite_events"))
    result["query_rewrite_rx_log"] = existing
```

**주의**: plan.py 는 이미 result dict 반환 구조. 기존 return 에 `query_rewrite_rx_log` key 만 merge.

### 4.3 Condition split — `integrate.py:130/137/141/150`

4 지점 모두 `return "condition_split"` 직전. 각각 `reason` 이 다르므로 파라미터화:

**변경 후** (Rule 2 예시):
```python
# Rule 2: conditions 있으면 condition_split
if claim_conditions:
    _emit_condition_split_event(state, events_buffer, claim, "conditions")
    return "condition_split"
```

`events_buffer` 는 `detect_conflict` 호출자 (integrate 루프) 가 주입하는 list. 루프 종료 후 `state["condition_split_events"]` 에 extend + `logger.info` 1회 요약.

**Helper**:
```python
def _emit_condition_split_event(state, events_buffer, claim, reason):
    cycle = state.get("cycle_count", 0)
    events_buffer.append({
        "cycle": cycle,
        "ku_id": claim.get("ku_id"),
        "claim_entity": claim.get("entity_key", ""),
        "field": claim.get("field", ""),
        "reason": reason,  # "conditions" | "value_shape" | "condition_axes" | "axis_tags"
    })
```

### 4.4 Suppress — `integrate.py:320`

**현재 코드**:
```python
if cat_field_counts:
    mean_count = sum(cat_field_counts.values()) / len(cat_field_counts)
    threshold = mean_count * 1.5
    suppressed_fields = {f for f, c in cat_field_counts.items() if c > threshold}
```

**변경 후** — `suppressed_fields` 가 비어있지 않을 때만 event 기록:
```python
if cat_field_counts:
    mean_count = sum(cat_field_counts.values()) / len(cat_field_counts)
    threshold = mean_count * 1.5
    suppressed_fields = {f for f, c in cat_field_counts.items() if c > threshold}
    # SI-P7 V2 계측
    if suppressed_fields:
        cycle = state.get("cycle_count", 0)
        suppress_log = state.setdefault("suppress_event_log", [])
        suppress_log.append({
            "cycle": cycle,
            "category": category,
            "threshold": round(threshold, 2),
            "suppressed_fields": sorted(suppressed_fields),
            "field_counts": dict(cat_field_counts),
        })
        logger.info("[si-p7] adjacency suppressed: cycle=%d cat=%s thr=%.2f fields=%s",
                    cycle, category, threshold, sorted(suppressed_fields))
```

**주의**: `_generate_adjacent_gus` 는 claim 별로 여러 번 호출됨. 같은 (cycle, category) 조합이 중복 append 될 수 있음 → L1 테스트에서 dedupe 검증 필요 없음 (cycle 내 중복은 진단 용도로 허용, 사후 재파싱에서 유니크화).

### 4.5 Adjacency yield / recent_conflict_fields / coverage_map

이미 state 에 기록되고 있음 (integrate.py:411+ 등). **persist 만 추가** (§2 state_io 변경) → 별도 emit 불요.

---

## 5. L1 Test Design

### 원칙 (D-187)

- **fixture = real snapshot**. `bench/japan-travel/state/*.json` load 사용
- function stub 금지. production 함수 직접 호출
- caplog 으로 logger.info 검증

### Test 파일 배치

- `tests/test_si_p7_v2_instrumentation.py` (신규)

### Test 케이스 (최소 8개)

| # | 테스트 | 검증 대상 |
|---|---|---|
| 1 | `test_save_state_writes_si_p7_signals_file` | `save_state` → `si-p7-signals.json` 존재 + 필드 match (state 에 값 주입) |
| 2 | `test_save_state_skips_si_p7_signals_when_empty` | 모든 필드가 비면 파일 생성 안 됨 |
| 3 | `test_load_state_populates_si_p7_signals` | 기존 파일 있으면 state 에 load, 없으면 기본값 |
| 4 | `test_snapshot_state_copies_si_p7_signals` | `snapshot_state` 후 cycle-N-snapshot 에 파일 존재 |
| 5 | `test_critique_emits_aggressive_mode_entry` | stagnation trigger → `aggressive_mode_history` append + logger.info `[si-p7] β aggressive_mode entered` |
| 6 | `test_plan_emits_query_rewrite_event` | `is_stagnation=True` 경로 → `query_rewrite_rx_log` append + logger.info `[si-p7] query_rewrite` |
| 7 | `test_integrate_emits_condition_split_events` | 각 reason (conditions/value_shape/condition_axes/axis_tags) 별로 event append |
| 8 | `test_integrate_emits_suppress_event` | field 수가 `mean × 1.5` 초과 시 `suppress_event_log` append |
| 9 | `test_telemetry_emits_si_p7_subdict` | `_build_snapshot` 결과에 `si_p7` key 존재 + 8개 sub-field |
| 10 | `test_telemetry_helpers_readonly` | `_extract_integration_cycle` 등 helper 가 state 를 변형하지 않음 |

### Fixture 전략

- 기존 `bench/japan-travel/state/*.json` 을 `load_state` 로 읽은 뒤 state dict 에 V2 필드 주입해서 사용
- snapshot_state 테스트는 `tmp_path` 에 state 복사 후 실행

---

## 6. V-T6 Smoke Acceptance Criteria

**실행 명령**:
```bash
PYTHONUTF8=1 python scripts/run_readiness.py \
  --bench-root bench/silver/japan-travel/p7-v2-smoke \
  --cycles 1 \
  --trial-id p7-v2-smoke
```

**검증 체크리스트** (1 cycle 후):

- [ ] `bench/silver/japan-travel/p7-v2-smoke/state/si-p7-signals.json` 파일 존재
- [ ] 파일에 10개 필드 중 **최소 2개** 이상 non-empty (c1 에서 observed: `integration_result_dist`, `ku_stagnation_signals` 등)
- [ ] `bench/silver/japan-travel/p7-v2-smoke/state-snapshots/cycle-1-snapshot/si-p7-signals.json` 복사 확인
- [ ] `telemetry/cycles.jsonl` 첫 라인에 `si_p7` key 존재 + 8개 sub-field
- [ ] `run.log` 에 `[si-p7]` prefix 로그 **최소 1건** 이상 (가장 가능성 높음: query_rewrite 또는 suppress)
- [ ] 기존 테스트 926 passed 유지 (회귀 없음)

**Failure modes** (V-T6 에서 발견 시 대응):
- emit 경로가 호출 안 됨 → 분기 조건 검토
- state 변형 발생 (test #10 fail) → helper 에서 copy 누락
- 성능 regression (cycle 시간 ≥+20%) → logger.info 를 logger.debug 로 전환

---

## 7. H5c 확정 조건 (V-T10 으로 이월)

V2 계측이 작동한 뒤, **c3~c15 동안 `aggressive_mode_history` 에 entry event 가 1건 이상 기록되지만** 동일 cycle range 에서:
- target 수 변화 없음 (tgt=0 고정 유지)
- LLM query 호출 수 변화 없음
- source_count ≥1 임시 적재 없음

→ **H5c 확정**: β aggressive mode state 는 작동하지만 효과 경로 부재 (S5a-T11 미구현). `p7-ab-on` FAIL 의 근본 원인 중 하나.

반대로 entry event 가 0건이면 **H5c 이전 단계 (entry 자체 실패)** — `critique.py:655` 로직 결함 의심.

---

## 8. 변경 파일 요약

| 파일 | 변경 유형 | 규모 추정 |
|---|---|---|
| `src/state.py` | 필드 4개 추가 | +10 lines |
| `src/utils/state_io.py` | 상수 + save/load/snapshot 확장 | +40 lines |
| `src/obs/telemetry.py` | si_p7 sub-dict + helper 3개 | +50 lines |
| `src/nodes/critique.py` | aggressive entry emit | +8 lines |
| `src/nodes/plan.py` | query_rewrite emit (2 지점) | +16 lines |
| `src/nodes/integrate.py` | condition_split 4 지점 + suppress | +25 lines |
| `tests/test_si_p7_v2_instrumentation.py` | 신규 10 테스트 | +200 lines |

**총 예상 LOC**: ~350 추가, ~0 삭제. 기존 로직 분기 변경 0건.

---

## 9. Risks / Open Questions

- **R1**: `cycle_count` state 필드 신뢰성 — orchestrator 가 cycle 시작/종료 어느 시점에 increment 하는지 확인 필요 (cycle=0 offset 이슈가 V-T1 에서 발생했음). emit 전 `state.get("cycle_count", 0)` 로 안전 처리
- **R2**: `integrate.py` 의 `detect_conflict` 호출 context 에서 `state` 접근 가능 여부 — 현재 signature 확인 필요. 접근 불가 시 events_buffer 패턴 사용 (설계 §4.3 반영)
- **R3**: Emit overhead — cycle 당 append 수 수십~수백 수준이면 perf 영향 무시 가능. 수천 건 넘으면 batch + flush 필요 (현재 기준 무관)
- **Q1**: `aggressive_mode_history` 를 state append 로 할지, telemetry 전용으로 할지? — 현 설계: 둘 다 (state 는 전 cycle 이력, telemetry 는 해당 cycle scalar)
- **Q2**: `si-p7-signals.json` 이 커지면 분할 필요? — c15 기준 추정 KB 단위, 분할 불요

---

## 10. Next Steps

1. **사용자 승인**: 본 설계 OK → V-T5 구현 착수
2. **V-T5 순서**:
   a. state.py 필드 추가 + state_io.py 확장 (test #1~4)
   b. telemetry.py si_p7 sub-dict (test #9~10)
   c. critique / plan / integrate emit (test #5~8)
   d. 전체 pytest 실행 (회귀 없음 확인)
3. **V-T6**: 1-cycle smoke 실행, §6 acceptance 검증
4. **V-T10 (후속)**: smoke 결과로 H5c 가설 1차 판단. 15c trial 필요 시 V3 (D-191 ablation) 결정

---

## 참조

- `v1-signal-audit.md` [D]/[E] (emit 매핑 + H5c 가설)
- `src/state.py:220-266` (SI-P7 필드 정의)
- `src/utils/state_io.py:184-259` (save/snapshot 구조)
- `src/obs/telemetry.py:67-158` (cycle snapshot 빌드)
- D-187 (mock 금지) / D-190 (Step V) / D-191 (V3 비용 원칙)
- Memory `feedback_l3_trial_item_signal_audit.md`
