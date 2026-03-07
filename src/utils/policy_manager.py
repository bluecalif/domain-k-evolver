"""PolicyManager — Policy 버전 관리 + Patch 적용 + 롤백.

Phase 4 Task 4.4~4.5.
- apply_patches(): AuditReport의 PolicyPatch를 policies에 적용
- rollback(): 이전 버전으로 복원
- version/change_history 관리
- Safety: 한 Audit당 최대 3 필드 변경 (audit.py에서 이미 제한)
"""

from __future__ import annotations

import copy
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Safety 상수
MAX_PATCHES_PER_APPLY = 3


def _get_nested(d: dict, dotted_key: str) -> Any:
    """dotted key로 중첩 dict 값 조회. 없으면 KeyError."""
    keys = dotted_key.split(".")
    current = d
    for k in keys:
        current = current[k]
    return current


def _set_nested(d: dict, dotted_key: str, value: Any) -> None:
    """dotted key로 중첩 dict 값 설정. 중간 경로 없으면 생성."""
    keys = dotted_key.split(".")
    current = d
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value


def apply_patches(
    policies: dict,
    patches: list[dict],
    *,
    cycle: int = 0,
) -> tuple[dict, list[dict]]:
    """PolicyPatch 목록을 policies에 적용.

    Args:
        policies: 현재 policies dict (원본 변경하지 않음).
        patches: PolicyPatch dict 목록.
        cycle: 적용 시점 cycle 번호.

    Returns:
        (new_policies, applied_patches) — 새 policies dict와 실제 적용된 패치 목록.
    """
    if not patches:
        return policies, []

    new_policies = copy.deepcopy(policies)
    applied: list[dict] = []

    for patch in patches[:MAX_PATCHES_PER_APPLY]:
        target = patch.get("target_field", "")
        proposed = patch.get("proposed_value")

        if not target or proposed is None:
            logger.warning("잘못된 patch 무시: %s", patch)
            continue

        try:
            _set_nested(new_policies, target, proposed)
            applied.append(patch)
            logger.info(
                "Patch 적용: %s = %s (이전: %s)",
                target,
                proposed,
                patch.get("current_value"),
            )
        except Exception as e:
            logger.warning("Patch 적용 실패: %s — %s", target, e)

    if applied:
        # version 증가
        old_version = new_policies.get("version", 0)
        new_policies["version"] = old_version + 1

        # change_history 기록
        history = list(new_policies.get("change_history", []))
        history.append({
            "version": new_policies["version"],
            "cycle": cycle,
            "patches_applied": [p.get("patch_id", "") for p in applied],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        new_policies["change_history"] = history

    return new_policies, applied


def rollback(
    policies: dict,
    previous_policies: dict,
    *,
    cycle: int = 0,
    reason: str = "performance_degradation",
) -> dict:
    """이전 버전 policies로 롤백.

    version과 change_history는 보존하며 롤백 기록을 추가한다.

    Args:
        policies: 현재 policies (롤백 대상).
        previous_policies: 복원할 이전 policies.
        cycle: 롤백 시점 cycle 번호.
        reason: 롤백 사유.

    Returns:
        롤백된 policies dict.
    """
    restored = copy.deepcopy(previous_policies)

    # version은 현재 기준으로 증가 (되돌리지 않음)
    current_version = policies.get("version", 0)
    restored["version"] = current_version + 1

    # change_history는 현재 것을 계승 + 롤백 기록 추가
    history = list(policies.get("change_history", []))
    history.append({
        "version": restored["version"],
        "cycle": cycle,
        "patches_applied": ["ROLLBACK"],
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    restored["change_history"] = history

    logger.info(
        "Policy 롤백: v%d → v%d (reason: %s)",
        current_version,
        restored["version"],
        reason,
    )

    return restored


def should_rollback(
    current_metrics: dict,
    previous_metrics: dict,
    *,
    threshold: float = 0.05,
) -> bool:
    """Patch 적용 후 성능 악화 여부 판정.

    evidence_rate 또는 gap_resolution_rate가 threshold 이상 하락하면 롤백 권장.

    Args:
        current_metrics: patch 적용 후 cycle의 metrics.rates.
        previous_metrics: patch 적용 전 cycle의 metrics.rates.
        threshold: 하락 허용 임계치.

    Returns:
        True면 롤백 권장.
    """
    check_keys = ["evidence_rate", "gap_resolution_rate"]

    for key in check_keys:
        curr = current_metrics.get(key, 0.0)
        prev = previous_metrics.get(key, 0.0)
        if prev > 0 and (prev - curr) > threshold:
            logger.info(
                "롤백 권장: %s 하락 %.3f → %.3f (threshold=%.3f)",
                key,
                prev,
                curr,
                threshold,
            )
            return True

    return False


def compute_credibility_stats(
    knowledge_units: list[dict],
) -> dict[str, dict]:
    """KU의 source_type별 품질 통계 산출.

    Returns:
        {source_type: {"total": int, "disputed": int, "deprecated": int, "avg_confidence": float}}
    """
    stats: dict[str, dict] = {}

    for ku in knowledge_units:
        st = ku.get("source_type")
        if not st:
            continue

        if st not in stats:
            stats[st] = {
                "total": 0,
                "disputed": 0,
                "deprecated": 0,
                "conf_sum": 0.0,
            }

        stats[st]["total"] += 1
        status = ku.get("status", "active")
        if status == "disputed":
            stats[st]["disputed"] += 1
        elif status == "deprecated":
            stats[st]["deprecated"] += 1
        stats[st]["conf_sum"] += ku.get("confidence", 0.0)

    # avg_confidence 계산
    result: dict[str, dict] = {}
    for st, s in stats.items():
        total = s["total"]
        result[st] = {
            "total": total,
            "disputed": s["disputed"],
            "deprecated": s["deprecated"],
            "avg_confidence": round(s["conf_sum"] / total, 4) if total > 0 else 0.0,
        }

    return result


def learn_credibility(
    stats: dict[str, dict],
    current_priors: dict[str, float],
    *,
    adjustment_rate: float = 0.05,
    min_samples: int = 3,
) -> list[dict]:
    """Credibility 통계 기반 credibility_priors 조정 patch 생성.

    규칙:
    - disputed + deprecated 비율 > 30% → prior 하향 (adjustment_rate만큼)
    - disputed + deprecated 비율 < 10% & avg_confidence > 0.8 → prior 상향
    - min_samples 미만이면 무시
    - prior 범위: [0.1, 0.99]

    Args:
        stats: compute_credibility_stats() 결과.
        current_priors: 현재 credibility_priors dict.
        adjustment_rate: 조정 단위.
        min_samples: 통계 신뢰 최소 샘플 수.

    Returns:
        PolicyPatch dict 목록.
    """
    patches: list[dict] = []
    patch_counter = 1

    for source_type, s in stats.items():
        if source_type not in current_priors:
            continue
        if s["total"] < min_samples:
            continue

        current = current_priors[source_type]
        bad_ratio = (s["disputed"] + s["deprecated"]) / s["total"]

        if bad_ratio > 0.30:
            new_val = max(0.10, round(current - adjustment_rate, 2))
            if new_val != current:
                patches.append({
                    "patch_id": f"PP-CRED-{patch_counter:03d}",
                    "target_field": f"credibility_priors.{source_type}",
                    "current_value": current,
                    "proposed_value": new_val,
                    "reason": (
                        f"{source_type} bad_ratio={bad_ratio:.0%} "
                        f"(disputed={s['disputed']}, deprecated={s['deprecated']}, "
                        f"total={s['total']})"
                    ),
                })
                patch_counter += 1

        elif bad_ratio < 0.10 and s["avg_confidence"] > 0.80:
            new_val = min(0.99, round(current + adjustment_rate, 2))
            if new_val != current:
                patches.append({
                    "patch_id": f"PP-CRED-{patch_counter:03d}",
                    "target_field": f"credibility_priors.{source_type}",
                    "current_value": current,
                    "proposed_value": new_val,
                    "reason": (
                        f"{source_type} 고품질: bad_ratio={bad_ratio:.0%}, "
                        f"avg_confidence={s['avg_confidence']:.3f}"
                    ),
                })
                patch_counter += 1

    return patches
