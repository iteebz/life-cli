import typer

from ...config import get_or_set_context

cmd = typer.Typer()


@cmd.command()
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),  # noqa: B008
):
    """View or update your context"""
    typer.echo(get_or_set_context(context_text))
