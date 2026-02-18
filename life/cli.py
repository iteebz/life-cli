import typer

from . import db
from .commands import (
    cmd_archive,
    cmd_backup,
    cmd_block,
    cmd_check,
    cmd_dashboard,
    cmd_dates,
    cmd_defer,
    cmd_done,
    cmd_due,
    cmd_focus,
    cmd_habit,
    cmd_habits,
    cmd_momentum,
    cmd_now,
    cmd_profile,
    cmd_rename,
    cmd_rm,
    cmd_schedule,
    cmd_stats,
    cmd_status,
    cmd_steward,
    cmd_tag,
    cmd_uncheck,
    cmd_unfocus,
    cmd_untag,
    cmd_task,
    cmd_today,
    cmd_tomorrow,
    cmd_track,
    cmd_set,
    cmd_unblock,
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


@app.command(name="dash")
def dash(
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show IDs"),
):
    """Life dashboard"""
    cmd_dashboard(verbose=verbose)


@app.command()
def task(
    content_args: list[str] = typer.Argument(..., help="Task content"),
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),
    under: str = typer.Option(None, "--under", "-u", help="Parent task (fuzzy match)"),
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    cmd_task(content_args, focus=focus, due=due, tags=tags, under=under)


@app.command()
def habit(
    content_args: list[str] = typer.Argument(..., help="Habit content"),
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),
):
    """Add daily habit (auto-resets on completion)"""
    cmd_habit(content_args, tags=tags)


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
    cmd_done(args)


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),
):
    """Delete item or completed task (fuzzy match)"""
    cmd_rm(args)


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
):
    """Toggle focus status on task (fuzzy match)"""
    cmd_focus(args)


@app.command()
def unfocus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),
):
    """Remove focus from task (fuzzy match)"""
    cmd_unfocus(args)


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),
):
    """Set or remove due date on item (fuzzy match)"""
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
    tag_name: str | None = typer.Argument(None, help="Tag name"),
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),
):
    """Add or remove tag on item (fuzzy match)"""
    cmd_tag(tag_name, args, tag_opt=tag_opt, remove=remove)


@app.command()
def untag(
    tag_name: str | None = typer.Argument(None, help="Tag name"),
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),
):
    """Remove tag from item (fuzzy match)"""
    cmd_untag(tag_name, args, tag_opt=tag_opt)


@app.command()
def archive(
    args: list[str] = typer.Argument(None, help="Habit to archive (fuzzy match)"),
    list_archived: bool = typer.Option(False, "--list", "-l", help="List archived habits"),
):
    """Archive a habit (keeps history, hides from daily view)"""
    cmd_archive(args or [], show_list=list_archived)


@app.command()
def habits():
    """Show all habits and their checked off list for the last 7 days."""
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
    """Health check — untagged tasks, overdue, habit streaks, jaynice signal"""
    cmd_status()


@app.command()
def stats():
    """Feedback-loop metrics and escalation signals"""
    cmd_stats()


@app.command()
def backup():
    """Create database backup"""
    cmd_backup()


@app.command()
def momentum():
    """Show momentum and weekly trends"""
    cmd_momentum()


@app.command(name="defer")
def defer_cmd(
    args: list[str] = typer.Argument(..., help="Task to defer (fuzzy)"),
    reason: str = typer.Option(..., "--reason", "--why", help="Why are you deferring this?"),
):
    """Defer a task with a required reason"""
    cmd_defer(args, reason)


@app.command(name="now")
def now_cmd(
    args: list[str] = typer.Argument(..., help="Task to schedule for right now"),
):
    """Set a task due today at the current time"""
    cmd_now(args)


@app.command(name="today")
def today_cmd(
    args: list[str] = typer.Argument(None, help="Partial task name to set due today"),
):
    """Set due date to today on a task (fuzzy match)"""
    cmd_today(args)


@app.command()
def tomorrow(
    args: list[str] = typer.Argument(None, help="Partial task name to set due tomorrow"),
):
    """Set due date to tomorrow on a task (fuzzy match)"""
    cmd_tomorrow(args)


@app.command()
def schedule(
    args: list[str] = typer.Argument(..., help="HH:MM and task name, or task name with -r"),
    remove: bool = typer.Option(False, "-r", "--remove", help="Clear scheduled time"),
):
    """Set or clear scheduled time on a task (fuzzy match)"""
    cmd_schedule(args, remove=remove)


@app.command(name="set")
def set_cmd(
    args: list[str] = typer.Argument(..., help="Task to modify (fuzzy match)"),
    parent: str = typer.Option(None, "--parent", "-p", help="Set parent task (fuzzy match)"),
    content: str = typer.Option(None, "--content", "-c", help="Rename task"),
):
    """Set parent or content on an existing task"""
    cmd_set(args, parent=parent, content=content)


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


@app.command()
def steward():
    """Print autonomous Steward boot prompt"""
    cmd_steward()


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


def main():
    db.init()
    app()


if __name__ == "__main__":
    main()
