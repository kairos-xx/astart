"""Every name documented in ``docs/guides/API.md`` must resolve."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Final, final

from astart import CommentedModule, __all__

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from ast import AST
    from pathlib import Path
    from types import ModuleType


astart: ModuleType = import_module(name="astart")


@final
class Constants:
    """Shared fixtures for the API surface check.

    Attributes:
        root (Final[Path]): Repository root directory.
        api_doc (Final[Path]): The documented public surface.
        probe_source (Final[str]): Minimal module used to bind ``module``
            paths.
        public_names (Final[tuple[str, ...]]): Pinned snapshot of
            ``astart.__all__``.

    """

    root: Final[Path] = Paths.root
    api_doc: Final[Path] = root / "docs" / "guides" / "API.md"
    probe_source: Final[str] = """\
x = 1
"""
    public_names: Final[tuple[str, ...]] = (
        "AST",
        "AnalysisBudgets",
        "Args",
        "ArgumentSpec",
        "BoundArgument",
        "BoundCall",
        "CallableContract",
        "Comment",
        "CommentGroup",
        "CommentedModule",
        "ContractDiagnostic",
        "DocDescription",
        "DocEntry",
        "DocSection",
        "DocStyle",
        "DocSummary",
        "DocstringNode",
        "FileOutcome",
        "FormatPreservationError",
        "GraphAnnotation",
        "GraphConversion",
        "LexicalToken",
        "Module",
        "ModuleDocstringNode",
        "MultilineComment",
        "ParameterContract",
        "ParameterKind",
        "ProtocolSpec",
        "SemanticAnalyzer",
        "Settings",
        "ShebangNode",
        "SingleLineComment",
        "SourceSpan",
        "SuppressionComment",
        "SuppressionRule",
        "TokenSnapshot",
        "TypeEvidence",
        "TypeExpression",
        "TypeExpressionCodec",
        "TypeHintCatalog",
        "TypeInference",
        "TypeShape",
        "Types",
        "ValueEvidence",
        "check_source",
        "convert",
        "fix_file",
        "fix_paths",
        "fix_source",
        "parse",
        "unparse",
    )


def _table_rows(*, text: str) -> list[str]:
    """Return the table rows that mention a backticked name.

    Args:
        text (str): Markdown document text.

    Returns:
        list[str]: Rows of the API table containing backticks.

    """
    return [
        line
        for line in text.splitlines()
        if line.startswith("|") and "`" in line and "Public API" not in line
    ]


def _backtick_spans(*, text: str) -> list[str]:
    """Return the contents of each `` `...` `` span in ``text``.

    Args:
        text (str): One table row.

    Returns:
        list[str]: Span contents in order.

    """
    spans: list[str] = []
    rest: str = text
    while "`" in rest:
        _, _, rest = rest.partition("`")
        span, _, rest = rest.partition("`")
        if span:
            spans.append(span)
    return spans


def _api_names(*, span: str) -> list[str]:
    """Expand one backtick span into documented API paths.

    Args:
        span (str): Raw backtick contents, call arguments allowed.

    Returns:
        list[str]: ``module.`` /``node.``/bare paths; ``/`` joins share a
            prefix and non-API mentions such as ``.pyi`` are dropped.

    """
    base: str = span.partition("(")[0].strip()
    if not base or base.startswith("."):
        return []
    segments: list[str] = base.split(sep="/")
    first: str = segments[0].strip()
    stem: str = ""
    if "." in first:
        stem = f"{first.rsplit(sep='.', maxsplit=1)[0]}."
    names: list[str] = [first] if first else []
    names.extend(f"{stem}{part.strip()}" for part in segments[1:])
    return [name for name in names if name]


def _resolve(*, dotted: str, tree: CommentedModule, node: AST) -> object:
    """Resolve a documented ``module.``/``node.``/bare path.

    Args:
        dotted (str): Documented name, call arguments already stripped.
        tree (CommentedModule): Live module instance behind ``module`` paths.
        node (AST): Live AST node behind ``node`` paths.

    Returns:
        object: The resolved attribute or module member.

    """
    parts: list[str] = dotted.split(sep=".")
    target: object
    if parts[0] == "module":
        target = tree
        parts = parts[1:]
    elif parts[0] == "node":
        target = node
        parts = parts[1:]
    else:
        target = astart
    for part in parts:
        target = getattr(target, part)
    return target


def test_api_surface_matches_documentation() -> None:
    """Every documented API name resolves on the real objects."""
    tree: CommentedModule = CommentedModule.parse(
        source=Constants.probe_source,
    )
    node: AST = tree.body[0]
    missing: list[str] = []
    not_callable: list[str] = []
    text: str = Constants.api_doc.read_text(encoding="utf-8")
    for row in _table_rows(text=text):
        context: object = astart
        for span in _backtick_spans(text=row):
            wants_call: bool = "(" in span
            for name in _api_names(span=span):
                target: object | None = None
                if "." in name:
                    target = _resolve(dotted=name, tree=tree, node=node)
                    if name == "module.semantic.symbols":
                        context = target
                else:
                    found: bool = False
                    for base in (context, astart):
                        if hasattr(base, name):
                            target = getattr(base, name)
                            found = True
                            break
                    if not found:
                        missing.append(f"{name} ({span})")
                        continue
                label: str = f"{name} ({span})"
                if wants_call and not callable(target):
                    not_callable.append(label)
    expect_equal(actual=missing, expected=[])
    expect_equal(actual=not_callable, expected=[])


def test_all_matches_the_pinned_public_surface() -> None:
    """``astart.__all__`` is pinned; changes need an explicit test edit."""
    expect_equal(
        actual=tuple(sorted(__all__)),
        expected=Constants.public_names,
    )
