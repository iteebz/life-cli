import typer

from ..api import get_pending_items, get_today_breakdown, get_today_completed
from ..lib.ansi import ANSI
from ..lib.render import render_dashboard

cmd = typer.Typer(help="Show dashboard summary.")

@cmd.callback(invoke_without_command=True)
def dashboard():
    """Show dashboard summary."""
    typer.echo(render_dashboard())