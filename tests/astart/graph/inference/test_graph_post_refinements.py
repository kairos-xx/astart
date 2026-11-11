"""Drive the generic post-refinement passes with pre-annotated modules."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    BinOp,
    ClassDef,
    Constant,
    FunctionDef,
    Load,
    Module,
    Name,
    Store,
    Subscript,
    Tuple,
    expr,
    parse,
    unparse,
)
from textwrap import dedent
from typing import TYPE_CHECKING, Final, cast, final

import pytest
from astart.graph.inference.post_refinements import (
    GenericPostRefiner,
    drop_bound_callable_arguments,
    import_insert_index,
    infer_yielded_type,
    is_narrowing,
    refine_inferred_module,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)

if TYPE_CHECKING:
    from astart.graph.inference.post_refinements import RefinementResult


def _expression(*, source: str) -> expr:
    """Parse one type expression.

    Args:
        source (str): Expression source text.

    Returns:
        expr: Parsed expression node.

    """
    return parse(source=source, mode="eval").body


def _binop(*, source: str) -> BinOp:
    """Parse a binary-operator expression.

    Args:
        source (str): Expression source text.

    Returns:
        BinOp: Parsed binary operation.

    """
    return cast(typ="BinOp", val=_expression(source=source))


def _subscript(*, source: str) -> Subscript:
    """Parse a subscript expression.

    Args:
        source (str): Expression source text.

    Returns:
        Subscript: Parsed subscript.

    """
    return cast(typ="Subscript", val=_expression(source=source))


def _function(*, source: str) -> FunctionDef:
    """Parse source and return its first function.

    Args:
        source (str): Module source text.

    Returns:
        FunctionDef: First function definition.

    """
    return cast(typ="FunctionDef", val=parse(source=source).body[0])


def _refine(*, source: str) -> tuple[str, RefinementResult]:
    """Refine a module and render the result.

    Args:
        source (str): Module source text.

    Returns:
        tuple[str, RefinementResult]: Rendered refined source and the
            refinement result.

    """
    module: Module = parse(source=dedent(text=source))
    result: RefinementResult = refine_inferred_module(module=module)
    return (result.source, result)


def test_is_narrowing_requires_shared_member_nodes() -> None:
    """Treat unions and generics as narrowing only for shared sub-nodes."""
    union: BinOp = _binop(source="int | None")
    expect_true(condition=is_narrowing(current=union, candidate=union.left))
    expect_false(condition=is_narrowing(current=union, candidate=union))
    expect_false(
        condition=is_narrowing(
            current=_expression(source="int | str"),
            candidate=_expression(source="int | bytes"),
        ),
    )
    for base in ("list", "set", "Sequence", "Iterable", "Iterator"):
        outer: Subscript = _subscript(source=f"{base}[int | str]")
        inner: BinOp = cast(typ="BinOp", val=outer.slice)
        narrowed: Subscript = Subscript(
            value=outer.value,
            slice=inner.left,
            ctx=Load(),
        )
        expect_true(condition=is_narrowing(current=outer, candidate=narrowed))
    mapping: Subscript = _subscript(source="dict[str, int | None]")
    pair: Tuple = cast(typ="Tuple", val=mapping.slice)
    key: expr = pair.elts[0]
    value: BinOp = cast(typ="BinOp", val=pair.elts[1])
    narrowed_mapping: Subscript = Subscript(
        value=mapping.value,
        slice=Tuple(elts=[key, value.left], ctx=Load()),
        ctx=Load(),
    )
    expect_true(
        condition=is_narrowing(current=mapping, candidate=narrowed_mapping),
    )
    different_key: Subscript = _subscript(source="dict[bytes, int]")
    expect_false(
        condition=is_narrowing(current=mapping, candidate=different_key),
    )
    expect_false(
        condition=is_narrowing(
            current=_expression(source="list[int]"),
            candidate=_expression(source="set[int]"),
        ),
    )
    expect_false(
        condition=is_narrowing(
            current=_expression(source="dict[str]"),
            candidate=_expression(source="dict[str, int]"),
        ),
    )
    expect_false(
        condition=is_narrowing(
            current=_expression(source="int"),
            candidate=_expression(source="str"),
        ),
    )


@final
class Constants:
    """Group module-level constants.

    Attributes:
        no_keywords (Final[frozenset[str]]): Grouped module constant.
        scenarios (Final[dict[str, str]]): Grouped module constant.

    """

    no_keywords: Final[frozenset[str]] = frozenset()
    scenarios: Final[dict[str, str]] = {
        "protocol_attributes": (
            """\
        from typing import Protocol

        class Holder(Protocol):
            value: list[object]
            count: dict[str, object]
            plain: int

        holder: Holder = make()
        holder.value = [1, 2]
        holder.count = {'a': 1}
        holder.other = 1
        other.value = 2
        pair: Holder = make()
        pair.value = [4.5]
        skipped: Holder = make()
        skipped.value = unknown_call()
        skipped.plain = 3
        """
        ),
        "metaclass_call": (
            """\
        class Meta(type):
            _instances: dict[type, object] = {}

            def __call__(cls, *args: object, **kwargs: object) -> object:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
                return instance

            def __new__(mcs, name: object, bases: object, namespace: object)\
:
                return super().__new__(mcs, name, bases, namespace)

        class Service(metaclass=Meta):
            def run(self) -> None: ...

        def build() -> object:
            service = Service()
            service.run()
            return service
        """
        ),
        "descriptor": (
            """\
        class Descriptor:
            def __get__(self, instance: object, objtype: object) -> object:
                return self

            def __set__(self, instance: object, value: object) -> None: ...

        class Other:
            def __get__(self, instance: object, objtype: int | None) -> \
object:
                return self

        class Third:
            def __get__(self, instance: object) -> object:
                return self
        """
        ),
        "singleton": (
            """\
        class Single:
            _inst: object = None

            def __new__(cls, *args: object) -> object:
                if cls._inst is None:
                    cls._inst = super().__new__(cls)
                return cls._inst

            def __enter__(self) -> object:
                return self

            def chain(self) -> object:
                return self
        """
        ),
        "proxy_decorator": (
            """\
        from typing import Callable

        def proxy(cls: object) -> object:
            class Wrapper:
                def __init__(self, *args: object) -> None:
                    instance: object = cls(*args)
                    self.instance = instance

                def __getattr__(self, name: str) -> object:
                    return getattr(self.instance, name)

            return Wrapper

        def identity(cls: object) -> object:
            result: object = cls
            return result

        @proxy
        class Thing:
            pass
        """
        ),
        "factories": (
            """\
        def make(flag: bool) -> type:
            class Local:
                pass

            class Other(Local):
                pass

            return Local

        def make_two() -> type[object]:
            class Only(int):
                pass

            return Only

        def plain() -> type:
            return int
        """
        ),
        "context_managers": (
            """\
        from contextlib import contextmanager
        from typing import Iterator

        @contextmanager
        def opened(path: str) -> object:
            handle: int = 3
            try:
                yield handle
            finally:
                pass

        @contextmanager
        def other(path: str) -> Iterator[object]:
            yield 'x'

        @contextmanager
        def empty() -> object:
            yield
        """
        ),
        "get_override": (
            """\
        class Registry(list):
            def append(self, item: int) -> None: ...

        class Third(dict):
            def get(self, key: str, default: object) -> object:
                return default

        class Fifth(dict):
            def get(self, key: str, default: int) -> int:
                return default

        class Other(dict):
            def get(self, key: str) -> int:
                return 1

        class Fourth(list):
            def append(self, item: object) -> None: ...
        """
        ),
        "init_widening": (
            """\
        class Box:
            def __init__(self, value: int, name: str = 'x') -> None:
                self.value = value
                self.name = name

            def reset(self) -> None:
                self.value = None
                self.name = 3.5

            def other(self, v: object) -> None:
                self.value = 'text'

        class Wide:
            def __init__(self, item: object) -> None:
                self.item = item

            def set(self) -> None:
                self.item = 3
        """
        ),
        "nested_numeric": (
            """\
        class Matrix:
            def __init__(self, rows: list[list[object]]) -> None:
                self.rows: list[list[object]] = rows

            def scale(self, factor: object) -> list[list[object]]:
                out: list[list[object]] = []
                for row in self.rows:
                    out.append([cell * 2.5 for cell in row])
                return out

            def total(self, values: list[list[object]]) -> float:
                total: object = 0
                for row in values:
                    for cell in row:
                        total = total + cell * 1.5
                return total
        """
        ),
        "partial_and_callables": (
            """\
        from functools import partial
        from typing import Callable

        def add(a: int, b: int) -> int:
            return a + b

        def apply(fn: Callable[..., object], value: object) -> object:
            return fn(value, 1)

        bound = partial(add, 1)
        other = partial(add, b=2)
        run = apply(add, 3)
        handler: Callable[[int], str] = add(1, 2)
        factory: Callable[[int], int] = make_callable()

        def make_callable() -> Callable[[int], int]:
            return lambda x: x
        """
        ),
        "dict_and_list": (
            """\
        def info() -> dict:
            return {'a': 1, 'b': 'x'}

        def nested(x: object) -> object:
            return {'a': [x], 'b': {'c': x}}

        def numbers(a: object) -> list:
            return [1, 2.5, a]

        def zipped(a: list[int], b: list[str]) -> object:
            import itertools
            return list(itertools.zip_longest(a, b, fillvalue=0))

        def lookup(name: str) -> object:
            return globals()[name]
        """
        ),
        "async_generators": (
            """\
        async def agen(n: int) -> object:
            for i in range(n):
                yield i

        async def agen2() -> object:
            yield 'x'
            yield b'y'

        async def consume() -> None:
            async for item in agen(3):
                print(item)
        """
        ),
        "super_calls": (
            """\
        class Base:
            def __init__(self, a: object) -> None:
                self.a = a

        class Child(Base):
            def __init__(self, a: object, b: object) -> None:
                super().__init__(a)
                self.b = b
                other = super().__new__(Child)
                other.b = 1

        class Third(Child):
            def make(self) -> object:
                inst = Child(1, 2)
                inst.b = 'x'
                return inst
        """
        ),
        "class_aliases": (
            """\
        class Node:
            def __init__(self) -> None:
                self.next: object = None

        alias = Node
        first = alias()
        second = Node()
        second.next = first

        def build() -> object:
            node = Node()
            node.next = Node()
            return node
        """
        ),
        "returned_class_bases": (
            """\
        class Base: ...

        def make() -> type:
            class Child(Base):
                pass

            return Child

        def make_generic() -> type:
            class Box(list):
                pass

            return Box
        """
        ),
        "annotated_assignments": (
            """\
        values: list[object] = []
        values.append(1)
        mapping: dict[str, object] = {}
        mapping['a'] = 1
        count: object = 0
        count += 1
        name: object = 'x'
        flag: object = True
        items: object = [1, 2, 3]
        """
        ),
        "dataclass_like": (
            """\
        class Config:
            host: None = None
            port: None = None
            mode: None = None
            name: None = None
            level: None = None

            def __init__(
                self,
                host: None,
                port: None,
                mode: None,
                name: None,
                flag: bool,
            ) -> None:
                self.host = 'localhost'
                self.port = 8080
                self.mode = 'a' if flag else 3
                self.name = None
                self.level = [1]
                self.other = 1 if flag else 2

        class Builder:
            def __init__(self, value: None) -> None:
                self.value = {'a': 1}
        """
        ),
        "metaclass_registry": (
            """\
        class Meta(type):
            registry: None = None
            other: int = 1

            def __new__(mcs, name: str, bases: object, namespace: object):
                return super().__new__(mcs, name, bases, namespace)

            def __init__(cls, name: str, bases: object, namespace: object):
                super().__init__(name, bases, namespace)

            def get(cls, key: str) -> object:
                return cls.registry
        """
        ),
        "callable_calls": (
            """\
        from typing import Callable
        import functools

        def inner(a: int, b: str) -> bool:
            return True

        bound = functools.partial(inner, 1)
        bound_keyword = functools.partial(inner, b='x')
        no_args = functools.partial()
        not_name = functools.partial(lambda: 1)
        unknown = functools.partial(missing_function, 1)

        def dispatch(name: str) -> object:
            first = globals()['inner'](1, 'a')
            second = globals()[name]()
            return first, second, locals()['x']()

        def string_dict() -> dict:
            return {'a': 1, **{'b': 2}}

        def int_dict() -> dict:
            return {1: 'a'}

        def callbacks(
            cb: Callable[..., object],
            other: Callable[[int], str],
        ) -> None:
            cb(1, 2)
            other(3)
        """
        ),
        "docstring_and_future": (
            """\
        '''Module docstring.'''
        from __future__ import annotations

        class Holder:
            def get(self) -> object:
                return self

            def chain(self) -> object:
                return self.get()
        """
        ),
    }


@pytest.mark.parametrize(
    ("signature", "positional", "keywords", "expected"),
    [
        (
            "Callable[[int, str], bool]",
            1,
            Constants.no_keywords,
            "Callable[[str], bool]",
        ),
        (
            "Callable[..., bool]",
            1,
            Constants.no_keywords,
            "Callable[..., bool]",
        ),
        ("Callable[[int], bool]", 5, Constants.no_keywords, None),
        ("Callable[[int, str], bool]", 1, frozenset({"x"}), None),
        ("list[int]", 0, Constants.no_keywords, None),
        ("Callable[int]", 0, Constants.no_keywords, None),
        (
            "Callable[int, bool]",
            0,
            Constants.no_keywords,
            "Callable[[], bool]",
        ),
    ],
)
def test_drop_bound_callable_arguments(
    *,
    signature: str,
    positional: int,
    keywords: frozenset[str],
    expected: str | None,
) -> None:
    """Remove partially applied arguments from a callable signature.

    Args:
        signature (str): Callable signature source.
        positional (int): Count of bound positional arguments.
        keywords (frozenset[str]): Names of bound keyword arguments.
        expected (str | None): Rendered result, or None when binding is unsafe.

    """
    result: expr | None = drop_bound_callable_arguments(
        signature=_expression(source=signature),
        bound_positional_count=positional,
        bound_keyword_names=keywords,
    )
    if expected is None:
        expect_equal(actual=result, expected=None)
    else:
        expect_equal(
            actual=unparse(ast_obj=cast(typ="AST", val=result)),
            expected=expected,
        )


def test_import_insert_index_skips_docstring_and_future_imports() -> None:
    """Insert new imports after the docstring and __future__ imports."""
    plain: Module = parse(source="x = 1")
    docstring: Module = parse(
        source="""\
\"""Doc.\"""
x = 1""",
    )
    futures: Module = parse(
        source=dedent(
            text=(
                """\
    \"""Doc.\"""
    from __future__ import annotations
    from x import y
    """
            ),
        ),
    )
    expect_equal(actual=import_insert_index(module=plain), expected=0)
    expect_equal(actual=import_insert_index(module=docstring), expected=1)
    expect_equal(actual=import_insert_index(module=futures), expected=2)


def test_infer_yielded_type_reads_generator_bodies() -> None:
    """Merge yielded types, including values yielded from iterables."""
    module: Module = parse(
        source=dedent(
            text="""\
            def gen(items: list[int]):
                total: float = 0.0
                yield 1
                yield 'a'
                yield total
                yield from items
                yield
                def nested():
                    yield b'ignored'
                class Inner:
                    def m(self):
                        yield 3.5
            """,
        ),
    )
    function: FunctionDef = cast(typ="FunctionDef", val=module.body[0])
    inferred: expr | None = infer_yielded_type(function=function)
    expect_true(condition=inferred is not None)
    empty: FunctionDef = _function(
        source="""\
def g():
    return 1
""",
    )
    expect_equal(actual=infer_yielded_type(function=empty), expected=None)


@pytest.mark.parametrize("name", sorted(Constants.scenarios))
def test_scenarios_refine_without_breaking_syntax(*, name: str) -> None:
    """Refine each scenario and keep the output parseable.

    Args:
        name (str): Key of the scenario source.

    """
    text, result = _refine(source=Constants.scenarios[name])
    parse(source=text)
    expect_true(condition=result.stats.changed_annotations >= 0)
    expect_false(condition=len(text) == 0)


def test_unreachable_helpers_are_correct_when_called_directly() -> None:
    """Exercise helpers that the default pipeline never invokes."""
    module: Module = parse(
        source=dedent(
            text="""\
            class Proto:
                a: int
                b: int

            def factory() -> type:
                class Local:
                    pass
                return Local

            def metaclass_call(cls):
                instance = super().__call__()
                alias = instance
                other = 3
                return alias
            """,
        ),
    )
    refiner: GenericPostRefiner = GenericPostRefiner(module=module)
    refiner.refine_returned_local_classes()
    function: FunctionDef = cast(typ="FunctionDef", val=module.body[2])
    refiner.add_cast_to_instance(
        function=function,
        instance_name="instance",
        protocol_name="Proto",
    )
    refiner.add_cast_to_instance(
        function=function,
        instance_name="absent",
        protocol_name="Proto",
    )
    refiner.annotate_instance_aliases(
        function=function,
        instance_name="instance",
        protocol_name="Proto",
    )
    attributes: dict[str, dict[str, AnnAssign]] = {
        "Proto": {
            name: AnnAssign(
                target=Name(id=name, ctx=Store()),
                annotation=Name(id="int", ctx=Load()),
                simple=1,
            )
            for name in ("a", "b")
        },
    }
    expect_equal(
        actual=refiner.find_matching_protocol(
            attributes={"a"},
            protocol_attributes=attributes,
        ),
        expected="Proto",
    )
    expect_equal(
        actual=refiner.find_matching_protocol(
            attributes={"z"},
            protocol_attributes=attributes,
        ),
        expected=None,
    )
    expect_equal(
        actual=refiner.find_protocol_by_attribute(
            attribute_name="b",
            protocol_attributes=attributes,
        ),
        expected="Proto",
    )
    expect_equal(
        actual=refiner.find_protocol_by_attribute(
            attribute_name="z",
            protocol_attributes=attributes,
        ),
        expected=None,
    )
    text: str = unparse(ast_obj=module)
    expect_in(item="cast", container=text)
    expect_in(item="-> Local", container=text)


def test_widening_helpers_rewrite_none_annotations() -> None:
    """Widen None-typed attributes and parameters for each strategy."""
    module: Module = parse(
        source=dedent(
            text="""\
            class Holder:
                one: None = None
                two: None = None
                three: None = None
                four: None = None
                five: None = None

                def __init__(
                    self,
                    one: None,
                    two: None,
                    three: None,
                    four: None,
                    five: None,
                    untyped,
                ) -> None:
                    pass
            """,
        ),
    )
    class_def: ClassDef = cast(typ="ClassDef", val=module.body[0])
    init: FunctionDef = cast(typ="FunctionDef", val=class_def.body[-1])
    refiner: GenericPostRefiner = GenericPostRefiner(module=module)
    refiner.widen_attribute_type_with_union(
        class_def=class_def,
        attr_name="one",
        type1="int",
        type2="str",
    )
    refiner.widen_init_param_type_with_union(
        init_method=init,
        attr_name="one",
        type1="int",
        type2="str",
    )
    refiner.widen_attribute_type_to_object(
        class_def=class_def,
        attr_name="two",
    )
    refiner.widen_init_param_type_to_object(init_method=init, attr_name="two")
    refiner.widen_init_param_type_to_object(
        init_method=init,
        attr_name="untyped",
    )
    refiner.widen_attribute_type_with_specific(
        class_def=class_def,
        attr_name="three",
        type_name="bytes",
    )
    refiner.widen_init_param_type_with_specific(
        init_method=init,
        attr_name="three",
        type_name="bytes",
    )
    refiner.widen_init_param_type(
        init_method=init,
        attr_name="four",
        init_value=Constant(value="text"),
    )
    refiner.widen_init_param_type(
        init_method=init,
        attr_name="untyped",
        init_value=Constant(value="text"),
    )
    refiner.widen_attribute_type(
        class_def=class_def,
        attr_name="four",
        init_value=Constant(value=3),
    )
    for value in (
        Constant(value=1),
        Constant(value="a"),
        Constant(value=b"x"),
    ):
        refiner.widen_attribute_type(
            class_def=class_def,
            attr_name="five",
            init_value=value,
        )
    expect_true(condition=refiner.stats.changed_annotations > 0)
    text: str = unparse(ast_obj=module)
    expect_in(item="None | int | str", container=text)
