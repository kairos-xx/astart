"""Balanced paragraph wrapping with protected documentation and list layout."""

from __future__ import annotations

from dataclasses import dataclass
from math import inf
from re import Match, Pattern
from re import compile as compile_pattern
from typing import Final, final


@final
class Constants:
    """Controls for deterministic optimal line breaking.

    Attributes:
        widow (Final[float]): Cost of a final line containing only one word.
        bracket_break (Final[float]): Cost of breaking inside an open bracket
            pair, keeping type
            expressions and grouped prose on one line when possible.
        transition (Final[float]): Cost of jumping between distant spacing
            classes.
        weak (Final[float]): Cost of ending a line after a weak separator.
        strong (Final[float]): Bonus for ending a line at sentence punctuation.
        tight (Final[float]): Tightness threshold relative to available width.
        loose (Final[float]): Looseness threshold relative to available width.
        classes (Final[int]): Number of line-fitness classes.
        tokens (Final[Pattern[str]]): Inline code spans stay indivisible while
            other words split.
        list_item (Final[Pattern[str]]): Bullet and numbered list markers.
        entry (Final[Pattern[str]]): Google-style entry prefix and hanging
            indentation.
        closing_punctuation (Final[str]): TODO.
        opening_punctuation (Final[str]): TODO.
        sentence_endings (Final[str]): TODO.

    """

    widow: Final[float] = 100_000.0
    bracket_break: Final[float] = 200_000.0
    transition: Final[float] = 100.0
    weak: Final[float] = 50.0
    strong: Final[float] = -5.0
    tight: Final[float] = 0.1
    loose: Final[float] = 0.5
    classes: Final[int] = 3
    tokens: Final[Pattern[str]] = compile_pattern(
        pattern=(
            r"``[^`]*``[.,;:!?…)\]}>»]*"
            r"|`[^`]*`[.,;:!?…)\]}>»]*"
            r"|\S+"
        ),
    )
    list_item: Final[Pattern[str]] = compile_pattern(
        pattern=r"^(?P<pad>\s*)(?P<marker>[-*+]|\d+[a-zA-Z]?[.)\]])\s+(?P<body>.*)$",
    )
    entry: Final[Pattern[str]] = compile_pattern(
        pattern=(
            r"^(?P<pad>\s*)(?P<name>[*\w.]+"
            r"(?:\s*\((?:[^()]|\([^()]*\))*\))?):\s+(?P<body>.+)$"
        ),
    )
    closing_punctuation: Final[str] = ".,;:!?…)]}>»"
    opening_punctuation: Final[str] = "([{«"
    sentence_endings: Final[str] = ".!?;:…"


@final
@dataclass(frozen=True, slots=True)
class _Break:
    """Best predecessor for one end position and line-fitness state.

    Attributes:
        cost (float): Accumulated line-breaking cost.
        previous (int): First word of this line.
        fitness (int): Predecessor's spacing class.

    """

    cost: float
    previous: int
    fitness: int


def balanced_lines(*, text: str, width: int) -> list[str]:
    """Find balanced line breaks without splitting words or inline code.

    Unlike a single-state greedy predecessor, the dynamic program retains
    every fitness class at each break, so transition costs remain optimal.
    An indivisible token longer than the width remains intact on its own.

    Args:
        text (str): One paragraph with no structural line boundaries.
        width (int): Available content columns, excluding indentation.

    Returns:
        list[str]: Deterministic lines containing the original ordered tokens.

    Raises:
        ValueError: Width is not positive.

    """
    if width < 1:
        msg: str = "Wrapping width must be positive"
        raise ValueError(msg)

    words: list[str] = Constants.tokens.findall(string=text)
    if not words:
        return []

    depths: list[int] = [0] * (len(words) + 1)
    depth: int = 0
    for index, word in enumerate(iterable=words):
        depths[index] = depth
        depth = max(
            0,
            depth
            + sum(word.count(opening) for opening in "([{")
            - sum(word.count(closing) for closing in ")]}"),
        )

    states: list[list[_Break]] = [
        [_Break(cost=inf, previous=0, fitness=0)] * Constants.classes
        for _ in range(len(words) + 1)
    ]
    states[0][1] = _Break(cost=0.0, previous=0, fitness=1)

    for stop in range(1, len(words) + 1):
        length: int = -1
        for start in range(stop - 1, -1, -1):
            length += len(words[start]) + 1
            if length > width and start < stop - 1:
                break

            remaining: int = max(0, width - length)
            ratio: float = remaining / width
            fitness: int = (
                0
                if ratio < Constants.tight
                else 1
                if ratio < Constants.loose
                else Constants.classes - 1
            )

            cost: float = float(remaining**3)
            cost += Constants.bracket_break * (
                depths[start] > 0
            ) + Constants.widow * (
                stop == len(words) and stop - start == 1 and start > 0
            )

            last: str = words[stop - 1]
            cost += (
                Constants.strong
                if last.endswith((".", "!", "?", ":", ";"))
                else Constants.weak
                if last.endswith(("/", "-", "("))
                else 0
            )

            _relax(
                states=states,
                start=start,
                stop=stop,
                fitness=fitness,
                cost=cost,
            )

    stop: int = len(words)
    fitness = min(
        range(Constants.classes),
        key=lambda index: states[stop][index].cost,
    )

    lines: list[str] = []
    while stop:
        predecessor: _Break = states[stop][fitness]
        lines.append(" ".join(words[predecessor.previous : stop]))
        stop, fitness = predecessor.previous, predecessor.fitness

    return list(reversed(lines))


def _relax(
    *,
    states: list[list[_Break]],
    start: int,
    stop: int,
    fitness: int,
    cost: float,
) -> None:
    """Offer ``cost`` as a candidate break into ``states[stop][fitness]``.

    Every fitness class reachable from ``states[start]`` competes; the
    cheapest total transition wins the slot.

    Args:
        states (list[list[_Break]]): DP table of break candidates per
            word boundary.
        start (int): First word index of the candidate line.
        stop (int): Last word index (exclusive) of the candidate line.
        fitness (int): Fitness class of the candidate break.
        cost (float): Precomputed span cost for the candidate line.

    """
    for previous_fitness, previous in enumerate(iterable=states[start]):
        transition: float = (
            Constants.transition
            if abs(fitness - previous_fitness) > 1
            else 0.0
        )
        total: float = previous.cost + cost + transition
        if total < states[stop][fitness].cost:
            states[stop][fitness] = _Break(
                cost=total,
                previous=start,
                fitness=previous_fitness,
            )


def leading_fit(*, text: str, room: int) -> tuple[str, str]:
    """Split reflowed prose into a fitting head run and the remainder.

    Structural lines (lists, indented blocks, blanks) never split: they
    return an empty head so callers keep the label on its own line.

    Args:
        text (str): One reflowed line.
        room (int): Columns available for the leading run.

    Returns:
        tuple[str, str]: Joined fitting tokens and the remaining tokens,
            or ``("", text)`` for structural lines.

    """
    stripped: str = text.lstrip()
    if (
        not stripped
        or text[0].isspace()
        or Constants.list_item.match(string=stripped) is not None
    ):
        return "", text
    tokens: list[str] = Constants.tokens.findall(string=stripped)
    head: list[str] = []
    used: int = 0
    while tokens:
        needed: int = len(tokens[0]) + (1 if head else 0)
        if used + needed > room:
            break
        head.append(tokens.pop(0))
        used += needed
    if not head:
        return "", text
    return " ".join(head), " ".join(tokens)


@final
class _Reflow:
    """Per-call prose state; code and examples never enter the line breaker."""

    def __init__(self, *, width: int, normalize_lists: bool) -> None:
        """Initialize a paragraph builder.

        Args:
            width (int): Available content columns.
            normalize_lists (bool): Normalize numbered separators.

        """
        self._width: int = width
        self._normalize: bool = normalize_lists
        self._output: list[str] = []
        self._paragraph: list[str] = []
        self._prefix: str = ""
        self._continuation: str = ""
        self._base_indent: int = 0
        self._fence: str | None = None
        self._example_indent: int | None = None
        self._literal_indent: int | None = None
        self._doctest: bool = False

    def run(self, *, text: str) -> str:
        """Wrap the unprotected paragraphs of a document.

        Args:
            text (str): Documentation text in its own indentation space.

        Returns:
            str: Reflowed text with code examples unchanged.

        """
        lines: list[str] = text.splitlines()
        for index, line in enumerate(iterable=lines):
            following: str = lines[index + 1] if index + 1 < len(lines) else ""
            if self._protected(line=line, following=following):
                self._flush()
                self._output.append(line)
            elif not line.strip():
                self._flush()
                self._output.append(line)
                self._doctest = False
            else:
                self._prose(line=line)
        self._flush()
        return "\n".join(self._output)

    def _protected(self, *, line: str, following: str) -> bool:
        """Track fences, doctests, literal blocks and example sections.

        Args:
            line (str): Current physical documentation line.
            following (str): Next line, to recognize NumPy section underlines.

        Returns:
            bool: Whether this line must bypass wrapping.

        """
        stripped: str = line.strip()
        indent: int = len(line) - len(line.lstrip())
        heading: bool = bool(stripped) and (
            stripped.endswith(":")
            or (bool(following.strip()) and set(following.strip()) == {"-"})
        )
        stripped_len_max: int = 3
        return (
            self._fenced(stripped=stripped)
            or self._example_section(
                stripped=stripped,
                indent=indent,
                heading=heading,
            )
            or self._literal_block(stripped=stripped, indent=indent)
            or self._doctest_line(stripped=stripped)
            or stripped.startswith(("|", ":", "..", ">>>", "```", "~~~"))
            or (
                len(stripped) >= stripped_len_max
                and set(stripped) in ({"="}, {"-"})
            )
            or heading
        )

    def _fenced(self, *, stripped: str) -> bool:
        """Track fenced code blocks opened by backticks or tildes.

        Args:
            stripped (str): Line content without surrounding whitespace.

        Returns:
            bool: Whether this line sits inside a fence or opens one.

        """
        if self._fence is not None:
            if stripped.startswith(self._fence):
                self._fence = None
            return True
        if stripped.startswith(("```", "~~~")):
            marker: str = stripped[0]
            self._fence = stripped[
                : len(stripped) - len(stripped.lstrip(marker))
            ]
            return True
        return False

    def _example_section(
        self,
        *,
        stripped: str,
        indent: int,
        heading: bool,
    ) -> bool:
        """Track an Examples section until an out-denting heading.

        Args:
            stripped (str): Line content without surrounding whitespace.
            indent (int): Leading whitespace column count.
            heading (bool): Whether this line is a section heading.

        Returns:
            bool: Whether this line belongs to an example section.

        """
        if self._example_indent is not None:
            if (
                heading
                and indent <= self._example_indent
                and not stripped.startswith((">>>", "..."))
            ):
                self._example_indent = None
            else:
                return True
        if stripped in {"Examples:", "Examples", "Example:", "Example"}:
            self._example_indent = indent
            return True
        return False

    def _literal_block(self, *, stripped: str, indent: int) -> bool:
        """Track ``::`` literal blocks until the indentation dedents.

        Args:
            stripped (str): Line content without surrounding whitespace.
            indent (int): Leading whitespace column count.

        Returns:
            bool: Whether this line sits inside a literal block or opens one.

        """
        if self._literal_indent is not None:
            if not stripped or indent > self._literal_indent:
                return True
            self._literal_indent = None
        if stripped.endswith("::"):
            self._literal_indent = indent
            return True
        return False

    def _doctest_line(self, *, stripped: str) -> bool:
        """Track doctest sessions until a blank line resets them.

        Args:
            stripped (str): Line content without surrounding whitespace.

        Returns:
            bool: Whether this line belongs to a doctest session.

        """
        if stripped.startswith(">>>"):
            self._doctest = True
        return self._doctest and bool(stripped)

    def _prose(self, *, line: str) -> None:
        """Accumulate a plain paragraph or start a hanging list/field entry.

        Args:
            line (str): One unprotected prose line.

        """
        marker: Match[str] | None = Constants.list_item.match(string=line)
        entry: Match[str] | None = Constants.entry.match(string=line)
        pad: str = line[: len(line) - len(line.lstrip())]
        if marker is not None or entry is not None:
            self._flush()
            self._base_indent = len(pad)
            if marker is not None:
                bullet: str = marker.group("marker")
                if self._normalize and bullet[0].isdigit():
                    bullet = bullet.rstrip(").]") + "."
                self._prefix = pad + bullet + " "
                self._paragraph.append(marker.group("body"))
            elif entry is not None:
                self._prefix = pad + entry.group("name") + ": "
                self._paragraph.append(entry.group("body"))
            self._continuation = " " * len(self._prefix)
            return
        hanging: bool = len(self._prefix) > self._base_indent
        if self._paragraph and (
            len(pad) <= self._base_indent
            if hanging
            else pad != self._continuation
        ):
            self._flush()
        if not self._paragraph:
            self._prefix = self._continuation = pad
            self._base_indent = len(pad)
        self._paragraph.append(line.strip())

    def _flush(self) -> None:
        """Append the pending paragraph and clear its text buffer."""
        if not self._paragraph:
            return
        content: list[str] = balanced_lines(
            text=normalize_spacing(line=" ".join(self._paragraph)),
            width=max(
                1,
                self._width - max(len(self._prefix), len(self._continuation)),
            ),
        )
        self._output.extend(
            (self._prefix if index == 0 else self._continuation) + line
            for index, line in enumerate(iterable=content)
        )
        self._paragraph.clear()


def _closing_word(*, word: str) -> bool:
    """Tell whether a token is detached trailing punctuation.

    Args:
        word (str): One prose token.

    Returns:
        bool: Whether it glues onto the preceding word. Pure colon runs
            such as ``::`` stay detached so literal-block markers survive,
            and dot runs such as ``...`` stay detached so ellipsis type
            arguments keep their spacing.

    """
    if not word or word.strip(":") == "":
        return False
    if word.strip(Constants.closing_punctuation) != "":
        return False
    return len(word) - len(word.lstrip(".")) <= 1


def _sentence_tail(*, word: str) -> bool:
    """Tell whether a token ends a sentence, ignoring closing marks.

    Args:
        word (str): One prose token, possibly already punctuation-merged.

    Returns:
        bool: Whether a wide gap after it should collapse to one space.

    """
    return word.rstrip("\"')]}>»").endswith(
        tuple(Constants.sentence_endings),
    )


def _opening_tail(*, word: str) -> bool:
    """Tell whether a token is detached opening punctuation.

    Args:
        word (str): One prose token.

    Returns:
        bool: Whether the following gap should disappear.

    """
    return bool(word) and word.strip(Constants.opening_punctuation) == ""


def normalize_spacing(*, line: str) -> str:
    """Attach detached punctuation and tighten post-sentence gaps.

    Prose tokens — inline code spans included — are walked with their
    intervening gaps, so `` ``literal``. `` becomes `` ``literal``. ``
    and ``word.  Next`` becomes ``word. Next`` while unrelated spacing,
    including alignment inside ordinary text, is preserved verbatim.

    Args:
        line (str): One physical line, indentation included.

    Returns:
        str: The line with punctuation spacing normalized.

    """
    pad: str = line[: len(line) - len(line.lstrip())]
    body: str = line.strip()
    if not body:
        return line
    pieces: list[str] = []
    tail: str = ""
    cursor: int = 0
    for match in Constants.tokens.finditer(string=body):
        word: str = match.group(0)
        gap: str = body[cursor : match.start()]
        cursor = match.end()
        if tail and _closing_word(word=word):
            pieces[-1] += word
            tail += word
            continue
        if tail:
            if len(gap) > 1 and _sentence_tail(word=tail):
                gap = " "
            elif _opening_tail(word=tail):
                gap = ""
        pieces.append(gap + word)
        tail = word
    return pad + "".join(pieces)


def reflow_text(*, text: str, width: int, normalize_lists: bool = True) -> str:
    """Reflow prose while retaining code examples and structural boundaries.

    Args:
        text (str): Cleaned documentation or a standalone comment block.
        width (int): Columns available after the source indentation/comment
            prefix.
        normalize_lists (bool): Convert numbered closing separators to periods.

    Returns:
        str: Reflowed text with hanging list/entry indentation.

    """
    return _Reflow(width=width, normalize_lists=normalize_lists).run(text=text)
