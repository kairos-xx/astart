"""Verify call-site resolution of methods (D4, D5)."""

from __future__ import annotations

from ast import AST, Attribute, Call, ClassDef, FunctionDef, Module, walk
from textwrap import dedent
from typing import TYPE_CHECKING, Final

from astart import parse
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.methods import (
    MethodIndex,
    ast_children,
    dataclass_init_names,
)
from astart.rules.resolve import binding_counts
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_instance,
    expect_is,
    expect_not_in,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from astart import CommentedModule
    from astart.rules.registry import Registries
    from astart.semantic import BoundCall


def _fix(*, source: str) -> FixResult:
    """Fix ``source`` under the guarded ceiling.

    Args:
        source: Module source text.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


BASE: Final[str] = """
class C:
    def m(self, a, b):
        print(a, b)

    def run(self):
        return self.m(1, 2)
"""


def test_self_call_is_keyworded() -> None:
    """Check that self call is keyworded."""
    result: FixResult = _fix(source=BASE)
    expect_in(item="self.m(a=1, b=2)", container=result.source)


def test_self_call_gives_the_method_parameters_a_hint() -> None:
    """Check that self call gives the method parameters a hint."""
    result: FixResult = _fix(source=BASE)
    expect_in(item="def m(self, a: int, b: int)", container=result.source)


def test_call_on_a_constructed_instance_is_keyworded() -> None:
    """Check that call on a constructed instance is keyworded."""
    result: FixResult = _fix(source=BASE + "\n\nC().m(3, 4)\n")
    expect_in(item="C().m(a=3, b=4)", container=result.source)


def test_explicit_receiver_is_not_keyworded() -> None:
    """Check that explicit receiver is not keyworded."""
    result: FixResult = _fix(source=BASE + "\n\nc = C()\nC.m(c, 5, 6)\n")
    expect_in(item="C.m(c, a=5, b=6)", container=result.source)
    expect_not_in(item="self=", container=result.source)


def test_overrides_with_other_parameter_names_block_keywords() -> None:
    """Check that overrides with other parameter names block keywords."""
    result: FixResult = _fix(
        source=BASE
        + """

class D(C):
    def m(self, x, y):
        return y
""",
    )
    expect_in(item="self.m(1, 2)", container=result.source)


def test_instance_attribute_override_blocks_keywords() -> None:
    """Check that instance attribute override blocks keywords."""
    result: FixResult = _fix(source=BASE + "\n\nobj = C()\nobj.m = print\n")
    expect_in(item="self.m(1, 2)", container=result.source)


def test_static_and_class_methods_are_left_alone() -> None:
    """Check that static and class methods are left alone."""
    for decorator in ("staticmethod", "classmethod"):
        extra: str = "cls, " if decorator == "classmethod" else ""
        result: FixResult = _fix(
            source=f"""
class C:
    @{decorator}
    def m({extra}a, b):
        print(a, b)

    def run(self):
        return self.m(1, 2)
""",
        )
        expect_in(item="self.m(1, 2)", container=result.source)


def test_rebinding_self_blocks_resolution() -> None:
    """Check that rebinding self blocks resolution."""
    result: FixResult = _fix(
        source="""
class C:
    def m(self, a, b):
        print(a, b)

    def run(self, other):
        self = other
        return self.m(1, 2)
""",
    )
    expect_in(item="self.m(1, 2)", container=result.source)


def test_inherited_method_resolves_through_an_in_module_base() -> None:
    """Check that inherited method resolves through an in-module base."""
    result: FixResult = _fix(
        source="""
class B:
    def m(self, a, b):
        print(a, b)


class D(B):
    def run(self):
        return self.m(1, 2)
""",
    )
    expect_in(item="self.m(a=1, b=2)", container=result.source)


def _index(*, source: str) -> tuple[MethodIndex, CommentedModule]:
    """Build the method index of a parsed module.

    Args:
        source: Module source text.

    Returns:
        The index and the module it was built from.

    """
    module: CommentedModule = parse(
        source=dedent(text=source),
        filename="m.py",
    )
    return (
        MethodIndex(module=module, counts=binding_counts(module=module)),
        module,
    )


def _calls(*, module: Module) -> list[Call]:
    """List the call nodes of a module in walk order.

    Args:
        module: Parsed module.

    Returns:
        Every ``Call`` node.

    """
    return [node for node in walk(node=module) if isinstance(node, Call)]


def _attribute_calls(*, module: Module, name: str) -> list[Call]:
    """List the ``x.name(...)`` calls of a module.

    Args:
        module: Parsed module.
        name: Attribute name called.

    Returns:
        Matching ``Call`` nodes.

    """
    return [
        node
        for node in _calls(module=module)
        if isinstance(node.func, Attribute) and node.func.attr == name
    ]


def _class(*, module: Module, index: int = 0) -> ClassDef:
    """Return the class at a module body position.

    Args:
        module: Parsed module.
        index: Body position.

    Returns:
        The class definition.

    """
    return expect_instance(value=module.body[index], kind=ClassDef)


def _method(*, cls: ClassDef, name: str) -> FunctionDef:
    """Return a method of a class by name.

    Args:
        cls: Class definition.
        name: Method name.

    Returns:
        The method definition.

    Raises:
        AssertionError: ``name`` is not a method of ``cls``.

    """
    for item in cls.body:
        if isinstance(item, FunctionDef) and item.name == name:
            return item
    msg: str = f"{cls.name}.{name} was not found"
    raise AssertionError(msg)


def _self_call(*, source: str, name: str = "n") -> tuple[MethodIndex, Call]:
    """Index a module and return its first ``self.name(...)`` call.

    Args:
        source: Module source text.
        name: Attribute name called on ``self``.

    Returns:
        The index and the matching call node.

    """
    index, module = _index(source=source)
    calls: list[Call] = _attribute_calls(module=module, name=name)
    expect_equal(actual=len(calls), expected=1)
    return index, calls[0]


def _init_names(*, source: str) -> list[str] | None:
    """List the generated ``__init__`` names of the first class.

    Args:
        source: Module source text.

    Returns:
        The parameter names, or ``None`` for an unclear class.

    """
    module: CommentedModule = parse(
        source=dedent(text=source),
        filename="m.py",
    )
    return dataclass_init_names(cls=_class(module=module))


def test_index_marks_once_defined_class_names() -> None:
    """Only classes bound exactly once count as class names."""
    index, _module = _index(source="class C:\n    pass\n")
    expect_true(condition=index.is_class_name(name="C"))
    expect_false(condition=index.is_class_name(name="D"))


def test_is_safe_accepts_a_plain_name_call() -> None:
    """A call that is not ``x.y`` is always safe."""
    index, module = _index(source="f()\n")
    call: Call = _calls(module=module)[0]
    expect_true(condition=index.is_safe(call=call, declaration=call.func))


def test_is_safe_accepts_a_non_function_declaration() -> None:
    """A call bound to something that is not a function is safe."""
    index, module = _index(source="x.m()\n\nclass C:\n    pass\n")
    expect_true(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_class(module=module, index=1),
        ),
    )


def test_is_safe_accepts_a_single_consistent_signature() -> None:
    """One definition of the called name is trusted."""
    index, module = _index(
        source="class C:\n    def m(self, a):\n        return a\n\nx.m()\n",
    )
    expect_true(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module), name="m"),
        ),
    )


def test_is_safe_rejects_a_stored_attribute() -> None:
    """An attribute assigned anywhere is unsafe."""
    index, module = _index(
        source="""
class C:
    def m(self):
        pass

obj.m = print
x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module), name="m"),
        ),
    )


def test_is_safe_rejects_dynamic_attribute_writes() -> None:
    """A ``setattr`` call makes every attribute call unsafe."""
    index, module = _index(
        source="""
setattr(obj, 'm', f)

class C:
    def m(self):
        pass

x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module, index=1), name="m"),
        ),
    )


def test_is_safe_rejects_an_attribute_hook_use() -> None:
    """Touching ``__dict__`` makes every attribute call unsafe."""
    index, module = _index(
        source="""
obj.__dict__

class C:
    def m(self):
        pass

x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module, index=1), name="m"),
        ),
    )


def test_is_safe_rejects_an_interceptor() -> None:
    """A ``__getattribute__`` makes every attribute call unsafe."""
    index, module = _index(
        source="""
class A:
    def __getattribute__(self, name):
        return name


class C:
    def m(self):
        pass

x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module, index=1), name="m"),
        ),
    )


def test_is_safe_rejects_a_rebound_class_name() -> None:
    """A name bound twice in its class body is unsafe."""
    index, module = _index(
        source="""
class C:
    def m(self):
        pass
    m = 1

x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module), name="m"),
        ),
    )


def test_is_safe_rejects_a_second_signature_shape() -> None:
    """Two same-named definitions must share their parameter shape."""
    index, module = _index(
        source="""
def m(a):
    return a


class C:
    def m(self, a, b):
        return a

x.m()
""",
    )
    expect_false(
        condition=index.is_safe(
            call=_attribute_calls(module=module, name="m")[0],
            declaration=_method(cls=_class(module=module, index=1), name="m"),
        ),
    )


def test_dynamic_attributes_property() -> None:
    """Attribute hooks and ``setattr`` report a dynamic module."""
    index, _module = _index(
        source="""
class A:
    def __getattr__(self, name):
        return name
""",
    )
    expect_true(condition=index.dynamic_attributes)
    clean, _module2 = _index(source="x = 1\n")
    expect_false(condition=clean.dynamic_attributes)


def test_intercepts_property() -> None:
    """``__getattribute__`` reports interception."""
    index, _module = _index(
        source="""
class A:
    def __getattribute__(self, name):
        return name
""",
    )
    expect_true(condition=index.intercepts)
    clean, _module2 = _index(source="x = 1\n")
    expect_false(condition=clean.intercepts)


def test_class_ok_accepts_plain_and_final_classes() -> None:
    """A once-bound class with at most ``@final`` is trusted."""
    index, module = _index(source="class C:\n    pass\n")
    expect_true(condition=index.class_ok(cls=_class(module=module)))
    index2, module2 = _index(source="@final\nclass C:\n    pass\n")
    expect_true(condition=index2.class_ok(cls=_class(module=module2)))


def test_class_ok_rejects_other_decorators() -> None:
    """``class_ok`` admits no decorator besides ``final``."""
    index, module = _index(source="@dataclass\nclass C:\n    pass\n")
    expect_false(condition=index.class_ok(cls=_class(module=module)))


def test_class_ok_rejects_a_repeated_name() -> None:
    """A class name bound twice cannot be reasoned about."""
    index, module = _index(
        source="class C:\n    pass\n\n\nclass C:\n    pass\n",
    )
    expect_false(condition=index.class_ok(cls=_class(module=module)))


def test_class_ok_rejects_a_metaclass() -> None:
    """A class keyword makes construction untrusted."""
    index, module = _index(source="class C(metaclass=M):\n    pass\n")
    expect_false(condition=index.class_ok(cls=_class(module=module)))


def test_inherited_names_collects_base_members() -> None:
    """Base methods, class attributes and instance attributes are listed."""
    index, module = _index(
        source="""
class B:
    shared = 1

    def method(self):
        self.attr = 1


class D(B):
    pass
""",
    )
    names: set[str] = index.inherited_names(
        _cls=_class(module=module, index=1),
    )
    expect_in(item="shared", container=names)
    expect_in(item="method", container=names)
    expect_in(item="attr", container=names)


def test_inherited_names_deduplicates_shared_bases() -> None:
    """A diamond visits a shared base once."""
    index, module = _index(
        source="""
class A:
    a = 1


class B1(A):
    pass


class B2(A):
    pass


class D(B1, B2):
    pass
""",
    )
    names: set[str] = index.inherited_names(
        _cls=_class(module=module, index=3),
    )
    expect_in(item="a", container=names)


def test_inherited_names_follows_subscript_bases() -> None:
    """A ``Base[...]`` base still resolves to the module class."""
    index, module = _index(
        source="""
class B:
    x = 1


class D(B[int]):
    pass
""",
    )
    names: set[str] = index.inherited_names(
        _cls=_class(module=module, index=1),
    )
    expect_in(item="x", container=names)


def test_inherited_names_skips_foreign_bases() -> None:
    """Bases that are not module classes contribute no names."""
    index, module = _index(
        source="""
class B:
    x = 1


class D(Foreign, B):
    pass
""",
    )
    names: set[str] = index.inherited_names(
        _cls=_class(module=module, index=1),
    )
    expect_in(item="x", container=names)


def test_binds_counts_every_class_body_binding() -> None:
    """Assignments, ``del``, loops, imports and defs each count once."""
    index, module = _index(
        source="""
class C:
    x = 1
    x = 2
    del x
    for i in ():
        pass
    import os
    from re import match
    y = lambda: 0

    def m(self):
        inner = 1
""",
    )
    cls: ClassDef = _class(module=module)
    expect_equal(actual=index.binds(owner=cls, name="x"), expected=3)
    expect_equal(actual=index.binds(owner=cls, name="i"), expected=1)
    expect_equal(actual=index.binds(owner=cls, name="os"), expected=1)
    expect_equal(actual=index.binds(owner=cls, name="match"), expected=1)
    expect_equal(actual=index.binds(owner=cls, name="y"), expected=1)
    expect_equal(actual=index.binds(owner=cls, name="m"), expected=1)
    expect_equal(actual=index.binds(owner=cls, name="inner"), expected=0)
    expect_equal(actual=index.binds(owner=cls, name="missing"), expected=0)


def test_callee_allowed_for_attribute_calls() -> None:
    """Attribute callees are not blocked by module rebinding."""
    index, module = _index(source="obj.m()\n")
    expect_true(condition=index.callee_allowed(call=_calls(module=module)[0]))


def test_callee_allowed_for_class_calls() -> None:
    """A safe module class may be called; an unsafe one may not."""
    index, module = _index(source="class C:\n    pass\n\nC()\n")
    expect_true(condition=index.callee_allowed(call=_calls(module=module)[0]))
    unsafe, module2 = _index(source="class C(Foreign):\n    pass\n\nC()\n")
    expect_false(
        condition=unsafe.callee_allowed(call=_calls(module=module2)[0]),
    )


def test_callee_allowed_rejects_dynamic_attributes() -> None:
    """``setattr`` anywhere blocks construction binding."""
    index, module = _index(
        source="setattr(obj, 'x', 1)\n\nclass C:\n    pass\n\nC()\n",
    )
    expect_false(
        condition=index.callee_allowed(call=_calls(module=module)[1]),
    )


def test_callee_allowed_rejects_dynamic_names() -> None:
    """``globals()`` makes bare-name calls unsafe."""
    index, module = _index(source="globals()\n\nf()\n")
    expect_false(
        condition=index.callee_allowed(call=_calls(module=module)[1]),
    )
    clean, module2 = _index(source="f()\n")
    expect_true(condition=clean.callee_allowed(call=_calls(module=module2)[0]))


def test_constructor_safe_unknown_name() -> None:
    """Names outside the module are assumed safe."""
    index, _module = _index(source="x = 1\n")
    expect_true(condition=index.constructor_safe(name="Missing"))


def test_constructor_safe_rejects_cyclic_bases() -> None:
    """A base cycle stops the chain check."""
    index, _module = _index(
        source="class A(B):\n    pass\n\n\nclass B(A):\n    pass\n",
    )
    expect_false(condition=index.constructor_safe(name="A"))


def test_constructor_safe_rejects_hooks() -> None:
    """Metaclasses and rewriting decorators are unsafe."""
    metaclass, _module = _index(source="class C(metaclass=M):\n    pass\n")
    expect_false(condition=metaclass.constructor_safe(name="C"))
    decorated, _module2 = _index(source="@dec\nclass C:\n    pass\n")
    expect_false(condition=decorated.constructor_safe(name="C"))
    called, _module3 = _index(source="@dec(1)\nclass C:\n    pass\n")
    expect_false(condition=called.constructor_safe(name="C"))


def test_constructor_safe_accepts_safe_decorators() -> None:
    """``dataclass`` and ``final`` leave construction alone."""
    plain, _module = _index(source="@dataclass\nclass C:\n    pass\n")
    expect_true(condition=plain.constructor_safe(name="C"))
    dotted, _module2 = _index(
        source="@dataclasses.dataclass\nclass C:\n    pass\n",
    )
    expect_true(condition=dotted.constructor_safe(name="C"))


def test_constructor_safe_checks_new_init_agreement() -> None:
    """``__new__`` must exist alongside and match ``__init__``."""
    new_only, _module = _index(
        source="class C:\n    def __new__(cls):\n        return cls\n",
    )
    expect_false(condition=new_only.constructor_safe(name="C"))
    matching, _module2 = _index(
        source="""
class C:
    def __new__(cls, a):
        return cls
    def __init__(self, a):
        pass
""",
    )
    expect_true(condition=matching.constructor_safe(name="C"))
    mismatched, _module3 = _index(
        source="""
class C:
    def __new__(cls, a, b):
        return cls
    def __init__(self, a):
        pass
""",
    )
    expect_false(condition=mismatched.constructor_safe(name="C"))


def test_constructor_safe_checks_bases() -> None:
    """Bases must be safe builtins, exceptions, or safe module classes."""
    foreign, _module = _index(source="class C(Foreign):\n    pass\n")
    expect_false(condition=foreign.constructor_safe(name="C"))
    exception, _module2 = _index(source="class C(ValueError):\n    pass\n")
    expect_true(condition=exception.constructor_safe(name="C"))
    plain, _module3 = _index(source="class C(object):\n    pass\n")
    expect_true(condition=plain.constructor_safe(name="C"))
    compound, _module4 = _index(source="class C(B + C):\n    pass\n")
    expect_false(condition=compound.constructor_safe(name="C"))


def test_constructor_safe_follows_in_module_bases() -> None:
    """An unsafe module base poisons its subclasses."""
    unsafe, _module = _index(
        source="class B(Foreign):\n    pass\n\n\nclass D(B):\n    pass\n",
    )
    expect_false(condition=unsafe.constructor_safe(name="D"))
    safe, _module2 = _index(
        source="class B:\n    pass\n\n\nclass D(B[int]):\n    pass\n",
    )
    expect_true(condition=safe.constructor_safe(name="D"))


def test_constructed_receiver() -> None:
    """``Class().m()`` resolves; other receivers do not."""
    index, module = _index(
        source="""
class C:
    def m(self):
        pass

C().m()
obj.m()
""",
    )
    calls: list[Call] = _attribute_calls(module=module, name="m")
    expect_true(condition=index.constructed_receiver(call=calls[0]))
    expect_false(condition=index.constructed_receiver(call=calls[1]))


def test_constructed_receiver_rejects_an_unsafe_class() -> None:
    """An unsafe class is not a trusted constructed receiver."""
    index, module = _index(
        source="""
class D(Foreign):
    def m(self):
        pass

D().m()
""",
    )
    expect_false(
        condition=index.constructed_receiver(
            call=_attribute_calls(module=module, name="m")[0],
        ),
    )


def test_bind_self_call_rejects_calls_outside_methods() -> None:
    """Module-level and plain-function calls have no method context."""
    index, module = _index(source="x.m()\n")
    expect_is(
        actual=index.bind_self_call(
            call=_attribute_calls(module=module, name="m")[0],
        ),
        expected=None,
    )
    index2, module2 = _index(source="def outer():\n    self.m()\n")
    expect_is(
        actual=index2.bind_self_call(
            call=_attribute_calls(module=module2, name="m")[0],
        ),
        expected=None,
    )


def test_bind_self_call_rejects_non_receiver_calls() -> None:
    """Only ``name.method(...)`` on a simple name receiver binds."""
    index, module = _index(
        source="class C:\n    def m(self):\n        helper()\n",
    )
    expect_is(
        actual=index.bind_self_call(call=_calls(module=module)[0]),
        expected=None,
    )
    index2, module2 = _index(
        source="class C:\n    def m(self):\n        a.b.c()\n",
    )
    expect_is(
        actual=index2.bind_self_call(call=_calls(module=module2)[0]),
        expected=None,
    )


def test_bind_self_call_rejects_a_different_receiver() -> None:
    """The receiver must be the method's first parameter."""
    index, call = _self_call(
        source="""
class C:
    def n(self):
        pass
    def m(self):
        other.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_receiver_free_method() -> None:
    """A method without parameters cannot take ``self`` calls."""
    index, call = _self_call(
        source="class C:\n    def m():\n        self.n()\n",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_decorated_method() -> None:
    """A decorated enclosing method is unsafe."""
    index, call = _self_call(
        source="class C:\n    @dec\n    def m(self):\n        self.n()\n",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_rebound_receiver() -> None:
    """Rebinding ``self`` inside the method is unsafe."""
    index, call = _self_call(
        source="""
class C:
    def n(self):
        pass
    def m(self):
        self = other
        self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_an_unknown_method() -> None:
    """A name the class does not define cannot bind."""
    index, call = _self_call(
        source="class C:\n    def m(self):\n        self.missing()\n",
        name="missing",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_repeated_method() -> None:
    """Two same-named definitions are ambiguous."""
    index, call = _self_call(
        source="""
class C:
    def n(self):
        pass
    def n(self, x):
        pass
    def m(self):
        self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_keyword_base() -> None:
    """A class keyword makes the single base unusable."""
    index, call = _self_call(
        source="""
class C(Base, metaclass=M):
    def m(self):
        self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_foreign_base() -> None:
    """Only an in-module base can be searched."""
    index, call = _self_call(
        source="class C(Base):\n    def m(self):\n        self.n()\n",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_resolves_through_a_module_base() -> None:
    """A method defined on the lone in-module base binds."""
    index, call = _self_call(
        source="""
class B:
    def n(self, x):
        return x


class C(B):
    def m(self):
        self.n(1)
""",
    )
    bound: BoundCall = expect_not_none(value=index.bind_self_call(call=call))
    expect_is(actual=bound.call, expected=call)


def test_bind_self_call_rejects_a_nested_class() -> None:
    """A class inside a function has no resolvable signature."""
    index, call = _self_call(
        source="""
def outer():
    class C:
        def n(self):
            pass
        def m(self):
            self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_decorated_target() -> None:
    """A decorated resolved method is unsafe."""
    index, call = _self_call(
        source="""
class C:
    @dec
    def n(self):
        pass
    def m(self):
        self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_an_unsafe_target() -> None:
    """A name rebound in its class body is unsafe."""
    index, call = _self_call(
        source="""
class C:
    def n(self):
        pass
    n = 1
    def m(self):
        self.n()
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_starred_arguments() -> None:
    """``*args`` at the call site cannot be matched."""
    index, call = _self_call(
        source="""
class C:
    def n(self, a):
        pass
    def m(self):
        self.n(*xs)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_star_kwargs() -> None:
    """``**kwargs`` at the call site cannot be matched."""
    index, call = _self_call(
        source="""
class C:
    def n(self, a):
        pass
    def m(self):
        self.n(**kw)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_variadic_target() -> None:
    """A variadic signature cannot be matched."""
    index, call = _self_call(
        source="""
class C:
    def n(self, *args):
        pass
    def m(self):
        self.n(1)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_surplus_arguments() -> None:
    """More positional arguments than slots cannot bind."""
    index, call = _self_call(
        source="""
class C:
    def n(self, a):
        pass
    def m(self):
        self.n(1, 2)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_an_unknown_keyword() -> None:
    """A keyword the signature lacks cannot bind."""
    index, call = _self_call(
        source="""
class C:
    def n(self, a):
        pass
    def m(self):
        self.n(z=1)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_bind_self_call_rejects_a_repeated_keyword() -> None:
    """A keyword for an already-bound parameter cannot bind."""
    index, call = _self_call(
        source="""
class C:
    def n(self, a):
        pass
    def m(self):
        self.n(1, a=2)
""",
    )
    expect_is(actual=index.bind_self_call(call=call), expected=None)


def test_dataclass_init_names_collects_fields() -> None:
    """Annotated attributes become ``__init__`` parameters in order."""
    expect_equal(
        actual=_init_names(
            source="@dataclass\nclass C:\n    x: int\n    y: str = 'd'\n",
        ),
        expected=["x", "y"],
    )


def test_dataclass_init_names_skips_non_parameters() -> None:
    """``ClassVar``, ``init=False`` and other statements are skipped."""
    expect_equal(
        actual=_init_names(
            source="""
@dataclass
class C:
    '''doc'''
    x: int
    marker: ClassVar[int] = 0
    skipped: int = field(init=False)
    gone: int = dataclasses.field(init=False)
    made: int = factory()
    keep: int = field(init=True)

    def helper(self):
        pass
""",
        ),
        expected=["x", "made", "keep"],
    )


def test_dataclass_init_names_rejects_unclear_headers() -> None:
    """Only a lone neutral ``@dataclass`` on a plain class qualifies."""
    for source in (
        "class C:\n    x: int\n",
        "@a\n@b\nclass C:\n    x: int\n",
        "@dec\nclass C:\n    x: int\n",
        "@dataclass\nclass C(Base):\n    x: int\n",
        "@dataclass\nclass C(metaclass=M):\n    x: int\n",
        "@dataclass(kw_only=True)\nclass C:\n    x: int\n",
    ):
        expect_is(actual=_init_names(source=source), expected=None)


def test_dataclass_init_names_rejects_custom_construction() -> None:
    """A written ``__init__`` or ``__new__`` hides the generated one."""
    expect_is(
        actual=_init_names(
            source="""
@dataclass
class C:
    def __init__(self):
        pass
""",
        ),
        expected=None,
    )
    expect_is(
        actual=_init_names(
            source="""
@dataclass
class C:
    def __new__(cls):
        return cls
""",
        ),
        expected=None,
    )


def test_dataclass_init_names_rejects_unclear_fields() -> None:
    """``KW_ONLY`` and per-field ``kw_only`` make the signature unclear."""
    expect_is(
        actual=_init_names(
            source="@dataclass\nclass C:\n    x: KW_ONLY\n    y: int\n",
        ),
        expected=None,
    )
    expect_is(
        actual=_init_names(
            source="@dataclass\nclass C:\n    x: int = field(kw_only=True)\n",
        ),
        expected=None,
    )
    expect_is(
        actual=_init_names(
            source="@dataclass\nclass C:\n    self.x: int\n",
        ),
        expected=None,
    )


def test_ast_children_lists_direct_children() -> None:
    """Direct children come from list and scalar ``__dict__`` fields."""
    _index_unused, module = _index(
        source="class C:\n    def m(self):\n        pass\n",
    )
    cls: ClassDef = _class(module=module)
    children: list[AST] = ast_children(node=cls)
    expect_in(item=_method(cls=cls, name="m"), container=children)
