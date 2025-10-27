from unittest.mock import patch

from life.app.render import render_dashboard, render_item_list


def test_render_dashboard_empty():
    with patch("life.app.render.get_tags", return_value=[]):
        output = render_dashboard([], (0, 0, 0), (0.0, 0.0, 0.0), "test context")
        assert "No pending items" in output


def test_render_dashboard_with_focus_items():
    items = [(1, "focus item", 1, None, None, None, None)]
    with patch("life.app.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), (0.0, 0.0, 0.0), "context")
        assert "focus item" in output
        assert "🔥" in output


def test_render_dashboard_with_scheduled():
    items = [(1, "scheduled item", 0, "2025-12-01", None, None, None)]
    with patch("life.app.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), (0.0, 0.0, 0.0), "context")
        assert "scheduled item" in output


def test_render_dashboard_with_backlog():
    items = [(1, "backlog item", 0, None, None, None, None)]
    with patch("life.app.render.get_tags", return_value=[]):
        output = render_dashboard(items, (0, 0, 0), (0.0, 0.0, 0.0), "context")
        assert "BACKLOG" in output


def test_render_dashboard_with_habits():
    items = [(1, "meditate", 0, None, None, None, None)]
    with patch("life.app.render.get_tags", return_value=["habit"]):
        output = render_dashboard(items, (0, 0, 0), (0.0, 0.0, 0.0), "context")
        assert "HABITS" in output


def test_render_dashboard_with_chores():
    items = [(1, "dishes", 0, None, None, None, None)]
    with patch("life.app.render.get_tags", return_value=["chore"]):
        output = render_dashboard(items, (0, 0, 0), (0.0, 0.0, 0.0), "context")
        assert "CHORES" in output


def test_render_item_list_empty():
    output = render_item_list([])
    assert "No pending items" in output


def test_render_item_list_with_items():
    items = [(1, "item 1", 0, None), (2, "item 2", 1, None)]
    with patch("life.app.render.get_tags", return_value=[]):
        output = render_item_list(items)
        assert "item 1" in output
        assert "item 2" in output
