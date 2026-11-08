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
    Module,
    Name,
    Raise,
    Return,
    arg,
    expr,
    stmt,
    unparse,
    walk,
)
from dataclasses import dataclass
from inspect import cleandoc
from re import Match
from re import compile as compile_pattern
from types import GenericAlias, MappingProxyType, UnionType
from typing import TYPE_CHECKING, ClassVar, Final, Literal, final

from astart.node_attributes import initialize_node
from astart.tokens import TokenAwareMixin

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


@final
class Constants:
    """Group module-level constants.

    Attributes:
        google_header: Grouped module constant.
        directive: Grouped module constant.
        google_entry: Grouped module constant.
        google_parameter: Grouped module constant.
        numpy_entry: Grouped module constant.
        section_names: Grouped module constant.
        field_names: Grouped module constant.
        titles: Grouped module constant.
        numpy_titles: Grouped module constant.
        min_underline_length: Grouped module constant.

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
        pattern="^([*\\w.]+)(?:\\s*\\(([^)]*)\\))?$",
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


@final
class DocSummary(AST):
    """An individually mutable, traversable PEP 257 summary line.

    Attributes:
        text: Summary prose without Python string literal quoting.

    """

    text: str
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "text": str,
    }
    _fields: ClassVar[tuple[str, ...]] = ("text",)

    def __init__(self, *, text: str) -> None:
        """Create a summary node.

        Args:
            text: Summary sentence or line.

        """
        initialize_node(node=self, text=text)


@final
class DocDescription(AST):
    """Individually mutable prose between the summary and field sections.

    Attributes:
        text: Description paragraphs, preserving internal newlines.

    """

    text: str
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "text": str,
    }
    _fields: ClassVar[tuple[str, ...]] = ("text",)

    def __init__(self, *, text: str) -> None:
        """Create a description node.

        Args:
            text: Explanatory prose.

        """
        initialize_node(node=self, text=text)


@final
class DocstringLayout(AST):
    """PEP 257 structural properties, independent of the chosen field syntax.

    Attributes:
        is_one_line: Whether the string value has a single physical line.
        has_blank_after_summary: Whether the summary is followed by a blank
            line.
        summary_has_period: Whether its summary ends in a full stop.
        is_trailing_blank: Whether the string value ends with a blank line.

    """

    is_one_line: bool
    has_blank_after_summary: bool
    summary_has_period: bool
    is_trailing_blank: bool
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "is_one_line": bool,
        "has_blank_after_summary": bool,
        "summary_has_period": bool,
        "is_trailing_blank": bool,
    }
    _fields: ClassVar[tuple[str, ...]] = (
        "is_one_line",
        "has_blank_after_summary",
        "summary_has_period",
        "is_trailing_blank",
    )

    def __init__(
        self,
        *,
        is_one_line: bool,
        has_blank_after_summary: bool,
        summary_has_period: bool,
        is_trailing_blank: bool,
    ) -> None:
        """Capture the structural properties of the original string constant.

        Args:
            is_one_line: Source string value contains no line breaks.
            has_blank_after_summary: A blank separator follows the first line.
            summary_has_period: Summary ends with a period.
            is_trailing_blank: String ends with a blank line.

        """
        initialize_node(
            node=self,
            is_one_line=is_one_line,
            has_blank_after_summary=has_blank_after_summary,
            summary_has_period=summary_has_period,
            is_trailing_blank=is_trailing_blank,
        )


@final
class DocEntry(AST):
    """One typed semantic doc field, optionally linked to Python code.

    Attributes:
        kind: Normalized semantic category.
        name: Argument, exception, attribute, or return-value name.
        type_name: Documentation type expression, without evaluating it.
        description: Free-form prose, with paragraphs preserved.
        raw: Original field text for audit or unsupported markup.
        target: Linked executable AST node, excluded from AST traversal.
        link_role: Why the AST node is linked, or None.

    """

    kind: DocKind
    name: str | None
    type_name: str | None
    description: str
    raw: str
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "kind": str,
        "name": str | None,
        "type_name": str | None,
        "description": str,
        "raw": str,
    }
    _fields: ClassVar[tuple[str, ...]] = (
        "kind",
        "name",
        "type_name",
        "description",
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
            kind: Standardized semantic category.
            name: Optional documented symbol.
            type_name: Optional source-language type expression.
            description: Documented prose.
            raw: Original entry text.

        """
        initialize_node(
            node=self,
            kind=kind,
            name=name,
            type_name=type_name,
            description=description,
            raw=raw,
        )
        self.target: AST | None = None
        self.link_role: str | None = None


@final
class DocSection(AST):
    """A logical documentation section containing structured entries.

    Attributes:
        kind: Semantic category across all supported syntaxes.
        title: Original section title.
        description: Free-form section content without recognized entries.
        entries: Parsed fields in this section.
        raw: Original section contents for unsupported markup.

    """

    kind: DocKind
    title: str
    description: str
    entries: list[DocEntry]
    raw: str
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "kind": str,
        "title": str,
        "description": str,
        "entries": list[DocEntry],
        "raw": str,
    }
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
            kind: Standard semantic section.
            title: Display title or original directive name.
            description: Unstructured section prose.
            entries: Structured subfields.
            raw: Original content.

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
        style: Detected source format.
        summary: First docstring sentence or line.
        description: Introductory paragraphs.
        sections: Typed documentation blocks.
        raw: Original string constant.
        layout: PEP 257 structure metadata.
        owner: Python definition containing the docstring.
        expression: Original executable AST string expression.

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
        owner: Python definition containing the docstring.
        parameters: Argument nodes indexed by name.
        attributes: Assignments indexed by attribute name.
        raises: Raise statements indexed by exception name.
        returns: Return statements in walk order.

    """

    owner: DocumentedOwner
    parameters: dict[str, arg]
    attributes: dict[str, AST]
    raises: dict[str, Raise]
    returns: list[Return]


class DocstringNode(TokenAwareMixin):
    """Parsed Python docstring, addressable through ``ast.walk``.

    Attributes:
        style: Detected source syntax or requested output syntax.
        summary: PEP 257 summary line.
        description: Prose preceding structured fields.
        sections: Normalized semantic sections.
        raw: Original string constant value, including original whitespace.
        layout: PEP 257 structure metadata node.
        owner: Associated class or function, excluded from child traversal.
        expression: Real docstring expression, excluded from child traversal.
        lineno: Starting source line of the string constant.
        col_offset: Starting UTF-8 byte column.
        end_lineno: Last source line.
        end_col_offset: Ending UTF-8 byte column.


        description_node: Description node retained as DocDescription by this
            instance.
        summary_node: Summary node retained as DocSummary by this instance.

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
    _field_types: ClassVar[dict[str, type | GenericAlias | UnionType]] = {
        "style": str,
        "summary": str,
        "description": str,
        "sections": list[DocSection],
        "raw": str,
        "layout": DocstringLayout,
        "summary_node": DocSummary,
        "description_node": DocDescription,
    }
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
            spec: Normalized documentation content and owner links.
            lineno: Start line.
            col_offset: Start byte column.
            end_lineno: End line.
            end_col_offset: End byte column.

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
                name: The semantic field name for error messages.
                field_value: Text currently in the legacy string field.
                node_value: Text currently in the AST child.
                last_value: Last synchronized text.

            Returns:
                Single reconciled string value.

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
            kind: Field category, or None to include every category.

        Returns:
            Ordered semantic fields.

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
            style: Target format; defaults to the detected format.

        Returns:
            Document string value, without Python quotation marks.

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
        output: list[str] = [self.summary]
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
            content: list[str] = self._section_content(
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
        return """\

""".join(output).rstrip()

    def synchronize_symbols(self, *, include_types: bool = False) -> None:
        """Synchronize documented identifiers with linked executable AST nodes.

        A function argument or class attribute rename can be propagated to
        its DocEntry without reparsing or guessing from source positions.
        This operation is explicit; parsing alone never changes
        documentation.

        Args:
            include_types: Also update documentation types from AST
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

    def link(self) -> None:
        """Connect semantic fields to arguments, annotations and statements."""
        if self.owner is None:
            return
        owner: DocumentedOwner = self.owner
        attributes: dict[str, AST] = (
            self._class_attributes(owner=owner)
            if isinstance(owner, ClassDef)
            else {}
        )
        raises, returns = self._scan_owner(owner=owner, attributes=attributes)
        tables: _LinkTables = _LinkTables(
            owner=owner,
            parameters=self._owner_parameters(owner=owner),
            attributes=attributes,
            raises=raises,
            returns=returns,
        )
        for entry in self.entries():
            self._link_entry(entry=entry, tables=tables)

    @staticmethod
    def _unknown_section_lines(
        *,
        section: DocSection,
        target: DocStyle,
    ) -> list[str]:
        """Serialize a section whose syntax is not understood.

        Args:
            section: Unrecognized section.
            target: Output format.

        Returns:
            Lines including a leading blank separator.

        """
        output: list[str] = [""]
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
    def _numpy_entry_lines(*, entry: DocEntry) -> list[str]:
        """Serialize one entry in NumPy style.

        Args:
            entry: Semantic field.

        Returns:
            Header line plus indented description lines.

        """
        key: str = entry.name or entry.type_name or ""
        lines: list[str] = [
            (f"{entry.name} : {entry.type_name}")
            if entry.name and entry.type_name
            else key,
        ]
        if entry.description:
            lines.extend(
                (f"    {line}") if line else ""
                for line in entry.description.split(
                    sep="""\

""",
                )
            )
        return lines

    @staticmethod
    def _directive_entry_lines(
        *,
        entry: DocEntry,
        kind: DocKind,
        target: DocStyle,
    ) -> list[str]:
        """Serialize one entry in reST or Epytext directive style.

        Args:
            entry: Semantic field.
            kind: Containing section kind.
            target: Output format.

        Returns:
            Directive lines, including a separate type directive.

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
        lines: list[str] = [
            (f"{sign}{label_name}{suffix}: {entry.description}").rstrip(),
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
        content: list[str],
        target: DocStyle,
    ) -> list[str]:
        """Emit a section header followed by its content lines.

        Args:
            section: Normalized section.
            content: Rendered entry lines.
            target: Output format.

        Returns:
            Lines including a leading blank separator.

        """
        output: list[str] = [""]
        if target in ("google", "pep257"):
            output.append(f"{Constants.titles[section.kind]}:")
            output.extend(
                line if line.startswith("    ") else (f"    {line}")
                for line in """\

""".join(content).split(
                    sep="""\

""",
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
            owner: Function or class containing the docstring.

        Returns:
            Argument nodes keyed by parameter name; empty for classes.

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
    def _class_attributes(*, owner: ClassDef) -> dict[str, AST]:
        """Index class-level annotated and assigned names.

        Args:
            owner: Class containing the docstring.

        Returns:
            Assignment statements keyed by attribute name.

        """
        attributes: dict[str, AST] = {}
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
        attributes: dict[str, AST],
    ) -> tuple[dict[str, Raise], list[Return]]:
        """Walk an owner collecting raises, returns and self attributes.

        Args:
            owner: Function or class containing the docstring.
            attributes: Attribute table extended with ``self`` assignments.

        Returns:
            Raise statements by exception name and returns in walk order.

        """
        raises: dict[str, Raise] = {}
        returns: list[Return] = []
        for node in walk(node=owner):
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
        return (raises, returns)

    @staticmethod
    def _link_entry(*, entry: DocEntry, tables: _LinkTables) -> None:
        """Attach one semantic field to its executable counterpart.

        Args:
            entry: Documentation field to link.
            tables: Candidate executable nodes indexed by kind.

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

    def _section_content(
        self,
        *,
        section: DocSection,
        target: DocStyle,
    ) -> list[str]:
        """Collect rendered entry lines for one known section.

        Args:
            section: Normalized section to serialize.
            target: Output format.

        Returns:
            Content lines, without the section header.

        """
        content: list[str] = []
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
    ) -> list[str]:
        """Serialize one entry in the target style.

        Args:
            entry: Semantic field.
            kind: Containing section kind.
            target: Output format.

        Returns:
            Lines for this entry.

        """
        key: str = entry.name or entry.type_name or ""
        if target in ("google", "pep257"):
            label: str = (
                (f"{entry.name} ({entry.type_name})")
                if entry.name and entry.type_name
                else key
            )
            return [
                (f"    {label}: {entry.description}").rstrip()
                if label
                else (f"    {entry.description}").rstrip(),
            ]
        if target == "numpy":
            return self._numpy_entry_lines(entry=entry)
        if target in ("rest", "epytext"):
            return self._directive_entry_lines(
                entry=entry,
                kind=kind,
                target=target,
            )
        return [": ".join(part for part in (key, entry.description) if part)]


@final
class ModuleDocstringNode(DocstringNode):
    """A semantically distinguished leading module-level documentation node."""


def _find_marker(
    lines: list[str],
    index: int,
) -> tuple[DocStyle, str, str] | None:
    """Recognize a structured field or section at a dedented line.

    Args:
        lines: Dedented document lines.
        index: Current zero-based line index.

    Returns:
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
    intro: list[str],
    entries: list[DocEntry],
    current: DocEntry | None,
) -> None:
    """Record a blank line as a description gap or intro spacing.

    Args:
        intro: Free-form lines preceding the first entry.
        entries: Structured entries parsed so far.
        current: Entry receiving continuation text, if any.

    """
    if current is not None and current.description:
        current.description += """\

"""
    elif not entries:
        intro.append("")


def _matched_entry(
    *,
    match: Match[str],
    kind: DocKind,
    style: DocStyle,
    line: str,
) -> DocEntry:
    """Build an entry from a style-specific item-header match.

    Args:
        match: Regex hit on a dedented section line.
        kind: Semantic category.
        style: Source style used by this section.
        line: Raw source line for the entry.

    Returns:
        A normalized structured entry.

    """
    label: str = match.group(1).strip()
    payload: str = match.group(2).strip()
    if style == "google":
        detail: Match[str] | None = Constants.google_parameter.fullmatch(
            string=label,
        )
        name: str | None = detail.group(1) if detail else label
        type_name: str | None = detail.group(2) if detail else None
        if kind in ("returns", "yields") and (not type_name):
            type_name, name = (label, None)
    else:
        name = label
        type_name = payload
        payload = ""
    return DocEntry(
        kind=kind,
        name=name,
        type_name=type_name,
        description=payload,
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
        entries: Parsed section entries.
        style: Source style used by this section.
        kind: Semantic category.

    Returns:
        Expanded entries, or the original list when inapplicable.

    """
    if not (style == "numpy" and kind in ("parameters", "attributes")):
        return entries
    expanded: list[DocEntry] = []
    for entry in entries:
        names: list[str] = (
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


def _parse_indented_entries(
    *,
    kind: DocKind,
    lines: list[str],
    style: DocStyle,
) -> tuple[list[DocEntry], str]:
    """Normalize Google or NumPy item blocks and continuation lines.

    Args:
        kind: Semantic category.
        lines: Raw contents of one section.
        style: Source style used by this section.

    Returns:
        Structured entries and remaining free-form description.

    """
    if kind not in ("parameters", "returns", "yields", "raises", "attributes"):
        return (
            [],
            """\

""".join(lines).strip(),
        )
    entries: list[DocEntry] = []
    intro: list[str] = []
    current: DocEntry | None = None
    base_indent: int | None = None
    for line in lines:
        if not line.strip():
            _absorb_blank_line(intro=intro, entries=entries, current=current)
            continue
        stripped: str = line.strip()
        indent: int = len(line) - len(line.lstrip())
        if base_indent is None:
            base_indent = indent
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
        if match is not None:
            current = _matched_entry(
                match=match,
                kind=kind,
                style=style,
                line=line,
            )
            entries.append(current)
        elif (
            is_root
            and style == "numpy"
            and (kind in ("returns", "yields", "raises"))
        ):
            current = DocEntry(
                kind=kind,
                name=stripped if kind == "raises" else None,
                type_name=stripped if kind != "raises" else None,
                raw=line,
            )
            entries.append(current)
        elif (
            is_root
            and style == "google"
            and (kind in ("returns", "yields"))
            and (current is None)
        ):
            current = DocEntry(kind=kind, description=stripped, raw=line)
            entries.append(current)
        elif current is not None:
            current.description = """\

""".join(
                part
                for part in (
                    current.description.rstrip("""\

"""),
                    stripped,
                )
                if part
            )
        else:
            intro.append(stripped)
    return (
        _expand_numpy_names(entries=entries, style=style, kind=kind),
        """\

""".join(intro).strip(),
    )


def _merge_field(
    *,
    sections: list[DocSection],
    line: str,
    continuation: list[str],
) -> None:
    """Accumulate a reST/Epytext field with independently supplied types.

    Args:
        sections: Existing normalized sections to update.
        line: Directive's first line.
        continuation: Indented continuation lines.

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
    description: str = """\

""".join(
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
                raw="""\

""".join([line, *continuation]),
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
        source: Evaluated Python docstring constant.
        owner: Containing function or class, if available.
        expression: Executable statement containing the string constant.

    Returns:
        An AST docstring node with semantic entries and source links.

    """
    cleaned: str = cleandoc(doc=source)
    lines: list[str] = cleaned.split(
        sep="""\

""",
    )
    while lines and (not lines[0].strip()):
        lines.pop(0)
    summary: str = lines.pop(0).strip() if lines else ""
    while lines and (not lines[0].strip()):
        lines.pop(0)
    introduction: list[str] = []
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
            following: list[str] = []
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
        chunk: list[str] = [payload] if payload else []
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
                raw="""\

""".join(chunk).strip(),
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
    node: DocstringNode = node_type(
        spec=DocstringSpec(
            style=style,
            summary=summary,
            description="""\

""".join(introduction).strip(),
            sections=sections,
            raw=source,
            layout=DocstringLayout(
                is_one_line="""\

"""
                not in source
                and "\r" not in source,
                has_blank_after_summary=len(source.splitlines()) > 1
                and (not source.splitlines()[1].strip()),
                summary_has_period=summary.endswith("."),
                is_trailing_blank=source.endswith("""\


"""),
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
        body: Module statement list, including nested definitions.

    Returns:
        Lexically ordered normalized docstring AST nodes.

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
