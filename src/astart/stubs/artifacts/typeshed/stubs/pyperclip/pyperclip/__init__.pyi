__all__ = ["copy", "determine_clipboard", "paste", "set_clipboard"]
from collections.abc import Callable
from typing import Literal

class PyperclipException(RuntimeError): ...

class PyperclipWindowsException(PyperclipException):
    def __init__(self, message: str) -> None: ...

class PyperclipTimeoutException(PyperclipException): ...

type _ClipboardMechanismName = Literal[
    "pbcopy",
    "pyobjc",
    "qt",
    "xclip",
    "xsel",
    "wl-clipboard",
    "klipper",
    "windows",
    "no",
]
type _ClipboardCopyMechanism = Callable[[str], None]
type _ClipboardPasteMechanism = Callable[[], str]

def copy(text: str) -> None: ...
def paste() -> str: ...
def set_clipboard(clipboard: _ClipboardMechanismName) -> None: ...
def determine_clipboard() -> tuple[
    _ClipboardCopyMechanism,
    _ClipboardPasteMechanism,
]: ...
def is_available() -> bool: ...
