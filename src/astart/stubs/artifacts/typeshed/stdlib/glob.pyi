import sys
from collections.abc import Iterator, Sequence
from typing import AnyStr
from warnings import deprecated

from _typeshed import StrOrBytesPath

__all__ = ["escape", "glob", "iglob"]
__all__ += ["translate"]
if sys.version_info < (3, 15):
    @deprecated(
        "Deprecated since Python 3.10; will be removed in Python 3.15. Use `glob.glob()` with the *root_dir* argument instead.",
    )
    def glob0(dirname: AnyStr, pattern: AnyStr) -> list[AnyStr]: ...
    @deprecated(
        "Deprecated since Python 3.10; will be removed in Python 3.15. Use `glob.glob()` with the *root_dir* argument instead.",
    )
    def glob1(dirname: AnyStr, pattern: AnyStr) -> list[AnyStr]: ...

def glob[AnyStr: (bytes, str)](
    pathname: AnyStr,
    *,
    root_dir: StrOrBytesPath | None = None,
    dir_fd: int | None = None,
    recursive: bool = False,
    include_hidden: bool = False,
) -> list[AnyStr]: ...
def iglob[AnyStr: (bytes, str)](
    pathname: AnyStr,
    *,
    root_dir: StrOrBytesPath | None = None,
    dir_fd: int | None = None,
    recursive: bool = False,
    include_hidden: bool = False,
) -> Iterator[AnyStr]: ...
def escape[AnyStr: (bytes, str)](pathname: AnyStr) -> AnyStr: ...
def has_magic(s: str | bytes) -> bool: ...
def translate(
    pat: str,
    *,
    recursive: bool = False,
    include_hidden: bool = False,
    seps: Sequence[str] | None = None,
) -> str: ...
