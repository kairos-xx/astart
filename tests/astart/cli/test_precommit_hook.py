"""The pre-commit hook definition exists."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final

from tests.support.expectations import expect_in
from tests.support.paths import Paths

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        hook (Final[Path]): Path of the hook manifest.

    """

    hook: Final[Path] = Paths.root / ".pre-commit-hooks.yaml"


def test_hook_definition_names_the_check_mode() -> None:
    """Check the hook runs ``astart fix --check``."""
    text: str = Constants.hook.read_text(encoding="utf-8")
    expect_in(item="id: astart-fix", container=text)
    expect_in(item="astart fix --check", container=text)
