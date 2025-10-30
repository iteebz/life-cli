import contextlib
import sqlite3
import uuid
from datetime import date, datetime

from .. import db
from ..lib import clock
from .models import Habit


def _row_to_habit(
    row: tuple, checks: list[date] | None = None, tags: list[str] | None = None
) -> Habit:
    """Convert a database row to a Habit instance."""
    habit_id, content, created_str = row
    created = datetime.fromisoformat(created_str)
    return Habit(
        id=habit_id,
        content=content,
        created=created,
        checks=checks or [],
        tags=tags or [],
    )


def _get_habit_checks(conn, habit_id: str) -> list[date]:
    """Get all check dates for a habit."""
    cursor = conn.execute(
        "SELECT check_date FROM checks WHERE habit_id = ? ORDER BY check_date",
        (habit_id,),
    )
    return [datetime.fromisoformat(row[0]).date() for row in cursor.fetchall()]


def _get_habit_tags(conn, habit_id: str) -> list[str]:
    """Get all tags for a habit."""
    cursor = conn.execute(
        "SELECT tag FROM tags WHERE habit_id = ? ORDER BY tag",
        (habit_id,),
    )
    return [row[0] for row in cursor.fetchall()]


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
            "SELECT id, content, created FROM habits WHERE id = ?",
            (habit_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        checks = _get_habit_checks(conn, habit_id)
        tags = _get_habit_tags(conn, habit_id)
        return _row_to_habit(row, checks, tags)


def get_all_habits() -> list[Habit]:
    """SELECT all habits with checks and tags."""
    with db.get_db() as conn:
        cursor = conn.execute("SELECT id, content, created FROM habits ORDER BY created DESC")
        habits = []
        for row in cursor.fetchall():
            habit_id = row[0]
            checks = _get_habit_checks(conn, habit_id)
            tags = _get_habit_tags(conn, habit_id)
            habits.append(_row_to_habit(row, checks, tags))
        return habits


def get_pending_habits() -> list[Habit]:
    """SELECT all uncompleted habits, ordered by created."""
    return get_all_habits()


def get_checked_habits_today() -> list[Habit]:
    """SELECT habits with checks WHERE check_date = today."""
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT h.id, h.content, h.created
            FROM habits h
            INNER JOIN checks c ON h.id = c.habit_id
            WHERE DATE(c.check_date) = DATE(?)
            ORDER BY h.created DESC
            """,
            (today_str,),
        )
        habits = []
        for row in cursor.fetchall():
            habit_id = row[0]
            checks = _get_habit_checks(conn, habit_id)
            tags = _get_habit_tags(conn, habit_id)
            habits.append(_row_to_habit(row, checks, tags))
        return habits


def update_habit(habit_id: str, content: str | None = None) -> Habit:
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


def get_habits() -> list[Habit]:
    """Alias for get_all_habits for backward compatibility."""
    return get_all_habits()


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


def get_streak(habit_id: str) -> int:
    """Count consecutive days checked (most recent backwards)."""
    if not habit_id:
        raise ValueError("habit_id cannot be empty")

    checks = get_checks(habit_id)

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


def toggle_check(habit_id: str) -> None:
    """Toggle check for today."""
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM checks WHERE habit_id = ? AND check_date = ?",
            (habit_id, today_str),
        )
        if cursor.fetchone():
            conn.execute(
                "DELETE FROM checks WHERE habit_id = ? AND check_date = ?",
                (habit_id, today_str),
            )
        else:
            with contextlib.suppress(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO checks (habit_id, check_date) VALUES (?, ?)",
                    (habit_id, today_str),
                )
