from dataclasses import dataclass
from datetime import datetime

from .db import get_db


@dataclass(frozen=True)
class StewardSession:
    id: int
    summary: str
    logged_at: datetime


def add_session(summary: str) -> int:
    with get_db() as conn:
        cursor = conn.execute("INSERT INTO steward_sessions (summary) VALUES (?)", (summary,))
        return cursor.lastrowid or 0


def get_sessions(limit: int = 10) -> list[StewardSession]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, summary, logged_at FROM steward_sessions ORDER BY logged_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            StewardSession(id=row[0], summary=row[1], logged_at=datetime.fromisoformat(row[2]))
            for row in rows
        ]
