# Session Compact

> Generated: 2026-04-21
> Source: Conversation compaction via /compact-and-go

## Goal

SI-P7 S2 축 착수 — S2-T1 (integration_result_dist 제어 입력화) + S2-T2 (ku_stagnation trigger) 구현.

---

## Completed

- [x] **S2-T1**: `integration_result_dist` state 승격 + plan/critique 제어 입력화
  - `src/state.py`: `integration_result_dist: dict` 필드 추가
  - `src/utils/metrics.py`: `accumulate_integration_dist(prev_dist, cycle_outcomes, cycle)` 함수 추가
  - `src/nodes/integrate.py`: `resolve_outcomes` key 통일 (`no_source_gu_id` → `no_source_gu`) + `integration_result_dist` state 반환 (per-cycle + 누적 cycle_history)
  - `src/nodes/critique.py`: `INTEGRATION_CONV_RATE_THRESHOLD = 0.3` + `_analyze_failure_modes` 에 `integration_bottleneck` 처방 추가 + `_generate_machine_rules` 에 `integration_bottleneck` 규칙 추가
  - `src/nodes/plan.py`: `INTEGRATION_LOW_CONV_THRESHOLD = 0.3` + `_assign_reason_code` 에 `integration:low_conversion(conv=X.XX)` reason code 추가 + `plan_node` 에 `integration_signal` 필드 추가
  - L1 테스트 18개 추가 (853 passed, 3 skipped)
  - 커밋: `7bd9f2b`

---

## Current State

**브랜치**: `main` (모두 커밋됨)
**테스트**: 853 passed, 3 skipped

### 커밋 이력 (이번 세션)

| 커밋 | 내용 |
|------|------|
| `7bd9f2b` | S2-T1: integration_result_dist state 승격 + plan/critique 제어 입력화 |

### integration_result_dist 구조

```python
{
  "resolved": int,        # 이번 cycle
  "no_source_gu": int,
  "invalid_result": int,
  "other": int,
  "conv_rate": float,     # resolved / total_claims
  "total_claims": int,
  "cycle_history": [
    {"cycle": int, "resolved": int, "no_source_gu": int,
     "invalid_result": int, "other": int, "conv_rate": float, "total_claims": int}
  ]
}
```

---

## Remaining / TODO

### 즉시 착수 (다음 세션)

- [ ] **S2-T2**: `added_ratio<0.3×3c` + `conflict_hold 증가` + `condition_split 부재` 3종 trigger → critique `rx_id=ku_stagnation:*`
  - **필요 선결 작업**: `state.py`에 `ku_added_history: list[dict]` 필드 추가 (per-cycle added KU 수 추적용)
  - `integrate.py` 또는 `critique.py`에서 cycle별 added/conflict_hold/condition_split 카운트 누적
  - `critique.py` `_analyze_failure_modes` 또는 신규 함수에서 3종 trigger 감지 로직 추가:
    1. `added_ratio_window < 0.3` 최근 3c 평균 (added / total_claims 또는 added / open_count)
    2. `conflict_hold_delta > 0` 증가 추세 감지
    3. `condition_split_count == 0` 최근 cycle들
  - 처방 형식: `{"rx_id": "RX-XXXX", "type": "ku_stagnation:added_low|conflict_rising|no_condition_split", ...}`

- [ ] **S2-T3/T4**: F2 확정 (α + β aggressive mode) 구현 — S5a에 의존하므로 S5a 이후

### 이후 (Step B)

- [ ] S2-T5~T8: condition_split 재정의 (`_detect_value_shape_diff`)
- [ ] S3: adjacent rule engine
- [ ] S4: virtual `balance-*` entity 즉시 제거 (C1 502초 병목)
- [ ] 기존 telemetry 버그: cycles.jsonl의 `cycle` 번호 전부 0, `search_calls`/`llm_calls` 전부 0

---

## Key Decisions

- **S2-T1 구현 방식**: `integrate.py`가 per-cycle 분포를 계산하여 state에 저장, `critique.py`/`plan.py`가 읽어서 제어 입력으로 사용 (단방향 흐름 유지)
- **S2-T2 선결 작업**: `added_ratio` 계산에 cycle별 added KU 이력이 필요 → state에 `ku_added_history` 신설 필요 (integrate.py에서 기록)
- **임계치**: `integration:low_conversion` = conv_rate < 0.3 (INTEGRATION_CONV_RATE_THRESHOLD/INTEGRATION_LOW_CONV_THRESHOLD 둘 다 0.3으로 통일)

---

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 진입점 — 읽기 우선순위

1. `docs/structural-redesign-tasks_CC.md` v2 — 단일 진실 소스 (S2-T2 스펙: 120~130번째 줄)
2. `dev/active/phase-si-p7-structural-redesign/si-p7-tasks_CC.md` — task checklist

### S2-T2 관련 코드 경로

- `src/nodes/integrate.py` — added/conflict_hold/condition_split 카운트 위치 (현재 `resolve_outcomes` dict 계산 후)
- `src/nodes/critique.py` — `_analyze_failure_modes` 함수 (처방 추가 위치), `critique_node` (state에서 데이터 읽기)
- `src/state.py` — `ku_added_history` 필드 신설 위치 (integration_result_dist 아래)

### S2-T2 스펙 (structural-redesign-tasks_CC.md 기준)

```
S2-T2: `added_ratio<0.3×3c` + `conflict_hold 증가` + `condition_split 부재` 3종 trigger
→ critique `rx_id=ku_stagnation:*`
파일: src/nodes/critique.py
예상 변경: +50L
```

### 현재 integrate.py 내부 데이터 (S2-T2 활용 가능)

`integrate_node` 반환 직전에 이미 다음이 계산됨:
- `adds`: 신규 KU 리스트 → `len(adds)` = added count
- `resolve_outcomes["invalid_result"]`: conflict_hold가 아님 (hold는 별도)
- `claim["integration_result"]` == "conflict_hold": conflict hold 건수
- `claim["integration_result"]` == "condition_split": condition_split 건수

→ `integration_result_dist`에 `added`, `conflict_hold`, `condition_split` 카운트를 추가하거나, 별도 `ku_stagnation_signals` state 필드 신설

---

## Next Action

1. `src/state.py`에 `ku_stagnation_signals: dict` 필드 추가
   - 구조: `{"added_history": [{"cycle": int, "added": int, "total_claims": int, "added_ratio": float}], "conflict_hold_history": [...], "condition_split_history": [...]}`
2. `src/nodes/integrate.py`에서 per-cycle added/conflict_hold/condition_split 카운트 계산 후 `ku_stagnation_signals`로 state 반환
3. `src/nodes/critique.py` `_analyze_failure_modes` 에 3종 trigger 감지 로직 추가:
   - `added_ratio < 0.3` 최근 3c → `ku_stagnation:added_low`
   - `conflict_hold_trend > 0` → `ku_stagnation:conflict_rising`
   - `condition_split_count == 0` 최근 3c → `ku_stagnation:no_condition_split`
4. L1 테스트 작성 (test_integrate.py + test_critique.py)
5. 전체 테스트 통과 확인 + 커밋
