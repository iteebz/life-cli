"""Signal messaging commands."""

from datetime import datetime

import typer

from comms.adapters.messaging import signal as signal_module

from .helpers import get_signal_phone

app = typer.Typer()


@app.command()
def messages(
    phone: str = typer.Option(None, "--phone", "-p", help="Signal phone number"),
    timeout: int = typer.Option(5, "--timeout", "-t", help="Receive timeout in seconds"),
) -> None:
    """Receive new Signal messages and store them"""
    phone = get_signal_phone(phone)

    typer.echo(f"Receiving messages for {phone}...")
    new_messages = signal_module.receive(phone, timeout=timeout)

    if new_messages:
        typer.echo(f"Received {len(new_messages)} new message(s)")
        for message in new_messages:
            sender = message.get("from_name") or message.get("from", "Unknown")
            body = message.get("body", "")
            typer.echo(f"  {sender}: {body}")
    else:
        typer.echo("No new messages")


@app.command()
def signal_inbox(
    phone: str = typer.Option(None, "--phone", "-p"),
) -> None:
    """Show Signal conversations"""
    phone = get_signal_phone(phone)

    conversations = signal_module.get_conversations(phone)
    if not conversations:
        typer.echo("No conversations yet. Run: comms messages")
        return

    for conversation in conversations:
        name = conversation["sender_name"] or conversation["sender_phone"]
        unread = conversation["unread_count"]
        count = conversation["message_count"]
        unread_str = f" ({unread} unread)" if unread else ""
        typer.echo(f"{conversation['sender_phone']:16} | {name:20} | {count} msgs{unread_str}")


@app.command()
def signal_history(
    contact: str = typer.Argument(..., help="Phone number to view history with"),
    phone: str = typer.Option(None, "--phone", "-p"),
    limit: int = typer.Option(20, "--limit", "-n"),
) -> None:
    """Show message history with a contact"""
    phone = get_signal_phone(phone)

    history_messages = signal_module.get_messages(phone=phone, sender=contact, limit=limit)
    if not history_messages:
        typer.echo(f"No messages from {contact}")
        return

    history_messages.reverse()
    for message in history_messages:
        sender = message["sender_name"] or message["sender_phone"]
        timestamp = datetime.fromtimestamp(message["timestamp"] / 1000).strftime("%m-%d %H:%M")
        message_id = message["id"][:8] if message.get("id") else ""
        typer.echo(f"{message_id} [{timestamp}] {sender}: {message['body']}")


@app.command()
def signal_send(
    recipient: str = typer.Argument(..., help="Phone number or group ID"),
    message: str = typer.Option(..., "--message", "-m", help="Message to send"),
    phone: str = typer.Option(None, "--phone", "-p"),
    group: bool = typer.Option(False, "--group", "-g", help="Send to group"),
    attachment: str = typer.Option(None, "--attachment", "-a", help="Path to attachment"),
) -> None:
    """Send Signal message"""
    phone = get_signal_phone(phone)

    if group:
        success, error_msg = signal_module.send_group(phone, recipient, message)
    else:
        success, error_msg = signal_module.send(phone, recipient, message, attachment=attachment)

    if success:
        typer.echo(f"Sent to {recipient}")
    else:
        typer.echo(f"Failed: {error_msg}")
        raise typer.Exit(1)


@app.command()
def signal_reply(
    message_id: str = typer.Argument(..., help="Message ID to reply to"),
    message: str = typer.Option(..., "--message", "-m", help="Reply message"),
    phone: str = typer.Option(None, "--phone", "-p"),
) -> None:
    """Reply to a Signal message"""
    phone = get_signal_phone(phone)

    success, error_msg, original_message = signal_module.reply(phone, message_id, message)

    if success and original_message:
        sender = original_message["sender_name"] or original_message["sender_phone"]
        typer.echo(f"Replied to {sender}")
        typer.echo(f"  Original: {original_message['body'][:50]}...")
    else:
        typer.echo(f"Failed: {error_msg}")
        raise typer.Exit(1)


@app.command()
def signal_draft(
    contact: str = typer.Argument(..., help="Phone number to reply to"),
    instructions: str = typer.Option(None, "--instructions", "-i", help="Instructions for Claude"),
    phone: str = typer.Option(None, "--phone", "-p"),
) -> None:
    """Generate Signal reply using Claude"""
    from .. import claude

    phone = get_signal_phone(phone)
    conversation_history = signal_module.get_messages(phone=phone, sender=contact, limit=10)

    if not conversation_history:
        typer.echo(f"No messages from {contact}")
        raise typer.Exit(1)

    typer.echo("Generating reply...")
    reply_body, reasoning = claude.generate_signal_reply(conversation_history, instructions)

    if not reply_body:
        typer.echo(f"Failed: {reasoning}")
        raise typer.Exit(1)

    typer.echo(f"\nReasoning: {reasoning}")
    typer.echo(f"\nDraft reply to {contact}:")
    typer.echo(f"  {reply_body}\n")

    if typer.confirm("Send this reply?"):
        success, error_msg = signal_module.send(phone, contact, reply_body)
        if success:
            typer.echo("Sent!")
        else:
            typer.echo(f"Failed: {error_msg}")
            raise typer.Exit(1)


@app.command()
def signal_contacts(phone: str = typer.Option(None, "--phone", "-p")) -> None:
    """List Signal contacts"""
    phone = get_signal_phone(phone)
    contacts = signal_module.list_contacts(phone)
    if not contacts:
        typer.echo("No contacts")
        return

    for contact in contacts:
        name = contact.get("name", "")
        number = contact.get("number", "")
        typer.echo(f"{number:20} {name}")


@app.command()
def signal_groups(phone: str = typer.Option(None, "--phone", "-p")) -> None:
    """List Signal groups"""
    phone = get_signal_phone(phone)
    groups = signal_module.list_groups(phone)
    if not groups:
        typer.echo("No groups")
        return

    for group in groups:
        typer.echo(f"{group.get('id', '')[:16]} | {group.get('name', '')}")


@app.command()
def signal_status() -> None:
    """Check Signal connection status"""
    accounts = signal_module.list_accounts()
    if not accounts:
        typer.echo("No Signal accounts registered with signal-cli")
        typer.echo("Run: comms link signal")
        return

    for phone in accounts:
        success, error_msg = signal_module.test_connection(phone)
        status = "OK" if success else f"FAIL: {error_msg}"
        typer.echo(f"{phone}: {status}")
