from typer.testing import CliRunner

from life.cli import app


def test_tag_positional_syntax(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["task", "home loan"])
    result = runner.invoke(app, ["tag", "finance", "home loan"])

    assert result.exit_code == 0
    assert "Tagged:" in result.stdout


def test_tag_option_syntax(tmp_life_dir):
    runner = CliRunner()
    runner.invoke(app, ["task", "home loan"])
    result = runner.invoke(app, ["tag", "home loan", "--tag", "finance"])

    assert result.exit_code == 0
    assert "Tagged:" in result.stdout
