from datetime import timedelta

from life import db
from life.api import add_habit, add_task, toggle_check, toggle_completed
from life.api.dashboard import (
    get_pending_items,
    get_today_breakdown,
    get_today_completed,
)


def test_pending_empty(tmp_life_dir):
    items = get_pending_items()
    assert items == []


def test_pending_returns_tasks(tmp_life_dir):
    add_task("task 1")
    add_task("task 2")
    items = get_pending_items()
    assert len(items) == 2


def test_pending_items_sort_focus_first(tmp_life_dir):
    add_task("unfocused soon", focus=False, due="2025-01-01")
    add_task("focused later", focus=True, due="2025-12-31")
    add_task("unfocused later", focus=False, due="2025-12-31")

    items = get_pending_items()
    assert items[0].focus is True
    assert items[0].content == "focused later"


def test_pending_items_exclude_completed(tmp_life_dir):
    task1_id = add_task("task 1")
    add_task("task 2")
    toggle_completed(task1_id)

    items = get_pending_items()
    assert len(items) == 1
    assert items[0].content == "task 2"


def test_completed_empty(tmp_life_dir, fixed_today):
    completed = get_today_completed()
    assert completed == []


def test_completed_tasks(tmp_life_dir, fixed_today):
    task1_id = add_task("task 1")
    add_task("task 2")
    toggle_completed(task1_id)

    completed = get_today_completed()
    assert len(completed) == 1
    assert completed[0].id == task1_id


def test_completed_habits(tmp_life_dir, fixed_today):
    habit_id = add_habit("morning routine")
    toggle_check(habit_id)

    completed = get_today_completed()
    assert len(completed) == 1
    assert completed[0].id == habit_id


def test_completed_mixed(tmp_life_dir, fixed_today):
    task_id = add_task("task")
    habit_id = add_habit("habit")
    toggle_completed(task_id)
    toggle_check(habit_id)

    completed = get_today_completed()
    assert len(completed) == 2


def test_breakdown_empty(tmp_life_dir, fixed_today):
    habits_today, tasks_today = get_today_breakdown()
    assert habits_today == 0
    assert tasks_today == 0


def test_breakdown_tasks(tmp_life_dir, fixed_today):
    task1_id = add_task("task 1")
    task2_id = add_task("task 2")
    toggle_completed(task1_id)
    toggle_completed(task2_id)

    habits_today, tasks_today = get_today_breakdown()
    assert habits_today == 0
    assert tasks_today == 2


def test_breakdown_habits(tmp_life_dir, fixed_today):
    habit1_id = add_habit("habit 1")
    habit2_id = add_habit("habit 2")
    toggle_check(habit1_id)
    toggle_check(habit2_id)

    habits_today, tasks_today = get_today_breakdown()
    assert habits_today == 2
    assert tasks_today == 0


def test_breakdown_mixed(tmp_life_dir, fixed_today):
    task_id = add_task("task")
    habit1_id = add_habit("habit 1")
    habit2_id = add_habit("habit 2")
    toggle_completed(task_id)
    toggle_check(habit1_id)
    toggle_check(habit2_id)

    habits_today, tasks_today = get_today_breakdown()
    assert habits_today == 2
    assert tasks_today == 1


def test_today_completed_exclude_yesterday(tmp_life_dir, fixed_today):
    from datetime import datetime, time

    task_id = add_task("task completed yesterday")

    with db.get_db() as conn:
        yesterday = fixed_today - timedelta(days=1)
        conn.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (datetime.combine(yesterday, time.min).isoformat(), task_id),
        )

    completed = get_today_completed()
    assert len(completed) == 0


def test_pending_items_all_returned(tmp_life_dir):
    add_task("task 1")
    add_task("task 2")
    add_task("task 3")

    items_asc = get_pending_items(asc=True)
    items_desc = get_pending_items(asc=False)

    assert len(items_asc) == 3
    assert len(items_desc) == 3
    assert len(items_asc) == len(items_desc)
