"""Semantic AST helpers for protocol, type-variable, and cast generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from ast import (
    Add,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Div,
    Expr,
    FloorDiv,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Load,
    Mod,
    Module,
    Mult,
    Name,
    ParamSpec,
    Return,
    Store,
    Sub,
    Subscript,
    TypeVar,
    alias,
    arg,
    expr,
    fix_missing_locations,
    stmt,
    type_param,
    unparse,
)
from ast import List as AstList
from ast import Tuple as AstTuple
from ast import arguments as ast_arguments
from ast import keyword as ast_keyword
from dataclasses import dataclass, field
from enum import StrEnum
from keyword import iskeyword
from re import sub
from sys import stdlib_module_names
from typing import TYPE_CHECKING, Final, Literal, Never, final

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
ExistingTopNode = (
    Import
    | ImportFrom
    | ClassDef
    | FunctionDef
    | AsyncFunctionDef
    | Assign
    | AnnAssign
)
ArgumentKind = Literal[
    "positional_only",
    "positional_or_keyword",
    "keyword_only",
    "vararg",
    "kwarg",
]
ImportSourceKind = Literal["absolute", "relative"]
LiteralValue = str | int | float | bool | None


@final
class Constants:
    """Group module-level constants.

    Attributes:
        two_item_count: Grouped module constant.

    """

    two_item_count: Final[int] = 2


class SemanticCodegenError(ValueError):
    """Raised when semantic AST generation receives invalid input."""


def fail(*, message: str) -> Never:
    """Raise a semantic code-generation error.

    Args:
        message: Message supplied as str for this operation.

    Raises:
        SemanticCodegenError: If this operation cannot satisfy its documented
            contract.

    """
    raise SemanticCodegenError(message)


class IdentifierValidator:
    """Validate Python identifiers used by generated nodes."""

    @staticmethod
    def validate_identifier(*, name: str, label: str) -> None:
        """Validate a single identifier.

        Args:
            name: Identifier to validate.
            label: Human-readable label for error messages.

        Raises:
            ValueError: If the name is not a valid Python identifier.

        """
        if not name.isidentifier() or iskeyword(name):
            msg: str = f"Invalid {label}: {name!r}."
            fail(message=msg)

    def validate_module_parts(self, *, parts: Sequence[str]) -> None:
        """Validate dotted module path parts.

        Args:
            parts: Module path components.

        """
        for part in parts:
            self.validate_identifier(name=part, label="module part")


@dataclass(slots=True, frozen=True)
class ExistingImportedName:
    """A name already available in the target generation context.

    Attributes:
        imported_name: Identifier used to refer to the imported.
        is_module_import: Is module import retained as bool by this instance.
        level: Level retained as int by this instance.
        local_name: Identifier used to refer to the local.
        module: Module retained as str | None by this instance.

    """

    local_name: str
    module: str | None
    imported_name: str
    level: int
    is_module_import: bool


@dataclass(slots=True, frozen=True)
class ExistingModuleImport:
    """Existing ``import module`` data.

    Attributes:
        local_name: Identifier used to refer to the local.
        module: Module retained as str by this instance.

    """

    module: str
    local_name: str


@dataclass(slots=True, frozen=True)
class ExistingNodeContext:
    """Existing import/class nodes used as generation context.

    Attributes:
        bound_names: Names bound by existing functions and assignments.
        class_nodes: Class nodes retained as tuple[ClassDef, ...] by this
            instance.
        import_nodes: Import nodes retained as tuple[Import | ImportFrom, ...]
            by this instance.

    """

    import_nodes: tuple[Import | ImportFrom, ...]
    class_nodes: tuple[ClassDef, ...]
    bound_names: tuple[str, ...] = ()

    @classmethod
    def from_nodes(
        cls,
        *,
        nodes: Iterable[ExistingTopNode],
    ) -> ExistingNodeContext:
        """Create context from a sequence of existing nodes.

        Args:
            nodes: Import and class nodes already present in the file.

        Returns:
            Existing-node context split into imports and classes.

        """
        import_nodes: list[Import | ImportFrom] = []
        class_nodes: list[ClassDef] = []
        bound_names: list[str] = []
        for node in nodes:
            if isinstance(node, Import | ImportFrom):
                import_nodes.append(node)
            elif isinstance(node, ClassDef):
                class_nodes.append(node)
            elif isinstance(node, FunctionDef | AsyncFunctionDef):
                bound_names.append(node.name)
            elif isinstance(node, AnnAssign):
                if isinstance(node.target, Name):
                    bound_names.append(node.target.id)
            else:
                bound_names.extend(
                    target.id
                    for target in node.targets
                    if isinstance(target, Name)
                )
        return cls(
            import_nodes=tuple(import_nodes),
            class_nodes=tuple(class_nodes),
            bound_names=tuple(bound_names),
        )


@dataclass(slots=True)
class ScriptSymbolIndex:
    """Index of names already available in the generation context.

    Attributes:
        imported_from: Imported from retained as dict[tuple[str | None, int,
            str], str] by this instance.
        imported_names: Imported names retained as dict[str,
            ExistingImportedName] by this instance.
        local_class_names: Local class names retained as set[str] by this
            instance.
        module_imports: Module imports retained as dict[str,
            ExistingModuleImport] by this instance.
        wildcard_imports: Wildcard imports retained as set[tuple[str | None,
            int]] by this instance.

    """

    local_class_names: set[str] = field(default_factory=set)
    imported_names: dict[str, ExistingImportedName] = field(
        default_factory=dict,
    )
    imported_from: dict[tuple[str | None, int, str], str] = field(
        default_factory=dict,
    )
    module_imports: dict[str, ExistingModuleImport] = field(
        default_factory=dict,
    )
    wildcard_imports: set[tuple[str | None, int]] = field(default_factory=set)

    @classmethod
    def from_context(
        cls,
        *,
        context: ExistingNodeContext,
    ) -> ScriptSymbolIndex:
        """Build a symbol index from an existing-node context.

        Args:
            context: Existing import and class nodes.

        Returns:
            Populated symbol index.

        """
        index: ScriptSymbolIndex = cls()
        for class_node in context.class_nodes:
            index.local_class_names.add(class_node.name)
        index.local_class_names.update(context.bound_names)
        for import_node in context.import_nodes:
            if isinstance(import_node, ImportFrom):
                index._record_import_from(node=import_node)
            else:
                index._record_import(node=import_node)
        return index

    def is_name_available(self, *, name: str) -> bool:
        """Return whether a simple name already exists.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Whether the requested condition holds.

        """
        return name in self.local_class_names or name in self.imported_names

    def find_imported_from(
        self,
        *,
        module: str | None,
        level: int,
        name: str,
    ) -> str | None:
        """Return local name for an existing ``from`` import.

        Args:
            level: Level supplied as int for this operation.
            module: The module examined while return local name for an existing
                ``from`` import.
            name: Identifier of the name being resolved.

        Returns:
            str | None produced by this operation.

        """
        return self.imported_from.get((module, level, name))

    def has_wildcard_from(self, *, module: str | None, level: int) -> bool:
        """Return whether a matching wildcard import exists.

        Args:
            level: Level supplied as int for this operation.
            module: The module examined while return whether a matching
                wildcard import exists.

        Returns:
            Whether the requested condition holds.

        """
        return (module, level) in self.wildcard_imports

    def _record_import_from(self, *, node: ImportFrom) -> None:
        """Record an existing ``from module import name`` node.

        Args:
            node: The node examined while record an existing ``from module
                import name`` node.

        """
        for imported_alias in node.names:
            if imported_alias.name == "*":
                self.wildcard_imports.add((node.module, node.level))
                continue
            local_name: str = imported_alias.asname or imported_alias.name
            self.imported_names[local_name] = ExistingImportedName(
                local_name=local_name,
                module=node.module,
                imported_name=imported_alias.name,
                level=node.level,
                is_module_import=False,
            )
            self.imported_from[
                node.module,
                node.level,
                imported_alias.name,
            ] = local_name

    def _record_import(self, *, node: Import) -> None:
        """Record an existing ``import module`` node.

        Args:
            node: The node examined while record an existing ``import module``
                node.

        """
        for imported_alias in node.names:
            local_name: str = (
                imported_alias.asname
                or imported_alias.name.split(sep=".", maxsplit=1)[0]
            )
            self.module_imports[local_name] = ExistingModuleImport(
                module=imported_alias.name,
                local_name=local_name,
            )
            self.imported_names[local_name] = ExistingImportedName(
                local_name=local_name,
                module=imported_alias.name,
                imported_name=imported_alias.name,
                level=0,
                is_module_import=True,
            )


class ImportUsePlace(StrEnum):
    """Semantic place where an imported symbol is used.

    Attributes:
        ANNOTATION: Annotation associated with this instance.
        METHOD_BODY: Method body associated with this instance.
        PARAMSPEC_DECLARATION: Paramspec declaration associated with this
            instance.
        PROTOCOL_BASE: Protocol base associated with this instance.
        RUNTIME: Runtime associated with this instance.
        STRING_TYPE_HINT: String type hint associated with this instance.
        TYPEVAR_BOUND: Typevar bound associated with this instance.
        TYPEVAR_CONSTRAINT: Typevar constraint associated with this instance.
        TYPEVAR_DECLARATION: Typevar declaration associated with this instance.

    """

    RUNTIME = "runtime"
    ANNOTATION = "annotation"
    STRING_TYPE_HINT = "string_type_hint"
    TYPEVAR_DECLARATION = "typevar_declaration"
    PARAMSPEC_DECLARATION = "paramspec_declaration"
    TYPEVAR_BOUND = "typevar_bound"
    TYPEVAR_CONSTRAINT = "typevar_constraint"
    PROTOCOL_BASE = "protocol_base"
    METHOD_BODY = "method_body"


class ImportLanding(StrEnum):
    """Final landing location for a generated import.

    Attributes:
        TOP_LEVEL: Top level associated with this instance.
        TYPE_CHECKING_BLOCK: Type checking block associated with this instance.

    """

    TOP_LEVEL = "top_level"
    TYPE_CHECKING_BLOCK = "type_checking_block"


class ImportGroup(StrEnum):
    """PEP 8 import group.

    Attributes:
        FUTURE: Future associated with this instance.
        LOCAL: Local associated with this instance.
        STDLIB: Stdlib associated with this instance.
        THIRD_PARTY: Third party associated with this instance.

    """

    FUTURE = "future"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    LOCAL = "local"


@dataclass(slots=True, frozen=True)
class ImportUseSite:
    """One semantic use site of an imported symbol.

    Attributes:
        owner: Owner retained as str | None by this instance.
        place: Place retained as ImportUsePlace by this instance.
        reason: Explanation associated with this result.

    """

    place: ImportUsePlace
    owner: str | None = None
    reason: str | None = None

    @classmethod
    def runtime(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a runtime use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.RUNTIME, owner=owner)

    @classmethod
    def annotation(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create an annotation use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.ANNOTATION, owner=owner)

    @classmethod
    def string_type_hint(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a string-type-hint use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.STRING_TYPE_HINT, owner=owner)

    @classmethod
    def typevar_declaration(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-constructor use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.TYPEVAR_DECLARATION, owner=owner)

    @classmethod
    def paramspec_declaration(
        cls,
        *,
        owner: str | None = None,
    ) -> ImportUseSite:
        """Create a ParamSpec-constructor use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.PARAMSPEC_DECLARATION, owner=owner)

    @classmethod
    def typevar_bound(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-bound use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.TYPEVAR_BOUND, owner=owner)

    @classmethod
    def typevar_constraint(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-constraint use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.TYPEVAR_CONSTRAINT, owner=owner)

    @classmethod
    def protocol_base(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a protocol-base use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.PROTOCOL_BASE, owner=owner)

    @classmethod
    def method_body(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a method-body use site.

        Args:
            owner: Owner supplied as str | None for this operation.

        Returns:
            ImportUseSite produced by this operation.

        """
        return cls(place=ImportUsePlace.METHOD_BODY, owner=owner)


@dataclass(slots=True, frozen=True)
class SemanticImportSource:
    """Semantic source location for importing one symbol.

    Attributes:
        asname: Asname retained as str | None by this instance.
        imported_name: Identifier used to refer to the imported.
        kind: Kind retained as ImportSourceKind by this instance.
        level: Level retained as int by this instance.
        module_parts: Module parts retained as tuple[str, ...] by this
            instance.

    """

    kind: ImportSourceKind
    module_parts: tuple[str, ...]
    imported_name: str
    level: int = 0
    asname: str | None = None

    @classmethod
    def absolute(
        cls,
        *,
        module_parts: tuple[str, ...],
        imported_name: str,
        asname: str | None = None,
    ) -> SemanticImportSource:
        """Create an absolute import source.

        Args:
            asname: Asname supplied as str | None for this operation.
            imported_name: Identifier of the imported being resolved.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.

        Returns:
            SemanticImportSource produced by this operation.

        """
        return cls(
            kind="absolute",
            module_parts=module_parts,
            imported_name=imported_name,
            asname=asname,
        )

    @classmethod
    def relative(
        cls,
        *,
        level: int,
        imported_name: str,
        module_parts: tuple[str, ...] = (),
        asname: str | None = None,
    ) -> SemanticImportSource:
        """Create a relative import source.

        Args:
            asname: Asname supplied as str | None for this operation.
            imported_name: Identifier of the imported being resolved.
            level: Level supplied as int for this operation.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.

        Returns:
            SemanticImportSource produced by this operation.

        """
        if level <= 0:
            msg: str = "Relative imports require level >= 1."
            fail(message=msg)
        return cls(
            kind="relative",
            module_parts=module_parts,
            imported_name=imported_name,
            level=level,
            asname=asname,
        )

    @property
    def module(self) -> str | None:
        """Return the ``ast.ImportFrom.module`` value.

        Returns:
            str | None produced by this operation.

        """
        if not self.module_parts:
            return None
        return ".".join(self.module_parts)

    def validate(self, *, validator: IdentifierValidator) -> None:
        """Validate all identifiers in this import source.

        Args:
            validator: Validator supplied as IdentifierValidator for this
                operation.

        """
        if self.kind == "absolute" and self.level != 0:
            msg: str = "Absolute imports must have level 0."
            fail(message=msg)
        if self.kind == "relative" and self.level <= 0:
            msg = "Relative imports require level >= 1."
            fail(message=msg)
        if self.kind == "absolute" and (not self.module_parts):
            msg = "Absolute imports require at least one module part."
            fail(message=msg)
        validator.validate_module_parts(parts=self.module_parts)
        validator.validate_identifier(
            name=self.imported_name,
            label="imported name",
        )
        if self.asname is not None:
            validator.validate_identifier(
                name=self.asname,
                label="import alias",
            )


@dataclass(slots=True, frozen=True)
class ImportRequirementKey:
    """Stable key for one importable symbol.

    Attributes:
        level: Level retained as int by this instance.
        module: Module retained as str | None by this instance.
        name: Identifier used to refer to the name.

    """

    module: str | None
    level: int
    name: str


@dataclass(slots=True)
class ImportRequirement:
    """One collected import requirement.

    Attributes:
        level: Level retained as int by this instance.
        local_name: Identifier used to refer to the local.
        module: Module retained as str | None by this instance.
        name: Identifier used to refer to the name.
        uses: Uses retained as list[ImportUseSite] by this instance.

    """

    module: str | None
    level: int
    name: str
    local_name: str
    uses: list[ImportUseSite] = field(default_factory=list)

    @property
    def asname(self) -> str | None:
        """Return import alias if needed.

        Returns:
            str | None produced by this operation.

        """
        if self.local_name == self.name:
            return None
        return self.local_name

    def add_use(self, *, use: ImportUseSite) -> None:
        """Record a semantic usage site.

        Args:
            use: Use supplied as ImportUseSite for this operation.

        """
        if use not in self.uses:
            self.uses.append(use)


@dataclass(slots=True, frozen=True)
class ImportAliasSpec:
    """One imported name inside an ``ImportFrom`` node.

    Attributes:
        asname: Asname retained as str | None by this instance.
        name: Identifier used to refer to the name.

    """

    name: str
    asname: str | None


@dataclass(slots=True, frozen=True)
class ImportFromGroup:
    """Grouped imports from a single module.

    Attributes:
        level: Level retained as int by this instance.
        module: Module retained as str | None by this instance.
        names: Names retained as tuple[ImportAliasSpec, ...] by this instance.

    """

    module: str | None
    level: int
    names: tuple[ImportAliasSpec, ...]


@dataclass(slots=True, frozen=True)
class GeneratedImportGroups:
    """Generated import nodes grouped by PEP 8 sections.

    Attributes:
        top_level_local: Top level local retained as tuple[stmt, ...] by this
            instance.
        top_level_stdlib: Top level stdlib retained as tuple[stmt, ...] by this
            instance.
        top_level_third_party: Top level third party retained as tuple[stmt,
            ...] by this instance.
        type_checking_block: Type checking block retained as If | None by this
            instance.
        type_checking_local: Type checking local retained as tuple[stmt, ...]
            by this instance.
        type_checking_stdlib: Type checking stdlib retained as tuple[stmt, ...]
            by this instance.
        type_checking_third_party: Type checking third party retained as
            tuple[stmt, ...] by this instance.

    """

    top_level_stdlib: tuple[stmt, ...]
    top_level_third_party: tuple[stmt, ...]
    top_level_local: tuple[stmt, ...]
    type_checking_stdlib: tuple[stmt, ...]
    type_checking_third_party: tuple[stmt, ...]
    type_checking_local: tuple[stmt, ...]
    type_checking_block: If | None

    @property
    def top_level_nodes(self) -> tuple[stmt, ...]:
        """Return top-level imports in PEP 8 order.

        Returns:
            tuple[stmt, ...] produced by this operation.

        """
        return (
            *self.top_level_stdlib,
            *self.top_level_third_party,
            *self.top_level_local,
        )

    @property
    def type_checking_nodes(self) -> tuple[stmt, ...]:
        """Return imports inside the ``TYPE_CHECKING`` block.

        Returns:
            tuple[stmt, ...] produced by this operation.

        """
        return (
            *self.type_checking_stdlib,
            *self.type_checking_third_party,
            *self.type_checking_local,
        )

    @property
    def all_import_nodes(self) -> tuple[stmt, ...]:
        """Return all generated import nodes.

        Returns:
            tuple[stmt, ...] produced by this operation.

        """
        if self.type_checking_block is None:
            return self.top_level_nodes
        return (*self.top_level_nodes, self.type_checking_block)


class ImportPlacementPolicy:
    """Decide final landing for usage-aware imports."""

    _RUNTIME_PLACES: Final[frozenset[ImportUsePlace]] = frozenset(
        {
            ImportUsePlace.RUNTIME,
            ImportUsePlace.TYPEVAR_DECLARATION,
            ImportUsePlace.PARAMSPEC_DECLARATION,
            ImportUsePlace.TYPEVAR_BOUND,
            ImportUsePlace.TYPEVAR_CONSTRAINT,
            ImportUsePlace.PROTOCOL_BASE,
            ImportUsePlace.METHOD_BODY,
        },
    )
    _TYPE_CHECKING_ONLY_PLACES: Final[frozenset[ImportUsePlace]] = frozenset(
        {ImportUsePlace.STRING_TYPE_HINT},
    )

    def __init__(self, *, postponed_annotations: bool) -> None:
        """Initialize the import placement policy.

        Args:
            postponed_annotations: Postponed annotations supplied as bool for
                this operation.

        """
        self._postponed_annotations: bool = postponed_annotations

    def landing_for(self, *, requirement: ImportRequirement) -> ImportLanding:
        """Return final landing for an import requirement.

        Args:
            requirement: Requirement supplied as ImportRequirement for this
                operation.

        Returns:
            ImportLanding produced by this operation.

        """
        places: set[ImportUsePlace] = {use.place for use in requirement.uses}
        if places & self._RUNTIME_PLACES:
            return ImportLanding.TOP_LEVEL
        if places <= self._TYPE_CHECKING_ONLY_PLACES:
            return ImportLanding.TYPE_CHECKING_BLOCK
        if (
            places == {ImportUsePlace.ANNOTATION}
            and self._postponed_annotations
        ):
            return ImportLanding.TYPE_CHECKING_BLOCK
        return ImportLanding.TOP_LEVEL


class Pep8ImportGrouper:
    """Group generated ``ImportFrom`` nodes by PEP 8 sections."""

    def __init__(self, *, local_roots: Iterable[str]) -> None:
        """Initialize the grouper.

        Args:
            local_roots: Local roots supplied as Iterable[str] for this
                operation.

        """
        self._local_roots: frozenset[str] = frozenset(local_roots)

    def group_for(self, *, module: str | None, level: int) -> ImportGroup:
        """Return the PEP 8 group for one import source.

        Args:
            level: Level supplied as int for this operation.
            module: The module examined while return the PEP 8 group for one
                import source.

        Returns:
            ImportGroup produced by this operation.

        """
        if module == "__future__":
            return ImportGroup.FUTURE
        if level > 0:
            return ImportGroup.LOCAL
        if module is None:
            return ImportGroup.LOCAL
        root: str = module.split(sep=".", maxsplit=1)[0]
        if root in self._local_roots:
            return ImportGroup.LOCAL
        if root in stdlib_module_names:
            return ImportGroup.STDLIB
        return ImportGroup.THIRD_PARTY

    def build_import_from_nodes(
        self,
        *,
        groups: tuple[ImportFromGroup, ...],
    ) -> dict[ImportGroup, tuple[stmt, ...]]:
        """Build import nodes for each PEP 8 group.

        Args:
            groups: Groups supplied as tuple[ImportFromGroup, ...] for this
                operation.

        Returns:
            dict[ImportGroup, tuple[stmt, ...]] produced by this operation.

        """
        grouped: dict[ImportGroup, list[stmt]] = {
            ImportGroup.FUTURE: [],
            ImportGroup.STDLIB: [],
            ImportGroup.THIRD_PARTY: [],
            ImportGroup.LOCAL: [],
        }
        for group in sorted(groups, key=self._group_sort_key):
            import_group: ImportGroup = self.group_for(
                module=group.module,
                level=group.level,
            )
            grouped[import_group].append(
                ImportFrom(
                    module=group.module,
                    names=[
                        alias(name=item.name, asname=item.asname)
                        for item in group.names
                    ],
                    level=group.level,
                ),
            )
        return {key: tuple(value) for key, value in grouped.items()}

    @staticmethod
    def _group_sort_key(group: ImportFromGroup) -> tuple[int, str]:
        """Return a stable sort key for import groups.

        Args:
            group: Group supplied as ImportFromGroup for this operation.

        Returns:
            tuple[int, str] produced by this operation.

        """
        return (group.level, group.module or "")


class UsageAwareImportCollector:
    """Collect imports with usage-aware placement and PEP 8 grouping."""

    def __init__(
        self,
        *,
        symbol_index: ScriptSymbolIndex,
        existing_import_nodes: Iterable[Import | ImportFrom],
        postponed_annotations: bool | None,
        local_roots: Iterable[str],
    ) -> None:
        """Initialize the collector.

        Args:
            existing_import_nodes: Existing import nodes supplied as
                Iterable[Import | ImportFrom] for this operation.
            local_roots: Local roots supplied as Iterable[str] for this
                operation.
            postponed_annotations: Postponed annotations supplied as bool |
                None for this operation.
            symbol_index: Symbol index supplied as ScriptSymbolIndex for this
                operation.

        """
        self._symbols: ScriptSymbolIndex = symbol_index
        self._validator: IdentifierValidator = IdentifierValidator()
        self._requirements: dict[ImportRequirementKey, ImportRequirement] = {}
        self._generated_local_names: set[str] = set()
        self._reserved_generated_names: set[str] = set()
        detected_postponed: bool = self._detect_postponed_annotations(
            import_nodes=existing_import_nodes,
        )
        final_postponed: bool = (
            detected_postponed
            if postponed_annotations is None
            else postponed_annotations
        )
        self._policy: ImportPlacementPolicy = ImportPlacementPolicy(
            postponed_annotations=final_postponed,
        )
        self._grouper: Pep8ImportGrouper = Pep8ImportGrouper(
            local_roots=local_roots,
        )
        self._type_checking_name: str | None = None

    def reserve_generated_name(self, *, name: str) -> None:
        """Reserve a generated declaration name.

        Args:
            name: Identifier of the name being resolved.

        """
        self._reserved_generated_names.add(name)

    def require_from_source(
        self,
        *,
        source: SemanticImportSource,
        use: ImportUseSite,
    ) -> Name:
        """Require a semantic import source and return its local name node.

        Args:
            source: The source examined while require a semantic import source
                and return its local name node.
            use: Use supplied as ImportUseSite for this operation.

        Returns:
            Name produced by this operation.

        """
        source.validate(validator=self._validator)
        existing_name: str | None = self._symbols.find_imported_from(
            module=source.module,
            level=source.level,
            name=source.imported_name,
        )
        if existing_name is not None:
            return Name(id=existing_name, ctx=Load())
        if self._symbols.has_wildcard_from(
            module=source.module,
            level=source.level,
        ):
            return Name(id=source.imported_name, ctx=Load())
        if source.imported_name in self._symbols.local_class_names:
            return Name(id=source.imported_name, ctx=Load())
        if source.imported_name in self._reserved_generated_names:
            return Name(id=source.imported_name, ctx=Load())
        requirement: ImportRequirement = self._requirement_from_source(
            source=source,
        )
        requirement.add_use(use=use)
        return Name(id=requirement.local_name, ctx=Load())

    def require_absolute(
        self,
        *,
        module_parts: tuple[str, ...],
        name: str,
        use: ImportUseSite,
    ) -> Name:
        """Require an absolute ``from ... import ...`` source.

        Args:
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.
            use: Use supplied as ImportUseSite for this operation.

        Returns:
            Name produced by this operation.

        """
        return self.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=module_parts,
                imported_name=name,
            ),
            use=use,
        )

    def build_import_nodes(self) -> GeneratedImportGroups:
        """Build generated imports grouped by PEP 8 sections.

        Returns:
            GeneratedImportGroups produced by this operation.

        """
        top_level_groups: tuple[ImportFromGroup, ...]
        type_checking_groups: tuple[ImportFromGroup, ...]
        top_level_groups, type_checking_groups = self._split_groups()
        if type_checking_groups:
            self._type_checking_name = self._ensure_type_checking_name()
            top_level_groups, type_checking_groups = self._split_groups()
        top_level_by_group: dict[ImportGroup, tuple[stmt, ...]] = (
            self._grouper.build_import_from_nodes(groups=top_level_groups)
        )
        type_checking_by_group: dict[ImportGroup, tuple[stmt, ...]] = (
            self._grouper.build_import_from_nodes(groups=type_checking_groups)
        )
        type_checking_nodes: tuple[stmt, ...] = (
            *type_checking_by_group[ImportGroup.STDLIB],
            *type_checking_by_group[ImportGroup.THIRD_PARTY],
            *type_checking_by_group[ImportGroup.LOCAL],
        )
        type_checking_block: If | None = self._build_type_checking_block(
            nodes=type_checking_nodes,
        )
        return GeneratedImportGroups(
            top_level_stdlib=top_level_by_group[ImportGroup.STDLIB],
            top_level_third_party=top_level_by_group[ImportGroup.THIRD_PARTY],
            top_level_local=top_level_by_group[ImportGroup.LOCAL],
            type_checking_stdlib=type_checking_by_group[ImportGroup.STDLIB],
            type_checking_third_party=type_checking_by_group[
                ImportGroup.THIRD_PARTY
            ],
            type_checking_local=type_checking_by_group[ImportGroup.LOCAL],
            type_checking_block=type_checking_block,
        )

    def import_nodes(self) -> tuple[stmt, ...]:
        """Return all generated import nodes.

        Returns:
            tuple[stmt, ...] produced by this operation.

        """
        return self.build_import_nodes().all_import_nodes

    @staticmethod
    def _alias_for(*, module: str | None, name: str) -> str:
        """Create a deterministic alias for a colliding import.

        Args:
            module: The module examined while create a deterministic alias for
                a colliding import.
            name: Identifier of the name being resolved.

        Returns:
            str produced by this operation.

        """
        raw_alias: str = f"{module or 'relative'}_{name}"
        return sub(pattern="\\W+", repl="_", string=raw_alias).strip("_")

    @staticmethod
    def _dict_to_groups(
        *,
        items: dict[tuple[str | None, int], list[ImportAliasSpec]],
    ) -> tuple[ImportFromGroup, ...]:
        """Convert grouped aliases into sorted import groups.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            tuple[ImportFromGroup, ...] produced by this operation.

        """
        groups: list[ImportFromGroup] = []
        for (module, level), aliases in sorted(
            items.items(),
            key=lambda item: (item[0][1], item[0][0] or ""),
        ):
            unique_aliases: dict[tuple[str, str | None], ImportAliasSpec] = {
                (item.name, item.asname): item for item in aliases
            }
            groups.append(
                ImportFromGroup(
                    module=module,
                    level=level,
                    names=tuple(
                        sorted(
                            unique_aliases.values(),
                            key=lambda item: (item.name, item.asname or ""),
                        ),
                    ),
                ),
            )
        return tuple(groups)

    @staticmethod
    def _detect_postponed_annotations(
        *,
        import_nodes: Iterable[Import | ImportFrom],
    ) -> bool:
        """Detect ``from __future__ import annotations``.

        Args:
            import_nodes: Import nodes supplied as Iterable[Import |
                ImportFrom] for this operation.

        Returns:
            Whether the requested condition holds.

        """
        for node in import_nodes:
            if not isinstance(node, ImportFrom):
                continue
            if node.module != "__future__":
                continue
            if any(item.name == "annotations" for item in node.names):
                return True
        return False

    def _build_type_checking_block(
        self,
        *,
        nodes: tuple[stmt, ...],
    ) -> If | None:
        """Build the optional ``if TYPE_CHECKING`` block.

        Args:
            nodes: Collection of nodes supplied for this operation.

        Returns:
            If | None produced by this operation.

        """
        if not nodes or self._type_checking_name is None:
            return None
        return If(
            test=Name(id=self._type_checking_name, ctx=Load()),
            body=list(nodes),
            orelse=[],
        )

    def _ensure_type_checking_name(self) -> str:
        """Ensure the ``TYPE_CHECKING`` guard name exists.

        Returns:
            str produced by this operation.

        """
        existing_name: str | None = self._symbols.find_imported_from(
            module="typing",
            level=0,
            name="TYPE_CHECKING",
        )
        if existing_name is not None:
            return existing_name
        requirement: ImportRequirement = self._requirement_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="TYPE_CHECKING",
            ),
        )
        requirement.add_use(use=ImportUseSite.runtime(owner="TYPE_CHECKING"))
        return requirement.local_name

    def _requirement_from_source(
        self,
        *,
        source: SemanticImportSource,
    ) -> ImportRequirement:
        """Return or create a requirement from a semantic source.

        Args:
            source: The source examined while return or create a requirement
                from a semantic source.

        Returns:
            ImportRequirement produced by this operation.

        """
        key: ImportRequirementKey = ImportRequirementKey(
            module=source.module,
            level=source.level,
            name=source.imported_name,
        )
        existing: ImportRequirement | None = self._requirements.get(key)
        if existing is not None:
            return existing
        local_name: str = self._select_local_name(source=source)
        requirement: ImportRequirement = ImportRequirement(
            module=source.module,
            level=source.level,
            name=source.imported_name,
            local_name=local_name,
        )
        self._requirements[key] = requirement
        self._generated_local_names.add(local_name)
        return requirement

    def _select_local_name(self, *, source: SemanticImportSource) -> str:
        """Select the local imported name for a source.

        Args:
            source: The source examined while select the local imported name
                for a source.

        Returns:
            Rendered source text produced by this operation.

        """
        if source.asname is not None:
            return source.asname
        if self._can_use_simple_name(name=source.imported_name):
            return source.imported_name
        return self._free_generated_name(
            preferred=self._alias_for(
                module=source.module,
                name=source.imported_name,
            ),
        )

    def _can_use_simple_name(self, *, name: str) -> bool:
        """Return whether an imported name is available without aliasing.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Whether the requested condition holds.

        """
        return (
            not self._symbols.is_name_available(name=name)
            and name not in self._reserved_generated_names
            and (name not in self._generated_local_names)
        )

    def _free_generated_name(self, *, preferred: str) -> str:
        """Return a collision-free generated name.

        Args:
            preferred: Preferred supplied as str for this operation.

        Returns:
            str produced by this operation.

        """
        if self._is_free_generated_name(name=preferred):
            return preferred
        index: int = 1
        while True:
            candidate: str = f"{preferred}_{index}"
            if self._is_free_generated_name(name=candidate):
                return candidate
            index += 1

    def _is_free_generated_name(self, *, name: str) -> bool:
        """Return whether a generated name is free.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Whether the requested condition holds.

        """
        return (
            not self._symbols.is_name_available(name=name)
            and name not in self._reserved_generated_names
            and (name not in self._generated_local_names)
        )

    def _split_groups(
        self,
    ) -> tuple[tuple[ImportFromGroup, ...], tuple[ImportFromGroup, ...]]:
        """Split requirements into top-level and TYPE_CHECKING groups.

        Returns:
            tuple[tuple[ImportFromGroup, ...], tuple[ImportFromGroup, ...]]
            produced by this operation.

        """
        top_level: dict[tuple[str | None, int], list[ImportAliasSpec]] = {}
        type_checking: dict[tuple[str | None, int], list[ImportAliasSpec]] = {}
        for requirement in self._requirements.values():
            landing: ImportLanding = self._policy.landing_for(
                requirement=requirement,
            )
            target: dict[tuple[str | None, int], list[ImportAliasSpec]] = (
                top_level
                if landing is ImportLanding.TOP_LEVEL
                else type_checking
            )
            target.setdefault(
                (requirement.module, requirement.level),
                [],
            ).append(
                ImportAliasSpec(
                    name=requirement.name,
                    asname=requirement.asname,
                ),
            )
        return (
            self._dict_to_groups(items=top_level),
            self._dict_to_groups(items=type_checking),
        )


class TypeExpression(ABC):
    """Base class for semantic type expressions."""

    @abstractmethod
    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Convert this type expression to an AST node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """

    @abstractmethod
    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type expression as a type-hint string.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """

    @abstractmethod
    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """

    def __or__(self, other: TypeExpression) -> UnionTypeRef:
        """Create a normalized semantic union with another type."""
        return UnionTypeRef(options=(self, other))


@dataclass(slots=True, frozen=True)
class BuiltinTypeRef(TypeExpression):
    """Reference a built-in type by name.

    Attributes:
        name: Identifier used to refer to the name.

    """

    name: str

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a simple name node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        if self.name != "None":
            resolver.validate_identifier(name=self.name, label="built-in type")
        return Name(id=self.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type reference.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        if self.name != "None":
            renderer.validate_identifier(name=self.name, label="built-in type")
        return self.name

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"builtins:{self.name}"


@dataclass(slots=True, frozen=True)
class LocalTypeRef(TypeExpression):
    """Reference a type already available in the local module.

    Attributes:
        name: Identifier used to refer to the name.

    """

    name: str

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a local name node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        resolver.validate_identifier(name=self.name, label="local type")
        return Name(id=self.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type reference.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        renderer.validate_identifier(name=self.name, label="local type")
        return self.name

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"local:{self.name}"


@dataclass(slots=True, frozen=True)
class ImportedTypeRef(TypeExpression):
    """Reference a type that should be imported from a semantic source.

    Attributes:
        source: Original source text retained for parsing and reconstruction.

    """

    source: SemanticImportSource

    @classmethod
    def absolute(
        cls,
        *,
        module_parts: tuple[str, ...],
        name: str,
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create an absolute imported type reference.

        Args:
            asname: Asname supplied as str | None for this operation.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.

        Returns:
            ImportedTypeRef produced by this operation.

        """
        return cls(
            source=SemanticImportSource.absolute(
                module_parts=module_parts,
                imported_name=name,
                asname=asname,
            ),
        )

    @classmethod
    def relative(
        cls,
        *,
        level: int,
        name: str,
        module_parts: tuple[str, ...] = (),
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create a relative imported type reference.

        Args:
            asname: Asname supplied as str | None for this operation.
            level: Level supplied as int for this operation.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.

        Returns:
            ImportedTypeRef produced by this operation.

        """
        return cls(
            source=SemanticImportSource.relative(
                level=level,
                module_parts=module_parts,
                imported_name=name,
                asname=asname,
            ),
        )

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a name node and register the import source.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        return resolver.imports.require_from_source(
            source=self.source,
            use=_use,
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this imported type and register string-hint imports.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        return renderer.render_imported(source=self.source)

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return (
            f"imported:"
            f"{self.source.module}"
            f":"
            f"{self.source.level}"
            f":"
            f"{self.source.imported_name}"
            f":"
            f"{self.source.asname or ''}"
        )


@dataclass(slots=True, frozen=True)
class TypeVarRef(TypeExpression):
    """Reference a generated TypeVar.

    Attributes:
        spec: Spec retained as TypeVarSpec by this instance.

    """

    spec: TypeVarSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the TypeVar name.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        resolver.validate_identifier(name=self.spec.name, label="TypeVar")
        return Name(id=self.spec.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the TypeVar name.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        renderer.validate_identifier(name=self.spec.name, label="TypeVar")
        return self.spec.name

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"typevar:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecRef(TypeExpression):
    """Reference a generated ParamSpec.

    Attributes:
        spec: Spec retained as ParamSpecSpec by this instance.

    """

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the ParamSpec name.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Name(id=self.spec.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the ParamSpec name.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return self.spec.name

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"paramspec:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecArgsRef(TypeExpression):
    """Reference ``P.args``.

    Attributes:
        spec: Spec retained as ParamSpecSpec by this instance.

    """

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``P.args``.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Attribute(
            value=Name(id=self.spec.name, ctx=Load()),
            attr="args",
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``P.args``.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return f"{self.spec.name}.args"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"paramspec-args:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecKwargsRef(TypeExpression):
    """Reference ``P.kwargs``.

    Attributes:
        spec: Spec retained as ParamSpecSpec by this instance.

    """

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``P.kwargs``.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Attribute(
            value=Name(id=self.spec.name, ctx=Load()),
            attr="kwargs",
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``P.kwargs``.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return f"{self.spec.name}.kwargs"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"paramspec-kwargs:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class SelfTypeRef(TypeExpression):
    """Reference ``typing.Self``."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a ``Self`` name and register its import.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        return resolver.imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Self",
            ),
            use=_use,
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``Self`` and register its string-hint import.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        return renderer.render_imported(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Self",
            ),
        )

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return "typing:Self"


@dataclass(slots=True, frozen=True)
class GenericTypeRef(TypeExpression):
    """Reference a generic type expression.

    Attributes:
        arguments: Arguments retained as tuple[TypeExpression, ...] by this
            instance.
        origin: Origin retained as TypeExpression by this instance.

    """

    origin: TypeExpression
    arguments: tuple[TypeExpression, ...]

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a subscripted type node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        value_node: expr = self.origin.to_ast(resolver=resolver, _use=_use)
        argument_nodes: tuple[expr, ...] = tuple(
            argument.to_ast(resolver=resolver, _use=_use)
            for argument in self.arguments
        )
        return AstExpressionBuilder.subscript(
            value=value_node,
            args=argument_nodes,
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a generic type expression.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        origin_text: str = self.origin.render(renderer=renderer)
        argument_text: str = ", ".join(
            argument.render(renderer=renderer) for argument in self.arguments
        )
        return f"{origin_text}[{argument_text}]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        argument_key: str = ",".join(
            argument.key() for argument in self.arguments
        )
        return f"generic:{self.origin.key()}[{argument_key}]"


@dataclass(slots=True, frozen=True)
class UnionTypeRef(TypeExpression):
    """Reference a normalized union type expression.

    Attributes:
        collapse_limit: Collapse limit retained as int | None by this instance.
        options: Options retained as tuple[TypeExpression, ...] by this
            instance.

    """

    options: tuple[TypeExpression, ...]
    collapse_limit: int | None = None

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a PEP 604 union AST expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        option_nodes: tuple[expr, ...] = tuple(
            option.to_ast(resolver=resolver, _use=_use)
            for option in self.options
        )
        return AstExpressionBuilder.union(options=option_nodes)

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a normalized PEP 604 union string.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        return " | ".join(
            option.render(renderer=renderer) for option in self.options
        )

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return "union:" + "|".join(option.key() for option in self.options)

    def __post_init__(self) -> None:
        """Normalize union options after initialization."""
        normalized_options: tuple[TypeExpression, ...] = (
            TypeUnionSimplifier().simplify(
                options=self.options,
                collapse_limit=self.collapse_limit,
            )
        )
        object.__setattr__(self, "options", normalized_options)


@dataclass(slots=True, frozen=True)
class EmptyGenericTypeRef(TypeExpression):
    """Semantic representation of an intentionally empty generic subscript.

    Attributes:
        origin: Origin retained as TypeExpression by this instance.

    """

    origin: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a best-effort AST node for an empty generic expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        return self.origin.to_ast(resolver=resolver, _use=_use)

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render as ``Origin[]``.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        origin_text: str = self.origin.render(renderer=renderer)
        return f"{origin_text}[]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return f"empty-generic:{self.origin.key()}"


@dataclass(slots=True, frozen=True)
class EllipsisTypeRef(TypeExpression):
    """Semantic ellipsis used inside constrained type templates."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return an ellipsis constant.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        _ = resolver
        return Constant(value=Ellipsis)

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render as ``...``.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        _ = renderer
        return "..."

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return "ellipsis"


@dataclass(slots=True, frozen=True)
class TypeTemplateRef:
    """Constrained generic type template with semantic arity validation.

    Attributes:
        allow_empty: Allow empty retained as bool by this instance.
        label: Label retained as str by this instance.
        max_args: Max args retained as int | None by this instance.
        min_args: Min args retained as int by this instance.
        origin: Origin retained as TypeExpression by this instance.

    """

    origin: TypeExpression
    label: str
    min_args: int
    max_args: int | None
    allow_empty: bool = False

    def of(self, *, arguments: tuple[TypeExpression, ...]) -> TypeExpression:
        """Create a generic type expression after arity validation.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        argument_count: int = len(arguments)
        if argument_count == 0 and self.allow_empty:
            return EmptyGenericTypeRef(origin=self.origin)
        if argument_count < self.min_args:
            msg: str = (
                f"{self.label}"
                f" expects at least "
                f"{self.min_args}"
                f" type arguments; received "
                f"{argument_count}"
                f"."
            )
            fail(message=msg)
        if self.max_args is not None and argument_count > self.max_args:
            msg = (
                f"{self.label}"
                f" expects at most "
                f"{self.max_args}"
                f" type arguments; received "
                f"{argument_count}"
                f"."
            )
            fail(message=msg)
        return GenericTypeRef(origin=self.origin, arguments=arguments)

    def empty(self) -> EmptyGenericTypeRef:
        """Create an intentionally empty generic expression.

        Returns:
            EmptyGenericTypeRef produced by this operation.

        """
        if not self.allow_empty:
            msg: str = (
                f"{self.label} does not allow an empty type argument list."
            )
            fail(message=msg)
        return EmptyGenericTypeRef(origin=self.origin)


@dataclass(slots=True, frozen=True)
class _GenericParts:
    """Decomposed generic type information for union simplification.

    Attributes:
        arguments: Arguments retained as tuple[TypeExpression, ...] by this
            instance.
        family: Family retained as str by this instance.
        origin_name: Identifier used to refer to the origin.

    """

    family: str
    arguments: tuple[TypeExpression, ...]
    origin_name: str


class TypeUnionSimplifier:
    """Normalize, sort, deduplicate, and generalize union members."""

    _NUMERIC_RANKS: Final[dict[str, int]] = {
        "bool": 0,
        "int": 1,
        "float": 2,
        "complex": 3,
    }
    _MAPPING_ORIGINS: Final[frozenset[str]] = frozenset(
        {
            "dict",
            "Mapping",
            "MutableMapping",
            "defaultdict",
            "ChainMap",
            "Counter",
            "OrderedDict",
            "UserDict",
        },
    )
    _MUTABLE_MAPPING_ORIGINS: Final[frozenset[str]] = frozenset(
        {
            "dict",
            "MutableMapping",
            "defaultdict",
            "Counter",
            "OrderedDict",
            "UserDict",
        },
    )
    _ITERABLE_ORIGINS: Final[frozenset[str]] = frozenset(
        {
            "list",
            "tuple",
            "set",
            "frozenset",
            "deque",
            "UserList",
            "Iterable",
            "Iterator",
            "Reversible",
            "Collection",
            "Sequence",
            "MutableSequence",
            "Set",
            "MutableSet",
        },
    )
    _SEQUENCE_ORIGINS: Final[frozenset[str]] = frozenset(
        {"list", "tuple", "deque", "UserList", "Sequence", "MutableSequence"},
    )
    _MUTABLE_SEQUENCE_ORIGINS: Final[frozenset[str]] = frozenset(
        {"list", "deque", "UserList", "MutableSequence"},
    )
    _SET_ORIGINS: Final[frozenset[str]] = frozenset(
        {"set", "frozenset", "Set", "MutableSet"},
    )
    _MUTABLE_SET_ORIGINS: Final[frozenset[str]] = frozenset(
        {"set", "MutableSet"},
    )

    def simplify(
        self,
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None,
    ) -> tuple[TypeExpression, ...]:
        """Return canonical union options.

        Args:
            collapse_limit: Collapse limit supplied as int | None for this
                operation.
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        flattened_options: tuple[TypeExpression, ...] = self._flatten(
            options=options,
        )
        non_never_options: tuple[TypeExpression, ...] = tuple(
            option
            for option in flattened_options
            if not self._is_imported_name(option=option, name="Never")
        )
        if not non_never_options:
            return (
                ImportedTypeRef.absolute(
                    module_parts=("typing",),
                    name="Never",
                ),
            )
        deduplicated_options: tuple[TypeExpression, ...] = self._deduplicate(
            options=non_never_options,
        )
        if self._has_builtin(options=deduplicated_options, name="object"):
            return (BuiltinTypeRef(name="object"),)
        literal_collapsed_options: tuple[TypeExpression, ...] = (
            self._collapse_literals(options=deduplicated_options)
        )
        numeric_collapsed_options: tuple[TypeExpression, ...] = (
            self._collapse_numeric(options=literal_collapsed_options)
        )
        generic_collapsed_options: tuple[TypeExpression, ...] = (
            self._generalize_generics(options=numeric_collapsed_options)
        )
        sorted_options: tuple[TypeExpression, ...] = self._sort_options(
            options=generic_collapsed_options,
        )
        if collapse_limit is not None and len(sorted_options) > collapse_limit:
            return (BuiltinTypeRef(name="object"),)
        return sorted_options

    @staticmethod
    def _flatten(
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Flatten nested unions.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        flattened_options: list[TypeExpression] = []
        for option in options:
            if isinstance(option, UnionTypeRef):
                flattened_options.extend(option.options)
            else:
                flattened_options.append(option)
        return tuple(flattened_options)

    @staticmethod
    def _deduplicate(
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Remove duplicate semantic options preserving first occurrence.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        seen_keys: set[str] = set()
        deduplicated_options: list[TypeExpression] = []
        for option in options:
            option_key: str = option.key()
            if option_key in seen_keys:
                continue
            seen_keys.add(option_key)
            deduplicated_options.append(option)
        return tuple(deduplicated_options)

    @staticmethod
    def _literal_is_covered(
        *,
        literal: LiteralTypeRef,
        builtin_names: set[str],
    ) -> bool:
        """Return whether all literal values are covered by builtin options.

        Args:
            builtin_names: Builtin names supplied as set[str] for this
                operation.
            literal: Literal supplied as LiteralTypeRef for this operation.

        Returns:
            Whether the requested condition holds.

        """
        for value in literal.values:
            if isinstance(value, bool):
                value_type_name: str = "bool"
            elif isinstance(value, int):
                value_type_name = "int"
            elif isinstance(value, float):
                value_type_name = "float"
            elif isinstance(value, str):
                value_type_name = "str"
            elif value is None:
                value_type_name = "None"
            else:
                return False
            if value_type_name not in builtin_names:
                return False
        return True

    @staticmethod
    def _origin_name_from_parts(*, parts_item: _GenericParts) -> str:
        """Return a stable origin name from generic parts metadata.

        Args:
            parts_item: Parts item supplied as _GenericParts for this
                operation.

        Returns:
            str produced by this operation.

        """
        return parts_item.origin_name

    @staticmethod
    def _origin_name(*, option: TypeExpression) -> str | None:
        """Return a generic origin name when it is easily known.

        Args:
            option: Option supplied as TypeExpression for this operation.

        Returns:
            str | None produced by this operation.

        """
        if isinstance(option, BuiltinTypeRef):
            return option.name
        if isinstance(option, ImportedTypeRef):
            return option.source.imported_name
        return None

    @staticmethod
    def _builtin_name(*, option: TypeExpression) -> str | None:
        """Return builtin name when the option is a builtin ref.

        Args:
            option: Option supplied as TypeExpression for this operation.

        Returns:
            str | None produced by this operation.

        """
        if isinstance(option, BuiltinTypeRef):
            return option.name
        return None

    @staticmethod
    def _is_imported_name(*, option: TypeExpression, name: str) -> bool:
        """Return whether an option is an imported ref with this name.

        Args:
            name: Identifier of the name being resolved.
            option: Option supplied as TypeExpression for this operation.

        Returns:
            Whether the requested condition holds.

        """
        return (
            isinstance(option, ImportedTypeRef)
            and option.source.imported_name == name
        )

    def _collapse_literals(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse literals covered by concrete builtin primitive types.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        literal_options: list[LiteralTypeRef] = []
        other_options: list[TypeExpression] = []
        builtin_names: set[str] = set()
        for option in options:
            if isinstance(option, LiteralTypeRef):
                literal_options.append(option)
                continue
            builtin_name: str | None = self._builtin_name(option=option)
            if builtin_name is not None:
                builtin_names.add(builtin_name)
            other_options.append(option)
        kept_literals: list[TypeExpression] = []
        for literal in literal_options:
            if self._literal_is_covered(
                literal=literal,
                builtin_names=builtin_names,
            ):
                continue
            kept_literals.append(literal)
        return (*other_options, *kept_literals)

    def _collapse_numeric(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse compatible numeric unions such as ``int | float``.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        highest_rank: int = -1
        other_options: list[TypeExpression] = []
        for option in options:
            builtin_name: str | None = self._builtin_name(option=option)
            numeric_rank: int | None = (
                self._NUMERIC_RANKS.get(builtin_name)
                if builtin_name is not None
                else None
            )
            if numeric_rank is None:
                other_options.append(option)
                continue
            highest_rank = max(highest_rank, numeric_rank)
        if highest_rank < 0:
            return options
        collapsed_numeric_name: str = self._numeric_name_for_rank(
            rank=highest_rank,
        )
        collapsed_options: list[TypeExpression] = [
            option
            for option in other_options
            if not self._is_builtin_name(
                option=option,
                name=collapsed_numeric_name,
            )
        ]
        collapsed_options.append(BuiltinTypeRef(name=collapsed_numeric_name))
        return tuple(collapsed_options)

    def _numeric_name_for_rank(self, *, rank: int) -> str:
        """Return builtin numeric type name for a rank.

        Args:
            rank: Rank supplied as int for this operation.

        Returns:
            str produced by this operation.

        """
        for name, candidate_rank in self._NUMERIC_RANKS.items():
            if candidate_rank == rank:
                return name
        fail(message="Invalid numeric rank.")

    def _generalize_generics(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse compatible container unions to ABC supertypes.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        generic_parts: list[_GenericParts] = []
        other_options: list[TypeExpression] = []
        for option in options:
            parts: _GenericParts | None = self._generic_parts(option=option)
            if parts is None:
                other_options.append(option)
            else:
                generic_parts.append(parts)
        if not generic_parts or other_options:
            return options
        if all(item.family == "mapping" for item in generic_parts):
            return (self._mapping_union(parts=tuple(generic_parts)),)
        if all(item.family == "iterable" for item in generic_parts):
            return (self._iterable_union(parts=tuple(generic_parts)),)
        return options

    def _generic_parts(
        self,
        *,
        option: TypeExpression,
    ) -> _GenericParts | None:
        """Return generic family details if an option is generalizable.

        Args:
            option: Option supplied as TypeExpression for this operation.

        Returns:
            _GenericParts | None produced by this operation.

        """
        if isinstance(option, EmptyGenericTypeRef):
            return None
        if not isinstance(option, GenericTypeRef):
            return None
        origin_name: str | None = self._origin_name(option=option.origin)
        if origin_name is None:
            return None
        if (
            origin_name in self._MAPPING_ORIGINS
            and len(option.arguments) == Constants.two_item_count
        ):
            return _GenericParts(
                family="mapping",
                arguments=option.arguments,
                origin_name=origin_name,
            )
        if origin_name in self._ITERABLE_ORIGINS and option.arguments:
            return _GenericParts(
                family="iterable",
                arguments=(self._iterable_argument(option=option),),
                origin_name=origin_name,
            )
        return None

    def _iterable_argument(self, *, option: GenericTypeRef) -> TypeExpression:
        """Return the element argument for iterable-like generics.

        Args:
            option: Option supplied as GenericTypeRef for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        origin_name: str | None = self._origin_name(option=option.origin)
        if origin_name == "tuple" and option.arguments:
            return option.arguments[0]
        return option.arguments[0]

    def _mapping_union(
        self,
        *,
        parts: tuple[_GenericParts, ...],
    ) -> TypeExpression:
        """Return a mapping ABC target for compatible mapping unions.

        Args:
            parts: Parts supplied as tuple[_GenericParts, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        key_options: tuple[TypeExpression, ...] = tuple(
            item.arguments[0] for item in parts
        )
        value_options: tuple[TypeExpression, ...] = tuple(
            item.arguments[1] for item in parts
        )
        key_type: TypeExpression = self._collapse_argument_union(
            options=key_options,
        )
        value_type: TypeExpression = self._collapse_argument_union(
            options=value_options,
        )
        target_name: str = self._mapping_target_name(parts=parts)
        return GenericTypeRef(
            origin=ImportedTypeRef.absolute(
                module_parts=("collections", "abc"),
                name=target_name,
            ),
            arguments=(key_type, value_type),
        )

    def _mapping_target_name(self, *, parts: tuple[_GenericParts, ...]) -> str:
        """Return ``Mapping`` or ``MutableMapping`` for mapping parts.

        Args:
            parts: Parts supplied as tuple[_GenericParts, ...] for this
                operation.

        Returns:
            str produced by this operation.

        """
        origin_names: set[str] = {
            self._origin_name_from_parts(parts_item=part) for part in parts
        }
        if origin_names <= self._MUTABLE_MAPPING_ORIGINS:
            return "MutableMapping"
        return "Mapping"

    def _iterable_union(
        self,
        *,
        parts: tuple[_GenericParts, ...],
    ) -> TypeExpression:
        """Return an iterable ABC target for compatible iterable unions.

        Args:
            parts: Parts supplied as tuple[_GenericParts, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        item_options: tuple[TypeExpression, ...] = tuple(
            item.arguments[0] for item in parts
        )
        item_type: TypeExpression = self._collapse_argument_union(
            options=item_options,
        )
        target_name: str = self._iterable_target_name(parts=parts)
        return GenericTypeRef(
            origin=ImportedTypeRef.absolute(
                module_parts=("collections", "abc"),
                name=target_name,
            ),
            arguments=(item_type,),
        )

    def _iterable_target_name(
        self,
        *,
        parts: tuple[_GenericParts, ...],
    ) -> str:
        """Return the narrowest supported ABC for iterable parts.

        Args:
            parts: Parts supplied as tuple[_GenericParts, ...] for this
                operation.

        Returns:
            str produced by this operation.

        """
        origin_names: set[str] = {
            self._origin_name_from_parts(parts_item=part) for part in parts
        }
        if origin_names <= self._MUTABLE_SEQUENCE_ORIGINS:
            return "MutableSequence"
        if origin_names <= self._SEQUENCE_ORIGINS:
            return "Sequence"
        if origin_names <= self._MUTABLE_SET_ORIGINS:
            return "MutableSet"
        if origin_names <= self._SET_ORIGINS:
            return "Set"
        if origin_names <= self._ITERABLE_ORIGINS:
            return "Collection"
        return "Iterable"

    def _collapse_argument_union(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Collapse nested generic argument unions.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        simplified_options: tuple[TypeExpression, ...] = self.simplify(
            options=options,
            collapse_limit=None,
        )
        if len(simplified_options) == 1:
            return simplified_options[0]
        return UnionTypeRef(options=simplified_options)

    def _sort_options(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Sort union members coherently and deterministically.

        Args:
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            tuple[TypeExpression, ...] produced by this operation.

        """
        return tuple(sorted(options, key=self._sort_key))

    def _sort_key(self, option: TypeExpression) -> tuple[int, str]:
        """Return deterministic union-sort key.

        Args:
            option: Option supplied as TypeExpression for this operation.

        Returns:
            tuple[int, str] produced by this operation.

        """
        builtin_name: str | None = self._builtin_name(option=option)
        rank: int = self._sort_rank(option=option, builtin_name=builtin_name)
        key_text: str = (
            builtin_name if builtin_name is not None else option.key()
        )
        return (rank, key_text)

    def _sort_rank(
        self,
        *,
        option: TypeExpression,
        builtin_name: str | None,
    ) -> int:
        """Return a deterministic rank for a union option.

        Args:
            builtin_name: Identifier of the builtin being resolved.
            option: Option supplied as TypeExpression for this operation.

        Returns:
            int produced by this operation.

        """
        rank: int = 50
        if builtin_name == "object":
            rank = 0
        elif builtin_name in self._NUMERIC_RANKS:
            rank = 10
        elif builtin_name == "None":
            rank = 90
        elif isinstance(option, LiteralTypeRef):
            rank = 20
        elif isinstance(option, GenericTypeRef):
            rank = 30
        elif isinstance(option, ImportedTypeRef):
            rank = 40
        return rank

    def _has_builtin(
        self,
        *,
        options: tuple[TypeExpression, ...],
        name: str,
    ) -> bool:
        """Return whether the options contain a builtin name.

        Args:
            name: Identifier of the name being resolved.
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        return any(
            self._is_builtin_name(option=option, name=name)
            for option in options
        )

    def _is_builtin_name(self, *, option: TypeExpression, name: str) -> bool:
        """Return whether an option is a builtin ref with this name.

        Args:
            name: Identifier of the name being resolved.
            option: Option supplied as TypeExpression for this operation.

        Returns:
            Whether the requested condition holds.

        """
        return self._builtin_name(option=option) == name


@dataclass(slots=True, frozen=True)
class CallableTypeRef(TypeExpression):
    """Reference a ``collections.abc.Callable`` type expression.

    Attributes:
        parameters: Parameters retained as tuple[TypeExpression, ...] | None by
            this instance.
        returns: Returns retained as TypeExpression by this instance.

    """

    parameters: tuple[TypeExpression, ...] | None
    returns: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a callable type AST expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        callable_node: expr = resolver.imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("collections", "abc"),
                imported_name="Callable",
            ),
            use=_use,
        )
        parameter_node: expr = self._parameter_node(
            resolver=resolver,
            _use=_use,
        )
        return_node: expr = self.returns.to_ast(resolver=resolver, _use=_use)
        return AstExpressionBuilder.subscript(
            value=callable_node,
            args=(parameter_node, return_node),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a callable type string.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        callable_name: str = renderer.render_imported(
            source=SemanticImportSource.absolute(
                module_parts=("collections", "abc"),
                imported_name="Callable",
            ),
        )
        if self.parameters is None:
            parameters_text: str = "..."
        else:
            parameters_text = (
                "["
                + ", ".join(
                    parameter.render(renderer=renderer)
                    for parameter in self.parameters
                )
                + "]"
            )
        returns_text: str = self.returns.render(renderer=renderer)
        return f"{callable_name}[{parameters_text}, {returns_text}]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        if self.parameters is None:
            parameter_key: str = "..."
        else:
            parameter_key = ",".join(
                parameter.key() for parameter in self.parameters
            )
        return f"callable:[{parameter_key}]->{self.returns.key()}"

    def _parameter_node(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Build callable parameter node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        if self.parameters is None:
            return Constant(value=Ellipsis)
        return AstList(
            elts=[
                parameter.to_ast(resolver=resolver, _use=_use)
                for parameter in self.parameters
            ],
            ctx=Load(),
        )


@dataclass(slots=True, frozen=True)
class LiteralTypeRef(TypeExpression):
    """Reference a ``typing.Literal`` expression.

    Attributes:
        values: Values retained as tuple[LiteralValue, ...] by this instance.

    """

    values: tuple[LiteralValue, ...]

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a Literal AST expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        literal_node: expr = resolver.imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Literal",
            ),
            use=_use,
        )
        return AstExpressionBuilder.subscript(
            value=literal_node,
            args=tuple(Constant(value=value) for value in self.values),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a Literal string.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        literal_name: str = renderer.render_imported(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Literal",
            ),
        )
        values_text: str = ", ".join(repr(value) for value in self.values)
        return f"{literal_name}[{values_text}]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return "literal:" + ",".join(repr(value) for value in self.values)


class AstExpressionBuilder:
    """Semantic helpers for AST expression composition."""

    @staticmethod
    def subscript(*, value: expr, args: tuple[expr, ...]) -> Subscript:
        """Create ``value[arg]`` or ``value[arg1, arg2]``.

        Args:
            args: Collection of args supplied for this operation.
            value: The value examined while create ``value[arg]`` or
                ``value[arg1, arg2]``.

        Returns:
            Subscript produced by this operation.

        """
        if not args:
            msg: str = "Subscript requires at least one argument."
            fail(message=msg)
        slice_node: expr
        if len(args) == 1:
            slice_node = args[0]
        else:
            slice_node = AstTuple(elts=list(args), ctx=Load())
        return Subscript(value=value, slice=slice_node, ctx=Load())

    @staticmethod
    def union(*, options: tuple[expr, ...]) -> expr:
        """Create ``A | B | C`` as nested ``BinOp`` nodes.

        Args:
            options: Options supplied as tuple[expr, ...] for this operation.

        Returns:
            expr produced by this operation.

        """
        if not options:
            msg: str = "Union requires at least one option."
            fail(message=msg)
        current: expr = options[0]
        for option in options[1:]:
            current = BinOp(left=current, op=BitOr(), right=option)
        return current


class TypeExpressionResolver:
    """Resolve semantic type expressions into AST annotation nodes."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the resolver.

        Args:
            imports: Imports supplied as UsageAwareImportCollector for this
                operation.

        """
        self.imports: UsageAwareImportCollector = imports
        self._validator: IdentifierValidator = IdentifierValidator()

    def validate_identifier(self, *, name: str, label: str) -> None:
        """Validate a type-expression identifier.

        Args:
            label: Label supplied as str for this operation.
            name: Identifier of the name being resolved.

        """
        self._validator.validate_identifier(name=name, label=label)

    def annotation(self, *, value: TypeExpression) -> expr:
        """Resolve an annotation use.

        Args:
            value: The value examined while resolve an annotation use.

        Returns:
            expr produced by this operation.

        """
        return value.to_ast(resolver=self, _use=ImportUseSite.annotation())

    def protocol_base(self, *, value: TypeExpression) -> expr:
        """Resolve a protocol-base use.

        Args:
            value: The value examined while resolve a protocol-base use.

        Returns:
            expr produced by this operation.

        """
        return value.to_ast(resolver=self, _use=ImportUseSite.protocol_base())

    def typevar_bound(self, *, value: TypeExpression) -> expr:
        """Resolve a TypeVar bound use.

        Args:
            value: The value examined while resolve a TypeVar bound use.

        Returns:
            expr produced by this operation.

        """
        return value.to_ast(resolver=self, _use=ImportUseSite.typevar_bound())

    def typevar_constraint(self, *, value: TypeExpression) -> expr:
        """Resolve a TypeVar constraint use.

        Args:
            value: The value examined while resolve a TypeVar constraint use.

        Returns:
            expr produced by this operation.

        """
        return value.to_ast(
            resolver=self,
            _use=ImportUseSite.typevar_constraint(),
        )


class TypeHintStringRenderer:
    """Render semantic type expressions as strings and collect imports."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the string renderer.

        Args:
            imports: Imports supplied as UsageAwareImportCollector for this
                operation.

        """
        self._imports: UsageAwareImportCollector = imports
        self._validator: IdentifierValidator = IdentifierValidator()

    def validate_identifier(self, *, name: str, label: str) -> None:
        """Validate a rendered identifier.

        Args:
            label: Label supplied as str for this operation.
            name: Identifier of the name being resolved.

        """
        self._validator.validate_identifier(name=name, label=label)

    def render(self, *, value: TypeExpression) -> str:
        """Render a semantic type expression as a type-hint string.

        Args:
            value: The value examined while render a semantic type expression
                as a type-hint string.

        Returns:
            Rendered source text produced by this operation.

        """
        return value.render(renderer=self)

    def render_imported(self, *, source: SemanticImportSource) -> str:
        """Render an imported type and collect a string-hint import.

        Args:
            source: The source examined while render an imported type and
                collect a string-hint import.

        Returns:
            Rendered source text produced by this operation.

        """
        node: Name = self._imports.require_from_source(
            source=source,
            use=ImportUseSite.string_type_hint(owner=source.imported_name),
        )
        return node.id


@dataclass(slots=True, frozen=True)
class TypeVarSignature:
    """Semantic identity of a generated ``TypeVar``.

    Attributes:
        bound: Bound retained as TypeExpression | None by this instance.
        constraints: Constraints retained as tuple[TypeExpression, ...] by this
            instance.
        contravariant: Contravariant retained as bool by this instance.
        covariant: Covariant retained as bool by this instance.

    """

    bound: TypeExpression | None
    constraints: tuple[TypeExpression, ...]
    covariant: bool
    contravariant: bool


@dataclass(slots=True, frozen=True)
class ParamSpecSignature:
    """Semantic identity of a generated ``ParamSpec``.

    Attributes:
        bound: Bound retained as TypeExpression | None by this instance.
        contravariant: Contravariant retained as bool by this instance.
        covariant: Covariant retained as bool by this instance.

    """

    bound: TypeExpression | None
    covariant: bool
    contravariant: bool


@dataclass(slots=True, frozen=True)
class TypeVarSpec:
    """Generated TypeVar declaration spec.

    Attributes:
        name: Identifier used to refer to the name.
        signature: Signature retained as TypeVarSignature by this instance.

    """

    name: str
    signature: TypeVarSignature

    def ref(self) -> TypeVarRef:
        """Return a type-expression reference to this TypeVar.

        Returns:
            TypeVarRef produced by this operation.

        """
        return TypeVarRef(spec=self)


@dataclass(slots=True, frozen=True)
class ParamSpecSpec:
    """Generated ParamSpec declaration spec.

    Attributes:
        name: Identifier used to refer to the name.
        signature: Signature retained as ParamSpecSignature by this instance.

    """

    name: str
    signature: ParamSpecSignature

    def ref(self) -> ParamSpecRef:
        """Return a type-expression reference to this ParamSpec.

        Returns:
            ParamSpecRef produced by this operation.

        """
        return ParamSpecRef(spec=self)

    def args_ref(self) -> ParamSpecArgsRef:
        """Return a ``P.args`` type-expression reference.

        Returns:
            ParamSpecArgsRef produced by this operation.

        """
        return ParamSpecArgsRef(spec=self)

    def kwargs_ref(self) -> ParamSpecKwargsRef:
        """Return a ``P.kwargs`` type-expression reference.

        Returns:
            ParamSpecKwargsRef produced by this operation.

        """
        return ParamSpecKwargsRef(spec=self)


class TypeParameterNameRegistry:
    """Allocate stable TypeVar and ParamSpec names."""

    _TYPEVAR_NAMES: Final[tuple[str, ...]] = (
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    )
    _PARAMSPEC_NAMES: Final[tuple[str, ...]] = ("P", "Q", "R", "S")

    def __init__(self) -> None:
        """Initialize the registry."""
        self._typevars_by_key: dict[str, str] = {}
        self._typevar_keys_by_name: dict[str, str] = {}
        self._paramspecs_by_key: dict[str, str] = {}
        self._paramspec_keys_by_name: dict[str, str] = {}

    def typevar_name(self, *, key: str, name: str | None) -> str:
        """Return a stable TypeVar name.

        Args:
            key: Key supplied as str for this operation.
            name: Identifier of the name being resolved.

        Returns:
            str produced by this operation.

        """
        if name is not None:
            return self._register_typevar(name=name, key=key)
        existing: str | None = self._typevars_by_key.get(key)
        if existing is not None:
            return existing
        return self._register_typevar(
            name=self._next_name(
                names=self._TYPEVAR_NAMES,
                used=set(self._typevar_keys_by_name),
            ),
            key=key,
        )

    def paramspec_name(self, *, key: str, name: str | None) -> str:
        """Return a stable ParamSpec name.

        Args:
            key: Key supplied as str for this operation.
            name: Identifier of the name being resolved.

        Returns:
            str produced by this operation.

        """
        if name is not None:
            return self._register_paramspec(name=name, key=key)
        existing: str | None = self._paramspecs_by_key.get(key)
        if existing is not None:
            return existing
        return self._register_paramspec(
            name=self._next_name(
                names=self._PARAMSPEC_NAMES,
                used=set(self._paramspec_keys_by_name),
            ),
            key=key,
        )

    @staticmethod
    def _next_name(*, names: tuple[str, ...], used: set[str]) -> str:
        """Return the next available generated name.

        Args:
            names: Names supplied as tuple[str, ...] for this operation.
            used: Used supplied as set[str] for this operation.

        Returns:
            str produced by this operation.

        """
        for name in names:
            if name not in used:
                return name
        index: int = 1
        while True:
            for name in names:
                candidate: str = f"{name}{index}"
                if candidate not in used:
                    return candidate
            index += 1

    def _register_typevar(self, *, name: str, key: str) -> str:
        """Register a TypeVar name for a semantic key.

        Args:
            key: Key supplied as str for this operation.
            name: Identifier of the name being resolved.

        Returns:
            str produced by this operation.

        """
        existing_key: str | None = self._typevar_keys_by_name.get(name)
        if existing_key is not None and existing_key != key:
            msg: str = (
                f"TypeVar name {name!r} already has a different signature."
            )
            fail(message=msg)
        self._typevar_keys_by_name[name] = key
        self._typevars_by_key[key] = name
        return name

    def _register_paramspec(self, *, name: str, key: str) -> str:
        """Register a ParamSpec name for a semantic key.

        Args:
            key: Key supplied as str for this operation.
            name: Identifier of the name being resolved.

        Returns:
            str produced by this operation.

        """
        existing_key: str | None = self._paramspec_keys_by_name.get(name)
        if existing_key is not None and existing_key != key:
            msg: str = (
                f"ParamSpec name {name!r} already has a different signature."
            )
            fail(message=msg)
        self._paramspec_keys_by_name[name] = key
        self._paramspecs_by_key[key] = name
        return name


class TypeParameterBuilder:
    """Build AST type parameters for function/class definitions."""

    def build_type_params(
        self,
        *,
        type_vars: tuple[TypeVarSpec, ...] = (),
        param_specs: tuple[ParamSpecSpec, ...] = (),
    ) -> list[type_param]:
        """Build type parameters from specs.

        Args:
            param_specs: Param specs supplied as tuple[ParamSpecSpec, ...] for
                this operation.
            type_vars: Type vars supplied as tuple[TypeVarSpec, ...] for this
                operation.

        Returns:
            list[type_param] produced by this operation.

        """
        result: list[type_param] = [
            self._build_typevar(spec=tv) for tv in type_vars
        ]
        result.extend(self._build_paramspec(spec=ps) for ps in param_specs)
        return result

    @staticmethod
    def _build_typevar(*, spec: TypeVarSpec) -> TypeVar:
        """Build a TypeVar type parameter.

        Args:
            spec: Spec supplied as TypeVarSpec for this operation.

        Returns:
            TypeVar produced by this operation.

        """
        bound_node: expr | None = None
        if spec.signature.bound is not None:
            bound_node = None
        return TypeVar(name=spec.name, bound=bound_node, default_value=None)

    @staticmethod
    def _build_paramspec(*, spec: ParamSpecSpec) -> ParamSpec:
        """Build a ParamSpec type parameter.

        Args:
            spec: Spec supplied as ParamSpecSpec for this operation.

        Returns:
            ParamSpec produced by this operation.

        """
        return ParamSpec(name=spec.name, default_value=None)


def create_simple_typevar(name: str) -> TypeVar:
    """Create a simple TypeVar with no bound or constraints.

    This is the canonical way to create TypeVars in the codebase.
    Direct TypeVar() calls should be replaced with this function.


    Args:
        name: Identifier of the name being resolved.

    Returns:
        TypeVar produced by this operation.

    """
    return TypeVar(name=name, bound=None, default_value=None)


def create_simple_paramspec(name: str) -> ParamSpec:
    """Create a simple ParamSpec with no default value.

    This is the canonical way to create ParamSpecs in the codebase.
    Direct ParamSpec() calls should be replaced with this function.


    Args:
        name: Identifier of the name being resolved.

    Returns:
        ParamSpec produced by this operation.

    """
    return ParamSpec(name=name, default_value=None)


@dataclass(slots=True, frozen=True)
class ArgumentSpec:
    """Semantic method argument spec.

    Attributes:
        default: Default retained as expr | None by this instance.
        kind: Kind retained as ArgumentKind by this instance.
        name: Identifier used to refer to the name.
        type_hint: Type hint retained as TypeExpression by this instance.

    """

    name: str
    type_hint: TypeExpression
    kind: ArgumentKind = "positional_or_keyword"
    default: expr | None = None


@dataclass(slots=True, frozen=True)
class SelfArgument:
    """Special receiver argument representing ``self``.

    Attributes:
        type_hint: Type hint retained as TypeExpression by this instance.

    """

    type_hint: TypeExpression = field(default_factory=SelfTypeRef)

    def to_argument(self) -> ArgumentSpec:
        """Convert to a normal argument spec.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(name="self", type_hint=self.type_hint)


@dataclass(slots=True, frozen=True)
class ClsArgument:
    """Special receiver argument representing ``cls``.

    Attributes:
        type_hint: Type hint retained as TypeExpression by this instance.

    """

    type_hint: TypeExpression

    def to_argument(self) -> ArgumentSpec:
        """Convert to a normal argument spec.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(name="cls", type_hint=self.type_hint)


@dataclass(slots=True, frozen=True)
class SlashMarker:
    """Semantic marker for positional-only slash syntax."""


@dataclass(slots=True, frozen=True)
class StarMarker:
    """Semantic marker for bare keyword-only star syntax."""


ArgumentItem = (
    ArgumentSpec | SelfArgument | ClsArgument | SlashMarker | StarMarker
)


class Args:
    """Factory for semantic argument objects."""

    @staticmethod
    def self_arg(*, type_hint: TypeExpression | None = None) -> SelfArgument:
        """Create a special ``self`` argument.

        Args:
            type_hint: Type hint supplied as TypeExpression | None for this
                operation.

        Returns:
            SelfArgument produced by this operation.

        """
        return SelfArgument(type_hint=type_hint or SelfTypeRef())

    @staticmethod
    def cls_arg(*, type_hint: TypeExpression | None = None) -> ClsArgument:
        """Create a special ``cls`` argument.

        Args:
            type_hint: Type hint supplied as TypeExpression | None for this
                operation.

        Returns:
            ClsArgument produced by this operation.

        """
        return ClsArgument(
            type_hint=type_hint
            or GenericTypeRef(
                origin=BuiltinTypeRef(name="type"),
                arguments=(SelfTypeRef(),),
            ),
        )

    @staticmethod
    def arg(
        *,
        name: str,
        type_hint: TypeExpression,
        default: expr | None = None,
    ) -> ArgumentSpec:
        """Create a positional-or-keyword argument.

        Args:
            default: Default supplied as expr | None for this operation.
            name: Identifier of the name being resolved.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(name=name, type_hint=type_hint, default=default)

    @staticmethod
    def posonly(
        *,
        name: str,
        type_hint: TypeExpression,
        default: expr | None = None,
    ) -> ArgumentSpec:
        """Create a positional-only argument.

        Args:
            default: Default supplied as expr | None for this operation.
            name: Identifier of the name being resolved.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(
            name=name,
            type_hint=type_hint,
            kind="positional_only",
            default=default,
        )

    @staticmethod
    def kwonly(
        *,
        name: str,
        type_hint: TypeExpression,
        default: expr | None = None,
    ) -> ArgumentSpec:
        """Create a keyword-only argument.

        Args:
            default: Default supplied as expr | None for this operation.
            name: Identifier of the name being resolved.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(
            name=name,
            type_hint=type_hint,
            kind="keyword_only",
            default=default,
        )

    @staticmethod
    def varargs(
        *,
        type_hint: TypeExpression,
        name: str = "args",
    ) -> ArgumentSpec:
        """Create a ``*args`` argument.

        Args:
            name: Identifier of the name being resolved.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(name=name, type_hint=type_hint, kind="vararg")

    @staticmethod
    def kwargs(
        *,
        type_hint: TypeExpression,
        name: str = "kwargs",
    ) -> ArgumentSpec:
        """Create a ``**kwargs`` argument.

        Args:
            name: Identifier of the name being resolved.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        return ArgumentSpec(name=name, type_hint=type_hint, kind="kwarg")

    @staticmethod
    def slash() -> SlashMarker:
        """Create a positional-only slash marker.

        Returns:
            SlashMarker produced by this operation.

        """
        return SlashMarker()

    @staticmethod
    def star() -> StarMarker:
        """Create a bare keyword-only star marker.

        Returns:
            StarMarker produced by this operation.

        """
        return StarMarker()


@dataclass(slots=True, frozen=True)
class MethodSpec:
    """Semantic protocol method spec.

    Attributes:
        arguments: Arguments retained as tuple[ArgumentItem, ...] by this
            instance.
        body: Body retained as tuple[stmt, ...] | None by this instance.
        decorators: Decorators retained as tuple[expr, ...] by this instance.
        docstring: Docstring retained as str | None by this instance.
        name: Identifier used to refer to the name.
        returns: Returns retained as TypeExpression by this instance.
        type_params: Type params retained as tuple[TypeVarSpec | ParamSpecSpec,
            ...] by this instance.

    """

    name: str
    arguments: tuple[ArgumentItem, ...]
    returns: TypeExpression
    docstring: str | None = None
    decorators: tuple[expr, ...] = ()
    body: tuple[stmt, ...] | None = None
    type_params: tuple[TypeVarSpec | ParamSpecSpec, ...] = ()


@dataclass(slots=True, frozen=True)
class ProtocolSpec:
    """Semantic protocol class spec.

    Attributes:
        bases: Bases retained as tuple[TypeExpression, ...] by this instance.
        decorators: Decorators retained as tuple[expr, ...] by this instance.
        docstring: Docstring retained as str | None by this instance.
        methods: Methods retained as tuple[MethodSpec, ...] by this instance.
        name: Identifier used to refer to the name.

    """

    methods: tuple[MethodSpec, ...]
    name: str | None = None
    docstring: str | None = None
    bases: tuple[TypeExpression, ...] = ()
    decorators: tuple[expr, ...] = ()


@dataclass(slots=True, frozen=True)
class ProtocolRegistration:
    """Result of registering a protocol.

    Attributes:
        class_node: Class node retained as ClassDef by this instance.
        is_existing: Is existing retained as bool by this instance.
        match_reason: Match reason retained as Literal['name', 'shape', 'new']
            by this instance.
        spec: Spec retained as ProtocolSpec by this instance.

    """

    spec: ProtocolSpec
    class_node: ClassDef
    is_existing: bool
    match_reason: Literal["name", "shape", "new"]


@dataclass(slots=True, frozen=True)
class GeneratedTopBlock:
    """Top-of-module nodes generated by the collector.

    Attributes:
        declaration_nodes_after_imports: Declaration nodes after imports
            retained as tuple[stmt, ...] by this instance.
        missing_import_nodes: Missing import nodes retained as tuple[stmt, ...]
            by this instance.

    """

    missing_import_nodes: tuple[stmt, ...]
    declaration_nodes_after_imports: tuple[stmt, ...]

    @property
    def all_nodes_for_empty_module(self) -> tuple[stmt, ...]:
        """Return imports followed by declarations.

        Returns:
            tuple[stmt, ...] produced by this operation.

        """
        return (
            *self.missing_import_nodes,
            *self.declaration_nodes_after_imports,
        )


@dataclass(slots=True, frozen=True)
class ProtocolShape:
    """Comparable structural shape of a protocol class.

    Attributes:
        methods: Methods retained as tuple[tuple[str, tuple[str, ...]], ...] by
            this instance.

    """

    methods: tuple[tuple[str, tuple[str, ...]], ...]


class ExistingProtocolIndex:
    """Index existing protocol classes by name and method shape."""

    def __init__(self, *, class_nodes: Iterable[ClassDef]) -> None:
        """Initialize the index.

        Args:
            class_nodes: Class nodes supplied as Iterable[ClassDef] for this
                operation.

        """
        self._classes_by_name: dict[str, ClassDef] = {}
        self._protocols_by_shape: dict[ProtocolShape, ClassDef] = {}
        for class_node in class_nodes:
            self._classes_by_name[class_node.name] = class_node
            if self._is_protocol_class(node=class_node):
                shape: ProtocolShape = self._shape_from_class(node=class_node)
                self._protocols_by_shape[shape] = class_node

    @classmethod
    def from_context(
        cls,
        *,
        context: ExistingNodeContext,
    ) -> ExistingProtocolIndex:
        """Create an index from existing-node context.

        Args:
            context: Context supplied as ExistingNodeContext for this
                operation.

        Returns:
            ExistingProtocolIndex produced by this operation.

        """
        return cls(class_nodes=context.class_nodes)

    def find_by_name(self, *, name: str) -> ClassDef | None:
        """Return an existing protocol class by name.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            ClassDef | None produced by this operation.

        """
        node: ClassDef | None = self._classes_by_name.get(name)
        if node is None or not self._is_protocol_class(node=node):
            return None
        return node

    def find_by_shape(self, *, spec: ProtocolSpec) -> ClassDef | None:
        """Return an existing protocol class by method shape.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            ClassDef | None produced by this operation.

        """
        return self._protocols_by_shape.get(self._shape_from_spec(spec=spec))

    @staticmethod
    def _method_shape_from_function(
        *,
        node: FunctionDef,
    ) -> tuple[str, tuple[str, ...]]:
        """Return a comparable shape for one function.

        Args:
            node: The node examined while return a comparable shape for one
                function.

        Returns:
            tuple[str, tuple[str, ...]] produced by this operation.

        """
        argument_names: list[str] = []
        argument_names.extend(item.arg for item in node.args.posonlyargs)
        argument_names.extend(item.arg for item in node.args.args)
        if node.args.vararg is not None:
            argument_names.append(f"*{node.args.vararg.arg}")
        argument_names.extend(item.arg for item in node.args.kwonlyargs)
        if node.args.kwarg is not None:
            argument_names.append(f"**{node.args.kwarg.arg}")
        return (node.name, tuple(argument_names))

    @staticmethod
    def _argument_shape_name(*, argument: ArgumentSpec) -> str:
        """Return the shape name for one argument.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.

        Returns:
            str produced by this operation.

        """
        if argument.kind == "vararg":
            return f"*{argument.name}"
        if argument.kind == "kwarg":
            return f"**{argument.name}"
        return argument.name

    def _is_protocol_class(self, *, node: ClassDef) -> bool:
        """Return whether a class base mentions Protocol.

        Args:
            node: The node examined while return whether a class base mentions
                Protocol.

        Returns:
            Whether the requested condition holds.

        """
        return any(
            self._base_mentions_protocol(base=base) for base in node.bases
        )

    def _base_mentions_protocol(self, *, base: expr) -> bool:
        """Return whether a base expression mentions Protocol.

        Args:
            base: Base supplied as expr for this operation.

        Returns:
            Whether the requested condition holds.

        """
        if isinstance(base, Name):
            return base.id == "Protocol"
        if isinstance(base, Attribute):
            return base.attr == "Protocol"
        if isinstance(base, Subscript):
            return self._base_mentions_protocol(base=base.value)
        return False

    def _shape_from_class(self, *, node: ClassDef) -> ProtocolShape:
        """Build a structural method shape from an existing class.

        Args:
            node: The node examined while build a structural method shape from
                an existing class.

        Returns:
            ProtocolShape produced by this operation.

        """
        methods: list[tuple[str, tuple[str, ...]]] = [
            self._method_shape_from_function(node=body_node)
            for body_node in node.body
            if isinstance(body_node, FunctionDef)
        ]
        return ProtocolShape(methods=tuple(sorted(methods)))

    def _shape_from_spec(self, *, spec: ProtocolSpec) -> ProtocolShape:
        """Build a structural shape from a protocol spec.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            ProtocolShape produced by this operation.

        """
        methods: list[tuple[str, tuple[str, ...]]] = []
        for method in spec.methods:
            argument_names: tuple[str, ...] = self._argument_names(
                arguments=method.arguments,
            )
            methods.append((method.name, argument_names))
        return ProtocolShape(methods=tuple(sorted(methods)))

    def _argument_names(
        self,
        *,
        arguments: tuple[ArgumentItem, ...],
    ) -> tuple[str, ...]:
        """Return comparable argument names from semantic arguments.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            tuple[str, ...] produced by this operation.

        """
        names: list[str] = []
        for item in arguments:
            if isinstance(item, SelfArgument):
                names.append("self")
            elif isinstance(item, ClsArgument):
                names.append("cls")
            elif isinstance(item, ArgumentSpec):
                names.append(self._argument_shape_name(argument=item))
        return tuple(names)


class ParameterNormalizer:
    """Normalize rich argument grammar into AST-compatible specs."""

    def __init__(self) -> None:
        """Initialize the normalizer."""
        self._validator: IdentifierValidator = IdentifierValidator()

    def normalize(
        self,
        *,
        items: tuple[ArgumentItem, ...],
    ) -> tuple[ArgumentSpec, ...]:
        """Normalize argument objects and markers.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            tuple[ArgumentSpec, ...] produced by this operation.

        """
        state: ParameterState = ParameterState()
        normalized: list[ArgumentSpec] = []
        for item in items:
            self._apply_item(item=item, state=state, normalized=normalized)
        return tuple(normalized)

    @staticmethod
    def _as_posonly(*, argument: ArgumentSpec) -> ArgumentSpec:
        """Convert a normal argument to positional-only.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        if argument.kind in {"keyword_only", "vararg", "kwarg"}:
            return argument
        return ArgumentSpec(
            name=argument.name,
            type_hint=argument.type_hint,
            kind="positional_only",
            default=argument.default,
        )

    @staticmethod
    def _as_kwonly(*, argument: ArgumentSpec) -> ArgumentSpec:
        """Convert a normal argument to keyword-only.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.

        Returns:
            ArgumentSpec produced by this operation.

        """
        if argument.kind in {"vararg", "kwarg"}:
            return argument
        return ArgumentSpec(
            name=argument.name,
            type_hint=argument.type_hint,
            kind="keyword_only",
            default=argument.default,
        )

    def _apply_item(
        self,
        *,
        item: ArgumentItem,
        state: ParameterState,
        normalized: list[ArgumentSpec],
    ) -> None:
        """Apply one grammar item to the normalized argument list.

        Args:
            item: Item supplied as ArgumentItem for this operation.
            normalized: Normalized supplied as list[ArgumentSpec] for this
                operation.
            state: State supplied as ParameterState for this operation.

        """
        if isinstance(item, SelfArgument):
            normalized.append(item.to_argument())
            return
        if isinstance(item, ClsArgument):
            normalized.append(item.to_argument())
            return
        if isinstance(item, SlashMarker):
            state.apply_slash()
            normalized[:] = [
                self._as_posonly(argument=arg) for arg in normalized
            ]
            return
        if isinstance(item, StarMarker):
            state.apply_star()
            return
        self._append_argument(
            argument=item,
            state=state,
            normalized=normalized,
        )

    def _append_argument(
        self,
        *,
        argument: ArgumentSpec,
        state: ParameterState,
        normalized: list[ArgumentSpec],
    ) -> None:
        """Append one normalized argument.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.
            normalized: Normalized supplied as list[ArgumentSpec] for this
                operation.
            state: State supplied as ParameterState for this operation.

        """
        self._validator.validate_identifier(
            name=argument.name,
            label="argument",
        )
        if argument.kind == "vararg":
            state.apply_vararg()
            normalized.append(argument)
            return
        if argument.kind == "kwarg":
            state.apply_kwarg()
            normalized.append(argument)
            return
        if state.star_seen or state.vararg_seen:
            normalized.append(self._as_kwonly(argument=argument))
            return
        normalized.append(argument)


@dataclass(slots=True)
class ParameterState:
    """Mutable state used while normalizing arguments.

    Attributes:
        kwarg_seen: Kwarg seen retained as bool by this instance.
        slash_seen: Slash seen retained as bool by this instance.
        star_seen: Star seen retained as bool by this instance.
        vararg_seen: Vararg seen retained as bool by this instance.

    """

    slash_seen: bool = False
    star_seen: bool = False
    vararg_seen: bool = False
    kwarg_seen: bool = False

    def apply_slash(self) -> None:
        """Record a slash marker."""
        if self.slash_seen:
            msg: str = "Only one slash marker is allowed."
            fail(message=msg)
        if self.star_seen or self.vararg_seen:
            msg = "Slash marker must appear before * or *args."
            fail(message=msg)
        self.slash_seen = True

    def apply_star(self) -> None:
        """Record a bare star marker."""
        if self.star_seen:
            msg: str = "Only one star marker is allowed."
            fail(message=msg)
        if self.vararg_seen:
            msg = "Bare star cannot follow *args."
            fail(message=msg)
        self.star_seen = True

    def apply_vararg(self) -> None:
        """Record a varargs argument."""
        if self.star_seen:
            msg: str = "*args cannot follow a bare star marker."
            fail(message=msg)
        if self.vararg_seen:
            msg = "Only one *args argument is allowed."
            fail(message=msg)
        self.vararg_seen = True

    def apply_kwarg(self) -> None:
        """Record a kwargs argument."""
        if self.kwarg_seen:
            msg: str = "Only one **kwargs argument is allowed."
            fail(message=msg)
        self.kwarg_seen = True


@dataclass(slots=True, frozen=True)
class MethodSemanticProfile:
    """Semantic summary of one protocol method.

    Attributes:
        capability: Capability retained as str by this instance.
        is_dunder: Is dunder retained as bool by this instance.
        name: Identifier used to refer to the name.
        required_argument_count: Required argument count retained as int by
            this instance.

    """

    name: str
    capability: str
    required_argument_count: int
    is_dunder: bool


class ProtocolGrammar:
    """Infer protocol names and docstrings from method content."""

    _DUNDER_CAPABILITIES: Final[dict[str, str]] = {
        "__call__": "Call",
        "__iter__": "Iteration",
        "__next__": "NextItem",
        "__len__": "Length",
        "__contains__": "Containment",
        "__getitem__": "ItemAccess",
        "__setitem__": "ItemMutation",
        "__enter__": "ContextManagement",
        "__exit__": "ContextManagement",
        "__await__": "Awaiting",
        "__mul__": "Multiplication",
    }
    _VERB_CAPABILITIES: Final[dict[str, str]] = {
        "read": "Reading",
        "write": "Writing",
        "load": "Loading",
        "save": "Saving",
        "parse": "Parsing",
        "format": "Formatting",
        "transform": "Transformation",
        "convert": "Conversion",
        "validate": "Validation",
        "serialize": "Serialization",
        "deserialize": "Deserialization",
        "encode": "Encoding",
        "decode": "Decoding",
        "get": "Retrieval",
        "set": "Assignment",
        "add": "Mutation",
        "remove": "Removal",
    }
    _COMPOSITES: Final[dict[frozenset[str], str]] = {
        frozenset({"__iter__", "__next__"}): "Iterator",
        frozenset({"read", "write"}): "IO",
        frozenset({"encode", "decode"}): "EncodingRoundTrip",
        frozenset({"serialize", "deserialize"}): "SerializationRoundTrip",
        frozenset({"get", "set"}): "PropertyAccess",
    }

    def infer(self, *, spec: ProtocolSpec) -> ProtocolSpec:
        """Return a protocol spec with inferred name and docstrings.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            ProtocolSpec produced by this operation.

        """
        profiles: tuple[MethodSemanticProfile, ...] = tuple(
            self.profile_method(method=method) for method in spec.methods
        )
        protocol_name: str = spec.name or self.infer_name(profiles=profiles)
        protocol_docstring: str = spec.docstring or self.protocol_docstring(
            name=protocol_name,
            profiles=profiles,
        )
        return ProtocolSpec(
            name=protocol_name,
            docstring=protocol_docstring,
            methods=tuple(
                (
                    self._method_with_docstring(method=method, profile=profile)
                    for method, profile in zip(
                        spec.methods,
                        profiles,
                        strict=True,
                    )
                ),
            ),
            bases=spec.bases,
            decorators=spec.decorators,
        )

    def profile_method(self, *, method: MethodSpec) -> MethodSemanticProfile:
        """Build a semantic method profile.

        Args:
            method: Method supplied as MethodSpec for this operation.

        Returns:
            MethodSemanticProfile produced by this operation.

        """
        is_dunder: bool = method.name.startswith(
            "__",
        ) and method.name.endswith("__")
        capability: str = self._capability_for(method_name=method.name)
        required_count: int = sum(
            1
            for item in method.arguments
            if isinstance(item, ArgumentSpec)
            and item.default is None
            and (
                item.kind
                in {"positional_only", "positional_or_keyword", "keyword_only"}
            )
        )
        return MethodSemanticProfile(
            name=method.name,
            capability=capability,
            required_argument_count=required_count,
            is_dunder=is_dunder,
        )

    def infer_name(
        self,
        *,
        profiles: tuple[MethodSemanticProfile, ...],
    ) -> str:
        """Infer a protocol class name.

        Args:
            profiles: Profiles supplied as tuple[MethodSemanticProfile, ...]
                for this operation.

        Returns:
            str produced by this operation.

        """
        if not profiles:
            return "SupportsProtocolBehavior"
        composite: str | None = self._composite_name(profiles=profiles)
        if composite is not None:
            return f"Supports{composite}"
        capabilities: tuple[str, ...] = self._unique_capabilities(
            profiles=profiles,
        )
        if len(capabilities) == 1:
            return f"Supports{capabilities[0]}"
        return "Supports" + "And".join(capabilities[:3])

    def protocol_docstring(
        self,
        *,
        name: str,
        profiles: tuple[MethodSemanticProfile, ...],
    ) -> str:
        """Infer a protocol docstring.

        Args:
            name: Identifier of the name being resolved.
            profiles: Profiles supplied as tuple[MethodSemanticProfile, ...]
                for this operation.

        Returns:
            str produced by this operation.

        """
        if not profiles:
            return f"Protocol for objects implementing {name}."
        capabilities: str = self._human_join(
            values=tuple(
                self._title_to_words(value=profile.capability)
                for profile in profiles
            ),
        )
        methods: str = self._human_join(
            values=tuple(profile.name for profile in profiles),
        )
        return (
            f"Protocol for objects that support "
            f"{capabilities}"
            f". Required method set: "
            f"{methods}"
            f"."
        )

    def method_docstring(self, *, profile: MethodSemanticProfile) -> str:
        """Infer one method docstring.

        Args:
            profile: Profile supplied as MethodSemanticProfile for this
                operation.

        Returns:
            str produced by this operation.

        """
        capability: str = self._title_to_words(value=profile.capability)
        if profile.is_dunder:
            return f"Implement {capability} behavior for this object."
        return f"Perform {capability} using this method's declared inputs."

    @staticmethod
    def _unique_capabilities(
        *,
        profiles: tuple[MethodSemanticProfile, ...],
    ) -> tuple[str, ...]:
        """Return capabilities without duplicates.

        Args:
            profiles: Profiles supplied as tuple[MethodSemanticProfile, ...]
                for this operation.

        Returns:
            tuple[str, ...] produced by this operation.

        """
        result: list[str] = []
        seen: set[str] = set()
        for profile in profiles:
            if profile.capability not in seen:
                seen.add(profile.capability)
                result.append(profile.capability)
        return tuple(result)

    @staticmethod
    def _split_identifier(*, name: str) -> tuple[str, ...]:
        """Split snake/camel/Pascal/dunder identifiers into words.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            tuple[str, ...] produced by this operation.

        """
        stripped: str = name.strip("_")
        snake_ready: str = sub(
            pattern="([a-z0-9])([A-Z])",
            repl="\\1_\\2",
            string=stripped,
        )
        return tuple(
            part.lower() for part in snake_ready.split(sep="_") if part
        )

    @staticmethod
    def _pascal_case(*, words: tuple[str, ...]) -> str:
        """Convert words to PascalCase.

        Args:
            words: Words supplied as tuple[str, ...] for this operation.

        Returns:
            str produced by this operation.

        """
        return "".join(word[:1].upper() + word[1:] for word in words)

    @staticmethod
    def _title_to_words(*, value: str) -> str:
        """Convert PascalCase to lowercase words.

        Args:
            value: The value examined while convert PascalCase to lowercase
                words.

        Returns:
            str produced by this operation.

        """
        return sub(pattern="(?<!^)(?=[A-Z])", repl=" ", string=value).lower()

    @staticmethod
    def _human_join(*, values: tuple[str, ...]) -> str:
        """Join words with English punctuation.

        Args:
            values: Values supplied as tuple[str, ...] for this operation.

        Returns:
            str produced by this operation.

        """
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        if len(values) == Constants.two_item_count:
            return f"{values[0]} and {values[1]}"
        return f"{', '.join(values[:-1])}, and {values[-1]}"

    def _method_with_docstring(
        self,
        *,
        method: MethodSpec,
        profile: MethodSemanticProfile,
    ) -> MethodSpec:
        """Return method with generated docstring when missing.

        Args:
            method: Method supplied as MethodSpec for this operation.
            profile: Profile supplied as MethodSemanticProfile for this
                operation.

        Returns:
            MethodSpec produced by this operation.

        """
        return MethodSpec(
            name=method.name,
            arguments=method.arguments,
            returns=method.returns,
            docstring=method.docstring
            or self.method_docstring(profile=profile),
            decorators=method.decorators,
            body=method.body,
            type_params=method.type_params,
        )

    def _capability_for(self, *, method_name: str) -> str:
        """Infer a capability for one method name.

        Args:
            method_name: Identifier of the method being resolved.

        Returns:
            str produced by this operation.

        """
        if method_name in self._DUNDER_CAPABILITIES:
            return self._DUNDER_CAPABILITIES[method_name]
        words: tuple[str, ...] = self._split_identifier(name=method_name)
        if not words:
            return "ProtocolBehavior"
        first: str = words[0]
        mapped: str | None = self._VERB_CAPABILITIES.get(first)
        if mapped is not None:
            noun: str = words[-1]
            if noun != first:
                return self._pascal_case(words=(noun, mapped))
            return mapped
        return self._pascal_case(words=words)

    def _composite_name(
        self,
        *,
        profiles: tuple[MethodSemanticProfile, ...],
    ) -> str | None:
        """Return a composite protocol name if applicable.

        Args:
            profiles: Profiles supplied as tuple[MethodSemanticProfile, ...]
                for this operation.

        Returns:
            str | None produced by this operation.

        """
        names: frozenset[str] = frozenset(profile.name for profile in profiles)
        public_names: frozenset[str] = frozenset(
            name.strip("_") for name in names
        )
        for required_names, capability in self._COMPOSITES.items():
            if required_names <= names or required_names <= public_names:
                return capability
        return None


class CastExpressionFactory:
    """Build semantic ``typing.cast`` call expressions."""

    def __init__(
        self,
        *,
        imports: UsageAwareImportCollector,
        renderer: TypeHintStringRenderer,
    ) -> None:
        """Initialize the factory.

        Args:
            imports: Imports supplied as UsageAwareImportCollector for this
                operation.
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        """
        self._imports: UsageAwareImportCollector = imports
        self._renderer: TypeHintStringRenderer = renderer

    def cast(self, *, type_hint: TypeExpression, target: expr) -> Call:
        """Return ``cast("TypeHint", target)`` as an AST call.

        The cast function itself is a runtime import, while every import needed
        only by the string type hint is collected as a type-checking import.


        Args:
            target: The target examined while return ``cast("TypeHint",
                target)`` as an AST call.
            type_hint: Type hint supplied as TypeExpression for this operation.

        Returns:
            Call produced by this operation.

        """
        cast_func: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="cast",
            ),
            use=ImportUseSite.runtime(owner="cast"),
        )
        type_hint_text: str = self._renderer.render(value=type_hint)
        return Call(
            func=cast_func,
            args=[Constant(value=type_hint_text), target],
            keywords=[],
        )


class OverloadExpressionFactory:
    """Build semantic ``typing.overload`` decorated function stubs."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the factory.

        Args:
            imports: Imports supplied as UsageAwareImportCollector for this
                operation.

        """
        self._imports: UsageAwareImportCollector = imports

    def overload_stub(
        self,
        *,
        function_name: str,
        parameters: tuple[ArgumentSpec, ...],
        return_type: TypeExpression,
        docstring: str | None = None,
    ) -> FunctionDef:
        """Return an @overload decorated function stub as an AST node.

        The overload decorator is a type-checking import.


        Args:
            docstring: Docstring supplied as str | None for this operation.
            function_name: Identifier of the function being resolved.
            parameters: Collection of parameters supplied for this operation.
            return_type: Return type supplied as TypeExpression for this
                operation.

        Returns:
            FunctionDef produced by this operation.

        """
        overload_decorator: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="overload",
            ),
            use=ImportUseSite.annotation(owner="overload"),
        )
        body: list[stmt] = []
        if docstring:
            body.append(Expr(value=Constant(value=docstring)))
        body.append(Expr(value=Constant(value=...)))
        args_builder: AstArgsBuilder = AstArgsBuilder(
            resolver=TypeExpressionResolver(imports=self._imports),
        )
        ast_args: ast_arguments = args_builder.build(arguments=parameters)
        resolver: TypeExpressionResolver = TypeExpressionResolver(
            imports=self._imports,
        )
        return_ast: expr = return_type.to_ast(
            resolver=resolver,
            _use=ImportUseSite.annotation(owner=function_name),
        )
        return FunctionDef(
            name=function_name,
            args=ast_args,
            body=body,
            decorator_list=[overload_decorator],
            returns=return_ast,
        )


class ProtocolNodeBuilder:
    """Build AST nodes for TypeVars, ParamSpecs, and Protocol classes."""

    def __init__(
        self,
        *,
        imports: UsageAwareImportCollector,
        resolver: TypeExpressionResolver,
    ) -> None:
        """Initialize the node builder.

        Args:
            imports: Imports supplied as UsageAwareImportCollector for this
                operation.
            resolver: Callable used to resolver the requested information.

        """
        self._imports: UsageAwareImportCollector = imports
        self._resolver: TypeExpressionResolver = resolver
        self._parameters: ParameterNormalizer = ParameterNormalizer()
        self._validator: IdentifierValidator = IdentifierValidator()

    def typevar(self, *, spec: TypeVarSpec) -> Assign:
        """Build a TypeVar assignment.

        Args:
            spec: Spec supplied as TypeVarSpec for this operation.

        Returns:
            Assign produced by this operation.

        """
        typevar_func: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="TypeVar",
            ),
            use=ImportUseSite.typevar_declaration(owner=spec.name),
        )
        args: list[expr] = []
        keywords: list[ast_keyword] = []
        if spec.signature.constraints:
            args.append(Constant(value=spec.name))
        else:
            keywords.append(
                ast_keyword(arg="name", value=Constant(value=spec.name)),
            )
        self._append_typevar_keywords(spec=spec, keywords=keywords)
        args.extend(
            self._resolver.typevar_constraint(value=constraint)
            for constraint in spec.signature.constraints
        )
        return Assign(
            targets=[Name(id=spec.name, ctx=Store())],
            value=Call(func=typevar_func, args=args, keywords=keywords),
            type_comment=None,
        )

    def paramspec(self, *, spec: ParamSpecSpec) -> Assign:
        """Build a ParamSpec assignment.

        Args:
            spec: Spec supplied as ParamSpecSpec for this operation.

        Returns:
            Assign produced by this operation.

        """
        paramspec_func: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="ParamSpec",
            ),
            use=ImportUseSite.paramspec_declaration(owner=spec.name),
        )
        keywords: list[ast_keyword] = [
            ast_keyword(arg="name", value=Constant(value=spec.name)),
        ]
        if spec.signature.bound is not None:
            keywords.append(
                ast_keyword(
                    arg="bound",
                    value=self._resolver.typevar_bound(
                        value=spec.signature.bound,
                    ),
                ),
            )
        if spec.signature.covariant:
            keywords.append(
                ast_keyword(arg="covariant", value=Constant(value=True)),
            )
        if spec.signature.contravariant:
            keywords.append(
                ast_keyword(arg="contravariant", value=Constant(value=True)),
            )
        return Assign(
            targets=[Name(id=spec.name, ctx=Store())],
            value=Call(func=paramspec_func, args=[], keywords=keywords),
            type_comment=None,
        )

    def protocol(self, *, spec: ProtocolSpec) -> ClassDef:
        """Build a Protocol class definition.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            ClassDef produced by this operation.

        """
        if spec.name is None:
            msg: str = "Protocol name must be inferred before building."
            fail(message=msg)
        self._validator.validate_identifier(name=spec.name, label="protocol")
        body: list[stmt] = [Expr(value=Constant(value=spec.docstring or ""))]
        body.extend(self.method(spec=method) for method in spec.methods)
        bases: list[expr] = self._protocol_bases(spec=spec)
        return ClassDef(
            name=spec.name,
            bases=bases,
            keywords=[],
            body=body,
            decorator_list=list(spec.decorators),
            type_params=[],
        )

    def method(self, *, spec: MethodSpec) -> FunctionDef:
        """Build one protocol method definition.

        Args:
            spec: Spec supplied as MethodSpec for this operation.

        Returns:
            FunctionDef produced by this operation.

        """
        method_body: list[stmt] = [
            Expr(value=Constant(value=spec.docstring or "")),
        ]
        if spec.body is not None and spec.body:
            method_body.extend(spec.body)
        elif self._is_magic_method(name=spec.name):
            return_stmt: stmt | None = self._generate_magic_method_return(
                spec=spec,
            )
            if return_stmt is not None:
                method_body.append(return_stmt)
            else:
                method_body.append(Expr(value=Constant(value=Ellipsis)))
        else:
            method_body.append(Expr(value=Constant(value=Ellipsis)))
        type_params_list: list[type_param] = []
        if spec.type_params:
            type_params_list = self._build_type_params(spec=spec.type_params)
        return FunctionDef(
            name=spec.name,
            args=self.arguments(items=spec.arguments),
            body=method_body,
            decorator_list=list(spec.decorators),
            returns=self._resolver.annotation(value=spec.returns),
            type_comment=None,
            type_params=type_params_list,
        )

    def arguments(self, *, items: tuple[ArgumentItem, ...]) -> ast_arguments:
        """Build ``ast.arguments`` from semantic argument items.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            ast_arguments produced by this operation.

        """
        normalized: tuple[ArgumentSpec, ...] = self._parameters.normalize(
            items=items,
        )
        self._validate_unique_argument_names(arguments=normalized)
        builder: AstArgsBuilder = AstArgsBuilder(resolver=self._resolver)
        return builder.build(arguments=normalized)

    @staticmethod
    def _is_magic_method(*, name: str) -> bool:
        """Check if method name is a magic (dunder) method.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            Whether the requested condition holds.

        """
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def _generate_magic_method_return(*, spec: MethodSpec) -> stmt | None:
        """Generate return statement for known magic methods.

        Args:
            spec: Spec supplied as MethodSpec for this operation.

        Returns:
            stmt | None produced by this operation.

        """
        binary_ops: dict[str, type] = {
            "__add__": Add,
            "__sub__": Sub,
            "__mul__": Mult,
            "__truediv__": Div,
            "__floordiv__": FloorDiv,
            "__mod__": Mod,
        }
        if spec.name in binary_ops:
            return Return(
                value=BinOp(
                    left=Name(id="self", ctx=Load()),
                    op=binary_ops[spec.name](),
                    right=Name(id="other", ctx=Load()),
                ),
            )
        return None

    @staticmethod
    def _validate_unique_argument_names(
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> None:
        """Validate unique argument names.

        Args:
            arguments: Collection of arguments supplied for this operation.

        """
        names: set[str] = set()
        for argument in arguments:
            if argument.name in names:
                msg: str = f"Duplicate argument name: {argument.name!r}."
                fail(message=msg)
            names.add(argument.name)

    def _build_type_params(
        self,
        *,
        spec: tuple[TypeVarSpec | ParamSpecSpec, ...],
    ) -> list[type_param]:
        """Build AST type parameters from specs.

        Args:
            spec: Spec supplied as tuple[TypeVarSpec | ParamSpecSpec, ...] for
                this operation.

        Returns:
            list[type_param] produced by this operation.

        """
        result: list[type_param] = []
        for tp in spec:
            if hasattr(tp.signature, "constraints"):
                bound_expr: expr | None = None
                if tp.signature.bound is not None:
                    bound_expr = tp.signature.bound.to_ast(
                        resolver=self._resolver,
                        _use=ImportUseSite.typevar_bound(),
                    )
                result.append(
                    TypeVar(
                        name=tp.name,
                        bound=bound_expr,
                        default_value=None,
                    ),
                )
            else:
                result.append(ParamSpec(name=tp.name, default_value=None))
        return result

    def _protocol_bases(self, *, spec: ProtocolSpec) -> list[expr]:
        """Return protocol base expressions.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            list[expr] produced by this operation.

        """
        if spec.bases:
            return [
                self._resolver.protocol_base(value=base) for base in spec.bases
            ]
        protocol_node: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Protocol",
            ),
            use=ImportUseSite.protocol_base(owner=spec.name),
        )
        return [protocol_node]

    def _append_typevar_keywords(
        self,
        *,
        spec: TypeVarSpec,
        keywords: list[ast_keyword],
    ) -> None:
        """Append TypeVar keyword arguments.

        Args:
            keywords: Keywords supplied as list[ast_keyword] for this
                operation.
            spec: Spec supplied as TypeVarSpec for this operation.

        """
        if spec.signature.bound is not None:
            keywords.append(
                ast_keyword(
                    arg="bound",
                    value=self._resolver.typevar_bound(
                        value=spec.signature.bound,
                    ),
                ),
            )
        if spec.signature.covariant:
            keywords.append(
                ast_keyword(arg="covariant", value=Constant(value=True)),
            )
        if spec.signature.contravariant:
            keywords.append(
                ast_keyword(arg="contravariant", value=Constant(value=True)),
            )


class AstArgsBuilder:
    """Build AST argument lists from normalized semantic arguments."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the builder.

        Args:
            resolver: Callable used to resolver the requested information.

        """
        self._resolver: TypeExpressionResolver = resolver

    def build(self, *, arguments: tuple[ArgumentSpec, ...]) -> ast_arguments:
        """Build an ``ast.arguments`` node.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            ast_arguments produced by this operation.

        """
        groups: AstArgumentGroups = self._split(arguments=arguments)
        defaults: list[expr] = self._positional_defaults(
            arguments=tuple(groups.positional_specs),
        )
        return ast_arguments(
            posonlyargs=groups.posonlyargs,
            args=groups.args,
            vararg=groups.vararg,
            kwonlyargs=groups.kwonlyargs,
            kw_defaults=groups.kw_defaults,
            kwarg=groups.kwarg,
            defaults=defaults,
        )

    @staticmethod
    def _positional_defaults(
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> list[expr]:
        """Build positional defaults while enforcing Python ordering.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            list[expr] produced by this operation.

        """
        defaults: list[expr] = []
        default_started: bool = False
        for argument in arguments:
            if argument.default is None:
                if default_started:
                    msg: str = (
                        "Non-default positional arguments cannot follow "
                        "default positional arguments."
                    )
                    fail(message=msg)
                continue
            default_started = True
            defaults.append(argument.default)
        return defaults

    def _split(
        self,
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> AstArgumentGroups:
        """Split semantic arguments into AST argument groups.

        Args:
            arguments: Collection of arguments supplied for this operation.

        Returns:
            AstArgumentGroups produced by this operation.

        """
        groups: AstArgumentGroups = AstArgumentGroups()
        for argument in arguments:
            node: arg = self._node(argument=argument)
            groups.add(argument=argument, node=node)
        return groups

    def _node(self, *, argument: ArgumentSpec) -> arg:
        """Build one annotated AST argument.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.

        Returns:
            arg produced by this operation.

        """
        return arg(
            arg=argument.name,
            annotation=self._resolver.annotation(value=argument.type_hint),
            type_comment=None,
        )


@dataclass(slots=True)
class AstArgumentGroups:
    """Intermediate AST argument groups.

    Attributes:
        args: Args retained as list[arg] by this instance.
        kw_defaults: Kw defaults retained as list[expr | None] by this
            instance.
        kwarg: Kwarg retained as arg | None by this instance.
        kwonlyargs: Kwonlyargs retained as list[arg] by this instance.
        positional_specs: Positional specs retained as list[ArgumentSpec] by
            this instance.
        posonlyargs: Posonlyargs retained as list[arg] by this instance.
        vararg: Vararg retained as arg | None by this instance.

    """

    posonlyargs: list[arg] = field(default_factory=list)
    args: list[arg] = field(default_factory=list)
    kwonlyargs: list[arg] = field(default_factory=list)
    kw_defaults: list[expr | None] = field(default_factory=list)
    positional_specs: list[ArgumentSpec] = field(default_factory=list)
    vararg: arg | None = None
    kwarg: arg | None = None

    def add(self, *, argument: ArgumentSpec, node: arg) -> None:
        """Add one argument to the correct AST group.

        Args:
            argument: Argument supplied as ArgumentSpec for this operation.
            node: The node examined while add one argument to the correct AST
                group.

        """
        if argument.kind == "positional_only":
            self.posonlyargs.append(node)
            self.positional_specs.append(argument)
        elif argument.kind == "positional_or_keyword":
            self.args.append(node)
            self.positional_specs.append(argument)
        elif argument.kind == "keyword_only":
            self.kwonlyargs.append(node)
            self.kw_defaults.append(argument.default)
        elif argument.kind == "vararg":
            self.vararg = self._single(
                current=self.vararg,
                value=node,
                label="*args",
            )
        elif argument.kind == "kwarg":
            self.kwarg = self._single(
                current=self.kwarg,
                value=node,
                label="**kwargs",
            )

    @staticmethod
    def _single(*, current: arg | None, value: arg, label: str) -> arg:
        """Validate singleton argument slots.

        Args:
            current: Current supplied as arg | None for this operation.
            label: Label supplied as str for this operation.
            value: The value examined while validate singleton argument slots.

        Returns:
            arg produced by this operation.

        """
        if current is not None:
            msg: str = f"Only one {label} argument is allowed."
            fail(message=msg)
        return value


class ProtocolTypeBlockCollector:
    """Collect TypeVars, ParamSpecs, Protocols, and cast expressions."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the collector.

        Args:
            existing_nodes: Existing nodes supplied as
                Iterable[ExistingTopNode] for this operation.
            local_roots: Local roots supplied as Iterable[str] for this
                operation.
            postponed_annotations: Postponed annotations supplied as bool |
                None for this operation.

        """
        context: ExistingNodeContext = ExistingNodeContext.from_nodes(
            nodes=existing_nodes,
        )
        self._symbols: ScriptSymbolIndex = ScriptSymbolIndex.from_context(
            context=context,
        )
        self._existing_protocols: ExistingProtocolIndex = (
            ExistingProtocolIndex.from_context(context=context)
        )
        self._imports: UsageAwareImportCollector = UsageAwareImportCollector(
            symbol_index=self._symbols,
            existing_import_nodes=context.import_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self._resolver: TypeExpressionResolver = TypeExpressionResolver(
            imports=self._imports,
        )
        self._renderer: TypeHintStringRenderer = TypeHintStringRenderer(
            imports=self._imports,
        )
        self._node_builder: ProtocolNodeBuilder = ProtocolNodeBuilder(
            imports=self._imports,
            resolver=self._resolver,
        )
        self._name_registry: TypeParameterNameRegistry = (
            TypeParameterNameRegistry()
        )
        self._grammar: ProtocolGrammar = ProtocolGrammar()
        self._validator: IdentifierValidator = IdentifierValidator()
        self._typevars: list[TypeVarSpec] = []
        self._paramspecs: list[ParamSpecSpec] = []
        self._protocol_nodes: list[ClassDef] = []
        self.casts: CastExpressionFactory = CastExpressionFactory(
            imports=self._imports,
            renderer=self._renderer,
        )

    @staticmethod
    def render_nodes(*, nodes: Iterable[stmt]) -> str:
        """Render generated nodes to source for diagnostics.

        Args:
            nodes: Collection of nodes supplied for this operation.

        Returns:
            Rendered source text produced by this operation.

        """
        module: Module = Module(body=list(nodes), type_ignores=[])
        fixed_module: Module = fix_missing_locations(node=module)
        return unparse(ast_obj=fixed_module)

    def typevar(
        self,
        *,
        name: str | None = None,
        bound: TypeExpression | None = None,
        constraints: tuple[TypeExpression, ...] = (),
        covariant: bool = False,
        contravariant: bool = False,
    ) -> TypeVarSpec:
        """Create and collect a TypeVar spec.

        Args:
            bound: Bound supplied as TypeExpression | None for this operation.
            constraints: Constraints supplied as tuple[TypeExpression, ...] for
                this operation.
            contravariant: Contravariant supplied as bool for this operation.
            covariant: Covariant supplied as bool for this operation.
            name: Identifier of the name being resolved.

        Returns:
            TypeVarSpec produced by this operation.

        """
        if bound is not None and constraints:
            msg: str = "TypeVar cannot have both bound and constraints."
            fail(message=msg)
        signature: TypeVarSignature = TypeVarSignature(
            bound=bound,
            constraints=constraints,
            covariant=covariant,
            contravariant=contravariant,
        )
        key: str = self._typevar_key(signature=signature)
        resolved_name: str = self._name_registry.typevar_name(
            key=key,
            name=name,
        )
        self._validator.validate_identifier(
            name=resolved_name,
            label="TypeVar",
        )
        self._imports.reserve_generated_name(name=resolved_name)
        spec: TypeVarSpec = TypeVarSpec(
            name=resolved_name,
            signature=signature,
        )
        if spec not in self._typevars:
            self._typevars.append(spec)
        return spec

    def paramspec(
        self,
        *,
        name: str | None = None,
        bound: TypeExpression | None = None,
        covariant: bool = False,
        contravariant: bool = False,
    ) -> ParamSpecSpec:
        """Create and collect a ParamSpec spec.

        Args:
            bound: Bound supplied as TypeExpression | None for this operation.
            contravariant: Contravariant supplied as bool for this operation.
            covariant: Covariant supplied as bool for this operation.
            name: Identifier of the name being resolved.

        Returns:
            ParamSpecSpec produced by this operation.

        """
        signature: ParamSpecSignature = ParamSpecSignature(
            bound=bound,
            covariant=covariant,
            contravariant=contravariant,
        )
        key: str = self._paramspec_key(signature=signature)
        resolved_name: str = self._name_registry.paramspec_name(
            key=key,
            name=name,
        )
        self._validator.validate_identifier(
            name=resolved_name,
            label="ParamSpec",
        )
        self._imports.reserve_generated_name(name=resolved_name)
        spec: ParamSpecSpec = ParamSpecSpec(
            name=resolved_name,
            signature=signature,
        )
        if spec not in self._paramspecs:
            self._paramspecs.append(spec)
        return spec

    def protocol(self, *, spec: ProtocolSpec) -> ProtocolRegistration:
        """Register a protocol or return an equivalent existing protocol.

        Args:
            spec: Spec supplied as ProtocolSpec for this operation.

        Returns:
            ProtocolRegistration produced by this operation.

        """
        inferred_spec: ProtocolSpec = self._grammar.infer(spec=spec)
        if inferred_spec.name is None:
            msg: str = "Protocol name inference failed."
            fail(message=msg)
        by_name: ClassDef | None = self._existing_protocols.find_by_name(
            name=inferred_spec.name,
        )
        if by_name is not None:
            return ProtocolRegistration(
                spec=inferred_spec,
                class_node=by_name,
                is_existing=True,
                match_reason="name",
            )
        by_shape: ClassDef | None = self._existing_protocols.find_by_shape(
            spec=inferred_spec,
        )
        if by_shape is not None:
            return ProtocolRegistration(
                spec=inferred_spec,
                class_node=by_shape,
                is_existing=True,
                match_reason="shape",
            )
        self._imports.reserve_generated_name(name=inferred_spec.name)
        class_node: ClassDef = self._node_builder.protocol(spec=inferred_spec)
        self._protocol_nodes.append(class_node)
        return ProtocolRegistration(
            spec=inferred_spec,
            class_node=class_node,
            is_existing=False,
            match_reason="new",
        )

    def build_block(self) -> GeneratedTopBlock:
        """Build imports and declarations ready for top insertion.

        Returns:
            GeneratedTopBlock produced by this operation.

        """
        declarations: list[stmt] = []
        declarations.extend(
            self._node_builder.typevar(spec=item) for item in self._typevars
        )
        declarations.extend(
            self._node_builder.paramspec(spec=item)
            for item in self._paramspecs
        )
        declarations.extend(self._protocol_nodes)
        return GeneratedTopBlock(
            missing_import_nodes=self._imports.import_nodes(),
            declaration_nodes_after_imports=tuple(declarations),
        )

    @staticmethod
    def _typevar_key(*, signature: TypeVarSignature) -> str:
        """Return a stable semantic key for a TypeVar signature.

        Args:
            signature: Signature supplied as TypeVarSignature for this
                operation.

        Returns:
            str produced by this operation.

        """
        constraints: str = ",".join(
            item.key() for item in signature.constraints
        )
        bound: str = (
            signature.bound.key() if signature.bound is not None else "None"
        )
        return (
            f"bound="
            f"{bound}"
            f";constraints="
            f"{constraints}"
            f";covariant="
            f"{signature.covariant}"
            f";contravariant="
            f"{signature.contravariant}"
        )

    @staticmethod
    def _paramspec_key(*, signature: ParamSpecSignature) -> str:
        """Return a stable semantic key for a ParamSpec signature.

        Args:
            signature: Signature supplied as ParamSpecSignature for this
                operation.

        Returns:
            str produced by this operation.

        """
        bound: str = (
            signature.bound.key() if signature.bound is not None else "None"
        )
        return (
            f"bound="
            f"{bound}"
            f";covariant="
            f"{signature.covariant}"
            f";contravariant="
            f"{signature.contravariant}"
        )


@dataclass(slots=True, frozen=True)
class EmptyTupleTypeRef(TypeExpression):
    """Semantic representation of ``tuple[()]``."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the AST node for ``tuple[()]``.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        tuple_node: expr = BuiltinTypeRef(name="tuple").to_ast(
            resolver=resolver,
            _use=_use,
        )
        return Subscript(
            value=tuple_node,
            slice=AstTuple(elts=[], ctx=Load()),
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``tuple[()]``.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        _ = renderer
        return "tuple[()]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        return "builtins:tuple[()]"


@dataclass(slots=True, frozen=True)
class ConcatenateTypeRef(TypeExpression):
    """Semantic representation of ``typing.Concatenate``.

    Attributes:
        params: Params retained as TypeExpression by this instance.
        prefix: Prefix retained as tuple[TypeExpression, ...] by this instance.

    """

    prefix: tuple[TypeExpression, ...]
    params: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a subscripted ``Concatenate`` AST expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        origin_node: expr = ImportedTypeRef.absolute(
            module_parts=("typing",),
            name="Concatenate",
        ).to_ast(resolver=resolver, _use=_use)
        argument_nodes: tuple[expr, ...] = tuple(
            item.to_ast(resolver=resolver, _use=_use) for item in self.prefix
        )
        params_node: expr = self.params.to_ast(resolver=resolver, _use=_use)
        return AstExpressionBuilder.subscript(
            value=origin_node,
            args=(*argument_nodes, params_node),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a ``Concatenate`` expression.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        origin_text: str = ImportedTypeRef.absolute(
            module_parts=("typing",),
            name="Concatenate",
        ).render(renderer=renderer)
        prefix_text: str = ", ".join(
            item.render(renderer=renderer) for item in self.prefix
        )
        params_text: str = self.params.render(renderer=renderer)
        return f"{origin_text}[{prefix_text}, {params_text}]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        prefix_key: str = ",".join(item.key() for item in self.prefix)
        return f"typing:Concatenate[{prefix_key},{self.params.key()}]"

    def __post_init__(self) -> None:
        """Validate that Concatenate has at least one prefix type."""
        if not self.prefix:
            fail(message="Concatenate requires at least one prefix type.")


type CallableParameterSpec = TypeExpression | tuple[TypeExpression, ...] | None


@dataclass(slots=True, frozen=True)
class FlexibleCallableTypeRef(TypeExpression):
    """Semantic representation of all canonical ``Callable`` forms.

    Attributes:
        parameters: Parameters retained as CallableParameterSpec by this
            instance.
        returns: Returns retained as TypeExpression by this instance.

    """

    parameters: CallableParameterSpec
    returns: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a canonical ``collections.abc.Callable`` AST expression.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        callable_node: expr = ImportedTypeRef.absolute(
            module_parts=("collections", "abc"),
            name="Callable",
        ).to_ast(resolver=resolver, _use=_use)
        parameter_node: expr = self._parameter_node(
            resolver=resolver,
            _use=_use,
        )
        returns_node: expr = self.returns.to_ast(resolver=resolver, _use=_use)
        return AstExpressionBuilder.subscript(
            value=callable_node,
            args=(parameter_node, returns_node),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a canonical callable expression.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        callable_name: str = ImportedTypeRef.absolute(
            module_parts=("collections", "abc"),
            name="Callable",
        ).render(renderer=renderer)
        parameters_text: str = self._parameters_text(renderer=renderer)
        returns_text: str = self.returns.render(renderer=renderer)
        return f"{callable_name}[{parameters_text}, {returns_text}]"

    def key(self) -> str:
        """Return a stable semantic key.

        Returns:
            str produced by this operation.

        """
        parameter_key: str = self._parameter_key()
        return (
            f"collections.abc:Callable[{parameter_key},{self.returns.key()}]"
        )

    def _parameter_node(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the callable parameter AST node.

        Args:
            _use: Use supplied as ImportUseSite for this operation.
            resolver: Callable used to resolver the requested information.

        Returns:
            expr produced by this operation.

        """
        if self.parameters is None:
            return Constant(value=Ellipsis)
        if isinstance(self.parameters, tuple):
            return AstList(
                elts=[
                    item.to_ast(resolver=resolver, _use=_use)
                    for item in self.parameters
                ],
                ctx=Load(),
            )
        return self.parameters.to_ast(resolver=resolver, _use=_use)

    def _parameters_text(self, *, renderer: TypeHintStringRenderer) -> str:
        """Return callable parameter text.

        Args:
            renderer: Renderer supplied as TypeHintStringRenderer for this
                operation.

        Returns:
            str produced by this operation.

        """
        if self.parameters is None:
            return "..."
        if isinstance(self.parameters, tuple):
            inner_text: str = ", ".join(
                item.render(renderer=renderer) for item in self.parameters
            )
            return f"[{inner_text}]"
        return self.parameters.render(renderer=renderer)

    def _parameter_key(self) -> str:
        """Return callable parameter key text.

        Returns:
            str produced by this operation.

        """
        if self.parameters is None:
            return "..."
        if isinstance(self.parameters, tuple):
            return "[" + ",".join(item.key() for item in self.parameters) + "]"
        return self.parameters.key()


class DirectTypeRefs:
    """Direct, unsubscripted type-expression references."""

    @staticmethod
    def builtin(*, name: str) -> BuiltinTypeRef:
        """Return a direct builtin type reference.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            BuiltinTypeRef produced by this operation.

        """
        return BuiltinTypeRef(name=name)

    @staticmethod
    def imported(
        *,
        module_parts: tuple[str, ...],
        name: str,
    ) -> ImportedTypeRef:
        """Return a direct imported type reference.

        Args:
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.

        Returns:
            ImportedTypeRef produced by this operation.

        """
        return ImportedTypeRef.absolute(module_parts=module_parts, name=name)


class BuiltinTypeHints:
    """Canonical builtin direct references and generic templates.

    Attributes:
        BOOL: Bool retained as Final[BuiltinTypeRef] by this instance.
        BYTEARRAY: Bytearray retained as Final[BuiltinTypeRef] by this
            instance.
        BYTES: Bytes retained as Final[BuiltinTypeRef] by this instance.
        COMPLEX: Complex retained as Final[BuiltinTypeRef] by this instance.
        DICT: Dict retained as Final[TypeTemplateRef] by this instance.
        ELLIPSIS_OBJECT: Ellipsis object retained as Final[BuiltinTypeRef] by
            this instance.
        FLOAT: Float retained as Final[BuiltinTypeRef] by this instance.
        FROZENSET: Frozenset retained as Final[TypeTemplateRef] by this
            instance.
        INT: Int retained as Final[BuiltinTypeRef] by this instance.
        LIST: List retained as Final[TypeTemplateRef] by this instance.
        MEMORYVIEW: Memoryview retained as Final[BuiltinTypeRef] by this
            instance.
        NONE: None retained as Final[BuiltinTypeRef] by this instance.
        OBJECT: Object retained as Final[BuiltinTypeRef] by this instance.
        RANGE: Range retained as Final[BuiltinTypeRef] by this instance.
        SET: Set retained as Final[TypeTemplateRef] by this instance.
        SLICE: Slice retained as Final[BuiltinTypeRef] by this instance.
        STR: Str retained as Final[BuiltinTypeRef] by this instance.
        TUPLE: Tuple retained as Final[TypeTemplateRef] by this instance.
        TYPE: Type retained as Final[TypeTemplateRef] by this instance.
        TYPE_DIRECT: Type direct retained as Final[BuiltinTypeRef] by this
            instance.

    """

    NONE: Final[BuiltinTypeRef] = BuiltinTypeRef(name="None")
    BOOL: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bool")
    INT: Final[BuiltinTypeRef] = BuiltinTypeRef(name="int")
    FLOAT: Final[BuiltinTypeRef] = BuiltinTypeRef(name="float")
    COMPLEX: Final[BuiltinTypeRef] = BuiltinTypeRef(name="complex")
    STR: Final[BuiltinTypeRef] = BuiltinTypeRef(name="str")
    BYTES: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bytes")
    BYTEARRAY: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bytearray")
    MEMORYVIEW: Final[BuiltinTypeRef] = BuiltinTypeRef(name="memoryview")
    OBJECT: Final[BuiltinTypeRef] = BuiltinTypeRef(name="object")
    TYPE_DIRECT: Final[BuiltinTypeRef] = BuiltinTypeRef(name="type")
    SLICE: Final[BuiltinTypeRef] = BuiltinTypeRef(name="slice")
    RANGE: Final[BuiltinTypeRef] = BuiltinTypeRef(name="range")
    ELLIPSIS_OBJECT: Final[BuiltinTypeRef] = BuiltinTypeRef(name="Ellipsis")
    LIST: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="list"),
        label="list",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    TUPLE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="tuple"),
        label="tuple",
        min_args=1,
        max_args=None,
        allow_empty=True,
    )
    DICT: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="dict"),
        label="dict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    SET: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="set"),
        label="set",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    FROZENSET: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="frozenset"),
        label="frozenset",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    TYPE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="type"),
        label="type",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )

    @classmethod
    def list_of(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``list[item]``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.LIST.of(arguments=(item,))

    @classmethod
    def tuple_variadic(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``tuple[item, ...]``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.TUPLE.of(arguments=(item, EllipsisTypeRef()))

    @classmethod
    def tuple_of(cls, *, items: tuple[TypeExpression, ...]) -> TypeExpression:
        """Return fixed heterogeneous ``tuple[...]``.

        Args:
            items: Collection of items supplied for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.TUPLE.of(arguments=items)

    @classmethod
    def dict_of(
        cls,
        *,
        keys: TypeExpression,
        values: TypeExpression,
    ) -> TypeExpression:
        """Return ``dict[keys, values]``.

        Args:
            keys: Keys supplied as TypeExpression for this operation.
            values: Values supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.DICT.of(arguments=(keys, values))

    @classmethod
    def set_of(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``set[item]``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.SET.of(arguments=(item,))

    @classmethod
    def frozenset_of(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``frozenset[item]``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.FROZENSET.of(arguments=(item,))

    @classmethod
    def type_of(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``type[item]``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.TYPE.of(arguments=(item,))

    @staticmethod
    def tuple_empty() -> EmptyTupleTypeRef:
        """Return ``tuple[()]``.

        Returns:
            EmptyTupleTypeRef produced by this operation.

        """
        return EmptyTupleTypeRef()


class TypesModuleTypeHints:
    """Direct runtime type references from the ``types`` module.

    Attributes:
        ASYNC_GENERATOR_TYPE: Async generator type retained as
            Final[ImportedTypeRef] by this instance.
        BUILTIN_FUNCTION_TYPE: Builtin function type retained as
            Final[ImportedTypeRef] by this instance.
        BUILTIN_METHOD_TYPE: Builtin method type retained as
            Final[ImportedTypeRef] by this instance.
        CELL_TYPE: Cell type retained as Final[ImportedTypeRef] by this
            instance.
        CODE_TYPE: Code type retained as Final[ImportedTypeRef] by this
            instance.
        COROUTINE_TYPE: Coroutine type retained as Final[ImportedTypeRef] by
            this instance.
        ELLIPSIS_TYPE: Ellipsis type retained as Final[ImportedTypeRef] by this
            instance.
        FRAME_TYPE: Frame type retained as Final[ImportedTypeRef] by this
            instance.
        FUNCTION_TYPE: Function type retained as Final[ImportedTypeRef] by this
            instance.
        GENERATOR_TYPE: Generator type retained as Final[ImportedTypeRef] by
            this instance.
        GENERIC_ALIAS: Generic alias retained as Final[ImportedTypeRef] by this
            instance.
        GET_SET_DESCRIPTOR_TYPE: Get set descriptor type retained as
            Final[ImportedTypeRef] by this instance.
        LAMBDA_TYPE: Lambda type retained as Final[ImportedTypeRef] by this
            instance.
        MAPPING_PROXY_TYPE: Mapping proxy type retained as
            Final[ImportedTypeRef] by this instance.
        MEMBER_DESCRIPTOR_TYPE: Member descriptor type retained as
            Final[ImportedTypeRef] by this instance.
        METHOD_DESCRIPTOR_TYPE: Method descriptor type retained as
            Final[ImportedTypeRef] by this instance.
        METHOD_TYPE: Method type retained as Final[ImportedTypeRef] by this
            instance.
        METHOD_WRAPPER_TYPE: Method wrapper type retained as
            Final[ImportedTypeRef] by this instance.
        MODULE_TYPE: Module type retained as Final[ImportedTypeRef] by this
            instance.
        NONE_TYPE: None type retained as Final[ImportedTypeRef] by this
            instance.
        NOT_IMPLEMENTED_TYPE: Not implemented type retained as
            Final[ImportedTypeRef] by this instance.
        SIMPLE_NAMESPACE: Simple namespace retained as Final[ImportedTypeRef]
            by this instance.
        TRACEBACK_TYPE: Traceback type retained as Final[ImportedTypeRef] by
            this instance.
        UNION_TYPE: Union type retained as Final[ImportedTypeRef] by this
            instance.

    """

    ASYNC_GENERATOR_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="AsyncGeneratorType",
    )
    BUILTIN_FUNCTION_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="BuiltinFunctionType",
    )
    BUILTIN_METHOD_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="BuiltinMethodType",
    )
    CELL_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CellType",
    )
    CODE_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CodeType",
    )
    COROUTINE_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CoroutineType",
    )
    ELLIPSIS_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="EllipsisType",
    )
    FRAME_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="FrameType",
    )
    FUNCTION_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="FunctionType",
    )
    GENERATOR_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GeneratorType",
    )
    GENERIC_ALIAS: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GenericAlias",
    )
    GET_SET_DESCRIPTOR_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GetSetDescriptorType",
    )
    LAMBDA_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="LambdaType",
    )
    MAPPING_PROXY_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MappingProxyType",
    )
    MEMBER_DESCRIPTOR_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MemberDescriptorType",
    )
    METHOD_DESCRIPTOR_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodDescriptorType",
    )
    METHOD_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodType",
    )
    METHOD_WRAPPER_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodWrapperType",
    )
    MODULE_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="ModuleType",
    )
    NONE_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="NoneType",
    )
    NOT_IMPLEMENTED_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="NotImplementedType",
    )
    SIMPLE_NAMESPACE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="SimpleNamespace",
    )
    TRACEBACK_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="TracebackType",
    )
    UNION_TYPE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="UnionType",
    )


class CollectionsAbcTypeHints:
    """Canonical ``collections.abc`` direct refs and generic templates.

    Attributes:
        ASYNC_GENERATOR: Async generator retained as Final[TypeTemplateRef] by
            this instance.
        ASYNC_ITERABLE: Async iterable retained as Final[TypeTemplateRef] by
            this instance.
        ASYNC_ITERATOR: Async iterator retained as Final[TypeTemplateRef] by
            this instance.
        AWAITABLE: Awaitable retained as Final[TypeTemplateRef] by this
            instance.
        BYTE_STRING: Byte string retained as Final[ImportedTypeRef] by this
            instance.
        COLLECTION: Collection retained as Final[TypeTemplateRef] by this
            instance.
        CONTAINER: Container retained as Final[TypeTemplateRef] by this
            instance.
        COROUTINE: Coroutine retained as Final[TypeTemplateRef] by this
            instance.
        GENERATOR: Generator retained as Final[TypeTemplateRef] by this
            instance.
        HASHABLE: Hashable retained as Final[ImportedTypeRef] by this instance.
        ITEMS_VIEW: Items view retained as Final[TypeTemplateRef] by this
            instance.
        ITERABLE: Iterable retained as Final[TypeTemplateRef] by this instance.
        ITERATOR: Iterator retained as Final[TypeTemplateRef] by this instance.
        KEYS_VIEW: Keys view retained as Final[TypeTemplateRef] by this
            instance.
        MAPPING: Mapping retained as Final[TypeTemplateRef] by this instance.
        MAPPING_VIEW: Mapping view retained as Final[TypeTemplateRef] by this
            instance.
        MUTABLE_MAPPING: Mutable mapping retained as Final[TypeTemplateRef] by
            this instance.
        MUTABLE_SEQUENCE: Mutable sequence retained as Final[TypeTemplateRef]
            by this instance.
        MUTABLE_SET: Mutable set retained as Final[TypeTemplateRef] by this
            instance.
        REVERSIBLE: Reversible retained as Final[TypeTemplateRef] by this
            instance.
        SEQUENCE: Sequence retained as Final[TypeTemplateRef] by this instance.
        SET: Set retained as Final[TypeTemplateRef] by this instance.
        SIZED: Sized retained as Final[ImportedTypeRef] by this instance.
        VALUES_VIEW: Values view retained as Final[TypeTemplateRef] by this
            instance.

    """

    HASHABLE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="Hashable",
    )
    SIZED: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="Sized",
    )
    BYTE_STRING: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="ByteString",
    )
    AWAITABLE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Awaitable",
        ),
        label="Awaitable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ASYNC_ITERABLE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncIterable",
        ),
        label="AsyncIterable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ASYNC_ITERATOR: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncIterator",
        ),
        label="AsyncIterator",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ITERABLE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Iterable",
        ),
        label="Iterable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ITERATOR: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Iterator",
        ),
        label="Iterator",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    REVERSIBLE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Reversible",
        ),
        label="Reversible",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    CONTAINER: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Container",
        ),
        label="Container",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    COLLECTION: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Collection",
        ),
        label="Collection",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    SEQUENCE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Sequence",
        ),
        label="Sequence",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    MUTABLE_SEQUENCE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableSequence",
        ),
        label="MutableSequence",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    SET: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Set",
        ),
        label="Set",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    MUTABLE_SET: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableSet",
        ),
        label="MutableSet",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    MAPPING_VIEW: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MappingView",
        ),
        label="MappingView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    KEYS_VIEW: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="KeysView",
        ),
        label="KeysView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    VALUES_VIEW: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="ValuesView",
        ),
        label="ValuesView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ITEMS_VIEW: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="ItemsView",
        ),
        label="ItemsView",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    MAPPING: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Mapping",
        ),
        label="Mapping",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    MUTABLE_MAPPING: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableMapping",
        ),
        label="MutableMapping",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    ASYNC_GENERATOR: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncGenerator",
        ),
        label="AsyncGenerator",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    COROUTINE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Coroutine",
        ),
        label="Coroutine",
        min_args=3,
        max_args=3,
        allow_empty=True,
    )
    GENERATOR: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Generator",
        ),
        label="Generator",
        min_args=3,
        max_args=3,
        allow_empty=True,
    )

    @staticmethod
    def callable_of(
        *,
        parameters: CallableParameterSpec,
        returns: TypeExpression,
    ) -> FlexibleCallableTypeRef:
        """Return a canonical callable type expression.

        Args:
            parameters: Collection of parameters supplied for this operation.
            returns: Returns supplied as TypeExpression for this operation.

        Returns:
            FlexibleCallableTypeRef produced by this operation.

        """
        return FlexibleCallableTypeRef(parameters=parameters, returns=returns)

    @staticmethod
    def one_arg(
        *,
        template: TypeTemplateRef,
        item: TypeExpression,
    ) -> TypeExpression:
        """Apply a one-argument ABC template.

        Args:
            item: Item supplied as TypeExpression for this operation.
            template: Template supplied as TypeTemplateRef for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return template.of(arguments=(item,))

    @staticmethod
    def two_arg(
        *,
        template: TypeTemplateRef,
        first: TypeExpression,
        second: TypeExpression,
    ) -> TypeExpression:
        """Apply a two-argument ABC template.

        Args:
            first: First supplied as TypeExpression for this operation.
            second: Second supplied as TypeExpression for this operation.
            template: Template supplied as TypeTemplateRef for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return template.of(arguments=(first, second))

    @staticmethod
    def three_arg(
        *,
        template: TypeTemplateRef,
        first: TypeExpression,
        second: TypeExpression,
        third: TypeExpression,
    ) -> TypeExpression:
        """Apply a three-argument ABC template.

        Args:
            first: First supplied as TypeExpression for this operation.
            second: Second supplied as TypeExpression for this operation.
            template: Template supplied as TypeTemplateRef for this operation.
            third: Third supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return template.of(arguments=(first, second, third))


class CollectionsConcreteTypeHints:
    """Concrete generic collection classes from ``collections``.

    Attributes:
        CHAIN_MAP: Chain map retained as Final[TypeTemplateRef] by this
            instance.
        COUNTER: Counter retained as Final[TypeTemplateRef] by this instance.
        DEFAULTDICT: Defaultdict retained as Final[TypeTemplateRef] by this
            instance.
        DEQUE: Deque retained as Final[TypeTemplateRef] by this instance.
        ORDERED_DICT: Ordered dict retained as Final[TypeTemplateRef] by this
            instance.
        USER_DICT: User dict retained as Final[TypeTemplateRef] by this
            instance.
        USER_LIST: User list retained as Final[TypeTemplateRef] by this
            instance.
        USER_STRING: User string retained as Final[ImportedTypeRef] by this
            instance.

    """

    CHAIN_MAP: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="ChainMap",
        ),
        label="ChainMap",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    COUNTER: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="Counter",
        ),
        label="Counter",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ORDERED_DICT: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="OrderedDict",
        ),
        label="OrderedDict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    USER_DICT: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="UserDict",
        ),
        label="UserDict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    USER_LIST: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="UserList",
        ),
        label="UserList",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    USER_STRING: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections",),
        name="UserString",
    )
    DEFAULTDICT: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="defaultdict",
        ),
        label="defaultdict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    DEQUE: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="deque",
        ),
        label="deque",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


class TypingTypeHints:
    """Canonical direct special forms from ``typing``.

    Attributes:
        ANNOTATED: Annotated retained as Final[TypeTemplateRef] by this
            instance.
        BINARY_IO: Binary io retained as Final[ImportedTypeRef] by this
            instance.
        CLASSVAR: Classvar retained as Final[TypeTemplateRef] by this instance.
        FINAL: Final retained as Final[TypeTemplateRef] by this instance.
        GENERIC: Generic retained as Final[TypeTemplateRef] by this instance.
        IO: Io retained as Final[TypeTemplateRef] by this instance.
        LITERAL_STRING: Literal string retained as Final[ImportedTypeRef] by
            this instance.
        NEVER: Never retained as Final[ImportedTypeRef] by this instance.
        NOT_REQUIRED: Not required retained as Final[TypeTemplateRef] by this
            instance.
        NO_RETURN: No return retained as Final[ImportedTypeRef] by this
            instance.
        PARAM_SPEC: Param spec retained as Final[ImportedTypeRef] by this
            instance.
        PROTOCOL: Protocol retained as Final[TypeTemplateRef] by this instance.
        READ_ONLY: Read only retained as Final[TypeTemplateRef] by this
            instance.
        REQUIRED: Required retained as Final[TypeTemplateRef] by this instance.
        SELF: Self retained as Final[SelfTypeRef] by this instance.
        TEXT_IO: Text io retained as Final[ImportedTypeRef] by this instance.
        TYPED_DICT: Typed dict retained as Final[ImportedTypeRef] by this
            instance.
        TYPE_ALIAS: Type alias retained as Final[ImportedTypeRef] by this
            instance.
        TYPE_GUARD: Type guard retained as Final[TypeTemplateRef] by this
            instance.
        TYPE_IS: Type is retained as Final[TypeTemplateRef] by this instance.
        TYPE_VAR: Type var retained as Final[ImportedTypeRef] by this instance.
        TYPE_VAR_TUPLE: Type var tuple retained as Final[ImportedTypeRef] by
            this instance.
        UNPACK: Unpack retained as Final[TypeTemplateRef] by this instance.

    """

    SELF: Final[SelfTypeRef] = SelfTypeRef()
    LITERAL_STRING: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="LiteralString",
    )
    NEVER: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="Never",
    )
    NO_RETURN: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="NoReturn",
    )
    PARAM_SPEC: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="ParamSpec",
    )
    PROTOCOL: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Protocol",
        ),
        label="Protocol",
        min_args=0,
        max_args=None,
        allow_empty=True,
    )
    GENERIC: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Generic",
        ),
        label="Generic",
        min_args=1,
        max_args=None,
        allow_empty=True,
    )
    TYPE_ALIAS: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeAlias",
    )
    TYPE_VAR: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeVar",
    )
    TYPE_VAR_TUPLE: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeVarTuple",
    )
    TYPED_DICT: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypedDict",
    )
    CLASSVAR: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="ClassVar",
        ),
        label="ClassVar",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    FINAL: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("typing",), name="Final"),
        label="Final",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    REQUIRED: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Required",
        ),
        label="Required",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    NOT_REQUIRED: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="NotRequired",
        ),
        label="NotRequired",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    READ_ONLY: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="ReadOnly",
        ),
        label="ReadOnly",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    UNPACK: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Unpack",
        ),
        label="Unpack",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    TYPE_GUARD: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="TypeGuard",
        ),
        label="TypeGuard",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    TYPE_IS: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="TypeIs",
        ),
        label="TypeIs",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ANNOTATED: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Annotated",
        ),
        label="Annotated",
        min_args=2,
        max_args=None,
        allow_empty=False,
    )
    IO: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("typing",), name="IO"),
        label="IO",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    TEXT_IO: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TextIO",
    )
    BINARY_IO: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="BinaryIO",
    )

    @classmethod
    def noneable(cls, *, item: TypeExpression) -> TypeExpression:
        """Return ``item | None`` without using ``Optional``.

        Args:
            item: Item supplied as TypeExpression for this operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return cls.union_of(options=(item, BuiltinTypeHints.NONE))

    @staticmethod
    def literal_of(*, values: tuple[LiteralValue, ...]) -> LiteralTypeRef:
        """Return a ``Literal[...]`` expression.

        Args:
            values: Values supplied as tuple[LiteralValue, ...] for this
                operation.

        Returns:
            LiteralTypeRef produced by this operation.

        """
        if not values:
            fail(message="Literal requires at least one value.")
        return LiteralTypeRef(values=values)

    @staticmethod
    def union_of(
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Return a normalized modern PEP 604 union expression.

        Args:
            collapse_limit: Collapse limit supplied as int | None for this
                operation.
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        simplified_options: tuple[TypeExpression, ...] = (
            TypeUnionSimplifier().simplify(
                options=options,
                collapse_limit=collapse_limit,
            )
        )
        if len(simplified_options) == 1:
            return simplified_options[0]
        return UnionTypeRef(
            options=simplified_options,
            collapse_limit=collapse_limit,
        )

    @staticmethod
    def concatenate_of(
        *,
        prefix: tuple[TypeExpression, ...],
        params: TypeExpression,
    ) -> ConcatenateTypeRef:
        """Return a ``Concatenate[..., P]`` expression.

        Args:
            params: Params supplied as TypeExpression for this operation.
            prefix: Prefix supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            ConcatenateTypeRef produced by this operation.

        """
        return ConcatenateTypeRef(prefix=prefix, params=params)


class RegexTypeHints:
    """Canonical regular-expression type templates.

    Attributes:
        MATCH: Match retained as Final[TypeTemplateRef] by this instance.
        PATTERN: Pattern retained as Final[TypeTemplateRef] by this instance.

    """

    PATTERN: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("re",), name="Pattern"),
        label="Pattern",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    MATCH: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("re",), name="Match"),
        label="Match",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


class ContextManagerTypeHints:
    """Canonical context-manager type templates.

    Attributes:
        ABSTRACT_ASYNC_CONTEXT_MANAGER: Abstract async context manager retained
            as Final[TypeTemplateRef] by this instance.
        ABSTRACT_CONTEXT_MANAGER: Abstract context manager retained as
            Final[TypeTemplateRef] by this instance.

    """

    ABSTRACT_CONTEXT_MANAGER: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("contextlib",),
            name="AbstractContextManager",
        ),
        label="AbstractContextManager",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ABSTRACT_ASYNC_CONTEXT_MANAGER: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("contextlib",),
            name="AbstractAsyncContextManager",
        ),
        label="AbstractAsyncContextManager",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


class TypeParameterNames:
    """Common type-parameter names used inside annotations.

    Attributes:
        K: K retained as Final[LocalTypeRef] by this instance.
        P: P retained as Final[LocalTypeRef] by this instance.
        R: R retained as Final[LocalTypeRef] by this instance.
        T: T retained as Final[LocalTypeRef] by this instance.
        TS: Ts retained as Final[LocalTypeRef] by this instance.
        T_CO: T co retained as Final[LocalTypeRef] by this instance.
        T_CONTRA: T contra retained as Final[LocalTypeRef] by this instance.
        V: V retained as Final[LocalTypeRef] by this instance.

    """

    T: Final[LocalTypeRef] = LocalTypeRef(name="T")
    T_CO: Final[LocalTypeRef] = LocalTypeRef(name="T_co")
    T_CONTRA: Final[LocalTypeRef] = LocalTypeRef(name="T_contra")
    K: Final[LocalTypeRef] = LocalTypeRef(name="K")
    V: Final[LocalTypeRef] = LocalTypeRef(name="V")
    R: Final[LocalTypeRef] = LocalTypeRef(name="R")
    P: Final[LocalTypeRef] = LocalTypeRef(name="P")
    TS: Final[LocalTypeRef] = LocalTypeRef(name="Ts")


class TypeHintCatalog:
    """Flat direct-annotation catalog organized by canonical source.

    Attributes:
        ABC: Abc retained as Final[type[CollectionsAbcTypeHints]] by this
            instance.
        BUILTINS: Builtins retained as Final[type[BuiltinTypeHints]] by this
            instance.
        COLLECTIONS: Collections retained as
            Final[type[CollectionsConcreteTypeHints]] by this instance.
        CONTEXT: Context retained as Final[type[ContextManagerTypeHints]] by
            this instance.
        PARAMS: Params retained as Final[type[TypeParameterNames]] by this
            instance.
        REGEX: Regex retained as Final[type[RegexTypeHints]] by this instance.
        TYPES: Types retained as Final[type[TypesModuleTypeHints]] by this
            instance.
        TYPING: Typing retained as Final[type[TypingTypeHints]] by this
            instance.

    """

    BUILTINS: Final[type[BuiltinTypeHints]] = BuiltinTypeHints
    TYPES: Final[type[TypesModuleTypeHints]] = TypesModuleTypeHints
    ABC: Final[type[CollectionsAbcTypeHints]] = CollectionsAbcTypeHints
    COLLECTIONS: Final[type[CollectionsConcreteTypeHints]] = (
        CollectionsConcreteTypeHints
    )
    TYPING: Final[type[TypingTypeHints]] = TypingTypeHints
    REGEX: Final[type[RegexTypeHints]] = RegexTypeHints
    CONTEXT: Final[type[ContextManagerTypeHints]] = ContextManagerTypeHints
    PARAMS: Final[type[TypeParameterNames]] = TypeParameterNames


class Types:
    """Convenience facade for canonical semantic type expressions.

    Attributes:
        ABC: Abc retained as Final[type[CollectionsAbcTypeHints]] by this
            instance.
        BOOL: Bool retained as Final[BuiltinTypeRef] by this instance.
        BUILTINS: Builtins retained as Final[type[BuiltinTypeHints]] by this
            instance.
        BYTEARRAY: Bytearray retained as Final[BuiltinTypeRef] by this
            instance.
        BYTES: Bytes retained as Final[BuiltinTypeRef] by this instance.
        CATALOG: Catalog retained as Final[type[TypeHintCatalog]] by this
            instance.
        COLLECTIONS: Collections retained as
            Final[type[CollectionsConcreteTypeHints]] by this instance.
        COMPLEX: Complex retained as Final[BuiltinTypeRef] by this instance.
        CONTEXT: Context retained as Final[type[ContextManagerTypeHints]] by
            this instance.
        ELLIPSIS: Ellipsis retained as Final[EllipsisTypeRef] by this instance.
        FLOAT: Float retained as Final[BuiltinTypeRef] by this instance.
        INT: Int retained as Final[BuiltinTypeRef] by this instance.
        LITERAL_STRING: Literal string retained as Final[ImportedTypeRef] by
            this instance.
        MEMORYVIEW: Memoryview retained as Final[BuiltinTypeRef] by this
            instance.
        NEVER: Never retained as Final[ImportedTypeRef] by this instance.
        NONE: None retained as Final[BuiltinTypeRef] by this instance.
        NO_RETURN: No return retained as Final[ImportedTypeRef] by this
            instance.
        OBJECT: Object retained as Final[BuiltinTypeRef] by this instance.
        PARAMS: Params retained as Final[type[TypeParameterNames]] by this
            instance.
        RANGE: Range retained as Final[BuiltinTypeRef] by this instance.
        REGEX: Regex retained as Final[type[RegexTypeHints]] by this instance.
        SELF: Self retained as Final[SelfTypeRef] by this instance.
        SLICE: Slice retained as Final[BuiltinTypeRef] by this instance.
        STR: Str retained as Final[BuiltinTypeRef] by this instance.
        TYPE: Type retained as Final[BuiltinTypeRef] by this instance.
        TYPES: Types retained as Final[type[TypesModuleTypeHints]] by this
            instance.
        TYPING: Typing retained as Final[type[TypingTypeHints]] by this
            instance.

    """

    NONE: Final[BuiltinTypeRef] = BuiltinTypeHints.NONE
    BOOL: Final[BuiltinTypeRef] = BuiltinTypeHints.BOOL
    INT: Final[BuiltinTypeRef] = BuiltinTypeHints.INT
    FLOAT: Final[BuiltinTypeRef] = BuiltinTypeHints.FLOAT
    COMPLEX: Final[BuiltinTypeRef] = BuiltinTypeHints.COMPLEX
    STR: Final[BuiltinTypeRef] = BuiltinTypeHints.STR
    BYTES: Final[BuiltinTypeRef] = BuiltinTypeHints.BYTES
    BYTEARRAY: Final[BuiltinTypeRef] = BuiltinTypeHints.BYTEARRAY
    MEMORYVIEW: Final[BuiltinTypeRef] = BuiltinTypeHints.MEMORYVIEW
    OBJECT: Final[BuiltinTypeRef] = BuiltinTypeHints.OBJECT
    TYPE: Final[BuiltinTypeRef] = BuiltinTypeHints.TYPE_DIRECT
    SLICE: Final[BuiltinTypeRef] = BuiltinTypeHints.SLICE
    RANGE: Final[BuiltinTypeRef] = BuiltinTypeHints.RANGE
    ELLIPSIS: Final[EllipsisTypeRef] = EllipsisTypeRef()
    SELF: Final[SelfTypeRef] = SelfTypeRef()
    NEVER: Final[ImportedTypeRef] = TypingTypeHints.NEVER
    NO_RETURN: Final[ImportedTypeRef] = TypingTypeHints.NO_RETURN
    LITERAL_STRING: Final[ImportedTypeRef] = TypingTypeHints.LITERAL_STRING
    BUILTINS: Final[type[BuiltinTypeHints]] = BuiltinTypeHints
    ABC: Final[type[CollectionsAbcTypeHints]] = CollectionsAbcTypeHints
    COLLECTIONS: Final[type[CollectionsConcreteTypeHints]] = (
        CollectionsConcreteTypeHints
    )
    TYPING: Final[type[TypingTypeHints]] = TypingTypeHints
    TYPES: Final[type[TypesModuleTypeHints]] = TypesModuleTypeHints
    REGEX: Final[type[RegexTypeHints]] = RegexTypeHints
    CONTEXT: Final[type[ContextManagerTypeHints]] = ContextManagerTypeHints
    PARAMS: Final[type[TypeParameterNames]] = TypeParameterNames
    CATALOG: Final[type[TypeHintCatalog]] = TypeHintCatalog

    @staticmethod
    def local(*, name: str) -> LocalTypeRef:
        """Create a local type reference.

        Args:
            name: Identifier of the name being resolved.

        Returns:
            LocalTypeRef produced by this operation.

        """
        return LocalTypeRef(name=name)

    @staticmethod
    def imported(
        *,
        module_parts: tuple[str, ...],
        name: str,
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create an absolute imported type reference.

        Args:
            asname: Asname supplied as str | None for this operation.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.

        Returns:
            ImportedTypeRef produced by this operation.

        """
        return ImportedTypeRef.absolute(
            module_parts=module_parts,
            name=name,
            asname=asname,
        )

    @staticmethod
    def relative(
        *,
        level: int,
        name: str,
        module_parts: tuple[str, ...] = (),
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create a relative imported type reference.

        Args:
            asname: Asname supplied as str | None for this operation.
            level: Level supplied as int for this operation.
            module_parts: Module parts supplied as tuple[str, ...] for this
                operation.
            name: Identifier of the name being resolved.

        Returns:
            ImportedTypeRef produced by this operation.

        """
        return ImportedTypeRef.relative(
            level=level,
            module_parts=module_parts,
            name=name,
            asname=asname,
        )

    @staticmethod
    def generic(
        *,
        origin: TypeExpression,
        arguments: tuple[TypeExpression, ...],
    ) -> GenericTypeRef:
        """Create a generic type reference.

        Args:
            arguments: Collection of arguments supplied for this operation.
            origin: Origin supplied as TypeExpression for this operation.

        Returns:
            GenericTypeRef produced by this operation.

        """
        return GenericTypeRef(origin=origin, arguments=arguments)

    @staticmethod
    def union(
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Create a normalized union type reference.

        Args:
            collapse_limit: Collapse limit supplied as int | None for this
                operation.
            options: Options supplied as tuple[TypeExpression, ...] for this
                operation.

        Returns:
            TypeExpression produced by this operation.

        """
        return TypingTypeHints.union_of(
            options=options,
            collapse_limit=collapse_limit,
        )

    @staticmethod
    def callable(
        *,
        parameters: CallableParameterSpec,
        returns: TypeExpression,
    ) -> FlexibleCallableTypeRef:
        """Create a canonical callable type reference.

        Args:
            parameters: Collection of parameters supplied for this operation.
            returns: Returns supplied as TypeExpression for this operation.

        Returns:
            FlexibleCallableTypeRef produced by this operation.

        """
        return FlexibleCallableTypeRef(parameters=parameters, returns=returns)
