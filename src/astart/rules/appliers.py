"""Edit appliers: tree-level rewrites that fixes are made of."""

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
    FunctionDef,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Store,
    Subscript,
    arg,
    dump,
    expr,
    keyword,
    parse,
    stmt,
    unparse,
    walk,
)
from ast import (
    ParamSpec as AstParamSpec,
)
from ast import (
    TypeVar as AstTypeVar,
)
from ast import (
    TypeVarTuple as AstTypeVarTuple,
)
from typing import TYPE_CHECKING, Final, final

from astart.rules.facts import Constants, bound_call, keyword_candidates
from astart.rules.hints import Hint, HintBasis, returns_nothing
from astart.rules.imports import ensure_names, insert_import
from astart.rules.protocols import protocol_source, structural_usage
from astart.rules.provable import never_returns
from astart.rules.typevars import passthrough_return
from astart.semantic import ArgumentOrigin, ParameterKind

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import BoundCall
    from astart.rules.facts import Applier, ModuleFacts, Subject
    from astart.rules.protocols import StructuralUsage
type NodeAttributes = dict[str, AST | list[AST] | int | str | None]


def _final_reference(*, facts: ModuleFacts) -> tuple[expr, bool]:
    """Choose how to spell ``Final`` in this module.

    Args:
        facts: Resolved imports.

    Returns:
        The expression and whether an import must be added.

    """
    if facts.final_names:
        return Name(id=sorted(facts.final_names)[0], ctx=Load()), False
    if facts.typing_names:
        owner: str = sorted(facts.typing_names)[0]
        return (
            Attribute(
                value=Name(id=owner, ctx=Load()),
                attr="Final",
                ctx=Load(),
            ),
            False,
        )
    return Name(id="Final", ctx=Load()), True


def add_final(subject: Subject, facts: ModuleFacts) -> None:
    """Turn ``NAME = <literal>`` into ``NAME: Final[type] = <literal>``.

    The statement keeps its identity, so comments and layout survive.

    Args:
        subject: Assignment subject.
        facts: Resolved imports and the parsed module.

    """
    statement: AST | None = subject.statement
    match statement:
        case Assign(
            targets=[Name() as target],
            value=Constant(value=value),
        ) if isinstance(value, Constants.immutable_literals):
            pass
        case _:
            return
    reference, needs_import = _final_reference(facts=facts)
    if needs_import:
        reference: expr = Name(
            id=insert_import(
                module=facts.module,
                source="typing",
                name="Final",
                before=_ancestor_index(module=facts.module, node=statement),
            ),
            ctx=Load(),
        )
    attributes: NodeAttributes = vars(statement)
    attributes["target"] = target
    attributes["annotation"] = Subscript(
        value=reference,
        slice=Name(id=type(value).__name__, ctx=Load()),
        ctx=Load(),
    )
    attributes["simple"] = 1
    del attributes["targets"]
    _ = attributes.pop("type_comment", None)
    object.__setattr__(statement, "__class__", AnnAssign)


def add_keywords(subject: Subject, facts: ModuleFacts) -> None:
    """Pass keyword-capable positional arguments by name.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    """
    call: AST = subject.node
    bound: BoundCall | None = bound_call(subject=subject, facts=facts)
    names: list[str] = keyword_candidates(subject=subject, facts=facts)
    if not isinstance(call, Call) or bound is None or not names:
        return
    positional_only: int = sum(
        1
        for argument in bound.arguments
        if argument.origin is ArgumentOrigin.POSITIONAL
        and argument.parameter.kind is ParameterKind.POSITIONAL_ONLY
    )
    movable: list[expr] = call.args[positional_only:]
    if len(movable) != len(names):
        return
    keywords: list[keyword] = [
        keyword(arg=name, value=value)
        for name, value in zip(names, movable, strict=True)
    ]
    call.args = call.args[:positional_only]
    call.keywords = [*keywords, *call.keywords]


def add_none_return(subject: Subject, _facts: ModuleFacts) -> None:
    """Annotate a function that provably returns nothing with ``-> None``.

    Args:
        subject: Function subject.
        _facts: Unused resolved imports.

    """
    match subject.node:
        case (
            FunctionDef(returns=None)
            | AsyncFunctionDef(
                returns=None,
            ) as function
        ) if returns_nothing(function=function):
            function.returns = Constant(value=None)
        case _:
            return


def add_noreturn(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a function whose every path raises with ``NoReturn``.

    Args:
        subject: Function subject.
        facts: Resolved imports and the parsed module.

    """
    match subject.node:
        case (
            FunctionDef(returns=None)
            | AsyncFunctionDef(returns=None) as function
        ) if never_returns(function=function):
            name: str = insert_import(
                module=facts.module,
                source="typing",
                name="NoReturn",
                before=_ancestor_index(module=facts.module, node=function),
            )
            function.returns = Name(id=name, ctx=Load())
        case _:
            return


def add_inferred_annotation(subject: Subject, facts: ModuleFacts) -> None:
    """Write a corroborated hint onto an unannotated parameter or function.

    Args:
        subject: Parameter or function subject.
        facts: Resolved imports, parsed module and lazily computed hints.

    """
    if facts.hints is None:
        return
    hint: Hint | None = facts.hints.index().hint_for(node=subject.node)
    if hint is None or hint.basis is HintBasis.proven_none:
        return
    expression: expr = parse(source=hint.source, mode="eval").body
    owner: AST = (
        subject.statement if subject.kind == "Parameter" else subject.node
    ) or subject.node
    ensure_names(
        module=facts.module,
        expression=expression,
        before=_ancestor_index(module=facts.module, node=owner),
    )
    match subject.node:
        case arg(annotation=None) as parameter:
            parameter.annotation = expression
        case (
            FunctionDef(returns=None)
            | AsyncFunctionDef(
                returns=None,
            ) as function
        ):
            function.returns = expression
        case _:
            return


def _pascal(*, text: str) -> str:
    """Convert a snake_case identifier to PascalCase.

    Args:
        text: Identifier.

    Returns:
        The identifier without underscores, each part capitalised.

    """
    return "".join(part[:1].upper() + part[1:] for part in text.split(sep="_"))


def _module_names(*, module: Module) -> set[str]:
    """Collect the names bound at module level.

    Args:
        module: Module to inspect.

    Returns:
        Every top-level binding name.

    """
    names: set[str] = set()
    for statement in module.body:
        match statement:
            case ClassDef(name=name) | FunctionDef(name=name):
                names.add(name)
            case AsyncFunctionDef(name=name):
                names.add(name)
            case Import(names=aliases) | ImportFrom(names=aliases):
                names.update(
                    (a.asname or a.name).split(sep=".")[0] for a in aliases
                )
            case _:
                names.update(
                    node.id
                    for node in walk(node=statement)
                    if isinstance(node, Name) and isinstance(node.ctx, Store)
                )
    return names


def _strip_locations(*, node: AST) -> None:
    """Remove source positions so the writer treats the node as new.

    Args:
        node: Root of the subtree to clear.

    """
    for child in walk(node=node):
        for attribute in (
            "lineno",
            "col_offset",
            "end_lineno",
            "end_col_offset",
        ):
            _ = vars(child).pop(attribute, None)


def _existing_protocol(
    *,
    module: Module,
    candidate: ClassDef,
) -> str | None:
    """Find a protocol class with the same members.

    Args:
        module: Module to search.
        candidate: Class whose members are compared.

    Returns:
        The existing class name, or ``None``.

    """
    wanted: str = "".join(dump(node=item) for item in candidate.body[1:])
    for statement in module.body:
        if isinstance(statement, ClassDef) and any(
            unparse(ast_obj=base).split(sep=".")[-1] == "Protocol"
            for base in statement.bases
        ):
            found: str = "".join(
                dump(node=item) for item in statement.body[1:]
            )
            if found == wanted:
                return statement.name
    return None


def synthesize_protocol(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a structurally used parameter with a synthesized ``Protocol``.

    The class is inserted before the top-level statement that contains the
    function, so it exists when the annotation is evaluated.

    Args:
        subject: Parameter subject.
        facts: Resolved imports and the parsed module.

    """
    match (subject.node, subject.statement):
        case [
            arg(annotation=None) as parameter,
            FunctionDef() | AsyncFunctionDef() as function,
        ]:
            pass
        case _:
            return
    usage: StructuralUsage | None = structural_usage(
        function=function,
        parameter=parameter.arg,
        counts=facts.binding_counts,
    )
    if usage is None:
        return
    module: Module = facts.module
    taken: set[str] = _module_names(module=module)
    base: str = (
        f"{_pascal(text=function.name)}{_pascal(text=parameter.arg)}Protocol"
    )
    name: str = base
    suffix: int = 2
    while name in taken:
        name = f"{base}{suffix}"
        suffix += 1
    match parse(
        source=protocol_source(
            name=name,
            function=function.name,
            parameter=parameter.arg,
            usage=usage,
        ),
    ).body:
        case [ClassDef() as candidate]:
            pass
        case _:
            return
    reused: str | None = _existing_protocol(module=module, candidate=candidate)
    if reused is None:
        local: str = insert_import(
            module=module,
            source="typing",
            name="Protocol",
            before=_ancestor_index(module=module, node=function),
        )
        candidate.bases = [Name(id=local, ctx=Load())]
        _strip_locations(node=candidate)
        module.body.insert(
            _ancestor_index(module=module, node=function),
            candidate,
        )
    parameter.annotation = Name(id=reused or name, ctx=Load())


def _is_plain_typevar(*, statement: stmt, name: str) -> bool:
    """Tell whether a statement is ``NAME = TypeVar("NAME")``.

    Args:
        statement: Top-level statement.
        name: Expected variable name.

    Returns:
        ``True`` for an unconstrained, unbounded, invariant declaration.

    """
    match statement:
        case Assign(
            targets=[Name(id=target)],
            value=Call(
                func=Name(id="TypeVar") | Attribute(attr="TypeVar"),
                args=[Constant(value=label)],
                keywords=[],
            ),
        ):
            return target == name and label == name
        case _:
            return False


def _ancestor_index(*, module: Module, node: AST) -> int:
    """Find the top-level statement that contains a node.

    Args:
        module: Module to search.
        node: Node inside a top-level statement.

    Returns:
        The statement's index in the module body.

    """
    return next(
        position
        for position, statement in enumerate(iterable=module.body)
        if any(child is node for child in walk(node=statement))
    )


def _class_variables(*, module: Module, function: AST) -> set[str]:
    """Collect names the enclosing classes already use as type parameters.

    Args:
        module: Module to search.
        function: Function whose enclosing classes are inspected.

    Returns:
        Names in base lists, class keywords and PEP 695 type parameters.

    """
    names: set[str] = set()
    for statement in module.body:
        for node in walk(node=statement):
            if isinstance(node, ClassDef) and any(
                child is function for child in walk(node=node)
            ):
                for part in (*node.bases, *(k.value for k in node.keywords)):
                    names.update(
                        item.id
                        for item in walk(node=part)
                        if isinstance(item, Name)
                    )
                names.update(
                    item.name
                    for item in node.type_params
                    if isinstance(
                        item,
                        (AstTypeVar, AstParamSpec, AstTypeVarTuple),
                    )
                )
    return names


def _typevar_name(
    *,
    module: Module,
    before: int,
    forbidden: set[str],
) -> tuple[str, bool]:
    """Choose the type variable to use, reusing a plain declaration.

    Args:
        module: Module to search.
        before: Declarations at or after this body index cannot be used.
        forbidden: Names the enclosing classes already use as parameters.

    Returns:
        The name and whether it must be declared.

    """
    taken: set[str] = _module_names(module=module)
    suffix: int = 1
    while True:
        name: str = "T" if suffix == 1 else f"T{suffix}"
        if name in forbidden:
            suffix += 1
            continue
        if any(
            _is_plain_typevar(statement=statement, name=name)
            for statement in module.body[:before]
        ):
            return name, False
        if name not in taken:
            return name, True
        suffix += 1


def synthesize_typevar(subject: Subject, facts: ModuleFacts) -> None:
    """Make a pass-through parameter and its return share a type variable.

    The declaration ``T = TypeVar("T")`` is inserted before the top-level
    statement that contains the function.

    Args:
        subject: Parameter subject.
        facts: Resolved imports and the parsed module.

    """
    match (subject.node, subject.statement):
        case [
            arg(annotation=None) as parameter,
            FunctionDef() | AsyncFunctionDef() as function,
        ]:
            pass
        case _:
            return
    module: Module = facts.module
    index: int = _ancestor_index(module=module, node=function)
    name, declare = _typevar_name(
        module=module,
        before=index,
        forbidden=_class_variables(module=module, function=function),
    )
    returns: str | None = passthrough_return(
        function=function,
        parameter=parameter.arg,
        variable=name,
        counts=facts.binding_counts,
    )
    if returns is None:
        return
    if declare:
        factory: str = insert_import(
            module=module,
            source="typing",
            name="TypeVar",
            before=index,
        )
        match parse(source=f'{name} = {factory}("{name}")').body:
            case [Assign() as declaration]:
                _strip_locations(node=declaration)
                module.body.insert(
                    _ancestor_index(module=module, node=function),
                    declaration,
                )
            case _:
                return
    parameter.annotation = Name(id=name, ctx=Load())
    function.returns = parse(source=returns, mode="eval").body


@final
class Appliers:
    """Group the registered appliers.

    Attributes:
        table: Applier function for every key in the registries.

    """

    table: Final[Mapping[str, Applier]] = {
        "typing.add-final": add_final,
        "calls.add-keywords": add_keywords,
        "typing.add-none-return": add_none_return,
        "typing.add-noreturn": add_noreturn,
        "typing.add-inferred-annotation": add_inferred_annotation,
        "typing.synthesize-protocol": synthesize_protocol,
        "typing.synthesize-typevar": synthesize_typevar,
    }
