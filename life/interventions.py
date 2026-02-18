from dataclasses import dataclass
from datetime import datetime

from .db import get_db


@dataclass(frozen=True)
class Intervention:
    id: int
    timestamp: datetime
    description: str
    result: str
    note: str | None


def add_intervention(description: str, result: str, note: str | None = None) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO interventions (description, result, note) VALUES (?, ?, ?)",
            (description, result, note),
        )
        return cursor.lastrowid or 0


def get_interventions(limit: int = 20) -> list[Intervention]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, description, result, note FROM interventions ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Intervention(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                description=row[2],
                result=row[3],
                note=row[4],
            )
            for row in rows
        ]


def get_stats() -> dict[str, int]:
    with get_db() as conn:
        rows = conn.execute("SELECT result, COUNT(*) FROM interventions GROUP BY result").fetchall()
        return {row[0]: row[1] for row in rows}
