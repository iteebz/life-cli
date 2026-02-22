"""Email thread commands."""

import typer

from comms import audit, services

from .helpers import run_service

app = typer.Typer()


@app.command()
def threads(
    label: str = typer.Option(
        "inbox", "--label", "-l", help="Label filter: inbox, unread, archive, trash, starred, sent"
    ),
) -> None:
    """List threads from all accounts"""
    for entry in services.list_threads(label):
        account = entry["account"]
        thread_list = entry["threads"]
        typer.echo(f"\n{account['email']} ({label}):")

        if not thread_list:
            typer.echo("  No threads")
            continue

        for thread in thread_list:
            date_str = thread.get("date", "")[:16]
            typer.echo(f"  {thread['id'][:8]} | {date_str:16} | {thread['snippet'][:50]}")


@app.command()
def thread(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Fetch and display full thread"""
    full_id = run_service(services.resolve_thread_id, thread_id, email) or thread_id
    thread_messages = run_service(services.fetch_thread, full_id, email)

    typer.echo(f"\nThread: {thread_messages[0]['subject']}")
    typer.echo("=" * 80)

    for message in thread_messages:
        typer.echo(f"\nFrom: {message['from']}")
        typer.echo(f"Date: {message['date']}")
        typer.echo(f"\n{message['body']}\n")
        typer.echo("-" * 80)


@app.command()
def summarize(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Summarize thread using Claude"""
    from comms import claude

    full_id = run_service(services.resolve_thread_id, thread_id, email) or thread_id
    thread_messages = run_service(services.fetch_thread, full_id, email)

    typer.echo(f"Summarizing {len(thread_messages)} messages...")
    summary = claude.summarize_thread(thread_messages)
    typer.echo(f"\n{summary}")


@app.command()
def snooze(
    thread_id: str,
    until: str = typer.Option(
        "tomorrow", "--until", "-u", help="When to resurface: tomorrow, monday, 2d, 4h"
    ),
    email: str = typer.Option(None, "--email", "-e"),
) -> None:
    """Snooze thread until later"""
    from comms import snooze as snooze_module

    full_id = run_service(services.resolve_thread_id, thread_id, email) or thread_id
    _, snooze_until = snooze_module.snooze_item(
        entity_type="thread",
        entity_id=full_id,
        until=until,
        source_id=email,
    )
    typer.echo(f"Snoozed until {snooze_until.strftime('%Y-%m-%d %H:%M')}")


@app.command()
def snoozed() -> None:
    """List snoozed threads"""
    from comms import snooze as snooze_module

    items = snooze_module.get_snoozed_items()
    if not items:
        typer.echo("No snoozed items")
        return

    for item in items:
        until = item["snooze_until"][:16]
        typer.echo(
            f"  {item['id'][:8]} | {until} | {item['entity_id'][:8]} | {item.get('reason') or ''}"
        )


@app.command()
def archive(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Archive thread (remove from inbox)"""
    run_service(services.thread_action, "archive", thread_id, email)
    typer.echo(f"Archived thread: {thread_id}")
    audit.log("archive", "thread", thread_id, {"reason": "manual"})


@app.command()
def delete(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Delete thread (move to trash)"""
    run_service(services.thread_action, "delete", thread_id, email)
    typer.echo(f"Deleted thread: {thread_id}")
    audit.log("delete", "thread", thread_id, {"reason": "manual"})


@app.command()
def flag(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Flag thread (star it)"""
    _thread_action(thread_id, "flag", email)


@app.command()
def unflag(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Unflag thread (unstar it)"""
    _thread_action(thread_id, "unflag", email)


@app.command()
def unarchive(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Unarchive thread (restore to inbox)"""
    _thread_action(thread_id, "unarchive", email)


@app.command()
def undelete(thread_id: str, email: str = typer.Option(None, "--email", "-e")) -> None:
    """Undelete thread (restore from trash)"""
    _thread_action(thread_id, "undelete", email)


def _thread_action(thread_id: str, action_name: str, email: str | None = None) -> None:
    run_service(services.thread_action, action_name, thread_id, email)
    past_tense = f"{action_name}ged" if action_name.endswith("flag") else f"{action_name}d"
    typer.echo(f"{past_tense.capitalize()} thread: {thread_id}")
    audit.log(action_name, "thread", thread_id, {"reason": "manual"})
