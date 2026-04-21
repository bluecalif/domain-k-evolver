"""entity_discovery_node — Entity Discovery stub.

S5a (S5a-T3~T11) 에서 full implementation.
현재 담당:
  - β aggressive mode 잔여 cycle 감소 (aggressive_mode_remaining decrement)
  - aggressive_mode_remaining > 0 일 때 β 파라미터 state 노출 (S5a-T11 에서 소비)

graph 삽입 위치 (D-183): plan_modify → entity_discovery → plan
"""

from __future__ import annotations

import logging

from src.state import EvolverState

logger = logging.getLogger(__name__)

# β aggressive mode 파라미터 (D-181) — S5a-T11 에서 entity_discovery 로직에 적용
AGGRESSIVE_DISCOVERY_TARGET_COUNT = 5   # 정상 1-2 → β 3-5
AGGRESSIVE_SOURCE_COUNT_MIN = 1         # 정상 source≥2 → β source≥1


def entity_discovery_node(state: EvolverState) -> dict:
    """Entity Discovery (stub).

    S5a full 구현 전까지:
    - aggressive_mode_remaining 을 1 감소시킴 (β 지속 기간 관리)
    - β 활성 상태를 로그로 기록
    """
    remaining = state.get("aggressive_mode_remaining", 0)

    if remaining <= 0:
        return {}

    new_remaining = remaining - 1
    logger.info(
        "entity_discovery: β aggressive mode active (remaining=%d → %d)",
        remaining, new_remaining,
    )

    return {"aggressive_mode_remaining": new_remaining}
