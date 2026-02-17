from datetime import date

from . import clock
from ..models import Habit, Task
from .ansi import ANSI


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


def format_task(task, tags: list[str] | None = None, show_id: bool = False) -> str:
    """Format a task for display. Returns: [⦿] [due] content [#tags] [id]"""
    parts = []

    if task.focus:
        parts.append(f"{ANSI.BOLD}⦿{ANSI.RESET}")

    if task.due_date:
        parts.append(format_due(task.due_date, colorize=True))

    parts.append(task.content.lower())

    if tags:
        tags_str = " ".join(f"{ANSI.GREY}#{tag}{ANSI.RESET}" for tag in tags)
        parts.append(tags_str)

    if show_id:
        parts.append(f"{ANSI.GREY}[{task.id[:8]}]{ANSI.RESET}")

    return " ".join(parts)


def format_habit(
    habit, checked: bool = False, tags: list[str] | None = None, show_id: bool = False
) -> str:
    """Format a habit for display. Returns: [✓|□] content [#tags] [id]"""
    parts = []

    if checked:
        parts.append(f"{ANSI.GREY}✓{ANSI.RESET}")
    else:
        parts.append("□")

    parts.append(habit.content.lower())

    if tags:
        tags_str = " ".join(f"{ANSI.GREY}#{tag}{ANSI.RESET}" for tag in tags)
        parts.append(tags_str)

    if show_id:
        parts.append(f"{ANSI.GREY}[{habit.id[:8]}]{ANSI.RESET}")

    return " ".join(parts)


def format_status(symbol: str, content: str, item_id: str | None = None) -> str:
    """Format status message for action confirmations."""
    if item_id:
        return f"{symbol} {content} {ANSI.GREY}[{item_id[:8]}]{ANSI.RESET}"
    return f"{symbol} {content}"


def format_ambiguous(items: list[Task | Habit]) -> str:
    """Format ambiguous match list for user disambiguation."""
    lines = ["Multiple matches:"]
    for item in items:
        item_id = item.id[:8]
        lines.append(f"  {item_id}: {item.content}")
    return "\n".join(lines)
