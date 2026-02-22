import sys

from fncli import UsageError, cli

from . import db
from .commands import (
    cmd_dashboard,
    cmd_dates,
    cmd_momentum,
    cmd_mood,
    cmd_pattern,
    cmd_profile,
    cmd_stats,
    cmd_status,
    cmd_tail,
    cmd_track,
)
from .habits import cmd_archive, cmd_habit, cmd_habits
from .items import cmd_check, cmd_rename, cmd_rm, cmd_uncheck
from .lib.errors import echo
from .steward import (
    boot,
    close,
    dash,
    improve,
    log,
    observe,
    rm,
)
from .tags import cmd_tag, cmd_untag
from .tasks import (
    cmd_block,
    cmd_cancel,
    cmd_defer,
    cmd_due,
    cmd_focus,
    cmd_now,
    cmd_schedule,
    cmd_set,
    cmd_show,
    cmd_task,
    cmd_today,
    cmd_tomorrow,
    cmd_unblock,
    cmd_unfocus,
)

_ = (boot, close, dash, improve, log, observe, rm)


@cli("life")
def dashboard(verbose: bool = False):
    """Life dashboard"""
    cmd_dashboard(verbose=verbose)


@cli("life")
def add(
    content_args: list[str],
    habit: bool = False,
    focus: bool = False,
    due: str | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    desc: str | None = None,
    done: bool = False,
    private: bool = False,
    steward: bool = False,
    source: str | None = None,
):
    """Add task or habit (--habit). Supports due date/time, tags, focus."""
    tags = list(tag) if tag else []
    if habit:
        cmd_habit(content_args, tags=tags, under=under, private=private)
        return
    cmd_task(
        content_args,
        focus=focus,
        due=due,
        tags=tags,
        under=under,
        description=desc,
        done=done,
        steward=steward,
        source=source,
    )


@cli("life")
def task(
    content_args: list[str],
    focus: bool = False,
    due: str | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    desc: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
):
    """Alias for add"""
    cmd_task(
        content_args,
        focus=focus,
        due=due,
        tags=list(tag) if tag else [],
        under=under,
        description=desc,
        done=done,
        steward=steward,
        source=source,
    )


@cli("life")
def show(args: list[str]):
    """Show full task detail: ID, tags, due, subtasks, links"""
    cmd_show(args)


@cli("life")
def habit(
    content_args: list[str] | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    private: bool = False,
    log: bool = False,
):
    """Add daily habit or view history (--log)"""
    if log or not content_args:
        cmd_habits()
        return
    cmd_habit(content_args, tags=list(tag) if tag else [], under=under, private=private)


@cli("life")
def check(args: list[str]):
    """Mark task/habit as done"""
    cmd_check(args)


@cli("life")
def uncheck(args: list[str]):
    """Unmark task/habit as done"""
    cmd_uncheck(args)


@cli("life")
def done(args: list[str]):
    """Alias for check"""
    cmd_check(args)


@cli("life", name="rm")
def rm_cmd(args: list[str]):
    """Delete item or completed task (fuzzy match)"""
    cmd_rm(args)


@cli("life")
def focus(
    args: list[str],
    off: bool = False,
):
    """Toggle focus on task; --off to remove"""
    if off:
        cmd_unfocus(args)
    else:
        cmd_focus(args)


@cli("life")
def unfocus(args: list[str]):
    """Alias: life focus --off <task>"""
    cmd_unfocus(args)


@cli("life")
def due(
    args: list[str],
    remove: bool = False,
):
    """Mark a hard deadline — sets scheduled date/time and flags it as deadline"""
    cmd_due(args, remove=remove)


@cli("life")
def rename(
    from_args: list[str],
    to: str,
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    cmd_rename(from_args, to)


@cli("life")
def tag(
    args: list[str],
    tag_opt: str | None = None,
    remove: bool = False,
):
    """Add tag: life tag \"ITEM\" TAG"""
    cmd_tag(None, args, tag_opt=tag_opt, remove=remove)


@cli("life")
def untag(
    args: list[str],
    tag_opt: str | None = None,
):
    """Alias: life tag \"ITEM\" TAG --remove"""
    cmd_untag(None, args, tag_opt=tag_opt)


@cli("life")
def archive(
    args: list[str] | None = None,
    list_archived: bool = False,
):
    """Archive a habit (keeps history, hides from daily view)"""
    cmd_archive(args or [], show_list=list_archived)


@cli("life")
def habits():
    """Alias for habit --log"""
    cmd_habits()


@cli("life")
def profile(profile_text: str | None = None):
    """View or set personal profile"""
    cmd_profile(profile_text)


@cli("life")
def dates(
    args: list[str] | None = None,
    type_: str = "other",
):
    """Add, remove, or list recurring dates (birthdays, anniversaries)"""
    items = args or []
    action = items[0] if len(items) > 0 else None
    name = items[1] if len(items) > 1 else None
    date_str = items[2] if len(items) > 2 else None
    cmd_dates(action, name, date_str, type_)


@cli("life")
def status():
    """Health check — untagged tasks, overdue, habit streaks, janice signal"""
    cmd_status()


@cli("life")
def stats():
    """Feedback-loop metrics and escalation signals"""
    cmd_stats()


@cli("life")
def momentum():
    """Show momentum and weekly trends"""
    cmd_momentum()


@cli("life")
def cancel(
    args: list[str],
    reason: str | None = None,
):
    """Cancel a task with a reason (preserved for analytics)"""
    if not reason:
        raise UsageError("--reason is required")
    cmd_cancel(args, reason)


@cli("life")
def defer(
    args: list[str],
    reason: str | None = None,
):
    """Defer a task with a required reason"""
    if not reason:
        raise UsageError("--reason is required")
    cmd_defer(args, reason)


@cli("life")
def now(args: list[str]):
    """Alias: life due now <task>"""
    cmd_now(args)


@cli("life")
def today(args: list[str] | None = None):
    """Alias: life due today <task>"""
    cmd_today(args or [])


@cli("life")
def tomorrow(args: list[str] | None = None):
    """Alias: life due tomorrow <task>"""
    cmd_tomorrow(args or [])


@cli("life")
def schedule(
    args: list[str],
    remove: bool = False,
):
    """Soft-schedule a task — today, tomorrow, HH:MM, YYYY-MM-DD, or combined"""
    cmd_schedule(args, remove=remove)


@cli("life", name="set")
def set_cmd(
    args: list[str],
    parent: str | None = None,
    content: str | None = None,
    desc: str | None = None,
):
    """Set parent or content on an existing task"""
    cmd_set(args, parent=parent, content=content, description=desc)


@cli("life")
def block(
    blocked: list[str],
    by: list[str] | None = None,
):
    """Mark a task as blocked by another task"""
    cmd_block(blocked, by or [])


@cli("life")
def unblock(args: list[str]):
    """Clear blocked_by on a task"""
    cmd_unblock(args)


@cli("life db", name="migrate")
def db_migrate():
    """Run pending database migrations"""
    db.migrate()
    echo("migrations applied")


@cli("life db", name="backup")
def db_backup():
    """Create database backup"""
    from .lib.backup import backup as _backup

    result = _backup()
    path = result["path"]
    rows = result["rows"]
    delta_total = result["delta_total"]
    delta_by_table = result["delta_by_table"]
    delta_str = ""
    if delta_total is not None and delta_total != 0:
        delta_str = f" (+{delta_total})" if delta_total > 0 else f" ({delta_total})"
    echo(str(path))
    echo(f"  {rows} rows{delta_str}")
    for tbl, delta in sorted(delta_by_table.items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if delta > 0 else ""
        echo(f"    {tbl} {sign}{delta}")


@cli("life db", name="health")
def db_health():
    """Check database integrity"""
    from .health import cli as health_cli

    health_cli()


@cli("life signal", name="send")
def signal_send(
    recipient: str,
    message_args: list[str] | None = None,
    message: str | None = None,
    attachment: str | None = None,
):
    """Send a Signal message to a contact or number"""
    from .lib.errors import exit_error
    from .signal import resolve_contact, send

    args = message_args or []
    body = message or (" ".join(args) if args else None)
    if not body:
        raise UsageError("message required: life signal send <recipient> <message> or --message")

    number = resolve_contact(recipient)
    success, result = send(number, body, attachment=attachment)
    if success:
        display = recipient if number == recipient else f"{recipient} ({number})"
        echo(f"sent → {display}")
    else:
        exit_error(f"failed: {result}")


@cli("life signal", name="check")
def signal_check(timeout: int = 5):
    """Pull and display recent Signal messages"""
    from .signal import receive

    messages = receive(timeout=timeout)
    if not messages:
        echo("no new messages")
        return
    for msg in messages:
        sender = msg.get("from_name") or msg.get("from", "?")
        echo(f"{sender}: {msg['body']}")


@cli("life signal", name="status")
def signal_status():
    """Show registered Signal accounts"""
    from .signal import list_accounts

    accounts = list_accounts()
    if not accounts:
        echo("no Signal accounts — run: signal-cli link")
        return
    for account in accounts:
        echo(account)


@cli("life", name="tail")
def tail_cmd(
    cycles: int = 1,
    every: int = 0,
    model: str = "glm-4",
    timeout: int = 1200,
    retries: int = 2,
    retry_delay: int = 2,
    dry_run: bool = False,
    raw: bool = False,
    quiet_system: bool = False,
    continue_on_error: bool = False,
):
    """Compatibility alias for auto"""
    cmd_tail(
        cycles=cycles,
        interval_seconds=every,
        model=model,
        timeout_seconds=timeout,
        retries=retries,
        retry_delay_seconds=retry_delay,
        dry_run=dry_run,
        raw=raw,
        quiet_system=quiet_system,
        continue_on_error=continue_on_error,
    )


@cli("life")
def auto(
    cycles: int = 1,
    every: int = 0,
    model: str = "glm-4",
    timeout: int = 1200,
    retries: int = 2,
    retry_delay: int = 2,
    dry_run: bool = False,
    raw: bool = False,
    quiet_system: bool = False,
    continue_on_error: bool = False,
):
    """Run unattended Steward loop through the glm connector"""
    cmd_tail(
        cycles=cycles,
        interval_seconds=every,
        model=model,
        timeout_seconds=timeout,
        retries=retries,
        retry_delay_seconds=retry_delay,
        dry_run=dry_run,
        raw=raw,
        quiet_system=quiet_system,
        continue_on_error=continue_on_error,
    )


@cli("life")
def track(
    description: list[str] | None = None,
    won: bool = False,
    lost: bool = False,
    deferred: bool = False,
    note: str | None = None,
    stats: bool = False,
    log: bool = False,
):
    """Log intervention results (Steward use)"""
    if stats:
        cmd_track(show_stats=True)
        return
    if log:
        cmd_track(show_log=True)
        return
    result = None
    if won:
        result = "won"
    elif lost:
        result = "lost"
    elif deferred:
        result = "deferred"
    desc = " ".join(description) if description else None
    cmd_track(description=desc, result=result, note=note)


@cli("life")
def pattern(
    body: list[str] | None = None,
    log: bool = False,
    limit: int = 20,
    rm: str | None = None,
    tag: str | None = None,
):
    """Log or review Steward observations about Tyson"""
    if rm is not None:
        cmd_pattern(rm=rm)
        return
    if log:
        cmd_pattern(show_log=True, limit=limit, tag=tag)
        return
    if body:
        text = " ".join(body)
        cmd_pattern(body=text, tag=tag)
        return
    cmd_pattern(show_log=True, limit=limit, tag=tag)


@cli("life")
def mood(
    args: list[str] | None = None,
    log: bool = False,
):
    """Log energy/mood (1-5), view rolling 24h window, or rm latest entry"""
    from .lib.errors import exit_error
    from .mood import delete_latest_mood

    items = args or []
    if log or not items:
        cmd_mood(show=True)
        return
    if items[0] == "rm":
        try:
            entry = delete_latest_mood()
        except ValueError as e:
            exit_error(str(e))
        if not entry:
            exit_error("no mood entries to remove")
        bar = "█" * entry.score + "░" * (5 - entry.score)
        label_str = f"  {entry.label}" if entry.label else ""
        echo(f"✗ {bar}  {entry.score}/5{label_str}")
        return
    try:
        score = int(items[0])
    except (ValueError, IndexError):
        raise UsageError("Usage: life mood <1-5> [label]") from None
    label = " ".join(items[1:]) if len(items) > 1 else None
    cmd_mood(score=score, label=label)


@cli("life steward", name="run")
def steward_run():
    """Run autonomous steward loop"""
    from .steward import _run_autonomous

    _run_autonomous()


def main():
    db.init()
    from fncli import dispatch

    user_args = sys.argv[1:]
    if not user_args or user_args == ["-v"] or user_args == ["--verbose"]:
        verbose = "--verbose" in user_args or "-v" in user_args
        cmd_dashboard(verbose=verbose)
        return
    argv = ["life", *user_args]
    code = dispatch(argv)
    sys.exit(code)


if __name__ == "__main__":
    main()
