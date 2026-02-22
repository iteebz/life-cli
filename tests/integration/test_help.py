from tests.conftest import FnCLIRunner


def test_dash_h_shows_help(tmp_life_dir):
    runner = FnCLIRunner()
    result = runner.invoke(["-h"])

    assert result.exit_code == 0
    assert "usage:" in result.stdout
