# autowrap's normalise-to-google pass currently strips structured
# ``Args:``/``Returns:`` blocks when the descriptions look like
# placeholders; keep it disabled so the templated docstrings emitted by
# ``add_doc_strings`` survive intact and existing real docstrings are
# left alone too.

from __future__ import annotations

import asyncio
import json
import re
import subprocess
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from time import monotonic
from typing import (
    TYPE_CHECKING,
    ClassVar,
    NamedTuple,
    Protocol,
    Self,
    TypedDict,
    TypeGuard,
    overload,
    Final,
    TypeVar,
    ParamSpec,
)
from re import Match
from collections.abc import Callable, Sized

type ListInt = list[int]
type ListStr = list[str]
type DictInt = dict[str, int]
type DictObject = dict[str, object]

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Callable,
        Iterable,
        Mapping,
        MutableMapping,
    )


# =============================================================================
# 1. Docstring style normalisation — four flavours of one function
# =============================================================================
# The normaliser should land all four below in Google style configured by
# the header ``# AUTOTYPE: docstrings-format=google``.


def google_style(names, keep_empty=False):
    """Summarise a sequence of names.

    Args:
        names: Sequence of raw names that may need whitespace cleanup
            and title casing.
        keep_empty: Whether empty items should be preserved after
            normalization.

    Returns:
        Normalized names ready for display.

    Raises:
        ValueError: If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def numpy_style(names, keep_empty=False):
    """Summarise a sequence of names.

    Parameters
    ----------
    names : list[str]
        Sequence of raw names that may need whitespace cleanup and
        title casing.
    keep_empty : bool
        Whether empty items should be preserved after normalization.

    Returns
    -------
    list[str]
        Normalized names ready for display.

    Raises
    ------
    ValueError
        If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def rest_style(names, keep_empty=False):
    """Summarise a sequence of names.

    :param names: Sequence of raw names that may need whitespace
        cleanup and title casing.
    :type names: list[str]
    :param keep_empty: Whether empty items should be preserved.
    :type keep_empty: bool
    :returns: Normalized names ready for display.
    :rtype: list[str]
    :raises ValueError: If all names are empty and keep_empty is False.
    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def github_style(names, keep_empty=False):
    """Summarise a sequence of names.

    ## Arguments
    - `names` (`list[str]`): Sequence of raw names that may need
      whitespace cleanup and title casing.
    - `keep_empty` (`bool`): Whether empty items should be preserved.

    ## Returns
    - `list[str]`: Normalized names ready for display.

    ## Raises
    - `ValueError`: If all names are empty and keep_empty is False.

    Args:
        names: TODO.
        keep_empty: TODO.

    Returns:
        TODO.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def missing_docstring_target(value, repeat=2):
    return str(value) * repeat


T = TypeVar("T")


# =============================================================================
# 2. Long single-line docstring → paragraph-wrapped
# =============================================================================


def long_single_line_doc(value: T) -> T:
    """This is a deliberately very long single-line summary that exceeds the configured line width so the wrapper has to fold it across multiple physical lines while preserving the semantic punctuation and the trailing period at the end of the sentence.

    Args:
        value (T): TODO.

    Returns:
        T: TODO.

    """
    return value


# =============================================================================
# 3. Bullet renest + nested-bullet indentation
# =============================================================================


def bullets_and_nesting() -> None:
    """Demonstrate bullet renesting and nested indentation.

    Top-level bullets that should align after wrapping:
        - primary item
          - nested item under primary (deeper indent should be
            preserved relative to the parent)
            - third-level nested item with a long description that
              forces a wrap of the body line
          - sibling nested item
        - second top-level item

    Mixed numbered + bullets:
        1. first numbered item
        2. second numbered item with intentionally extra space after
            the dot (separator-normaliser should collapse it)
        3) third item using a different separator (normaliser unifies)

    """
    return


T2 = TypeVar("T2")


class SupportsRadd(Protocol):
    """Structural contract requiring ``__radd__``."""

    def __radd__(self, arg0, /):
        """Provide the required ``__radd__`` operation.

        Args:
            arg0: TODO."""
        ...


class SupportsRadd2(Protocol):
    """Structural contract requiring ``__radd__``."""

    def __radd__(self, arg0, /) -> T2:
        """Provide the required ``__radd__`` operation.

        Args:
            arg0: TODO.

        Returns:
            TODO."""
        ...


# =============================================================================
# 4. Colon-aligned definitions and ruler underlines
# =============================================================================


def colon_aligned_and_rulers(a: T2, b: SupportsRadd, c: SupportsRadd2) -> T2:
    """Show colon-introduced definition alignment and ruler-line tidy.

    Args:
        a (T2): a short description that should align with siblings
        b (SupportsRadd): another one whose name is longer; the colon-alignment
            pass should pad ``a`` so its colon column matches.
        c (SupportsRadd2): a third with a longer name still and a multi-line
            body
            wrapping the rest of the prose under the colon column.

    Attributes:
        ----------
        items
        underlined section heading where the ``----`` underline should
        be normalised to match the heading width exactly.

    Attributes:
        -------
        run
        another underlined section header.

    Returns:
        T2: TODO.

    """
    return a + b + c


# =============================================================================
# 5. Code-block preservation, URL preservation, backtick names
# =============================================================================


def code_blocks_and_urls() -> None:
    """Preserve fenced code and URLs verbatim while wrapping prose.

    The wrapper should NOT touch the fenced block below, nor split URLs
    across lines. Inline backtick names like ``my_function`` should be
    preserved as visual emphasis.

    Example::

        result = my_function(value=42)
        print(result.upper())

    Reference: https://example.com/very/long/path/that/should/not/be/broken?query=1&also=2

    """
    return


# =============================================================================
# 6. Continuation paragraphs under list items
# =============================================================================


def continuation_paragraphs() -> None:
    """List items with continuation prose.

    Notes:
        - The first item has a one-line body.

          A continuation paragraph belonging to the same list item,
          indented under the bullet, should remain associated with the
          item after wrapping.

        - Second item.

          Another continuation paragraph that should wrap independently
          from the first item's prose, preserving the blank line.

    """
    return


# =============================================================================
# 7. Multi-line consecutive comment wrapping
# =============================================================================
# This is a deliberately long block comment that spans many lines and would, without the comment wrapper, leave a stretched physical line. The wrapper should fold all these consecutive lines into a single re-flowed paragraph with the leading ``#`` preserved on every emitted line so the visual effect is consistent.
# A separate paragraph below the blank line should NOT be merged into the one above because the wrapper respects blank-line boundaries.


# =============================================================================
# 8. Long string assignments → parenthesised implicit concatenation
# =============================================================================
LONG_LITERAL: Final[str] = (
    "lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
    "eiusmod tempor incididunt ut labore et dolore magna aliqua, ut enim "
    "ad minim veniam"
)


# =============================================================================
# 9. Inference feature 1 — SSA local re-typing
# =============================================================================


def union_via_reassignment(flag):
    probe = 0
    if flag:
        probe = "fallback"
    return probe


# =============================================================================
# 10. Inference feature 2 — `is None` / `is not None` narrowing
# =============================================================================


def narrow_via_is_none(value) -> int:
    if value is None:
        return 0
    return len(value) * 2


# =============================================================================
# 11. Inference feature 3 — receiver chain inference
# =============================================================================


def chain_inference(p) -> tuple[str, ListStr]:
    body: str = Path(p).read_text()
    lines: ListStr = body.splitlines()
    upper_first: str = lines[0].upper() if lines else ""
    raw: bytes = Path(p).read_bytes()
    text: str = raw.decode()
    return upper_first, text.split()


# =============================================================================
# 12. Inference feature 4 — kwarg backflow at call sites
# =============================================================================


def helper_backflow(name: str, count: int, prefix: str) -> str:
    return f"{prefix}{name}:{count}"


def caller_with_kwargs() -> str:
    return helper_backflow(name="alice", count=42, prefix=">> ")


# =============================================================================
# 13. Inference feature 5 — Literal narrowing from `==` / `match`
# =============================================================================


def colour_to_hex(colour) -> str:
    if colour == "red":
        return "#ff0000"
    if colour == "green":
        return "#00ff00"
    if colour == "blue":
        return "#0000ff"
    return "#000000"


def http_status_word(code) -> str:
    match code:
        case 200:
            return "ok"
        case 404:
            return "missing"
        case 500:
            return "error"
        case _:
            return "unknown"


# =============================================================================
# 14. Inference feature 6 — TypedDict synthesis
# =============================================================================


def build_user_record(name, age):
    if not name:
        return {"name": "anonymous", "age": 0, "active": False}
    if age < 18:
        return {"name": name, "age": age, "active": False}
    return {"name": name, "age": age, "active": True}


# =============================================================================
# 15. autokwargs — deep inspection of stdlib + workspace receivers
# =============================================================================
# - ``f.write_text("hi", encoding="utf-8")`` becomes ``data="hi"``
# - ``c.most_common(2)`` becomes ``n=2``


def writes_path(target_dir):
    f = Path(target_dir) / "out.txt"
    f.write_text("hello world", encoding="utf-8")
    return f.read_text()


class SupportsSplit(Protocol):
    """Structural contract requiring ``split``."""

    def split(self):
        """Provide the required ``split`` operation."""
        ...


def top_words(text: SupportsSplit, n):
    c = Counter(text.split())
    return c.most_common(n)


# =============================================================================
# 16. Autosort — methods out of canonical order
# =============================================================================


class OutOfOrderClass:
    """Methods intentionally misordered to exercise autosort."""

    def helper(self):
        return self._x

    def __repr__(self) -> str:
        return f"OutOfOrderClass({self._x!r})"

    @property
    def value(self):
        return self._x

    @classmethod
    def from_int(cls, value) -> Self:
        return cls(value)

    def __init__(self, x) -> None:
        self._x = x

    @staticmethod
    def banner() -> str:
        return "OutOfOrderClass"


# =============================================================================
# 17. autorestore — lint-ignore positions survive transformation
# =============================================================================
# Each suppression below is on a line that the pipeline will rewrap;
# autorestore should reposition the comment onto the new line where the
# diagnostic still fires.


async def with_timeout(coro, timeout):  # noqa: ASYNC109
    """Run coro with a timeout; return None on expiry.

    Args:
        coro: TODO.
        timeout: TODO.

    Returns:
        TODO.

    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError:
        return None


def narrow_with_assert(x):
    """Use assert isinstance to narrow x to numeric.

    Args:
        x: TODO.

    Returns:
        TODO.

    """
    assert isinstance(x, (int, float))  # noqa: S101
    return x + 1


@contextmanager
def timer(label):
    """Print elapsed time around a ``with`` block.

    Args:
        label: TODO.

    Yields:
        TODO.

    """
    start: float = monotonic()
    try:
        yield
    finally:
        elapsed = monotonic() - start
        print(f"{label}: {elapsed:.4f}s")  # noqa: T201


def yield_in_loop(n):
    """Yield-in-for that ruff would suggest converting to yield-from.

    Args:
        n: TODO.

    Yields:
        TODO.

    """
    for i in range(n):  # noqa: UP028
        yield i


# =============================================================================
# 18. Generators + async generator + Protocol + NamedTuple + TypedDict
# =============================================================================


def count_up(n):
    """Yield integers from 0 up to n-1.

    Args:
        n: TODO.

    Yields:
        TODO.

    """
    yield from range(n)


async def async_count(n):
    """Async generator yielding integers.

    Args:
        n: TODO.

    Yields:
        TODO.

    """
    for i in range(n):
        yield i


@dataclass(frozen=True)
class Vector3:
    """Immutable 3-D vector.

    Attributes:
        x (float): TODO.
        y (float): TODO.
        z (float): TODO.

    """

    x: float
    y: float
    z: float = 0.0

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass
class Stack:
    """Stack backed by a list.

    Attributes:
        items (list): TODO.

    """

    items: list = field(default_factory=list)

    def push(self, item) -> None:
        self.items.append(item)

    def pop(self):
        return self.items.pop() if self.items else None


class Sizeable(Protocol):
    """Anything with __len__."""

    def __len__(self) -> int:
        """Return the container length."""
        ...


class Point(NamedTuple):
    """2-D point.

    Attributes:
        x (float): TODO.
        y (float): TODO.

    """

    x: float
    y: float


class WorkerConfig(TypedDict):
    """Statically-shaped dict input.

    Attributes:
        name (str): TODO.
        parallelism (int): TODO.

    """

    name: str
    parallelism: int


# =============================================================================
# 19. Walrus, comprehensions, match-mapping
# =============================================================================


def first_long_token(text):
    return next((t for t in text.split() if len(t) > 5), None)


def keep_unique(items):
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]


def describe_action(payload) -> str:
    match payload:
        case {"kind": "move", "dx": dx, "dy": dy}:
            return f"move by ({dx},{dy})"
        case {"kind": "stop"}:
            return "stop"
        case _:
            return "ignore"


# =============================================================================
# 20. Self-returning methods → Self
# =============================================================================


class Builder:
    """Fluent builder; each setter returns self."""

    def __init__(self) -> None:
        self._parts = []

    def add(self, x):
        self._parts.append(x)
        return self

    def build(self) -> str:
        return ":".join(map(str, self._parts))


# =============================================================================
# 22. Deeply nested bullet alignment + Returns with multiple typed entries
# =============================================================================


def deeply_nested_bullets():
    """Showcase deep bullet renest, alignment, and structured Returns.

    Notes:
        * top-level star bullet (should be normalised to ``-``):
            * level-2 star bullet with a long body that has to fold across
              several physical lines while staying aligned
                * level-3 nested bullet whose marker indent should be
                  preserved exactly two columns deeper than its parent
                * level-3 sibling
            * level-2 sibling with mixed inline ``code`` and a URL
              https://example.com/extremely/long/path/that/must/not/break
        1. numbered top-level item
            a. lettered nested item under numeric (mixed-marker nesting)
            b. lettered sibling
                i. roman-numeral inner item
                ii. roman-numeral sibling
        2. numbered sibling

    Returns:
        tuple: A 3-tuple containing
            - ``int``: the count of top-level items
            - ``list[str]``: the flattened bullet bodies in DFS order
            - ``dict[str, int]``: per-marker-style frequency map

    Raises:
        ValueError: never, but documented to exercise the Raises section
            alignment and multi-line body wrapping.

    """
    return 0, [], {}


# =============================================================================
# 23. Inference through imported non-builtin (stdlib) modules
# =============================================================================
# Exercises receiver-chain inference across ``json``, ``re``, ``subprocess``
# and Path so autotype/autokwargs trace return types through module APIs.


def parse_user_json(blob: str):
    data: DictObject = json.loads(s=blob)
    name = data.get("name")
    age = data.get("age", 0)
    return name, age


def extract_first_int(text: str) -> int | None:
    match: Match[str] | None = re.search(pattern="\\d+", string=text)
    if match is None:
        return None
    return int(match.group(0))


def normalise_whitespace(text: str):
    pattern = re.compile(pattern="\\s+")
    return pattern.sub(" ", text).strip()


def list_python_versions():
    proc = subprocess.run(
        args=["python3", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip(), proc.returncode


# =============================================================================
# 24. Conflicting / shadowed scopes — same name, different inferred types
# =============================================================================
# The inference engine must keep per-scope bindings distinct so the outer
# ``value: str`` is not confused with the inner ``value: int``.

GREETING: Final[str] = "module-level-string"


def length_doubled(text: str) -> int:
    return len(text) * 2


def coerce_in_branches(flag: bool, raw: str) -> float | str:
    return float(raw) if flag else str(raw).upper()


class ScopeMixer:
    """Class attribute and method-local exercise distinct scopes.

    Attributes:
        counter (int): TODO.

    """

    counter: int = 0

    def bump(self, delta: int):
        next_value = self.counter + delta
        self.counter = next_value
        return next_value

    def reset(self):
        self.counter = 0
        return self.counter


# =============================================================================
# 25. Magic-number injection — many int/float literals in expressions
# =============================================================================
# autoinsert should hoist these into named module-level constants.


def temperature_score(celsius: float) -> float:
    if celsius < -40:
        return 0.0
    if celsius < 0:
        return celsius * 0.5 + 50
    if celsius < 100:
        return celsius * 1.5 + 75
    return 300.0


class SupportsGe(Protocol):
    """Structural contract requiring ``__ge__``."""

    def __ge__(self, arg0: int, /) -> bool:
        """Provide the required ``__ge__`` operation.

        Args:
            arg0 (int): TODO.

        Returns:
            TODO.

        """
        ...


def grade_from_score(score: SupportsGe) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def compute_discount(price: float, units: int) -> float:
    if units >= 24:
        return price * 0.65
    if units >= 12:
        return price * 0.8
    if units >= 6:
        return price * 0.9
    return price


# =============================================================================
# 26. autokwargs — positional calls promoted to keyword on stdlib + workspace
# =============================================================================


def write_log_file(target_dir, payload):
    path = Path(target_dir) / "log.json"
    path.write_text(json.dumps(obj=payload, indent=2), encoding="utf-8")
    return path


def replace_tokens(text: str, token: str, replacement: str) -> str:
    return re.sub(pattern=token, repl=replacement, string=text, count=0)


def slice_window(items, start: int, stop: int):
    return list(items)[start:stop]


# =============================================================================
# 27. Fuller method-order exercise (canonical: dunders → classmethod →
#     staticmethod → property → public → private)
# =============================================================================


class OrderingHeavy:
    """A class with members in deliberately scrambled order."""

    def _helper(self, x):
        return x * 2

    def public_action(self):
        return self._helper(self.size)

    @property
    def size(self) -> int:
        return len(self._items)

    @staticmethod
    def banner() -> str:
        return "OrderingHeavy"

    @classmethod
    def make_empty(cls) -> Self:
        return cls([])

    def __repr__(self) -> str:
        return f"OrderingHeavy(items={self._items!r})"

    def __init__(self, items) -> None:
        self._items = list(items)

    def __len__(self) -> int:
        return len(self._items)


# =============================================================================
# 28. @overload — multiple signatures + runtime dispatch
# =============================================================================


@overload
def coerce(value: int) -> str: ...
@overload
def coerce(value: str) -> int: ...
def coerce(value):
    if isinstance(value, int):
        return str(value)
    return len(value)


# =============================================================================
# 28b. functools.lru_cache — decorator preserving recursive signature
# =============================================================================


@lru_cache(maxsize=128)
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)


# =============================================================================
# 30. Enum values + Literal narrowing on members
# =============================================================================


class Status(Enum):
    """Three-state job status."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


def status_priority(status: Status) -> int:
    if status is Status.PENDING:
        return 0
    if status is Status.RUNNING:
        return 1
    return 2


# =============================================================================
# 31. Dataclass field with default_factory + __post_init__
# =============================================================================


@dataclass
class HistoryBuffer:
    """Bounded history buffer with derived count attribute.

    Attributes:
        items (ListStr): TODO.
        capacity (int): TODO.

    """

    items: ListStr = field(default_factory=list)
    capacity: int = 16

    def __post_init__(self) -> None:
        if len(self.items) > self.capacity:
            self.items = self.items[-self.capacity :]
        self.count = len(self.items)


# =============================================================================
# 32. ClassVar — class-scoped constants distinct from instance attrs
# =============================================================================


class HttpClient:
    """Demonstrate ClassVar distinct from instance attrs.

    Attributes:
        DEFAULT_TIMEOUT (ClassVar[float]): TODO.
        PROTOCOL (ClassVar[str]): TODO.

    """

    DEFAULT_TIMEOUT: ClassVar[float] = 30.0
    PROTOCOL: ClassVar[str] = "https"

    def __init__(self, host: str, timeout: float | None = None) -> None:
        self.host = host
        self.timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT


# =============================================================================
# 33. Walrus operator inside conditional and comprehension
# =============================================================================


def walrus_filter(items: ListStr) -> ListStr:
    return [stripped for x in items if (stripped := x.strip())]


def walrus_in_if(items: ListStr) -> int | None:
    if (n := len(items)) > 3:
        return n
    return None


# =============================================================================
# 34. f-string with nested expressions and format spec
# =============================================================================


def format_record(name: str, score: float, width: int) -> str:
    upper: str = name.upper()
    return f"{upper:>{width}} :: {score:7.2f}% [{Status.DONE.value!r}]"


# =============================================================================
# 35. Async context manager + async iteration
# =============================================================================


class AsyncGate:
    """Simple async context manager + async iterator."""

    def __init__(self, limit: int) -> None:
        self._limit = limit
        self._n = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        self._n = 0

    def __aiter__(self) -> AsyncGate:
        return self

    async def __anext__(self) -> int:
        if self._n >= self._limit:
            raise StopAsyncIteration
        self._n += 1
        return self._n


async def consume_gate(limit: int) -> ListInt:
    out: ListInt = []
    async with AsyncGate(limit) as gate:
        async for value in gate:
            out.append(value)  # noqa: PERF401
    return out


# =============================================================================
# 36. Starred unpacking and **kwargs forwarding
# =============================================================================


def forward_call(target, *args, **kwargs):
    return target(*args, **kwargs)


def merge_dicts(base: DictObject, extras: DictObject):
    return {**base, **extras}


# =============================================================================
# 37. Iterator protocol — __iter__ + __next__
# =============================================================================


class CountDown:
    """Manual iterator that counts down from ``start`` to zero."""

    def __init__(self, start: int) -> None:
        self._current = start

    def __iter__(self) -> CountDown:
        return self

    def __next__(self) -> int:
        if self._current <= 0:
            raise StopIteration
        self._current -= 1
        return self._current + 1


# =============================================================================
# 38. TypeGuard narrowing
# =============================================================================


def is_str_list(items: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in items)


def join_if_strings(items: list[object]) -> str:
    if is_str_list(items=items):
        return ", ".join(items)
    return ""


# =============================================================================
# 39. Forward inference — narrow as we walk down through guards
# =============================================================================
# Each assignment refines the inferred type further. autotype should track:
#   raw: object → str (after isinstance) → str (split-result is list[str])
#   first: str → int (after int() coercion)
#   ratio: float (from int / float arithmetic with explicit float divisor)


def forward_narrow_pipeline(raw):
    assert isinstance(raw, str)  # noqa: S101
    parts = raw.split(":")
    first = parts[0]
    first = int(first)
    ratio = first / 3.5
    return parts, first, ratio


# =============================================================================
# 40. Backward inference — call-site usage refines the parameter type
# =============================================================================
# ``packet_payload`` and ``packet_count`` are only ever called with concrete
# types; autotype's kwarg-backflow should annotate them precisely from the
# call sites below without any explicit annotations at the def-site.


def packet_payload(name: str, headers: dict[str, str], body: bytes) -> str:
    return f"{name}:{len(headers)}:{len(body)}"


def packet_count(items: ListStr) -> int:
    return sum(1 for _ in items)


def call_packet_helpers() -> tuple[str, int]:
    out: str = packet_payload(
        name="alpha", headers={"x-trace": "id-7"}, body=b"hello"
    )
    return out, packet_count(items=["a", "b", "c"])


# =============================================================================
# 41. Deep docstring bullets — 4-level nesting + mixed marker styles
# =============================================================================


def deep_docstring_alignment() -> None:
    """Showcase 4-level bullet nesting with mixed marker styles.

    Layers (each level indents two columns deeper than its parent):

    - ``level 1`` — top-level dash item with a description long enough
      that the wrapper must fold it across multiple physical lines
      while keeping the continuation aligned under the first letter.
        * ``level 2`` — switches to star marker (renormalised to
          dash by the docstring normaliser) with body text that
          itself wraps to verify the continuation indent.
            + ``level 3`` — plus marker (also renormalised) with
              a multi-paragraph body:

              A continuation paragraph still belonging to ``level 3``
              that must remain associated with the bullet after the
              blank-line separator above.
                - ``level 4`` — back to dash marker; the deepest
                  level has a body wide enough to force a wrap and
                  exercise the deepest column alignment.
                - ``level 4`` sibling whose colon-introduced body
                  must align with the sibling above.

    Numbered nesting (markers and alignment also normalised):

    1. ``primary`` — top-level numbered.
        a) ``letter`` — lower-case letter marker with parenthesis
           separator (normaliser unifies to a single style).
            i. ``roman`` — lower-case roman inside a letter inside
               a numeric: three levels of mixed-marker nesting.
            ii. ``roman`` sibling with a body long enough to wrap
                under the column established by the marker.
        b) ``letter`` sibling.
    2. ``secondary`` — top-level sibling with one nested item:
        a) ``solo``.
    3. ``tertiary``.

    Description list (term :: definition) — colon-introduced
    definitions that align on the longest term:

        short_term :: a brief description aligned to the colon
            column established by the longest term below.
        medium_term :: another description; same alignment column.
        very_long_term_name :: anchors the colon column for the
            group; siblings above pad with spaces so all colons
            stack vertically.

    Returns:
        None: this function exists purely to drive the wrapper.

    """
    return


# =============================================================================
# 42. Generic TypeVar containers — element type flows through methods
# =============================================================================
# Exercises PEP 695 syntax-style generics resolved by autotype: ``Stack[T]``
# preserves the element type across ``push``/``pop``/``peek``.


class TypedStack[T]:
    """Stack parameterised on element type ``T``."""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T | None:
        return self._items.pop() if self._items else None

    def peek(self) -> T | None:
        return self._items[-1] if self._items else None

    def __len__(self) -> int:
        return len(self._items)


class TypedQueue[T]:
    """FIFO queue parameterised on element type ``T``."""

    def __init__(self, items: list[T] | None = None) -> None:
        self._items: list[T] = list(items) if items is not None else []

    def enqueue(self, item: T) -> None:
        self._items.append(item)

    def dequeue(self) -> T | None:
        return self._items.pop(0) if self._items else None

    def drain(self) -> list[T]:
        drained = list(self._items)
        self._items.clear()
        return drained


class Pair[K, V]:
    """Two-key generic record mirroring ``typing.Generic`` style."""

    def __init__(self, key: K, value: V) -> None:
        self.key: K = key
        self.value: V = value

    def swapped(self) -> Pair[V, K]:
        return Pair(self.value, self.key)


# =============================================================================
# 43. Abstract base class + concrete subclasses (template method)
# =============================================================================


from abc import ABC, abstractmethod


class Renderer(ABC):
    """Abstract renderer with a templated public ``render`` method."""

    def render(self, value: object) -> str:
        prepared = self._prepare(value=value)
        body = self._format(prepared=prepared)
        return self._wrap(body=body)

    @abstractmethod
    def _format(self, prepared: str) -> str:
        """Return ``prepared`` formatted for the concrete output.

        Args:
            prepared (str): TODO.

        """

    def _prepare(self, value: object) -> str:
        return str(value).strip()

    def _wrap(self, body: str) -> str:
        return body


class JsonRenderer(Renderer):
    """Renderer that emits JSON-quoted strings."""

    def _format(self, prepared: str) -> str:
        return json.dumps(obj=prepared)


class BracketRenderer(Renderer):
    """Renderer that wraps the body in square brackets."""

    def _format(self, prepared: str) -> str:
        return prepared.upper()

    def _wrap(self, body: str) -> str:
        return f"[{body}]"


# =============================================================================
# 44. Mixin pattern — cooperative MRO, super() forwarding
# =============================================================================


class TimestampMixin:
    """Mixin attaching a creation timestamp to any record."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.created_at: float = monotonic()


class CountingMixin:
    """Mixin counting how many times ``record`` has been called."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.hits = 0

    def record(self) -> int:
        self.hits += 1
        return self.hits


class AuditLog(TimestampMixin, CountingMixin):
    """Concrete record combining timestamp + counter mixins."""

    def __init__(self, source: str) -> None:
        super().__init__()
        self.source = source

    def describe(self) -> str:
        return f"{self.source}@{self.created_at:.3f}#{self.hits}"


# =============================================================================
# 45. itertools / functools heavy use — receiver chains across stdlib
# =============================================================================


from functools import reduce
from itertools import accumulate, chain, groupby, islice, takewhile


def running_total(values: ListInt) -> ListInt:
    return list(accumulate(values))


def grouped_runs(text: str) -> list[tuple[str, int]]:
    return [(key, sum(1 for _ in group)) for key, group in groupby(text)]


def flatten_pairs(pairs: list[tuple[int, int]]) -> ListInt:
    return list(chain.from_iterable(pairs))


def first_n_under_limit(values: ListInt, limit: int) -> ListInt:
    return list(islice(takewhile(lambda v: v < limit, values), 8))


def fold_product(values: ListInt) -> int:
    return reduce(lambda a, b: a * b, values, 1)


# =============================================================================
# 46. datetime arithmetic — chain through stdlib date/time types
# =============================================================================


from datetime import UTC, datetime, timedelta


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def shift_days(stamp: datetime, days: int) -> datetime:
    return stamp + timedelta(days=days)


def is_recent(stamp: datetime, window_hours: int) -> bool:
    threshold = datetime.now(tz=UTC) - timedelta(hours=window_hours)
    return stamp >= threshold


def days_between(a: datetime, b: datetime) -> int:
    return abs((a - b).days)


# =============================================================================
# 47. pathlib — heavy receiver-chain inference + with statements
# =============================================================================


def read_first_nonblank(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.strip()
    return ""


def write_listing(target_dir: Path, names: ListStr) -> Path:
    listing = target_dir / "listing.txt"
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("\n".join(sorted(names)), encoding="utf-8")
    return listing


def walk_python_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if not p.name.startswith(".")]


def file_size_kb(path: Path) -> float:
    return path.stat().st_size / 1024


# =============================================================================
# 48. collections.abc — ABC-based duck typing
# =============================================================================


def map_values[K, V, W](
    source: Mapping[K, V],
    fn: Callable[[V], W],
) -> dict[K, W]:
    return {k: fn(v) for k, v in source.items()}


def merge_dicts_inplace(
    target: MutableMapping[str, int],
    extra: Mapping[str, int],
) -> None:
    for key, value in extra.items():
        target[key] = target.get(key, 0) + value


def iterable_to_counts(items: Iterable[str]) -> DictInt:
    counts: DictInt = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


# =============================================================================
# 49. Recursive shape inference — tree walker that returns dict[str, object]
# =============================================================================


def flatten_tree(
    node: DictObject,
    prefix: str = "",
) -> DictObject:
    """Flatten a nested ``dict``/``list`` tree into dotted-key form.

    Args:
        node (DictObject): TODO.
        prefix (str): TODO.

    Returns:
        DictObject: TODO.

    """
    result: DictObject = {}
    for key, value in node.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_tree(value, full))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    result.update(flatten_tree(item, f"{full}[{index}]"))
                else:
                    result[f"{full}[{index}]"] = item
        else:
            result[full] = value
    return result


def deep_merge(
    left: DictObject,
    right: DictObject,
) -> DictObject:
    """Recursively merge two dict trees; ``right`` wins on conflicts.

    Args:
        left (DictObject): TODO.
        right (DictObject): TODO.

    Returns:
        DictObject: TODO.

    """
    merged: DictObject = dict(left)
    for key, value in right.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(
                cast_dict(merged[key]),
                cast_dict(value),
            )
        else:
            merged[key] = value
    return merged


def cast_dict(value: object) -> DictObject:
    return value if isinstance(value, dict) else {}


# =============================================================================
# 50. Algorithm patterns — magic-number-rich math/sort/search
# =============================================================================


def binary_search(items: ListInt, target: int) -> int:
    low, high = 0, len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def insertion_sort(items: ListInt) -> ListInt:
    out: ListInt = list(items)
    for i in range(1, len(out)):
        current: int = out[i]
        j = i - 1
        while j >= 0 and out[j] > current:
            out[j + 1] = out[j]
            j -= 1
        out[j + 1] = current
    return out


def fibonacci_iter(limit: int) -> ListInt:
    out: ListInt = []
    a, b = 0, 1
    while a < limit:
        out.append(a)
        a, b = b, a + b
    return out


def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a=a, b=b) if a and b else 0


def factorial(n: int) -> int:
    if n < 0:
        return 0
    result = 1
    for k in range(2, n + 1):
        result *= k
    return result


def power_mod(base: int, exp: int, modulus: int) -> int:
    result = 1 % modulus
    current = base % modulus
    while exp > 0:
        if exp & 1:
            result = (result * current) % modulus
        current = (current * current) % modulus
        exp >>= 1
    return result


# =============================================================================
# 51. String parsing — state-machine style with explicit transitions
# =============================================================================


def parse_csv_row(line: str) -> ListStr:
    fields: ListStr = []
    buffer: ListStr = []
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            fields.append("".join(buffer))
            buffer.clear()
        else:
            buffer.append(char)
    fields.append("".join(buffer))
    return fields


def tokenize_simple(text: str) -> ListStr:
    tokens: ListStr = []
    current: ListStr = []
    for char in text:
        if char.isalnum() or char == "_":
            current.append(char)
            continue
        if current:
            tokens.append("".join(current))
            current.clear()
        if not char.isspace():
            tokens.append(char)
    if current:
        tokens.append("".join(current))
    return tokens


def strip_comments(source: str) -> str:
    lines: ListStr = source.splitlines()
    cleaned: ListStr = []
    for line in lines:
        idx: int = line.find("#")
        cleaned.append(line[:idx].rstrip() if idx >= 0 else line)
    return "\n".join(cleaned)


# =============================================================================
# 52. Graph / tree data structures — recursive methods exercise inference
# =============================================================================


@dataclass
class TreeNode:
    """Binary tree node with value and optional children.

    Attributes:
        value (int): TODO.
        left (TreeNode | None): TODO.
        right (TreeNode | None): TODO.

    """

    value: int
    left: TreeNode | None = None
    right: TreeNode | None = None

    def insert(self, value: int) -> None:
        if value < self.value:
            if self.left is None:
                self.left = TreeNode(value=value)
            else:
                self.left.insert(value)
        elif self.right is None:
            self.right = TreeNode(value=value)
        else:
            self.right.insert(value)

    def in_order(self) -> ListInt:
        result: ListInt = []
        if self.left is not None:
            result.extend(self.left.in_order())
        result.append(self.value)
        if self.right is not None:
            result.extend(self.right.in_order())
        return result

    def depth(self) -> int:
        left_depth = 0 if self.left is None else self.left.depth()
        right_depth = 0 if self.right is None else self.right.depth()
        return 1 + max(left_depth, right_depth)


@dataclass
class Graph:
    """Adjacency-list graph keyed by node id.

    Attributes:
        adjacency (dict[int, ListInt]): TODO.

    """

    adjacency: dict[int, ListInt] = field(default_factory=dict)

    def add_edge(self, source: int, target: int) -> None:
        self.adjacency.setdefault(source, []).append(target)
        self.adjacency.setdefault(target, []).append(source)

    def neighbours(self, node: int) -> ListInt:
        return list(self.adjacency.get(node, []))

    def bfs(self, start: int) -> ListInt:
        visited: set[int] = {start}
        order: ListInt = [start]
        frontier: ListInt = [start]
        while frontier:
            current: int = frontier.pop(0)
            for neighbour in self.adjacency.get(current, []):
                if neighbour in visited:
                    continue
                visited.add(neighbour)
                order.append(neighbour)
                frontier.append(neighbour)
        return order


# =============================================================================
# 53. Numeric helpers — statistics-like with float divisors
# =============================================================================


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    avg: float = mean(values=values)
    return sum((v - avg) ** 2 for v in values) / (len(values) - 1)


def stdev(values: list[float]) -> float:
    return variance(values=values) ** 0.5


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values: list[float] = sorted(values)
    middle: int = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def clip(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def remap(
    value: float,
    src_low: float,
    src_high: float,
    dst_low: float,
    dst_high: float,
) -> float:
    if src_high == src_low:
        return dst_low
    ratio: float = (value - src_low) / (src_high - src_low)
    return dst_low + (dst_high - dst_low) * ratio


# =============================================================================
# 54. Long prose docstring — many paragraphs + Examples + See also
# =============================================================================


def long_prose_doc(value: str) -> str:
    """Demonstrate paragraph-wrapped long-form prose with sections.

    This first paragraph is intentionally extensive so the wrapper has
    something substantial to fold across multiple physical lines. The
    autowrap pass should preserve sentence boundaries, keep punctuation
    flush against the preceding word, and avoid breaking inside inline
    ``code`` spans or URLs like https://example.com/wrap-me-not.

    A second paragraph follows after a blank line. It must remain a
    distinct paragraph rather than merging with the first; the wrapper
    respects blank-line separators. Within this paragraph we exercise
    *emphasis*, **strong emphasis**, and ``inline code`` markers — all
    must round-trip cleanly through the rendering pass without becoming
    plain text and without altering whitespace inside the markers.

    A third paragraph contains a single very long sentence with no
    natural break points that must be folded by the wrapper using the
    width budget rather than punctuation cues to choose its breaks.

    Args:
        value (str): The input string to echo back; its presence forces the
            wrapper to emit an Args block with a multi-line entry whose
            continuation must indent under the parameter name.

    Returns:
        str: The input string returned verbatim. Documented across
            multiple lines to verify the Returns block alignment.

    Raises:
        ValueError: Never actually raised; documented so the Raises
            section receives a multi-line entry whose continuation
            indents under the exception name.

    Examples:
        Basic usage with a single short argument::

            >>> long_prose_doc("hi")
            'hi'

        Round-tripping a longer literal::

            >>> long_prose_doc("hello, world")
            'hello, world'

    Notes:
        The Examples block above uses the doctest convention and must
        survive the docstring normaliser without indentation drift.

    See Also:
        :func:`forward_narrow_pipeline`: a related forward-inference demo.
        :func:`call_packet_helpers`: a related backward-inference demo.

    """
    return value


# =============================================================================
# 55. Yields section — generator with documented yield type
# =============================================================================


def chunk_iter(values: ListInt, size: int):
    """Yield successive ``size``-sized chunks of ``values``.

    Args:
        values (ListInt): The source sequence to chunk.
        size (int): Number of elements in each yielded chunk; the final
            chunk may be smaller if ``len(values)`` is not divisible.

    Yields:
        list[int]: A slice of ``values`` of length ``<= size``.

    Raises:
        ValueError: If ``size`` is less than one.

    """
    if size < 1:
        msg: str = "size must be >= 1"
        raise ValueError(msg)
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def stride_iter(values: ListInt, step: int):
    """Yield values at the given ``step`` interval.

    Args:
        values (ListInt): The source sequence.
        step (int): Stride between successive yielded items.

    Yields:
        int: Every ``step``-th item from ``values``.

    """
    for index in range(0, len(values), step):
        yield values[index]


# =============================================================================
# 56. Deeply nested generics — Mapping[str, list[tuple[int, set[str]]]]
# =============================================================================


def index_records(
    rows: list[tuple[str, int, str]],
) -> dict[str, list[tuple[int, set[str]]]]:
    """Bucket rows by category, aggregating ids and tags.

    Args:
        rows (list[tuple[str, int, str]]): 3-tuples of (category, id, tag).

    Returns:
        dict[str, list[tuple[int, set[str]]]]: A mapping from category to a
            list of (id, set-of-tags) entries.

    """
    out: dict[str, list[tuple[int, set[str]]]] = {}
    for category, row_id, tag in rows:
        bucket = out.setdefault(category, [])
        # Try merge into existing entry with the same id.
        merged = False
        for index, (existing_id, tags) in enumerate(bucket):
            if existing_id == row_id:
                bucket[index] = (existing_id, tags | {tag})
                merged = True
                break
        if not merged:
            bucket.append((row_id, {tag}))
    return out


def matrix_transpose(matrix: list[list[float]]) -> list[list[float]]:
    if not matrix:
        return []
    cols: int = len(matrix[0])
    return [[row[col] for row in matrix] for col in range(cols)]


def nested_lookup(
    table: dict[str, dict[str, ListInt]],
    outer: str,
    inner: str,
) -> ListInt:
    return list(table.get(outer, {}).get(inner, []))


# =============================================================================
# 57. dict/list narrowing chains — many isinstance branches
# =============================================================================


def coerce_value(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return format(value, ".3f")
    if isinstance(value, list):
        parts = [coerce_value(item) for item in value]
        return ",".join(parts)
    if isinstance(value, dict):
        kv_parts: ListStr = []
        for key, item in value.items():
            kv_parts.append(str(key) + "=" + coerce_value(item))
        return ";".join(kv_parts)
    return "" if value is None else repr(value)


def flatten_lists_of_lists(values: list[ListInt | int]) -> ListInt:
    out: ListInt = []
    for item in values:
        if isinstance(item, list):
            out.extend(item)
        else:
            out.append(item)
    return out


def type_summary(values: list[object]) -> DictInt:
    summary: DictInt = {}
    for value in values:
        if isinstance(value, bool):
            key = "bool"
        elif isinstance(value, int):
            key = "int"
        elif isinstance(value, float):
            key = "float"
        elif isinstance(value, str):
            key = "str"
        elif isinstance(value, list):
            key = "list"
        elif isinstance(value, dict):
            key = "dict"
        else:
            key = "other"
        summary[key] = summary.get(key, 0) + 1
    return summary


# =============================================================================
# 58. Even more magic numbers — pricing/billing rules
# =============================================================================


def quarterly_rate(annual: float, quarter: int) -> float:
    if quarter == 1:
        return annual * 0.22
    if quarter == 2:
        return annual * 0.27
    if quarter == 3:
        return annual * 0.26
    return annual * 0.25


def shipping_cost(weight_kg: float, distance_km: float) -> float:
    base: float = 4.5
    weight_fee = weight_kg * 1.2
    distance_fee = distance_km * 0.08
    if distance_km > 500:
        distance_fee += 12.0
    if weight_kg > 20:
        weight_fee += 18.0
    return base + weight_fee + distance_fee


def tier_for_score(score: int) -> str:
    if score >= 950:
        return "platinum"
    if score >= 850:
        return "gold"
    if score >= 750:
        return "silver"
    if score >= 600:
        return "bronze"
    return "none"


def piecewise_tax(income: float) -> float:
    if income <= 10000:
        return income * 0.08
    if income <= 50000:
        return 800 + (income - 10000) * 0.15
    if income <= 200000:
        return 6800 + (income - 50000) * 0.24
    return 42800 + (income - 200000) * 0.33


# =============================================================================
# 59. Larger method-sort exercise — full canonical-order test class
# =============================================================================


class FullScrambledClass:
    """Class with every canonical-order category present and misordered.

    Attributes:
        _internal_state (int): TODO.

    """

    _internal_state: int = 0

    def _internal_helper(self) -> int:
        return self._internal_state

    def adjust(self, delta: int) -> int:
        self._internal_state += delta
        return self._internal_state

    @property
    def state(self) -> int:
        return self._internal_state

    @staticmethod
    def signature() -> str:
        return "FullScrambledClass"

    @classmethod
    def from_dict(cls, payload: DictInt) -> FullScrambledClass:
        instance = cls()
        instance._internal_state = payload.get("state", 0)
        return instance

    def __repr__(self) -> str:
        return f"FullScrambledClass(state={self._internal_state})"

    def __init__(self) -> None:
        self._internal_state = 0

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, FullScrambledClass)
            and other._internal_state == self._internal_state
        )

    def __hash__(self) -> int:
        return hash(self._internal_state)

    def __len__(self) -> int:
        return abs(self._internal_state)


# =============================================================================
# 60. Yet another autokwargs exercise — many positional stdlib calls
# =============================================================================


def lots_of_positional_calls(
    target_dir: Path,
    items: ListStr,
    delim: str,
) -> DictInt:
    joined: str = delim.join(items)
    out_path = target_dir / "joined.txt"
    out_path.write_text(joined, encoding="utf-8")
    counts = Counter(items)
    top = counts.most_common(3)
    return dict(top)


def regex_pipeline(text: str) -> dict[str, str]:
    return {
        "compact": re.sub(pattern="\\s+", repl=" ", string=text),
        "upper_alpha": re.sub(pattern="[^A-Z]", repl="", string=text.upper()),
        "first_word": re.split(pattern="\\s+", string=text.strip())[0]
        if text.strip()
        else "",
        "letters_only": re.sub(pattern="[^A-Za-z]", repl="", string=text),
    }


def slice_helpers(items: ListInt) -> dict[str, ListInt]:
    return {
        "first_three": items[:3],
        "last_three": items[-3:],
        "middle": items[len(items) // 4 : -len(items) // 4]
        if len(items) >= 4
        else [],
        "evens": items[::2],
        "reversed": items[::-1],
    }


# =============================================================================
# 61. Edge-case docstring wrapping — embedded blockquotes and citations
# =============================================================================


def docstring_with_blockquote(value: str) -> str:
    """Docstring with embedded quotes and citation styles.

    Inline quote followed by attribution:

        "Premature optimization is the root of all evil."
            — Donald Knuth, *Structured Programming with go to Statements*

    A second blockquote, multi-paragraph:

        First quoted paragraph spanning enough words that the wrapper
        has to fold the quote across multiple lines while preserving
        the leading indentation that marks it as a blockquote.

        Second quoted paragraph; both belong to the same quote block
        and the blank-line separator between them must survive the
        wrap pass.

    A code block follows the quote to verify the wrapper doesn't
    accidentally promote prose into the code block::

        result = docstring_with_blockquote("x")
        assert result == "x"

    Args:
        value (str): A simple string echo argument.

    Returns:
        str: The unchanged input value.

    """
    return value


# =============================================================================
# 62. Forward + backward inference loop — call-site propagates upstream
# =============================================================================


def upstream_consumer(payload):
    parts = payload.split("=", 1)
    return parts[0], parts[1]


def upstream_aggregator(items: ListStr):
    return [upstream_consumer(item) for item in items]


def driver_for_inference():
    fixed = ["k1=v1", "k2=v2", "k3=v3"]
    return upstream_aggregator(items=fixed)


# =============================================================================
# 63. Closure tracking — inner function captures outer typed parameter
# =============================================================================
# autotype's nonlocal-tracking pass should infer the inner function's
# parameters from how it uses values closed-over from the enclosing scope.
# (See docs/README_autotype.md → "Closure Tracking".)


def make_adder(base: int):
    def adder(amount: int) -> int:
        return base + amount

    return adder


def make_indexed_getter(prefix: str):
    def get(key: str) -> str:
        return prefix + "." + key

    return get


def use_closures() -> tuple[int, str]:
    add5 = make_adder(base=5)
    label = make_indexed_getter(prefix="env")
    return add5(7), label("PATH")


# =============================================================================
# 64. String alias synthesis — repeated Literal unions across params
# =============================================================================
# When two distinct functions narrow on the same finite string set, autotype's
# alias synthesizer hoists the union into a single named Literal alias so the
# annotations stay DRY. (See docs/README_autotype.md → "String Alias
# Synthesis".)


def process_status(status) -> bool:
    if status == "active":
        return True
    if status == "inactive":
        return False
    return False


def handle_mode(mode) -> int:
    if mode == "active":
        return 1
    if mode == "inactive":
        return 0
    return -1


def render_state(state) -> str:
    if state == "active":
        return ">"
    if state == "inactive":
        return "."
    return "?"


# =============================================================================
# 65. Memoization pattern — manual cache dict synthesized as concrete dict
# =============================================================================
# autotype detects the ``if x in cache: return cache[x]; cache[x] = result``
# shape and annotates ``cache`` from the values it stores rather than leaving
# it ``dict[object, object]``. (See docs/README_autotype.md → "Memoization
# Pattern".)


_FIB_CACHE: dict[int, int] = {}


def cached_fib(n: int) -> int:
    if n in _FIB_CACHE:
        return _FIB_CACHE[n]
    result = n if n < 2 else cached_fib(n=n - 1) + cached_fib(n=n - 2)
    _FIB_CACHE[n] = result
    return result


_TITLE_CACHE: dict[str, str] = {}


def cached_title(value: str) -> str:
    if value in _TITLE_CACHE:
        return _TITLE_CACHE[value]
    result: str = value.strip().title()
    _TITLE_CACHE[value] = result
    return result


# =============================================================================
# 66. Override decorator addition — subclass methods missing @override
# =============================================================================
# autotype walks subclass MROs and inserts ``@override`` on every method
# that already exists on a base class. (See docs/README_autotype.md → "Override
# Decorator Addition".) The base ``Greeter`` declares the contract; the two
# subclasses below override ``greet`` / ``__repr__`` *without* the decorator
# at the def-site — the pipeline should add it.


class Greeter:
    """Friendly base whose subclasses customise the greeting verb."""

    def greet(self, name: str) -> str:
        return "hi " + name

    def __repr__(self) -> str:
        return "Greeter()"


class FormalGreeter(Greeter):
    """Subclass overriding both base methods without the decorator."""

    def greet(self, name: str) -> str:
        return "Good day, " + name + "."

    def __repr__(self) -> str:
        return "FormalGreeter()"


class CasualGreeter(Greeter):
    """Subclass overriding only ``greet``."""

    def greet(self, name: str) -> str:
        return "yo " + name


# =============================================================================
# 67. Module-level annotations — unannotated constants
# =============================================================================
# autotype's module-level annotation pass should turn each of these
# right-hand-side-inferred assignments into typed declarations
# (``int`` / ``list[object]`` / ``dict[str, int]`` / ``tuple[int, int, int]``).
# (See docs/README_autotype.md → "Module-Level Annotations".)


_DEFAULT_BATCH_SIZE: Final[int] = 256
_KNOWN_TAGS = ["alpha", "beta", "gamma"]
_PRIORITY_LEVELS = {"low": 1, "medium": 5, "high": 9}
_CHANNEL_RGB = (12, 34, 56)


def batch_summary() -> str:
    return (
        f"batch={_DEFAULT_BATCH_SIZE} tags={_KNOWN_TAGS!r} "
        f"priorities={_PRIORITY_LEVELS!r} channel={_CHANNEL_RGB!r}"
    )


# =============================================================================
# 68. Escaped-newline literals → dedent(text=...) auto-conversion
# =============================================================================
# autowrap's `NewlineAndDedentStringFormatter` rewrites every plain
# string literal containing ``\n`` escapes into a triple-quoted
# ``dedent(text="""…""")`` block, and adds ``from textwrap import
# dedent`` when the module doesn't already import it. The originals
# below are deliberately short-ish multi-line escapes that the
# conversion heuristic considers worth rewriting (more than one ``\n``
# and at least one non-blank line in the value).


def render_html_skeleton() -> str:
    return """\
<html>
  <body>
    <p>placeholder</p>
  </body>
</html>
"""


def render_help_banner() -> str:
    return """\
USAGE: tool [options] FILE

OPTIONS:
  --help    show help
"""


def render_sql_template(table: str) -> str:
    base: str = """\
SELECT id, name, value
FROM TABLE_NAME
WHERE active = TRUE
ORDER BY id;
"""
    return base.replace("TABLE_NAME", table)


class SupportsGt(Protocol):
    """Structural contract requiring ``__gt__``."""

    def __gt__(self, arg0, /) -> bool:
        """Provide the required ``__gt__`` operation.

        Args:
            arg0: TODO.

        Returns:
            TODO."""
        ...


# =============================================================================
# 69. Docstring-extracted type hints — comment-based & doctstring-based
# =============================================================================
# autotype's docstring parser pulls explicit ``Args:`` types out of a Google
# block when the def-site lacks annotations and the docstring carries an
# unambiguous one. (See docs/README_autotype.md → "Docstring Parsing".)


def parse_with_doc_types(raw, retries: SupportsGt):
    """Parse ``raw`` with bounded retries.

    Args:
        raw (str): The raw text to parse — annotation deliberately omitted
            on the ``def`` line so autotype must read the docstring to
            recover the type.
        retries (SupportsGt): Number of times to retry on transient failure.

    Returns:
        list[str]: Parsed tokens.

    """
    attempt: int = 0
    while attempt < retries:
        tokens: ListStr = raw.split(":")
        if tokens:
            return tokens
        attempt += 1
    return []


# =============================================================================
# 70. Decorator awareness in autokwargs — @staticmethod / @classmethod
# =============================================================================
# autokwargs resolves the receiver kind correctly for ``@staticmethod`` and
# ``@classmethod`` calls and adds keyword names even when the caller goes
# through the *class* rather than an instance.
# (See docs/README_autokwargs.md → "Decorator awareness".)


class Registry:
    """Class whose static and class methods are called positionally.

    Attributes:
        label (str): TODO.

    """

    label: str = ""

    @staticmethod
    def stamp(prefix, value):
        return prefix + ":" + value

    @classmethod
    def from_pair(cls, head: str, tail: str) -> Registry:
        instance: Registry = cls()
        instance.label = head + "/" + tail
        return instance


def call_registry() -> tuple[str, Registry]:
    return Registry.stamp("env", "production"), Registry.from_pair("a", "b")


# =============================================================================
# 71. Function-scope magic values — autoinsert local-extraction
# =============================================================================
# When ``magic-values-scope=function`` is set, autoinsert hoists numeric
# literals inside *one* function into a local constant rather than a
# module-level one. The header runs in module-scope so this section is here
# to demonstrate the *expression density* that an inner-scope extraction
# would normalise; switch the header to ``function`` to see the difference.


def physics_step(velocity: float, acceleration: float) -> float:
    drag: float = velocity * 0.97
    push: float = acceleration * 1.21
    floor: float = max(drag + push, 0.0)
    return min(floor, 99.5)


# =============================================================================
# 72. PEP 695 generic functions — autotype on the new type-param syntax
# =============================================================================
# Type-parameter syntax (``def f[T](...)``) lets autotype infer the element
# type from the bound. The body uses ``x`` as if it were ``T`` — no extra
# annotation should be needed at the def site.


def first_of[T](items: list[T]) -> T | None:
    if not items:
        return None
    return items[0]


def pair_keys[K, V](mapping: dict[K, V]) -> list[K]:
    return list(mapping.keys())


# =============================================================================
# 73. TypeAlias hoisting — explicit ``type Foo = ...`` (PEP 695)
# =============================================================================
# autotype recognises PEP 695 type-alias statements and treats the RHS as a
# real type expression when inferring downstream annotations.

type JSONPrimitive = str | int | float | bool | None
type StringList = ListStr


def normalise_primitive(value: JSONPrimitive) -> str:
    return "null" if value is None else str(value)


def join_string_list(parts: StringList, sep: str = ", ") -> str:
    return sep.join(parts)


# =============================================================================
# 74. Async generator — autotype's ``AsyncIterator`` return inference
# =============================================================================
# An ``async def`` whose body uses ``yield`` should be annotated as
# ``AsyncIterator[...]``; the element type is inferred from the yield expr.


async def count_async(limit: int) -> AsyncIterator[int]:
    n = 0
    while n < limit:
        yield n
        n += 1
        await asyncio.sleep(0)


async def collect_async(limit: int) -> ListInt:
    return [value async for value in count_async(limit)]


# =============================================================================
# 75. Context manager protocol — ``__enter__`` / ``__exit__`` self-typing
# =============================================================================
# autotype should annotate ``__enter__`` as returning ``Self`` and ``__exit__``
# as returning ``bool | None`` with the standard exception-info signature.


class Transaction:
    def __init__(self, label: str) -> None:
        self.label = label
        self.entered = False

    def __enter__(self):
        self.entered = True
        return self

    def __exit__(self, exc_type, exc, tb) -> bool | None:
        self.entered = False
        return False


# =============================================================================
# 76. Additional inference stress cases — factories, scopes, overload-like
# flows
# =============================================================================
# These cases intentionally stress places where automatic typing tools commonly
# fall back to ``object`` or accidentally change runtime behavior.


@dataclass
class EventLog:
    """Dataclass whose builtin generic factories stay unparameterized.

    Attributes:
        names (list): TODO.
        counts (dict): TODO.
        seen (set): TODO.

    """

    names: list = field(default_factory=list)
    counts: dict = field(default_factory=dict)
    seen: set = field(default_factory=set)

    def add(self, name, amount=1):
        self.names.append(name)
        self.counts[name] = self.counts.get(name, 0) + amount
        self.seen.add(name)
        return self

    def summary(self):
        return {name: self.counts[name] for name in self.seen}


@dataclass
class KeyValueStore:
    """Stateful generic candidate using one key type and one value type.

    Attributes:
        values (dict): TODO.

    """

    values: dict = field(default_factory=dict)

    def put(self, key, value):
        previous = self.values.get(key)
        self.values[key] = value
        return previous

    def get_or(self, key, default):
        return self.values.get(key, default)

    def keys_list(self):
        return list(self.values.keys())

    def values_list(self):
        return list(self.values.values())


class FluentCounter:
    """Self-returning mutator should infer Self for fluent methods."""

    def __init__(self) -> None:
        self.total = 0

    @classmethod
    def from_values(cls, values):
        instance = cls()
        for value in values:
            instance.add(value)
        return instance

    def add(self, amount):
        self.total += amount
        return self

    def reset(self):
        self.total = 0
        return self


class LazyValue:
    """Property and cached state should keep optional narrowing precise."""

    def __init__(self, raw) -> None:
        self.raw = raw
        self._cached = None

    @property
    def value(self):
        if self._cached is None:
            self._cached = self.raw.strip().lower()
        return self._cached


class Descriptor:
    """Simple descriptor stress case for __get__ and __set__."""

    def __init__(self, default) -> None:
        self.default = default
        self.name = ""

    def __set_name__(self, owner, name) -> None:
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value) -> None:
        instance.__dict__[self.name] = value


class DescriptorUser:
    label = Descriptor("unknown")

    def rename(self, value):
        self.label = value
        return self.label


@contextmanager
def temporary_mapping_value(mapping, key, value):
    """Context manager should infer the yielded previous value.

    Args:
        mapping: TODO.
        key: TODO.
        value: TODO.

    Yields:
        TODO.

    """
    missing = object()
    previous = mapping.get(key, missing)
    mapping[key] = value
    try:
        yield previous if previous is not missing else None
    finally:
        if previous is missing:
            mapping.pop(key, None)
        else:
            mapping[key] = previous


def select_first_present(primary: None, secondary: str, fallback: str) -> str:
    """Identity-preserving union/narrowing across three candidate values.

    Args:
        primary (None): TODO.
        secondary (str): TODO.
        fallback (str): TODO.

    Returns:
        str: TODO.

    """
    if primary is not None:
        return primary
    if secondary is not None:
        return secondary
    return fallback


def transpose_pairs(pairs: list[tuple[str, int]]):
    """Infer tuple element relationships without collapsing to object.

    Args:
        pairs (list[tuple[str, int]]): TODO.

    Returns:
        TODO.

    """
    left = []
    right = []
    for first, second in pairs:
        left.append(first)
        right.append(second)
    return left, right


def group_by_key(rows: ListStr, key_func: Callable[..., object]):
    """Callable return drives dict key type; rows preserve element type.

    Args:
        rows (ListStr): TODO.
        key_func (Callable[..., object]): TODO.

    Returns:
        TODO.

    """
    grouped = {}
    for row in rows:
        key = key_func(row)
        grouped.setdefault(key, []).append(row)
    return grouped


def invert_mapping(mapping: DictInt) -> dict[int, str]:
    """Swap key/value types when values are hashable.

    Args:
        mapping (DictInt): TODO.

    Returns:
        dict[int, str]: TODO.

    """
    return {value: key for key, value in mapping.items()}


def merge_optional_dicts(
    left: DictInt, right: DictInt | None = None
) -> DictInt:
    """Optional dict input should narrow before update.

    Args:
        left (DictInt): TODO.
        right (DictInt | None): TODO.

    Returns:
        DictInt: TODO.

    """
    merged: DictInt = dict(left)
    if right is not None:
        merged.update(right)
    return merged


def safe_index(items: ListInt, index: int, default: int | None = None):
    """Element type should unify with default type only when needed.

    Args:
        items (ListInt): TODO.
        index (int): TODO.
        default (int | None): TODO.

    Returns:
        TODO.

    """
    try:
        return items[index]
    except IndexError:
        return default


def parse_ints_with_errors(
    values: ListStr,
) -> tuple[ListInt, list[tuple[str, str]]]:
    """Exception paths should not poison successful list element type.

    Args:
        values (ListStr): TODO.

    Returns:
        tuple[ListInt, list[tuple[str, str]]]: TODO.

    """
    parsed: ListInt = []
    errors: list[tuple[str, str]] = []
    for value in values:
        try:
            parsed.append(int(value))
        except ValueError as error:
            errors.append((value, str(error)))
    return parsed, errors


def nested_match_payload(payload):
    """Pattern matching should narrow nested dict/list shapes.

    Args:
        payload: TODO.

    Returns:
        TODO.

    """
    match payload:
        case {"kind": "point", "coords": [x, y]}:
            return float(x) + float(y)
        case {"kind": "name", "value": str(name)}:
            return name.title()
        case {"kind": "items", "value": [*items]}:
            return len(items)
        case _:
            return None


def build_typed_dict_like(name: str, age: int, active=True):
    """Repeated literal keys should be candidates for TypedDict inference.

    Args:
        name (str): TODO.
        age (int): TODO.
        active: TODO.

    Returns:
        TODO.

    """
    return {
        "name": name,
        "age": age,
        "active": active,
    }


def read_known_json_user(blob: str):
    """Schema-like validation should refine json.loads object values.

    Args:
        blob (str): TODO.

    Returns:
        TODO.

    Raises:
        TypeError: TODO.

    """
    data = json.loads(s=blob)
    if not isinstance(data, dict):
        msg = "expected object"
        raise TypeError(msg)
    name = data.get("name")
    age = data.get("age")
    if not isinstance(name, str):
        msg = "expected string name"
        raise TypeError(msg)
    if not isinstance(age, int):
        msg = "expected integer age"
        raise TypeError(msg)
    return name, age


def callback_pipeline(value: str, *callbacks):
    """Sequential callable output should feed the next callable input.

    Args:
        value (str): TODO.
        callbacks: TODO.

    Returns:
        TODO.

    """
    current = value
    for callback in callbacks:
        current = callback(current)
    return current


def make_counter_closure(start: int = 0):
    """Closure variable mutation should preserve numeric type.

    Args:
        start (int): TODO.

    Returns:
        TODO.

    """
    total = start

    def add(amount):
        nonlocal total
        total += amount
        return total

    return add


def make_registry():
    """Nested functions stored in dict should preserve callable returns.

    Returns:
        TODO.

    """

    def as_upper(value):
        return value.upper()

    def as_length(value: Sized) -> int:
        return len(value)

    return {
        "upper": as_upper,
        "length": as_length,
    }


P = ParamSpec("P")
R = TypeVar("R")


def add_logging(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that prints the wrapped callable's name before forwarding.

    Demonstrates the v4 §3 Target 1 pattern: a function-shaped decorator
    that preserves the wrapped callable's full signature through a
    nested ``wrapper`` that forwards both positional and keyword
    argument packs. The ParamSpec promotion pass should rewrite this
    as ``add_logging[**P, R](func: Callable[P, R]) -> Callable[P, R]``
    with the wrapper typed as ``(*args: P.args, **kwargs: P.kwargs) -> R``.

    Args:
        func (Callable[P, R]): TODO.

    Returns:
        Callable[P, R]: TODO.

    """

    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def trace_method(func):
    """Method decorator preserving the bound-method signature.

    Demonstrates the v5 §3 Target 2 pattern: a wrapper whose first
    positional parameter is the bound ``self``, followed by the
    forwarded ``*args``/``**kwargs`` pack. The ParamSpec method-
    decorator promotion pass should rewrite this as
    ``trace_method[SelfT, **P, R](func: Callable[Concatenate[SelfT, P], R])``
    so the bound receiver's type is preserved through ``Concatenate``.

    Args:
        func: TODO.

    Returns:
        TODO.

    """

    def wrapper(self, *args, **kwargs):
        return func(self, *args, **kwargs)

    return wrapper


# =============================================================================
# 25. TypeVarTuple stress fixtures (v4 §4 — inference deferred, fixtures only)
# =============================================================================
# These two functions are the canonical variadic-tuple-pack and
# variadic-callback-pack patterns that future TypeVarTuple inference
# work must distinguish from ordinary homogeneous ``*args``. They
# are present in the demo as stress fixtures: the inference pass
# does not yet rewrite them, but their continued presence (and the
# basedpyright clean status of the generated output) is the
# regression gate for the upcoming TypeVarTuple bundle.


def rotate_left[T, *Ts](
    items: tuple[T, *Ts],
) -> tuple[*Ts, T]:
    """Rotate a tuple left one position while preserving its element types.

    Demonstrates ``TypeVarTuple`` shape-preservation: the return type
    re-orders the pack so the first element moves to the end while
    each non-first element keeps its precise type. This is the
    smallest test that distinguishes ``TypeVarTuple`` from
    homogeneous ``tuple[T, ...]``.

    Args:
        items (tuple[T, *Ts]): TODO.

    Returns:
        tuple[*Ts, T]: TODO.

    """
    return (*items[1:], items[0])


def call_with_args[*Ts, R](
    callback: Callable[[*Ts], R],
    *args: *Ts,
) -> R:
    """Forward a positional pack to a callback typed by the same pack.

    Demonstrates ``TypeVarTuple`` for callable forwarding: the
    ``*Ts`` pack on both the callback's parameter list and the
    outer ``*args`` ensures the caller cannot pass a positional
    shape the callback cannot accept. Distinct from ``ParamSpec``,
    which forwards a *signature* including keyword arguments.

    Args:
        callback (Callable[[*Ts], R]): TODO.
        args (*Ts): TODO.

    Returns:
        R: TODO.

    """
    return callback(*args)


def sum_values(*values: float) -> float:
    """Sum a homogeneous variadic ``float`` pack.

    Negative ``TypeVarTuple`` fixture: ``*values: float`` is a
    homogeneous pack, so a future ``TypeVarTuple`` inference pass
    must leave it verbatim and NOT promote it to ``*Ts``. v5 §5
    requires this distinction; the regression gate is in

    :class:`TestV5TypeVarTupleNegativeFixture`.

    :param values: TODO.
    :type values: float

    :return: TODO.
    :rtype: float

    """
    return sum(values)


async def async_fetch_one(name, delay=0):
    """Coroutine result type should survive gather/create_task.

    Args:
        name: TODO.
        delay: TODO.

    Returns:
        TODO.

    """
    await asyncio.sleep(delay)
    return {"name": name, "size": len(name)}


async def async_fetch_many(names: ListStr):
    tasks = [asyncio.create_task(async_fetch_one(name)) for name in names]
    return await asyncio.gather(*tasks)


def path_roundtrip(path: str):
    """PathLike/string inputs often need pathlib-aware inference.

    Args:
        path (str): TODO.

    Returns:
        TODO.

    """
    resolved = Path(path).expanduser()
    return resolved.name, resolved.suffix, resolved.parent


def regex_groupdict(text: str):
    """Regex match narrowing should refine groupdict return.

    Args:
        text (str): TODO.

    Returns:
        TODO.

    """
    match: Match[str] | None = re.match(
        pattern="(?P<name>[a-z]+)-(?P<id>\\d+)$", string=text
    )
    if match is None:
        return {}
    return match.groupdict()


def bytes_text_boundary(data, encoding="utf-8") -> str | bytes:
    """Bytes/str conversion should not collapse to object.

    Args:
        data: TODO.
        encoding: TODO.

    Returns:
        str | bytes: TODO.

    """
    if isinstance(data, bytes):
        return data.decode(encoding)
    return data.encode(encoding)


def variadic_numeric_sum(*values: int, scale: int = 1):
    """Variadic args plus keyword-only numeric parameter.

    Args:
        values (int): TODO.
        scale (int): TODO.

    Returns:
        TODO.

    """
    total = 0
    for value in values:
        total += value
    return total * scale


class Plugin(Protocol):
    def run(self, payload) -> None:
        """Run the plugin against ``payload``.

        Args:
            payload: TODO.

        """
        ...


class EchoPlugin:
    def run(self, payload: T) -> T:
        return payload


class SizePlugin:
    def run(self, payload: Sized) -> int:
        return len(payload)


def run_plugin(plugin, payload: str):
    """Structural protocol candidate from repeated .run() calls.

    Args:
        plugin: TODO.
        payload (str): TODO.

    Returns:
        TODO.

    """
    return plugin.run(payload)


def stress_smoke_calls():
    """Return deterministic outputs for the additional stress section.

    Returns:
        TODO.

    """
    event_log = EventLog().add("a").add("b", 2).add("a", 3)
    store: KeyValueStore = KeyValueStore()
    previous = store.put("x", 1)
    store.put("y", 2)
    counter = FluentCounter.from_values([1, 2, 3]).add(4)
    lazy: LazyValue = LazyValue("  Hello  ")
    descriptor_value = DescriptorUser().rename("Ada")
    mapping = {"a": 1}
    with temporary_mapping_value(mapping, "a", 9) as old_value:
        temporary_value = mapping["a"]
    add = make_counter_closure(start=10)
    registry = make_registry()
    return {
        "event_log": event_log.summary(),
        "store_previous": previous,
        "store_keys": store.keys_list(),
        "store_values": store.values_list(),
        "counter": counter.total,
        "lazy": lazy.value,
        "descriptor": descriptor_value,
        "temporary": (old_value, temporary_value, mapping["a"]),
        "select": select_first_present(
            primary=None, secondary="secondary", fallback="fallback"
        ),
        "transpose": transpose_pairs(pairs=[("a", 1), ("b", 2)]),
        "group": group_by_key(rows=["aa", "b"], key_func=len),
        "invert": invert_mapping(mapping={"a": 1, "b": 2}),
        "merge": merge_optional_dicts(left={"a": 1}, right={"b": 2}),
        "safe_index": safe_index(items=[1, 2], index=9, default=-1),
        "parsed": parse_ints_with_errors(values=["1", "x", "3"]),
        "match_point": nested_match_payload(
            payload={"kind": "point", "coords": [1, 2]}
        ),
        "typed_dict_like": build_typed_dict_like(name="Ada", age=37),
        "json_user": read_known_json_user(blob='{"name":"Ada","age":37}'),
        "callback": callback_pipeline(" ada ", str.strip, str.title),
        "closure": (add(5), add(2)),
        "registry": (registry["upper"]("ada"), registry["length"]("ada")),
        "async_many": asyncio.run(async_fetch_many(names=["aa", "bbb"])),
        "path": path_roundtrip(path="demo.py"),
        "regex": regex_groupdict(text="abc-123"),
        "boundary_text": bytes_text_boundary(data=b"abc"),
        "boundary_bytes": bytes_text_boundary(data="abc"),
        "variadic": variadic_numeric_sum(1, 2, 3, scale=2),
        "plugin_echo": run_plugin(plugin=EchoPlugin(), payload="x"),
        "plugin_size": run_plugin(plugin=SizePlugin(), payload="abcd"),
    }


# =============================================================================
# 77. Demo entry point — printed when the pipeline auto-runs the file
# =============================================================================


def _demo_main() -> None:
    """Smoke-call a handful of items so the auto-run emits useful output."""
    _demo_extras()
    time.sleep(1)


def _demo_extras() -> None:
    """Smoke-call the PEP 695 / async / context-manager sections."""
    with Transaction("demo"):
        pass


if __name__ == "__main__":
    _demo_main()
