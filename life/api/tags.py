import contextlib
import sqlite3

from .. import db
from ..lib.converters import _hydrate_tags, _row_to_habit, _row_to_task
from .models import Habit, Task


def add_tag(task_id: str | None, habit_id: str | None, tag: str, conn=None) -> None:
    if (task_id is None and habit_id is None) or (task_id is not None and habit_id is not None):
        raise ValueError("Exactly one of (task_id, habit_id) must be not None")

    if conn is None:
        with db.get_db() as conn:
            with contextlib.suppress(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?)",
                    (task_id, habit_id, tag.lower()),
                )
    else:
        with contextlib.suppress(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO tags (task_id, habit_id, tag) VALUES (?, ?, ?)",
                (task_id, habit_id, tag.lower()),
            )


def get_tags_for_task(task_id: str) -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task_id,))
        return [row[0] for row in cursor.fetchall()]


def get_tags_for_habit(habit_id: str) -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT tag FROM tags WHERE habit_id = ?", (habit_id,))
        return [row[0] for row in cursor.fetchall()]


def get_tasks_by_tag(tag: str) -> list[Task]:
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT t.id, t.content, t.focus, t.due_date, t.created, t.completed
            FROM tasks t
            INNER JOIN tags tg ON t.id = tg.task_id
            WHERE tg.tag = ?
            """,
            (tag.lower(),),
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]

        result = []
        for task in tasks:
            cursor = conn.execute("SELECT tag FROM tags WHERE task_id = ?", (task.id,))
            task_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(task, task_tags))

        return result


def get_habits_by_tag(tag: str) -> list[Habit]:
    with db.get_db() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT h.id, h.content, h.created
            FROM habits h
            INNER JOIN tags tg ON h.id = tg.habit_id
            WHERE tg.tag = ?
            """,
            (tag.lower(),),
        )
        habits = [_row_to_habit(row) for row in cursor.fetchall()]

        result = []
        for habit in habits:
            cursor = conn.execute("SELECT tag FROM tags WHERE habit_id = ?", (habit.id,))
            habit_tags = [tag_row[0] for tag_row in cursor.fetchall()]
            result.append(_hydrate_tags(habit, habit_tags))

        return result


def remove_tag(task_id: str | None, habit_id: str | None, tag: str) -> None:
    if (task_id is None and habit_id is None) or (task_id is not None and habit_id is not None):
        raise ValueError("Exactly one of (task_id, habit_id) must be not None")

    with db.get_db() as conn:
        conn.execute(
            "DELETE FROM tags WHERE (task_id = ? OR habit_id = ?) AND tag = ?",
            (task_id, habit_id, tag.lower()),
        )


def list_all_tags() -> list[str]:
    with db.get_db() as conn:
        cursor = conn.execute("SELECT DISTINCT tag FROM tags ORDER BY tag ASC")
        return [row[0] for row in cursor.fetchall()]
