"""The accuracy-contract targets: evaluation, collection and table coverage."""

from __future__ import annotations

from re import Match, Pattern
from re import compile as re_compile
from typing import TYPE_CHECKING, Final, final

from scripts.benchmark.targets import (
    Target,
    evaluate,
    format_row,
    load_targets,
)
from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        targets_file (Final[Path]): The shipped target list.
        todo (Final[Path]): The TODO document holding the contract table.
        contract_row (Final[Pattern[str]]): Regex matching an ``A-NN`` contract
            table row.
        min_contract_rows (Final[int]): Contract rows the table must at least
            have.

    """

    root: Final[Path] = Paths.root
    targets_file: Final[Path] = (
        Paths.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "targets.json"
    )
    todo: Final[Path] = Paths.root / "docs" / "planning" / "TODO.md"
    contract_row: Final[Pattern[str]] = re_compile(
        pattern=r"^\| (A-\d\d) \|",
    )
    min_contract_rows: Final[int] = 11


def _target(*, op: str, value: float = 0.9) -> Target:
    """Build a target for operator tests.

    Args:
        op (str): The comparison operator.
        value (float): The threshold.

    Returns:
        Target: The target.

    """
    return Target(
        id="A-00",
        metric="test.metric",
        op=op,
        value=value,
    )


def _contract_ids() -> set[str]:
    """Read the A-NN ids of the Accuracy contract table.

    The table lives in ``docs/planning/TODO.md``.

    Returns:
        set[str]: The ids of every contract row.

    """
    ids: set[str] = set()
    in_table: bool = False
    for line in Constants.todo.read_text(encoding="utf-8").splitlines():
        if "Accuracy contract" in line:
            in_table = True
        elif in_table and line.startswith("## ") and ids:
            break
        if in_table:
            found: Match[str] | None = Constants.contract_row.match(
                string=line,
            )
            if found is not None:
                ids.add(found.group(1))
    return ids


def test_evaluate_covers_every_operator() -> None:
    """Check each ``op`` string maps to the right comparison."""
    reports: Mapping[str, float] = {"test.metric": 0.9}
    expect_true(
        condition=evaluate(
            target=_target(op=">="),
            reports=reports,
        ),
    )
    expect_true(
        condition=evaluate(
            target=_target(op="<=", value=0.95),
            reports=reports,
        ),
    )
    expect_true(
        condition=evaluate(
            target=_target(op="==", value=0.9),
            reports=reports,
        ),
    )
    expect_false(
        condition=evaluate(
            target=_target(op="<", value=0.9),
            reports=reports,
        ),
    )
    expect_true(
        condition=evaluate(
            target=_target(op=">", value=0.5),
            reports=reports,
        ),
    )
    expect_true(
        condition=evaluate(
            target=_target(op="!=", value=0.5),
            reports=reports,
        ),
    )


def test_evaluate_fails_when_the_metric_is_missing() -> None:
    """Check an uncollected metric fails rather than passing silently."""
    expect_false(
        condition=evaluate(
            target=_target(op=">="),
            reports={},
        ),
    )


def test_targets_json_covers_the_contract_table_and_vice_versa() -> None:
    """Check every contract row has targets and every target a row."""
    contract: set[str] = _contract_ids()
    expect_true(condition=len(contract) >= Constants.min_contract_rows)
    shipped: set[str] = {
        target.id for target in load_targets(path=Constants.targets_file)
    }
    expect_equal(actual=shipped, expected=contract)


def test_format_row_renders_verdict_and_threshold() -> None:
    """Check the printed row matches ``A-02  FAIL  52.5 % < 90 %``."""
    row: str = format_row(
        target=Target(
            id="A-02",
            metric="pair.dev.params.exact_share",
            op=">=",
            value=0.9,
        ),
        reports={"pair.dev.params.exact_share": 0.525},
    )
    expect_in(item="A-02", container=row)
    expect_in(item="FAIL", container=row)
    expect_in(item="52.5 %", container=row)
    expect_in(item="90 %", container=row)
    missing: str = format_row(
        target=_target(op=">="),
        reports={},
    )
    expect_in(item="n/a", container=missing)
