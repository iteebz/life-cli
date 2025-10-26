import sys

import typer

from ..config import get_context
from ..core.item import (
    get_pending_items,
    get_today_completed,
    today_completed,
    weekly_momentum,
)
from .commands import maybe_spawn_persona, register_commands
from .render import render_dashboard

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        items = get_pending_items()
        today_count = today_completed()
        momentum = weekly_momentum()
        life_context = get_context()
        today_items = get_today_completed()
        typer.echo(render_dashboard(items, today_count, momentum, life_context, today_items))


register_commands(app)


def main_with_personas():
    """Wrapper that checks for personas before passing to typer."""
    if maybe_spawn_persona():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_personas()
