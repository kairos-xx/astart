"""Keep annotation binding checks linear in the module's AST size."""

from __future__ import annotations

from ast import AST, FunctionDef, walk
from ast import parse as ast_parse
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

import pytest
from astart import CommentedModule, parse
from astart.rules.engine_hints import LazyConversion, engine_hints
from astart.rules.negotiation import supplement

from tests.support.expectations import expect_equal

if TYPE_CHECKING:
    from collections.abc import Iterator

    from astart.rules.hints import Hint, Key


@final
@dataclass(kw_only=True, slots=True)
class _WalkCounter:
    """Count whole-module traversals without counting annotation parsing.

    Attributes:
        module (AST): Module whose traversal budget is measured.
        calls (int): Whole-module walks requested.

    """

    module: AST
    calls: int = 0

    def __call__(self, *, node: AST) -> Iterator[AST]:
        """Delegate AST traversal and count visits to the module root.

        Args:
            node (AST): Root of the requested traversal.

        Returns:
            Iterator[AST]: Nodes of the original AST walk.

        """
        if node is self.module:
            self.calls += 1
        return walk(node=node)


def test_negotiated_binding_checks_share_module_traversals(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check forty returns with two module walks rather than forty-one.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture tracking module traversals.

    """
    module: CommentedModule = parse(
        source="\n".join(
            (f"def f{index}():\n    return 1\n") for index in range(40)
        ),
    )
    counter: _WalkCounter = _WalkCounter(module=module)
    monkeypatch.setattr(target=supplement, name="walk", value=counter)
    hints: dict[Key, Hint] = supplement.negotiated_hints(
        module=module,
        proposals={},
    )
    expect_equal(actual=len(hints), expected=40)
    expect_equal(actual=counter.calls, expected=2)


def test_engine_binding_checks_share_module_traversals(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reuse one class index for every engine parameter and return hint.

    Args:
        monkeypatch (pytest.MonkeyPatch): Fixture substituting converted text
            and counting walks.

    """
    module: CommentedModule = parse(
        source="\n".join(
            (f"def f{index}(x):\n    return x\n") for index in range(40)
        ),
    )
    text: str = "\n".join(
        f"def f{index}(x: int) -> int:\n    return x\n" for index in range(40)
    )

    def converted_text(conversion: LazyConversion) -> str:
        """Provide deterministic converted annotations without execution.

        Args:
            conversion (LazyConversion): Unused conversion object.

        Returns:
            str: The fixture's already converted source.

        """
        _ = conversion
        return text

    monkeypatch.setattr(
        target=LazyConversion,
        name="text",
        value=property(fget=converted_text),
    )
    counter: _WalkCounter = _WalkCounter(module=module)
    monkeypatch.setattr(target=supplement, name="walk", value=counter)
    hints: dict[Key, Hint] = engine_hints(
        module=module,
        conversion=LazyConversion(module=module),
    )
    expect_equal(actual=len(hints), expected=80)
    expect_equal(actual=counter.calls, expected=2)


@pytest.mark.parametrize(
    ("source", "annotation", "expected"),
    [
        (
            """\
class A: pass
def f(): pass
""",
            "A",
            True,
        ),
        (
            """\
def f(): pass
class A: pass
""",
            "A",
            False,
        ),
        (
            """\
class A:
    def f(self): pass
""",
            "A",
            False,
        ),
        (
            """\
class A:
    def f(self): pass
""",
            "'A'",
            True,
        ),
        (
            """\
def outer():
    def f(): pass
class A: pass
""",
            "A",
            True,
        ),
        (
            """\
class A: pass
def f(): pass
class A: pass
""",
            "A",
            False,
        ),
        (
            """\
def f(): pass
def outer():
    class A: pass
""",
            "A",
            False,
        ),
        (
            """\
def f(): pass
class A: pass
""",
            "dict[str, A]",
            False,
        ),
        (
            """\
def f(): pass
class A: pass
""",
            "B",
            True,
        ),
    ],
)
def test_class_index_preserves_binding_refusals(
    *,
    source: str,
    annotation: str,
    expected: bool,
) -> None:
    """Keep late, enclosing, duplicate and nested-class behavior unchanged.

    Args:
        source (str): Module with the queried function named ``f``.
        annotation (str): Annotation whose binding availability is checked.
        expected (bool): Whether the original binding rule accepts it.

    """
    module: AST = ast_parse(source=source)
    function: FunctionDef = next(
        node
        for node in walk(node=module)
        if isinstance(node, FunctionDef) and node.name == "f"
    )
    parents: dict[int, AST] = supplement.parents_of(module=module)
    expect_equal(
        actual=supplement.bound_when_evaluated(
            node=function,
            source=annotation,
            module=module,
            parents=parents,
            classes=supplement.class_boundaries(module=module),
        ),
        expected=expected,
    )
    expect_equal(
        actual=supplement.bound_when_evaluated(
            node=function,
            source=annotation,
            module=module,
            parents=parents,
        ),
        expected=expected,
    )


def test_binding_check_outside_a_function_is_unchanged() -> None:
    """Leave non-signature annotations outside this binding restriction."""
    module: AST = ast_parse(
        source="""\
x = 1
""",
    )
    expect_equal(
        actual=supplement.bound_when_evaluated(
            node=module,
            source="Unknown",
            module=module,
            parents={},
            classes=supplement.class_boundaries(module=module),
        ),
        expected=True,
    )
