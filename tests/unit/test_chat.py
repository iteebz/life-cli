"""Tests for ephemeral Claude persona invocations."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from life.chat import _build_prompt, _ephemeral_claude_md, _format_output, invoke


@pytest.fixture
def temp_home():
    """Fixture providing a temporary home directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_build_prompt_includes_persona_and_message(tmp_life_dir):
    """_build_prompt constructs prompt with persona instructions and user message."""
    with patch("life.chat.get_profile", return_value=""):
        prompt = _build_prompt("test message", persona="roast")
        assert "[ROASTER IDENTITY]" in prompt
        assert "test message" in prompt
        assert "USER MESSAGE:" in prompt


def test_build_prompt_includes_profile_when_set(tmp_life_dir):
    """_build_prompt includes profile section when profile is set."""
    with patch("life.chat.get_profile", return_value="ADHD, works late"):
        prompt = _build_prompt("test", persona="pepper")
        assert "PROFILE:" in prompt
        assert "ADHD, works late" in prompt


def test_build_prompt_skips_profile_when_empty(tmp_life_dir):
    """_build_prompt skips profile section when profile is empty."""
    with patch("life.chat.get_profile", return_value=""):
        prompt = _build_prompt("test", persona="kim")
        assert "PROFILE:" not in prompt


def test_ephemeral_claude_md_creates_file(temp_home, tmp_life_dir):
    """_ephemeral_claude_md context manager creates CLAUDE.md with persona."""
    with patch("life.chat.Path.home", return_value=temp_home):
        with _ephemeral_claude_md("roast"):
            claude_path = temp_home / ".claude" / "CLAUDE.md"
            assert claude_path.exists()
            content = claude_path.read_text()
            assert "[ROASTER IDENTITY]" in content


def test_ephemeral_claude_md_restores_original(temp_home, tmp_life_dir):
    """_ephemeral_claude_md restores original CLAUDE.md on exit."""
    with patch("life.chat.Path.home", return_value=temp_home):
        claude_path = temp_home / ".claude" / "CLAUDE.md"
        original = "# Original"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(original)

        with _ephemeral_claude_md("pepper"):
            assert "[PEPPER IDENTITY]" in claude_path.read_text()

        assert claude_path.read_text() == original


def test_ephemeral_claude_md_deletes_if_no_original(temp_home, tmp_life_dir):
    """_ephemeral_claude_md deletes CLAUDE.md if none existed before."""
    with patch("life.chat.Path.home", return_value=temp_home):
        claude_path = temp_home / ".claude" / "CLAUDE.md"
        assert not claude_path.exists()

        with _ephemeral_claude_md("kim"):
            assert claude_path.exists()

        assert not claude_path.exists()


def test_ephemeral_claude_md_restores_on_error(temp_home, tmp_life_dir):
    """_ephemeral_claude_md restores original even if context raises error."""
    with patch("life.chat.Path.home", return_value=temp_home):
        claude_path = temp_home / ".claude" / "CLAUDE.md"
        original = "# Original"
        claude_path.parent.mkdir(parents=True, exist_ok=True)
        claude_path.write_text(original)

        with pytest.raises(ValueError):
            with _ephemeral_claude_md("roast"):
                raise ValueError("test error")

        assert claude_path.read_text() == original


def test_format_output_includes_persona_header(tmp_life_dir):
    """_format_output includes persona header in output."""
    output = _format_output("response text", persona="roast")
    assert "[roast]" in output
    assert "response text" in output


def test_invoke_calls_all_steps(temp_home, tmp_life_dir):
    """invoke orchestrates prompt → file setup → subprocess → output."""
    with (
        patch("life.chat.Path.home", return_value=temp_home),
        patch("life.chat.subprocess.run") as mock_run,
        patch("life.chat.Spinner"),
        patch("life.chat.md_to_ansi", return_value="formatted"),
        patch("life.chat.sys.stdout.write") as mock_write,
    ):
        mock_run.return_value = MagicMock(stdout="claude output")

        invoke("test message", persona="roast")

        mock_run.assert_called_once()
        mock_write.assert_called_once()
        assert "[roast]" in mock_write.call_args[0][0]


def test_invoke_default_persona_is_roast(temp_home, tmp_life_dir):
    """invoke defaults to roast persona."""
    with (
        patch("life.chat.Path.home", return_value=temp_home),
        patch("life.chat.subprocess.run") as mock_run,
        patch("life.chat.Spinner"),
        patch("life.chat.md_to_ansi", return_value="output"),
        patch("life.chat.sys.stdout.write"),
    ):
        mock_run.return_value = MagicMock(stdout="test")

        invoke("test message")

        call_args = mock_run.call_args[0][0]
        prompt_idx = call_args.index("-p") + 1
        prompt = call_args[prompt_idx]
        assert "[ROASTER IDENTITY]" in prompt
