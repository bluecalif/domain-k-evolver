# metrics_logger Metric Key 목록 — Silver P0 동결

> **Frozen at**: Silver P0 (phase-si-p0-foundation), 2026-04-12
> **Source**: `src/utils/metrics_logger.py::MetricsLogger.log()` (commit `e3f5659` + X5 패치)
> **Purpose**: P1 이후 Phase 에서 metric key 를 임의 추가/삭제하지 않도록 동결. 키를 변경하려면 명시적 decision (D-XX) 필요.

---

## 1. Entry 키 (MetricsLogger.log 반환 dict)

### 1.1 KU/GU 카운트

| 키 | 타입 | 계산 |
|----|------|------|
| `cycle` | `int` | 현재 cycle 번호 |
| `ku_total` | `int` | `len(knowledge_units)` |
| `ku_active` | `int` | `status == "active"` 카운트 |
| `ku_disputed` | `int` | `status == "disputed"` 카운트 |
| `gu_total` | `int` | `len(gap_map)` |
| `gu_open` | `int` | `status == "open"` 카운트 |
| `gu_resolved` | `int` | `status == "resolved"` 카운트 |

### 1.2 비율 지표 (metrics.rates 에서 복사)

| 키 | 타입 | 출처 | 건강 임계치 |
|----|------|------|------------|
| `evidence_rate` | `float` | `rates.evidence_rate` | ≥ 0.95 |
| `multi_evidence_rate` | `float` | `rates.multi_evidence_rate` | — |
| `conflict_rate` | `float` | `rates.conflict_rate` | ≤ 0.05 |
| `avg_confidence` | `float` | `rates.avg_confidence` | ≥ 0.85 |
| `gap_resolution_rate` | `float` | `rates.gap_resolution_rate` | — |
| `staleness_risk` | `int` | `rates.staleness_risk` | — |

### 1.3 Mode

| 키 | 타입 | 계산 |
|----|------|------|
| `mode` | `str` | `current_mode.mode` (`"normal"` \| `"jump"`) |

### 1.4 Silver 신규 (P0 추가)

| 키 | 타입 | 출처 | 비고 |
|----|------|------|------|
| `collect_failure_rate` | `float` | `state.collect_failure_rate` | B6 에서 collect_node 반환, X5 에서 logger 에 추가 |

### 1.5 비용 추적

| 키 | 타입 | 비고 |
|----|------|------|
| `llm_calls` | `int` | orchestrator 에서 전달 |
| `llm_tokens` | `int` | orchestrator 에서 전달 |
| `search_calls` | `int` | orchestrator 에서 전달 |
| `fetch_calls` | `int` | orchestrator 에서 전달 |

---

## 2. Summary 키 (MetricsLogger.summary 반환 dict)

| 키 | 타입 | 계산 |
|----|------|------|
| `total_cycles` | `int` | `len(entries)` |
| `ku_growth` | `int` | `last.ku_active - first.ku_active` |
| `gu_resolved_total` | `int` | `last.gu_resolved` |
| `final_evidence_rate` | `float` | `last.evidence_rate` |
| `final_conflict_rate` | `float` | `last.conflict_rate` |
| `final_avg_confidence` | `float` | `last.avg_confidence` |
| `jump_cycles` | `int` | `mode == "jump"` 카운트 |
| `total_llm_calls` | `int` | 합산 |
| `total_llm_tokens` | `int` | 합산 |
| `total_search_calls` | `int` | 합산 |
| `total_fetch_calls` | `int` | 합산 |

---

## 3. 변경 금지 / 허용

**변경 금지:**
- 기존 키 이름 변경 또는 삭제
- 기존 키 타입 변경

**허용되는 확장:**
- 새 키 추가 (끝에 append, entry/summary 모두)
- P3 에서 `timeout_count`, `retry_success_rate` 추가 예정 (adapter 레벨 집계 필요)

---

## 4. 검증 테스트

- `tests/test_metrics_logger.py` — log/save_json/save_csv/summary 경로
- `tests/test_nodes/test_collect.py` — `collect_failure_rate` 반환 검증

> **Gap**: `collect_failure_rate` 가 logger entry 에 잘 기록되는지 직접 검증하는 테스트 추가 필요.
