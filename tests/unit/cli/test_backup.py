from typer.testing import CliRunner

from life.cli.backup import cmd

runner = CliRunner()


def test_backup_command_returns_path(tmp_life_dir):
    result = runner.invoke(cmd, [])

    assert result.exit_code == 0
    assert "/" in result.stdout
