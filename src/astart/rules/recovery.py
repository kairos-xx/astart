"""Annotation-recovery benchmark: strip a typed module, fix it, compare.

Well-typed code is the ground truth. Removing its parameter and return
annotations and running the fixer shows how many annotations it recovers
(recall) and how many of the ones it writes match the original (precision).

"""

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
    Lambda,
    Module,
    Name,
    Starred,
    Subscript,
    Tuple,
    TypeAlias,
    arg,
    arguments,
    expr,
    iter_child_nodes,
    parse,
    stmt,
    unparse,
    walk,
)
from builtins import __dict__
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import import_module
from itertools import product
from time import perf_counter
from typing import (
    TYPE_CHECKING,
    Final,
    ParamSpec,
    TypeVar,
    TypeVarTuple,
    final,
)

from astart.graph.dispatch import LowercaseTransformer
from astart.rules import (
    FixResult,
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.confidence import Constants as ConfidenceConstants
from astart.rules.hints import HintIndex, LazyHints
from astart.rules.vocabulary import FixSafety
from astart.source.api import parse as parse_module

type ListStr = list[str]
type SetStr = set[str]
type DictStr = dict[str, str]

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import ModuleType

    from astart import CommentedModule
    from astart.rules.checker import Checker, MypyChecker, PyrightChecker
    from astart.rules.registry import Registries


@final
@dataclass(frozen=True, slots=True)
class RecoveryScore:
    """Result of recovering the annotations of one module.

    Attributes:
        truth (int): Annotations the original module had.
        correct (int): Recovered annotations equal to the original.
        wrong (tuple[str, ...]): Keys written with an annotation that
            contradicts the original.
        missed (tuple[str, ...]): Keys the original had that the fixer did not
            write.
        synthesized (tuple[str, ...]): Keys annotated with a synthesized
            ``Protocol`` or type
            variable; these have no original to match and are
            judged by the external checker, not by this score.
        seconds (float): Wall-clock time of the fix run.
        rounds (int): Passes the fix run needed.
        new_errors (int | None): New type-checker errors the fixes introduced,
            or ``None`` when no checker was asked.
        missed_reasons (tuple[tuple[str, int], ...]): Why annotations were
            missed, as ``(reason, count)`` pairs
            sorted by count; empty unless attribution was requested.
        compatible (tuple[str, ...]): Keys written with a subtype or supertype
            of the original
            (see :func:`relation`); neither correct nor wrong.

    """

    truth: int
    correct: int
    wrong: tuple[str, ...]
    missed: tuple[str, ...]
    synthesized: tuple[str, ...]
    seconds: float
    rounds: int = 0
    new_errors: int | None = None
    missed_reasons: tuple[tuple[str, int], ...] = ()
    compatible: tuple[str, ...] = ()

    @property
    def precision(self) -> float:
        """Fraction of written annotations that match the original.

        Returns:
            float: ``1.0`` when nothing was written.

        """
        written: int = self.correct + len(self.compatible) + len(self.wrong)
        return 1.0 if written == 0 else 1 - len(self.wrong) / written

    @property
    def recall(self) -> float:
        """Fraction of original annotations that were recovered.

        Returns:
            float: ``1.0`` when the original had no annotations.

        """
        return 1.0 if self.truth == 0 else self.correct / self.truth


def _walk_functions(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: DictStr,
) -> None:
    """Collect annotations keyed by their qualified name.

    Args:
        node (AST): Node whose children are scanned.
        trail (tuple[str, ...]): Qualified-name prefix.
        out (DictStr): Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            if child.returns is not None:
                out[f"{name}->"] = normalize_annotation(
                    text=unparse(ast_obj=child.returns),
                )
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg) and parameter.annotation:
                    out[f"{name}.{parameter.arg}"] = normalize_annotation(
                        text=unparse(ast_obj=parameter.annotation),
                    )
            _walk_functions(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _walk_functions(node=child, trail=(*trail, child.name), out=out)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        aliases (Final[dict[str, str]]): ``typing`` generic names and their
            builtin spelling.
        unions (Final[frozenset[str]]): ``typing`` constructs that spell a
            union.
        typing_module (Final[ModuleType]): Grouped module constant.
        wildcard (Final[str]): Grouped module constant.
        unspecified (Final[str]): Grouped module constant.
        defaulted_args (Final[frozenset[str]]): Grouped module constant.
        callable_arity (Final[int]): Grouped module constant.
        distributed_limit (Final[int]): Grouped module constant.
        mapping_origins (Final[frozenset[str]]): Grouped module constant.
        typing_protocols (Final[frozenset[str]]): Grouped module constant.

    """

    aliases: Final[dict[str, str]] = {
        "Dict": "dict",
        "FrozenSet": "frozenset",
        "List": "list",
        "Set": "set",
        "Tuple": "tuple",
        "Type": "type",
    }
    unions: Final[frozenset[str]] = frozenset({"Optional", "Union"})

    typing_module: Final[ModuleType] = import_module(name="typing")
    wildcard: Final[str] = "__astart_wildcard__"
    unspecified: Final[str] = "__astartunspecified__"
    defaulted_args: Final[frozenset[str]] = frozenset(
        {"Generator", "AsyncGenerator"},
    )
    callable_arity: Final[int] = 2

    distributed_limit: Final[int] = 16

    mapping_origins: Final[frozenset[str]] = frozenset(
        {"Mapping", "MutableMapping"},
    )

    typing_protocols: Final[frozenset[str]] = frozenset(
        {
            "AsyncIterable",
            "AsyncIterator",
            "Collection",
            "Container",
            "Hashable",
            "Iterable",
            "Iterator",
            "Reversible",
            "Sized",
        },
    )


def _base_name(*, node: AST) -> str:
    """Read the last name of ``name`` or ``typing.name``.

    Args:
        node (AST): Name or attribute expression.

    Returns:
        str: The identifier with ``typing`` generics mapped to builtins.

    """
    name: str = (
        node.id
        if isinstance(node, Name)
        else node.attr
        if isinstance(node, Attribute)
        else unparse(ast_obj=node)
    )
    return Constants.aliases.get(name, name)


def _is_none(*, node: AST) -> bool:
    """Tell whether an annotation node is the literal ``None``.

    Args:
        node (AST): Annotation expression.

    Returns:
        bool: ``True`` for ``Constant(None)``.

    """
    return isinstance(node, Constant) and node.value is None


def _subscript_members(*, node: Subscript) -> ListStr:
    """Normalize the spelling of a subscripted annotation.

    Args:
        node (Subscript): A subscript such as ``list[int]`` or
            ``Optional[int]``.

    Returns:
        ListStr:
            The members: the arms of a ``Union`` /``Optional``, else one member
            with its arguments normalized. ``Generator[X, None, None]`` and
            ``AsyncGenerator[X, None]`` collapse to their defaulted spelling.

    """
    head: str = _base_name(node=node.value)
    if isinstance(node.slice, Tuple) and not node.slice.elts:
        return [f"{head}[()]"]
    items: list[expr] = (
        node.slice.elts if isinstance(node.slice, Tuple) else [node.slice]
    )
    if head in Constants.unions:
        found: ListStr = [
            member for item in items for member in _members(node=item)
        ]
        return [*found, "None"] if head == "Optional" else found
    items_len: list[int] = [2, 3]
    if (
        head == "Generator"
        and len(items) == items_len[-1]
        and all(_is_none(node=item) for item in items[1:])
    ) or (
        head == "AsyncGenerator"
        and len(items) == items_len[0]
        and _is_none(
            node=items[1],
        )
    ):
        items = items[:1]
    return [f"{head}[{', '.join(_one(node=item) for item in items)}]"]


def _members(*, node: AST) -> ListStr:
    """Flatten a union into its normalized member spellings.

    Args:
        node (AST): Annotation expression.

    Returns:
        ListStr: The members; a non-union gives a single one.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return [*_members(node=node.left), *_members(node=node.right)]
    if isinstance(node, Subscript):
        return _subscript_members(node=node)
    if isinstance(node, Constant):
        return [
            node.value if isinstance(node.value, str) else repr(node.value),
        ]
    if isinstance(node, (Name, Attribute)):
        return [_base_name(node=node)]
    return [unparse(ast_obj=node)]


def _one(*, node: AST) -> str:
    """Normalize one annotation expression.

    Args:
        node (AST): Annotation expression.

    Returns:
        str: Its members de-duplicated and sorted,
            ``None`` last, joined by `` | ``.

    """
    unique: ListStr = sorted(
        set(_members(node=node)),
        key=lambda item: (item == "None", item),
    )
    return " | ".join(unique)


def normalize_annotation(*, text: str) -> str:
    """Spell an annotation canonically so equivalent forms compare equal.

    ``Optional[X]``, ``Union[A, B]`` and ``A | B`` agree, ``typing`` generics
    map to the builtin ones, quotes around a forward reference are dropped
    and union members are ordered.

    Args:
        text (str): Annotation source.

    Returns:
        str: The canonical spelling.

    """
    return _one(node=parse(source=text, mode="eval").body)


def _arms(*, text: str) -> SetStr:
    """Split an annotation at its top-level ``|`` and drop module prefixes.

    Args:
        text (str): Annotation source.

    Returns:
        SetStr: The arms; ``te.NoReturn`` and ``typing.NoReturn`` both read
            ``NoReturn``.

    """
    arms: ListStr = []
    depth: int = 0
    start: int = 0
    for index, char in enumerate(iterable=text):
        depth += (char == "[") - (char == "]")
        if char == "|" and depth == 0:
            arms.append(text[start:index].strip())
            start = index + 1
    arms.append(text[start:].strip())
    found: SetStr = set()
    for arm in arms:
        found.add(
            arm.rsplit(sep=".", maxsplit=1)[-1] if "[" not in arm else arm,
        )
    return found


def _tower(*, arms: SetStr) -> SetStr:
    """Add the types the numeric tower lets an annotation accept.

    Args:
        arms (SetStr): Annotation arms.

    Returns:
        SetStr: The arms plus ``int`` and ``bool`` under
            ``float``, ``bool`` under ``int``.

    """
    widened: SetStr = set(arms)
    if "float" in arms:
        widened |= {"int", "bool"}
    if "int" in arms:
        widened.add("bool")
    return widened


@final
@dataclass(frozen=True, slots=True)
class Shape:
    """The members a class declares, for name-agnostic protocol scoring.

    Attributes:
        attrs (Mapping[str, str]): Attribute annotations by name; ``""`` when
            unannotated.
        methods (Mapping[str, tuple[tuple[str, ...] | None, str]]): Method
            signatures by name as ``(parameters, returns)``;
            parameter annotations are ``""`` when unannotated and the
            parameter tuple is ``None`` for an any-signature ``...``.

    """

    attrs: Mapping[str, str]
    methods: Mapping[str, tuple[tuple[str, ...] | None, str]]


@final
@dataclass(frozen=True, slots=True)
class Context:
    """What the original module defines, for judging its annotations.

    Attributes:
        aliases (Mapping[str, str]): Module-level type aliases by name, as
            annotation source.
        typevars (frozenset[str]): Names bound to ``TypeVar(...)`` in the
            module.
        bases (Mapping[str, tuple[str, ...]]): Base-class names of each class
            the module defines.
        classes (frozenset[str]): Names of the classes the module defines.
        protocols (frozenset[str]): Names of the classes deriving from
            ``Protocol``.
        shapes (Mapping[str, Shape]): Member shapes of every class the module
            defines,
            including function-local ones, by simple name.
        alias_parameters (Mapping[str, tuple[str, ...]]): Ordered PEP 695
            binders of generic aliases.

    """

    aliases: Mapping[str, str] = field(default_factory=dict[str, str])
    alias_parameters: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict[str, tuple[str, ...]],
    )
    classes: frozenset[str] = frozenset()
    typevars: frozenset[str] = frozenset()
    bases: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict[str, tuple[str, ...]],
    )
    protocols: frozenset[str] = frozenset()
    shapes: Mapping[str, Shape] = field(
        default_factory=dict[str, Shape],
    )


def _self_attribute(node: expr) -> Attribute | None:
    """Return an assignment target when it is ``self.name``.

    Args:
        node (expr): Assignment target.

    Returns:
        Attribute | None: The target as :class:`ast.Attribute`, or ``None``.

    """
    if (
        isinstance(node, Attribute)
        and isinstance(node.value, Name)
        and node.value.id == "self"
    ):
        return node
    return None


def _self_attributes(*, body: Sequence[stmt]) -> DictStr:
    """Collect ``self.X`` annotations inside one method body.

    Nested classes open a new ``self`` scope and are skipped; nested
    functions close over the same ``self`` and are scanned.

    Args:
        body (Sequence[stmt]): Statements of the method.

    Returns:
        DictStr:
            Attribute name to normalized annotation (``""`` when unannotated).

    """
    found: DictStr = {}
    stack: list[AST] = list(body)
    while stack:
        node: AST = stack.pop()
        if isinstance(node, (ClassDef, Lambda)):
            continue
        if isinstance(node, AnnAssign):
            target: Attribute | None = _self_attribute(node=node.target)
            if target is not None:
                found[target.attr] = normalize_annotation(
                    text=unparse(ast_obj=node.annotation),
                )
        elif isinstance(node, Assign):
            for candidate in node.targets:
                attribute: Attribute | None = _self_attribute(node=candidate)
                if attribute is not None:
                    found.setdefault(attribute.attr, "")
        stack.extend(iter_child_nodes(node=node))
    return found


def _method_shape(
    *,
    node: FunctionDef | AsyncFunctionDef,
) -> tuple[tuple[str, ...], str]:
    """Read one method's parameter and return annotations.

    Args:
        node (FunctionDef | AsyncFunctionDef): The method definition.

    Returns:
        tuple[tuple[str, ...], str]:
            ``(parameter annotations, return annotation)``; ``self``
            /``cls`` are dropped and unannotated parts read as ``""``.

    """
    params: ListStr = []
    signature: arguments = node.args
    for parameter in (
        *signature.posonlyargs,
        *signature.args,
        *signature.kwonlyargs,
    ):
        if parameter.arg in {"self", "cls"}:
            continue
        params.append(
            normalize_annotation(text=unparse(ast_obj=parameter.annotation))
            if parameter.annotation is not None
            else "",
        )
    params.extend(
        normalize_annotation(text=unparse(ast_obj=variadic.annotation))
        if variadic.annotation is not None
        else ""
        for variadic in (signature.vararg, signature.kwarg)
        if variadic is not None
    )
    returns: str = (
        normalize_annotation(text=unparse(ast_obj=node.returns))
        if node.returns is not None
        else ""
    )
    return tuple(params), returns


def _class_shape(*, node: ClassDef) -> Shape:
    """Read the member shape of one class definition.

    Args:
        node (ClassDef): The class definition, at any nesting depth.

    Returns:
        Shape: Its attributes and method signatures; ``self.X`` assignments in
            methods count as attributes when the class body does not declare
            them.

    """
    attrs: DictStr = {}
    methods: dict[str, tuple[tuple[str, ...] | None, str]] = {}
    for child in node.body:
        if isinstance(child, AnnAssign) and isinstance(child.target, Name):
            attrs[child.target.id] = normalize_annotation(
                text=unparse(ast_obj=child.annotation),
            )
        elif isinstance(child, Assign):
            for target in child.targets:
                if isinstance(target, Name):
                    attrs.setdefault(target.id, "")
        elif isinstance(child, (FunctionDef, AsyncFunctionDef)):
            methods[child.name] = _method_shape(node=child)
            for name, annotation in _self_attributes(body=child.body).items():
                if not attrs.get(name):
                    attrs[name] = annotation
    return Shape(attrs=attrs, methods=methods)


def _is_protocol(*, node: ClassDef) -> bool:
    """Tell whether a class definition derives from ``Protocol``.

    Args:
        node (ClassDef): The class definition.

    Returns:
        bool: ``True`` when a base spells ``Protocol`` , ``typing.Protocol``
            or a subscripted form such as ``Protocol[T]``.

    """
    return any(
        unparse(ast_obj=base).partition("[")[0].split(sep=".")[-1]
        == "Protocol"
        for base in node.bases
    )


def _class_details(
    *,
    tree: AST,
) -> tuple[dict[str, Shape], SetStr, dict[str, tuple[str, ...]], SetStr]:
    """Collect shapes, protocols, bases and names of every class in a tree.

    Args:
        tree (AST): Parsed module.

    Returns:
        tuple[dict[str, Shape], SetStr, dict[str, tuple[str, ...]], SetStr]:
            ``(shapes, protocols, bases, class names)``; the first class of a
        repeated name wins, matching :func:`ast.walk` order.

    """
    shapes: dict[str, Shape] = {}
    protocols: SetStr = set()
    found_bases: dict[str, tuple[str, ...]] = {}
    names: SetStr = set()
    for node in walk(node=tree):
        if not isinstance(node, ClassDef):
            continue
        names.add(node.name)
        if node.name not in found_bases:
            found_bases[node.name] = tuple(
                unparse(ast_obj=base).partition("[")[0] for base in node.bases
            )
        if node.name not in shapes:
            shapes[node.name] = _class_shape(node=node)
        if _is_protocol(node=node):
            protocols.add(node.name)
    return shapes, protocols, found_bases, names


def module_context(*, source: str, tree: Module | None = None) -> Context:
    """Collect the aliases and classes a module defines at top level.

    Args:
        source (str): Original module text.
        tree (Module | None): Existing module to reuse instead of parsing
            source.

    Returns:
        Context: class:`Context`, including member shapes of every class at
            any nesting depth and the names of ``Protocol`` classes.

    """
    aliases: DictStr = {}
    alias_parameters: dict[str, tuple[str, ...]] = {}
    classes: SetStr = set()
    typevars: SetStr = set()
    bases: dict[str, tuple[str, ...]] = {}
    tree = parse(source=source) if tree is None else tree
    for node in tree.body:
        match node:
            case TypeAlias(name=Name(id=name)):
                aliases[name] = unparse(ast_obj=node.value)
                alias_parameters[name] = tuple(
                    parameter_name
                    for parameter in node.type_params
                    if isinstance(
                        parameter_name := getattr(parameter, "name", None),
                        str,
                    )
                )
            case ClassDef(name=name):
                classes.add(name)
                bases[name] = tuple(
                    unparse(ast_obj=base).partition("[")[0]
                    for base in node.bases
                )
            case Assign(
                targets=[Name(id=name)],
                value=Call(func=Name(id="TypeVar")),
            ):
                typevars.add(name)
            case Assign(targets=[Name(id=name)], value=BinOp() | Subscript()):
                aliases[name] = unparse(ast_obj=node.value)
            case AnnAssign(target=Name(id=name), value=BinOp() | Subscript()):
                if node.value is not None:
                    aliases[name] = unparse(ast_obj=node.value)
            case _:
                continue
    shapes, protocols, found_bases, found_classes = _class_details(tree=tree)
    classes |= found_classes
    for name, value in found_bases.items():
        bases.setdefault(name, value)
    return Context(
        aliases=aliases,
        alias_parameters=alias_parameters,
        classes=frozenset(classes),
        typevars=frozenset(typevars),
        bases=bases,
        protocols=frozenset(protocols),
        shapes=shapes,
    )


def merge_contexts(*, primary: Context, extra: Context) -> Context:
    """Combine two module contexts, ``primary`` winning name collisions.

    Args:
        primary (Context): Context whose aliases, bases and shapes take
            precedence.
        extra (Context): Context merged underneath it (for example the fixed
            module's synthesized protocols and type variables).

    Returns:
        Context: The merged :class:`Context`.

    """
    return Context(
        aliases={**extra.aliases, **primary.aliases},
        alias_parameters={
            **extra.alias_parameters,
            **primary.alias_parameters,
        },
        classes=primary.classes | extra.classes,
        typevars=primary.typevars | extra.typevars,
        bases={**extra.bases, **primary.bases},
        protocols=primary.protocols | extra.protocols,
        shapes={**extra.shapes, **primary.shapes},
    )


def _expand(*, arms: SetStr, context: Context, depth: int = 64) -> SetStr:
    """Replace alias names by the arms they stand for.

    Args:
        arms (SetStr): Annotation arms.
        context (Context): The original module's aliases.
        depth (int): How many alias levels to unfold.

    Returns:
        SetStr: The arms with aliases resolved.

    """
    if depth == 0:
        return arms
    out: SetStr = set()
    for arm in arms:
        target: str | None = context.aliases.get(arm)
        if target is None or context.alias_parameters.get(arm):
            out.add(arm)
        else:
            try:
                inner: SetStr = _arms(text=normalize_annotation(text=target))
            except SyntaxError:
                out.add(arm)
            else:
                out |= _expand(arms=inner, context=context, depth=depth - 1)
    return out


@final
class _AliasArguments(LowercaseTransformer):
    """Substitute generic alias binders without interpreting value payloads."""

    def __init__(self, *, values: Mapping[str, expr]) -> None:
        """Keep the actual arguments of one generic alias application.

        Args:
            values (Mapping[str, expr]): Formal binder names mapped to actual
                expression nodes.

        """
        self._values: Mapping[str, expr] = values

    def visit_name(self, node: Name) -> expr:
        """Replace a type binder with an independent actual argument.

        Args:
            node (Name): Name at a type position.

        Returns:
            expr: Fresh actual syntax or the original non-parameter name.

        """
        value: expr | None = self._values.get(node.id)
        return deepcopy(x=value) if value is not None else node

    def visit_subscript(self, node: Subscript) -> AST:
        """Protect Literal values and Annotated metadata during substitution.

        Args:
            node (Subscript): Generic expression.

        Returns:
            AST: Substituted type syntax with value payloads unchanged.

        """
        name: str = _base_name(node=node.value)
        if name == "Literal":
            return node
        if name == "Annotated" and isinstance(node.slice, Tuple):
            if node.slice.elts:
                value: AST | list[AST] | None = self.visit(
                    node=node.slice.elts[0],
                )
                if isinstance(value, expr):
                    node.slice.elts[0] = value
            return node
        return self.generic_visit(node=node)


@final
class _Unfolder(LowercaseTransformer):
    """Replace alias names inside an annotation by their targets.

    ``Literal`` slices are left alone: their parameters are values, not
    types, so an alias there would change meaning.

    Attributes:
        _aliases: Module-level type aliases by name.
        _depth: Alias levels still allowed to unfold.

    """

    def __init__(
        self,
        *,
        aliases: Mapping[str, str],
        depth: int,
        parameters: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        """Remember the aliases and remaining unfold depth.

        Args:
            aliases (Mapping[str, str]): Module-level type aliases by name.
            depth (int): How many alias levels to unfold.
            parameters (Mapping[str, tuple[str, ...]] | None): Ordered binders
                for generic alias declarations.

        """
        self._aliases: Mapping[str, str] = aliases
        self._depth: int = depth
        self._parameters: Mapping[str, tuple[str, ...]] = (
            {} if parameters is None else parameters
        )

    def visit_name(self, node: Name) -> AST:
        """Splice in the alias target for a known name.

        Args:
            node (Name): The name node.

        Returns:
            AST: The unfolded expression, or the node unchanged.

        """
        target: str | None = self._aliases.get(node.id)
        if target is None or self._depth <= 0 or self._parameters.get(node.id):
            return node
        try:
            inner: expr = parse(source=target, mode="eval").body
        except SyntaxError:
            return node
        self._depth -= 1
        try:
            result: AST | list[AST] | None = self.visit(node=inner)
        finally:
            self._depth += 1
        return result if isinstance(result, AST) else node

    def visit_subscript(self, node: Subscript) -> AST:
        """Descend into a subscript unless it is a ``Literal``.

        Args:
            node (Subscript): The subscript node.

        Returns:
            AST: The transformed node.

        """
        head: expr = node.value
        name: str = (
            head.id
            if isinstance(head, Name)
            else head.attr
            if isinstance(head, Attribute)
            else ""
        )
        if name == "Literal":
            return node
        parameters: tuple[str, ...] = self._parameters.get(name, ())
        target: str | None = self._aliases.get(name)
        if parameters and target is not None and self._depth > 0:
            return self._application(
                node=node,
                parameters=parameters,
                target=target,
            )
        if name == "Annotated" and isinstance(node.slice, Tuple):
            if node.slice.elts:
                first: AST | list[AST] | None = self.visit(
                    node=node.slice.elts[0],
                )
                if isinstance(first, expr):
                    node.slice.elts[0] = first
            return node
        return self.generic_visit(node=node)

    def _application(
        self,
        *,
        node: Subscript,
        parameters: tuple[str, ...],
        target: str,
    ) -> AST:
        """Expand one generic alias with a bounded substitution depth.

        Args:
            node (Subscript): Generic alias application.
            parameters (tuple[str, ...]): Ordered formal binder identifiers.
            target (str): Declared alias body source.

        Returns:
            AST: Instantiated type syntax, or the
                original unsupported application.

        """
        arguments: list[expr] = (
            node.slice.elts if isinstance(node.slice, Tuple) else [node.slice]
        )
        if len(parameters) != len(arguments):
            return node
        try:
            body: expr = parse(source=target, mode="eval").body
        except SyntaxError:
            return node
        substituted: AST | list[AST] | None = _AliasArguments(
            values=dict(zip(parameters, arguments, strict=True)),
        ).visit(node=body)
        if not isinstance(substituted, expr):
            return node
        self._depth -= 1
        try:
            expanded: AST | list[AST] | None = self.visit(node=substituted)
        finally:
            self._depth += 1
        return expanded if isinstance(expanded, AST) else node


def _union_parts(*, node: expr) -> list[expr]:
    """Split one expression at its top-level ``|`` operators.

    Args:
        node (expr): The expression.

    Returns:
        list[expr]: The union members; the node itself when it is not a union.

    """
    if isinstance(node, BinOp) and isinstance(node.op, BitOr):
        return [
            *_union_parts(node=node.left),
            *_union_parts(node=node.right),
        ]
    return [node]


def _distributed(*, arm: str) -> SetStr:
    """Spread top-level unions of a ``tuple[...]`` arm's arguments.

    ``tuple[X, A | B]`` is exactly ``tuple[X, A] | tuple[X, B]``, so the
    arm reads as the union a multi-arm counterpart already spells. Other
    containers keep their union argument: mixing element types is not the
    same as a union of homogeneous containers.

    Args:
        arm (str): One normalized annotation arm.

    Returns:
        SetStr: The distributed arms, or the arm unchanged.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return {arm}
    if not isinstance(node, Subscript):
        return {arm}
    head: expr = node.value
    name: str = (
        head.id
        if isinstance(head, Name)
        else head.attr
        if isinstance(head, Attribute)
        else ""
    )
    if name != "tuple":
        return {arm}
    inner: expr = node.slice
    parts: list[expr] = (
        list(inner.elts) if isinstance(inner, Tuple) else [inner]
    )
    if any(
        isinstance(part, Starred)
        or (isinstance(part, Constant) and part.value is Ellipsis)
        or (isinstance(part, Name) and part.id == "Ellipsis")
        for part in parts
    ):
        return {arm}
    pools: list[list[expr]] = [_union_parts(node=part) for part in parts]
    total: int = 1
    for pool in pools:
        total *= len(pool)
    if total <= 1 or total > Constants.distributed_limit:
        return {arm}
    out: SetStr = set()
    for combo in product(*pools):
        chosen: list[expr] = list(combo)
        new_slice: expr = (
            chosen[0]
            if len(chosen) == 1 and not isinstance(inner, Tuple)
            else Tuple(elts=chosen)
        )
        out.add(
            unparse(ast_obj=Subscript(value=node.value, slice=new_slice)),
        )
    return out


def _resolved(*, arm: str, context: Context) -> SetStr:
    """Unfold aliases inside an arm, then distribute ``tuple`` unions.

    Args:
        arm (str): One annotation arm.
        context (Context): The original module's aliases and classes.

    Returns:
        SetStr: The arm variants the scorer should compare.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return {arm}
    unfurled: AST | list[AST] | None = _Unfolder(
        aliases=context.aliases,
        parameters=context.alias_parameters,
        depth=64,
    ).visit(node=node)
    if not isinstance(unfurled, AST):
        return {arm}
    out: SetStr = set()
    for variant in _distributed(arm=unparse(ast_obj=unfurled)):
        out.add(variant)
    return out


@final
class Hierarchy:
    """The ``collections.abc`` ancestry of the builtin containers.

    Attributes:
        ancestors (Final[dict[str, frozenset[str]]]): Abstract bases of each
            builtin container.
        covariant (Final[frozenset[str]]): Abstract bases whose element
            argument may be narrower.
        pairs (Final[frozenset[str]]): Abstract bases whose first argument is
            invariant and whose second may be narrower.
        pair_size (Final[int]): Number of arguments of such a base.

    """

    ancestors: Final[dict[str, frozenset[str]]] = {
        "list": frozenset(
            {
                "MutableSequence",
                "Sequence",
                "Collection",
                "Iterable",
                "Reversible",
            },
        ),
        "tuple": frozenset(
            {"Sequence", "Collection", "Iterable", "Reversible"},
        ),
        "set": frozenset(
            {"MutableSet", "Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "frozenset": frozenset(
            {"Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "dict": frozenset(
            {"MutableMapping", "Mapping", "Collection", "Iterable"},
        ),
        "Collection": frozenset({"Iterable"}),
        "Sequence": frozenset({"Reversible", "Collection", "Iterable"}),
        "MutableSequence": frozenset(
            {"Sequence", "Reversible", "Collection", "Iterable"},
        ),
        "Set": frozenset({"Collection", "Iterable"}),
        "AbstractSet": frozenset({"Collection", "Iterable"}),
        "MutableSet": frozenset(
            {"Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "Mapping": frozenset({"Collection", "Iterable"}),
        "MutableMapping": frozenset(
            {"Mapping", "Collection", "Iterable"},
        ),
        "KeysView": frozenset(
            {"Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "ItemsView": frozenset(
            {"Set", "AbstractSet", "Collection", "Iterable"},
        ),
        "ValuesView": frozenset({"Collection", "Iterable"}),
        "Iterator": frozenset({"Iterable"}),
        "AsyncIterator": frozenset({"AsyncIterable"}),
        "Generator": frozenset({"Iterator", "Iterable"}),
        "AsyncGenerator": frozenset({"AsyncIterator", "AsyncIterable"}),
        "Coroutine": frozenset({"Awaitable"}),
    }
    covariant: Final[frozenset[str]] = frozenset(
        {
            "Sequence",
            "Collection",
            "Iterable",
            "Reversible",
            "Set",
            "AbstractSet",
            "Iterator",
            "AsyncIterator",
            "AsyncIterable",
        },
    )
    pairs: Final[frozenset[str]] = frozenset({"Mapping"})
    pair_size: Final[int] = 2


@lru_cache(maxsize=4096)
def _generic(*, arm: str) -> tuple[str, ListStr] | None:
    """Split ``origin[a, b]`` into its origin and argument texts.

    Args:
        arm (str): One annotation arm.

    Returns:
        tuple[str, ListStr] | None: The origin and arguments, or ``None``
            when the arm is not a subscript.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(node, Subscript):
        return None
    inner: expr = node.slice
    parts: list[expr] = inner.elts if isinstance(inner, Tuple) else [inner]
    return unparse(ast_obj=node.value), [
        unparse(ast_obj=part) for part in parts
    ]


def _arg_within(*, small: str, big: str, known: Context) -> bool:
    """Tell whether one written generic argument fits a truth argument.

    A truth argument spelled ``object`` reaches here as the wildcard
    marker and accepts anything; padding markers mean "not claimed".

    Args:
        small (str): Argument of the written annotation.
        big (str): Argument of the truth annotation, possibly wildcarded.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when ``small`` fits inside ``big``.

    """
    if small == Constants.unspecified or big in {
        Constants.unspecified,
        Constants.wildcard,
    }:
        return True
    return _within(
        small=_arms(text=small),
        big=_arms(text=big),
        known=known,
    )


def _callable_params(*, text: str) -> ListStr | None:
    """Split a ``Callable`` parameter-list argument into its members.

    Args:
        text (str): The first argument of a ``Callable[...]`` arm: ``[...]``,
            ``...`` or an opaque expression such as ``Concatenate[...]``.

    Returns:
        ListStr | None: The parameter annotations, or ``None`` for
            ``...`` /``Ellipsis`` (any signature).

    """
    if text in {"...", "Ellipsis"}:
        return None
    if not (text.startswith("[") and text.endswith("]")):
        return [text]
    inner: str = text[1:-1].strip()
    if not inner:
        return []
    parts: ListStr = []
    depth: int = 0
    start: int = 0
    for index, char in enumerate(iterable=inner):
        depth += (char == "[") - (char == "]")
        depth += (char == "(") - (char == ")")
        if char == "," and depth == 0:
            parts.append(inner[start:index].strip())
            start = index + 1
    parts.append(inner[start:].strip())
    return parts


def _callable_fit(
    *,
    written: ListStr,
    truth: ListStr,
    known: Context,
) -> bool:
    """Tell whether a written ``Callable`` arm fits a truth one.

    Args:
        written (ListStr): Arguments of the written ``Callable`` (parameters,
            return).
        truth (ListStr): Arguments of the truth ``Callable`` , possibly
            wildcarded.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when the parameters and the return fit pairwise; ``...``
            on the truth side accepts any written parameter list.

    """
    len_args: int = 2
    if len(written) != len_args or len(truth) != len_args:
        return written == truth
    mine: ListStr | None = _callable_params(text=written[0])
    theirs: ListStr | None = _callable_params(text=truth[0])
    params_fit: bool = theirs is None or (
        mine is not None
        and len(mine) == len(theirs)
        and all(
            _arg_within(small=one, big=other, known=known)
            for one, other in zip(mine, theirs, strict=False)
        )
    )
    return params_fit and _arg_within(
        small=written[1],
        big=truth[1],
        known=known,
    )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _TupleLayout:
    """A fixed tuple or one variadic run with fixed prefix and suffix.

    Attributes:
        prefix (tuple[str, ...]): Leading fixed-position types.
        middle (str | None): Repeated element type, or None for a fixed tuple.
        suffix (tuple[str, ...]): Fixed positions following the variadic run.

    """

    prefix: tuple[str, ...]
    middle: str | None = None
    suffix: tuple[str, ...] = ()


def _tuple_layout(*, arguments: ListStr) -> _TupleLayout | None:
    """Read homogeneous variadics and a single PEP 646 starred tuple run.

    Args:
        arguments (ListStr): Already unfolded tuple argument spellings.

    Returns:
        _TupleLayout | None:
            Fixed/variadic layout, or None for unsupported unpacking.

    """
    if len(arguments) == Hierarchy.pair_size and arguments[-1] in {
        "...",
        "Ellipsis",
    }:
        return _TupleLayout(prefix=(), middle=arguments[0])
    if arguments == ["()"]:
        return _TupleLayout(prefix=())
    unpacked: list[int] = [
        index
        for index, item in enumerate(iterable=arguments)
        if item.startswith("*")
    ]
    if not unpacked:
        return _TupleLayout(prefix=tuple(arguments))
    if len(unpacked) != 1:
        return None
    index: int = unpacked[0]
    inner: tuple[str, ListStr] | None = _generic(
        arm=arguments[index].removeprefix("*"),
    )
    if (
        inner is None
        or inner[0] != "tuple"
        or len(inner[1]) != (Hierarchy.pair_size)
        or inner[1][-1] not in {"...", "Ellipsis"}
    ):
        return None
    return _TupleLayout(
        prefix=tuple(arguments[:index]),
        middle=inner[1][0],
        suffix=tuple(arguments[index + 1 :]),
    )


def _tuple_fit(
    *,
    written: ListStr,
    truth: ListStr,
    known: Context,
) -> bool:
    """Check covariant tuple positions without confusing length contracts.

    Args:
        written (ListStr): Narrower tuple arguments.
        truth (ListStr): Wider tuple arguments.
        known (Context): Alias and type-variable context.

    Returns:
        bool: Whether every sequence described by written is admitted by truth.

    """
    mine: _TupleLayout | None = _tuple_layout(arguments=written)
    theirs: _TupleLayout | None = _tuple_layout(arguments=truth)
    if mine is None or theirs is None:
        return written == truth
    if theirs.middle is None:
        return (
            mine.middle is None
            and len(mine.prefix) == len(theirs.prefix)
            and all(
                _argument_fits(small=a, big=b, known=known)
                for a, b in zip(mine.prefix, theirs.prefix, strict=False)
            )
        )
    if mine.middle is None:
        if len(mine.prefix) < len(theirs.prefix) + len(theirs.suffix):
            return False
        tail: int = len(mine.prefix) - len(theirs.suffix)
        prefix: tuple[str, ...] = mine.prefix[: len(theirs.prefix)]
        suffix: tuple[str, ...] = mine.prefix[tail:]
        middle: tuple[str, ...] = mine.prefix[len(theirs.prefix) : tail]
    else:
        if len(mine.prefix) < len(theirs.prefix) or len(mine.suffix) < len(
            theirs.suffix,
        ):
            return False
        prefix = mine.prefix[: len(theirs.prefix)]
        cut: int = len(mine.suffix) - len(theirs.suffix)
        suffix = mine.suffix[cut:]
        middle = (
            *mine.prefix[len(theirs.prefix) :],
            mine.middle,
            *mine.suffix[:cut],
        )
    return all(
        _argument_fits(small=a, big=b, known=known)
        for a, b in (
            *zip(prefix, theirs.prefix, strict=True),
            *zip(suffix, theirs.suffix, strict=True),
        )
    ) and all(
        _argument_fits(small=item, big=theirs.middle, known=known)
        for item in middle
    )


def _same_origin_fit(
    *,
    origin: str,
    written: ListStr,
    truth: ListStr,
    known: Context,
) -> bool:
    """Tell whether same-origin generic arguments fit pairwise.

    Origins with defaulted parameters (``Generator``, ``AsyncGenerator``)
    pad the shorter argument list with "not claimed" markers. ``Callable``
    compares its parameter list element-wise.

    Args:
        origin (str): The shared generic origin.
        written (ListStr): Arguments of the written annotation.
        truth (ListStr): Arguments of the truth annotation, possibly
            wildcarded.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when every written argument fits its truth counterpart.

    """
    mine: ListStr = list(written)
    theirs: ListStr = list(truth)
    if origin in Constants.defaulted_args and len(mine) != len(theirs):
        size: int = max(len(mine), len(theirs))
        mine += [Constants.unspecified] * (size - len(mine))
        theirs += [Constants.unspecified] * (size - len(theirs))
    if origin == "Callable":
        return _callable_fit(written=mine, truth=theirs, known=known)
    if origin == "tuple":
        return _tuple_fit(written=mine, truth=theirs, known=known)
    return len(mine) == len(theirs) and all(
        _arg_within(small=one, big=other, known=known)
        for one, other in zip(mine, theirs, strict=False)
    )


def _argument_fits(*, small: str, big: str, known: Context) -> bool:
    """Tell whether one type argument fits a covariant position.

    Args:
        small (str): Argument of the narrower container.
        big (str): Argument of the wider container.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when equal, when the wider one is a type variable of the
            module, or when ``small`` is within ``big``.

    """
    return (
        small == big
        or big in known.typevars
        or _within(
            small=_arms(text=small),
            big=_arms(text=big),
            known=known,
        )
    )


def _bare_generic(*, arm: str) -> tuple[str, ListStr] | None:
    """Read a bare container name as ``name[Any]``.

    Args:
        arm (str): One annotation arm.

    Returns:
        tuple[str, ListStr] | None:
            ``(name, ["Any"])`` when the arm names a generic
            container without arguments, else ``None``.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return None
    if isinstance(node, Name):
        head: str = node.id
    elif isinstance(node, Attribute):
        head = unparse(ast_obj=node).rpartition(".")[2]
    else:
        return None
    if (
        head in Hierarchy.ancestors
        or head in Hierarchy.covariant
        or head in Hierarchy.pairs
    ):
        return head, ["Any"]
    return None


def _container_within(*, small: str, big: str, known: Context) -> bool:
    """Tell whether a builtin container arm fits an abstract container arm.

    Args:
        small (str): A narrower arm such as ``list[int]``.
        big (str): A wider arm such as ``Sequence[int]``.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when ``small``'s origin derives from ``big``'s and the
            arguments fit with the right variance (invariant positions must be
            equal).

    """
    mine: tuple[str, ListStr] | None = _generic(arm=small) or _bare_generic(
        arm=small,
    )
    theirs: tuple[str, ListStr] | None = _generic(
        arm=big,
    ) or _bare_generic(arm=big)
    if mine is None or theirs is None:
        return False
    origin, args = mine
    base, wide = theirs
    if origin == base:
        return _same_origin_fit(
            origin=origin,
            written=args,
            truth=wide,
            known=known,
        )
    if base not in Hierarchy.ancestors.get(origin, frozenset()):
        return False
    if base in Hierarchy.covariant:
        elements: ListStr = [
            item for item in args if item not in {"...", "Ellipsis"}
        ]
        if origin in Constants.mapping_origins and elements:
            elements = elements[:1]
        return (
            len(wide) == 1
            and bool(elements)
            and all(
                _argument_fits(small=item, big=wide[0], known=known)
                for item in elements
            )
        )
    if base in Hierarchy.pairs:
        return (
            len(args) == len(wide) == Hierarchy.pair_size
            and _argument_fits(small=args[0], big=wide[0], known=known)
            and _argument_fits(small=args[1], big=wide[1], known=known)
        )
    return len(args) == len(wide) and all(
        _arg_within(small=one, big=other, known=known)
        for one, other in zip(args, wide, strict=False)
    )


def _within(
    *,
    small: SetStr,
    big: SetStr,
    known: Context | None = None,
) -> bool:
    """Tell whether every arm of ``small`` fits inside ``big``.

    Args:
        small (SetStr): Arms of the narrower candidate.
        big (SetStr): Arms of the wider candidate.
        known (Context | None): What the original module defines, for its type
            variables.

    Returns:
        bool: ``True`` when each arm is in ``big`` (numeric tower included),
            is a ``Literal`` of a scalar type that ``big`` accepts, or
            is a builtin container that fits an abstract one in ``big``.

    """
    roof: SetStr = _tower(arms=big)
    context: Context = Context() if known is None else known
    return bool({"object", "Any", Constants.wildcard} & big) or all(
        arm in roof
        or (
            arm.startswith("Literal[")
            and bool(roof & {"str", "int", "bytes", "bool"})
        )
        or (arm.startswith(("TypeGuard[", "TypeIs[")) and "bool" in roof)
        or any(
            _container_within(small=arm, big=wider, known=context)
            for wider in big
        )
        for arm in small
    )


def _foreign_ancestry(*, arm: str, known: Context) -> bool:
    """Tell whether a module class derives from something defined elsewhere.

    Such a class may be a subtype of the original annotation through a base
    this module does not show, so the scorer cannot call it a contradiction.

    Args:
        arm (str): One arm of what the fixer wrote.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when the arm names something the module does not define
            (an import) or a class of the module with a base that is neither a
            class of the module nor a builtin; the caller only asks when the
            original names abstract ``typing`` types.

    """
    head: str = arm.partition("[")[0]
    if head not in known.classes:
        return not (
            (head in __dict__) or hasattr(Constants.typing_module, head)
        )
    pending: ListStr = [head]
    seen: SetStr = set()
    while pending:
        name: str = pending.pop()
        if name in seen or name not in known.classes:
            continue
        seen.add(name)
        for base in known.bases.get(name, ()):
            if base in known.classes:
                pending.append(base)
            elif base not in __dict__ and not hasattr(
                Constants.typing_module,
                base,
            ):
                return True
    return False


def _resolvable(*, arm: str, known: Context) -> bool:
    """Tell whether an arm names something this module can account for.

    Args:
        arm (str): One arm of an annotation.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` for builtins, ``typing`` names, classes of the module
            and
            subscripts of those; ``False`` for names imported from elsewhere.

    """
    base: str = arm.split(sep="[", maxsplit=1)[0]
    return (
        base in known.classes
        or (base in __dict__)
        or hasattr(Constants.typing_module, base)
        or hasattr(Constants.typing_module, base)
    )


def _head(*, arm: str) -> str:
    """Read the origin name of an annotation arm.

    Args:
        arm (str): One annotation arm.

    Returns:
        str: The text before the first ``[``.

    """
    return arm.partition("[")[0]


def _callable_shape(*, arm: str) -> Shape | None:
    """Read a ``Callable[...]`` arm as a ``__call__`` method shape.

    Args:
        arm (str): The annotation arm.

    Returns:
        Shape | None: class:`Shape` with one ``__call__`` member, or ``None``
            when the arm is not a two-argument ``Callable``.

    """
    generic: tuple[str, ListStr] | None = _generic(arm=arm)
    if generic is None:
        return None
    origin, args = generic
    if origin != "Callable" or len(args) != Constants.callable_arity:
        return None
    params: ListStr | None = _callable_params(text=args[0])
    return Shape(
        attrs={},
        methods={
            "__call__": (
                None if params is None else tuple(params),
                normalize_annotation(text=args[1]),
            ),
        },
    )


def _typing_protocol(*, arm: str) -> Shape | None:
    """Synthesize the member shape of a ``typing`` iteration protocol.

    The first generic argument fills the element type; a bare protocol
    reads as ``Any``. Only protocols whose members are a fixed set of
    dunders are synthesized — containers with overloaded accessors such
    as ``Sequence`` or ``Mapping`` stay opaque.

    Args:
        arm (str): One annotation arm.

    Returns:
        Shape | None: class:`Shape` for a known protocol name, or ``None``.

    """
    base: str = _head(arm=arm).rsplit(sep=".", maxsplit=1)[-1]
    if base not in Constants.typing_protocols:
        return None
    generic: tuple[str, ListStr] | None = _generic(arm=arm)
    arg: str = generic[1][0] if generic is not None and generic[1] else "Any"
    iterator: str = f"Iterator[{arg}]"
    async_iterator: str = f"AsyncIterator[{arg}]"
    members: dict[str, Shape] = {
        "AsyncIterable": Shape(
            attrs={},
            methods={"__aiter__": ((), async_iterator)},
        ),
        "AsyncIterator": Shape(
            attrs={},
            methods={
                "__aiter__": ((), async_iterator),
                "__anext__": ((), arg),
            },
        ),
        "Collection": Shape(
            attrs={},
            methods={
                "__contains__": (("object",), "bool"),
                "__iter__": ((), iterator),
                "__len__": ((), "int"),
            },
        ),
        "Container": Shape(
            attrs={},
            methods={"__contains__": (("object",), "bool")},
        ),
        "Hashable": Shape(attrs={}, methods={"__hash__": ((), "int")}),
        "Iterable": Shape(attrs={}, methods={"__iter__": ((), iterator)}),
        "Iterator": Shape(
            attrs={},
            methods={
                "__iter__": ((), iterator),
                "__next__": ((), arg),
            },
        ),
        "Reversible": Shape(
            attrs={},
            methods={"__reversed__": ((), iterator)},
        ),
        "Sized": Shape(attrs={}, methods={"__len__": ((), "int")}),
    }
    return members[base]


def _shape_of(*, arm: str, known: Context) -> Shape | str | None:
    """Resolve an annotation arm to a member shape.

    Args:
        arm (str): One annotation arm.
        known (Context): What the original module defines.

    Returns:
        Shape | str | None:
            class:`Shape` for module classes, protocols, ``Callable``
            arms and synthesized ``typing`` protocols; the bare name
            for builtins and ``typing`` names (members are probed with
            ``hasattr``); ``None`` for names the module cannot account for.

    """
    base: str = _head(arm=arm)
    if base == "Callable":
        return _callable_shape(arm=arm)
    shape: Shape | None = known.shapes.get(base)
    if shape is not None:
        return shape
    protocol: Shape | None = _typing_protocol(arm=arm)
    if protocol is not None:
        return protocol
    if (base in __dict__) or hasattr(Constants.typing_module, base):
        return base
    return None


def _has_member(*, impl: Shape | str, name: str) -> bool:
    """Tell whether an implementation shape provides a member.

    Args:
        impl (Shape | str): Shape of the implementing side, or a
            builtin/``typing`` name.
        name (str): Member name.

    Returns:
        bool: ``True`` when the member exists.

    """
    if isinstance(impl, Shape):
        return name in impl.attrs or name in impl.methods
    if (
        target := __dict__.get(
            impl,
            getattr(Constants.typing_module, impl, None),
        )
    ) is None:
        return False
    return hasattr(target, name)


def _attr_ann(*, impl: Shape | str, name: str) -> str:
    """Read an implementation's annotation for an attribute.

    Args:
        impl (Shape | str): Shape of the implementing side, or a
            builtin/``typing`` name.
        name (str): Attribute name.

    Returns:
        str: The normalized annotation, or ``""`` when unknown (builtins and
            unannotated attributes carry no checkable type).

    """
    if isinstance(impl, Shape):
        return impl.attrs.get(name, "")
    return ""


def _method_sig(
    *,
    impl: Shape | str,
    name: str,
) -> tuple[tuple[str, ...] | None, str] | None:
    """Read an implementation's signature for a method.

    Args:
        impl (Shape | str): Shape of the implementing side, or a
            builtin/``typing`` name.
        name (str): Method name.

    Returns:
        tuple[tuple[str, ...] | None, str] | None:
            ``(parameters, returns)`` with ``None`` parameters for an
            any-signature member, or ``None`` when the method is absent.

    """
    if isinstance(impl, Shape):
        return impl.methods.get(name)
    if (
        target := __dict__.get(
            impl,
            getattr(Constants.typing_module, impl, None),
        )
    ) is None:
        return None
    if callable(getattr(target, name, None)):
        return (None, "")
    return None


def _ann_fits(
    *,
    small: str,
    big: str,
    known: Context,
    seen: frozenset[tuple[str, str]],
) -> bool:
    """Tell whether one member annotation fits another's requirement.

    Args:
        small (str): Annotation the implementation provides.
        big (str): Annotation the protocol requires.
        known (Context): What the original module defines.
        seen (frozenset[tuple[str, str]]): Protocol pairs already being
            compared (coinductive guard).

    Returns:
        bool: ``True`` when equal, empty, ``small`` within ``big``, or a
            non-contradictory protocol relation holds; ``False`` on a proven
            contradiction.

    """
    if not small or not big or small == big:
        return True
    if _within(small=_arms(text=small), big=_arms(text=big), known=known):
        return True
    return (
        _protocol_relation(written=small, truth=big, known=known, seen=seen)
        is not None
    )


def _sig_fits(
    *,
    impl: tuple[tuple[str, ...] | None, str],
    proto: tuple[tuple[str, ...] | None, str],
    known: Context,
    seen: frozenset[tuple[str, str]],
) -> bool:
    """Tell whether an implementation signature meets a protocol's.

    Args:
        impl (tuple[tuple[str, ...] | None, str]): ``(parameters, returns)``
            the implementation provides.
        proto (tuple[tuple[str, ...] | None, str]): ``(parameters, returns)``
            the protocol requires.
        known (Context): What the original module defines.
        seen (frozenset[tuple[str, str]]): Protocol pairs already being
            compared.

    Returns:
        bool: ``True`` when parameter counts match (unless either side is
            any-signature) and every annotation fits.

    """
    impl_params, impl_returns = impl
    proto_params, proto_returns = proto
    params_fit: bool = impl_params is None or (
        proto_params is not None
        and len(impl_params) == len(proto_params)
        and all(
            _ann_fits(small=one, big=other, known=known, seen=seen)
            for one, other in zip(impl_params, proto_params, strict=False)
        )
    )
    if not params_fit:
        return False
    return _ann_fits(
        small=impl_returns,
        big=proto_returns,
        known=known,
        seen=seen,
    )


def _shape_covers(
    *,
    impl: Shape | str | None,
    proto: Shape,
    known: Context,
    seen: frozenset[tuple[str, str]],
) -> bool:
    """Tell whether ``impl`` provides every member ``proto`` requires.

    Args:
        impl (Shape | str | None): Shape of the implementing side (``None``
            when unknown).
        proto (Shape): Shape of the required side.
        known (Context): What the original module defines.
        seen (frozenset[tuple[str, str]]): Protocol pairs already being
            compared.

    Returns:
        bool: ``True`` when every protocol attribute and method is present with
            a fitting signature.

    """
    if impl is None:
        return False
    for name, annotation in proto.attrs.items():
        if not _has_member(impl=impl, name=name):
            return False
        if not _ann_fits(
            small=_attr_ann(impl=impl, name=name),
            big=annotation,
            known=known,
            seen=seen,
        ):
            return False
    for name, signature in proto.methods.items():
        impl_signature: tuple[tuple[str, ...] | None, str] | None = (
            _method_sig(impl=impl, name=name)
        )
        if impl_signature is None:
            return False
        if not _sig_fits(
            impl=impl_signature,
            proto=signature,
            known=known,
            seen=seen,
        ):
            return False
    return True


def _protocol_relation(
    *,
    written: str,
    truth: str,
    known: Context,
    seen: frozenset[tuple[str, str]] = frozenset(),
) -> str | None:
    """Compare two arms name-agnostically when a ``Protocol`` is involved.

    Compares member structure instead of names: an implementation covers a
    protocol when it provides every required attribute and method with a
    fitting signature. Recursive references assume compatibility
    (coinductive), matching how type checkers read recursive protocols.

    Args:
        written (str): What the fixer wrote.
        truth (str): The original annotation.
        known (Context): What the original module defines.
        seen (frozenset[tuple[str, str]]): Protocol pairs already being
            compared.

    Returns:
        str | None: ``"exact"`` when each side covers the other, ``"narrower"``
            when only the written side covers, ``"looser"`` when
            only the truth side covers, and ``None`` when no
            protocol is involved or neither side covers the other.

    """
    written_base: str = _head(arm=written)
    truth_base: str = _head(arm=truth)
    if written_base == "Callable" and truth_base == "Callable":
        return None
    pair: tuple[str, str] = (written_base, truth_base)
    if pair in seen or (truth_base, written_base) in seen:
        return "exact"
    seen = seen | {pair}
    written_shape: Shape | str | None = _shape_of(arm=written, known=known)
    truth_shape: Shape | str | None = _shape_of(arm=truth, known=known)
    written_protocol: bool = (
        written_base in known.protocols
        or written_base == "Callable"
        or written_base.rsplit(sep=".", maxsplit=1)[-1]
        in Constants.typing_protocols
    )
    truth_protocol: bool = (
        truth_base in known.protocols
        or truth_base == "Callable"
        or truth_base.rsplit(sep=".", maxsplit=1)[-1]
        in Constants.typing_protocols
    )
    if (
        written_shape is None
        or truth_shape is None
        or not (written_protocol or truth_protocol)
    ):
        return None
    written_covers: bool = (
        _shape_covers(
            impl=written_shape,
            proto=truth_shape,
            known=known,
            seen=seen,
        )
        if isinstance(truth_shape, Shape) and truth_protocol
        else False
    )
    truth_covers: bool = (
        _shape_covers(
            impl=truth_shape,
            proto=written_shape,
            known=known,
            seen=seen,
        )
        if isinstance(written_shape, Shape) and written_protocol
        else False
    )
    if written_covers and truth_covers:
        return "exact"
    if written_covers:
        return "narrower"
    return "looser" if truth_covers else None


@lru_cache(maxsize=4096)
def _wildcarded(*, arm: str) -> str:
    """Replace ``object`` arguments of a truth arm by the wildcard marker.

    A bare ``object`` arm is left alone: the top-level ``object`` check in
    :func:`_within` already accepts anything. Nested occurrences (generic
    arguments, ``Callable`` parameters and returns) become wildcards so a
    written argument always fits them as ``narrower``.

    Args:
        arm: One normalized annotation arm.

    Returns:
        The arm with ``object`` names replaced, or the arm unchanged when
        it does not parse.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return arm
    if isinstance(node, Name) and node.id == "object":
        return arm
    for inner in walk(node=node):
        if isinstance(inner, Name) and inner.id == "object":
            inner.id = Constants.wildcard
    return unparse(ast_obj=node)


def relation(
    *,
    written: str,
    truth: str,
    context: Context | None = None,
) -> str | None:
    """Say how a written annotation relates to the original one.

    Args:
        written (str): What the fixer wrote.
        truth (str): The original annotation.
        context (Context | None): Aliases and classes of the original module,
            if known.

    Returns:
        str | None: ``None`` when they mean the same, ``"narrower"`` when the
            written type is a subtype of the original, ``"looser"`` when
            it is a supertype, ``"unresolved"`` when the original names
            something imported that cannot be judged from this module,
            and ``"contradiction"`` otherwise. ``NoReturn`` is the empty
            type, ``Any`` accepts everything, ``Self`` is a subtype of
            its class, and the original module's aliases are unfolded.

    """
    known: Context = Context() if context is None else context
    ours: SetStr = _arms(text=normalize_annotation(text=written))
    theirs: SetStr = _arms(text=normalize_annotation(text=truth))
    if ours == theirs:
        return None
    ours = _expand(arms=ours, context=known)
    theirs = _expand(arms=theirs, context=known)
    ours = {v for arm in ours for v in _resolved(arm=arm, context=known)}
    theirs = {v for arm in theirs for v in _resolved(arm=arm, context=known)}
    theirs = {_wildcarded(arm=arm) for arm in theirs}
    if "Self" in ours and theirs & known.classes:
        ours = (ours - {"Self"}) | (theirs & known.classes)
        return "narrower"
    if ours == theirs:
        return None
    if len(ours) == 1 and len(theirs) == 1:
        kind: str | None = _protocol_relation(
            written=next(iter(ours)),
            truth=next(iter(theirs)),
            known=known,
        )
        if kind is not None:
            return None if kind == "exact" else kind
    if len(ours) == 1 and len(theirs) > 1:
        written_arm: str = next(iter(ours))
        for truth_arm in theirs:
            kind = _protocol_relation(
                written=written_arm,
                truth=truth_arm,
                known=known,
            )
            if kind in {"exact", "narrower"}:
                return "narrower"
    return _classify(ours=ours, theirs=theirs, known=known)


def _typevar_arm(*, arm: str, known: Context) -> bool:
    """Tell whether an arm mentions a type variable.

    Args:
        arm (str): One annotation arm.
        known (Context): What the original module defines.

    Returns:
        bool: ``True`` when any name inside the arm is a type variable of the
            module or a ``typing`` type variable such as ``T``.

    """
    try:
        node: expr = parse(source=arm, mode="eval").body
    except SyntaxError:
        return False
    for child in walk(node=node):
        if isinstance(child, Name):
            head: str = child.id
        elif isinstance(child, Attribute):
            head = unparse(ast_obj=child).rpartition(".")[2]
        else:
            continue
        if head in known.typevars:
            return True
        if isinstance(
            getattr(Constants.typing_module, head, None),
            (TypeVar, ParamSpec, TypeVarTuple),
        ):
            return True
    return False


def _classify(*, ours: SetStr, theirs: SetStr, known: Context) -> str:
    """Compare two resolved arm sets that are not the same.

    Args:
        ours (SetStr): Arms of what the fixer wrote.
        theirs (SetStr): Arms of the original.
        known (Context): What the original module defines.

    Returns:
        str: ``"narrower"`` , ``"looser"`` ,
            ``"unresolved"`` or ``"contradiction"``.

    """
    ours_effective: SetStr = ours - {"NoReturn"}
    theirs_effective: SetStr = theirs - {"NoReturn"}
    if "Any" in theirs or _within(
        small=ours_effective,
        big=theirs_effective,
        known=known,
    ):
        return "narrower"
    if "Any" in ours or _within(
        small=theirs_effective,
        big=ours_effective,
        known=known,
    ):
        return "looser"
    if any(
        _typevar_arm(arm=arm, known=known)
        for arm in ours_effective | theirs_effective
    ):
        return "unresolved"
    if not all(
        _resolvable(arm=arm, known=known) for arm in theirs_effective
    ) or not all(_resolvable(arm=arm, known=known) for arm in ours_effective):
        return "unresolved"
    if all(
        hasattr(Constants.typing_module, arm.partition("[")[0])
        for arm in theirs_effective
    ) and any(
        _foreign_ancestry(arm=arm, known=known) for arm in ours_effective
    ):
        return "unresolved"
    return "contradiction"


def annotation_map(
    *,
    source: str,
    tree: Module | None = None,
) -> DictStr:
    """List the parameter and return annotations of a module.

    Args:
        source (str): Python source.
        tree (Module | None): Existing module to reuse instead of parsing
            source.

    Returns:
        DictStr: Normalised annotation text by
            ``function.parameter`` or ``function->``.

    """
    out: DictStr = {}
    _walk_functions(
        node=parse(source=source) if tree is None else tree,
        trail=(),
        out=out,
    )
    return out


def _walk_variables(
    *,
    body: Sequence[stmt],
    trail: tuple[str, ...],
    out: DictStr,
) -> None:
    """Collect annotated variables keyed by their scope.

    Args:
        body (Sequence[stmt]): Statements of one scope.
        trail (tuple[str, ...]): Qualified-name prefix.
        out (DictStr): Destination mapping, extended in place.

    """
    for node in body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef)):
            _walk_variables(
                body=node.body,
                trail=(*trail, node.name),
                out=out,
            )
            continue
        if isinstance(node, AnnAssign) and isinstance(node.target, Name):
            out[".".join((*trail, node.target.id))] = normalize_annotation(
                text=unparse(ast_obj=node.annotation),
            )
        for branch in ("body", "orelse", "finalbody"):
            inner: Sequence[stmt] | None = getattr(node, branch, None)
            if isinstance(inner, list):
                _walk_variables(body=inner, trail=trail, out=out)


def variable_map(*, source: str, tree: Module | None = None) -> DictStr:
    """List the annotated variables of a module.

    Args:
        source (str): Python source.
        tree (Module | None): Existing module to reuse instead of parsing
            source.

    Returns:
        DictStr: Normalised annotation by ``scope.name``.

    """
    found: DictStr = {}
    _walk_variables(
        body=(parse(source=source) if tree is None else tree).body,
        trail=(),
        out=found,
    )
    return found


def strip_annotations(*, source: str) -> str:
    """Remove every parameter and return annotation from a module.

    Args:
        source (str): Python source.

    Returns:
        str: The module re-rendered without those annotations (formatting and
            comments are not kept; this is benchmark input only).

    """
    tree: AST = parse(source=source)
    for node in walk(node=tree):
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            node.returns = None
        elif isinstance(node, arg):
            node.annotation = None
    return unparse(ast_obj=tree) + "\n"


def _invented_names(*, source: str) -> SetStr:
    """List the module-level names that are protocols or type variables.

    Args:
        source (str): Python source.

    Returns:
        SetStr: Names of classes deriving from ``Protocol``
            and of ``TypeVar`` assignments.

    """
    names: SetStr = set()
    for node in parse(source=source).body:
        if isinstance(node, ClassDef) and any(
            unparse(ast_obj=base).split(sep=".")[-1] == "Protocol"
            for base in node.bases
        ):
            names.add(node.name)
        elif (
            isinstance(node, Assign)
            and isinstance(node.value, Call)
            and unparse(ast_obj=node.value.func).split(sep=".")[-1]
            == "TypeVar"
        ):
            names.update(
                target.id
                for target in node.targets
                if isinstance(target, Name)
            )
    return names


def _targets(
    *,
    node: AST,
    trail: tuple[str, ...],
    out: dict[str, AST],
) -> None:
    """Index functions and parameters by their qualified key.

    Args:
        node (AST): Node whose children are scanned.
        trail (tuple[str, ...]): Qualified-name prefix.
        out (dict[str, AST]): Destination mapping, extended in place.

    """
    for child in getattr(node, "body", []):
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            name: str = ".".join((*trail, child.name))
            out[f"{name}->"] = child
            for parameter in walk(node=child.args):
                if isinstance(parameter, arg):
                    out[f"{name}.{parameter.arg}"] = parameter
            _targets(node=child, trail=(*trail, child.name), out=out)
        elif isinstance(child, ClassDef):
            _targets(node=child, trail=(*trail, child.name), out=out)


def attribute_misses(
    *,
    source: str,
    missed: Sequence[str],
) -> tuple[tuple[str, int], ...]:
    """Say why the fixer left annotations out.

    Args:
        source (str): The module after fixing.
        missed (Sequence[str]): Keys the original annotated and the fixer did
            not.

    Returns:
        tuple[tuple[str, int], ...]: ``(reason, count)`` pairs, most frequent
            first. The reason is the
            hint index's refusal (taint details dropped), or ``not judged``
            for subjects the index never considered (receivers, variadics).

    """
    module: CommentedModule = parse_module(source=source, filename="miss.py")
    index: HintIndex = LazyHints(
        module=module,
        stubs_path=None,
        source=source,
        cache=None,
    ).index()
    nodes: dict[str, AST] = {}
    _targets(node=module, trail=(), out=nodes)
    counts: Counter[str] = Counter()
    for key in missed:
        node: AST | None = nodes.get(key)
        reason: str | None = (
            None
            if node is None
            else index.rejection_for(
                node=node,
            )
        )
        counts[
            "not judged"
            if reason is None
            else str(object=reason).split(sep=" by parameter")[0]
        ] += 1
    return tuple(sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])))


@final
@dataclass(frozen=True, slots=True)
class RecoveryOptions:
    """Choices of one recovery run.

    Attributes:
        ceiling (FixSafety): Highest fix safety to apply.
        checker (Checker | None): External checker gate, or ``None``.
        attribute (bool): Whether to explain the missed annotations
            (costs one more inference run).
        delta (PyrightChecker | MypyChecker | None): A checker used to count
            the new errors the
            fixes introduce (two checker runs per module).
        min_confidence (float): Least confidence a fix needs, as in the CLI.
        negotiate (bool): Whether negotiated hints supplement the hint index.
        annotate_variables (bool): Whether local variables are annotated.
        engine (bool): Conversion mode (the engine's own annotations).

    """

    ceiling: FixSafety = FixSafety.guarded
    checker: Checker | None = None
    attribute: bool = False
    delta: PyrightChecker | MypyChecker | None = None
    min_confidence: float = ConfidenceConstants.default_minimum
    negotiate: bool = True
    annotate_variables: bool = False
    engine: bool = False


def recover(
    *,
    source: str,
    filename: str,
    options: RecoveryOptions | None = None,
) -> RecoveryScore:
    """Strip a typed module, fix it, and score the recovered annotations.

    Args:
        source (str): Python source of a well-typed module.
        filename (str): Name used for the fix run.
        options (RecoveryOptions | None): Ceiling, checker gate, attribution
            and delta;
            defaults to the guarded ceiling with nothing else.

    Returns:
        RecoveryScore:
            Precision and recall counts against the original annotations.

    """
    chosen: RecoveryOptions = options or RecoveryOptions()
    truth: DictStr = annotation_map(source=source)
    registries: Registries = default_registries()
    stripped: str = strip_annotations(source=source)
    started: float = perf_counter()
    result: FixResult = fix_source(
        source=stripped,
        filename=filename,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=chosen.ceiling,
            checker=chosen.checker,
            min_confidence=chosen.min_confidence,
            negotiate=chosen.negotiate,
            annotate_variables=chosen.annotate_variables,
            engine=chosen.engine,
        ),
    )
    seconds: float = perf_counter() - started
    written: DictStr = annotation_map(source=result.source)
    invented: SetStr = _invented_names(source=result.source)
    synthesized: tuple[str, ...] = tuple(
        sorted(
            key
            for key, text in written.items()
            if key not in truth
            or any(
                isinstance(node, Name) and node.id in invented
                for node in walk(node=parse(source=text, mode="eval"))
            )
        ),
    )
    judged: DictStr = {
        key: text for key, text in written.items() if key not in synthesized
    }
    correct: int = sum(
        1 for key, text in judged.items() if truth.get(key) == text
    )
    known: Context = module_context(source=source)
    differing: DictStr = {
        key: kind
        for key, text in judged.items()
        if key in truth
        and truth[key] != text
        and (
            kind := relation(
                written=text,
                truth=truth[key],
                context=known,
            )
        )
        is not None
    }
    wrong: tuple[str, ...] = tuple(
        sorted(
            f"{key}: wrote {judged[key]!r}, expected {truth[key]!r}"
            for key, kind in differing.items()
            if kind == "contradiction"
        ),
    )
    compatible: tuple[str, ...] = tuple(
        sorted(
            f"{key}: wrote {judged[key]!r} ({kind}), expected {truth[key]!r}"
            for key, kind in differing.items()
            if kind != "contradiction"
        ),
    )
    missed: tuple[str, ...] = tuple(
        sorted(key for key in truth if key not in written),
    )
    return RecoveryScore(
        truth=len(truth),
        correct=correct,
        wrong=wrong,
        compatible=compatible,
        missed=missed,
        synthesized=synthesized,
        seconds=seconds,
        rounds=result.rounds,
        new_errors=(
            None
            if chosen.delta is None
            else chosen.delta.new_errors(
                filename=filename,
                before=stripped,
                after=result.source,
            )
        ),
        missed_reasons=(
            attribute_misses(source=result.source, missed=missed)
            if chosen.attribute
            else ()
        ),
    )
