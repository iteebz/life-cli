from pathlib import Path

from life.commands import cmd_tail


def test_cmd_tail_runs_glm_via_zsh(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")

    calls: list[tuple[list[str], Path]] = []

    class _Result:
        returncode = 0

    def fake_run(cmd, cwd=None, check=False):  # noqa: ARG001
        calls.append((cmd, cwd))
        return _Result()

    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("life.commands.subprocess.run", fake_run)
    monkeypatch.setattr("life.commands.time.sleep", lambda _seconds: None)

    cmd_tail(cycles=2, interval_seconds=1, model="glm-5", dry_run=False)

    assert len(calls) == 2
    assert calls[0][0][0:2] == ["zsh", "-lic"]
    assert "glm --print --model glm-5 -p " in calls[0][0][2]
    assert calls[0][1] == life_dir


def test_cmd_tail_dry_run_does_not_execute(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")

    monkeypatch.setattr(Path, "home", lambda: home)

    called = {"run": 0}

    def fake_run(cmd, cwd=None, check=False):  # noqa: ARG001
        called["run"] += 1
        raise AssertionError("subprocess.run should not be called in dry-run")

    monkeypatch.setattr("life.commands.subprocess.run", fake_run)

    cmd_tail(cycles=1, model="glm-5", dry_run=True)
    assert called["run"] == 0
