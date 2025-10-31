from .. import db
from ..lib import clock
from ..lib.converters import _row_to_task
from .habits import get_checks, get_habit
from models import Habit, Task
from .tags import hydrate_tags, load_tags_for_tasks
from .tasks import _task_sort_key


def _get_pending_tasks() -> list[Task]:
    """Internal: SELECT completed IS NULL, sorted by (focus DESC, due_date ASC, created ASC)."""
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE completed IS NULL"
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        result = hydrate_tags(tasks, tags_map)

    return sorted(result, key=_task_sort_key)


def _get_checked_today() -> list[Habit]:
    """Internal: SELECT habits with checks WHERE check_date = today."""
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
            get_checks(habit_id)
            habit = get_habit(habit_id)
            if habit:
                habits.append(habit)
        return habits


def _get_completed_today() -> list[Task]:
    """Internal: SELECT completed tasks from today."""
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT id, content, focus, due_date, created, completed FROM tasks WHERE date(completed) = ? AND completed IS NOT NULL",
            (today_str,),
        )
        tasks = [_row_to_task(row) for row in cursor.fetchall()]
        task_ids = [t.id for t in tasks]
        tags_map = load_tags_for_tasks(task_ids, conn=conn)
        return hydrate_tags(tasks, tags_map)


def get_pending_items(asc=True) -> list[Task | Habit]:
    """Get pending tasks for display."""
    tasks = _get_pending_tasks()
    return sorted(tasks, key=_task_sort_key, reverse=not asc)


def get_today_completed() -> list[Task | Habit]:
    """Get tasks and habits completed today."""
    completed_tasks = _get_completed_today()
    completed_habits = _get_checked_today()
    return completed_tasks + completed_habits


def get_today_breakdown():
    """Get count of tasks and habits completed today."""
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT habit_id) FROM checks WHERE DATE(check_date) = DATE(?)",
            (today_str,),
        )
        habits_today = cursor.fetchone()[0]

    tasks_today = len(_get_completed_today())
    return habits_today, tasks_today
