"""Build an annotated copy of a converted module, for line-by-line review.

The copy is the converted code with ``# [FIX]`` comments on the lines that
differ from the author's typed module and ``# [ADD]`` comments for imports and
definitions the typed module has and the converted one lacks. Everything is
read from the AST of the two modules; the comments' reasons come from the
caller.

Used by ``scripts/conversion_report.py``.
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Module,
    Name,
    TypeAlias,
    arg,
    parse,
    stmt,
    unparse,
    walk,
)
from collections import defaultdict
from typing import Final, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        protocol_reason: Why a class stays a plain class.
        bases_reason: Reason for any other header difference.
        limit: Longest generated comment, in characters.

    """

    protocol_reason: Final[str] = (
        "the author's file declares it a structural Protocol; astart "
        "synthesizes Protocols for parameters (M5-09, M5-04) but does not "
        "turn existing classes into Protocols"
    )
    bases_reason: Final[str] = (
        "the base classes or keywords differ from the author's"
    )
    limit: Final[int] = 320


def shorten(*, text: str) -> str:
    """Cut a comment to the length limit.

    Args:
        text: Comment text.

    Returns:
        The text, ending with an ellipsis when it was cut.

    """
    limit: int = Constants.limit
    return text if len(text) <= limit else text[: limit - 1] + "…"


def header_of(*, node: ClassDef) -> str:
    """Render the header line of a class.

    Args:
        node: A class definition.

    Returns:
        For example ``class A(Base, metaclass=Meta):``.

    """
    parts: list[str] = [unparse(ast_obj=base) for base in node.bases]
    parts.extend(
        f"{keyword.arg}={unparse(ast_obj=keyword.value)}"
        if keyword.arg
        else f"**{unparse(ast_obj=keyword.value)}"
        for keyword in node.keywords
    )
    params: str = (
        "["
        + ", ".join(
            unparse(ast_obj=param) for param in node.type_params
        )
        + "]"
        if node.type_params
        else ""
    )
    bases: str = f"({', '.join(parts)})" if parts else ""
    return f"class {node.name}{params}{bases}:"


def _classes(*, source: str) -> dict[str, tuple[int, str]]:
    """Index the classes of a module by qualified path.

    Args:
        source: Python source.

    Returns:
        Line and header text by qualified class path.

    """
    found: dict[str, tuple[int, str]] = {}

    def visit(*, body: list[AST], trail: tuple[str, ...]) -> None:
        """Collect class headers, descending into nested scopes.

        Args:
            body: Statements of the current scope.
            trail: Qualified name path of the enclosing scopes.

        """
        for node in body:
            if isinstance(node, ClassDef):
                key: str = ".".join((*trail, node.name))
                found[key] = (node.lineno, header_of(node=node))
                visit(body=list(node.body), trail=(*trail, node.name))
            elif isinstance(node, (FunctionDef, AsyncFunctionDef)):
                visit(body=list(node.body), trail=(*trail, node.name))

    visit(body=list(parse(source=source).body), trail=())
    return found


def header_flags(*, typed: str, converted: str) -> list[tuple[int, str]]:
    """Flag classes whose header differs from the author's.

    Args:
        typed: The author's typed source.
        converted: The converted source.

    Returns:
        ``(line in the converted source, comment)`` pairs.

    """
    theirs: dict[str, tuple[int, str]] = _classes(source=typed)
    mine: dict[str, tuple[int, str]] = _classes(source=converted)
    flags: list[tuple[int, str]] = []
    for key, (line, header) in mine.items():
        wanted: tuple[int, str] | None = theirs.get(key)
        if wanted is None or wanted[1] == header:
            continue
        reason: str = (
            Constants.protocol_reason
            if "Protocol" in wanted[1] and "Protocol" not in header
            else Constants.bases_reason
        )
        flags.append(
            (
                line,
                shorten(
                    text=f"[FIX] {wanted[1]} - {reason} "
                    f"(typed.py:{wanted[0]})",
                ),
            ),
        )
    return flags


def _imports(*, source: str) -> dict[str, set[str]]:
    """Collect the names a module imports with ``from ... import``.

    Args:
        source: Python source.

    Returns:
        Imported names by module text.

    """
    found: dict[str, set[str]] = defaultdict(set)
    for node in walk(node=parse(source=source)):
        if isinstance(node, ImportFrom):
            module: str = "." * node.level + (node.module or "")
            for alias in node.names:
                found[module].add(
                    alias.name
                    if alias.asname is None
                    else f"{alias.name} as {alias.asname}",
                )
    return found


def _defined(*, body: list[stmt]) -> dict[str, stmt]:
    """Collect the names defined at the top level of a module.

    Args:
        body: Module statements.

    Returns:
        The defining statement by name.

    """
    found: dict[str, stmt] = {}
    for node in body:
        if isinstance(node, (ClassDef, FunctionDef, AsyncFunctionDef)):
            found[node.name] = node
        elif isinstance(node, Assign):
            for target in node.targets:
                if isinstance(target, Name):
                    found[target.id] = node
        elif isinstance(node, AnnAssign) and isinstance(node.target, Name):
            found[node.target.id] = node
        elif isinstance(node, TypeAlias):
            found[node.name.id] = node
    return found


def _definition_text(*, node: AST) -> str:
    """Render a definition on one line.

    Args:
        node: A top-level definition.

    Returns:
        The class header, the function signature, or the statement.

    """
    if isinstance(node, ClassDef):
        return header_of(node=node) + " ..."
    if isinstance(node, (FunctionDef, AsyncFunctionDef)):
        returns: str = (
            f" -> {unparse(ast_obj=node.returns)}"
            if node.returns
            else ""
        )
        return f"def {node.name}({unparse(ast_obj=node.args)}){returns}: ..."
    return " ".join(unparse(ast_obj=node).split())


def _first_use(*, tree: AST, name: str, after: int) -> int | None:
    """Find the first line that uses a name after its definition.

    Args:
        tree: A module.
        name: The name.
        after: Last line of the definition.

    Returns:
        The line, or ``None`` when the name is not used later.

    """
    lines: list[int] = [
        node.lineno
        for node in walk(node=tree)
        if isinstance(node, Name) and node.id == name and node.lineno > after
    ]
    return min(lines) if lines else None


def _annotation_names(*, tree: AST) -> dict[str, int]:
    """Find the names that appear inside annotations and class bases.

    Args:
        tree: A module.

    Returns:
        The first line of each such name.

    """
    names: dict[str, int] = {}
    for node in walk(node=tree):
        found: list[AST] = []
        if isinstance(node, arg) and node.annotation is not None:
            found.append(node.annotation)
        elif (
            isinstance(node, (FunctionDef, AsyncFunctionDef)) and node.returns
        ):
            found.append(node.returns)
        elif isinstance(node, AnnAssign):
            found.append(node.annotation)
        elif isinstance(node, ClassDef):
            found.extend(node.bases)
        for annotation in found:
            for inner in walk(node=annotation):
                if isinstance(inner, Name):
                    names.setdefault(inner.id, inner.lineno)
    return names


def additions(*, typed: str, converted: str) -> list[str]:
    """List what the typed module has and the converted one lacks.

    Args:
        typed: The author's typed source.
        converted: The converted source.

    Returns:
        ``[ADD]`` comment texts: missing imports first, then definitions.

    """
    adds: list[str] = []
    mine: dict[str, set[str]] = _imports(source=converted)
    tree_for_names: Module = parse(source=typed)
    used: dict[str, int] = _annotation_names(tree=tree_for_names)
    for module, names in sorted(_imports(source=typed).items()):
        missing: set[str] = names - mine.get(module, set())
        in_annotations: list[str] = sorted(
            n for n in missing if n.partition(" as ")[0] in used
        )
        for_code: list[str] = sorted(missing - set(in_annotations))
        if in_annotations:
            first: int = min(
                used[n.partition(" as ")[0]] for n in in_annotations
            )
            adds.append(
                shorten(
                    text=f"[ADD] from {module} import "
                    f"{', '.join(in_annotations)} - used in the author's "
                    f"annotations (first at typed.py:{first})",
                ),
            )
        if for_code:
            adds.append(
                shorten(
                    text=f"[ADD] from {module} import "
                    f"{', '.join(for_code)} - the author's file imports "
                    "these for code, not for annotations (its from-import "
                    "style; see M8-27)",
                ),
            )
    tree: Module = parse(source=typed)
    have: dict[str, stmt] = _defined(body=list(parse(source=converted).body))
    for name, node in _defined(body=list(tree.body)).items():
        if name in have:
            continue
        end: int = node.end_lineno or node.lineno
        use: int | None = _first_use(tree=tree, name=name, after=end)
        where: str = (
            f"first used at typed.py:{use}" if use else "not used later"
        )
        adds.append(
            shorten(
                text=f"[ADD] {_definition_text(node=node)} - defined at "
                f"typed.py:{node.lineno}; {where}",
            ),
        )
    return adds


def _import_end(*, source: str) -> int:
    """Find the last line of the module's import block.

    Args:
        source: Python source.

    Returns:
        The last line of the final top-level import (or ``TYPE_CHECKING``
        block); 0 when there are none.

    """
    last: int = 0
    for node in parse(source=source).body:
        is_block: bool = (
            isinstance(node, If)
            and isinstance(node.test, Name)
            and node.test.id == "TYPE_CHECKING"
        )
        if isinstance(node, (Import, ImportFrom)) or is_block:
            last = max(last, node.end_lineno or node.lineno)
    return last


def render(
    *,
    converted: str,
    flags: dict[int, list[str]],
    adds: list[str],
) -> str:
    """Produce the annotated copy.

    Args:
        converted: The converted source.
        flags: Comments by line of the converted source.
        adds: ``[ADD]`` comment texts, placed after the import block.

    Returns:
        The converted code with the comments added.

    """
    lines: list[str] = converted.splitlines()
    for number, texts in flags.items():
        if 1 <= number <= len(lines):
            lines[number - 1] = (
                lines[number - 1].rstrip() + "  # " + " | ".join(texts)
            )
    anchor: int = _import_end(source=converted)
    lines[anchor:anchor] = [f"# {text}" for text in adds]
    return "\n".join(lines) + "\n"
