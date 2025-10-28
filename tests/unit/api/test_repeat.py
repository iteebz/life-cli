from datetime import date, timedelta

from life.api import add_check, add_item, get_checks, get_pending_items, is_repeating


def test_add_check_habit(tmp_life_dir):
    habit_id = add_item("daily standup", tags=["habit"])
    assert is_repeating(habit_id) is True
    add_check(habit_id)


def test_add_check_chore(tmp_life_dir):
    chore_id = add_item("vacuum", tags=["chore"])
    assert is_repeating(chore_id) is True
    add_check(chore_id)


def test_add_check_idempotent(tmp_life_dir):
    habit_id = add_item("meditation", tags=["habit"])
    add_check(habit_id)
    add_check(habit_id)
    checks = get_checks(habit_id)
    assert len(checks) == 1
    pending_items = get_pending_items()
    assert any(item.id == habit_id for item in pending_items)


def test_repeat_habit(tmp_life_dir):
    item_id = add_item("habit", tags=["habit"])
    assert is_repeating(item_id)


def test_repeat_chore(tmp_life_dir):
    item_id = add_item("chore", tags=["chore"])
    assert is_repeating(item_id)


def test_repeat_not_task(tmp_life_dir):
    item_id = add_item("task")
    assert not is_repeating(item_id)


def test_check_repeat(tmp_life_dir):
    iid = add_item("habit", tags=["habit"], is_repeat=True)
    add_check(iid)
    items = get_pending_items()
    assert len(items) == 1
    assert items[0].id == iid


def test_check_repeat_once_per_day(tmp_life_dir):
    iid = add_item("habit", tags=["habit"], is_repeat=True)
    add_check(iid)
    add_check(iid)
    checks = get_checks(iid)
    assert len(checks) == 1
    items = get_pending_items()
    assert len(items) == 1
    assert items[0].id == iid
    assert items[0].is_repeat


def test_check_repeat_to_completion(tmp_life_dir):
    iid = add_item("5x", tags=["habit"], is_repeat=True)
    for i in range(5):
        check_date = (date.today() - timedelta(days=5 - i)).isoformat()
        add_check(iid, check_date)
    assert len(get_pending_items()) == 1  # Should still be pending
    assert get_pending_items()[0].id == iid
