"""Snooze management — defer items to resurface later."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any

from . import db


def parse_until(until: str) -> datetime:
    now = datetime.now()
    until_lower = until.lower().strip()

    if until_lower in ("tomorrow", "tmrw"):
        return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)

    if until_lower in ("monday", "mon"):
        days_ahead = (7 - now.weekday()) % 7 or 7
        return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)

    if until_lower in ("next week", "nextweek"):
        days_ahead = (7 - now.weekday()) % 7 or 7
        return (now + timedelta(days=days_ahead)).replace(hour=9, minute=0, second=0, microsecond=0)

    if until_lower.endswith(("h", "hr", "hour")):
        hours = int("".join(c for c in until_lower if c.isdigit()) or "1")
        return now + timedelta(hours=hours)

    if until_lower.endswith(("d", "day")):
        days = int("".join(c for c in until_lower if c.isdigit()) or "1")
        return (now + timedelta(days=days)).replace(hour=9, minute=0, second=0, microsecond=0)

    if until_lower == "evening":
        return now.replace(hour=18, minute=0, second=0, microsecond=0)

    if until_lower == "morning":
        target = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    if until_lower == "weekend":
        days_ahead = (5 - now.weekday()) % 7 or 7
        return (now + timedelta(days=days_ahead)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )

    try:
        return datetime.fromisoformat(until)
    except ValueError:
        pass

    return now + timedelta(days=1)


def snooze_item(
    entity_type: str,
    entity_id: str,
    until: str,
    source_id: str | None = None,
    reason: str | None = None,
) -> tuple[str, datetime]:
    snooze_until = parse_until(until)
    snooze_id = uuid.uuid4().hex[:16]

    with db.get_db() as conn:
        conn.execute(
            """INSERT INTO snoozed_items (id, entity_type, entity_id, source_id, snooze_until, reason)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (snooze_id, entity_type, entity_id, source_id, snooze_until.isoformat(), reason),
        )

    return snooze_id, snooze_until


def get_due_snoozes() -> list[dict[str, Any]]:
    now = datetime.now().isoformat()

    with db.get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM snoozed_items
            WHERE snooze_until <= ? AND resurfaced_at IS NULL
            ORDER BY snooze_until ASC""",
            (now,),
        ).fetchall()

    return [dict(row) for row in rows]


def mark_resurfaced(snooze_id: str) -> bool:
    now = datetime.now().isoformat()

    with db.get_db() as conn:
        result = conn.execute(
            "UPDATE snoozed_items SET resurfaced_at = ? WHERE id = ?",
            (now, snooze_id),
        )
        return result.rowcount > 0


def get_snoozed_items() -> list[dict[str, Any]]:
    now = datetime.now().isoformat()

    with db.get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM snoozed_items
            WHERE resurfaced_at IS NULL AND snooze_until > ?
            ORDER BY snooze_until ASC""",
            (now,),
        ).fetchall()

    return [dict(row) for row in rows]


def unsnooze(snooze_id: str) -> bool:
    with db.get_db() as conn:
        result = conn.execute(
            "DELETE FROM snoozed_items WHERE id = ?",
            (snooze_id,),
        )
        return result.rowcount > 0


def is_snoozed(entity_type: str, entity_id: str) -> bool:
    now = datetime.now().isoformat()

    with db.get_db() as conn:
        row = conn.execute(
            """SELECT id FROM snoozed_items
            WHERE entity_type = ? AND entity_id = ?
            AND snooze_until > ? AND resurfaced_at IS NULL""",
            (entity_type, entity_id, now),
        ).fetchone()

    return row is not None
