import json
from dataclasses import dataclass
from typing import Any

from . import config
from .db import get_db


@dataclass
class ActionStats:
    action: str
    total: int
    approved: int
    rejected: int
    corrected: int
    accuracy: float
    corrections: list[tuple[str, str]]


def get_decision_stats() -> dict[str, ActionStats]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT proposed_action, user_decision, metadata
            FROM audit_log
            WHERE action = 'decision' AND proposed_action IS NOT NULL
            """
        ).fetchall()

    stats: dict[str, dict[str, Any]] = {}
    for row in rows:
        action = row["proposed_action"]
        decision = row["user_decision"]
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}

        if action not in stats:
            stats[action] = {
                "total": 0,
                "approved": 0,
                "rejected": 0,
                "corrected": 0,
                "corrections": [],
            }

        stats[action]["total"] += 1
        if decision == "approved":
            stats[action]["approved"] += 1
        elif decision == "rejected":
            stats[action]["rejected"] += 1
        elif decision == "rejected_with_correction":
            stats[action]["corrected"] += 1
            if metadata.get("correction"):
                stats[action]["corrections"].append((action, metadata["correction"]))

    result = {}
    for action, s in stats.items():
        total = s["total"]
        accuracy = s["approved"] / total if total > 0 else 0.0
        result[action] = ActionStats(
            action=action,
            total=total,
            approved=s["approved"],
            rejected=s["rejected"],
            corrected=s["corrected"],
            accuracy=accuracy,
            corrections=s["corrections"],
        )

    return result


def get_correction_patterns() -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT proposed_action, metadata
            FROM audit_log
            WHERE action = 'decision' AND user_decision = 'rejected_with_correction'
            """
        ).fetchall()

    patterns: dict[tuple[str, str], int] = {}
    for row in rows:
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        if metadata.get("correction"):
            key = (row["proposed_action"], metadata["correction"])
            patterns[key] = patterns.get(key, 0) + 1

    result = []
    for (original, corrected), count in sorted(patterns.items(), key=lambda x: -x[1]):
        result.append({"original": original, "corrected": corrected, "count": count})
    return result


def suggest_auto_approve(threshold: float = 0.95, min_samples: int = 10) -> list[str]:
    stats = get_decision_stats()
    suggestions = []
    for action, s in stats.items():
        if s.total >= min_samples and s.accuracy >= threshold:
            suggestions.append(action)
    return suggestions


def should_auto_approve(action: str) -> bool:
    policy = config.get_policy()
    auto: dict[str, Any] = policy.get("auto_approve", {})

    if not auto.get("enabled", False):
        return False

    allowed_actions = auto.get("actions", [])
    if allowed_actions and action not in allowed_actions:
        return False

    threshold = auto.get("threshold", 0.95)
    min_samples = auto.get("min_samples", 10)

    stats = get_decision_stats()
    if action not in stats:
        return False

    s = stats[action]
    return s.total >= min_samples and s.accuracy >= threshold
