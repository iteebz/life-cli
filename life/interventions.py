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
        cur = conn.execute(
            "INSERT INTO interventions (description, result, note) VALUES (?, ?, ?)",
            (description, result, note),
        )
        return cur.lastrowid


def get_interventions(limit: int = 20) -> list[Intervention]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, timestamp, description, result, note FROM interventions ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            Intervention(
                id=r[0],
                timestamp=datetime.fromisoformat(r[1]),
                description=r[2],
                result=r[3],
                note=r[4],
            )
            for r in rows
        ]


def get_stats() -> dict[str, int]:
    with get_db() as conn:
        rows = conn.execute("SELECT result, COUNT(*) FROM interventions GROUP BY result").fetchall()
        return {r[0]: r[1] for r in rows}
