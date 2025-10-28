from typer.testing import CliRunner

from life.cli.countdown import cmd

runner = CliRunner()


def test_countdown_list_empty(tmp_life_dir):
    result = runner.invoke(cmd, [])

    assert result.exit_code == 0
    assert "No countdowns" in result.stdout


def test_countdown_add(tmp_life_dir):
    result = runner.invoke(cmd, ["add", "vacation", "2025-12-25"])

    assert result.exit_code == 0
    assert "Added countdown" in result.stdout


def test_countdown_list_shows_added(tmp_life_dir):
    runner.invoke(cmd, ["add", "launch", "2025-06-01"])

    result = runner.invoke(cmd, [])

    assert result.exit_code == 0
    assert "launch" in result.stdout
    assert "2025-06-01" in result.stdout


def test_countdown_remove(tmp_life_dir):
    runner.invoke(cmd, ["add", "test", "2025-03-15"])

    result = runner.invoke(cmd, ["remove", "test"])

    assert result.exit_code == 0
    assert "Removed" in result.stdout


def test_countdown_add_missing_args_fails(tmp_life_dir):
    result = runner.invoke(cmd, ["add", "name_only"])

    assert result.exit_code != 0


def test_countdown_invalid_action_fails(tmp_life_dir):
    result = runner.invoke(cmd, ["invalid", "arg"])

    assert result.exit_code != 0
