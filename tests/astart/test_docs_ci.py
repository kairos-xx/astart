"""Check the documented pre-commit hooks stay in sync with ci.md."""

from pathlib import Path
from typing import Final

from tests.support.expectations import expect_in, expect_true
from tests.support.paths import Paths

ROOT: Final[Path] = Paths.root
HOOKS: Final[Path] = ROOT / ".pre-commit-hooks.yaml"
CI_DOC: Final[Path] = ROOT / "docs" / "engineering" / "ci.md"


def _hook_ids() -> list[str]:
    """Return the ``id:`` values declared in the hooks file.

    Returns:
        list[str]: Hook identifiers, in file order.

    """
    return [
        line.split(sep=":", maxsplit=1)[1].strip()
        for line in HOOKS.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(("id:", "- id:"))
    ]


def test_hooks_file_declares_both_hooks() -> None:
    """The hooks file must expose the fix-check and check hooks."""
    ids: list[str] = _hook_ids()
    expect_in(item="astart-fix", container=ids)
    expect_in(item="astart-check", container=ids)


def test_ci_doc_mentions_every_hook() -> None:
    """Check declared hook ids appear in ``docs/engineering/ci.md``."""
    doc: str = CI_DOC.read_text(encoding="utf-8")
    for hook_id in _hook_ids():
        expect_true(
            condition=hook_id in doc,
            message=f"ci.md does not mention hook {hook_id!r}",
        )


def test_ci_doc_has_config_examples_and_exit_table() -> None:
    """The CI doc must contain the config example and the exit-code table."""
    doc: str = CI_DOC.read_text(encoding="utf-8")
    expect_in(item="pre-commit-config.yaml", container=doc)
    expect_in(item="pip install astart", container=doc)
    expect_in(item="Exit codes", container=doc)
