"""M8-09 ``structure.constants-grouping``: loose module constants.

The house convention groups module constants in a ``@final class
Constants`` with ``Final`` annotations.  The detector flags top-level
``UPPER_SNAKE`` assignments and annotated constants that sit outside
such a class; dunder names, ``TYPE_CHECKING`` aliases and ``__all__``
are exempt.
"""

from __future__ import annotations

from ast import (
    AnnAssign,
    Assign,
    ClassDef,
    Constant,
    Dict,
    List,
    Module,
    Name,
    Set,
    Tuple,
    expr,
    stmt,
)
from re import compile as compile_pattern
from typing import Final, final

from astart.rules.procedural import Candidate, span_of


@final
class Constants:
    """Group module-level constants (Group module-level constants.).

    Attributes:
        class_name: The conventional grouping class name.
        constant_name: ``UPPER_SNAKE`` pattern for constant names.
        exempt: Names never flagged.
        evidence_subject: Evidence key for the constant name.

    """

    class_name: Final[str] = "Constants"
    constant_name: Final = compile_pattern(pattern=r"^[A-Z][A-Z0-9_]*$")
    exempt: Final[frozenset[str]] = frozenset({"__all__", "TYPE_CHECKING"})
    evidence_subject: str = "constant"


def find_loose_constants(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag top-level constants outside a ``Constants`` class.

    Args:
        module: Parsed module.
        filename: Name used in spans.

    Returns:
        Candidates in source order.

    """
    grouped: set[int] = _grouped_ids(module=module)
    candidates: list[Candidate] = []
    for statement in module.body:
        names: tuple[str, ...] = _constant_targets(
            statement=statement,
            grouped=grouped,
        )
        candidates.extend(
            Candidate(
                span=span_of(node=statement, filename=filename),
                evidence={Constants.evidence_subject: name},
            )
            for name in names
        )
    return tuple(candidates)


def _grouped_ids(*, module: Module) -> set[int]:
    """Collect statement ids already inside a ``Constants`` class.

    Args:
        module: Parsed module.

    Returns:
        ``id``s of statements nested in the grouping class.

    """
    inside: set[int] = set()
    for statement in module.body:
        if (
            isinstance(statement, ClassDef)
            and statement.name == Constants.class_name
        ):
            inside.update(id(item) for item in statement.body)
    return inside


def _constant_targets(
    *,
    statement: stmt,
    grouped: set[int],
) -> tuple[str, ...]:
    """Read constant names a top-level statement binds.

    Args:
        statement: Module-body statement.
        grouped: Statement ids exempt as already grouped.

    Returns:
        ``UPPER_SNAKE`` names the statement binds.

    """
    if id(statement) in grouped:
        return ()
    match statement:
        case Assign(targets=targets, value=value):
            if not _plain_value(node=value):
                return ()
            return tuple(
                target.id
                for target in targets
                if isinstance(target, Name)
                and Constants.constant_name.match(string=target.id)
                and target.id not in Constants.exempt
            )
        case AnnAssign(target=Name(id=name)):
            if (
                Constants.constant_name.match(string=name)
                and name not in Constants.exempt
            ):
                return (name,)
            return ()
        case _:
            return ()


def _plain_value(*, node: expr) -> bool:
    """Answer whether a value is a plain literal worth grouping.

    Args:
        node: Right-hand side expression.

    Returns:
        ``True`` for constants and empty/simple containers.

    """
    return isinstance(node, (Constant, List, Set, Tuple, Dict))
