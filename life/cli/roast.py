import typer

from life.lib.claude import invoke as invoke_claude

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def roast(message: str = typer.Argument(..., help="The message to send to the Roast persona.")):
    """Invoke the Roast persona."""
    invoke_claude(message, "roast")
