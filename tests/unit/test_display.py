from unittest.mock import patch
from life.display import render_dashboard, render_task_list
from life.lib.ansi import ANSI


def test_render_dashboard_empty():
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard([], 0, (0, 0, 0, 0), "test context")
        assert ANSI.MAGENTA in output
        assert "LIFE CONTEXT:" in output


def test_render_dashboard_with_focus_tasks():
    tasks = [(1, "focus task", "task", 1, None, None, None)]
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard(tasks, 0, (0, 0, 0, 0), "context")
        assert ANSI.RED in output
        assert "FOCUS" in output
        assert "focus task" in output


def test_render_dashboard_with_scheduled():
    tasks = [(1, "scheduled task", "task", 0, "2025-12-01", None, None)]
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard(tasks, 0, (0, 0, 0, 0), "context")
        assert ANSI.CYAN in output
        assert "SCHEDULE" in output


def test_render_dashboard_with_backlog():
    tasks = [(1, "backlog task", "task", 0, None, None, None)]
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard(tasks, 0, (0, 0, 0, 0), "context")
        assert "BACKLOG" in output


def test_render_dashboard_with_habits():
    tasks = [(1, "meditate", "habit", 0, None, None, None)]
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard(tasks, 0, (0, 0, 0, 0), "context")
        assert "HABITS" in output


def test_render_dashboard_with_chores():
    tasks = [(1, "dishes", "chore", 0, None, None, None)]
    with patch("life.display.get_tags", return_value=[]):
        output = render_dashboard(tasks, 0, (0, 0, 0, 0), "context")
        assert "CHORES" in output


def test_render_task_list_empty():
    output = render_task_list([])
    assert "No pending tasks" in output


def test_render_task_list_with_tasks():
    tasks = [(1, "task 1", "task", 0, None), (2, "task 2", "task", 1, None)]
    output = render_task_list(tasks)
    assert "task 1" in output
    assert "task 2" in output
