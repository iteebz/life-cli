import typer

from ..ops.toggle import toggle_focus

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def focus(
    args: list[str] = typer.Argument(  # noqa: B008
        None, help="Item content for fuzzy matching or 'list' to show focus items"
    ),
):
    """Toggle focus status on item (fuzzy match) or list focus items"""
    if not args:
        # items = get_focus_items()
        # typer.echo(render_focus_items(items))
        typer.echo(
            "No arguments provided. Use 'list' to show focus items or provide an item to toggle focus."
        )
        return

    first_arg = args[0].lower()
    valid_personas = {"roast", "pepper", "kim"}

    if first_arg in valid_personas and len(args) > 1:
        persona = first_arg
        # focus_items = get_focus_items()
        # focus_list = render_focus_items(focus_items)
        # message = f"{' '.join(args[1:])} Here are my focus items:\n{focus_list}"
        # invoke_claude(message, persona)
        typer.echo(f"Persona command for {persona} not yet implemented with new focus logic.")
    elif first_arg in ("list", "--list", "-l"):
        # items = get_focus_items()
        # typer.echo(render_focus_items(items))
        typer.echo("Listing focus items not yet implemented with new focus logic.")
    else:
        partial = " ".join(args)
        status_text, content = toggle_focus(partial)
        if status_text is None:
            typer.echo(f"Error: Item not found for '{partial}'")
            raise typer.Exit(code=1)
        typer.echo(f"{status_text}: {content}")
