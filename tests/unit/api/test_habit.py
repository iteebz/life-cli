from datetime import date, timedelta

from life.api import add_check, get_checks, get_pending_items
from life.api.habits import add_habit, is_habit
from life.api.tasks import add_task


def test_add_check_habit(tmp_life_dir):
    habit_id = add_habit("daily standup")
    assert is_habit(habit_id)
    add_check(habit_id)


def test_add_check_idempotent(tmp_life_dir):
    habit_id = add_habit("meditation")
    add_check(habit_id)
    add_check(habit_id)
    checks = get_checks(habit_id)
    assert len(checks) == 1
    pending_items = get_pending_items()
    assert any(item.id == habit_id for item in pending_items)


def test_is_habit(tmp_life_dir):
    item_id = add_habit("a habit")
    assert is_habit(item_id)


def test_is_not_habit(tmp_life_dir):
    item_id = add_task("a task")
    assert not is_habit(item_id)


def test_pending_habit_shows_up(tmp_life_dir):
    iid = add_habit("a habit")
    items = get_pending_items()
    assert len(items) == 1
    assert items[0].id == iid


def test_check_repeat_once_per_day(tmp_life_dir):
    iid = add_habit("a habit")
    add_check(iid)
    add_check(iid)
    checks = get_checks(iid)
    assert len(checks) == 1
    items = get_pending_items()
    assert len(items) == 1
    assert items[0].id == iid
    assert items[0].is_habit


def test_check_repeat_to_completion(tmp_life_dir):
    iid = add_habit("5x")
    for i in range(5):
        check_date = (date.today() - timedelta(days=5 - i)).isoformat()
        add_check(iid, check_date)
    assert len(get_pending_items()) == 1  # Should still be pending
    assert get_pending_items()[0].id == iid
