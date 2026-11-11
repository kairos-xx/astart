"""``fix_source`` output does not depend on ``PYTHONHASHSEED``."""

from __future__ import annotations

from itertools import islice
from os import environ
from subprocess import run
from sys import executable
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    FormatTarget,
    default_registries,
    fix_and_format,
    fix_source,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path
    from subprocess import CompletedProcess

    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        seeds (Final[tuple[str, str, str]]): Hash seeds the subprocess runs
            with.
        max_lines (Final[int]): Corpus files must be shorter than this many
            lines.
        sample_count (Final[int]): Number of corpus files exercised by the
            determinism run.
        payload (Final[str]): ``python -c`` script fixing one file.

    """

    root: Final[Path] = Paths.root
    seeds: Final[tuple[str, str, str]] = ("0", "1", "2")
    max_lines: Final[int] = 300
    sample_count: Final[int] = 10
    payload: Final[str] = """\
import sys
from pathlib import Path
from astart.rules import FixSettings, default_registries
from astart.rules import fix_source, load_default_catalog
from astart.rules.vocabulary import FixSafety
registries = default_registries()
result = fix_source(
    source=Path(sys.argv[1]).read_text(encoding="utf-8"),
    filename=sys.argv[1],
    catalog=load_default_catalog(registries=registries),
    registries=registries,
    settings=FixSettings(
        ceiling=FixSafety.guarded,
        negotiate=True,
        annotate_variables=True,
    ),
)
sys.stdout.write(result.source)
"""


def _corpus_files() -> list[Path]:
    """List the first ten corpus files under 300 lines, sorted by name.

    Returns:
        list[Path]: Corpus paths.

    """
    return list(
        islice(
            (
                path
                for path in sorted(
                    (Constants.root / "tests" / "corpus" / "base").glob(
                        pattern="*.py",
                    ),
                )
                if len(path.read_text(encoding="utf-8").splitlines())
                < Constants.max_lines
            ),
            Constants.sample_count,
        ),
    )


def _fix_plain(*, text: str, name: str) -> str:
    """Fix ``text`` once without running the external formatter.

    Args:
        text (str): Source text to fix.
        name (str): File name for parsing and spans.

    Returns:
        str: Fixed source text.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=text,
        filename=name,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            negotiate=True,
            annotate_variables=True,
        ),
    ).source


def _fix_formatted(*, text: str, name: str) -> str:
    """Fix and format ``text`` once.

    Args:
        text (str): Source text to fix.
        name (str): File name for parsing and formatting.

    Returns:
        str: Fixed and formatted source text.

    """
    registries: Registries = default_registries()
    _fixed, formatted = fix_and_format(
        source=text,
        target=FormatTarget(filename=name, cwd=Constants.root),
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            negotiate=True,
            annotate_variables=True,
        ),
    )
    return formatted.source


@pytest.mark.slow
@pytest.mark.parametrize("path", _corpus_files(), ids=lambda item: item.name)
def test_fix_source_is_seed_deterministic(*, path: Path) -> None:
    """Check three hash seeds produce byte-identical fixed sources.

    Args:
        path (Path): Corpus file to fix.

    """
    outputs: dict[str, str] = {}
    for seed in Constants.seeds:
        env: dict[str, str] = dict(environ)
        env["PYTHONHASHSEED"] = seed
        env["PYTHONPATH"] = str(object=Constants.root / "src")
        proc: CompletedProcess[str] = run(
            args=[executable, "-c", Constants.payload, str(object=path)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        expect_equal(actual=proc.returncode, expected=0, message=proc.stderr)
        outputs[seed] = proc.stdout
    expect_equal(actual=outputs["0"], expected=outputs["1"])
    expect_equal(actual=outputs["1"], expected=outputs["2"])


@pytest.mark.slow
@pytest.mark.parametrize("path", _corpus_files(), ids=lambda item: item.name)
def test_fix_source_is_idempotent_with_and_without_formatter(
    *,
    path: Path,
) -> None:
    """Check ``fix(fix(x)) == fix(x)`` with and without ``run_formatter``.

    Args:
        path (Path): Corpus file to fix twice.

    """
    raw: str = path.read_text(encoding="utf-8")
    first_plain: str = _fix_plain(text=raw, name=path.name)
    second_plain: str = _fix_plain(text=first_plain, name=path.name)
    expect_equal(actual=second_plain, expected=first_plain)
    first_fmt: str = _fix_formatted(text=raw, name=path.name)
    second_fmt: str = _fix_formatted(text=first_fmt, name=path.name)
    expect_equal(actual=second_fmt, expected=first_fmt)
