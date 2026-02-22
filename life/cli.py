import sys

from fncli import UsageError, cli

from . import db
from .commands import cmd_dashboard, cmd_momentum, cmd_stats, cmd_status
from .habits import cmd_archive, cmd_habits
from .lib.errors import echo, exit_error
from . import mood as _mood
from . import signal as _signal
from .steward import (
    boot,
    close,
    dash,
    improve,
    log,
    observe,
    rm,
)

_ = (boot, close, dash, improve, log, observe, rm, _mood, _signal)


@cli("life")
def dashboard(verbose: bool = False):
    """Life dashboard"""
    cmd_dashboard(verbose=verbose)


@cli("life")
def task(
    content: list[str],
    focus: bool = False,
    due: str | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    desc: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
):
    """Add a task"""
    from .tasks import cmd_task

    cmd_task(
        content,
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
def add(
    content: list[str],
    habit: bool = False,
    focus: bool = False,
    due: str | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    desc: str | None = None,
    done: bool = False,
    steward: bool = False,
    source: str | None = None,
):
    """Add task or habit (--habit)"""
    tags = list(tag) if tag else []
    if habit:
        from .habits import cmd_habit

        cmd_habit(content, tags=tags, under=under)
        return
    from .tasks import cmd_task

    cmd_task(
        content,
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
def show(ref: list[str]):
    """Show full task detail: ID, tags, due, subtasks, links"""
    from .lib.render import render_task_detail
    from .lib.resolve import resolve_task
    from .tasks import get_mutations, get_subtasks

    task = resolve_task(" ".join(ref))
    subtasks = get_subtasks(task.id)
    mutations = get_mutations(task.id)
    echo(render_task_detail(task, subtasks, mutations))


@cli("life")
def habit(
    content: list[str] | None = None,
    tag: list[str] | None = None,
    under: str | None = None,
    private: bool = False,
    log: bool = False,
):
    """Add daily habit or view history (--log)"""
    if log or not content:
        cmd_habits()
        return
    from .habits import cmd_habit

    cmd_habit(content or [], tags=list(tag) if tag else [], under=under, private=private)


@cli("life")
def check(ref: list[str]):
    """Mark task/habit as done"""
    from .items import cmd_check

    cmd_check(ref)


@cli("life")
def uncheck(ref: list[str]):
    """Unmark task/habit as done"""
    from .items import cmd_uncheck

    cmd_uncheck(ref)


@cli("life")
def done(ref: list[str]):
    """Alias for check"""
    from .items import cmd_check

    cmd_check(ref)


@cli("life", name="rm")
def rm_cmd(ref: list[str]):
    """Delete item or completed task (fuzzy match)"""
    from .items import cmd_rm

    cmd_rm(ref)


@cli("life")
def focus(ref: list[str], off: bool = False):
    """Toggle focus on task; --off to remove"""
    from .tasks import cmd_focus, cmd_unfocus

    if off:
        cmd_unfocus(ref)
    else:
        cmd_focus(ref)


@cli("life")
def unfocus(ref: list[str]):
    """Remove focus from task"""
    from .tasks import cmd_unfocus

    cmd_unfocus(ref)


@cli("life")
def due(ref: list[str], when: str, remove: bool = False):
    """Mark a hard deadline — sets scheduled date/time and flags it as deadline"""
    from .tasks import cmd_due

    if remove:
        cmd_due(ref, remove=True)
    else:
        cmd_due([when, *ref])


@cli("life")
def schedule(ref: list[str], when: str | None = None, remove: bool = False):
    """Soft-schedule a task"""
    from .tasks import cmd_schedule

    if remove:
        cmd_schedule(ref, remove=True)
    elif when:
        cmd_schedule([when, *ref])
    else:
        raise UsageError("Usage: life schedule <ref> <when>  or  --remove")


@cli("life")
def now(ref: list[str]):
    """Schedule task for right now"""
    from .tasks import cmd_schedule

    cmd_schedule(["now", *ref])


@cli("life")
def today(ref: list[str] | None = None):
    """Schedule task for today"""
    from .tasks import cmd_schedule

    if ref:
        cmd_schedule(["today", *ref])
    else:
        cmd_dashboard()


@cli("life")
def tomorrow(ref: list[str] | None = None):
    """Schedule task for tomorrow"""
    from .tasks import cmd_schedule

    if ref:
        cmd_schedule(["tomorrow", *ref])


@cli("life")
def rename(ref: list[str], to: str):
    """Rename an item"""
    from .items import cmd_rename

    cmd_rename(ref, to)


@cli("life")
def tag(ref: str, tag_name: str):
    """Add tag to item: life tag <item> <tag>"""
    from .lib.ansi import ANSI
    from .lib.resolve import resolve_item_exact
    from .tags import add_tag

    task, hab = resolve_item_exact(ref)
    if task:
        add_tag(task.id, None, tag_name)
        echo(f"{task.content} {ANSI.GREY}#{tag_name}{ANSI.RESET}")
    elif hab:
        add_tag(None, hab.id, tag_name)
        echo(f"{hab.content} {ANSI.GREY}#{tag_name}{ANSI.RESET}")


@cli("life")
def untag(ref: str, tag_name: str):
    """Remove tag from item"""
    from .lib.ansi import ANSI
    from .lib.resolve import resolve_item_exact
    from .tags import remove_tag

    task, hab = resolve_item_exact(ref)
    if task:
        remove_tag(task.id, None, tag_name)
        echo(f"{task.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}")
    elif hab:
        remove_tag(None, hab.id, tag_name)
        echo(f"{hab.content} ← {ANSI.GREY}#{tag_name}{ANSI.RESET}")


@cli("life")
def cancel(ref: list[str], reason: str):
    """Cancel a task with a reason"""
    from .lib.resolve import resolve_task
    from .tasks import cancel_task

    task = resolve_task(" ".join(ref))
    cancel_task(task.id, reason)
    echo(f"✗ {task.content.lower()} — {reason}")


@cli("life")
def defer(ref: list[str], reason: str):
    """Defer a task with a required reason"""
    from .lib.resolve import resolve_task
    from .tasks import defer_task

    task = resolve_task(" ".join(ref))
    defer_task(task.id, reason)
    echo(f"→ {task.content.lower()} deferred: {reason}")


@cli("life")
def block(ref: list[str], by: str):
    """Mark a task as blocked by another task"""
    from .lib.resolve import resolve_task
    from .tasks import set_blocked_by

    task = resolve_task(" ".join(ref))
    blocker = resolve_task(by)
    if blocker.id == task.id:
        exit_error("A task cannot block itself")
    set_blocked_by(task.id, blocker.id)
    echo(f"⊘ {task.content.lower()}  ←  {blocker.content.lower()}")


@cli("life")
def unblock(ref: list[str]):
    """Clear blocked_by on a task"""
    from .lib.resolve import resolve_task
    from .tasks import set_blocked_by

    task = resolve_task(" ".join(ref))
    if not task.blocked_by:
        exit_error(f"'{task.content}' is not blocked")
    set_blocked_by(task.id, None)
    echo(f"□ {task.content.lower()}  unblocked")


@cli("life", name="set")
def set_cmd(
    ref: list[str], parent: str | None = None, content: str | None = None, desc: str | None = None
):
    """Set parent or content on an existing task"""
    from .tasks import cmd_set

    cmd_set(ref, parent=parent, content=content, description=desc)


@cli("life")
def archive(ref: str | None = None, list_archived: bool = False):
    """Archive a habit (keeps history, hides from daily view)"""
    cmd_archive([ref] if ref else [], show_list=list_archived)


@cli("life")
def habits():
    """Show habits matrix"""
    cmd_habits()


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


@cli("life dates", name="add")
def dates_add(name: str, date: str, type_: str = "other"):
    """Add a recurring date (DD-MM)"""
    from .lib.dates import add_date

    try:
        add_date(name, date, type_)
    except ValueError as e:
        exit_error(str(e))
    echo(f"added: {name} on {date}")


@cli("life dates", name="rm")
def dates_rm(name: str):
    """Remove a recurring date"""
    from .lib.dates import remove_date

    remove_date(name)
    echo(f"removed: {name}")


@cli("life dates", name="list")
def dates_list():
    """List all recurring dates"""
    from .lib.dates import list_dates

    items = list_dates()
    if not items:
        echo("no dates set")
        return
    for d in items:
        type_label = f"  [{d['type']}]" if d["type"] != "other" else ""
        days = d["days_until"]
        days_str = "today" if days == 0 else f"in {days}d"
        echo(f"  {d['name']} — {d['day']:02d}-{d['month']:02d}{type_label}  ({days_str})")


@cli("life pattern", name="log")
def pattern_log(limit: int = 20, tag: str | None = None):
    """Review logged patterns"""
    from .commands import cmd_pattern

    cmd_pattern(show_log=True, limit=limit, tag=tag)


@cli("life pattern", name="add")
def pattern_add(body: str, tag: str | None = None):
    """Log a new pattern"""
    from .commands import cmd_pattern

    cmd_pattern(body=body, tag=tag)


@cli("life pattern", name="rm")
def pattern_rm(ref: str):
    """Remove a pattern by ID or fuzzy match"""
    from .commands import cmd_pattern

    cmd_pattern(rm=ref)


@cli("life track", name="log")
def track_log():
    """Show recent intervention log"""
    from .commands import cmd_track

    cmd_track(show_log=True)


@cli("life track", name="stats")
def track_stats():
    """Show intervention stats"""
    from .commands import cmd_track

    cmd_track(show_stats=True)


@cli("life track", name="won")
def track_won(description: str, note: str | None = None):
    """Log a won intervention"""
    from .commands import cmd_track

    cmd_track(description=description, result="won", note=note)


@cli("life track", name="lost")
def track_lost(description: str, note: str | None = None):
    """Log a lost intervention"""
    from .commands import cmd_track

    cmd_track(description=description, result="lost", note=note)


@cli("life track", name="deferred")
def track_deferred(description: str, note: str | None = None):
    """Log a deferred intervention"""
    from .commands import cmd_track

    cmd_track(description=description, result="deferred", note=note)


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
    from .steward import cmd_tail

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
