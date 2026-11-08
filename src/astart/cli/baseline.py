"""Persist and apply finding baselines.

A baseline is a JSON document of finding fingerprints plus file-level
errors.  Findings whose fingerprint is in the baseline are suppressed
when a run reapplies the baseline, so only new findings surface.
"""

from __future__ import annotations

from dataclasses import replace
from json import dumps, loads
from typing import TYPE_CHECKING, Final, cast, final

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from astart.cli.render import FileReport


@final
class Constants:
    """Group module-level constants.

    Attributes:
        version: Baseline document version emitted.
        version_key: JSON key for the version.
        fingerprints_key: JSON key for the fingerprint list.
        errors_key: JSON key for the file-error list.

    """

    version: Final[int] = 1
    version_key: Final[str] = "version"
    fingerprints_key: Final[str] = "fingerprints"
    errors_key: Final[str] = "errors"


@final
class BaselineError(ValueError):
    """Raised when a baseline file is malformed."""


def save_baseline(*, results: Sequence[FileReport], path: Path) -> None:
    """Write every fingerprint and file error to a baseline file.

    Args:
        results: Reports to capture.
        path: Destination JSON file.

    """
    fingerprints: list[str] = sorted(
        finding.fingerprint
        for report in results
        for finding in report.findings
    )
    errors: list[str] = sorted(
        report.path for report in results if report.error is not None
    )
    path.write_text(
        data=dumps(
            obj={
                Constants.version_key: Constants.version,
                Constants.fingerprints_key: fingerprints,
                Constants.errors_key: errors,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_baseline(*, path: Path) -> frozenset[str]:
    """Read a baseline file into a fingerprint set.

    Args:
        path: The baseline JSON file.

    Returns:
        The fingerprints it captured.

    Raises:
        BaselineError: If the document is malformed.

    """
    document: object | dict[str, str | int] = loads(
        s=path.read_text(encoding="utf-8"),
    )
    if not isinstance(document, dict):
        msg: str = "baseline must be a JSON object"
        raise BaselineError(msg)
    version: str | int | None = (
        document := cast(typ="dict[str, str | int]", val=document)
    ).get(Constants.version_key)
    if version != Constants.version:
        msg = f"unsupported baseline version {version!r}"
        raise BaselineError(msg)
    values: object = document.get(Constants.fingerprints_key, [])
    if not isinstance(values, list) or not all(
        isinstance(item, str) for item in values
    ):
        msg = f"{Constants.fingerprints_key} must be a list of strings"
        raise BaselineError(msg)
    return frozenset(values)


def apply_baseline(
    *,
    results: Sequence[FileReport],
    fingerprints: frozenset[str],
) -> tuple[FileReport, ...]:
    """Drop findings whose fingerprint is in the baseline.

    Args:
        results: Reports to filter.
        fingerprints: Baselined fingerprints.

    Returns:
        Reports with baselined findings removed.

    """
    return tuple(
        replace(
            report,
            findings=tuple(
                finding
                for finding in report.findings
                if finding.fingerprint not in fingerprints
            ),
        )
        for report in results
    )
