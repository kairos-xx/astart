from collections.abc import Collection
from typing import Any, Protocol, TypeVar, type_check_only

import numpy as np

_GenericT_co = TypeVar("_GenericT_co", bound=np.generic, covariant=True)
_ShapeT_co = TypeVar(
    "_ShapeT_co",
    bound=tuple[int, ...],
    default=Any,
    covariant=True,
)

@type_check_only
class SupportsArray(Protocol[_GenericT_co, _ShapeT_co]):
    def __array__(self) -> np.ndarray[_ShapeT_co, np.dtype[_GenericT_co]]: ...

type ArrayLike1D[
    _ScalarT: bool | int | float | complex | str | bytes | np.generic,
    _GenericT: np.generic,
] = Collection[_ScalarT] | SupportsArray[_GenericT, tuple[int]]
type Array1D[_GenericT: np.generic] = np.ndarray[
    tuple[int],
    np.dtype[_GenericT],
]
type Array2D[_GenericT: np.generic] = np.ndarray[
    tuple[int, int],
    np.dtype[_GenericT],
]
type Seed = int | np.random.Generator | np.random.RandomState
