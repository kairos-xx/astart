"""Concrete conversion pipeline stages."""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Attribute,
    FunctionDef,
    Module,
    Name,
    NodeTransformer,
    ParamSpec,
    Subscript,
    Tuple,
    TypeVar,
    expr,
    walk,
)
from dataclasses import dataclass
from io import StringIO
from tokenize import (
    NAME,
    NUMBER,
    OP,
    STRING,
    TokenError,
    TokenInfo,
    generate_tokens,
)
from typing import TYPE_CHECKING, Final, cast, final

from astart.graph.backend.engine import Parenthesized
from astart.graph.backend.finalizer import organize_protocols_and_typevars
from astart.graph.conversion.synthesis import (
    create_simple_paramspec,
    create_simple_typevar,
)
from astart.graph.graph.document import AstDocument
from astart.graph.graph.usage import UsageGraph, build_usage_graph
from astart.graph.inference.explanations import (
    InferenceExplanationBuilder,
    InferenceExplanationReport,
)
from astart.graph.inference.graph_refinements import GraphRefiner
from astart.graph.inference.post_refinements import refine_inferred_module
from astart.graph.inference.resolver import InferenceResolver, InferenceResult
from astart.graph.stubs.index import LazyStubIndex
from astart.source.node_attributes import read_attribute

type SetStr = set[str]
type TupleIntInt = tuple[int, int]

if TYPE_CHECKING:
    from astart.graph.conversion.context import ConversionContext
    from astart.graph.conversion.interfaces import ConversionBackend


def _character_column(*, line: str, byte_offset: int) -> int:
    """Convert an AST column (a UTF-8 byte offset) to a character index.

    ``ast`` reports columns in bytes while ``tokenize`` and string indexing use
    characters, so the two only agree on pure-ASCII text.

    Args:
        line (str): Source line.
        byte_offset (int): Column as reported by ``ast``.

    Returns:
        int: The index of the same position in ``line``.

    """
    return len(line.encode()[:byte_offset].decode(errors="ignore"))


class _ParenthesisMarker(NodeTransformer):
    """Wraps parenthesized expressions in Parenthesized nodes.

    Attributes:
        _STRUCTURAL_PREV_TYPES (frozenset[int]): TODO.
        _STRUCTURAL_PREV_OPS (frozenset[str]): TODO.

    """

    _STRUCTURAL_PREV_TYPES: frozenset[int] = frozenset({NAME, NUMBER, STRING})
    _STRUCTURAL_PREV_OPS: frozenset[str] = frozenset({")", "]", "}"})

    def __init__(self, source_lines: list[str]) -> None:
        """Initialize with source lines for token-based paren detection.

        Args:
            source_lines (list[str]): Source lines supplied as list[str] for
                this operation.

        """
        self.source_lines: list[str] = source_lines
        self.source: str = "\n".join(source_lines)
        self.token_map: dict[TupleIntInt, str] = self._build_token_map()

    def visit(self, node: AST) -> AST:
        """Visit a node and wrap in Parenthesized if original had parens.

        Args:
            node (AST): The node examined while visit a node and wrap in
                Parenthesized if original had parens.

        Returns:
            AST: AST produced by this operation.

        """
        if not isinstance(node, expr):
            return self.generic_visit(node=node)
        result: AST = self.generic_visit(node=node)
        start_pos: TupleIntInt | None = self._find_opening_paren_pos(
            node=node,
        )
        end_pos: TupleIntInt | None = self._find_closing_paren_pos(
            node=node,
        )
        if start_pos is not None and end_pos is not None:
            return Parenthesized(
                value=cast(typ="expr", val=result),
                start_pos=start_pos,
                end_pos=end_pos,
            )
        return result

    def _build_token_map(self) -> dict[TupleIntInt, str]:
        """Build a map of (line, col) -> '(' or ')' for expression parens only.

        Structural parens — those immediately following a NAME token or a
        closing bracket (function calls, class bases, decorators) — are
        excluded, along with their matching closing paren.

        Returns:
            dict[TupleIntInt, str]: dict[tuple[int, int], str] produced by this
                operation.

        """
        token_map: dict[TupleIntInt, str] = {}
        try:
            all_tokens: list[TokenInfo] = list(
                generate_tokens(
                    readline=StringIO(initial_value=self.source).readline,
                ),
            )
        except TokenError:
            return token_map
        structural_stack: list[TupleIntInt] = []
        for i, tok in enumerate(iterable=all_tokens):
            if tok.type != OP:
                continue
            pos: TupleIntInt = (tok.start[0], tok.start[1])
            if tok.string == "(":
                prev: TokenInfo | None = all_tokens[i - 1] if i > 0 else None
                is_structural: bool = prev is not None and (
                    prev.type in self._STRUCTURAL_PREV_TYPES
                    or (
                        prev.type == OP
                        and prev.string in self._STRUCTURAL_PREV_OPS
                    )
                )
                if is_structural:
                    structural_stack.append(pos)
                else:
                    token_map[pos] = "("
            elif tok.string == ")":
                if structural_stack:
                    structural_stack.pop()
                else:
                    token_map[pos] = ")"
        return token_map

    def _find_opening_paren_pos(self, *, node: AST) -> TupleIntInt | None:
        """Find '(' immediately before this node, skipping whitespace.

        Args:
            node (AST): The node examined while find '(' immediately
                before this node, skipping whitespace.

        Returns:
            TupleIntInt | None:
                tuple[int, int] | None produced by this operation.

        """
        lineno: int | None = read_attribute(node=node, name="lineno", kind=int)
        col_offset: int | None = read_attribute(
            node=node,
            name="col_offset",
            kind=int,
        )
        if lineno is None or col_offset is None:
            return None
        line: str = (
            self.source_lines[lineno - 1]
            if 0 <= lineno - 1 < len(self.source_lines)
            else ""
        )
        column: int = _character_column(line=line, byte_offset=col_offset)
        for i in range(column - 1, -1, -1):
            if line[i] in {" ", "\t"}:
                continue
            return (
                (lineno, i) if self.token_map.get((lineno, i)) == "(" else None
            )
        return None

    def _find_closing_paren_pos(self, *, node: AST) -> TupleIntInt | None:
        """Find ')' immediately after this node, skipping whitespace.

        Args:
            node (AST): The node examined while find ')' immediately
                after this node, skipping whitespace.

        Returns:
            TupleIntInt | None:
                tuple[int, int] | None produced by this operation.

        """
        if not hasattr(node, "end_lineno") or not hasattr(
            node,
            "end_col_offset",
        ):
            return None
        end_lineno: int | None = read_attribute(
            node=node,
            name="end_lineno",
            kind=int,
        )
        end_col_offset: int | None = read_attribute(
            node=node,
            name="end_col_offset",
            kind=int,
        )
        if end_lineno is None or end_col_offset is None:
            return None
        line: str = (
            self.source_lines[end_lineno - 1]
            if 0 <= end_lineno - 1 < len(self.source_lines)
            else ""
        )
        start: int = _character_column(line=line, byte_offset=end_col_offset)
        for i in range(start, len(line)):
            if line[i] in {" ", "\t"}:
                continue
            return (
                (end_lineno, i)
                if self.token_map.get((end_lineno, i)) == ")"
                else None
            )
        return None


@dataclass(frozen=True, slots=True)
class BuildInputDocumentStage:
    """Parse source once and build the input document graph.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "build-input-document"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach the input document graph to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        document: AstDocument = AstDocument.from_source(
            source=context.source,
            filename=context.options.filename,
        )
        marked_tree: Module = cast(
            typ="Module",
            val=_ParenthesisMarker(
                source_lines=context.source.splitlines(),
            ).visit(node=document.tree),
        )
        object.__setattr__(document, "tree", marked_tree)
        return context.with_input_document(document=document)


@dataclass(frozen=True, slots=True)
class BuildInputUsageGraphStage:
    """Build the usage graph for the untyped input document.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "build-input-usage-graph"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach input usage evidence to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        usage_graph: UsageGraph = build_usage_graph(
            document=context.require_input_document(),
        )
        return context.with_input_usage_graph(usage_graph=usage_graph)


@dataclass(frozen=True, slots=True)
class LoadStubIndexStage:
    """Load the lazy typeshed or stub index.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "load-stub-index"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach the lazy stub index to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        stub_index: LazyStubIndex = LazyStubIndex.from_path(
            path=context.options.stubs_path,
        )
        return context.with_stub_index(stub_index=stub_index)


@dataclass(frozen=True, slots=True)
class BackendConversionStage:
    """Run the source-to-source inference backend.

    Attributes:
        backend (ConversionBackend): Backend retained as ConversionBackend by
            this instance.
        name (str): Identifier used to refer to the name.

    """

    backend: ConversionBackend
    name: str = "backend-conversion"

    def run(self, *, context: ConversionContext) -> ConversionContext:
        """Attach converted AST module from the configured backend.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        module: Module = self.backend.convert(context=context)
        return context.with_backend_module(module=module)


@dataclass(frozen=True, slots=True)
class RefineBackendSourceStage:
    """Apply generic source-agnostic AST refinements to backend output.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "refine-backend-source"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Apply post-refinements to the backend module.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        module: Module = context.require_backend_module()
        refine_inferred_module(module=module)
        return context.with_backend_module(module=module)


@dataclass(frozen=True, slots=True)
class BuildOutputDocumentStage:
    """Parse converted source and build the output document graph.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "build-output-document"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach the output document graph to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        output_module: Module = context.require_backend_module()
        document: AstDocument = AstDocument.from_module(
            tree=output_module,
            source=context.source,
            filename=context.options.filename,
        )
        return context.with_output_document(document=document)


@dataclass(frozen=True, slots=True)
class ApplyGraphRefinementsStage:
    """Apply graph-based type refinements to the output document.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "apply-graph-refinements"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Apply graph-based refinements using the AST document API.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        document: AstDocument = context.require_output_document()
        refiner: GraphRefiner = GraphRefiner(document=document)
        refiner.refine()
        organize_protocols_and_typevars(module=document.tree)
        _add_missing_type_params(module=document.tree)
        return context.with_backend_module(module=document.tree)


@dataclass(frozen=True, slots=True)
class BuildOutputUsageGraphStage:
    """Build the usage graph for the inferred output document.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "build-output-usage-graph"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach output usage evidence to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        usage_graph: UsageGraph = build_usage_graph(
            document=context.require_output_document(),
        )
        return context.with_output_usage_graph(usage_graph=usage_graph)


@dataclass(frozen=True, slots=True)
class ResolveInferenceReportStage:
    """Resolve a structured inference report from output annotations.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "resolve-inference-report"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Attach structured hypotheses and annotation plans.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        resolver: InferenceResolver = InferenceResolver.create(
            document=context.require_output_document(),
            usage_graph=context.require_output_usage_graph(),
            stub_index=context.require_stub_index(),
        )
        inference: InferenceResult = resolver.resolve(
            baseline_document=context.require_input_document(),
        )
        return context.with_inference(inference=inference)


@dataclass(frozen=True, slots=True)
class BuildExplanationReportStage:
    """Build a human-readable explanation report.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "build-explanation-report"

    def run(self, *, context: ConversionContext) -> ConversionContext:
        """Attach an explanation report to the pipeline context.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        report: InferenceExplanationReport = InferenceExplanationBuilder.build(
            document=context.require_output_document(),
            usage_graph=context.require_output_usage_graph(),
            inference=context.require_inference(),
            stage_names=(*context.completed_stage_names, self.name),
            validation_messages=context.validation_messages,
        )
        return context.with_explanation(explanation=report)


@dataclass(frozen=True, slots=True)
class ValidateSyntaxStage:
    """Validate that the converted source parses as Python.

    Attributes:
        name (str): Identifier used to refer to the name.

    """

    name: str = "validate-syntax"

    @staticmethod
    def run(*, context: ConversionContext) -> ConversionContext:
        """Validate by unparsing the module and parsing it back.

        Args:
            context (ConversionContext): Context supplied as ConversionContext
                for this operation.

        Returns:
            ConversionContext: ConversionContext produced by this operation.

        """
        return context.with_validation_message(message="syntax: skipped")


@final
class Constants:
    """Group module-level constants.

    Attributes:
        paramspec_names (Final[frozenset[str]]): Grouped module constant.

    """

    paramspec_names: Final[frozenset[str]] = frozenset({"P", "Q", "R", "S"})


def _add_missing_type_params(*, module: Module) -> None:
    """Add type parameters to module-level functions using ParamSpec.

    Args:
        module (Module): The module examined while add type parameters
            to module-level functions using ParamSpec.

    """
    for node in module.body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            _add_type_params_to_function(function=node)


def _add_type_params_to_function(
    *,
    function: FunctionDef | AsyncFunctionDef,
) -> None:
    """Add type parameters to a function if needed.

    Args:
        function (FunctionDef | AsyncFunctionDef): The function examined while
            add type
            parameters to a function if needed.

    """
    paramspec_names: SetStr = set()
    typevar_names: SetStr = set()
    _collect_type_vars_from_params(
        function=function,
        paramspec_names=paramspec_names,
        typevar_names=typevar_names,
    )
    _collect_type_vars_from_return(
        function=function,
        paramspec_names=paramspec_names,
        typevar_names=typevar_names,
    )
    all_type_params: SetStr = paramspec_names | typevar_names
    if not all_type_params:
        return
    _add_type_params_to_function_impl(
        function=function,
        all_type_params=all_type_params,
        paramspec_names=paramspec_names,
    )


def _collect_type_vars_from_params(
    *,
    function: FunctionDef | AsyncFunctionDef,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Collect type variables from function parameters.

    Args:
        function (FunctionDef | AsyncFunctionDef): The function examined while
            collect type
            variables from function parameters.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    for param in function.args.args + function.args.posonlyargs:
        if param.annotation is not None:
            _analyze_type_vars(
                node=param.annotation,
                paramspec_names=paramspec_names,
                typevar_names=typevar_names,
            )
    if function.args.vararg and function.args.vararg.annotation is not None:
        _analyze_type_vars(
            node=function.args.vararg.annotation,
            paramspec_names=paramspec_names,
            typevar_names=typevar_names,
        )
    for param in function.args.kwonlyargs:
        if param.annotation is not None:
            _analyze_type_vars(
                node=param.annotation,
                paramspec_names=paramspec_names,
                typevar_names=typevar_names,
            )
    if function.args.kwarg and function.args.kwarg.annotation is not None:
        _analyze_type_vars(
            node=function.args.kwarg.annotation,
            paramspec_names=paramspec_names,
            typevar_names=typevar_names,
        )


def _collect_type_vars_from_return(
    *,
    function: FunctionDef | AsyncFunctionDef,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Collect type variables from return annotation.

    Args:
        function (FunctionDef | AsyncFunctionDef): The function examined while
            collect
            type variables from return annotation.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    if function.returns is not None:
        _analyze_type_vars(
            node=function.returns,
            paramspec_names=paramspec_names,
            typevar_names=typevar_names,
        )


def _add_type_params_to_function_impl(
    *,
    function: FunctionDef | AsyncFunctionDef,
    all_type_params: SetStr,
    paramspec_names: SetStr,
) -> None:
    """Add missing type parameters to function.

    Args:
        all_type_params (SetStr): All type params supplied as set[str] for this
            operation.
        function (FunctionDef | AsyncFunctionDef): The function examined while
            add
            missing type parameters to function.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.

    """
    existing_names: SetStr = set()
    for tp in function.type_params:
        if isinstance(tp, (TypeVar, ParamSpec)):
            existing_names.add(tp.name)
    for name in sorted(all_type_params):
        if name not in existing_names:
            if name in paramspec_names:
                function.type_params.append(create_simple_paramspec(name=name))
            else:
                function.type_params.append(create_simple_typevar(name=name))


def _handle_attribute_node(
    *,
    node: Attribute,
    paramspec_names: SetStr,
) -> None:
    """Handle Attribute nodes to detect ParamSpec usage.

    Args:
        node (Attribute): The node examined while handle Attribute
            nodes to detect ParamSpec usage.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.

    """
    if isinstance(node.value, Name) and node.attr in ("args", "kwargs"):
        paramspec_names.add(node.value.id)


def _handle_name_node(
    *,
    node: Name,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Handle Name nodes to detect TypeVar usage.

    Args:
        node (Name): The node examined while handle Name nodes to detect
            TypeVar usage.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    if (
        node.id not in paramspec_names
        and node.id.isupper()
        and (len(node.id) == 1)
    ):
        typevar_names.add(node.id)


def _handle_tuple_slice(
    *,
    slice_node: Tuple,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Handle Tuple slices in subscripts.

    Args:
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        slice_node (Tuple): Slice node supplied as Tuple for this operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    for i, elt in enumerate(iterable=slice_node.elts):
        if isinstance(elt, Name):
            if i == 0 and elt.id in Constants.paramspec_names:
                paramspec_names.add(elt.id)
            elif elt.id.isupper() and len(elt.id) == 1:
                typevar_names.add(elt.id)


def _handle_subscript_node(
    *,
    node: Subscript,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Handle Subscript nodes to extract type variables.

    Args:
        node (Subscript): The node examined while handle Subscript
            nodes to extract type variables.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    if isinstance(node.slice, Name):
        if node.slice.id.isupper() and len(node.slice.id) == 1:
            typevar_names.add(node.slice.id)
    elif isinstance(node.slice, Tuple):
        _handle_tuple_slice(
            slice_node=node.slice,
            paramspec_names=paramspec_names,
            typevar_names=typevar_names,
        )


def _analyze_type_vars(
    *,
    node: AST,
    paramspec_names: SetStr,
    typevar_names: SetStr,
) -> None:
    """Analyze type variable usage in an annotation node.

    Detects whether a name is used as ParamSpec (P.args, P.kwargs)
    or as TypeVar (direct type usage).

    Args:
        node (AST): The node examined while analyze type variable usage in an
            annotation node.
        paramspec_names (SetStr): Paramspec names supplied as set[str] for this
            operation.
        typevar_names (SetStr): Typevar names supplied as set[str] for this
            operation.

    """
    for child in walk(node=node):
        if isinstance(child, Attribute):
            _handle_attribute_node(node=child, paramspec_names=paramspec_names)
        elif isinstance(child, Name):
            _handle_name_node(
                node=child,
                paramspec_names=paramspec_names,
                typevar_names=typevar_names,
            )
        elif isinstance(child, Subscript):
            _handle_subscript_node(
                node=child,
                paramspec_names=paramspec_names,
                typevar_names=typevar_names,
            )
