"""Metrics Guard — 위험 임계치 초과 시 경고/중단 판정.

Bronze: conflict_rate > 0.30 또는 evidence_rate < 0.50 → halt 권고.
Silver: 5개 임계치 기반 should_auto_pause (HITL-E 연결).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Hard-stop 임계치 (Task 2.13)
GUARD_THRESHOLDS = {
    "conflict_rate_max": 0.30,
    "evidence_rate_min": 0.50,
}

# Silver v2 HITL-E auto-pause 임계치 (P0-C4/C6, masterplan §14)
AUTO_PAUSE_THRESHOLDS = {
    "conflict_rate_max": 0.25,
    "evidence_rate_min": 0.55,
    "collect_failure_rate_max": 0.50,
    "staleness_ratio_max": 0.30,
    "avg_confidence_min": 0.60,
}


@dataclass
class GuardResult:
    """Guard 판정 결과."""

    triggered: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class AutoPauseResult:
    """HITL-E auto-pause 판정 결과."""

    should_pause: bool = False
    violations: list[str] = field(default_factory=list)


def check_metrics_guard(state: dict) -> GuardResult:
    """State의 metrics를 검사하여 halt 여부 판정.

    Args:
        state: EvolverState dict (metrics.rates 포함).

    Returns:
        GuardResult with halt flag and warning messages.
    """
    rates = state.get("metrics", {}).get("rates", {})
    result = GuardResult()

    conflict_rate = rates.get("conflict_rate", 0.0)
    evidence_rate = rates.get("evidence_rate", 0.0)

    if conflict_rate > GUARD_THRESHOLDS["conflict_rate_max"]:
        result.triggered = True
        result.warnings.append(
            f"conflict_rate={conflict_rate:.3f} > "
            f"{GUARD_THRESHOLDS['conflict_rate_max']:.2f} (warning)"
        )

    if evidence_rate < GUARD_THRESHOLDS["evidence_rate_min"]:
        result.triggered = True
        result.warnings.append(
            f"evidence_rate={evidence_rate:.3f} < "
            f"{GUARD_THRESHOLDS['evidence_rate_min']:.2f} (warning)"
        )

    return result


def should_auto_pause(state: dict) -> AutoPauseResult:
    """Silver HITL-E auto-pause 판정 — 5개 임계치 검사.

    1개라도 위반 시 pause 권고 (HITL-E interrupt 발동).

    Args:
        state: EvolverState dict.

    Returns:
        AutoPauseResult with pause flag and violation details.
    """
    rates = state.get("metrics", {}).get("rates", {})
    result = AutoPauseResult()

    # 1. conflict_rate
    conflict_rate = rates.get("conflict_rate", 0.0)
    if conflict_rate > AUTO_PAUSE_THRESHOLDS["conflict_rate_max"]:
        result.violations.append(
            f"conflict_rate={conflict_rate:.3f} > {AUTO_PAUSE_THRESHOLDS['conflict_rate_max']}"
        )

    # 2. evidence_rate
    evidence_rate = rates.get("evidence_rate", 1.0)
    if evidence_rate < AUTO_PAUSE_THRESHOLDS["evidence_rate_min"]:
        result.violations.append(
            f"evidence_rate={evidence_rate:.3f} < {AUTO_PAUSE_THRESHOLDS['evidence_rate_min']}"
        )

    # 3. collect_failure_rate (collect_node 반환값에서 state에 기록)
    collect_failure_rate = state.get("collect_failure_rate", 0.0)
    if collect_failure_rate > AUTO_PAUSE_THRESHOLDS["collect_failure_rate_max"]:
        result.violations.append(
            f"collect_failure_rate={collect_failure_rate:.3f} > "
            f"{AUTO_PAUSE_THRESHOLDS['collect_failure_rate_max']}"
        )

    # 4. staleness_ratio
    staleness_ratio = rates.get("staleness_ratio", 0.0)
    if staleness_ratio > AUTO_PAUSE_THRESHOLDS["staleness_ratio_max"]:
        result.violations.append(
            f"staleness_ratio={staleness_ratio:.3f} > "
            f"{AUTO_PAUSE_THRESHOLDS['staleness_ratio_max']}"
        )

    # 5. avg_confidence
    avg_confidence = rates.get("avg_confidence", 1.0)
    if avg_confidence < AUTO_PAUSE_THRESHOLDS["avg_confidence_min"]:
        result.violations.append(
            f"avg_confidence={avg_confidence:.3f} < "
            f"{AUTO_PAUSE_THRESHOLDS['avg_confidence_min']}"
        )

    result.should_pause = len(result.violations) > 0
    if result.should_pause:
        logger.warning(
            "Auto-pause 발동: %d개 임계치 위반 — %s",
            len(result.violations), "; ".join(result.violations),
        )

    return result
