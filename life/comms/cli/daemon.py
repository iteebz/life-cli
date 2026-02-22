"""Daemon and agent management commands."""

import typer

app = typer.Typer()


@app.command()
def agent_authorize(phone: str = typer.Argument(..., help="Phone number to authorize")) -> None:
    """Authorize a phone number to send commands"""
    from .. import agent

    agent.add_authorized_sender(phone)
    typer.echo(f"Authorized: {phone}")


@app.command()
def agent_revoke(phone: str = typer.Argument(..., help="Phone number to revoke")) -> None:
    """Revoke command authorization from a phone number"""
    from .. import agent

    if agent.remove_authorized_sender(phone):
        typer.echo(f"Revoked: {phone}")
    else:
        typer.echo(f"Not authorized: {phone}")


@app.command()
def agent_list() -> None:
    """List authorized command senders"""
    from .. import agent

    authorized_senders = agent.get_authorized_senders()
    if not authorized_senders:
        typer.echo("No authorized senders (all senders allowed)")
        return

    typer.echo("Authorized senders:")
    for sender in sorted(authorized_senders):
        typer.echo(f"  {sender}")


@app.command()
def agent_config(
    enable: bool | None = typer.Option(None, "--enable/--disable", help="Enable or disable agent"),
    nlp: bool | None = typer.Option(None, "--nlp/--no-nlp", help="Enable natural language parsing"),
) -> None:
    """Configure agent settings"""
    from life.comms.config import get_agent_config, set_agent_config

    config = get_agent_config()

    if enable is not None:
        config["enabled"] = enable
    if nlp is not None:
        config["nlp"] = nlp

    set_agent_config(config)

    typer.echo(f"Agent: {'enabled' if config.get('enabled', True) else 'disabled'}")
    typer.echo(f"NLP: {'enabled' if config.get('nlp', False) else 'disabled'}")


@app.command()
def daemon_start(
    interval: int = typer.Option(5, "--interval", "-i", help="Polling interval in seconds"),
    foreground: bool = typer.Option(False, "--foreground", "-f", help="Run in foreground"),
) -> None:
    """Start Signal daemon (background polling)"""
    from life.comms import daemon

    success, status_msg = daemon.start(interval=interval, foreground=foreground)
    typer.echo(status_msg)
    if not success:
        raise typer.Exit(1)


@app.command()
def daemon_stop() -> None:
    """Stop Signal daemon"""
    from life.comms import daemon

    success, status_msg = daemon.stop()
    typer.echo(status_msg)
    if not success:
        raise typer.Exit(1)


@app.command()
def daemon_status() -> None:
    """Show daemon status"""
    from life.comms import daemon, launchd

    daemon_info = daemon.status()
    launchd_info = launchd.status()

    if launchd_info["installed"]:
        typer.echo(
            f"Launchd: {'running' if launchd_info['running'] else 'installed but not running'}"
        )
    elif daemon_info["running"]:
        typer.echo(f"Running (PID {daemon_info['pid']})")
        typer.echo(f"Accounts: {', '.join(daemon_info['accounts'])}")
    else:
        typer.echo("Not running")

    if daemon_info.get("last_log"):
        typer.echo("\nRecent log:")
        for line in daemon_info["last_log"]:
            typer.echo(f"  {line}")


@app.command()
def daemon_install(
    interval: int = typer.Option(5, "--interval", "-i", help="Polling interval"),
) -> None:
    """Install daemon as launchd service (auto-start on boot)"""
    from life.comms import launchd

    success, status_msg = launchd.install(interval=interval)
    typer.echo(status_msg)
    if not success:
        raise typer.Exit(1)


@app.command()
def daemon_uninstall() -> None:
    """Uninstall daemon launchd service"""
    from life.comms import launchd

    success, status_msg = launchd.uninstall()
    typer.echo(status_msg)
    if not success:
        raise typer.Exit(1)
