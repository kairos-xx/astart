"""Resolve method calls that the analyzer does not bind, or binds loosely.

A call is only trusted when nothing in the module can make it reach another
signature: the method is defined once, every definition of that name takes the
same parameters, and no instance attribute of that name is ever assigned.

"""

from __future__ import annotations

from ast import (
    AST,
    AnnAssign,
    AsyncFunctionDef,
    Attribute,
    Call,
    ClassDef,
    Constant,
    Del,
    FunctionDef,
    Import,
    ImportFrom,
    Lambda,
    Load,
    Name,
    Starred,
    Store,
    Subscript,
    arg,
    expr,
    iter_child_nodes,
    walk,
)
from ast import (
    arguments as ast_arguments,
)
from builtins import __dict__
from typing import TYPE_CHECKING, Final, final

from astart.rules.scopes import names_bound_by
from astart.semantic import (
    ArgumentOrigin,
    BoundArgument,
    BoundCall,
    CallableContract,
    ParameterContract,
    ParameterKind,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from astart import CommentedModule

    type Function = FunctionDef | AsyncFunctionDef
    type Shape = tuple[tuple[str, ...], str | None, str | None]


@final
class Constants:
    """Group module-level constants.

    Attributes:
        neutral_options (Final[frozenset[str | None]]): ``@dataclass`` options
            that do not change ``__init__``.
        init_methods (Final[frozenset[str]]): Method names that replace the
            generated ``__init__``.
        name_rebinders (Final[frozenset[str]]): Builtins that can rebind
            module-level names.
        name_readers (Final[frozenset[str]]): Dict methods that only read a
            namespace view.
        namespace_views (Final[frozenset[str]]): Builtins that return a view of
            a namespace, which
            only rebinds names when it is written or kept.
        attribute_rebinders (Final[frozenset[str]]): Builtins that can rebind
            attributes.
        attribute_hooks (Final[frozenset[str]]): Attributes whose use can
            rebind or intercept others.
        interceptors (Final[frozenset[str]]): Methods that intercept every
            attribute access.
        attribute_defs (Final[frozenset[str]]): Methods that customise
            attribute writes or misses.
        safe_decorators (Final[frozenset[str]]): Class decorators that keep
            ``__init__`` as written.
        safe_bases (Final[frozenset[str]]): External bases that do not change
            construction.

    """

    neutral_options: Final[frozenset[str | None]] = frozenset(
        {
            "frozen",
            "order",
            "eq",
            "slots",
            "repr",
            "unsafe_hash",
            "match_args",
        },
    )
    init_methods: Final[frozenset[str]] = frozenset({"__init__", "__new__"})
    name_rebinders: Final[frozenset[str]] = frozenset(
        {"globals", "vars", "locals", "exec", "eval"},
    )
    name_readers: Final[frozenset[str]] = frozenset(
        {"get", "keys", "values", "items", "copy"},
    )
    namespace_views: Final[frozenset[str]] = frozenset(
        {"globals", "vars", "locals"},
    )
    attribute_rebinders: Final[frozenset[str]] = frozenset(
        {"setattr", "delattr", "vars", "exec", "eval"},
    )
    attribute_hooks: Final[frozenset[str]] = frozenset(
        {"__setattr__", "__delattr__", "__dict__", "__class__"},
    )
    interceptors: Final[frozenset[str]] = frozenset({"__getattribute__"})
    attribute_defs: Final[frozenset[str]] = frozenset(
        {"__setattr__", "__delattr__", "__getattr__"},
    )
    safe_decorators: Final[frozenset[str]] = frozenset({"dataclass", "final"})
    safe_bases: Final[frozenset[str]] = frozenset(
        {
            "ABC",
            "BaseException",
            "Exception",
            "Generic",
            "NamedTuple",
            "object",
        },
    )


def _shape(*, function: Function) -> Shape:
    """Describe the parameter names a function accepts.

    Args:
        function (Function): Function definition.

    Returns:
        Shape: Positional and keyword-only names,
            then ``*args`` and ``**kwargs``.

    """
    arguments: ast_arguments = function.args
    names: tuple[str, ...] = tuple(
        item.arg
        for item in (
            *arguments.posonlyargs,
            *arguments.args,
            *arguments.kwonlyargs,
        )
    )
    return (
        names,
        arguments.vararg.arg if arguments.vararg else None,
        arguments.kwarg.arg if arguments.kwarg else None,
    )


@final
class MethodIndex:
    """Facts about the classes and methods of one module."""

    def __init__(
        self,
        *,
        module: CommentedModule,
        counts: Mapping[str, int],
    ) -> None:
        """Index the module once.

        Args:
            module (CommentedModule): Parsed module.
            counts (Mapping[str, int]): Binding counts from ``binding_counts``.

        """
        self._module: CommentedModule = module
        self._parents: dict[int, AST] = {}
        self._classes: dict[str, ClassDef] = {}
        self._defs: dict[str, list[Function]] = {}
        self._stored: set[str] = set()
        self._dynamic_names: bool = False
        self._dynamic_attributes: bool = False
        self._intercepts: bool = False
        for node in walk(node=module):
            for child in ast_children(node=node):
                self._parents[id(child)] = node
            if isinstance(node, ClassDef) and counts.get(node.name) == 1:
                self._classes[node.name] = node
            elif isinstance(node, (FunctionDef, AsyncFunctionDef)):
                self._defs.setdefault(node.name, []).append(node)
                self._intercepts = self._intercepts or (
                    node.name in Constants.interceptors
                )
            elif isinstance(node, Attribute):
                if isinstance(node.ctx, (Store, Del)):
                    self._stored.add(node.attr)
                if node.attr in Constants.attribute_hooks:
                    self._dynamic_attributes = True
            elif isinstance(node, Call) and isinstance(node.func, Name):
                self._dynamic_names = self._dynamic_names or (
                    node.func.id in Constants.name_rebinders
                    and not self._only_reads(call=node)
                )
                self._dynamic_attributes = self._dynamic_attributes or (
                    node.func.id in Constants.attribute_rebinders
                )

    def _only_reads(self, *, call: Call) -> bool:
        """Tell whether a namespace-view call is used only to read names.

        ``globals()["f"]`` and ``globals().get("f")`` cannot rebind a name;
        a store, ``update``, an alias, or ``exec``/``eval`` can.

        Args:
            call (Call): A call of ``globals`` , ``vars`` ,
                ``locals``, ``exec`` or ``eval``.

        Returns:
            bool: ``True`` when the call only reads from the view.

        """
        if not (
            isinstance(call.func, Name)
            and call.func.id in Constants.namespace_views
        ):
            return False
        parent: AST | None = self._parents.get(id(call))
        if isinstance(parent, Subscript) and parent.value is call:
            return isinstance(parent.ctx, Load)
        return (
            isinstance(parent, Attribute)
            and parent.value is call
            and parent.attr in Constants.name_readers
        )

    def is_class_name(self, *, name: str) -> bool:
        """Tell whether a name is a class defined once in the module.

        Args:
            name (str): Candidate name.

        Returns:
            bool: ``True`` for a module class bound exactly once.

        """
        return name in self._classes

    def is_safe(self, *, call: Call, declaration: AST) -> bool:
        """Tell whether an attribute call can only reach one signature.

        Args:
            call (Call): Attribute call.
            declaration (AST): Definition the call was bound to.

        Returns:
            bool: ``True`` when every definition of the name takes the same
                parameters and no instance attribute of that name is assigned.

        """
        if not isinstance(call.func, Attribute):
            return True
        if not isinstance(declaration, (FunctionDef, AsyncFunctionDef)):
            return True
        name: str = call.func.attr
        if (
            name in self._stored
            or self._dynamic_attributes
            or self._intercepts
        ):
            return False
        owner: AST | None = self._parents.get(id(declaration))
        if (
            isinstance(owner, ClassDef)
            and self._binds(
                owner=owner,
                name=name,
            )
            != 1
        ):
            return False
        shape: Shape = _shape(function=declaration)
        return all(
            _shape(function=other) == shape
            for other in self._defs.get(name, [])
        )

    @property
    def dynamic_attributes(self) -> bool:
        """Tell whether the module can rebind attributes behind the binder.

        Returns:
            bool: ``True`` when ``setattr`` , ``__dict__`` ,
                ``__class__`` writes or similar appear anywhere.

        """
        return self._dynamic_attributes or any(
            hook in self._defs for hook in Constants.attribute_defs
        )

    @property
    def intercepts(self) -> bool:
        """Tell whether some class intercepts every attribute access.

        Returns:
            bool: ``True`` when a ``__getattribute__`` is defined.

        """
        return self._intercepts

    def class_ok(self, *, cls: ClassDef) -> bool:
        """Tell whether a class's instance attributes can be reasoned about.

        Returns:
            bool: ``True`` for a module class bound once,
                with no decorators beyond ``final``, no
                construction hooks and only trusted bases.

        """
        return (
            self._classes.get(cls.name) is cls
            and all(
                _simple_name(node=_decorator_target(node=item)) == "final"
                for item in cls.decorator_list
            )
            and self._chain_safe(_cls=cls, seen=set())
        )

    def inherited_names(self, *, _cls: ClassDef) -> set[str]:
        """List the names the in-module bases of a class already define.

        Args:
            _cls (ClassDef): Class definition.

        Returns:
            set[str]: Method, class-level and instance attribute names of the
                bases.

        """
        names: set[str] = set()
        pending: list[ClassDef] = list(self._base_classes(_cls=_cls))
        seen: set[int] = set()
        while pending:
            base: ClassDef = pending.pop()
            if id(base) in seen:
                continue
            seen.add(id(base))
            for node in walk(node=base):
                if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
                    names.add(node.name)
                elif isinstance(node, Name) and isinstance(node.ctx, Store):
                    names.add(node.id)
                elif isinstance(node, Attribute) and isinstance(
                    node.ctx,
                    Store,
                ):
                    names.add(node.attr)
            pending.extend(self._base_classes(_cls=base))
        return names

    def _base_classes(self, *, _cls: ClassDef) -> list[ClassDef]:
        """List the module classes named in a class's base list.

        Args:
            _cls (ClassDef): Class definition.

        Returns:
            list[ClassDef]: The bases that are module classes.

        """
        found: list[ClassDef] = []
        for base in _cls.bases:
            label: str | None = _simple_name(
                node=base.value if isinstance(base, Subscript) else base,
            )
            if label in self._classes:
                found.append(self._classes[label])
        return found

    def binds(self, *, owner: ClassDef, name: str) -> int:
        """Count the ways a class body binds a name.

        Args:
            owner (ClassDef): Class definition.
            name (str): Attribute name.

        Returns:
            int: How many times the body defines, assigns or deletes it.

        """
        return self._binds(owner=owner, name=name)

    @staticmethod
    def _binds(*, owner: ClassDef, name: str) -> int:
        """Count the ways a class body binds a name.

        Definitions, assignments, ``del``, loop and ``with`` targets and
        imports all count; the bodies of nested functions and classes do not.

        Args:
            owner (ClassDef): Class definition.
            name (str): Attribute name.

        Returns:
            int: How many times the body binds or deletes the name.

        """
        total: int = 0
        stack: list[AST] = list(reversed(owner.body))
        while stack:
            node: AST = stack.pop()
            if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
                total += int(node.name == name)
                continue
            if isinstance(node, Lambda):
                continue
            if isinstance(node, Name) and isinstance(node.ctx, (Store, Del)):
                total += int(node.id == name)
            elif isinstance(node, (Import, ImportFrom)):
                total += sum(
                    1
                    for alias in node.names
                    if (alias.asname or alias.name.split(sep=".")[0]) == name
                )
            stack.extend(iter_child_nodes(node=node))
        return total

    def callee_allowed(self, *, call: Call) -> bool:
        """Tell whether a call's callee can be trusted at all in this module.

        A bare name is distrusted when the module can rebind names behind the
        binder's back (``globals()``, ``exec``…). A module class is trusted
        only when nothing in it or its bases changes construction.

        Args:
            call (Call): Call expression.

        Returns:
            bool: ``False`` when the call must keep its positional form.

        """
        func: AST = call.func
        if not isinstance(func, Name):
            return True
        if func.id in self._classes:
            return self.constructor_safe(name=func.id) and not (
                self._dynamic_attributes
            )
        return not self._dynamic_names

    def constructor_safe(self, *, name: str) -> bool:
        """Tell whether calling a module class runs ``__init__`` as written.

        Args:
            name (str): Class name.

        Returns:
            bool: ``True`` for a class with no metaclass, no ``__new__``, no
                decorator that rewrites it, and only bases that leave
                construction alone (checked through in-module bases).

        """
        return self._chain_safe(_cls=self._classes.get(name), seen=set())

    def _chain_safe(self, *, _cls: ClassDef | None, seen: set[int]) -> bool:
        """Check a class and its in-module bases for construction hooks.

        Args:
            _cls (ClassDef | None): Class to check.
            seen (set[int]): Classes already visited, to stop on cycles.

        Returns:
            bool: ``True`` when no class in the chain changes construction.

        """
        if _cls is None:
            return True
        if id(_cls) in seen:
            return False
        seen.add(id(_cls))
        decorators: list[str | None] = [
            _simple_name(node=_decorator_target(node=item))
            for item in _cls.decorator_list
        ]
        if (
            _cls.keywords
            or any(
                item not in Constants.safe_decorators for item in decorators
            )
            or not _construction_agrees(_cls=_cls)
        ):
            return False
        for base in _cls.bases:
            target: AST = base.value if isinstance(base, Subscript) else base
            label: str | None = _simple_name(node=target)
            if label in self._classes:
                if not self._chain_safe(_cls=self._classes[label], seen=seen):
                    return False
            elif label not in Constants.safe_bases and not _is_exception(
                name=label,
            ):
                return False
        return True

    def constructed_receiver(self, *, call: Call) -> bool:
        """Tell whether a call is made on a freshly constructed instance.

        Args:
            call (Call): Attribute call.

        Returns:
            bool: ``True`` for ``Class(...).method(...)`` with a module class.

        """
        return (
            isinstance(call.func, Attribute)
            and isinstance(call.func.value, Call)
            and isinstance(call.func.value.func, Name)
            and call.func.value.func.id in self._classes
            and self.constructor_safe(name=call.func.value.func.id)
        )

    def _enclosing_method(
        self,
        *,
        call: Call,
    ) -> tuple[Function, ClassDef] | None:
        """Find the method that directly contains a call.

        Args:
            call (Call): Call expression.

        Returns:
            tuple[Function, ClassDef] | None:
                The nearest function and its class, or ``None`` when that
                function is not a method defined directly in a class body.

        """
        node: AST | None = self._parents.get(id(call))
        while node is not None and not isinstance(
            node,
            (FunctionDef, AsyncFunctionDef),
        ):
            node = self._parents.get(id(node))
        if node is None:
            return None
        owner: AST | None = self._parents.get(id(node))
        return (node, owner) if isinstance(owner, ClassDef) else None

    def _find(
        self,
        *,
        owner: ClassDef,
        name: str,
    ) -> tuple[Function, ClassDef] | None:
        """Find the method a class resolves a name to.

        Args:
            owner (ClassDef): Class to start from.
            name (str): Method name.

        Returns:
            tuple[Function, ClassDef] | None:
                The single definition and its class, searching
                a lone in-module base chain, or ``None``
                when it is missing, repeated or ambiguous.

        """
        found: list[Function] = [
            item
            for item in owner.body
            if isinstance(item, (FunctionDef, AsyncFunctionDef))
            and item.name == name
        ]
        if found:
            return (found[0], owner) if len(found) == 1 else None
        if len(owner.bases) != 1 or owner.keywords:
            return None
        base: AST = owner.bases[0]
        if isinstance(base, Name) and base.id in self._classes:
            return self._find(owner=self._classes[base.id], name=name)
        return None

    def bind_self_call(self, *, call: Call) -> BoundCall | None:
        """Bind ``self.method(...)`` inside a method.

        Args:
            call (Call): Call expression.

        Returns:
            BoundCall | None:
                The binding, or ``None`` when the call is not a plain
                instance method call on the unmodified receiver.

        """
        func: expr = call.func
        context: tuple[Function, ClassDef] | None = self._enclosing_method(
            call=call,
        )
        if (
            context is None
            or not isinstance(func, Attribute)
            or not isinstance(func.value, Name)
        ):
            return None
        method, owner = context
        first: list[arg] = [*method.args.posonlyargs, *method.args.args]
        if (
            not first
            or first[0].arg != func.value.id
            or method.decorator_list
            or any(
                first[0].arg in names_bound_by(node=node)
                for statement in method.body
                for node in walk(node=statement)
            )
        ):
            return None
        located: tuple[Function, ClassDef] | None = self._find(
            owner=owner,
            name=func.attr,
        )
        if located is None:
            return None
        target, defining = located
        if target.decorator_list or not self.is_safe(
            call=call,
            declaration=target,
        ):
            return None
        return self._bind(call=call, target=target, owner=defining)

    def _bind(
        self,
        *,
        call: Call,
        target: Function,
        owner: ClassDef,
    ) -> BoundCall | None:
        """Match a call's arguments to an instance method's parameters.

        Args:
            call (Call): Call expression.
            target (Function): Method definition.
            owner (ClassDef): Class that defines it.

        Returns:
            BoundCall | None:
                The binding, or ``None`` for star arguments, surplus arguments,
                unknown or repeated keywords, or variadic signatures.

        """
        contracts: tuple[CallableContract, ...] = self._module.signature(
            name=f"{owner.name}.{target.name}",
        )
        matching: list[CallableContract] = [
            item for item in contracts if item.declaration is target
        ]
        if len(matching) != 1:
            return None
        contract: CallableContract = matching[0]
        slots: list[ParameterContract] = [
            item
            for item in contract.parameters
            if item.kind
            in {
                ParameterKind.POSITIONAL_ONLY,
                ParameterKind.POSITIONAL_OR_KEYWORD,
            }
        ]
        by_name: dict[str, ParameterContract] = {
            item.name: item
            for item in contract.parameters
            if item.kind
            in {
                ParameterKind.POSITIONAL_OR_KEYWORD,
                ParameterKind.KEYWORD_ONLY,
            }
        }
        variadic: bool = any(
            item.kind
            in {ParameterKind.VAR_POSITIONAL, ParameterKind.VAR_KEYWORD}
            for item in contract.parameters
        )
        keywords: list[str | None] = [item.arg for item in call.keywords]
        if (
            variadic
            or not slots
            or any(isinstance(item, Starred) for item in call.args)
            or None in keywords
            or len(call.args) > len(slots) - 1
            or len(set(keywords)) != len(keywords)
        ):
            return None
        receiver: tuple[AST, ...] = (
            (call.func.value,) if isinstance(call.func, Attribute) else ()
        )
        arguments: list[BoundArgument] = [
            BoundArgument(
                parameter=slots[0],
                origin=ArgumentOrigin.IMPLICIT_RECEIVER,
                values=receiver,
                types=(),
                definite=False,
            ),
        ]
        taken: set[str] = {slots[0].name}
        for parameter, value in zip(slots[1:], call.args, strict=False):
            arguments.append(
                BoundArgument(
                    parameter=parameter,
                    origin=ArgumentOrigin.POSITIONAL,
                    values=(value,),
                    types=(),
                    definite=False,
                ),
            )
            taken.add(parameter.name)
        for item in call.keywords:
            parameter: ParameterContract | None = by_name.get(item.arg or "")
            if parameter is None or parameter.name in taken:
                return None
            taken.add(parameter.name)
            arguments.append(
                BoundArgument(
                    parameter=parameter,
                    origin=ArgumentOrigin.KEYWORD,
                    values=(item.value,),
                    types=(),
                    definite=False,
                ),
            )
        return BoundCall(
            call=call,
            signature=contract,
            arguments=tuple(arguments),
        )


def _construction_agrees(*, _cls: ClassDef) -> bool:
    """Tell whether a class's ``__new__`` and ``__init__`` take the same names.

    Without a ``__new__`` there is nothing to disagree with. With one, an
    ``__init__`` must exist and accept exactly the same parameters after the
    receiver, because the call's arguments reach both.

    Args:
        _cls (ClassDef): Class definition.

    Returns:
        bool: ``True`` when construction cannot be redirected by ``__new__``.

    """
    methods: dict[str, Function] = {
        item.name: item
        for item in _cls.body
        if isinstance(item, (FunctionDef, AsyncFunctionDef))
        and item.name in Constants.init_methods
    }
    if "__new__" not in methods:
        return True
    if "__init__" not in methods:
        return False
    new_names, new_star, new_kw = _shape(function=methods["__new__"])
    init_names, init_star, init_kw = _shape(function=methods["__init__"])
    return (new_names[1:], new_star, new_kw) == (
        init_names[1:],
        init_star,
        init_kw,
    )


def _is_exception(*, name: str | None) -> bool:
    """Tell whether a name is a builtin exception class.

    Args:
        name (str | None): Candidate base-class name.

    Returns:
        bool: ``True`` for names such as ``ValueError`` or ``OSError``.

    """
    found: type | None = None if name is None else __dict__.get(name, None)
    return isinstance(found, type) and issubclass(found, BaseException)


def _decorator_target(*, node: AST) -> AST:
    """Unwrap a decorator call to the decorator expression itself.

    Args:
        node (AST): Decorator expression.

    Returns:
        AST: The called expression for ``@d(...)``, otherwise the node.

    """
    return node.func if isinstance(node, Call) else node


def _simple_name(*, node: AST) -> str | None:
    """Read the last name of ``name`` or ``module.name``.

    Args:
        node (AST): Expression.

    Returns:
        str | None: The identifier, or ``None`` for anything else.

    """
    if isinstance(node, Name):
        return node.id
    return node.attr if isinstance(node, Attribute) else None


def _keyword_constant(*, call: Call, name: str) -> Constant | None:
    """Find a constant keyword argument of a call.

    Args:
        call (Call): Call expression.
        name (str): Keyword name.

    Returns:
        Constant | None:
            The constant node, or ``None`` when absent or not a constant.

    """
    for item in call.keywords:
        if item.arg == name and isinstance(item.value, Constant):
            return item.value
    return None


def _header_is_plain(*, cls: ClassDef) -> bool:
    """Tell whether a class is decorated only by a neutral ``@dataclass``.

    Args:
        cls: Class definition.

    Returns:
        bool: ``True`` for one ``dataclass`` decorator whose options leave
            ``__init__`` alone, on a class with no bases or class keywords.

    """
    if cls.bases or cls.keywords or len(cls.decorator_list) != 1:
        return False
    decorator: AST = cls.decorator_list[0]
    if _simple_name(node=_decorator_target(node=decorator)) != "dataclass":
        return False
    return not (
        isinstance(decorator, Call)
        and any(
            item.arg not in Constants.neutral_options
            for item in decorator.keywords
        )
    )


def _field_of(*, statement: AnnAssign) -> tuple[bool, str | None]:
    """Classify one annotated class attribute of a dataclass.

    Args:
        statement (AnnAssign): Annotated assignment in the class body.

    Returns:
        tuple[bool, str | None]: ``(valid, name)`` : ``valid`` is ``False``
            when the attribute
            makes the generated signature unclear (``KW_ONLY``, per-field
            ``kw_only``); ``name`` is its parameter name, or ``None`` when
            it is not a parameter (``ClassVar``, ``field(init=False)``).

    """
    annotation: AST = statement.annotation
    marker: str | None = _simple_name(
        node=annotation.value
        if isinstance(annotation, Subscript)
        else annotation,
    )
    if marker == "KW_ONLY" or not isinstance(statement.target, Name):
        return False, None
    if marker == "ClassVar":
        return True, None
    value: expr | None = statement.value
    if isinstance(value, Call) and _simple_name(node=value.func) == "field":
        if _keyword_constant(call=value, name="kw_only") is not None:
            return False, None
        init: Constant | None = _keyword_constant(call=value, name="init")
        if init is not None and init.value is False:
            return True, None
    return True, statement.target.id


def dataclass_init_names(*, cls: ClassDef) -> list[str] | None:
    """List the ``__init__`` parameters a plain dataclass generates.

    Args:
        cls: Class definition.

    Returns:
        list[str] | None:
            Field names in order, or ``None`` when the class is not a simple
        dataclass: other decorators, bases, a custom ``__init__``, ``init=``
            or ``kw_only=`` options, ``KW_ONLY``, or per-field ``kw_only``.

    """
    if not _header_is_plain(cls=cls):
        return None
    names: list[str] = []
    for statement in cls.body:
        if isinstance(statement, (FunctionDef, AsyncFunctionDef)) and (
            statement.name in Constants.init_methods
        ):
            return None
        if isinstance(statement, AnnAssign):
            valid, name = _field_of(statement=statement)
            if not valid:
                return None
            if name is not None:
                names.append(name)
    return names


def ast_children(*, node: AST) -> list[AST]:
    """List the direct child nodes of a node.

    Args:
        node (AST): Parent node.

    Returns:
        list[AST]: Its children, in field order.

    """
    return [
        child
        for _name, value in node.__dict__.items()
        for child in _field_values(value=value)
        if isinstance(child, AST)
    ]


def _field_values(
    *,
    value: AST | list[AST] | str | int | None,
) -> Iterable[AST | list[AST] | str | int | None]:
    """Return the nodes held in one ``__dict__`` field.

    Args:
        value (AST | list[AST] | str | int | None): Raw field value; lists hold
            several children.

    Returns:
        Iterable[AST | list[AST] | str | int | None]: The field's items.

    """
    if isinstance(value, list):
        return value
    return [value]
