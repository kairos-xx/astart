"""Verify the external type-checker gate."""

from __future__ import annotations

from dataclasses import dataclass
from shutil import which
from typing import TYPE_CHECKING, Final, final

import pytest
from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.checker import PyrightChecker, detect_checker
from astart.rules.reasons import SkipCode
from astart.rules.vocabulary import FixSafety

from tests.expectations import (
    expect_equal,
    expect_in,
    expect_not_in,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.mark.structures import MarkDecorator
    from astart.rules import FixResult
    from astart.rules.registry import Registries

needs_pyright: MarkDecorator = pytest.mark.skipif(
    which(cmd="basedpyright") is None and which(cmd="pyright") is None,
    reason="no pyright on PATH",
)

SOURCE: Final[str] = "LIMIT = 3\n\n\ndef f(x=1):\n    print(x)\n\n\nf(2)\n"


@final
@dataclass
class _Verdict:
    """A checker that answers from a script and counts its calls.

    Attributes:
        reject: Whether every verified change is rejected.
        calls: How many verifications were requested.

    """

    reject: bool
    calls: int = 0

    def regresses(self, *, filename: str, before: str, after: str) -> bool:
        """Answer the scripted verdict.

        Args:
            filename: Unused file name.
            before: Unused original text.
            after: Unused changed text.

        Returns:
            The scripted verdict.

        """
        self.calls += 1
        return self.reject and bool(filename + before + after)


def _fix(
    *,
    checker: _Verdict | None,
    ceiling: FixSafety = FixSafety.guarded,
) -> FixResult:
    """Fix a small module under a stub checker.

    Args:
        checker: Checker stub deciding guarded fixes.
        ceiling: Highest fix safety to apply.

    Returns:
        The fix result.

    """
    registries: Registries = default_registries()
    return fix_source(
        source=SOURCE,
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=ceiling, checker=checker),
    )


def test_rejected_guarded_fixes_are_skipped_but_proven_ones_stay() -> None:
    """Check that rejected guarded fixes are skipped but proven ones stay."""
    verdict: _Verdict = _Verdict(reject=True)
    result: FixResult = _fix(checker=verdict)
    expect_in(item="LIMIT: Final[int] = 3", container=result.source)
    expect_in(item="-> None", container=result.source)
    expect_not_in(item="x: int", container=result.source)
    expect_not_in(item="f(x=2)", container=result.source)
    codes: set[SkipCode] = {item.code for item in result.skipped}
    expect_in(item=SkipCode.checker_rejected, container=codes)


def test_accepting_checker_keeps_every_fix() -> None:
    """Check that accepting checker keeps every fix."""
    verdict: _Verdict = _Verdict(reject=False)
    result: FixResult = _fix(checker=verdict)
    expect_in(item="x: int = 1", container=result.source)
    expect_in(item="f(x=2)", container=result.source)
    expect_true(condition=verdict.calls >= 1)


def test_proven_ceiling_never_consults_the_checker() -> None:
    """Check that proven ceiling never consults the checker."""
    verdict: _Verdict = _Verdict(reject=True)
    _ = _fix(checker=verdict, ceiling=FixSafety.proven)
    expect_equal(actual=verdict.calls, expected=0)


@needs_pyright
def test_pyright_flags_a_wrong_annotation_only(*, tmp_path: Path) -> None:
    """Check that pyright flags a wrong annotation only.

    Args:
        tmp_path: Directory holding the sample file.

    """
    command: tuple[str, ...] = expect_not_none(value=detect_checker())
    checker: PyrightChecker = PyrightChecker(command=command, root=tmp_path)
    name: str = str(object=tmp_path / "m.py")
    before: str = "def f(x):\n    return x\n"
    expect_true(
        condition=checker.regresses(
            filename=name,
            before=before,
            after="def f(x: int) -> str:\n    return x\n",
        ),
    )
    expect_equal(
        actual=checker.regresses(
            filename=name,
            before=before,
            after="def f(x: int) -> int:\n    return x\n",
        ),
        expected=False,
    )


@needs_pyright
def test_errors_naming_the_module_are_not_counted_as_new(
    *,
    tmp_path: Path,
) -> None:
    """Check that an error that quotes the module name compares equal.

    The scratch file's name differs per text, so an unchanged error that
    mentions it must not look like one the change introduced.

    Args:
        tmp_path: Directory holding the sample file.

    """
    command: tuple[str, ...] = expect_not_none(value=detect_checker())
    checker: PyrightChecker = PyrightChecker(command=command, root=tmp_path)
    name: str = str(object=tmp_path / "m.py")
    before: str = (
        "from decimal import Decimal\n"
        "class Decimal:\n"
        "    pass\n"
        "def f(x):\n"
        "    return x\n"
    )
    expect_equal(
        actual=checker.new_errors(
            filename=name,
            before=before,
            after=before.replace("def f(x):", "def f(x: int):"),
        ),
        expected=0,
    )


@needs_pyright
def test_partially_unknown_reports_are_not_regressions(
    *,
    tmp_path: Path,
) -> None:
    """Check that strict "unknown type" reports never count as new errors.

    Completing a signature rewrites the text of those reports; that is
    progress, not a mistake the change introduced.

    Args:
        tmp_path: Directory holding the sample file.

    """
    command: tuple[str, ...] = expect_not_none(value=detect_checker())
    checker: PyrightChecker = PyrightChecker(command=command, root=tmp_path)
    name: str = str(object=tmp_path / "m.py")
    before: str = "def f(x):\n    return x\n\nf(1)\n"
    after: str = "def f(x) -> int:\n    return x\n\nf(1)\n"
    expect_equal(
        actual=checker.new_errors(filename=name, before=before, after=after),
        expected=0,
    )


@needs_pyright
def test_scratch_files_live_in_a_temp_dir_yet_siblings_resolve(
    *,
    tmp_path: Path,
) -> None:
    """Check that nothing is written beside the source and imports still work.

    Args:
        tmp_path: Directory holding the sample modules.

    """
    _ = (tmp_path / "helper.py").write_text(
        data="def make() -> str:\n    return 'x'\n",
        encoding="utf-8",
    )
    command: tuple[str, ...] = expect_not_none(value=detect_checker())
    checker: PyrightChecker = PyrightChecker(command=command, root=tmp_path)
    name: str = str(object=tmp_path / "m.py")
    expect_equal(
        actual=checker.regresses(
            filename=name,
            before="x = 1\n",
            after="from helper import make\nx: str = make()\n",
        ),
        expected=False,
    )
    expect_true(
        condition=checker.regresses(
            filename=name,
            before="x = 1\n",
            after="from helper import make\nx: int = make()\n",
        ),
    )
    expect_equal(
        actual=sorted(
            path.name
            for path in tmp_path.iterdir()
            if path.name != "README.md"
        ),
        expected=["helper.py"],
    )
