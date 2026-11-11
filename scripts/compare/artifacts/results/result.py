"""Untyped test file for resolver inference with merged edge cases.

This companion intentionally removes type hints and keyword-style calls from
the typed corpus while preserving the same runtime scenarios.

"""

from __future__ import annotations

import asyncio
import importlib
import json
import math
import operator
import re
import tempfile
import uuid
from abc import ABC, abstractmethod
from collections import ChainMap, Counter, OrderedDict, defaultdict, deque
from collections.abc import Mapping, Generator, Callable, Sequence, Awaitable
from contextlib import asynccontextmanager, contextmanager, suppress
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum, auto
from functools import (
    cached_property,
    lru_cache,
    partial,
    reduce,
    singledispatch,
    wraps,
)
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
from pathlib import Path
from typing import Never, Final, Self
from weakref import WeakKeyDictionary, ref
from uuid import UUID

type DictInt = dict[str, int]

THRESHOLD: Final[int] = 5
MAX_VALUE: Final[int] = 10
MIN_LENGTH: Final[int] = 3


class SupportsUpdate:
    """Protocol for observer-like objects."""

    def update(self, message) -> None:
        """Receive an update message.

        Args:
            message: TODO.

        """


class SupportsExecuteInt:
    """Protocol for integer strategies."""

    def execute(self, a, b) -> None:
        """Execute with two integer inputs.

        Args:
            a: TODO.
            b: TODO.

        """


class SupportsAction:
    """Protocol for receiver objects."""

    def action(self) -> None:
        """Perform the action."""


class SupportsInitializedByMeta:
    """Protocol for objects initialized by metaclass."""

    initialized_by_meta = None


class SupportsNewMethod:
    """Protocol for objects with new_method."""

    def new_method(self) -> None:
        """Return new method for testing."""


class SupportsVector:
    """Protocol for vector-like objects."""

    x = None
    y = None

    def __add__(self, other: int):
        """Add vectors.

        Args:
            other (int): TODO.

        """


class MetaClass(type):
    """Metaclass for testing type inference."""

    def __new__(mcs, name: str, bases, namespace, **_kwargs):
        """Create a new class with ``meta_added``.

        Args:
            mcs: TODO.
            name (str): TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.

        """
        namespace["meta_added"] = True
        return super().__new__(mcs, name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        """Create instance with ``initialized_by_meta``.

        Args:
            args: TODO.
            kwargs: TODO.

        Returns:
            TODO.

        """
        instance = super().__call__(*args, **kwargs)
        initialized = instance
        initialized.initialized_by_meta = True
        return initialized


class AbstractBase(ABC):
    """Abstract base class for testing type inference."""

    @abstractmethod
    def abstract_method(self, value: int) -> int:
        """Abstract method for testing.

        Args:
            value (int): TODO.

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
            x (int): TODO.
            y (int | None): TODO.

        """
        self.x = x
        self.y = y

    def base_method(self, a: int, b: int = 10) -> int:
        """Test base method.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a + b

    @property
    def base_property(self):
        """Base property getter.

        Returns:
            TODO.

        """
        return self.x

    @base_property.setter
    def base_property(self, value) -> None:
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
            x (int): TODO.
            y (int | None): TODO.
            z (int): TODO.

        """
        super().__init__(x=x, y=y)
        self.z = z

    def abstract_method(self, value: int) -> int:
        """Implement abstract method.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

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
            a (int): TODO.
            b (int): TODO.
            c (int): TODO.
            d (int): TODO.

        Returns:
            int: TODO.

        """
        if a > b:
            return a - b
        if a < b:
            return b - a
        return c + d


class MetaDecoratedClass:
    """Class with metaclass for testing."""

    def __init__(self, value) -> None:
        """Initialize meta decorated class.

        Args:
            value: TODO.

        """
        self.value = value


def decorator(func):
    """Multiply result by 2.

    Args:
        func: TODO.

    Returns:
        TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args, **kwargs) -> int:
        result = func(*args, **kwargs)
        return result * 2

    return wrapper


def decorator_with_args(multiplier: int = 2):
    """Create decorator with configurable multiplier.

    Args:
        multiplier (int): TODO.

    Returns:
        TODO.

    """

    def actual_decorator(func):
        @wraps(wrapped=func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            return result * multiplier

        return wrapper

    return actual_decorator


def decorator_with_class(cls):
    """Wrap class in a proxy class.

    Returns:
        TODO.

    """

    class Wrapper:
        """Proxy wrapper created by a class decorator."""

        def __init__(self, *args, **kwargs) -> None:
            self.instance = cls(*args, **kwargs)

        def __getattr__(self, name: str):
            return getattr(self.instance, name)

    return Wrapper


@decorator
def simple_function(x: int) -> int:
    """Test simple function.

    Args:
        x (int): TODO.

    Returns:
        int: TODO.

    """
    return x + 1


@decorator_with_args(multiplier=3)
def function_with_args(x: int, y: int = 5) -> int:
    """Test function with args.

    Args:
        x (int): TODO.
        y (int): TODO.

    Returns:
        int: TODO.

    """
    return x + y


@decorator_with_class
class DecoratedClass:
    """Class decorated with class decorator."""

    def __init__(self, value: int) -> None:
        """Initialize decorated class.

        Args:
            value (int): TODO.

        """
        self.value = value

    def method(self) -> int:
        """Test method.

        Returns:
            int: TODO.

        """
        return self.value


@dataclass(init=False)
class DataClassExample:
    """Dataclass-like class for testing type inference."""

    x = None
    y = "default"
    z = None

    def __init__(self, x, y: str = "default", z=None) -> None:
        """Initialize dataclass-like example.

        Args:
            x: TODO.
            y (str): TODO.
            z: TODO.

        """
        self.x = x
        self.y = y
        self.z = [] if z is None else z


class EnumClass(Enum):
    """Enum class for testing type inference."""

    VALUE_A = auto()
    VALUE_B = auto()
    VALUE_C = auto()


def function_without_hints(
    a: int, b: int, c: int | None = None, d: int = 10, e: int = 20
) -> int:
    """Test function without missing type hints.

    Args:
        a (int): TODO.
        b (int): TODO.
        c (int | None): TODO.
        d (int): TODO.
        e (int): TODO.

    Returns:
        int: TODO.

    """
    resolved_c: int = a + b if c is None else c
    return resolved_c + d + e


def function_with_kwargs(a: int, b: int = 5, *args: int, **kwargs: int) -> int:
    """Test function with kwargs.

    Args:
        a (int): TODO.
        b (int): TODO.
        args (int): TODO.
        kwargs (int): TODO.

    Returns:
        int: TODO.

    """
    result: int = a + b
    for value in args:
        result += value
    for value in kwargs.values():
        result += value
    return result


def function_with_args_kwargs(*args: int, **kwargs: int) -> int:
    """Test function with args and kwargs.

    Args:
        args (int): TODO.
        kwargs (int): TODO.

    Returns:
        int: TODO.

    """
    total: int = sum(args)
    for value in kwargs.values():
        total += value
    return total


def nested_function(x: int, y: int, z: int) -> int:
    """Test nested function.

    Args:
        x (int): TODO.
        y (int): TODO.
        z (int): TODO.

    Returns:
        int: TODO.

    """

    def inner(a: int, b: int) -> int:
        """Inner function for testing.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """

        def deeper(c: int, d: int) -> int:
            """Deeper function for testing.

            Args:
                c (int): TODO.
                d (int): TODO.

            Returns:
                int: TODO.

            """
            return c * d

        return deeper(c=a, d=b) + a

    return inner(a=x, b=y) + z


def closure_function(x: int) -> Callable[[int], int]:
    """Test closure function.

    Args:
        x (int): TODO.

    Returns:
        Callable[[int], int]: TODO.

    """

    def inner(y: int) -> int:
        """Inner closure for testing.

        Args:
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x + y

    return inner


def function_with_slices(
    data: list[int], start: int, end: int, step: int | None = None
) -> list[int]:
    """Test function with slices.

    Args:
        data (list[int]): TODO.
        start (int): TODO.
        end (int): TODO.
        step (int | None): TODO.

    Returns:
        list[int]: TODO.

    """
    if step is None:
        return data[start:end]
    return data[start:end:step]


def function_with_comprehensions(
    items: list[int],
) -> tuple[list[int], dict[int, int], Generator[int]]:
    """Test function with comprehensions.

    Args:
        items (list[int]): TODO.

    Returns:
        tuple[list[int], dict[int, int], Generator[int]]: TODO.

    """
    squared: list[int] = [x**2 for x in items if x > 0]
    filtered: dict[int, int] = {
        k: v for k, v in enumerate(iterable=items) if v % 2 == 0
    }
    generator: Generator[int] = (x * 3 for x in items if x < MAX_VALUE)
    return (squared, filtered, generator)


def function_with_lambdas(
    items: list[str],
) -> tuple[list[str], list[str], list[str]]:
    """Test function with lambdas.

    Args:
        items (list[str]): TODO.

    Returns:
        tuple[list[str], list[str], list[str]]: TODO.

    """
    sorted_items: list[str] = sorted(items, key=lambda x: x.lower())
    mapped: list[str] = [x.upper() for x in items]
    filtered: list[str] = [x for x in items if len(x) > MIN_LENGTH]
    return (sorted_items, mapped, filtered)


def function_with_recursion(n) -> int:
    """Test function with recursion.

    Args:
        n: TODO.

    Returns:
        int: TODO.

    """
    if n <= 1:
        return 1
    return n * function_with_recursion(n=n - 1)


def function_with_try_except(value: str) -> int:
    """Test function with try except.

    Args:
        value (str): TODO.

    Returns:
        int: TODO.

    """
    try:
        result: int = int(value)
    except ValueError:
        result: int = 0
    except TypeError:
        result: int = -1
    else:
        result *= 2
    finally:
        pass
    return result


def function_with_context() -> bool:
    """Test function with context.

    Returns:
        bool: TODO.

    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        _ = f.write("test")
        temp_path: str = f.name
    Path(temp_path).unlink()
    return True


@contextmanager
def custom_context() -> Generator[str, None, None]:
    """Create custom context manager.

    Yields:
        str: TODO.

    """
    resource: str = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource=resource)


def acquire_resource() -> str:
    """Acquire resource.

    Returns:
        str: TODO.

    """
    return "resource"


def release_resource(resource: str) -> None:
    """Release resource.

    Args:
        resource (str): TODO.

    """
    resource = resource * 3


def function_with_generators():
    """Test function with generators.

    Returns:
        TODO.

    """

    def generator() -> Generator[int, None, None]:
        """Generate values.

        Yields:
            int: TODO.

        """
        yield from range(10)

    return list(generator())


def function_with_coroutines() -> Callable[[int], Awaitable[int]]:
    """Test function with coroutines.

    Returns:
        Callable[[int], Awaitable[int]]: TODO.

    """

    async def async_function(x: int) -> int:
        """Test async function.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        await asyncio.sleep(delay=1)
        return x * 2

    return async_function


def function_with_class_methods():
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
                str: TODO.

            """
            return cls.__name__

        @staticmethod
        def static_method() -> str:
            """Implement static method.

            Returns:
                str: TODO.

            """
            return "static"

        def instance_method(self) -> str:
            """Test instance method.

            Returns:
                str: TODO.

            """
            return "instance"

    return InnerClass


def function_with_property():
    """Test function with property.

    Returns:
        TODO.

    """

    class PropertyClass:
        """Test property class."""

        def __init__(self) -> None:
            """Initialize property class."""
            self._value = 0

        @property
        def value(self):
            """Get value property.

            Returns:
                TODO.

            """
            return self._value

        @value.setter
        def value(self, val) -> None:
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


def function_with_descriptor():
    """Test function with descriptor.

    Returns:
        TODO.

    """

    class Descriptor:
        """Test descriptor class."""

        def __init__(self) -> None:
            self._value = 0

        def __get__(self, obj, objtype) -> int:
            """Get descriptor value.

            Args:
                obj: TODO.
                objtype: TODO.

            Returns:
                int: TODO.

            """
            _ = (obj, objtype)
            return self._value

        def __set__(self, obj, value: int) -> None:
            """Set descriptor value.

            Args:
                obj: TODO.
                value (int): TODO.

            """
            _ = obj
            self._value = value

        def __delete__(self, obj) -> None:
            """Delete descriptor value.

            Args:
                obj: TODO.

            """
            _ = obj
            del self._value

    return Descriptor


def function_with_operator_overloading():
    """Test function with operator overloading.

    Returns:
        TODO.

    """

    class Vector:
        """Test vector class."""

        def __init__(self, x: int, y: int) -> None:
            """Initialize vector.

            Args:
                x (int): TODO.
                y (int): TODO.

            """
            self.x = x
            self.y = y

        def __add__(self, other: Vector) -> Vector:
            """Add vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x + other.x, y=self.y + other.y)

        def __sub__(self, other: Vector) -> Vector:
            """Subtract vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x - other.x, y=self.y - other.y)

        def __mul__(self, scalar: int) -> Vector:
            """Multiply vector by scalar.

            Args:
                scalar (int): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x * scalar, y=self.y * scalar)

        def __eq__(self, other) -> bool:
            """Check vector equality.

            Args:
                other: TODO.

            Returns:
                bool: TODO.

            """
            if not isinstance(other, Vector):
                return False
            return self.x == other.x and self.y == other.y

        def __hash__(self) -> int:
            """Return hash of vector.

            Returns:
                int: TODO.

            """
            return hash((self.x, self.y))

        def __lt__(self, other: Vector) -> bool:
            """Check if vector is less than other.

            Args:
                other (Vector): TODO.

            Returns:
                bool: TODO.

            """
            return self.x < other.x

        def __repr__(self) -> str:
            """Return vector representation.

            Returns:
                str: TODO.

            """
            return f"Vector({self.x}, {self.y})"

    return Vector


def function_with_metaclass_usage():
    """Test function with metaclass usage.

    Returns:
        TODO.

    """

    class MetaInstance:
        """Test meta instance class."""

    return MetaInstance()


def function_with_multiple_inheritance():
    """Test function with multiple inheritance.

    Returns:
        TODO.

    """

    class MixinA:
        """Test mixin A class."""

        def method_a(self) -> str:
            """Test method A.

            Returns:
                str: TODO.

            """
            return "A"

    class MixinB:
        """Test mixin B class."""

        def method_b(self) -> str:
            """Test method B.

            Returns:
                str: TODO.

            """
            return "B"

    class Combined(MixinA, MixinB):
        """Test combined class."""

        def combined_method(self) -> str:
            """Test combined method.

            Returns:
                str: TODO.

            """
            return self.method_a() + self.method_b()

    return Combined


def function_with_abstract_methods() -> type[AbstractBase]:
    """Test function with abstract methods.

    Returns:
        type[AbstractBase]: TODO.

    """

    class AbstractImplementation(AbstractBase):
        """Test abstract implementation class."""

        def abstract_method(self, value: int) -> int:
            """Test abstract method.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.

            """
            return value + 10

        @classmethod
        def class_method(cls) -> None:
            """Implement class method."""

        @staticmethod
        def static_method() -> None:
            """Implement static method."""

    return AbstractImplementation


def function_with_protocol():
    """Test function with protocol.

    Returns:
        TODO.

    """

    class ProtocolImplementation:
        """Test protocol implementation class."""

        def protocol_method(self, x: int) -> int:
            """Test protocol method.

            Args:
                x (int): TODO.

            Returns:
                int: TODO.

            """
            return x * 2

    return ProtocolImplementation


def function_with_generic_types() -> tuple[int, int, str]:
    """Test function with generic types.

    Returns:
        tuple[int, int, str]: TODO.

    """

    def generic_function(container: str | DictInt | list[int]) -> int | str:
        """Test generic function.

        Args:
            container (str | DictInt | list[int]): TODO.

        Returns:
            int | str: TODO.

        """
        if isinstance(container, Mapping):
            return next(iter(container.values()))
        return container[0]

    result1: int | str = generic_function(container=[1, 2, 3])
    result2: int | str = generic_function(container={"a": 1, "b": 2})
    result3: int | str = generic_function(container="hello")
    return (int(result1), int(result2), str(object=result3))


def function_with_union_types():
    """Test function with union types.

    Returns:
        TODO.

    """

    def union_function(value) -> int | str:
        """Test union function.

        Args:
            value: TODO.

        Returns:
            int | str: TODO.

        """
        if isinstance(value, int):
            return value * 2
        if isinstance(value, str):
            return value.upper()
        return str(object=value)

    return union_function


def function_with_optional_types() -> Callable[[None | int], int | str]:
    """Test function with optional types.

    Returns:
        Callable[[None | int], int | str]: TODO.

    """

    def optional_function(value: int | None = None) -> int | str:
        """Test optional function.

        Args:
            value (int | None): TODO.

        Returns:
            int | str: TODO.

        """
        if value is None:
            return "default"
        return value

    return optional_function


def function_with_callable():
    """Test function with callable.

    Returns:
        TODO.

    """

    def callable_function(func: Callable[..., object], arg):
        """Test callable function.

        Args:
            func (Callable[..., object]): TODO.
            arg: TODO.

        Returns:
            TODO.

        """
        return func(arg)

    return callable_function


def function_with_tuple_unpacking() -> tuple[int, int, int, int, int]:
    """Test function with tuple unpacking.

    Returns:
        tuple[int, int, int, int, int]: TODO.

    """
    data: tuple[int, int, int, int, int] = (1, 2, 3, 4, 5)
    a, b, *rest = data
    c, d, e = rest
    return (a, b, c, d, e)


def function_with_dict_operations() -> tuple[DictInt, DictInt]:
    """Test function with dict operations.

    Returns:
        tuple[DictInt, DictInt]: TODO.

    """
    d1: DictInt = {"a": 1, "b": 2}
    d2: DictInt = {"c": 3, "d": 4}
    merged: DictInt = {**d1, **d2}
    filtered: DictInt = {k: v for k, v in merged.items() if v > 1}
    return (merged, filtered)


def function_with_set_operations() -> tuple[set[int], set[int], set[int]]:
    """Test function with set operations.

    Returns:
        tuple[set[int], set[int], set[int]]: TODO.

    """
    s1: set[int] = {1, 2, 3, 4}
    s2: set[int] = {3, 4, 5, 6}
    union: set[int] = s1 | s2
    intersection: set[int] = s1 & s2
    difference: set[int] = s1 - s2
    return (union, intersection, difference)


def function_with_bitwise_operations() -> tuple[int, int, int, int, int, int]:
    """Test function with bitwise operations.

    Returns:
        tuple[int, int, int, int, int, int]: TODO.

    """
    a: int = 10
    b: int = 12
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
        int: TODO.

    """
    x: int = 10
    x += 5
    x -= 3
    x *= 2
    x: int = int(x / 4)
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
        tuple[int, int]: TODO.

    """
    x: int = 10
    y: int = 20
    max_val: int = max(y, x)
    min_val: int = min(y, x)
    return (max_val, min_val)


def function_with_chained_comparisons() -> tuple[bool, bool, bool]:
    """Test function with chained comparisons.

    Returns:
        tuple[bool, bool, bool]: TODO.

    """
    x = THRESHOLD
    result1: bool = 1 < x < MAX_VALUE
    result2: bool = MAX_VALUE > x > 0
    result3: bool = x == THRESHOLD or x != MAX_VALUE
    return (result1, result2, result3)


def function_with_boolean_logic() -> tuple[bool, bool, bool, bool, bool]:
    """Test function with boolean logic.

    Returns:
        tuple[bool, bool, bool, bool, bool]: TODO.

    """
    a: bool = True
    b: bool = False
    c: bool = True
    result1: bool = a and b
    result2: bool = a or b
    result3: bool = not a
    result4: bool = a and b or c
    result5: bool = (a or b) and c
    return (result1, result2, result3, result4, result5)


def function_with_none_handling() -> tuple[int | None, int | None]:
    """Test function with none handling.

    Returns:
        tuple[int | None, int | None]: TODO.

    """

    def maybe_none(value: int | None) -> int | None:
        """Maybe none function for testing.

        Args:
            value (int | None): TODO.

        Returns:
            int | None: TODO.

        """
        if value is None:
            return None
        return value * 2

    result1: int | None = maybe_none(value=5)
    result2: int | None = maybe_none(value=None)
    return (result1, result2)


def function_with_ellipsis() -> Callable[[int, int], int]:
    """Test function with ellipsis.

    Returns:
        Callable[[int, int], int]: TODO.

    """

    def ellipsis_function(a: int, b: int) -> int:
        """Ellipsis function for testing.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a + b

    return ellipsis_function


def function_with_star_expressions() -> list[int]:
    """Test function with star expressions.

    Returns:
        list[int]: TODO.

    """
    data: list[int] = [1, 2, 3]
    return [*data, 4, 5]


def function_with_double_star_expressions() -> DictInt:
    """Test function with double star expressions.

    Returns:
        DictInt: TODO.

    """
    d1: DictInt = {"a": 1}
    d2: DictInt = {"b": 2}
    return {**d1, **d2, "c": 3}


def function_with_matrix_multiplication():
    """Test function with matrix multiplication.

    Returns:
        TODO.

    """

    class Matrix:
        """Test matrix class."""

        def __init__(self, data: list[list[int]]) -> None:
            """Initialize matrix with data.

            Args:
                data (list[list[int]]): TODO.

            """
            self.data = data

        def __matmul__(self, other: Matrix) -> Matrix:
            """Matrix multiplication operator.

            Args:
                other (Matrix): TODO.

            Returns:
                Matrix: TODO.

            """
            return Matrix(
                data=[
                    [
                        sum(
                            (a * b for a, b in zip(row, col, strict=False)),
                        )
                        for col in zip(*other.data, strict=False)
                    ]
                    for row in self.data
                ],
            )

    return Matrix


def function_with_async_await() -> Callable[[], Awaitable[int]]:
    """Test function with async await.

    Returns:
        Callable[[], Awaitable[int]]: TODO.

    """

    async def async_func() -> int:
        """Async function for testing.

        Returns:
            int: TODO.

        """
        await asyncio.sleep(delay=0.1)
        return 42

    return async_func


def function_with_type_annotations_missing() -> tuple[
    Callable[[int], int],
    Callable[[int, int], int],
    Callable[[int, int], int],
    Callable[[], int],
    Callable[[], int],
    Callable[[], int],
]:
    """Test formerly missing type annotations.

    Returns:
        tuple[
                Callable[[int], int],
                Callable[[int, int], int],
                Callable[[int, int], int],
                Callable[[], int],
                Callable[[], int],
                Callable[[], int]
            ]: TODO.

    """

    def func1(x: int) -> int:
        """Func1 for testing.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        return x + 1

    def func2(x: int, y: int) -> int:
        """Func2 for testing.

        Args:
            x (int): TODO.
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x + y

    def func3(x: int, y: int = 10) -> int:
        """Func3 for testing.

        Args:
            x (int): TODO.
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x * y

    def func4(*args: int) -> int:
        """Func4 for testing.

        Args:
            args (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(args)

    def func5(**kwargs: int) -> int:
        """Func5 for testing.

        Args:
            kwargs (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(kwargs.values())

    def func6(*args: int, **kwargs: int) -> int:
        """Func6 for testing.

        Args:
            args (int): TODO.
            kwargs (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(args) + sum(kwargs.values())

    return (func1, func2, func3, func4, func5, func6)


def function_with_complex_conditionals() -> Callable[[int, int, int], int]:
    """Test function with complex conditionals.

    Returns:
        Callable[[int, int, int], int]: TODO.

    """

    def complex_func(x: int, y: int, z: int) -> int:
        """Complex function for testing.

        Args:
            x (int): TODO.
            y (int): TODO.
            z (int): TODO.

        Returns:
            int: TODO.

        """
        x_sign: int = 1 if x > 0 else -1
        y_sign: int = 1 if y > 0 else -1
        z_sign: int = 1 if z > 0 else -1
        return x_sign * x + y_sign * y + z_sign * z

    return complex_func


def function_with_nested_loops() -> Callable[
    [Sequence[Sequence[int]]], list[int]
]:
    """Test function with nested loops.

    Returns:
        Callable[[Sequence[Sequence[int]]], list[int]]: TODO.

    """

    def nested_loop_func(matrix: Sequence[Sequence[int]]) -> list[int]:
        """Nested loop function for testing.

        Args:
            matrix (Sequence[Sequence[int]]): TODO.

        Returns:
            list[int]: TODO.

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
        Callable[[], None]: TODO.

    """

    def exception_chain_func() -> None:
        """Exception chain function for testing."""

        def raise_first_error() -> Never:
            first_error: str = "First error"
            raise ValueError(first_error)

        def raise_second_error(original_error) -> Never:
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
        Callable[[], None]: TODO.

    """

    class CustomError(Exception):
        """Custom error for testing."""

    class AnotherCustomError(CustomError):
        """Another custom error for testing."""

    def raise_custom() -> Never:
        """Raise custom function for testing.

        Raises:
            AnotherCustomError: TODO.

        """
        error_message: str = "Custom error occurred"
        raise AnotherCustomError(error_message)

    return raise_custom


def function_with_weak_refs():
    """Test function with weak refs.

    Returns:
        TODO.

    """

    class RefClass:
        """Ref class for testing."""

    obj: RefClass = RefClass()
    return ref(obj)


def function_with_slots():
    """Test function with slots.

    Returns:
        TODO.

    """

    class SlottedClass:
        """Slotted class for testing."""

        __slots__ = ("x", "y")

        def __init__(self, x, y) -> None:
            self.x = x
            self.y = y

    return SlottedClass


def function_with_class_decorator():
    """Test function with class decorator.

    Returns:
        TODO.

    """

    def add_method(cls):
        """Add method for testing.

        Returns:
            TODO.

        """

        def new_method(self) -> str:
            """Add new method.

            Returns:
                str: TODO.

            """
            _ = self
            return "added method"

        dynamic_cls = cls
        dynamic_cls.new_method = new_method
        return cls

    @add_method
    class DecoratedByClass:
        """Test decorated by class."""

    return DecoratedByClass


def function_with_singleton():
    """Test function with singleton.

    Returns:
        TODO.

    """

    class Singleton:
        """Test singleton class."""

        _instance = None

        def __new__(cls) -> Self:
            """Create singleton instance.

            Returns:
                Self: TODO.

            """
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    return Singleton


def function_with_factory():
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
        def create(type_name) -> TypeA | TypeB | None:
            """Create type for testing.

            Args:
                type_name: TODO.

            Returns:
                TypeA | TypeB | None: TODO.

            """
            if type_name == "a":
                return TypeA()
            if type_name == "b":
                return TypeB()
            return None

    return Factory


def function_with_builder():
    """Test function with builder.

    Returns:
        TODO.

    """

    class Product:
        """Product class for testing."""

        def __init__(self, parts) -> None:
            """Initialize product with parts.

            Args:
                parts: TODO.

            """
            self.parts = list(parts)

    class Builder:
        """Test builder class."""

        def __init__(self) -> None:
            self.parts = []

        def add_part(self, part) -> Self:
            self.parts.append(part)
            return self

        def build(self) -> Product:
            return Product(parts=self.parts)

    return Builder


def function_with_observer():
    """Test function with observer.

    Returns:
        TODO.

    """

    class Observer:
        """Test observer class."""

        def update(self, message) -> None:
            """Update observer with message.

            Args:
                message: TODO.

            """
            _ = (self, message)

    class Subject:
        """Test subject class."""

        def __init__(self) -> None:
            """Initialize subject."""
            self.observers = []

        def attach(self, observer) -> None:
            """Attach observer to subject.

            Args:
                observer: TODO.

            """
            self.observers.append(observer)

        def notify(self, message) -> None:
            """Notify all observers with message.

            Args:
                message: TODO.

            """
            for observer in self.observers:
                observer.update(message)

    return (Subject, Observer)


def function_with_strategy():
    """Test function with strategy.

    Returns:
        TODO.

    """

    class Strategy:
        """Test strategy class."""

        def execute(self, a: int, b: int) -> int:
            """Execute strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            _ = (self, a, b)
            return 0

    class AddStrategy(Strategy):
        """Test add strategy."""

        def execute(self, a: int, b: int) -> int:
            """Execute add strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            return a + b

    class MultiplyStrategy(Strategy):
        """Test multiply strategy."""

        def execute(self, a: int, b: int) -> int:
            """Execute multiply strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            return a * b

    return (AddStrategy, MultiplyStrategy)


def function_with_command():
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
                str: TODO.

            """
            return "Action performed"

    class ConcreteCommand(Command):
        """Test concrete command."""

        def __init__(self, receiver) -> None:
            self.receiver = receiver

        def execute(self) -> None:
            self.receiver.action()

    return (ConcreteCommand, Receiver)


def function_with_chain_of_responsibility():
    """Test function with chain of responsibility.

    Returns:
        TODO.

    """

    class Handler:
        """Test handler class."""

        def __init__(self) -> None:
            """Initialize handler."""
            self.next = None

        def set_next(self, handler):
            """Set next handler.

            Args:
                handler: TODO.

            Returns:
                TODO.

            """
            self.next = handler
            return handler

        def handle(self, request) -> None:
            """Handle request.

            Args:
                request: TODO.

            Returns:
                None: TODO.

            """
            if self.next is not None:
                return self.next.handle(request)
            return None

    return Handler


def function_with_decorator_stack() -> Callable[[], str]:
    """Test function with decorator stack.

    Returns:
        Callable[[], str]: TODO.

    """

    def decorator1(func):
        """Test decorator 1.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args, **kwargs):
            """Wrap decorator 1.

            Args:
                args: TODO.
                kwargs: TODO.

            Returns:
                TODO.

            """
            return func(*args, **kwargs)

        return wrapper

    def decorator2(func):
        """Test decorator 2.

        Args:
            func: TODO.

        Returns:
            TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args, **kwargs):
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
            str: TODO.

        """
        return "stacked"

    return stacked_func


def function_with_partial() -> Callable[[int], int]:
    """Test function with partial.

    Returns:
        Callable[[int], int]: TODO.

    """

    def multiply(a: int, b: int) -> int:
        """Test multiply function.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a * b

    return partial(multiply, 2)


def function_with_reduce() -> int:
    """Test function with reduce.

    Returns:
        int: TODO.

    """
    numbers: list[int] = [1, 2, 3, 4, 5]
    return reduce(lambda x, y: x + y, numbers)


def function_with_groupby():
    """Test function with groupby.

    Returns:
        TODO.

    """
    data: list[tuple[str, int]] = [("a", 1), ("b", 2), ("a", 3), ("b", 4)]
    return {
        k: [v for _, v in g]
        for k, g in groupby(iterable=sorted(data), key=lambda x: x[0])
    }


def function_with_permutations_combinations():
    """Test function with permutations and combinations.

    Returns:
        TODO.

    """
    items: list[int] = [1, 2, 3]
    perms = list(permutations(iterable=items, r=2))
    combs = list(combinations(iterable=items, r=2))
    return (perms, combs)


def function_with_defaultdict() -> defaultdict[str, int]:
    """Test function with defaultdict.

    Returns:
        defaultdict[str, int]: TODO.

    """
    d: defaultdict[str, int] = defaultdict(int)
    d["a"] += 1
    d["b"] += 2
    return d


def function_with_counter() -> Counter[int]:
    """Test function with counter.

    Returns:
        Counter[int]: TODO.

    """
    return Counter([1, 2, 2, 3, 3, 3])


def function_with_deque():
    """Test function with deque.

    Returns:
        TODO.

    """
    d = deque(iterable=[1, 2, 3])
    d.append(4)
    d.appendleft(0)
    d.pop()
    d.popleft()
    return d


def function_with_ordereddict() -> OrderedDict[str, int]:
    """Test function with ordereddict.

    Returns:
        OrderedDict[str, int]: TODO.

    """
    return OrderedDict([("a", 1), ("b", 2), ("c", 3)])


def function_with_namedtuple():
    """Test function with namedtuple.

    Returns:
        TODO.

    """
    return Point(x=1, y=2)


class Point:
    """Test point."""

    def __init__(self, x, y) -> None:
        """Initialize point.

        Args:
            x: TODO.
            y: TODO.

        """
        self.x = x
        self.y = y


def function_with_chain() -> list[int]:
    """Test function with chain.

    Returns:
        list[int]: TODO.

    """
    list1: list[int] = [1, 2, 3]
    list2: list[int] = [4, 5, 6]
    return list(chain(list1, list2))


def function_with_islice() -> list[int]:
    """Test function with islice.

    Returns:
        list[int]: TODO.

    """
    data = range(10)
    return list(islice(data, 2, 8, 2))


def function_with_takewhile_dropwhile() -> tuple[list[int], list[int]]:
    """Test function with takewhile and dropwhile.

    Returns:
        tuple[list[int], list[int]]: TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    taken: list[int] = list(takewhile(lambda x: x < THRESHOLD, data))
    dropped: list[int] = list(dropwhile(lambda x: x < THRESHOLD, data))
    return (taken, dropped)


def function_with_zip_longest():
    """Test function with zip longest.

    Returns:
        TODO.

    """
    list1: list[int] = [1, 2, 3]
    list2: list[str] = ["a", "b"]
    return list(zip_longest(list1, list2))


def function_with_product() -> list[tuple[int, str]]:
    """Test function with product.

    Returns:
        list[tuple[int, str]]: TODO.

    """
    list1: list[int] = [1, 2]
    list2: list[str] = ["a", "b"]
    return list(product(list1, list2))


def function_with_compress():
    """Test function with compress.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5]
    selectors: list[bool] = [True, False, True, False, True]
    return list(compress(data=data, selectors=selectors))


def function_with_accumulate():
    """Test function with accumulate.

    Returns:
        TODO.

    """
    data: list[int] = [1, 2, 3, 4, 5]
    return list(accumulate(iterable=data))


def function_with_conditional_output(
    value: int, mode: str
) -> int | str | DictInt | list[int]:
    """Test function with conditions, globals, and conditional output type.

    Args:
        value (int): TODO.
        mode (str): TODO.

    Returns:
        int | str | DictInt | list[int]: TODO.

    """
    if value > THRESHOLD and mode == "list":
        return [value * 2 for _ in range(MAX_VALUE)]
    if value < THRESHOLD and mode == "dict":
        return {str(object=i): i * value for i in range(MIN_LENGTH)}
    if value == THRESHOLD and mode == "str":
        return str(object=value) * MAX_VALUE
    return value + MAX_VALUE


def test_function_calls_part1():
    """Test basic function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result1: int = function_without_hints(a=1, b=2)
    result2: int = function_without_hints(a=1, b=2, c=3, d=4, e=5)
    result3: int = function_with_kwargs(10, 20, 30, 40)
    result4: int = function_with_args_kwargs(1, 2, 3, 4, 5)
    result5: int = nested_function(x=1, y=2, z=3)
    result6: list[int] = function_with_slices(
        data=[1, 2, 3, 4, 5], start=1, end=4
    )
    result7: list[int] = function_with_slices(
        data=[1, 2, 3, 4, 5], start=0, end=5, step=2
    )
    result8: tuple[list[int], dict[int, int], Generator[int]] = (
        function_with_comprehensions(items=[1, 2, 3, 4, 5])
    )
    result9: tuple[list[str], list[str], list[str]] = function_with_lambdas(
        items=["apple", "banana", "cherry"]
    )
    result10: int = function_with_recursion(n=5)
    result11: int = function_with_try_except(value="123")
    result12: int = function_with_try_except(value="abc")
    result13 = function_with_generators()
    result14 = function_with_class_methods()
    result15 = function_with_property()
    result16 = function_with_operator_overloading()
    result17 = function_with_metaclass_usage()
    result18 = function_with_multiple_inheritance()
    result19 = function_with_abstract_methods()
    result20: tuple[int, int, str] = function_with_generic_types()
    result21 = function_with_union_types()
    result22: Callable[[None | int], int | str] = (
        function_with_optional_types()
    )
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


def test_function_calls_part2():
    """Test intermediate function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result23: tuple[int, int, int, int, int] = function_with_tuple_unpacking()
    result24: tuple[DictInt, DictInt] = function_with_dict_operations()
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
    result31: tuple[None | int, None | int] = function_with_none_handling()
    result32: list[int] = function_with_star_expressions()
    result33: DictInt = function_with_double_star_expressions()
    result34: tuple[
        Callable[[int], int],
        Callable[[int, int], int],
        Callable[[int, int], int],
        Callable[[], int],
        Callable[[], int],
        Callable[[], int],
    ] = function_with_type_annotations_missing()
    result35: int = function_with_complex_conditionals()(1, 2, 3)
    nested_loop: Callable[[Sequence[Sequence[int]]], list[int]] = (
        function_with_nested_loops()
    )
    result36: list[int] = nested_loop([[1, 2], [3, 4], [5, 6]])
    result37 = function_with_slots()
    result38 = function_with_class_decorator()
    result39 = function_with_singleton()
    result40 = function_with_factory()
    result41 = function_with_builder()
    result42 = function_with_observer()
    result43 = function_with_strategy()
    result44 = function_with_command()
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


def test_function_calls_part3():
    """Test advanced function calls with kwargs where possible.

    Returns:
        TODO.

    """
    result45 = function_with_chain_of_responsibility()
    result46: Callable[[], str] = function_with_decorator_stack()
    result47: Callable[[int], int] = function_with_partial()
    result48: int = function_with_reduce()
    result49 = function_with_groupby()
    result50 = function_with_permutations_combinations()
    result51: defaultdict[str, int] = function_with_defaultdict()
    result52: Counter[int] = function_with_counter()
    result53 = function_with_deque()
    result54: OrderedDict[str, int] = function_with_ordereddict()
    result55: Point = function_with_namedtuple()
    result56: list[int] = function_with_chain()
    result57: list[int] = function_with_islice()
    result58: tuple[list[int], list[int]] = function_with_takewhile_dropwhile()
    result59 = function_with_zip_longest()
    result60: list[tuple[int, str]] = function_with_product()
    result61 = function_with_compress()
    result62 = function_with_accumulate()
    result63: int | str | DictInt | list[int] = (
        function_with_conditional_output(value=10, mode="list")
    )
    result64: int | str | DictInt | list[int] = (
        function_with_conditional_output(value=3, mode="dict")
    )
    result65: int | str | DictInt | list[int] = (
        function_with_conditional_output(value=5, mode="str")
    )
    result66: int | str | DictInt | list[int] = (
        function_with_conditional_output(value=7, mode="other")
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


def test_function_calls():
    """Test various function calls with kwargs where possible.

    Returns:
        TODO.

    """
    return {
        **test_function_calls_part1(),
        **test_function_calls_part2(),
        **test_function_calls_part3(),
    }


def test_class_instantiations() -> dict[
    str,
    BaseClass
    | DataClassExample
    | DecoratedClass
    | DerivedClass
    | MetaDecoratedClass,
]:
    """Test class instantiations with kwargs where possible.

    Returns:
        dict[
                str,
                BaseClass | DataClassExample | DecoratedClass | DerivedClass |
                MetaDecoratedClass
            ]: TODO.

    """
    return {
        "obj1": BaseClass(x=10),
        "obj2": BaseClass(x=10, y=20),
        "obj3": DerivedClass(x=10, y=20, z=30),
        "obj4": MetaDecoratedClass(value=100),
        "obj5": DataClassExample(x=1, y="test"),
        "obj6": DecoratedClass(value=50),
    }


def test_other_operations():
    """Test enum, closure, context, and vector operations.

    Returns:
        TODO.

    """
    enum_val: EnumClass = EnumClass.VALUE_A
    closure: Callable[[int], int] = closure_function(x=10)
    closure_result: int = closure(5)
    with custom_context() as resource:
        context_result: str = resource
    vector = function_with_operator_overloading()
    vec = vector(1, 2)
    vec2 = vector(3, 4)
    vec_sum = vec + vec2
    return {
        "enum_val": enum_val,
        "closure_result": closure_result,
        "context_result": context_result,
        "vec_sum": vec_sum,
    }


class SliceExampleResult:
    """Result for list and dictionary slice inference examples."""

    def __init__(
        self,
        list_slice,
        list_stride_slice,
        dict_slice,
        dict_key_slice,
        dict_value_slice,
    ) -> None:
        """Initialize slice example result.

        Args:
            list_slice: TODO.
            list_stride_slice: TODO.
            dict_slice: TODO.
            dict_key_slice: TODO.
            dict_value_slice: TODO.

        """
        self.list_slice = list_slice
        self.list_stride_slice = list_stride_slice
        self.dict_slice = dict_slice
        self.dict_key_slice = dict_key_slice
        self.dict_value_slice = dict_value_slice


class BuiltinMethodList(list[int]):
    """List subclass whose method names intentionally shadow builtins."""

    def append(self, value: int) -> None:
        """Append a doubled integer, unlike ``list.append`` semantics.

        Args:
            value (int): TODO.

        """
        super().append(value * 2)

    def count(self, value: int) -> int:
        """Return the normal list count plus one for disambiguation.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        return super().count(value) + 1


class BuiltinMethodDict(dict[str, int]):
    """Dict subclass with names shared by built-in dict methods."""

    def get(self, key: str, default=None) -> int:
        """Return a stored value or a narrowed integer default.

        Args:
            key (str): TODO.
            default: TODO.

        Returns:
            int: TODO.

        """
        fallback: int = -1 if default is None else default
        return super().get(key, fallback)

    def update(
        self, other: DictInt | tuple[()] = (), *values, **kwargs
    ) -> None:
        """Update values while multiplying every incoming integer.

        Args:
            other (DictInt | tuple[()]): TODO.
            values: TODO.
            kwargs: TODO.

        """
        incoming: DictInt = dict(other)
        for index, value in enumerate(iterable=values):
            incoming[str(object=index)] = value
        incoming.update(kwargs)
        multiplied = {key: value * 10 for key, value in incoming.items()}
        super().update(multiplied)


class CustomAddSet(set[int]):
    """Set subclass with the same method name as a custom class below."""

    def add(self, element: int) -> None:
        """Add a shifted element.

        Args:
            element (int): TODO.

        """
        super().add(element + 100)


class CustomAdder:
    """Plain custom class with ``add`` sharing a name with ``set.add``."""

    def __init__(self, seed: int) -> None:
        """Initialize custom adder.

        Args:
            seed (int): TODO.

        """
        self.seed = seed

    def add(self, element: int) -> int:
        """Return an arithmetic result instead of mutating a set.

        Args:
            element (int): TODO.

        Returns:
            int: TODO.

        """
        return self.seed + element


class ImportExampleResult:
    """Result for importlib and ``__import__`` inference examples."""

    def __init__(
        self,
        importlib_module_name,
        dunder_module_name,
        imported_join_result,
    ) -> None:
        """Initialize import example result.

        Args:
            importlib_module_name: TODO.
            dunder_module_name: TODO.
            imported_join_result: TODO.

        """
        self.importlib_module_name = importlib_module_name
        self.dunder_module_name = dunder_module_name
        self.imported_join_result = imported_join_result


class RedefinitionResult:
    """Result for variable type redefinition examples."""

    def __init__(
        self,
        first_type_value,
        second_type_value,
        third_type_value,
        union_final_value,
    ) -> None:
        """Initialize redefinition result.

        Args:
            first_type_value: TODO.
            second_type_value: TODO.
            third_type_value: TODO.
            union_final_value: TODO.

        """
        self.first_type_value = first_type_value
        self.second_type_value = second_type_value
        self.third_type_value = third_type_value
        self.union_final_value = union_final_value


class ScopeResolutionResult:
    """Result for same names in nested, class, and module scopes."""

    def __init__(
        self,
        module_value,
        outer_value,
        inner_value,
        class_value,
        method_and_nested_results,
    ) -> None:
        """Initialize scope resolution result.

        Args:
            module_value: TODO.
            outer_value: TODO.
            inner_value: TODO.
            class_value: TODO.
            method_and_nested_results: TODO.

        """
        self.module_value = module_value
        self.outer_value = outer_value
        self.inner_value = inner_value
        self.class_value = class_value
        self.method_and_nested_results = method_and_nested_results


def duplicate_scope_name(value) -> str:
    """Module-scope function intentionally reused in inner scopes.

    Args:
        value: TODO.

    Returns:
        str: TODO.

    """
    return f"module:{value}"


def function_with_list_and_dict_slices() -> SliceExampleResult:
    """Assign variables from slices of lists and dictionary views.

    Returns:
        SliceExampleResult: TODO.

    """
    numbers: list[int] = [10, 20, 30, 40, 50, 60]
    mapping: DictInt = {"alpha": 1, "beta": 2, "gamma": 3, "delta": 4}
    list_slice: list[int] = numbers[1:4]
    list_stride_slice: list[int] = numbers[::2]
    dict_slice: DictInt = dict(islice(mapping.items(), 1, 3))
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
    BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int
]:
    """Disambiguate builtin method names from custom method names.

    Returns:
        tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]: TODO.

    """
    custom_list: BuiltinMethodList = BuiltinMethodList([1, 2, 2])
    builtin_list: list[int] = [1, 2, 2]
    custom_list.append(value=3)
    builtin_list.append(3)
    custom_count: int = custom_list.count(value=2)
    builtin_count: int = builtin_list.count(2)
    custom_dict: BuiltinMethodDict = BuiltinMethodDict({"a": 1})
    builtin_dict: DictInt = {"a": 1}
    custom_dict.update({"b": 2}, 3)
    builtin_dict.update({"b": 2})
    custom_set: CustomAddSet = CustomAddSet({1, 2})
    builtin_set: set[int] = {1, 2}
    custom_set.add(element=5)
    builtin_set.add(5)
    adder: CustomAdder = CustomAdder(seed=40)
    adder_result: int = adder.add(element=2)
    collision_score: int = custom_count + builtin_count + adder_result
    return (custom_list, custom_dict, custom_set, collision_score)


def function_with_importlib_and_dunder_import() -> ImportExampleResult:
    """Use both importlib and ``__import__`` in resolvable examples.

    Returns:
        ImportExampleResult: TODO.

    """
    pathlib_module = importlib.import_module(name="pathlib")
    os_path_module = __import__(name="os.path")
    imported_join_result: str = os_path_module.path.join("a", "b")
    return ImportExampleResult(
        importlib_module_name=pathlib_module.__name__,
        dunder_module_name=os_path_module.__name__,
        imported_join_result=imported_join_result,
    )


def function_with_variable_type_redefinition() -> RedefinitionResult:
    """Redefine variable types in a deliberate linear flow.

    Returns:
        RedefinitionResult: TODO.

    """
    evolving_value = None
    evolving_value = 10
    first_type_value: int | None = evolving_value
    evolving_value = "ten"
    second_type_value: int | str | None = evolving_value
    evolving_value = [1, 2, 3]
    third_type_value: list[int] = evolving_value
    evolving_value = {"ten": 10}
    union_final_value: DictInt = evolving_value
    return RedefinitionResult(
        first_type_value=first_type_value,
        second_type_value=second_type_value,
        third_type_value=third_type_value,
        union_final_value=union_final_value,
    )


def function_with_scope_resolution() -> ScopeResolutionResult:
    """Use identical names in module, function, nested, and class scopes.

    Returns:
        ScopeResolutionResult: TODO.

    """
    duplicated_name: int = 7

    def duplicate_scope_name(value: int) -> str:
        """Inner function that shadows the module-level function.

        Args:
            value (int): TODO.

        Returns:
            str: TODO.

        """
        duplicated_name: list[int] = [value, value + 1]

        def deepest():
            """Return the innermost variable with the reused name.

            Returns:
                TODO.

            """
            return duplicated_name

        return f"inner:{sum(deepest())}"

    class DuplicateScopeNameClass:
        """Class with same conceptual name family as outer symbols."""

        duplicated_name = "class"

        def method(self) -> float:
            """Return a method-local value with a reused variable name.

            Returns:
                float: TODO.

            """
            return 3.5

    instance: DuplicateScopeNameClass = DuplicateScopeNameClass()
    nested_function_result = duplicate_scope_name(value=duplicated_name)
    module_value = globals()["duplicate_scope_name"]("root")
    return ScopeResolutionResult(
        module_value=module_value,
        outer_value=duplicated_name,
        inner_value=[duplicated_name, duplicated_name + 1],
        class_value=instance.duplicated_name,
        method_and_nested_results=[instance.method(), nested_function_result],
    )


def function_with_positional_and_keyword_only(
    pos_only: int, /, normal: int, *, kw_only: int
) -> int:
    """Test function with positional-only and keyword-only arguments.

    Args:
        pos_only (int): TODO.
        normal (int): TODO.
        kw_only (int): TODO.

    Returns:
        int: TODO.

    """
    return pos_only + normal + kw_only


def test_new_inference_edge_cases() -> dict[
    str,
    ImportExampleResult
    | RedefinitionResult
    | ScopeResolutionResult
    | SliceExampleResult
    | list[int]
    | tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int],
]:
    """Run extra tests for slices, builtins, imports, and scoping.

    Returns:
        dict[
                str,
                ImportExampleResult | RedefinitionResult |
                ScopeResolutionResult | SliceExampleResult | list[int] |
                tuple[BuiltinMethodList, BuiltinMethodDict, CustomAddSet, int]
            ]: TODO.

    """
    return {
        "slices": function_with_list_and_dict_slices(),
        "builtin_name_collisions": function_with_builtin_name_collisions(),
        "imports": function_with_importlib_and_dunder_import(),
        "redefinitions": function_with_variable_type_redefinition(),
        "scope_resolution": function_with_scope_resolution(),
        "positional_and_keyword_only": [
            function_with_positional_and_keyword_only(1, normal=2, kw_only=3),
        ],
    }

    # ------------------------------------------------------------------------
    # Extended stress cases for automatic type inference.
    # ------------------------------------------------------------------------


EXTENDED_SENTINEL = object()
EXTENDED_CONTEXT = ContextVar("extended_context", default=None)


class ExtendedResult:
    """Tiny tuple-like result container intentionally left untyped."""

    def __init__(self, name: str, payload: list[int], metadata=None) -> None:
        """Store a name, payload, and metadata mapping.

        Args:
            name (str): TODO.
            payload (list[int]): TODO.
            metadata: TODO.

        """
        self.name = name
        self.payload = payload
        self.metadata = {} if metadata is None else metadata

    def __iter__(self):
        """Iterate over stored fields.

        Yields:
            TODO.

        """
        yield self.name
        yield self.payload
        yield self.metadata

    def __len__(self) -> int:
        """Return tuple-like field count.

        Returns:
            int: TODO.

        """
        return 3

    def __getitem__(self, index):
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
        values=None,
        lookup=None,
        flags=None,
    ) -> None:
        """Initialize values without leaking mutable defaults.

        Args:
            name (str): TODO.
            values: TODO.
            lookup: TODO.
            flags: TODO.

        """
        self.name = name
        self.values = [] if values is None else values
        self.lookup = {} if lookup is None else lookup
        self.flags = set() if flags is None else flags
        self.lookup.setdefault(self.name, len(self.values))
        self.flags.add(self.name in self.lookup)
        self.normalized = tuple(sorted(self.lookup.items()))


class DescriptorWithOwnerCache:
    """Descriptor using WeakKeyDictionary to stress descriptor inference."""

    def __init__(self, default: int | str) -> None:
        """Initialize descriptor storage.

        Args:
            default (int | str): TODO.

        """
        self.default = default
        self.storage = WeakKeyDictionary()

    def __set_name__(self, owner, name: str) -> None:
        """Store the owner/name pair.

        Args:
            owner: TODO.
            name (str): TODO.

        """
        self.owner = owner
        self.name = name

    def __get__(self, instance, owner=None) -> Self:
        """Return descriptor or stored instance value.

        Args:
            instance: TODO.
            owner: TODO.

        Returns:
            Self: TODO.

        """
        if instance is None:
            return self
        return self.storage.get(instance, self.default)

    def __set__(self, instance, value) -> None:
        """Set a value in weak storage.

        Args:
            instance: TODO.
            value: TODO.

        """
        self.storage[instance] = value

    def __delete__(self, instance) -> None:
        """Delete value if present.

        Args:
            instance: TODO.

        """
        with suppress(KeyError):
            del self.storage[instance]


class DescriptorStressOwner:
    """Owner class for descriptor stress."""

    score = DescriptorWithOwnerCache(default=0)
    label = DescriptorWithOwnerCache(default="unset")

    def __init__(self, score: int, label: str) -> None:
        """Initialize descriptor-backed fields.

        Args:
            score (int): TODO.
            label (str): TODO.

        """
        self.score = score
        self.label = label

    @cached_property
    def summary(self):
        """Return cached mixed summary.

        Returns:
            TODO.

        """
        return {"score": self.score, "label": self.label}


class RegistryMeta(type):
    """Metaclass that registers subclasses and injects attributes."""

    registry = None

    def __new__(mcls, name: str, bases, namespace, **_kwargs):
        """Create class and register it by lower-case name.

        Args:
            mcls: TODO.
            name (str): TODO.
            bases: TODO.
            namespace: TODO.
            _kwargs: TODO.

        Returns:
            TODO.

        """
        namespace.setdefault("created_by_registry_meta", True)
        cls = super().__new__(mcls, name, bases, namespace)
        if mcls.registry is None:
            mcls.registry = {}
        if not name.startswith("Abstract"):
            mcls.registry[name.lower()] = cls
        return cls

    def __call__(cls, *args, **_kwargs):
        """Create instance and mark it.

        Args:
            args: TODO.
            _kwargs: TODO.

        Returns:
            TODO.

        """
        instance = super().__call__(*args, **_kwargs)
        instance.registry_key = cls.__name__.lower()
        return instance


class RegistryBase(metaclass=RegistryMeta):
    """Base class using RegistryMeta."""

    def clone(self, **overrides):
        """Clone using the current instance dictionary.

        Args:
            overrides: TODO.

        Returns:
            TODO.

        """
        data: DictInt = dict(self.__dict__)
        data.update(overrides)
        return self.__class__(**data)


class RegistryItem(RegistryBase):
    """Concrete registry item."""

    def __init__(self, name: str, count: int = 0, tags=None, **extras) -> None:
        """Initialize with optional tags and arbitrary extras.

        Args:
            name (str): TODO.
            count (int): TODO.
            tags: TODO.
            extras: TODO.

        """
        self.name = name
        self.count = count
        self.tags = [] if tags is None else tags
        self.extras = extras

    def bump(self, amount: int = 1) -> Self:
        """Increment count and return self for chaining.

        Args:
            amount (int): TODO.

        Returns:
            Self: TODO.

        """
        self.count += amount
        return self


class FluentBuilder:
    """Builder with fluent methods and conditional finalization."""

    def __init__(self) -> None:
        """Initialize builder state."""
        self.parts = []
        self.options = {}

    def add(self, part: str, *, repeat: int = 1) -> Self:
        """Add repeated parts and return self.

        Args:
            part (str): TODO.
            repeat (int): TODO.

        Returns:
            Self: TODO.

        """
        for _ in range(repeat):
            self.parts.append(part)
        return self

    def configure(self, **options) -> Self:
        """Merge options and return self.

        Args:
            options: TODO.

        Returns:
            Self: TODO.

        """
        self.options.update(options)
        return self

    def build(self, *, compact: bool = False):
        """Return a compact string or a structured result.

        Args:
            compact (bool): TODO.

        Returns:
            TODO.

        """
        if compact:
            return ":".join(self.parts)
        return {"parts": list(self.parts), "options": dict(self.options)}


class HybridContainer:
    """Container exposing list-like and dict-like operations."""

    def __init__(self, *items, **named) -> None:
        """Initialize mixed storage.

        Args:
            items: TODO.
            named: TODO.

        """
        self.items = list(items)
        self.named = dict(named)

    def __iter__(self):
        """Iterate over positional items.

        Returns:
            TODO.

        """
        return iter(self.items)

    def __contains__(self, item) -> bool:
        """Check both positional and named storage.

        Args:
            item: TODO.

        Returns:
            bool: TODO.

        """
        return item in self.items or item in self.named

    def __getitem__(self, key) -> int:
        """Return item by int index or dict key.

        Args:
            key: TODO.

        Returns:
            int: TODO.

        """
        if isinstance(key, int):
            return self.items[key]
        return self.named[key]

    def __setitem__(self, key, value) -> None:
        """Set item by int index or dict key.

        Args:
            key: TODO.
            value: TODO.

        """
        if isinstance(key, int):
            self.items[key] = value
        else:
            self.named[key] = value

    def __or__(self, other):
        """Merge with another container or mapping.

        Args:
            other: TODO.

        Returns:
            TODO.

        """
        merged: HybridContainer = HybridContainer(*self.items, **self.named)
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
            mode (str): TODO.

        """
        self.mode = mode

    def __call__(self, value, *, scale: int = 1) -> int | str | DictInt:
        """Return different types based on mode.

        Args:
            value: TODO.
            scale (int): TODO.

        Returns:
            int | str | DictInt: TODO.

        """
        if self.mode == "number":
            return value * scale
        if self.mode == "text":
            return str(object=value) * scale
        return {"value": value, "scale": scale}


class AsyncResource:
    """Async resource with enter/exit methods."""

    def __init__(self, name) -> None:
        """Initialize resource.

        Args:
            name: TODO.

        """
        self.name = name
        self.events = []

    async def __aenter__(self):
        """Enter async context.

        Returns:
            TODO.

        """
        self.events.append("enter")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Exit async context.

        Args:
            exc_type: TODO.
            exc: TODO.
            tb: TODO.

        Returns:
            TODO.

        """
        self.events.append("exit")
        return exc_type is None

    async def fetch(self, value):
        """Return async payload.

        Args:
            value: TODO.

        Returns:
            TODO.

        """
        await asyncio.sleep(delay=0)
        return {"resource": self.name, "value": value}


@contextmanager
def extended_sync_context(seed):
    """Yield a mutable context dictionary.

    Args:
        seed: TODO.

    Yields:
        TODO.

    """
    context = {"seed": seed, "events": []}
    context["events"].append("enter")
    try:
        yield context
    finally:
        context["events"].append("exit")


@asynccontextmanager
async def extended_async_context(seed):
    """Yield an async resource and mutate its events.

    Args:
        seed: TODO.

    Yields:
        TODO.

    """
    resource: AsyncResource = AsyncResource(name=f"resource-{seed}")
    async with resource as opened:
        yield opened


def preserve_signature_decorator(func):
    """Preserve arbitrary args and kwargs through a decorator.

    Args:
        func: TODO.

    Returns:
        TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, tuple):
            return list(result)
        return result

    return wrapper


def decorator_factory(prefix, *, uppercase: bool = False):
    """Create a decorator factory changing string outputs.

    Args:
        prefix: TODO.
        uppercase (bool): TODO.

    Returns:
        TODO.

    """

    def decorate(func):
        @wraps(wrapped=func)
        def wrapper(*args, **kwargs) -> str:
            result = func(*args, **kwargs)
            text: str = f"{prefix}:{result}"
            if uppercase:
                return text.upper()
            return text

        return wrapper

    return decorate


@preserve_signature_decorator
@decorator_factory(prefix="tag", uppercase=True)
def decorated_pipeline_value(value, suffix: str = "end") -> str:
    """Return decorated text.

    Args:
        value: TODO.
        suffix (str): TODO.

    Returns:
        str: TODO.

    """
    return f"{value}-{suffix}"


@singledispatch
def singledispatch_stress(
    value: int | str | list[int],
) -> dict[str, list[int] | int | str]:
    """Return the default singledispatch branch.

    Args:
        value (int | str | list[int]): TODO.

    Returns:
        dict[str, list[int] | int | str]: TODO.

    """
    return {"type": type(value).__name__, "value": value}


@singledispatch_stress.register(int)
def _(value):
    """Integer branch.

    Args:
        value: TODO.

    Returns:
        TODO.

    """
    return value * 10


@singledispatch_stress.register(str)
def _(value):
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
        n (int): TODO.

    Returns:
        tuple[int, int]: TODO.

    """
    if n <= 1:
        return (n, 1)
    left = cached_recursive_pair(n=n - 1)
    right = cached_recursive_pair(n=n - 2)
    return (left[0] + right[0], left[1] + right[1])


def function_with_pattern_matching_stress(
    value: dict[str, list[int] | int | str],
):
    """Exercise match/case inference across structural patterns.

    Args:
        value (dict[str, list[int] | int | str]): TODO.

    Returns:
        TODO.

    """
    match value:
        case {"kind": "point", "x": int(x), "y": int(y)}:
            return (x, y)
        case {"kind": "line", "points": [first, *rest]}:
            return [first, *rest]
        case [name, count] if isinstance(name, str):
            return {name: count}
        case (left, right):
            return {"left": left, "right": right}
        case None:
            return EXTENDED_SENTINEL
        case _:
            return str(object=value)


def function_with_walrus_and_narrowing(records):
    """Use walrus, truthiness, regex, and narrowing.

    Args:
        records: TODO.

    Returns:
        TODO.

    """
    totals: defaultdict[str, int] = defaultdict(int)
    matched = []
    for record in records:
        if (raw_name := record.get("name")) and isinstance(raw_name, str):
            name: str = raw_name.strip().lower()
        else:
            name: str = "unknown"
        if (raw_amount := record.get("amount")) is None:
            amount: int = 0
        elif isinstance(raw_amount, str):
            amount: int = int(raw_amount) if raw_amount.isnumeric() else 0
        elif isinstance(raw_amount, int):
            amount: int = raw_amount
        else:
            amount: int = 0
        totals[name] += amount
        if found := re.search(pattern=r"[a-z]+", string=name):
            matched.append(found.group(0))
    return totals, matched


def function_with_recursive_containers(seed):
    """Create recursive containers and aliased references.

    Args:
        seed: TODO.

    Returns:
        TODO.

    """
    root = {"seed": seed, "children": []}
    child = {"parent": root, "values": [seed]}
    root["children"].append(child)
    alias = root["children"][0]
    alias["values"].extend([seed + 1, seed + 2])
    return root


def function_with_numeric_tower(values: list[float]):
    """Mix int, float, complex, bool, and math/operator functions.

    Args:
        values (list[float]): TODO.

    Returns:
        TODO.

    """
    total: int = 0
    products: list[int] = []
    for index, value in enumerate(iterable=values):
        adjusted: int = index if isinstance(value, str) else int(value) + index
        total += adjusted
        products.append(adjusted * 2)
    mean: float = total / len(values) if values else math.nan
    magnitude = abs(complex(real=mean, imag=total))
    return total, mean, magnitude, products


def function_with_type_reassignment_maze(flag: str, payload: int | str):
    """Stress linear reassignment across unrelated runtime shapes.

    Args:
        flag (str): TODO.
        payload (int | str): TODO.

    Returns:
        TODO.

    """
    if flag == "none":
        return None
    if flag == "int":
        return 1
    if flag == "list":
        value: dict[str, int | str] | list[int | str] = [payload]
        return [*value, "extra"]
    if flag == "dict":
        value: dict[str, int | str] | list[int | str] = {"payload": payload}
        return {**value, "seen": True}
    if flag == "callable":

        def callback(item):
            return (item, payload)

        return callback("called")
    return str(object=payload)


class LocalExtendedError(Exception):
    """Local exception for inference."""


def raise_value_error() -> Never:
    """Raise ValueError with message.

    Raises:
        ValueError: TODO.

    """
    message: str = "bad value"
    raise ValueError(message)


def raise_type_error() -> Never:
    """Raise TypeError with message.

    Raises:
        TypeError: TODO.

    """
    message: str = "bad type"
    raise TypeError(message)


def raise_local_error() -> Never:
    """Raise LocalExtendedError with message.

    Raises:
        LocalExtendedError: TODO.

    """
    message: str = "local"
    raise LocalExtendedError(message)


def function_with_chained_exceptions(mode: str) -> str | dict[str, str]:
    """Exercise exception value types and chained exceptions.

    Args:
        mode (str): TODO.

    Returns:
        str | dict[str, str]: TODO.

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
        message: str = "wrapped"
        raise RuntimeError(message) from error
    except LocalExtendedError as error:
        return {"local": str(object=error)}
    else:
        return "ok"


def function_with_exception_group_stress(values):
    """Exercise except* branches and collected errors.

    Args:
        values: TODO.

    Returns:
        TODO.

    """

    def raise_error_group(errors) -> Never:
        message: str = "extended"
        raise ExceptionGroup(message, errors)

    errors = []
    value_errors = []
    type_errors = []
    for value in values:
        if isinstance(value, int) and value < 0:
            errors.append(ValueError(value))
        elif value is None:
            message: str = "missing"
            errors.append(TypeError(message))
    try:
        if errors:
            raise_error_group(errors=errors)
    except* ValueError as group:
        value_errors = [error.args[0] for error in group.exceptions]
    except* TypeError as group:
        type_errors = [str(object=error) for error in group.exceptions]
    return value_errors, type_errors


def function_with_import_and_reflection_stress(
    module_name: str, attr_name: str
) -> dict[str, bool | str]:
    """Import module dynamically and inspect attributes.

    Args:
        module_name (str): TODO.
        attr_name (str): TODO.

    Returns:
        dict[str, bool | str]: TODO.

    """
    module = importlib.import_module(name=module_name)
    attr = getattr(module, attr_name)
    attr_type = type(attr)
    return {
        "module": module.__name__,
        "attr": attr,
        "attr_type": attr_type.__name__,
        "has_doc": bool(getattr(attr, "__doc__", None)),
    }


def function_with_json_uuid_and_path_stress(tmp_name: str):
    """Exercise JSON, UUID, Path, and text round-tripping.

    Args:
        tmp_name (str): TODO.

    Returns:
        TODO.

    """
    identifier: UUID = uuid.uuid5(namespace=uuid.NAMESPACE_DNS, name=tmp_name)
    path = Path(tempfile.gettempdir()) / f"{identifier}.json"
    payload = {
        "id": str(object=identifier),
        "parts": path.stem.split(sep="-"),
        "exists": path.exists(),
    }
    path.write_text(data=json.dumps(obj=payload), encoding="utf-8")
    loaded = json.loads(s=path.read_text(encoding="utf-8"))
    path.unlink(missing_ok=True)
    return loaded


def function_with_contextvars_and_chainmap(configs: list[DictInt]):
    """Use ContextVar and ChainMap layered lookup.

    Args:
        configs (list[DictInt]): TODO.

    Returns:
        TODO.

    """
    token = EXTENDED_CONTEXT.set(None)
    try:
        current_map: DictInt = {"seed": len(configs)}
        chain_map = ChainMap(current_map, *configs)
        resolved = {key: chain_map[key] for key in chain_map}
    finally:
        EXTENDED_CONTEXT.reset(token)
    return resolved


def function_with_iterable_unpacking_stress(data: list[int]):
    """Mix star-unpacking, zip, enumerate, and heterogeneous outputs.

    Args:
        data (list[int]): TODO.

    Returns:
        TODO.

    """
    head, *middle, tail = data
    pairs = [(index, value) for index, value in enumerate(iterable=middle)]
    zipped = list(zip([head], [tail], strict=False))
    return head, middle, tail, pairs, zipped


def function_with_generator_send_throw_close(limit: int):
    """Return a generator supporting send/throw/close interactions.

    Args:
        limit (int): TODO.

    Returns:
        TODO.

    """

    def controlled_generator():
        current: int = 0
        while current < limit:
            received = yield current
            if received is None:
                current += 1
            elif received == "stop":
                return current
            else:
                current += received

    generator = controlled_generator()
    first = next(generator)
    second = generator.send(2)
    generator.close()
    return first, second, generator


def function_with_property_and_descriptor_interaction():
    """Use descriptor owner, cached property, deletion, and reset.

    Returns:
        TODO.

    """
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=10, label="alpha"
    )
    before = owner.summary
    current_score = owner.score
    if current_score is None or isinstance(
        current_score,
        DescriptorWithOwnerCache,
    ):
        current_score = 0
    owner.score = current_score + 5
    del owner.label
    after_delete = owner.label
    return before, owner.score, after_delete


def function_with_metaclass_registry_stress():
    """Create registry instances and clone them.

    Returns:
        TODO.

    """
    item: RegistryItem = RegistryItem(
        name="alpha", count=1, tags=["x"], extra=True
    )
    clone = item.bump(amount=2).clone(name="beta")
    registry = RegistryMeta.registry
    registry_names = sorted(registry) if registry else []
    return item, clone, registry_names


def function_with_fluent_builder_stress():
    """Use fluent builder and mixed finalization modes.

    Returns:
        TODO.

    """
    builder: FluentBuilder = FluentBuilder()
    structured = (
        builder.add(part="a").add("b", repeat=2).configure(debug=True).build()
    )
    compact = builder.build(compact=True)
    return structured, compact


def function_with_hybrid_container_stress():
    """Stress custom container protocols and operator overloads.

    Returns:
        TODO.

    """
    left: HybridContainer = HybridContainer(1, 2, name="left")
    right: HybridContainer = HybridContainer(3, 4, name="right", enabled=True)
    merged = left | right
    merged[0] = merged[0] + 10
    merged["extra"] = [value for value in merged if isinstance(value, int)]
    return merged, "name" in merged, merged["extra"]


def function_with_callable_object_stress():
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


async def function_with_async_comprehension_stress(values: list[int]):
    """Use async context, async helper, and async comprehension.

    Args:
        values (list[int]): TODO.

    Returns:
        TODO.

    """

    async def produce():
        for value in values:
            await asyncio.sleep(delay=0)
            yield value * 2

    async with extended_async_context(seed=len(values)) as resource:
        fetched = await resource.fetch(sum(values))
        doubled: list[int] = [value async for value in produce()]
    return fetched, doubled


def function_with_local_class_closure_stress(multiplier: int):
    """Return a local class capturing outer state.

    Args:
        multiplier (int): TODO.

    Returns:
        TODO.

    """

    class LocalMultiplier:
        """Local class closing over multiplier."""

        def __init__(self, offset: int = 0) -> None:
            self.offset = offset

        def apply(self, value: int) -> int:
            return value * multiplier + self.offset

        @classmethod
        def from_values(cls, values: list[int]):
            return cls(offset=sum(values))

    return LocalMultiplier


def function_with_nested_default_factories():
    """Build nested defaultdict structures.

    Returns:
        TODO.

    """
    tree = defaultdict(lambda: defaultdict(list))
    for section, key, value in [
        ("a", "x", 1),
        ("a", "x", 2),
        ("a", "y", 3),
        ("b", "z", 4),
    ]:
        tree[section][key].append(value)
    frozen = {
        section: {key: tuple(values) for key, values in group.items()}
        for section, group in tree.items()
    }
    return tree, frozen


def function_with_sort_key_and_grouping_stress(rows):
    """Sort/group by computed keys and return nested groups.

    Args:
        rows: TODO.

    Returns:
        TODO.

    """
    normalized: list[DictInt] = [
        {"name": row["name"].strip().lower(), "score": int(row["score"])}
        for row in rows
    ]
    normalized.sort(key=lambda row: (row["name"], -row["score"]))
    grouped = {
        name: [item["score"] for item in group]
        for name, group in groupby(
            iterable=normalized,
            key=lambda row: row["name"],
        )
    }
    return normalized, grouped


def function_with_partial_reduce_and_operator_stress(
    numbers: list[int],
) -> tuple[list[int], int, int]:
    """Mix partial, reduce, and operator functions.

    Args:
        numbers (list[int]): TODO.

    Returns:
        tuple[list[int], int, int]: TODO.

    """
    add_five = partial(operator.add, 5)
    transformed: list[int] = [add_five(number) for number in numbers]
    total: int = reduce(operator.add, transformed, 0)
    product_value: int = reduce(operator.mul, transformed, 1)
    return transformed, total, product_value


def function_with_protocol_like_runtime_checks(candidate):
    """Infer from hasattr/callable runtime protocol checks.

    Args:
        candidate: TODO.

    Returns:
        TODO.

    """
    if hasattr(candidate, "update") and callable(candidate.update):
        candidate.update("message")
        return "updated"
    if hasattr(candidate, "execute") and callable(candidate.execute):
        return candidate.execute(2, 3)
    if callable(candidate):
        return candidate("value")
    return None


def function_with_deep_attribute_assignment():
    """Assign attributes at several depths and return snapshots.

    Returns:
        TODO.

    """

    class Node:
        def __init__(self, name) -> None:
            self.name = name
            self.children = []
            self.metadata = {}

        def add(self, child):
            self.children.append(child)
            child.parent = self
            return child

    root: Node = Node(offset="root")
    child = root.add(Node(offset="child"))
    leaf = child.add(Node(offset="leaf"))
    leaf.metadata = {"depth": 2, "path": [root.name, child.name, leaf.name]}
    return root, child, leaf.metadata


def function_with_bytes_memoryview_and_slices(data: bytes):
    """Exercise bytes, bytearray, memoryview, and slice inference.

    Args:
        data (bytes): TODO.

    Returns:
        TODO.

    """
    raw = bytearray(data)
    raw.extend(b"!")
    view = memoryview(obj=raw)
    prefix: bytes = bytes(view[:2])
    ordinal_sum: int = sum(view)
    return raw, view, prefix, ordinal_sum


def function_with_map_filter_zip_stress(values: list[int]):
    """Use map/filter/zip pipelines with lambdas.

    Args:
        values (list[int]): TODO.

    Returns:
        TODO.

    """
    mapped: Generator[int] = (value * 2 for value in values)
    filtered: Generator[int] = (value for value in mapped if value % 3 != 0)
    paired = zip(values, filtered, strict=False)
    return list(paired)


def function_with_composed_inner_functions(seed: int):
    """Compose inner functions where each narrows a value.

    Args:
        seed (int): TODO.

    Returns:
        TODO.

    """

    def normalize(value: str) -> str:
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, bytes):
            return value.decode().strip().lower()
        return str(object=value)

    def tokenize(value: str):
        return [
            part
            for part in re.split(pattern=r"\W+", string=normalize(value=value))
            if part
        ]

    def score(tokens):
        return {
            token: index + seed for index, token in enumerate(iterable=tokens)
        }

    return score(tokens=tokenize(value="Alpha beta alpha"))


def function_with_mutable_default_like_pattern(value: str, store=None):
    """Avoid mutable defaults while preserving accumulator type.

    Args:
        value (str): TODO.
        store: TODO.

    Returns:
        TODO.

    """
    if store is None:
        store = []
    store.append(value)
    return store, tuple(store), set(store)


def function_with_literal_mode_dispatch(mode: str, value):
    """Dispatch by string literal-like mode.

    Args:
        mode (str): TODO.
        value: TODO.

    Returns:
        TODO.

    """
    handlers = {
        "int": int,
        "str": str,
        "repr": repr,
        "json": json.dumps,
    }
    if mode not in handlers:
        return value
    handler = handlers[mode]
    return handler(value)


def function_with_complex_boolean_narrowing(
    value: DictInt, fallback: bool
) -> int | str | bool:
    """Exercise bool-op narrowing with dict/list/tuple/string paths.

    Args:
        value (DictInt): TODO.
        fallback (bool): TODO.

    Returns:
        int | str | bool: TODO.

    """
    if isinstance(value, dict):
        if "result" in value:
            return value["result"]
        return fallback
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    if isinstance(value, str) and value.strip():
        return value.strip().upper()
    return fallback


def function_with_extended_named_results():
    """Return custom result objects and tuple-unpacking behavior.

    Returns:
        TODO.

    """
    result: ExtendedResult = ExtendedResult(
        name="alpha", payload=[1, 2, 3], metadata={"ok": True}
    )
    name: str = result.name
    payload: list[int] = result.payload
    metadata = result.metadata
    return result, name, payload[-1], metadata["ok"]


def test_extended_inference_edge_cases_part1():
    """Run extended stress cases part 1.

    Returns:
        TODO.

    """
    records: list[dict[str, None | int | str]] = [
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


def test_extended_inference_edge_cases_part2():
    """Run extended stress cases part 2.

    Returns:
        TODO.

    """
    rows: list[dict[str, int | str]] = [
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


def test_extended_inference_edge_cases_part3():
    """Run extended stress cases part 3.

    Returns:
        TODO.

    """
    local_multiplier = function_with_local_class_closure_stress(multiplier=10)
    local_instance = local_multiplier.from_values(values=[1, 2, 3])
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=3, label="candidate"
    )
    async_result = asyncio.run(
        args=function_with_async_comprehension_stress(values=[1, 2, 3]),
    )
    return {
        "local_class": local_instance.apply(5),
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
            fallback=False,
        ),
        "extended_result": function_with_extended_named_results(),
        "decorated_pipeline": decorated_pipeline_value(value="start"),
        "singledispatch_int": singledispatch_stress(value=3),
        "singledispatch_str": singledispatch_stress(value="hello"),
        "singledispatch_default": singledispatch_stress(value=[1, 2]),
        "cached_recursive": cached_recursive_pair(n=6),
        "async_result": async_result,
    }


def test_extended_inference_edge_cases():
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
