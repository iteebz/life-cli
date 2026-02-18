import io
from pathlib import Path

from life.commands import cmd_tail
from life.lib.tail import StreamParser, format_entry


class _FakePopen:
    def __init__(self, stdout_text: str, stderr_text: str, returncode: int = 0):
        self.stdout = io.StringIO(stdout_text)
        self.stderr = io.StringIO(stderr_text)
        self.returncode = returncode

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):  # noqa: ARG002
        return self.returncode

    def terminate(self):
        self.returncode = 124

    def kill(self):
        self.returncode = 124


def test_tail_parser_text_block_formats_ai_line():
    parser = StreamParser()
    entry = parser.parse_line(
        '{"type":"assistant","message":{"content":[{"type":"text","text":"hello world"}]}}'
    )
    assert entry is not None
    assert format_entry(entry) == "ai: hello world"


def test_tail_parser_tool_result_correlates_tool_name():
    parser = StreamParser()
    parser.parse_line(
        '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"toolu_1","name":"Read","input":{"file":"a.txt"}}]}}'
    )
    entry = parser.parse_line(
        '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"toolu_1","content":"ok"}]}}'
    )
    assert entry is not None
    assert format_entry(entry) == "result: Read ok"


def test_tail_parser_malformed_json_falls_back_to_raw():
    parser = StreamParser()
    entry = parser.parse_line("{not-json")
    assert entry is not None
    assert format_entry(entry) == "raw: {not-json"


def test_cmd_tail_streams_pretty_output(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("life.commands.time.sleep", lambda _seconds: None)

    calls: list[tuple[list[str], Path, dict | None, int | None]] = []
    outputs: list[str] = []

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, text=None, bufsize=None):  # noqa: ARG001
        calls.append((cmd, cwd, env, bufsize))
        return _FakePopen(
            '{"type":"assistant","message":{"content":[{"type":"text","text":"hi"}]}}\n',
            "",
            0,
        )

    monkeypatch.setattr("life.commands.subprocess.Popen", fake_popen)
    monkeypatch.setattr("life.commands.echo", lambda msg="", err=False: outputs.append(msg))

    cmd_tail(cycles=1, interval_seconds=0, dry_run=False)

    assert len(calls) == 1
    assert calls[0][0][0:5] == ["claude", "--print", "--verbose", "--output-format", "stream-json"]
    assert calls[0][1] == life_dir
    assert calls[0][2] is not None
    assert calls[0][2]["ANTHROPIC_AUTH_TOKEN"] == "test-key"
    assert "ai: hi" in outputs


def test_cmd_tail_raw_mode_prints_raw_lines(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr(Path, "home", lambda: home)

    outputs: list[str] = []

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, text=None, bufsize=None):  # noqa: ARG001
        return _FakePopen('{"type":"assistant"}\n', "", 0)

    monkeypatch.setattr("life.commands.subprocess.Popen", fake_popen)
    monkeypatch.setattr("life.commands.echo", lambda msg="", err=False: outputs.append(msg))

    cmd_tail(cycles=1, raw=True)
    assert '{"type":"assistant"}' in outputs


def test_cmd_tail_retries_then_succeeds(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr("life.commands.time.sleep", lambda _seconds: None)

    calls = {"n": 0}

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, text=None, bufsize=None):  # noqa: ARG001
        calls["n"] += 1
        return _FakePopen("", "boom\n", 1 if calls["n"] == 1 else 0)

    monkeypatch.setattr("life.commands.subprocess.Popen", fake_popen)
    cmd_tail(cycles=1, retries=2, retry_delay_seconds=0)
    assert calls["n"] == 2


def test_cmd_tail_dry_run_does_not_execute(monkeypatch, tmp_path):
    home = tmp_path
    life_dir = home / "life"
    life_dir.mkdir()
    (life_dir / "STEWARD.md").write_text("test steward prompt")
    monkeypatch.setattr(Path, "home", lambda: home)

    called = {"popen": 0}

    def fake_popen(cmd, cwd=None, env=None, stdout=None, stderr=None, text=None, bufsize=None):  # noqa: ARG001
        called["popen"] += 1
        raise AssertionError("subprocess.Popen should not be called in dry-run")

    monkeypatch.setattr("life.commands.subprocess.Popen", fake_popen)

    cmd_tail(cycles=1, dry_run=True)
    assert called["popen"] == 0
