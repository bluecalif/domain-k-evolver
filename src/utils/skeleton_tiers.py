"""Tiered skeleton helpers — active vs candidate categories (D-139).

Active categories (`skeleton["categories"]`) drive all core loop semantics
(plan, collect, integrate, audit, remodel). Candidate categories
(`skeleton["candidate_categories"]`) are proposals from universe_probe that
MUST be approved via HITL-R before promotion to active.

Invariant: active loop readers continue to use `skeleton.get("categories", [])`
directly — they MUST NOT see candidates. These helpers are the only sanctioned
path for tier-aware access.
"""
from __future__ import annotations

from typing import Any, Optional

TIER_ACTIVE = "active"
TIER_CANDIDATE = "candidate"

_VALID_TYPES = {"NEW_CATEGORY", "NEW_AXIS"}
_VALID_STATUSES = {"pending_validation", "validated", "promoted", "rejected"}
_REQUIRED_FIELDS = ("slug", "name", "rationale", "type", "proposed_at_cycle")


def get_active_categories(skeleton: dict) -> list[dict]:
    return list(skeleton.get("categories", []))


def get_candidate_categories(skeleton: dict) -> list[dict]:
    return list(skeleton.get("candidate_categories", []))


def get_active_category_slugs(skeleton: dict) -> list[str]:
    return [c["slug"] for c in skeleton.get("categories", []) if "slug" in c]


def get_candidate_category_slugs(skeleton: dict) -> list[str]:
    return [c["slug"] for c in skeleton.get("candidate_categories", []) if "slug" in c]


def find_category(skeleton: dict, slug: str) -> Optional[tuple[str, dict]]:
    for entry in skeleton.get("categories", []):
        if entry.get("slug") == slug:
            return (TIER_ACTIVE, entry)
    for entry in skeleton.get("candidate_categories", []):
        if entry.get("slug") == slug:
            return (TIER_CANDIDATE, entry)
    return None


def _validate_candidate(entry: dict) -> None:
    missing = [f for f in _REQUIRED_FIELDS if f not in entry]
    if missing:
        raise ValueError(f"candidate entry missing fields: {missing}")
    if entry["type"] not in _VALID_TYPES:
        raise ValueError(f"invalid candidate type: {entry['type']!r}")
    status = entry.get("status", "pending_validation")
    if status not in _VALID_STATUSES:
        raise ValueError(f"invalid candidate status: {status!r}")
    if not isinstance(entry["proposed_at_cycle"], int) or entry["proposed_at_cycle"] < 0:
        raise ValueError("proposed_at_cycle must be non-negative int")


def add_candidate_category(skeleton: dict, entry: dict) -> dict:
    """Add a candidate proposal to skeleton. Returns normalized entry.

    Raises ValueError on schema violation or slug collision with active
    or existing candidate.
    """
    _validate_candidate(entry)
    slug = entry["slug"]

    if slug in get_active_category_slugs(skeleton):
        raise ValueError(f"slug {slug!r} already exists in active categories")
    if slug in get_candidate_category_slugs(skeleton):
        raise ValueError(f"slug {slug!r} already exists in candidate categories")

    normalized = dict(entry)
    normalized.setdefault("status", "pending_validation")
    normalized.setdefault("evidence", None)

    skeleton.setdefault("candidate_categories", []).append(normalized)
    return normalized


def promote_candidate(skeleton: dict, slug: str, description: Optional[str] = None) -> dict:
    """Move a candidate to active categories (HITL-R approved path, D-139).

    Returns the active entry. Raises ValueError if slug not found in candidates
    or already active.
    """
    if slug in get_active_category_slugs(skeleton):
        raise ValueError(f"slug {slug!r} already active")

    candidates = skeleton.get("candidate_categories", [])
    for i, entry in enumerate(candidates):
        if entry.get("slug") == slug:
            active_entry = {
                "slug": slug,
                "description": description or entry.get("name", slug),
            }
            skeleton.setdefault("categories", []).append(active_entry)
            entry["status"] = "promoted"
            candidates.pop(i)
            return active_entry

    raise ValueError(f"slug {slug!r} not found in candidate categories")


def reject_candidate(skeleton: dict, slug: str) -> dict:
    """Mark a candidate as rejected and remove it. Returns the removed entry."""
    candidates = skeleton.get("candidate_categories", [])
    for i, entry in enumerate(candidates):
        if entry.get("slug") == slug:
            entry["status"] = "rejected"
            return candidates.pop(i)
    raise ValueError(f"slug {slug!r} not found in candidate categories")
