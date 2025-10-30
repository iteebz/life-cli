from datetime import date, timedelta

from ..api.checks import get_checks
from ..api.habits import get_all_habits
from ..api.models import Habit, Task
from ..api.tags import get_tags_for_habit, get_tags_for_task
from ..config import get_countdowns
from . import clock
from .ansi import ANSI
from .format import format_decay, format_due


def get_habit_trend(habit_id: str) -> str:
    """Determine if a habit is trending up, down, or stable based on check counts."""
    check_dates = get_checks(habit_id)

    today = clock.today()

    # Define two 7-day periods
    # Period 1: Last 7 days (today to 6 days ago)
    period1_start = today - timedelta(days=6)
    # Period 2: 7 days before Period 1 (13 days ago to 7 days ago)
    period2_start = today - timedelta(days=13)
    period2_end = period1_start - timedelta(days=1)

    check_count_p1 = sum(1 for d in check_dates if period1_start <= d <= today)
    check_count_p2 = sum(1 for d in check_dates if period2_start <= d <= period2_end)

    if check_count_p1 > check_count_p2:
        return "↗"
    if check_count_p1 < check_count_p2:
        return "↘"
    return "→"


def render_today_completed(today_items: list[Task | Habit]):
    """Render today's completed tasks only (habits handled at bottom)"""
    if not today_items:
        return ""

    tasks_only = [item for item in today_items if isinstance(item, Task)]

    if not tasks_only:
        return ""

    lines = [f"\n{ANSI.BOLD}{ANSI.GREEN}✅ DONE TODAY:{ANSI.RESET}"]

    for task in tasks_only:
        content = task.content
        time_str = f" {format_decay(task.completed)}" if task.completed else ""
        tags = get_tags_for_task(task.id)
        tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
        lines.append(f"  ✓ {content.lower()}{tags_str}{time_str}")

    return "\n".join(lines)


def render_dashboard(items, today_breakdown, momentum, context, today_items=None, profile=None):
    """Render full dashboard view"""
    habits_today, tasks_today = today_breakdown
    today = clock.today()
    now = clock.now().astimezone()
    current_time = now.strftime("%H:%M")

    lines = []
    if profile:
        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}PROFILE:{ANSI.RESET}")
        lines.append(f"{profile}")
    if context:
        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}CONTEXT:{ANSI.RESET}")
        lines.append(f"{context}")
    lines.append(f"\nToday: {today} {current_time}")
    countdowns = get_countdowns()
    if countdowns:
        upcoming = sorted(countdowns, key=lambda x: x["date"])
        next_cd = upcoming[0]
        days = (date.fromisoformat(next_cd["date"]) - today).days
        emoji = next_cd.get("emoji", "📌")
        name = next_cd.get("name", "event")
        lines.append(f"{emoji} {days} days until {name}!")

    lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}MOMENTUM:{ANSI.RESET}")
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

    # Add trend indicators (comparing this_week to last_week)
    if "this_week" in momentum and "last_week" in momentum:
        this_week = momentum["this_week"]
        last_week = momentum["last_week"]

        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TRENDS (vs. Last Week):{ANSI.RESET}")

        def get_trend(current, previous):
            if previous == 0:
                return "↗" if current > 0 else "→"
            if current > previous:
                return "↗"
            if current < previous:
                return "↘"
            return "→"

        tasks_trend = get_trend(this_week.tasks_completed, last_week.tasks_completed)
        habits_trend = get_trend(this_week.habits_completed, last_week.habits_completed)

        lines.append(f"  Tasks: {tasks_trend}")
        lines.append(f"  Habits: {habits_trend}")

    if today_items:
        lines.append(render_today_completed(today_items))

    habits = [item for item in items if isinstance(item, Habit)]
    regular_items = [item for item in items if isinstance(item, Task)]

    today_habit_items = [item for item in (today_items or []) if isinstance(item, Habit)]
    today_habit_ids = {item.id for item in today_habit_items}

    all_habits_for_display = list(set(habits + today_habit_items))

    if all_habits_for_display:
        checked_today_count = len(today_habit_ids)
        lines.append(
            f"\n{ANSI.BOLD}{ANSI.WHITE}HABITS ({checked_today_count}/{len(all_habits_for_display)}):{ANSI.RESET}"
        )

        sorted_habits = sorted(all_habits_for_display, key=lambda x: x.content.lower())

        displayed_completed_content = set()

        for habit in sorted_habits:
            content = habit.content
            decay = format_decay(habit.created) if habit.created else ""
            decay_str = f" {decay}" if decay else ""
            tags = get_tags_for_habit(habit.id)
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
            trend_indicator = get_habit_trend(habit.id)
            if habit.id in today_habit_ids:
                if content not in displayed_completed_content:
                    lines.append(
                        f"  {ANSI.GREY}✓ {trend_indicator} {content.lower()}{tags_str}{decay_str}{ANSI.RESET}"
                    )
                    displayed_completed_content.add(content)
            else:
                lines.append(f"  □ {trend_indicator} {content.lower()}{tags_str}{decay_str}")

    if not regular_items:
        lines.append("\nNo pending items. You're either productive or fucked.")
    else:
        today = clock.today()

        tagged_regular = {}
        untagged = []

        for task in regular_items:
            tags = get_tags_for_task(task.id)
            if tags:
                for tag in tags:
                    if tag not in tagged_regular:
                        tagged_regular[tag] = []
                    tagged_regular[tag].append(task)
            else:
                untagged.append(task)

        def sort_items(task_list: list[Task]):
            return sorted(
                task_list,
                key=lambda x: (
                    not x.focus,
                    x.due_date is None,
                    x.due_date or date.min,
                    x.content.lower(),
                ),
            )

        for idx, tag in enumerate(sorted(tagged_regular.keys())):
            items_by_tag = sort_items(tagged_regular[tag])
            tag_color = ANSI.POOL[idx % len(ANSI.POOL)]
            lines.append(
                f"\n{ANSI.BOLD}{tag_color}#{tag.upper()} ({len(items_by_tag)}):{ANSI.RESET}"
            )
            for task in items_by_tag:
                due_str = format_due(task.due_date) if task.due_date else ""
                other_tags = [t for t in get_tags_for_task(task.id) if t != tag]
                tags_str = " " + " ".join(f"#{t}" for t in other_tags) if other_tags else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if task.focus else ""
                due_part = f"{due_str} " if due_str else ""
                lines.append(f"  {indicator}{due_part}{task.content.lower()}{tags_str}")

        untagged_sorted = sort_items(untagged)
        if untagged_sorted:
            lines.append(f"\n{ANSI.BOLD}{ANSI.DIM}BACKLOG ({len(untagged_sorted)}):{ANSI.RESET}")
            for task in untagged_sorted:
                due_str = format_due(task.due_date) if task.due_date else ""
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if task.focus else ""
                due_part = f"{due_str} " if due_str else ""
                lines.append(f"  {indicator}{due_part}{task.content.lower()}")

    return "\n".join(lines)


def render_item_list(items: list[Task | Habit]):
    """Render item list view with IDs"""
    if not items:
        return "No pending items."

    lines = []
    for item in items:
        focus_label = ""
        due_part = ""

        if isinstance(item, Task):
            focus_label = "🔥" if item.focus else ""
            due_str = format_due(item.due_date) if item.due_date else ""
            due_part = f"{due_str} " if due_str else ""
            tags = get_tags_for_task(item.id)
        else:
            tags = get_tags_for_habit(item.id)

        tags_str = " " + " ".join(f"#{tag}" for tag in tags) if tags else ""
        lines.append(f"{item.id}: {focus_label}{due_part}{item.content.lower()}{tags_str}")

    return "\n".join(lines)


def render_focus_items(items: list[Task]):
    """Render focused items list"""
    if not items:
        return f"{ANSI.GREY}No focus items. Time to focus on something.{ANSI.RESET}"

    lines = [f"{ANSI.BOLD}{ANSI.YELLOW}🔥 FOCUS ITEMS:{ANSI.RESET}\n"]
    for task in items:
        due_str = format_due(task.due_date) if task.due_date else ""
        due_part = f"{due_str} " if due_str else ""
        tags = get_tags_for_task(task.id)
        tags_str = " " + " ".join(f"{ANSI.GREY}#{tag}{ANSI.RESET}" for tag in tags) if tags else ""
        lines.append(f"  • {due_part}{task.content.lower()}{tags_str}")

    return "\n".join(lines)


def render_habit_matrix() -> str:
    """Render a matrix of habits and their check-off status for the last 7 days."""
    lines = []
    lines.append("HABIT TRACKER (last 7 days)\n")

    habit_matrix = get_all_habits()

    if not habit_matrix:
        return "No habits found."

    today = clock.today()
    day_names = [(today - timedelta(days=i)).strftime("%a").lower() for i in range(6, -1, -1)]
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    header = "habit           " + " ".join(day_names)
    lines.append(header)
    lines.append("-" * len(header))

    sorted_habits = sorted(habit_matrix, key=lambda x: x.content.lower())

    for habit in sorted_habits:
        habit_name = habit.content.lower()
        padded_habit_name = f"{habit_name:<15}"

        check_dates = set(get_checks(habit.id))

        status_indicators = []
        for d in dates:
            if d in check_dates:
                status_indicators.append("✓")
            else:
                status_indicators.append("□")

        lines.append(f"{padded_habit_name} {'   '.join(status_indicators)}")

    return "\n".join(lines)
