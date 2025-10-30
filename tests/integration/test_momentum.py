from datetime import date, datetime, timedelta

import pytest

import life.lib.clock as clock
from life.api import add_check, add_item
from life.api.momentum import weekly_momentum


def _midnight(day: date) -> datetime:
    return datetime.combine(day, datetime.min.time())


def _set_clock(patcher, today_value: date, now_value: datetime | None = None) -> None:
    patcher.setattr(clock, "today", lambda: today_value)
    patcher.setattr(
        clock,
        "now",
        lambda: now_value if now_value is not None else _midnight(today_value),
    )


@pytest.fixture
def setup_db_with_data(tmp_life_dir):
    # Ensure a clean slate for each test
    # tmp_life_dir fixture already calls db.init()
    pass


def test_weekly_momentum_no_data(setup_db_with_data):
    momentum = weekly_momentum()
    assert momentum["this_week"].tasks_completed == 0
    assert momentum["this_week"].tasks_total == 0
    assert momentum["this_week"].habits_completed == 0
    assert momentum["this_week"].habits_total == 0
    assert momentum["this_week"].chores_completed == 0
    assert momentum["this_week"].chores_total == 0

    assert momentum["last_week"].tasks_completed == 0
    assert momentum["last_week"].tasks_total == 0
    assert momentum["last_week"].habits_completed == 0
    assert momentum["last_week"].habits_total == 0
    assert momentum["last_week"].chores_completed == 0
    assert momentum["last_week"].chores_total == 0


def test_weekly_momentum_single_habit_today(setup_db_with_data, monkeypatch):
    fixed_today = date(2025, 10, 28)  # Tuesday
    _set_clock(monkeypatch, fixed_today)

    add_item("test habit", item_type="habit", tags=["habit"])
    item_id = add_item("test habit 2", item_type="habit", tags=["habit"])
    add_check(item_id, check_date=fixed_today.isoformat())

    momentum = weekly_momentum()

    assert momentum["this_week"].habits_completed == 1
    assert momentum["this_week"].habits_total == 2
    assert momentum["last_week"].habits_completed == 0
    assert momentum["last_week"].habits_total == 0


def test_weekly_momentum_single_habit_yesterday(setup_db_with_data, monkeypatch):
    fixed_today = date(2025, 10, 28)  # Tuesday
    _set_clock(monkeypatch, fixed_today)

    yesterday = fixed_today - timedelta(days=1)  # Monday

    item_id = add_item("test habit yesterday", item_type="habit", tags=["habit"])
    add_check(item_id, check_date=yesterday.isoformat())

    momentum = weekly_momentum()

    # Yesterday (Monday) is part of 'this_week' (which starts on Monday)
    assert momentum["this_week"].habits_completed == 1
    assert momentum["this_week"].habits_total == 1
    assert momentum["last_week"].habits_completed == 0
    assert momentum["last_week"].habits_total == 0


def test_weekly_momentum_habit_last_week(setup_db_with_data, monkeypatch):
    fixed_today = date(2025, 10, 28)  # Tuesday
    _set_clock(monkeypatch, fixed_today)

    last_week_day = fixed_today - timedelta(days=7)  # Tuesday last week

    with monkeypatch.context() as ctx:
        _set_clock(ctx, last_week_day)
        item_id = add_item("test habit last week", item_type="habit", tags=["habit"])
    add_check(item_id, check_date=last_week_day.isoformat())

    momentum = weekly_momentum()

    assert momentum["this_week"].habits_completed == 0
    assert momentum["this_week"].habits_total == 7
    assert momentum["last_week"].habits_completed == 1
    assert momentum["last_week"].habits_total == 1
