"""Canonical benchmark input and output locations."""

from __future__ import annotations

from pathlib import Path
from typing import Final, final


@final
class Paths:
    """Stable repository-relative locations, independent of working directory.

    Attributes:
        root (Final[Path]): Repository root.
        package (Final[Path]): Benchmark implementation modules.
        artifacts (Final[Path]): Benchmark artifact root.
        results (Final[Path]): Generated reports and sensor output.
        resources (Final[Path]): Input manifests and accepted baselines.

    """

    root: Final[Path] = Path(__file__).resolve().parents[2]
    package: Final[Path] = root / "scripts" / "benchmark"
    artifacts: Final[Path] = package / "artifacts"
    results: Final[Path] = artifacts / "results"
    resources: Final[Path] = artifacts / "resources"


def write_artifact(
    *,
    name: str,
    text: str,
    output: Path | None = None,
) -> Path:
    """Write generated evidence to the default or explicit CLI destination.

    Args:
        name (str): Default artifact filename.
        text (str): Serialized evidence.
        output (Path | None): Explicit user-selected output, when supplied.

    Returns:
        Path: Written artifact path.

    """
    destination: Path = Paths.results / name if output is None else output
    destination.parent.mkdir(parents=True, exist_ok=True)
    _: int = destination.write_text(data=text, encoding="utf-8")
    return destination
