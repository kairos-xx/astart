from collections.abc import Callable, Iterable
from typing import Protocol, type_check_only

from ..base import _ConvertibleToGeoSeries
from ..geodataframe import GeoDataFrame

@type_check_only
class _GeoCoder(Protocol):
    def geocode(self, query: str, /): ...
    def reverse(self, coords, /, exactly_one: bool = ...): ...

def geocode(
    strings: Iterable[str],
    provider: str | Callable[..., _GeoCoder] | None = None,
    **kwargs,
) -> GeoDataFrame: ...
def reverse_geocode(
    points: _ConvertibleToGeoSeries,
    provider: str | Callable[..., _GeoCoder] | None = None,
    **kwargs,
) -> GeoDataFrame: ...
