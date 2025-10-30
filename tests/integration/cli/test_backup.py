from typer.testing import CliRunner

from life.cli import app

runner = CliRunner()


def test_backup_command_returns_path(tmp_life_dir):
    result = runner.invoke(app, ["backup"])

    assert result.exit_code == 0
    assert "/" in result.stdout
