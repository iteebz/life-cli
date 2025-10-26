import typer

from ...config import backup

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def backup_cmd(ctx: typer.Context):
    """Create database backup"""
    if ctx.invoked_subcommand is not None:
        return
    typer.echo(backup())
