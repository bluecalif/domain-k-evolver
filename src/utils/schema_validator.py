"""JSON Schema 검증 유틸리티 — KU/EU/GU/PU + 전체 State 검증.

schemas/ 디렉토리의 4종 JSON Schema (Draft 2020-12) 기반.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

_SCHEMA_FILES = {
    "ku": "knowledge-unit.json",
    "eu": "evidence-unit.json",
    "gu": "gap-unit.json",
    "pu": "patch-unit.json",
}


@lru_cache(maxsize=4)
def _load_schema(kind: str) -> dict:
    path = SCHEMA_DIR / _SCHEMA_FILES[kind]
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _get_validator(kind: str) -> Draft202012Validator:
    schema = _load_schema(kind)
    return Draft202012Validator(schema)


def validate_ku(ku: dict[str, Any]) -> list[ValidationError]:
    """KU dict를 knowledge-unit.json 스키마로 검증. 에러 목록 반환 (빈 리스트=유효)."""
    return list(_get_validator("ku").iter_errors(ku))


def validate_eu(eu: dict[str, Any]) -> list[ValidationError]:
    """EU dict를 evidence-unit.json 스키마로 검증."""
    return list(_get_validator("eu").iter_errors(eu))


def validate_gu(gu: dict[str, Any]) -> list[ValidationError]:
    """GU dict를 gap-unit.json 스키마로 검증."""
    return list(_get_validator("gu").iter_errors(gu))


def validate_pu(pu: dict[str, Any]) -> list[ValidationError]:
    """PU dict를 patch-unit.json 스키마로 검증."""
    return list(_get_validator("pu").iter_errors(pu))


def validate_skeleton_aliases(skeleton: dict[str, Any]) -> list[str]:
    """Skeleton aliases / is_a 필드 검증. 에러 메시지 목록 반환.

    Silver P1-A3: 필드가 없으면 통과 (backward compat).
    존재하면 포맷 검증:
    - aliases: {canonical_key: [alias1, ...]} — key/value 모두 str
    - is_a: {child_key: parent_key} — key/value 모두 str
    """
    errors: list[str] = []

    aliases = skeleton.get("aliases")
    if aliases is not None:
        if not isinstance(aliases, dict):
            errors.append("aliases 는 dict 이어야 합니다")
        else:
            for canonical, alias_list in aliases.items():
                if not isinstance(canonical, str):
                    errors.append(f"aliases key 는 str 이어야 합니다: {canonical!r}")
                if not isinstance(alias_list, list):
                    errors.append(f"aliases[{canonical!r}] 는 list 이어야 합니다")
                elif not all(isinstance(a, str) for a in alias_list):
                    errors.append(f"aliases[{canonical!r}] 의 모든 항목은 str 이어야 합니다")

    is_a = skeleton.get("is_a")
    if is_a is not None:
        if not isinstance(is_a, dict):
            errors.append("is_a 는 dict 이어야 합니다")
        else:
            for child, parent in is_a.items():
                if not isinstance(child, str):
                    errors.append(f"is_a key 는 str 이어야 합니다: {child!r}")
                if not isinstance(parent, str):
                    errors.append(f"is_a[{child!r}] 값은 str 이어야 합니다: {parent!r}")

    return errors


def validate_state(state: dict[str, Any]) -> list[ValidationError]:
    """전체 State의 KU/GU를 일괄 검증. 모든 에러를 합쳐서 반환."""
    errors: list[ValidationError] = []

    for ku in state.get("knowledge_units", []):
        for err in validate_ku(ku):
            err.message = f"[{ku.get('ku_id', '?')}] {err.message}"
            errors.append(err)

    for gu in state.get("gap_map", []):
        for err in validate_gu(gu):
            err.message = f"[{gu.get('gu_id', '?')}] {err.message}"
            errors.append(err)

    return errors
