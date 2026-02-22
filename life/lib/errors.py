import sys
from typing import NoReturn

__all__ = ["echo", "exit_error"]


def echo(message: str = "", err: bool = False) -> None:
    if err:
        sys.stderr.write(message + "\n")
    else:
        sys.stdout.write(message + "\n")


def exit_error(message: str, code: int = 1) -> NoReturn:
    sys.stderr.write(message + "\n")
    sys.exit(code)
