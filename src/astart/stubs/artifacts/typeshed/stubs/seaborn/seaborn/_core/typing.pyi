from collections.abc import Iterable, Mapping
from datetime import date, datetime, timedelta
from typing import Any, Protocol, type_check_only

from _typeshed import Incomplete
from matplotlib.colors import Colormap, Normalize
from numpy import ndarray
from pandas import DataFrame, Index, Series, Timedelta, Timestamp

@type_check_only
class SupportsDataFrame(Protocol):
    def __dataframe__(
        self,
        nan_as_null: bool = ...,
        allow_copy: bool = ...,
    ): ...

type ColumnName = (
    str
    | bytes
    | date
    | datetime
    | timedelta
    | bool
    | complex
    | Timestamp
    | Timedelta
)
type Vector = Series[Any] | Index[Any] | ndarray[Any, Any]
type VariableSpec = ColumnName | Vector | None
type VariableSpecList = list[VariableSpec] | Index[Any] | None
type DataSource = (
    DataFrame | SupportsDataFrame | Mapping[Any, Incomplete] | None
)
type OrderSpec = Iterable[str] | None
type NormSpec = tuple[float | None, float | None] | Normalize | None
type PaletteSpec = (
    str | list[Incomplete] | dict[Incomplete, Incomplete] | Colormap | None
)
type DiscreteValueSpec = dict[Incomplete, Incomplete] | list[Incomplete] | None
type ContinuousValueSpec = (
    tuple[float, float] | list[float] | dict[Any, float] | None
)

class Default: ...
class Deprecated: ...

default: Default
deprecated: Deprecated
