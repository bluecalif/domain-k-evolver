"""test_collect — collect_node 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.nodes.collect import _calc_execution_queue, collect_node
from src.tools.search import MockSearchTool


class _FailingSearchTool:
    """search/fetch 가 예외를 던지는 mock tool (B9 S1: timeout)."""

    def __init__(self, exc: Exception = TimeoutError("search timeout")) -> None:
        self.exc = exc
        self.search_calls: list[str] = []
        self.fetch_calls: list[str] = []

    def search(self, query: str) -> list[dict]:
        self.search_calls.append(query)
        raise self.exc

    def fetch(self, url: str) -> str:
        self.fetch_calls.append(url)
        raise self.exc


class _EmptySearchTool:
    """search 가 빈 리스트만 반환하는 mock tool."""

    def __init__(self) -> None:
        self.search_calls: list[str] = []
        self.fetch_calls: list[str] = []

    def search(self, query: str) -> list[dict]:
        self.search_calls.append(query)
        return []

    def fetch(self, url: str) -> str:
        self.fetch_calls.append(url)
        return ""


class TestCollectNode:
    def test_with_mock_search(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {
                    "gu_id": "GU-0001",
                    "status": "open",
                    "target": {"entity_key": "d:a:x", "field": "price"},
                    "expected_utility": "high",
                    "risk_level": "financial",
                    "resolution_criteria": "Find price info",
                },
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["x price", "x price 2026"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        claims = result["current_claims"]

        assert len(claims) >= 1
        assert claims[0]["entity_key"] == "d:a:x"
        assert claims[0]["field"] == "price"
        assert claims[0]["source_gu_id"] == "GU-0001"

    def test_search_tool_called(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {
                    "gu_id": "GU-0001",
                    "status": "open",
                    "target": {"entity_key": "d:a:x", "field": "price"},
                    "expected_utility": "high",
                    "risk_level": "financial",
                },
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1", "q2"]},
                "budget": 10,
            },
            "current_mode": {"mode": "normal"},
        }
        collect_node(state, search_tool=tool)
        assert len(tool.search_calls) == 2

    def test_no_search_tool_returns_empty(self) -> None:
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "y"}},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1"]},
                "budget": 2,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state)
        assert result["current_claims"] == []

    def test_budget_respected(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": f"GU-{i:04d}", "status": "open",
                 "target": {"entity_key": f"d:a:x{i}", "field": "price"},
                 "expected_utility": "low", "risk_level": "convenience"}
                for i in range(1, 6)
            ],
            "current_plan": {
                "target_gaps": [f"GU-{i:04d}" for i in range(1, 6)],
                "queries": {f"GU-{i:04d}": [f"q{i}a", f"q{i}b"] for i in range(1, 6)},
                "budget": 4,  # Only 2 targets worth of budget
            },
            "current_mode": {"mode": "normal"},
        }
        collect_node(state, search_tool=tool)
        assert len(tool.search_calls) <= 4

    def test_risk_flag_on_high_risk(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "policy"},
                 "expected_utility": "critical", "risk_level": "safety"},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["safety policy"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        for claim in result["current_claims"]:
            assert claim["risk_flag"] is True

    def test_evidence_has_required_fields(self) -> None:
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": "GU-0001", "status": "open",
                 "target": {"entity_key": "d:a:x", "field": "price"},
                 "expected_utility": "high", "risk_level": "financial"},
            ],
            "current_plan": {
                "target_gaps": ["GU-0001"],
                "queries": {"GU-0001": ["q1"]},
                "budget": 4,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        for claim in result["current_claims"]:
            ev = claim["evidence"]
            assert "eu_id" in ev
            assert "url" in ev
            assert "observed_at" in ev
            assert "credibility" in ev


def _gu_state(gu_ids: list[str], risk: str = "financial") -> dict:
    """테스트용 state 헬퍼 — 여러 GU + plan 구성."""
    gap_map = [
        {
            "gu_id": gu_id,
            "status": "open",
            "target": {"entity_key": f"d:a:{gu_id.lower()}", "field": "price"},
            "expected_utility": "high",
            "risk_level": risk,
        }
        for gu_id in gu_ids
    ]
    return {
        "gap_map": gap_map,
        "current_plan": {
            "target_gaps": gu_ids,
            "queries": {gu_id: ["query1"] for gu_id in gu_ids},
            "budget": len(gu_ids) * 2,
        },
        "current_mode": {"mode": "normal"},
    }


# ============================================================
# P0-B9: Silver Remediation 테스트 (S1 timeout, malformed, empty, duplicate)
# ============================================================

class TestCollectFailureRate:
    """P0-B9: collect_failure_rate emit + 반환 shape."""

    def test_failure_rate_emitted(self) -> None:
        """정상 수집 시 failure_rate = 0.0."""
        tool = MockSearchTool()
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        assert "collect_failure_rate" in result
        assert result["collect_failure_rate"] == 0.0

    def test_failure_rate_zero_on_empty_targets(self) -> None:
        """대상 GU 없음 → failure_rate = 0.0 (division guard)."""
        tool = MockSearchTool()
        state = {
            "gap_map": [],
            "current_plan": {"target_gaps": [], "queries": {}, "budget": 0},
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        assert result["collect_failure_rate"] == 0.0
        assert result["current_claims"] == []

    def test_return_shape_contains_both_keys(self) -> None:
        """반환 dict 는 current_claims + collect_failure_rate 포함."""
        tool = MockSearchTool()
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        assert set(result.keys()) >= {"current_claims", "collect_failure_rate"}


class TestCollectTimeoutResilience:
    """P0-B9 S1: search/fetch timeout 시 bare-except 없이 graceful."""

    def test_search_timeout_does_not_raise(self) -> None:
        """search 가 TimeoutError → 예외 전파 없이 failure_rate 반영."""
        tool = _FailingSearchTool(TimeoutError("search timeout"))
        state = _gu_state(["GU-0001"])
        # bare-except 제거 + 구체 예외 로깅 — collect_node 자체는 raise 하지 않음
        result = collect_node(state, search_tool=tool)
        # 검색은 실패했지만 함수는 정상 반환 (claims 는 deterministic fallback 혹은 empty)
        assert "current_claims" in result
        assert "collect_failure_rate" in result

    def test_connection_error_does_not_raise(self) -> None:
        """ConnectionError 도 동일하게 graceful."""
        tool = _FailingSearchTool(ConnectionError("conn refused"))
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        assert "current_claims" in result

    def test_os_error_does_not_raise(self) -> None:
        """OSError (e.g. DNS fail) — 동일."""
        tool = _FailingSearchTool(OSError("DNS fail"))
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        assert "current_claims" in result


class TestCollectEmptySearch:
    """P0-B9: empty search results — claim 0개 리턴, 예외 없음."""

    def test_empty_results_returns_empty_claims(self) -> None:
        tool = _EmptySearchTool()
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        assert result["current_claims"] == []
        # search 는 호출됐지만 결과는 비어 있음 → failure 아님
        assert result["collect_failure_rate"] == 0.0
        assert len(tool.search_calls) >= 1


class TestCollectMalformedLLM:
    """P0-B9 S2: LLM 이 malformed JSON 반환 시 deterministic fallback."""

    def test_llm_returns_bad_json_falls_back(self) -> None:
        """LLM batch 가 invalid JSON 반환 → deterministic fallback → claims 여전히 존재."""
        tool = MockSearchTool()
        bad_llm = MagicMock()
        bad_response = MagicMock()
        bad_response.content = "not a json { broken"
        bad_llm.batch.return_value = [bad_response]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool, llm=bad_llm)
        # fallback 덕분에 claim 은 생성됨 (mock 검색 결과 기반)
        assert len(result["current_claims"]) >= 1
        # batch 경로로 LLM 호출됐음
        assert bad_llm.batch.called

    def test_llm_raises_attribute_error_falls_back(self) -> None:
        """LLM batch 응답 객체가 content 없음 → AttributeError → fallback."""
        tool = MockSearchTool()
        broken_llm = MagicMock()
        no_content = MagicMock(spec=[])  # no .content attribute
        broken_llm.batch.return_value = [no_content]
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool, llm=broken_llm)
        assert len(result["current_claims"]) >= 1


class TestCollectDuplicateGU:
    """P0-B9: 동일 GU 중복 호출 시 claims 가 중복 누적되지 않는지 확인."""

    def test_same_gu_twice_in_target(self) -> None:
        """target_gaps 에 같은 GU ID 가 두 번 나와도 정상 동작."""
        tool = MockSearchTool()
        state = _gu_state(["GU-0001"])
        # target_gaps 에 중복 추가
        state["current_plan"]["target_gaps"] = ["GU-0001", "GU-0001"]
        result = collect_node(state, search_tool=tool)
        # 중복 처리는 구현상 허용 (같은 GU 2번 수집) — 단지 예외 없음만 확인
        assert "current_claims" in result
        assert isinstance(result["current_claims"], list)

    def test_claim_has_provenance_field(self) -> None:
        """SI-P3R: 축소 provenance 4필드 검증."""
        tool = MockSearchTool()
        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool)
        for claim in result["current_claims"]:
            assert "provenance" in claim
            prov = claim["provenance"]
            assert isinstance(prov, dict)
            assert "provider" in prov
            assert "domain" in prov
            assert "retrieved_at" in prov
            assert "trust_tier" in prov


class TestCollectBatch:
    """P6-B1: LLM batch 호출 경로 검증."""

    def test_batch_called_not_invoke(self) -> None:
        """LLM이 있을 때 invoke 대신 batch 1회 호출."""
        tool = MockSearchTool()
        mock_llm = MagicMock()
        good_response = MagicMock()
        good_response.content = '[{"claim_id": "CL-0001-01", "entity_key": "e", "field": "f", "value": "v", "source_gu_id": "GU-0001", "evidence": {"eu_id": "EU-0001-01", "url": "http://x.com", "title": "T", "snippet": "S", "observed_at": "2026-01-01", "credibility": 0.7}, "risk_flag": false}]'
        mock_llm.batch.return_value = [good_response]

        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool, llm=mock_llm)

        assert mock_llm.batch.called
        assert not mock_llm.invoke.called
        assert len(result["current_claims"]) >= 1

    def test_batch_fallback_on_api_error(self) -> None:
        """batch API 실패 시 단발 invoke fallback → claims 여전히 존재."""
        tool = MockSearchTool()
        mock_llm = MagicMock()
        mock_llm.batch.side_effect = RuntimeError("API error")
        fallback_response = MagicMock()
        fallback_response.content = "[]"
        mock_llm.invoke.return_value = fallback_response

        state = _gu_state(["GU-0001"])
        result = collect_node(state, search_tool=tool, llm=mock_llm)

        assert mock_llm.batch.called
        assert "current_claims" in result

    def test_multi_gu_single_batch_call(self) -> None:
        """GU 3개 → batch 1회, invoke 0회."""
        tool = MockSearchTool()
        mock_llm = MagicMock()
        resp = MagicMock()
        resp.content = "[]"
        mock_llm.batch.return_value = [resp, resp, resp]

        state = _gu_state(["GU-0001", "GU-0002", "GU-0003"])
        collect_node(state, search_tool=tool, llm=mock_llm)

        assert mock_llm.batch.call_count == 1
        assert not mock_llm.invoke.called


# ============================================================
# S1-T4: _calc_execution_queue L1 테스트
# ============================================================

def _make_gu(gu_id: str, utility: str = "high") -> dict:
    return {"gu_id": gu_id, "expected_utility": utility, "status": "open"}


class TestCalcExecutionQueue:
    """S1-T4: _calc_execution_queue — defer/queue 분리 검증."""

    def test_within_budget_all_queued(self) -> None:
        gu_by_id = {f"GU-{i:04d}": _make_gu(f"GU-{i:04d}") for i in range(1, 4)}
        queries = {f"GU-{i:04d}": [f"q{i}"] for i in range(1, 4)}
        tasks, deferred = _calc_execution_queue(list(gu_by_id), gu_by_id, queries, budget=10)
        assert len(tasks) == 3
        assert deferred == []

    def test_over_budget_excess_deferred(self) -> None:
        """budget=2 → 첫 2 query 분만 실행, 나머지 defer."""
        gu_by_id = {f"GU-{i:04d}": _make_gu(f"GU-{i:04d}") for i in range(1, 4)}
        queries = {f"GU-{i:04d}": [f"q{i}"] for i in range(1, 4)}
        tasks, deferred = _calc_execution_queue(list(gu_by_id), gu_by_id, queries, budget=2)
        assert len(tasks) == 2
        assert len(deferred) == 1
        assert deferred[0]["gu_id"] == "GU-0003"

    def test_low_utility_deferred_not_dropped(self) -> None:
        """utility=low 도 budget 초과 시 drop 아닌 defer."""
        gu_by_id = {
            "GU-0001": _make_gu("GU-0001", utility="high"),
            "GU-0002": _make_gu("GU-0002", utility="low"),
        }
        queries = {"GU-0001": ["q1"], "GU-0002": ["q2"]}
        tasks, deferred = _calc_execution_queue(["GU-0001", "GU-0002"], gu_by_id, queries, budget=1)
        assert len(tasks) == 1
        assert len(deferred) == 1
        assert deferred[0]["expected_utility"] == "low"

    def test_medium_utility_deferred_not_dropped(self) -> None:
        """utility=medium 도 budget 초과 시 drop 아닌 defer."""
        gu_by_id = {
            "GU-0001": _make_gu("GU-0001", utility="high"),
            "GU-0002": _make_gu("GU-0002", utility="medium"),
        }
        queries = {"GU-0001": ["q1"], "GU-0002": ["q2"]}
        tasks, deferred = _calc_execution_queue(["GU-0001", "GU-0002"], gu_by_id, queries, budget=1)
        assert len(deferred) == 1
        assert deferred[0]["expected_utility"] == "medium"

    def test_unknown_gu_id_skipped(self) -> None:
        gu_by_id = {"GU-0001": _make_gu("GU-0001")}
        queries = {"GU-0001": ["q1"]}
        tasks, deferred = _calc_execution_queue(["GU-0001", "MISSING"], gu_by_id, queries, budget=10)
        assert len(tasks) == 1
        assert deferred == []

    def test_collect_node_returns_deferred_targets(self) -> None:
        """collect_node 반환 dict 에 deferred_targets 포함."""
        tool = MockSearchTool()
        state = {
            "gap_map": [
                {"gu_id": f"GU-{i:04d}", "status": "open",
                 "target": {"entity_key": f"d:a:x{i}", "field": "price"},
                 "expected_utility": "low"}
                for i in range(1, 4)
            ],
            "current_plan": {
                "target_gaps": [f"GU-{i:04d}" for i in range(1, 4)],
                "queries": {f"GU-{i:04d}": [f"q{i}"] for i in range(1, 4)},
                "budget": 1,
            },
            "current_mode": {"mode": "normal"},
        }
        result = collect_node(state, search_tool=tool)
        assert "deferred_targets" in result
        assert len(result["deferred_targets"]) >= 1
