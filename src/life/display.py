from datetime import date, datetime, timedelta

from .prompts import CLAUDE_INSTRUCTIONS
from .utils import format_due_date


def render_dashboard(tasks, today_count, momentum, context):
    """Render full dashboard view"""
    this_week_completed, this_week_added, last_week_completed, last_week_added = momentum
    today = date.today()
    now = datetime.now()
    current_time = now.strftime("%H:%M")

    lines = []
    lines.append(f"\nToday: {today} {current_time}")
    lines.append(f"Completed today: {today_count}")
    lines.append(f"\nThis week: {this_week_completed} completed, {this_week_added} added")
    lines.append(f"Last week: {last_week_completed} completed, {last_week_added} added")

    if not tasks:
        lines.append("\nNo pending tasks. You're either productive or fucked.")
    else:
        tomorrow = str(date.today() + timedelta(days=1))

        focus_tasks = [t for t in tasks if t[3] == 1 and t[2] == "task"]
        today_tasks = [t for t in tasks if t[4] == str(today) and t[2] == "task" and t[3] == 0]
        tomorrow_tasks = [t for t in tasks if t[4] == tomorrow and t[2] == "task" and t[3] == 0]
        backlog_tasks = [
            t
            for t in tasks
            if t[2] == "task" and t[3] == 0 and t[4] != str(today) and t[4] != tomorrow
        ]
        reminders = [t for t in tasks if t[2] == "reminder"]

        if focus_tasks:
            lines.append(f"\n🔥 FOCUS ({len(focus_tasks)}/3 max):")
            for _task_id, content, _category, _focus, _due, _created in focus_tasks:
                lines.append(f"  {content.lower()}")

        if today_tasks:
            lines.append(f"\nTODAY ({len(today_tasks)}):")
            for _task_id, content, _category, _focus, _due, _created in today_tasks:
                lines.append(f"  {content.lower()}")

        if tomorrow_tasks:
            lines.append(f"\nTOMORROW ({len(tomorrow_tasks)}):")
            for _task_id, content, _category, _focus, _due, _created in tomorrow_tasks:
                lines.append(f"  {content.lower()}")

        if backlog_tasks:
            lines.append(f"\nBACKLOG ({len(backlog_tasks)}):")
            for _task_id, content, _category, _focus, due, _created in backlog_tasks:
                due_str = f" {format_due_date(due)}" if due else ""
                lines.append(f"  {content.lower()}{due_str}")

        if reminders:
            lines.append(f"\nREMINDERS ({len(reminders)}):")
            sorted_reminders = sorted(reminders, key=lambda x: x[1].lower())
            for _task_id, content, _category, _focus, _due, _created in sorted_reminders:
                lines.append(f"  {content.lower()}")

        lines.append(f"\nLIFE CONTEXT:\n{context}")
        lines.append(f"\n{CLAUDE_INSTRUCTIONS}")

    return "\n".join(lines)


def render_task_list(tasks):
    """Render task list view with IDs"""
    if not tasks:
        return "No pending tasks."

    lines = []
    for task_id, content, category, focus, due, _created in tasks:
        focus_label = "🔥" if focus else ""
        due_str = f" {format_due_date(due)}" if due else ""
        cat_label = f"[{category}]" if category == "reminder" else ""
        lines.append(f"{task_id}: {focus_label}{content.lower()}{due_str} {cat_label}")

    return "\n".join(lines)
