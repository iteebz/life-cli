from typer.testing import CliRunner

from life.api import add_item
from life.cli.focus import cmd

runner = CliRunner()


def test_focus_list_empty(tmp_life_dir):
    result = runner.invoke(cmd, [])

    assert result.exit_code == 0


def test_focus_list_shows_focused(tmp_life_dir):
    add_item("focused task", focus=True)

    result = runner.invoke(cmd, [])

    assert result.exit_code == 0


def test_focus_toggle_on_task(tmp_life_dir):
    add_item("toggle me")

    result = runner.invoke(cmd, ["toggle"])

    assert result.exit_code == 0


def test_focus_list_arg(tmp_life_dir):
    add_item("focused item", focus=True)

    result = runner.invoke(cmd, ["list"])

    assert result.exit_code == 0
