from collections.abc import Callable, Hashable, Mapping
from typing import Concatenate, ParamSpec

from _typeshed import Incomplete
from numpy import ufunc
from pandas import DataFrame

type _AggFuncTypeBase = Callable[..., Incomplete] | str | ufunc
type _AggFuncTypeDictFrame = Mapping[
    Hashable,
    _AggFuncTypeBase | list[_AggFuncTypeBase],
]
type _AggFuncTypeFrame = (
    _AggFuncTypeBase | list[_AggFuncTypeBase] | _AggFuncTypeDictFrame
)
_P = ParamSpec("_P")

class GroupBy:
    order: dict[str, list[Incomplete] | None]
    def __init__(
        self,
        order: list[str] | dict[str, list[Incomplete] | None],
    ) -> None: ...
    def agg(
        self,
        data: DataFrame,
        func: _AggFuncTypeFrame = ...,
        *args,
        engine: str | None = None,
        engine_kwargs: dict[str, bool] | None = None,
        **kwargs,
    ) -> DataFrame: ...
    def apply(
        self,
        data: DataFrame,
        func: Callable[Concatenate[DataFrame, _P], DataFrame],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> DataFrame: ...
