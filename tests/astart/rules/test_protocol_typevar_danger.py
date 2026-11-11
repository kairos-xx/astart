"""M5-25: protocol and TypeVar synthesis danger-corpus gate.

Runs ``fix_source`` with default settings on every module in
``tests/corpus/base``
and ``tests/corpus/extended``, asserting that every output compiles and that
every
synthesised ``Protocol`` or ``TypeVar`` name is defined before its first use.

"""

from __future__ import annotations

from ast import (
    AST,
    Assign,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Expr,
    Load,
    Module,
    Name,
    parse,
    walk,
)
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.protocols import Constants as ProtocolConstants
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository tests directory.
        corpus_dirs (Final[tuple[str, str]]): Directories containing corpus
            modules.

    """

    root: Final[Path] = Paths.tests
    corpus_dirs: Final[tuple[str, str]] = ("corpus/base", "corpus/extended")


def _all_corpus_paths() -> tuple[Path, ...]:
    """Collect Python modules in the base and extended corpora.

    Returns:
        tuple[Path, ...]: Sorted tuple of corpus file paths.

    """
    paths: list[Path] = []
    for folder in Constants.corpus_dirs:
        directory: Path = Constants.root / folder
        paths.extend(sorted(directory.glob(pattern="*.py")))
    return tuple(paths)


def _is_synthesized_protocol(*, node: ClassDef) -> bool:
    """Tell whether ``node`` is a ``Protocol`` class synthesized by astart.

    Args:
        node (ClassDef): Class definition node.

    Returns:
        bool: ``True`` when the class docstring begins with the protocol
            marker.

    """
    if not node.body:
        return False
    first: AST = node.body[0]
    return (
        isinstance(first, Expr)
        and isinstance(first.value, Constant)
        and isinstance(first.value.value, str)
        and first.value.value.startswith(ProtocolConstants.docstring_marker)
    )


def _is_typevar_assign(
    *,
    node: Assign,
    original_names: frozenset[str],
) -> str | None:
    """Return the bound ``TypeVar`` name when ``node`` was synthesized.

    Args:
        node (Assign): Top-level assignment statement.
        original_names (frozenset[str]): Top-level names already defined in the
            input module.

    Returns:
        str | None: The new ``TypeVar`` identifier, or ``None``.

    """
    if len(node.targets) != 1 or not isinstance(node.targets[0], Name):
        return None
    target_name: str = node.targets[0].id
    if target_name in original_names or not isinstance(node.value, Call):
        return None
    func: AST = node.value.func
    is_tv: bool = (isinstance(func, Name) and func.id == "TypeVar") or (
        isinstance(func, Attribute) and func.attr == "TypeVar"
    )
    return target_name if is_tv else None


def _top_level_defined_names(*, tree: Module) -> frozenset[str]:
    """Collect top-level class and assignment names in ``tree``.

    Args:
        tree (Module): Parsed AST module.

    Returns:
        frozenset[str]: Frozenset of bound top-level identifiers.

    """
    names: set[str] = set()
    for statement in tree.body:
        if isinstance(statement, ClassDef):
            names.add(statement.name)
        elif isinstance(statement, Assign):
            for target in statement.targets:
                if isinstance(target, Name):
                    names.add(target.id)
    return frozenset(names)


def _check_module(*, path: Path) -> tuple[bool, tuple[str, ...]]:
    """Fix ``path`` and check compilation and definition-before-use order.

    Args:
        path (Path): Corpus file to check.

    Returns:
        tuple[bool, tuple[str, ...]]: ``(compiled_ok, ordering_violations)``.

    """
    source: str = path.read_text(encoding="utf-8")
    before_tree: Module = parse(source=source)
    original_names: frozenset[str] = _top_level_defined_names(tree=before_tree)
    registries: Registries = default_registries()
    output: str = fix_source(
        source=source,
        filename=path.name,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded),
    ).source
    try:
        _ = compile(source=output, filename=path.name, mode="exec")
    except SyntaxError:
        return False, ()
    after_tree: Module = parse(source=output)
    def_index: dict[str, int] = {}
    for index, statement in enumerate(iterable=after_tree.body):
        if isinstance(statement, ClassDef) and _is_synthesized_protocol(
            node=statement,
        ):
            def_index.setdefault(statement.name, index)
        elif isinstance(statement, Assign):
            tv_name: str | None = _is_typevar_assign(
                node=statement,
                original_names=original_names,
            )
            if tv_name is not None:
                def_index.setdefault(tv_name, index)
    violations: list[str] = []
    for name, defined_at in def_index.items():
        first_use: int | None = next(
            (
                index
                for index, statement in enumerate(iterable=after_tree.body)
                if index != defined_at
                and any(
                    isinstance(child, Name)
                    and isinstance(child.ctx, Load)
                    and child.id == name
                    for child in walk(node=statement)
                )
            ),
            None,
        )
        if first_use is not None and defined_at >= first_use:
            violations.append(
                f"{path.name}: {name} defined at {defined_at} "
                f"after use at {first_use}",
            )
    return True, tuple(violations)


@pytest.mark.slow
def test_danger_corpus_compiles_and_defines_synthesized_names_before_use() -> (
    None
):
    """Check corpora compile with synthesized names defined before use."""
    failures: list[str] = []
    ordering_errors: list[str] = []
    paths: tuple[Path, ...] = _all_corpus_paths()
    expect_true(condition=len(paths) > 0)
    for path in paths:
        compiled, violations = _check_module(path=path)
        if not compiled:
            failures.append(path.name)
        ordering_errors.extend(violations)
    expect_equal(actual=failures, expected=[])
    expect_equal(actual=ordering_errors, expected=[])
