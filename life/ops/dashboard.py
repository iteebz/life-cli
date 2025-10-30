from ..api import checks, items
from ..api.models import Item


def get_pending_items(asc=True) -> list[Item]:
    all_pending_items = items.get_pending_items()

    # Sorting logic: focused items first, then by due date, then by creation date.
    # Habits are not given special sorting treatment here, they are sorted like other tasks.
    return sorted(
        all_pending_items,
        key=lambda item: (
            not item.focus,  # Focused items first
            item.due_date is None,
            item.due_date,  # Undue items last, then by due date
            item.created,  # Then by created date
        ),
        reverse=not asc,
    )


def get_today_completed() -> list[Item]:
    completed_items = items.get_completed_tasks_today()
    completed_items.extend(checks.get_checked_habits_today())
    return completed_items


def get_today_breakdown():
    habits_today = checks.count_today()
    tasks_today = items.count_completed_tasks_today()
    chores_today = 0

    return habits_today, tasks_today, chores_today
