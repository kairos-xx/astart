import sys
from collections.abc import (
    Awaitable,
    Buffer,
    Callable,
    Iterable,
    Iterator,
    Sequence,
    Sized,
)
from collections.abc import Set as AbstractSet
from dataclasses import Field
from os import PathLike
from types import FrameType, TracebackType
from types import NoneType as NoneType
from typing import (
    Any,
    ClassVar,
    Final,
    Literal,
    LiteralString,
    Protocol,
    SupportsFloat,
    SupportsIndex,
    SupportsInt,
    TypeVar,
    overload,
)
from typing import Self as _Self

_KT = TypeVar("_KT")
_KT_co = TypeVar("_KT_co", covariant=True)
_KT_contra = TypeVar("_KT_contra", contravariant=True)
_VT = TypeVar("_VT")
_VT_co = TypeVar("_VT_co", covariant=True)
_T = TypeVar("_T")
_T_co = TypeVar("_T_co", covariant=True)
_T_contra = TypeVar("_T_contra", contravariant=True)
Self = TypeVar("Self")
AnyStr_co = TypeVar("AnyStr_co", str, bytes, covariant=True)
type Incomplete = Any
type Unused = object
type MaybeNone = Any
sentinel: Any

class IdentityFunction(Protocol):
    def __call__(self, x: _T, /) -> _T: ...

class SupportsNext(Protocol[_T_co]):
    def __next__(self) -> _T_co: ...

class SupportsAnext(Protocol[_T_co]):
    def __anext__(self) -> Awaitable[_T_co]: ...

class SupportsBool(Protocol):
    def __bool__(self) -> bool: ...

class SupportsDunderLT(Protocol[_T_contra]):
    def __lt__(self, other: _T_contra, /) -> SupportsBool: ...

class SupportsDunderGT(Protocol[_T_contra]):
    def __gt__(self, other: _T_contra, /) -> SupportsBool: ...

class SupportsDunderLE(Protocol[_T_contra]):
    def __le__(self, other: _T_contra, /) -> SupportsBool: ...

class SupportsDunderGE(Protocol[_T_contra]):
    def __ge__(self, other: _T_contra, /) -> SupportsBool: ...

class SupportsAllComparisons(
    SupportsDunderLT[Any],
    SupportsDunderGT[Any],
    SupportsDunderLE[Any],
    SupportsDunderGE[Any],
    Protocol,
): ...

type SupportsRichComparison = SupportsDunderLT[Any] | SupportsDunderGT[Any]
SupportsRichComparisonT = TypeVar(
    "SupportsRichComparisonT",
    bound=SupportsRichComparison,
)

class SupportsAdd(Protocol[_T_contra, _T_co]):
    def __add__(self, x: _T_contra, /) -> _T_co: ...

class SupportsRAdd(Protocol[_T_contra, _T_co]):
    def __radd__(self, x: _T_contra, /) -> _T_co: ...

class SupportsSub(Protocol[_T_contra, _T_co]):
    def __sub__(self, x: _T_contra, /) -> _T_co: ...

class SupportsRSub(Protocol[_T_contra, _T_co]):
    def __rsub__(self, x: _T_contra, /) -> _T_co: ...

class SupportsMul(Protocol[_T_contra, _T_co]):
    def __mul__(self, x: _T_contra, /) -> _T_co: ...

class SupportsRMul(Protocol[_T_contra, _T_co]):
    def __rmul__(self, x: _T_contra, /) -> _T_co: ...

class SupportsMod(Protocol[_T_contra, _T_co]):
    def __mod__(self, other: _T_contra, /) -> _T_co: ...

class SupportsRMod(Protocol[_T_contra, _T_co]):
    def __rmod__(self, other: _T_contra, /) -> _T_co: ...

class SupportsDivMod(Protocol[_T_contra, _T_co]):
    def __divmod__(self, other: _T_contra, /) -> _T_co: ...

class SupportsRDivMod(Protocol[_T_contra, _T_co]):
    def __rdivmod__(self, other: _T_contra, /) -> _T_co: ...

class SupportsIter(Protocol[_T_co]):
    def __iter__(self) -> _T_co: ...

class SupportsAiter(Protocol[_T_co]):
    def __aiter__(self) -> _T_co: ...

class SupportsLen(Protocol):
    def __len__(self) -> int: ...

class SupportsLenAndGetItem(Protocol[_T_co]):
    def __len__(self) -> int: ...
    def __getitem__(self, k: int, /) -> _T_co: ...

class SupportsTrunc(Protocol):
    def __trunc__(self) -> int: ...

class SupportsItems(Protocol[_KT_co, _VT_co]):
    def items(self) -> AbstractSet[tuple[_KT_co, _VT_co]]: ...

class SupportsKeysAndGetItem(Protocol[_KT, _VT_co]):
    def keys(self) -> Iterable[_KT]: ...
    def __getitem__(self, key: _KT, /) -> _VT_co: ...

class SupportsGetItem(Protocol[_KT_contra, _VT_co]):
    def __getitem__(self, key: _KT_contra, /) -> _VT_co: ...

class SupportsContainsAndGetItem(Protocol[_KT_contra, _VT_co]):
    def __contains__(self, x: Any, /) -> bool: ...
    def __getitem__(self, key: _KT_contra, /) -> _VT_co: ...

class SupportsItemAccess(Protocol[_KT_contra, _VT]):
    def __contains__(self, x: Any, /) -> bool: ...
    def __getitem__(self, key: _KT_contra, /) -> _VT: ...
    def __setitem__(self, key: _KT_contra, value: _VT, /) -> None: ...
    def __delitem__(self, key: _KT_contra, /) -> None: ...

type StrPath = str | PathLike[str]
type BytesPath = bytes | PathLike[bytes]
type GenericPath[AnyStr: (bytes, str)] = AnyStr | PathLike[AnyStr]
type StrOrBytesPath = str | bytes | PathLike[str] | PathLike[bytes]
type OpenTextModeUpdating = Literal[
    "r+",
    "+r",
    "rt+",
    "r+t",
    "+rt",
    "tr+",
    "t+r",
    "+tr",
    "w+",
    "+w",
    "wt+",
    "w+t",
    "+wt",
    "tw+",
    "t+w",
    "+tw",
    "a+",
    "+a",
    "at+",
    "a+t",
    "+at",
    "ta+",
    "t+a",
    "+ta",
    "x+",
    "+x",
    "xt+",
    "x+t",
    "+xt",
    "tx+",
    "t+x",
    "+tx",
]
type OpenTextModeWriting = Literal[
    "w",
    "wt",
    "tw",
    "a",
    "at",
    "ta",
    "x",
    "xt",
    "tx",
]
type OpenTextModeReading = Literal[
    "r",
    "rt",
    "tr",
    "U",
    "rU",
    "Ur",
    "rtU",
    "rUt",
    "Urt",
    "trU",
    "tUr",
    "Utr",
]
type OpenTextMode = (
    OpenTextModeUpdating | OpenTextModeWriting | OpenTextModeReading
)
type OpenBinaryModeUpdating = Literal[
    "rb+",
    "r+b",
    "+rb",
    "br+",
    "b+r",
    "+br",
    "wb+",
    "w+b",
    "+wb",
    "bw+",
    "b+w",
    "+bw",
    "ab+",
    "a+b",
    "+ab",
    "ba+",
    "b+a",
    "+ba",
    "xb+",
    "x+b",
    "+xb",
    "bx+",
    "b+x",
    "+bx",
]
type OpenBinaryModeWriting = Literal["wb", "bw", "ab", "ba", "xb", "bx"]
type OpenBinaryModeReading = Literal[
    "rb",
    "br",
    "rbU",
    "rUb",
    "Urb",
    "brU",
    "bUr",
    "Ubr",
]
type OpenBinaryMode = (
    OpenBinaryModeUpdating | OpenBinaryModeReading | OpenBinaryModeWriting
)

class HasFileno(Protocol):
    def fileno(self) -> int: ...

type FileDescriptor = int
type FileDescriptorLike = int | HasFileno
type FileDescriptorOrPath = int | StrOrBytesPath

class SupportsRead(Protocol[_T_co]):
    def read(self, length: int = ..., /) -> _T_co: ...

class SupportsReadline(Protocol[_T_co]):
    def readline(self, length: int = ..., /) -> _T_co: ...

class SupportsNoArgReadline(Protocol[_T_co]):
    def readline(self) -> _T_co: ...

class SupportsWrite(Protocol[_T_contra]):
    def write(self, s: _T_contra, /) -> object: ...

class SupportsFlush(Protocol):
    def flush(self) -> object: ...

class Viewable(Protocol[_T_co]):
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_T_co]: ...

class SupportsGetItemViewable(Protocol[_KT, _VT_co]):
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[_KT]: ...
    def __getitem__(self, key: _KT, /) -> _VT_co: ...

type ReadOnlyBuffer = Buffer
type WriteableBuffer = Buffer
type ReadableBuffer = Buffer

class SliceableBuffer(Buffer, Protocol):
    def __getitem__(
        self,
        slice: slice[SupportsIndex | None],
        /,
    ) -> Sequence[int]: ...

class IndexableBuffer(Buffer, Protocol):
    def __getitem__(self, i: int, /) -> int: ...

class SupportsGetItemBuffer(SliceableBuffer, IndexableBuffer, Protocol):
    def __contains__(self, x: Any, /) -> bool: ...
    @overload
    def __getitem__(
        self,
        slice: slice[SupportsIndex | None],
        /,
    ) -> Sequence[int]: ...
    @overload
    def __getitem__(self, i: int, /) -> int: ...

class SizedBuffer(Sized, Buffer, Protocol): ...

type ExcInfo = tuple[type[BaseException], BaseException, TracebackType]
type OptExcInfo = ExcInfo | tuple[None, None, None]

class structseq[T_co]:
    n_fields: Final[int]
    n_unnamed_fields: Final[int]
    n_sequence_fields: Final[int]
    def __new__(
        cls,
        sequence: Iterable[_T_co],
        dict: dict[str, Any] = ...,
    ) -> _Self: ...
    def __replace__(self, **kwargs: Any) -> _Self: ...

AnyOrLiteralStr = TypeVar("AnyOrLiteralStr", str, bytes, LiteralString)
StrOrLiteralStr = TypeVar("StrOrLiteralStr", LiteralString, str)
type ProfileFunction = Callable[
    [
        FrameType,
        Literal["call", "return", "c_call", "c_return", "c_exception"],
        Any,
    ],
    object,
]
type TraceFunction = Callable[
    [FrameType, Literal["call", "line", "return", "exception", "opcode"], Any],
    TraceFunction | None,
]

class DataclassInstance(Protocol):
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]

if sys.version_info >= (3, 14):
    type ConvertibleToInt = str | ReadableBuffer | SupportsInt | SupportsIndex
else:
    type ConvertibleToInt = (
        str | ReadableBuffer | SupportsInt | SupportsIndex | SupportsTrunc
    )
type ConvertibleToFloat = str | ReadableBuffer | SupportsFloat | SupportsIndex
from enum import StrEnum as StrEnum

type AnnotationForm = Any
if sys.version_info >= (3, 14):
    from annotationlib import Format

    type AnnotateFunc = Callable[[Format], dict[str, AnnotationForm]]
    type EvaluateFunc = Callable[[Format], AnnotationForm]
