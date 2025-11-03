from typer.testing import CliRunner

from life.cli import app


def test_list_empty(tmp_life_dir):
    runner = CliRunner()
    result = runner.invoke(app, ["dates"])

    assert result.exit_code == 0
    assert "No dates" in result.stdout


def test_add(tmp_life_dir):
    runner = CliRunner()
    result = runner.invoke(app, ["dates", "add", "vacation", "2025-12-25"])

    assert result.exit_code == 0
    assert "Added date" in result.stdout


def test_list_shows_added(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["dates", "add", "launch", "2025-06-01"])

    result = runner.invoke(app, ["dates"])

    assert result.exit_code == 0
    assert "launch" in result.stdout
    assert "2025-06-01" in result.stdout


def test_remove(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["dates", "add", "test", "2025-03-15"])

    result = runner.invoke(app, ["dates", "remove", "test"])

    assert result.exit_code == 0
    assert "Removed" in result.stdout


def test_add_missing_args_fails(tmp_life_dir):
    runner = CliRunner()
    result = runner.invoke(app, ["dates", "add", "name_only"])

    assert result.exit_code != 0


def test_invalid_action_fails(tmp_life_dir):
    runner = CliRunner()
    result = runner.invoke(app, ["dates", "invalid", "arg"])

    assert result.exit_code != 0
