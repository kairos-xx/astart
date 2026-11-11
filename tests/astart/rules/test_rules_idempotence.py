"""M1-11: ``fix_source`` is idempotent across the whole replay corpus.

Every corpus module is fixed twice under the guarded ceiling; the second
run must reproduce the first byte-for-byte and parse cleanly. That is
the observable fixed-point check -- ``FixResult`` does not expose per-round
counts, so convergence depth stays an internal property of the runner.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import FixResult, default_registries
from astart.rules.catalog import load_default_catalog
from astart.rules.runner import FixSettings, fix_source
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal, expect_true
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path

    from astart.rules.model import Catalog
    from astart.rules.registry import Registries


@final
class Constants:
    """Group module-level constants.

    Attributes:
        corpus (Final[Path]): Directory of corpus ``.py`` modules.
        settings (Final[FixSettings]): Guarded-ceiling options shared by every
            run.
        registries (Final[Registries]): Grouped module constant.

    """

    corpus: Final[Path] = Paths.tests / "corpus" / "base"
    settings: Final[FixSettings] = FixSettings(ceiling=FixSafety.guarded)

    registries: Final[Registries] = default_registries()


_CATALOG: Final[Catalog] = load_default_catalog(
    registries=Constants.registries,
)
_MODULES: Final[tuple[Path, ...]] = tuple(
    sorted(Constants.corpus.glob(pattern="*.py")),
)


@pytest.mark.parametrize("path", _MODULES, ids=lambda p: p.name)
def test_fix_is_idempotent(path: Path) -> None:
    """A second ``fix_source`` run changes nothing.

    Args:
        path (Path): Corpus module to fix twice.

    """
    source: str = path.read_text(encoding="utf-8")
    filename: str = path.name.removesuffix(".py") + ".py"
    first: FixResult = fix_source(
        source=source,
        filename=filename,
        catalog=_CATALOG,
        registries=Constants.registries,
        settings=Constants.settings,
    )
    second: FixResult = fix_source(
        source=first.source,
        filename=filename,
        catalog=_CATALOG,
        registries=Constants.registries,
        settings=Constants.settings,
    )
    expect_true(
        condition=second.parse_error is None,
        message=f"{filename}: second pass failed: {second.parse_error}",
    )
    expect_equal(actual=second.source, expected=first.source)
