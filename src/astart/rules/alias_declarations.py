"""Recognize annotation-only legacy aliases using the native lexical graph."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Import,
    ImportFrom,
    List,
    Load,
    Name,
    ParamSpec,
    Subscript,
    Tuple,
    TypeAlias,
    TypeVar,
    TypeVarTuple,
    expr,
    type_param,
    walk,
)
from builtins import __dict__
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from astart.source.node_attributes import reclassify_node
from astart.transforms.alias_patterns import Constants as TypeConstants

if TYPE_CHECKING:
    from astart.semantic.identities import Role
    from astart.semantic.scopes import ScopeGraph
    from astart.source.ast import CommentedModule


@final
class Constants:
    """Trusted typing syntax, independent of user-chosen alias names.

    Attributes:
        origins (Final[frozenset[str]]): Modules providing known type
            constructors.
        forbidden (Final[frozenset[str]]): Contextual special forms that cannot
            be alias bodies.

    """

    origins: Final[frozenset[str]] = frozenset(
        {
            "typing",
            "typing_extensions",
            "collections.abc",
            "collections",
            "re",
        },
    )
    forbidden: Final[frozenset[str]] = TypeConstants.opaque | {"TypeAlias"}


@final
@dataclass(frozen=True, slots=True)
class LegacyAlias:
    """An existing declaration whose name and RHS must retain identity.

    Attributes:
        statement (Assign | AnnAssign): Original assignment owner.
        name (Name): Sole target name.
        value (expr): Original type expression.
        parameters (tuple[type_param, ...]): Fresh ordinary type parameters for
            legacy generic aliases.

    """

    statement: Assign | AnnAssign
    name: Name
    value: expr
    parameters: tuple[type_param, ...] = ()


@final
class AliasDeclarations:
    """Lazily index one facts batch, without parsing or executing source."""

    def __init__(self) -> None:
        """Create an empty per-batch declaration cache."""
        self._module: CommentedModule | None = None
        self._plans: dict[int, LegacyAlias] = {}

    def get(
        self,
        *,
        module: CommentedModule,
        statement: AST | None,
    ) -> LegacyAlias | None:
        """Find a type-only binding using the shared lexical symbol index.

        Args:
            module (CommentedModule): Authoritative mutable source tree.
            statement (AST | None): Assignment under consideration.

        Returns:
            LegacyAlias | None: A safe declaration plan, or None
                for an ordinary/runtime binding.

        """
        if self._module is not module:
            self._module = module
            possible: bool = any(
                (plan := _AliasIndex.assignment(node=node)) is not None
                and isinstance(plan.value, (Name, Attribute, Subscript, BinOp))
                for node in module.body
            )
            self._plans = (
                _AliasIndex(module=module).plans() if possible else {}
            )
        return self._plans.get(id(statement))

    def apply(self, *, module: CommentedModule, statement: AST | None) -> None:
        """Convert an eligible owner in place, retaining its name and RHS.

        Args:
            module (CommentedModule): Authoritative mutable tree.
            statement (AST | None): Original assignment owner.

        """
        plan: LegacyAlias | None = self.get(module=module, statement=statement)
        if plan is None or isinstance(plan.statement, TypeAlias):
            return
        reclassify_node(
            node=plan.statement,
            kind=TypeAlias,
            removed=(
                "targets",
                "target",
                "annotation",
                "simple",
                "type_comment",
            ),
            fields={"name": plan.name, "type_params": list(plan.parameters)},
        )
        used: set[str] = {
            node.id
            for node in walk(node=module)
            if isinstance(node, Name) and isinstance(node.ctx, Load)
        }
        for node in tuple(module.body):
            if isinstance(node, ImportFrom) and node.module in {
                "typing",
                "typing_extensions",
            }:
                node.names[:] = [
                    item
                    for item in node.names
                    if item.name != "TypeAlias"
                    or (item.asname or item.name) in used
                ]
                if not node.names:
                    module.body.remove(node)
            elif isinstance(node, Import):
                node.names[:] = [
                    item
                    for item in node.names
                    if item.name not in {"typing", "typing_extensions"}
                    or (item.asname or item.name) in used
                ]
                if not node.names:
                    module.body.remove(node)


@final
class _AliasIndex:
    """Prove type expressions and propagate runtime refusal across aliases."""

    def __init__(self, *, module: CommentedModule) -> None:
        """Reuse owned nodes and semantic identities for one linear index.

        Args:
            module (CommentedModule): Source module with its existing semantic
                analyzer.

        """
        self._module: CommentedModule = module
        self._graph: ScopeGraph = module.semantic.scopes
        self._imports: dict[int, str] = {
            id(item): f"{node.module}.{item.name}"
            if isinstance(node, ImportFrom)
            else item.name
            for node in module.body
            if isinstance(node, (Import, ImportFrom))
            and (not isinstance(node, ImportFrom) or node.level == 0)
            for item in node.names
        }
        self._candidates: dict[str, LegacyAlias] = {}
        self._active: set[str] = set()
        self._proven: dict[str, bool] = {}
        self._binders: dict[str, type_param] = {}
        self._native_names: frozenset[int] = frozenset(
            id(node.name)
            for node in module.body
            if isinstance(node, TypeAlias)
        )
        for node in module.body:
            plan: LegacyAlias | None = self.assignment(node=node)
            if plan is not None:
                self._candidates[plan.name.id] = plan
        for name, plan in self._candidates.items():
            value: expr = plan.value
            if not isinstance(value, Call) or any(
                item.arg != "name" for item in value.keywords
            ):
                continue
            factory: str | None = self._reference(node=value.func)
            if factory is None or factory.rpartition(".")[0] not in {
                "typing",
                "typing_extensions",
            }:
                continue
            kind: str = factory.rpartition(".")[2]
            if (
                kind not in {"TypeVar", "ParamSpec", "TypeVarTuple"}
                or len(value.args) + len(value.keywords) != 1
            ):
                continue
            if self._definition(name=name) is not plan.name:
                continue
            self._binders[name] = (
                ParamSpec(name=name, default_value=None)
                if kind == "ParamSpec"
                else TypeVarTuple(name=name, default_value=None)
                if kind == "TypeVarTuple"
                else TypeVar(name=name, bound=None, default_value=None)
            )

    @staticmethod
    def assignment(*, node: AST) -> LegacyAlias | None:
        """Read a single-name alias-shaped assignment without rewriting it.

        Args:
            node (AST): Top-level statement.

        Returns:
            LegacyAlias | None: Original owner/name/value, excluding
                destructuring and None values.

        """
        if (
            isinstance(node, Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], Name)
        ):
            return LegacyAlias(
                statement=node,
                name=node.targets[0],
                value=node.value,
            )
        if (
            isinstance(node, AnnAssign)
            and isinstance(node.target, Name)
            and node.value is not None
        ):
            return LegacyAlias(
                statement=node,
                name=node.target,
                value=node.value,
            )
        return None

    def _definition(self, *, name: str) -> AST | None:
        """Resolve a unique module binding, including shadowing definitions.

        Args:
            name (str): Identifier used in a type expression.

        Returns:
            AST | None: The sole definition, or None when absent or ambiguous.

        """
        symbol: int | None = self._graph.resolve(
            name=name,
            scope_id=self._graph.root_id,
        )
        definitions: tuple[AST, ...] = (
            self._graph.definitions(symbol_id=symbol)
            if symbol is not None
            else ()
        )
        return definitions[0] if len(definitions) == 1 else None

    def _reference(self, *, node: expr) -> str | None:
        """Resolve a trusted imported type spelling or an unshadowed builtin.

        Args:
            node (expr): Name or qualified imported expression.

        Returns:
            str | None:
                Canonical reference, or None when its meaning is not proven.

        """
        if isinstance(node, Name):
            definition: AST | None = self._definition(name=node.id)
            if definition is None:
                return (
                    node.id
                    if self._graph.resolve(
                        name=node.id,
                        scope_id=self._graph.root_id,
                    )
                    is None
                    and isinstance(__dict__.get(node.id), type)
                    else None
                )
            return self._imports.get(id(definition))
        if isinstance(node, Attribute):
            prefix: str | None = self._reference(node=node.value)
            return f"{prefix}.{node.attr}" if prefix is not None else None
        return None

    def _type(self, *, node: expr) -> bool:
        """Recognize ordinary type syntax, keeping Literal payloads opaque.

        Args:
            node (expr): RHS expression or a genuine type argument.

        Returns:
            bool: Whether the expression is a statically known type contract.

        """
        reference: str | None = self._reference(node=node)
        if reference is not None:
            origin, _, name = reference.rpartition(".")
            return not origin or (
                origin in Constants.origins
                and name not in Constants.forbidden
                and (
                    name in TypeConstants.constructors
                    or name
                    in {
                        "Any",
                        "Never",
                        "NoReturn",
                        "LiteralString",
                        "List",
                        "Dict",
                        "Set",
                        "FrozenSet",
                        "Tuple",
                        "Type",
                    }
                )
            )
        if isinstance(node, Name):
            definition: AST | None = self._definition(name=node.id)
            return (
                node.id in self._binders
                or isinstance(definition, ClassDef)
                or (
                    isinstance(definition, Name)
                    and (
                        id(definition) in self._native_names
                        or self._candidate(name=node.id)
                    )
                )
            )
        if isinstance(node, BinOp) and isinstance(node.op, BitOr):
            return self._argument(node=node.left) and self._argument(
                node=node.right,
            )
        if isinstance(node, Subscript):
            return self._subscript(node=node)
        return False

    def _subscript(self, *, node: Subscript) -> bool:
        """Check known generic type slots without interpreting value payloads.

        Args:
            node (Subscript): Original subscription expression.

        Returns:
            bool: Whether the subscription denotes a supported type.

        """
        origin: str | None = self._reference(node=node.value)
        if origin is None or not self._type(node=node.value):
            return False
        name: str = origin.rpartition(".")[2]
        if "." not in origin and name not in TypeConstants.constructors:
            return False
        arguments: list[expr] = (
            node.slice.elts if isinstance(node.slice, Tuple) else [node.slice]
        )
        if name == "Literal":
            return bool(arguments) and all(
                isinstance(item, Constant) for item in arguments
            )
        if name == "Annotated":
            return (
                bool(arguments)
                and self._type(node=arguments[0])
                and all(isinstance(item, Constant) for item in arguments[1:])
            )
        return all(self._argument(node=item) for item in arguments)

    def _argument(self, *, node: expr) -> bool:
        """Accept ordinary type slots, callable parameter lists and sentinels.

        Args:
            node (expr): Type argument, never an executable expression.

        Returns:
            bool: Whether the argument is supported without runtime evaluation.

        """
        if isinstance(node, Constant):
            return node.value is None or node.value is Ellipsis
        if isinstance(node, List):
            return all(self._type(node=item) for item in node.elts)
        return self._type(node=node)

    def _candidate(self, *, name: str) -> bool:
        """Memoize dependency-safe alias bodies, refusing cycles and rebinding.

        Args:
            name (str): Original alias identifier, with no naming heuristics.

        Returns:
            bool: Whether this binding is a stable type-only candidate.

        """
        if name in self._proven:
            return self._proven[name]
        plan: LegacyAlias | None = self._candidates.get(name)
        if plan is None or name in self._active:
            return False
        self._active.add(name)
        result: bool = self._definition(name=name) is plan.name and self._type(
            node=plan.value,
        )
        if isinstance(plan.statement, AnnAssign):
            annotation: expr = plan.statement.annotation
            marker: str | None = self._reference(
                node=annotation.value
                if isinstance(annotation, Subscript)
                else annotation,
            )
            result = result and marker not in {
                "typing.Final",
                "typing.ClassVar",
                "typing_extensions.Final",
                "typing_extensions.ClassVar",
            }
        self._active.remove(name)
        self._proven[name] = result
        return result

    def plans(self) -> dict[int, LegacyAlias]:
        """Propagate runtime refusals in linear dependency-graph order.

        Returns:
            dict[int, LegacyAlias]: Safe original assignment identities and
                their native plans.

        """
        safe: dict[str, LegacyAlias] = {
            name: plan
            for name, plan in self._candidates.items()
            if self._candidate(name=name)
        }
        if any(
            isinstance(node, ImportFrom)
            and any(item.name == "*" for item in node.names)
            for node in self._module.body
        ):
            return {}
        type_reads: dict[int, str] = {
            id(child): name
            for name, plan in safe.items()
            for child in walk(node=plan.value)
        }
        metadata: set[int] = self._metadata_reads()
        dependencies: dict[str, set[str]] = {name: set() for name in safe}
        refused: set[str] = set()
        for name in safe:
            symbol: int | None = self._graph.resolve(
                name=name,
                scope_id=self._graph.root_id,
            )
            if symbol is None:
                refused.add(name)
                continue
            for reference in self._graph.references(symbol_id=symbol):
                owner: str | None = type_reads.get(id(reference))
                roles: frozenset[Role] = self._graph.occurrences[
                    self._graph.identities.node_id(node=reference)
                ].roles
                if id(reference) in metadata or (
                    owner is None and "ANNOTATION" not in roles
                ):
                    refused.add(name)
                elif owner is not None:
                    dependencies[owner].add(name)
        pending: deque[str] = deque(iterable=refused)
        while pending:
            for dependency in dependencies[pending.popleft()] - refused:
                refused.add(dependency)
                pending.append(dependency)
        return {
            id(plan.statement): LegacyAlias(
                statement=plan.statement,
                name=plan.name,
                value=plan.value,
                parameters=tuple(
                    deepcopy(x=self._binders[binder])
                    for binder in dict.fromkeys(
                        child.id
                        for child in walk(node=plan.value)
                        if isinstance(child, Name)
                        and child.id in self._binders
                    )
                ),
            )
            for name, plan in safe.items()
            if name not in refused
        }

    def _metadata_reads(self) -> set[int]:
        """Keep runtime metadata objects outside the type-only read set.

        Returns:
            set[int]: Identities in Literal values or Annotated metadata slots.

        """
        result: set[int] = set()
        for node in walk(node=self._module):
            if not isinstance(node, Subscript):
                continue
            reference: str | None = self._reference(node=node.value)
            if reference not in {
                "typing.Annotated",
                "typing_extensions.Annotated",
                "typing.Literal",
                "typing_extensions.Literal",
            }:
                continue
            arguments: list[expr] = (
                node.slice.elts
                if isinstance(node.slice, Tuple)
                else [node.slice]
            )
            payloads: list[expr] = (
                arguments[1:]
                if reference.endswith(".Annotated")
                else arguments
            )
            result.update(
                id(child)
                for payload in payloads
                for child in walk(node=payload)
            )
        return result
