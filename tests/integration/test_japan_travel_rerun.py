"""Silver P1-C3: japan-travel 재통합 — alias resolver 적용 후 중복 KU 감소 검증.

P0 baseline state 의 KU 를 가져와 alias entity_key 로 claim 을 재생성하고,
integrate_node 를 통과시켜 중복 KU 가 생성되지 않음을 확인한다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.nodes.integrate import integrate_node
from tests.conftest import make_minimal_state

P0_BASELINE = Path("bench/silver/japan-travel/p0-20260412-baseline/state")

# Silver P1 skeleton (aliases/is_a 포함)
SKELETON_P1 = None  # lazy load


def _load_skeleton() -> dict:
    global SKELETON_P1
    if SKELETON_P1 is None:
        with open(P0_BASELINE / "domain-skeleton.json", encoding="utf-8") as f:
            SKELETON_P1 = json.load(f)
    return SKELETON_P1


def _load_kus() -> list[dict]:
    with open(P0_BASELINE / "knowledge-units.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def baseline_kus() -> list[dict]:
    return _load_kus()


@pytest.fixture
def skeleton() -> dict:
    return _load_skeleton()


class TestAliasDeduplication:
    """alias claim 이 기존 canonical KU 와 merge 되어 중복 KU 미생성."""

    def test_jr_pass_alias_no_duplicate(self, baseline_kus, skeleton):
        """jr-pass 의 alias (재팬레일패스) 로 claim → 기존 KU update, 신규 미생성."""
        # jr-pass 관련 기존 KU 찾기
        jr_kus = [ku for ku in baseline_kus if "jr-pass" in ku.get("entity_key", "")]
        if not jr_kus:
            pytest.skip("baseline 에 jr-pass KU 없음")

        target_ku = jr_kus[0]
        original_count = len(baseline_kus)

        # alias entity_key 로 claim 생성
        claims = [
            {
                "claim_id": "CL-ALIAS-TEST",
                "entity_key": "재팬레일패스",  # alias
                "field": target_ku["field"],
                "value": target_ku["value"],
                "source_gu_id": "",
                "evidence": {"eu_id": "EU-ALIAS-001", "credibility": 0.85},
            },
        ]

        state = make_minimal_state(
            knowledge_units=list(baseline_kus),
            current_claims=claims,
            domain_skeleton=skeleton,
            current_mode={"mode": "normal"},
        )

        result = integrate_node(state)
        result_kus = result["knowledge_units"]

        # 중복 KU 미생성 확인 (동일 수 유지)
        assert len(result_kus) == original_count

    def test_bullet_train_alias_no_duplicate(self, baseline_kus, skeleton):
        """shinkansen alias (bullet-train) → 기존 KU update."""
        shin_kus = [ku for ku in baseline_kus if "shinkansen" in ku.get("entity_key", "")]
        if not shin_kus:
            pytest.skip("baseline 에 shinkansen KU 없음")

        target_ku = shin_kus[0]
        original_count = len(baseline_kus)

        claims = [
            {
                "claim_id": "CL-BULLET-TEST",
                "entity_key": "bullet-train",
                "field": target_ku["field"],
                "value": target_ku["value"],
                "source_gu_id": "",
                "evidence": {"eu_id": "EU-BULLET-001", "credibility": 0.8},
            },
        ]

        state = make_minimal_state(
            knowledge_units=list(baseline_kus),
            current_claims=claims,
            domain_skeleton=skeleton,
            current_mode={"mode": "normal"},
        )

        result = integrate_node(state)
        assert len(result["knowledge_units"]) == original_count

    def test_multiple_alias_claims_reduce_duplicates(self, baseline_kus, skeleton):
        """여러 alias claim 동시 투입 → 중복 KU 생성률 측정.

        alias 가 없을 때는 각각 신규 KU 가 되지만,
        resolver 적용 후에는 기존 KU 와 merge 된다.
        """
        jr_kus = [ku for ku in baseline_kus if "jr-pass" in ku.get("entity_key", "")]
        if not jr_kus:
            pytest.skip("baseline 에 jr-pass KU 없음")

        # alias 3종으로 claim 생성 (모두 같은 canonical)
        alias_keys = ["japan-rail-pass", "재팬레일패스", "japan-travel:pass-ticket:japan-rail-pass"]
        claims = []
        for i, alias_key in enumerate(alias_keys):
            for jr_ku in jr_kus[:1]:
                claims.append({
                    "claim_id": f"CL-MULTI-{i}",
                    "entity_key": alias_key,
                    "field": jr_ku["field"],
                    "value": jr_ku["value"],
                    "source_gu_id": "",
                    "evidence": {"eu_id": f"EU-MULTI-{i}", "credibility": 0.8},
                })

        original_count = len(baseline_kus)

        state = make_minimal_state(
            knowledge_units=list(baseline_kus),
            current_claims=claims,
            domain_skeleton=skeleton,
            current_mode={"mode": "normal"},
        )

        result = integrate_node(state)
        result_kus = result["knowledge_units"]

        # alias 없이는 3개 신규 KU 추가됐을 것.
        # resolver 적용 후: 0개 추가 (모두 기존 KU update)
        assert len(result_kus) == original_count
        # 최소 15% 감소 효과 (3개 중복 방지 / 기존 127개 기준 ≈ 2.4%)
        # 실제 gate 기준은 full rerun 이므로 여기서는 "중복 방지됨" 을 확인
        prevented_duplicates = (original_count + len(claims)) - len(result_kus)
        assert prevented_duplicates >= len(claims)  # 모든 alias claim 이 merge 됨
