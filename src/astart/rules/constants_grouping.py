"""M8-09 ``structure.constants-grouping``: loose module constants.

The house convention groups module constants in a ``@final class
Constants`` with ``Final`` annotations. The detector flags top-level
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
from typing import Final, final

from astart.rules.procedural import Candidate, span_of


def is_constant_name(*, name: str) -> bool:
    """Tell whether ``name`` is an ``UPPER_SNAKE`` constant identifier.

    Equivalent to ``^[A-Z][A-Z0-9_]*$`` without a regular expression:
    ASCII-only, leading letter, every cased character uppercase, and a
    valid identifier so digits/underscores after the first char behave
    exactly like the pattern's ``[A-Z0-9_]*`` tail.

    Args:
        name (str): Candidate identifier text.

    Returns:
        bool: ``True`` for ``MAX_VALUE``, ``A1`` and ``A_B``; ``False`` for
            ``_X`` (leading underscore fails ``isalpha``), ``x``, ``A_b``,
            ``É`` and non-identifiers.

    """
    return (
        name.isidentifier()
        and name.isascii()
        and name[0].isalpha()
        and name.isupper()
    )


@final
class Constants:
    """Group module-level constants (Group module-level constants.).

    Attributes:
        class_name (Final[str]): The conventional grouping class name.
        exempt (Final[frozenset[str]]): Names never flagged.
        evidence_subject (str): Evidence key for the constant name.

    """

    class_name: Final[str] = "Constants"
    exempt: Final[frozenset[str]] = frozenset({"__all__", "TYPE_CHECKING"})
    evidence_subject: str = "constant"


def find_loose_constants(
    *,
    module: Module,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag top-level constants outside a ``Constants`` class.

    Args:
        module (Module): Parsed module.
        filename (str): Name used in spans.

    Returns:
        tuple[Candidate, ...]: Candidates in source order.

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
        module (Module): Parsed module.

    Returns:
        set[int]: ``id``s of statements nested in the grouping class.

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
        statement (stmt): Module-body statement.
        grouped (set[int]): Statement ids exempt as already grouped.

    Returns:
        tuple[str, ...]: ``UPPER_SNAKE`` names the statement binds.

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
                and is_constant_name(name=target.id)
                and target.id not in Constants.exempt
            )
        case AnnAssign(target=Name(id=name)):
            if is_constant_name(name=name) and name not in Constants.exempt:
                return (name,)
            return ()
        case _:
            return ()


def _plain_value(*, node: expr) -> bool:
    """Answer whether a value is a plain literal worth grouping.

    Args:
        node (expr): Right-hand side expression.

    Returns:
        bool: ``True`` for constants and empty/simple containers.

    """
    return isinstance(node, (Constant, List, Set, Tuple, Dict))
