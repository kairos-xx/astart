from collections.abc import Callable, Hashable, Iterable, Sequence, Sized
from decimal import Decimal
from fractions import Fraction
from typing import (
    Literal,
    NamedTuple,
    Protocol,
    Self,
    SupportsFloat,
    SupportsIndex,
    TypeVar,
    type_check_only,
)

from _typeshed import SupportsRichComparisonT

__all__ = [
    "NormalDist",
    "StatisticsError",
    "correlation",
    "covariance",
    "fmean",
    "geometric_mean",
    "harmonic_mean",
    "linear_regression",
    "mean",
    "median",
    "median_grouped",
    "median_high",
    "median_low",
    "mode",
    "multimode",
    "pstdev",
    "pvariance",
    "quantiles",
    "stdev",
    "variance",
]
__all__ += ["kde", "kde_random"]
type _Number = float | Decimal | Fraction
_NumberT = TypeVar("_NumberT", float, Decimal, Fraction)
_HashableT = TypeVar("_HashableT", bound=Hashable)
type _Seed = int | float | str | bytes | bytearray
_T_co = TypeVar("_T_co", covariant=True)

@type_check_only
class _SizedIterable(Iterable[_T_co], Sized, Protocol[_T_co]): ...

class StatisticsError(ValueError): ...

def fmean(
    data: Iterable[SupportsFloat],
    weights: Iterable[SupportsFloat] | None = None,
) -> float: ...
def geometric_mean(data: Iterable[SupportsFloat]) -> float: ...
def mean[NumberT: (float, Decimal, Fraction)](
    data: Iterable[_NumberT],
) -> _NumberT: ...
def harmonic_mean[NumberT: (float, Decimal, Fraction)](
    data: Iterable[_NumberT],
    weights: Iterable[_Number] | None = None,
) -> _NumberT: ...
def median[NumberT: (float, Decimal, Fraction)](
    data: Iterable[_NumberT],
) -> _NumberT: ...
def median_low(
    data: Iterable[SupportsRichComparisonT],
) -> SupportsRichComparisonT: ...
def median_high(
    data: Iterable[SupportsRichComparisonT],
) -> SupportsRichComparisonT: ...
def median_grouped(
    data: Iterable[SupportsFloat],
    interval: SupportsFloat = 1.0,
) -> float: ...
def mode[HashableT: Hashable](data: Iterable[_HashableT]) -> _HashableT: ...
def multimode[HashableT: Hashable](
    data: Iterable[_HashableT],
) -> list[_HashableT]: ...
def pstdev(
    data: Iterable[_NumberT],
    mu: _NumberT | None = None,
) -> _NumberT: ...
def pvariance(
    data: Iterable[_NumberT],
    mu: _NumberT | None = None,
) -> _NumberT: ...
def quantiles[NumberT: (float, Decimal, Fraction)](
    data: Iterable[_NumberT],
    *,
    n: int = 4,
    method: Literal["inclusive", "exclusive"] = "exclusive",
) -> list[_NumberT]: ...
def stdev(
    data: Iterable[_NumberT],
    xbar: _NumberT | None = None,
) -> _NumberT: ...
def variance(
    data: Iterable[_NumberT],
    xbar: _NumberT | None = None,
) -> _NumberT: ...

class NormalDist:
    __slots__ = {
        "_mu": "Arithmetic mean of a normal distribution",
        "_sigma": "Standard deviation of a normal distribution",
    }
    def __init__(self, mu: float = 0.0, sigma: float = 1.0) -> None: ...
    @property
    def mean(self) -> float: ...
    @property
    def median(self) -> float: ...
    @property
    def mode(self) -> float: ...
    @property
    def stdev(self) -> float: ...
    @property
    def variance(self) -> float: ...
    @classmethod
    def from_samples(cls, data: Iterable[SupportsFloat]) -> Self: ...
    def samples(
        self,
        n: SupportsIndex,
        *,
        seed: _Seed | None = None,
    ) -> list[float]: ...
    def pdf(self, x: float) -> float: ...
    def cdf(self, x: float) -> float: ...
    def inv_cdf(self, p: float) -> float: ...
    def overlap(self, other: NormalDist) -> float: ...
    def quantiles(self, n: int = 4) -> list[float]: ...
    def zscore(self, x: float) -> float: ...
    def __eq__(self, x2: object) -> bool: ...
    def __add__(self, x2: float | NormalDist) -> NormalDist: ...
    def __sub__(self, x2: float | NormalDist) -> NormalDist: ...
    def __mul__(self, x2: float) -> NormalDist: ...
    def __truediv__(self, x2: float) -> NormalDist: ...
    def __pos__(self) -> NormalDist: ...
    def __neg__(self) -> NormalDist: ...
    __radd__ = __add__
    def __rsub__(self, x2: float | NormalDist) -> NormalDist: ...
    __rmul__ = __mul__
    def __hash__(self) -> int: ...

def correlation(
    x: Sequence[_Number],
    y: Sequence[_Number],
    /,
    *,
    method: Literal["linear", "ranked"] = "linear",
) -> float: ...
def covariance(x: Sequence[_Number], y: Sequence[_Number], /) -> float: ...

class LinearRegression(NamedTuple):
    slope: float
    intercept: float

def linear_regression(
    regressor: _SizedIterable[_Number],
    dependent_variable: _SizedIterable[_Number],
    /,
    *,
    proportional: bool = False,
) -> LinearRegression: ...

type _Kernel = Literal[
    "normal",
    "gauss",
    "logistic",
    "sigmoid",
    "rectangular",
    "uniform",
    "triangular",
    "parabolic",
    "epanechnikov",
    "quartic",
    "biweight",
    "triweight",
    "cosine",
]

def kde(
    data: Sequence[float],
    h: float,
    kernel: _Kernel = "normal",
    *,
    cumulative: bool = False,
) -> Callable[[float], float]: ...
def kde_random(
    data: Sequence[float],
    h: float,
    kernel: _Kernel = "normal",
    *,
    seed: _Seed | None = None,
) -> Callable[[], float]: ...
