import typer

from ..lib.render import render_dashboard

cmd = typer.Typer(help="Show dashboard summary.")


@cmd.callback(invoke_without_command=True)
def dashboard():
    """Show dashboard summary."""
    typer.echo(render_dashboard())
