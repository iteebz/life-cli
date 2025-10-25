import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "life"))

from lib.ansi import ANSI, md_to_ansi


def test_bold():
    result = md_to_ansi("**bold**")
    assert ANSI.BOLD in result
    assert ANSI.RESET in result


def test_italic():
    result = md_to_ansi("*italic*")
    assert ANSI.ITALIC in result
    assert ANSI.RESET in result


def test_code():
    result = md_to_ansi("`code`")
    assert ANSI.CYAN in result


def test_h1():
    result = md_to_ansi("# heading")
    assert ANSI.MAGENTA in result
    assert ANSI.BOLD in result


def test_h2():
    result = md_to_ansi("## heading")
    assert ANSI.BLUE in result
    assert ANSI.BOLD in result


def test_bullet():
    result = md_to_ansi("- item")
    assert ANSI.GREEN in result
    assert "•" in result


def test_multiple_formats():
    result = md_to_ansi("**bold** and *italic* and `code`")
    assert ANSI.BOLD in result
    assert ANSI.ITALIC in result
    assert ANSI.CYAN in result
