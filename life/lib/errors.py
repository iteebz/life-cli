from typing import NoReturn

import typer

__all__ = ["echo", "exit_error"]


def echo(message: str = "", err: bool = False) -> None:
    typer.echo(message, err=err)


def exit_error(message: str, code: int = 1) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(code)
