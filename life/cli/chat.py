import typer

from ..lib.claude import invoke as invoke_claude
from ..ops.personas import get_default_persona_name

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def chat(
    args: list[str] = typer.Argument(None, help="Message to send to agent"),  # noqa: B008
    persona: str = typer.Option(None, help="Persona to use (roast, pepper, kim)"),  # noqa: B008
):
    """Chat with ephemeral agent."""
    message = " ".join(args) if args else ""
    if not message:
        typer.echo("Error: message required")
        raise typer.Exit(1)
    default_persona = "roast"
    selected_persona = persona or get_default_persona_name() or default_persona
    invoke_claude(message, selected_persona)
