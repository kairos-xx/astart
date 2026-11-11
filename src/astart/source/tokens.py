"""Immutable lexical snapshots for mutable, comment-aware Python AST nodes.

Each snapshot is computed on demand from the *current emitted source*, never
updated in place. This deliberately detects in-place edits of AST child lists.

"""

from __future__ import annotations

from ast import (
    AST,
    Add,
    And,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    Compare,
    Div,
    Eq,
    FloorDiv,
    Gt,
    GtE,
    In,
    Invert,
    Is,
    IsNot,
    LShift,
    Lt,
    LtE,
    MatMult,
    Mod,
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
    boolop,
    cmpop,
    expr_context,
    iter_fields,
    operator,
    unaryop,
)
from bisect import bisect_left, bisect_right
from copy import copy
from dataclasses import dataclass
from io import StringIO
from tokenize import COMMENT, NL, OP, generate_tokens
from typing import (
    TYPE_CHECKING,
    Final,
    Protocol,
    cast,
    final,
    runtime_checkable,
)

from astart.source.node_attributes import list_items

if TYPE_CHECKING:
    from weakref import ReferenceType


@final
class Constants:
    """Group module-level constants.

    Attributes:
        operator_symbols (Final[dict[type[AST], str]]): Grouped module
            constant.
        delimiters (Final[dict[str, str]]): Matching Python punctuation,
            excluding string contents.
        isolated_node_attr (Final[str]): Grouped module constant.

    """

    delimiters: Final[dict[str, str]] = {"(": ")", "[": "]", "{": "}"}
    operator_symbols: Final[dict[type[AST], str]] = {
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

    isolated_node_attr: Final[str] = "_astart_isolated"


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class SourceSpan:
    """Inclusive start and exclusive end, using Python AST UTF-8 columns.

    Attributes:
        start_line (int): One-based starting line.
        start_column (int): Zero-based starting UTF-8 byte column.
        end_line (int): One-based ending line.
        end_column (int): Zero-based exclusive ending UTF-8 byte column.

    """

    start_line: int
    start_column: int
    end_line: int
    end_column: int


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class LexicalToken:
    """Frozen copy of the complete relevant ``tokenize.TokenInfo`` record.

    Attributes:
        type (int): Python tokenizer integer token kind.
        exact_type (int): Exact operator type, when different from ``type``.
        string (str): Token spelling, exactly as emitted.
        start (tuple[int, int]): TokenInfo starting (line, character column).
        end (tuple[int, int]): TokenInfo exclusive ending (line, character
            column).
        line (str): Original physical source line returned by the tokenizer.
        start_byte_column (int): Starting UTF-8 byte column.
        end_byte_column (int): Exclusive ending UTF-8 byte column.
        index (int): Token position in the complete tokenizer stream.

    """

    type: int
    exact_type: int
    string: str
    start: tuple[int, int]
    end: tuple[int, int]
    line: str
    start_byte_column: int
    end_byte_column: int
    index: int


@final
@dataclass(frozen=True, slots=True, kw_only=True)
class TokenSnapshot:
    """Immutable, versioned lexical information for one mutable AST node.

    Attributes:
        tokens (tuple[LexicalToken, ...]): Python tokens covering the node or
            inherited host source span.
        span (SourceSpan): Span in the regenerated source, using UTF-8 byte
            columns.
        source_text (str): Literal source covered by ``span`` , including
            whitespace.
        source_revision (int): Monotonically increasing source-tokenization
            revision.
        provenance (str): Own source tokens, inherited parent tokens, or
            synthetic.

    """

    tokens: tuple[LexicalToken, ...]
    span: SourceSpan
    source_text: str
    source_revision: int
    provenance: str


class TokenProvider(Protocol):
    """Interface for lazily retrieving immutable tokenized node snapshots."""

    def token_snapshot(self, *, node: AST) -> TokenSnapshot:
        """Get synchronized information for one AST node.

        Args:
            node (AST): Owned executable or semantic AST node.

        Returns:
            Frozen token snapshot describing the current emitted source.

        """
        ...


@runtime_checkable
class LocatedAST(Protocol):
    """Precise structural interface for nodes with complete AST locations.

    Attributes:
        lineno (int): One-based source line.
        col_offset (int): Starting UTF-8 byte column.
        end_lineno (int | None): Optional ending line.
        end_col_offset (int | None): Optional exclusive ending UTF-8 byte
            column.

    """

    lineno: int
    col_offset: int
    end_lineno: int | None
    end_col_offset: int | None


class TokenAwareMixin(AST):
    """AST-compatible lexical properties supplied by the host module.

    The original ``ast`` node fields remain mutable. Accessing these
    properties checks the whole host tree, including in-place list changes,
    then requests a new immutable snapshot when necessary.

    Attributes:
        token_provider (ReferenceType[TokenProvider]): Weak owner reference,
            attached during parsing.

    """

    token_provider: ReferenceType[TokenProvider]

    @property
    def token_info(self) -> TokenSnapshot:
        """Get a current frozen lexical snapshot, rebuilding if necessary.

        Returns:
            TokenSnapshot: Snapshot for this AST node.

        Raises:
            ReferenceError: If the module owning this node was destroyed.
            ValueError: If edited source cannot be safely regenerated.

        """
        provider: TokenProvider | None = self.token_provider()
        if provider is None:
            msg: str = "The AST node's lexical owner no longer exists."
            raise ReferenceError(msg)
        return provider.token_snapshot(node=self)

    @property
    def tokens(self) -> tuple[LexicalToken, ...]:
        """Return token information without permitting token mutations.

        Returns:
            tuple[LexicalToken, ...]: tuple[LexicalToken, ...] produced by this
                operation.

        """
        return self.token_info.tokens

    @property
    def token_span(self) -> SourceSpan:
        """Return current source coordinates, independent of AST fields.

        Returns:
            SourceSpan: SourceSpan produced by this operation.

        """
        return self.token_info.span

    @property
    def token_text(self) -> str:
        """Return exact source text covering this node's current span.

        Returns:
            str: Rendered source text produced by this operation.

        """
        return self.token_info.source_text


@final
class SourceTokenizer:
    """Tokenize one source revision and produce frozen source-level snapshots.

    Attributes:
        source: Source text for this revision.
        revision: Monotonic version of the host module.
        tokens: Full immutable Python tokenizer stream.

    """

    def __init__(self, *, source: str, revision: int) -> None:
        """Tokenize a complete current source representation.

        Args:
            source (str): Current parseable Python source.
            revision (int): Host module generation number.

        Raises:
            tokenize.TokenError: If source tokenization fails.

        """
        self.source: str = source
        self.revision: int = revision
        self.lines: list[str] = source.splitlines(keepends=True)
        self.tokens: tuple[LexicalToken, ...] = tuple(
            (
                LexicalToken(
                    type=token.type,
                    exact_type=token.exact_type,
                    string=token.string,
                    start=token.start,
                    end=token.end,
                    line=token.line,
                    start_byte_column=len(
                        token.line[: token.start[1]].encode(encoding="utf-8"),
                    ),
                    end_byte_column=len(
                        token.line[: token.end[1]].encode(encoding="utf-8"),
                    )
                    if token.start[0] == token.end[0]
                    else len(
                        self.lines[token.end[0] - 1][: token.end[1]].encode(
                            encoding="utf-8",
                        ),
                    )
                    if 0 < token.end[0] <= len(self.lines)
                    else 0,
                    index=index,
                )
                for index, token in enumerate(
                    iterable=generate_tokens(
                        readline=StringIO(initial_value=source).readline,
                    ),
                )
            ),
        )
        self._starts: tuple[tuple[int, int], ...] = tuple(
            (token.start[0], token.start_byte_column) for token in self.tokens
        )
        self._pairs: dict[int, int] = {}
        self._index_delimiters()

    def _index_delimiters(self) -> None:
        """Index balanced punctuation once, ignoring comments and strings."""
        stack: list[LexicalToken] = []
        for token in self.tokens:
            if token.type != OP:
                continue
            if token.string in Constants.delimiters:
                stack.append(token)
            elif token.string in Constants.delimiters.values() and stack:
                opening: LexicalToken = stack[-1]
                if Constants.delimiters[opening.string] == token.string:
                    stack.pop()
                    self._pairs[opening.index] = token.index
                    self._pairs[token.index] = opening.index

    def matching_delimiter(self, *, token_index: int) -> LexicalToken | None:
        """Find a punctuation partner in constant time in this revision.

        Args:
            token_index (int): Index of an opening or closing lexical token.

        Returns:
            LexicalToken | None:
                Its partner, or None for non-delimiters and unknown indices.

        """
        partner: int | None = self._pairs.get(token_index)
        return self.tokens[partner] if partner is not None else None

    def parenthesized_span(self, *, node: AST) -> SourceSpan | None:
        """Include redundant parentheses omitted by Python AST positions.

        Comments and continuation newlines inside parentheses are retained.
        This is a lexical range, not a claim that the parentheses are
        redundant. Callers use the parent AST to establish syntactic ownership.

        Args:
            node (AST): Located expression from this source revision.

        Returns:
            SourceSpan | None:
                Its maximal immediately enclosing parenthesized source span.

        """
        span: SourceSpan | None = self.span_of(node=node)
        if span is None:
            return None
        left: int = (
            bisect_left(
                a=self._starts,
                x=(span.start_line, span.start_column),
            )
            - 1
        )
        right: int = bisect_left(
            a=self._starts,
            x=(span.end_line, span.end_column),
        )
        while left >= 0 and right < len(self.tokens):
            if self.tokens[left].type in (COMMENT, NL):
                left -= 1
                continue
            if self.tokens[right].type in (COMMENT, NL):
                right += 1
                continue
            opening: LexicalToken = self.tokens[left]
            closing: LexicalToken = self.tokens[right]
            if opening.string != "(" or self._pairs.get(left) != right:
                break
            span = SourceSpan(
                start_line=opening.start[0],
                start_column=opening.start_byte_column,
                end_line=closing.end[0],
                end_column=closing.end_byte_column,
            )
            left -= 1
            right += 1
        return span

    @property
    def full_span(self) -> SourceSpan:
        """Return the complete emitted source location.

        Returns:
            SourceSpan: SourceSpan produced by this operation.

        """
        return SourceSpan(
            start_line=1,
            start_column=0,
            end_line=max(1, len(self.lines)),
            end_column=len(self.lines[-1].encode(encoding="utf-8"))
            if self.lines
            else 0,
        )

    @staticmethod
    def span_of(*, node: AST) -> SourceSpan | None:
        """Get source coordinates from AST location attributes when complete.

        Args:
            node (AST): Executable AST node with optional location attributes.

        Returns:
            SourceSpan | None:
                UTF-8 position or None for location-less structural nodes.

        """
        if not all(
            hasattr(node, field)
            for field in (
                "lineno",
                "col_offset",
                "end_lineno",
                "end_col_offset",
            )
        ):
            return None
        located: LocatedAST = cast(typ="LocatedAST", val=node)
        start_line: int = located.lineno
        start_col: int = located.col_offset
        end_line: int | None = located.end_lineno
        end_col: int | None = located.end_col_offset
        if end_line is None or end_col is None:
            return None
        return SourceSpan(
            start_line=start_line,
            start_column=start_col,
            end_line=end_line,
            end_column=end_col,
        )

    def snapshot(
        self,
        *,
        span: SourceSpan,
        provenance: str = "own",
    ) -> TokenSnapshot:
        """Create an immutable lexical snapshot for the specified source range.

        Args:
            span (SourceSpan): Source range in UTF-8 byte coordinates.
            provenance (str): Whether the node owns or inherits the range.

        Returns:
            TokenSnapshot:
                Immutable tokens and exact source slice covering the range.

        """
        start: tuple[int, int] = (span.start_line, span.start_column)
        end: tuple[int, int] = (span.end_line, span.end_column)
        selected: tuple[LexicalToken, ...] = tuple(
            token
            for token in self.tokens[
                bisect_left(a=self._starts, x=start) : bisect_right(
                    a=self._starts,
                    x=end,
                )
            ]
            if token.type != 0
            and (token.end[0], token.end_byte_column) <= end
            and (
                (token.start[0], token.start_byte_column)
                != (token.end[0], token.end_byte_column)
            )
        )
        return TokenSnapshot(
            tokens=selected,
            span=span,
            source_text=self._slice(span=span),
            source_revision=self.revision,
            provenance=provenance,
        )

    def operator_span(
        self,
        *,
        parent: AST,
        field: str,
        index: int = 0,
    ) -> SourceSpan | None:
        """Locate a specific operator AST node with no native source locations.

        Args:
            parent (AST): Current parsed expression owning the operator.
            field (str): Name of the operator-bearing field.
            index (int): Index within the comparison-operator sequence.

        Returns:
            SourceSpan | None:
                Precise operator-only UTF-8 span, if unambiguous.

        """
        bounds: tuple[tuple[int, int], tuple[int, int], AST] | None = (
            self._operator_bounds(parent=parent, field=field, index=index)
        )
        if bounds is None:
            return None
        start, end, operation = bounds
        symbol: str | None = next(
            (
                text
                for kind, text in Constants.operator_symbols.items()
                if isinstance(operation, kind)
            ),
            None,
        )
        if symbol is None:
            return None
        if isinstance(parent, AugAssign):
            symbol += "="
        candidates: list[LexicalToken] = [
            token
            for token in self.tokens[
                bisect_left(a=self._starts, x=start) : bisect_right(
                    a=self._starts,
                    x=end,
                )
            ]
            if (token.end[0], token.end_byte_column) <= end
            and token.type not in (COMMENT, NL)
        ]
        words: list[str] = symbol.split()
        matching: list[list[LexicalToken]] = [
            candidates[position : position + len(words)]
            for position in range(len(candidates) - len(words) + 1)
            if [
                token.string
                for token in candidates[position : position + len(words)]
            ]
            == words
        ]
        if len(matching) != 1:
            return None
        first: LexicalToken = matching[0][0]
        last: LexicalToken = matching[0][-1]
        return SourceSpan(
            start_line=first.start[0],
            start_column=first.start_byte_column,
            end_line=last.end[0],
            end_column=last.end_byte_column,
        )

    def snapshot_cached(
        self,
        *,
        span: SourceSpan,
        previous: TokenSnapshot | None,
        provenance: str = "own",
    ) -> TokenSnapshot:
        """Reuse a frozen node snapshot only if all lexical metadata is stable.

        Args:
            span (SourceSpan): Source coordinates inferred from the validated
                new AST.
            previous (TokenSnapshot | None): The same mutable node's preceding
                immutable snapshot.
            provenance (str): Whether the node owns these tokens or inherits
                them.

        Returns:
            TokenSnapshot: The exact previous object when
                unchanged, or a current snapshot.

        """
        if (
            previous is not None
            and previous.span == span
            and (previous.provenance == provenance)
            and (previous.source_text == self._slice(span=span))
            and (
                not previous.tokens
                or (
                    previous.tokens[0].index < len(self.tokens)
                    and previous.tokens[-1].index < len(self.tokens)
                    and (
                        self.tokens[previous.tokens[0].index]
                        == previous.tokens[0]
                    )
                    and (
                        self.tokens[previous.tokens[-1].index]
                        == previous.tokens[-1]
                    )
                )
            )
        ):
            return previous
        return self.snapshot(span=span, provenance=provenance)

    def _slice(self, *, span: SourceSpan) -> str:
        """Extract exact UTF-8 byte source span without lossy char offsets.

        Args:
            span (SourceSpan): Inclusive/exclusive UTF-8 source range.

        Returns:
            str: Decoded source slice at the requested location.

        """
        if not self.lines:
            return ""
        if not 1 <= span.start_line <= span.end_line <= len(self.lines):
            return ""
        chunks: list[bytes] = [
            line.encode(encoding="utf-8")
            for line in self.lines[span.start_line - 1 : span.end_line]
        ]
        if len(chunks) == 1:
            return chunks[0][span.start_column : span.end_column].decode(
                encoding="utf-8",
            )
        chunks[0] = chunks[0][span.start_column :]
        chunks[-1] = chunks[-1][: span.end_column]
        return b"".join(chunks).decode(encoding="utf-8")

    def _operator_bounds(
        self,
        *,
        parent: AST,
        field: str,
        index: int,
    ) -> tuple[tuple[int, int], tuple[int, int], AST] | None:
        """Locate the lexical gap and operation for a supported operator.

        Args:
            field (str): Field supplied as str for this operation.
            index (int): Index identifying a position in
                the relevant sequence or source.
            parent (AST): Parent supplied as AST for this operation.

        Returns:
            tuple[tuple[int, int], tuple[int, int], AST] | None:
                tuple[tuple[int, int], tuple[int, int],
                AST] | None produced by this operation.

        """
        if field == "op" and isinstance(parent, UnaryOp):
            outer: SourceSpan | None = self.span_of(node=parent)
            operand: SourceSpan | None = self.span_of(node=parent.operand)
            if outer is None or operand is None:
                return None
            return (
                (outer.start_line, outer.start_column),
                (operand.start_line, operand.start_column),
                parent.op,
            )
        if field == "op" and isinstance(parent, (BinOp, AugAssign)):
            left: AST = (
                parent.left if isinstance(parent, BinOp) else parent.target
            )
            right: AST = (
                parent.right if isinstance(parent, BinOp) else parent.value
            )
            operation: AST = parent.op
        elif field == "ops" and isinstance(parent, Compare):
            if index >= len(parent.ops):
                return None
            operands: list[AST] = [parent.left, *parent.comparators]
            left, right, operation = (
                operands[index],
                operands[index + 1],
                parent.ops[index],
            )
        else:
            return None
        preceding: SourceSpan | None = self.span_of(node=left)
        following: SourceSpan | None = self.span_of(node=right)
        if preceding is None or following is None:
            return None
        return (
            (preceding.end_line, preceding.end_column),
            (following.start_line, following.start_column),
            operation,
        )


def _unique_ast_child(*, child: AST, seen: set[int]) -> AST:
    """Clone interned nodes and reject ambiguous executable aliases.

    CPython interns operator and context nodes process-wide: the same
    ``Mod``/``Load`` instance is shared by every ``ast.parse`` call, so
    the canonical object must never stay in a bound tree — mutating its
    class would leak into unrelated parses. Operator and context singletons
    are therefore cloned on every occurrence. Every clone
    is marked so repeated isolation passes keep stable node identities.

    Args:
        child (AST): AST node to register.
        seen (set[int]): Identities already encountered in the traversal.

    Returns:
        AST: Original or independently cloned AST node.

    Raises:
        TypeError: If an executable AST node is shared between locations.

    """
    if getattr(child, Constants.isolated_node_attr, False):
        if id(child) not in seen:
            seen.add(id(child))
            return child
    elif isinstance(child, (operator, unaryop, boolop, cmpop, expr_context)):
        pass
    elif id(child) not in seen:
        seen.add(id(child))
        return child
    elif not isinstance(child, expr_context):
        msg: str = (
            "One AST node instance cannot occupy multiple source locations; "
            "clone it before inserting it twice."
        )
        raise TypeError(msg)
    cloned: AST = copy(x=child)
    setattr(cloned, Constants.isolated_node_attr, True)
    seen.add(id(cloned))
    return cloned


def isolate_shared_ast_nodes(*, root: AST) -> None:
    """Give shared interned operator and context nodes unique identities.

    CPython shares ``Load``, ``Store`` and operator singletons inside a parse
    result. Without isolation, one object can occupy several source locations,
    so an identity-indexed tokenizer cannot assign correct independent spans.

    Args:
        root (AST): Parsed executable and semantic AST owner.

    Raises:
        TypeError: If a caller reused an executable non-operator node in two
            different places; no unambiguous per-node source span exists.

    """
    seen: set[int] = {id(root)}
    pending: list[AST] = [root]
    while pending:
        owner: AST = pending.pop()
        for field, value in iter_fields(node=owner):
            field_members: list[object] = list_items(value=value)
            if isinstance(value, AST):
                current: AST = _unique_ast_child(child=value, seen=seen)
                if current is not value:
                    setattr(owner, field, current)
                pending.append(current)
            elif isinstance(value, list):
                for index, member in enumerate(iterable=field_members):
                    if not isinstance(member, AST):
                        continue
                    child: AST = _unique_ast_child(child=member, seen=seen)
                    if child is not member:
                        value[index] = child
                    pending.append(child)
