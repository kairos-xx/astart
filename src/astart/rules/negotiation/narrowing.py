"""Read what tests, patterns and handlers say about names on each arm."""

from __future__ import annotations

from ast import (
    And,
    Attribute,
    BoolOp,
    Call,
    Compare,
    Constant,
    Is,
    IsNot,
    MatchAs,
    MatchClass,
    MatchOr,
    MatchSingleton,
    MatchValue,
    Name,
    NamedExpr,
    Not,
    Or,
    Tuple,
    UAdd,
    UnaryOp,
    USub,
    expr,
    pattern,
    unparse,
)
from builtins import __dict__
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

if TYPE_CHECKING:
    from collections.abc import Container, Mapping


@final
class Constants:
    """Group module-level constants.

    Attributes:
        not_none (Final[str]): Constraint text that removes ``None``.
        none (Final[str]): Constraint text of the ``None`` arm.
        pair (Final[int]): Arguments of ``isinstance``.
        conjunction (Final[str]): Joins the atoms of one arm's constraint.
        negation (Final[str]): Marks a complement atom inside a constraint.

    """

    not_none: Final[str] = "!None"
    none: Final[str] = "None"
    pair: Final[int] = 2
    conjunction: Final[str] = " & "
    negation: Final[str] = "!"


@final
@dataclass(frozen=True, slots=True)
class Arms:
    """What a test establishes about one name.

    Attributes:
        name (str): The narrowed name.
        when_true (str | None): Constraint on the arm where the test holds, or
            ``None``.
        when_false (str | None): Constraint on the arm where it does not, or
            ``None``.

    """

    name: str
    when_true: str | None
    when_false: str | None


@final
@dataclass(frozen=True, slots=True)
class CaseArms:
    """What one ``case`` pattern establishes about the match subject.

    Attributes:
        positive (str | None): Constraint inside the case body, or ``None``.
        excluded (tuple[str, ...]): Types the pattern removes for the cases
            that follow; empty
            when the pattern cannot be subtracted safely (literals,
            sequences, mappings) — guarded cases must pass ``()`` too.

    """

    positive: str | None
    excluded: tuple[str, ...]


# name -> (atoms when the test holds, atoms when it does not); a ``None``
# side marks an arm the test says nothing about.
type _Entry = tuple[tuple[str, ...] | None, tuple[str, ...] | None]
type _Reading = dict[str, _Entry]


def _tested(*, node: expr) -> str | None:
    """Name the variable a test operand reads or binds.

    Args:
        node (expr): The operand expression.

    Returns:
        str | None: ``x`` for ``x`` and ``(x := ...)``, else ``None``.

    """
    if isinstance(node, NamedExpr):
        return node.target.id
    if isinstance(node, Name):
        return node.id
    return None


def _is_none(*, test: Compare) -> _Reading:
    """Read ``x is None`` and ``x is not None``.

    Args:
        test (Compare): A comparison.

    Returns:
        _Reading: The reading, empty for any other comparison.

    """
    name: str | None = _tested(node=test.left)
    if not (
        name is not None
        and len(test.ops) == 1
        and isinstance(test.comparators[0], Constant)
        and test.comparators[0].value is None
    ):
        return {}
    if isinstance(test.ops[0], Is):
        return {name: ((Constants.none,), (Constants.not_none,))}
    if isinstance(test.ops[0], IsNot):
        return {name: ((Constants.not_none,), (Constants.none,))}
    return {}


def _isinstance(*, test: Call, counts: Mapping[str, int]) -> _Reading:
    """Read ``isinstance(x, C)`` and ``isinstance(x, (C, D))``.

    Args:
        test (Call): A call.
        counts (Mapping[str, int]): Module binding counts, to see that
            ``isinstance`` is the builtin.

    Returns:
        _Reading: The reading, empty for any other call.

    """
    name: str | None = _tested(node=test.args[0]) if test.args else None
    if not (
        isinstance(test.func, Name)
        and test.func.id == "isinstance"
        and counts.get("isinstance", 0) == 0
        and len(test.args) == Constants.pair
        and name is not None
        and not test.keywords
    ):
        return {}
    classes: expr = test.args[1]
    members: list[expr] = (
        list(classes.elts) if isinstance(classes, Tuple) else [classes]
    )
    if not members or not all(isinstance(item, Name) for item in members):
        return {}
    texts: tuple[str, ...] = tuple(unparse(ast_obj=item) for item in members)
    return {
        name: (
            (" | ".join(texts),),
            tuple(f"{Constants.negation}{text}" for text in texts),
        ),
    }


def _conjoin(*, readings: list[_Reading]) -> _Reading:
    """Merge ``and`` operands: every known true side holds at once.

    The false side of a conjunction is a disjunction of failures, which no
    single constraint expresses, so it stays unknown.

    Args:
        readings (list[_Reading]): The per-operand readings.

    Returns:
        _Reading: One reading per name.

    """
    merged: dict[str, list[str]] = {}
    for reading in readings:
        for name, (when_true, _when_false) in reading.items():
            if when_true is not None:
                merged.setdefault(name, []).extend(when_true)
    return {name: (tuple(atoms), None) for name, atoms in merged.items()}


def _disjoin(*, readings: list[_Reading]) -> _Reading:
    """Merge ``or`` operands: every known false side holds at once.

    The true side of a disjunction is a union, expressible only when every
    operand narrows the name to plain positive types.

    Args:
        readings (list[_Reading]): The per-operand readings.

    Returns:
        _Reading: One reading per name.

    """
    falses: dict[str, list[str]] = {}
    for reading in readings:
        for name, (_when_true, when_false) in reading.items():
            if when_false is not None:
                falses.setdefault(name, []).extend(when_false)
    found: _Reading = {}
    names: set[str] = {name for reading in readings for name in reading}
    for name in names:
        positives: list[str] = []
        mergeable: bool = True
        for reading in readings:
            entry: _Entry | None = reading.get(name)
            if (
                entry is None
                or entry[0] is None
                or any(
                    atom.startswith(Constants.negation) for atom in entry[0]
                )
            ):
                mergeable = False
                break
            positives.extend(entry[0])
        when_true: tuple[str, ...] | None = (
            (" | ".join(dict.fromkeys(positives)),)
            if mergeable and positives
            else None
        )
        when_false: tuple[str, ...] | None = (
            tuple(falses[name]) if name in falses else None
        )
        found[name] = (when_true, when_false)
    return found


def _read(*, test: expr, counts: Mapping[str, int]) -> _Reading:
    """Read the narrowing a test establishes, per name and per arm.

    Args:
        test (expr): The test expression.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        _Reading: Atoms for each arm; empty when the test says nothing.

    """
    if isinstance(test, UnaryOp) and isinstance(test.op, Not):
        return {
            name: (when_false, when_true)
            for name, (when_true, when_false) in _read(
                test=test.operand,
                counts=counts,
            ).items()
        }
    if isinstance(test, BoolOp) and isinstance(test.op, And):
        return _conjoin(
            readings=[
                _read(test=value, counts=counts) for value in test.values
            ],
        )
    if isinstance(test, BoolOp) and isinstance(test.op, Or):
        return _disjoin(
            readings=[
                _read(test=value, counts=counts) for value in test.values
            ],
        )
    if isinstance(test, Compare):
        return _is_none(test=test)
    if isinstance(test, Call):
        return _isinstance(test=test, counts=counts)
    name: str | None = _tested(node=test)
    return {name: ((Constants.not_none,), None)} if name is not None else {}


def read_test(*, test: expr, counts: Mapping[str, int]) -> tuple[Arms, ...]:
    """Read the narrowing an ``if`` test establishes.

    Args:
        test (expr): The test expression.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        tuple[Arms, ...]:
            class:`Arms` per name the test constrains: ``x is None``
            , ``x is not None``, ``isinstance`` (with tuples and
            ``not``), bare ``x`` (truthiness removes ``None``
            ) and ``and`` /``or`` combinations by De Morgan.

    """
    found: _Reading = _read(test=test, counts=counts)
    return tuple(
        Arms(
            name=name,
            when_true=_join(atoms=when_true),
            when_false=_join(atoms=when_false),
        )
        for name, (when_true, when_false) in sorted(found.items())
        if when_true is not None or when_false is not None
    )


def _join(*, atoms: tuple[str, ...] | None) -> str | None:
    """Render one arm's atoms as a constraint.

    Args:
        atoms (tuple[str, ...] | None): The atoms, or ``None`` for an
            unconstrained arm.

    Returns:
        str | None: The ``" & "``-joined constraint, or ``None``.

    """
    if not atoms:
        return None
    return Constants.conjunction.join(atoms)


def _resolvable(*, name: str, counts: Mapping[str, int]) -> bool:
    """Tell whether a bare name is an unshadowed builtin.

    Args:
        name (str): The name.
        counts (Mapping[str, int]): Module binding counts.

    Returns:
        bool: ``True`` when nothing in the module binds the name.

    """
    return counts.get(name, 0) == 0 and (name in __dict__)


def _class_text(
    *,
    node: expr,
    counts: Mapping[str, int],
    classes: Container[str],
) -> str | None:
    """Name the class a pattern refers to, when it resolves.

    Args:
        node (expr): The class expression.
        counts (Mapping[str, int]): Module binding counts.
        classes (Container[str]): Names of the module's own classes.

    Returns:
        str | None: The class name for a builtin or module class, the source
            text of an attribute, or ``None`` for anything else.

    """
    if isinstance(node, Name):
        if _resolvable(name=node.id, counts=counts) or node.id in classes:
            return node.id
        return None
    if isinstance(node, Attribute):
        return unparse(ast_obj=node)
    return None


def _literal_type(*, node: expr) -> str | None:
    """Give the type a literal pattern value belongs to.

    Args:
        node (expr): The pattern value.

    Returns:
        str | None:
            The builtin type name, or ``None`` when it is not a plain literal.

    """
    if isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
        return _literal_type(node=node.operand)
    if not isinstance(node, Constant):
        return None
    kinds: dict[type, str] = {
        bool: "bool",
        int: "int",
        float: "float",
        complex: "complex",
        str: "str",
        bytes: "bytes",
    }
    if node.value is None:
        return Constants.none
    return kinds.get(type(node.value))


def read_case(
    *,
    node: pattern,
    counts: Mapping[str, int],
    classes: Container[str],
) -> CaseArms:
    """Read what one ``case`` pattern establishes about the subject.

    Args:
        node (pattern): The case pattern.
        counts (Mapping[str, int]): Module binding counts.
        classes (Container[str]): Names of the module's own classes.

    Returns:
        CaseArms: The positive constraint for the case body and the types later
            cases may subtract; unsupported patterns stay opaque on both.

    """
    if isinstance(node, MatchOr):
        arms: list[CaseArms] = [
            read_case(node=item, counts=counts, classes=classes)
            for item in node.patterns
        ]
        positive: str | None = (
            " | ".join(
                dict.fromkeys(
                    arm.positive for arm in arms if arm.positive is not None
                ),
            )
            if all(arm.positive is not None for arm in arms)
            else None
        )
        return CaseArms(
            positive=positive,
            excluded=tuple(
                dict.fromkeys(text for arm in arms for text in arm.excluded),
            ),
        )
    if isinstance(node, MatchAs):
        return (
            CaseArms(positive=None, excluded=())
            if node.pattern is None
            else read_case(node=node.pattern, counts=counts, classes=classes)
        )
    if isinstance(node, MatchClass):
        text: str | None = _class_text(
            node=node.cls,
            counts=counts,
            classes=classes,
        )
        return (
            CaseArms(positive=text, excluded=(text,))
            if text is not None
            else CaseArms(positive=None, excluded=())
        )
    if isinstance(node, MatchSingleton):
        is_none: bool = node.value is None
        return CaseArms(
            positive=Constants.none if is_none else "bool",
            excluded=(Constants.none,) if is_none else (),
        )
    if isinstance(node, MatchValue):
        kind: str | None = _literal_type(node=node.value)
        return (
            CaseArms(positive=kind, excluded=())
            if kind is not None
            else CaseArms(positive=None, excluded=())
        )
    return CaseArms(positive=None, excluded=())


def exception_types(
    *,
    node: expr | None,
    counts: Mapping[str, int],
    classes: Container[str],
) -> str | None:
    """Read the type an ``except`` clause binds its name to.

    Args:
        node (expr | None): The handler's type expression, ``None`` for a bare
            ``except``.
        counts (Mapping[str, int]): Module binding counts.
        classes (Container[str]): Names of the module's own classes.

    Returns:
        str | None: The class name or the ``" | "`` -joined union
            of a tuple's classes, or ``None`` when a member
            does not resolve to a builtin or a module class.

    """
    if node is None:
        return None
    members: list[expr] = (
        list(node.elts) if isinstance(node, Tuple) else [node]
    )
    if not members or not all(isinstance(item, Name) for item in members):
        return None
    names: list[str] = []
    for item in members:
        if isinstance(item, Name):
            name: str = item.id
            if not (_resolvable(name=name, counts=counts) or name in classes):
                return None
            names.append(name)
    return " | ".join(names)
