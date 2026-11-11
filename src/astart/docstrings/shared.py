"""Shared docstring helpers for the DOC rule family.

The detectors prefer the structured ``module.docstrings`` a
``CommentedModule`` carries; on a plain ``ast.Module`` they fall back to
the style-aware docstring parser, retaining the legacy Google-style fallback
for parameter spelling and dedent boundaries. The rules run on either AST.

"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    Module,
    get_docstring,
)
from re import Pattern
from re import compile as compile_pattern
from typing import TYPE_CHECKING, Final, final

from astart.docstrings import parse_docstring

if TYPE_CHECKING:
    from re import Match

    from astart.docstrings import DocKind, DocstringNode


@final
class Constants:
    """Group module-level constants.

    Attributes:
        section_titles (Final[dict[str, str]]): Google-style headers mapped to
            entry kinds.
        entry_pattern (Final[Pattern[str]]): ``name:`` or ``name (type):``
            inside a section.
        kinds (Final[tuple[str, ...]]): Entry kinds used by the rule family.

    """

    section_titles: Final[dict[str, str]] = {
        "args": "parameters",
        "arguments": "parameters",
        "parameters": "parameters",
        "params": "parameters",
        "keyword args": "parameters",
        "returns": "returns",
        "yields": "yields",
        "raises": "raises",
        "exceptions": "raises",
    }
    entry_pattern: Final[Pattern[str]] = compile_pattern(
        pattern=(
            r"^\s*(\*{0,2}[\w]+)"
            r"(?:\s*\((?:[^()]|\([^()]*\))*\))?\s*:"
        ),
    )
    kinds: Final[tuple[str, ...]] = (
        "parameters",
        "returns",
        "yields",
        "raises",
    )


def documented_names(
    *,
    module: Module,
    owner: FunctionDef | AsyncFunctionDef | ClassDef,
    kind: DocKind,
) -> tuple[str | None, ...]:
    """Collect names documented under one entry kind for a definition.

    Args:
        module (Module): Parsed module (structured docstrings preferred).
        owner (FunctionDef | AsyncFunctionDef | ClassDef): Definition whose
            docstring is read.
        kind (DocKind): Entry kind: ``parameters``, ``returns``, ``yields`` or
            ``raises``.

    Returns:
        tuple[str | None, ...]: Documented names; ``None`` entries keep
            un-named
            kinds like ``returns`` /``raises`` detectable.

    """
    docstrings: list[DocstringNode] | None = getattr(
        module,
        "docstrings",
        None,
    )
    if docstrings:
        for document in docstrings:
            if document.owner is owner:
                return tuple(
                    entry.name for entry in document.entries(kind=kind)
                )
        return ()
    return _parsed_names(owner=owner, kind=kind)


def parameter_names(
    *,
    owner: FunctionDef | AsyncFunctionDef,
) -> tuple[str, ...]:
    """List a function's declared parameter names.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        tuple[str, ...]: Positional and keyword-only names, ``self`` /``cls``
            excluded.

    """
    return tuple(
        param.arg
        for param in (*owner.args.args, *owner.args.kwonlyargs)
        if param.arg not in {"self", "cls"}
    )


def owner_docstring(
    *,
    owner: ClassDef | FunctionDef | AsyncFunctionDef,
) -> str | None:
    """Return an owner's docstring, or ``None``.

    Args:
        owner (ClassDef | FunctionDef | AsyncFunctionDef): Definition to read.

    Returns:
        str | None: The docstring text.

    """
    return get_docstring(node=owner)


def _parsed_names(
    *,
    owner: FunctionDef | AsyncFunctionDef | ClassDef,
    kind: DocKind,
) -> tuple[str | None, ...]:
    """Read entry names from a docstring's Google-style sections.

    Args:
        owner (FunctionDef | AsyncFunctionDef | ClassDef): Definition whose
            docstring is read.
        kind (DocKind): Entry kind wanted.

    Returns:
        tuple[str | None, ...]: Documented names in order.

    """
    docstring: str | None = get_docstring(node=owner)
    if docstring is None:
        return ()
    parsed: DocstringNode = parse_docstring(source=docstring)
    if parsed.style in {"numpy", "rest", "epytext"}:
        return tuple(entry.name for entry in parsed.entries(kind=kind))
    names: list[str | None] = []
    active: bool = False
    for line in docstring.splitlines():
        stripped: str = line.strip()
        title: str | None = Constants.section_titles.get(
            stripped.rstrip(":").lower(),
        )
        if title is not None:
            active = title == kind
            continue
        if not active:
            continue
        if not line.startswith((" ", "\t")) and stripped:
            active = False
            continue
        match: Match[str] | None = Constants.entry_pattern.match(string=line)
        if match:
            names.append(match.group(1).lstrip("*"))
        elif kind in {"returns", "yields"} and stripped:
            names.append(None)
    return tuple(names)
