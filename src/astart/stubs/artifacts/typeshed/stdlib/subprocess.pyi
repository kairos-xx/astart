import sys
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from types import GenericAlias, TracebackType
from typing import (
    IO,
    Any,
    AnyStr,
    Final,
    Literal,
    Self,
    TypeVar,
    overload,
)

from _typeshed import MaybeNone, ReadableBuffer, StrOrBytesPath

__all__ = [
    "DEVNULL",
    "PIPE",
    "STDOUT",
    "CalledProcessError",
    "CompletedProcess",
    "Popen",
    "SubprocessError",
    "TimeoutExpired",
    "call",
    "check_call",
    "check_output",
    "getoutput",
    "getstatusoutput",
    "run",
]
if sys.platform == "win32":
    __all__ += [
        "ABOVE_NORMAL_PRIORITY_CLASS",
        "BELOW_NORMAL_PRIORITY_CLASS",
        "CREATE_BREAKAWAY_FROM_JOB",
        "CREATE_DEFAULT_ERROR_MODE",
        "CREATE_NEW_CONSOLE",
        "CREATE_NEW_PROCESS_GROUP",
        "CREATE_NO_WINDOW",
        "DETACHED_PROCESS",
        "HIGH_PRIORITY_CLASS",
        "IDLE_PRIORITY_CLASS",
        "NORMAL_PRIORITY_CLASS",
        "REALTIME_PRIORITY_CLASS",
        "STARTF_USESHOWWINDOW",
        "STARTF_USESTDHANDLES",
        "STARTUPINFO",
        "STD_ERROR_HANDLE",
        "STD_INPUT_HANDLE",
        "STD_OUTPUT_HANDLE",
        "SW_HIDE",
    ]
type _FILE = None | int | IO[Any]
type _InputString = ReadableBuffer | str
type _CMD = StrOrBytesPath | Sequence[StrOrBytesPath]
if sys.platform == "win32":
    type _ENV = Mapping[str, str]
else:
    type _ENV = Mapping[bytes, StrOrBytesPath] | Mapping[str, StrOrBytesPath]
_T = TypeVar("_T")
_USE_VFORK: Final[bool]
_USE_POSIX_SPAWN: Final[bool]

class CompletedProcess[T]:
    args: Any
    returncode: int
    stdout: _T
    stderr: _T
    def __init__(
        self,
        args: _CMD,
        returncode: int,
        stdout: _T | None = None,
        stderr: _T | None = None,
    ) -> None: ...
    def check_returncode(self) -> None: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: Literal[True] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    capture_output: bool = False,
    check: bool = False,
    encoding: str | None = None,
    errors: str | None = None,
    input: str | None = None,
    text: Literal[True],
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[str]: ...
@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    capture_output: bool = False,
    check: bool = False,
    encoding: str,
    errors: str | None = None,
    input: str | None = None,
    text: bool | None = None,
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[str]: ...
@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    capture_output: bool = False,
    check: bool = False,
    encoding: str | None = None,
    errors: str,
    input: str | None = None,
    text: bool | None = None,
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[str]: ...
@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    *,
    universal_newlines: Literal[True],
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    capture_output: bool = False,
    check: bool = False,
    encoding: str | None = None,
    errors: str | None = None,
    input: str | None = None,
    text: Literal[True] | None = None,
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[str]: ...
@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: Literal[False] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    capture_output: bool = False,
    check: bool = False,
    encoding: None = None,
    errors: None = None,
    input: ReadableBuffer | None = None,
    text: Literal[False] | None = None,
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[bytes]: ...
@overload
def run(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    capture_output: bool = False,
    check: bool = False,
    encoding: str | None = None,
    errors: str | None = None,
    input: _InputString | None = None,
    text: bool | None = None,
    timeout: float | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> CompletedProcess[Any]: ...
def call(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    encoding: str | None = None,
    timeout: float | None = None,
    text: bool | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> int: ...
def check_call(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stdout: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    timeout: float | None = None,
    *,
    encoding: str | None = None,
    text: bool | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> int: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: Literal[True] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: str | None = None,
    errors: str | None = None,
    text: Literal[True],
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> str: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: str,
    errors: str | None = None,
    text: bool | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> str: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: str | None = None,
    errors: str,
    text: bool | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> str: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    *,
    universal_newlines: Literal[True],
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: str | None = None,
    errors: str | None = None,
    text: Literal[True] | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> str: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: Literal[False] | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: None = None,
    errors: None = None,
    text: Literal[False] | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> bytes: ...
@overload
def check_output(
    args: _CMD,
    bufsize: int = -1,
    executable: StrOrBytesPath | None = None,
    stdin: _FILE = None,
    stderr: _FILE = None,
    preexec_fn: Callable[[], object] | None = None,
    close_fds: bool = True,
    shell: bool = False,
    cwd: StrOrBytesPath | None = None,
    env: _ENV | None = None,
    universal_newlines: bool | None = None,
    startupinfo: Any = None,
    creationflags: int = 0,
    restore_signals: bool = True,
    start_new_session: bool = False,
    pass_fds: Collection[int] = (),
    *,
    timeout: float | None = None,
    input: _InputString | None = None,
    encoding: str | None = None,
    errors: str | None = None,
    text: bool | None = None,
    user: str | int | None = None,
    group: str | int | None = None,
    extra_groups: Iterable[str | int] | None = None,
    umask: int = -1,
    pipesize: int = -1,
    process_group: int | None = None,
) -> Any: ...

PIPE: Final[int]
STDOUT: Final[int]
DEVNULL: Final[int]

class SubprocessError(Exception): ...

class TimeoutExpired(SubprocessError):
    def __init__(
        self,
        cmd: _CMD,
        timeout: float,
        output: str | bytes | None = None,
        stderr: str | bytes | None = None,
    ) -> None: ...
    cmd: Any
    timeout: float
    output: Any
    stdout: bytes | None
    stderr: bytes | None

class CalledProcessError(SubprocessError):
    returncode: int
    cmd: Any
    output: Any
    stdout: Any
    stderr: Any
    def __init__(
        self,
        returncode: int,
        cmd: _CMD,
        output: str | bytes | None = None,
        stderr: str | bytes | None = None,
    ) -> None: ...

class Popen[AnyStr: (bytes, str)]:
    args: _CMD
    stdin: IO[Any] | None
    stdout: IO[Any] | None
    stderr: IO[Any] | None
    pid: int
    returncode: int | MaybeNone
    universal_newlines: bool
    @overload
    def __init__(
        self: Popen[str],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        universal_newlines: bool | None = None,
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        *,
        text: bool | None = None,
        encoding: str,
        errors: str | None = None,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Popen[str],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        universal_newlines: bool | None = None,
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        *,
        text: bool | None = None,
        encoding: str | None = None,
        errors: str,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Popen[str],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        *,
        universal_newlines: Literal[True],
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        text: bool | None = None,
        encoding: str | None = None,
        errors: str | None = None,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Popen[str],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        universal_newlines: Literal[True] | None = None,
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        *,
        text: Literal[True],
        encoding: str | None = None,
        errors: str | None = None,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Popen[bytes],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        universal_newlines: Literal[False] | None = None,
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        *,
        text: Literal[False] | None = None,
        encoding: None = None,
        errors: None = None,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    @overload
    def __init__(
        self: Popen[Any],
        args: _CMD,
        bufsize: int = -1,
        executable: StrOrBytesPath | None = None,
        stdin: _FILE | None = None,
        stdout: _FILE | None = None,
        stderr: _FILE | None = None,
        preexec_fn: Callable[[], object] | None = None,
        close_fds: bool = True,
        shell: bool = False,
        cwd: StrOrBytesPath | None = None,
        env: _ENV | None = None,
        universal_newlines: bool | None = None,
        startupinfo: Any | None = None,
        creationflags: int = 0,
        restore_signals: bool = True,
        start_new_session: bool = False,
        pass_fds: Collection[int] = (),
        *,
        text: bool | None = None,
        encoding: str | None = None,
        errors: str | None = None,
        user: str | int | None = None,
        group: str | int | None = None,
        extra_groups: Iterable[str | int] | None = None,
        umask: int = -1,
        pipesize: int = -1,
        process_group: int | None = None,
    ) -> None: ...
    def poll(self) -> int | None: ...
    def wait(self, timeout: float | None = None) -> int: ...
    def communicate(
        self,
        input: AnyStr | None = None,
        timeout: float | None = None,
    ) -> tuple[AnyStr, AnyStr]: ...
    def send_signal(self, sig: int) -> None: ...
    def terminate(self) -> None: ...
    def kill(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def __del__(self) -> None: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

def getstatusoutput(
    cmd: _CMD,
    *,
    encoding: str | None = None,
    errors: str | None = None,
) -> tuple[int, str]: ...
def getoutput(
    cmd: _CMD,
    *,
    encoding: str | None = None,
    errors: str | None = None,
) -> str: ...
def list2cmdline(seq: Iterable[StrOrBytesPath]) -> str: ...

if sys.platform == "win32":
    from _winapi import STARTF_FORCEOFFFEEDBACK, STARTF_FORCEONFEEDBACK

    __all__ += ["STARTF_FORCEOFFFEEDBACK", "STARTF_FORCEONFEEDBACK"]
    class STARTUPINFO:
        def __init__(
            self,
            *,
            dwFlags: int = 0,
            hStdInput: Any | None = None,
            hStdOutput: Any | None = None,
            hStdError: Any | None = None,
            wShowWindow: int = 0,
            lpAttributeList: Mapping[str, Any] | None = None,
        ) -> None: ...
        dwFlags: int
        hStdInput: Any | None
        hStdOutput: Any | None
        hStdError: Any | None
        wShowWindow: int
        lpAttributeList: Mapping[str, Any]
        def copy(self) -> STARTUPINFO: ...

    from _winapi import (
        ABOVE_NORMAL_PRIORITY_CLASS as ABOVE_NORMAL_PRIORITY_CLASS,
    )
    from _winapi import (
        BELOW_NORMAL_PRIORITY_CLASS as BELOW_NORMAL_PRIORITY_CLASS,
    )
    from _winapi import (
        CREATE_BREAKAWAY_FROM_JOB as CREATE_BREAKAWAY_FROM_JOB,
    )
    from _winapi import (
        CREATE_DEFAULT_ERROR_MODE as CREATE_DEFAULT_ERROR_MODE,
    )
    from _winapi import (
        CREATE_NEW_CONSOLE as CREATE_NEW_CONSOLE,
    )
    from _winapi import (
        CREATE_NEW_PROCESS_GROUP as CREATE_NEW_PROCESS_GROUP,
    )
    from _winapi import (
        CREATE_NO_WINDOW as CREATE_NO_WINDOW,
    )
    from _winapi import (
        DETACHED_PROCESS as DETACHED_PROCESS,
    )
    from _winapi import (
        HIGH_PRIORITY_CLASS as HIGH_PRIORITY_CLASS,
    )
    from _winapi import (
        IDLE_PRIORITY_CLASS as IDLE_PRIORITY_CLASS,
    )
    from _winapi import (
        NORMAL_PRIORITY_CLASS as NORMAL_PRIORITY_CLASS,
    )
    from _winapi import (
        REALTIME_PRIORITY_CLASS as REALTIME_PRIORITY_CLASS,
    )
    from _winapi import (
        STARTF_USESHOWWINDOW as STARTF_USESHOWWINDOW,
    )
    from _winapi import (
        STARTF_USESTDHANDLES as STARTF_USESTDHANDLES,
    )
    from _winapi import (
        STD_ERROR_HANDLE as STD_ERROR_HANDLE,
    )
    from _winapi import (
        STD_INPUT_HANDLE as STD_INPUT_HANDLE,
    )
    from _winapi import (
        STD_OUTPUT_HANDLE as STD_OUTPUT_HANDLE,
    )
    from _winapi import (
        SW_HIDE as SW_HIDE,
    )
