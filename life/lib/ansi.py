import re
from typing import ClassVar

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_MD_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_MD_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
_MD_CODE_RE = re.compile(r"`([^`]+)`")
_MD_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


class ANSI:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GREY = "\033[90m"
    RESET = "\033[0m"

    SOFT_BLUE = "\033[38;5;110m"
    SOFT_GREEN = "\033[38;5;108m"
    SOFT_YELLOW = "\033[38;5;179m"
    SOFT_MAGENTA = "\033[38;5;139m"
    SOFT_CYAN = "\033[38;5;109m"
    SOFT_ORANGE = "\033[38;5;173m"
    SOFT_RED = "\033[38;5;167m"
    SOFT_PURPLE = "\033[38;5;141m"
    SOFT_TEAL = "\033[38;5;72m"
    SOFT_PINK = "\033[38;5;175m"
    SOFT_LAVENDER = "\033[38;5;146m"
    SOFT_CORAL = "\033[38;5;209m"
    SOFT_LIME = "\033[38;5;154m"
    SOFT_SKY = "\033[38;5;117m"
    SOFT_APRICOT = "\033[38;5;216m"
    SOFT_MINT = "\033[38;5;122m"
    SOFT_BERRY = "\033[38;5;163m"
    SOFT_GOLD = "\033[38;5;185m"
    SOFT_SAGE = "\033[38;5;151m"
    SOFT_INDIGO = "\033[38;5;99m"

    POOL: ClassVar[list[str]] = [
        SOFT_ORANGE,
        SOFT_BLUE,
        SOFT_MAGENTA,
        SOFT_CYAN,
        SOFT_YELLOW,
        SOFT_GREEN,
        SOFT_RED,
        SOFT_PURPLE,
        SOFT_TEAL,
        SOFT_PINK,
        SOFT_LAVENDER,
        SOFT_CORAL,
        SOFT_LIME,
        SOFT_SKY,
        SOFT_APRICOT,
        SOFT_MINT,
        SOFT_BERRY,
        SOFT_GOLD,
        SOFT_SAGE,
        SOFT_INDIGO,
    ]


_R = ANSI.RESET
_B = ANSI.BOLD

_LIME   = "\033[38;5;155m"
_TEAL   = "\033[38;5;80m"
_GOLD   = "\033[38;5;220m"
_CORAL  = "\033[38;5;209m"
_PURPLE = "\033[38;5;141m"
_SKY    = "\033[38;5;67m"
_BLUE   = "\033[38;5;111m"
_GREEN  = "\033[38;5;114m"
_RED    = "\033[38;5;203m"
_GRAY   = "\033[38;5;245m"
_WHITE  = "\033[38;5;252m"
_FOREST = "\033[38;5;65m"
_SLATE  = "\033[38;5;103m"
_PEACH  = "\033[38;5;217m"


def strip(text: str) -> str:
    return _ANSI_RE.sub("", text)


def strip_markdown(text: str) -> str:
    text = _MD_BOLD_RE.sub(r"\1", text)
    text = _MD_ITALIC_RE.sub(r"\1", text)
    text = _MD_CODE_RE.sub(r"\1", text)
    text = _MD_HEADING_RE.sub("", text)
    text = _MD_LINK_RE.sub(r"\1", text)
    return text


def bold(text: str) -> str:
    return f"{_B}{text}\033[22m{_R}"


def dim(text: str) -> str:
    return f"\033[2m{text}\033[22m{_R}"


def lime(text: str) -> str:
    return f"{_LIME}{text}{_R}"


def teal(text: str) -> str:
    return f"{_TEAL}{text}{_R}"


def gold(text: str) -> str:
    return f"{_GOLD}{text}{_R}"


def coral(text: str) -> str:
    return f"{_CORAL}{text}{_R}"


def purple(text: str) -> str:
    return f"{_PURPLE}{text}{_R}"


def sky(text: str) -> str:
    return f"{_SKY}{text}{_R}"


def blue(text: str) -> str:
    return f"{_BLUE}{text}{_R}"


def green(text: str) -> str:
    return f"{_GREEN}{text}{_R}"


def red(text: str) -> str:
    return f"{_RED}{text}{_R}"


def gray(text: str) -> str:
    return f"{_GRAY}{text}{_R}"


def white(text: str) -> str:
    return f"{_WHITE}{text}{_R}"


def forest(text: str) -> str:
    return f"{_FOREST}{text}{_R}"


def slate(text: str) -> str:
    return f"{_SLATE}{text}{_R}"


def peach(text: str) -> str:
    return f"{_PEACH}{text}{_R}"
