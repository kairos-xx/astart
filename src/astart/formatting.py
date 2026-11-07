"""Conservative, source-slice-preserving editor for mutable Python ASTs.

The editor reconstructs syntax only at changed lexical spans. Unsupported
transformations raise rather than silently claiming source fidelity.
"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    And,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    BoolOp,
    ClassDef,
    Compare,
    Constant,
    Div,
    Eq,
    FloorDiv,
    FormattedValue,
    FunctionDef,
    Gt,
    GtE,
    In,
    Invert,
    Is,
    IsNot,
    JoinedStr,
    Lambda,
    LShift,
    Lt,
    LtE,
    MatMult,
    Mod,
    Module,
    Mult,
    Not,
    NotEq,
    NotIn,
    Or,
    Pow,
    RShift,
    Sub,
    UAdd,
    UnaryOp,
    USub,
    alias,
    arg,
    arguments,
    fix_missing_locations,
    iter_fields,
    stmt,
    unparse,
    walk,
)
from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from itertools import pairwise
from re import compile as compile_pattern
from tokenize import (
    COMMENT,
    FSTRING_END,
    FSTRING_MIDDLE,
    FSTRING_START,
    NAME,
    STRING,
    generate_tokens,
)
from types import EllipsisType
from typing import TYPE_CHECKING, Literal, final

from astart.node_attributes import list_items, read_attribute

if TYPE_CHECKING:
    from re import Match
type PatchValue = AST | list[AST] | tuple[AST, ...] | str | float | bool | None
type FieldValue = (
    AST | str | bytes | int | float | complex | bool | None | list[FieldValue]
)


@final
class FormatPreservationError(ValueError):
    """An AST mutation cannot be reconstructed without risking source loss.

    Attributes:
        recoverable: Whether an enclosing node may repair the failure by
            regenerating itself. Edits that would produce invalid Python
            when regenerated set this to ``False``.

    """

    def __init__(self, *args: str, recoverable: bool = True) -> None:
        """Create the error.

        Args:
            *args: Message parts.
            recoverable: Whether an enclosing node may regenerate itself.

        """
        super().__init__(*args)
        self.recoverable: bool = recoverable


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class Patch:
    """A replacement in absolute original source character coordinates.

    Attributes:
        start: Inclusive original character index.
        end: Exclusive original character index.
        text: Replacement text.

    """

    start: int
    end: int
    text: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Field:
    """Original AST field contents, using identity for child nodes.

    Attributes:
        kind: Scalar, individual AST child, or AST-child list.
        ids: Original AST child identity tuple.
        value: Immutable scalar representation.

    """

    kind: Literal["scalar", "child", "children"]
    ids: tuple[int, ...]
    value: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _Node:
    """Original snapshot for one mutable executable AST node.

    Attributes:
        fields: Original fields and identities.
        start: Absolute start of original AST lexical span, if available.
        end: Absolute end of original AST lexical span, if available.
        line_start: Start of a statement's physical line.
        line_end: Exclusive end of a statement's final physical line.
        indent: Original statement's indentation prefix.

    """

    fields: dict[str, _Field]
    start: int | None
    end: int | None
    line_start: int | None
    line_end: int | None
    indent: str


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _DebugField:
    """Resolved lexical spans of a debug ``{expr=}`` field and its label.

    Attributes:
        label_text: Raw label text preceding the debug expression.
        formatted: Snapshot of the FormattedValue node.
        formatted_span: Original span of the whole formatted field.
        label_end: Absolute end of the label text.
        value_span: Original span of the wrapped value expression.
        previous_id: Identity of the originally wrapped value expression.

    """

    label_text: str
    formatted: _Node
    formatted_span: tuple[int, int]
    label_end: int
    value_span: tuple[int, int]
    previous_id: int


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class _ArgumentTrivia:
    """Original trivia surrounding a function's positional arguments.

    Attributes:
        prefix: Text between ``(`` and the first original argument.
        suffix: Text between the last original argument and ``)``.
        separator: Comma spelling and whitespace between arguments.

    """

    prefix: str
    suffix: str
    separator: str


@final
class FormatPreserver:
    """Capture initial lexical ownership and reconstruct supported AST edits.

    Source text is never advanced to a regenerated baseline, permitting
    repeated edits, undo operations, and source-relative node moves.

    Attributes:
        source: Complete original source.
        lines: Original physical lines including their newline endings.
        nodes: Immutable-at-capture AST field snapshots by node identity.

    """

    def __init__(self, *, source: str, body: list[stmt]) -> None:
        """Snapshot executable nodes and initial statement-suite trivia.

        Args:
            source: Exact Python source, including whitespace and comments.
            body: Root executable AST statements, before any edits.

        """
        self.source: str = source
        self.lines: list[str] = source.splitlines(keepends=True)
        self.offsets: list[int] = [0]
        for line in self.lines:
            self.offsets.append(self.offsets[-1] + len(line))
        self._lexical_tokens: tuple[tuple[int, str, int, int], ...] = tuple(
            (
                token.type,
                token.string,
                self.offsets[token.start[0] - 1] + token.start[1],
                self.offsets[token.end[0] - 1] + token.end[1],
            )
            for token in generate_tokens(
                readline=StringIO(initial_value=source).readline,
            )
            if 0 < token.start[0] <= len(self.lines)
            and 0 < token.end[0] <= len(self.lines)
        )
        self.newline: str = (
            """\
\r
"""
            if """\
\r
"""
            in source
            else "\r"
            if "\r" in source
            else """\

"""
        )
        self.root_ids: tuple[int, ...] = tuple(
            id(statement) for statement in body
        )
        self.nodes: dict[int, _Node] = {}
        self._node_by_id: dict[int, AST] = {}
        self.parents: dict[int, int] = {}
        self._shared_line_counts: dict[tuple[int, int], int] = {}
        self._inline_parents: set[int] = set()
        self.leading: dict[int, str] = {}
        self.first_prefix: str = ""
        self.footer: str = ""
        self._capture_suite(body=body, is_root=True)
        for statement in body:
            self._capture(node=statement)

    @staticmethod
    def apply(
        *,
        source: str,
        begin: int,
        end: int,
        patches: list[Patch],
    ) -> str:
        """Apply disjoint source patches without shifting offsets.

        Args:
            begin: Begin supplied as int for this operation.
            end: End identifying a position in the relevant sequence or source.
            patches: Patches supplied as list[Patch] for this operation.
            source: The source examined while apply disjoint source patches
                without shifting offsets.

        Returns:
            Rendered source text produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        ordered: list[Patch] = sorted(
            patches,
            key=lambda item: (item.start, item.end),
        )
        result: list[str] = []
        position: int = begin
        for patch in ordered:
            if (
                patch.start < position
                or patch.end > end
                or patch.start > patch.end
            ):
                msg: str = (
                    "Overlapping or out-of-bounds format-preserving changes."
                )
                raise FormatPreservationError(msg)
            result.extend((source[position : patch.start], patch.text))
            position = patch.end
        result.append(source[position:end])
        return "".join(result)

    def has_structural_mutations(self, *, body: list[stmt]) -> bool:
        """Detect list membership or ordering edits affecting lexical scopes.

        Args:
            body: Current executable program statement list.

        Returns:
            Whether any structural AST child sequence changed identity/order.

        """
        if tuple(id(statement) for statement in body) != self.root_ids:
            return True
        for node in walk(node=Module(body=body, type_ignores=[])):
            if isinstance(node, Module):
                continue
            state: _Node | None = self.nodes.get(id(node))
            if state is None:
                return True
            for name, item in iter_fields(node=node):
                field: FieldValue = item
                children: list[FieldValue] = list_items(value=field)
                if (
                    isinstance(field, list)
                    and all(isinstance(child, AST) for child in children)
                    and tuple(
                        id(child)
                        for child in children
                        if isinstance(child, AST)
                    )
                    != (state.fields[name].ids if name in state.fields else ())
                ):
                    return True
        return False

    def render(
        self,
        *,
        body: list[stmt],
        comments: list[tuple[int, int, str]],
    ) -> str:
        """Render the edited AST with exact preservation of untouched trivia.

        Args:
            body: Mutable executable root statements.
            comments: Original coordinate spans and current replacement text.

        Returns:
            Python source with supported changes localized.

        Raises:
            FormatPreservationError: On ambiguous or lossy transformations.

        """
        replacements: list[Patch] = [
            Patch(start=start, end=end, text=text)
            for start, end, text in comments
            if self.source[start:end] != text
        ]
        original_order: tuple[int, ...] = self.root_ids
        current_order: tuple[int, ...] = tuple(id(item) for item in body)
        # Root changes require moving complete statement fragments, not lines
        # modified after the fact. The caller always validates AST equivalence.
        if current_order != original_order:
            return self._emit_statements(
                body=body,
                nested=False,
                replacements=replacements,
            )
        edits: list[Patch] = list(replacements)
        for statement in body:
            edits.extend(
                self._changed(node=statement, replacements=replacements),
            )
        return self.apply(
            source=self.source,
            begin=0,
            end=len(self.source),
            patches=edits,
        )

    @staticmethod
    def _span(*, state: _Node) -> tuple[int, int] | None:
        """Return a node's lexical span when both ends are known.

        Args:
            state: State supplied as _Node for this operation.

        Returns:
            tuple[int, int] | None produced by this operation.

        """
        if state.start is None or state.end is None:
            return None
        return state.start, state.end

    @staticmethod
    def _debug_positions(
        *,
        formatted_span: tuple[int, int],
        label_span: tuple[int, int],
        value_span: tuple[int, int],
    ) -> bool:
        """Check that the label sits between ``{`` and its value.

        Args:
            formatted_span: Formatted span supplied as tuple[int, int] for this
                operation.
            label_span: Label span supplied as tuple[int, int] for this
                operation.
            value_span: Value span supplied as tuple[int, int] for this
                operation.

        Returns:
            Whether the requested condition holds.

        """
        return (
            formatted_span[0] < label_span[0] <= value_span[0]
            and value_span[1] < label_span[1]
        )

    @staticmethod
    def _render_constant(
        *,
        value: str | complex | bytes | bool | None | EllipsisType,
        original: str,
    ) -> str:
        """Keep compatible quote/base spelling for edited literal values.

        Args:
            original: Original supplied as str for this operation.
            value: The value examined while keep compatible quote/base spelling
                for edited literal values.

        Returns:
            str produced by this operation.

        """
        if isinstance(value, EllipsisType):
            return "..."
        if isinstance(value, str):
            match: Match[str] | None = compile_pattern(
                pattern=r"(?is)^(?P<prefix>[rub]*)?(?P<quote>'''|\"\"\"|'|\")",
            ).match(string=original)
            if match is None or "b" in (match.group("prefix") or "").lower():
                return repr(value)
            quote: str = match.group("quote")
            escaped: str = value.replace("\\", "\\\\").replace(
                quote,
                "\\" + quote,
            )
            if len(quote) == 1:
                escaped = escaped.replace(
                    """\

""",
                    "\\n",
                ).replace("\r", "\\r")
            return quote + escaped + quote
        if isinstance(value, int) and not isinstance(value, bool):
            lower: str = original.lower().replace("_", "")
            prefix: str = (
                original[:2] if lower.startswith(("0x", "0b", "0o")) else ""
            )
            digits: str = original[len(prefix) :]
            symbol: str = (
                "X"
                if prefix == "0X"
                or (
                    prefix.lower() == "0x"
                    and any(letter in digits for letter in "ABCDEF")
                )
                else "x"
                if prefix.lower() == "0x"
                else "b"
                if prefix.lower() == "0b"
                else "o"
                if prefix.lower() == "0o"
                else "d"
            )
            rendering: str = format(value, symbol)
            if "_" in digits and len(rendering) == len(
                digits.replace("_", ""),
            ):
                positions: set[int] = {
                    index
                    for index, character in enumerate(iterable=digits)
                    if character == "_"
                }
                output: list[str] = []
                cursor: int = 0
                for index in range(len(digits)):
                    if index in positions:
                        output.append("_")
                    else:
                        output.append(rendering[cursor])
                        cursor += 1
                rendering = "".join(output)
            return prefix + rendering
        return repr(value)

    @staticmethod
    def _require_simple_signature(*, node: arguments) -> None:
        """Reject signatures beyond plain positional-or-keyword args.

        Args:
            node: The node examined while reject signatures beyond plain
                positional-or-keyword args.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if (
            node.posonlyargs
            or node.vararg
            or node.kwonlyargs
            or node.kwarg
            or node.defaults
            or node.kw_defaults
        ):
            msg: str = (
                "Argument-list preservation currently supports simple "
                "positional-or-keyword signatures without defaults."
            )
            raise FormatPreservationError(msg)

    @staticmethod
    def _reindent(*, source: str, old: str, new: str) -> str:
        """Reindent a moved statement, rejecting unsafe multiline strings.

        Args:
            new: New supplied as str for this operation.
            old: Old supplied as str for this operation.
            source: The source examined while reindent a moved statement,
                rejecting unsafe multiline strings.

        Returns:
            str produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if any(
            token.type in (STRING, FSTRING_START, FSTRING_MIDDLE)
            and token.start[0] != token.end[0]
            for token in generate_tokens(
                readline=StringIO(initial_value=source).readline,
            )
        ):
            msg: str = (
                "Cannot reindent moved multiline strings "
                "without changing their value."
            )
            raise FormatPreservationError(msg)
        rewritten: list[str] = []
        for line in source.splitlines(keepends=True):
            if line.strip() and not line.startswith(old):
                msg = "Moved statement has inconsistent indentation."
                raise FormatPreservationError(msg)
            rewritten.append(new + line[len(old) :] if line.strip() else line)
        return "".join(rewritten)

    @staticmethod
    def _render_annotation(*, value: AST) -> str:
        """Render a new annotation expression as source.

        Args:
            value: Annotation expression.

        Returns:
            Source text of the expression.

        """
        return unparse(
            ast_obj=fix_missing_locations(node=deepcopy(x=value)),
        )

    def _position(self, *, line: int, byte_column: int) -> int:
        """Map one-based UTF-8 AST locations to Python source indices.

        Args:
            byte_column: Byte column supplied as int for this operation.
            line: Line identifying a position in the relevant sequence or
                source.

        Returns:
            int produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if line < 1 or line > len(self.lines):
            msg: str = "AST location is outside the original source."
            raise FormatPreservationError(msg)
        prefix: bytes = self.lines[line - 1].encode(encoding="utf-8")[
            :byte_column
        ]
        try:
            return self.offsets[line - 1] + len(
                prefix.decode(encoding="utf-8"),
            )
        except UnicodeDecodeError as exc:
            msg = "AST location bisects a UTF-8 code point."
            raise FormatPreservationError(msg) from exc

    def _line_start(self, *, node: stmt) -> int:
        """Locate a statement's first physical line, including decorators.

        Args:
            node: The node examined while locate a statement's first physical
                line, including decorators.

        Returns:
            int produced by this operation.

        """
        line: int = node.lineno
        if (
            isinstance(node, (FunctionDef, AsyncFunctionDef, ClassDef))
            and node.decorator_list
        ):
            line = min(
                line,
                *(decorator.lineno for decorator in node.decorator_list),
            )
        return self.offsets[line - 1]

    def _capture(self, *, node: AST) -> None:
        """Snapshot a node and its original descendants recursively.

        Args:
            node: The node examined while snapshot a node and its original
                descendants recursively.

        """
        if id(node) in self.nodes:
            return
        self._node_by_id[id(node)] = node
        first: int | None = None
        last: int | None = None
        line: int | None = read_attribute(node=node, name="lineno", kind=int)
        column: int | None = read_attribute(
            node=node,
            name="col_offset",
            kind=int,
        )
        end_line: int | None = read_attribute(
            node=node,
            name="end_lineno",
            kind=int,
        )
        end_column: int | None = read_attribute(
            node=node,
            name="end_col_offset",
            kind=int,
        )
        if (
            line is not None
            and column is not None
            and end_line is not None
            and end_column is not None
        ):
            first = self._position(line=line, byte_column=column)
            last = self._position(line=end_line, byte_column=end_column)
        is_statement: bool = isinstance(node, stmt)
        line_start: int | None = (
            self._line_start(node=node) if is_statement else None
        )
        line_end: int | None = (
            self.offsets[node.end_lineno]
            if is_statement and node.end_lineno is not None
            else None
        )
        indent: str = (
            self.lines[node.lineno - 1][
                : len(self.lines[node.lineno - 1])
                - len(self.lines[node.lineno - 1].lstrip(" \t"))
            ]
            if is_statement
            else ""
        )
        fields: dict[str, _Field] = {}
        descendants: list[AST] = []
        for name, item in iter_fields(node=node):
            value: FieldValue = item
            children: list[FieldValue] = list_items(value=value)
            if isinstance(value, AST):
                fields[name] = _Field(kind="child", ids=(id(value),), value="")
                descendants.append(value)
            elif isinstance(value, list) and all(
                isinstance(child, AST) for child in children
            ):
                nodes: list[AST] = [
                    child for child in children if isinstance(child, AST)
                ]
                fields[name] = _Field(
                    kind="children",
                    ids=tuple(id(child) for child in nodes),
                    value="",
                )
                descendants.extend(nodes)
            else:
                fields[name] = _Field(kind="scalar", ids=(), value=repr(item))
        self.nodes[id(node)] = _Node(
            fields=fields,
            start=first,
            end=last,
            line_start=line_start,
            line_end=line_end,
            indent=indent,
        )
        if is_statement and line_start is not None and line_end is not None:
            location: tuple[int, int] = (line_start, line_end)
            self._shared_line_counts[location] = (
                self._shared_line_counts.get(location, 0)
                + 1
                - self._inline_parent_credit(node=node, location=location)
            )
        for child in descendants:
            self.parents[id(child)] = id(node)
            self._capture(node=child)
        for name, item in iter_fields(node=node):
            children = list_items(value=item)
            if (
                name in ("body", "orelse", "finalbody")
                and children
                and all(isinstance(part, stmt) for part in children)
            ):
                self._capture_suite(
                    body=[part for part in children if isinstance(part, stmt)],
                    is_root=False,
                )

    def _inline_parent_credit(
        self,
        *,
        node: AST,
        location: tuple[int, int],
    ) -> int:
        """Cancel a compound statement's own claim on its inline body's line.

        ``def f(): ...`` is one statement written on one line, not two
        statements sharing it. The first inline child of a compound statement
        that occupies exactly the same physical lines gives back the parent's
        count, so only genuine siblings (``a = 1; b = 2``, or several
        statements in one inline body) count as sharing a line.

        Args:
            node: Statement being captured.
            location: Its physical line span.

        Returns:
            One for the first inline child of a parent, otherwise zero.

        """
        parent_id: int | None = self.parents.get(id(node))
        parent: _Node | None = (
            self.nodes.get(parent_id) if parent_id is not None else None
        )
        if (
            parent_id is None
            or parent is None
            or (parent.line_start, parent.line_end) != location
            or parent_id in self._inline_parents
        ):
            return 0
        self._inline_parents.add(parent_id)
        return 1

    def _capture_suite(self, *, body: list[stmt], is_root: bool) -> None:
        """Assign inter-statement trivia to the following statement.

        Args:
            body: Body supplied as list[stmt] for this operation.
            is_root: Whether to root.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        previous: int = 0
        for index, statement in enumerate(iterable=body):
            begin: int = self._line_start(node=statement)
            if index == 0:
                if is_root:
                    self.first_prefix = self.source[:begin]
            else:
                self.leading[id(statement)] = self.source[previous:begin]
            end: int | None = statement.end_lineno
            if end is None:
                msg: str = "A parsed statement must carry an end line."
                raise FormatPreservationError(msg)
            previous = self.offsets[end]
        if is_root:
            if body:
                self.footer = self.source[previous:]
            else:
                self.first_prefix = self.source
                self.footer = ""

    def _tokens(
        self,
        *,
        start: int,
        end: int,
    ) -> list[tuple[int, str, int, int]]:
        """Read tokenizer tokens with absolute character coordinates.

        Args:
            end: End identifying a position in the relevant sequence or source.
            start: Start identifying a position in the relevant sequence or
                source.

        Returns:
            list[tuple[int, str, int, int]] produced by this operation.

        """
        fragment: str = self.source[start:end]
        result: list[tuple[int, str, int, int]] = []
        lines: list[str] = fragment.splitlines(keepends=True)
        offsets: list[int] = [0]
        for line in lines:
            offsets.append(offsets[-1] + len(line))
        try:
            for token in generate_tokens(
                readline=StringIO(initial_value=fragment).readline,
            ):
                if token.start[0] > len(lines) or token.end[0] > len(lines):
                    continue
                left: int = (
                    start + offsets[token.start[0] - 1] + token.start[1]
                )
                right: int = start + offsets[token.end[0] - 1] + token.end[1]
                result.append((token.type, token.string, left, right))
        except (IndentationError, SyntaxError):
            # A subsection can begin with a syntactically incomplete
            # expression.
            pass
        return result

    def _fstring_literal_patch(self, *, node: Constant, value: str) -> Patch:
        """Edit an f-string literal segment without quoting it as Python code.

        Args:
            node: Original f-string literal node.
            value: Current decoded literal value.

        Returns:
            Replacement for exactly one FSTRING_MIDDLE token.

        Raises:
            FormatPreservationError: If the segment cannot be mapped safely.

        """
        state: _Node = self.nodes[id(node)]
        if state.start is None or state.end is None:
            msg: str = "The f-string literal has no original source span."
            raise FormatPreservationError(msg)
        stack: list[str] = []
        prefix: str = ""
        original: str | None = None
        for kind, text, start, end in self._lexical_tokens:
            if kind == FSTRING_START:
                stack.append(text)
            elif kind == FSTRING_END and stack:
                stack.pop()
            elif kind == FSTRING_MIDDLE and (start, end) == (
                state.start,
                state.end,
            ):
                original = text
                prefix = stack[-1] if stack else ""
                break
        if original is None:
            msg = "The f-string literal is not a standalone lexical segment."
            raise FormatPreservationError(msg)
        quote: str = (
            "'" * 3
            if "'" * 3 in prefix
            else '"' * 3
            if '"' * 3 in prefix
            else "'"
            if "'" in prefix
            else '"'
        )
        raw: bool = "r" in prefix[: prefix.find(quote)].lower()
        if raw and (quote in value or value.endswith("\\")):
            msg = (
                "A raw f-string literal cannot represent "
                "this replacement safely."
            )
            raise FormatPreservationError(msg)
        rendered: str = value.replace("{", "{{").replace("}", "}}")
        if not raw:
            rendered = rendered.replace("\\", "\\\\").replace(
                quote,
                "\\" + quote,
            )
        if len(quote) == 1:
            rendered = rendered.replace(
                """\

""",
                "\\n",
            ).replace("\r", "\\r")
        return Patch(start=state.start, end=state.end, text=rendered)

    def _conversion_patch(
        self,
        *,
        node: FormattedValue,
        old: _Field,
    ) -> Patch:
        """Change only the !r/!s/!a token inside a replacement field.

        Args:
            node: The node examined while change only the !r/!s/!a token inside
                a replacement field.
            old: Old supplied as _Field for this operation.

        Returns:
            Patch produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        state: _Node = self.nodes[id(node)]
        child: _Node = self.nodes[id(node.value)]
        if state.end is None or child.end is None or state.start is None:
            msg: str = "F-string conversion has no exact source anchor."
            raise FormatPreservationError(msg)
        old_code: int = int(old.value)
        new_code: int = node.conversion
        if old_code not in (-1, 114, 115, 97) or new_code not in (
            -1,
            114,
            115,
            97,
        ):
            msg = "Invalid f-string conversion directive."
            raise FormatPreservationError(msg)
        conversion: tuple[int, int] | None = None
        tokens: list[tuple[int, str, int, int]] = [
            token
            for token in self._lexical_tokens
            if child.end <= token[2] and token[3] <= state.end
        ]
        for index, token in enumerate(iterable=tokens[:-1]):
            if token[1] == "!" and tokens[index + 1][1] in ("r", "s", "a"):
                conversion = (token[2], tokens[index + 1][3])
                break
        if old_code != -1 and conversion is None:
            msg = (
                "The original f-string conversion is not lexically available."
            )
            raise FormatPreservationError(msg)
        if conversion is not None:
            return Patch(
                start=conversion[0],
                end=conversion[1],
                text="" if new_code == -1 else "!" + chr(new_code),
            )
        delimiter: int = state.end - 1
        for token in tokens:
            if token[1] == ":" and token[2] < delimiter:
                delimiter = token[2]
                break
        return Patch(
            start=delimiter,
            end=delimiter,
            text="" if new_code == -1 else "!" + chr(new_code),
        )

    def _debug_fstring_patch(
        self,
        *,
        node: FormattedValue,
        replacements: list[Patch],
    ) -> Patch | None:
        """Retain a debug f-string's printed label when its expression changes.

        Args:
            node: Formatted expression potentially preceded by a debug label.
            replacements: Existing semantic comment edits.

        Returns:
            The exact localized debug-field edit, or None if not needed.

        Raises:
            FormatPreservationError: If simultaneous edits cannot be merged.

        """
        field: _DebugField | None = self._debug_field(node=node)
        if field is None:
            return None
        expression: str | None = self._debug_expression(
            node=node,
            field=field,
            replacements=replacements,
        )
        if expression is None:
            return None
        self._check_debug_coedits(
            node=node,
            formatted=field.formatted,
            replacements=replacements,
        )
        delimiter: int | None = next(
            (
                start
                for _, spelling, start, _ in self._lexical_tokens
                if field.label_end <= start < field.formatted_span[1]
                and spelling in ("!", ":", "}")
            ),
            None,
        )
        if delimiter is None:
            msg: str = (
                "The debug f-string field has no conversion "
                "or closing delimiter."
            )
            raise FormatPreservationError(msg)
        suffix: str = self.source[delimiter : field.formatted_span[1]]
        if not suffix.startswith("!") and node.conversion != -1:
            suffix = "!" + chr(node.conversion) + suffix
        return Patch(
            start=field.formatted_span[0],
            end=field.formatted_span[1],
            text=(
                field.label_text.replace("{", "{{").replace("}", "}}")
                + "{"
                + expression
                + suffix
            ),
        )

    def _debug_field(self, *, node: FormattedValue) -> _DebugField | None:
        """Locate a debug ``{expr=}`` label and resolve its spans.

        Args:
            node: The node examined while locate a debug ``{expr=}`` label and
                resolve its spans.

        Returns:
            _DebugField | None produced by this operation.

        """
        parent: AST | None = self._node_by_id.get(
            self.parents.get(id(node), -1),
        )
        if not isinstance(parent, JoinedStr):
            return None
        position: int = next(
            (
                index
                for index, item in enumerate(iterable=parent.values)
                if item is node
            ),
            -1,
        )
        if position == 0:
            return None
        label: AST = parent.values[position - 1]
        if not isinstance(label, Constant):
            return None
        formatted: _Node = self.nodes[id(node)]
        label_state: _Node = self.nodes[id(label)]
        previous_id: int = formatted.fields["value"].ids[0]
        value_state: _Node = self.nodes[previous_id]
        formatted_span: tuple[int, int] | None = self._span(state=formatted)
        label_span: tuple[int, int] | None = self._span(state=label_state)
        value_span: tuple[int, int] | None = self._span(state=value_state)
        if (
            formatted_span is None
            or label_span is None
            or value_span is None
            or not self._debug_positions(
                formatted_span=formatted_span,
                label_span=label_span,
                value_span=value_span,
            )
            or not isinstance(label.value, str)
            or not label.value.rstrip().endswith("=")
        ):
            return None
        return _DebugField(
            label_text=label.value,
            formatted=formatted,
            formatted_span=formatted_span,
            label_end=label_span[1],
            value_span=value_span,
            previous_id=previous_id,
        )

    def _debug_expression(
        self,
        *,
        node: FormattedValue,
        field: _DebugField,
        replacements: list[Patch],
    ) -> str | None:
        """Render the debug expression from local edits or regeneration.

        Args:
            field: Field supplied as _DebugField for this operation.
            node: The node examined while render the debug expression from
                local edits or regeneration.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Returns:
            str | None produced by this operation.

        """
        if id(node.value) != field.previous_id:
            return unparse(
                ast_obj=fix_missing_locations(
                    node=deepcopy(x=node.value),
                ),
            )
        edits: list[Patch] = self._changed(
            node=node.value,
            replacements=replacements,
        )
        if not edits:
            return None
        return self.apply(
            source=self.source,
            begin=field.value_span[0],
            end=field.value_span[1],
            patches=edits,
        )

    def _check_debug_coedits(
        self,
        *,
        node: FormattedValue,
        formatted: _Node,
        replacements: list[Patch],
    ) -> None:
        """Reject simultaneous conversion or format-spec edits.

        Args:
            formatted: Formatted supplied as _Node for this operation.
            node: The node examined while reject simultaneous conversion or
                format-spec edits.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        old_conversion: int = int(formatted.fields["conversion"].value)
        if node.conversion != old_conversion:
            msg: str = (
                "Simultaneous debug-expression and conversion "
                "edits need regeneration."
            )
            raise FormatPreservationError(msg)
        old_spec: _Field = formatted.fields["format_spec"]
        if (
            old_spec.kind == "child"
            and isinstance(node.format_spec, AST)
            and self._changed(node=node.format_spec, replacements=replacements)
        ):
            msg = (
                "Simultaneous debug-expression and format-spec "
                "edits are ambiguous."
            )
            raise FormatPreservationError(msg)

    def _operator_patch(self, *, node: AST, old: _Field) -> list[Patch]:
        """Patch a nested arithmetic or boolean operator, keeping operands.

        Args:
            node: The node examined while patch a nested arithmetic or boolean
                operator, keeping operands.
            old: Old supplied as _Field for this operation.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        operators: dict[type[AST], str] = {
            Add: "+",
            Sub: "-",
            Mult: "*",
            MatMult: "@",
            Div: "/",
            FloorDiv: "//",
            Mod: "%",
            Pow: "**",
            LShift: "<<",
            RShift: ">>",
            BitOr: "|",
            BitAnd: "&",
            BitXor: "^",
            And: "and",
            Or: "or",
            UAdd: "+",
            USub: "-",
            Invert: "~",
            Not: "not",
        }
        before: AST = self._node_by_id[old.ids[0]]
        after: AST | None = read_attribute(node=node, name="op", kind=AST)
        old_text: str | None = next(
            (
                symbol
                for kind, symbol in operators.items()
                if isinstance(before, kind)
            ),
            None,
        )
        new_text: str | None = next(
            (
                symbol
                for kind, symbol in operators.items()
                if isinstance(after, kind)
            ),
            None,
        )
        if old_text is None or new_text is None:
            msg: str = "The operator cannot be changed lexically."
            raise FormatPreservationError(msg)
        if isinstance(node, (BinOp, AugAssign)):
            left: _Node = self.nodes[
                id(node.left if isinstance(node, BinOp) else node.target)
            ]
            right: _Node = self.nodes[
                id(node.right if isinstance(node, BinOp) else node.value)
            ]
            first: int | None = left.end
            last: int | None = right.start
            if isinstance(node, AugAssign):
                old_text += "="
                new_text += "="
        elif isinstance(node, UnaryOp):
            outer: _Node = self.nodes[id(node)]
            operand: _Node = self.nodes[id(node.operand)]
            first, last = outer.start, operand.start
        elif isinstance(node, BoolOp):
            return [
                self._operator_between(
                    before=self.nodes[id(left)].end,
                    after=self.nodes[id(right)].start,
                    old_text=old_text,
                    new_text=new_text,
                )
                for left, right in zip(
                    node.values,
                    node.values[1:],
                    strict=False,
                )
            ]
        else:
            msg = "This operator shape requires structural regeneration."
            raise FormatPreservationError(msg)
        return [
            self._operator_between(
                before=first,
                after=last,
                old_text=old_text,
                new_text=new_text,
            ),
        ]

    def _operator_between(
        self,
        *,
        before: int | None,
        after: int | None,
        old_text: str,
        new_text: str,
    ) -> Patch:
        """Find one unique operator token between two original AST operands.

        Args:
            after: After supplied as int | None for this operation.
            before: Before supplied as int | None for this operation.
            new_text: New text supplied as str for this operation.
            old_text: Old text supplied as str for this operation.

        Returns:
            Patch produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if before is None or after is None:
            msg: str = "The operator's source span is incomplete."
            raise FormatPreservationError(msg)
        words: list[str] = old_text.split()
        tokens: list[tuple[int, str, int, int]] = [
            token
            for token in self._lexical_tokens
            if before <= token[2] and token[3] <= after
        ]
        matches: list[tuple[int, int]] = [
            (tokens[index][2], tokens[index + len(words) - 1][3])
            for index in range(len(tokens) - len(words) + 1)
            if [token[1] for token in tokens[index : index + len(words)]]
            == words
        ]
        if len(matches) != 1:
            msg = "The original operator is not uniquely identifiable."
            raise FormatPreservationError(msg)
        return Patch(start=matches[0][0], end=matches[0][1], text=new_text)

    def _compare_patches(
        self,
        *,
        node: Compare,
        old: _Field,
    ) -> list[Patch]:
        """Reconstruct each changed comparison operator, keeping operands.

        Args:
            node: The node examined while reconstruct each changed comparison
                operator, keeping operands.
            old: Old supplied as _Field for this operation.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        operators: dict[type[AST], str] = {
            Eq: "==",
            NotEq: "!=",
            Lt: "<",
            LtE: "<=",
            Gt: ">",
            GtE: ">=",
            Is: "is",
            IsNot: "is not",
            In: "in",
            NotIn: "not in",
        }
        if len(old.ids) != len(node.ops) or len(node.ops) != len(
            node.comparators,
        ):
            msg: str = "The number of comparison operators changed."
            raise FormatPreservationError(msg)
        operands: list[AST] = [node.left, *node.comparators]
        patches: list[Patch] = []
        for index, (old_id, new_op) in enumerate(
            iterable=zip(old.ids, node.ops, strict=True),
        ):
            if old_id == id(new_op):
                continue
            before: AST = self._node_by_id[old_id]
            old_text: str | None = next(
                (
                    text
                    for kind, text in operators.items()
                    if isinstance(before, kind)
                ),
                None,
            )
            new_text: str | None = next(
                (
                    text
                    for kind, text in operators.items()
                    if isinstance(new_op, kind)
                ),
                None,
            )
            if old_text is None or new_text is None:
                msg = (
                    "A comparison operation cannot be mapped to Python syntax."
                )
                raise FormatPreservationError(msg)
            patches.append(
                self._operator_between(
                    before=self.nodes[id(operands[index])].end,
                    after=self.nodes[id(operands[index + 1])].start,
                    old_text=old_text,
                    new_text=new_text,
                ),
            )
        return patches

    def _scalar_patch(self, *, node: AST, name: str, old: _Field) -> Patch:
        """Patch one scalar token, keeping surrounding lexical trivia.

        Args:
            name: Identifier of the name being resolved.
            node: The node examined while patch one scalar token, keeping
                surrounding lexical trivia.
            old: Old supplied as _Field for this operation.

        Returns:
            Patch produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        state: _Node = self.nodes[id(node)]
        if state.start is None or state.end is None:
            msg: str = (
                "Changing a location-less syntactic field needs regeneration."
            )
            raise FormatPreservationError(msg)
        value: str | int | float | complex | bytes | bool | None = getattr(
            node,
            name,
        )
        if isinstance(node, (BinOp, UnaryOp)) and name == "op":
            msg = "Operator edits must be handled as child replacements."
            raise FormatPreservationError(msg)
        if isinstance(node, FormattedValue) and name == "conversion":
            return self._conversion_patch(node=node, old=old)
        if isinstance(node, Constant) and name == "value":
            owner: AST | None = self._node_by_id.get(
                self.parents.get(id(node), -1),
            )
            if isinstance(owner, JoinedStr):
                if not isinstance(value, str):
                    msg = "An f-string literal segment must remain a string."
                    raise FormatPreservationError(msg)
                return self._fstring_literal_patch(node=node, value=value)
            original: str = self.source[state.start : state.end]
            rendered: str = self._render_constant(
                value=value,
                original=original,
            )
            return Patch(start=state.start, end=state.end, text=rendered)
        old_value: str = old.value
        if name not in ("id", "arg", "attr", "name", "asname"):
            msg = f"Cannot surgically patch {type(node).__name__}.{name}."
            raise FormatPreservationError(msg)
        if not isinstance(value, str):
            msg = f"{type(node).__name__}.{name} must remain a string."
            raise FormatPreservationError(msg)
        original_name: str = (
            old_value[1:-1] if old_value[:1] in ("'", '"') else old_value
        )
        tokens: list[tuple[int, str, int, int]] = [
            token
            for token in self._tokens(start=state.start, end=state.end)
            if token[0] == NAME and token[1] == original_name
        ]
        selected: tuple[int, str, int, int] | None = (
            tokens[-1]
            if isinstance(node, Attribute)
            or (isinstance(node, alias) and name == "asname")
            else tokens[0]
            if tokens
            else None
        )
        if selected is None:
            msg = f"Original identifier {original_name!r} was not found."
            raise FormatPreservationError(msg)
        return Patch(start=selected[2], end=selected[3], text=value)

    def _changed(
        self,
        *,
        node: AST,
        replacements: list[Patch],
    ) -> list[Patch]:
        """Compute minimal original-coordinate edits to an AST node.

        Args:
            node: The node examined while compute minimal original-coordinate
                edits to an AST node.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        state: _Node | None = self.nodes.get(id(node))
        if state is None:
            msg: str = "A new node has no original lexical position."
            raise FormatPreservationError(msg)
        try:
            return self._field_patches(
                node=node,
                state=state,
                replacements=replacements,
            )
        except FormatPreservationError as error:
            if not error.recoverable:
                raise
            if (
                state.start is None
                or state.end is None
                or isinstance(
                    node,
                    (
                        FunctionDef,
                        AsyncFunctionDef,
                        ClassDef,
                        JoinedStr,
                        FormattedValue,
                    ),
                )
            ):
                raise
            if self._has_inner_comments(start=state.start, end=state.end):
                raise
            return [
                Patch(
                    start=state.start,
                    end=state.end,
                    text=unparse(
                        ast_obj=fix_missing_locations(node=deepcopy(x=node)),
                    ),
                ),
            ]

    def _field_patches(
        self,
        *,
        node: AST,
        state: _Node,
        replacements: list[Patch],
    ) -> list[Patch]:
        """Collect field-level patches, dispatching on each field kind.

        Args:
            node: The node examined while collect field-level patches,
                dispatching on each field kind.
            replacements: Replacements supplied as list[Patch] for this
                operation.
            state: State supplied as _Node for this operation.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if isinstance(node, FormattedValue):
            debug: Patch | None = self._debug_fstring_patch(
                node=node,
                replacements=replacements,
            )
            if debug is not None:
                return [debug]
        patches: list[Patch] = []
        for name, value in iter_fields(node=node):
            previous: _Field | None = state.fields.get(name)
            if previous is None:
                msg: str = "AST field layout changed."
                raise FormatPreservationError(msg)
            annotation: list[Patch] | None = self._annotation_patches(
                node=node,
                name=name,
                value=value,
                previous=previous,
            )
            if annotation is not None:
                patches.extend(annotation)
                continue
            if previous.kind == "scalar":
                if repr(value) != previous.value:
                    patches.append(
                        self._scalar_patch(
                            node=node,
                            name=name,
                            old=previous,
                        ),
                    )
            elif previous.kind == "child":
                patches.extend(
                    self._child_patches(
                        node=node,
                        name=name,
                        value=value,
                        old=previous,
                        replacements=replacements,
                    ),
                )
            else:
                patches.extend(
                    self._children_patches(
                        node=node,
                        name=name,
                        value=value,
                        old=previous,
                        replacements=replacements,
                    ),
                )
        return patches

    def _annotation_patches(
        self,
        *,
        node: AST,
        name: str,
        value: AST | list[AST] | tuple[AST, ...] | str | float | bool | None,
        previous: _Field,
    ) -> list[Patch] | None:
        """Add or remove a return or parameter annotation in place.

        Args:
            node: Node whose field changed.
            name: Field name.
            value: Current field value.
            previous: Original snapshot of the field.

        Returns:
            Patches, or ``None`` when the field is not an annotation that was
            added or removed, so the generic rules apply.

        """
        if isinstance(node, (FunctionDef, AsyncFunctionDef)) and (
            name == "returns"
        ):
            return self._return_patches(
                node=node,
                value=value,
                previous=previous,
            )
        if isinstance(node, arg) and name == "annotation":
            return self._parameter_patches(
                node=node,
                value=value,
                previous=previous,
            )
        return None

    def _header_marks(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
    ) -> tuple[int, int]:
        """Locate the end of a parameter list and the header's colon.

        Brackets of type parameters and of the return annotation are skipped,
        so only the delimiters that belong to the header itself are found.

        Args:
            node: Function definition.

        Returns:
            The absolute end of the closing parenthesis and the absolute start
            of the colon that ends the header.

        Raises:
            FormatPreservationError: If the header cannot be located.

        """
        state: _Node = self.nodes[id(node)]
        if state.start is None or state.end is None:
            msg: str = "The function has no original lexical header."
            raise FormatPreservationError(msg)
        depth: int = 0
        opened: bool = False
        close_end: int | None = None
        for _kind, spelling, left, right in self._tokens(
            start=state.start,
            end=state.end,
        ):
            if spelling in ("(", "[", "{"):
                if spelling == "(" and depth == 0 and close_end is None:
                    opened = True
                depth += 1
            elif spelling in (")", "]", "}"):
                depth -= 1
                if depth == 0 and opened and close_end is None:
                    close_end = right
            elif spelling == ":" and depth == 0 and close_end is not None:
                return close_end, left
        msg = "Cannot locate the original function header delimiters."
        raise FormatPreservationError(msg)

    def _return_patches(
        self,
        *,
        node: FunctionDef | AsyncFunctionDef,
        value: AST | list[AST] | tuple[AST, ...] | str | float | bool | None,
        previous: _Field,
    ) -> list[Patch] | None:
        """Insert or delete ``-> annotation`` after the parameter list.

        Args:
            node: Function definition.
            value: Current ``returns`` value.
            previous: Original snapshot of the field.

        Returns:
            Patches, or ``None`` when the annotation was neither added nor
            removed.

        Raises:
            FormatPreservationError: If a comment sits in the removed span.

        """
        if previous.kind == "scalar" and isinstance(value, AST):
            close_end, _colon = self._header_marks(node=node)
            text: str = f" -> {self._render_annotation(value=value)}"
            return [Patch(start=close_end, end=close_end, text=text)]
        if previous.kind == "child" and value is None:
            close_end, colon = self._header_marks(node=node)
            if self._has_inner_comments(start=close_end, end=colon):
                msg: str = (
                    "A comment inside the return annotation would be lost."
                )
                raise FormatPreservationError(msg)
            return [Patch(start=close_end, end=colon, text="")]
        return None

    def _default_end(self, *, position: int) -> int | None:
        """Find where a parameter's ``= default`` marker ends.

        Args:
            position: Absolute end of the parameter name or annotation.

        Returns:
            The index after the ``=`` and the spaces following it, or ``None``
            when the parameter has no default.

        """
        index: int = position
        while index < len(self.source) and self.source[index] in " \t":
            index += 1
        if not self.source.startswith("=", index) or self.source.startswith(
            "==",
            index,
        ):
            return None
        index += 1
        while index < len(self.source) and self.source[index] in " \t":
            index += 1
        return index

    def _reject_lambda_parameter(self, *, node: arg) -> None:
        """Refuse to annotate a lambda parameter.

        Args:
            node: Parameter being annotated.

        Raises:
            FormatPreservationError: If the parameter belongs to a lambda.

        """
        container: AST | None = self._node_by_id.get(
            self.parents.get(id(node), -1),
        )
        owner: AST | None = (
            None
            if container is None
            else self._node_by_id.get(self.parents.get(id(container), -1))
        )
        if isinstance(owner, Lambda):
            msg: str = "A lambda parameter cannot be annotated."
            raise FormatPreservationError(msg, recoverable=False)

    def _parameter_patches(
        self,
        *,
        node: arg,
        value: AST | list[AST] | tuple[AST, ...] | str | float | bool | None,
        previous: _Field,
    ) -> list[Patch] | None:
        """Insert or delete ``: annotation`` on a parameter.

        A parameter with a default is written ``name: type = default`` when
        annotated and ``name=default`` when not, matching common style.

        Args:
            node: Parameter.
            value: Current ``annotation`` value.
            previous: Original snapshot of the field.

        Returns:
            Patches, or ``None`` when the annotation was neither added nor
            removed.

        Raises:
            FormatPreservationError: If the parameter has no lexical span or a
                comment sits in the removed annotation.

        """
        state: _Node = self.nodes[id(node)]
        if state.start is None or state.end is None:
            msg: str = "The parameter has no original lexical span."
            raise FormatPreservationError(msg)
        if previous.kind == "scalar" and isinstance(value, AST):
            self._reject_lambda_parameter(node=node)
            rendered: str = self._render_annotation(value=value)
            default_end: int | None = self._default_end(position=state.end)
            if default_end is None:
                return [
                    Patch(
                        start=state.end,
                        end=state.end,
                        text=f": {rendered}",
                    ),
                ]
            return [
                Patch(
                    start=state.end,
                    end=default_end,
                    text=f": {rendered} = ",
                ),
            ]
        if previous.kind == "child" and value is None:
            names: list[tuple[int, str, int, int]] = [
                token
                for token in self._tokens(start=state.start, end=state.end)
                if token[0] == NAME
            ]
            if not names:
                msg = "Cannot locate the parameter name."
                raise FormatPreservationError(msg)
            name_end: int = names[0][3]
            if self._has_inner_comments(start=name_end, end=state.end):
                msg = "A comment inside the annotation would be lost."
                raise FormatPreservationError(msg)
            default_end = self._default_end(position=state.end)
            if default_end is None:
                return [Patch(start=name_end, end=state.end, text="")]
            return [Patch(start=name_end, end=default_end, text="=")]
        return None

    def _child_patches(
        self,
        *,
        node: AST,
        name: str,
        value: AST | list[AST] | tuple[AST, ...] | str | float | bool | None,
        old: _Field,
        replacements: list[Patch],
    ) -> list[Patch]:
        """Patch a single-child field by recursion, operator, or rerender.

        Args:
            name: Identifier of the name being resolved.
            node: The node examined while patch a single-child field by
                recursion, operator, or rerender.
            old: Old supplied as _Field for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.
            value: The value examined while patch a single-child field by
                recursion, operator, or rerender.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if isinstance(value, AST) and id(value) == old.ids[0]:
            return self._changed(node=value, replacements=replacements)
        if (
            name == "op"
            and isinstance(
                node,
                (
                    BinOp,
                    UnaryOp,
                    BoolOp,
                    AugAssign,
                ),
            )
            and isinstance(value, AST)
        ):
            return self._operator_patch(node=node, old=old)
        old_child: _Node = self.nodes[old.ids[0]]
        if (
            old_child.start is None
            or old_child.end is None
            or not isinstance(value, AST)
        ):
            msg: str = "Replaced AST field has no concrete source range."
            raise FormatPreservationError(msg)
        rendering: str = (
            self._render_constant(
                value=value.value,
                original=self.source[old_child.start : old_child.end],
            )
            if isinstance(value, Constant)
            else unparse(
                ast_obj=fix_missing_locations(
                    node=deepcopy(x=value),
                ),
            )
        )
        return [
            Patch(
                start=old_child.start,
                end=old_child.end,
                text=rendering,
            ),
        ]

    def _children_patches(
        self,
        *,
        node: AST,
        name: str,
        value: AST | list[AST] | tuple[AST, ...] | str | float | bool | None,
        old: _Field,
        replacements: list[Patch],
    ) -> list[Patch]:
        """Patch a child-list field by alignment or structural rewrite.

        Args:
            name: Identifier of the name being resolved.
            node: The node examined while patch a child-list field by alignment
                or structural rewrite.
            old: Old supplied as _Field for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.
            value: The value examined while patch a child-list field by
                alignment or structural rewrite.

        Returns:
            list[Patch] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        children: list[PatchValue] = list_items(value=value)
        if not isinstance(value, list) or not all(
            isinstance(child, AST) for child in children
        ):
            msg: str = "AST child field changed category."
            raise FormatPreservationError(msg)
        nodes: list[AST] = [
            child for child in children if isinstance(child, AST)
        ]
        current: tuple[int, ...] = tuple(id(child) for child in nodes)
        if current == old.ids:
            return [
                patch
                for child in nodes
                for patch in self._changed(
                    node=child,
                    replacements=replacements,
                )
            ]
        if name == "ops" and isinstance(node, Compare):
            return self._compare_patches(node=node, old=old)
        if name in ("body", "orelse", "finalbody") and all(
            isinstance(child, stmt) for child in nodes
        ):
            return [
                self._replace_suite(
                    original=old.ids,
                    current=[
                        child for child in nodes if isinstance(child, stmt)
                    ],
                    replacements=replacements,
                ),
            ]
        if (
            isinstance(node, arguments)
            and name == "args"
            and all(isinstance(child, arg) for child in nodes)
        ):
            return [
                self._replace_arguments(
                    node=node,
                    original=old.ids,
                    current=[
                        child for child in nodes if isinstance(child, arg)
                    ],
                    replacements=replacements,
                ),
            ]
        msg = f"Changing {type(node).__name__}.{name} "
        "requires syntax regeneration."
        raise FormatPreservationError(msg)

    def _has_inner_comments(self, *, start: int, end: int) -> bool:
        """Check whether a regeneration could discard lexical comments.

        Args:
            end: End identifying a position in the relevant sequence or source.
            start: Start identifying a position in the relevant sequence or
                source.

        Returns:
            Whether the requested condition holds.

        """
        return any(
            token[0] == COMMENT for token in self._tokens(start=start, end=end)
        )

    def _replace_arguments(
        self,
        *,
        node: arguments,
        original: tuple[int, ...],
        current: list[arg],
        replacements: list[Patch],
    ) -> Patch:
        """Preserve comma, quote, and whitespace style in simple signatures.

        Args:
            node: Mutable standard-library function-argument AST container.
            original: Captured identities of positional-or-keyword arguments.
            current: Edited positional-or-keyword argument sequence.
            replacements: Current source-comment text replacements.

        Returns:
            One localized patch of a function's argument-list interior.

        Raises:
            FormatPreservationError: If signature syntax is ambiguous.

        """
        self._require_simple_signature(node=node)
        start, stop = self._parameter_span(node=node)
        if self._has_inner_comments(start=start, end=stop):
            msg: str = (
                "Parameter comments prevent safe comma-list reconstruction."
            )
            raise FormatPreservationError(msg)
        trivia: _ArgumentTrivia = self._argument_trivia(
            original=original,
            start=start,
            stop=stop,
        )
        content: str = self._argument_list_text(
            original=original,
            current=current,
            trivia=trivia,
            replacements=replacements,
        )
        return Patch(start=start, end=stop, text=content)

    def _parameter_span(self, *, node: arguments) -> tuple[int, int]:
        """Locate the interior of the owning function's parentheses.

        Args:
            node: The node examined while locate the interior of the owning
                function's parentheses.

        Returns:
            tuple[int, int] produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        owner_id: int | None = self.parents.get(id(node))
        owner: _Node | None = self.nodes.get(owner_id) if owner_id else None
        if owner is None or owner.start is None or owner.end is None:
            msg: str = "The argument list has no original function header."
            raise FormatPreservationError(msg)
        tokens: list[tuple[int, str, int, int]] = self._tokens(
            start=owner.start,
            end=owner.end,
        )
        start: int | None = None
        stop: int | None = None
        depth: int = 0
        for _kind, spelling, left, right in tokens:
            if spelling == "(" and start is None:
                start = right
                depth = 1
                continue
            if start is None:
                continue
            if spelling in ("(", "[", "{"):
                depth += 1
            elif spelling in (")", "]", "}"):
                depth -= 1
                if depth == 0:
                    stop = left
                    break
        if start is None or stop is None:
            msg = "Cannot locate the original balanced parameter delimiters."
            raise FormatPreservationError(msg)
        return start, stop

    def _argument_trivia(
        self,
        *,
        original: tuple[int, ...],
        start: int,
        stop: int,
    ) -> _ArgumentTrivia:
        """Recover the prefix, suffix, and separator around original args.

        Args:
            original: Original supplied as tuple[int, ...] for this operation.
            start: Start identifying a position in the relevant sequence or
                source.
            stop: Stop supplied as int for this operation.

        Returns:
            _ArgumentTrivia produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        positions: list[_Node] = [
            self.nodes[identity] for identity in original
        ]
        if any(info.start is None or info.end is None for info in positions):
            msg: str = (
                "One or more original arguments have no lexical source span."
            )
            raise FormatPreservationError(msg)
        if not positions:
            return _ArgumentTrivia(
                prefix=self.source[start:stop],
                suffix="",
                separator=", ",
            )
        first: int | None = positions[0].start
        last: int | None = positions[-1].end
        if first is None or last is None:
            msg = "Original argument span is incomplete."
            raise FormatPreservationError(msg)
        separators: list[str] = [
            self.source[before.end : after.start]
            for before, after in pairwise(positions)
            if before.end is not None and after.start is not None
        ]
        separator: str = separators[0] if separators else ", "
        if not separator.strip().startswith(","):
            msg = "Original parameter separators cannot be inferred."
            raise FormatPreservationError(msg)
        return _ArgumentTrivia(
            prefix=self.source[start:first],
            suffix=self.source[last:stop],
            separator=separator,
        )

    def _argument_list_text(
        self,
        *,
        original: tuple[int, ...],
        current: list[arg],
        trivia: _ArgumentTrivia,
        replacements: list[Patch],
    ) -> str:
        """Build the replacement text between the parameter delimiters.

        Args:
            current: Current supplied as list[arg] for this operation.
            original: Original supplied as tuple[int, ...] for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.
            trivia: Trivia supplied as _ArgumentTrivia for this operation.

        Returns:
            str produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if not current:
            if original and (
                trivia.prefix.strip() or trivia.suffix.strip() not in ("", ",")
            ):
                msg: str = (
                    "Removing all arguments would leave ambiguous punctuation."
                )
                raise FormatPreservationError(msg)
            return trivia.prefix if not original else ""
        chunks: list[str] = [
            self._render_argument(
                argument=argument,
                replacements=replacements,
            )
            for argument in current
        ]
        return trivia.prefix + trivia.separator.join(chunks) + trivia.suffix

    def _render_argument(
        self,
        *,
        argument: arg,
        replacements: list[Patch],
    ) -> str:
        """Render one argument, patching its original span when available.

        Args:
            argument: Argument supplied as arg for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        """
        original_arg: _Node | None = self.nodes.get(id(argument))
        if (
            original_arg is not None
            and original_arg.start is not None
            and original_arg.end is not None
        ):
            return self.apply(
                source=self.source,
                begin=original_arg.start,
                end=original_arg.end,
                patches=self._changed(
                    node=argument,
                    replacements=replacements,
                ),
            )
        return unparse(
            ast_obj=fix_missing_locations(
                node=deepcopy(x=argument),
            ),
        )

    def _replace_suite(
        self,
        *,
        original: tuple[int, ...],
        current: list[stmt],
        replacements: list[Patch],
    ) -> Patch:
        """Reorder or replace a nested statement sequence in its span.

        Args:
            current: Current supplied as list[stmt] for this operation.
            original: Original supplied as tuple[int, ...] for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Returns:
            Patch produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        if not original:
            msg: str = (
                "Cannot place new statements in a previously empty suite."
            )
            raise FormatPreservationError(msg)
        first: _Node = self.nodes[original[0]]
        last: _Node = self.nodes[original[-1]]
        if first.line_start is None or last.line_end is None:
            msg = "The original suite lacks complete source coordinates."
            raise FormatPreservationError(msg)
        return Patch(
            start=first.line_start,
            end=last.line_end,
            text=self._emit_statements(
                body=current,
                nested=True,
                replacements=replacements,
                target_indent=first.indent,
            ),
        )

    def _render_stmt(
        self,
        *,
        node: stmt,
        indent: str,
        replacements: list[Patch],
    ) -> str:
        """Render a moved or modified statement, keeping its trivia.

        Args:
            indent: Indent supplied as str for this operation.
            node: The node examined while render a moved or modified statement,
                keeping its trivia.
            replacements: Replacements supplied as list[Patch] for this
                operation.

        Returns:
            Rendered source text produced by this operation.

        Raises:
            FormatPreservationError: If this operation cannot satisfy its
                documented contract.

        """
        state: _Node | None = self.nodes.get(id(node))
        if state is None:
            generated: str = unparse(
                ast_obj=fix_missing_locations(
                    node=deepcopy(x=node),
                ),
            )
            return "".join(
                indent + line + self.newline for line in generated.splitlines()
            )
        if state.line_start is None or state.line_end is None:
            msg: str = "Original statement location is incomplete."
            raise FormatPreservationError(msg)
        if self._is_shared_line(node=node):
            msg = "Moving same-line semicolon statements is ambiguous."
            raise FormatPreservationError(msg)
        edits: list[Patch] = self._changed(
            node=node,
            replacements=replacements,
        )
        edits.extend(
            patch
            for patch in replacements
            if state.line_start <= patch.start and patch.end <= state.line_end
        )
        rendered: str = self.apply(
            source=self.source,
            begin=state.line_start,
            end=state.line_end,
            patches=edits,
        )
        if indent != state.indent:
            rendered = self._reindent(
                source=rendered,
                old=state.indent,
                new=indent,
            )
        return rendered

    def _is_shared_line(self, *, node: stmt) -> bool:
        """Detect original statements sharing a physical source line.

        Args:
            node: The node examined while detect original statements sharing a
                physical source line.

        Returns:
            Whether the requested condition holds.

        """
        state: _Node = self.nodes[id(node)]
        if state.line_start is None or state.line_end is None:
            return False
        return (
            self._shared_line_counts.get(
                (state.line_start, state.line_end),
                0,
            )
            > 1
        )

    def _emit_statements(
        self,
        *,
        body: list[stmt],
        nested: bool,
        replacements: list[Patch],
        target_indent: str = "",
    ) -> str:
        """Join original statements in identity order with their trivia.

        Args:
            body: Body supplied as list[stmt] for this operation.
            nested: Nested supplied as bool for this operation.
            replacements: Replacements supplied as list[Patch] for this
                operation.
            target_indent: Target indent supplied as str for this operation.

        Returns:
            str produced by this operation.

        """
        if nested:
            original_indent: str = target_indent
            base: str = ""
        else:
            original_indent = ""
            base = self.apply(
                source=self.source,
                begin=0,
                end=len(self.first_prefix),
                patches=[
                    patch
                    for patch in replacements
                    if patch.end <= len(self.first_prefix)
                ],
            )
        parts: list[str] = [base]
        tail: str = base
        for node in body:
            leading: str = self.leading.get(id(node), "")
            if tail and not tail.endswith(
                (
                    """\

""",
                    "\r",
                ),
            ):
                leading = self.newline + leading
            rendered: str = self._render_stmt(
                node=node,
                indent=original_indent,
                replacements=replacements,
            )
            parts.extend((leading, rendered))
            tail = rendered or leading or tail
        if not nested:
            beginning: int = len(self.source) - len(self.footer)
            parts.append(
                self.apply(
                    source=self.source,
                    begin=beginning,
                    end=len(self.source),
                    patches=[
                        patch
                        for patch in replacements
                        if patch.start >= beginning
                    ],
                ),
            )
        return "".join(parts)


def preserve_docstring_content(
    *,
    original: str,
    old_summary: str,
    new_summary: str,
    old_description: str,
    new_description: str,
) -> str:
    """Apply PEP 257 prose edits without normalizing original indentation.

    Args:
        original: Exact string value before structured edits.
        old_summary: Originally parsed one-line summary.
        new_summary: Current edited summary.
        old_description: Originally parsed normalized prose.
        new_description: Edited prose to interpolate into original layout.

    Returns:
        Updated raw docstring value retaining layout outside changed prose.

    Raises:
        FormatPreservationError: If text locations are ambiguous.

    """
    if (
        """\

"""
        in new_summary
        or "\r" in new_summary
    ):
        msg: str = "Docstring summary must occupy one physical line."
        raise FormatPreservationError(msg)
    lines: list[str] = original.splitlines(keepends=True)
    if not lines:
        if old_summary:
            msg = "Original summary text has no lexical representation."
            raise FormatPreservationError(msg)
        return new_summary
    first: int = next(
        (index for index, line in enumerate(iterable=lines) if line.strip()),
        -1,
    )
    if first < 0 or lines[first].strip() != old_summary:
        msg = "Original docstring summary has no unique source location."
        raise FormatPreservationError(msg)
    previous: str = lines[first]
    content: str = previous.rstrip("""\
\r
""")
    left: str = content[: len(content) - len(content.lstrip(" \t"))]
    right: str = previous[len(content) :]
    lines[first] = left + new_summary + right
    if old_description == new_description:
        return "".join(lines)
    if not old_description:
        msg = "Inserting new prose without a source anchor is ambiguous."
        raise FormatPreservationError(msg)
    description: list[str] = old_description.splitlines()
    matches: list[int] = [
        index
        for index in range(first + 1, len(lines) - len(description) + 1)
        if all(
            lines[index + offset].strip() == raw.strip()
            for offset, raw in enumerate(iterable=description)
        )
    ]
    if len(matches) != 1:
        msg = "Original docstring description does not have a unique span."
        raise FormatPreservationError(msg)
    begin: int = matches[0]
    sample: str = lines[begin]
    indent: str = sample[: len(sample) - len(sample.lstrip(" \t"))]
    ending: str = (
        """\
\r
"""
        if """\
\r
"""
        in sample
        else """\

"""
        if """\

"""
        in sample
        else ""
    )
    replacement: list[str] = [
        indent + text + ending if text else ending
        for text in new_description.splitlines()
    ]
    lines[begin : begin + len(description)] = replacement
    return "".join(lines)
