from typer.testing import CliRunner

from life.cli.personas import cmd

runner = CliRunner()


def test_personas_list(tmp_life_dir):
    result = runner.invoke(cmd, [])

    assert result.exit_code == 0


def test_personas_show_roast(tmp_life_dir):
    result = runner.invoke(cmd, ["roast"])

    assert result.exit_code == 0
    assert "roast" in result.stdout.lower()


def test_personas_show_pepper(tmp_life_dir):
    result = runner.invoke(cmd, ["pepper"])

    assert result.exit_code == 0
    assert "pepper" in result.stdout.lower()


def test_personas_show_kim(tmp_life_dir):
    result = runner.invoke(cmd, ["kim"])

    assert result.exit_code == 0
    assert "kim" in result.stdout.lower()


def test_personas_invalid_persona_fails(tmp_life_dir):
    result = runner.invoke(cmd, ["invalid"])

    assert result.exit_code != 0
