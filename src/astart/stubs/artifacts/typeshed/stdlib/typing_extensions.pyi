import abc
import enum
import sys
from _collections_abc import dict_items, dict_keys, dict_values
from collections import ChainMap as ChainMap
from collections import Counter as Counter
from collections.abc import (
    AsyncGenerator as AsyncGenerator,
)
from collections.abc import (
    AsyncIterable as AsyncIterable,
)
from collections.abc import (
    AsyncIterator as AsyncIterator,
)
from collections.abc import (
    Awaitable as Awaitable,
)
from collections.abc import Callable as Callable
from collections.abc import (
    Collection as Collection,
)
from collections.abc import (
    Container as Container,
)
from collections.abc import (
    Coroutine as Coroutine,
)
from collections.abc import (
    Generator as Generator,
)
from collections.abc import (
    Hashable as Hashable,
)
from collections.abc import (
    ItemsView as ItemsView,
)
from collections.abc import (
    Iterable as Iterable,
)
from collections.abc import (
    Iterator as Iterator,
)
from collections.abc import (
    KeysView as KeysView,
)
from collections.abc import (
    Mapping as Mapping,
)
from collections.abc import (
    MappingView as MappingView,
)
from collections.abc import (
    MutableMapping as MutableMapping,
)
from collections.abc import (
    MutableSequence as MutableSequence,
)
from collections.abc import (
    MutableSet as MutableSet,
)
from collections.abc import (
    Reversible as Reversible,
)
from collections.abc import (
    Sequence as Sequence,
)
from collections.abc import (
    Sized as Sized,
)
from collections.abc import (
    ValuesView as ValuesView,
)
from contextlib import AbstractAsyncContextManager as AsyncContextManager
from contextlib import AbstractContextManager as ContextManager
from re import Match as Match
from re import Pattern as Pattern
from types import GenericAlias, ModuleType, UnionType
from typing import (
    IO as IO,
)
from typing import (
    TYPE_CHECKING as TYPE_CHECKING,
)
from typing import (
    AbstractSet as AbstractSet,
)
from typing import (
    Any as Any,
)
from typing import (
    AnyStr as AnyStr,
)
from typing import (
    BinaryIO as BinaryIO,
)
from typing import (
    ClassVar as ClassVar,
)
from typing import (
    Concatenate as Concatenate,
)
from typing import (
    DefaultDict as DefaultDict,
)
from typing import (
    Deque as Deque,
)
from typing import (
    Dict as Dict,
)
from typing import (
    ForwardRef as ForwardRef,
)
from typing import (
    FrozenSet as FrozenSet,
)
from typing import (
    Generic as Generic,
)
from typing import (
    List as List,
)
from typing import (
    NoReturn as NoReturn,
)
from typing import (
    Optional as Optional,
)
from typing import (
    ParamSpecArgs as ParamSpecArgs,
)
from typing import (
    ParamSpecKwargs as ParamSpecKwargs,
)
from typing import (
    Self,
    _Alias,
    _SpecialForm,
    type_check_only,
)
from typing import (
    Set as Set,
)
from typing import (
    Text as Text,
)
from typing import (
    TextIO as TextIO,
)
from typing import (
    Tuple as Tuple,
)
from typing import (
    Type as Type,
)
from typing import (
    TypeAlias as TypeAlias,
)
from typing import (
    TypedDict as TypedDict,
)
from typing import (
    TypeGuard as TypeGuard,
)
from typing import (
    TypeVar as _TypeVar,
)
from typing import (
    Union as Union,
)
from typing import (
    cast as cast,
)
from typing import (
    is_typeddict as is_typeddict,
)
from typing import (
    no_type_check as no_type_check,
)
from typing import (
    overload as overload,
)

from _typeshed import AnnotationForm, Incomplete, Unused

# Please keep order the same as at runtime.
__all__ = [
    "IO",
    "TYPE_CHECKING",
    # Pure aliases, have always been in typing
    "AbstractSet",
    # One-off things.
    "Annotated",
    # Super-special typing primitives.
    "Any",
    "AnyStr",
    "AsyncContextManager",
    "AsyncGenerator",
    "AsyncIterable",
    "AsyncIterator",
    # ABCs (from collections.abc).
    "Awaitable",
    "BinaryIO",
    "Buffer",
    "Callable",
    # Added dynamically
    "CapsuleType",
    "ChainMap",
    "ClassVar",
    "Collection",
    "Concatenate",
    "Container",
    # Concrete collection types.
    "ContextManager",
    "Coroutine",
    "Counter",
    "DefaultDict",
    "Deque",
    "Dict",
    "Doc",
    "Final",
    "Format",
    "ForwardRef",
    "FrozenSet",
    "Generator",
    "Generic",
    "Hashable",
    "IntVar",
    "ItemsView",
    "Iterable",
    "Iterator",
    "KeysView",
    "List",
    "Literal",
    "LiteralString",
    "Mapping",
    "MappingView",
    "Match",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "NamedTuple",
    "Never",
    "NewType",
    "NoDefault",
    "NoExtraItems",
    "NoReturn",
    "NotRequired",
    "Optional",
    "OrderedDict",
    "ParamSpec",
    "ParamSpecArgs",
    "ParamSpecKwargs",
    "Pattern",
    "Protocol",
    "ReadOnly",
    "Reader",
    "Required",
    "Reversible",
    "Self",
    "Sentinel",
    "Sequence",
    "Set",
    "Sized",
    # Structural checks, a.k.a. protocols.
    "SupportsAbs",
    "SupportsBytes",
    "SupportsComplex",
    "SupportsFloat",
    "SupportsIndex",
    "SupportsInt",
    "SupportsRound",
    "Text",
    "TextIO",
    "Tuple",
    "Type",
    "TypeAlias",
    "TypeAliasType",
    "TypeForm",
    "TypeGuard",
    "TypeIs",
    "TypeVar",
    "TypeVarTuple",
    "TypedDict",
    "Union",
    "Unpack",
    "ValuesView",
    "Writer",
    "assert_never",
    "assert_type",
    "cast",
    "clear_overloads",
    "dataclass_transform",
    "deprecated",
    "disjoint_base",
    "evaluate_forward_ref",
    "final",
    "get_annotations",
    "get_args",
    "get_origin",
    "get_original_bases",
    "get_overloads",
    "get_protocol_members",
    "get_type_hints",
    "is_protocol",
    "is_typeddict",
    "no_type_check",
    "no_type_check_decorator",
    "overload",
    "override",
    "reveal_type",
    "runtime",
    "runtime_checkable",
    "type_repr",
]

_T = _TypeVar("_T")
_F = _TypeVar("_F", bound=Callable[..., Any])
_TC = _TypeVar("_TC", bound=type[object])
_T_co = _TypeVar("_T_co", covariant=True)  # Any type covariant containers.
_T_contra = _TypeVar("_T_contra", contravariant=True)

if sys.version_info < (3, 15):
    def no_type_check_decorator[F: Callable[..., Any]](
        decorator: _F,
    ) -> _F: ...

# Do not import (and re-export) Protocol or runtime_checkable from
# typing module because type checkers need to be able to distinguish
# typing.Protocol and typing_extensions.Protocol so they can properly
# warn users about potential runtime exceptions when using typing.Protocol
# on older versions of Python.
Protocol: _SpecialForm

def runtime_checkable[TC: type[object]](cls: _TC) -> _TC: ...

# This alias for above is kept here for backwards compatibility.
runtime = runtime_checkable
Final: _SpecialForm

def final[T](f: _T) -> _T: ...
def disjoint_base[TC: type[object]](cls: _TC) -> _TC: ...

Literal: _SpecialForm

def IntVar(name: str) -> Any: ...  # returns a new TypeVar

# Internal mypy fallback type for all typed dicts (does not exist at runtime)
# N.B. Keep this mostly in sync with typing._TypedDict/mypy_extensions._TypedDict
@type_check_only
class _TypedDict(Mapping[str, object], metaclass=abc.ABCMeta):
    __required_keys__: ClassVar[frozenset[str]]
    __optional_keys__: ClassVar[frozenset[str]]
    __total__: ClassVar[bool]
    __orig_bases__: ClassVar[tuple[Any, ...]]
    # PEP 705
    __readonly_keys__: ClassVar[frozenset[str]]
    __mutable_keys__: ClassVar[frozenset[str]]
    # PEP 728
    __closed__: ClassVar[bool | None]
    __extra_items__: ClassVar[AnnotationForm]
    def copy(self) -> Self: ...
    # Using Never so that only calls using mypy plugin hook that specialize the signature
    # can go through.
    def setdefault(self, k: Never, default: object) -> object: ...
    # Mypy plugin hook for 'pop' expects that 'default' has a type variable type.
    def pop(self, k: Never, default: _T = ...) -> object: ...  # pyright: ignore[reportInvalidTypeVarUse]
    def update(self, m: Self, /) -> None: ...
    def items(self) -> dict_items[str, object]: ...
    def keys(self) -> dict_keys[str, object]: ...
    def values(self) -> dict_values[str, object]: ...
    def __delitem__(self, k: Never) -> None: ...
    @overload
    def __or__(self, value: Self, /) -> Self: ...
    @overload
    def __or__(self, value: dict[str, Any], /) -> dict[str, object]: ...
    @overload
    def __ror__(self, value: Self, /) -> Self: ...
    @overload
    def __ror__(self, value: dict[str, Any], /) -> dict[str, object]: ...

    # supposedly incompatible definitions of `__ior__` and `__or__`:
    # Since this module defines "Self" it is not recognized by Ruff as typing_extensions.Self
    def __ior__(self, value: Self, /) -> Self: ...  # type: ignore[misc]

OrderedDict = _Alias()

from typing import get_type_hints as get_type_hints

def get_args(tp: AnnotationForm) -> tuple[AnnotationForm, ...]: ...
@overload
def get_origin(tp: UnionType) -> type[UnionType]: ...
@overload
def get_origin(tp: GenericAlias) -> type: ...
@overload
def get_origin(tp: ParamSpecArgs | ParamSpecKwargs) -> ParamSpec: ...
@overload
def get_origin(tp: AnnotationForm) -> AnnotationForm | None: ...

Annotated: _SpecialForm
_AnnotatedAlias: Any  # undocumented

# New and changed things in 3.11
from collections.abc import Buffer as Buffer
from types import get_original_bases as get_original_bases
from typing import (
    LiteralString as LiteralString,
)
from typing import (
    NamedTuple as NamedTuple,
)
from typing import (
    Never as Never,
)
from typing import (
    NewType as NewType,
)
from typing import (
    NotRequired as NotRequired,
)
from typing import (
    Required as Required,
)
from typing import (
    SupportsAbs as SupportsAbs,
)
from typing import (
    SupportsBytes as SupportsBytes,
)
from typing import (
    SupportsComplex as SupportsComplex,
)
from typing import (
    SupportsFloat as SupportsFloat,
)
from typing import (
    SupportsIndex as SupportsIndex,
)
from typing import (
    SupportsInt as SupportsInt,
)
from typing import (
    SupportsRound as SupportsRound,
)
from typing import (
    Unpack as Unpack,
)
from typing import (
    assert_never as assert_never,
)
from typing import (
    assert_type as assert_type,
)
from typing import (
    clear_overloads as clear_overloads,
)
from typing import (
    dataclass_transform as dataclass_transform,
)
from typing import (
    get_overloads as get_overloads,
)
from typing import (
    override as override,
)
from typing import (
    reveal_type as reveal_type,
)

if sys.version_info >= (3, 14):
    from io import Reader as Reader
    from io import Writer as Writer
else:
    @runtime_checkable
    class Reader(Protocol[_T_co]):
        __slots__ = ()
        @abc.abstractmethod
        def read(self, size: int = ..., /) -> _T_co: ...

    @runtime_checkable
    class Writer(Protocol[_T_contra]):
        __slots__ = ()
        @abc.abstractmethod
        def write(self, data: _T_contra, /) -> int: ...

from types import CapsuleType as CapsuleType
from typing import (
    NoDefault as NoDefault,
)
from typing import (
    ParamSpec as ParamSpec,
)
from typing import (
    ReadOnly as ReadOnly,
)
from typing import (
    TypeIs as TypeIs,
)
from typing import (
    TypeVar as TypeVar,
)
from typing import (
    TypeVarTuple as TypeVarTuple,
)
from typing import (
    get_protocol_members as get_protocol_members,
)
from typing import (
    is_protocol as is_protocol,
)
from warnings import deprecated as deprecated

# TypeAliasType was added in Python 3.12, but had significant changes in 3.14.
if sys.version_info >= (3, 14):
    from typing import TypeAliasType as TypeAliasType
else:
    @final
    class TypeAliasType:
        def __init__(
            self,
            name: str,
            value: AnnotationForm,
            *,
            type_params: tuple[TypeVar | ParamSpec | TypeVarTuple, ...] = (),
        ) -> None: ...
        @property
        def __value__(self) -> AnnotationForm: ...
        @property
        def __type_params__(
            self,
        ) -> tuple[TypeVar | ParamSpec | TypeVarTuple, ...]: ...
        @property
        # `__parameters__` can include special forms if a `TypeVarTuple` was
        # passed as a `type_params` element to the constructor method.
        def __parameters__(
            self,
        ) -> tuple[TypeVar | ParamSpec | AnnotationForm, ...]: ...
        @property
        def __name__(self) -> str: ...
        # It's writable on types, but not on instances of TypeAliasType.
        @property
        def __module__(self) -> str | None: ...  # type: ignore[override]
        # Returns typing._GenericAlias, which isn't stubbed.
        def __getitem__(
            self,
            parameters: Incomplete | tuple[Incomplete, ...],
        ) -> AnnotationForm: ...
        def __init_subclass__(
            cls,
            *args: Unused,
            **kwargs: Unused,
        ) -> NoReturn: ...
        def __or__(self, right: Any, /) -> _SpecialForm: ...
        def __ror__(self, left: Any, /) -> _SpecialForm: ...

# PEP 727
class Doc:
    documentation: str
    def __init__(self, documentation: str, /) -> None: ...
    def __hash__(self) -> int: ...
    def __eq__(self, other: object) -> bool: ...

# PEP 728
@type_check_only
class _NoExtraItemsType: ...

NoExtraItems: _NoExtraItemsType

# PEP 747
TypeForm: _SpecialForm

# PEP 649/749
if sys.version_info >= (3, 14):
    from typing import evaluate_forward_ref as evaluate_forward_ref

    from annotationlib import Format as Format
    from annotationlib import get_annotations as get_annotations
    from annotationlib import type_repr as type_repr
else:
    class Format(enum.IntEnum):
        VALUE = 1
        VALUE_WITH_FAKE_GLOBALS = 2
        FORWARDREF = 3
        STRING = 4

    @overload
    def get_annotations(
        obj: Any,  # any object with __annotations__ or __annotate__
        *,
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        eval_str: bool = False,
        format: Literal[Format.STRING],
    ) -> dict[str, str]: ...
    @overload
    def get_annotations(
        obj: Any,  # any object with __annotations__ or __annotate__
        *,
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        eval_str: bool = False,
        format: Literal[Format.FORWARDREF],
    ) -> dict[str, AnnotationForm | ForwardRef]: ...
    @overload
    def get_annotations(
        obj: Any,  # any object with __annotations__ or __annotate__
        *,
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        eval_str: bool = False,
        format: Format = ...,
    ) -> dict[str, AnnotationForm]: ...
    @overload
    def evaluate_forward_ref(
        forward_ref: ForwardRef,
        *,
        owner: Callable[..., object]
        | type[object]
        | ModuleType
        | None = None,  # any callable, class, or module
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        type_params: Iterable[TypeVar | ParamSpec | TypeVarTuple]
        | None = None,
        format: Literal[Format.STRING],
        _recursive_guard: Container[str] = ...,
    ) -> str: ...
    @overload
    def evaluate_forward_ref(
        forward_ref: ForwardRef,
        *,
        owner: Callable[..., object]
        | type[object]
        | ModuleType
        | None = None,  # any callable, class, or module
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        type_params: Iterable[TypeVar | ParamSpec | TypeVarTuple]
        | None = None,
        format: Literal[Format.FORWARDREF],
        _recursive_guard: Container[str] = ...,
    ) -> AnnotationForm | ForwardRef: ...
    @overload
    def evaluate_forward_ref(
        forward_ref: ForwardRef,
        *,
        owner: Callable[..., object]
        | type[object]
        | ModuleType
        | None = None,  # any callable, class, or module
        globals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        locals: Mapping[str, Any]
        | None = None,  # value types depend on the key
        type_params: Iterable[TypeVar | ParamSpec | TypeVarTuple]
        | None = None,
        format: Format | None = None,
        _recursive_guard: Container[str] = ...,
    ) -> AnnotationForm: ...
    def type_repr(value: object) -> str: ...

# PEP 661
class Sentinel:
    def __init__(self, name: str, repr: str | None = None) -> None: ...
    if sys.version_info >= (3, 14):
        def __or__(
            self,
            other: Any,
        ) -> UnionType: ...  # other can be any type form legal for unions
        def __ror__(
            self,
            other: Any,
        ) -> UnionType: ...  # other can be any type form legal for unions
    else:
        def __or__(
            self,
            other: Any,
        ) -> _SpecialForm: ...  # other can be any type form legal for unions
        def __ror__(
            self,
            other: Any,
        ) -> _SpecialForm: ...  # other can be any type form legal for unions
