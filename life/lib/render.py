from datetime import date, timedelta

from ..config import get_dates
from ..models import Habit, Task
from ..tasks import _task_sort_key
from . import clock
from .ansi import ANSI
from .format import format_habit, format_task


def _get_trend(current: int, previous: int) -> str:
    """Determine trend indicator based on current vs previous value."""
    if previous == 0:
        return "↗" if current > 0 else "→"
    if current > previous:
        return "↗"
    if current < previous:
        return "↘"
    return "→"


def get_habit_trend(checks: list[date]) -> str:
    """Determine if a habit is trending up, down, or stable based on check counts."""
    today = clock.today()

    # Define two 7-day periods
    # Period 1: Last 7 days (today to 6 days ago)
    period1_start = today - timedelta(days=6)
    # Period 2: 7 days before Period 1 (13 days ago to 7 days ago)
    period2_start = today - timedelta(days=13)
    period2_end = period1_start - timedelta(days=1)

    check_count_p1 = sum(1 for d in checks if period1_start <= d <= today)
    check_count_p2 = sum(1 for d in checks if period2_start <= d <= period2_end)

    if check_count_p1 > check_count_p2:
        return "↗"
    if check_count_p1 < check_count_p2:
        return "↘"
    return "→"


def render_today_completed(today_items: list[Task | Habit]):
    """Render today's completed tasks and habits, chronologically."""
    if not today_items:
        return ""

    def _sort_key(item):
        if isinstance(item, Task) and item.completed_at:
            return item.completed_at
        return item.created

    sorted_items = sorted(today_items, key=_sort_key)

    lines = [f"{ANSI.BOLD}{ANSI.GREEN}DONE:{ANSI.RESET}"]

    for item in sorted_items:
        tags = item.tags
        tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
        content = item.content.lower()
        if isinstance(item, Task) and item.completed_at:
            time_str = item.completed_at.strftime("%H:%M")
        else:
            time_str = "--:--"
        if isinstance(item, Habit):
            lines.append(f"  {ANSI.GREY}{time_str} ✓ {content}{tags_str}{ANSI.RESET}")
        else:
            lines.append(f"  {ANSI.GREY}{time_str}{ANSI.RESET} ✓ {content}{tags_str}")

    return "\n".join(lines)


def render_dashboard(items, today_breakdown, momentum, context, today_items=None, profile=None):
    """Render full dashboard view"""
    habits_today, tasks_today, added_today = today_breakdown
    today = clock.today()
    now = clock.now().astimezone()
    current_time = now.strftime("%H:%M")

    today_str = today.isoformat()
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    scheduled_ids = set()

    lines = []
    checked_today = habits_today + tasks_today

    done_section = render_today_completed(today_items or [])
    if done_section:
        lines.append(f"\n{done_section}")

    lines.append(f"\n{today} {current_time}\ndone: {checked_today}  added: {added_today}")
    dates_list = get_dates()
    if dates_list:
        upcoming = sorted(
            [d for d in dates_list if date.fromisoformat(d["date"]) >= today],
            key=lambda x: x["date"],
        )
        if upcoming:
            next_date = upcoming[0]
            days = (date.fromisoformat(next_date["date"]) - today).days
            emoji = next_date.get("emoji", "📌")
            name = next_date.get("name", "event")
            lines.append(f"{emoji} {days} days until {name}!")

    all_pending = [item for item in items if isinstance(item, Task)]
    due_today = [t for t in all_pending if t.due_date and t.due_date.isoformat() == today_str]
    due_tomorrow = [t for t in all_pending if t.due_date and t.due_date.isoformat() == tomorrow_str]

    lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TODAY:{ANSI.RESET}")
    if due_today:
        for task in sorted(due_today, key=_task_sort_key):
            scheduled_ids.add(task.id)
            fire = f" {ANSI.BOLD}🔥{ANSI.RESET}" if task.focus else ""
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in task.tags) if task.tags else ""
            lines.append(f"  □ {task.content.lower()}{tags_str}{fire}")
    else:
        lines.append(f"  {ANSI.GREY}nothing scheduled.{ANSI.RESET}")

    if due_tomorrow:
        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TOMORROW:{ANSI.RESET}")
        for task in sorted(due_tomorrow, key=_task_sort_key):
            scheduled_ids.add(task.id)
            fire = f" {ANSI.BOLD}🔥{ANSI.RESET}" if task.focus else ""
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in task.tags) if task.tags else ""
            lines.append(f"  □ {task.content.lower()}{tags_str}{fire}")

    habits = [item for item in items if isinstance(item, Habit)]
    regular_items = [item for item in items if isinstance(item, Task) and item.id not in scheduled_ids]

    today_habit_items = [item for item in (today_items or []) if isinstance(item, Habit)]
    today_habit_ids = {item.id for item in today_habit_items}

    all_habits_for_display = list(set(habits + today_habit_items))

    if all_habits_for_display:
        checked_today_count = len(today_habit_ids)
        lines.append(
            f"\n{ANSI.BOLD}{ANSI.WHITE}HABITS ({checked_today_count}/{len(all_habits_for_display)}):{ANSI.RESET}"
        )

        sorted_habits = sorted(all_habits_for_display, key=lambda x: x.content.lower())

        incomplete_habits = [h for h in sorted_habits if h.id not in today_habit_ids]
        completed_habits = [h for h in sorted_habits if h.id in today_habit_ids]

        for habit in incomplete_habits:
            content = habit.content
            tags = habit.tags
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
            trend_indicator = get_habit_trend(habit.checks)
            lines.append(f"  □ {trend_indicator} {content.lower()}{tags_str}")

        for habit in completed_habits:
            content = habit.content
            tags = habit.tags
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
            trend_indicator = get_habit_trend(habit.checks)
            lines.append(
                f"  {ANSI.GREY}✓ {trend_indicator} {content.lower()}{tags_str}{ANSI.RESET}"
            )

    if regular_items:
        tagged_regular = {}
        untagged = []

        for task in regular_items:
            tags = task.tags
            if tags:
                for tag in tags:
                    if tag not in tagged_regular:
                        tagged_regular[tag] = []
                    tagged_regular[tag].append(task)
            else:
                untagged.append(task)

        def sort_items(task_list: list[Task]):
            return sorted(task_list, key=_task_sort_key)

        subtask_ids = {t.id for t in regular_items if t.parent_id}
        subtasks_by_parent: dict[str, list[Task]] = {}
        for t in regular_items:
            if t.parent_id:
                subtasks_by_parent.setdefault(t.parent_id, []).append(t)

        def _render_task_with_subtasks(task: Task, indent: str = "  ", tag: str | None = None) -> list[str]:
            other_tags = [t for t in task.tags if t != tag] if tag else task.tags
            tags_str = " " + " ".join(f"#{t}" for t in other_tags) if other_tags else ""
            indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if task.focus else ""
            rows = [f"{indent}{indicator}{task.content.lower()}{tags_str}"]
            for sub in sort_items(subtasks_by_parent.get(task.id, [])):
                sub_tags_str = " " + " ".join(f"#{t}" for t in sub.tags) if sub.tags else ""
                sub_indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if sub.focus else ""
                rows.append(f"{indent}  └ {sub_indicator}{sub.content.lower()}{sub_tags_str}")
            return rows

        for idx, tag in enumerate(sorted(tagged_regular.keys())):
            tag_tasks = [t for t in sort_items(tagged_regular[tag]) if t.id not in subtask_ids]
            if not tag_tasks:
                continue
            tag_color = ANSI.POOL[idx % len(ANSI.POOL)]
            lines.append(
                f"\n{ANSI.BOLD}{tag_color}{tag.upper()} ({len(tag_tasks)}):{ANSI.RESET}"
            )
            for task in tag_tasks:
                lines.extend(_render_task_with_subtasks(task, tag=tag))

        top_untagged = [t for t in sort_items(untagged) if t.id not in subtask_ids]
        if top_untagged:
            lines.append(f"\n{ANSI.BOLD}{ANSI.DIM}BACKLOG ({len(top_untagged)}):{ANSI.RESET}")
            for task in top_untagged:
                lines.extend(_render_task_with_subtasks(task))

    return "\n".join(lines) + "\n"


def render_momentum(momentum) -> str:
    """Render momentum and trends view."""
    lines = [f"\n{ANSI.BOLD}{ANSI.WHITE}MOMENTUM:{ANSI.RESET}"]
    for week_name in ["this_week", "last_week", "prior_week"]:
        week_data = momentum[week_name]
        tasks_c = week_data.tasks_completed
        habits_c = week_data.habits_completed
        tasks_t = week_data.tasks_total
        habits_t = week_data.habits_total

        tasks_rate = (tasks_c / tasks_t) * 100 if tasks_t > 0 else 0
        habits_rate = (habits_c / habits_t) * 100 if habits_t > 0 else 0

        lines.append(f"  {week_name.replace('_', ' ').lower()}:")
        lines.append(f"    tasks: {tasks_c}/{tasks_t} ({tasks_rate:.0f}%)")
        lines.append(f"    habits: {habits_c}/{habits_t} ({habits_rate:.0f}%)")

    if "this_week" in momentum and "last_week" in momentum:
        this_week = momentum["this_week"]
        last_week = momentum["last_week"]

        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TRENDS (vs. Last Week):{ANSI.RESET}")

        tasks_trend = _get_trend(this_week.tasks_completed, last_week.tasks_completed)
        habits_trend = _get_trend(this_week.habits_completed, last_week.habits_completed)

        lines.append(f"  Tasks: {tasks_trend}")
        lines.append(f"  Habits: {habits_trend}")

    return "\n".join(lines)


def render_item_list(items: list[Task | Habit]):
    """Render item list view with IDs"""
    if not items:
        return "No pending items."

    lines = []
    for item in items:
        if isinstance(item, Task):
            lines.append(format_task(item, tags=item.tags, show_id=True))
        else:
            lines.append(format_habit(item, tags=item.tags, show_id=True))

    return "\n".join(lines)


def render_habit_matrix(habits: list[Habit]) -> str:
    """Render a matrix of habits and their check-off status for the last 7 days."""
    lines = []
    lines.append("HABIT TRACKER (last 7 days)\n")

    if not habits:
        return "No habits found."

    today = clock.today()
    day_names = [(today - timedelta(days=i)).strftime("%a").lower() for i in range(6, -1, -1)]
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    header = "habit           " + " ".join(day_names)
    lines.append(header)
    lines.append("-" * len(header))

    sorted_habits = sorted(habits, key=lambda x: x.content.lower())

    for habit in sorted_habits:
        habit_name = habit.content.lower()
        padded_habit_name = f"{habit_name:<15}"

        check_dates = set(habit.checks)

        status_indicators = []
        for d in dates:
            if d in check_dates:
                status_indicators.append("✓")
            else:
                status_indicators.append("□")

        lines.append(f"{padded_habit_name} {'   '.join(status_indicators)}")

    return "\n".join(lines)
