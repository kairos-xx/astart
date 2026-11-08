"""``fix_source`` output does not depend on ``PYTHONHASHSEED``."""

from __future__ import annotations

from os import environ
from pathlib import Path
from subprocess import run
from sys import executable
from typing import TYPE_CHECKING, Final, final

import pytest

from tests.expectations import expect_equal

if TYPE_CHECKING:
    from subprocess import CompletedProcess


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root: Repository root directory.
        seeds: Hash seeds the subprocess runs with.
        max_lines: Corpus files must be shorter than this many lines.
        payload: ``python -c`` script fixing one file.

    """

    root: Final[Path] = Path(__file__).parent.parent
    seeds: Final[tuple[str, str]] = ("1", "2")
    max_lines: Final[int] = 300
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
    settings=FixSettings(ceiling=FixSafety.guarded),
)
sys.stdout.write(result.source)
"""


def _corpus_files() -> list[Path]:
    """List the first five corpus files under 300 lines, sorted by name.

    Returns:
        Corpus paths.

    """
    files: list[Path] = [
        path
        for path in sorted(
            (Constants.root / "tests" / "corpus").glob(pattern="*.py.txt"),
        )
        if len(path.read_text(encoding="utf-8").splitlines())
        < Constants.max_lines
    ]
    return files[:5]


@pytest.mark.slow
@pytest.mark.parametrize("path", _corpus_files(), ids=lambda item: item.name)
def test_fix_source_is_seed_deterministic(*, path: Path) -> None:
    """Check two hash seeds produce byte-identical fixed sources.

    Args:
        path: Corpus file to fix.

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
    expect_equal(actual=outputs["1"], expected=outputs["2"])
