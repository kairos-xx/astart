"""Unit coverage for the pure helpers of ``rules.typevars``."""

from __future__ import annotations

from ast import ClassDef, FunctionDef, If, Module, expr, parse, stmt
from textwrap import dedent

from astart.rules.typevars import (
    forwarding_decorator,
    function_scope_names,
    isinstance_guard,
    passthrough_return,
    pep695_candidate,
    typevar_holders,
    variadic_passthrough,
    variance_role,
)

from tests.support.expectations import (
    FunctionStatement,
    expect_equal,
    expect_function_node,
    expect_instance,
    expect_true,
)


def _function(*, source: str) -> FunctionStatement:
    """Parse the first statement of ``source`` as a function.

    Args:
        source (str): Python source.

    Returns:
        FunctionStatement: The function node.

    """
    return expect_function_node(value=_module(source=source).body[0])


def _module(*, source: str) -> Module:
    """Parse ``source`` as a module.

    Args:
        source (str): Python source.

    Returns:
        Module: The module node.

    """
    return parse(source=dedent(text=source))


def test_variadic_passthrough_names_returned_varargs() -> None:
    """Check ``*args`` returned unchanged is named for TypeVarTuple."""
    function: FunctionStatement = _function(
        source="""\
def pack(*args):
    return args
""",
    )
    expect_equal(
        actual=variadic_passthrough(function=function),
        expected="args",
    )
    used: FunctionStatement = _function(
        source="""\
def pack(*args):
    return args + (1,)
""",
    )
    expect_equal(actual=variadic_passthrough(function=used), expected=None)
    annotated: FunctionStatement = _function(
        source="""\
def pack(*args) -> tuple:
    return args
""",
    )
    expect_equal(
        actual=variadic_passthrough(function=annotated),
        expected=None,
    )
    no_vararg: FunctionStatement = _function(
        source="""\
def pack(a):
    return a
""",
    )
    expect_equal(
        actual=variadic_passthrough(function=no_vararg),
        expected=None,
    )
    rebound: FunctionStatement = _function(
        source="""\
def pack(*args):
    args = ()
    return args
""",
    )
    expect_equal(
        actual=variadic_passthrough(function=rebound),
        expected=None,
    )


def test_variance_role_classifies_parameter_and_result_positions() -> None:
    """Check covariant, contravariant and invariant class roles."""
    covariant: ClassDef = expect_instance(
        value=_module(
            source=(
                "class Box:\n"
                "    item: T\n"
                "    def get(self) -> T:\n"
                "        return self.item\n"
            ),
        ).body[0],
        kind=ClassDef,
    )
    expect_equal(
        actual=variance_role(statement=covariant, typevar="T"),
        expected="covariant",
    )
    contravariant: ClassDef = expect_instance(
        value=_module(
            source=(
                "class Sink:\n"
                "    def put(self, item: T) -> None:\n"
                "        pass\n"
            ),
        ).body[0],
        kind=ClassDef,
    )
    expect_equal(
        actual=variance_role(statement=contravariant, typevar="T"),
        expected="contravariant",
    )
    invariant: ClassDef = expect_instance(
        value=_module(
            source=(
                "class Both:\n"
                "    def swap(self, item: T) -> T:\n"
                "        return item\n"
            ),
        ).body[0],
        kind=ClassDef,
    )
    expect_equal(
        actual=variance_role(statement=invariant, typevar="T"),
        expected=None,
    )
    unused: ClassDef = expect_instance(
        value=_module(
            source="""\
class Empty:
    pass
""",
        ).body[0],
        kind=ClassDef,
    )
    expect_equal(
        actual=variance_role(statement=unused, typevar="T"),
        expected=None,
    )
    skipped_receiver: ClassDef = expect_instance(
        value=_module(
            source=(
                "class Selfish:\n"
                "    def clone(self: T) -> T:\n"
                "        return self\n"
            ),
        ).body[0],
        kind=ClassDef,
    )
    expect_equal(
        actual=variance_role(statement=skipped_receiver, typevar="T"),
        expected="covariant",
    )


def test_typevar_holders_finds_single_function_users() -> None:
    """Check holder discovery and the outside-use refusal."""
    module: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    declaration: stmt = module.body[1]
    holders, refused = typevar_holders(
        module=module,
        declaration=declaration,
        name="T",
    )
    expect_equal(actual=holders, expected=frozenset({"ident"}))
    expect_equal(actual=refused, expected=False)
    shared: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
            "def twice(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    holders, refused = typevar_holders(
        module=shared,
        declaration=shared.body[1],
        name="T",
    )
    expect_equal(
        actual=holders,
        expected=frozenset({"ident", "twice"}),
    )
    exported: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "__all__ = ['T']\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    holders, refused = typevar_holders(
        module=exported,
        declaration=exported.body[2],
        name="T",
    )
    expect_equal(actual=holders, expected=frozenset({"ident"}))
    leaked: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "value: T\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    holders, refused = typevar_holders(
        module=leaked,
        declaration=leaked.body[1],
        name="T",
    )
    expect_true(condition=refused)


def test_pep695_candidate_names_single_use_module_typevars() -> None:
    """Check PEP 695 collapse candidates and their refusals."""
    module: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(
        actual=pep695_candidate(module=module),
        expected=("T", "ident"),
    )
    shared: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
            "def twice(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=shared), expected=None)
    exported: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "__all__ = ['T']\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=exported), expected=None)
    leaked: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
            "def other(y: T) -> None:\n"
            "    pass\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=leaked), expected=None)
    constrained: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T', int, str)\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=constrained), expected=None)
    aliased: Module = _module(
        source=(
            "from typing import TypeVar as TV\n"
            "T = TV('T')\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=aliased), expected=None)
    bound: Module = _module(
        source=(
            "from typing import TypeVar\n"
            "T = TypeVar('T', bound=int)\n"
            "def ident(x: T) -> T:\n"
            "    return x\n"
        ),
    )
    expect_equal(actual=pep695_candidate(module=bound), expected=None)


def test_passthrough_return_spells_generic_returns() -> None:
    """Check the identity-function return spelling and its refusals."""
    function: FunctionStatement = _function(
        source="""\
def ident(x):
    return x
""",
    )
    expect_equal(
        actual=passthrough_return(
            function=function,
            parameter="x",
            variable="T",
            counts={},
        ),
        expected="T",
    )
    annotated: FunctionStatement = _function(
        source="""\
def ident(x) -> int:
    return x
""",
    )
    expect_equal(
        actual=passthrough_return(
            function=annotated,
            parameter="x",
            variable="T",
            counts={},
        ),
        expected=None,
    )
    transformed: FunctionStatement = _function(
        source="""\
def ident(x):
    return x + 1
""",
    )
    expect_equal(
        actual=passthrough_return(
            function=transformed,
            parameter="x",
            variable="T",
            counts={},
        ),
        expected=None,
    )
    generator: FunctionStatement = _function(
        source="""\
def ident(x):
    yield x
""",
    )
    expect_equal(
        actual=passthrough_return(
            function=generator,
            parameter="x",
            variable="T",
            counts={},
        ),
        expected=None,
    )
    container: FunctionStatement = _function(
        source="""\
def ident(x):
    return [x, x]
""",
    )
    result: str | None = passthrough_return(
        function=container,
        parameter="x",
        variable="T",
        counts={},
    )
    expect_true(condition=result is not None and "T" in result)


def test_forwarding_decorator_detects_passthrough_wrappers() -> None:
    """Check ``ParamSpec`` forwarding detection and its refusals."""
    function: FunctionStatement = _function(
        source=(
            "def deco(f):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        return f(*args, **kwargs)\n"
            "    return wrapper\n"
        ),
    )
    expect_equal(
        actual=forwarding_decorator(function=function),
        expected=("f", "wrapper"),
    )
    mutating: FunctionStatement = _function(
        source=(
            "def deco(f):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        kwargs['x'] = 1\n"
            "        return f(*args, **kwargs)\n"
            "    return wrapper\n"
        ),
    )
    expect_equal(
        actual=forwarding_decorator(function=mutating),
        expected=None,
    )
    plain: FunctionStatement = _function(
        source="""\
def deco(f):
    return f
""",
    )
    expect_equal(
        actual=forwarding_decorator(function=plain),
        expected=None,
    )


def test_function_scope_names_collects_bindings() -> None:
    """Check the generated-name avoidance set."""
    function: FunctionStatement = _function(
        source=(
            "def f(a, *args, key=1, **kwargs):\n"
            "    local = 1\n"
            "    return a + local\n"
        ),
    )
    names: frozenset[str] = function_scope_names(function=function)
    for expected in ("a", "args", "key", "kwargs", "local"):
        expect_true(condition=expected in names)


def _if_test(*, module: Module) -> expr:
    """Return the test expression of the module's first ``if``.

    Args:
        module (Module): Module holding one function with an ``if``.

    Returns:
        expr: The ``if`` test expression.

    """
    function: FunctionDef = expect_instance(
        value=module.body[0],
        kind=FunctionDef,
    )
    statement: If = expect_instance(value=function.body[0], kind=If)
    return statement.test


def test_isinstance_guard_collects_constraint_classes() -> None:
    """Check isinstance-only tests yield constraint classes."""
    module: Module = _module(
        source=(
            "def f(x):\n"
            "    if isinstance(x, int):\n"
            "        return x\n"
            "    return 0\n"
        ),
    )
    int_guard: frozenset[str] | None = isinstance_guard(
        test=_if_test(module=module),
        parameter="x",
        counts={},
    )
    expect_equal(actual=int_guard, expected=frozenset({"int"}))
    mixed: Module = _module(
        source=(
            "def f(x):\n"
            "    if isinstance(x, int) and x > 0:\n"
            "        return x\n"
            "    return 0\n"
        ),
    )
    mixed_guard: frozenset[str] | None = isinstance_guard(
        test=_if_test(module=mixed),
        parameter="x",
        counts={},
    )
    expect_equal(actual=mixed_guard, expected=None)
    tupled: Module = _module(
        source=(
            "def f(x):\n"
            "    if isinstance(x, (int, str)):\n"
            "        return x\n"
            "    return 0\n"
        ),
    )
    tuple_guard: frozenset[str] | None = isinstance_guard(
        test=_if_test(module=tupled),
        parameter="x",
        counts={},
    )
    expect_equal(actual=tuple_guard, expected=frozenset({"int", "str"}))
    wrong_param: Module = _module(
        source=(
            "def f(x, y):\n"
            "    if isinstance(y, int):\n"
            "        return x\n"
            "    return 0\n"
        ),
    )
    wrong_guard: frozenset[str] | None = isinstance_guard(
        test=_if_test(module=wrong_param),
        parameter="x",
        counts={},
    )
    expect_equal(actual=wrong_guard, expected=None)
