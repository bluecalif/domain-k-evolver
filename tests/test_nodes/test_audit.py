"""Executive Audit (Phase 4 Task 4.1) 테스트."""

from __future__ import annotations

import math

import pytest

from src.nodes.audit import (
    _analyze_cross_axis_coverage,
    _analyze_quality_trends,
    _analyze_yield_cost,
    _generate_policy_patches,
    _generate_recommendations,
    run_audit,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ku(ku_id: str, category: str, field: str = "price", status: str = "active") -> dict:
    return {
        "ku_id": ku_id,
        "entity_key": f"japan-travel:{category}:item-{ku_id[-2:]}",
        "field": field,
        "value": "test",
        "status": status,
        "evidence_links": ["EU-0001"],
        "confidence": 0.85,
    }


def _make_gu(
    gu_id: str, category: str, status: str = "resolved",
    geo: str = "", field: str = "price",
) -> dict:
    gu = {
        "gu_id": gu_id,
        "target": {"entity_key": f"japan-travel:{category}:item-{gu_id[-2:]}", "field": field},
        "status": status,
        "expected_utility": "medium",
        "gap_type": "missing",
    }
    if geo:
        gu["axis_tags"] = {"geography": geo}
    return gu


def _make_skeleton(categories: list[str], geo_anchors: list[str] | None = None) -> dict:
    skel = {
        "categories": [{"slug": c, "description": ""} for c in categories],
        "axes": [
            {"name": "category", "anchors": categories, "required": True},
        ],
    }
    if geo_anchors:
        skel["axes"].append({
            "name": "geography", "anchors": geo_anchors, "required": True,
        })
    return skel


def _make_trajectory(n: int, *, declining_yield: bool = False) -> list[dict]:
    entries = []
    for i in range(n):
        ku_active = 10 + (i * 5 if not declining_yield else (i * 5 if i < n // 2 else (n // 2) * 5 + 1))
        entries.append({
            "cycle": i + 1,
            "ku_active": ku_active,
            "ku_disputed": 0,
            "llm_calls": 20,
            "avg_confidence": 0.90 - (i * 0.01 if declining_yield else 0),
            "multi_evidence_rate": 0.60,
            "conflict_rate": 0.0,
        })
    return entries


# ---------------------------------------------------------------------------
# Coverage Analysis Tests
# ---------------------------------------------------------------------------

class TestCoverageAnalysis:
    def test_balanced_categories_no_finding(self):
        """균등 분포면 axis_imbalance finding 없음."""
        cats = ["transport", "dining", "accommodation"]
        kus = [_make_ku(f"KU-{i:04d}", cats[i % len(cats)]) for i in range(9)]
        skeleton = _make_skeleton(cats)

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        imbalance = [f for f in findings if f["category"] == "axis_imbalance"]
        assert len(imbalance) == 0

    def test_imbalanced_categories_finding(self):
        """한 카테고리에 KU 편중 → axis_imbalance."""
        cats = ["transport", "dining", "accommodation", "payment"]
        kus = [_make_ku(f"KU-{i:04d}", "transport") for i in range(10)]
        kus.append(_make_ku("KU-0010", "dining"))
        skeleton = _make_skeleton(cats)

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        imbalance = [f for f in findings if f["category"] == "axis_imbalance"]
        assert len(imbalance) == 1
        assert imbalance[0]["evidence"]["uniformity"] < 0.75

    def test_empty_category_critical_finding(self):
        """KU 0인 카테고리 → critical coverage_gap."""
        cats = ["transport", "dining"]
        kus = [_make_ku("KU-0001", "transport")]
        skeleton = _make_skeleton(cats)

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        critical = [f for f in findings if f["severity"] == "critical"]
        assert any("dining" in f["description"] for f in critical)

    def test_low_ku_category_warning(self):
        """KU < 3인 카테고리 → warning coverage_gap."""
        cats = ["transport", "dining"]
        kus = [
            _make_ku("KU-0001", "transport"),
            _make_ku("KU-0002", "transport"),
            _make_ku("KU-0003", "transport"),
            _make_ku("KU-0004", "dining"),  # dining = 1
        ]
        skeleton = _make_skeleton(cats)

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        warnings = [f for f in findings if f["severity"] == "warning" and "dining" in f["description"]]
        assert len(warnings) >= 1

    def test_geo_blind_spot_detection(self):
        """category x geography 교차 blind spot 감지."""
        cats = ["transport", "dining"]
        geos = ["tokyo", "osaka", "kyoto"]
        skeleton = _make_skeleton(cats, geos)

        # transport는 tokyo/osaka만 커버, dining은 전무
        gus = [
            _make_gu("GU-0001", "transport", "resolved", "tokyo"),
            _make_gu("GU-0002", "transport", "resolved", "osaka"),
        ]
        kus = [_make_ku("KU-0001", "transport"), _make_ku("KU-0002", "transport"),
               _make_ku("KU-0003", "dining")]

        findings = _analyze_cross_axis_coverage(kus, gus, skeleton)
        geo_findings = [f for f in findings if f.get("finding_id") == "F-COV-GEO"]
        assert len(geo_findings) == 1
        assert geo_findings[0]["evidence"]["blind_ratio"] > 0.40

    def test_no_geo_axis_no_crash(self):
        """geography axis 없어도 에러 없음."""
        cats = ["transport"]
        kus = [_make_ku("KU-0001", "transport")]
        skeleton = _make_skeleton(cats)  # no geo

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        assert isinstance(findings, list)

    def test_disputed_kus_excluded(self):
        """disputed KU는 coverage 계산에서 제외."""
        cats = ["transport", "dining"]
        kus = [
            _make_ku("KU-0001", "transport"),
            _make_ku("KU-0002", "transport"),
            _make_ku("KU-0003", "transport"),
            _make_ku("KU-0004", "dining", status="disputed"),
        ]
        skeleton = _make_skeleton(cats)

        findings = _analyze_cross_axis_coverage(kus, [], skeleton)
        # dining은 active 0개 → critical
        critical = [f for f in findings if f["severity"] == "critical"]
        assert any("dining" in f["description"] for f in critical)


# ---------------------------------------------------------------------------
# Yield/Cost Analysis Tests
# ---------------------------------------------------------------------------

class TestYieldCostAnalysis:
    def test_stable_yield_no_finding(self):
        """일정한 yield → finding 없음."""
        trajectory = _make_trajectory(6)
        findings = _analyze_yield_cost(trajectory)
        yield_findings = [f for f in findings if f["category"] == "yield_decline"]
        assert len(yield_findings) == 0

    def test_declining_yield_finding(self):
        """후반 yield 체감 → yield_decline."""
        # 전반: 매 cycle 5 KU 성장, 후반: 0~1 KU 성장
        trajectory = [
            {"cycle": 1, "ku_active": 10, "llm_calls": 20},
            {"cycle": 2, "ku_active": 15, "llm_calls": 20},
            {"cycle": 3, "ku_active": 20, "llm_calls": 20},
            {"cycle": 4, "ku_active": 25, "llm_calls": 20},
            {"cycle": 5, "ku_active": 25, "llm_calls": 20},
            {"cycle": 6, "ku_active": 25, "llm_calls": 20},
            {"cycle": 7, "ku_active": 25, "llm_calls": 20},
            {"cycle": 8, "ku_active": 25, "llm_calls": 20},
        ]
        findings = _analyze_yield_cost(trajectory)
        yield_findings = [f for f in findings if f["category"] == "yield_decline"]
        assert len(yield_findings) == 1

    def test_short_trajectory_no_crash(self):
        """trajectory 2개 미만이면 분석 생략."""
        findings = _analyze_yield_cost([{"cycle": 1, "ku_active": 5, "llm_calls": 10}])
        assert findings == []


# ---------------------------------------------------------------------------
# Quality Trends Tests
# ---------------------------------------------------------------------------

class TestQualityTrends:
    def test_confidence_decline_detected(self):
        """avg_confidence 3연속 하락 감지."""
        trajectory = [
            {"cycle": 1, "avg_confidence": 0.90, "multi_evidence_rate": 0.60},
            {"cycle": 2, "avg_confidence": 0.87, "multi_evidence_rate": 0.60},
            {"cycle": 3, "avg_confidence": 0.84, "multi_evidence_rate": 0.60},
        ]
        findings = _analyze_quality_trends(trajectory)
        assert any(f["finding_id"] == "F-QUAL-01" for f in findings)

    def test_stable_confidence_no_finding(self):
        """avg_confidence 안정 → finding 없음."""
        trajectory = [
            {"cycle": 1, "avg_confidence": 0.85, "multi_evidence_rate": 0.60},
            {"cycle": 2, "avg_confidence": 0.86, "multi_evidence_rate": 0.60},
            {"cycle": 3, "avg_confidence": 0.85, "multi_evidence_rate": 0.60},
        ]
        findings = _analyze_quality_trends(trajectory)
        assert not any(f["finding_id"] == "F-QUAL-01" for f in findings)

    def test_low_multi_evidence_detected(self):
        """multi_evidence_rate 3연속 < 0.50 감지."""
        trajectory = [
            {"cycle": 1, "avg_confidence": 0.85, "multi_evidence_rate": 0.40},
            {"cycle": 2, "avg_confidence": 0.85, "multi_evidence_rate": 0.42},
            {"cycle": 3, "avg_confidence": 0.85, "multi_evidence_rate": 0.38},
        ]
        findings = _analyze_quality_trends(trajectory)
        assert any(f["finding_id"] == "F-QUAL-02" for f in findings)


# ---------------------------------------------------------------------------
# Policy Patches Tests
# ---------------------------------------------------------------------------

class TestPolicyPatches:
    def test_max_3_patches(self):
        """한 Audit당 최대 3개 patch."""
        findings = [
            {"finding_id": f"F-QUAL-02", "category": "quality_issue"},
            {"finding_id": f"F-YIELD-01", "category": "yield_decline"},
        ] * 5  # 10개 findings
        policies = {
            "cross_validation": {
                "safety": {"min_sources": 1},
                "financial": {"min_sources": 1},
            },
            "ttl_defaults": {"price": 90, "policy": 60},
        }
        patches = _generate_policy_patches(findings, policies)
        assert len(patches) <= 3

    def test_multi_evidence_patch(self):
        """multi_evidence_rate 부족 → min_sources 증가 patch."""
        findings = [{"finding_id": "F-QUAL-02", "category": "quality_issue"}]
        policies = {"cross_validation": {"safety": {"min_sources": 1}}}
        patches = _generate_policy_patches(findings, policies)
        assert len(patches) == 1
        assert patches[0]["proposed_value"] == 2

    def test_yield_decline_ttl_patch(self):
        """yield 체감 → TTL 연장 patch."""
        findings = [{"finding_id": "F-YIELD-01", "category": "yield_decline"}]
        policies = {"ttl_defaults": {"price": 100, "policy": 60}}
        patches = _generate_policy_patches(findings, policies)
        assert len(patches) == 1
        assert patches[0]["target_field"] == "ttl_defaults.policy"
        assert patches[0]["proposed_value"] == 90  # 60 * 1.5

    def test_no_findings_no_patches(self):
        """findings 없으면 patch 없음."""
        patches = _generate_policy_patches([], {})
        assert patches == []


# ---------------------------------------------------------------------------
# Recommendations Tests
# ---------------------------------------------------------------------------

class TestRecommendations:
    def test_critical_finding_recommendation(self):
        findings = [{"finding_id": "F-01", "category": "coverage_gap", "severity": "critical"}]
        recs = _generate_recommendations(findings)
        assert any("Critical" in r for r in recs)

    def test_no_findings_healthy(self):
        recs = _generate_recommendations([])
        assert any("양호" in r for r in recs)


# ---------------------------------------------------------------------------
# Integration: run_audit
# ---------------------------------------------------------------------------

class TestRunAudit:
    def test_basic_audit_report_structure(self):
        """run_audit이 올바른 구조의 AuditReport 반환."""
        cats = ["transport", "dining"]
        skeleton = _make_skeleton(cats)
        kus = [_make_ku("KU-0001", "transport")]
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": skeleton,
            "policies": {},
            "current_cycle": 5,
        }
        trajectory = _make_trajectory(5)

        report = run_audit(state, trajectory, audit_cycle=5)

        assert "audit_cycle" in report
        assert report["audit_cycle"] == 5
        assert "window" in report
        assert "findings" in report
        assert "recommendations" in report
        assert "policy_patches" in report
        assert isinstance(report["findings"], list)

    def test_audit_with_window_filter(self):
        """window_start로 trajectory 필터링."""
        trajectory = _make_trajectory(10)
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "domain_skeleton": _make_skeleton(["a"]),
            "policies": {},
            "current_cycle": 10,
        }

        report = run_audit(state, trajectory, audit_cycle=10, window_start=6)
        assert report["window"][0] == 6
        assert report["window"][1] == 10

    def test_audit_empty_trajectory(self):
        """빈 trajectory에서도 에러 없음."""
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "domain_skeleton": _make_skeleton(["a"]),
            "policies": {},
        }
        report = run_audit(state, [])
        assert report["findings"] is not None

    def test_full_audit_with_findings(self):
        """커버리지 갭 있는 상태에서 audit → findings 생성."""
        cats = ["transport", "dining", "payment", "accommodation"]
        skeleton = _make_skeleton(cats)
        # transport만 KU 다수, 나머지 0
        kus = [_make_ku(f"KU-{i:04d}", "transport") for i in range(10)]
        state = {
            "knowledge_units": kus,
            "gap_map": [],
            "domain_skeleton": skeleton,
            "policies": {},
            "current_cycle": 5,
        }
        trajectory = _make_trajectory(5)

        report = run_audit(state, trajectory, audit_cycle=5)
        assert len(report["findings"]) > 0
        # 최소 3개 카테고리(dining, payment, accommodation)에서 critical/warning
        gap_findings = [f for f in report["findings"] if f["category"] == "coverage_gap"]
        assert len(gap_findings) >= 3
