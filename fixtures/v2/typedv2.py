"""Strictly typed inference stress suite derived from untypedv2.py."""

# Copyright (c) 2026 Contributors

# autowrap's normalise-to-google pass currently strips structured
# ``Args:``/``Returns:`` blocks when the descriptions look like placeholders;
# keep it disabled so the templated docstrings emitted by ``add_doc_strings``
# survive intact and existing real docstrings are left alone too.
from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import Task, create_task, gather, sleep, wait_for
from asyncio import run as asyncio_run
from collections import Counter
from collections.abc import Callable, Generator, Hashable, Iterable, Mapping
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum, auto
from functools import lru_cache, reduce
from itertools import accumulate, chain, groupby, islice, takewhile
from json import dumps, loads
from math import sqrt
from pathlib import Path
from re import Match, Pattern, search, split, sub
from re import compile as re_compile
from re import match as re_match
from subprocess import CompletedProcess, run
from sys import executable, stdout
from textwrap import dedent
from time import monotonic
from time import sleep as time_sleep
from typing import (
    IO,
    TYPE_CHECKING,
    ClassVar,
    Concatenate,
    Final,
    NamedTuple,
    Protocol,
    Self,
    TextIO,
    TypedDict,
    TypeGuard,
    cast,
    final,
    overload,
    override,
)

if TYPE_CHECKING:
    from collections.abc import (
        AsyncGenerator,
        AsyncIterator,
        Awaitable,
        MutableMapping,
        Sequence,
        Sized,
    )
    from types import TracebackType


type StringList = list[str]
type StringTransform = Callable[[str], str]
type StringToInt = dict[str, int]
type StringIntPair = tuple[str, int]
type StringCountPairs = list[StringIntPair]
type FloatList = list[float]
type OptionalString = str | None
type OptionalInt = int | None
type OptionalFloat = float | None
type BytesOrText = bytes | str
type IntegerGenerator = Generator[int]
type StringToString = dict[str, str]
type FloatOrStr = float | str
type StrCounter = Counter[str]
type StrIterable = Iterable[str]
type PToRCallable[**P, R] = Callable[P, R]
type OptionalTreeNode = TreeNode | None
type FloatListList = list[FloatList]
type IntListOrInt = list[int] | int
type StrPair = tuple[str, str]
type KToTListMap[K, T] = dict[K, list[T]]
type MappingStrInt = Mapping[str, int]
type OptionalStrMatch = Match[str] | None
type StrOrIntOrFloat = str | int | float
type JSONPrimitive = StrOrIntOrFloat | bool | None
type JSONValue = JSONPrimitive | list[JSONValue] | dict[str, JSONValue]
type JSONObject = dict[str, JSONValue]
type OptionalJSONValue = JSONValue | None
type NameTToFloatMap[NameT] = dict[NameT, float]
type IntToIntCallable = Callable[[int], int]
type StrToIntListMap = dict[str, list[int]]
type TupleIntStrSet = tuple[int, set[str]]
type DescriptorUserType = type[DescriptorUser]
type StrPairList = list[StrPair]
type TupleStrStrPath = tuple[str, str, Path]
type AsyncFetchResultList = list[AsyncFetchResult]
type FloatToFloatCallable = Callable[[float], float]
type StrToOptionalStringMap = dict[str, OptionalString]
type TupleIntStrSetList = list[TupleIntStrSet]
type StringToIntTagGroups = dict[str, TupleIntStrSetList]
type FloatOrIntOrOptionalString = float | int | OptionalString
type TupleStrOrIntOrFloatStr = tuple[StrOrIntOrFloat, str]
type BoundMethodCallable[SelfT, **P, R] = Callable[Concatenate[SelfT, P], R]
type TupleStrOrIntOrFloatStrList = list[TupleStrOrIntOrFloatStr]
type ParsedIntegers = tuple[list[int], TupleStrOrIntOrFloatStrList]


class FunctionRegistry(TypedDict):
    """Literal-key callback registry produced by ``make_registry``.

    Attributes:
        upper (Callable[[str], str]): TODO.
        length (Callable[[str], int]): TODO.

    """

    upper: StringTransform
    length: Callable[[str], int]


class UserRecord(TypedDict):
    """Stable user record with a fixed set of keys.

    Attributes:
        name (str): TODO.
        age (int): TODO.
        active (bool): TODO.

    """

    name: str
    age: int
    active: bool


class AsyncFetchResult(TypedDict):
    """Resource label and measured length.

    Attributes:
        name (str): TODO.
        size (int): TODO.

    """

    name: str
    size: int


class StressSmokeResults(TypedDict):
    """Results from the deterministic inference stress calls.

    All fields are derived from the original individual producers.

    Attributes:
        event_log (dict[str, float]): TODO.
        store_previous (int | None): TODO.
        store_keys (list[str]): TODO.
        store_values (list[int]): TODO.
        counter (int): TODO.
        lazy (str): TODO.
        descriptor (str): TODO.
        temporary (tuple[int | None, int, int]): TODO.
        select (str): TODO.
        transpose (tuple[list[str], list[int]]): TODO.
        group (dict[int, list[str]]): TODO.
        invert (dict[int, str]): TODO.
        merge (dict[str, int]): TODO.
        safe_index (int | None): TODO.
        parsed (ParsedIntegers): TODO.
        match_point (float | int | str | None): TODO.
        typed_dict_like (UserRecord): TODO.
        json_user (tuple[str, int]): TODO.
        callback (str): TODO.
        closure (tuple[float, float]): TODO.
        registry (tuple[str, int]): TODO.
        async_many (list[AsyncFetchResult]): TODO.
        path (tuple[str, str, Path]): TODO.
        regex (dict[str, str | None]): TODO.
        boundary_text (bytes | str): TODO.
        boundary_bytes (bytes | str): TODO.
        variadic (float): TODO.
        plugin_echo (str): TODO.
        plugin_size (int): TODO.

    """

    event_log: dict[str, float]
    store_previous: OptionalInt
    store_keys: StringList
    store_values: list[int]
    counter: int
    lazy: str
    descriptor: str
    temporary: tuple[OptionalInt, int, int]
    select: str
    transpose: tuple[StringList, list[int]]
    group: dict[int, StringList]
    invert: dict[int, str]
    merge: StringToInt
    safe_index: OptionalInt
    parsed: ParsedIntegers
    match_point: FloatOrIntOrOptionalString
    typed_dict_like: UserRecord
    json_user: StringIntPair
    callback: str
    closure: tuple[float, float]
    registry: StringIntPair
    async_many: AsyncFetchResultList
    path: TupleStrStrPath
    regex: StrToOptionalStringMap
    boundary_text: BytesOrText
    boundary_bytes: BytesOrText
    variadic: float
    plugin_echo: str
    plugin_size: int


@final
class Constants:
    """Hold immutable configuration values and shared caches.

    Attributes:
        int_18 (Final[int]): TODO.
        int_5 (Final[int]): TODO.
        int_neg_40 (Final[int]): TODO.
        int_100 (Final[int]): TODO.
        int_90 (Final[int]): TODO.
        int_80 (Final[int]): TODO.
        int_70 (Final[int]): TODO.
        int_60 (Final[int]): TODO.
        int_24 (Final[int]): TODO.
        int_12 (Final[int]): TODO.
        int_6 (Final[int]): TODO.
        int_2 (Final[int]): TODO.
        int_3 (Final[int]): TODO.
        int_500 (Final[int]): TODO.
        int_20 (Final[int]): TODO.
        int_950 (Final[int]): TODO.
        int_850 (Final[int]): TODO.
        int_750 (Final[int]): TODO.
        int_600 (Final[int]): TODO.
        int_10000 (Final[int]): TODO.
        int_50000 (Final[int]): TODO.
        int_200000 (Final[int]): TODO.
        int_4 (Final[int]): TODO.
        int_800 (Final[int]): TODO.
        int_6800 (Final[int]): TODO.
        int_42800 (Final[int]): TODO.
        int_1024 (Final[int]): TODO.
        long_literal (Final[str]): TODO.
        fib_cache (Final[dict[int, int]]): TODO.
        title_cache (Final[dict[str, str]]): TODO.
        default_batch_size (Final[int]): TODO.
        known_tags (Final[list[str]]): TODO.
        priority_levels (Final[dict[str, int]]): TODO.
        channel_rgb (Final[tuple[int, int, int]]): TODO.

    """

    int_18: Final[int] = 18
    int_5: Final[int] = 5
    int_neg_40: Final[int] = -40
    int_100: Final[int] = 100
    int_90: Final[int] = 90
    int_80: Final[int] = 80
    int_70: Final[int] = 70
    int_60: Final[int] = 60
    int_24: Final[int] = 24
    int_12: Final[int] = 12
    int_6: Final[int] = 6
    int_2: Final[int] = 2
    int_3: Final[int] = 3
    int_500: Final[int] = 500
    int_20: Final[int] = 20
    int_950: Final[int] = 950
    int_850: Final[int] = 850
    int_750: Final[int] = 750
    int_600: Final[int] = 600
    int_10000: Final[int] = 10000
    int_50000: Final[int] = 50000
    int_200000: Final[int] = 200000
    int_4: Final[int] = 4
    int_800: Final[int] = 800
    int_6800: Final[int] = 6800
    int_42800: Final[int] = 42800
    int_1024: Final[int] = 1024
    long_literal: Final[str] = (
        "lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua, ut "
        "enim ad minim veniam"
    )
    fib_cache: Final[dict[int, int]] = {}
    title_cache: Final[StringToString] = {}
    default_batch_size: Final[int] = 256
    known_tags: Final[StringList] = ["alpha", "beta", "gamma"]
    priority_levels: Final[StringToInt] = {"low": 1, "medium": 5, "high": 9}
    channel_rgb: Final[tuple[int, int, int]] = (12, 34, 56)


def aprint(
    *args: object,
    sep: OptionalString = None,
    end: OptionalString = None,
    file: str | Path | TextIO | None = None,
    mode: str = "a",
    flush: bool = False,
) -> None:
    """Mimic print() using write(), optionally writing to a file path.

    Args:
        sep (str | None): TODO.
        end (str | None): TODO.
        file (str | Path | TextIO | None): TODO.
        mode (str): TODO.
        flush (bool): TODO.
        *args (object): TODO.

    """
    stream: IO[str]
    with (
        Path(file).open(mode=mode, encoding="utf-8")
        if isinstance(file, str | Path)
        else nullcontext(enter_result=file or stdout)
    ) as stream:
        _ = stream.write(
            (sep if sep is not None else " ").join(map(str, args))
            + (end if end is not None else "\n"),
        )
        if flush:
            _ = stream.flush()


# =============================================================================
# 1. Docstring style normalisation — four flavours of one function
# =============================================================================
# The normaliser should land all four below in Google style configured by the
# header ``# AUTOTYPE: docstrings-format=google``.


def google_style(
    names: StrIterable,
    *,
    keep_empty: bool = False,
) -> StringList:
    """Summarise a sequence of names.

    Args:
        names (Iterable[str]): Sequence of raw names that may need whitespace
            cleanup and title casing.
        keep_empty (bool): Whether empty items should be preserved
            after normalization.

    Returns:
        Normalized names ready for display.

    Raises:
        ValueError: If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def numpy_style(
    names: StrIterable,
    *,
    keep_empty: bool = False,
) -> StringList:
    """Summarise a sequence of names.

    Args:
        names (Iterable[str]): Sequence of raw names that may need whitespace
            cleanup and title casing.
        keep_empty (bool): Whether empty items should be preserved
            after normalization.

    Returns:
        Normalized names ready for display.

    Raises:
        ValueError: If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def rest_style(
    names: StrIterable,
    *,
    keep_empty: bool = False,
) -> StringList:
    """Summarise a sequence of names.

    Args:
        names (Iterable[str]): Sequence of raw names that may need whitespace
        keep_empty (bool): Whether empty items should be preserved.

    Returns:
        Normalized names ready for display.

    Raises:
        ValueError: If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def github_style(
    names: StrIterable,
    *,
    keep_empty: bool = False,
) -> StringList:
    """Summarise a sequence of names.

    Args:
        names (Iterable[str]): Sequence of raw names that may need whitespace
        cleanup and title casing.
        keep_empty (bool): Whether empty items should be preserved.

    Returns:
        Normalized names ready for display.

    Raises:
        ValueError: If all names are empty and keep_empty is False.

    """
    return [n.strip() for n in names if keep_empty or n.strip()]


def missing_docstring_target(value: object, repeat: int = 2) -> str:
    """Return missing docstring target.

    Args:
        value (object): TODO.
        repeat (int): TODO.

    Returns:
        str: TODO.

    """
    return str(object=value) * repeat


# =============================================================================
# 2. Long single-line docstring → paragraph-wrapped
# =============================================================================


def long_single_line_doc[T](value: T) -> T:
    """Describe a deliberately long single-line summary that exceeds the.

    configured line width so the wrapper has to fold it across multiple
    physical lines while preserving the semantic punctuation and the
    trailing period at the end of the sentence.

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
    3. third item using a different separator (normaliser unifies)
    """
    return


# =============================================================================
# 4. Colon-aligned definitions and ruler underlines
# =============================================================================


def colon_aligned_and_rulers(a: float, b: float, c: float) -> float:
    """Show colon-introduced definition alignment and ruler-line tidy.

    Args:
        a (float): a short description that should align with siblings
        b (float): another one whose name is longer; the colon-alignment
            pass should pad ``a`` so its colon column matches.
        c (float): a third with a longer name still and a multi-line body
            wrapping the rest of the prose under the colon column.

    Attributes:
        items: underlined section heading where the ``----`` underline
            should be normalised to match the heading width exactly.

    Methods:
        run: another underlined section header.

    Returns:
            float: TODO.

    """
    return a + b + c


# =============================================================================
# 5. Code-block preservation, URL preservation, backtick names
# =============================================================================


def code_blocks_and_urls() -> None:
    """Preserve fenced code and URLs verbatim while wrapping prose.

    The wrapper should NOT touch the fenced block below,
    nor split URLs across lines. Inline backtick names like
    ``my_function`` should be preserved as visual emphasis.

    Example:
        result = my_function(value=42)
        print(result.upper())

    Reference:
    https://example.com/very/long/path/that/should/not/be/broken?query=1&also=2

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
# This is a deliberately long block comment that spans many lines and
# would, without the comment wrapper, leave a stretched physical line.
# The wrapper should fold all these consecutive lines into a single re-
# flowed paragraph with the leading ``#`` preserved on every emitted
# line so the visual effect is consistent. A separate paragraph below
# the blank line should NOT be merged into the one above because the
# wrapper respects blank-line boundaries.


# =============================================================================
# 8. Long string assignments → parenthesised implicit concatenation
# =============================================================================
# =============================================================================
# 9. Inference feature 1 — SSA local re-typing
# =============================================================================


def union_via_reassignment(*, flag: bool) -> int | str:
    """Return union via reassignment.

    Args:
        flag (bool): TODO.

    Returns:
        int | str: TODO.

    """
    probe: int | str = 0
    if flag:
        probe = "fallback"
    return probe


# =============================================================================
# 10. Inference feature 2 — `is None` / `is not None` narrowing
# =============================================================================


def narrow_via_is_none(value: Sized | None) -> int:
    """Return narrow via is none.

    Args:
        value (Sized | None): TODO.

    Returns:
        int: TODO.

    """
    if value is None:
        return 0
    return len(value) * 2


# =============================================================================
# 11. Inference feature 3 — receiver chain inference
# =============================================================================


def chain_inference(p: str) -> tuple[str, StringList]:
    """Return chain inference.

    Args:
        p (str): TODO.

    Returns:
        tuple[str, list[str]]: TODO.

    """
    body: str = Path(p).read_text()
    lines: StringList = body.splitlines()
    upper_first: str = lines[0].upper() if lines else ""
    raw: bytes = Path(p).read_bytes()
    text: str = raw.decode()
    return upper_first, text.split()


# =============================================================================
# 12. Inference feature 4 — kwarg backflow at call sites
# =============================================================================


def helper_backflow(name: str, count: int, prefix: str) -> str:
    """Return helper backflow.

    Args:
        name (str): TODO.
        count (int): TODO.
        prefix (str): TODO.

    Returns:
        str: TODO.

    """
    return f"{prefix}{name}:{count}"


def caller_with_kwargs() -> str:
    """Return caller with kwargs.

    Returns:
        str: TODO.

    """
    return helper_backflow(name="alice", count=42, prefix=">> ")


# =============================================================================
# 13. Inference feature 5 — Literal narrowing from `==` / `match`
# =============================================================================


def colour_to_hex(colour: str) -> str:
    """Return colour to hex.

    Args:
        colour (str): TODO.

    Returns:
        str: TODO.

    """
    if colour == "red":
        return "#ff0000"
    if colour == "green":
        return "#00ff00"
    if colour == "blue":
        return "#0000ff"
    return "#000000"


def http_status_word(code: object) -> str:
    """Return http status word.

    Args:
        code (object): TODO.

    Returns:
        str: TODO.

    """
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


def build_user_record(name: str, age: int) -> UserRecord:
    """Return build user record.

    Args:
        name (str): TODO.
        age (int): TODO.

    Returns:
        UserRecord: TODO.

    """
    if not name:
        return {"name": "anonymous", "age": 0, "active": False}
    if age < Constants.int_18:
        return {"name": name, "age": age, "active": False}
    return {"name": name, "age": age, "active": True}


# =============================================================================
# 15. autokwargs — deep inspection of stdlib + workspace receivers
# =============================================================================
# - ``f.write_text("hi", encoding="utf-8")`` becomes ``data="hi"`` -
# ``c.most_common(2)`` becomes ``n=2``


def writes_path(target_dir: str) -> str:
    """Return writes path.

    Args:
        target_dir (str): The target dir value passed to the call.

    Returns:
        str: TODO.

    """
    f: Path = Path(target_dir) / "out.txt"
    _ = f.write_text(data="hello world", encoding="utf-8")
    return f.read_text()


def top_words(text: str, n: int) -> StringCountPairs:
    """Return top words.

    Args:
        text (str): TODO.
        n (int): TODO.

    Returns:
        list[tuple[str, int]]: TODO.

    """
    c: StrCounter = Counter(text.split())
    return c.most_common(n=n)


# =============================================================================
# 16. Autosort — methods out of canonical order
# =============================================================================


class OutOfOrderClass:
    """Methods intentionally misordered to exercise autosort."""

    def __init__(self, x: int) -> None:
        """Return init.

        Args:
            x (int): TODO.

        """
        self._x: int = x

    @override
    def __repr__(self) -> str:
        """Return repr.

        Returns:
            str: TODO.

        """
        return f"OutOfOrderClass({self._x!r})"

    @property
    def value(self) -> int:
        """Return value.

        Returns:
            int: TODO.

        """
        return self._x

    @classmethod
    def from_int(cls, value: int) -> Self:
        """Return from int.

        Args:
            value (int): TODO.

        Returns:
            Self: TODO.

        """
        return cls(value)

    @staticmethod
    def banner() -> str:
        """Return banner.

        Returns:
            str: TODO.

        """
        return "OutOfOrderClass"

    def helper(self) -> int:
        """Return helper.

        Returns:
            int: TODO.

        """
        return self._x


# =============================================================================
# 17. autorestore — lint-ignore positions survive transformation
# =============================================================================
# Each suppression below is on a line that the pipeline will rewrap;
# autorestore should reposition the comment onto the new line where the
# diagnostic still fires.


async def with_timeout[T](
    coro: Awaitable[T],
    timeout: OptionalFloat,
) -> T | None:
    """Run coro with a timeout; return None on expiry.

    Args:
        coro (Awaitable[T]): TODO.
        timeout (float | None): TODO.

    Returns:
        T | None: TODO.

    """
    try:
        return await wait_for(fut=coro, timeout=timeout)
    except TimeoutError:
        return None


def narrow_with_assert(x: float) -> float:
    """Use assert isinstance to narrow x to numeric.

    Args:
        x (float): TODO.

    Returns:
        float: TODO.

    """
    assert isinstance(x, (int, float))  # noqa: S101
    return x + 1


@contextmanager
def timer(label: object) -> Generator[None]:
    """Print elapsed time around a ``with`` block.

    Args:
        label (object): TODO.

    Yields:
        None: TODO.

    """
    start: float = monotonic()
    try:
        yield
    finally:
        elapsed: float = monotonic() - start
        aprint(f"{label}: {elapsed:.4f}s")


def yield_in_loop(n: int) -> IntegerGenerator:
    """Yield-in-for that ruff would suggest converting to yield-from.

    Args:
        n (int): TODO.

    Yields:
        int: TODO.

    """
    i: int
    for i in range(n):  # noqa: UP028
        yield i


# =============================================================================
# 18. Generators + async generator + Protocol + NamedTuple + TypedDict
# =============================================================================


def count_up(n: int) -> IntegerGenerator:
    """Yield integers from 0 up to n-1.

    Args:
        n (int): TODO.

    Yields:
        int: TODO.

    """
    yield from range(n)


async def async_count(n: int) -> AsyncGenerator[int]:
    """Async generator yielding integers.

    Args:
        n (int): TODO.

    Yields:
        int: TODO.

    """
    i: int
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

    def dot(self, other: Vector3) -> float:
        """Return dot.

        Args:
            other (Vector3): TODO.

        Returns:
            float: TODO.

        """
        return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass
class Stack[T]:
    """Stack backed by a list.

    Attributes:
        items (list[T]): TODO.

    """

    items: list[T] = field(default_factory=list)

    def pop(self) -> T | None:
        """Return pop.

        Returns:
            T | None: TODO.

        """
        return self.items.pop() if self.items else None

    def push(self, item: T) -> None:
        """Return push.

        Args:
            item (T): TODO.

        """
        _ = self.items.append(item)


class Sizeable(Protocol):
    """Anything with __len__."""

    def __len__(self) -> int:
        """Return the container length.

        Returns:
            int: TODO.

        """
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


def first_long_token(text: str) -> OptionalString:
    """Return first long token.

    Args:
        text (str): TODO.

    Returns:
        str | None: TODO.

    """
    return next((t for t in text.split() if len(t) > Constants.int_5), None)


def keep_unique[T](items: Iterable[T]) -> list[T]:
    """Return keep unique.

    Args:
        items (Iterable[T]): TODO.

    Returns:
        list[T]: TODO.

    """
    seen: set[T] = set()
    return [x for x in items if not (x in seen or seen.add(x))]


def describe_action(payload: JSONObject) -> OptionalString:
    """Return describe action.

    Args:
        payload (dict[str, JSONValue]): TODO.

    Returns:
        str | None: TODO.

    """
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
        """Return init."""
        self._parts: StringList = []

    def add(self, x: str) -> Self:
        """Return add.

        Args:
            x (str): TODO.

        Returns:
            Self: TODO.

        """
        _ = self._parts.append(x)
        return self

    def build(self) -> str:
        """Return build.

        Returns:
            str: TODO.

        """
        return ":".join(map(str, self._parts))


# =============================================================================
# 22. Deeply nested bullet alignment + Returns with multiple typed entries
# =============================================================================


def deeply_nested_bullets() -> tuple[int, StringList, StringToInt]:
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

    Args:
        first: a short name to align against
        second_much_longer_name: longer sibling whose colon
            column should anchor the alignment for both items
        third: a third item with a multi-line description that should
            re-wrap under the colon column without disturbing the
            bullets below.

    Returns:
        tuple: A 3-tuple containing
            - ``int``: the count of top-level items
            - ``list[str]``: the flattened bullet bodies in DFS order
            - ``dict[str, int]``: per-marker-style frequency map

    Raises:
        ValueError: never, but documented to exercise the
            Raises section alignment and multi-line body wrapping.

    """
    return 0, [], {}


# =============================================================================
# 23. Inference through imported non-builtin (stdlib) modules
# =============================================================================
# Exercises receiver-chain inference across ``json``, ``re``, ``subprocess``
# and Path so autotype/autokwargs trace return types through module APIs.


def parse_user_json(blob: str) -> tuple[OptionalJSONValue, OptionalJSONValue]:
    """Return parse user json.

    Args:
        blob (str): TODO.

    Returns:
        tuple[JSONValue | None, JSONValue | None]: TODO.

    """
    data: JSONObject = cast(
        typ="dict[str, JSONValue]",
        val=loads(s=blob),
    )
    name: OptionalJSONValue = data.get("name")
    age: OptionalJSONValue = data.get("age", 0)
    return name, age


def extract_first_int(text: str) -> OptionalInt:
    """Return extract first int.

    Args:
        text (str): TODO.

    Returns:
        int | None: TODO.

    """
    match: OptionalStrMatch = search(pattern=r"\d+", string=text)
    if match is None:
        return None
    return int(match.group(0))


def normalise_whitespace(text: str) -> str:
    """Return normalise whitespace.

    Args:
        text (str): TODO.

    Returns:
        str: TODO.

    """
    pattern: Pattern[str] = re_compile(pattern=r"\s+")
    return pattern.sub(repl=" ", string=text).strip()


def list_python_versions() -> StringIntPair:
    """Return list python versions.

    Returns:
        tuple[str, int]: TODO.

    """
    proc: CompletedProcess[str] = run(
        args=[executable, "--version"],
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


def length_doubled(text: str) -> int:
    """Return length doubled.

    Args:
        text (str): TODO.

    Returns:
        int: TODO.

    """
    doubled: int = len(text) * 2
    return doubled


def coerce_in_branches(*, flag: bool, raw: str) -> FloatOrStr:
    """Return coerce in branches.

    Args:
        flag (bool): TODO.
        raw (str): TODO.

    Returns:
        float | str: TODO.

    """
    if flag:
        coerced: FloatOrStr = float(raw)
    else:
        coerced = str(object=raw).upper()
    return coerced


class ScopeMixer:
    """Class attribute and method-local exercise distinct scopes.

    Attributes:
        counter (int): TODO.

    """

    counter: int = 0

    def bump(self, delta: int) -> int:
        """Return bump.

        Args:
            delta (int): TODO.

        Returns:
            int: TODO.

        """
        next_value: int = self.counter + delta
        self.counter = next_value
        return next_value

    def reset(self) -> int:
        """Return reset.

        Returns:
            int: TODO.

        """
        self.counter = 0
        return self.counter


# =============================================================================
# 25. Magic-number injection — many int/float literals in expressions
# =============================================================================
# autoinsert should hoist these into named module-level constants.


def temperature_score(celsius: float) -> float:
    """Return temperature score.

    Args:
        celsius (float): TODO.

    Returns:
        float: TODO.

    """
    if celsius < Constants.int_neg_40:
        return 0.0
    if celsius < 0:
        return celsius * 0.5 + 50
    if celsius < Constants.int_100:
        return celsius * 1.5 + 75
    return 300.0


def grade_from_score(score: int) -> str:
    """Return grade from score.

    Args:
        score (int): TODO.

    Returns:
        str: TODO.

    """
    if score >= Constants.int_90:
        return "A"
    if score >= Constants.int_80:
        return "B"
    if score >= Constants.int_70:
        return "C"
    if score >= Constants.int_60:
        return "D"
    return "F"


def compute_discount(price: float, units: int) -> float:
    """Return compute discount.

    Args:
        price (float): TODO.
        units (int): TODO.

    Returns:
        float: TODO.

    """
    if units >= Constants.int_24:
        return price * 0.65
    if units >= Constants.int_12:
        return price * 0.8
    if units >= Constants.int_6:
        return price * 0.9
    return price


# =============================================================================
# 26. autokwargs — positional calls promoted to keyword on stdlib + workspace
# =============================================================================


def write_log_file(target_dir: str, payload: object) -> Path:
    """Return write log file.

    Args:
        target_dir (str): The target dir value passed to the call.
        payload (object): TODO.

    Returns:
        Path: TODO.

    """
    path: Path = Path(target_dir) / "log.json"
    _ = path.write_text(data=dumps(obj=payload, indent=2), encoding="utf-8")
    return path


def replace_tokens(text: str, token: str, replacement: str) -> str:
    """Return replace tokens.

    Args:
        text (str): TODO.
        token (str): TODO.
        replacement (str): TODO.

    Returns:
        str: TODO.

    """
    return sub(pattern=token, repl=replacement, string=text, count=0)


def slice_window[T](
    items: Iterable[T],
    start: int,
    stop: int,
) -> list[T]:
    """Return slice window.

    Args:
        items (Iterable[T]): TODO.
        start (int): TODO.
        stop (int): TODO.

    Returns:
        list[T]: TODO.

    """
    return list(items)[start:stop]


# =============================================================================
# 27. Fuller method-order exercise (canonical: dunders → classmethod →
# staticmethod → property → public → private)
# =============================================================================


class OrderingHeavy:
    """A class with members in deliberately scrambled order."""

    def __init__(self, items: list[int]) -> None:
        """Return init.

        Args:
            items (list[int]): TODO.

        """
        self._items: list[int] = list(items)

    def __len__(self) -> int:
        """Return len.

        Returns:
            int: TODO.

        """
        return len(self._items)

    @override
    def __repr__(self) -> str:
        """Return repr.

        Returns:
            str: TODO.

        """
        return f"OrderingHeavy(items={self._items!r})"

    @property
    def size(self) -> int:
        """Return size.

        Returns:
            int: TODO.

        """
        return len(self._items)

    @classmethod
    def make_empty(cls) -> Self:
        """Return make empty.

        Returns:
            Self: TODO.

        """
        return cls([])

    @staticmethod
    def banner() -> str:
        """Return banner.

        Returns:
            str: TODO.

        """
        return "OrderingHeavy"

    def public_action(self) -> int:
        """Return public action.

        Returns:
            int: TODO.

        """
        return self._helper(x=self.size)

    def _helper(self, x: int) -> int:
        """Return helper.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        return x * 2


# =============================================================================
# 28. @overload — multiple signatures + runtime dispatch
# =============================================================================


@overload
def coerce(value: int) -> str: ...
@overload
def coerce(value: str) -> int: ...
def coerce(value: int | str) -> int | str:
    """Return coerce.

    Args:
        value (int | str): TODO.

    Returns:
        int | str: TODO.

    """
    if isinstance(value, int):
        return str(object=value)
    return len(value)


# =============================================================================
# 28b. functools.lru_cache — decorator preserving recursive signature
# =============================================================================


@lru_cache(maxsize=128)
def fib(n: int) -> int:
    """Return fib.

    Args:
        n (int): TODO.

    Returns:
        int: TODO.

    """
    return n if n < Constants.int_2 else fib(n=n - 1) + fib(n=n - 2)


# =============================================================================
# 30. Enum values + Literal narrowing on members
# =============================================================================


class Status(Enum):
    """Three-state job status."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"


def status_priority(status: Status) -> int:
    """Return status priority.

    Args:
        status (Status): TODO.

    Returns:
        int: TODO.

    """
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
        items (list[str]): TODO.
        capacity (int): TODO.
        count (int): TODO.

    """

    items: StringList = field(default_factory=list)
    capacity: int = 16
    count: int = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Return post init."""
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

    def __init__(self, host: str, timeout: OptionalFloat = None) -> None:
        """Return init.

        Args:
            host (str): TODO.
            timeout (float | None): TODO.

        """
        self.host: str = host
        self.timeout: OptionalFloat = (
            timeout if timeout is not None else self.DEFAULT_TIMEOUT
        )


# =============================================================================
# 33. Walrus operator inside conditional and comprehension
# =============================================================================


def walrus_filter(items: StringList) -> StringList:
    """Return walrus filter.

    Args:
        items (list[str]): TODO.

    Returns:
        list[str]: TODO.

    """
    stripped: str
    return [stripped for x in items if (stripped := x.strip())]


def walrus_in_if(items: StringList) -> OptionalInt:
    """Return walrus in if.

    Args:
        items (list[str]): TODO.

    Returns:
        int | None: TODO.

    """
    n: int
    if (n := len(items)) > Constants.int_3:
        return n
    return None


# =============================================================================
# 34. f-string with nested expressions and format spec
# =============================================================================


def format_record(name: str, score: float, width: int) -> str:
    """Return format record.

    Args:
        name (str): TODO.
        score (float): TODO.
        width (int): TODO.

    Returns:
        str: TODO.

    """
    upper: str = name.upper()
    return f"{upper:>{width}} :: {score:7.2f}% [{Status.DONE.value!r}]"


# =============================================================================
# 35. Async context manager + async iteration
# =============================================================================


class AsyncGate:
    """Simple async context manager + async iterator."""

    def __init__(self, limit: int) -> None:
        """Return init.

        Args:
            limit (int): TODO.

        """
        self._limit: int = limit
        self._n: int = 0

    async def __aenter__(self) -> Self:
        """Return aenter.

        Returns:
            Self: TODO.

        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Reset the asynchronous iterator when context management ends.

        Args:
            exc_type (type[BaseException] | None): TODO.
            exc (BaseException | None): TODO.
            tb (TracebackType | None): TODO.

        """
        self._n = 0

    def __aiter__(self) -> AsyncGate:
        """Return aiter.

        Returns:
            AsyncGate: TODO.

        """
        return self

    async def __anext__(self) -> int:
        """Return anext.

        Returns:
            int: TODO.

        """
        if self._n >= self._limit:
            raise StopAsyncIteration
        self._n += 1
        return self._n


async def consume_gate(limit: int) -> list[int]:
    """Return consume gate.

    Args:
        limit (int): TODO.

    Returns:
        list[int]: TODO.

    """
    out: list[int] = []
    async with AsyncGate(limit=limit) as gate:
        value: int
        async for value in gate:
            _ = out.append(value)
    return out


# =============================================================================
# 36. Starred unpacking and **kwargs forwarding
# =============================================================================


def forward_call[**P, R](
    target: PToRCallable[P, R],
    *args: P.args,
    **kwargs: P.kwargs,
) -> R:
    """Return forward call.

    Args:
        target (Callable[P, R]): TODO.
        *args (P.args): TODO.
        **kwargs (P.kwargs): TODO.

    Returns:
        R: TODO.

    """
    return target(*args, **kwargs)


def merge_dicts[K, V, W](
    base: dict[K, V],
    extras: dict[K, W],
) -> dict[K, V | W]:
    """Return merge dicts.

    Args:
        base (dict[K, V]): TODO.
        extras (dict[K, W]): TODO.

    Returns:
        dict[K, V | W]: TODO.

    """
    return {**base, **extras}


# =============================================================================
# 37. Iterator protocol — __iter__ + __next__
# =============================================================================


class CountDown:
    """Manual iterator that counts down from ``start`` to zero."""

    def __init__(self, start: int) -> None:
        """Return init.

        Args:
            start (int): TODO.

        """
        self._current: int = start

    def __iter__(self) -> CountDown:
        """Return iter.

        Returns:
            CountDown: TODO.

        """
        return self

    def __next__(self) -> int:
        """Return next.

        Returns:
            int: TODO.

        """
        if self._current <= 0:
            raise StopIteration
        self._current -= 1
        return self._current + 1


# =============================================================================
# 38. TypeGuard narrowing
# =============================================================================


def is_str_list(items: list[object]) -> TypeGuard[StringList]:
    """Return is str list.

    Args:
        items (list[object]): TODO.

    Returns:
        TypeGuard[list[str]]: TODO.

    """
    return all(isinstance(x, str) for x in items)


def join_if_strings(items: list[object]) -> str:
    """Return join if strings.

    Args:
        items (list[object]): TODO.

    Returns:
        str: TODO.

    """
    if is_str_list(items=items):
        return ", ".join(items)
    return ""


# =============================================================================
# 39. Forward inference — narrow as we walk down through guards
# =============================================================================
# Each assignment refines the inferred type further. autotype should
# track: raw: object → str (after isinstance) → str (split-result
# is list[str]) first: str → int (after int() coercion) ratio: float (from
# int / float arithmetic with explicit float divisor)


def forward_narrow_pipeline(raw: str) -> tuple[StringList, int, float]:
    """Return forward narrow pipeline.

    Args:
        raw (str): TODO.

    Returns:
        tuple[list[str], int, float]: TODO.

    """
    assert isinstance(raw, str)  # noqa: S101
    parts: StringList = raw.split(sep=":")
    first: int | str = parts[0]
    first = int(first)
    ratio: float = first / 3.5
    return parts, first, ratio


# =============================================================================
# 40. Backward inference — call-site usage refines the parameter type
# =============================================================================
# ``packet_payload`` and ``packet_count`` are only ever called with concrete
# types; autotype's kwarg-backflow should annotate them precisely from the
# call sites below without any explicit annotations at the def-site.


def packet_payload(name: str, headers: Sized, body: Sized) -> str:
    """Return packet payload.

    Args:
        name (str): TODO.
        headers (Sized): TODO.
        body (Sized): TODO.

    Returns:
        str: TODO.

    """
    return f"{name}:{len(headers)}:{len(body)}"


def packet_count(items: StrIterable) -> int:
    """Return packet count.

    Args:
        items (Iterable[str]): TODO.

    Returns:
        int: TODO.

    """
    return sum(1 for _ in items)


def call_packet_helpers() -> StringIntPair:
    """Return call packet helpers.

    Returns:
        tuple[str, int]: TODO.

    """
    out: str = packet_payload(
        name="alpha",
        headers={"x-trace": "id-7"},
        body=b"hello",
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
          A continuation paragraph still belonging to ``level 3`` that must
          remain associated with the bullet after the blank-line
          separator above.
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

    Description list (term : definition) — colon-introduced
    definitions that align on the longest term:

    short_term         : a brief description aligned to the
                         colon column established by the longest term below.
    medium_term        : another description; same alignment column.
    very_long_term_name: anchors the colon column for the group;
                         siblings above pad with spaces so all colons
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
        """Return init."""
        self._items: list[T] = []

    def __len__(self) -> int:
        """Return len.

        Returns:
            int: TODO.

        """
        return len(self._items)

    def peek(self) -> T | None:
        """Return peek.

        Returns:
            T | None: TODO.

        """
        return self._items[-1] if self._items else None

    def pop(self) -> T | None:
        """Return pop.

        Returns:
            T | None: TODO.

        """
        return self._items.pop() if self._items else None

    def push(self, item: T) -> None:
        """Return push.

        Args:
            item (T): TODO.

        """
        _ = self._items.append(item)


class TypedQueue[T]:
    """FIFO queue parameterised on element type ``T``."""

    def __init__(self, items: list[T] | None = None) -> None:
        """Return init.

        Args:
            items (list[T] | None): TODO.

        """
        self._items: list[T] = list(items) if items is not None else []

    def dequeue(self) -> T | None:
        """Return dequeue.

        Returns:
            T | None: TODO.

        """
        return self._items.pop(0) if self._items else None

    def drain(self) -> list[T]:
        """Return drain.

        Returns:
            list[T]: TODO.

        """
        drained: list[T] = list(self._items)
        _ = self._items.clear()
        return drained

    def enqueue(self, item: T) -> None:
        """Return enqueue.

        Args:
            item (T): TODO.

        """
        _ = self._items.append(item)


class Pair[K, V]:
    """Two-key generic record mirroring ``typing.Generic`` style."""

    def __init__(self, key: K, value: V) -> None:
        """Return init.

        Args:
            key (K): TODO.
            value (V): TODO.

        """
        self.key: K = key
        self.value: V = value

    def swapped(self) -> Pair[V, K]:
        """Return swapped.

        Returns:
            Pair[V, K]: TODO.

        """
        return Pair(key=self.value, value=self.key)


# =============================================================================
# 43. Abstract base class + concrete subclasses (template method)
# =============================================================================


class Renderer(ABC):
    """Abstract renderer with a templated public ``render`` method."""

    def render(self, value: object) -> str:
        """Return render.

        Args:
            value (object): TODO.

        Returns:
            str: TODO.

        """
        prepared: str = self._prepare(value=value)
        body: str = self._format(prepared=prepared)
        return self._wrap(body=body)

    @abstractmethod
    def _format(self, prepared: str) -> str:
        """Return ``prepared`` formatted for the concrete output.

        Args:
            prepared (str): TODO.

        Returns:
            str: TODO.

        """

    def _prepare(self, value: object) -> str:
        """Return prepare.

        Args:
            value (object): TODO.

        Returns:
            str: TODO.

        """
        return str(object=value).strip()

    def _wrap(self, body: str) -> str:
        """Return wrap.

        Args:
            body (str): TODO.

        Returns:
            str: TODO.

        """
        return body


class JsonRenderer(Renderer):
    """Renderer that emits JSON-quoted strings."""

    @override
    def _format(self, prepared: str) -> str:
        """Return format.

        Args:
            prepared (str): TODO.

        Returns:
            str: TODO.

        """
        return dumps(obj=prepared)


class BracketRenderer(Renderer):
    """Renderer that wraps the body in square brackets."""

    @override
    def _format(self, prepared: str) -> str:
        """Return format.

        Args:
            prepared (str): TODO.

        Returns:
            str: TODO.

        """
        return prepared.upper()

    @override
    def _wrap(self, body: str) -> str:
        """Return wrap.

        Args:
            body (str): TODO.

        Returns:
            str: TODO.

        """
        return f"[{body}]"


# =============================================================================
# 44. Mixin pattern — cooperative MRO, super() forwarding
# =============================================================================


class TimestampMixin:
    """Mixin attaching a creation timestamp to any record."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Initialize the mixin and forward its constructor arguments.

        Args:
                *args (object): TODO.
                **kwargs (object): TODO.

            args (object): TODO.
            kwargs (object): TODO.

        """
        _ = super().__init__(*args, **kwargs)
        self.created_at: float = monotonic()


class CountingMixin:
    """Mixin counting how many times ``record`` has been called.

    Attributes:
        hits (int): TODO.

    """

    hits: int = 0

    def initialize_count(self) -> None:
        """Initialize the number of completed record operations."""
        self.hits = 0

    def record(self) -> int:
        """Return record.

        Returns:
            int: TODO.

        """
        self.hits += 1
        return self.hits


class AuditLog(TimestampMixin, CountingMixin):
    """Concrete record combining timestamp + counter mixins."""

    @override
    def __init__(self, source: str) -> None:
        """Return init.

        Args:
            source (str): TODO.

        """
        _ = super().__init__()
        self.initialize_count()
        self.source: str = source

    def describe(self) -> str:
        """Return describe.

        Returns:
            str: TODO.

        """
        return f"{self.source}@{self.created_at:.3f}#{self.hits}"


# =============================================================================
# 45. itertools / functools heavy use — receiver chains across stdlib
# =============================================================================


def running_total(values: list[int]) -> list[int]:
    """Return running total.

    Args:
        values (list[int]): TODO.

    Returns:
        list[int]: TODO.

    """
    return list(accumulate(iterable=values))


def grouped_runs(text: str) -> StringCountPairs:
    """Return grouped runs.

    Args:
        text (str): TODO.

    Returns:
        list[tuple[str, int]]: TODO.

    """
    return [
        (key, sum(1 for _ in group)) for key, group in groupby(iterable=text)
    ]


def flatten_pairs(pairs: list[tuple[int, int]]) -> list[int]:
    """Return flatten pairs.

    Args:
        pairs (list[tuple[int, int]]): TODO.

    Returns:
        list[int]: TODO.

    """
    return list(chain.from_iterable(pairs))


def first_n_under_limit(values: list[int], limit: int) -> list[int]:
    """Return first n under limit.

    Args:
        values (list[int]): TODO.
        limit (int): TODO.

    Returns:
        list[int]: TODO.

    """
    return list(islice(takewhile(lambda v: v < limit, values), 8))


def fold_product(values: list[int]) -> int:
    """Return fold product.

    Args:
        values (list[int]): TODO.

    Returns:
        int: TODO.

    """
    return reduce(lambda a, b: a * b, values, 1)


# =============================================================================
# 46. datetime arithmetic — chain through stdlib date/time types
# =============================================================================


def now_iso() -> str:
    """Return now iso.

    Returns:
        str: TODO.

    """
    return datetime.now(tz=UTC).isoformat()


def shift_days(stamp: datetime, days: int) -> datetime:
    """Return shift days.

    Args:
        stamp (datetime): TODO.
        days (int): TODO.

    Returns:
        datetime: TODO.

    """
    return stamp + timedelta(days=days)


def is_recent(stamp: datetime, window_hours: int) -> bool:
    """Return is recent.

    Args:
        stamp (datetime): TODO.
        window_hours (int): The window hours value passed to the call.

    Returns:
        bool: TODO.

    """
    threshold: datetime = datetime.now(tz=UTC) - timedelta(hours=window_hours)
    return stamp >= threshold


def days_between(a: datetime, b: datetime) -> int:
    """Return days between.

    Args:
        a (datetime): TODO.
        b (datetime): TODO.

    Returns:
        int: TODO.

    """
    return abs((a - b).days)


# =============================================================================
# 47. pathlib — heavy receiver-chain inference + with statements
# =============================================================================


def read_first_nonblank(path: Path) -> str:
    """Return read first nonblank.

    Args:
        path (Path): TODO.

    Returns:
        str: TODO.

    """
    line: str
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.strip()
    return ""


def write_listing(target_dir: Path, names: StringList) -> Path:
    """Return write listing.

    Args:
        target_dir (Path): The target dir value passed to the call.
        names (list[str]): TODO.

    Returns:
        Path: TODO.

    """
    listing: Path = target_dir / "listing.txt"
    _ = listing.parent.mkdir(parents=True, exist_ok=True)
    _ = listing.write_text(data="\n".join(sorted(names)), encoding="utf-8")
    return listing


def walk_python_files(root: Path) -> list[Path]:
    """Return walk python files.

    Args:
        root (Path): TODO.

    Returns:
        list[Path]: TODO.

    """
    return [
        p for p in root.rglob(pattern="*.py") if not p.name.startswith(".")
    ]


def file_size_kb(path: Path) -> float:
    """Return file size kb.

    Args:
        path (Path): TODO.

    Returns:
        float: TODO.

    """
    return path.stat().st_size / Constants.int_1024


# =============================================================================
# 48. collections.abc — ABC-based duck typing
# =============================================================================


def map_values[K, V, W](
    source: Mapping[K, V],
    fn: Callable[[V], W],
) -> dict[K, W]:
    """Return map values.

    Args:
        source (Mapping[K, V]): TODO.
        fn (Callable[[V], W]): TODO.

    Returns:
        dict[K, W]: TODO.

    """
    return {k: fn(v) for k, v in source.items()}


def merge_dicts_inplace(
    target: MutableMapping[str, int],
    extra: MappingStrInt,
) -> None:
    """Return merge dicts inplace.

    Args:
        target (MutableMapping[str, int]): TODO.
        extra (Mapping[str, int]): TODO.

    """
    for key, value in extra.items():
        target[key] = target.get(key, 0) + value


def iterable_to_counts(items: StrIterable) -> StringToInt:
    """Return iterable to counts.

    Args:
        items (Iterable[str]): TODO.

    Returns:
        dict[str, int]: TODO.

    """
    counts: StringToInt = {}
    item: str
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


# =============================================================================
# 49. Recursive shape inference — tree walker that returns dict[str, object]
# =============================================================================


def flatten_tree(
    node: JSONObject,
    prefix: str = "",
) -> JSONObject:
    """Flatten a nested ``dict``/``list`` tree into dotted-key form.

    Args:
        node (dict[str, JSONValue]): TODO.
        prefix (str): TODO.

    Returns:
        dict[str, JSONValue]: TODO.

    """
    result: JSONObject = {}
    for key, value in node.items():
        full: str = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            _ = result.update(flatten_tree(node=value, prefix=full))
        elif isinstance(value, list):
            for index, item in enumerate(iterable=value):
                if isinstance(item, dict):
                    _ = result.update(
                        flatten_tree(node=item, prefix=f"{full}[{index}]"),
                    )
                else:
                    result[f"{full}[{index}]"] = item
        else:
            result[full] = value
    return result


def deep_merge(
    left: JSONObject,
    right: JSONObject,
) -> JSONObject:
    """Recursively merge two dict trees; ``right`` wins on conflicts.

    Args:
        left (dict[str, JSONValue]): TODO.
        right (dict[str, JSONValue]): TODO.

    Returns:
        dict[str, JSONValue]: TODO.

    """
    merged: JSONObject = dict(left)
    for key, value in right.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(
                left=cast_dict(value=merged[key]),
                right=cast_dict(value=value),
            )
        else:
            merged[key] = value
    return merged


def cast_dict(value: JSONValue) -> JSONObject:
    """Return cast dict.

    Args:
        value (JSONValue): TODO.

    Returns:
        dict[str, JSONValue]: TODO.

    """
    return value if isinstance(value, dict) else {}


# =============================================================================
# 50. Algorithm patterns — magic-number-rich math/sort/search
# =============================================================================


def binary_search(items: list[int], target: int) -> int:
    """Return binary search.

    Args:
        items (list[int]): TODO.
        target (int): TODO.

    Returns:
        int: TODO.

    """
    low, high = 0, len(items) - 1
    while low <= high:
        mid: float = (low + high) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            low: float = mid + 1
        else:
            high: float = mid - 1
    return -1


def insertion_sort(items: list[int]) -> list[int]:
    """Return insertion sort.

    Args:
        items (list[int]): TODO.

    Returns:
        list[int]: TODO.

    """
    out: list[int] = list(items)
    i: int
    for i in range(1, len(out)):
        current: int = out[i]
        j: int = i - 1
        while j >= 0 and out[j] > current:
            out[j + 1] = out[j]
            j -= 1
        out[j + 1] = current
    return out


def fibonacci_iter(limit: int) -> list[int]:
    """Return fibonacci iter.

    Args:
        limit (int): TODO.

    Returns:
        list[int]: TODO.

    """
    out: list[int] = []
    a, b = 0, 1
    while a < limit:
        _ = out.append(a)
        a, b = b, a + b
    return out


def gcd(a: int, b: int) -> int:
    """Return gcd.

    Args:
        a (int): TODO.
        b (int): TODO.

    Returns:
        int: TODO.

    """
    while b:
        a, b = b, a % b
    return a


def lcm(a: int, b: int) -> int:
    """Return lcm.

    Args:
        a (int): TODO.
        b (int): TODO.

    Returns:
        int: TODO.

    """
    return abs(a * b) // gcd(a=a, b=b) if a and b else 0


def factorial(n: int) -> int:
    """Return factorial.

    Args:
        n (int): TODO.

    Returns:
        int: TODO.

    """
    if n < 0:
        return 0
    result: int = 1
    k: int
    for k in range(2, n + 1):
        result *= k
    return result


def power_mod(base: int, exp: int, modulus: int) -> int:
    """Return power mod.

    Args:
        base (int): TODO.
        exp (int): TODO.
        modulus (int): TODO.

    Returns:
        int: TODO.

    """
    result: int = 1 % modulus
    current: int = base % modulus
    while exp > 0:
        if exp & 1:
            result = (result * current) % modulus
        current = (current * current) % modulus
        exp >>= 1
    return result


# =============================================================================
# 51. String parsing — state-machine style with explicit transitions
# =============================================================================


def parse_csv_row(line: str) -> StringList:
    """Return parse csv row.

    Args:
        line (str): TODO.

    Returns:
        list[str]: TODO.

    """
    fields: StringList = []
    buffer: StringList = []
    in_quotes: bool = False
    char: str
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            _ = fields.append("".join(buffer))
            _ = buffer.clear()
        else:
            _ = buffer.append(char)
    _ = fields.append("".join(buffer))
    return fields


def tokenize_simple(text: str) -> StringList:
    """Return tokenize simple.

    Args:
        text (str): TODO.

    Returns:
        list[str]: TODO.

    """
    tokens: StringList = []
    current: StringList = []
    char: str
    for char in text:
        if char.isalnum() or char == "_":
            _ = current.append(char)
            continue
        if current:
            _ = tokens.append("".join(current))
            _ = current.clear()
        if not char.isspace():
            _ = tokens.append(char)
    if current:
        _ = tokens.append("".join(current))
    return tokens


def strip_comments(source: str) -> str:
    """Return strip comments.

    Args:
        source (str): TODO.

    Returns:
        str: TODO.

    """
    lines: StringList = source.splitlines()
    cleaned: StringList = []
    line: str
    for line in lines:
        idx: int = line.find("#")
        _ = cleaned.append(line[:idx].rstrip() if idx >= 0 else line)
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
    left: OptionalTreeNode = None
    right: OptionalTreeNode = None

    def depth(self) -> int:
        """Return depth.

        Returns:
            int: TODO.

        """
        left_depth: int = 0 if self.left is None else self.left.depth()
        right_depth: int = 0 if self.right is None else self.right.depth()
        return 1 + max(left_depth, right_depth)

    def in_order(self) -> list[int]:
        """Return in order.

        Returns:
            list[int]: TODO.

        """
        result: list[int] = []
        if self.left is not None:
            _ = result.extend(self.left.in_order())
        _ = result.append(self.value)
        if self.right is not None:
            _ = result.extend(self.right.in_order())
        return result

    def insert(self, value: int) -> None:
        """Return insert.

        Args:
            value (int): TODO.

        """
        if value < self.value:
            if self.left is None:
                self.left = TreeNode(value=value)
            else:
                _ = self.left.insert(value=value)
        elif self.right is None:
            self.right = TreeNode(value=value)
        else:
            _ = self.right.insert(value=value)


@dataclass
class Graph:
    """Adjacency-list graph keyed by node id.

    Attributes:
        adjacency (dict[int, list[int]]): TODO.

    """

    adjacency: dict[int, list[int]] = field(default_factory=dict)

    def add_edge(self, source: int, target: int) -> None:
        """Return add edge.

        Args:
            source (int): TODO.
            target (int): TODO.

        """
        _ = self.adjacency.setdefault(source, []).append(target)
        _ = self.adjacency.setdefault(target, []).append(source)

    def bfs(self, start: int) -> list[int]:
        """Return bfs.

        Args:
            start (int): TODO.

        Returns:
            list[int]: TODO.

        """
        visited: set[int] = {start}
        order: list[int] = [start]
        frontier: list[int] = [start]
        while frontier:
            current: int = frontier.pop(0)
            neighbour: int
            for neighbour in self.adjacency.get(current, []):
                if neighbour in visited:
                    continue
                _ = visited.add(neighbour)
                _ = order.append(neighbour)
                _ = frontier.append(neighbour)
        return order

    def neighbours(self, node: int) -> list[int]:
        """Return neighbours.

        Args:
            node (int): TODO.

        Returns:
            list[int]: TODO.

        """
        return list(self.adjacency.get(node, []))


# =============================================================================
# 53. Numeric helpers — statistics-like with float divisors
# =============================================================================


def mean(values: FloatList) -> float:
    """Return mean.

    Args:
        values (list[float]): TODO.

    Returns:
        float: TODO.

    """
    return sum(values) / len(values) if values else 0.0


def variance(values: FloatList) -> float:
    """Return variance.

    Args:
        values (list[float]): TODO.

    Returns:
        float: TODO.

    """
    if len(values) < Constants.int_2:
        return 0.0
    avg: float = mean(values=values)
    return sum((v - avg) ** 2 for v in values) / (len(values) - 1)


def stdev(values: FloatList) -> float:
    """Return stdev.

    Args:
        values (list[float]): TODO.

    Returns:
        float: TODO.

    """
    return sqrt(variance(values=values))


def median(values: FloatList) -> float:
    """Return median.

    Args:
        values (list[float]): TODO.

    Returns:
        float: TODO.

    """
    if not values:
        return 0.0
    sorted_values: FloatList = sorted(values)
    middle: int = len(sorted_values) // 2
    if len(sorted_values) % 2:
        return sorted_values[middle]
    return (sorted_values[middle - 1] + sorted_values[middle]) / 2


def clip(value: float, low: float, high: float) -> float:
    """Return clip.

    Args:
        value (float): TODO.
        low (float): TODO.
        high (float): TODO.

    Returns:
        float: TODO.

    """
    return max(low, min(value, high))


def lerp(start: float, end: float, t: float) -> float:
    """Return lerp.

    Args:
        start (float): TODO.
        end (float): TODO.
        t (float): TODO.

    Returns:
        float: TODO.

    """
    return start + (end - start) * t


def remap(
    value: float,
    src_low: float,
    src_high: float,
    dst_low: float,
    dst_high: float,
) -> float:
    """Return remap.

    Args:
        value (float): TODO.
        src_low (float): The src low value passed to the call.
        src_high (float): The src high value passed to the call.
        dst_low (float): The dst low value passed to the call.
        dst_high (float): The dst high value passed to the call.

    Returns:
        float: TODO.

    """
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

    Note:
        The Examples block above uses the doctest convention and
        must survive the docstring normaliser without indentation drift.

    See Also:
        :func:`forward_narrow_pipeline`: a related forward-inference demo.
        :func:`call_packet_helpers`: a related backward-inference demo.

    Args:
        value (str): The input string to echo back; its presence forces
            the wrapper to emit an Args block with a multi-line entry
            whose continuation must indent under the parameter name.

    Returns:
        str: The input string returned verbatim. Documented across
            multiple lines to verify the Returns block alignment.

    Raises:
        ValueError: Never actually raised; documented so the
            Raises section receives a multi-line entry whose
            continuation indents under the exception name.

    Examples:
        Basic usage with a single short argument:

            >>> long_prose_doc("hi")
            'hi'

        Round-tripping a longer literal:

            >>> long_prose_doc("hello, world")
            'hello, world'

    """
    return value


# =============================================================================
# 55. Yields section — generator with documented yield type
# =============================================================================


def chunk_iter(values: list[int], size: int) -> Generator[list[int]]:
    """Yield successive ``size``-sized chunks of ``values``.

    Args:
        values (list[int]): The source sequence to chunk.
        size (int): Number of elements in each yielded chunk; the final chunk
            may be smaller if ``len(values)`` is not divisible.

    Yields:
        list[int]: A slice of ``values`` of length ``<= size``.

    Raises:
        ValueError: If ``size`` is less than one.

    """
    if size < 1:
        msg: str = "size must be >= 1"
        raise ValueError(msg)
    offset: int
    for offset in range(0, len(values), size):
        yield values[offset : offset + size]


def stride_iter(values: list[int], step: int) -> IntegerGenerator:
    """Yield values at the given ``step`` interval.

    Args:
        values (list[int]): The source sequence.
        step (int): Stride between successive yielded items.

    Yields:
        int: Every ``step``-th item from ``values``.

    """
    index: int
    for index in range(0, len(values), step):
        yield values[index]


# =============================================================================
# 56. Deeply nested generics — Mapping[str, list[tuple[int, set[str]]]]
# =============================================================================


def index_records(
    rows: list[tuple[str, int, str]],
) -> StringToIntTagGroups:
    """Bucket rows by category, aggregating ids and tags.

    Args:
        rows (list[tuple[str, int, str]]): 3-tuples of (category, id, tag).

    Returns:
        A mapping from category to a list of (id, set-of-tags) entries.

    """
    out: StringToIntTagGroups = {}
    for category, row_id, tag in rows:
        bucket: TupleIntStrSetList = out.setdefault(category, [])
        # Try merge into existing entry with the same id.
        merged: bool = False
        for index, (existing_id, tags) in enumerate(iterable=bucket):
            if existing_id == row_id:
                bucket[index] = (existing_id, tags | {tag})
                merged = True
                break
        if not merged:
            _ = bucket.append((row_id, {tag}))
    return out


def matrix_transpose(matrix: FloatListList) -> FloatListList:
    """Return matrix transpose.

    Args:
        matrix (list[list[float]]): TODO.

    Returns:
        list[list[float]]: TODO.

    """
    if not matrix:
        return []
    cols: int = len(matrix[0])
    return [[row[col] for row in matrix] for col in range(cols)]


def nested_lookup(
    table: dict[str, StrToIntListMap],
    outer: str,
    inner: str,
) -> list[int]:
    """Return nested lookup.

    Args:
        table (dict[str, dict[str, list[int]]]): The table value
            passed to the call.
        outer (str): TODO.
        inner (str): TODO.

    Returns:
        list[int]: TODO.

    """
    return list(table.get(outer, {}).get(inner, []))


# =============================================================================
# 57. dict/list narrowing chains — many isinstance branches
# =============================================================================


def coerce_value(value: JSONValue) -> str:
    """Return coerce value.

    Args:
        value (JSONValue): TODO.

    Returns:
        str: TODO.

    """
    if isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(object=value)
    if isinstance(value, float):
        return format(value, ".3f")
    if isinstance(value, list):
        parts: StringList = [coerce_value(value=item) for item in value]
        return ",".join(parts)
    if isinstance(value, dict):
        kv_parts: StringList = []
        for key, item in value.items():
            _ = kv_parts.append(
                str(object=key) + "=" + coerce_value(value=item),
            )
        return ";".join(kv_parts)
    return "" if value is None else repr(value)


def flatten_lists_of_lists(values: list[IntListOrInt]) -> list[int]:
    """Return flatten lists of lists.

    Args:
        values (list[list[int] | int]): TODO.

    Returns:
        list[int]: TODO.

    """
    out: list[int] = []
    item: IntListOrInt
    for item in values:
        _ = out.extend(item) if isinstance(item, list) else out.append(item)
    return out


def type_summary(values: list[object]) -> StringToInt:
    """Return type summary.

    Args:
        values (list[object]): TODO.

    Returns:
        dict[str, int]: TODO.

    """
    summary: StringToInt = {}
    value: object
    for value in values:
        if isinstance(value, bool):
            key: str = "bool"
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
    """Return quarterly rate.

    Args:
        annual (float): TODO.
        quarter (int): TODO.

    Returns:
        float: TODO.

    """
    if quarter == 1:
        return annual * 0.22
    if quarter == Constants.int_2:
        return annual * 0.27
    if quarter == Constants.int_3:
        return annual * 0.26
    return annual * 0.25


def shipping_cost(weight_kg: float, distance_km: float) -> float:
    """Return shipping cost.

    Args:
        weight_kg (float): The weight kg value passed to the call.
        distance_km (float): The distance km value passed to the call.

    Returns:
        float: TODO.

    """
    base: float = 4.5
    weight_fee: float = weight_kg * 1.2
    distance_fee: float = distance_km * 0.08
    if distance_km > Constants.int_500:
        distance_fee += 12.0
    if weight_kg > Constants.int_20:
        weight_fee += 18.0
    return base + weight_fee + distance_fee


def tier_for_score(score: int) -> str:
    """Return tier for score.

    Args:
        score (int): TODO.

    Returns:
        str: TODO.

    """
    if score >= Constants.int_950:
        return "platinum"
    if score >= Constants.int_850:
        return "gold"
    if score >= Constants.int_750:
        return "silver"
    if score >= Constants.int_600:
        return "bronze"
    return "none"


def piecewise_tax(income: float) -> float:
    """Return piecewise tax.

    Args:
        income (float): TODO.

    Returns:
        float: TODO.

    """
    if income <= Constants.int_10000:
        return income * 0.08
    if income <= Constants.int_50000:
        return Constants.int_800 + (income - Constants.int_10000) * 0.15
    if income <= Constants.int_200000:
        return Constants.int_6800 + (income - Constants.int_50000) * 0.24
    return Constants.int_42800 + (income - Constants.int_200000) * 0.33


# =============================================================================
# 59. Larger method-sort exercise — full canonical-order test class
# =============================================================================


class FullScrambledClass:
    """Class with every canonical-order category present and misordered.

    Attributes:
        _internal_state (int): TODO.

    """

    _internal_state: int = 0

    def __init__(self) -> None:
        """Return init."""
        self._internal_state = 0

    @override
    def __eq__(self, other: object) -> bool:
        """Return eq.

        Args:
            other (object): TODO.

        Returns:
            bool: TODO.

        """
        return (
            isinstance(other, FullScrambledClass)
            and other._internal_state == self._internal_state
        )

    @override
    def __hash__(self) -> int:
        """Return hash.

        Returns:
            int: TODO.

        """
        return hash(self._internal_state)

    def __len__(self) -> int:
        """Return len.

        Returns:
            int: TODO.

        """
        return abs(self._internal_state)

    @override
    def __repr__(self) -> str:
        """Return repr.

        Returns:
            str: TODO.

        """
        return f"FullScrambledClass(state={self._internal_state})"

    @property
    def state(self) -> int:
        """Return state.

        Returns:
            int: TODO.

        """
        return self._internal_state

    @classmethod
    def from_dict(cls, payload: StringToInt) -> FullScrambledClass:
        """Return from dict.

        Args:
            payload (dict[str, int]): TODO.

        Returns:
            FullScrambledClass: TODO.

        """
        instance: FullScrambledClass = cls()
        instance._internal_state = payload.get("state", 0)
        return instance

    @staticmethod
    def signature() -> str:
        """Return signature.

        Returns:
            str: TODO.

        """
        return "FullScrambledClass"

    def adjust(self, delta: int) -> int:
        """Return adjust.

        Args:
            delta (int): TODO.

        Returns:
            int: TODO.

        """
        self._internal_state += delta
        return self._internal_state

    def _internal_helper(self) -> int:
        """Return internal helper.

        Returns:
            int: TODO.

        """
        return self._internal_state


# =============================================================================
# 60. Yet another autokwargs exercise — many positional stdlib calls
# =============================================================================


def lots_of_positional_calls(
    target_dir: Path,
    items: StringList,
    delim: str,
) -> StringToInt:
    """Return lots of positional calls.

    Args:
        target_dir (Path): The target dir value passed to the call.
        items (list[str]): TODO.
        delim (str): TODO.

    Returns:
        dict[str, int]: TODO.

    """
    joined: str = delim.join(items)
    out_path: Path = target_dir / "joined.txt"
    _ = out_path.write_text(data=joined, encoding="utf-8")
    counts: StrCounter = Counter(items)
    top: StringCountPairs = counts.most_common(n=3)
    return dict(top)


def regex_pipeline(text: str) -> StringToString:
    """Return regex pipeline.

    Args:
        text (str): TODO.

    Returns:
        dict[str, str]: TODO.

    """
    return {
        "compact": sub(pattern=r"\s+", repl=" ", string=text),
        "upper_alpha": sub(pattern=r"[^A-Z]", repl="", string=text.upper()),
        "first_word": split(pattern=r"\s+", string=text.strip())[0]
        if text.strip()
        else "",
        "letters_only": sub(pattern=r"[^A-Za-z]", repl="", string=text),
    }


def slice_helpers(items: list[int]) -> StrToIntListMap:
    """Return slice helpers.

    Args:
        items (list[int]): TODO.

    Returns:
        dict[str, list[int]]: TODO.

    """
    return {
        "first_three": items[:3],
        "last_three": items[-3:],
        "middle": items[len(items) // 4 : -len(items) // 4]
        if len(items) >= Constants.int_4
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

    A code block follows the quote to verify the wrapper
    doesn't accidentally promote prose into the code block:

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


def upstream_consumer(payload: str) -> StrPair:
    """Return upstream consumer.

    Args:
        payload (str): TODO.

    Returns:
        tuple[str, str]: TODO.

    """
    parts: StringList = payload.split(sep="=", maxsplit=1)
    return parts[0], parts[1]


def upstream_aggregator(items: StrIterable) -> StrPairList:
    """Return upstream aggregator.

    Args:
        items (Iterable[str]): TODO.

    Returns:
        list[tuple[str, str]]: TODO.

    """
    return [upstream_consumer(payload=item) for item in items]


def driver_for_inference() -> StrPairList:
    """Return driver for inference.

    Returns:
        list[tuple[str, str]]: TODO.

    """
    fixed: StringList = ["k1=v1", "k2=v2", "k3=v3"]
    return upstream_aggregator(items=fixed)


# =============================================================================
# 63. Closure tracking — inner function captures outer typed parameter
# =============================================================================
# autotype's nonlocal-tracking pass should infer the inner function's
# parameters from how it uses values closed-over from the enclosing scope.
# (See docs/README_autotype.md → "Closure Tracking".)


def make_adder(base: int) -> IntToIntCallable:
    """Return make adder.

    Args:
        base (int): TODO.

    Returns:
        Callable[[int], int]: TODO.

    """

    def adder(amount: int) -> int:
        """Return adder.

        Args:
            amount (int): TODO.

        Returns:
            int: TODO.

        """
        return base + amount

    return adder


def make_indexed_getter(prefix: str) -> StringTransform:
    """Return make indexed getter.

    Args:
        prefix (str): TODO.

    Returns:
        Callable[[str], str]: TODO.

    """

    def get(key: str) -> str:
        """Return get.

        Args:
            key (str): TODO.

        Returns:
            str: TODO.

        """
        return prefix + "." + key

    return get


def use_closures() -> tuple[int, str]:
    """Return use closures.

    Returns:
        tuple[int, str]: TODO.

    """
    add5: IntToIntCallable = make_adder(base=5)
    label: StringTransform = make_indexed_getter(prefix="env")
    return add5(7), label("PATH")


# =============================================================================
# 64. String alias synthesis — repeated Literal unions across params
# =============================================================================
# When two distinct functions narrow on the same finite string set,
# autotype's alias synthesizer hoists the union into a single named
# Literal alias so the annotations stay DRY. (See
# docs/README_autotype.md → "String Alias Synthesis".)


def process_status(status: str) -> bool:
    """Return process status.

    Args:
        status (str): TODO.

    Returns:
        bool: TODO.

    """
    if status == "active":
        return True
    if status == "inactive":
        return False
    return False


def handle_mode(mode: str) -> int:
    """Return handle mode.

    Args:
        mode (str): TODO.

    Returns:
        int: TODO.

    """
    if mode == "active":
        return 1
    if mode == "inactive":
        return 0
    return -1


def render_state(state: str) -> str:
    """Return render state.

    Args:
        state (str): TODO.

    Returns:
        str: TODO.

    """
    if state == "active":
        return ">"
    if state == "inactive":
        return "."
    return "?"


# =============================================================================
# 65. Memoization pattern — manual cache dict synthesized as concrete dict
# =============================================================================
# autotype detects the ``if x in cache: return cache[x]; cache[x] =
# result`` shape and annotates ``cache`` from the values it stores
# rather than leaving it ``dict[object, object]``. (See
# docs/README_autotype.md → "Memoization Pattern".)


def cached_fib(n: int) -> int:
    """Return cached fib.

    Args:
        n (int): TODO.

    Returns:
        int: TODO.

    """
    if n in Constants.fib_cache:
        return Constants.fib_cache[n]
    result: int = (
        n if n < Constants.int_2 else cached_fib(n=n - 1) + cached_fib(n=n - 2)
    )
    Constants.fib_cache[n] = result
    return result


def cached_title(value: str) -> str:
    """Return cached title.

    Args:
        value (str): TODO.

    Returns:
        str: TODO.

    """
    if value in Constants.title_cache:
        return Constants.title_cache[value]
    result: str = value.strip().title()
    Constants.title_cache[value] = result
    return result


# =============================================================================
# 66. Override decorator addition — subclass methods missing @override
# =============================================================================
# autotype walks subclass MROs and inserts ``@override`` on every method that
# already exists on a base class. (See docs/README_autotype.md → "Override
# Decorator Addition".) The base ``Greeter`` declares the contract; the two
# subclasses below override ``greet`` / ``__repr__`` *without* the decorator
# at the def-site — the pipeline should add it.


class Greeter:
    """Friendly base whose subclasses customise the greeting verb."""

    @override
    def __repr__(self) -> str:
        """Return repr.

        Returns:
            str: TODO.

        """
        return "Greeter()"

    def greet(self, name: str) -> str:
        """Return greet.

        Args:
            name (str): TODO.

        Returns:
            str: TODO.

        """
        return "hi " + name


class FormalGreeter(Greeter):
    """Subclass overriding both base methods without the decorator."""

    @override
    def __repr__(self) -> str:
        """Return repr.

        Returns:
            str: TODO.

        """
        return "FormalGreeter()"

    @override
    def greet(self, name: str) -> str:
        """Return greet.

        Args:
            name (str): TODO.

        Returns:
            str: TODO.

        """
        return "Good day, " + name + "."


class CasualGreeter(Greeter):
    """Subclass overriding only ``greet``."""

    @override
    def greet(self, name: str) -> str:
        """Return greet.

        Args:
            name (str): TODO.

        Returns:
            str: TODO.

        """
        return "yo " + name


# =============================================================================
# 67. Module-level annotations — unannotated constants
# =============================================================================
# autotype's module-level annotation pass should turn each of these right-
# hand-side-inferred assignments into typed declarations (``int`` /
# ``list[object]`` / ``dict[str, int]`` / ``tuple[int, int, int]``). (See
# docs/README_autotype.md → "Module-Level Annotations".)


def batch_summary() -> str:
    """Return batch summary.

    Returns:
        str: TODO.

    """
    return (
        f"batch={Constants.default_batch_size} tags={Constants.known_tags!r} "
        f"priorities={Constants.priority_levels!r} "
        f"channel={Constants.channel_rgb!r}"
    )


# =============================================================================
# 68. Escaped-newline literals → dedent(text=...) auto-conversion
# =============================================================================
# autowrap's `NewlineAndDedentStringFormatter` rewrites every plain string
# literal containing ``\n`` escapes into a triple-quoted
# ``dedent(text="""…""")`` block, and adds ``from textwrap import dedent``
# when the module doesn't already import it. The originals below are
# deliberately short-ish multi-line escapes that the conversion heuristic
# considers worth rewriting (more than one ``\n`` and at least one non-blank
# line in the value).


def render_html_skeleton() -> str:
    """Return render html skeleton.

    Returns:
        str: TODO.

    """
    return dedent(
        text="""\
                <html>
                  <body>
                    <p>placeholder</p>
                  </body>
                </html>
            """,
    )


def render_help_banner() -> str:
    """Return render help banner.

    Returns:
        str: TODO.

    """
    return dedent(
        text="""\
            USAGE: tool [options] FILE

            OPTIONS:
              --help    show help
        """,
    )


def render_sql_template(table: str) -> str:
    """Return render sql template.

    Args:
        table (str): TODO.

    Returns:
        str: TODO.

    """
    base: str = dedent(
        text="""\
                SELECT id, name, value
                FROM TABLE_NAME
                WHERE active = TRUE
                ORDER BY id;
            """,
    )
    return base.replace("TABLE_NAME", table)


# =============================================================================
# 69. Docstring-extracted type hints — comment-based & doctstring-based
# =============================================================================
# autotype's docstring parser pulls explicit ``Args:`` types out of a Google
# block when the def-site lacks annotations and the docstring carries an
# unambiguous one. (See docs/README_autotype.md → "Docstring Parsing".)


def parse_with_doc_types(raw: str, retries: int) -> StringList:
    """Parse ``raw`` with bounded retries.

    Args:
        raw (str): The raw text to parse — annotation deliberately omitted on
            the ``def`` line so autotype must read the docstring to
            recover the type.
        retries (int): Number of times to retry on transient failure.

    Returns:
        list[str]: Parsed tokens.

    """
    attempt: int = 0
    while attempt < retries:
        tokens: StringList = raw.split(sep=":")
        if tokens:
            return tokens
        attempt += 1
    return []


# =============================================================================
# 70. Decorator awareness in autokwargs — @staticmethod / @classmethod
# =============================================================================
# autokwargs resolves the receiver kind correctly for ``@staticmethod``
# and ``@classmethod`` calls and adds keyword names even when the caller
# goes through the *class* rather than an instance. (See
# docs/README_autokwargs.md → "Decorator awareness".)


class Registry:
    """Class whose static and class methods are called positionally.

    Attributes:
        label (str): TODO.

    """

    label: str = ""

    @classmethod
    def from_pair(cls, head: str, tail: str) -> Registry:
        """Return from pair.

        Args:
            head (str): TODO.
            tail (str): TODO.

        Returns:
            Registry: TODO.

        """
        instance: Registry = cls()
        instance.label = head + "/" + tail
        return instance

    @staticmethod
    def stamp(prefix: str, value: str) -> str:
        """Return stamp.

        Args:
            prefix (str): TODO.
            value (str): TODO.

        Returns:
            str: TODO.

        """
        return prefix + ":" + value


def call_registry() -> tuple[str, Registry]:
    """Return call registry.

    Returns:
        tuple[str, Registry]: TODO.

    """
    return Registry.stamp(
        prefix="env",
        value="production",
    ), Registry.from_pair(head="a", tail="b")


# =============================================================================
# 71. Function-scope magic values — autoinsert local-extraction
# =============================================================================
# When ``magic-values-scope=function`` is set, autoinsert hoists numeric
# literals inside *one* function into a local constant rather than a module-
# level one. The header runs in module-scope so this section is here to
# demonstrate the *expression density* that an inner-scope extraction would
# normalise; switch the header to ``function`` to see the difference.


def physics_step(velocity: float, acceleration: float) -> float:
    """Return physics step.

    Args:
        velocity (float): TODO.
        acceleration (float): TODO.

    Returns:
        float: TODO.

    """
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
    """Return first of.

    Args:
        items (list[T]): TODO.

    Returns:
        T | None: TODO.

    """
    if not items:
        return None
    return items[0]


def pair_keys[K, V](mapping: dict[K, V]) -> list[K]:
    """Return pair keys.

    Args:
        mapping (dict[K, V]): TODO.

    Returns:
        list[K]: TODO.

    """
    return list(mapping.keys())


# =============================================================================
# 73. TypeAlias hoisting — explicit ``type Foo = ...`` (PEP 695)
# =============================================================================
# autotype recognises PEP 695 type-alias statements and treats the RHS as a
# real type expression when inferring downstream annotations.


def normalise_primitive(value: JSONPrimitive) -> str:
    """Return normalise primitive.

    Args:
        value (JSONPrimitive): TODO.

    Returns:
        str: TODO.

    """
    return "null" if value is None else str(object=value)


def join_string_list(parts: StringList, sep: str = ", ") -> str:
    """Return join string list.

    Args:
        parts (StringList): TODO.
        sep (str): TODO.

    Returns:
        str: TODO.

    """
    return sep.join(parts)


# =============================================================================
# 74. Async generator — autotype's ``AsyncIterator`` return inference
# =============================================================================
# An ``async def`` whose body uses ``yield`` should be annotated as
# ``AsyncIterator[...]``; the element type is inferred from the yield expr.


async def count_async(limit: int) -> AsyncIterator[int]:
    """Return count async.

    Args:
        limit (int): TODO.

    Returns:
        AsyncIterator[int]: TODO.

    Yields:
            int: TODO.

    """
    n: int = 0
    while n < limit:
        yield n
        n += 1
        await sleep(delay=0)


async def collect_async(limit: int) -> list[int]:
    """Return collect async.

    Args:
        limit (int): TODO.

    Returns:
        list[int]: TODO.

    """
    return [value async for value in count_async(limit=limit)]


# =============================================================================
# 75. Context manager protocol — ``__enter__`` / ``__exit__`` self-typing
# =============================================================================
# autotype should annotate ``__enter__`` as returning ``Self`` and
# ``__exit__`` as returning ``bool | None`` with the standard exception-info
# signature.


class Transaction:
    """Represent Transaction."""

    def __init__(self, label: str) -> None:
        """Return init.

        Args:
            label (str): TODO.

        """
        self.label: str = label
        self.entered: bool = False

    def __enter__(self) -> Self:
        """Return enter.

        Returns:
            Self: TODO.

        """
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        """Return exit.

        Args:
            exc_type (type[BaseException] | None): TODO.
            exc (BaseException | None): TODO.
            tb (TracebackType | None): TODO.

        Returns:
            bool: TODO.

        """
        self.entered = False
        return False


# =============================================================================
# 76. Additional inference stress cases — factories, scopes, overload-like
# flows
# =============================================================================
# These cases intentionally stress places where automatic typing tools
# commonly fall back to ``object`` or accidentally change runtime behavior.


@dataclass
class EventLog[NameT: Hashable]:
    """Track numeric totals per hashable event name.

    Attributes:
        names (list[NameT]): TODO.
        counts (dict[NameT, float]): TODO.
        seen (set[NameT]): TODO.

    """

    names: list[NameT] = field(default_factory=list)
    counts: NameTToFloatMap[NameT] = field(default_factory=dict)
    seen: set[NameT] = field(default_factory=set)

    def add(self, name: NameT, amount: float = 1) -> Self:
        """Return add.

        Args:
            name (NameT): TODO.
            amount (float): TODO.

        Returns:
            Self: TODO.

        """
        _ = self.names.append(name)
        self.counts[name] = self.counts.get(name, 0) + amount
        _ = self.seen.add(name)
        return self

    def summary(self) -> NameTToFloatMap[NameT]:
        """Return summary.

        Returns:
            dict[NameT, float]: TODO.

        """
        return {name: self.counts[name] for name in self.seen}


@dataclass
class KeyValueStore[KeyT: Hashable, ValueT]:
    """Store values under hashable keys with precise retrieval types.

    Attributes:
        values (dict[KeyT, ValueT]): TODO.

    """

    values: dict[KeyT, ValueT] = field(default_factory=dict)

    def get_or[DefaultT](
        self,
        key: KeyT,
        default: DefaultT,
    ) -> ValueT | DefaultT:
        """Return get or.

        Args:
            key (KeyT): TODO.
            default (DefaultT): TODO.

        Returns:
            ValueT | DefaultT: TODO.

        """
        return self.values.get(key, default)

    def keys_list(self) -> list[KeyT]:
        """Return keys list.

        Returns:
            list[KeyT]: TODO.

        """
        return list(self.values.keys())

    def put(self, key: KeyT, value: ValueT) -> ValueT | None:
        """Return put.

        Args:
            key (KeyT): TODO.
            value (ValueT): TODO.

        Returns:
            ValueT | None: TODO.

        """
        previous: ValueT | None = self.values.get(key)
        self.values[key] = value
        return previous

    def values_list(self) -> list[ValueT]:
        """Return values list.

        Returns:
            list[ValueT]: TODO.

        """
        return list(self.values.values())


class FluentCounter:
    """Self-returning mutator should infer Self for fluent methods."""

    def __init__(self) -> None:
        """Return init."""
        self.total: int = 0

    @classmethod
    def from_values(cls, values: Iterable[int]) -> FluentCounter:
        """Return from values.

        Args:
            values (Iterable[int]): TODO.

        Returns:
            FluentCounter: TODO.

        """
        instance: FluentCounter = cls()
        value: int
        for value in values:
            _: Self = instance.add(amount=value)
        return instance

    def add(self, amount: int) -> Self:
        """Return add.

        Args:
            amount (int): TODO.

        Returns:
            Self: TODO.

        """
        self.total += amount
        return self

    def reset(self) -> Self:
        """Return reset.

        Returns:
            Self: TODO.

        """
        self.total = 0
        return self


class LazyValue:
    """Property and cached state should keep optional narrowing precise."""

    def __init__(self, raw: str) -> None:
        """Return init.

        Args:
            raw (str): TODO.

        """
        self.raw: str = raw
        self._cached: OptionalString = None

    @property
    def value(self) -> str:
        """Return value.

        Returns:
            str: TODO.

        """
        if self._cached is None:
            self._cached = self.raw.strip().lower()
        return self._cached


class SupportsStringAttributes(Protocol):
    """Expose a string-valued instance attribute dictionary.

    Attributes:
        __dict__ (dict[str, str]): TODO.

    """

    __dict__: StringToString


class Descriptor:
    """String descriptor backed by the instance attribute dictionary."""

    def __init__(self, default: str) -> None:
        """Return init.

        Args:
            default (str): TODO.

        """
        self.default: str = default
        self.name: str = ""

    @overload
    def __get__(
        self,
        instance: None,
        owner: DescriptorUserType,
    ) -> Self: ...

    @overload
    def __get__(
        self,
        instance: SupportsStringAttributes,
        owner: DescriptorUserType,
    ) -> str: ...

    def __get__(
        self,
        instance: SupportsStringAttributes | None,
        owner: DescriptorUserType | None = None,
    ) -> Self | str:
        """Return get.

        Args:
            instance (SupportsStringAttributes | None): TODO.
            owner (type[DescriptorUser] | None): TODO.

        Returns:
            Self | str: TODO.

        """
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance: SupportsStringAttributes, value: str) -> None:
        """Return set.

        Args:
            instance (SupportsStringAttributes): TODO.
            value (str): TODO.

        """
        instance.__dict__[self.name] = value

    def __set_name__(self, owner: DescriptorUserType, name: str) -> None:
        """Return set name.

        Args:
            owner (type[DescriptorUser]): TODO.
            name (str): TODO.

        """
        self.name = name


class DescriptorUser:
    """Represent DescriptorUser.

    Attributes:
        label (Descriptor): TODO.

    """

    label: Descriptor = Descriptor(default="unknown")

    def rename(self, value: str) -> str:
        """Return rename.

        Args:
            value (str): TODO.

        Returns:
            str: TODO.

        """
        self.label = value
        return self.label


class _SentinelMissing(Enum):
    """Internal sentinel for context-manager identity narrowing."""

    TOKEN = auto()


@contextmanager
def temporary_mapping_value[K, V](
    mapping: MutableMapping[K, V],
    key: K,
    value: V,
) -> Generator[V | None]:
    """Context manager should infer the yielded previous value.

    Args:
        mapping (MutableMapping[K, V]): TODO.
        key (K): TODO.
        value (V): TODO.

    Yields:
        V | None: TODO.

    """
    missing: _SentinelMissing = _SentinelMissing.TOKEN
    previous: V | _SentinelMissing = mapping.get(key, missing)
    mapping[key] = value
    try:
        yield previous if previous is not missing else None
    finally:
        if previous is missing:
            _ = mapping.pop(key, None)
        else:
            mapping[key] = previous


def select_first_present(
    primary: OptionalString,
    secondary: OptionalString,
    fallback: str,
) -> str:
    """Identity-preserving union/narrowing across three candidate values.

    Args:
        primary (str | None): TODO.
        secondary (str | None): TODO.
        fallback (str): TODO.

    Returns:
        str: TODO.

    """
    if primary is not None:
        return primary
    if secondary is not None:
        return secondary
    return fallback


def transpose_pairs[A, B](
    pairs: Iterable[tuple[A, B]],
) -> tuple[list[A], list[B]]:
    """Infer tuple element relationships without collapsing to object.

    Args:
        pairs (Iterable[tuple[A, B]]): TODO.

    Returns:
        tuple[list[A], list[B]]: TODO.

    """
    left: list[A] = []
    right: list[B] = []
    for first, second in pairs:
        _ = left.append(first)
        _ = right.append(second)
    return left, right


def group_by_key[T, K](
    rows: Iterable[T],
    key_func: Callable[[T], K],
) -> KToTListMap[K, T]:
    """Callable return drives dict key type; rows preserve element type.

    Args:
        rows (Iterable[T]): TODO.
        key_func (Callable[[T], K]): TODO.

    Returns:
        dict[K, list[T]]: TODO.

    """
    grouped: KToTListMap[K, T] = {}
    row: T
    for row in rows:
        key: K = key_func(row)
        _ = grouped.setdefault(key, []).append(row)
    return grouped


def invert_mapping[K, V: Hashable](mapping: Mapping[K, V]) -> dict[V, K]:
    """Swap key/value types when values are hashable.

    Args:
        mapping (Mapping[K, V]): TODO.

    Returns:
        dict[V, K]: TODO.

    """
    return {value: key for key, value in mapping.items()}


def merge_optional_dicts(
    left: MappingStrInt,
    right: StringToInt | None = None,
) -> StringToInt:
    """Narrow optional dictionary input before updating.

    Args:
        left (Mapping[str, int]): TODO.
        right (dict[str, int] | None): TODO.

    Returns:
        dict[str, int]: TODO.

    """
    merged: StringToInt = dict(left)
    if right is not None:
        _ = merged.update(right)
    return merged


def safe_index[T](
    items: Sequence[T],
    index: int,
    default: T | None = None,
) -> T | None:
    """Element type should unify with default type only when needed.

    Args:
        items (Sequence[T]): TODO.
        index (int): TODO.
        default (T | None): TODO.

    Returns:
        T | None: TODO.

    """
    try:
        return items[index]
    except IndexError:
        return default


def _parse_int_or_error(
    value: FloatOrStr,
) -> tuple[OptionalInt, OptionalString]:
    """Parse a numeric value and preserve its conversion error.

    Args:
        value (str | float): TODO.

    Returns:
        tuple[int | None, str | None]: TODO.

    """
    try:
        return int(value), None
    except ValueError as error:
        return None, str(object=error)


def parse_ints_with_errors(
    values: Iterable[StrOrIntOrFloat],
) -> ParsedIntegers:
    """Keep successfully parsed integers and their original failures.

    Args:
        values (Iterable[str | int | float]): TODO.

    Returns:
        tuple[list[int], list[tuple[str | int | float, str]]]: TODO.

    """
    parsed: list[int] = []
    errors: TupleStrOrIntOrFloatStrList = []
    value: FloatOrStr
    for value in values:
        parsed_value: OptionalInt
        error_message: OptionalString
        parsed_value, error_message = _parse_int_or_error(value=value)
        if error_message is not None:
            _ = errors.append((value, error_message))
        elif parsed_value is not None:
            _ = parsed.append(parsed_value)
    return parsed, errors


def nested_match_payload(
    payload: JSONObject,
) -> FloatOrIntOrOptionalString:
    """Pattern matching should narrow nested dict/list shapes.

    Args:
        payload (dict[str, JSONValue]): TODO.

    Returns:
        float | int | str | None: TODO.

    Raises:
        TypeError: TODO.

    """
    match payload:
        case {"kind": "point", "coords": [x, y]}:
            if not (
                isinstance(x, (str, int, float))
                and isinstance(y, (str, int, float))
            ):
                msg: str = "expected numeric x, y"
                raise TypeError(msg)
            return float(x) + float(y)
        case {"kind": "name", "value": str(name)}:
            return name.title()
        case {"kind": "items", "value": [*items]}:
            return len(items)
        case _:
            return None


def build_typed_dict_like(
    name: str,
    age: int,
    *,
    active: bool = True,
) -> UserRecord:
    """Repeated literal keys should be candidates for TypedDict inference.

    Args:
        name (str): TODO.
        age (int): TODO.
        active (bool): TODO.

    Returns:
        UserRecord: TODO.

    """
    return {
        "name": name,
        "age": age,
        "active": active,
    }


def read_known_json_user(blob: str) -> StringIntPair:
    """Schema-like validation should refine json.loads object values.

    Args:
        blob (str): TODO.

    Returns:
        tuple[str, int]: TODO.

    Raises:
        TypeError: TODO.

    """
    data: JSONValue = cast(typ="JSONValue", val=loads(s=blob))
    if not isinstance(data, dict):
        msg: str = "expected object"
        raise TypeError(msg)
    name: OptionalJSONValue = data.get("name")
    age: OptionalJSONValue = data.get("age")
    if not isinstance(name, str):
        msg = "expected string name"
        raise TypeError(msg)
    if not isinstance(age, int):
        msg = "expected integer age"
        raise TypeError(msg)
    return name, age


def callback_pipeline(
    value: str,
    *callbacks: StringTransform,
) -> str:
    """Sequential callable output should feed the next callable input.

    Args:
        value (str): TODO.
        *callbacks (Callable[[str], str]): TODO.

    Returns:
        str: TODO.

    """
    current: str = value
    callback: StringTransform
    for callback in callbacks:
        current = callback(current)
    return current


def make_counter_closure(
    start: float = 0,
) -> FloatToFloatCallable:
    """Closure variable mutation should preserve numeric type.

    Args:
        start (float): TODO.

    Returns:
        Callable[[float], float]: TODO.

    """
    total: float = start

    def add(amount: float) -> float:
        """Return add.

        Args:
            amount (float): TODO.

        Returns:
            float: TODO.

        """
        nonlocal total
        total += amount
        return total

    return add


def make_registry() -> FunctionRegistry:
    """Nested functions stored in dict should preserve callable returns.

    Returns:
        FunctionRegistry: TODO.

    """

    def as_upper(value: str) -> str:
        """Return as upper.

        Args:
            value (str): TODO.

        Returns:
            str: TODO.

        """
        return value.upper()

    def as_length(value: Sized) -> int:
        """Return as length.

        Args:
            value (Sized): TODO.

        Returns:
            int: TODO.

        """
        return len(value)

    return {
        "upper": as_upper,
        "length": as_length,
    }


def add_logging[**P, R](func: PToRCallable[P, R]) -> PToRCallable[P, R]:
    """Preserve the wrapped function signature while logging its name.

    Demonstrates the v4 §3 Target 1 pattern: a function-shaped decorator
    that preserves the wrapped callable's full signature through a
    nested ``wrapper`` that forwards both positional and keyword
    argument packs. The ParamSpec promotion pass should rewrite this as
    ``add_logging[**P, R](func: Callable[P, R]) -> Callable[P, R]`` with
    the wrapper typed as ``(*args: P.args, **kwargs: P.kwargs) -> R``.

    Args:
            func (Callable[P, R]): TODO.

    Returns:
            Callable[P, R]: TODO.

    """

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        """Return wrapper.

        Args:
            *args (P.args): TODO.
            **kwargs (P.kwargs): TODO.

        Returns:
            R: TODO.

        """
        aprint(func.__name__)
        return func(*args, **kwargs)

    return wrapper


def trace_method[SelfT, **P, R](
    func: BoundMethodCallable[SelfT, P, R],
) -> BoundMethodCallable[SelfT, P, R]:
    """Preserve the bound-method signature.

    Demonstrates the v5 §3 Target 2 pattern: a wrapper whose first
    positional parameter is the bound ``self``, followed by the forwarded
    ``*args``/``**kwargs`` pack. The ParamSpec method- decorator
    promotion pass should rewrite this as ``trace_method[SelfT,
    **P, R](func: Callable[Concatenate[SelfT, P], R])`` so the
    bound receiver's type is preserved through ``Concatenate``.

    Args:
            func (Callable[Concatenate[SelfT, P], R]): TODO.

    Returns:
            Callable[Concatenate[SelfT, P], R]: TODO.

    """

    def wrapper(self: SelfT, *args: P.args, **kwargs: P.kwargs) -> R:
        """Return wrapper.

        Args:
            self: The bound-method receiver.
            *args (P.args): TODO.
            **kwargs (P.kwargs): TODO.

        Returns:
            R: TODO.

        """
        return func(self, *args, **kwargs)

    return wrapper


# =============================================================================
# 25. TypeVarTuple stress fixtures (v4 §4 — inference deferred, fixtures only)
# =============================================================================
# These two functions are the canonical variadic-tuple-pack and variadic-
# callback-pack patterns that future TypeVarTuple inference work must
# distinguish from ordinary homogeneous ``*args``. They are present in the
# demo as stress fixtures: the inference pass does not yet rewrite them, but
# their continued presence (and the basedpyright clean status of the generated
# output) is the regression gate for the upcoming TypeVarTuple bundle.


def rotate_left[T, *Ts](
    items: tuple[T, *Ts],
) -> tuple[*Ts, T]:
    """Rotate a tuple left one position while preserving its element types.

    Demonstrates ``TypeVarTuple`` shape-preservation: the return type
    re-orders the pack so the first element moves to the end while each
    non-first element keeps its precise type. This is the smallest test
    that distinguishes ``TypeVarTuple`` from homogeneous ``tuple[T, ...]``.

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
            *args (*Ts): TODO.

    Returns:
            R: TODO.

    """
    return callback(*args)


def sum_values(*values: float) -> float:
    """Sum a homogeneous variadic ``float`` pack.

    Negative ``TypeVarTuple`` fixture: ``*values: float`` is a homogeneous
    pack, so a future ``TypeVarTuple`` inference pass must leave it verbatim
    and NOT promote it to ``*Ts``. v5 §5 requires this distinction; the
    regression gate is in :class:`TestV5TypeVarTupleNegativeFixture`.

    Args:
            *values (float): TODO.

    Returns:
            float: TODO.

    """
    return sum(values)


async def async_fetch_one(
    name: str,
    delay: float = 0,
) -> AsyncFetchResult:
    """Coroutine result type should survive gather/create_task.

    Args:
        name (str): TODO.
        delay (float): TODO.

    Returns:
        AsyncFetchResult: TODO.

    """
    await sleep(delay=delay)
    return {"name": name, "size": len(name)}


async def async_fetch_many(
    names: StrIterable,
) -> AsyncFetchResultList:
    """Return async fetch many.

    Args:
        names (Iterable[str]): TODO.

    Returns:
        list[AsyncFetchResult]: TODO.

    """
    tasks: list[Task[AsyncFetchResult]] = [
        create_task(coro=async_fetch_one(name=name)) for name in names
    ]
    return await gather(*tasks)


def path_roundtrip(path: str) -> TupleStrStrPath:
    """PathLike/string inputs often need pathlib-aware inference.

    Args:
        path (str): TODO.

    Returns:
        tuple[str, str, Path]: TODO.

    """
    resolved: Path = Path(path).expanduser()
    return resolved.name, resolved.suffix, resolved.parent


def regex_groupdict(text: str) -> StrToOptionalStringMap:
    """Regex match narrowing should refine groupdict return.

    Args:
        text (str): TODO.

    Returns:
        dict[str, str | None]: TODO.

    """
    match: OptionalStrMatch = re_match(
        pattern=r"(?P<name>[a-z]+)-(?P<id>\d+)$",
        string=text,
    )
    if match is None:
        return {}
    return match.groupdict()


def bytes_text_boundary(
    data: BytesOrText,
    encoding: str = "utf-8",
) -> BytesOrText:
    """Bytes/str conversion should not collapse to object.

    Args:
        data (bytes | str): TODO.
        encoding (str): TODO.

    Returns:
        bytes | str: TODO.

    """
    if isinstance(data, bytes):
        return data.decode(encoding)
    return data.encode(encoding)


def variadic_numeric_sum(*values: float, scale: float = 1) -> float:
    """Variadic args plus keyword-only numeric parameter.

    Args:
        scale (float): TODO.
        *values (float): TODO.

    Returns:
        float: TODO.

    """
    total: float = 0
    value: float
    for value in values:
        total += value
    return total * scale


class Plugin[InputT, OutputT](Protocol):
    """Execute a transformation preserving its input/output contract."""

    def run(self, payload: InputT) -> OutputT:
        """Run the plugin against ``payload``.

        Args:
            payload (InputT): TODO.

        Returns:
            OutputT: TODO.

        """
        ...


class EchoPlugin:
    """Represent EchoPlugin."""

    def run[T](self, payload: T) -> T:
        """Return run.

        Args:
            payload (T): TODO.

        Returns:
            T: TODO.

        """
        return payload


class SizePlugin:
    """Represent SizePlugin."""

    def run(self, payload: Sized) -> int:
        """Return run.

        Args:
            payload (Sized): TODO.

        Returns:
            int: TODO.

        """
        return len(payload)


@overload
def run_plugin(plugin: EchoPlugin, payload: str) -> str: ...


@overload
def run_plugin(plugin: SizePlugin, payload: str) -> int: ...


def run_plugin(
    plugin: Plugin[str, str] | Plugin[str, int],
    payload: str,
) -> str | int:
    """Structural protocol candidate from repeated .run() calls.

    Args:
        plugin (Plugin[str, str] | Plugin[str, int]): TODO.
        payload (str): TODO.

    Returns:
        str | int: TODO.

    """
    return plugin.run(payload)


def stress_smoke_calls() -> StressSmokeResults:
    """Return deterministic outputs for the additional stress section.

    Returns:
        StressSmokeResults: TODO.

    """
    event_log: EventLog[str] = (
        EventLog[str]()
        .add(name="a")
        .add(name="b", amount=2)
        .add(name="a", amount=3)
    )
    store: KeyValueStore[str, int] = KeyValueStore[str, int]()
    previous: OptionalInt = store.put(key="x", value=1)
    _ = store.put(key="y", value=2)
    counter: FluentCounter = FluentCounter.from_values(values=[1, 2, 3]).add(
        amount=4,
    )
    lazy: LazyValue = LazyValue(raw="  Hello  ")
    descriptor_value: str = DescriptorUser().rename(value="Ada")
    mapping: StringToInt = {"a": 1}
    old_value: OptionalInt
    with temporary_mapping_value(
        mapping=mapping,
        key="a",
        value=9,
    ) as old_value:
        temporary_value: int = mapping["a"]
    add: FloatToFloatCallable = make_counter_closure(start=10)
    registry: FunctionRegistry = make_registry()
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
            primary=None,
            secondary="secondary",
            fallback="fallback",
        ),
        "transpose": transpose_pairs(pairs=[("a", 1), ("b", 2)]),
        "group": group_by_key(rows=["aa", "b"], key_func=len),
        "invert": invert_mapping(mapping={"a": 1, "b": 2}),
        "merge": merge_optional_dicts(left={"a": 1}, right={"b": 2}),
        "safe_index": safe_index(items=[1, 2], index=9, default=-1),
        "parsed": parse_ints_with_errors(values=["1", "x", "3"]),
        "match_point": nested_match_payload(
            payload={"kind": "point", "coords": [1, 2]},
        ),
        "typed_dict_like": build_typed_dict_like(name="Ada", age=37),
        "json_user": read_known_json_user(blob='{"name":"Ada","age":37}'),
        "callback": callback_pipeline(" ada ", str.strip, str.title),
        "closure": (add(5), add(2)),
        "registry": (registry["upper"]("ada"), registry["length"]("ada")),
        "async_many": asyncio_run(main=async_fetch_many(names=["aa", "bbb"])),
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
    aprint("google_style ->", google_style(names=["  a ", "b"]))
    aprint("union_via_reassignment ->", union_via_reassignment(flag=True))
    aprint("narrow_via_is_none(None) ->", narrow_via_is_none(value=None))
    aprint("colour_to_hex('red') ->", colour_to_hex(colour="red"))
    aprint("build_user_record ->", build_user_record(name="alice", age=30))
    aprint(
        "Vector3 dot ->",
        Vector3(x=1, y=2, z=3).dot(other=Vector3(x=4, y=5, z=6)),
    )
    aprint("Builder ->", Builder().add(x="a").add(x="b").build())
    aprint("top_words ->", top_words(text="a a b c a b", n=2))
    aprint("yield_in_loop ->", list(yield_in_loop(n=3)))
    aprint(
        "first_long_token ->",
        first_long_token(text="short pretty looong tail"),
    )
    aprint("describe_action ->", describe_action(payload={"kind": "stop"}))
    aprint("parse_user_json ->", parse_user_json(blob='{"name":"x","age":7}'))
    aprint("extract_first_int ->", extract_first_int(text="ab12cd34"))
    aprint("normalise_whitespace ->", normalise_whitespace(text="a  b\tc"))
    aprint("length_doubled ->", length_doubled(text="abc"))
    aprint("temperature_score ->", temperature_score(celsius=25))
    aprint("grade_from_score ->", grade_from_score(score=83))
    aprint("OrderingHeavy ->", OrderingHeavy(items=[1, 2, 3]).public_action())
    aprint("fib(10) ->", fib(n=10))
    aprint("status_priority ->", status_priority(status=Status.RUNNING))
    aprint("HistoryBuffer ->", HistoryBuffer(items=["a", "b"]).count)
    aprint("walrus_filter ->", walrus_filter(items=["  ", "x", "y "]))
    aprint("format_record ->", format_record(name="bob", score=87.5, width=8))
    aprint("CountDown ->", list(CountDown(start=3)))
    aprint("is_str_list ->", join_if_strings(items=["a", "b"]))
    aprint("consume_gate ->", asyncio_run(main=consume_gate(limit=3)))
    aprint("forward_narrow ->", forward_narrow_pipeline(raw="17:42:99"))
    aprint("call_packet_helpers ->", call_packet_helpers())
    aprint("use_closures ->", use_closures())
    aprint("process_status ->", process_status(status="active"))
    aprint("handle_mode ->", handle_mode(mode="inactive"))
    aprint("render_state ->", render_state(state="active"))
    aprint("cached_fib(10) ->", cached_fib(n=10))
    aprint("cached_title ->", cached_title(value="  hello world  "))
    aprint("FormalGreeter ->", FormalGreeter().greet(name="Ada"))
    aprint("CasualGreeter ->", CasualGreeter().greet(name="Ada"))
    aprint("batch_summary ->", batch_summary())
    aprint("render_help_banner ->", repr(render_help_banner()[:30]))
    aprint(
        "render_sql_template ->",
        repr(render_sql_template(table="users")[:30]),
    )
    aprint("render_html_skeleton ->", repr(render_html_skeleton()[:30]))
    aprint(
        "parse_with_doc_types ->",
        parse_with_doc_types(raw="a:b:c", retries=2),
    )
    aprint("call_registry ->", call_registry())
    aprint("physics_step ->", physics_step(velocity=10.0, acceleration=0.5))
    _demo_extras()
    _ = time_sleep(1)


def _demo_extras() -> None:
    """Smoke-call the PEP 695 / async / context-manager sections."""
    aprint("first_of([1,2]) ->", first_of(items=[1, 2]))
    aprint("pair_keys ->", pair_keys(mapping={"a": 1, "b": 2}))
    aprint("normalise_primitive(None) ->", normalise_primitive(value=None))
    aprint("join_string_list ->", join_string_list(parts=["a", "b"]))
    aprint("collect_async(3) ->", asyncio_run(main=collect_async(limit=3)))
    txn: Transaction
    with Transaction(label="demo") as txn:
        aprint("Transaction entered ->", txn.entered)
    aprint("stress_smoke_calls ->", stress_smoke_calls())


if __name__ == "__main__":
    _demo_main()
