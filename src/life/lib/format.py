from datetime import date, datetime


def format_due(due_date_str):
    if not due_date_str:
        return ""

    due = date.fromisoformat(due_date_str)
    today = date.today()
    diff = (due - today).days

    if diff == 0:
        return "today:"
    if diff > 0:
        return f"{diff}d:"
    return f"{abs(diff)}d overdue:"


def format_decay(completed_str):
    if not completed_str:
        return ""

    try:
        completed = datetime.fromisoformat(completed_str)
        now = datetime.now().astimezone()
        diff = now - completed

        days = diff.days
        hours = diff.seconds // 3600
        mins = (diff.seconds % 3600) // 60

        if days > 0:
            return f"- {days}d ago"
        if hours > 0:
            return f"- {hours}h ago"
        return f"- {mins}m ago"
    except Exception:
        return ""
