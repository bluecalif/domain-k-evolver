"""PlateauDetector 테스트."""

from __future__ import annotations

import pytest

from src.utils.plateau_detector import PlateauDetector


def _make_state(ku_active: int, gu_resolved: int, ku_disputed: int = 0) -> dict:
    """테스트용 간이 State 생성."""
    kus = [{"status": "active"} for _ in range(ku_active)]
    kus += [{"status": "disputed"} for _ in range(ku_disputed)]
    gus = [{"status": "resolved"} for _ in range(gu_resolved)]
    return {"knowledge_units": kus, "gap_map": gus}


class TestPlateauDetector:
    def test_window_too_small_raises(self):
        with pytest.raises(ValueError, match="plateau_window must be >= 2"):
            PlateauDetector(window=1)

    def test_no_plateau_before_window(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(10, 5))
        assert not pd.is_plateau()

    def test_plateau_detected(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(10, 5))
        pd.record(3, _make_state(10, 5))
        assert pd.is_plateau()

    def test_no_plateau_when_ku_changes(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(11, 5))
        pd.record(3, _make_state(11, 5))
        assert not pd.is_plateau()

    def test_no_plateau_when_gu_changes(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(10, 5))
        pd.record(3, _make_state(10, 6))
        assert not pd.is_plateau()

    def test_plateau_after_growth_then_stall(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(12, 7))
        pd.record(3, _make_state(15, 9))
        assert not pd.is_plateau()
        pd.record(4, _make_state(15, 9))
        assert not pd.is_plateau()
        pd.record(5, _make_state(15, 9))
        assert pd.is_plateau()

    def test_window_4(self):
        pd = PlateauDetector(window=4)
        for i in range(1, 4):
            pd.record(i, _make_state(10, 5))
        assert not pd.is_plateau()
        pd.record(4, _make_state(10, 5))
        assert pd.is_plateau()

    def test_history_property(self):
        pd = PlateauDetector(window=2)
        pd.record(1, _make_state(10, 5))
        pd.record(2, _make_state(12, 6))
        assert len(pd.history) == 2
        assert pd.history[0].ku_active == 10
        assert pd.history[1].ku_active == 12

    def test_empty_state(self):
        pd = PlateauDetector(window=2)
        pd.record(1, {})
        pd.record(2, {})
        assert pd.is_plateau()

    def test_conflict_rate_tracked(self):
        pd = PlateauDetector(window=2)
        pd.record(1, _make_state(8, 5, ku_disputed=2))
        assert pd.history[0].conflict_rate == pytest.approx(0.2)

    def test_is_stuck_plateau_high_conflict(self):
        """plateau + high conflict_rate → stuck."""
        pd = PlateauDetector(window=2, conflict_rate_threshold=0.15)
        pd.record(1, _make_state(8, 5, ku_disputed=4))
        pd.record(2, _make_state(8, 5, ku_disputed=4))
        assert pd.is_plateau()
        assert pd.is_stuck()
        assert "stuck" in pd.plateau_reason()

    def test_not_stuck_plateau_low_conflict(self):
        """plateau + low conflict_rate → 정상 수렴."""
        pd = PlateauDetector(window=2, conflict_rate_threshold=0.15)
        pd.record(1, _make_state(10, 5, ku_disputed=1))
        pd.record(2, _make_state(10, 5, ku_disputed=1))
        assert pd.is_plateau()
        assert not pd.is_stuck()
        assert "converged" in pd.plateau_reason()

    def test_not_stuck_no_plateau(self):
        pd = PlateauDetector(window=3)
        pd.record(1, _make_state(10, 5, ku_disputed=5))
        pd.record(2, _make_state(11, 6, ku_disputed=5))
        assert not pd.is_stuck()
        assert pd.plateau_reason() == ""
