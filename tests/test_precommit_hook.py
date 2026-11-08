"""The pre-commit hook definition exists."""

from __future__ import annotations

from pathlib import Path
from typing import Final, final

from tests.expectations import expect_in


@final
class Constants:
    """Group module-level constants.

    Attributes:
        hook: Path of the hook manifest.

    """

    hook: Final[Path] = Path(__file__).parent.parent / ".pre-commit-hooks.yaml"


def test_hook_definition_names_the_check_mode() -> None:
    """Check the hook runs ``astart fix --check``."""
    text: str = Constants.hook.read_text(encoding="utf-8")
    expect_in(item="id: astart-fix", container=text)
    expect_in(item="astart fix --check", container=text)
