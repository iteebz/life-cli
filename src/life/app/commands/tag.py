import typer

from ...core.tag import manage_tag

cmd = typer.Typer()


@cmd.command()
def tag(
    tag_name: str = typer.Argument(..., help="Tag name"),  # noqa: B008
    args: list[str] = typer.Argument(None, help="Item content for fuzzy matching"),  # noqa: B008
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove tag instead of adding"),  # noqa: B008
):
    """Add/remove tag to/from item (fuzzy match), or view items by tag"""
    typer.echo(manage_tag(tag_name, " ".join(args) if args else None, remove=remove))
