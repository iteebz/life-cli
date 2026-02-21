from dataclasses import dataclass
from datetime import datetime

from .db import get_db


@dataclass(frozen=True)
class Pattern:
    id: int
    body: str
    logged_at: datetime
    tag: str | None = None


def add_pattern(body: str, tag: str | None = None) -> int:
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO patterns (body, tag) VALUES (?, ?)", (body, tag))
        return cursor.lastrowid or 0


def delete_pattern(pattern_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
        return cursor.rowcount > 0


def get_patterns(limit: int = 20, tag: str | None = None) -> list[Pattern]:
    with get_db() as conn:
        if tag:
            rows = conn.execute(
                "SELECT id, body, logged_at, tag FROM patterns WHERE tag = ? ORDER BY logged_at DESC LIMIT ?",
                (tag, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, body, logged_at, tag FROM patterns ORDER BY logged_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            Pattern(id=row[0], body=row[1], logged_at=datetime.fromisoformat(row[2]), tag=row[3])
            for row in rows
        ]
