"""Python lexical scope graph: symbols, bindings and occurrences."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    AugAssign,
    ClassDef,
    Del,
    DictComp,
    ExceptHandler,
    FunctionDef,
    GeneratorExp,
    Global,
    If,
    Import,
    ImportFrom,
    Lambda,
    ListComp,
    MatchAs,
    MatchMapping,
    MatchStar,
    Name,
    NamedExpr,
    Nonlocal,
    ParamSpec,
    SetComp,
    Store,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    While,
    alias,
    arg,
    arguments,
    iter_child_nodes,
    walk,
)
from dataclasses import dataclass
from typing import Final, TypedDict, Unpack, cast, final

from astart.node_attributes import list_items, write_attribute
from astart.semantic.identities import (
    Binding,
    DependencyGraph,
    IdentityIndex,
    Occurrence,
    Role,
    Symbol,
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        annotation_fields: Grouped module constant.
        function_like: Grouped module constant.
        graftable_kinds: Grouped module constant.
        write_roles: Grouped module constant.

    """

    annotation_fields: Final[dict[type, frozenset[str]]] = {
        AnnAssign: frozenset({"annotation"}),
        TypeAlias: frozenset({"value"}),
        TypeVar: frozenset({"bound", "default_value"}),
        TypeVarTuple: frozenset({"default_value"}),
        ParamSpec: frozenset({"default_value"}),
        arg: frozenset({"annotation"}),
        FunctionDef: frozenset({"returns"}),
        AsyncFunctionDef: frozenset({"returns"}),
    }
    function_like: Final[frozenset[str]] = frozenset(
        {"function", "lambda", "comprehension"},
    )
    graftable_kinds: Final[frozenset[str]] = frozenset(
        {"module", "function", "class"},
    )
    write_roles: Final[frozenset[str]] = frozenset(
        {"WRITE", "DEFINE", "PARAMETER", "IMPORT", "DELETE"},
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Scope:
    """One lexical namespace with explicit compiler-relevant behavior.

    Attributes:
        id: Stable AST scope-owner identity.
        parent_id: Enclosing scope, absent only for module.
        kind: Module, function, lambda, class, or comprehension.
        owner_node_id: Syntactic scope owner identity.
        globals: Names explicitly declared global.
        nonlocals: Names explicitly declared nonlocal.

    """

    id: int
    parent_id: int | None
    kind: str
    owner_node_id: int
    globals: frozenset[str] = frozenset()
    nonlocals: frozenset[str] = frozenset()


class OccurrenceOptions(TypedDict, total=False):
    """Optional metadata controlling how a lexical occurrence is indexed.

    Attributes:
        definition_kind: Classification assigned to a newly created binding.
        annotation: Whether a name read belongs to a type expression.

    """

    definition_kind: str
    annotation: bool


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class RevisionDiff:
    """Node-level mutation summary used for incremental reindexing.

    Attributes:
        changed: Node identities whose fingerprint entries differed.
        structural: Changed identities that also altered tree topology.
        parents_new: Node to parent map of the current tree.
        parents_old: Node to parent map of the prior tree.

    """

    changed: frozenset[int]
    structural: frozenset[int]
    parents_new: dict[int, int | None]
    parents_old: dict[int, int | None]


def _occurrence_name(
    *,
    occurrence: Occurrence,
    previous: ScopeGraph,
) -> str | None:
    """Recover the identifier an occurrence originally resolved.

    Args:
        occurrence: Previously recorded occurrence.
        previous: Previously indexed revision.

    Returns:
        The lexical name to re-resolve, or None when it cannot be
        recovered from the previous index or the node itself.

    """
    if occurrence.symbol_id is not None:
        symbol: Symbol | None = previous.symbols.get(occurrence.symbol_id)
        if symbol is not None:
            return symbol.name
    node: AST | None = previous.node_index.get(occurrence.node_id)
    if isinstance(node, alias):
        return node.asname or node.name.split(sep=".")[0]
    if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
        return node.name
    found: object = (
        getattr(node, "id", None)
        or getattr(node, "arg", None)
        or getattr(node, "name", None)
    )
    return found if isinstance(found, str) else None


@final
class ScopeGraph:
    """Index lexical scopes, symbolic occurrences, and definition records."""

    def __init__(
        self,
        *,
        root: AST,
        identities: IdentityIndex,
        previous: ScopeGraph | None = None,
        diff: RevisionDiff | None = None,
    ) -> None:
        """Index the current mutable AST with stable IDs when possible.

        Args:
            root: Python module AST, not its supplementary comment children.
            identities: Persistent per-module syntax identity allocator.
            previous: Previously indexed revision for identity reuse.
            diff: Node-level change summary enabling clean-subtree reuse.

        """
        self.identities: IdentityIndex = identities
        self._previous: ScopeGraph | None = previous
        self._diff: RevisionDiff | None = diff
        self.grafted_scopes: set[int] = set()
        self.scopes: dict[int, Scope] = {}
        self.symbols: dict[int, Symbol] = {}
        self.bindings: dict[int, Binding] = {}
        self.occurrences: dict[int, Occurrence] = {}
        self.node_index: dict[int, AST] = {}
        self.node_scopes: dict[int, int] = {}
        self.symbol_references: dict[int, set[int]] = {}
        self.symbol_definitions: dict[int, set[int]] = {}
        self.symbol_bindings: dict[int, set[int]] = {}
        self.scope_symbols: dict[int, dict[str, int]] = {}
        self.scope_children: dict[int, set[int]] = {}
        self.graph: DependencyGraph = DependencyGraph()
        self._old_symbols: dict[tuple[int, str], Symbol] = (
            {
                (record.scope_id, record.name): record
                for record in previous.symbols.values()
            }
            if previous is not None
            else {}
        )
        self._old_by_definition: dict[int, Symbol] = (
            {
                record.declaration_node_id: record
                for record in previous.symbols.values()
                if record.declaration_node_id is not None
            }
            if previous is not None
            else {}
        )
        self._old_bindings: dict[tuple[int, int], Binding] = (
            {
                (binding.node_id, binding.symbol_id): binding
                for binding in previous.bindings.values()
            }
            if previous is not None
            else {}
        )
        self.next_symbol: int = previous.next_symbol if previous else 1
        self.next_binding: int = previous.next_binding if previous else 1
        root_id: int = identities.node_id(node=root)
        self.root_id: int = root_id
        self.scopes[root_id] = Scope(
            id=root_id,
            parent_id=None,
            kind="module",
            owner_node_id=root_id,
        )
        self.scope_symbols[root_id] = {}
        self._visit_scope(owner=root, scope_id=root_id, kind="module")
        for symbol_id, references in self.symbol_references.items():
            for consumer in references:
                for producer in self.symbol_definitions.get(symbol_id, ()):
                    self.graph.add(
                        consumer=consumer,
                        producer=producer,
                        kind="REACHES_DEFINITION",
                    )

    def resolve_with_path(
        self,
        *,
        name: str,
        scope_id: int,
    ) -> tuple[int | None, frozenset[int]]:
        """Resolve a read and report the scopes consulted in order.

        Args:
            name: Unqualified Python name.
            scope_id: Scope of the read.

        Returns:
            Resolved symbol identity, or None, plus every scope whose
            structure the resolution depended on (read scope first).

        """
        current: int | None = scope_id
        crossed_function: bool = False
        path: list[int] = []
        while current is not None:
            scope: Scope = self.scopes[current]
            path.append(current)
            if name in scope.globals:
                return (
                    self.scope_symbols[self.root_id].get(name),
                    frozenset(path),
                )
            if name in scope.nonlocals:
                current = scope.parent_id
                continue
            if not (scope.kind == "class" and crossed_function):
                found: int | None = self.scope_symbols[current].get(name)
                if found is not None:
                    return (found, frozenset(path))
            if scope.kind in Constants.function_like:
                crossed_function = True
            current = scope.parent_id
        return (None, frozenset(path))

    def resolve(self, *, name: str, scope_id: int) -> int | None:
        """Resolve a read from its lexical scope, honoring class lookup rules.

        Args:
            name: Unqualified Python name.
            scope_id: Scope of the read.

        Returns:
            Symbol identity, or None for unknown external/builtin names.

        """
        resolved, _path = self.resolve_with_path(name=name, scope_id=scope_id)
        return resolved

    def references(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return individual read nodes in deterministic source order.

        Args:
            symbol_id: Lexical symbol.

        Returns:
            AST occurrences using that symbol.

        """
        return tuple(
            sorted(
                (
                    self.node_index[node_id]
                    for node_id in self.symbol_references.get(symbol_id, ())
                ),
                key=lambda node: (
                    getattr(node, "lineno", 0),
                    getattr(node, "col_offset", 0),
                ),
            ),
        )

    def definitions(self, *, symbol_id: int) -> tuple[AST, ...]:
        """Return syntactic definitions of a symbol in source order.

        Args:
            symbol_id: Lexical symbol.

        Returns:
            AST nodes defining or assigning the symbol.

        """
        return tuple(
            sorted(
                (
                    self.node_index[node_id]
                    for node_id in self.symbol_definitions.get(symbol_id, ())
                ),
                key=lambda node: (
                    getattr(node, "lineno", 0),
                    getattr(node, "col_offset", 0),
                ),
            ),
        )

    @classmethod
    def _scan_locals(
        cls,
        *,
        owner: AST,
    ) -> tuple[list[tuple[str, str, AST]], frozenset[str], frozenset[str]]:
        """Collect scope-local names before visiting reads.

        Args:
            owner: Owner supplied as AST for this operation.

        Returns:
            tuple[list[tuple[str, str, AST]], frozenset[str], frozenset[str]]
            produced by this operation.

        """
        declared: list[tuple[str, str, AST]] = []
        globals_set: set[str] = set()
        nonlocals_set: set[str] = set()
        pending: list[AST] = list(
            reversed(tuple(iter_child_nodes(node=owner))),
        )
        while pending:
            node: AST = pending.pop()
            if isinstance(node, Global):
                globals_set.update(node.names)
            elif isinstance(node, Nonlocal):
                nonlocals_set.update(node.names)
            elif isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
                kind: str = (
                    "class" if isinstance(node, ClassDef) else "function"
                )
                declared.append((node.name, kind, node))
                continue
            elif isinstance(
                node,
                (Lambda, ListComp, SetComp, DictComp, GeneratorExp),
            ):
                continue
            else:
                declared.extend(cls._leaf_declarations(node=node))
            pending.extend(reversed(tuple(iter_child_nodes(node=node))))
        return (declared, frozenset(globals_set), frozenset(nonlocals_set))

    @staticmethod
    def _leaf_declarations(*, node: AST) -> list[tuple[str, str, AST]]:
        """Names a single non-scope node binds in its owning scope.

        Args:
            node: The node examined while names a single non-scope node binds
                in its owning scope.

        Returns:
            list[tuple[str, str, AST]] produced by this operation.

        """
        if isinstance(node, Name) and isinstance(node.ctx, (Store, Del)):
            return [(node.id, "variable", node)]
        if isinstance(node, arg):
            return [(node.arg, "parameter", node)]
        if isinstance(node, (Import, ImportFrom)):
            return [
                (entry.asname or entry.name.split(sep=".")[0], "import", entry)
                for entry in node.names
            ]
        if (
            isinstance(node, (ExceptHandler, MatchAs, MatchStar))
            and node.name is not None
        ):
            return [(node.name, "variable", node)]
        if isinstance(node, MatchMapping) and node.rest is not None:
            return [(node.rest, "variable", node)]
        return []

    @staticmethod
    def _children(*, node: AST, annotation: bool) -> list[tuple[AST, bool]]:
        """Return each AST child with its type-expression annotation flag.

        Args:
            annotation: True when the node is already inside a type
                expression; the flag then propagates to every child.
            node: Node whose children are enumerated in field order.

        Returns:
            ``(child, in_type_expression)`` pairs matching ``iter_child_nodes``
            ordering while marking annotation-only fields.

        """
        annotation_fields: frozenset[str] = frozenset()
        for klass in type(node).__mro__:
            found_fields: frozenset[str] | None = (
                Constants.annotation_fields.get(klass)
            )
            if found_fields is not None:
                annotation_fields = found_fields
                break
        result: list[tuple[AST, bool]] = []
        for field in node._fields:
            value: object = getattr(node, field, None)
            flag: bool = annotation or field in annotation_fields
            if isinstance(value, AST):
                result.append((value, flag))
            elif isinstance(value, list):
                result.extend(
                    (item, flag)
                    for item in list_items(
                        value=cast(
                            typ="list[tuple[object, bool]] ",
                            val=value,
                        ),
                    )
                    if isinstance(item, AST)
                )
        return result

    def _node(self, *, node: AST, scope_id: int) -> int:
        """Register one node and its current lexical scope.

        Args:
            node: The node examined while register one node and its current
                lexical scope.
            scope_id: Scope id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        identity: int = self.identities.node_id(node=node)
        self.node_index[identity] = node
        self.node_scopes[identity] = scope_id
        write_attribute(node=node, name="scope_id", value=scope_id)
        return identity

    def _symbol(
        self,
        *,
        name: str,
        scope_id: int,
        kind: str,
        declaration: AST | None,
    ) -> int:
        """Create/reuse one lexical symbol without conflating definitions.

        Args:
            declaration: Declaration supplied as AST | None for this operation.
            kind: Kind supplied as str for this operation.
            name: Identifier of the name being resolved.
            scope_id: Scope id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        current: int | None = self.scope_symbols.setdefault(scope_id, {}).get(
            name,
        )
        if current is not None:
            return current
        declaration_id: int | None = (
            self.identities.node_id(node=declaration)
            if declaration is not None
            else None
        )
        prior: Symbol | None = self._old_symbols.get((scope_id, name))
        origin_id: int | None = None
        if prior is None and declaration_id is not None:
            candidate: Symbol | None = self._old_by_definition.get(
                declaration_id,
            )
            if candidate is not None:
                if candidate.scope_id == scope_id:
                    prior = candidate
                else:
                    origin_id = candidate.id
        if prior is not None and prior.id not in self.symbols:
            symbol_id: int = prior.id
            origin_id = prior.origin_id
        else:
            symbol_id = self.next_symbol
            self.next_symbol += 1
        self.scope_symbols[scope_id][name] = symbol_id
        self.symbols[symbol_id] = Symbol(
            id=symbol_id,
            name=name,
            kind=kind,
            scope_id=scope_id,
            declaration_node_id=declaration_id,
            origin_id=origin_id,
        )
        return symbol_id

    def _binding(self, *, node: AST, symbol_id: int, kind: str) -> int:
        """Index one definition, reusing its identity across revisions.

        Args:
            kind: Kind supplied as str for this operation.
            node: The node examined while index one definition, reusing its
                identity across revisions.
            symbol_id: Symbol id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        node_id: int = self.identities.node_id(node=node)
        candidate: Binding | None = self._old_bindings.get(
            (node_id, symbol_id),
        )
        if candidate is not None and candidate.id not in self.bindings:
            binding_id: int = candidate.id
        else:
            binding_id = self.next_binding
            self.next_binding += 1
        self.bindings[binding_id] = Binding(
            id=binding_id,
            symbol_id=symbol_id,
            node_id=node_id,
            kind=kind,
        )
        self.symbol_bindings.setdefault(symbol_id, set()).add(binding_id)
        self.symbol_definitions.setdefault(symbol_id, set()).add(node_id)
        write_attribute(node=node, name="binding_id", value=binding_id)
        return binding_id

    def _resolve_target(self, *, name: str, scope_id: int) -> int:
        """Resolve a binding target, honoring global and nonlocal.

        Args:
            name: Identifier of the name being resolved.
            scope_id: Scope id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        scope: Scope = self.scopes[scope_id]
        if name in scope.globals:
            return self._symbol(
                name=name,
                scope_id=self.root_id,
                kind="variable",
                declaration=None,
            )
        if name in scope.nonlocals:
            parent: int | None = scope.parent_id
            while parent is not None:
                candidate: int | None = self.scope_symbols[parent].get(name)
                if (
                    candidate is not None
                    and self.scopes[parent].kind != "class"
                ):
                    return candidate
                parent = self.scopes[parent].parent_id
        return self._symbol(
            name=name,
            scope_id=scope_id,
            kind="variable",
            declaration=None,
        )

    def _occurrence(
        self,
        *,
        node: AST,
        scope_id: int,
        name: str,
        roles: frozenset[Role | str],
        **options: Unpack[OccurrenceOptions],
    ) -> None:
        """Resolve and index one lexical occurrence and its dependencies.

        A binding occurrence resolves its assignment target; a read instead
        follows lexical lookup. Captured reads and annotation reads acquire
        additional semantic roles before their dependency edges are recorded.

        Args:
            node: Syntax node representing the occurrence.
            scope_id: Lexical scope in which the occurrence appears.
            name: Identifier read, assigned, imported, or declared.
            roles: Initial semantic roles of the occurrence.
            **options: Optional binding classification and annotation flag.

        """
        node_id: int = self._node(node=node, scope_id=scope_id)
        scope_path: frozenset[int]
        if roles.intersection(
            {"WRITE", "DEFINE", "PARAMETER", "IMPORT", "DELETE"},
        ):
            symbol_id: int | None = self._resolve_target(
                name=name,
                scope_id=scope_id,
            )
            scope_path = frozenset({scope_id})
        else:
            symbol_id, scope_path = self.resolve_with_path(
                name=name,
                scope_id=scope_id,
            )
        if symbol_id is not None:
            owner: int = self.symbols[symbol_id].scope_id
            if (
                owner != scope_id
                and owner in self.scopes
                and (self.scopes[owner].kind in Constants.function_like)
            ):
                roles = roles | {"CAPTURE"}
        if options.get("annotation", False) and "READ" in roles:
            roles = roles | {"ANNOTATION"}
        occurrence: Occurrence = Occurrence(
            node_id=node_id,
            symbol_id=symbol_id,
            scope_id=scope_id,
            roles=cast(typ="frozenset[Role]", val=roles),
        )
        self.occurrences[node_id] = occurrence
        write_attribute(node=node, name="symbol_id", value=symbol_id)
        self._index_occurrence_dependencies(
            node=node,
            occurrence=occurrence,
            scope_path=scope_path,
            definition_kind=options.get("definition_kind", "write"),
        )

    def _index_occurrence_dependencies(
        self,
        *,
        node: AST,
        occurrence: Occurrence,
        scope_path: frozenset[int],
        definition_kind: str,
    ) -> None:
        """Connect an indexed occurrence to its lexical and binding sources.

        Every occurrence depends on the scopes used during name resolution.
        Resolved reads additionally reference their declaration, whereas
        definitions create binding records and scope-definition edges.

        Args:
            node: Syntax node associated with the recorded occurrence.
            occurrence: Resolved occurrence carrying identity and roles.
            scope_path: Scopes consulted while resolving the identifier.
            definition_kind: Binding classification for definition occurrences.

        """
        node_id: int = occurrence.node_id
        symbol_id: int | None = occurrence.symbol_id
        scope_dependencies: set[int] = set(scope_path)
        if symbol_id is not None:
            scope_dependencies.add(self.symbols[symbol_id].scope_id)
        for traversed in scope_dependencies:
            self.graph.add(
                consumer=node_id,
                producer=self.scopes[traversed].owner_node_id,
                kind="DEPENDS_ON_SCOPE",
            )
        if symbol_id is None:
            return
        if occurrence.roles.intersection({"READ", "CAPTURE", "ANNOTATION"}):
            self.symbol_references.setdefault(symbol_id, set()).add(node_id)
            declaration_id: int | None = self.symbols[
                symbol_id
            ].declaration_node_id
            if declaration_id is not None:
                self.graph.add(
                    consumer=node_id,
                    producer=declaration_id,
                    kind="CAPTURES_SYMBOL"
                    if "CAPTURE" in occurrence.roles
                    else "READS_SYMBOL",
                )
        if occurrence.roles.intersection(
            {"WRITE", "DEFINE", "PARAMETER", "IMPORT", "DELETE"},
        ):
            self._binding(node=node, symbol_id=symbol_id, kind=definition_kind)
            self.graph.add(
                consumer=self.scopes[
                    self.symbols[symbol_id].scope_id
                ].owner_node_id,
                producer=node_id,
                kind="DEFINES_SYMBOL",
            )

    def _visit_scope(self, *, owner: AST, scope_id: int, kind: str) -> None:
        """Predeclare all lexical names, then traverse their uses.

        Args:
            kind: Kind supplied as str for this operation.
            owner: Owner supplied as AST for this operation.
            scope_id: Scope id supplied as int for this operation.

        """
        if self._graft_scope(owner=owner, scope_id=scope_id, kind=kind):
            return
        declarations, globals_set, nonlocals_set = self._scan_locals(
            owner=owner,
        )
        previous: Scope = self.scopes[scope_id]
        self.scopes[scope_id] = Scope(
            id=scope_id,
            parent_id=previous.parent_id,
            kind=kind,
            owner_node_id=previous.owner_node_id,
            globals=globals_set,
            nonlocals=nonlocals_set,
        )
        for name, symbol_kind, declaration in declarations:
            if name not in globals_set and name not in nonlocals_set:
                self._symbol(
                    name=name,
                    scope_id=scope_id,
                    kind=symbol_kind,
                    declaration=declaration,
                )
        self._visit(node=owner, scope_id=scope_id, is_owner=True)

    def _graft_scope(self, *, owner: AST, scope_id: int, kind: str) -> bool:
        """Reuse the prior index for a subtree untouched by this revision.

        When no changed or structurally moved node lies inside ``owner``'s
        statement body, the scope and all scopes nested within it retain
        identical declarations, occurrences, bindings, and dependency edges.
        The previous records are copied wholesale once every occurrence in
        the subtree re-resolves to the same symbol through the already
        rebuilt ancestor index, replicating any global or nonlocal symbol
        creation the normal visit would have performed.

        Returns:
            Whether the subtree index was grafted instead of revisited.

        Args:
            kind: Kind supplied as str for this operation.
            owner: Scope owner whose statement body bounds the subtree.
            scope_id: Scope identity of ``owner``.

        """
        previous: ScopeGraph | None = self._previous
        diff: RevisionDiff | None = self._diff
        if previous is None or diff is None:
            return False
        prior: Scope | None = previous.scopes.get(scope_id)
        if (
            kind not in Constants.graftable_kinds
            or prior is None
            or prior.kind != kind
        ):
            return False
        subtree_nodes: set[int] = {
            self.identities.node_id(node=item) for item in walk(node=owner)
        }
        if diff.changed & subtree_nodes or diff.structural & subtree_nodes:
            return False
        subtree_scopes: set[int] = {scope_id}
        pending: list[int] = [scope_id]
        while pending:
            for child in previous.scope_children.get(pending.pop(), ()):
                if child not in subtree_scopes:
                    subtree_scopes.add(child)
                    pending.append(child)
        subtree_occurrences: list[Occurrence] = [
            occurrence
            for occurrence in previous.occurrences.values()
            if occurrence.node_id in subtree_nodes
        ]
        if not self._graft_verify(
            previous=previous,
            subtree_scopes=subtree_scopes,
            subtree_occurrences=subtree_occurrences,
            scope_id=scope_id,
        ):
            return False
        self._graft_copy(
            previous=previous,
            subtree_nodes=subtree_nodes,
            subtree_scopes=subtree_scopes,
            subtree_occurrences=subtree_occurrences,
            scope_id=scope_id,
        )
        return True

    def _graft_verify(
        self,
        *,
        previous: ScopeGraph,
        subtree_scopes: set[int],
        subtree_occurrences: list[Occurrence],
        scope_id: int,
    ) -> bool:
        """Check that grafted tables reproduce identical resolutions.

        Scope records and predeclared symbol tables are installed first so
        lookups behave exactly as a normal visit would; every prior
        occurrence must then re-resolve to its previous symbol.

        Returns:
            Whether every subtree occurrence resolves identically.

        Args:
            previous: Previously indexed revision.
            scope_id: Grafted scope supplied as int for this operation.
            subtree_occurrences: Occurrences recorded inside the subtree.
            subtree_scopes: Scope identities belonging to the subtree.

        """
        for sid in subtree_scopes:
            scope: Scope | None = previous.scopes.get(sid)
            if scope is None:
                return False
            self.scopes[sid] = scope
            self.scope_symbols[sid] = dict(previous.scope_symbols.get(sid, {}))
            if sid != scope_id and scope.parent_id is not None:
                self.scope_children.setdefault(scope.parent_id, set()).add(sid)
        for occurrence in subtree_occurrences:
            name: str | None = _occurrence_name(
                occurrence=occurrence,
                previous=previous,
            )
            if name is None:
                return False
            resolved: int | None
            if occurrence.roles.intersection(Constants.write_roles):
                resolved = self._resolve_target(
                    name=name,
                    scope_id=occurrence.scope_id,
                )
            else:
                resolved, _ = self.resolve_with_path(
                    name=name,
                    scope_id=occurrence.scope_id,
                )
            if resolved != occurrence.symbol_id:
                return False
        return True

    def _graft_copy(
        self,
        *,
        previous: ScopeGraph,
        subtree_nodes: set[int],
        subtree_scopes: set[int],
        subtree_occurrences: list[Occurrence],
        scope_id: int,
    ) -> None:
        """Copy subtree index records and dependency edges wholesale.

        Args:
            previous: Previously indexed revision.
            scope_id: Grafted scope supplied as int for this operation.
            subtree_nodes: Node identities inside the grafted region.
            subtree_occurrences: Occurrences recorded inside the subtree.
            subtree_scopes: Scope identities belonging to the subtree.

        """
        self._graft_node_records(
            previous=previous,
            subtree_nodes=subtree_nodes,
        )
        self._graft_symbol_records(
            previous=previous,
            subtree_nodes=subtree_nodes,
            subtree_scopes=subtree_scopes,
            subtree_occurrences=subtree_occurrences,
        )
        for consumer in subtree_nodes | subtree_scopes:
            for edge in previous.graph.dependencies(node_id=consumer):
                if edge.kind != "REACHES_DEFINITION":
                    self.graph.add(
                        consumer=edge.consumer,
                        producer=edge.producer,
                        kind=edge.kind,
                    )
        self.grafted_scopes.add(scope_id)

    def _graft_node_records(
        self,
        *,
        previous: ScopeGraph,
        subtree_nodes: set[int],
    ) -> None:
        """Copy per-node index records for a grafted subtree.

        Args:
            previous: Previously indexed revision.
            subtree_nodes: Node identities inside the grafted region.

        """
        for node_id in subtree_nodes:
            node: AST | None = previous.node_index.get(node_id)
            if node is not None:
                self.node_index[node_id] = node
            containing: int | None = previous.node_scopes.get(node_id)
            if containing is not None:
                self.node_scopes[node_id] = containing
            occurrence: Occurrence | None = previous.occurrences.get(node_id)
            if occurrence is not None:
                self.occurrences[node_id] = occurrence

    def _graft_symbol_records(
        self,
        *,
        previous: ScopeGraph,
        subtree_nodes: set[int],
        subtree_scopes: set[int],
        subtree_occurrences: list[Occurrence],
    ) -> None:
        """Copy symbol, reference, definition and binding records.

        Args:
            previous: Previously indexed revision.
            subtree_nodes: Node identities inside the grafted region.
            subtree_occurrences: Occurrences recorded inside the subtree.
            subtree_scopes: Scope identities belonging to the subtree.

        """
        for sid in subtree_scopes:
            for symbol_id in previous.scope_symbols.get(sid, {}).values():
                record: Symbol | None = previous.symbols.get(symbol_id)
                if record is not None:
                    self.symbols[symbol_id] = record
        for occurrence in subtree_occurrences:
            symbol_id: int | None = occurrence.symbol_id
            node_id: int = occurrence.node_id
            if symbol_id is None:
                continue
            if node_id in previous.symbol_references.get(symbol_id, ()):
                self.symbol_references.setdefault(symbol_id, set()).add(
                    node_id,
                )
            if node_id in previous.symbol_definitions.get(symbol_id, ()):
                self.symbol_definitions.setdefault(symbol_id, set()).add(
                    node_id,
                )
        for binding in previous.bindings.values():
            if binding.node_id in subtree_nodes:
                self.bindings[binding.id] = binding
                self.symbol_bindings.setdefault(binding.symbol_id, set()).add(
                    binding.id,
                )

    def _child_scope(self, *, node: AST, parent_id: int, kind: str) -> int:
        """Create and register one nested lexical scope.

        Args:
            kind: Kind supplied as str for this operation.
            node: The node examined while create and register one nested
                lexical scope.
            parent_id: Parent id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        scope_id: int = self._node(node=node, scope_id=parent_id)
        self.scopes[scope_id] = Scope(
            id=scope_id,
            parent_id=parent_id,
            kind=kind,
            owner_node_id=scope_id,
        )
        self.scope_symbols[scope_id] = {}
        self.scope_children.setdefault(parent_id, set()).add(scope_id)
        return scope_id

    def _type_parameter_scope(self, *, owner: AST, parent_id: int) -> int:
        """Create a distinct annotation scope for PEP 695/696 type parameters.

        Negative scope IDs are reserved for synthetic annotation scopes,
        keeping them distinct from real AST identities and stable on moves.


        Args:
            owner: Owner supplied as AST for this operation.
            parent_id: Parent id supplied as int for this operation.

        Returns:
            int produced by this operation.

        """
        owner_id: int = self.identities.node_id(node=owner)
        scope_id: int = -owner_id
        self.scopes[scope_id] = Scope(
            id=scope_id,
            parent_id=parent_id,
            kind="type_parameters",
            owner_node_id=owner_id,
        )
        self.scope_symbols[scope_id] = {}
        self.scope_children.setdefault(parent_id, set()).add(scope_id)
        parameters: list[AST] = getattr(owner, "type_params", [])
        for parameter in parameters:
            if isinstance(parameter, (TypeVar, TypeVarTuple, ParamSpec)):
                self._symbol(
                    name=parameter.name,
                    scope_id=scope_id,
                    kind="type_parameter",
                    declaration=parameter,
                )
        for parameter in parameters:
            if isinstance(parameter, (TypeVar, TypeVarTuple, ParamSpec)):
                self._occurrence(
                    node=parameter,
                    scope_id=scope_id,
                    name=parameter.name,
                    roles=frozenset({"PARAMETER"}),
                    definition_kind="type_parameter",
                )
                for child, flag in self._children(
                    node=parameter,
                    annotation=False,
                ):
                    self._visit(node=child, scope_id=scope_id, annotation=flag)
        return scope_id

    def _visit_class_header(
        self,
        *,
        node: ClassDef,
        annotation_scope_id: int,
    ) -> None:
        """Visit base classes and class keywords in the annotation scope.

        Args:
            annotation_scope_id: Annotation scope id supplied as int for this
                operation.
            node: The node examined while visit base classes and class keywords
                in the annotation scope.

        """
        for item in (
            *node.bases,
            *(keyword.value for keyword in node.keywords),
        ):
            self._visit(node=item, scope_id=annotation_scope_id)

    def _visit_function_header(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        annotation_scope_id: int,
    ) -> None:
        """Visit defaults and annotations in the annotation scope.

        Args:
            annotation_scope_id: Annotation scope id supplied as int for this
                operation.
            node: The node examined while visit defaults and annotations in the
                annotation scope.

        """
        args: arguments = node.args
        for item in (
            *args.defaults,
            *(part for part in args.kw_defaults if part is not None),
        ):
            self._visit(node=item, scope_id=annotation_scope_id)
        for parameter in (*args.posonlyargs, *args.args, *args.kwonlyargs):
            if parameter.annotation is not None:
                self._visit(
                    node=parameter.annotation,
                    scope_id=annotation_scope_id,
                    annotation=True,
                )
        if node.returns is not None:
            self._visit(
                node=node.returns,
                scope_id=annotation_scope_id,
                annotation=True,
            )

    def _visit_definition(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef | ClassDef,
        scope_id: int,
    ) -> None:
        """Define a function or class, then open its own scope.

        Args:
            node: The node examined while define a function or class, then open
                its own scope.
            scope_id: Scope id supplied as int for this operation.

        """
        self._occurrence(
            node=node,
            scope_id=scope_id,
            name=node.name,
            roles=frozenset({"DEFINE"}),
            definition_kind="definition",
        )
        for decorator in node.decorator_list:
            self._visit(node=decorator, scope_id=scope_id)
        annotation_scope_id: int = (
            self._type_parameter_scope(owner=node, parent_id=scope_id)
            if node.type_params
            else scope_id
        )
        kind: str = "function"
        if isinstance(node, ClassDef):
            self._visit_class_header(
                node=node,
                annotation_scope_id=annotation_scope_id,
            )
            kind = "class"
        else:
            self._visit_function_header(
                node=node,
                annotation_scope_id=annotation_scope_id,
            )
        child_id: int = self._child_scope(
            node=node,
            parent_id=annotation_scope_id,
            kind=kind,
        )
        self._visit_scope(owner=node, scope_id=child_id, kind=kind)

    def _visit_type_alias(self, *, node: TypeAlias, scope_id: int) -> None:
        """Visit a ``type`` statement's name and lazily scoped value.

        Args:
            node: The node examined while visit a ``type`` statement's name and
                lazily scoped value.
            scope_id: Scope id supplied as int for this operation.

        """
        self._visit(node=node.name, scope_id=scope_id)
        annotation_scope_id: int = (
            self._type_parameter_scope(owner=node, parent_id=scope_id)
            if node.type_params
            else scope_id
        )
        self._visit(
            node=node.value,
            scope_id=annotation_scope_id,
            annotation=True,
        )

    def _visit_lambda(self, *, node: Lambda, scope_id: int) -> None:
        """Visit lambda defaults, then open the lambda scope.

        Args:
            node: The node examined while visit lambda defaults, then open the
                lambda scope.
            scope_id: Scope id supplied as int for this operation.

        """
        for default in (
            *node.args.defaults,
            *(part for part in node.args.kw_defaults if part is not None),
        ):
            self._visit(node=default, scope_id=scope_id)
        child_id: int = self._child_scope(
            node=node,
            parent_id=scope_id,
            kind="lambda",
        )
        self._visit_scope(owner=node, scope_id=child_id, kind="lambda")

    def _visit_comprehension(
        self,
        *,
        node: ListComp | SetComp | DictComp | GeneratorExp,
        scope_id: int,
    ) -> None:
        """Evaluate the first iterable outside, then open the scope.

        Args:
            node: The node examined while evaluate the first iterable outside,
                then open the scope.
            scope_id: Scope id supplied as int for this operation.

        """
        if node.generators:
            self._visit(node=node.generators[0].iter, scope_id=scope_id)
        child_id: int = self._child_scope(
            node=node,
            parent_id=scope_id,
            kind="comprehension",
        )
        self._visit_scope(owner=node, scope_id=child_id, kind="comprehension")

    def _visit_scoped_form(self, *, node: AST, scope_id: int) -> bool:
        """Open a nested scope for ``node`` when it introduces one.

        Returns:
            Whether ``node`` was fully handled here.



        Args:
            node: The node examined while open a nested scope for ``node`` when
                it introduces one.
            scope_id: Scope id supplied as int for this operation.

        """
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            self._visit_definition(node=node, scope_id=scope_id)
        elif isinstance(node, TypeAlias):
            self._visit_type_alias(node=node, scope_id=scope_id)
        elif isinstance(node, Lambda):
            self._visit_lambda(node=node, scope_id=scope_id)
        elif isinstance(node, (ListComp, SetComp, DictComp, GeneratorExp)):
            self._visit_comprehension(node=node, scope_id=scope_id)
        else:
            return False
        return True

    def _declare_name(
        self,
        *,
        node: Name,
        scope_id: int,
        annotation: bool = False,
    ) -> None:
        """Record a read, write or delete of a name.

        Args:
            annotation: True when the occurrence appears in a type
                expression rather than executable code.
            node: The node examined while record a read, write or delete of a
                name.
            scope_id: Scope id supplied as int for this operation.

        """
        roles: frozenset[Role] = (
            frozenset({"WRITE"})
            if isinstance(node.ctx, Store)
            else frozenset({"DELETE"})
            if isinstance(node.ctx, Del)
            else frozenset({"READ"})
        )
        self._occurrence(
            node=node,
            scope_id=scope_id,
            name=node.id,
            roles=roles,
            definition_kind="delete" if isinstance(node.ctx, Del) else "write",
            annotation=annotation,
        )

    def _declare_import(
        self,
        *,
        node: Import | ImportFrom,
        scope_id: int,
    ) -> None:
        """Record every name an import statement binds.

        Args:
            node: The node examined while record every name an import statement
                binds.
            scope_id: Scope id supplied as int for this operation.

        """
        self._node(node=node, scope_id=scope_id)
        for entry in node.names:
            self._occurrence(
                node=entry,
                scope_id=scope_id,
                name=entry.asname or entry.name.split(sep=".")[0],
                roles=frozenset({"IMPORT"}),
                definition_kind="import",
            )

    def _declare_binding(
        self,
        *,
        node: AST,
        scope_id: int,
        annotation: bool = False,
    ) -> bool:
        """Record the binding a node introduces.

        Returns:
            Whether the node was an import, which has no children to visit.



        Args:
            annotation: True when the occurrence appears in a type
                expression rather than executable code.
            node: The node examined while record the binding a node introduces.
            scope_id: Scope id supplied as int for this operation.

        """
        if isinstance(node, Name):
            self._declare_name(
                node=node,
                scope_id=scope_id,
                annotation=annotation,
            )
        elif isinstance(node, arg):
            self._occurrence(
                node=node,
                scope_id=scope_id,
                name=node.arg,
                roles=frozenset({"PARAMETER"}),
                definition_kind="parameter",
            )
        elif isinstance(node, (Import, ImportFrom)):
            self._declare_import(node=node, scope_id=scope_id)
            return True
        elif isinstance(node, ExceptHandler) and node.name is not None:
            self._occurrence(
                node=node,
                scope_id=scope_id,
                name=node.name,
                roles=frozenset({"WRITE"}),
                definition_kind="exception",
            )
        elif isinstance(node, (MatchAs, MatchStar)) and node.name is not None:
            self._occurrence(
                node=node,
                scope_id=scope_id,
                name=node.name,
                roles=frozenset({"WRITE"}),
                definition_kind="pattern",
            )
        elif isinstance(node, MatchMapping) and node.rest is not None:
            self._occurrence(
                node=node,
                scope_id=scope_id,
                name=node.rest,
                roles=frozenset({"WRITE"}),
                definition_kind="pattern",
            )
        else:
            self._node(node=node, scope_id=scope_id)
        return False

    def _visit_owner_callable(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef | Lambda,
        scope_id: int,
    ) -> None:
        """Declare parameters and visit the body inside the owned scope.

        Args:
            node: The node examined while declare parameters and visit the body
                inside the owned scope.
            scope_id: Scope id supplied as int for this operation.

        """
        for parameter in (
            *node.args.posonlyargs,
            *node.args.args,
            *(part for part in (node.args.vararg,) if part is not None),
            *node.args.kwonlyargs,
            *(part for part in (node.args.kwarg,) if part is not None),
        ):
            self._occurrence(
                node=parameter,
                scope_id=scope_id,
                name=parameter.arg,
                roles=frozenset({"PARAMETER"}),
                definition_kind="parameter",
            )
        for statement in (
            node.body if isinstance(node.body, list) else (node.body,)
        ):
            self._visit(node=statement, scope_id=scope_id)
            self.graph.add(
                consumer=self.identities.node_id(node=node),
                producer=self.identities.node_id(node=statement),
                kind="DEPENDS_ON_VALUE",
            )

    def _visit_owner_comprehension(
        self,
        *,
        node: ListComp | SetComp | DictComp | GeneratorExp,
        scope_id: int,
    ) -> None:
        """Visit targets, later iterables, conditions and result parts.

        Args:
            node: The node examined while visit targets, later iterables,
                conditions and result parts.
            scope_id: Scope id supplied as int for this operation.

        """
        for index, generator in enumerate(iterable=node.generators):
            self._visit(node=generator.target, scope_id=scope_id)
            if index > 0:
                self._visit(node=generator.iter, scope_id=scope_id)
            for condition in generator.ifs:
                self._visit(node=condition, scope_id=scope_id)
        for field in ("elt", "key", "value"):
            component: AST | None = getattr(node, field, None)
            if component is not None:
                self._visit(node=component, scope_id=scope_id)

    def _link_dependencies(self, *, node: AST) -> None:
        """Add value and control dependency edges for ``node``.

        Args:
            node: The node examined while add value and control dependency
                edges for ``node``.

        """
        if isinstance(node, (AnnAssign, NamedExpr)) and node.value is not None:
            self.graph.add(
                consumer=self.identities.node_id(node=node.target),
                producer=self.identities.node_id(node=node.value),
                kind="DEPENDS_ON_VALUE",
            )
        if isinstance(node, (Assign, AugAssign)):
            targets: tuple[AST, ...] = (
                tuple(node.targets)
                if isinstance(node, Assign)
                else (node.target,)
            )
            for target in targets:
                self.graph.add(
                    consumer=self.identities.node_id(node=target),
                    producer=self.identities.node_id(node=node.value),
                    kind="DEPENDS_ON_VALUE",
                )
        if isinstance(node, (If, While)):
            for branch in (node.body, node.orelse):
                for instruction in branch:
                    self.graph.add(
                        consumer=self.identities.node_id(node=instruction),
                        producer=self.identities.node_id(node=node.test),
                        kind="DEPENDS_ON_CONTROL",
                    )

    def _visit(
        self,
        *,
        node: AST,
        scope_id: int,
        is_owner: bool = False,
        annotation: bool = False,
    ) -> None:
        """Traverse syntax without duplicating nested-scope ownership.

        Args:
            annotation: True while traversing a type expression; name
                occurrences then receive the ``ANNOTATION`` role.
            is_owner: Whether to owner.
            node: The node examined while traverse syntax without duplicating
                nested-scope ownership.
            scope_id: Scope id supplied as int for this operation.

        """
        if not is_owner and self._visit_scoped_form(
            node=node,
            scope_id=scope_id,
        ):
            return
        if self._declare_binding(
            node=node,
            scope_id=scope_id,
            annotation=annotation,
        ):
            return
        if is_owner and isinstance(
            node,
            (FunctionDef, AsyncFunctionDef, Lambda),
        ):
            self._visit_owner_callable(node=node, scope_id=scope_id)
        elif is_owner and isinstance(
            node,
            (ListComp, SetComp, DictComp, GeneratorExp),
        ):
            self._visit_owner_comprehension(node=node, scope_id=scope_id)
        else:
            for child, flag in self._children(
                node=node,
                annotation=annotation,
            ):
                self._visit(node=child, scope_id=scope_id, annotation=flag)
                self.graph.add(
                    consumer=self.identities.node_id(node=node),
                    producer=self.identities.node_id(node=child),
                    kind="DEPENDS_ON_VALUE",
                )
            self._link_dependencies(node=node)
