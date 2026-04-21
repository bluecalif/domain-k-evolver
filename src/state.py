"""EvolverState — LangGraph State 타입 정의.

design-v2.md §10 기반. bench/japan-travel/state/ JSON 구조와 1:1 대응.
"""

from __future__ import annotations

from typing import TypedDict


# --- 보조 타입 (JSON dict 구조 명시) ---


class KnowledgeUnit(TypedDict, total=False):
    """Knowledge Unit — 정규화된 주장. schemas/knowledge-unit.json 대응."""

    ku_id: str
    entity_key: str
    field: str
    value: str | dict
    observed_at: str
    validity: dict  # {"ttl_days": int}
    evidence_links: list[str]  # EU ID 목록
    confidence: float
    status: str  # "active" | "disputed" | "deprecated"
    # optional
    conditions: dict
    dispute: dict
    supersedes: str
    axis_tags: dict  # {"geography": str, ...}
    provenance: dict | None  # P3 에서 채움: {"provider": str, "fetch_method": str, ...}


class GapUnit(TypedDict, total=False):
    """Gap Unit — 결손/불확실/충돌/노후화. schemas/gap-unit.json 대응."""

    gu_id: str
    gap_type: str  # "missing" | "uncertain" | "conflicting" | "stale"
    target: dict  # {"entity_key": str, "field": str}
    expected_utility: str  # "critical" | "high" | "medium" | "low"
    risk_level: str  # "safety" | "financial" | "policy" | "convenience" | "informational"
    resolution_criteria: str
    status: str  # "open" | "resolved" | "deferred"
    # optional
    resolved_by: str
    note: str
    trigger: str
    trigger_source: str
    axis_tags: dict  # {"geography": str, "condition": str, ...}
    expansion_mode: str  # "normal" | "jump"
    created_at: str


class ScopeBoundary(TypedDict):
    includes: list[str]
    excludes: list[str]
    boundary_rule: str


class CategoryDef(TypedDict):
    slug: str
    description: str


class FieldDef(TypedDict, total=False):
    name: str
    type: str
    categories: list[str]
    description: str


class RelationDef(TypedDict, total=False):
    name: str
    source: str | list[str]
    target: str | list[str]
    description: str


class AxisDef(TypedDict, total=False):
    name: str
    description: str
    anchors: list[str]
    required: bool
    note: str


class DomainSkeleton(TypedDict, total=False):
    """Domain Skeleton — 카테고리/필드/관계/키규칙/축."""

    domain: str
    version: int
    scope_boundary: ScopeBoundary
    categories: list[CategoryDef]
    fields: list[FieldDef]
    relations: list[RelationDef]
    axes: list[AxisDef]
    axis_meta: dict
    canonical_key_rule: dict


class Policies(TypedDict, total=False):
    """출처신뢰/TTL/교차검증/충돌해결 규칙."""

    credibility_priors: dict[str, float]
    ttl_defaults: dict[str, int]
    cross_validation: dict[str, dict]
    conflict_resolution: dict


class AuditFinding(TypedDict, total=False):
    """Audit 진단 결과 항목."""

    finding_id: str
    category: str  # "coverage_gap" | "yield_decline" | "axis_imbalance" | "quality_issue"
    severity: str  # "critical" | "warning" | "info"
    description: str
    evidence: dict  # 수치 근거


class PolicyPatch(TypedDict, total=False):
    """Policy 수정 제안."""

    patch_id: str
    target_field: str  # e.g. "ttl_defaults.price", "credibility_priors.personal"
    current_value: float | int | str
    proposed_value: float | int | str
    reason: str


class AuditReport(TypedDict, total=False):
    """Executive Audit 결과."""

    audit_cycle: int  # audit가 실행된 시점의 cycle
    window: list[int]  # 분석 대상 cycle 범위 [start, end]
    findings: list[AuditFinding]
    recommendations: list[str]
    policy_patches: list[PolicyPatch]


class MetricRates(TypedDict, total=False):
    evidence_rate: float
    multi_evidence_rate: float
    gap_resolution_rate: float
    conflict_rate: float
    avg_confidence: float
    staleness_risk: int


class Metrics(TypedDict, total=False):
    """Metrics — 6개 지표 + delta."""

    cycle: int
    phase: str
    timestamp: str
    counts: dict
    rates: MetricRates
    delta_from_prev_cycle: dict
    jump_mode: dict
    notes: str


class ModeDecision(TypedDict, total=False):
    """mode_node 출력 — Normal/Jump 판정 결과."""

    mode: str  # "normal" | "jump"
    cap: int  # base_cap or jump_cap
    explore_budget: int
    exploit_budget: int
    trigger_set: list[str]  # 발동된 trigger ID 목록


class AxisCoverageEntry(TypedDict, total=False):
    axis: str
    anchor: str
    open_count: int
    resolved_count: int
    total_count: int
    coverage: float
    deficit_ratio: float


# --- 메인 State ---


class EvolverState(TypedDict, total=False):
    """LangGraph State — design-v2 §10.

    노드 함수는 `def node(state: EvolverState) -> dict` 시그니처로,
    변경된 필드만 반환한다.
    """

    # Core State (K, G, P, M, D)
    knowledge_units: list[KnowledgeUnit]
    gap_map: list[GapUnit]
    policies: Policies
    metrics: Metrics
    domain_skeleton: DomainSkeleton

    # Cycle 관리
    current_cycle: int
    current_plan: dict | None
    current_claims: list[dict] | None
    current_critique: dict | None

    # Mode 관리 (Phase 0C)
    current_mode: ModeDecision | None
    axis_coverage: list[AxisCoverageEntry] | None
    jump_history: list[int]

    # Convergence tracking
    net_gap_changes: list[int]

    # Audit (Phase 4)
    audit_history: list[dict] | None  # AuditReport 이력

    # HITL
    hitl_pending: dict | None

    # Silver: dispute batch queue (HITL-D 비블로킹, P0-C7)
    dispute_queue: list[dict]

    # Silver P0-X4: 후속 Phase 용 필드 예약 (빈 컨테이너 기본값)
    conflict_ledger: list[dict]   # P1: 충돌 감사 로그 (영속)
    phase_number: int             # P2: 현재 phase 번호 (remodel 승인 시 +1)
    phase_history: list[dict]     # P2: phase transition 스냅샷
    remodel_report: dict | None   # P2: 현재 pending RemodelReport (HITL-R 전달용)
    coverage_map: dict            # P4: 축 × 엔티티 그리드
    novelty_history: list[float]  # P4: cycle 별 novelty 점수
    external_novelty_history: list[float]  # SI-P4 Stage E: cycle 별 external novelty
    external_observation_keys: list[str]   # SI-P4 Stage E: 누적 (entity_key|field) 관찰 키
    reach_history: list[dict]   # SI-P5: cycle 별 reach target 기록
    probe_history: list[dict]   # SI-P5: cycle 별 universe probe 결과
    pivot_history: list[dict]   # SI-P5: cycle 별 exploration pivot 기록

    # SI-P7 S1-T4/T8: budget 초과 GU defer queue (다음 cycle 우선 소진)
    deferred_targets: list[str]  # gu_id 목록 (FIFO)
    defer_reason: dict  # {reason_str: count}, e.g. {"budget_exceeded": 3}

    # SI-P7 S2-T1: integration_result 분포 (per-cycle + 누적 history)
    # {"resolved": int, "no_source_gu": int, "invalid_result": int, "other": int,
    #  "conv_rate": float, "total_claims": int,
    #  "cycle_history": [{"cycle": int, "resolved": int, ...}]}
    integration_result_dist: dict

    # SI-P7 S2-T2: KU stagnation 신호 (per-cycle added/conflict_hold/condition_split 이력)
    # {"added_history": [{"cycle": int, "added": int, "total_claims": int, "added_ratio": float}],
    #  "conflict_hold_history": [{"cycle": int, "conflict_hold": int}],
    #  "condition_split_history": [{"cycle": int, "condition_split": int}]}
    ku_stagnation_signals: dict

    # SI-P7 S2-T4: β aggressive mode 잔여 cycle 수 (0=비활성, >0=활성 중)
    # critique에서 ku_stagnation:added_low 발동 시 3 설정, entity_discovery가 매 cycle 1씩 감소
    aggressive_mode_remaining: int

    # Diagnostic fields (진단 전용, orchestrator가 cycle마다 읽고 제거)
    _diag_search_by_gu: dict | None       # collect: {gu_id: search_result_count}
    _diag_adjacent_gap_count: int | None  # integrate: 신규 dynamic GU 수
    _diag_resolved_gus: list | None       # integrate: resolved GU gu_id 목록
