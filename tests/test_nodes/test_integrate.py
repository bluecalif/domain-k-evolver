"""test_integrate — integrate_node 단위 테스트."""

from __future__ import annotations

import pytest

from src.adapters.llm_adapter import MockLLM
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
        assert ku["confidence"] == 0.85  # (0.8 + 0.9) / 2

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
        assert ku["confidence"] == 0.85

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
