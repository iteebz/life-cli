"""Draft commands: compose, reply, approve, send."""

import typer

from life.comms import drafts as drafts_module
from life.comms import policy, services

from .helpers import run_service

app = typer.Typer()


@app.command()
def drafts_list() -> None:
    """List pending drafts"""
    pending = drafts_module.list_pending_drafts()
    if not pending:
        typer.echo("No pending drafts")
        return

    for draft in pending:
        status = "✓ approved" if draft.approved_at else "⧗ pending"
        typer.echo(
            f"{draft.id[:8]} | {draft.to_addr} | {draft.subject or '(no subject)'} | {status}"
        )


@app.command()
def draft_show(draft_id: str) -> None:
    """Show draft details"""
    draft = drafts_module.get_draft(draft_id)
    if not draft:
        typer.echo(f"Draft {draft_id} not found")
        raise typer.Exit(1)

    typer.echo(f"To: {draft.to_addr}")
    if draft.cc_addr:
        typer.echo(f"Cc: {draft.cc_addr}")
    typer.echo(f"Subject: {draft.subject or '(no subject)'}")
    typer.echo(f"\n{draft.body}\n")

    if draft.claude_reasoning:
        typer.echo(f"--- Claude reasoning ---\n{draft.claude_reasoning}")

    typer.echo(f"\nCreated: {draft.created_at}")
    if draft.approved_at:
        typer.echo(f"Approved: {draft.approved_at}")
    if draft.sent_at:
        typer.echo(f"Sent: {draft.sent_at}")


@app.command()
def compose(
    to: str,
    subject: str = typer.Option(None, "--subject", "-s"),
    body: str = typer.Option(None, "--body", "-b"),
    cc: str = typer.Option(None, "--cc"),
    email: str = typer.Option(None, "--email", "-e"),
) -> None:
    """Compose new email draft"""
    if not body:
        typer.echo("Error: --body required")
        raise typer.Exit(1)

    draft_id, from_addr = run_service(
        services.compose_email_draft,
        to_addr=to,
        subject=subject,
        body=body,
        cc_addr=cc,
        email=email,
    )

    typer.echo(f"Created draft {draft_id[:8]}")
    typer.echo(f"From: {from_addr}")
    typer.echo(f"To: {to}")
    if cc:
        typer.echo(f"Cc: {cc}")
    typer.echo(f"Subject: {subject or '(no subject)'}")
    typer.echo(f"\nRun `comms approve {draft_id[:8]}` to approve for sending")


@app.command()
def approve_draft(draft_id: str) -> None:
    """Approve draft for sending"""
    full_id = drafts_module.resolve_draft_id(draft_id) or draft_id
    draft = drafts_module.get_draft(full_id)
    if not draft:
        typer.echo(f"Draft {draft_id} not found")
        raise typer.Exit(1)

    if draft.approved_at:
        typer.echo("Draft already approved")
        return

    allowed, error_msg = policy.check_recipient_allowed(draft.to_addr)
    if not allowed:
        typer.echo(f"Cannot approve draft: {error_msg}")
        raise typer.Exit(1)

    drafts_module.approve_draft(full_id)
    typer.echo(f"Approved draft {full_id[:8]}")
    typer.echo(f"\nRun `comms send {full_id[:8]}` to send")


@app.command()
def reply(
    thread_id: str,
    body: str = typer.Option(None, "--body", "-b"),
    email: str = typer.Option(None, "--email", "-e"),
    reply_all: bool = typer.Option(False, "--all", "-a", help="Reply to all recipients"),
) -> None:
    """Reply to thread"""
    if not body:
        typer.echo("Error: --body required")
        raise typer.Exit(1)

    draft_id, to_addr, reply_subject, cc_addr = run_service(
        services.reply_to_thread, thread_id=thread_id, body=body, email=email, reply_all=reply_all
    )

    typer.echo(f"Created reply draft {draft_id[:8]}")
    typer.echo(f"To: {to_addr}")
    if cc_addr:
        typer.echo(f"Cc: {cc_addr}")
    typer.echo(f"Subject: {reply_subject}")
    typer.echo(f"\nRun `comms approve {draft_id[:8]}` to approve for sending")


@app.command()
def draft_reply(
    thread_id: str,
    instructions: str = typer.Option(None, "--instructions", "-i", help="Instructions for Claude"),
    email: str = typer.Option(None, "--email", "-e"),
    reply_all: bool = typer.Option(False, "--all", "-a", help="Reply to all recipients"),
) -> None:
    """Generate reply draft using Claude"""
    from life.comms import claude

    full_id = run_service(services.resolve_thread_id, thread_id, email) or thread_id
    thread_messages = run_service(services.fetch_thread, full_id, email)

    context_lines = []
    for message in thread_messages[-5:]:
        context_lines.append(f"From: {message['from']}")
        context_lines.append(f"Date: {message['date']}")
        context_lines.append(f"Body: {message['body'][:500]}")
        context_lines.append("---")

    context = "\n".join(context_lines)

    typer.echo("Generating draft...")
    reply_body, reasoning = claude.generate_reply(context, instructions)

    if not reply_body:
        typer.echo(f"Failed: {reasoning}")
        raise typer.Exit(1)

    draft_id, to_addr, reply_subject, cc_addr = run_service(
        services.reply_to_thread,
        thread_id=full_id,
        body=reply_body,
        email=email,
        reply_all=reply_all,
    )

    typer.echo(f"\nReasoning: {reasoning}")
    typer.echo(f"\nDraft {draft_id[:8]}:")
    typer.echo(f"To: {to_addr}")
    if cc_addr:
        typer.echo(f"Cc: {cc_addr}")
    typer.echo(f"Subject: {reply_subject}")
    typer.echo(f"\n{reply_body}\n")
    typer.echo(f"Run `comms approve {draft_id[:8]}` to approve")


@app.command()
def send(draft_id: str) -> None:
    """Send approved draft"""
    full_id = drafts_module.resolve_draft_id(draft_id) or draft_id
    draft = drafts_module.get_draft(full_id)
    if not draft:
        typer.echo(f"Draft {draft_id} not found")
        raise typer.Exit(1)

    run_service(services.send_draft, full_id)
    typer.echo(f"Sent: {draft.to_addr}")
    typer.echo(f"Subject: {draft.subject}")
