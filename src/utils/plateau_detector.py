"""Plateau Detector — 연속 N사이클 KU/GU 변화 0 감지 + novelty 기반 정체.

연속 plateau_window 사이클 동안 KU active 수와 GU resolved 수가
변하지 않으면 plateau로 판정.

Phase 3 확장: conflict_rate 복합 조건.
- plateau + conflict_rate > threshold → stuck 상태 (조기 종료 권장)
- plateau + conflict_rate ≤ threshold → 안정적 수렴 (정상 종료)

P4 확장: novelty 기반 plateau.
- novelty < novelty_threshold × novelty_window 연속 cycle → novelty_plateau
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlateauSnapshot:
    """사이클 종료 시점의 KU/GU 스냅샷."""

    cycle: int
    ku_active: int
    gu_resolved: int
    conflict_rate: float = 0.0


class PlateauDetector:
    """연속 N사이클 변화 없음 + novelty 정체 감지."""

    # P4 novelty plateau 기본값
    NOVELTY_THRESHOLD = 0.1    # novelty 이하면 정체 판정
    NOVELTY_WINDOW = 5         # 연속 N cycle 정체 시 plateau

    def __init__(
        self,
        window: int = 3,
        conflict_rate_threshold: float = 0.15,
        *,
        novelty_threshold: float = NOVELTY_THRESHOLD,
        novelty_window: int = NOVELTY_WINDOW,
    ) -> None:
        if window < 2:
            raise ValueError("plateau_window must be >= 2")
        self.window = window
        self.conflict_rate_threshold = conflict_rate_threshold
        self.novelty_threshold = novelty_threshold
        self.novelty_window = novelty_window
        self._history: list[PlateauSnapshot] = []

    def record(self, cycle: int, state: dict) -> None:
        """사이클 종료 후 스냅샷 기록."""
        kus = state.get("knowledge_units", [])
        gus = state.get("gap_map", [])

        active = [k for k in kus if k.get("status") == "active"]
        disputed = [k for k in kus if k.get("status") == "disputed"]
        total_ad = len(active) + len(disputed)
        conflict_rate = len(disputed) / total_ad if total_ad > 0 else 0.0

        self._history.append(PlateauSnapshot(
            cycle=cycle,
            ku_active=len(active),
            gu_resolved=sum(1 for g in gus if g.get("status") == "resolved"),
            conflict_rate=conflict_rate,
        ))

    def is_plateau(self) -> bool:
        """최근 window 사이클 동안 KU/GU 변화가 0이면 True."""
        if len(self._history) < self.window:
            return False
        recent = self._history[-self.window:]
        first = recent[0]
        return all(
            s.ku_active == first.ku_active and s.gu_resolved == first.gu_resolved
            for s in recent[1:]
        )

    def is_novelty_plateau(self, novelty_history: list[float]) -> bool:
        """최근 novelty_window cycle 동안 novelty < threshold 이면 True (P4)."""
        if len(novelty_history) < self.novelty_window:
            return False
        recent = novelty_history[-self.novelty_window:]
        return all(n < self.novelty_threshold for n in recent)

    def is_any_plateau(self, novelty_history: list[float] | None = None) -> bool:
        """KU/GU plateau 또는 novelty plateau 중 하나라도 True."""
        if self.is_plateau():
            return True
        if novelty_history and self.is_novelty_plateau(novelty_history):
            return True
        return False

    def is_stuck(self) -> bool:
        """plateau + conflict_rate > threshold → 개선 불가 상태."""
        if not self.is_plateau():
            return False
        latest = self._history[-1]
        return latest.conflict_rate > self.conflict_rate_threshold

    def plateau_reason(self, novelty_history: list[float] | None = None) -> str:
        """plateau 판정 시 사유 반환."""
        reasons: list[str] = []

        if self.is_plateau():
            latest = self._history[-1]
            if latest.conflict_rate > self.conflict_rate_threshold:
                reasons.append(
                    f"stuck: plateau + conflict_rate {latest.conflict_rate:.3f} "
                    f"> {self.conflict_rate_threshold}"
                )
            else:
                reasons.append("converged: plateau + low conflict_rate")

        if novelty_history and self.is_novelty_plateau(novelty_history):
            recent = novelty_history[-self.novelty_window:]
            avg_n = sum(recent) / len(recent)
            reasons.append(
                f"novelty_plateau: avg={avg_n:.3f} < {self.novelty_threshold} "
                f"for {self.novelty_window} cycles"
            )

        return " | ".join(reasons) if reasons else ""

    @property
    def history(self) -> list[PlateauSnapshot]:
        return list(self._history)
