"""Single-file semantic contract farm, consolidated from the supplied modules.

Original module boundaries are retained as section comments.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    Call,
    ClassDef,
    Compare,
    Constant,
    DictComp,
    ExceptHandler,
    Expr,
    FunctionDef,
    Global,
    If,
    IfExp,
    Import,
    ImportFrom,
    ListComp,
    Load,
    Match,
    Module,
    Mult,
    Name,
    NamedExpr,
    NodeTransformer,
    Nonlocal,
    Pass,
    Return,
    SetComp,
    Store,
    Subscript,
    Try,
    UnaryOp,
    With,
    Yield,
    YieldFrom,
    alias,
    arg,
    copy_location,
    expr,
    fix_missing_locations,
    iter_child_nodes,
    parse,
    stmt,
    type_param,
    unparse,
    walk,
)
from ast import Dict as AstDict
from ast import List as AstList
from ast import ParamSpec as AstParamSpec
from ast import Set as AstSet
from ast import Tuple as AstTuple
from ast import TypeAlias as AstTypeAlias
from ast import TypeVar as AstTypeVar
from ast import TypeVarTuple as AstTypeVarTuple
from ast import arguments as ast_arguments
from ast import keyword as ast_keyword
from collections import deque
from copy import deepcopy
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from keyword import iskeyword
from math import isfinite, log2
from pathlib import Path
from re import sub
from sys import stdlib_module_names
from token import LPAR, RPAR, STRING
from tokenize import COMMENT, TokenInfo, generate_tokens
from types import EllipsisType
from typing import TYPE_CHECKING, ClassVar, Final, Literal, Never, cast, final

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence
__all__: list[str] = [
    "ExistingImportedName",
    "ExistingModuleImport",
    "ExistingNodeContext",
    "ScriptSymbolIndex",
]
# ===== paths =====
"""Stable path identities for semantic AST analysis."""
# ===== semantic_core (definitions) =====
"""Semantic AST helpers for code generation and type hint synthesis.
This module centralises the low-level mechanics of generating
synthetic AST nodes used by the Semantic-Contract-Farm.  It contains
helpers to:
* Generate protocols, type variables and type aliases based on
  collected evidence.  Functions in the inference pipeline call into
  this module to create new class and function definitions, stubs and
  type expressions when the existing code lacks the necessary
  constructs.
* Build import statements for these synthetic types and existing
  typeshed imports.  The module analyses existing imports, decides
  whether a new import should be absolute or relative, and generates
  ``import`` or ``from … import …`` nodes accordingly.
* Insert ``cast`` calls or helper functions where explicit casts are
  required to satisfy type contracts.
* Unparse and re-parse modified ASTs while preserving formatting and
  comments, using Python's built-in ``unparse`` and custom helpers.
To support these operations, the module defines a number of data
structures (e.g. :class:`ExistingImportedName`,
:class:`ExistingModuleImport`, :class:`ExistingNodeContext`,
:class:`ScriptSymbolIndex`) that index existing imports and classes
available in the file.  Validators ensure generated identifiers are
valid Python names.  ``SemanticCodegenError`` is raised when invalid
input is encountered.
Because this module is long and handles many unrelated concerns, one
of the main improvement tasks is to split it into smaller modules
(``imports.py``, ``protocols.py``, ``editor.py``, etc.) with
well-defined responsibilities.  See the project report for further
guidance.
"""
# ===== imports =====
"""Import-related data models for semantic code generation.
This module centralises simple data structures used to index and
organise existing imports and classes when generating new code.  The
Semantic-Contract-Farm analyses the AST of a Python module to
determine what names are already available so that newly generated
type hints, protocols and helper functions can be imported without
colliding with or shadowing existing names.  These data structures
were previously defined in :mod:`semantic_contract_farm.semantic_core`
but have been extracted into a dedicated module to improve
modularity and readability.
The key classes provided here are:
* :class:`ExistingImportedName` - records the local name bound by
  an import, along with the originating module, imported name,
  import level and whether the binding comes from an ``import`` or
  ``from … import …`` statement.
* :class:`ExistingModuleImport` - captures a simple ``import module``
  statement, storing the fully qualified module name and the local
  alias used.
* :class:`ExistingNodeContext` - splits a list of existing top-level
  AST nodes into import and class nodes.  It provides a
  ``from_nodes`` class method to build the context from a sequence
  of AST statements.
* :class:`ScriptSymbolIndex` - builds a rich index over existing
  imports and class definitions.  It tracks local class names,
  imported names, module imports, wildcard imports, and provides
  helpers to query whether a simple name is available or whether a
  specific import already exists.
These classes are immutable (where appropriate) and make use of
``@dataclass`` for brevity.  They are designed to be lightweight and
safe to share across analysis passes.
"""
# ===== contracts =====
"""Contract and belief algebra for ant-farm type inference."""
# ===== data_model =====
"""Shared data models for semantic entities and graph nodes.
This module defines data structures that represent the nodes, edges and
traces used throughout the Semantic-Contract-Farm.  Separating these
definitions into a dedicated module improves cohesion and allows
multiple components (graph construction, advanced feature seeding,
contract negotiation) to depend on a single source of truth.
The key classes exported here are:
* :class:`GraphNodeKind` - an enumeration of the kinds of semantic
  entities represented in the contract graph (modules, classes,
  functions, arguments, variables, attributes, returns, literals,
  containers, calls, conditions, decorators, bases, context managers
  and metaclasses).
* :class:`ContractGraphNode` - a frozen dataclass carrying a
  stable path, node kind, human-readable name and optional AST
  reference.  Instances of this class are hashable and can be used as
  dictionary keys.
* :class:`ContractGraphEdge` - a frozen dataclass pairing an
  edge identifier with a type contract.  Edges connect two
  ``ContractGraphNode`` instances and describe how evidence flows
  between them.
* :class:`FunctionTrace` and :class:`ClassTrace` - simple containers
  capturing metadata about functions/methods and classes respectively.
These data structures are imported by :mod:`semantic_contract_farm.graph`
and re-exported there for backwards compatibility.
"""
# ===== graph =====
"""Traceable graph model for type-inference contracts.
This module defines a scope-aware directed graph used by the
Semantic-Contract-Farm to model relationships between semantic
entities such as modules, classes, functions, arguments,
variables, attributes and return values.  Each node is identified by
a stable qualified path (see :mod:`semantic_contract_farm.paths`),
and edges carry type contracts and evidence with associated
confidence.
The graph is built by the analyzer while walking the AST.  Nodes
represent definitions and usages; edges represent type
constraints (contracts).  Seeds store initial type hints and
confidence scores attached to nodes.  See the README and the
`ContractGraph` class for details on how the graph is used during
propagation and negotiation.
The public API exposes:
* :class:`GraphNodeKind` - an enumeration of node categories.
* :class:`ContractGraphNode` and :class:`ContractGraphEdge` - data
  structures for graph elements.
* :class:`ContractGraph` - container storing nodes, edges, seeds and
  trace metadata.
* Helper classes :class:`FunctionTrace` and :class:`ClassTrace`
  capturing metadata about functions and classes.
"""
# ===== advanced_features =====
"""Catalogue of advanced Python constructs and graph seeding helpers.
This module identifies higher-level language features that the core
inferencer does not immediately convert into type annotations.  It
records occurrences of constructs such as ``TypedDict`` classes,
``NamedTuple`` definitions, magic methods, async functions, ternary
expressions and match/case patterns.  Detected features are added to
an :class:`AdvancedFeatureCatalog`, which is later used by the
annotation phase to insert appropriate type hints or protocol
definitions.
The module defines:
* :class:`AdvancedFeatureKind` - an enumeration of recognised feature
  categories.
* :class:`AdvancedFeatureRecord` - a record describing a single
  occurrence of a feature in the source code (its kind, path, name,
  AST node and optional details).
* :class:`AdvancedFeatureCatalog` - a mutable collection of records
  offering convenience methods to filter by kind or name.
* :class:`AdvancedFeatureAnalysisResult` - a wrapper around a
  catalog returned by the feature seeder.
* :class:`AdvancedFeatureSeeder` - the visitor that walks the AST,
  detects occurrences of advanced features and seeds the contract
  graph accordingly.
The detection logic is currently baked into methods of
``AdvancedFeatureSeeder``.  In future releases, this module may
support a plug-in architecture where external detectors can register
their own feature kinds; see the project report for further
improvement ideas.
"""
# ===== objective =====
"""Objective model for collective type-hint synthesis."""
# ===== swarm =====
"""Ant-farm contract negotiation engine."""
# ===== annotator =====
"""Automatic annotation synthesis from contract inference results."""
# ===== analyzer =====
"""High-level analyzer facade for contract ant-farm inference."""
type ExistingTopNode = Import | ImportFrom | ClassDef
# ===== semantic_core (implementation) =====
type ArgumentKind = Literal[
    "positional_only",
    "positional_or_keyword",
    "keyword_only",
    "vararg",
    "kwarg",
]
type ImportSourceKind = Literal["absolute", "relative"]
type LiteralValue = str | int | float | bool | None


def fail(*, message: str) -> Never:
    """Raise a semantic code-generation error."""
    raise SemanticCodegenError(message)


type ArgumentItem = (
    ArgumentSpec | SelfArgument | ClsArgument | SlashMarker | StarMarker
)
type OverrideArgumentInput = ast_arguments | tuple[ArgumentSpec, ...]
type OverrideReturnInput = TypeExpression | expr | None
type AttributeAssignmentNode = Assign | AnnAssign
type CallableParameterSpec = TypeExpression | tuple[TypeExpression, ...] | None
type DocstringOwner = Module | ClassDef | FunctionDef
type SemanticFunctionNode = FunctionDef | AsyncFunctionDef
type SemanticNodeId = str
type SemanticScopeId = str
type SemanticSymbolId = str
type TypeParameterOwnerNode = (
    FunctionDef | AsyncFunctionDef | ClassDef | AstTypeAlias
)
type IndexedNodeId = int
type IndexedEdgeId = int
type IndexedScopeId = int
type IndexedSymbolId = int
type TraceableSymbolId = int
type TraceablePathText = str
type CatalogSymbolRecord = TraceableSymbolRecord | LocalImportSymbolRecord
type CatalogSymbolIndex = int
type CatalogSymbolSelector = int | slice
type FunctionNode = FunctionDef | AsyncFunctionDef
type ConstantValue = (
    str | bytes | bool | int | float | complex | None | EllipsisType
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        two_item_count (Final[int]): Expected length of a two-item tuple.
        three_item_count (Final[int]): Expected length of a three-item tuple.
        conflict_confidence (Final[float]): Confidence threshold for
            conflicts.
        one_arg (Final[int]): Count of one argument.
        two_args (Final[int]): Count of two arguments.
        two_items (Final[int]): Count of two items.
        three_items (Final[int]): Count of three items.
        magic_method_names (Final[frozenset[str]]): Dunder method names that
            mark advanced Python features.

    """

    two_item_count: Final[int] = 2
    three_item_count: Final[int] = 3
    conflict_confidence: Final[float] = 0.55
    one_arg: Final[int] = 1
    two_args: Final[int] = 2
    magic_method_names: Final[frozenset[str]] = frozenset(
        {
            "__call__",
            "__getattr__",
            "__getattribute__",
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__iter__",
            "__next__",
            "__aiter__",
            "__anext__",
            "__enter__",
            "__exit__",
            "__aenter__",
            "__aexit__",
            "__import__",
            "__add__",
            "__sub__",
            "__mul__",
            "__matmul__",
            "__truediv__",
            "__floordiv__",
            "__mod__",
            "__pow__",
            "__lshift__",
            "__rshift__",
            "__and__",
            "__xor__",
            "__or__",
            "__invert__",
            "__eq__",
            "__ne__",
            "__lt__",
            "__le__",
            "__gt__",
            "__ge__",
            "__bool__",
            "__len__",
            "__contains__",
            "__int__",
            "__float__",
            "__str__",
            "__bytes__",
        },
    )
    two_items: Final[int] = 2
    three_items: Final[int] = 3


class PathSegmentKind(StrEnum):
    """Kind of a path segment."""

    ROOT = "root"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    SYMBOL = "symbol"
    ATTRIBUTE = "attribute"
    SLOT = "slot"
    TEMPORARY = "temporary"
    RETURN = "return"
    DECORATOR = "decorator"
    BASE = "base"
    METACLASS = "metaclass"


class ImportUsePlace(StrEnum):
    """Semantic place where an imported symbol is used."""

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
    """Final landing location for a generated import."""

    TOP_LEVEL = "top_level"
    TYPE_CHECKING_BLOCK = "type_checking_block"


class ImportGroup(StrEnum):
    """PEP 8 import group."""

    FUTURE = "future"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    LOCAL = "local"


class StringQuoteKind(StrEnum):
    """Quote style used by a string token."""

    SINGLE = "'"
    DOUBLE = '"'
    TRIPLE_SINGLE = "'''"
    TRIPLE_DOUBLE = '"""'


class TypeAliasParameterKind(StrEnum):
    """Kinds of Python 3.13 type-alias type parameters."""

    TYPEVAR = "typevar"
    PARAMSPEC = "paramspec"
    TYPEVARTUPLE = "typevartuple"


class ComparisonIntConstantScope(StrEnum):
    """Where generated integer comparison constants should be inserted."""

    MODULE = "module"
    FUNCTION = "function"
    CLASS = "class"


class SemanticNodeKind(StrEnum):
    """Semantic categories used by the AST graph."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ARGUMENT = "argument"
    RETURN = "return"
    VARIABLE = "variable"
    ATTRIBUTE = "attribute"
    CALL = "call"
    COMPARISON = "comparison"
    CONTAINER = "container"
    CONSTANT = "constant"
    TYPE_HINT = "type_hint"
    STATEMENT = "statement"
    EXPRESSION = "expression"
    UNKNOWN = "unknown"


class SemanticEdgeKind(StrEnum):
    """Semantic relationships between graph nodes."""

    CHILD = "child"
    DEFINES = "defines"
    USES = "uses"
    ASSIGNS_VALUE = "assigns_value"
    RETURNS_VALUE = "returns_value"
    READS_ATTRIBUTE = "reads_attribute"
    WRITES_ATTRIBUTE = "writes_attribute"
    CALLS = "calls"
    CONTAINS_VALUE = "contains_value"
    COMPARES_WITH = "compares_with"
    HAS_TYPE_HINT = "has_type_hint"
    ENCLOSES_SCOPE = "encloses_scope"


class SemanticScopeKind(StrEnum):
    """Kinds of lexical scopes represented in the semantic graph."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"


class SemanticSymbolKind(StrEnum):
    """Kinds of symbols tracked by the graph."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    ARGUMENT = "argument"
    VARIABLE = "variable"
    ATTRIBUTE = "attribute"
    TYPE_PARAMETER = "type_parameter"
    TYPE_ALIAS = "type_alias"


class SemanticUsageKind(StrEnum):
    """Places where a symbol or value is used."""

    LOAD = "load"
    STORE = "store"
    DELETE = "delete"
    ARGUMENT = "argument"
    RETURN = "return"
    CALL_TARGET = "call_target"
    CALL_ARGUMENT = "call_argument"
    ATTRIBUTE_READ = "attribute_read"
    ATTRIBUTE_WRITE = "attribute_write"
    CONTAINER_ELEMENT = "container_element"
    DICT_KEY = "dict_key"
    DICT_VALUE = "dict_value"
    COMPARISON_LEFT = "comparison_left"
    COMPARISON_RIGHT = "comparison_right"


class TypeEvidenceKind(StrEnum):
    """Kinds of type evidence collected from syntax and usage."""

    ANNOTATION = "annotation"
    CONSTANT_VALUE = "constant_value"
    ASSIGNMENT_VALUE = "assignment_value"
    RETURN_VALUE = "return_value"
    CONTAINER_LITERAL = "container_literal"
    CALL_RESULT = "call_result"
    COMPARISON_LITERAL = "comparison_literal"
    ATTRIBUTE_VALUE = "attribute_value"
    UNKNOWN = "unknown"


class GenericTypeParameterKind(StrEnum):
    """Kinds of PEP 695 generic type parameters."""

    TYPEVAR = "typevar"
    PARAMSPEC = "paramspec"
    TYPEVARTUPLE = "typevartuple"


class AdvancedUsageKind(StrEnum):
    """Detailed syntax relationships tracked by the advanced model."""

    CONDITION = "condition"
    ISINSTANCE_NARROWING = "isinstance_narrowing"
    COMPARISON = "comparison"
    SLICE = "slice"
    SUBSCRIPT_READ = "subscript_read"
    SUBSCRIPT_WRITE = "subscript_write"
    APPEND = "append"
    EXTEND = "extend"
    SETDEFAULT = "setdefault"
    DICT_UPDATE = "dict_update"
    ATTRIBUTE_READ = "attribute_read"
    ATTRIBUTE_WRITE = "attribute_write"
    RETURN = "return"
    DECORATOR = "decorator"
    INHERITANCE = "inheritance"
    CLASS_VARIABLE = "class_variable"
    INSTANCE_VARIABLE = "instance_variable"
    PROPERTY_GETTER = "property_getter"
    PROPERTY_SETTER = "property_setter"
    PROPERTY_DELETER = "property_deleter"


class EvidenceMergeMode(StrEnum):
    """How multiple evidence groups should be combined."""

    UNION = "union"
    INTERSECTION = "intersection"
    SEQUENTIAL = "sequential"


class EvidenceContributionKind(StrEnum):
    """Semantic contribution of one evidence item during solving."""

    DECLARES = "declares"
    SUPPORTS_UNION = "supports_union"
    NARROWS = "narrows"
    IGNORED = "ignored"


class TraceablePathKind(StrEnum):
    """Kinds of traceable path segments."""

    ROOT = "root"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    SYMBOL = "symbol"
    ATTRIBUTE = "attribute"
    CONTAINER_SLOT = "container_slot"
    RETURN = "return"
    TEMPORARY = "temporary"


class TraceableValueRelation(StrEnum):
    """Kinds of value-flow relationships between traceable paths."""

    ASSIGNED_FROM = "assigned_from"
    CONTAINS_ELEMENT = "contains_element"
    CONTAINS_KEY = "contains_key"
    CONTAINS_VALUE = "contains_value"
    ATTRIBUTE_OF = "attribute_of"
    RETURNED_FROM = "returned_from"
    ARGUMENT_TO = "argument_to"
    NARROWED_BY = "narrowed_by"


class LocalImportInspectionSource(StrEnum):
    """Source area used to inspect a local or stub import."""

    SCRIPT_DIRECTORY = "script_directory"
    PROJECT_ROOT = "project_root"
    STUB_ROOT = "stub_root"


class LocalImportSymbolKind(StrEnum):
    """Kind of symbol discovered inside an inspected import file."""

    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    TYPE_ALIAS = "type_alias"
    TYPEVAR = "typevar"
    PARAMSPEC = "paramspec"
    TYPEVARTUPLE = "typevartuple"
    IMPORTED = "imported"


class SwarmEvidencePolarity(StrEnum):
    """How propagated evidence contributes to a solved type."""

    DECLARES = "declares"
    SUPPORTS_UNION = "supports_union"
    NARROWS = "narrows"


class SwarmPropagationEdgeKind(StrEnum):
    """Kinds of type-evidence propagation tunnels."""

    ASSIGNMENT = "assignment"
    CONTAINER = "container"
    CALL_ARGUMENT = "call_argument"
    CALL_RETURN = "call_return"
    RETURN_VALUE = "return_value"
    APPEND_MUTATION = "append_mutation"
    EXTEND_MUTATION = "extend_mutation"
    SET_ADD_MUTATION = "set_add_mutation"
    DICT_VALUE_MUTATION = "dict_value_mutation"
    NARROWING = "narrowing"
    CONVERSION_ARGUMENT = "conversion_argument"


class TypeshedParameterKind(StrEnum):
    """Parameter category extracted from a stub signature."""

    POSITIONAL_ONLY = "positional_only"
    POSITIONAL_OR_KEYWORD = "positional_or_keyword"
    VAR_POSITIONAL = "var_positional"
    KEYWORD_ONLY = "keyword_only"
    VAR_KEYWORD = "var_keyword"


class ContractRelation(StrEnum):
    """Semantic relation between two paths."""

    ASSIGNS = "assigns"
    RETURNS = "returns"
    ARGUMENT = "argument"
    CALL_RESULT = "call_result"
    ELEMENT = "element"
    KEY = "key"
    VALUE = "value"
    ATTRIBUTE = "attribute"
    INSTANCE_FIELD = "instance_field"
    CLASS_FIELD = "class_field"
    NARROWS = "narrows"
    REQUIRES_PROTOCOL = "requires_protocol"
    DECORATES = "decorates"
    INHERITS = "inherits"
    METACLASS = "metaclass"
    CONTEXT_ENTER = "context_enter"
    CONTEXT_EXIT = "context_exit"
    OPERATOR = "operator"


class ContractPolarity(StrEnum):
    """How a contract contributes to a belief."""

    UNION = "union"
    INTERSECTION = "intersection"
    DECLARATION = "declaration"
    CAPABILITY = "capability"
    CONFLICT = "conflict"


class GraphNodeKind(StrEnum):
    """Kinds of semantic graph nodes.

    Each node in the contract graph is annotated with a kind to
    describe the semantic entity it represents.  The kinds roughly
    correspond to elements of the Python language (modules, classes,
    functions) and the positions where type hints may be inferred.
    """

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    ARGUMENT = "argument"
    VARIABLE = "variable"
    ATTRIBUTE = "attribute"
    RETURN = "return"
    LITERAL = "literal"
    CONTAINER = "container"
    CALL = "call"
    CONDITION = "condition"
    DECORATOR = "decorator"
    BASE = "base"
    CONTEXT_MANAGER = "context_manager"
    METACLASS = "metaclass"


class AdvancedFeatureKind(StrEnum):
    """Kinds of advanced Python features recognized by the analyzer."""

    TYPED_DICT_CLASS = "typed_dict_class"
    TYPED_DICT_FUNCTION = "typed_dict_function"
    NAMED_TUPLE_CLASS = "named_tuple_class"
    NAMED_TUPLE_FUNCTION = "named_tuple_function"
    MAGIC_METHOD = "magic_method"
    ASYNC_FUNCTION = "async_function"
    ASYNC_ITERATOR_PROTOCOL = "async_iterator_protocol"
    PROPERTY_METHOD = "property_method"
    SUPER_CALL = "super_call"
    DYNAMIC_IMPORT = "dynamic_import"
    IMPORTLIB_CALL = "importlib_call"
    WALRUS = "walrus"
    TERNARY = "ternary"
    MATCH = "match"
    CASE_CONDITION = "case_condition"
    TRY = "try"
    EXCEPT_HANDLER = "except_handler"
    LIST_COMPREHENSION = "list_comprehension"
    SET_COMPREHENSION = "set_comprehension"
    DICT_COMPREHENSION = "dict_comprehension"
    BIT_OPERATOR = "bit_operator"
    YIELD = "yield"
    YIELD_FROM = "yield_from"


class SyntheticStepKind(StrEnum):
    """Synthetic operation kind used by the objective function."""

    ATTRIBUTE_SETATTR_REWRITE = "attribute_setattr_rewrite"
    CAST_WRAP = "cast_wrap"
    OVERRIDE = "override"
    PROTOCOL = "protocol"
    TYPEVAR = "typevar"
    PARAMSPEC = "paramspec"
    TYPE_ALIAS_REUSE = "type_alias_reuse"
    EXISTING_TYPE_REUSE = "existing_type_reuse"
    DIRECT_ANNOTATION = "direct_annotation"


@dataclass(slots=True, frozen=True)
class IndexedNodeKindRule:
    """One AST-type to semantic-kind classification rule."""

    node_types: tuple[type[AST], ...]
    kind: SemanticNodeKind


@dataclass(slots=True, frozen=True)
class SemanticImportSource:
    """Semantic source location for importing one symbol."""

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
        """Create an absolute import source."""
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
        """Create a relative import source."""
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
        """Return the ``ast.ImportFrom.module`` value."""
        if not self.module_parts:
            return None
        return ".".join(self.module_parts)

    def validate(self, *, validator: IdentifierValidator) -> None:
        """Validate all identifiers in this import source."""
        if self.kind == "absolute" and self.level != 0:
            msg: str = "Absolute imports must have level 0."
            fail(message=msg)
        if self.kind == "relative" and self.level <= 0:
            msg = "Relative imports require level >= 1."
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
class TypeTemplateRef:
    """Constrained generic type template with semantic arity validation."""

    origin: TypeExpression
    label: str
    min_args: int
    max_args: int | None
    allow_empty: bool = False

    def of(self, *, arguments: tuple[TypeExpression, ...]) -> TypeExpression:
        """Create a generic type expression after arity validation."""
        argument_count: int = len(arguments)
        if argument_count == 0 and self.allow_empty:
            return EmptyGenericTypeRef(origin=self.origin)
        if argument_count < self.min_args:
            msg: str = (
                f"{self.label} expects at least {self.min_args} type "
                f"arguments; received {argument_count}."
            )
            fail(message=msg)
        if self.max_args is not None and argument_count > self.max_args:
            msg = (
                f"{self.label} expects at most {self.max_args} type "
                f"arguments; received {argument_count}."
            )
            fail(message=msg)
        return GenericTypeRef(origin=self.origin, arguments=arguments)

    def empty(self) -> EmptyGenericTypeRef:
        """Create an intentionally empty generic expression."""
        if not self.allow_empty:
            msg: str = (
                f"{self.label} does not allow an empty type argument list."
            )
            fail(message=msg)
        return EmptyGenericTypeRef(origin=self.origin)


class TypeExpression(ABC):
    """Base class for semantic type expressions."""

    @abstractmethod
    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Convert this type expression to an AST node."""

    @abstractmethod
    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type expression as a type-hint string."""

    @abstractmethod
    def key(self) -> str:
        """Return a stable semantic key."""

    def __or__(self, other: TypeExpression) -> UnionTypeRef:
        """Create a normalized semantic union with another type."""
        return UnionTypeRef(options=(self, other))


@dataclass(slots=True, frozen=True)
class BuiltinTypeRef(TypeExpression):
    """Reference a built-in type by name."""

    name: str

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a simple name node."""
        resolver.validate_identifier(name=self.name, label="built-in type")
        return Name(id=self.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type reference."""
        renderer.validate_identifier(name=self.name, label="built-in type")
        return self.name

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"builtins:{self.name}"


@dataclass(slots=True, frozen=True)
class LocalTypeRef(TypeExpression):
    """Reference a type already available in the local module."""

    name: str

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a local name node."""
        resolver.validate_identifier(name=self.name, label="local type")
        return Name(id=self.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this type reference."""
        renderer.validate_identifier(name=self.name, label="local type")
        return self.name

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"local:{self.name}"


@dataclass(slots=True, frozen=True)
class SelfTypeRef(TypeExpression):
    """Reference ``typing.Self``."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a ``Self`` name and register its import."""
        return resolver.imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Self",
            ),
            use=_use,
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``Self`` and register its string-hint import."""
        return renderer.render_imported(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Self",
            ),
        )

    def key(self) -> str:
        """Return a stable semantic key."""
        return "typing:Self"


@dataclass(slots=True, frozen=True)
class EllipsisTypeRef(TypeExpression):
    """Semantic ellipsis used inside constrained type templates."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return an ellipsis constant."""
        _: TypeExpressionResolver = resolver
        return Constant(value=Ellipsis)

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render as ``...``."""
        _: TypeHintStringRenderer = renderer
        return "..."

    def key(self) -> str:
        """Return a stable semantic key."""
        return "ellipsis"


class DirectTypeRefs:
    """Direct, unsubscripted type-expression references."""

    @staticmethod
    def builtin(*, name: str) -> BuiltinTypeRef:
        """Return a direct builtin type reference."""
        return BuiltinTypeRef(name=name)

    @staticmethod
    def imported(
        *,
        module_parts: tuple[str, ...],
        name: str,
    ) -> ImportedTypeRef:
        """Return a direct imported type reference."""
        return ImportedTypeRef.absolute(module_parts=module_parts, name=name)


@dataclass(slots=True, frozen=True)
class ImportedTypeRef(TypeExpression):
    """Reference a type that should be imported from a semantic source."""

    source: SemanticImportSource

    @classmethod
    def absolute(
        cls,
        *,
        module_parts: tuple[str, ...],
        name: str,
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create an absolute imported type reference."""
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
        """Create a relative imported type reference."""
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
        """Return a name node and register the import source."""
        return resolver.imports.require_from_source(
            source=self.source,
            use=_use,
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this imported type and register string-hint imports."""
        return renderer.render_imported(source=self.source)

    def key(self) -> str:
        """Return a stable semantic key."""
        return (
            f"imported:{self.source.module}:{self.source.level}:"
            f"{self.source.imported_name}:{self.source.asname or ''}"
        )


@final
class BuiltinTypeHints:
    """Canonical builtin direct references and generic templates."""

    none: Final[BuiltinTypeRef] = BuiltinTypeRef(name="None")
    bool: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bool")
    int: Final[BuiltinTypeRef] = BuiltinTypeRef(name="int")
    float: Final[BuiltinTypeRef] = BuiltinTypeRef(name="float")
    complex: Final[BuiltinTypeRef] = BuiltinTypeRef(name="complex")
    str: Final[BuiltinTypeRef] = BuiltinTypeRef(name="str")
    bytes: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bytes")
    bytearray: Final[BuiltinTypeRef] = BuiltinTypeRef(name="bytearray")
    memoryview: Final[BuiltinTypeRef] = BuiltinTypeRef(name="memoryview")
    object: Final[BuiltinTypeRef] = BuiltinTypeRef(name="object")
    type_direct: Final[BuiltinTypeRef] = BuiltinTypeRef(name="type")
    slice: Final[BuiltinTypeRef] = BuiltinTypeRef(name="slice")
    range: Final[BuiltinTypeRef] = BuiltinTypeRef(name="range")
    ellipsis_object: Final[BuiltinTypeRef] = BuiltinTypeRef(name="Ellipsis")
    list: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="list"),
        label="list",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    tuple: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="tuple"),
        label="tuple",
        min_args=1,
        max_args=None,
        allow_empty=True,
    )
    dict: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="dict"),
        label="dict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    set: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="set"),
        label="set",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    frozenset: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="frozenset"),
        label="frozenset",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    type: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=BuiltinTypeRef(name="type"),
        label="type",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )

    @staticmethod
    def list_of(*, item: TypeExpression) -> TypeExpression:
        """Return ``list[item]``."""
        return BuiltinTypeHints.list.of(arguments=(item,))

    @staticmethod
    def tuple_variadic(*, item: TypeExpression) -> TypeExpression:
        """Return ``tuple[item, ...]``."""
        return BuiltinTypeHints.tuple.of(arguments=(item, EllipsisTypeRef()))

    @staticmethod
    def tuple_of(*, items: tuple[TypeExpression, ...]) -> TypeExpression:
        """Return fixed heterogeneous ``tuple[...]``."""
        return BuiltinTypeHints.tuple.of(arguments=items)

    @staticmethod
    def tuple_empty() -> EmptyTupleTypeRef:
        """Return ``tuple[()]``."""
        return EmptyTupleTypeRef()

    @staticmethod
    def dict_of(
        *,
        keys: TypeExpression,
        values: TypeExpression,
    ) -> TypeExpression:
        """Return ``dict[keys, values]``."""
        return BuiltinTypeHints.dict.of(arguments=(keys, values))

    @staticmethod
    def set_of(*, item: TypeExpression) -> TypeExpression:
        """Return ``set[item]``."""
        return BuiltinTypeHints.set.of(arguments=(item,))

    @staticmethod
    def frozenset_of(*, item: TypeExpression) -> TypeExpression:
        """Return ``frozenset[item]``."""
        return BuiltinTypeHints.frozenset.of(arguments=(item,))

    @staticmethod
    def type_of(*, item: TypeExpression) -> TypeExpression:
        """Return ``type[item]``."""
        return BuiltinTypeHints.type.of(arguments=(item,))


@final
class TypesModuleTypeHints:
    """Direct runtime type references from the ``types`` module."""

    async_generator_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="AsyncGeneratorType",
    )
    builtin_function_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="BuiltinFunctionType",
    )
    builtin_method_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="BuiltinMethodType",
    )
    cell_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CellType",
    )
    code_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CodeType",
    )
    coroutine_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="CoroutineType",
    )
    ellipsis_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="EllipsisType",
    )
    frame_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="FrameType",
    )
    function_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="FunctionType",
    )
    generator_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GeneratorType",
    )
    generic_alias: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GenericAlias",
    )
    get_set_descriptor_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="GetSetDescriptorType",
    )
    lambda_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="LambdaType",
    )
    mapping_proxy_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MappingProxyType",
    )
    member_descriptor_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MemberDescriptorType",
    )
    method_descriptor_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodDescriptorType",
    )
    method_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodType",
    )
    method_wrapper_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="MethodWrapperType",
    )
    module_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="ModuleType",
    )
    none_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="NoneType",
    )
    not_implemented_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="NotImplementedType",
    )
    simple_namespace: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="SimpleNamespace",
    )
    traceback_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="TracebackType",
    )
    union_type: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("types",),
        name="UnionType",
    )


@final
class CollectionsAbcTypeHints:
    """Canonical ``collections.abc`` direct refs and generic templates."""

    hashable: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="Hashable",
    )
    sized: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="Sized",
    )
    byte_string: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections", "abc"),
        name="ByteString",
    )
    awaitable: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Awaitable",
        ),
        label="Awaitable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    async_iterable: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncIterable",
        ),
        label="AsyncIterable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    async_iterator: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncIterator",
        ),
        label="AsyncIterator",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    iterable: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Iterable",
        ),
        label="Iterable",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    iterator: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Iterator",
        ),
        label="Iterator",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    reversible: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Reversible",
        ),
        label="Reversible",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    container: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Container",
        ),
        label="Container",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    collection: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Collection",
        ),
        label="Collection",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    sequence: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Sequence",
        ),
        label="Sequence",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    mutable_sequence: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableSequence",
        ),
        label="MutableSequence",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    set: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Set",
        ),
        label="Set",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    mutable_set: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableSet",
        ),
        label="MutableSet",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    mapping_view: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MappingView",
        ),
        label="MappingView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    keys_view: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="KeysView",
        ),
        label="KeysView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    values_view: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="ValuesView",
        ),
        label="ValuesView",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    items_view: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="ItemsView",
        ),
        label="ItemsView",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    mapping: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Mapping",
        ),
        label="Mapping",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    mutable_mapping: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="MutableMapping",
        ),
        label="MutableMapping",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    async_generator: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="AsyncGenerator",
        ),
        label="AsyncGenerator",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    coroutine: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections", "abc"),
            name="Coroutine",
        ),
        label="Coroutine",
        min_args=3,
        max_args=3,
        allow_empty=True,
    )
    generator: Final[TypeTemplateRef] = TypeTemplateRef(
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
        """Return a canonical callable type expression."""
        return FlexibleCallableTypeRef(parameters=parameters, returns=returns)

    @staticmethod
    def one_arg(
        *,
        template: TypeTemplateRef,
        item: TypeExpression,
    ) -> TypeExpression:
        """Apply a one-argument ABC template."""
        return template.of(arguments=(item,))

    @staticmethod
    def two_arg(
        *,
        template: TypeTemplateRef,
        first: TypeExpression,
        second: TypeExpression,
    ) -> TypeExpression:
        """Apply a two-argument ABC template."""
        return template.of(arguments=(first, second))

    @staticmethod
    def three_arg(
        *,
        template: TypeTemplateRef,
        first: TypeExpression,
        second: TypeExpression,
        third: TypeExpression,
    ) -> TypeExpression:
        """Apply a three-argument ABC template."""
        return template.of(arguments=(first, second, third))


@final
class CollectionsConcreteTypeHints:
    """Concrete generic collection classes from ``collections``."""

    chain_map: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="ChainMap",
        ),
        label="ChainMap",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    counter: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="Counter",
        ),
        label="Counter",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    ordered_dict: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="OrderedDict",
        ),
        label="OrderedDict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    user_dict: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="UserDict",
        ),
        label="UserDict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    user_list: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="UserList",
        ),
        label="UserList",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    user_string: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("collections",),
        name="UserString",
    )
    defaultdict: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="defaultdict",
        ),
        label="defaultdict",
        min_args=2,
        max_args=2,
        allow_empty=True,
    )
    deque: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("collections",),
            name="deque",
        ),
        label="deque",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


@final
class TypingTypeHints:
    """Canonical direct special forms from ``typing``."""

    self: Final[SelfTypeRef] = SelfTypeRef()
    literal_string: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="LiteralString",
    )
    never: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="Never",
    )
    no_return: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="NoReturn",
    )
    param_spec: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="ParamSpec",
    )
    protocol: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Protocol",
        ),
        label="Protocol",
        min_args=0,
        max_args=None,
        allow_empty=True,
    )
    generic: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Generic",
        ),
        label="Generic",
        min_args=1,
        max_args=None,
        allow_empty=True,
    )
    type_alias: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeAlias",
    )
    type_var: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeVar",
    )
    type_var_tuple: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypeVarTuple",
    )
    typed_dict: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TypedDict",
    )
    classvar: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="ClassVar",
        ),
        label="ClassVar",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    final: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("typing",), name="Final"),
        label="Final",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    required: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Required",
        ),
        label="Required",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    not_required: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="NotRequired",
        ),
        label="NotRequired",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    read_only: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="ReadOnly",
        ),
        label="ReadOnly",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    unpack: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Unpack",
        ),
        label="Unpack",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    type_guard: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="TypeGuard",
        ),
        label="TypeGuard",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    type_is: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="TypeIs",
        ),
        label="TypeIs",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    annotated: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("typing",),
            name="Annotated",
        ),
        label="Annotated",
        min_args=2,
        max_args=None,
        allow_empty=False,
    )
    io: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("typing",), name="IO"),
        label="IO",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    text_io: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="TextIO",
    )
    binary_io: Final[ImportedTypeRef] = DirectTypeRefs.imported(
        module_parts=("typing",),
        name="BinaryIO",
    )

    @staticmethod
    def literal_of(*, values: tuple[LiteralValue, ...]) -> LiteralTypeRef:
        """Return a ``Literal[...]`` expression."""
        if not values:
            fail(message="Literal requires at least one value.")
        return LiteralTypeRef(values=values)

    @staticmethod
    def union_of(
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Return a normalized modern PEP 604 union expression."""
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
    def noneable(*, item: TypeExpression) -> TypeExpression:
        """Return ``item | None`` without using ``Optional``."""
        return TypingTypeHints.union_of(options=(item, BuiltinTypeHints.none))

    @staticmethod
    def concatenate_of(
        *,
        prefix: tuple[TypeExpression, ...],
        params: TypeExpression,
    ) -> ConcatenateTypeRef:
        """Return a ``Concatenate[..., P]`` expression."""
        return ConcatenateTypeRef(prefix=prefix, params=params)


@final
class RegexTypeHints:
    """Canonical regular-expression type templates."""

    pattern: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("re",), name="Pattern"),
        label="Pattern",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    match: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(module_parts=("re",), name="Match"),
        label="Match",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


@final
class ContextManagerTypeHints:
    """Canonical context-manager type templates."""

    abstract_context_manager: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("contextlib",),
            name="AbstractContextManager",
        ),
        label="AbstractContextManager",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )
    abstract_async_context_manager: Final[TypeTemplateRef] = TypeTemplateRef(
        origin=DirectTypeRefs.imported(
            module_parts=("contextlib",),
            name="AbstractAsyncContextManager",
        ),
        label="AbstractAsyncContextManager",
        min_args=1,
        max_args=1,
        allow_empty=True,
    )


@final
class TypeParameterNames:
    """Common type-parameter names used inside annotations."""

    t: Final[LocalTypeRef] = LocalTypeRef(name="T")
    t_co: Final[LocalTypeRef] = LocalTypeRef(name="T_co")
    t_contra: Final[LocalTypeRef] = LocalTypeRef(name="T_contra")
    k: Final[LocalTypeRef] = LocalTypeRef(name="K")
    v: Final[LocalTypeRef] = LocalTypeRef(name="V")
    r: Final[LocalTypeRef] = LocalTypeRef(name="R")
    p: Final[LocalTypeRef] = LocalTypeRef(name="P")
    ts: Final[LocalTypeRef] = LocalTypeRef(name="Ts")


@final
class TypeHintCatalog:
    """Flat direct-annotation catalog organized by canonical source."""

    builtins: Final[type[BuiltinTypeHints]] = BuiltinTypeHints
    types: Final[type[TypesModuleTypeHints]] = TypesModuleTypeHints
    abc: Final[type[CollectionsAbcTypeHints]] = CollectionsAbcTypeHints
    collections: Final[type[CollectionsConcreteTypeHints]] = (
        CollectionsConcreteTypeHints
    )
    typing: Final[type[TypingTypeHints]] = TypingTypeHints
    regex: Final[type[RegexTypeHints]] = RegexTypeHints
    context: Final[type[ContextManagerTypeHints]] = ContextManagerTypeHints
    params: Final[type[TypeParameterNames]] = TypeParameterNames


@final
class Types:
    """Convenience facade for canonical semantic type expressions."""

    none: Final[BuiltinTypeRef] = BuiltinTypeHints.none
    bool: Final[BuiltinTypeRef] = BuiltinTypeHints.bool
    int: Final[BuiltinTypeRef] = BuiltinTypeHints.int
    float: Final[BuiltinTypeRef] = BuiltinTypeHints.float
    complex: Final[BuiltinTypeRef] = BuiltinTypeHints.complex
    str: Final[BuiltinTypeRef] = BuiltinTypeHints.str
    bytes: Final[BuiltinTypeRef] = BuiltinTypeHints.bytes
    bytearray: Final[BuiltinTypeRef] = BuiltinTypeHints.bytearray
    memoryview: Final[BuiltinTypeRef] = BuiltinTypeHints.memoryview
    object: Final[BuiltinTypeRef] = BuiltinTypeHints.object
    type: Final[BuiltinTypeRef] = BuiltinTypeHints.type_direct
    slice: Final[BuiltinTypeRef] = BuiltinTypeHints.slice
    range: Final[BuiltinTypeRef] = BuiltinTypeHints.range
    ellipsis: Final[EllipsisTypeRef] = EllipsisTypeRef()
    self: Final[SelfTypeRef] = SelfTypeRef()
    never: Final[ImportedTypeRef] = TypingTypeHints.never
    no_return: Final[ImportedTypeRef] = TypingTypeHints.no_return
    literal_string: Final[ImportedTypeRef] = TypingTypeHints.literal_string
    builtins: Final[type[BuiltinTypeHints]] = BuiltinTypeHints
    abc: Final[type[CollectionsAbcTypeHints]] = CollectionsAbcTypeHints
    collections: Final[type[CollectionsConcreteTypeHints]] = (
        CollectionsConcreteTypeHints
    )
    typing: Final[type[TypingTypeHints]] = TypingTypeHints
    types: Final[type[TypesModuleTypeHints]] = TypesModuleTypeHints
    regex: Final[type[RegexTypeHints]] = RegexTypeHints
    context: Final[type[ContextManagerTypeHints]] = ContextManagerTypeHints
    params: Final[type[TypeParameterNames]] = TypeParameterNames
    catalog: Final[type[TypeHintCatalog]] = TypeHintCatalog

    @staticmethod
    def local(*, name: str) -> LocalTypeRef:
        """Create a local type reference."""
        return LocalTypeRef(name=name)

    @staticmethod
    def imported(
        *,
        module_parts: tuple[str, ...],
        name: str,
        asname: str | None = None,
    ) -> ImportedTypeRef:
        """Create an absolute imported type reference."""
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
        """Create a relative imported type reference."""
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
        """Create a generic type reference."""
        return GenericTypeRef(origin=origin, arguments=arguments)

    @staticmethod
    def union(
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Create a normalized union type reference."""
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
        """Create a canonical callable type reference."""
        return FlexibleCallableTypeRef(parameters=parameters, returns=returns)


@final
class UnionSimplificationTables:
    """Rank and origin tables for union simplification."""

    numeric_ranks: Final[dict[str, int]] = {
        "bool": 0,
        "int": 1,
        "float": 2,
        "complex": 3,
    }
    mapping_origins: Final[frozenset[str]] = frozenset(
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
    mutable_mapping_origins: Final[frozenset[str]] = frozenset(
        {
            "dict",
            "MutableMapping",
            "defaultdict",
            "Counter",
            "OrderedDict",
            "UserDict",
        },
    )
    iterable_origins: Final[frozenset[str]] = frozenset(
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
    sequence_origins: Final[frozenset[str]] = frozenset(
        {
            "list",
            "tuple",
            "deque",
            "UserList",
            "Sequence",
            "MutableSequence",
        },
    )
    mutable_sequence_origins: Final[frozenset[str]] = frozenset(
        {
            "list",
            "deque",
            "UserList",
            "MutableSequence",
        },
    )
    set_origins: Final[frozenset[str]] = frozenset(
        {"set", "frozenset", "Set", "MutableSet"},
    )
    mutable_set_origins: Final[frozenset[str]] = frozenset(
        {"set", "MutableSet"},
    )


@final
class TypeParameterNameTables:
    """Type-parameter name tables for signature matching."""

    typevar_names: Final[tuple[str, ...]] = (
        "T",
        "U",
        "V",
        "W",
        "X",
        "Y",
        "Z",
    )
    paramspec_names: Final[tuple[str, ...]] = ("P", "Q", "R", "S")


@final
class ExistingTypeParameterNames:
    """Typing construct names found in existing signatures."""

    typevar_names: Final[frozenset[str]] = frozenset({"TypeVar"})
    paramspec_names: Final[frozenset[str]] = frozenset({"ParamSpec"})
    typevartuple_names: Final[frozenset[str]] = frozenset({"TypeVarTuple"})


@final
class ProtocolCapabilityTables:
    """Dunder and verb capability maps for protocol grammar."""

    dunder_capabilities: Final[dict[str, str]] = {
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
    verb_capabilities: Final[dict[str, str]] = {
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
    composites: Final[dict[frozenset[str], str]] = {
        frozenset({"__iter__", "__next__"}): "Iterator",
        frozenset({"read", "write"}): "IO",
        frozenset({"encode", "decode"}): "EncodingRoundTrip",
        frozenset({"serialize", "deserialize"}): "SerializationRoundTrip",
        frozenset({"get", "set"}): "PropertyAccess",
    }


@final
class ImportPlacementTables:
    """Import placement classification tables."""

    runtime_places: Final[frozenset[ImportUsePlace]] = frozenset(
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
    type_checking_only_places: Final[frozenset[ImportUsePlace]] = frozenset(
        {ImportUsePlace.STRING_TYPE_HINT},
    )


@final
class AstNodeKindTables:
    """AST node type to semantic kind mapping."""

    kind_by_type: ClassVar[
        tuple[tuple[tuple[type[AST], ...], SemanticNodeKind], ...]
    ] = (
        ((Module,), SemanticNodeKind.MODULE),
        ((ClassDef,), SemanticNodeKind.CLASS),
        ((FunctionDef, AsyncFunctionDef), SemanticNodeKind.FUNCTION),
        ((arg,), SemanticNodeKind.ARGUMENT),
        ((Return,), SemanticNodeKind.RETURN),
        ((Name,), SemanticNodeKind.VARIABLE),
        ((Attribute,), SemanticNodeKind.ATTRIBUTE),
        ((Call,), SemanticNodeKind.CALL),
        ((Compare,), SemanticNodeKind.COMPARISON),
        ((AstList, AstTuple, AstDict, AstSet), SemanticNodeKind.CONTAINER),
        ((Constant,), SemanticNodeKind.CONSTANT),
        ((stmt,), SemanticNodeKind.STATEMENT),
        ((expr,), SemanticNodeKind.EXPRESSION),
    )


@final
class AdvancedUsageTables:
    """Advanced usage classification tables."""

    mutating_methods: ClassVar[dict[str, AdvancedUsageKind]] = {
        "append": AdvancedUsageKind.APPEND,
        "extend": AdvancedUsageKind.EXTEND,
        "setdefault": AdvancedUsageKind.SETDEFAULT,
        "update": AdvancedUsageKind.DICT_UPDATE,
    }


@final
class EvidenceKindTables:
    """Type-evidence kind classification tables."""

    declaration_kinds: ClassVar[frozenset[TypeEvidenceKind]] = frozenset(
        {TypeEvidenceKind.ANNOTATION},
    )
    narrowing_kinds: ClassVar[frozenset[TypeEvidenceKind]] = frozenset(
        {TypeEvidenceKind.COMPARISON_LITERAL},
    )
    union_kinds: ClassVar[frozenset[TypeEvidenceKind]] = frozenset(
        {
            TypeEvidenceKind.ASSIGNMENT_VALUE,
            TypeEvidenceKind.ATTRIBUTE_VALUE,
            TypeEvidenceKind.CALL_RESULT,
            TypeEvidenceKind.CONSTANT_VALUE,
            TypeEvidenceKind.CONTAINER_LITERAL,
            TypeEvidenceKind.RETURN_VALUE,
        },
    )


@final
class SemanticNodeKindTables:
    """Semantic node kind classification rules."""

    kind_rules: ClassVar[tuple[IndexedNodeKindRule, ...]] = (
        IndexedNodeKindRule(
            node_types=(Module,),
            kind=SemanticNodeKind.MODULE,
        ),
        IndexedNodeKindRule(
            node_types=(ClassDef,),
            kind=SemanticNodeKind.CLASS,
        ),
        IndexedNodeKindRule(
            node_types=(FunctionDef, AsyncFunctionDef),
            kind=SemanticNodeKind.FUNCTION,
        ),
        IndexedNodeKindRule(node_types=(arg,), kind=SemanticNodeKind.ARGUMENT),
        IndexedNodeKindRule(
            node_types=(Return,),
            kind=SemanticNodeKind.RETURN,
        ),
        IndexedNodeKindRule(
            node_types=(Name,),
            kind=SemanticNodeKind.VARIABLE,
        ),
        IndexedNodeKindRule(
            node_types=(Attribute,),
            kind=SemanticNodeKind.ATTRIBUTE,
        ),
        IndexedNodeKindRule(node_types=(Call,), kind=SemanticNodeKind.CALL),
        IndexedNodeKindRule(
            node_types=(Compare,),
            kind=SemanticNodeKind.COMPARISON,
        ),
        IndexedNodeKindRule(
            node_types=(AstList, AstTuple, AstSet, AstDict),
            kind=SemanticNodeKind.CONTAINER,
        ),
        IndexedNodeKindRule(
            node_types=(Constant,),
            kind=SemanticNodeKind.CONSTANT,
        ),
        IndexedNodeKindRule(
            node_types=(stmt,),
            kind=SemanticNodeKind.STATEMENT,
        ),
        IndexedNodeKindRule(
            node_types=(expr,),
            kind=SemanticNodeKind.EXPRESSION,
        ),
    )


@final
class SwarmConversionTables:
    """Swarm conversion method and return-type tables."""

    conversion_methods: ClassVar[dict[str, tuple[str, TypeExpression]]] = {
        "int": ("__int__", Types.int),
        "float": ("__float__", Types.float),
        "complex": ("__complex__", Types.complex),
        "str": ("__str__", Types.str),
        "bytes": ("__bytes__", Types.bytes),
        "bool": ("__bool__", Types.bool),
    }
    conversion_return_types: ClassVar[dict[str, TypeExpression]] = {
        "bool": Types.bool,
        "int": Types.int,
        "float": Types.float,
        "complex": Types.complex,
        "str": Types.str,
        "bytes": Types.bytes,
    }


@final
class TypeshedNameTables:
    """Typeshed builtin and typing name tables."""

    builtins: ClassVar[dict[str, TypeExpression]] = {
        "None": Types.none,
        "bool": Types.bool,
        "int": Types.int,
        "float": Types.float,
        "complex": Types.complex,
        "str": Types.str,
        "bytes": Types.bytes,
        "bytearray": Types.bytearray,
        "memoryview": Types.memoryview,
        "object": Types.object,
        "type": Types.type,
        "slice": Types.slice,
        "range": Types.range,
    }
    typing_names: ClassVar[dict[str, TypeExpression]] = {
        "Self": Types.self,
        "Never": Types.never,
        "NoReturn": Types.no_return,
        "LiteralString": Types.literal_string,
    }


@final
class TypeNarrownessTables:
    """Type narrowness scoring tables."""

    builtin_base: Final[dict[str, float]] = {
        "None": 0.95,
        "bool": 0.95,
        "int": 0.9,
        "float": 0.86,
        "complex": 0.82,
        "str": 0.9,
        "bytes": 0.88,
        "object": 0.0,
    }


@dataclass(frozen=True, slots=True)
class PathSegment:
    """One stable path segment."""

    kind: PathSegmentKind
    name: str
    index: int = 1

    def text(self) -> str:
        """Return the stable text for this segment."""
        if self.kind is PathSegmentKind.ROOT:
            return "root"
        if self.index <= 1:
            return self.name
        return f"{self.name}_{self.index}"


@dataclass(frozen=True, slots=True)
class QualifiedPath:
    """A stable traceable path for scopes, symbols, and values."""

    segments: tuple[PathSegment, ...]

    @classmethod
    def root(cls) -> QualifiedPath:
        """Create the root path."""
        return cls(
            segments=(PathSegment(kind=PathSegmentKind.ROOT, name="root"),),
        )

    @classmethod
    def parse(cls, *, value: str) -> QualifiedPath:
        """Parse a dotted path into a qualified path."""
        parts: tuple[str, ...] = tuple(
            part for part in value.split(sep=".") if part
        )
        if not parts:
            return cls.root()
        segments: list[PathSegment] = []
        for index, part in enumerate(iterable=parts):
            kind: PathSegmentKind = (
                PathSegmentKind.ROOT if index == 0 else PathSegmentKind.SYMBOL
            )
            segments.append(PathSegment(kind=kind, name=part))
        return cls(segments=tuple(segments))

    def child(
        self,
        *,
        kind: PathSegmentKind,
        name: str,
        index: int = 1,
    ) -> QualifiedPath:
        """Return a child path."""
        return QualifiedPath(
            segments=(
                *self.segments,
                PathSegment(kind=kind, name=name, index=index),
            ),
        )

    def parent(self) -> QualifiedPath | None:
        """Return the parent path."""
        if len(self.segments) <= 1:
            return None
        return QualifiedPath(segments=self.segments[:-1])

    def text(self) -> str:
        """Return the dotted path text."""
        return ".".join(segment.text() for segment in self.segments)

    def __str__(self) -> str:
        """Return the dotted path text."""
        return self.text()


@dataclass(slots=True, frozen=True)
class ExistingImportedName:
    """A name already available in the target generation context.

    Attributes:
        local_name: The local alias bound by the import statement.
        module: The dotted module path from which the name was imported,
            or ``None`` for relative imports.
        imported_name: The original imported symbol (for ``from`` imports)
            or the module name (for ``import`` statements).
        level: The relative import level (0 for absolute imports).
        is_module_import: Whether the binding comes from a plain
            ``import`` statement instead of ``from``.

    """

    local_name: str
    module: str | None
    imported_name: str
    level: int
    is_module_import: bool


@dataclass(slots=True, frozen=True)
class ExistingModuleImport:
    """Existing ``import module`` data.

    A simple container capturing a fully qualified module import and
    the local alias bound by the ``import`` statement.

    Attributes:
        module: The fully qualified module name.
        local_name: The local alias used in the ``import`` statement.

    """

    module: str
    local_name: str


@dataclass(slots=True, frozen=True)
class ExistingNodeContext:
    """Existing import/class nodes used as generation context.

    This context separates a sequence of existing top-level AST nodes
    into import and class nodes.  It is used to build a
    :class:`ScriptSymbolIndex`.

    Attributes:
        import_nodes: Tuple of :class:`ast.Import` or :class:`ast.ImportFrom`
            nodes present at the top of the file.
        class_nodes: Tuple of :class:`ast.ClassDef` nodes representing
            classes defined at the top level of the file.

    """

    import_nodes: tuple[Import | ImportFrom, ...]
    class_nodes: tuple[ClassDef, ...]

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
        for node in nodes:
            if isinstance(node, (Import, ImportFrom)):
                import_nodes.append(node)
            else:
                class_nodes.append(node)
        return cls(
            import_nodes=tuple(import_nodes),
            class_nodes=tuple(class_nodes),
        )


@dataclass(slots=True)
class ScriptSymbolIndex:
    """Index of names already available in the generation context.

    This index records what symbols have already been imported or defined
    in a given AST, enabling the code generator to avoid duplicate
    imports and to choose unique names.  It tracks:
    * Local class names defined in the current module.
    * Individual imported names (from ``from`` imports) and their
      associated modules.
    * Plain module imports and their local aliases.
    * Wildcard imports (``from module import *``) by module and level.

    Methods provide efficient lookup to determine whether a name is
    available or whether a particular import exists.
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
    wildcard_imports: set[tuple[str | None, int]] = field(
        default_factory=set,
    )

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
        for import_node in context.import_nodes:
            if isinstance(import_node, ImportFrom):
                index._record_import_from(node=import_node)
            else:
                index._record_import(node=import_node)
        return index

    def is_name_available(self, *, name: str) -> bool:
        """Return whether a simple name already exists."""
        return name in self.local_class_names or name in self.imported_names

    def find_imported_from(
        self,
        *,
        module: str | None,
        level: int,
        name: str,
    ) -> str | None:
        """Return local name for an existing ``from`` import."""
        return self.imported_from.get((module, level, name))

    def has_wildcard_from(self, *, module: str | None, level: int) -> bool:
        """Return whether a matching wildcard import exists."""
        return (module, level) in self.wildcard_imports

    def _record_import_from(self, *, node: ImportFrom) -> None:
        """Record an existing ``from module import name`` node."""
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
                (node.module, node.level, imported_alias.name)
            ] = local_name

    def _record_import(self, *, node: Import) -> None:
        """Record an existing ``import module`` node."""
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


@dataclass(slots=True, frozen=True)
class ImportUseSite:
    """One semantic use site of an imported symbol."""

    place: ImportUsePlace
    owner: str | None = None
    reason: str | None = None

    @classmethod
    def runtime(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a runtime use site."""
        return cls(place=ImportUsePlace.RUNTIME, owner=owner)

    @classmethod
    def annotation(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create an annotation use site."""
        return cls(place=ImportUsePlace.ANNOTATION, owner=owner)

    @classmethod
    def string_type_hint(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a string-type-hint use site."""
        return cls(place=ImportUsePlace.STRING_TYPE_HINT, owner=owner)

    @classmethod
    def typevar_declaration(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-constructor use site."""
        return cls(place=ImportUsePlace.TYPEVAR_DECLARATION, owner=owner)

    @classmethod
    def paramspec_declaration(
        cls,
        *,
        owner: str | None = None,
    ) -> ImportUseSite:
        """Create a ParamSpec-constructor use site."""
        return cls(place=ImportUsePlace.PARAMSPEC_DECLARATION, owner=owner)

    @classmethod
    def typevar_bound(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-bound use site."""
        return cls(place=ImportUsePlace.TYPEVAR_BOUND, owner=owner)

    @classmethod
    def typevar_constraint(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a TypeVar-constraint use site."""
        return cls(place=ImportUsePlace.TYPEVAR_CONSTRAINT, owner=owner)

    @classmethod
    def protocol_base(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a protocol-base use site."""
        return cls(place=ImportUsePlace.PROTOCOL_BASE, owner=owner)

    @classmethod
    def method_body(cls, *, owner: str | None = None) -> ImportUseSite:
        """Create a method-body use site."""
        return cls(place=ImportUsePlace.METHOD_BODY, owner=owner)


@dataclass(slots=True, frozen=True)
class ImportRequirementKey:
    """Stable key for one importable symbol."""

    module: str | None
    level: int
    name: str


@dataclass(slots=True)
class ImportRequirement:
    """One collected import requirement."""

    module: str | None
    level: int
    name: str
    local_name: str
    uses: list[ImportUseSite] = field(default_factory=list)

    @property
    def asname(self) -> str | None:
        """Return import alias if needed."""
        if self.local_name == self.name:
            return None
        return self.local_name

    def add_use(self, *, use: ImportUseSite) -> None:
        """Record a semantic usage site."""
        if use not in self.uses:
            self.uses.append(use)


@dataclass(slots=True, frozen=True)
class ImportAliasSpec:
    """One imported name inside an ``ImportFrom`` node."""

    name: str
    asname: str | None


@dataclass(slots=True, frozen=True)
class ImportFromGroup:
    """Grouped imports from a single module."""

    module: str | None
    level: int
    names: tuple[ImportAliasSpec, ...]


@dataclass(slots=True, frozen=True)
class GeneratedImportGroups:
    """Generated import nodes grouped by PEP 8 sections."""

    top_level_stdlib: tuple[stmt, ...]
    top_level_third_party: tuple[stmt, ...]
    top_level_local: tuple[stmt, ...]
    type_checking_stdlib: tuple[stmt, ...]
    type_checking_third_party: tuple[stmt, ...]
    type_checking_local: tuple[stmt, ...]
    type_checking_block: If | None

    @property
    def top_level_nodes(self) -> tuple[stmt, ...]:
        """Return top-level imports in PEP 8 order."""
        return (
            *self.top_level_stdlib,
            *self.top_level_third_party,
            *self.top_level_local,
        )

    @property
    def type_checking_nodes(self) -> tuple[stmt, ...]:
        """Return imports inside the ``TYPE_CHECKING`` block."""
        return (
            *self.type_checking_stdlib,
            *self.type_checking_third_party,
            *self.type_checking_local,
        )

    @property
    def all_import_nodes(self) -> tuple[stmt, ...]:
        """Return all generated import nodes."""
        if self.type_checking_block is None:
            return self.top_level_nodes
        return (*self.top_level_nodes, self.type_checking_block)


@dataclass(slots=True, frozen=True)
class _GenericParts:
    """Decomposed generic type information for union simplification."""

    family: str
    arguments: tuple[TypeExpression, ...]
    origin_name: str


@dataclass(slots=True, frozen=True)
class TypeVarSignature:
    """Semantic identity of a generated ``TypeVar``."""

    bound: TypeExpression | None
    constraints: tuple[TypeExpression, ...]
    covariant: bool
    contravariant: bool


@dataclass(slots=True, frozen=True)
class ParamSpecSignature:
    """Semantic identity of a generated ``ParamSpec``."""

    bound: TypeExpression | None
    covariant: bool
    contravariant: bool


@dataclass(slots=True, frozen=True)
class TypeVarSpec:
    """Semantic specification for a generated ``TypeVar``.

    Instances of this class record the chosen name for a type variable and
    its signature (constraints, bound and variance).  The signature is
    encapsulated in a :class:`TypeVarSignature` and used both when
    reserving a stable name and when building the corresponding
    :class:`ast.Assign` node.  A :class:`TypeVarSpec` can be converted
    into a :class:`TypeVarRef` via :meth:`ref`, which provides a
    lightweight reference into type expressions.
    """

    name: str
    signature: TypeVarSignature

    def ref(self) -> TypeVarRef:
        """Return a type-expression reference to this TypeVar."""
        return TypeVarRef(spec=self)


@dataclass(slots=True, frozen=True)
class ParamSpecSpec:
    """Semantic specification for a generated ``ParamSpec``.

    A :class:`ParamSpecSpec` records the name and signature for a
    parametrized call signature.  It supports conversion to
    :class:`ParamSpecRef` via :meth:`ref` as well as convenience methods
    :meth:`args_ref` and :meth:`kwargs_ref` for referring to the
    ``*args`` and ``**kwargs`` portions of the specification.  Just like
    ``TypeVar``, parameter specifications can have bounds and variance,
    which are captured in the associated :class:`ParamSpecSignature`.
    """

    name: str
    signature: ParamSpecSignature

    def ref(self) -> ParamSpecRef:
        """Return a type-expression reference to this ParamSpec."""
        return ParamSpecRef(spec=self)

    def args_ref(self) -> ParamSpecArgsRef:
        """Return a ``P.args`` type-expression reference."""
        return ParamSpecArgsRef(spec=self)

    def kwargs_ref(self) -> ParamSpecKwargsRef:
        """Return a ``P.kwargs`` type-expression reference."""
        return ParamSpecKwargsRef(spec=self)


@dataclass(slots=True, frozen=True)
class ArgumentSpec:
    """Semantic method argument spec."""

    name: str
    type_hint: TypeExpression
    kind: ArgumentKind = "positional_or_keyword"
    default: expr | None = None


@dataclass(slots=True, frozen=True)
class ClsArgument:
    """Special receiver argument representing ``cls``."""

    type_hint: TypeExpression

    def to_argument(self) -> ArgumentSpec:
        """Convert to a normal argument spec."""
        return ArgumentSpec(name="cls", type_hint=self.type_hint)


@dataclass(slots=True, frozen=True)
class SlashMarker:
    """Semantic marker for positional-only slash syntax."""


@dataclass(slots=True, frozen=True)
class StarMarker:
    """Semantic marker for bare keyword-only star syntax."""


@dataclass(slots=True, frozen=True)
class MethodSpec:
    """Semantic protocol method spec."""

    name: str
    arguments: tuple[ArgumentItem, ...]
    returns: TypeExpression
    docstring: str | None = None
    decorators: tuple[expr, ...] = ()
    body: tuple[stmt, ...] | None = None


@dataclass(slots=True, frozen=True)
class ProtocolSpec:
    """Semantic protocol class spec."""

    methods: tuple[MethodSpec, ...]
    name: str | None = None
    docstring: str | None = None
    bases: tuple[TypeExpression, ...] = ()
    decorators: tuple[expr, ...] = ()


@dataclass(slots=True, frozen=True)
class ProtocolRegistration:
    """Result of registering a protocol."""

    spec: ProtocolSpec
    class_node: ClassDef
    is_existing: bool
    match_reason: Literal["name", "shape", "new"]


@dataclass(slots=True, frozen=True)
class GeneratedTopBlock:
    """Top-of-module nodes generated by the collector."""

    missing_import_nodes: tuple[stmt, ...]
    declaration_nodes_after_imports: tuple[stmt, ...]

    @property
    def all_nodes_for_empty_module(self) -> tuple[stmt, ...]:
        """Return imports followed by declarations."""
        return (
            *self.missing_import_nodes,
            *self.declaration_nodes_after_imports,
        )


@dataclass(slots=True, frozen=True)
class ProtocolShape:
    """Comparable structural shape of a protocol class."""

    methods: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(slots=True)
class ParameterState:
    """Mutable state used while normalizing arguments."""

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
    """Semantic summary of one protocol method."""

    name: str
    capability: str
    required_argument_count: int
    is_dunder: bool


@dataclass(slots=True)
class AstArgumentGroups:
    """Intermediate AST argument groups."""

    posonlyargs: list[arg] = field(default_factory=list)
    args: list[arg] = field(default_factory=list)
    kwonlyargs: list[arg] = field(default_factory=list)
    kw_defaults: list[expr | None] = field(default_factory=list)
    positional_specs: list[ArgumentSpec] = field(default_factory=list)
    vararg: arg | None = None
    kwarg: arg | None = None

    def add(self, *, argument: ArgumentSpec, node: arg) -> None:
        """Add one argument to the correct AST group."""
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

    def _single(self, *, current: arg | None, value: arg, label: str) -> arg:
        """Validate singleton argument slots."""
        if current is not None:
            msg: str = f"Only one {label} argument is allowed."
            fail(message=msg)
        return value


@dataclass(slots=True, frozen=True)
class MethodOverrideUpdate:
    """Replacement fields for a copied method override."""

    arguments: OverrideArgumentInput | None = None
    return_annotation: OverrideReturnInput = None
    name: str | None = None
    body: tuple[stmt, ...] | None = None
    decorators: tuple[expr, ...] | None = None
    order: int | None = None


@dataclass(slots=True, frozen=True)
class MethodOverrideSpec:
    """Semantic request for one method override clone.

    The original method is copied structurally. Optional fields replace only
    the corresponding part of the copied method.
    """

    original: FunctionDef
    update: MethodOverrideUpdate


@dataclass(slots=True, frozen=True)
class MethodOverrideEntry:
    """One ordered override function node."""

    order: int
    node: FunctionDef


@dataclass(slots=True, frozen=True)
class AttributeSetattrRewriteResult:
    """Replacement nodes for one attribute assignment.

    ``attribute_name_node`` is equivalent to ``_attr_name: str = "b"``.
    ``setattr_node`` is equivalent to ``setattr(a, _attr_name, value)``.
    """

    attribute_name_node: AnnAssign
    setattr_node: Expr

    @property
    def nodes(self) -> tuple[stmt, stmt]:
        """Return both replacement nodes in insertion order."""
        return (self.attribute_name_node, self.setattr_node)


@dataclass(slots=True, frozen=True)
class SourcePosition:
    """Zero-based column and one-based line source position."""

    line: int
    column: int

    def key(self) -> tuple[int, int]:
        """Return a sortable key."""
        return (self.line, self.column)


@dataclass(slots=True, frozen=True)
class SourceSpan:
    """Half-open source span using tokenizer coordinates."""

    start: SourcePosition
    end: SourcePosition

    def key(self) -> tuple[int, int, int, int]:
        """Return a stable key for dictionary indexing."""
        return (
            self.start.line,
            self.start.column,
            self.end.line,
            self.end.column,
        )

    def encloses(self, *, inner: SourceSpan) -> bool:
        """Return whether this span encloses another span."""
        return (
            self.start.key() <= inner.start.key()
            and inner.end.key() <= self.end.key()
        )


@dataclass(slots=True, frozen=True)
class SourceToken:
    """Token with normalized span metadata."""

    kind: int
    exact_kind: int
    text: str
    span: SourceSpan

    @classmethod
    def from_token(cls, *, token: TokenInfo) -> SourceToken:
        """Create source-token metadata from ``tokenize`` output."""
        start: SourcePosition = SourcePosition(
            line=token.start[0],
            column=token.start[1],
        )
        end: SourcePosition = SourcePosition(
            line=token.end[0],
            column=token.end[1],
        )
        return cls(
            kind=token.type,
            exact_kind=token.exact_type,
            text=token.string,
            span=SourceSpan(start=start, end=end),
        )


@dataclass(slots=True, frozen=True)
class StringQuoteMetadata:
    """Original string-token quote metadata."""

    span: SourceSpan
    quote: StringQuoteKind
    prefix: str


@dataclass(slots=True, frozen=True)
class ParenthesisMetadata:
    """Original parenthesis pair metadata."""

    outer_span: SourceSpan
    inner_span: SourceSpan


@dataclass(slots=True, frozen=True)
class TokenizedParseResult:
    """Result of token-aware semantic parsing."""

    module: Module
    tokens: tuple[SourceToken, ...]
    string_quotes: tuple[StringQuoteMetadata, ...]
    parentheses: tuple[ParenthesisMetadata, ...]
    quoted_nodes: tuple[QuotedConstantNode, ...]
    parenthesized_nodes: tuple[ParenthesizedExpressionNode, ...]
    body: BodyBlockNode
    source: str


@dataclass(slots=True, frozen=True)
class TypeAliasTypeParameterSpec:
    """Semantic description of a type parameter for a PEP-695 type alias.

    Python-3.13 introduces parameterised ``type`` aliases which can bind
    ``TypeVar``, ``ParamSpec`` or ``TypeVarTuple`` parameters.  This
    dataclass captures the name of the parameter, its kind
    (type variable, parameter specification or type-variable tuple) and
    optional bound and default.  The helper constructors
    :meth:`typevar`, :meth:`paramspec` and :meth:`typevartuple` make it
    easy to instantiate the appropriate kind.  Use :meth:`to_ast` to
    convert the specification into the corresponding ``ast.type_param``
    node when emitting an ``ast.TypeAlias``.
    """

    name: str
    kind: TypeAliasParameterKind = TypeAliasParameterKind.TYPEVAR
    bound: TypeExpression | None = None
    default: TypeExpression | None = None

    @classmethod
    def typevar(
        cls,
        *,
        name: str,
        bound: TypeExpression | None = None,
        default: TypeExpression | None = None,
    ) -> TypeAliasTypeParameterSpec:
        """Create a type-var alias parameter."""
        return cls(
            name=name,
            kind=TypeAliasParameterKind.TYPEVAR,
            bound=bound,
            default=default,
        )

    @classmethod
    def paramspec(
        cls,
        *,
        name: str,
        default: TypeExpression | None = None,
    ) -> TypeAliasTypeParameterSpec:
        """Create a ParamSpec alias parameter."""
        return cls(
            name=name,
            kind=TypeAliasParameterKind.PARAMSPEC,
            default=default,
        )

    @classmethod
    def typevartuple(
        cls,
        *,
        name: str,
        default: TypeExpression | None = None,
    ) -> TypeAliasTypeParameterSpec:
        """Create a TypeVarTuple alias parameter."""
        return cls(
            name=name,
            kind=TypeAliasParameterKind.TYPEVARTUPLE,
            default=default,
        )

    def to_ast(self, *, resolver: TypeExpressionResolver) -> type_param:
        """Build the corresponding Python 3.13 AST type parameter."""
        validator: IdentifierValidator = IdentifierValidator()
        validator.validate_identifier(
            name=self.name,
            label="type alias parameter",
        )
        default_node: expr | None = self._default_node(resolver=resolver)
        if self.kind is TypeAliasParameterKind.PARAMSPEC:
            return AstParamSpec(name=self.name, default_value=default_node)
        if self.kind is TypeAliasParameterKind.TYPEVARTUPLE:
            return AstTypeVarTuple(name=self.name, default_value=default_node)
        return AstTypeVar(
            name=self.name,
            bound=self._bound_node(resolver=resolver),
            default_value=default_node,
        )

    def _bound_node(self, *, resolver: TypeExpressionResolver) -> expr | None:
        """Return the bound node for a type-var parameter."""
        if self.bound is None:
            return None
        return self.bound.to_ast(
            resolver=resolver,
            _use=ImportUseSite.runtime(owner=self.name),
        )

    def _default_node(
        self,
        *,
        resolver: TypeExpressionResolver,
    ) -> expr | None:
        """Return the default node for a type parameter."""
        if self.default is None:
            return None
        return self.default.to_ast(
            resolver=resolver,
            _use=ImportUseSite.runtime(owner=self.name),
        )


@dataclass(slots=True, frozen=True)
class TypeAliasSpec:
    """Semantic specification for a ``type`` alias in Python-3.13.

    A ``type`` alias associates a new alias name with a target
    type expression, optionally parameterised over one or more type
    parameters.  This dataclass bundles the alias name, the
    canonicalised value to alias and any type parameters (see
    :class:`TypeAliasTypeParameterSpec`).  A semantic key computed by
    :meth:`key` combines the alias value and parameter kinds, allowing
    reuse detection across distinct alias names.
    """

    name: str
    value: TypeExpression
    type_params: tuple[TypeAliasTypeParameterSpec, ...] = ()

    def key(self) -> str:
        """Return a semantic key used for reuse and merging."""
        params_key: str = ",".join(
            f"{param.kind.value}:{param.name}" for param in self.type_params
        )
        return f"alias:{self.value.key()}[{params_key}]"


@dataclass(slots=True, frozen=True)
class TypeAliasRegistration:
    """Result of registering a semantic type alias with the manager.

    When adding a type alias, the manager either reuses an existing
    ``ast.TypeAlias`` node (matched by name or value) or builds a new
    node.  This dataclass records the associated specification, the
    alias node itself, whether it already existed in the parsed module,
    and the reason for the match (``"name"``, ``"value"`` or ``"new"``).
    """

    spec: TypeAliasSpec
    node: AstTypeAlias
    is_existing: bool
    match_reason: Literal["name", "value", "new"]


@dataclass(slots=True, frozen=True)
class SemanticDeclarationBlock:
    """Generated declaration block including Python 3.13 type aliases."""

    imports: tuple[stmt, ...]
    typevars: tuple[stmt, ...]
    paramspecs: tuple[stmt, ...]
    type_aliases: tuple[stmt, ...]
    protocols: tuple[stmt, ...]
    constants: tuple[stmt, ...] = ()

    def to_preamble_node(self) -> GeneratedPreambleBlockNode:
        """Convert this block to a custom preamble AST node."""
        preamble: GeneratedPreambleBlockNode = GeneratedPreambleBlockNode(
            imports=self.imports,
            typevars=self.typevars,
            paramspecs=self.paramspecs,
            type_aliases=self.type_aliases,
            protocols=self.protocols,
        )
        preamble.constants = self.constants
        return preamble

    @property
    def ordered_nodes(self) -> tuple[stmt, ...]:
        """Return nodes in canonical order before the body."""
        return self.to_preamble_node().ordered_nodes


@dataclass(slots=True, frozen=True)
class CommentMetadata:
    """Source comment metadata preserved by token-aware parsing."""

    span: SourceSpan
    text: str
    indent: str

    @property
    def line(self) -> int:
        """Return the one-based source line."""
        return self.span.start.line


@dataclass(slots=True, frozen=True)
class CommentAwareParseResult:
    """Parse result containing tokens, AST metadata, and comments."""

    parsed: TokenizedParseResult
    comments: tuple[CommentMetadata, ...]

    @property
    def module(self) -> Module:
        """Return the parsed module."""
        return self.parsed.module

    @property
    def body(self) -> BodyBlockNode:
        """Return the parsed body block."""
        return self.parsed.body

    @property
    def source(self) -> str:
        """Return the original source text."""
        return self.parsed.source


@dataclass(slots=True, frozen=True)
class StatementCommentBlock:
    """Comments associated with one statement during rendering."""

    leading: tuple[CommentMetadata, ...]
    inline: CommentMetadata | None


@dataclass(slots=True, frozen=True)
class StatementReplacement:
    """Replacement statements for one original statement."""

    original: stmt
    replacements: tuple[stmt, ...]


@dataclass(slots=True)
class DeclarationBlockBuildState:
    """Mutable state used while organizing generated declaration blocks."""

    imports: list[stmt] = field(default_factory=list)
    typevars: list[stmt] = field(default_factory=list)
    paramspecs: list[stmt] = field(default_factory=list)
    type_aliases: list[stmt] = field(default_factory=list)
    protocols: list[stmt] = field(default_factory=list)
    constants: list[stmt] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class ComparisonIntConstantConfig:
    """Configuration for integer comparison literal hoisting."""

    scope: ComparisonIntConstantScope = ComparisonIntConstantScope.MODULE
    prefix: str | None = None

    @property
    def resolved_prefix(self) -> str:
        """Return the configured prefix or the default prefix."""
        if self.prefix is None:
            return "_INT"
        return self.prefix


@dataclass(slots=True, frozen=True)
class ComparisonIntConstantSpec:
    """One generated integer comparison constant."""

    value: int
    name: str


@dataclass(slots=True, frozen=True)
class ComparisonIntConstantBlock:
    """Generated integer constants grouped as statement nodes."""

    nodes: tuple[stmt, ...]


@dataclass(slots=True, frozen=True)
class ParsedDocstring:
    """Docstring parsed from a module, class, or function."""

    owner_name: str
    owner_kind: Literal["module", "class", "function"]
    text: str
    node: Expr


@dataclass(slots=True, frozen=True)
class ParsedImportModel:
    """Parsed import model for one import statement."""

    node: Import | ImportFrom
    module: str | None
    level: int
    names: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ParsedFunctionSignature:
    """Parsed function signature and annotation model."""

    node: FunctionDef
    name: str
    arguments: tuple[arg, ...]
    vararg: arg | None
    keyword_only_arguments: tuple[arg, ...]
    kwarg: arg | None
    return_annotation: AstBackedTypeExpression | None
    docstring: ParsedDocstring | None


@dataclass(slots=True, frozen=True)
class ParsedClassModel:
    """Parsed class model including docstring and methods."""

    node: ClassDef
    name: str
    bases: tuple[AstBackedTypeExpression, ...]
    docstring: ParsedDocstring | None
    methods: tuple[ParsedFunctionSignature, ...]
    is_protocol: bool


@dataclass(slots=True, frozen=True)
class ParsedTypeParameterModel:
    """Parsed TypeVar, ParamSpec, or TypeVarTuple declaration."""

    node: Assign | AnnAssign
    name: str
    kind: Literal["typevar", "paramspec", "typevartuple"]
    value_node: expr | None


@dataclass(slots=True, frozen=True)
class ParsedTypeAliasModel:
    """Parsed type alias model."""

    node: AstTypeAlias | Assign | AnnAssign
    name: str
    value: AstBackedTypeExpression


@dataclass(slots=True, frozen=True)
class ParsedSemanticModel:
    """Semantic model extracted from an existing Python source tree."""

    parsed: CommentAwareParseResult
    context: ExistingNodeContext
    imports: tuple[ParsedImportModel, ...]
    module_docstring: ParsedDocstring | None
    classes: tuple[ParsedClassModel, ...]
    functions: tuple[ParsedFunctionSignature, ...]
    type_parameters: tuple[ParsedTypeParameterModel, ...]
    type_aliases: tuple[ParsedTypeAliasModel, ...]

    @property
    def protocols(self) -> tuple[ParsedClassModel, ...]:
        """Return parsed protocol classes."""
        return tuple(
            class_model
            for class_model in self.classes
            if class_model.is_protocol
        )


@dataclass(slots=True, frozen=True)
class SemanticGraphEdge:
    """Directed semantic edge between graph nodes."""

    source_id: SemanticNodeId
    target_id: SemanticNodeId
    kind: SemanticEdgeKind
    label: str | None = None


@dataclass(slots=True)
class SemanticScope:
    """Lexical scope tracked by the semantic graph."""

    id: SemanticScopeId
    kind: SemanticScopeKind
    name: str
    node_id: SemanticNodeId
    parent_id: SemanticScopeId | None
    symbols: dict[str, SemanticSymbolId] = field(default_factory=dict)

    def define(self, *, name: str, symbol_id: SemanticSymbolId) -> None:
        """Define or replace a symbol in this scope."""
        self.symbols[name] = symbol_id


@dataclass(slots=True)
class SemanticGraphNode:
    """Graph node wrapping an AST node with semantic metadata."""

    id: SemanticNodeId
    ast_node: AST
    kind: SemanticNodeKind
    scope_id: SemanticScopeId
    parent_id: SemanticNodeId | None
    name: str | None = None
    role: SemanticUsageKind | None = None

    def view(self, *, graph: SemanticAstGraph) -> SemanticAstNodeView:
        """Return a navigable view for this node."""
        return SemanticAstNodeView(graph=graph, node_id=self.id)


@dataclass(slots=True)
class SemanticSymbol:
    """Symbol definition and usage model."""

    id: SemanticSymbolId
    name: str
    kind: SemanticSymbolKind
    scope_id: SemanticScopeId
    definition_node_id: SemanticNodeId | None
    usage_node_ids: list[SemanticNodeId] = field(default_factory=list)
    evidence: list[TypeInferenceEvidence] = field(default_factory=list)

    def add_usage(self, *, node_id: SemanticNodeId) -> None:
        """Record a usage node."""
        if node_id not in self.usage_node_ids:
            self.usage_node_ids.append(node_id)

    def add_evidence(self, *, evidence: TypeInferenceEvidence) -> None:
        """Record type evidence."""
        if evidence not in self.evidence:
            self.evidence.append(evidence)


@dataclass(slots=True, frozen=True)
class TypeInferenceEvidence:
    """One piece of evidence for a semantic type."""

    kind: TypeEvidenceKind
    type_hint: TypeExpression
    node_id: SemanticNodeId
    confidence: float
    reason: str


@dataclass(slots=True, frozen=True)
class SemanticValueUsage:
    """Summary of where a value or symbol participates."""

    symbol: SemanticSymbol
    definitions: tuple[SemanticAstNodeView, ...]
    usages: tuple[SemanticAstNodeView, ...]
    evidence: tuple[TypeInferenceEvidence, ...]


@dataclass(slots=True, frozen=True)
class SemanticAstNodeView:
    """Convenient navigable view over a semantic graph node."""

    graph: SemanticAstGraph
    node_id: SemanticNodeId

    @property
    def graph_node(self) -> SemanticGraphNode:
        """Return the underlying graph node."""
        return self.graph.nodes[self.node_id]

    @property
    def node(self) -> AST:
        """Return the underlying AST node."""
        return self.graph_node.ast_node

    @property
    def kind(self) -> SemanticNodeKind:
        """Return the semantic node kind."""
        return self.graph_node.kind

    @property
    def name(self) -> str | None:
        """Return the semantic node name."""
        return self.graph_node.name

    @property
    def parent(self) -> SemanticAstNodeView | None:
        """Return the parent node view."""
        parent_id: SemanticNodeId | None = self.graph.parent_of(
            node_id=self.node_id,
        )
        if parent_id is None:
            return None
        return self.graph.view(node_id=parent_id)

    @property
    def children(self) -> tuple[SemanticAstNodeView, ...]:
        """Return child node views."""
        return tuple(
            self.graph.view(node_id=child_id)
            for child_id in self.graph.children_of(node_id=self.node_id)
        )

    @property
    def descendants(self) -> tuple[SemanticAstNodeView, ...]:
        """Return all descendant node views."""
        result: list[SemanticAstNodeView] = []
        stack: list[SemanticAstNodeView] = list(self.children)
        while stack:
            current: SemanticAstNodeView = stack.pop()
            result.append(current)
            stack.extend(current.children)
        return tuple(result)

    @property
    def text(self) -> str:
        """Return ``ast.unparse`` text for this node."""
        return unparse(
            ast_obj=fix_missing_locations(node=deepcopy(x=self.node)),
        )

    @property
    def outgoing_edges(self) -> tuple[SemanticGraphEdge, ...]:
        """Return outgoing semantic edges."""
        return self.graph.outgoing(node_id=self.node_id)

    @property
    def incoming_edges(self) -> tuple[SemanticGraphEdge, ...]:
        """Return incoming semantic edges."""
        return self.graph.incoming(node_id=self.node_id)

    @property
    def symbols(self) -> tuple[SemanticSymbol, ...]:
        """Return symbols defined at this node."""
        return tuple(
            symbol
            for symbol in self.graph.symbols.values()
            if symbol.definition_node_id == self.node_id
        )

    def children_of_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return direct children with a semantic kind."""
        return tuple(child for child in self.children if child.kind == kind)

    def descendants_of_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return descendant nodes with a semantic kind."""
        return tuple(child for child in self.descendants if child.kind == kind)


@dataclass(slots=True, frozen=True)
class SemanticGraphParseResult:
    """Parse result containing native and semantic graph models."""

    model: ParsedSemanticModel
    graph: SemanticAstGraph

    @property
    def root(self) -> SemanticAstNodeView | None:
        """Return the root graph view."""
        return self.graph.root()


@dataclass(slots=True, frozen=True)
class GenericTypeParameterSpec:
    """Semantic specification for a PEP 695 type parameter."""

    name: str
    kind: GenericTypeParameterKind
    bound: TypeExpression | None = None
    default: TypeExpression | None = None


@dataclass(slots=True, frozen=True)
class GenericTypeParameterBlock:
    """Ordered block of PEP 695 type parameter nodes."""

    parameters: tuple[type_param, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Return parameter names in declaration order."""
        return tuple(
            TypeParameterNameReader.name(parameter=parameter)
            for parameter in self.parameters
        )


@dataclass(slots=True, frozen=True)
class AdvancedScopeRef:
    """Scope path for an advanced semantic usage record."""

    parts: tuple[str, ...]

    @property
    def text(self) -> str:
        """Return a dotted scope path."""
        if not self.parts:
            return "<module>"
        return ".".join(self.parts)

    def child(self, *, name: str) -> AdvancedScopeRef:
        """Return a nested scope path."""
        return AdvancedScopeRef(parts=(*self.parts, name))


@dataclass(slots=True, frozen=True)
class AdvancedUsageRecord:
    """One tracked advanced syntax usage."""

    kind: AdvancedUsageKind
    name: str
    scope: AdvancedScopeRef
    node: AST
    detail: str
    related: str | None = None


@dataclass(slots=True, frozen=True)
class PropertyUsageRecord:
    """Relationship between property accessors of the same logical name."""

    name: str
    owner: str
    getter: FunctionDef | None
    setter: FunctionDef | None
    deleter: FunctionDef | None


@dataclass(slots=True, frozen=True)
class ClassVariableRecord:
    """Tracked class or instance variable declaration/write."""

    owner: str
    name: str
    node: AST
    is_instance: bool
    method_name: str | None


@dataclass(slots=True, frozen=True)
class FunctionFlowRecord:
    """Tracked function-level flow facts."""

    name: str
    scope: AdvancedScopeRef
    arguments: tuple[str, ...]
    returns: tuple[Return, ...]
    decorators: tuple[str, ...]
    type_parameters: tuple[str, ...]


@dataclass(slots=True, frozen=True)
class ClassFlowRecord:
    """Tracked class-level structure and relationships."""

    name: str
    scope: AdvancedScopeRef
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    init_method: FunctionDef | None
    new_method: FunctionDef | None
    properties: tuple[PropertyUsageRecord, ...]
    class_variables: tuple[ClassVariableRecord, ...]
    instance_variables: tuple[ClassVariableRecord, ...]


@dataclass(slots=True, frozen=True)
class AdvancedSemanticUsageModel:
    """Introspective model richer than the native AST."""

    usages: tuple[AdvancedUsageRecord, ...]
    functions: tuple[FunctionFlowRecord, ...]
    classes: tuple[ClassFlowRecord, ...]

    def usages_for(self, *, name: str) -> tuple[AdvancedUsageRecord, ...]:
        """Return all usage records for a name."""
        return tuple(record for record in self.usages if record.name == name)

    def conditions_for(self, *, name: str) -> tuple[AdvancedUsageRecord, ...]:
        """Return all conditions applied to a variable or attribute name."""
        return tuple(
            record
            for record in self.usages_for(name=name)
            if record.kind
            in {
                AdvancedUsageKind.CONDITION,
                AdvancedUsageKind.ISINSTANCE_NARROWING,
                AdvancedUsageKind.COMPARISON,
            }
        )

    def mutations_for(self, *, name: str) -> tuple[AdvancedUsageRecord, ...]:
        """Return container and attribute mutation records for a name."""
        return tuple(
            record
            for record in self.usages_for(name=name)
            if record.kind
            in {
                AdvancedUsageKind.APPEND,
                AdvancedUsageKind.EXTEND,
                AdvancedUsageKind.SETDEFAULT,
                AdvancedUsageKind.DICT_UPDATE,
                AdvancedUsageKind.ATTRIBUTE_WRITE,
                AdvancedUsageKind.SUBSCRIPT_WRITE,
            }
        )

    def class_named(self, *, name: str) -> ClassFlowRecord | None:
        """Return a tracked class by simple name."""
        for record in self.classes:
            if record.name == name:
                return record
        return None

    def function_named(self, *, name: str) -> FunctionFlowRecord | None:
        """Return a tracked function or method by simple name."""
        for record in self.functions:
            if record.name == name:
                return record
        return None


@dataclass(slots=True)
class _ClassFlowMutable:
    """Mutable accumulator for class-flow data."""

    name: str
    scope: AdvancedScopeRef
    bases: tuple[str, ...]
    decorators: tuple[str, ...]
    init_method: FunctionDef | None = None
    new_method: FunctionDef | None = None
    class_variables: list[ClassVariableRecord] = field(default_factory=list)
    instance_variables: list[ClassVariableRecord] = field(default_factory=list)
    getters: dict[str, FunctionDef] = field(default_factory=dict)
    setters: dict[str, FunctionDef] = field(default_factory=dict)
    deleters: dict[str, FunctionDef] = field(default_factory=dict)

    def frozen(self) -> ClassFlowRecord:
        """Return the immutable class-flow record."""
        property_names: tuple[str, ...] = tuple(
            sorted({*self.getters, *self.setters, *self.deleters}),
        )
        properties: tuple[PropertyUsageRecord, ...] = tuple(
            PropertyUsageRecord(
                name=name,
                owner=self.name,
                getter=self.getters.get(name),
                setter=self.setters.get(name),
                deleter=self.deleters.get(name),
            )
            for name in property_names
        )
        return ClassFlowRecord(
            name=self.name,
            scope=self.scope,
            bases=self.bases,
            decorators=self.decorators,
            init_method=self.init_method,
            new_method=self.new_method,
            properties=properties,
            class_variables=tuple(self.class_variables),
            instance_variables=tuple(self.instance_variables),
        )


@dataclass(slots=True, frozen=True)
class AdvancedSemanticParseResult:
    """Parse result including model, graph, and advanced usage model."""

    model: ParsedSemanticModel
    graph: SemanticAstGraph
    advanced: AdvancedSemanticUsageModel


@dataclass(slots=True, frozen=True)
class EvidenceContribution:
    """One classified evidence item used by the solver."""

    evidence: TypeInferenceEvidence
    contribution: EvidenceContributionKind

    @property
    def type_hint(self) -> TypeExpression:
        """Return the semantic type hint carried by the evidence."""
        return self.evidence.type_hint


@dataclass(slots=True, frozen=True)
class IndexedSemanticGraphNode:
    """Compact node record used by the indexed semantic graph."""

    id: IndexedNodeId
    ast_node: AST
    kind: SemanticNodeKind
    scope_id: IndexedScopeId
    parent_id: IndexedNodeId | None
    name: str | None = None
    role: SemanticUsageKind | None = None

    def view(self, *, graph: IndexedSemanticAstGraph) -> IndexedNodeView:
        """Return a navigable view for this node."""
        return IndexedNodeView(graph=graph, node_id=self.id)


@dataclass(slots=True, frozen=True)
class IndexedSemanticGraphEdge:
    """Compact directed edge record used by the indexed graph."""

    id: IndexedEdgeId
    source_id: IndexedNodeId
    target_id: IndexedNodeId
    kind: SemanticEdgeKind
    label: str | None = None


@dataclass(slots=True, frozen=True)
class IndexedNodeCreate:
    """Creation payload for compact graph nodes."""

    ast_node: AST
    kind: SemanticNodeKind
    scope_id: IndexedScopeId
    parent_id: IndexedNodeId | None
    name: str | None = None
    role: SemanticUsageKind | None = None


@dataclass(slots=True)
class IndexedSemanticScope:
    """Compact lexical scope record with parent and symbol index."""

    id: IndexedScopeId
    kind: SemanticScopeKind
    name: str
    node_id: IndexedNodeId
    parent_id: IndexedScopeId | None
    symbols: dict[str, IndexedSymbolId] = field(default_factory=dict)

    def define(self, *, name: str, symbol_id: IndexedSymbolId) -> None:
        """Define a symbol in this scope."""
        self.symbols[name] = symbol_id


@dataclass(slots=True)
class IndexedSemanticSymbol:
    """Compact symbol record with direct usage and evidence ids."""

    id: IndexedSymbolId
    name: str
    kind: SemanticSymbolKind
    scope_id: IndexedScopeId
    definition_node_id: IndexedNodeId | None
    usage_node_ids: list[IndexedNodeId] = field(default_factory=list)
    evidence: list[TypeInferenceEvidence] = field(default_factory=list)

    def add_usage(self, *, node_id: IndexedNodeId) -> None:
        """Record one usage node id."""
        if node_id not in self.usage_node_ids:
            self.usage_node_ids.append(node_id)

    def add_evidence(self, *, evidence: TypeInferenceEvidence) -> None:
        """Record one type-evidence item."""
        if evidence not in self.evidence:
            self.evidence.append(evidence)


@dataclass(slots=True, frozen=True)
class IndexedValueUsage:
    """Precomputed symbol usage summary returned by fast queries."""

    symbol: IndexedSemanticSymbol
    definitions: tuple[IndexedNodeView, ...]
    usages: tuple[IndexedNodeView, ...]
    evidence: tuple[TypeInferenceEvidence, ...]


@dataclass(slots=True, frozen=True)
class IndexedNodeView:
    """Fast navigable view over an indexed semantic node."""

    graph: IndexedSemanticAstGraph
    node_id: IndexedNodeId

    @property
    def graph_node(self) -> IndexedSemanticGraphNode:
        """Return the underlying compact graph node."""
        return self.graph.node(node_id=self.node_id)

    @property
    def node(self) -> AST:
        """Return the underlying AST node."""
        return self.graph_node.ast_node

    @property
    def kind(self) -> SemanticNodeKind:
        """Return the semantic node kind."""
        return self.graph_node.kind

    @property
    def name(self) -> str | None:
        """Return the semantic node name."""
        return self.graph_node.name

    @property
    def scope_id(self) -> IndexedScopeId:
        """Return the lexical scope id."""
        return self.graph_node.scope_id

    @property
    def parent(self) -> IndexedNodeView | None:
        """Return the parent view."""
        parent_id: IndexedNodeId | None = self.graph.parent_id(
            node_id=self.node_id,
        )
        if parent_id is None:
            return None
        return self.graph.view(node_id=parent_id)

    @property
    def children(self) -> tuple[IndexedNodeView, ...]:
        """Return child views from the indexed adjacency list."""
        return tuple(
            self.graph.view(node_id=item)
            for item in self.graph.children_ids(node_id=self.node_id)
        )

    @property
    def descendants(self) -> tuple[IndexedNodeView, ...]:
        """Return all descendant views without recursive calls."""
        result: list[IndexedNodeView] = []
        stack: list[IndexedNodeId] = list(
            self.graph.children_ids(node_id=self.node_id),
        )
        while stack:
            current_id: IndexedNodeId = stack.pop()
            result.append(self.graph.view(node_id=current_id))
            stack.extend(self.graph.children_ids(node_id=current_id))
        return tuple(result)

    @property
    def outgoing_edges(self) -> tuple[IndexedSemanticGraphEdge, ...]:
        """Return outgoing edges."""
        return tuple(
            self.graph.edge(edge_id=item)
            for item in self.graph.outgoing_edge_ids(node_id=self.node_id)
        )

    @property
    def incoming_edges(self) -> tuple[IndexedSemanticGraphEdge, ...]:
        """Return incoming edges."""
        return tuple(
            self.graph.edge(edge_id=item)
            for item in self.graph.incoming_edge_ids(node_id=self.node_id)
        )

    @property
    def text(self) -> str:
        """Return source text for this AST node."""
        fixed_node: AST = fix_missing_locations(node=deepcopy(x=self.node))
        return unparse(ast_obj=fixed_node)

    def children_of_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[IndexedNodeView, ...]:
        """Return direct child views of one semantic kind."""
        return tuple(child for child in self.children if child.kind == kind)

    def descendants_of_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[IndexedNodeView, ...]:
        """Return descendant views of one semantic kind."""
        return tuple(item for item in self.descendants if item.kind == kind)


@dataclass(slots=True, frozen=True)
class IndexedSemanticGraphParseResult:
    """Parse result containing AST, model, and indexed graph."""

    source: str
    filename: str
    parsed: CommentAwareParseResult
    model: ParsedSemanticModel
    graph: IndexedSemanticAstGraph

    @property
    def query(self) -> IndexedGraphQuery:
        """Return a cache-aware query facade for the graph."""
        return IndexedGraphQuery(graph=self.graph)


@dataclass(slots=True, frozen=True)
class TraceablePathSegment:
    """One canonical path segment with stable sibling ordinal."""

    name: str
    kind: TraceablePathKind
    ordinal: int | None = None

    @property
    def text(self) -> str:
        """Return the stable textual form of this segment."""
        if self.ordinal is None:
            return self.name
        return f"{self.name}_{self.ordinal}"


@dataclass(slots=True, frozen=True)
class TraceableQualifiedPath:
    """Canonical path that uniquely identifies a semantic entity."""

    segments: tuple[TraceablePathSegment, ...]

    @classmethod
    def root(cls) -> TraceableQualifiedPath:
        """Return the root path."""
        return cls(
            segments=(
                TraceablePathSegment(
                    name="root",
                    kind=TraceablePathKind.ROOT,
                ),
            ),
        )

    @property
    def text(self) -> TraceablePathText:
        """Return the dotted canonical path text."""
        return ".".join(segment.text for segment in self.segments)

    @property
    def name(self) -> str:
        """Return the last segment name without ordinal."""
        return self.segments[-1].name

    @property
    def parent(self) -> TraceableQualifiedPath | None:
        """Return the parent path if this path is not root."""
        if len(self.segments) <= 1:
            return None
        return TraceableQualifiedPath(segments=self.segments[:-1])

    def child(
        self,
        *,
        name: str,
        kind: TraceablePathKind,
        ordinal: int | None = None,
    ) -> TraceableQualifiedPath:
        """Return a child path."""
        return TraceableQualifiedPath(
            segments=(
                *self.segments,
                TraceablePathSegment(name=name, kind=kind, ordinal=ordinal),
            ),
        )

    def startswith(self, *, other: TraceableQualifiedPath) -> bool:
        """Return whether this path is nested under another path."""
        if len(other.segments) > len(self.segments):
            return False
        return self.segments[: len(other.segments)] == other.segments


@dataclass(slots=True, frozen=True)
class TraceableScopeRecord:
    """Scope record with canonical path identity."""

    scope_id: IndexedScopeId
    name: str
    kind: SemanticScopeKind
    node_id: IndexedNodeId
    parent_scope_id: IndexedScopeId | None
    path: TraceableQualifiedPath


@dataclass(slots=True)
class TraceableSymbolRecord:
    """Symbol record keyed by a unique canonical path, not by name alone."""

    id: TraceableSymbolId
    indexed_symbol_id: IndexedSymbolId
    name: str
    kind: SemanticSymbolKind
    scope_id: IndexedScopeId
    path: TraceableQualifiedPath
    definition_node_id: IndexedNodeId | None
    usage_node_ids: list[IndexedNodeId] = field(default_factory=list)
    evidence: list[TypeInferenceEvidence] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Return the unique path text."""
        return self.path.text

    def add_usage(self, *, node_id: IndexedNodeId) -> None:
        """Add a usage node while preserving path identity."""
        if node_id not in self.usage_node_ids:
            self.usage_node_ids.append(node_id)

    def add_evidence(self, *, evidence: TypeInferenceEvidence) -> None:
        """Add one evidence item if it is not already present."""
        if evidence not in self.evidence:
            self.evidence.append(evidence)


@dataclass(slots=True, frozen=True)
class TraceableAttributeRecord:
    """Attribute path record, including instance/class ownership."""

    owner_path: TraceableQualifiedPath
    attribute_name: str
    path: TraceableQualifiedPath
    node_id: IndexedNodeId
    is_write: bool


@dataclass(slots=True, frozen=True)
class TraceableContainerSlotRecord:
    """Path record for a value placed in a container."""

    container_path: TraceableQualifiedPath
    slot_path: TraceableQualifiedPath
    value_path: TraceableQualifiedPath
    relation: TraceableValueRelation
    node_id: IndexedNodeId


@dataclass(slots=True, frozen=True)
class TraceableValueFlowRecord:
    """Path-based value-flow edge between traceable semantic entities."""

    source_path: TraceableQualifiedPath
    target_path: TraceableQualifiedPath
    relation: TraceableValueRelation
    source_node_id: IndexedNodeId | None
    target_node_id: IndexedNodeId | None
    label: str | None = None


@dataclass(slots=True)
class TraceableSiblingOrdinalState:
    """Allocate stable sibling ordinals."""

    _next_by_parent_and_name: dict[
        tuple[TraceablePathText, str, TraceablePathKind],
        int,
    ] = field(default_factory=dict)

    def next(
        self,
        *,
        parent: TraceableQualifiedPath,
        name: str,
        kind: TraceablePathKind,
    ) -> int:
        """Return the next ordinal for a sibling path segment."""
        key: tuple[TraceablePathText, str, TraceablePathKind] = (
            parent.text,
            name,
            kind,
        )
        ordinal: int = self._next_by_parent_and_name.get(key, 0) + 1
        self._next_by_parent_and_name[key] = ordinal
        return ordinal


@dataclass(slots=True, frozen=True)
class TraceableGraphParseResult:
    """Parse result with indexed graph and path-based identity index."""

    indexed: IndexedSemanticGraphParseResult
    trace: TraceablePathIndex

    @property
    def graph(self) -> IndexedSemanticAstGraph:
        """Return the indexed graph."""
        return self.indexed.graph

    @property
    def query(self) -> TraceableGraphQuery:
        """Return a path-aware query facade."""
        return TraceableGraphQuery(trace=self.trace)


@dataclass(slots=True, frozen=True)
class LocalImportInspectionConfig:
    """Configuration for inspecting project files and stub folders."""

    script_path: Path | None = None
    project_root: Path | None = None
    stub_roots: tuple[Path, ...] = ()
    inspect_project: bool = True
    inspect_stubs: bool = True
    inspect_relative: bool = True

    @property
    def script_directory(self) -> Path | None:
        """Return the directory of the current script, when known."""
        if self.script_path is None:
            return None
        return self.script_path.parent

    def normalized(self) -> LocalImportInspectionConfig:
        """Return a config with resolved path objects."""
        resolved_script_path: Path | None = None
        resolved_project_root: Path | None = None
        if self.script_path is not None:
            resolved_script_path = self.script_path.expanduser().resolve(
                strict=False,
            )
        if self.project_root is not None:
            resolved_project_root = self.project_root.expanduser().resolve(
                strict=False,
            )
        resolved_stub_roots: list[Path] = [
            stub_root.expanduser().resolve(strict=False)
            for stub_root in self.stub_roots
        ]
        return LocalImportInspectionConfig(
            script_path=resolved_script_path,
            project_root=resolved_project_root,
            stub_roots=tuple(resolved_stub_roots),
            inspect_project=self.inspect_project,
            inspect_stubs=self.inspect_stubs,
            inspect_relative=self.inspect_relative,
        )


@dataclass(slots=True, frozen=True)
class LocalImportPathCandidate:
    """One concrete file candidate for a semantic import source."""

    path: Path
    source: LocalImportInspectionSource
    is_stub: bool


@dataclass(slots=True, frozen=True)
class LocalImportResolution:
    """Resolved file candidates for an import source."""

    source: SemanticImportSource
    candidates: tuple[LocalImportPathCandidate, ...]

    @property
    def existing_candidates(self) -> tuple[LocalImportPathCandidate, ...]:
        """Return candidates whose files exist on disk."""
        return tuple(
            candidate
            for candidate in self.candidates
            if candidate.path.exists()
        )


@dataclass(slots=True, frozen=True)
class LocalImportSymbolRecord:
    """Symbol discovered by inspecting a local source or stub file."""

    name: str
    kind: LocalImportSymbolKind
    module: str | None
    file_path: Path
    node: AST
    source: LocalImportInspectionSource
    is_stub: bool

    @property
    def path_text(self) -> str:
        """Return a stable catalog path for this imported symbol."""
        module_text: str = self.module or "relative"
        return f"import:{module_text}.{self.name}"


@dataclass(slots=True, frozen=True)
class ImportInspectingTraceableGraphParseResult:
    """Traceable parse result enriched with local-import symbol inspection."""

    traceable: TraceableGraphParseResult
    import_symbols: LocalImportSymbolCatalog
    symbol_catalog: UnifiedSymbolCatalog

    @property
    def query(self) -> TraceableGraphQuery:
        """Return the path-aware graph query."""
        return self.traceable.query

    @property
    def trace(self) -> TraceablePathIndex:
        """Return the traceable path index."""
        return self.traceable.trace


@dataclass(slots=True, frozen=True)
class ImportInspectingEditingCollectorConfig:
    """Configuration for import-inspecting editing collectors."""

    trace: TraceablePathIndex | None = None
    symbol_catalog: UnifiedSymbolCatalog | None = None
    existing_nodes: tuple[ExistingTopNode, ...] = ()
    postponed_annotations: bool | None = None
    local_roots: tuple[str, ...] = ()
    existing_type_aliases: tuple[AstTypeAlias, ...] = ()


@dataclass(slots=True, frozen=True)
class AntFarmSymbolView:
    """Chainable, navigable view over one traceable or imported symbol."""

    record: CatalogSymbolRecord
    trace: TraceablePathIndex | None = None

    @property
    def name(self) -> str:
        """Return the symbol display name."""
        return self.record.name

    @property
    def path(self) -> str:
        """Return the stable ant-farm path for this symbol."""
        if isinstance(self.record, TraceableSymbolRecord):
            return self.record.text
        return self.record.path_text

    @property
    def kind(self) -> str:
        """Return the symbol kind as a stable string."""
        return self.record.kind.value

    @property
    def is_trace(self) -> bool:
        """Return whether this view wraps an in-file trace symbol."""
        return isinstance(self.record, TraceableSymbolRecord)

    @property
    def is_import(self) -> bool:
        """Return whether this view wraps an inspected import symbol."""
        return isinstance(self.record, LocalImportSymbolRecord)

    @property
    def definition(self) -> AST | None:
        """Return the AST node defining this symbol when available."""
        if isinstance(self.record, LocalImportSymbolRecord):
            return self.record.node
        if self.record.definition_node_id is None or self.trace is None:
            return None
        return self.trace.graph.node(
            node_id=self.record.definition_node_id,
        ).ast_node

    @property
    def node(self) -> AST | None:
        """Return the defining AST node alias."""
        return self.definition

    @property
    def definition_view(self) -> IndexedNodeView | None:
        """Return the indexed node view for the definition when available."""
        if not isinstance(self.record, TraceableSymbolRecord):
            return None
        if self.record.definition_node_id is None or self.trace is None:
            return None
        return self.trace.graph.view(node_id=self.record.definition_node_id)

    @property
    def usages(self) -> tuple[IndexedNodeView, ...]:
        """Return usage node views for trace symbols."""
        if not isinstance(self.record, TraceableSymbolRecord):
            return ()
        if self.trace is None:
            return ()
        return tuple(
            self.trace.graph.view(node_id=node_id)
            for node_id in self.record.usage_node_ids
        )

    @property
    def evidence(self) -> tuple[TypeInferenceEvidence, ...]:
        """Return collected type evidence for trace symbols."""
        if not isinstance(self.record, TraceableSymbolRecord):
            return ()
        return tuple(self.record.evidence)

    @property
    def children(self) -> AntFarmAstCollection:
        """Return child AST nodes of the defining node."""
        node: AST | None = self.definition
        if node is None:
            return AntFarmAstCollection(nodes=())
        return AntFarmAstCollection(nodes=tuple(iter_child_nodes(node=node)))

    @property
    def descendants(self) -> AntFarmAstCollection:
        """Return descendant AST nodes of the defining node."""
        node: AST | None = self.definition
        if node is None:
            return AntFarmAstCollection(nodes=())
        return AntFarmAstCollection(nodes=tuple(walk(node=node)))

    @property
    def text(self) -> str:
        """Return rendered source for the definition when available."""
        node: AST | None = self.definition
        if node is None:
            return self.path
        fixed_node: AST = fix_missing_locations(node=deepcopy(x=node))
        return unparse(ast_obj=fixed_node)

    def __call__(self, *, path: str | None = None) -> AntFarmAstCollection:
        """Return descendant AST nodes, optionally filtered by class name."""
        if path is None:
            return self.descendants
        selected_nodes: tuple[AST, ...] = tuple(
            node
            for node in self.descendants.nodes
            if type(node).__name__ == path
        )
        return AntFarmAstCollection(nodes=selected_nodes)


@dataclass(slots=True, frozen=True)
class AntFarmAstView:
    """Sliceable and navigable view over one AST node."""

    node: AST

    @property
    def text(self) -> str:
        """Return rendered source for this AST node."""
        fixed_node: AST = fix_missing_locations(node=deepcopy(x=self.node))
        return unparse(ast_obj=fixed_node)

    @property
    def children(self) -> AntFarmAstCollection:
        """Return direct child AST views."""
        return AntFarmAstCollection(
            nodes=tuple(iter_child_nodes(node=self.node)),
        )

    @property
    def descendants(self) -> AntFarmAstCollection:
        """Return descendant AST views."""
        return AntFarmAstCollection(nodes=tuple(walk(node=self.node)))

    @property
    def kind(self) -> str:
        """Return the concrete AST class name."""
        return type(self.node).__name__

    def __call__(self, *, kind: str | None = None) -> AntFarmAstCollection:
        """Return descendants, optionally filtered by AST class name."""
        if kind is None:
            return self.descendants
        return AntFarmAstCollection(
            nodes=tuple(
                node
                for node in self.descendants.nodes
                if type(node).__name__ == kind
            ),
        )


@dataclass(slots=True, frozen=True)
class AntFarmAstCollection:
    """Callable, sliceable, iterable AST node collection."""

    nodes: tuple[AST, ...]

    def __iter__(self) -> Iterator[AntFarmAstView]:
        """Iterate over AST node views."""
        return iter(tuple(AntFarmAstView(node=node) for node in self.nodes))

    def __len__(self) -> int:
        """Return collection length."""
        return len(self.nodes)

    def __bool__(self) -> bool:
        """Return whether the collection has nodes."""
        return bool(self.nodes)

    def __getitem__(
        self,
        index: CatalogSymbolSelector,
    ) -> AntFarmAstView | AntFarmAstCollection:
        """Return one AST view or a sliced AST collection."""
        if isinstance(index, slice):
            return AntFarmAstCollection(nodes=self.nodes[index])
        return AntFarmAstView(node=self.nodes[index])

    def __call__(self, *, kind: str | None = None) -> AntFarmAstCollection:
        """Filter AST nodes by concrete class name."""
        if kind is None:
            return self
        return AntFarmAstCollection(
            nodes=tuple(
                node for node in self.nodes if type(node).__name__ == kind
            ),
        )

    @property
    def text(self) -> tuple[str, ...]:
        """Return rendered source for all nodes."""
        return tuple(view.text for view in self)


@dataclass(slots=True, frozen=True)
class AntFarmQuery:
    """Ant-farm facade where every tunnel is chainable and navigable."""

    catalog: UnifiedSymbolCatalog
    trace: TraceablePathIndex

    @property
    def symbols(self) -> AntFarmSymbolCollection:
        """Return the chainable symbol tunnel."""
        return AntFarmSymbolCollection(
            records=self.catalog.all(),
            trace=self.trace,
        )

    @property
    def imports(self) -> AntFarmSymbolCollection:
        """Return the chainable import-symbol tunnel."""
        return self.symbols.imports()

    @property
    def graph(self) -> IndexedSemanticAstGraph:
        """Return the indexed graph backing this ant farm."""
        return self.trace.graph

    def __call__(
        self,
        *,
        path: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        lib: str | None = None,
    ) -> AntFarmSymbolCollection:
        """Filter the symbol tunnel directly from the query object."""
        return self.symbols(path=path, name=name, kind=kind, lib=lib)


@dataclass(slots=True, frozen=True)
class AntFarmParseResult:
    """Parse result exposing an ant-farm chainable query facade."""

    result: ImportInspectingTraceableGraphParseResult
    query: AntFarmQuery

    @property
    def trace(self) -> TraceablePathIndex:
        """Return the traceable path index."""
        return self.result.trace

    @property
    def symbol_catalog(self) -> UnifiedSymbolCatalog:
        """Return the underlying unified symbol catalog."""
        return self.result.symbol_catalog

    @property
    def traceable(self) -> TraceableGraphParseResult:
        """Return the original traceable parse result."""
        return self.result.traceable


@dataclass(slots=True, frozen=True)
class SwarmPropagationConfig:
    """Configuration for front/backward type-evidence swarming."""

    max_depth: int = 8
    confidence_decay: float = 0.82
    minimum_confidence: float = 0.05
    backward_decay: float = 0.62
    collapse_limit: int | None = None


@dataclass(slots=True, frozen=True)
class SwarmTypeEvidence:
    """One propagated type hint evidence item with confidence and path."""

    type_hint: TypeExpression
    polarity: SwarmEvidencePolarity
    confidence: float
    source_path: TraceablePathText
    current_path: TraceablePathText
    depth: int
    reason: str

    @property
    def key(self) -> tuple[str, SwarmEvidencePolarity, TraceablePathText]:
        """Return the deduplication key for this evidence."""
        return (self.type_hint.key(), self.polarity, self.source_path)

    def decayed(
        self,
        *,
        target_path: TraceablePathText,
        factor: float,
        reason: str,
    ) -> SwarmTypeEvidence:
        """Return a copy moved to another path with lower confidence."""
        return SwarmTypeEvidence(
            type_hint=self.type_hint,
            polarity=self.polarity,
            confidence=self.confidence * factor,
            source_path=self.source_path,
            current_path=target_path,
            depth=self.depth + 1,
            reason=reason,
        )

    def as_type_inference_evidence(self) -> TypeInferenceEvidence:
        """Convert to the evidence item understood by the solver."""
        evidence_kind: TypeEvidenceKind = TypeEvidenceKind.ASSIGNMENT_VALUE
        if self.polarity is SwarmEvidencePolarity.DECLARES:
            evidence_kind = TypeEvidenceKind.ANNOTATION
        elif self.polarity is SwarmEvidencePolarity.NARROWS:
            evidence_kind = TypeEvidenceKind.COMPARISON_LITERAL
        return TypeInferenceEvidence(
            kind=evidence_kind,
            type_hint=self.type_hint,
            node_id=self.current_path,
            confidence=self.confidence,
            reason=self.reason,
        )


@dataclass(slots=True, frozen=True)
class SwarmPropagationEdge:
    """Directed edge used by the swarming propagation algorithm."""

    source_path: TraceablePathText
    target_path: TraceablePathText
    kind: SwarmPropagationEdgeKind
    forward_confidence: float
    backward_confidence: float
    polarity: SwarmEvidencePolarity
    label: str | None = None

    def reversed_edge(self) -> SwarmPropagationEdge:
        """Return the backward propagation view of this edge."""
        return SwarmPropagationEdge(
            source_path=self.target_path,
            target_path=self.source_path,
            kind=self.kind,
            forward_confidence=self.backward_confidence,
            backward_confidence=self.forward_confidence,
            polarity=self.polarity,
            label=self.label,
        )


@dataclass(slots=True)
class SwarmPathState:
    """All propagated evidence associated with one traceable path."""

    path: TraceablePathText
    items: list[SwarmTypeEvidence] = field(default_factory=list)

    def add(self, *, evidence: SwarmTypeEvidence) -> bool:
        """Add evidence, keeping the highest-confidence duplicate."""
        for index, item in enumerate(iterable=self.items):
            if item.key != evidence.key:
                continue
            if item.confidence >= evidence.confidence:
                return False
            self.items[index] = evidence
            return True
        self.items.append(evidence)
        return True

    def solved(self) -> TypeExpression:
        """Solve all path evidence into one semantic type expression."""
        solver_evidence: tuple[TypeInferenceEvidence, ...] = tuple(
            item.as_type_inference_evidence() for item in self.items
        )
        return TypeEvidenceSolver().solve(evidence=solver_evidence)

    @property
    def confidence(self) -> float:
        """Return the strongest confidence associated with this path."""
        if not self.items:
            return 0.0
        return max(item.confidence for item in self.items)


@dataclass(slots=True, frozen=True)
class SwarmProtocolSuggestion:
    """Protocol synthesized from swarm usage."""

    name: str
    type_hint: TypeExpression
    methods: tuple[MethodSpec, ...]
    reason: str

    @property
    def spec(self) -> ProtocolSpec:
        """Return the semantic protocol spec for this suggestion."""
        return ProtocolSpec(
            name=self.name,
            methods=self.methods,
            docstring=self.reason,
        )


@dataclass(slots=True, frozen=True)
class SwarmInferenceResult:
    """Solved result for a swarming inference run."""

    graph: SwarmPropagationGraph
    config: SwarmPropagationConfig

    def type_for(self, *, path: TraceablePathText) -> TypeExpression | None:
        """Return the inferred type for one path."""
        return self.graph.solve(path=path)

    def state_for(self, *, path: TraceablePathText) -> SwarmPathState | None:
        """Return raw propagated state for one path."""
        return self.graph.state(path=path)

    @property
    def protocol_suggestions(self) -> tuple[SwarmProtocolSuggestion, ...]:
        """Return synthesized protocol suggestions."""
        return tuple(self.graph.protocol_suggestions.values())


@dataclass(slots=True, frozen=True)
class SwarmSymbolView:
    """Chainable view over one path's swarming inference state."""

    path: TraceablePathText
    result: SwarmInferenceResult

    @property
    def type_hint(self) -> TypeExpression | None:
        """Return the solved type hint for this path."""
        return self.result.type_for(path=self.path)

    @property
    def evidence(self) -> tuple[SwarmTypeEvidence, ...]:
        """Return propagated evidence for this path."""
        state: SwarmPathState | None = self.result.state_for(path=self.path)
        if state is None:
            return ()
        return tuple(state.items)

    @property
    def confidence(self) -> float:
        """Return the strongest confidence for this path."""
        state: SwarmPathState | None = self.result.state_for(path=self.path)
        if state is None:
            return 0.0
        return state.confidence


@dataclass(slots=True, frozen=True)
class SwarmAntFarmParseResult:
    """Ant-farm result extended with bidirectional swarm inference."""

    ant_farm: AntFarmParseResult
    swarm_result: SwarmInferenceResult

    @property
    def query(self) -> AntFarmQuery:
        """Return the regular ant-farm query facade."""
        return self.ant_farm.query

    @property
    def swarm(self) -> SwarmResultQuery:
        """Return the swarming inference query facade."""
        return SwarmResultQuery(result=self.swarm_result)


@dataclass(slots=True, frozen=True)
class TypeshedParameterModel:
    """One parsed parameter from a typeshed or local stub signature."""

    name: str
    type_hint: TypeExpression
    kind: TypeshedParameterKind
    has_default: bool = False


@dataclass(slots=True, frozen=True)
class TypeshedSignatureModel:
    """One function or method signature known by the stub catalog."""

    owner: str
    name: str
    parameters: tuple[TypeshedParameterModel, ...]
    returns: TypeExpression
    module: str
    confidence: float
    source: str

    @property
    def qualified_name(self) -> str:
        """Return a stable qualified signature name."""
        if self.owner:
            return f"{self.owner}.{self.name}"
        return self.name


@dataclass(slots=True, frozen=True)
class TypeshedClassModel:
    """Parsed class-level signature information from a stub module."""

    name: str
    methods: tuple[TypeshedSignatureModel, ...]
    module: str
    source: str


@dataclass(slots=True, frozen=True)
class TypeshedModuleModel:
    """Parsed module-level signature information from a stub file."""

    module: str
    classes: tuple[TypeshedClassModel, ...]
    functions: tuple[TypeshedSignatureModel, ...]
    source: str


@dataclass(slots=True, frozen=True)
class TypeshedLookupConfig:
    """Configuration for loading typeshed, local stubs, and fallback rules."""

    typeshed_root: Path | None = None
    stdlib_root: Path | None = None
    stub_roots: tuple[Path, ...] = ()
    include_builtin_fallbacks: bool = True
    include_operator_fallbacks: bool = True


@dataclass(slots=True, frozen=True)
class MarkovInferenceStep:
    """One step in a confidence-decayed inference explanation chain."""

    source_path: TraceablePathText
    target_path: TraceablePathText
    edge_label: str
    confidence: float
    type_hint: TypeExpression


@dataclass(slots=True, frozen=True)
class MarkovConflictWarning:
    """Conflict warning produced while solving a path's evidence."""

    path: TraceablePathText
    message: str
    candidate_types: tuple[TypeExpression, ...]
    confidence: float


@dataclass(slots=True, frozen=True)
class MarkovInferenceExplanation:
    """Human-readable inference explanation with confidence and conflicts."""

    path: TraceablePathText
    type_hint: TypeExpression | None
    confidence: float
    steps: tuple[MarkovInferenceStep, ...]
    conflicts: tuple[MarkovConflictWarning, ...]

    def text(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render this explanation as text."""
        type_text: str = self._type_text(renderer=renderer)
        step_lines: tuple[str, ...] = tuple(
            self._step_text(step=step, renderer=renderer)
            for step in self.steps
        )
        conflict_lines: tuple[str, ...] = tuple(
            self._conflict_text(conflict=conflict, renderer=renderer)
            for conflict in self.conflicts
        )
        lines: tuple[str, ...] = (
            f"{self.path}: {type_text} confidence={self.confidence:.3f}",
            *step_lines,
            *conflict_lines,
        )
        return "\n".join(lines)

    def _type_text(self, *, renderer: TypeHintStringRenderer) -> str:
        """Return solved type text."""
        if self.type_hint is None:
            return "<unknown>"
        return renderer.render(value=self.type_hint)

    def _step_text(
        self,
        *,
        step: MarkovInferenceStep,
        renderer: TypeHintStringRenderer,
    ) -> str:
        """Render one explanation step."""
        return (
            f"  <- {step.source_path} via {step.edge_label}: "
            f"{renderer.render(value=step.type_hint)} "
            f"p={step.confidence:.3f}"
        )

    def _conflict_text(
        self,
        *,
        conflict: MarkovConflictWarning,
        renderer: TypeHintStringRenderer,
    ) -> str:
        """Render one conflict warning."""
        candidate_text: str = ", ".join(
            renderer.render(value=item) for item in conflict.candidate_types
        )
        return f"  ! {conflict.message}: {candidate_text}"


@dataclass(slots=True, frozen=True)
class TypeshedBackedSwarmResult:
    """Swarm inference result enriched with typeshed signatures."""

    base: SwarmInferenceResult
    catalog: TypeshedSignatureCatalog
    explanations: tuple[MarkovInferenceExplanation, ...]
    warnings: tuple[MarkovConflictWarning, ...]

    def type_for(self, *, path: TraceablePathText) -> TypeExpression | None:
        """Return inferred type for a path."""
        return self.base.type_for(path=path)

    def explanation_for(
        self,
        *,
        path: TraceablePathText,
    ) -> MarkovInferenceExplanation | None:
        """Return explanation for one path when available."""
        for explanation in self.explanations:
            if explanation.path == path:
                return explanation
        return None


@dataclass(slots=True, frozen=True)
class TypeshedBackedSwarmParseResult:
    """Parse result with ant farm, trace graph, and typeshed-backed swarm."""

    ant_farm: AntFarmParseResult
    swarm_result: TypeshedBackedSwarmResult

    @property
    def query(self) -> AntFarmQuery:
        """Return the ant-farm query."""
        return self.ant_farm.query

    @property
    def swarm(self) -> TypeshedBackedSwarmQuery:
        """Return the typeshed-backed swarm query."""
        return TypeshedBackedSwarmQuery(result=self.swarm_result)


@dataclass(frozen=True, slots=True)
class TypeCandidate:
    """One type candidate with confidence and explanation."""

    type_hint: TypeExpression
    confidence: float
    distance: int
    explanation: str

    def decayed(self, *, decay: float) -> TypeCandidate:
        """Return a decayed candidate."""
        return TypeCandidate(
            type_hint=self.type_hint,
            confidence=self.confidence * decay,
            distance=self.distance + 1,
            explanation=self.explanation,
        )


@dataclass(frozen=True, slots=True)
class TypeContract:
    """A directed type contract between two semantic paths."""

    source: QualifiedPath
    target: QualifiedPath
    relation: ContractRelation
    polarity: ContractPolarity
    confidence: float
    decay: float
    explanation: str

    def reversed(self, *, decay: float) -> TypeContract:
        """Return the reverse contract for backward swarming."""
        return TypeContract(
            source=self.target,
            target=self.source,
            relation=self.relation,
            polarity=self.polarity,
            confidence=self.confidence * decay,
            decay=self.decay * decay,
            explanation=f"backward from {self.explanation}",
        )


@dataclass(frozen=True, slots=True)
class TypeConflict:
    """A conflict between two type candidates."""

    path: QualifiedPath
    left: TypeExpression
    right: TypeExpression
    confidence: float
    explanation: str


@dataclass(slots=True)
class TypeBelief:
    """A local belief distribution for one path."""

    path: QualifiedPath
    candidates: dict[str, TypeCandidate]
    conflicts: list[TypeConflict]

    @classmethod
    def empty(cls, *, path: QualifiedPath) -> TypeBelief:
        """Create an empty belief."""
        return cls(path=path, candidates={}, conflicts=[])

    def add(
        self,
        *,
        candidate: TypeCandidate,
        polarity: ContractPolarity,
    ) -> bool:
        """Add or combine a candidate and return whether it changed."""
        if polarity is ContractPolarity.INTERSECTION:
            return self._intersect(candidate=candidate)
        if polarity is ContractPolarity.CONFLICT:
            return self._conflict(candidate=candidate)
        return self._union(candidate=candidate)

    def entropy(self) -> float:
        """Return Shannon entropy for this belief."""
        total: float = sum(
            item.confidence for item in self.candidates.values()
        )
        if total <= 0.0:
            return 0.0
        entropy: float = 0.0
        for candidate in self.candidates.values():
            probability: float = candidate.confidence / total
            if probability > 0.0:
                entropy -= probability * log2(probability)
        return entropy

    def selected(self) -> TypeExpression:
        """Return the best normalized type expression."""
        if not self.candidates:
            return Types.object
        ordered: list[TypeCandidate] = sorted(
            self.candidates.values(),
            key=lambda candidate: (
                -candidate.confidence,
                candidate.type_hint.key(),
            ),
        )
        return ordered[0].type_hint

    def _union(self, *, candidate: TypeCandidate) -> bool:
        """Union a candidate into the belief."""
        key: str = candidate.type_hint.key()
        current: TypeCandidate | None = self.candidates.get(key)
        if current is None or candidate.confidence > current.confidence:
            self.candidates[key] = candidate
            return True
        return False

    def _intersect(self, *, candidate: TypeCandidate) -> bool:
        """Intersect a narrowing candidate with existing belief."""
        if not self.candidates:
            self.candidates[candidate.type_hint.key()] = candidate
            return True
        algebra: TypeExpressionAlgebra = TypeExpressionAlgebra()
        changed: bool = False
        updated: dict[str, TypeCandidate] = {}
        for existing in self.candidates.values():
            narrowed: TypeExpression = algebra.intersect(
                left=existing.type_hint,
                right=candidate.type_hint,
            )
            narrowed_confidence: float = min(
                existing.confidence,
                candidate.confidence,
            )
            narrowed_candidate: TypeCandidate = TypeCandidate(
                type_hint=narrowed,
                confidence=narrowed_confidence,
                distance=max(existing.distance, candidate.distance),
                explanation=(
                    f"{existing.explanation}; narrowed by "
                    f"{candidate.explanation}"
                ),
            )
            updated[narrowed.key()] = narrowed_candidate
            changed = changed or narrowed.key() != existing.type_hint.key()
        self.candidates = updated
        return changed

    def _conflict(self, *, candidate: TypeCandidate) -> bool:
        """Record conflicts between the new candidate and current choices."""
        for current in self.candidates.values():
            if current.type_hint.key() != candidate.type_hint.key():
                self.conflicts.append(
                    TypeConflict(
                        path=self.path,
                        left=current.type_hint,
                        right=candidate.type_hint,
                        confidence=min(
                            current.confidence,
                            candidate.confidence,
                        ),
                        explanation=candidate.explanation,
                    ),
                )
        return bool(self.candidates)


@dataclass(frozen=True, slots=True)
class ContractEntropySnapshot:
    """Entropy snapshot for one negotiation step."""

    iteration: int
    total_entropy: float
    changed_beliefs: int


@dataclass(frozen=True, slots=True)
class ContractNegotiationConfig:
    """Configuration for contract propagation."""

    max_iterations: int = 24
    confidence_epsilon: float = 0.0001
    entropy_epsilon: float = 0.0001
    minimum_confidence: float = 0.02
    forward_decay: float = 0.86
    backward_decay: float = 0.63
    max_propagation_events: int = 10000
    wormhole_confidence_delta: float = 0.000001


@dataclass(frozen=True, slots=True)
class ContractNegotiationResult:
    """Result of contract propagation."""

    beliefs: tuple[TypeBelief, ...]
    snapshots: tuple[ContractEntropySnapshot, ...]
    conflicts: tuple[TypeConflict, ...]

    def belief(self, *, path: QualifiedPath) -> TypeBelief | None:
        """Return a belief by path."""
        requested_path: str = path.text()
        for belief in self.beliefs:
            if belief.path.text() == requested_path:
                return belief
        return None


@dataclass(frozen=True, slots=True)
class ContractGraphNode:
    """One graph node with stable path identity.

    Attributes:
        node_id: Unique numeric identifier assigned by the graph.
        path: Qualified path identifying the entity within the module.
        kind: Category of the node (see :class:`GraphNodeKind`).
        name: Human-readable name of the entity (e.g. function or
            variable name).
        ast_node: Optional reference to the originating AST node.

    """

    node_id: int
    path: QualifiedPath
    kind: GraphNodeKind
    name: str
    ast_node: AST | None


@dataclass(frozen=True, slots=True)
class ContractGraphEdge:
    """One graph edge backed by a type contract.

    Attributes:
        edge_id: Unique numeric identifier for the edge.
        contract: The type contract associated with this edge.  The
            contract describes how type information flows from source to
            target and carries polarity and decay factors.

    """

    edge_id: int
    contract: TypeContract  # Forward declaration for type checker


@dataclass(frozen=True, slots=True)
class FunctionTrace:
    """Trace metadata for a function or method.

    Captures the path to the function, a reference to the AST node,
    lists of argument and return paths, and any decorators applied.
    """

    path: QualifiedPath
    node: FunctionNode
    argument_paths: tuple[QualifiedPath, ...]
    return_path: QualifiedPath
    decorators: tuple[QualifiedPath, ...]


@dataclass(frozen=True, slots=True)
class ClassTrace:
    """Trace metadata for a class.

    Captures the path to the class, a reference to the AST node,
    information about base classes and decorators, and paths for
    ``__init__`` and ``__new__`` methods and the metaclass.
    """

    path: QualifiedPath
    node: ClassDef
    bases: tuple[QualifiedPath, ...]
    decorators: tuple[QualifiedPath, ...]
    init_path: QualifiedPath | None
    new_path: QualifiedPath | None
    metaclass_path: QualifiedPath | None


@dataclass(slots=True)
class ContractGraph:
    """Fast traceable graph with contract edges and type seeds."""

    nodes: dict[str, ContractGraphNode] = field(default_factory=dict)
    edges: list[ContractGraphEdge] = field(default_factory=list)
    outgoing: dict[str, list[int]] = field(default_factory=dict)
    incoming: dict[str, list[int]] = field(default_factory=dict)
    seeds: dict[str, list[TypeCandidate]] = field(default_factory=dict)
    functions: dict[str, FunctionTrace] = field(default_factory=dict)
    classes: dict[str, ClassTrace] = field(default_factory=dict)
    ast_to_path: dict[int, QualifiedPath] = field(default_factory=dict)
    class_assigned_attributes: dict[str, set[str]] = field(
        default_factory=dict,
    )

    def add_node(
        self,
        *,
        path: QualifiedPath,
        kind: GraphNodeKind,
        name: str,
        ast_node: AST | None,
    ) -> ContractGraphNode:
        """Add or return a graph node."""
        key: str = path.text()
        existing: ContractGraphNode | None = self.nodes.get(key)
        if existing is not None:
            if ast_node is not None:
                self.ast_to_path[id(ast_node)] = existing.path
            return existing
        node: ContractGraphNode = ContractGraphNode(
            node_id=len(self.nodes),
            path=path,
            kind=kind,
            name=name,
            ast_node=ast_node,
        )
        self.nodes[key] = node
        if ast_node is not None:
            self.ast_to_path[id(ast_node)] = path
        return node

    def add_seed(
        self,
        *,
        path: QualifiedPath,
        type_hint: TypeExpression,
        confidence: float,
        explanation: str,
    ) -> None:
        """Add a type candidate seed."""
        key: str = path.text()
        self.seeds.setdefault(key, []).append(
            TypeCandidate(
                type_hint=type_hint,
                confidence=confidence,
                distance=0,
                explanation=explanation,
            ),
        )

    def add_contract(self, *, contract: TypeContract) -> None:
        """Add a contract edge."""
        edge: ContractGraphEdge = ContractGraphEdge(
            edge_id=len(self.edges),
            contract=contract,
        )
        self.edges.append(edge)
        self.outgoing.setdefault(contract.source.text(), []).append(
            edge.edge_id,
        )
        self.incoming.setdefault(contract.target.text(), []).append(
            edge.edge_id,
        )

    def path_for_node(self, *, node: AST) -> QualifiedPath | None:
        """Return the path for an AST node."""
        return self.ast_to_path.get(id(node))


@dataclass(frozen=True, slots=True)
class AdvancedFeatureRecord:
    """One inspectable advanced Python feature occurrence."""

    kind: AdvancedFeatureKind
    path: QualifiedPath
    name: str
    ast_node: AST
    details: tuple[str, ...] = ()


@dataclass(slots=True)
class AdvancedFeatureCatalog:
    """Iterable catalog of advanced feature records."""

    records: list[AdvancedFeatureRecord] = field(default_factory=list)

    def add(
        self,
        *,
        kind: AdvancedFeatureKind,
        path: QualifiedPath,
        name: str,
        ast_node: AST,
        details: tuple[str, ...] = (),
    ) -> None:
        """Append a feature record."""
        self.records.append(
            AdvancedFeatureRecord(
                kind=kind,
                path=path,
                name=name,
                ast_node=ast_node,
                details=details,
            ),
        )

    def __iter__(self) -> Iterator[AdvancedFeatureRecord]:
        """Iterate over feature records."""
        return iter(self.records)

    def by_kind(
        self,
        *,
        kind: AdvancedFeatureKind,
    ) -> tuple[AdvancedFeatureRecord, ...]:
        """Return records of a specific kind."""
        return tuple(record for record in self.records if record.kind is kind)

    def by_name(self, *, name: str) -> tuple[AdvancedFeatureRecord, ...]:
        """Return records with a specific feature name."""
        return tuple(record for record in self.records if record.name == name)


@dataclass(frozen=True, slots=True)
class AdvancedFeatureAnalysisResult:
    """Result of the advanced feature pass."""

    catalog: AdvancedFeatureCatalog


@dataclass(frozen=True, slots=True)
class SyntheticStepCostProfile:
    """Penalty and reward values for synthesis operations."""

    attribute_setattr_rewrite: float = 14.0
    cast_wrap: float = 10.0
    override: float = 7.0
    protocol: float = 5.0
    typevar: float = 3.0
    paramspec: float = 3.0
    direct_annotation: float = 0.15
    type_alias_reuse_reward: float = 3.5
    existing_type_reuse_reward: float = 2.0

    def cost_for(self, *, kind: SyntheticStepKind) -> float:
        """Return signed cost for one synthesis step."""
        costs: dict[SyntheticStepKind, float] = {}
        costs[SyntheticStepKind.ATTRIBUTE_SETATTR_REWRITE] = (
            self.attribute_setattr_rewrite
        )
        costs[SyntheticStepKind.CAST_WRAP] = self.cast_wrap
        costs[SyntheticStepKind.OVERRIDE] = self.override
        costs[SyntheticStepKind.PROTOCOL] = self.protocol
        costs[SyntheticStepKind.TYPEVAR] = self.typevar
        costs[SyntheticStepKind.PARAMSPEC] = self.paramspec
        costs[
            SyntheticStepKind.TYPE_ALIAS_REUSE
        ] = -self.type_alias_reuse_reward
        costs[
            SyntheticStepKind.EXISTING_TYPE_REUSE
        ] = -self.existing_type_reuse_reward
        costs[SyntheticStepKind.DIRECT_ANNOTATION] = self.direct_annotation
        return costs[kind]


@dataclass(frozen=True, slots=True)
class TypeHintObjectiveConfig:
    """Configuration for collective type-hint optimization."""

    coverage_reward: float = 16.0
    confidence_weight: float = 10.0
    narrowness_weight: float = 8.0
    entropy_penalty: float = 2.0
    conflict_penalty: float = 5.0
    synthetic_cost_weight: float = 1.0
    minimum_emit_score: float = 0.0
    fallback_to_object: bool = True
    object_fallback_confidence: float = 0.01
    costs: SyntheticStepCostProfile = field(
        default_factory=SyntheticStepCostProfile,
    )


@dataclass(frozen=True, slots=True)
class ExistingTypeRegistry:
    """Known types and aliases that should be rewarded when reused."""

    existing_type_keys: frozenset[str] = frozenset()
    existing_alias_keys: frozenset[str] = frozenset()

    @classmethod
    def empty(cls) -> ExistingTypeRegistry:
        """Return an empty registry."""
        return cls()

    def is_existing_type(self, *, type_hint: TypeExpression) -> bool:
        """Return whether a type expression is already available."""
        return type_hint.key() in self.existing_type_keys

    def is_existing_alias(self, *, type_hint: TypeExpression) -> bool:
        """Return whether a type expression is an existing alias."""
        return type_hint.key() in self.existing_alias_keys


@dataclass(frozen=True, slots=True)
class SynthesisStep:
    """One synthetic operation contributing to a plan score."""

    kind: SyntheticStepKind
    explanation: str


@dataclass(frozen=True, slots=True)
class TypeHintCandidatePlan:
    """Scored candidate type-hint synthesis plan for one entity."""

    path: QualifiedPath
    type_hint: TypeExpression
    confidence: float
    entropy: float
    narrowness: float
    steps: tuple[SynthesisStep, ...]
    score: float
    explanation: str

    @property
    def should_emit(self) -> bool:
        """Return whether this candidate is useful enough to emit."""
        return self.score >= 0.0


@dataclass(frozen=True, slots=True)
class TypeHintObjectiveDecision:
    """Objective decision for one path."""

    path: QualifiedPath
    selected: TypeHintCandidatePlan | None
    alternatives: tuple[TypeHintCandidatePlan, ...]
    warnings: tuple[str, ...]

    @property
    def is_covered(self) -> bool:
        """Return whether this path has a selected type hint."""
        return self.selected is not None and self.selected.should_emit


@dataclass(frozen=True, slots=True)
class TypeHintObjectiveReport:
    """Collective objective result over all inferable entities."""

    decisions: tuple[TypeHintObjectiveDecision, ...]
    total_score: float
    covered_entities: int
    total_entities: int
    warnings: tuple[str, ...]

    @property
    def coverage_ratio(self) -> float:
        """Return covered/total entity ratio."""
        if self.total_entities == 0:
            return 0.0
        return self.covered_entities / self.total_entities

    def decision(
        self,
        *,
        path: QualifiedPath,
    ) -> TypeHintObjectiveDecision | None:
        """Return the decision for a path."""
        requested_path: str = path.text()
        for decision in self.decisions:
            if decision.path.text() == requested_path:
                return decision
        return None


@dataclass(frozen=True, slots=True)
class AntMessage:
    """One propagation message moving through the contract graph."""

    path: QualifiedPath
    candidate: TypeCandidate
    polarity: ContractPolarity


@dataclass(slots=True, frozen=True)
class AnnotationTraversalContext:
    """Context needed while recursively annotating statements."""

    result: ContractAnalysisResult
    resolver: TypeExpressionResolver
    function_paths: dict[int, QualifiedPath]
    class_paths: dict[int, QualifiedPath]


@dataclass(frozen=True, slots=True)
class ContractExplanation:
    """Human-readable explanation for one inferred path."""

    path: QualifiedPath
    selected: TypeExpression
    entropy: float
    lines: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContractAnalysisResult:
    """Complete analysis result."""

    source: str
    module: Module
    graph: ContractGraph
    negotiation: ContractNegotiationResult
    objective: TypeHintObjectiveReport
    advanced: AdvancedFeatureAnalysisResult

    @property
    def query(self) -> ContractQuery:
        """Return a chainable query facade."""
        return ContractQuery(result=self)


class PathIndexAllocator:
    """Allocate stable ordered indices for duplicate path children."""

    def __init__(self) -> None:
        """Initialize the allocator."""
        self._counts: dict[tuple[str, PathSegmentKind, str], int] = {}

    def child(
        self,
        *,
        parent: QualifiedPath,
        kind: PathSegmentKind,
        name: str,
    ) -> QualifiedPath:
        """Allocate and return a child path."""
        key: tuple[str, PathSegmentKind, str] = (parent.text(), kind, name)
        next_index: int = self._counts.get(key, 0) + 1
        self._counts[key] = next_index
        return parent.child(kind=kind, name=name, index=next_index)


class SemanticCodegenError(ValueError):
    """Raised when semantic AST generation receives invalid input."""


class IdentifierValidator:
    """Validate Python identifiers used by generated nodes."""

    def validate_identifier(self, *, name: str, label: str) -> None:
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


class ImportPlacementPolicy:
    """Decide final landing for usage-aware imports."""

    def __init__(self, *, postponed_annotations: bool) -> None:
        """Initialize the import placement policy."""
        self._postponed_annotations: bool = postponed_annotations

    def landing_for(self, *, requirement: ImportRequirement) -> ImportLanding:
        """Return final landing for an import requirement."""
        places: set[ImportUsePlace] = {use.place for use in requirement.uses}
        if places & ImportPlacementTables.runtime_places:
            return ImportLanding.TOP_LEVEL
        if places <= ImportPlacementTables.type_checking_only_places:
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
        """Initialize the grouper."""
        self._local_roots: frozenset[str] = frozenset(local_roots)

    def group_for(self, *, module: str | None, level: int) -> ImportGroup:
        """Return the PEP 8 group for one import source."""
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
        """Build import nodes for each PEP 8 group."""
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

    def _group_sort_key(self, group: ImportFromGroup) -> tuple[int, str]:
        """Return a stable sort key for import groups."""
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
        """Initialize the collector."""
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
        """Reserve a generated declaration name."""
        self._reserved_generated_names.add(name)

    def require_from_source(
        self,
        *,
        source: SemanticImportSource,
        use: ImportUseSite,
    ) -> Name:
        """Require a semantic import source and return its local name node."""
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
        """Require an absolute ``from ... import ...`` source."""
        return self.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=module_parts,
                imported_name=name,
            ),
            use=use,
        )

    def build_import_nodes(self) -> GeneratedImportGroups:
        """Build generated imports grouped by PEP 8 sections."""
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
        """Return all generated import nodes."""
        return self.build_import_nodes().all_import_nodes

    def _build_type_checking_block(
        self,
        *,
        nodes: tuple[stmt, ...],
    ) -> If | None:
        """Build the optional ``if TYPE_CHECKING`` block."""
        if not nodes or self._type_checking_name is None:
            return None
        return If(
            test=Name(id=self._type_checking_name, ctx=Load()),
            body=list(nodes),
            orelse=[],
        )

    def _ensure_type_checking_name(self) -> str:
        """Ensure the ``TYPE_CHECKING`` guard name exists."""
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
        """Return or create a requirement from a semantic source."""
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
        """Select the local imported name for a source."""
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
        """Return whether an imported name is available without aliasing."""
        return (
            not self._symbols.is_name_available(name=name)
            and name not in self._reserved_generated_names
            and name not in self._generated_local_names
        )

    def _alias_for(self, *, module: str | None, name: str) -> str:
        """Create a deterministic alias for a colliding import."""
        raw_alias: str = f"{module or 'relative'}_{name}"
        return sub(pattern=r"\W+", repl="_", string=raw_alias).strip("_")

    def _free_generated_name(self, *, preferred: str) -> str:
        """Return a collision-free generated name."""
        if self._is_free_generated_name(name=preferred):
            return preferred
        index: int = 1
        while True:
            candidate: str = f"{preferred}_{index}"
            if self._is_free_generated_name(name=candidate):
                return candidate
            index += 1

    def _is_free_generated_name(self, *, name: str) -> bool:
        """Return whether a generated name is free."""
        return (
            not self._symbols.is_name_available(name=name)
            and name not in self._reserved_generated_names
            and name not in self._generated_local_names
        )

    def _split_groups(
        self,
    ) -> tuple[tuple[ImportFromGroup, ...], tuple[ImportFromGroup, ...]]:
        """Split requirements into top-level and TYPE_CHECKING groups."""
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

    def _dict_to_groups(
        self,
        *,
        items: dict[tuple[str | None, int], list[ImportAliasSpec]],
    ) -> tuple[ImportFromGroup, ...]:
        """Convert grouped aliases into sorted import groups."""
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

    def _detect_postponed_annotations(
        self,
        *,
        import_nodes: Iterable[Import | ImportFrom],
    ) -> bool:
        """Detect ``from __future__ import annotations``."""
        for node in import_nodes:
            if not isinstance(node, ImportFrom):
                continue
            if node.module != "__future__":
                continue
            if any(item.name == "annotations" for item in node.names):
                return True
        return False


@dataclass(slots=True, frozen=True)
class TypeVarRef(TypeExpression):
    """Reference a generated TypeVar."""

    spec: TypeVarSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the TypeVar name."""
        resolver.validate_identifier(name=self.spec.name, label="TypeVar")
        return Name(id=self.spec.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the TypeVar name."""
        renderer.validate_identifier(name=self.spec.name, label="TypeVar")
        return self.spec.name

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"typevar:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecRef(TypeExpression):
    """Reference a generated ParamSpec."""

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the ParamSpec name."""
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Name(id=self.spec.name, ctx=Load())

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the ParamSpec name."""
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return self.spec.name

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"paramspec:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecArgsRef(TypeExpression):
    """Reference ``P.args``."""

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``P.args``."""
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Attribute(
            value=Name(id=self.spec.name, ctx=Load()),
            attr="args",
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``P.args``."""
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return f"{self.spec.name}.args"

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"paramspec-args:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class ParamSpecKwargsRef(TypeExpression):
    """Reference ``P.kwargs``."""

    spec: ParamSpecSpec

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``P.kwargs``."""
        resolver.validate_identifier(name=self.spec.name, label="ParamSpec")
        return Attribute(
            value=Name(id=self.spec.name, ctx=Load()),
            attr="kwargs",
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render ``P.kwargs``."""
        renderer.validate_identifier(name=self.spec.name, label="ParamSpec")
        return f"{self.spec.name}.kwargs"

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"paramspec-kwargs:{self.spec.name}"


@dataclass(slots=True, frozen=True)
class GenericTypeRef(TypeExpression):
    """Reference a generic type expression."""

    origin: TypeExpression
    arguments: tuple[TypeExpression, ...]

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a subscripted type node."""
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
        """Render a generic type expression."""
        origin_text: str = self.origin.render(renderer=renderer)
        argument_text: str = ", ".join(
            argument.render(renderer=renderer) for argument in self.arguments
        )
        return f"{origin_text}[{argument_text}]"

    def key(self) -> str:
        """Return a stable semantic key."""
        argument_key: str = ",".join(
            argument.key() for argument in self.arguments
        )
        return f"generic:{self.origin.key()}[{argument_key}]"


@dataclass(slots=True, frozen=True)
class UnionTypeRef(TypeExpression):
    """Reference a normalized union type expression."""

    options: tuple[TypeExpression, ...]
    collapse_limit: int | None = None

    def __post_init__(self) -> None:
        """Normalize union options after initialization."""
        normalized_options: tuple[TypeExpression, ...] = (
            TypeUnionSimplifier().simplify(
                options=self.options,
                collapse_limit=self.collapse_limit,
            )
        )
        object.__setattr__(self, "options", normalized_options)

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a PEP 604 union AST expression."""
        option_nodes: tuple[expr, ...] = tuple(
            option.to_ast(resolver=resolver, _use=_use)
            for option in self.options
        )
        return AstExpressionBuilder.union(options=option_nodes)

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render a normalized PEP 604 union string."""
        return " | ".join(
            option.render(renderer=renderer) for option in self.options
        )

    def key(self) -> str:
        """Return a stable semantic key."""
        return "union:" + "|".join(option.key() for option in self.options)


@dataclass(slots=True, frozen=True)
class EmptyGenericTypeRef(TypeExpression):
    """Semantic representation of an intentionally empty generic subscript."""

    origin: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a best-effort AST node for an empty generic expression."""
        origin_node: expr = self.origin.to_ast(resolver=resolver, _use=_use)
        return Subscript(
            value=origin_node,
            slice=AstTuple(elts=[], ctx=Load()),
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render as ``Origin[]``."""
        origin_text: str = self.origin.render(renderer=renderer)
        return f"{origin_text}[]"

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"empty-generic:{self.origin.key()}"


@dataclass(slots=True, frozen=True)
class CallableTypeRef(TypeExpression):
    """Reference a ``collections.abc.Callable`` type expression."""

    parameters: tuple[TypeExpression, ...] | None
    returns: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a callable type AST expression."""
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
        """Render a callable type string."""
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
        """Return a stable semantic key."""
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
        """Build callable parameter node."""
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
    """Reference a ``typing.Literal`` expression."""

    values: tuple[LiteralValue, ...]

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a Literal AST expression."""
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
        """Render a Literal string."""
        literal_name: str = renderer.render_imported(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Literal",
            ),
        )
        values_text: str = ", ".join(repr(value) for value in self.values)
        return f"{literal_name}[{values_text}]"

    def key(self) -> str:
        """Return a stable semantic key."""
        return "literal:" + ",".join(repr(value) for value in self.values)


@dataclass(slots=True, frozen=True)
class SelfArgument:
    """Special receiver argument representing ``self``."""

    type_hint: TypeExpression = field(default_factory=SelfTypeRef)

    def to_argument(self) -> ArgumentSpec:
        """Convert to a normal argument spec."""
        return ArgumentSpec(name="self", type_hint=self.type_hint)


@dataclass(slots=True, frozen=True)
class EmptyTupleTypeRef(TypeExpression):
    """Semantic representation of ``tuple[()]``."""

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the AST node for ``tuple[()]``."""
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
        """Render ``tuple[()]``."""
        _: TypeHintStringRenderer = renderer
        return "tuple[()]"

    def key(self) -> str:
        """Return a stable semantic key."""
        return "builtins:tuple[()]"


@dataclass(slots=True, frozen=True)
class ConcatenateTypeRef(TypeExpression):
    """Semantic representation of ``typing.Concatenate``."""

    prefix: tuple[TypeExpression, ...]
    params: TypeExpression

    def __post_init__(self) -> None:
        """Validate that Concatenate has at least one prefix type."""
        if not self.prefix:
            fail(message="Concatenate requires at least one prefix type.")

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a subscripted ``Concatenate`` AST expression."""
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
        """Render a ``Concatenate`` expression."""
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
        """Return a stable semantic key."""
        prefix_key: str = ",".join(item.key() for item in self.prefix)
        return f"typing:Concatenate[{prefix_key},{self.params.key()}]"


@dataclass(slots=True, frozen=True)
class FlexibleCallableTypeRef(TypeExpression):
    """Semantic representation of all canonical ``Callable`` forms."""

    parameters: CallableParameterSpec
    returns: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return a canonical ``collections.abc.Callable`` AST expression."""
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
        """Render a canonical callable expression."""
        callable_name: str = ImportedTypeRef.absolute(
            module_parts=("collections", "abc"),
            name="Callable",
        ).render(renderer=renderer)
        parameters_text: str = self._parameters_text(renderer=renderer)
        returns_text: str = self.returns.render(renderer=renderer)
        return f"{callable_name}[{parameters_text}, {returns_text}]"

    def key(self) -> str:
        """Return a stable semantic key."""
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
        """Return the callable parameter AST node."""
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
        """Return callable parameter text."""
        if self.parameters is None:
            return "..."
        if isinstance(self.parameters, tuple):
            inner_text: str = ", ".join(
                item.render(renderer=renderer) for item in self.parameters
            )
            return f"[{inner_text}]"
        return self.parameters.render(renderer=renderer)

    def _parameter_key(self) -> str:
        """Return callable parameter key text."""
        if self.parameters is None:
            return "..."
        if isinstance(self.parameters, tuple):
            return "[" + ",".join(item.key() for item in self.parameters) + "]"
        return self.parameters.key()


@dataclass(slots=True, frozen=True)
class AstBackedTypeExpression(TypeExpression):
    """Semantic type expression backed by an existing annotation AST node."""

    node: expr

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return the existing annotation node."""
        _: TypeExpressionResolver | ImportUseSite = resolver
        _ = _use
        return self.node

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the existing annotation node."""
        _: TypeHintStringRenderer = renderer
        return unparse(ast_obj=fix_missing_locations(node=self.node))

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"ast:{unparse(ast_obj=fix_missing_locations(node=self.node))}"


@dataclass(slots=True, frozen=True)
class StarTypeHintRef(TypeExpression):
    """Semantic ``*T`` type hint wrapper backed by ``Unpack[T]``."""

    item: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``Unpack[T]`` as the semantic AST fallback."""
        _: ImportUseSite = _use
        return Types.typing.unpack.of(arguments=(self.item,)).to_ast(
            resolver=resolver,
            _use=ImportUseSite.annotation(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the star-prefixed form."""
        return f"*{self.item.render(renderer=renderer)}"

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"star:{self.item.key()}"


@dataclass(slots=True, frozen=True)
class DoubleStarTypeHintRef(TypeExpression):
    """Semantic ``**P`` type hint wrapper backed by ``Unpack[P]``."""

    item: TypeExpression

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return ``Unpack[P]`` as the semantic AST fallback."""
        _: ImportUseSite = _use
        return Types.typing.unpack.of(arguments=(self.item,)).to_ast(
            resolver=resolver,
            _use=ImportUseSite.annotation(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render the double-star-prefixed form."""
        return f"**{self.item.render(renderer=renderer)}"

    def key(self) -> str:
        """Return a stable semantic key."""
        return f"double-star:{self.item.key()}"


@dataclass(slots=True, frozen=True)
class CallableParameterListRef(TypeExpression):
    """Internal semantic representation of ``Callable[[...], R]`` params."""

    parameters: tuple[TypeExpression, ...]

    def to_ast(
        self,
        *,
        resolver: TypeExpressionResolver,
        _use: ImportUseSite,
    ) -> expr:
        """Return an AST list of callable parameter annotations."""
        return AstList(
            elts=[
                item.to_ast(resolver=resolver, _use=_use)
                for item in self.parameters
            ],
            ctx=Load(),
        )

    def render(self, *, renderer: TypeHintStringRenderer) -> str:
        """Render callable parameters as a bracketed list."""
        values: str = ", ".join(
            item.render(renderer=renderer) for item in self.parameters
        )
        return f"[{values}]"

    def key(self) -> str:
        """Return a stable semantic key."""
        return "callable-params:" + ",".join(
            item.key() for item in self.parameters
        )


class TypeUnionSimplifier:
    """Normalize, sort, deduplicate and generalize union members.

    Union types (PEP-604) can quickly become unwieldy when many
    observations are merged.  This simplifier performs a number of
    normalisation steps on a set of candidate type expressions:
    * **Flattening** nested unions into a single options list.
    * **Deduplication** of semantically identical types (preserving the
      first occurrence).
    * **Literal collapsing**: when all literal values of a given primitive
      type (e.g., ``Literal[1, 2]`` and ``Literal[3]``) are covered by
      an existing builtin like ``int``, the literal options are removed.
    * **Numeric collapsing**: ``bool | int | float`` is simplified to
      ``float`` (the widest numeric type) while preserving non-numeric
      options.
    * **Generic generalisation**: unions of container types with the same
      semantic family (e.g., ``list[str] | tuple[str]``) are collapsed
      to the appropriate ``collections.abc`` ABC such as
      ``MutableSequence[str]`` or ``Sequence[str]``.  Similarly, mapping
      unions are collapsed to ``Mapping`` or ``MutableMapping``.
    * **Sorting**: the resulting options are sorted deterministically
      according to builtin precedence and their semantic keys, so that
      equal unions compare equal and rendering order is stable.

    If a collapse limit is provided and the number of simplified options
    exceeds the limit, the simplifier returns ``object`` to avoid
    enormous unions.  See :meth:`simplify` for the entry point.
    """

    def simplify(
        self,
        *,
        options: tuple[TypeExpression, ...],
        collapse_limit: int | None,
    ) -> tuple[TypeExpression, ...]:
        """Return canonical union options."""
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
            self._collapse_literals(
                options=deduplicated_options,
            )
        )
        numeric_collapsed_options: tuple[TypeExpression, ...] = (
            self._collapse_numeric(
                options=literal_collapsed_options,
            )
        )
        generic_collapsed_options: tuple[TypeExpression, ...] = (
            self._generalize_generics(
                options=numeric_collapsed_options,
            )
        )
        sorted_options: tuple[TypeExpression, ...] = self._sort_options(
            options=generic_collapsed_options,
        )
        if collapse_limit is not None and len(sorted_options) > collapse_limit:
            return (BuiltinTypeRef(name="object"),)
        return sorted_options

    def _flatten(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Flatten nested unions."""
        flattened_options: list[TypeExpression] = []
        for option in options:
            if isinstance(option, UnionTypeRef):
                flattened_options.extend(option.options)
            else:
                flattened_options.append(option)
        return tuple(flattened_options)

    def _deduplicate(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Remove duplicate semantic options.

        Preserve the first occurrence.
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

    def _collapse_literals(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse literals covered by concrete builtin primitive types."""
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

    def _literal_is_covered(
        self,
        *,
        literal: LiteralTypeRef,
        builtin_names: set[str],
    ) -> bool:
        """Return whether all literal values are covered by builtin options."""
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

    def _collapse_numeric(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse compatible numeric unions such as ``int | float``."""
        highest_rank: int = -1
        other_options: list[TypeExpression] = []
        for option in options:
            builtin_name: str | None = self._builtin_name(option=option)
            numeric_rank: int | None = (
                UnionSimplificationTables.numeric_ranks.get(builtin_name)
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
        """Return builtin numeric type name for a rank."""
        for (
            name,
            candidate_rank,
        ) in UnionSimplificationTables.numeric_ranks.items():
            if candidate_rank == rank:
                return name
        fail(message="Invalid numeric rank.")

    def _generalize_generics(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> tuple[TypeExpression, ...]:
        """Collapse compatible container unions to ABC supertypes."""
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
        """Return generic family details if an option is generalizable."""
        if isinstance(option, EmptyGenericTypeRef):
            return None
        if not isinstance(option, GenericTypeRef):
            return None
        origin_name: str | None = self._origin_name(option=option.origin)
        if origin_name is None:
            return None
        if (
            origin_name in UnionSimplificationTables.mapping_origins
            and len(option.arguments) == Constants.two_item_count
        ):
            return _GenericParts(
                family="mapping",
                arguments=option.arguments,
                origin_name=origin_name,
            )
        if (
            origin_name in UnionSimplificationTables.iterable_origins
            and option.arguments
        ):
            return _GenericParts(
                family="iterable",
                arguments=(self._iterable_argument(option=option),),
                origin_name=origin_name,
            )
        return None

    def _iterable_argument(self, *, option: GenericTypeRef) -> TypeExpression:
        """Return the element argument for iterable-like generics."""
        origin_name: str | None = self._origin_name(option=option.origin)
        if origin_name == "tuple" and option.arguments:
            return option.arguments[0]
        return option.arguments[0]

    def _mapping_union(
        self,
        *,
        parts: tuple[_GenericParts, ...],
    ) -> TypeExpression:
        """Return a mapping ABC target for compatible mapping unions."""
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
        """Return ``Mapping`` or ``MutableMapping`` for mapping parts."""
        origin_names: set[str] = {
            self._origin_name_from_parts(parts_item=part) for part in parts
        }
        if origin_names <= UnionSimplificationTables.mutable_mapping_origins:
            return "MutableMapping"
        return "Mapping"

    def _iterable_union(
        self,
        *,
        parts: tuple[_GenericParts, ...],
    ) -> TypeExpression:
        """Return an iterable ABC target for compatible iterable unions."""
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
        """Return the narrowest supported ABC for iterable parts."""
        origin_names: set[str] = {
            self._origin_name_from_parts(parts_item=part) for part in parts
        }
        if origin_names <= UnionSimplificationTables.mutable_sequence_origins:
            return "MutableSequence"
        if origin_names <= UnionSimplificationTables.sequence_origins:
            return "Sequence"
        if origin_names <= UnionSimplificationTables.mutable_set_origins:
            return "MutableSet"
        if origin_names <= UnionSimplificationTables.set_origins:
            return "Set"
        if origin_names <= UnionSimplificationTables.iterable_origins:
            return "Collection"
        return "Iterable"

    def _origin_name_from_parts(self, *, parts_item: _GenericParts) -> str:
        """Return a stable origin name from generic parts metadata."""
        return parts_item.origin_name

    def _collapse_argument_union(
        self,
        *,
        options: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Collapse nested generic argument unions."""
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
        """Sort union members coherently and deterministically."""
        return tuple(sorted(options, key=self._sort_key))

    def _sort_key(self, option: TypeExpression) -> tuple[int, str]:
        """Return deterministic union-sort key."""
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
        """Return a deterministic rank for a union option."""
        rank: int = 50
        if builtin_name == "object":
            rank = 0
        elif builtin_name in UnionSimplificationTables.numeric_ranks:
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

    def _origin_name(self, *, option: TypeExpression) -> str | None:
        """Return a generic origin name when it is easily known."""
        if isinstance(option, BuiltinTypeRef):
            return option.name
        if isinstance(option, ImportedTypeRef):
            return option.source.imported_name
        return None

    def _builtin_name(self, *, option: TypeExpression) -> str | None:
        """Return builtin name when the option is a builtin ref."""
        if isinstance(option, BuiltinTypeRef):
            return option.name
        return None

    def _has_builtin(
        self,
        *,
        options: tuple[TypeExpression, ...],
        name: str,
    ) -> bool:
        """Return whether the options contain a builtin name."""
        return any(
            self._is_builtin_name(option=option, name=name)
            for option in options
        )

    def _is_builtin_name(self, *, option: TypeExpression, name: str) -> bool:
        """Return whether an option is a builtin ref with this name."""
        return self._builtin_name(option=option) == name

    def _is_imported_name(self, *, option: TypeExpression, name: str) -> bool:
        """Return whether an option is an imported ref with this name."""
        return (
            isinstance(option, ImportedTypeRef)
            and option.source.imported_name == name
        )


class AstExpressionBuilder:
    """Semantic helpers for AST expression composition."""

    @staticmethod
    def subscript(*, value: expr, args: tuple[expr, ...]) -> Subscript:
        """Create ``value[arg]`` or ``value[arg1, arg2]``."""
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
        """Create ``A | B | C`` as nested ``BinOp`` nodes."""
        if not options:
            msg: str = "Union requires at least one option."
            fail(message=msg)
        current: expr | BinOp = options[0]
        for option in options[1:]:
            current = BinOp(left=current, op=BitOr(), right=option)
        return current


class TypeExpressionResolver:
    """Resolve semantic type expressions into AST annotation nodes."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the resolver."""
        self.imports: UsageAwareImportCollector = imports
        self._validator: IdentifierValidator = IdentifierValidator()

    def validate_identifier(self, *, name: str, label: str) -> None:
        """Validate a type-expression identifier."""
        self._validator.validate_identifier(name=name, label=label)

    def annotation(self, *, value: TypeExpression) -> expr:
        """Resolve an annotation use."""
        return value.to_ast(resolver=self, _use=ImportUseSite.annotation())

    def protocol_base(self, *, value: TypeExpression) -> expr:
        """Resolve a protocol-base use."""
        return value.to_ast(resolver=self, _use=ImportUseSite.protocol_base())

    def typevar_bound(self, *, value: TypeExpression) -> expr:
        """Resolve a TypeVar bound use."""
        return value.to_ast(resolver=self, _use=ImportUseSite.typevar_bound())

    def typevar_constraint(self, *, value: TypeExpression) -> expr:
        """Resolve a TypeVar constraint use."""
        return value.to_ast(
            resolver=self,
            _use=ImportUseSite.typevar_constraint(),
        )


class TypeHintStringRenderer:
    """Render semantic type expressions as strings and collect imports."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the string renderer."""
        self._imports: UsageAwareImportCollector = imports
        self._validator: IdentifierValidator = IdentifierValidator()

    def validate_identifier(self, *, name: str, label: str) -> None:
        """Validate a rendered identifier."""
        self._validator.validate_identifier(name=name, label=label)

    def render(self, *, value: TypeExpression) -> str:
        """Render a semantic type expression as a type-hint string."""
        return value.render(renderer=self)

    def render_imported(self, *, source: SemanticImportSource) -> str:
        """Render an imported type and collect a string-hint import."""
        node: Name = self._imports.require_from_source(
            source=source,
            use=ImportUseSite.string_type_hint(owner=source.imported_name),
        )
        return node.id


class TypeParameterNameRegistry:
    """Allocate stable names for ``TypeVar`` and ``ParamSpec`` declarations.

    The type inference engine synthesizes many type parameters on demand.
    To avoid clashes and to make generated names deterministic, this
    registry maintains a bijection between semantic keys (derived from
    signatures) and short identifier names.  When a caller requests a
    name for a given key, the registry either returns an existing
    assignment or generates a fresh name (e.g., ``T``, ``U``, ``P``, ``Q``).
    Explicitly supplied names are registered verbatim, but a conflict
    will raise an exception to prevent silently inconsistent TypeVar
    declarations.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._typevars_by_key: dict[str, str] = {}
        self._typevar_keys_by_name: dict[str, str] = {}
        self._paramspecs_by_key: dict[str, str] = {}
        self._paramspec_keys_by_name: dict[str, str] = {}

    def typevar_name(self, *, key: str, name: str | None) -> str:
        """Return a stable TypeVar name."""
        if name is not None:
            return self._register_typevar(name=name, key=key)
        existing: str | None = self._typevars_by_key.get(key)
        if existing is not None:
            return existing
        return self._register_typevar(
            name=self._next_name(
                names=TypeParameterNameTables.typevar_names,
                used=set(self._typevar_keys_by_name),
            ),
            key=key,
        )

    def paramspec_name(self, *, key: str, name: str | None) -> str:
        """Return a stable ParamSpec name."""
        if name is not None:
            return self._register_paramspec(name=name, key=key)
        existing: str | None = self._paramspecs_by_key.get(key)
        if existing is not None:
            return existing
        return self._register_paramspec(
            name=self._next_name(
                names=TypeParameterNameTables.paramspec_names,
                used=set(self._paramspec_keys_by_name),
            ),
            key=key,
        )

    def _register_typevar(self, *, name: str, key: str) -> str:
        """Register a TypeVar name for a semantic key."""
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
        """Register a ParamSpec name for a semantic key."""
        existing_key: str | None = self._paramspec_keys_by_name.get(name)
        if existing_key is not None and existing_key != key:
            msg: str = (
                f"ParamSpec name {name!r} already has a different signature."
            )
            fail(message=msg)
        self._paramspec_keys_by_name[name] = key
        self._paramspecs_by_key[key] = name
        return name

    def _next_name(self, *, names: tuple[str, ...], used: set[str]) -> str:
        """Return the next available generated name."""
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


class Args:
    """Factory for semantic argument objects."""

    @staticmethod
    def self_arg(*, type_hint: TypeExpression | None = None) -> SelfArgument:
        """Create a special ``self`` argument."""
        return SelfArgument(type_hint=type_hint or SelfTypeRef())

    @staticmethod
    def cls_arg(*, type_hint: TypeExpression | None = None) -> ClsArgument:
        """Create a special ``cls`` argument."""
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
        """Create a positional-or-keyword argument."""
        return ArgumentSpec(
            name=name,
            type_hint=type_hint,
            default=default,
        )

    @staticmethod
    def posonly(
        *,
        name: str,
        type_hint: TypeExpression,
        default: expr | None = None,
    ) -> ArgumentSpec:
        """Create a positional-only argument."""
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
        """Create a keyword-only argument."""
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
        """Create a ``*args`` argument."""
        return ArgumentSpec(name=name, type_hint=type_hint, kind="vararg")

    @staticmethod
    def kwargs(
        *,
        type_hint: TypeExpression,
        name: str = "kwargs",
    ) -> ArgumentSpec:
        """Create a ``**kwargs`` argument."""
        return ArgumentSpec(name=name, type_hint=type_hint, kind="kwarg")

    @staticmethod
    def slash() -> SlashMarker:
        """Create a positional-only slash marker."""
        return SlashMarker()

    @staticmethod
    def star() -> StarMarker:
        """Create a bare keyword-only star marker."""
        return StarMarker()


class ExistingProtocolIndex:
    """Index existing protocol classes by name and method shape."""

    def __init__(self, *, class_nodes: Iterable[ClassDef]) -> None:
        """Initialize the index."""
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
        """Create an index from existing-node context."""
        return cls(class_nodes=context.class_nodes)

    def find_by_name(self, *, name: str) -> ClassDef | None:
        """Return an existing protocol class by name."""
        node: ClassDef | None = self._classes_by_name.get(name)
        if node is None or not self._is_protocol_class(node=node):
            return None
        return node

    def find_by_shape(self, *, spec: ProtocolSpec) -> ClassDef | None:
        """Return an existing protocol class by method shape."""
        return self._protocols_by_shape.get(self._shape_from_spec(spec=spec))

    def _is_protocol_class(self, *, node: ClassDef) -> bool:
        """Return whether a class base mentions Protocol."""
        return any(
            self._base_mentions_protocol(base=base) for base in node.bases
        )

    def _base_mentions_protocol(self, *, base: expr) -> bool:
        """Return whether a base expression mentions Protocol."""
        if isinstance(base, Name):
            return base.id == "Protocol"
        if isinstance(base, Attribute):
            return base.attr == "Protocol"
        if isinstance(base, Subscript):
            return self._base_mentions_protocol(base=base.value)
        return False

    def _shape_from_class(self, *, node: ClassDef) -> ProtocolShape:
        """Build a structural method shape from an existing class."""
        methods: list[tuple[str, tuple[str, ...]]] = [
            self._method_shape_from_function(node=body_node)
            for body_node in node.body
            if isinstance(body_node, FunctionDef)
        ]
        return ProtocolShape(methods=tuple(sorted(methods)))

    def _method_shape_from_function(
        self,
        *,
        node: FunctionDef,
    ) -> tuple[str, tuple[str, ...]]:
        """Return a comparable shape for one function."""
        argument_names: list[str] = []
        argument_names.extend(item.arg for item in node.args.posonlyargs)
        argument_names.extend(item.arg for item in node.args.args)
        if node.args.vararg is not None:
            argument_names.append(f"*{node.args.vararg.arg}")
        argument_names.extend(item.arg for item in node.args.kwonlyargs)
        if node.args.kwarg is not None:
            argument_names.append(f"**{node.args.kwarg.arg}")
        return (node.name, tuple(argument_names))

    def _shape_from_spec(self, *, spec: ProtocolSpec) -> ProtocolShape:
        """Build a structural shape from a protocol spec."""
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
        """Return comparable argument names from semantic arguments."""
        names: list[str] = []
        for item in arguments:
            if isinstance(item, SelfArgument):
                names.append("self")
            elif isinstance(item, ClsArgument):
                names.append("cls")
            elif isinstance(item, ArgumentSpec):
                names.append(self._argument_shape_name(argument=item))
        return tuple(names)

    def _argument_shape_name(self, *, argument: ArgumentSpec) -> str:
        """Return the shape name for one argument."""
        if argument.kind == "vararg":
            return f"*{argument.name}"
        if argument.kind == "kwarg":
            return f"**{argument.name}"
        return argument.name


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
        """Normalize argument objects and markers."""
        state: ParameterState = ParameterState()
        normalized: list[ArgumentSpec] = []
        for item in items:
            self._apply_item(item=item, state=state, normalized=normalized)
        return tuple(normalized)

    def _apply_item(
        self,
        *,
        item: ArgumentItem,
        state: ParameterState,
        normalized: list[ArgumentSpec],
    ) -> None:
        """Apply one grammar item to the normalized argument list."""
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
        """Append one normalized argument."""
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

    def _as_posonly(self, *, argument: ArgumentSpec) -> ArgumentSpec:
        """Convert a normal argument to positional-only."""
        if argument.kind in {"keyword_only", "vararg", "kwarg"}:
            return argument
        return ArgumentSpec(
            name=argument.name,
            type_hint=argument.type_hint,
            kind="positional_only",
            default=argument.default,
        )

    def _as_kwonly(self, *, argument: ArgumentSpec) -> ArgumentSpec:
        """Convert a normal argument to keyword-only."""
        if argument.kind in {"vararg", "kwarg"}:
            return argument
        return ArgumentSpec(
            name=argument.name,
            type_hint=argument.type_hint,
            kind="keyword_only",
            default=argument.default,
        )


class ProtocolGrammar:
    """Infer protocol names and docstrings from method signatures and names.

    When the inference pipeline synthesises a protocol to represent
    structural typing requirements, it often lacks a meaningful class
    name and documentation.  The grammar analyses the names and
    signatures of the protocol methods to derive semantic *capabilities*.
    Dunder methods map to well-known behaviours such as ``__iter__`` →
    ``Iteration`` and ``__call__`` → ``Call``.  Verb-prefixed methods
    like ``read_*`` or ``write_*`` translate to capabilities like
    ``Reading`` or ``Writing``.  Composite capabilities combine
    complementary operations (e.g. ``__iter__`` and ``__next__`` →
    ``Iterator``).

    The derived capabilities inform both the generated class name
    (prefixed with ``Supports``) and the docstring, which lists the
    human-readable names of the required behaviours and method set.
    Individual method docstrings are generated when absent, using the
    capability to describe the expected behaviour succinctly.  See
    :meth:`infer` for the main entry point.
    """

    def infer(self, *, spec: ProtocolSpec) -> ProtocolSpec:
        """Return a protocol spec with inferred name and docstrings."""
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
                self._method_with_docstring(method=method, profile=profile)
                for method, profile in zip(spec.methods, profiles, strict=True)
            ),
            bases=spec.bases,
            decorators=spec.decorators,
        )

    def profile_method(self, *, method: MethodSpec) -> MethodSemanticProfile:
        """Build a semantic method profile."""
        is_dunder: bool = method.name.startswith(
            "__",
        ) and method.name.endswith("__")
        capability: str = self._capability_for(method_name=method.name)
        required_count: int = sum(
            1
            for item in method.arguments
            if isinstance(item, ArgumentSpec)
            and item.default is None
            and item.kind
            in {"positional_only", "positional_or_keyword", "keyword_only"}
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
        """Infer a protocol class name."""
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
        """Infer a protocol docstring."""
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
            f"Protocol for objects that support {capabilities}. "
            f"Required method set: {methods}."
        )

    def method_docstring(self, *, profile: MethodSemanticProfile) -> str:
        """Infer one method docstring."""
        capability: str = self._title_to_words(value=profile.capability)
        if profile.is_dunder:
            return f"Implement {capability} behavior for this object."
        return f"Perform {capability} using this method's declared inputs."

    def _method_with_docstring(
        self,
        *,
        method: MethodSpec,
        profile: MethodSemanticProfile,
    ) -> MethodSpec:
        """Return method with generated docstring when missing."""
        return MethodSpec(
            name=method.name,
            arguments=method.arguments,
            returns=method.returns,
            docstring=method.docstring
            or self.method_docstring(profile=profile),
            decorators=method.decorators,
            body=method.body,
        )

    def _capability_for(self, *, method_name: str) -> str:
        """Infer a capability for one method name."""
        if method_name in ProtocolCapabilityTables.dunder_capabilities:
            return ProtocolCapabilityTables.dunder_capabilities[method_name]
        words: tuple[str, ...] = self._split_identifier(name=method_name)
        if not words:
            return "ProtocolBehavior"
        first: str = words[0]
        mapped: str | None = ProtocolCapabilityTables.verb_capabilities.get(
            first,
        )
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
        """Return a composite protocol name if applicable."""
        names: frozenset[str] = frozenset(profile.name for profile in profiles)
        public_names: frozenset[str] = frozenset(
            name.strip("_") for name in names
        )
        for (
            required_names,
            capability,
        ) in ProtocolCapabilityTables.composites.items():
            if required_names.issubset(names) or required_names.issubset(
                public_names,
            ):
                return capability
        return None

    def _unique_capabilities(
        self,
        *,
        profiles: tuple[MethodSemanticProfile, ...],
    ) -> tuple[str, ...]:
        """Return capabilities without duplicates."""
        result: list[str] = []
        seen: set[str] = set()
        for profile in profiles:
            if profile.capability not in seen:
                seen.add(profile.capability)
                result.append(profile.capability)
        return tuple(result)

    def _split_identifier(self, *, name: str) -> tuple[str, ...]:
        """Split snake/camel/Pascal/dunder identifiers into words."""
        stripped: str = name.strip("_")
        snake_ready: str = sub(
            pattern=r"([a-z0-9])([A-Z])",
            repl=r"\1_\2",
            string=stripped,
        )
        return tuple(
            part.lower() for part in snake_ready.split(sep="_") if part
        )

    def _pascal_case(self, *, words: tuple[str, ...]) -> str:
        """Convert words to PascalCase."""
        return "".join(word[:1].upper() + word[1:] for word in words)

    def _title_to_words(self, *, value: str) -> str:
        """Convert PascalCase to lowercase words."""
        return sub(pattern=r"(?<!^)(?=[A-Z])", repl=" ", string=value).lower()

    def _human_join(self, *, values: tuple[str, ...]) -> str:
        """Join words with English punctuation."""
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        if len(values) == Constants.two_item_count:
            return f"{values[0]} and {values[1]}"
        return f"{', '.join(values[:-1])}, and {values[-1]}"


class SemanticCastNode(AST):
    """Custom AST node representing a semantic cast around any AST target."""

    _fields: ClassVar[tuple[str, ...]] = ("target",)

    def __init__(
        self,
        *,
        type_hint: TypeExpression,
        type_hint_text: str,
        target: AST,
        call_expr: Call | None,
    ) -> None:
        """Initialize a semantic cast node."""
        super().__init__()
        self.type_hint: TypeExpression = type_hint
        self.type_hint_text: str = type_hint_text
        self.target: AST = target
        self.call_expr: Call | None = call_expr

    def require_call_expr(self) -> Call:
        """Return the concrete cast call.

        Fail for non-expression targets.
        """
        if self.call_expr is None:
            msg: str = "Semantic cast target is not an expression node."
            fail(message=msg)
        return self.call_expr


class CastExpressionFactory:
    """Build semantic ``typing.cast`` call expressions."""

    def __init__(
        self,
        *,
        imports: UsageAwareImportCollector,
        renderer: TypeHintStringRenderer,
    ) -> None:
        """Initialize the factory."""
        self._imports: UsageAwareImportCollector = imports
        self._renderer: TypeHintStringRenderer = renderer

    def cast(
        self,
        *,
        type_hint: TypeExpression,
        target: AST,
    ) -> SemanticCastNode:
        """Return a semantic cast node for any AST target.

        Expression targets expose a concrete ``cast("TypeHint", target)`` call.
        Non-expression targets are preserved semantically without fabricating
        invalid Python syntax.
        """
        cast_func: expr = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="cast",
            ),
            use=ImportUseSite.runtime(owner="cast"),
        )
        type_hint_text: str = self._renderer.render(value=type_hint)
        call_expr: Call | None = None
        if isinstance(target, expr):
            call_expr = Call(
                func=cast_func,
                args=[Constant(value=type_hint_text), target],
                keywords=[],
            )
        return SemanticCastNode(
            type_hint=type_hint,
            type_hint_text=type_hint_text,
            target=target,
            call_expr=call_expr,
        )

    def cast_call(self, *, type_hint: TypeExpression, target: expr) -> Call:
        """Return a concrete ``typing.cast`` call for expression targets."""
        return self.cast(
            type_hint=type_hint,
            target=target,
        ).require_call_expr()


class ProtocolNodeBuilder:
    """Build AST nodes for TypeVars, ParamSpecs, and Protocol classes."""

    def __init__(
        self,
        *,
        imports: UsageAwareImportCollector,
        resolver: TypeExpressionResolver,
    ) -> None:
        """Initialize the node builder."""
        self._imports: UsageAwareImportCollector = imports
        self._resolver: TypeExpressionResolver = resolver
        self._parameters: ParameterNormalizer = ParameterNormalizer()
        self._validator: IdentifierValidator = IdentifierValidator()

    def typevar(self, *, spec: TypeVarSpec) -> Assign:
        """Build a TypeVar assignment."""
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
        """Build a ParamSpec assignment."""
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
        """Build a Protocol class definition."""
        if spec.name is None:
            msg: str = "Protocol name must be inferred before building."
            fail(message=msg)
        self._validator.validate_identifier(name=spec.name, label="protocol")
        bases: list[expr] = self._protocol_bases(spec=spec)
        class_node: ClassDef = ClassDef(
            name=spec.name,
            bases=bases,
            keywords=[],
            body=[],
            decorator_list=list(spec.decorators),
            type_params=[],
        )
        DocstringEditor().set_class(
            class_node=class_node,
            text=spec.docstring or "",
        )
        class_node.body.extend(
            self.method(spec=method) for method in spec.methods
        )
        return class_node

    def method(self, *, spec: MethodSpec) -> FunctionDef:
        """Build one protocol method definition."""
        method_node: FunctionDef = FunctionDef(
            name=spec.name,
            args=self.arguments(items=spec.arguments),
            body=[],
            decorator_list=list(spec.decorators),
            returns=self._resolver.annotation(value=spec.returns),
            type_comment=None,
            type_params=[],
        )
        DocstringEditor().set_function(
            function=method_node,
            text=spec.docstring or "",
        )
        if spec.body is None:
            method_node.body.append(Expr(value=Constant(value=Ellipsis)))
        else:
            method_node.body.extend(spec.body or (Pass(),))
        return method_node

    def arguments(self, *, items: tuple[ArgumentItem, ...]) -> ast_arguments:
        """Build ``ast.arguments`` from semantic argument items."""
        normalized: tuple[ArgumentSpec, ...] = self._parameters.normalize(
            items=items,
        )
        self._validate_unique_argument_names(arguments=normalized)
        builder: AstArgsBuilder = AstArgsBuilder(resolver=self._resolver)
        return builder.build(arguments=normalized)

    def _protocol_bases(self, *, spec: ProtocolSpec) -> list[expr]:
        """Return protocol base expressions."""
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
        """Append TypeVar keyword arguments."""
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

    def _validate_unique_argument_names(
        self,
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> None:
        """Validate unique argument names."""
        names: set[str] = set()
        for argument in arguments:
            if argument.name in names:
                msg: str = f"Duplicate argument name: {argument.name!r}."
                fail(message=msg)
            names.add(argument.name)


class AstArgsBuilder:
    """Build AST argument lists from normalized semantic arguments."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the builder."""
        self._resolver: TypeExpressionResolver = resolver

    def build(self, *, arguments: tuple[ArgumentSpec, ...]) -> ast_arguments:
        """Build an ``ast.arguments`` node."""
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

    def _split(
        self,
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> AstArgumentGroups:
        """Split semantic arguments into AST argument groups."""
        groups: AstArgumentGroups = AstArgumentGroups()
        for argument in arguments:
            node: arg = self._node(argument=argument)
            groups.add(argument=argument, node=node)
        return groups

    def _node(self, *, argument: ArgumentSpec) -> arg:
        """Build one annotated AST argument."""
        return arg(
            arg=argument.name,
            annotation=self._resolver.annotation(value=argument.type_hint),
            type_comment=None,
        )

    def _positional_defaults(
        self,
        *,
        arguments: tuple[ArgumentSpec, ...],
    ) -> list[expr]:
        """Build positional defaults while enforcing Python ordering."""
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


class AttributeSetattrRewriteFactory:
    """Rewrite ``obj.attr = value`` assignments into ``setattr`` nodes."""

    def __init__(self) -> None:
        """Initialize the attribute rewrite factory."""
        self._validator: IdentifierValidator = IdentifierValidator()

    def rewrite(
        self,
        *,
        node: AttributeAssignmentNode,
        variable_name: str = "_attr_name",
    ) -> AttributeSetattrRewriteResult:
        """Rewrite an attribute assignment node into two AST statements.

        Args:
            node: Assignment whose target must be an ``ast.Attribute``.
            variable_name: Local variable name storing the attribute name.

        Returns:
            Replacement nodes equivalent to ``name: str = "attr"`` and
            ``setattr(object, name, value)``.

        """
        target: Attribute = self._attribute_target(node=node)
        value_node: expr = self._assigned_value(node=node)
        return self.from_parts(
            object_node=target.value,
            attribute_name=target.attr,
            value_node=value_node,
            variable_name=variable_name,
            location_node=node,
        )

    def from_parts(
        self,
        *,
        object_node: expr,
        attribute_name: str,
        value_node: expr,
        variable_name: str = "_attr_name",
        location_node: stmt | None = None,
    ) -> AttributeSetattrRewriteResult:
        """Build replacement nodes from semantic assignment parts."""
        self._validator.validate_identifier(
            name=variable_name,
            label="attribute-name variable",
        )
        self._validator.validate_identifier(
            name=attribute_name,
            label="attribute name",
        )
        attribute_name_node: AnnAssign = AnnAssign(
            target=Name(id=variable_name, ctx=Store()),
            annotation=Name(id="str", ctx=Load()),
            value=Constant(value=attribute_name),
            simple=1,
        )
        setattr_node: Expr = Expr(
            value=Call(
                func=Name(id="setattr", ctx=Load()),
                args=[
                    deepcopy(x=object_node),
                    Name(id=variable_name, ctx=Load()),
                    deepcopy(x=value_node),
                ],
                keywords=[],
            ),
        )
        if location_node is None:
            fixed_attribute_node: AnnAssign = fix_missing_locations(
                node=attribute_name_node,
            )
            fixed_setattr_node: Expr = fix_missing_locations(node=setattr_node)
        else:
            located_attribute_node: AnnAssign = copy_location(
                new_node=attribute_name_node,
                old_node=location_node,
            )
            located_setattr_node: Expr = copy_location(
                new_node=setattr_node,
                old_node=location_node,
            )
            fixed_attribute_node = fix_missing_locations(
                node=located_attribute_node,
            )
            fixed_setattr_node = fix_missing_locations(
                node=located_setattr_node,
            )
        return AttributeSetattrRewriteResult(
            attribute_name_node=fixed_attribute_node,
            setattr_node=fixed_setattr_node,
        )

    def _attribute_target(self, *, node: AttributeAssignmentNode) -> Attribute:
        """Return the attribute target from an assignment node."""
        target_node: expr
        if isinstance(node, Assign):
            if len(node.targets) != 1:
                msg: str = "Only single-target assignments can be rewritten."
                fail(message=msg)
            target_node = node.targets[0]
        else:
            target_node = node.target
        if not isinstance(target_node, Attribute):
            msg = "Assignment target must be an attribute node."
            fail(message=msg)
        return target_node

    def _assigned_value(self, *, node: AttributeAssignmentNode) -> expr:
        """Return the assigned value from an assignment node."""
        if isinstance(node, Assign):
            return node.value
        if node.value is None:
            msg: str = "Annotated attribute assignments need a value."
            fail(message=msg)
        return node.value


class MethodOverrideFactory:
    """Create method override clones while preserving original method data."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the method override factory."""
        self._resolver: TypeExpressionResolver = resolver
        self._args_builder: AstArgsBuilder = AstArgsBuilder(
            resolver=resolver,
        )

    def copy_method(self, *, spec: MethodOverrideSpec) -> FunctionDef:
        """Copy a method and replace selected signature/body fields."""
        if spec.update.name is None:
            method_name: str = spec.original.name
        else:
            method_name = spec.update.name
        arguments_node: ast_arguments = self._arguments(spec=spec)
        returns_node: expr | None = self._returns(spec=spec)
        body_nodes: list[stmt] = self._body(spec=spec)
        decorator_nodes: list[expr] = self._decorators(spec=spec)
        type_parameter_nodes: list[type_param] = deepcopy(
            x=spec.original.type_params,
        )
        function_node: FunctionDef = FunctionDef(
            name=method_name,
            args=arguments_node,
            body=body_nodes,
            decorator_list=decorator_nodes,
            returns=returns_node,
            type_comment=spec.original.type_comment,
            type_params=type_parameter_nodes,
        )
        located_node: FunctionDef = copy_location(
            new_node=function_node,
            old_node=spec.original,
        )
        return fix_missing_locations(node=located_node)

    def _arguments(self, *, spec: MethodOverrideSpec) -> ast_arguments:
        """Return replacement or copied method arguments."""
        if spec.update.arguments is None:
            return deepcopy(x=spec.original.args)
        if isinstance(spec.update.arguments, ast_arguments):
            return deepcopy(x=spec.update.arguments)
        return self._args_builder.build(arguments=spec.update.arguments)

    def _returns(self, *, spec: MethodOverrideSpec) -> expr | None:
        """Return replacement or copied return annotation."""
        if spec.update.return_annotation is None:
            original_returns: expr | None = spec.original.returns
            if original_returns is None:
                return None
            return deepcopy(x=original_returns)
        if isinstance(spec.update.return_annotation, TypeExpression):
            return self._resolver.annotation(
                value=spec.update.return_annotation,
            )
        return deepcopy(x=spec.update.return_annotation)

    def _body(self, *, spec: MethodOverrideSpec) -> list[stmt]:
        """Return replacement or copied method body."""
        if spec.update.body is None:
            return deepcopy(x=spec.original.body)
        return deepcopy(x=list(spec.update.body))

    def _decorators(self, *, spec: MethodOverrideSpec) -> list[expr]:
        """Return replacement or copied method decorators."""
        if spec.update.decorators is None:
            return deepcopy(x=spec.original.decorator_list)
        return deepcopy(x=list(spec.update.decorators))


class MethodOverrideBlock:
    """Collect ordered override method nodes for one original function."""

    def __init__(
        self,
        *,
        original: FunctionDef,
        factory: MethodOverrideFactory,
    ) -> None:
        """Initialize the override block."""
        self._original: FunctionDef = original
        self._factory: MethodOverrideFactory = factory
        self._entries: list[MethodOverrideEntry] = []

    @property
    def original(self) -> FunctionDef:
        """Return the original function node."""
        return self._original

    def add(self, *, update: MethodOverrideUpdate) -> FunctionDef:
        """Create and store one override method node."""
        if update.order is None:
            resolved_order: int = len(self._entries)
        else:
            resolved_order = update.order
        resolved_update: MethodOverrideUpdate = MethodOverrideUpdate(
            arguments=update.arguments,
            return_annotation=update.return_annotation,
            name=update.name,
            body=update.body,
            decorators=update.decorators,
            order=resolved_order,
        )
        node: FunctionDef = self._factory.copy_method(
            spec=MethodOverrideSpec(
                original=self._original,
                update=resolved_update,
            ),
        )
        self._entries.append(
            MethodOverrideEntry(order=resolved_order, node=node),
        )
        return node

    def nodes(self) -> list[FunctionDef]:
        """Return override nodes ordered for insertion."""
        ordered_entries: list[MethodOverrideEntry] = sorted(
            self._entries,
            key=self._entry_sort_key,
        )
        return [entry.node for entry in ordered_entries]

    def _entry_sort_key(self, entry: MethodOverrideEntry) -> tuple[int, str]:
        """Return a stable override order key."""
        return (entry.order, entry.node.name)


class MethodOverrideManager:
    """Manage override blocks keyed by original function identity."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the override manager."""
        self._factory: MethodOverrideFactory = MethodOverrideFactory(
            resolver=resolver,
        )
        self._blocks_by_identity: dict[int, MethodOverrideBlock] = {}

    def block_for(self, *, original: FunctionDef) -> MethodOverrideBlock:
        """Return the override block associated with an original function."""
        identity: int = id(original)
        existing_block: MethodOverrideBlock | None = (
            self._blocks_by_identity.get(
                identity,
            )
        )
        if existing_block is not None:
            return existing_block
        block: MethodOverrideBlock = MethodOverrideBlock(
            original=original,
            factory=self._factory,
        )
        self._blocks_by_identity[identity] = block
        return block

    def add(
        self,
        *,
        original: FunctionDef,
        update: MethodOverrideUpdate,
    ) -> FunctionDef:
        """Create and store one override for an original function."""
        return self.block_for(original=original).add(update=update)

    def nodes_for(self, *, original: FunctionDef) -> list[FunctionDef]:
        """Return ordered override nodes for an original function."""
        return self.block_for(original=original).nodes()

    def blocks(self) -> tuple[MethodOverrideBlock, ...]:
        """Return all override blocks ordered by original source location."""
        blocks: list[MethodOverrideBlock] = list(
            self._blocks_by_identity.values(),
        )
        return tuple(sorted(blocks, key=self._block_sort_key))

    def _block_sort_key(
        self,
        block: MethodOverrideBlock,
    ) -> tuple[int, int, str]:
        """Return a stable order key for an override block."""
        line_number: int = getattr(block.original, "lineno", 0)
        column: int = getattr(block.original, "col_offset", 0)
        return (line_number, column, block.original.name)


class ProtocolTypeBlockCollector:
    """Collect TypeVars, ParamSpecs, Protocols, and cast expressions."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the collector."""
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
        self.attribute_sets: AttributeSetattrRewriteFactory = (
            AttributeSetattrRewriteFactory()
        )
        self.overrides: MethodOverrideManager = MethodOverrideManager(
            resolver=self._resolver,
        )

    def typevar(
        self,
        *,
        name: str | None = None,
        bound: TypeExpression | None = None,
        constraints: tuple[TypeExpression, ...] = (),
        covariant: bool = False,
        contravariant: bool = False,
    ) -> TypeVarSpec:
        """Create and collect a TypeVar spec."""
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
        """Create and collect a ParamSpec spec."""
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
        """Register a protocol or return an equivalent existing protocol."""
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
        """Build imports and declarations ready for top insertion."""
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

    def render_nodes(self, *, nodes: Iterable[stmt]) -> str:
        """Render generated nodes to source for diagnostics."""
        module: Module = Module(body=list(nodes), type_ignores=[])
        fixed_module: Module = fix_missing_locations(node=module)
        return unparse(ast_obj=fixed_module)

    def rewrite_attribute_set(
        self,
        *,
        node: AttributeAssignmentNode,
        variable_name: str = "_attr_name",
    ) -> AttributeSetattrRewriteResult:
        """Rewrite ``obj.attr = value`` into name storage and ``setattr``.

        Args:
            node: Attribute assignment node to rewrite.
            variable_name: Local variable storing the attribute name.

        Returns:
            The two replacement nodes in semantic form.

        """
        return self.attribute_sets.rewrite(
            node=node,
            variable_name=variable_name,
        )

    def _typevar_key(self, *, signature: TypeVarSignature) -> str:
        """Return a stable semantic key for a TypeVar signature."""
        constraints: str = ",".join(
            item.key() for item in signature.constraints
        )
        bound: str = (
            signature.bound.key() if signature.bound is not None else "None"
        )
        return (
            f"bound={bound};constraints={constraints};"
            f"covariant={signature.covariant};"
            f"contravariant={signature.contravariant}"
        )

    def _paramspec_key(self, *, signature: ParamSpecSignature) -> str:
        """Return a stable semantic key for a ParamSpec signature."""
        bound: str = (
            signature.bound.key() if signature.bound is not None else "None"
        )
        return (
            f"bound={bound};covariant={signature.covariant};"
            f"contravariant={signature.contravariant}"
        )


class ParenthesizedExpressionNode(AST):
    """Custom AST node preserving original expression parentheses."""

    _fields: ClassVar[tuple[str, ...]] = ("value",)

    def __init__(self, *, value: AST, metadata: ParenthesisMetadata) -> None:
        """Initialize a parenthesized expression wrapper."""
        super().__init__()
        self.value: AST = value
        self.metadata: ParenthesisMetadata = metadata


class QuotedConstantNode(AST):
    """Custom AST node preserving original quote style."""

    _fields: ClassVar[tuple[str, ...]] = ("value",)

    def __init__(
        self,
        *,
        value: Constant,
        metadata: StringQuoteMetadata,
    ) -> None:
        """Initialize a quoted constant wrapper."""
        super().__init__()
        self.value: Constant = value
        self.metadata: StringQuoteMetadata = metadata


class BodyBlockNode(AST):
    """Custom AST node representing the non-preamble code body."""

    _fields: ClassVar[tuple[str, ...]] = ("body",)

    def __init__(self, *, body: tuple[stmt, ...]) -> None:
        """Initialize a semantic body block."""
        super().__init__()
        self.body: tuple[stmt, ...] = body


class GeneratedPreambleBlockNode(AST):
    """Custom AST node representing generated declarations before the body."""

    _fields: ClassVar[tuple[str, ...]] = (
        "imports",
        "constants",
        "typevars",
        "paramspecs",
        "type_aliases",
        "protocols",
    )

    def __init__(
        self,
        *,
        imports: tuple[stmt, ...],
        typevars: tuple[stmt, ...],
        paramspecs: tuple[stmt, ...],
        type_aliases: tuple[stmt, ...],
        protocols: tuple[stmt, ...],
    ) -> None:
        """Initialize a semantic generated preamble."""
        super().__init__()
        self.imports: tuple[stmt, ...] = imports
        self.constants: tuple[stmt, ...] = ()
        self.typevars: tuple[stmt, ...] = typevars
        self.paramspecs: tuple[stmt, ...] = paramspecs
        self.type_aliases: tuple[stmt, ...] = type_aliases
        self.protocols: tuple[stmt, ...] = protocols

    @property
    def ordered_nodes(self) -> tuple[stmt, ...]:
        """Return nodes in canonical insertion order."""
        return (
            *self.imports,
            *self.constants,
            *self.typevars,
            *self.paramspecs,
            *self.type_aliases,
            *self.protocols,
        )


class StringQuoteAnalyzer:
    """Extract quote styles from Python string tokens."""

    def analyze(
        self,
        *,
        tokens: tuple[SourceToken, ...],
    ) -> tuple[StringQuoteMetadata, ...]:
        """Return quote metadata for all string tokens."""
        result: list[StringQuoteMetadata] = []
        for token in tokens:
            if token.kind != STRING:
                continue
            result.append(self._metadata_from_token(token=token))
        return tuple(result)

    def _metadata_from_token(
        self,
        *,
        token: SourceToken,
    ) -> StringQuoteMetadata:
        """Create quote metadata for a string token."""
        prefix: str = self._prefix(text=token.text)
        body_start: int = len(prefix)
        quote: StringQuoteKind = self._quote_kind(text=token.text[body_start:])
        return StringQuoteMetadata(
            span=token.span,
            quote=quote,
            prefix=prefix,
        )

    def _prefix(self, *, text: str) -> str:
        """Return a Python string prefix such as ``r`` or ``f``."""
        index: int = 0
        while index < len(text) and text[index].isalpha():
            index += 1
        return text[:index]

    def _quote_kind(self, *, text: str) -> StringQuoteKind:
        """Return the quote style used by a token body."""
        if text.startswith("'''"):
            return StringQuoteKind.TRIPLE_SINGLE
        if text.startswith('"""'):
            return StringQuoteKind.TRIPLE_DOUBLE
        if text.startswith("'"):
            return StringQuoteKind.SINGLE
        return StringQuoteKind.DOUBLE


class ParenthesisAnalyzer:
    """Extract parenthesis pairs from token streams."""

    def analyze(
        self,
        *,
        tokens: tuple[SourceToken, ...],
    ) -> tuple[ParenthesisMetadata, ...]:
        """Return metadata for matched parenthesis pairs."""
        stack: list[SourceToken] = []
        pairs: list[ParenthesisMetadata] = []
        for token in tokens:
            if token.exact_kind == LPAR:
                stack.append(token)
                continue
            if token.exact_kind != RPAR or not stack:
                continue
            opening: SourceToken = stack.pop()
            outer_span: SourceSpan = SourceSpan(
                start=opening.span.start,
                end=token.span.end,
            )
            inner_span: SourceSpan = SourceSpan(
                start=opening.span.end,
                end=token.span.start,
            )
            pairs.append(
                ParenthesisMetadata(
                    outer_span=outer_span,
                    inner_span=inner_span,
                ),
            )
        return tuple(pairs)


class AstSpanReader:
    """Read source spans from AST nodes without assuming attributes exist."""

    def span(self, *, node: AST) -> SourceSpan | None:
        """Return the source span of a node when available."""
        lineno: int | None = self._int_attr(node=node, name="lineno")
        col_offset: int | None = self._int_attr(node=node, name="col_offset")
        end_lineno: int | None = self._int_attr(node=node, name="end_lineno")
        end_col_offset: int | None = self._int_attr(
            node=node,
            name="end_col_offset",
        )
        if (
            lineno is None
            or col_offset is None
            or end_lineno is None
            or end_col_offset is None
        ):
            return None
        return SourceSpan(
            start=SourcePosition(line=lineno, column=col_offset),
            end=SourcePosition(line=end_lineno, column=end_col_offset),
        )

    def _int_attr(self, *, node: AST, name: str) -> int | None:
        """Return an integer AST attribute if present."""
        value: object = getattr(node, name, None)
        if isinstance(value, int):
            return value
        return None


class TokenMetadataNodeFactory:
    """Create custom AST metadata nodes from parsed AST and tokens."""

    def __init__(self) -> None:
        """Initialize the metadata-node factory."""
        self._span_reader: AstSpanReader = AstSpanReader()

    def quoted_nodes(
        self,
        *,
        module: Module,
        quotes: tuple[StringQuoteMetadata, ...],
    ) -> tuple[QuotedConstantNode, ...]:
        """Create custom quote-preserving nodes for string constants."""
        quote_by_span: dict[tuple[int, int, int, int], StringQuoteMetadata] = {
            item.span.key(): item for item in quotes
        }
        nodes: list[QuotedConstantNode] = []
        for node in self._walk(module=module):
            if not isinstance(node, Constant):
                continue
            if not isinstance(node.value, str):
                continue
            span: SourceSpan | None = self._span_reader.span(node=node)
            if span is None:
                continue
            metadata: StringQuoteMetadata | None = quote_by_span.get(
                span.key(),
            )
            if metadata is None:
                continue
            nodes.append(QuotedConstantNode(value=node, metadata=metadata))
        return tuple(nodes)

    def parenthesized_nodes(
        self,
        *,
        module: Module,
        parentheses: tuple[ParenthesisMetadata, ...],
    ) -> tuple[ParenthesizedExpressionNode, ...]:
        """Create custom nodes for expressions enclosed by parentheses."""
        nodes: list[ParenthesizedExpressionNode] = []
        for node in self._walk(module=module):
            if not isinstance(node, expr):
                continue
            span: SourceSpan | None = self._span_reader.span(node=node)
            if span is None:
                continue
            metadata: ParenthesisMetadata | None = self._parenthesis_for(
                span=span,
                parentheses=parentheses,
            )
            if metadata is None:
                continue
            nodes.append(
                ParenthesizedExpressionNode(value=node, metadata=metadata),
            )
        return tuple(nodes)

    def _parenthesis_for(
        self,
        *,
        span: SourceSpan,
        parentheses: tuple[ParenthesisMetadata, ...],
    ) -> ParenthesisMetadata | None:
        """Return matching parenthesis metadata for a node span."""
        for metadata in parentheses:
            if metadata.inner_span.encloses(inner=span):
                return metadata
        return None

    def _walk(self, *, module: Module) -> tuple[AST, ...]:
        """Return all nodes in the module tree."""
        return tuple(walk(node=module))


class TokenizedAstParser:
    """Parse Python source with token and preservation metadata."""

    def parse_module(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> TokenizedParseResult:
        """Parse source into an AST module plus token metadata."""
        module: Module = parse(
            source=source,
            filename=filename,
            mode="exec",
            type_comments=True,
        )
        token_stream: tuple[SourceToken, ...] = self._tokens(source=source)
        quotes: tuple[StringQuoteMetadata, ...] = (
            StringQuoteAnalyzer().analyze(
                tokens=token_stream,
            )
        )
        parentheses: tuple[ParenthesisMetadata, ...] = (
            ParenthesisAnalyzer().analyze(
                tokens=token_stream,
            )
        )
        metadata_factory: TokenMetadataNodeFactory = TokenMetadataNodeFactory()
        quoted_nodes: tuple[QuotedConstantNode, ...] = (
            metadata_factory.quoted_nodes(
                module=module,
                quotes=quotes,
            )
        )
        parenthesized_nodes: tuple[ParenthesizedExpressionNode, ...] = (
            metadata_factory.parenthesized_nodes(
                module=module,
                parentheses=parentheses,
            )
        )
        return TokenizedParseResult(
            module=module,
            tokens=token_stream,
            string_quotes=quotes,
            parentheses=parentheses,
            quoted_nodes=quoted_nodes,
            parenthesized_nodes=parenthesized_nodes,
            body=BodyBlockNode(body=self._body_after_imports(module=module)),
            source=source,
        )

    def _body_after_imports(self, *, module: Module) -> tuple[stmt, ...]:
        """Return the code body after module docstring and imports."""
        index: int = 0
        if module.body and self._is_module_docstring(node=module.body[0]):
            index = 1
        while index < len(module.body) and isinstance(
            module.body[index],
            Import | ImportFrom,
        ):
            index += 1
        return tuple(module.body[index:])

    def _is_module_docstring(self, *, node: stmt) -> bool:
        """Return whether a statement is a module docstring."""
        return (
            isinstance(node, Expr)
            and isinstance(node.value, Constant)
            and isinstance(node.value.value, str)
        )

    def _tokens(self, *, source: str) -> tuple[SourceToken, ...]:
        """Tokenize source into semantic token metadata."""
        reader: StringIO = StringIO(initial_value=source)
        return tuple(
            SourceToken.from_token(token=token)
            for token in generate_tokens(readline=reader.readline)
        )


class QuotePreservingStringRenderer:
    """Render string constants with explicit quote styles."""

    def render(
        self,
        *,
        value: str,
        quote: StringQuoteKind,
        prefix: str = "",
    ) -> str:
        """Render a string value using the requested quote style."""
        escaped: str = self._escape(value=value, quote=quote)
        return f"{prefix}{quote.value}{escaped}{quote.value}"

    def _escape(self, *, value: str, quote: StringQuoteKind) -> str:
        """Escape a string for a quote style."""
        if quote in {StringQuoteKind.SINGLE, StringQuoteKind.TRIPLE_SINGLE}:
            return value.replace("\\", "\\\\").replace("'", "\\'")
        return value.replace("\\", "\\\\").replace('"', '\\"')


class TokenAwareUnparser:
    """Unparse AST while honoring token preservation metadata when possible."""

    def __init__(self, *, parsed: TokenizedParseResult | None = None) -> None:
        """Initialize the token-aware unparser."""
        self._parsed: TokenizedParseResult | None = parsed
        self._span_reader: AstSpanReader = AstSpanReader()
        self._string_renderer: QuotePreservingStringRenderer = (
            QuotePreservingStringRenderer()
        )

    def unparse_node(self, *, node: AST) -> str:
        """Render a node to source code."""
        rendered: str
        if isinstance(node, BodyBlockNode):
            rendered = self._unparse_body_block(node=node)
        elif isinstance(node, GeneratedPreambleBlockNode):
            rendered = self._unparse_preamble(node=node)
        elif isinstance(node, ParenthesizedExpressionNode):
            rendered = f"({self.unparse_node(node=node.value)})"
        elif isinstance(node, QuotedConstantNode):
            rendered = self._unparse_quoted_constant(node=node)
        elif isinstance(node, SemanticCastNode):
            rendered = self._unparse_semantic_cast(node=node)
        else:
            rendered = self._unparse_standard_node(node=node)
        return rendered

    def _unparse_standard_node(self, *, node: AST) -> str:
        """Render a normal AST node with optional token metadata."""
        metadata: StringQuoteMetadata | None = None
        if isinstance(node, Constant) and isinstance(node.value, str):
            metadata = self._quote_metadata(
                node=node,
            )
        if metadata is not None and isinstance(node, Constant):
            value_text: str = str(object=node.value)
            rendered: str = self._string_renderer.render(
                value=value_text,
                quote=metadata.quote,
                prefix=metadata.prefix,
            )
        else:
            rendered = unparse(ast_obj=fix_missing_locations(node=node))
        if isinstance(node, expr) and self._is_parenthesized(node=node):
            return f"({rendered})"
        return rendered

    def _unparse_semantic_cast(self, *, node: SemanticCastNode) -> str:
        """Render a semantic cast node when it has an expression target."""
        return self.unparse_node(node=node.require_call_expr())

    def module_with_preamble(
        self,
        *,
        preamble: GeneratedPreambleBlockNode,
        body: BodyBlockNode,
    ) -> str:
        """Render generated preamble followed by a body block."""
        preamble_text: str = self._unparse_preamble(node=preamble)
        body_text: str = self._unparse_body_block(node=body)
        if not preamble_text:
            return body_text
        if not body_text:
            return preamble_text
        return f"{preamble_text}\n\n{body_text}"

    def _unparse_body_block(self, *, node: BodyBlockNode) -> str:
        """Render a body block, preserving original source when possible."""
        original: str | None = self._original_block_text(statements=node.body)
        if original is not None:
            return original
        return self._unparse_statements(statements=node.body)

    def _original_block_text(
        self,
        *,
        statements: tuple[stmt, ...],
    ) -> str | None:
        """Return original source text for an unchanged parsed block."""
        if self._parsed is None or not statements:
            return None
        first_span: SourceSpan | None = self._span_reader.span(
            node=statements[0],
        )
        last_span: SourceSpan | None = self._span_reader.span(
            node=statements[-1],
        )
        if first_span is None or last_span is None:
            return None
        return self._source_slice(start=first_span.start, end=last_span.end)

    def _source_slice(
        self,
        *,
        start: SourcePosition,
        end: SourcePosition,
    ) -> str:
        """Return exact source text between two positions."""
        if self._parsed is None:
            return ""
        lines: list[str] = self._parsed.source.splitlines(keepends=True)
        if start.line == end.line:
            return lines[start.line - 1][start.column : end.column]
        parts: list[str] = [lines[start.line - 1][start.column :]]
        parts.extend(lines[start.line : end.line - 1])
        parts.append(lines[end.line - 1][: end.column])
        return "".join(parts)

    def _unparse_preamble(self, *, node: GeneratedPreambleBlockNode) -> str:
        """Render a generated preamble block."""
        return self._unparse_statements(statements=node.ordered_nodes)

    def _unparse_statements(self, *, statements: tuple[stmt, ...]) -> str:
        """Render a tuple of statements as source."""
        if not statements:
            return ""
        module: Module = Module(body=list(statements), type_ignores=[])
        return unparse(ast_obj=fix_missing_locations(node=module))

    def _unparse_quoted_constant(self, *, node: QuotedConstantNode) -> str:
        """Render a custom quote-preserving constant."""
        value: str = str(object=node.value.value)
        return self._string_renderer.render(
            value=value,
            quote=node.metadata.quote,
            prefix=node.metadata.prefix,
        )

    def _quote_metadata(self, *, node: Constant) -> StringQuoteMetadata | None:
        """Return quote metadata for a parsed string constant."""
        if self._parsed is None:
            return None
        span: SourceSpan | None = self._span_reader.span(node=node)
        if span is None:
            return None
        for metadata in self._parsed.string_quotes:
            if metadata.span.key() == span.key():
                return metadata
        return None

    def _is_parenthesized(self, *, node: expr) -> bool:
        """Return whether a parsed expression was parenthesized."""
        if self._parsed is None:
            return False
        span: SourceSpan | None = self._span_reader.span(node=node)
        if span is None:
            return False
        return any(
            metadata.inner_span.encloses(inner=span)
            for metadata in self._parsed.parentheses
        )


class TypeAliasNameInferer:
    """Infer sensible PascalCase names for generated type aliases.

    When no explicit alias name is provided, the manager derives one
    from the aliased type expression.  Names are formed by extracting
    a canonical word from the underlying expression (for example
    ``List[int]`` yields ``ListAlias``) and converting it to
    PascalCase.  All inferred names are suffixed with ``Alias`` to
    indicate their purpose.  The validator ensures that the result is a
    valid Python identifier.
    """

    def __init__(self) -> None:
        """Initialize the alias-name inferer."""
        self._validator: IdentifierValidator = IdentifierValidator()

    def infer(self, *, value: TypeExpression) -> str:
        """Infer a type alias name from a type expression."""
        raw: str = self._raw_name(value=value)
        name: str = self._pascal_case(words=tuple(raw.split(sep="_")))
        if not name.endswith("Alias"):
            name = f"{name}Alias"
        self._validator.validate_identifier(name=name, label="type alias")
        return name

    def _raw_name(self, *, value: TypeExpression) -> str:
        """Return a raw name fragment for a type expression."""
        raw_name: str = "type"
        if isinstance(value, BuiltinTypeRef):
            raw_name = value.name
        elif isinstance(value, ImportedTypeRef):
            raw_name = value.source.imported_name
        elif isinstance(value, LocalTypeRef):
            raw_name = value.name
        elif isinstance(value, GenericTypeRef):
            raw_name = self._raw_name(value=value.origin)
        elif isinstance(value, UnionTypeRef):
            raw_name = "union"
        elif isinstance(value, FlexibleCallableTypeRef | CallableTypeRef):
            raw_name = "callable"
        elif isinstance(value, LiteralTypeRef):
            raw_name = "literal"
        return raw_name

    def _pascal_case(self, *, words: tuple[str, ...]) -> str:
        """Convert words to PascalCase."""
        return "".join(word[:1].upper() + word[1:] for word in words if word)


class ExistingTypeAliasIndex:
    """Index existing Python 3.13 type aliases by name and value text."""

    def __init__(self, *, aliases: Iterable[AstTypeAlias]) -> None:
        """Initialize the existing alias index."""
        self._by_name: dict[str, AstTypeAlias] = {}
        self._by_value_text: dict[str, AstTypeAlias] = {}
        for node in aliases:
            alias_name: str = self._alias_name(node=node)
            self._by_name[alias_name] = node
            self._by_value_text[unparse(ast_obj=node.value)] = node

    def find_by_name(self, *, name: str) -> AstTypeAlias | None:
        """Return an existing type alias by name."""
        return self._by_name.get(name)

    def find_by_value(self, *, value_node: expr) -> AstTypeAlias | None:
        """Return an existing type alias by rendered value."""
        return self._by_value_text.get(unparse(ast_obj=value_node))

    def _alias_name(self, *, node: AstTypeAlias) -> str:
        """Return the alias name."""
        return node.name.id


class TypeAliasNodeBuilder:
    """Construct ``ast.TypeAlias`` nodes from semantic specifications.

    This helper validates alias names, converts type parameters to their
    corresponding ``ast.type_param`` nodes using a
    :class:`TypeExpressionResolver`, and renders the alias value into
    an ``ast.expr`` suitable for runtime evaluation.  The resulting
    ``AstTypeAlias`` can be inserted into a module body.  See
    :class:`TypeAliasSpec` for the semantic input.
    """

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the type-alias node builder."""
        self._resolver: TypeExpressionResolver = resolver
        self._validator: IdentifierValidator = IdentifierValidator()

    def build(self, *, spec: TypeAliasSpec) -> AstTypeAlias:
        """Build a Python 3.13 type-alias AST node."""
        self._validator.validate_identifier(name=spec.name, label="type alias")
        type_params: list[type_param] = [
            param.to_ast(resolver=self._resolver) for param in spec.type_params
        ]
        value_node: expr = spec.value.to_ast(
            resolver=self._resolver,
            _use=ImportUseSite.runtime(owner=spec.name),
        )
        return AstTypeAlias(
            name=Name(id=spec.name, ctx=Store()),
            type_params=type_params,
            value=value_node,
        )


class TypeAliasManager:
    """Manage semantic type aliases with reuse and automatic name inference.

    The manager keeps track of existing type aliases in a module and
    synthesises new ones on demand.  When adding an alias, it first
    consults the existing alias index to detect matches by name or by
    alias value, returning a :class:`TypeAliasRegistration` that
    indicates whether an existing alias was reused.  If no match is
    found, the manager uses the :class:`TypeAliasNameInferer` to
    generate a fresh PascalCase name (unless an explicit name was
    provided) and builds a new ``ast.TypeAlias`` node via the
    :class:`TypeAliasNodeBuilder`.  Registrations are recorded so that
    :attr:`nodes` returns only the newly created alias nodes for
    insertion into the code.  Duplicate value alias requests share the
    same name, ensuring a single canonical alias per distinct type
    expression.
    """

    def __init__(
        self,
        *,
        resolver: TypeExpressionResolver,
        existing_aliases: Iterable[AstTypeAlias] = (),
    ) -> None:
        """Initialize the type-alias manager."""
        self._builder: TypeAliasNodeBuilder = TypeAliasNodeBuilder(
            resolver=resolver,
        )
        self._existing: ExistingTypeAliasIndex = ExistingTypeAliasIndex(
            aliases=existing_aliases,
        )
        self._inferer: TypeAliasNameInferer = TypeAliasNameInferer()
        self._registrations: list[TypeAliasRegistration] = []
        self._names_by_key: dict[str, str] = {}

    @property
    def nodes(self) -> tuple[AstTypeAlias, ...]:
        """Return new type-alias nodes ordered by alias name."""
        new_nodes: list[AstTypeAlias] = [
            registration.node
            for registration in self._registrations
            if not registration.is_existing
        ]
        return tuple(sorted(new_nodes, key=self._node_name))

    def add(
        self,
        *,
        value: TypeExpression,
        name: str | None = None,
        type_params: tuple[TypeAliasTypeParameterSpec, ...] = (),
    ) -> TypeAliasRegistration:
        """Add or reuse a semantic type alias."""
        normalized_value: TypeExpression = value
        resolved_name: str = self._name_for(value=normalized_value, name=name)
        spec: TypeAliasSpec = TypeAliasSpec(
            name=resolved_name,
            value=normalized_value,
            type_params=type_params,
        )
        by_name: AstTypeAlias | None = self._existing.find_by_name(
            name=spec.name,
        )
        if by_name is not None:
            return TypeAliasRegistration(
                spec=spec,
                node=by_name,
                is_existing=True,
                match_reason="name",
            )
        node: AstTypeAlias = self._builder.build(spec=spec)
        by_value: AstTypeAlias | None = self._existing.find_by_value(
            value_node=node.value,
        )
        if by_value is not None:
            return TypeAliasRegistration(
                spec=spec,
                node=by_value,
                is_existing=True,
                match_reason="value",
            )
        registration: TypeAliasRegistration = TypeAliasRegistration(
            spec=spec,
            node=node,
            is_existing=False,
            match_reason="new",
        )
        self._registrations.append(registration)
        return registration

    def _name_for(self, *, value: TypeExpression, name: str | None) -> str:
        """Return explicit, reused, or inferred alias name."""
        if name is not None:
            return name
        key: str = value.key()
        existing: str | None = self._names_by_key.get(key)
        if existing is not None:
            return existing
        inferred: str = self._free_name(base=self._inferer.infer(value=value))
        self._names_by_key[key] = inferred
        return inferred

    def _free_name(self, *, base: str) -> str:
        """Return a free generated alias name."""
        used: set[str] = set(self._names_by_key.values())
        if base not in used:
            return base
        index: int = 1
        while True:
            candidate: str = f"{base}{index}"
            if candidate not in used:
                return candidate
            index += 1

    def _node_name(self, node: AstTypeAlias) -> str:
        """Return a sortable node name."""
        return node.name.id


class SemanticModuleComposer:
    """Compose generated imports/declarations before a semantic body block."""

    def compose(
        self,
        *,
        block: SemanticDeclarationBlock,
        body: BodyBlockNode,
    ) -> Module:
        """Compose a full AST module from generated declarations and body."""
        module: Module = Module(
            body=[*block.ordered_nodes, *body.body],
            type_ignores=[],
        )
        return fix_missing_locations(node=module)


class SemanticCodegenCollector(ProtocolTypeBlockCollector):
    """Extended collector with Python 3.13 type aliases and parse helpers."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the extended collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self.aliases: TypeAliasManager = TypeAliasManager(
            resolver=self._resolver,
            existing_aliases=existing_type_aliases,
        )

    def type_alias(
        self,
        *,
        value: TypeExpression,
        name: str | None = None,
        type_params: tuple[TypeAliasTypeParameterSpec, ...] = (),
    ) -> TypeAliasRegistration:
        """Create or reuse a Python 3.13 semantic type alias."""
        return self.aliases.add(
            value=value,
            name=name,
            type_params=type_params,
        )

    def build_declaration_block(self) -> SemanticDeclarationBlock:
        """Build imports, TypeVars, ParamSpecs, aliases, and protocols."""
        top_block: GeneratedTopBlock = self.build_block()
        typevar_nodes: list[stmt] = []
        paramspec_nodes: list[stmt] = []
        protocol_nodes: list[stmt] = []
        for node in top_block.declaration_nodes_after_imports:
            self._append_declaration_node(
                node=node,
                typevar_nodes=typevar_nodes,
                paramspec_nodes=paramspec_nodes,
                protocol_nodes=protocol_nodes,
            )
        return SemanticDeclarationBlock(
            imports=top_block.missing_import_nodes,
            typevars=tuple(typevar_nodes),
            paramspecs=tuple(paramspec_nodes),
            type_aliases=tuple(self.aliases.nodes),
            protocols=tuple(protocol_nodes),
            constants=(),
        )

    def compose_module(self, *, body: BodyBlockNode) -> Module:
        """Compose a full module with generated preamble before body."""
        return SemanticModuleComposer().compose(
            block=self.build_declaration_block(),
            body=body,
        )

    def _append_declaration_node(
        self,
        *,
        node: stmt,
        typevar_nodes: list[stmt],
        paramspec_nodes: list[stmt],
        protocol_nodes: list[stmt],
    ) -> None:
        """Classify a generated declaration node."""
        if isinstance(node, Assign):
            name_text: str = self._assign_call_name(node=node)
            if name_text == "TypeVar":
                typevar_nodes.append(node)
                return
            if name_text == "ParamSpec":
                paramspec_nodes.append(node)
                return
        protocol_nodes.append(node)

    def _assign_call_name(self, *, node: Assign) -> str:
        """Return the called helper name in an assignment, when present."""
        if not isinstance(node.value, Call):
            return ""
        if isinstance(node.value.func, Name):
            return node.value.func.id
        if isinstance(node.value.func, Attribute):
            return node.value.func.attr
        return ""


class ParseUnparseToolkit:
    """Facade for token-aware parse and preservation-aware unparse."""

    def parse(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> TokenizedParseResult:
        """Parse source with token metadata."""
        return TokenizedAstParser().parse_module(
            source=source,
            filename=filename,
        )

    def unparse(
        self,
        *,
        node: AST,
        parsed: TokenizedParseResult | None = None,
    ) -> str:
        """Unparse a node with optional token metadata."""
        return TokenAwareUnparser(parsed=parsed).unparse_node(node=node)

    def unparse_module_with_preamble(
        self,
        *,
        preamble: GeneratedPreambleBlockNode,
        body: BodyBlockNode,
        parsed: TokenizedParseResult | None = None,
    ) -> str:
        """Unparse a generated preamble followed by parsed body."""
        return TokenAwareUnparser(parsed=parsed).module_with_preamble(
            preamble=preamble,
            body=body,
        )


class CommentAnalyzer:
    """Extract comments from a token stream with indentation metadata."""

    def analyze(
        self,
        *,
        tokens: tuple[SourceToken, ...],
    ) -> tuple[CommentMetadata, ...]:
        """Return comment metadata for all comment tokens."""
        comments: list[CommentMetadata] = []
        for token in tokens:
            if token.kind != COMMENT:
                continue
            comments.append(
                CommentMetadata(
                    span=token.span,
                    text=token.text,
                    indent=" " * token.span.start.column,
                ),
            )
        return tuple(comments)


class CommentAwareTokenizedAstParser:
    """Parse Python source with token, quote, parenthesis, and comment data."""

    def parse_module(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> CommentAwareParseResult:
        """Parse source into a comment-aware semantic parse result."""
        parsed: TokenizedParseResult = TokenizedAstParser().parse_module(
            source=source,
            filename=filename,
        )
        comments: tuple[CommentMetadata, ...] = CommentAnalyzer().analyze(
            tokens=parsed.tokens,
        )
        return CommentAwareParseResult(parsed=parsed, comments=comments)


class CommentPreservationIndex:
    """Index comments by statement spans for transformed unparsing."""

    def __init__(self, *, parsed: CommentAwareParseResult) -> None:
        """Initialize the comment preservation index."""
        self._parsed: CommentAwareParseResult = parsed
        self._span_reader: AstSpanReader = AstSpanReader()
        self._comments_by_line: dict[int, list[CommentMetadata]] = (
            self._build_line_index(comments=parsed.comments)
        )

    def comments_for(
        self,
        *,
        statement: stmt,
        previous_statement: stmt | None,
        minimum_line: int = 1,
    ) -> StatementCommentBlock:
        """Return leading and inline comments for a statement."""
        span: SourceSpan | None = self._span_reader.span(node=statement)
        if span is None:
            return StatementCommentBlock(leading=(), inline=None)
        start_line: int = max(
            minimum_line,
            self._leading_start(previous_statement=previous_statement),
        )
        leading_comments: tuple[CommentMetadata, ...] = self._comments_between(
            start_line=start_line,
            end_line=span.start.line - 1,
        )
        inline_comment: CommentMetadata | None = self._inline_comment(
            span=span,
        )
        return StatementCommentBlock(
            leading=leading_comments,
            inline=inline_comment,
        )

    def _leading_start(self, *, previous_statement: stmt | None) -> int:
        """Return the first line considered for leading comments."""
        if previous_statement is None:
            return 1
        previous_span: SourceSpan | None = self._span_reader.span(
            node=previous_statement,
        )
        if previous_span is None:
            return 1
        return previous_span.end.line + 1

    def _comments_between(
        self,
        *,
        start_line: int,
        end_line: int,
    ) -> tuple[CommentMetadata, ...]:
        """Return comments between two line numbers, inclusive."""
        if end_line < start_line:
            return ()
        comments: list[CommentMetadata] = []
        line_number: int
        for line_number in range(start_line, end_line + 1):
            comments.extend(self._comments_by_line.get(line_number, ()))
        return tuple(comments)

    def _inline_comment(self, *, span: SourceSpan) -> CommentMetadata | None:
        """Return a comment on the same line as a statement end."""
        candidates: list[CommentMetadata] = self._comments_by_line.get(
            span.end.line,
            [],
        )
        for comment in candidates:
            if comment.span.start.column >= span.end.column:
                return comment
        return None

    def _build_line_index(
        self,
        *,
        comments: tuple[CommentMetadata, ...],
    ) -> dict[int, list[CommentMetadata]]:
        """Group comments by source line."""
        result: dict[int, list[CommentMetadata]] = {}
        for comment in comments:
            result.setdefault(comment.line, []).append(comment)
        return result


class StatementReplacementRegistry:
    """Track statement replacements keyed by original node identity."""

    def __init__(self) -> None:
        """Initialize the replacement registry."""
        self._replacements: dict[int, StatementReplacement] = {}

    def add(self, *, original: stmt, replacements: tuple[stmt, ...]) -> None:
        """Register replacement statements for an original statement."""
        self._replacements[id(original)] = StatementReplacement(
            original=original,
            replacements=replacements,
        )

    def replacement_for(self, *, original: stmt) -> tuple[stmt, ...] | None:
        """Return replacement statements for an original statement."""
        replacement: StatementReplacement | None = self._replacements.get(
            id(original),
        )
        if replacement is None:
            return None
        return replacement.replacements


class FunctionTypeHintEditor:
    """Edit function annotations directly in the existing AST tree."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the function type-hint editor."""
        self._resolver: TypeExpressionResolver = resolver
        self._args_builder: AstArgsBuilder = AstArgsBuilder(resolver=resolver)

    def set_return(
        self,
        *,
        function: FunctionDef,
        type_hint: TypeExpression | expr | None,
    ) -> None:
        """Set a function return annotation in place."""
        if type_hint is None:
            function.returns = None
            return
        if isinstance(type_hint, TypeExpression):
            function.returns = self._resolver.annotation(
                value=type_hint,
            )
            return
        function.returns = deepcopy(x=type_hint)

    def set_arguments(
        self,
        *,
        function: FunctionDef,
        arguments: ast_arguments | tuple[ArgumentSpec, ...],
    ) -> None:
        """Set a function argument node in place."""
        if isinstance(arguments, ast_arguments):
            function.args = deepcopy(x=arguments)
            return
        function.args = self._args_builder.build(
            arguments=arguments,
        )

    def set_argument_annotation(
        self,
        *,
        function: FunctionDef,
        name: str,
        type_hint: TypeExpression | expr | None,
    ) -> None:
        """Set one function argument annotation in place."""
        target: arg = self._find_argument(function=function, name=name)
        if type_hint is None:
            target.annotation = None
            return
        if isinstance(type_hint, TypeExpression):
            target.annotation = self._resolver.annotation(
                value=type_hint,
            )
            return
        target.annotation = deepcopy(x=type_hint)

    def _find_argument(self, *, function: FunctionDef, name: str) -> arg:
        """Find one argument by name or fail."""
        candidates: tuple[arg, ...] = (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
        for candidate in candidates:
            if candidate.arg == name:
                return candidate
        if (
            function.args.vararg is not None
            and function.args.vararg.arg == name
        ):
            return function.args.vararg
        if function.args.kwarg is not None and function.args.kwarg.arg == name:
            return function.args.kwarg
        msg: str = f"Function {function.name!r} has no argument {name!r}."
        fail(message=msg)


class BodyTransformationPlan:
    """Plan in-tree replacements and insertions for a body block."""

    def __init__(self, *, collector: ProtocolTypeBlockCollector) -> None:
        """Initialize the transformation plan."""
        self._collector: ProtocolTypeBlockCollector = collector
        self._replacements: StatementReplacementRegistry = (
            StatementReplacementRegistry()
        )

    def replace_attribute_set(
        self,
        *,
        node: AttributeAssignmentNode,
        variable_name: str = "_attr_name",
    ) -> AttributeSetattrRewriteResult:
        """Replace ``a.b = value`` with name storage plus ``setattr``."""
        result: AttributeSetattrRewriteResult = (
            self._collector.rewrite_attribute_set(
                node=node,
                variable_name=variable_name,
            )
        )
        self._replacements.add(original=node, replacements=result.nodes)
        return result

    def add_override(
        self,
        *,
        original: FunctionDef,
        update: MethodOverrideUpdate,
    ) -> FunctionDef:
        """Add an override to be inserted immediately after its original."""
        return self._collector.overrides.add(original=original, update=update)

    def transformed_body(self, *, body: BodyBlockNode) -> BodyBlockNode:
        """Return a body block with replacements and overrides inserted."""
        transformer: BodyTransformationApplier = BodyTransformationApplier(
            replacements=self._replacements,
            overrides=self._collector.overrides,
        )
        transformed: tuple[stmt, ...] = transformer.transform_statements(
            statements=body.body,
        )
        return BodyBlockNode(body=transformed)


class BodyTransformationApplier:
    """Apply statement replacements and override insertions recursively."""

    def __init__(
        self,
        *,
        replacements: StatementReplacementRegistry,
        overrides: MethodOverrideManager,
    ) -> None:
        """Initialize the body transformation applier."""
        self._replacements: StatementReplacementRegistry = replacements
        self._overrides: MethodOverrideManager = overrides

    def transform_statements(
        self,
        *,
        statements: tuple[stmt, ...],
    ) -> tuple[stmt, ...]:
        """Transform a tuple of statements recursively."""
        transformed: list[stmt] = []
        for statement in statements:
            replacement: tuple[stmt, ...] | None = (
                self._replacements.replacement_for(
                    original=statement,
                )
            )
            if replacement is not None:
                transformed.extend(replacement)
                continue
            transformed_statement: stmt = self._transform_statement(
                statement=statement,
            )
            transformed.append(transformed_statement)
            if isinstance(statement, FunctionDef):
                transformed.extend(
                    self._overrides.nodes_for(original=statement),
                )
        return tuple(transformed)

    def _transform_statement(self, *, statement: stmt) -> stmt:
        """Transform nested statement bodies.

        Preserve the node object.
        """
        if isinstance(statement, ClassDef | FunctionDef):
            statement.body = list(
                self.transform_statements(statements=tuple(statement.body)),
            )
        elif isinstance(statement, If):
            statement.body = list(
                self.transform_statements(statements=tuple(statement.body)),
            )
            statement.orelse = list(
                self.transform_statements(statements=tuple(statement.orelse)),
            )
        return statement


class DeclarationBlockOrganizer:
    """Organize supplied import/declaration blocks for canonical unparsing."""

    def organize(
        self,
        *,
        blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ],
    ) -> GeneratedPreambleBlockNode:
        """Return one canonical preamble node from existing block objects."""
        state: DeclarationBlockBuildState = DeclarationBlockBuildState()
        for block in blocks:
            self._extend_block(block=block, state=state)
        preamble: GeneratedPreambleBlockNode = GeneratedPreambleBlockNode(
            imports=tuple(sorted(state.imports, key=self._statement_text)),
            typevars=tuple(sorted(state.typevars, key=self._assignment_name)),
            paramspecs=tuple(
                sorted(state.paramspecs, key=self._assignment_name),
            ),
            type_aliases=tuple(
                sorted(state.type_aliases, key=self._type_alias_name),
            ),
            protocols=tuple(sorted(state.protocols, key=self._class_name)),
        )
        preamble.constants = tuple(
            sorted(state.constants, key=self._assignment_name),
        )
        return preamble

    def _extend_block(
        self,
        *,
        block: (
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode
        ),
        state: DeclarationBlockBuildState,
    ) -> None:
        """Append one block into mutable category lists."""
        if isinstance(block, GeneratedTopBlock):
            state.imports.extend(block.missing_import_nodes)
            self._categorize_nodes(
                nodes=block.declaration_nodes_after_imports,
                state=state,
            )
            return
        if isinstance(block, SemanticDeclarationBlock):
            state.imports.extend(block.imports)
            state.typevars.extend(block.typevars)
            state.paramspecs.extend(block.paramspecs)
            state.type_aliases.extend(block.type_aliases)
            state.protocols.extend(block.protocols)
            state.constants.extend(block.constants)
            return
        state.imports.extend(block.imports)
        state.typevars.extend(block.typevars)
        state.paramspecs.extend(block.paramspecs)
        state.type_aliases.extend(block.type_aliases)
        state.protocols.extend(block.protocols)
        state.constants.extend(block.constants)

    def _categorize_nodes(
        self,
        *,
        nodes: tuple[stmt, ...],
        state: DeclarationBlockBuildState,
    ) -> None:
        """Categorize loose declaration nodes."""
        for node in nodes:
            if isinstance(node, Assign):
                call_name: str = self._assign_call_name(node=node)
                if call_name == "TypeVar":
                    state.typevars.append(node)
                    continue
                if call_name == "ParamSpec":
                    state.paramspecs.append(node)
                    continue
            if isinstance(node, AstTypeAlias):
                state.type_aliases.append(node)
                continue
            state.protocols.append(node)

    def _assign_call_name(self, *, node: Assign) -> str:
        """Return the helper call name used by an assignment."""
        if not isinstance(node.value, Call):
            return ""
        if isinstance(node.value.func, Name):
            return node.value.func.id
        if isinstance(node.value.func, Attribute):
            return node.value.func.attr
        return ""

    def _statement_text(self, node: stmt) -> str:
        """Return statement source text for sorting."""
        return unparse(ast_obj=fix_missing_locations(node=node))

    def _assignment_name(self, node: stmt) -> str:
        """Return assignment target name for sorting."""
        if (
            isinstance(node, Assign)
            and node.targets
            and isinstance(node.targets[0], Name)
        ):
            return node.targets[0].id
        return self._statement_text(node=node)

    def _type_alias_name(self, node: stmt) -> str:
        """Return type-alias name for sorting."""
        if isinstance(node, AstTypeAlias):
            return node.name.id
        return self._statement_text(node=node)

    def _class_name(self, node: stmt) -> str:
        """Return class name for sorting."""
        if isinstance(node, ClassDef):
            return node.name
        return self._statement_text(node=node)


class CommentPreservingTokenAwareUnparser(TokenAwareUnparser):
    """Token-aware unparser that can reattach existing comments."""

    def __init__(
        self,
        *,
        parsed: CommentAwareParseResult | None = None,
    ) -> None:
        """Initialize the comment-preserving unparser."""
        super().__init__(parsed=None if parsed is None else parsed.parsed)
        self._comment_parsed: CommentAwareParseResult | None = parsed
        self._comment_index: CommentPreservationIndex | None = (
            None if parsed is None else CommentPreservationIndex(parsed=parsed)
        )

    def _unparse_body_block(self, *, node: BodyBlockNode) -> str:
        """Render a body block with comment preservation when available."""
        if self._comment_index is None:
            return super()._unparse_body_block(node=node)
        return self._unparse_commented_statements(statements=node.body)

    def unparse_transformed_body(self, *, body: BodyBlockNode) -> str:
        """Render a transformed body block with preserved comments."""
        if self._comment_index is None:
            return self._unparse_body_block(node=body)
        return self._unparse_commented_statements(statements=body.body)

    def unparse_module_with_blocks(
        self,
        *,
        blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ],
        body: BodyBlockNode,
    ) -> str:
        """Organize generated blocks and render them before a body."""
        preamble: GeneratedPreambleBlockNode = (
            DeclarationBlockOrganizer().organize(
                blocks=blocks,
            )
        )
        preamble_text: str = self._unparse_preamble(node=preamble)
        body_text: str = self.unparse_transformed_body(body=body)
        if not preamble_text:
            return body_text
        if not body_text:
            return preamble_text
        return f"{preamble_text}\n\n{body_text}"

    def _unparse_commented_statements(
        self,
        *,
        statements: tuple[stmt, ...],
        start_line: int = 1,
    ) -> str:
        """Render statements with leading and inline comments."""
        if self._comment_index is None:
            return self._unparse_statements(statements=statements)
        rendered_parts: list[str] = []
        previous_statement: stmt | None = None
        for statement in statements:
            comment_block: StatementCommentBlock = (
                self._comment_index.comments_for(
                    statement=statement,
                    previous_statement=previous_statement,
                    minimum_line=start_line,
                )
            )
            rendered_parts.extend(
                self._render_leading_comments(comments=comment_block.leading),
            )
            rendered_statement: str = self._unparse_standard_node(
                node=statement,
            )
            if comment_block.inline is not None:
                rendered_statement = (
                    f"{rendered_statement}  {comment_block.inline.text}"
                )
            rendered_parts.append(rendered_statement)
            previous_statement = statement
        return "\n".join(part for part in rendered_parts if part)

    def _render_leading_comments(
        self,
        *,
        comments: tuple[CommentMetadata, ...],
    ) -> list[str]:
        """Render leading comments relative to the active block."""
        return [comment.text for comment in comments]

    def _unparse_standard_node(self, *, node: AST) -> str:
        """Render normal nodes, preserving nested comments when possible."""
        if self._comment_index is not None and isinstance(node, ClassDef):
            return self._unparse_classdef(node=node)
        if self._comment_index is not None and isinstance(node, FunctionDef):
            return self._unparse_functiondef(node=node)
        return super()._unparse_standard_node(node=node)

    def _unparse_classdef(self, *, node: ClassDef) -> str:
        """Render a class definition with a comment-aware body."""
        header: str = self._compound_header(node=node)
        body_text: str = self._unparse_commented_statements(
            statements=tuple(node.body),
            start_line=getattr(node, "lineno", 0) + 1,
        )
        return f"{header}\n{self._indent(text=body_text)}"

    def _unparse_functiondef(self, *, node: FunctionDef) -> str:
        """Render a function definition with a comment-aware body."""
        header: str = self._compound_header(node=node)
        body_text: str = self._unparse_commented_statements(
            statements=tuple(node.body),
            start_line=getattr(node, "lineno", 0) + 1,
        )
        return f"{header}\n{self._indent(text=body_text)}"

    def _compound_header(self, *, node: ClassDef | FunctionDef) -> str:
        """Return the source header for a compound statement."""
        clone: ClassDef | FunctionDef = deepcopy(x=node)
        clone.body = [Pass()]
        source: str = unparse(ast_obj=fix_missing_locations(node=clone))
        return source.splitlines()[0]

    def _indent(self, *, text: str) -> str:
        """Indent a rendered block by one Python indentation level."""
        if not text:
            return "    pass"
        return "\n".join(
            f"    {line}" if line else line for line in text.splitlines()
        )


class CommentAwareParseUnparseToolkit(ParseUnparseToolkit):
    """Facade for comment-aware parse, transform, and unparse operations."""

    def parse_comments(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> CommentAwareParseResult:
        """Parse source with token and comment metadata."""
        return CommentAwareTokenizedAstParser().parse_module(
            source=source,
            filename=filename,
        )

    def unparse_with_comments(
        self,
        *,
        body: BodyBlockNode,
        parsed: CommentAwareParseResult | None = None,
    ) -> str:
        """Unparse a body block while preserving known comments."""
        unparser: CommentPreservingTokenAwareUnparser = (
            CommentPreservingTokenAwareUnparser(parsed=parsed)
        )
        return unparser.unparse_transformed_body(body=body)

    def unparse_module_with_blocks_and_comments(
        self,
        *,
        blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ],
        body: BodyBlockNode,
        parsed: CommentAwareParseResult | None = None,
    ) -> str:
        """Unparse generated blocks before a possibly transformed body."""
        unparser: CommentPreservingTokenAwareUnparser = (
            CommentPreservingTokenAwareUnparser(parsed=parsed)
        )
        return unparser.unparse_module_with_blocks(blocks=blocks, body=body)


class DocstringEditor:
    """Add, remove, read, and edit function/class/module docstrings."""

    def get(self, *, owner: DocstringOwner) -> str | None:
        """Return the current docstring for an owner node."""
        body: list[stmt] = self._body_for(owner=owner)
        index: int | None = self._docstring_index(body=body)
        if index is None:
            return None
        doc_node: stmt = body[index]
        if not isinstance(doc_node, Expr):
            return None
        if not isinstance(doc_node.value, Constant):
            return None
        if not isinstance(doc_node.value.value, str):
            return None
        return doc_node.value.value

    def set(self, *, owner: DocstringOwner, text: str) -> Expr:
        """Set or create a docstring and return the docstring node."""
        body: list[stmt] = self._body_for(owner=owner)
        node: Expr = self._docstring_node(text=text)
        index: int | None = self._docstring_index(body=body)
        if index is None:
            body.insert(0, node)
            return node
        body[index] = node
        return node

    def add(self, *, owner: DocstringOwner, text: str) -> Expr:
        """Add a docstring, failing when one already exists."""
        existing: str | None = self.get(owner=owner)
        if existing is not None:
            fail(message="Docstring already exists.")
        return self.set(owner=owner, text=text)

    def edit(self, *, owner: DocstringOwner, text: str) -> Expr:
        """Edit an existing docstring, failing when none exists."""
        existing: str | None = self.get(owner=owner)
        if existing is None:
            fail(message="Cannot edit a missing docstring.")
        return self.set(owner=owner, text=text)

    def remove(self, *, owner: DocstringOwner) -> str | None:
        """Remove a docstring and return its previous value."""
        body: list[stmt] = self._body_for(owner=owner)
        index: int | None = self._docstring_index(body=body)
        if index is None:
            return None
        previous: str | None = self.get(owner=owner)
        del body[index]
        return previous

    def get_function(self, *, function: FunctionDef) -> str | None:
        """Return a function docstring."""
        return self.get(owner=function)

    def set_function(self, *, function: FunctionDef, text: str) -> Expr:
        """Set or create a function docstring."""
        return self.set(owner=function, text=text)

    def add_function(self, *, function: FunctionDef, text: str) -> Expr:
        """Add a function docstring."""
        return self.add(owner=function, text=text)

    def edit_function(self, *, function: FunctionDef, text: str) -> Expr:
        """Edit a function docstring."""
        return self.edit(owner=function, text=text)

    def remove_function(self, *, function: FunctionDef) -> str | None:
        """Remove a function docstring."""
        return self.remove(owner=function)

    def get_class(self, *, class_node: ClassDef) -> str | None:
        """Return a class docstring."""
        return self.get(owner=class_node)

    def set_class(self, *, class_node: ClassDef, text: str) -> Expr:
        """Set or create a class docstring."""
        return self.set(owner=class_node, text=text)

    def add_class(self, *, class_node: ClassDef, text: str) -> Expr:
        """Add a class docstring."""
        return self.add(owner=class_node, text=text)

    def edit_class(self, *, class_node: ClassDef, text: str) -> Expr:
        """Edit a class docstring."""
        return self.edit(owner=class_node, text=text)

    def remove_class(self, *, class_node: ClassDef) -> str | None:
        """Remove a class docstring."""
        return self.remove(owner=class_node)

    def _body_for(self, *, owner: DocstringOwner) -> list[stmt]:
        """Return the mutable body list for a supported owner."""
        return owner.body

    def _docstring_index(self, *, body: list[stmt]) -> int | None:
        """Return the index of the first docstring statement."""
        if not body:
            return None
        first: stmt = body[0]
        if not isinstance(first, Expr):
            return None
        if not isinstance(first.value, Constant):
            return None
        if not isinstance(first.value.value, str):
            return None
        return 0

    def _docstring_node(self, *, text: str) -> Expr:
        """Create a docstring expression node."""
        return Expr(value=Constant(value=text))


class EasyFunctionEditor:
    """Small facade for editing function signatures and docstrings."""

    def __init__(
        self,
        *,
        type_hints: FunctionTypeHintEditor,
        docstrings: DocstringEditor,
    ) -> None:
        """Initialize the function editing facade."""
        self._type_hints: FunctionTypeHintEditor = type_hints
        self._docstrings: DocstringEditor = docstrings

    def arg(
        self,
        *,
        function: FunctionDef,
        name: str,
        type_hint: TypeExpression | expr | None,
    ) -> FunctionDef:
        """Set one argument annotation and return the function node."""
        self._type_hints.set_argument_annotation(
            function=function,
            name=name,
            type_hint=type_hint,
        )
        return function

    def returns(
        self,
        *,
        function: FunctionDef,
        type_hint: TypeExpression | expr | None,
    ) -> FunctionDef:
        """Set the return annotation and return the function node."""
        self._type_hints.set_return(function=function, type_hint=type_hint)
        return function

    def args(
        self,
        *,
        function: FunctionDef,
        arguments: ast_arguments | tuple[ArgumentSpec, ...],
    ) -> FunctionDef:
        """Set the complete function argument list."""
        self._type_hints.set_arguments(function=function, arguments=arguments)
        return function

    def docstring(self, *, function: FunctionDef, text: str) -> FunctionDef:
        """Set or create the function docstring."""
        self._docstrings.set_function(function=function, text=text)
        return function

    def remove_docstring(self, *, function: FunctionDef) -> FunctionDef:
        """Remove the function docstring if present."""
        self._docstrings.remove_function(function=function)
        return function


class EasyClassEditor:
    """Small facade for editing class docstrings."""

    def __init__(self, *, docstrings: DocstringEditor) -> None:
        """Initialize the class editing facade."""
        self._docstrings: DocstringEditor = docstrings

    def docstring(self, *, class_node: ClassDef, text: str) -> ClassDef:
        """Set or create the class docstring."""
        self._docstrings.set_class(class_node=class_node, text=text)
        return class_node

    def remove_docstring(self, *, class_node: ClassDef) -> ClassDef:
        """Remove the class docstring if present."""
        self._docstrings.remove_class(class_node=class_node)
        return class_node


class SemanticEasyEditor:
    """High-level facade for common semantic editing operations."""

    def __init__(self, *, collector: SemanticCodegenEditingCollector) -> None:
        """Initialize the easy editor."""
        self._collector: SemanticCodegenEditingCollector = collector
        self.functions: EasyFunctionEditor = EasyFunctionEditor(
            type_hints=collector.type_hints,
            docstrings=collector.docstrings,
        )
        self.classes: EasyClassEditor = EasyClassEditor(
            docstrings=collector.docstrings,
        )

    def typevar(
        self,
        *,
        name: str | None = None,
        bound: TypeExpression | None = None,
        constraints: tuple[TypeExpression, ...] = (),
        covariant: bool = False,
        contravariant: bool = False,
    ) -> TypeVarSpec:
        """Create a TypeVar using the collector."""
        return self._collector.typevar(
            name=name,
            bound=bound,
            constraints=constraints,
            covariant=covariant,
            contravariant=contravariant,
        )

    def paramspec(
        self,
        *,
        name: str | None = None,
        bound: TypeExpression | None = None,
        covariant: bool = False,
        contravariant: bool = False,
    ) -> ParamSpecSpec:
        """Create a ParamSpec using the collector."""
        return self._collector.paramspec(
            name=name,
            bound=bound,
            covariant=covariant,
            contravariant=contravariant,
        )

    def replace_attribute_set(
        self,
        *,
        node: AttributeAssignmentNode,
        variable_name: str = "_attr_name",
    ) -> AttributeSetattrRewriteResult:
        """Queue an attribute assignment rewrite."""
        return self._collector.transforms.replace_attribute_set(
            node=node,
            variable_name=variable_name,
        )

    def override(
        self,
        *,
        original: FunctionDef,
        update: MethodOverrideUpdate,
    ) -> FunctionDef:
        """Queue a function override after the original function."""
        return self._collector.transforms.add_override(
            original=original,
            update=update,
        )

    def int_constants(
        self,
        *,
        scope: ComparisonIntConstantScope | None = None,
        prefix: str | None = None,
    ) -> ComparisonIntConstantConfig:
        """Configure integer comparison constant hoisting."""
        selected_scope: ComparisonIntConstantScope = (
            ComparisonIntConstantScope.MODULE if scope is None else scope
        )
        config: ComparisonIntConstantConfig = ComparisonIntConstantConfig(
            scope=selected_scope,
            prefix=prefix,
        )
        self._collector.int_comparisons.configure(config=config)
        return config

    def transform(self, *, body: BodyBlockNode) -> BodyBlockNode:
        """Apply queued transformations to a body block."""
        return self._collector.transformed_body(body=body)

    def unparse(
        self,
        *,
        body: BodyBlockNode,
        parsed: CommentAwareParseResult | None = None,
        extra_blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ] = (),
    ) -> str:
        """Unparse the generated preamble plus transformed body."""
        return self._collector.unparse_with_body(
            body=body,
            parsed=parsed,
            extra_blocks=extra_blocks,
        )


class ComparisonIntConstantNameFactory:
    """Create deterministic names for integer comparison constants."""

    def __init__(self, *, prefix: str) -> None:
        """Initialize the factory."""
        self._prefix: str = prefix

    def name_for(self, *, value: int) -> str:
        """Return the canonical constant name for an integer value."""
        if value < 0:
            return f"{self._prefix}_NEG_{abs(value)}"
        return f"{self._prefix}{value}"


class ComparisonIntConstantNodeBuilder:
    """Build AST declaration nodes for integer comparison constants."""

    def __init__(self, *, imports: UsageAwareImportCollector) -> None:
        """Initialize the builder."""
        self._imports: UsageAwareImportCollector = imports

    def declaration(self, *, spec: ComparisonIntConstantSpec) -> AnnAssign:
        """Build ``_INT3: Final[int] = 3`` as an AST node."""
        final_node: Name = self._imports.require_from_source(
            source=SemanticImportSource.absolute(
                module_parts=("typing",),
                imported_name="Final",
            ),
            use=ImportUseSite.runtime(owner=spec.name),
        )
        annotation: Subscript = AstExpressionBuilder.subscript(
            value=final_node,
            args=(Name(id="int", ctx=Load()),),
        )
        return AnnAssign(
            target=Name(id=spec.name, ctx=Store()),
            annotation=annotation,
            value=Constant(value=spec.value),
            simple=1,
        )


class ComparisonIntConstantScopeState:
    """Track integer constants generated for one insertion scope."""

    def __init__(self, *, config: ComparisonIntConstantConfig) -> None:
        """Initialize the scope state."""
        self._config: ComparisonIntConstantConfig = config
        self._name_factory: ComparisonIntConstantNameFactory = (
            ComparisonIntConstantNameFactory(prefix=config.resolved_prefix)
        )
        self._by_value: dict[int, ComparisonIntConstantSpec] = {}

    @property
    def specs(self) -> tuple[ComparisonIntConstantSpec, ...]:
        """Return generated constant specs sorted by value."""
        return tuple(self._by_value[value] for value in sorted(self._by_value))

    def reference_for(self, *, value: int) -> Name:
        """Return a reference name, creating the declaration spec if needed."""
        spec: ComparisonIntConstantSpec | None = self._by_value.get(value)
        if spec is None:
            spec = ComparisonIntConstantSpec(
                value=value,
                name=self._name_factory.name_for(value=value),
            )
            self._by_value[value] = spec
        return Name(id=spec.name, ctx=Load())


class ComparisonIntLiteralNodeTransformer(NodeTransformer):
    """Replace integer constants inside comparison expressions."""

    def __init__(
        self,
        *,
        scope_state: ComparisonIntConstantScopeState,
    ) -> None:
        """Initialize the transformer."""
        super().__init__()
        self._scope_state: ComparisonIntConstantScopeState = scope_state

    def visit(self, node: AST) -> AST:
        """Dispatch compare nodes to the lowercase handler.

        Args:
            node (AST): Node to transform.

        Returns:
            AST: The transformed node.

        """
        if isinstance(node, Compare):
            return self.visit_compare(node=node)
        return self.generic_visit(node=node)

    def visit_compare(self, node: Compare) -> Compare:
        """Replace integer constants in one comparison node."""
        visited: AST = self.generic_visit(node=node)
        if not isinstance(visited, Compare):
            msg: str = "Comparison transformer expected an ast.Compare node."
            fail(message=msg)
        visited.left = self._replace_expr(expression=visited.left)
        visited.comparators = [
            self._replace_expr(expression=comparator)
            for comparator in visited.comparators
        ]
        return visited

    def _replace_expr(self, *, expression: expr) -> expr:
        """Replace one expression when it is an integer constant."""
        int_value: int | None = self._int_value(expression=expression)
        if int_value is not None:
            return self._scope_state.reference_for(value=int_value)
        return expression

    def _int_value(self, *, expression: expr) -> int | None:
        """Return a non-bool integer constant value when available."""
        if not isinstance(expression, Constant):
            return None
        if not isinstance(expression.value, int):
            return None
        if isinstance(expression.value, bool):
            return None
        return expression.value


class ComparisonIntConstantInserter:
    """Insert generated integer constants at the top of a scope body."""

    def __init__(self, *, builder: ComparisonIntConstantNodeBuilder) -> None:
        """Initialize the inserter."""
        self._builder: ComparisonIntConstantNodeBuilder = builder

    def declarations_for(
        self,
        *,
        scope_state: ComparisonIntConstantScopeState,
    ) -> tuple[stmt, ...]:
        """Return declaration nodes for a scope state."""
        return tuple(
            self._builder.declaration(spec=spec) for spec in scope_state.specs
        )

    def insert_at_body_start(
        self,
        *,
        body: list[stmt],
        declarations: tuple[stmt, ...],
    ) -> None:
        """Insert declarations after a docstring if a body has one."""
        if not declarations:
            return
        insert_index: int = self._insertion_index(body=body)
        body[insert_index:insert_index] = list(declarations)

    def _insertion_index(self, *, body: list[stmt]) -> int:
        """Return insertion index after an optional docstring."""
        if body and self._is_docstring(node=body[0]):
            return 1
        return 0

    def _is_docstring(self, *, node: stmt) -> bool:
        """Return whether a statement is a docstring statement."""
        return (
            isinstance(node, Expr)
            and isinstance(node.value, Constant)
            and isinstance(node.value.value, str)
        )


class ComparisonIntConstantTransformer:
    """Hoist integer comparison constants according to configuration."""

    def __init__(
        self,
        *,
        imports: UsageAwareImportCollector,
        config: ComparisonIntConstantConfig | None = None,
    ) -> None:
        """Initialize the transformer."""
        self._imports: UsageAwareImportCollector = imports
        self._config: ComparisonIntConstantConfig = (
            config or ComparisonIntConstantConfig()
        )
        self._builder: ComparisonIntConstantNodeBuilder = (
            ComparisonIntConstantNodeBuilder(imports=imports)
        )
        self._inserter: ComparisonIntConstantInserter = (
            ComparisonIntConstantInserter(
                builder=self._builder,
            )
        )
        self._module_state: ComparisonIntConstantScopeState = (
            ComparisonIntConstantScopeState(config=self._config)
        )

    @property
    def module_declarations(self) -> tuple[stmt, ...]:
        """Return module-level constant declaration nodes."""
        return self._inserter.declarations_for(scope_state=self._module_state)

    def configure(self, *, config: ComparisonIntConstantConfig) -> None:
        """Replace the transformation configuration."""
        self._config = config
        self._module_state = ComparisonIntConstantScopeState(config=config)

    def transform_body(self, *, body: BodyBlockNode) -> BodyBlockNode:
        """Return a body with comparison integers replaced."""
        statements: tuple[stmt, ...]
        if self._config.scope is ComparisonIntConstantScope.MODULE:
            statements = self._transform_module_statements(
                statements=body.body,
            )
        elif self._config.scope is ComparisonIntConstantScope.FUNCTION:
            statements = self._transform_function_scoped_statements(
                statements=body.body,
            )
        else:
            statements = self._transform_class_scoped_statements(
                statements=body.body,
            )
        return BodyBlockNode(body=statements)

    def _transform_module_statements(
        self,
        *,
        statements: tuple[stmt, ...],
    ) -> tuple[stmt, ...]:
        """Transform statements using one module-level constant scope."""
        transformer: ComparisonIntLiteralNodeTransformer = (
            ComparisonIntLiteralNodeTransformer(scope_state=self._module_state)
        )
        return tuple(
            cast(typ="stmt", val=transformer.visit(node=statement))
            for statement in statements
        )

    def _transform_function_scoped_statements(
        self,
        *,
        statements: tuple[stmt, ...],
    ) -> tuple[stmt, ...]:
        """Transform statements with generated constants in functions."""
        return tuple(
            self._transform_function_scope_statement(statement=statement)
            for statement in statements
        )

    def _transform_function_scope_statement(self, *, statement: stmt) -> stmt:
        """Transform one statement for function-scoped constants."""
        if isinstance(statement, FunctionDef):
            self._transform_function(function=statement)
            return statement
        if isinstance(statement, ClassDef):
            statement.body = list(
                self._transform_function_scoped_statements(
                    statements=tuple(statement.body),
                ),
            )
            return statement
        if isinstance(statement, If):
            statement.body = list(
                self._transform_function_scoped_statements(
                    statements=tuple(statement.body),
                ),
            )
            statement.orelse = list(
                self._transform_function_scoped_statements(
                    statements=tuple(statement.orelse),
                ),
            )
        return statement

    def _transform_class_scoped_statements(
        self,
        *,
        statements: tuple[stmt, ...],
    ) -> tuple[stmt, ...]:
        """Transform statements with generated constants in classes."""
        return tuple(
            self._transform_class_scope_statement(statement=statement)
            for statement in statements
        )

    def _transform_class_scope_statement(self, *, statement: stmt) -> stmt:
        """Transform one statement for class-scoped constants."""
        if isinstance(statement, ClassDef):
            self._transform_class(class_node=statement)
            return statement
        if isinstance(statement, FunctionDef):
            return statement
        if isinstance(statement, If):
            statement.body = list(
                self._transform_class_scoped_statements(
                    statements=tuple(statement.body),
                ),
            )
            statement.orelse = list(
                self._transform_class_scoped_statements(
                    statements=tuple(statement.orelse),
                ),
            )
        return statement

    def _transform_function(self, *, function: FunctionDef) -> None:
        """Transform comparison integers inside a function body."""
        scope_state: ComparisonIntConstantScopeState = (
            ComparisonIntConstantScopeState(
                config=self._config,
            )
        )
        transformer: ComparisonIntLiteralNodeTransformer = (
            ComparisonIntLiteralNodeTransformer(scope_state=scope_state)
        )
        function.body = [
            cast(typ="stmt", val=transformer.visit(node=statement))
            for statement in function.body
        ]
        declarations: tuple[stmt, ...] = self._inserter.declarations_for(
            scope_state=scope_state,
        )
        self._inserter.insert_at_body_start(
            body=function.body,
            declarations=declarations,
        )

    def _transform_class(self, *, class_node: ClassDef) -> None:
        """Transform comparison integers inside a class body."""
        scope_state: ComparisonIntConstantScopeState = (
            ComparisonIntConstantScopeState(
                config=self._config,
            )
        )
        transformer: ComparisonIntLiteralNodeTransformer = (
            ComparisonIntLiteralNodeTransformer(scope_state=scope_state)
        )
        class_node.body = [
            self._transform_class_child(
                statement=statement,
                transformer=transformer,
            )
            for statement in class_node.body
        ]
        declarations: tuple[stmt, ...] = self._inserter.declarations_for(
            scope_state=scope_state,
        )
        self._inserter.insert_at_body_start(
            body=class_node.body,
            declarations=declarations,
        )

    def _transform_class_child(
        self,
        *,
        statement: stmt,
        transformer: ComparisonIntLiteralNodeTransformer,
    ) -> stmt:
        """Transform a class-body child but not method internals."""
        if isinstance(statement, FunctionDef):
            return statement
        transformed_statement: AST = transformer.visit(node=statement)
        if not isinstance(transformed_statement, stmt):
            fail(
                message="Expected statement after class-child transformation.",
            )
        return transformed_statement


class SemanticCodegenEditingCollector(SemanticCodegenCollector):
    """Collector extended with edit plans and direct type-hint mutation."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the editing collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            existing_type_aliases=existing_type_aliases,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self.type_hints: FunctionTypeHintEditor = FunctionTypeHintEditor(
            resolver=self._resolver,
        )
        self.docstrings: DocstringEditor = DocstringEditor()
        self.transforms: BodyTransformationPlan = BodyTransformationPlan(
            collector=self,
        )
        self.int_comparisons: ComparisonIntConstantTransformer = (
            ComparisonIntConstantTransformer(imports=self._imports)
        )
        self.edit: SemanticEasyEditor = SemanticEasyEditor(collector=self)

    def build_declaration_block(self) -> SemanticDeclarationBlock:
        """Build imports, declarations, and module-level int constants."""
        constants: tuple[stmt, ...] = self.int_comparisons.module_declarations
        block: SemanticDeclarationBlock = super().build_declaration_block()
        return SemanticDeclarationBlock(
            imports=block.imports,
            typevars=block.typevars,
            paramspecs=block.paramspecs,
            type_aliases=block.type_aliases,
            protocols=block.protocols,
            constants=constants,
        )

    def transformed_body(self, *, body: BodyBlockNode) -> BodyBlockNode:
        """Return a body block with queued transformations applied."""
        transformed_body: BodyBlockNode = self.transforms.transformed_body(
            body=body,
        )
        return self.int_comparisons.transform_body(body=transformed_body)

    def organized_preamble(
        self,
        *,
        extra_blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ] = (),
    ) -> GeneratedPreambleBlockNode:
        """Return generated and supplied blocks as one organized preamble."""
        own_block: SemanticDeclarationBlock = self.build_declaration_block()
        return DeclarationBlockOrganizer().organize(
            blocks=(own_block, *extra_blocks),
        )

    def unparse_with_body(
        self,
        *,
        body: BodyBlockNode,
        parsed: CommentAwareParseResult | None = None,
        extra_blocks: tuple[
            GeneratedTopBlock
            | SemanticDeclarationBlock
            | GeneratedPreambleBlockNode,
            ...,
        ] = (),
    ) -> str:
        """Unparse generated declarations before a transformed body."""
        preamble: GeneratedPreambleBlockNode = self.organized_preamble(
            extra_blocks=extra_blocks,
        )
        unparser: CommentPreservingTokenAwareUnparser = (
            CommentPreservingTokenAwareUnparser(parsed=parsed)
        )
        return unparser.unparse_module_with_blocks(
            blocks=(preamble,),
            body=body,
        )


class TypeExpressionAstParser:
    """Convert existing annotation AST nodes into semantic type expressions."""

    def from_node(
        self,
        *,
        node: expr | None,
    ) -> AstBackedTypeExpression | None:
        """Return an AST-backed type expression for a node."""
        if node is None:
            return None
        return AstBackedTypeExpression(node=node)

    def from_required_node(self, *, node: expr) -> AstBackedTypeExpression:
        """Return an AST-backed type expression for a required node."""
        return AstBackedTypeExpression(node=node)


class ExistingDocstringParser:
    """Parse existing docstrings using the same editor semantics."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._editor: DocstringEditor = DocstringEditor()

    def module_docstring(self, *, module: Module) -> ParsedDocstring | None:
        """Parse the module docstring if one exists."""
        return self._docstring(
            owner=module,
            owner_name="<module>",
            owner_kind="module",
        )

    def class_docstring(
        self,
        *,
        class_node: ClassDef,
    ) -> ParsedDocstring | None:
        """Parse a class docstring if one exists."""
        return self._docstring(
            owner=class_node,
            owner_name=class_node.name,
            owner_kind="class",
        )

    def function_docstring(
        self,
        *,
        function: FunctionDef,
    ) -> ParsedDocstring | None:
        """Parse a function docstring if one exists."""
        return self._docstring(
            owner=function,
            owner_name=function.name,
            owner_kind="function",
        )

    def _docstring(
        self,
        *,
        owner: DocstringOwner,
        owner_name: str,
        owner_kind: Literal["module", "class", "function"],
    ) -> ParsedDocstring | None:
        """Return parsed docstring metadata for an owner."""
        text: str | None = self._editor.get(owner=owner)
        if text is None:
            return None
        body: list[stmt] = owner.body
        if not body or not isinstance(body[0], Expr):
            return None
        return ParsedDocstring(
            owner_name=owner_name,
            owner_kind=owner_kind,
            text=text,
            node=body[0],
        )


class ExistingImportModelParser:
    """Parse existing import nodes into semantic import models."""

    def parse(
        self,
        *,
        nodes: tuple[Import | ImportFrom, ...],
    ) -> tuple[ParsedImportModel, ...]:
        """Parse import nodes."""
        return tuple(self._parse_one(node=node) for node in nodes)

    def _parse_one(self, *, node: Import | ImportFrom) -> ParsedImportModel:
        """Parse a single import node."""
        if isinstance(node, ImportFrom):
            return ParsedImportModel(
                node=node,
                module=node.module,
                level=node.level,
                names=tuple(item.asname or item.name for item in node.names),
            )
        return ParsedImportModel(
            node=node,
            module=None,
            level=0,
            names=tuple(item.asname or item.name for item in node.names),
        )


class ExistingFunctionModelParser:
    """Parse function definitions into semantic signature models."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._types: TypeExpressionAstParser = TypeExpressionAstParser()
        self._docstrings: ExistingDocstringParser = ExistingDocstringParser()

    def parse(self, *, function: FunctionDef) -> ParsedFunctionSignature:
        """Parse one function definition."""
        positional: tuple[arg, ...] = (
            *function.args.posonlyargs,
            *function.args.args,
        )
        return ParsedFunctionSignature(
            node=function,
            name=function.name,
            arguments=positional,
            vararg=function.args.vararg,
            keyword_only_arguments=tuple(function.args.kwonlyargs),
            kwarg=function.args.kwarg,
            return_annotation=self._types.from_node(node=function.returns),
            docstring=self._docstrings.function_docstring(function=function),
        )


class ExistingClassModelParser:
    """Parse class definitions into semantic class models."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._types: TypeExpressionAstParser = TypeExpressionAstParser()
        self._functions: ExistingFunctionModelParser = (
            ExistingFunctionModelParser()
        )
        self._docstrings: ExistingDocstringParser = ExistingDocstringParser()

    def parse(self, *, class_node: ClassDef) -> ParsedClassModel:
        """Parse one class definition."""
        methods: tuple[ParsedFunctionSignature, ...] = tuple(
            self._functions.parse(function=body_node)
            for body_node in class_node.body
            if isinstance(body_node, FunctionDef)
        )
        return ParsedClassModel(
            node=class_node,
            name=class_node.name,
            bases=tuple(
                self._types.from_required_node(node=base)
                for base in class_node.bases
            ),
            docstring=self._docstrings.class_docstring(class_node=class_node),
            methods=methods,
            is_protocol=self._is_protocol_class(class_node=class_node),
        )

    def _is_protocol_class(self, *, class_node: ClassDef) -> bool:
        """Return whether a class appears to inherit from Protocol."""
        return any(
            self._base_mentions_protocol(base=base)
            for base in class_node.bases
        )

    def _base_mentions_protocol(self, *, base: expr) -> bool:
        """Return whether a base expression mentions Protocol."""
        if isinstance(base, Name):
            return base.id == "Protocol"
        if isinstance(base, Attribute):
            return base.attr == "Protocol"
        if isinstance(base, Subscript):
            return self._base_mentions_protocol(base=base.value)
        return False


class ExistingTypeParameterModelParser:
    """Parse existing TypeVar, ParamSpec, and TypeVarTuple declarations."""

    def parse_module(
        self,
        *,
        module: Module,
    ) -> tuple[ParsedTypeParameterModel, ...]:
        """Parse all top-level type-parameter helper declarations."""
        models: list[ParsedTypeParameterModel] = []
        for node in module.body:
            model: ParsedTypeParameterModel | None = self.parse_statement(
                node=node,
            )
            if model is not None:
                models.append(model)
        return tuple(models)

    def parse_statement(
        self,
        *,
        node: stmt,
    ) -> ParsedTypeParameterModel | None:
        """Parse one statement when it is a type-parameter declaration."""
        if isinstance(node, Assign):
            return self._parse_assign(node=node)
        if isinstance(node, AnnAssign):
            return self._parse_ann_assign(node=node)
        return None

    def _parse_assign(
        self,
        *,
        node: Assign,
    ) -> ParsedTypeParameterModel | None:
        """Parse assignment-style type-parameter declarations."""
        if len(node.targets) != 1 or not isinstance(node.targets[0], Name):
            return None
        return self._model_from_value(
            target=node.targets[0],
            value=node.value,
            node=node,
        )

    def _parse_ann_assign(
        self,
        *,
        node: AnnAssign,
    ) -> ParsedTypeParameterModel | None:
        """Parse annotated assignment-style type-parameter declarations."""
        if not isinstance(node.target, Name):
            return None
        return self._model_from_value(
            target=node.target,
            value=node.value,
            node=node,
        )

    def _model_from_value(
        self,
        *,
        target: Name,
        value: expr | None,
        node: Assign | AnnAssign,
    ) -> ParsedTypeParameterModel | None:
        """Return a model from a declaration value."""
        if not isinstance(value, Call):
            return None
        called_name: str | None = self._called_name(call=value)
        if called_name in ExistingTypeParameterNames.typevar_names:
            kind: str = "typevar"
        elif called_name in ExistingTypeParameterNames.paramspec_names:
            kind = "paramspec"
        elif called_name in ExistingTypeParameterNames.typevartuple_names:
            kind = "typevartuple"
        else:
            return None
        return ParsedTypeParameterModel(
            node=node,
            name=target.id,
            kind=kind,
            value_node=value,
        )

    def _called_name(self, *, call: Call) -> str | None:
        """Return the unqualified called function name."""
        if isinstance(call.func, Name):
            return call.func.id
        if isinstance(call.func, Attribute):
            return call.func.attr
        return None


class ExistingTypeAliasModelParser:
    """Parse existing type aliases into semantic models."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._types: TypeExpressionAstParser = TypeExpressionAstParser()

    def parse_module(
        self,
        *,
        module: Module,
    ) -> tuple[ParsedTypeAliasModel, ...]:
        """Parse all top-level type aliases."""
        aliases: list[ParsedTypeAliasModel] = []
        for node in module.body:
            alias_model: ParsedTypeAliasModel | None = self.parse_statement(
                node=node,
            )
            if alias_model is not None:
                aliases.append(alias_model)
        return tuple(aliases)

    def parse_statement(self, *, node: stmt) -> ParsedTypeAliasModel | None:
        """Parse one statement as a type alias when possible."""
        if isinstance(node, AstTypeAlias):
            return self._parse_type_alias(node=node)
        if isinstance(node, AnnAssign):
            return self._parse_type_alias_assignment(node=node)
        return None

    def _parse_type_alias(
        self,
        *,
        node: AstTypeAlias,
    ) -> ParsedTypeAliasModel | None:
        """Parse a Python 3.13 type alias node."""
        return ParsedTypeAliasModel(
            node=node,
            name=node.name.id,
            value=self._types.from_required_node(node=node.value),
        )

    def _parse_type_alias_assignment(
        self,
        *,
        node: AnnAssign,
    ) -> ParsedTypeAliasModel | None:
        """Parse ``Alias: TypeAlias = ...`` assignments."""
        if node.value is None or not isinstance(node.target, Name):
            return None
        if not self._is_type_alias_annotation(annotation=node.annotation):
            return None
        return ParsedTypeAliasModel(
            node=node,
            name=node.target.id,
            value=self._types.from_required_node(node=node.value),
        )

    def _is_type_alias_annotation(self, *, annotation: expr) -> bool:
        """Return whether an annotation is ``TypeAlias``."""
        if isinstance(annotation, Name):
            return annotation.id == "TypeAlias"
        if isinstance(annotation, Attribute):
            return annotation.attr == "TypeAlias"
        return False


class SemanticModelParser:
    """Parse source code into the semantic editing model."""

    def __init__(self) -> None:
        """Initialize the semantic model parser."""
        self._docstrings: ExistingDocstringParser = ExistingDocstringParser()
        self._imports: ExistingImportModelParser = ExistingImportModelParser()
        self._classes: ExistingClassModelParser = ExistingClassModelParser()
        self._functions: ExistingFunctionModelParser = (
            ExistingFunctionModelParser()
        )
        self._type_parameters: ExistingTypeParameterModelParser = (
            ExistingTypeParameterModelParser()
        )
        self._type_aliases: ExistingTypeAliasModelParser = (
            ExistingTypeAliasModelParser()
        )

    def parse_source(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> ParsedSemanticModel:
        """Parse source into a full semantic model."""
        parsed: CommentAwareParseResult = (
            CommentAwareTokenizedAstParser().parse_module(
                source=source,
                filename=filename,
            )
        )
        return self.parse_result(parsed=parsed)

    def parse_result(
        self,
        *,
        parsed: CommentAwareParseResult,
    ) -> ParsedSemanticModel:
        """Parse a comment-aware result.

        Return the semantic model.
        """
        context: ExistingNodeContext = ExistingNodeContext.from_nodes(
            nodes=self._existing_top_nodes(module=parsed.module),
        )
        return ParsedSemanticModel(
            parsed=parsed,
            context=context,
            imports=self._imports.parse(nodes=context.import_nodes),
            module_docstring=self._docstrings.module_docstring(
                module=parsed.module,
            ),
            classes=self._parse_classes(context=context),
            functions=self._parse_functions(module=parsed.module),
            type_parameters=self._type_parameters.parse_module(
                module=parsed.module,
            ),
            type_aliases=self._type_aliases.parse_module(module=parsed.module),
        )

    def _existing_top_nodes(
        self,
        *,
        module: Module,
    ) -> tuple[ExistingTopNode, ...]:
        """Return import and class nodes from a module body."""
        return tuple(
            node
            for node in module.body
            if isinstance(node, Import | ImportFrom | ClassDef)
        )

    def _parse_classes(
        self,
        *,
        context: ExistingNodeContext,
    ) -> tuple[ParsedClassModel, ...]:
        """Parse existing class nodes."""
        return tuple(
            self._classes.parse(class_node=item)
            for item in context.class_nodes
        )

    def _parse_functions(
        self,
        *,
        module: Module,
    ) -> tuple[ParsedFunctionSignature, ...]:
        """Parse top-level function nodes."""
        return tuple(
            self._functions.parse(function=item)
            for item in module.body
            if isinstance(item, FunctionDef)
        )


class AutoTypeParameterFacade:
    """Simpler automatic TypeVar and ParamSpec creation helpers."""

    def __init__(self, *, collector: ProtocolTypeBlockCollector) -> None:
        """Initialize the facade."""
        self._collector: ProtocolTypeBlockCollector = collector

    def typevar(
        self,
        *,
        bound: TypeExpression | None = None,
        constraints: tuple[TypeExpression, ...] = (),
        covariant: bool = False,
        contravariant: bool = False,
    ) -> TypeVarSpec:
        """Create an automatically named TypeVar."""
        return self._collector.typevar(
            bound=bound,
            constraints=constraints,
            covariant=covariant,
            contravariant=contravariant,
        )

    def paramspec(
        self,
        *,
        bound: TypeExpression | None = None,
        covariant: bool = False,
        contravariant: bool = False,
    ) -> ParamSpecSpec:
        """Create an automatically named ParamSpec."""
        return self._collector.paramspec(
            bound=bound,
            covariant=covariant,
            contravariant=contravariant,
        )


class SemanticModelParseUnparseToolkit(CommentAwareParseUnparseToolkit):
    """Parse/unparse toolkit that also returns semantic models."""

    def parse_model(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> ParsedSemanticModel:
        """Parse source into the semantic model."""
        parsed: CommentAwareParseResult = self.parse_comments(
            source=source,
            filename=filename,
        )
        return SemanticModelParser().parse_result(parsed=parsed)


class SemanticModelEditingCollector(SemanticCodegenEditingCollector):
    """Editing collector with parsed-model and automatic parameter helpers."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            existing_type_aliases=existing_type_aliases,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self.auto: AutoTypeParameterFacade = AutoTypeParameterFacade(
            collector=self,
        )

    @classmethod
    def from_model(
        cls,
        *,
        model: ParsedSemanticModel,
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> SemanticModelEditingCollector:
        """Create an editing collector initialized from a parsed model."""
        type_alias_nodes: tuple[AstTypeAlias, ...] = tuple(
            item.node
            for item in model.type_aliases
            if isinstance(item.node, AstTypeAlias)
        )
        return cls(
            existing_nodes=(
                *model.context.import_nodes,
                *model.context.class_nodes,
            ),
            existing_type_aliases=type_alias_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )


class SemanticGraphIdFactory:
    """Generate stable graph identifiers."""

    def __init__(self) -> None:
        """Initialize counters."""
        self._node_index: int = 0
        self._scope_index: int = 0
        self._symbol_index: int = 0

    def node_id(self) -> SemanticNodeId:
        """Return the next graph-node identifier."""
        self._node_index += 1
        return f"node:{self._node_index}"

    def scope_id(self) -> SemanticScopeId:
        """Return the next scope identifier."""
        self._scope_index += 1
        return f"scope:{self._scope_index}"

    def symbol_id(self) -> SemanticSymbolId:
        """Return the next symbol identifier."""
        self._symbol_index += 1
        return f"symbol:{self._symbol_index}"


class SemanticAstGraph:
    """Introspective semantic graph built from Python AST nodes."""

    def __init__(self) -> None:
        """Initialize graph storage."""
        self.nodes: dict[SemanticNodeId, SemanticGraphNode] = {}
        self.edges: list[SemanticGraphEdge] = []
        self.scopes: dict[SemanticScopeId, SemanticScope] = {}
        self.symbols: dict[SemanticSymbolId, SemanticSymbol] = {}
        self._node_ids_by_ast_id: dict[int, SemanticNodeId] = {}
        self._children_by_node: dict[SemanticNodeId, list[SemanticNodeId]] = {}
        self._parents_by_node: dict[SemanticNodeId, SemanticNodeId] = {}
        self.root_node_id: SemanticNodeId | None | str = None
        self.root_scope_id: SemanticScopeId | None | str = None

    def add_scope(
        self,
        *,
        scope: SemanticScope,
    ) -> None:
        """Add a lexical scope."""
        self.scopes[scope.id] = scope
        if self.root_scope_id is None:
            self.root_scope_id = scope.id

    def add_node(self, *, node: SemanticGraphNode) -> None:
        """Add a semantic graph node."""
        self.nodes[node.id] = node
        self._node_ids_by_ast_id[id(node.ast_node)] = node.id
        self._children_by_node.setdefault(node.id, [])
        if node.parent_id is not None:
            self._parents_by_node[node.id] = node.parent_id
            self._children_by_node.setdefault(node.parent_id, []).append(
                node.id,
            )
        if self.root_node_id is None:
            self.root_node_id = node.id

    def add_edge(
        self,
        *,
        source_id: SemanticNodeId,
        target_id: SemanticNodeId,
        kind: SemanticEdgeKind,
        label: str | None = None,
    ) -> None:
        """Add a semantic edge."""
        self.edges.append(
            SemanticGraphEdge(
                source_id=source_id,
                target_id=target_id,
                kind=kind,
                label=label,
            ),
        )

    def add_symbol(self, *, symbol: SemanticSymbol) -> None:
        """Add a symbol to the graph."""
        self.symbols[symbol.id] = symbol
        scope: SemanticScope | None = self.scopes.get(symbol.scope_id)
        if scope is not None:
            scope.define(name=symbol.name, symbol_id=symbol.id)

    def node_id_for_ast(self, *, node: AST) -> SemanticNodeId | None:
        """Return the graph node id for an AST node."""
        return self._node_ids_by_ast_id.get(id(node))

    def view_for_ast(self, *, node: AST) -> SemanticAstNodeView | None:
        """Return a navigable view for an AST node."""
        node_id: SemanticNodeId | None = self.node_id_for_ast(node=node)
        if node_id is None:
            return None
        return SemanticAstNodeView(graph=self, node_id=node_id)

    def view(self, *, node_id: SemanticNodeId) -> SemanticAstNodeView:
        """Return a navigable node view."""
        return SemanticAstNodeView(graph=self, node_id=node_id)

    def root(self) -> SemanticAstNodeView | None:
        """Return the root node view."""
        if self.root_node_id is None:
            return None
        return self.view(node_id=self.root_node_id)

    def children_of(
        self,
        *,
        node_id: SemanticNodeId,
    ) -> tuple[SemanticNodeId, ...]:
        """Return children of a graph node."""
        return tuple(self._children_by_node.get(node_id, []))

    def parent_of(self, *, node_id: SemanticNodeId) -> SemanticNodeId | None:
        """Return parent of a graph node."""
        return self._parents_by_node.get(node_id)

    def outgoing(
        self,
        *,
        node_id: SemanticNodeId,
        kind: SemanticEdgeKind | None = None,
    ) -> tuple[SemanticGraphEdge, ...]:
        """Return outgoing semantic edges."""
        return tuple(
            edge
            for edge in self.edges
            if edge.source_id == node_id
            and (kind is None or edge.kind == kind)
        )

    def incoming(
        self,
        *,
        node_id: SemanticNodeId,
        kind: SemanticEdgeKind | None = None,
    ) -> tuple[SemanticGraphEdge, ...]:
        """Return incoming semantic edges."""
        return tuple(
            edge
            for edge in self.edges
            if edge.target_id == node_id
            and (kind is None or edge.kind == kind)
        )

    def lookup_symbol(
        self,
        *,
        name: str,
        scope_id: SemanticScopeId,
    ) -> SemanticSymbol | None:
        """Resolve a symbol by walking lexical parent scopes."""
        current_id: SemanticScopeId | None | str = scope_id
        while current_id is not None:
            scope: SemanticScope | None = self.scopes.get(current_id)
            if scope is None:
                return None
            symbol_id: SemanticSymbolId | None = scope.symbols.get(name)
            if symbol_id is not None:
                return self.symbols.get(symbol_id)
            current_id = scope.parent_id
        return None

    def symbols_named(self, *, name: str) -> tuple[SemanticSymbol, ...]:
        """Return all symbols with a name."""
        return tuple(
            symbol for symbol in self.symbols.values() if symbol.name == name
        )

    def functions(self) -> tuple[SemanticAstNodeView, ...]:
        """Return function and method node views."""
        return tuple(
            self.view(node_id=node.id)
            for node in self.nodes.values()
            if node.kind == SemanticNodeKind.FUNCTION
        )

    def classes(self) -> tuple[SemanticAstNodeView, ...]:
        """Return class node views."""
        return tuple(
            self.view(node_id=node.id)
            for node in self.nodes.values()
            if node.kind == SemanticNodeKind.CLASS
        )

    def init_methods(
        self,
        *,
        class_name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return ``__init__`` methods for a class name."""
        return self._class_methods_named(
            class_name=class_name,
            method_name="__init__",
        )

    def new_methods(
        self,
        *,
        class_name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return ``__new__`` methods for a class name."""
        return self._class_methods_named(
            class_name=class_name,
            method_name="__new__",
        )

    def usages_for_symbol(
        self,
        *,
        symbol: SemanticSymbol,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return usage node views for a symbol."""
        return tuple(
            self.view(node_id=node_id) for node_id in symbol.usage_node_ids
        )

    def value_usage(self, *, name: str) -> tuple[SemanticValueUsage, ...]:
        """Return value usage summaries for all symbols named ``name``."""
        result: list[SemanticValueUsage] = []
        for symbol in self.symbols_named(name=name):
            definitions: tuple[SemanticAstNodeView, ...]
            if symbol.definition_node_id is None:
                definitions = ()
            else:
                definitions = (self.view(node_id=symbol.definition_node_id),)
            result.append(
                SemanticValueUsage(
                    symbol=symbol,
                    definitions=definitions,
                    usages=self.usages_for_symbol(symbol=symbol),
                    evidence=tuple(symbol.evidence),
                ),
            )
        return tuple(result)

    def _class_methods_named(
        self,
        *,
        class_name: str,
        method_name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return methods by class and method name."""
        result: list[SemanticAstNodeView] = []
        for class_view in self.classes():
            class_node: SemanticGraphNode = class_view.graph_node
            if class_node.name != class_name:
                continue
            for child in class_view.children:
                child_node: SemanticGraphNode = child.graph_node
                if (
                    child_node.kind == SemanticNodeKind.FUNCTION
                    and child_node.name == method_name
                ):
                    result.append(child)
        return tuple(result)


class AstNodeClassifier:
    """Classify AST nodes into semantic node kinds."""

    def kind_for(self, *, node: AST) -> SemanticNodeKind:
        """Return the semantic kind for one AST node."""
        result: SemanticNodeKind = SemanticNodeKind.UNKNOWN
        for node_types, kind in AstNodeKindTables.kind_by_type:
            if isinstance(node, node_types):
                result = kind
                break
        return result

    def name_for(self, *, node: AST) -> str | None:
        """Return a semantic name for a node when available."""
        result: str | None = None
        if isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef):
            result = node.name
        elif isinstance(node, arg):
            result = node.arg
        elif isinstance(node, Name):
            result = node.id
        elif isinstance(node, Attribute):
            result = node.attr
        return result


class SemanticLiteralTypeInferencer:
    """Infer type expressions from literals and simple expressions."""

    def __init__(self, *, graph: SemanticAstGraph) -> None:
        """Initialize the inferencer."""
        self._graph: SemanticAstGraph = graph

    def infer(self, *, node: AST) -> TypeExpression | None:
        """Infer a best-effort semantic type expression for an AST node."""
        result: TypeExpression | None = None
        if isinstance(node, Constant):
            result = self._constant(node=node)
        elif isinstance(node, AstList):
            result = self._list(node=node)
        elif isinstance(node, AstTuple):
            result = self._tuple(node=node)
        elif isinstance(node, AstSet):
            result = self._set(node=node)
        elif isinstance(node, AstDict):
            result = self._dict(node=node)
        elif isinstance(node, Name):
            result = self._name(node=node)
        elif isinstance(node, Call):
            result = self._call(node=node)
        elif isinstance(node, BinOp):
            result = self._binop(node=node)
        return result

    def _constant(self, *, node: Constant) -> TypeExpression:
        """Infer from a constant node."""
        value: object = node.value
        result: TypeExpression | BuiltinTypeRef | EllipsisTypeRef = (
            Types.object
        )
        if value is None:
            result = Types.none
        elif value is Ellipsis:
            result = Types.ellipsis
        elif isinstance(value, bool):
            result = Types.bool
        elif isinstance(value, int):
            result = Types.int
        elif isinstance(value, float):
            result = Types.float
        elif isinstance(value, complex):
            result = Types.complex
        elif isinstance(value, str):
            result = Types.str
        elif isinstance(value, bytes):
            result = Types.bytes
        return result

    def _list(self, *, node: AstList) -> TypeExpression:
        """Infer from a list literal."""
        item_type: TypeExpression = self._merged_items(items=tuple(node.elts))
        return Types.builtins.list_of(item=item_type)

    def _tuple(self, *, node: AstTuple) -> TypeExpression:
        """Infer from a tuple literal."""
        if not node.elts:
            return Types.builtins.tuple_empty()
        return Types.builtins.tuple_of(
            items=tuple(
                self.infer(node=item) or Types.object for item in node.elts
            ),
        )

    def _set(self, *, node: AstSet) -> TypeExpression:
        """Infer from a set literal."""
        item_type: TypeExpression = self._merged_items(items=tuple(node.elts))
        return Types.builtins.set_of(item=item_type)

    def _dict(self, *, node: AstDict) -> TypeExpression:
        """Infer from a dict literal."""
        key_nodes: tuple[expr, ...] = tuple(
            key for key in node.keys if key is not None
        )
        key_type: TypeExpression = self._merged_items(items=key_nodes)
        value_type: TypeExpression = self._merged_items(
            items=tuple(node.values),
        )
        return Types.builtins.dict_of(keys=key_type, values=value_type)

    def _name(self, *, node: Name) -> TypeExpression | None:
        """Infer from previously collected symbol evidence."""
        graph_node_id: SemanticNodeId | None = self._graph.node_id_for_ast(
            node=node,
        )
        if graph_node_id is None:
            return None
        graph_node: SemanticGraphNode = self._graph.nodes[graph_node_id]
        symbol: SemanticSymbol | None = self._graph.lookup_symbol(
            name=node.id,
            scope_id=graph_node.scope_id,
        )
        if symbol is None or not symbol.evidence:
            return None
        return SemanticEvidenceMerger().merge(evidence=tuple(symbol.evidence))

    def _call(self, *, node: Call) -> TypeExpression | None:
        """Infer from simple builtin constructor calls."""
        if not isinstance(node.func, Name):
            return None
        mapping: dict[str, TypeExpression] = {
            "bool": Types.bool,
            "dict": Types.builtins.dict.empty(),
            "float": Types.float,
            "int": Types.int,
            "list": Types.builtins.list.empty(),
            "set": Types.builtins.set.empty(),
            "str": Types.str,
        }
        return mapping.get(node.func.id)

    def _binop(self, *, node: BinOp) -> TypeExpression | None:
        """Infer from binary operations by merging operand evidence."""
        left_type: TypeExpression | None = self.infer(node=node.left)
        right_type: TypeExpression | None = self.infer(node=node.right)
        if left_type is None:
            return right_type
        if right_type is None:
            return left_type
        return Types.union(options=(left_type, right_type))

    def _merged_items(self, *, items: tuple[expr, ...]) -> TypeExpression:
        """Infer and merge item types."""
        inferred: tuple[TypeExpression, ...] = tuple(
            item_type
            for item in items
            if (item_type := self.infer(node=item)) is not None
        )
        if not inferred:
            return Types.object
        return Types.union(options=inferred)


class SemanticEvidenceMerger:
    """Merge type evidences into a single best type expression."""

    def merge(
        self,
        *,
        evidence: tuple[TypeInferenceEvidence, ...],
    ) -> TypeExpression:
        """Merge evidence using declaration, union, and narrowing algebra."""
        ordered: tuple[TypeInferenceEvidence, ...] = tuple(
            sorted(evidence, key=lambda item: item.confidence, reverse=True),
        )
        return TypeEvidenceSolver().solve(evidence=ordered)


class SemanticGraphBuilder:
    """Build a semantic AST graph with symbols and type evidence."""

    def __init__(self) -> None:
        """Initialize the graph builder."""
        self._ids: SemanticGraphIdFactory = SemanticGraphIdFactory()
        self._classifier: AstNodeClassifier = AstNodeClassifier()
        self._graph: SemanticAstGraph = SemanticAstGraph()
        self._inferencer: SemanticLiteralTypeInferencer = (
            SemanticLiteralTypeInferencer(
                graph=self._graph,
            )
        )

    def build(self, *, module: Module) -> SemanticAstGraph:
        """Build a graph from an AST module."""
        scope_id: SemanticScopeId = self._ids.scope_id()
        node_id: SemanticNodeId = self._ids.node_id()
        scope: SemanticScope = SemanticScope(
            id=scope_id,
            kind=SemanticScopeKind.MODULE,
            name="<module>",
            node_id=node_id,
            parent_id=None,
        )
        self._graph.add_scope(scope=scope)
        self._visit(
            node=module,
            parent_id=None,
            node_id=node_id,
            scope_id=scope_id,
            role=None,
        )
        return self._graph

    def _visit(
        self,
        *,
        node: AST,
        parent_id: SemanticNodeId | None,
        scope_id: SemanticScopeId,
        role: SemanticUsageKind | None,
        node_id: SemanticNodeId | None = None,
    ) -> SemanticNodeId:
        """Visit a node and its children."""
        current_id: SemanticNodeId = node_id or self._ids.node_id()
        graph_node: SemanticGraphNode = SemanticGraphNode(
            id=current_id,
            ast_node=node,
            kind=self._classifier.kind_for(node=node),
            scope_id=scope_id,
            parent_id=parent_id,
            name=self._classifier.name_for(node=node),
            role=role,
        )
        self._graph.add_node(node=graph_node)
        if parent_id is not None:
            self._graph.add_edge(
                source_id=parent_id,
                target_id=current_id,
                kind=SemanticEdgeKind.CHILD,
            )
        return self._dispatch(
            node=node,
            node_id=current_id,
            scope_id=scope_id,
        )

    def _dispatch(
        self,
        *,
        node: AST,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> SemanticNodeId:
        """Apply semantic processing for a node."""
        if self._dispatch_scoped(
            node=node,
            node_id=node_id,
            scope_id=scope_id,
        ):
            return node_id
        self._dispatch_unscoped(
            node=node,
            node_id=node_id,
            scope_id=scope_id,
        )
        self._visit_children(node=node, node_id=node_id, scope_id=scope_id)
        return node_id

    def _dispatch_scoped(
        self,
        *,
        node: AST,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> bool:
        """Process nodes that own a nested scope."""
        handled: bool = False
        if isinstance(node, ClassDef):
            self._class(node=node, node_id=node_id, scope_id=scope_id)
            handled = True
        elif isinstance(node, FunctionDef | AsyncFunctionDef):
            self._function(node=node, node_id=node_id, scope_id=scope_id)
            handled = True
        return handled

    def _dispatch_unscoped(
        self,
        *,
        node: AST,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process ordinary non-scope-owning nodes."""
        if isinstance(node, Assign):
            self._assign(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, AnnAssign):
            self._ann_assign(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, Return):
            self._return(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, Name):
            self._name(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, Attribute):
            self._attribute(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, Call):
            self._call(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, Compare):
            self._compare(node=node, node_id=node_id, scope_id=scope_id)
        elif isinstance(node, AstList | AstTuple | AstDict | AstSet):
            self._container(node=node, node_id=node_id, scope_id=scope_id)

    def _visit_children(
        self,
        *,
        node: AST,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Visit ordinary children."""
        for child in iter_child_nodes(node=node):
            if self._graph.node_id_for_ast(node=child) is not None:
                continue
            self._visit(
                node=child,
                parent_id=node_id,
                scope_id=scope_id,
                role=None,
            )

    def _class(
        self,
        *,
        node: ClassDef,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a class definition and its class scope."""
        self._define_symbol(
            name=node.name,
            kind=SemanticSymbolKind.CLASS,
            scope_id=scope_id,
            node_id=node_id,
        )
        class_scope_id: SemanticScopeId = self._new_scope(
            kind=SemanticScopeKind.CLASS,
            name=node.name,
            node_id=node_id,
            parent_id=scope_id,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=node_id,
            kind=SemanticEdgeKind.ENCLOSES_SCOPE,
            label=class_scope_id,
        )
        self._visit_scoped_children(
            children=tuple(node.body),
            parent_id=node_id,
            scope_id=class_scope_id,
        )

    def _function(
        self,
        *,
        node: SemanticFunctionNode,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a function and its local scope."""
        symbol_kind: SemanticSymbolKind = self._function_symbol_kind(
            scope_id=scope_id,
        )
        self._define_symbol(
            name=node.name,
            kind=symbol_kind,
            scope_id=scope_id,
            node_id=node_id,
        )
        function_scope_id: SemanticScopeId = self._new_scope(
            kind=SemanticScopeKind.FUNCTION,
            name=node.name,
            node_id=node_id,
            parent_id=scope_id,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=node_id,
            kind=SemanticEdgeKind.ENCLOSES_SCOPE,
            label=function_scope_id,
        )
        self._function_arguments(
            node=node,
            function_node_id=node_id,
            scope_id=function_scope_id,
        )
        if node.returns is not None:
            return_hint_id: SemanticNodeId = self._visit(
                node=node.returns,
                parent_id=node_id,
                scope_id=function_scope_id,
                role=SemanticUsageKind.RETURN,
            )
            self._graph.add_edge(
                source_id=node_id,
                target_id=return_hint_id,
                kind=SemanticEdgeKind.HAS_TYPE_HINT,
                label="return",
            )
        self._visit_scoped_children(
            children=tuple(node.body),
            parent_id=node_id,
            scope_id=function_scope_id,
        )

    def _function_arguments(
        self,
        *,
        node: SemanticFunctionNode,
        function_node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process function arguments."""
        argument_nodes: tuple[arg, ...] = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
        for argument in argument_nodes:
            argument_id: SemanticNodeId = self._visit(
                node=argument,
                parent_id=function_node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.ARGUMENT,
            )
            symbol: SemanticSymbol = self._define_symbol(
                name=argument.arg,
                kind=SemanticSymbolKind.ARGUMENT,
                scope_id=scope_id,
                node_id=argument_id,
            )
            if argument.annotation is not None:
                symbol.add_evidence(
                    evidence=TypeInferenceEvidence(
                        kind=TypeEvidenceKind.ANNOTATION,
                        type_hint=AstBackedTypeExpression(
                            node=argument.annotation,
                        ),
                        node_id=argument_id,
                        confidence=1.0,
                        reason="Argument annotation.",
                    ),
                )
        if node.args.vararg is not None:
            self._vararg(
                node=node.args.vararg,
                parent_id=function_node_id,
                scope_id=scope_id,
            )
        if node.args.kwarg is not None:
            self._vararg(
                node=node.args.kwarg,
                parent_id=function_node_id,
                scope_id=scope_id,
            )

    def _vararg(
        self,
        *,
        node: arg,
        parent_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process ``*args`` or ``**kwargs`` arguments."""
        argument_id: SemanticNodeId = self._visit(
            node=node,
            parent_id=parent_id,
            scope_id=scope_id,
            role=SemanticUsageKind.ARGUMENT,
        )
        self._define_symbol(
            name=node.arg,
            kind=SemanticSymbolKind.ARGUMENT,
            scope_id=scope_id,
            node_id=argument_id,
        )

    def _assign(
        self,
        *,
        node: Assign,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process an assignment."""
        value_type: TypeExpression | None = self._inferencer.infer(
            node=node.value,
        )
        value_id: SemanticNodeId = self._visit(
            node=node.value,
            parent_id=node_id,
            scope_id=scope_id,
            role=SemanticUsageKind.STORE,
        )
        for target in node.targets:
            self._assignment_target(
                target=target,
                value_id=value_id,
                value_type=value_type,
                parent_id=node_id,
                scope_id=scope_id,
            )

    def _ann_assign(
        self,
        *,
        node: AnnAssign,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process an annotated assignment."""
        value_id: SemanticNodeId | None | str = None
        value_type: TypeExpression | None = None
        if node.value is not None:
            value_type = self._inferencer.infer(
                node=node.value,
            )
            value_id = self._visit(
                node=node.value,
                parent_id=node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.STORE,
            )
        self._assignment_target(
            target=node.target,
            value_id=value_id,
            value_type=value_type,
            parent_id=node_id,
            scope_id=scope_id,
        )
        annotation_id: SemanticNodeId = self._visit(
            node=node.annotation,
            parent_id=node_id,
            scope_id=scope_id,
            role=None,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=annotation_id,
            kind=SemanticEdgeKind.HAS_TYPE_HINT,
            label="annotation",
        )

    def _assignment_target(
        self,
        *,
        target: expr,
        value_id: SemanticNodeId | None,
        value_type: TypeExpression | None,
        parent_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process one assignment target."""
        target_id: SemanticNodeId = self._visit(
            node=target,
            parent_id=parent_id,
            scope_id=scope_id,
            role=SemanticUsageKind.STORE,
        )
        if value_id is not None:
            self._graph.add_edge(
                source_id=target_id,
                target_id=value_id,
                kind=SemanticEdgeKind.ASSIGNS_VALUE,
            )
        if isinstance(target, Name):
            symbol: SemanticSymbol = self._define_symbol(
                name=target.id,
                kind=SemanticSymbolKind.VARIABLE,
                scope_id=scope_id,
                node_id=target_id,
            )
            if value_type is not None:
                symbol.add_evidence(
                    evidence=TypeInferenceEvidence(
                        kind=TypeEvidenceKind.ASSIGNMENT_VALUE,
                        type_hint=value_type,
                        node_id=target_id,
                        confidence=0.85,
                        reason="Assigned value inference.",
                    ),
                )
        elif isinstance(target, Attribute):
            self._graph.add_edge(
                source_id=target_id,
                target_id=target_id,
                kind=SemanticEdgeKind.WRITES_ATTRIBUTE,
                label=target.attr,
            )

    def _return(
        self,
        *,
        node: Return,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a return statement."""
        if node.value is None:
            return
        value_id: SemanticNodeId = self._visit(
            node=node.value,
            parent_id=node_id,
            scope_id=scope_id,
            role=SemanticUsageKind.RETURN,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=value_id,
            kind=SemanticEdgeKind.RETURNS_VALUE,
        )

    def _name(
        self,
        *,
        node: Name,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a name usage."""
        symbol: SemanticSymbol | None = self._graph.lookup_symbol(
            name=node.id,
            scope_id=scope_id,
        )
        if symbol is None:
            return
        symbol.add_usage(node_id=node_id)
        self._graph.add_edge(
            source_id=node_id,
            target_id=symbol.definition_node_id or node_id,
            kind=SemanticEdgeKind.USES,
            label=node.id,
        )

    def _attribute(
        self,
        *,
        node: Attribute,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process an attribute usage."""
        value_id: SemanticNodeId = self._visit(
            node=node.value,
            parent_id=node_id,
            scope_id=scope_id,
            role=SemanticUsageKind.LOAD,
        )
        edge_kind: SemanticEdgeKind = SemanticEdgeKind.READS_ATTRIBUTE
        if isinstance(node.ctx, Store):
            edge_kind = SemanticEdgeKind.WRITES_ATTRIBUTE
        self._graph.add_edge(
            source_id=node_id,
            target_id=value_id,
            kind=edge_kind,
            label=node.attr,
        )

    def _call(
        self,
        *,
        node: Call,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a call expression."""
        function_id: SemanticNodeId = self._visit(
            node=node.func,
            parent_id=node_id,
            scope_id=scope_id,
            role=SemanticUsageKind.CALL_TARGET,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=function_id,
            kind=SemanticEdgeKind.CALLS,
        )
        for call_arg in node.args:
            argument_id: SemanticNodeId = self._visit(
                node=call_arg,
                parent_id=node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.CALL_ARGUMENT,
            )
            self._graph.add_edge(
                source_id=node_id,
                target_id=argument_id,
                kind=SemanticEdgeKind.USES,
                label="call-arg",
            )
        for keyword in node.keywords:
            keyword_id: SemanticNodeId = self._visit(
                node=keyword.value,
                parent_id=node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.CALL_ARGUMENT,
            )
            self._graph.add_edge(
                source_id=node_id,
                target_id=keyword_id,
                kind=SemanticEdgeKind.USES,
                label=keyword.arg,
            )

    def _compare(
        self,
        *,
        node: Compare,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a comparison expression."""
        left_id: SemanticNodeId = self._visit(
            node=node.left,
            parent_id=node_id,
            scope_id=scope_id,
            role=SemanticUsageKind.COMPARISON_LEFT,
        )
        self._graph.add_edge(
            source_id=node_id,
            target_id=left_id,
            kind=SemanticEdgeKind.COMPARES_WITH,
            label="left",
        )
        for comparator in node.comparators:
            right_id: SemanticNodeId = self._visit(
                node=comparator,
                parent_id=node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.COMPARISON_RIGHT,
            )
            self._graph.add_edge(
                source_id=node_id,
                target_id=right_id,
                kind=SemanticEdgeKind.COMPARES_WITH,
                label="right",
            )

    def _container(
        self,
        *,
        node: AST,
        node_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Process a container literal."""
        for child in iter_child_nodes(node=node):
            child_id: SemanticNodeId = self._visit(
                node=child,
                parent_id=node_id,
                scope_id=scope_id,
                role=SemanticUsageKind.CONTAINER_ELEMENT,
            )
            self._graph.add_edge(
                source_id=node_id,
                target_id=child_id,
                kind=SemanticEdgeKind.CONTAINS_VALUE,
            )

    def _visit_scoped_children(
        self,
        *,
        children: tuple[stmt, ...],
        parent_id: SemanticNodeId,
        scope_id: SemanticScopeId,
    ) -> None:
        """Visit children in a nested scope."""
        for child in children:
            self._visit(
                node=child,
                parent_id=parent_id,
                scope_id=scope_id,
                role=None,
            )

    def _new_scope(
        self,
        *,
        kind: SemanticScopeKind,
        name: str,
        node_id: SemanticNodeId,
        parent_id: SemanticScopeId,
    ) -> SemanticScopeId:
        """Create a new lexical scope."""
        scope_id: SemanticScopeId = self._ids.scope_id()
        self._graph.add_scope(
            scope=SemanticScope(
                id=scope_id,
                kind=kind,
                name=name,
                node_id=node_id,
                parent_id=parent_id,
            ),
        )
        return scope_id

    def _define_symbol(
        self,
        *,
        name: str,
        kind: SemanticSymbolKind,
        scope_id: SemanticScopeId,
        node_id: SemanticNodeId,
    ) -> SemanticSymbol:
        """Define or reuse a symbol in a scope."""
        existing_id: SemanticSymbolId | None = self._graph.scopes[
            scope_id
        ].symbols.get(
            name,
        )
        if existing_id is not None:
            symbol: SemanticSymbol = self._graph.symbols[existing_id]
            symbol.definition_node_id = node_id
            return symbol
        symbol_id: SemanticSymbolId = self._ids.symbol_id()
        symbol = SemanticSymbol(
            id=symbol_id,
            name=name,
            kind=kind,
            scope_id=scope_id,
            definition_node_id=node_id,
        )
        self._graph.add_symbol(symbol=symbol)
        return symbol

    def _function_symbol_kind(
        self,
        *,
        scope_id: SemanticScopeId,
    ) -> SemanticSymbolKind:
        """Return function or method symbol kind from parent scope."""
        scope: SemanticScope = self._graph.scopes[scope_id]
        if scope.kind == SemanticScopeKind.CLASS:
            return SemanticSymbolKind.METHOD
        return SemanticSymbolKind.FUNCTION


class SemanticGraphQuery:
    """High-level query facade for semantic graph data."""

    def __init__(self, *, graph: SemanticAstGraph) -> None:
        """Initialize the query facade."""
        self._graph: SemanticAstGraph = graph

    def variable(self, *, name: str) -> tuple[SemanticValueUsage, ...]:
        """Return definition, usage, and evidence for a variable."""
        return self._graph.value_usage(name=name)

    def functions_returning(
        self,
        *,
        type_hint: TypeExpression,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return functions with matching inferred return evidence."""
        target_key: str = type_hint.key()
        return tuple(
            function
            for function in self._graph.functions()
            if self._function_has_return_type(
                function=function,
                target_key=target_key,
            )
        )

    def init_methods(
        self,
        *,
        class_name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return ``__init__`` method views for a class."""
        return self._graph.init_methods(class_name=class_name)

    def new_methods(
        self,
        *,
        class_name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return ``__new__`` method views for a class."""
        return self._graph.new_methods(class_name=class_name)

    def calls_named(self, *, name: str) -> tuple[SemanticAstNodeView, ...]:
        """Return call nodes whose target has a simple name."""
        result: list[SemanticAstNodeView] = []
        for node in self._graph.nodes.values():
            if node.kind != SemanticNodeKind.CALL:
                continue
            if self._call_name(node=node) == name:
                result.append(self._graph.view(node_id=node.id))
        return tuple(result)

    def attributes_named(
        self,
        *,
        name: str,
    ) -> tuple[SemanticAstNodeView, ...]:
        """Return attribute nodes by attribute name."""
        return tuple(
            self._graph.view(node_id=node.id)
            for node in self._graph.nodes.values()
            if node.kind == SemanticNodeKind.ATTRIBUTE and node.name == name
        )

    def _function_has_return_type(
        self,
        *,
        function: SemanticAstNodeView,
        target_key: str,
    ) -> bool:
        """Return whether a function has matching return evidence."""
        for child in function.descendants_of_kind(
            kind=SemanticNodeKind.RETURN,
        ):
            for edge in child.outgoing_edges:
                if edge.kind != SemanticEdgeKind.RETURNS_VALUE:
                    continue
                value_node: SemanticGraphNode = self._graph.nodes[
                    edge.target_id
                ]
                inferred: TypeExpression | None = (
                    SemanticLiteralTypeInferencer(
                        graph=self._graph,
                    ).infer(node=value_node.ast_node)
                )
                if inferred is not None and inferred.key() == target_key:
                    return True
        return False

    def _call_name(self, *, node: SemanticGraphNode) -> str | None:
        """Return a simple call target name when available."""
        if not isinstance(node.ast_node, Call):
            return None
        func: expr = node.ast_node.func
        if isinstance(func, Name):
            return func.id
        if isinstance(func, Attribute):
            return func.attr
        return None


class SemanticGraphTypeSynthesizer:
    """Synthesize easier type-hint edits from collected evidence."""

    def __init__(self, *, graph: SemanticAstGraph) -> None:
        """Initialize the synthesizer."""
        self._graph: SemanticAstGraph = graph
        self._merger: SemanticEvidenceMerger = SemanticEvidenceMerger()

    def inferred_symbol_type(self, *, name: str) -> TypeExpression | None:
        """Infer a type for a symbol name from all evidence."""
        evidence: list[TypeInferenceEvidence] = []
        for symbol in self._graph.symbols_named(name=name):
            evidence.extend(symbol.evidence)
        if not evidence:
            return None
        return self._merger.merge(evidence=tuple(evidence))

    def inferred_argument_type(
        self,
        *,
        function: SemanticFunctionNode,
        argument_name: str,
    ) -> TypeExpression | None:
        """Infer an argument type from graph evidence."""
        function_view: SemanticAstNodeView | None = self._graph.view_for_ast(
            node=function,
        )
        if function_view is None:
            return None
        for child in function_view.descendants_of_kind(
            kind=SemanticNodeKind.ARGUMENT,
        ):
            graph_node: SemanticGraphNode = child.graph_node
            if graph_node.name != argument_name:
                continue
            symbols: tuple[SemanticSymbol, ...] = child.symbols
            if not symbols:
                return None
            return self._merger.merge(evidence=tuple(symbols[0].evidence))
        return None

    def inferred_return_type(
        self,
        *,
        function: SemanticFunctionNode,
    ) -> TypeExpression | None:
        """Infer a return type from return statements."""
        function_view: SemanticAstNodeView | None = self._graph.view_for_ast(
            node=function,
        )
        if function_view is None:
            return None
        evidence: list[TypeInferenceEvidence] = []
        inferencer: SemanticLiteralTypeInferencer = (
            SemanticLiteralTypeInferencer(
                graph=self._graph,
            )
        )
        for return_view in function_view.descendants_of_kind(
            kind=SemanticNodeKind.RETURN,
        ):
            if not isinstance(return_view.node, Return):
                continue
            if return_view.node.value is None:
                evidence.append(
                    TypeInferenceEvidence(
                        kind=TypeEvidenceKind.RETURN_VALUE,
                        type_hint=Types.none,
                        node_id=return_view.node_id,
                        confidence=0.9,
                        reason="Explicit bare return.",
                    ),
                )
                continue
            inferred: TypeExpression | None = inferencer.infer(
                node=return_view.node.value,
            )
            if inferred is not None:
                evidence.append(
                    TypeInferenceEvidence(
                        kind=TypeEvidenceKind.RETURN_VALUE,
                        type_hint=inferred,
                        node_id=return_view.node_id,
                        confidence=0.8,
                        reason="Return value inference.",
                    ),
                )
        if not evidence:
            return None
        return self._merger.merge(evidence=tuple(evidence))


class SemanticGraphEditingFacade:
    """Bridge semantic graph inference with existing tree editors."""

    def __init__(
        self,
        *,
        graph: SemanticAstGraph,
        collector: SemanticCodegenEditingCollector,
    ) -> None:
        """Initialize the editing facade."""
        self._graph: SemanticAstGraph = graph
        self._collector: SemanticCodegenEditingCollector = collector
        self._synthesizer: SemanticGraphTypeSynthesizer = (
            SemanticGraphTypeSynthesizer(
                graph=graph,
            )
        )

    def annotate_function_from_evidence(
        self,
        *,
        function: FunctionDef,
    ) -> None:
        """Apply inferred argument and return annotations in-place."""
        for argument in self._all_arguments(function=function):
            inferred: TypeExpression | None = (
                self._synthesizer.inferred_argument_type(
                    function=function,
                    argument_name=argument.arg,
                )
            )
            if inferred is not None:
                self._collector.edit.functions.arg(
                    function=function,
                    name=argument.arg,
                    type_hint=inferred,
                )
        return_type: TypeExpression | None = (
            self._synthesizer.inferred_return_type(
                function=function,
            )
        )
        if return_type is not None:
            self._collector.edit.functions.returns(
                function=function,
                type_hint=return_type,
            )

    def _all_arguments(self, *, function: FunctionDef) -> tuple[arg, ...]:
        """Return all normal, vararg, and kwarg argument nodes."""
        result: list[arg] = [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]
        if function.args.vararg is not None:
            result.append(function.args.vararg)
        if function.args.kwarg is not None:
            result.append(function.args.kwarg)
        return tuple(result)


class SemanticGraphParseUnparseToolkit(SemanticModelParseUnparseToolkit):
    """Toolkit that parses code into model and semantic graph layers."""

    def parse_graph(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> SemanticGraphParseResult:
        """Parse source into semantic model and graph."""
        model: ParsedSemanticModel = self.parse_model(
            source=source,
            filename=filename,
        )
        graph: SemanticAstGraph = SemanticGraphBuilder().build(
            module=model.parsed.module,
        )
        return SemanticGraphParseResult(model=model, graph=graph)


class SemanticGraphEditingCollector(SemanticModelEditingCollector):
    """Editing collector with semantic graph inference helpers."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the graph-aware editing collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            existing_type_aliases=existing_type_aliases,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self.graph: SemanticAstGraph | None = None
        self.query: SemanticGraphQuery | None = None
        self.infer: SemanticGraphTypeSynthesizer | None = None
        self.graph_edit: SemanticGraphEditingFacade | None = None

    @classmethod
    def from_graph_result(
        cls,
        *,
        result: SemanticGraphParseResult,
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> SemanticGraphEditingCollector:
        """Create a collector from a graph parse result."""
        type_alias_nodes: tuple[AstTypeAlias, ...] = tuple(
            item.node
            for item in result.model.type_aliases
            if isinstance(item.node, AstTypeAlias)
        )
        collector: SemanticGraphEditingCollector = cls(
            existing_nodes=(
                *result.model.context.import_nodes,
                *result.model.context.class_nodes,
            ),
            existing_type_aliases=type_alias_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        collector.attach_graph(graph=result.graph)
        return collector

    def attach_graph(self, *, graph: SemanticAstGraph) -> None:
        """Attach a graph and create query/inference facades."""
        self.graph = graph
        self.query = SemanticGraphQuery(graph=graph)
        self.infer = SemanticGraphTypeSynthesizer(graph=graph)
        self.graph_edit = SemanticGraphEditingFacade(
            graph=graph,
            collector=self,
        )


class TypeParameterNameReader:
    """Read names from PEP 695 type parameter nodes safely."""

    @staticmethod
    def name(*, parameter: type_param) -> str:
        """Return the declared type parameter name."""
        if isinstance(parameter, AstTypeVar | AstParamSpec | AstTypeVarTuple):
            return parameter.name
        msg: str = "Unsupported type parameter node."
        fail(message=msg)


class GenericTypeParameterFactory:
    """Create PEP 695 type parameter AST nodes semantically."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the factory."""
        self._resolver: TypeExpressionResolver = resolver
        self._validator: IdentifierValidator = IdentifierValidator()

    def typevar(
        self,
        *,
        name: str,
        bound: TypeExpression | None = None,
        default: TypeExpression | None = None,
    ) -> AstTypeVar:
        """Create a ``T`` type parameter node."""
        spec: GenericTypeParameterSpec = GenericTypeParameterSpec(
            name=name,
            kind=GenericTypeParameterKind.TYPEVAR,
            bound=bound,
            default=default,
        )
        node: type_param = self.node(spec=spec)
        if not isinstance(node, AstTypeVar):
            msg: str = "Internal error while creating TypeVar node."
            fail(message=msg)
        return node

    def paramspec(
        self,
        *,
        name: str,
        default: TypeExpression | None = None,
    ) -> AstParamSpec:
        """Create a ``**P`` parameter specification node."""
        spec: GenericTypeParameterSpec = GenericTypeParameterSpec(
            name=name,
            kind=GenericTypeParameterKind.PARAMSPEC,
            default=default,
        )
        node: type_param = self.node(spec=spec)
        if not isinstance(node, AstParamSpec):
            msg: str = "Internal error while creating ParamSpec node."
            fail(message=msg)
        return node

    def typevartuple(
        self,
        *,
        name: str,
        default: TypeExpression | None = None,
    ) -> AstTypeVarTuple:
        """Create a ``*Ts`` type variable tuple node."""
        spec: GenericTypeParameterSpec = GenericTypeParameterSpec(
            name=name,
            kind=GenericTypeParameterKind.TYPEVARTUPLE,
            default=default,
        )
        node: type_param = self.node(spec=spec)
        if not isinstance(node, AstTypeVarTuple):
            msg: str = "Internal error while creating TypeVarTuple node."
            fail(message=msg)
        return node

    def node(self, *, spec: GenericTypeParameterSpec) -> type_param:
        """Create one type parameter node from a semantic spec."""
        self._validator.validate_identifier(
            name=spec.name,
            label="type parameter",
        )
        default_node: expr | None = self._optional_node(value=spec.default)
        if spec.kind is GenericTypeParameterKind.TYPEVAR:
            return AstTypeVar(
                name=spec.name,
                bound=self._optional_node(value=spec.bound),
                default_value=default_node,
            )
        if spec.kind is GenericTypeParameterKind.PARAMSPEC:
            return AstParamSpec(name=spec.name, default_value=default_node)
        return AstTypeVarTuple(name=spec.name, default_value=default_node)

    def block(
        self,
        *,
        specs: tuple[GenericTypeParameterSpec, ...],
    ) -> GenericTypeParameterBlock:
        """Create an ordered type-parameter block."""
        return GenericTypeParameterBlock(
            parameters=tuple(self.node(spec=spec) for spec in specs),
        )

    def _optional_node(self, *, value: TypeExpression | None) -> expr | None:
        """Return a type expression AST node when available."""
        if value is None:
            return None
        return self._resolver.annotation(value=value)


class TypeHintPrefixFactory:
    """Create semantic star and double-star type-hint wrappers."""

    @staticmethod
    def star(*, item: TypeExpression) -> StarTypeHintRef:
        """Create a single-star type-hint wrapper."""
        return StarTypeHintRef(item=item)

    @staticmethod
    def double_star(*, item: TypeExpression) -> DoubleStarTypeHintRef:
        """Create a double-star type-hint wrapper."""
        return DoubleStarTypeHintRef(item=item)


class GenericTypeParameterEditor:
    """Edit PEP 695 type parameters on functions, classes, and aliases."""

    def __init__(self, *, resolver: TypeExpressionResolver) -> None:
        """Initialize the editor."""
        self._factory: GenericTypeParameterFactory = (
            GenericTypeParameterFactory(
                resolver=resolver,
            )
        )

    def set_parameters(
        self,
        *,
        node: TypeParameterOwnerNode,
        specs: tuple[GenericTypeParameterSpec, ...],
    ) -> GenericTypeParameterBlock:
        """Replace all type parameters on a supported AST node."""
        block: GenericTypeParameterBlock = self._factory.block(specs=specs)
        node.type_params = list(block.parameters)
        return block

    def add_typevar(
        self,
        *,
        node: TypeParameterOwnerNode,
        name: str,
        bound: TypeExpression | None = None,
        default: TypeExpression | None = None,
    ) -> AstTypeVar:
        """Append a TypeVar-like parameter to an AST node."""
        parameter: AstTypeVar = self._factory.typevar(
            name=name,
            bound=bound,
            default=default,
        )
        node.type_params.append(parameter)
        return parameter

    def add_paramspec(
        self,
        *,
        node: TypeParameterOwnerNode,
        name: str,
        default: TypeExpression | None = None,
    ) -> AstParamSpec:
        """Append a ParamSpec-like parameter to an AST node."""
        parameter: AstParamSpec = self._factory.paramspec(
            name=name,
            default=default,
        )
        node.type_params.append(parameter)
        return parameter

    def add_typevartuple(
        self,
        *,
        node: TypeParameterOwnerNode,
        name: str,
        default: TypeExpression | None = None,
    ) -> AstTypeVarTuple:
        """Append a TypeVarTuple-like parameter to an AST node."""
        parameter: AstTypeVarTuple = self._factory.typevartuple(
            name=name,
            default=default,
        )
        node.type_params.append(parameter)
        return parameter

    def clear(self, *, node: TypeParameterOwnerNode) -> None:
        """Remove all type parameters from a supported AST node."""
        node.type_params.clear()


class AdvancedSemanticUsageAnalyzer:
    """Analyze conditions, mutations, decorators, inheritance, and scopes."""

    def __init__(self) -> None:
        """Initialize the analyzer."""
        self._usages: list[AdvancedUsageRecord] = []
        self._functions: list[FunctionFlowRecord] = []
        self._classes: list[ClassFlowRecord] = []
        self._class_stack: list[_ClassFlowMutable] = []

    def analyze(self, *, module: Module) -> AdvancedSemanticUsageModel:
        """Analyze a module and return an introspective usage model."""
        self._usages = []
        self._functions = []
        self._classes = []
        self._class_stack = []
        self._visit_body(
            body=tuple(module.body),
            scope=AdvancedScopeRef(parts=()),
        )
        return AdvancedSemanticUsageModel(
            usages=tuple(self._usages),
            functions=tuple(self._functions),
            classes=tuple(self._classes),
        )

    def _visit_body(
        self,
        *,
        body: tuple[stmt, ...],
        scope: AdvancedScopeRef,
    ) -> None:
        """Visit a statement body while preserving scope."""
        for item in body:
            self._visit_stmt(node=item, scope=scope)

    def _visit_stmt(self, *, node: stmt, scope: AdvancedScopeRef) -> None:
        """Visit one statement with scope tracking."""
        if isinstance(node, ClassDef):
            self._visit_class(node=node, scope=scope)
        elif isinstance(node, FunctionDef | AsyncFunctionDef):
            self._visit_function(node=node, scope=scope)
        elif isinstance(node, Assign):
            self._visit_assign(node=node, scope=scope)
        elif isinstance(node, AnnAssign):
            self._visit_ann_assign(node=node, scope=scope)
        elif isinstance(node, If):
            self._visit_if(node=node, scope=scope)
        elif isinstance(node, Return):
            self._record_return(node=node, scope=scope)
            self._visit_optional_expr(node=node.value, scope=scope)
        else:
            self._visit_ast_children(node=node, scope=scope)

    def _visit_class(self, *, node: ClassDef, scope: AdvancedScopeRef) -> None:
        """Visit a class definition and track relationships."""
        class_scope: AdvancedScopeRef = scope.child(name=node.name)
        class_flow: _ClassFlowMutable = _ClassFlowMutable(
            name=node.name,
            scope=class_scope,
            bases=tuple(unparse(ast_obj=base) for base in node.bases),
            decorators=tuple(
                unparse(ast_obj=item) for item in node.decorator_list
            ),
        )
        self._class_stack.append(class_flow)
        self._record_class_decorators(node=node, scope=scope)
        self._record_inheritance(node=node, scope=scope)
        self._visit_body(body=tuple(node.body), scope=class_scope)
        completed: _ClassFlowMutable = self._class_stack.pop()
        self._classes.append(completed.frozen())

    def _visit_function(
        self,
        *,
        node: SemanticFunctionNode,
        scope: AdvancedScopeRef,
    ) -> None:
        """Visit a function or method definition."""
        function_scope: AdvancedScopeRef = scope.child(name=node.name)
        decorators: tuple[str, ...] = tuple(
            unparse(ast_obj=item) for item in node.decorator_list
        )
        self._record_function_decorators(node=node, scope=scope)
        self._record_property_relationship(node=node)
        self._record_special_method(node=node)
        self._functions.append(
            FunctionFlowRecord(
                name=node.name,
                scope=function_scope,
                arguments=tuple(
                    argument.arg for argument in self._arguments(node=node)
                ),
                returns=tuple(
                    child
                    for child in walk(node=node)
                    if isinstance(child, Return)
                ),
                decorators=decorators,
                type_parameters=tuple(
                    TypeParameterNameReader.name(parameter=parameter)
                    for parameter in node.type_params
                ),
            ),
        )
        self._visit_body(body=tuple(node.body), scope=function_scope)

    def _visit_assign(self, *, node: Assign, scope: AdvancedScopeRef) -> None:
        """Visit an assignment and record variable categories."""
        for target in node.targets:
            self._record_assignment_target(
                target=target,
                value=node.value,
                scope=scope,
            )
        self._visit_expr(node=node.value, scope=scope)

    def _visit_ann_assign(
        self,
        *,
        node: AnnAssign,
        scope: AdvancedScopeRef,
    ) -> None:
        """Visit an annotated assignment and record variable categories."""
        self._record_assignment_target(
            target=node.target,
            value=node.value,
            scope=scope,
        )
        self._visit_optional_expr(node=node.value, scope=scope)

    def _visit_if(self, *, node: If, scope: AdvancedScopeRef) -> None:
        """Visit an if statement and track narrowing conditions."""
        self._record_condition(node=node.test, scope=scope)
        self._visit_expr(node=node.test, scope=scope)
        self._visit_body(body=tuple(node.body), scope=scope)
        self._visit_body(body=tuple(node.orelse), scope=scope)

    def _visit_ast_children(
        self,
        *,
        node: AST,
        scope: AdvancedScopeRef,
    ) -> None:
        """Visit child expressions/statements of an arbitrary node."""
        for child in iter_child_nodes(node=node):
            if isinstance(child, stmt):
                self._visit_stmt(node=child, scope=scope)
            elif isinstance(child, expr):
                self._visit_expr(node=child, scope=scope)

    def _visit_expr(self, *, node: expr, scope: AdvancedScopeRef) -> None:
        """Visit one expression and record detailed usage."""
        if isinstance(node, Call):
            self._record_call(node=node, scope=scope)
        elif isinstance(node, Attribute):
            self._record_attribute(node=node, scope=scope)
        elif isinstance(node, Subscript):
            self._record_subscript(node=node, scope=scope)
        elif isinstance(node, Compare):
            self._record_comparison(node=node, scope=scope)
        self._visit_ast_children(node=node, scope=scope)

    def _visit_optional_expr(
        self,
        *,
        node: expr | None,
        scope: AdvancedScopeRef,
    ) -> None:
        """Visit an optional expression."""
        if node is not None:
            self._visit_expr(node=node, scope=scope)

    def _record_assignment_target(
        self,
        *,
        target: expr,
        value: expr | None,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record class and instance assignment categories."""
        _: expr | None = value
        if isinstance(target, Name) and self._inside_class_body(scope=scope):
            self._record_class_variable(
                name=target.id,
                node=target,
                scope=scope,
            )
        elif isinstance(target, Attribute):
            self._record_attribute_write(target=target, scope=scope)
        elif isinstance(target, Subscript):
            self._add_usage(
                kind=AdvancedUsageKind.SUBSCRIPT_WRITE,
                name=self._expr_name(node=target.value),
                scope=scope,
                node=target,
                detail=unparse(ast_obj=target),
            )

    def _record_class_variable(
        self,
        *,
        name: str,
        node: AST,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record a class variable declaration."""
        if not self._class_stack:
            return
        class_flow: _ClassFlowMutable = self._class_stack[-1]
        record: ClassVariableRecord = ClassVariableRecord(
            owner=class_flow.name,
            name=name,
            node=node,
            is_instance=False,
            method_name=None,
        )
        class_flow.class_variables.append(record)
        self._add_usage(
            kind=AdvancedUsageKind.CLASS_VARIABLE,
            name=name,
            scope=scope,
            node=node,
            detail="class variable",
        )

    def _record_attribute_write(
        self,
        *,
        target: Attribute,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record an attribute write and instance variable when applicable."""
        name: str = target.attr
        self._add_usage(
            kind=AdvancedUsageKind.ATTRIBUTE_WRITE,
            name=name,
            scope=scope,
            node=target,
            detail=unparse(ast_obj=target),
        )
        if not self._class_stack or not self._is_self_attribute(node=target):
            return
        class_flow: _ClassFlowMutable = self._class_stack[-1]
        class_flow.instance_variables.append(
            ClassVariableRecord(
                owner=class_flow.name,
                name=name,
                node=target,
                is_instance=True,
                method_name=scope.parts[-1] if scope.parts else None,
            ),
        )
        self._add_usage(
            kind=AdvancedUsageKind.INSTANCE_VARIABLE,
            name=name,
            scope=scope,
            node=target,
            detail="instance variable",
        )

    def _record_condition(
        self,
        *,
        node: expr,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record conditions and isinstance narrowings."""
        if (
            isinstance(node, Call)
            and self._call_name(node=node) == "isinstance"
        ):
            self._record_isinstance(node=node, scope=scope)
            return
        if isinstance(node, Compare):
            self._record_comparison(node=node, scope=scope)
            return
        self._add_usage(
            kind=AdvancedUsageKind.CONDITION,
            name=self._expr_name(node=node),
            scope=scope,
            node=node,
            detail=unparse(ast_obj=node),
        )

    def _record_isinstance(
        self,
        *,
        node: Call,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record an ``isinstance`` narrowing."""
        if len(node.args) < Constants.two_item_count:
            return
        variable: expr = node.args[0]
        type_expr: expr = node.args[1]
        self._add_usage(
            kind=AdvancedUsageKind.ISINSTANCE_NARROWING,
            name=self._expr_name(node=variable),
            scope=scope,
            node=node,
            detail=unparse(ast_obj=type_expr),
        )

    def _record_comparison(
        self,
        *,
        node: Compare,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record all comparison operands for later narrowing."""
        left_name: str = self._expr_name(node=node.left)
        self._add_usage(
            kind=AdvancedUsageKind.COMPARISON,
            name=left_name,
            scope=scope,
            node=node,
            detail=unparse(ast_obj=node),
        )
        for comparator in node.comparators:
            self._add_usage(
                kind=AdvancedUsageKind.COMPARISON,
                name=self._expr_name(node=comparator),
                scope=scope,
                node=node,
                detail=unparse(ast_obj=node),
            )

    def _record_call(self, *, node: Call, scope: AdvancedScopeRef) -> None:
        """Record calls and container mutation methods."""
        if isinstance(node.func, Attribute):
            mutation_kind: AdvancedUsageKind | None = (
                AdvancedUsageTables.mutating_methods.get(
                    node.func.attr,
                )
            )
            if mutation_kind is not None:
                self._add_usage(
                    kind=mutation_kind,
                    name=self._expr_name(node=node.func.value),
                    scope=scope,
                    node=node,
                    detail=unparse(ast_obj=node),
                )

    def _record_attribute(
        self,
        *,
        node: Attribute,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record attribute reads."""
        if isinstance(node.ctx, Store):
            return
        self._add_usage(
            kind=AdvancedUsageKind.ATTRIBUTE_READ,
            name=node.attr,
            scope=scope,
            node=node,
            detail=unparse(ast_obj=node),
        )

    def _record_subscript(
        self,
        *,
        node: Subscript,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record subscript and slice use."""
        name: str = self._expr_name(node=node.value)
        detail: str = unparse(ast_obj=node.slice)
        if isinstance(node.slice, Constant) and node.slice.value is Ellipsis:
            usage_kind: AdvancedUsageKind = AdvancedUsageKind.SLICE
        else:
            usage_kind = AdvancedUsageKind.SUBSCRIPT_READ
        self._add_usage(
            kind=usage_kind,
            name=name,
            scope=scope,
            node=node,
            detail=detail,
        )

    def _record_return(self, *, node: Return, scope: AdvancedScopeRef) -> None:
        """Record a return value use."""
        self._add_usage(
            kind=AdvancedUsageKind.RETURN,
            name="return",
            scope=scope,
            node=node,
            detail=unparse(ast_obj=node.value)
            if node.value is not None
            else "None",
        )

    def _record_class_decorators(
        self,
        *,
        node: ClassDef,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record class decorator relationships."""
        for decorator in node.decorator_list:
            self._add_usage(
                kind=AdvancedUsageKind.DECORATOR,
                name=node.name,
                scope=scope,
                node=decorator,
                detail=unparse(ast_obj=decorator),
            )

    def _record_function_decorators(
        self,
        *,
        node: SemanticFunctionNode,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record function decorator relationships."""
        for decorator in node.decorator_list:
            self._add_usage(
                kind=AdvancedUsageKind.DECORATOR,
                name=node.name,
                scope=scope,
                node=decorator,
                detail=unparse(ast_obj=decorator),
            )

    def _record_inheritance(
        self,
        *,
        node: ClassDef,
        scope: AdvancedScopeRef,
    ) -> None:
        """Record inheritance base expressions."""
        for base in node.bases:
            self._add_usage(
                kind=AdvancedUsageKind.INHERITANCE,
                name=node.name,
                scope=scope,
                node=base,
                detail=unparse(ast_obj=base),
            )

    def _record_property_relationship(
        self,
        *,
        node: SemanticFunctionNode,
    ) -> None:
        """Record property getter, setter, and deleter relationships."""
        if not self._class_stack or not isinstance(node, FunctionDef):
            return
        class_flow: _ClassFlowMutable = self._class_stack[-1]
        for decorator in node.decorator_list:
            if isinstance(decorator, Name) and decorator.id == "property":
                class_flow.getters[node.name] = node
                self._property_usage(
                    kind=AdvancedUsageKind.PROPERTY_GETTER,
                    node=node,
                )
            elif (
                isinstance(decorator, Attribute) and decorator.attr == "setter"
            ):
                property_name: str = self._expr_name(node=decorator.value)
                class_flow.setters[property_name] = node
                self._property_usage(
                    kind=AdvancedUsageKind.PROPERTY_SETTER,
                    node=node,
                )
            elif (
                isinstance(decorator, Attribute)
                and decorator.attr == "deleter"
            ):
                property_name = self._expr_name(node=decorator.value)
                class_flow.deleters[property_name] = node
                self._property_usage(
                    kind=AdvancedUsageKind.PROPERTY_DELETER,
                    node=node,
                )

    def _record_special_method(self, *, node: SemanticFunctionNode) -> None:
        """Record ``__init__`` and ``__new__`` for the current class."""
        if not self._class_stack or not isinstance(node, FunctionDef):
            return
        class_flow: _ClassFlowMutable = self._class_stack[-1]
        if node.name == "__init__":
            class_flow.init_method = node
        elif node.name == "__new__":
            class_flow.new_method = node

    def _property_usage(
        self,
        *,
        kind: AdvancedUsageKind,
        node: FunctionDef,
    ) -> None:
        """Record a property accessor usage."""
        if not self._class_stack:
            return
        self._add_usage(
            kind=kind,
            name=node.name,
            scope=self._class_stack[-1].scope,
            node=node,
            detail=kind.value,
        )

    def _arguments(self, *, node: SemanticFunctionNode) -> tuple[arg, ...]:
        """Return every argument node in source order."""
        result: list[arg] = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg is not None:
            result.append(node.args.vararg)
        if node.args.kwarg is not None:
            result.append(node.args.kwarg)
        return tuple(result)

    def _inside_class_body(self, *, scope: AdvancedScopeRef) -> bool:
        """Return whether the scope is directly a class body."""
        return bool(self._class_stack) and self._class_stack[-1].scope == scope

    def _is_self_attribute(self, *, node: Attribute) -> bool:
        """Return whether an attribute is written on ``self``."""
        return isinstance(node.value, Name) and node.value.id == "self"

    def _call_name(self, *, node: Call) -> str:
        """Return a readable call target name."""
        return self._expr_name(node=node.func)

    def _expr_name(self, *, node: expr) -> str:
        """Return a stable readable expression name."""
        if isinstance(node, Name):
            return node.id
        if isinstance(node, Attribute):
            return node.attr
        if isinstance(node, Subscript):
            return self._expr_name(node=node.value)
        return unparse(ast_obj=node)

    def _add_usage(
        self,
        *,
        kind: AdvancedUsageKind,
        name: str,
        scope: AdvancedScopeRef,
        node: AST,
        detail: str,
    ) -> None:
        """Add one advanced usage record."""
        self._usages.append(
            AdvancedUsageRecord(
                kind=kind,
                name=name,
                scope=scope,
                node=node,
                detail=detail,
            ),
        )


class AdvancedSemanticParseUnparseToolkit(SemanticGraphParseUnparseToolkit):
    """Toolkit with graph plus advanced usage tracking."""

    def parse_advanced(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> AdvancedSemanticParseResult:
        """Parse source into semantic outputs."""
        graph_result: SemanticGraphParseResult = self.parse_graph(
            source=source,
            filename=filename,
        )
        advanced_model: AdvancedSemanticUsageModel = (
            AdvancedSemanticUsageAnalyzer().analyze(
                module=graph_result.model.parsed.module,
            )
        )
        return AdvancedSemanticParseResult(
            model=graph_result.model,
            graph=graph_result.graph,
            advanced=advanced_model,
        )


class AdvancedSemanticEditingCollector(SemanticGraphEditingCollector):
    """Editing collector with generic parameter and advanced usage helpers."""

    def __init__(
        self,
        *,
        existing_nodes: Iterable[ExistingTopNode] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> None:
        """Initialize the advanced editing collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            existing_type_aliases=existing_type_aliases,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        self.type_params: GenericTypeParameterEditor = (
            GenericTypeParameterEditor(
                resolver=self._resolver,
            )
        )
        self.type_prefixes: type[TypeHintPrefixFactory] = TypeHintPrefixFactory
        self.advanced: AdvancedSemanticUsageModel | None = None

    @classmethod
    def from_advanced_result(
        cls,
        *,
        result: AdvancedSemanticParseResult,
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
    ) -> AdvancedSemanticEditingCollector:
        """Create a collector from an advanced parse result."""
        type_alias_nodes: tuple[AstTypeAlias, ...] = tuple(
            item.node
            for item in result.model.type_aliases
            if isinstance(item.node, AstTypeAlias)
        )
        collector: AdvancedSemanticEditingCollector = cls(
            existing_nodes=(
                *result.model.context.import_nodes,
                *result.model.context.class_nodes,
            ),
            existing_type_aliases=type_alias_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
        )
        collector.attach_graph(graph=result.graph)
        collector.advanced = result.advanced
        return collector


class SemanticKeyedNode(ABC):
    """Common base for semantic objects that expose a stable key."""

    @abstractmethod
    def key(self) -> str:
        """Return a stable semantic key."""


@dataclass(slots=True, frozen=True)
class TypeExpressionPair(SemanticKeyedNode):
    """Pair of semantic type expressions used as algebra input."""

    left: TypeExpression
    right: TypeExpression

    def key(self) -> str:
        """Return a stable pair key."""
        return f"{self.left.key()}&{self.right.key()}"


class SemanticEvidenceContainer(ABC):
    """Common base for evidence containers that solve to type hints."""

    @property
    @abstractmethod
    def evidence(self) -> tuple[TypeInferenceEvidence, ...]:
        """Return contained type-inference evidence."""

    @abstractmethod
    def solve(self) -> TypeExpression:
        """Solve contained evidence into a semantic type expression."""

    def union_with(
        self,
        *,
        other: SemanticEvidenceContainer,
    ) -> UnionEvidenceSet:
        """Return a container representing possible values from both sets."""
        return UnionEvidenceSet(groups=(self, other))

    def intersect_with(
        self,
        *,
        other: SemanticEvidenceContainer,
    ) -> IntersectionEvidenceSet:
        """Return a container representing values allowed by both sets."""
        return IntersectionEvidenceSet(groups=(self, other))


@dataclass(slots=True, frozen=True)
class TypeEvidenceSet(SemanticEvidenceContainer):
    """Flat evidence set with sequential declaration/union/narrow solving."""

    items: tuple[TypeInferenceEvidence, ...]

    @property
    def evidence(self) -> tuple[TypeInferenceEvidence, ...]:
        """Return contained evidence items."""
        return self.items

    def solve(self) -> TypeExpression:
        """Solve evidence into a semantic type expression."""
        return TypeEvidenceSolver().solve(evidence=self.evidence)

    @classmethod
    def from_symbol(cls, *, symbol: SemanticSymbol) -> TypeEvidenceSet:
        """Create an evidence set from a graph symbol."""
        return cls(items=tuple(symbol.evidence))


@dataclass(slots=True, frozen=True)
class UnionEvidenceSet(SemanticEvidenceContainer):
    """Evidence set representing alternative possible values."""

    groups: tuple[SemanticEvidenceContainer, ...]

    @property
    def evidence(self) -> tuple[TypeInferenceEvidence, ...]:
        """Return flattened contained evidence."""
        items: list[TypeInferenceEvidence] = []
        for group in self.groups:
            items.extend(group.evidence)
        return tuple(items)

    def solve(self) -> TypeExpression:
        """Solve by unioning all group solutions."""
        solved: tuple[TypeExpression, ...] = tuple(
            group.solve() for group in self.groups
        )
        return TypeExpressionAlgebra().union(values=solved)


@dataclass(slots=True, frozen=True)
class IntersectionEvidenceSet(SemanticEvidenceContainer):
    """Evidence set representing values valid in all groups."""

    groups: tuple[SemanticEvidenceContainer, ...]

    @property
    def evidence(self) -> tuple[TypeInferenceEvidence, ...]:
        """Return flattened contained evidence."""
        items: list[TypeInferenceEvidence] = []
        for group in self.groups:
            items.extend(group.evidence)
        return tuple(items)

    def solve(self) -> TypeExpression:
        """Solve by intersecting all group solutions."""
        solved: tuple[TypeExpression, ...] = tuple(
            group.solve() for group in self.groups
        )
        return TypeExpressionAlgebra().intersect_all(values=solved)


class TypeExpressionInspector:
    """Shared introspection helpers for semantic type expressions."""

    def builtin_name(self, *, value: TypeExpression) -> str | None:
        """Return the builtin name for a builtin type expression."""
        if isinstance(value, BuiltinTypeRef):
            return value.name
        return None

    def origin_name(self, *, value: TypeExpression) -> str | None:
        """Return a readable origin name for a generic or direct reference."""
        if isinstance(value, BuiltinTypeRef):
            return value.name
        if isinstance(value, ImportedTypeRef):
            return value.source.imported_name
        if isinstance(value, GenericTypeRef):
            return self.origin_name(value=value.origin)
        return None

    def union_options(
        self,
        *,
        value: TypeExpression,
    ) -> tuple[TypeExpression, ...]:
        """Return flattened union options for a type expression."""
        if isinstance(value, UnionTypeRef):
            return value.options
        return (value,)

    def is_builtin(self, *, value: TypeExpression, name: str) -> bool:
        """Return whether a type expression is a specific builtin."""
        return self.builtin_name(value=value) == name

    def is_never(self, *, value: TypeExpression) -> bool:
        """Return whether a type expression is ``Never``."""
        return (
            isinstance(value, ImportedTypeRef)
            and value.source.imported_name == "Never"
        )

    def is_object(self, *, value: TypeExpression) -> bool:
        """Return whether a type expression is builtin ``object``."""
        return self.is_builtin(value=value, name="object")

    def numeric_rank(self, *, value: TypeExpression) -> int | None:
        """Return numeric tower rank for builtin numeric types."""
        name: str | None = self.builtin_name(value=value)
        if name is None:
            return None
        return UnionSimplificationTables.numeric_ranks.get(name)

    def numeric_type_for_rank(self, *, rank: int) -> TypeExpression:
        """Return the builtin numeric type expression for a rank."""
        for name, candidate in UnionSimplificationTables.numeric_ranks.items():
            if candidate == rank:
                return BuiltinTypeRef(name=name)
        fail(message="Invalid numeric rank for type-expression algebra.")

    def literal_covered_by_builtin(
        self,
        *,
        literal: LiteralTypeRef,
        builtin: BuiltinTypeRef,
    ) -> bool:
        """Return whether a builtin type covers all literal values."""
        for value in literal.values:
            if not self._literal_value_covered(value=value, builtin=builtin):
                return False
        return True

    def _literal_value_covered(
        self,
        *,
        value: LiteralValue,
        builtin: BuiltinTypeRef,
    ) -> bool:
        """Return whether one literal value is covered by a builtin."""
        if isinstance(value, bool):
            value_name: str = "bool"
        elif isinstance(value, int):
            value_name = "int"
        elif isinstance(value, float):
            value_name = "float"
        elif isinstance(value, str):
            value_name = "str"
        elif value is None:
            value_name = "None"
        else:
            return False
        return value_name == builtin.name


class TypeExpressionAlgebra:
    """Union and intersection algebra for semantic type expressions."""

    def __init__(self) -> None:
        """Initialize the algebra."""
        self._inspector: TypeExpressionInspector = TypeExpressionInspector()

    def union(
        self,
        *,
        values: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Return a normalized union of semantic type expressions."""
        if not values:
            return Types.object
        return Types.union(options=values, collapse_limit=collapse_limit)

    def intersect(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression:
        """Return the semantic intersection of two type expressions."""
        if left.key() == right.key():
            return left
        if self._inspector.is_never(value=left) or self._inspector.is_never(
            value=right,
        ):
            return Types.never
        if self._inspector.is_object(value=left):
            return right
        if self._inspector.is_object(value=right):
            return left
        return self._intersect_non_trivial(left=left, right=right)

    def intersect_all(
        self,
        *,
        values: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Return the intersection of all supplied type expressions."""
        if not values:
            return Types.object
        result: TypeExpression = values[0]
        for value in values[1:]:
            result = self.intersect(left=result, right=value)
        return result

    def _intersect_non_trivial(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression:
        """Intersect two non-identical and non-object expressions."""
        if isinstance(left, UnionTypeRef) or isinstance(right, UnionTypeRef):
            return self._intersect_union(left=left, right=right)
        literal_result: TypeExpression | None = self._literal_intersection(
            left=left,
            right=right,
        )
        if literal_result is not None:
            return literal_result
        numeric_result: TypeExpression | None = self._numeric_intersection(
            left=left,
            right=right,
        )
        if numeric_result is not None:
            return numeric_result
        generic_result: TypeExpression | None = self._generic_intersection(
            left=left,
            right=right,
        )
        if generic_result is not None:
            return generic_result
        return Types.never

    def _intersect_union(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression:
        """Intersect expressions when either side is a union."""
        results: list[TypeExpression] = []
        left_options: tuple[TypeExpression, ...] = (
            self._inspector.union_options(
                value=left,
            )
        )
        right_options: tuple[TypeExpression, ...] = (
            self._inspector.union_options(
                value=right,
            )
        )
        for left_option in left_options:
            for right_option in right_options:
                candidate: TypeExpression = self.intersect(
                    left=left_option,
                    right=right_option,
                )
                if not self._inspector.is_never(value=candidate):
                    results.append(candidate)
        if not results:
            return Types.never
        return self.union(values=tuple(results))

    def _literal_intersection(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression | None:
        """Return a literal-aware intersection when possible."""
        result: TypeExpression | None = None
        if isinstance(left, LiteralTypeRef) and isinstance(
            right,
            LiteralTypeRef,
        ):
            result = self._literal_literal_intersection(
                left=left,
                right=right,
            )
        elif isinstance(left, LiteralTypeRef) and isinstance(
            right,
            BuiltinTypeRef,
        ):
            result = self._literal_builtin_intersection(
                literal=left,
                builtin=right,
            )
        elif isinstance(right, LiteralTypeRef) and isinstance(
            left,
            BuiltinTypeRef,
        ):
            result = self._literal_builtin_intersection(
                literal=right,
                builtin=left,
            )
        return result

    def _literal_literal_intersection(
        self,
        *,
        left: LiteralTypeRef,
        right: LiteralTypeRef,
    ) -> TypeExpression:
        """Return the common values between two literal expressions."""
        values: tuple[LiteralValue, ...] = tuple(
            value for value in left.values if value in right.values
        )
        if values:
            return LiteralTypeRef(values=values)
        return Types.never

    def _literal_builtin_intersection(
        self,
        *,
        literal: LiteralTypeRef,
        builtin: BuiltinTypeRef,
    ) -> TypeExpression:
        """Return the intersection between literals and a builtin type."""
        if self._inspector.literal_covered_by_builtin(
            literal=literal,
            builtin=builtin,
        ):
            return literal
        return Types.never

    def _numeric_intersection(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression | None:
        """Return numeric tower intersection when both sides are numeric."""
        left_rank: int | None = self._inspector.numeric_rank(value=left)
        right_rank: int | None = self._inspector.numeric_rank(value=right)
        if left_rank is None or right_rank is None:
            return None
        return self._inspector.numeric_type_for_rank(
            rank=min(left_rank, right_rank),
        )

    def _generic_intersection(
        self,
        *,
        left: TypeExpression,
        right: TypeExpression,
    ) -> TypeExpression | None:
        """Return generic intersection for matching generic origins."""
        if not isinstance(left, GenericTypeRef) or not isinstance(
            right,
            GenericTypeRef,
        ):
            return None
        left_origin: str | None = self._inspector.origin_name(
            value=left.origin,
        )
        right_origin: str | None = self._inspector.origin_name(
            value=right.origin,
        )
        if left_origin != right_origin or len(left.arguments) != len(
            right.arguments,
        ):
            return None
        argument_results: tuple[TypeExpression, ...] = tuple(
            self.intersect(left=left_arg, right=right_arg)
            for left_arg, right_arg in zip(
                left.arguments,
                right.arguments,
                strict=True,
            )
        )
        if any(
            self._inspector.is_never(value=item) for item in argument_results
        ):
            return Types.never
        return GenericTypeRef(origin=left.origin, arguments=argument_results)


class EvidenceClassifier:
    """Categorise raw type evidence into declaration, union or narrowing.

    During analysis the farm collects many pieces of evidence for each
    program element.  These pieces fall into three broad categories:
    * **Declarations**: explicit annotations on variables or function
      signatures that should override any derived types.
    * **Narrowings**: boolean comparisons to literals (e.g.,
      ``x == 0``) that restrict the set of possible values for a
      variable.
    * **Unions**: assignment targets, return values, constant literals and
      other observations that contribute to the set of candidate types
      without fixing a single choice.

    The classifier returns a :class:`EvidenceContribution` indicating
    how each evidence instance should influence the evolving type
    belief.  Evidence kinds not listed in any category are ignored.
    Extend the class-level frozensets to support additional evidence
    kinds as the inferencer becomes more sophisticated.
    """

    def classify(
        self,
        *,
        evidence: TypeInferenceEvidence,
    ) -> EvidenceContribution:
        """Classify one evidence item."""
        contribution: EvidenceContributionKind = (
            EvidenceContributionKind.IGNORED
        )
        if evidence.kind in EvidenceKindTables.declaration_kinds:
            contribution = EvidenceContributionKind.DECLARES
        elif evidence.kind in EvidenceKindTables.narrowing_kinds:
            contribution = EvidenceContributionKind.NARROWS
        elif evidence.kind in EvidenceKindTables.union_kinds:
            contribution = EvidenceContributionKind.SUPPORTS_UNION
        return EvidenceContribution(
            evidence=evidence,
            contribution=contribution,
        )


class TypeEvidenceSolver:
    """Solve evidence using union and narrowing intersection semantics."""

    def __init__(self) -> None:
        """Initialize the evidence solver."""
        self._classifier: EvidenceClassifier = EvidenceClassifier()
        self._algebra: TypeExpressionAlgebra = TypeExpressionAlgebra()

    def solve(
        self,
        *,
        evidence: tuple[TypeInferenceEvidence, ...],
    ) -> TypeExpression:
        """Solve evidence into one normalized semantic type expression."""
        if not evidence:
            return Types.object
        contributions: tuple[EvidenceContribution, ...] = tuple(
            self._classifier.classify(evidence=item) for item in evidence
        )
        declared: tuple[TypeExpression, ...] = self._types_for(
            contributions=contributions,
            kind=EvidenceContributionKind.DECLARES,
        )
        unioned: tuple[TypeExpression, ...] = self._types_for(
            contributions=contributions,
            kind=EvidenceContributionKind.SUPPORTS_UNION,
        )
        narrowed: tuple[TypeExpression, ...] = self._types_for(
            contributions=contributions,
            kind=EvidenceContributionKind.NARROWS,
        )
        result: TypeExpression = self._base_type(
            declared=declared,
            unioned=unioned,
        )
        for narrowed_type in narrowed:
            result = self._algebra.intersect(
                left=result,
                right=narrowed_type,
            )
        return result

    def solve_union(
        self,
        *,
        evidence_sets: tuple[SemanticEvidenceContainer, ...],
    ) -> TypeExpression:
        """Solve multiple evidence sets as alternatives."""
        return UnionEvidenceSet(groups=evidence_sets).solve()

    def solve_intersection(
        self,
        *,
        evidence_sets: tuple[SemanticEvidenceContainer, ...],
    ) -> TypeExpression:
        """Solve multiple evidence sets as simultaneous constraints."""
        return IntersectionEvidenceSet(groups=evidence_sets).solve()

    def _types_for(
        self,
        *,
        contributions: tuple[EvidenceContribution, ...],
        kind: EvidenceContributionKind,
    ) -> tuple[TypeExpression, ...]:
        """Return type hints for a contribution kind."""
        return tuple(
            contribution.type_hint
            for contribution in contributions
            if contribution.contribution is kind
        )

    def _base_type(
        self,
        *,
        declared: tuple[TypeExpression, ...],
        unioned: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Build the base type before narrowing evidence is applied."""
        declared_type: TypeExpression | None = None
        union_type: TypeExpression | None = None
        if declared:
            declared_type = self._algebra.intersect_all(
                values=declared,
            )
        if unioned:
            union_type = self._algebra.union(values=unioned)
        if declared_type is None and union_type is None:
            return Types.object
        if declared_type is None:
            return union_type or Types.object
        if union_type is None:
            return declared_type
        return self._algebra.intersect(left=declared_type, right=union_type)


class EvidenceAlgebraFacade:
    """Convenience API for solving and combining evidence containers."""

    def __init__(self) -> None:
        """Initialize the facade."""
        self._solver: TypeEvidenceSolver = TypeEvidenceSolver()
        self._algebra: TypeExpressionAlgebra = TypeExpressionAlgebra()

    def set_from_symbol(self, *, symbol: SemanticSymbol) -> TypeEvidenceSet:
        """Return an evidence set for one graph symbol."""
        return TypeEvidenceSet.from_symbol(symbol=symbol)

    def union(
        self,
        *,
        left: SemanticEvidenceContainer,
        right: SemanticEvidenceContainer,
    ) -> TypeExpression:
        """Solve two evidence containers as alternative value sources."""
        return self._solver.solve_union(evidence_sets=(left, right))

    def intersection(
        self,
        *,
        left: SemanticEvidenceContainer,
        right: SemanticEvidenceContainer,
    ) -> TypeExpression:
        """Solve two evidence containers as simultaneous constraints."""
        return self._solver.solve_intersection(evidence_sets=(left, right))

    def union_types(
        self,
        *,
        values: tuple[TypeExpression, ...],
        collapse_limit: int | None = None,
    ) -> TypeExpression:
        """Return the normalized union of type expressions."""
        return self._algebra.union(
            values=values,
            collapse_limit=collapse_limit,
        )

    def intersect_types(
        self,
        *,
        values: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Return the normalized intersection of type expressions."""
        return self._algebra.intersect_all(values=values)


class AlgebraicSemanticGraphTypeSynthesizer(SemanticGraphTypeSynthesizer):
    """Graph synthesizer variant that uses evidence algebra."""

    def __init__(self, *, graph: SemanticAstGraph) -> None:
        """Initialize the graph synthesizer."""
        super().__init__(graph=graph)
        self.evidence: EvidenceAlgebraFacade = EvidenceAlgebraFacade()

    def inferred_symbol_type(self, *, name: str) -> TypeExpression | None:
        """Infer a symbol type with union/intersection evidence algebra."""
        evidence_items: list[TypeInferenceEvidence] = []
        for symbol in self._graph.symbols_named(name=name):
            evidence_items.extend(symbol.evidence)
        if not evidence_items:
            return None
        return TypeEvidenceSolver().solve(evidence=tuple(evidence_items))


class IndexedSemanticAstGraph:
    """High-performance semantic graph with indexed adjacency lists.

    This graph keeps the public semantics of ``SemanticAstGraph`` but uses
    integer identifiers and direct indexes for hot operations. Lookups such as
    ``children_of``, ``outgoing``, ``incoming``, ``nodes_named``, and
    ``symbols_named`` avoid full graph scans.
    """

    def __init__(self) -> None:
        """Initialize graph storage and indexes."""
        self.nodes: list[IndexedSemanticGraphNode] = []
        self.edges: list[IndexedSemanticGraphEdge] = []
        self.scopes: list[IndexedSemanticScope] = []
        self.symbols: list[IndexedSemanticSymbol] = []
        self._node_ids_by_ast_id: dict[int, IndexedNodeId] = {}
        self._children_by_node: dict[IndexedNodeId, list[IndexedNodeId]] = {}
        self._parent_by_node: dict[IndexedNodeId, IndexedNodeId] = {}
        self._out_edges_by_node: dict[IndexedNodeId, list[IndexedEdgeId]] = {}
        self._in_edges_by_node: dict[IndexedNodeId, list[IndexedEdgeId]] = {}
        self._edges_by_kind: dict[SemanticEdgeKind, list[IndexedEdgeId]] = {}
        self._nodes_by_kind: dict[SemanticNodeKind, list[IndexedNodeId]] = {}
        self._nodes_by_name: dict[str, list[IndexedNodeId]] = {}
        self._symbols_by_name: dict[str, list[IndexedSymbolId]] = {}
        self.root_node_id: IndexedNodeId | None | int = None
        self.root_scope_id: IndexedScopeId | None | int = None
        self.version: int = 0

    def add_scope(
        self,
        *,
        kind: SemanticScopeKind,
        name: str,
        node_id: IndexedNodeId,
        parent_id: IndexedScopeId | None,
    ) -> IndexedScopeId:
        """Add a scope and return its integer identifier."""
        scope_id: IndexedScopeId = len(self.scopes)
        self.scopes.append(
            IndexedSemanticScope(
                id=scope_id,
                kind=kind,
                name=name,
                node_id=node_id,
                parent_id=parent_id,
            ),
        )
        if self.root_scope_id is None:
            self.root_scope_id = scope_id
        self._mark_changed()
        return scope_id

    def add_node(self, *, data: IndexedNodeCreate) -> IndexedNodeId:
        """Add a node and update all node indexes."""
        node_id: IndexedNodeId = len(self.nodes)
        node: IndexedSemanticGraphNode = IndexedSemanticGraphNode(
            id=node_id,
            ast_node=data.ast_node,
            kind=data.kind,
            scope_id=data.scope_id,
            parent_id=data.parent_id,
            name=data.name,
            role=data.role,
        )
        self.nodes.append(node)
        self._node_ids_by_ast_id[id(data.ast_node)] = node_id
        self._nodes_by_kind.setdefault(data.kind, []).append(node_id)
        if data.name is not None:
            self._nodes_by_name.setdefault(data.name, []).append(node_id)
        self._children_by_node.setdefault(node_id, [])
        if data.parent_id is not None:
            self._parent_by_node[node_id] = data.parent_id
            self._children_by_node.setdefault(data.parent_id, []).append(
                node_id,
            )
        if self.root_node_id is None:
            self.root_node_id = node_id
        self._mark_changed()
        return node_id

    def add_edge(
        self,
        *,
        source_id: IndexedNodeId,
        target_id: IndexedNodeId,
        kind: SemanticEdgeKind,
        label: str | None = None,
    ) -> IndexedEdgeId:
        """Add an edge and update all edge indexes."""
        edge_id: IndexedEdgeId = len(self.edges)
        edge: IndexedSemanticGraphEdge = IndexedSemanticGraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            kind=kind,
            label=label,
        )
        self.edges.append(edge)
        self._out_edges_by_node.setdefault(source_id, []).append(edge_id)
        self._in_edges_by_node.setdefault(target_id, []).append(edge_id)
        self._edges_by_kind.setdefault(kind, []).append(edge_id)
        self._mark_changed()
        return edge_id

    def add_symbol(
        self,
        *,
        name: str,
        kind: SemanticSymbolKind,
        scope_id: IndexedScopeId,
        definition_node_id: IndexedNodeId | None,
    ) -> IndexedSymbolId:
        """Add a symbol and register it in the lexical scope."""
        existing_id: IndexedSymbolId | None = self._existing_symbol_id(
            name=name,
            scope_id=scope_id,
        )
        if existing_id is not None:
            return existing_id
        symbol_id: IndexedSymbolId = len(self.symbols)
        symbol: IndexedSemanticSymbol = IndexedSemanticSymbol(
            id=symbol_id,
            name=name,
            kind=kind,
            scope_id=scope_id,
            definition_node_id=definition_node_id,
        )
        self.symbols.append(symbol)
        self._symbols_by_name.setdefault(name, []).append(symbol_id)
        self.scopes[scope_id].define(name=name, symbol_id=symbol_id)
        self._mark_changed()
        return symbol_id

    def replace_ast_node(
        self,
        *,
        node_id: IndexedNodeId,
        ast_node: AST,
    ) -> None:
        """Replace an AST node while preserving graph identity."""
        old_node: IndexedSemanticGraphNode = self.nodes[node_id]
        self._node_ids_by_ast_id.pop(id(old_node.ast_node), None)
        self.nodes[node_id] = IndexedSemanticGraphNode(
            id=old_node.id,
            ast_node=ast_node,
            kind=old_node.kind,
            scope_id=old_node.scope_id,
            parent_id=old_node.parent_id,
            name=old_node.name,
            role=old_node.role,
        )
        self._node_ids_by_ast_id[id(ast_node)] = node_id
        self._mark_changed()

    def node(self, *, node_id: IndexedNodeId) -> IndexedSemanticGraphNode:
        """Return a node record by id."""
        return self.nodes[node_id]

    def edge(self, *, edge_id: IndexedEdgeId) -> IndexedSemanticGraphEdge:
        """Return an edge record by id."""
        return self.edges[edge_id]

    def scope(self, *, scope_id: IndexedScopeId) -> IndexedSemanticScope:
        """Return a scope record by id."""
        return self.scopes[scope_id]

    def symbol(self, *, symbol_id: IndexedSymbolId) -> IndexedSemanticSymbol:
        """Return a symbol record by id."""
        return self.symbols[symbol_id]

    def node_id_for_ast(self, *, node: AST) -> IndexedNodeId | None:
        """Return the indexed node id for an AST node."""
        return self._node_ids_by_ast_id.get(id(node))

    def view_for_ast(self, *, node: AST) -> IndexedNodeView | None:
        """Return a node view for an AST node."""
        node_id: IndexedNodeId | None = self.node_id_for_ast(node=node)
        if node_id is None:
            return None
        return self.view(node_id=node_id)

    def view(self, *, node_id: IndexedNodeId) -> IndexedNodeView:
        """Return a navigable view for a node id."""
        return IndexedNodeView(graph=self, node_id=node_id)

    def root(self) -> IndexedNodeView | None:
        """Return the root view if present."""
        if self.root_node_id is None:
            return None
        return self.view(node_id=self.root_node_id)

    def children_ids(
        self,
        *,
        node_id: IndexedNodeId,
    ) -> tuple[IndexedNodeId, ...]:
        """Return child node ids without scanning all nodes."""
        return tuple(self._children_by_node.get(node_id, []))

    def parent_id(self, *, node_id: IndexedNodeId) -> IndexedNodeId | None:
        """Return the parent node id."""
        return self._parent_by_node.get(node_id)

    def outgoing_edge_ids(
        self,
        *,
        node_id: IndexedNodeId,
        kind: SemanticEdgeKind | None = None,
    ) -> tuple[IndexedEdgeId, ...]:
        """Return outgoing edge ids for a node."""
        edge_ids: tuple[IndexedEdgeId, ...] = tuple(
            self._out_edges_by_node.get(node_id, []),
        )
        if kind is None:
            return edge_ids
        return tuple(
            edge_id for edge_id in edge_ids if self.edges[edge_id].kind == kind
        )

    def incoming_edge_ids(
        self,
        *,
        node_id: IndexedNodeId,
        kind: SemanticEdgeKind | None = None,
    ) -> tuple[IndexedEdgeId, ...]:
        """Return incoming edge ids for a node."""
        edge_ids: tuple[IndexedEdgeId, ...] = tuple(
            self._in_edges_by_node.get(node_id, []),
        )
        if kind is None:
            return edge_ids
        return tuple(
            edge_id for edge_id in edge_ids if self.edges[edge_id].kind == kind
        )

    def edge_ids_by_kind(
        self,
        *,
        kind: SemanticEdgeKind,
    ) -> tuple[IndexedEdgeId, ...]:
        """Return all edge ids for a semantic edge kind."""
        return tuple(self._edges_by_kind.get(kind, []))

    def node_ids_by_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[IndexedNodeId, ...]:
        """Return all node ids for a semantic node kind."""
        return tuple(self._nodes_by_kind.get(kind, []))

    def node_ids_named(self, *, name: str) -> tuple[IndexedNodeId, ...]:
        """Return all node ids with a semantic name."""
        return tuple(self._nodes_by_name.get(name, []))

    def symbols_named(self, *, name: str) -> tuple[IndexedSemanticSymbol, ...]:
        """Return all symbols with a given name."""
        return tuple(
            self.symbol(symbol_id=item)
            for item in self._symbols_by_name.get(name, [])
        )

    def lookup_symbol(
        self,
        *,
        name: str,
        scope_id: IndexedScopeId,
    ) -> IndexedSemanticSymbol | None:
        """Resolve a symbol by walking lexical parent scopes."""
        current_id: IndexedScopeId | None | int = scope_id
        while current_id is not None:
            scope: IndexedSemanticScope = self.scope(scope_id=current_id)
            symbol_id: IndexedSymbolId | None = scope.symbols.get(name)
            if symbol_id is not None:
                return self.symbol(symbol_id=symbol_id)
            current_id = scope.parent_id
        return None

    def views_by_kind(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> tuple[IndexedNodeView, ...]:
        """Return node views for a semantic kind."""
        return tuple(
            self.view(node_id=item)
            for item in self.node_ids_by_kind(kind=kind)
        )

    def views_named(self, *, name: str) -> tuple[IndexedNodeView, ...]:
        """Return node views for a semantic name."""
        return tuple(
            self.view(node_id=item) for item in self.node_ids_named(name=name)
        )

    def functions(self) -> tuple[IndexedNodeView, ...]:
        """Return function and method views."""
        return self.views_by_kind(kind=SemanticNodeKind.FUNCTION)

    def classes(self) -> tuple[IndexedNodeView, ...]:
        """Return class views."""
        return self.views_by_kind(kind=SemanticNodeKind.CLASS)

    def value_usage(self, *, name: str) -> tuple[IndexedValueUsage, ...]:
        """Return indexed value usage summaries for all matching symbols."""
        result: list[IndexedValueUsage] = []
        for symbol in self.symbols_named(name=name):
            definitions: tuple[IndexedNodeView, ...]
            if symbol.definition_node_id is None:
                definitions = ()
            else:
                definitions = (self.view(node_id=symbol.definition_node_id),)
            usages: tuple[IndexedNodeView, ...] = tuple(
                self.view(node_id=item) for item in symbol.usage_node_ids
            )
            result.append(
                IndexedValueUsage(
                    symbol=symbol,
                    definitions=definitions,
                    usages=usages,
                    evidence=tuple(symbol.evidence),
                ),
            )
        return tuple(result)

    def _existing_symbol_id(
        self,
        *,
        name: str,
        scope_id: IndexedScopeId,
    ) -> IndexedSymbolId | None:
        """Return a symbol id already defined in one exact scope."""
        return self.scopes[scope_id].symbols.get(name)

    def _mark_changed(self) -> None:
        """Increment the mutation version used by cached query objects."""
        self.version += 1


class IndexedLiteralTypeInferencer:
    """Fast literal/container type inferencer independent of graph walks."""

    def infer(self, *, node: AST) -> TypeExpression | None:
        """Infer a conservative type expression for one AST node."""
        if isinstance(node, Constant):
            return self._constant(node=node)
        if isinstance(node, AstList):
            return self._list(node=node)
        if isinstance(node, AstTuple):
            return self._tuple(node=node)
        if isinstance(node, AstSet):
            return self._set(node=node)
        if isinstance(node, AstDict):
            return self._dict(node=node)
        return None

    def _constant(self, *, node: Constant) -> TypeExpression:
        """Infer a type from an AST constant."""
        value_type: TypeExpression | BuiltinTypeRef | EllipsisTypeRef = (
            Types.object
        )
        if node.value is None:
            value_type = Types.none
        elif node.value is Ellipsis:
            value_type = Types.ellipsis
        elif isinstance(node.value, bool):
            value_type = Types.bool
        elif isinstance(node.value, int):
            value_type = Types.int
        elif isinstance(node.value, float):
            value_type = Types.float
        elif isinstance(node.value, complex):
            value_type = Types.complex
        elif isinstance(node.value, str):
            value_type = Types.str
        elif isinstance(node.value, bytes):
            value_type = Types.bytes
        return value_type

    def _list(self, *, node: AstList) -> TypeExpression:
        """Infer a type from a list literal."""
        item_type: TypeExpression = self._merge(nodes=tuple(node.elts))
        return Types.builtins.list_of(item=item_type)

    def _tuple(self, *, node: AstTuple) -> TypeExpression:
        """Infer a type from a tuple literal."""
        if not node.elts:
            return Types.builtins.tuple_empty()
        return Types.builtins.tuple_of(
            items=tuple(
                self.infer(node=item) or Types.object for item in node.elts
            ),
        )

    def _set(self, *, node: AstSet) -> TypeExpression:
        """Infer a type from a set literal."""
        item_type: TypeExpression = self._merge(nodes=tuple(node.elts))
        return Types.builtins.set_of(item=item_type)

    def _dict(self, *, node: AstDict) -> TypeExpression:
        """Infer a type from a dict literal."""
        keys: tuple[expr, ...] = tuple(
            item for item in node.keys if item is not None
        )
        key_type: TypeExpression = self._merge(nodes=keys)
        value_type: TypeExpression = self._merge(nodes=tuple(node.values))
        return Types.builtins.dict_of(keys=key_type, values=value_type)

    def _merge(self, *, nodes: tuple[expr, ...]) -> TypeExpression:
        """Merge type expressions from expression nodes."""
        values: tuple[TypeExpression, ...] = tuple(
            value
            for value in (self.infer(node=node) for node in nodes)
            if value is not None
        )
        if not values:
            return Types.object
        return EvidenceAlgebraFacade().union_types(values=values)


class IndexedGraphScopeStack:
    """Mutable scope stack used while building an indexed graph."""

    def __init__(self, *, graph: IndexedSemanticAstGraph) -> None:
        """Initialize the stack."""
        self._graph: IndexedSemanticAstGraph = graph
        self._items: list[IndexedScopeId] = []

    @property
    def current(self) -> IndexedScopeId:
        """Return the current scope id."""
        if not self._items:
            msg: str = "Scope stack is empty."
            fail(message=msg)
        return self._items[-1]

    def push(
        self,
        *,
        kind: SemanticScopeKind,
        name: str,
        node_id: IndexedNodeId,
    ) -> IndexedScopeId:
        """Create and push a child scope."""
        parent_id: IndexedScopeId | None = (
            self._items[-1] if self._items else None
        )
        scope_id: IndexedScopeId = self._graph.add_scope(
            kind=kind,
            name=name,
            node_id=node_id,
            parent_id=parent_id,
        )
        self._items.append(scope_id)
        return scope_id

    def pop(self) -> None:
        """Pop the current scope."""
        if not self._items:
            msg: str = "Cannot pop an empty scope stack."
            fail(message=msg)
        self._items.pop()


class IndexedSemanticGraphBuilder:
    """Build an indexed semantic graph from Python AST nodes."""

    def __init__(self) -> None:
        """Initialize graph-builder helpers."""
        self._graph: IndexedSemanticAstGraph = IndexedSemanticAstGraph()
        self._scopes: IndexedGraphScopeStack = IndexedGraphScopeStack(
            graph=self._graph,
        )
        self._inferencer: IndexedLiteralTypeInferencer = (
            IndexedLiteralTypeInferencer()
        )

    def build(self, *, root: AST) -> IndexedSemanticAstGraph:
        """Build and return an indexed semantic graph."""
        self._walk(node=root, parent_id=None)
        return self._graph

    def _walk(
        self,
        *,
        node: AST,
        parent_id: IndexedNodeId | None,
    ) -> IndexedNodeId:
        """Walk one AST node and its children."""
        kind: SemanticNodeKind = self._kind_for(node=node)
        name: str | None = self._name_for(node=node)
        scope_id: IndexedScopeId = self._scope_for_new_node(
            parent_id=parent_id,
        )
        node_id: IndexedNodeId = self._graph.add_node(
            data=IndexedNodeCreate(
                ast_node=node,
                kind=kind,
                scope_id=scope_id,
                parent_id=parent_id,
                name=name,
                role=self._role_for(node=node),
            ),
        )
        pushed_scope: bool = self._maybe_push_scope(
            node=node,
            kind=kind,
            node_id=node_id,
            name=name,
        )
        self._define_named_scope_symbol(node=node, node_id=node_id, name=name)
        for child in iter_child_nodes(node=node):
            child_id: IndexedNodeId = self._walk(node=child, parent_id=node_id)
            self._graph.add_edge(
                source_id=node_id,
                target_id=child_id,
                kind=SemanticEdgeKind.CHILD,
            )
        self._add_late_semantics(node=node, node_id=node_id)
        if pushed_scope:
            self._scopes.pop()
        return node_id

    def _scope_for_new_node(
        self,
        *,
        parent_id: IndexedNodeId | None,
    ) -> IndexedScopeId:
        """Return scope id for a node before optional scope push."""
        if parent_id is None:
            return 0
        return self._scopes.current

    def _maybe_push_scope(
        self,
        *,
        node: AST,
        kind: SemanticNodeKind,
        node_id: IndexedNodeId,
        name: str | None,
    ) -> bool:
        """Push a lexical scope when the node introduces one."""
        scope_kind: SemanticScopeKind | None = self._scope_kind_for(kind=kind)
        if scope_kind is None:
            return False
        scope_name: str = name or "<module>"
        scope_id: IndexedScopeId = self._scopes.push(
            kind=scope_kind,
            name=scope_name,
            node_id=node_id,
        )
        self._patch_node_scope(node_id=node_id, scope_id=scope_id)
        self._define_arguments(node=node, scope_id=scope_id)
        return True

    def _patch_node_scope(
        self,
        *,
        node_id: IndexedNodeId,
        scope_id: IndexedScopeId,
    ) -> None:
        """Patch a just-created scope owner with its own scope id."""
        old_node: IndexedSemanticGraphNode = self._graph.node(node_id=node_id)
        self._graph.nodes[node_id] = IndexedSemanticGraphNode(
            id=old_node.id,
            ast_node=old_node.ast_node,
            kind=old_node.kind,
            scope_id=scope_id,
            parent_id=old_node.parent_id,
            name=old_node.name,
            role=old_node.role,
        )

    def _define_arguments(
        self,
        *,
        node: AST,
        scope_id: IndexedScopeId,
    ) -> None:
        """Define function arguments in a function scope."""
        if not isinstance(node, FunctionDef | AsyncFunctionDef):
            return
        argument_nodes: tuple[arg, ...] = self._all_argument_nodes(node=node)
        for argument in argument_nodes:
            argument_node_id: IndexedNodeId | None = (
                self._graph.node_id_for_ast(
                    node=argument,
                )
            )
            self._graph.add_symbol(
                name=argument.arg,
                kind=SemanticSymbolKind.ARGUMENT,
                scope_id=scope_id,
                definition_node_id=argument_node_id,
            )

    def _define_named_scope_symbol(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
        name: str | None,
    ) -> None:
        """Define class/function symbols in the enclosing scope."""
        if name is None:
            return
        symbol_kind: SemanticSymbolKind | None = self._symbol_kind_for(
            node=node,
        )
        if symbol_kind is None:
            return
        scope_id: IndexedScopeId = self._enclosing_scope_id(node_id=node_id)
        self._graph.add_symbol(
            name=name,
            kind=symbol_kind,
            scope_id=scope_id,
            definition_node_id=node_id,
        )

    def _enclosing_scope_id(self, *, node_id: IndexedNodeId) -> IndexedScopeId:
        """Return the lexical scope that encloses a node."""
        node: IndexedSemanticGraphNode = self._graph.node(node_id=node_id)
        parent_id: IndexedNodeId | None = node.parent_id
        if parent_id is None:
            return node.scope_id
        return self._graph.node(node_id=parent_id).scope_id

    def _add_late_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Add edges and evidence that require child ids to exist."""
        self._add_name_semantics(node=node, node_id=node_id)
        self._add_assignment_semantics(node=node)
        self._add_return_semantics(node=node, node_id=node_id)
        self._add_call_semantics(node=node, node_id=node_id)
        self._add_attribute_semantics(node=node, node_id=node_id)
        self._add_comparison_semantics(node=node, node_id=node_id)

    def _add_name_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Record name loads and stores."""
        if not isinstance(node, Name):
            return
        if isinstance(node.ctx, Store):
            self._define_or_use_name(node=node, node_id=node_id, store=True)
        elif isinstance(node.ctx, Load):
            self._define_or_use_name(node=node, node_id=node_id, store=False)

    def _define_or_use_name(
        self,
        *,
        node: Name,
        node_id: IndexedNodeId,
        store: bool,
    ) -> None:
        """Record one name definition or usage."""
        symbol: IndexedSemanticSymbol | None = self._graph.lookup_symbol(
            name=node.id,
            scope_id=self._graph.node(node_id=node_id).scope_id,
        )
        if symbol is None and store:
            symbol_id: IndexedSymbolId = self._graph.add_symbol(
                name=node.id,
                kind=SemanticSymbolKind.VARIABLE,
                scope_id=self._graph.node(node_id=node_id).scope_id,
                definition_node_id=node_id,
            )
            symbol = self._graph.symbol(
                symbol_id=symbol_id,
            )
        if symbol is not None and not store:
            symbol.add_usage(node_id=node_id)

    def _add_assignment_semantics(self, *, node: AST) -> None:
        """Record assignment value edges and type evidence."""
        if not isinstance(node, Assign | AnnAssign):
            return
        value_node: expr | None = self._assignment_value(node=node)
        if value_node is None:
            return
        value_id: IndexedNodeId | None = self._graph.node_id_for_ast(
            node=value_node,
        )
        if value_id is None:
            return
        for target in self._assignment_targets(node=node):
            target_id: IndexedNodeId | None = self._graph.node_id_for_ast(
                node=target,
            )
            if target_id is not None:
                self._graph.add_edge(
                    source_id=target_id,
                    target_id=value_id,
                    kind=SemanticEdgeKind.ASSIGNS_VALUE,
                )
                self._add_assignment_evidence(
                    target=target,
                    value=value_node,
                    node_id=target_id,
                )

    def _add_assignment_evidence(
        self,
        *,
        target: expr,
        value: expr,
        node_id: IndexedNodeId,
    ) -> None:
        """Attach inferred assignment evidence to a target symbol."""
        if not isinstance(target, Name):
            return
        value_type: TypeExpression | None = self._inferencer.infer(node=value)
        if value_type is None:
            return
        symbol: IndexedSemanticSymbol | None = self._graph.lookup_symbol(
            name=target.id,
            scope_id=self._graph.node(node_id=node_id).scope_id,
        )
        if symbol is None:
            return
        symbol.add_evidence(
            evidence=TypeInferenceEvidence(
                kind=TypeEvidenceKind.ASSIGNMENT_VALUE,
                type_hint=value_type,
                node_id=f"indexed:{node_id}",
                confidence=0.75,
                reason="Indexed assignment literal evidence.",
            ),
        )

    def _add_return_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Record return value edges."""
        if not isinstance(node, Return) or node.value is None:
            return
        value_id: IndexedNodeId | None = self._graph.node_id_for_ast(
            node=node.value,
        )
        if value_id is None:
            return
        self._graph.add_edge(
            source_id=node_id,
            target_id=value_id,
            kind=SemanticEdgeKind.RETURNS_VALUE,
        )

    def _add_call_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Record call-target and call-argument edges."""
        if not isinstance(node, Call):
            return
        function_id: IndexedNodeId | None = self._graph.node_id_for_ast(
            node=node.func,
        )
        if function_id is not None:
            self._graph.add_edge(
                source_id=node_id,
                target_id=function_id,
                kind=SemanticEdgeKind.CALLS,
                label="target",
            )
        for argument in node.args:
            argument_id: IndexedNodeId | None = self._graph.node_id_for_ast(
                node=argument,
            )
            if argument_id is not None:
                self._graph.add_edge(
                    source_id=node_id,
                    target_id=argument_id,
                    kind=SemanticEdgeKind.USES,
                    label="argument",
                )

    def _add_attribute_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Record attribute read/write edges."""
        if not isinstance(node, Attribute):
            return
        value_id: IndexedNodeId | None = self._graph.node_id_for_ast(
            node=node.value,
        )
        if value_id is None:
            return
        edge_kind: SemanticEdgeKind = SemanticEdgeKind.READS_ATTRIBUTE
        if isinstance(node.ctx, Store):
            edge_kind = SemanticEdgeKind.WRITES_ATTRIBUTE
        self._graph.add_edge(
            source_id=node_id,
            target_id=value_id,
            kind=edge_kind,
            label=node.attr,
        )

    def _add_comparison_semantics(
        self,
        *,
        node: AST,
        node_id: IndexedNodeId,
    ) -> None:
        """Record comparison operand edges."""
        if not isinstance(node, Compare):
            return
        left_id: IndexedNodeId | None = self._graph.node_id_for_ast(
            node=node.left,
        )
        if left_id is not None:
            self._graph.add_edge(
                source_id=node_id,
                target_id=left_id,
                kind=SemanticEdgeKind.COMPARES_WITH,
                label="left",
            )
        for comparator in node.comparators:
            right_id: IndexedNodeId | None = self._graph.node_id_for_ast(
                node=comparator,
            )
            if right_id is not None:
                self._graph.add_edge(
                    source_id=node_id,
                    target_id=right_id,
                    kind=SemanticEdgeKind.COMPARES_WITH,
                    label="right",
                )

    def _kind_for(self, *, node: AST) -> SemanticNodeKind:
        """Return the semantic node kind for an AST node."""
        for rule in SemanticNodeKindTables.kind_rules:
            if isinstance(node, rule.node_types):
                return rule.kind
        return SemanticNodeKind.UNKNOWN

    def _name_for(self, *, node: AST) -> str | None:
        """Return a semantic name for named AST nodes."""
        result: str | None = None
        if isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef):
            result = node.name
        elif isinstance(node, Name):
            result = node.id
        elif isinstance(node, Attribute):
            result = node.attr
        elif isinstance(node, arg):
            result = node.arg
        return result

    def _role_for(self, *, node: AST) -> SemanticUsageKind | None:
        """Return a usage role for name and attribute nodes."""
        result: SemanticUsageKind | None = None
        if isinstance(node, Name | Attribute):
            if isinstance(node.ctx, Store):
                result = SemanticUsageKind.STORE
            elif isinstance(node.ctx, Load):
                result = SemanticUsageKind.LOAD
        return result

    def _scope_kind_for(
        self,
        *,
        kind: SemanticNodeKind,
    ) -> SemanticScopeKind | None:
        """Return a scope kind for a node kind."""
        result: SemanticScopeKind | None = None
        if kind == SemanticNodeKind.MODULE:
            result = SemanticScopeKind.MODULE
        elif kind == SemanticNodeKind.CLASS:
            result = SemanticScopeKind.CLASS
        elif kind == SemanticNodeKind.FUNCTION:
            result = SemanticScopeKind.FUNCTION
        return result

    def _symbol_kind_for(self, *, node: AST) -> SemanticSymbolKind | None:
        """Return a symbol kind for a named AST node."""
        result: SemanticSymbolKind | None = None
        if isinstance(node, ClassDef):
            result = SemanticSymbolKind.CLASS
        elif isinstance(node, FunctionDef | AsyncFunctionDef):
            result = SemanticSymbolKind.FUNCTION
        return result

    def _all_argument_nodes(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
    ) -> tuple[arg, ...]:
        """Return all argument nodes for a function."""
        items: list[arg] = []
        items.extend(node.args.posonlyargs)
        items.extend(node.args.args)
        if node.args.vararg is not None:
            items.append(node.args.vararg)
        items.extend(node.args.kwonlyargs)
        if node.args.kwarg is not None:
            items.append(node.args.kwarg)
        return tuple(items)

    def _assignment_targets(
        self,
        *,
        node: Assign | AnnAssign,
    ) -> tuple[expr, ...]:
        """Return assignment target expressions."""
        if isinstance(node, Assign):
            return tuple(node.targets)
        return (node.target,)

    def _assignment_value(self, *, node: Assign | AnnAssign) -> expr | None:
        """Return assignment value if available."""
        if isinstance(node, Assign):
            return node.value
        return node.value


class IndexedGraphQueryCache:
    """Small version-aware cache for indexed graph queries."""

    def __init__(self, *, graph: IndexedSemanticAstGraph) -> None:
        """Initialize the cache."""
        self._graph: IndexedSemanticAstGraph = graph
        self._version: int = graph.version
        self._class_methods: dict[
            tuple[str, str],
            tuple[IndexedNodeView, ...],
        ] = {}

    def class_methods(
        self,
        *,
        class_name: str,
        method_name: str,
        compute: tuple[IndexedNodeView, ...],
    ) -> tuple[IndexedNodeView, ...]:
        """Return cached class method results."""
        self._refresh_if_needed()
        key: tuple[str, str] = (class_name, method_name)
        if key not in self._class_methods:
            self._class_methods[key] = compute
        return self._class_methods[key]

    def _refresh_if_needed(self) -> None:
        """Clear caches when the graph has changed."""
        if self._version == self._graph.version:
            return
        self._version = self._graph.version
        self._class_methods.clear()


class IndexedGraphQuery:
    """High-level, cache-aware query API for indexed semantic graphs."""

    def __init__(self, *, graph: IndexedSemanticAstGraph) -> None:
        """Initialize the query facade."""
        self.graph: IndexedSemanticAstGraph = graph
        self._cache: IndexedGraphQueryCache = IndexedGraphQueryCache(
            graph=graph,
        )

    def variable(self, *, name: str) -> tuple[IndexedValueUsage, ...]:
        """Return value-usage summaries for a variable name."""
        return self.graph.value_usage(name=name)

    def functions(self) -> tuple[IndexedNodeView, ...]:
        """Return all function views."""
        return self.graph.functions()

    def classes(self) -> tuple[IndexedNodeView, ...]:
        """Return all class views."""
        return self.graph.classes()

    def nodes_named(self, *, name: str) -> tuple[IndexedNodeView, ...]:
        """Return all nodes with a semantic name."""
        return self.graph.views_named(name=name)

    def calls_named(self, *, name: str) -> tuple[IndexedNodeView, ...]:
        """Return calls whose target has the given name."""
        return tuple(
            call
            for call in self.graph.views_by_kind(kind=SemanticNodeKind.CALL)
            if self._call_target_name(view=call) == name
        )

    def attributes_named(self, *, name: str) -> tuple[IndexedNodeView, ...]:
        """Return attribute nodes with an attribute name."""
        return tuple(
            view
            for view in self.graph.views_named(name=name)
            if view.kind == SemanticNodeKind.ATTRIBUTE
        )

    def init_methods(self, *, class_name: str) -> tuple[IndexedNodeView, ...]:
        """Return indexed ``__init__`` method views for a class."""
        return self.class_methods(
            class_name=class_name,
            method_name="__init__",
        )

    def new_methods(self, *, class_name: str) -> tuple[IndexedNodeView, ...]:
        """Return indexed ``__new__`` method views for a class."""
        return self.class_methods(class_name=class_name, method_name="__new__")

    def class_methods(
        self,
        *,
        class_name: str,
        method_name: str,
    ) -> tuple[IndexedNodeView, ...]:
        """Return methods for a class and method name."""
        computed: tuple[IndexedNodeView, ...] = self._compute_class_methods(
            class_name=class_name,
            method_name=method_name,
        )
        return self._cache.class_methods(
            class_name=class_name,
            method_name=method_name,
            compute=computed,
        )

    def inferred_symbol_type(self, *, name: str) -> TypeExpression | None:
        """Infer a type for all symbols with a given name."""
        evidence: list[TypeInferenceEvidence] = []
        for symbol in self.graph.symbols_named(name=name):
            evidence.extend(symbol.evidence)
        if not evidence:
            return None
        return TypeEvidenceSolver().solve(evidence=tuple(evidence))

    def _compute_class_methods(
        self,
        *,
        class_name: str,
        method_name: str,
    ) -> tuple[IndexedNodeView, ...]:
        """Compute class method views without cache lookup."""
        return tuple(
            child
            for class_view in self.graph.classes()
            if class_view.name == class_name
            for child in class_view.children
            if child.kind == SemanticNodeKind.FUNCTION
            and child.name == method_name
        )

    def _call_target_name(self, *, view: IndexedNodeView) -> str | None:
        """Return the best-effort call target name."""
        for edge in view.outgoing_edges:
            if edge.kind != SemanticEdgeKind.CALLS or edge.label != "target":
                continue
            target: IndexedNodeView = self.graph.view(node_id=edge.target_id)
            return target.name
        return None


class IndexedSemanticGraphParseUnparseToolkit:
    """Parse/unparse toolkit with a high-performance indexed graph."""

    def __init__(self) -> None:
        """Initialize toolkit components."""
        self._model_toolkit: SemanticModelParseUnparseToolkit = (
            SemanticModelParseUnparseToolkit()
        )
        self._parser: CommentAwareParseUnparseToolkit = (
            CommentAwareParseUnparseToolkit()
        )

    def parse_indexed(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> IndexedSemanticGraphParseResult:
        """Parse source and build an indexed semantic graph."""
        parsed: CommentAwareParseResult = self._parser.parse_comments(
            source=source,
        )
        model: ParsedSemanticModel = self._model_toolkit.parse_model(
            source=source,
            filename=filename,
        )
        graph: IndexedSemanticAstGraph = IndexedSemanticGraphBuilder().build(
            root=parsed.body,
        )
        return IndexedSemanticGraphParseResult(
            source=source,
            filename=filename,
            parsed=parsed,
            model=model,
            graph=graph,
        )


class IndexedSemanticGraphEditingCollector(SemanticModelEditingCollector):
    """Editing collector that carries an indexed graph query facade."""

    def __init__(
        self,
        *,
        graph_result: IndexedSemanticGraphParseResult | None = None,
        existing_nodes: Iterable[ExistingTopNode] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
    ) -> None:
        """Initialize an indexed graph-aware editing collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
            existing_type_aliases=existing_type_aliases,
        )
        self.graph_result: IndexedSemanticGraphParseResult | None = (
            graph_result
        )
        self.graph_query: IndexedGraphQuery | None = None
        if graph_result is not None:
            self.graph_query = graph_result.query

    @classmethod
    def from_indexed_result(
        cls,
        *,
        result: IndexedSemanticGraphParseResult,
    ) -> IndexedSemanticGraphEditingCollector:
        """Create a collector initialized from an indexed parse result."""
        return cls(
            graph_result=result,
            existing_nodes=(
                *result.model.context.import_nodes,
                *result.model.context.class_nodes,
            ),
            existing_type_aliases=tuple(
                alias_model.node
                for alias_model in result.model.type_aliases
                if isinstance(alias_model.node, AstTypeAlias)
            ),
        )

    def infer_name(self, *, name: str) -> TypeExpression | None:
        """Infer a type expression for a name from indexed evidence."""
        if self.graph_query is None:
            return None
        return self.graph_query.inferred_symbol_type(name=name)


class TraceableNameSanitizer:
    """Sanitize names used inside traceable path segments."""

    def sanitize(self, *, name: str) -> str:
        """Return a stable path-safe name segment."""
        cleaned: str = sub(pattern=r"\W+", repl="_", string=name).strip("_")
        if not cleaned:
            return "anonymous"
        if cleaned[0].isdigit():
            return f"n_{cleaned}"
        return cleaned


class TraceablePathIndex:
    """Path-based identity index over an indexed semantic graph.

    Names remain queryable, but identity is the canonical path. For example,
    two root functions with the same name become ``root.func_1`` and
    ``root.func_2``. A variable named ``a`` inside the first function is
    ``root.func_1.a`` regardless of how many branch-local stores produce
    evidence for it.
    """

    def __init__(self, *, graph: IndexedSemanticAstGraph) -> None:
        """Build a traceable path index from an indexed graph."""
        self.graph: IndexedSemanticAstGraph = graph
        self.scopes_by_id: dict[IndexedScopeId, TraceableScopeRecord] = {}
        self.symbols_by_id: dict[TraceableSymbolId, TraceableSymbolRecord] = {}
        self.symbols_by_indexed_id: dict[
            IndexedSymbolId,
            TraceableSymbolId,
        ] = {}
        self.symbols_by_path: dict[TraceablePathText, TraceableSymbolId] = {}
        self.symbols_by_name: dict[str, list[TraceableSymbolId]] = {}
        self.attributes: list[TraceableAttributeRecord] = []
        self.container_slots: list[TraceableContainerSlotRecord] = []
        self.value_flows: list[TraceableValueFlowRecord] = []
        self._sanitizer: TraceableNameSanitizer = TraceableNameSanitizer()
        self._ordinals: TraceableSiblingOrdinalState = (
            TraceableSiblingOrdinalState()
        )
        self._build()

    def symbol_by_path(
        self,
        *,
        path: TraceablePathText,
    ) -> TraceableSymbolRecord | None:
        """Return one symbol by canonical path text."""
        symbol_id: TraceableSymbolId | None = self.symbols_by_path.get(path)
        if symbol_id is None:
            return None
        return self.symbols_by_id[symbol_id]

    def symbols_named(self, *, name: str) -> tuple[TraceableSymbolRecord, ...]:
        """Return symbols with a given display name across all scopes."""
        return tuple(
            self.symbols_by_id[symbol_id]
            for symbol_id in self.symbols_by_name.get(name, [])
        )

    def symbols_under(
        self,
        *,
        path: TraceableQualifiedPath,
    ) -> tuple[TraceableSymbolRecord, ...]:
        """Return all symbols nested under a canonical path."""
        return tuple(
            symbol
            for symbol in self.symbols_by_id.values()
            if symbol.path.startswith(other=path)
        )

    def value_flows_for(
        self,
        *,
        path: TraceableQualifiedPath,
    ) -> tuple[TraceableValueFlowRecord, ...]:
        """Return all value-flow records touching a path."""
        return tuple(
            flow
            for flow in self.value_flows
            if path in (flow.source_path, flow.target_path)
        )

    def attribute_writes(
        self,
        *,
        owner_path: TraceableQualifiedPath | None = None,
        name: str | None = None,
    ) -> tuple[TraceableAttributeRecord, ...]:
        """Return attribute write records filtered by owner and name."""
        return tuple(
            record
            for record in self.attributes
            if record.is_write
            and (owner_path is None or record.owner_path == owner_path)
            and (name is None or record.attribute_name == name)
        )

    def _build(self) -> None:
        """Build scopes, symbols, attributes, containers, and value flows."""
        self._build_scope_paths()
        self._build_symbol_paths()
        self._build_attribute_paths()
        self._build_assignment_value_flows()
        self._build_container_value_flows()

    def _build_scope_paths(self) -> None:
        """Build canonical scope paths from lexical scope records."""
        for scope in self.graph.scopes:
            parent_path: TraceableQualifiedPath | None = None
            if scope.parent_id is not None:
                parent_path = self.scopes_by_id[scope.parent_id].path
            path: TraceableQualifiedPath = self._scope_path(
                scope=scope,
                parent_path=parent_path,
            )
            self.scopes_by_id[scope.id] = TraceableScopeRecord(
                scope_id=scope.id,
                name=scope.name,
                kind=scope.kind,
                node_id=scope.node_id,
                parent_scope_id=scope.parent_id,
                path=path,
            )

    def _scope_path(
        self,
        *,
        scope: IndexedSemanticScope,
        parent_path: TraceableQualifiedPath | None,
    ) -> TraceableQualifiedPath:
        """Return the canonical path for one scope."""
        if parent_path is None:
            return TraceableQualifiedPath.root()
        kind: TraceablePathKind = self._path_kind_for_scope(kind=scope.kind)
        name: str = self._sanitizer.sanitize(name=scope.name)
        ordinal: int = self._ordinals.next(
            parent=parent_path,
            name=name,
            kind=kind,
        )
        return parent_path.child(name=name, kind=kind, ordinal=ordinal)

    def _path_kind_for_scope(
        self,
        *,
        kind: SemanticScopeKind,
    ) -> TraceablePathKind:
        """Return a path segment kind for a semantic scope kind."""
        if kind == SemanticScopeKind.CLASS:
            return TraceablePathKind.CLASS
        if kind == SemanticScopeKind.FUNCTION:
            return TraceablePathKind.FUNCTION
        return TraceablePathKind.MODULE

    def _build_symbol_paths(self) -> None:
        """Create traceable symbol records from indexed graph symbols."""
        for indexed_symbol in self.graph.symbols:
            path: TraceableQualifiedPath = self._path_for_indexed_symbol(
                symbol=indexed_symbol,
            )
            symbol_id: TraceableSymbolId = len(self.symbols_by_id)
            record: TraceableSymbolRecord = TraceableSymbolRecord(
                id=symbol_id,
                indexed_symbol_id=indexed_symbol.id,
                name=indexed_symbol.name,
                kind=indexed_symbol.kind,
                scope_id=indexed_symbol.scope_id,
                path=path,
                definition_node_id=indexed_symbol.definition_node_id,
                usage_node_ids=list(indexed_symbol.usage_node_ids),
                evidence=list(indexed_symbol.evidence),
            )
            self.symbols_by_id[symbol_id] = record
            self.symbols_by_indexed_id[indexed_symbol.id] = symbol_id
            self.symbols_by_path[path.text] = symbol_id
            self.symbols_by_name.setdefault(indexed_symbol.name, []).append(
                symbol_id,
            )

    def _path_for_indexed_symbol(
        self,
        *,
        symbol: IndexedSemanticSymbol,
    ) -> TraceableQualifiedPath:
        """Return canonical path for one indexed symbol."""
        matching_scope_path: TraceableQualifiedPath | None = (
            self._owned_scope_path(
                symbol=symbol,
            )
        )
        if matching_scope_path is not None:
            return matching_scope_path
        scope_path: TraceableQualifiedPath = self.scopes_by_id[
            symbol.scope_id
        ].path
        name: str = self._sanitizer.sanitize(name=symbol.name)
        return scope_path.child(name=name, kind=TraceablePathKind.SYMBOL)

    def _owned_scope_path(
        self,
        *,
        symbol: IndexedSemanticSymbol,
    ) -> TraceableQualifiedPath | None:
        """Return child scope path if a class/function symbol owns one."""
        if symbol.kind not in {
            SemanticSymbolKind.CLASS,
            SemanticSymbolKind.FUNCTION,
        }:
            return None
        if symbol.definition_node_id is None:
            return None
        for scope_record in self.scopes_by_id.values():
            if scope_record.node_id == symbol.definition_node_id:
                return scope_record.path
        return None

    def _build_attribute_paths(self) -> None:
        """Build path records for attribute reads and writes."""
        for node in self.graph.nodes:
            if not isinstance(node.ast_node, Attribute):
                continue
            owner_path: TraceableQualifiedPath | None = self._path_for_expr(
                node=node.ast_node.value,
            )
            if owner_path is None:
                continue
            attribute_path: TraceableQualifiedPath = owner_path.child(
                name=self._sanitizer.sanitize(name=node.ast_node.attr),
                kind=TraceablePathKind.ATTRIBUTE,
            )
            self.attributes.append(
                TraceableAttributeRecord(
                    owner_path=owner_path,
                    attribute_name=node.ast_node.attr,
                    path=attribute_path,
                    node_id=node.id,
                    is_write=isinstance(node.ast_node.ctx, Store),
                ),
            )

    def _build_assignment_value_flows(self) -> None:
        """Build path-level value flows for assignments."""
        for edge in self.graph.edges:
            if edge.kind != SemanticEdgeKind.ASSIGNS_VALUE:
                continue
            source_node: IndexedSemanticGraphNode = self.graph.node(
                node_id=edge.source_id,
            )
            target_node: IndexedSemanticGraphNode = self.graph.node(
                node_id=edge.target_id,
            )
            source_path: TraceableQualifiedPath | None = self._path_for_ast(
                node=source_node.ast_node,
            )
            target_path: TraceableQualifiedPath | None = self._path_for_ast(
                node=target_node.ast_node,
            )
            if source_path is None or target_path is None:
                continue
            self.value_flows.append(
                TraceableValueFlowRecord(
                    source_path=target_path,
                    target_path=source_path,
                    relation=TraceableValueRelation.ASSIGNED_FROM,
                    source_node_id=edge.target_id,
                    target_node_id=edge.source_id,
                ),
            )

    def _build_container_value_flows(self) -> None:
        """Build traceable paths for literal container elements."""
        for node in self.graph.nodes:
            if isinstance(node.ast_node, AstList | AstTuple | AstSet):
                self._add_sequence_slots(node=node)
            elif isinstance(node.ast_node, AstDict):
                self._add_dict_slots(node=node)

    def _add_sequence_slots(self, *, node: IndexedSemanticGraphNode) -> None:
        """Add slot records for list/tuple/set literal elements."""
        if not isinstance(node.ast_node, AstList | AstTuple | AstSet):
            return
        container_path: TraceableQualifiedPath | None = self._path_for_ast(
            node=node.ast_node,
        )
        if container_path is None:
            container_path = self._temporary_path(
                node_id=node.id,
            )
        for index, element in enumerate(iterable=node.ast_node.elts):
            value_path: TraceableQualifiedPath | None = self._path_for_ast(
                node=element,
            )
            if value_path is None:
                element_id: IndexedNodeId | None = self.graph.node_id_for_ast(
                    node=element,
                )
                if element_id is None:
                    continue
                value_path = self._temporary_path(
                    node_id=element_id,
                )
            slot_path: TraceableQualifiedPath = container_path.child(
                name=f"item_{index}",
                kind=TraceablePathKind.CONTAINER_SLOT,
            )
            self.container_slots.append(
                TraceableContainerSlotRecord(
                    container_path=container_path,
                    slot_path=slot_path,
                    value_path=value_path,
                    relation=TraceableValueRelation.CONTAINS_ELEMENT,
                    node_id=node.id,
                ),
            )
            self.value_flows.append(
                TraceableValueFlowRecord(
                    source_path=value_path,
                    target_path=slot_path,
                    relation=TraceableValueRelation.CONTAINS_ELEMENT,
                    source_node_id=self.graph.node_id_for_ast(node=element),
                    target_node_id=node.id,
                    label=str(object=index),
                ),
            )

    def _add_dict_slots(self, *, node: IndexedSemanticGraphNode) -> None:
        """Add slot records for dictionary literal keys and values."""
        if not isinstance(node.ast_node, AstDict):
            return
        container_path: TraceableQualifiedPath | None = self._path_for_ast(
            node=node.ast_node,
        )
        if container_path is None:
            container_path = self._temporary_path(
                node_id=node.id,
            )
        for index, key_node in enumerate(iterable=node.ast_node.keys):
            value_node: expr = node.ast_node.values[index]
            value_path: TraceableQualifiedPath | None = self._path_for_ast(
                node=value_node,
            )
            if value_path is None:
                value_id: IndexedNodeId | None = self.graph.node_id_for_ast(
                    node=value_node,
                )
                if value_id is None:
                    continue
                value_path = self._temporary_path(
                    node_id=value_id,
                )
            value_slot_path: TraceableQualifiedPath = container_path.child(
                name=f"value_{index}",
                kind=TraceablePathKind.CONTAINER_SLOT,
            )
            self.container_slots.append(
                TraceableContainerSlotRecord(
                    container_path=container_path,
                    slot_path=value_slot_path,
                    value_path=value_path,
                    relation=TraceableValueRelation.CONTAINS_VALUE,
                    node_id=node.id,
                ),
            )
            self.value_flows.append(
                TraceableValueFlowRecord(
                    source_path=value_path,
                    target_path=value_slot_path,
                    relation=TraceableValueRelation.CONTAINS_VALUE,
                    source_node_id=self.graph.node_id_for_ast(node=value_node),
                    target_node_id=node.id,
                    label=str(object=index),
                ),
            )
            if key_node is not None:
                self._add_dict_key_flow(
                    container_path=container_path,
                    key_node=key_node,
                    index=index,
                    container_node_id=node.id,
                )

    def _add_dict_key_flow(
        self,
        *,
        container_path: TraceableQualifiedPath,
        key_node: expr,
        index: int,
        container_node_id: IndexedNodeId,
    ) -> None:
        """Add one dictionary key flow record."""
        key_path: TraceableQualifiedPath | None = self._path_for_ast(
            node=key_node,
        )
        if key_path is None:
            key_id: IndexedNodeId | None = self.graph.node_id_for_ast(
                node=key_node,
            )
            if key_id is None:
                return
            key_path = self._temporary_path(
                node_id=key_id,
            )
        key_slot_path: TraceableQualifiedPath = container_path.child(
            name=f"key_{index}",
            kind=TraceablePathKind.CONTAINER_SLOT,
        )
        self.container_slots.append(
            TraceableContainerSlotRecord(
                container_path=container_path,
                slot_path=key_slot_path,
                value_path=key_path,
                relation=TraceableValueRelation.CONTAINS_KEY,
                node_id=container_node_id,
            ),
        )
        self.value_flows.append(
            TraceableValueFlowRecord(
                source_path=key_path,
                target_path=key_slot_path,
                relation=TraceableValueRelation.CONTAINS_KEY,
                source_node_id=self.graph.node_id_for_ast(node=key_node),
                target_node_id=container_node_id,
                label=str(object=index),
            ),
        )

    def _path_for_ast(self, *, node: AST) -> TraceableQualifiedPath | None:
        """Return the canonical path for an AST node when available."""
        if isinstance(node, Name):
            return self._path_for_name(node=node)
        if isinstance(node, Attribute):
            owner_path: TraceableQualifiedPath | None = self._path_for_expr(
                node=node.value,
            )
            if owner_path is None:
                return None
            return owner_path.child(
                name=self._sanitizer.sanitize(name=node.attr),
                kind=TraceablePathKind.ATTRIBUTE,
            )
        node_id: IndexedNodeId | None = self.graph.node_id_for_ast(node=node)
        if node_id is None:
            return None
        return self._temporary_path(node_id=node_id)

    def _path_for_expr(self, *, node: expr) -> TraceableQualifiedPath | None:
        """Return the canonical path for an expression when available."""
        return self._path_for_ast(node=node)

    def _path_for_name(self, *, node: Name) -> TraceableQualifiedPath | None:
        """Resolve a name node to its traceable lexical symbol path."""
        node_id: IndexedNodeId | None = self.graph.node_id_for_ast(node=node)
        if node_id is None:
            return None
        graph_node: IndexedSemanticGraphNode = self.graph.node(node_id=node_id)
        symbol: IndexedSemanticSymbol | None = self.graph.lookup_symbol(
            name=node.id,
            scope_id=graph_node.scope_id,
        )
        if symbol is None:
            return None
        trace_symbol_id: TraceableSymbolId | None = (
            self.symbols_by_indexed_id.get(
                symbol.id,
            )
        )
        if trace_symbol_id is None:
            return None
        return self.symbols_by_id[trace_symbol_id].path

    def _temporary_path(
        self,
        *,
        node_id: IndexedNodeId,
    ) -> TraceableQualifiedPath:
        """Return a stable temporary path for anonymous expression values."""
        node: IndexedSemanticGraphNode = self.graph.node(node_id=node_id)
        scope_path: TraceableQualifiedPath = self.scopes_by_id[
            node.scope_id
        ].path
        return scope_path.child(
            name=f"tmp_{node_id}",
            kind=TraceablePathKind.TEMPORARY,
        )


class TraceableGraphQuery:
    """Path-aware query API that never treats name alone as identity."""

    def __init__(self, *, trace: TraceablePathIndex) -> None:
        """Initialize the query facade."""
        self._trace: TraceablePathIndex = trace

    def symbol(
        self,
        *,
        path: TraceablePathText,
    ) -> TraceableSymbolRecord | None:
        """Return a unique symbol by canonical path."""
        return self._trace.symbol_by_path(path=path)

    def symbols_named(self, *, name: str) -> tuple[TraceableSymbolRecord, ...]:
        """Return all symbols with this name across all paths."""
        return self._trace.symbols_named(name=name)

    def under(
        self,
        *,
        path: TraceableQualifiedPath,
    ) -> tuple[TraceableSymbolRecord, ...]:
        """Return all symbols nested under a path."""
        return self._trace.symbols_under(path=path)

    def flows_for(
        self,
        *,
        path: TraceableQualifiedPath,
    ) -> tuple[TraceableValueFlowRecord, ...]:
        """Return all value-flow records touching a path."""
        return self._trace.value_flows_for(path=path)

    def attribute_writes(
        self,
        *,
        owner_path: TraceableQualifiedPath | None = None,
        name: str | None = None,
    ) -> tuple[TraceableAttributeRecord, ...]:
        """Return attribute write records."""
        return self._trace.attribute_writes(owner_path=owner_path, name=name)

    def inferred_type(
        self,
        *,
        path: TraceablePathText,
    ) -> TypeExpression | None:
        """Infer a symbol type by unique path, not by name."""
        symbol: TraceableSymbolRecord | None = self.symbol(path=path)
        if symbol is None or not symbol.evidence:
            return None
        return TypeEvidenceSolver().solve(evidence=tuple(symbol.evidence))


class TraceableSemanticGraphParseUnparseToolkit(
    IndexedSemanticGraphParseUnparseToolkit,
):
    """Toolkit that returns both fast IDs and traceable path identities."""

    def parse_traceable(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> TraceableGraphParseResult:
        """Parse source into an indexed graph with canonical symbol paths."""
        indexed: IndexedSemanticGraphParseResult = self.parse_indexed(
            source=source,
            filename=filename,
        )
        trace: TraceablePathIndex = TraceablePathIndex(graph=indexed.graph)
        return TraceableGraphParseResult(indexed=indexed, trace=trace)


class TraceableSemanticGraphEditingCollector(
    IndexedSemanticGraphEditingCollector,
):
    """Editing collector with path-aware symbol inference helpers."""

    def __init__(
        self,
        *,
        trace: TraceablePathIndex | None = None,
        existing_nodes: Iterable[ExistingTopNode] = (),
        postponed_annotations: bool | None = None,
        local_roots: Iterable[str] = (),
        existing_type_aliases: Iterable[AstTypeAlias] = (),
    ) -> None:
        """Initialize path-aware editing collector."""
        super().__init__(
            existing_nodes=existing_nodes,
            postponed_annotations=postponed_annotations,
            local_roots=local_roots,
            existing_type_aliases=existing_type_aliases,
        )
        self.trace: TraceablePathIndex | None = trace
        self.trace_query: TraceableGraphQuery | None = None
        if trace is not None:
            self.trace_query = TraceableGraphQuery(
                trace=trace,
            )

    @classmethod
    def from_traceable_result(
        cls,
        *,
        result: TraceableGraphParseResult,
    ) -> TraceableSemanticGraphEditingCollector:
        """Create a collector from a traceable parse result."""
        return cls(
            trace=result.trace,
            existing_nodes=(
                *result.indexed.model.context.import_nodes,
                *result.indexed.model.context.class_nodes,
            ),
            existing_type_aliases=tuple(
                alias_model.node
                for alias_model in result.indexed.model.type_aliases
                if isinstance(alias_model.node, AstTypeAlias)
            ),
        )

    def infer_path(self, *, path: TraceablePathText) -> TypeExpression | None:
        """Infer a type for a canonical symbol path."""
        if self.trace is None:
            return None
        query: TraceableGraphQuery = TraceableGraphQuery(trace=self.trace)
        return query.inferred_type(path=path)

    def symbols_named(
        self,
        *,
        name: str,
    ) -> tuple[TraceableSymbolRecord, ...]:
        """Return all traceable symbols by display name."""
        if self.trace is None:
            return ()
        return self.trace.symbols_named(name=name)


class LocalImportPathResolver:
    """Resolve semantic import sources to project or stub files."""

    def __init__(self, *, config: LocalImportInspectionConfig) -> None:
        """Initialize the resolver."""
        self.config: LocalImportInspectionConfig = config.normalized()

    def resolve(
        self,
        *,
        source: SemanticImportSource,
    ) -> LocalImportResolution:
        """Resolve a semantic import source to candidate files."""
        candidates: list[LocalImportPathCandidate] = []
        candidates.extend(self._project_candidates(source=source))
        candidates.extend(self._relative_candidates(source=source))
        candidates.extend(self._stub_candidates(source=source))
        return LocalImportResolution(
            source=source,
            candidates=tuple(candidates),
        )

    def _project_candidates(
        self,
        *,
        source: SemanticImportSource,
    ) -> tuple[LocalImportPathCandidate, ...]:
        """Return project-root candidates for absolute imports."""
        if not self.config.inspect_project or self.config.project_root is None:
            return ()
        if source.level != 0:
            return ()
        if not source.module_parts:
            return ()
        return self._module_candidates(
            root=self.config.project_root,
            module_parts=source.module_parts,
            source=LocalImportInspectionSource.PROJECT_ROOT,
            is_stub=False,
            suffix=".py",
        )

    def _relative_candidates(
        self,
        *,
        source: SemanticImportSource,
    ) -> tuple[LocalImportPathCandidate, ...]:
        """Return candidates for relative imports based on script_path."""
        if (
            not self.config.inspect_relative
            or self.config.script_directory is None
        ):
            return ()
        if source.level <= 0:
            return ()
        base: Path = self.config.script_directory
        for _index in range(source.level - 1):
            base = base.parent
        return self._module_candidates(
            root=base,
            module_parts=source.module_parts,
            source=LocalImportInspectionSource.SCRIPT_DIRECTORY,
            is_stub=False,
            suffix=".py",
        )

    def _stub_candidates(
        self,
        *,
        source: SemanticImportSource,
    ) -> tuple[LocalImportPathCandidate, ...]:
        """Return stub-root candidates for absolute imports."""
        if not self.config.inspect_stubs:
            return ()
        if source.level != 0:
            return ()
        if not source.module_parts:
            return ()
        candidates: list[LocalImportPathCandidate] = []
        for stub_root in self.config.stub_roots:
            candidates.extend(
                self._module_candidates(
                    root=stub_root,
                    module_parts=source.module_parts,
                    source=LocalImportInspectionSource.STUB_ROOT,
                    is_stub=True,
                    suffix=".pyi",
                ),
            )
        return tuple(candidates)

    def _module_candidates(
        self,
        *,
        root: Path,
        module_parts: tuple[str, ...],
        source: LocalImportInspectionSource,
        is_stub: bool,
        suffix: str,
    ) -> tuple[LocalImportPathCandidate, ...]:
        """Return module-file and package-init candidates."""
        module_path: Path = root.joinpath(*module_parts)
        return (
            LocalImportPathCandidate(
                path=module_path.with_suffix(suffix=suffix),
                source=source,
                is_stub=is_stub,
            ),
            LocalImportPathCandidate(
                path=module_path / f"__init__{suffix}",
                source=source,
                is_stub=is_stub,
            ),
        )


class LocalImportSymbolCatalog:
    """Iterable catalog of symbols discovered from local imports and stubs."""

    def __init__(self) -> None:
        """Initialize an empty local-import symbol catalog."""
        self._records: list[LocalImportSymbolRecord] = []
        self._by_name: dict[str, list[int]] = {}
        self._by_module: dict[str | None, list[int]] = {}
        self._by_file: dict[Path, list[int]] = {}

    def __iter__(self) -> Iterator[LocalImportSymbolRecord]:
        """Iterate over all discovered import symbols."""
        return iter(self._records)

    def __len__(self) -> int:
        """Return the number of discovered symbols."""
        return len(self._records)

    def add(self, *, record: LocalImportSymbolRecord) -> None:
        """Add one symbol record."""
        index: int = len(self._records)
        self._records.append(record)
        self._by_name.setdefault(record.name, []).append(index)
        self._by_module.setdefault(record.module, []).append(index)
        self._by_file.setdefault(record.file_path, []).append(index)

    def extend(self, *, records: Iterable[LocalImportSymbolRecord]) -> None:
        """Add many records."""
        for record in records:
            self.add(record=record)

    def by_name(self, *, name: str) -> tuple[LocalImportSymbolRecord, ...]:
        """Return records with the given symbol name."""
        return tuple(
            self._records[index] for index in self._by_name.get(name, ())
        )

    def by_module(
        self,
        *,
        module: str | None,
    ) -> tuple[LocalImportSymbolRecord, ...]:
        """Return records discovered in a module."""
        return tuple(
            self._records[index] for index in self._by_module.get(module, ())
        )

    def by_file(self, *, path: Path) -> tuple[LocalImportSymbolRecord, ...]:
        """Return records discovered in one file."""
        resolved_path: Path = path.expanduser().resolve(strict=False)
        return tuple(
            self._records[index]
            for index in self._by_file.get(resolved_path, ())
        )

    def all(self) -> tuple[LocalImportSymbolRecord, ...]:
        """Return all records as a tuple."""
        return tuple(self._records)


class LocalImportInspector:
    """Inspect local project files and stubs for importable symbols."""

    def __init__(self, *, resolver: LocalImportPathResolver) -> None:
        """Initialize the inspector."""
        self._resolver: LocalImportPathResolver = resolver
        self._seen_files: set[Path] = set()

    def inspect_source(
        self,
        *,
        source: SemanticImportSource,
    ) -> LocalImportSymbolCatalog:
        """Inspect all existing files for one import source."""
        resolution: LocalImportResolution = self._resolver.resolve(
            source=source,
        )
        catalog: LocalImportSymbolCatalog = LocalImportSymbolCatalog()
        for candidate in resolution.existing_candidates:
            catalog.extend(records=self.inspect_candidate(candidate=candidate))
        return catalog

    def inspect_sources(
        self,
        *,
        sources: Iterable[SemanticImportSource],
    ) -> LocalImportSymbolCatalog:
        """Inspect many semantic import sources."""
        catalog: LocalImportSymbolCatalog = LocalImportSymbolCatalog()
        for source in sources:
            catalog.extend(records=self.inspect_source(source=source))
        return catalog

    def inspect_candidate(
        self,
        *,
        candidate: LocalImportPathCandidate,
    ) -> tuple[LocalImportSymbolRecord, ...]:
        """Inspect one concrete file candidate."""
        resolved_path: Path = candidate.path.expanduser().resolve(strict=False)
        if resolved_path in self._seen_files:
            return ()
        self._seen_files.add(resolved_path)
        source_text: str = resolved_path.read_text(encoding="utf-8")
        module: Module = parse(
            source=source_text,
            filename=str(object=resolved_path),
        )
        module_name: str | None = self._module_name_from_path(
            path=resolved_path,
        )
        return self._records_from_module(
            module=module,
            module_name=module_name,
            candidate=LocalImportPathCandidate(
                path=resolved_path,
                source=candidate.source,
                is_stub=candidate.is_stub,
            ),
        )

    def _records_from_module(
        self,
        *,
        module: Module,
        module_name: str | None,
        candidate: LocalImportPathCandidate,
    ) -> tuple[LocalImportSymbolRecord, ...]:
        """Extract top-level symbols from a parsed module."""
        records: list[LocalImportSymbolRecord] = []
        for node in module.body:
            kind: LocalImportSymbolKind | None = self._symbol_kind(node=node)
            if kind is None:
                continue
            name: str | None = self._symbol_name(node=node)
            if name is None:
                continue
            records.append(
                LocalImportSymbolRecord(
                    name=name,
                    kind=kind,
                    module=module_name,
                    file_path=candidate.path,
                    node=node,
                    source=candidate.source,
                    is_stub=candidate.is_stub,
                ),
            )
        return tuple(records)

    def _symbol_kind(self, *, node: stmt) -> LocalImportSymbolKind | None:
        """Return the catalog kind for one top-level statement."""
        direct_kind: LocalImportSymbolKind | None = None
        if isinstance(node, ClassDef):
            direct_kind = LocalImportSymbolKind.CLASS
        elif isinstance(node, AsyncFunctionDef):
            direct_kind = LocalImportSymbolKind.ASYNC_FUNCTION
        elif isinstance(node, FunctionDef):
            direct_kind = LocalImportSymbolKind.FUNCTION
        elif isinstance(node, AstTypeAlias):
            direct_kind = LocalImportSymbolKind.TYPE_ALIAS
        elif isinstance(node, ImportFrom | Import):
            direct_kind = LocalImportSymbolKind.IMPORTED
        if direct_kind is not None:
            return direct_kind
        if isinstance(node, Assign):
            return self._assignment_symbol_kind(node=node)
        return None

    def _symbol_name(self, *, node: stmt) -> str | None:
        """Return the exported symbol name for one top-level statement."""
        if isinstance(node, ClassDef | FunctionDef | AsyncFunctionDef):
            return node.name
        if isinstance(node, AstTypeAlias):
            return self._type_alias_name(node=node)
        if isinstance(node, Assign):
            return self._assignment_name(node=node)
        if isinstance(node, ImportFrom):
            return self._import_from_name(node=node)
        if isinstance(node, Import):
            return self._import_name(node=node)
        return None

    def _type_alias_name(self, *, node: AstTypeAlias) -> str:
        """Return a type alias name."""
        return node.name.id

    def _assignment_name(self, *, node: Assign) -> str | None:
        """Return a simple assignment target name."""
        if len(node.targets) != 1:
            return None
        target: expr = node.targets[0]
        if isinstance(target, Name):
            return target.id
        return None

    def _import_from_name(self, *, node: ImportFrom) -> str | None:
        """Return the first imported local name from a from-import."""
        if not node.names:
            return None
        return node.names[0].asname or node.names[0].name

    def _import_name(self, *, node: Import) -> str | None:
        """Return the first local name from an import statement."""
        if not node.names:
            return None
        import_name: str = node.names[0].name.split(sep=".", maxsplit=1)[0]
        return node.names[0].asname or import_name

    def _assignment_symbol_kind(
        self,
        *,
        node: Assign,
    ) -> LocalImportSymbolKind | None:
        """Classify a top-level assignment symbol."""
        if not isinstance(node.value, Call):
            return None
        function_name: str | None = self._call_function_name(node=node.value)
        if function_name == "TypeVar":
            return LocalImportSymbolKind.TYPEVAR
        if function_name == "ParamSpec":
            return LocalImportSymbolKind.PARAMSPEC
        if function_name == "TypeVarTuple":
            return LocalImportSymbolKind.TYPEVARTUPLE
        return None

    def _call_function_name(self, *, node: Call) -> str | None:
        """Return the final function name for a call expression."""
        if isinstance(node.func, Name):
            return node.func.id
        if isinstance(node.func, Attribute):
            return node.func.attr
        return None

    def _module_name_from_path(self, *, path: Path) -> str | None:
        """Return a best-effort module name for a file path."""
        stem: str = path.stem
        if stem == "__init__":
            return path.parent.name
        return stem


class ImportSourceCollector:
    """Collect semantic import sources from existing ImportFrom nodes."""

    def sources_from_imports(
        self,
        *,
        imports: Iterable[Import | ImportFrom],
    ) -> tuple[SemanticImportSource, ...]:
        """Return semantic sources represented by import statements."""
        sources: list[SemanticImportSource] = []
        for import_node in imports:
            if isinstance(import_node, ImportFrom):
                sources.extend(
                    self._sources_from_import_from(node=import_node),
                )
            else:
                sources.extend(self._sources_from_import(node=import_node))
        return tuple(sources)

    def _sources_from_import_from(
        self,
        *,
        node: ImportFrom,
    ) -> tuple[SemanticImportSource, ...]:
        """Return sources from a from-import statement."""
        module_parts: tuple[str, ...] = ()
        if node.module is not None:
            module_parts = tuple(
                part for part in node.module.split(sep=".") if part
            )
        sources: list[SemanticImportSource] = []
        for item in node.names:
            if item.name == "*":
                continue
            if node.level > 0:
                sources.append(
                    SemanticImportSource.relative(
                        level=node.level,
                        module_parts=module_parts,
                        imported_name=item.name,
                        asname=item.asname,
                    ),
                )
            else:
                sources.append(
                    SemanticImportSource.absolute(
                        module_parts=module_parts,
                        imported_name=item.name,
                        asname=item.asname,
                    ),
                )
        return tuple(sources)

    def _sources_from_import(
        self,
        *,
        node: Import,
    ) -> tuple[SemanticImportSource, ...]:
        """Return module sources from plain import statements."""
        sources: list[SemanticImportSource] = []
        for item in node.names:
            module_parts: tuple[str, ...] = tuple(
                part for part in item.name.split(sep=".") if part
            )
            if not module_parts:
                continue
            sources.append(
                SemanticImportSource.absolute(
                    module_parts=module_parts,
                    imported_name=module_parts[-1],
                    asname=item.asname,
                ),
            )
        return tuple(sources)


class TraceableSymbolCatalog:
    """Iterable catalog facade over traceable symbols."""

    def __init__(self, *, trace: TraceablePathIndex) -> None:
        """Initialize the catalog."""
        self._trace: TraceablePathIndex = trace

    def __iter__(self) -> Iterator[TraceableSymbolRecord]:
        """Iterate over every traceable symbol record."""
        return iter(self._trace.symbols_by_id.values())

    def __len__(self) -> int:
        """Return the number of traceable symbols."""
        return len(self._trace.symbols_by_id)

    def by_name(self, *, name: str) -> tuple[TraceableSymbolRecord, ...]:
        """Return traceable symbols by display name."""
        return self._trace.symbols_named(name=name)

    def by_path(
        self,
        *,
        path: TraceablePathText,
    ) -> TraceableSymbolRecord | None:
        """Return one traceable symbol by canonical path."""
        return self._trace.symbol_by_path(path=path)

    def all(self) -> tuple[TraceableSymbolRecord, ...]:
        """Return all traceable symbols."""
        return tuple(self)


class UnifiedSymbolCatalog:
    """Combine graph and import symbols."""

    def __init__(
        self,
        *,
        trace_symbols: TraceableSymbolCatalog,
        import_symbols: LocalImportSymbolCatalog,
    ) -> None:
        """Initialize the unified catalog."""
        self.trace_symbols: TraceableSymbolCatalog = trace_symbols
        self.import_symbols: LocalImportSymbolCatalog = import_symbols

    def __iter__(
        self,
    ) -> Iterator[TraceableSymbolRecord | LocalImportSymbolRecord]:
        """Iterate over every known graph and import symbol."""
        for record in self.trace_symbols:
            yield record
        for record in self.import_symbols:
            yield record

    def __len__(self) -> int:
        """Return the total symbol count."""
        return len(self.trace_symbols) + len(self.import_symbols)

    def trace_named(self, *, name: str) -> tuple[TraceableSymbolRecord, ...]:
        """Return graph symbols by display name."""
        return self.trace_symbols.by_name(name=name)

    def imports_named(
        self,
        *,
        name: str,
    ) -> tuple[LocalImportSymbolRecord, ...]:
        """Return inspected import symbols by name."""
        return self.import_symbols.by_name(name=name)

    def all(
        self,
    ) -> tuple[TraceableSymbolRecord | LocalImportSymbolRecord, ...]:
        """Return all symbol records."""
        return tuple(self)


class ImportInspectingTraceableSemanticGraphParseUnparseToolkit(
    TraceableSemanticGraphParseUnparseToolkit,
):
    """Traceable toolkit with optional project/stub import inspection."""

    def parse_traceable_with_imports(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
        import_config: LocalImportInspectionConfig | None = None,
    ) -> ImportInspectingTraceableGraphParseResult:
        """Parse source and optionally inspect local/stub imports."""
        traceable: TraceableGraphParseResult = self.parse_traceable(
            source=source,
            filename=filename,
        )
        config: LocalImportInspectionConfig = self._config_for(
            filename=filename,
            import_config=import_config,
        )
        import_symbols: LocalImportSymbolCatalog = self._inspect_imports(
            traceable=traceable,
            config=config,
        )
        trace_symbols: TraceableSymbolCatalog = TraceableSymbolCatalog(
            trace=traceable.trace,
        )
        return ImportInspectingTraceableGraphParseResult(
            traceable=traceable,
            import_symbols=import_symbols,
            symbol_catalog=UnifiedSymbolCatalog(
                trace_symbols=trace_symbols,
                import_symbols=import_symbols,
            ),
        )

    def _config_for(
        self,
        *,
        filename: str,
        import_config: LocalImportInspectionConfig | None,
    ) -> LocalImportInspectionConfig:
        """Return an import-inspection config for a parse request."""
        if import_config is not None:
            return import_config
        if filename == "<unknown>":
            return LocalImportInspectionConfig()
        return LocalImportInspectionConfig(script_path=Path(filename))

    def _inspect_imports(
        self,
        *,
        traceable: TraceableGraphParseResult,
        config: LocalImportInspectionConfig,
    ) -> LocalImportSymbolCatalog:
        """Inspect imports from a traceable parse result."""
        context: ExistingNodeContext = traceable.indexed.model.context
        source_collector: ImportSourceCollector = ImportSourceCollector()
        sources: tuple[SemanticImportSource, ...] = (
            source_collector.sources_from_imports(imports=context.import_nodes)
        )
        resolver: LocalImportPathResolver = LocalImportPathResolver(
            config=config,
        )
        inspector: LocalImportInspector = LocalImportInspector(
            resolver=resolver,
        )
        return inspector.inspect_sources(sources=sources)


class ImportInspectingTraceableSemanticGraphEditingCollector(
    TraceableSemanticGraphEditingCollector,
):
    """Editing collector that exposes an iterable unified symbol catalog."""

    def __init__(
        self,
        *,
        config: ImportInspectingEditingCollectorConfig | None = None,
    ) -> None:
        """Initialize the collector."""
        final_config: ImportInspectingEditingCollectorConfig = (
            config or ImportInspectingEditingCollectorConfig()
        )
        super().__init__(
            trace=final_config.trace,
            existing_nodes=final_config.existing_nodes,
            postponed_annotations=final_config.postponed_annotations,
            local_roots=final_config.local_roots,
            existing_type_aliases=final_config.existing_type_aliases,
        )
        self.symbol_catalog: UnifiedSymbolCatalog | None = (
            final_config.symbol_catalog
        )

    @classmethod
    def from_import_inspecting_result(
        cls,
        *,
        result: ImportInspectingTraceableGraphParseResult,
    ) -> ImportInspectingTraceableSemanticGraphEditingCollector:
        """Create a collector from an import-inspecting parse result."""
        return cls(
            config=ImportInspectingEditingCollectorConfig(
                trace=result.trace,
                symbol_catalog=result.symbol_catalog,
                existing_nodes=(
                    *result.traceable.indexed.model.context.import_nodes,
                    *result.traceable.indexed.model.context.class_nodes,
                ),
            ),
        )

    def iter_symbols(
        self,
    ) -> Iterator[TraceableSymbolRecord | LocalImportSymbolRecord]:
        """Iterate over the unified symbol catalog when available."""
        if self.symbol_catalog is None:
            return iter(())
        return iter(self.symbol_catalog)


class AntFarmSymbolCollection:
    """Callable, sliceable, navigable collection of symbol views."""

    def __init__(
        self,
        *,
        records: Iterable[CatalogSymbolRecord],
        trace: TraceablePathIndex | None = None,
    ) -> None:
        """Initialize the collection."""
        self._records: tuple[CatalogSymbolRecord, ...] = tuple(records)
        self._trace: TraceablePathIndex | None = trace

    def __iter__(self) -> Iterator[AntFarmSymbolView]:
        """Iterate over chainable symbol views."""
        return iter(
            tuple(
                AntFarmSymbolView(record=record, trace=self._trace)
                for record in self._records
            ),
        )

    def __len__(self) -> int:
        """Return symbol count."""
        return len(self._records)

    def __bool__(self) -> bool:
        """Return whether the collection has symbols."""
        return bool(self._records)

    def __getitem__(
        self,
        index: CatalogSymbolSelector,
    ) -> AntFarmSymbolView | AntFarmSymbolCollection:
        """Return one symbol view or a sliced collection."""
        if isinstance(index, slice):
            return AntFarmSymbolCollection(
                records=self._records[index],
                trace=self._trace,
            )
        return AntFarmSymbolView(
            record=self._records[index],
            trace=self._trace,
        )

    def __call__(
        self,
        *,
        path: str | None = None,
        name: str | None = None,
        kind: str | None = None,
        lib: str | None = None,
    ) -> AntFarmSymbolCollection:
        """Filter symbols by path, name, kind, or import library/module."""
        selected: (
            tuple[CatalogSymbolRecord, ...]
            | tuple[
                TraceableSymbolRecord | LocalImportSymbolRecord,
                ...,
            ]
        ) = self._records
        if path is not None:
            selected = tuple(
                record
                for record in selected
                if self._path(record=record) == path
            )
        if name is not None:
            selected = tuple(
                record for record in selected if record.name == name
            )
        if kind is not None:
            selected = tuple(
                record for record in selected if record.kind.value == kind
            )
        if lib is not None:
            selected = tuple(
                record
                for record in selected
                if self._matches_lib(record=record, lib=lib)
            )
        return AntFarmSymbolCollection(records=selected, trace=self._trace)

    @property
    def catalog(self) -> AntFarmSymbolCollection:
        """Return this collection as the chainable catalog object."""
        return self

    @property
    def paths(self) -> tuple[str, ...]:
        """Return every symbol path."""
        return tuple(self._path(record=record) for record in self._records)

    @property
    def names(self) -> tuple[str, ...]:
        """Return every symbol display name."""
        return tuple(record.name for record in self._records)

    @property
    def definitions(self) -> tuple[AST, ...]:
        """Return all available definition nodes."""
        nodes: list[AST] = []
        for view in self:
            node: AST | None = view.definition
            if node is not None:
                nodes.append(node)
        return tuple(nodes)

    def imports(
        self,
        *,
        lib: str | None = None,
        name: str | None = None,
    ) -> AntFarmSymbolCollection:
        """Return inspected import symbols, optionally filtered."""
        selected: (
            tuple[CatalogSymbolRecord, ...]
            | tuple[LocalImportSymbolRecord, ...]
        ) = tuple(
            record
            for record in self._records
            if isinstance(record, LocalImportSymbolRecord)
        )
        if lib is not None:
            selected = tuple(
                record
                for record in selected
                if self._matches_lib(record=record, lib=lib)
            )
        if name is not None:
            selected = tuple(
                record for record in selected if record.name == name
            )
        return AntFarmSymbolCollection(records=selected, trace=self._trace)

    def trace(
        self,
        *,
        path: str | None = None,
        name: str | None = None,
    ) -> AntFarmSymbolCollection:
        """Return traceable in-file symbols, optionally filtered."""
        selected: (
            tuple[CatalogSymbolRecord, ...] | tuple[TraceableSymbolRecord, ...]
        ) = tuple(
            record
            for record in self._records
            if isinstance(record, TraceableSymbolRecord)
        )
        if path is not None:
            selected = tuple(
                record
                for record in selected
                if self._path(record=record) == path
            )
        if name is not None:
            selected = tuple(
                record for record in selected if record.name == name
            )
        return AntFarmSymbolCollection(records=selected, trace=self._trace)

    def first(self) -> AntFarmSymbolView | None:
        """Return the first symbol view when present."""
        if not self._records:
            return None
        return AntFarmSymbolView(record=self._records[0], trace=self._trace)

    def all(self) -> tuple[AntFarmSymbolView, ...]:
        """Return all symbol views as a tuple."""
        return tuple(self)

    def _path(self, *, record: CatalogSymbolRecord) -> str:
        """Return a stable path for one symbol record."""
        if isinstance(record, TraceableSymbolRecord):
            return record.text
        return record.path_text

    def _matches_lib(self, *, record: CatalogSymbolRecord, lib: str) -> bool:
        """Return whether a symbol belongs to an import library/module."""
        if not isinstance(record, LocalImportSymbolRecord):
            return False
        module: str | None = record.module
        if module is None:
            return lib == "relative"
        root: str = module.split(sep=".", maxsplit=1)[0]
        return lib in (module, root)


class AntFarmSemanticGraphParseUnparseToolkit(
    ImportInspectingTraceableSemanticGraphParseUnparseToolkit,
):
    """Toolkit that returns chainable ant-farm query results."""

    def parse_ant_farm(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
        import_config: LocalImportInspectionConfig | None = None,
    ) -> AntFarmParseResult:
        """Parse source and return a chainable ant-farm result."""
        result: ImportInspectingTraceableGraphParseResult = (
            self.parse_traceable_with_imports(
                source=source,
                filename=filename,
                import_config=import_config,
            )
        )
        return AntFarmParseResult(
            result=result,
            query=AntFarmQuery(
                catalog=result.symbol_catalog,
                trace=result.trace,
            ),
        )


class SwarmCapabilityProtocolFactory:
    """Create local protocol suggestions for conversion/narrowing evidence."""

    def for_conversion(self, *, name: str) -> SwarmProtocolSuggestion | None:
        """Return a protocol suggestion for a builtin conversion call."""
        method_data: tuple[str, TypeExpression] | None = (
            SwarmConversionTables.conversion_methods.get(
                name,
            )
        )
        if method_data is None:
            return None
        method_name: str = method_data[0]
        return_type: TypeExpression = method_data[1]
        protocol_name: str = f"ProtocolCan{name.title()}"
        return SwarmProtocolSuggestion(
            name=protocol_name,
            type_hint=Types.local(name=protocol_name),
            methods=(
                MethodSpec(
                    name=method_name,
                    arguments=(Args.self_arg(),),
                    returns=return_type,
                    docstring=(
                        f"Return the {name} representation required by "
                        f"{name}(...)."
                    ),
                ),
            ),
            reason=(
                f"Protocol for objects accepted by the builtin {name}(...) "
                "conversion."
            ),
        )


class SwarmEvidenceTypeAdapter:
    """Adapt propagated evidence across mutation-specific edges."""

    def __init__(self) -> None:
        """Initialize the adapter."""
        self._inspector: TypeExpressionInspector = TypeExpressionInspector()

    def adapt(
        self,
        *,
        evidence: SwarmTypeEvidence,
        edge: SwarmPropagationEdge,
    ) -> TypeExpression:
        """Return the type hint that should arrive through an edge."""
        if edge.kind is SwarmPropagationEdgeKind.APPEND_MUTATION:
            return Types.builtins.list_of(item=evidence.type_hint)
        if edge.kind is SwarmPropagationEdgeKind.EXTEND_MUTATION:
            return Types.abc.iterable.of(arguments=(evidence.type_hint,))
        if edge.kind is SwarmPropagationEdgeKind.SET_ADD_MUTATION:
            return Types.builtins.set_of(item=evidence.type_hint)
        if edge.kind is SwarmPropagationEdgeKind.CONTAINER:
            return Types.builtins.list_of(item=evidence.type_hint)
        return evidence.type_hint

    def adapt_backward(
        self,
        *,
        evidence: SwarmTypeEvidence,
        edge: SwarmPropagationEdge,
    ) -> TypeExpression:
        """Return the type hint that should flow backward through an edge."""
        if edge.kind in {
            SwarmPropagationEdgeKind.APPEND_MUTATION,
            SwarmPropagationEdgeKind.EXTEND_MUTATION,
            SwarmPropagationEdgeKind.SET_ADD_MUTATION,
            SwarmPropagationEdgeKind.CONTAINER,
        }:
            return self._first_generic_argument(value=evidence.type_hint)
        return evidence.type_hint

    def _first_generic_argument(
        self,
        *,
        value: TypeExpression,
    ) -> TypeExpression:
        """Return first generic argument when present, else original type."""
        if not isinstance(value, GenericTypeRef):
            return value
        if not value.arguments:
            return value
        return value.arguments[0]


class SwarmPropagationGraph:
    """High-level type-evidence propagation graph over traceable paths."""

    def __init__(self) -> None:
        """Initialize propagation storage."""
        self._edges: list[SwarmPropagationEdge] = []
        self._outgoing: dict[
            TraceablePathText,
            list[SwarmPropagationEdge],
        ] = {}
        self._incoming: dict[
            TraceablePathText,
            list[SwarmPropagationEdge],
        ] = {}
        self._states: dict[TraceablePathText, SwarmPathState] = {}
        self.protocol_suggestions: dict[str, SwarmProtocolSuggestion] = {}
        self._adapter: SwarmEvidenceTypeAdapter = SwarmEvidenceTypeAdapter()

    @property
    def edges(self) -> tuple[SwarmPropagationEdge, ...]:
        """Return all propagation edges."""
        return tuple(self._edges)

    @property
    def states(self) -> tuple[SwarmPathState, ...]:
        """Return all path states."""
        return tuple(self._states.values())

    def add_edge(self, *, edge: SwarmPropagationEdge) -> None:
        """Add an edge to the propagation graph."""
        self._edges.append(edge)
        self._outgoing.setdefault(edge.source_path, []).append(edge)
        self._incoming.setdefault(edge.target_path, []).append(edge)
        self._ensure_state(path=edge.source_path)
        self._ensure_state(path=edge.target_path)

    def add_protocol_suggestion(
        self,
        *,
        suggestion: SwarmProtocolSuggestion,
    ) -> None:
        """Register a synthesized protocol suggestion."""
        self.protocol_suggestions.setdefault(suggestion.name, suggestion)

    def add_seed(self, *, evidence: SwarmTypeEvidence) -> None:
        """Add initial evidence to its current path."""
        self._ensure_state(path=evidence.current_path).add(evidence=evidence)

    def state(self, *, path: TraceablePathText) -> SwarmPathState | None:
        """Return evidence state for one path."""
        return self._states.get(path)

    def solve(self, *, path: TraceablePathText) -> TypeExpression | None:
        """Return the solved type for one path."""
        state: SwarmPathState | None = self.state(path=path)
        if state is None:
            return None
        return state.solved()

    def propagate(self, *, config: SwarmPropagationConfig) -> None:
        """Run bidirectional front/backward evidence propagation."""
        queue: list[SwarmTypeEvidence] = [
            item for state in self._states.values() for item in state.items
        ]
        index: int = 0
        while index < len(queue):
            evidence: SwarmTypeEvidence = queue[index]
            index += 1
            if evidence.depth >= config.max_depth:
                continue
            next_items: tuple[SwarmTypeEvidence, ...] = self._expanded(
                evidence=evidence,
                config=config,
            )
            for next_evidence in next_items:
                if next_evidence.confidence < config.minimum_confidence:
                    continue
                state: SwarmPathState = self._ensure_state(
                    path=next_evidence.current_path,
                )
                if state.add(evidence=next_evidence):
                    queue.append(next_evidence)

    def _expanded(
        self,
        *,
        evidence: SwarmTypeEvidence,
        config: SwarmPropagationConfig,
    ) -> tuple[SwarmTypeEvidence, ...]:
        """Return all one-step propagated evidence items."""
        forward_items: tuple[SwarmTypeEvidence, ...] = tuple(
            self._move(
                evidence=evidence,
                edge=edge,
                factor=edge.forward_confidence * config.confidence_decay,
            )
            for edge in self._outgoing.get(evidence.current_path, [])
        )
        backward_items: tuple[SwarmTypeEvidence, ...] = tuple(
            self._move_backward(
                evidence=evidence,
                edge=edge,
                factor=edge.backward_confidence
                * config.confidence_decay
                * config.backward_decay,
            )
            for edge in self._incoming.get(evidence.current_path, [])
        )
        return (*forward_items, *backward_items)

    def _move(
        self,
        *,
        evidence: SwarmTypeEvidence,
        edge: SwarmPropagationEdge,
        factor: float,
    ) -> SwarmTypeEvidence:
        """Move evidence along one edge."""
        adapted_type: TypeExpression = self._adapter.adapt(
            evidence=evidence,
            edge=edge,
        )
        return SwarmTypeEvidence(
            type_hint=adapted_type,
            polarity=edge.polarity,
            confidence=evidence.confidence * factor,
            source_path=evidence.source_path,
            current_path=edge.target_path,
            depth=evidence.depth + 1,
            reason=edge.label or edge.kind.value,
        )

    def _move_backward(
        self,
        *,
        evidence: SwarmTypeEvidence,
        edge: SwarmPropagationEdge,
        factor: float,
    ) -> SwarmTypeEvidence:
        """Move evidence backward along one edge."""
        adapted_type: TypeExpression = self._adapter.adapt_backward(
            evidence=evidence,
            edge=edge,
        )
        return SwarmTypeEvidence(
            type_hint=adapted_type,
            polarity=edge.polarity,
            confidence=evidence.confidence * factor,
            source_path=evidence.source_path,
            current_path=edge.source_path,
            depth=evidence.depth + 1,
            reason=edge.label or edge.kind.value,
        )

    def _ensure_state(self, *, path: TraceablePathText) -> SwarmPathState:
        """Return existing state or create an empty one."""
        state: SwarmPathState | None = self._states.get(path)
        if state is not None:
            return state
        state = SwarmPathState(path=path)
        self._states[path] = state
        return state


class SwarmPathHelper:
    """Resolve AST nodes and function internals to traceable path texts."""

    def __init__(self, *, trace: TraceablePathIndex) -> None:
        """Initialize path helper."""
        self._trace: TraceablePathIndex = trace

    def path_for_ast(self, *, node: AST) -> TraceableQualifiedPath | None:
        """Return a trace path for an AST node when possible."""
        if isinstance(node, Name):
            return self._path_for_name(node=node)
        if isinstance(node, Attribute):
            return self._path_for_attribute(node=node)
        node_id: IndexedNodeId | None = self._trace.graph.node_id_for_ast(
            node=node,
        )
        if node_id is None:
            return None
        return self._temporary_path(node_id=node_id)

    def _path_for_attribute(
        self,
        *,
        node: Attribute,
    ) -> TraceableQualifiedPath | None:
        """Return a trace path for an attribute expression."""
        owner_path: TraceableQualifiedPath | None = self.path_for_ast(
            node=node.value,
        )
        if owner_path is None:
            return None
        return owner_path.child(
            name=node.attr,
            kind=TraceablePathKind.ATTRIBUTE,
        )

    def _path_for_name(self, *, node: Name) -> TraceableQualifiedPath | None:
        """Return a trace path for a name expression."""
        node_id: IndexedNodeId | None = self._trace.graph.node_id_for_ast(
            node=node,
        )
        if node_id is None:
            return None
        graph_node: IndexedSemanticGraphNode = self._trace.graph.node(
            node_id=node_id,
        )
        symbol: IndexedSemanticSymbol | None = self._trace.graph.lookup_symbol(
            name=node.id,
            scope_id=graph_node.scope_id,
        )
        if symbol is None:
            return None
        trace_symbol_id: TraceableSymbolId | None = (
            self._trace.symbols_by_indexed_id.get(symbol.id)
        )
        if trace_symbol_id is None:
            return None
        return self._trace.symbols_by_id[trace_symbol_id].path

    def _temporary_path(
        self,
        *,
        node_id: IndexedNodeId,
    ) -> TraceableQualifiedPath:
        """Return a stable temporary path for an anonymous node."""
        graph_node: IndexedSemanticGraphNode = self._trace.graph.node(
            node_id=node_id,
        )
        scope_path: TraceableQualifiedPath = self._trace.scopes_by_id[
            graph_node.scope_id
        ].path
        return scope_path.child(
            name=f"tmp_{node_id}",
            kind=TraceablePathKind.TEMPORARY,
        )

    def text_for_ast(self, *, node: AST) -> TraceablePathText | None:
        """Return trace path text for an AST node when possible."""
        path: TraceableQualifiedPath | None = self.path_for_ast(node=node)
        if path is None:
            return None
        return path.text

    def function_record_for_call(
        self,
        *,
        call: Call,
    ) -> TraceableSymbolRecord | None:
        """Return the function symbol called by a simple name call."""
        if not isinstance(call.func, Name):
            return None
        candidates: tuple[TraceableSymbolRecord, ...] = (
            self._trace.symbols_named(
                name=call.func.id,
            )
        )
        for candidate in candidates:
            if candidate.kind is SemanticSymbolKind.FUNCTION:
                return candidate
        return None

    def argument_path(
        self,
        *,
        function: TraceableSymbolRecord,
        name: str,
    ) -> TraceablePathText | None:
        """Return the canonical path for a function argument."""
        for symbol in self._trace.symbols_under(path=function.path):
            if (
                symbol.name == name
                and symbol.kind is SemanticSymbolKind.ARGUMENT
            ):
                return symbol.text
        return None

    def return_path(
        self,
        *,
        function: TraceableSymbolRecord,
    ) -> TraceablePathText:
        """Return the synthetic return path for a function."""
        return function.path.child(
            name="return",
            kind=TraceablePathKind.SYMBOL,
        ).text


class SwarmSeedBuilder:
    """Create initial swarming evidence."""

    def __init__(self, *, trace: TraceablePathIndex) -> None:
        """Initialize seed builder."""
        self._trace: TraceablePathIndex = trace
        self._paths: SwarmPathHelper = SwarmPathHelper(trace=trace)
        self._protocols: SwarmCapabilityProtocolFactory = (
            SwarmCapabilityProtocolFactory()
        )

    def add_initial_evidence(self, *, graph: SwarmPropagationGraph) -> None:
        """Seed symbol evidence and builtin conversion call evidence."""
        self._add_symbol_evidence(graph=graph)
        self._add_conversion_call_evidence(graph=graph)

    def _add_symbol_evidence(self, *, graph: SwarmPropagationGraph) -> None:
        """Seed evidence already attached to traceable symbols."""
        for symbol in self._trace.symbols_by_id.values():
            for evidence in symbol.evidence:
                graph.add_seed(
                    evidence=SwarmTypeEvidence(
                        type_hint=evidence.type_hint,
                        polarity=self._polarity_for(kind=evidence.kind),
                        confidence=evidence.confidence,
                        source_path=symbol.text,
                        current_path=symbol.text,
                        depth=0,
                        reason=evidence.reason,
                    ),
                )

    def _add_conversion_call_evidence(
        self,
        *,
        graph: SwarmPropagationGraph,
    ) -> None:
        """Seed builtin conversion evidence."""
        for node in self._trace.graph.nodes:
            if not isinstance(node.ast_node, Call):
                continue
            if not isinstance(node.ast_node.func, Name):
                continue
            conversion_name: str = node.ast_node.func.id
            return_type: TypeExpression | None = (
                SwarmConversionTables.conversion_return_types.get(
                    conversion_name,
                )
            )
            if return_type is None:
                continue
            call_path: TraceablePathText | None = self._paths.text_for_ast(
                node=node.ast_node,
            )
            if call_path is None:
                continue
            graph.add_seed(
                evidence=SwarmTypeEvidence(
                    type_hint=return_type,
                    polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                    confidence=0.96,
                    source_path=call_path,
                    current_path=call_path,
                    depth=0,
                    reason=f"builtin {conversion_name}(...) return type",
                ),
            )
            self._add_conversion_argument_narrowing(
                graph=graph,
                call=node.ast_node,
                conversion_name=conversion_name,
            )

    def _add_conversion_argument_narrowing(
        self,
        *,
        graph: SwarmPropagationGraph,
        call: Call,
        conversion_name: str,
    ) -> None:
        """Add protocol narrowing evidence for conversion call arguments."""
        if not call.args:
            return
        argument_path: TraceablePathText | None = self._paths.text_for_ast(
            node=call.args[0],
        )
        if argument_path is None:
            return
        suggestion: SwarmProtocolSuggestion | None = (
            self._protocols.for_conversion(
                name=conversion_name,
            )
        )
        if suggestion is None:
            return
        graph.add_protocol_suggestion(suggestion=suggestion)
        graph.add_seed(
            evidence=SwarmTypeEvidence(
                type_hint=suggestion.type_hint,
                polarity=SwarmEvidencePolarity.NARROWS,
                confidence=0.78,
                source_path=argument_path,
                current_path=argument_path,
                depth=0,
                reason=f"argument accepted by {conversion_name}(...)",
            ),
        )

    def _polarity_for(
        self,
        *,
        kind: TypeEvidenceKind,
    ) -> SwarmEvidencePolarity:
        """Return propagation polarity for an existing evidence kind."""
        if kind is TypeEvidenceKind.ANNOTATION:
            return SwarmEvidencePolarity.DECLARES
        if kind is TypeEvidenceKind.COMPARISON_LITERAL:
            return SwarmEvidencePolarity.NARROWS
        return SwarmEvidencePolarity.SUPPORTS_UNION


class SwarmNetworkBuilder:
    """Build swarming propagation edges from traceable graph semantics."""

    def __init__(self, *, trace: TraceablePathIndex) -> None:
        """Initialize network builder."""
        self._trace: TraceablePathIndex = trace
        self._paths: SwarmPathHelper = SwarmPathHelper(trace=trace)

    def build(self) -> SwarmPropagationGraph:
        """Build and return a propagation graph."""
        graph: SwarmPropagationGraph = SwarmPropagationGraph()
        self._add_traceable_value_flows(graph=graph)
        self._add_container_edges(graph=graph)
        self._add_function_edges(graph=graph)
        self._add_call_edges(graph=graph)
        self._add_mutation_edges(graph=graph)
        SwarmSeedBuilder(trace=self._trace).add_initial_evidence(graph=graph)
        return graph

    def _add_traceable_value_flows(
        self,
        *,
        graph: SwarmPropagationGraph,
    ) -> None:
        """Add edges from generic traceable value-flow records."""
        for flow in self._trace.value_flows:
            graph.add_edge(
                edge=SwarmPropagationEdge(
                    source_path=flow.source_path.text,
                    target_path=flow.target_path.text,
                    kind=SwarmPropagationEdgeKind.ASSIGNMENT,
                    forward_confidence=0.94,
                    backward_confidence=0.56,
                    polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                    label=flow.label or flow.relation.value,
                ),
            )

    def _add_container_edges(self, *, graph: SwarmPropagationGraph) -> None:
        """Connect container slots back to their owning containers."""
        for slot in self._trace.container_slots:
            graph.add_edge(
                edge=SwarmPropagationEdge(
                    source_path=slot.value_path.text,
                    target_path=slot.container_path.text,
                    kind=SwarmPropagationEdgeKind.CONTAINER,
                    forward_confidence=0.88,
                    backward_confidence=0.28,
                    polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                    label=slot.relation.value,
                ),
            )

    def _add_function_edges(self, *, graph: SwarmPropagationGraph) -> None:
        """Connect returned expressions to synthetic function return paths."""
        for function in self._function_symbols():
            node: AST | None = self._definition_node(symbol=function)
            if not isinstance(node, FunctionDef | AsyncFunctionDef):
                continue
            return_path: TraceablePathText = self._paths.return_path(
                function=function,
            )
            for return_node in self._returns_in(function=node):
                if return_node.value is None:
                    continue
                value_path: TraceablePathText | None = (
                    self._paths.text_for_ast(
                        node=return_node.value,
                    )
                )
                if value_path is None:
                    continue
                graph.add_edge(
                    edge=SwarmPropagationEdge(
                        source_path=value_path,
                        target_path=return_path,
                        kind=SwarmPropagationEdgeKind.RETURN_VALUE,
                        forward_confidence=0.95,
                        backward_confidence=0.48,
                        polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                        label=f"return from {function.text}",
                    ),
                )

    def _add_call_edges(self, *, graph: SwarmPropagationGraph) -> None:
        """Connect actual call arguments and function return paths."""
        for node in self._trace.graph.nodes:
            if not isinstance(node.ast_node, Call):
                continue
            function: TraceableSymbolRecord | None = (
                self._paths.function_record_for_call(call=node.ast_node)
            )
            if function is None:
                continue
            call_path: TraceablePathText | None = self._paths.text_for_ast(
                node=node.ast_node,
            )
            if call_path is None:
                continue
            self._add_call_return_edge(
                graph=graph,
                function=function,
                call_path=call_path,
            )
            self._add_call_argument_edges(
                graph=graph,
                function=function,
                call=node.ast_node,
            )

    def _add_call_return_edge(
        self,
        *,
        graph: SwarmPropagationGraph,
        function: TraceableSymbolRecord,
        call_path: TraceablePathText,
    ) -> None:
        """Connect a function return path to one call expression."""
        graph.add_edge(
            edge=SwarmPropagationEdge(
                source_path=self._paths.return_path(function=function),
                target_path=call_path,
                kind=SwarmPropagationEdgeKind.CALL_RETURN,
                forward_confidence=0.91,
                backward_confidence=0.35,
                polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                label=f"call result from {function.text}",
            ),
        )

    def _add_call_argument_edges(
        self,
        *,
        graph: SwarmPropagationGraph,
        function: TraceableSymbolRecord,
        call: Call,
    ) -> None:
        """Connect actual call arguments to formal parameter paths."""
        function_node: AST | None = self._definition_node(symbol=function)
        if not isinstance(function_node, FunctionDef | AsyncFunctionDef):
            return
        argument_names: tuple[str, ...] = tuple(
            argument.arg for argument in function_node.args.args
        )
        for index, actual in enumerate(iterable=call.args):
            if index >= len(argument_names):
                break
            actual_path: TraceablePathText | None = self._paths.text_for_ast(
                node=actual,
            )
            formal_path: TraceablePathText | None = self._paths.argument_path(
                function=function,
                name=argument_names[index],
            )
            if actual_path is None or formal_path is None:
                continue
            graph.add_edge(
                edge=SwarmPropagationEdge(
                    source_path=actual_path,
                    target_path=formal_path,
                    kind=SwarmPropagationEdgeKind.CALL_ARGUMENT,
                    forward_confidence=0.9,
                    backward_confidence=0.42,
                    polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                    label=(
                        f"argument {argument_names[index]} for {function.text}"
                    ),
                ),
            )

    def _add_mutation_edges(self, *, graph: SwarmPropagationGraph) -> None:
        """Add edges for collection mutations such as ``a.append(x)``."""
        for node in self._trace.graph.nodes:
            if not isinstance(node.ast_node, Call):
                continue
            if not isinstance(node.ast_node.func, Attribute):
                continue
            if not node.ast_node.args:
                continue
            owner_path: TraceablePathText | None = self._paths.text_for_ast(
                node=node.ast_node.func.value,
            )
            value_path: TraceablePathText | None = self._paths.text_for_ast(
                node=node.ast_node.args[0],
            )
            if owner_path is None or value_path is None:
                continue
            edge_kind: SwarmPropagationEdgeKind | None = self._mutation_kind(
                name=node.ast_node.func.attr,
            )
            if edge_kind is None:
                continue
            graph.add_edge(
                edge=SwarmPropagationEdge(
                    source_path=value_path,
                    target_path=owner_path,
                    kind=edge_kind,
                    forward_confidence=0.93,
                    backward_confidence=0.2,
                    polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                    label=f"{node.ast_node.func.attr}(...) mutation",
                ),
            )

    def _mutation_kind(self, *, name: str) -> SwarmPropagationEdgeKind | None:
        """Return edge kind for a mutating method name."""
        if name == "append":
            return SwarmPropagationEdgeKind.APPEND_MUTATION
        if name == "extend":
            return SwarmPropagationEdgeKind.EXTEND_MUTATION
        if name == "add":
            return SwarmPropagationEdgeKind.SET_ADD_MUTATION
        return None

    def _function_symbols(self) -> tuple[TraceableSymbolRecord, ...]:
        """Return all function symbols in the trace index."""
        return tuple(
            symbol
            for symbol in self._trace.symbols_by_id.values()
            if symbol.kind is SemanticSymbolKind.FUNCTION
        )

    def _definition_node(self, *, symbol: TraceableSymbolRecord) -> AST | None:
        """Return the AST definition node for a traceable symbol."""
        if symbol.definition_node_id is None:
            return None
        return self._trace.graph.node(
            node_id=symbol.definition_node_id,
        ).ast_node

    def _returns_in(
        self,
        *,
        function: SemanticFunctionNode,
    ) -> tuple[Return, ...]:
        """Return all return nodes lexically inside a function body."""
        return tuple(
            node for node in walk(node=function) if isinstance(node, Return)
        )


class SwarmTypeInferenceEngine:
    """Bidirectional ant-farm propagation engine for type inference."""

    def infer(
        self,
        *,
        trace: TraceablePathIndex,
        config: SwarmPropagationConfig | None = None,
    ) -> SwarmInferenceResult:
        """Build a propagation graph, swarm evidence, and solve lazily."""
        final_config: SwarmPropagationConfig = (
            config or SwarmPropagationConfig()
        )
        graph: SwarmPropagationGraph = SwarmNetworkBuilder(trace=trace).build()
        graph.propagate(config=final_config)
        return SwarmInferenceResult(graph=graph, config=final_config)


class SwarmResultQuery:
    """Callable/sliceable query facade for swarming results."""

    def __init__(self, *, result: SwarmInferenceResult) -> None:
        """Initialize query facade."""
        self._result: SwarmInferenceResult = result

    def __call__(self, *, path: TraceablePathText) -> SwarmSymbolView:
        """Return one swarming view by canonical path."""
        return SwarmSymbolView(path=path, result=self._result)

    @property
    def protocols(self) -> tuple[SwarmProtocolSuggestion, ...]:
        """Return synthesized protocol suggestions."""
        return self._result.protocol_suggestions

    @property
    def states(self) -> tuple[SwarmPathState, ...]:
        """Return every swarmed path state."""
        return self._result.graph.states


class SwarmAntFarmSemanticGraphParseUnparseToolkit(
    AntFarmSemanticGraphParseUnparseToolkit,
):
    """Toolkit that parses an ant farm and runs swarming type inference."""

    def parse_indexed(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> IndexedSemanticGraphParseResult:
        """Parse source into an indexed graph using the native module tree."""
        parsed: CommentAwareParseResult = self._parser.parse_comments(
            source=source,
        )
        model: ParsedSemanticModel = self._model_toolkit.parse_model(
            source=source,
            filename=filename,
        )
        module: Module = parse(source=source, mode="exec")
        graph: IndexedSemanticAstGraph = IndexedSemanticGraphBuilder().build(
            root=module,
        )
        return IndexedSemanticGraphParseResult(
            source=source,
            filename=filename,
            parsed=parsed,
            model=model,
            graph=graph,
        )

    def parse_swarm_ant_farm(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
        import_config: LocalImportInspectionConfig | None = None,
        swarm_config: SwarmPropagationConfig | None = None,
    ) -> SwarmAntFarmParseResult:
        """Parse code, build ant farm, and run bidirectional type swarming."""
        ant_farm: AntFarmParseResult = self.parse_ant_farm(
            source=source,
            filename=filename,
            import_config=import_config,
        )
        swarm_result: SwarmInferenceResult = SwarmTypeInferenceEngine().infer(
            trace=ant_farm.trace,
            config=swarm_config,
        )
        return SwarmAntFarmParseResult(
            ant_farm=ant_farm,
            swarm_result=swarm_result,
        )


class TypeshedTypeExpressionParser:
    """Convert stub annotation nodes."""

    def parse_annotation(self, *, node: expr | None) -> TypeExpression:
        """Return a semantic type expression for a stub annotation node."""
        result: TypeExpression
        if node is None:
            result = Types.object

        elif isinstance(node, Name):
            result = self._name(node=node)

        elif isinstance(node, Constant):
            result = self._constant(node=node)

        elif isinstance(node, Attribute):
            result = self._attribute(node=node)

        elif isinstance(node, Subscript):
            result = self._subscript(node=node)

        elif isinstance(node, BinOp) and isinstance(node.op, BitOr):
            result = self._union_from_binop(node=node)

        elif isinstance(node, AstTuple):
            result = Types.builtins.tuple_of(
                items=tuple(
                    self.parse_annotation(node=item) for item in node.elts
                ),
            )
        else:
            result = AstBackedTypeExpression(node=node)

        return result

    def _name(self, *, node: Name) -> TypeExpression:
        """Parse a simple name annotation."""
        builtin: TypeExpression | None = TypeshedNameTables.builtins.get(
            node.id,
        )
        if builtin is not None:
            return builtin
        typing_name: TypeExpression | None = (
            TypeshedNameTables.typing_names.get(node.id)
        )
        if typing_name is not None:
            return typing_name
        return Types.local(name=node.id)

    def _constant(self, *, node: Constant) -> TypeExpression:
        """Parse a constant annotation fragment."""
        if node.value is None:
            return Types.none
        if node.value is Ellipsis:
            return Types.ellipsis
        return AstBackedTypeExpression(node=node)

    def _attribute(self, *, node: Attribute) -> TypeExpression:
        """Parse a qualified annotation reference."""
        parts: tuple[str, ...] = self._attribute_parts(node=node)
        if not parts:
            return AstBackedTypeExpression(node=node)
        return self._qualified(parts=parts)

    def _subscript(self, *, node: Subscript) -> TypeExpression:
        """Parse a subscripted annotation."""
        origin: TypeExpression = self.parse_annotation(node=node.value)
        arguments: tuple[TypeExpression, ...] = self._subscript_arguments(
            node=node.slice,
        )
        return self._canonical_generic(origin=origin, arguments=arguments)

    def _union_from_binop(self, *, node: BinOp) -> TypeExpression:
        """Parse a PEP 604 union annotation."""
        left: TypeExpression = self.parse_annotation(node=node.left)
        right: TypeExpression = self.parse_annotation(node=node.right)
        return Types.union(options=(left, right))

    def _subscript_arguments(
        self,
        *,
        node: expr,
    ) -> tuple[TypeExpression, ...]:
        """Return semantic arguments from a subscript slice."""
        if isinstance(node, AstTuple):
            return tuple(
                self.parse_annotation(node=item) for item in node.elts
            )
        if isinstance(node, AstList):
            return (
                CallableParameterListRef(
                    parameters=tuple(
                        self.parse_annotation(node=item) for item in node.elts
                    ),
                ),
            )
        return (self.parse_annotation(node=node),)

    def _canonical_generic(
        self,
        *,
        origin: TypeExpression,
        arguments: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Return a canonical generic expression when recognized."""
        key: str = origin.key()
        result: TypeExpression
        if key == "builtins:list":
            result = BuiltinTypeHints.list.of(
                arguments=arguments,
            )
        elif key == "builtins:dict":
            result = BuiltinTypeHints.dict.of(
                arguments=arguments,
            )
        elif key == "builtins:set":
            result = BuiltinTypeHints.set.of(
                arguments=arguments,
            )
        elif key == "builtins:frozenset":
            result = BuiltinTypeHints.frozenset.of(arguments=arguments)
        elif key == "builtins:tuple":
            result = BuiltinTypeHints.tuple.of(arguments=arguments)
        elif key == "builtins:type":
            result = BuiltinTypeHints.type.of(
                arguments=arguments,
            )
        elif key.endswith(":Callable"):
            result = self._callable(
                arguments=arguments,
            )
        elif key.endswith(":Union"):
            result = Types.union(
                options=arguments,
            )
        else:
            result = GenericTypeRef(
                origin=origin,
                arguments=arguments,
            )
        return result

    def _callable(
        self,
        *,
        arguments: tuple[TypeExpression, ...],
    ) -> TypeExpression:
        """Return a canonical callable from parsed arguments."""
        if len(arguments) != Constants.two_item_count:
            return GenericTypeRef(
                origin=DirectTypeRefs.imported(
                    module_parts=("collections", "abc"),
                    name="Callable",
                ),
                arguments=arguments,
            )
        first: TypeExpression = arguments[0]
        returns: TypeExpression = arguments[1]
        if isinstance(first, CallableParameterListRef):
            return FlexibleCallableTypeRef(
                parameters=first.parameters,
                returns=returns,
            )
        if isinstance(first, EllipsisTypeRef):
            return FlexibleCallableTypeRef(parameters=None, returns=returns)
        return FlexibleCallableTypeRef(parameters=first, returns=returns)

    def _qualified(self, *, parts: tuple[str, ...]) -> TypeExpression:
        """Return a canonical imported type for qualified names."""
        if parts[0] == "typing" and len(parts) == Constants.two_item_count:
            return self._typing_qualified(name=parts[1])
        if (
            parts[0] == "collections"
            and len(parts) == Constants.three_item_count
            and parts[1] == "abc"
        ):
            return DirectTypeRefs.imported(
                module_parts=("collections", "abc"),
                name=parts[2],
            )
        return DirectTypeRefs.imported(module_parts=parts[:-1], name=parts[-1])

    def _typing_qualified(self, *, name: str) -> TypeExpression:
        """Return canonical replacement for a typing-qualified name."""
        if name == "Any":
            return Types.object
        if name == "Optional":
            return Types.local(name="Optional")
        if name == "Union":
            return Types.local(name="Union")
        if name == "Callable":
            return DirectTypeRefs.imported(
                module_parts=("collections", "abc"),
                name="Callable",
            )
        return DirectTypeRefs.imported(module_parts=("typing",), name=name)

    def _attribute_parts(self, *, node: Attribute) -> tuple[str, ...]:
        """Return dotted parts for an attribute expression."""
        parts: list[str] = [node.attr]
        current: expr = node.value
        while isinstance(current, Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, Name):
            parts.append(current.id)
            return tuple(reversed(parts))
        return ()


class TypeshedStubParser:
    """Parse Python stub files into a lightweight typeshed signature model."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._type_parser: TypeshedTypeExpressionParser = (
            TypeshedTypeExpressionParser()
        )

    def parse_file(self, *, path: Path, module: str) -> TypeshedModuleModel:
        """Parse one stub file into a module model."""
        source: str = path.read_text(encoding="utf-8")
        return self.parse_source(
            source=source,
            module=module,
            source_name=str(object=path),
        )

    def parse_source(
        self,
        *,
        source: str,
        module: str,
        source_name: str,
    ) -> TypeshedModuleModel:
        """Parse stub source into a module model."""
        tree: Module = parse(source=source, filename=source_name, mode="exec")
        classes: list[TypeshedClassModel] = []
        functions: list[TypeshedSignatureModel] = []
        for node in tree.body:
            if isinstance(node, ClassDef):
                classes.append(
                    self._class(node=node, module=module, source=source_name),
                )
            elif isinstance(node, FunctionDef | AsyncFunctionDef):
                functions.append(
                    self._signature(
                        node=node,
                        owner="",
                        module=module,
                        source=source_name,
                    ),
                )
        return TypeshedModuleModel(
            module=module,
            classes=tuple(classes),
            functions=tuple(functions),
            source=source_name,
        )

    def _class(
        self,
        *,
        node: ClassDef,
        module: str,
        source: str,
    ) -> TypeshedClassModel:
        """Parse one class definition from a stub file."""
        methods: list[TypeshedSignatureModel] = [
            self._signature(
                node=item,
                owner=node.name,
                module=module,
                source=source,
            )
            for item in node.body
            if isinstance(item, FunctionDef | AsyncFunctionDef)
        ]
        return TypeshedClassModel(
            name=node.name,
            methods=tuple(methods),
            module=module,
            source=source,
        )

    def _signature(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        owner: str,
        module: str,
        source: str,
    ) -> TypeshedSignatureModel:
        """Parse one function signature."""
        return TypeshedSignatureModel(
            owner=owner,
            name=node.name,
            parameters=self._parameters(arguments=node.args),
            returns=self._type_parser.parse_annotation(node=node.returns),
            module=module,
            confidence=0.92,
            source=source,
        )

    def _parameters(
        self,
        *,
        arguments: ast_arguments,
    ) -> tuple[TypeshedParameterModel, ...]:
        """Parse all parameters from an AST arguments node."""
        result: list[TypeshedParameterModel] = []
        result.extend(
            self._parameter(
                node=item,
                kind=TypeshedParameterKind.POSITIONAL_ONLY,
                has_default=False,
            )
            for item in arguments.posonlyargs
        )
        result.extend(
            self._parameter(
                node=item,
                kind=TypeshedParameterKind.POSITIONAL_OR_KEYWORD,
                has_default=False,
            )
            for item in arguments.args
        )
        if arguments.vararg is not None:
            result.append(
                self._parameter(
                    node=arguments.vararg,
                    kind=TypeshedParameterKind.VAR_POSITIONAL,
                    has_default=False,
                ),
            )
        result.extend(
            self._parameter(
                node=item,
                kind=TypeshedParameterKind.KEYWORD_ONLY,
                has_default=default is not None,
            )
            for item, default in zip(
                arguments.kwonlyargs,
                arguments.kw_defaults,
                strict=True,
            )
        )
        if arguments.kwarg is not None:
            result.append(
                self._parameter(
                    node=arguments.kwarg,
                    kind=TypeshedParameterKind.VAR_KEYWORD,
                    has_default=False,
                ),
            )
        return tuple(result)

    def _parameter(
        self,
        *,
        node: arg,
        kind: TypeshedParameterKind,
        has_default: bool,
    ) -> TypeshedParameterModel:
        """Parse one parameter model."""
        return TypeshedParameterModel(
            name=node.arg,
            type_hint=self._type_parser.parse_annotation(node=node.annotation),
            kind=kind,
            has_default=has_default,
        )


class TypeshedSignatureCatalog:
    """Lookup table for typeshed and fallback signature models."""

    def __init__(self) -> None:
        """Initialize empty catalog indexes."""
        self._methods: dict[tuple[str, str], list[TypeshedSignatureModel]] = {}
        self._functions: dict[str, list[TypeshedSignatureModel]] = {}
        self._classes: dict[str, TypeshedClassModel] = {}
        self._modules: dict[str, TypeshedModuleModel] = {}

    @property
    def modules(self) -> tuple[TypeshedModuleModel, ...]:
        """Return all loaded modules."""
        return tuple(self._modules.values())

    @property
    def classes(self) -> tuple[TypeshedClassModel, ...]:
        """Return all loaded classes."""
        return tuple(self._classes.values())

    @property
    def signatures(self) -> tuple[TypeshedSignatureModel, ...]:
        """Return all loaded signatures."""
        method_items: tuple[TypeshedSignatureModel, ...] = tuple(
            item for values in self._methods.values() for item in values
        )
        function_items: tuple[TypeshedSignatureModel, ...] = tuple(
            item for values in self._functions.values() for item in values
        )
        return (*method_items, *function_items)

    def add_module(self, *, module: TypeshedModuleModel) -> None:
        """Add a parsed module to the catalog."""
        self._modules[module.module] = module
        for function in module.functions:
            self.add_signature(signature=function)
        for class_model in module.classes:
            self._classes[class_model.name] = class_model
            for method in class_model.methods:
                self.add_signature(signature=method)

    def add_signature(self, *, signature: TypeshedSignatureModel) -> None:
        """Add one signature to the catalog."""
        if signature.owner:
            self._methods.setdefault(
                (signature.owner, signature.name),
                [],
            ).append(signature)
            return
        self._functions.setdefault(signature.name, []).append(signature)

    def method(
        self,
        *,
        owner: str,
        name: str,
    ) -> tuple[TypeshedSignatureModel, ...]:
        """Return method signatures by owner and method name."""
        return tuple(self._methods.get((owner, name), ()))

    def function(self, *, name: str) -> tuple[TypeshedSignatureModel, ...]:
        """Return function signatures by name."""
        return tuple(self._functions.get(name, ()))

    def __iter__(self) -> Iterator[TypeshedSignatureModel]:
        """Iterate over every signature in the catalog."""
        return iter(self.signatures)


class BuiltinFallbackSignatureFactory:
    """Create high-value builtin/operator signatures without external stubs."""

    def build(self) -> tuple[TypeshedSignatureModel, ...]:
        """Return builtins fallback signatures used by swarm inference."""
        t_ref: TypeExpression = Types.params.t
        k_ref: TypeExpression = Types.params.k
        v_ref: TypeExpression = Types.params.v
        list_t: TypeExpression = Types.builtins.list_of(item=t_ref)
        set_t: TypeExpression = Types.builtins.set_of(item=t_ref)
        dict_kv: TypeExpression = Types.builtins.dict_of(
            keys=k_ref,
            values=v_ref,
        )
        iterable_t: TypeExpression = Types.abc.iterable.of(arguments=(t_ref,))
        return (
            self._method(
                owner="list",
                name="append",
                parameters=(
                    self._param(name="self", hint=list_t),
                    self._param(name="item", hint=t_ref),
                ),
                returns=Types.none,
            ),
            self._method(
                owner="list",
                name="extend",
                parameters=(
                    self._param(name="self", hint=list_t),
                    self._param(name="items", hint=iterable_t),
                ),
                returns=Types.none,
            ),
            self._method(
                owner="list",
                name="__imul__",
                parameters=(
                    self._param(name="self", hint=list_t),
                    self._param(name="value", hint=Types.int),
                ),
                returns=list_t,
            ),
            self._method(
                owner="list",
                name="__mul__",
                parameters=(
                    self._param(name="self", hint=list_t),
                    self._param(name="value", hint=Types.int),
                ),
                returns=list_t,
            ),
            self._method(
                owner="set",
                name="add",
                parameters=(
                    self._param(name="self", hint=set_t),
                    self._param(name="item", hint=t_ref),
                ),
                returns=Types.none,
            ),
            self._method(
                owner="dict",
                name="__getitem__",
                parameters=(
                    self._param(name="self", hint=dict_kv),
                    self._param(name="key", hint=k_ref),
                ),
                returns=v_ref,
            ),
            self._method(
                owner="dict",
                name="__setitem__",
                parameters=(
                    self._param(name="self", hint=dict_kv),
                    self._param(name="key", hint=k_ref),
                    self._param(name="value", hint=v_ref),
                ),
                returns=Types.none,
            ),
            self._function(
                name="int",
                parameters=(self._param(name="value", hint=Types.object),),
                returns=Types.int,
            ),
            self._function(
                name="float",
                parameters=(self._param(name="value", hint=Types.object),),
                returns=Types.float,
            ),
            self._function(
                name="str",
                parameters=(self._param(name="value", hint=Types.object),),
                returns=Types.str,
            ),
        )

    def _method(
        self,
        *,
        owner: str,
        name: str,
        parameters: tuple[TypeshedParameterModel, ...],
        returns: TypeExpression,
    ) -> TypeshedSignatureModel:
        """Create a builtin method signature."""
        return TypeshedSignatureModel(
            owner=owner,
            name=name,
            parameters=parameters,
            returns=returns,
            module="builtins",
            confidence=0.98,
            source="builtin-fallback",
        )

    def _function(
        self,
        *,
        name: str,
        parameters: tuple[TypeshedParameterModel, ...],
        returns: TypeExpression,
    ) -> TypeshedSignatureModel:
        """Create a builtin function signature."""
        return TypeshedSignatureModel(
            owner="",
            name=name,
            parameters=parameters,
            returns=returns,
            module="builtins",
            confidence=0.97,
            source="builtin-fallback",
        )

    def _param(
        self,
        *,
        name: str,
        hint: TypeExpression,
    ) -> TypeshedParameterModel:
        """Create a fallback parameter model."""
        return TypeshedParameterModel(
            name=name,
            type_hint=hint,
            kind=TypeshedParameterKind.POSITIONAL_OR_KEYWORD,
        )


class TypeshedCatalogBuilder:
    """Build a signature catalog from typeshed/local stubs and fallbacks."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._parser: TypeshedStubParser = TypeshedStubParser()

    def build(
        self,
        *,
        config: TypeshedLookupConfig,
    ) -> TypeshedSignatureCatalog:
        """Build a catalog from configured stub roots."""
        catalog: TypeshedSignatureCatalog = TypeshedSignatureCatalog()
        if config.include_builtin_fallbacks:
            for signature in BuiltinFallbackSignatureFactory().build():
                catalog.add_signature(signature=signature)
        for root in self._roots(config=config):
            self._load_root(root=root, catalog=catalog)
        return catalog

    def _roots(self, *, config: TypeshedLookupConfig) -> tuple[Path, ...]:
        """Return existing configured roots in deterministic order."""
        roots: list[Path] = []
        if config.stdlib_root is not None:
            roots.append(config.stdlib_root)
        if config.typeshed_root is not None:
            roots.append(config.typeshed_root / "stdlib")
        roots.extend(config.stub_roots)
        return tuple(root for root in roots if root.exists())

    def _load_root(
        self,
        *,
        root: Path,
        catalog: TypeshedSignatureCatalog,
    ) -> None:
        """Load every pyi file from one root into the catalog."""
        paths: tuple[Path, ...] = tuple(sorted(root.rglob(pattern="*.pyi")))
        for path in paths:
            module_name: str = self._module_name(root=root, path=path)
            try:
                module: TypeshedModuleModel = self._parser.parse_file(
                    path=path,
                    module=module_name,
                )
            except SyntaxError:
                continue
            catalog.add_module(module=module)

    def _module_name(self, *, root: Path, path: Path) -> str:
        """Return module name for a stub path."""
        relative: Path = path.relative_to(root)
        parts: list[str] = list(relative.with_suffix(suffix="").parts)
        if parts and parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)


class SignatureTypeSubstitutor:
    """Apply simple type-parameter substitutions to signature expressions."""

    def substitute(
        self,
        *,
        value: TypeExpression,
        substitutions: dict[str, TypeExpression],
    ) -> TypeExpression:
        """Return value with local type parameters substituted."""
        if isinstance(value, LocalTypeRef):
            replacement: TypeExpression | None = substitutions.get(value.name)
            if replacement is not None:
                return replacement
            return value
        if isinstance(value, GenericTypeRef):
            return GenericTypeRef(
                origin=self.substitute(
                    value=value.origin,
                    substitutions=substitutions,
                ),
                arguments=tuple(
                    self.substitute(value=item, substitutions=substitutions)
                    for item in value.arguments
                ),
            )
        if isinstance(value, UnionTypeRef):
            return Types.union(
                options=tuple(
                    self.substitute(value=item, substitutions=substitutions)
                    for item in value.options
                ),
                collapse_limit=value.collapse_limit,
            )
        if isinstance(value, FlexibleCallableTypeRef):
            return self._callable(value=value, substitutions=substitutions)
        return value

    def _callable(
        self,
        *,
        value: FlexibleCallableTypeRef,
        substitutions: dict[str, TypeExpression],
    ) -> FlexibleCallableTypeRef:
        """Substitute callable parameters and return values."""
        if isinstance(value.parameters, tuple):
            parameters: CallableParameterSpec | TypeExpression | None = tuple(
                self.substitute(value=item, substitutions=substitutions)
                for item in value.parameters
            )
        else:
            parameters = value.parameters
        return FlexibleCallableTypeRef(
            parameters=parameters,
            returns=self.substitute(
                value=value.returns,
                substitutions=substitutions,
            ),
        )


class SignatureOwnerTypeMatcher:
    """Match a receiver type to catalog owner signatures and substitutions."""

    def match(
        self,
        *,
        receiver_type: TypeExpression,
        method_name: str,
        catalog: TypeshedSignatureCatalog,
    ) -> tuple[tuple[TypeshedSignatureModel, dict[str, TypeExpression]], ...]:
        """Return matching signatures and inferred substitutions."""
        owner_name: str = self._owner_name(value=receiver_type)
        signatures: tuple[TypeshedSignatureModel, ...] = catalog.method(
            owner=owner_name,
            name=method_name,
        )
        substitutions: dict[str, TypeExpression] = self._substitutions(
            value=receiver_type,
        )
        return tuple((signature, substitutions) for signature in signatures)

    def _owner_name(self, *, value: TypeExpression) -> str:
        """Return catalog owner name for a receiver type."""
        if isinstance(value, GenericTypeRef):
            return self._owner_name(value=value.origin)
        if isinstance(value, BuiltinTypeRef):
            return value.name
        if isinstance(value, ImportedTypeRef):
            return value.source.imported_name
        if isinstance(value, LocalTypeRef):
            return value.name
        return ""

    def _substitutions(
        self,
        *,
        value: TypeExpression,
    ) -> dict[str, TypeExpression]:
        """Return simple T/K/V substitutions from generic receiver values."""
        result: dict[str, TypeExpression] = {}
        if not isinstance(value, GenericTypeRef):
            return result
        owner_name: str = self._owner_name(value=value.origin)
        if owner_name in {"list", "set", "frozenset", "deque"}:
            self._bind_one(result=result, name="T", arguments=value.arguments)
        elif owner_name in {
            "dict",
            "defaultdict",
            "Mapping",
            "MutableMapping",
        }:
            self._bind_pair(result=result, arguments=value.arguments)
        return result

    def _bind_one(
        self,
        *,
        result: dict[str, TypeExpression],
        name: str,
        arguments: tuple[TypeExpression, ...],
    ) -> None:
        """Bind one type parameter if available."""
        if arguments:
            result[name] = arguments[0]

    def _bind_pair(
        self,
        *,
        result: dict[str, TypeExpression],
        arguments: tuple[TypeExpression, ...],
    ) -> None:
        """Bind K and V type parameters when available."""
        if len(arguments) >= Constants.two_item_count:
            result["K"] = arguments[0]
            result["V"] = arguments[1]


class MarkovConflictDetector:
    """Detect likely conflicts between high-confidence propagated evidence."""

    def conflicts_for(
        self,
        *,
        path: TraceablePathText,
        state: SwarmPathState,
    ) -> tuple[MarkovConflictWarning, ...]:
        """Return warnings for incompatible high-confidence candidates."""
        candidates: tuple[SwarmTypeEvidence, ...] = tuple(
            item
            for item in state.items
            if item.confidence >= Constants.conflict_confidence
        )
        unique: dict[str, TypeExpression] = {
            item.type_hint.key(): item.type_hint for item in candidates
        }
        if len(unique) <= 1:
            return ()
        solved: TypeExpression = state.solved()
        if isinstance(solved, UnionTypeRef):
            return ()
        return (
            MarkovConflictWarning(
                path=path,
                message=(
                    "high-confidence evidence collapsed to a narrower type"
                ),
                candidate_types=tuple(unique.values()),
                confidence=state.confidence,
            ),
        )


class MarkovExplanationBuilder:
    """Build confidence explanations from a swarm propagation result."""

    def __init__(self, *, result: SwarmInferenceResult) -> None:
        """Initialize explanation builder."""
        self._result: SwarmInferenceResult = result
        self._conflicts: MarkovConflictDetector = MarkovConflictDetector()

    def explanation_for(
        self,
        *,
        path: TraceablePathText,
    ) -> MarkovInferenceExplanation:
        """Return an explanation for one path."""
        state: SwarmPathState | None = self._result.state_for(path=path)
        if state is None:
            return MarkovInferenceExplanation(
                path=path,
                type_hint=None,
                confidence=0.0,
                steps=(),
                conflicts=(),
            )
        steps: tuple[MarkovInferenceStep, ...] = tuple(
            self._step(evidence=item) for item in state.items
        )
        return MarkovInferenceExplanation(
            path=path,
            type_hint=state.solved(),
            confidence=state.confidence,
            steps=steps,
            conflicts=self._conflicts.conflicts_for(path=path, state=state),
        )

    def all_explanations(self) -> tuple[MarkovInferenceExplanation, ...]:
        """Return explanations for every solved path."""
        return tuple(
            self.explanation_for(path=state.path)
            for state in self._result.graph.states
        )

    def _step(self, *, evidence: SwarmTypeEvidence) -> MarkovInferenceStep:
        """Convert raw evidence into an explanation step."""
        return MarkovInferenceStep(
            source_path=evidence.source_path,
            target_path=evidence.current_path,
            edge_label=evidence.reason,
            confidence=evidence.confidence,
            type_hint=evidence.type_hint,
        )


class TypeshedMethodInferenceSeeder:
    """Seed method/call evidence using a typeshed signature catalog."""

    def __init__(
        self,
        *,
        trace: TraceablePathIndex,
        catalog: TypeshedSignatureCatalog,
    ) -> None:
        """Initialize the seeder."""
        self._trace: TraceablePathIndex = trace
        self._catalog: TypeshedSignatureCatalog = catalog
        self._paths: SwarmPathHelper = SwarmPathHelper(trace=trace)
        self._matcher: SignatureOwnerTypeMatcher = SignatureOwnerTypeMatcher()
        self._substitutor: SignatureTypeSubstitutor = (
            SignatureTypeSubstitutor()
        )

    def enrich(self, *, result: SwarmInferenceResult) -> None:
        """Add signature-derived evidence to an existing swarm graph."""
        for graph_node in self._trace.graph.nodes:
            if isinstance(graph_node.ast_node, Call):
                self._call(node=graph_node.ast_node, result=result)
        result.graph.propagate(config=result.config)

    def _call(self, *, node: Call, result: SwarmInferenceResult) -> None:
        """Add evidence for one call expression."""
        if isinstance(node.func, Attribute):
            self._method_call(node=node, result=result)
            return
        if isinstance(node.func, Name):
            self._function_call(node=node, result=result)

    def _method_call(
        self,
        *,
        node: Call,
        result: SwarmInferenceResult,
    ) -> None:
        """Seed a method call using receiver type and catalog signatures."""
        func: expr = node.func
        if not isinstance(func, Attribute):
            return
        owner_path: TraceablePathText | None = self._paths.text_for_ast(
            node=func.value,
        )
        call_path: TraceablePathText | None = self._paths.text_for_ast(
            node=node,
        )
        if owner_path is None or call_path is None:
            return
        owner_type: TypeExpression | None = result.type_for(path=owner_path)
        if owner_type is None:
            return
        matches: tuple[
            tuple[TypeshedSignatureModel, dict[str, TypeExpression]],
            ...,
        ]
        matches = self._matcher.match(
            receiver_type=owner_type,
            method_name=func.attr,
            catalog=self._catalog,
        )
        for signature, substitutions in matches:
            self._seed_signature_return(
                result=result,
                path=call_path,
                signature=signature,
                substitutions=substitutions,
            )
            self._seed_signature_arguments(
                result=result,
                node=node,
                signature=signature,
                substitutions=substitutions,
            )

    def _function_call(
        self,
        *,
        node: Call,
        result: SwarmInferenceResult,
    ) -> None:
        """Seed a direct function call using catalog signatures."""
        func: expr = node.func
        if not isinstance(func, Name):
            return
        call_path: TraceablePathText | None = self._paths.text_for_ast(
            node=node,
        )
        if call_path is None:
            return
        for signature in self._catalog.function(name=func.id):
            self._seed_signature_return(
                result=result,
                path=call_path,
                signature=signature,
                substitutions={},
            )
            self._seed_signature_arguments(
                result=result,
                node=node,
                signature=signature,
                substitutions={},
            )

    def _seed_signature_return(
        self,
        *,
        result: SwarmInferenceResult,
        path: TraceablePathText,
        signature: TypeshedSignatureModel,
        substitutions: dict[str, TypeExpression],
    ) -> None:
        """Seed return evidence for a call path."""
        return_type: TypeExpression = self._substitutor.substitute(
            value=signature.returns,
            substitutions=substitutions,
        )
        result.graph.add_seed(
            evidence=SwarmTypeEvidence(
                type_hint=return_type,
                polarity=SwarmEvidencePolarity.SUPPORTS_UNION,
                confidence=signature.confidence,
                source_path=path,
                current_path=path,
                depth=0,
                reason=f"typeshed {signature.qualified_name} return",
            ),
        )

    def _seed_signature_arguments(
        self,
        *,
        result: SwarmInferenceResult,
        node: Call,
        signature: TypeshedSignatureModel,
        substitutions: dict[str, TypeExpression],
    ) -> None:
        """Seed argument evidence from a call signature."""
        parameters: tuple[TypeshedParameterModel, ...] = tuple(
            item
            for item in signature.parameters
            if item.name not in {"self", "cls"}
        )
        for index, actual in enumerate(iterable=node.args):
            if index >= len(parameters):
                break
            actual_path: TraceablePathText | None = self._paths.text_for_ast(
                node=actual,
            )
            if actual_path is None:
                continue
            parameter_type: TypeExpression = self._substitutor.substitute(
                value=parameters[index].type_hint,
                substitutions=substitutions,
            )
            result.graph.add_seed(
                evidence=SwarmTypeEvidence(
                    type_hint=parameter_type,
                    polarity=SwarmEvidencePolarity.NARROWS,
                    confidence=signature.confidence * 0.76,
                    source_path=actual_path,
                    current_path=actual_path,
                    depth=0,
                    reason=f"typeshed {signature.qualified_name} argument",
                ),
            )


class TypeshedBackedSwarmInferenceEngine:
    """Static analyzer based on a simplified Markov-chain evidence swarm."""

    def infer(
        self,
        *,
        trace: TraceablePathIndex,
        swarm_config: SwarmPropagationConfig | None = None,
        typeshed_config: TypeshedLookupConfig | None = None,
    ) -> TypeshedBackedSwarmResult:
        """Infer types using graph propagation plus typeshed signatures."""
        final_typeshed_config: TypeshedLookupConfig = (
            typeshed_config or TypeshedLookupConfig()
        )
        catalog: TypeshedSignatureCatalog = TypeshedCatalogBuilder().build(
            config=final_typeshed_config,
        )
        base: SwarmInferenceResult = SwarmTypeInferenceEngine().infer(
            trace=trace,
            config=swarm_config,
        )
        TypeshedMethodInferenceSeeder(trace=trace, catalog=catalog).enrich(
            result=base,
        )
        explanation_builder: MarkovExplanationBuilder = (
            MarkovExplanationBuilder(
                result=base,
            )
        )
        explanations: tuple[MarkovInferenceExplanation, ...] = (
            explanation_builder.all_explanations()
        )
        warnings: tuple[MarkovConflictWarning, ...] = tuple(
            warning
            for explanation in explanations
            for warning in explanation.conflicts
        )
        return TypeshedBackedSwarmResult(
            base=base,
            catalog=catalog,
            explanations=explanations,
            warnings=warnings,
        )


class TypeshedBackedSwarmQuery:
    """Chainable query facade for typeshed-backed swarm results."""

    def __init__(self, *, result: TypeshedBackedSwarmResult) -> None:
        """Initialize query facade."""
        self._result: TypeshedBackedSwarmResult = result

    def __call__(self, *, path: TraceablePathText) -> SwarmSymbolView:
        """Return the base swarm view for one path."""
        return SwarmSymbolView(path=path, result=self._result.base)

    def explain(
        self,
        *,
        path: TraceablePathText,
    ) -> MarkovInferenceExplanation | None:
        """Return inference explanation for one path."""
        return self._result.explanation_for(path=path)

    @property
    def explanations(self) -> tuple[MarkovInferenceExplanation, ...]:
        """Return all path explanations."""
        return self._result.explanations

    @property
    def warnings(self) -> tuple[MarkovConflictWarning, ...]:
        """Return all conflict warnings."""
        return self._result.warnings

    @property
    def catalog(self) -> TypeshedSignatureCatalog:
        """Return the loaded signature catalog."""
        return self._result.catalog


class TypeshedBackedSwarmAntFarmToolkit(
    SwarmAntFarmSemanticGraphParseUnparseToolkit,
):
    """Toolkit that adds typeshed-backed Markov-style swarm inference."""

    def parse_typeshed_swarm(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
        import_config: LocalImportInspectionConfig | None = None,
        swarm_config: SwarmPropagationConfig | None = None,
        typeshed_config: TypeshedLookupConfig | None = None,
    ) -> TypeshedBackedSwarmParseResult:
        """Parse code and run typeshed-backed bidirectional inference."""
        ant_farm: AntFarmParseResult = self.parse_ant_farm(
            source=source,
            filename=filename,
            import_config=import_config,
        )
        swarm_result: TypeshedBackedSwarmResult = (
            TypeshedBackedSwarmInferenceEngine().infer(
                trace=ant_farm.trace,
                swarm_config=swarm_config,
                typeshed_config=typeshed_config,
            )
        )
        return TypeshedBackedSwarmParseResult(
            ant_farm=ant_farm,
            swarm_result=swarm_result,
        )


class LiteralTypeInferencer:
    """Infer simple semantic types from literal/container AST values."""

    def __init__(self) -> None:
        """Initialize the inferencer."""
        self._algebra: TypeExpressionAlgebra = TypeExpressionAlgebra()

    def infer(self, *, node: AST) -> TypeExpression:
        """Infer a type expression for an AST node."""
        if isinstance(node, Constant):
            return self._constant(node=node)
        if isinstance(node, AstList):
            return self._list(node=node)
        if isinstance(node, AstTuple):
            return self._tuple(node=node)
        if isinstance(node, AstSet):
            return self._set(node=node)
        if isinstance(node, AstDict):
            return self._dict(node=node)
        return Types.object

    def _constant(self, *, node: Constant) -> TypeExpression:
        """Infer a constant type."""
        value: bool | int | float | complex | str | bytes | None | EllipsisType
        value = node.value

        result: TypeExpression | BuiltinTypeRef | EllipsisTypeRef = (
            Types.object
        )
        if value is None:
            result = Types.none
        elif isinstance(value, bool):
            result = Types.bool
        elif isinstance(value, int):
            result = Types.int
        elif isinstance(value, float):
            result = Types.float
        elif isinstance(value, complex):
            result = Types.complex
        elif isinstance(value, str):
            result = Types.str
        elif isinstance(value, bytes):
            result = Types.bytes
        elif value is Ellipsis:
            result = Types.ellipsis
        return result

    def _list(self, *, node: AstList) -> TypeExpression:
        """Infer a list element type."""
        elements: tuple[TypeExpression, ...] = tuple(
            self.infer(node=item) for item in node.elts
        )
        element_type: TypeExpression = self._algebra.union(values=elements)
        return Types.builtins.list_of(item=element_type)

    def _tuple(self, *, node: AstTuple) -> TypeExpression:
        """Infer a tuple type."""
        if not node.elts:
            return Types.builtins.tuple_empty()
        return Types.builtins.tuple_of(
            items=tuple(self.infer(node=item) for item in node.elts),
        )

    def _set(self, *, node: AstSet) -> TypeExpression:
        """Infer a set element type."""
        elements: tuple[TypeExpression, ...] = tuple(
            self.infer(node=item) for item in node.elts
        )
        element_type: TypeExpression = self._algebra.union(values=elements)
        return Types.builtins.set_of(item=element_type)

    def _dict(self, *, node: AstDict) -> TypeExpression:
        """Infer a dict key/value type."""
        keys: tuple[TypeExpression, ...] = tuple(
            self.infer(node=key) for key in node.keys if key is not None
        )
        values: tuple[TypeExpression, ...] = tuple(
            self.infer(node=value) for value in node.values
        )
        key_type: TypeExpression = self._algebra.union(values=keys)
        value_type: TypeExpression = self._algebra.union(values=values)
        return Types.builtins.dict_of(keys=key_type, values=value_type)


class ContractGraphBuilder:
    """Build a contract graph from native AST while preserving paths."""

    def __init__(self) -> None:
        """Initialize the builder."""
        self._allocator: PathIndexAllocator = PathIndexAllocator()
        self._literal_types: LiteralTypeInferencer = LiteralTypeInferencer()
        self._symbols_by_scope: dict[tuple[str, str], QualifiedPath] = {}
        self._function_returns: dict[str, QualifiedPath] = {}
        self._symbol_class_by_path: dict[str, str] = {}
        self._global_names_by_scope: dict[str, set[str]] = {}
        self._nonlocal_names_by_scope: dict[str, set[str]] = {}

    def build(self, *, module: AST) -> ContractGraph:
        """Build a contract graph from an AST tree."""
        graph: ContractGraph = ContractGraph()
        root: QualifiedPath = QualifiedPath.root()
        graph.add_node(
            path=root,
            kind=GraphNodeKind.MODULE,
            name="root",
            ast_node=module,
        )
        self._visit_body(
            graph=graph,
            body=tuple(getattr(module, "body", ())),
            scope=root,
        )
        return graph

    def _visit_body(
        self,
        *,
        graph: ContractGraph,
        body: tuple[AST, ...],
        scope: QualifiedPath,
    ) -> None:
        """Visit a sequence of statements inside one scope."""
        for statement in body:
            self._visit_statement(
                graph=graph,
                statement=statement,
                scope=scope,
            )

    def _visit_statement(
        self,
        *,
        graph: ContractGraph,
        statement: AST,
        scope: QualifiedPath,
    ) -> None:
        """Visit one statement."""
        if self._visit_definition_statement(
            graph=graph,
            statement=statement,
            scope=scope,
        ):
            return
        if self._visit_assignment_statement(
            graph=graph,
            statement=statement,
            scope=scope,
        ):
            return
        if self._visit_flow_statement(
            graph=graph,
            statement=statement,
            scope=scope,
        ):
            return
        self._walk_statement(graph=graph, node=statement, scope=scope)

    def _visit_definition_statement(
        self,
        *,
        graph: ContractGraph,
        statement: AST,
        scope: QualifiedPath,
    ) -> bool:
        """Visit definition statements and return whether handled."""
        if isinstance(statement, FunctionDef | AsyncFunctionDef):
            self._function(graph=graph, node=statement, scope=scope)
            return True
        if isinstance(statement, ClassDef):
            self._class(graph=graph, node=statement, scope=scope)
            return True
        return False

    def _visit_assignment_statement(
        self,
        *,
        graph: ContractGraph,
        statement: AST,
        scope: QualifiedPath,
    ) -> bool:
        """Visit assignment statements and return whether handled."""
        if isinstance(statement, Assign):
            self._assign(graph=graph, node=statement, scope=scope)
            return True
        if isinstance(statement, AnnAssign):
            self._ann_assign(graph=graph, node=statement, scope=scope)
            return True
        if isinstance(statement, AugAssign):
            self._aug_assign(graph=graph, node=statement, scope=scope)
            return True
        return False

    def _visit_flow_statement(
        self,
        *,
        graph: ContractGraph,
        statement: AST,
        scope: QualifiedPath,
    ) -> bool:
        """Visit flow/control statements and return whether handled."""
        handled: bool = True
        if isinstance(statement, Return):
            self._return(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, If):
            self._if(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, With):
            self._with(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, Match):
            self._match(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, Try):
            self._try(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, Global):
            self._global(graph=graph, node=statement, scope=scope)
        elif isinstance(statement, Nonlocal):
            self._nonlocal(graph=graph, node=statement, scope=scope)
        else:
            handled = False
        return handled

    def _global(
        self,
        *,
        graph: ContractGraph,
        node: Global,
        scope: QualifiedPath,
    ) -> None:
        """Record names declared global inside a scope."""
        _: ContractGraph = graph
        self._global_names_by_scope.setdefault(scope.text(), set()).update(
            node.names,
        )

    def _nonlocal(
        self,
        *,
        graph: ContractGraph,
        node: Nonlocal,
        scope: QualifiedPath,
    ) -> None:
        """Record names declared nonlocal inside a scope."""
        _: ContractGraph = graph
        self._nonlocal_names_by_scope.setdefault(scope.text(), set()).update(
            node.names,
        )

    def _function(
        self,
        *,
        graph: ContractGraph,
        node: FunctionNode,
        scope: QualifiedPath,
    ) -> None:
        """Visit a function or method definition."""
        function_path: QualifiedPath = self._allocator.child(
            parent=scope,
            kind=PathSegmentKind.FUNCTION,
            name=node.name,
        )
        graph.add_node(
            path=function_path,
            kind=GraphNodeKind.FUNCTION,
            name=node.name,
            ast_node=node,
        )
        self._symbols_by_scope.setdefault(
            (scope.text(), node.name),
            function_path,
        )
        decorator_paths: tuple[QualifiedPath, ...] = self._function_decorators(
            graph=graph,
            node=node,
            function_path=function_path,
        )
        argument_paths: tuple[QualifiedPath, ...] = self._function_arguments(
            graph=graph,
            node=node,
            function_path=function_path,
        )
        return_path: QualifiedPath = self._function_return_path(
            graph=graph,
            node=node,
            function_path=function_path,
        )
        self._function_returns[function_path.text()] = return_path
        graph.functions[function_path.text()] = FunctionTrace(
            path=function_path,
            node=node,
            argument_paths=argument_paths,
            return_path=return_path,
            decorators=decorator_paths,
        )
        self._visit_body(
            graph=graph,
            body=tuple(node.body),
            scope=function_path,
        )

    def _function_decorators(
        self,
        *,
        graph: ContractGraph,
        node: FunctionNode,
        function_path: QualifiedPath,
    ) -> tuple[QualifiedPath, ...]:
        """Return decorator paths for a function."""
        decorator_paths: list[QualifiedPath] = []
        for decorator in node.decorator_list:
            decorator_path: QualifiedPath = self._allocator.child(
                parent=function_path,
                kind=PathSegmentKind.DECORATOR,
                name="decorator",
            )
            graph.add_node(
                path=decorator_path,
                kind=GraphNodeKind.DECORATOR,
                name="decorator",
                ast_node=decorator,
            )
            decorator_paths.append(decorator_path)
        return tuple(decorator_paths)

    def _function_arguments(
        self,
        *,
        graph: ContractGraph,
        node: FunctionNode,
        function_path: QualifiedPath,
    ) -> tuple[QualifiedPath, ...]:
        """Return argument paths and seed declared annotations."""
        argument_paths: list[QualifiedPath] = []
        for arg_node in self._all_function_args(node=node):
            argument_path: QualifiedPath = self._symbol_path(
                graph=graph,
                scope=function_path,
                name=arg_node.arg,
                kind=GraphNodeKind.ARGUMENT,
                ast_node=arg_node,
            )
            argument_paths.append(argument_path)
            if arg_node.annotation is not None:
                self._seed_declared_annotation(
                    graph=graph,
                    path=argument_path,
                    annotation=arg_node.annotation,
                    explanation=(
                        f"declared argument annotation for {arg_node.arg}"
                    ),
                )
        return tuple(argument_paths)

    def _all_function_args(self, *, node: FunctionNode) -> tuple[arg, ...]:
        """Return every explicit function argument node."""
        arguments: tuple[arg, ...] | tuple[*tuple[arg, ...], arg] = (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
        if node.args.vararg is not None:
            arguments = (
                *arguments,
                node.args.vararg,
            )
        if node.args.kwarg is not None:
            arguments = (
                *arguments,
                node.args.kwarg,
            )
        return arguments

    def _function_return_path(
        self,
        *,
        graph: ContractGraph,
        node: FunctionNode,
        function_path: QualifiedPath,
    ) -> QualifiedPath:
        """Create and seed the function return path."""
        return_path: QualifiedPath = function_path.child(
            kind=PathSegmentKind.RETURN,
            name="return",
        )
        graph.add_node(
            path=return_path,
            kind=GraphNodeKind.RETURN,
            name="return",
            ast_node=node,
        )
        self._seed_function_return(
            graph=graph,
            node=node,
            return_path=return_path,
        )
        return return_path

    def _seed_function_return(
        self,
        *,
        graph: ContractGraph,
        node: FunctionNode,
        return_path: QualifiedPath,
    ) -> None:
        """Seed declared and structural function return evidence."""
        if node.returns is not None:
            self._seed_declared_annotation(
                graph=graph,
                path=return_path,
                annotation=node.returns,
                explanation=f"declared return annotation for {node.name}",
            )
        if self._function_returns_no_value(node=node):
            graph.add_seed(
                path=return_path,
                type_hint=Types.none,
                confidence=0.86,
                explanation=f"{node.name} has no value return",
            )
        if node.name == "__init__":
            graph.add_seed(
                path=return_path,
                type_hint=Types.none,
                confidence=0.99,
                explanation="__init__ returns None",
            )
        elif node.name == "__new__":
            self._seed_new_return(graph=graph, path=return_path)

    def _seed_new_return(
        self,
        *,
        graph: ContractGraph,
        path: QualifiedPath,
    ) -> None:
        """Seed a ``__new__`` return from the nearest class scope."""
        class_scope: QualifiedPath | None = self._nearest_class_scope(
            scope=path,
        )
        if class_scope is None:
            return
        graph.add_seed(
            path=path,
            type_hint=Types.local(name=class_scope.segments[-1].name),
            confidence=0.88,
            explanation="__new__ returns class instance",
        )

    def _class(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
        scope: QualifiedPath,
    ) -> None:
        """Visit a class definition."""
        class_path: QualifiedPath = self._allocator.child(
            parent=scope,
            kind=PathSegmentKind.CLASS,
            name=node.name,
        )
        graph.add_node(
            path=class_path,
            kind=GraphNodeKind.CLASS,
            name=node.name,
            ast_node=node,
        )
        graph.class_assigned_attributes.setdefault(class_path.text(), set())
        self._seed_special_class_body(
            graph=graph,
            node=node,
            class_path=class_path,
        )
        base_paths: list[QualifiedPath] = []
        metaclass_path: QualifiedPath | None = None
        for base in node.bases:
            base_path: QualifiedPath = self._allocator.child(
                parent=class_path,
                kind=PathSegmentKind.BASE,
                name="base",
            )
            graph.add_node(
                path=base_path,
                kind=GraphNodeKind.BASE,
                name="base",
                ast_node=base,
            )
            base_paths.append(base_path)
        for keyword in node.keywords:
            if keyword.arg == "metaclass":
                metaclass_path = class_path.child(
                    kind=PathSegmentKind.METACLASS,
                    name="metaclass",
                )
                graph.add_node(
                    path=metaclass_path,
                    kind=GraphNodeKind.METACLASS,
                    name="metaclass",
                    ast_node=keyword.value,
                )
        decorator_paths: list[QualifiedPath] = []
        for decorator in node.decorator_list:
            decorator_path: QualifiedPath = self._allocator.child(
                parent=class_path,
                kind=PathSegmentKind.DECORATOR,
                name="decorator",
            )
            graph.add_node(
                path=decorator_path,
                kind=GraphNodeKind.DECORATOR,
                name="decorator",
                ast_node=decorator,
            )
            decorator_paths.append(decorator_path)
        self._visit_body(graph=graph, body=tuple(node.body), scope=class_path)
        init_path: QualifiedPath | None = self._method_path(
            class_path=class_path,
            method_name="__init__",
        )
        new_path: QualifiedPath | None = self._method_path(
            class_path=class_path,
            method_name="__new__",
        )
        graph.classes[class_path.text()] = ClassTrace(
            path=class_path,
            node=node,
            bases=tuple(base_paths),
            decorators=tuple(decorator_paths),
            init_path=init_path,
            new_path=new_path,
            metaclass_path=metaclass_path,
        )

    def _seed_special_class_body(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
        class_path: QualifiedPath,
    ) -> None:
        """Seed dataclass fields and enum members from class body."""
        if self._is_dataclass(node=node):
            self._seed_dataclass_fields(
                graph=graph,
                node=node,
                class_path=class_path,
            )
        if self._is_enum_class(node=node):
            self._seed_enum_members(
                graph=graph,
                node=node,
                class_path=class_path,
            )

    def _is_dataclass(self, *, node: ClassDef) -> bool:
        """Return whether a class has a dataclass decorator."""
        for decorator in node.decorator_list:
            if isinstance(decorator, Name) and decorator.id == "dataclass":
                return True
            if (
                isinstance(decorator, Attribute)
                and decorator.attr == "dataclass"
            ):
                return True
            if isinstance(decorator, Call):
                called: expr = decorator.func
                if isinstance(called, Name) and called.id == "dataclass":
                    return True
                if (
                    isinstance(called, Attribute)
                    and called.attr == "dataclass"
                ):
                    return True
        return False

    def _is_enum_class(self, *, node: ClassDef) -> bool:
        """Return whether a class inherits from a known enum base."""
        enum_bases: set[str] = {
            "Enum",
            "IntEnum",
            "StrEnum",
            "Flag",
            "IntFlag",
        }
        for base in node.bases:
            if isinstance(base, Name) and base.id in enum_bases:
                return True
            if isinstance(base, Attribute) and base.attr in enum_bases:
                return True
        return False

    def _seed_dataclass_fields(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
        class_path: QualifiedPath,
    ) -> None:
        """Seed dataclass field types from class annotations/defaults."""
        for statement in node.body:
            if isinstance(statement, AnnAssign) and isinstance(
                statement.target,
                Name,
            ):
                field_path: QualifiedPath = class_path.child(
                    kind=PathSegmentKind.ATTRIBUTE,
                    name=statement.target.id,
                )
                graph.add_node(
                    path=field_path,
                    kind=GraphNodeKind.ATTRIBUTE,
                    name=statement.target.id,
                    ast_node=statement.target,
                )
                graph.class_assigned_attributes.setdefault(
                    class_path.text(),
                    set(),
                ).add(statement.target.id)
                self._seed_declared_annotation(
                    graph=graph,
                    path=field_path,
                    annotation=statement.annotation,
                    explanation=f"dataclass field {statement.target.id}",
                )
                if statement.value is not None:
                    value_path: QualifiedPath = self._expression_path(
                        graph=graph,
                        node=statement.value,
                        scope=class_path,
                    )
                    graph.add_contract(
                        contract=TypeContract(
                            source=value_path,
                            target=field_path,
                            relation=ContractRelation.CLASS_FIELD,
                            polarity=ContractPolarity.UNION,
                            confidence=0.9,
                            decay=0.88,
                            explanation="dataclass field default",
                        ),
                    )
            elif isinstance(statement, Assign):
                for target in statement.targets:
                    if not isinstance(target, Name):
                        continue
                    field_path = class_path.child(
                        kind=PathSegmentKind.ATTRIBUTE,
                        name=target.id,
                    )
                    graph.add_node(
                        path=field_path,
                        kind=GraphNodeKind.ATTRIBUTE,
                        name=target.id,
                        ast_node=target,
                    )
                    graph.class_assigned_attributes.setdefault(
                        class_path.text(),
                        set(),
                    ).add(target.id)
                    graph.add_seed(
                        path=field_path,
                        type_hint=self._literal_types.infer(
                            node=statement.value,
                        ),
                        confidence=0.86,
                        explanation=f"dataclass field default {target.id}",
                    )

    def _seed_enum_members(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
        class_path: QualifiedPath,
    ) -> None:
        """Seed enum members as instances of their enum class."""
        for statement in node.body:
            if not isinstance(statement, Assign):
                continue
            for target in statement.targets:
                if not isinstance(target, Name):
                    continue
                member_path: QualifiedPath = class_path.child(
                    kind=PathSegmentKind.ATTRIBUTE,
                    name=target.id,
                )
                graph.add_node(
                    path=member_path,
                    kind=GraphNodeKind.ATTRIBUTE,
                    name=target.id,
                    ast_node=target,
                )
                graph.class_assigned_attributes.setdefault(
                    class_path.text(),
                    set(),
                ).add(target.id)
                graph.add_seed(
                    path=member_path,
                    type_hint=Types.local(name=node.name),
                    confidence=0.97,
                    explanation=f"enum member {node.name}.{target.id}",
                )

    def _assign(
        self,
        *,
        graph: ContractGraph,
        node: Assign,
        scope: QualifiedPath,
    ) -> None:
        """Visit an assignment and connect value to every target."""
        value_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        for target in node.targets:
            target_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=target,
                scope=scope,
            )
            self._record_class_assignment(
                graph=graph,
                scope=scope,
                target=target,
            )
            class_name: str | None = self._constructor_name(
                graph=graph,
                node=node.value,
            )
            if class_name is not None and isinstance(target, Name):
                self._symbol_class_by_path[target_path.text()] = class_name
            graph.add_contract(
                contract=TypeContract(
                    source=value_path,
                    target=target_path,
                    relation=ContractRelation.ASSIGNS,
                    polarity=ContractPolarity.UNION,
                    confidence=0.95,
                    decay=0.9,
                    explanation=f"assignment {value_path} -> {target_path}",
                ),
            )
            if isinstance(target, Subscript):
                container_path: QualifiedPath = self._expression_path(
                    graph=graph,
                    node=target.value,
                    scope=scope,
                )
                graph.add_contract(
                    contract=TypeContract(
                        source=value_path,
                        target=container_path,
                        relation=ContractRelation.VALUE,
                        polarity=ContractPolarity.UNION,
                        confidence=0.78,
                        decay=0.82,
                        explanation="subscript assignment contributes value",
                    ),
                )

    def _ann_assign(
        self,
        *,
        graph: ContractGraph,
        node: AnnAssign,
        scope: QualifiedPath,
    ) -> None:
        """Visit an annotated assignment and enforce declared type."""
        target_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.target,
            scope=scope,
        )
        self._record_class_assignment(
            graph=graph,
            scope=scope,
            target=node.target,
        )
        class_name: str | None = (
            self._constructor_name(graph=graph, node=node.value)
            if node.value is not None
            else None
        )
        if class_name is not None and isinstance(node.target, Name):
            self._symbol_class_by_path[target_path.text()] = class_name
        self._seed_declared_annotation(
            graph=graph,
            path=target_path,
            annotation=node.annotation,
            explanation=f"declared variable annotation for {target_path}",
        )
        if node.value is None:
            return
        value_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        graph.add_contract(
            contract=TypeContract(
                source=value_path,
                target=target_path,
                relation=ContractRelation.ASSIGNS,
                polarity=ContractPolarity.UNION,
                confidence=0.96,
                decay=0.92,
                explanation=(
                    f"annotated assignment {value_path} -> {target_path}"
                ),
            ),
        )

    def _aug_assign(
        self,
        *,
        graph: ContractGraph,
        node: AugAssign,
        scope: QualifiedPath,
    ) -> None:
        """Visit an augmented assignment."""
        target_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.target,
            scope=scope,
        )
        value_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        if isinstance(node.op, Mult):
            graph.add_contract(
                contract=TypeContract(
                    source=target_path,
                    target=target_path,
                    relation=ContractRelation.OPERATOR,
                    polarity=ContractPolarity.UNION,
                    confidence=0.76,
                    decay=0.72,
                    explanation=(
                        "in-place multiplication preserves target type"
                    ),
                ),
            )
            _: QualifiedPath = value_path

    def _return(
        self,
        *,
        graph: ContractGraph,
        node: Return,
        scope: QualifiedPath,
    ) -> None:
        """Visit a return statement."""
        function_return: QualifiedPath | None = self._nearest_return_path(
            scope=scope,
        )
        if node.value is None or function_return is None:
            return
        value_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        graph.add_contract(
            contract=TypeContract(
                source=value_path,
                target=function_return,
                relation=ContractRelation.RETURNS,
                polarity=ContractPolarity.UNION,
                confidence=0.95,
                decay=0.9,
                explanation=f"{value_path} returns from {scope}",
            ),
        )

    def _if(
        self,
        *,
        graph: ContractGraph,
        node: If,
        scope: QualifiedPath,
    ) -> None:
        """Visit an if statement and condition narrowing."""
        condition_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.test,
            scope=scope,
        )
        graph.add_node(
            path=condition_path,
            kind=GraphNodeKind.CONDITION,
            name="condition",
            ast_node=node.test,
        )
        self._isinstance_narrowing(graph=graph, node=node.test, scope=scope)
        self._visit_body(graph=graph, body=tuple(node.body), scope=scope)
        self._visit_body(graph=graph, body=tuple(node.orelse), scope=scope)

    def _with(
        self,
        *,
        graph: ContractGraph,
        node: With,
        scope: QualifiedPath,
    ) -> None:
        """Visit a with statement as a context-manager use."""
        for item in node.items:
            context_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=item.context_expr,
                scope=scope,
            )
            graph.add_seed(
                path=context_path,
                type_hint=Types.context.abstract_context_manager.of(
                    arguments=(Types.object,),
                ),
                confidence=0.72,
                explanation="with statement requires context manager",
            )
            graph.add_contract(
                contract=TypeContract(
                    source=context_path,
                    target=context_path,
                    relation=ContractRelation.CONTEXT_ENTER,
                    polarity=ContractPolarity.CAPABILITY,
                    confidence=0.72,
                    decay=0.82,
                    explanation="context manager requires __enter__/__exit__",
                ),
            )
            if item.optional_vars is not None:
                optional_path: QualifiedPath = self._expression_path(
                    graph=graph,
                    node=item.optional_vars,
                    scope=scope,
                )
                graph.add_seed(
                    path=optional_path,
                    type_hint=Types.object,
                    confidence=0.4,
                    explanation="context manager enter value",
                )
        self._visit_body(graph=graph, body=tuple(node.body), scope=scope)

    def _match(
        self,
        *,
        graph: ContractGraph,
        node: Match,
        scope: QualifiedPath,
    ) -> None:
        """Visit a match statement and all case bodies."""
        _: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.subject,
            scope=scope,
        )
        for case in node.cases:
            self._visit_body(graph=graph, body=tuple(case.body), scope=scope)

    def _try(
        self,
        *,
        graph: ContractGraph,
        node: Try,
        scope: QualifiedPath,
    ) -> None:
        """Visit a try statement and all controlled bodies."""
        self._visit_body(graph=graph, body=tuple(node.body), scope=scope)
        for handler in node.handlers:
            if handler.name is not None:
                handler_path: QualifiedPath = self._symbol_path(
                    graph=graph,
                    scope=scope,
                    name=handler.name,
                    kind=GraphNodeKind.VARIABLE,
                    ast_node=handler,
                )
                graph.add_seed(
                    path=handler_path,
                    type_hint=Types.local(name="Exception"),
                    confidence=0.7,
                    explanation="except handler exception value",
                )
            self._visit_body(
                graph=graph,
                body=tuple(handler.body),
                scope=scope,
            )
        self._visit_body(graph=graph, body=tuple(node.orelse), scope=scope)
        self._visit_body(graph=graph, body=tuple(node.finalbody), scope=scope)

    def _walk_statement(
        self,
        *,
        graph: ContractGraph,
        node: AST,
        scope: QualifiedPath,
    ) -> None:
        """Walk a generic statement and collect expressions."""
        for child in walk(node=node):
            if isinstance(child, Name):
                self._name(graph=graph, node=child, scope=scope)
            elif isinstance(child, Attribute):
                self._attribute(graph=graph, node=child, scope=scope)
            elif isinstance(child, Call):
                self._call(graph=graph, node=child, scope=scope)
            elif isinstance(child, Compare):
                self._compare(graph=graph, node=child, scope=scope)
            elif isinstance(child, Subscript):
                self._subscript(graph=graph, node=child, scope=scope)

    def _expression_path(
        self,
        *,
        graph: ContractGraph,
        node: AST,
        scope: QualifiedPath,
    ) -> QualifiedPath:
        """Return a path for an expression node."""
        if isinstance(node, Name):
            return self._name(graph=graph, node=node, scope=scope)
        if isinstance(node, Attribute):
            return self._attribute(graph=graph, node=node, scope=scope)
        temporary_path: QualifiedPath = self._allocator.child(
            parent=scope,
            kind=PathSegmentKind.TEMPORARY,
            name=type(node).__name__,
        )
        graph.add_node(
            path=temporary_path,
            kind=self._expression_kind(node=node),
            name=type(node).__name__,
            ast_node=node,
        )
        inferred: TypeExpression = self._literal_types.infer(node=node)
        if inferred.key() != Types.object.key():
            graph.add_seed(
                path=temporary_path,
                type_hint=inferred,
                confidence=0.92,
                explanation=f"literal/container evidence at {temporary_path}",
            )
        if isinstance(node, Call):
            return self._call(graph=graph, node=node, scope=scope)
        return temporary_path

    def _expression_kind(self, *, node: AST) -> GraphNodeKind:
        """Return graph kind for an expression."""
        if isinstance(node, Constant):
            return GraphNodeKind.LITERAL
        if isinstance(node, AstList | AstTuple | AstSet | AstDict):
            return GraphNodeKind.CONTAINER
        if isinstance(node, Call):
            return GraphNodeKind.CALL
        return GraphNodeKind.VARIABLE

    def _name(
        self,
        *,
        graph: ContractGraph,
        node: Name,
        scope: QualifiedPath,
    ) -> QualifiedPath:
        """Record a name load/store."""
        effective_scope: QualifiedPath = self._effective_symbol_scope(
            scope=scope,
            name=node.id,
        )
        return self._symbol_path(
            graph=graph,
            scope=effective_scope,
            name=node.id,
            kind=GraphNodeKind.VARIABLE,
            ast_node=node,
        )

    def _effective_symbol_scope(
        self,
        *,
        scope: QualifiedPath,
        name: str,
    ) -> QualifiedPath:
        """Return the scope where a name should be resolved."""
        if name in self._global_names_by_scope.get(scope.text(), set()):
            return QualifiedPath.root()
        if name in self._nonlocal_names_by_scope.get(scope.text(), set()):
            return self._nearest_nonlocal_scope(scope=scope) or scope
        return scope

    def _nearest_nonlocal_scope(
        self,
        *,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return the nearest enclosing nonlocal-compatible scope."""
        parent: QualifiedPath | None = scope.parent()
        while parent is not None:
            if any(
                segment.kind is PathSegmentKind.FUNCTION
                for segment in parent.segments
            ):
                return parent
            parent = parent.parent()
        return None

    def _record_class_assignment(
        self,
        *,
        graph: ContractGraph,
        scope: QualifiedPath,
        target: AST,
    ) -> None:
        """Record class-level fields for class variable annotation."""
        if scope.segments[-1].kind is not PathSegmentKind.CLASS:
            return
        if not isinstance(target, Name):
            return
        graph.class_assigned_attributes.setdefault(scope.text(), set()).add(
            target.id,
        )

    def _attribute(
        self,
        *,
        graph: ContractGraph,
        node: Attribute,
        scope: QualifiedPath,
    ) -> QualifiedPath:
        """Record an attribute load/store."""
        direct_class_field_path: QualifiedPath | None = (
            self._direct_class_field_path(graph=graph, node=node)
        )
        if direct_class_field_path is not None:
            graph.add_node(
                path=direct_class_field_path,
                kind=GraphNodeKind.ATTRIBUTE,
                name=node.attr,
                ast_node=node,
            )
            return direct_class_field_path
        class_field_path: QualifiedPath | None = self._class_field_path(
            node=node,
            scope=scope,
        )
        if class_field_path is not None:
            graph.add_node(
                path=class_field_path,
                kind=GraphNodeKind.ATTRIBUTE,
                name=node.attr,
                ast_node=node,
            )
            return class_field_path
        owner_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        attribute_path: QualifiedPath = owner_path.child(
            kind=PathSegmentKind.ATTRIBUTE,
            name=node.attr,
        )
        self._link_known_property_access(
            graph=graph,
            owner_path=owner_path,
            attribute_path=attribute_path,
            attribute_name=node.attr,
        )
        graph.add_node(
            path=attribute_path,
            kind=GraphNodeKind.ATTRIBUTE,
            name=node.attr,
            ast_node=node,
        )
        graph.add_contract(
            contract=TypeContract(
                source=owner_path,
                target=attribute_path,
                relation=ContractRelation.ATTRIBUTE,
                polarity=ContractPolarity.CAPABILITY,
                confidence=0.68,
                decay=0.81,
                explanation=f"attribute {node.attr} accessed on {owner_path}",
            ),
        )
        return attribute_path

    def _direct_class_field_path(
        self,
        *,
        graph: ContractGraph,
        node: Attribute,
    ) -> QualifiedPath | None:
        """Return a canonical path for direct ``Class.attr`` access."""
        if not isinstance(node.value, Name):
            return None
        class_trace: ClassTrace | None = self._class_trace_by_name(
            graph=graph,
            name=node.value.id,
        )
        if class_trace is None:
            return None
        return class_trace.path.child(
            kind=PathSegmentKind.ATTRIBUTE,
            name=node.attr,
        )

    def _class_field_path(
        self,
        *,
        node: Attribute,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return a canonical class-field path for self/cls attributes."""
        if not isinstance(node.value, Name):
            return None
        if node.value.id not in {"self", "cls"}:
            return None
        class_scope: QualifiedPath | None = self._nearest_class_scope(
            scope=scope,
        )
        if class_scope is None:
            return None
        return class_scope.child(
            kind=PathSegmentKind.ATTRIBUTE,
            name=node.attr,
        )

    def _link_known_property_access(
        self,
        *,
        graph: ContractGraph,
        owner_path: QualifiedPath,
        attribute_path: QualifiedPath,
        attribute_name: str,
    ) -> None:
        """Link known property getter return types to instance attributes."""
        class_name: str | None = self._symbol_class_by_path.get(
            owner_path.text(),
        )
        if class_name is None:
            return
        class_trace: ClassTrace | None = self._class_trace_by_name(
            graph=graph,
            name=class_name,
        )
        if class_trace is None:
            return
        self._link_known_class_attribute(
            graph=graph,
            class_trace=class_trace,
            attribute_path=attribute_path,
            attribute_name=attribute_name,
        )
        property_path: QualifiedPath | None = self._method_path(
            class_path=class_trace.path,
            method_name=attribute_name,
        )
        if property_path is None:
            return
        property_trace: FunctionTrace | None = graph.functions.get(
            property_path.text(),
        )
        if property_trace is None:
            return
        graph.add_contract(
            contract=TypeContract(
                source=property_trace.return_path,
                target=attribute_path,
                relation=ContractRelation.ATTRIBUTE,
                polarity=ContractPolarity.UNION,
                confidence=0.86,
                decay=0.88,
                explanation=f"property {class_name}.{attribute_name} return",
            ),
        )

    def _link_known_class_attribute(
        self,
        *,
        graph: ContractGraph,
        class_trace: ClassTrace,
        attribute_path: QualifiedPath,
        attribute_name: str,
    ) -> None:
        """Link known class/dataclass fields to instance attributes."""
        assigned: set[str] = graph.class_assigned_attributes.get(
            class_trace.path.text(),
            set(),
        )
        if attribute_name not in assigned:
            return
        class_attribute_path: QualifiedPath = class_trace.path.child(
            kind=PathSegmentKind.ATTRIBUTE,
            name=attribute_name,
        )
        graph.add_contract(
            contract=TypeContract(
                source=class_attribute_path,
                target=attribute_path,
                relation=ContractRelation.ATTRIBUTE,
                polarity=ContractPolarity.UNION,
                confidence=0.9,
                decay=0.9,
                explanation=(
                    f"class attribute {class_trace.node.name}.{attribute_name}"
                ),
            ),
        )

    def _call(
        self,
        *,
        graph: ContractGraph,
        node: Call,
        scope: QualifiedPath,
    ) -> QualifiedPath:
        """Record call argument/result contracts."""
        call_path: QualifiedPath = self._allocator.child(
            parent=scope,
            kind=PathSegmentKind.TEMPORARY,
            name="call",
        )
        graph.add_node(
            path=call_path,
            kind=GraphNodeKind.CALL,
            name="call",
            ast_node=node,
        )
        cast_type: TypeExpression | None = self._cast_type(node=node)
        if cast_type is not None:
            graph.add_seed(
                path=call_path,
                type_hint=cast_type,
                confidence=0.99,
                explanation="declared cast target type",
            )
            return call_path
        if isinstance(node.func, Name) and node.func.id in {
            "int",
            "float",
            "str",
        }:
            return_type: TypeExpression = self._conversion_result(
                name=node.func.id,
            )
            graph.add_seed(
                path=call_path,
                type_hint=return_type,
                confidence=0.96,
                explanation=f"builtin conversion {node.func.id}(...) result",
            )
            # Conversion calls seed their return type. Argument capability
            # protocols are synthesized by the wider semantic synthesis engine.
            return call_path
        if isinstance(node.func, Name):
            class_trace: ClassTrace | None = self._class_trace_by_name(
                graph=graph,
                name=node.func.id,
            )
            if class_trace is not None:
                self._class_constructor_call(
                    graph=graph,
                    node=node,
                    scope=scope,
                    call_path=call_path,
                    class_trace=class_trace,
                )
            else:
                self._named_function_call(
                    graph=graph,
                    node=node,
                    scope=scope,
                    call_path=call_path,
                    function_name=node.func.id,
                )
        if isinstance(node.func, Attribute) and node.func.attr in {
            "append",
            "extend",
            "add",
            "update",
        }:
            receiver_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=node.func.value,
                scope=scope,
            )
            for argument in node.args:
                argument_path: QualifiedPath = self._expression_path(
                    graph=graph,
                    node=argument,
                    scope=scope,
                )
                graph.add_contract(
                    contract=TypeContract(
                        source=argument_path,
                        target=receiver_path,
                        relation=ContractRelation.ELEMENT,
                        polarity=ContractPolarity.UNION,
                        confidence=0.82,
                        decay=0.86,
                        explanation=(
                            f"{node.func.attr} contributes element type"
                        ),
                    ),
                )
        return call_path

    def _constructor_name(
        self,
        *,
        graph: ContractGraph,
        node: AST,
    ) -> str | None:
        """Return a class name when node is a known constructor call."""
        if not isinstance(node, Call):
            return None
        if not isinstance(node.func, Name):
            return None
        class_trace: ClassTrace | None = self._class_trace_by_name(
            graph=graph,
            name=node.func.id,
        )
        if class_trace is None:
            return None
        return class_trace.node.name

    def _class_constructor_call(
        self,
        *,
        graph: ContractGraph,
        node: Call,
        scope: QualifiedPath,
        call_path: QualifiedPath,
        class_trace: ClassTrace,
    ) -> None:
        """Connect a class construction call to __init__ arguments."""
        graph.add_seed(
            path=call_path,
            type_hint=Types.local(name=class_trace.node.name),
            confidence=0.95,
            explanation=f"constructor call creates {class_trace.node.name}",
        )
        if class_trace.init_path is None:
            return
        init_trace: FunctionTrace | None = graph.functions.get(
            class_trace.init_path.text(),
        )
        if init_trace is None:
            return
        init_arguments: tuple[QualifiedPath, ...] = tuple(
            path
            for path in init_trace.argument_paths
            if path.segments[-1].name not in {"self", "cls"}
        )
        for index, argument in enumerate(iterable=node.args):
            if index >= len(init_arguments):
                continue
            argument_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=argument,
                scope=scope,
            )
            graph.add_contract(
                contract=TypeContract(
                    source=argument_path,
                    target=init_arguments[index],
                    relation=ContractRelation.ARGUMENT,
                    polarity=ContractPolarity.UNION,
                    confidence=0.9,
                    decay=0.88,
                    explanation=(
                        f"constructor argument for {class_trace.node.name}"
                    ),
                ),
            )

    def _named_function_call(
        self,
        *,
        graph: ContractGraph,
        node: Call,
        scope: QualifiedPath,
        call_path: QualifiedPath,
        function_name: str,
    ) -> None:
        """Connect a direct call to a known function trace."""
        candidates: list[FunctionTrace] = [
            function
            for function in graph.functions.values()
            if function.node.name == function_name
        ]
        if not candidates:
            return
        function: FunctionTrace = candidates[0]
        for index, argument in enumerate(iterable=node.args):
            if index >= len(function.argument_paths):
                continue
            argument_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=argument,
                scope=scope,
            )
            graph.add_contract(
                contract=TypeContract(
                    source=argument_path,
                    target=function.argument_paths[index],
                    relation=ContractRelation.ARGUMENT,
                    polarity=ContractPolarity.UNION,
                    confidence=0.83,
                    decay=0.84,
                    explanation=f"call argument to {function_name}",
                ),
            )
        graph.add_contract(
            contract=TypeContract(
                source=function.return_path,
                target=call_path,
                relation=ContractRelation.CALL_RESULT,
                polarity=ContractPolarity.UNION,
                confidence=0.9,
                decay=0.86,
                explanation=f"call result from {function_name}",
            ),
        )

    def _compare(
        self,
        *,
        graph: ContractGraph,
        node: Compare,
        scope: QualifiedPath,
    ) -> None:
        """Record comparison constraints."""
        left_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.left,
            scope=scope,
        )
        for comparator in node.comparators:
            right_path: QualifiedPath = self._expression_path(
                graph=graph,
                node=comparator,
                scope=scope,
            )
            graph.add_contract(
                contract=TypeContract(
                    source=right_path,
                    target=left_path,
                    relation=ContractRelation.NARROWS,
                    polarity=ContractPolarity.INTERSECTION,
                    confidence=0.58,
                    decay=0.7,
                    explanation="comparison narrows compatible types",
                ),
            )

    def _subscript(
        self,
        *,
        graph: ContractGraph,
        node: Subscript,
        scope: QualifiedPath,
    ) -> None:
        """Record subscript read/write contracts."""
        value_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.value,
            scope=scope,
        )
        slice_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.slice,
            scope=scope,
        )
        graph.add_contract(
            contract=TypeContract(
                source=slice_path,
                target=value_path,
                relation=ContractRelation.KEY,
                polarity=ContractPolarity.UNION,
                confidence=0.62,
                decay=0.75,
                explanation="subscript key/index use",
            ),
        )

    def _isinstance_narrowing(
        self,
        *,
        graph: ContractGraph,
        node: AST,
        scope: QualifiedPath,
    ) -> None:
        """Record simple isinstance narrowing."""
        if not isinstance(node, Call):
            return
        if not isinstance(node.func, Name) or node.func.id != "isinstance":
            return
        expected_arg_count: int = 2
        if len(node.args) != expected_arg_count:
            return
        target_path: QualifiedPath = self._expression_path(
            graph=graph,
            node=node.args[0],
            scope=scope,
        )
        type_hint: TypeExpression = self._type_from_isinstance(
            node=node.args[1],
        )
        graph.add_seed(
            path=target_path,
            type_hint=type_hint,
            confidence=0.93,
            explanation="isinstance narrowing",
        )

    def _type_from_isinstance(self, *, node: AST) -> TypeExpression:
        """Convert a simple isinstance type argument to a type expression."""
        if isinstance(node, Name):
            if node.id == "int":
                return Types.int
            if node.id == "str":
                return Types.str
            if node.id == "float":
                return Types.float
            if node.id == "bool":
                return Types.bool
            if node.id == "bytes":
                return Types.bytes
        return Types.object

    def _seed_declared_annotation(
        self,
        *,
        graph: ContractGraph,
        path: QualifiedPath,
        annotation: expr,
        explanation: str,
    ) -> None:
        """Seed a hard declaration from an existing annotation node."""
        graph.add_seed(
            path=path,
            type_hint=self._type_from_annotation(node=annotation),
            confidence=self._annotation_confidence(node=annotation),
            explanation=explanation,
        )

    def _annotation_confidence(self, *, node: expr) -> float:
        """Return declaration confidence for existing annotations."""
        if self._annotation_is_any(node=node):
            return 0.05
        if self._annotation_is_object(node=node):
            return 0.18
        return 1.0

    def _annotation_is_any(self, *, node: expr) -> bool:
        """Return whether an annotation is ``Any``."""
        if isinstance(node, Name):
            return node.id == "Any"
        if isinstance(node, Attribute):
            return node.attr == "Any"
        return False

    def _annotation_is_object(self, *, node: expr) -> bool:
        """Return whether an annotation is ``object``."""
        return isinstance(node, Name) and node.id == "object"

    def _type_from_annotation(self, *, node: expr) -> TypeExpression:
        """Convert a common annotation AST node into a semantic type."""
        if isinstance(node, Constant) and node.value is None:
            return Types.none
        if isinstance(node, Name):
            return self._type_from_name(name=node.id)
        if isinstance(node, Attribute):
            return AstBackedTypeExpression(node=node)
        if isinstance(node, Subscript):
            return self._type_from_subscript(node=node)
        return AstBackedTypeExpression(node=node)

    def _type_from_name(self, *, name: str) -> TypeExpression:
        """Convert a simple annotation name into a semantic type."""
        builtin_map: dict[str, TypeExpression] = {
            "None": Types.none,
            "bool": Types.bool,
            "int": Types.int,
            "float": Types.float,
            "complex": Types.complex,
            "str": Types.str,
            "bytes": Types.bytes,
            "object": Types.object,
            "Any": Types.object,
        }
        builtin: TypeExpression | None = builtin_map.get(name)
        if builtin is not None:
            return builtin
        return Types.local(name=name)

    def _type_from_subscript(self, *, node: Subscript) -> TypeExpression:
        """Convert supported subscripted annotations into semantic types."""
        if not isinstance(node.value, Name):
            return AstBackedTypeExpression(node=node)
        origin_name: str = node.value.id
        arguments: tuple[TypeExpression, ...] = self._annotation_arguments(
            node=node.slice,
        )
        builders: dict[str, TypeExpression] = self._subscript_builders(
            arguments=arguments,
        )
        result: TypeExpression | None = builders.get(origin_name)
        if result is None:
            return AstBackedTypeExpression(node=node)
        return result

    def _subscript_builders(
        self,
        *,
        arguments: tuple[TypeExpression, ...],
    ) -> dict[str, TypeExpression]:
        """Return subscripted type candidates for supported origins."""
        builders: dict[str, TypeExpression] = {}
        if len(arguments) == Constants.one_arg:
            builders.update(
                self._one_arg_subscript_builders(arguments=arguments),
            )
        if len(arguments) == Constants.two_args:
            builders.update(
                self._two_arg_subscript_builders(arguments=arguments),
            )
        if arguments:
            builders["tuple"] = Types.builtins.tuple_of(
                items=arguments,
            )
        return builders

    def _one_arg_subscript_builders(
        self,
        *,
        arguments: tuple[TypeExpression, ...],
    ) -> dict[str, TypeExpression]:
        """Return supported one-argument generic annotations."""
        return {
            "list": Types.builtins.list_of(item=arguments[0]),
            "set": Types.builtins.set_of(item=arguments[0]),
            "MutableSequence": Types.abc.mutable_sequence.of(
                arguments=arguments,
            ),
            "AbstractContextManager": (
                Types.context.abstract_context_manager.of(
                    arguments=arguments,
                )
            ),
        }

    def _two_arg_subscript_builders(
        self,
        *,
        arguments: tuple[TypeExpression, ...],
    ) -> dict[str, TypeExpression]:
        """Return supported two-argument generic annotations."""
        return {
            "dict": Types.builtins.dict_of(
                keys=arguments[0],
                values=arguments[1],
            ),
            "MutableMapping": Types.abc.mutable_mapping.of(
                arguments=arguments,
            ),
        }

    def _annotation_arguments(
        self,
        *,
        node: expr,
    ) -> tuple[TypeExpression, ...]:
        """Return semantic type arguments from an annotation slice."""
        if isinstance(node, AstTuple):
            return tuple(
                self._type_from_annotation(node=item) for item in node.elts
            )
        return (self._type_from_annotation(node=node),)

    def _cast_type(self, *, node: Call) -> TypeExpression | None:
        """Return the requested type of a ``cast`` call when present."""
        if not isinstance(node.func, Name) or node.func.id != "cast":
            return None
        if not node.args:
            return None
        first_arg: expr = node.args[0]
        if isinstance(first_arg, Constant) and isinstance(
            first_arg.value,
            str,
        ):
            return self._type_from_annotation_text(text=first_arg.value)
        return self._type_from_annotation(node=first_arg)

    def _type_from_annotation_text(self, *, text: str) -> TypeExpression:
        """Parse a simple string annotation used by an existing cast."""
        stripped: str = text.strip()
        simple: TypeExpression | None = self._type_from_simple_text(
            text=stripped,
        )
        if simple is not None:
            return simple
        return Types.local(name=stripped)

    def _type_from_simple_text(self, *, text: str) -> TypeExpression | None:
        """Return simple semantic types from string annotations."""
        builtin_map: dict[str, TypeExpression] = {
            "None": Types.none,
            "bool": Types.bool,
            "int": Types.int,
            "float": Types.float,
            "complex": Types.complex,
            "str": Types.str,
            "bytes": Types.bytes,
            "object": Types.object,
            "Any": Types.object,
        }
        return builtin_map.get(text)

    def _function_returns_no_value(self, *, node: FunctionNode) -> bool:
        """Return whether a function has no return statement with a value."""
        return not any(
            isinstance(child, Return) and child.value is not None
            for child in walk(node=node)
        )

    def _conversion_result(self, *, name: str) -> TypeExpression:
        """Return result type for a builtin conversion."""
        if name == "int":
            return Types.int
        if name == "float":
            return Types.float
        return Types.str

    def _symbol_path(
        self,
        *,
        graph: ContractGraph,
        scope: QualifiedPath,
        name: str,
        kind: GraphNodeKind,
        ast_node: AST,
    ) -> QualifiedPath:
        """Return a stable lexical symbol path."""
        key: tuple[str, str] = (scope.text(), name)
        existing: QualifiedPath | None = self._symbols_by_scope.get(key)
        if existing is not None:
            return existing
        path: QualifiedPath = scope.child(
            kind=PathSegmentKind.SYMBOL,
            name=name,
        )
        self._symbols_by_scope[key] = path
        graph.add_node(path=path, kind=kind, name=name, ast_node=ast_node)
        return path

    def _nearest_return_path(
        self,
        *,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return nearest function return path for a scope."""
        current: QualifiedPath | None = scope
        while current is not None:
            found: QualifiedPath | None = self._function_returns.get(
                current.text(),
            )
            if found is not None:
                return found
            current = current.parent()
        return None

    def _method_path(
        self,
        *,
        class_path: QualifiedPath,
        method_name: str,
    ) -> QualifiedPath | None:
        """Return a known method path by class path and method name."""
        key: tuple[str, str] = (class_path.text(), method_name)
        return self._symbols_by_scope.get(key)

    def _nearest_class_scope(
        self,
        *,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return the nearest enclosing class path."""
        current: QualifiedPath | None = scope
        while current is not None:
            if (
                len(current.segments) > 1
                and current.segments[-1].kind is PathSegmentKind.CLASS
            ):
                return current
            current = current.parent()
        return None

    def _class_trace_by_name(
        self,
        *,
        graph: ContractGraph,
        name: str,
    ) -> ClassTrace | None:
        """Return the first class trace matching a class name."""
        for class_trace in graph.classes.values():
            if class_trace.node.name == name:
                return class_trace
        return None


class AdvancedFeatureSeeder:
    """Inspect advanced Python constructs and add semantic graph evidence."""

    def __init__(self) -> None:
        """Initialize the feature seeder."""
        self._catalog: AdvancedFeatureCatalog = AdvancedFeatureCatalog()
        self._anonymous_index: int = 0

    def seed(
        self,
        *,
        graph: ContractGraph,
        module: AST,
    ) -> AdvancedFeatureAnalysisResult:
        """Seed graph evidence and return an advanced feature catalog."""
        self._catalog = AdvancedFeatureCatalog()
        self._anonymous_index = 0
        for node in walk(node=module):
            self._inspect_node(graph=graph, node=node)
        return AdvancedFeatureAnalysisResult(catalog=self._catalog)

    def _inspect_node(self, *, graph: ContractGraph, node: AST) -> None:
        """Inspect one AST node."""
        if self._inspect_definition_node(graph=graph, node=node):
            return
        if self._inspect_control_node(graph=graph, node=node):
            return
        self._inspect_expression_node(graph=graph, node=node)

    def _inspect_definition_node(
        self,
        *,
        graph: ContractGraph,
        node: AST,
    ) -> bool:
        """Inspect definition nodes and return whether handled."""
        if isinstance(node, ClassDef):
            self._class(graph=graph, node=node)
            return True
        if isinstance(node, FunctionDef | AsyncFunctionDef):
            self._function(graph=graph, node=node)
            return True
        return False

    def _inspect_control_node(
        self,
        *,
        graph: ContractGraph,
        node: AST,
    ) -> bool:
        """Inspect control-flow nodes and return whether handled."""
        if isinstance(node, Match):
            self._match(graph=graph, node=node)
            return True
        if isinstance(node, Try):
            self._try(graph=graph, node=node)
            return True
        if isinstance(node, ExceptHandler):
            self._except_handler(graph=graph, node=node)
            return True
        return False

    def _inspect_expression_node(
        self,
        *,
        graph: ContractGraph,
        node: AST,
    ) -> None:
        """Inspect expression-like nodes."""
        if isinstance(node, Call):
            self._call(graph=graph, node=node)
        elif isinstance(node, NamedExpr):
            self._named_expr(graph=graph, node=node)
        elif isinstance(node, IfExp):
            self._if_exp(graph=graph, node=node)
        elif isinstance(node, ListComp | SetComp | DictComp):
            self._comprehension(graph=graph, node=node)
        elif isinstance(node, BinOp):
            self._bin_op(graph=graph, node=node)
        elif isinstance(node, Yield):
            self._yield(graph=graph, node=node)
        elif isinstance(node, YieldFrom):
            self._yield_from(graph=graph, node=node)

    def _class(self, *, graph: ContractGraph, node: ClassDef) -> None:
        """Inspect class definitions."""
        path: QualifiedPath = self._path_for_class(graph=graph, node=node)
        if self._is_typed_dict_class(node=node):
            self._catalog.add(
                kind=AdvancedFeatureKind.TYPED_DICT_CLASS,
                path=path,
                name=node.name,
                ast_node=node,
            )
            self._seed_structural_class_fields(
                graph=graph,
                node=node,
                path=path,
            )
        if self._is_named_tuple_class(node=node):
            self._catalog.add(
                kind=AdvancedFeatureKind.NAMED_TUPLE_CLASS,
                path=path,
                name=node.name,
                ast_node=node,
            )
            self._seed_structural_class_fields(
                graph=graph,
                node=node,
                path=path,
            )

    def _function(
        self,
        *,
        graph: ContractGraph,
        node: FunctionDef | AsyncFunctionDef,
    ) -> None:
        """Inspect function definitions."""
        path: QualifiedPath = self._path_for_function(graph=graph, node=node)
        if isinstance(node, AsyncFunctionDef):
            self._catalog.add(
                kind=AdvancedFeatureKind.ASYNC_FUNCTION,
                path=path,
                name=node.name,
                ast_node=node,
            )
            self._seed_async_function_return(graph=graph, node=node, path=path)
        if node.name in Constants.magic_method_names:
            self._catalog.add(
                kind=AdvancedFeatureKind.MAGIC_METHOD,
                path=path,
                name=node.name,
                ast_node=node,
            )
            self._seed_magic_method(graph=graph, node=node, path=path)
        if self._has_decorator(node=node, decorator_name="property"):
            self._catalog.add(
                kind=AdvancedFeatureKind.PROPERTY_METHOD,
                path=path,
                name=node.name,
                ast_node=node,
            )

    def _call(self, *, graph: ContractGraph, node: Call) -> None:
        """Inspect calls such as super(), __import__, importlib, NamedTuple."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        called_name: str = self._callable_name(node=node.func)
        if called_name == "super":
            self._catalog.add(
                kind=AdvancedFeatureKind.SUPER_CALL,
                path=path,
                name="super",
                ast_node=node,
            )
        if called_name == "__import__":
            self._catalog.add(
                kind=AdvancedFeatureKind.DYNAMIC_IMPORT,
                path=path,
                name="__import__",
                ast_node=node,
            )
            graph.add_seed(
                path=path,
                type_hint=Types.types.module_type,
                confidence=0.86,
                explanation="__import__ returns module-like object",
            )
        if called_name.startswith("importlib."):
            self._catalog.add(
                kind=AdvancedFeatureKind.IMPORTLIB_CALL,
                path=path,
                name=called_name,
                ast_node=node,
            )
            if called_name.endswith("import_module"):
                graph.add_seed(
                    path=path,
                    type_hint=Types.types.module_type,
                    confidence=0.86,
                    explanation="importlib.import_module returns ModuleType",
                )
        if called_name == "TypedDict":
            self._catalog.add(
                kind=AdvancedFeatureKind.TYPED_DICT_FUNCTION,
                path=path,
                name="TypedDict",
                ast_node=node,
            )
        if called_name == "NamedTuple":
            self._catalog.add(
                kind=AdvancedFeatureKind.NAMED_TUPLE_FUNCTION,
                path=path,
                name="NamedTuple",
                ast_node=node,
            )
        self._seed_common_magic_call(graph=graph, node=node, path=path)

    def _named_expr(self, *, graph: ContractGraph, node: NamedExpr) -> None:
        """Record and seed walrus expressions."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.WALRUS,
            path=path,
            name="walrus",
            ast_node=node,
        )
        target_path: QualifiedPath = self._path_for_name(
            graph=graph,
            name=node.target.id,
            node=node.target,
        )
        value_type: TypeExpression = self._literal_type(node=node.value)
        graph.add_seed(
            path=target_path,
            type_hint=value_type,
            confidence=0.72,
            explanation="walrus value evidence",
        )

    def _if_exp(self, *, graph: ContractGraph, node: IfExp) -> None:
        """Record ternary expression and union branch evidence."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.TERNARY,
            path=path,
            name="if_expression",
            ast_node=node,
        )
        graph.add_seed(
            path=path,
            type_hint=Types.union(
                options=(
                    self._literal_type(node=node.body),
                    self._literal_type(node=node.orelse),
                ),
            ),
            confidence=0.68,
            explanation="ternary branch union",
        )

    def _match(self, *, graph: ContractGraph, node: Match) -> None:
        """Record match/case narrowing conditions."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.MATCH,
            path=path,
            name="match",
            ast_node=node,
        )
        subject_type: TypeExpression = self._literal_type(node=node.subject)
        if subject_type.key() != Types.object.key():
            graph.add_seed(
                path=path,
                type_hint=subject_type,
                confidence=0.55,
                explanation="match subject literal evidence",
            )
        for index, case in enumerate(iterable=node.cases, start=1):
            case_path: QualifiedPath = path.child(
                kind=PathSegmentKind.TEMPORARY,
                name=f"case_{index}",
            )
            self._catalog.add(
                kind=AdvancedFeatureKind.CASE_CONDITION,
                path=case_path,
                name=f"case_{index}",
                ast_node=case.pattern,
            )

    def _try(self, *, graph: ContractGraph, node: Try) -> None:
        """Record try/except/finally structures."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.TRY,
            path=path,
            name="try",
            ast_node=node,
        )

    def _except_handler(
        self,
        *,
        graph: ContractGraph,
        node: ExceptHandler,
    ) -> None:
        """Record except handler exception variable type."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.EXCEPT_HANDLER,
            path=path,
            name=node.name or "except",
            ast_node=node,
        )
        if node.name is None:
            return
        exception_path: QualifiedPath = self._path_for_name(
            graph=graph,
            name=node.name,
            node=node,
        )
        graph.add_seed(
            path=exception_path,
            type_hint=Types.local(name="Exception"),
            confidence=0.7,
            explanation="except handler exception value",
        )

    def _comprehension(
        self,
        *,
        graph: ContractGraph,
        node: ListComp | SetComp | DictComp,
    ) -> None:
        """Record comprehension expressions."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        kind: AdvancedFeatureKind
        result_type: TypeExpression
        if isinstance(node, ListComp):
            kind = AdvancedFeatureKind.LIST_COMPREHENSION
            result_type = Types.builtins.list_of(
                item=self._literal_type(node=node.elt),
            )
        elif isinstance(node, SetComp):
            kind = AdvancedFeatureKind.SET_COMPREHENSION
            result_type = Types.builtins.set_of(
                item=self._literal_type(node=node.elt),
            )
        else:
            kind = AdvancedFeatureKind.DICT_COMPREHENSION
            result_type = Types.builtins.dict_of(
                keys=self._literal_type(node=node.key),
                values=self._literal_type(node=node.value),
            )
        self._catalog.add(kind=kind, path=path, name=kind.value, ast_node=node)
        graph.add_seed(
            path=path,
            type_hint=result_type,
            confidence=0.7,
            explanation=f"{kind.value} result type",
        )
        for generator in node.generators:
            if isinstance(generator.target, Name):
                target_path: QualifiedPath = self._path_for_name(
                    graph=graph,
                    name=generator.target.id,
                    node=generator.target,
                )
                graph.add_seed(
                    path=target_path,
                    type_hint=Types.object,
                    confidence=0.22,
                    explanation="comprehension target fallback",
                )

    def _bin_op(self, *, graph: ContractGraph, node: BinOp) -> None:
        """Record bitwise operator result evidence."""
        if not isinstance(node.op, BitAnd | BitOr | BitXor):
            return
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.BIT_OPERATOR,
            path=path,
            name=type(node.op).__name__,
            ast_node=node,
        )
        result_type: TypeExpression = Types.int
        graph.add_seed(
            path=path,
            type_hint=result_type,
            confidence=0.64,
            explanation="bit operator operand union",
        )

    def _yield(self, *, graph: ContractGraph, node: Yield) -> None:
        """Record yield expressions."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.YIELD,
            path=path,
            name="yield",
            ast_node=node,
        )
        yielded_type: TypeExpression
        if node.value is None:
            yielded_type = Types.none
        else:
            yielded_type = self._literal_type(
                node=node.value,
            )
        graph.add_seed(
            path=path,
            type_hint=Types.abc.generator.of(
                arguments=(yielded_type, Types.none, Types.none),
            ),
            confidence=0.72,
            explanation="yield expression implies Generator",
        )

    def _yield_from(self, *, graph: ContractGraph, node: YieldFrom) -> None:
        """Record yield-from expressions."""
        path: QualifiedPath = self._path_for_ast(graph=graph, node=node)
        self._catalog.add(
            kind=AdvancedFeatureKind.YIELD_FROM,
            path=path,
            name="yield_from",
            ast_node=node,
        )
        graph.add_seed(
            path=path,
            type_hint=Types.abc.iterable.of(arguments=(Types.object,)),
            confidence=0.65,
            explanation="yield from requires Iterable",
        )

    def _seed_structural_class_fields(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
        path: QualifiedPath,
    ) -> None:
        """Seed class body annotations for TypedDict / NamedTuple fields."""
        for statement in node.body:
            target_name: str | None = self._class_field_name(node=statement)
            if target_name is None:
                continue
            field_path: QualifiedPath = path.child(
                kind=PathSegmentKind.ATTRIBUTE,
                name=target_name,
            )
            graph.add_node(
                path=field_path,
                kind=GraphNodeKind.ATTRIBUTE,
                name=target_name,
                ast_node=statement,
            )
            graph.add_seed(
                path=field_path,
                type_hint=Types.object,
                confidence=0.35,
                explanation="structural class field fallback",
            )

    def _seed_async_function_return(
        self,
        *,
        graph: ContractGraph,
        node: AsyncFunctionDef,
        path: QualifiedPath,
    ) -> None:
        """Seed async function return path."""
        return_path: QualifiedPath = path.child(
            kind=PathSegmentKind.RETURN,
            name="return",
        )
        if node.returns is None:
            graph.add_seed(
                path=return_path,
                type_hint=Types.abc.awaitable.of(arguments=(Types.object,)),
                confidence=0.36,
                explanation="async function without return annotation",
            )

    def _seed_magic_method(
        self,
        *,
        graph: ContractGraph,
        node: FunctionDef | AsyncFunctionDef,
        path: QualifiedPath,
    ) -> None:
        """Seed common magic-method returns and protocols."""
        return_path: QualifiedPath = path.child(
            kind=PathSegmentKind.RETURN,
            name="return",
        )
        self._seed_magic_arguments(graph=graph, node=node, path=path)
        inferred: TypeExpression | None = self._magic_return_type(
            name=node.name,
        )
        if inferred is None:
            return
        graph.add_seed(
            path=return_path,
            type_hint=inferred,
            confidence=0.82,
            explanation=f"magic method {node.name} return contract",
        )

    def _seed_common_magic_call(
        self,
        *,
        graph: ContractGraph,
        node: Call,
        path: QualifiedPath,
    ) -> None:
        """Seed calls to common magic-compatible builtins."""
        called_name: str = self._callable_name(node=node.func)
        if called_name == "getattr":
            graph.add_seed(
                path=path,
                type_hint=Types.object,
                confidence=0.38,
                explanation="getattr result is dynamically typed object",
            )
        if called_name == "iter":
            graph.add_seed(
                path=path,
                type_hint=Types.abc.iterator.of(arguments=(Types.object,)),
                confidence=0.62,
                explanation="iter returns Iterator",
            )
        if called_name == "next":
            graph.add_seed(
                path=path,
                type_hint=Types.object,
                confidence=0.45,
                explanation="next result element",
            )

    def _seed_magic_arguments(
        self,
        *,
        graph: ContractGraph,
        node: FunctionDef | AsyncFunctionDef,
        path: QualifiedPath,
    ) -> None:
        """Seed common magic-method argument contracts."""
        args: list[arg] = [*node.args.posonlyargs, *node.args.args]
        non_receiver_args: tuple[arg, ...] = tuple(
            item for item in args if item.arg not in {"self", "cls"}
        )
        if not non_receiver_args:
            return
        first: arg = non_receiver_args[0]
        argument_path: QualifiedPath = path.child(
            kind=PathSegmentKind.SYMBOL,
            name=first.arg,
        )
        if node.name == "__getitem__":
            graph.add_seed(
                path=argument_path,
                type_hint=Types.int,
                confidence=0.78,
                explanation="__getitem__ index argument",
            )
        elif node.name in {"__getattr__", "__getattribute__"}:
            graph.add_seed(
                path=argument_path,
                type_hint=Types.str,
                confidence=0.78,
                explanation="attribute lookup name argument",
            )

    def _magic_return_type(self, *, name: str) -> TypeExpression | None:
        """Return a known magic-method return type."""
        mapping: dict[str, TypeExpression] = {
            "__len__": Types.int,
            "__int__": Types.int,
            "__bool__": Types.bool,
            "__contains__": Types.bool,
            "__exit__": Types.bool,
            "__aexit__": Types.bool,
            "__str__": Types.str,
            "__bytes__": Types.bytes,
            "__iter__": Types.abc.iterator.of(arguments=(Types.object,)),
            "__next__": Types.object,
        }
        return mapping.get(name)

    def _path_for_class(
        self,
        *,
        graph: ContractGraph,
        node: ClassDef,
    ) -> QualifiedPath:
        """Return the graph path for a class node."""
        existing: QualifiedPath | None = graph.path_for_node(node=node)
        if existing is not None:
            return existing
        return self._anonymous_path(graph=graph, node=node, name=node.name)

    def _path_for_function(
        self,
        *,
        graph: ContractGraph,
        node: FunctionDef | AsyncFunctionDef,
    ) -> QualifiedPath:
        """Return the graph path for a function node."""
        for trace in graph.functions.values():
            if trace.node is node:
                return trace.path
        existing: QualifiedPath | None = graph.path_for_node(node=node)
        if existing is not None:
            return existing
        return self._anonymous_path(graph=graph, node=node, name=node.name)

    def _path_for_ast(
        self,
        *,
        graph: ContractGraph,
        node: AST,
    ) -> QualifiedPath:
        """Return an existing path or create an anonymous one."""
        existing: QualifiedPath | None = graph.path_for_node(node=node)
        if existing is not None:
            return existing
        return self._anonymous_path(
            graph=graph,
            node=node,
            name=type(node).__name__,
        )

    def _path_for_name(
        self,
        *,
        graph: ContractGraph,
        name: str,
        node: AST,
    ) -> QualifiedPath:
        """Return a root-level fallback path for a named value."""
        path: QualifiedPath = QualifiedPath.root().child(
            kind=PathSegmentKind.SYMBOL,
            name=name,
        )
        graph.add_node(
            path=path,
            kind=GraphNodeKind.VARIABLE,
            name=name,
            ast_node=node,
        )
        return path

    def _anonymous_path(
        self,
        *,
        graph: ContractGraph,
        node: AST,
        name: str,
    ) -> QualifiedPath:
        """Create an anonymous path for a node not seen by the base graph."""
        self._anonymous_index += 1
        path: QualifiedPath = QualifiedPath.root().child(
            kind=PathSegmentKind.TEMPORARY,
            name=f"{name}_{self._anonymous_index}",
        )
        graph.add_node(
            path=path,
            kind=GraphNodeKind.VARIABLE,
            name=name,
            ast_node=node,
        )
        return path

    def _class_field_name(self, *, node: stmt) -> str | None:
        """Return simple class field names from assignment statements."""
        if isinstance(node, AnnAssign) and isinstance(node.target, Name):
            return node.target.id
        if isinstance(node, Assign) and node.targets:
            first_target: expr = node.targets[0]
            if isinstance(first_target, Name):
                return first_target.id
        return None

    def _is_typed_dict_class(self, *, node: ClassDef) -> bool:
        """Return whether a class inherits from TypedDict."""
        return any(
            self._name_like(node=base, value="TypedDict")
            for base in node.bases
        )

    def _is_named_tuple_class(self, *, node: ClassDef) -> bool:
        """Return whether a class inherits from NamedTuple."""
        return any(
            self._name_like(node=base, value="NamedTuple")
            for base in node.bases
        )

    def _has_decorator(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        decorator_name: str,
    ) -> bool:
        """Return whether a function has a decorator name."""
        return any(
            self._name_like(node=decorator, value=decorator_name)
            for decorator in node.decorator_list
        )

    def _name_like(self, *, node: expr, value: str) -> bool:
        """Return whether an expression name/attribute matches value."""
        if isinstance(node, Name):
            return node.id == value
        if isinstance(node, Attribute):
            return node.attr == value
        if isinstance(node, Call):
            return self._name_like(node=node.func, value=value)
        return False

    def _callable_name(self, *, node: expr) -> str:
        """Return a dotted callable name for a call expression."""
        if isinstance(node, Name):
            return node.id
        if isinstance(node, Attribute):
            prefix: str = self._callable_name(node=node.value)
            if prefix:
                return f"{prefix}.{node.attr}"
            return node.attr
        return ""

    def _literal_type(self, *, node: AST | None) -> TypeExpression:
        """Return a simple literal or object type for an AST node."""
        if node is None:
            return Types.none
        if isinstance(node, Constant):
            return self._constant_type(value=node.value)
        if isinstance(node, Name):
            return self._name_constant_type(name=node.id)
        if isinstance(node, UnaryOp):
            return self._literal_type(node=node.operand)
        return Types.object

    def _constant_type(self, *, value: ConstantValue) -> TypeExpression:
        """Return the semantic type of a constant value."""
        result: TypeExpression | BuiltinTypeRef = Types.object
        if value is None:
            result = Types.none
        elif isinstance(value, bool):
            result = Types.bool
        elif isinstance(value, int):
            result = Types.int
        elif isinstance(value, float):
            result = Types.float
        elif isinstance(value, complex):
            result = Types.complex
        elif isinstance(value, str):
            result = Types.str
        elif isinstance(value, bytes):
            result = Types.bytes
        return result

    def _name_constant_type(self, *, name: str) -> TypeExpression:
        """Return the semantic type of a constant-like name."""
        if name in {"True", "False"}:
            return Types.bool
        if name == "None":
            return Types.none
        return Types.object


class TypeHintNarrownessScorer:
    """Score how narrow or informative a type expression is."""

    def __init__(self) -> None:
        """Initialize the narrowness scorer."""
        self._inspector: TypeExpressionInspector = TypeExpressionInspector()

    def score(self, *, type_hint: TypeExpression) -> float:
        """Return a narrowness score in the range roughly 0..1."""
        if isinstance(type_hint, BuiltinTypeRef):
            return self._builtin_score(type_hint=type_hint)
        if isinstance(type_hint, GenericTypeRef):
            return self._generic_score(type_hint=type_hint)
        if isinstance(type_hint, UnionTypeRef):
            return self._union_score(type_hint=type_hint)
        if isinstance(type_hint, ImportedTypeRef | LocalTypeRef):
            return 0.78
        if isinstance(type_hint, TypeVarRef | ParamSpecRef):
            return 0.62
        return 0.55

    def _builtin_score(self, *, type_hint: BuiltinTypeRef) -> float:
        """Return builtin narrowness."""
        return TypeNarrownessTables.builtin_base.get(type_hint.name, 0.75)

    def _generic_score(self, *, type_hint: GenericTypeRef) -> float:
        """Return generic narrowness with argument contribution."""
        if not type_hint.arguments:
            return 0.45
        argument_scores: tuple[float, ...] = tuple(
            self.score(type_hint=argument) for argument in type_hint.arguments
        )
        average_argument: float = sum(argument_scores) / len(argument_scores)
        return min(1.0, 0.62 + average_argument * 0.32)

    def _union_score(self, *, type_hint: UnionTypeRef) -> float:
        """Return union narrowness with arity penalty."""
        options: tuple[TypeExpression, ...] = self._inspector.union_options(
            value=type_hint,
        )
        if not options:
            return 0.0
        option_scores: tuple[float, ...] = tuple(
            self.score(type_hint=option) for option in options
        )
        average: float = sum(option_scores) / len(option_scores)
        penalty: float = min(0.45, (len(options) - 1) * 0.08)
        return max(0.0, average - penalty)


class SynthesisStepPlanner:
    """Infer synthesis steps required for a candidate type."""

    def steps_for(
        self,
        *,
        type_hint: TypeExpression,
        registry: ExistingTypeRegistry,
    ) -> tuple[SynthesisStep, ...]:
        """Return synthetic steps implied by the type expression."""
        steps: list[SynthesisStep] = [
            SynthesisStep(
                kind=SyntheticStepKind.DIRECT_ANNOTATION,
                explanation="direct annotation synthesis",
            ),
        ]
        if registry.is_existing_alias(type_hint=type_hint):
            steps.append(
                SynthesisStep(
                    kind=SyntheticStepKind.TYPE_ALIAS_REUSE,
                    explanation="reuse existing type alias",
                ),
            )
        if registry.is_existing_type(type_hint=type_hint):
            steps.append(
                SynthesisStep(
                    kind=SyntheticStepKind.EXISTING_TYPE_REUSE,
                    explanation="reuse existing type",
                ),
            )
        if self._looks_like_protocol(type_hint=type_hint):
            steps.append(
                SynthesisStep(
                    kind=SyntheticStepKind.PROTOCOL,
                    explanation="synthetic protocol capability",
                ),
            )
        if isinstance(type_hint, TypeVarRef):
            steps.append(
                SynthesisStep(
                    kind=SyntheticStepKind.TYPEVAR,
                    explanation="synthetic TypeVar",
                ),
            )
        if isinstance(type_hint, ParamSpecRef):
            steps.append(
                SynthesisStep(
                    kind=SyntheticStepKind.PARAMSPEC,
                    explanation="synthetic ParamSpec",
                ),
            )
        return tuple(steps)

    def _looks_like_protocol(self, *, type_hint: TypeExpression) -> bool:
        """Return whether a type likely requires a synthetic protocol."""
        key: str = type_hint.key()
        if "Protocol" in key or "Supports" in key:
            return True
        if isinstance(type_hint, ImportedTypeRef):
            name: str = type_hint.source.imported_name
            return name.startswith(("Protocol", "Supports"))
        if isinstance(type_hint, LocalTypeRef):
            return type_hint.name.startswith(("Protocol", "Supports"))
        return False


class TypeHintCandidateScorer:
    """Score candidate plans for one entity."""

    def __init__(self, *, config: TypeHintObjectiveConfig) -> None:
        """Initialize the scorer."""
        self._config: TypeHintObjectiveConfig = config
        self._narrowness: TypeHintNarrownessScorer = TypeHintNarrownessScorer()
        self._steps: SynthesisStepPlanner = SynthesisStepPlanner()

    def plan(
        self,
        *,
        path: QualifiedPath,
        candidate: TypeCandidate,
        entropy: float,
        conflict_count: int,
        registry: ExistingTypeRegistry,
    ) -> TypeHintCandidatePlan:
        """Return a scored plan for one candidate."""
        normalized_hint: TypeExpression = self._normalize(
            type_hint=candidate.type_hint,
        )
        narrowness: float = self._narrowness.score(type_hint=normalized_hint)
        steps: tuple[SynthesisStep, ...] = self._steps.steps_for(
            type_hint=normalized_hint,
            registry=registry,
        )
        synthetic_cost: float = self._synthetic_cost(steps=steps)
        score: float = self._score(
            confidence=candidate.confidence,
            narrowness=narrowness,
            entropy=entropy,
            conflict_count=conflict_count,
            synthetic_cost=synthetic_cost,
        )
        return TypeHintCandidatePlan(
            path=path,
            type_hint=normalized_hint,
            confidence=candidate.confidence,
            entropy=entropy,
            narrowness=narrowness,
            steps=steps,
            score=score,
            explanation=candidate.explanation,
        )

    def fallback_plan(self, *, path: QualifiedPath) -> TypeHintCandidatePlan:
        """Return an object fallback plan."""
        candidate: TypeCandidate = TypeCandidate(
            type_hint=Types.object,
            confidence=self._config.object_fallback_confidence,
            distance=0,
            explanation="fallback to object for coverage",
        )
        return self.plan(
            path=path,
            candidate=candidate,
            entropy=0.0,
            conflict_count=0,
            registry=ExistingTypeRegistry.empty(),
        )

    def _normalize(self, *, type_hint: TypeExpression) -> TypeExpression:
        """Normalize one type hint through the existing algebra."""
        algebra: TypeExpressionAlgebra = TypeExpressionAlgebra()
        return algebra.union(values=(type_hint,))

    def _synthetic_cost(self, *, steps: tuple[SynthesisStep, ...]) -> float:
        """Return total signed synthetic operation cost."""
        return sum(
            self._config.costs.cost_for(kind=step.kind) for step in steps
        )

    def _score(
        self,
        *,
        confidence: float,
        narrowness: float,
        entropy: float,
        conflict_count: int,
        synthetic_cost: float,
    ) -> float:
        """Return objective score for one plan."""
        return (
            self._config.coverage_reward
            + confidence * self._config.confidence_weight
            + narrowness * self._config.narrowness_weight
            - entropy * self._config.entropy_penalty
            - conflict_count * self._config.conflict_penalty
            - synthetic_cost * self._config.synthetic_cost_weight
        )


class CollectiveTypeHintObjectiveSolver:
    """Solve the collective objective over all entity beliefs."""

    def __init__(
        self,
        *,
        config: TypeHintObjectiveConfig | None = None,
    ) -> None:
        """Initialize the solver."""
        self._config: TypeHintObjectiveConfig = (
            config if config is not None else TypeHintObjectiveConfig()
        )
        self._scorer: TypeHintCandidateScorer = TypeHintCandidateScorer(
            config=self._config,
        )

    def solve(
        self,
        *,
        beliefs: tuple[TypeBelief, ...],
        registry: ExistingTypeRegistry | None = None,
    ) -> TypeHintObjectiveReport:
        """Return the best collective type-hint plan."""
        active_registry: ExistingTypeRegistry = (
            registry if registry is not None else ExistingTypeRegistry.empty()
        )
        decisions: tuple[TypeHintObjectiveDecision, ...] = tuple(
            self._decision(belief=belief, registry=active_registry)
            for belief in beliefs
        )
        covered: int = sum(1 for decision in decisions if decision.is_covered)
        total_score: float = sum(
            decision.selected.score
            for decision in decisions
            if decision.selected is not None and decision.selected.should_emit
        )
        warnings: tuple[str, ...] = tuple(
            warning for decision in decisions for warning in decision.warnings
        )
        return TypeHintObjectiveReport(
            decisions=decisions,
            total_score=total_score,
            covered_entities=covered,
            total_entities=len(decisions),
            warnings=warnings,
        )

    def _decision(
        self,
        *,
        belief: TypeBelief,
        registry: ExistingTypeRegistry,
    ) -> TypeHintObjectiveDecision:
        """Return the best decision for one belief."""
        plans: (
            tuple[TypeHintCandidatePlan, ...] | tuple[TypeHintCandidatePlan]
        ) = self._plans(
            belief=belief,
            registry=registry,
        )
        if not plans and self._config.fallback_to_object:
            plans = (self._scorer.fallback_plan(path=belief.path),)
        selected: TypeHintCandidatePlan | None = self._select(plans=plans)
        warnings: tuple[str, ...] = self._warnings(belief=belief, plans=plans)
        return TypeHintObjectiveDecision(
            path=belief.path,
            selected=selected,
            alternatives=plans,
            warnings=warnings,
        )

    def _plans(
        self,
        *,
        belief: TypeBelief,
        registry: ExistingTypeRegistry,
    ) -> tuple[TypeHintCandidatePlan, ...]:
        """Return sorted candidate plans for one belief."""
        entropy: float = belief.entropy()
        conflict_count: int = len(belief.conflicts)
        plans: list[TypeHintCandidatePlan] = [
            self._scorer.plan(
                path=belief.path,
                candidate=candidate,
                entropy=entropy,
                conflict_count=conflict_count,
                registry=registry,
            )
            for candidate in belief.candidates.values()
        ]
        return tuple(
            sorted(
                plans,
                key=lambda plan: (
                    -plan.score,
                    -plan.confidence,
                    -plan.narrowness,
                    plan.type_hint.key(),
                ),
            ),
        )

    def _select(
        self,
        *,
        plans: tuple[TypeHintCandidatePlan, ...],
    ) -> TypeHintCandidatePlan | None:
        """Return the selected plan respecting minimum score."""
        if not plans:
            return None
        best: TypeHintCandidatePlan = plans[0]
        if best.score < self._config.minimum_emit_score:
            return None
        if not isfinite(best.score):
            return None
        return best

    def _warnings(
        self,
        *,
        belief: TypeBelief,
        plans: tuple[TypeHintCandidatePlan, ...],
    ) -> tuple[str, ...]:
        """Return human-readable objective warnings."""
        warnings: list[str] = []
        if belief.conflicts:
            warnings.append(
                f"{belief.path.text()} has {len(belief.conflicts)} "
                "type conflict(s).",
            )
        if len(plans) > 1:
            first: TypeHintCandidatePlan = plans[0]
            second: TypeHintCandidatePlan = plans[1]
            gap: float = first.score - second.score
            if gap < 1.0:
                warnings.append(
                    f"{belief.path.text()} has competing type plans "
                    f"within {gap:.3f} score points.",
                )
        if plans and plans[0].type_hint.key() == Types.object.key():
            warnings.append(
                f"{belief.path.text()} falls back to object due to weak "
                "evidence.",
            )
        return tuple(warnings)


class ContractNegotiator:
    """Negotiate type beliefs across the contract graph until stability.

    The negotiator implements the "ant-farm" propagation algorithm
    described in the project report: candidate type hints (ants)
    traverse contracts (paths) in the graph, combining and narrowing
    beliefs at each node.  Propagation continues until the total
    information entropy of all beliefs stabilises or a configured
    iteration/event limit is reached.  The current implementation
    includes several micro-optimisations:
    * Cached configuration attributes are stored in local variables to
      avoid repeated attribute lookups inside hot loops.
    * Early exit is performed when no beliefs change and the message
      queue is empty, skipping an unnecessary entropy calculation.
    * Event counts prevent runaway propagation when the graph is
      extremely connected.

    These enhancements improve performance on large stress fixtures
    without altering the semantics of the negotiation.
    """

    def __init__(self, *, config: ContractNegotiationConfig) -> None:
        """Initialize the negotiator."""
        self._config: ContractNegotiationConfig = config

    def solve(self, *, graph: ContractGraph) -> ContractNegotiationResult:
        """Solve all graph contracts and return final beliefs.

        This implementation optimises the negotiation loop by avoiding
        expensive entropy computations when an early exit is possible.  If
        the queue is empty immediately after processing new events, there
        is no need to calculate a fresh entropy value - we can return
        without performing additional work.  Configuration values are
        hoisted into local variables to reduce attribute lookups in
        hot loops.  These micro-optimisations make the swarm algorithm
        slightly more efficient without changing its semantics.
        """
        beliefs: dict[str, TypeBelief] = self._initial_beliefs(graph=graph)
        queue: deque[AntMessage] = self._initial_queue(graph=graph)
        snapshots: list[ContractEntropySnapshot] = []
        previous_entropy: float = -1.0
        best_messages: dict[tuple[str, str, ContractPolarity], float] = {}
        processed_events: int = 0
        # Copy configuration values into local variables for faster access.
        max_iterations: int = self._config.max_iterations
        max_propagation_events: int = self._config.max_propagation_events
        for iteration in range(max_iterations):
            # Process messages in the queue and count how many beliefs changed.
            changed: int = self._step(
                graph=graph,
                beliefs=beliefs,
                queue=queue,
                best_messages=best_messages,
                processed_events=processed_events,
            )
            processed_events += changed
            # If nothing changed and the queue is empty, the negotiation is
            # stable.  Skip entropy computation and exit early.
            if changed == 0 and not queue:
                snapshots.append(
                    ContractEntropySnapshot(
                        iteration=iteration,
                        total_entropy=max(previous_entropy, 0.0),
                        changed_beliefs=changed,
                    ),
                )
                break
            # Compute total entropy only when needed.  This call walks the
            # entire beliefs dict, so avoiding it on early exit reduces
            # overhead on large graphs.
            entropy: float = self._total_entropy(beliefs=beliefs)
            snapshots.append(
                ContractEntropySnapshot(
                    iteration=iteration,
                    total_entropy=entropy,
                    changed_beliefs=changed,
                ),
            )
            # If the system is stable according to the configured criteria,
            # break out of the loop.  This check uses the newly computed
            # entropy and the previous value.
            if self._is_stable(
                entropy=entropy,
                previous_entropy=previous_entropy,
                changed=changed,
                queue=queue,
                processed_events=processed_events,
            ):
                break
            previous_entropy = entropy
            # Stop if we've processed too many events.  This prevents
            # runaway propagation when configuration bounds are reached.
            if processed_events >= max_propagation_events:
                break
        conflicts: tuple[TypeConflict, ...] = tuple(
            conflict
            for belief in beliefs.values()
            for conflict in belief.conflicts
        )
        return ContractNegotiationResult(
            beliefs=tuple(
                sorted(beliefs.values(), key=lambda item: item.path.text()),
            ),
            snapshots=tuple(snapshots),
            conflicts=conflicts,
        )

    def _initial_beliefs(
        self,
        *,
        graph: ContractGraph,
    ) -> dict[str, TypeBelief]:
        """Create empty beliefs for every graph node."""
        beliefs: dict[str, TypeBelief] = {}
        for path_text, node in graph.nodes.items():
            beliefs[path_text] = TypeBelief.empty(path=node.path)
        return beliefs

    def _initial_queue(self, *, graph: ContractGraph) -> deque[AntMessage]:
        """Create the initial queue from seed candidates."""
        queue: deque[AntMessage] = deque()
        for path_text, candidates in graph.seeds.items():
            path: QualifiedPath = QualifiedPath.parse(value=path_text)
            for candidate in candidates:
                queue.append(
                    AntMessage(
                        path=path,
                        candidate=candidate,
                        polarity=ContractPolarity.UNION,
                    ),
                )
        return queue

    def _step(
        self,
        *,
        graph: ContractGraph,
        beliefs: dict[str, TypeBelief],
        queue: deque[AntMessage],
        best_messages: dict[tuple[str, str, ContractPolarity], float],
        processed_events: int,
    ) -> int:
        """Run one propagation step over the current queue."""
        changed: int = 0
        pending_count: int = len(queue)
        for _ in range(pending_count):
            event_count: int = processed_events + changed
            if event_count >= self._config.max_propagation_events:
                queue.clear()
                break
            message: AntMessage = queue.popleft()
            if not self._should_process(
                message=message,
                best_messages=best_messages,
            ):
                continue
            path_text: str = message.path.text()
            belief: TypeBelief = beliefs.setdefault(
                path_text,
                TypeBelief.empty(path=message.path),
            )
            if belief.add(
                candidate=message.candidate,
                polarity=message.polarity,
            ):
                changed += 1
                self._propagate_from(
                    graph=graph,
                    message=message,
                    queue=queue,
                )
        return changed

    def _should_process(
        self,
        *,
        message: AntMessage,
        best_messages: dict[tuple[str, str, ContractPolarity], float],
    ) -> bool:
        """Return whether a message has enough new confidence to process."""
        key: tuple[str, str, ContractPolarity] = (
            message.path.text(),
            message.candidate.type_hint.key(),
            message.polarity,
        )
        previous: float = best_messages.get(key, -1.0)
        if (
            message.candidate.confidence
            <= previous + self._config.wormhole_confidence_delta
        ):
            return False
        best_messages[key] = message.candidate.confidence
        return True

    def _propagate_from(
        self,
        *,
        graph: ContractGraph,
        message: AntMessage,
        queue: deque[AntMessage],
    ) -> None:
        """Propagate one message through outgoing and incoming contracts."""
        current: str = message.path.text()
        outgoing_edges: list[int] = graph.outgoing.get(current, [])
        incoming_edges: list[int] = graph.incoming.get(current, [])
        for edge_id in outgoing_edges:
            edge: ContractGraphEdge = graph.edges[edge_id]
            if edge.contract.polarity is ContractPolarity.CAPABILITY:
                continue
            candidate: TypeCandidate = self._transformed_candidate(
                candidate=message.candidate,
                relation=edge.contract.relation,
                decay=edge.contract.decay * self._config.forward_decay,
                forward=True,
            )
            if candidate.confidence >= self._config.minimum_confidence:
                queue.append(
                    AntMessage(
                        path=edge.contract.target,
                        candidate=candidate,
                        polarity=edge.contract.polarity,
                    ),
                )
        for edge_id in incoming_edges:
            edge = graph.edges[edge_id]
            if edge.contract.polarity is ContractPolarity.CAPABILITY:
                continue
            reversed_candidate: TypeCandidate = message.candidate.decayed(
                decay=edge.contract.decay * self._config.backward_decay,
            )
            if (
                reversed_candidate.confidence
                >= self._config.minimum_confidence
            ):
                queue.append(
                    AntMessage(
                        path=edge.contract.source,
                        candidate=reversed_candidate,
                        polarity=edge.contract.polarity,
                    ),
                )

    def _transformed_candidate(
        self,
        *,
        candidate: TypeCandidate,
        relation: ContractRelation,
        decay: float,
        forward: bool,
    ) -> TypeCandidate:
        """Transform a candidate while it crosses one contract edge."""
        type_hint: TypeExpression = candidate.type_hint
        if relation is ContractRelation.ELEMENT and forward:
            type_hint = Types.builtins.list_of(item=type_hint)
        elif relation is ContractRelation.ELEMENT and not forward:
            type_hint = self._element_type(type_hint=type_hint)
        return TypeCandidate(
            type_hint=type_hint,
            confidence=candidate.confidence * decay,
            distance=candidate.distance + 1,
            explanation=candidate.explanation,
        )

    def _element_type(
        self,
        *,
        type_hint: GenericTypeRef | TypeExpression,
    ) -> TypeExpression:
        """Return the first generic argument when available."""
        if isinstance(type_hint, GenericTypeRef) and type_hint.arguments:
            return type_hint.arguments[0]
        return Types.object

    def _total_entropy(self, *, beliefs: dict[str, TypeBelief]) -> float:
        """Return total graph entropy."""
        return sum(belief.entropy() for belief in beliefs.values())

    def _is_stable(
        self,
        *,
        entropy: float,
        previous_entropy: float,
        changed: int,
        queue: deque[AntMessage],
        processed_events: int,
    ) -> bool:
        """Return whether propagation should stop."""
        if previous_entropy < 0.0:
            return False
        entropy_delta: float = abs(entropy - previous_entropy)
        if not queue:
            return True
        if processed_events >= self._config.max_propagation_events:
            return True
        return changed == 0 and entropy_delta < self._config.entropy_epsilon


class ContractAnnotator:
    """Apply inferred annotations back to the original AST."""

    def annotate(self, *, result: ContractAnalysisResult) -> str:
        """Return annotated source code."""
        import_nodes: tuple[Import | ImportFrom, ...] = tuple(
            node
            for node in result.module.body
            if isinstance(node, Import | ImportFrom)
        )
        existing_nodes: tuple[Import | ImportFrom | ClassDef, ...] = tuple(
            node
            for node in result.module.body
            if isinstance(node, Import | ImportFrom | ClassDef)
        )
        context: ExistingNodeContext = ExistingNodeContext.from_nodes(
            nodes=existing_nodes,
        )
        symbols: ScriptSymbolIndex = ScriptSymbolIndex.from_context(
            context=context,
        )
        imports: UsageAwareImportCollector = UsageAwareImportCollector(
            symbol_index=symbols,
            existing_import_nodes=import_nodes,
            postponed_annotations=False,
            local_roots=(),
        )
        resolver: TypeExpressionResolver = TypeExpressionResolver(
            imports=imports,
        )
        function_paths: dict[int, QualifiedPath] = {
            id(function.node): function.path
            for function in result.graph.functions.values()
        }
        class_paths: dict[int, QualifiedPath] = {
            id(class_trace.node): class_trace.path
            for class_trace in result.graph.classes.values()
        }
        for function in result.graph.functions.values():
            self._annotate_function(
                result=result,
                resolver=resolver,
                function_path=function.path,
            )
        traversal: AnnotationTraversalContext = AnnotationTraversalContext(
            result=result,
            resolver=resolver,
            function_paths=function_paths,
            class_paths=class_paths,
        )
        self._annotate_statement_list(
            context=traversal,
            statements=result.module.body,
            scope=QualifiedPath.root(),
        )
        generated_imports: tuple[stmt, ...] = imports.import_nodes()
        if generated_imports:
            result.module.body[:0] = list(generated_imports)
        self._remove_forbidden_any_imports(module=result.module)
        fixed: Module = fix_missing_locations(node=result.module)
        return unparse(ast_obj=fixed)

    def _annotate_function(
        self,
        *,
        result: ContractAnalysisResult,
        resolver: TypeExpressionResolver,
        function_path: QualifiedPath,
    ) -> None:
        """Annotate one function from graph beliefs."""
        function: FunctionTrace = result.graph.functions[function_path.text()]
        all_arguments: tuple[arg, ...] | tuple[*tuple[arg, ...], arg] = (
            *function.node.args.posonlyargs,
            *function.node.args.args,
            *function.node.args.kwonlyargs,
        )
        if function.node.args.vararg is not None:
            all_arguments = (
                *all_arguments,
                function.node.args.vararg,
            )
        if function.node.args.kwarg is not None:
            all_arguments = (
                *all_arguments,
                function.node.args.kwarg,
            )
        for argument in all_arguments:
            self._annotate_argument(
                result=result,
                resolver=resolver,
                function_path=function_path,
                argument=argument,
            )
        return_type: TypeExpression = self._type_for_path(
            result=result,
            path=function.return_path,
        )
        if (
            function.node.returns is not None
            and not self._should_replace_annotation(
                annotation=function.node.returns,
                replacement=return_type,
            )
        ):
            return
        function.node.returns = self._to_annotation(
            resolver=resolver,
            type_hint=return_type,
        )

    def _annotate_argument(
        self,
        *,
        result: ContractAnalysisResult,
        resolver: TypeExpressionResolver,
        function_path: QualifiedPath,
        argument: arg,
    ) -> None:
        """Annotate one argument if evidence exists."""
        if argument.arg in {"self", "cls"}:
            return
        argument_path: QualifiedPath = function_path.child(
            kind=PathSegmentKind.SYMBOL,
            name=argument.arg,
        )
        type_hint: TypeExpression = self._type_for_path(
            result=result,
            path=argument_path,
        )
        if (
            argument.annotation is not None
            and not self._should_replace_annotation(
                annotation=argument.annotation,
                replacement=type_hint,
            )
        ):
            return
        argument.annotation = self._to_annotation(
            resolver=resolver,
            type_hint=type_hint,
        )

    def _annotate_statement_list(
        self,
        *,
        context: AnnotationTraversalContext,
        statements: list[stmt],
        scope: QualifiedPath,
    ) -> None:
        """Annotate assignments recursively inside a statement list."""
        for index, statement in enumerate(iterable=tuple(statements)):
            replacement: stmt = self._annotate_statement(
                context=context,
                statement=statement,
                scope=scope,
            )
            statements[index] = replacement

    def _annotate_statement(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: stmt,
        scope: QualifiedPath,
    ) -> stmt:
        """Annotate one statement and recurse as needed."""
        replacement: stmt | AnnAssign = statement
        if self._annotate_definition_statement(
            context=context,
            statement=statement,
            scope=scope,
        ):
            return replacement
        if self._annotate_control_statement(
            context=context,
            statement=statement,
            scope=scope,
        ):
            return replacement
        if isinstance(statement, Assign):
            replacement = self._annotated_assignment(
                result=context.result,
                resolver=context.resolver,
                statement=statement,
                scope=scope,
            )
        elif isinstance(statement, AnnAssign):
            replacement = self._updated_annotated_assignment(
                result=context.result,
                resolver=context.resolver,
                statement=statement,
                scope=scope,
            )
        return replacement

    def _annotate_definition_statement(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: stmt,
        scope: QualifiedPath,
    ) -> bool:
        """Annotate nested definitions and return whether handled."""
        if isinstance(statement, FunctionDef | AsyncFunctionDef):
            self._annotate_function_body(
                context=context,
                function=statement,
                parent_scope=scope,
            )
            return True
        if isinstance(statement, ClassDef):
            self._annotate_class_body(
                context=context,
                class_node=statement,
                parent_scope=scope,
            )
            return True
        return False

    def _annotate_control_statement(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: stmt,
        scope: QualifiedPath,
    ) -> bool:
        """Annotate control-flow bodies and return whether handled."""
        handled: bool = True
        if isinstance(statement, If | With):
            self._annotate_if_or_with(
                context=context,
                statement=statement,
                scope=scope,
            )
        elif isinstance(statement, Match):
            self._annotate_match(
                context=context,
                statement=statement,
                scope=scope,
            )
        elif isinstance(statement, Try):
            self._annotate_try(
                context=context,
                statement=statement,
                scope=scope,
            )
        else:
            handled = False
        return handled

    def _annotate_if_or_with(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: If | With,
        scope: QualifiedPath,
    ) -> None:
        """Annotate an if or with body."""
        self._annotate_statement_list(
            context=context,
            statements=statement.body,
            scope=scope,
        )
        if isinstance(statement, If):
            self._annotate_statement_list(
                context=context,
                statements=statement.orelse,
                scope=scope,
            )

    def _annotate_match(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: Match,
        scope: QualifiedPath,
    ) -> None:
        """Annotate a match statement body."""
        for case in statement.cases:
            self._annotate_statement_list(
                context=context,
                statements=case.body,
                scope=scope,
            )

    def _annotate_try(
        self,
        *,
        context: AnnotationTraversalContext,
        statement: Try,
        scope: QualifiedPath,
    ) -> None:
        """Annotate try/except/else/finally statement bodies."""
        self._annotate_statement_list(
            context=context,
            statements=statement.body,
            scope=scope,
        )
        for handler in statement.handlers:
            self._annotate_statement_list(
                context=context,
                statements=handler.body,
                scope=scope,
            )
        self._annotate_statement_list(
            context=context,
            statements=statement.orelse,
            scope=scope,
        )
        self._annotate_statement_list(
            context=context,
            statements=statement.finalbody,
            scope=scope,
        )

    def _annotate_function_body(
        self,
        *,
        context: AnnotationTraversalContext,
        function: FunctionNode,
        parent_scope: QualifiedPath,
    ) -> None:
        """Annotate statements inside one function."""
        function_scope: QualifiedPath = context.function_paths.get(
            id(function),
            parent_scope,
        )
        self._annotate_statement_list(
            context=context,
            statements=function.body,
            scope=function_scope,
        )

    def _annotate_class_body(
        self,
        *,
        context: AnnotationTraversalContext,
        class_node: ClassDef,
        parent_scope: QualifiedPath,
    ) -> None:
        """Annotate statements inside one class."""
        class_scope: QualifiedPath = context.class_paths.get(
            id(class_node),
            parent_scope,
        )
        self._annotate_statement_list(
            context=context,
            statements=class_node.body,
            scope=class_scope,
        )

    def _annotated_assignment(
        self,
        *,
        result: ContractAnalysisResult,
        resolver: TypeExpressionResolver,
        statement: Assign,
        scope: QualifiedPath,
    ) -> stmt:
        """Convert a simple assignment into an annotated assignment."""
        if len(statement.targets) != 1:
            return statement
        target: expr = statement.targets[0]
        if not isinstance(target, Name | Attribute | Subscript):
            return statement
        target_path: QualifiedPath | None = self._assignment_target_path(
            result=result,
            target=target,
            scope=scope,
        )
        if target_path is None:
            return statement
        if isinstance(target, Name) and target_path.parent() != scope:
            return statement
        if isinstance(
            target,
            Attribute,
        ) and not self._should_annotate_attribute(
            result=result,
            scope=scope,
            attribute=target,
            path=target_path,
        ):
            return statement
        annotation: expr = self._to_annotation(
            resolver=resolver,
            type_hint=self._type_for_path(result=result, path=target_path),
        )
        return AnnAssign(
            target=target,
            annotation=annotation,
            value=statement.value,
            simple=1 if isinstance(target, Name) else 0,
        )

    def _updated_annotated_assignment(
        self,
        *,
        result: ContractAnalysisResult,
        resolver: TypeExpressionResolver,
        statement: AnnAssign,
        scope: QualifiedPath,
    ) -> AnnAssign:
        """Narrow weak existing annotations on annotated assignments."""
        target_path: QualifiedPath | None = self._assignment_target_path(
            result=result,
            target=statement.target,
            scope=scope,
        )
        if target_path is None:
            return statement
        type_hint: TypeExpression = self._type_for_path(
            result=result,
            path=target_path,
        )
        if not self._should_replace_annotation(
            annotation=statement.annotation,
            replacement=type_hint,
        ):
            return statement
        statement.annotation = self._to_annotation(
            resolver=resolver,
            type_hint=type_hint,
        )
        return statement

    def _assignment_target_path(
        self,
        *,
        result: ContractAnalysisResult,
        target: expr,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return the best known path for an assignment target."""
        target_path: QualifiedPath | None = result.graph.path_for_node(
            node=target,
        )
        if target_path is not None:
            return target_path
        if not isinstance(target, Name):
            return None
        return self._best_symbol_path(
            result=result,
            scope=scope,
            name=target.id,
        )

    def _best_symbol_path(
        self,
        *,
        result: ContractAnalysisResult,
        scope: QualifiedPath,
        name: str,
    ) -> QualifiedPath:
        """Resolve a name to local, nonlocal, or global evidence path."""
        local_path: QualifiedPath = scope.child(
            kind=PathSegmentKind.SYMBOL,
            name=name,
        )
        local_type: TypeExpression = self._type_for_path(
            result=result,
            path=local_path,
        )
        candidate_paths: tuple[QualifiedPath, ...] = (
            *self._ancestor_symbol_paths(scope=scope, name=name),
            QualifiedPath.root().child(
                kind=PathSegmentKind.SYMBOL,
                name=name,
            ),
        )
        for candidate_path in candidate_paths:
            candidate_type: TypeExpression = self._type_for_path(
                result=result,
                path=candidate_path,
            )
            if (
                local_type.key() == "builtins:object"
                and candidate_type.key() != "builtins:object"
            ):
                return candidate_path
        return local_path

    def _ancestor_symbol_paths(
        self,
        *,
        scope: QualifiedPath,
        name: str,
    ) -> tuple[QualifiedPath, ...]:
        """Return nearest ancestor symbol paths for a name."""
        paths: list[QualifiedPath] = []
        parent: QualifiedPath | None = scope.parent()
        while parent is not None:
            paths.append(
                parent.child(kind=PathSegmentKind.SYMBOL, name=name),
            )
            parent = parent.parent()
        return tuple(paths)

    def _should_annotate_attribute(
        self,
        *,
        result: ContractAnalysisResult,
        scope: QualifiedPath,
        attribute: Attribute,
        path: QualifiedPath,
    ) -> bool:
        """Return whether an attribute assignment should be annotated here."""
        if not isinstance(attribute.value, Name):
            return True
        if attribute.value.id not in {"self", "cls"}:
            return True
        class_path: QualifiedPath | None = self._nearest_class_path(
            scope=scope,
        )
        if class_path is None:
            return True
        assigned: set[str] = result.graph.class_assigned_attributes.get(
            class_path.text(),
            set(),
        )
        if attribute.attr in assigned:
            return False
        return (
            scope.segments[-1].name == "__init__" and path.parent() is not None
        )

    def _nearest_class_path(
        self,
        *,
        scope: QualifiedPath,
    ) -> QualifiedPath | None:
        """Return the nearest class path in a scope path."""
        segments: tuple[PathSegment, ...] = scope.segments
        for index in range(len(segments), 0, -1):
            candidate: QualifiedPath = QualifiedPath(segments=segments[:index])
            if candidate.segments[-1].kind is PathSegmentKind.CLASS:
                return candidate
        return None

    def _should_replace_annotation(
        self,
        *,
        annotation: expr,
        replacement: TypeExpression,
    ) -> bool:
        """Return whether an existing annotation is intentionally weak."""
        if self._annotation_is_any(annotation=annotation):
            return True
        if replacement.key() == "builtins:object":
            return False
        if isinstance(annotation, Name):
            return annotation.id == "object"
        return False

    def _annotation_is_any(self, *, annotation: expr) -> bool:
        """Return whether an annotation refers to Any."""
        if isinstance(annotation, Name):
            return annotation.id == "Any"
        if isinstance(annotation, Attribute):
            return annotation.attr == "Any"
        return False

    def _remove_forbidden_any_imports(self, *, module: Module) -> None:
        """Remove direct ``typing.Any`` imports from the output module."""
        new_body: list[stmt] = []
        for statement in module.body:
            if (
                isinstance(statement, ImportFrom)
                and statement.module == "typing"
            ):
                names: list[alias] = [
                    item for item in statement.names if item.name != "Any"
                ]
                if not names:
                    continue
                statement.names = names
            new_body.append(statement)
        module.body = new_body

    def _type_for_path(
        self,
        *,
        result: ContractAnalysisResult,
        path: QualifiedPath,
    ) -> TypeExpression:
        """Return the selected type for a path, falling back to object."""
        decision: TypeHintObjectiveDecision | None = result.objective.decision(
            path=path,
        )
        if decision is not None and decision.selected is not None:
            return decision.selected.type_hint
        belief_type: TypeExpression | None = result.query.type_of(
            path=path.text(),
        )
        if belief_type is not None:
            return belief_type
        return Types.object

    def _to_annotation(
        self,
        *,
        resolver: TypeExpressionResolver,
        type_hint: TypeExpression,
    ) -> expr:
        """Convert a type expression to an annotation AST node."""
        if type_hint.key() == "builtins:None":
            return Constant(value=None)
        return resolver.annotation(value=type_hint)


class ContractQuery:
    """Chainable query facade for analysis results."""

    def __init__(self, *, result: ContractAnalysisResult) -> None:
        """Initialize the query facade."""
        self._result: ContractAnalysisResult = result

    def belief(self, *, path: str) -> TypeBelief | None:
        """Return a belief by dotted path text."""
        return self._result.negotiation.belief(
            path=QualifiedPath.parse(value=path),
        )

    def type_of(self, *, path: str) -> TypeExpression | None:
        """Return the objective-selected type for a path."""
        decision: TypeHintObjectiveDecision | None = self.objective_decision(
            path=path,
        )
        if decision is not None and decision.selected is not None:
            return decision.selected.type_hint
        belief: TypeBelief | None = self.belief(path=path)
        if belief is None:
            return None
        return belief.selected()

    def objective_decision(
        self,
        *,
        path: str,
    ) -> TypeHintObjectiveDecision | None:
        """Return the optimization decision for one path."""
        return self._result.objective.decision(
            path=QualifiedPath.parse(value=path),
        )

    def objective(self) -> TypeHintObjectiveReport:
        """Return the full collective objective report."""
        return self._result.objective

    def features(self) -> AdvancedFeatureAnalysisResult:
        """Return the advanced feature analysis result."""
        return self._result.advanced

    def explain(self, *, path: str) -> ContractExplanation | None:
        """Return an explanation object for a path."""
        belief: TypeBelief | None = self.belief(path=path)
        if belief is None:
            return None
        lines: tuple[str, ...] = tuple(
            f"{candidate.confidence:.3f}: {candidate.explanation}"
            for candidate in sorted(
                belief.candidates.values(),
                key=lambda item: (-item.confidence, item.type_hint.key()),
            )
        )
        return ContractExplanation(
            path=belief.path,
            selected=belief.selected(),
            entropy=belief.entropy(),
            lines=lines,
        )

    def paths(self) -> tuple[str, ...]:
        """Return all known belief paths."""
        return tuple(
            belief.path.text() for belief in self._result.negotiation.beliefs
        )


class ContractAnalyzer:
    """Parse Python source, build a contract graph, and negotiate types."""

    def __init__(
        self,
        *,
        config: ContractNegotiationConfig | None = None,
        objective_config: TypeHintObjectiveConfig | None = None,
    ) -> None:
        """Initialize the analyzer."""
        self._config: ContractNegotiationConfig = (
            config if config is not None else ContractNegotiationConfig()
        )
        self._objective_config: TypeHintObjectiveConfig | None = (
            objective_config
        )

    def analyze(
        self,
        *,
        source: str,
        filename: str = "<unknown>",
    ) -> ContractAnalysisResult:
        """Analyze source code with the contract ant-farm algorithm."""
        module: Module = parse(source=source, filename=filename, mode="exec")
        graph_builder: ContractGraphBuilder = ContractGraphBuilder()
        graph: ContractGraph = graph_builder.build(module=module)
        negotiator: ContractNegotiator = ContractNegotiator(
            config=self._config,
        )
        advanced: AdvancedFeatureAnalysisResult = AdvancedFeatureSeeder().seed(
            graph=graph,
            module=module,
        )
        negotiation: ContractNegotiationResult = negotiator.solve(graph=graph)
        objective_solver: CollectiveTypeHintObjectiveSolver = (
            CollectiveTypeHintObjectiveSolver(config=self._objective_config)
        )
        objective: TypeHintObjectiveReport = objective_solver.solve(
            beliefs=negotiation.beliefs,
        )
        return ContractAnalysisResult(
            source=source,
            module=module,
            graph=graph,
            negotiation=negotiation,
            objective=objective,
            advanced=advanced,
        )
