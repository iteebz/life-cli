"""CLI package — modular command groups."""

import typer

from comms import db

from .accounts import app as accounts_app
from .daemon import app as daemon_app
from .drafts import app as drafts_app
from .email import app as email_app
from .proposals import app as proposals_app
from .signal import app as signal_app
from .system import app as system_app
from .system import show_dashboard

app = typer.Typer(
    name="comms",
    help="AI-managed comms for ADHD brains",
    no_args_is_help=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def _main_callback(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        show_dashboard()


app.add_typer(system_app, name="")
app.add_typer(accounts_app, name="")
app.add_typer(email_app, name="")
app.add_typer(drafts_app, name="")
app.add_typer(signal_app, name="")
app.add_typer(daemon_app, name="")
app.add_typer(proposals_app, name="")


def main() -> None:
    db.init()
    app()


if __name__ == "__main__":
    main()
