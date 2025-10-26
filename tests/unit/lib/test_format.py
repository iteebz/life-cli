from datetime import date, datetime, timedelta

from life.lib.format import format_decay, format_due


def test_format_due_today():
    today = date.today().isoformat()
    result = format_due(today)
    assert result == "today:"


def test_format_due_future():
    future = (date.today() + timedelta(days=5)).isoformat()
    result = format_due(future)
    assert result == "5d:"


def test_format_due_tomorrow():
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    result = format_due(tomorrow)
    assert result == "1d:"


def test_format_due_past():
    past = (date.today() - timedelta(days=3)).isoformat()
    result = format_due(past)
    assert result == "3d overdue:"


def test_format_due_empty():
    result = format_due("")
    assert result == ""


def test_format_due_none():
    result = format_due(None)
    assert result == ""


def test_format_decay_minutes():
    five_min_ago = datetime.now().astimezone() - timedelta(minutes=5)
    iso = five_min_ago.isoformat()
    result = format_decay(iso)
    assert "5m ago" in result


def test_format_decay_hours():
    two_hours_ago = datetime.now().astimezone() - timedelta(hours=2)
    iso = two_hours_ago.isoformat()
    result = format_decay(iso)
    assert "2h ago" in result


def test_format_decay_days():
    three_days_ago = datetime.now().astimezone() - timedelta(days=3)
    iso = three_days_ago.isoformat()
    result = format_decay(iso)
    assert "3d ago" in result


def test_format_decay_empty():
    result = format_decay("")
    assert result == ""


def test_format_decay_none():
    result = format_decay(None)
    assert result == ""


def test_format_decay_invalid():
    result = format_decay("invalid date")
    assert result == ""
