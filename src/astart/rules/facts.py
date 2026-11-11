"""Subjects, fact providers and registries for the reference engine."""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    Await,
    Call,
    ClassDef,
    Constant,
    Expr,
    Expression,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    Starred,
    Subscript,
    arg,
    arguments,
    expr,
    get_docstring,
    iter_child_nodes,
    parse,
    unparse,
    walk,
)
from dataclasses import dataclass, field, replace
from functools import partial
from typing import TYPE_CHECKING, Final, cast, final

from astart.docstrings.core import Constants as DocstringConstants
from astart.docstrings.fixes import (
    generator_needs_results,
    is_editable,
    is_missing_public,
    is_untidy,
    stale_count,
    stale_evidence,
    stubs_wanted,
    triple_quoted_owners,
)
from astart.docstrings.types import needs_types
from astart.project.versions import resolve_target
from astart.rules.alias_declarations import AliasDeclarations
from astart.rules.engine_hints import LazyConversion, engine_hints
from astart.rules.grouping import (
    creatable,
    find_group,
    renameable,
    snake_name,
)
from astart.rules.hints import (
    HintBasis,
    HintCache,
    LazyHints,
    is_declaration,
    returns_nothing,
)
from astart.rules.library_calls import library_binding
from astart.rules.negotiation.supplement import negotiated_hints
from astart.rules.negotiation.variables import LazyVariables
from astart.rules.predicate import FactValue
from astart.rules.protocol_verify import call_site_objection
from astart.rules.protocols import Constants as ProtocolConstants
from astart.rules.protocols import parameter_has_default, structural_usage
from astart.rules.provable import (
    mark_noreturn_calls,
    module_constants,
    never_returns,
    scope_types,
)
from astart.rules.registry import FactSpec, Registries
from astart.rules.resolve import CallBindings, binding_counts
from astart.rules.strings_normalize import normalize_strings
from astart.rules.typevars import (
    TypeVarPlan,
    candidate_params,
    forwarding_decorator,
    multi_return,
    receiver_info,
    shared_parameters,
    shared_return,
    typevar_plan,
)
from astart.rules.vocabulary import Cost
from astart.rules.whitespace_rules import (
    comment_wrap_plans,
    count_blank_line_runs,
    count_trailing_space_lines,
)
from astart.semantic import ArgumentOrigin, ParameterKind

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from astart import BoundCall, CommentedModule
    from astart.project.libraries import LibraryIndex
    from astart.project.versions import PythonTarget
    from astart.rules.hints import Hint, HintIndex, Key
    from astart.rules.jsonvalue import JsonValue
    from astart.rules.project_bridge import ProjectView
    from astart.rules.protocols import StructuralUsage
type FactProvider = Callable[[Subject, ModuleFacts], FactValue]
type Applier = Callable[[Subject, ModuleFacts], None]
type EvidenceProvider = Callable[[Subject, ModuleFacts], JsonValue]


@final
@dataclass(frozen=True, slots=True)
class Subject:
    """One thing a rule inspects.

    Attributes:
        kind (str): Node kind, or ``Annotation`` for annotation expressions.
        node (AST): Syntax node the rule reports on.
        path (str): Dotted qualified path used for the finding fingerprint.
        scope (str): Enclosing scope kind: ``module`` , ``class`` or
            ``function``.
        name (str): Name of the bound or annotated thing.
        statement (AST | None): Statement owning the subject, when different
            from node.

    """

    kind: str
    node: AST
    path: str
    scope: str
    name: str
    statement: AST | None = None


def _no_owners() -> dict[int, ClassDef]:
    """Create an empty method-owner mapping.

    Returns:
        dict[int, ClassDef]: A new empty dictionary.

    """
    return {}


def _is_overload(*, function: AST) -> bool:
    """Tell whether a function is decorated with ``overload``.

    Args:
        function (AST): Candidate node.

    Returns:
        bool: ``True`` for ``@overload`` and ``@typing.overload``.

    """
    if not isinstance(function, (FunctionDef, AsyncFunctionDef)):
        return False
    return any(
        (isinstance(item, Name) and item.id == "overload")
        or (isinstance(item, Attribute) and item.attr == "overload")
        for item in function.decorator_list
    )


def _structure(
    *,
    module: Module,
) -> tuple[dict[int, ClassDef], frozenset[int]]:
    """Find method owners and overload groups in one walk.

    Args:
        module (Module): Parsed module.

    Returns:
        tuple[dict[int, ClassDef], frozenset[int]]: The owning class of every
            method
            and the ids of overloaded functions.

    """
    owners: dict[int, ClassDef] = {}
    overloaded: set[int] = set()
    for node in walk(node=module):
        if isinstance(node, ClassDef):
            owners.update(
                {
                    id(child): node
                    for child in node.body
                    if isinstance(
                        child,
                        (FunctionDef, AsyncFunctionDef),
                    )
                },
            )
        for field_name in ("body", "orelse", "finalbody"):
            block: None | list[AST] = getattr(node, field_name, None)
            if not isinstance(block, list):
                continue
            functions: list[FunctionDef | AsyncFunctionDef] = [
                cast(typ="FunctionDef | AsyncFunctionDef", val=item)
                for item in block
                if isinstance(item, Constants.function_nodes)
            ]
            names: set[str] = {
                item.name for item in functions if _is_overload(function=item)
            }
            overloaded.update(
                id(item) for item in functions if item.name in names
            )
    return (owners, frozenset(overloaded))


def _no_counts() -> dict[str, int]:
    """Create an empty binding-count mapping.

    Returns:
        dict[str, int]: A new empty dictionary.

    """
    return {}


@final
@dataclass(frozen=True, slots=True)
class ModuleFacts:
    """Import information resolved once per module.

    Attributes:
        module (CommentedModule): Parsed module.
        any_names (frozenset[str]): Local names bound to ``typing.Any``.
        final_names (frozenset[str]): Local names bound to ``typing.Final``.
        typing_names (frozenset[str]): Local names bound to the ``typing``
            module.
        hints (LazyHints | None): Lazily computed type hints for the module.
        variables (LazyVariables | None): Lazily negotiated annotations for
            local variables,
            or ``None`` when variable annotation is off.
        calls (CallBindings | None): Trusted call bindings, computed in one
            batch on first use.
        method_owner (Mapping[int, ClassDef]): Class that directly defines each
            method, by node id.
        overloaded (frozenset[int]): Node ids of functions that belong to an
            overload group.
        triple_quoted (frozenset[int]): Node ids of definitions whose docstring
            literal uses
            triple quotes, read before any fix changes the tree.
        create_constants (bool): Whether a missing ``Constants`` class may be
            created for ``Final`` module constants.
        docstring_types (bool): Include annotation types in generated
            documentation.
        stub_docstrings (bool): Whether undocumented public definitions get a
            stub docstring.
        binding_counts (Mapping[str, int]): How many times each name is bound
            in the
            module, ignoring names bound directly in class
            bodies (they do not shadow module-level names).
        project (ProjectView | None): Cross-module view of the project, or
            ``None`` for single-module analysis.
        libraries (LibraryIndex | None): External signature index for callees
            outside the project, or ``None``.
        target (PythonTarget): Oldest Python version emitted code must run on.
        source (str | None): Module source text, or ``None`` when only the tree
            is known.
        runtime_protocols (bool): Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general (bool): Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement (str): Where synthesized protocols land:
            ``"module"``, ``"function"`` or ``"type-checking"``.
        discarded_calls (frozenset[int]): Node ids of calls whose result an
            ``Expr`` statement
            discards, directly or under a single ``await``.
        underscore_used (bool): Whether the name ``_`` appears anywhere in the
            module, so rebinding it for a discarded result is unsafe.
        aliases (AliasDeclarations): Cached, scope-proven legacy alias
            declarations.

    """

    module: CommentedModule
    any_names: frozenset[str] = field(default_factory=frozenset)
    final_names: frozenset[str] = field(default_factory=frozenset)
    typing_names: frozenset[str] = field(default_factory=frozenset)
    binding_counts: Mapping[str, int] = field(default_factory=_no_counts)
    hints: LazyHints | None = None
    variables: LazyVariables | None = None
    calls: CallBindings | None = None
    method_owner: Mapping[int, ClassDef] = field(
        default_factory=_no_owners,
    )
    overloaded: frozenset[int] = field(default_factory=frozenset)
    triple_quoted: frozenset[int] = field(default_factory=frozenset)
    discarded_calls: frozenset[int] = field(default_factory=frozenset)
    underscore_used: bool = False
    create_constants: bool = False
    stub_docstrings: bool = False
    docstring_types: bool = True
    project: ProjectView | None = None
    libraries: LibraryIndex | None = None
    target: PythonTarget = field(default_factory=resolve_target)
    source: str | None = None
    runtime_protocols: bool = False
    accept_general: bool = False
    protocol_placement: str = "module"
    aliases: AliasDeclarations = field(default_factory=AliasDeclarations)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        typing_modules (Final[frozenset[str]]): Grouped module constant.
        node_kinds (Final[frozenset[str]]): Grouped module constant.
        position_attributes (Final[tuple[str, ...]]): Grouped module constant.
        function_nodes (Final[tuple[type[AST], ...]]): Grouped module constant.
        type_constructors (Final[frozenset[str]]): Grouped module constant.
        applier_keys (Final[frozenset[str]]): Grouped module constant.
        immutable_literals (Final[tuple[type, ...]]): Grouped module constant.
        unused_result_none (Final[frozenset[str]]): Declared return names that
            prove a call result is safe to discard.

    """

    typing_modules: Final[frozenset[str]] = frozenset(
        {"typing", "typing_extensions"},
    )
    node_kinds: Final[frozenset[str]] = frozenset(
        {
            "Module",
            "FunctionDef",
            "AsyncFunctionDef",
            "ClassDef",
            "Assign",
            "AnnAssign",
            "Attribute",
            "Call",
            "Annotation",
            "Parameter",
        },
    )
    position_attributes: Final[tuple[str, ...]] = (
        "lineno",
        "col_offset",
        "end_lineno",
        "end_col_offset",
    )
    function_nodes: Final[tuple[type[AST], ...]] = (
        FunctionDef,
        AsyncFunctionDef,
    )
    type_constructors: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType", "TypeAliasType"},
    )
    applier_keys: Final[frozenset[str]] = frozenset(
        {
            "typing.add-final",
            "typing.use-type-statement",
            "structure.group-constants",
            "structure.snake-constant",
            "whitespace.wrap-comments",
            "typing.add-attribute-annotation",
            "typing.add-variable-annotation",
            "calls.add-keywords",
            "calls.discard-result",
            "typing.add-none-return",
            "typing.add-noreturn",
            "typing.add-inferred-annotation",
            "typing.synthesize-protocol",
            "typing.synthesize-typevar",
            "typing.synthesize-self",
            "docs.add-parameter-entries",
            "docs.add-generator-results",
            "docs.add-types",
            "docs.heal-parameter-rename",
            "docs.remove-stale-entries",
            "docs.tidy-docstring",
        },
    )
    immutable_literals: Final[tuple[type, ...]] = (
        bool,
        int,
        float,
        str,
        bytes,
    )
    unused_result_none: Final[frozenset[str]] = frozenset(
        {"None", "NoReturn", "Never", "Any", "Unknown"},
    )


@final
@dataclass(frozen=True, slots=True)
class FactsOptions:
    """Optional knobs for :func:`module_facts`.

    Attributes:
        stubs_path (Path | None): Stub directory for type hints, or ``None``.
        source (str | None): Source text of the module, to share hints through
            ``cache``.
        cache (HintCache | None): Shared hint cache, or ``None``.
        create_constants (bool): Whether a missing ``Constants`` class may be
            created to hold ``Final`` module constants.
        docstring_types (bool): Include annotation types in generated
            documentation.
        stub_docstrings (bool): Whether undocumented public definitions get a
            stub docstring.
        annotate_variables (bool): Whether function-local variables get a type
            annotation.
        negotiate (bool): Whether negotiated annotations supplement the hint
            index.
        engine (bool): Conversion mode: the inference engine's annotations fill
            what nothing else decided.
        project (ProjectView | None): Cross-module view of the project, or
            ``None``.
        libraries (LibraryIndex | None): External signature index for callees
            outside the project, or ``None``.
        target (PythonTarget | None): Oldest Python version emitted code must
            run
            on, or ``None`` for the running interpreter.
        runtime_protocols (bool): Whether synthesized protocols used under
            ``isinstance`` get ``@runtime_checkable``.
        accept_general (bool): Whether abstract collection types may replace a
            synthesized ``Protocol`` on read-only container parameters.
        protocol_placement (str): Where synthesized protocols land:
            ``"module"``, ``"function"`` or ``"type-checking"``.

    """

    stubs_path: Path | None = None
    source: str | None = None
    cache: HintCache | None = None
    create_constants: bool = False
    stub_docstrings: bool = False
    docstring_types: bool = True
    annotate_variables: bool = False
    negotiate: bool = False
    engine: bool = False
    project: ProjectView | None = None
    libraries: LibraryIndex | None = None
    target: PythonTarget | None = None
    runtime_protocols: bool = False
    accept_general: bool = False
    protocol_placement: str = "module"


def module_facts(
    *,
    module: CommentedModule,
    options: FactsOptions | None = None,
) -> ModuleFacts:
    """Resolve typing imports of a module.

    Args:
        module (CommentedModule): Parsed module.
        options (FactsOptions | None): Optional knobs, or ``None`` for the
            defaults.

    Returns:
        ModuleFacts: The resolved import information.

    """
    chosen: FactsOptions = options or FactsOptions()
    any_names: set[str] = set()
    final_names: set[str] = set()
    typing_names: set[str] = set()
    discarded_calls: set[int] = set()
    underscore_used: bool = False
    for node in walk(node=module):
        match node:
            case ImportFrom(module=origin, names=aliases) if (
                origin in Constants.typing_modules
            ):
                for alias in aliases:
                    bound: str = alias.asname or alias.name
                    if alias.name == "Any":
                        any_names.add(bound)
                    elif alias.name == "Final":
                        final_names.add(bound)
            case Import(names=aliases):
                typing_names.update(
                    alias.asname or alias.name
                    for alias in aliases
                    if alias.name in Constants.typing_modules
                )
            case Expr(value=Call() as call):
                discarded_calls.add(id(call))
            case Expr(value=Await(value=Call() as call)):
                discarded_calls.add(id(call))
            case Name(id="_"):
                underscore_used = True
            case _:
                continue
    counts: dict[str, int] = binding_counts(module=module)
    _ = mark_noreturn_calls(module=module, counts=counts)
    owners, overloaded = _structure(module=module)
    conversion: LazyConversion | None = (
        LazyConversion(module=module) if chosen.engine else None
    )
    return ModuleFacts(
        create_constants=chosen.create_constants,
        stub_docstrings=chosen.stub_docstrings,
        docstring_types=chosen.docstring_types,
        method_owner=owners,
        overloaded=overloaded,
        triple_quoted=triple_quoted_owners(module=module),
        discarded_calls=frozenset(discarded_calls),
        underscore_used=underscore_used,
        module=module,
        any_names=frozenset(any_names),
        final_names=frozenset(final_names),
        typing_names=frozenset(typing_names),
        binding_counts=counts,
        hints=_hints_for(
            module=module,
            options=chosen,
            conversion=conversion,
        ),
        variables=LazyVariables(
            module=module,
            forced=chosen.annotate_variables or chosen.engine,
            conversion=conversion,
        ),
        calls=CallBindings(module=module, counts=counts),
        project=chosen.project,
        libraries=chosen.libraries,
        target=(
            chosen.target if chosen.target is not None else resolve_target()
        ),
        source=chosen.source,
        runtime_protocols=chosen.runtime_protocols,
        accept_general=chosen.accept_general,
        protocol_placement=chosen.protocol_placement,
    )


def _mentions_any(*, root: AST, facts: ModuleFacts) -> bool:
    """Report whether a tree mentions ``typing.Any``, quoted or not.

    Args:
        root (AST): Annotation expression.
        facts (ModuleFacts): Resolved imports.

    Returns:
        bool: Whether ``Any`` appears, including inside string annotations.

    """
    for node in walk(node=root):
        match node:
            case Name(id=name) if name in facts.any_names:
                return True
            case Attribute(attr="Any", value=Name(id=owner)) if (
                owner in facts.typing_names
            ):
                return True
            case Constant(value=str() as text):
                try:
                    quoted: Expression = parse(
                        source=text,
                        mode="eval",
                    )
                except SyntaxError:
                    continue
                if _mentions_any(root=quoted, facts=facts):
                    return True
            case _:
                continue
    return False


def _uses_typing_any(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether an annotation mentions ``typing.Any``.

    Args:
        subject (Subject): Annotation subject.
        facts (ModuleFacts): Resolved imports.

    Returns:
        FactValue: Whether ``Any`` appears anywhere in the annotation.

    """
    return _mentions_any(root=subject.node, facts=facts)


def _is_module_global(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a binding is at module scope.

    Args:
        subject (Subject): Binding subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the enclosing scope is the module.

    """
    return subject.scope == "module"


def _name_is_uppercase(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a binding name is uppercase.

    Args:
        subject (Subject): Binding subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the name has cased characters and all are uppercase.

    """
    return subject.name.isupper()


def _is_final(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a binding is annotated ``Final``.

    Args:
        subject (Subject): Binding subject.
        facts (ModuleFacts): Resolved imports.

    Returns:
        FactValue: Whether the annotation is ``Final`` or ``Final[...]``.

    """
    match subject.statement:
        case AnnAssign(annotation=annotation):
            target: expr = (
                annotation.value
                if isinstance(annotation, Subscript)
                else annotation
            )
            match target:
                case Name(id=name):
                    return name in facts.final_names or name == "Final"
                case Attribute(attr="Final", value=Name(id=owner)):
                    return owner in facts.typing_names
                case _:
                    return False
        case _:
            return False


def _value_is_immutable_literal(
    subject: Subject,
    _facts: ModuleFacts,
) -> FactValue:
    """Report whether a plain assignment stores a scalar literal.

    Args:
        subject (Subject): Binding subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the statement is ``NAME = <scalar literal>``.

    """
    match subject.statement:
        case Assign(targets=[Name()], value=Constant(value=value)):
            return isinstance(value, Constants.immutable_literals)
        case _:
            return False


def _is_assigned_once(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether the name is bound exactly once in the module.

    Args:
        subject (Subject): Binding subject.
        facts (ModuleFacts): Resolved imports and binding counts.

    Returns:
        FactValue: Whether no other statement or scope rebinds the name.

    """
    return facts.binding_counts.get(subject.name, 0) == 1


def _final_is_spellable(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether ``Final`` can be written without clashing.

    Args:
        _subject (Subject): Unused binding subject.
        facts (ModuleFacts): Resolved imports and binding counts.

    Returns:
        FactValue: Whether ``Final`` is imported already, reachable through the
            ``typing`` module, or otherwise unbound.

    """
    return (
        bool(facts.final_names or facts.typing_names)
        or facts.binding_counts.get("Final", 0) == 0
    )


def _is_type_declaration(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether an assignment declares a type, not a constant.

    Args:
        subject (Subject): Binding subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the value is a ``TypeVar``-style constructor call.

    """
    if (
        _facts.aliases.get(module=_facts.module, statement=subject.statement)
        is not None
    ):
        return True
    match subject.statement:
        case Assign(value=Call(func=func)):
            match func:
                case Name(id=name) | Attribute(attr=name):
                    return name in Constants.type_constructors
                case _:
                    return False
        case _:
            return False


def _legacy_alias(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report an alias that can use the target's native type statement.

    Args:
        subject (Subject): Existing assignment binding.
        facts (ModuleFacts): Target version and shared lexical declaration
            cache.

    Returns:
        FactValue: Whether the binding has a guarded PEP 695 migration.

    """
    return (
        facts.target.type_statement
        and facts.aliases.get(
            module=facts.module,
            statement=subject.statement,
        )
        is not None
    )


def _annotation_missing(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a parameter or a function return lacks an annotation.

    Members of a synthesized ``Protocol`` are exempt: their types are open by
    construction, and flagging them would make ``fix`` and ``check`` disagree.

    Args:
        subject (Subject): Parameter or function subject.
        facts (ModuleFacts): Resolved structure of the module.

    Returns:
        FactValue: Whether the annotation is missing; receivers are exempt.

    """
    function: AST = (
        subject.statement if subject.kind == "Parameter" else subject.node
    ) or subject.node
    if _is_synthesized_member(function=function, facts=facts):
        return False
    match (subject.node, subject.statement):
        case [
            arg(annotation=None, arg=name),
            FunctionDef() | AsyncFunctionDef() as owner,
        ]:
            first: list[arg] = [*owner.args.posonlyargs, *owner.args.args]
            is_receiver: bool = (
                bool(first)
                and first[0] is subject.node
                and (name in {"self", "cls"})
            )
            return not is_receiver
        case [
            FunctionDef(returns=None) | AsyncFunctionDef(returns=None),
            _,
        ]:
            return subject.kind != "Parameter"
        case _:
            return False


def _returns_nothing(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a function provably returns ``None``.

    Args:
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the function provably returns nothing.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            return returns_nothing(function=function)
        case _:
            return False


def _plain_parameter(
    subject: Subject,
    facts: ModuleFacts,
) -> tuple[arg, FunctionDef | AsyncFunctionDef] | None:
    """Select unannotated, defaultless, non-variadic, non-receiver parameters.

    Args:
        subject (Subject): Candidate subject.
        facts (ModuleFacts): Resolved imports.

    Returns:
        tuple[arg, FunctionDef | AsyncFunctionDef] | None:
            The parameter and its function, or ``None`` for any other subject.

    """
    if subject.kind != "Parameter" or not _annotation_missing(
        subject=subject,
        facts=facts,
    ):
        return None
    match (subject.node, subject.statement):
        case [
            arg() as parameter,
            FunctionDef() | AsyncFunctionDef() as function,
        ]:
            variadic: bool = parameter in {
                function.args.vararg,
                function.args.kwarg,
            }
            if variadic or parameter_has_default(
                function=function,
                parameter=parameter,
            ):
                return None
            return (parameter, function)
        case _:
            return None


def _synthesis_allowed(
    *,
    function: FunctionDef | AsyncFunctionDef,
    parameter: arg,
    facts: ModuleFacts,
) -> bool:
    """Tell whether a parameter may get a synthesized type.

    Refused: overload groups, dunder methods, the first parameter of any
    non-static method, and methods of classes with bases (they may override
    a signature that is not visible here).

    Args:
        function (FunctionDef | AsyncFunctionDef): Function that owns the
            parameter.
        parameter (arg): The parameter.
        facts (ModuleFacts): Resolved structure of the module.

    Returns:
        bool: ``True`` when synthesis cannot contradict another signature.

    """
    if id(function) in facts.overloaded:
        return False
    owner: ClassDef | None = facts.method_owner.get(id(function))
    if owner is None:
        return True
    dunder: bool = function.name.startswith("__") and function.name.endswith(
        "__",
    )
    static: bool = any(
        isinstance(item, Name) and item.id == "staticmethod"
        for item in function.decorator_list
    )
    first: list[arg] = [*function.args.posonlyargs, *function.args.args]
    is_first: bool = bool(first) and first[0] is parameter
    return not (dunder or bool(owner.bases) or (is_first and (not static)))


def _is_synthesized_member(*, function: AST, facts: ModuleFacts) -> bool:
    """Tell whether a function is a member of a synthesized ``Protocol``.

    Args:
        function (AST): Candidate function node.
        facts (ModuleFacts): Resolved structure of the module.

    Returns:
        bool: ``True`` when the owning class carries the synthesized docstring.

    """
    owner: ClassDef | None = facts.method_owner.get(id(function))
    if owner is None:
        return False
    return (get_docstring(node=owner) or "").startswith(
        ProtocolConstants.docstring_marker,
    )


def _has_structural_protocol(
    subject: Subject,
    facts: ModuleFacts,
) -> FactValue:
    """Report whether a parameter is used only through its attributes.

    Args:
        subject (Subject): Parameter subject.
        facts (ModuleFacts): Resolved imports and lazily computed hints.

    Returns:
        FactValue:
            Whether a ``Protocol`` can be synthesized for it and the hint
            index itself (not a negotiated supplement) has no hint for it.

    """
    return (
        _structural_candidate(subject=subject, facts=facts)
        and not _is_passthrough(subject=subject, facts=facts)
        and (
            facts.hints is None
            or facts.hints.index().own_hint_for(node=subject.node) is None
        )
    )


def _structural_candidate(subject: Subject, facts: ModuleFacts) -> bool:
    """Report whether a parameter's usage would justify a ``Protocol``.

    Args:
        subject (Subject): Parameter subject.
        facts (ModuleFacts): Resolved imports and lazily computed hints.

    Returns:
        bool: Whether the parameter is used only
            through members and no call site objects.

    """
    plain: tuple[arg, FunctionDef | AsyncFunctionDef] | None = (
        _plain_parameter(subject=subject, facts=facts)
    )
    if plain is None:
        return False
    parameter, function = plain
    if not _synthesis_allowed(
        function=function,
        parameter=parameter,
        facts=facts,
    ):
        return False
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
    return not (
        usage is None
        or call_site_objection(
            function=function,
            parameter=parameter.arg,
            members=[member.name for member in usage.members],
            facts=facts,
        )
    )


def _is_passthrough(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a parameter only flows through to the return value.

    Args:
        subject (Subject): Parameter subject.
        facts (ModuleFacts): Resolved imports.

    Returns:
        FactValue:
            Whether a type variable can describe the parameter and the return.

    """
    plain: tuple[arg, FunctionDef | AsyncFunctionDef] | None = (
        _plain_parameter(subject=subject, facts=facts)
    )
    if plain is None:
        return False
    parameter, function = plain
    receiver: tuple[str, bool] | None = receiver_info(
        module=facts.module,
        function=function,
    )
    if not _synthesis_allowed(
        function=function,
        parameter=parameter,
        facts=facts,
    ):
        return False
    if (
        typevar_plan(
            function=function,
            parameter=parameter.arg,
            variable="T",
            counts=facts.binding_counts,
            receiver=receiver,
        )
        is not None
    ):
        return True
    candidates: dict[str, arg] = candidate_params(
        function=function,
        receiver=receiver,
    )
    if parameter.arg not in candidates:
        return False
    forwarded: tuple[str, str] | None = forwarding_decorator(
        function=function,
    )
    shared: list[str] | None = shared_parameters(
        function=function,
        candidates=candidate_params(
            function=function,
            receiver=receiver,
            include_annotated=True,
        ),
    )
    if (
        forwarded is not None
        and forwarded[0] == parameter.arg
        and facts.target.param_spec
    ) or (
        shared is not None
        and parameter.arg in shared
        and shared_return(
            function=function,
            involved=shared,
            variable="T",
            counts=facts.binding_counts,
        )
        is not None
    ):
        return True
    shaped: tuple[tuple[str, ...], str] | None = multi_return(
        function=function,
        candidates={name: name for name in candidates},
    )
    return shaped is not None and parameter.arg in shaped[0]


def _self_return(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a method returns its receiver and can use ``Self``.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: ``True`` when every return hands back ``self`` or ``cls()``.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            pass
        case _:
            return False
    if not facts.target.self_type:
        return False
    if function.returns is not None:
        return False
    receiver: tuple[str, bool] | None = receiver_info(
        module=facts.module,
        function=function,
    )
    if receiver is None:
        return False
    plan: TypeVarPlan | None = typevar_plan(
        function=function,
        parameter=receiver[0],
        variable="T",
        counts=facts.binding_counts,
        receiver=receiver,
    )
    return plan is not None and not plan.variable


def _constants_wanted(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether the module follows the ``Constants`` convention.

    Args:
        _subject (Subject): Unused subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: ``True`` when the module defines a ``Constants``
            class, or when creating one was asked for.

    """
    return facts.create_constants or any(
        isinstance(item, ClassDef) and item.name == "Constants"
        for item in facts.module.body
    )


def _groupable(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a ``Final`` constant can move into ``Constants``.

    Args:
        subject (Subject): Annotated assignment subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue:
            Whether an existing ``Constants`` class can take it safely, or one
            can be created because the module has no binding of that name.

    """
    match subject.statement:
        case AnnAssign(target=Name(id=name)) as statement:
            return find_group(
                module=facts.module,
                statement=statement,
                name=name,
                counts=facts.binding_counts,
            ) is not None or creatable(
                module=facts.module,
                statement=statement,
                counts=facts.binding_counts,
            )
        case _:
            return False


def _constants_snake_case(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a ``Constants`` attribute can take snake_case.

    Args:
        subject (Subject): Assignment subject inside the class body.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue:
            Whether the attribute name is not already snake_case and
            :func:`renameable` accepts the rename.

    """
    name: str = subject.name
    if (
        subject.scope != "class"
        or snake_name(name=name) == name
        or not isinstance(subject.statement, (AnnAssign, Assign))
    ):
        return False
    return (
        renameable(
            module=facts.module,
            statement=subject.statement,
            name=name,
            counts=facts.binding_counts,
        )
        is not None
    )


def _never_returns(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a function provably never returns a value.

    Args:
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue:
            Whether every path raises and the function is not a declaration.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            return (
                function.returns is None
                and not is_declaration(function=function)
                and never_returns(function=function)
            )
        case _:
            return False


def _has_inferred_hint(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a corroborated hint other than ``None`` exists.

    Args:
        subject (Subject): Parameter or function subject.
        facts (ModuleFacts): Resolved imports and lazily computed hints.

    Returns:
        FactValue: Whether an accepted hint is available for the node.

    """
    if facts.hints is None:
        return False
    hint: Hint | None = facts.hints.index().hint_for(node=subject.node)
    if hint is None or hint.basis is HintBasis.proven_none:
        return False
    if hint.basis is HintBasis.negotiated and subject.kind == "Parameter":
        return not _structural_candidate(subject=subject, facts=facts)
    return True


def _hints_for(
    *,
    module: CommentedModule,
    options: FactsOptions,
    conversion: LazyConversion | None,
) -> LazyHints:
    """Build the lazy hints of a module, with negotiation if asked for.

    Args:
        module (CommentedModule): Parsed module.
        options (FactsOptions): Options of the facts run.
        conversion (LazyConversion | None): The inference engine's lazy output
            in conversion mode.

    Returns:
        LazyHints: The lazy hint index.

    """
    lazy: LazyHints = LazyHints(
        module=module,
        stubs_path=options.stubs_path,
        source=options.source,
        cache=options.cache,
        project=options.project,
    )
    if options.negotiate or options.engine:
        return lazy.supplemented(
            by=partial(
                _negotiated,
                module=module,
                conversion=conversion,
                negotiate=options.negotiate,
            ),
        )
    return lazy


def _negotiated(
    index: HintIndex,
    *,
    module: CommentedModule,
    conversion: LazyConversion | None,
    negotiate: bool,
) -> dict[Key, Hint]:
    """Negotiate parameter and return hints to supplement the hint index.

    Args:
        index (HintIndex): The built hint index, whose engine proposals
            corroborate.
        module (CommentedModule): Parsed module.
        conversion (LazyConversion | None): The inference engine's lazy output
            in conversion mode, or ``None``.
        negotiate (bool): Whether negotiated hints are produced.

    Returns:
        dict[Key, Hint]: Hints for nodes the index has none for.

    """
    found: dict[Key, Hint] = (
        negotiated_hints(module=module, proposals=index.proposals)
        if negotiate
        else {}
    )
    if conversion is not None:
        for key, hint in engine_hints(
            module=module,
            conversion=conversion,
        ).items():
            _ = found.setdefault(key, hint)
    return found


def _has_variable_hint(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether negotiation justified a variable annotation.

    Args:
        subject (Subject): Assignment subject.
        facts (ModuleFacts): Resolved imports and the lazily negotiated
            variables.

    Returns:
        FactValue: Whether the assignment statement can carry an annotation.

    """
    statement: AST | None = subject.statement
    if facts.variables is None or not isinstance(statement, Assign):
        return False
    if len(statement.targets) != 1:
        return False
    if facts.aliases.get(module=facts.module, statement=statement) is not None:
        return False
    return facts.variables.hint_for(node=statement) is not None


def bound_call(subject: Subject, facts: ModuleFacts) -> BoundCall | None:
    """Bind a call to a function or class defined in this module.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        BoundCall | None:
            The bound call, or ``None`` when the callee is not defined here.

    """
    match subject.node:
        case Call() as call:
            if facts.calls is not None:
                bound: BoundCall | None = facts.calls.get(call=call)
                if bound is not None:
                    return bound
            if facts.project is not None:
                bound = facts.project.binding(call=call)
                if bound is not None:
                    return bound
            return library_binding(
                module=facts.module,
                call=call,
                counts=facts.binding_counts,
            )
        case _:
            return None


def kept_positionals(*, bound: BoundCall) -> int:
    """Count the leading arguments that must stay positional.

    These are positional-only parameters and, for a method called through its
    class, the explicit receiver.

    Args:
        bound (BoundCall): Binding of the call.

    Returns:
        int: How many leading arguments are not turned into keywords.

    """
    fixed: int = sum(
        1
        for argument in bound.arguments
        if argument.origin is ArgumentOrigin.POSITIONAL
        and argument.parameter.kind is ParameterKind.POSITIONAL_ONLY
    )
    explicit_receiver: bool = (
        bound.signature.method_kind == "instance"
        and bool(bound.signature.parameters)
        and any(
            argument.origin is ArgumentOrigin.POSITIONAL
            and argument.parameter.name == bound.signature.parameters[0].name
            for argument in bound.arguments
        )
    )
    return max(fixed, 1) if explicit_receiver else fixed


def keyword_candidates(subject: Subject, facts: ModuleFacts) -> list[str]:
    """List parameters passed positionally that could be keywords.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        list[str]: Parameter names, in declaration order.

    """
    bound: BoundCall | None = bound_call(subject=subject, facts=facts)
    if bound is None:
        return []
    if any(
        argument.origin is ArgumentOrigin.VAR_POSITIONAL and argument.values
        for argument in bound.arguments
    ):
        return []
    if any(isinstance(arg, Starred) for arg in _call_args(subject=subject)):
        return []
    receiver: str | None = (
        bound.signature.parameters[0].name
        if bound.signature.method_kind == "instance"
        and bound.signature.parameters
        else None
    )
    return [
        argument.parameter.name
        for argument in bound.arguments
        if argument.origin is ArgumentOrigin.POSITIONAL
        and argument.parameter.kind is ParameterKind.POSITIONAL_OR_KEYWORD
        and argument.parameter.name != receiver
    ]


def _candidate_count(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count parameters passed positionally that could be keywords.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: The number of such parameters.

    """
    return len(keyword_candidates(subject=subject, facts=facts))


def _is_resolved(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a call's callee is defined in this module.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: Whether the call binds to a local definition.

    """
    return bound_call(subject=subject, facts=facts) is not None


def _unused_result(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a call's result is provably discarded.

    The call must sit in statement position — an ``Expr`` value, directly
    or under a single ``await`` — its callee must declare a return type
    that is not ``None``, and ``_`` must be free to bind the result.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: Whether the call's value is unused and worth keeping.

    """
    call: AST = subject.node
    if not isinstance(call, Call):
        return False
    if id(call) not in facts.discarded_calls:
        return False
    if facts.underscore_used:
        return False
    bound: BoundCall | None = bound_call(subject=subject, facts=facts)
    if bound is None or bound.signature.returns is None:
        return False
    return bound.signature.returns.name not in Constants.unused_result_none


def _has_docstring(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a function has a docstring.

    Args:
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        FactValue: Whether the function body starts with a docstring.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            return get_docstring(node=function) is not None
        case _:
            return False


def _undocumented(subject: Subject, facts: ModuleFacts) -> list[str]:
    """List parameters missing from the docstring's parameter sections.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        list[str]: Undocumented parameter names, without stars, in declaration
            order.

    """
    match subject.node:
        case FunctionDef() | AsyncFunctionDef() as function:
            pass
        case _:
            return []
    documented: set[str] | None = None
    for docstring in facts.module.docstrings:
        if docstring.owner is function:
            documented = {
                (entry.name or "").lstrip("*")
                for section in docstring.sections
                if section.kind == "parameters"
                for entry in section.entries
            }
    if documented is None:
        return []
    arguments: arguments = function.args
    names: list[str] = [
        arg.arg
        for arg in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
            *(a for a in (arguments.vararg, arguments.kwarg) if a),
        )
    ]
    return [
        name
        for name in names
        if name not in {"self", "cls"} and name not in documented
    ]


def _undocumented_count(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count parameters missing from the docstring.

    Args:
        subject (Subject): Function subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        FactValue: The number of undocumented parameters.

    """
    return len(_undocumented(subject=subject, facts=facts))


def _blank_run_count(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count blank-line runs beyond the tolerated maximum.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved facts; ``source`` carries the module
            text.

    Returns:
        FactValue:
            The number of excessive blank-line runs, zero without source.

    """
    if facts.source is None:
        return 0
    return count_blank_line_runs(source=facts.source)


def _trailing_space_count(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count lines ending in spaces or tabs.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved facts; ``source`` carries the module
            text.

    Returns:
        FactValue: The number of lines with trailing whitespace, zero without
            source.

    """
    if facts.source is None:
        return 0
    return count_trailing_space_lines(source=facts.source)


def _overlong_string_count(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count string literals the split rewrite would change.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved facts; ``source`` carries the module
            text.

    Returns:
        FactValue: The number of overlong literals and f-strings, zero without
            source.

    """
    if facts.source is None:
        return 0
    return sum(
        1
        for change in normalize_strings(
            source=facts.source,
            line_length=DocstringConstants.line_length,
        ).changes
        if change.kind == "split"
    )


def _overlong_comment_count(
    _subject: Subject,
    facts: ModuleFacts,
) -> FactValue:
    """Count comment paragraphs the wrap rewrite would change.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved facts; ``source`` carries the module
            text.

    Returns:
        FactValue: The number of overlong comment paragraphs, zero without
            source.

    """
    if facts.source is None:
        return 0
    return len(
        comment_wrap_plans(
            comments=facts.module.comments,
            source_lines=facts.source.splitlines(),
            line_length=DocstringConstants.line_length,
        ),
    )


def _escaped_newline_count(_subject: Subject, facts: ModuleFacts) -> FactValue:
    r"""Count literals whose ``\\\\n`` escapes the triple rewrite expands.

    Args:
        _subject (Subject): Module subject.
        facts (ModuleFacts): Resolved facts; ``source`` carries the module
            text.

    Returns:
        FactValue: The number of literals the rewrite would expand, zero
            without source.

    """
    if facts.source is None:
        return 0
    return sum(
        1
        for change in normalize_strings(
            source=facts.source,
            line_length=DocstringConstants.line_length,
        ).changes
        if change.kind in ("triple", "collapse")
    )


def name_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``name`` evidence slot.

    Args:
        subject (Subject): Subject being reported.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        JsonValue: The bound or annotated name.

    """
    return subject.name


def callee_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``callee`` evidence slot.

    Args:
        subject (Subject): Call subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        JsonValue: The callee as written.

    """
    return subject.name


def function_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``function`` evidence slot.

    Args:
        subject (Subject): Function subject.
        _facts (ModuleFacts): Unused resolved imports.

    Returns:
        JsonValue: The qualified function path.

    """
    return subject.path


def call_parameters_evidence(
    subject: Subject,
    facts: ModuleFacts,
) -> JsonValue:
    """Provide the ``parameters`` slot of a call finding.

    Args:
        subject (Subject): Call subject.
        facts (ModuleFacts): Resolved imports and the parsed module.

    Returns:
        JsonValue: Parameter names that should be passed by keyword.

    """
    match subject.node:
        case Call():
            return cast(
                typ="JsonValue",
                val=list(keyword_candidates(subject=subject, facts=facts)),
            )
        case _:
            return cast(
                typ="JsonValue",
                val=list(_undocumented(subject=subject, facts=facts)),
            )


@final
class Registry:
    """Group the engine's fact specifications and providers.

    Attributes:
        specs (Final[tuple[FactSpec, ...]]): Declarations of every fact.
        providers (Final[Mapping[str, FactProvider]]): Provider function for
            every fact.
        evidence (Final[Mapping[str, EvidenceProvider]]): Provider function for
            every evidence slot.

    """

    specs: Final[tuple[FactSpec, ...]] = (
        FactSpec(
            name="binding.is_legacy_alias",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="annotation.uses_typing_any",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="binding.is_module_global",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="binding.name_is_uppercase",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(name="binding.is_final", value_type="bool", cost=Cost.scope),
        FactSpec(
            name="binding.value_is_immutable_literal",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="binding.is_assigned_once",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="binding.final_is_spellable",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="binding.is_type_declaration",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="node.annotation_missing",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="function.returns_nothing",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="constants.wanted",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="constants.groupable",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="constants.snake_case",
            value_type="bool",
            cost=Cost.scope,
        ),
        FactSpec(
            name="function.never_returns",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="annotation.has_inferred_hint",
            value_type="bool",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="variable.has_inferred_hint",
            value_type="bool",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="parameter.has_structural_protocol",
            value_type="bool",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="parameter.is_passthrough",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="function.self_return",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="call.positional_keyword_candidates",
            value_type="int",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="call.is_resolved_in_module",
            value_type="bool",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="call.unused_result",
            value_type="bool",
            cost=Cost.semantic,
        ),
        FactSpec(
            name="function.has_docstring",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="function.undocumented_parameter_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="function.stale_documented_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docstring.is_editable",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docstring.generator_needs_results",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docstring.needs_types",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docstring.is_untidy",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docs.stubs_wanted",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="docstring.is_missing_public",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="whitespace.blank_run_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="whitespace.trailing_space_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="whitespace.overlong_string_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="whitespace.overlong_comment_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="whitespace.escaped_newline_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
    )
    providers: Final[Mapping[str, FactProvider]] = {
        "binding.is_legacy_alias": _legacy_alias,
        "annotation.uses_typing_any": _uses_typing_any,
        "binding.is_module_global": _is_module_global,
        "binding.name_is_uppercase": _name_is_uppercase,
        "binding.is_final": _is_final,
        "binding.value_is_immutable_literal": _value_is_immutable_literal,
        "binding.is_assigned_once": _is_assigned_once,
        "binding.final_is_spellable": _final_is_spellable,
        "binding.is_type_declaration": _is_type_declaration,
        "node.annotation_missing": _annotation_missing,
        "function.returns_nothing": _returns_nothing,
        "constants.groupable": _groupable,
        "constants.wanted": _constants_wanted,
        "constants.snake_case": _constants_snake_case,
        "function.never_returns": _never_returns,
        "annotation.has_inferred_hint": _has_inferred_hint,
        "variable.has_inferred_hint": _has_variable_hint,
        "parameter.has_structural_protocol": _has_structural_protocol,
        "parameter.is_passthrough": _is_passthrough,
        "function.self_return": _self_return,
        "call.positional_keyword_candidates": _candidate_count,
        "call.is_resolved_in_module": _is_resolved,
        "call.unused_result": _unused_result,
        "function.has_docstring": _has_docstring,
        "function.stale_documented_count": stale_count,
        "docstring.is_editable": is_editable,
        "docstring.needs_types": needs_types,
        "docstring.is_untidy": is_untidy,
        "docstring.generator_needs_results": generator_needs_results,
        "docstring.is_missing_public": is_missing_public,
        "docs.stubs_wanted": stubs_wanted,
        "function.undocumented_parameter_count": _undocumented_count,
        "whitespace.blank_run_count": _blank_run_count,
        "whitespace.trailing_space_count": _trailing_space_count,
        "whitespace.overlong_string_count": _overlong_string_count,
        "whitespace.overlong_comment_count": _overlong_comment_count,
        "whitespace.escaped_newline_count": _escaped_newline_count,
    }
    evidence: Final[Mapping[str, EvidenceProvider]] = {
        "name": name_evidence,
        "callee": callee_evidence,
        "function": function_evidence,
        "parameters": call_parameters_evidence,
        "stale": stale_evidence,
    }


def default_registries() -> Registries:
    """Build the registries describing this engine.

    Returns:
        Registries: Node kinds, facts, appliers and no procedures.

    """
    return Registries(
        node_kinds=Constants.node_kinds,
        facts={spec.name: spec for spec in Registry.specs},
        procedures=frozenset(),
        appliers=Constants.applier_keys,
    )


def collect_subjects(
    *,
    module: CommentedModule,
    kinds: frozenset[str],
) -> list[Subject]:
    """Enumerate subjects of the wanted kinds in source order.

    Args:
        module (CommentedModule): Parsed module.
        kinds (frozenset[str]): Subject kinds to enumerate.

    Returns:
        list[Subject]: Subjects in traversal order.

    """
    subjects: list[Subject] = []
    _visit(
        node=module,
        kinds=kinds,
        site=_Site(trail=(), scope="module"),
        out=subjects,
    )
    return _number_repeats(subjects=subjects)


def _visit(
    *,
    node: AST,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Visit one node and its children, emitting subjects.

    Args:
        node (AST): Node to visit.
        kinds (frozenset[str]): Subject kinds to enumerate.
        site (_Site): Enclosing scope trail and kind.
        out (list[Subject]): Destination list, extended in place.

    """
    kind: str = type(node).__name__
    if isinstance(node, Module) and kind != "Module":
        kind = "Module"
    inner: _Site = site
    match node:
        case FunctionDef() | AsyncFunctionDef():
            _emit_function(node=node, kinds=kinds, site=site, out=out)
            inner = _Site(trail=(*site.trail, node.name), scope="function")
        case ClassDef():
            if kind in kinds:
                out.append(site.subject(kind=kind, node=node, name=node.name))
            inner = _Site(trail=(*site.trail, node.name), scope="class")
        case Assign():
            _emit_assign(node=node, kinds=kinds, site=site, out=out)
        case AnnAssign():
            _emit_annotated(node=node, kinds=kinds, site=site, out=out)
        case Call() | Module():
            if kind in kinds:
                out.append(
                    site.subject(
                        kind=kind,
                        node=node,
                        name=_call_name(node=node),
                    ),
                )
        case _:
            pass
    for child in iter_child_nodes(node=node):
        _visit(node=child, kinds=kinds, site=inner, out=out)


@final
@dataclass(frozen=True, slots=True)
class _Site:
    """Position in the scope tree where subjects are created.

    Attributes:
        trail (tuple[str, ...]): Qualified names of the enclosing scopes.
        scope (str): Enclosing scope kind.

    """

    trail: tuple[str, ...]
    scope: str

    def subject(
        self,
        kind: str,
        node: AST,
        name: str,
        statement: AST | None = None,
    ) -> Subject:
        """Build a subject whose path extends the scope trail.

        Args:
            kind (str): Subject kind.
            node (AST): Node the rule reports on.
            name (str): Name of the subject.
            statement (AST | None): Owning statement when different from the
                node.

        Returns:
            Subject: The subject.

        """
        parts: tuple[str, ...] = (*self.trail, name) if name else self.trail
        return Subject(
            kind=kind,
            node=node,
            path=".".join(parts),
            scope=self.scope,
            name=name,
            statement=statement or node,
        )


def _call_args(subject: Subject) -> list[expr]:
    """Return the positional argument expressions of a call subject.

    Args:
        subject (Subject): Call subject.

    Returns:
        list[expr]: The arguments, empty for non-call subjects.

    """
    match subject.node:
        case Call(args=args):
            return list(args)
        case _:
            return []


def _call_name(node: AST) -> str:
    """Name a subject node for path purposes.

    Args:
        node (AST): Call or module node.

    Returns:
        str: The callee text for calls, empty for modules.

    """
    match node:
        case Call(func=func):
            return unparse(ast_obj=func)
        case Module():
            return "<module>"
        case _:
            return ""


def _emit_assign(
    *,
    node: Assign,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Emit name and attribute subjects for one assignment.

    Args:
        node (Assign): Assignment statement.
        kinds (frozenset[str]): Subject kinds to enumerate.
        site (_Site): Scope the assignment lives in.
        out (list[Subject]): Destination list, extended in place.

    """
    if "Assign" in kinds:
        out.extend(
            site.subject(
                kind="Assign",
                node=target,
                name=target.id,
                statement=node,
            )
            for target in node.targets
            if isinstance(target, Name)
        )
    if "Attribute" not in kinds:
        return
    out.extend(
        site.subject(
            kind="Attribute",
            node=node,
            name=target.attr,
            statement=node,
        )
        for target in node.targets
        if isinstance(target, Attribute) and isinstance(target.value, Name)
    )


def _emit_function(
    *,
    node: FunctionDef | AsyncFunctionDef,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Emit the function subject and its annotation subjects.

    Args:
        node (FunctionDef | AsyncFunctionDef): Function definition.
        kinds (frozenset[str]): Subject kinds to enumerate.
        site (_Site): Scope the function is defined in.
        out (list[Subject]): Destination list, extended in place.

    """
    kind: str = type(node).__name__
    if kind in kinds:
        out.append(site.subject(kind=kind, node=node, name=node.name))
    if not kinds & {"Annotation", "Parameter"}:
        return
    inner: _Site = _Site(trail=(*site.trail, node.name), scope="function")
    arguments: arguments = node.args
    parameters: list[arg] = [
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        *(a for a in (arguments.vararg, arguments.kwarg) if a is not None),
    ]
    if "Parameter" in kinds:
        out.extend(
            inner.subject(
                kind="Parameter",
                node=arg,
                name=arg.arg,
                statement=node,
            )
            for arg in parameters
        )
    if "Annotation" not in kinds:
        return
    out.extend(
        inner.subject(kind="Annotation", node=arg.annotation, name=arg.arg)
        for arg in parameters
        if arg.annotation is not None
    )
    if node.returns is not None:
        out.append(
            inner.subject(
                kind="Annotation",
                node=node.returns,
                name="<return>",
            ),
        )


def _emit_annotated(
    *,
    node: AnnAssign,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Emit subjects for an annotated assignment.

    Args:
        node (AnnAssign): Annotated assignment.
        kinds (frozenset[str]): Subject kinds to enumerate.
        site (_Site): Scope the assignment is in.
        out (list[Subject]): Destination list, extended in place.

    """
    if not isinstance(node.target, Name):
        return
    name: str = node.target.id
    if "AnnAssign" in kinds:
        out.append(
            site.subject(
                kind="AnnAssign",
                node=node.target,
                name=name,
                statement=node,
            ),
        )
    if "Assign" in kinds:
        out.append(
            site.subject(
                kind="Assign",
                node=node.target,
                name=name,
                statement=node,
            ),
        )
    if "Annotation" in kinds:
        out.append(
            site.subject(
                kind="Annotation",
                node=node.annotation,
                name=name,
                statement=node,
            ),
        )


def _number_repeats(*, subjects: list[Subject]) -> list[Subject]:
    """Suffix repeated paths of one kind with ``#2``, ``#3`` and so on.

    Args:
        subjects (list[Subject]): Subjects in traversal order.

    Returns:
        list[Subject]: The subjects with distinct paths per kind.

    """
    seen: dict[tuple[str, str], int] = {}
    result: list[Subject] = []
    for subject in subjects:
        slot: tuple[str, str] = (subject.kind, subject.path)
        count: int = seen.get(slot, 0) + 1
        seen[slot] = count
        result.append(
            subject
            if count == 1
            else replace(subject, path=(f"{subject.path}#{count}")),
        )
    return result
