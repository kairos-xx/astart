from collections.abc import Buffer, Sequence
from typing import (
    Any,
    Literal,
    Protocol,
    TypedDict,
    TypeVar,
    type_check_only,
)

import numpy as np
import numpy.typing as npt
from _typeshed import SupportsWrite as SupportsWrite

from .lib import Geometry

_T_co = TypeVar("_T_co", covariant=True)
_DType_co = TypeVar("_DType_co", covariant=True, bound=np.dtype[Any])
GeoT = TypeVar("GeoT", bound=Geometry)
OptGeoT = TypeVar("OptGeoT", bound=Geometry | None)

@type_check_only
class SupportsArray(Protocol[_DType_co]):
    def __array__(self) -> np.ndarray[Any, _DType_co]: ...

type NestedSequence[_T] = (
    Sequence[_T] | Sequence[Sequence[_T]] | Sequence[Sequence[Sequence[_T]]]
)
type DualArrayLike[_DType: np.dtype[Any], _T] = (
    SupportsArray[_DType]
    | NestedSequence[SupportsArray[_DType]]
    | NestedSequence[_T]
)
type ArrayLikeSeq[_T] = Buffer | DualArrayLike[np.dtype[Any], _T]
type GeoArrayLikeSeq = ArrayLikeSeq[Geometry]
type OptGeoArrayLikeSeq = ArrayLikeSeq[Geometry | None]
type ArrayLike[_T] = _T | ArrayLikeSeq[_T]
type GeoArrayLike = ArrayLike[Geometry]
type OptGeoArrayLike = ArrayLike[Geometry | None]
type GeoArray = npt.NDArray[np.object_]

@type_check_only
class SupportsGeoInterface(Protocol):
    @property
    def __geo_interface__(self) -> dict[str, Any]: ...

@type_check_only
class SupportsRead(Protocol[_T_co]):
    def read(self) -> _T_co: ...

type CastingKind = Literal["no", "equiv", "safe", "same_kind", "unsafe"]
type OrderKind = Literal["K", "A", "C", "F"]

@type_check_only
class _UFuncKwargsBase(TypedDict, total=False):
    where: npt.ArrayLike
    casting: CastingKind
    order: OrderKind
    dtype: np.dtype[Any] | type[Any]
    subok: bool

@type_check_only
class UFuncKwargs(_UFuncKwargsBase, total=False):
    out: npt.NDArray[Any] | tuple[npt.NDArray[Any], ...]

@type_check_only
class UFuncKwargsNoOut(_UFuncKwargsBase, total=False): ...
