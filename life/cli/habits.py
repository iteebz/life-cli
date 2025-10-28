import typer

from ..lib.render import render_habit_matrix

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def habits():
    """Show all habits and their checked off list for the last 7 days."""
    typer.echo(render_habit_matrix())
