"""Strictly typed test file for inference, calls, decorators, and kwargs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import run, sleep
from collections import ChainMap, Counter, OrderedDict, defaultdict, deque
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from contextlib import asynccontextmanager, contextmanager, suppress
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import (
    cached_property,
    lru_cache,
    partial,
    reduce,
    singledispatch,
    wraps,
)
from importlib import import_module
from itertools import (
    accumulate,
    chain,
    combinations,
    compress,
    dropwhile,
    groupby,
    islice,
    permutations,
    product,
    takewhile,
    zip_longest,
)
from json import dumps, loads
from math import nan
from operator import add, mul
from pathlib import Path
from re import search, split
from tempfile import NamedTemporaryFile, gettempdir
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Final,
    NamedTuple,
    NoReturn,
    ParamSpec,
    Protocol,
    Self,
    TypeVar,
    cast,
    final,
)

if TYPE_CHECKING:
    from types import ModuleType

from uuid import NAMESPACE_DNS, UUID, uuid5
from weakref import ReferenceType, WeakKeyDictionary, ref

P = ParamSpec(name="P")
R = TypeVar(name="R")
T = TypeVar(name="T")
U = TypeVar(name="U")
V = TypeVar(name="V")
W = TypeVar(name="W")
K = TypeVar(name="K")
N = TypeVar("N", int, float, complex)


@final
class Constants:
    """Constants for the test.

    Attributes:
        threshold: TODO.
        max_value: TODO.
        min_length: TODO.
        extended_sentinel: TODO.
        extended_context: TODO.

    """

    threshold: Final[int] = 5
    max_value: Final[int] = 10
    min_length: Final[int] = 3
    extended_sentinel: Final[object] = object()
    extended_context: ContextVar[ExtendedContextMap | None] = ContextVar(
        "extended_context",
        default=None,
    )


type IntList = list[int]
type IntDict = dict[str, int]
type TestResult = dict[str, object]
type ConditionalResult = list[int] | IntDict | str | int
type NestedLoopFunc = Callable[[Sequence[Sequence[int]]], list[int]]
type ExtendedPayload = object
type ExtendedMetadata = dict[str, object]
type ExtendedContextMap = dict[str, object]
type ExtendedResultTuple = tuple["ExtendedResult", str, object, object]
type ExtendedTestResult = dict[str, object]
type PatternStressInput = Mapping[str, object] | Sequence[object] | None
type PatternStressResult = (
    tuple[int, int] | list[object] | dict[str, object] | object | str
)
type ConfigMapping = MutableMapping[str, object]


class SupportsUpdate(Protocol):
    """Protocol for observer-like objects."""

    def update(self, message: str) -> None:
        """Receive an update message.

        Args:
            message: TODO.

        """
        ...


class SupportsExecuteInt(Protocol):
    """Protocol for integer strategies."""

    def execute(self, a: int, b: int) -> int:
        """Execute with two integer inputs.

        Args:
            a: TODO.
            b: TODO.

        Returns:
            TODO.

        """
        ...


class SupportsAction(Protocol):
    """Protocol for receiver objects."""

    def action(self) -> str:
        """Perform the action.

        Returns:
            TODO.

        """
        ...


class SupportsInitializedByMeta(Protocol):
    """Protocol for objects initialized by metaclass.

    Attributes:
        initialized_by_meta: TODO.

    """

    initialized_by_meta: bool


class SupportsNewMethod(Protocol):
    """Protocol for objects with new_method."""

    def new_method(self) -> str:
        """Return new method for testing.

        Returns:
            TODO.

        """
        ...


class SupportsVector(Protocol):
    """Protocol for vector-like objects.

    Attributes:
        x: TODO.
        y: TODO.

    """

    x: int
    y: int

    def __add__(self, other: SupportsVector) -> SupportsVector:
        """Add vectors.

        Args:
            other: TODO.

        Returns:
            TODO.

        """
        ...


type VectorFactory = Callable[[int, int], SupportsVector]


class MetaClass(type):
    """Metaclass for testing type inference."""

    def __new__(
        mcs: type[MetaClass],
        name: str,
        bases: tuple[type[object], ...],
        namespace: dict[str, object],
        **_kwargs: object,
    ) -> MetaClass:
        """Create a new class with ``meta_added``.

        Args:
            mcs: TODO.
            name: TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.

        """
        namespace["meta_added"] = True
        created: MetaClass = super().__new__(mcs, name, bases, namespace)
        return created

    def __call__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> object:
        """Create instance with ``initialized_by_meta``.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        instance: SupportsInitializedByMeta = cast(
            typ="SupportsInitializedByMeta",
            val=super().__call__(*args, **kwargs),
        )
        instance.initialized_by_meta = True
        return instance


class AbstractBase(ABC):
    """Abstract base class for testing type inference."""

    @abstractmethod
    def abstract_method(self, value: int) -> int:
        """Abstract method for testing.

        Args:
            value: TODO.

        Returns:
            TODO.

        """

    @classmethod
    @abstractmethod
    def class_method(cls) -> None:
        """Abstract class method for testing."""

    @staticmethod
    @abstractmethod
    def static_method() -> None:
        """Abstract static method for testing."""


class BaseClass:
    """Base class for testing type inference."""

    def __init__(self, x: int, y: int | None = None) -> None:
        """Initialize base class.

        Args:
            x: TODO.
            y: TODO.

        """
        self.x: int = x
        self.y: int | None = y

    def base_method(self, a: int, b: int = 10) -> int:
        """Test base method.

        Args:
            a: TODO.
            b: TODO.

        Returns:
            TODO.

        """
        return a + b

    @property
    def base_property(self) -> int:
        """Base property getter.

        Returns:
            TODO.

        """
        return self.x

    @base_property.setter
    def base_property(self, value: int) -> None:
        """Set base property.

        Args:
            value: TODO.

        """
        self.x = value


class DerivedClass(BaseClass, AbstractBase):
    """Derived class for testing type inference."""

    def __init__(self, x: int, y: int | None = None, z: int = 0) -> None:
        """Initialize derived class.

        Args:
            x: TODO.
            y: TODO.
            z: TODO.

        """
        super().__init__(x=x, y=y)
        self.z: int = z

    def abstract_method(self, value: int) -> int:
        """Implement abstract method.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        return value * 2

    @classmethod
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    def static_method() -> None:
        """Implement static method."""

    def derived_method(self, a: int, b: int, c: int = 5, d: int = 10) -> int:
        """Test derived method.

        Args:
            a: TODO.
            b: TODO.
            c: TODO.
            d: TODO.

        Returns:
            TODO.

        """
        if a > b:
            return a - b
        if a < b:
            return b - a
        return c + d


class MetaDecoratedClass:
    """Class with metaclass for testing."""

    def __init__(self, value: int) -> None:
        """Initialize meta decorated class.

        Args:
            value: TODO.

        """
        self.value: int = value


def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Multiply result by 2.

    Args:
        func: TODO.

    Returns:
        TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """TODO.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        result: R = func(*args, **kwargs)
        if isinstance(result, int):
            return cast(typ="R", val=result * 2)
        return result

    return wrapper


def decorator_with_args[**P, R](
    multiplier: int = 2,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Create decorator with configurable multiplier.

    Args:
        multiplier: TODO.

    Returns:
        TODO.

    """

    def actual_decorator(func: Callable[P, R]) -> Callable[P, R]:
        """TODO.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """TODO.

            Args:
                args: TODO.
                kwargs: TODO.

            Returns:
                TODO.

            """
            result: R = func(*args, **kwargs)
            if isinstance(result, int):
                return cast(typ="R", val=result * multiplier)
            return result

        return wrapper

    return actual_decorator


def decorator_with_class(cls: type[T]) -> type:
    """Wrap class in a proxy class.

    Args:
        cls: TODO.

    Returns:
        TODO.

    """

    class Wrapper:
        """Proxy wrapper created by a class decorator."""

        def __init__(self, *args: object, **_kwargs: object) -> None:
            """TODO.

            Args:
                args: TODO.
                _kwargs: TODO.

            """
            self.instance: T = cls(*args)

        def __getattr__(self, name: str) -> object:
            """Get attribute from wrapped instance.

            Args:
                name: TODO.

            Returns:
                TODO.

            """
            return getattr(self.instance, name)

    return cast(typ="type", val=Wrapper)


@decorator
def simple_function(x: int) -> int:
    """Test simple function.

    Args:
        x: TODO.

    Returns:
        TODO.

    """
    return x + 1


@decorator_with_args(multiplier=3)
def function_with_args(x: int, y: int = 5) -> int:
    """Test function with args.

    Args:
        x: TODO.
        y: TODO.

    Returns:
        TODO.

    """
    return x + y


@decorator_with_class
class DecoratedClass:
    """Class decorated with class decorator."""

    def __init__(self, value: int) -> None:
        """Initialize decorated class.

        Args:
            value: TODO.

        """
        self.value: int = value

    def method(self) -> int:
        """Test method.

        Returns:
            TODO.

        """
        return self.value


@dataclass(slots=True)
class DataClassExample:
    """Dataclass for testing type inference.

    Attributes:
        x: TODO.
        y: TODO.
        z: TODO.

    """

    x: int
    y: str = "default"
    z: list[int] = field(default_factory=list)


class EnumClass(Enum):
    """Enum class for testing type inference.

    Attributes:
        VALUE_A: TODO.
        VALUE_B: TODO.
        VALUE_C: TODO.

    """

    VALUE_A = auto()
    VALUE_B = auto()
    VALUE_C = auto()


def function_without_hints(
    a: int,
    b: int,
    c: int | None = None,
    d: int = 10,
    e: int = 20,
) -> int:
    """Test function without missing type hints.

    Args:
        a: TODO.
        b: TODO.
        c: TODO.
        d: TODO.
        e: TODO.

    Returns:
        TODO.

    """
    resolved_c: int = a + b if c is None else c
    return resolved_c + d + e


def function_with_kwargs(a: int, b: int = 5, **kwargs: int) -> int:
    """Test function with kwargs.

    Args:
        a: TODO.
        b: TODO.
        kwargs: TODO.

    Returns:
        TODO.

    """
    result: int = a + b
    for value in kwargs.values():
        result += value
    return result


def function_with_args_kwargs(*args: int, **kwargs: int) -> int:
    """Test function with args and kwargs.

    Args:
        args: TODO.
        kwargs: TODO.

    Returns:
        TODO.

    """
    total: int = sum(args)
    for value in kwargs.values():
        total += value
    return total


def nested_function(x: int, y: int, z: int) -> int:
    """Test nested function.

    Args:
        x: TODO.
        y: TODO.
        z: TODO.

    Returns:
        TODO.

    """

    def inner(a: int, b: int) -> int:
        """Inner function for testing.

        Args:
            a: TODO.
            b: TODO.

        Returns:
            TODO.

        """

        def deeper(c: int, d: int) -> int:
            """Deeper function for testing.

            Args:
                c: TODO.
                d: TODO.

            Returns:
                TODO.

            """
            return c * d

        return deeper(c=a, d=b) + a

    return inner(a=x, b=y) + z


def closure_function(x: int) -> Callable[[int], int]:
    """Test closure function.

    Args:
        x: TODO.

    Returns:
        TODO.

    """

    def inner(y: int) -> int:
        """Inner closure for testing.

        Args:
            y: TODO.

        Returns:
            TODO.

        """
        return x + y

    return inner


def function_with_slices(
    data: Sequence[T],
    start: int,
    end: int,
    step: int | None = None,
) -> Sequence[T]:
    """Test function with slices.

    Args:
        data: TODO.
        start: TODO.
        end: TODO.
        step: TODO.

    Returns:
        TODO.

    """
    if step is None:
        return data[start:end]
    return data[start:end:step]


def function_with_comprehensions(
    items: Sequence[int],
) -> tuple[list[int], dict[int, int], Generator[int]]:
    """Test function with comprehensions.

    Args:
        items: TODO.

    Returns:
        TODO.

    """
    squared: list[int] = [x**2 for x in items if x > 0]
    filtered: dict[int, int] = {
        k: v for k, v in enumerate(iterable=items) if v % 2 == 0
    }
    generator: Generator[int] = (
        x * 3 for x in items if x < Constants.max_value
    )
    return squared, filtered, generator


def function_with_lambdas(
    items: Sequence[str],
) -> tuple[list[str], list[str], list[str]]:
    """Test function with lambdas.

    Args:
        items: TODO.

    Returns:
        TODO.

    """
    sorted_items: list[str] = sorted(items, key=lambda x: x.lower())
    mapped: list[str] = [x.upper() for x in items]
    filtered: list[str] = [x for x in items if len(x) > Constants.min_length]
    return sorted_items, mapped, filtered


def function_with_recursion(n: int) -> int:
    """Test function with recursion.

    Args:
        n: TODO.

    Returns:
        TODO.

    """
    if n <= 1:
        return 1
    return n * function_with_recursion(n=n - 1)


def function_with_try_except(value: str) -> int:
    """Test function with try except.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    try:
        result: int = int(value)
    except ValueError:
        result = 0
    except TypeError:
        result = -1
    else:
        result *= 2
    finally:
        pass
    return result


def function_with_context() -> bool:
    """Test function with context.

    Returns:
        TODO.

    """
    with NamedTemporaryFile(mode="w", delete=False) as f:
        _ = f.write("test")
        temp_path: str = f.name
    Path(temp_path).unlink()
    return True


@contextmanager
def custom_context() -> Generator[str]:
    """Create custom context manager.

    Returns:
        TODO.

    """
    resource: str = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource=resource)


def acquire_resource() -> str:
    """Acquire resource.

    Returns:
        TODO.

    """
    return "resource"


def release_resource(resource: str) -> None:
    """Release resource.

    Args:
        resource: TODO.

    """
    resource = resource * 3


def function_with_generators() -> list[int]:
    """Test function with generators.

    Returns:
        TODO.

    """

    def generator() -> Generator[int]:
        """Generate values.

        Returns:
            TODO.

        """
        yield from range(10)

    return list(generator())


def function_with_coroutines() -> Callable[[int], Awaitable[int]]:
    """Test function with coroutines.

    Returns:
        TODO.

    """

    async def async_function(x: int) -> int:
        """Test async function.

        Args:
            x: TODO.

        Returns:
            TODO.

        """
        await sleep(delay=1)
        return x * 2

    return async_function


def function_with_class_methods() -> type[object]:
    """Test function with class methods.

    Returns:
        TODO.

    """

    class InnerClass:
        """Inner class for testing."""

        @classmethod
        def class_method(cls) -> str:
            """Implement class method.

            Returns:
                TODO.

            """
            return cls.__name__

        @staticmethod
        def static_method() -> str:
            """Implement static method.

            Returns:
                TODO.

            """
            return "static"

        def instance_method(self) -> str:
            """Test instance method.

            Returns:
                TODO.

            """
            return "instance"

    return InnerClass


def function_with_property() -> type[object]:
    """Test function with property.

    Returns:
        TODO.

    """

    class PropertyClass:
        """Test property class."""

        def __init__(self) -> None:
            """Initialize property class."""
            self._value: int = 0

        @property
        def value(self) -> int:
            """Get value property.

            Returns:
                TODO.

            """
            return self._value

        @value.setter
        def value(self, val: int) -> None:
            """Set value property.

            Args:
                val: TODO.

            """
            self._value = val

        @value.deleter
        def value(self) -> None:
            """Delete value property."""
            del self._value

    return PropertyClass


def function_with_descriptor() -> type[object]:
    """Test function with descriptor.

    Returns:
        TODO.

    """

    class Descriptor:
        """Test descriptor class."""

        def __init__(self) -> None:
            """TODO."""
            self._value: int = 0

        def __get__(self, obj: object, objtype: type[object]) -> int:
            """Get descriptor value.

            Args:
                obj: TODO.
                objtype: TODO.

            Returns:
                TODO.

            """
            _ = obj, objtype
            return self._value

        def __set__(self, obj: object, value: int) -> None:
            """Set descriptor value.

            Args:
                obj: TODO.
                value: TODO.

            """
            _ = obj
            self._value = value

        def __delete__(self, obj: object) -> None:
            """Delete descriptor value.

            Args:
                obj: TODO.

            """
            _ = obj
            del self._value

    return Descriptor


def function_with_operator_overloading() -> VectorFactory:
    """Test function with operator overloading.

    Returns:
        TODO.

    """

    class Vector:
        """Test vector class."""

        def __init__(self, x: int, y: int) -> None:
            """Initialize vector.

            Args:
                x: TODO.
                y: TODO.

            """
            self.x: int = x
            self.y: int = y

        def __add__(self, other: SupportsVector) -> Vector:
            """Add vectors.

            Args:
                other: TODO.

            Returns:
                TODO.

            """
            return Vector(x=self.x + other.x, y=self.y + other.y)

        def __sub__(self, other: Vector) -> Vector:
            """Subtract vectors.

            Args:
                other: TODO.

            Returns:
                TODO.

            """
            return Vector(x=self.x - other.x, y=self.y - other.y)

        def __mul__(self, scalar: int) -> Vector:
            """Multiply vector by scalar.

            Args:
                scalar: TODO.

            Returns:
                TODO.

            """
            return Vector(x=self.x * scalar, y=self.y * scalar)

        def __eq__(self, other: object) -> bool:
            """Check vector equality.

            Args:
                other: TODO.

            Returns:
                TODO.

            """
            if not isinstance(other, Vector):
                return False
            return self.x == other.x and self.y == other.y

        def __hash__(self) -> int:
            """Return hash of vector.

            Returns:
                TODO.

            """
            return hash((self.x, self.y))

        def __lt__(self, other: Vector) -> bool:
            """Check if vector is less than other.

            Args:
                other: TODO.

            Returns:
                TODO.

            """
            return self.x < other.x

        def __repr__(self) -> str:
            """Return vector representation.

            Returns:
                TODO.

            """
            return f"Vector({self.x}, {self.y})"

    return Vector


def function_with_metaclass_usage() -> object:
    """Test function with metaclass usage.

    Returns:
        TODO.

    """

    class MetaInstance:
        """Test meta instance class."""

    return MetaInstance()


def function_with_multiple_inheritance() -> type[object]:
    """Test function with multiple inheritance.

    Returns:
        TODO.

    """

    class MixinA:
        """Test mixin A class."""

        def method_a(self) -> str:
            """Test method A.

            Returns:
                TODO.

            """
            return "A"

    class MixinB:
        """Test mixin B class."""

        def method_b(self) -> str:
            """Test method B.

            Returns:
                TODO.

            """
            return "B"

    class Combined(MixinA, MixinB):
        """Test combined class."""

        def combined_method(self) -> str:
            """Test combined method.

            Returns:
                TODO.

            """
            return self.method_a() + self.method_b()

    return Combined


def function_with_abstract_methods() -> type[AbstractBase]:
    """Test function with abstract methods.

    Returns:
        TODO.

    """

    class AbstractImplementation(AbstractBase):
        """Test abstract implementation class."""

        def abstract_method(self, value: int) -> int:
            """Test abstract method.

            Args:
                value: TODO.

            Returns:
                TODO.

            """
            return value + 10

        @classmethod
        def class_method(cls) -> None:
            """Implement class method."""

        @staticmethod
        def static_method() -> None:
            """Implement static method."""

    return AbstractImplementation


def function_with_protocol() -> type[object]:
    """Test function with protocol.

    Returns:
        TODO.

    """

    class ProtocolImplementation:
        """Test protocol implementation class."""

        def protocol_method(self, x: int) -> int:
            """Test protocol method.

            Args:
                x: TODO.

            Returns:
                TODO.

            """
            return x * 2

    return ProtocolImplementation


def function_with_generic_types() -> tuple[int, int, str]:
    """Test function with generic types.

    Returns:
        TODO.

    """

    def generic_function(container: Sequence[T] | Mapping[T, U]) -> T | U:
        """Test generic function.

        Args:
            container: TODO.

        Returns:
            TODO.

        """
        if isinstance(container, Mapping):
            return next(iter(container.values()))
        return container[0]

    result1: int = generic_function(container=[1, 2, 3])
    result2: str | int = generic_function(container={"a": 1, "b": 2})
    result3: str = generic_function(container="hello")
    return int(result1), int(result2), str(object=result3)


def function_with_union_types() -> Callable[[int | str], int | str]:
    """Test function with union types.

    Returns:
        TODO.

    """

    def union_function(value: int | str) -> int | str:
        """Test union function.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        if isinstance(value, int):
            return value * 2
        if value:
            return value.upper()
        return str(object=value)

    return union_function


def function_with_optional_types() -> Callable[[object], object]:
    """Test function with optional types.

    Returns:
        TODO.

    """

    def optional_function(value: object = None) -> object:
        """Test optional function.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        if value is None:
            return "default"
        return value

    return optional_function


def function_with_callable() -> Callable[
    [Callable[[object], object], object],
    object,
]:
    """Test function with callable.

    Returns:
        TODO.

    """

    def callable_function(
        func: Callable[[object], object],
        arg: object,
    ) -> object:
        """Test callable function.

        Args:
            func: TODO.
            arg: TODO.

        Returns:
            TODO.

        """
        return func(arg)

    return callable_function


def function_with_tuple_unpacking() -> tuple[int, int, int, int, int]:
    """Test function with tuple unpacking.

    Returns:
        TODO.

    """
    data: tuple[int, int, int, int, int] = (1, 2, 3, 4, 5)
    a, b, *rest = data
    c, d, e = rest
    return a, b, c, d, e


def function_with_dict_operations() -> tuple[IntDict, IntDict]:
    """Test function with dict operations.

    Returns:
        TODO.

    """
    d1: IntDict = {"a": 1, "b": 2}
    d2: IntDict = {"c": 3, "d": 4}
    merged: IntDict = {**d1, **d2}
    filtered: IntDict = {k: v for k, v in merged.items() if v > 1}
    return merged, filtered


def function_with_set_operations() -> tuple[set[int], set[int], set[int]]:
    """Test function with set operations.

    Returns:
        TODO.

    """
    s1: set[int] = {1, 2, 3, 4}
    s2: set[int] = {3, 4, 5, 6}
    union: set[int] = s1 | s2
    intersection: set[int] = s1 & s2
    difference: set[int] = s1 - s2
    return union, intersection, difference


def function_with_bitwise_operations() -> tuple[int, int, int, int, int, int]:
    """Test function with bitwise operations.

    Returns:
        TODO.

    """
    a: int = 0b1010
    b: int = 0b1100
    and_result: int = a & b
    or_result: int = a | b
    xor_result: int = a ^ b
    not_result: int = ~a
    shift_left: int = a << 2
    shift_right: int = a >> 2
    return (
        and_result,
        or_result,
        xor_result,
        not_result,
        shift_left,
        shift_right,
    )


def function_with_augmented_assignment() -> int:
    """Test function with augmented assignment.

    Returns:
        TODO.

    """
    x: int = 10
    x += 5
    x -= 3
    x *= 2
    x = int(x / 4)
    x //= 2
    x %= 3
    x **= 2
    x &= 15
    x |= 8
    x ^= 5
    x <<= 1
    x >>= 1
    return x


def function_with_ternary() -> tuple[int, int]:
    """Test function with ternary.

    Returns:
        TODO.

    """
    x: int = 10
    y: int = 20
    max_val: int = max(y, x)
    min_val: int = min(y, x)
    return max_val, min_val


def function_with_chained_comparisons() -> tuple[bool, bool, bool]:
    """Test function with chained comparisons.

    Returns:
        TODO.

    """
    x: int = Constants.threshold
    result1: bool = 1 < x < Constants.max_value
    result2: bool = Constants.max_value > x > 0
    result3: bool = x == Constants.threshold or x != Constants.max_value
    return result1, result2, result3


def function_with_boolean_logic() -> tuple[bool, bool, bool, bool, bool]:
    """Test function with boolean logic.

    Returns:
        TODO.

    """
    a: bool = True
    b: bool = False
    c: bool = True
    result1: bool = a and b
    result2: bool = a or b
    result3: bool = not a
    result4: bool = (a and b) or c
    result5: bool = (a or b) and c
    return result1, result2, result3, result4, result5


def function_with_none_handling() -> tuple[int | None, int | None]:
    """Test function with none handling.

    Returns:
        TODO.

    """

    def maybe_none(value: int | None) -> int | None:
        """Maybe none function for testing.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        if value is None:
            return None
        return value * 2

    result1: int | None = maybe_none(value=5)
    result2: int | None = maybe_none(value=None)
    return result1, result2


def function_with_ellipsis() -> Callable[[int, int], int]:
    """Test function with ellipsis.

    Returns:
        TODO.

    """

    def ellipsis_function(a: int, b: int) -> int:
        """Ellipsis function for testing.

        Args:
            a: TODO.
            b: TODO.

        Returns:
            TODO.

        """
        return a + b

    return ellipsis_function


def function_with_star_expressions() -> list[int]:
    """Test function with star expressions.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3]
    return [*data, 4, 5]


def function_with_double_star_expressions() -> IntDict:
    """Test function with double star expressions.

    Returns:
        TODO.

    """
    d1: IntDict = {"a": 1}
    d2: IntDict = {"b": 2}
    return {**d1, **d2, "c": 3}


def function_with_matrix_multiplication() -> type[object]:
    """Test function with matrix multiplication.

    Returns:
        TODO.

    """

    class Matrix:
        """Test matrix class."""

        def __init__(self, data: list[list[int]]) -> None:
            """Initialize matrix with data.

            Args:
                data: TODO.

            """
            self.data: list[list[int]] = data

        def __matmul__(self, other: Matrix) -> Matrix:
            """Matrix multiplication operator.

            Args:
                other: TODO.

            Returns:
                TODO.

            """
            return Matrix(
                data=[
                    [
                        sum(a * b for a, b in zip(row, col, strict=True))
                        for col in zip(*other.data, strict=True)
                    ]
                    for row in self.data
                ],
            )

    return Matrix


def function_with_async_await() -> Callable[[], Awaitable[int]]:
    """Test function with async await.

    Returns:
        TODO.

    """

    async def async_func() -> int:
        """Async function for testing.

        Returns:
            TODO.

        """
        await sleep(delay=0.1)
        return 42

    return async_func


def function_with_type_annotations_missing() -> tuple[
    Callable[[int], int],
    Callable[[int, int], int],
    Callable[[int, int], int],
    Callable[..., int],
    Callable[..., int],
    Callable[..., int],
]:
    """Test formerly missing type annotations.

    Returns:
        TODO.

    """

    def func1(x: int) -> int:
        """Func1 for testing.

        Args:
            x: TODO.

        Returns:
            TODO.

        """
        return x + 1

    def func2(x: int, y: int) -> int:
        """Func2 for testing.

        Args:
            x: TODO.
            y: TODO.

        Returns:
            TODO.

        """
        return x + y

    def func3(x: int, y: int = 10) -> int:
        """Func3 for testing.

        Args:
            x: TODO.
            y: TODO.

        Returns:
            TODO.

        """
        return x * y

    def func4(*args: int) -> int:
        """Func4 for testing.

        Args:
            args: TODO.

        Returns:
            TODO.

        """
        return sum(args)

    def func5(**kwargs: int) -> int:
        """Func5 for testing.

        Args:
            kwargs: TODO.

        Returns:
            TODO.

        """
        return sum(kwargs.values())

    def func6(*args: int, **kwargs: int) -> int:
        """Func6 for testing.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        return sum(args) + sum(kwargs.values())

    return func1, func2, func3, func4, func5, func6


def function_with_complex_conditionals() -> Callable[[int, int, int], int]:
    """Test function with complex conditionals.

    Returns:
        TODO.

    """

    def complex_func(x: int, y: int, z: int) -> int:
        """Complex function for testing.

        Args:
            x: TODO.
            y: TODO.
            z: TODO.

        Returns:
            TODO.

        """
        x_sign: int = 1 if x > 0 else -1
        y_sign: int = 1 if y > 0 else -1
        z_sign: int = 1 if z > 0 else -1
        return x_sign * x + y_sign * y + z_sign * z

    return complex_func


def function_with_nested_loops() -> NestedLoopFunc:
    """Test function with nested loops.

    Returns:
        TODO.

    """

    def nested_loop_func(matrix: Sequence[Sequence[int]]) -> list[int]:
        """Nested loop function for testing.

        Args:
            matrix: TODO.

        Returns:
            TODO.

        """
        result: list[int] = []
        for row in matrix:
            row_sum: int = 0
            for element in row:
                row_sum += element
            result.append(row_sum)
        return result

    return nested_loop_func


def function_with_exception_chaining() -> Callable[[], None]:
    """Test function with exception chaining.

    Returns:
        TODO.

    """

    def exception_chain_func() -> None:
        """Exception chain function for testing."""

        def raise_first_error() -> None:
            """TODO.

            Raises:
                ValueError: TODO.

            """
            first_error: str = "First error"
            raise ValueError(first_error)

        def raise_second_error(original_error: ValueError) -> None:
            """TODO.

            Args:
                original_error: TODO.

            Raises:
                TypeError: TODO.

            """
            second_error: str = "Second error"
            raise TypeError(second_error) from original_error

        try:
            raise_first_error()
        except ValueError as e:
            raise_second_error(original_error=e)

    return exception_chain_func


def function_with_custom_exceptions() -> Callable[[], None]:
    """Test function with custom exceptions.

    Returns:
        TODO.

    """

    class CustomError(Exception):
        """Custom error for testing."""

    class AnotherCustomError(CustomError):
        """Another custom error for testing."""

    def raise_custom() -> None:
        """Raise custom function for testing.

        Raises:
            AnotherCustomError: TODO.

        """
        msg: str = "Custom error occurred"
        raise AnotherCustomError(msg)

    return raise_custom


def function_with_weak_refs() -> ReferenceType[object]:
    """Test function with weak refs.

    Returns:
        TODO.

    """

    class RefClass:
        """Ref class for testing."""

    obj: RefClass = RefClass()
    return ref(obj)


def function_with_slots() -> type[object]:
    """Test function with slots.

    Returns:
        TODO.

    """

    class SlottedClass:
        """Slotted class for testing.

        Attributes:
            __slots__: TODO.

        """

        __slots__ = ("x", "y")

        def __init__(self, x: int, y: int) -> None:
            """TODO.

            Args:
                x: TODO.
                y: TODO.

            """
            self.x: int = x
            self.y: int = y

    return SlottedClass


def function_with_class_decorator() -> type[object]:
    """Test function with class decorator.

    Returns:
        TODO.

    """

    def add_method(cls: type[T]) -> type[T]:
        """Add method for testing.

        Args:
            cls: TODO.

        Returns:
            TODO.

        """

        def new_method(self: T) -> str:
            """Add new method.

            Args:
                self: TODO.

            Returns:
                TODO.

            """
            _ = self
            return "added method"

        method_name: str = "new_method"
        setattr(cls, method_name, new_method)
        return cls

    @add_method
    class DecoratedByClass:
        """Test decorated by class."""

    return DecoratedByClass


def function_with_singleton() -> type[object]:
    """Test function with singleton.

    Returns:
        TODO.

    """

    class Singleton:
        """Test singleton class.

        Attributes:
            _instance: TODO.

        """

        _instance: Singleton | None = None

        def __new__(cls) -> Self:
            """Create singleton instance.

            Returns:
                TODO.

            """
            if cls._instance is None:
                cls._instance = super().__new__(cls=cls)
            return cast(typ="Self", val=cls._instance)

    return Singleton


def function_with_factory() -> type[object]:
    """Test function with factory.

    Returns:
        TODO.

    """

    class TypeA:
        """Type A for testing."""

    class TypeB:
        """Type B for testing."""

    class Factory:
        """Test factory class."""

        @staticmethod
        def create(type_name: str) -> TypeA | TypeB | None:
            """Create type for testing.

            Args:
                type_name: TODO.

            Returns:
                TODO.

            """
            if type_name == "a":
                return TypeA()
            if type_name == "b":
                return TypeB()
            return None

    return Factory


def function_with_builder() -> type[object]:
    """Test function with builder.

    Returns:
        TODO.

    """

    class Product:
        """Product class for testing."""

        def __init__(self, parts: Sequence[str]) -> None:
            """Initialize product with parts.

            Args:
                parts: TODO.

            """
            self.parts: list[str] = list(parts)

    class Builder:
        """Test builder class."""

        def __init__(self) -> None:
            """TODO."""
            self.parts: list[str] = []

        def add_part(self, part: str) -> Self:
            """TODO.

            Args:
                part: TODO.

            Returns:
                TODO.

            """
            self.parts.append(part)
            return self

        def build(self) -> Product:
            """TODO.

            Returns:
                TODO.

            """
            return Product(parts=self.parts)

    return Builder


def function_with_observer() -> tuple[type[object], type[object]]:
    """Test function with observer.

    Returns:
        TODO.

    """

    class Observer:
        """Test observer class."""

        def update(self, message: str) -> None:
            """Update observer with message.

            Args:
                message: TODO.

            """
            _ = self, message

    class Subject:
        """Test subject class."""

        def __init__(self) -> None:
            """Initialize subject."""
            self.observers: list[SupportsUpdate] = []

        def attach(self, observer: SupportsUpdate) -> None:
            """Attach observer to subject.

            Args:
                observer: TODO.

            """
            self.observers.append(observer)

        def notify(self, message: str) -> None:
            """Notify all observers with message.

            Args:
                message: TODO.

            """
            for observer in self.observers:
                observer.update(message=message)

    return Subject, Observer


def function_with_strategy() -> tuple[type[object], type[object]]:
    """Test function with strategy.

    Returns:
        TODO.

    """

    class Strategy:
        """Test strategy class."""

        def execute(self, a: int, b: int) -> int:
            """Execute strategy.

            Args:
                a: TODO.
                b: TODO.

            Returns:
                TODO.

            """
            _ = self, a, b
            return 0

    class AddStrategy(Strategy):
        """Test add strategy."""

        def execute(self, a: int, b: int) -> int:
            """Execute add strategy.

            Args:
                a: TODO.
                b: TODO.

            Returns:
                TODO.

            """
            return a + b

    class MultiplyStrategy(Strategy):
        """Test multiply strategy."""

        def execute(self, a: int, b: int) -> int:
            """Execute multiply strategy.

            Args:
                a: TODO.
                b: TODO.

            Returns:
                TODO.

            """
            return a * b

    return AddStrategy, MultiplyStrategy


def function_with_command() -> tuple[type[object], type[object]]:
    """Test function with command.

    Returns:
        TODO.

    """

    class Command:
        """Test command class."""

        def execute(self) -> None:
            """Execute command."""

    class Receiver:
        """Test receiver class."""

        def action(self) -> str:
            """Perform action.

            Returns:
                TODO.

            """
            return "Action performed"

    class ConcreteCommand(Command):
        """Test concrete command."""

        def __init__(self, receiver: SupportsAction) -> None:
            """TODO.

            Args:
                receiver: TODO.

            """
            self.receiver: SupportsAction = receiver

        def execute(self) -> None:
            """TODO."""
            self.receiver.action()

    return ConcreteCommand, Receiver


def function_with_chain_of_responsibility() -> type[object]:
    """Test function with chain of responsibility.

    Returns:
        TODO.

    """

    class Handler:
        """Test handler class."""

        def __init__(self) -> None:
            """Initialize handler."""
            self.next: Handler | None = None

        def set_next(self, handler: Handler) -> Handler:
            """Set next handler.

            Args:
                handler: TODO.

            Returns:
                TODO.

            """
            self.next = handler
            return handler

        def handle(self, request: str) -> str | None:
            """Handle request.

            Args:
                request: TODO.

            Returns:
                TODO.

            """
            if self.next is not None:
                return self.next.handle(request=request)
            return None

    return Handler


def function_with_decorator_stack() -> Callable[[], str]:
    """Test function with decorator stack.

    Returns:
        TODO.

    """

    def decorator1(func: Callable[P, R]) -> Callable[P, R]:
        """Test decorator 1.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Wrap decorator 1.

            Args:
                args: TODO.
                kwargs: TODO.

            Returns:
                TODO.

            """
            return func(*args, **kwargs)

        return wrapper

    def decorator2(func: Callable[P, R]) -> Callable[P, R]:
        """Test decorator 2.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Wrap decorator 2.

            Args:
                args: TODO.
                kwargs: TODO.

            Returns:
                TODO.

            """
            return func(*args, **kwargs)

        return wrapper

    @decorator1
    @decorator2
    def stacked_func() -> str:
        """Test stacked function.

        Returns:
            TODO.

        """
        return "stacked"

    return stacked_func


def function_with_partial() -> Callable[[int], int]:
    """Test function with partial.

    Returns:
        TODO.

    """

    def multiply(a: int, b: int) -> int:
        """Test multiply function.

        Args:
            a: TODO.
            b: TODO.

        Returns:
            TODO.

        """
        return a * b

    return partial(multiply, 2)


def function_with_reduce() -> int:
    """Test function with reduce.

    Returns:
        TODO.

    """
    numbers: list[int] = [1, 2, 3, 4, 5]
    return reduce(lambda x, y: x + y, numbers)


def function_with_groupby() -> dict[str, list[int]]:
    """Test function with groupby.

    Returns:
        TODO.

    """
    data: list[tuple[str, int]] = [("a", 1), ("b", 2), ("a", 3), ("b", 4)]
    return {
        k: [v for _, v in g]
        for k, g in groupby(iterable=sorted(data), key=lambda x: x[0])
    }


def function_with_permutations_combinations() -> tuple[
    list[tuple[int, ...]],
    list[tuple[int, ...]],
]:
    """Test function with permutations and combinations.

    Returns:
        TODO.

    """
    items: list[int] = [1, 2, 3]
    perms: list[tuple[int, ...]] = list(permutations(iterable=items, r=2))
    combs: list[tuple[int, ...]] = list(combinations(iterable=items, r=2))
    return perms, combs


def function_with_defaultdict() -> defaultdict[str, int]:
    """Test function with defaultdict.

    Returns:
        TODO.

    """
    d: defaultdict[str, int] = defaultdict(int)
    d["a"] += 1
    d["b"] += 2
    return d


def function_with_counter() -> Counter[int]:
    """Test function with counter.

    Returns:
        TODO.

    """
    return Counter([1, 2, 2, 3, 3, 3])


def function_with_deque() -> deque[int]:
    """Test function with deque.

    Returns:
        TODO.

    """
    d: deque[int] = deque(iterable=[1, 2, 3])
    d.append(4)
    d.appendleft(0)
    d.pop()
    d.popleft()
    return d


def function_with_ordereddict() -> OrderedDict[str, int]:
    """Test function with ordereddict.

    Returns:
        TODO.

    """
    return OrderedDict([("a", 1), ("b", 2), ("c", 3)])


def function_with_namedtuple() -> Point:
    """Test function with namedtuple.

    Returns:
        TODO.

    """
    return Point(x=1, y=2)


class Point(NamedTuple):
    """Test point.

    Attributes:
        x: TODO.
        y: TODO.

    """

    x: int
    y: int


def function_with_chain() -> list[int]:
    """Test function with chain.

    Returns:
        TODO.

    """
    list1: list[int] = [1, 2, 3]
    list2: list[int] = [4, 5, 6]
    return list(chain(list1, list2))


def function_with_islice() -> list[int]:
    """Test function with islice.

    Returns:
        TODO.

    """
    data: range = range(10)
    return list(islice(data, 2, 8, 2))


def function_with_takewhile_dropwhile() -> tuple[list[int], list[int]]:
    """Test function with takewhile and dropwhile.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    taken: list[int] = list(takewhile(lambda x: x < Constants.threshold, data))
    dropped: list[int] = list(
        dropwhile(lambda x: x < Constants.threshold, data),
    )
    return taken, dropped


def function_with_zip_longest() -> list[tuple[int | None, str | None]]:
    """Test function with zip longest.

    Returns:
        TODO.

    """
    list1: list[int] = [1, 2, 3]
    list2: list[str] = ["a", "b"]
    return list(zip_longest(list1, list2, fillvalue=None))


def function_with_product() -> list[tuple[int, str]]:
    """Test function with product.

    Returns:
        TODO.

    """
    list1: list[int] = [1, 2]
    list2: list[str] = ["a", "b"]
    return list(product(list1, list2))


def function_with_positional_and_keyword_only(
    pos_only: int,
    /,
    normal: int,
    *,
    kw_only: int,
) -> int:
    """Test function with positional-only and keyword-only arguments.

    Args:
        pos_only: TODO.
        normal: TODO.
        kw_only: TODO.

    Returns:
        TODO.

    """
    return pos_only + normal + kw_only


def function_with_compress() -> list[int]:
    """Test function with compress.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5]
    selectors: list[bool] = [True, False, True, False, True]
    return list(compress(data=data, selectors=selectors))


def function_with_accumulate() -> list[int]:
    """Test function with accumulate.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5]
    return list(accumulate(iterable=data))


def function_with_conditional_output(
    value: int,
    mode: str,
) -> list[int] | IntDict | str | int:
    """Test function with conditions, globals, and conditional output type.

    Args:
        value: TODO.
        mode: TODO.

    Returns:
        TODO.

    """
    if value > Constants.threshold and mode == "list":
        return [value * 2 for _ in range(Constants.max_value)]
    if value < Constants.threshold and mode == "dict":
        return {str(object=i): i * value for i in range(Constants.min_length)}
    if value == Constants.threshold and mode == "str":
        return str(object=value) * Constants.max_value
    return value + Constants.max_value


def test_function_calls_part1() -> TestResult:
    """Test basic function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result1: int = function_without_hints(a=1, b=2)
    result2: int = function_without_hints(a=1, b=2, c=3, d=4, e=5)
    result3: int = function_with_kwargs(a=10, b=20, c=30, d=40)
    result4: int = function_with_args_kwargs(1, 2, 3, a=4, b=5)
    result5: int = nested_function(x=1, y=2, z=3)
    result6: Sequence[int] = function_with_slices(
        data=[1, 2, 3, 4, 5],
        start=1,
        end=4,
    )
    result7: Sequence[int] = function_with_slices(
        data=[1, 2, 3, 4, 5],
        start=0,
        end=5,
        step=2,
    )
    result8: tuple[list[int], dict[int, int], Generator[int]] = (
        function_with_comprehensions(items=[1, 2, 3, 4, 5])
    )
    result9: tuple[list[str], list[str], list[str]] = function_with_lambdas(
        items=["apple", "banana", "cherry"],
    )
    result10: int = function_with_recursion(n=5)
    result11: int = function_with_try_except(value="123")
    result12: int = function_with_try_except(value="abc")
    result13: list[int] = function_with_generators()
    result14: type[object] = function_with_class_methods()
    result15: type[object] = function_with_property()
    result16: VectorFactory = function_with_operator_overloading()
    result17: object = function_with_metaclass_usage()
    result18: type[object] = function_with_multiple_inheritance()
    result19: type[AbstractBase] = function_with_abstract_methods()
    result20: tuple[int, int, str] = function_with_generic_types()
    result21: Callable[[int | str], int | str] = function_with_union_types()
    result22: Callable[[object], object] = function_with_optional_types()
    return {
        "result1": result1,
        "result2": result2,
        "result3": result3,
        "result4": result4,
        "result5": result5,
        "result6": result6,
        "result7": result7,
        "result8": result8,
        "result9": result9,
        "result10": result10,
        "result11": result11,
        "result12": result12,
        "result13": result13,
        "result14": result14,
        "result15": result15,
        "result16": result16,
        "result17": result17,
        "result18": result18,
        "result19": result19,
        "result20": result20,
        "result21": result21,
        "result22": result22,
    }


def test_function_calls_part2() -> TestResult:
    """Test intermediate function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result23: tuple[int, int, int, int, int] = function_with_tuple_unpacking()
    result24: tuple[IntDict, IntDict] = function_with_dict_operations()
    result25: tuple[set[int], set[int], set[int]] = (
        function_with_set_operations()
    )
    result26: tuple[int, int, int, int, int, int] = (
        function_with_bitwise_operations()
    )
    result27: int = function_with_augmented_assignment()
    result28: tuple[int, int] = function_with_ternary()
    result29: tuple[bool, bool, bool] = function_with_chained_comparisons()
    result30: tuple[bool, bool, bool, bool, bool] = (
        function_with_boolean_logic()
    )
    result31: tuple[int | None, int | None] = function_with_none_handling()
    result32: list[int] = function_with_star_expressions()
    result33: IntDict = function_with_double_star_expressions()
    result34: tuple[
        Callable[[int], int],
        Callable[[int, int], int],
        Callable[[int, int], int],
        Callable[..., int],
        Callable[..., int],
        Callable[..., int],
    ] = function_with_type_annotations_missing()
    result35: int = function_with_complex_conditionals()(1, 2, 3)
    nested_loop: NestedLoopFunc = function_with_nested_loops()
    result36: list[int] = nested_loop([[1, 2], [3, 4], [5, 6]])
    result37: type[object] = function_with_slots()
    result38: type[object] = function_with_class_decorator()
    result39: type[object] = function_with_singleton()
    result40: type[object] = function_with_factory()
    result41: type[object] = function_with_builder()
    result42: tuple[type[object], type[object]] = function_with_observer()
    result43: tuple[type[object], type[object]] = function_with_strategy()
    result44: tuple[type[object], type[object]] = function_with_command()
    return {
        "result23": result23,
        "result24": result24,
        "result25": result25,
        "result26": result26,
        "result27": result27,
        "result28": result28,
        "result29": result29,
        "result30": result30,
        "result31": result31,
        "result32": result32,
        "result33": result33,
        "result34": result34,
        "result35": result35,
        "result36": result36,
        "result37": result37,
        "result38": result38,
        "result39": result39,
        "result40": result40,
        "result41": result41,
        "result42": result42,
        "result43": result43,
        "result44": result44,
    }


def test_function_calls_part3() -> TestResult:
    """Test advanced function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result45: type[object] = function_with_chain_of_responsibility()
    result46: Callable[[], str] = function_with_decorator_stack()
    result47: Callable[[int], int] = function_with_partial()
    result48: int = function_with_reduce()
    result49: dict[str, list[int]] = function_with_groupby()
    result50: tuple[list[tuple[int, ...]], list[tuple[int, ...]]] = (
        function_with_permutations_combinations()
    )
    result51: defaultdict[str, int] = function_with_defaultdict()
    result52: Counter[int] = function_with_counter()
    result53: deque[int] = function_with_deque()
    result54: OrderedDict[str, int] = function_with_ordereddict()
    result55: Point = function_with_namedtuple()
    result56: list[int] = function_with_chain()
    result57: list[int] = function_with_islice()
    result58: tuple[list[int], list[int]] = function_with_takewhile_dropwhile()
    result59: list[tuple[int | None, str | None]] = function_with_zip_longest()
    result60: list[tuple[int, str]] = function_with_product()
    result61: list[int] = function_with_compress()
    result62: list[int] = function_with_accumulate()
    result63: ConditionalResult = function_with_conditional_output(
        value=10,
        mode="list",
    )
    result64: ConditionalResult = function_with_conditional_output(
        value=3,
        mode="dict",
    )
    result65: ConditionalResult = function_with_conditional_output(
        value=5,
        mode="str",
    )
    result66: ConditionalResult = function_with_conditional_output(
        value=7,
        mode="other",
    )
    return {
        "result45": result45,
        "result46": result46,
        "result47": result47,
        "result48": result48,
        "result49": result49,
        "result50": result50,
        "result51": result51,
        "result52": result52,
        "result53": result53,
        "result54": result54,
        "result55": result55,
        "result56": result56,
        "result57": result57,
        "result58": result58,
        "result59": result59,
        "result60": result60,
        "result61": result61,
        "result62": result62,
        "result63": result63,
        "result64": result64,
        "result65": result65,
        "result66": result66,
    }


def test_function_calls() -> TestResult:
    """Test various function calls with kwargs where possible.

    Returns:
        TODO.

    """
    return {
        **test_function_calls_part1(),
        **test_function_calls_part2(),
        **test_function_calls_part3(),
    }


def test_class_instantiations() -> TestResult:
    """Test class instantiations with kwargs where possible.

    Returns:
        TODO.

    """
    return {
        "obj1": BaseClass(x=10),
        "obj2": BaseClass(x=10, y=20),
        "obj3": DerivedClass(x=10, y=20, z=30),
        "obj4": MetaDecoratedClass(value=100),
        "obj5": DataClassExample(x=1, y="test"),
        "obj6": cast(typ="object", val=DecoratedClass(value=50)),
    }


def test_other_operations() -> TestResult:
    """Test enum, closure, context, and vector operations.

    Returns:
        TODO.

    """
    enum_val: EnumClass = EnumClass.VALUE_A
    closure: Callable[[int], int] = closure_function(x=10)
    closure_result: int = closure(5)
    with custom_context() as resource:
        context_result: str = resource
    vector: VectorFactory = function_with_operator_overloading()
    vec: SupportsVector = vector(1, 2)
    vec2: SupportsVector = vector(3, 4)
    vec_sum: SupportsVector = vec + vec2
    return {
        "enum_val": enum_val,
        "closure_result": closure_result,
        "context_result": context_result,
        "vec_sum": vec_sum,
    }


class SliceExampleResult(NamedTuple):
    """Result for list and dictionary slice inference examples.

    Attributes:
        list_slice: TODO.
        list_stride_slice: TODO.
        dict_slice: TODO.
        dict_key_slice: TODO.
        dict_value_slice: TODO.

    """

    list_slice: list[int]
    list_stride_slice: list[int]
    dict_slice: dict[str, int]
    dict_key_slice: list[str]
    dict_value_slice: list[int]


class BuiltinMethodList(list[int]):
    """List subclass whose method names intentionally shadow builtins."""

    def append(self, value: int) -> None:
        """Append a doubled integer, unlike ``list.append`` semantics.

        Args:
            value: TODO.

        """
        super().append(value * 2)

    def count(self, value: int) -> int:
        """Return the normal list count plus one for disambiguation.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        return super().count(value) + 1


class BuiltinMethodDict(dict[str, int]):
    """Dict subclass with names shared by built-in dict methods."""


class CustomAddSet(set[int]):
    """Set subclass with the same method name as a custom class below."""

    def add(self, element: int) -> None:
        """Add a shifted element.

        Args:
            element: TODO.

        """
        super().add(element + 100)


class CustomAdder:
    """Plain custom class with ``add`` sharing a name with ``set.add``."""

    def __init__(self, seed: int) -> None:
        """Initialize custom adder.

        Args:
            seed: TODO.

        """
        self.seed: int = seed

    def add(self, element: int) -> int:
        """Return an arithmetic result instead of mutating a set.

        Args:
            element: TODO.

        Returns:
            TODO.

        """
        return self.seed + element


class ImportExampleResult(NamedTuple):
    """Result for importlib and ``__import__`` inference examples.

    Attributes:
        importlib_module_name: TODO.
        dunder_module_name: TODO.
        imported_join_result: TODO.

    """

    importlib_module_name: str
    dunder_module_name: str
    imported_join_result: str


class RedefinitionResult(NamedTuple):
    """Result for variable type redefinition examples.

    Attributes:
        first_type_value: TODO.
        second_type_value: TODO.
        third_type_value: TODO.
        union_final_value: TODO.

    """

    first_type_value: int
    second_type_value: str
    third_type_value: list[int]
    union_final_value: dict[str, int]


class ScopeResolutionResult(NamedTuple):
    """Result for same names in nested, class, and module scopes.

    Attributes:
        module_value: TODO.
        outer_value: TODO.
        inner_value: TODO.
        class_value: TODO.
        method_and_nested_results: TODO.

    """

    module_value: str
    outer_value: int
    inner_value: list[int]
    class_value: str
    method_and_nested_results: list[float | str]


def duplicate_scope_name(value: str) -> str:
    """Module-scope function intentionally reused in inner scopes.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    return f"module:{value}"


def function_with_list_and_dict_slices() -> SliceExampleResult:
    """Assign variables from slices of lists and dictionary views.

    Returns:
        TODO.

    """
    numbers: list[int] = [10, 20, 30, 40, 50, 60]
    mapping: dict[str, int] = {
        "alpha": 1,
        "beta": 2,
        "gamma": 3,
        "delta": 4,
    }
    list_slice: list[int] = numbers[1:4]
    list_stride_slice: list[int] = numbers[::2]
    dict_slice: dict[str, int] = dict(islice(mapping.items(), 1, 3))
    dict_key_slice: list[str] = list(mapping.keys())[1:]
    dict_value_slice: list[int] = list(mapping.values())[:3]
    return SliceExampleResult(
        list_slice=list_slice,
        list_stride_slice=list_stride_slice,
        dict_slice=dict_slice,
        dict_key_slice=dict_key_slice,
        dict_value_slice=dict_value_slice,
    )


def function_with_builtin_name_collisions() -> tuple[
    BuiltinMethodList,
    BuiltinMethodDict,
    CustomAddSet,
    int,
]:
    """Disambiguate builtin method names from custom method names.

    Returns:
        TODO.

    """
    custom_list: BuiltinMethodList = BuiltinMethodList([1, 2, 2])
    builtin_list: list[int] = [1, 2, 2]
    custom_list.append(value=3)
    builtin_list.append(3)
    custom_count: int = custom_list.count(value=2)
    builtin_count: int = builtin_list.count(2)

    custom_dict: BuiltinMethodDict = BuiltinMethodDict({"a": 1})
    builtin_dict: dict[str, int] = {"a": 1}
    custom_dict.update({"b": 2}, c=3)
    builtin_dict.update({"b": 2}, c=3)

    custom_set: CustomAddSet = CustomAddSet({1, 2})
    builtin_set: set[int] = {1, 2}
    custom_set.add(element=5)
    builtin_set.add(5)

    adder: CustomAdder = CustomAdder(seed=40)
    adder_result: int = adder.add(element=2)
    collision_score: int = custom_count + builtin_count + adder_result
    return custom_list, custom_dict, custom_set, collision_score


def function_with_importlib_and_dunder_import() -> ImportExampleResult:
    """Use both importlib and ``__import__`` in resolvable examples.

    Returns:
        TODO.

    """
    pathlib_module: ModuleType = import_module(name="pathlib")
    os_path_module: ModuleType = __import__(name="os.path")
    imported_join_result: str = os_path_module.path.join("a", "b")
    return ImportExampleResult(
        importlib_module_name=pathlib_module.__name__,
        dunder_module_name=os_path_module.__name__,
        imported_join_result=imported_join_result,
    )


def function_with_variable_type_redefinition() -> RedefinitionResult:
    """Redefine variable types in a deliberate linear flow.

    Returns:
        TODO.

    """
    evolving_value: int | str | list[int] | dict[str, int]
    evolving_value = 10
    first_type_value: int = evolving_value
    evolving_value = "ten"
    second_type_value: str = evolving_value
    evolving_value = [1, 2, 3]
    third_type_value: list[int] = evolving_value
    evolving_value = {"ten": 10}
    union_final_value: dict[str, int] = evolving_value
    return RedefinitionResult(
        first_type_value=first_type_value,
        second_type_value=second_type_value,
        third_type_value=third_type_value,
        union_final_value=union_final_value,
    )


def function_with_scope_resolution() -> ScopeResolutionResult:
    """Use identical names in module, function, nested, and class scopes.

    Returns:
        TODO.

    """
    duplicated_name: int = 7

    def duplicate_scope_name(value: int) -> str:
        """Inner function that shadows the module-level function.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        duplicated_name: list[int] = [value, value + 1]

        def deepest() -> list[int]:
            """Return the innermost variable with the reused name.

            Returns:
                TODO.

            """
            return duplicated_name

        return f"inner:{sum(deepest())}"

    class DuplicateScopeNameClass:
        """Class with same conceptual name family as outer symbols.

        Attributes:
            duplicated_name: TODO.

        """

        duplicated_name: str = "class"

        def method(self) -> float:
            """Return a method-local value with a reused variable name.

            Returns:
                TODO.

            """
            duplicated_name: float = 3.5
            return duplicated_name

    instance: DuplicateScopeNameClass = DuplicateScopeNameClass()
    nested_function_result: str = duplicate_scope_name(value=duplicated_name)
    module_value: str = globals()["duplicate_scope_name"]("root")
    return ScopeResolutionResult(
        module_value=module_value,
        outer_value=duplicated_name,
        inner_value=[duplicated_name, duplicated_name + 1],
        class_value=instance.duplicated_name,
        method_and_nested_results=[instance.method(), nested_function_result],
    )


def test_new_inference_edge_cases() -> TestResult:
    """Run extra tests for slices, builtins, imports, and scoping.

    Returns:
        TODO.

    """
    return {
        "slices": function_with_list_and_dict_slices(),
        "builtin_name_collisions": function_with_builtin_name_collisions(),
        "imports": function_with_importlib_and_dunder_import(),
        "redefinitions": function_with_variable_type_redefinition(),
        "scope_resolution": function_with_scope_resolution(),
        "positional_and_keyword_only": [
            function_with_positional_and_keyword_only(
                1,
                normal=2,
                kw_only=3,
            ),
        ],
    }

    # ------------------------------------------------------------------------
    # Extended stress cases for automatic type inference.
    # ------------------------------------------------------------------------


class ExtendedResult:
    """Tiny tuple-like result container."""

    def __init__(
        self,
        name: str,
        payload: object,
        metadata: ExtendedMetadata | None = None,
    ) -> None:
        """Store a name, payload, and metadata mapping.

        Args:
            name: TODO.
            payload: TODO.
            metadata: TODO.

        """
        self.name: str = name
        self.payload: object = payload
        self.metadata: ExtendedMetadata = {} if metadata is None else metadata

    def __iter__(self) -> Iterator[object]:
        """Iterate over stored fields.

        Returns:
            TODO.

        """
        yield self.name
        yield self.payload
        yield self.metadata

    def __len__(self) -> int:
        """Return tuple-like field count.

        Returns:
            TODO.

        """
        return 3

    def __getitem__(self, index: int | str) -> object:
        """Return one field by index or name.

        Args:
            index: TODO.

        Returns:
            TODO.

        Raises:
            IndexError: TODO.

        """
        if index in {0, "name"}:
            return self.name
        if index in {1, "payload"}:
            return self.payload
        metadata_indexes: set[int | str] = {2, "metadata"}
        if index in metadata_indexes:
            return self.metadata
        raise IndexError(index)


class ExtendedDataclassStress:
    """Dataclass-like class with factory-style defaults."""

    def __init__(
        self,
        name: str = "anonymous",
        values: list[int] | None = None,
        lookup: dict[str, int] | None = None,
        flags: set[bool] | None = None,
    ) -> None:
        """Initialize values without leaking mutable defaults.

        Args:
            name: TODO.
            values: TODO.
            lookup: TODO.
            flags: TODO.

        """
        self.name: str = name
        self.values: list[int] = [] if values is None else values
        self.lookup: dict[str, int] = {} if lookup is None else lookup
        self.flags: set[bool] = set() if flags is None else flags
        self.lookup.setdefault(self.name, len(self.values))
        self.flags.add(self.name in self.lookup)
        self.normalized: tuple[tuple[str, int], ...] = tuple(
            sorted(self.lookup.items()),
        )


class DescriptorWithOwnerCache:
    """Descriptor using WeakKeyDictionary to stress descriptor inference."""

    def __init__(self, default: object) -> None:
        """Initialize descriptor storage.

        Args:
            default: TODO.

        """
        self.default: object = default
        self.storage: WeakKeyDictionary[object, object] = WeakKeyDictionary()
        self.owner: type[object] | None = None
        self.name: str = ""

    def __set_name__(self, owner: type[object], name: str) -> None:
        """Store the owner/name pair.

        Args:
            owner: TODO.
            name: TODO.

        """
        self.owner = owner
        self.name = name

    def __get__(
        self,
        instance: object | None,
        owner: type[object] | None = None,
    ) -> object:
        """Return descriptor or stored instance value.

        Args:
            instance: TODO.
            owner: TODO.

        Returns:
            TODO.

        """
        _ = owner
        if instance is None:
            return self
        return self.storage.get(instance, self.default)

    def __set__(self, instance: object, value: object) -> None:
        """Set a value in weak storage.

        Args:
            instance: TODO.
            value: TODO.

        """
        self.storage[instance] = value

    def __delete__(self, instance: object) -> None:
        """Delete value if present.

        Args:
            instance: TODO.

        """
        with suppress(KeyError):
            del self.storage[instance]


class DescriptorStressOwner:
    """Owner class for descriptor stress.

    Attributes:
        score: TODO.
        label: TODO.

    """

    score: ClassVar[DescriptorWithOwnerCache] = DescriptorWithOwnerCache(
        default=0,
    )
    label: ClassVar[DescriptorWithOwnerCache] = DescriptorWithOwnerCache(
        default="unset",
    )

    def __init__(self, score: int, label: str) -> None:
        """Initialize descriptor-backed fields.

        Args:
            score: TODO.
            label: TODO.

        """
        self.score = score
        self.label = label

    @cached_property
    def summary(self) -> dict[str, object]:
        """Return cached mixed summary.

        Returns:
            TODO.

        """
        return {"score": self.score, "label": self.label}


class RegistryMeta(type):
    """Metaclass that registers subclasses and injects attributes.

    Attributes:
        registry: TODO.

    """

    registry: ClassVar[dict[str, type[object]]] = {}

    def __new__(
        mcls: type[RegistryMeta],
        name: str,
        bases: tuple[type[object], ...],
        namespace: dict[str, object],
        **_kwargs: object,
    ) -> RegistryMeta:
        """Create class and register it by lower-case name.

        Args:
            mcls: TODO.
            name: TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.

        """
        namespace.setdefault("created_by_registry_meta", True)
        cls: RegistryMeta = super().__new__(mcls, name, bases, namespace)
        if not name.startswith("Abstract"):
            mcls.registry[name.lower()] = cast(typ="type[object]", val=cls)
        return cls

    def __call__(cls, *args: object, **kwargs: object) -> object:
        """Create instance and mark it.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        instance = super().__call__(*args, **kwargs)
        instance.registry_key = cls.__name__.lower()
        return instance


class RegistryBase(metaclass=RegistryMeta):
    """Base class using RegistryMeta."""

    def clone(self, **overrides: object) -> object:
        """Clone using the current instance dictionary.

        Args:
            overrides: TODO.

        Returns:
            TODO.

        """
        data: dict[str, object] = dict(self.__dict__)
        data.update(overrides)
        return self.__class__(**data)


class RegistryItem(RegistryBase):
    """Concrete registry item."""

    def __init__(
        self,
        name: str,
        count: int = 0,
        tags: list[str] | None = None,
        **extras: object,
    ) -> None:
        """Initialize with optional tags and arbitrary extras.

        Args:
            name: TODO.
            count: TODO.
            tags: TODO.
            extras: TODO.

        """
        self.name: str = name
        self.count: int = count
        self.tags: list[str] = [] if tags is None else tags
        self.extras: dict[str, object] = extras

    def bump(self, amount: int = 1) -> Self:
        """Increment count and return self for chaining.

        Args:
            amount: TODO.

        Returns:
            TODO.

        """
        self.count += amount
        return self


class FluentBuilder:
    """Builder with fluent methods and conditional finalization."""

    def __init__(self) -> None:
        """Initialize builder state."""
        self.parts: list[str] = []
        self.options: dict[str, object] = {}

    def add(self, part: str, *, repeat: int = 1) -> Self:
        """Add repeated parts and return self.

        Args:
            part: TODO.
            repeat: TODO.

        Returns:
            TODO.

        """
        for _ in range(repeat):
            self.parts.append(part)
        return self

    def configure(self, **options: object) -> Self:
        """Merge options and return self.

        Args:
            options: TODO.

        Returns:
            TODO.

        """
        self.options.update(options)
        return self

    def build(self, *, compact: bool = False) -> str | dict[str, object]:
        """Return a compact string or a structured result.

        Args:
            compact: TODO.

        Returns:
            TODO.

        """
        if compact:
            return ":".join(self.parts)
        return {"parts": list(self.parts), "options": dict(self.options)}


class HybridContainer:
    """Container exposing list-like and dict-like operations."""

    def __init__(self, *items: object, **named: object) -> None:
        """Initialize mixed storage.

        Args:
            items: TODO.
            named: TODO.

        """
        self.items: list[object] = list(items)
        self.named: dict[str, object] = dict(named)

    def __iter__(self) -> Iterator[object]:
        """Iterate over positional items.

        Returns:
            TODO.

        """
        return iter(self.items)

    def __contains__(self, item: object) -> bool:
        """Check both positional and named storage.

        Args:
            item: TODO.

        Returns:
            TODO.

        """
        return item in self.items or item in self.named

    def __getitem__(self, key: int | str) -> object:
        """Return item by int index or dict key.

        Args:
            key: TODO.

        Returns:
            TODO.

        """
        if isinstance(key, int):
            return self.items[key]
        return self.named[key]

    def __setitem__(self, key: int | str, value: object) -> None:
        """Set item by int index or dict key.

        Args:
            key: TODO.
            value: TODO.

        """
        if isinstance(key, int):
            self.items[key] = value
        else:
            self.named[key] = value

    def __or__(self, other: HybridContainer | Mapping[str, object]) -> Self:
        """Merge with another container or mapping.

        Args:
            other: TODO.

        Returns:
            TODO.

        """
        merged: Self = self.__class__(*self.items, **self.named)
        if isinstance(other, HybridContainer):
            merged.items.extend(other.items)
            merged.named.update(other.named)
        else:
            merged.named.update(other)
        return merged


class CallableObject:
    """Callable object with state-dependent returns."""

    def __init__(self, mode: str) -> None:
        """Store call mode.

        Args:
            mode: TODO.

        """
        self.mode: str = mode

    def __call__(self, value: object, *, scale: int = 1) -> object:
        """Return different types based on mode.

        Args:
            value: TODO.
            scale: TODO.

        Returns:
            TODO.

        """
        if self.mode == "number" and isinstance(value, int):
            return value * scale
        if self.mode == "text":
            return str(object=value) * scale
        return {"value": value, "scale": scale}


class AsyncResource:
    """Async resource with enter/exit methods."""

    def __init__(self, name: str) -> None:
        """Initialize resource.

        Args:
            name: TODO.

        """
        self.name: str = name
        self.events: list[str] = []

    async def __aenter__(self) -> Self:
        """Enter async context.

        Returns:
            TODO.

        """
        self.events.append("enter")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: object,
    ) -> bool:
        """Exit async context.

        Args:
            exc_type: TODO.
            exc: TODO.
            tb: TODO.

        Returns:
            TODO.

        """
        _ = (exc, tb)
        self.events.append("exit")
        return exc_type is None

    async def fetch(self, value: int) -> dict[str, object]:
        """Return async payload.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        await sleep(delay=0)
        return {"resource": self.name, "value": value}


@contextmanager
def extended_sync_context(seed: int) -> Generator[dict[str, object]]:
    """Yield a mutable context dictionary.

    Args:
        seed: TODO.

    Returns:
        TODO.

    """
    events: list[str] = []
    context: dict[str, object] = {"seed": seed, "events": events}
    events.append("enter")
    try:
        yield context
    finally:
        events.append("exit")


@asynccontextmanager
async def extended_async_context(seed: int) -> AsyncGenerator[AsyncResource]:
    """Yield an async resource and mutate its events.

    Args:
        seed: TODO.

    Returns:
        TODO.

    """
    resource: AsyncResource = AsyncResource(name=f"resource-{seed}")
    async with resource as opened:
        yield opened


def preserve_signature_decorator[**P, R](
    func: Callable[P, R],
) -> Callable[P, R | list[object]]:
    """Preserve arbitrary args and kwargs through a decorator.

    Args:
        func: TODO.

    Returns:
        TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | list[object]:
        """TODO.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        result: R | list[object] = func(*args, **kwargs)
        if isinstance(result, list):
            return cast(typ="list[object]", val=result)
        if isinstance(result, tuple):
            tuple_result: tuple[object, ...] = cast(
                typ="tuple[object, ...]",
                val=result,
            )
            return list(tuple_result)
        return result

    return wrapper


def decorator_factory[**P](
    prefix: str,
    *,
    uppercase: bool = False,
) -> Callable[[Callable[P, object]], Callable[P, str]]:
    """Create a decorator factory changing string outputs.

    Args:
        prefix: TODO.
        uppercase: TODO.

    Returns:
        TODO.

    """

    def decorate(func: Callable[P, object]) -> Callable[P, str]:
        """TODO.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
            """TODO.

            Args:
                args: TODO.
                kwargs: TODO.

            Returns:
                TODO.

            """
            result: object = func(*args, **kwargs)
            text: str = f"{prefix}:{result}"
            if uppercase:
                return text.upper()
            return text

        return wrapper

    return decorate


@preserve_signature_decorator
@decorator_factory(prefix="tag", uppercase=True)
def decorated_pipeline_value(value: str, suffix: str = "end") -> str:
    """Return decorated text.

    Args:
        value: TODO.
        suffix: TODO.

    Returns:
        TODO.

    """
    return f"{value}-{suffix}"


@singledispatch
def singledispatch_stress(value: object) -> object:
    """Return the default singledispatch branch.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    return {"type": type(value).__name__, "value": value}


@singledispatch_stress.register(int)
def _(value: int) -> int:
    """Integer branch.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    return value * 10


@singledispatch_stress.register(str)
def _(value: str) -> str:
    """Return the string branch.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    return value.upper()


@lru_cache(maxsize=16)
def cached_recursive_pair(n: int) -> tuple[int, int]:
    """Return Fibonacci-like pair with recursion and cache.

    Args:
        n: TODO.

    Returns:
        TODO.

    """
    if n <= 1:
        return (n, 1)
    left: tuple[int, int] = cached_recursive_pair(n=n - 1)
    right: tuple[int, int] = cached_recursive_pair(n=n - 2)
    return (left[0] + right[0], left[1] + right[1])


def function_with_pattern_matching_stress(
    value: PatternStressInput,
) -> PatternStressResult:
    """Exercise match/case inference across structural patterns.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    match value:
        case {"kind": "point", "x": int(x), "y": int(y)}:
            return (x, y)
        case {"kind": "line", "points": points} if isinstance(
            points,
            Sequence,
        ):
            line_points: list[object] = list(
                cast(typ="Sequence[object]", val=points),
            )
            return line_points
        case [name, count] if isinstance(name, str):
            return {name: count}
        case (left, right):
            return {"left": left, "right": right}
        case None:
            return Constants.extended_sentinel
        case _:
            return str(object=value)


class LocalExtendedError(Exception):
    """Local exception for inference."""


def raise_local_error() -> NoReturn:
    """Raise LocalExtendedError with message.

    Returns:
        TODO.

    Raises:
        LocalExtendedError: TODO.

    """
    msg: str = "local"
    raise LocalExtendedError(msg)


def raise_value_error() -> NoReturn:
    """Raise ValueError with message.

    Returns:
        TODO.

    Raises:
        ValueError: TODO.

    """
    msg: str = "bad value"
    raise ValueError(msg)


def raise_type_error() -> NoReturn:
    """Raise TypeError with message.

    Returns:
        TODO.

    Raises:
        TypeError: TODO.

    """
    msg: str = "bad type"
    raise TypeError(msg)


def function_with_chained_exceptions(mode: str) -> object:
    """Exercise exception value types and chained exceptions.

    Args:
        mode: TODO.

    Returns:
        TODO.

    Raises:
        RuntimeError: TODO.

    """
    try:
        if mode == "value":
            raise_value_error()
        if mode == "type":
            raise_type_error()
        if mode == "local":
            raise_local_error()
    except ValueError as error:
        return error.args[0]
    except TypeError as error:
        msg: str = "wrapped"
        raise RuntimeError(msg) from error
    except LocalExtendedError as error:
        return {"local": str(object=error)}
    else:
        return "ok"


def function_with_walrus_and_narrowing(
    records: Sequence[Mapping[str, object]],
) -> tuple[defaultdict[str, int], list[str]]:
    """Use walrus, truthiness, regex, and narrowing.

    Args:
        records: TODO.

    Returns:
        TODO.

    """
    totals: defaultdict[str, int] = defaultdict(int)
    matched: list[str] = []
    for record in records:
        if (raw_name := record.get("name")) and isinstance(raw_name, str):
            name: str = raw_name.strip().lower()
        else:
            name = "unknown"
        if (raw_amount := record.get("amount")) is None:
            amount: int = 0
        elif isinstance(raw_amount, str):
            amount = int(raw_amount) if raw_amount.isnumeric() else 0
        elif isinstance(raw_amount, int):
            amount = raw_amount
        else:
            amount = 0
        totals[name] += amount
        if found := search(pattern=r"[a-z]+", string=name):
            matched.append(found.group(0))
    return totals, matched


def function_with_recursive_containers(seed: int) -> dict[str, object]:
    """Create recursive containers and aliased references.

    Args:
        seed: TODO.

    Returns:
        TODO.

    """
    root: dict[str, object] = {"seed": seed, "children": []}
    child: dict[str, object] = {"parent": root, "values": [seed]}
    children: list[dict[str, object]] = cast(
        typ="list[dict[str, object]]",
        val=root["children"],
    )
    children.append(child)
    alias: dict[str, object] = children[0]
    values: list[int] = cast(typ="list[int]", val=alias["values"])
    values.extend([seed + 1, seed + 2])
    return root


def function_with_numeric_tower(
    values: Sequence[int | float | str],
) -> tuple[int, float, float, list[int]]:
    """Mix int, float, string fallback, and math/operator functions.

    Args:
        values: TODO.

    Returns:
        TODO.

    """
    total: int = 0
    products: list[int] = []
    for index, value in enumerate(iterable=values):
        adjusted: int = index if isinstance(value, str) else int(value) + index
        total += adjusted
        products.append(mul(adjusted, 2))
    mean: float = total / len(values) if values else nan
    magnitude: float = abs(complex(real=mean, imag=total))
    return total, mean, magnitude, products


def function_with_type_reassignment_maze(
    flag: str,
    payload: object,
) -> object:
    """Stress linear reassignment across unrelated runtime shapes.

    Args:
        flag: TODO.
        payload: TODO.

    Returns:
        TODO.

    """
    if flag == "none":
        return None
    if flag == "int":
        return 1
    if flag == "list":
        value_list: list[object] = [payload]
        return [*value_list, "extra"]
    if flag == "dict":
        value_dict: dict[str, object] = {"payload": payload}
        return {**value_dict, "seen": True}
    if flag == "callable":

        def callback(item: object) -> tuple[object, object]:
            """TODO.

            Args:
                item: TODO.

            Returns:
                TODO.

            """
            return (item, payload)

        return callback(item="called")
    return str(object=payload)


def function_with_exception_group_stress(
    values: Sequence[int | None],
) -> tuple[list[object], list[str]]:
    """Exercise except* branches and collected errors.

    Args:
        values: TODO.

    Returns:
        TODO.

    """

    def raise_error_group(errors: list[Exception]) -> None:
        """TODO.

        Args:
            errors: TODO.

        Raises:
            ExceptionGroup: TODO.

        """
        msg: str = "extended"
        raise ExceptionGroup(msg, errors)

    errors: list[Exception] = []
    value_errors: list[object] = []
    type_errors: list[str] = []
    for value in values:
        if isinstance(value, int) and value < 0:
            errors.append(ValueError(value))
        elif value is None:
            msg: str = "missing"
            errors.append(TypeError(msg))
    try:
        if errors:
            raise_error_group(errors=errors)
    except* ValueError as group:
        value_errors = [error.args[0] for error in group.exceptions]
    except* TypeError as group:
        type_errors = [str(object=error) for error in group.exceptions]
    return value_errors, type_errors


def function_with_import_and_reflection_stress(
    module_name: str,
    attr_name: str,
) -> dict[str, object]:
    """Import module dynamically and inspect attributes.

    Args:
        module_name: TODO.
        attr_name: TODO.

    Returns:
        TODO.

    """
    module: ModuleType = import_module(name=module_name)
    attr: object = getattr(module, attr_name)
    attr_type: type[object] = type(attr)
    return {
        "module": module.__name__,
        "attr": attr,
        "attr_type": attr_type.__name__,
        "has_doc": bool(getattr(attr, "__doc__", None)),
    }


def function_with_json_uuid_and_path_stress(tmp_name: str) -> object:
    """Exercise JSON, UUID, Path, and text round-tripping.

    Args:
        tmp_name: TODO.

    Returns:
        TODO.

    """
    identifier: UUID = uuid5(namespace=NAMESPACE_DNS, name=tmp_name)
    path: Path = Path(gettempdir()) / f"{identifier}.json"
    payload: dict[str, object] = {
        "id": str(object=identifier),
        "parts": path.stem.split(sep="-"),
        "exists": path.exists(),
    }
    path.write_text(data=dumps(obj=payload), encoding="utf-8")
    loaded = loads(s=path.read_text(encoding="utf-8"))
    path.unlink(missing_ok=True)
    return loaded


def function_with_contextvars_and_chainmap(
    configs: Sequence[MutableMapping[str, object]],
) -> Mapping[str, object]:
    """Use ContextVar and ChainMap layered lookup.

    Args:
        configs: TODO.

    Returns:
        TODO.

    """
    token: Token[dict[str, object] | None] = Constants.extended_context.set(
        None,
    )
    try:
        current_map: dict[str, object] = {"seed": len(configs)}
        chain_map: ChainMap[str, object] = ChainMap(current_map, *configs)
        resolved: dict[str, object] = {
            key: chain_map[key] for key in chain_map
        }
    finally:
        Constants.extended_context.reset(token)
    return resolved


def function_with_iterable_unpacking_stress(
    data: Sequence[int],
) -> tuple[int, list[int], int, list[tuple[int, int]], list[tuple[int, int]]]:
    """Mix star-unpacking, zip, enumerate, and heterogeneous outputs.

    Args:
        data: TODO.

    Returns:
        TODO.

    """
    head, *middle, tail = data
    pairs: list[tuple[int, int]] = [
        (index, value) for index, value in enumerate(iterable=middle)
    ]
    zipped: list[tuple[int, int]] = list(zip([head], [tail], strict=False))
    return head, middle, tail, pairs, zipped


def function_with_generator_send_throw_close(
    limit: int,
) -> tuple[int, int, Generator[int, int | str | None, int]]:
    """Return a generator supporting send/throw/close interactions.

    Args:
        limit: TODO.

    Returns:
        TODO.

    """

    def controlled_generator() -> Generator[int, int | str | None, int]:
        """TODO.

        Returns:
            TODO.

        """
        current: int = 0
        while current < limit:
            received: int | str | None = yield current
            if received is None:
                current += 1
            elif received == "stop":
                return current
            elif isinstance(received, int):
                current += received
        return current

    generator: Generator[int, int | str | None, int] = controlled_generator()
    first: int = next(generator)
    second: int = generator.send(2)
    generator.close()
    return first, second, generator


def function_with_property_and_descriptor_interaction() -> tuple[
    dict[str, object],
    int,
    object,
]:
    """Use descriptor owner, cached property, deletion, and reset.

    Returns:
        TODO.

    """
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=10,
        label="alpha",
    )
    before: dict[str, object] = owner.summary
    current_score: int = cast(typ="int", val=owner.score)
    owner.score = current_score + 5
    del owner.label
    after_delete: object = owner.label
    return before, owner.score, after_delete


def function_with_metaclass_registry_stress() -> tuple[
    RegistryItem,
    object,
    list[str],
]:
    """Create registry instances and clone them.

    Returns:
        TODO.

    """
    item: RegistryItem = cast(
        typ="RegistryItem",
        val=RegistryItem(name="alpha", count=1, tags=["x"], extra=True),
    )
    clone: RegistryItem = cast(
        typ="RegistryItem",
        val=item.bump(amount=2).clone(name="beta"),
    )
    registry: dict[str, type[object]] = RegistryMeta.registry or {}
    registry_names: list[str] = sorted(registry)
    return item, clone, registry_names


def function_with_fluent_builder_stress() -> tuple[object, str]:
    """Use fluent builder and mixed finalization modes.

    Returns:
        TODO.

    """
    builder: FluentBuilder = FluentBuilder()
    structured: str | dict[str, object] = (
        builder.add(part="a")
        .add(part="b", repeat=2)
        .configure(debug=True)
        .build()
    )
    compact: str | dict[str, object] = builder.build(compact=True)
    return structured, cast(typ="str", val=compact)


def function_with_hybrid_container_stress() -> tuple[
    HybridContainer,
    bool,
    object,
]:
    """Stress custom container protocols and operator overloads.

    Returns:
        TODO.

    """
    left: HybridContainer = HybridContainer(1, 2, name="left")
    right: HybridContainer = HybridContainer(3, 4, name="right", enabled=True)
    merged: HybridContainer = left | right
    first: object = merged[0]
    merged[0] = (first if isinstance(first, int) else 0) + 10
    merged["extra"] = [value for value in merged if isinstance(value, int)]
    return merged, "name" in merged, merged["extra"]


def function_with_callable_object_stress() -> tuple[object, object, object]:
    """Call stateful callable objects with keyword-only args.

    Returns:
        TODO.

    """
    number_call: CallableObject = CallableObject(mode="number")
    text_call: CallableObject = CallableObject(mode="text")
    dict_call: CallableObject = CallableObject(mode="dict")
    return (
        number_call(value=4, scale=3),
        text_call(value="ha", scale=2),
        dict_call(value="payload", scale=5),
    )


async def function_with_async_comprehension_stress(
    values: Sequence[int],
) -> tuple[dict[str, object], list[int]]:
    """Use async context, async helper, and async comprehension.

    Args:
        values: TODO.

    Returns:
        TODO.

    """

    async def produce() -> AsyncIterator[int]:
        """TODO.

        Returns:
            TODO.

        """
        for value in values:
            await sleep(delay=0)
            yield value * 2

    async with extended_async_context(seed=len(values)) as resource:
        fetched: dict[str, object] = await resource.fetch(value=sum(values))
        doubled: list[int] = [value async for value in produce()]
    return fetched, doubled


class LocalMultiplierProtocol(Protocol):
    """Protocol for local multiplier instances.

    Attributes:
        offset: TODO.

    """

    offset: int

    def apply(self, value: int) -> int:
        """Apply multiplier.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        ...


class LocalMultiplierFactory(Protocol):
    """Protocol for local multiplier classes."""

    def __call__(self, offset: int = 0) -> LocalMultiplierProtocol:
        """Create a local multiplier.

        Args:
            offset: TODO.

        Returns:
            TODO.

        """
        ...

    def from_values(
        self,
        values: Sequence[int],
    ) -> LocalMultiplierProtocol:
        """Create from values.

        Args:
            values: TODO.

        Returns:
            TODO.

        """
        ...


def function_with_local_class_closure_stress(
    multiplier: int,
) -> LocalMultiplierFactory:
    """Return a local class capturing outer state.

    Args:
        multiplier: TODO.

    Returns:
        TODO.

    """

    class LocalMultiplier:
        """Local class closing over multiplier."""

        def __init__(self, offset: int = 0) -> None:
            """TODO.

            Args:
                offset: TODO.

            """
            self.offset: int = offset

        def apply(self, value: int) -> int:
            """TODO.

            Args:
                value: TODO.

            Returns:
                TODO.

            """
            return value * multiplier + self.offset

        @classmethod
        def from_values(cls, values: Sequence[int]) -> Self:
            """TODO.

            Args:
                values: TODO.

            Returns:
                TODO.

            """
            return cls(offset=sum(values))

    return LocalMultiplier


def function_with_nested_default_factories() -> tuple[
    defaultdict[str, defaultdict[str, list[int]]],
    dict[str, dict[str, tuple[int, ...]]],
]:
    """Build nested defaultdict structures.

    Returns:
        TODO.

    """
    tree: defaultdict[str, defaultdict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list),
    )
    for section, key, value in [
        ("a", "x", 1),
        ("a", "x", 2),
        ("a", "y", 3),
        ("b", "z", 4),
    ]:
        tree[section][key].append(value)
    frozen: dict[str, dict[str, tuple[int, ...]]] = {
        section: {key: tuple(values) for key, values in group.items()}
        for section, group in tree.items()
    }
    return tree, frozen


def function_with_sort_key_and_grouping_stress(
    rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, list[int]]]:
    """Sort/group by computed keys and return nested groups.

    Args:
        rows: TODO.

    Returns:
        TODO.

    """
    normalized: list[dict[str, object]] = [
        {
            "name": str(object=row["name"]).strip().lower(),
            "score": int(cast(typ="int | str", val=row["score"])),
        }
        for row in rows
    ]
    normalized.sort(
        key=lambda row: (
            cast(typ="str", val=row["name"]),
            -int(cast(typ="int | str", val=row["score"])),
        ),
    )
    grouped: dict[str, list[int]] = {
        name: [cast(typ="int", val=item["score"]) for item in group]
        for name, group in groupby(
            iterable=normalized,
            key=lambda row: cast(typ="str", val=row["name"]),
        )
    }
    return normalized, grouped


def function_with_partial_reduce_and_operator_stress(
    numbers: Sequence[int],
) -> tuple[list[int], int, int]:
    """Mix partial, reduce, and operator functions.

    Args:
        numbers: TODO.

    Returns:
        TODO.

    """
    add_five: Callable[[int], int] = partial(add, 5)
    transformed: list[int] = [add_five(number) for number in numbers]
    total: int = reduce(add, transformed, 0)
    product_value: int = reduce(mul, transformed, 1)
    return transformed, total, product_value


def function_with_protocol_like_runtime_checks(candidate: object) -> object:
    """Infer from hasattr/callable runtime protocol checks.

    Args:
        candidate: TODO.

    Returns:
        TODO.

    """
    update: Callable[..., str] | None = getattr(candidate, "update", None)
    if callable(update):
        update("message")
        return "updated"
    execute: Callable[..., tuple[int, int]] | None = getattr(
        candidate,
        "execute",
        None,
    )
    if callable(execute):
        return execute(2, 3)
    if callable(candidate):
        return candidate("value")
    return None


def function_with_deep_attribute_assignment() -> tuple[object, object, object]:
    """Assign attributes at several depths and return snapshots.

    Returns:
        TODO.

    """

    class Node:
        """TODO."""

        def __init__(self, name: str) -> None:
            """TODO.

            Args:
                name: TODO.

            """
            self.name: str = name
            self.children: list[Node] = []
            self.metadata: dict[str, object] = {}
            self.parent: Node | None = None

        def add(self, child: Node) -> Node:
            """TODO.

            Args:
                child: TODO.

            Returns:
                TODO.

            """
            self.children.append(child)
            child.parent = self
            return child

    root: Node = Node(name="root")
    child: Node = root.add(child=Node(name="child"))
    leaf: Node = child.add(child=Node(name="leaf"))
    leaf.metadata = {"depth": 2, "path": [root.name, child.name, leaf.name]}
    return root, child, leaf.metadata


def function_with_bytes_memoryview_and_slices(
    data: bytes,
) -> tuple[bytearray, memoryview, bytes, int]:
    """Exercise bytes, bytearray, memoryview, and slice inference.

    Args:
        data: TODO.

    Returns:
        TODO.

    """
    raw: bytearray = bytearray(data)
    raw.extend(b"!")
    view: memoryview[int] = memoryview(obj=raw)
    prefix: bytes = bytes(view[:2])
    ordinal_sum: int = sum(view)
    return raw, view, prefix, ordinal_sum


def function_with_map_filter_zip_stress(
    values: Sequence[int],
) -> list[tuple[int, int]]:
    """Use map/filter/zip pipelines with generator expressions.

    Args:
        values: TODO.

    Returns:
        TODO.

    """
    mapped: Generator[int] = (value * 2 for value in values)
    filtered: Generator[int] = (value for value in mapped if value % 3 != 0)
    paired: zip[tuple[int, int]] = zip(values, filtered, strict=False)
    return list(paired)


def function_with_composed_inner_functions(seed: int) -> dict[str, int]:
    """Compose inner functions where each narrows a value.

    Args:
        seed: TODO.

    Returns:
        TODO.

    """

    def normalize(value: object) -> str:
        """TODO.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, bytes):
            return value.decode().strip().lower()
        return str(object=value)

    def tokenize(value: object) -> list[str]:
        """TODO.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        return [
            part
            for part in split(pattern=r"\W+", string=normalize(value=value))
            if part
        ]

    def score(tokens: Sequence[str]) -> dict[str, int]:
        """TODO.

        Args:
            tokens: TODO.

        Returns:
            TODO.

        """
        return {
            token: index + seed for index, token in enumerate(iterable=tokens)
        }

    return score(tokens=tokenize(value="Alpha beta alpha"))


def function_with_mutable_default_like_pattern(
    value: object,
    store: list[object] | None = None,
) -> tuple[list[object], tuple[object, ...], set[object]]:
    """Avoid mutable defaults while preserving accumulator type.

    Args:
        value: TODO.
        store: TODO.

    Returns:
        TODO.

    """
    if store is None:
        store = []
    store.append(value)
    return store, tuple(store), set(store)


def function_with_literal_mode_dispatch(mode: str, value: object) -> object:
    """Dispatch by string literal-like mode.

    Args:
        mode: TODO.
        value: TODO.

    Returns:
        TODO.

    """
    if mode == "int":
        return int(cast(typ="str | bytes | int | float", val=value))
    if mode == "str":
        return str(object=value)
    if mode == "repr":
        return repr(value)
    if mode == "json":
        return dumps(obj=value)
    return value


def function_with_complex_boolean_narrowing(
    value: object,
    fallback: object | None = None,
) -> object:
    """Exercise bool-op narrowing with dict/list/tuple/string paths.

    Args:
        value: TODO.
        fallback: TODO.

    Returns:
        TODO.

    """
    if isinstance(value, dict):
        if "result" in value:
            return cast(typ="object", val=value["result"])
        return fallback
    if isinstance(value, (list, tuple)) and value:
        return cast(typ="object", val=value[0])
    if isinstance(value, str) and value.strip():
        return cast(typ="object", val=value.strip().upper())
    return fallback


def function_with_extended_named_results() -> ExtendedResultTuple:
    """Return custom result objects and tuple-unpacking behavior.

    Returns:
        TODO.

    """
    result: ExtendedResult = ExtendedResult(
        name="alpha",
        payload=[1, 2, 3],
        metadata={"ok": True},
    )
    name_obj, payload_obj, metadata_obj = result
    name: str = cast(typ="str", val=name_obj)
    payload: list[int] = cast(typ="list[int]", val=payload_obj)
    metadata: dict[str, bool] = cast(typ="dict[str, bool]", val=metadata_obj)
    return result, name, payload[-1], metadata["ok"]


def test_extended_inference_edge_cases_part1() -> ExtendedTestResult:
    """Run extended stress cases part 1.

    Returns:
        TODO.

    """
    records: list[dict[str, object]] = [
        {"name": " Alpha ", "amount": "10"},
        {"name": "beta", "amount": 5},
        {"name": None, "amount": None},
    ]
    return {
        "pattern_point": function_with_pattern_matching_stress(
            value={"kind": "point", "x": 1, "y": 2},
        ),
        "pattern_line": function_with_pattern_matching_stress(
            value={"kind": "line", "points": [1, 2, 3]},
        ),
        "walrus": function_with_walrus_and_narrowing(records=records),
        "recursive": function_with_recursive_containers(seed=5),
        "numeric": function_with_numeric_tower(values=[1, 2.5, 3]),
        "reassignment_int": function_with_type_reassignment_maze(
            flag="int",
            payload=10,
        ),
        "reassignment_callable": function_with_type_reassignment_maze(
            flag="callable",
            payload="x",
        ),
        "exceptions": function_with_chained_exceptions(mode="value"),
        "exception_group": function_with_exception_group_stress(
            values=[-1, None, 2],
        ),
        "reflection": function_with_import_and_reflection_stress(
            module_name="pathlib",
            attr_name="Path",
        ),
    }


def test_extended_inference_edge_cases_part2() -> ExtendedTestResult:
    """Run extended stress cases part 2.

    Returns:
        TODO.

    """
    rows: list[dict[str, object]] = [
        {"name": " Alpha", "score": "10"},
        {"name": "alpha", "score": 7},
        {"name": "Beta", "score": 3},
    ]
    return {
        "json_uuid_path": function_with_json_uuid_and_path_stress(
            tmp_name="demo",
        ),
        "contextvars": function_with_contextvars_and_chainmap(
            configs=[{"fallback": 2}, {"seed": 99, "other": 3}],
        ),
        "unpacking": function_with_iterable_unpacking_stress(
            data=[1, 2, 3, 4],
        ),
        "generator_control": function_with_generator_send_throw_close(
            limit=10,
        ),
        "descriptor": function_with_property_and_descriptor_interaction(),
        "metaclass_registry": function_with_metaclass_registry_stress(),
        "builder": function_with_fluent_builder_stress(),
        "container": function_with_hybrid_container_stress(),
        "callable_object": function_with_callable_object_stress(),
        "grouping": function_with_sort_key_and_grouping_stress(rows=rows),
    }


def test_extended_inference_edge_cases_part3() -> ExtendedTestResult:
    """Run extended stress cases part 3.

    Returns:
        TODO.

    """
    local_multiplier: LocalMultiplierFactory = (
        function_with_local_class_closure_stress(multiplier=10)
    )
    local_instance: LocalMultiplierProtocol = local_multiplier.from_values(
        values=[1, 2, 3],
    )
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=3,
        label="candidate",
    )
    async_result: tuple[dict[str, object], list[int]] = run(
        main=function_with_async_comprehension_stress(values=[1, 2, 3]),
    )
    return {
        "local_class": local_instance.apply(value=5),
        "nested_defaultdict": function_with_nested_default_factories(),
        "partial_reduce": function_with_partial_reduce_and_operator_stress(
            numbers=[1, 2, 3],
        ),
        "runtime_protocol_update": function_with_protocol_like_runtime_checks(
            candidate=owner,
        ),
        "runtime_protocol_callable": (
            function_with_protocol_like_runtime_checks(
                candidate=CallableObject(mode="text"),
            )
        ),
        "deep_attributes": function_with_deep_attribute_assignment(),
        "bytes_memoryview": function_with_bytes_memoryview_and_slices(
            data=b"abc",
        ),
        "map_filter_zip": function_with_map_filter_zip_stress(
            values=[1, 2, 3, 4],
        ),
        "composed_inner": function_with_composed_inner_functions(seed=100),
        "mutable_store": function_with_mutable_default_like_pattern(value="x"),
        "literal_dispatch": function_with_literal_mode_dispatch(
            mode="json",
            value={"a": 1},
        ),
        "boolean_narrowing": function_with_complex_boolean_narrowing(
            value={"result": 42},
        ),
        "extended_result": function_with_extended_named_results(),
        "decorated_pipeline": decorated_pipeline_value(value="start"),
        "singledispatch_int": singledispatch_stress(value=3),
        "singledispatch_str": singledispatch_stress(value="hello"),
        "singledispatch_default": singledispatch_stress(value=[1, 2]),
        "cached_recursive": cached_recursive_pair(n=6),
        "async_result": async_result,
    }


def test_extended_inference_edge_cases() -> ExtendedTestResult:
    """Run all extended inference stress cases.

    Returns:
        TODO.

    """
    return {
        **test_extended_inference_edge_cases_part1(),
        **test_extended_inference_edge_cases_part2(),
        **test_extended_inference_edge_cases_part3(),
    }


def main() -> None:
    """Test main function."""
    _ = test_function_calls()
    _ = test_class_instantiations()
    _ = test_other_operations()
    _ = test_new_inference_edge_cases()
    _ = test_extended_inference_edge_cases()


if __name__ == "__main__":
    main()
