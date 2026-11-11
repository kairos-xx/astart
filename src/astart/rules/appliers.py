"""Edit appliers: tree-level rewrites that fixes are made of."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Await,
    BinOp,
    BitOr,
    Call,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    Load,
    Module,
    Name,
    Store,
    Subscript,
    Tuple,
    arg,
    copy_location,
    dump,
    expr,
    iter_child_nodes,
    iter_fields,
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
from copy import deepcopy
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final, cast, final

from astart.docstrings.core import Constants as DocstringConstants
from astart.docstrings.fixes import (
    add_entries,
    add_generator_results,
    heal_rename,
    remove_entries,
    tidy,
)
from astart.docstrings.protocols import document_protocol
from astart.docstrings.types import add_types
from astart.graph.conversion.synthesis import ProtocolGrammar
from astart.graph.dispatch import LowercaseTransformer
from astart.rules.facts import (
    Constants,
    bound_call,
    kept_positionals,
    keyword_candidates,
)
from astart.rules.grouping import (
    creatable,
    create_group,
    find_group,
    move_into,
    rename_constant,
    renameable,
)
from astart.rules.hints import Hint, HintBasis, returns_nothing
from astart.rules.imports import ensure_names, insert_import, module_classes
from astart.rules.protocols import (
    StructuralUsage,
    abstract_parameter,
    builtin_protocol,
    protocol_isinstanced,
    protocol_source,
    structural_usage,
    vacuous_usage,
)
from astart.rules.provable import (
    can_fall_off,
    module_constants,
    never_returns,
    scope_types,
)
from astart.rules.typevars import (
    TypeVarPlan,
    candidate_params,
    forwarding_decorator,
    function_scope_names,
    multi_return,
    receiver_info,
    shared_parameters,
    shared_return,
    typevar_plan,
)
from astart.rules.whitespace_rules import comment_wrap_plans
from astart.semantic.type_expressions import TypeExpressionCodec

type SetStr = set[str]

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import BoundCall, CommentedModule
    from astart.project.versions import PythonTarget
    from astart.rules.facts import Applier, ModuleFacts, Subject
    from astart.rules.protocols import StructuralUsage
    from astart.semantic.analyzer import SymbolRegistry
    from astart.semantic.identities import Symbol
type NodeAttributes = dict[str, AST | list[AST] | int | str | None]


@final
class _UnionRewrite(LowercaseTransformer):
    """Rewrite ``X | Y`` union syntax as ``Union[X, Y]`` in annotations."""

    def visit_binop(self, node: BinOp) -> expr:
        """Flatten one ``|`` chain and rebuild it as ``Union[...]``.

        Args:
            node (BinOp): The binary operation node.

        Returns:
            expr: The replacement ``Union`` subscript, or the node with its
                children rewritten for non-union operations.

        """
        if not isinstance(node.op, BitOr):
            return cast(typ="expr", val=self.generic_visit(node=node))
        members: list[expr] = [
            cast(typ="expr", val=self.visit(node=member))
            for member in _union_members(node=node)
        ]
        return copy_location(
            new_node=Subscript(
                value=Name(id="Union", ctx=Load()),
                slice=Tuple(elts=members, ctx=Load()),
                ctx=Load(),
            ),
            old_node=node,
        )


def _union_members(*, node: expr) -> list[expr]:
    """Flatten a ``X | Y | Z`` chain into its members.

    Args:
        node (expr): The expression that may head a union chain.

    Returns:
        list[expr]: The union's operands, or ``[node]`` itself when not a
            union.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return [
            *_union_members(node=node.left),
            *_union_members(node=node.right),
        ]
    return [node]


def _respell_unions(*, expression: expr, target: PythonTarget) -> expr:
    """Rewrite ``X | Y`` unions when the target's Python cannot parse them.

    Args:
        expression (expr): Parsed annotation expression.
        target (PythonTarget): Oldest Python version emitted code must run on.

    Returns:
        expr: The expression, with unions respelled as ``Union[...]`` when
            needed.

    """
    if target.union_syntax:
        return expression
    return cast(typ="expr", val=_UnionRewrite().visit(node=expression))


def _final_reference(*, facts: ModuleFacts) -> tuple[expr, bool]:
    """Choose how to spell ``Final`` in this module.

    Args:
        facts (ModuleFacts): Resolved imports.

    Returns:
        tuple[expr, bool]: The expression and whether an import must be added.

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
        subject (Subject): Assignment subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

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


def group_constant(subject: Subject, facts: ModuleFacts) -> None:
    """Move a ``Final`` module constant into the ``Constants`` class.

    The class is created, after the leading imports, when the module has no
    binding of that name at all.

    Args:
        subject (Subject): Annotated assignment subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    statement: AST | None = subject.statement
    match statement:
        case AnnAssign(target=Name(id=name)):
            pass
        case _:
            return
    group: ClassDef | None = find_group(
        module=facts.module,
        statement=statement,
        name=name,
        counts=facts.binding_counts,
    )
    if group is None and creatable(
        module=facts.module,
        statement=statement,
        counts=facts.binding_counts,
    ):
        group = create_group(module=facts.module)
    if group is not None:
        move_into(
            module=facts.module,
            cls=group,
            statement=statement,
            name=name,
        )


def snake_constant(subject: Subject, facts: ModuleFacts) -> None:
    """Rename a ``Constants`` attribute to lowercase snake_case.

    Args:
        subject (Subject): Assignment subject inside the class body.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    name: str = subject.name
    statement: AST | None = subject.statement
    if not isinstance(statement, (AnnAssign, Assign)):
        return
    cls: ClassDef | None = renameable(
        module=facts.module,
        statement=statement,
        name=name,
        counts=facts.binding_counts,
    )
    if cls is not None:
        rename_constant(
            module=facts.module,
            cls=cls,
            statement=statement,
            name=name,
        )


def wrap_comments(_subject: Subject, facts: ModuleFacts) -> None:
    """Reflow overlong standalone comment paragraphs.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    if facts.source is None:
        return
    for members, lines in comment_wrap_plans(
        comments=facts.module.comments,
        source_lines=facts.source.splitlines(),
        line_length=DocstringConstants.line_length,
    ):
        facts.module.replace_comment_lines(comments=members, lines=lines)


def add_keywords(subject: Subject, facts: ModuleFacts) -> None:
    """Pass keyword-capable positional arguments by name.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    call: AST = subject.node
    bound: BoundCall | None = bound_call(subject=subject, facts=facts)
    names: list[str] = keyword_candidates(subject=subject, facts=facts)
    if not isinstance(call, Call) or bound is None or not names:
        return
    positional_only: int = kept_positionals(bound=bound)
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
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused resolved imports.

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


def discard_result(subject: Subject, facts: ModuleFacts) -> None:
    """Assign a discarded call result to ``_``.

    The ``Expr`` statement keeps its value — the call, or the ``await``
    wrapping it — so comments and layout inside the call survive; only
    the statement node is replaced.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    call: AST = subject.node
    if not isinstance(call, Call):
        return
    parents: dict[AST, AST] = {
        child: parent
        for parent in walk(node=facts.module)
        for child in iter_child_nodes(node=parent)
    }
    value: AST = call
    owner: AST | None = parents.get(call)
    if isinstance(owner, Await):
        value = owner
        owner = parents.get(owner)
    if not isinstance(owner, Expr) or owner.value is not value:
        return
    statement: Expr = owner
    parent: AST | None = parents.get(statement)
    if parent is None:
        return
    _replace_child(
        parent=parent,
        old=statement,
        new=Assign(
            targets=[Name(id="_", ctx=Store())],
            value=statement.value,
        ),
    )


def _replace_child(*, parent: AST, old: AST, new: AST) -> None:
    """Swap one child of a node for another.

    Args:
        parent (AST): Node that holds the child.
        old (AST): Child to replace.
        new (AST): Replacement.

    """
    for field_name, value in iter_fields(node=parent):
        if value is old:
            setattr(parent, field_name, new)
            return
        if isinstance(value, list):
            children: list[AST] = cast(typ="list[AST]", val=value)
            for position, item in enumerate(iterable=children):
                if item is old:
                    children[position] = new
                    return


def add_attribute_annotation(subject: Subject, facts: ModuleFacts) -> None:
    """Turn ``self.x = value`` into ``self.x: T = value``.

    The statement keeps its identity, so comments and layout survive.

    Args:
        subject (Subject): Attribute assignment subject.
        facts (ModuleFacts): Resolved imports, parsed module and lazily
            computed hints.

    """
    statement: AST | None = subject.statement
    if facts.hints is None or not isinstance(statement, Assign):
        return
    hint: Hint | None = facts.hints.index().hint_for(node=statement)
    if (
        hint is None
        or hint.basis is not HintBasis.attribute_assignments
        or len(statement.targets) != 1
    ):
        return
    expression: expr = _respell_unions(
        expression=parse(source=hint.source, mode="eval").body,
        target=facts.target,
    )
    ensure_names(
        module=facts.module,
        expression=expression,
        before=_ancestor_index(module=facts.module, node=statement),
    )
    attributes: NodeAttributes = vars(statement)
    attributes["target"] = statement.targets[0]
    attributes["annotation"] = expression
    attributes["simple"] = 0
    del attributes["targets"]
    _ = attributes.pop("type_comment", None)
    object.__setattr__(statement, "__class__", AnnAssign)


def add_variable_annotation(subject: Subject, facts: ModuleFacts) -> None:
    """Turn ``name = value`` into ``name: T = value``.

    The statement keeps its identity, so comments and layout survive.

    Args:
        subject (Subject): Assignment subject.
        facts (ModuleFacts): Resolved imports, parsed module and negotiated
            variables.

    """
    statement: AST | None = subject.statement
    if (
        facts.variables is None
        or not isinstance(statement, Assign)
        or len(statement.targets) != 1
        or not isinstance(statement.targets[0], Name)
    ):
        return
    hint: Hint | None = facts.variables.hint_for(node=statement)
    if hint is None:
        return
    expression: expr = _respell_unions(
        expression=parse(source=hint.source, mode="eval").body,
        target=facts.target,
    )
    ensure_names(
        module=facts.module,
        expression=expression,
        before=_ancestor_index(module=facts.module, node=statement),
        skip=module_classes(module=facts.module),
    )
    attributes: NodeAttributes = vars(statement)
    attributes["target"] = statement.targets[0]
    attributes["annotation"] = expression
    attributes["simple"] = 1
    del attributes["targets"]
    _ = attributes.pop("type_comment", None)
    object.__setattr__(statement, "__class__", AnnAssign)


def add_noreturn(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a function whose every path raises with ``NoReturn``.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

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
        subject (Subject): Parameter or function subject.
        facts (ModuleFacts): Resolved imports, parsed module and lazily
            computed hints.

    """
    if facts.hints is None:
        return
    hint: Hint | None = facts.hints.index().hint_for(node=subject.node)
    if hint is None or hint.basis is HintBasis.proven_none:
        return
    expression: expr = _respell_unions(
        expression=parse(source=hint.source, mode="eval").body,
        target=facts.target,
    )
    owner: AST = (
        subject.statement if subject.kind == "Parameter" else subject.node
    ) or subject.node
    ensure_names(
        module=facts.module,
        expression=expression,
        before=_ancestor_index(module=facts.module, node=owner),
        skip=(
            module_classes(module=facts.module)
            if hint.basis is HintBasis.negotiated
            else frozenset()
        ),
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


def _module_names(*, module: Module) -> SetStr:
    """Collect the names bound at module level.

    Args:
        module (Module): Module to inspect.

    Returns:
        SetStr: Every top-level binding name.

    """
    names: SetStr = set()
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
        node (AST): Root of the subtree to clear.

    """
    for child in walk(node=node):
        for attribute in (
            "lineno",
            "col_offset",
            "end_lineno",
            "end_col_offset",
        ):
            _ = vars(child).pop(attribute, None)


def _protocol_shape(*, node: ClassDef) -> tuple[str, ...]:
    """Compare structural declarations independently of descriptive prose.

    Args:
        node (ClassDef): Existing or proposed protocol class.

    Returns:
        tuple[str, ...]: Member syntax fingerprints with
            class and method docstrings omitted.

    """
    members: list[str] = []
    for item in node.body:
        if (
            isinstance(item, Expr)
            and isinstance(item.value, Constant)
            and (isinstance(item.value.value, str))
        ):
            continue
        member: stmt = deepcopy(x=item)
        if isinstance(member, (FunctionDef, AsyncFunctionDef)) and member.body:
            first: stmt = member.body[0]
            if (
                isinstance(first, Expr)
                and isinstance(first.value, Constant)
                and (isinstance(first.value.value, str))
            ):
                member.body.pop(0)
        members.append(dump(node=member))
    return tuple(members)


def _existing_protocol(
    *,
    module: Module,
    candidate: ClassDef,
) -> str | None:
    """Find a protocol class with the same members.

    Args:
        module (Module): Module to search.
        candidate (ClassDef): Class whose members are compared.

    Returns:
        str | None: The existing class name, or ``None``.

    """
    wanted: tuple[str, ...] = _protocol_shape(node=candidate)
    for statement in module.body:
        if isinstance(statement, ClassDef) and any(
            unparse(ast_obj=base).split(sep=".")[-1] == "Protocol"
            for base in statement.bases
        ):
            found: tuple[str, ...] = _protocol_shape(node=statement)
            if found == wanted:
                return statement.name
    return None


def synthesize_protocol(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a structurally used parameter with the narrowest contract.

    Standard library protocols and ``Callable`` annotations are reused
    before a new class is created. A synthesized class lands before the
    top-level statement that contains the function — or wherever
    ``protocol_placement`` sends it — so it exists when the annotation is
    evaluated.

    Args:
        subject (Subject): Parameter subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

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
        env=scope_types(
            function=function,
            counts=facts.binding_counts,
            constants=module_constants(
                module=facts.module,
                counts=facts.binding_counts,
            ),
        ),
    )
    if usage is None or vacuous_usage(usage=usage):
        return
    module: CommentedModule = facts.module
    index: int = _ancestor_index(module=module, node=function)
    reused_builtin: tuple[str, tuple[tuple[str, str], ...]] | None = (
        builtin_protocol(usage=usage)
    )
    if reused_builtin is not None:
        _annotate_spelling(
            module=module,
            index=index,
            parameter=parameter,
            spelling=reused_builtin[0],
            imports=reused_builtin[1],
        )
        return
    if facts.accept_general:
        abstract: tuple[str, tuple[tuple[str, str], ...]] | None = (
            abstract_parameter(usage=usage)
        )
        if abstract is not None:
            _annotate_spelling(
                module=module,
                index=index,
                parameter=parameter,
                spelling=abstract[0],
                imports=abstract[1],
            )
            return
    emitted: tuple[str, bool] | None = _emit_protocol(
        module=module,
        function=function,
        parameter=parameter.arg,
        usage=usage,
        facts=facts,
    )
    if emitted is None:
        return
    name, quoted = emitted
    parameter.annotation = (
        Constant(value=name) if quoted else Name(id=name, ctx=Load())
    )


def _annotate_spelling(
    *,
    module: CommentedModule,
    index: int,
    parameter: arg,
    spelling: str,
    imports: tuple[tuple[str, str], ...],
) -> None:
    """Write ``spelling`` as a parameter's annotation, importing its names.

    Args:
        module (CommentedModule): Module to modify.
        index (int): Position of the statement that will use the annotation.
        parameter (arg): Parameter node to annotate.
        spelling (str): Annotation source.
        imports (tuple[tuple[str, str], ...]): ``(module, name)`` pairs the
            spelling needs.

    """
    names: dict[str, str] = {}
    for origin, proto in imports:
        size: int = len(module.body)
        local: str = insert_import(
            module=module,
            source=origin,
            name=proto,
            before=index,
        )
        index += len(module.body) - size
        names[proto] = local
    expression: expr = annotation_expression(
        node=parse(source=spelling, mode="eval").body,
        names=names,
        symbols=module.semantic.symbols,
    )
    ensure_names(module=module, expression=expression, before=index)
    parameter.annotation = expression


def _protocol_index(
    *,
    module: Module,
    function: FunctionDef | AsyncFunctionDef,
    placement: str,
) -> tuple[list[stmt], int]:
    """Choose the body list and index a new protocol class lands at.

    ``"module"`` keeps today's position: directly before the top-level
    statement that encloses the def. ``"function"`` puts the class directly
    above the def inside whichever body holds it — a class body for a
    method — and never lands inside a function body.

    Args:
        module (Module): Module to modify.
        function (FunctionDef | AsyncFunctionDef): Def the protocol annotates.
        placement (str): ``"module"`` or ``"function"``.

    Returns:
        tuple[list[stmt], int]: The statement list and insertion index.

    """
    if placement != "function":
        return module.body, _ancestor_index(module=module, node=function)
    parents: dict[AST, AST] = {
        child: parent
        for parent in walk(node=module)
        for child in iter_child_nodes(node=parent)
    }
    node: AST = function
    owner: AST | None = parents.get(node)
    while owner is not None:
        if isinstance(owner, Module):
            return module.body, owner.body.index(cast(typ="stmt", val=node))
        if isinstance(owner, ClassDef):
            return owner.body, owner.body.index(cast(typ="stmt", val=node))
        node, owner = owner, parents.get(owner)
    return module.body, _ancestor_index(module=module, node=function)


def _emit_protocol(
    *,
    module: Module,
    function: FunctionDef | AsyncFunctionDef,
    parameter: str,
    usage: StructuralUsage,
    facts: ModuleFacts,
) -> tuple[str, bool] | None:
    """Insert the protocol class for a usage, honouring placement.

    Args:
        module (Module): Module to modify.
        function (FunctionDef | AsyncFunctionDef): Function the usage was
            derived from.
        parameter (str): Parameter name.
        usage (StructuralUsage): Required members.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        tuple[str, bool] | None:
            ``(class name, quote)`` — ``quote`` is ``True`` when the class
        landed under ``if TYPE_CHECKING:`` and the annotation must be a
            string — or ``None`` when the class could not be rendered.

    """
    taken: SetStr = _module_names(module=module)
    base: str = ProtocolGrammar().name_for_members(
        members=tuple(member.name for member in usage.members),
    )
    name: str = base
    suffix: int = 2
    while name in taken:
        name = f"{base}{suffix}"
        suffix += 1
    referenced: bool = protocol_isinstanced(module=module, names={name})
    type_checking: bool = (
        facts.protocol_placement == "type-checking" and not referenced
    )
    runtime: bool = facts.runtime_protocols and referenced
    match parse(
        source=protocol_source(
            name=name,
            function=function.name,
            parameter=parameter,
            usage=usage,
        ),
    ).body:
        case [ClassDef() as candidate]:
            pass
        case _:
            return None
    document_protocol(node=candidate, overwrite=True)
    reused: str | None = _existing_protocol(module=module, candidate=candidate)
    if reused is not None:
        return reused, False
    index: int = _ancestor_index(module=module, node=function)
    local: str = insert_import(
        module=module,
        source="typing",
        name="Protocol",
        before=index,
    )
    candidate.bases = [Name(id=local, ctx=Load())]
    if runtime:
        candidate.decorator_list = [
            Name(
                id=insert_import(
                    module=module,
                    source="typing",
                    name="runtime_checkable",
                    before=index,
                ),
                ctx=Load(),
            ),
        ]
    _strip_locations(node=candidate)
    if type_checking:
        local_checking: str = insert_import(
            module=module,
            source="typing",
            name="TYPE_CHECKING",
            before=index,
        )
        module.body.insert(
            _ancestor_index(module=module, node=function),
            If(
                test=Name(id=local_checking, ctx=Load()),
                body=[candidate],
                orelse=[],
            ),
        )
    else:
        body, position = _protocol_index(
            module=module,
            function=function,
            placement=facts.protocol_placement,
        )
        body.insert(position, candidate)
    return name, type_checking


def _is_plain_typevar(*, statement: stmt, name: str) -> bool:
    """Tell whether a statement is ``NAME = TypeVar("NAME")``.

    Args:
        statement (stmt): Top-level statement.
        name (str): Expected variable name.

    Returns:
        bool: ``True`` for an unconstrained, unbounded, invariant declaration.

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
        module (Module): Module to search.
        node (AST): Node inside a top-level statement.

    Returns:
        int: The statement's index in the module body.

    """
    return next(
        position
        for position, statement in enumerate(iterable=module.body)
        if any(child is node for child in walk(node=statement))
    )


def _class_variables(*, module: Module, function: AST) -> SetStr:
    """Collect names the enclosing classes already use as type parameters.

    Args:
        module (Module): Module to search.
        function (AST): Function whose enclosing classes are inspected.

    Returns:
        SetStr:
            Names in base lists, class keywords and PEP 695 type parameters.

    """
    names: SetStr = set()
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
    forbidden: SetStr,
) -> tuple[str, bool]:
    """Choose the type variable to use, reusing a plain declaration.

    Args:
        module (Module): Module to search.
        before (int): Declarations at or after this body index cannot be used.
        forbidden (SetStr): Names the enclosing classes already use as
            parameters.

    Returns:
        tuple[str, bool]: The name and whether it must be declared.

    """
    taken: SetStr = _module_names(module=module)
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


def _fresh_typevar_name(
    *,
    module: Module,
    before: int,
    forbidden: SetStr,
) -> str:
    """Choose an undeclared type variable name.

    Unlike :func:`_typevar_name` this never reuses an existing plain
    ``TypeVar`` declaration, so constrained and bound shapes always get a
    fresh name.

    Args:
        module (Module): Module to search.
        before (int): Unused; kept for signature symmetry.
        forbidden (SetStr): Names the enclosing classes already use as
            parameters.

    Returns:
        str: The first free ``T``, ``T2``, ... name.

    """
    del before
    taken: SetStr = _module_names(module=module)
    suffix: int = 1
    while True:
        name: str = "T" if suffix == 1 else f"T{suffix}"
        if name in forbidden or name in taken:
            suffix += 1
            continue
        return name


def annotation_expression(
    *,
    node: expr,
    names: Mapping[str, str],
    symbols: SymbolRegistry,
) -> expr:
    """Bind an existing type expression to native symbol identities.

    Args:
        node (expr): Existing native annotation; neither parsed nor cloned
            here.
        names (Mapping[str, str]): Canonical import slots and their selected
            local spellings.
        symbols (SymbolRegistry): Registry of the authoritative module's native
            symbols.

    Returns:
        expr: Native expression with bound Name
            nodes; no text replacement occurs.

    Raises:
        ValueError: A requested import binding is absent from the module.

    """
    aliases: dict[str, Symbol] = {}
    for canonical, local in names.items():
        if canonical == local:
            continue
        symbol: Symbol | None = symbols.resolve(name=local)
        if symbol is None:
            msg: str = f"Generated annotation import is not bound: {local}"
            raise ValueError(msg)
        aliases[canonical] = symbol
    if aliases:
        symbols.bind_references(
            bindings={
                reference: aliases[reference.id].id
                for reference in TypeExpressionCodec.name_nodes(node=node)
                if reference.id in aliases
            },
        )
    return node


def _insert_bound_protocol(
    *,
    module: Module,
    function: FunctionDef | AsyncFunctionDef,
    parameter: str,
    usage: StructuralUsage,
    facts: ModuleFacts,
) -> str | None:
    """Insert the protocol class a bound TypeVar refers to.

    Args:
        module (Module): Module to modify.
        function (FunctionDef | AsyncFunctionDef): Function the bound was
            derived from.
        parameter (str): Parameter name.
        usage (StructuralUsage): Required members.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        str | None: The protocol class name (existing or new), or ``None``.

    """
    emitted: tuple[str, bool] | None = _emit_protocol(
        module=module,
        function=function,
        parameter=parameter,
        usage=usage,
        facts=replace(facts, protocol_placement="module")
        if facts.protocol_placement == "type-checking"
        else facts,
    )
    return None if emitted is None else emitted[0]


def synthesize_typevar(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a pass-through parameter and its return with a type variable.

    Depending on how the parameter is used this emits a plain ``TypeVar``,
    a constrained one, a ``bound=`` protocol TypeVar, element pass-through
    container annotations, or ``Self`` for receiver returns. Declarations
    are inserted before the top-level statement that contains the function.

    Args:
        subject (Subject): Parameter subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

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
    receiver: tuple[str, bool] | None = receiver_info(
        module=module,
        function=function,
    )
    probe: TypeVarPlan | None = typevar_plan(
        function=function,
        parameter=parameter.arg,
        variable="T",
        counts=facts.binding_counts,
        receiver=receiver,
    )
    if probe is None:
        forwarding: tuple[str, str] | None = forwarding_decorator(
            function=function,
        )
        if (
            forwarding is not None
            and forwarding[0] == parameter.arg
            and _synthesize_paramspec(
                function=function,
                parameter=parameter,
                module=module,
                target=facts.target,
                forbidden=_class_variables(module=module, function=function)
                | set(function_scope_names(function=function)),
            )
        ):
            return
        _synthesize_multi(
            request=_MultiRequest(
                function=function,
                module=module,
                receiver=receiver,
                forbidden=_class_variables(module=module, function=function)
                | set(function_scope_names(function=function)),
                target=facts.target,
                counts=facts.binding_counts,
                subject=parameter,
            ),
        )
        return
    request: _TypevarRequest = _TypevarRequest(
        module=module,
        function=function,
        parameter=parameter,
        receiver=receiver,
        counts=facts.binding_counts,
        facts=facts,
    )
    resolved: tuple[str, bool, TypeVarPlan, int] | None = _resolve_typevar(
        request=request,
        probe=probe,
    )
    if resolved is None:
        return
    name, declare, plan, index = resolved
    if not _commit_typevar_plan(
        request=request,
        name=name,
        declare=declare,
        plan=plan,
        index=index,
    ):
        return


@dataclass(frozen=True, slots=True)
class _TypevarRequest:
    """Shared context for resolving and committing a type variable plan.

    Attributes:
        module (Module): Module to modify.
        function (FunctionDef | AsyncFunctionDef): Function that owns the
            parameter.
        parameter (arg): Parameter node.
        receiver (tuple[str, bool] | None): ``(name, is_classmethod)`` when the
            function is a method.
        counts (Mapping[str, int]): Module binding counts.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """

    module: Module
    function: FunctionDef | AsyncFunctionDef
    parameter: arg
    receiver: tuple[str, bool] | None
    counts: Mapping[str, int]
    facts: ModuleFacts


def _resolve_typevar(
    *,
    request: _TypevarRequest,
    probe: TypeVarPlan,
) -> tuple[str, bool, TypeVarPlan, int] | None:
    """Pick the type variable name and re-probe the plan with it.

    Args:
        request (_TypevarRequest): Module, function, parameter and binding
            context.
        probe (TypeVarPlan): Initial plan probed with the placeholder name.

    Returns:
        tuple[str, bool, TypeVarPlan, int] | None:
            ``(name, declare, plan, insertion index)`` or ``None``.

    """
    module: Module = request.module
    function: FunctionDef | AsyncFunctionDef = request.function
    index: int = _ancestor_index(module=module, node=function)
    forbidden: SetStr = _class_variables(module=module, function=function)
    if not probe.variable:
        name: str = ""
        declare: bool = False
    elif probe.constraints or probe.bound is not None:
        name = _fresh_typevar_name(
            module=module,
            before=index,
            forbidden=forbidden,
        )
        declare = True
    else:
        name, declare = _typevar_name(
            module=module,
            before=index,
            forbidden=forbidden,
        )
    plan: TypeVarPlan | None = probe
    if probe.variable and name != "T":
        plan = typevar_plan(
            function=function,
            parameter=request.parameter.arg,
            variable=name,
            counts=request.counts,
            receiver=request.receiver,
        )
    if plan is None:
        return None
    return name, declare, plan, index


def _declare_typevar(
    *,
    request: _TypevarRequest,
    name: str,
    plan: TypeVarPlan,
    protocol: str | None,
    local: Mapping[str, str],
) -> bool:
    """Insert the ``name = TypeVar(...)`` declaration before the function.

    Args:
        request (_TypevarRequest): Module and function context.
        name (str): Type variable name.
        plan (TypeVarPlan): Resolved plan (constraints and bound).
        protocol (str | None): Bound protocol name, if any.
        local (Mapping[str, str]): Canonical to local import names.

    Returns:
        bool: ``False`` when the declaration source did not parse as expected.

    """
    module: Module = request.module
    function: FunctionDef | AsyncFunctionDef = request.function
    arguments: str = f'"{name}"'
    if plan.constraints:
        arguments += "".join(f", {item}" for item in plan.constraints)
    if protocol is not None:
        arguments += f", bound={protocol}"
    match parse(source=f"{name} = {local['TypeVar']}({arguments})").body:
        case [Assign() as declaration]:
            _strip_locations(node=declaration)
            module.body.insert(
                _ancestor_index(module=module, node=function),
                declaration,
            )
            return True
        case _:
            return False


def _commit_typevar_plan(
    *,
    request: _TypevarRequest,
    name: str,
    declare: bool,
    plan: TypeVarPlan,
    index: int,
) -> bool:
    """Apply a resolved type variable plan to the module.

    Args:
        request (_TypevarRequest): Module, function, parameter and binding
            context.
        name (str): Type variable name (empty for nameless plans).
        declare (bool): Whether a new ``TypeVar`` declaration is required.
        plan (TypeVarPlan): Resolved plan.
        index (int): Insertion index for imports and declarations.

    Returns:
        bool: ``False`` when a required step failed.

    """
    module: Module = request.module
    function: FunctionDef | AsyncFunctionDef = request.function
    needed: list[tuple[str, str]] = [*plan.imports]
    if plan.variable:
        needed.append(("typing", "TypeVar"))
    local: dict[str, str] = {}
    for source_name, import_name in needed:
        local[import_name] = insert_import(
            module=module,
            source=source_name,
            name=import_name,
            before=index,
        )
    protocol: str | None = None
    if plan.bound is not None:
        protocol = _insert_bound_protocol(
            module=module,
            function=function,
            parameter=request.parameter.arg,
            usage=plan.bound,
            facts=request.facts,
        )
        if protocol is None:
            return False
    if (
        plan.variable
        and declare
        and not _declare_typevar(
            request=request,
            name=name,
            plan=plan,
            protocol=protocol,
            local=local,
        )
    ):
        return False
    if plan.annotate and plan.param is not None:
        request.parameter.annotation = annotation_expression(
            node=parse(source=plan.param, mode="eval").body,
            names=local,
            symbols=request.facts.module.semantic.symbols,
        )
    function.returns = annotation_expression(
        node=parse(source=plan.returns, mode="eval").body,
        names=local,
        symbols=request.facts.module.semantic.symbols,
    )
    return True


def _allocate_typevars(
    *,
    involved: tuple[str, ...],
    taken: SetStr,
) -> list[str]:
    """Allocate fresh ``T``, ``T2``, ... names for involved parameters.

    Args:
        involved (tuple[str, ...]): Parameter names needing a type variable.
        taken (SetStr): Names already unavailable.

    Returns:
        list[str]: One fresh name per involved parameter, in order.

    """
    names: list[str] = []
    suffix: int = 1
    for _name in involved:
        while True:
            candidate: str = "T" if suffix == 1 else f"T{suffix}"
            suffix += 1
            if candidate not in taken and candidate not in names:
                names.append(candidate)
                break
    return names


def _declare_typevars(
    *,
    module: Module,
    function: FunctionDef | AsyncFunctionDef,
    names: list[str],
    factory: str,
) -> bool:
    """Insert ``name = TypeVar("name")`` declarations before the function.

    Args:
        module (Module): Module to modify.
        function (FunctionDef | AsyncFunctionDef): Function the declarations
            precede.
        names (list[str]): Type variable names to declare.
        factory (str): Local name of ``TypeVar``.

    Returns:
        bool: ``False`` when a declaration source did not parse as expected.

    """
    for variable in names:
        match parse(source=f'{variable} = {factory}("{variable}")').body:
            case [Assign() as declaration]:
                _strip_locations(node=declaration)
                module.body.insert(
                    _ancestor_index(module=module, node=function),
                    declaration,
                )
            case _:
                return False
    return True


def _synthesize_paramspec(
    *,
    function: FunctionDef | AsyncFunctionDef,
    parameter: arg,
    module: Module,
    target: PythonTarget,
    forbidden: SetStr,
) -> bool:
    """Annotate a forwarding decorator with ``ParamSpec``.

    ``def deco(f):...; def wrapper(*a, **k): return f(*a, **k); return
    wrapper`` preserves the wrapped signature, so ``f`` is
    ``Callable[P, R]`` and ``deco`` returns ``Callable[P, R]``.

    Args:
        function (FunctionDef | AsyncFunctionDef): Decorator function.
        parameter (arg): Forwarded parameter node.
        module (Module): Module to modify.
        target (PythonTarget): Oldest Python version emitted code must run on.
        forbidden (SetStr): Names the function scope or enclosing classes
            reserve.

    Returns:
        bool: ``False`` when the target predates PEP 612 or emission failed.

    """
    if not target.param_spec:
        return False
    index: int = _ancestor_index(module=module, node=function)
    taken: SetStr = _module_names(module=module) | forbidden
    param_name: str = "P"
    counter: int = 2
    while param_name in taken:
        param_name = f"P{counter}"
        counter += 1
    result_name: str = "R"
    counter = 2
    while result_name in taken or result_name == param_name:
        result_name = f"R{counter}"
        counter += 1
    spec_factory: str = insert_import(
        module=module,
        source="typing",
        name="ParamSpec",
        before=index,
    )
    var_factory: str = insert_import(
        module=module,
        source="typing",
        name="TypeVar",
        before=index,
    )
    match parse(
        source=(
            f'{param_name} = {spec_factory}("{param_name}")\n'
            f'{result_name} = {var_factory}("{result_name}")\n'
        ),
    ).body:
        case [Assign() as spec_decl, Assign() as var_decl]:
            pass
        case _:
            return False
    local_callable: str = insert_import(
        module=module,
        source="collections.abc",
        name="Callable",
        before=index,
    )
    index = _ancestor_index(module=module, node=function)
    module.body.insert(index, var_decl)
    module.body.insert(index, spec_decl)
    spelling: str = f"{local_callable}[{param_name}, {result_name}]"
    expression: expr = parse(source=spelling, mode="eval").body
    parameter.annotation = expression
    function.returns = parse(source=spelling, mode="eval").body
    return True


@dataclass(frozen=True, slots=True)
class _MultiRequest:
    """Shared context for multi-parameter type variable synthesis.

    Attributes:
        function (FunctionDef | AsyncFunctionDef): Function that owns the
            parameters.
        module (Module): Module to modify.
        receiver (tuple[str, bool] | None): ``(name, is_classmethod)`` when the
            function is a method.
        forbidden (SetStr): Names the enclosing classes already use as
            parameters.
        target (PythonTarget): Oldest Python version emitted code must run on.
        counts (Mapping[str, int]): Module binding counts.
        subject (arg): Parameter this fix is annotating.

    """

    function: FunctionDef | AsyncFunctionDef
    module: Module
    receiver: tuple[str, bool] | None
    forbidden: SetStr
    target: PythonTarget
    counts: Mapping[str, int]
    subject: arg


def _synthesize_shared(
    *,
    request: _MultiRequest,
    shared: list[str],
) -> bool:
    """Apply one shared type variable when a return proves it.

    Args:
        request (_MultiRequest): Synthesis context; only ``request.subject`` is
            annotated
            so sibling parameters' queued fixes still apply.
        shared (list[str]): Parameter names combined in return expressions.

    Returns:
        bool: ``True`` when the shared annotation was applied.

    """
    module: Module = request.module
    function: FunctionDef | AsyncFunctionDef = request.function
    if request.subject.arg not in shared:
        return False
    index_shared: int = _ancestor_index(module=module, node=function)
    variable: str | None = None
    if function.returns is not None:
        for node in walk(node=function.returns):
            if isinstance(node, Name) and any(
                _is_plain_typevar(statement=statement, name=node.id)
                for statement in module.body[:index_shared]
            ):
                variable = node.id
                break
        if variable is None:
            return False
    else:
        taken_shared: SetStr = _module_names(module=module) | request.forbidden
        variable = _allocate_typevars(
            involved=tuple(shared[:1]),
            taken=taken_shared,
        )[0]
        returns_shared: str | None = shared_return(
            function=function,
            involved=shared,
            variable=variable,
            counts=request.counts,
        )
        if returns_shared is None:
            return False
        factory: str = insert_import(
            module=module,
            source="typing",
            name="TypeVar",
            before=index_shared,
        )
        index_shared = _ancestor_index(module=module, node=function)
        if not _declare_typevars(
            module=module,
            function=function,
            names=[variable],
            factory=factory,
        ):
            return False
        if can_fall_off(body=function.body):
            returns_shared = (
                f"{returns_shared} | None"
                if request.target.union_syntax
                else f"Optional[{returns_shared}]"
            )
        function.returns = _respell_unions(
            expression=parse(source=returns_shared, mode="eval").body,
            target=request.target,
        )
        ensure_names(
            module=module,
            expression=function.returns,
            before=_ancestor_index(module=module, node=function),
        )
    request.subject.annotation = Name(id=variable, ctx=Load())
    return True


def _synthesize_multi(*, request: _MultiRequest) -> None:
    """Annotate several parameters sharing one container return.

    Args:
        request (_MultiRequest): Synthesis context.

    """
    function: FunctionDef | AsyncFunctionDef = request.function
    module: Module = request.module
    candidates: dict[str, arg] = candidate_params(
        function=function,
        receiver=request.receiver,
    )
    pool: dict[str, arg] = candidate_params(
        function=function,
        receiver=request.receiver,
        include_annotated=True,
    )
    if len(pool) <= 1:
        return
    shared: list[str] | None = shared_parameters(
        function=function,
        candidates=pool,
    )
    if shared is not None and _synthesize_shared(
        request=request,
        shared=shared,
    ):
        return
    if len(candidates) <= 1:
        return
    shaped: tuple[tuple[str, ...], str] | None = multi_return(
        function=function,
        candidates={name: name for name in candidates},
    )
    if shaped is None:
        return
    involved: tuple[str, ...] = shaped[0]
    taken: SetStr = _module_names(module=module) | request.forbidden
    names: list[str] = _allocate_typevars(involved=involved, taken=taken)
    variables: dict[str, str] = dict(zip(involved, names, strict=True))
    final: tuple[tuple[str, ...], str] | None = multi_return(
        function=function,
        candidates={
            **{name: name for name in candidates},
            **variables,
        },
    )
    if final is None:
        return
    involved, returns_source = final
    index: int = _ancestor_index(module=module, node=function)
    factory_final: str = insert_import(
        module=module,
        source="typing",
        name="TypeVar",
        before=index,
    )
    if not _declare_typevars(
        module=module,
        function=function,
        names=names,
        factory=factory_final,
    ):
        return
    for name in involved:
        parameter: arg = candidates[name]
        parameter.annotation = Name(id=variables[name], ctx=Load())
    if can_fall_off(body=function.body):
        returns_source: str = (
            f"{returns_source} | None"
            if request.target.union_syntax
            else f"Optional[{returns_source}]"
        )
    function.returns = _respell_unions(
        expression=parse(source=returns_source, mode="eval").body,
        target=request.target,
    )
    ensure_names(
        module=module,
        expression=function.returns,
        before=_ancestor_index(module=module, node=function),
    )


def synthesize_self(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a receiver-returning method with ``Self``.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            pass
        case _:
            return
    if not facts.target.self_type:
        return
    module: Module = facts.module
    receiver: tuple[str, bool] | None = receiver_info(
        module=module,
        function=function,
    )
    if receiver is None:
        return
    plan: TypeVarPlan | None = typevar_plan(
        function=function,
        parameter=receiver[0],
        variable="T",
        counts=facts.binding_counts,
        receiver=receiver,
    )
    if plan is None or plan.variable:
        return
    index: int = _ancestor_index(module=module, node=function)
    local: str = insert_import(
        module=module,
        source="typing",
        name="Self",
        before=index,
    )
    function.returns = annotation_expression(
        node=parse(source=plan.returns, mode="eval").body,
        names={"Self": local},
        symbols=facts.module.semantic.symbols,
    )


def use_type_statement(subject: Subject, facts: ModuleFacts) -> None:
    """Migrate a type-only legacy alias without adding a variable hint.

    Args:
        subject (Subject): Original assignment binding.
        facts (ModuleFacts): Shared declaration cache and target version.

    """
    if facts.target.type_statement:
        facts.aliases.apply(module=facts.module, statement=subject.statement)


@final
class Appliers:
    """Group the registered appliers.

    Attributes:
        table (Final[Mapping[str, Applier]]): Applier function for every key in
            the registries.

    """

    table: Final[Mapping[str, Applier]] = {
        "typing.use-type-statement": use_type_statement,
        "typing.add-final": add_final,
        "structure.group-constants": group_constant,
        "structure.snake-constant": snake_constant,
        "whitespace.wrap-comments": wrap_comments,
        "calls.add-keywords": add_keywords,
        "calls.discard-result": discard_result,
        "typing.add-none-return": add_none_return,
        "typing.add-noreturn": add_noreturn,
        "typing.add-inferred-annotation": add_inferred_annotation,
        "typing.add-attribute-annotation": add_attribute_annotation,
        "typing.add-variable-annotation": add_variable_annotation,
        "typing.synthesize-protocol": synthesize_protocol,
        "typing.synthesize-typevar": synthesize_typevar,
        "typing.synthesize-self": synthesize_self,
        "docs.add-parameter-entries": add_entries,
        "docs.add-generator-results": add_generator_results,
        "docs.add-types": add_types,
        "docs.heal-parameter-rename": heal_rename,
        "docs.remove-stale-entries": remove_entries,
        "docs.tidy-docstring": tidy,
    }
