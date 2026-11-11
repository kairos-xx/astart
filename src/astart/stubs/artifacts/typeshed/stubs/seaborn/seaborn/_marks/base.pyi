from dataclasses import dataclass
from typing import Any, TypeVar

from _typeshed import Incomplete
from numpy.typing import NDArray
from pandas import DataFrame
from seaborn._core.properties import (
    DashPattern,
    DashPatternWithOffset,
    RGBATuple,
)
from seaborn._core.scales import Scale

_MarkT = TypeVar("_MarkT", bound=type[Mark])

class Mappable:
    def __init__(
        self,
        val: Any = None,
        depend: str | None = None,
        rc: str | None = None,
        auto: bool = False,
        grouping: bool = True,
    ) -> None: ...
    @property
    def depend(self) -> Any: ...
    @property
    def grouping(self) -> bool: ...
    @property
    def default(self) -> Any: ...

type MappableBool = bool | Mappable
type MappableString = str | Mappable
type MappableFloat = float | Mappable
type MappableColor = str | tuple[Incomplete, ...] | Mappable
type MappableStyle = str | DashPattern | DashPatternWithOffset | Mappable

@dataclass
class Mark:
    artist_kws: dict[str, Any] = ...

def resolve_properties(
    mark: Mark,
    data: DataFrame,
    scales: dict[str, Scale],
) -> dict[str, Any]: ...
def resolve_color(
    mark: Mark,
    data: DataFrame | dict[str, Any],
    prefix: str = "",
    scales: dict[str, Scale] | None = None,
) -> RGBATuple | NDArray[Incomplete]: ...
def document_properties[MarkT: type[Mark]](mark: _MarkT) -> _MarkT: ...
