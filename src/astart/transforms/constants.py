"""Extract comparison literals using native nodes and lexical scopes."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Compare,
    Constant,
    FunctionDef,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Store,
    Subscript,
    UAdd,
    UnaryOp,
    USub,
    alias,
    expr,
    get_docstring,
    iter_child_nodes,
    iter_fields,
    walk,
)
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite
from typing import TYPE_CHECKING, Literal, final

from astart.source.node_attributes import list_items

if TYPE_CHECKING:
    from astart.semantic.scopes import Scope, ScopeGraph
    from astart.source.ast import CommentedModule
    from astart.source.formatting import FieldValue

type MagicScope = Literal["off", "module", "function", "class"]
type ConstantOwner = Module | FunctionDef | AsyncFunctionDef | ClassDef


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class MagicChanges:
    """Counts of native numeric replacements and explicit preservation.

    Attributes:
        values_changed (int): Literal occurrences replaced.
        constants_added (int): Unique typed definitions inserted.
        skipped (tuple[str, ...]): Scope cases requiring preservation.

    """

    values_changed: int
    constants_added: int
    skipped: tuple[str, ...]


def _numeric(*, node: AST) -> int | float | None:
    """Read a signed finite numeric literal without evaluating target code.

    Args:
        node (AST): Potential literal or unary sign expression.

    Returns:
        int | float | None:
            Numeric value, or None for nonliteral/bool/nonfinite input.

    """
    if isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
        value: int | float | None = _numeric(node=node.operand)
        return (
            -value
            if value is not None and isinstance(node.op, USub)
            else value
        )
    if isinstance(node, Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            return None
        if isinstance(node.value, float) and not isfinite(node.value):
            return None
        return node.value
    return None


def _fresh(*, preferred: str, names: set[str]) -> str:
    """Choose a deterministic unused identifier across all lexical scopes.

    Args:
        preferred (str): Intrinsic name of the inserted symbol.
        names (set[str]): Names already reserved, updated with the result.

    Returns:
        str: Collision-free spelling.

    """
    result: str = preferred
    count: int = 1
    while result in names:
        count += 1
        result = f"{preferred}_{count}"
    names.add(result)
    return result


@final
class NumericExtractor:
    """Plan typed constants against one existing AST and its scope graph."""

    def __init__(self, *, tree: CommentedModule, scope: MagicScope) -> None:
        """Bind the original module; no Python source is parsed.

        Args:
            tree (CommentedModule): Authoritative mutable module.
            scope (MagicScope): Requested insertion scope with module fallback.

        """
        self._tree: CommentedModule = tree
        self._mode: MagicScope = scope
        self._scopes: ScopeGraph = tree.semantic.scopes
        self._names: set[str] = {
            symbol.name for symbol in self._scopes.symbols.values()
        }
        self._names.update(
            node.id for node in walk(node=tree) if isinstance(node, Name)
        )
        self._definitions: dict[ConstantOwner, list[AnnAssign]] = {}
        self._symbols: dict[
            tuple[int, type[int | float], int | float],
            str,
        ] = {}
        self._builtins: str = _fresh(
            preferred="_astart_numbers",
            names=self._names,
        )
        self._typing: str = _fresh(
            preferred="_astart_final",
            names=self._names,
        )
        self._namespace: str = _fresh(
            preferred="ComparisonConstants",
            names=self._names,
        )
        self._skipped: list[str] = []
        self._class_cells: dict[int, bool] = {}
        self._owner_cache: dict[int, tuple[ConstantOwner, bool] | None] = {}

    def run(self) -> MagicChanges:
        """Replace literals and insert only the constants actually needed.

        Returns:
            MagicChanges: Native mutation counts and refused scope reasons.

        """
        replacements: dict[int, expr] = {}
        parents: dict[int, AST] = {}
        pending: list[tuple[AST, bool]] = [(self._tree, False)]
        while pending:
            node, in_comparison = pending.pop()
            numeric: int | float | None = _numeric(node=node)
            if in_comparison and numeric is not None:
                if numeric not in (-1, 0, 1):
                    replacement: expr | None = self._replacement(
                        node=node,
                        value=numeric,
                    )
                    if replacement is not None:
                        replacements[id(node)] = replacement
                continue
            for child in iter_child_nodes(node=node):
                parents[id(child)] = node
                pending.append(
                    (child, in_comparison or isinstance(node, Compare)),
                )
        for identity, replacement in replacements.items():
            self._replace_child(
                parent=parents[identity],
                identity=identity,
                replacement=replacement,
            )
        if replacements:
            self._insert_definitions()
        return MagicChanges(
            values_changed=len(replacements),
            constants_added=len(self._symbols),
            skipped=tuple(self._skipped),
        )

    def _owner(self, *, node: AST) -> tuple[ConstantOwner, bool] | None:
        """Resolve actual evaluation scope, including defaults and closures.

        Args:
            node (AST): Literal occurrence indexed by the existing scope graph.

        Returns:
            tuple[ConstantOwner, bool] | None:
                Definition owner plus class-cell requirement, or refusal.

        """
        if self._mode == "module":
            return self._tree, False
        identity: int = self._scopes.identities.node_id(node=node)
        scope_id: int | None = self._scopes.node_scopes.get(identity)
        if scope_id is None:
            self._skipped.append("unindexed comparison scope preserved")
            return None
        if scope_id not in self._owner_cache:
            self._owner_cache[scope_id] = self._resolve_owner(
                scope_id=scope_id,
            )
        return self._owner_cache[scope_id]

    def _resolve_owner(
        self,
        *,
        scope_id: int,
    ) -> tuple[ConstantOwner, bool] | None:
        """Resolve one lexical scope once per insertion pass.

        Args:
            scope_id (int): Existing lexical scope identity.

        Returns:
            tuple[ConstantOwner, bool] | None:
                Insertion owner and class-cell policy, or refusal.

        """
        current: int | None = scope_id
        crossed_function: bool = False
        crossed_real_function: bool = False
        crossed_comprehension: bool = False
        while current is not None:
            scope: Scope = self._scopes.scopes[current]
            owner: AST = self._scopes.node_index[scope.owner_node_id]
            if self._mode == "function" and isinstance(
                owner,
                (FunctionDef, AsyncFunctionDef),
            ):
                return owner, False
            if self._mode == "class" and isinstance(owner, ClassDef):
                reason: str | None = None
                if crossed_function and (
                    not crossed_real_function
                    or not self._safe_class_cell(owner=owner)
                ):
                    reason = "class construction callable preserved"
                elif crossed_comprehension and not crossed_function:
                    reason = "class-body comprehension preserved"
                elif (
                    crossed_function
                    and self._scopes.resolve(
                        name="__class__",
                        scope_id=scope_id,
                    )
                    is not None
                ):
                    reason = "explicit __class__ binding preserved"
                if reason is not None:
                    self._skipped.append(reason)
                    return None
                return owner, crossed_function
            crossed_function |= scope.kind in ("function", "lambda")
            crossed_real_function |= scope.kind == "function"
            crossed_comprehension |= scope.kind == "comprehension"
            current = scope.parent_id
        return self._tree, False

    def _safe_class_cell(self, *, owner: ClassDef) -> bool:
        """Refuse class cells that can be observed during class construction.

        Args:
            owner (ClassDef): Class receiving constants used by one of its
                methods.

        Returns:
            bool: Whether the simple class construction has no early call
                hooks.

        """
        identity: int = id(owner)
        if identity not in self._class_cells:
            self._class_cells[identity] = self._class_without_early_hooks(
                owner=owner,
            )
        return self._class_cells[identity]

    def _class_without_early_hooks(self, *, owner: ClassDef) -> bool:
        """Inspect construction hooks once for a class.

        Args:
            owner (ClassDef): Class whose cell might be captured by generated
                references.

        Returns:
            bool: Whether the existing construction avoids early method calls.

        """
        if owner.bases or owner.keywords or owner.decorator_list:
            return False
        identity: int = self._scopes.identities.node_id(node=owner)
        for node in walk(node=owner):
            scope_id: int | None = self._scopes.node_scopes.get(
                self._scopes.identities.node_id(node=node),
            )
            if scope_id != identity:
                continue
            if isinstance(node, Call):
                return False
            if (
                isinstance(node, (FunctionDef, AsyncFunctionDef))
                and node.decorator_list
            ):
                return False
        return True

    def _replacement(self, *, node: AST, value: float) -> expr | None:
        """Allocate one constant and construct its correctly scoped reference.

        Args:
            node (AST): Original signed numeric expression.
            value (float): Its statically known finite value.

        Returns:
            expr | None:
                A fresh reference expression, or None for ambiguous ownership.

        """
        found: tuple[ConstantOwner, bool] | None = self._owner(node=node)
        if found is None or not isinstance(node, expr):
            return None
        owner, class_cell = found
        key: tuple[int, type[int | float], int | float] = (
            id(owner),
            type(value),
            value,
        )
        name: str | None = self._symbols.get(key)
        if name is None:
            kind: str = "FLOAT" if isinstance(value, float) else "INT"
            intrinsic: str = (
                repr(value)
                .replace("-", "NEG_")
                .replace(
                    "+",
                    "POS_",
                )
                .replace(".", "_")
            )
            name = _fresh(preferred=f"{kind}_{intrinsic}", names=self._names)
            self._symbols[key] = name
            self._definitions.setdefault(owner, []).append(
                AnnAssign(
                    target=Name(id=name, ctx=Store()),
                    annotation=Subscript(
                        value=Attribute(
                            value=Name(id=self._typing, ctx=Load()),
                            attr="Final",
                            ctx=Load(),
                        ),
                        slice=Attribute(
                            value=Name(id=self._builtins, ctx=Load()),
                            attr="float" if kind == "FLOAT" else "int",
                            ctx=Load(),
                        ),
                        ctx=Load(),
                    ),
                    value=deepcopy(x=node),
                    simple=1,
                ),
            )
        if owner is self._tree or class_cell:
            return Attribute(
                value=Name(
                    id="__class__" if class_cell else self._namespace,
                    ctx=Load(),
                ),
                attr=name,
                ctx=Load(),
            )
        return Name(id=name, ctx=Load())

    @staticmethod
    def _replace_child(
        *,
        parent: AST,
        identity: int,
        replacement: expr,
    ) -> None:
        """Replace one recorded expression without reparsing its container.

        Args:
            parent (AST): Original owning syntax node.
            identity (int): Original child identity.
            replacement (expr): New expression with independent child
                identities.

        """
        for field, item in iter_fields(node=parent):
            value: FieldValue = item
            children: list[FieldValue] = list_items(value=value)
            if isinstance(value, AST) and id(value) == identity:
                setattr(parent, field, replacement)
            elif isinstance(value, list):
                for index, child in enumerate(iterable=children):
                    if isinstance(child, AST) and id(child) == identity:
                        value[index] = replacement

    def _insert_definitions(self) -> None:
        """Insert imports and typed definitions into existing owner bodies."""
        position: int = int(get_docstring(node=self._tree) is not None)
        while position < len(self._tree.body) and isinstance(
            self._tree.body[position],
            (Import, ImportFrom),
        ):
            position += 1
        self._tree.body[position:position] = [
            Import(names=[alias(name="builtins", asname=self._builtins)]),
            Import(names=[alias(name="typing", asname=self._typing)]),
        ]
        position += 2
        for owner, definitions in self._definitions.items():
            if owner is self._tree:
                self._tree.body.insert(
                    position,
                    ClassDef(
                        name=self._namespace,
                        bases=[],
                        keywords=[],
                        body=list(definitions),
                        decorator_list=[
                            Attribute(
                                value=Name(id=self._typing, ctx=Load()),
                                attr="final",
                                ctx=Load(),
                            ),
                        ],
                        type_params=[],
                    ),
                )
            else:
                index: int = int(get_docstring(node=owner) is not None)
                owner.body[index:index] = definitions


def extract_magic(
    *,
    tree: CommentedModule,
    scope: MagicScope,
) -> MagicChanges:
    """Extract finite comparison literals with explicit scope selection.

    Args:
        tree (CommentedModule): Existing mutable module.
        scope (MagicScope): Off, module, function or class; absent owners use
            module scope.

    Returns:
        MagicChanges: Native mutation counts and preservation reasons.

    """
    if scope == "off":
        return MagicChanges(values_changed=0, constants_added=0, skipped=())
    return NumericExtractor(tree=tree, scope=scope).run()
