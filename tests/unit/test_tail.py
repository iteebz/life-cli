from pathlib import Path

from life.commands import cmd_tail


def test_cmd_tail_runs_glm_via_zsh(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")

    calls: list[tuple[list[str], Path, dict | None]] = []

    class _Result:
        returncode = 0

    monkeypatch.setenv("ZAI_API_KEY", "test-key")

    def fake_run(cmd, cwd=None, env=None, check=False, timeout=None):  # noqa: ARG001
        calls.append((cmd, cwd, env))
        assert timeout == 1200
        return _Result()

    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("life.commands.subprocess.run", fake_run)
    monkeypatch.setattr("life.commands.time.sleep", lambda _seconds: None)

    cmd_tail(cycles=2, interval_seconds=1, model="glm-5", dry_run=False)

    assert len(calls) == 2
    assert calls[0][0][0:5] == ["claude", "--print", "--verbose", "--output-format", "stream-json"]
    assert "--model" in calls[0][0]
    assert "-p" in calls[0][0]
    assert calls[0][1] == life_dir
    assert calls[0][2] is not None
    assert calls[0][2]["ANTHROPIC_AUTH_TOKEN"] == "test-key"


def test_cmd_tail_dry_run_does_not_execute(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")

    monkeypatch.setattr(Path, "home", lambda: home)

    called = {"run": 0}

    def fake_run(cmd, cwd=None, env=None, check=False, timeout=None):  # noqa: ARG001
        called["run"] += 1
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr("life.commands.subprocess.run", fake_run)

    cmd_tail(cycles=1, model="glm-5", dry_run=True)
    assert called["run"] == 0


def test_cmd_tail_retries_then_succeeds(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("life.commands.time.sleep", lambda _seconds: None)

    class _Result:
        def __init__(self, code: int):
            self.returncode = code

    calls = {"n": 0}

    def fake_run(cmd, cwd=None, env=None, check=False, timeout=None):  # noqa: ARG001
        calls["n"] += 1
        return _Result(1 if calls["n"] == 1 else 0)

    monkeypatch.setattr("life.commands.subprocess.run", fake_run)
    cmd_tail(cycles=1, retries=2, retry_delay_seconds=0)
    assert calls["n"] == 2
