import typer

from life.lib.claude import invoke as invoke_claude

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def pepper(message: str = typer.Argument(..., help="The message to send to the Pepper persona.")):
    """Invoke the Pepper persona."""
    invoke_claude(message, "pepper")
