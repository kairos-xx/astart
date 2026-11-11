"""Feed project-wide call evidence into per-module hint judging.

The project index knows calls in every file; :class:`ProjectView` turns
one module's slice of them into the same kind of per-site evidence the
local call machinery produces. Only what the argument's syntax proves in
the *caller's* scope counts — the inference engine's own types are not
independent evidence. Unresolvable expansions and ambiguous callees
produce unknown evidence, never evidence of absence.

"""

from __future__ import annotations

from ast import (
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    FunctionDef,
    Module,
    Name,
    expr,
    iter_child_nodes,
)
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, final

from astart.rules.methods import dataclass_init_names
from astart.rules.provable import (
    expression_type,
    module_constants,
    scope_types,
)
from astart.rules.resolve import binding_counts, definition_is_plain
from astart.semantic.parameter_kinds import ParameterKind
from astart.semantic.type_shapes import TypeShape, atomic
from astart.semantic.typing_contracts import (
    ArgumentOrigin,
    BoundArgument,
    CallableContract,
    ParameterContract,
    bind_signature,
    function_contract,
)

type DictInt = dict[str, int]
type DictStr = dict[str, str]

if TYPE_CHECKING:
    from ast import AST

    from astart.project.index import (
        CallRecord,
        Definition,
        ProjectIndex,
    )
    from astart.project.libraries import LibraryIndex
    from astart.project.scan import ModuleScan
    from astart.project.table import ResolvedSymbol
    from astart.semantic.typing_contracts import BoundCall


@final
class Constants:
    """Group module-level constants.

    Attributes:
        variadic_origins (Final[frozenset[ArgumentOrigin]]): Origins of
            arguments bound to ``*args`` and ``**kwargs``.
        shape_specific (Final[str]): Prefix of literal exact-shape types
            that say nothing about other callers.
        instance_kinds (Final[frozenset[str]]): Method kinds whose leading
            parameter is an implicit receiver.
        unknown (Final[TypeShape]): Shape handed to the binder for every call
            argument; the evidence layer only reads argument
            syntax, so the abstract shape is never consulted.

    """

    variadic_origins: Final[frozenset[ArgumentOrigin]] = frozenset(
        {ArgumentOrigin.VAR_POSITIONAL, ArgumentOrigin.VAR_KEYWORD},
    )
    shape_specific: Final[str] = "tuple["
    instance_kinds: Final[frozenset[str]] = frozenset(
        {"instance", "class"},
    )
    unknown: Final[TypeShape] = atomic(name="Unknown")


@final
@dataclass(frozen=True, slots=True)
class CrossSite:
    """What one cross-module call shows about one parameter.

    Mirrors the local call-site record the hint layer uses.

    Attributes:
        definite (bool): Whether the argument type is trustworthy.
        types (tuple[str, ...]): Rendered type spellings.
        proven (bool): Whether the argument expression's syntax alone proves
            the type.

    """

    definite: bool
    types: tuple[str, ...]
    proven: bool


def qualified_names(
    *,
    module: Module,
    name: str,
) -> dict[int, str]:
    """Map each definition in a module to its project-qualified name.

    Args:
        module (Module): Parsed module.
        name (str): The module's dotted name inside the project.

    Returns:
        dict[int, str]: ``id`` to ``"pkg.mod.outer.inner"`` for every
            function and class definition, nested ones included.

    """
    found: dict[int, str] = {}

    def visit(*, node: AST, prefix: str) -> None:
        """Record nested definitions under their qualified path.

        Args:
            node (AST): Node to walk.
            prefix (str): Qualified name of the enclosing scope.

        """
        for child in iter_child_nodes(node=node):
            if isinstance(child, (FunctionDef, AsyncFunctionDef, ClassDef)):
                qualified: str = f"{prefix}.{child.name}"
                found[id(child)] = qualified
                visit(node=child, prefix=qualified)
            else:
                visit(node=child, prefix=prefix)

    visit(node=module, prefix=name)
    return found


@final
@dataclass(frozen=True, slots=True)
class _Callable:
    """How one resolved callee binds its arguments.

    Attributes:
        contract (CallableContract): The callee's signature.
        receiver (str | None): Qualified name of the receiver class for method
            calls whose object
            is constructed at the call (``C().m(...)``) and for constructor
            calls (``C(...)``), or ``None`` when no implicit receiver exists.
        constructor (bool): Whether the callee is a class — constructor calls
            always bind the receiver implicitly, unlike ``C.m(...)``
            method references.

    """

    contract: CallableContract
    receiver: str | None
    constructor: bool = False


@final
@dataclass(slots=True)
class _EnvCache:
    """Caller-scope types computed once per calling module.

    Attributes:
        counts (dict[str, DictInt]): ``binding_counts`` of each calling module.
        constants (dict[str, DictStr]): ``module_constants`` of each calling
            module.
        envs (dict[str, DictStr]): ``scope_types`` of each calling scope, or
            module
            constants for top-level and class-body calls.

    """

    counts: dict[str, DictInt] = field(
        default_factory=dict[str, dict[str, int]],
    )
    constants: dict[str, DictStr] = field(
        default_factory=dict[str, dict[str, str]],
    )
    envs: dict[str, DictStr] = field(
        default_factory=dict[str, dict[str, str]],
    )


@final
class ProjectView:
    """One module's view of a whole-project index.

    The view is the bridge object passed through ``CheckOptions`` and
    ``FixSettings``: it knows which module is being analysed, so
    :meth:`sites` returns only *cross*-module calls — same-module calls
    stay with the local binding machinery. Caller-scope types are
    memoized per view because they cannot change while a module is being
    judged.

    """

    def __init__(
        self,
        *,
        index: ProjectIndex,
        module: str,
        libraries: LibraryIndex | None = None,
    ) -> None:
        """Bind the view to one module of the project.

        Args:
            index (ProjectIndex): Whole-project index.
            module (str): Dotted name of the module being analysed.
            libraries (LibraryIndex | None): External signature index for
                callees
                outside the project, or ``None``.

        """
        self.index: ProjectIndex = index
        self.module: str = module
        self.libraries: LibraryIndex | None = libraries
        self._envs: _EnvCache = _EnvCache()
        self._contracts: dict[str, _Callable | None] = {}
        self._sites: dict[str, dict[str, tuple[CrossSite, ...]] | None] = {}

    def open_world(self, *, qualified: str) -> bool:
        """Whether a definition's callers may be incomplete.

        Args:
            qualified (str): Qualified name in this module.

        Returns:
            bool: Whether outside callers could exist.

        """
        return self.index.open_world(qualified=qualified)

    def resolve_local(self, *, name: str) -> ResolvedSymbol | None:
        """Resolve a name as this module sees it.

        Args:
            name (str): Local name in the analysed module.

        Returns:
            ResolvedSymbol | None: The resolution, or ``None``.

        """
        return self.index.table.resolve(module=self.module, name=name)

    def sites(
        self,
        *,
        qualified: str,
    ) -> dict[str, tuple[CrossSite, ...]] | None:
        """Cross-module call-site evidence for one project definition.

        Args:
            qualified (str): Qualified name of a function or class defined in
                the analysed module.

        Returns:
            dict[str, tuple[CrossSite, ...]] | None:
                Per-parameter evidence from calls in *other* modules,
                or ``None`` when the callee cannot be bound at all (a
                decorated signature, an inherited constructor), which
                counts as no evidence rather than unknown evidence.

        """
        if qualified not in self._sites:
            self._sites[qualified] = self._compute_sites(qualified=qualified)
        return self._sites[qualified]

    def binding(self, *, call: Call) -> BoundCall | None:
        """Bind one of this module's calls to a project or library callee.

        Same-module calls stay with ``CallBindings``; this answers calls
        that resolve through the symbol table — a project function,
        method or constructor — plus external callees whose contract a
        library index declares.

        Args:
            call (Call): The call node, owned by this module.

        Returns:
            BoundCall | None: The bound call, or ``None`` when the callee
                cannot be resolved to a trusted contract.

        """
        resolved: ResolvedSymbol | None = self.index.resolve_callee(
            module=self.module,
            func=call.func,
        )
        if resolved is None:
            return None
        callable_: _Callable | None
        if resolved.external:
            contract: CallableContract | None = (
                self.libraries.contract(qualified_name=resolved.qualified)
                if self.libraries is not None
                else None
            )
            callable_ = (
                None
                if contract is None
                else _Callable(
                    contract=contract,
                    receiver=None,
                )
            )
        else:
            callable_ = self._callable(qualified=resolved.qualified)
        if callable_ is None:
            return None
        return bind_signature(
            call=call,
            signature=callable_.contract,
            positional_types=(Constants.unknown,) * len(call.args),
            keyword_types=tuple(
                (part.arg, Constants.unknown) for part in call.keywords
            ),
            receiver_type=(
                atomic(name=callable_.receiver)
                if callable_.receiver is not None
                and _implicit_receiver(func=call.func, callee=callable_)
                else None
            ),
        )

    def _compute_sites(
        self,
        *,
        qualified: str,
    ) -> dict[str, tuple[CrossSite, ...]] | None:
        """Produce cross-module sites for one callee.

        Args:
            qualified (str): Qualified callee name.

        Returns:
            dict[str, tuple[CrossSite, ...]] | None:
                Per-parameter evidence, or ``None`` when unbindable.

        """
        callable_: _Callable | None = self._callable(qualified=qualified)
        if callable_ is None:
            return None
        out: dict[str, list[CrossSite]] = {}
        for record in self.index.records_for(qualified=qualified):
            if record.module == self.module:
                continue
            bound: BoundCall = bind_signature(
                call=record.node,
                signature=callable_.contract,
                positional_types=(Constants.unknown,) * len(record.node.args),
                keyword_types=tuple(
                    (part.arg, Constants.unknown)
                    for part in record.node.keywords
                ),
                receiver_type=(
                    atomic(name=callable_.receiver)
                    if callable_.receiver is not None
                    and _implicit_receiver(
                        func=record.node.func,
                        callee=callable_,
                    )
                    else None
                ),
            )
            counts: DictInt = self._counts(module=record.module)
            env: DictStr = self._env(record=record, counts=counts)
            for argument in bound.arguments:
                site: CrossSite | None = _bound(
                    argument=argument,
                    counts=counts,
                    env=env,
                )
                if site is not None:
                    out.setdefault(argument.parameter.name, []).append(site)
        return {name: tuple(sites) for name, sites in out.items()}

    def _callable(self, *, qualified: str) -> _Callable | None:
        """Return the binding contract for a resolved callee.

        Args:
            qualified (str): Qualified callee name.

        Returns:
            _Callable | None: The contract plus implicit receiver, or ``None``
                when the callee cannot be trusted to keep its
                declared signature (decorated) or has no statically
                known parameters (inherited constructor).

        """
        if qualified in self._contracts:
            return self._contracts[qualified]
        self._contracts[qualified] = self._find_callable(qualified=qualified)
        return self._contracts[qualified]

    def _find_callable(self, *, qualified: str) -> _Callable | None:
        """Compute the contract for one callee.

        Args:
            qualified (str): Qualified callee name.

        Returns:
            _Callable | None: The contract plus implicit receiver, or ``None``.

        """
        definition: Definition | None = self.index.definition(
            qualified=qualified,
        )
        owner, _, _leaf = qualified.rpartition(".")
        owner_def: Definition | None = self.index.definition(
            qualified=owner,
        )
        if isinstance(definition, (FunctionDef, AsyncFunctionDef)):
            if not definition_is_plain(declaration=definition):
                return None
            kind: str = (
                _method_kind(definition=definition)
                if isinstance(owner_def, ClassDef)
                else "function"
            )
            return _Callable(
                contract=function_contract(
                    node=definition,
                    qualified_name=qualified,
                    method_kind=kind,
                ),
                receiver=owner if kind in Constants.instance_kinds else None,
            )
        if isinstance(definition, ClassDef):
            if definition.decorator_list and (
                dataclass_init_names(cls=definition) is None
            ):
                return None
            return _constructor(definition=definition, qualified=qualified)
        return None

    def _counts(self, *, module: str) -> DictInt:
        """Binding counts of a calling module, computed once.

        Args:
            module (str): Calling module name.

        Returns:
            DictInt: The counts.

        """
        if module not in self._envs.counts:
            scan: ModuleScan | None = self.index.module_scan(module=module)
            self._envs.counts[module] = (
                binding_counts(module=scan.tree) if scan is not None else {}
            )
        return self._envs.counts[module]

    def _env(
        self,
        *,
        record: CallRecord,
        counts: DictInt,
    ) -> DictStr:
        """Types of names visible where one call executes.

        Args:
            record (CallRecord): The call's record.
            counts (DictInt): Binding counts of the calling module.

        Returns:
            DictStr: Types by name.

        """
        if record.caller in self._envs.envs:
            return self._envs.envs[record.caller]
        constants: DictStr | None = self._envs.constants.get(
            record.module,
        )
        if constants is None:
            scan: ModuleScan | None = self.index.module_scan(
                module=record.module,
            )
            constants = (
                module_constants(module=scan.tree, counts=counts)
                if scan is not None
                else {}
            )
            self._envs.constants[record.module] = constants
        scope: Definition | None = self.index.definition(
            qualified=record.caller,
        )
        env: DictStr = (
            scope_types(
                function=scope,
                counts=counts,
                constants=constants,
            )
            if isinstance(scope, (FunctionDef, AsyncFunctionDef))
            else dict(constants)
        )
        self._envs.envs[record.caller] = env
        return env


def _implicit_receiver(*, func: expr, callee: _Callable) -> bool:
    """Whether one call's callee gets an implicit receiver.

    Constructors (``C(...)``) always do; so do constructor-method calls
    (``C().m(...)``). Plain ``C.m(...)`` calls pass the receiver
    explicitly.

    Args:
        func (expr): The call's ``func`` expression.
        callee (_Callable): The resolved callee's binding contract.

    Returns:
        bool: Whether the binding supplies the receiver itself.

    """
    if callee.constructor:
        return True
    return isinstance(func, Attribute) and isinstance(func.value, Call)


def _method_kind(*, definition: FunctionDef | AsyncFunctionDef) -> str:
    """Classify a method by its decorators.

    Args:
        definition (FunctionDef | AsyncFunctionDef): Method definition inside a
            class.

    Returns:
        str: ``"staticmethod"``, ``"classmethod"`` or ``"instance"``.

    """
    names: set[str] = set()
    for decorator in definition.decorator_list:
        match decorator:
            case Name(id=name):
                names.add(name)
            case Attribute(attr=attr):
                names.add(attr)
            case _:
                continue
    if "staticmethod" in names:
        return "staticmethod"
    if "classmethod" in names:
        return "classmethod"
    return "instance"


def _constructor(
    *,
    definition: ClassDef,
    qualified: str,
) -> _Callable | None:
    """Build a class's constructor contract.

    ``__init__`` wins over ``__new__``; with neither, a plain dataclass's
    generated parameters are used. Inherited constructors are unknown —
    the class's bases are not chased.

    Args:
        definition (ClassDef): Class definition.
        qualified (str): Qualified class name.

    Returns:
        _Callable | None: The contract, or ``None``.

    """
    for statement in definition.body:
        if isinstance(statement, (FunctionDef, AsyncFunctionDef)):
            if statement.name == "__init__":
                return _Callable(
                    contract=function_contract(
                        node=statement,
                        qualified_name=qualified,
                        method_kind="instance",
                    ),
                    receiver=qualified,
                    constructor=True,
                )
            if statement.name == "__new__":
                return _Callable(
                    contract=function_contract(
                        node=statement,
                        qualified_name=qualified,
                        method_kind="class",
                    ),
                    receiver=qualified,
                    constructor=True,
                )
    names: list[str] | None = dataclass_init_names(cls=definition)
    if names is None:
        return None
    return _Callable(
        contract=CallableContract(
            qualified_name=qualified,
            parameters=tuple(
                ParameterContract(
                    name=name,
                    kind=ParameterKind.POSITIONAL_OR_KEYWORD,
                )
                for name in names
            ),
            declaration=definition,
        ),
        receiver=None,
        constructor=True,
    )


def _bound(
    *,
    argument: BoundArgument,
    counts: DictInt,
    env: DictStr,
) -> CrossSite | None:
    """Turn one bound cross-module argument into evidence, if any.

    Same rules as the local layer: unresolvable expansions are unknown
    evidence, defaults and missing arguments carry no evidence, and only
    what the argument's own syntax proves counts.

    Args:
        argument (BoundArgument): Bound argument of a direct call.
        counts (DictInt): Binding counts of the calling module.
        env (DictStr): Types of names visible where the call executes.

    Returns:
        CrossSite | None: The site, or ``None`` when the argument says nothing.

    """
    origin: ArgumentOrigin = argument.origin
    if origin in Constants.variadic_origins:
        if not argument.definite:
            return CrossSite(definite=False, types=(), proven=False)
        if not argument.values:
            return None
    elif origin is ArgumentOrigin.EXPANSION_UNKNOWN:
        return CrossSite(definite=False, types=(), proven=False)
    elif origin not in (ArgumentOrigin.POSITIONAL, ArgumentOrigin.KEYWORD):
        return None
    proofs: set[str | None] = {
        expression_type(node=value, counts=counts, env=env)
        for value in argument.values
    }
    syntax: str | None = (
        next(iter(proofs))
        if argument.values and len(proofs) == 1 and None not in proofs
        else None
    )
    if syntax is None or syntax.startswith(Constants.shape_specific):
        return CrossSite(definite=False, types=(), proven=False)
    return CrossSite(definite=True, types=(syntax,), proven=True)
