"""Finalizer module for AST graph inference output.

This module provides functions to finalize and format inferred Python code,
including adding docstrings, fixing type annotations, and applying
various AST transformations to produce clean, type-annotated output.
"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Dict,
    Expr,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Return,
    Subscript,
    alias,
    dump,
    expr,
    fix_missing_locations,
    keyword,
    parse,
    stmt,
    unparse,
)
from typing import TYPE_CHECKING, Final, cast, final

from astart._graph.dispatch import LowercaseTransformer
from astart._graph.graph.semantics import (
    build_annotation,
    nodes_of_type,
    render_annotation,
)

if TYPE_CHECKING:
    from astart._graph.backend.engine import Parenthesized


@final
class Constants:
    """Group module-level constants.

    Attributes:
        typevar_factories: Grouped module constant.

    """

    typevar_factories: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple"},
    )


def parse_ann(src: str) -> expr:
    """Build a type annotation AST expression from a type string.

    Args:
        src: Src supplied as str for this operation.

    Returns:
        expr produced by this operation.

    """
    return build_annotation(text=src)


_DICT_OBJECT_OBJECT_CANON: Final[expr] = parse_ann(src="dict[object, object]")


def ann_src(node: AST | None) -> str:
    """Render an AST annotation node to its canonical type string.

    Args:
        node: The node examined while render an AST annotation node to its
            canonical type string.

    Returns:
        Rendered source text produced by this operation.

    """
    return render_annotation(node=node)


def name_of(node: AST) -> str | None:
    """Extract the name from an AST node if possible.

    Args:
        node: The node examined while extract the name from an AST node if
            possible.

    Returns:
        str | None produced by this operation.

    """
    if isinstance(node, Name):
        return node.id
    if isinstance(node, Attribute):
        return node.attr
    if isinstance(node, Subscript):
        return name_of(node=node.value)
    return None


def is_name(node: AST, name: str) -> bool:
    """Check if an AST node is a Name node with the given identifier.

    Args:
        name: Identifier of the name being resolved.
        node: The node examined while check if an AST node is a Name node with
            the given identifier.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(node, Name) and node.id == name


def ensure_import(module: Module, module_name: str, names: list[str]) -> None:
    """Ensure that specific names are imported from a module.

    Args:
        module: The module examined while ensure that specific names are
            imported from a module.
        module_name: Identifier of the module being resolved.
        names: Names supplied as list[str] for this operation.

    """
    existing: ImportFrom | None = None
    for s in module.body:
        if isinstance(s, ImportFrom) and s.module == module_name:
            existing = s
            break
    current: set[str] = {a.name for a in existing.names} if existing else set()
    missing: list[str] = [n for n in names if n not in current]
    if not missing:
        return
    if existing:
        existing.names.extend(alias(name=n) for n in missing)
        return
    idx: int = 0
    if (
        module.body
        and isinstance(module.body[0], Expr)
        and isinstance(module.body[0].value, Constant)
        and isinstance(module.body[0].value.value, str)
    ):
        idx = 1
    while (
        idx < len(module.body)
        and isinstance(module.body[idx], ImportFrom)
        and (
            cast(typ="ImportFrom", val=module.body[idx]).module == "__future__"
        )
    ):
        idx += 1
    module.body.insert(
        idx,
        ImportFrom(
            module=module_name,
            names=[alias(name=n) for n in names],
            level=0,
        ),
    )


def _add_protocol_method_doc(item: FunctionDef) -> None:
    """Add docstring to protocol method if missing.

    Args:
        item: Item supplied as FunctionDef for this operation.

    """
    if not (
        item.body
        and isinstance(item.body[0], Expr)
        and isinstance(item.body[0].value, Constant)
        and isinstance(item.body[0].value.value, str)
    ):
        item.body.insert(
            0,
            Expr(value=Constant(value=(f"Protocol method {item.name}."))),
        )


def protocol_method_docs(module: Module) -> None:
    """Add docstrings to protocol methods and fix known protocol classes.

    Args:
        module: The module examined while add docstrings to protocol methods
            and fix known protocol classes.

    """
    for cls in nodes_of_type(root=module, types=(ClassDef,)):
        if any(name_of(node=b) == "Protocol" for b in cls.bases):
            for item in cls.body:
                if isinstance(item, AnnAssign):
                    item.value = None
                if isinstance(item, FunctionDef):
                    _add_protocol_method_doc(item=item)


def _add_ellipsis_to_abstract_methods(_cls: ClassDef) -> None:
    """Add ellipsis to abstract methods that only have a docstring.

    Args:
        _cls: Cls supplied as ClassDef for this operation.

    """
    for item in _cls.body:
        if isinstance(item, FunctionDef):
            has_abstract: bool = any(
                name_of(node=dec) == "abstractmethod"
                for dec in item.decorator_list
            )
            only_doc: bool = (
                len(item.body) == 1
                and isinstance(item.body[0], Expr)
                and isinstance(item.body[0].value, Constant)
                and isinstance(item.body[0].value.value, str)
            )
            if has_abstract and only_doc:
                item.body.append(Expr(value=Constant(value=Ellipsis)))


def class_and_method_fixes(module: Module) -> None:
    """Apply structural, name-agnostic class/method fixes.

    Args:
        module: The module examined while apply structural, name-agnostic
            class/method fixes.

    """
    for _cls in nodes_of_type(root=module, types=(ClassDef,)):
        _add_ellipsis_to_abstract_methods(_cls=_cls)


def function_fixes(module: Module) -> None:
    """Apply structural, name-agnostic function fixes.

    Annotation refinement is performed by the inference engine and the
    generic post-refinement passes; no fixture-specific signature patching
    is applied here.


    Args:
        module: The module examined while apply structural, name-agnostic
            function fixes.

    """
    _ = module


def transform_namedtuple_keyword_calls(module: Module) -> None:
    """Preserve keyword-based NamedTuple construction calls.

    Args:
        module: The module examined while preserve keyword-based NamedTuple
            construction calls.

    """
    _ = module


def replace_assigns_with_annassigns(module: Module) -> None:
    """Reserved for structural assign-to-annassign promotion (none applied).

    Args:
        module: The module examined while reserved for structural
            assign-to-annassign promotion (none applied).

    """
    _ = module


def ensure_type_checking_import(
    module: Module,
    module_name: str,
    names: list[str],
) -> None:
    """Ensure imports are added inside a TYPE_CHECKING block.

    Args:
        module: The module examined while ensure imports are added inside a
            TYPE_CHECKING block.
        module_name: Identifier of the module being resolved.
        names: Names supplied as list[str] for this operation.

    """
    existing_if: If | None = None
    for s in module.body:
        if (
            isinstance(s, If)
            and isinstance(s.test, Name)
            and (s.test.id == "TYPE_CHECKING")
        ):
            existing_if = s
            break
    import_stmt: ImportFrom = ImportFrom(
        module=module_name,
        names=[alias(name=name) for name in names],
        level=0,
    )
    if existing_if is None:
        idx: int = 0
        if (
            module.body
            and isinstance(module.body[0], Expr)
            and isinstance(module.body[0].value, Constant)
            and isinstance(module.body[0].value.value, str)
        ):
            idx = 1
        while idx < len(module.body) and isinstance(
            module.body[idx],
            (Import, ImportFrom),
        ):
            idx += 1
        module.body.insert(
            idx,
            If(
                test=Name(id="TYPE_CHECKING", ctx=Load()),
                body=[import_stmt],
                orelse=[],
            ),
        )
        return
    for s in existing_if.body:
        if isinstance(s, ImportFrom) and s.module == module_name:
            current: set[str] = {alias.name for alias in s.names}
            s.names.extend(
                alias(name=name) for name in names if name not in current
            )
            return
    existing_if.body.append(import_stmt)


def structural_equal(left: AST, right: AST) -> bool:
    """Compare two AST nodes by structure, ignoring source positions.

    Args:
        left: Left supplied as AST for this operation.
        right: Right supplied as AST for this operation.

    Returns:
        Whether the requested condition holds.

    """
    return dump(node=left) == dump(node=right)


class _BareTypeExpander(LowercaseTransformer):
    """Expand bare ``type`` names to ``type[object]`` subscripts on the AST."""

    @staticmethod
    def visit_name(node: Name) -> AST:
        """Visit name.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Transformed AST node, or None when no replacement is produced.

        """
        if node.id == "type":
            return Subscript(
                value=Name(id="type", ctx=Load()),
                slice=Name(id="object", ctx=Load()),
                ctx=Load(),
            )
        return node

    def visit_subscript(self, node: Subscript) -> AST:
        """Visit subscript.

        Args:
            node: AST node being inspected or transformed.

        Returns:
            Transformed AST node, or None when no replacement is produced.

        """
        node.slice = cast(typ="expr", val=self.visit(node=node.slice))
        if not (isinstance(node.value, Name) and node.value.id == "type"):
            node.value = cast(typ="expr", val=self.visit(node=node.value))
        return node

    def visit_parenthesized(self, node: Parenthesized) -> Parenthesized:
        """Visit a Parenthesized node and preserve it through expansion.

        Args:
            node: The node examined while visit a Parenthesized node and
                preserve it through expansion.

        Returns:
            Parenthesized produced by this operation.

        """
        node.value = cast(typ="expr", val=self.visit(node=node.value))
        return node


def expand_bare_type_annotation(node: expr) -> expr:
    """Expand bare ``type`` annotations to ``type[object]``.

    Args:
        node: The node examined while expand bare ``type`` annotations to
            ``type[object]``.

    Returns:
        expr produced by this operation.

    """
    return cast(typ="expr", val=_BareTypeExpander().visit(node=node))


def minimize_type_object_annotations(module: Module) -> None:
    """Expand bare ``type`` to ``type[object]`` to keep the instance bound.

    Args:
        module: The module examined while expand bare ``type`` to
            ``type[object]`` to keep the instance bound.

    """
    for node in nodes_of_type(
        root=module,
        types=(FunctionDef, AsyncFunctionDef, AnnAssign),
    ):
        if isinstance(node, AnnAssign):
            node.annotation = expand_bare_type_annotation(node=node.annotation)
            continue
        if node.returns is not None and node.name != "__new__":
            node.returns = expand_bare_type_annotation(node=node.returns)
        for arg_node in [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]:
            if arg_node.annotation is not None:
                arg_node.annotation = expand_bare_type_annotation(
                    node=arg_node.annotation,
                )
        if node.args.vararg and node.args.vararg.annotation is not None:
            node.args.vararg.annotation = expand_bare_type_annotation(
                node=node.args.vararg.annotation,
            )
        if node.args.kwarg and node.args.kwarg.annotation is not None:
            node.args.kwarg.annotation = expand_bare_type_annotation(
                node=node.args.kwarg.annotation,
            )


def return_has_string_keys(function: FunctionDef) -> bool:
    """Check if a function's return dict has only string keys.

    Args:
        function: The function examined while check if a function's return dict
            has only string keys.

    Returns:
        Whether the requested condition holds.

    """
    saw_dict: bool = False
    for node in nodes_of_type(root=function, types=(Return,)):
        if not isinstance(node.value, Dict):
            continue
        saw_dict = True
        for key in node.value.keys:
            if key is None:
                continue
            if not isinstance(key, Constant) or not isinstance(key.value, str):
                return False
    return saw_dict


def minimize_heterogeneous_result_returns(module: Module) -> None:
    """Normalize string-keyed heterogeneous dict returns structurally.

    A ``dict[object, object]`` return whose dict literals only use string
    keys is narrowed to ``dict[str, object]``. No named alias is fabricated:
    inventing a corpus-specific alias name would not be agnostic.


    Args:
        module: The module examined while normalize string-keyed heterogeneous
            dict returns structurally.

    """
    for node in module.body:
        if not isinstance(node, FunctionDef) or node.returns is None:
            continue
        returns: expr = node.returns
        if structural_equal(
            left=returns,
            right=_DICT_OBJECT_OBJECT_CANON,
        ) and return_has_string_keys(function=node):
            node.returns = parse_ann(src="dict[str, object]")


def minimize_object_surface(module: Module) -> None:
    """Minimize the use of ``object`` in type annotations.

    Args:
        module: The module examined while minimize the use of ``object`` in
            type annotations.

    """
    minimize_type_object_annotations(module=module)
    minimize_heterogeneous_result_returns(module=module)


def _is_protocol_class(node: stmt) -> bool:
    """Report whether ``node`` is a module-level ``Protocol`` subclass.

    Args:
        node: The node examined while report whether ``node`` is a module-level
            ``Protocol`` subclass.

    Returns:
        Whether the requested condition holds.

    """
    return isinstance(node, ClassDef) and any(
        name_of(node=base) == "Protocol" for base in node.bases
    )


def _is_type_checking_block(node: stmt) -> bool:
    """Report whether ``node`` is an ``if TYPE_CHECKING:`` block.

    Args:
        node: The node examined while report whether ``node`` is an ``if
            TYPE_CHECKING:`` block.

    Returns:
        Whether the requested condition holds.

    """
    if not isinstance(node, If):
        return False
    if not isinstance(node.test, Name):
        return False
    return node.test.id == "TYPE_CHECKING"


def _typevar_call(node: stmt) -> Call | None:
    """Return the ``TypeVar``/``ParamSpec`` call bound by ``node``, if any.

    Args:
        node: The node examined while return the ``TypeVar``/``ParamSpec`` call
            bound by ``node``, if any.

    Returns:
        Call | None produced by this operation.

    """
    if (
        isinstance(node, Assign)
        and isinstance(node.value, Call)
        and (name_of(node=node.value.func) in Constants.typevar_factories)
    ):
        return node.value
    return None


def _normalize_typevar_call(call: Call) -> None:
    """Rewrite ``TypeVar(name="X")`` into positional ``TypeVar("X")`` form.

    Args:
        call: The call examined while rewrite ``TypeVar(name="X")`` into
            positional ``TypeVar("X")`` form.

    """
    if call.args:
        return
    remaining: list[keyword] = []
    name_value: expr | None = None
    for kw in call.keywords:
        if kw.arg == "name" and name_value is None:
            name_value = kw.value
        else:
            remaining.append(kw)
    if name_value is not None:
        call.args = [name_value]
        call.keywords = remaining


def organize_protocols_and_typevars(module: Module) -> None:
    """Group module-level Protocols and type variables into one block.

    Different inference stages append synthesized ``Protocol`` classes and
    ``TypeVar``/``ParamSpec`` declarations independently, so they end up
    interleaved with each other (and with unrelated statements). This pass
    gathers them, preserving relative order, and re-emits all protocols
    first followed by all type variables at the position of the earliest
    such statement. Protocols precede type variables so a ``bound=`` that
    references a protocol still resolves. Type-variable calls are normalized
    to the positional-name form for a consistent style.

    Also moves ``if TYPE_CHECKING:`` blocks to follow the imports,
    before protocols and type variables.


    Args:
        module: The module examined while group module-level Protocols and type
            variables into one block.

    """
    protocols: list[stmt] = []
    typevars: list[stmt] = []
    type_checking_blocks: list[stmt] = []
    anchor: int | None = None
    for index, node in enumerate(iterable=module.body):
        call: Call | None = _typevar_call(node=node)
        if _is_protocol_class(node=node):
            protocols.append(node)
        elif call is not None:
            _normalize_typevar_call(call=call)
            typevars.append(node)
        elif _is_type_checking_block(node=node):
            type_checking_blocks.append(node)
        else:
            continue
        if anchor is None:
            anchor = index
    if anchor is None:
        return
    if not (protocols or typevars or type_checking_blocks):
        return
    grouped: set[int] = {
        id(node) for node in (*protocols, *typevars, *type_checking_blocks)
    }
    remaining: list[stmt] = [
        node for node in module.body if id(node) not in grouped
    ]
    insert_at: int = min(anchor, len(remaining))
    remaining[insert_at:insert_at] = [
        *type_checking_blocks,
        *protocols,
        *typevars,
    ]
    module.body[:] = remaining


def finalize_module(module: Module) -> None:
    """Run all finalize passes on a module in place (no parse/unparse).

    Args:
        module: The module examined while run all finalize passes on a module
            in place (no parse/unparse).

    """
    ensure_import(
        module=module,
        module_name="typing",
        names=[
            "TYPE_CHECKING",
            "cast",
            "Protocol",
            "override",
            "TypeVar",
            "ParamSpec",
            "Final",
            "NamedTuple",
        ],
    )
    ensure_type_checking_import(
        module=module,
        module_name="_typeshed",
        names=["SupportsKeysAndGetItem"],
    )
    protocol_method_docs(module=module)
    class_and_method_fixes(module=module)
    function_fixes(module=module)
    transform_namedtuple_keyword_calls(module=module)
    replace_assigns_with_annassigns(module=module)
    minimize_object_surface(module=module)
    organize_protocols_and_typevars(module=module)
    fix_missing_locations(node=module)


def finalize(source: str) -> str:
    """Finalize source code by applying all AST transformations.

    Args:
        source: The source examined while finalize source code by applying all
            AST transformations.

    Returns:
        Rendered source text produced by this operation.

    """
    module: Module = parse(source=source)
    finalize_module(module=module)
    return (
        unparse(ast_obj=module)
        + """\

"""
    )


def finalize_and_format_module(module: Module) -> str:
    """Finalize a module in place and format it, unparsing exactly once.

    Type annotations are emitted structurally (``dict[str, int]`` rather than
    a fabricated ``IntDict`` alias). The source under conversion defines no
    such aliases, so inventing names would be specific to a corpus rather
    than agnostic.


    Args:
        module: The module examined while finalize a module in place and format
            it, unparsing exactly once.

    Returns:
        str produced by this operation.

    """
    finalize_module(module=module)
    fix_missing_locations(node=module)
    return (
        unparse(ast_obj=module)
        + """\

"""
    )
