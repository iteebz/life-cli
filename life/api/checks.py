import contextlib
import sqlite3
from datetime import date, datetime

from .. import db
from ..lib import clock


def add_check(habit_id: str, check_date: str | None = None) -> None:
    """INSERT into checks. Use today if check_date is None. Idempotent (UNIQUE constraint)."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    check_date_str = check_date or clock.today().isoformat()

    with db.get_db() as conn:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO checks (habit_id, check_date) VALUES (?, ?)",
                (habit_id, check_date_str),
            )


def delete_check(habit_id: str, check_date: str | None = None) -> None:
    """DELETE from checks. Use today if check_date is None."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    check_date_str = check_date or clock.today().isoformat()

    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM checks WHERE habit_id = ? AND check_date = ?",
            (habit_id, check_date_str),
        )


def get_checks(habit_id: str) -> list[date]:
    """SELECT check_dates for habit, return as date objects (sorted DESC)."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT check_date FROM checks WHERE habit_id = ? ORDER BY check_date DESC",
            (habit_id,),
        )
        return [datetime.fromisoformat(row[0]).date() for row in cursor.fetchall()]


def count_checks_today() -> int:
    """COUNT habits checked today."""
    today_str = clock.today().isoformat()

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT habit_id) FROM checks WHERE DATE(check_date) = DATE(?)",
            (today_str,),
        )
        result = cursor.fetchone()
        return result[0] if result else 0


def count_checks_for_habit(habit_id: str) -> int:
    """COUNT total checks for a habit."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM checks WHERE habit_id = ?",
            (habit_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else 0


def get_streak(habit_id: str) -> int:
    """Count consecutive days checked (most recent backwards)."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT check_date FROM checks WHERE habit_id = ? ORDER BY check_date DESC",
            (habit_id,),
        )
        checks = [datetime.fromisoformat(row[0]).date() for row in cursor.fetchall()]

    if not checks:
        return 0

    streak = 1
    today = clock.today()

    for i in range(len(checks) - 1):
        current = checks[i]
        next_date = checks[i + 1]
        if (current - next_date).days == 1:
            streak += 1
        else:
            break

    if checks[0] != today:
        return 0

    return streak
