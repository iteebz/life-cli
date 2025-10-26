import typer

from ...config import get_or_set_profile

cmd = typer.Typer()


@cmd.command()
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or update your profile"""
    typer.echo(get_or_set_profile(profile_text))
