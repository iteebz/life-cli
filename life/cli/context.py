import typer

from ..config import get_context, set_context

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def context(
    context_text: str = typer.Argument(None, help="Context text to set"),  # noqa: B008
):
    """View or set current context"""
    if context_text:
        set_context(context_text)
        typer.echo(f"Context set to: {context_text}")
    else:
        typer.echo(get_context())
