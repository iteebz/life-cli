import typer

from ...lib.ops import remove

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def rm(
    ctx: typer.Context,
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
):
    """Delete item or completed task (fuzzy match)"""
    if ctx.invoked_subcommand is not None:
        return
    if not args:
        typer.echo("Usage: life rm <item>")
        raise typer.Exit(1)
    partial = " ".join(args)
    result = remove(partial)
    typer.echo(f"Removed: {result}" if result else f"No match for: {partial}")
