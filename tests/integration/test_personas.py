from typer.testing import CliRunner

from life.cli import app

runner = CliRunner()


def test_list(tmp_life_dir):
    result = runner.invoke(app, ["personas"])

    assert result.exit_code == 0


def test_show_roast(tmp_life_dir):
    result = runner.invoke(app, ["personas", "roast"])

    assert result.exit_code == 0
    assert "roast" in result.stdout.lower()


def test_show_pepper(tmp_life_dir):
    result = runner.invoke(app, ["personas", "pepper"])

    assert result.exit_code == 0
    assert "pepper" in result.stdout.lower()


def test_show_kim(tmp_life_dir):
    result = runner.invoke(app, ["personas", "kim"])

    assert result.exit_code == 0
    assert "kim" in result.stdout.lower()


def test_invalid_persona_fails(tmp_life_dir):
    result = runner.invoke(app, ["personas", "invalid"])

    assert result.exit_code != 0
