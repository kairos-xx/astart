import sys
from typing import (
    Any,
    Final,
    Literal,
    Protocol,
    SupportsFloat,
    SupportsIndex,
    final,
    type_check_only,
)

from _typeshed import structseq

type _TimeTuple = tuple[int, int, int, int, int, int, int, int, int]
if sys.version_info >= (3, 15):
    type _SupportsFloatOrIndex = SupportsFloat | SupportsIndex
else:
    type _SupportsFloatOrIndex = float | SupportsIndex
altzone: int
daylight: int
timezone: int
tzname: tuple[str, str]
if sys.platform == "linux":
    CLOCK_BOOTTIME: Final[int]
if (
    sys.platform != "linux"
    and sys.platform != "win32"
    and sys.platform != "darwin"
):
    CLOCK_PROF: Final[int]
    CLOCK_UPTIME: Final[int]
if sys.platform != "win32":
    CLOCK_MONOTONIC: Final[int]
    CLOCK_MONOTONIC_RAW: Final[int]
    CLOCK_PROCESS_CPUTIME_ID: Final[int]
    CLOCK_REALTIME: Final[int]
    CLOCK_THREAD_CPUTIME_ID: Final[int]
    if sys.platform != "linux" and sys.platform != "darwin":
        CLOCK_HIGHRES: Final[int]
if sys.platform == "darwin":
    CLOCK_UPTIME_RAW: Final[int]
    CLOCK_UPTIME_RAW_APPROX: Final[int]
    CLOCK_MONOTONIC_RAW_APPROX: Final[int]
if sys.platform == "linux":
    CLOCK_TAI: Final[int]

@final
class struct_time(structseq[Any | int], _TimeTuple):
    __match_args__: Final = (
        "tm_year",
        "tm_mon",
        "tm_mday",
        "tm_hour",
        "tm_min",
        "tm_sec",
        "tm_wday",
        "tm_yday",
        "tm_isdst",
    )
    @property
    def tm_year(self) -> int: ...
    @property
    def tm_mon(self) -> int: ...
    @property
    def tm_mday(self) -> int: ...
    @property
    def tm_hour(self) -> int: ...
    @property
    def tm_min(self) -> int: ...
    @property
    def tm_sec(self) -> int: ...
    @property
    def tm_wday(self) -> int: ...
    @property
    def tm_yday(self) -> int: ...
    @property
    def tm_isdst(self) -> int: ...
    @property
    def tm_zone(self) -> str: ...
    @property
    def tm_gmtoff(self) -> int: ...

def asctime(time_tuple: _TimeTuple | struct_time = ..., /) -> str: ...
def ctime(seconds: _SupportsFloatOrIndex | None = None, /) -> str: ...
def gmtime(seconds: _SupportsFloatOrIndex | None = None, /) -> struct_time: ...
def localtime(
    seconds: _SupportsFloatOrIndex | None = None,
    /,
) -> struct_time: ...
def mktime(time_tuple: _TimeTuple | struct_time, /) -> float: ...
def sleep(seconds: _SupportsFloatOrIndex, /) -> None: ...
def strftime(
    format: str,
    time_tuple: _TimeTuple | struct_time = ...,
    /,
) -> str: ...
def strptime(
    data_string: str,
    format: str = "%a %b %d %H:%M:%S %Y",
    /,
) -> struct_time: ...
def time() -> float: ...

if sys.platform != "win32":
    def tzset() -> None: ...

@type_check_only
class _ClockInfo(Protocol):
    adjustable: bool
    implementation: str
    monotonic: bool
    resolution: float

def get_clock_info(
    name: Literal[
        "monotonic",
        "perf_counter",
        "process_time",
        "time",
        "thread_time",
    ],
    /,
) -> _ClockInfo: ...
def monotonic() -> float: ...
def perf_counter() -> float: ...
def process_time() -> float: ...

if sys.platform != "win32":
    def clock_getres(clk_id: int, /) -> float: ...
    def clock_gettime(clk_id: int, /) -> float: ...
    def clock_settime(clk_id: int, time: float, /) -> None: ...

if sys.platform != "win32":
    def clock_gettime_ns(clk_id: int, /) -> int: ...
    def clock_settime_ns(clock_id: int, time: int, /) -> int: ...

if sys.platform == "linux":
    def pthread_getcpuclockid(thread_id: int, /) -> int: ...

def monotonic_ns() -> int: ...
def perf_counter_ns() -> int: ...
def process_time_ns() -> int: ...
def time_ns() -> int: ...
def thread_time() -> float: ...
def thread_time_ns() -> int: ...
