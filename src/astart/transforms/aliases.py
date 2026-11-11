"""Plan bounded PEP 695 alias extraction on the authoritative native AST."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    FunctionDef,
    Import,
    ImportFrom,
    Load,
    Name,
    ParamSpec,
    Starred,
    Store,
    Subscript,
    Tuple,
    TypeAlias,
    TypeVar,
    alias,
    arg,
    expr,
    type_param,
    unparse,
    walk,
)
from builtins import __dict__
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from typing import TYPE_CHECKING, final

from astart.source.node_attributes import read_attribute
from astart.transforms.alias_patterns import (
    AntiUnifier,
    Constants,
    Pattern,
    alias_name,
    children,
    head,
    key,
    normalize_type,
    rebuild,
)

if TYPE_CHECKING:
    from astart.semantic.analyzer import SemanticAnalyzer
    from astart.semantic.identities import Symbol
    from astart.semantic.scopes import ScopeGraph
    from astart.source.ast import CommentedModule
    from astart.source.transactions import AnnotationTransaction


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AliasSettings:
    """Bound conservative alias extraction and deterministic plan search.

    Attributes:
        min_repetitions (int): Required occurrences of a candidate.
        min_distinct_sites (int): Required distinct annotation owners.
        min_source_savings (int): Minimum canonical source characters saved.
        min_complexity (int): Minimum AST node count in a candidate body.
        max_candidates (int): Maximum generated candidate pool.
        max_generic_patterns (int): Maximum anti-unified generic templates.
        max_pattern_pairs (int): Maximum pairs examined for anti-unification.
        max_exact_candidates (int): Largest pool eligible for exhaustive
            search.
        max_plan_evaluations (int): Hard bound on complete plans priced.
        require_aliases (bool): Normalize repeated types before candidate
            discovery.

    """

    min_repetitions: int = 2
    min_distinct_sites: int = 2
    min_source_savings: int = 8
    min_complexity: int = 5
    max_candidates: int = 48
    max_generic_patterns: int = 24
    max_pattern_pairs: int = 1000
    max_exact_candidates: int = 9
    max_plan_evaluations: int = 512
    require_aliases: bool = False

    def __post_init__(self) -> None:
        """Reject invalid limits before indexing or staging any edits.

        Raises:
            ValueError: A count is negative or a required limit is zero.

        """
        if (
            min(
                self.min_repetitions,
                self.min_distinct_sites,
                self.max_candidates,
                self.max_plan_evaluations,
            )
            < 1
            or min(
                self.min_source_savings,
                self.min_complexity,
                self.max_generic_patterns,
                self.max_pattern_pairs,
                self.max_exact_candidates,
            )
            < 0
        ):
            msg: str = "Alias optimizer limits must be positive/nonnegative."
            raise ValueError(msg)


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Site:
    """One owned annotation field and its proven ordinary generic binders.

    Attributes:
        owner (AST): Existing field owner, retained by identity.
        field (str): Annotation or return field.
        annotation (expr): Original expression.
        parameters (tuple[str, ...]): Unconstrained parameters referenced by
            this expression.
        constructors (frozenset[str]): Type constructors visible at the
            original site.

    """

    owner: AST
    field: str
    annotation: expr
    parameters: tuple[str, ...]
    constructors: frozenset[str] = Constants.constructors


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Candidate:
    """A generated or existing declaration template.

    Attributes:
        name (str): Collision-free module binding.
        pattern (Pattern): Type-only structural pattern.
        existing (TypeAlias | None): Actual existing declaration, when reused.

    """

    name: str
    pattern: Pattern
    existing: TypeAlias | None = None

    def reference(self, *, arguments: tuple[expr, ...]) -> expr:
        """Build a fresh ordinary or specialized alias reference.

        Args:
            arguments (tuple[expr, ...]): Matched actual generic arguments.

        Returns:
            expr: Detached reference AST.

        """
        name: Name = Name(id=self.name, ctx=Load())
        return (
            Subscript(
                value=name,
                slice=deepcopy(x=arguments[0])
                if len(arguments) == 1
                else Tuple(
                    elts=[deepcopy(x=item) for item in arguments],
                    ctx=Load(),
                ),
                ctx=Load(),
            )
            if arguments
            else name
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Plan:
    """A completely priced combination of declarations and annotations.

    Attributes:
        declarations (tuple[TypeAlias, ...]): New declarations in dependency
            order.
        annotations (tuple[expr, ...]): Detached per-site rewritten
            expressions.
        cost (int): Canonical annotation and new declaration character count.
        repetitions (int): Repeated composite shapes remaining after
            substitution.

    """

    declarations: tuple[TypeAlias, ...]
    annotations: tuple[expr, ...]
    cost: int
    repetitions: int = 0


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class AliasChanges:
    """Evidence from a committed native alias transformation.

    Attributes:
        declarations (tuple[TypeAlias, ...]): Actual inserted PEP 695
            declaration nodes.
        declaration_ids (tuple[str, ...]): Stable module-qualified semantic
            identifiers.
        annotations_changed (int): Count of replaced annotation fields.
        source_savings (int): Canonical source characters saved, including
            aliases.
        candidates_considered (int): Size of the generated candidate pool.
        plans_evaluated (int): Number of complete candidate subsets priced.
        optimality_proven (bool): All subsets of the generated pool were
            priced.
        skipped (tuple[str, ...]): Conservative refusal explanations.

    """

    declarations: tuple[TypeAlias, ...]
    declaration_ids: tuple[str, ...]
    annotations_changed: int
    source_savings: int
    candidates_considered: int
    plans_evaluated: int
    optimality_proven: bool
    skipped: tuple[str, ...]


@final
class _Context:
    """Use native scope identities for hoisting and capture checks."""

    def __init__(self, *, tree: CommentedModule) -> None:
        """Index one native tree without parsing or building another AST.

        Args:
            tree (CommentedModule): Authoritative comment-aware module.

        """
        self.model: SemanticAnalyzer = tree.semantic
        self.graph: ScopeGraph = self.model.scopes
        self.reserved: set[str] = (
            set(__dict__)
            | {symbol.name for symbol in self.graph.symbols.values()}
            | {node.id for node in walk(node=tree) if isinstance(node, Name)}
        )
        self.skipped: list[str] = []
        self._comments: tuple[tuple[int, int], ...] = tuple(
            (comment.lineno, comment.col_offset) for comment in tree.comments
        )
        self._wildcard: bool = any(
            isinstance(node, alias) and node.name == "*"
            for node in walk(node=tree)
        )
        self._alias_names: dict[int, TypeAlias] = {
            id(node.name): node
            for node in tree.body
            if isinstance(node, TypeAlias)
        }
        self.alias_names: frozenset[str] = frozenset(
            node.name.id for node in self._alias_names.values()
        )
        self._origins: dict[int, str] = {
            id(item): statement.module or ""
            if isinstance(statement, ImportFrom)
            else item.name
            for statement in tree.body
            if isinstance(statement, (Import, ImportFrom))
            for item in statement.names
        }
        self.constructors: frozenset[str] = Constants.constructors | frozenset(
            node.name if isinstance(node, ClassDef) else node.name.id
            for node in tree.body
            if isinstance(node, (ClassDef, TypeAlias))
            and node.type_params
            and not (
                isinstance(node, ClassDef)
                and any(
                    isinstance(member, (FunctionDef, AsyncFunctionDef))
                    and member.name == "__class_getitem__"
                    for member in node.body
                )
            )
        )
        self.paramspecs: set[str] = set()
        self._legacy: dict[int, str] = self._legacy_binders(tree=tree)

    def _legacy_binders(self, *, tree: CommentedModule) -> dict[int, str]:
        """Recognize unconstrained typing binders by their actual import.

        Args:
            tree (CommentedModule): Original module containing legacy binder
                assignments.

        Returns:
            dict[int, str]: Target identities mapped to their proven binder
                category.

        """
        found: dict[int, str] = {}
        imports: dict[str, str] = {
            item.asname or item.name: item.name
            for statement in tree.body
            if isinstance(statement, ImportFrom)
            and statement.module == "typing"
            for item in statement.names
            if item.name in {"TypeVar", "ParamSpec"}
        }
        for node in tree.body:
            if (
                not isinstance(node, Assign)
                or len(node.targets) != 1
                or not (
                    isinstance(node.targets[0], Name)
                    and isinstance(node.value, Call)
                    and isinstance(node.value.func, Name)
                )
            ):
                continue
            category: str | None = imports.get(node.value.func.id)
            if (
                category is not None
                and len(node.value.args) <= 1
                and all(item.arg == "name" for item in node.value.keywords)
            ):
                symbol: int | None = self.graph.resolve(
                    name=node.value.func.id,
                    scope_id=self.graph.root_id,
                )
                if (
                    symbol is not None
                    and len(
                        self.graph.definitions(symbol_id=symbol),
                    )
                    == 1
                ):
                    found[id(node.targets[0])] = category
        return found

    def type_constructors(self, *, at: expr) -> frozenset[str]:
        """Exclude constructor names captured by a local binding.

        Args:
            at (expr): Original source annotation.

        Returns:
            frozenset[str]: Proven type-slot constructors visible at this site.

        """
        scope: int = self.graph.node_scopes.get(
            self.model.identities.node_id(node=at),
            self.graph.root_id,
        )
        return frozenset(
            name
            for name in self.constructors
            if self.graph.resolve(name=name, scope_id=scope)
            == (self.graph.resolve(name=name, scope_id=self.graph.root_id))
        )

    def parameters(self, *, node: expr) -> tuple[str, ...] | None:
        """Prove that an annotation can move to a module-level alias body.

        Args:
            node (expr): Original owned annotation.

        Returns:
            tuple[str, ...] | None:
                Ordinary binders, or None for ambiguous or unsafe syntax.

        """
        if read_attribute(node=node, name="lineno", kind=int) is None:
            return None
        if (
            self._wildcard
            or self._forward_string(node=node)
            or any(
                isinstance(child, (Call, Starred)) for child in walk(node=node)
            )
            or any(
                (node.lineno, node.col_offset)
                <= position
                < (
                    node.end_lineno or node.lineno,
                    node.end_col_offset or node.col_offset,
                )
                for position in self._comments
            )
        ):
            return None
        parameters: list[str] = []
        for child in walk(node=node):
            if isinstance(child, Attribute) and not self._attribute(
                node=child,
            ):
                return None
            if not isinstance(child, Name):
                continue
            permitted: bool | str = self._name(node=child)
            if permitted is False:
                return None
            if isinstance(permitted, str) and permitted not in parameters:
                parameters.append(permitted)
        return tuple(parameters)

    def _forward_string(self, *, node: expr) -> bool:
        """Refuse unresolved string types while preserving value payloads.

        Args:
            node (expr): Type-position expression.

        Returns:
            bool: Whether a forward string prevents proven scope-safe hoisting.

        """
        return (
            isinstance(node, Constant) and isinstance(node.value, str)
        ) or any(
            self._forward_string(node=child) for child in children(node=node)
        )

    def _attribute(self, *, node: Attribute) -> bool:
        """Accept qualified special forms only from known typing namespaces.

        Args:
            node (Attribute): Qualified annotation reference.

        Returns:
            bool: Whether qualification is known and context independent.

        """
        root: expr = node.value
        while isinstance(root, Attribute):
            root = root.value
        if not isinstance(root, Name) or node.attr in Constants.opaque:
            return False
        symbol_id: int | None = self.graph.resolve(
            name=root.id,
            scope_id=self.graph.root_id,
        )
        return symbol_id is not None and any(
            self._origins.get(id(declaration))
            in {
                "typing",
                "collections",
                "collections.abc",
                "re",
            }
            for declaration in self.graph.definitions(symbol_id=symbol_id)
        )

    def visible(self, *, name: str, at: expr) -> bool:
        """Check an existing alias against the source annotation's scope.

        Args:
            name (str): Existing module-level alias binding.
            at (expr): Original annotation receiving a possible reference.

        Returns:
            bool: Whether the reference reaches the actual module declaration.

        """
        scope: int = self.graph.node_scopes.get(
            self.model.identities.node_id(node=at),
            self.graph.root_id,
        )
        declaration: TypeAlias | None = next(
            (
                node
                for node in self._alias_names.values()
                if node.name.id == name
            ),
            None,
        )
        return (
            declaration is not None
            and self.precedes(declaration=declaration, at=at)
            and (self.graph.resolve(name=name, scope_id=scope))
            == (self.graph.resolve(name=name, scope_id=self.graph.root_id))
        )

    @staticmethod
    def precedes(*, declaration: TypeAlias, at: expr) -> bool:
        """Require proven source order before reusing an existing alias.

        Args:
            declaration (TypeAlias): Original module-level alias.
            at (expr): Source annotation receiving a reference.

        Returns:
            bool: Whether both positions prove that the alias is already
                defined.

        """
        line: int | None = read_attribute(
            node=declaration,
            name="lineno",
            kind=int,
        )
        target: int | None = read_attribute(node=at, name="lineno", kind=int)
        return line is not None and target is not None and line < target

    def stable_alias(self, *, node: TypeAlias) -> bool:
        """Require the exact declaration to be a binding's sole definition.

        Args:
            node (TypeAlias): Existing module-level alias declaration.

        Returns:
            bool: Whether the declaration has no
                competing definition or deletion.

        """
        symbol_id: int | None = self.graph.resolve(
            name=node.name.id,
            scope_id=self.graph.root_id,
        )
        definitions: tuple[AST, ...] = (
            self.graph.definitions(
                symbol_id=symbol_id,
            )
            if symbol_id is not None
            else ()
        )
        return len(definitions) == 1 and definitions[0] is node.name

    def _name(self, *, node: Name) -> bool | str:
        """Check one reference using the shared lexical symbol identity.

        Args:
            node (Name): Owned name occurrence in an annotation.

        Returns:
            bool | str:
                True for a stable global, a generic binder, or False if unsafe.

        """
        identity: int = self.model.identities.node_id(node=node)
        scope: int = self.graph.node_scopes.get(identity, self.graph.root_id)
        symbol_id: int | None = self.graph.resolve(
            name=node.id,
            scope_id=scope,
        )
        symbol: Symbol | None = (
            self.graph.symbols.get(symbol_id)
            if symbol_id is not None
            else None
        )
        if symbol is None:
            return node.id in __dict__ and node.id not in Constants.opaque
        definitions: tuple[AST, ...] = self.graph.definitions(
            symbol_id=symbol.id,
        )
        if len(definitions) != 1:
            return False
        return self._definition(
            node=node,
            declaration=definitions[0],
            symbol=symbol,
        )

    def _definition(
        self,
        *,
        node: Name,
        declaration: AST,
        symbol: Symbol,
    ) -> bool | str:
        """Classify a uniquely resolved definition for annotation hoisting.

        Args:
            node (Name): Annotation name occurrence.
            declaration (AST): Its sole original definition.
            symbol (Symbol): Shared lexical binding.

        Returns:
            bool | str:
                Stable globals, unconstrained binder names, or a safe refusal.

        """
        category: str | None = self._legacy.get(id(declaration))
        if category is not None:
            if category == "ParamSpec":
                self.paramspecs.add(node.id)
            return node.id
        if id(declaration) in self._alias_names:
            return symbol.scope_id == self.graph.root_id and self.precedes(
                declaration=self._alias_names[id(declaration)],
                at=node,
            )
        if isinstance(declaration, TypeVar):
            return (
                declaration.name
                if (
                    declaration.bound is None
                    and declaration.default_value is None
                )
                else False
            )
        if (
            isinstance(declaration, ParamSpec)
            and declaration.default_value is None
        ):
            self.paramspecs.add(declaration.name)
            return declaration.name
        if isinstance(declaration, alias) and (
            declaration.name in Constants.opaque
            or (
                declaration.name in {"Literal", "Annotated"}
                and node.id != declaration.name
            )
            or (
                node.id in Constants.constructors
                and self._origins.get(id(declaration))
                not in {
                    "typing",
                    "collections.abc",
                    "collections",
                    "re",
                }
            )
        ):
            return False
        return symbol.scope_id == self.graph.root_id and symbol.kind in {
            "class",
            "import",
            "type_alias",
        }


def _composites(
    *,
    node: expr,
    constructors: frozenset[str] = Constants.constructors,
    aliases: frozenset[str] = frozenset(),
) -> tuple[expr, ...]:
    """Collect ordinary composite types at type-only positions.

    Args:
        node (expr): Type-expression root.
        constructors (frozenset[str]): Proven type-slot constructors.
        aliases (frozenset[str]): Already factored declarations, excluded as
            new candidates.

    Returns:
        tuple[expr, ...]: Composite subexpressions, excluding
            restricted wrappers and metadata.

    """
    own: tuple[expr, ...] = (
        (node,)
        if (
            (
                isinstance(node, Subscript)
                and head(node=node.value) in constructors
                and head(node=node.value) not in aliases
                and head(node=node.value) not in Constants.opaque
            )
            or (isinstance(node, BinOp) and isinstance(node.op, BitOr))
        )
        else ()
    )
    return own + tuple(
        item
        for child in children(node=node, constructors=constructors)
        for item in _composites(
            node=child,
            constructors=constructors,
            aliases=aliases,
        )
    )


def _represent(
    *,
    node: expr,
    available: tuple[_Candidate, ...],
    constructors: frozenset[str] = Constants.constructors,
    force: bool = False,
) -> expr:
    """Find the shortest type-preserving representation at one position.

    Args:
        node (expr): Type expression, never mutated.
        available (tuple[_Candidate, ...]): Dependency-safe visible alias
            patterns.
        constructors (frozenset[str]): Proven type constructors at the source
            site.
        force (bool): Prefer an available alias even when its spelling is
            longer.

    Returns:
        expr: Fresh shortest representation with deterministic tie breaking.

    """
    normalized: expr = (
        normalize_type(node=node, constructors=constructors)
        if (force)
        else node
    )
    alternatives: list[expr] = [
        rebuild(
            node=normalized,
            parts=tuple(
                _represent(
                    node=child,
                    available=available,
                    constructors=constructors,
                    force=force,
                )
                for child in children(
                    node=normalized,
                    constructors=constructors,
                )
            ),
        ),
    ]
    for candidate in available:
        arguments: tuple[expr, ...] | None = candidate.pattern.match(
            target=normalized,
        )
        if arguments is not None:
            alternatives.append(candidate.reference(arguments=arguments))
    if force and len(alternatives) > 1:
        alternatives.pop(0)
    return min(
        alternatives,
        key=lambda item: (len(unparse(ast_obj=item)), unparse(ast_obj=item)),
    )


@final
class AliasOptimizer:
    """Extract conservative aliases using bounded deterministic cost search.

    Only expression proposals are copied. The module, executable nodes,
    comments, import order and existing aliases retain their identities.
    Assignability reductions are deliberately delegated to inference rather
    than inferred from a container or class name by this presentation pass.

    """

    def __init__(
        self,
        *,
        tree: CommentedModule,
        settings: AliasSettings | None = None,
        module_id: str = "",
    ) -> None:
        """Capture scope facts and a guarded transaction on the same tree.

        Args:
            tree (CommentedModule): Authoritative native module.
            settings (AliasSettings | None): Conservative thresholds and
                explicit search budgets.
            module_id (str): Stable namespace for declaration evidence
                identifiers.

        """
        self._tree: CommentedModule = tree
        self._settings: AliasSettings = settings or AliasSettings()
        self._module_id: str = module_id
        self._context: _Context = _Context(tree=tree)
        self._transaction: AnnotationTransaction = (
            tree.annotation_transaction()
        )
        self._sites: tuple[_Site, ...] = self._collect()
        self._existing: tuple[_Candidate, ...] = tuple(
            _Candidate(
                name=node.name.id,
                pattern=Pattern(
                    body=node.value,
                    parameters=tuple(
                        parameter.name
                        for parameter in node.type_params
                        if isinstance(parameter, (TypeVar, ParamSpec))
                    ),
                    paramspecs=frozenset(
                        parameter.name
                        for parameter in node.type_params
                        if isinstance(parameter, ParamSpec)
                    ),
                    constructors=self._context.constructors,
                ),
                existing=node,
            )
            for node in tree.body
            if isinstance(node, TypeAlias)
            and self._context.stable_alias(node=node)
            and all(
                isinstance(parameter, (TypeVar, ParamSpec))
                and (
                    not isinstance(parameter, TypeVar)
                    or parameter.bound is None
                )
                and parameter.default_value is None
                for parameter in node.type_params
            )
        )
        self._baseline: _Plan = self._evaluate(candidates=())

    def _collect(self) -> tuple[_Site, ...]:
        """Collect eligible annotation owners and explain refused sites.

        Returns:
            tuple[_Site, ...]: Owned fields with proven safe type dependencies.

        """
        sites: list[_Site] = []
        for node in walk(node=self._tree):
            annotation: expr | None = (
                node.annotation
                if isinstance(node, (arg, AnnAssign))
                else node.value
                if isinstance(node, TypeAlias)
                else node.returns
                if isinstance(
                    node,
                    (FunctionDef, AsyncFunctionDef),
                )
                else None
            )
            if annotation is None:
                continue
            parameters: tuple[str, ...] | None = self._context.parameters(
                node=annotation,
            )
            if parameters is None:
                line: int | None = read_attribute(
                    node=annotation,
                    name="lineno",
                    kind=int,
                )
                self._context.skipped.append(
                    f"line {line}: unsafe scope, payload or trivia",
                )
                continue
            sites.append(
                _Site(
                    owner=node,
                    field="annotation"
                    if isinstance(
                        node,
                        (arg, AnnAssign),
                    )
                    else "value"
                    if isinstance(node, TypeAlias)
                    else "returns",
                    annotation=annotation,
                    parameters=parameters or (),
                    constructors=self._context.type_constructors(
                        at=annotation,
                    ),
                ),
            )
        return tuple(sites)

    def _patterns(self) -> tuple[Pattern, ...]:
        """Generate repeated concrete and anti-unified generic templates.

        Returns:
            tuple[Pattern, ...]: Deduplicated templates satisfying
                repetition and site thresholds.

        """
        occurrences: dict[str, list[tuple[int, expr]]] = {}
        entries: list[tuple[int, expr]]
        identity: str
        for index, site in enumerate(iterable=self._sites):
            for node in _composites(
                node=site.annotation,
                constructors=site.constructors,
                aliases=self._context.alias_names,
            ):
                if self._context.parameters(node=node) is None:
                    continue
                normalized: expr = (
                    normalize_type(
                        node=node,
                        constructors=site.constructors,
                    )
                    if self._settings.require_aliases
                    else node
                )
                occurrences.setdefault(key(node=normalized), []).append(
                    (index, normalized),
                )
        patterns: dict[str, Pattern] = {}
        for identity, entries in occurrences.items():
            body: expr = entries[0][1]
            if self._frequent(entries=entries) and self._complex(node=body):
                names: set[str] = {
                    node.id
                    for node in walk(node=body)
                    if isinstance(node, Name)
                }
                patterns[identity] = Pattern(
                    body=body,
                    parameters=tuple(
                        name
                        for name in self._context.parameters(
                            node=self._sites[entries[0][0]].annotation,
                        )
                        or ()
                        if name in names
                    ),
                    paramspecs=frozenset(names & self._context.paramspecs),
                    constructors=self._context.constructors,
                )
        unique: list[expr] = [
            occurrences[item][0][1] for item in sorted(occurrences)
        ]
        count: int = 0
        for index, (left, right) in enumerate(
            iterable=combinations(iterable=unique, r=2),
        ):
            if index >= self._settings.max_pattern_pairs or (
                count >= self._settings.max_generic_patterns
            ):
                break
            pattern: Pattern | None = AntiUnifier(
                constructors=self._context.constructors,
            ).create(
                left=left,
                right=right,
            )
            if pattern is None or not self._complex(node=pattern.body):
                continue
            entries = [
                (site_index, node)
                for values in occurrences.values()
                for site_index, node in values
                if pattern.match(target=node) is not None
            ]
            identity = key(node=pattern.body)
            if self._frequent(entries=entries) and identity not in patterns:
                patterns[identity] = pattern
                count += 1
        return tuple(
            sorted(
                patterns.values(),
                key=lambda pattern: (
                    -sum(1 for _ in walk(node=pattern.body)),
                    key(node=pattern.body),
                ),
            ),
        )

    def _frequent(self, *, entries: list[tuple[int, expr]]) -> bool:
        """Check occurrence and distinct-site thresholds separately.

        Args:
            entries (list[tuple[int, expr]]): Matching annotation positions and
                expressions.

        Returns:
            bool: Whether both configured thresholds are satisfied.

        """
        return (
            len(entries) >= self._settings.min_repetitions
            and len({index for index, _ in entries})
            >= self._settings.min_distinct_sites
        )

    def _complex(self, *, node: expr) -> bool:
        """Apply the minimum complexity threshold without source parsing.

        Args:
            node (expr): Candidate type expression.

        Returns:
            bool: Whether it contains enough syntax to consider extraction.

        """
        return sum(1 for _ in walk(node=node)) >= self._settings.min_complexity

    def _candidates(self) -> tuple[_Candidate, ...]:
        """Assign stable names while avoiding every existing lexical binding.

        Returns:
            tuple[_Candidate, ...]: Bounded generated candidate pool in
                deterministic order.

        """
        reserved: set[str] = set(self._context.reserved)
        result: list[_Candidate] = []
        for pattern in self._patterns()[: self._settings.max_candidates]:
            base: str = alias_name(
                node=pattern.body,
                parameters=pattern.parameters,
            )
            digest: str = sha256(
                string=key(node=pattern.body).encode(encoding="utf-8"),
            ).hexdigest()
            name: str = base
            suffix: int = 0
            while name in reserved:
                name = f"{base}_{digest[:8]}" + (
                    f"_{suffix}" if suffix else ""
                )
                suffix += 1
            reserved.add(name)
            result.append(_Candidate(name=name, pattern=pattern))
        return tuple(result)

    def _evaluate(self, *, candidates: tuple[_Candidate, ...]) -> _Plan:
        """Price one complete combination including declaration overhead.

        Args:
            candidates (tuple[_Candidate, ...]): Selected candidate subset.

        Returns:
            _Plan: Dependency-safe declarations,
                rewrites and total canonical cost.

        """
        available: tuple[_Candidate, ...] = self._existing
        declarations: list[TypeAlias] = []
        for candidate in sorted(
            candidates,
            key=lambda item: (
                sum(1 for _ in walk(node=item.pattern.body)),
                item.name,
            ),
        ):
            body: expr = _represent(
                node=candidate.pattern.body,
                available=tuple(
                    item
                    for item in available
                    if item.name not in candidate.pattern.parameters
                    and (
                        item.existing is None
                        or all(
                            self._context.precedes(
                                declaration=item.existing,
                                at=site.annotation,
                            )
                            for site in self._sites
                        )
                    )
                ),
            )
            params: list[type_param] = [
                ParamSpec(name=name)
                if name in candidate.pattern.paramspecs
                else TypeVar(name=name)
                for name in candidate.pattern.parameters
            ]
            declarations.append(
                TypeAlias(
                    name=Name(id=candidate.name, ctx=Store()),
                    type_params=params,
                    value=body,
                ),
            )
            available = (*available, candidate)
        annotations: tuple[expr, ...] = tuple(
            _represent(
                node=site.annotation,
                available=tuple(
                    item
                    for item in available
                    if (
                        item.existing is None
                        and not isinstance(site.owner, TypeAlias)
                    )
                    or (
                        item.existing is not None
                        and item.existing is not site.owner
                        and self._context.visible(
                            name=item.name,
                            at=site.annotation,
                        )
                    )
                ),
            )
            for site in self._sites
        )
        return _Plan(
            declarations=tuple(declarations),
            annotations=annotations,
            cost=sum(len(unparse(ast_obj=node)) for node in annotations)
            + sum(len(unparse(ast_obj=node)) + 1 for node in declarations),
        )

    def _search(
        self,
        *,
        pool: tuple[_Candidate, ...],
    ) -> tuple[_Plan, int, bool]:
        """Enumerate small pools or use bounded deterministic local search.

        Args:
            pool (tuple[_Candidate, ...]): Generated candidates.

        Returns:
            tuple[_Plan, int, bool]: Best priced plan, evaluation count and
                exhaustive-search flag.

        """
        seen: set[frozenset[int]] = {frozenset()}
        exact: bool = (
            len(pool) <= self._settings.max_exact_candidates
            and (1 << len(pool)) <= self._settings.max_plan_evaluations
        )
        pending: deque[frozenset[int]] = deque(
            iterable=(frozenset({index}) for index in range(len(pool))),
        )
        best: _Plan = self._baseline
        if exact:
            pending = deque(
                iterable=(
                    frozenset(
                        index
                        for index in range(len(pool))
                        if mask & (1 << index)
                    )
                    for mask in range(1, 1 << len(pool))
                ),
            )
        queued: set[frozenset[int]] = set(pending)
        while pending and len(seen) < self._settings.max_plan_evaluations:
            active: frozenset[int] = pending.popleft()
            if active in seen:
                continue
            plan: _Plan = self._evaluate(
                candidates=tuple(pool[index] for index in sorted(active)),
            )
            seen.add(active)
            if self._order(plan=plan) <= self._order(plan=best):
                best = plan
                if not exact:
                    additions: tuple[frozenset[int], ...] = tuple(
                        active ^ {index}
                        for index in range(len(pool))
                        if active ^ {index} not in queued
                    )
                    pending.extend(additions)
                    queued.update(additions)
        return best, len(seen), exact

    @staticmethod
    def _order(*, plan: _Plan) -> tuple[int, int, tuple[str, ...]]:
        """Break equal-cost ties by declaration count and stable names.

        Args:
            plan (_Plan): Completely priced candidate plan.

        Returns:
            tuple[int, int, tuple[str, ...]]: Deterministic optimization order.

        """
        return (
            plan.cost,
            len(plan.declarations),
            tuple(node.name.id for node in plan.declarations),
        )

    def optimize(self) -> AliasChanges:
        """Stage and atomically commit the best safe native alias plan.

        Returns:
            AliasChanges:
                Committed declaration identities and measured search evidence.

        Raises:
            ValueError: The tree became stale or a declaration conflicts.
            TypeError: Native compiler validation rejects malformed syntax.
            SyntaxError: Proposed typing syntax is invalid.

        """
        pool: tuple[_Candidate, ...] = self._candidates()
        plan: _Plan
        plan, evaluated, exact = self._search(pool=pool)
        original: int = sum(
            len(unparse(ast_obj=site.annotation)) for site in self._sites
        )
        if original - plan.cost < self._settings.min_source_savings:
            plan = self._baseline
        changed: int = 0
        for declaration in plan.declarations:
            self._transaction.add_alias(declaration=declaration)
        for site, annotation in zip(
            self._sites,
            plan.annotations,
            strict=True,
        ):
            if key(node=site.annotation) != key(node=annotation):
                self._transaction.replace(
                    owner=site.owner,
                    field=site.field,
                    value=annotation,
                )
                changed += 1
        self._transaction.commit()
        return AliasChanges(
            declarations=plan.declarations,
            declaration_ids=tuple(
                f"alias:{self._module_id}:{node.name.id}"
                for node in plan.declarations
            ),
            annotations_changed=changed,
            source_savings=original - plan.cost,
            candidates_considered=len(pool),
            plans_evaluated=evaluated,
            optimality_proven=exact,
            skipped=tuple(self._context.skipped),
        )
