"""Structured, style-agnostic AST nodes for Python docstrings."""

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
    Expr,
    FunctionDef,
    Lambda,
    Module,
    Name,
    Raise,
    Return,
    Subscript,
    Tuple,
    Yield,
    YieldFrom,
    arg,
    expr,
    iter_child_nodes,
    parse,
    stmt,
    unparse,
    walk,
)
from dataclasses import dataclass
from inspect import cleandoc
from re import Match
from re import compile as compile_pattern
from types import MappingProxyType
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Final,
    Literal,
    final,
)

from astart.docstrings.prose import leading_fit, reflow_text
from astart.docstrings.type_layout import (
    canonical_type,
    compact_type,
    type_lines,
)
from astart.source.node_attributes import initialize_node
from astart.source.tokens import TokenAwareMixin
from astart.transforms.typeuniondict import TypeUnionDict, TypeUnionDictType

type ListStr = list[str]
type DictAST = dict[str, AST]

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from re import Pattern


type DocStyle = Literal[
    "google",
    "numpy",
    "rest",
    "epytext",
    "pep257",
    "mixed",
]
type DocKind = Literal[
    "parameters",
    "returns",
    "yields",
    "raises",
    "attributes",
    "examples",
    "notes",
    "warnings",
    "see_also",
    "deprecated",
    "unknown",
]
type DocumentedOwner = FunctionDef | AsyncFunctionDef | ClassDef


def function_body_nodes(*, owner: FunctionDef | AsyncFunctionDef) -> list[AST]:
    """Collect executable nodes belonging to one function's scope.

    Nested definitions own their bodies. Their defaults, decorators and
    class bases still execute in the enclosing function.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Function whose execution scope
            is inspected.

    Returns:
        list[AST]: Nodes in deterministic source traversal order.

    """
    found: list[AST] = []
    pending: list[AST] = list(reversed(owner.body))
    while pending:
        node: AST = pending.pop()
        children: list[AST]
        if isinstance(node, (FunctionDef, AsyncFunctionDef, Lambda)):
            children = [
                *node.args.defaults,
                *(x for x in node.args.kw_defaults if x is not None),
            ]
            if isinstance(node, (FunctionDef, AsyncFunctionDef)):
                children = [*node.decorator_list, *children]
        elif isinstance(node, ClassDef):
            children = [
                *node.decorator_list,
                *node.bases,
                *(keyword.value for keyword in node.keywords),
            ]
        else:
            found.append(node)
            children = list(iter_child_nodes(node=node))
        pending.extend(reversed(children))
    return found


def generator_result_annotation(
    *,
    owner: FunctionDef | AsyncFunctionDef,
    kind: DocKind,
    constructor_name: str | None = None,
) -> expr | None:
    """Select the yield or terminal-result component of a generator type.

    Args:
        owner (FunctionDef | AsyncFunctionDef): Annotated generator function.
        kind (DocKind): Yielded values or terminal returns.
        constructor_name (str | None): Semantically resolved constructor, when
            available.

    Returns:
        expr | None:
            The corresponding type argument, or ``None`` for an unknown alias.

    """
    annotation: expr | None = owner.returns
    if not isinstance(annotation, Subscript):
        return None
    base: expr = annotation.value
    name: str = constructor_name or (
        base.id
        if isinstance(base, Name)
        else base.attr
        if isinstance(base, Attribute)
        else ""
    )
    arguments: list[expr] = (
        list(annotation.slice.elts)
        if isinstance(annotation.slice, Tuple)
        else [annotation.slice]
    )
    if kind == "yields" and name in {
        "Generator",
        "Iterator",
        "Iterable",
        "AsyncGenerator",
        "AsyncIterator",
        "AsyncIterable",
    }:
        return arguments[0] if arguments else None
    if kind == "returns" and name == "Generator":
        return (
            arguments[-1]
            if len(arguments) == Constants.generator_return_arity
            else None
        )
    return None


@final
class Constants:
    """Group module-level constants.

    Attributes:
        google_header (Final[Pattern[str]]): Grouped module constant.
        directive (Final[Pattern[str]]): Grouped module constant.
        google_entry (Final[Pattern[str]]): Grouped module constant.
        google_parameter (Final[Pattern[str]]): Grouped module constant.
        numpy_entry (Final[Pattern[str]]): Grouped module constant.
        section_names (Final[Mapping[str, DocKind]]): Grouped module constant.
        field_names (Final[Mapping[str, DocKind]]): Grouped module constant.
        titles (Final[Mapping[DocKind, str]]): Grouped module constant.
        numpy_titles (Final[Mapping[DocKind, str]]): Grouped module constant.
        min_underline_length (Final[int]): Grouped module constant.
        generator_return_arity (Final[int]): Arguments needed for an explicit
            return type.
        line_length (Final[int]): TODO.
        named_label_overhead (Final[int]): TODO.
        bare_label_overhead (Final[int]): TODO.
        label_join_limit (Final[int]): TODO.
        min_type_candidate_length (Final[int]): Minimum pre-colon length for a
            wrapped type candidate.
        todo_placeholder (Final[str]): TODO.

    """

    google_header: Final[Pattern[str]] = compile_pattern(
        pattern=(
            "^(Args|Arguments|Parameters|Keyword Args|Keyword "
            "Arguments|Returns|Return|Yields|Raises|Exceptions|Attributes|"
            "Examples|Example|Notes|Note|Warnings|Warns|See "
            "Also|Deprecated|Methods|References|Todo|TODO):\\s*(.*)$"
        ),
    )
    directive: Final[Pattern[str]] = compile_pattern(
        pattern="^\\s*([:@])([\\w-]+)(?:\\s+([^:]+))?:\\s*(.*)$",
    )
    google_entry: Final[Pattern[str]] = compile_pattern(
        pattern="^([^:]+?):\\s*(.*)$",
    )
    google_parameter: Final[Pattern[str]] = compile_pattern(
        pattern=(r"^([*\w.]+)(?:\s*\(((?:[^()]|\([^()]*\))*)\))?$"),
    )
    numpy_entry: Final[Pattern[str]] = compile_pattern(
        pattern="^([^:]+?)\\s+:\\s*(.+)$",
    )
    section_names: Final[Mapping[str, DocKind]] = MappingProxyType(
        mapping={
            "args": "parameters",
            "arguments": "parameters",
            "parameters": "parameters",
            "keyword args": "parameters",
            "keyword arguments": "parameters",
            "other parameters": "parameters",
            "other args": "parameters",
            "return": "returns",
            "returns": "returns",
            "yield": "yields",
            "yields": "yields",
            "raises": "raises",
            "exceptions": "raises",
            "attributes": "attributes",
            "ivar": "attributes",
            "methods": "attributes",
            "example": "examples",
            "examples": "examples",
            "note": "notes",
            "notes": "notes",
            "warnings": "warnings",
            "warns": "warnings",
            "see also": "see_also",
            "deprecated": "deprecated",
        },
    )
    field_names: Final[Mapping[str, DocKind]] = MappingProxyType(
        mapping={
            "param": "parameters",
            "parameter": "parameters",
            "arg": "parameters",
            "keyword": "parameters",
            "key": "parameters",
            "type": "parameters",
            "return": "returns",
            "returns": "returns",
            "rtype": "returns",
            "yield": "yields",
            "yields": "yields",
            "ytype": "yields",
            "raise": "raises",
            "raises": "raises",
            "except": "raises",
            "ivar": "attributes",
            "cvar": "attributes",
            "var": "attributes",
            "vartype": "attributes",
            "note": "notes",
            "see": "see_also",
        },
    )
    titles: Final[Mapping[DocKind, str]] = MappingProxyType(
        mapping={
            "parameters": "Args",
            "returns": "Returns",
            "yields": "Yields",
            "raises": "Raises",
            "attributes": "Attributes",
            "examples": "Examples",
            "notes": "Notes",
            "warnings": "Warnings",
            "see_also": "See Also",
            "deprecated": "Deprecated",
            "unknown": "Other",
        },
    )
    numpy_titles: Final[Mapping[DocKind, str]] = MappingProxyType(
        mapping={**titles, "parameters": "Parameters"},
    )
    min_underline_length: Final[int] = 3
    line_length: Final[int] = 79
    generator_return_arity: Final[int] = 3
    named_label_overhead: Final[int] = 8
    bare_label_overhead: Final[int] = 5
    label_join_limit: Final[int] = 16
    min_type_candidate_length: Final[int] = 30
    todo_placeholder: Final[str] = "TODO."


@final
class DocSummary(AST):
    """An individually mutable, traversable PEP 257 summary line.

    Attributes:
        text (str): Summary prose without Python string literal quoting.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    text: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("text",)

    def __init__(self, *, text: str) -> None:
        """Create a summary node.

        Args:
            text (str): Summary sentence or line.

        """
        initialize_node(node=self, text=text)


@final
class DocDescription(AST):
    """Individually mutable prose between the summary and field sections.

    Attributes:
        text (str): Description paragraphs, preserving internal newlines.
        _field_types (ClassVar[TypeUnionDictType,TypeUnionDict]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    text: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("text",)

    def __init__(self, *, text: str) -> None:
        """Create a description node.

        Args:
            text (str): Explanatory prose.

        """
        initialize_node(node=self, text=text)


@final
class DocTodo(AST):
    """A ``TODO.`` placeholder marking documentation prose still owed.

    Entries and sections carry this node instead of treating the marker
    as ordinary text, so consumers can find pending documentation
    semantically through AST traversal rather than string matching.

    Attributes:
        text (str): Placeholder prose emitted in place of real content.
        _field_types (ClassVar[TypeUnionDictType]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    text: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "text": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = ("text",)

    def __init__(self, *, text: str = Constants.todo_placeholder) -> None:
        """Create a TODO placeholder node.

        Args:
            text (str): Placeholder prose to emit.

        """
        initialize_node(node=self, text=text)


@final
class DocstringLayout(AST):
    """PEP 257 structural properties, independent of the chosen field syntax.

    Attributes:
        is_one_line (bool): Whether the string value has a single physical
            line.
        has_blank_after_summary (bool): Whether the summary is followed by a
            blank line.
        summary_has_period (bool): Whether its summary ends in a full stop.
        is_trailing_blank (bool): Whether the string value ends with a blank
            line.
        preserve_original (bool): Retain source prose layout during ordinary
            edits; false
            when an explicit AST wrapping pass requests new layout.
        _field_types (ClassVar[TypeUnionDictType,TypeUnionDict]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    is_one_line: bool
    has_blank_after_summary: bool
    summary_has_period: bool
    is_trailing_blank: bool
    preserve_original: bool
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "is_one_line": bool,
            "has_blank_after_summary": bool,
            "summary_has_period": bool,
            "is_trailing_blank": bool,
            "preserve_original": bool,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "is_one_line",
        "has_blank_after_summary",
        "summary_has_period",
        "is_trailing_blank",
        "preserve_original",
    )

    def __init__(
        self,
        *,
        is_one_line: bool,
        has_blank_after_summary: bool,
        summary_has_period: bool,
        is_trailing_blank: bool,
        preserve_original: bool = True,
    ) -> None:
        """Capture the structural properties of the original string constant.

        Args:
            is_one_line (bool): Source string value contains no line breaks.
            has_blank_after_summary (bool): A blank separator follows the first
                line.
            summary_has_period (bool): Summary ends with a period.
            is_trailing_blank (bool): String ends with a blank line.
            preserve_original (bool): Whether source prose layout is
                authoritative.

        """
        initialize_node(
            node=self,
            is_one_line=is_one_line,
            has_blank_after_summary=has_blank_after_summary,
            summary_has_period=summary_has_period,
            is_trailing_blank=is_trailing_blank,
            preserve_original=preserve_original,
        )


@final
class DocEntry(AST):
    """One typed semantic doc field, optionally linked to Python code.

    Attributes:
        kind (DocKind): Normalized semantic category.
        name (str | None): Argument, exception, attribute, or return-value
            name.
        type_name (str | None): Documentation type expression, without
            evaluating it.
        description (str): Free-form prose, with paragraphs preserved.
        todo (DocTodo | None): Placeholder node when the description is still
            owed prose.
        raw (str): Original field text for audit or unsupported markup.
        target: Linked executable AST node, excluded from AST traversal.
        link_role: Why the AST node is linked, or None.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _field_types (ClassVar[TypeUnionDictType,TypeUnionDict]): TODO.

    """

    kind: DocKind
    name: str | None
    type_name: str | None
    description: str
    todo: DocTodo | None
    raw: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "kind": str,
            "name": (str, None),
            "type_name": (str, None),
            "description": str,
            "todo": (DocTodo, None),
            "raw": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "kind",
        "name",
        "type_name",
        "description",
        "todo",
        "raw",
    )

    def __init__(
        self,
        *,
        kind: DocKind,
        name: str | None = None,
        type_name: str | None = None,
        description: str = "",
        raw: str = "",
    ) -> None:
        """Create a documentation entry.

        Args:
            kind (DocKind): Standardized semantic category.
            name (str | None): Optional documented symbol.
            type_name (str | None): Optional source-language type expression.
            description (str): Documented prose.
            raw (str): Original entry text.

        """
        todo: DocTodo | None = (
            DocTodo()
            if description.strip() == Constants.todo_placeholder
            else None
        )
        initialize_node(
            node=self,
            kind=kind,
            name=name,
            type_name=type_name,
            description=description,
            todo=todo,
            raw=raw,
        )
        self.target: AST | None = None
        self.link_role: str | None = None

    def sync_todo(self) -> None:
        """Re-derive the placeholder node after description edits.

        Direct ``description`` assignment bypasses ``__init__``; call this
        so ``todo`` keeps marking exactly the ``TODO.`` placeholder.

        """
        self.todo = (
            DocTodo()
            if self.description.strip() == Constants.todo_placeholder
            else None
        )


@final
class DocSection(AST):
    """A logical documentation section containing structured entries.

    Attributes:
        kind (DocKind): Semantic category across all supported syntaxes.
        title (str): Original section title.
        description (str): Free-form section content without recognized
            entries.
        entries (list[DocEntry]): Parsed fields in this section.
        raw (str): Original section contents for unsupported markup.
        _field_types (ClassVar[TypeUnionDictType,TypeUnionDict]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.

    """

    kind: DocKind
    title: str
    description: str
    entries: list[DocEntry]
    raw: str
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "kind": str,
            "title": str,
            "description": str,
            "entries": list[DocEntry],
            "raw": str,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "kind",
        "title",
        "description",
        "entries",
        "raw",
    )

    def __init__(
        self,
        *,
        kind: DocKind,
        title: str,
        description: str = "",
        entries: list[DocEntry] | None = None,
        raw: str = "",
    ) -> None:
        """Initialize a normalized documentation section.

        Args:
            kind (DocKind): Standard semantic section.
            title (str): Display title or original directive name.
            description (str): Unstructured section prose.
            entries (list[DocEntry] | None): Structured subfields.
            raw (str): Original content.

        """
        initialize_node(
            node=self,
            kind=kind,
            title=title,
            description=description,
            entries=entries if entries is not None else [],
            raw=raw,
        )


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class DocstringSpec:
    """Normalized documentation content and links, without lexical position.

    Attributes:
        style (DocStyle): Detected source format.
        summary (str): First docstring sentence or line.
        description (str): Introductory paragraphs.
        sections (list[DocSection]): Typed documentation blocks.
        raw (str): Original string constant.
        layout (DocstringLayout): PEP 257 structure metadata.
        owner (DocumentedOwner | None): Python definition containing the
            docstring.
        expression (Expr | None): Original executable AST string expression.

    """

    style: DocStyle
    summary: str
    description: str
    sections: list[DocSection]
    raw: str
    layout: DocstringLayout
    owner: DocumentedOwner | None
    expression: Expr | None


@final
@dataclass(slots=True, kw_only=True)
class _LinkTables:
    """Executable nodes available for semantic doc linking.

    Attributes:
        owner (DocumentedOwner): Python definition containing the docstring.
        parameters (dict[str, arg]): Argument nodes indexed by name.
        attributes (DictAST): Assignments indexed by attribute name.
        raises (dict[str, Raise]): Raise statements indexed by exception name.
        returns (list[Return]): Return statements in walk order.
        yields (list[Yield | YieldFrom]): Yield and delegation statements in
            execution scope.

    """

    owner: DocumentedOwner
    parameters: dict[str, arg]
    attributes: DictAST
    raises: dict[str, Raise]
    returns: list[Return]
    yields: list[Yield | YieldFrom]


class DocstringNode(TokenAwareMixin):
    """Parsed Python docstring, addressable through ``ast.walk``.

    Attributes:
        style (DocStyle): Detected source syntax or requested output syntax.
        summary (str): PEP 257 summary line.
        description (str): Prose preceding structured fields.
        sections (list[DocSection]): Normalized semantic sections.
        raw (str): Original string constant value, including original
            whitespace.
        layout (DocstringLayout): PEP 257 structure metadata node.
        owner: Associated class or function, excluded from child traversal.
        expression: Real docstring expression, excluded from child traversal.
        lineno (int): Starting source line of the string constant.
        col_offset (int): Starting UTF-8 byte column.
        end_lineno (int): Last source line.
        end_col_offset (int): Ending UTF-8 byte column.
        description_node (DocDescription): Description node retained as
            DocDescription by this instance.
        summary_node (DocSummary): Summary node retained as DocSummary by this
            instance.
        _field_types (ClassVar[TypeUnionDictType,TypeUnionDict]): TODO.
        _fields (ClassVar[tuple[str, ...]]): TODO.
        _attributes (ClassVar[tuple[str, ...]]): TODO.

    """

    style: DocStyle
    summary: str
    description: str
    sections: list[DocSection]
    raw: str
    layout: DocstringLayout
    summary_node: DocSummary
    description_node: DocDescription
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    _field_types: ClassVar[TypeUnionDictType] = TypeUnionDict(
        values={
            "style": str,
            "summary": str,
            "description": str,
            "sections": list[DocSection],
            "raw": str,
            "layout": DocstringLayout,
            "summary_node": DocSummary,
            "description_node": DocDescription,
        },
    )
    _fields: ClassVar[tuple[str, ...]] = (
        "style",
        "summary",
        "description",
        "sections",
        "raw",
        "layout",
        "summary_node",
        "description_node",
    )
    _attributes: ClassVar[tuple[str, ...]] = (
        "lineno",
        "col_offset",
        "end_lineno",
        "end_col_offset",
    )

    def __init__(
        self,
        *,
        spec: DocstringSpec,
        lineno: int,
        col_offset: int,
        end_lineno: int,
        end_col_offset: int,
    ) -> None:
        """Store parsed documentation and its lexical location.

        Args:
            spec (DocstringSpec): Normalized documentation content and owner
                links.
            lineno (int): Start line.
            col_offset (int): Start byte column.
            end_lineno (int): End line.
            end_col_offset (int): End byte column.

        """
        initialize_node(
            node=self,
            style=spec.style,
            summary=spec.summary,
            description=spec.description,
            sections=spec.sections,
            raw=spec.raw,
            layout=spec.layout,
            summary_node=DocSummary(text=spec.summary),
            description_node=DocDescription(text=spec.description),
            lineno=lineno,
            col_offset=col_offset,
            end_lineno=end_lineno,
            end_col_offset=end_col_offset,
        )
        self._synchronized_summary: str = spec.summary
        self._synchronized_description: str = spec.description
        self.owner: DocumentedOwner | None = spec.owner
        self.expression: Expr | None = spec.expression

    def synchronize_text_parts(self) -> None:
        """Reconcile legacy string fields with their semantic AST children.

        Both legacy ``summary``/``description`` and the new child ``.text``
        fields may be edited. Conflicting simultaneous edits raise rather
        than silently discarding one modification.

        Raises:
            ValueError: If a field and its semantic node changed differently.

        """

        def resolve(
            *,
            name: str,
            field_value: str,
            node_value: str,
            last_value: str,
        ) -> str:
            """Choose one edit without discarding competing changes.

            Args:
                name (str): The semantic field name for error messages.
                field_value (str): Text currently in the legacy string field.
                node_value (str): Text currently in the AST child.
                last_value (str): Last synchronized text.

            Returns:
                str: Single reconciled string value.

            Raises:
                ValueError: If legacy and AST fields changed differently.

            """
            if (
                last_value not in (field_value, node_value)
                and field_value != node_value
            ):
                msg: str = f"Conflicting changes to docstring {name}."
                raise ValueError(msg)
            return field_value if field_value != last_value else node_value

        self.summary = resolve(
            name="summary",
            field_value=self.summary,
            node_value=self.summary_node.text,
            last_value=self._synchronized_summary,
        )
        self.description = resolve(
            name="description",
            field_value=self.description,
            node_value=self.description_node.text,
            last_value=self._synchronized_description,
        )
        self.summary_node.text = self.summary
        self.description_node.text = self.description
        self._synchronized_summary = self.summary
        self._synchronized_description = self.description

    def entries(self, *, kind: DocKind | None = None) -> list[DocEntry]:
        """Retrieve typed semantic fields, optionally restricted by category.

        Args:
            kind (DocKind | None): Field category, or None to include every
                category.

        Returns:
            list[DocEntry]: Ordered semantic fields.

        """
        return [
            entry
            for section in self.sections
            for entry in section.entries
            if kind is None or entry.kind == kind
        ]

    def render(self, *, style: DocStyle | None = None) -> str:
        """Serialize normalized documentation to a selected supported style.

        Args:
            style (DocStyle | None): Target format; defaults to the detected
                format.

        Returns:
            str: Document string value, without Python quotation marks.

        Raises:
            ValueError: If mixed syntax is requested as an output format.

        """
        self.synchronize_text_parts()
        target: DocStyle = style if style is not None else self.style
        if target == "mixed":
            msg: str = "Mixed syntax cannot be generated as one output style."
            raise ValueError(msg)
        if target != self.style and any(
            section.kind == "unknown" for section in self.sections
        ):
            msg = (
                "Unknown documentation syntax cannot be converted losslessly."
            )
            raise ValueError(msg)
        output: ListStr = [self.summary]
        if self.description:
            output.extend(("", self.description))
        for section in self.sections:
            if section.kind == "unknown":
                output.extend(
                    self._unknown_section_lines(
                        section=section,
                        target=target,
                    ),
                )
                continue
            content: ListStr = self._section_content(
                section=section,
                target=target,
            )
            if not content and (not section.raw):
                continue
            output.extend(
                self._section_lines(
                    section=section,
                    content=content,
                    target=target,
                ),
            )
        return "\n".join(output).rstrip()

    def synchronize_symbols(self, *, include_types: bool = False) -> None:
        """Synchronize documented identifiers with linked executable AST nodes.

        A function argument or class attribute rename can be propagated to
        its DocEntry without reparsing or guessing from source positions.
        This operation is explicit; parsing alone never changes
        documentation.

        Args:
            include_types (bool): Also update documentation types from AST
                annotations.

        """
        for entry in self.entries():
            if entry.link_role == "argument" and isinstance(entry.target, arg):
                entry.name = entry.target.arg
                if include_types and entry.target.annotation is not None:
                    entry.type_name = unparse(ast_obj=entry.target.annotation)
            elif (
                entry.link_role == "attribute"
                and isinstance(entry.target, AnnAssign)
                and isinstance(entry.target.target, Name)
            ):
                entry.name = entry.target.target.id
                if include_types:
                    entry.type_name = unparse(ast_obj=entry.target.annotation)
            elif (
                entry.link_role == "return_annotation"
                and isinstance(self.owner, (FunctionDef, AsyncFunctionDef))
                and (self.owner.returns is not None)
            ):
                entry.target = self.owner.returns
                if include_types:
                    entry.type_name = unparse(ast_obj=entry.target)
            elif entry.link_role in {
                "yield_annotation",
                "generator_return_annotation",
            }:
                self._synchronize_generator_entry(
                    entry=entry,
                    include_types=include_types,
                )

    def link(self) -> None:
        """Connect semantic fields to arguments, annotations and statements."""
        if self.owner is None:
            for entry in self.entries():
                entry.target = None
                entry.link_role = None
            return
        owner: DocumentedOwner = self.owner
        attributes: DictAST = (
            self._class_attributes(owner=owner)
            if isinstance(owner, ClassDef)
            else {}
        )
        raises, returns, yields = self._scan_owner(
            owner=owner,
            attributes=attributes,
        )
        tables: _LinkTables = _LinkTables(
            owner=owner,
            parameters=self._owner_parameters(owner=owner),
            attributes=attributes,
            raises=raises,
            returns=returns,
            yields=yields,
        )
        for entry in self.entries():
            self._link_entry(entry=entry, tables=tables)

    @staticmethod
    def _unknown_section_lines(
        *,
        section: DocSection,
        target: DocStyle,
    ) -> ListStr:
        """Serialize a section whose syntax is not understood.

        Args:
            section (DocSection): Unrecognized section.
            target (DocStyle): Output format.

        Returns:
            ListStr: Lines including a leading blank separator.

        """
        output: ListStr = [""]
        if target == "numpy":
            output.extend(
                (section.title, "-" * len(section.title), section.raw),
            )
        elif target in ("rest", "epytext"):
            output.extend(entry.raw for entry in section.entries)
            if section.description:
                output.append(section.description)
        else:
            output.extend((f"{section.title}:", section.raw))
        return output

    @staticmethod
    def _numpy_entry_lines(*, entry: DocEntry, kind: DocKind) -> ListStr:
        """Serialize one entry in NumPy style.

        Args:
            entry (DocEntry): Semantic field.
            kind (DocKind): Containing section kind.

        Returns:
            ListStr: Header line plus indented description lines.

        """
        key: str = entry.name or entry.type_name or "TODO"
        lines: ListStr = [
            (
                f"{entry.name} : {entry.type_name or 'TODO.'}"
                if entry.name and kind in ("parameters", "attributes")
                else key
            ),
        ]
        if entry.description:
            lines.extend(
                (f"    {line}") if line else ""
                for line in entry.description.split(
                    sep="\n",
                )
            )
        return lines

    @staticmethod
    def _directive_entry_lines(
        *,
        entry: DocEntry,
        kind: DocKind,
        target: DocStyle,
    ) -> ListStr:
        """Serialize one entry in reST or Epytext directive style.

        Args:
            entry (DocEntry): Semantic field.
            kind (DocKind): Containing section kind.
            target (DocStyle): Output format.

        Returns:
            ListStr: Directive lines, including a separate type directive.

        """
        sign: str = ":" if target == "rest" else "@"
        label_name: str = {
            "parameters": "param",
            "returns": "return",
            "yields": "yield",
            "raises": "raises",
            "attributes": "ivar",
        }.get(kind, kind)
        suffix: str = f" {entry.name}" if entry.name else ""
        description: ListStr = entry.description.splitlines() or [""]
        lines: ListStr = [
            (f"{sign}{label_name}{suffix}: {description[0]}").rstrip(),
            *(f"    {line}" if line else "" for line in description[1:]),
        ]
        if entry.type_name and kind in (
            "parameters",
            "returns",
            "attributes",
            "yields",
        ):
            type_label: str = {
                "parameters": "type",
                "returns": "rtype",
                "attributes": "type",
                "yields": "ytype",
            }[kind]
            type_suffix: str = (
                (f" {entry.name}")
                if entry.name and kind not in ("returns", "yields")
                else ""
            )
            lines.append(f"{sign}{type_label}{type_suffix}: {entry.type_name}")
        return lines

    @staticmethod
    def _section_lines(
        *,
        section: DocSection,
        content: ListStr,
        target: DocStyle,
    ) -> ListStr:
        """Emit a section header followed by its content lines.

        Args:
            section (DocSection): Normalized section.
            content (ListStr): Rendered entry lines.
            target (DocStyle): Output format.

        Returns:
            ListStr: Lines including a leading blank separator.

        """
        output: ListStr = [""]
        if target in ("google", "pep257"):
            output.append(f"{Constants.titles[section.kind]}:")
            output.extend(
                line if line.startswith("    ") else (f"    {line}")
                for line in "\n".join(content).split(
                    sep="\n",
                )
            )
        elif target == "numpy":
            title: str = Constants.numpy_titles[section.kind]
            output.extend((title, "-" * len(title), *content))
        elif target in ("rest", "epytext"):
            output.extend(content or [section.raw])
        else:
            output.extend((section.title, *content))
        return output

    @staticmethod
    def _owner_parameters(owner: DocumentedOwner) -> dict[str, arg]:
        """Index an owner's argument nodes by name.

        Args:
            owner (DocumentedOwner): Function or class containing the
                docstring.

        Returns:
            dict[str, arg]: Argument nodes keyed by parameter name; empty for
                classes.

        """
        if not isinstance(owner, (FunctionDef, AsyncFunctionDef)):
            return {}
        return {
            parameter.arg: parameter
            for parameter in (
                *owner.args.posonlyargs,
                *owner.args.args,
                *owner.args.kwonlyargs,
                *((owner.args.vararg,) if owner.args.vararg else ()),
                *((owner.args.kwarg,) if owner.args.kwarg else ()),
            )
        }

    @staticmethod
    def _class_attributes(*, owner: ClassDef) -> DictAST:
        """Index class-level annotated and assigned names.

        Args:
            owner (ClassDef): Class containing the docstring.

        Returns:
            DictAST: Assignment statements keyed by attribute name.

        """
        attributes: DictAST = {}
        for statement in owner.body:
            if isinstance(statement, AnnAssign) and isinstance(
                statement.target,
                Name,
            ):
                attributes[statement.target.id] = statement
            elif isinstance(statement, Assign):
                for target in statement.targets:
                    if isinstance(target, Name):
                        attributes[target.id] = statement
        return attributes

    @staticmethod
    def _scan_owner(
        *,
        owner: DocumentedOwner,
        attributes: DictAST,
    ) -> tuple[dict[str, Raise], list[Return], list[Yield | YieldFrom]]:
        """Walk an owner collecting raises, returns and self attributes.

        Args:
            owner (DocumentedOwner): Function or class containing the
                docstring.
            attributes (DictAST): Attribute table extended with ``self``
                assignments.

        Returns:
            tuple[dict[str, Raise], list[Return], list[Yield | YieldFrom]]:
                Raise statements by name, owned returns, and owned yields.

        """
        raises: dict[str, Raise] = {}
        returns: list[Return] = []
        yields: list[Yield | YieldFrom] = []
        nodes: list[AST] = (
            list(walk(node=owner))
            if isinstance(owner, ClassDef)
            else function_body_nodes(owner=owner)
        )
        for node in nodes:
            if isinstance(node, Raise) and node.exc is not None:
                expression: AST = (
                    node.exc.func if isinstance(node.exc, Call) else node.exc
                )
                if isinstance(expression, Name):
                    raises.setdefault(expression.id, node)
                elif isinstance(expression, Attribute):
                    raises.setdefault(expression.attr, node)
            elif isinstance(node, Return):
                returns.append(node)
            elif isinstance(node, (Yield, YieldFrom)):
                yields.append(node)
            elif isinstance(node, (Assign, AnnAssign)) and isinstance(
                owner,
                ClassDef,
            ):
                targets: list[expr] = (
                    node.targets if isinstance(node, Assign) else [node.target]
                )
                for target in targets:
                    if (
                        isinstance(target, Attribute)
                        and isinstance(target.value, Name)
                        and (target.value.id == "self")
                    ):
                        attributes.setdefault(target.attr, node)
        return raises, returns, yields

    @staticmethod
    def _link_entry(*, entry: DocEntry, tables: _LinkTables) -> None:
        """Attach one semantic field to its executable counterpart.

        Args:
            entry (DocEntry): Documentation field to link.
            tables (_LinkTables): Candidate executable nodes indexed by kind.

        """
        entry.target = None
        entry.link_role = None
        if entry.kind == "parameters" and entry.name is not None:
            entry.target = tables.parameters.get(entry.name.lstrip("*"))
            entry.link_role = "argument" if entry.target else None
        elif entry.kind in ("returns", "yields") and isinstance(
            tables.owner,
            (FunctionDef, AsyncFunctionDef),
        ):
            if tables.yields:
                component: expr | None = generator_result_annotation(
                    owner=tables.owner,
                    kind=entry.kind,
                )
                if component is not None:
                    entry.target = component
                    entry.link_role = (
                        "yield_annotation"
                        if entry.kind == "yields"
                        else "generator_return_annotation"
                    )
                elif entry.kind == "yields":
                    entry.target = tables.yields[0]
                    entry.link_role = "yield"
                else:
                    entry.target = (
                        tables.returns[0] if tables.returns else tables.owner
                    )
                    entry.link_role = "return"
                return
            entry.target = tables.owner.returns or (
                tables.returns[0] if tables.returns else tables.owner
            )
            entry.link_role = (
                "return_annotation" if tables.owner.returns else "return"
            )
        elif entry.kind == "raises" and entry.name is not None:
            entry.target = tables.raises.get(
                entry.name.rsplit(sep=".", maxsplit=1)[-1],
            )
            entry.link_role = "raise" if entry.target else None
        elif entry.kind == "attributes" and entry.name is not None:
            entry.target = tables.attributes.get(entry.name)
            entry.link_role = "attribute" if entry.target else None

    def _synchronize_generator_entry(
        self,
        *,
        entry: DocEntry,
        include_types: bool,
    ) -> None:
        """Refresh one generator component after an annotation mutation.

        Args:
            entry (DocEntry): Yield or terminal-return documentation field.
            include_types (bool): Whether to update its documented type too.

        """
        if not isinstance(self.owner, (FunctionDef, AsyncFunctionDef)):
            return
        component: expr | None = generator_result_annotation(
            owner=self.owner,
            kind=entry.kind,
        )
        if component is not None:
            entry.target = component
            if include_types:
                entry.type_name = unparse(ast_obj=component)

    def _section_content(
        self,
        *,
        section: DocSection,
        target: DocStyle,
    ) -> ListStr:
        """Collect rendered entry lines for one known section.

        Args:
            section (DocSection): Normalized section to serialize.
            target (DocStyle): Output format.

        Returns:
            ListStr: Content lines, without the section header.

        """
        content: ListStr = []
        if section.description:
            content.append(section.description)
        for entry in section.entries:
            content.extend(
                self._entry_lines(
                    entry=entry,
                    kind=section.kind,
                    target=target,
                ),
            )
        return content

    def _entry_lines(
        self,
        *,
        entry: DocEntry,
        kind: DocKind,
        target: DocStyle,
    ) -> ListStr:
        """Serialize one entry in the target style.

        Args:
            entry (DocEntry): Semantic field.
            kind (DocKind): Containing section kind.
            target (DocStyle): Output format.

        Returns:
            ListStr: Lines for this entry.

        """
        key: str = entry.name or entry.type_name or ""
        if target in ("google", "pep257"):
            label: str = (
                (f"{entry.name} ({entry.type_name})")
                if entry.name and entry.type_name
                else key
            )
            return self._google_entry_lines(label=label, entry=entry)
        if target == "numpy":
            return self._numpy_entry_lines(entry=entry, kind=kind)
        if target in ("rest", "epytext"):
            return self._directive_entry_lines(
                entry=entry,
                kind=kind,
                target=target,
            )
        return [": ".join(part for part in (key, entry.description) if part)]

    def _google_entry_lines(self, *, label: str, entry: DocEntry) -> ListStr:
        """Serialize one Google-style entry, wrapping over-budget lines.

        Args:
            label (str): ``name (type)`` or bare key prefixing the description.
            entry (DocEntry): Semantic field being serialized.

        Returns:
            ListStr: Lines for this entry, reflowed when they exceed the
                width budget.

        """
        budget: int = Constants.line_length - self.col_offset
        if label and len(f"    {label}:") > budget:
            label_lines: ListStr | None = wrapped_label_lines(
                label=label,
                budget=budget,
            )
            if label_lines is not None:
                return self._entry_tail_lines(
                    label_lines=label_lines,
                    entry=entry,
                    budget=budget,
                )
        description: ListStr = entry.description.splitlines() or [""]
        lines: ListStr = [
            (
                (f"    {label}: {description[0]}").rstrip()
                if label
                else (f"    {description[0]}").rstrip()
            ),
            *(f"        {line}" if line else "" for line in description[1:]),
        ]
        wrapped: ListStr = (
            reflow_text(
                text=entry.description,
                width=max(1, budget - 8),
                normalize_lists=True,
            ).splitlines()
            if entry.description.strip()
            and not all(len(line) <= budget for line in lines)
            else []
        )
        if not wrapped:
            return lines
        if not label:
            return [f"    {line}" if line else "" for line in wrapped]
        return self._fit_entry_lines(
            label=label,
            entry=entry,
            wrapped=wrapped,
            budget=budget,
        )

    def _fit_entry_lines(
        self,
        *,
        label: str,
        entry: DocEntry,
        wrapped: ListStr,
        budget: int,
    ) -> ListStr:
        """Fit reflowed description lines under an entry label.

        The canonical ``name (type):`` label keeps leading description
        words when they fit; compact type spacing and a bare ``name:``
        label are tried in turn so the entry never ends up malformed.

        Args:
            label (str): Canonical ``name (type)`` label.
            entry (DocEntry): Semantic field being serialized.
            wrapped (ListStr): Reflowed description lines.
            budget (int): Columns per emitted line, indent included.

        Returns:
            ListStr: Label line plus indented description continuations.

        """
        first: str = f"    {label}: {wrapped[0]}"
        if len(first) <= budget:
            return [
                first,
                *(f"        {line}" if line else "" for line in wrapped[1:]),
            ]
        prefix: str = f"    {label}: "
        head, rest = leading_fit(
            text=wrapped[0],
            room=budget - len(prefix),
        )
        if head:
            return self._entry_head_lines(
                prefix=prefix,
                head=head,
                rest=rest,
                wrapped=wrapped,
            )
        for fallback in self._label_fallbacks(label=label, entry=entry):
            fprefix: str = f"    {fallback}: "
            if len(fprefix) > budget:
                continue
            fhead, frest = leading_fit(
                text=wrapped[0],
                room=budget - len(fprefix),
            )
            if fhead:
                return self._entry_head_lines(
                    prefix=fprefix,
                    head=fhead,
                    rest=frest,
                    wrapped=wrapped,
                )
        return [
            f"    {label}:",
            *(f"        {line}" if line else "" for line in wrapped),
        ]

    @staticmethod
    def _entry_head_lines(
        *,
        prefix: str,
        head: str,
        rest: str,
        wrapped: ListStr,
    ) -> ListStr:
        """Emit a label line carrying leading description words.

        Args:
            prefix (str): ``name (type): `` label prefix.
            head (str): Leading description words fitting the label line.
            rest (str): Remaining words of the first wrapped line.
            wrapped (ListStr): Reflowed description lines.

        Returns:
            ListStr: Label line plus indented description continuations.

        """
        tail: ListStr = ([f"        {rest}"] if rest else []) + [
            f"        {line}" if line else "" for line in wrapped[1:]
        ]
        return [f"{prefix}{head}", *tail]

    @staticmethod
    def _label_fallbacks(*, label: str, entry: DocEntry) -> ListStr:
        """Label renderings to try when the canonical label admits no words.

        Compact type spacing keeps the annotation while shortening the
        label; dropping the type entirely is the last resort so the entry
        still carries description text on its label line.

        Args:
            label (str): Canonical ``name (type)`` label.
            entry (DocEntry): Semantic field being serialized.

        Returns:
            ListStr: Alternative labels in preference order.

        """
        fallbacks: ListStr = []
        if entry.name and entry.type_name:
            compact: str | None = compact_type(type_text=entry.type_name)
            if compact and compact != entry.type_name:
                candidate: str = f"{entry.name} ({compact})"
                if candidate != label:
                    fallbacks.append(candidate)
        if entry.name and label != entry.name:
            fallbacks.append(entry.name)
        return fallbacks

    @staticmethod
    def _entry_tail_lines(
        *,
        label_lines: ListStr,
        entry: DocEntry,
        budget: int,
    ) -> ListStr:
        """Emit description lines below a wrapped entry label.

        Args:
            label_lines (ListStr): Wrapped label lines ending in ``:``
                or ``):``.
            entry (DocEntry): Semantic field being serialized.
            budget (int): Columns per emitted line, indentation included.

        Returns:
            ListStr: Label lines followed by reflowed description lines.

        """
        wrapped: ListStr = (
            reflow_text(
                text=entry.description,
                width=max(1, budget - 8),
                normalize_lists=True,
            ).splitlines()
            if entry.description.strip()
            else []
        )
        if wrapped:
            joined: str = f"{label_lines[-1]} {wrapped[0]}"
            if len(joined) <= budget:
                label_lines = [*label_lines[:-1], joined]
                wrapped = wrapped[1:]
        return [
            *label_lines,
            *(f"        {line}" if line else "" for line in wrapped),
        ]


@final
class ModuleDocstringNode(DocstringNode):
    """A semantically distinguished leading module-level documentation node."""


def wrapped_label_lines(*, label: str, budget: int) -> ListStr | None:
    """Lay out an over-long entry label on type-expression boundaries.

    Args:
        label (str): ``name (type)`` or bare type text.
        budget (int): Columns per emitted line, indentation included.

    Returns:
        ListStr | None: Label lines ending in ``:`` or ``):``, or ``None``
            when the type cannot be laid out inside the budget.

    """
    name: str = ""
    type_text: str = label
    if label.endswith(")") and " (" in label:
        head: str
        head, _, rest = label.rpartition(" (")
        candidate: str = head.strip()
        if candidate and all(
            character.isalnum() or character in "._* "
            for character in candidate
        ):
            name = candidate
            type_text = rest[:-1].strip()
    closer: str = ":"
    pieces: ListStr | None = type_lines(
        type_name=type_text,
        first_width=(
            budget - len(name) - Constants.named_label_overhead
            if name
            else budget - Constants.bare_label_overhead
        ),
        budget=budget - len(closer),
        parenthesize_union=not name,
    )
    if pieces is None or len(pieces) == 1:
        return None
    body: ListStr = (
        [f"    {name}: {pieces[0]}", *pieces[1:]]
        if name
        else [f"    {pieces[0]}", *pieces[1:]]
    )
    body[-1] = f"{body[-1]}{closer}"
    if any(len(line) > budget for line in body):
        return None
    return body


def _find_marker(
    lines: ListStr,
    index: int,
) -> tuple[DocStyle, str, str] | None:
    """Recognize a structured field or section at a dedented line.

    Args:
        lines (ListStr): Dedented document lines.
        index (int): Current zero-based line index.

    Returns:
        tuple[DocStyle, str, str] | None:
            Format, normalized section title, and heading payload, if found.

    """
    line: str = lines[index]
    if line != line.lstrip() or not line.strip():
        return None
    if (match := Constants.directive.match(string=line)) is not None:
        if match.group(1) == ":":
            return ("rest", match.group(2), "")
        return ("epytext", match.group(2), "")
    if (match := Constants.google_header.match(string=line)) is not None:
        return ("google", match.group(1), match.group(2))
    if (
        index + 1 < len(lines)
        and (title := line.strip())
        and (underline := lines[index + 1].strip())
        and (len(underline) >= Constants.min_underline_length)
        and (set(underline) == {"-"})
        and title[0].isalpha()
    ):
        return ("numpy", title, "")
    return None


def _absorb_blank_line(
    *,
    intro: ListStr,
    entries: list[DocEntry],
    current: DocEntry | None,
) -> None:
    """Record a blank line as a description gap or intro spacing.

    Args:
        intro (ListStr): Free-form lines preceding the first entry.
        entries (list[DocEntry]): Structured entries parsed so far.
        current (DocEntry | None): Entry receiving continuation text, if any.

    """
    if current is not None and current.description:
        current.description += "\n"
    elif not entries:
        intro.append("")


def _type_like(*, label: str) -> bool:
    """Tell whether a Returns/Yields label is a type expression, not prose.

    Prose containing a colon — timestamps, `` ``src:.`` `` paths,
    ``key: value`` examples — must stay description text; treating it as a
    type lets a later type insertion overwrite the prefix and lose the
    prose.

    Args:
        label (str): Text before the first colon of a style entry line.

    Returns:
        bool: Whether the label parses as a Python expression without calls.

    """
    try:
        tree: AST = parse(source=label, mode="eval")
    except (SyntaxError, ValueError):
        return False
    return not any(
        isinstance(node, (Call, Lambda)) for node in walk(node=tree)
    )


def _matched_entry(
    *,
    match: Match[str],
    kind: DocKind,
    style: DocStyle,
    line: str,
) -> DocEntry:
    """Build an entry from a style-specific item-header match.

    Args:
        match (Match[str]): Regex hit on a dedented section line.
        kind (DocKind): Semantic category.
        style (DocStyle): Source style used by this section.
        line (str): Raw source line for the entry.

    Returns:
        DocEntry: A normalized structured entry.

    """
    label: str = match.group(1).strip()
    payload: str = match.group(2).strip()
    prose: str | None = None
    if style == "google":
        detail: Match[str] | None = Constants.google_parameter.fullmatch(
            string=label,
        )
        name: str | None = detail.group(1) if detail else label
        type_name: str | None = detail.group(2) if detail else None
        if kind in ("returns", "yields") and (not type_name):
            if _type_like(label=label):
                type_name, name = (label, None)
            else:
                name = None
                prose = line.strip()
    else:
        name = label
        type_name = payload
        payload = ""
    return DocEntry(
        kind=kind,
        name=name,
        type_name=type_name,
        description=prose if prose is not None else payload,
        raw=line,
    )


def _expand_numpy_names(
    *,
    entries: list[DocEntry],
    style: DocStyle,
    kind: DocKind,
) -> list[DocEntry]:
    """Split comma-joined NumPy parameter names into separate entries.

    Args:
        entries (list[DocEntry]): Parsed section entries.
        style (DocStyle): Source style used by this section.
        kind (DocKind): Semantic category.

    Returns:
        list[DocEntry]: Expanded entries, or the original list when
            inapplicable.

    """
    if not (style == "numpy" and kind in ("parameters", "attributes")):
        return entries
    expanded: list[DocEntry] = []
    for entry in entries:
        names: ListStr = (
            [name.strip() for name in entry.name.split(sep=",")]
            if entry.name and "," in entry.name
            else []
        )
        if len(names) > 1:
            expanded.extend(
                DocEntry(
                    kind=entry.kind,
                    name=name,
                    type_name=entry.type_name,
                    description=entry.description,
                    raw=entry.raw,
                )
                for name in names
                if name
            )
        else:
            expanded.append(entry)
    return expanded


def _bracket_balance(*, text: str) -> int:
    """Net unclosed bracket count of ``text``.

    Args:
        text (str): Candidate label fragment.

    Returns:
        int: Open brackets minus close brackets.

    """
    depth: int = 0
    for character in text:
        if character in "([{":
            depth += 1
        elif character in ")]}":
            depth -= 1
    return depth


def _accumulate_label(
    *,
    lines: ListStr,
    start: int,
) -> tuple[str | None, int]:
    """Join wrapped label fragments until brackets balance.

    Args:
        lines (ListStr): Section lines being parsed.
        start (int): Index of the first fragment.

    Returns:
        tuple[str | None, int]: Joined text and the index after the last
            fragment,
            or ``(None, start + 1)`` when depth never closes.

    """
    parts: ListStr = []
    depth: int = 0
    index: int = start
    limit: int = min(start + Constants.label_join_limit, len(lines))
    while index < limit:
        stripped: str = lines[index].strip()
        if not stripped:
            break
        parts.append(stripped)
        depth += _bracket_balance(text=stripped)
        index += 1
        if depth <= 0:
            return " ".join(parts), index
    return None, start + 1


def _canonical_label(*, label: str) -> str | None:
    """Canonicalize a wrapped label's type through a real parse.

    Args:
        label (str): ``name (type)`` or bare type text.

    Returns:
        str | None: Canonical label, or ``None`` for non-type text.

    """
    head: str = label.strip()
    if head.endswith(")") and " (" in head:
        name_part: str
        name_part, _, rest = head.rpartition(" (")
        candidate: str = name_part.strip()
        if candidate and all(
            character.isalnum() or character in "._* "
            for character in candidate
        ):
            canonical: str | None = canonical_type(type_text=rest[:-1])
            if canonical is not None:
                return f"{candidate} ({canonical})"
    return canonical_type(type_text=head)


def _logical_entry_line(*, text: str) -> str | None:
    """Rebuild one canonical entry line from joined fragments.

    Args:
        text (str): Space-joined label fragments.

    Returns:
        str | None: ``label: payload`` with a canonical label, or
            ``None`` when the text is not a recognizable entry.

    """
    match: Match[str] | None = Constants.google_entry.match(string=text)
    if match is None:
        return None
    canonical: str | None = _canonical_label(label=match.group(1))
    if canonical is None:
        return None
    payload: str = match.group(2).strip()
    return f"{canonical}: {payload}" if payload else f"{canonical}:"


def _join_wrapped_labels(*, lines: ListStr) -> ListStr:
    """Rejoin entry labels wrapped on type-expression boundaries.

    Only entry-level lines that fail the entry match and leave brackets
    unbalanced are candidates; following lines merge only while bracket
    depth stays positive, and the joined text is kept only when it
    parses as an entry whose label canonicalizes — every other line
    passes through untouched.

    Args:
        lines (ListStr): Raw contents of one section.

    Returns:
        ListStr: Lines with wrapped labels restored to one line.

    """
    base: int = 0
    for line in lines:
        if line.strip():
            base = len(line) - len(line.lstrip())
            break
    out: ListStr = []
    index: int = 0
    while index < len(lines):
        line: str = lines[index]
        stripped: str = line.strip()
        indent: int = len(line) - len(line.lstrip())
        if (
            stripped
            and indent <= base
            and Constants.google_entry.match(string=stripped) is None
            and _bracket_balance(text=stripped) > 0
        ):
            joined: str | None
            stop: int
            joined, stop = _accumulate_label(lines=lines, start=index)
            if joined is not None:
                logical: str | None = _logical_entry_line(text=joined)
                if logical is not None:
                    out.append(f"{' ' * indent}{logical}")
                    index = stop
                    continue
        out.append(line)
        index += 1
    return out


def _parse_indented_entries(
    *,
    kind: DocKind,
    lines: ListStr,
    style: DocStyle,
) -> tuple[list[DocEntry], str]:
    """Normalize Google or NumPy item blocks and continuation lines.

    Args:
        kind (DocKind): Semantic category.
        lines (ListStr): Raw contents of one section.
        style (DocStyle): Source style used by this section.

    Returns:
        tuple[list[DocEntry], str]: Structured entries and remaining free-form
            description.

    """
    if kind not in ("parameters", "returns", "yields", "raises", "attributes"):
        return (
            [],
            "\n".join(lines).strip(),
        )

    if style == "google":
        lines = _join_wrapped_labels(lines=lines)

    entries: list[DocEntry] = []
    intro: ListStr = []
    current: DocEntry | None = None
    base_indent: int | None = None

    for line in lines:
        if not line.strip():
            _absorb_blank_line(intro=intro, entries=entries, current=current)
            continue

        stripped: str = line.strip()
        indent: int = len(line) - len(line.lstrip())
        base_indent = indent if base_indent is None else base_indent
        is_root: bool = indent <= base_indent

        match: Match[str] | None = (
            (
                Constants.google_entry.match(string=stripped)
                if style == "google"
                else Constants.numpy_entry.match(string=stripped)
            )
            if is_root
            else None
        )

        numpy_label: bool = (
            is_root
            and style == "numpy"
            and kind in ("returns", "yields", "raises")
            and (kind == "raises" or _type_like(label=stripped))
        )
        google_description: bool = (
            is_root
            and style == "google"
            and kind in ("returns", "yields")
            and current is None
        )

        if match is not None or numpy_label or google_description:
            current = (
                _matched_entry(
                    match=match,
                    kind=kind,
                    style=style,
                    line=line,
                )
                if match is not None
                else DocEntry(
                    kind=kind,
                    name=(
                        stripped if numpy_label and kind == "raises" else None
                    ),
                    type_name=(
                        stripped if numpy_label and kind != "raises" else None
                    ),
                    description=stripped if google_description else "",
                    raw=line,
                )
            )
            entries.append(current)
        elif current is not None:
            current.description = "\n".join(
                part
                for part in (
                    current.description.rstrip("\n"),
                    stripped,
                )
                if part
            )
            current.sync_todo()
        else:
            intro.append(stripped)

    if style == "google" and kind in ("parameters", "attributes"):
        for entry in entries:
            if (
                entry.name is not None
                and entry.type_name is None
                and (
                    split := _inline_type_split(
                        description=entry.description,
                    )
                )
                is not None
            ):
                entry.type_name, entry.description = split
                entry.sync_todo()

    return (
        _expand_numpy_names(entries=entries, style=style, kind=kind),
        "\n".join(intro).strip(),
    )


def _inline_type_split(*, description: str) -> tuple[str, str] | None:
    """Split a wrapped ``name: TYPE`` description into type and prose.

    Multiline type labels serialize without parentheses, so the type
    text lands inside the entry description followed by ``:`` and the
    real description. Recover the type when the leading fragment
    parses as a type expression containing type structure.

    Args:
        description (str): Entry description possibly opening with a
            wrapped type expression.

    Returns:
        tuple[str, str] | None:
            ``(canonical_type, remaining_description)`` or ``None``
            when no type prefix is present.

    """
    depth: int = 0
    quote: str | None = None
    index: int = 0

    while index < len(description):
        char: str = description[index]

        if quote is not None:
            quote = None if char == quote else quote
            index += int(char == "\\")
        elif char in "'\"":
            quote = char
        else:
            depth += int(char in "([{") - int(char in ")]}")

            if (
                char == ":"
                and depth == 0
                and description[index + 1 : index + 2]
                in (
                    "",
                    " ",
                    "\t",
                    "\n",
                )
            ):
                candidate: str = " ".join(description[:index].split())
                canonical: str | None = (
                    canonical_type(type_text=candidate)
                    if (
                        len(candidate) > Constants.min_type_candidate_length
                        and any(mark in candidate for mark in "|[](),.")
                    )
                    else None
                )
                return (
                    (canonical, description[index + 1 :].lstrip())
                    if canonical is not None
                    else None
                )

        index += 1

    return None


def _merge_field(
    *,
    sections: list[DocSection],
    line: str,
    continuation: ListStr,
) -> None:
    """Accumulate a reST/Epytext field with independently supplied types.

    Args:
        sections (list[DocSection]): Existing normalized sections to update.
        line (str): Directive's first line.
        continuation (ListStr): Indented continuation lines.

    """
    match: Match[str] | None = Constants.directive.match(string=line)
    if match is None:
        return
    directive: str = match.group(2).lower()
    kind: DocKind = Constants.field_names.get(directive, "unknown")
    section: DocSection | None = next(
        (candidate for candidate in sections if candidate.kind == kind),
        None,
    )
    if section is None:
        section = DocSection(kind=kind, title=directive)
        sections.append(section)
    name: str | None = match.group(3).strip() if match.group(3) else None
    annotation: str | None = None
    if directive in ("param", "parameter", "arg", "keyword", "key") and (
        name is not None and " " in name
    ):
        annotation, name = name.rsplit(sep=" ", maxsplit=1)
    description: str = "\n".join(
        [match.group(4).strip(), *(part.strip() for part in continuation)],
    ).strip()
    is_type: bool = directive in ("type", "rtype", "ytype", "vartype")
    current: DocEntry | None = (
        next((entry for entry in section.entries if entry.name == name), None)
        if is_type
        else None
    )
    if current is not None:
        current.type_name = description
    elif is_type:
        section.entries.append(
            DocEntry(kind=kind, name=name, type_name=description, raw=line),
        )
    else:
        section.entries.append(
            DocEntry(
                kind=kind,
                name=name,
                type_name=annotation,
                description=description,
                raw="\n".join([line, *continuation]),
            ),
        )


def parse_docstring(
    *,
    source: str,
    owner: DocumentedOwner | None = None,
    expression: Expr | None = None,
) -> DocstringNode:
    """Parse all five major formats into one inspectable AST schema.

    Args:
        source (str): Evaluated Python docstring constant.
        owner (DocumentedOwner | None): Containing function or class, if
            available.
        expression (Expr | None): Executable statement containing the string
            constant.

    Returns:
        DocstringNode:
            An AST docstring node with semantic entries and source links.

    """
    cleaned: str = cleandoc(doc=source)
    lines: ListStr = cleaned.split(
        sep="\n",
    )
    while lines and (not lines[0].strip()):
        lines.pop(0)
    summary: str = lines.pop(0).strip() if lines else ""
    while lines and (not lines[0].strip()):
        lines.pop(0)
    introduction: ListStr = []
    sections: list[DocSection] = []
    found: set[DocStyle] = set()
    index: int = 0
    while index < len(lines):
        marker: tuple[DocStyle, str, str] | None = _find_marker(
            lines=lines,
            index=index,
        )
        if marker is None:
            introduction.append(lines[index])
            index += 1
            continue
        format_style: DocStyle
        title: str
        payload: str
        format_style, title, payload = marker
        found.add(format_style)
        if format_style in ("rest", "epytext"):
            following: ListStr = []
            index += 1
            while index < len(lines) and (
                not lines[index].strip()
                or lines[index] != lines[index].lstrip()
            ):
                following.append(lines[index])
                index += 1
            _merge_field(
                sections=sections,
                line=lines[index - len(following) - 1],
                continuation=following,
            )
            continue
        index += 2 if format_style == "numpy" else 1
        chunk: ListStr = [payload] if payload else []
        while (
            index < len(lines)
            and _find_marker(lines=lines, index=index) is None
        ):
            chunk.append(lines[index])
            index += 1
        kind: DocKind = Constants.section_names.get(title.lower(), "unknown")
        entries: list[DocEntry]
        description: str
        entries, description = _parse_indented_entries(
            kind=kind,
            lines=chunk,
            style=format_style,
        )
        sections.append(
            DocSection(
                kind=kind,
                title=title,
                description=description,
                entries=entries,
                raw="\n".join(chunk).strip(),
            ),
        )
    style: DocStyle = (
        next(iter(found))
        if len(found) == 1
        else "mixed"
        if found
        else "pep257"
    )
    node_type: type[DocstringNode] = (
        ModuleDocstringNode if owner is None else DocstringNode
    )
    source_lines: ListStr = source.split(
        sep="\n",
    )
    node: DocstringNode = node_type(
        spec=DocstringSpec(
            style=style,
            summary=summary,
            description="\n".join(introduction).strip(),
            sections=sections,
            raw=source,
            layout=DocstringLayout(
                is_one_line="\n" not in source and "\r" not in source,
                has_blank_after_summary=len(source.splitlines()) > 1
                and (not source.splitlines()[1].strip()),
                summary_has_period=summary.endswith("."),
                is_trailing_blank=len(source_lines) > 1
                and not source_lines[-1].strip()
                and not source_lines[-2].strip(),
            ),
            owner=owner,
            expression=expression,
        ),
        lineno=getattr(expression.value, "lineno", 1)
        if expression is not None
        else 1,
        col_offset=getattr(expression.value, "col_offset", 0)
        if expression is not None
        else 0,
        end_lineno=getattr(expression.value, "end_lineno", 1)
        if expression is not None
        else 1,
        end_col_offset=getattr(expression.value, "end_col_offset", 0)
        if expression is not None
        else 0,
    )
    node.link()
    return node


def collect_docstrings(*, body: Sequence[AST]) -> list[DocstringNode]:
    """Extract definition and module docstrings without double-counting.

    Args:
        body (Sequence[AST]): Module statement list, including nested
            definitions.

    Returns:
        list[DocstringNode]: Lexically ordered normalized docstring AST nodes.

    """
    results: list[DocstringNode] = []
    module: Module = Module(
        body=[item for item in body if isinstance(item, stmt)],
        type_ignores=[],
    )
    owners: list[DocumentedOwner | None] = [None]
    owners.extend(
        node
        for node in walk(node=module)
        if isinstance(node, (ClassDef, FunctionDef, AsyncFunctionDef))
    )
    for owner in owners:
        statements: list[stmt] = module.body if owner is None else owner.body
        if (
            statements
            and isinstance(statements[0], Expr)
            and isinstance(statements[0].value, Constant)
            and isinstance(statements[0].value.value, str)
        ):
            results.append(
                parse_docstring(
                    source=statements[0].value.value,
                    owner=owner,
                    expression=statements[0],
                ),
            )
    return sorted(results, key=lambda doc: (doc.lineno, doc.col_offset))
