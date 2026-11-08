"""Edit appliers: tree-level rewrites that fixes are made of."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    BitOr,
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
    Tuple,
    arg,
    copy_location,
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
from dataclasses import dataclass
from re import sub as re_sub
from typing import TYPE_CHECKING, Final, cast, final

from astart._graph.dispatch import LowercaseTransformer
from astart.rules.docs_fixes import (
    add_entries,
    heal_rename,
    remove_entries,
    tidy,
)
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
)
from astart.rules.hints import Hint, HintBasis, returns_nothing
from astart.rules.imports import ensure_names, insert_import, module_classes
from astart.rules.protocols import (
    StructuralUsage,
    protocol_source,
    structural_usage,
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
    multi_return,
    receiver_info,
    typevar_plan,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from astart import BoundCall
    from astart.project.versions import PythonTarget
    from astart.rules.facts import Applier, ModuleFacts, Subject
    from astart.rules.protocols import StructuralUsage
type NodeAttributes = dict[str, AST | list[AST] | int | str | None]


@final
class _UnionRewrite(LowercaseTransformer):
    """Rewrite ``X | Y`` union syntax as ``Union[X, Y]`` in annotations."""

    def visit_binop(self, node: BinOp) -> expr:
        """Flatten one ``|`` chain and rebuild it as ``Union[...]``.

        Args:
            node: The binary operation node.

        Returns:
            The replacement ``Union`` subscript, or the node with its
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
        node: The expression that may head a union chain.

    Returns:
        The union's operands, or ``[node]`` itself when not a union.

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
        expression: Parsed annotation expression.
        target: Oldest Python version emitted code must run on.

    Returns:
        The expression, with unions respelled as ``Union[...]`` when
        needed.

    """
    if target.union_syntax:
        return expression
    return cast(typ="expr", val=_UnionRewrite().visit(node=expression))


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


def group_constant(subject: Subject, facts: ModuleFacts) -> None:
    """Move a ``Final`` module constant into the ``Constants`` class.

    The class is created, after the leading imports, when the module has no
    binding of that name at all.

    Args:
        subject: Annotated assignment subject.
        facts: Resolved imports and the parsed module.

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


def add_attribute_annotation(subject: Subject, facts: ModuleFacts) -> None:
    """Turn ``self.x = value`` into ``self.x: T = value``.

    The statement keeps its identity, so comments and layout survive.

    Args:
        subject: Attribute assignment subject.
        facts: Resolved imports, parsed module and lazily computed hints.

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
        subject: Assignment subject.
        facts: Resolved imports, parsed module and negotiated variables.

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
        env=scope_types(
            function=function,
            counts=facts.binding_counts,
            constants=module_constants(
                module=facts.module,
                counts=facts.binding_counts,
            ),
        ),
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


def _fresh_typevar_name(
    *,
    module: Module,
    before: int,
    forbidden: set[str],
) -> str:
    """Choose an undeclared type variable name.

    Unlike :func:`_typevar_name` this never reuses an existing plain
    ``TypeVar`` declaration, so constrained and bound shapes always get a
    fresh name.

    Args:
        module: Module to search.
        before: Unused; kept for signature symmetry.
        forbidden: Names the enclosing classes already use as parameters.

    Returns:
        The first free ``T``, ``T2``, ... name.

    """
    del before
    taken: set[str] = _module_names(module=module)
    suffix: int = 1
    while True:
        name: str = "T" if suffix == 1 else f"T{suffix}"
        if name in forbidden or name in taken:
            suffix += 1
            continue
        return name


def _localize(*, source: str, names: Mapping[str, str]) -> str:
    """Substitute imported local names into an annotation source.

    Args:
        source: Annotation source spelling canonical import names.
        names: Canonical name to local (possibly aliased) name.

    Returns:
        The source with aliases applied.

    """
    for canonical, local in names.items():
        if canonical != local:
            source = re_sub(
                pattern=rf"\b{canonical}\b",
                repl=local,
                string=source,
            )
    return source


def _insert_bound_protocol(
    *,
    module: Module,
    function: FunctionDef | AsyncFunctionDef,
    parameter: str,
    usage: StructuralUsage,
) -> str | None:
    """Insert the protocol class a bound TypeVar refers to.

    Args:
        module: Module to modify.
        function: Function the bound was derived from.
        parameter: Parameter name.
        usage: Required members.

    Returns:
        The protocol class name (existing or new), or ``None``.

    """
    taken: set[str] = _module_names(module=module)
    base: str = (
        f"{_pascal(text=function.name)}{_pascal(text=parameter)}Protocol"
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
            parameter=parameter,
            usage=usage,
        ),
    ).body:
        case [ClassDef() as candidate]:
            pass
        case _:
            return None
    reused: str | None = _existing_protocol(module=module, candidate=candidate)
    if reused is not None:
        return reused
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
    return name


def synthesize_typevar(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a pass-through parameter and its return with a type variable.

    Depending on how the parameter is used this emits a plain ``TypeVar``,
    a constrained one, a ``bound=`` protocol TypeVar, element pass-through
    container annotations, or ``Self`` for receiver returns. Declarations
    are inserted before the top-level statement that contains the function.

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
        _synthesize_multi(
            function=function,
            module=module,
            receiver=receiver,
            forbidden=_class_variables(module=module, function=function),
            target=facts.target,
        )
        return
    request: _TypevarRequest = _TypevarRequest(
        module=module,
        function=function,
        parameter=parameter,
        receiver=receiver,
        counts=facts.binding_counts,
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
        module: Module to modify.
        function: Function that owns the parameter.
        parameter: Parameter node.
        receiver: ``(name, is_classmethod)`` when the function is a method.
        counts: Module binding counts.

    """

    module: Module
    function: FunctionDef | AsyncFunctionDef
    parameter: arg
    receiver: tuple[str, bool] | None
    counts: Mapping[str, int]


def _resolve_typevar(
    *,
    request: _TypevarRequest,
    probe: TypeVarPlan,
) -> tuple[str, bool, TypeVarPlan, int] | None:
    """Pick the type variable name and re-probe the plan with it.

    Args:
        request: Module, function, parameter and binding context.
        probe: Initial plan probed with the placeholder name.

    Returns:
        ``(name, declare, plan, insertion index)`` or ``None``.

    """
    module: Module = request.module
    function: FunctionDef | AsyncFunctionDef = request.function
    index: int = _ancestor_index(module=module, node=function)
    forbidden: set[str] = _class_variables(module=module, function=function)
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
        request: Module and function context.
        name: Type variable name.
        plan: Resolved plan (constraints and bound).
        protocol: Bound protocol name, if any.
        local: Canonical to local import names.

    Returns:
        ``False`` when the declaration source did not parse as expected.

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
        request: Module, function, parameter and binding context.
        name: Type variable name (empty for nameless plans).
        declare: Whether a new ``TypeVar`` declaration is required.
        plan: Resolved plan.
        index: Insertion index for imports and declarations.

    Returns:
        ``False`` when a required step failed.

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
        request.parameter.annotation = parse(
            source=_localize(source=plan.param, names=local),
            mode="eval",
        ).body
    function.returns = parse(
        source=_localize(source=plan.returns, names=local),
        mode="eval",
    ).body
    return True


def _allocate_typevars(
    *,
    involved: tuple[str, ...],
    taken: set[str],
) -> list[str]:
    """Allocate fresh ``T``, ``T2``, ... names for involved parameters.

    Args:
        involved: Parameter names needing a type variable.
        taken: Names already unavailable.

    Returns:
        One fresh name per involved parameter, in order.

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
        module: Module to modify.
        function: Function the declarations precede.
        names: Type variable names to declare.
        factory: Local name of ``TypeVar``.

    Returns:
        ``False`` when a declaration source did not parse as expected.

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


def _synthesize_multi(
    *,
    function: FunctionDef | AsyncFunctionDef,
    module: Module,
    receiver: tuple[str, bool] | None,
    forbidden: set[str],
    target: PythonTarget,
) -> None:
    """Annotate several parameters sharing one container return.

    Args:
        function: Function that owns the parameters.
        module: Module to modify.
        receiver: ``(name, is_classmethod)`` when the function is a method.
        forbidden: Names the enclosing classes already use as parameters.
        target: Oldest Python version emitted code must run on.

    """
    candidates: dict[str, arg] = candidate_params(
        function=function,
        receiver=receiver,
    )
    if len(candidates) <= 1:
        return
    shaped: tuple[tuple[str, ...], str] | None = multi_return(
        function=function,
        candidates={name: name for name in candidates},
    )
    if shaped is None:
        return
    involved: tuple[str, ...] = shaped[0]
    taken: set[str] = _module_names(module=module) | forbidden
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
    factory: str = insert_import(
        module=module,
        source="typing",
        name="TypeVar",
        before=index,
    )
    if not _declare_typevars(
        module=module,
        function=function,
        names=names,
        factory=factory,
    ):
        return
    for name in involved:
        parameter: arg = candidates[name]
        parameter.annotation = Name(id=variables[name], ctx=Load())
    if can_fall_off(body=function.body):
        returns_source: str = (
            f"{returns_source} | None"
            if target.union_syntax
            else f"Optional[{returns_source}]"
        )
    function.returns = _respell_unions(
        expression=parse(source=returns_source, mode="eval").body,
        target=target,
    )
    ensure_names(
        module=module,
        expression=function.returns,
        before=_ancestor_index(module=module, node=function),
    )


def synthesize_self(subject: Subject, facts: ModuleFacts) -> None:
    """Annotate a receiver-returning method with ``Self``.

    Args:
        subject: Function subject.
        facts: Resolved imports and the parsed module.

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
    function.returns = parse(
        source=_localize(source=plan.returns, names={"Self": local}),
        mode="eval",
    ).body


@final
class Appliers:
    """Group the registered appliers.

    Attributes:
        table: Applier function for every key in the registries.

    """

    table: Final[Mapping[str, Applier]] = {
        "typing.add-final": add_final,
        "structure.group-constants": group_constant,
        "calls.add-keywords": add_keywords,
        "typing.add-none-return": add_none_return,
        "typing.add-noreturn": add_noreturn,
        "typing.add-inferred-annotation": add_inferred_annotation,
        "typing.add-attribute-annotation": add_attribute_annotation,
        "typing.add-variable-annotation": add_variable_annotation,
        "typing.synthesize-protocol": synthesize_protocol,
        "typing.synthesize-typevar": synthesize_typevar,
        "typing.synthesize-self": synthesize_self,
        "docs.add-parameter-entries": add_entries,
        "docs.heal-parameter-rename": heal_rename,
        "docs.remove-stale-entries": remove_entries,
        "docs.tidy-docstring": tidy,
    }
