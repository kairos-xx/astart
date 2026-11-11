"""Resolve registered Python type expressions without evaluating source."""

from __future__ import annotations

from ast import (
    Attribute,
    BinOp,
    BitOr,
    Constant,
    List,
    Name,
    Subscript,
    Tuple,
    expr,
    parse,
)
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import nullcontext
from inspect import currentframe
from pathlib import Path
from sys import stdout
from textwrap import dedent
from types import EllipsisType, FrameType, GenericAlias, UnionType
from typing import IO, ClassVar, TextIO, cast, final

type TypeForm = type | GenericAlias | UnionType
type OptionalString = str | None
type TypeAtom = TypeForm | OptionalString
type TypeMembers = tuple[TypeAtom, ...]
type TypeInput = TypeAtom | TypeMembers | list[TypeAtom]
type TypeNamespace = Mapping[str, type]
type AnnotationItems = tuple[expr, ...]
type GenericArgument = TypeForm | EllipsisType
type CallableParameters = list[TypeForm] | EllipsisType
type CallableArguments = tuple[CallableParameters, TypeForm]
type CallableSubscription = Callable[[CallableArguments], GenericAlias]
type DictType = dict[str, type]
type TypeUnionDictType = dict[str, TypeForm]


def aprint(
    *args: object,
    sep: OptionalString = None,
    end: OptionalString = None,
    file: str | Path | TextIO | None = None,
    mode: str = "a",
    flush: bool = False,
) -> None:
    """Write printable values to a stream or UTF-8 file.

    Args:
        *args (object): Values converted to strings.
        sep (str | None): Separator; defaults to a space.
        end (str | None): Terminator; defaults to a newline.
        file (str | Path | TextIO | None): Output path or stream.
        mode (str): File opening mode when a path is supplied.
        flush (bool): Flush the stream after writing.

    """
    separator: str = sep if sep is not None else " "
    stream: IO[str]
    with (
        Path(file).open(mode=mode, encoding="utf-8")
        if isinstance(file, str | Path)
        else nullcontext(enter_result=file if file is not None else stdout)
    ) as stream:
        _ = stream.write(
            separator.join(map(str, args))
            + (end if end is not None else "\n"),
        )
        if flush:
            stream.flush()


@final
class _TypeResolver:
    """Resolve registered annotation expressions without source execution."""

    types: ClassVar[DictType] = {
        "bool": bool,
        "bytes": bytes,
        "bytearray": bytearray,
        "complex": complex,
        "dict": dict,
        "float": float,
        "frozenset": frozenset,
        "int": int,
        "list": list,
        "memoryview": memoryview,
        "object": object,
        "range": range,
        "set": set,
        "slice": slice,
        "str": str,
        "tuple": tuple,
        "type": type,
        "None": type(None),
    }
    generics: ClassVar[DictType] = {
        "Mapping": Mapping,
        "Sequence": Sequence,
        "Iterable": Iterable,
        "collections.abc.Mapping": Mapping,
        "collections.abc.Sequence": Sequence,
        "collections.abc.Iterable": Iterable,
    }
    special: ClassVar[frozenset[str]] = frozenset(
        {
            "Union",
            "Optional",
            "Literal",
            "Annotated",
            "Required",
            "NotRequired",
            "Callable",
        },
    )
    _callable_arguments: ClassVar[int] = 2
    _annotated_arguments: ClassVar[int] = 2

    def __init__(self, *, namespace: TypeNamespace | None = None) -> None:
        """Initialize the registered type namespace.

        Args:
            namespace (TypeNamespace | None): Custom class registry.

        Raises:
            ValueError: If a registered name is reserved.

        """
        self._names: DictType = {**self.types, **self.generics}
        for name, value in (namespace or {}).items():
            if name in self._names or name in self.special:
                msg: str = f"Reserved type name: {name}"
                raise ValueError(msg)
            self._names[name] = value

    @staticmethod
    def _name(*, node: expr) -> str:
        """Extract a qualified identifier without accessing attributes.

        Args:
            node (expr): Identifier expression.

        Returns:
            str: Qualified identifier.

        Raises:
            TypeError: If the expression is not an identifier.

        """
        if isinstance(node, Name):
            return node.id
        if isinstance(node, Attribute):
            return f"{_TypeResolver._name(node=node.value)}.{node.attr}"
        msg: str = "Expected a registered type identifier."
        raise TypeError(msg)

    @staticmethod
    def _items(*, node: expr) -> AnnotationItems:
        """Extract subscription arguments.

        Args:
            node (expr): Subscription slice.

        Returns:
            AnnotationItems: Individual argument expressions.

        """
        return tuple(node.elts) if isinstance(node, Tuple) else (node,)

    @staticmethod
    def _combine(*, left: TypeForm, right: TypeForm) -> TypeForm:
        """Combine two runtime type expressions.

        Args:
            left (TypeForm): Left union member.
            right (TypeForm): Right union member.

        Returns:
            TypeForm: Combined runtime union.

        """
        return left | right

    @staticmethod
    def _subscribe_callable(*, arguments: CallableArguments) -> GenericAlias:
        """Construct a callable alias using native subscription semantics.

        Args:
            arguments (CallableArguments): Callable parameter types and
                return annotation.

        Returns:
            GenericAlias: Native parameterized callable alias.

        Raises:
            AttributeError: If native Callable subscription is unavailable.

        """

        def _missing(*, arguments: CallableArguments) -> GenericAlias:
            """Reject unavailable native Callable subscription.

            Args:
                arguments (CallableArguments): Callable subscription arguments.

            Raises:
                AttributeError: Always, because native subscription is missing.

            """
            _ = arguments
            msg: str = "Callable.__class_getitem__ is unavailable."
            raise AttributeError(msg)

        subscription: CallableSubscription = cast(
            typ="CallableSubscription",
            val=getattr(Callable, "__class_getitem__", _missing),
        )
        return subscription(arguments)

    def _resolve_name(self, *, node: expr) -> TypeForm:
        """Resolve an explicitly registered type identifier.

        Args:
            node (expr): Name or qualified identifier.

        Returns:
            TypeForm: Registered runtime class.

        Raises:
            ValueError: If the identifier is not registered.

        """
        identifier: str = self._name(node=node)
        if identifier not in self._names:
            msg: str = f"Unknown type name: {identifier}"
            raise ValueError(msg)
        return self._names[identifier]

    def _resolve_union(self, *, node: BinOp) -> TypeForm:
        """Resolve a binary union expression.

        Args:
            node (BinOp): Union expression.

        Returns:
            TypeForm: Combined runtime union.

        """
        return self._combine(
            left=self.resolve(node=node.left),
            right=self.resolve(node=node.right),
        )

    def _resolve_union_items(self, *, items: AnnotationItems) -> TypeForm:
        """Resolve members of a parameterized union.

        Args:
            items (AnnotationItems): Union members.

        Returns:
            TypeForm: Combined runtime union.

        Raises:
            TypeError: If the union has no members.

        """
        if not items:
            msg: str = "Union requires at least one member."
            raise TypeError(msg)
        result: TypeForm = self.resolve(node=items[0])
        for item in items[1:]:
            result = self._combine(left=result, right=self.resolve(node=item))
        return result

    def _resolve_optional(self, *, items: AnnotationItems) -> TypeForm:
        """Resolve an Optional annotation.

        Args:
            items (AnnotationItems): Optional arguments.

        Returns:
            TypeForm: Nullable runtime union.

        Raises:
            TypeError: If the argument count is invalid.

        """
        if len(items) != 1:
            msg: str = "Optional requires exactly one argument."
            raise TypeError(msg)
        return self._combine(
            left=self.resolve(node=items[0]),
            right=type(None),
        )

    def _resolve_callable(self, *, items: AnnotationItems) -> TypeForm:
        """Resolve a callable annotation with native subscription semantics.

        Args:
            items (AnnotationItems): Parameter signature and return type.

        Returns:
            TypeForm: Native parameterized callable alias.

        Raises:
            TypeError: If the callable signature is unsupported.
            AttributeError: If native callable subscription is unavailable.

        """
        if len(items) != self._callable_arguments:
            msg: str = "Callable requires parameters and a return type."
            raise TypeError(msg)
        result: TypeForm = self.resolve(node=items[1])
        if isinstance(items[0], List):
            parameters: CallableParameters = [
                self.resolve(node=item) for item in items[0].elts
            ]
        elif isinstance(items[0], Constant) and items[0].value is Ellipsis:
            parameters = Ellipsis
        else:
            msg = "Callable parameters must be a list or ellipsis."
            raise TypeError(msg)
        return self._subscribe_callable(
            arguments=(parameters, result),
        )

    def _resolve_special(
        self,
        *,
        identifier: str,
        items: AnnotationItems,
    ) -> TypeForm:
        """Resolve a recognized special typing construct.

        Args:
            identifier (str): Special typing identifier.
            items (AnnotationItems): Subscription arguments.

        Returns:
            TypeForm: Resolved runtime annotation.

        Raises:
            TypeError: If the construct is unsupported.

        """
        if identifier == "Union":
            return self._resolve_union_items(items=items)
        if identifier == "Optional":
            return self._resolve_optional(items=items)
        if identifier == "Callable":
            return self._resolve_callable(items=items)
        if (
            identifier == "Annotated"
            and len(items) < self._annotated_arguments
        ):
            msg: str = "Annotated requires a type and metadata."
            raise TypeError(msg)
        if identifier in {"Required", "NotRequired"} and len(items) != 1:
            msg = f"{identifier} requires exactly one argument."
            raise TypeError(msg)
        msg = (
            f"{identifier} cannot be represented by the "
            "restricted TypeForm model."
        )
        raise TypeError(msg)

    def _resolve_generic(
        self,
        *,
        identifier: str,
        items: AnnotationItems,
    ) -> TypeForm:
        """Resolve a subscription of an approved generic origin.

        Args:
            identifier (str): Registered generic origin.
            items (AnnotationItems): Generic arguments.

        Returns:
            TypeForm: Parameterized generic alias.

        Raises:
            TypeError: If the origin is not approved.

        """
        if identifier not in self.types and identifier not in self.generics:
            msg: str = f"Untrusted generic subscription: {identifier}"
            raise TypeError(msg)
        arguments: tuple[GenericArgument, ...] = tuple(
            Ellipsis
            if isinstance(item, Constant) and item.value is Ellipsis
            else self.resolve(node=item)
            for item in items
        )
        return GenericAlias(self._names[identifier], arguments)

    def _resolve_subscript(self, *, node: Subscript) -> TypeForm:
        """Resolve an approved generic or special typing expression.

        Args:
            node (Subscript): Subscription expression.

        Returns:
            TypeForm: Resolved runtime annotation.

        Raises:
            TypeError: If the subscription is unsupported.

        """
        identifier: str = self._name(node=node.value)
        items: AnnotationItems = self._items(node=node.slice)
        short_name: str = identifier.removeprefix("typing.")
        if short_name in self.special:
            return self._resolve_special(identifier=short_name, items=items)
        return self._resolve_generic(identifier=identifier, items=items)

    def resolve(self, *, node: expr) -> TypeForm:
        """Resolve a supported annotation AST expression.

        Args:
            node (expr): Annotation expression.

        Returns:
            TypeForm: Resolved runtime annotation.

        Raises:
            TypeError: If the expression is unsupported.
            ValueError: If a referenced name is unknown.

        """
        if isinstance(node, Constant) and node.value is None:
            return type(None)
        if isinstance(node, (Name, Attribute)):
            return self._resolve_name(node=node)
        if isinstance(node, BinOp) and isinstance(node.op, BitOr):
            return self._resolve_union(node=node)
        if isinstance(node, Subscript):
            return self._resolve_subscript(node=node)
        msg: str = f"Unsupported annotation expression: {type(node).__name__}"
        raise TypeError(msg)

    def normalize(self, *, member: TypeAtom) -> TypeForm:
        """Normalize a runtime type or textual annotation.

        Args:
            member (TypeAtom): Type expression to normalize.

        Returns:
            TypeForm: Resolved runtime annotation.

        Raises:
            TypeError: If the expression is unsupported.
            ValueError: If a referenced name is unknown.
            SyntaxError: If annotation syntax is invalid.

        """
        if member is None:
            return type(None)
        if isinstance(member, str):
            return self.resolve(node=parse(source=member, mode="eval").body)
        return member


@final
class TypeUnionDict(dict[str, TypeForm]):
    """Normalize registered runtime types and textual type expressions."""

    def __init__(
        self,
        values: Mapping[str, TypeInput],
        *,
        namespace: TypeNamespace | None = None,
    ) -> None:
        """Initialize the dictionary with normalized annotations.

        Args:
            values (Mapping[str, TypeInput]): Field type expressions.
            namespace (TypeNamespace | None): Custom classes.
                If omitted, discover classes in the constructor
                caller's globals and locals.

        Raises:
            TypeError: If an expression is unsupported.
            ValueError: If a referenced name is unknown.
            SyntaxError: If annotation syntax is invalid.

        """
        if namespace is None:
            frame: FrameType | None = currentframe()
            try:
                caller: FrameType | None = (
                    frame.f_back if frame is not None else None
                )
                if caller is None:
                    msg: str = (
                        "Cannot inspect the TypeUnionDict constructor caller."
                    )
                    raise RuntimeError(msg)
                namespace = {
                    name: value
                    for name, value in {
                        **caller.f_globals,
                        **caller.f_locals,
                    }.items()
                    if isinstance(value, type)
                    and name not in _TypeResolver.types
                    and name not in _TypeResolver.generics
                    and name not in _TypeResolver.special
                }
            finally:
                del frame
        resolver: _TypeResolver = _TypeResolver(namespace=namespace)
        for key, value in values.items():
            self[key] = self._union(
                resolver=resolver,
                members=(
                    tuple(value)
                    if isinstance(value, (tuple, list))
                    else (value,)
                ),
            )

    @staticmethod
    def _union(
        *,
        resolver: _TypeResolver,
        members: TypeMembers,
    ) -> TypeForm:
        """Combine normalized runtime type expressions.

        Args:
            resolver (_TypeResolver): Registered annotation resolver.
            members (TypeMembers): Union members.

        Returns:
            TypeForm: Combined runtime union.

        Raises:
            TypeError: If no members are supplied.

        """
        if not members:
            msg: str = "At least one union member is required."
            raise TypeError(msg)
        result: TypeForm = resolver.normalize(member=members[0])
        for member in members[1:]:
            result = result | resolver.normalize(member=member)
        return result

    @staticmethod
    def union(
        *members: TypeAtom,
        namespace: TypeNamespace | None = None,
    ) -> TypeForm:
        """Combine runtime types and registered textual annotations.

        Args:
            *members (TypeAtom): Runtime or textual type expressions.
            namespace (TypeNamespace | None): Registered custom classes.

        Returns:
            TypeForm: Combined runtime union.

        Raises:
            TypeError: If an expression is unsupported.
            ValueError: If a referenced name is unknown.
            SyntaxError: If annotation syntax is invalid.

        """
        return TypeUnionDict._union(
            resolver=_TypeResolver(namespace=namespace),
            members=members,
        )


if __name__ == "__main__":

    @final
    class CustomClass:
        """Represent a custom registered annotation class."""

    @final
    class AnotherClass:
        """Represent a second registered annotation class."""

    namespace: DictType = {
        "CustomClass": CustomClass,
        "AnotherClass": AnotherClass,
        "models.CustomClass": CustomClass,
    }
    definitions: dict[str, TypeInput] = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "float": float,
        "bytes": bytes,
        "none": None,
        "string_name": "str",
        "integer_name": "int",
        "none_name": "None",
        "optional_string": "str | None",
        "optional_integer": "Optional[int]",
        "optional_custom": "Optional[CustomClass]",
        "union_operator": "str | int | None",
        "union_generic": "Union[str, int, None]",
        "union_tuple": (str, int, None),
        "union_strings": ("str", "int", "None"),
        "union_mixed": (str, "int", None),
        "union_list": ["str", "float", None],
        "duplicate_union": ("str", "str", "int"),
        "nested_union": "list[str | int | None]",
        "list_string": "list[str]",
        "list_integer": "list[int]",
        "list_custom": "list[CustomClass]",
        "list_optional": "list[CustomClass | None]",
        "nested_list": "list[list[int]]",
        "set_string": "set[str]",
        "frozen_set": "frozenset[int]",
        "dictionary": "dict[str, int]",
        "dictionary_custom": "dict[str, CustomClass]",
        "dictionary_optional": "dict[str, CustomClass | None]",
        "nested_dictionary": "dict[str, list[int | None]]",
        "tuple_fixed": "tuple[str, int, bool]",
        "tuple_variadic": "tuple[int, ...]",
        "tuple_nested": "tuple[list[str], dict[str, int]]",
        "mapping": "Mapping[str, int]",
        "mapping_custom": "Mapping[str, CustomClass]",
        "mapping_qualified": "collections.abc.Mapping[str, int]",
        "sequence": "Sequence[str]",
        "sequence_custom": "Sequence[CustomClass]",
        "sequence_qualified": "collections.abc.Sequence[int]",
        "iterable": "Iterable[str]",
        "iterable_qualified": "collections.abc.Iterable[int]",
        "callable_simple": "Callable[[str], bool]",
        "callable_multiple": "Callable[[str, int], bool]",
        "callable_empty": "Callable[[], None]",
        "callable_variadic": "Callable[..., str]",
        "callable_nested": "Callable[[list[int]], dict[str, bool]]",
        "custom_class": CustomClass,
        "custom_name": "CustomClass",
        "custom_optional": "CustomClass | None",
        "custom_union": "CustomClass | AnotherClass",
        "custom_qualified": "models.CustomClass",
        "custom_nested": "dict[str, list[CustomClass | None]]",
        "complex_union": (
            "dict[str, list[CustomClass | None]]",
            "tuple[int, ...]",
            None,
        ),
    }
    aprint(
        dedent(
            text=f"""\
        {"=" * 79}
        TYPEUNIONDICT - EXTENSIVE DEMONSTRATION
        {"=" * 79}

        1. INITIALIZING TYPEUNIONDICT
        {"-" * 79}""",
        ),
    )
    fields: TypeUnionDict = TypeUnionDict(
        values=definitions,
        namespace=namespace,
    )
    for name, annotation in fields.items():
        aprint(f"{name:<25} {annotation!r}")

    aprint(
        dedent(
            text=f"""\

        Total normalized fields: {len(fields)}

        2. STATIC UNION METHOD
        {"-" * 79}""",
        ),
    )
    union_examples: dict[str, TypeMembers] = {
        "runtime types": (str, int, float),
        "textual types": ("str", "int", "float"),
        "mixed types": (str, "int", None),
        "nullable type": ("str", None),
        "custom classes": ("CustomClass", "AnotherClass"),
        "nested generics": ("list[int]", "dict[str, int]"),
        "duplicate types": (str, str, int),
        "single type": (str,),
        "single textual type": ("str",),
        "single None": (None,),
        "nested optional": ("list[str | None]", None),
        "generic union": ("Mapping[str, int]", "Sequence[str]"),
    }
    for name, members in union_examples.items():
        result: TypeForm = TypeUnionDict.union(*members, namespace=namespace)
        aprint(f"{name:<25} {result!r}")

    equivalence_checks: dict[str, bool] = {
        "str | None": fields["optional_string"] == str | None,
        "Optional[int]": fields["optional_integer"] == int | None,
        "Union[str, int, None]": fields["union_generic"] == str | int | None,
        "list[str]": fields["list_string"] == list[str],
        "dict[str, int]": fields["dictionary"] == dict[str, int],
        "tuple[int, ...]": fields["tuple_variadic"] == tuple[int, ...],
        "Mapping[str, int]": fields["mapping"] == Mapping[str, int],
        "Sequence[str]": fields["sequence"] == Sequence[str],
        "Iterable[str]": fields["iterable"] == Iterable[str],
        "Callable[[str], bool]": (
            fields["callable_simple"] == Callable[[str], bool]
        ),
        "Callable[[str, int], bool]": (
            fields["callable_multiple"] == Callable[[str, int], bool]
        ),
        "Callable[[], None]": (
            fields["callable_empty"] == Callable[[], type(None)]
        ),
        "Callable[[list[int]], dict[str, bool]]": (
            fields["callable_nested"] == Callable[[list[int]], dict[str, bool]]
        ),
        "Callable[..., str]": (
            fields["callable_variadic"] == Callable[..., str]
        ),
        "custom class": fields["custom_name"] is CustomClass,
        "custom nullable": fields["custom_optional"] == CustomClass | None,
        "custom qualified": fields["custom_qualified"] is CustomClass,
        "duplicate normalization": fields["duplicate_union"] == str | int,
    }
    aprint(
        dedent(
            text=f"""\

        3. TYPE EQUIVALENCE CHECKS
        {"-" * 79}""",
        ),
    )
    for name, passed in equivalence_checks.items():
        aprint(f"{'PASS' if passed else 'FAIL':<6} {name}")

    equivalence_passed: int = sum(equivalence_checks.values())
    equivalence_total: int = len(equivalence_checks)
    aprint(
        dedent(
            text=f"""\

        Equivalence checks passed: {equivalence_passed}/{equivalence_total}

        4. RUNTIME TYPE INTROSPECTION
        {"-" * 79}""",
        ),
    )
    for name in (
        "string",
        "optional_string",
        "list_string",
        "dictionary",
        "mapping",
        "callable_simple",
        "custom_name",
        "complex_union",
    ):
        annotation: TypeForm = fields[name]
        aprint(f"{name:<25} {type(annotation).__name__:<20} {annotation!r}")

    invalid_annotations: dict[str, str] = {
        "unknown type": "UnknownClass",
        "unregistered module": "unknown.module.Type",
        "function call": "str()",
        "arithmetic": "int + str",
        "list expression": "[str, int]",
        "dictionary expression": "{'a': int}",
        "lambda expression": "lambda x: x",
        "comprehension": "[x for x in range(10)]",
        "attribute call": "CustomClass.__subclasses__()",
        "unsupported literal": "Literal['pending', 'done']",
        "unsupported annotated": "Annotated[str, 'metadata']",
        "unsupported required": "Required[str]",
        "unsupported not required": "NotRequired[str]",
        "custom generic": "CustomClass[int]",
        "invalid optional": "Optional[str, int]",
        "invalid callable": "Callable[str, int]",
        "invalid syntax": "list[",
    }
    aprint(
        dedent(
            text=f"""\

        5. EXPECTED REJECTIONS
        {"-" * 79}""",
        ),
    )
    rejected: int = 0
    for name, expression in invalid_annotations.items():
        try:
            TypeUnionDict.union(expression, namespace=namespace)
        except (TypeError, ValueError, SyntaxError) as error:
            rejected += 1
            aprint(f"REJECT {name:<25} {type(error).__name__}: {error}")
        else:
            aprint(f"ACCEPT {name:<25} Unexpected acceptance")

    aprint(
        dedent(
            text=f"""\

        Expected rejections: {rejected}/{len(invalid_annotations)}

        6. RESERVED NAMESPACE PROTECTION
        {"-" * 79}""",
        ),
    )
    reserved_rejections: int = 0
    reserved_names: tuple[str, ...] = ("str", "int", "Mapping", "Union")
    for reserved_name in reserved_names:
        try:
            TypeUnionDict(
                values={"value": reserved_name},
                namespace={reserved_name: CustomClass},
            )
        except ValueError as error:
            reserved_rejections += 1
            aprint(f"REJECT {reserved_name:<15} {error}")
        else:
            aprint(f"ACCEPT {reserved_name:<15} Unexpected acceptance")

    copied: TypeUnionDictType = fields.copy()
    overall_passed: bool = (
        all(equivalence_checks.values())
        and rejected == len(invalid_annotations)
        and reserved_rejections == len(reserved_names)
    )
    aprint(
        dedent(
            text=f"""\

        7. DICTIONARY OPERATIONS
        {"-" * 79}
        Dictionary length:          {len(fields)}
        Contains 'string':          {"string" in fields}
        Contains 'missing':         {"missing" in fields}
        Lookup 'string':            {fields["string"]!r}
        Lookup 'custom_name':       {fields["custom_name"]!r}
        Copy preserves values:      {copied == fields}
        Copy is a separate object:  {copied is not fields}

        8. SUMMARY
        {"-" * 79}
        Normalized fields:          {len(fields)}
        Equivalence checks:         {equivalence_passed}/{equivalence_total}
        Expected rejections:        {rejected}/{len(invalid_annotations)}
        Reserved-name rejections:   {reserved_rejections}/{len(reserved_names)}
        Overall demonstration:      {"PASS" if overall_passed else "FAIL"}
        {"=" * 79}""",
        ),
    )
