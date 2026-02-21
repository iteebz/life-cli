from typer.testing import CliRunner

from life.cli import app

runner = CliRunner()


def test_observe_write_retrieve_roundtrip(tmp_life_dir):
    result = runner.invoke(app, ["steward", "observe", "Janice seemed stressed about the wedding"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["steward", "boot"])
    assert result.exit_code == 0
    assert "Janice seemed stressed" in result.stdout


def test_observe_tag_filters_on_boot(tmp_life_dir):
    runner.invoke(app, ["steward", "observe", "noise entry", "--tag", "finance"])
    runner.invoke(app, ["steward", "observe", "janice hens weekend", "--tag", "janice"])

    result = runner.invoke(app, ["steward", "boot"])
    assert result.exit_code == 0
    assert "janice hens weekend" in result.stdout


def test_steward_close_persists_session(tmp_life_dir):
    result = runner.invoke(app, ["steward", "close", "closed tax loop, mood 3"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["steward", "boot"])
    assert result.exit_code == 0
    assert "closed tax loop" in result.stdout


def test_pattern_write_retrieve_roundtrip(tmp_life_dir):
    result = runner.invoke(app, ["pattern", "Decision fatigue disengages him"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["pattern", "--log"])
    assert result.exit_code == 0
    assert "Decision fatigue" in result.stdout


def test_mood_write_retrieve_rm_cycle(tmp_life_dir):
    result = runner.invoke(app, ["mood", "3", "flat"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["mood", "--log"])
    assert result.exit_code == 0
    assert "3" in result.stdout

    result = runner.invoke(app, ["mood", "rm"])
    assert result.exit_code == 0

    result = runner.invoke(app, ["mood", "--log"])
    assert result.exit_code == 0
    assert "3" not in result.stdout


def test_boot_exits_zero_on_empty_db(tmp_life_dir):
    result = runner.invoke(app, ["steward", "boot"])
    assert result.exit_code == 0


def test_steward_task_visible_in_boot(tmp_life_dir):
    runner.invoke(app, ["task", "build mood rm", "--steward", "--source", "tyson", "-t", "steward"])

    result = runner.invoke(app, ["steward", "boot"])
    assert result.exit_code == 0
    assert "build mood rm" in result.stdout
