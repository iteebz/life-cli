"""Account management commands."""

import typer

from comms import accounts as accts_module
from comms.adapters.email import gmail, outlook
from comms.adapters.messaging import signal

app = typer.Typer()


@app.command()
def link(
    provider: str = typer.Argument(..., help="Provider: gmail, outlook, signal"),
    identifier: str = typer.Argument(
        None, help="Email or phone number (e.g., +1234567890 for Signal)"
    ),
    client_id: str = typer.Option(None, "--client-id", help="OAuth Client ID (Outlook)"),
    client_secret: str = typer.Option(
        None, "--client-secret", help="OAuth Client Secret (Outlook)"
    ),
) -> None:
    """Link email or messaging account"""
    if provider not in ["gmail", "outlook", "signal"]:
        typer.echo(f"Unknown provider: {provider}")
        raise typer.Exit(1)

    if provider == "signal":
        typer.echo("Linking Signal as secondary device...")
        typer.echo("Open Signal on your phone -> Settings -> Linked Devices -> Link New Device")
        typer.echo("Then scan the QR code that will appear.")
        success, error_msg = signal.link("comms-cli")
        if not success:
            typer.echo(f"Link failed: {error_msg}")
            raise typer.Exit(1)

        accounts = signal.list_accounts()
        if not accounts:
            typer.echo("No accounts found after linking")
            raise typer.Exit(1)

        phone = accounts[0]
        account_id = accts_module.add_messaging_account("signal", phone)
        typer.echo(f"Linked Signal: {phone}")
        typer.echo(f"Account ID: {account_id}")
        return

    email = identifier
    account_id: str = ""
    if provider == "gmail":
        try:
            email = gmail.init_oauth()
            typer.echo(f"OAuth completed: {email}")
        except Exception as e:
            typer.echo(f"OAuth failed: {e}")
            raise typer.Exit(1) from None

        account_id = accts_module.add_email_account(provider, email)
        success, error_msg = gmail.test_connection(account_id, email)
        if not success:
            typer.echo(f"Failed to connect: {error_msg}")
            raise typer.Exit(1)

    elif provider == "outlook":
        if not email:
            typer.echo("Outlook requires email address")
            raise typer.Exit(1)

        if not client_id or not client_secret:
            typer.echo("Outlook requires --client-id and --client-secret")
            typer.echo(
                "Get them from: https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps"
            )
            raise typer.Exit(1)

        account_id = accts_module.add_email_account(provider, email)
        outlook.store_credentials(email, client_id, client_secret)
        success, error_msg = outlook.test_connection(account_id, email, client_id, client_secret)
        if not success:
            typer.echo(f"Failed to connect: {error_msg}")
            raise typer.Exit(1)

    typer.echo(f"Linked {provider}: {email}")
    typer.echo(f"Account ID: {account_id}")


@app.command()
def accounts() -> None:
    """List all accounts"""
    accts = accts_module.list_accounts()
    if not accts:
        typer.echo("No accounts configured")
        return

    for account in accts:
        status = "✓" if account["enabled"] else "✗"
        typer.echo(f"{status} {account['provider']:10} {account['email']:30} {account['id'][:8]}")


@app.command()
def unlink(account_id: str) -> None:
    """Unlink account by ID or email"""
    accounts = accts_module.list_accounts()
    matching = [
        account
        for account in accounts
        if account["id"].startswith(account_id) or account["email"] == account_id
    ]

    if not matching:
        typer.echo(f"No account found matching: {account_id}")
        raise typer.Exit(1)

    if len(matching) > 1:
        typer.echo(f"Multiple accounts match '{account_id}':")
        for account in matching:
            typer.echo(f"  {account['id'][:8]} {account['provider']} {account['email']}")
        raise typer.Exit(1)

    account = matching[0]
    if accts_module.remove_account(account["id"]):
        typer.echo(f"Unlinked {account['provider']}: {account['email']}")
    else:
        typer.echo("Failed to unlink account")
        raise typer.Exit(1)
