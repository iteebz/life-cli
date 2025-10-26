import typer

from ...lib.match import complete, uncomplete

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def done(
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    undo: bool = typer.Option(False, "-u", "--undo", "-r", "--remove", help="Undo item completion"),  # noqa: B008
):
    """Mark item complete or undo completion (fuzzy match)"""
    partial = " ".join(args) if args else ""
    if not partial:
        typer.echo("No item specified")
        return

    op = uncomplete if undo else complete
    result = op(partial)

    if result:
        typer.echo(f"✓ {result}")
    else:
        typer.echo(f"No match for: {partial}")
