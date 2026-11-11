"""Which names a syntax node binds."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    ClassDef,
    Del,
    ExceptHandler,
    FunctionDef,
    Global,
    MatchAs,
    MatchMapping,
    MatchStar,
    Name,
    Nonlocal,
    Store,
    alias,
    arg,
)


def names_bound_by(*, node: AST) -> tuple[str, ...]:
    """List the names a node binds, rebinds or deletes.

    Args:
        node (AST): Node to inspect.

    Returns:
        tuple[str, ...]: The names it introduces, possibly none.

    """
    names: tuple[str, ...] = ()
    match node:
        case Name(id=found, ctx=Store() | Del()) | arg(arg=found):
            names = (found,)
        case Global(names=listed) | Nonlocal(names=listed):
            names = tuple(listed)
        case alias(name=found, asname=asname):
            names = (asname or found.split(sep=".")[0],)
        case (
            ExceptHandler(name=found)
            | FunctionDef(name=found)
            | AsyncFunctionDef(name=found)
            | ClassDef(name=found)
            | MatchAs(name=found)
            | MatchStar(name=found)
            | MatchMapping(rest=found)
        ) if found is not None:
            names = (found,)
        case _:
            pass
    return names
