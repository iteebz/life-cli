import json
from typing import Any

from .db import get_db, now_iso


def log(
    action: str,
    entity_type: str,
    entity_id: str,
    metadata: dict[str, Any] | None = None,
    proposed_action: str | None = None,
    user_decision: str | None = None,
    reasoning: str | None = None,
) -> None:
    metadata_json = json.dumps(metadata) if metadata else None

    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO audit_log (action, entity_type, entity_id, metadata, timestamp, proposed_action, user_decision, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                action,
                entity_type,
                entity_id,
                metadata_json,
                now_iso(),
                proposed_action,
                user_decision,
                reasoning,
            ),
        )


def get_recent_logs(limit: int = 50) -> list[dict[str, Any]]:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT action, entity_type, entity_id, metadata, timestamp, proposed_action, user_decision, reasoning
            FROM audit_log
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        return [dict(row) for row in rows]


def log_decision(
    proposed_action: str,
    entity_type: str,
    entity_id: str,
    user_decision: str,
    reasoning: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    log(
        action="decision",
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata,
        proposed_action=proposed_action,
        user_decision=user_decision,
        reasoning=reasoning,
    )
