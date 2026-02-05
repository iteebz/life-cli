from typer.testing import CliRunner

from life.cli import app


def test_dash_h_shows_help():
    runner = CliRunner()
    result = runner.invoke(app, ["-h"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
