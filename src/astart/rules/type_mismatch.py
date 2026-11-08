"""M8-06 detectors: return-type mismatches and incompatible defaults.

``find_return_mismatches`` flags ``return`` expressions whose inferred
type is provably incompatible with the declared return annotation.
``find_incompatible_defaults`` flags parameter defaults whose inferred
type is provably incompatible with the parameter annotation.

Both refuse whenever inference is indeterminate — only a definitive
``compatible is False`` verdict from :func:`subtype` produces a
candidate.  Standalone detectors; catalog wiring is deferred (M8-22).
"""

from __future__ import annotations

from ast import (
    AST,
    AsyncFunctionDef,
    Constant,
    FunctionDef,
    Lambda,
    Return,
    Yield,
    YieldFrom,
    arg,
    arguments,
    expr,
    iter_child_nodes,
)
from typing import TYPE_CHECKING

from astart.rules.procedural import Candidate, span_of
from astart.semantic.type_expressions import TypeExpressionCodec
from astart.semantic.type_inference import TypeShape, type_shape
from astart.semantic.type_shapes import atomic
from astart.semantic.typing_relations import subtype

if TYPE_CHECKING:
    from types import EllipsisType

    from astart.ast import CommentedModule
    from astart.semantic.type_expressions import TypeExpression
    from astart.semantic.typing_relations import Compatibility

_SCOPE_NODES = (FunctionDef, AsyncFunctionDef, Lambda)


def _declared_shape(*, annotation: expr | None) -> TypeShape | None:
    """Convert an annotation expression to a :class:`TypeShape`.

    Args:
        annotation: Annotation AST, or ``None``.

    Returns:
        The shape, or ``None`` when absent or unconvertible.

    """
    if annotation is None:
        return None
    try:
        expression: TypeExpression = TypeExpressionCodec.from_ast(
            node=annotation,
        )
        return type_shape(expression=expression)
    except (ValueError, TypeError):
        return None


def _definitely_incompatible(
    *,
    actual: TypeShape,
    expected: TypeShape,
) -> Compatibility | None:
    """Return the subtype verdict only when it is definitively False.

    Args:
        actual: Inferred type of the value.
        expected: Declared/annotated type.

    Returns:
        The verdict when ``compatible is False``, else ``None``.

    """
    if str(object=actual) == "Unknown":
        return None
    verdict: Compatibility = subtype(actual=actual, expected=expected)
    if verdict.compatible is False:
        return verdict
    return None


def _value_shape(*, module: CommentedModule, value: expr) -> TypeShape:
    """Infer the shape of a value expression.

    Bare constants are not indexed by the solver, so literals map
    directly; everything else goes through :meth:`infer_type`.

    Args:
        module: Parsed module.
        value: Expression to type.

    Returns:
        Inferred shape.

    """
    if isinstance(value, Constant):
        literal: (
            str | bytes | bool | int | float | complex | EllipsisType | None
        ) = value.value
        return atomic(
            name="None" if literal is None else type(literal).__name__,
        )
    return module.infer_type(node=value).inferred


def _own_returns(*, node: FunctionDef | AsyncFunctionDef) -> list[Return]:
    """Return statements belonging directly to ``node``'s body.

    Nested function, async function and lambda bodies are pruned —
    their returns belong to their own signatures.

    Args:
        node: Function to inspect.

    Returns:
        ``return`` statement nodes in source order.

    """
    found: list[Return] = []
    stack: list[AST] = list(node.body)
    while stack:
        current: AST = stack.pop()
        if isinstance(current, Return):
            found.append(current)
            continue
        if isinstance(current, _SCOPE_NODES):
            continue
        stack.extend(iter_child_nodes(node=current))
    found.reverse()
    return found


def _all_functions(
    *,
    module: CommentedModule,
) -> list[FunctionDef | AsyncFunctionDef]:
    """Every function definition in the module, any nesting depth.

    Args:
        module: Parsed module.

    Returns:
        Function nodes in source order.

    """
    found: list[FunctionDef | AsyncFunctionDef] = []
    stack: list[AST] = list(module.body)
    while stack:
        current: AST = stack.pop()
        if isinstance(current, (FunctionDef, AsyncFunctionDef)):
            found.append(current)
        stack.extend(iter_child_nodes(node=current))
    found.reverse()
    return found


def find_return_mismatches(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag returns provably incompatible with the declared return type.

    Args:
        filename: Source name for spans.
        module: Parsed module.

    Returns:
        Candidates for each mismatched ``return`` statement.

    """
    candidates: list[Candidate] = []
    for node in _all_functions(module=module):
        expected: TypeShape | None = _declared_shape(annotation=node.returns)
        if expected is None:
            continue
        for stmt_node in _own_returns(node=node):
            value: expr | None = stmt_node.value
            if value is None or isinstance(value, (Yield, YieldFrom)):
                continue
            actual: TypeShape = _value_shape(module=module, value=value)
            verdict: Compatibility | None = _definitely_incompatible(
                actual=actual,
                expected=expected,
            )
            if verdict is None:
                continue
            candidates.append(
                Candidate(
                    span=span_of(node=stmt_node, filename=filename),
                    evidence={
                        "function": node.name,
                        "declared": str(object=expected),
                        "inferred": str(object=actual),
                    },
                ),
            )
    return tuple(candidates)


def find_incompatible_defaults(
    *,
    module: CommentedModule,
    filename: str,
) -> tuple[Candidate, ...]:
    """Flag parameter defaults provably incompatible with annotations.

    Args:
        filename: Source name for spans.
        module: Parsed module.

    Returns:
        Candidates for each mismatched default.

    """
    candidates: list[Candidate] = []
    for node in _all_functions(module=module):
        args: arguments = node.args
        positional: list[arg] = [*args.posonlyargs, *args.args]
        defaults: list[expr | None] = [
            *([None] * (len(positional) - len(args.defaults))),
            *args.defaults,
        ]
        pairs: list[tuple[arg, expr]] = [
            (parameter, default)
            for parameter, default in zip(positional, defaults, strict=True)
            if default is not None and parameter.arg not in ("self", "cls")
        ]
        pairs.extend(
            (parameter, default)
            for parameter, default in zip(
                args.kwonlyargs,
                args.kw_defaults,
                strict=True,
            )
            if default is not None
        )
        for parameter, default in pairs:
            expected: TypeShape | None = _declared_shape(
                annotation=parameter.annotation,
            )
            if expected is None:
                continue
            actual: TypeShape = _value_shape(module=module, value=default)
            verdict: Compatibility | None = _definitely_incompatible(
                actual=actual,
                expected=expected,
            )
            if verdict is None:
                continue
            candidates.append(
                Candidate(
                    span=span_of(node=default, filename=filename),
                    evidence={
                        "function": node.name,
                        "parameter": parameter.arg,
                        "declared": str(object=expected),
                        "inferred": str(object=actual),
                    },
                ),
            )
    return tuple(candidates)
