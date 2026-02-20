from dataclasses import dataclass
from datetime import datetime

from .db import get_db


@dataclass(frozen=True)
class Pattern:
    id: int
    body: str
    logged_at: datetime


def add_pattern(body: str) -> int:
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO patterns (body) VALUES (?)", (body,))
        return cursor.lastrowid or 0


def delete_pattern(pattern_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
        return cursor.rowcount > 0


def get_patterns(limit: int = 20) -> list[Pattern]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, body, logged_at FROM patterns ORDER BY logged_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Pattern(id=row[0], body=row[1], logged_at=datetime.fromisoformat(row[2]))
            for row in rows
        ]
