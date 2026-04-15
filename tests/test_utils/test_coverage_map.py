"""P4-D2: coverage_map + Gini 통합 테스트."""

from __future__ import annotations

import pytest

from src.utils.coverage_map import build_coverage_map, _gini_coefficient


def _make_skeleton(categories: list[str]) -> dict:
    return {
        "domain": "test",
        "categories": [{"slug": c, "name": c.title()} for c in categories],
        "axes": [],
        "fields": [],
    }


def _make_ku(entity_key: str, field: str = "price") -> dict:
    return {
        "status": "active",
        "entity_key": entity_key,
        "field": field,
    }


class TestGiniCoefficient:
    """_gini_coefficient 단위 테스트."""

    def test_equal_distribution(self):
        """균등 분포 → Gini ≈ 0."""
        assert _gini_coefficient([10, 10, 10]) == pytest.approx(0.0, abs=0.01)

    def test_total_inequality(self):
        """완전 불균등 → Gini 높음."""
        # [0, 0, 30] → 높은 Gini
        gini = _gini_coefficient([0, 0, 30])
        assert gini > 0.5

    def test_empty_returns_zero(self):
        assert _gini_coefficient([]) == 0.0

    def test_all_zeros_returns_zero(self):
        assert _gini_coefficient([0, 0, 0]) == 0.0

    def test_single_value(self):
        assert _gini_coefficient([5]) == 0.0


class TestBuildCoverageMap:
    """build_coverage_map 통합 테스트."""

    def test_balanced_categories(self):
        """균등 분포 → Gini 낮음, deficit 낮음."""
        skeleton = _make_skeleton(["transport", "food", "culture"])
        state = {
            "knowledge_units": [
                _make_ku("d:transport:jr", "price"),
                _make_ku("d:transport:bus", "route"),
                _make_ku("d:food:ramen", "price"),
                _make_ku("d:food:sushi", "taste"),
                _make_ku("d:culture:temple", "hours"),
                _make_ku("d:culture:shrine", "location"),
            ],
            "domain_skeleton": skeleton,
        }
        result = build_coverage_map(state, skeleton, target_per_category=5)

        assert result["transport"]["ku_count"] == 2
        assert result["food"]["ku_count"] == 2
        assert result["culture"]["ku_count"] == 2

        summary = result["summary"]
        assert summary["category_gini"] == pytest.approx(0.0, abs=0.01)
        assert summary["gini_deficit_adjustment"] == pytest.approx(0.0, abs=0.01)

    def test_imbalanced_categories(self):
        """편중 분포 → Gini 높음, 소수 카테고리 deficit 상향."""
        skeleton = _make_skeleton(["transport", "food", "culture"])
        kus = [_make_ku(f"d:transport:item{i}", "price") for i in range(10)]
        # food 에 일부만 (deficit < 1.0 이어야 gini 보정 관찰 가능)
        kus.append(_make_ku("d:food:ramen", "price"))
        # culture 는 0
        state = {"knowledge_units": kus, "domain_skeleton": skeleton}

        result = build_coverage_map(state, skeleton, target_per_category=5)

        assert result["transport"]["ku_count"] == 10
        assert result["food"]["ku_count"] == 1
        assert result["culture"]["ku_count"] == 0

        summary = result["summary"]
        assert summary["category_gini"] > 0.45  # 불균형

        # food 의 deficit 는 base (0.8) + gini 보정 → base 보다 높아야 함
        assert result["food"]["deficit_score"] > result["food"]["base_deficit"]

    def test_single_category(self):
        """카테고리 1개 → Gini 0."""
        skeleton = _make_skeleton(["only"])
        state = {
            "knowledge_units": [_make_ku("d:only:a", "price")],
            "domain_skeleton": skeleton,
        }
        result = build_coverage_map(state, skeleton)
        assert result["summary"]["category_gini"] == 0.0

    def test_no_kus(self):
        """KU 없으면 deficit 전부 1.0."""
        skeleton = _make_skeleton(["a", "b"])
        state = {"knowledge_units": [], "domain_skeleton": skeleton}
        result = build_coverage_map(state, skeleton, target_per_category=5)

        assert result["a"]["ku_count"] == 0
        assert result["a"]["base_deficit"] == 1.0
        assert result["b"]["ku_count"] == 0

    def test_inactive_kus_excluded(self):
        """inactive KU 는 카운트 제외."""
        skeleton = _make_skeleton(["cat"])
        state = {
            "knowledge_units": [
                _make_ku("d:cat:a", "price"),
                {"status": "superseded", "entity_key": "d:cat:b", "field": "name"},
            ],
            "domain_skeleton": skeleton,
        }
        result = build_coverage_map(state, skeleton)
        assert result["cat"]["ku_count"] == 1

    def test_field_coverage_tracked(self):
        """필드별 KU 수 추적."""
        skeleton = _make_skeleton(["transport"])
        state = {
            "knowledge_units": [
                _make_ku("d:transport:jr", "price"),
                _make_ku("d:transport:bus", "price"),
                _make_ku("d:transport:train", "route"),
            ],
            "domain_skeleton": skeleton,
        }
        result = build_coverage_map(state, skeleton)
        fc = result["transport"]["field_coverage"]
        assert fc["price"] == 2
        assert fc["route"] == 1

    def test_gini_weight_zero_no_adjustment(self):
        """gini_weight=0 이면 deficit 보정 없음."""
        skeleton = _make_skeleton(["a", "b"])
        kus = [_make_ku(f"d:a:item{i}", "price") for i in range(10)]
        state = {"knowledge_units": kus, "domain_skeleton": skeleton}

        result = build_coverage_map(state, skeleton, gini_weight=0.0, target_per_category=5)
        assert result["b"]["deficit_score"] == result["b"]["base_deficit"]

    def test_disputed_kus_included(self):
        """disputed KU 도 카운트에 포함."""
        skeleton = _make_skeleton(["cat"])
        state = {
            "knowledge_units": [
                {"status": "disputed", "entity_key": "d:cat:a", "field": "price"},
            ],
            "domain_skeleton": skeleton,
        }
        result = build_coverage_map(state, skeleton)
        assert result["cat"]["ku_count"] == 1


class TestPlateauDetectorNovelty:
    """PlateauDetector novelty 확장 테스트 (P4-A4)."""

    def test_novelty_plateau_detected(self):
        """5 cycle 연속 novelty < 0.1 → plateau."""
        from src.utils.plateau_detector import PlateauDetector
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        history = [0.05, 0.03, 0.08, 0.02, 0.01]
        assert pd.is_novelty_plateau(history) is True

    def test_novelty_plateau_not_enough_cycles(self):
        """5 cycle 미만 → False."""
        from src.utils.plateau_detector import PlateauDetector
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        history = [0.05, 0.03, 0.08]
        assert pd.is_novelty_plateau(history) is False

    def test_novelty_plateau_one_above_threshold(self):
        """1개라도 threshold 이상이면 False."""
        from src.utils.plateau_detector import PlateauDetector
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        history = [0.05, 0.03, 0.15, 0.02, 0.01]
        assert pd.is_novelty_plateau(history) is False

    def test_is_any_plateau_novelty(self):
        """KU/GU plateau 아니어도 novelty plateau 면 True."""
        from src.utils.plateau_detector import PlateauDetector
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        # KU/GU plateau 아님 (history 부족)
        assert pd.is_plateau() is False
        # novelty plateau
        history = [0.05, 0.03, 0.08, 0.02, 0.01]
        assert pd.is_any_plateau(history) is True

    def test_plateau_reason_includes_novelty(self):
        """plateau_reason 에 novelty 정보 포함."""
        from src.utils.plateau_detector import PlateauDetector
        pd = PlateauDetector(window=3, novelty_threshold=0.1, novelty_window=5)
        history = [0.05, 0.03, 0.08, 0.02, 0.01]
        reason = pd.plateau_reason(history)
        assert "novelty_plateau" in reason
