"""Complete structured documentation from native function annotations."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    FunctionDef,
    ImportFrom,
    Name,
    Raise,
    Subscript,
    expr,
    unparse,
    walk,
)
from typing import TYPE_CHECKING

from astart.docstrings import (
    Constants,
    DocEntry,
    DocSection,
    function_body_nodes,
    generator_result_annotation,
    wrapped_label_lines,
)
from astart.docstrings.missing_returns import result_kinds

if TYPE_CHECKING:
    from re import Match

    from astart import CommentedModule
    from astart.docstrings import DocKind, DocstringNode
    from astart.rules.facts import ModuleFacts, Subject
    from astart.rules.predicate import FactValue
    from astart.semantic.identities import Symbol


def desired_entries(
    *,
    owner: FunctionDef | AsyncFunctionDef,
    module: CommentedModule | None = None,
) -> list[DocEntry]:
    """Build typed TODO entries from an owner's executable AST.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Function whose own body and
            annotations supply evidence.
        module (CommentedModule | None): Shared source graph for import-symbol
            resolution.

    Returns:
        list[DocEntry]: Parameter, result and explicit exception entries in
            source order.

    """
    entries: list[DocEntry] = []
    for argument in (
        *owner.args.posonlyargs,
        *owner.args.args,
        *([owner.args.vararg] if owner.args.vararg is not None else []),
        *owner.args.kwonlyargs,
        *([owner.args.kwarg] if owner.args.kwarg is not None else []),
    ):
        if argument.arg in {"self", "cls"}:
            continue
        entries.append(
            DocEntry(
                kind="parameters",
                name=argument.arg,
                type_name=(
                    unparse(ast_obj=argument.annotation)
                    if argument.annotation is not None
                    else None
                ),
                description=Constants.todo_placeholder,
            ),
        )
    kinds: tuple[DocKind, ...] = result_kinds(node=owner)
    for kind in kinds:
        annotation: expr | None = (
            generator_result_annotation(
                owner=owner,
                kind=kind,
                constructor_name=_constructor(owner=owner, module=module),
            )
            if "yields" in kinds
            else owner.returns
        )
        entries.append(
            DocEntry(
                kind=kind,
                type_name=unparse(ast_obj=annotation) if annotation else None,
                description=Constants.todo_placeholder,
            ),
        )
    exceptions: set[str] = set()
    for node in function_body_nodes(owner=owner):
        if not isinstance(node, Raise) or node.exc is None:
            continue
        exception: expr = (
            node.exc.func if isinstance(node.exc, Call) else node.exc
        )
        if not isinstance(exception, (Name, Attribute)):
            continue
        name: str = unparse(ast_obj=exception)
        if name not in exceptions:
            exceptions.add(name)
            entries.append(
                DocEntry(
                    kind="raises",
                    name=name,
                    description=Constants.todo_placeholder,
                ),
            )
    return entries


def desired_attributes(*, owner: ClassDef) -> list[DocEntry]:
    """Build typed TODO entries from a class body's annotated assignments.

    Args:
        owner (ClassDef): Class whose class-level annotations supply evidence.

    Returns:
        list[DocEntry]: Attribute entries in class-body order.

    """
    entries: list[DocEntry] = []
    for statement in owner.body:
        if not (
            isinstance(statement, AnnAssign)
            and isinstance(statement.target, Name)
        ):
            continue
        entries.append(
            DocEntry(
                kind="attributes",
                name=statement.target.id,
                type_name=unparse(ast_obj=statement.annotation),
                description=Constants.todo_placeholder,
            ),
        )
    return entries


def _constructor(
    *,
    owner: FunctionDef | AsyncFunctionDef,
    module: CommentedModule | None,
) -> str | None:
    """Resolve generator import aliases through the shared symbol registry.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Annotated generator.
        module (CommentedModule | None): Owning source graph, when available.

    Returns:
        str | None: Canonical imported constructor name, or no override.

    """
    annotation: expr | None = owner.returns
    if module is None or not isinstance(annotation, Subscript):
        return None
    base: expr = annotation.value
    if not isinstance(base, Name):
        return None
    symbol: Symbol | None = module.semantic.symbol(node=base)
    if symbol is None or symbol.kind != "import":
        return None
    for statement in walk(node=module):
        if not isinstance(statement, ImportFrom) or statement.module not in {
            "typing",
            "typing_extensions",
            "collections.abc",
        }:
            continue
        for imported in statement.names:
            if module.semantic.symbol(node=imported) == symbol:
                return imported.name
    return None


def _uneditable(*, document: DocstringNode) -> bool:
    """Keep mixed syntax and pending legacy constant edits untouched.

    Args:
        document (DocstringNode): Shared structured documentation.

    Returns:
        bool: Whether another edit must settle before structural changes.

    """
    return document.style == "mixed" or (
        document.expression is not None
        and isinstance(document.expression.value, Constant)
        and document.expression.value.value != document.raw
    )


def _migrate_yields(
    *,
    document: DocstringNode,
    owner: FunctionDef | AsyncFunctionDef,
    apply: bool,
) -> bool:
    """Move legacy generator result prose to the yielded-value section.

    Args:
        document (DocstringNode): Native documentation.
        owner (FunctionDef | AsyncFunctionDef): Generator definition.
        apply (bool): Whether to commit section changes.

    Returns:
        bool: Whether a legacy section needs migration.

    """
    changed: bool = False
    kinds: tuple[DocKind, ...] = result_kinds(node=owner)
    if kinds == ("yields",) and not document.entries(kind="yields"):
        for section in document.sections:
            if section.kind == "returns":
                changed = True
                if apply:
                    section.kind = "yields"
                    section.title = "Yields"
                    for entry in section.entries:
                        entry.kind = "yields"
    return changed


def _wanted(*, owner: AST, facts: ModuleFacts) -> list[DocEntry] | None:
    """Collect the typed entries an owner owes its documentation.

    Args:
        owner (AST): Subject node; functions and classes are supported.
        facts (ModuleFacts): Module graph for import-symbol resolution.

    Returns:
        list[DocEntry] | None: Desired entries, or ``None`` for other owners.

    """
    if isinstance(owner, (FunctionDef, AsyncFunctionDef)):
        return desired_entries(owner=owner, module=facts.module)
    if isinstance(owner, ClassDef):
        return desired_attributes(owner=owner)
    return None


def _migrate(
    *,
    document: DocstringNode,
    owner: AST,
    apply: bool,
) -> bool:
    """Run owner-specific section migrations before entry updates.

    Args:
        document (DocstringNode): Native documentation.
        owner (AST): Subject node; only functions yield sections.
        apply (bool): Whether to commit section changes.

    Returns:
        bool: Whether a legacy section needs migration.

    """
    if isinstance(owner, (FunctionDef, AsyncFunctionDef)):
        return _migrate_yields(document=document, owner=owner, apply=apply)
    return False


def _update(*, subject: Subject, facts: ModuleFacts, apply: bool) -> bool:
    """Plan or apply documentation changes on the shared docstring AST.

    Args:
        subject (Subject): Function or class subject.
        facts (ModuleFacts): Module and generation preferences.
        apply (bool): Whether to mutate the native documentation fields.

    Returns:
        bool: Whether any field needs changing.

    """
    owner: AST = subject.node
    if (
        (
            not facts.docstring_types
            or (wanted := _wanted(owner=owner, facts=facts)) is None
        )
        or (
            document := next(
                (
                    item
                    for item in facts.module.docstrings
                    if item.owner is owner
                ),
                None,
            )
        )
        is None
        or _uneditable(document=document)
    ):
        return False

    changed: bool = _migrate(document=document, owner=owner, apply=apply)
    for desired in wanted:
        existing: DocEntry | None = next(
            (
                entry
                for entry in document.entries(kind=desired.kind)
                if (entry.name or "").lstrip("*") == (desired.name or "")
            ),
            None,
        )
        if existing is not None:
            if desired.type_name and existing.type_name != desired.type_name:
                changed = True
                if apply:
                    existing.type_name = desired.type_name
            continue
        changed = True
        if apply:
            _section_for(document=document, desired=desired).entries.append(
                desired,
            )
    over_budget: bool = not changed and _labels_over_budget(
        document=document,
    )
    if (changed or over_budget) and apply:
        document.layout.preserve_original = False
        document.layout.is_trailing_blank = True
        document.link()
    return changed or over_budget


def _labels_over_budget(*, document: DocstringNode) -> bool:
    """Tell whether a physical docstring line is a wrappable entry label.

    The check inspects rendered lines rather than the flat label: once
    the label is wrapped every physical line fits, so the predicate
    converges instead of firing on every pass.

    Args:
        document (DocstringNode): Native documentation.

    Returns:
        bool: Whether an over-budget entry label can be type-wrapped.

    """
    if document.style not in ("google", "pep257"):
        return False
    budget: int = Constants.line_length - document.col_offset
    for line in document.raw.splitlines():
        if len(line) <= Constants.line_length:
            continue
        stripped: str = line.strip()
        match: Match[str] | None = Constants.google_entry.match(
            string=stripped,
        )
        if match is None:
            continue
        label: str = match.group(1).strip()
        if len(f"    {label}:") <= budget:
            continue
        if wrapped_label_lines(label=label, budget=budget) is not None:
            return True
    return False


def _section_for(*, document: DocstringNode, desired: DocEntry) -> DocSection:
    """Return the section a desired entry belongs to, creating it if absent.

    Args:
        document (DocstringNode): Native documentation to search.
        desired (DocEntry): Entry whose kind names the section.

    Returns:
        DocSection: Existing or newly appended section.

    """
    section: DocSection | None = next(
        (
            item
            for item in document.sections
            if item.kind == desired.kind
            and not (
                desired.kind == "attributes"
                and item.title.strip().rstrip(":").lower() == "methods"
            )
        ),
        None,
    )
    if section is None:
        title: str = (
            "Args"
            if desired.kind == "parameters"
            else desired.kind.capitalize()
        )
        section = DocSection(kind=desired.kind, title=title, entries=[])
        document.sections.append(section)
    return section


def _legacy_work(
    *,
    document: DocstringNode,
    owner: FunctionDef | AsyncFunctionDef,
) -> bool:
    """Defer structural repairs to their existing catalog rules.

    Args:
        document (DocstringNode): Existing native documentation.
        owner (FunctionDef | AsyncFunctionDef): Function definition.

    Returns:
        bool: Whether a parameter or generator rule owns the pending repair.

    """
    desired: list[DocEntry] = desired_entries(owner=owner)
    declared: set[str | None] = {
        item.name for item in desired if item.kind == "parameters"
    }
    documented: set[str] = {
        (item.name or "").lstrip("*")
        for item in document.entries(kind="parameters")
        if item.name not in {"self", "cls"}
    }
    kinds: tuple[DocKind, ...] = result_kinds(node=owner)
    return (
        document.style in {"google", "pep257"} and declared != documented
    ) or (
        "yields" in kinds
        and any(not document.entries(kind=kind) for kind in kinds)
    )


def needs_types(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Find missing or stale documentation types.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Module facts.

    Returns:
        FactValue: Whether native documentation needs completion.

    """
    owner: AST = subject.node
    if isinstance(owner, (FunctionDef, AsyncFunctionDef)):
        document: DocstringNode | None = next(
            (item for item in facts.module.docstrings if item.owner is owner),
            None,
        )
        if document is not None and _legacy_work(
            document=document,
            owner=owner,
        ):
            return False
    return _update(subject=subject, facts=facts, apply=False)


def add_types(subject: Subject, facts: ModuleFacts) -> None:
    """Complete native docstring fields, preserving existing prose.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Module facts.

    """
    _ = _update(subject=subject, facts=facts, apply=True)
