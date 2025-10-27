"""Tests for ephemeral Claude persona invocations."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from life.lib.claude import invoke


@pytest.fixture
def temp_home():
    """Fixture providing a temporary home directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_invoke_creates_ephemeral_claude_md(temp_home, tmp_life_dir):
    """Invoke creates temporary CLAUDE.md with persona content during execution."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):

        def check_claude_md_exists(*args, **kwargs):
            claude_path = temp_home / ".claude" / "CLAUDE.md"
            assert claude_path.exists(), "CLAUDE.md should exist during subprocess call"
            return MagicMock(stdout="test")

        mock_run.side_effect = check_claude_md_exists

        invoke("test message", persona="roast")


def test_invoke_restores_original_claude_md(temp_home, tmp_life_dir):
    """Invoke restores original CLAUDE.md after execution."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        claude_path = temp_home / ".claude" / "CLAUDE.md"
        original = "# Original Zealot"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(original)

        invoke("test message", persona="pepper")

        assert claude_path.read_text() == original


def test_invoke_restores_original_when_subprocess_fails(temp_home, tmp_life_dir):
    """Invoke restores CLAUDE.md even if subprocess fails."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.side_effect = RuntimeError("subprocess failed")

        claude_path = temp_home / ".claude" / "CLAUDE.md"
        original = "# Original"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(original)

        with pytest.raises(RuntimeError):
            invoke("test message", persona="kim")

        assert claude_path.read_text() == original


def test_invoke_deletes_ephemeral_if_no_original(temp_home, tmp_life_dir):
    """Invoke removes CLAUDE.md if none existed before."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        claude_path = temp_home / ".claude" / "CLAUDE.md"
        assert not claude_path.exists()

        invoke("test message", persona="roast")

        assert not claude_path.exists()


def test_invoke_writes_persona_instructions(temp_home, tmp_life_dir):
    """Invoke writes persona instructions to CLAUDE.md during execution."""
    captured_content = None

    def capture_claude_md(*args, **kwargs):
        nonlocal captured_content
        claude_path = temp_home / ".claude" / "CLAUDE.md"
        captured_content = claude_path.read_text()
        return MagicMock(stdout="test")

    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.side_effect = capture_claude_md

        invoke("test message", persona="pepper")

        assert captured_content is not None
        assert "[PEPPER IDENTITY]" in captured_content
        assert "optimistic realist" in captured_content.lower()


def test_invoke_passes_task_prompt_to_claude(temp_home, tmp_life_dir):
    """Invoke passes task prompt (not CLAUDE.md) to Claude subprocess."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        invoke("test message", persona="roast")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        assert "claude" in call_args
        assert "--model" in call_args
        assert "claude-haiku-4-5" in call_args
        assert "-p" in call_args

        prompt_idx = call_args.index("-p") + 1
        prompt = call_args[prompt_idx]
        assert "[ROASTER IDENTITY]" in prompt


def test_invoke_default_persona_is_roast(temp_home, tmp_life_dir):
    """Invoke defaults to roast persona."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        invoke("test message")

        call_args = mock_run.call_args[0][0]
        prompt_idx = call_args.index("-p") + 1
        prompt = call_args[prompt_idx]
        assert "[ROASTER IDENTITY]" in prompt


def test_invoke_creates_parent_directories(temp_home, tmp_life_dir):
    """Invoke creates .claude directory if needed."""
    with (
        patch("life.lib.claude.Path.home", return_value=temp_home),
        patch("life.lib.claude.subprocess.run") as mock_run,
        patch("life.lib.claude.Spinner"),
        patch("life.lib.claude.md_to_ansi", return_value="output"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        temp_home / ".claude" / "CLAUDE.md"
        assert not (temp_home / ".claude").exists()

        invoke("test message", persona="pepper")

        assert (temp_home / ".claude").exists()
