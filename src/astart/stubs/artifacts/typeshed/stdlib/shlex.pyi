from collections import deque
from collections.abc import Iterable
from io import TextIOWrapper
from typing import Literal, Protocol, Self, type_check_only

__all__ = ["join", "quote", "shlex", "split"]

@type_check_only
class _ShlexInstream(Protocol):
    def read(self, size: Literal[1], /) -> str: ...
    def readline(self) -> object: ...
    def close(self) -> object: ...

def split(
    s: str | _ShlexInstream,
    comments: bool = False,
    posix: bool = True,
) -> list[str]: ...
def join(split_command: Iterable[str]) -> str: ...
def quote(s: str) -> str: ...

class shlex:
    commenters: str
    wordchars: str
    whitespace: str
    escape: str
    quotes: str
    escapedquotes: str
    whitespace_split: bool
    infile: str | None
    instream: _ShlexInstream
    source: str
    debug: int
    lineno: int
    token: str
    filestack: deque[tuple[str | None, _ShlexInstream, int]]
    eof: str | None
    @property
    def punctuation_chars(self) -> str: ...
    def __init__(
        self,
        instream: str | _ShlexInstream | None = None,
        infile: str | None = None,
        posix: bool = False,
        punctuation_chars: bool | str = False,
    ) -> None: ...
    def get_token(self) -> str | None: ...
    def push_token(self, tok: str) -> None: ...
    def read_token(self) -> str | None: ...
    def sourcehook(self, newfile: str) -> tuple[str, TextIOWrapper] | None: ...
    def push_source(
        self,
        newstream: str | _ShlexInstream,
        newfile: str | None = None,
    ) -> None: ...
    def pop_source(self) -> None: ...
    def error_leader(
        self,
        infile: str | None = None,
        lineno: int | None = None,
    ) -> str: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> str: ...
