from datetime import date, datetime, timedelta

from life.config import get_dates
from life.models import Habit, Task
from life.tasks import _task_sort_key, get_all_links

from . import clock
from .ansi import ANSI, bold, cyan, dim, gold, gray, green, red, white
from .clusters import build_clusters, cluster_focus, link_distances
from .format import format_habit, format_task

__all__ = [
    "render_dashboard",
    "render_habit_matrix",
    "render_item_list",
    "render_momentum",
    "render_task_detail",
]

_R = ANSI.RESET
_GREY = ANSI.GREY


def _fmt_time(t: str) -> str:
    return f"{_GREY}{t}{_R}"


def _fmt_countdown(due_time: str, now_dt) -> str:
    from datetime import datetime as _dt
    due_dt = _dt.combine(now_dt.date(), _dt.strptime(due_time, "%H:%M").time())
    diff = due_dt - now_dt.replace(tzinfo=None)
    total = int(diff.total_seconds())
    if total < 0:
        total = -total
        h, m = divmod(total // 60, 60)
        s = f"{h}h{m:02d}m" if h else f"{m}m"
        return f"{ANSI.GREY}overdue {s}{_R}"
    h, m = divmod(total // 60, 60)
    s = f"{h}h{m:02d}m" if h else f"{m}m"
    return f"{ANSI.GREY}in {s}{_R}"


def _fmt_rel_date(due: date, today: date) -> str:
    delta = (due - today).days
    if delta <= 7:
        day_label = due.strftime("%a").lower()
        return f"{day_label}·{delta}d"
    return f"+{delta}d"


def _fmt_tags(tags: list[str], tag_colors: dict[str, str]) -> str:
    if not tags:
        return ""
    parts = [f"{tag_colors.get(t, _GREY)}#{t}{_R}" for t in tags]
    return " " + " ".join(parts)


def _get_direct_tags(task: Task, all_pending: list[Task]) -> list[str]:
    if not task.parent_id:
        return task.tags

    parent = next((t for t in all_pending if t.id == task.parent_id), None)
    if not parent:
        return task.tags

    parent_tags = parent.tags
    return [tag for tag in task.tags if tag not in parent_tags]


def _build_tag_colors(items: list) -> dict[str, str]:
    tags = sorted({tag for item in items if isinstance(item, (Task, Habit)) for tag in item.tags})
    return {tag: ANSI.POOL[i % len(ANSI.POOL)] for i, tag in enumerate(tags)}


def _get_trend(current: int, previous: int) -> str:
    if previous == 0:
        return "↗" if current > 0 else "→"
    if current > previous:
        return "↗"
    if current < previous:
        return "↘"
    return "→"


def _get_habit_trend(checks: list[datetime]) -> str:
    today = clock.today()
    period1_start = today - timedelta(days=6)
    period2_start = today - timedelta(days=13)
    period2_end = period1_start - timedelta(days=1)

    count_p1 = sum(1 for dt in checks if period1_start <= dt.date() <= today)
    count_p2 = sum(1 for dt in checks if period2_start <= dt.date() <= period2_end)

    if count_p1 > count_p2:
        return "↗"
    if count_p1 < count_p2:
        return "↘"
    return "→"


def _short_date(due: date, today: date) -> str:
    delta = (due - today).days
    if 0 < delta <= 7:
        return due.strftime("%a").upper()
    return due.isoformat()


def _link_hint(task_id: str, linked_peers: dict[str, list[str]]) -> str:
    peers = list(dict.fromkeys(linked_peers.get(task_id, [])))
    if not peers:
        return ""
    return f" {dim('~ ' + ', '.join(peers))}"


def _build_link_peers(tasks: list[Task], links: list[tuple[str, str]]) -> dict[str, list[str]]:
    task_map = {t.id: t for t in tasks}
    peers: dict[str, list[str]] = {}
    for from_id, to_id in links:
        if from_id in task_map and to_id in task_map:
            peers.setdefault(from_id, []).append(task_map[to_id].content.lower())
            peers.setdefault(to_id, []).append(task_map[from_id].content.lower())
    return peers


def _render_header(
    today: date, tasks_done: int, habits_done: int, total_habits: int, added: int, deleted: int
) -> list[str]:
    lines = [f"\n{bold(white(str(today)))}"]
    lines.append(f"{_GREY}done:{_R} {green(str(tasks_done))}")
    lines.append(f"{_GREY}habits:{_R} {cyan(str(habits_done))}{_GREY}/{total_habits}{_R}")
    if added:
        lines.append(f"{_GREY}added:{_R} {gold(str(added))}")
    if deleted:
        lines.append(f"{_GREY}deleted:{_R} {red(str(deleted))}")
    return lines


def _render_done(
    today_items: list[Task | Habit],
    all_pending: list[Task],
    tag_colors: dict[str, str],
) -> list[str]:
    if not today_items:
        return []

    def _sort_key(item):
        if isinstance(item, Task) and item.completed_at:
            return item.completed_at
        if isinstance(item, Habit) and item.checks:
            return max(item.checks)
        return item.created

    sorted_items = sorted(today_items, key=_sort_key)
    pending_by_id = {t.id: t for t in all_pending}

    lines = [bold(green("DONE:"))]
    for item in sorted_items:
        tags_str = _fmt_tags(item.tags, tag_colors)
        content = item.content.lower()
        id_str = f" {_GREY}[{item.id[:8]}]{_R}"
        if isinstance(item, Habit):
            time_str = ""
            if item.checks:
                latest_check = max(item.checks)
                if latest_check.date() == clock.today():
                    time_str = latest_check.strftime("%H:%M")
            lines.append(f"  {gray('✓')} {_GREY}{time_str}{_R} {content}{tags_str}{id_str}")
        elif isinstance(item, Task) and item.completed_at:
            time_str = item.completed_at.strftime("%H:%M")
            parent_str = ""
            if item.parent_id:
                parent = pending_by_id.get(item.parent_id)
                if parent and not parent.completed_at:
                    parent_str = f" {dim('→ ' + parent.content.lower())}"
            lines.append(
                f"  {green('✓')} {_GREY}{time_str}{_R} {content}{tags_str}{id_str}{parent_str}"
            )
    return lines


def _render_upcoming_date(dates_list: list, today: date) -> list[str]:
    if not dates_list:
        return []
    upcoming = sorted(
        [d for d in dates_list if date.fromisoformat(d["date"]) >= today],
        key=lambda x: x["date"],
    )
    if not upcoming:
        return []
    next_date = upcoming[0]
    days = (date.fromisoformat(next_date["date"]) - today).days
    emoji = next_date.get("emoji", "📌")
    name = next_date.get("name", "event")
    return [f"{emoji} {days} days until {name}!"]


def _render_today_tasks(
    due_today: list[Task],
    current_time: str,
    now_dt,
    tag_colors: dict[str, str],
    linked_peers: dict[str, list[str]],
    task_id_to_content: dict[str, str],
    subtasks_by_parent: dict[str, list[Task]],
    all_pending: list[Task],
) -> tuple[list[str], set[str]]:
    lines = [f"\n{bold(white('TODAY:'))}"]
    scheduled_ids: set[str] = set()

    if not due_today:
        lines.append(f"  {gray('nothing scheduled.')}")
        return lines, scheduled_ids

    def _sort_key(task: Task):
        if task.due_time:
            return (0, task.due_time, not task.focus)
        return (1, "", not task.focus)

    sorted_today = sorted(due_today, key=_sort_key)
    now_inserted = False

    for task in sorted_today:
        if not now_inserted and (
            (task.due_time and task.due_time >= current_time) or not task.due_time
        ):
            lines.append(f"  {bold(white('→ ' + current_time))}")
            now_inserted = True

        scheduled_ids.add(task.id)
        tags_str = _fmt_tags(task.tags, tag_colors)
        id_str = f" {_GREY}[{task.id[:8]}]{_R}"
        link_str = _link_hint(task.id, linked_peers)
        time_str = f"{_fmt_countdown(task.due_time, now_dt)} " if task.due_time else ""

        if task.blocked_by:
            blocker = task_id_to_content.get(task.blocked_by, task.blocked_by[:8])
            blocked_str = f" {dim('← ' + blocker.lower())}"
            lines.append(
                f"  ⊘ {_GREY}{time_str}{task.content.lower()}{tags_str}{_R}{blocked_str}{id_str}{link_str}"
            )
        else:
            fire = f" {ANSI.BOLD}🔥{_R}" if task.focus else ""
            lines.append(f"  □ {time_str}{task.content.lower()}{tags_str}{fire}{id_str}{link_str}")

        for sub in sorted(subtasks_by_parent.get(task.id, []), key=_task_sort_key):
            scheduled_ids.add(sub.id)
            sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
            sub_direct_tags = _get_direct_tags(sub, all_pending)
            sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
            sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
            lines.append(f"    {sub_time_str}└ {sub.content.lower()}{sub_tags_str}{sub_id_str}{_R}")

    return lines, scheduled_ids


def _render_day_tasks(
    due_day: list[Task],
    label: str,
    tag_colors: dict[str, str],
    linked_peers: dict[str, list[str]],
    subtasks_by_parent: dict[str, list[Task]],
    all_pending: list[Task],
) -> tuple[list[str], set[str]]:
    if not due_day:
        return [], set()

    lines = [f"\n{bold(white(label + ':'))}"]  
    scheduled_ids: set[str] = set()

    for task in sorted(due_day, key=_task_sort_key):
        scheduled_ids.add(task.id)
        fire = f" {ANSI.BOLD}🔥{_R}" if task.focus else ""
        tags_str = _fmt_tags(task.tags, tag_colors)
        id_str = f" {_GREY}[{task.id[:8]}]{_R}"
        link_str = _link_hint(task.id, linked_peers)
        time_str = f"{_fmt_time(task.due_time)} " if task.due_time else ""
        lines.append(f"  □ {time_str}{task.content.lower()}{tags_str}{fire}{id_str}{link_str}")

        for sub in sorted(subtasks_by_parent.get(task.id, []), key=_task_sort_key):
            scheduled_ids.add(sub.id)
            sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
            sub_direct_tags = _get_direct_tags(sub, all_pending)
            sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
            sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
            lines.append(f"    {sub_time_str}└ {sub.content.lower()}{sub_tags_str}{sub_id_str}{_R}")

    return lines, scheduled_ids


def _render_habits(
    habits: list[Habit], today_habit_ids: set[str], tag_colors: dict[str, str]
) -> list[str]:
    if not habits:
        return []

    checked_count = len(today_habit_ids)
    lines = [f"\n{bold(white(f'HABITS ({checked_count}/{len(habits)}):'))}"]
    sorted_habits = sorted(habits, key=lambda x: x.content.lower())

    for habit in sorted_habits:
        if habit.id in today_habit_ids:
            continue
        tags_str = _fmt_tags(habit.tags, tag_colors)
        trend = _get_habit_trend(habit.checks)
        id_str = f" {_GREY}[{habit.id[:8]}]{_R}"
        lines.append(f"  □ {trend} {habit.content.lower()}{tags_str}{id_str}")

    for habit in sorted_habits:
        if habit.id not in today_habit_ids:
            continue
        tags_str = _fmt_tags(habit.tags, tag_colors)
        trend = _get_habit_trend(habit.checks)
        id_str = f" {_GREY}[{habit.id[:8]}]{_R}"
        lines.append(f"  {gray('✓ ' + trend + ' ' + habit.content.lower())}{tags_str}{id_str}")

    return lines


def _render_task_row(
    task: Task,
    today: date,
    today_str: str,
    tomorrow_str: str,
    tag_colors: dict[str, str],
    task_id_to_content: dict[str, str],
    subtasks_by_parent: dict[str, list[Task]],
    completed_subs_by_parent: dict[str, list[Task]],
    all_pending: list[Task],
    indent: str = "  ",
) -> list[str]:
    tags_str = _fmt_tags(task.tags, tag_colors)
    id_str = f" {_GREY}[{task.id[:8]}]{_R}"

    date_str = ""
    if task.due_date and task.due_date.isoformat() not in (today_str, tomorrow_str):
        label = _fmt_rel_date(task.due_date, today)
        date_str = f"{dim(label)} "

    if task.blocked_by:
        blocker = task_id_to_content.get(task.blocked_by, task.blocked_by[:8])
        blocked_str = f" {dim('← ' + blocker.lower())}"
        row = (
            f"{indent}⊘ {_GREY}{date_str}{task.content.lower()}{tags_str}{_R}{blocked_str}{id_str}"
        )
    else:
        indicator = f"{ANSI.BOLD}🔥{_R} " if task.focus else ""
        row = f"{indent}{indicator}{date_str}{task.content.lower()}{tags_str}{id_str}"

    rows = [row]
    for sub in sorted(subtasks_by_parent.get(task.id, []), key=_task_sort_key):
        sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
        sub_direct_tags = _get_direct_tags(sub, all_pending)
        sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
        sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
        rows.append(
            f"{indent}  {sub_time_str}└ {sub.content.lower()}{sub_tags_str}{sub_id_str}{_R}"
        )
    for sub in completed_subs_by_parent.get(task.id, []):
        sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
        sub_direct_tags = _get_direct_tags(sub, all_pending)
        sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
        sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
        rows.append(
            f"{indent}  {gray(sub_time_str + '└ ✓ ' + sub.content.lower())}{sub_tags_str}{id_str}"
        )
    return rows


def _render_clusters(
    regular_items: list[Task],
    all_links: list[tuple[str, str]],
    today: date,
    today_str: str,
    tomorrow_str: str,
    tag_colors: dict[str, str],
    task_id_to_content: dict[str, str],
    subtasks_by_parent: dict[str, list[Task]],
    completed_subs_by_parent: dict[str, list[Task]],
    all_pending: list[Task],
) -> list[str]:
    if not regular_items:
        return []

    subtask_ids = {t.id for t in regular_items if t.parent_id}
    top_level = [t for t in regular_items if t.id not in subtask_ids]

    clusters = build_clusters(top_level, all_links)
    focused_clusters = [c for c in clusters if cluster_focus(c)]
    clustered_ids: set[str] = {t.id for cluster in focused_clusters for t in cluster}

    lines: list[str] = []

    for cluster in sorted(focused_clusters, key=lambda c: min((t.due_date or date.max) for t in c)):
        focus = cluster_focus(cluster)
        if not focus:
            continue

        distances = link_distances(focus.id, all_links)
        tags_str = _fmt_tags(focus.tags, tag_colors)
        id_str = f" {_GREY}[{focus.id[:8]}]{_R}"
        date_str = ""
        if focus.due_date and focus.due_date.isoformat() not in (today_str, tomorrow_str):
            label = _fmt_rel_date(focus.due_date, today)
            date_str = f"{dim(label)} "
        lines.append(f"\n{bold('⦿')} {date_str}{focus.content.lower()}{tags_str}{id_str}")

        for sub in sorted(subtasks_by_parent.get(focus.id, []), key=_task_sort_key):
            sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
            sub_direct_tags = _get_direct_tags(sub, all_pending)
            sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
            sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
            lines.append(f"  {sub_time_str}└ {sub.content.lower()}{sub_tags_str}{sub_id_str}{_R}")

        peers_close = sorted(
            [t for t in cluster if t.id != focus.id and distances.get(t.id, 99) <= 2],
            key=_task_sort_key,
        )
        peers_far = sorted(
            [t for t in cluster if t.id != focus.id and distances.get(t.id, 99) > 2],
            key=_task_sort_key,
        )

        for peer in peers_close:
            peer_tags_str = _fmt_tags(peer.tags, tag_colors)
            peer_id_str = f" {_GREY}[{peer.id[:8]}]{_R}"
            peer_date_str = ""
            if peer.due_date and peer.due_date.isoformat() not in (today_str, tomorrow_str):
                label = _fmt_rel_date(peer.due_date, today)
                peer_date_str = f"{dim(label)} "
            lines.append(
                f"  {_GREY}~{_R} {peer_date_str}{peer.content.lower()}{peer_tags_str}{peer_id_str}"
            )
            for sub in sorted(subtasks_by_parent.get(peer.id, []), key=_task_sort_key):
                sub_id_str = f" {_GREY}[{sub.id[:8]}]{_R}"
                sub_direct_tags = _get_direct_tags(sub, all_pending)
                sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
                sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
                lines.append(
                    f"    {sub_time_str}└ {sub.content.lower()}{sub_tags_str}{sub_id_str}{_R}"
                )

        for peer in peers_far:
            peer_tags_str = _fmt_tags(peer.tags, tag_colors)
            peer_id_str = f" {_GREY}[{peer.id[:8]}]{_R}"
            peer_date_str = ""
            if peer.due_date and peer.due_date.isoformat() not in (today_str, tomorrow_str):
                label = _fmt_rel_date(peer.due_date, today)
                peer_date_str = f"{label} "
            lines.append(
                f"  {dim('~ ' + peer_date_str + peer.content.lower())}{peer_tags_str}{peer_id_str}"
            )

    unlinked = [t for t in top_level if t.id not in clustered_ids]
    if unlinked:
        lines.append("")
        seen: set[str] = set()
        for task in sorted(unlinked, key=_task_sort_key):
            if task.id in seen:
                continue
            seen.add(task.id)
            lines.extend(
                _render_task_row(
                    task,
                    today,
                    today_str,
                    tomorrow_str,
                    tag_colors,
                    task_id_to_content,
                    subtasks_by_parent,
                    completed_subs_by_parent,
                    all_pending,
                )
            )

    return lines


def render_dashboard(
    items, today_breakdown, momentum, context, today_items=None, profile=None, verbose=False
):
    habits_today, tasks_today, added_today, deleted_today = today_breakdown
    today = clock.today()
    now = clock.now().astimezone()
    current_time = now.strftime("%H:%M")

    today_str = today.isoformat()
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()

    all_pending = [item for item in items if isinstance(item, Task)]
    all_items = items + (today_items or [])
    tag_colors = _build_tag_colors(all_items)
    all_links = get_all_links()
    linked_peers = _build_link_peers(all_pending, all_links)

    lines: list[str] = []

    habits = [item for item in items if isinstance(item, Habit)]
    total_habits = len({h.id for h in habits})
    lines.extend(
        _render_header(today, tasks_today, habits_today, total_habits, added_today, deleted_today)
    )

    done_lines = _render_done(today_items or [], all_pending, tag_colors)
    if done_lines:
        lines.append("")
        lines.extend(done_lines)

    lines.extend(_render_upcoming_date(get_dates(), today))

    all_subtask_ids = {t.id for t in all_pending if t.parent_id}
    subtasks_by_parent: dict[str, list[Task]] = {}
    for t in all_pending:
        if t.parent_id:
            subtasks_by_parent.setdefault(t.parent_id, []).append(t)

    task_id_to_content = {t.id: t.content for t in all_pending}

    due_today = [
        t
        for t in all_pending
        if t.due_date and t.due_date.isoformat() == today_str and t.id not in all_subtask_ids
    ]

    today_lines, scheduled_ids = _render_today_tasks(
        due_today,
        current_time,
        now,
        tag_colors,
        linked_peers,
        task_id_to_content,
        subtasks_by_parent,
        all_pending,
    )
    lines.extend(today_lines)

    for offset in range(1, 8):
        day = today + timedelta(days=offset)
        day_str = day.isoformat()
        if offset == 1:
            label = "TOMORROW"
        elif offset <= 7:
            label = day.strftime("%A").upper()
        else:
            label = day_str
        due_day = [
            t
            for t in all_pending
            if t.due_date and t.due_date.isoformat() == day_str and t.id not in all_subtask_ids
        ]
        day_lines, day_scheduled = _render_day_tasks(
            due_day,
            label,
            tag_colors,
            linked_peers,
            subtasks_by_parent,
            all_pending,
        )
        scheduled_ids.update(day_scheduled)
        lines.extend(day_lines)

    today_habit_items = [item for item in (today_items or []) if isinstance(item, Habit)]
    today_habit_ids = {item.id for item in today_habit_items}
    all_habits = list(set(habits + today_habit_items))
    lines.extend(_render_habits(all_habits, today_habit_ids, tag_colors))

    regular_items = [
        item for item in items if isinstance(item, Task) and item.id not in scheduled_ids
    ]
    completed_today_tasks = [i for i in (today_items or []) if isinstance(i, Task)]
    completed_subs_by_parent: dict[str, list[Task]] = {}
    for t in completed_today_tasks:
        if t.parent_id:
            completed_subs_by_parent.setdefault(t.parent_id, []).append(t)

    lines.extend(
        _render_clusters(
            regular_items,
            all_links,
            today,
            today_str,
            tomorrow_str,
            tag_colors,
            task_id_to_content,
            subtasks_by_parent,
            completed_subs_by_parent,
            all_pending,
        )
    )

    return "\n".join(lines) + "\n"


def render_momentum(momentum) -> str:
    lines = [f"\n{bold(white('MOMENTUM:'))}"]
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

        lines.append(f"\n{bold(white('TRENDS (vs. Last Week):'))}")

        tasks_trend = _get_trend(this_week.tasks_completed, last_week.tasks_completed)
        habits_trend = _get_trend(this_week.habits_completed, last_week.habits_completed)

        lines.append(f"  Tasks: {tasks_trend}")
        lines.append(f"  Habits: {habits_trend}")

    return "\n".join(lines)


def render_item_list(items: list[Task | Habit]):
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
    lines = []
    lines.append("HABIT TRACKER (last 7 days)\n")

    if not habits:
        return "No habits found."

    today = clock.today()
    day_names = [(today - timedelta(days=i)).strftime("%a").lower() for i in range(6, -1, -1)]
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    header = "habit           " + " ".join(day_names) + "   key"
    lines.append(header)
    lines.append("-" * len(header))

    sorted_habits = sorted(habits, key=lambda x: x.content.lower())

    for habit in sorted_habits:
        habit_name = habit.content.lower()
        padded_habit_name = f"{habit_name:<15}"

        check_dates = {dt.date() for dt in habit.checks}

        status_indicators = []
        for date_item in dates:
            if date_item in check_dates:
                status_indicators.append("✓")
            else:
                status_indicators.append("□")

        lines.append(
            f"{padded_habit_name} {'   '.join(status_indicators)}   {_GREY}[{habit.id[:8]}]{_R}"
        )

    return "\n".join(lines)


def render_task_detail(task: Task, subtasks: list[Task], linked: list[Task], mutations: list | None = None) -> str:
    lines = []

    all_tasks = [task, *subtasks, *linked]
    tag_colors = _build_tag_colors(all_tasks)
    tags_str = _fmt_tags(task.tags, tag_colors)
    focus_str = f" {ANSI.BOLD}🔥{_R}" if task.focus else ""
    status = gray("✓") if task.completed_at else "□"
    id_str = f"{dim('[' + task.id + ']')}"

    lines.append(f"{status} {id_str}  {task.content.lower()}{tags_str}{focus_str}")

    if task.due_date:
        due_str = task.due_date.isoformat()
        if task.due_time:
            due_str += f" {_fmt_time(task.due_time)}"
        lines.append(f"  due: {due_str}")

    if task.description:
        lines.append(f"  {task.description}")

    if task.blocked_by:
        lines.append(f"  blocked by: {task.blocked_by}")

    if subtasks:
        lines.append("  subtasks:")
        for sub in sorted(subtasks, key=_task_sort_key):
            sub_status = gray("✓") if sub.completed_at else "□"
            sub_id_str = dim(f"[{sub.id}]")
            sub_direct_tags = _get_direct_tags(sub, all_tasks)
            sub_tags_str = _fmt_tags(sub_direct_tags, tag_colors)
            sub_time_str = f"{dim(_fmt_time(sub.due_time))} " if sub.due_time else ""
            lines.append(
                f"    {sub_status} {sub_id_str}  {sub_time_str}{sub.content.lower()}{sub_tags_str}"
            )

    if linked:
        lines.append("  links:")
        for lt in sorted(linked, key=_task_sort_key):
            lt_status = gray("✓") if lt.completed_at else "□"
            lt_id_str = dim(f"[{lt.id}]")
            lt_tags_str = _fmt_tags(lt.tags, tag_colors)
            lt_time_str = f"{dim(_fmt_time(lt.due_time))} " if lt.due_time else ""
            lines.append(
                f"    {lt_status} {lt_id_str}  {lt_time_str}{lt.content.lower()}{lt_tags_str}"
            )

    deferrals = [m for m in (mutations or []) if m.field == "defer" or m.reason == "overdue_reset"]
    if deferrals:
        lines.append("  deferrals:")
        for m in deferrals:
            when = m.mutated_at.strftime("%Y-%m-%d")
            reason = f" — {m.reason}" if m.reason else ""
            lines.append(f"    {when}{reason}")

    return "\n".join(lines)
