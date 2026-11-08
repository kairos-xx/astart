"""Return types that typeshed states plainly enough to rely on."""

from __future__ import annotations

from ast import (
    AST,
    BinOp,
    BitOr,
    Constant,
    Load,
    Name,
    Subscript,
    Tuple,
    expr,
    unparse,
    walk,
)
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from astart.stubs.parser import StubName
    from astart.stubs.resolver import Resolved


@final
class Constants:
    """Group module-level constants.

    Attributes:
        plain: Builtin types a return annotation may be made of.
        decorators: Decorators a library function may carry.
        structure: Syntax a return annotation may use besides names.

    """

    plain: Final[frozenset[str]] = frozenset(
        {
            "int",
            "str",
            "bool",
            "bytes",
            "float",
            "complex",
            "list",
            "dict",
            "set",
            "frozenset",
            "tuple",
        },
    )
    decorators: Final[frozenset[str]] = frozenset({"staticmethod"})
    structure: Final[tuple[type[AST], ...]] = (BitOr, Subscript, Tuple, Load)


def _plain(*, node: expr, typevars: set[str]) -> bool:
    """Tell whether an annotation uses only builtin types and ``None``.

    Args:
        node: The return annotation.
        typevars: Type variables of the defining stub.

    Returns:
        ``True`` for builtin names, ``None``, ``X | Y`` and subscripts of
        those; ``False`` for names that need an import, type variables,
        strings and anything else.

    """
    for part in walk(node=node):
        if isinstance(part, Name):
            if part.id not in Constants.plain or part.id in typevars:
                return False
        elif isinstance(part, Constant):
            if part.value is not None and part.value is not Ellipsis:
                return False
        elif isinstance(part, BinOp):
            if not isinstance(part.op, BitOr):
                return False
        elif not isinstance(part, Constants.structure):
            return False
    return True


def function_return(*, resolved: Resolved) -> str | None:
    """State the return type of a library function, if it is certain.

    The function must have exactly one definition (no ``@overload``), be
    defined in a branch the evaluator decided, and return a type spelled with
    builtin names only, so the result does not depend on the arguments and
    needs no import.

    Args:
        resolved: The function as found by the resolver.

    Returns:
        The return annotation as source text, or ``None``.

    """
    entry: StubName = resolved.name
    if (
        entry.kind != "function"
        or entry.overloaded
        or entry.ambiguous
        or len(entry.nodes) != 1
        or resolved.owner is not None
        or set(entry.decorators) - Constants.decorators
    ):
        return None
    node: AST = entry.nodes[0]
    returns: expr | None = getattr(node, "returns", None)
    if returns is None or not _plain(
        node=returns,
        typevars=resolved.module.typevars,
    ):
        return None
    return unparse(ast_obj=returns)
