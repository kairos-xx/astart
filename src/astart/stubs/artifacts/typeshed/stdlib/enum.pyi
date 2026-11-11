import sys
import types
from builtins import property as _builtins_property
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import (
    Any,
    Final,
    Literal,
    Self,
    SupportsIndex,
    TypeVar,
    overload,
)

import _typeshed
from _typeshed import SupportsKeysAndGetItem, Unused

__all__ = ["Enum", "EnumMeta", "Flag", "IntEnum", "IntFlag", "auto", "unique"]

__all__ += [
    "CONFORM",
    "CONTINUOUS",
    "EJECT",
    "KEEP",
    "NAMED_FLAGS",
    "STRICT",
    "UNIQUE",
    "EnumCheck",
    "EnumType",
    "FlagBoundary",
    "ReprEnum",
    "StrEnum",
    "global_enum",
    "global_enum_repr",
    "global_flag_repr",
    "global_str",
    "member",
    "nonmember",
    "pickle_by_enum_name",
    "pickle_by_global_name",
    "property",
    "verify",
]

__all__ += ["EnumDict"]
if sys.version_info >= (3, 15):
    __all__ += ["bin", "show_flag_values"]

_EnumMemberT = TypeVar("_EnumMemberT")
_EnumerationT = TypeVar("_EnumerationT", bound=type[Enum])

# The following all work:
# >>> from enum import Enum
# >>> from string import ascii_lowercase
# >>> Enum('Foo', names='RED YELLOW GREEN')
# <enum 'Foo'>
# >>> Enum('Foo', names=[('RED', 1), ('YELLOW, 2)])
# <enum 'Foo'>
# >>> Enum('Foo', names=((x for x in (ascii_lowercase[i], i)) for i in range(5)))
# <enum 'Foo'>
# >>> Enum('Foo', names={'RED': 1, 'YELLOW': 2})
# <enum 'Foo'>
type _EnumNames = (
    str | Iterable[str] | Iterable[Iterable[str | Any]] | Mapping[str, Any]
)
type _Signature = Any  # TODO: Unable to import Signature from inspect module

class nonmember[EnumMemberT]:
    value: _EnumMemberT
    def __init__(self, value: _EnumMemberT) -> None: ...

class member[EnumMemberT]:
    value: _EnumMemberT
    def __init__(self, value: _EnumMemberT) -> None: ...

class _EnumDict(dict[str, Any]):
    def __init__(self, cls_name: str | None = None) -> None: ...
    def __setitem__(self, key: str, value: Any) -> None: ...
    @overload  # type: ignore[override]
    def update(
        self,
        members: SupportsKeysAndGetItem[str, Any],
        **more_members: Any,
    ) -> None: ...
    @overload
    def update(
        self,
        members: Iterable[tuple[str, Any]],
        **more_members: Any,
    ) -> None: ...
    @property
    def member_names(self) -> list[str]: ...

EnumDict = _EnumDict

# Structurally: Iterable[T], Reversible[T], Container[T] where T is the enum itself
class EnumMeta(type):
    def __new__(
        metacls: type[_typeshed.Self],
        cls: str,
        bases: tuple[type, ...],
        classdict: _EnumDict,
        *,
        boundary: FlagBoundary | None = None,
        _simple: bool = False,
        **kwds: Any,
    ) -> _typeshed.Self: ...
    @classmethod
    def __prepare__(
        metacls,
        cls: str,
        bases: tuple[type, ...],
        **kwds: Any,
    ) -> _EnumDict: ...  # type: ignore[override]
    def __iter__(cls: type[_EnumMemberT]) -> Iterator[_EnumMemberT]: ...
    def __reversed__(cls: type[_EnumMemberT]) -> Iterator[_EnumMemberT]: ...
    def __contains__(cls: type[Any], value: object) -> bool: ...
    def __getitem__(cls: type[_EnumMemberT], name: str) -> _EnumMemberT: ...
    @_builtins_property
    def __members__(
        cls: type[_EnumMemberT],
    ) -> types.MappingProxyType[str, _EnumMemberT]: ...
    def __len__(cls) -> int: ...
    def __bool__(cls) -> Literal[True]: ...
    def __dir__(cls) -> list[str]: ...

    # Overload 1: Value lookup on an already existing enum class (simple case)
    @overload
    def __call__(
        cls: type[_EnumMemberT],
        value: Any,
        names: None = None,
    ) -> _EnumMemberT: ...

    # Overload 2: Functional API for constructing new enum classes.
    @overload
    def __call__(
        cls,
        value: str,
        names: _EnumNames,
        *,
        module: str | None = None,
        qualname: str | None = None,
        type: type | None = None,
        start: int = 1,
        boundary: FlagBoundary | None = None,
    ) -> type[Enum]: ...

    # Overload 3 (py312+ only): Value lookup on an already existing enum class (complex case)
    #
    # >>> class Foo(enum.Enum):
    # ...     X = 1, 2, 3
    # >>> Foo(1, 2, 3)
    # <Foo.X: (1, 2, 3)>
    #
    @overload
    def __call__(
        cls: type[_EnumMemberT],
        value: Any,
        *values: Any,
    ) -> _EnumMemberT: ...
    if sys.version_info >= (3, 14):
        @property
        def __signature__(cls) -> _Signature: ...

    _member_names_: list[str]  # undocumented
    _member_map_: dict[str, Enum]  # undocumented
    _value2member_map_: dict[Any, Enum]  # undocumented

EnumType = EnumMeta

class property(types.DynamicClassAttribute):
    def __set_name__(self, ownerclass: type[Enum], name: str) -> None: ...
    name: str
    clsname: str
    member: Enum | None

_magic_enum_attr = property

class Enum(metaclass=EnumMeta):
    @_magic_enum_attr
    def name(self) -> str: ...
    @_magic_enum_attr
    def value(self) -> Any: ...
    _name_: str
    _value_: Any
    _ignore_: str | list[str]
    _order_: str
    __order__: str
    @classmethod
    def _missing_(cls, value: object) -> Any: ...
    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[Any],
    ) -> Any: ...
    # It's not true that `__new__` will accept any argument type,
    # so ideally we'd use `Any` to indicate that the argument type is inexpressible.
    # However, using `Any` causes too many false-positives for those using mypy's `--disallow-any-expr`
    # (see #7752, #2539, mypy/#5788),
    # and in practice using `object` here has the same effect as using `Any`.
    def __new__(cls, value: object) -> Self: ...
    def __dir__(self) -> list[str]: ...
    def __hash__(self) -> int: ...
    def __format__(self, format_spec: str) -> str: ...
    def __reduce_ex__(self, proto: Unused) -> tuple[Any, ...]: ...
    def __copy__(self) -> Self: ...
    def __deepcopy__(self, memo: Any) -> Self: ...
    if sys.version_info >= (3, 12) and sys.version_info < (3, 14):
        @classmethod
        def __signature__(cls) -> str: ...
    def _add_value_alias_(self, value: Any) -> None: ...
    def _add_alias_(self, name: str) -> None: ...

class ReprEnum(Enum): ...

class IntEnum(int, ReprEnum):
    _value_: int
    @_magic_enum_attr
    def value(self) -> int: ...
    def __new__(cls, value: int) -> Self: ...

def unique[EnumerationT: type[Enum]](
    enumeration: _EnumerationT,
) -> _EnumerationT: ...

_auto_null: Any

class Flag(Enum):
    _name_: str | None  # type: ignore[assignment]
    _value_: int
    _numeric_repr_: Callable[[int], str]
    @_magic_enum_attr
    def name(self) -> str | None: ...  # type: ignore[override]
    @_magic_enum_attr
    def value(self) -> int: ...
    def __contains__(self, other: Self) -> bool: ...
    def __bool__(self) -> bool: ...
    def __or__(self, other: Self) -> Self: ...
    def __and__(self, other: Self) -> Self: ...
    def __xor__(self, other: Self) -> Self: ...
    def __invert__(self) -> Self: ...
    def __iter__(self) -> Iterator[Self]: ...
    def __len__(self) -> int: ...
    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__

class StrEnum(str, ReprEnum):
    def __new__(cls, value: str) -> Self: ...
    _value_: str
    @_magic_enum_attr
    def value(self) -> str: ...
    @staticmethod
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str: ...

class EnumCheck(StrEnum):
    CONTINUOUS = "no skipped integer values"
    NAMED_FLAGS = "multi-flag aliases may not contain unnamed flags"
    UNIQUE = "one name per value"

CONTINUOUS: Final = EnumCheck.CONTINUOUS
NAMED_FLAGS: Final = EnumCheck.NAMED_FLAGS
UNIQUE: Final = EnumCheck.UNIQUE

class verify:
    def __init__(self, *checks: EnumCheck) -> None: ...
    def __call__(self, enumeration: _EnumerationT) -> _EnumerationT: ...

class FlagBoundary(StrEnum):
    STRICT = "strict"
    CONFORM = "conform"
    EJECT = "eject"
    KEEP = "keep"

STRICT: Final = FlagBoundary.STRICT
CONFORM: Final = FlagBoundary.CONFORM
EJECT: Final = FlagBoundary.EJECT
KEEP: Final = FlagBoundary.KEEP

def global_str(self: Enum) -> str: ...
def global_enum[EnumerationT: type[Enum]](
    cls: _EnumerationT,
    update_str: bool = False,
) -> _EnumerationT: ...
def global_enum_repr(self: Enum) -> str: ...
def global_flag_repr(self: Flag) -> str: ...
def show_flag_values(value: int) -> list[int]: ...
def bin(num: SupportsIndex, max_bits: int | None = None) -> str: ...

class IntFlag(int, ReprEnum, Flag, boundary=KEEP):  # type: ignore[misc]  # complaints about incompatible bases
    def __new__(cls, value: int) -> Self: ...
    def __or__(self, other: int) -> Self: ...
    def __and__(self, other: int) -> Self: ...
    def __xor__(self, other: int) -> Self: ...
    def __invert__(self) -> Self: ...
    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__

class auto:
    _value_: Any
    @_magic_enum_attr
    def value(self) -> Any: ...
    def __new__(cls) -> Self: ...

    # These don't exist, but auto is basically immediately replaced with
    # either an int or a str depending on the type of the enum. StrEnum's auto
    # shouldn't have these, but they're needed for int versions of auto (mostly the __or__).
    # Ideally type checkers would special case auto enough to handle this,
    # but until then this is a slightly inaccurate helping hand.
    def __or__(self, other: int | Self) -> Self: ...
    def __and__(self, other: int | Self) -> Self: ...
    def __xor__(self, other: int | Self) -> Self: ...
    __ror__ = __or__
    __rand__ = __and__
    __rxor__ = __xor__

def pickle_by_global_name(self: Enum, proto: int) -> str: ...
def pickle_by_enum_name[EnumMemberT](
    self: _EnumMemberT,
    proto: int,
) -> tuple[Callable[..., Any], tuple[type[_EnumMemberT], str]]: ...
