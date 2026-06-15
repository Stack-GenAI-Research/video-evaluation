from __future__ import annotations

from rich.console import Console

console = Console(highlight=False)


def info(message: str) -> None:
    console.print(f"info: {message}")


def warn(message: str) -> None:
    console.print(f"warn: {message}")


def error(message: str) -> None:
    console.print(f"error: {message}")
