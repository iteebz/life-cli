from datetime import date, timedelta

from life.lib.format import format_due


def test_format_due_today():
    today = date.today().isoformat()
    result = format_due(today, colorize=False)
    assert result == "0d:"


def test_format_due_future():
    future = (date.today() + timedelta(days=5)).isoformat()
    result = format_due(future, colorize=False)
    assert result == "5d:"


def test_format_due_tomorrow():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    result = format_due(tomorrow, colorize=False)
    assert result == "1d:"


def test_format_due_past():
    past = (date.today() - timedelta(days=3)).isoformat()
    result = format_due(past, colorize=False)
    assert result == "-3d:"


def test_format_due_empty():
    result = format_due("")
    assert result == ""


def test_format_due_none():
    result = format_due(None)
    assert result == ""
