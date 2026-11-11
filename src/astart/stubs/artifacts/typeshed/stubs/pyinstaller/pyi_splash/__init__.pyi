from typing import Final

__all__ = [
    "CLOSE_CONNECTION",
    "FLUSH_CHARACTER",
    "close",
    "is_alive",
    "update_text",
]

def is_alive() -> bool: ...
def update_text(msg: str) -> None: ...
def close() -> None: ...

CLOSE_CONNECTION: Final = b"\x04"
FLUSH_CHARACTER: Final = b"\x0d"
