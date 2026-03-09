"""test_integrate — integrate_node 단위 테스트."""

from __future__ import annotations

from datetime import date

import pytest

from src.adapters.llm_adapter import MockLLM
from src.nodes.integrate import (
    integrate_node,
    _normalize_entity_key,
    _detect_conflict,
    _find_source_gu,
    _copy_axis_tags,
    _generate_dynamic_gus,
    _infer_geography,
)


class TestNormalizeEntityKey:
    def test_lowercase(self) -> None:
        assert _normalize_entity_key("Japan-Travel:Transport:JR-Pass") == "japan-travel:transport:jr-pass"

    def test_space_to_hyphen(self) -> None:
        assert _normalize_entity_key("japan travel:transport:jr pass") == "japan-travel:transport:jr-pass"


class TestDetectConflict:
    def test_no_conflict_same_value(self) -> None:
        ku = {"value": "100 JPY", "entity_key": "d:a:x", "field": "price"}
        claim = {"value": "100 JPY"}
        assert _detect_conflict(ku, claim) is None

    def test_hold_different_value_no_llm(self) -> None:
        """LLM 없으면 결정론적 fallback → hold."""
        ku = {"value": "100 JPY", "entity_key": "d:a:x", "field": "price"}
        claim = {"value": "200 JPY"}
        assert _detect_conflict(ku, claim) == "hold"

    def test_condition_split(self) -> None:
        ku = {"value": "100 JPY", "conditions": {"season": "summer"}}
        claim = {"value": "200 JPY", "conditions": {"season": "winter"}}
        assert _detect_conflict(ku, claim) == "condition_split"

    def test_llm_verdict_update(self) -> None:
        """LLM이 update 판정 → 충돌 아님 (None)."""
        llm = MockLLM(['{"verdict": "update", "reason": "more detailed info"}'])
        ku = {"value": "JR Pass available", "entity_key": "d:t:jr", "field": "info"}
        claim = {"value": "JR Pass available for 7/14/21 days"}
        assert _detect_conflict(ku, claim, llm=llm) is None

    def test_llm_verdict_equivalent(self) -> None:
        """LLM이 equivalent 판정 → 충돌 아님 (None)."""
        llm = MockLLM(['{"verdict": "equivalent", "reason": "same meaning"}'])
        ku = {"value": "29,650 yen", "entity_key": "d:t:jr", "field": "price"}
        claim = {"value": "29650 JPY"}
        assert _detect_conflict(ku, claim, llm=llm) is None

    def test_llm_verdict_conflict(self) -> None:
        """LLM이 conflict 판정 → hold."""
        llm = MockLLM(['{"verdict": "conflict", "reason": "contradictory prices"}'])
        ku = {"value": "29,650 JPY", "entity_key": "d:t:jr", "field": "price"}
        claim = {"value": "50,000 JPY"}
        assert _detect_conflict(ku, claim, llm=llm) == "hold"

    def test_llm_failure_fallback(self) -> None:
        """LLM 실패 시 hold fallback."""
        llm = MockLLM(["not valid json at all"])
        ku = {"value": "100 JPY", "entity_key": "d:a:x", "field": "price"}
        claim = {"value": "200 JPY"}
        assert _detect_conflict(ku, claim, llm=llm) == "hold"


class TestIntegrateNode:
    def test_add_new_ku(self) -> None:
        state = {
            "knowledge_units": [],
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "price"}},
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "url": "http://x", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)

        assert len(result["knowledge_units"]) == 1
        ku = result["knowledge_units"][0]
        assert ku["ku_id"] == "KU-0001"
        assert ku["entity_key"] == "d:a:x"
        assert ku["status"] == "active"
        assert "EU-001" in ku["evidence_links"]

    def test_gu_resolved_after_integration(self) -> None:
        state = {
            "knowledge_units": [],
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "price"}},
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        gu = result["gap_map"][0]
        assert gu["status"] == "resolved"

    def test_conflict_hold(self) -> None:
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.9,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "2000 JPY",  # 다른 값 → conflict
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["status"] == "disputed"
        assert len(ku.get("disputes", [])) >= 1

    def test_disputed_ku_not_deleted(self) -> None:
        """불변원칙: Conflict-preserving — disputed KU는 삭제 불가."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "disputed",
                    "evidence_links": ["EU-001"],
                    "disputes": [{"nature": "test"}],
                },
            ],
            "gap_map": [],
            "current_claims": [],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        # disputed KU 여전히 존재
        assert any(ku["status"] == "disputed" for ku in result["knowledge_units"])

    def test_evidence_first_invariant(self) -> None:
        """불변원칙: Evidence-first — 새 active KU는 EU >= 1."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "y"}},
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "y",
                    "value": "test",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        for ku in result["knowledge_units"]:
            if ku["status"] == "active":
                assert len(ku["evidence_links"]) >= 1

    def test_dynamic_gu_discovery(self) -> None:
        """Trigger A: 인접 Gap 발견 시 동적 GU 생성."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:transport:bus", "field": "price"}},
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {
                "categories": [{"slug": "transport"}],
                "fields": [
                    {"name": "price", "categories": ["*"]},
                    {"name": "how_to_use", "categories": ["transport"]},
                    {"name": "tips", "categories": ["*"]},
                ],
            },
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        # how_to_use, tips에 대한 동적 GU가 생성될 수 있음
        new_gus = [gu for gu in result["gap_map"] if gu.get("trigger") == "A:adjacent_gap"]
        assert len(new_gus) >= 1

    def test_update_existing_ku(self) -> None:
        """같은 값으로 Claim → EU 추가, confidence 갱신."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",  # 같은 값
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-04", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert "EU-002" in ku["evidence_links"]
        # D-69: (0.8*2 + 0.9)/3 = 0.833, D-70: +0.03 boost (2 evidence) = 0.863
        assert ku["confidence"] == 0.863

    def test_llm_semantic_update_avoids_dispute(self) -> None:
        """LLM이 update 판정 → disputed 대신 EU 추가 + confidence 갱신."""
        llm = MockLLM(['{"verdict": "update", "reason": "more detailed info"}'])
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "description",
                    "value": "Good ramen shop",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "description",
                    "value": "Excellent ramen shop with 50 years of history",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-04", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state, llm=llm)
        ku = result["knowledge_units"][0]
        assert ku["status"] == "active"  # disputed가 아님!
        assert "EU-002" in ku["evidence_links"]
        # D-69: (0.8*2 + 0.9)/3 = 0.833, D-70: +0.03 boost (2 evidence) = 0.863
        assert ku["confidence"] == 0.863

    def test_llm_semantic_conflict_creates_dispute(self) -> None:
        """LLM이 conflict 판정 → disputed 처리."""
        llm = MockLLM(['{"verdict": "conflict", "reason": "contradictory prices"}'])
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.9,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "5000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state, llm=llm)
        ku = result["knowledge_units"][0]
        assert ku["status"] == "disputed"


# ---------------------------------------------------------------------------
# Task 5.1: axis_tags 전파
# ---------------------------------------------------------------------------

class TestAxisTagsPropagation:
    def test_find_source_gu(self) -> None:
        gap_map = [
            {"gu_id": "GU-0001", "axis_tags": {"geography": "tokyo"}},
            {"gu_id": "GU-0002", "axis_tags": {"geography": "osaka"}},
        ]
        assert _find_source_gu("GU-0002", gap_map)["gu_id"] == "GU-0002"
        assert _find_source_gu("GU-9999", gap_map) is None
        assert _find_source_gu("", gap_map) is None

    def test_copy_axis_tags(self) -> None:
        gu = {"gu_id": "GU-0001", "axis_tags": {"geography": "tokyo"}}
        tags = _copy_axis_tags(gu)
        assert tags == {"geography": "tokyo"}
        # 원본 변경 안 됨 (deep copy)
        tags["geography"] = "osaka"
        assert gu["axis_tags"]["geography"] == "tokyo"

    def test_copy_axis_tags_none(self) -> None:
        assert _copy_axis_tags(None) == {}
        assert _copy_axis_tags({"gu_id": "GU-0001"}) == {}

    def test_new_ku_inherits_axis_tags(self) -> None:
        """신규 KU 생성 시 source GU의 axis_tags가 복사되는지 확인."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                    "axis_tags": {"geography": "tokyo"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["axis_tags"] == {"geography": "tokyo"}

    def test_geography_inferred_when_gu_has_no_axis_tags(self) -> None:
        """source GU에 axis_tags 없어도 geography는 entity_key에서 추론."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "d:a:x", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "100 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # geography 축이 없는 skeleton → nationwide 기본값
        assert ku["axis_tags"]["geography"] == "nationwide"

    def test_condition_split_inherits_axis_tags(self) -> None:
        """condition_split 새 KU도 axis_tags 상속."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "conditions": {"season": "summer"},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0002", "status": "open",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                    "axis_tags": {"geography": "osaka"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "300 JPY",
                    "conditions": {"season": "winter"},
                    "source_gu_id": "GU-0002",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-04", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        new_ku = [ku for ku in result["knowledge_units"] if ku["ku_id"] == "KU-0002"][0]
        assert new_ku["axis_tags"] == {"geography": "osaka"}


# ---------------------------------------------------------------------------
# Task 5.2: geography 추론
# ---------------------------------------------------------------------------

_GEO_SKELETON = {
    "categories": [{"slug": "transport"}],
    "fields": [],
    "axes": [
        {"name": "geography", "anchors": ["tokyo", "osaka", "kyoto", "rural", "nationwide"]},
    ],
}


class TestGeographyInference:
    def test_tokyo_in_entity_key(self) -> None:
        assert _infer_geography("japan-travel:transport:tokyo-metro", _GEO_SKELETON) == "tokyo"

    def test_osaka_in_entity_key(self) -> None:
        assert _infer_geography("japan-travel:dining:osaka-takoyaki", _GEO_SKELETON) == "osaka"

    def test_kyoto_in_entity_key(self) -> None:
        assert _infer_geography("japan-travel:attraction:kyoto-kinkakuji", _GEO_SKELETON) == "kyoto"

    def test_no_match_defaults_nationwide(self) -> None:
        assert _infer_geography("japan-travel:regulation:visa-waiver", _GEO_SKELETON) == "nationwide"

    def test_no_geography_axis(self) -> None:
        skeleton = {"categories": [], "fields": [], "axes": []}
        assert _infer_geography("japan-travel:transport:tokyo-metro", skeleton) == "nationwide"

    def test_integrate_infers_geography_when_gu_has_none(self) -> None:
        """GU에 axis_tags 없어도 entity_key에서 geography 추론."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "japan-travel:transport:tokyo-metro", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "japan-travel:transport:tokyo-metro",
                    "field": "price",
                    "value": "170 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": _GEO_SKELETON,
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["axis_tags"]["geography"] == "tokyo"

    def test_gu_geography_takes_precedence(self) -> None:
        """GU에 geography가 있으면 entity_key 추론보다 우선."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "japan-travel:transport:tokyo-metro", "field": "price"},
                    "axis_tags": {"geography": "osaka"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "japan-travel:transport:tokyo-metro",
                    "field": "price",
                    "value": "170 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": _GEO_SKELETON,
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["axis_tags"]["geography"] == "osaka"


# ---------------------------------------------------------------------------
# Task 5.3: 동적 GU geography 부여
# ---------------------------------------------------------------------------

class TestDynamicGuGeography:
    def test_dynamic_gu_gets_geography(self) -> None:
        """동적 GU 생성 시 부모 claim entity_key에서 geography 추론."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "japan-travel:transport:tokyo-metro", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "japan-travel:transport:tokyo-metro",
                    "field": "price",
                    "value": "170 JPY",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {
                "categories": [{"slug": "transport"}],
                "fields": [
                    {"name": "price", "categories": ["*"]},
                    {"name": "how_to_use", "categories": ["transport"]},
                ],
                "axes": [
                    {"name": "geography", "anchors": ["tokyo", "osaka", "kyoto", "rural", "nationwide"]},
                ],
            },
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        dynamic_gus = [gu for gu in result["gap_map"] if gu.get("trigger") == "A:adjacent_gap"]
        assert len(dynamic_gus) >= 1
        for dgu in dynamic_gus:
            assert dgu["axis_tags"]["geography"] == "tokyo"

    def test_dynamic_gu_nationwide_fallback(self) -> None:
        """entity_key에 지역 없으면 nationwide."""
        state = {
            "knowledge_units": [],
            "gap_map": [
                {
                    "gu_id": "GU-0001", "status": "open",
                    "target": {"entity_key": "japan-travel:regulation:visa-waiver", "field": "policy"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "japan-travel:regulation:visa-waiver",
                    "field": "policy",
                    "value": "90 days visa-free",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-04", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {
                "categories": [{"slug": "regulation"}],
                "fields": [
                    {"name": "policy", "categories": ["regulation"]},
                    {"name": "tips", "categories": ["*"]},
                ],
                "axes": [
                    {"name": "geography", "anchors": ["tokyo", "osaka", "kyoto", "rural", "nationwide"]},
                ],
            },
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        dynamic_gus = [gu for gu in result["gap_map"] if gu.get("trigger") == "A:adjacent_gap"]
        assert len(dynamic_gus) >= 1
        for dgu in dynamic_gus:
            assert dgu["axis_tags"]["geography"] == "nationwide"


# ---------------------------------------------------------------------------
# Task 5.6: Refresh 통합 시 KU 갱신
# ---------------------------------------------------------------------------

class TestRefreshIntegration:
    def test_stale_gu_refreshes_existing_ku(self) -> None:
        """gap_type=stale인 GU 기반 claim → 기존 KU 갱신 (충돌 없이)."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "observed_at": "2025-01-01",
                    "validity": {"ttl_days": 180},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0010", "status": "open",
                    "gap_type": "stale",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                    "trigger": "D:stale_refresh",
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "220 JPY",
                    "source_gu_id": "GU-0010",
                    "evidence": {"eu_id": "EU-010", "observed_at": "2026-03-07", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # D-62: observed_at = today (evidence date 무시)
        assert ku["observed_at"] == date.today().isoformat()
        # EU 추가
        assert "EU-010" in ku["evidence_links"]
        # D-63: confidence 가중 0.3:0.7 → 0.8*0.3 + 0.9*0.7 = 0.87
        assert ku["confidence"] == 0.87
        # TTL 리셋
        assert ku["validity"]["ttl_days"] == 180
        # GU resolved
        gu = result["gap_map"][0]
        assert gu["status"] == "resolved"
        # claim result
        assert result["current_claims"][0]["integration_result"] == "refreshed"

    def test_stale_gu_skips_conflict_detection(self) -> None:
        """stale refresh는 값이 달라도 충돌 감지하지 않음."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "observed_at": "2025-01-01",
                    "validity": {"ttl_days": 180},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0010", "status": "open",
                    "gap_type": "stale",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "500 JPY",  # 다른 값이지만 stale이므로 갱신
                    "source_gu_id": "GU-0010",
                    "evidence": {"eu_id": "EU-010", "observed_at": "2026-03-07", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # disputed가 아님
        assert ku["status"] == "active"
        assert result["current_claims"][0]["integration_result"] == "refreshed"

    def test_stale_refresh_with_ttl_from_policies(self) -> None:
        """policies.ttl_defaults에서 TTL 읽기."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "observed_at": "2025-01-01",
                    "validity": {"ttl_days": 180},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0010", "status": "open",
                    "gap_type": "stale",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "220 JPY",
                    "source_gu_id": "GU-0010",
                    "evidence": {"eu_id": "EU-010", "observed_at": "2026-03-07", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
            "policies": {"ttl_defaults": {"transport": 90, "default": 180}},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["validity"]["ttl_days"] == 90


# ---------------------------------------------------------------------------
# Task 5.8: Field 다양성 억제
# ---------------------------------------------------------------------------

class TestFieldDiversitySuppression:
    _SKELETON = {
        "categories": [{"slug": "transport"}],
        "fields": [
            {"name": "price", "categories": ["*"]},
            {"name": "tips", "categories": ["*"]},
            {"name": "how_to_use", "categories": ["transport"]},
        ],
        "axes": [],
    }

    def test_overrepresented_field_suppressed(self) -> None:
        """count > mean×1.5인 필드 GU 생성 억제."""
        # price=10, tips=2, how_to_use=1 → mean=4.33, threshold=6.5
        # price(10) > 6.5 → suppressed
        kus = [
            {"ku_id": f"KU-p{i}", "entity_key": f"d:transport:e{i}",
             "field": "price", "status": "active"}
            for i in range(10)
        ] + [
            {"ku_id": f"KU-t{i}", "entity_key": f"d:transport:et{i}",
             "field": "tips", "status": "active"}
            for i in range(2)
        ] + [
            {"ku_id": "KU-h1", "entity_key": "d:transport:eh1",
             "field": "how_to_use", "status": "active"},
        ]
        claim = {
            "claim_id": "CL-001",
            "entity_key": "d:transport:new-bus",
            "field": "price",
        }
        gus = _generate_dynamic_gus(
            claim, [], self._SKELETON, "normal", 5, kus=kus,
        )
        fields = {gu["target"]["field"] for gu in gus}
        assert "price" not in fields  # suppressed
        assert "tips" in fields or "how_to_use" in fields

    def test_no_suppression_when_balanced(self) -> None:
        """균등 분포시 억제 없음."""
        kus = [
            {"ku_id": f"KU-{f}-{i}", "entity_key": f"d:transport:e{i}",
             "field": f, "status": "active"}
            for f in ["price", "tips", "how_to_use"]
            for i in range(3)
        ]
        claim = {
            "claim_id": "CL-001",
            "entity_key": "d:transport:new-train",
            "field": "price",
        }
        gus = _generate_dynamic_gus(
            claim, [], self._SKELETON, "normal", 5, kus=kus,
        )
        fields = {gu["target"]["field"] for gu in gus}
        assert "tips" in fields
        assert "how_to_use" in fields

    def test_suppression_in_integrate_node(self) -> None:
        """integrate_node에서 과다 필드 동적 GU 억제 확인."""
        kus = [
            {"ku_id": f"KU-{i}", "entity_key": f"d:transport:e{i}",
             "field": "price", "status": "active",
             "evidence_links": ["EU-1"], "confidence": 0.9}
            for i in range(10)
        ]
        state = {
            "knowledge_units": kus,
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:transport:bus", "field": "how_to_use"}},
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "how_to_use",
                    "value": "Tap IC card",
                    "source_gu_id": "GU-0001",
                    "evidence": {"eu_id": "EU-100", "observed_at": "2026-03-07", "credibility": 0.9},
                },
            ],
            "domain_skeleton": self._SKELETON,
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        dynamic_gus = [gu for gu in result["gap_map"] if gu.get("trigger") == "A:adjacent_gap"]
        dynamic_fields = {gu["target"]["field"] for gu in dynamic_gus}
        # price is overrepresented (10 vs mean~3.7, threshold~5.5) → suppressed
        assert "price" not in dynamic_fields


# ---------------------------------------------------------------------------
# Stage E: Fix A — observed_at = today (D-62)
# ---------------------------------------------------------------------------

class TestStaleRefreshObservedAtToday:
    def test_observed_at_ignores_evidence_date(self) -> None:
        """D-62: stale refresh는 evidence의 old observed_at를 무시하고 today 사용."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "observed_at": "2024-06-01",  # 21개월 전 seed
                    "validity": {"ttl_days": 180},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.7,
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0010", "status": "open",
                    "gap_type": "stale",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "220 JPY",
                    "source_gu_id": "GU-0010",
                    # evidence has old date — should NOT be used
                    "evidence": {"eu_id": "EU-010", "observed_at": "2024-06-15", "credibility": 0.85},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # Must be today, not "2024-06-15"
        assert ku["observed_at"] == date.today().isoformat()
        assert ku["observed_at"] != "2024-06-15"
        assert ku["observed_at"] != "2024-06-01"


# ---------------------------------------------------------------------------
# Stage E: Fix B — confidence 가중 0.3:0.7 (D-63)
# ---------------------------------------------------------------------------

class TestStaleRefreshWeightedConfidence:
    def test_weighted_confidence_favors_new(self) -> None:
        """D-63: old*0.3 + new*0.7 → 최신 evidence 우선."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "200 JPY",
                    "observed_at": "2024-06-01",
                    "validity": {"ttl_days": 180},
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.6,  # old, low
                },
            ],
            "gap_map": [
                {
                    "gu_id": "GU-0010", "status": "open",
                    "gap_type": "stale",
                    "target": {"entity_key": "d:transport:bus", "field": "price"},
                },
            ],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:transport:bus",
                    "field": "price",
                    "value": "220 JPY",
                    "source_gu_id": "GU-0010",
                    "evidence": {"eu_id": "EU-010", "observed_at": "2026-03-07", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # 0.6 * 0.3 + 0.9 * 0.7 = 0.18 + 0.63 = 0.81
        assert ku["confidence"] == 0.81
        # 단순 평균이었다면 (0.6+0.9)/2 = 0.75
        assert ku["confidence"] > 0.75


# ---------------------------------------------------------------------------
# Stage E-2 테스트: D-67~D-70
# ---------------------------------------------------------------------------

class TestStageE2:
    """D-67~D-70: observed_at=today, evidence-count 가중 평균, multi-evidence boost."""

    def test_d67_new_ku_observed_at_today(self) -> None:
        """D-67: 신규 KU는 evidence의 오래된 observed_at 무시, today 사용."""
        state = {
            "knowledge_units": [],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2024-01-01", "credibility": 0.8},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["observed_at"] == date.today().isoformat()

    def test_d67_condition_split_observed_at_today(self) -> None:
        """D-67: condition_split KU도 today 사용."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "2000 JPY",
                    "conditions": {"season": "summer"},
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2024-06-01", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        split_kus = [k for k in result["knowledge_units"] if k.get("conditions")]
        assert len(split_kus) >= 1
        assert split_kus[0]["observed_at"] == date.today().isoformat()

    def test_d68_update_observed_at_today(self) -> None:
        """D-68: 일반 업데이트 시 observed_at이 today로 갱신."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                    "observed_at": "2024-01-01",
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2024-06-01", "credibility": 0.9},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        assert ku["observed_at"] == date.today().isoformat()

    def test_d69_evidence_count_weighted_average(self) -> None:
        """D-69: evidence 3개인 KU에 새 evidence 추가 → (old*3+new)/4."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001", "EU-002", "EU-003"],
                    "confidence": 0.9,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-004",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-004", "observed_at": "2026-03-09", "credibility": 0.7},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # N=4 (after append), weighted: (0.9*4 + 0.7)/5 = 4.3/5 = 0.86
        # D-70 boost: 4 evidence → +0.07, min(0.86+0.07, 0.95) = 0.93
        assert ku["confidence"] == 0.93

    def test_d70_multi_evidence_boost_2(self) -> None:
        """D-70: evidence 2개 → +0.03 boost."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001"],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-002",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-002", "observed_at": "2026-03-09", "credibility": 0.7},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # N=2 (after append), weighted: (0.8*2 + 0.7)/3 = 2.3/3 ≈ 0.767
        # D-70 boost: 2 evidence → +0.03 → 0.797
        assert ku["confidence"] == 0.797

    def test_d70_boost_cap_095(self) -> None:
        """D-70: boost 적용 후 0.95 cap."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": ["EU-001", "EU-002", "EU-003"],
                    "confidence": 0.95,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-004",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-004", "observed_at": "2026-03-09", "credibility": 0.95},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # 4 evidence → boost +0.07, but capped at 0.95
        assert ku["confidence"] <= 0.95

    def test_d70_no_boost_single_evidence(self) -> None:
        """D-70: evidence 1개 → boost 없음."""
        state = {
            "knowledge_units": [
                {
                    "ku_id": "KU-0001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "status": "active",
                    "evidence_links": [],
                    "confidence": 0.8,
                },
            ],
            "gap_map": [],
            "current_claims": [
                {
                    "claim_id": "CL-001",
                    "entity_key": "d:a:x",
                    "field": "price",
                    "value": "1000 JPY",
                    "source_gu_id": "",
                    "evidence": {"eu_id": "EU-001", "observed_at": "2026-03-09", "credibility": 0.7},
                },
            ],
            "domain_skeleton": {"categories": [], "fields": []},
            "current_mode": {"mode": "normal"},
        }
        result = integrate_node(state)
        ku = result["knowledge_units"][0]
        # N=1 (after append), weighted: (0.8*1 + 0.7)/2 = 0.75
        # 1 evidence → no boost
        assert ku["confidence"] == 0.75
