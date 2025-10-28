from datetime import datetime
from unittest.mock import patch

from life.api.models import Item, Weekly
from life.lib.render import render_dashboard, render_item_list


def test_render_dashboard_empty():
    momentum = {
        "this_week": Weekly(
            tasks_completed=0,
            tasks_total=0,
            habits_completed=0,
            habits_total=0,
            chores_completed=0,
            chores_total=0,
        ),
        "last_week": Weekly(
            tasks_completed=0,
            tasks_total=0,
            habits_completed=0,
            habits_total=0,
            chores_completed=0,
            chores_total=0,
        ),
        "prior_week": Weekly(
            tasks_completed=0,
            tasks_total=0,
            habits_completed=0,
            habits_total=0,
            chores_completed=0,
            chores_total=0,
        ),
    }
    with patch("life.lib.render.get_tags", return_value=[]):
        output = render_dashboard([], (0, 0, 0), momentum, "test context")
        assert "No pending items" in output


def test_render_dashboard_with_focus_items():
    items = [
        Item(
            id="1",
            content="focus item",
            focus=True,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=False,
        )
    ]
    momentum = {
        "this_week": Weekly(),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    with patch("life.lib.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), momentum, "context")
        assert "focus item" in output
        assert "🔥" in output

    momentum = {
        "this_week": Weekly(),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    with patch("life.lib.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), momentum, "context")
        assert "focus item" in output


def test_render_dashboard_with_backlog():
    items = [
        Item(
            id="1",
            content="backlog item",
            focus=False,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=False,
        )
    ]
    momentum = {
        "this_week": Weekly(),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    with patch("life.lib.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), momentum, "context")
        assert "BACKLOG" in output


def test_render_dashboard_with_habits():
    items = [
        Item(
            id="1",
            content="meditate",
            focus=False,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=True,
        )
    ]
    momentum = {
        "this_week": Weekly(),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    with patch("life.lib.render.get_tags", return_value=["habit"]):
        output = render_dashboard(items, (0, 0, 0), momentum, "context")
        assert "HABITS" in output


def test_render_dashboard_with_chores():
    items = [
        Item(
            id="1",
            content="dishes",
            focus=False,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=True,
        )
    ]
    momentum = {
        "this_week": Weekly(),
        "last_week": Weekly(),
        "prior_week": Weekly(),
    }
    with patch("life.lib.render.get_tags", return_value=["chore"]):
        output = render_dashboard(items, (0, 0, 0), momentum, "context")
        assert "CHORES" in output


def test_render_item_list_empty():
    output = render_item_list([])
    assert "No pending items" in output


def test_render_item_list_with_items():
    items = [
        Item(
            id="1",
            content="item 1",
            focus=False,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=False,
        ),
        Item(
            id="2",
            content="item 2",
            focus=True,
            due=None,
            created=datetime.now(),
            completed=None,
            is_repeat=False,
        ),
    ]
    with patch("life.lib.render.get_tags", return_value=[]):
        output = render_item_list(items)
        assert "item 1" in output
        assert "item 2" in output
