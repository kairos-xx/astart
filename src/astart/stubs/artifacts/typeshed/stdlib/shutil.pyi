import os
import sys
from collections.abc import Callable, Iterable, Sequence
from tarfile import _TarfileFilter
from typing import (
    Any,
    AnyStr,
    NamedTuple,
    NoReturn,
    Protocol,
    TypeVar,
    overload,
    type_check_only,
)
from warnings import deprecated

from _typeshed import (
    BytesPath,
    ExcInfo,
    FileDescriptorOrPath,
    MaybeNone,
    StrOrBytesPath,
    StrPath,
    SupportsRead,
    SupportsWrite,
)

__all__ = [
    "Error",
    "SameFileError",
    "SpecialFileError",
    "chown",
    "copy",
    "copy2",
    "copyfile",
    "copyfileobj",
    "copymode",
    "copystat",
    "copytree",
    "disk_usage",
    "get_archive_formats",
    "get_terminal_size",
    "get_unpack_formats",
    "ignore_patterns",
    "make_archive",
    "move",
    "register_archive_format",
    "register_unpack_format",
    "rmtree",
    "unpack_archive",
    "unregister_archive_format",
    "unregister_unpack_format",
    "which",
]
if sys.version_info < (3, 14):
    __all__ += ["ExecError"]
_StrOrBytesPathT = TypeVar("_StrOrBytesPathT", bound=StrOrBytesPath)
_StrPathT = TypeVar("_StrPathT", bound=StrPath)
_BytesPathT = TypeVar("_BytesPathT", bound=BytesPath)

class Error(OSError): ...
class SameFileError(Error): ...
class SpecialFileError(OSError): ...

if sys.version_info >= (3, 14):
    ExecError = RuntimeError
else:
    class ExecError(OSError): ...

class ReadError(OSError): ...
class RegistryError(Exception): ...

def copyfileobj(
    fsrc: SupportsRead[AnyStr],
    fdst: SupportsWrite[AnyStr],
    length: int = 0,
) -> None: ...
def copyfile[StrOrBytesPathT: StrOrBytesPath](
    src: StrOrBytesPath,
    dst: _StrOrBytesPathT,
    *,
    follow_symlinks: bool = True,
) -> _StrOrBytesPathT: ...
def copymode(
    src: StrOrBytesPath,
    dst: StrOrBytesPath,
    *,
    follow_symlinks: bool = True,
) -> None: ...
def copystat(
    src: StrOrBytesPath,
    dst: StrOrBytesPath,
    *,
    follow_symlinks: bool = True,
) -> None: ...
@overload
def copy[StrPathT: StrPath](
    src: StrPath,
    dst: _StrPathT,
    *,
    follow_symlinks: bool = True,
) -> _StrPathT | str: ...
@overload
def copy[BytesPathT: BytesPath](
    src: BytesPath,
    dst: _BytesPathT,
    *,
    follow_symlinks: bool = True,
) -> _BytesPathT | bytes: ...
@overload
def copy2[StrPathT: StrPath](
    src: StrPath,
    dst: _StrPathT,
    *,
    follow_symlinks: bool = True,
) -> _StrPathT | str: ...
@overload
def copy2[BytesPathT: BytesPath](
    src: BytesPath,
    dst: _BytesPathT,
    *,
    follow_symlinks: bool = True,
) -> _BytesPathT | bytes: ...
def ignore_patterns(
    *patterns: StrPath,
) -> Callable[[Any, list[str]], set[str]]: ...
def copytree[StrPathT: StrPath](
    src: StrPath,
    dst: _StrPathT,
    symlinks: bool = False,
    ignore: None
    | Callable[[str, list[str]], Iterable[str]]
    | Callable[[StrPath, list[str]], Iterable[str]] = None,
    copy_function: Callable[[str, str], object] = ...,
    ignore_dangling_symlinks: bool = False,
    dirs_exist_ok: bool = False,
) -> _StrPathT: ...

type _OnErrorCallback = Callable[[Callable[..., Any], str, ExcInfo], object]
type _OnExcCallback = Callable[
    [Callable[..., Any], str, BaseException],
    object,
]

@type_check_only
class _RmtreeType(Protocol):
    avoids_symlink_attacks: bool
    @overload
    @deprecated("The `onerror` parameter is deprecated. Use `onexc` instead.")
    def __call__(
        self,
        path: StrOrBytesPath,
        ignore_errors: bool,
        onerror: _OnErrorCallback | None,
        *,
        onexc: None = None,
        dir_fd: int | None = None,
    ) -> None: ...
    @overload
    @deprecated("The `onerror` parameter is deprecated. Use `onexc` instead.")
    def __call__(
        self,
        path: StrOrBytesPath,
        ignore_errors: bool = False,
        *,
        onerror: _OnErrorCallback | None,
        onexc: None = None,
        dir_fd: int | None = None,
    ) -> None: ...
    @overload
    def __call__(
        self,
        path: StrOrBytesPath,
        ignore_errors: bool = False,
        *,
        onexc: _OnExcCallback | None = None,
        dir_fd: int | None = None,
    ) -> None: ...

rmtree: _RmtreeType
type _CopyFn = (
    Callable[[str, str], object] | Callable[[StrPath, StrPath], object]
)

def move[StrPathT: StrPath](
    src: StrPath,
    dst: _StrPathT,
    copy_function: _CopyFn = ...,
) -> _StrPathT | str | MaybeNone: ...

class _ntuple_diskusage(NamedTuple):
    total: int
    used: int
    free: int

def disk_usage(path: FileDescriptorOrPath) -> _ntuple_diskusage: ...
@overload
def chown(
    path: FileDescriptorOrPath,
    user: str | int,
    group: None = None,
    *,
    dir_fd: int | None = None,
    follow_symlinks: bool = True,
) -> None: ...
@overload
def chown(
    path: FileDescriptorOrPath,
    user: None = None,
    *,
    group: str | int,
    dir_fd: int | None = None,
    follow_symlinks: bool = True,
) -> None: ...
@overload
def chown(
    path: FileDescriptorOrPath,
    user: None,
    group: str | int,
    *,
    dir_fd: int | None = None,
    follow_symlinks: bool = True,
) -> None: ...
@overload
def chown(
    path: FileDescriptorOrPath,
    user: str | int,
    group: str | int,
    *,
    dir_fd: int | None = None,
    follow_symlinks: bool = True,
) -> None: ...

if sys.platform == "win32" and sys.version_info < (3, 12):
    @overload
    @deprecated(
        "On Windows before Python 3.12, using a PathLike as `cmd` would always fail or return `None`.",
    )
    def which(
        cmd: os.PathLike[str],
        mode: int = 1,
        path: StrPath | None = None,
    ) -> NoReturn: ...

@overload
def which(
    cmd: StrPath,
    mode: int = 1,
    path: StrPath | None = None,
) -> str | None: ...
@overload
def which(
    cmd: bytes,
    mode: int = 1,
    path: StrPath | None = None,
) -> bytes | None: ...
def make_archive(
    base_name: str,
    format: str,
    root_dir: StrPath | None = None,
    base_dir: StrPath | None = None,
    verbose: bool = ...,
    dry_run: bool = ...,
    owner: str | None = None,
    group: str | None = None,
    logger: Any | None = None,
) -> str: ...
def get_archive_formats() -> list[tuple[str, str]]: ...
@overload
def register_archive_format(
    name: str,
    function: Callable[..., object],
    extra_args: Sequence[tuple[str, Any] | list[Any]],
    description: str = "",
) -> None: ...
@overload
def register_archive_format(
    name: str,
    function: Callable[[str, str], object],
    extra_args: None = None,
    description: str = "",
) -> None: ...
def unregister_archive_format(name: str) -> None: ...
def unpack_archive(
    filename: StrPath,
    extract_dir: StrPath | None = None,
    format: str | None = None,
    *,
    filter: _TarfileFilter | None = None,
) -> None: ...
@overload
def register_unpack_format(
    name: str,
    extensions: list[str],
    function: Callable[..., object],
    extra_args: Sequence[tuple[str, Any]],
    description: str = "",
) -> None: ...
@overload
def register_unpack_format(
    name: str,
    extensions: list[str],
    function: Callable[[str, str], object],
    extra_args: None = None,
    description: str = "",
) -> None: ...
def unregister_unpack_format(name: str) -> None: ...
def get_unpack_formats() -> list[tuple[str, list[str], str]]: ...
def get_terminal_size(
    fallback: tuple[int, int] = (80, 24),
) -> os.terminal_size: ...
