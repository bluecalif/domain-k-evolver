---
name: silver-hitl-policy
description: Domain-K-Evolver Silver 세대 HITL 축소 정책 (masterplan v2 §14). Bronze 의 인라인 HITL-A/B/C 를 제거하고 HITL-S (Seed) / HITL-R (Remodel) / HITL-D (Dispute batch) / HITL-E (Exception) 4 세트로 재배치한다. `graph.py` 에서 HITL edge 를 제거·추가하거나, `hitl_gate.py` / `metrics_guard.py` 를 만지거나, `dispute_queue` / `conflict_ledger` 관계를 다루거나, "HITL 줄이자", "graph edge 정리", "auto-pause 임계치 추가", "HITL inbox", "interrupt 어디 걸지", "dispute_resolver 실패 처리", "exception trigger" 같은 요청이 나오면 반드시 사용한다. Bronze (Phase 1~5) HITL gate 코드를 그대로 유지·디버깅하는 작업에는 사용하지 않는다.
---

# Silver HITL Policy

## 목적

Bronze 시기에 모든 cycle 에 인라인으로 박혀 있던 HITL-A/B/C 는 Silver 에서 **제거**된다. 대신 4 가지 새 HITL 세트가 도입되며, 이들은 cycle 내부가 아니라 phase 경계 또는 예외 조건에서만 작동한다.

이 skill 은 그 재배치 규칙과 graph 변경 절차를 제공한다. masterplan v2 §14 가 단일 진실 소스다.

## 언제 쓰는가

- P0-C task (HITL 축소) 작업 시
- `graph.py` 에서 HITL edge 를 추가·제거할 때
- `src/nodes/hitl_gate.py` 를 수정할 때
- `metrics_guard.py` 의 임계치 항목을 추가할 때
- `dispute_queue` / `conflict_ledger` 의 관계를 다룰 때
- P5 dashboard 의 HITL inbox view 를 설계할 때
- "왜 이 HITL 이 있어야 하나" 라는 질문이 나올 때 (3 keep-criteria 확인)

## 언제 쓰지 않는가

- Bronze Phase 1~5 의 HITL gate 작동을 그대로 유지·디버깅
- LangGraph interrupt API 자체의 사용법 학습 (이건 `langgraph-dev` skill)
- HITL 과 무관한 graph routing 디버깅

---

## 핵심 원칙 — HITL 3 keep-criteria

HITL 은 다음 **3 조건 중 하나** 를 만족할 때만 유지한다. 나머지는 자동화하거나 배치 검토로 이연한다.

1. **Irreversible** — structural 변경, policy 영구 수정 (돌이키는 비용 > 개입 비용)
2. **Auto-resolver 실패** — 결정론적·통계적 처리가 먼저 시도되고, 결과가 불확실할 때만 사람에게 넘김
3. **Trust boundary crossing** — 새 domain / provider / skeleton 등록

이 3 조건은 **테스트 질문** 으로 쓴다. 새 HITL 을 추가하자는 제안이 나오면 "이 중 어느 조건에 해당하는가?" 를 물어 답이 없으면 거부한다.

---

## Bronze HITL → Silver HITL 매핑 (§14.2 verbatim)

| Bronze HITL | 위치 | 빈도 | 본질 | Silver 조치 |
|-------------|------|------|------|-------------|
| **HITL-A (plan)** | `plan → HITL-A → collect` | 매 cycle | plan 승인 | ❌ **제거** — critique/mode 가 rationale 보유, 결과는 다음 cycle 에서 복구 가능 (reversible) |
| **HITL-B (collect)** | `collect → HITL-B → integrate` | 매 cycle | 수집 결과 승인 | ❌ **제거** → `HITL-E` 예외로 이관 |
| **HITL-C (integrate)** | `integrate → HITL-C → critique` | 매 cycle | 통합 결과 승인 | ❌ **제거** → `HITL-D` 배치 + `HITL-E` 예외로 분리 |
| **HITL-R (remodel)** | outer-loop, 미구현 | audit 후 | 구조 변경 승인 | ✅ **유지** (irreversible) — P2 에서 구현 |

A/B/C 의 제거가 가능한 근본 이유는 **plan/collect/integrate 결과는 다음 cycle 에서 critique 가 처방으로 교정**한다는 점이다. critique 가 inner loop 의 자동 governance 라면, 매 cycle HITL 은 중복이며 운영 비용만 발생시킨다.

---

## Silver v2 HITL 4 세트 (§14.3 verbatim)

| HITL | 트리거 | 인터럽트 | 근거 (3 criteria 중) | 구현 위치 |
|------|--------|----------|----------------------|-----------|
| **HITL-S** (Seed) | phase 시작 1회 (새 도메인 / remodel 후 phase bump) | **blocking** | (1) Irreversible + (3) Trust boundary | `seed_node` 직후 1회 gate |
| **HITL-R** (Remodel) | `remodel_node` 가 제안 생성 시 | **blocking** | (1) Irreversible (structural) | P2 의 `remodel_node` 직후 gate |
| **HITL-D** (Dispute batch) | `dispute_resolver` auto-resolve 실패 KU 누적 | **non-blocking** — cycle 계속, `dispute_queue` 에 append | (2) Auto-resolver 실패 | P5 대시보드 inbox, 체크박스 일괄 승인 |
| **HITL-E** (Exception) | 임계치 위반 시에만 (아래 5 항) | **blocking** (auto-pause + 대시보드 알림) | (2) Auto-resolver 실패 — 시스템 수준 | `metrics_guard` 확장, `graph.py` 조건부 edge |

### HITL-E 트리거 조건 (5 항, 모두 OR)

```python
should_pause = (
    metrics["collect_failure_rate"] > 0.3
    or metrics["conflict_rate"]      > 0.4
    or metrics["fetch_failure_rate"] > 0.5
    or state.get("cost_regression_flag") is True
    or len(state["dispute_queue"])    > 20
)
```

이 5 개는 `metrics_guard.py` 에 명시 — warning-only 가 아니라 실제 graph interrupt 로 연결한다.

### 효과

- **일반 cycle = 100% 자동 진행** — `HITL-S` / `HITL-R` 는 cycle 내부가 아니라 경계 이벤트
- 운영자 개입 빈도: cycle 당 3~4 회 → **Phase 당 2~3 회 + 예외 시**
- `HITL-D` 의 배치 검토는 P5 대시보드의 **핵심 view** 로 승격 (R10 리스크 연결)

---

## Graph 변경 절차 (P0-C)

### 변경 전 (Bronze)

```python
# graph.py — 인라인 HITL 3개
g.add_edge("plan", "hitl_a")
g.add_edge("hitl_a", "collect")
g.add_edge("collect", "hitl_b")
g.add_edge("hitl_b", "integrate")
g.add_edge("integrate", "hitl_c")
g.add_edge("hitl_c", "critique")
```

### 변경 후 (Silver)

```python
# graph.py — A/B/C 제거, S/R/E 재배치
g.add_edge("seed", "hitl_s")          # phase 첫 cycle 1회만
g.add_conditional_edges("hitl_s", route_after_seed)  # approved → plan, rejected → END

g.add_edge("plan", "collect")          # ← 직결
g.add_edge("collect", "integrate")     # ← 직결
g.add_edge("integrate", "critique")    # ← 직결

g.add_conditional_edges(
    "critique", route_after_critique,  # → plan_modify | audit | END
)

# Outer loop (P2)
g.add_edge("audit", "remodel")
g.add_edge("remodel", "hitl_r")
g.add_conditional_edges("hitl_r", route_after_remodel)  # approved → phase_bump, rejected → plan_modify

# Exception 분기 (모든 노드 후 공통)
g.add_conditional_edges(
    "integrate", route_to_hitl_e_if_breach,
)
g.add_conditional_edges(
    "collect", route_to_hitl_e_if_breach,
)
```

### `route_to_hitl_e_if_breach` 공통 함수

```python
def route_to_hitl_e_if_breach(state: EvolverState) -> Literal["hitl_e", "next"]:
    m = state["metrics"]
    breach = (
        m.get("collect_failure_rate", 0) > 0.3
        or m.get("conflict_rate", 0) > 0.4
        or m.get("fetch_failure_rate", 0) > 0.5
        or state.get("cost_regression_flag") is True
        or len(state.get("dispute_queue", [])) > 20
    )
    return "hitl_e" if breach else "next"
```

이 함수는 **단일 정의** — node 별로 복제하지 않는다. P0-C4 task 의 핵심.

### `hitl_gate.py` 축소

```python
# Bronze: HITL-A/B/C/D/E 5 케이스 큰 if 분기
# Silver: HITL-S / HITL-R / HITL-E 3 케이스 (HITL-D 는 비차단 → 노드 아님)

def hitl_gate_node(state: EvolverState) -> dict:
    gate_type = state.get("hitl_gate_type")  # "S" | "R" | "E"
    if gate_type == "S":
        return _handle_seed_gate(state)
    elif gate_type == "R":
        return _handle_remodel_gate(state)
    elif gate_type == "E":
        return _handle_exception_gate(state)
    raise ValueError(f"unknown gate type: {gate_type}")
```

HITL-D 는 **node 가 아니다** — `integrate_node` 안에서 auto-resolve 실패 KU 를 `state["dispute_queue"]` 에 append 만 한다. 사용자는 cycle 진행과 무관하게 P5 대시보드의 inbox 에서 일괄 처리한다.

---

## dispute_queue ↔ conflict_ledger 관계

두 구조는 동일 KU 를 참조할 수 있지만 **독립** 이다. 헷갈리지 말 것.

| 구조 | 위치 | 휘발성 | 용도 | 누가 쓰는가 |
|------|------|--------|------|-------------|
| `dispute_queue` | `EvolverState.dispute_queue: list[DisputeEntry]` | **휘발성** (resolve 시 pop) | auto-resolve 실패 KU 의 작업 큐 | `integrate_node` (append), HITL-D 배치 (pop), HITL-E (`>20` 임계 감시) |
| `conflict_ledger` | `state/conflict_ledger.json` | **영속** (resolve 후에도 유지) | 충돌 감사 로그 | `integrate_node` (entry 생성), `dispute_resolver` (status update), readiness audit |

핵심 규칙:
- `dispute_queue` 에서 pop 되어도 `conflict_ledger` 의 entry 는 **삭제 금지** (`status=resolved` 로 update).
- 동일 `ku_id` 가 두 구조에 동시에 있을 수 있다. 별개로 다룬다.
- `len(dispute_queue) > 20` → HITL-E 트리거 (큐 적체 = 시스템 차원의 처리 실패).

---

## metrics_guard.py 확장 항목 (P0-C6)

기존 metrics_guard 는 warning-only 였다. Silver 에서는 **5 개 임계치** 를 추가하고, 그 중 일부는 실제 interrupt 로 연결.

```python
SILVER_GUARDS = {
    "collect_failure_rate": {"warn": 0.15, "interrupt": 0.30},
    "conflict_rate":        {"warn": 0.20, "interrupt": 0.40},
    "fetch_failure_rate":   {"warn": 0.30, "interrupt": 0.50},
    "cost_regression_flag": {"interrupt": True},  # boolean
    "dispute_queue_size":   {"warn": 10,   "interrupt": 20},
}
```

`warn` 임계치는 metrics 로그에만 기록. `interrupt` 임계치는 HITL-E 노드로 분기.

---

## P5 Dashboard 연결 (§14.6)

P5 의 HITL inbox view 는 다음 3 탭으로 구성:

| 탭 | 내용 | 데이터 소스 |
|----|------|-------------|
| **[Seed/Remodel 승인]** | HITL-S, HITL-R 처리 대기 항목 | `state/hitl_pending.json` |
| **[Dispute 배치 검토]** | `dispute_queue` 의 모든 항목, 체크박스 일괄 승인 | `EvolverState.dispute_queue` (telemetry 경유) |
| **[Exception 알림]** | HITL-E 트리거 history + 현재 paused 여부 | `metrics_logger` + `cost_regression_flag` |

배치 검토는 **체크박스 다중 선택** → `approve all` / `reject all` / `edit selected`. Exception 탭은 실시간 push 없음 — 운영자가 대시보드를 열 때 표시. HITL-E 트리거 시에는 CLI 알림 (`stderr`) 만 추가로 발생.

---

## Anti-Patterns

| 패턴 | 문제 | 교정 |
|------|------|------|
| 새 인라인 HITL 추가 ("collect 결과 항상 보고 싶다") | A/B/C 제거 의도 무력화, 운영비 폭증 | 3 keep-criteria 통과 확인 → 못 통과하면 telemetry 로 보내고 HITL 은 거부 |
| HITL-D 를 graph node 로 만들기 | non-blocking 원칙 위반 | `state.dispute_queue` append 만 하고 cycle 계속 |
| `conflict_ledger` 의 resolved entry 삭제 | 감사 불가, R10 리스크 발생 | resolve 시 `status=resolved` update 만 |
| 임계치 5 항을 warning-only 로만 둠 | HITL-E 가 실제로는 작동 안 함 | metrics_guard 에서 `interrupt` 분기 보장 |
| `route_to_hitl_e_if_breach` 를 node 별로 복제 | 임계치 변경 시 누락 발생 | 단일 함수, 모든 분기에서 import |
| 매 cycle 마다 HITL-S 호출 | "phase 시작 1회" 위반 | `state["phase_first_cycle"]` 플래그로 제어 |
| HITL-E 트리거 후 자동 재시작 | auto-pause 의미 상실 | 사용자 명시 resume 까지 정지 유지 |

---

## 관련

- **masterplan v2 §14** — 단일 진실 소스. 충돌 시 §14 가 옳다.
- **masterplan v2 §8 R10** — `dispute_queue` 적체 리스크.
- **silver-implementation-tasks.md §4 P0-C** — 8 개 task (P0-C1~C8) 가 이 skill 의 직접 적용 대상.
- **`langgraph-dev` skill** — LangGraph interrupt API / 노드 패턴.
- **`evolver-framework` skill** — 5 대 불변원칙 (Conflict-preserving 가 ledger 영속화의 근거).
