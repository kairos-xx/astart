"""House rules that must never regress."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    FunctionDef,
    Name,
    arg,
    arguments,
    expr,
    parse,
    walk,
)
from pathlib import Path
from re import Pattern
from re import compile as re_compile
from typing import Final, final

from tests.support.expectations import expect_equal
from tests.support.paths import Paths


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        self_name (Final[str]): This file's name, skipped by the scans.
        forbidden (Final[tuple[Pattern[str], ...]]): Suppression-comment
            patterns, as regexes.
        bare_ast (Final[Pattern[str]]): Pattern for a bare ``import ast`` line.
        production (Final[tuple[str, ...]]): Trees whose signatures must stay
            fully typed.
        every_tree (Final[tuple[str, ...]]): Every first-party tree the
            annotation scan covers.

    """

    root: Final[Path] = Paths.root
    self_name: Final[str] = Path(__file__).name
    forbidden: Final[tuple[Pattern[str], ...]] = (
        re_compile(pattern=r"#\s*noqa\b"),
        re_compile(pattern=r"#\s*type:\s*ignore\b"),
    )
    bare_ast: Final[Pattern[str]] = re_compile(pattern=r"^import ast$")
    production: Final[tuple[str, ...]] = ("src", "scripts")
    every_tree: Final[tuple[str, ...]] = (
        "src",
        "tests",
        "scripts",
    )


def _offenders(*, pattern: Pattern[str]) -> list[str]:
    """List ``path:line`` hits of ``pattern`` under ``src`` and ``tests``.

    Args:
        pattern (Pattern[str]): Regular expression searched per line.

    Returns:
        list[str]: Offender locations in sorted order.

    """
    found: list[str] = []
    for folder in ("src", "tests"):
        for path in sorted((Constants.root / folder).rglob(pattern="*.py")):
            if path.name == Constants.self_name or path.is_relative_to(
                Constants.root / "tests" / "corpus",
            ):
                continue
            lines: list[str] = path.read_text(encoding="utf-8").splitlines()
            found.extend(
                f"{path.relative_to(Constants.root)}:{number}"
                for number, line in enumerate(iterable=lines, start=1)
                if pattern.search(string=line)
            )
    return found


def test_no_suppression_comments() -> None:
    """Check that no source or test file silences a tool."""
    for pattern in Constants.forbidden:
        expect_equal(actual=_offenders(pattern=pattern), expected=[])


def test_no_bare_ast_import() -> None:
    """Check that modules import names from ``ast``, not the package."""
    expect_equal(
        actual=_offenders(pattern=Constants.bare_ast),
        expected=[],
    )


def _is_final(*, decorator: expr) -> bool:
    """Check whether ``decorator`` applies ``typing.final``.

    Args:
        decorator (expr): One decorator expression.

    Returns:
        bool: Whether it is ``@final`` or ``@final()``.

    """
    target: expr = decorator.func if isinstance(decorator, Call) else decorator
    if isinstance(target, Name):
        return target.id == "final"
    return isinstance(target, Attribute) and target.attr == "final"


def test_constants_classes_are_final() -> None:
    """Check every ``Constants`` class in ``src`` is ``@final``."""
    sources: Path = Constants.root / "src" / "astart"
    offenders: list[str] = [
        f"{path.relative_to(Constants.root)}:{node.lineno}"
        for path in sorted(sources.rglob(pattern="*.py"))
        for node in walk(node=parse(source=path.read_text(encoding="utf-8")))
        if isinstance(node, ClassDef)
        and node.name == "Constants"
        and not any(
            _is_final(decorator=decorator) for decorator in node.decorator_list
        )
    ]
    expect_equal(actual=offenders, expected=[])


def _annotations_of(*, node: AST) -> list[expr]:
    """Collect the annotation expressions owned by ``node``.

    Args:
        node (AST): One AST node.

    Returns:
        list[expr]: Parameter, return and assignment annotations, in order.

    """
    found: list[expr] = []
    if isinstance(node, AnnAssign):
        found.append(node.annotation)
    if isinstance(node, (FunctionDef, AsyncFunctionDef)):
        arguments: arguments = node.args
        parameters: tuple[arg, ...] = (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
        found.extend(
            parameter.annotation
            for parameter in parameters
            if parameter.annotation is not None
        )
        found.extend(
            extra.annotation
            for extra in (arguments.vararg, arguments.kwarg)
            if extra is not None and extra.annotation is not None
        )
        if node.returns is not None:
            found.append(node.returns)
    return found


def _annotation_hits(
    *,
    folders: tuple[str, ...],
    banned: frozenset[str],
    signatures_only: bool,
) -> list[str]:
    """List ``path:line`` where an annotation names a banned type.

    Args:
        folders (tuple[str, ...]): Repository folders to scan.
        banned (frozenset[str]): Bare type names that must not appear.
        signatures_only (bool): Skip ``name: T = ...`` assignment annotations.

    Returns:
        list[str]: Offender locations in sorted order.

    """
    hits: list[str] = []
    for folder in folders:
        for path in sorted((Constants.root / folder).rglob(pattern="*.py")):
            if path.name == Constants.self_name or path.is_relative_to(
                Constants.root / "tests" / "corpus",
            ):
                continue
            if path == (
                Constants.root
                / "scripts"
                / "compare"
                / "artifacts"
                / "results"
                / "result.py"
            ):
                continue
            tree: AST = parse(source=path.read_text(encoding="utf-8"))
            for node in walk(node=tree):
                if signatures_only and isinstance(node, AnnAssign):
                    continue
                for annotation in _annotations_of(node=node):
                    hits.extend(
                        f"{path.relative_to(Constants.root)}:{sub.lineno}"
                        for sub in walk(node=annotation)
                        if isinstance(sub, Name) and sub.id in banned
                    )
    return hits


def test_no_any_annotations() -> None:
    """No annotation in any first-party tree names ``Any``."""
    expect_equal(
        actual=_annotation_hits(
            folders=Constants.every_tree,
            banned=frozenset({"Any"}),
            signatures_only=False,
        ),
        expected=[],
    )


def test_no_object_in_production_signatures() -> None:
    """Production signatures never degrade to ``object``.

    ``tests`` is exempt: doubles legitimately take ``**_kwargs: object``
    and return opaque ``object`` values. ``name: object = expr`` locals
    are the sanctioned narrow-then-``isinstance`` idiom, not signatures.

    """
    expect_equal(
        actual=_annotation_hits(
            folders=Constants.production,
            banned=frozenset({"object"}),
            signatures_only=True,
        ),
        expected=[],
    )


def _protocol_ranges(*, tree: AST) -> list[tuple[int, int]]:
    """Line ranges of classes deriving from ``Protocol``.

    Args:
        tree (AST): Parsed module.

    Returns:
        list[tuple[int, int]]: ``(first, last)`` line numbers of each protocol
            class.

    """
    return [
        (node.lineno, node.end_lineno or node.lineno)
        for node in walk(node=tree)
        if isinstance(node, ClassDef)
        and any(
            (isinstance(base, Name) and base.id == "Protocol")
            or (isinstance(base, Attribute) and base.attr == "Protocol")
            for base in node.bases
        )
    ]


def _positional_params(*, node: FunctionDef | AsyncFunctionDef) -> int:
    """Count parameters callers may still pass positionally.

    Args:
        node (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        int: Positional-or-keyword parameters beyond ``self``/``cls``.

    """
    arguments: arguments = node.args
    count: int = len(arguments.args)
    if arguments.args and arguments.args[0].arg in ("self", "cls"):
        count -= 1
    return count


def test_scripts_signatures_are_keyword_only() -> None:
    """Functions in ``scripts`` take parameters by keyword only.

    ``Protocol`` members mirror external signatures (``hashlib``,
    ``argparse``) and stay positional; positional-only parameters cannot
    be passed by keyword anyway. ``tests`` is exempt because pytest
    fixtures are injected by name.

    """
    offenders: list[str] = []
    sources: Path = Constants.root / "scripts"
    for path in sorted(sources.rglob(pattern="*.py")):
        if path == sources / "compare" / "artifacts" / "results" / "result.py":
            continue
        tree: AST = parse(source=path.read_text(encoding="utf-8"))
        protocols: list[tuple[int, int]] = _protocol_ranges(tree=tree)
        for node in walk(node=tree):
            if not isinstance(node, (FunctionDef, AsyncFunctionDef)):
                continue
            if any(start <= node.lineno <= end for start, end in protocols):
                continue
            if _positional_params(node=node) > 0:
                offenders.append(
                    f"{path.relative_to(Constants.root)}:{node.lineno}"
                    f" {node.name}",
                )
    expect_equal(actual=offenders, expected=[])
