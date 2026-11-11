from collections.abc import Callable, Iterable, Iterator
from types import GenericAlias
from typing import (
    Any,
    Literal,
    Self,
    SupportsComplex,
    SupportsFloat,
    SupportsIndex,
    SupportsInt,
    TypeVar,
    overload,
)

from _typeshed import MaybeNone
from typing_extensions import disjoint_base

_T = TypeVar("_T")
_S = TypeVar("_S")
_N = TypeVar(
    "_N",
    int,
    float,
    SupportsFloat,
    SupportsInt,
    SupportsIndex,
    SupportsComplex,
)
_T_co = TypeVar("_T_co", covariant=True)
_S_co = TypeVar("_S_co", covariant=True)
_T1 = TypeVar("_T1")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")
_T4 = TypeVar("_T4")
_T5 = TypeVar("_T5")
_T6 = TypeVar("_T6")
_T7 = TypeVar("_T7")
_T8 = TypeVar("_T8")
_T9 = TypeVar("_T9")
_T10 = TypeVar("_T10")
type _Step = SupportsFloat | SupportsInt | SupportsIndex | SupportsComplex
type _Predicate[_T] = Callable[[_T], object]

@disjoint_base
class count[
    N: (int, float, SupportsFloat, SupportsInt, SupportsIndex, SupportsComplex)
]:
    @overload
    def __new__(cls) -> count[int]: ...
    @overload
    def __new__(cls, start: _N, step: _Step = 1) -> count[_N]: ...
    @overload
    def __new__(cls, *, step: _N) -> count[_N]: ...
    def __next__(self) -> _N: ...
    def __iter__(self) -> Self: ...

@disjoint_base
class cycle[T]:
    def __new__(cls, iterable: Iterable[_T], /) -> Self: ...
    def __next__(self) -> _T: ...
    def __iter__(self) -> Self: ...

@disjoint_base
class repeat[T]:
    @overload
    def __new__(cls, object: _T) -> Self: ...
    @overload
    def __new__(cls, object: _T, times: int) -> Self: ...
    def __next__(self) -> _T: ...
    def __iter__(self) -> Self: ...
    def __length_hint__(self) -> int: ...

@disjoint_base
class accumulate[T]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        func: None = None,
        *,
        initial: _T | None = None,
    ) -> Self: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_S],
        func: Callable[[_T, _S], _T],
        *,
        initial: _T | None = None,
    ) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class chain[T]:
    def __new__(cls, *iterables: Iterable[_T]) -> Self: ...
    def __next__(self) -> _T: ...
    def __iter__(self) -> Self: ...
    @classmethod
    def from_iterable(
        cls: type[Any],
        iterable: Iterable[Iterable[_S]],
        /,
    ) -> chain[_S]: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

@disjoint_base
class compress[T]:
    def __new__(cls, data: Iterable[_T], selectors: Iterable[Any]) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class dropwhile[T]:
    def __new__(
        cls,
        predicate: _Predicate[_T],
        iterable: Iterable[_T],
        /,
    ) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class filterfalse[T]:
    def __new__(
        cls,
        function: _Predicate[_T] | None,
        iterable: Iterable[_T],
        /,
    ) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class groupby[T_co, S_co]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T1],
        key: None = None,
    ) -> groupby[_T1, _T1]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T1],
        key: Callable[[_T1], _T2],
    ) -> groupby[_T2, _T1]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> tuple[_T_co, Iterator[_S_co]]: ...

@disjoint_base
class islice[T]:
    @overload
    def __new__(cls, iterable: Iterable[_T], stop: int | None, /) -> Self: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        start: int | None,
        stop: int | None,
        step: int | None = 1,
        /,
    ) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

@disjoint_base
class starmap[T_co]:
    def __new__(
        cls,
        function: Callable[..., _T],
        iterable: Iterable[Iterable[Any]],
        /,
    ) -> starmap[_T]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class takewhile[T]:
    def __new__(
        cls,
        predicate: _Predicate[_T],
        iterable: Iterable[_T],
        /,
    ) -> Self: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T: ...

def tee[T](
    iterable: Iterable[_T],
    n: int = 2,
    /,
) -> tuple[Iterator[_T], ...]: ...
@disjoint_base
class zip_longest[T_co]:
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        /,
        *,
        fillvalue: object = None,
    ) -> zip_longest[tuple[_T1]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        /,
    ) -> zip_longest[tuple[_T1 | MaybeNone, _T2 | MaybeNone]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        /,
        *,
        fillvalue: _T,
    ) -> zip_longest[tuple[_T1 | _T, _T2 | _T]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        /,
    ) -> zip_longest[
        tuple[_T1 | MaybeNone, _T2 | MaybeNone, _T3 | MaybeNone]
    ]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        /,
        *,
        fillvalue: _T,
    ) -> zip_longest[tuple[_T1 | _T, _T2 | _T, _T3 | _T]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        /,
    ) -> zip_longest[
        tuple[
            _T1 | MaybeNone,
            _T2 | MaybeNone,
            _T3 | MaybeNone,
            _T4 | MaybeNone,
        ]
    ]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        /,
        *,
        fillvalue: _T,
    ) -> zip_longest[tuple[_T1 | _T, _T2 | _T, _T3 | _T, _T4 | _T]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        /,
    ) -> zip_longest[
        tuple[
            _T1 | MaybeNone,
            _T2 | MaybeNone,
            _T3 | MaybeNone,
            _T4 | MaybeNone,
            _T5 | MaybeNone,
        ]
    ]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        /,
        *,
        fillvalue: _T,
    ) -> zip_longest[
        tuple[_T1 | _T, _T2 | _T, _T3 | _T, _T4 | _T, _T5 | _T]
    ]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T],
        iter2: Iterable[_T],
        iter3: Iterable[_T],
        iter4: Iterable[_T],
        iter5: Iterable[_T],
        iter6: Iterable[_T],
        /,
        *iterables: Iterable[_T],
    ) -> zip_longest[tuple[_T | MaybeNone, ...]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T],
        iter2: Iterable[_T],
        iter3: Iterable[_T],
        iter4: Iterable[_T],
        iter5: Iterable[_T],
        iter6: Iterable[_T],
        /,
        *iterables: Iterable[_T],
        fillvalue: _T,
    ) -> zip_longest[tuple[_T, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class product[T_co]:
    @overload
    def __new__(cls, iter1: Iterable[_T1], /) -> product[tuple[_T1]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        /,
    ) -> product[tuple[_T1, _T2]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        /,
    ) -> product[tuple[_T1, _T2, _T3]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        iter6: Iterable[_T6],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5, _T6]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        iter6: Iterable[_T6],
        iter7: Iterable[_T7],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        iter6: Iterable[_T6],
        iter7: Iterable[_T7],
        iter8: Iterable[_T8],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        iter6: Iterable[_T6],
        iter7: Iterable[_T7],
        iter8: Iterable[_T8],
        iter9: Iterable[_T9],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9]]: ...
    @overload
    def __new__(
        cls,
        iter1: Iterable[_T1],
        iter2: Iterable[_T2],
        iter3: Iterable[_T3],
        iter4: Iterable[_T4],
        iter5: Iterable[_T5],
        iter6: Iterable[_T6],
        iter7: Iterable[_T7],
        iter8: Iterable[_T8],
        iter9: Iterable[_T9],
        iter10: Iterable[_T10],
        /,
    ) -> product[tuple[_T1, _T2, _T3, _T4, _T5, _T6, _T7, _T8, _T9, _T10]]: ...
    @overload
    def __new__(
        cls,
        *iterables: Iterable[_T1],
        repeat: int = 1,
    ) -> product[tuple[_T1, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class permutations[T_co]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[2],
    ) -> permutations[tuple[_T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[3],
    ) -> permutations[tuple[_T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[4],
    ) -> permutations[tuple[_T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[5],
    ) -> permutations[tuple[_T, _T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: int | None = None,
    ) -> permutations[tuple[_T, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class combinations[T_co]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[2],
    ) -> combinations[tuple[_T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[3],
    ) -> combinations[tuple[_T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[4],
    ) -> combinations[tuple[_T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[5],
    ) -> combinations[tuple[_T, _T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: int,
    ) -> combinations[tuple[_T, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class combinations_with_replacement[T_co]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[2],
    ) -> combinations_with_replacement[tuple[_T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[3],
    ) -> combinations_with_replacement[tuple[_T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[4],
    ) -> combinations_with_replacement[tuple[_T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: Literal[5],
    ) -> combinations_with_replacement[tuple[_T, _T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        r: int,
    ) -> combinations_with_replacement[tuple[_T, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class pairwise[T_co]:
    def __new__(cls, iterable: Iterable[_T], /) -> pairwise[tuple[_T, _T]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...

@disjoint_base
class batched[T_co]:
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: Literal[1],
        *,
        strict: Literal[True],
    ) -> batched[tuple[_T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: Literal[2],
        *,
        strict: Literal[True],
    ) -> batched[tuple[_T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: Literal[3],
        *,
        strict: Literal[True],
    ) -> batched[tuple[_T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: Literal[4],
        *,
        strict: Literal[True],
    ) -> batched[tuple[_T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: Literal[5],
        *,
        strict: Literal[True],
    ) -> batched[tuple[_T, _T, _T, _T, _T]]: ...
    @overload
    def __new__(
        cls,
        iterable: Iterable[_T],
        n: int,
        *,
        strict: bool = False,
    ) -> batched[tuple[_T, ...]]: ...
    def __iter__(self) -> Self: ...
    def __next__(self) -> _T_co: ...
