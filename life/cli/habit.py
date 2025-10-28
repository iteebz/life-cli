import typer

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def habit(
    content: str = typer.Argument(..., help="Habit content"),  # noqa: B008
    focus: bool = typer.Option(False, "--focus", "-f", help="Set habit as focused"),  # noqa: B008
    tags: list[str] = typer.Option(None, "--tag", "-t", help="Add tags to habit"),  # noqa: B008
):
    """Add daily habit (auto-resets on completion)"""
    item_id = add_habit(
        content, focus=focus, tags=tags
    )
    typer.echo(f"Added habit: {content} {ANSI.GREY}{item_id}{ANSI.RESET}")
