import typer


def exit_error(message: str, code: int = 1) -> None:
    """Print error and exit."""
    typer.echo(message, err=True)
    raise typer.Exit(code)
