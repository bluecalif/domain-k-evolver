"""Metrics Guard — 위험 임계치 초과 시 경고/중단 판정.

conflict_rate > 0.30 또는 evidence_rate < 0.50 → halt 권고.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Hard-stop 임계치 (Task 2.13)
GUARD_THRESHOLDS = {
    "conflict_rate_max": 0.30,
    "evidence_rate_min": 0.50,
}


@dataclass
class GuardResult:
    """Guard 판정 결과."""

    triggered: bool = False
    warnings: list[str] = field(default_factory=list)


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
