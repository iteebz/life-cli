from ..api.checks import count_checks_today
from ..api.habits import get_checked_habits_today
from ..api.models import Habit, Task
from ..api.tasks import get_pending_tasks, get_today_completed_tasks


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
    habits_today = count_checks_today()
    tasks_today = len(get_today_completed_tasks())
    return habits_today, tasks_today
