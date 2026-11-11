"""M6-05…M6-08 call-shape detectors.

Four standalone detectors over the trusted :class:`CallBindings` layer:

- ``find_missing_arguments`` — required parameters with no effective
  argument (``missing required argument`` binding errors);
- ``find_unexpected_arguments`` — keyword arguments no parameter
  accepts, or surplus positional arguments;
- ``find_ambiguous_callees`` — bindings marked ``indeterminate``
  (uncertain ``*args``/``**kwargs`` expansions);
- ``find_unresolved_callees`` — calls whose callee root is bound in the
  module yet the trusted binding refuses it (distrusted receivers,
  unsafe methods, redefinitions).

Builtins and unbound names are out of scope: project binding only
covers module-level definitions, so ``print``/``len``/unknown externals
are never flagged. Catalog wiring is deferred (M8-22).

"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    FunctionDef,
    Import,
    ImportFrom,
    Name,
    walk,
)
from typing import TYPE_CHECKING

from astart.rules.procedural import Candidate, span_of
from astart.rules.resolve import CallBindings, binding_counts

if TYPE_CHECKING:
    from astart.semantic.typing_contracts import BoundCall
    from astart.source.ast import CommentedModule


def _module_bindings(*, module: CommentedModule) -> CallBindings:
    """Trusted call bindings for the whole module, computed once.

    Args:
        module (CommentedModule): Parsed module.

    Returns:
        CallBindings: class:`CallBindings` cache.

    """
    return CallBindings(
        module=module,
        counts=binding_counts(module=module),
    )


def _callee_name(*, call: Call) -> str:
    """Best-effort dotted name of a call's callee.

    Args:
        call (Call): Call expression.

    Returns:
        str: Dotted name, or ``"?"``.

    """
    parts: list[str] = []
    cursor: AST = call.func
    while isinstance(cursor, Attribute):
        parts.append(cursor.attr)
        cursor = cursor.value
    if isinstance(cursor, Name):
        parts.append(cursor.id)
    return ".".join(reversed(parts)) if parts else "?"


def _bound_roots(*, module: CommentedModule) -> set[str]:
    """Root names bound by definitions or imports in the module.

    Args:
        module (CommentedModule): Parsed module.

    Returns:
        set[str]: Bound root identifiers.

    """
    roots: set[str] = set()
    for node in walk(node=module):
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            roots.add(node.name)
        elif isinstance(node, (Import, ImportFrom)):
            for entry in node.names:
                if isinstance(node, Import):
                    roots.add(
                        entry.asname
                        if entry.asname is not None
                        else entry.name.split(sep=".", maxsplit=1)[0],
                    )
                elif entry.name != "*":
                    roots.add(
                        entry.asname
                        if entry.asname is not None
                        else entry.name,
                    )
    return roots


def _calls(*, module: CommentedModule) -> list[Call]:
    """Every call expression in the module.

    Args:
        module (CommentedModule): Parsed module.

    Returns:
        list[Call]: Call nodes in source order.

    """
    found: list[Call] = [
        node for node in walk(node=module) if isinstance(node, Call)
    ]
    return found


def _trusted(
    *,
    bindings: CallBindings,
    call: Call,
) -> BoundCall | None:
    """Trusted binding of one call.

    Args:
        bindings (CallBindings): Shared binding cache.
        call (Call): Call expression.

    Returns:
        BoundCall | None: The binding or ``None``.

    """
    return bindings.get(call=call)


def find_missing_arguments(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag calls missing required arguments.

    Args:
        filename (str): Source name for spans.
        module (CommentedModule): Parsed module.

    Returns:
        tuple[Candidate, ...]: Candidates for each missing-argument error.

    """
    bindings: CallBindings = _module_bindings(module=module)
    candidates: list[Candidate] = []
    for call in _calls(module=module):
        bound: BoundCall | None = _trusted(bindings=bindings, call=call)
        if bound is None:
            continue
        for error in bound.errors:
            if not error.startswith("missing required argument"):
                continue
            param: str = error.split(sep="'")[1] if "'" in error else error
            candidates.append(
                Candidate(
                    span=span_of(node=call, filename=filename),
                    evidence={
                        "callee": _callee_name(call=call),
                        "parameter": param,
                        "error": error,
                    },
                ),
            )
    return tuple(candidates)


def find_unexpected_arguments(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag calls with arguments no parameter accepts.

    Args:
        filename (str): Source name for spans.
        module (CommentedModule): Parsed module.

    Returns:
        tuple[Candidate, ...]: Candidates for each unexpected-argument error.

    """
    bindings: CallBindings = _module_bindings(module=module)
    candidates: list[Candidate] = []
    for call in _calls(module=module):
        bound: BoundCall | None = _trusted(bindings=bindings, call=call)
        if bound is None:
            continue
        for error in bound.errors:
            if not (
                error.startswith(("unexpected keyword", "too many positional"))
            ):
                continue
            candidates.append(
                Candidate(
                    span=span_of(node=call, filename=filename),
                    evidence={
                        "callee": _callee_name(call=call),
                        "error": error,
                    },
                ),
            )
    return tuple(candidates)


def find_ambiguous_callees(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag calls whose binding is indeterminate.

    Indeterminate bindings come from ``*args``/``**kwargs`` expansions
    whose arity cannot be decided statically — the callee's effective
    arguments are ambiguous.

    Args:
        filename (str): Source name for spans.
        module (CommentedModule): Parsed module.

    Returns:
        tuple[Candidate, ...]: Candidates for each indeterminate binding.

    """
    bindings: CallBindings = _module_bindings(module=module)
    candidates: list[Candidate] = []
    for call in _calls(module=module):
        bound: BoundCall | None = _trusted(bindings=bindings, call=call)
        if bound is None or not bound.indeterminate:
            continue
        candidates.append(
            Candidate(
                span=span_of(node=call, filename=filename),
                evidence={
                    "callee": _callee_name(call=call),
                    "reason": "indeterminate-expansion",
                },
            ),
        )
    return tuple(candidates)


def find_unresolved_callees(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag calls whose bound callee the trusted layer refuses.

    Only callees whose root name is bound in the module are considered
    — builtins, imports of externals and unknown names cannot be
    resolved by project binding and are skipped rather than flooded.

    Args:
        filename (str): Source name for spans.
        module (CommentedModule): Parsed module.

    Returns:
        tuple[Candidate, ...]: Candidates for each unresolvable call.

    """
    roots: set[str] = _bound_roots(module=module)
    bindings: CallBindings = _module_bindings(module=module)
    candidates: list[Candidate] = []
    for call in _calls(module=module):
        cursor: AST = call.func
        while isinstance(cursor, Attribute):
            cursor = cursor.value
        if not (isinstance(cursor, Name) and cursor.id in roots):
            continue
        if _trusted(bindings=bindings, call=call) is not None:
            continue
        candidates.append(
            Candidate(
                span=span_of(node=call, filename=filename),
                evidence={"callee": _callee_name(call=call)},
            ),
        )
    return tuple(candidates)
