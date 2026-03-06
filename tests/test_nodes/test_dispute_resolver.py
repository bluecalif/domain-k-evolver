"""test_dispute_resolver — Dispute Resolution 단위 테스트."""

from __future__ import annotations

import pytest

from src.adapters.llm_adapter import MockLLM
from src.nodes.dispute_resolver import (
    EVIDENCE_RATIO,
    evaluate_disputed_ku,
    resolve_dispute,
    resolve_disputes,
)


class TestEvaluateDisputedKU:
    def test_no_disputes_resolves(self) -> None:
        """disputes가 비어있으면 즉시 resolve."""
        ku = {"ku_id": "KU-0001", "status": "disputed", "evidence_links": ["EU-1"], "disputes": []}
        result = evaluate_disputed_ku(ku)
        assert result["action"] == "resolve"

    def test_evidence_majority_resolves(self) -> None:
        """evidence >= EVIDENCE_RATIO * disputes → 자동 resolve."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "evidence_links": ["EU-1", "EU-2", "EU-3", "EU-4"],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku)
        assert result["action"] == "resolve"
        assert "evidence majority" in result["reason"]

    def test_insufficient_evidence_keeps_disputed(self) -> None:
        """evidence < EVIDENCE_RATIO * disputes, LLM 없으면 keep_disputed."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "evidence_links": ["EU-1"],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku)
        assert result["action"] == "keep_disputed"

    def test_llm_resolve(self) -> None:
        """LLM이 resolve 판정."""
        llm = MockLLM(['{"verdict": "resolve", "reason": "minor update"}'])
        ku = {
            "ku_id": "KU-0001",
            "entity_key": "d:a:x",
            "field": "price",
            "value": "1000 JPY",
            "status": "disputed",
            "evidence_links": ["EU-1"],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku, llm=llm)
        assert result["action"] == "resolve"

    def test_llm_keep_disputed(self) -> None:
        """LLM이 keep_disputed 판정."""
        llm = MockLLM(['{"verdict": "keep_disputed", "reason": "genuine conflict"}'])
        ku = {
            "ku_id": "KU-0001",
            "entity_key": "d:a:x",
            "field": "price",
            "value": "1000 JPY",
            "status": "disputed",
            "evidence_links": ["EU-1"],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku, llm=llm)
        assert result["action"] == "keep_disputed"

    def test_llm_failure_fallback(self) -> None:
        """LLM 실패 시 keep_disputed fallback."""
        llm = MockLLM(["not valid json"])
        ku = {
            "ku_id": "KU-0001",
            "entity_key": "d:a:x",
            "field": "price",
            "value": "1000 JPY",
            "status": "disputed",
            "evidence_links": ["EU-1"],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku, llm=llm)
        assert result["action"] == "keep_disputed"

    def test_evidence_ratio_boundary(self) -> None:
        """정확히 EVIDENCE_RATIO 배 경계에서 resolve."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "evidence_links": [f"EU-{i}" for i in range(EVIDENCE_RATIO)],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku)
        assert result["action"] == "resolve"

    def test_evidence_below_ratio_needs_llm(self) -> None:
        """EVIDENCE_RATIO 미만이면 LLM 필요."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "evidence_links": [f"EU-{i}" for i in range(EVIDENCE_RATIO - 1)],
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        result = evaluate_disputed_ku(ku)
        assert result["action"] == "keep_disputed"


class TestResolveDispute:
    def test_resolve_changes_status(self) -> None:
        """resolve 시 status → active."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        decision = {"action": "resolve", "reason": "evidence majority"}
        assert resolve_dispute(ku, decision) is True
        assert ku["status"] == "active"

    def test_resolve_preserves_disputes(self) -> None:
        """Conflict-preserving: disputes 삭제하지 않고 resolved로 마킹."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        decision = {"action": "resolve", "reason": "evidence majority"}
        resolve_dispute(ku, decision)
        assert len(ku["disputes"]) == 1
        assert ku["disputes"][0]["resolution"] == "resolved"
        assert ku["disputes"][0]["resolution_reason"] == "evidence majority"

    def test_keep_disputed_no_change(self) -> None:
        """keep_disputed 시 status 변경 없음."""
        ku = {
            "ku_id": "KU-0001",
            "status": "disputed",
            "disputes": [{"nature": "conflict", "resolution": "hold"}],
        }
        decision = {"action": "keep_disputed", "reason": "genuine conflict"}
        assert resolve_dispute(ku, decision) is False
        assert ku["status"] == "disputed"


class TestResolveDisputes:
    def test_resolves_eligible_kus(self) -> None:
        """evidence 충분한 disputed KU만 해소."""
        kus = [
            {
                "ku_id": "KU-0001",
                "entity_key": "d:a:x",
                "field": "price",
                "status": "disputed",
                "evidence_links": ["EU-1", "EU-2", "EU-3"],
                "disputes": [{"nature": "conflict", "resolution": "hold"}],
            },
            {
                "ku_id": "KU-0002",
                "entity_key": "d:a:y",
                "field": "price",
                "status": "disputed",
                "evidence_links": ["EU-4"],
                "disputes": [{"nature": "conflict", "resolution": "hold"}],
            },
            {
                "ku_id": "KU-0003",
                "entity_key": "d:a:z",
                "field": "price",
                "status": "active",
                "evidence_links": ["EU-5"],
            },
        ]
        log = resolve_disputes(kus)
        assert len(log) == 1
        assert log[0]["ku_id"] == "KU-0001"
        assert kus[0]["status"] == "active"
        assert kus[1]["status"] == "disputed"
        assert kus[2]["status"] == "active"

    def test_empty_list(self) -> None:
        """빈 목록 처리."""
        assert resolve_disputes([]) == []

    def test_no_disputed(self) -> None:
        """disputed KU 없으면 빈 로그."""
        kus = [{"ku_id": "KU-0001", "status": "active"}]
        assert resolve_disputes(kus) == []

    def test_with_llm(self) -> None:
        """LLM 중재로 해소."""
        llm = MockLLM(['{"verdict": "resolve", "reason": "update not conflict"}'])
        kus = [
            {
                "ku_id": "KU-0001",
                "entity_key": "d:a:x",
                "field": "info",
                "status": "disputed",
                "evidence_links": ["EU-1"],
                "disputes": [{"nature": "value difference", "resolution": "hold"}],
            },
        ]
        log = resolve_disputes(kus, llm=llm)
        assert len(log) == 1
        assert kus[0]["status"] == "active"
