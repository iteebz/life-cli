from datetime import datetime

from life.api import add_item, get_focus_items
from life.api.models import Item, Weekly
from life.lib.render import render_dashboard, render_focus_items, render_today_completed
from life.ops.toggle import toggle_done


def test_render_today_completed_empty(tmp_life_dir):
    result = render_today_completed([])

    assert result == ""


def test_render_today_completed_shows_tasks(tmp_life_dir):
    item_id = add_item("completed task")
    toggle_done(str(item_id))

    # Manually construct an Item object for the test
    today_items = [
        Item(
            id=item_id,
            content="completed task",
            focus=False,
            due_date=None,
            created=datetime.now(),
            completed=datetime.now(),
            is_habit=False,
        )
    ]
    result = render_today_completed(today_items)

    assert "completed task" in result.lower()
    assert "✓" in result


def test_render_focus_items_empty(tmp_life_dir):
    result = render_focus_items([])

    assert "focus" in result.lower() or result == ""


def test_render_focus_items_shows_items(tmp_life_dir):
    add_item("focused item", focus=True)

    items = get_focus_items()
    result = render_focus_items(items)

    assert "item" in result.lower() or len(result) > 0


def test_render_dashboard_returns_string(tmp_life_dir):
    add_item("task 1")
    add_item("task 2")

    momentum = {
        "this_week": Weekly(
            tasks_completed=5,
            tasks_total=5,
            habits_completed=10,
            habits_total=10,
        ),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    result = render_dashboard([], (1, 2), momentum, "", [])

    assert isinstance(result, str)
    assert len(result) > 0
