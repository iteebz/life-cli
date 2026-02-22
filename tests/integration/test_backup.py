from tests.conftest import FnCLIRunner

runner = FnCLIRunner()


def test_backup_command_returns_path(tmp_life_dir):
    result = runner.invoke(["db", "backup"])

    assert result.exit_code == 0
    assert "/" in result.stdout
