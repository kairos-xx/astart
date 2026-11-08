"""Fuzz the writer: any subset of fixes must still yield valid code."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from io import StringIO
from pathlib import Path
from tokenize import COMMENT, generate_tokens
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from astart.rules import Catalog
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        files: Small corpus modules to fuzz.
        seeds: Number of random fix subsets per module.

    """

    files: Final[tuple[str, ...]] = (
        "abc.py.txt",
        "csv.py.txt",
        "graphlib.py.txt",
        "types.py.txt",
        "zipapp.py.txt",
        "tomllib__parser.py.txt",
    )
    seeds: Final[int] = 3


def _subset(*, catalog: Catalog, keys: frozenset[str]) -> Catalog:
    """Keep only the named fixes, and only the rules that offer them.

    Args:
        catalog: Full catalog.
        keys: Fix keys to keep.

    Returns:
        A catalog whose rules reference only kept fixes.

    """
    return replace(
        catalog,
        fixes=tuple(fix for fix in catalog.fixes if fix.key in keys),
        rules=tuple(
            replace(
                rule,
                fixes=tuple(key for key in rule.fixes if key in keys),
            )
            for rule in catalog.rules
        ),
    )


def _comments(*, text: str) -> list[str]:
    """List the comment texts of a source.

    Args:
        text: Python source.

    Returns:
        Comments in order.

    """
    return [
        token.string
        for token in generate_tokens(
            readline=StringIO(initial_value=text).readline,
        )
        if token.type == COMMENT
    ]


@pytest.mark.parametrize("name", Constants.files)
def test_random_fix_subsets_stay_valid(*, name: str) -> None:
    """Check that random fix subsets stay valid.

    Args:
        name: Corpus file name.

    """
    source: str = (Path(__file__).parent / "corpus" / name).read_text(
        encoding="utf-8",
    )
    registries: Registries = default_registries()
    full: Catalog = load_default_catalog(
        registries=registries,
    )
    every: list[str] = sorted(fix.key for fix in full.fixes)
    for seed in range(Constants.seeds):
        mask: int = int.from_bytes(
            bytes=sha256(data=f"{name}:{seed}".encode()).digest()[:4],
        )
        keys: frozenset[str] = frozenset(
            key for bit, key in enumerate(iterable=every) if (mask >> bit) & 1
        ) or frozenset(every[:1])
        result: FixResult = fix_source(
            source=source,
            filename=name,
            catalog=_subset(catalog=full, keys=keys),
            registries=registries,
            settings=FixSettings(ceiling=FixSafety.guarded),
        )
        expect_equal(actual=result.parse_error, expected=None)
        _ = compile(source=result.source, filename=name, mode="exec")
        expect_equal(
            actual=_comments(text=result.source),
            expected=_comments(text=source),
            message=f"{name} seed {seed} keys {sorted(keys)}",
        )
