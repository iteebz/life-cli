import re

PERSONA_COLORS = {
    "roast": "\033[91m",
    "pepper": "\033[93m",
    "kim": "\033[94m",
}


class ANSI:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
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

    POOL = [RED, BLUE, MAGENTA, CYAN, YELLOW, GREEN]


def md_to_ansi(text: str) -> str:
    """Convert markdown formatting to ANSI escape codes."""

    lines = []
    for line in text.split("\n"):
        formatted = line

        formatted = re.sub(r"\*\*(.+?)\*\*", rf"{ANSI.BOLD}\1{ANSI.RESET}", formatted)

        formatted = re.sub(r"__(.+?)__", rf"{ANSI.BOLD}\1{ANSI.RESET}", formatted)

        formatted = re.sub(r"\*(.+?)\*", rf"{ANSI.ITALIC}\1{ANSI.RESET}", formatted)

        formatted = re.sub(r"_(.+?)_", rf"{ANSI.ITALIC}\1{ANSI.RESET}", formatted)

        formatted = re.sub(r"`(.+?)`", rf"{ANSI.CYAN}\1{ANSI.RESET}", formatted)

        if formatted.startswith("# "):
            formatted = f"{ANSI.BOLD}{ANSI.MAGENTA}{formatted[2:]}{ANSI.RESET}"
        elif formatted.startswith("## "):
            formatted = f"{ANSI.BOLD}{ANSI.BLUE}{formatted[3:]}{ANSI.RESET}"
        elif formatted.startswith("### "):
            formatted = f"{ANSI.BOLD}{formatted[4:]}{ANSI.RESET}"

        if formatted.lstrip().startswith("- "):
            indent = len(formatted) - len(formatted.lstrip())
            bullet = f"{ANSI.GREEN}•{ANSI.RESET}"
            formatted = " " * indent + bullet + formatted[indent + 1 :]

        lines.append(formatted)

    return "\n".join(lines)
