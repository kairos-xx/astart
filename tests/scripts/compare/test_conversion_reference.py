"""Reference evidence integrity and fair conversion-report comparisons."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from json import dumps
from typing import TYPE_CHECKING

import pytest
from astart.rules import recovery

from scripts.compare.conversion_report import (
    Item,
    Sources,
    case,
    compare,
    contract_meaning,
    load_reference,
    pair_json,
    summary_table,
)
from tests.support.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_true,
)
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from scripts.compare.conversion_report import ReferenceGraph


def test_reference_keeps_overloads_and_context() -> None:
    """Resolve every authored annotation's declared and contextual evidence."""
    root: Path = Paths.root
    graph: ReferenceGraph = load_reference(
        path=root / "fixtures" / "artifacts" / "typed_graph.json",
        source=(root / "fixtures" / "typed.py").read_text(
            encoding="utf-8",
        ),
    )
    targets: list[str] = [
        target["path"]
        for target in graph.document["annotation_targets"].values()
    ]
    expect_equal(actual=len(targets), expected=1182)
    expect_true(condition=any("#overload:" in key for key in targets))
    for key in targets:
        base: str = key.split(sep="#overload:", maxsplit=1)[0]
        expect_true(condition=bool(graph.facts(key=base)))
    expect_true(
        condition=any(
            target["supporting_evidence_ids"]
            for target in graph.document["annotation_targets"].values()
        ),
    )
    vector: str = graph.targets(
        key="SupportsAdditionAndXAndY.__add__.other",
    )[0]["expected_type_id"]
    reading: str = contract_meaning(graph=graph, type_id=vector)
    expect_in(item="`x`", container=reading)
    expect_in(item="`y`", container=reading)
    with pytest.raises(expected_exception=ValueError, match="stale"):
        _ = load_reference(path=graph.path, source="different source")


def test_broken_evidence_is_rejected(*, tmp_path: Path) -> None:
    """Reject dangling evidence instead of emitting an explanation.

    Args:
        tmp_path (Path): Temporary directory for a malformed reference fixture.

    """
    source: str = """\
x: int = 1
"""
    path: Path = tmp_path / "reference.json"
    _ = path.write_text(
        data=dumps(
            obj={
                "schema_version": "4.0.0",
                "revision": {
                    "source_digest": sha256(
                        string=source.encode(),
                    ).hexdigest(),
                },
                "annotation_targets": {
                    "ann_test": {
                        "evidence_ids": ["missing"],
                        "supporting_evidence_ids": [],
                    },
                },
                "evidence": {},
            },
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        expected_exception=ValueError,
        match="Unresolved reference evidence",
    ):
        _ = load_reference(path=path, source=source)


def test_reference_only_definitions_are_not_tool_failures() -> None:
    """Score current output and keep absent reference definitions separate."""
    items: list[Item]
    extra: dict[str, int]
    items, extra = compare(
        untyped="""\
def f(x):
    return x
""",
        typed="""\
def f(x: int | str) -> int | str:
    return x
def reference_only(x: bytes) -> bytes:
    return x
""",
        converted="""\
def f(x: str | int) -> str | int:
    return x
""",
        recovery=recovery,
    )
    verdicts: dict[str, str] = {item.key: item.verdict for item in items}
    expect_equal(actual=verdicts["f.x"], expected="exact")
    expect_equal(
        actual=verdicts["reference_only.x"],
        expected="reference_only",
    )
    counts: dict[str, Counter[str]] = {
        "parameters_and_returns": Counter(item.verdict for item in items),
        "variables": Counter(),
    }
    result: dict[str, dict[str, int]] = pair_json(counts=counts, extra=extra)
    expect_equal(
        actual=result["parameters_and_returns"]["to_recover"],
        expected=2,
    )
    expect_equal(
        actual=result["parameters_and_returns"]["missing"],
        expected=0,
    )


def test_alias_equivalence_does_not_count_as_looser() -> None:
    """Track spelling recovery separately without hiding tuple widening."""
    items, extra = compare(
        untyped="""\
def f(x):
    y = x
    return (1, 2)
""",
        typed="""\
type Vec = list[int]
type Result = tuple[int, ...]
def f(x: Vec) -> Result:
    y: Vec = x
    return (1, 2)
""",
        converted="""\
def f(x: list[int]) -> tuple[int, int]:
    y: list[int] = x
    return (1, 2)
""",
        recovery=recovery,
    )
    counts: dict[str, Counter[str]] = {
        scope: Counter(item.verdict for item in items if item.scope == scope)
        for scope in ("parameters_and_returns", "variables")
    }
    shaped: dict[str, dict[str, int]] = pair_json(counts=counts, extra=extra)
    for row in shaped.values():
        expect_equal(actual=row["correct"], expected=0)
        expect_equal(actual=row["equivalent"], expected=1)
        expect_equal(actual=row["looser"], expected=0)
        expect_equal(actual=row["semantic_exact"], expected=1)
        expect_equal(
            actual=row["to_recover"],
            expected=sum(
                row[key]
                for key in (
                    "correct",
                    "equivalent",
                    "narrower",
                    "looser",
                    "unresolved",
                    "wrong",
                    "missing",
                )
            ),
        )
    expect_equal(
        actual=shaped["parameters_and_returns"]["narrower"],
        expected=1,
    )
    rendered: str = "\n".join(summary_table(shaped=shaped))
    expect_in(item="Exact spelling", container=rendered)
    expect_in(item="Equivalent", container=rendered)
    expect_in(item="same type", container=rendered)


def test_case_has_hierarchy_and_qualified_diagnosis() -> None:
    """Keep successive cases separate and avoid invented failure causes."""
    item: Item = Item(
        scope="parameters_and_returns",
        key="f.x",
        verdict="wrong",
        written="int",
        author="str",
        family="Scalar",
    )
    sources: Sources = Sources(
        untyped=[],
        typed=[],
        converted=[],
        links={
            "typed": "reference.py",
            "untyped": "input.py",
            "converted": "out.py",
        },
        untyped_params={},
        untyped_vars={},
        anchors={},
        evidence=None,
        reasons={},
    )
    rendered: str = "\n".join(case(item=item, sources=sources))
    expect_in(
        item="""\
---

### Wrong annotation: `f.x`""",
        container=rendered,
    )
    expect_in(
        item="| Current tool output | Expected reference |",
        container=rendered,
    )
    expect_in(
        item="**2. Evidence in the untyped input**",
        container=rendered,
    )
    expect_in(
        item="No candidate-selection trace was recorded",
        container=rendered,
    )
    expect_not_in(item="no rule looked at it", container=rendered)
    expect_not_in(item="valid for every caller", container=rendered)
