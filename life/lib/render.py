from datetime import date, datetime, timedelta

from life.config import get_dates
from life.models import Habit, Task
from life.tasks import _task_sort_key, get_all_links

from . import clock
from .ansi import ANSI
from .clusters import build_clusters, cluster_focus, link_distances
from .format import format_habit, format_task

__all__ = [
    "render_dashboard",
    "render_habit_matrix",
    "render_item_list",
    "render_momentum",
]


def _due_time_color(due_time: str, now: datetime) -> str:
    try:
        h, m = map(int, due_time.split(":"))
        task_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        delta = (task_dt - now).total_seconds() / 60
        if delta < 0:
            return ANSI.BOLD + ANSI.SOFT_ORANGE
        if delta <= 15:
            return ANSI.SOFT_ORANGE
        if delta <= 60:
            return ANSI.YELLOW
        return ANSI.GREY
    except (ValueError, AttributeError):
        return ANSI.GREY


def _get_trend(current: int, previous: int) -> str:
    """Determine trend indicator based on current vs previous value."""
    if previous == 0:
        return "↗" if current > 0 else "→"
    if current > previous:
        return "↗"
    if current < previous:
        return "↘"
    return "→"


def _get_habit_trend(checks: list[date]) -> str:
    """Determine if a habit is trending up, down, or stable based on check counts."""
    today = clock.today()

    # Define two 7-day periods
    # Period 1: Last 7 days (today to 6 days ago)
    period1_start = today - timedelta(days=6)
    # Period 2: 7 days before Period 1 (13 days ago to 7 days ago)
    period2_start = today - timedelta(days=13)
    period2_end = period1_start - timedelta(days=1)

    check_count_p1 = sum(1 for check_date in checks if period1_start <= check_date <= today)
    check_count_p2 = sum(1 for check_date in checks if period2_start <= check_date <= period2_end)

    if check_count_p1 > check_count_p2:
        return "↗"
    if check_count_p1 < check_count_p2:
        return "↘"
    return "→"


def render_today_completed(today_items: list[Task | Habit], all_pending: list[Task] | None = None):
    """Render today's completed tasks and habits, chronologically."""
    if not today_items:
        return ""

    def _sort_key(item):
        if isinstance(item, Task) and item.completed_at:
            return item.completed_at
        return item.created

    sorted_items = sorted(today_items, key=_sort_key)

    pending_by_id: dict[str, Task] = {t.id: t for t in (all_pending or [])}
    pending_by_parent: dict[str, list[Task]] = {}
    for t in (all_pending or []):
        if t.parent_id:
            pending_by_parent.setdefault(t.parent_id, []).append(t)

    completed_tasks = [i for i in sorted_items if isinstance(i, Task)]
    completed_by_parent: dict[str, list[Task]] = {}
    for t in completed_tasks:
        if t.parent_id:
            completed_by_parent.setdefault(t.parent_id, []).append(t)

    lines = [f"{ANSI.BOLD}{ANSI.GREEN}DONE:{ANSI.RESET}"]

    for item in sorted_items:
        tags = item.tags
        tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""
        content = item.content.lower()
        if isinstance(item, Habit):
            lines.append(f"  {ANSI.GREY}✓ --:-- {content}{tags_str}{ANSI.RESET}")
        elif isinstance(item, Task) and item.completed_at:
            time_str = item.completed_at.strftime("%H:%M")
            if item.parent_id:
                parent = pending_by_id.get(item.parent_id)
                if parent and not parent.completed_at:
                    parent_str = f" {ANSI.DIM}→ {parent.content.lower()}{ANSI.RESET}"
                else:
                    parent_str = ""
            else:
                parent_str = ""
            lines.append(f"  ✓ {ANSI.GREY}{time_str}{ANSI.RESET} {content}{tags_str}{parent_str}")

    return "\n".join(lines)


def _build_tag_color_map(items) -> dict[str, str]:
    all_tags = sorted({tag for item in items if isinstance(item, Task) for tag in item.tags})
    return {tag: ANSI.POOL[i % len(ANSI.POOL)] for i, tag in enumerate(all_tags)}


def _fmt_tags(tags: list[str], tag_colors: dict[str, str]) -> str:
    if not tags:
        return ""
    parts = [f"{tag_colors.get(t, ANSI.GREY)}#{t}{ANSI.RESET}" for t in tags]
    return " " + " ".join(parts)


def render_dashboard(
    items, today_breakdown, momentum, context, today_items=None, profile=None, verbose=False
):
    """Render full dashboard view"""
    habits_today, tasks_today, added_today, deleted_today = today_breakdown
    today = clock.today()
    now = clock.now().astimezone()
    current_time = now.strftime("%H:%M")

    today_str = today.isoformat()
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    scheduled_ids = set()
    tag_colors = _build_tag_color_map(items)

    lines = []
    checked_today = habits_today + tasks_today

    deleted_str = f"  deleted: {ANSI.BOLD}{ANSI.DIM}{deleted_today}{ANSI.RESET}" if deleted_today else ""
    lines.append(f"\n{ANSI.BOLD}{today}{ANSI.RESET} {ANSI.DIM}·{ANSI.RESET} {ANSI.WHITE}{current_time}{ANSI.RESET}\ndone: {ANSI.BOLD}{ANSI.GREEN}{checked_today}{ANSI.RESET}  added: {ANSI.BOLD}{ANSI.SOFT_ORANGE}{added_today}{ANSI.RESET}{deleted_str}")

    all_pending = [item for item in items if isinstance(item, Task)]
    done_section = render_today_completed(today_items or [], all_pending)
    if done_section:
        lines.append(f"\n{done_section}")
    dates_list = get_dates()
    if dates_list:
        upcoming = sorted(
            [
                date_item
                for date_item in dates_list
                if date.fromisoformat(date_item["date"]) >= today
            ],
            key=lambda x: x["date"],
        )
        if upcoming:
            next_date = upcoming[0]
            days = (date.fromisoformat(next_date["date"]) - today).days
            emoji = next_date.get("emoji", "📌")
            name = next_date.get("name", "event")
            lines.append(f"{emoji} {days} days until {name}!")
    all_subtask_ids = {t.id for t in all_pending if t.parent_id}
    due_today = [
        t
        for t in all_pending
        if t.due_date and t.due_date.isoformat() == today_str and t.id not in all_subtask_ids
    ]
    due_tomorrow = [
        t
        for t in all_pending
        if t.due_date and t.due_date.isoformat() == tomorrow_str and t.id not in all_subtask_ids
    ]

    def _today_sort_key(task: Task):
        if task.due_time:
            return (0, task.due_time, not task.focus)
        return (1, "", not task.focus)

    today_task_id_to_content: dict[str, str] = {t.id: t.content for t in all_pending}

    all_subtasks_by_parent: dict[str, list[Task]] = {}
    for t in all_pending:
        if t.parent_id:
            all_subtasks_by_parent.setdefault(t.parent_id, []).append(t)

    lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TODAY:{ANSI.RESET}")
    if due_today:
        for task in sorted(due_today, key=_today_sort_key):
            scheduled_ids.add(task.id)
            tags_str = _fmt_tags(task.tags, tag_colors)
            id_str = f" {ANSI.DIM}[{task.id[:8]}]{ANSI.RESET}" if verbose else ""
            if task.due_time:
                tc = _due_time_color(task.due_time, now)
                time_str = f"{tc}{task.due_time}{ANSI.RESET} "
            else:
                time_str = ""
            if task.blocked_by:
                blocker_name = today_task_id_to_content.get(task.blocked_by, task.blocked_by[:8])
                blocked_str = f" {ANSI.DIM}← {blocker_name.lower()}{ANSI.RESET}"
                lines.append(
                    f"  ⊘ {ANSI.GREY}{time_str}{task.content.lower()}{tags_str}{ANSI.RESET}{blocked_str}{id_str}"
                )
            else:
                fire = f" {ANSI.BOLD}🔥{ANSI.RESET}" if task.focus else ""
                lines.append(f"  □ {time_str}{task.content.lower()}{tags_str}{fire}{id_str}")
            for sub in sorted(all_subtasks_by_parent.get(task.id, []), key=_task_sort_key):
                scheduled_ids.add(sub.id)
                sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                lines.append(f"    {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
    else:
        lines.append(f"  {ANSI.GREY}nothing scheduled.{ANSI.RESET}")

    if due_tomorrow:
        lines.append(f"\n{ANSI.BOLD}{ANSI.WHITE}TOMORROW:{ANSI.RESET}")
        for task in sorted(due_tomorrow, key=_task_sort_key):
            scheduled_ids.add(task.id)
            fire = f" {ANSI.BOLD}🔥{ANSI.RESET}" if task.focus else ""
            tags_str = _fmt_tags(task.tags, tag_colors)
            id_str = f" {ANSI.DIM}[{task.id[:8]}]{ANSI.RESET}" if verbose else ""
            lines.append(f"  □ {task.content.lower()}{tags_str}{fire}{id_str}")
            for sub in sorted(all_subtasks_by_parent.get(task.id, []), key=_task_sort_key):
                scheduled_ids.add(sub.id)
                sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                lines.append(f"    {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")

    habits = [item for item in items if isinstance(item, Habit)]
    regular_items = [
        item for item in items if isinstance(item, Task) and item.id not in scheduled_ids
    ]

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
            trend_indicator = _get_habit_trend(habit.checks)
            lines.append(f"  □ {trend_indicator} {content.lower()}{tags_str}")

        for habit in completed_habits:
            content = habit.content
            tags = habit.tags
            tags_str = " " + " ".join(f"{ANSI.GREY}#{t}{ANSI.RESET}" for t in tags) if tags else ""

            trend_indicator = _get_habit_trend(habit.checks)
            lines.append(
                f"  {ANSI.GREY}✓ {trend_indicator} {content.lower()}{tags_str}{ANSI.RESET}"
            )

    if regular_items:
        def sort_items(task_list: list[Task]):
            return sorted(task_list, key=_task_sort_key)

        completed_today_tasks = [i for i in (today_items or []) if isinstance(i, Task)]
        completed_subs_by_parent: dict[str, list[Task]] = {}
        for t in completed_today_tasks:
            if t.parent_id:
                completed_subs_by_parent.setdefault(t.parent_id, []).append(t)

        subtask_ids = {t.id for t in all_pending if t.parent_id}
        subtasks_by_parent = all_subtasks_by_parent

        task_id_to_content: dict[str, str] = {t.id: t.content for t in items if isinstance(t, Task)}

        def _short_date(due: date) -> str:
            delta = (due - today).days
            if delta <= 7:
                return f"{delta}d"
            return due.strftime("%b %-d")

        def _render_task_with_subtasks(
            task: Task, indent: str = "  ", tag: str | None = None, dim: bool = False
        ) -> list[str]:
            other_tags = [t for t in task.tags if t != tag] if tag else task.tags
            tags_str = _fmt_tags(other_tags, tag_colors)
            id_str = f" {ANSI.DIM}[{task.id[:8]}]{ANSI.RESET}" if verbose else ""
            if task.due_date and task.due_date.isoformat() not in (today_str, tomorrow_str):
                label = _short_date(task.due_date)
                if task.due_time:
                    date_str = f"{ANSI.DIM}{label}·{task.due_time}{ANSI.RESET} "
                else:
                    date_str = f"{ANSI.DIM}{label}{ANSI.RESET} "
            else:
                date_str = ""
            if task.blocked_by:
                blocker_name = task_id_to_content.get(task.blocked_by, task.blocked_by[:8])
                blocked_str = f" {ANSI.DIM}← {blocker_name.lower()}{ANSI.RESET}"
                row = f"{indent}⊘ {ANSI.GREY}{date_str}{task.content.lower()}{tags_str}{ANSI.RESET}{blocked_str}{id_str}"
            else:
                indicator = f"{ANSI.BOLD}🔥{ANSI.RESET} " if task.focus else ""
                row = f"{indent}{indicator}{date_str}{task.content.lower()}{tags_str}{id_str}"
            if dim:
                row = f"{ANSI.DIM}{row}{ANSI.RESET}"
            rows = [row]
            for sub in sort_items(subtasks_by_parent.get(task.id, [])):
                sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                rows.append(f"{indent}  {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
            for sub in completed_subs_by_parent.get(task.id, []):
                sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                rows.append(f"{indent}  {ANSI.ITALIC}{ANSI.GREY}└ ✓ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
            return rows

        all_links = get_all_links()
        top_level_regular = [t for t in regular_items if t.id not in subtask_ids]
        clusters = build_clusters(top_level_regular, all_links)
        clustered_ids: set[str] = {t.id for cluster in clusters for t in cluster}

        for cluster in sorted(clusters, key=lambda c: (not any(t.focus for t in c), min((t.due_date or date.max) for t in c))):
            focus = cluster_focus(cluster)
            if focus:
                distances = link_distances(focus.id, all_links)
                tags_str = _fmt_tags(focus.tags, tag_colors)
                id_str = f" {ANSI.DIM}[{focus.id[:8]}]{ANSI.RESET}" if verbose else ""
                lines.append(f"\n{ANSI.BOLD}⦿{ANSI.RESET} {focus.content.lower()}{tags_str}{id_str}")
                for sub in sort_items(subtasks_by_parent.get(focus.id, [])):
                    sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                    lines.append(f"    {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
                peers_1 = sorted([t for t in cluster if t.id != focus.id and distances.get(t.id, 99) == 1], key=_task_sort_key)
                peers_2 = sorted([t for t in cluster if t.id != focus.id and distances.get(t.id, 99) == 2], key=_task_sort_key)
                for peer in peers_1:
                    peer_tags_str = _fmt_tags(peer.tags, tag_colors)
                    peer_id_str = f" {ANSI.DIM}[{peer.id[:8]}]{ANSI.RESET}" if verbose else ""
                    lines.append(f"  {ANSI.GREY}~{ANSI.RESET} {peer.content.lower()}{peer_tags_str}{peer_id_str}")
                    for sub in sort_items(subtasks_by_parent.get(peer.id, [])):
                        sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                        lines.append(f"      {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
                for peer in peers_2:
                    peer_tags_str = _fmt_tags(peer.tags, tag_colors)
                    peer_id_str = f" {ANSI.DIM}[{peer.id[:8]}]{ANSI.RESET}" if verbose else ""
                    lines.append(f"  {ANSI.DIM}~ {peer.content.lower()}{peer_tags_str}{peer_id_str}{ANSI.RESET}")
            else:
                sorted_cluster = sort_items(cluster)
                first = sorted_cluster[0]
                tags_str = _fmt_tags(first.tags, tag_colors)
                id_str = f" {ANSI.DIM}[{first.id[:8]}]{ANSI.RESET}" if verbose else ""
                lines.append(f"\n  {first.content.lower()}{tags_str}{id_str}")
                for sub in sort_items(subtasks_by_parent.get(first.id, [])):
                    sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                    lines.append(f"    {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")
                for peer in sorted_cluster[1:]:
                    peer_tags_str = _fmt_tags(peer.tags, tag_colors)
                    peer_id_str = f" {ANSI.DIM}[{peer.id[:8]}]{ANSI.RESET}" if verbose else ""
                    lines.append(f"  {ANSI.GREY}~{ANSI.RESET} {peer.content.lower()}{peer_tags_str}{peer_id_str}")
                    for sub in sort_items(subtasks_by_parent.get(peer.id, [])):
                        sub_id_str = f" {ANSI.DIM}[{sub.id[:8]}]{ANSI.RESET}" if verbose else ""
                        lines.append(f"      {ANSI.ITALIC}└ {sub.content.lower()}{sub_id_str}{ANSI.RESET}")

        unlinked = [t for t in top_level_regular if t.id not in clustered_ids]
        if unlinked:
            tagged_regular: dict[str, list[Task]] = {}
            untagged: list[Task] = []
            for task in unlinked:
                if task.tags:
                    for tag in task.tags:
                        tagged_regular.setdefault(tag, []).append(task)
                else:
                    untagged.append(task)

            for tag in sorted(tagged_regular.keys()):
                tag_tasks = sort_items(tagged_regular[tag])
                if not tag_tasks:
                    continue
                tag_color = tag_colors.get(tag, ANSI.GREY)
                lines.append(f"\n{ANSI.BOLD}{tag_color}{tag.upper()} ({len(tag_tasks)}):{ANSI.RESET}")
                for task in tag_tasks:
                    lines.extend(_render_task_with_subtasks(task, tag=tag))

            top_untagged = sort_items(untagged)
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
        for date_item in dates:
            if date_item in check_dates:
                status_indicators.append("✓")
            else:
                status_indicators.append("□")

        lines.append(f"{padded_habit_name} {'   '.join(status_indicators)}")

    return "\n".join(lines)
