"""Annotation-recovery benchmark: strip a typed module, fix it, compare.

Well-typed code is the ground truth. Removing its parameter and return
annotations and running the fixer shows how many annotations it recovers
(recall) and how many of the ones it writes match the original (precision).
"""

from __future__ import annotations

from ast import (
    AST,
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
    unparse,
    walk,
)
from collections import Counter
from dataclasses import dataclass
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
from astart.rules.hints import HintIndex, LazyHints
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Sequence

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
        wrong: Keys written with a different annotation than the original.
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

    @property
    def precision(self) -> float:
        """Fraction of written annotations that match the original.

        Returns:
            ``1.0`` when nothing was written.

        """
        written: int = self.correct + len(self.wrong)
        return 1.0 if written == 0 else self.correct / written

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
        head: str = _base_name(node=node.value)
        if head in Constants.unions:
            items: list[expr] = (
                node.slice.elts
                if isinstance(node.slice, Tuple)
                else [node.slice]
            )
            found: list[str] = [
                member for item in items for member in _members(node=item)
            ]
            return [*found, "None"] if head == "Optional" else found
        inner: list[expr] = (
            node.slice.elts if isinstance(node.slice, Tuple) else [node.slice]
        )
        return [f"{head}[{', '.join(_one(node=item) for item in inner)}]"]
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

    """

    ceiling: FixSafety = FixSafety.guarded
    checker: Checker | None = None
    attribute: bool = False
    delta: PyrightChecker | MypyChecker | None = None


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
    wrong: tuple[str, ...] = tuple(
        sorted(
            f"{key}: wrote {text!r}, expected {truth[key]!r}"
            for key, text in judged.items()
            if key in truth and truth[key] != text
        ),
    )
    missed: tuple[str, ...] = tuple(
        sorted(key for key in truth if key not in written),
    )
    return RecoveryScore(
        truth=len(truth),
        correct=correct,
        wrong=wrong,
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
