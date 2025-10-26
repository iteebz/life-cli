import typer

from ...lib.match import toggle

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def focus(
    args: list[str] = typer.Argument(..., help="Item content for fuzzy matching"),  # noqa: B008
):
    """Toggle focus status on item (fuzzy match)"""
    partial = " ".join(args)
    result = toggle(partial)
    if result is None:
        typer.echo(f"Cannot focus habits/chores: {partial}")
    else:
        status, content = result
        typer.echo(f"{status}: {content}")
