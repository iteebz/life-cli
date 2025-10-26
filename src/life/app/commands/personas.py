import typer

from ...personas import manage_personas

cmd = typer.Typer()


@cmd.command()
def personas(
    name: str = typer.Argument(None, help="Persona name (roast, pepper, kim)"),  # noqa: B008
    set: bool = typer.Option(False, "-s", "--set", help="Set as default persona"),  # noqa: B008
    prompt: bool = typer.Option(False, "-p", "--prompt", help="Show full ephemeral prompt"),  # noqa: B008
):
    """Show available personas or view/set a specific persona"""
    try:
        typer.echo(manage_personas(name, set_default=set, show_prompt=prompt))
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None  # noqa: B904
