"""Verify ``astart check --format`` reaches every reporter."""

from __future__ import annotations

from io import StringIO
from json import loads
from typing import TYPE_CHECKING, Final, Protocol, cast, final

import pytest
from astart.__main__ import main

from tests.support.expectations import expect_equal, expect_in, expect_true

type DictJsonValue = dict[str, JsonValue]

if TYPE_CHECKING:
    from pathlib import Path
    from xml.etree.ElementTree import Element

    from astart.rules.jsonvalue import JsonValue


class _DefusedParser(Protocol):
    """Typed view of defusedxml's untyped ``ElementTree.fromstring``."""

    def fromstring(self, *, text: str) -> Element:
        """Parse XML text into an element.

        Args:
            text (str): XML document text.

        Returns:
            The parsed root element.

        """
        ...


@final
class Constants:
    """Group module-level constants.

    Attributes:
        source (Final[str]): Module source producing exactly one ``TYP001``
            finding.

    """

    source: Final[str] = """\
from typing import Any


def f(x: Any) -> int:
    return 1
"""


def _xml_root(*, text: str) -> Element:
    """Parse reporter XML with defusedxml, skipping when it is absent.

    Args:
        text (str): XML document text.

    Returns:
        Element: The parsed root element.

    """
    parser: _DefusedParser = cast(
        typ="_DefusedParser",
        val=pytest.importorskip(modname="defusedxml.ElementTree"),
    )
    return parser.fromstring(text=text)


def _run(
    *,
    fmt: str,
    path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> str:
    """Run ``astart check --format`` on ``path`` and return stdout.

    Args:
        fmt (str): ``--format`` value.
        path (Path): File to check.
        monkeypatch (pytest.MonkeyPatch): Fixture replacing the module's stdout
            handle.

    Returns:
        str: Captured stdout text.

    """
    out: StringIO = StringIO()
    monkeypatch.setattr(target="astart.__main__.stdout", name=out)
    _ = main(argv=["check", str(object=path), "--format", fmt])
    return out.getvalue()


def _write(tmp_path: Path) -> Path:
    """Write the one-finding module into ``tmp_path``.

    Args:
        tmp_path (Path): pytest temporary directory.

    Returns:
        Path: Path of the written module.

    """
    target: Path = tmp_path / "m.py"
    _ = target.write_text(data=Constants.source, encoding="utf-8")
    return target


def _object(*, value: JsonValue) -> DictJsonValue:
    """Return ``value`` after checking it is a JSON object.

    Args:
        value (JsonValue): Parsed JSON node.

    Returns:
        DictJsonValue: The node as an object.

    Raises:
        TypeError: If ``value`` is not an object.

    """
    if not isinstance(value, dict):
        msg: str = f"expected a JSON object, got {value!r}"
        raise TypeError(msg)
    return value


def _array(*, value: JsonValue) -> list[JsonValue]:
    """Return ``value`` after checking it is a JSON array.

    Args:
        value (JsonValue): Parsed JSON node.

    Returns:
        list[JsonValue]: The node as an array.

    Raises:
        TypeError: If ``value`` is not an array.

    """
    if not isinstance(value, list):
        msg: str = f"expected a JSON array, got {value!r}"
        raise TypeError(msg)
    return value


def test_sarif_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that ``--format sarif`` emits a SARIF 2.1.0 document.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.
        monkeypatch (pytest.MonkeyPatch): Fixture capturing
            ``astart.__main__.stdout``.

    """
    out: str = _run(
        fmt="sarif",
        path=_write(tmp_path=tmp_path),
        monkeypatch=monkeypatch,
    )
    document: DictJsonValue = _object(value=loads(s=out))
    expect_equal(actual=document["version"], expected="2.1.0")
    runs: list[JsonValue] = _array(value=document["runs"])
    expect_equal(actual=len(runs), expected=1)
    run: DictJsonValue = _object(value=runs[0])
    results: list[JsonValue] = _array(value=run["results"])
    expect_equal(actual=len(results), expected=1)
    result: DictJsonValue = _object(value=results[0])
    expect_equal(actual=result["ruleId"], expected="typing.no-any")
    expect_equal(actual=result["level"], expected="error")
    message: DictJsonValue = _object(value=result["message"])
    expect_in(item="Any", container=str(object=message["text"]))
    locations: list[JsonValue] = _array(value=result["locations"])
    expect_equal(actual=len(locations), expected=1)
    location: DictJsonValue = _object(value=locations[0])
    physical: DictJsonValue = _object(
        value=location["physicalLocation"],
    )
    artifact: DictJsonValue = _object(
        value=physical["artifactLocation"],
    )
    expect_in(item="m.py", container=str(object=artifact["uri"]))
    region: DictJsonValue = _object(value=physical["region"])
    expect_equal(actual=region["startLine"], expected=4)


def test_junit_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that ``--format junit`` emits one testcase per finding.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.
        monkeypatch (pytest.MonkeyPatch): Fixture capturing
            ``astart.__main__.stdout``.

    """
    out: str = _run(
        fmt="junit",
        path=_write(tmp_path=tmp_path),
        monkeypatch=monkeypatch,
    )
    root: Element = _xml_root(text=out)
    cases: list[Element] = root.findall(path=".//testcase")
    expect_equal(actual=len(cases), expected=1)
    case: Element = cases[0]
    failures: list[Element] = case.findall(path="failure")
    expect_equal(actual=len(failures), expected=1)
    expect_in(item="TYP001", container=str(object=failures[0].attrib))


def test_github_format(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check that ``--format github`` emits workflow-command lines.

    Args:
        tmp_path (Path): Directory receiving the fixture source file.
        monkeypatch (pytest.MonkeyPatch): Fixture capturing
            ``astart.__main__.stdout``.

    """
    out: str = _run(
        fmt="github",
        path=_write(tmp_path=tmp_path),
        monkeypatch=monkeypatch,
    )
    lines: list[str] = [line for line in out.splitlines() if line]
    expect_true(condition=len(lines) >= 1)
    for line in lines:
        expect_true(condition=line.startswith("::"))
    expect_in(item="::error", container=out)
    expect_in(item="TYP001", container=out)
