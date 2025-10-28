from datetime import date, datetime

from . import clock
from .ansi import ANSI  # Need to import ANSI for coloring


def format_due(due_date, colorize=True):
    if not due_date:
        return ""

    if isinstance(due_date, str):
        due = date.fromisoformat(due_date)
    elif isinstance(due_date, date):
        due = due_date
    else:
        return ""

    today = clock.today()
    diff = (due - today).days

    if colorize:
        if diff == 0:
            return f"{ANSI.GREY}0d:{ANSI.RESET}"
        if diff > 0:
            return f"{ANSI.GREY}{diff}d:{ANSI.RESET}"
        return f"{ANSI.GREY}{diff}d:{ANSI.RESET}"
    if diff == 0:
        return "0d:"
    if diff > 0:
        return f"{diff}d:"
    return f"{diff}d:"


def format_decay(completed_str):
    if not completed_str:
        return ""

    try:
        completed = datetime.fromisoformat(completed_str)
        now = clock.now().astimezone()
        diff = now - completed

        days = diff.days
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60

        if days > 0:
            return f"- {days}d ago"
        if hours > 0:
            return f"- {hours}h ago"
        return f"- {mins}m ago"
    except ValueError:
        return ""
