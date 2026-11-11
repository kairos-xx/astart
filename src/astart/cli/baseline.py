"""Persist and apply finding baselines.

A baseline is a JSON document of finding fingerprints plus file-level
errors. Findings whose fingerprint is in the baseline are suppressed
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
        version (Final[int]): Baseline document version emitted.
        version_key (Final[str]): JSON key for the version.
        fingerprints_key (Final[str]): JSON key for the fingerprint list.
        errors_key (Final[str]): JSON key for the file-error list.

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
        results (Sequence[FileReport]): Reports to capture.
        path (Path): Destination JSON file.

    """
    fingerprints: list[str] = sorted(
        _key(report=report, fingerprint=finding.fingerprint)
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
        path (Path): The baseline JSON file.

    Returns:
        frozenset[str]: The fingerprints it captured.

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
        results (Sequence[FileReport]): Reports to filter.
        fingerprints (frozenset[str]): Baselined fingerprints.

    Returns:
        tuple[FileReport, ...]: Reports with baselined findings removed.

    """
    return tuple(
        replace(
            report,
            findings=tuple(
                finding
                for finding in report.findings
                if _key(report=report, fingerprint=finding.fingerprint)
                not in fingerprints
            ),
        )
        for report in results
    )


def _key(*, report: FileReport, fingerprint: str) -> str:
    """Build the baseline key for one finding.

    Args:
        report (FileReport): Report the finding belongs to.
        fingerprint (str): The finding's stable fingerprint.

    Returns:
        str: ``path#fingerprint`` so identical findings in different files
            never share a baseline entry.

    """
    return f"{report.path}#{fingerprint}"
