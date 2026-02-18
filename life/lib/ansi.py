from typing import ClassVar


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
    CREAM = "\033[38;5;248m"
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
