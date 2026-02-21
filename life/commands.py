from datetime import datetime

from .config import get_profile, set_profile
from .dashboard import get_pending_items, get_today_breakdown, get_today_completed
from .habits import get_habits
from .interventions import add_intervention, get_interventions
from .interventions import get_stats as get_intervention_stats
from .lib.clock import now, today
from .lib.dates import add_date, list_dates, parse_due_date, remove_date
from .lib.errors import echo, exit_error
from .lib.render import render_dashboard, render_momentum
from .metrics import build_feedback_snapshot, render_feedback_snapshot
from .momentum import weekly_momentum
from .patterns import add_pattern, delete_pattern, get_patterns
from .tasks import get_all_tasks, get_tasks, last_completion

from .steward import cmd_tail

__all__ = [
    "cmd_dashboard",
    "cmd_dates",
    "cmd_momentum",
    "cmd_mood",
    "cmd_pattern",
    "cmd_profile",
    "cmd_stats",
    "cmd_status",
    "cmd_tail",
    "cmd_track",
]


def cmd_dashboard(verbose: bool = False) -> None:
    items = get_pending_items() + get_habits()
    today_items = get_today_completed()
    today_breakdown = get_today_breakdown()
    echo(render_dashboard(items, today_breakdown, None, None, today_items, verbose=verbose))


def cmd_profile(profile_text: str | None = None) -> None:
    if profile_text:
        set_profile(profile_text)
        echo(f"Profile set to: {profile_text}")
    else:
        echo(get_profile() or "No profile set")


def cmd_dates(
    action: str | None = None,
    name: str | None = None,
    date_str: str | None = None,
    emoji: str = "📌",
) -> None:
    if not action:
        dates_list = list_dates()
        if dates_list:
            for date_item in dates_list:
                echo(f"{date_item.get('emoji', '📌')} {date_item['name']} - {date_item['date']}")
        else:
            echo("No dates set")
        return
    if action == "add":
        if not name or not date_str:
            exit_error("Error: add requires name and date (YYYY-MM-DD)")
        add_date(name, date_str, emoji)
        echo(f"Added date: {emoji} {name} on {date_str}")
    elif action == "remove":
        if not name:
            exit_error("Error: remove requires a date name")
        remove_date(name)
        echo(f"Removed date: {name}")
    else:
        exit_error(
            f"Error: unknown action '{action}'. Use 'add', 'remove', or no argument to list."
        )


def _format_elapsed(dt) -> str:
    delta = now() - dt
    s = int(delta.total_seconds())
    if s < 60:
        return f"{s}s ago"
    m = s // 60
    if m < 60:
        return f"{m}m ago"
    h = m // 60
    if h < 24:
        return f"{h}h ago"
    d = h // 24
    return f"{d}d ago"


def cmd_status() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    habits = get_habits()
    today_date = today()

    untagged = [t for t in tasks if not t.tags]
    overdue = [t for t in tasks if t.due_date and t.due_date < today_date]
    janice = [t for t in tasks if "janice" in (t.tags or [])]
    focused = [t for t in tasks if t.focus]

    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)

    lc = last_completion()
    last_check_str = _format_elapsed(lc) if lc else "never"

    lines = []
    lines.append(
        f"tasks: {len(tasks)}  habits: {len(habits)}  focused: {len(focused)}  last check: {last_check_str}"
    )
    lines.append("\nHEALTH:")
    lines.append(f"  untagged: {len(untagged)}")
    lines.append(f"  overdue: {len(overdue)}")
    lines.append(f"  janice_open: {len(janice)}")
    lines.append("\nFLAGS:")
    if snapshot.flags:
        lines.append("  " + ", ".join(snapshot.flags))
    else:
        lines.append("  none")
    lines.append("\nHOT LIST:")
    overdue_ids = {t.id for t in overdue}
    hot_overdue = overdue[:3]
    hot_janice = [t for t in janice if t.id not in overdue_ids][:3]
    lines.extend(f"  ! {t.content}" for t in hot_overdue)
    lines.extend(f"  \u2665 {t.content}" for t in hot_janice)
    if not hot_overdue and not hot_janice:
        lines.append("  none")
    echo("\n".join(lines))


def cmd_stats() -> None:
    tasks = get_tasks()
    all_tasks = get_all_tasks()
    today_date = today()
    snapshot = build_feedback_snapshot(all_tasks=all_tasks, pending_tasks=tasks, today=today_date)
    echo("\n".join(render_feedback_snapshot(snapshot)))


def cmd_momentum() -> None:
    echo(render_momentum(weekly_momentum()))


def cmd_mood(
    score: int | None = None,
    label: str | None = None,
    show: bool = False,
) -> None:
    from .mood import add_mood, get_recent_moods

    if show or score is None:
        entries = get_recent_moods(hours=24)
        if not entries:
            echo("no mood logged in the last 24h")
            return
        now_dt = datetime.now()
        for e in entries:
            delta = now_dt - e.logged_at
            secs = delta.total_seconds()
            if secs < 3600:
                rel = f"{int(secs // 60)}m ago"
            elif secs < 86400:
                rel = f"{int(secs // 3600)}h ago"
            else:
                rel = f"{int(secs // 86400)}d ago"
            bar = "\u2588" * e.score + "\u2591" * (5 - e.score)
            label_str = f"  {e.label}" if e.label else ""
            echo(f"  {rel:<10}  {bar}  {e.score}/5{label_str}")
        return

    if score < 1 or score > 5:
        exit_error("Score must be 1-5")
    add_mood(score, label)
    bar = "\u2588" * score + "\u2591" * (5 - score)
    label_str = f"  {label}" if label else ""
    echo(f"\u2192 {bar}  {score}/5{label_str}")


def cmd_track(
    description: str | None = None,
    result: str | None = None,
    note: str | None = None,
    show_stats: bool = False,
    show_log: bool = False,
) -> None:
    if show_stats:
        stats = get_intervention_stats()
        total = sum(stats.values())
        if not total:
            echo("no interventions logged")
            return
        won = stats.get("won", 0)
        lost = stats.get("lost", 0)
        deferred = stats.get("deferred", 0)
        win_rate = int((won / total) * 100) if total else 0
        echo(
            f"won: {won}  lost: {lost}  deferred: {deferred}  total: {total}  win_rate: {win_rate}%"
        )
        return

    if show_log:
        interventions = get_interventions(20)
        if not interventions:
            echo("no interventions logged")
            return
        for intervention in interventions:
            ts = intervention.timestamp.strftime("%m-%d %H:%M")
            note_str = f"  ({intervention.note})" if intervention.note else ""
            echo(f"{ts}  {intervention.result:<8}  {intervention.description}{note_str}")
        return

    if not description or not result:
        exit_error("Usage: life track <description> --won|--lost|--deferred [--note 'text']")

    if result not in ("won", "lost", "deferred"):
        exit_error("Result must be --won, --lost, or --deferred")

    add_intervention(description, result, note)
    symbol = {"won": "\u2713", "lost": "\u2717", "deferred": "\u2192"}[result]
    echo(f"{symbol} {description}")


def cmd_pattern(
    body: str | None = None,
    show_log: bool = False,
    limit: int = 20,
    rm: str | None = None,
    tag: str | None = None,
) -> None:
    if rm is not None:
        patterns = get_patterns(limit=50)
        if not patterns:
            exit_error("no patterns to remove")
        if rm == "":
            target = patterns[0]
        else:
            q = rm.lower()
            matches = [p for p in patterns if q in p.body.lower()]
            if not matches:
                exit_error(f"no pattern matching '{rm}'")
            target = matches[0]
        deleted = delete_pattern(target.id)
        if deleted:
            echo(f"\u2192 removed: {target.body[:80]}")
        else:
            exit_error("delete failed")
        return

    if show_log:
        patterns = get_patterns(limit, tag=tag)
        if not patterns:
            echo("no patterns logged")
            return
        now = datetime.now()
        for p in patterns:
            delta = now - p.logged_at
            s = delta.total_seconds()
            if s < 3600:
                rel = f"{int(s // 60)}m ago"
            elif s < 86400:
                rel = f"{int(s // 3600)}h ago"
            elif s < 86400 * 7:
                rel = f"{int(s // 86400)}d ago"
            else:
                rel = p.logged_at.strftime("%Y-%m-%d")
            tag_suffix = f"  [{p.tag}]" if p.tag else ""
            echo(f"{rel:<10}  {p.body}{tag_suffix}")
        return

    if not body:
        exit_error('Usage: life pattern "observation" or life pattern --log')

    add_pattern(body, tag=tag)
    echo(f"\u2192 {body}")
