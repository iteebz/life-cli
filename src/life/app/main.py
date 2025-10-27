import sys

import typer

from ..config import get_context
from ..core.item import (
    get_pending_items,
    get_today_completed,
)
from .commands import maybe_spawn_persona, register_commands
from .render import render_dashboard

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Ephemeral life agent"""
    if ctx.invoked_subcommand is None:
        from ..lib.store import get_momentum_7d, get_today_breakdown

        items = get_pending_items()
        life_context = get_context()
        today_items = get_today_completed()
        today_breakdown = get_today_breakdown()
        momentum_7d = get_momentum_7d()
        typer.echo(render_dashboard(items, today_breakdown, momentum_7d, life_context, today_items))


register_commands(app)


def main_with_personas():
    """Wrapper that checks for personas before passing to typer."""
    if maybe_spawn_persona():
        sys.exit(0)
    app()


if __name__ == "__main__":
    main_with_personas()
