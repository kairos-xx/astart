"""Annotation-recovery benchmark: strip a typed module, fix it, compare.

Well-typed code is the ground truth. Removing its parameter and return
annotations and running the fixer shows how many annotations it recovers
(recall) and how many of the ones it writes match the original (precision).
"""

from __future__ import annotations

import builtins
import typing
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    FunctionDef,
    Name,
    Subscript,
    Tuple,
    arg,
    expr,
    parse,
    stmt,
    unparse,
    walk,
)
from collections import Counter
from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING, Final, final

from astart import parse as parse_module
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.confidence import Constants as ConfidenceConstants
from astart.rules.hints import HintIndex, LazyHints
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from astart import CommentedModule
    from astart.rules.checker import Checker, MypyChecker, PyrightChecker
    from astart.rules.registry import Registries


@final
@dataclass(frozen=True, slots=True)
class RecoveryScore:
    """Result of recovering the annotations of one module.

    Attributes:
        truth: Annotations the original module had.
        correct: Recovered annotations equal to the original.
        wrong: Keys written with an annotation that contradicts the original.
        missed: Keys the original had that the fixer did not write.
        synthesized: Keys annotated with a synthesized ``Protocol`` or type
            variable; these have no original to match and are judged by the
            external checker, not by this score.
        seconds: Wall-clock time of the fix run.
        rounds: Passes the fix run needed.
        new_errors: New type-checker errors the fixes introduced, or ``None``
            when no checker was asked.
        missed_reasons: Why annotations were missed, as ``(reason, count)``
            pairs sorted by count; empty unless attribution was requested.
        compatible: Keys written with a subtype or supertype of the original
            (see :func:`relation`); neither correct nor wrong.

    """

    truth: int
    correct: int
    wrong: tuple[str, ...]
    missed: tuple[str, ...]
    synthesized: tuple[str, ...]
    seconds: float
    rounds: int = 0
    new_errors: int | None = None
    missed_reasons: tuple[tuple[str, int], ...] = ()
    compatible: tuple[str, ...] = ()

    @property
    def precision(self) -> float:
        """Fraction of written annotations that match the original.

        Returns:
            ``1.0`` when nothing was written.

        """
        written: int = self.correct + len(self.compatible) + len(self.wrong)
        return 1.0 if written == 0 else 1 - len(self.wrong) / written

    @property
    def recall(self) -> float:
        """Fraction of original annotations that were recovered.

        Returns:
            ``1.0`` when the original had no annotations.

        """
        return 1.0 if self.truth == 0 else self.correct / self.truth


def _walk_functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: dict[str, str],
) -> None:
    """Collect annotations keyed by their qualified name.

    Args:
        node: Node whose children are scanned.
        trail: Qualified-name prefix.
        out: Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            if child.returns is not None:
                out[f"{name}->"] = normalize_annotation(
                    text=unparse(ast_obj=child.returns),
                )
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg) and parameter.annotation:
                    out[f"{name}.{parameter.arg}"] = normalize_annotation(
                        text=unparse(ast_obj=parameter.annotation),
                    )
            _walk_functions(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _walk_functions(node=child, trail=(*trail, child.name), out=out)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        aliases: ``typing`` generic names and their builtin spelling.
        unions: ``typing`` constructs that spell a union.

    """

    aliases: Final[dict[str, str]] = {
        "Dict": "dict",
        "FrozenSet": "frozenset",
        "List": "list",
        "Set": "set",
        "Tuple": "tuple",
        "Type": "type",
    }
    unions: Final[frozenset[str]] = frozenset({"Optional", "Union"})


def _base_name(*, node: AST) -> str:
    """Read the last name of ``name`` or ``typing.name``.

    Args:
        node: Name or attribute expression.

    Returns:
        The identifier with ``typing`` generics mapped to builtins.

    """
    name: str = (
        node.id
        if isinstance(node, Name)
        else node.attr
        if isinstance(node, Attribute)
        else unparse(ast_obj=node)
    )
    return Constants.aliases.get(name, name)


def _subscript_members(*, node: Subscript) -> list[str]:
    """Normalize the spelling of a subscripted annotation.

    Args:
        node: A subscript such as ``list[int]`` or ``Optional[int]``.

    Returns:
        The members: the arms of a ``Union``/``Optional``, else one member
        with its arguments normalized.

    """
    head: str = _base_name(node=node.value)
    if isinstance(node.slice, Tuple) and not node.slice.elts:
        return [f"{head}[()]"]
    items: list[expr] = (
        node.slice.elts if isinstance(node.slice, Tuple) else [node.slice]
    )
    if head in Constants.unions:
        found: list[str] = [
            member for item in items for member in _members(node=item)
        ]
        return [*found, "None"] if head == "Optional" else found
    return [f"{head}[{', '.join(_one(node=item) for item in items)}]"]


def _members(*, node: AST) -> list[str]:
    """Flatten a union into its normalized member spellings.

    Args:
        node: Annotation expression.

    Returns:
        The members; a non-union gives a single one.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return [*_members(node=node.left), *_members(node=node.right)]
    if isinstance(node, Subscript):
        return _subscript_members(node=node)
    if isinstance(node, Constant):
        return [
            node.value if isinstance(node.value, str) else repr(node.value),
        ]
    if isinstance(node, (Name, Attribute)):
        return [_base_name(node=node)]
    return [unparse(ast_obj=node)]


def _one(*, node: AST) -> str:
    """Normalize one annotation expression.

    Args:
        node: Annotation expression.

    Returns:
        Its members de-duplicated and sorted, ``None`` last, joined by `` | ``.

    """
    unique: list[str] = sorted(
        set(_members(node=node)),
        key=lambda item: (item == "None", item),
    )
    return " | ".join(unique)


def normalize_annotation(*, text: str) -> str:
    """Spell an annotation canonically so equivalent forms compare equal.

    ``Optional[X]``, ``Union[A, B]`` and ``A | B`` agree, ``typing`` generics
    map to the builtin ones, quotes around a forward reference are dropped
    and union members are ordered.

    Args:
        text: Annotation source.

    Returns:
        The canonical spelling.

    """
    return _one(node=parse(source=text, mode="eval").body)


def _arms(*, text: str) -> set[str]:
    """Split an annotation at its top-level ``|`` and drop module prefixes.

    Args:
        text: Annotation source.

    Returns:
        The arms; ``te.NoReturn`` and ``typing.NoReturn`` both read
        ``NoReturn``.

    """
    arms: list[str] = []
    depth: int = 0
    start: int = 0
    for index, char in enumerate(iterable=text):
        depth += (char == "[") - (char == "]")
        if char == "|" and depth == 0:
            arms.append(text[start:index].strip())
            start = index + 1
    arms.append(text[start:].strip())
    found: set[str] = set()
    for arm in arms:
        found.add(
            arm.rsplit(sep=".", maxsplit=1)[-1] if "[" not in arm else arm,
        )
    return found


def _tower(*, arms: set[str]) -> set[str]:
    """Add the types the numeric tower lets an annotation accept.

    Args:
        arms: Annotation arms.

    Returns:
        The arms plus ``int`` and ``bool`` under ``float``, ``bool`` under
        ``int``.

    """
    widened: set[str] = set(arms)
    if "float" in arms:
        widened |= {"int", "bool"}
    if "int" in arms:
        widened.add("bool")
    return widened


@final
@dataclass(frozen=True, slots=True)
class Context:
    """What the original module defines, for judging its annotations.

    Attributes:
        aliases: Module-level type aliases by name, as annotation source.
        typevars: Names bound to ``TypeVar(...)`` in the module.
        bases: Base-class names of each class the module defines.
        classes: Names of the classes the module defines.

    """

    aliases: Mapping[str, str] = field(default_factory=dict[str, str])
    classes: frozenset[str] = frozenset()
    typevars: frozenset[str] = frozenset()
    bases: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict[str, tuple[str, ...]],
    )


def module_context(*, source: str) -> Context:
    """Collect the aliases and classes a module defines at top level.

    Args:
        source: Original module text.

    Returns:
        Its :class:`Context`.

    """
    aliases: dict[str, str] = {}
    classes: set[str] = set()
    typevars: set[str] = set()
    bases: dict[str, tuple[str, ...]] = {}
    for node in parse(source=source).body:
        match node:
            case ClassDef(name=name):
                classes.add(name)
                bases[name] = tuple(
                    unparse(ast_obj=base).partition("[")[0]
                    for base in node.bases
                )
            case Assign(
                targets=[Name(id=name)],
                value=Call(func=Name(id="TypeVar")),
            ):
                typevars.add(name)
            case Assign(targets=[Name(id=name)], value=BinOp() | Subscript()):
                aliases[name] = unparse(ast_obj=node.value)
            case AnnAssign(target=Name(id=name), value=BinOp() | Subscript()):
                if node.value is not None:
                    aliases[name] = unparse(ast_obj=node.value)
            case _:
                continue
    return Context(
        aliases=aliases,
        classes=frozenset(classes),
        typevars=frozenset(typevars),
        bases=bases,
    )


def _expand(*, arms: set[str], context: Context, depth: int = 3) -> set[str]:
    """Replace alias names by the arms they stand for.

    Args:
        arms: Annotation arms.
        context: The original module's aliases.
        depth: How many alias levels to unfold.

    Returns:
        The arms with aliases resolved.

    """
    if depth == 0:
        return arms
    out: set[str] = set()
    for arm in arms:
        target: str | None = context.aliases.get(arm)
        if target is None:
            out.add(arm)
        else:
            try:
                inner: set[str] = _arms(text=normalize_annotation(text=target))
            except SyntaxError:
                out.add(arm)
            else:
                out |= _expand(arms=inner, context=context, depth=depth - 1)
    return out


@final
class Hierarchy:
    """The ``collections.abc`` ancestry of the builtin containers.

    Attributes:
        ancestors: Abstract bases of each builtin container.
        covariant: Abstract bases whose element argument may be narrower.
        pairs: Abstract bases whose first argument is invariant and whose
            second may be narrower.
        pair_size: Number of arguments of such a base.

    """

    ancestors: Final[dict[str, frozenset[str]]] = {
        "list": frozenset(
            {
                "MutableSequence",
                "Sequence",
                "Collection",
                "Iterable",
                "Reversible",
            },
        ),
        "tuple": frozenset(
            {"Sequence", "Collection", "Iterable", "Reversible"},
        ),
        "set": frozenset(
            {"MutableSet", "Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "frozenset": frozenset(
            {"Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "dict": frozenset(
            {"MutableMapping", "Mapping", "Collection", "Iterable"},
        ),
    }
    covariant: Final[frozenset[str]] = frozenset(
        {
            "Sequence",
            "Collection",
            "Iterable",
            "Reversible",
            "Set",
            "AbstractSet",
            "Iterator",
        },
    )
    pairs: Final[frozenset[str]] = frozenset({"Mapping"})
    pair_size: Final[int] = 2


def _generic(*, arm: str) -> tuple[str, list[str]] | None:
    """Split ``origin[a, b]`` into its origin and argument texts.

    Args:
        arm: One annotation arm.

    Returns:
        The origin and arguments, or ``None`` when the arm is not a
        subscript.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, Subscript):
        return None
    inner: expr = node.slice
    parts: list[expr] = inner.elts if isinstance(inner, Tuple) else [inner]
    return unparse(ast_obj=node.value), [
        unparse(ast_obj=part) for part in parts
    ]


def _argument_fits(*, small: str, big: str, known: Context) -> bool:
    """Tell whether one type argument fits a covariant position.

    Args:
        small: Argument of the narrower container.
        big: Argument of the wider container.
        known: What the original module defines.

    Returns:
        ``True`` when equal, when the wider one is a type variable of the
        module, or when ``small`` is within ``big``.

    """
    return (
        small == big
        or big in known.typevars
        or _within(
            small=_arms(text=small),
            big=_arms(text=big),
            known=known,
        )
    )


def _container_within(*, small: str, big: str, known: Context) -> bool:
    """Tell whether a builtin container arm fits an abstract container arm.

    Args:
        small: A narrower arm such as ``list[int]``.
        big: A wider arm such as ``Sequence[int]``.
        known: What the original module defines.

    Returns:
        ``True`` when ``small``'s origin derives from ``big``'s and the
        arguments fit with the right variance (invariant positions must be
        equal).

    """
    mine: tuple[str, list[str]] | None = _generic(arm=small)
    theirs: tuple[str, list[str]] | None = _generic(arm=big)
    if mine is None or theirs is None:
        return False
    origin, args = mine
    base, wide = theirs
    if base not in Hierarchy.ancestors.get(origin, frozenset()):
        return False
    if base in Hierarchy.covariant:
        elements: list[str] = [
            item for item in args if item not in {"...", "Ellipsis"}
        ]
        return (
            len(wide) == 1
            and bool(elements)
            and all(
                _argument_fits(small=item, big=wide[0], known=known)
                for item in elements
            )
        )
    if base in Hierarchy.pairs:
        return (
            len(args) == len(wide) == Hierarchy.pair_size
            and args[0] == wide[0]
            and _argument_fits(small=args[1], big=wide[1], known=known)
        )
    return args == wide


def _within(
    *,
    small: set[str],
    big: set[str],
    known: Context | None = None,
) -> bool:
    """Tell whether every arm of ``small`` fits inside ``big``.

    Args:
        small: Arms of the narrower candidate.
        big: Arms of the wider candidate.
        known: What the original module defines, for its type variables.

    Returns:
        ``True`` when each arm is in ``big`` (numeric tower included), is
        a ``Literal`` of a scalar type that ``big`` accepts, or is a builtin
        container that fits an abstract one in ``big``.

    """
    roof: set[str] = _tower(arms=big)
    context: Context = Context() if known is None else known
    return "object" in big or all(
        arm in roof
        or (
            arm.startswith("Literal[")
            and bool(roof & {"str", "int", "bytes", "bool"})
        )
        or (arm.startswith(("TypeGuard[", "TypeIs[")) and "bool" in roof)
        or any(
            _container_within(small=arm, big=wider, known=context)
            for wider in big
        )
        for arm in small
    )


def _foreign_ancestry(*, arm: str, known: Context) -> bool:
    """Tell whether a module class derives from something defined elsewhere.

    Such a class may be a subtype of the original annotation through a base
    this module does not show, so the scorer cannot call it a contradiction.

    Args:
        arm: One arm of what the fixer wrote.
        known: What the original module defines.

    Returns:
        ``True`` when the arm names something the module does not define
        (an import) or a class of the module with a base that is neither a
        class of the module nor a builtin; the caller only asks when the
        original names abstract ``typing`` types.

    """
    head: str = arm.partition("[")[0]
    if head not in known.classes:
        return not (hasattr(builtins, head) or hasattr(typing, head))
    pending: list[str] = [head]
    seen: set[str] = set()
    while pending:
        name: str = pending.pop()
        if name in seen or name not in known.classes:
            continue
        seen.add(name)
        for base in known.bases.get(name, ()):
            if base in known.classes:
                pending.append(base)
            elif not hasattr(builtins, base) and not hasattr(typing, base):
                return True
    return False


def _resolvable(*, arm: str, known: Context) -> bool:
    """Tell whether an arm names something this module can account for.

    Args:
        arm: One arm of an annotation.
        known: What the original module defines.

    Returns:
        ``True`` for builtins, ``typing`` names, classes of the module and
        subscripts of those; ``False`` for names imported from elsewhere.

    """
    base: str = arm.split(sep="[", maxsplit=1)[0]
    return (
        base in known.classes
        or hasattr(builtins, base)
        or hasattr(typing, base)
        or hasattr(typing, base)
    )


def relation(
    *,
    written: str,
    truth: str,
    context: Context | None = None,
) -> str | None:
    """Say how a written annotation relates to the original one.

    Args:
        written: What the fixer wrote.
        truth: The original annotation.
        context: Aliases and classes of the original module, if known.

    Returns:
        ``None`` when they mean the same, ``"narrower"`` when the written type
        is a subtype of the original, ``"looser"`` when it is a supertype,
        ``"unresolved"`` when the original names something imported that
        cannot be judged from this module, and ``"contradiction"`` otherwise.
        ``NoReturn`` is the empty type, ``Any`` accepts everything, ``Self``
        is a subtype of its class, and the original module's aliases are
        unfolded.

    """
    known: Context = Context() if context is None else context
    ours: set[str] = _arms(text=normalize_annotation(text=written))
    theirs: set[str] = _arms(text=normalize_annotation(text=truth))
    if ours == theirs:
        return None
    ours = _expand(arms=ours, context=known)
    theirs = _expand(arms=theirs, context=known)
    if "Self" in ours and theirs & known.classes:
        ours = (ours - {"Self"}) | (theirs & known.classes)
        return "narrower"
    if ours == theirs:
        return None
    return _classify(ours=ours, theirs=theirs, known=known)


def _classify(*, ours: set[str], theirs: set[str], known: Context) -> str:
    """Compare two resolved arm sets that are not the same.

    Args:
        ours: Arms of what the fixer wrote.
        theirs: Arms of the original.
        known: What the original module defines.

    Returns:
        ``"narrower"``, ``"looser"``, ``"unresolved"`` or ``"contradiction"``.

    """
    ours_effective: set[str] = ours - {"NoReturn"}
    theirs_effective: set[str] = theirs - {"NoReturn"}
    if "Any" in theirs or _within(
        small=ours_effective,
        big=theirs_effective,
        known=known,
    ):
        return "narrower"
    if "Any" in ours or _within(
        small=theirs_effective,
        big=ours_effective,
        known=known,
    ):
        return "looser"
    if not all(_resolvable(arm=arm, known=known) for arm in theirs_effective):
        return "unresolved"
    if all(
        hasattr(typing, arm.partition("[")[0]) for arm in theirs_effective
    ) and any(
        _foreign_ancestry(arm=arm, known=known) for arm in ours_effective
    ):
        return "unresolved"
    return "contradiction"


def annotation_map(*, source: str) -> dict[str, str]:
    """List the parameter and return annotations of a module.

    Args:
        source: Python source.

    Returns:
        Normalised annotation text by ``function.parameter`` or ``function->``.

    """
    out: dict[str, str] = {}
    _walk_functions(node=parse(source=source), trail=(), out=out)
    return out


def _walk_variables(
    *,
    body: Sequence[stmt],
    trail: tuple[str, ...],
    out: dict[str, str],
) -> None:
    """Collect annotated variables keyed by their scope.

    Args:
        body: Statements of one scope.
        trail: Qualified-name prefix.
        out: Destination mapping, extended in place.

    """
    for node in body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            _walk_variables(
                body=node.body,
                trail=(*trail, node.name),
                out=out,
            )
            continue
        if isinstance(node, AnnAssign) and isinstance(node.target, Name):
            out[".".join((*trail, node.target.id))] = normalize_annotation(
                text=unparse(ast_obj=node.annotation),
            )
        for branch in ("body", "orelse", "finalbody"):
            inner: Sequence[stmt] | None = getattr(node, branch, None)
            if isinstance(inner, list):
                _walk_variables(body=inner, trail=trail, out=out)


def variable_map(*, source: str) -> dict[str, str]:
    """List the annotated variables of a module.

    Args:
        source: Python source.

    Returns:
        Normalised annotation by ``scope.name``.

    """
    found: dict[str, str] = {}
    _walk_variables(body=parse(source=source).body, trail=(), out=found)
    return found


def strip_annotations(*, source: str) -> str:
    """Remove every parameter and return annotation from a module.

    Args:
        source: Python source.

    Returns:
        The module re-rendered without those annotations (formatting and
        comments are not kept; this is benchmark input only).

    """
    tree: AST = parse(source=source)
    for node in walk(node=tree):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            node.returns = None
        elif isinstance(node, arg):
            node.annotation = None
    return unparse(ast_obj=tree) + "\n"


def _invented_names(*, source: str) -> set[str]:
    """List the module-level names that are protocols or type variables.

    Args:
        source: Python source.

    Returns:
        Names of classes deriving from ``Protocol`` and of ``TypeVar``
        assignments.

    """
    names: set[str] = set()
    for node in parse(source=source).body:
        if isinstance(node, ClassDef) and any(
            unparse(ast_obj=base).split(sep=".")[-1] == "Protocol"
            for base in node.bases
        ):
            names.add(node.name)
        elif (
            isinstance(node, Assign)
            and isinstance(node.value, Call)
            and unparse(ast_obj=node.value.func).split(sep=".")[-1]
            == "TypeVar"
        ):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, Name)
            )
    return names


def _targets(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: dict[str, AST],
) -> None:
    """Index functions and parameters by their qualified key.

    Args:
        node: Node whose children are scanned.
        trail: Qualified-name prefix.
        out: Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            out[f"{name}->"] = child
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg):
                    out[f"{name}.{parameter.arg}"] = parameter
            _targets(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _targets(node=child, trail=(*trail, child.name), out=out)


def attribute_misses(
    *,
    source: str,
    missed: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    """Say why the fixer left annotations out.

    Args:
        source: The module after fixing.
        missed: Keys the original annotated and the fixer did not.

    Returns:
        ``(reason, count)`` pairs, most frequent first. The reason is the
        hint index's refusal (taint details dropped), or ``not judged`` for
        subjects the index never considered (receivers, variadics).

    """
    module: CommentedModule = parse_module(source=source, filename="miss.py")
    index: HintIndex = LazyHints(
        module=module,
        stubs_path=None,
        source=source,
        cache=None,
    ).index()
    nodes: dict[str, AST] = {}
    _targets(node=module, trail=(), out=nodes)
    counts: Counter[str] = Counter()
    for key in missed:
        node: AST | None = nodes.get(key)
        reason: str | None = (
            None
            if node is None
            else index.rejection_for(
                node=node,
            )
        )
        counts[
            "not judged"
            if reason is None
            else str(object=reason).split(sep=" by parameter")[0]
        ] += 1
    return tuple(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


@final
@dataclass(frozen=True, slots=True)
class RecoveryOptions:
    """Choices of one recovery run.

    Attributes:
        ceiling: Highest fix safety to apply.
        checker: External checker gate, or ``None``.
        attribute: Whether to explain the missed annotations (costs one more
            inference run).
        delta: A checker used to count the new errors the fixes introduce
            (two checker runs per module).
        min_confidence: Least confidence a fix needs, as in the CLI.
        negotiate: Whether negotiated hints supplement the hint index.
        annotate_variables: Whether local variables are annotated.
        engine: Conversion mode (the engine's own annotations).

    """

    ceiling: FixSafety = FixSafety.guarded
    checker: Checker | None = None
    attribute: bool = False
    delta: PyrightChecker | MypyChecker | None = None
    min_confidence: float = ConfidenceConstants.default_minimum
    negotiate: bool = True
    annotate_variables: bool = False
    engine: bool = False


def recover(
    *,
    source: str,
    filename: str,
    options: RecoveryOptions | None = None,
) -> RecoveryScore:
    """Strip a typed module, fix it, and score the recovered annotations.

    Args:
        source: Python source of a well-typed module.
        filename: Name used for the fix run.
        options: Ceiling, checker gate, attribution and delta; defaults to
            the guarded ceiling with nothing else.

    Returns:
        Precision and recall counts against the original annotations.

    """
    chosen: RecoveryOptions = options or RecoveryOptions()
    truth: dict[str, str] = annotation_map(source=source)
    registries: Registries = default_registries()
    stripped: str = strip_annotations(source=source)
    started: float = perf_counter()
    result: FixResult = fix_source(
        source=stripped,
        filename=filename,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=chosen.ceiling,
            checker=chosen.checker,
            min_confidence=chosen.min_confidence,
            negotiate=chosen.negotiate,
            annotate_variables=chosen.annotate_variables,
            engine=chosen.engine,
        ),
    )
    seconds: float = perf_counter() - started
    written: dict[str, str] = annotation_map(source=result.source)
    invented: set[str] = _invented_names(source=result.source)
    synthesized: tuple[str, ...] = tuple(
        sorted(
            key
            for key, text in written.items()
            if key not in truth
            or any(
                isinstance(node, Name) and node.id in invented
                for node in walk(node=parse(source=text, mode="eval"))
            )
        ),
    )
    judged: dict[str, str] = {
        key: text for key, text in written.items() if key not in synthesized
    }
    correct: int = sum(
        1 for key, text in judged.items() if truth.get(key) == text
    )
    known: Context = module_context(source=source)
    differing: dict[str, str] = {
        key: kind
        for key, text in judged.items()
        if key in truth
        and truth[key] != text
        and (
            kind := relation(
                written=text,
                truth=truth[key],
                context=known,
            )
        )
        is not None
    }
    wrong: tuple[str, ...] = tuple(
        sorted(
            f"{key}: wrote {judged[key]!r}, expected {truth[key]!r}"
            for key, kind in differing.items()
            if kind == "contradiction"
        ),
    )
    compatible: tuple[str, ...] = tuple(
        sorted(
            f"{key}: wrote {judged[key]!r} ({kind}), expected {truth[key]!r}"
            for key, kind in differing.items()
            if kind != "contradiction"
        ),
    )
    missed: tuple[str, ...] = tuple(
        sorted(key for key in truth if key not in written),
    )
    return RecoveryScore(
        truth=len(truth),
        correct=correct,
        wrong=wrong,
        compatible=compatible,
        missed=missed,
        synthesized=synthesized,
        seconds=seconds,
        rounds=result.rounds,
        new_errors=(
            None
            if chosen.delta is None
            else chosen.delta.new_errors(
                filename=filename,
                before=stripped,
                after=result.source,
            )
        ),
        missed_reasons=(
            attribute_misses(source=result.source, missed=missed)
            if chosen.attribute
            else ()
        ),
    )
