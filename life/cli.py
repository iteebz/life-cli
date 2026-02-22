import typer

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
from .steward import app as steward_app
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

app = typer.Typer(
    name="life",
    help="Life CLI: manage your tasks, habits, and focus.",
    no_args_is_help=False,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def dashboard(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show IDs"),
):
    """Life dashboard"""
    if ctx.invoked_subcommand is None:
        cmd_dashboard(verbose=verbose)


@app.command(name="dash", hidden=True)
def dash(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show IDs"),
):
    """Alias: life (root)"""
    cmd_dashboard(verbose=verbose)


@app.command()
def add(
    content_args: list[str] = typer.Argument(..., help="Task or habit content"),
    habit: bool = typer.Option(False, "--habit", "-H", help="Add as a daily habit"),
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date/time (today, tomorrow, mon, 'monday 10:00', YYYY-MM-DD)"
    ),
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags"),
    under: str = typer.Option(None, "--under", "-u", help="Parent task/habit (fuzzy match)"),
    description: str = typer.Option(None, "--desc", help="Optional description"),
    done: bool = typer.Option(False, "--done", help="Mark task as done immediately"),
    private: bool = typer.Option(False, "--private", "-p", help="Hide habit from dash (--habit only)"),
    steward: bool = typer.Option(False, "--steward", help="Steward task (hidden from dash)"),
    source: str = typer.Option(None, "--source", help="Task provenance: tyson, steward, scheduled"),
):
    """Add task or habit (--habit). Supports due date/time, tags, focus."""
    if habit:
        from .habits import cmd_habit
        cmd_habit(content_args, tags=list(tags) if tags else [], under=under, private=private)
        return
    cmd_task(
        content_args,
        focus=focus,
        due=due,
        tags=list(tags) if tags else [],
        under=under,
        description=description,
        done=done,
        steward=steward,
        source=source,
    )


@app.command(name="task", hidden=True)
def task(
    content_args: list[str] = typer.Argument(..., help="Task content"),
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),
    under: str = typer.Option(None, "--under", "-u", help="Parent task (fuzzy match)"),
    description: str = typer.Option(None, "--desc", help="Optional description"),
    done: bool = typer.Option(False, "--done", help="Mark task as done immediately"),
    steward: bool = typer.Option(False, "--steward", help="Steward task (hidden from dash)"),
    source: str = typer.Option(None, "--source", help="Task provenance: tyson, steward, scheduled"),
):
    """Alias for add"""
    cmd_task(
        content_args,
        focus=focus,
        due=due,
        tags=list(tags) if tags else [],
        under=under,
        description=description,
        done=done,
        steward=steward,
        source=source,
    )


@app.command()
def show(
    args: list[str] = typer.Argument(..., help="Task to inspect (fuzzy or UUID prefix)"),
):
    """Show full task detail: ID, tags, due, subtasks, links"""
    cmd_show(args)


@app.command()
def habit(
    content_args: list[str] = typer.Argument(None, help="Habit content"),
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),
    under: str = typer.Option(None, "--under", "-u", help="Parent habit (fuzzy match)"),
    private: bool = typer.Option(False, "--private", "-p", help="Hide from dash (steward still sees it)"),
    log: bool = typer.Option(False, "--log", "-l", help="Show all habits and 7-day history"),
):
    """Add daily habit or view history (--log)"""
    if log or not content_args:
        cmd_habits()
        return
    cmd_habit(content_args, tags=tags, under=under, private=private)


@app.command()
def check(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
):
    """Mark task/habit as done"""
    cmd_check(args)


@app.command()
def uncheck(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
):
    """Unmark task/habit as done"""
    cmd_uncheck(args)


@app.command(hidden=True)
def done(
    args: list[str] = typer.Argument(..., help="Partial match for the item to mark done"),
):
    """Alias for check"""
    cmd_check(args)


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),
):
    """Delete item or completed task (fuzzy match)"""
    cmd_rm(args)


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
    off: bool = typer.Option(False, "--off", help="Remove focus"),
):
    """Toggle focus on task; --off to remove"""
    if off:
        cmd_unfocus(args)
    else:
        cmd_focus(args)


@app.command(hidden=True)
def unfocus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
):
    """Alias: life focus --off <task>"""
    cmd_unfocus(args)


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Time spec and item: today, tomorrow, HH:MM, now, YYYY-MM-DD"),
    remove: bool = typer.Option(False, "-r", "--remove", help="Clear deadline"),
):
    """Mark a hard deadline — sets scheduled date/time and flags it as deadline"""
    cmd_due(args, remove=remove)


@app.command()
def rename(
    from_args: list[str] = typer.Argument(
        ..., help="Content to fuzzy match for the item to rename"
    ),
    to_content: str = typer.Argument(..., help="The exact new content for the item"),
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    cmd_rename(from_args, to_content)


@app.command()
def tag(
    args: list[str] = typer.Argument(None, help='Item content then tag name: "ITEM" TAG'),
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),
):
    """Add tag: life tag \"ITEM\" TAG"""
    cmd_tag(None, args, tag_opt=tag_opt, remove=remove)


@app.command(hidden=True)
def untag(
    args: list[str] = typer.Argument(None, help='Item content then tag name: "ITEM" TAG'),
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),
):
    """Alias: life tag "ITEM" TAG --remove"""
    cmd_untag(None, args, tag_opt=tag_opt)


@app.command()
def archive(
    args: list[str] = typer.Argument(None, help="Habit to archive (fuzzy match)"),
    list_archived: bool = typer.Option(False, "--list", "-l", help="List archived habits"),
):
    """Archive a habit (keeps history, hides from daily view)"""
    cmd_archive(args or [], show_list=list_archived)


@app.command(name="habits", hidden=True)
def habits():
    """Alias for habit --log"""
    cmd_habits()


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),
):
    """View or set personal profile"""
    cmd_profile(profile_text)


@app.command()
def dates(
    action: str = typer.Argument(None, help="add, remove, or list"),
    name: str = typer.Argument(None, help="Date name"),
    date_str: str = typer.Argument(None, help="Target date (YYYY-MM-DD)"),
    emoji: str = typer.Option("📌", "-e", "--emoji", help="Emoji for date"),
):
    """Add, remove, or list dates to track"""
    cmd_dates(action, name, date_str, emoji)


@app.command()
def status():
    """Health check — untagged tasks, overdue, habit streaks, janice signal"""
    cmd_status()


@app.command()
def stats():
    """Feedback-loop metrics and escalation signals"""
    cmd_stats()


@app.command()
def momentum():
    """Show momentum and weekly trends"""
    cmd_momentum()


@app.command(name="cancel")
def cancel_cmd(
    args: list[str] = typer.Argument(..., help="Task to cancel (fuzzy)"),
    reason: str = typer.Option(..., "--reason", "--why", help="Why are you cancelling this?"),
):
    """Cancel a task with a reason (preserved for analytics)"""
    cmd_cancel(args, reason)


@app.command(name="defer")
def defer_cmd(
    args: list[str] = typer.Argument(..., help="Task to defer (fuzzy)"),
    reason: str = typer.Option(..., "--reason", "--why", help="Why are you deferring this?"),
):
    """Defer a task with a required reason"""
    cmd_defer(args, reason)


@app.command(name="now", hidden=True)
def now_cmd(
    args: list[str] = typer.Argument(..., help="Task to schedule for right now"),
):
    """Alias: life due now <task>"""
    cmd_now(args)


@app.command(name="today", hidden=True)
def today_cmd(
    args: list[str] = typer.Argument(None, help="Partial task name to set due today"),
):
    """Alias: life due today <task>"""
    cmd_today(args)


@app.command(hidden=True)
def tomorrow(
    args: list[str] = typer.Argument(None, help="Partial task name to set due tomorrow"),
):
    """Alias: life due tomorrow <task>"""
    cmd_tomorrow(args)


@app.command()
def schedule(
    args: list[str] = typer.Argument(..., help="Date/time and task name, or task name with -r"),
    remove: bool = typer.Option(False, "-r", "--remove", help="Clear scheduled date/time"),
):
    """Soft-schedule a task — today, tomorrow, HH:MM, YYYY-MM-DD, or combined"""
    cmd_schedule(args, remove=remove)


@app.command(name="set")
def set_cmd(
    args: list[str] = typer.Argument(..., help="Task to modify (fuzzy match)"),
    parent: str = typer.Option(None, "--parent", "-p", help="Set parent task (fuzzy match)"),
    content: str = typer.Option(None, "--content", "-c", help="Rename task"),
    description: str = typer.Option(
        None, "--desc", "-d", help="Set or clear description (pass empty string to clear)"
    ),
):
    """Set parent or content on an existing task"""
    cmd_set(args, parent=parent, content=content, description=description)


@app.command()
def block(
    blocked: list[str] = typer.Argument(..., help="Task to mark as blocked (fuzzy)"),
    blocker: list[str] = typer.Option(..., "--by", "-b", help="Task that is blocking (fuzzy)"),
):
    """Mark a task as blocked by another task"""
    cmd_block(blocked, blocker)


@app.command()
def unblock(
    args: list[str] = typer.Argument(..., help="Task to unblock (fuzzy)"),
):
    """Clear blocked_by on a task"""
    cmd_unblock(args)


db_app = typer.Typer(
    name="db",
    help="Database management commands",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(db_app, name="db")


@db_app.command(name="migrate")
def db_migrate():
    """Run pending database migrations"""
    from .lib.errors import echo

    db.migrate()
    echo("migrations applied")


@db_app.command(name="backup")
def db_backup():
    """Create database backup"""
    from .lib.backup import backup as _backup
    from .lib.errors import echo

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
    for table, delta in sorted(delta_by_table.items(), key=lambda x: abs(x[1]), reverse=True):
        sign = "+" if delta > 0 else ""
        echo(f"    {table} {sign}{delta}")


@db_app.command(name="health")
def db_health():
    """Check database integrity"""
    from .health import cli as health_cli

    health_cli()


app.add_typer(steward_app, name="steward")


signal_app = typer.Typer(
    name="signal",
    help="Signal messaging",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(signal_app, name="signal")


@signal_app.command(name="send")
def signal_send(
    recipient: str = typer.Argument(..., help="Contact name or +number"),
    message_args: list[str] = typer.Argument(None, help="Message text"),
    message_opt: str = typer.Option(None, "--message", "-m", help="Message text"),
    attachment: str = typer.Option(None, "--attachment", "-a", help="Path to file"),
) -> None:
    """Send a Signal message to a contact or number"""
    from .lib.errors import echo, exit_error
    from .signal import resolve_contact, send

    body = message_opt or (" ".join(message_args) if message_args else None)
    if not body:
        exit_error("message required: life signal send <recipient> <message> or --message")

    number = resolve_contact(recipient)
    success, result = send(number, body, attachment=attachment)
    if success:
        display = recipient if number == recipient else f"{recipient} ({number})"
        echo(f"sent → {display}")
    else:
        exit_error(f"failed: {result}")


@signal_app.command(name="check")
def signal_check(
    timeout: int = typer.Option(5, "--timeout", "-t", help="Receive timeout in seconds"),
) -> None:
    """Pull and display recent Signal messages"""
    from .lib.errors import echo
    from .signal import receive

    messages = receive(timeout=timeout)
    if not messages:
        echo("no new messages")
        return
    for msg in messages:
        sender = msg.get("from_name") or msg.get("from", "?")
        echo(f"{sender}: {msg['body']}")


@signal_app.command(name="status")
def signal_status() -> None:
    """Show registered Signal accounts"""
    from .lib.errors import echo
    from .signal import list_accounts

    accounts = list_accounts()
    if not accounts:
        echo("no Signal accounts — run: signal-cli link")
        return
    for account in accounts:
        echo(account)


@app.command(name="tail", hidden=True)
def tail(
    cycles: int = typer.Option(1, "--cycles", "-n", min=1, help="Number of loop cycles"),
    every: int = typer.Option(0, "--every", min=0, help="Sleep between cycles (seconds)"),
    model: str = typer.Option("glm-4", "--model", "-m", help="Model passed to glm"),
    timeout: int = typer.Option(1200, "--timeout", min=1, help="Per-cycle timeout (seconds)"),
    retries: int = typer.Option(2, "--retries", min=0, help="Retries after failed cycle"),
    retry_delay: int = typer.Option(
        2, "--retry-delay", min=0, help="Sleep between retries (seconds)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print command without executing"),
    raw: bool = typer.Option(False, "--raw", "--json", help="Emit raw stream JSON lines"),
    quiet_system: bool = typer.Option(
        False, "--quiet-system", help="Suppress session/init system lines"
    ),
    continue_on_error: bool = typer.Option(
        False, "--continue-on-error", help="Continue remaining cycles after command failures"
    ),
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


@app.command(name="auto")
def auto(
    cycles: int = typer.Option(1, "--cycles", "-n", min=1, help="Number of loop cycles"),
    every: int = typer.Option(0, "--every", min=0, help="Sleep between cycles (seconds)"),
    model: str = typer.Option("glm-4", "--model", "-m", help="Model passed to glm"),
    timeout: int = typer.Option(1200, "--timeout", min=1, help="Per-cycle timeout (seconds)"),
    retries: int = typer.Option(2, "--retries", min=0, help="Retries after failed cycle"),
    retry_delay: int = typer.Option(
        2, "--retry-delay", min=0, help="Sleep between retries (seconds)"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print command without executing"),
    raw: bool = typer.Option(False, "--raw", "--json", help="Emit raw stream JSON lines"),
    quiet_system: bool = typer.Option(
        False, "--quiet-system", help="Suppress session/init system lines"
    ),
    continue_on_error: bool = typer.Option(
        False, "--continue-on-error", help="Continue remaining cycles after command failures"
    ),
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


@app.command()
def track(
    description: list[str] = typer.Argument(None, help="Intervention description"),
    won: bool = typer.Option(False, "--won", "-w", help="Mark as won"),
    lost: bool = typer.Option(False, "--lost", "-l", help="Mark as lost"),
    deferred: bool = typer.Option(False, "--deferred", "-d", help="Mark as deferred"),
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),
    stats: bool = typer.Option(False, "--stats", "-s", help="Show intervention stats"),
    log: bool = typer.Option(False, "--log", help="Show recent interventions"),
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


@app.command()
def pattern(
    body: list[str] = typer.Argument(None, help="Pattern observation to log"),
    log: bool = typer.Option(False, "--log", "-l", help="Show recent patterns"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of patterns to show"),
    rm: str = typer.Option(None, "--rm", help="Remove pattern by fuzzy match (empty string = latest)"),
    tag: str = typer.Option(None, "--tag", "-t", help="Tag to attach or filter by"),
):
    """Log or review Steward observations about Tyson"""
    if rm is not None:
        cmd_pattern(rm=rm)
        return
    if log:
        cmd_pattern(show_log=True, limit=limit, tag=tag)
        return
    text = " ".join(body) if body else None
    cmd_pattern(body=text, tag=tag)


@app.command()
def mood(
    args: list[str] = typer.Argument(None, help="Score (1-5) and optional label, or 'rm'"),
    show: bool = typer.Option(False, "--log", "-l", help="Show last 24h mood log"),
):
    """Log energy/mood (1-5), view rolling 24h window, or rm latest entry"""
    from .lib.errors import echo, exit_error

    if show or not args:
        cmd_mood(show=True)
        return
    if args[0] == "rm":
        from .mood import delete_latest_mood

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
        score = int(args[0])
    except (ValueError, IndexError):
        exit_error("Usage: life mood <1-5> [label]")
    label = " ".join(args[1:]) if len(args) > 1 else None
    cmd_mood(score=score, label=label)


def main():
    db.init()
    app()


if __name__ == "__main__":
    main()
