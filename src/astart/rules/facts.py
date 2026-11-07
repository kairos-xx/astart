"""Subjects, fact providers and registries for the reference engine."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Final, final

from astart.rules.hints import HintBasis, HintCache, LazyHints, returns_nothing
from astart.rules.predicate import FactValue
from astart.rules.protocols import Constants as ProtocolConstants
from astart.rules.protocols import parameter_has_default, structural_usage
from astart.rules.registry import FactSpec, Registries
from astart.rules.resolve import CallBindings, binding_counts
from astart.rules.typevars import passthrough_return
from astart.rules.vocabulary import Cost
from astart.semantic import ArgumentOrigin, ParameterKind

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from astart import BoundCall, CommentedModule
    from astart.rules.jsonvalue import JsonValue
type FactProvider = Callable[[Subject, ModuleFacts], FactValue]
type Applier = Callable[[Subject, ModuleFacts], None]
type EvidenceProvider = Callable[[Subject, ModuleFacts], JsonValue]


@final
@dataclass(frozen=True, slots=True)
class Subject:
    """One thing a rule inspects.

    Attributes:
        kind: Node kind, or ``Annotation`` for annotation expressions.
        node: Syntax node the rule reports on.
        path: Dotted qualified path used for the finding fingerprint.
        scope: Enclosing scope kind: ``module``, ``class`` or ``function``.
        name: Name of the bound or annotated thing.
        statement: Statement owning the subject, when different from node.

    """

    kind: str
    node: ast.AST
    path: str
    scope: str
    name: str
    statement: ast.AST | None = None


def _no_owners() -> dict[int, ast.ClassDef]:
    """Create an empty method-owner mapping.

    Returns:
        A new empty dictionary.

    """
    return {}


def _is_overload(*, function: ast.AST) -> bool:
    """Tell whether a function is decorated with ``overload``.

    Args:
        function: Candidate node.

    Returns:
        ``True`` for ``@overload`` and ``@typing.overload``.

    """
    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(
        (isinstance(item, ast.Name) and item.id == "overload")
        or (isinstance(item, ast.Attribute) and item.attr == "overload")
        for item in function.decorator_list
    )


def _structure(
    *,
    module: ast.Module,
) -> tuple[dict[int, ast.ClassDef], frozenset[int]]:
    """Find method owners and overload groups in one walk.

    Args:
        module: Parsed module.

    Returns:
        The owning class of every method and the ids of overloaded functions.

    """
    owners: dict[int, ast.ClassDef] = {}
    overloaded: set[int] = set()
    for node in ast.walk(node=module):
        if isinstance(node, ast.ClassDef):
            owners.update(
                {
                    id(child): node
                    for child in node.body
                    if isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef),
                    )
                },
            )
        for field_name in ("body", "orelse", "finalbody"):
            block = getattr(node, field_name, None)
            if not isinstance(block, list):
                continue
            functions = [
                item
                for item in block
                if isinstance(item, Constants.function_nodes)
            ]
            names = {
                item.name for item in functions if _is_overload(function=item)
            }
            overloaded.update(
                id(item) for item in functions if item.name in names
            )
    return (owners, frozenset(overloaded))


def _no_counts() -> dict[str, int]:
    """Create an empty binding-count mapping.

    Returns:
        A new empty dictionary.

    """
    return {}


@final
@dataclass(frozen=True, slots=True)
class ModuleFacts:
    """Import information resolved once per module.

    Attributes:
        module: Parsed module.
        any_names: Local names bound to ``typing.Any``.
        final_names: Local names bound to ``typing.Final``.
        typing_names: Local names bound to the ``typing`` module.
        hints: Lazily computed type hints for the module.
        calls: Trusted call bindings, computed in one batch on first use.
        method_owner: Class that directly defines each method, by node id.
        overloaded: Node ids of functions that belong to an overload group.
        binding_counts: How many times each name is bound in the module,
            ignoring names bound directly in class bodies (they do not
            shadow module-level names).

    """

    module: CommentedModule
    any_names: frozenset[str] = field(default_factory=frozenset)
    final_names: frozenset[str] = field(default_factory=frozenset)
    typing_names: frozenset[str] = field(default_factory=frozenset)
    binding_counts: Mapping[str, int] = field(default_factory=_no_counts)
    hints: LazyHints | None = None
    calls: CallBindings | None = None
    method_owner: Mapping[int, ast.ClassDef] = field(
        default_factory=_no_owners,
    )
    overloaded: frozenset[int] = field(default_factory=frozenset)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        typing_modules: Grouped module constant.
        node_kinds: Grouped module constant.
        position_attributes: Grouped module constant.
        function_nodes: Grouped module constant.
        type_constructors: Grouped module constant.
        applier_keys: Grouped module constant.
        immutable_literals: Grouped module constant.

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
    function_nodes: Final[tuple[type[ast.AST], ...]] = (
        ast.FunctionDef,
        ast.AsyncFunctionDef,
    )
    type_constructors: Final[frozenset[str]] = frozenset(
        {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType", "TypeAliasType"},
    )
    applier_keys: Final[frozenset[str]] = frozenset(
        {
            "typing.add-final",
            "calls.add-keywords",
            "typing.add-none-return",
            "typing.add-inferred-annotation",
            "typing.synthesize-protocol",
            "typing.synthesize-typevar",
        },
    )
    immutable_literals: Final[tuple[type, ...]] = (
        bool,
        int,
        float,
        str,
        bytes,
    )


def module_facts(
    *,
    module: CommentedModule,
    stubs_path: Path | None = None,
    source: str | None = None,
    cache: HintCache | None = None,
) -> ModuleFacts:
    """Resolve typing imports of a module.

    Args:
        module: Parsed module.
        stubs_path: Stub directory for type hints, or ``None``.
        source: Source text of the module, to share hints through ``cache``.
        cache: Shared hint cache, or ``None``.

    Returns:
        The resolved import information.

    """
    any_names: set[str] = set()
    final_names: set[str] = set()
    typing_names: set[str] = set()
    for node in ast.walk(node=module):
        match node:
            case ast.ImportFrom(module=source, names=aliases) if (
                source in Constants.typing_modules
            ):
                for alias in aliases:
                    bound: str = alias.asname or alias.name
                    if alias.name == "Any":
                        any_names.add(bound)
                    elif alias.name == "Final":
                        final_names.add(bound)
            case ast.Import(names=aliases):
                typing_names.update(
                    alias.asname or alias.name
                    for alias in aliases
                    if alias.name in Constants.typing_modules
                )
            case _:
                continue
    counts: dict[str, int] = binding_counts(module=module)
    owners, overloaded = _structure(module=module)
    return ModuleFacts(
        method_owner=owners,
        overloaded=overloaded,
        module=module,
        any_names=frozenset(any_names),
        final_names=frozenset(final_names),
        typing_names=frozenset(typing_names),
        binding_counts=counts,
        hints=LazyHints(
            module=module,
            stubs_path=stubs_path,
            source=source,
            cache=cache,
        ),
        calls=CallBindings(module=module, counts=counts),
    )


def _mentions_any(*, root: ast.AST, facts: ModuleFacts) -> bool:
    """Report whether a tree mentions ``typing.Any``, quoted or not.

    Args:
        root: Annotation expression.
        facts: Resolved imports.

    Returns:
        Whether ``Any`` appears, including inside string annotations.

    """
    for node in ast.walk(node=root):
        match node:
            case ast.Name(id=name) if name in facts.any_names:
                return True
            case ast.Attribute(attr="Any", value=ast.Name(id=owner)) if (
                owner in facts.typing_names
            ):
                return True
            case ast.Constant(value=str() as text):
                try:
                    quoted: ast.Expression = ast.parse(
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
        subject: Annotation subject.
        facts: Resolved imports.

    Returns:
        Whether ``Any`` appears anywhere in the annotation.

    """
    return _mentions_any(root=subject.node, facts=facts)


def _is_module_global(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a binding is at module scope.

    Args:
        subject: Binding subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the enclosing scope is the module.

    """
    return subject.scope == "module"


def _name_is_uppercase(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a binding name is uppercase.

    Args:
        subject: Binding subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the name has cased characters and all are uppercase.

    """
    return subject.name.isupper()


def _is_final(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a binding is annotated ``Final``.

    Args:
        subject: Binding subject.
        facts: Resolved imports.

    Returns:
        Whether the annotation is ``Final`` or ``Final[...]``.

    """
    match subject.statement:
        case ast.AnnAssign(annotation=annotation):
            target: ast.expr = (
                annotation.value
                if isinstance(annotation, ast.Subscript)
                else annotation
            )
            match target:
                case ast.Name(id=name):
                    return name in facts.final_names or name == "Final"
                case ast.Attribute(attr="Final", value=ast.Name(id=owner)):
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
        subject: Binding subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the statement is ``NAME = <scalar literal>``.

    """
    match subject.statement:
        case ast.Assign(targets=[ast.Name()], value=ast.Constant(value=value)):
            return isinstance(value, Constants.immutable_literals)
        case _:
            return False


def _is_assigned_once(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether the name is bound exactly once in the module.

    Args:
        subject: Binding subject.
        facts: Resolved imports and binding counts.

    Returns:
        Whether no other statement or scope rebinds the name.

    """
    return facts.binding_counts.get(subject.name, 0) == 1


def _final_is_spellable(_subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether ``Final`` can be written without clashing.

    Args:
        _subject: Unused binding subject.
        facts: Resolved imports and binding counts.

    Returns:
        Whether ``Final`` is imported already, reachable through the
        ``typing`` module, or otherwise unbound.

    """
    return (
        bool(facts.final_names or facts.typing_names)
        or facts.binding_counts.get("Final", 0) == 0
    )


def _is_type_declaration(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether an assignment declares a type, not a constant.

    Args:
        subject: Binding subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the value is a ``TypeVar``-style constructor call.

    """
    match subject.statement:
        case ast.Assign(value=ast.Call(func=func)):
            match func:
                case ast.Name(id=name) | ast.Attribute(attr=name):
                    return name in Constants.type_constructors
                case _:
                    return False
        case _:
            return False


def _annotation_missing(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a parameter or a function return lacks an annotation.

    Members of a synthesized ``Protocol`` are exempt: their types are open by
    construction, and flagging them would make ``fix`` and ``check`` disagree.

    Args:
        subject: Parameter or function subject.
        facts: Resolved structure of the module.

    Returns:
        Whether the annotation is missing; receivers are exempt.

    """
    function: ast.AST = (
        subject.statement if subject.kind == "Parameter" else subject.node
    ) or subject.node
    if _is_synthesized_member(function=function, facts=facts):
        return False
    match (subject.node, subject.statement):
        case [
            ast.arg(annotation=None, arg=name),
            ast.FunctionDef() | ast.AsyncFunctionDef() as owner,
        ]:
            first: list[ast.arg] = [*owner.args.posonlyargs, *owner.args.args]
            is_receiver: bool = (
                bool(first)
                and first[0] is subject.node
                and (name in {"self", "cls"})
            )
            return not is_receiver
        case [
            ast.FunctionDef(returns=None) | ast.AsyncFunctionDef(returns=None),
            _,
        ]:
            return subject.kind != "Parameter"
        case _:
            return False


def _returns_nothing(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a function provably returns ``None``.

    Args:
        subject: Function subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the function provably returns nothing.

    """
    match subject.node:
        case ast.FunctionDef() | ast.AsyncFunctionDef() as function:
            return returns_nothing(function=function)
        case _:
            return False


def _plain_parameter(
    subject: Subject,
    facts: ModuleFacts,
) -> tuple[ast.arg, ast.FunctionDef | ast.AsyncFunctionDef] | None:
    """Select unannotated, defaultless, non-variadic, non-receiver parameters.

    Args:
        subject: Candidate subject.
        facts: Resolved imports.

    Returns:
        The parameter and its function, or ``None`` for any other subject.

    """
    if subject.kind != "Parameter" or not _annotation_missing(subject=subject, facts=facts):
        return None
    match (subject.node, subject.statement):
        case [
            ast.arg() as parameter,
            ast.FunctionDef() | ast.AsyncFunctionDef() as function,
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
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter: ast.arg,
    facts: ModuleFacts,
) -> bool:
    """Tell whether a parameter may get a synthesized type.

    Refused: overload groups, dunder methods, the first parameter of any
    non-static method, and methods of classes with bases (they may override
    a signature that is not visible here).

    Args:
        function: Function that owns the parameter.
        parameter: The parameter.
        facts: Resolved structure of the module.

    Returns:
        ``True`` when synthesis cannot contradict another signature.

    """
    if id(function) in facts.overloaded:
        return False
    owner = facts.method_owner.get(id(function))
    if owner is None:
        return True
    dunder: bool = function.name.startswith("__") and function.name.endswith(
        "__",
    )
    static: bool = any(
        isinstance(item, ast.Name) and item.id == "staticmethod"
        for item in function.decorator_list
    )
    first: list[ast.arg] = [*function.args.posonlyargs, *function.args.args]
    is_first: bool = bool(first) and first[0] is parameter
    return not (dunder or bool(owner.bases) or (is_first and (not static)))


def _is_synthesized_member(*, function: ast.AST, facts: ModuleFacts) -> bool:
    """Tell whether a function is a member of a synthesized ``Protocol``.

    Args:
        function: Candidate function node.
        facts: Resolved structure of the module.

    Returns:
        ``True`` when the owning class carries the synthesized docstring.

    """
    owner = facts.method_owner.get(id(function))
    if owner is None:
        return False
    return (ast.get_docstring(node=owner) or "").startswith(
        ProtocolConstants.docstring_marker,
    )


def _has_structural_protocol(
    subject: Subject,
    facts: ModuleFacts,
) -> FactValue:
    """Report whether a parameter is used only through its attributes.

    Args:
        subject: Parameter subject.
        facts: Resolved imports and lazily computed hints.

    Returns:
        Whether a ``Protocol`` can be synthesized for it.

    """
    plain = _plain_parameter(subject=subject, facts=facts)
    if plain is None:
        return False
    parameter, function = plain
    if not _synthesis_allowed(
        function=function,
        parameter=parameter,
        facts=facts,
    ):
        return False
    usage = structural_usage(
        function=function,
        parameter=parameter.arg,
        counts=facts.binding_counts,
    )
    if usage is None:
        return False
    return (
        facts.hints is None
        or facts.hints.index().hint_for(node=parameter) is None
    )


def _is_passthrough(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a parameter only flows through to the return value.

    Args:
        subject: Parameter subject.
        facts: Resolved imports.

    Returns:
        Whether a type variable can describe the parameter and the return.

    """
    plain = _plain_parameter(subject=subject, facts=facts)
    if plain is None:
        return False
    parameter, function = plain
    if not _synthesis_allowed(
        function=function,
        parameter=parameter,
        facts=facts,
    ):
        return False
    return (
        passthrough_return(
            function=function,
            parameter=parameter.arg,
            variable="T",
            counts=facts.binding_counts,
        )
        is not None
    )


def _has_inferred_hint(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a corroborated hint other than ``None`` exists.

    Args:
        subject: Parameter or function subject.
        facts: Resolved imports and lazily computed hints.

    Returns:
        Whether an accepted hint is available for the node.

    """
    if facts.hints is None:
        return False
    hint = facts.hints.index().hint_for(node=subject.node)
    return hint is not None and hint.basis is not HintBasis.proven_none


def bound_call(subject: Subject, facts: ModuleFacts) -> BoundCall | None:
    """Bind a call to a function or class defined in this module.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    Returns:
        The bound call, or ``None`` when the callee is not defined here.

    """
    match subject.node:
        case ast.Call() as call if facts.calls is not None:
            return facts.calls.get(call=call)
        case _:
            return None


def keyword_candidates(subject: Subject, facts: ModuleFacts) -> list[str]:
    """List parameters passed positionally that could be keywords.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    Returns:
        Parameter names, in declaration order.

    """
    bound: BoundCall | None = bound_call(subject=subject, facts=facts)
    if bound is None:
        return []
    if any(
        argument.origin is ArgumentOrigin.VAR_POSITIONAL and argument.values
        for argument in bound.arguments
    ):
        return []
    if any(
        isinstance(arg, ast.Starred) for arg in _call_args(subject=subject)
    ):
        return []
    return [
        argument.parameter.name
        for argument in bound.arguments
        if argument.origin is ArgumentOrigin.POSITIONAL
        and argument.parameter.kind is ParameterKind.POSITIONAL_OR_KEYWORD
    ]


def _candidate_count(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Count parameters passed positionally that could be keywords.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    Returns:
        The number of such parameters.

    """
    return len(keyword_candidates(subject=subject, facts=facts))


def _is_resolved(subject: Subject, facts: ModuleFacts) -> FactValue:
    """Report whether a call's callee is defined in this module.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    Returns:
        Whether the call binds to a local definition.

    """
    return bound_call(subject=subject, facts=facts) is not None


def _has_docstring(subject: Subject, _facts: ModuleFacts) -> FactValue:
    """Report whether a function has a docstring.

    Args:
        subject: Function subject.
        _facts: Unused resolved imports.

    Returns:
        Whether the function body starts with a docstring.

    """
    match subject.node:
        case ast.FunctionDef() | ast.AsyncFunctionDef() as function:
            return ast.get_docstring(node=function) is not None
        case _:
            return False


def _undocumented(subject: Subject, facts: ModuleFacts) -> list[str]:
    """List parameters missing from the docstring's parameter sections.

    Args:
        subject: Function subject.
        facts: Resolved imports and the parsed module.

    Returns:
        Undocumented parameter names, without stars, in declaration order.

    """
    match subject.node:
        case ast.FunctionDef() | ast.AsyncFunctionDef() as function:
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
    arguments: ast.arguments = function.args
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
        subject: Function subject.
        facts: Resolved imports and the parsed module.

    Returns:
        The number of undocumented parameters.

    """
    return len(_undocumented(subject=subject, facts=facts))


def name_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``name`` evidence slot.

    Args:
        subject: Subject being reported.
        _facts: Unused resolved imports.

    Returns:
        The bound or annotated name.

    """
    return subject.name


def callee_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``callee`` evidence slot.

    Args:
        subject: Call subject.
        _facts: Unused resolved imports.

    Returns:
        The callee as written.

    """
    return subject.name


def function_evidence(subject: Subject, _facts: ModuleFacts) -> JsonValue:
    """Provide the ``function`` evidence slot.

    Args:
        subject: Function subject.
        _facts: Unused resolved imports.

    Returns:
        The qualified function path.

    """
    return subject.path


def call_parameters_evidence(
    subject: Subject,
    facts: ModuleFacts,
) -> JsonValue:
    """Provide the ``parameters`` slot of a call finding.

    Args:
        subject: Call subject.
        facts: Resolved imports and the parsed module.

    Returns:
        Parameter names that should be passed by keyword.

    """
    match subject.node:
        case ast.Call():
            return list(keyword_candidates(subject=subject, facts=facts))
        case _:
            return list(_undocumented(subject=subject, facts=facts))


@final
class Registry:
    """Group the engine's fact specifications and providers.

    Attributes:
        specs: Declarations of every fact.
        providers: Provider function for every fact.
        evidence: Provider function for every evidence slot.

    """

    specs: Final[tuple[FactSpec, ...]] = (
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
            name="annotation.has_inferred_hint",
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
            name="function.has_docstring",
            value_type="bool",
            cost=Cost.syntactic,
        ),
        FactSpec(
            name="function.undocumented_parameter_count",
            value_type="int",
            cost=Cost.syntactic,
        ),
    )
    providers: Final[Mapping[str, FactProvider]] = {
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
        "annotation.has_inferred_hint": _has_inferred_hint,
        "parameter.has_structural_protocol": _has_structural_protocol,
        "parameter.is_passthrough": _is_passthrough,
        "call.positional_keyword_candidates": _candidate_count,
        "call.is_resolved_in_module": _is_resolved,
        "function.has_docstring": _has_docstring,
        "function.undocumented_parameter_count": _undocumented_count,
    }
    evidence: Final[Mapping[str, EvidenceProvider]] = {
        "name": name_evidence,
        "callee": callee_evidence,
        "function": function_evidence,
        "parameters": call_parameters_evidence,
    }


def default_registries() -> Registries:
    """Build the registries describing this engine.

    Returns:
        Node kinds, facts, appliers and no procedures.

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
        module: Parsed module.
        kinds: Subject kinds to enumerate.

    Returns:
        Subjects in traversal order.

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
    node: ast.AST,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Visit one node and its children, emitting subjects.

    Args:
        node: Node to visit.
        kinds: Subject kinds to enumerate.
        site: Enclosing scope trail and kind.
        out: Destination list, extended in place.

    """
    kind: str = type(node).__name__
    inner: _Site = site
    match node:
        case ast.FunctionDef() | ast.AsyncFunctionDef():
            _emit_function(node=node, kinds=kinds, site=site, out=out)
            inner = _Site(trail=(*site.trail, node.name), scope="function")
        case ast.ClassDef():
            if kind in kinds:
                out.append(site.subject(kind=kind, node=node, name=node.name))
            inner = _Site(trail=(*site.trail, node.name), scope="class")
        case ast.Assign():
            if kind in kinds:
                out.extend(
                    site.subject(
                        kind=kind,
                        node=target,
                        name=target.id,
                        statement=node,
                    )
                    for target in node.targets
                    if isinstance(target, ast.Name)
                )
        case ast.AnnAssign():
            _emit_annotated(node=node, kinds=kinds, site=site, out=out)
        case ast.Call() | ast.Module():
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
    for child in ast.iter_child_nodes(node=node):
        _visit(node=child, kinds=kinds, site=inner, out=out)


@final
@dataclass(frozen=True, slots=True)
class _Site:
    """Position in the scope tree where subjects are created.

    Attributes:
        trail: Qualified names of the enclosing scopes.
        scope: Enclosing scope kind.

    """

    trail: tuple[str, ...]
    scope: str

    def subject(
        self,
        kind: str,
        node: ast.AST,
        name: str,
        statement: ast.AST | None = None,
    ) -> Subject:
        """Build a subject whose path extends the scope trail.

        Args:
            kind: Subject kind.
            node: Node the rule reports on.
            name: Name of the subject.
            statement: Owning statement when different from the node.

        Returns:
            The subject.

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


def _call_args(subject: Subject) -> list[ast.expr]:
    """Return the positional argument expressions of a call subject.

    Args:
        subject: Call subject.

    Returns:
        The arguments, empty for non-call subjects.

    """
    match subject.node:
        case ast.Call(args=args):
            return list(args)
        case _:
            return []


def _call_name(node: ast.AST) -> str:
    """Name a subject node for path purposes.

    Args:
        node: Call or module node.

    Returns:
        The callee text for calls, empty for modules.

    """
    match node:
        case ast.Call(func=func):
            return ast.unparse(ast_obj=func)
        case _:
            return ""


def _emit_function(
    *,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Emit the function subject and its annotation subjects.

    Args:
        node: Function definition.
        kinds: Subject kinds to enumerate.
        site: Scope the function is defined in.
        out: Destination list, extended in place.

    """
    kind: str = type(node).__name__
    if kind in kinds:
        out.append(site.subject(kind=kind, node=node, name=node.name))
    if not kinds & {"Annotation", "Parameter"}:
        return
    inner: _Site = _Site(trail=(*site.trail, node.name), scope="function")
    arguments: ast.arguments = node.args
    parameters: list[ast.arg] = [
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
    node: ast.AnnAssign,
    kinds: frozenset[str],
    site: _Site,
    out: list[Subject],
) -> None:
    """Emit subjects for an annotated assignment.

    Args:
        node: Annotated assignment.
        kinds: Subject kinds to enumerate.
        site: Scope the assignment is in.
        out: Destination list, extended in place.

    """
    if not isinstance(node.target, ast.Name):
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
        subjects: Subjects in traversal order.

    Returns:
        The subjects with distinct paths per kind.

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
