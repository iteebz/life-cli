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
    GREY = "\033[90m"
    RESET = "\033[0m"

    MUTED = "\033[90m"
    SECONDARY = "\033[38;5;245m"

    LIME = "\033[38;5;155m"
    TEAL = "\033[38;5;80m"
    GOLD = "\033[38;5;220m"
    CORAL = "\033[38;5;209m"
    PURPLE = "\033[38;5;141m"
    SKY = "\033[38;5;67m"
    BLUE = "\033[38;5;111m"
    GREEN = "\033[38;5;114m"
    RED = "\033[38;5;203m"
    GRAY = "\033[38;5;245m"
    WHITE = "\033[38;5;252m"
    FOREST = "\033[38;5;65m"
    SLATE = "\033[38;5;103m"
    PEACH = "\033[38;5;217m"
    ORANGE = "\033[38;5;173m"
    MAGENTA = "\033[38;5;139m"
    CYAN = "\033[38;5;109m"
    YELLOW = "\033[38;5;179m"
    PINK = "\033[38;5;175m"
    LAVENDER = "\033[38;5;146m"
    APRICOT = "\033[38;5;216m"
    MINT = "\033[38;5;122m"
    BERRY = "\033[38;5;163m"
    SAGE = "\033[38;5;151m"
    INDIGO = "\033[38;5;99m"

    POOL: ClassVar[list[str]] = [
        ORANGE,
        BLUE,
        MAGENTA,
        CYAN,
        YELLOW,
        GREEN,
        RED,
        PURPLE,
        TEAL,
        PINK,
        LAVENDER,
        CORAL,
        LIME,
        SKY,
        APRICOT,
        MINT,
        BERRY,
        GOLD,
        SAGE,
        INDIGO,
        FOREST,
        SLATE,
        PEACH,
    ]


_R = ANSI.RESET
_B = ANSI.BOLD


def strip(text: str) -> str:
    return _ANSI_RE.sub("", text)


def strip_markdown(text: str) -> str:
    text = _MD_BOLD_RE.sub(r"\1", text)
    text = _MD_ITALIC_RE.sub(r"\1", text)
    text = _MD_CODE_RE.sub(r"\1", text)
    text = _MD_HEADING_RE.sub("", text)
    return _MD_LINK_RE.sub(r"\1", text)


def bold(text: str) -> str:
    return f"{_B}{text}\033[22m{_R}"


def dim(text: str) -> str:
    return f"\033[2m{text}\033[22m{_R}"


def muted(text: str) -> str:
    return f"{ANSI.MUTED}{text}{_R}"


def secondary(text: str) -> str:
    return f"{ANSI.SECONDARY}{text}{_R}"


def lime(text: str) -> str:
    return f"{ANSI.LIME}{text}{_R}"


def teal(text: str) -> str:
    return f"{ANSI.TEAL}{text}{_R}"


def gold(text: str) -> str:
    return f"{ANSI.GOLD}{text}{_R}"


def coral(text: str) -> str:
    return f"{ANSI.CORAL}{text}{_R}"


def purple(text: str) -> str:
    return f"{ANSI.PURPLE}{text}{_R}"


def sky(text: str) -> str:
    return f"{ANSI.SKY}{text}{_R}"


def blue(text: str) -> str:
    return f"{ANSI.BLUE}{text}{_R}"


def green(text: str) -> str:
    return f"{ANSI.GREEN}{text}{_R}"


def red(text: str) -> str:
    return f"{ANSI.RED}{text}{_R}"


def gray(text: str) -> str:
    return f"{ANSI.GRAY}{text}{_R}"


def white(text: str) -> str:
    return f"{ANSI.WHITE}{text}{_R}"


def forest(text: str) -> str:
    return f"{ANSI.FOREST}{text}{_R}"


def slate(text: str) -> str:
    return f"{ANSI.SLATE}{text}{_R}"


def peach(text: str) -> str:
    return f"{ANSI.PEACH}{text}{_R}"


def orange(text: str) -> str:
    return f"{ANSI.ORANGE}{text}{_R}"


def magenta(text: str) -> str:
    return f"{ANSI.MAGENTA}{text}{_R}"


def cyan(text: str) -> str:
    return f"{ANSI.CYAN}{text}{_R}"


def yellow(text: str) -> str:
    return f"{ANSI.YELLOW}{text}{_R}"


def pink(text: str) -> str:
    return f"{ANSI.PINK}{text}{_R}"


def lavender(text: str) -> str:
    return f"{ANSI.LAVENDER}{text}{_R}"


def mint(text: str) -> str:
    return f"{ANSI.MINT}{text}{_R}"


def sage(text: str) -> str:
    return f"{ANSI.SAGE}{text}{_R}"


def indigo(text: str) -> str:
    return f"{ANSI.INDIGO}{text}{_R}"
