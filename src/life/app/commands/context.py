import typer

from ...config import get_or_set_context

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),  # noqa: B008
):
    """View or set current context"""
    typer.echo(get_or_set_context(context_text))
