"""Generate ``src/astart/rules/libkw.py`` from typeshed stubs.

Walks a typeshed root — the first one ``astart.stubs.find_typeshed`` finds by
default — and emits a deterministic data module mapping every qualified callee
to the parameter names that may be passed by keyword: positional-or-keyword
and keyword-only parameters, never positional-only ones (``/`` markers
and ``__name`` convention), never ``self``/``cls`` receivers.  Callees
carrying ``**kwargs`` are marked as accepting arbitrary keywords.

Stdlib entries come first; third-party packages are only included when
their top-level module is in ``THIRD_PARTY``.

Usage::

    python3 scripts/generate_libkw.py [typeshed-root] > out.py
"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    Module,
    arg,
    parse,
    stmt,
)
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from sys import argv, stdout
from typing import Final, final


@final
class Constants:
    """Constants for the library keyword generator.

    Attributes:
        line_lenght: Width a rendered signature entry may occupy.
        header: Docstring written at the top of the generated module.

    """

    line_lenght: Final[int] = 79

    header: Final[str] = '''"""Typeshed-generated library keyword-safety table.

``SIGNATURES`` maps ``"module.qualname"`` to the parameter names a call
may pass by keyword.  ``names`` lists keyword-passable parameters
(positional-or-keyword and keyword-only); positional-only parameters
never appear there: ``/`` markers and the ``__name`` convention are
excluded, as are ``self`` and ``cls`` receivers.  ``positional`` lists
every parameter a positional argument can fill, in order (positional-only
included).  ``ANY_KEYWORD``/``var_positional`` mark ``**kwargs``/``*args``.

Stdlib entries come first; third-party modules join only through an
explicit allow-list.  Regenerate with ``scripts/generate_libkw.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final


@final
@dataclass(frozen=True, slots=True)
class KwSignature:
    """Keyword-passable parameters of one library callee.

    Attributes:
        names: Parameters that accept a keyword, in signature order.
        any_keyword: Whether ``**kwargs`` accepts arbitrary names.
        positional: Parameters a positional argument can fill, in order.
        var_positional: Whether ``*args`` absorbs extra positionals.

    """

    names: tuple[str, ...]
    any_keyword: bool
    positional: tuple[str, ...]
    var_positional: bool


def keyword_names(*, callee: str) -> tuple[str, ...] | None:
    """Look up the keyword-passable parameters of a callee.

    Args:
        callee: Qualified ``module.name`` key.

    Returns:
        The keyword-passable parameter names, or ``None`` when the
        callee is not in the table.

    """
    signature: KwSignature | None = SIGNATURES.get(callee)
    return None if signature is None else signature.names


def accepts_keyword(*, callee: str, name: str) -> bool:
    """Answer whether ``callee`` accepts ``name`` by keyword.

    Args:
        callee: Qualified ``module.name`` key.
        name: Parameter name the call would pass.

    Returns:
        ``True`` when the name is keyword-passable or the callee takes
        ``**kwargs``; ``False`` for unknown callees.

    """
    signature: KwSignature | None = SIGNATURES.get(callee)
    return signature is not None and (
        signature.any_keyword or name in signature.names
    )


'''


def _qualname(*, module: str, parents: tuple[str, ...], name: str) -> str:
    """Join a module and a dotted qualified name.

    Args:
        module: Module the name lives in.
        parents: Enclosing qualified names, outermost first.
        name: Leaf name.

    Returns:
        The dotted callee name.

    """
    return (
        f"{module}.{'.'.join(parents)}.{name}"
        if parents
        else (f"{module}.{name}")
    )


def _posonly(*, function: FunctionDef | AsyncFunctionDef) -> set[int]:
    """Identify positional-only parameters of a stub signature.

    ``/`` markers populate ``posonlyargs``; the typeshed ``__name``
    convention marks positional intent where ``/`` cannot.

    Args:
        function: Function node from the stub.

    Returns:
        ``id``s of parameters never passable by keyword.

    """
    excluded: set[int] = {id(param) for param in function.args.posonlyargs}
    excluded.update(
        id(param)
        for param in [*function.args.args, *function.args.kwonlyargs]
        if param.arg.startswith("__")
    )
    return excluded


def collect(
    *,
    root: Path,
) -> dict[str, tuple[tuple[str, ...], bool, tuple[str, ...], bool]]:
    """Collect keyword signatures from every stub under a root.

    Args:
        root: Typeshed directory containing stdlib stubs.

    Returns:
        Qualified callee to ``(names, any_keyword)``.

    """
    table: dict[str, tuple[tuple[str, ...], bool, tuple[str, ...], bool]] = {}
    for stub in sorted(root.rglob(pattern="*.pyi")):
        module: str = ".".join(
            stub.relative_to(root).with_suffix(suffix="").parts,
        )
        module = module.removesuffix(".__init__")
        try:
            tree: Module = parse(source=stub.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        _walk_body(
            body=tree.body,
            module=module,
            parents=(),
            table=table,
        )
    return table


def _walk_body(
    *,
    body: list[stmt],
    module: str,
    parents: tuple[str, ...],
    table: dict[str, tuple[tuple[str, ...], bool, tuple[str, ...], bool]],
) -> None:
    """Walk a stub body, recording functions and recursing into classes.

    Args:
        body: Statements of a module or class body.
        module: Dotted module name.
        parents: Enclosing class names.
        table: Accumulating signature table.

    """
    for node in body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            excluded: set[int] = _posonly(function=node)
            params: list[arg] = [*node.args.args, *node.args.kwonlyargs]
            names: tuple[str, ...] = tuple(
                param.arg
                for param in params
                if id(param) not in excluded
                and param.arg not in {"self", "cls"}
            )
            positional: tuple[str, ...] = tuple(
                param.arg
                for param in [*node.args.posonlyargs, *node.args.args]
                if param.arg not in {"self", "cls"}
            )
            table[
                _qualname(module=module, parents=parents, name=node.name)
            ] = (
                names,
                node.args.kwarg is not None,
                positional,
                node.args.vararg is not None,
            )
        elif isinstance(node, ClassDef):
            _walk_body(
                body=node.body,
                module=module,
                parents=(*parents, node.name),
                table=table,
            )


def _key_literal(*, key: str) -> str:
    """Render a dict key, splitting long literals across lines.

    Args:
        key: The qualified callee name.

    Returns:
        A string literal expression that fits the line limit.

    """
    literal: str = repr(key)
    if len(f"    {literal}: KwSignature(") <= Constants.line_lenght:
        return literal
    width: int = 56
    return "\n    ".join(
        repr(key[start : start + width]) for start in range(0, len(key), width)
    )


def main() -> int:
    """Generate the data module to stdout.

    Returns:
        Process exit status; ``0`` on success.

    """
    root: Path
    if len(argv) > 1:
        root = Path(argv[1])
    else:
        client_file: str | None = __import__("typeshed_client").__file__
        root = (
            Path(client_file).parent / "typeshed"
            if client_file is not None
            else Path("typeshed")
        )
    table: dict[str, tuple[tuple[str, ...], bool, tuple[str, ...], bool]] = (
        collect(root=root)
    )
    lines: list[str] = [
        Constants.header,
        "SIGNATURES: Final[dict[str, KwSignature]] = {\n",
    ]
    for key in sorted(table):
        names, any_kw, positional, var_pos = table[key]
        rendered: str = (
            f"({', '.join(repr(name) for name in names)})"
            if len(names) != 1
            else f"({names[0]!r},)"
        )
        positional_rendered: str = (
            f"({', '.join(repr(name) for name in positional)})"
            if len(positional) != 1
            else f"({positional[0]!r},)"
        )
        entry: str = (
            f"    {key!r}: KwSignature(names={rendered}, "
            f"any_keyword={any_kw!r}, positional={positional_rendered}, "
            f"var_positional={var_pos!r}),\n"
        )
        if len(entry) - 1 <= Constants.line_lenght:
            lines.append(entry)
            continue
        lines.append(
            f"    {_key_literal(key=key)}: KwSignature(\n"
            f"        names={rendered},\n"
            f"        any_keyword={any_kw!r},\n"
            f"        positional={positional_rendered},\n"
            f"        var_positional={var_pos!r},\n"
            f"    ),\n",
        )
    lines.append("}\n")
    try:
        client_version: str = version(distribution_name="typeshed_client")
    except PackageNotFoundError:
        client_version = "unknown"
    lines.append(
        f"\n# Generated by scripts/generate_libkw.py "
        f"on {datetime.now(tz=UTC).isoformat()}\n"
        f"# from {root} using typeshed_client {client_version}.\n",
    )
    stdout.write("".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
