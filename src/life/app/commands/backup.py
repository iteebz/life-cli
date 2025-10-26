import typer

from ...config import backup

cmd = typer.Typer()


@cmd.command()
def backup_cmd():
    """Backup database"""
    typer.echo(backup())
