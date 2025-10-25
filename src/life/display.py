from datetime import date, datetime

from .lib.ansi import ANSI, md_to_ansi
from .sqlite import get_tags
from .utils import format_decay, format_due_date


def render_today_completed(today_items):
    """Render today's completed items with checkboxes"""
    if not today_items:
        return ""

    lines = [f"\n{ANSI.BOLD}{ANSI.GREEN}✅ DONE TODAY:{ANSI.RESET}"]

    tasks = [t for t in today_items if t[2] == "task"]
    habits = [t for t in today_items if t[2] == "habit"]
    chores = [t for t in today_items if t[2] == "chore"]

    if tasks:
        for task in tasks:
            time_str = f" {format_decay(task[3])}" if task[3] else ""
            lines.append(f"  ☑ {task[1].lower()}{time_str}")

    if habits:
        for habit in habits:
            time_str = f" {format_decay(habit[3])}" if habit[3] else ""
            lines.append(f"  ☑ {habit[1].lower()} #habit{time_str}")

    if chores:
        for chore in chores:
            time_str = f" {format_decay(chore[3])}" if chore[3] else ""
            lines.append(f"  ☑ {chore[1].lower()} #chore{time_str}")

    return "\n".join(lines)


def render_dashboard(tasks, today_count, momentum, context, today_items=None):
    """Render full dashboard view"""
    this_week_completed, this_week_added, last_week_completed, last_week_added = momentum
    today = date.today()
    now = datetime.now().astimezone()
    current_time = now.strftime("%H:%M")

    lines = []
    lines.append(f"\n{ANSI.BOLD}{ANSI.MAGENTA}LIFE CONTEXT:{ANSI.RESET}\n{md_to_ansi(context)}")

    lines.append(f"\nToday: {today} {current_time}")
    wedding_date = date(2025, 11, 15)
    days_until_wedding = (wedding_date - today).days
    lines.append(f"👰‍♀️ {days_until_wedding} days until wedding!")
    lines.append(f"\nCompleted today: {today_count}")
    lines.append(f"\nThis week: {this_week_completed} completed, {this_week_added} added")
    lines.append(f"Last week: {last_week_completed} completed, {last_week_added} added")

    if today_items:
        lines.append(render_today_completed(today_items))

    if not tasks:
        lines.append("\nNo pending tasks. You're either productive or fucked.")
    else:
        all_tasks = [t for t in tasks if t[2] == "task"]
        habits = [t for t in tasks if t[2] == "habit"]
        chores = [t for t in tasks if t[2] == "chore"]

        # Filter habits/chores: only show if streak broken (last check older than today)
        today = date.today()
        all_habits = habits
        all_chores = chores
        habits = [t for t in habits if t[6] is None or date.fromisoformat(t[6][:10]) < today]
        chores = [t for t in chores if t[6] is None or date.fromisoformat(t[6][:10]) < today]

        tagged_all = {}
        untagged = []

        for task in all_tasks:
            task_id = task[0]
            task_tags = get_tags(task_id)
            if task_tags:
                for tag in task_tags:
                    if tag not in tagged_all:
                        tagged_all[tag] = []
                    tagged_all[tag].append(task)
            else:
                untagged.append(task)

        def sort_tasks(task_list):
            return sorted(task_list, key=lambda x: (not x[3], x[4] or "", x[1].lower()))

        for idx, tag in enumerate(sorted(tagged_all.keys())):
            tasks_by_tag = sort_tasks(tagged_all[tag])
            tag_color = ANSI.POOL[idx % len(ANSI.POOL)]
            lines.append(f"\n{ANSI.BOLD}{tag_color}#{tag.upper()} ({len(tasks_by_tag)}):{ANSI.RESET}")
            for task in tasks_by_tag:
                task_id, content, _category, _focus, due = task[:5]
                due_str = f" {format_due_date(due)}" if due else ""
                other_tags = [t for t in get_tags(task_id) if t != tag]
                tags_str = " " + " ".join(f"#{t}" for t in other_tags) if other_tags else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if _focus else ""
                lines.append(f"  {indicator}{content.lower()}{due_str}{tags_str}")

        untagged_sorted = sort_tasks(untagged)
        if untagged_sorted:
            lines.append(f"\n{ANSI.BOLD}{ANSI.DIM}BACKLOG ({len(untagged_sorted)}):{ANSI.RESET}")
            for task in untagged_sorted:
                task_id, content, _category, _focus, due = task[:5]
                due_str = f" {format_due_date(due)}" if due else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if _focus else ""
                lines.append(f"  {indicator}{content.lower()}{due_str}")

        if all_habits:
            active_habits = [t for t in all_habits if t[6] is not None and date.fromisoformat(t[6][:10]) == today]
            total_habit_completions = sum(task[7] if len(task) > 7 else 0 for task in active_habits)
            lines.append(
                f"\n{ANSI.BOLD}{ANSI.WHITE}HABITS ({total_habit_completions}/{len(all_habits)}):{ANSI.RESET}"
            )
            today_habit_ids = {item[0] for item in (today_items or []) if item[2] == "habit"}
            sorted_habits = sorted(all_habits, key=lambda x: x[1].lower())
            for task in sorted_habits:
                content = task[1]
                last_checked = task[6] if len(task) > 6 else None
                decay = format_decay(last_checked) if last_checked else ""
                decay_str = f" {decay}" if decay else ""
                checked_today = "☑" if task[0] in today_habit_ids else "☐"
                lines.append(f"  {checked_today} {content.lower()}{decay_str}")

        if all_chores:
            active_chores = [t for t in all_chores if t[6] is not None and date.fromisoformat(t[6][:10]) == today]
            total_chore_completions = sum(task[7] if len(task) > 7 else 0 for task in active_chores)
            lines.append(
                f"\n{ANSI.BOLD}{ANSI.WHITE}CHORES ({total_chore_completions}/{len(all_chores)}):{ANSI.RESET}"
            )
            today_chore_ids = {item[0] for item in (today_items or []) if item[2] == "chore"}
            sorted_chores = sorted(all_chores, key=lambda x: x[1].lower())
            for task in sorted_chores:
                content = task[1]
                last_checked = task[6] if len(task) > 6 else None
                decay = format_decay(last_checked) if last_checked else ""
                decay_str = f" {decay}" if decay else ""
                checked_today = "☑" if task[0] in today_chore_ids else "☐"
                lines.append(f"  {checked_today} {content.lower()}{decay_str}")

    return "\n".join(lines)


def render_task_list(tasks):
    """Render task list view with IDs"""
    if not tasks:
        return "No pending tasks."

    lines = []
    for task in tasks:
        task_id, content, category, focus, due = task[:5]
        focus_label = "🔥" if focus else ""
        due_str = f" {format_due_date(due)}" if due else ""
        cat_label = f"[{category}]" if category != "task" else ""
        tags = get_tags(task_id)
        tags_str = " " + " ".join(f"#{tag}" for tag in tags) if tags else ""
        lines.append(f"{task_id}: {focus_label}{content.lower()}{due_str} {cat_label}{tags_str}")

    return "\n".join(lines)
