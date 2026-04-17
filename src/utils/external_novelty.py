"""External Novelty — 누적 history 대비 신규성 측정 (Stage E / SI-P4).

internal `novelty.py` 가 cycle-to-cycle 자기수렴을 재는 반면, external_novelty 는
run 전체 누적 관찰 집합(history) 대비 현재 cycle 이 얼마나 새로운 관찰을 가져왔는지를 잰다.

Granularity (D-138): (entity_key, field) 튜플. claim_value 차이는 claim_hash 로 보조.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


def _observation_key(entity_key: str, field: str) -> str:
    return f"{entity_key}|{field}"


def extract_observation_keys(items: Iterable[dict]) -> set[str]:
    """claim/KU 목록에서 (entity_key, field) 키 셋 추출.

    entity_key 또는 field 가 비어있는 항목은 제외.
    """
    keys: set[str] = set()
    for item in items:
        ek = item.get("entity_key", "") or ""
        field = item.get("field", "") or ""
        if not ek or not field:
            continue
        keys.add(_observation_key(ek, field))
    return keys


def claim_value_hash(value: Any) -> str:
    """claim value 의 안정적 해시 (12자 hex).

    dict key 정렬을 통해 동일 내용이면 동일 해시를 보장.
    """
    if isinstance(value, str):
        payload = value
    else:
        payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def compute_delta_kus(prev_kus: list[dict], curr_kus: list[dict]) -> list[dict]:
    """이전 cycle KU 목록 대비 이번 cycle 에 신규 추가된 KU 반환.

    (entity_key, field) 기준으로 prev_kus 에 없던 항목만 반환.
    orchestrator 가 external_novelty 분모를 '이번 cycle 신규 KU 키' 로 제한하는 데 사용 (D-148).
    """
    prev_obs = extract_observation_keys(prev_kus)
    return [
        ku for ku in curr_kus
        if _observation_key(ku.get("entity_key", ""), ku.get("field", "")) not in prev_obs
    ]


def compute_external_novelty(
    new_items: list[dict],
    history: Iterable[str] | None,
) -> tuple[float, set[str]]:
    """현재 cycle 관찰이 누적 history 대비 얼마나 새로운지 측정.

    Args:
        new_items: 이번 cycle 의 claims 또는 KUs (entity_key/field 필드 필수).
        history: 이전 cycle 까지 관찰된 "entity_key|field" 키 목록/집합.

    Returns:
        (score, new_keys)
          score  — 0.0~1.0. (현재 cycle 키 중 history 에 없던 비율). 현재 cycle 에
                    유효 키가 없으면 0.0.
          new_keys — 이번 cycle 에서 처음 관찰된 키 집합. caller 는 이를 history 에
                     union 해서 다음 cycle 로 전달한다.
    """
    hist: set[str] = set(history) if history else set()
    curr = extract_observation_keys(new_items)

    if not curr:
        return 0.0, set()

    novel = curr - hist
    score = round(len(novel) / len(curr), 4)
    return score, novel
