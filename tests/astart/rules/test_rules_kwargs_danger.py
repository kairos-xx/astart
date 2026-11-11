"""Danger matrix for the keyword fixer: unsafe calls must stay positional."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_in

if TYPE_CHECKING:
    from astart.rules.registry import Registries


type Case = tuple[str, str, tuple[str, ...], str | None]
"""One matrix row: name, source, call texts, expected-failure reason."""


@final
class Constants:
    """Group module-level constants.

    Attributes:
        cases (Final[tuple[Case, ...]]): Danger-matrix rows. ``needles`` are
            call texts that must survive
            ``fix_source`` verbatim: the positional form for calls that must
            be refused, the keyworded form for calls that are proven safe.
            ``reason`` marks rows the engine is expected to fail today.

    """

    cases: Final[tuple[Case, ...]] = (
        # --- proven-safe calls are keyworded -------------------------------
        (
            "plain-function",
            """
def run(a, b):
    return a

run(1, 2)
""",
            ("run(a=1, b=2)",),
            None,
        ),
        (
            "function-defaults",
            """
def run(a, b=2):
    return a

run(1)
run(1, 5)
""",
            ("run(a=1)", "run(a=1, b=5)"),
            None,
        ),
        (
            "keyword-only-param",
            """
def run(a, *, b):
    return a

run(1, b=2)
""",
            ("run(a=1, b=2)",),
            None,
        ),
        (
            "mixed-positional-keyword",
            """
def run(a, b):
    return a

run(1, b=2)
""",
            ("run(a=1, b=2)",),
            None,
        ),
        (
            "async-function",
            """
async def run(a, b):
    return a

async def main():
    return await run(1, 2)
""",
            ("run(a=1, b=2)",),
            None,
        ),
        (
            "recursive-call",
            """
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)
""",
            ("fact(n=n - 1)",),
            None,
        ),
        (
            "nested-call",
            """
def outer(a, b):
    return a

def mid(x):
    return outer(x, 2)
""",
            ("outer(a=x, b=2)",),
            None,
        ),
        (
            "self-call",
            """
class C:
    def m(self, a, b):
        print(a, b)

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(a=1, b=2)",),
            None,
        ),
        (
            "constructed-call",
            """
class C:
    def m(self, a, b):
        print(a, b)

C().m(1, 2)
""",
            ("C().m(a=1, b=2)",),
            None,
        ),
        (
            "explicit-receiver",
            """
class C:
    def m(self, a, b):
        print(a, b)

c = C()
C.m(c, 1, 2)
""",
            ("C.m(c, a=1, b=2)",),
            None,
        ),
        (
            "unbound-method-call",
            """
class C:
    def m(self, a, b):
        print(a, b)

C.m(C(), 1, 2)
""",
            ("C.m(C(), a=1, b=2)",),
            None,
        ),
        (
            "staticmethod-via-class",
            """
class C:
    @staticmethod
    def m(a, b):
        return a

C.m(1, 2)
""",
            ("C.m(a=1, b=2)",),
            None,
        ),
        (
            "classmethod-via-class",
            """
class C:
    @classmethod
    def m(cls, a, b):
        return a

C.m(1, 2)
""",
            ("C.m(a=1, b=2)",),
            None,
        ),
        (
            "constructor-call",
            """
class C:
    def __init__(self, a, b):
        self.a = a

c = C(1, 2)
""",
            ("C(a=1, b=2)",),
            None,
        ),
        (
            "init-keyword-only",
            """
class C:
    def __init__(self, a, *, b):
        pass

C(1, b=2)
""",
            ("C(a=1, b=2)",),
            None,
        ),
        (
            "init-posonly-partial",
            """
class C:
    def __init__(self, a, /, b):
        pass

C(1, 2)
""",
            ("C(1, b=2)",),
            None,
        ),
        (
            "new-and-init-agree",
            """
class C:
    def __new__(cls, a, b):
        return super().__new__(cls)

    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(a=1, b=2)",),
            None,
        ),
        (
            "posonly-partial",
            """
def run(a, /, b, c):
    return a

run(1, 2, 3)
""",
            ("run(1, b=2, c=3)",),
            None,
        ),
        (
            "all-posonly-partial",
            """
def run(a, b, /, c):
    return a

run(1, 2, 3)
""",
            ("run(1, 2, c=3)",),
            None,
        ),
        (
            "var-keyword-call",
            """
def run(a, **kw):
    return a

run(1, x=2)
""",
            ("run(a=1, x=2)",),
            None,
        ),
        (
            "keyword-only-call",
            """
def run(a, b, *, c):
    return a

run(1, 2, c=3)
""",
            ("run(a=1, b=2, c=3)",),
            None,
        ),
        (
            "renamed-parameters",
            """
def run(alpha, beta):
    return alpha

run(1, 2)
""",
            ("run(alpha=1, beta=2)",),
            None,
        ),
        (
            "soft-keyword-parameters",
            """
def run(match, case):
    return match

run(1, 2)
""",
            ("run(match=1, case=2)",),
            None,
        ),
        (
            "method-posonly-partial",
            """
class C:
    def m(self, a, /, b):
        return a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, b=2)",),
            None,
        ),
        # --- decorated and dynamic callees are refused ---------------------
        (
            "decorated-function",
            """
def deco(fn):
    return fn

@deco
def run(a, b):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "decorator-factory",
            """
def deco(*dargs, **dkwargs):
    def wrap(fn):
        return fn
    return wrap

@deco(1, x=2)
def run(a, b):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "wraps-preserving-wrapper",
            """
import functools

def deco(fn):
    @functools.wraps(fn)
    def inner(*args, **kwargs):
        return fn(*args, **kwargs)
    return inner

@deco
def run(a, b):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "decorated-method-self-call",
            """
def deco(fn):
    return fn

class C:
    @deco
    def m(self, a, b):
        return a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "decorated-init",
            """
def deco(fn):
    return fn

class C:
    @deco
    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "property-returning-callable",
            """
class C:
    @property
    def m(self):
        return lambda a, b: a

c = C()
c.m(1, 2)
""",
            ("c.m(1, 2)",),
            None,
        ),
        (
            "singledispatch",
            """
from functools import singledispatch

@singledispatch
def run(a, b):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "overloads",
            """
from typing import overload

@overload
def run(a: int, b: int) -> int: ...
@overload
def run(a: str, b: str) -> str: ...
def run(a, b):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        # --- __getattr__, __call__ and indirect dispatch -------------------
        (
            "getattr-missing-method",
            """
class C:
    def __getattr__(self, name):
        return lambda *a: a

    def m(self, a, b):
        return a

    def run(self):
        return self.missing(1, 2)
""",
            ("self.missing(1, 2)",),
            None,
        ),
        (
            "getattr-instance-attribute",
            """
class C:
    def __getattr__(self, name):
        return lambda *a: a

c = C()
c.whatever(1, 2)
""",
            ("c.whatever(1, 2)",),
            None,
        ),
        (
            "callable-object",
            """
class Adder:
    def __call__(self, a, b):
        return a + b

add = Adder()
add(1, 2)
""",
            ("add(1, 2)",),
            None,
        ),
        (
            "dunder-call",
            """
class Adder:
    def __call__(self, a, b):
        return a + b

    def run(self):
        return self(1, 2)
""",
            ("self(1, 2)",),
            None,
        ),
        (
            "getattr-dynamic-dispatch",
            """
class C:
    def m(self, a, b):
        return a

c = C()
getattr(c, "m")(1, 2)
""",
            ('getattr(c, "m")(1, 2)',),
            None,
        ),
        (
            "call-result-call",
            """
class C:
    def m(self, a, b):
        return lambda x: x

c = C()
c.m(1, 2)(3)
""",
            ("c.m(1, 2)(3)",),
            None,
        ),
        # --- overrides and ambiguous shapes -------------------------------
        (
            "override-renamed-parameters",
            """
class B:
    def m(self, a, b):
        return a

class D(B):
    def m(self, x, y):
        return y

class E(D):
    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "override-added-parameter",
            """
class B:
    def m(self, a, b):
        return a

class D(B):
    def m(self, a, b, c):
        return c

class E(D):
    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "override-posonly",
            """
class B:
    def m(self, a, b):
        return a

class D(B):
    def m(self, a, b, /):
        return a

class E(D):
    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "instance-attribute-override",
            """
class C:
    def m(self, a, b):
        print(a, b)

    def run(self):
        return self.m(1, 2)

obj = C()
obj.m = print
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "self-attribute-rebind",
            """
class C:
    def m(self, a, b):
        return a

    def run(self):
        self.m = lambda x, y: x
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "multiple-inheritance",
            """
class A:
    def m(self, a, b):
        return a

class B:
    def m(self, x, y):
        return y

class C(A, B):
    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "conditional-method-def",
            """
class C:
    if True:
        def m(self, a, b):
            return a
    else:
        def m(self, x, y):
            return y

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "redefined-method",
            """
class C:
    def m(self, a, b):
        return a
    def m(self, x, y):
        return y

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        # --- C-implemented and positional-only callees ---------------------
        (
            "builtin-print",
            """
print("a", "b")
""",
            ('print("a", "b")',),
            None,
        ),
        (
            "builtin-getattr",
            """
getattr(obj, "x", 1)
""",
            ('getattr(obj, "x", 1)',),
            None,
        ),
        (
            "builtin-isinstance",
            """
isinstance(1, int)
""",
            ("isinstance(1, int)",),
            None,
        ),
        (
            "posonly-definition",
            """
def run(a, b, /):
    return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "init-posonly",
            """
class C:
    def __init__(self, a, b, /):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "init-var-positional",
            """
class C:
    def __init__(self, *args):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        # --- rebinding, shadowing and conditional definitions --------------
        (
            "shadowed-function",
            """
def run(a, b):
    return a

def run(a, c):
    return c

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "conditional-if-def",
            """
if True:
    def run(a, b):
        return a
else:
    def run(a, b):
        return b

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "conditional-try-def",
            """
try:
    def run(a, b):
        return a
except ImportError:
    def run(a, b):
        return b

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "conditional-import-def",
            """
try:
    from mod import run
except ImportError:
    def run(a, b):
        return a

run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "rebinding-lambda",
            """
def run(a, b):
    return a

run = lambda x, y: x
run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "global-rebinding",
            """
def run(a, b):
    return a

def swap():
    global run
    run = lambda x: x

swap()
run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "lambda-assignment",
            """
run = lambda a, b: a
run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        # --- callback containers and partials -----------------------------
        (
            "callback-list",
            """
def run(a, b):
    return a

handlers = [run]
handlers[0](1, 2)
""",
            ("handlers[0](1, 2)",),
            None,
        ),
        (
            "callback-parameter",
            """
def apply(fn, x, y):
    return fn(x, y)

def run(a, b):
    return a

apply(run, 1, 2)
""",
            ("fn(x, y)", "apply(fn=run, x=1, y=2)"),
            None,
        ),
        (
            "bound-method-alias",
            """
class C:
    def m(self, a, b):
        return a

c = C()
f = c.m
f(1, 2)
""",
            ("f(1, 2)",),
            None,
        ),
        (
            "partial-call",
            """
import functools

def run(a, b, c):
    return a

p = functools.partial(run, 1)
p(2, 3)
""",
            ("p(2, 3)",),
            None,
        ),
        (
            "partial-method-call",
            """
import functools

class C:
    def m(self, a, b):
        return a

c = C()
p = functools.partial(c.m, 1)
p(2)
""",
            ("p(2)",),
            None,
        ),
        # --- unresolved and synthesized callees ---------------------------
        (
            "method-on-parameter",
            """
class C:
    def m(self, a, b):
        return a

def use(c):
    return c.m(1, 2)
""",
            ("c.m(1, 2)",),
            None,
        ),
        (
            "chained-attribute-call",
            """
class Inner:
    def m(self, a, b):
        return a

class Outer:
    def __init__(self):
        self.inner = Inner()

o = Outer()
o.inner.m(1, 2)
""",
            ("o.inner.m(1, 2)",),
            None,
        ),
        (
            "super-method-call",
            """
class B:
    def m(self, a, b):
        return a

class D(B):
    def m(self, a, b):
        return super().m(1, 2)
""",
            ("super().m(1, 2)",),
            None,
        ),
        (
            "imported-function",
            """
from os.path import join

join("a", "b")
""",
            ('join("a", "b")',),
            None,
        ),
        (
            "dataclass-constructor",
            """
from dataclasses import dataclass

@dataclass
class C:
    a: int
    b: str

C(1, "x")
""",
            ("C(a=1, b='x')",),
            None,
        ),
        (
            "inherited-init",
            """
class B:
    def __init__(self, a, b):
        pass

class D(B):
    pass

D(1, 2)
""",
            ("D(1, 2)",),
            None,
        ),
        # --- expected failures: known-unsafe keywording --------------------
        (
            "setattr-instance-rebind",
            """
class C:
    def m(self, a, b):
        return a

c = C()
setattr(c, "m", lambda x, y: x)
c.m(1, 2)
""",
            ("c.m(1, 2)",),
            None,
        ),
        (
            "setattr-class-rebind",
            """
class C:
    def m(self, a, b):
        return a

setattr(C, "m", lambda self, x, y: x)
C().m(1, 2)
""",
            ("C().m(1, 2)",),
            None,
        ),
        (
            "object-setattr-rebind",
            """
class C:
    def m(self, a, b):
        return a

c = C()
object.__setattr__(c, "m", lambda x, y: x)
c.m(1, 2)
""",
            ("c.m(1, 2)",),
            None,
        ),
        (
            "dict-attribute-rebind",
            """
class C:
    def m(self, a, b):
        return a

c = C()
c.__dict__["m"] = lambda x, y: x
c.m(1, 2)
""",
            ("c.m(1, 2)",),
            None,
        ),
        (
            "globals-rebind",
            """
def run(a, b):
    return a

globals()["run"] = lambda x: x
run(1, 2)
""",
            ("run(1, 2)",),
            None,
        ),
        (
            "getattribute-override",
            """
class C:
    def __getattribute__(self, name):
        return lambda *a: a

    def m(self, a, b):
        return a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "descriptor-shadows-method",
            """
class Descriptor:
    def __get__(self, obj, objtype=None):
        return lambda a, b: a

class C:
    def m(self, a, b):
        return a

    m = Descriptor()

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "descriptor-before-method",
            """
class Descriptor:
    def __get__(self, obj, objtype=None):
        return lambda a, b: a

class C:
    m = Descriptor()

    def m(self, a, b):
        return a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "staticmethod-assign-shadows",
            """
class C:
    def m(self, a, b):
        return a

    m = staticmethod(lambda a, b: a)

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "partial-assign-shadows",
            """
import functools

def impl(a, b, c):
    return a

class C:
    def m(self, a, b):
        return a

    m = functools.partial(impl, 1)

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "del-method-class-body",
            """
class C:
    def m(self, a, b):
        return a

    del m

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "annotated-assign-shadows",
            """
class C:
    def m(self, a, b):
        return a

    m: object = lambda a, b: a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "tuple-assign-shadows",
            """
class C:
    def m(self, a, b):
        return a

    m = other = lambda a, b: a

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "for-target-shadows-method",
            """
class C:
    def m(self, a, b):
        return a

    for m in [lambda a, b: a]:
        pass

    def run(self):
        return self.m(1, 2)
""",
            ("self.m(1, 2)",),
            None,
        ),
        (
            "metaclass-diff-names",
            """
class Meta(type):
    def __call__(cls, x, y):
        return super().__call__(x, y)

class C(metaclass=Meta):
    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "metaclass-posonly",
            """
class Meta(type):
    def __call__(cls, a, b, /):
        return super().__call__(a, b)

class C(metaclass=Meta):
    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "new-init-mismatch",
            """
class C:
    def __new__(cls, a, b):
        return super().__new__(cls)

    def __init__(self, x, y):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "new-init-swapped",
            """
class C:
    def __new__(cls, x, y):
        return super().__new__(cls)

    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
        (
            "new-init-diff-arity",
            """
class C:
    def __new__(cls, a, b):
        return super().__new__(cls)

    def __init__(self, a, b, c):
        pass

C(1, 2, 3)
""",
            ("C(1, 2, 3)",),
            None,
        ),
        (
            "class-decorator",
            """
def deco(cls):
    return cls

@deco
class C:
    def __init__(self, a, b):
        pass

C(1, 2)
""",
            ("C(1, 2)",),
            None,
        ),
    )


def _fix(*, source: str) -> FixResult:
    """Run the guarded fix pipeline on one source.

    Args:
        source (str): Python source text.

    Returns:
        FixResult: The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=dedent(text=source),
        filename="danger.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    )


_cases: Final = [
    pytest.param(
        case,
        id=case[0],
        marks=(
            [pytest.mark.xfail(strict=True, reason=case[3])]
            if case[3] is not None
            else []
        ),
    )
    for case in Constants.cases
]


@pytest.mark.parametrize("case", _cases)
def test_keyword_fix_danger_matrix(*, case: Case) -> None:
    """Check that dangerous calls keep their positional form.

    Args:
        case (Case): Matrix row of name, source, required call texts and an
            optional expected-failure reason.

    """
    name: str
    source: str
    needles: tuple[str, ...]
    reason: str | None
    name, source, needles, reason = case
    _ = reason
    result: FixResult = _fix(source=source)
    expect_equal(
        actual=result.parse_error,
        expected=None,
        message=name,
    )
    _ = compile(source=result.source, filename=name, mode="exec")
    for needle in needles:
        expect_in(item=needle, container=result.source, message=name)
