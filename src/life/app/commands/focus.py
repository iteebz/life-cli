import typer

from ...app.render import render_focus_items
from ...lib.claude import invoke as invoke_claude
from ...lib.ops import toggle
from ...lib.store import get_focus_items

cmd = typer.Typer()


@cmd.callback(invoke_without_command=True)
def focus(
    args: list[str] = typer.Argument(  # noqa: B008
        None, help="Item content for fuzzy matching or 'list' to show focus items"
    ),
):
    """Toggle focus status on item (fuzzy match) or list focus items"""
    if not args:
        items = get_focus_items()
        typer.echo(render_focus_items(items))
        return

    first_arg = args[0].lower()
    valid_personas = {"roast", "pepper", "kim"}

    if first_arg in valid_personas and len(args) > 1:
        persona = first_arg
        focus_items = get_focus_items()
        focus_list = render_focus_items(focus_items)
        message = f"{' '.join(args[1:])} Here are my focus items:\n{focus_list}"
        invoke_claude(message, persona)
    elif first_arg in ("list", "--list", "-l"):
        items = get_focus_items()
        typer.echo(render_focus_items(items))
    else:
        partial = " ".join(args)
        result = toggle(partial)
        if result is None:
            typer.echo(f"Cannot focus habits/chores: {partial}")
        else:
            status, content = result
            typer.echo(f"{status}: {content}")
