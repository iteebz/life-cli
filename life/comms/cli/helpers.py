"""Shared CLI helpers."""

import typer

from life.comms import accounts as accts_module


def run_service(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        typer.echo(str(exc))
        raise typer.Exit(1) from None


def get_signal_phone(phone: str | None) -> str:
    if phone:
        return phone
    accounts = accts_module.list_accounts("messaging")
    signal_accounts = [account for account in accounts if account["provider"] == "signal"]
    if not signal_accounts:
        typer.echo("No Signal accounts linked. Run: comms link signal")
        raise typer.Exit(1)
    return signal_accounts[0]["email"]
