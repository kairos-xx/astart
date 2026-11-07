"""Execute Astart's graph conversion and merge safe conclusions into ASTs.

Astart's complete conversion pipeline runs on a current source snapshot.
Its generated *code* is never blindly substituted for the caller's source:
only annotations with matching semantic declaration paths, valid names and
unambiguous sites become proposals. Proposals are immutable and carry the
original mutable AST node to which evidence may be attached. No analyzed code
is imported or executed.
"""

from __future__ import annotations

import builtins
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    Subscript,
    alias,
    arg,
    copy_location,
    fix_missing_locations,
    iter_fields,
    parse,
    stmt,
    unparse,
    walk,
)
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, final

from astart._graph.conversion.engine import GraphOnlyConverter
from astart.node_attributes import list_items, render_source
from astart.semantic.type_expressions import TypeExpressionCodec
from astart.semantic.type_shapes import TypeShape, type_shape

if TYPE_CHECKING:
    from ast import arguments as ast_arguments
    from ast import expr
    from pathlib import Path

    from astart._graph.conversion.engine import ConversionResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        typing_names: Grouped module constant.

    """

    typing_names: Final[frozenset[str]] = frozenset(
        (
            "Any",
            "Never",
            "Self",
            "Literal",
            "LiteralString",
            "Annotated",
            "Optional",
            "Union",
            "Callable",
            "ClassVar",
            "Final",
            "Required",
            "NotRequired",
            "TypeGuard",
            "TypeIs",
            "TypeVar",
            "ParamSpec",
            "TypeVarTuple",
            "Unpack",
            "Concatenate",
            "Protocol",
            "TypedDict",
            "TypeAlias",
            "TypeAliasType",
            "ReadOnly",
            "NoReturn",
            "Type",
            "Generic",
            "Iterable",
            "Iterator",
            "Mapping",
            "Sequence",
            "MutableSequence",
            "MutableMapping",
            "Awaitable",
            "Coroutine",
            "Generator",
            "AsyncGenerator",
            "AsyncIterator",
            "AsyncIterable",
            "Collection",
            "Hashable",
            "Sized",
            "SupportsInt",
            "SupportsFloat",
            "SupportsIndex",
            "SupportsBytes",
            "IO",
            "TextIO",
            "BinaryIO",
            "Pattern",
            "Match",
            "ParamSpecArgs",
            "ParamSpecKwargs",
            "NewType",
            "override",
        ),
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GraphAnnotation:
    """One verified proposal bound to a stable original syntax node.

    Attributes:
        annotation: Annotation retained as TypeShape by this instance.
        role: Role retained as str by this instance.
        site: Site retained as tuple[str, ...] by this instance.
        source: Original source text retained for parsing and reconstruction.
        target: AST target associated with this record.

    """

    target: AST
    annotation: TypeShape
    source: str
    site: tuple[str, ...]
    role: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class GraphConversion:
    """Full Astart conversion output and selectively reusable evidence.

    Attributes:
        converted_source: Converted source retained as str by this instance.
        proposals: Proposals retained as tuple[GraphAnnotation, ...] by this
            instance.
        skipped: Skipped retained as tuple[str, ...] by this instance.
        stages: Stages retained as tuple[str, ...] by this instance.
        warnings: Warnings retained as tuple[str, ...] by this instance.

    """

    proposals: tuple[GraphAnnotation, ...]
    skipped: tuple[str, ...]
    converted_source: str
    stages: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def proposal_count(self) -> int:
        """Count annotations that have a safe target in the original AST.

        Returns:
            int produced by this operation.

        """
        return len(self.proposals)


def declaration_sites(*, module: Module) -> dict[tuple[str, ...], AST]:
    """Index declarations by scope and occurrence, not line number.

    Args:
        module: The module examined while index declarations by scope and
            occurrence, not line number.

    Returns:
        dict[tuple[str, ...], AST] produced by this operation.

    """
    result: dict[tuple[str, ...], AST] = {}
    pending: list[tuple[tuple[str, ...], list[AST]]] = [
        ((), list(module.body)),
    ]
    while pending:
        prefix, suite = pending.pop()
        occurrences: dict[tuple[str, str], int] = {}
        for statement_index, statement in enumerate(iterable=suite):
            if isinstance(
                statement,
                (FunctionDef, AsyncFunctionDef, ClassDef),
            ):
                category: str = (
                    "class" if isinstance(statement, ClassDef) else "function"
                )
                key: tuple[str, str] = (category, statement.name)
                occurrence: int = occurrences.get(key, 0)
                occurrences[key] = occurrence + 1
                site: tuple[str, ...] = (
                    *prefix,
                    (f"{category}:{statement.name}:{occurrence}"),
                )
                result[site] = statement
                pending.append((site, list(statement.body)))
            elif isinstance(statement, AnnAssign) and isinstance(
                statement.target,
                Name,
            ):
                key = ("variable", statement.target.id)
                occurrence = occurrences.get(key, 0)
                occurrences[key] = occurrence + 1
                result[
                    *prefix,
                    (f"variable:{statement.target.id}:{occurrence}"),
                ] = statement
            elif (
                isinstance(statement, Assign)
                and len(statement.targets) == 1
                and isinstance(statement.targets[0], Name)
            ):
                key = ("variable", statement.targets[0].id)
                occurrence = occurrences.get(key, 0)
                occurrences[key] = occurrence + 1
                result[
                    *prefix,
                    (f"variable:{statement.targets[0].id}:{occurrence}"),
                ] = statement
            elif not isinstance(
                statement,
                (FunctionDef, AsyncFunctionDef, ClassDef),
            ):
                for field, contents in iter_fields(node=statement):
                    field_items: list[object] = list_items(value=contents)
                    if any(isinstance(item, stmt) for item in field_items):
                        pending.append(
                            (
                                (
                                    *prefix,
                                    (
                                        f"branch:"
                                        f"{type(statement).__name__}"
                                        f":"
                                        f"{statement_index}"
                                        f":"
                                        f"{field}"
                                    ),
                                ),
                                [
                                    item
                                    for item in field_items
                                    if isinstance(item, stmt)
                                ],
                            ),
                        )
    return result


def available_type_names(*, root: Module) -> frozenset[str]:
    """Collect names available to unquoted annotations in the source.

    Args:
        root: Filesystem path identifying the root.

    Returns:
        frozenset[str] produced by this operation.

    """
    available: set[str] = set(dir(builtins))
    available.update(Constants.typing_names)
    for node in walk(node=root):
        if isinstance(node, Import):
            available.update(
                item.asname or item.name.split(sep=".")[0]
                for item in node.names
            )
        elif isinstance(node, ImportFrom):
            available.update(item.asname or item.name for item in node.names)
        elif isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            available.add(node.name)
        elif isinstance(node, (Assign, AnnAssign)):
            targets: list[expr] | tuple[expr, ...] = (
                node.targets if isinstance(node, Assign) else (node.target,)
            )
            available.update(
                target.id for target in targets if isinstance(target, Name)
            )
    return frozenset(available)


def annotation_shape(
    *,
    node: AST,
    available: frozenset[str],
) -> TypeShape | None:
    """Reject converter-generated names that would be undefined at runtime.

    Args:
        available: Available supplied as frozenset[str] for this operation.
        node: The node examined while reject converter-generated names that
            would be undefined at runtime.

    Returns:
        TypeShape | None produced by this operation.

    """
    if any(
        item.id not in available
        for item in walk(node=node)
        if isinstance(item, Name)
    ):
        return None
    shape: TypeShape = type_shape(
        expression=TypeExpressionCodec.from_ast(node=node),
    )
    if shape.name in ("object", "Any", "typing.Any", "Unknown"):
        return None
    return shape


def _all_arguments(*, arguments: ast_arguments) -> tuple[arg, ...]:
    """Every parameter of a signature, including ``*args`` and ``**kwargs``.

    Args:
        arguments: Collection of arguments supplied for this operation.

    Returns:
        tuple[arg, ...] produced by this operation.

    """
    variadic: tuple[arg, ...] = tuple(
        item
        for item in (arguments.vararg, arguments.kwarg)
        if item is not None
    )
    return (
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        *variadic,
    )


def _function_proposals(
    *,
    site: tuple[str, ...],
    target: FunctionDef | AsyncFunctionDef,
    output: FunctionDef | AsyncFunctionDef,
    available: frozenset[str],
    skipped: list[str],
) -> list[GraphAnnotation]:
    """Propose missing parameter and return annotations of one function.

    Args:
        available: Available supplied as frozenset[str] for this operation.
        output: Output supplied as FunctionDef | AsyncFunctionDef for this
            operation.
        site: Site supplied as tuple[str, ...] for this operation.
        skipped: Skipped supplied as list[str] for this operation.
        target: The target examined while propose missing parameter and return
            annotations of one function.

    Returns:
        list[GraphAnnotation] produced by this operation.

    """
    proposals: list[GraphAnnotation] = []
    output_parameters: dict[str, arg] = {
        item.arg: item for item in _all_arguments(arguments=output.args)
    }
    for parameter in _all_arguments(arguments=target.args):
        external: arg | None = output_parameters.get(parameter.arg)
        if (
            external is None
            or external.annotation is None
            or parameter.annotation is not None
        ):
            continue
        inferred: TypeShape | None = annotation_shape(
            node=external.annotation,
            available=available,
        )
        if inferred is None:
            skipped.append(
                f"{'.'.join(site)}:{parameter.arg}:undefined-or-imprecise",
            )
            continue
        proposals.append(
            GraphAnnotation(
                target=parameter,
                annotation=inferred,
                source=unparse(ast_obj=external.annotation),
                site=(*site, (f"parameter:{parameter.arg}")),
                role="parameter",
            ),
        )
    if target.returns is None and output.returns is not None:
        returned: TypeShape | None = annotation_shape(
            node=output.returns,
            available=available,
        )
        if returned is None:
            skipped.append(f"{'.'.join(site)}:return:undefined-or-imprecise")
        else:
            proposals.append(
                GraphAnnotation(
                    target=target,
                    annotation=returned,
                    source=unparse(ast_obj=output.returns),
                    site=(*site, "return"),
                    role="return",
                ),
            )
    return proposals


def _variable_proposal(
    *,
    site: tuple[str, ...],
    target: Assign,
    output: AnnAssign,
    available: frozenset[str],
    skipped: list[str],
) -> GraphAnnotation | None:
    """Propose an annotation for a plain assignment, if it is precise.

    Args:
        available: Available supplied as frozenset[str] for this operation.
        output: Output supplied as AnnAssign for this operation.
        site: Site supplied as tuple[str, ...] for this operation.
        skipped: Skipped supplied as list[str] for this operation.
        target: The target examined while propose an annotation for a plain
            assignment, if it is precise.

    Returns:
        GraphAnnotation | None produced by this operation.

    """
    inferred: TypeShape | None = annotation_shape(
        node=output.annotation,
        available=available,
    )
    if inferred is None:
        skipped.append(f"{'.'.join(site)}:variable:undefined-or-imprecise")
        return None
    return GraphAnnotation(
        target=target,
        annotation=inferred,
        source=unparse(ast_obj=output.annotation),
        site=site,
        role="variable",
    )


def collect_graph_annotations(
    *,
    root: Module,
    stubs_path: Path,
    filename: str = "<memory>",
) -> GraphConversion:
    """Run Astart's complete conversion pipeline on the current AST.

    Only annotation deltas against declaration-matched AST nodes are
    accepted. Imports, expression changes, statement reorderings, and
    foreign declarations from converter output are never propagated as part
    of an annotation update.

    Raises:
        SyntaxError: The current AST cannot be serialized as valid Python.
        OSError: The explicitly selected source/stubs cannot be read.
        RuntimeError: A Astart conversion stage failed.



    Args:
        filename: Filename supplied as str for this operation.
        root: Filesystem path identifying the root.
        stubs_path: Filesystem path identifying the stubs.

    Returns:
        GraphConversion produced by this operation.

    """
    current_source: str = render_source(
        tree=root,
        on_format_conflict="fallback",
    )
    parse(source=current_source)
    conversion: ConversionResult = GraphOnlyConverter.create(
        stubs_path=stubs_path,
    ).convert_text(source=current_source, filename=filename)
    original: dict[tuple[str, ...], AST] = declaration_sites(module=root)
    converted: dict[tuple[str, ...], AST] = declaration_sites(
        module=parse(source=conversion.output_source),
    )
    available: frozenset[str] = available_type_names(root=root)
    proposals: list[GraphAnnotation] = []
    skipped: list[str] = []
    for site, output in converted.items():
        target: AST | None = original.get(site)
        if isinstance(output, (FunctionDef, AsyncFunctionDef)) and isinstance(
            target,
            (FunctionDef, AsyncFunctionDef),
        ):
            proposals.extend(
                _function_proposals(
                    site=site,
                    target=target,
                    output=output,
                    available=available,
                    skipped=skipped,
                ),
            )
        elif isinstance(output, AnnAssign) and isinstance(target, Assign):
            proposal: GraphAnnotation | None = _variable_proposal(
                site=site,
                target=target,
                output=output,
                available=available,
                skipped=skipped,
            )
            if proposal is not None:
                proposals.append(proposal)
    return GraphConversion(
        proposals=tuple(proposals),
        skipped=tuple(skipped),
        converted_source=conversion.output_source,
        stages=conversion.stage_names,
        warnings=conversion.inference.warnings,
    )


def _introduce_typing_imports(
    *,
    root: Module,
    proposals: tuple[GraphAnnotation, ...],
) -> None:
    """Import only required typing names absent from the original module.

    Insert after a module docstring and all future imports. No synthesized
    Astart helper code or unnecessary converter imports are copied.


    Args:
        proposals: Proposals supplied as tuple[GraphAnnotation, ...] for this
            operation.
        root: Filesystem path identifying the root.

    """
    available: set[str] = set(dir(builtins))
    for statement in root.body:
        if isinstance(statement, Import):
            available.update(
                item.asname or item.name.split(sep=".")[0]
                for item in statement.names
            )
        elif isinstance(statement, ImportFrom):
            available.update(
                item.asname or item.name for item in statement.names
            )
        elif isinstance(statement, (FunctionDef, AsyncFunctionDef, ClassDef)):
            available.add(statement.name)
    necessary: set[str] = set()
    for proposal in proposals:
        annotation: expr = parse(source=proposal.source, mode="eval").body
        necessary.update(
            child.id
            for child in walk(node=annotation)
            if isinstance(child, Name)
            and child.id in Constants.typing_names
            and (child.id not in available)
        )
    if not necessary:
        return
    position: int = 0
    if (
        root.body
        and isinstance(root.body[0], Expr)
        and isinstance(root.body[0].value, Constant)
        and isinstance(root.body[0].value.value, str)
    ):
        position = 1
    while position < len(root.body):
        candidate: stmt = root.body[position]
        if not (
            isinstance(candidate, ImportFrom)
            and candidate.module == "__future__"
        ):
            break
        position += 1
    root.body.insert(
        position,
        ImportFrom(
            module="typing",
            names=[
                alias(name=name, asname=None) for name in sorted(necessary)
            ],
            level=0,
        ),
    )


def _apply_signature_annotation(*, proposal: GraphAnnotation) -> bool:
    """Attach a parameter or return annotation when still missing.

    Args:
        proposal: Proposal supplied as GraphAnnotation for this operation.

    Returns:
        Whether the requested condition holds.

    """
    target: AST = proposal.target
    if (
        proposal.role == "parameter"
        and isinstance(target, arg)
        and (target.annotation is None)
    ):
        target.annotation = copy_location(
            new_node=parse(source=proposal.source, mode="eval").body,
            old_node=target,
        )
        return True
    if (
        proposal.role == "return"
        and isinstance(target, (FunctionDef, AsyncFunctionDef))
        and (target.returns is None)
    ):
        target.returns = copy_location(
            new_node=parse(source=proposal.source, mode="eval").body,
            old_node=target,
        )
        return True
    return False


def _apply_variable_annotations(
    *,
    root: Module,
    variables: dict[int, GraphAnnotation],
) -> int:
    """Turn matched plain assignments into annotated assignments.

    Args:
        root: Filesystem path identifying the root.
        variables: Variables supplied as dict[int, GraphAnnotation] for this
            operation.

    Returns:
        int produced by this operation.

    """
    applied: int = 0
    pending: list[list[stmt]] = [root.body]
    while pending:
        suite: list[stmt] = pending.pop()
        for index, statement in enumerate(iterable=suite):
            proposal: GraphAnnotation | None = variables.get(id(statement))
            if (
                proposal is not None
                and isinstance(statement, Assign)
                and (len(statement.targets) == 1)
                and isinstance(
                    (single := statement.targets[0]),
                    (Name, Attribute, Subscript),
                )
            ):
                replacement: AnnAssign = AnnAssign(
                    target=single,
                    annotation=parse(source=proposal.source, mode="eval").body,
                    value=statement.value,
                    simple=1,
                )
                suite[index] = copy_location(
                    new_node=replacement,
                    old_node=statement,
                )
                applied += 1
            if isinstance(
                statement,
                (ClassDef, FunctionDef, AsyncFunctionDef),
            ):
                pending.append(statement.body)
    return applied


def apply_graph_annotations(
    *,
    root: Module,
    integration: GraphConversion,
) -> int:
    """Apply only matched annotation proposals; keep other source.

    Args:
        integration: Integration supplied as GraphConversion for this
            operation.
        root: Filesystem path identifying the root.

    Returns:
        int produced by this operation.

    """
    _introduce_typing_imports(root=root, proposals=integration.proposals)
    applied: int = 0
    variables: dict[int, GraphAnnotation] = {}
    for proposal in integration.proposals:
        if proposal.role == "variable":
            variables[id(proposal.target)] = proposal
        elif _apply_signature_annotation(proposal=proposal):
            applied += 1
    if variables:
        applied += _apply_variable_annotations(root=root, variables=variables)
    if applied:
        fix_missing_locations(node=root)
    return applied
