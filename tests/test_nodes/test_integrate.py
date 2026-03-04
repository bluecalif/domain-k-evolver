"""test_integrate — integrate_node 단위 테스트."""

from __future__ import annotations

import pytest

from src.nodes.integrate import integrate_node, _normalize_entity_key, _detect_conflict


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

    def test_hold_different_value(self) -> None:
        ku = {"value": "100 JPY", "entity_key": "d:a:x", "field": "price"}
        claim = {"value": "200 JPY"}
        assert _detect_conflict(ku, claim) == "hold"

    def test_condition_split(self) -> None:
        ku = {"value": "100 JPY", "conditions": {"season": "summer"}}
        claim = {"value": "200 JPY", "conditions": {"season": "winter"}}
        assert _detect_conflict(ku, claim) == "condition_split"


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
        assert ku["confidence"] == 0.85  # (0.8 + 0.9) / 2
