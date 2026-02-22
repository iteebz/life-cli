from tests.conftest import FnCLIRunner


def test_tag_positional_syntax(tmp_life_dir):
    runner = FnCLIRunner()
    runner.invoke(["add", "home loan"])
    result = runner.invoke(["tag", "home loan", "finance"])

    assert result.exit_code == 0
    assert "#finance" in result.stdout


def test_tag_option_syntax(tmp_life_dir):
    runner = FnCLIRunner()
    runner.invoke(["add", "home loan"])
    result = runner.invoke(["tag", "home loan", "finance"])

    assert result.exit_code == 0
    assert "#finance" in result.stdout
