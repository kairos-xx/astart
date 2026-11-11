"""Source-position primitives for graph-based AST editing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Self, final


@final
class Constants:
    """Group module-level constants.

    Attributes:
        min_line (Final[int]): Grouped module constant.
        min_column (Final[int]): Grouped module constant.
        one_column (Final[int]): Grouped module constant.

    """

    min_line: Final[int] = 1
    min_column: Final[int] = 0
    one_column: Final[int] = 1


@dataclass(frozen=True, slots=True, order=True)
class SourcePosition:
    """One-based line and zero-based column position.

    Attributes:
        column (int): Column retained as int by this instance.
        line (int): Line retained as int by this instance.

    """

    line: int
    column: int

    def translated(
        self,
        *,
        origin: SourcePosition,
        target: SourcePosition,
    ) -> Self:
        """Translate this position from one origin to another.

        Args:
            origin (SourcePosition): Origin supplied as SourcePosition for this
                operation.
            target (SourcePosition): The target examined while translate this
                position from one origin to another.

        Returns:
            Self: Self produced by this operation.

        """
        line_delta: int = self.line - origin.line
        column_delta: int = target.column - origin.column
        return self.__class__(
            line=target.line + line_delta,
            column=max(Constants.min_column, self.column + column_delta),
        )

    def shifted(self, *, delta: PositionDelta) -> Self:
        """Return this position shifted by an edit delta.

        Args:
            delta (PositionDelta): Delta supplied as PositionDelta for this
                operation.

        Returns:
            Self: Self produced by this operation.

        """
        if self.line == delta.pivot.line:
            return self.__class__(
                line=self.line + delta.line_delta,
                column=max(
                    Constants.min_column,
                    self.column + delta.column_delta,
                ),
            )
        return self.__class__(
            line=self.line + delta.line_delta,
            column=self.column,
        )

    def __post_init__(self) -> None:
        """Validate line and column values.

        Raises:
            ValueError: TODO.

        """
        if self.line < Constants.min_line:
            msg: str = "line must be one-based and greater than zero."
            raise ValueError(msg)
        if self.column < Constants.min_column:
            msg = "column must be zero-based and non-negative."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Half-open span represented with AST-compatible positions.

    Attributes:
        end (SourcePosition): End retained as SourcePosition by this instance.
        start (SourcePosition): Start retained as SourcePosition by this
            instance.

    """

    start: SourcePosition
    end: SourcePosition

    @classmethod
    def one_column_at(cls, *, position: SourcePosition) -> Self:
        """Create a one-column fallback span.

        Args:
            position (SourcePosition): Position supplied as SourcePosition for
                this operation.

        Returns:
            Self: Self produced by this operation.

        """
        return cls(
            start=position,
            end=SourcePosition(
                line=position.line,
                column=position.column + Constants.one_column,
            ),
        )

    @classmethod
    def from_text(cls, *, start: SourcePosition, text: str) -> Self:
        """Create a span occupied by ``text`` starting at ``start``.

        Args:
            start (SourcePosition): Start identifying a position in
                the relevant sequence or source.
            text (str): Text supplied as str for this operation.

        Returns:
            Self: Self produced by this operation.

        """
        newline_count: int = text.count("\n")
        if newline_count == 0:
            return cls(
                start=start,
                end=SourcePosition(
                    line=start.line,
                    column=start.column + len(text),
                ),
            )
        tail: str = text.rsplit(
            sep="\n",
            maxsplit=1,
        )[-1]
        return cls(
            start=start,
            end=SourcePosition(
                line=start.line + newline_count,
                column=len(tail),
            ),
        )

    @classmethod
    def enclosing(cls, *, spans: tuple[SourceSpan, ...]) -> Self:
        """Return the smallest span enclosing all spans.

        Args:
            spans (tuple[SourceSpan, ...]): Spans supplied as tuple[SourceSpan,
                ...] for this operation.

        Returns:
            Self: Self produced by this operation.

        Raises:
            ValueError: If this operation cannot satisfy its documented
                contract.

        """
        if not spans:
            msg: str = "cannot enclose an empty span collection."
            raise ValueError(msg)
        return cls(
            start=min(span.start for span in spans),
            end=max(span.end for span in spans),
        )

    def contains(self, *, position: SourcePosition) -> bool:
        """Return whether this span contains ``position``.

        Args:
            position (SourcePosition): Position supplied as SourcePosition for
                this operation.

        Returns:
            bool: Whether the requested condition holds.

        """
        return self.start <= position < self.end

    def contains_span(self, *, other: SourceSpan) -> bool:
        """Return whether this span fully contains ``other``.

        Args:
            other (SourceSpan): Other supplied as SourceSpan for this
                operation.

        Returns:
            bool: Whether the requested condition holds.

        """
        return self.start <= other.start and other.end <= self.end

    def intersects(self, *, other: SourceSpan) -> bool:
        """Return whether this span intersects ``other``.

        Args:
            other (SourceSpan): Other supplied as SourceSpan for this
                operation.

        Returns:
            bool: Whether the requested condition holds.

        """
        return not (self.end <= other.start or other.end <= self.start)

    def translated(
        self,
        *,
        origin: SourcePosition,
        target: SourcePosition,
    ) -> Self:
        """Translate this span from one origin to another.

        Args:
            origin (SourcePosition): Origin supplied as SourcePosition for this
                operation.
            target (SourcePosition): The target examined while translate
                this span from one origin to another.

        Returns:
            Self: Self produced by this operation.

        """
        return self.__class__(
            start=self.start.translated(origin=origin, target=target),
            end=self.end.translated(origin=origin, target=target),
        )

    def shifted(self, *, delta: PositionDelta) -> Self:
        """Return this span shifted by an edit delta.

        Args:
            delta (PositionDelta): Delta supplied as PositionDelta for this
                operation.

        Returns:
            Self: Self produced by this operation.

        """
        return self.__class__(
            start=self.start.shifted(delta=delta),
            end=self.end.shifted(delta=delta),
        )

    def __post_init__(self) -> None:
        """Validate that the span is not inverted.

        Raises:
            ValueError: TODO.

        """
        if self.end < self.start:
            msg: str = "span end cannot be before span start."
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class PositionDelta:
    """Source position delta produced by a concrete edit.

    Attributes:
        column_delta (int): Column delta retained as int by this instance.
        line_delta (int): Line delta retained as int by this instance.
        pivot (SourcePosition): Pivot retained as SourcePosition by this
            instance.

    """

    pivot: SourcePosition
    line_delta: int
    column_delta: int

    @classmethod
    def from_replacement(
        cls,
        *,
        old_span: SourceSpan,
        new_span: SourceSpan,
    ) -> Self:
        """Create a delta from replacing ``old_span`` by ``new_span``.

        Args:
            new_span (SourceSpan): New span supplied as SourceSpan for this
                operation.
            old_span (SourceSpan): Old span supplied as SourceSpan for this
                operation.

        Returns:
            Self: Self produced by this operation.

        """
        return cls(
            pivot=old_span.end,
            line_delta=new_span.end.line - old_span.end.line,
            column_delta=new_span.end.column - old_span.end.column,
        )

    def is_zero(self) -> bool:
        """Return whether this delta has no effect.

        Returns:
            bool: Whether the requested condition holds.

        """
        return self.line_delta == 0 and self.column_delta == 0


@dataclass(frozen=True, slots=True)
class LineIndex:
    """Line table for source offset and column conversion.

    Attributes:
        line_start_offsets (tuple[int, ...]): Line start offsets retained as
            tuple[int, ...] by this instance.
        lines (tuple[str, ...]): Lines retained as tuple[str, ...] by this
            instance.
        source (str): Original source text retained for parsing and
            reconstruction.

    """

    source: str
    lines: tuple[str, ...]
    line_start_offsets: tuple[int, ...]

    @classmethod
    def from_source(cls, *, source: str) -> Self:
        """Build a line index from source text.

        Args:
            source (str): The source examined while build a line index from
                source text.

        Returns:
            Self: Self produced by this operation.

        """
        lines: tuple[str, ...] = tuple(source.splitlines(keepends=True))
        offsets: list[int] = []
        current: int = 0
        line: str
        for line in lines:
            offsets.append(current)
            current += len(line)
        if not offsets:
            offsets.append(0)
        return cls(
            source=source,
            lines=lines,
            line_start_offsets=tuple(offsets),
        )

    def position_to_offset(self, *, position: SourcePosition) -> int:
        """Convert a source position to a character offset.

        Args:
            position (SourcePosition): Position supplied as SourcePosition for
                this operation.

        Returns:
            int: int produced by this operation.

        """
        line_index: int = max(0, min(position.line - 1, len(self.lines) - 1))
        line_text: str = self.lines[line_index] if self.lines else ""
        column: int = max(0, min(position.column, len(line_text)))
        return self.line_start_offsets[line_index] + column

    def span_text(self, *, span: SourceSpan) -> str:
        """Return the exact source text covered by ``span``.

        Args:
            span (SourceSpan): Span supplied as SourceSpan for this operation.

        Returns:
            str: Rendered source text produced by this operation.

        """
        start: int = self.position_to_offset(position=span.start)
        end: int = self.position_to_offset(position=span.end)
        return self.source[start:end]
