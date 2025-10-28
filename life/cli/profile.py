import typer

from ..config import get_profile, set_profile

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def profile(
    profile_text: str = typer.Argument(None, help="Profile to set"),  # noqa: B008
):
    """View or set personal profile"""
    if profile_text:
        set_profile(profile_text)
        typer.echo(f"Profile set to: {profile_text}")
    else:
        current = get_profile()
        typer.echo(current if current else "No profile set")
