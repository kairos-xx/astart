"""Staged annotation and import edits with guarded in-place rollback."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    Constant,
    Del,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    MatchMapping,
    Name,
    ParamSpec,
    Store,
    TypeAlias,
    TypeVar,
    alias,
    arg,
    boolop,
    cmpop,
    copy_location,
    dump,
    expr,
    expr_context,
    fix_missing_locations,
    iter_child_nodes,
    iter_fields,
    keyword,
    operator,
    stmt,
    unaryop,
    walk,
)
from builtins import __dict__
from dataclasses import dataclass
from keyword import iskeyword
from typing import TYPE_CHECKING, Final, final
from unicodedata import normalize

from astart.source.node_attributes import read_attribute

if TYPE_CHECKING:
    from astart.docstrings import DocEntry
    from astart.source.ast import CommentedModule
    from astart.source.formatting import FieldValue


type _TreeState = tuple[
    str,
    tuple[int, ...],
    tuple[tuple[int, str], ...],
    tuple[tuple[int, str, int], ...],
]


def _identifier(*, name: str) -> bool:
    """Check that an AST identifier survives source spelling unchanged.

    Args:
        name (str): Proposed native identifier.

    Returns:
        bool: Whether Python can spell this identifier without normalization.

    """
    return (
        name.isidentifier()
        and not iskeyword(name)
        and normalize("NFKC", name) == name
    )


@final
class Constants:
    """Mutation boundaries for annotation and dependency edits.

    Attributes:
        locations (Final[tuple[str, ...]]): Location attributes temporarily
            filled for compilation.
        shared (Final[tuple[type[AST], ...]]): Interpreter-owned structural
            singleton node families.

    """

    locations: Final[tuple[str, ...]] = (
        "lineno",
        "col_offset",
        "end_lineno",
        "end_col_offset",
    )
    shared: Final[tuple[type[AST], ...]] = (
        operator,
        unaryop,
        boolop,
        cmpop,
        expr_context,
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Edit:
    """One staged field replacement retaining exact original references.

    Attributes:
        owner (AST): Existing owned annotation container.
        field (str): Annotation or return field.
        before (expr | None): Original annotation reference.
        after (expr | None): Proposed annotation reference.

    """

    owner: AST
    field: str
    before: expr | None
    after: expr | None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Location:
    """Original location state of a proposed, unattached syntax node.

    Attributes:
        node (AST): Proposed annotation node.
        field (str): Location attribute.
        present (bool): Whether the attribute existed before validation.
        value (int | None): Original integer coordinate or None.

    """

    node: AST
    field: str
    present: bool
    value: int | None


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Link:
    """Original derived documentation link, restored if commit fails.

    Attributes:
        entry (DocEntry): Existing semantic documentation entry.
        target (AST | None): Original linked executable node.
        role (str | None): Original link category.

    """

    entry: DocEntry
    target: AST | None
    role: str | None


@final
class AnnotationTransaction:
    """Stage annotation fields and imports on the authoritative AST.

    This is a single-writer API. Compilation checks syntax without executing
    target code or parsing emitted source. Exhaustive identity/fingerprint
    guards remain a compatibility cost until tracked mutations land.

    """

    def __init__(self, *, tree: CommentedModule) -> None:
        """Capture original identities without cloning the executable tree.

        Args:
            tree (CommentedModule): Authoritative mutable comment-aware module.

        """
        self._tree: CommentedModule = tree
        self._containers: tuple[FieldValue, ...] = tuple(
            value for _, _, value in self._lists()
        )
        self._baseline: _TreeState = self._state()
        self._revision: int = tree.source_graph.last_change.revision
        self._owned: dict[int, AST] = {
            id(node): node for node in walk(node=tree)
        }
        self._edits: dict[tuple[int, str], _Edit] = {}
        self._imports: list[ImportFrom] = []
        self._aliases: list[TypeAlias] = []
        self._closed: bool = False

    def _state(self) -> _TreeState:
        """Capture structure, identity and the flat comment view.

        Returns:
            _TreeState: Compatibility fingerprint detecting raw external AST
                edits.

        """
        return (
            dump(node=self._tree, include_attributes=True),
            tuple(id(node) for node in walk(node=self._tree)),
            tuple(
                (id(comment), comment.text) for comment in self._tree.comments
            ),
            tuple(
                (id(node), field, id(value))
                for node, field, value in self._lists()
            ),
        )

    def _lists(self) -> list[tuple[AST, str, FieldValue]]:
        """Retain list identity witnesses for compatibility validation.

        Returns:
            list[tuple[AST, str, FieldValue]]: Existing list-valued fields
                without copying their contents.

        """
        result: list[tuple[AST, str, FieldValue]] = []
        field: str
        value: FieldValue
        for node in walk(node=self._tree):
            for field, value in iter_fields(node=node):
                if isinstance(value, list):
                    result.append((node, field, value))
        return result

    def add_import(self, *, declaration: ImportFrom) -> None:
        """Stage one absolute, unaliased annotation dependency import.

        No module code is executed. Commit checks the binding against names
        in every scope, conservatively refusing possible shadowing. This
        API does not merge imports, add future flags or resolve aliases.

        Args:
            declaration (ImportFrom): Fresh from-import containing exactly one
                name.

        Raises:
            ValueError: The transaction is closed.

        """
        if self._closed:
            msg: str = "Annotation transaction is already closed."
            raise ValueError(msg)
        self._imports.append(declaration)

    def replace(self, *, owner: AST, field: str, value: expr | None) -> None:
        """Stage only a permitted annotation field on an owned node.

        Args:
            owner (AST): Existing parameter, annotated assignment or function.
            field (str): Annotation field permitted for that container.
            value (expr | None): Fresh annotation subtree, or None where
                removal is valid.

        Raises:
            ValueError: The transaction is closed or field/owner is invalid.

        """
        if self._closed or id(owner) not in self._owned:
            msg: str = "Annotation transaction is closed or owner is detached."
            raise ValueError(msg)
        before: expr | None
        if field == "returns" and isinstance(
            owner,
            (FunctionDef, AsyncFunctionDef),
        ):
            before = owner.returns
        elif field == "value" and isinstance(owner, TypeAlias):
            before = owner.value
            if value is None:
                msg = "A type alias requires a value."
                raise ValueError(msg)
        elif field == "annotation" and isinstance(owner, (arg, AnnAssign)):
            before = owner.annotation
            if isinstance(owner, AnnAssign) and value is None:
                msg = "An annotated assignment requires an annotation."
                raise ValueError(msg)
        else:
            msg = "Annotation transactions cannot change executable fields."
            raise ValueError(msg)
        key: tuple[int, str] = (id(owner), field)
        existing: _Edit | None = self._edits.get(key)
        self._edits[key] = _Edit(
            owner=owner,
            field=field,
            before=before if existing is None else existing.before,
            after=value,
        )

    def cancel(self) -> None:
        """Discard pending edits without touching the module."""
        self._edits.clear()
        self._imports.clear()
        self._aliases.clear()
        self._closed = True

    def add_alias(self, *, declaration: TypeAlias) -> None:
        """Stage a fresh PEP 695 declaration with ordinary type parameters.

        Args:
            declaration (TypeAlias): Alias to insert after the import preamble.

        Raises:
            ValueError: The transaction is closed.

        """
        if self._closed:
            msg: str = "Annotation transaction is already closed."
            raise ValueError(msg)
        self._aliases.append(declaration)

    def _proposals(self) -> list[AST]:
        """Validate new ownership, cycles and source-level identifiers.

        Returns:
            list[AST]: Fresh proposed nodes requiring temporary compiler
                locations.

        Raises:
            ValueError: A proposal aliases owned syntax or has invalid names.

        """
        nodes: list[AST] = []
        seen: set[int] = set()
        roots: list[AST] = [
            edit.after
            for edit in self._edits.values()
            if edit.after is not None and edit.after is not edit.before
        ]
        roots.extend(self._imports)
        roots.extend(self._aliases)
        for root in roots:
            pending: list[AST] = [root]
            while pending:
                node: AST = pending.pop()
                if isinstance(node, Constants.shared):
                    continue
                if id(node) in seen or id(node) in self._owned:
                    msg: str = "Annotation proposal aliases or cycles syntax."
                    raise ValueError(msg)
                seen.add(id(node))
                name: str | None = (
                    node.id
                    if isinstance(node, Name)
                    else node.attr
                    if isinstance(node, Attribute)
                    else node.arg
                    if isinstance(node, (arg, keyword))
                    else None
                )
                if name is not None and not _identifier(name=name):
                    msg = "Annotation proposal contains an invalid identifier."
                    raise ValueError(msg)
                nodes.append(node)
                pending.extend(iter_child_nodes(node=node))
        return nodes

    def _validate_imports(self) -> None:
        """Refuse unsupported import syntax and existing binding collisions.

        Raises:
            ValueError: An import is unsupported or could shadow a binding.

        """
        if self._imports and any(
            isinstance(node, alias) and node.name == "*"
            for node in self._owned.values()
        ):
            msg: str = "Annotation import conflicts with wildcard bindings."
            raise ValueError(msg)
        annotations: set[int] = set()
        for owner in self._owned.values():
            annotation: expr | None = (
                owner.annotation
                if isinstance(owner, (arg, AnnAssign))
                else owner.returns
                if isinstance(owner, (FunctionDef, AsyncFunctionDef))
                else None
            )
            if annotation is not None:
                annotations.update(id(node) for node in walk(node=annotation))
        names: set[str] = set()
        for node in self._owned.values():
            name: str | None = (
                node.id
                if isinstance(node, Name)
                and (
                    isinstance(node.ctx, (Store, Del))
                    or id(node) not in annotations
                    or node.id in __dict__
                )
                else node.arg
                if isinstance(node, arg)
                else node.asname or node.name.split(sep=".")[0]
                if isinstance(node, alias)
                else node.rest
                if isinstance(node, MatchMapping)
                else read_attribute(node=node, name="name", kind=str)
            )
            if name is not None:
                names.add(name)
        for declaration in self._imports:
            if (
                declaration.level != 0
                or declaration.module is None
                or declaration.module == "__future__"
                or not all(
                    _identifier(name=part)
                    for part in declaration.module.split(sep=".")
                )
                or len(declaration.names) != 1
                or declaration.names[0].asname is not None
                or not _identifier(name=declaration.names[0].name)
            ):
                msg = "Unsupported annotation import declaration."
                raise ValueError(msg)
            binding: str = declaration.names[0].name
            if binding in names:
                msg = "Annotation import conflicts with an existing binding."
                raise ValueError(msg)
            names.add(binding)

    def _validate_aliases(self) -> None:
        """Validate fresh alias bindings and unconstrained generic parameters.

        Raises:
            ValueError: An alias captures a name or has unsupported binders.

        """
        reserved: set[str] = {
            node.id for node in self._owned.values() if isinstance(node, Name)
        }
        reserved.update(
            binding
            for node in self._owned.values()
            if (binding := read_attribute(node=node, name="name", kind=str))
            is not None
        )
        reserved.update(
            node.arg for node in self._owned.values() if isinstance(node, arg)
        )
        reserved.update(
            node.asname or node.name.split(sep=".")[0]
            for node in self._owned.values()
            if isinstance(node, alias)
        )
        reserved.update(item.names[0].name for item in self._imports)
        for declaration in self._aliases:
            name: str = declaration.name.id
            parameters: list[str] = [
                parameter.name
                for parameter in declaration.type_params
                if isinstance(parameter, (TypeVar, ParamSpec))
                and (
                    not isinstance(parameter, TypeVar)
                    or parameter.bound is None
                )
                and parameter.default_value is None
            ]
            if (
                not isinstance(declaration.name.ctx, Store)
                or not _identifier(name=name)
                or name in reserved
                or name in __dict__
                or len(parameters) != len(declaration.type_params)
                or len(set(parameters)) != len(parameters)
                or any(not _identifier(name=item) for item in parameters)
            ):
                msg: str = "Unsupported or conflicting annotation alias."
                raise ValueError(msg)
            reserved.add(name)

    def commit(self) -> tuple[AST, ...]:
        """Commit declared edits and restore original references on failure.

        Proposed location attributes are temporary: emission owns their final
        coordinates. No source, token or semantic cache is published here.
        Existing lazy reconciliation discovers the committed field changes.

        Returns:
            tuple[AST, ...]: Inserted imports followed by changed owners, once
                per node.

        Raises:
            ValueError: Closed/stale transaction, aliasing or invalid syntax.
            TypeError: The proposed native AST is structurally invalid.
            SyntaxError: The compiler rejects a proposed annotation subtree.
            RecursionError: The compiler's syntax depth limit is exceeded.

        """
        if self._closed:
            msg: str = "Annotation transaction is already closed."
            raise ValueError(msg)
        self._closed = True
        if (
            self._tree.source_graph.last_change.revision != self._revision
            or self._state() != self._baseline
        ):
            msg = "Cannot commit a stale annotation transaction."
            raise ValueError(msg)
        if (
            not self._imports
            and not self._aliases
            and not any(
                edit.after is not edit.before for edit in self._edits.values()
            )
        ):
            return ()
        nodes: list[AST] = self._proposals()
        self._validate_imports()
        self._validate_aliases()
        body: list[stmt] = self._tree.body
        original_body: tuple[stmt, ...] = tuple(body)
        locations: list[_Location] = [
            _Location(
                node=node,
                field=field,
                present=hasattr(node, field),
                value=read_attribute(node=node, name=field, kind=int),
            )
            for node in nodes
            for field in Constants.locations
        ]
        links: list[_Link] = [
            _Link(entry=entry, target=entry.target, role=entry.link_role)
            for doc in self._tree.docstrings
            for entry in doc.entries()
        ]
        changed: dict[int, AST] = {}
        committed: bool = False
        try:
            changed = self._apply()
            committed = True
        finally:
            if not committed:
                body[:] = original_body
                for edit in reversed(tuple(self._edits.values())):
                    setattr(edit.owner, edit.field, edit.before)
                for link in links:
                    link.entry.target = link.target
                    link.entry.link_role = link.role
            self._restore_locations(locations=locations)
        return tuple(changed.values())

    def _apply(self) -> dict[int, AST]:
        """Apply staged fields, compile without execution and relink doc views.

        Returns:
            dict[int, AST]: Changed owner nodes, deduplicated in staging order.

        """
        changed: dict[int, AST] = {}
        if self._imports or self._aliases:
            position: int = 0
            for statement in self._tree.body:
                if isinstance(statement, (Import, ImportFrom)) or (
                    position == 0
                    and isinstance(statement, Expr)
                    and isinstance(statement.value, Constant)
                    and isinstance(statement.value.value, str)
                ):
                    position += 1
                else:
                    break
            for declaration in (*self._imports, *self._aliases):
                if self._tree.body:
                    copy_location(
                        new_node=declaration,
                        old_node=self._tree.body[
                            min(position, len(self._tree.body) - 1)
                        ],
                    )
                fix_missing_locations(node=declaration)
                changed[id(declaration)] = declaration
            self._tree.body[position:position] = [
                *self._imports,
                *self._aliases,
            ]
        for edit in self._edits.values():
            if edit.after is edit.before:
                continue
            if edit.after is not None:
                copy_location(new_node=edit.after, old_node=edit.owner)
                fix_missing_locations(node=edit.after)
            setattr(edit.owner, edit.field, edit.after)
            changed[id(edit.owner)] = edit.owner
        compile(
            source=self._tree,
            filename="<annotation-transaction>",
            mode="exec",
        )
        for document in self._tree.docstrings:
            document.link()
        return changed

    @staticmethod
    def _restore_locations(*, locations: list[_Location]) -> None:
        """Restore proposed nodes keeping the owned node locations.

        Args:
            locations (list[_Location]): Original coordinate state before
                compiler validation.

        """
        for location in locations:
            if location.present:
                setattr(location.node, location.field, location.value)
            elif hasattr(location.node, location.field):
                delattr(location.node, location.field)
