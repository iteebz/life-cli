from dataclasses import dataclass
from datetime import datetime, timedelta

from .db import get_db


@dataclass(frozen=True)
class MoodEntry:
    id: int
    score: int
    label: str | None
    logged_at: datetime


def add_mood(score: int, label: str | None = None) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO mood_log (score, label) VALUES (?, ?)",
            (score, label),
        )
        return cursor.lastrowid or 0


def get_recent_moods(hours: int = 24) -> list[MoodEntry]:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, score, label, logged_at FROM mood_log WHERE logged_at > ? ORDER BY logged_at DESC",
            (cutoff.isoformat(),),
        ).fetchall()
    return [
        MoodEntry(id=row[0], score=row[1], label=row[2], logged_at=datetime.fromisoformat(row[3]))
        for row in rows
    ]


def get_latest_mood() -> MoodEntry | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, score, label, logged_at FROM mood_log ORDER BY logged_at DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    return MoodEntry(id=row[0], score=row[1], label=row[2], logged_at=datetime.fromisoformat(row[3]))


def delete_latest_mood(within_seconds: int = 3600) -> MoodEntry | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, score, label, logged_at FROM mood_log ORDER BY logged_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        entry = MoodEntry(id=row[0], score=row[1], label=row[2], logged_at=datetime.fromisoformat(row[3]))
        age = (datetime.utcnow() - entry.logged_at).total_seconds()
        if age > within_seconds:
            raise ValueError(f"latest entry is {int(age // 60)}m old — too old to remove")
        conn.execute("DELETE FROM mood_log WHERE id = ?", (row[0],))
    return entry
