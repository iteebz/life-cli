import typer

from . import db
from .commands import (
    cmd_backup,
    cmd_block,
    cmd_dashboard,
    cmd_dates,
    cmd_done,
    cmd_due,
    cmd_focus,
    cmd_habit,
    cmd_habits,
    cmd_list,
    cmd_momentum,
    cmd_profile,
    cmd_rename,
    cmd_rm,
    cmd_schedule,
    cmd_stats,
    cmd_status,
    cmd_steward,
    cmd_tag,
    cmd_task,
    cmd_today,
    cmd_tomorrow,
    cmd_track,
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
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Show IDs"),  # noqa: B008
):
    """Life dashboard"""
    if ctx.invoked_subcommand is None:
        cmd_dashboard(verbose=verbose)


@app.command()
def task(
    content_args: list[str] = typer.Argument(..., help="Task content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set task as focused"),  # noqa: B008
    due: str = typer.Option(
        None, "--due", "-d", help="Set due date (today, tomorrow, mon, YYYY-MM-DD)"
    ),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to task"),  # noqa: B008
    under: str = typer.Option(None, "--under", "-u", help="Parent task (fuzzy match)"),  # noqa: B008
):
    """Add task (supports focus, due date, tags, immediate completion)"""
    cmd_task(content_args, focus=focus, due=due, tags=tags, under=under)


@app.command()
def habit(
    content_args: list[str] = typer.Argument(..., help="Habit content"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    cmd_habit(content_args, tags=tags)


@app.command()
def done(
    args: list[str] = typer.Argument(..., help="Partial match for the item to mark done/undone"),  # noqa: B008
):
    """Mark task/habit as done or undone."""
    cmd_done(args)


@app.command()
def rm(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    cmd_rm(args)


@app.command()
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus status on task (fuzzy match)"""
    cmd_focus(args)


@app.command()
def due(
    args: list[str] = typer.Argument(..., help="Due date (YYYY-MM-DD) and item content"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Remove due date"),  # noqa: B008
):
    """Set or remove due date on item (fuzzy match)"""
    cmd_due(args, remove=remove)


@app.command()
def rename(
    from_args: list[str] = typer.Argument(  # noqa: B008
        ..., help="Content to fuzzy match for the item to rename"
    ),
    to_content: str = typer.Argument(..., help="The exact new content for the item"),  # noqa: B008
):
    """Rename an item using fuzzy matching for 'from' and exact match for 'to'"""
    cmd_rename(from_args, to_content)


@app.command()
def tag(
    tag_name: str | None = typer.Argument(None, help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    tag_opt: str | None = typer.Option(None, "--tag", "-t", help="Tag name (option form)"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
):
    """Add or remove tag on item (fuzzy match)"""
    cmd_tag(tag_name, args, tag_opt=tag_opt, remove=remove)


@app.command()
def habits():
    """Show all habits and their checked off list for the last 7 days."""
    cmd_habits()


@app.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or set personal profile"""
    cmd_profile(profile_text)


@app.command()
def dates(
    action: str = typer.Argument(None, help="add, remove, or list"),  # noqa: B008
    name: str = typer.Argument(None, help="Date name"),  # noqa: B008
    date_str: str = typer.Argument(None, help="Target date (YYYY-MM-DD)"),  # noqa: B008
    emoji: str = typer.Option("📌", "-e", "--emoji", help="Emoji for date"),  # noqa: B008
):
    """Add, remove, or list dates to track"""
    cmd_dates(action, name, date_str, emoji)


@app.command(name="list")
def list_cmd():
    """List all pending tasks and habits"""
    cmd_list()


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


@app.command(name="today")
def today_cmd(
    args: list[str] = typer.Argument(None, help="Partial task name to set due today"),  # noqa: B008
):
    """Set due date to today on a task (fuzzy match)"""
    cmd_today(args)


@app.command()
def tomorrow(
    args: list[str] = typer.Argument(None, help="Partial task name to set due tomorrow"),  # noqa: B008
):
    """Set due date to tomorrow on a task (fuzzy match)"""
    cmd_tomorrow(args)


@app.command()
def schedule(
    args: list[str] = typer.Argument(..., help="HH:MM and task name, or task name with -r"),  # noqa: B008
    remove: bool = typer.Option(False, "-r", "--remove", help="Clear scheduled time"),  # noqa: B008
):
    """Set or clear scheduled time on a task (fuzzy match)"""
    cmd_schedule(args, remove=remove)


@app.command()
def block(
    blocked: list[str] = typer.Argument(..., help="Task to mark as blocked (fuzzy)"),  # noqa: B008
    blocker: list[str] = typer.Option(..., "--by", "-b", help="Task that is blocking (fuzzy)"),  # noqa: B008
):
    """Mark a task as blocked by another task"""
    cmd_block(blocked, blocker)


@app.command()
def unblock(
    args: list[str] = typer.Argument(..., help="Task to unblock (fuzzy)"),  # noqa: B008
):
    """Clear blocked_by on a task"""
    cmd_unblock(args)


@app.command()
def steward():
    """Print autonomous Steward boot prompt"""
    cmd_steward()


@app.command()
def track(
    description: list[str] = typer.Argument(None, help="Intervention description"),  # noqa: B008
    won: bool = typer.Option(False, "--won", "-w", help="Mark as won"),  # noqa: B008
    lost: bool = typer.Option(False, "--lost", "-l", help="Mark as lost"),  # noqa: B008
    deferred: bool = typer.Option(False, "--deferred", "-d", help="Mark as deferred"),  # noqa: B008
    note: str = typer.Option(None, "--note", "-n", help="Optional note"),  # noqa: B008
    stats: bool = typer.Option(False, "--stats", "-s", help="Show intervention stats"),  # noqa: B008
    log: bool = typer.Option(False, "--log", help="Show recent interventions"),  # noqa: B008
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
