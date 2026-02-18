import contextlib
import dataclasses
import sqlite3
import uuid
from datetime import date, datetime

from . import db
from .lib import clock
from .lib.converters import row_to_habit
from .lib.fuzzy import find_in_pool, find_in_pool_exact
from .models import Habit
from .tags import get_tags_for_habit, load_tags_for_habits

__all__ = [
    "add_habit",
    "archive_habit",
    "check_habit",
    "delete_habit",
    "find_habit",
    "get_archived_habits",
    "get_checks",
    "get_habit",
    "get_habits",
    "get_streak",
    "toggle_check",
    "uncheck_habit",
    "update_habit",
]


def _hydrate_habit(habit: Habit, checks: list[date], tags: list[str]) -> Habit:
    """Attach checks and tags to a habit."""
    return dataclasses.replace(habit, checks=checks, tags=tags)


def _get_habit_checks(conn, habit_id: str) -> list[datetime]:
    cursor = conn.execute(
        "SELECT completed_at FROM checks WHERE habit_id = ? ORDER BY completed_at",
        (habit_id,),
    )
    return [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]


def add_habit(content: str, tags: list[str] | None = None) -> str:
    """Insert a habit and optionally add tags. Returns habit_id."""
    habit_id = str(uuid.uuid4())
    with db.get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO habits (id, content) VALUES (?, ?)",
                (habit_id, content),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to add habit: {e}") from e

        if tags:
            for tag in tags:
                with contextlib.suppress(sqlite3.IntegrityError):
                    conn.execute(
                        "INSERT INTO tags (habit_id, tag) VALUES (?, ?)",
                        (habit_id, tag.lower()),
                    )
    return habit_id


def get_habit(habit_id: str) -> Habit | None:
    """SELECT from habits + LEFT JOIN checks + LEFT JOIN tags."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, created, archived_at FROM habits WHERE id = ?",
            (habit_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        habit = row_to_habit(row)
        checks = _get_habit_checks(conn, habit_id)
        tags = get_tags_for_habit(habit_id)
        return _hydrate_habit(habit, checks, tags)


def update_habit(habit_id: str, content: str | None = None) -> Habit | None:
    """UPDATE content only (habits have no other mutable fields), return updated Habit."""
    if content is None:
        return get_habit(habit_id)

    with db.get_db() as conn:
        try:
            conn.execute(
                "UPDATE habits SET content = ? WHERE id = ?",
                (content, habit_id),
            )
        except sqlite3.IntegrityError as e:
            raise ValueError(f"Failed to update habit: {e}") from e

    return get_habit(habit_id)


def delete_habit(habit_id: str) -> None:
    """DELETE from habits."""
    with db.get_db() as conn:
        conn.execute("DELETE FROM habits WHERE id = ?", (habit_id,))


def get_habits(habit_ids: list[str] | None = None) -> list[Habit]:
    """Get active (non-archived) habits by IDs, or all active habits if IDs is None."""
    if habit_ids is None:
        with db.get_db() as conn:
            cursor = conn.execute(
                "SELECT id, content, created, archived_at FROM habits WHERE archived_at IS NULL ORDER BY created DESC"
            )
            rows = cursor.fetchall()
            all_habit_ids = [row[0] for row in rows]
            tags_map = load_tags_for_habits(all_habit_ids, conn=conn)
            habits = []
            for row in rows:
                habit_id = row[0]
                checks = _get_habit_checks(conn, habit_id)
                tags = tags_map.get(habit_id, [])
                habit = row_to_habit(row)
                habits.append(_hydrate_habit(habit, checks, tags))
            return habits

    result = []
    for habit_id in habit_ids:
        habit = get_habit(habit_id)
        if habit:
            result.append(habit)
    return result


def get_checks(habit_id: str) -> list[datetime]:
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT completed_at FROM checks WHERE habit_id = ? ORDER BY completed_at DESC",
            (habit_id,),
        )
        return [datetime.fromisoformat(row[0]) for row in cursor.fetchall()]


def get_streak(habit_id: str) -> int:
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    checks = get_checks(habit_id)

    if not checks:
        return 0

    streak = 1
    today = clock.today()

    for i in range(len(checks) - 1):
        current = checks[i].date()
        next_date = checks[i + 1].date()
        if (current - next_date).days == 1:
            streak += 1
        else:
            break

    if checks[0].date() != today:
        return 0

    return streak


def get_archived_habits() -> list[Habit]:
    """Get archived habits."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, created, archived_at FROM habits WHERE archived_at IS NOT NULL ORDER BY archived_at DESC"
        )
        rows = cursor.fetchall()
        all_habit_ids = [row[0] for row in rows]
        tags_map = load_tags_for_habits(all_habit_ids, conn=conn)
        habits = []
        for row in rows:
            habit_id = row[0]
            checks = _get_habit_checks(conn, habit_id)
            tags = tags_map.get(habit_id, [])
            habit = row_to_habit(row)
            habits.append(_hydrate_habit(habit, checks, tags))
        return habits


def archive_habit(habit_id: str) -> Habit | None:
    """Set archived_at to now. Returns updated Habit or None if not found."""
    habit = get_habit(habit_id)
    if not habit:
        return None
    archived_at = datetime.now().isoformat()
    with db.get_db() as conn:
        conn.execute(
            "UPDATE habits SET archived_at = ? WHERE id = ?",
            (archived_at, habit_id),
        )
    return get_habit(habit_id)


def find_habit(ref: str) -> Habit | None:
    return find_in_pool(ref, get_habits())


def find_habit_exact(ref: str) -> Habit | None:
    return find_in_pool_exact(ref, get_habits())


def check_habit(habit_id: str) -> Habit | None:
    habit = get_habit(habit_id)
    if not habit:
        return None
    now = datetime.now().isoformat()
    with db.get_db() as conn:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO checks (habit_id, check_date, completed_at) VALUES (?, ?, ?)",
                (habit_id, clock.today().isoformat(), now),
            )
    return get_habit(habit_id)


def uncheck_habit(habit_id: str) -> Habit | None:
    habit = get_habit(habit_id)
    if not habit:
        return None
    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM checks WHERE habit_id = ? AND check_date = ?",
            (habit_id, clock.today().isoformat()),
        )
    return get_habit(habit_id)


def toggle_check(habit_id: str) -> Habit | None:
    habit = get_habit(habit_id)
    if not habit:
        return None
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM checks WHERE habit_id = ? AND check_date = ?",
            (habit_id, clock.today().isoformat()),
        )
        if cursor.fetchone():
            return uncheck_habit(habit_id)
    return check_habit(habit_id)
