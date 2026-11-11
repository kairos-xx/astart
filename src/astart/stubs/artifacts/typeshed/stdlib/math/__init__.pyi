import sys
from collections.abc import Iterable
from typing import (
    Any,
    Final,
    Literal,
    Protocol,
    SupportsFloat,
    SupportsIndex,
    TypeVar,
    overload,
    type_check_only,
)

from _typeshed import SupportsMul, SupportsRMul

_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
type _SupportsFloatOrIndex = SupportsFloat | SupportsIndex
e: Final[float]
pi: Final[float]
inf: Final[float]
nan: Final[float]
tau: Final[float]

def acos(x: _SupportsFloatOrIndex, /) -> float: ...
def acosh(x: _SupportsFloatOrIndex, /) -> float: ...
def asin(x: _SupportsFloatOrIndex, /) -> float: ...
def asinh(x: _SupportsFloatOrIndex, /) -> float: ...
def atan(x: _SupportsFloatOrIndex, /) -> float: ...
def atan2(y: _SupportsFloatOrIndex, x: _SupportsFloatOrIndex, /) -> float: ...
def atanh(x: _SupportsFloatOrIndex, /) -> float: ...
def cbrt(x: _SupportsFloatOrIndex, /) -> float: ...
@type_check_only
class _SupportsCeil(Protocol[_T_co]):
    def __ceil__(self) -> _T_co: ...

@overload
def ceil[T](x: _SupportsCeil[_T], /) -> _T: ...
@overload
def ceil(x: _SupportsFloatOrIndex, /) -> int: ...
def comb(n: SupportsIndex, k: SupportsIndex, /) -> int: ...
def copysign(
    x: _SupportsFloatOrIndex,
    y: _SupportsFloatOrIndex,
    /,
) -> float: ...
def cos(x: _SupportsFloatOrIndex, /) -> float: ...
def cosh(x: _SupportsFloatOrIndex, /) -> float: ...
def degrees(x: _SupportsFloatOrIndex, /) -> float: ...
def dist(
    p: Iterable[_SupportsFloatOrIndex],
    q: Iterable[_SupportsFloatOrIndex],
    /,
) -> float: ...
def erf(x: _SupportsFloatOrIndex, /) -> float: ...
def erfc(x: _SupportsFloatOrIndex, /) -> float: ...
def exp(x: _SupportsFloatOrIndex, /) -> float: ...
def exp2(x: _SupportsFloatOrIndex, /) -> float: ...
def expm1(x: _SupportsFloatOrIndex, /) -> float: ...
def fabs(x: _SupportsFloatOrIndex, /) -> float: ...
def factorial(x: SupportsIndex, /) -> int: ...
@type_check_only
class _SupportsFloor(Protocol[_T_co]):
    def __floor__(self) -> _T_co: ...

@overload
def floor[T](x: _SupportsFloor[_T], /) -> _T: ...
@overload
def floor(x: _SupportsFloatOrIndex, /) -> int: ...
def fmod(x: _SupportsFloatOrIndex, y: _SupportsFloatOrIndex, /) -> float: ...

if sys.version_info >= (3, 15):
    def fmax(
        x: _SupportsFloatOrIndex,
        y: _SupportsFloatOrIndex,
        /,
    ) -> float: ...
    def fmin(
        x: _SupportsFloatOrIndex,
        y: _SupportsFloatOrIndex,
        /,
    ) -> float: ...

def frexp(x: _SupportsFloatOrIndex, /) -> tuple[float, int]: ...
def fsum(seq: Iterable[_SupportsFloatOrIndex], /) -> float: ...
def gamma(x: _SupportsFloatOrIndex, /) -> float: ...
def gcd(*integers: SupportsIndex) -> int: ...
def hypot(*coordinates: _SupportsFloatOrIndex) -> float: ...
def isclose(
    a: _SupportsFloatOrIndex,
    b: _SupportsFloatOrIndex,
    *,
    rel_tol: _SupportsFloatOrIndex = 1e-09,
    abs_tol: _SupportsFloatOrIndex = 0.0,
) -> bool: ...
def isinf(x: _SupportsFloatOrIndex, /) -> bool: ...
def isfinite(x: _SupportsFloatOrIndex, /) -> bool: ...
def isnan(x: _SupportsFloatOrIndex, /) -> bool: ...

if sys.version_info >= (3, 15):
    def isnormal(x: _SupportsFloatOrIndex, /) -> bool: ...
    def issubnormal(x: _SupportsFloatOrIndex, /) -> bool: ...

def isqrt(n: SupportsIndex, /) -> int: ...
def lcm(*integers: SupportsIndex) -> int: ...
def ldexp(x: _SupportsFloatOrIndex, i: int, /) -> float: ...
def lgamma(x: _SupportsFloatOrIndex, /) -> float: ...
def log(
    x: _SupportsFloatOrIndex,
    base: _SupportsFloatOrIndex = ...,
) -> float: ...
def log10(x: _SupportsFloatOrIndex, /) -> float: ...
def log1p(x: _SupportsFloatOrIndex, /) -> float: ...
def log2(x: _SupportsFloatOrIndex, /) -> float: ...
def modf(x: _SupportsFloatOrIndex, /) -> tuple[float, float]: ...
def nextafter(
    x: _SupportsFloatOrIndex,
    y: _SupportsFloatOrIndex,
    /,
    *,
    steps: SupportsIndex | None = None,
) -> float: ...
def perm(n: SupportsIndex, k: SupportsIndex | None = None, /) -> int: ...
def pow(x: _SupportsFloatOrIndex, y: _SupportsFloatOrIndex, /) -> float: ...

type _PositiveInteger = Literal[
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
]
type _NegativeInteger = Literal[
    -1,
    -2,
    -3,
    -4,
    -5,
    -6,
    -7,
    -8,
    -9,
    -10,
    -11,
    -12,
    -13,
    -14,
    -15,
    -16,
    -17,
    -18,
    -19,
    -20,
]
type _LiteralInteger = (
    _PositiveInteger | _NegativeInteger | Literal[0]
)  # TODO: Use TypeAlias once mypy bugs are fixed
_MultiplicableT1 = TypeVar("_MultiplicableT1", bound=SupportsMul[Any, Any])
_MultiplicableT2 = TypeVar("_MultiplicableT2", bound=SupportsMul[Any, Any])

@type_check_only
class _SupportsProdWithNoDefaultGiven(
    SupportsMul[Any, Any],
    SupportsRMul[int, Any],
    Protocol,
): ...

_SupportsProdNoDefaultT = TypeVar(
    "_SupportsProdNoDefaultT",
    bound=_SupportsProdWithNoDefaultGiven,
)

@overload
def prod(
    iterable: Iterable[bool | _LiteralInteger],
    /,
    *,
    start: int = 1,
) -> int: ...
@overload
def prod[SupportsProdNoDefaultT: _SupportsProdWithNoDefaultGiven](
    iterable: Iterable[_SupportsProdNoDefaultT],
    /,
) -> _SupportsProdNoDefaultT | Literal[1]: ...
@overload
def prod[
    MultiplicableT1: SupportsMul[Any, Any],
    MultiplicableT2: SupportsMul[Any, Any],
](
    iterable: Iterable[_MultiplicableT1],
    /,
    *,
    start: _MultiplicableT2,
) -> _MultiplicableT1 | _MultiplicableT2: ...
def radians(x: _SupportsFloatOrIndex, /) -> float: ...
def remainder(
    x: _SupportsFloatOrIndex,
    y: _SupportsFloatOrIndex,
    /,
) -> float: ...
def sin(x: _SupportsFloatOrIndex, /) -> float: ...

if sys.version_info >= (3, 15):
    def signbit(x: _SupportsFloatOrIndex, /) -> bool: ...

def sinh(x: _SupportsFloatOrIndex, /) -> float: ...
def sumprod(p: Iterable[float], q: Iterable[float], /) -> float: ...
def sqrt(x: _SupportsFloatOrIndex, /) -> float: ...
def tan(x: _SupportsFloatOrIndex, /) -> float: ...
def tanh(x: _SupportsFloatOrIndex, /) -> float: ...
@type_check_only
class _SupportsTrunc(Protocol[_T_co]):
    def __trunc__(self) -> _T_co: ...

def trunc[T](x: _SupportsTrunc[_T], /) -> _T: ...
def ulp(x: _SupportsFloatOrIndex, /) -> float: ...
def fma(
    x: _SupportsFloatOrIndex,
    y: _SupportsFloatOrIndex,
    z: _SupportsFloatOrIndex,
    /,
) -> float: ...
