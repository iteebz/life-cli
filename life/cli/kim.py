import typer

from life.lib.claude import invoke as invoke_claude

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def kim(message: str = typer.Argument(..., help="The message to send to the Kim persona.")):
    """Invoke the Kim persona."""
    invoke_claude(message, "kim")
