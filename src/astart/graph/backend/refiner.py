"""Vendored agnostic graph-only type inference engine.

This module is the proven research checkpoint engine, vendored into the
package so the clean ``src`` API can drive it. It parses untyped source once
into an AST graph, uses the vendored base semantic engine, applies generic
graph refinements, and unparses once. The typed benchmark is never read here.

It is intentionally excluded from the strict ``src`` lint/type gate (see the
``[tool.ruff]`` and ``[tool.basedpyright]`` excludes): it is research-grade
checkpoint code, not hand-written API code. Behavioural correctness is
covered by the conversion fidelity reports.

"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    BoolOp,
    Call,
    ClassDef,
    Compare,
    Constant,
    Dict,
    DictComp,
    Div,
    Expr,
    FloorDiv,
    For,
    FunctionDef,
    GeneratorExp,
    If,
    IfExp,
    Import,
    ImportFrom,
    Lambda,
    List,
    ListComp,
    Load,
    LShift,
    Mod,
    Module,
    Mult,
    Name,
    Not,
    Pow,
    Return,
    RShift,
    Set,
    Slice,
    Starred,
    Store,
    Sub,
    Subscript,
    Tuple,
    UnaryOp,
    With,
    Yield,
    YieldFrom,
    alias,
    arg,
    expr,
    operator,
    stmt,
)
from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, cast, final

from astart.graph.dispatch import LowercaseTransformer, LowercaseVisitor
from astart.graph.graph.semantics import (
    build_annotation,
    child_nodes,
    nodes_of_type,
    render_annotation,
)

type StrOrNone = str | None
type ListStr = list[str]
type SetStr = set[str]
type DictStr = dict[str, str]

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import EllipsisType

    from astart.graph.backend.engine import Parenthesized


@final
class Constants:
    """Group module-level constants.

    Attributes:
        object_names (Final[set[str]]): Grouped module constant.
        min_args_for_annotation (Final[int]): Grouped module constant.
        tuple_ellipsis_args (Final[int]): Grouped module constant.
        min_element_type_args (Final[int]): Grouped module constant.
        builtin_type_names (Final[set[str]]): Grouped module constant.
        abc_names (Final[set[str]]): Grouped module constant.

    """

    object_names: Final[set[str]] = {"object", "Any", "Unknown"}
    min_args_for_annotation: Final[int] = 2
    tuple_ellipsis_args: Final[int] = 2
    min_element_type_args: Final[int] = 2
    builtin_type_names: Final[set[str]] = {
        "int",
        "float",
        "str",
        "bool",
        "bytes",
        "None",
        "object",
    }
    abc_names: Final[set[str]] = {
        "Awaitable",
        "Callable",
        "Generator",
        "Iterable",
        "Iterator",
        "Mapping",
        "MutableMapping",
        "Sequence",
    }


def parse_ann(source: str) -> expr:
    """Build an annotation expression node from a type string.

    Args:
        source (str): The source examined while build an annotation
            expression node from a type string.

    Returns:
        expr: expr produced by this operation.

    """
    return build_annotation(text=source)


def ann_source(node: AST | None) -> str:
    """Render an annotation node for comparison or synthesis.

    Args:
        node (AST | None): The node examined while render an
            annotation node for comparison or synthesis.

    Returns:
        str: Rendered source text produced by this operation.

    """
    return render_annotation(node=node)


def norm(source: str) -> str:
    """Normalize type-source text for equality checks.

    Args:
        source (str): The source examined while normalize type-source text for
            equality checks.

    Returns:
        str: Rendered source text produced by this operation.

    """
    return (
        source.replace("typing.", "")
        .replace("collections.abc.", "")
        .replace(" ", "")
    )


def split_top_level(source: str, delimiter: str = "|") -> ListStr:
    """Split by a delimiter that is outside brackets and parentheses.

    Args:
        delimiter (str): Delimiter supplied as str for this operation.
        source (str): The source examined while split by a delimiter
            that is outside brackets and parentheses.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    parts: ListStr = []
    depth: int = 0
    chunk: ListStr = []
    for char in source:
        if char in "[(":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == delimiter and depth == 0:
            text: str = "".join(chunk).strip()
            if text:
                parts.append(text)
            chunk = []
        else:
            chunk.append(char)
    if text := "".join(chunk).strip():
        parts.append(text)
    return parts


def split_args(source: str) -> ListStr:
    """Split generic argument text at top-level commas.

    Args:
        source (str): The source examined while split generic argument text at
            top-level commas.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    parts: ListStr = []
    depth: int = 0
    chunk: ListStr = []
    for char in source:
        if char in "[(":
            depth += 1
        elif char in ")]":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            text: str = "".join(chunk).strip()
            if text:
                parts.append(text)
            chunk = []
        else:
            chunk.append(char)
    if text := "".join(chunk).strip():
        parts.append(text)
    return parts


def _are_types_compatible(type1: str, type2: str) -> bool:
    """Check if two types can be reasonably unioned together.

    Args:
        type1 (str): Type1 supplied as str for this operation.
        type2 (str): Type2 supplied as str for this operation.

    Returns:
        bool: Whether the requested condition holds.

    """
    norm1: str = norm(source=type1)
    norm2: str = norm(source=type2)
    primitives: frozenset[str] = frozenset(
        {"int", "float", "str", "bool", "bytes"},
    )
    containers: frozenset[str] = frozenset(
        {"list", "set", "tuple", "dict", "frozenset"},
    )
    is_primitive1: bool = any(
        norm1 == p or norm1.startswith(f"{p}[") for p in primitives
    )
    is_primitive2: bool = any(
        norm2 == p or norm2.startswith(f"{p}[") for p in primitives
    )
    is_container1: bool = any(norm1.startswith(c) for c in containers)
    is_container2: bool = any(norm2.startswith(c) for c in containers)
    if is_primitive1 and is_container2:
        return False
    if is_primitive2 and is_container1:
        return False
    return not (
        (
            norm1.startswith("dict")
            and (not norm2.startswith("dict"))
            and (norm2 not in {"object", "Any"})
        )
        or (
            norm2.startswith("dict")
            and (not norm1.startswith("dict"))
            and (norm1 not in {"object", "Any"})
        )
    )


def _collect_type_items(*sources: str) -> DictStr:
    """Collect type items from sources.

    Args:
        sources (str): Sources supplied as str for this operation.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    items: DictStr = {}
    for source in sources:
        if not source:
            continue
        for part in split_top_level(source=source):
            key: str = norm(source=part)
            if key == "Unknown":
                continue
            items[key] = part.strip()
    return items


def _filter_object_any(items: DictStr) -> DictStr:
    """Drop ``object``/``Any`` from a union when a concrete type remains.

    ``object`` is the top type, so ``object | None`` is exactly ``object``;
    in that case ``object`` must be kept rather than collapsing the union to
    the far narrower ``None``. ``object``/``Any`` are only filtered out when
    a genuinely concrete (non-``None``) member is present.

    Args:
        items (DictStr): Collection of items supplied for this operation.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    object_keys: SetStr = {"object", "Any"}
    has_concrete: bool = any(
        key not in object_keys and key != "None" for key in items
    )
    if has_concrete:
        return {
            key: value
            for key, value in items.items()
            if key not in object_keys
        }
    for key, value in items.items():
        if key in object_keys:
            return {key: value}
    return items


def _sort_type_items(items: DictStr) -> ListStr:
    """Sort type items for stable output.

    Args:
        items (DictStr): Collection of items supplied for this operation.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    return sorted(
        items.values(),
        key=lambda item: (
            {"int": 1, "float": 2, "str": 3, "bool": 4, "None": 99}.get(
                norm(source=item),
                50,
            ),
            norm(source=item),
        ),
    )


def merge_type_sources(*sources: str) -> str:
    """Merge annotation sources into a stable union.

    Intended for reassignment widening: a transient ``None`` initializer is
    dropped when concrete types are also assigned. To merely reorder an
    existing union annotation without discarding ``None``, use
    :func:`order_union_source` instead.

    Args:
        sources: Sources supplied as str for this operation.

    Returns:
        Rendered source text produced by this operation.

    """
    items: DictStr = _collect_type_items(*sources)
    if not items:
        return "object"
    items = _filter_object_any(items=items)
    if len(items) > 1 and "None" in items:
        del items["None"]
    if len(items) == 1:
        return next(iter(items.values()))
    ordered: ListStr = _sort_type_items(items=items)
    return " | ".join(ordered) if ordered else "object"


def order_union_source(source: str) -> str:
    """Return a union annotation reordered without dropping any member.

    Unlike :func:`merge_type_sources`, ``None`` is preserved: this is used to
    stabilize the ordering of an already-correct union annotation (such as a
    genuine ``int | None``) rather than to widen reassigned variables.

    Args:
        source (str): The source examined while return a union
            annotation reordered without dropping any member.

    Returns:
        str: str produced by this operation.

    """
    items: DictStr = _collect_type_items(source)
    if not items:
        return source
    items = _filter_object_any(items=items)
    if len(items) == 1:
        return next(iter(items.values()))
    ordered: ListStr = _sort_type_items(items=items)
    return " | ".join(ordered) if ordered else source


def element_type(source: str) -> str:
    """Infer an element type from a container annotation source.

    Args:
        source (str): The source examined while infer an element type from a
            container annotation source.

    Returns:
        str: Rendered source text produced by this operation.

    """
    text: str = source.strip()
    arms: ListStr = split_top_level(source=text)
    if len(arms) > 1:
        return merge_type_sources(*(element_type(source=arm) for arm in arms))
    normalized: str = norm(source=text)
    result: StrOrNone = _element_type_from_prefix(
        text=text,
        normalized=normalized,
    )
    if result is not None:
        return result
    if normalized.startswith("tuple[") and text.endswith("]"):
        args: ListStr = split_args(source=text[text.index("[") + 1 : -1])
        if len(args) == Constants.tuple_ellipsis_args and args[1] == "...":
            return args[0]
        return merge_type_sources(*args)
    if normalized.startswith("dict[") and text.endswith("]"):
        args = split_args(source=text[text.index("[") + 1 : -1])
        return args[0] if args else "object"
    return _element_type_from_special(normalized=normalized)


def _element_type_from_prefix(*, text: str, normalized: str) -> StrOrNone:
    """Extract element type from container prefixes.

    Args:
        normalized (str): Normalized supplied as str for this operation.
        text (str): Text supplied as str for this operation.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    for prefix in (
        "list",
        "Sequence",
        "Iterable",
        "Iterator",
        "set",
        "frozenset",
        "Generator",
    ):
        raw_prefix: str = f"{prefix}["
        if normalized.startswith(raw_prefix) and text.endswith("]"):
            return split_args(source=text[text.index("[") + 1 : -1])[0]
    return None


def _element_type_from_special(*, normalized: str) -> str:
    """Handle special case element types.

    Args:
        normalized (str): Normalized supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if normalized == "range":
        return "int"
    if normalized == "str":
        return "str"
    return "object"


def dict_key_type(source: str) -> str:
    """Infer mapping key type.

    Args:
        source (str): The source examined while infer mapping key type.

    Returns:
        str: str produced by this operation.

    """
    text: str = source.strip()
    if norm(source=text).startswith(
        ("dict[", "Mapping[", "MutableMapping["),
    ) and text.endswith("]"):
        args: ListStr = split_args(source=text[text.index("[") + 1 : -1])
        if len(args) >= Constants.min_element_type_args:
            return args[0]
    return "object"


def dict_value_type(source: str) -> str:
    """Infer mapping value type.

    Args:
        source (str): The source examined while infer mapping value type.

    Returns:
        str: str produced by this operation.

    """
    text: str = source.strip()
    if norm(source=text).startswith(
        ("dict[", "Mapping[", "MutableMapping["),
    ) and text.endswith("]"):
        args: ListStr = split_args(source=text[text.index("[") + 1 : -1])
        if len(args) >= Constants.min_element_type_args:
            return args[1]
    return "object"


def literal_type(node: AST) -> StrOrNone:
    """Return a literal expression type when obvious.

    Args:
        node (AST): The node examined while return a
            literal expression type when obvious.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if not isinstance(node, Constant):
        return None
    if node.value is None:
        return "None"
    if node.value is Ellipsis:
        return "object"
    return _literal_value_type(value=node.value)


def _literal_value_type(
    *,
    value: str | bytes | complex | bool | None | EllipsisType,
) -> StrOrNone:
    """Get type from literal value.

    Args:
        value (str | bytes | complex | bool | None | EllipsisType): The value
            examined while get type from literal value.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    if isinstance(value, bytes):
        return "bytes"
    return None


@dataclass(slots=True)
class FunctionFact:
    """Function information used by generic refinement.

    Attributes:
        local_classes (dict[str, ClassDef]): Local classes retained as
            dict[str, ClassDef] by this instance.
        local_functions (dict[str, FunctionFact]): Local functions retained as
            dict[str,
            FunctionFact] by this instance.
        node (FunctionDef | AsyncFunctionDef): AST node associated with this
            record.
        qualified_name (str): Identifier used to refer to the qualified.

    """

    node: FunctionDef | AsyncFunctionDef
    qualified_name: str
    local_functions: dict[str, FunctionFact] = field(default_factory=dict)
    local_classes: dict[str, ClassDef] = field(default_factory=dict)

    @property
    def return_source(self) -> str:
        """Get the return type annotation source.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return ann_source(node=self.node.returns)


@dataclass(slots=True)
class GraphFacts:
    """Generic AST facts collected before refinement.

    Attributes:
        call_argument_evidence (dict[tuple[str, str], ListStr]): Call argument
            evidence retained as dict[tuple[str,
            str], list[str]] by this instance.
        classes (dict[str, ClassDef]): Classes retained as dict[str, ClassDef]
            by this instance.
        constructor_evidence (dict[tuple[str, str], ListStr]): Constructor
            evidence retained as dict[tuple[str,
            str], list[str]] by this instance.
        functions (dict[str, FunctionFact]): Functions retained as dict[str,
            FunctionFact] by this instance.
        functions_by_simple_name (dict[str, list[FunctionFact]]): Identifier
            used to refer to the functions by simple.
        namedtuple_fields (dict[str, DictStr]): Namedtuple fields retained as
            dict[str,
            dict[str, str]] by this instance.

    """

    functions: dict[str, FunctionFact] = field(default_factory=dict)
    functions_by_simple_name: dict[str, list[FunctionFact]] = field(
        default_factory=lambda: defaultdict(list),
    )
    classes: dict[str, ClassDef] = field(default_factory=dict)
    namedtuple_fields: dict[str, DictStr] = field(default_factory=dict)
    call_argument_evidence: dict[tuple[str, str], ListStr] = field(
        default_factory=lambda: defaultdict(list),
    )
    constructor_evidence: dict[tuple[str, str], ListStr] = field(
        default_factory=lambda: defaultdict(list),
    )


class SignaturePreScanner(LowercaseVisitor):
    """Register every function and class before evidence collection.

    ``FactCollector`` infers expression types as it walks the tree, so a call
    argument whose type depends on a function defined later in the module would
    otherwise resolve to ``object``. Pre-registering all signatures lets call
    and constructor evidence see forward references (e.g. a value produced by a
    helper defined below its first use).

    """

    def __init__(self, facts: GraphFacts) -> None:
        """Initialize the pre-scanner with graph facts.

        Args:
            facts (GraphFacts): Facts supplied as GraphFacts for this
                operation.

        """
        self.facts: GraphFacts = facts
        self.path: ListStr = []
        self.function_stack: list[FunctionFact] = []

    def visit_classdef(self, node: ClassDef) -> None:
        """Register a class definition before evidence collection.

        Args:
            node (ClassDef): The node examined while register a class
                definition before evidence collection.

        """
        qual: str = ".".join([*self.path, node.name])
        self.facts.classes[qual] = node
        self.facts.classes[node.name] = node
        if is_namedtuple_class(node=node):
            self.facts.namedtuple_fields.setdefault(
                node.name,
                collect_class_annotations(node=node),
            )
        if self.function_stack:
            self.function_stack[-1].local_classes[node.name] = node
        self.path.append(node.name)
        self.generic_visit(node=node)
        self.path.pop()

    def visit_functiondef(self, node: FunctionDef) -> None:
        """Register a function definition before evidence collection.

        Args:
            node (FunctionDef): The node examined while register a function
                definition before evidence collection.

        """
        self._visit_function(node=node)

    def visit_asyncfunctiondef(self, node: AsyncFunctionDef) -> None:
        """Register an async function definition before evidence collection.

        Args:
            node (AsyncFunctionDef): The node examined while register an async
                function definition before evidence collection.

        """
        self._visit_function(node=node)

    def _visit_function(self, node: FunctionDef | AsyncFunctionDef) -> None:
        """Visit function.

        Args:
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        """
        qual: str = ".".join([*self.path, node.name])
        if qual not in self.facts.functions:
            fact: FunctionFact = FunctionFact(node=node, qualified_name=qual)
            self.facts.functions[qual] = fact
            self.facts.functions_by_simple_name[node.name].append(fact)
            if self.function_stack:
                self.function_stack[-1].local_functions[node.name] = fact
        else:
            fact = self.facts.functions[qual]
        self.path.append(node.name)
        self.function_stack.append(fact)
        self.generic_visit(node=node)
        self.function_stack.pop()
        self.path.pop()


class FactCollector(LowercaseVisitor):
    """Collect generic graph facts from the already converted AST."""

    def __init__(self, facts: GraphFacts | None = None) -> None:
        """Initialize the fact collector with optional graph facts.

        Args:
            facts (GraphFacts | None): Facts supplied as GraphFacts | None for
                this operation.

        """
        self.facts: GraphFacts = facts if facts is not None else GraphFacts()
        self.path: ListStr = []
        self.scope_stack: list[DictStr] = [{}]
        self.function_stack: list[FunctionFact] = []

    def visit_classdef(self, node: ClassDef) -> None:
        """Collect facts from a class definition.

        Args:
            node (ClassDef): The node examined while collect facts from a class
                definition.

        """
        qual: str = ".".join([*self.path, node.name])
        self.facts.classes[qual] = node
        self.facts.classes[node.name] = node
        if is_namedtuple_class(node=node):
            self.facts.namedtuple_fields.setdefault(
                node.name,
                collect_class_annotations(node=node),
            )
        if self.function_stack:
            self.function_stack[-1].local_classes[node.name] = node
        self.path.append(node.name)
        self.generic_visit(node=node)
        self.path.pop()

    def visit_functiondef(self, node: FunctionDef) -> None:
        """Collect facts from a function definition.

        Args:
            node (FunctionDef): The node examined while collect
                facts from a function definition.

        """
        self._visit_function(node=node)

    def visit_asyncfunctiondef(self, node: AsyncFunctionDef) -> None:
        """Collect facts from an async function definition.

        Args:
            node (AsyncFunctionDef): The node examined while collect facts
                from an async function definition.

        """
        self._visit_function(node=node)

    def visit_assign(self, node: Assign) -> None:
        """Collect facts from an assignment statement.

        Args:
            node (Assign): The node examined while collect
                facts from an assignment statement.

        """
        value_type: str = infer_expr_source(
            node=node.value,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )
        for target in node.targets:
            bind_target_source(
                target=target,
                source=value_type,
                scope=self.scope_stack[-1],
            )
        self.generic_visit(node=node)

    def visit_annassign(self, node: AnnAssign) -> None:
        """Collect facts from an annotated assignment.

        Args:
            node (AnnAssign): The node examined while collect
                facts from an annotated assignment.

        """
        target_name: StrOrNone = name_from_target(node=node.target)
        if target_name is not None:
            self.scope_stack[-1][target_name] = ann_source(
                node=node.annotation,
            )
        self.generic_visit(node=node)

    def visit_for(self, node: For) -> None:
        """Collect facts from a for loop.

        Args:
            node (For): The node examined while collect facts from a for loop.

        """
        iter_source: str = infer_expr_source(
            node=node.iter,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )
        bind_target_source(
            target=node.target,
            source=element_type(source=iter_source),
            scope=self.scope_stack[-1],
        )
        self.generic_visit(node=node)

    def visit_call(self, node: Call) -> None:
        """Collect evidence from function calls.

        Args:
            node (Call): The node examined while collect evidence from function
                calls.

        """
        self._collect_call_argument_evidence(node=node)
        self._collect_constructor_evidence(node=node)
        self._collect_namedtuple_constructor_evidence(node=node)
        self.generic_visit(node=node)

    @staticmethod
    def _scan_local_declarations(fact: FunctionFact) -> None:
        """Scan local declarations.

        Args:
            fact (FunctionFact): Collected semantic evidence for the current
                node.

        """
        for item in fact.node.body:
            if isinstance(item, (FunctionDef, AsyncFunctionDef)):
                local_qual: str = f"{fact.qualified_name}.{item.name}"
                local_fact: FunctionFact = FunctionFact(
                    node=item,
                    qualified_name=local_qual,
                )
                fact.local_functions[item.name] = local_fact
            elif isinstance(item, ClassDef):
                fact.local_classes[item.name] = item

    def _visit_function(self, node: FunctionDef | AsyncFunctionDef) -> None:
        """Visit function.

        Args:
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        """
        qual: str = ".".join([*self.path, node.name])
        fact: FunctionFact | None = self.facts.functions.get(qual)
        if fact is None:
            fact = FunctionFact(node=node, qualified_name=qual)
            self.facts.functions[qual] = fact
            self.facts.functions_by_simple_name[node.name].append(fact)
        if self.function_stack:
            self.function_stack[-1].local_functions[node.name] = fact
        self.path.append(node.name)
        self.function_stack.append(fact)
        self.scope_stack.append(scope_from_function_args(node=node))
        self._scan_local_declarations(fact=fact)
        self.generic_visit(node=node)
        self.scope_stack.pop()
        self.function_stack.pop()
        self.path.pop()

    def _collect_call_argument_evidence(self, node: Call) -> None:
        """Collect call argument evidence.

        Args:
            node (Call): AST node being inspected or transformed.

        """
        name: str = call_name(node=node.func)
        if not name:
            return
        candidate: FunctionFact | None = unique_function_by_name(
            facts=self.facts,
            name=name,
        )
        if candidate is None:
            return
        params: list[arg] = explicit_parameters(node=candidate.node)
        for index, arg_node in enumerate(iterable=node.args):
            if index >= len(params):
                continue
            source: str = infer_expr_source(
                node=arg_node,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            if source not in Constants.object_names:
                self.facts.call_argument_evidence[
                    candidate.qualified_name,
                    params[index].arg,
                ].append(source)
        for kw in node.keywords:
            if kw.arg is None:
                continue
            source = infer_expr_source(
                node=kw.value,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            if source not in Constants.object_names:
                self.facts.call_argument_evidence[
                    candidate.qualified_name,
                    kw.arg,
                ].append(source)

    def _get_init_params(self, class_name: str) -> ListStr:
        """Get __init__ parameter names for a class.

        Args:
            class_name (str): Identifier of the class being resolved.

        Returns:
            ListStr: list[str] produced by this operation.

        """
        class_node: ClassDef | None = self.facts.classes.get(class_name)
        if class_node is not None:
            init_function: FunctionDef | None = find_method(
                node=class_node,
                name="__init__",
            )
            if init_function is not None:
                return [
                    param.arg
                    for param in explicit_parameters(node=init_function)
                ]
        if class_name in self.facts.namedtuple_fields:
            return list(self.facts.namedtuple_fields[class_name])
        return []

    def _collect_positional_constructor_evidence(
        self,
        node: Call,
        class_name: str,
        init_params: ListStr,
    ) -> None:
        """Collect evidence from positional constructor arguments.

        Args:
            class_name (str): Identifier of the class being resolved.
            init_params (ListStr): Init params supplied as list[str] for this
                operation.
            node (Call): The node examined while collect evidence
                from positional constructor arguments.

        """
        for pos_index, arg_node in enumerate(iterable=node.args):
            if pos_index < len(init_params):
                source: str = infer_expr_source(
                    node=arg_node,
                    scope=self.scope_stack[-1],
                    facts=self.facts,
                    current_function=self.function_stack[-1]
                    if self.function_stack
                    else None,
                )
                if source not in Constants.object_names:
                    self.facts.constructor_evidence[
                        class_name,
                        init_params[pos_index],
                    ].append(source)

    def _collect_keyword_constructor_evidence(
        self,
        node: Call,
        class_name: str,
    ) -> None:
        """Collect evidence from keyword constructor arguments.

        Args:
            class_name (str): Identifier of the class being resolved.
            node (Call): The node examined while collect evidence from keyword
                constructor arguments.

        """
        for kw in node.keywords:
            if kw.arg is None:
                continue
            source: str = infer_expr_source(
                node=kw.value,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            if source not in Constants.object_names:
                self.facts.constructor_evidence[class_name, kw.arg].append(
                    source,
                )

    def _collect_constructor_evidence(self, node: Call) -> None:
        """Collect constructor argument evidence regardless of class order.

        Args:
            node (Call): The node examined while collect constructor
                argument evidence regardless of class order.

        """
        class_name: str = call_name(node=node.func)
        if not class_name:
            return
        init_params: ListStr = self._get_init_params(class_name=class_name)
        self._collect_positional_constructor_evidence(
            node=node,
            class_name=class_name,
            init_params=init_params,
        )
        self._collect_keyword_constructor_evidence(
            node=node,
            class_name=class_name,
        )

    def _collect_namedtuple_constructor_evidence(self, node: Call) -> None:
        """Collect namedtuple constructor evidence.

        Args:
            node (Call): AST node being inspected or transformed.

        """
        class_name: str = call_name(node=node.func)
        if class_name not in self.facts.namedtuple_fields:
            return
        for kw in node.keywords:
            if kw.arg is None:
                continue
            source: str = infer_expr_source(
                node=kw.value,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            if source not in Constants.object_names:
                current: str = self.facts.namedtuple_fields[class_name].get(
                    kw.arg,
                    "object",
                )
                self.facts.namedtuple_fields[class_name][kw.arg] = (
                    merge_type_sources(current, source)
                )


class GenericGraphRefiner(LowercaseTransformer):
    """Apply benchmark-independent graph refinements."""

    def __init__(self, facts: GraphFacts) -> None:
        """Initialize the refiner with graph facts.

        Args:
            facts (GraphFacts): Facts supplied as GraphFacts for this
                operation.

        """
        self.facts: GraphFacts = facts
        self.path: ListStr = []
        self.scope_stack: list[DictStr] = [{}]
        self.function_stack: list[FunctionFact] = []
        self.needed_imports: SetStr = set()
        self.annotated_names_stack: list[SetStr] = []
        self.class_attr_names_stack: list[SetStr] = []

    def visit_module(self, node: Module) -> Module:
        """Visit the module and apply final refinements.

        Args:
            node (Module): The node examined while visit the
                module and apply final refinements.

        Returns:
            Module: Module produced by this operation.

        """
        self.generic_visit(node=node)
        self._refine_module_constants(node=node)
        normalize_annotation_unions(node=node)
        self._finalize_imports(node=node)
        return node

    def visit_classdef(self, node: ClassDef) -> ClassDef:
        """Visit a class definition and apply refinements.

        Args:
            node (ClassDef): The node examined while visit a class
                definition and apply refinements.

        Returns:
            ClassDef: ClassDef produced by this operation.

        """
        class_name: str = node.name
        self.path.append(class_name)
        self.class_attr_names_stack.append(
            class_body_annotated_names(node=node),
        )
        self.generic_visit(node=node)
        self.class_attr_names_stack.pop()
        self.path.pop()
        self._apply_constructor_evidence_to_class(node=node)
        if is_namedtuple_class(node=node):
            self._refine_namedtuple_fields(node=node)
        self._refine_builtin_subclass_overrides(node=node)
        prune_redundant_class_attr_annotations(node=node)
        return node

    def visit_functiondef(self, node: FunctionDef) -> FunctionDef:
        """Visit a function definition and apply refinements.

        Args:
            node (FunctionDef): The node examined while visit a function
                definition and apply refinements.

        Returns:
            FunctionDef: FunctionDef produced by this operation.

        """
        return cast(typ="FunctionDef", val=self._visit_function(node=node))

    def visit_asyncfunctiondef(
        self,
        node: AsyncFunctionDef,
    ) -> AsyncFunctionDef:
        """Visit an async function definition and apply refinements.

        Args:
            node (AsyncFunctionDef): The node examined while visit an async
                function definition and apply refinements.

        Returns:
            AsyncFunctionDef: AsyncFunctionDef produced by this operation.

        """
        return cast(
            typ="AsyncFunctionDef",
            val=self._visit_function(node=node),
        )

    def visit_assign(self, node: Assign) -> stmt:
        """Visit an assignment and add type annotations where appropriate.

        Args:
            node (Assign): The node examined while visit an assignment
                and add type annotations where appropriate.

        Returns:
            stmt: stmt produced by this operation.

        """
        self.generic_visit(node=node)
        value_type: str = infer_expr_source(
            node=node.value,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )
        for target in node.targets:
            bind_target_source(
                target=target,
                source=value_type,
                scope=self.scope_stack[-1],
            )
        if len(node.targets) != 1:
            return node
        target: expr = node.targets[0]
        if (
            value_type in Constants.object_names
            or norm(source=value_type) in Constants.object_names
        ):
            return node
        if contains_unavailable_local_type(source=value_type):
            return node
        if (
            isinstance(target, Name)
            and self.annotated_names_stack
            and (target.id not in self.annotated_names_stack[-1])
            and should_annotate_local_name(name=target.id)
        ):
            self.annotated_names_stack[-1].add(target.id)
            self._record_imports_from_annotation(source=value_type)
            return AnnAssign(
                target=target,
                annotation=parse_ann(source=value_type),
                value=node.value,
                simple=1,
            )
        if (
            isinstance(target, Attribute)
            and self.function_stack
            and isinstance(target.value, Name)
            and (target.value.id in {"self", "cls"})
        ):
            self._record_imports_from_annotation(source=value_type)
            return AnnAssign(
                target=target,
                annotation=parse_ann(source=value_type),
                value=node.value,
                simple=0,
            )
        return node

    def visit_annassign(self, node: AnnAssign) -> stmt:
        """Visit an annotated assignment and refine the annotation.

        Args:
            node (AnnAssign): The node examined while visit an annotated
                assignment and refine the annotation.

        Returns:
            stmt: stmt produced by this operation.

        """
        self.generic_visit(node=node)
        target_name: StrOrNone = name_from_target(node=node.target)
        if target_name is None:
            return node
        value_type: StrOrNone = None
        if node.value is not None:
            value_type = infer_expr_source(
                node=node.value,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
        old_source: str = ann_source(node=node.annotation)
        if value_type is not None and should_replace_object_annotation(
            current=old_source,
            inferred=value_type,
        ):
            guarded: str = refined_annotation_source(
                current=old_source,
                candidate=value_type,
            )
            node.annotation = parse_ann(source=guarded)
            self._record_imports_from_annotation(source=guarded)
            old_source = guarded
        self.scope_stack[-1][target_name] = old_source
        return node

    def visit_for(self, node: For) -> For:
        """Visit a for loop and annotate the iteration variable.

        Args:
            node (For): The node examined while visit a for loop
                and annotate the iteration variable.

        Returns:
            For: For produced by this operation.

        """
        iter_type: str = infer_expr_source(
            node=node.iter,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )
        bind_target_source(
            target=node.target,
            source=element_type(source=iter_type),
            scope=self.scope_stack[-1],
        )
        self.generic_visit(node=node)
        return node

    def visit_with(self, node: With) -> With:
        """Visit a with statement and annotate context variables.

        Args:
            node (With): The node examined while visit a with
                statement and annotate context variables.

        Returns:
            With: With produced by this operation.

        """
        for item in node.items:
            if item.optional_vars is None:
                continue
            context_type: str = infer_expr_source(
                node=item.context_expr,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            bind_target_source(
                target=item.optional_vars,
                source=context_entry_source(source=context_type),
                scope=self.scope_stack[-1],
            )
        self.generic_visit(node=node)
        return node

    def visit_parenthesized(self, node: Parenthesized) -> Parenthesized:
        """Visit a Parenthesized node and preserve it through refinement.

        Args:
            node (Parenthesized): The node examined while visit a Parenthesized
                node and preserve it through refinement.

        Returns:
            Parenthesized: Parenthesized produced by this operation.

        """
        self.generic_visit(node=node.value)
        return node

    @staticmethod
    def _get_assignment_target(item: AST) -> Attribute | None:
        """Extract Attribute target from AnnAssign or Assign statements.

        Args:
            item (AST): Item supplied as AST for this operation.

        Returns:
            Attribute | None: Attribute | None produced by this operation.

        """
        if isinstance(item, AnnAssign):
            return (
                item.target
                if isinstance(item.target, Attribute)
                and item.value is not None
                else None
            )
        if isinstance(item, Assign):
            return (
                item.targets[0]
                if len(item.targets) == 1
                and isinstance(item.targets[0], Attribute)
                else None
            )
        return None

    @staticmethod
    def _resolve_param_name_for_field(
        *,
        field_name: str,
        field_norm: str,
        attr_to_param: DictStr,
        param_annotations: DictStr,
    ) -> StrOrNone:
        """Resolve the init param name for a given class field, or None.

        Args:
            attr_to_param (DictStr): Attr to param supplied as dict[str, str]
                for this operation.
            field_name (str): Identifier of the field being resolved.
            field_norm (str): Field norm supplied as str for this operation.
            param_annotations (DictStr): Param annotations supplied as
                dict[str, str] for this operation.

        Returns:
            StrOrNone: str | None produced by this operation.

        """
        param_name: StrOrNone = attr_to_param.get(field_name)
        if param_name is None and field_name in param_annotations:
            param_name = field_name
        if param_name is None:
            return None
        if field_norm not in Constants.object_names:
            param_source: str = param_annotations.get(param_name, "object")
            has_none: bool = "None" in norm(source=param_source)
            if not has_none or norm(source=param_source) == "None":
                return None
        return param_name

    @staticmethod
    def _fix_dict_get_method(item: FunctionDef) -> None:
        """Fix get method for dict subclasses.

        Args:
            item (FunctionDef): Item supplied as FunctionDef for this
                operation.

        """
        ensure_override(node=item)
        if len(item.args.args) >= Constants.min_args_for_annotation:
            item.args.args[1].annotation = parse_ann(source="str")
        item.returns = parse_ann(source="int")

    def _visit_function(
        self,
        node: FunctionDef | AsyncFunctionDef,
    ) -> FunctionDef | AsyncFunctionDef:
        """Visit function.

        Args:
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        Returns:
            FunctionDef | AsyncFunctionDef:
                Transformed AST node, or None when no replacement is produced.

        """
        fact: FunctionFact | None = self._fact_for_node(node=node)
        if fact is None:
            fact = FunctionFact(node=node, qualified_name=node.name)
        self.function_stack.append(fact)
        self.path.append(node.name)
        scope: DictStr = scope_from_function_args(node=node)
        self.scope_stack.append(scope)
        local_annotations: SetStr = existing_local_annotations(node=node)
        local_annotations.update(parameter_names(node=node))
        self.annotated_names_stack.append(local_annotations)
        self._apply_call_argument_evidence(node=node, fact=fact)
        self._refine_decorator_pattern(node=node, fact=fact)
        self._refine_redefined_local_annotations(node=node, fact=fact)
        self.generic_visit(node=node)
        self._refine_mutated_collection_locals(node=node, fact=fact)
        self._refine_return(node=node, fact=fact)
        self.annotated_names_stack.pop()
        self.scope_stack.pop()
        self.path.pop()
        self.function_stack.pop()
        return node

    def _fact_for_node(
        self,
        node: FunctionDef | AsyncFunctionDef,
    ) -> FunctionFact | None:
        """Fact for node.

        Args:
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        Returns:
            FunctionFact | None:
                Semantic evidence associated with the AST node, if available.

        """
        for fact in self.facts.functions.values():
            if fact.node is node:
                return fact
        return None

    def _apply_call_argument_evidence(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        fact: FunctionFact,
    ) -> None:
        """Apply call argument evidence.

        Args:
            fact (FunctionFact): Collected semantic evidence for the current
                node.
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        """
        for parameter in explicit_parameters(node=node):
            evidence: ListStr = self.facts.call_argument_evidence.get(
                (fact.qualified_name, parameter.arg),
                [],
            )
            if not evidence:
                continue
            observed: str = merge_type_sources(*evidence)
            current: str = ann_source(node=parameter.annotation)
            if should_replace_object_annotation(
                current=current,
                inferred=observed,
            ):
                parameter.annotation = parse_ann(source=observed)
                self._record_imports_from_annotation(source=observed)
                self.scope_stack[-1][parameter.arg] = observed

    def _refine_decorator_pattern(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        fact: FunctionFact,
    ) -> None:
        """Refine decorator pattern.

        Args:
            fact (FunctionFact): Collected semantic evidence for the current
                node.
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        """
        if not node.args.args:
            return
        callable_param: str = node.args.args[0].arg
        wrappers: list[FunctionDef | AsyncFunctionDef] = [
            item
            for item in node.body
            if isinstance(item, (FunctionDef, AsyncFunctionDef))
            and has_wraps_for(function=item, wrapped_name=callable_param)
        ]
        if not wrappers:
            returned_nested: FunctionDef | AsyncFunctionDef | None = (
                returned_nested_function(function=node, fact=fact)
            )
            if returned_nested is not None:
                self._refine_return(node=node, fact=fact)
            return
        wrapper: FunctionDef | AsyncFunctionDef = wrappers[0]
        wrapper_return: str = infer_wrapper_return(
            wrapper=wrapper,
            wrapped_name=callable_param,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=fact,
        )
        if wrapper_return == "object":
            wrapper_return = "R"
            self.needed_imports.add("TypeVar")
        if wrapper_return == "R":
            callable_source: str = "Callable[P, R]"
            outer_return: str = "Callable[P, R]"
            self.needed_imports.update({"Callable", "ParamSpec", "TypeVar"})
        else:
            callable_source = f"Callable[P, {wrapper_return}]"
            outer_return = f"Callable[P, {wrapper_return}]"
            self.needed_imports.update({"Callable", "ParamSpec"})
        node.args.args[0].annotation = parse_ann(source=callable_source)
        node.returns = parse_ann(source=outer_return)
        if wrapper.args.vararg is not None:
            wrapper.args.vararg.annotation = parse_ann(source="P.args")
        if wrapper.args.kwarg is not None:
            wrapper.args.kwarg.annotation = parse_ann(source="P.kwargs")
        wrapper.returns = parse_ann(source=wrapper_return)
        self._record_imports_from_annotation(source=callable_source)
        self._record_imports_from_annotation(source=outer_return)
        self._record_imports_from_annotation(source=wrapper_return)

    def _refine_return(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        fact: FunctionFact,
    ) -> None:
        """Refine return.

        Args:
            fact (FunctionFact): Collected semantic evidence for the current
                node.
            node (FunctionDef | AsyncFunctionDef): AST node being inspected or
                transformed.

        """
        current: str = ann_source(node=node.returns)
        refined: StrOrNone = infer_function_return_annotation(
            function=node,
            fact=fact,
            facts=self.facts,
            scope=self.scope_stack[-1],
        )
        if refined is None:
            return
        if should_replace_object_annotation(current=current, inferred=refined):
            node.returns = parse_ann(source=refined)
            self._record_imports_from_annotation(source=refined)

    def _refine_mutated_collection_locals(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        fact: FunctionFact,
    ) -> None:
        """Narrow local collection annotations from later mutations.

        Args:
            fact (FunctionFact): Fact supplied as FunctionFact for this
                operation.
            node (FunctionDef | AsyncFunctionDef): The node examined while
                narrow local
                collection annotations from later mutations.

        """
        local_scope: DictStr = scope_from_function_args(node=node)
        for statement in node.body:
            apply_statement_scope_effects(
                statement=statement,
                scope=local_scope,
                facts=self.facts,
                current_function=fact,
            )
        for statement in nodes_of_type(root=node, types=(AnnAssign,)):
            target_name: StrOrNone = name_from_target(node=statement.target)
            if target_name is None:
                continue
            inferred: StrOrNone = local_scope.get(target_name)
            if inferred is None:
                continue
            current: str = ann_source(node=statement.annotation)
            if _is_more_specific_container_annotation(
                current=current,
                inferred=inferred,
            ):
                statement.annotation = parse_ann(source=inferred)
                self._record_imports_from_annotation(source=inferred)

    def _collect_annassign_sources(
        self,
        statement: AnnAssign,
        scope: DictStr,
        fact: FunctionFact,
        assignment_sources: dict[str, ListStr],
    ) -> None:
        """Collect sources from annotated assignments.

        Args:
            assignment_sources (dict[str, ListStr]): Assignment sources
                supplied as
                dict[str, list[str]] for this operation.
            fact (FunctionFact): Fact supplied as FunctionFact for this
                operation.
            scope (DictStr): The scope examined while collect
                sources from annotated assignments.
            statement (AnnAssign): The statement examined while collect
                sources from annotated assignments.

        """
        target_name: StrOrNone = name_from_target(node=statement.target)
        if target_name is not None and statement.value is not None:
            inferred_value: str = infer_expr_source(
                node=statement.value,
                scope=scope,
                facts=self.facts,
                current_function=fact,
            )
            assignment_sources[target_name].append(inferred_value)

    def _collect_assign_sources(
        self,
        statement: Assign,
        scope: DictStr,
        fact: FunctionFact,
        assignment_sources: dict[str, ListStr],
    ) -> None:
        """Collect sources from regular assignments.

        Args:
            assignment_sources (dict[str, ListStr]): Assignment sources
                supplied as
                dict[str, list[str]] for this operation.
            fact (FunctionFact): Fact supplied as FunctionFact for this
                operation.
            scope (DictStr): The scope examined while collect
                sources from regular assignments.
            statement (Assign): The statement examined while collect
                sources from regular assignments.

        """
        value_source: str = infer_expr_source(
            node=statement.value,
            scope=scope,
            facts=self.facts,
            current_function=fact,
        )
        for target in statement.targets:
            target_name: StrOrNone = name_from_target(node=target)
            if target_name is not None:
                assignment_sources[target_name].append(value_source)

    def _apply_widened_annotations(
        self,
        node: FunctionDef | AsyncFunctionDef,
        assignment_sources: dict[str, ListStr],
    ) -> None:
        """Apply widened annotations to redefined variables.

        Args:
            assignment_sources (dict[str, ListStr]): Assignment sources
                supplied as
                dict[str, list[str]] for this operation.
            node (FunctionDef | AsyncFunctionDef): The node examined while
                apply widened
                annotations to redefined variables.

        """
        for statement in node.body:
            if not isinstance(statement, AnnAssign):
                continue
            target_name: StrOrNone = name_from_target(node=statement.target)
            if target_name is None:
                continue
            sources: ListStr = assignment_sources.get(target_name, [])
            if len(sources) <= 1:
                continue
            widened: str = merge_type_sources(*sources)
            current: str = ann_source(node=statement.annotation)
            if (
                norm(source=widened) in Constants.object_names
                and norm(source=current) not in Constants.object_names
            ):
                continue
            if norm(source=widened) != norm(source=current):
                if (
                    isinstance(statement.value, Constant)
                    and statement.value.value is None
                    and (len(sources) > 1)
                ):
                    statement.annotation = parse_ann(source=widened)
                    statement.value = None
                    statement.simple = 0
                    self._record_imports_from_annotation(source=widened)
                else:
                    statement.annotation = parse_ann(source=widened)
                    self._record_imports_from_annotation(source=widened)

    def _refine_redefined_local_annotations(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        fact: FunctionFact,
    ) -> None:
        """Widen local annotations that are intentionally reassigned.

        Args:
            fact (FunctionFact): Fact supplied as FunctionFact for this
                operation.
            node (FunctionDef | AsyncFunctionDef): The node examined while
                widen local
                annotations that are intentionally reassigned.

        """
        assignment_sources: dict[str, ListStr] = defaultdict(list)
        scope: DictStr = scope_from_function_args(node=node)
        for statement in node.body:
            if isinstance(statement, AnnAssign):
                self._collect_annassign_sources(
                    statement=statement,
                    scope=scope,
                    fact=fact,
                    assignment_sources=assignment_sources,
                )
            elif isinstance(statement, Assign):
                self._collect_assign_sources(
                    statement=statement,
                    scope=scope,
                    fact=fact,
                    assignment_sources=assignment_sources,
                )
        self._add_initial_annotations_for_reassignments(
            node=node,
            assignment_sources=assignment_sources,
        )
        self._apply_widened_annotations(
            node=node,
            assignment_sources=assignment_sources,
        )

    def _add_initial_annotations_for_reassignments(
        self,
        node: FunctionDef | AsyncFunctionDef,
        assignment_sources: dict[str, ListStr],
    ) -> None:
        """Add initial annotations for variables with multiple assignments.

        Args:
            assignment_sources (dict[str, ListStr]): Assignment sources
                supplied as
                dict[str, list[str]] for this operation.
            node (FunctionDef | AsyncFunctionDef): The node examined while add
                initial annotations
                for variables with multiple assignments.

        """
        seen_names: SetStr = set()
        for idx, statement in enumerate(iterable=node.body):
            if isinstance(statement, AnnAssign):
                name: StrOrNone = name_from_target(node=statement.target)
                if name is not None:
                    seen_names.add(name)
            elif isinstance(statement, Assign):
                for target in statement.targets:
                    assign_name: StrOrNone = name_from_target(node=target)
                    if assign_name is None or assign_name in seen_names:
                        continue
                    sources: ListStr = assignment_sources.get(
                        assign_name,
                        [],
                    )
                    if len(sources) > 1:
                        widened: str = merge_type_sources(*sources)
                        self._record_imports_from_annotation(source=widened)
                        if (
                            isinstance(statement.value, Constant)
                            and statement.value.value is None
                        ):
                            seen_names.add(assign_name)
                            temp_annassign: AnnAssign = AnnAssign(
                                target=cast(
                                    typ="Name | Attribute | Subscript",
                                    val=target,
                                ),
                                annotation=parse_ann(source=widened),
                                value=statement.value,
                                simple=1,
                            )
                            node.body[idx] = temp_annassign
                            break
                        new_annassign: AnnAssign = AnnAssign(
                            target=cast(
                                typ="Name | Attribute | Subscript",
                                val=target,
                            ),
                            annotation=parse_ann(source=widened),
                            value=statement.value,
                            simple=1,
                        )
                        node.body[idx] = new_annassign
                        seen_names.add(assign_name)
                        break

    def _refine_namedtuple_fields(self, node: ClassDef) -> None:
        """Refine namedtuple fields.

        Args:
            node (ClassDef): AST node being inspected or transformed.

        """
        field_types: DictStr = self.facts.namedtuple_fields.get(
            node.name,
            {},
        )
        for item in node.body:
            if not isinstance(item, AnnAssign):
                continue
            field_name: StrOrNone = name_from_target(node=item.target)
            if field_name is None:
                continue
            inferred: StrOrNone = field_types.get(field_name)
            if inferred is None:
                continue
            current: str = ann_source(node=item.annotation)
            if should_replace_object_annotation(
                current=current,
                inferred=inferred,
            ):
                item.annotation = parse_ann(source=inferred)
                self._record_imports_from_annotation(source=inferred)

    def _apply_constructor_evidence_to_params(
        self,
        node: ClassDef,
        init_function: FunctionDef,
    ) -> DictStr:
        """Apply constructor evidence to __init__ parameters.

        Args:
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.
            node (ClassDef): The node examined while apply constructor
                evidence to __init__ parameters.

        Returns:
            DictStr: dict[str, str] produced by this operation.

        """
        param_types: DictStr = {}
        for parameter in explicit_parameters(node=init_function):
            param_types[parameter.arg] = ann_source(node=parameter.annotation)
            evidence: ListStr = self.facts.constructor_evidence.get(
                (node.name, parameter.arg),
                [],
            )
            if evidence:
                param_inferred: str = merge_type_sources(*evidence)
                current: str = param_types[parameter.arg]
                if (
                    should_replace_object_annotation(
                        current=current,
                        inferred=param_inferred,
                    )
                    and norm(source=current) in Constants.object_names
                ):
                    parameter.annotation = parse_ann(source=param_inferred)
                    self._record_imports_from_annotation(source=param_inferred)
                    param_types[parameter.arg] = ann_source(
                        node=parameter.annotation,
                    )
        return param_types

    def _infer_field_type_from_value(self, item: AnnAssign) -> str:
        """Infer field type from its initial value.

        Args:
            item (AnnAssign): Item supplied as AnnAssign for this operation.

        Returns:
            str: str produced by this operation.

        """
        if item.value is None:
            return ""
        return infer_expr_source(
            node=item.value,
            scope=self.scope_stack[-1],
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )

    def _apply_field_type_to_init_param(
        self,
        field_name: str,
        field_inferred: str,
        init_function: FunctionDef,
    ) -> None:
        """Apply inferred field type to matching __init__ parameter.

        Args:
            field_inferred (str): Field inferred supplied as str for this
                operation.
            field_name (str): Identifier of the field being resolved.
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.

        """
        for parameter in explicit_parameters(node=init_function):
            if parameter.arg == field_name:
                guarded: str = refined_annotation_source(
                    current=ann_source(node=parameter.annotation),
                    candidate=field_inferred,
                )
                parameter.annotation = parse_ann(source=guarded)
                self._record_imports_from_annotation(source=guarded)
                self._update_self_attr_annotation_in_init(
                    field_name=field_name,
                    field_inferred=field_inferred,
                    init_function=init_function,
                )
                return

    def _update_self_attr_annotation_in_init(
        self,
        field_name: str,
        field_inferred: str,
        init_function: FunctionDef,
    ) -> None:
        """Update self.attribute annotations in __init__ to match.

        Args:
            field_inferred (str): Field inferred supplied as str for this
                operation.
            field_name (str): Identifier of the field being resolved.
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.

        """
        for item in nodes_of_type(root=init_function, types=(AnnAssign,)):
            if (
                isinstance(item.target, Attribute)
                and isinstance(item.target.value, Name)
                and (item.target.value.id == "self")
                and (item.target.attr == field_name)
            ):
                guarded: str = refined_annotation_source(
                    current=ann_source(node=item.annotation),
                    candidate=field_inferred,
                )
                item.annotation = parse_ann(source=guarded)
                self._record_imports_from_annotation(source=guarded)

    def _infer_value_from_assignment(
        self,
        item: AnnAssign | Assign,
        attr_name: str,
    ) -> str:
        """Infer value type from an assignment item.

        Args:
            attr_name (str): Identifier of the attr being resolved.
            item (AnnAssign | Assign): Item supplied as AnnAssign | Assign for
                this operation.

        Returns:
            str: str produced by this operation.

        """
        if item.value is None:
            return "object"
        if (
            isinstance(item.value, IfExp)
            and isinstance(item.value.test, Compare)
            and isinstance(item.value.test.left, Name)
            and isinstance(item.value.test.comparators[0], Constant)
            and (item.value.test.comparators[0].value is None)
            and isinstance(item.value.orelse, Name)
            and (item.value.orelse.id == attr_name)
        ):
            factory_type: str = infer_expr_source(
                node=item.value.body,
                scope=self.scope_stack[-1],
                facts=self.facts,
                current_function=self.function_stack[-1]
                if self.function_stack
                else None,
            )
            if factory_type and norm(source=factory_type) != "object":
                return order_union_source(source=f"{factory_type} | None")
        temp_scope: DictStr = dict(self.scope_stack[-1])
        temp_scope.pop(attr_name, None)
        return infer_expr_source(
            node=item.value,
            scope=temp_scope,
            facts=self.facts,
            current_function=self.function_stack[-1]
            if self.function_stack
            else None,
        )

    def _infer_element_type_from_usage(
        self,
        init_function: FunctionDef,
        attr_name: str,
        container_type: str,
    ) -> str:
        """Infer element type from method calls on container.

        Args:
            attr_name (str): Identifier of the attr being resolved.
            container_type (str): Container type supplied as str for this
                operation.
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.

        Returns:
            str: str produced by this operation.

        """
        container_norm: str = norm(source=container_type)
        if not container_norm.startswith("set["):
            return ""
        for item in nodes_of_type(root=init_function, types=(Call,)):
            if (
                isinstance(item.func, Attribute)
                and isinstance(item.func.value, Attribute)
                and isinstance(item.func.value.value, Name)
                and (item.func.value.value.id == "self")
                and (item.func.value.attr == attr_name)
                and (item.func.attr == "add")
                and item.args
            ):
                element_type: str = infer_expr_source(
                    node=item.args[0],
                    scope=self.scope_stack[-1],
                    facts=self.facts,
                    current_function=self.function_stack[-1]
                    if self.function_stack
                    else None,
                )
                if element_type and norm(source=element_type) != "object":
                    return f"set[{element_type}]"
        return ""

    def _infer_param_types_from_init_body(
        self,
        init_function: FunctionDef,
        param_types: DictStr,
    ) -> None:
        """Infer parameter types from self.attribute assignments.

        Args:
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.
            param_types (DictStr): Param types supplied as dict[str, str] for
                this operation.

        """
        init_param_names: SetStr = {
            parameter.arg
            for parameter in explicit_parameters(node=init_function)
        }
        for item in nodes_of_type(
            root=init_function,
            types=(AnnAssign, Assign),
        ):
            target: Attribute | None = self._get_assignment_target(item=item)
            if target is None:
                continue
            if (
                isinstance(item.value, Name)
                and item.value.id in init_param_names
            ):
                continue
            if (
                isinstance(target.value, Name)
                and target.value.id == "self"
                and (item.value is not None)
            ):
                attr_name: str = target.attr
                value_inferred: str = self._infer_value_from_assignment(
                    item=item,
                    attr_name=attr_name,
                )
                if value_inferred:
                    element_type_from_usage: str = (
                        self._infer_element_type_from_usage(
                            init_function=init_function,
                            attr_name=attr_name,
                            container_type=value_inferred,
                        )
                    )
                    if element_type_from_usage:
                        value_inferred = element_type_from_usage
                    self._update_param_annotation_for_attr(
                        init_function=init_function,
                        attr_name=attr_name,
                        value_inferred=value_inferred,
                        param_types=param_types,
                        force=True,
                    )
                else:
                    self._update_param_annotation_for_attr(
                        init_function=init_function,
                        attr_name=attr_name,
                        value_inferred=value_inferred,
                        param_types=param_types,
                        force=False,
                    )

    def _update_param_annotation_for_attr(
        self,
        *,
        init_function: FunctionDef,
        attr_name: str,
        value_inferred: str,
        param_types: DictStr,
        force: bool,
    ) -> None:
        """Update init param annotation and param_types for an attr.

        Args:
            attr_name (str): Identifier of the attr being resolved.
            force (bool): Force supplied as bool for this operation.
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.
            param_types (DictStr): Param types supplied as dict[str, str] for
                this operation.
            value_inferred (str): Value inferred supplied as str for this
                operation.

        """
        param_types[attr_name] = value_inferred
        for parameter in explicit_parameters(node=init_function):
            if parameter.arg != attr_name:
                continue
            current: str = ann_source(node=parameter.annotation)
            trivial: bool = (
                norm(source=current) in Constants.object_names
                or norm(source=current) == "None"
            )
            if force or trivial:
                parameter.annotation = parse_ann(source=value_inferred)
                self._record_imports_from_annotation(source=value_inferred)
                param_types[attr_name] = value_inferred
                self._update_self_attr_annotation_in_init(
                    field_name=attr_name,
                    field_inferred=value_inferred,
                    init_function=init_function,
                )
            break

    def _apply_constructor_evidence_to_fields(
        self,
        node: ClassDef,
        init_function: FunctionDef | None,
        param_types: DictStr,
    ) -> None:
        """Apply constructor evidence to class fields.

        Args:
            init_function (FunctionDef | None): Init function supplied as
                FunctionDef
                | None for this operation.
            node (ClassDef): The node examined while apply
                constructor evidence to class fields.
            param_types (DictStr): Param types supplied as dict[str, str] for
                this operation.

        """
        for item in node.body:
            if not isinstance(item, AnnAssign):
                continue
            field_name: StrOrNone = name_from_target(node=item.target)
            if field_name is None:
                continue
            field_ann: str = ann_source(node=item.annotation)
            field_norm: str = norm(source=field_ann)
            field_updated_from_param: bool = False
            if (
                field_norm == "None"
                and init_function is not None
                and (field_name in param_types)
            ):
                param_from_dict: str = param_types[field_name]
                if (
                    "None" in norm(source=param_from_dict)
                    and norm(source=param_from_dict) != "None"
                ):
                    item.annotation = parse_ann(source=param_from_dict)
                    self._record_imports_from_annotation(
                        source=param_from_dict,
                    )
                    field_ann = param_from_dict
                    field_norm = norm(source=param_from_dict)
                    field_updated_from_param = True
            field_inferred: str = self._infer_field_type_from_value(item=item)
            if (
                field_inferred
                and init_function is not None
                and (not self._is_descriptor_class(type_source=field_inferred))
                and (not field_updated_from_param)
            ):
                self._apply_field_type_to_init_param(
                    field_name=field_name,
                    field_inferred=field_inferred,
                    init_function=init_function,
                )
            current: str = ann_source(node=item.annotation)
            if field_inferred and should_replace_object_annotation(
                current=current,
                inferred=field_inferred,
            ):
                value_is_none: bool = (
                    isinstance(item.value, Constant)
                    and item.value.value is None
                )
                if value_is_none and "None" not in norm(source=field_inferred):
                    field_inferred = merge_type_sources(field_inferred, "None")
                item.annotation = parse_ann(source=field_inferred)
                self._record_imports_from_annotation(source=field_inferred)

    def _is_descriptor_class(self, *, type_source: str) -> bool:
        """Return whether a type name refers to a descriptor class.

        A descriptor defines ``__get__``, ``__set__``, or ``__delete__``;
        attributes typed as such a class are mediated by the data model, so
        the stored value type differs from the descriptor type.

        Args:
            type_source (str): Type source supplied as str for this operation.

        Returns:
            bool: Whether the requested condition holds.

        """
        class_node: ClassDef | None = self.facts.classes.get(
            norm(source=type_source),
        )
        if class_node is None:
            return False
        method_names: SetStr = {
            member.name
            for member in class_node.body
            if isinstance(member, (FunctionDef, AsyncFunctionDef))
        }
        return bool(method_names & {"__get__", "__set__", "__delete__"})

    def _apply_constructor_evidence_to_class(self, node: ClassDef) -> None:
        """Propagate constructor evidence into __init__ params and attrs.

        Args:
            node (ClassDef): The node examined while propagate constructor
                evidence into __init__ params and attrs.

        """
        init_function: FunctionDef | None = find_method(
            node=node,
            name="__init__",
        )
        param_types: DictStr = {}
        if init_function is not None:
            self._infer_param_types_from_init_body(
                init_function=init_function,
                param_types=param_types,
            )
            constructor_types: DictStr = (
                self._apply_constructor_evidence_to_params(
                    node=node,
                    init_function=init_function,
                )
            )
            for param_name, param_type in constructor_types.items():
                if (
                    param_name not in param_types
                    or norm(source=param_types[param_name])
                    in Constants.object_names
                ):
                    param_types[param_name] = param_type
        self._apply_constructor_evidence_to_fields(
            node=node,
            init_function=init_function,
            param_types=param_types,
        )
        if init_function is not None:
            self._propagate_init_param_types_to_fields(
                node=node,
                init_function=init_function,
            )

    def _propagate_init_param_types_to_fields(
        self,
        *,
        node: ClassDef,
        init_function: FunctionDef,
    ) -> None:
        """Give ``object`` class fields the type of the param they store.

        A bare ``self.attr = param`` assignment means the attribute's type is
        exactly the parameter's type. When the class-level annotation for
        such an attribute is still ``object``/``Any``/``Unknown`` (no
        independent evidence), adopt the parameter's resolved annotation.

        Args:
            init_function (FunctionDef): Init function supplied as FunctionDef
                for this operation.
            node (ClassDef): The node examined while give ``object`` class
                fields the type of the param they store.

        """
        attr_to_param: DictStr = self_attr_assignment_param_map(
            function=init_function,
        )
        param_annotations: DictStr = {
            parameter.arg: ann_source(node=parameter.annotation)
            for parameter in explicit_parameters(node=init_function)
        }
        for item in node.body:
            if not isinstance(item, AnnAssign):
                continue
            field_name: StrOrNone = name_from_target(node=item.target)
            if field_name is None:
                continue
            field_norm: str = norm(source=ann_source(node=item.annotation))
            if (
                field_norm != "None"
                and field_norm not in Constants.object_names
            ):
                continue
            param_name: StrOrNone = self._resolve_param_name_for_field(
                field_name=field_name,
                field_norm=field_norm,
                attr_to_param=attr_to_param,
                param_annotations=param_annotations,
            )
            if param_name is None:
                continue
            param_source: str = param_annotations.get(param_name, "object")
            if norm(source=param_source) in Constants.object_names:
                continue
            item.annotation = parse_ann(source=param_source)
            self._record_imports_from_annotation(source=param_source)

    def _fix_dict_update_method(self, item: FunctionDef) -> None:
        """Fix update method for dict subclasses.

        Args:
            item (FunctionDef): Item supplied as FunctionDef for this
                operation.

        """
        ensure_override(node=item)
        if len(item.args.args) >= Constants.min_args_for_annotation:
            item.args.args[1].annotation = parse_ann(
                source="Mapping[str, int] | Iterable[tuple[str, int]] | None",
            )
            self.needed_imports.update({"Iterable", "Mapping"})
        if item.args.vararg is not None:
            item.args.vararg.annotation = parse_ann(source="tuple[str, int]")
        if item.args.kwarg is not None:
            item.args.kwarg.annotation = parse_ann(source="int")
        item.returns = parse_ann(source="None")

    def _refine_builtin_subclass_overrides(self, node: ClassDef) -> None:
        """Refine builtin subclass overrides.

        Args:
            node (ClassDef): AST node being inspected or transformed.

        """
        base_names: SetStr = {base_name(node=base) for base in node.bases}
        if not base_names & {"list", "dict", "set"}:
            return
        for item in node.body:
            if not isinstance(item, FunctionDef):
                continue
            if item.name in {"append", "count", "add"}:
                ensure_override(node=item)
                self.needed_imports.add("override")
            if item.name == "get" and "dict" in base_names:
                self._fix_dict_get_method(item=item)

    def _record_imports_from_annotation(self, source: str) -> None:
        """Record imports from annotation.

        Args:
            source (str): Source text used for inference or transformation.

        """
        for name in (
            "Awaitable",
            "Callable",
            "Generator",
            "Iterable",
            "Iterator",
            "Mapping",
            "Sequence",
        ):
            if name in source:
                self.needed_imports.add(name)
        for name in (
            "ParamSpec",
            "TypeVar",
            "Self",
            "Final",
            "Protocol",
            "override",
            "cast",
        ):
            if name in source:
                self.needed_imports.add(name)

    def _refine_module_constants(self, node: Module) -> None:
        """Promote obvious module-level constants to Final[T].

        Args:
            node (Module): The node examined while promote obvious module-level
                constants to Final[T].

        """
        for statement in node.body:
            if not isinstance(statement, AnnAssign):
                continue
            if not isinstance(statement.target, Name):
                continue
            if not statement.target.id.isupper():
                continue
            current: str = ann_source(node=statement.annotation)
            if norm(source=current).startswith("Final["):
                continue
            if norm(source=current) in Constants.builtin_type_names:
                statement.annotation = parse_ann(source=f"Final[{current}]")
                self.needed_imports.add("Final")

    def _finalize_imports(self, node: Module) -> None:
        """Finalize imports.

        Args:
            node (Module): AST node being inspected or transformed.

        """
        if (
            uses_name(node=node, name="P")
            or "ParamSpec" in self.needed_imports
        ):
            self.needed_imports.add("ParamSpec")
            ensure_assignment(
                node=node,
                name="P",
                expression_source="ParamSpec('P')",
            )
        if uses_name(node=node, name="R") or "TypeVar" in self.needed_imports:
            self.needed_imports.add("TypeVar")
            ensure_assignment(
                node=node,
                name="R",
                expression_source="TypeVar('R')",
            )
        used: SetStr = collect_loaded_names(node=node) | self.needed_imports
        needed_typing: SetStr = {
            name
            for name in (
                "Final",
                "NamedTuple",
                "ParamSpec",
                "Protocol",
                "Self",
                "TypeVar",
                "cast",
                "override",
            )
            if name in used
        }
        needed_abc: SetStr = {
            name for name in Constants.abc_names if name in used
        }
        rewrite_imports(
            node=node,
            typing_names=needed_typing,
            _abc_names=needed_abc,
        )


def is_namedtuple_class(node: ClassDef) -> bool:
    """Return whether a class inherits from NamedTuple.

    Args:
        node (ClassDef): The node examined while return whether
            a class inherits from NamedTuple.

    Returns:
        bool: Whether the requested condition holds.

    """
    return any(base_name(node=base) == "NamedTuple" for base in node.bases)


def base_name(node: expr) -> str:
    """Return the unqualified base expression name.

    Args:
        node (expr): The node examined while return the
            unqualified base expression name.

    Returns:
        str: str produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Subscript):
        return base_name(node=node.value)
    if isinstance(node, Attribute):
        return node.attr
    return ""


def collect_class_annotations(node: ClassDef) -> DictStr:
    """Collect class-level annotations.

    Args:
        node (ClassDef): The node examined while collect class-level
            annotations.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    fields: DictStr = {}
    for item in node.body:
        if isinstance(item, AnnAssign):
            name: StrOrNone = name_from_target(node=item.target)
            if name is not None:
                fields[name] = ann_source(node=item.annotation)
    return fields


def prune_redundant_class_attr_annotations(node: ClassDef) -> None:
    """Ensure each instance attribute is declared at most once.

    Two declaration patterns trip ``reportRedeclaration``:

    * The v15 stage synthesizes a value-less class-body declaration (``x: T``)
      while the v18 refiner annotates the instance assignment (``self.x: T``).
    * ``__init__`` and a property setter (or another method) each annotate the
      same ``self.attr``.

    Resolution keeps a single annotated declaration per attribute. The first
    ``self.attr`` annotation in body order is kept; later ones are downgraded
    to plain assignments. A value-less class-body declaration covered by a
    surviving ``self.attr`` annotation is then removed. Class-body
    declarations that carry a value (e.g. dataclass-style fields) are left
    intact so their default values are preserved.

    Args:
        node (ClassDef): The node examined while ensure each instance
            attribute is declared at most once.

    """
    seen_self_annotations: SetStr = set()
    valued_class_decls: SetStr = {
        item.target.id
        for item in node.body
        if isinstance(item, AnnAssign)
        and isinstance(item.target, Name)
        and (item.value is not None)
    }
    for item in node.body:
        if not isinstance(item, FunctionDef):
            continue
        if item.args.args and item.args.args[0].arg != "self":
            continue
        _downgrade_self_attr_annotations(
            function=item,
            valued_class_decls=valued_class_decls,
            seen=seen_self_annotations,
        )
    node.body = [
        item
        for item in node.body
        if not (
            isinstance(item, AnnAssign)
            and item.value is None
            and isinstance(item.target, Name)
            and (item.target.id in seen_self_annotations)
        )
    ]


def _downgrade_self_attr_annotations(
    *,
    function: FunctionDef,
    valued_class_decls: SetStr,
    seen: SetStr,
) -> None:
    """Downgrade duplicate ``self.attr`` annotations within a method body.

    Args:
        function (FunctionDef): The function examined while downgrade duplicate
            ``self.attr`` annotations within a method body.
        seen (SetStr): Seen supplied as set[str] for this operation.
        valued_class_decls (SetStr): Valued class decls supplied as set[str]
            for this operation.

    """
    new_body: list[stmt] = []
    for statement in function.body:
        replacement: stmt = statement
        if (
            isinstance(statement, AnnAssign)
            and statement.value is not None
            and isinstance(statement.target, Attribute)
            and isinstance(statement.target.value, Name)
            and (statement.target.value.id == "self")
        ):
            attr: str = statement.target.attr
            if attr in seen or attr in valued_class_decls:
                replacement = Assign(
                    targets=[statement.target],
                    value=statement.value,
                )
            else:
                seen.add(attr)
        new_body.append(replacement)
    function.body = new_body


def class_body_annotated_names(node: ClassDef) -> SetStr:
    """Return the names declared by class-body annotations.

    Only simple ``name: T`` declarations directly in the class body count.
    These names already constitute a declaration, so an additional annotated
    ``self.name`` assignment in a method would be flagged as an obscured
    redeclaration.

    Args:
        node (ClassDef): The node examined while return the names
            declared by class-body annotations.

    Returns:
        SetStr: set[str] produced by this operation.

    """
    names: SetStr = set()
    for item in node.body:
        if isinstance(item, AnnAssign):
            name: StrOrNone = name_from_target(node=item.target)
            if name is not None and isinstance(item.target, Name):
                names.add(name)
    return names


def explicit_parameters(node: FunctionDef | AsyncFunctionDef) -> list[arg]:
    """Return parameters excluding implicit self/cls.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while return
            parameters excluding implicit self/cls.

    Returns:
        list[arg]: list[arg] produced by this operation.

    """
    params: list[arg] = [*node.args.posonlyargs, *node.args.args]
    if params and params[0].arg in {"self", "cls"}:
        params = params[1:]
    params.extend(node.args.kwonlyargs)
    return params


def all_parameters(node: FunctionDef | AsyncFunctionDef) -> list[arg]:
    """Return all explicit AST parameter nodes.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while return
            all explicit AST parameter nodes.

    Returns:
        list[arg]: list[arg] produced by this operation.

    """
    return [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]


def parameter_names(node: FunctionDef | AsyncFunctionDef) -> SetStr:
    """Return every parameter name, including ``*args`` and ``**kwargs``.

    A parameter is already a declaration, so the refiner must not turn a later
    plain assignment to that name into an annotated assignment, which would be
    an obscured redeclaration of the parameter.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while return
            every parameter
            name, including ``*args`` and ``**kwargs``.

    Returns:
        SetStr: set[str] produced by this operation.

    """
    names: SetStr = {parameter.arg for parameter in all_parameters(node=node)}
    if node.args.vararg is not None:
        names.add(node.args.vararg.arg)
    if node.args.kwarg is not None:
        names.add(node.args.kwarg.arg)
    return names


def scope_from_function_args(
    node: FunctionDef | AsyncFunctionDef,
) -> DictStr:
    """Build a local scope from function annotations.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while build a
            local
            scope from function annotations.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    scope: DictStr = {}
    for parameter in all_parameters(node=node):
        scope[parameter.arg] = ann_source(node=parameter.annotation)
    if node.args.vararg is not None:
        scope[node.args.vararg.arg] = ann_source(
            node=node.args.vararg.annotation,
        )
    if node.args.kwarg is not None:
        scope[node.args.kwarg.arg] = ann_source(
            node=node.args.kwarg.annotation,
        )
    return scope


def bind_target_source(
    *,
    target: AST,
    source: str,
    scope: DictStr,
) -> None:
    """Bind target names inside a flow scope.

    Args:
        scope (DictStr): The scope examined while bind target names inside a
            flow scope.
        source (str): The source examined while bind target names inside a flow
            scope.
        target (AST): The target examined while bind target names inside a flow
            scope.

    """
    if isinstance(target, Name):
        scope[target.id] = source
        return
    if isinstance(target, (Tuple, List)):
        args: ListStr
        if norm(source=source).startswith("tuple[") and source.endswith("]"):
            args = split_args(source=source[source.index("[") + 1 : -1])
        else:
            args = [element_type(source=source)] * len(target.elts)
        for index, item in enumerate(iterable=target.elts):
            bind_target_source(
                target=item,
                source=args[index]
                if index < len(args)
                else element_type(source=source),
                scope=scope,
            )


def name_from_target(node: AST) -> StrOrNone:
    """Return a simple target name.

    Args:
        node (AST): The node examined while return a simple target name.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    return None


def call_name(node: AST) -> str:
    """Return the call target name.

    Args:
        node (AST): The node examined while return the call target name.

    Returns:
        str: str produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    if isinstance(node, Call):
        return call_name(node=node.func)
    return ""


def unique_function_by_name(
    *,
    facts: GraphFacts,
    name: str,
) -> FunctionFact | None:
    """Resolve a non-ambiguous function by simple name.

    Args:
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.

    Returns:
        FunctionFact | None: FunctionFact | None produced by this operation.

    """
    candidates: list[FunctionFact] = facts.functions_by_simple_name.get(
        name,
        [],
    )
    if len(candidates) == 1:
        return candidates[0]
    return None


def _infer_collection_literal(
    *,
    node: List | Set | Tuple | Dict,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer type for collection literals.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (List | Set | Tuple | Dict): The node examined while infer type
            for collection literals.
        scope (DictStr): The scope examined while infer type for collection
            literals.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if isinstance(node, List):
        item_sources: ListStr = [
            infer_expr_source(
                node=item,
                scope=scope,
                facts=facts,
                current_function=current_function,
            )
            for item in node.elts
        ]
        return f"list[{merge_type_sources(*item_sources)}]"
    if isinstance(node, Set):
        item_sources = [
            infer_expr_source(
                node=item,
                scope=scope,
                facts=facts,
                current_function=current_function,
            )
            for item in node.elts
        ]
        return f"set[{merge_type_sources(*item_sources)}]"
    if isinstance(node, Tuple):
        return (
            "tuple["
            + ", ".join(
                infer_expr_source(
                    node=item,
                    scope=scope,
                    facts=facts,
                    current_function=current_function,
                )
                for item in node.elts
            )
            + "]"
        )
    return _infer_dict_literal(
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def _infer_dict_literal(
    *,
    node: Dict,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for dict literals.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Dict): The node examined while infer type for dict literals.
        scope (DictStr): The scope examined while infer type for dict literals.

    Returns:
        str: str produced by this operation.

    """
    keys: ListStr = []
    values: ListStr = []
    for key_node, value_node in zip(node.keys, node.values, strict=True):
        value_source: str = infer_expr_source(
            node=value_node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if key_node is None:
            keys.append(dict_key_type(source=value_source))
            values.append(dict_value_type(source=value_source))
            continue
        keys.append(
            infer_expr_source(
                node=key_node,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
        values.append(value_source)
    return f"dict[{merge_type_sources(*keys)}, {merge_type_sources(*values)}]"


def _infer_comprehension(
    *,
    node: ListComp | GeneratorExp | DictComp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer type for comprehensions.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (ListComp | GeneratorExp | DictComp): The node examined while
            infer type for comprehensions.
        scope (DictStr): The scope examined while infer type for
            comprehensions.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    local: DictStr = dict(scope)
    for generator in node.generators:
        iter_source: str = infer_expr_source(
            node=generator.iter,
            scope=local,
            facts=facts,
            current_function=current_function,
        )
        bind_target_source(
            target=generator.target,
            source=element_type(source=iter_source),
            scope=local,
        )
    if isinstance(node, ListComp):
        elt_source: str = infer_expr_source(
            node=node.elt,
            scope=local,
            facts=facts,
            current_function=current_function,
        )
        return f"list[{elt_source}]"
    if isinstance(node, GeneratorExp):
        elt_source = infer_expr_source(
            node=node.elt,
            scope=local,
            facts=facts,
            current_function=current_function,
        )
        return f"Generator[{elt_source}, None, None]"
    return _infer_dictcomp(
        node=node,
        scope=local,
        facts=facts,
        current_function=current_function,
    )


def _infer_dictcomp(
    *,
    node: DictComp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for dict comprehensions.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (DictComp): The node examined while infer type for dict
            comprehensions.
        scope (DictStr): The scope examined while infer type for dict
            comprehensions.

    Returns:
        str: str produced by this operation.

    """
    key_source: str = infer_expr_source(
        node=node.key,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    value_source: str = infer_expr_source(
        node=node.value,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    return f"dict[{key_source}, {value_source}]"


def _infer_ifexp(
    *,
    node: IfExp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for IfExp (ternary) expressions.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (IfExp): The node examined while infer type for IfExp (ternary)
            expressions.
        scope (DictStr): The scope examined while infer type
            for IfExp (ternary) expressions.

    Returns:
        str: str produced by this operation.

    """
    body_source: str = infer_expr_source(
        node=node.body,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    orelse_source: str = infer_expr_source(
        node=node.orelse,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    return _merge_ifexp_types(
        body_source=body_source,
        orelse_source=orelse_source,
    )


def _merge_ifexp_types(*, body_source: str, orelse_source: str) -> str:
    """Merge types from IfExp branches.

    Args:
        body_source (str): Body source supplied as str for this operation.
        orelse_source (str): Orelse source supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if norm(source=body_source) == "None":
        return orelse_source
    if norm(source=orelse_source) == "None":
        return body_source
    body_norm: str = norm(source=body_source)
    orelse_norm: str = norm(source=orelse_source)
    return _merge_container_types(
        body_source=body_source,
        orelse_source=orelse_source,
        body_norm=body_norm,
        orelse_norm=orelse_norm,
    )


def _merge_container_types(
    *,
    body_source: str,
    orelse_source: str,
    body_norm: str,
    orelse_norm: str,
) -> str:
    """Merge container types from IfExp branches.

    Args:
        body_norm (str): Body norm supplied as str for this operation.
        body_source (str): Body source supplied as str for this operation.
        orelse_norm (str): Orelse norm supplied as str for this operation.
        orelse_source (str): Orelse source supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    containers: frozenset[str] = frozenset(
        {"list", "set", "tuple", "dict", "frozenset"},
    )
    is_body_container: bool = any(body_norm.startswith(c) for c in containers)
    is_orelse_container: bool = any(
        orelse_norm.startswith(c) for c in containers
    )
    if is_body_container and (not is_orelse_container):
        if "None" in orelse_norm:
            return merge_type_sources(body_source, "None")
        return body_source
    if is_orelse_container and (not is_body_container):
        if "None" in body_norm:
            return merge_type_sources(orelse_source, "None")
        return orelse_source
    return merge_type_sources(body_source, orelse_source)


def _infer_operation(
    *,
    node: BinOp | BoolOp | Compare | UnaryOp | IfExp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer type for operations.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (BinOp | BoolOp | Compare | UnaryOp | IfExp): The node examined
            while infer type for operations.
        scope (DictStr): The scope examined while infer type for operations.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if isinstance(node, BinOp):
        return infer_binop_source(
            left=infer_expr_source(
                node=node.left,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
            right=infer_expr_source(
                node=node.right,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
            op=node.op,
        )
    if isinstance(node, BoolOp):
        return _infer_boolop(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if isinstance(node, Compare):
        return "bool"
    if isinstance(node, UnaryOp):
        return _infer_unaryop(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    return _infer_ifexp(
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def _infer_boolop(
    *,
    node: BoolOp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for BoolOp operations.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (BoolOp): The node examined while infer type for BoolOp
            operations.
        scope (DictStr): The scope examined while infer type for BoolOp
            operations.

    Returns:
        str: str produced by this operation.

    """
    value_sources: ListStr = [
        infer_expr_source(
            node=item,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        for item in node.values
    ]
    if all(norm(source=item) == "bool" for item in value_sources):
        return "bool"
    return merge_type_sources(*value_sources)


def _infer_unaryop(
    *,
    node: UnaryOp,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for UnaryOp operations.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (UnaryOp): The node examined while infer type for UnaryOp
            operations.
        scope (DictStr): The scope examined while infer type for UnaryOp
            operations.

    Returns:
        str: str produced by this operation.

    """
    if isinstance(node.op, Not):
        return "bool"
    return infer_expr_source(
        node=node.operand,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def _infer_subscript(
    *,
    node: Subscript,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for subscript operations.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Subscript): The node examined while infer type for subscript
            operations.
        scope (DictStr): The scope examined while infer type for subscript
            operations.

    Returns:
        str: str produced by this operation.

    """
    base_source: str = infer_expr_source(
        node=node.value,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if isinstance(node.slice, Slice):
        if norm(source=base_source).startswith("list["):
            return f"list[{element_type(source=base_source)}]"
        if norm(source=base_source).startswith("tuple["):
            return base_source
        if norm(source=base_source) == "str":
            return "str"
        return base_source
    if norm(source=base_source).startswith("dict["):
        return dict_value_type(source=base_source)
    return element_type(source=base_source)


def _infer_name(
    *,
    node: Name,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for Name nodes.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Name): The node examined while infer type for Name nodes.
        scope (DictStr): The scope examined while infer type for Name nodes.

    Returns:
        str: str produced by this operation.

    """
    if (
        current_function is not None
        and node.id in current_function.local_classes
    ):
        return "type[object]"
    return scope.get(
        node.id,
        class_or_function_type(name=node.id, facts=facts),
    )


def _infer_starred(
    *,
    node: Starred,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for Starred nodes.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Starred): The node examined while infer type for Starred nodes.
        scope (DictStr): The scope examined while infer type for Starred nodes.

    Returns:
        str: str produced by this operation.

    """
    return element_type(
        source=infer_expr_source(
            node=node.value,
            scope=scope,
            facts=facts,
            current_function=current_function,
        ),
    )


def _infer_lambda(
    *,
    node: Lambda,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer type for Lambda nodes.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Lambda): The node examined while infer type for Lambda nodes.
        scope (DictStr): The scope examined while infer type for Lambda nodes.

    Returns:
        str: str produced by this operation.

    """
    body_source: str = infer_expr_source(
        node=node.body,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    return f"Callable[..., {body_source}]"


def _infer_simple_expr(
    *,
    node: AST,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer type for simple expression nodes (literal, name, starred).

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (AST): The node examined while infer type for simple
            expression nodes (literal, name, starred).
        scope (DictStr): The scope examined while infer type for simple
            expression nodes (literal, name, starred).

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    literal: StrOrNone = literal_type(node=node)
    if literal is not None:
        return literal
    if isinstance(node, Name):
        return _infer_name(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if isinstance(node, Starred):
        return _infer_starred(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    return None


def _infer_complex_expr(
    *,
    node: Subscript | Attribute | Call | Lambda,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer type for complex expression nodes.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Subscript | Attribute | Call | Lambda): The node examined while
            infer type for complex expression nodes.
        scope (DictStr): The scope examined while infer type for complex
            expression nodes.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if isinstance(node, Subscript):
        return _infer_subscript(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if isinstance(node, Attribute):
        return infer_attribute_source(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if isinstance(node, Call):
        return infer_call_source(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    return _infer_lambda(
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def infer_expr_source(
    *,
    node: AST,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer a source-level type from an AST expression.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (AST): The node examined while infer a
            source-level type from an AST expression.
        scope (DictStr): The scope examined while infer a
            source-level type from an AST expression.

    Returns:
        str: Rendered source text produced by this operation.

    """
    simple_result: StrOrNone = _infer_simple_expr(
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if simple_result is not None:
        return simple_result
    if isinstance(node, (List, Set, Tuple, Dict)):
        collection_result: StrOrNone = _infer_collection_literal(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if collection_result is not None:
            return collection_result
    if isinstance(node, (ListComp, GeneratorExp, DictComp)):
        comprehension_result: StrOrNone = _infer_comprehension(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if comprehension_result is not None:
            return comprehension_result
    if isinstance(node, (BinOp, BoolOp, Compare, UnaryOp, IfExp)):
        operation_result: StrOrNone = _infer_operation(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if operation_result is not None:
            return operation_result
    if isinstance(node, (Subscript, Attribute, Call, Lambda)):
        complex_result: StrOrNone = _infer_complex_expr(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if complex_result is not None:
            return complex_result
    return "object"


def class_or_function_type(*, name: str, facts: GraphFacts) -> str:
    """Infer a reference type for a loaded name.

    Args:
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.

    Returns:
        str: str produced by this operation.

    """
    if name in facts.classes:
        return f"type[{name}]"
    if name == "None":
        return "None"
    if name in {"True", "False"}:
        return "bool"
    return _infer_function_reference_type(name=name, facts=facts)


def _infer_function_reference_type(*, name: str, facts: GraphFacts) -> str:
    """Infer type for function references.

    Args:
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.

    Returns:
        str: str produced by this operation.

    """
    candidates: list[FunctionFact] = facts.functions_by_simple_name.get(
        name,
        [],
    )
    if len(candidates) == 1:
        fact: FunctionFact = candidates[0]
        params: ListStr = [
            ann_source(node=param.annotation)
            for param in explicit_parameters(node=fact.node)
        ]
        return f"Callable[[{', '.join(params)}], {fact.return_source}]"
    return "object"


def _infer_builtin_type_call(name: str) -> StrOrNone:
    """Infer return type for built-in type constructors.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    type_map: DictStr = {
        "int": "int",
        "str": "str",
        "float": "float",
        "bool": "bool",
        "bytes": "bytes",
        "range": "range",
        "set": "set[object]",
        "list": "list[object]",
        "dict": "dict[object, object]",
        "frozenset": "frozenset[object]",
        "tuple": "tuple[object, ...]",
    }
    return type_map.get(name)


def _infer_builtin_int_call(name: str) -> StrOrNone:
    """Infer return type for built-in functions returning int.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if name in {"len", "hash", "id", "ord"}:
        return "int"
    return None


def _infer_builtin_bool_call(name: str) -> StrOrNone:
    """Infer return type for built-in functions returning bool.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if name in {
        "all",
        "any",
        "isinstance",
        "issubclass",
        "callable",
        "hasattr",
    }:
        return "bool"
    return None


def _infer_sum_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for sum function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for sum
            function.
        scope (DictStr): The scope examined while infer return type for sum
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if node.args:
        return element_type(
            source=infer_expr_source(
                node=node.args[0],
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return "int"


def _infer_minmax_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for min/max functions.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for min/max
            functions.
        scope (DictStr): The scope examined while infer return type for min/max
            functions.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if len(node.args) > 1:
        return merge_type_sources(
            *(
                infer_expr_source(
                    node=arg,
                    scope=scope,
                    facts=facts,
                    current_function=current_function,
                )
                for arg in node.args
            ),
        )
    if node.args:
        return element_type(
            source=infer_expr_source(
                node=node.args[0],
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return "object"


def _infer_sorted_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for sorted function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for sorted
            function.
        scope (DictStr): The scope examined while infer return type for sorted
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if node.args:
        arg_source: str = infer_expr_source(
            node=node.args[0],
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        return f"list[{element_type(source=arg_source)}]"
    return "list[object]"


def _infer_reduce_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for reduce function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for reduce
            function.
        scope (DictStr): The scope examined while infer return type for reduce
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if len(node.args) >= Constants.min_args_for_annotation:
        return element_type(
            source=infer_expr_source(
                node=node.args[1],
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return "object"


def _infer_groupby_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for groupby function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for groupby
            function.
        scope (DictStr): The scope examined while infer return type for groupby
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if not node.args:
        return "Iterable[tuple[object, Iterable[object]]]"
    input_type: str = infer_expr_source(
        node=node.args[0],
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    elem: str = element_type(source=input_type)
    key_type: str = "object"
    if norm(source=elem).startswith("tuple["):
        tuple_args: ListStr = split_args(
            source=elem[elem.index("[") + 1 : -1],
        )
        if tuple_args:
            key_type = tuple_args[0]
    return f"Iterable[tuple[{key_type}, Iterable[{elem}]]]"


def _infer_list_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for list function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for list
            function.
        scope (DictStr): The scope examined while infer return type for list
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if not node.args:
        return "list[object]"
    arg_type: str = infer_expr_source(
        node=node.args[0],
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if norm(source=arg_type).startswith("dict["):
        args: ListStr = split_args(
            source=arg_type[arg_type.index("[") + 1 : -1],
        )
        return f"list[{(args[0] if args else 'object')}]"
    if norm(source=arg_type).startswith(("dict_keys[", "dict_values[")):
        return f"list[{element_type(source=arg_type)}]"
    return f"list[{element_type(source=arg_type)}]"


def _infer_tuple_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for tuple function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for tuple
            function.
        scope (DictStr): The scope examined while infer return type for tuple
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if not node.args:
        return "tuple[()]"
    arg_source: str = infer_expr_source(
        node=node.args[0],
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    return f"tuple[{element_type(source=arg_source)}, ...]"


def _infer_dict_call(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for dict function.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer return type for dict
            function.
        scope (DictStr): The scope examined while infer return type for dict
            function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if node.args:
        arg_type: str = infer_expr_source(
            node=node.args[0],
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if norm(source=arg_type).startswith("dict_items["):
            args: ListStr = split_args(
                source=arg_type[arg_type.index("[") + 1 : -1],
            )
            if len(args) >= Constants.min_args_for_annotation:
                return f"dict[{args[0]}, {args[1]}]"
    return "dict[str, int]"


def _infer_complex_builtin_call(
    *,
    name: str,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for complex built-in functions.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.
        node (Call): The node examined while infer return
            type for complex built-in functions.
        scope (DictStr): The scope examined while infer return
            type for complex built-in functions.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    aggregation_result: StrOrNone = _infer_aggregation_builtin(
        name=name,
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if aggregation_result is not None:
        return aggregation_result
    container_result: StrOrNone = _infer_container_builtin(
        name=name,
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if container_result is not None:
        return container_result
    return None


def _infer_aggregation_builtin(
    *,
    name: str,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for aggregation built-ins.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.
        node (Call): The node examined while infer return type for aggregation
            built-ins.
        scope (DictStr): The scope examined while infer return
            type for aggregation built-ins.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if name == "sum":
        return _infer_sum_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name in {"max", "min"}:
        return _infer_minmax_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name == "sorted":
        return _infer_sorted_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name == "reduce":
        return _infer_reduce_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name == "groupby":
        return _infer_groupby_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    return None


def _infer_container_builtin(
    *,
    name: str,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> StrOrNone:
    """Infer return type for container built-ins.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.
        node (Call): The node examined while infer return type for container
            built-ins.
        scope (DictStr): The scope examined while infer return type for
            container built-ins.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if name == "list":
        return _infer_list_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name == "tuple":
        return _infer_tuple_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    if name == "dict":
        return _infer_dict_call(
            node=node,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    return None


def infer_call_source(
    *,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer a call result type.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Call): The node examined while infer a call result type.
        scope (DictStr): The scope examined while infer a call result type.

    Returns:
        str: str produced by this operation.

    """
    name: str = call_name(node=node.func)
    return _infer_call_by_name(
        name=name,
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def _infer_call_by_name(
    *,
    name: str,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer call type by name.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.
        node (Call): The node examined while infer call type by name.
        scope (DictStr): The scope examined while infer call type by name.

    Returns:
        str: str produced by this operation.

    """
    type_result: StrOrNone = _infer_builtin_type_call(name=name)
    if type_result is not None:
        return type_result
    int_result: StrOrNone = _infer_builtin_int_call(name=name)
    if int_result is not None:
        return int_result
    bool_result: StrOrNone = _infer_builtin_bool_call(name=name)
    if bool_result is not None:
        return bool_result
    complex_result: StrOrNone = _infer_complex_builtin_call(
        name=name,
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    if complex_result is not None:
        return complex_result
    return _infer_call_by_context(
        name=name,
        node=node,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )


def _infer_call_by_context(
    *,
    name: str,
    node: Call,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer call type from context.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        name (str): Identifier of the name being resolved.
        node (Call): The node examined while infer call type from context.
        scope (DictStr): The scope examined while infer call type from context.

    Returns:
        str: str produced by this operation.

    """
    if name in facts.classes:
        return name
    if current_function is not None and name in current_function.local_classes:
        return name
    fact: FunctionFact | None = unique_function_by_name(facts=facts, name=name)
    if fact is not None:
        return fact.return_source
    if isinstance(node.func, Attribute):
        receiver: str = infer_expr_source(
            node=node.func.value,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        return infer_method_source(
            receiver=receiver,
            method=node.func.attr,
            node=node,
            context=_InferenceContext(
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return "object"


def _infer_string_method(method: str) -> StrOrNone:
    """Infer return type for string methods.

    Args:
        method (str): Method supplied as str for this operation.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if method == "read_text":
        return "str"
    if method == "read_bytes":
        return "bytes"
    if method in {
        "upper",
        "lower",
        "strip",
        "replace",
        "title",
        "capitalize",
        "join",
    }:
        return "str"
    if method.startswith("is") or method in {"startswith", "endswith"}:
        return "bool"
    return None


def _infer_dict_method(
    *,
    receiver: str,
    method: str,
    node: Call,
    context: _InferenceContext,
) -> StrOrNone:
    """Infer return type for dict methods.

    Args:
        context (_InferenceContext): Context supplied as _InferenceContext for
            this operation.
        method (str): Method supplied as str for this operation.
        node (Call): The node examined while infer return type for dict
            methods.
        receiver (str): Receiver supplied as str for this operation.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    normalized: str = norm(source=receiver)
    if not normalized.startswith("dict["):
        return None
    args: ListStr = split_args(source=receiver[receiver.index("[") + 1 : -1])
    key_type: str = args[0] if args else "object"
    value_type: str = (
        args[1] if len(args) >= Constants.min_args_for_annotation else "object"
    )
    return _infer_dict_method_by_name(
        method=method,
        key_type=key_type,
        value_type=value_type,
        node=node,
        context=context,
    )


@dataclass(slots=True, frozen=True)
class _InferenceContext:
    """Context for type inference.

    Attributes:
        current_function (FunctionFact | None): Current function retained as
            FunctionFact | None by this instance.
        facts (GraphFacts): Facts retained as GraphFacts by this instance.
        scope (DictStr): Scope retained as dict[str, str] by this instance.

    """

    scope: DictStr
    facts: GraphFacts
    current_function: FunctionFact | None


def _infer_dict_method_by_name(
    *,
    method: str,
    key_type: str,
    value_type: str,
    node: Call,
    context: _InferenceContext,
) -> StrOrNone:
    """Infer return type for specific dict methods.

    Args:
        context (_InferenceContext): Context supplied as _InferenceContext for
            this operation.
        key_type (str): Key type supplied as str for this operation.
        method (str): Method supplied as str for this operation.
        node (Call): The node examined while infer return
            type for specific dict methods.
        value_type (str): Value type supplied as str for this operation.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if method == "keys":
        return f"dict_keys[{key_type}]"
    if method == "values":
        return f"dict_values[{value_type}]"
    if method == "items":
        return f"dict_items[{key_type}, {value_type}]"
    if method == "get":
        default: str = "None"
        if len(node.args) >= Constants.min_args_for_annotation:
            default = infer_expr_source(
                node=node.args[1],
                scope=context.scope,
                facts=context.facts,
                current_function=context.current_function,
            )
        return merge_type_sources(value_type, default)
    if method in {"update", "clear", "setdefault"}:
        return "None"
    return None


def _infer_collection_method(*, receiver: str, method: str) -> StrOrNone:
    """Infer return type for list/set methods.

    Args:
        method (str): Method supplied as str for this operation.
        receiver (str): Receiver supplied as str for this operation.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    normalized: str = norm(source=receiver)
    if not normalized.startswith(("list[", "set[")):
        return None
    if method in {"append", "extend", "add", "clear", "sort", "reverse"}:
        return "None"
    if method in {"pop", "popleft"}:
        return element_type(source=receiver)
    if method == "count":
        return "int"
    return None


def infer_method_source(
    *,
    receiver: str,
    method: str,
    node: Call,
    context: _InferenceContext,
) -> str:
    """Infer a method call from receiver type and protocol facts.

    Args:
        context (_InferenceContext): Context supplied as _InferenceContext for
            this operation.
        method (str): Method supplied as str for this operation.
        node (Call): The node examined while infer a method call
            from receiver type and protocol facts.
        receiver (str): Receiver supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    string_result: StrOrNone = _infer_string_method(method=method)
    if string_result is not None:
        return string_result
    dict_result: StrOrNone = _infer_dict_method(
        receiver=receiver,
        method=method,
        node=node,
        context=context,
    )
    if dict_result is not None:
        return dict_result
    collection_result: StrOrNone = _infer_collection_method(
        receiver=receiver,
        method=method,
    )
    if collection_result is not None:
        return collection_result
    if receiver in context.facts.classes:
        cls: ClassDef = context.facts.classes[receiver]
        for item in cls.body:
            if isinstance(item, FunctionDef) and item.name == method:
                return ann_source(node=item.returns)
    return "object"


def infer_attribute_source(
    *,
    node: Attribute,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> str:
    """Infer attribute access type.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (Attribute): The node examined while infer attribute access type.
        scope (DictStr): The scope examined while infer attribute access type.

    Returns:
        str: str produced by this operation.

    """
    if node.attr == "__name__":
        return "str"
    if isinstance(node.value, Name):
        if node.value.id in facts.classes and class_inherits(
            node=facts.classes[node.value.id],
            base="Enum",
        ):
            return node.value.id
        receiver: str = scope.get(node.value.id, "object")
        class_node: ClassDef | None = facts.classes.get(receiver)
        if class_node is not None:
            attrs: DictStr = collect_instance_attributes(
                node=class_node,
                facts=facts,
                current_function=current_function,
            )
            if node.attr in attrs:
                return attrs[node.attr]
    return "object"


def _infer_add_result(*, left: str, right: str) -> str:
    """Infer result of addition.

    Args:
        left (str): Left supplied as str for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if norm(source=left) == norm(source=right):
        return left
    if {norm(source=left), norm(source=right)} <= {"int", "float"}:
        return (
            "float"
            if "float" in {norm(source=left), norm(source=right)}
            else "int"
        )
    return merge_type_sources(left, right)


def _infer_mult_result(*, left: str, right: str) -> str:
    """Infer result of multiplication.

    Args:
        left (str): Left supplied as str for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if {norm(source=left), norm(source=right)} <= {"int", "float"}:
        return (
            "float"
            if "float" in {norm(source=left), norm(source=right)}
            else "int"
        )
    if norm(source=left) == "str" and norm(source=right) == "int":
        return "str"
    if norm(source=left).startswith("list[") and norm(source=right) == "int":
        return left
    return left if norm(source=left) not in Constants.object_names else right


def _infer_numeric_binop_result(*, left: str, right: str) -> str:
    """Infer result of numeric binary operations.

    Args:
        left (str): Left supplied as str for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if {norm(source=left), norm(source=right)} <= {"int", "float"}:
        return (
            "float"
            if "float" in {norm(source=left), norm(source=right)}
            else "int"
        )
    return left if norm(source=left) not in Constants.object_names else right


def infer_binop_source(*, left: str, right: str, op: operator) -> str:
    """Infer a binary operator result.

    Args:
        left (str): Left supplied as str for this operation.
        op (operator): Op supplied as operator for this operation.
        right (str): Right supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    if isinstance(op, Div):
        return "float"
    if isinstance(op, Add):
        return _infer_add_result(left=left, right=right)
    if isinstance(op, Mult):
        return _infer_mult_result(left=left, right=right)
    if isinstance(
        op,
        (Sub, FloorDiv, Mod, Pow, BitAnd, BitOr, BitXor, LShift, RShift),
    ):
        return _infer_numeric_binop_result(left=left, right=right)
    return merge_type_sources(left, right)


def context_entry_source(source: str) -> str:
    """Infer with-statement optional variable type.

    Args:
        source (str): The source examined while infer with-statement optional
            variable type.

    Returns:
        str: str produced by this operation.

    """
    normalized: str = norm(source=source)
    if normalized.startswith("Generator[") and source.endswith("]"):
        return split_args(source=source[source.index("[") + 1 : -1])[0]
    if normalized.startswith("Iterator[") and source.endswith("]"):
        return split_args(source=source[source.index("[") + 1 : -1])[0]
    if normalized.startswith("ContextManager[") and source.endswith("]"):
        return split_args(source=source[source.index("[") + 1 : -1])[0]
    return source


def collect_instance_attributes(
    node: ClassDef,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> DictStr:
    """Collect self attribute assignments inside class methods.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (ClassDef): The node examined while collect self
            attribute assignments inside class methods.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    attrs: DictStr = {}
    for item in node.body:
        if not isinstance(item, FunctionDef):
            continue
        scope: DictStr = scope_from_function_args(node=item)
        for sub in nodes_of_type(root=item, types=(AnnAssign, Assign)):
            if (
                isinstance(sub, AnnAssign)
                and isinstance(sub.target, Attribute)
                and isinstance(sub.target.value, Name)
                and (sub.target.value.id == "self")
            ):
                attrs[sub.target.attr] = ann_source(node=sub.annotation)
            if isinstance(sub, Assign):
                value_source: str = infer_expr_source(
                    node=sub.value,
                    scope=scope,
                    facts=facts,
                    current_function=current_function,
                )
                for target in sub.targets:
                    if (
                        isinstance(target, Attribute)
                        and isinstance(target.value, Name)
                        and (target.value.id == "self")
                    ):
                        attrs[target.attr] = value_source
    return attrs


def refined_annotation_source(*, current: str, candidate: str) -> str:
    """Return ``candidate`` unless it downgrades ``current``.

    Encodes the authoritative-analysis principle: a later refinement pass may
    only refine the type the inference engine already produced, never make it
    strictly less informative. Concretely, a concrete ``current`` is never
    replaced by ``object``/``Any``/``Unknown``, and a ``None`` member present
    in ``current`` is never silently dropped (it is re-added to the
    candidate). Equal or genuinely-more-specific candidates pass through.

    Args:
        candidate (str): Candidate supplied as str for this operation.
        current (str): Current supplied as str for this operation.

    Returns:
        str: str produced by this operation.

    """
    current_key: str = norm(source=current)
    candidate_key: str = norm(source=candidate)
    if current_key == candidate_key:
        return candidate
    if candidate_key in Constants.object_names or candidate_key == "Unknown":
        if current_key in Constants.object_names or current_key == "Unknown":
            return candidate
        return current
    current_has_none: bool = "None" in _collect_type_items(current)
    candidate_has_none: bool = "None" in _collect_type_items(candidate)
    if current_has_none and (not candidate_has_none):
        return order_union_source(source=f"{candidate} | None")
    return candidate


def should_replace_object_annotation(current: str, inferred: str) -> bool:
    """Return whether an annotation should be narrowed.

    Args:
        current (str): Current supplied as str for this operation.
        inferred (str): Inferred supplied as str for this operation.

    Returns:
        bool: Whether the requested condition holds.

    """
    current_key: str = norm(source=current)
    inferred_key: str = norm(source=inferred)
    if inferred_key in Constants.object_names or inferred_key == "Unknown":
        return False
    if current_key in Constants.object_names:
        return True
    if "object" in current_key and "object" not in inferred_key:
        return True
    if current_key in {"int", "bool"} and inferred_key == "str":
        return True
    if current_key == "int" and inferred_key == "float":
        return True
    return _is_more_specific_container_annotation(
        current=current,
        inferred=inferred,
    )


def _is_more_specific_container_annotation(
    *,
    current: str,
    inferred: str,
) -> bool:
    """Return whether ``inferred`` narrows a generated container type.

    Args:
        current (str): Current supplied as str for this operation.
        inferred (str): Inferred supplied as str for this operation.

    Returns:
        bool: Whether the requested condition holds.

    """
    current_key: str = norm(source=current)
    inferred_key: str = norm(source=inferred)
    for prefix in ("list", "set", "tuple", "dict", "Generator"):
        if not (
            current_key.startswith(f"{prefix}[")
            and inferred_key.startswith(f"{prefix}[")
        ):
            continue
        if "object" in current_key and "object" not in inferred_key:
            return True
        if "|" in current_key and "|" not in inferred_key:
            return True
    return False


def has_wraps_for(
    *,
    function: FunctionDef | AsyncFunctionDef,
    wrapped_name: str,
) -> bool:
    """Return whether a wrapper is decorated with functools.wraps(wrapped).

    Args:
        function (FunctionDef | AsyncFunctionDef): The function examined while
            return whether a
            wrapper is decorated with functools.wraps(wrapped).
        wrapped_name (str): Identifier of the wrapped being resolved.

    Returns:
        bool: Whether the requested condition holds.

    """
    for decorator in function.decorator_list:
        if not isinstance(decorator, Call):
            continue
        if call_name(node=decorator.func) != "wraps":
            continue
        if (
            decorator.args
            and isinstance(decorator.args[0], Name)
            and (decorator.args[0].id == wrapped_name)
        ):
            return True
        for kw in decorator.keywords:
            if (
                kw.arg == "wrapped"
                and isinstance(kw.value, Name)
                and (kw.value.id == wrapped_name)
            ):
                return True
    return False


def infer_wrapper_return(
    *,
    wrapper: FunctionDef | AsyncFunctionDef,
    wrapped_name: str,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact,
) -> str:
    """Infer a wrapper return type from its returns and wrapped call.

    Args:
        current_function (FunctionFact): Current function supplied as
            FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while infer a wrapper
            return type from its returns and wrapped call.
        wrapped_name (str): Identifier of the wrapped being resolved.
        wrapper (FunctionDef | AsyncFunctionDef): Wrapper supplied as
            FunctionDef |
            AsyncFunctionDef for this operation.

    Returns:
        str: str produced by this operation.

    """
    local: DictStr = dict(scope)
    for statement in wrapper.body:
        if isinstance(statement, Assign):
            value_type: str = infer_expr_source(
                node=statement.value,
                scope=local,
                facts=facts,
                current_function=current_function,
            )
            if calls_name(node=statement.value, name=wrapped_name):
                value_type = wrapped_return_from_annotation(
                    source=ann_source(
                        node=current_function.node.args.args[0].annotation,
                    ),
                )
            for target in statement.targets:
                bind_target_source(
                    target=target,
                    source=value_type,
                    scope=local,
                )
        if isinstance(statement, AnnAssign):
            target_name: StrOrNone = name_from_target(node=statement.target)
            if target_name is not None:
                local[target_name] = ann_source(node=statement.annotation)
        if isinstance(statement, Return) and statement.value is not None:
            if calls_name(node=statement.value, name=wrapped_name):
                return "R"
            return infer_expr_source(
                node=statement.value,
                scope=local,
                facts=facts,
                current_function=current_function,
            )
    return "R"


def wrapped_return_from_annotation(source: str) -> str:
    """Extract Callable return annotation source.

    Args:
        source (str): The source examined while extract
            Callable return annotation source.

    Returns:
        str: Rendered source text produced by this operation.

    """
    text: str = source.strip()
    if not norm(source=text).startswith("Callable[") or not text.endswith("]"):
        return "R"
    args: ListStr = split_args(source=text[text.index("[") + 1 : -1])
    if len(args) >= Constants.min_args_for_annotation:
        return args[-1]
    return "R"


def calls_name(node: AST, name: str) -> bool:
    """Return whether node contains a call to a named callable.

    Args:
        name (str): Identifier of the name being resolved.
        node (AST): The node examined while return whether
            node contains a call to a named callable.

    Returns:
        bool: Whether the requested condition holds.

    """
    for sub in nodes_of_type(root=node, types=(Call,)):
        if call_name(node=sub.func) == name:
            return True
    return False


def returned_nested_function(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
) -> FunctionDef | AsyncFunctionDef | None:
    """Return a nested function returned directly by a function.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            return a nested
            function returned directly by a function.

    Returns:
        FunctionDef | AsyncFunctionDef | None:
            FunctionDef | AsyncFunctionDef | None produced by this operation.

    """
    for statement in function.body:
        if isinstance(statement, Return) and isinstance(statement.value, Name):
            nested: FunctionFact | None = fact.local_functions.get(
                statement.value.id,
            )
            if nested is not None:
                return nested.node
    return None


def walk_without_nested_scopes(*, node: AST) -> Iterable[AST]:
    """Yield descendants without entering nested functions or classes.

    Args:
        node (AST): The node examined while yield descendants
            without entering nested functions or classes.

    Yields:
        AST: AST descendants visited without entering nested scopes.

    """
    for child in child_nodes(node=node):
        if isinstance(
            child,
            (FunctionDef, AsyncFunctionDef, ClassDef, Lambda),
        ):
            continue
        yield child
        yield from walk_without_nested_scopes(node=child)


def _apply_assign_effects(
    *,
    statement: Assign,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> None:
    """Apply type effects for Assign statements.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while apply type effects for Assign
            statements.
        statement (Assign): The statement examined while apply
            type effects for Assign statements.

    """
    value_source: str = infer_expr_source(
        node=statement.value,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    for target in statement.targets:
        bind_target_source(target=target, source=value_source, scope=scope)


def _apply_annassign_effects(
    *,
    statement: AnnAssign,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> None:
    """Apply type effects for AnnAssign statements.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while apply type
            effects for AnnAssign statements.
        statement (AnnAssign): The statement examined while apply
            type effects for AnnAssign statements.

    """
    target_name: StrOrNone = name_from_target(node=statement.target)
    if target_name is None:
        return
    if statement.value is not None:
        value_source: str = infer_expr_source(
            node=statement.value,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if should_replace_object_annotation(
            current=ann_source(node=statement.annotation),
            inferred=value_source,
        ):
            scope[target_name] = value_source
        else:
            scope[target_name] = ann_source(node=statement.annotation)
    else:
        scope[target_name] = ann_source(node=statement.annotation)


def _apply_for_effects(
    *,
    statement: For,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> ListStr:
    """Apply type effects for For statements and return discovered returns.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while apply type effects for
            For statements and return discovered returns.
        statement (For): The statement examined while apply type effects
            for For statements and return discovered returns.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    return_sources: ListStr = []
    iter_source: str = infer_expr_source(
        node=statement.iter,
        scope=scope,
        facts=facts,
        current_function=current_function,
    )
    bind_target_source(
        target=statement.target,
        source=element_type(source=iter_source),
        scope=scope,
    )
    for child in statement.body:
        return_sources.extend(
            apply_statement_scope_effects(
                statement=child,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return return_sources


def _apply_if_effects(
    *,
    statement: If,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> ListStr:
    """Apply type effects for If statements and return discovered returns.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while apply type effects for
            If statements and return discovered returns.
        statement (If): The statement examined while apply type effects for If
            statements and return discovered returns.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    branch_sources: ListStr = []
    for branch in (statement.body, statement.orelse):
        branch_scope: DictStr = dict(scope)
        for child in branch:
            branch_sources.extend(
                apply_statement_scope_effects(
                    statement=child,
                    scope=branch_scope,
                    facts=facts,
                    current_function=current_function,
                ),
            )
        for name, source in branch_scope.items():
            if name in scope and scope[name] != source:
                scope[name] = merge_type_sources(scope[name], source)
            elif name not in scope:
                scope[name] = source
    return branch_sources


def apply_statement_scope_effects(
    *,
    statement: stmt,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> ListStr:
    """Apply statement-local type effects and return discovered returns.

    The interpreter is intentionally conservative but recursive enough to see
    common evidence inside loops and branches, for example ``result.append``
    inside nested loops.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        scope (DictStr): The scope examined while apply statement-local
            type effects and return discovered returns.
        statement (stmt): The statement examined while apply statement-local
            type effects and return discovered returns.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    return_sources: ListStr = []
    if isinstance(statement, Assign):
        _apply_assign_effects(
            statement=statement,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    elif isinstance(statement, AnnAssign):
        _apply_annassign_effects(
            statement=statement,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    elif isinstance(statement, For):
        return_sources.extend(
            _apply_for_effects(
                statement=statement,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    elif isinstance(statement, If):
        return_sources.extend(
            _apply_if_effects(
                statement=statement,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    elif isinstance(statement, Expr):
        apply_expression_side_effects(
            node=statement.value,
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
    elif isinstance(statement, Return) and statement.value is not None:
        return_sources.append(
            infer_expr_source(
                node=statement.value,
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
    return return_sources


def _collect_yield_sources(
    *,
    function: FunctionDef | AsyncFunctionDef,
    scope: DictStr,
    facts: GraphFacts,
    fact: FunctionFact,
) -> ListStr:
    """Collect yield sources from a function.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            collect yield sources from a function.
        scope (DictStr): The scope examined while collect yield sources from a
            function.

    Returns:
        ListStr: list[str] produced by this operation.

    """
    yield_sources: ListStr = []
    for node in walk_without_nested_scopes(node=function):
        if isinstance(node, YieldFrom):
            yield_sources.append(
                element_type(
                    source=infer_expr_source(
                        node=node.value,
                        scope=scope,
                        facts=facts,
                        current_function=fact,
                    ),
                ),
            )
        if isinstance(node, Yield) and node.value is not None:
            yield_sources.append(
                infer_expr_source(
                    node=node.value,
                    scope=scope,
                    facts=facts,
                    current_function=fact,
                ),
            )
    return yield_sources


def _infer_contextmanager_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    scope: DictStr,
    facts: GraphFacts,
    fact: FunctionFact,
) -> StrOrNone:
    """Infer return type for contextmanager functions.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer return
            type for contextmanager functions.
        scope (DictStr): The scope examined while infer return
            type for contextmanager functions.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    local: DictStr = dict(scope)
    for statement in function.body:
        if isinstance(statement, Assign):
            value_type: str = infer_expr_source(
                node=statement.value,
                scope=local,
                facts=facts,
                current_function=fact,
            )
            for target in statement.targets:
                bind_target_source(
                    target=target,
                    source=value_type,
                    scope=local,
                )
    yield_sources: ListStr = _collect_yield_sources(
        function=function,
        scope=local,
        facts=facts,
        fact=fact,
    )
    if yield_sources:
        return f"Generator[{merge_type_sources(*yield_sources)}, None, None]"
    return None


def _infer_nested_function_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
) -> StrOrNone:
    """Infer return type when function returns a nested function.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer return type
            when function returns a nested function.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    nested: FunctionDef | AsyncFunctionDef | None = returned_nested_function(
        function=function,
        fact=fact,
    )
    if nested is None:
        return None
    params: ListStr = [
        ann_source(node=param.annotation)
        for param in explicit_parameters(node=nested)
    ]
    ret_source: str = ann_source(node=nested.returns)
    if isinstance(nested, AsyncFunctionDef):
        ret_source = f"Awaitable[{ret_source}]"
    return f"Callable[[{', '.join(params)}], {ret_source}]"


def _infer_local_class_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
) -> StrOrNone:
    """Infer return type when function returns local class instances.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer return type
            when function returns local class instances.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    for statement in function.body:
        if (
            isinstance(statement, Return)
            and isinstance(statement.value, Name)
            and (statement.value.id in fact.local_classes)
        ):
            return "type[object]"
        if (
            isinstance(statement, Return)
            and isinstance(statement.value, Call)
            and (call_name(node=statement.value.func) in fact.local_classes)
        ):
            return "object"
    return None


def infer_function_return_annotation(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
    facts: GraphFacts,
    scope: DictStr,
) -> StrOrNone:
    """Infer a better return annotation from graph structure.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer a better
            return annotation from graph structure.
        scope (DictStr): The scope examined while infer a better
            return annotation from graph structure.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    special_result: StrOrNone = _infer_special_return(
        function=function,
        fact=fact,
        facts=facts,
        scope=scope,
    )
    if special_result is not None:
        return special_result
    return _infer_return_from_body(
        function=function,
        fact=fact,
        facts=facts,
        scope=scope,
    )


def _infer_special_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
    facts: GraphFacts,
    scope: DictStr,
) -> StrOrNone:
    """Infer return type from special cases.

    Handles contextmanager, nested function, and local class returns.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer return type from special cases.
        scope (DictStr): The scope examined while infer return type from
            special cases.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    if has_decorator(node=function, name="contextmanager"):
        context_result: StrOrNone = _infer_contextmanager_return(
            function=function,
            scope=scope,
            facts=facts,
            fact=fact,
        )
        if context_result is not None:
            return context_result
    nested_result: StrOrNone = _infer_nested_function_return(
        function=function,
        fact=fact,
    )
    if nested_result is not None:
        return nested_result
    local_class_result: StrOrNone = _infer_local_class_return(
        function=function,
        fact=fact,
    )
    if local_class_result is not None:
        return local_class_result
    yield_values: ListStr = _collect_yield_sources(
        function=function,
        scope=scope,
        facts=facts,
        fact=fact,
    )
    if yield_values:
        return f"Generator[{merge_type_sources(*yield_values)}, None, None]"
    return None


def _infer_return_from_body(
    *,
    function: FunctionDef | AsyncFunctionDef,
    fact: FunctionFact,
    facts: GraphFacts,
    scope: DictStr,
) -> StrOrNone:
    """Infer return type from function body.

    Args:
        fact (FunctionFact): Fact supplied as FunctionFact for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            infer return type from function body.
        scope (DictStr): The scope examined while infer return type from
            function body.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    return_sources: ListStr = []
    local_scope: DictStr = dict(scope)
    for statement in function.body:
        return_sources.extend(
            apply_statement_scope_effects(
                statement=statement,
                scope=local_scope,
                facts=facts,
                current_function=fact,
            ),
        )
    if return_sources:
        non_none_sources: ListStr = [
            s for s in return_sources if norm(source=s) != "None"
        ]
        if non_none_sources:
            return merge_type_sources(*non_none_sources)
        return merge_type_sources(*return_sources)
    return None


def apply_expression_side_effects(
    *,
    node: AST,
    scope: DictStr,
    facts: GraphFacts,
    current_function: FunctionFact | None,
) -> None:
    """Apply generic expression side effects to the local type scope.

    This keeps the lightweight graph interpreter aware of collection-mutating
    method calls such as ``result.append(value)``. The update is deliberately
    structural and name-agnostic: any local variable with a list-like type is
    narrowed by the element passed to ``append`` or ``extend``.

    Args:
        current_function (FunctionFact | None): Current function supplied as
            FunctionFact | None for this operation.
        facts (GraphFacts): Facts supplied as GraphFacts for this operation.
        node (AST): The node examined while apply generic expression
            side effects to the local type scope.
        scope (DictStr): The scope examined while apply generic
            expression side effects to the local type scope.

    """
    if not isinstance(node, Call):
        return
    if not isinstance(node.func, Attribute):
        return
    if not isinstance(node.func.value, Name):
        return
    target_name: str = node.func.value.id
    current_source: str = scope.get(target_name, "object")
    current_norm: str = norm(source=current_source)
    if node.func.attr == "append" and node.args:
        value_source: str = infer_expr_source(
            node=node.args[0],
            scope=scope,
            facts=facts,
            current_function=current_function,
        )
        if current_norm.startswith("list["):
            merged: str = merge_type_sources(
                element_type(source=current_source),
                value_source,
            )
            scope[target_name] = f"list[{merged}]"
        elif current_source in Constants.object_names:
            scope[target_name] = f"list[{value_source}]"
    elif node.func.attr == "extend" and node.args:
        value_source = element_type(
            source=infer_expr_source(
                node=node.args[0],
                scope=scope,
                facts=facts,
                current_function=current_function,
            ),
        )
        if current_norm.startswith("list["):
            merged = merge_type_sources(
                element_type(source=current_source),
                value_source,
            )
            scope[target_name] = f"list[{merged}]"
        elif current_source in Constants.object_names:
            scope[target_name] = f"list[{value_source}]"


def has_decorator(node: FunctionDef | AsyncFunctionDef, name: str) -> bool:
    """Return whether a function has a decorator by simple name.

    Args:
        name (str): Identifier of the name being resolved.
        node (FunctionDef | AsyncFunctionDef): The node examined while return
            whether a
            function has a decorator by simple name.

    Returns:
        bool: Whether the requested condition holds.

    """
    return any(
        call_name(
            node=decorator
            if not isinstance(decorator, Call)
            else decorator.func,
        )
        == name
        for decorator in node.decorator_list
    )


def ensure_override(node: FunctionDef) -> None:
    """Add override decorator if missing.

    Args:
        node (FunctionDef): The node examined while add override decorator if
            missing.

    """
    if any(
        call_name(node=dec if not isinstance(dec, Call) else dec.func)
        == "override"
        for dec in node.decorator_list
    ):
        return
    node.decorator_list.insert(0, Name(id="override", ctx=Load()))


def ensure_assignment(node: Module, name: str, expression_source: str) -> None:
    """Ensure a top-level type variable assignment exists.

    Args:
        expression_source (str): Expression source supplied as str for this
            operation.
        name (str): Identifier of the name being resolved.
        node (Module): The node examined while ensure a top-level type variable
            assignment exists.

    """
    for statement in node.body:
        if isinstance(statement, Assign) and any(
            isinstance(target, Name) and target.id == name
            for target in statement.targets
        ):
            return
    insertion_index: int = first_body_index_after_imports(node=node)
    assignment: Assign = Assign(
        targets=[Name(id=name, ctx=Store())],
        value=parse_ann(source=expression_source),
    )
    node.body.insert(insertion_index, assignment)


def first_body_index_after_imports(node: Module) -> int:
    """Return insertion point after module docstring/imports.

    Args:
        node (Module): The node examined while return insertion
            point after module docstring/imports.

    Returns:
        int: int produced by this operation.

    """
    index: int = 0
    if (
        node.body
        and isinstance(node.body[0], Expr)
        and isinstance(node.body[0].value, Constant)
        and isinstance(node.body[0].value.value, str)
    ):
        index = 1
    while index < len(node.body) and isinstance(
        node.body[index],
        (Import, ImportFrom),
    ):
        index += 1
    return index


def collect_loaded_names(node: AST) -> SetStr:
    """Collect loaded names.

    Args:
        node (AST): The node examined while collect loaded names.

    Returns:
        SetStr: set[str] produced by this operation.

    """
    names: SetStr = set()
    for sub in nodes_of_type(root=node, types=(Name,)):
        if isinstance(sub.ctx, Load):
            names.add(sub.id)
    return names


def uses_name(node: AST, name: str) -> bool:
    """Return whether a name is loaded.

    Args:
        name (str): Identifier of the name being resolved.
        node (AST): The node examined while return whether a name is loaded.

    Returns:
        bool: Whether the requested condition holds.

    """
    return name in collect_loaded_names(node=node)


def rewrite_imports(
    *,
    node: Module,
    typing_names: SetStr,
    _abc_names: SetStr,
) -> None:
    """Rewrite typing/abc imports to exactly the loaded names.

    Names provided by ``collections.abc`` are emitted from that module so the
    output does not trigger ``reportDeprecated`` for the runtime generics that
    moved out of ``typing`` in Python 3.9.

    Args:
        _abc_names (SetStr): Abc names supplied as set[str] for this operation.
        node (Module): The node examined while rewrite typing/abc
            imports to exactly the loaded names.
        typing_names (SetStr): Typing names supplied as set[str] for this
            operation.

    """
    import_blocks: list[stmt] = []
    if typing_names:
        import_blocks.append(
            ImportFrom(
                module="typing",
                names=[alias(name=name) for name in sorted(typing_names)],
                level=0,
            ),
        )
    if _abc_names:
        import_blocks.append(
            ImportFrom(
                module="collections.abc",
                names=[alias(name=name) for name in sorted(_abc_names)],
                level=0,
            ),
        )
    new_body: list[stmt] = []
    inserted: bool = False
    for statement in node.body:
        if isinstance(statement, ImportFrom) and statement.module in {
            "typing",
            "collections.abc",
        }:
            continue
        new_body.append(statement)
        if (
            not inserted
            and isinstance(statement, ImportFrom)
            and (statement.module == "__future__")
        ):
            new_body.extend(import_blocks)
            inserted = True
    if not inserted and import_blocks:
        index: int = 0
        if (
            new_body
            and isinstance(new_body[0], Expr)
            and isinstance(new_body[0].value, Constant)
            and isinstance(new_body[0].value.value, str)
        ):
            index = 1
        new_body[index:index] = import_blocks
    node.body = new_body


def existing_local_annotations(
    node: FunctionDef | AsyncFunctionDef,
) -> SetStr:
    """Collect already annotated local names in a function body.

    Args:
        node (FunctionDef | AsyncFunctionDef): The node examined while collect
            already
            annotated local names in a function body.

    Returns:
        SetStr: set[str] produced by this operation.

    """
    names: SetStr = set()
    for sub in nodes_of_type(root=node, types=(AnnAssign,)):
        name: StrOrNone = name_from_target(node=sub.target)
        if name is not None:
            names.add(name)
    return names


def should_annotate_local_name(name: str) -> bool:
    """Return whether a local should receive an inferred annotation.

    Args:
        name (str): Identifier of the name being resolved.

    Returns:
        bool: Whether the requested condition holds.

    """
    return not name.startswith("_")


def contains_unavailable_local_type(source: str) -> bool:
    """Avoid annotations that mention local-only class names directly.

    Args:
        source (str): The source examined while avoid annotations that mention
            local-only class names directly.

    Returns:
        bool: Whether the requested condition holds.

    """
    _: str = source
    return False


def class_inherits(node: ClassDef, base: str) -> bool:
    """Return whether a class directly names a base.

    Args:
        base (str): Base supplied as str for this operation.
        node (ClassDef): The node examined while return
            whether a class directly names a base.

    Returns:
        bool: Whether the requested condition holds.

    """
    return any(base_name(node=item) == base for item in node.bases)


def normalize_annotation_unions(node: AST) -> None:
    """Normalize union annotation ordering across the graph.

    Args:
        node (AST): The node examined while normalize union annotation ordering
            across the graph.

    """
    for sub in nodes_of_type(
        root=node,
        types=(arg, AnnAssign, FunctionDef, AsyncFunctionDef),
    ):
        annotation: expr | None = None
        setter: StrOrNone = None
        if isinstance(sub, arg) and sub.annotation is not None:
            annotation = sub.annotation
            setter = "arg"
        elif (
            isinstance(sub, (FunctionDef, AsyncFunctionDef))
            and sub.returns is not None
        ):
            annotation = sub.returns
            setter = "returns"
        elif isinstance(sub, AnnAssign):
            annotation = sub.annotation
            setter = "annassign"
        if annotation is None or setter is None:
            continue
        source: str = ann_source(node=annotation)
        if "|" not in source:
            continue
        normalized: str = order_union_source(source=source)
        if normalized == source:
            continue
        if setter == "arg":
            cast(typ="arg", val=sub).annotation = parse_ann(source=normalized)
        elif setter == "returns":
            cast(
                typ="FunctionDef | AsyncFunctionDef",
                val=sub,
            ).returns = parse_ann(source=normalized)
        else:
            cast(typ="AnnAssign", val=sub).annotation = parse_ann(
                source=normalized,
            )


def find_method(node: ClassDef, name: str) -> FunctionDef | None:
    """Find a method by name.

    Args:
        name (str): Identifier of the name being resolved.
        node (ClassDef): The node examined while find a method by name.

    Returns:
        FunctionDef | None: FunctionDef | None produced by this operation.

    """
    for item in node.body:
        if isinstance(item, FunctionDef) and item.name == name:
            return item
    return None


def self_attr_assignment_param_map(function: FunctionDef) -> DictStr:
    """Map self.attr = parameter assignments inside a method.

    Args:
        function (FunctionDef): The function examined while map self.attr
            = parameter assignments inside a method.

    Returns:
        DictStr: dict[str, str] produced by this operation.

    """
    mapping: DictStr = {}
    for statement in nodes_of_type(root=function, types=(Assign,)):
        if not isinstance(statement.value, Name):
            continue
        for target in statement.targets:
            if (
                isinstance(target, Attribute)
                and isinstance(target.value, Name)
                and (target.value.id == "self")
            ):
                mapping[target.attr] = statement.value.id
    return mapping


def self_attr_return_attr_name(function: FunctionDef) -> StrOrNone:
    """Extract the attribute name from a property getter's return statement.

    For a property getter like:
        @property
        def base_property(self) -> object:
            return self.x

    This returns 'x'.

    Args:
        function (FunctionDef): The function examined while extract the
            attribute
            name from a property getter's return statement.

    Returns:
        StrOrNone: str | None produced by this operation.

    """
    for statement in nodes_of_type(root=function, types=(Return,)):
        if (
            isinstance(statement.value, Attribute)
            and isinstance(statement.value.value, Name)
            and (statement.value.value.id == "self")
        ):
            return statement.value.attr
    return None


def ensure_class_attr_annotation(
    *,
    class_node: ClassDef,
    name: str,
    source: str,
    replace_only_object: bool,
) -> None:
    """Ensure or refine a class attribute annotation.

    Args:
        class_node (ClassDef): Class node supplied as ClassDef for this
            operation.
        name (str): Identifier of the name being resolved.
        replace_only_object (bool): Replace only object supplied as bool for
            this operation.
        source (str): The source examined while ensure or
            refine a class attribute annotation.

    """
    for index, item in enumerate(iterable=class_node.body):
        if (
            isinstance(item, AnnAssign)
            and name_from_target(node=item.target) == name
        ):
            current: str = ann_source(node=item.annotation)
            if replace_only_object and (
                not should_replace_object_annotation(
                    current=current,
                    inferred=source,
                )
            ):
                return
            if item.value is not None:
                value_source: str = infer_expr_source(
                    node=item.value,
                    scope={},
                    facts=GraphFacts(),
                    current_function=None,
                )
                if value_source and (
                    not _are_types_compatible(type1=value_source, type2=source)
                ):
                    return
            item.annotation = parse_ann(source=source)
            return
        if isinstance(item, Assign):
            for target in item.targets:
                if isinstance(target, Name) and target.id == name:
                    class_node.body[index] = AnnAssign(
                        target=target,
                        annotation=parse_ann(source=source),
                        value=item.value,
                        simple=1,
                    )
                    return
