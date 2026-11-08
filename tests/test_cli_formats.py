"""``check --format json`` emits parseable JSON findings."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, cast

from astart.cli.commands import CheckSettings, run_check
from astart.rules.vocabulary import Severity

from tests.expectations import expect_equal, expect_in, expect_true

if TYPE_CHECKING:
    from pathlib import Path


def test_check_json_output_parses(tmp_path: Path) -> None:
    """Check JSON findings carry ``code``, ``message`` and ``line``.

    ``render_json`` puts ``path`` on each file entry and the finding keys
    on each element of its ``findings`` list. ``run_check`` is called
    directly because ``main`` writes to the import-time ``sys.stdout``.

    Args:
        tmp_path: pytest temporary directory.

    """
    target: Path = tmp_path / "pending.py"
    target.write_text(
        data="def f(a, b):\n    pass\n\nf(1, 2)\n",
        encoding="utf-8",
    )
    out: StringIO = StringIO()
    rc: int = run_check(
        settings=CheckSettings(
            paths=(target,),
            output_format="json",
            fail_on=Severity.error,
            stubs_path=None,
        ),
        out=out,
    )
    expect_equal(actual=rc, expected=1)
    entries: list[dict[str, object]] = loads(s=out.getvalue())
    expect_true(condition=len(entries) > 0)
    for entry in entries:
        expect_in(item="path", container=entry)
        findings: object = entry["findings"]
        expect_true(condition=isinstance(findings, list))
        for raw in cast(typ="list[dict[str,object]]", val=findings):
            finding: dict[str, object] = raw
            for key in ("code", "message", "line"):
                expect_in(item=key, container=finding)
