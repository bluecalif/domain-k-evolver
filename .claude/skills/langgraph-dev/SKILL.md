---
name: langgraph-dev
description: LangGraph 기반 Evolver 파이프라인 개발 가이드. 노드/엣지 설계, State 타입, 도구 바인딩, 파일 I/O 패턴.
---

# LangGraph Development Guide

## Purpose

Domain-K-Evolver의 LangGraph 자동화 파이프라인 구현 가이드.
노드 함수, 엣지 라우팅, State 관리, 도구 바인딩 패턴 제공.

## When to Use This Skill

- LangGraph 노드/엣지 구현 시
- EvolverState 타입 정의/수정 시
- JSON 파일 기반 State I/O 구현 시
- WebSearch/WebFetch 도구 바인딩 시
- HITL (Human-in-the-Loop) 게이트 구현 시

---

## Architecture Overview

```
seed_node → plan_node → [HITL Gate A] → collect_node → [HITL Gate B]
    → integrate_node → critique_node → plan_modify_node → plan_node (next cycle)
                                     → END (종료 조건 충족 시)
```

---

## EvolverState 정의

```python
from typing import TypedDict
from langgraph.graph import StateGraph

class EvolverState(TypedDict):
    # Core State (K, G, P, M, D)
    knowledge_units: list[dict]     # KU[]
    gap_map: list[dict]             # GU[]
    policies: dict                   # Policies
    metrics: dict                    # Metrics
    domain_skeleton: dict            # DomainSkeleton

    # Cycle State
    current_cycle: int
    current_plan: dict | None
    current_claims: list[dict] | None
    current_critique: dict | None
```

---

## Node 구현 패턴

### 기본 구조

```python
def node_name(state: EvolverState) -> dict:
    """노드 함수는 state를 받아 업데이트할 필드만 반환."""
    # 1. state에서 필요한 데이터 읽기
    # 2. LLM 호출 또는 로직 실행
    # 3. 업데이트할 필드만 dict로 반환
    return {"field_to_update": new_value}
```

### 노드별 입출력

| 노드 | 입력 (state에서) | 출력 (반환) | 도구 |
|------|-----------------|------------|------|
| seed_node | (외부 Seed Pack) | knowledge_units, gap_map, domain_skeleton, policies, metrics | — |
| plan_node | gap_map, metrics, domain_skeleton | current_plan | LLM |
| collect_node | current_plan | current_claims | WebSearch, WebFetch |
| integrate_node | current_claims, knowledge_units, gap_map | knowledge_units, gap_map, metrics | LLM |
| critique_node | knowledge_units, gap_map, metrics | current_critique | LLM |
| plan_modify_node | current_critique, current_plan | current_plan, current_cycle | LLM |

---

## 엣지 라우팅

```python
def should_continue(state: EvolverState) -> str:
    """critique_node 이후 종료 판단."""
    metrics = state["metrics"]
    cycle = state["current_cycle"]

    if metrics.get("gap_resolution_rate", 0) >= TARGET_RATE:
        return "end"
    if cycle >= MAX_CYCLES:
        return "end"
    return "continue"

# Graph 빌드
graph.add_conditional_edges(
    "critique_node",
    should_continue,
    {"continue": "plan_modify_node", "end": "__end__"}
)
```

---

## JSON 파일 I/O 패턴

```python
import json
from pathlib import Path

def load_state_file(bench_dir: Path, filename: str) -> list | dict:
    """State JSON 파일 로드."""
    filepath = bench_dir / "state" / filename
    with open(filepath, encoding='utf-8') as f:
        return json.load(f)

def save_state_file(bench_dir: Path, filename: str, data: list | dict) -> None:
    """State JSON 파일 저장."""
    filepath = bench_dir / "state" / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

**핵심**: `encoding='utf-8'` 항상 명시. `ensure_ascii=False`로 한글 보존.

---

## HITL Gate 패턴

```python
from langgraph.types import interrupt

def hitl_gate_node(state: EvolverState) -> dict:
    """사람 검토 게이트. 승인/거부/수정 입력 대기."""
    review_target = state.get("current_plan") or state.get("current_claims")
    decision = interrupt({"review": review_target})

    if decision["action"] == "reject":
        raise ValueError(f"Rejected: {decision.get('reason', 'no reason')}")

    return {}  # 승인 시 state 변경 없이 통과
```

---

## Directory Convention

```
src/
  graph.py              # StateGraph 빌드 + 엣지 정의
  state.py              # EvolverState TypedDict + 타입 정의
  nodes/
    seed.py             # seed_node
    plan.py             # plan_node
    collect.py          # collect_node + WebSearch/WebFetch
    integrate.py        # integrate_node
    critique.py         # critique_node
    plan_modify.py      # plan_modify_node
    hitl_gate.py        # hitl_gate_node
  utils/
    state_io.py         # JSON 파일 I/O
    schema_validator.py # JSON Schema 검증
    metrics.py          # Metrics 계산
```

---

## Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| 노드에서 전체 state 반환 | 불필요한 덮어쓰기 | 변경 필드만 반환 |
| encoding 생략 | Windows에서 깨짐 | `encoding='utf-8'` 필수 |
| collect에서 LLM 없이 파싱 | Claim 품질 저하 | LLM으로 구조화 |
| HITL 게이트 생략 | 잘못된 Plan 실행 | 최소 Gate A 유지 |

---

## Related

- `docs/design-v2.md` §10: 노드/엣지 설계 원본
- `evolver-framework` skill: 5대 불변원칙 체크
- `schemas/`: JSON Schema (KU, EU, GU, PU)
