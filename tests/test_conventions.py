"""House rules that must never regress."""

from __future__ import annotations

from ast import Attribute, Call, ClassDef, Name, expr, parse, walk
from pathlib import Path
from re import Pattern
from re import compile as re_compile
from typing import Final, final

from tests.expectations import expect_equal


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root: Repository root directory.
        self_name: This file's name, skipped by the scans.
        forbidden: Suppression-comment patterns, as regexes.
        bare_ast: Pattern for a bare ``import ast`` line.

    """

    root: Final[Path] = Path(__file__).parent.parent
    self_name: Final[str] = Path(__file__).name
    forbidden: Final[tuple[Pattern[str], ...]] = (
        re_compile(pattern=r"#\s*noqa\b"),
        re_compile(pattern=r"#\s*type:\s*ignore\b"),
    )
    bare_ast: Final[Pattern[str]] = re_compile(pattern=r"^import ast$")


def _offenders(*, pattern: Pattern[str]) -> list[str]:
    """List ``path:line`` hits of ``pattern`` under ``src`` and ``tests``.

    Args:
        pattern: Regular expression searched per line.

    Returns:
        Offender locations in sorted order.

    """
    found: list[str] = []
    for folder in ("src", "tests"):
        for path in sorted((Constants.root / folder).rglob(pattern="*.py")):
            if path.name == Constants.self_name:
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
        decorator: One decorator expression.

    Returns:
        Whether it is ``@final`` or ``@final()``.

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
