from .. import db
from ..lib import clock
from .habits import get_checked_habits_today
from .models import Habit, Task
from .tasks import get_pending_tasks, get_today_completed_tasks


def get_pending_items(asc=True) -> list[Task | Habit]:
    tasks = get_pending_tasks()
    return sorted(
        tasks,
        key=lambda task: (
            not task.focus,
            task.due_date is None,
            task.due_date,
            task.created,
        ),
        reverse=not asc,
    )


def get_today_completed() -> list[Task | Habit]:
    completed_tasks = get_today_completed_tasks()
    completed_habits = get_checked_habits_today()
    return completed_tasks + completed_habits


def get_today_breakdown():
    today_str = clock.today().isoformat()
    with db.get_db() as conn:
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT habit_id) FROM checks WHERE DATE(check_date) = DATE(?)",
            (today_str,),
        )
        habits_today = cursor.fetchone()[0]

    tasks_today = len(get_today_completed_tasks())
    return habits_today, tasks_today
