"""Convert an untyped module with astart and report how it differs, in meaning.

Usage (from the repository root)::

    python scripts/conversion_report.py
    python scripts/conversion_report.py --min-confidence 0.5 \
        --ledger "after G-02"
    python scripts/conversion_report.py --checker --no-opacity

Runs ``astart fix`` in conversion mode on ``dev/untyped.py`` in memory (the
file is never modified), compares every annotation of the result with
``dev/typed.py`` by meaning, not by text, and writes:

* ``docs/conversion-report.md``   the full report,
* ``docs/conversion-report.json`` the same data for tools,
* the ``conversion`` block of ``docs/TODO.md`` (summary and gap by family).
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    Call,
    ClassDef,
    Constant,
    Expression,
    FunctionDef,
    Name,
    TypeAlias,
    arg,
    expr,
    parse,
    walk,
)
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
from importlib import import_module
from json import dumps
from os.path import relpath
from pathlib import Path
from subprocess import run
from sys import executable, path, stdout
from time import perf_counter
from typing import TYPE_CHECKING, Final, Protocol, cast, final

if TYPE_CHECKING:
    from collections.abc import Iterable
    from subprocess import CompletedProcess
    from types import ModuleType

    from astart.rules.checker import Checker
    from astart.rules.recovery import Context
    from astart.rules.registry import Registries

    from scripts.evidence import Evidence, Index
    from scripts.opacity_report import Row, Section


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root: Repository root.
        scopes: Result scope key and its label.
        verdicts: Outcome names in display order.
        compatible: Outcomes that are valid but not identical.
        gap: Outcomes that count as the remaining gap.
        scalars: Scalar type names.
        containers: Builtin container names.
        iterators: Generator and iterator names.
        abstract: Abstract collection names.
        typevar_makers: Calls that create type variables.
        families: Annotation families in display order.
        hard: Families that are partly author choices.
        tasks: TODO tasks that close the gap of each family.
        bar_width: Width of a bar in characters.
        owner_rows: Owners listed in the report.
        list_limit: Missing keys listed per family in the full report.
        opacity_lines: Lines of the opacity report embedded in the report.
        max_typevar_len: Longest uppercase name treated as an inline TypeVar.
        wrong_listed: Wrong annotations listed in the TODO block.
        snippet_len: Characters of a source line kept in a diff snippet.

    """

    root: Final[Path] = Path(__file__).resolve().parent.parent
    scopes: Final[tuple[tuple[str, str], ...]] = (
        ("parameters_and_returns", "Parameters and returns"),
        ("variables", "Variables"),
    )
    verdicts: Final[tuple[str, ...]] = (
        "exact",
        "narrower",
        "looser",
        "compatible",
        "unresolved",
        "wrong",
        "missing",
    )
    compatible: Final[frozenset[str]] = frozenset(
        {"narrower", "looser", "compatible"},
    )
    gap: Final[frozenset[str]] = frozenset({"missing", "wrong", "unresolved"})
    scalars: Final[frozenset[str]] = frozenset(
        {"int", "str", "float", "bool", "bytes", "complex"},
    )
    containers: Final[frozenset[str]] = frozenset(
        {"list", "dict", "set", "tuple", "frozenset"},
    )
    iterators: Final[frozenset[str]] = frozenset(
        {
            "Generator",
            "AsyncGenerator",
            "Iterator",
            "AsyncIterator",
            "Iterable",
            "AsyncIterable",
        },
    )
    abstract: Final[frozenset[str]] = frozenset(
        {
            "Sequence",
            "Mapping",
            "MutableMapping",
            "MutableSequence",
            "MutableSet",
            "AbstractSet",
            "Collection",
            "Set",
        },
    )
    typevar_makers: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple"},
    )
    families: Final[tuple[str, ...]] = (
        "Scalar",
        "Builtin container",
        "Optional",
        "Union",
        "Module class",
        "Library class",
        "Type alias",
        "Abstract collection",
        "Generator/Iterator",
        "Callable",
        "TypeVar",
        "Self",
        "ClassVar/Final",
        "Top type (object)",
        "Other",
    )
    hard: Final[frozenset[str]] = frozenset(
        {
            "Abstract collection",
            "Generator/Iterator",
            "Callable",
            "TypeVar",
            "Self",
            "ClassVar/Final",
            "Top type (object)",
            "Type alias",
        },
    )
    tasks: Final[dict[str, str]] = {
        "Scalar": "W-06, W-08, I-10, F-37",
        "Builtin container": "I-05, I-09, I-17, F-40, AL-07",
        "Optional": "I-01, I-08, AL-01",
        "Union": "AL-05, I-19",
        "Module class": "M2-02, W-12, I-11, W-14",
        "Library class": "I-21, I-08, T-08",
        "Type alias": "S-03, AL-14 (author-defined names)",
        "Abstract collection": "M4-16, AL-13, G-02",
        "Generator/Iterator": "W-13, G-05",
        "Callable": "M4-17, M5-19",
        "TypeVar": "M5-16, I-18, M5-19",
        "Self": "W-11, AF-02, F-43",
        "ClassVar/Final": "AF-05, G-06",
        "Top type (object)": (
            "policy: astart never writes object; G-02 scores narrower"
        ),
        "Other": "G-04",
    }
    bar_width: Final[int] = 20
    owner_rows: Final[int] = 15
    list_limit: Final[int] = 30
    opacity_lines: Final[int] = 60
    max_typevar_len: Final[int] = 2
    wrong_listed: Final[int] = 10
    snippet_len: Final[int] = 200


@final
@dataclass(frozen=True, slots=True)
class Item:
    """One annotation of the typed file and what happened to it.

    Attributes:
        scope: ``parameters_and_returns`` or ``variables``.
        key: Node path such as ``Class.method.param`` or ``function->``.
        verdict: Outcome name.
        written: What astart wrote, or ``None`` when nothing was written.
        author: What the typed file has.
        family: Shape of the author's annotation.
        typed_line: Line of the annotation in the typed file.
        converted_line: Line of the node in the converted output.
        untyped_line: Line of the node in the untyped input.

    """

    scope: str
    key: str
    verdict: str
    written: str | None
    author: str
    family: str
    typed_line: int | None = None
    converted_line: int | None = None
    untyped_line: int | None = None


def bar(*, value: int, total: int) -> str:
    """Draw a progress bar.

    Args:
        value: Amount done.
        total: Amount that means 100 %.

    Returns:
        A bar of ``Constants.bar_width`` characters.

    """
    width: int = Constants.bar_width
    if total <= 0:
        return "░" * width
    filled: int = max(0, min(width, round(number=width * value / total)))
    return "█" * filled + "░" * (width - filled)


def percent(*, value: int, total: int) -> str:
    """Format a share as a percentage.

    Args:
        value: Part.
        total: Whole.

    Returns:
        For example ``"45.9 %"``.

    """
    return "n/a" if total <= 0 else f"{100 * value / total:.1f} %"


class _Digest(Protocol):
    """The slice of a hash object ``tree_hash`` uses."""

    def update(self, data: bytes, /) -> None:
        """Add bytes to the hash.

        Args:
            data: Bytes to add.

        """
        ...

    def hexdigest(self) -> str:
        """Render the hash as hexadecimal text.

        Returns:
            The lowercase hex digest.

        """
        ...


def tree_hash(*, root: Path) -> str:
    """Hash the astart source tree, to stamp the report.

    Args:
        root: Repository root.

    Returns:
        The first 12 hex digits of a SHA-256 over all source files.

    """
    digest: _Digest = sha256()
    for file in sorted((root / "src" / "astart").rglob(pattern="*.py")):
        if "__pycache__" in file.parts:
            continue
        digest.update(file.relative_to(root).as_posix().encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()[:12]


def module_names(
    *,
    source: str,
) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    """Collect class, type-variable and type-alias names of the typed module.

    Args:
        source: Source of the typed module.

    Returns:
        The class names, the type-variable names and the type-alias names.

    """
    classes: set[str] = set()
    typevars: set[str] = set()
    aliases: set[str] = set()
    for node in walk(node=parse(source=source)):
        if isinstance(node, ClassDef):
            classes.add(node.name)
        if isinstance(node, TypeAlias):
            aliases.add(node.name.id)
        if isinstance(node, Assign) and isinstance(node.value, Call):
            func: expr = node.value.func
            if isinstance(func, Name) and func.id in Constants.typevar_makers:
                typevars.update(
                    target.id
                    for target in node.targets
                    if isinstance(target, Name)
                )
        typevars.update(
            param.name for param in getattr(node, "type_params", ())
        )
    return frozenset(classes), frozenset(typevars), frozenset(aliases)


def family_of(
    *,
    text: str,
    classes: frozenset[str],
    typevars: frozenset[str],
    aliases: frozenset[str],
) -> str:
    """Classify an annotation by its shape.

    Args:
        text: Annotation source.
        classes: Class names defined in the typed module.
        typevars: Type-variable names defined in the typed module.
        aliases: Type-alias names defined in the typed module.

    Returns:
        One of ``Constants.families``.

    """
    try:
        tree: Expression = parse(source=text, mode="eval")
    except SyntaxError:
        return "Other"
    if isinstance(tree.body, Constant) and tree.body.value is None:
        return "Scalar"
    names: set[str] = set()
    has_union: bool = False
    has_none: bool = False
    for node in walk(node=tree):
        if isinstance(node, Name):
            names.add(node.id)
        elif isinstance(node, Attribute):
            names.add(node.attr)
        elif isinstance(node, BinOp):
            has_union = True
            has_none = has_none or any(
                isinstance(side, Constant) and side.value is None
                for side in (node.left, node.right)
            )
    short_upper: bool = any(
        len(n) <= Constants.max_typevar_len and n.isupper() for n in names
    )
    known: set[str] = (
        set(Constants.scalars)
        | set(Constants.containers)
        | classes
        | aliases
        | typevars
        | {"None", "type", "object", "Any"}
    )
    ordered: tuple[tuple[str, bool], ...] = (
        ("Self", "Self" in names),
        ("ClassVar/Final", bool(names & {"ClassVar", "Final"})),
        ("Callable", "Callable" in names),
        ("Generator/Iterator", bool(names & Constants.iterators)),
        ("Abstract collection", bool(names & Constants.abstract)),
        (
            "TypeVar",
            bool(names & typevars)
            or short_upper
            or bool(names & {"args", "kwargs"}),
        ),
        ("Top type (object)", bool(names & {"object", "Any"})),
        ("Optional", has_none or "Optional" in names),
        ("Union", has_union or "Union" in names),
        ("Type alias", bool(names & aliases)),
        ("Module class", bool(names & classes)),
        ("Library class", bool(names - known)),
        ("Builtin container", bool(names & Constants.containers)),
        ("Scalar", bool(names & Constants.scalars)),
    )
    for family, matched in ordered:
        if matched:
            return family
    return "Other"


class _Recovery(Protocol):
    """The slice of ``astart.rules.recovery`` the comparison calls."""

    def annotation_map(self, *, source: str) -> dict[str, str]:
        """Map annotation keys to their source text.

        Args:
            source: Module source.

        Returns:
            Annotation key to annotation text.

        """
        ...

    def variable_map(self, *, source: str) -> dict[str, str]:
        """Map variable keys to their annotation text.

        Args:
            source: Module source.

        Returns:
            Variable key to annotation text.

        """
        ...

    def module_context(self, *, source: str) -> Context:
        """Collect the aliases and classes a module defines.

        Args:
            source: Module source.

        Returns:
            Its :class:`Context`.

        """
        ...

    def normalize_annotation(self, *, text: str) -> str:
        """Reduce an annotation to a canonical form.

        Args:
            text: Annotation source.

        Returns:
            The canonical text.

        """
        ...

    def relation(
        self,
        *,
        written: str,
        truth: str,
        context: Context | None = None,
    ) -> str | None:
        """Say how a written annotation relates to the original one.

        Args:
            written: What the fixer wrote.
            truth: The original annotation.
            context: Aliases and classes of the original module.

        Returns:
            The relation name, or ``None`` when they mean the same.

        """
        ...


@final
@dataclass(frozen=True, slots=True)
class Sources:
    """Source lines, line maps and link targets, for snippets and links.

    Attributes:
        untyped: Lines of the untyped input.
        typed: Lines of the typed answer key.
        converted: Lines of the converted output.
        links: Link target per source (``untyped``, ``typed``, ``converted``).
        untyped_params: Lines of the input's parameters and returns.
        untyped_vars: Lines of the input's variables.
        anchors: TODO entry anchor by task ID.
        evidence: Evidence index of the untyped module.
        reasons: Opacity reason and evidence by node path.

    """

    untyped: list[str]
    typed: list[str]
    converted: list[str]
    links: dict[str, str]
    untyped_params: dict[str, int]
    untyped_vars: dict[str, int]
    anchors: dict[str, str]
    evidence: Index | None
    reasons: dict[str, tuple[str, str]]


@final
@dataclass(frozen=True, slots=True)
class Extras:
    """Optional report content beyond the scored items.

    Attributes:
        sections: Opacity sections (may be empty).
        sources: Source lines, line maps and link targets.
        examples: Code examples shown per family of missing annotations.

    """

    sections: list[Section]
    sources: Sources
    examples: int


def todo_anchors(*, todo: Path) -> dict[str, str]:
    """Compute the GitHub anchor of every task heading of the TODO file.

    Args:
        todo: Path of the TODO file.

    Returns:
        Anchor by task ID; empty when the file does not exist.

    """
    if not todo.exists():
        return {}
    anchors: dict[str, str] = {}
    seen: Counter[str] = Counter()
    fenced: bool = False
    for line in todo.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            fenced = not fenced
        if fenced or not line.startswith("#"):
            continue
        heading: str = line.lstrip("#").strip()
        base: str = "".join(
            char for char in heading.lower() if char.isalnum() or char in " -_"
        ).replace(" ", "-")
        anchor: str = base if seen[base] == 0 else f"{base}-{seen[base]}"
        seen[base] += 1
        if line.startswith("### ") and " — " in line:
            anchors.setdefault(heading.partition(" — ")[0], anchor)
    return anchors


def task_links(*, text: str, anchors: dict[str, str]) -> str:
    """Turn task IDs in a text into links to their TODO entries.

    Args:
        text: Text such as ``"W-06, W-08 (author names)"``.
        anchors: Anchor by task ID.

    Returns:
        The text with each known ID linked.

    """
    words: list[str] = []
    for word in text.split(sep=" "):
        core: str = word.strip(",;()")
        if core in anchors:
            words.append(
                word.replace(core, f"[{core}](TODO.md#{anchors[core]})"),
            )
        else:
            words.append(word)
    return " ".join(words)


def cell(*, text: str) -> str:
    """Make text safe inside a Markdown table cell.

    Args:
        text: Any text.

    Returns:
        The text with pipes escaped and backticks replaced.

    """
    return text.replace("|", "\\|").replace("`", "'")


def node_line(*, key: str, sources: Sources) -> int | None:
    """Find the line of a node in the untyped input.

    Args:
        key: Node path such as ``Class.method.param`` or ``function->``.
        sources: Source lines and line maps.

    Returns:
        The line number, or ``None``.

    """
    return sources.untyped_params.get(key) or sources.untyped_vars.get(key)


def _functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: dict[str, int],
) -> None:
    """Record the line of every parameter and return, like the scorer's keys.

    Args:
        node: Node whose body is scanned.
        trail: Qualified-name prefix.
        out: Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            out[f"{name}->"] = (child.returns or child).lineno
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg):
                    out[f"{name}.{parameter.arg}"] = parameter.lineno
            _functions(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _functions(node=child, trail=(*trail, child.name), out=out)


def param_lines(*, source: str) -> dict[str, int]:
    """Locate parameters and returns by the scorer's keys.

    Args:
        source: Python source.

    Returns:
        Line number by ``function.parameter`` or ``function->``; a return
        without annotation points at its ``def`` line.

    """
    out: dict[str, int] = {}
    _functions(node=parse(source=source), trail=(), out=out)
    return out


def _variables(
    *,
    body: Iterable[AST],
    trail: tuple[str, ...],
    annotated: dict[str, int],
    plain: dict[str, int],
) -> None:
    """Record the line of every annotated or plainly assigned variable.

    Args:
        body: Statements of one scope.
        trail: Qualified-name prefix.
        annotated: Lines of annotated assignments (last one wins).
        plain: Lines of the first plain assignment.

    """
    for node in body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            _variables(
                body=node.body,
                trail=(*trail, node.name),
                annotated=annotated,
                plain=plain,
            )
            continue
        if isinstance(node, AnnAssign) and isinstance(node.target, Name):
            annotated[".".join((*trail, node.target.id))] = node.lineno
        if isinstance(node, Assign):
            for target in node.targets:
                if isinstance(target, Name):
                    plain.setdefault(
                        ".".join((*trail, target.id)),
                        node.lineno,
                    )
        for branch in ("body", "orelse", "finalbody"):
            inner: list[AST] | None = cast(
                typ="list[AST] | None",
                val=getattr(node, branch, None),
            )
            if inner is not None:
                _variables(
                    body=inner,
                    trail=trail,
                    annotated=annotated,
                    plain=plain,
                )


def variable_lines(*, source: str) -> dict[str, int]:
    """Locate variables by the scorer's keys.

    Args:
        source: Python source.

    Returns:
        Line number by ``scope.name``: the annotated statement when there is
        one, else the first plain assignment.

    """
    annotated: dict[str, int] = {}
    plain: dict[str, int] = {}
    _variables(
        body=list(parse(source=source).body),
        trail=(),
        annotated=annotated,
        plain=plain,
    )
    return {**plain, **annotated}


def line_text(*, lines: list[str], number: int | None) -> str | None:
    """Read one source line for a snippet.

    Args:
        lines: Source lines.
        number: 1-based line number.

    Returns:
        The line without trailing blanks, shortened to 200 characters, with
        code-fence marks defused; ``None`` when the line is unknown.

    """
    if number is None or not 1 <= number <= len(lines):
        return None
    text: str = lines[number - 1].rstrip().replace("```", "'''")
    if len(text) <= Constants.snippet_len:
        return text
    return text[: Constants.snippet_len] + "…"


def link(*, label: str, target: str, number: int | None) -> str:
    """Build a Markdown link to a line.

    Args:
        label: File label.
        target: Relative path of the file.
        number: 1-based line number.

    Returns:
        ``[label:number](target#Lnumber)``, or ``n/a`` without a line.

    """
    if number is None:
        return "n/a"
    return f"[{label}:{number}]({target}#L{number})"


def snippet(*, item: Item, sources: Sources) -> list[str]:
    """Show an annotation as a diff: how it is against how it should be.

    Args:
        item: A scored annotation.
        sources: Source lines and link targets.

    Returns:
        Markdown lines: a line of links and a ``diff`` block whose ``-`` line
        is the converted code and whose ``+`` line is the typed code.

    """
    how: str | None = line_text(
        lines=sources.converted,
        number=item.converted_line,
    )
    should: str | None = line_text(lines=sources.typed, number=item.typed_line)
    out_link: str = link(
        label="conversion-output.py.txt",
        target=sources.links["converted"],
        number=item.converted_line,
    )
    typed_link: str = link(
        label="typed.py",
        target=sources.links["typed"],
        number=item.typed_line,
    )
    input_link: str = link(
        label="untyped.py",
        target=sources.links["untyped"],
        number=item.untyped_line,
    )
    lines: list[str] = [
        f"how it is {out_link} · should be {typed_link} · input {input_link}",
        "",
        "```diff",
        f"@@ {item.key} · {item.verdict} · {item.family} @@",
    ]
    if how is not None:
        lines.append(f"-{how}")
    if should is not None:
        lines.append(f"+{should}")
    lines.append("```")
    return lines


def _typed_link(*, item: Item, sources: Sources) -> str:
    """Link an item to its line in the typed file.

    Args:
        item: Scored annotation.
        sources: Source lines and link targets.

    Returns:
        A Markdown link labelled ``typed.py``.

    """
    return link(
        label="typed.py",
        target=sources.links["typed"],
        number=item.typed_line,
    )


def compare(
    *,
    untyped: str,
    typed: str,
    converted: str,
    recovery: _Recovery,
) -> tuple[list[Item], dict[str, int]]:
    """Score every annotation of the typed file against the converted module.

    Args:
        untyped: Source without annotations.
        typed: Source with the author's annotations.
        converted: What astart produced from the untyped source.
        recovery: The ``astart.rules.recovery`` module.

    Returns:
        One item per annotation to recover, and the count of annotations
        written that the typed file does not have, by scope.

    """
    truth: dict[str, str] = recovery.annotation_map(source=typed)
    start: dict[str, str] = recovery.annotation_map(source=untyped)
    written: dict[str, str] = recovery.annotation_map(source=converted)
    truth_vars: dict[str, str] = recovery.variable_map(source=typed)
    done_vars: dict[str, str] = recovery.variable_map(source=converted)
    context: Context = recovery.module_context(source=typed)
    classes, typevars, aliases = module_names(source=typed)
    typed_params: dict[str, int] = param_lines(source=typed)
    converted_params: dict[str, int] = param_lines(source=converted)
    untyped_params: dict[str, int] = param_lines(source=untyped)
    typed_vars: dict[str, int] = variable_lines(source=typed)
    converted_vars: dict[str, int] = variable_lines(source=converted)
    untyped_vars: dict[str, int] = variable_lines(source=untyped)
    items: list[Item] = []
    extra: dict[str, int] = {scope: 0 for scope, _label in Constants.scopes}

    def judge(*, mine: str | None, author: str, normalise: bool) -> str:
        """Score the converted annotation against the author's.

        Args:
            mine: The annotation astart wrote, or ``None``.
            author: The author's annotation.
            normalise: Whether to normalise ``mine`` before comparing.

        Returns:
            ``missing``, ``exact``, ``wrong``, a relation kind, or
            ``unresolved``.

        """
        if mine is None:
            return "missing"
        shown: str = (
            recovery.normalize_annotation(text=mine) if normalise else mine
        )
        if shown == author:
            return "exact"
        kind: str | None = recovery.relation(
            written=shown,
            truth=author,
            context=context,
        )
        if kind == "contradiction":
            return "wrong"
        return kind or "unresolved"

    for key, author in truth.items():
        if key in start:
            continue
        mine: str | None = written.get(key)
        items.append(
            Item(
                scope="parameters_and_returns",
                key=key,
                verdict=judge(mine=mine, author=author, normalise=True),
                written=mine,
                author=author,
                family=family_of(
                    text=author,
                    classes=classes,
                    typevars=typevars,
                    aliases=aliases,
                ),
                typed_line=typed_params.get(key),
                converted_line=converted_params.get(key),
                untyped_line=untyped_params.get(key),
            ),
        )
    for key, author in truth_vars.items():
        mine = done_vars.get(key)
        items.append(
            Item(
                scope="variables",
                key=key,
                verdict=judge(mine=mine, author=author, normalise=False),
                written=mine,
                author=author,
                family=family_of(
                    text=author,
                    classes=classes,
                    typevars=typevars,
                    aliases=aliases,
                ),
                typed_line=typed_vars.get(key),
                converted_line=converted_vars.get(key),
                untyped_line=untyped_vars.get(key),
            ),
        )
    extra["parameters_and_returns"] = sum(
        1 for key in written if key not in truth and key not in start
    )
    extra["variables"] = sum(1 for key in done_vars if key not in truth_vars)
    return items, extra


def tally(*, items: list[Item]) -> dict[str, Counter[str]]:
    """Count outcomes per scope.

    Args:
        items: Scored annotations.

    Returns:
        A counter of outcomes for each scope.

    """
    counts: dict[str, Counter[str]] = {
        scope: Counter() for scope, _label in Constants.scopes
    }
    for item in items:
        counts[item.scope][item.verdict] += 1
    return counts


def pair_json(
    *,
    counts: dict[str, Counter[str]],
    extra: dict[str, int],
) -> dict[str, dict[str, int]]:
    """Shape the counts like the output of ``benchmarks.pair``.

    Args:
        counts: Outcomes per scope.
        extra: Annotations written that the typed file lacks, per scope.

    Returns:
        ``correct``, ``wrong``, ``to_recover`` and the other outcomes
        per scope.

    """
    shaped: dict[str, dict[str, int]] = {}
    for scope, _label in Constants.scopes:
        found: Counter[str] = counts[scope]
        shaped[scope] = {
            "to_recover": sum(found.values()),
            "correct": found["exact"],
            "narrower": found["narrower"],
            "looser": found["looser"] + found["compatible"],
            "unresolved": found["unresolved"],
            "wrong": found["wrong"],
            "missing": found["missing"],
            "not_in_typed": extra[scope],
        }
    return shaped


def summary_table(*, shaped: dict[str, dict[str, int]]) -> list[str]:
    """Render the summary table.

    Args:
        shaped: Counts per scope in the ``benchmarks.pair`` shape.

    Returns:
        Markdown lines.

    """
    lines: list[str] = [
        "| Scope | To recover | Exact | Narrower | Looser | Unresolved | "
        "Wrong | Missing | Extra |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for scope, label in Constants.scopes:
        row: dict[str, int] = shaped[scope]
        total: int = row["to_recover"]
        lines.append(
            f"| {label} | {total} | {row['correct']} "
            f"({percent(value=row['correct'], total=total)}) | "
            f"{row['narrower']} | {row['looser']} | {row['unresolved']} | "
            f"{row['wrong']} | {row['missing']} | {row['not_in_typed']} |",
        )
    lines.extend(("", "```text"))
    for scope, label in Constants.scopes:
        row = shaped[scope]
        total = row["to_recover"]
        lines.append(
            f"{label:<24} exact {bar(value=row['correct'], total=total)} "
            f"{percent(value=row['correct'], total=total):>7}   "
            f"wrong {bar(value=row['wrong'], total=total)} "
            f"{percent(value=row['wrong'], total=total):>7}",
        )
    lines.append("```")
    return lines


def family_rows(*, items: list[Item]) -> list[dict[str, int | str]]:
    """Group outcomes by the family of the author's annotation.

    Args:
        items: Scored annotations.

    Returns:
        One row per family, largest gap first.

    """
    by_family: dict[str, Counter[str]] = {
        name: Counter() for name in Constants.families
    }
    for item in items:
        by_family[item.family][item.verdict] += 1
    total_gap: int = sum(1 for item in items if item.verdict in Constants.gap)
    rows: list[dict[str, int | str]] = []
    for name, found in by_family.items():
        total: int = sum(found.values())
        if total == 0:
            continue
        gap: int = sum(found[v] for v in Constants.gap)
        rows.append(
            {
                "family": name,
                "total": total,
                "exact": found["exact"],
                "compatible": sum(found[v] for v in Constants.compatible),
                "unresolved": found["unresolved"],
                "wrong": found["wrong"],
                "missing": found["missing"],
                "gap": gap,
                "share": round(number=100 * gap / total_gap)
                if total_gap
                else 0,
            },
        )
    return sorted(rows, key=lambda row: -int(row["gap"]))


def family_table(
    *,
    rows: list[dict[str, int | str]],
    limit: int,
    anchors: dict[str, str],
) -> list[str]:
    """Render the gap-by-family table.

    Args:
        rows: Output of ``family_rows``.
        limit: Maximum number of families shown.
        anchors: TODO anchor by task ID, to link the tasks.

    Returns:
        Markdown lines.

    """
    lines: list[str] = [
        "| Author's annotation | Total | Exact | Compatible | Wrong | "
        "Missing | Share of gap | Hard | Tasks |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |",
    ]
    for row in rows[:limit]:
        name: str = str(object=row["family"])
        hard: str = "yes" if name in Constants.hard else ""
        tasks: str = task_links(
            text=Constants.tasks[name],
            anchors=anchors,
        )
        lines.append(
            f"| {name} | {row['total']} | {row['exact']} | "
            f"{row['compatible']} | {row['wrong']} | {row['missing']} | "
            f"{row['share']} % | {hard} | {tasks} |",
        )
    return lines


def owner_of(*, key: str) -> str:
    """Name the function or class an annotation belongs to.

    Args:
        key: Node path such as ``Class.method.param`` or ``function->``.

    Returns:
        The path without its last part.

    """
    if key.endswith("->"):
        return key[:-2]
    return key.rpartition(".")[0] or key


@final
class Reasons:
    """Plain-language meaning and TODO tasks for each opacity reason.

    Attributes:
        known: Reason label to ``(meaning, tasks)``.
        unknown: Fallback for a reason that is not described yet.

    """

    known: Final[dict[str, tuple[str, str]]] = {
        "settled": (
            "Typed by negotiation: these are the nodes astart can write",
            "",
        ),
        "declared": (
            "Already annotated in the input, or guaranteed by the language",
            "",
        ),
        "unsettled (no evidence)": (
            "Nothing proves a type and no evidence reaches the node",
            "P-05, AL-05, AL-18",
        ),
        "downstream of a blocked node": (
            "Opacity spreads: the node depends on a blocked one. "
            "Fix the direct reasons first",
            "AL-03, AL-04",
        ),
        "lost a contribution": (
            "A contract could not be transferred, so the result would be "
            "incomplete",
            "F-07",
        ),
        "direct: unprovable Name": (
            "Returns a name the prover cannot type (a wrapper, a decorated "
            "function, a class)",
            "M5-19, AL-03, M4-03",
        ),
        "direct: unprovable Call": (
            "Returns a call result the prover cannot type "
            "(`super()`, `getattr`, constructors, `list(...)`)",
            "W-06, I-08, I-21, F-41",
        ),
        "direct: function escapes as a value": (
            "The function is passed around as a value, so its callers are "
            "unknown",
            "W-07, AL-04",
        ),
        "direct: no evidence reaches it": (
            "A parameter with no call site, default or use that proves a type",
            "W-08, P-05, AL-05, AL-09",
        ),
        "direct: stub, abstract or never returns": (
            "Protocol stubs, abstract methods and functions that never return",
            "AF-03, I-16, M5-04",
        ),
        "direct: a call to it cannot be bound": (
            "Some call to the function cannot be matched to its parameters",
            "W-07, M2-02, M2-11",
        ),
        "direct: unprovable Tuple": (
            "Returns a tuple whose members are not all typed",
            "I-17, F-40",
        ),
        "direct: unprovable Dict": (
            "Returns a dict display with unpacking or untyped members",
            "I-17, F-40",
        ),
        "direct: unprovable BinOp": (
            "Arithmetic over operands that are not typed",
            "I-10, W-06",
        ),
        "direct: generator": (
            "Generator functions: the return type needs the yield types",
            "W-13, M4-06",
        ),
        "direct: unprovable Attribute": (
            "Returns an attribute the class table does not type",
            "I-11, W-12, M2-06",
        ),
    }
    unknown: Final[tuple[str, str]] = (
        "Not described yet: add it to the table in "
        "scripts/conversion_report.py",
        "G-03",
    )


def describe(*, label: str) -> tuple[str, str]:
    """Look up the meaning and tasks of an opacity reason.

    Args:
        label: Reason label from the opacity report.

    Returns:
        The meaning and the tasks.

    """
    if label in Reasons.known:
        return Reasons.known[label]
    if label.startswith("direct: unprovable "):
        kind: str = label.removeprefix("direct: unprovable ")
        return f"Returns a {kind} expression the prover cannot type", "G-03"
    return Reasons.unknown


def opacity_sections(*, source: str, samples: int) -> list[Section]:
    """Run the opacity analysis of the untyped module.

    Args:
        source: Untyped source.
        samples: Examples kept per direct reason.

    Returns:
        The sections of ``scripts/opacity_report.collect``, or an empty list
        when that script cannot be imported.

    """
    for name in ("opacity_report", "scripts.opacity_report"):
        try:
            module: ModuleType = import_module(name=name)
        except ImportError:
            continue
        return cast(
            typ="list[Section]",
            val=list(module.collect(source=source, samples=samples)),
        )
    return []


def owner_cell(*, owner: str, sources: Sources) -> str:
    """Show an owner with a link to its definition in the input.

    Args:
        owner: Function or class path.
        sources: Source lines and line maps.

    Returns:
        The owner in code style, with a link when its line is known.

    """
    number: int | None = sources.untyped_params.get(
        f"{owner}->",
    ) or sources.untyped_vars.get(owner)
    if number is None:
        return f"`{owner}`"
    where: str = link(
        label="untyped.py",
        target=sources.links["untyped"],
        number=number,
    )
    return f"`{owner}` ({where})"


def opacity_markdown(
    *,
    sections: list[Section],
    sources: Sources,
) -> list[str]:
    """Render the opacity analysis as tables with linked examples.

    Args:
        sections: Sections from ``opacity_sections``.
        sources: Source lines, line maps and link targets.

    Returns:
        Markdown lines.

    """
    lines: list[str] = []
    anchors: dict[str, str] = sources.anchors
    for section in sections:
        lines.extend(
            (
                f"### {section.title.capitalize()}: {section.total} nodes",
                "",
                "| Reason | Nodes | Share | | What it means | Tasks |",
                "| --- | ---: | ---: | --- | --- | --- |",
            ),
        )
        for row in section.rows:
            meaning, tasks = describe(label=row.label)
            lines.append(
                f"| {row.label} | {row.count} | "
                f"{percent(value=row.count, total=section.total)} | "
                f"`{bar(value=row.count, total=section.total)}` | "
                f"{meaning} | {task_links(text=tasks, anchors=anchors)} |",
            )
        for row in section.rows:
            if not row.samples:
                continue
            lines.extend(
                (
                    "",
                    f"<details><summary>Examples: {row.label} "
                    f"({row.count} nodes)</summary>",
                    "",
                    "| Node | Line | Code | Evidence |",
                    "| --- | ---: | --- | --- |",
                ),
            )
            for node, why in row.samples:
                number: int | None = node_line(
                    key=node,
                    sources=sources,
                )
                code: str | None = line_text(
                    lines=sources.untyped,
                    number=number,
                )
                shown: str = (
                    "n/a" if code is None else f"`{cell(text=code.strip())}`"
                )
                where: str = link(
                    label="untyped.py",
                    target=sources.links["untyped"],
                    number=number,
                )
                lines.append(
                    f"| `{node}` | {where} | {shown} | `{cell(text=why)}` |",
                )
            lines.extend(("", "</details>"))
        lines.append("")
    return lines


def plain(*, text: str) -> str:
    """Make text safe inside inline code.

    Args:
        text: Any text.

    Returns:
        The text with backticks replaced.

    """
    return text.replace("`", "'")


class _EvidenceModule(Protocol):
    """The slice of ``scripts.evidence`` the report uses."""

    def build_index(self, *, source: str) -> Index:
        """Index a module for evidence lookup.

        Args:
            source: Module source.

        Returns:
            The evidence index.

        """
        ...

    def evidence_for(
        self,
        *,
        index: Index,
        key: str,
        scope: str,
    ) -> list[Evidence] | None:
        """Collect the evidence for one scored node.

        Args:
            index: The module index.
            key: Node path.
            scope: Result scope.

        Returns:
            The facts, or ``None`` when the node is unknown.

        """
        ...

    def conclusion(self, *, author: str, evidence: list[Evidence]) -> str:
        """Say in words why the evidence does not give the author's type.

        Args:
            author: The author's annotation.
            evidence: The collected facts.

        Returns:
            One paragraph of reading.

        """
        ...

    def short(self, *, node: AST | str) -> str:
        """Render an expression for display, shortened.

        Args:
            node: An AST node or text.

        Returns:
            The shortened rendering.

        """
        ...


def evidence_module() -> _EvidenceModule | None:
    """Import the evidence collector next to this script.

    Returns:
        The module, or ``None`` when it cannot be imported.

    """
    for name in ("evidence", "scripts.evidence"):
        try:
            return cast(typ="_EvidenceModule", val=import_module(name=name))
        except ImportError:
            continue
    return None


type _Collected = tuple[_EvidenceModule, list[Evidence]]


def _collect_evidence(
    *,
    module: _EvidenceModule | None,
    sources: Sources,
    item: Item,
) -> _Collected | None:
    """Pair the evidence module with the facts for one scored node.

    Args:
        module: The imported evidence module.
        sources: Source lines and the evidence index.
        item: The scored node.

    Returns:
        The module and its facts, or ``None`` when either is missing.

    """
    index: Index | None = sources.evidence
    if module is None or index is None:
        return None
    found: list[Evidence] | None = module.evidence_for(
        index=index,
        key=item.key,
        scope=item.scope,
    )
    if not found:
        return None
    return module, found


def astart_part(*, item: Item, sources: Sources) -> str:
    """Explain why astart missed or changed the author's type.

    Args:
        item: A scored annotation that is missing or differs.
        sources: Source lines, line maps and the opacity reasons.

    Returns:
        One paragraph, specific to the node.

    """
    if item.verdict == "missing":
        found: tuple[str, str] | None = sources.reasons.get(item.key)
        if found is None:
            return (
                "**Why astart left it unannotated:** its contract graph has "
                "no node for this path, so no rule looked at it."
            )
        label, why = found
        tasks: str = task_links(
            text=describe(label=label)[1],
            anchors=sources.anchors,
        )
        detail: str = f" (`{plain(text=why)}`)" if why else ""
        if label in {"settled", "declared"}:
            return (
                "**Why astart left it unannotated:** negotiation had "
                f"classified the node as *{label}*{detail}, yet nothing was "
                "written: the acceptance policy or a guard (for example "
                "`bound_when_evaluated`, the confidence floor or the checker) "
                "refused the hint, so trace it with the Cookbook debugging "
                "playbook (C-7)."
            )
        meaning: str = describe(label=label)[0]
        return (
            f"**Why astart left it unannotated:** *{label}*{detail}. "
            f"{meaning}. Tasks: {tasks}."
        )
    written: str = item.written or "?"
    if "object" in item.author and "object" not in written:
        return (
            f"**Why astart wrote `{plain(text=written)}`:** it is narrower "
            f"than the author's `{plain(text=item.author)}`, which uses the "
            "top type `object`. astart never writes `object`, and the "
            "narrower type is valid for every caller in this file "
            "(scoring task G-02)."
        )
    return (
        f"**Why astart wrote `{plain(text=written)}`:** it differs from the "
        f"author's `{plain(text=item.author)}` ({item.verdict}); compare the "
        "sources above to see which of them it followed."
    )


def explain(*, item: Item, sources: Sources) -> list[str]:
    """Explain, for one case, why the author's type is what it is.

    Args:
        item: A scored annotation.
        sources: Source lines, line maps, evidence index and reasons.

    Returns:
        Markdown lines: the numbered path of evidence in the untyped source,
        a reading of it, and why astart did not reach the author's type.

    """
    collected: _Collected | None = _collect_evidence(
        module=evidence_module(),
        sources=sources,
        item=item,
    )
    lines: list[str] = [
        f"**Why the author's type is `{plain(text=item.author)}`** "
        "(reading `dev/untyped.py` only):",
        "",
    ]
    if collected is None:
        lines.append(
            "No evidence was found for this node in the untyped source.",
        )
    else:
        module, found = collected
        for number, fact in enumerate(iterable=found[:8], start=1):
            where: str = link(
                label="untyped.py",
                target=sources.links["untyped"],
                number=fact.line,
            )
            shown: str = f" → `{fact.type}`" if fact.type else ""
            note: str = (
                "" if fact.certain else " *(matched by name only)*"
            )
            lines.append(
                f"{number}. {where} {fact.kind}: "
                f"`{plain(text=fact.text)}`{shown}{note}",
            )
        lines.extend(
            (
                "",
                "*Reading:* "
                + module.conclusion(author=item.author, evidence=found),
            ),
        )
    lines.extend(("", astart_part(item=item, sources=sources)))
    return lines


def case(*, item: Item, sources: Sources) -> list[str]:
    """Show one case: the diff, then the bespoke explanation.

    Args:
        item: A scored annotation.
        sources: Source lines, line maps, evidence index and reasons.

    Returns:
        Markdown lines.

    """
    return [
        *snippet(item=item, sources=sources),
        "",
        *explain(item=item, sources=sources),
    ]


def astart_short(*, item: Item, sources: Sources) -> str:
    """Say in a few words why astart missed or changed the author's type.

    Args:
        item: A scored annotation that is not exact.
        sources: Source lines, line maps and the opacity reasons.

    Returns:
        A short phrase for a code comment.

    """
    if item.verdict == "missing":
        found: tuple[str, str] | None = sources.reasons.get(item.key)
        if found is None:
            return "astart: no graph node for this path"
        label, why = found
        detail: str = f" ({plain(text=why)})" if why else ""
        return f"astart: {label}{detail}"
    written: str = item.written or "?"
    return f"astart wrote {plain(text=written)}"


def fix_comment(*, item: Item, sources: Sources) -> str:
    """Build the bespoke ``[FIX]`` comment for one case.

    Args:
        item: A scored annotation that is not exact.
        sources: Source lines, line maps, evidence index and reasons.

    Returns:
        One line: the author's type, the evidence that leads to it, and why
        astart did not reach it.

    """
    collected: _Collected | None = _collect_evidence(
        module=evidence_module(),
        sources=sources,
        item=item,
    )
    target: str = (
        "->" if item.key.endswith("->") else item.key.rpartition(".")[2]
    )
    parts: list[str] = []
    if collected is None:
        parts.append("no evidence for this node in the untyped source")
    else:
        module, found = collected
        typed_first: list[Evidence] = (
            [fact for fact in found if fact.type][:2] or found[:2]
        )
        for fact in typed_first:
            shown: str = f" -> {fact.type}" if fact.type else ""
            parts.append(
                f"untyped.py:{fact.line} {fact.kind} "
                f"{module.short(node=plain(text=fact.text))}{shown}",
            )
        parts.append(
            module.conclusion(author=item.author, evidence=found).rstrip("."),
        )
    parts.append(astart_short(item=item, sources=sources))
    text: str = (
        f"[FIX] {target}: {item.author} ({item.verdict}) - " + "; ".join(parts)
    )
    limit: int = 320
    return text if len(text) <= limit else text[: limit - 1] + "…"


def full_report(
    *,
    meta: dict[str, str],
    shaped: dict[str, dict[str, int]],
    items: list[Item],
    extras: Extras,
) -> str:
    """Render the full Markdown report.

    Args:
        meta: Header fields (time, tree, duration, settings, command).
        shaped: Counts per scope.
        items: Scored annotations.
        extras: Optional report content (sections, sources, examples).

    Returns:
        The report text.

    """
    sections: list[Section] = extras.sections
    sources: Sources = extras.sources
    examples: int = extras.examples
    files: str = (
        f"[dev/untyped.py]({sources.links['untyped']}) · "
        f"[dev/typed.py]({sources.links['typed']}) · "
        f"[conversion-output.py.txt]({sources.links['converted']})"
    )
    lines: list[str] = [
        f"# Conversion report: [`dev/untyped.py`]({sources.links['untyped']}) "
        f"to [`dev/typed.py`]({sources.links['typed']})",
        "",
        f"*Generated {meta['when']} by "
        "[`scripts/conversion_report.py`](../scripts/conversion_report.py). "
        "Do not edit; run the script again.*",
        "",
        "In every code example `-` is how the converted code is "
        "([conversion-output.py.txt](conversion-output.py.txt)) and `+` is "
        "how it should be (the author's `dev/typed.py`); the links go to "
        "the exact lines.",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| files | {files} |",
    ]
    lines.extend(
        f"| {key} | {value} |" for key, value in meta.items() if key != "when"
    )
    lines.extend(("", "## Summary", ""))
    lines.extend(summary_table(shaped=shaped))
    lines.extend(
        (
            "",
            "## Where the gap is, by the author's annotation",
            "",
            "Compatible means valid but not identical (narrower or looser). "
            "Hard families are partly author choices or policy and bound the "
            "90 % target.",
            "",
        ),
    )
    rows: list[dict[str, int | str]] = family_rows(items=items)
    lines.extend(
        family_table(rows=rows, limit=len(rows), anchors=sources.anchors),
    )
    wrong: list[Item] = sorted(
        (item for item in items if item.verdict == "wrong"),
        key=lambda item: (item.scope, item.key),
    )
    lines.extend(
        (
            "",
            f"## Wrong annotations ({len(wrong)}), with code",
            "",
            "Each one is a bug or a scoring difference "
            "(G-02, G-05, P-07, G-04).",
            "",
        ),
    )
    for item in wrong:
        lines.extend((*case(item=item, sources=sources), ""))
    owners: Counter[str] = Counter(
        owner_of(key=item.key)
        for item in items
        if item.verdict in Constants.gap
    )
    lines.extend(
        (
            "## Gap by owner (most missing or wrong first)",
            "",
            "| Owner | Gap |",
            "| --- | ---: |",
        ),
    )
    lines.extend(
        f"| {owner_cell(owner=owner, sources=sources)} | {count} |"
        for owner, count in owners.most_common(n=Constants.owner_rows)
    )
    lines.extend(("", "## Missing annotations by family, with code", ""))
    for row in rows:
        name: str = str(object=row["family"])
        missing: list[Item] = [
            item
            for item in items
            if item.family == name and item.verdict == "missing"
        ]
        if not missing:
            continue
        lines.extend(
            (
                f"### {name}: {len(missing)} missing",
                "",
                (
                    "Tasks: "
                    + task_links(
                        text=Constants.tasks[name],
                        anchors=sources.anchors,
                    )
                ),
                "",
            ),
        )
        for item in missing[:examples]:
            lines.extend((*case(item=item, sources=sources), ""))
        lines.extend(
            (
                f"<details><summary>All {len(missing)} (first "
                f"{Constants.list_limit}, with links to the author's line)"
                "</summary>",
                "",
            ),
        )
        lines.extend(
            f"- `{item.key}` "
            f"({_typed_link(item=item, sources=sources)})"
            f": `{item.author}`"
            for item in missing[: Constants.list_limit]
        )
        lines.extend(("", "</details>", ""))
    lines.extend(
        (
            "## Why nodes stay unannotated",
            "",
            "From [`scripts/opacity_report.py`](../scripts/opacity_report.py) "
            "on the untyped input. A node is something that has a type: a "
            "parameter, a return value or a local variable. A *direct* reason "
            "blocks a node by itself; the other labels describe nodes that "
            "are typed, declared, or blocked only because of another node.",
            "",
        ),
    )
    lines.extend(
        opacity_markdown(sections=sections, sources=sources)
        if sections
        else ["The opacity analysis was skipped or could not run.", ""],
    )
    lines.extend(("## Reproduce", "", f"`{meta['command']}`"))
    return "\n".join(lines) + "\n"


def todo_block(
    *,
    meta: dict[str, str],
    shaped: dict[str, dict[str, int]],
    items: list[Item],
    sections: list[Section],
    sources: Sources,
) -> str:
    """Render the compact block that is embedded in the TODO file.

    Args:
        meta: Header fields.
        shaped: Counts per scope.
        items: Scored annotations.
        sections: Opacity sections (may be empty).
        sources: Source lines, line maps and link targets.

    Returns:
        Markdown for the block between the conversion markers.

    """
    lines: list[str] = [
        f"Run {meta['when']} · tree `{meta['tree']}` · converted in "
        f"{meta['converted in']} · files: "
        f"[dev/untyped.py]({sources.links['untyped']}), "
        f"[dev/typed.py]({sources.links['typed']}), "
        "[conversion-output.py.txt](conversion-output.py.txt) · "
        "[full report](conversion-report.md)",
        "",
    ]
    anchors: dict[str, str] = sources.anchors
    lines.extend(summary_table(shaped=shaped))
    rows: list[dict[str, int | str]] = family_rows(items=items)
    lines.extend(("", "Where the gap is, by the author's annotation:", ""))
    lines.extend(family_table(rows=rows, limit=8, anchors=anchors))
    if sections:
        lines.extend(
            (
                "",
                "Why nodes stay unannotated (biggest direct reasons; "
                "examples with links are in the full report):",
                "",
                "| Nodes | Reason | Nodes of that kind | What it means | "
                "Tasks |",
                "| --- | --- | ---: | --- | --- |",
            ),
        )
        for section in sections:
            direct: list[Row] = [
                r
                for r in section.rows
                if r.label.startswith("direct")
            ]
            for row in direct[:4]:
                meaning, tasks = describe(label=row.label)
                lines.append(
                    f"| {section.title} | {row.label} | {row.count} "
                    f"({percent(value=row.count, total=section.total)}) | "
                    f"{meaning} | "
                    f"{task_links(text=tasks, anchors=anchors)} |",
                )
    wrong: list[Item] = sorted(
        (item for item in items if item.verdict == "wrong"),
        key=lambda item: (item.scope, item.key),
    )
    lines.extend(
        (
            "",
            "In the examples `-` is how the converted code is and `+` is how "
            "it should be (the author's `dev/typed.py`); the links go to the "
            "exact lines.",
            "",
            f"<details><summary>Wrong annotations with code "
            f"(first 6 of {len(wrong)})</summary>",
            "",
        ),
    )
    for item in wrong[:6]:
        lines.extend((*case(item=item, sources=sources), ""))
    lines.extend(("</details>", ""))
    lines.extend(
        (
            "<details><summary>Examples of missing annotations "
            "(1 per family, largest gaps first)</summary>",
            "",
        ),
    )
    for row in rows[:6]:
        name: str = str(object=row["family"])
        missing: list[Item] = [
            item
            for item in items
            if item.family == name and item.verdict == "missing"
        ]
        if not missing:
            continue
        tasks: str = task_links(
            text=Constants.tasks[name],
            anchors=anchors,
        )
        lines.extend(
            (
                f"**{name}** ({len(missing)} missing; tasks: {tasks})",
                "",
            ),
        )
        for item in missing[:1]:
            lines.extend((*case(item=item, sources=sources), ""))
    lines.append("</details>")
    return "\n".join(lines)


def write_block(*, todo: Path, name: str, block: str) -> bool:
    """Replace one generated block in the TODO file.

    Args:
        todo: Path of the TODO file.
        name: Marker name of the block.
        block: New block text.

    Returns:
        Whether the markers were found and the block written.

    """
    start: str = f"<!-- {name}:start -->"
    end: str = f"<!-- {name}:end -->"
    text: str = todo.read_text(encoding="utf-8")
    head, found_start, rest = text.partition(start)
    _, found_end, tail = rest.partition(end)
    if not found_start or not found_end:
        return False
    _ = todo.write_text(
        data=f"{head}{start}\n{block}\n{end}{tail}",
        encoding="utf-8",
    )
    return True


def convert(*, source: str, settings: Namespace) -> str:
    """Run astart in conversion mode on a source text.

    Args:
        source: Untyped source.
        settings: Parsed options (``min_confidence``, ``checker``).

    Returns:
        The converted source.

    """
    rules: ModuleType = import_module(name="astart.rules")
    vocabulary: ModuleType = import_module(name="astart.rules.vocabulary")
    registries: Registries = rules.default_registries()
    checker: Checker | None = None
    if settings.checker:
        checker = import_module(name="astart.rules.checker").build_checker(
            root=Path.cwd(),
        )
    return rules.fix_source(
        source=source,
        filename="untyped.py",
        catalog=rules.load_default_catalog(registries=registries),
        registries=registries,
        settings=rules.FixSettings(
            ceiling=vocabulary.FixSafety.guarded,
            min_confidence=settings.min_confidence,
            annotate_variables=True,
            negotiate=True,
            engine=True,
            checker=checker,
        ),
    ).source


def build_evidence_index(*, source: str) -> Index | None:
    """Index the untyped source for evidence lookup.

    Args:
        source: Untyped source.

    Returns:
        The index, or ``None`` when the collector cannot be imported.

    """
    module: _EvidenceModule | None = evidence_module()
    return None if module is None else module.build_index(source=source)


def _report_meta(
    *,
    namespace: Namespace,
    reused: bool,
    seconds: float,
    untyped: str,
    typed: str,
) -> tuple[dict[str, str], datetime]:
    """Build the report metadata and its timestamp.

    Args:
        namespace: Parsed command-line arguments.
        reused: Whether the saved conversion output was reused.
        seconds: Wall-clock seconds the conversion took.
        untyped: Untyped source.
        typed: Typed source.

    Returns:
        The metadata mapping and the generation time.

    """
    now: datetime = datetime.now().astimezone()
    command: str = "python scripts/conversion_report.py" + (
        f" --min-confidence {namespace.min_confidence}"
        + (" --checker" if namespace.checker else "")
    )
    meta: dict[str, str] = {
        "when": now.strftime(format="%a %d %b %Y, %H:%M %Z").strip(),
        "tree": tree_hash(root=Constants.root),
        "converted in": (
            "saved output reused" if reused else f"{seconds:.0f} s"
        ),
        "untyped / typed": (
            f"{len(untyped.splitlines())} / {len(typed.splitlines())} lines"
        ),
        "settings": (
            "conversion mode (engine), negotiation on, variables on, "
            f"minimum confidence {namespace.min_confidence}, "
            f"checker {'on' if namespace.checker else 'off'}"
        ),
        "command": command,
    }
    return meta, now


def _prepare_report(
    *,
    namespace: Namespace,
    untyped_source: str,
    typed_source: str,
    converted_source: str,
    items: list[Item],
) -> tuple[list[Section], Sources, Path, list[str], list[str]]:
    """Build the opacity sections, sources and annotated excerpt.

    Args:
        namespace: Parsed command-line arguments.
        untyped_source: Untyped source.
        typed_source: Typed source.
        converted_source: Converted source.
        items: Scored annotations.

    Returns:
        The opacity sections, the source bundle, the annotated copy path,
        the commented-line count source and the report excerpt lines.

    """
    sections: list[Section] = (
        []
        if namespace.no_opacity
        else opacity_sections(
            source=untyped_source,
            samples=namespace.examples + 1,
        )
    )
    out_dir: Path = namespace.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path: Path = out_dir / "conversion-output.py.txt"
    _ = output_path.write_text(data=converted_source, encoding="utf-8")
    sources: Sources = Sources(
        untyped=untyped_source.splitlines(),
        typed=typed_source.splitlines(),
        converted=converted_source.splitlines(),
        links={
            "typed": (
                relpath(path=namespace.typed, start=out_dir).replace("\\", "/")
            ),
            "untyped": relpath(
                path=namespace.untyped,
                start=out_dir,
            ).replace("\\", "/"),
            "converted": output_path.name,
        },
        untyped_params=param_lines(source=untyped_source),
        untyped_vars=variable_lines(source=untyped_source),
        anchors=todo_anchors(todo=namespace.todo),
        evidence=build_evidence_index(source=untyped_source),
        reasons={
            path: reason
            for section in sections
            for path, reason in section.nodes.items()
        },
    )
    flags: dict[int, list[str]] = {}
    for item in items:
        if item.verdict != "exact" and item.converted_line is not None:
            flags.setdefault(item.converted_line, []).append(
                fix_comment(item=item, sources=sources),
            )
    annotated: ModuleType = import_module(name="annotated")
    for line, text in annotated.header_flags(
        typed=typed_source,
        converted=converted_source,
    ):
        flags.setdefault(line, []).append(text)
    adds: list[str] = annotated.additions(
        typed=typed_source,
        converted=converted_source,
    )
    annotated_text: str = annotated.render(
        converted=converted_source,
        flags=flags,
        adds=adds,
    )
    annotated_path: Path = out_dir / "conversion-annotated.py.txt"
    _ = annotated_path.write_text(data=annotated_text, encoding="utf-8")
    marked: list[str] = [
        line
        for line in annotated_text.splitlines()
        if "# [FIX]" in line or "# [ADD]" in line
    ]
    excerpt: list[str] = [
        "## Annotated copy of the converted code",
        "",
        f"[conversion-annotated.py.txt]({annotated_path.name}) is the "
        "converted module with a bespoke comment on every line that differs "
        "from the author's: `# [FIX]` says what the line should be and the "
        "evidence in the untyped source that leads there, `# [ADD]` lists "
        "imports and definitions the author's file has and the converted one "
        f"lacks. {len(marked)} commented lines; the first 40:",
        "",
        "```python",
        *marked[:40],
        "```",
        "",
    ]
    return sections, sources, annotated_path, marked, excerpt


def main() -> int:
    """Convert, score and write the report.

    Returns:
        Zero.

    """
    parser: ArgumentParser = ArgumentParser(prog="conversion_report")
    parser.add_argument(
        "--untyped",
        type=Path,
        default=Constants.root / "dev" / "untyped.py",
    )
    parser.add_argument(
        "--typed",
        type=Path,
        default=Constants.root / "dev" / "typed.py",
    )
    parser.add_argument("--min-confidence", type=float, default=0.5)
    parser.add_argument("--examples", type=int, default=5)
    parser.add_argument("--checker", action="store_true")
    parser.add_argument("--no-opacity", action="store_true")
    parser.add_argument("--no-todo", action="store_true")
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--ledger", default="")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Constants.root / "docs",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=Constants.root / "docs" / "TODO.md",
    )
    args: Namespace = parser.parse_args()
    path.insert(0, str(object=Constants.root / "src"))
    untyped: str = args.untyped.read_text(encoding="utf-8")
    typed: str = args.typed.read_text(encoding="utf-8")
    _ = stdout.write(
        f"Converting {args.untyped} ({len(untyped.splitlines())} lines) "
        "in memory; this takes 1 to 2 minutes...\n",
    )
    saved: Path = args.out_dir / "conversion-output.py.txt"
    reused: bool = bool(args.reuse and saved.exists())
    began: float = perf_counter()
    converted: str = (
        saved.read_text(encoding="utf-8")
        if reused
        else convert(source=untyped, settings=args)
    )
    seconds: float = perf_counter() - began
    _ = stdout.write(
        ("Reused the saved output" if reused else "Converted")
        + f" in {seconds:.0f} s; scoring...\n",
    )
    recovery: _Recovery = cast(
        typ="_Recovery",
        val=import_module(name="astart.rules.recovery"),
    )
    items, extra = compare(
        untyped=untyped,
        typed=typed,
        converted=converted,
        recovery=recovery,
    )
    counts: dict[str, Counter[str]] = tally(items=items)
    shaped: dict[str, dict[str, int]] = pair_json(
        counts=counts,
        extra=extra,
    )
    meta, now = _report_meta(
        namespace=args,
        reused=reused,
        seconds=seconds,
        untyped=untyped,
        typed=typed,
    )
    (
        sections,
        sources,
        annotated_path,
        marked,
        excerpt,
    ) = _prepare_report(
        namespace=args,
        untyped_source=untyped,
        typed_source=typed,
        converted_source=converted,
        items=items,
    )
    report_path: Path = args.out_dir / "conversion-report.md"
    report_text: str = full_report(
        meta=meta,
        shaped=shaped,
        items=items,
        extras=Extras(
            sections=sections,
            sources=sources,
            examples=args.examples,
        ),
    )
    report_text = report_text.replace(
        "## Wrong annotations",
        "\n".join(excerpt) + "\n## Wrong annotations",
        count=1,
    )
    _ = report_path.write_text(data=report_text, encoding="utf-8")
    data: dict[str, object] = {
        **shaped,
        "generated": now.isoformat(timespec="seconds"),
        "meta": meta,
        "items": [asdict(obj=item) for item in items],
        "opacity": [asdict(obj=section) for section in sections],
    }
    json_path: Path = args.out_dir / "conversion-report.json"
    _ = json_path.write_text(
        data=dumps(obj=data, indent=2) + "\n",
        encoding="utf-8",
    )
    _ = stdout.write(
        f"Wrote {report_path}, {json_path}, {saved} and "
        f"{annotated_path} ({len(marked)} commented lines)\n",
    )
    if not args.no_todo:
        block: str = todo_block(
            meta=meta,
            shaped=shaped,
            items=items,
            sections=sections,
            sources=sources,
        ).replace(
            "[conversion-output.py.txt](conversion-output.py.txt)",
            "[conversion-output.py.txt](conversion-output.py.txt), "
            "[annotated copy](conversion-annotated.py.txt)",
            count=1,
        )
        wrote: bool = write_block(
            todo=args.todo,
            name="conversion",
            block=block,
        )
        _ = stdout.write(
            f"Updated the conversion block of {args.todo}\n"
            if wrote
            else f"No conversion markers in {args.todo}; block not written\n",
        )
    if args.ledger:
        done: CompletedProcess[str] = run(
            args=[
                executable,
                str(object=Constants.root / "scripts" / "status_update.py"),
                "--quiet",
                "pair",
                "--label",
                args.ledger,
            ],
            input=dumps(obj=shaped),
            text=True,
            check=False,
        )
        _ = stdout.write(f"Ledger updated (exit {done.returncode})\n")
    located: int = sum(1 for item in items if item.typed_line is not None)
    _ = stdout.write(
        f"Located the author's line for {located} of {len(items)} "
        "annotations\n",
    )
    for scope, label in Constants.scopes:
        row: dict[str, int] = shaped[scope]
        _ = stdout.write(
            f"{label}: {row['correct']} exact of {row['to_recover']}, "
            f"{row['wrong']} wrong, {row['missing']} missing\n",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
