import sys
import termios
from typing import IO, Final

if sys.platform != "win32":
    __all__ = ["setcbreak", "setraw"]
    __all__ += ["cfmakecbreak", "cfmakeraw"]
    type _ModeSetterReturn = termios._AttrReturn
    type _FD = int | IO[str]
    IFLAG: Final = 0
    OFLAG: Final = 1
    CFLAG: Final = 2
    LFLAG: Final = 3
    ISPEED: Final = 4
    OSPEED: Final = 5
    CC: Final = 6
    def setraw(fd: _FD, when: int = 2) -> _ModeSetterReturn: ...
    def setcbreak(fd: _FD, when: int = 2) -> _ModeSetterReturn: ...
    def cfmakeraw(mode: termios._Attr) -> None: ...
    def cfmakecbreak(mode: termios._Attr) -> None: ...
