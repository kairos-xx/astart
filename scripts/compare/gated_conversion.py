"""W-02: why the checker gate keeps only a few resolver-pair annotations.

Runs ``fix_source`` on the full resolver untyped file with
``engine=True`` and an installed pyright checker, prints timing, applied and
skipped counts and the skip-code histogram. When fixes are skipped with
``checker_rejected``, one skipped fix is then applied on its own — the
checker is asked what it actually reports for the single change — which
separates "the gate is right, the annotation really adds an error" from
"the degrade logic picks a wrong ``before``".

Usage::

    PYTHONPATH=src:. python scripts/compare/gated_conversion.py [--fix N]

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from pathlib import Path
from sys import stdout
from time import perf_counter
from typing import TYPE_CHECKING, Final, final

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.checker import (
    Checker,
    Diagnostic,
    MypyChecker,
    PyrightChecker,
    build_checker,
)
from astart.rules.engine import CheckResult, check
from astart.rules.hints import HintCache
from astart.rules.reasons import SkipCode
from astart.rules.runner import (
    Job,
    Round,
    attempt,
    eligible,
    options,
)
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from collections.abc import Callable

    from astart.rules.model import Catalog, Finding, Fix
    from astart.rules.registry import Registries
    from astart.rules.runner import FixResult


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root (the checker's project context).
        untyped (Final[Path]): Canonical untyped fixture.
        filename (Final[str]): Name used for parsing and spans.
        sample_fixes (Final[int]): How many isolated single-fix probes to
            print.

    """

    root: Final[Path] = Path(__file__).resolve().parents[2]
    untyped: Final[Path] = (
        Path(__file__).resolve().parents[2] / "fixtures" / "untyped.py"
    )
    filename: Final[str] = "untyped.py"
    sample_fixes: Final[int] = 3


@final
class _PermissiveChecker:
    """A checker that never vetoes, used to isolate one fix's output."""

    @staticmethod
    def regresses(*, filename: str, before: str, after: str) -> bool:
        """Accept every change.

        Args:
            filename (str): Path of the file the texts belong to.
            before (str): Original source text.
            after (str): Changed source text.

        Returns:
            bool: ``False`` always.

        """
        _: tuple[str, str, str] = (filename, before, after)
        return False


def _settings(*, checker: Checker | None) -> FixSettings:
    """Build the fix settings of the gated conversion run.

    Args:
        checker (Checker | None): External checker vetoing guarded fixes, or
            ``None``.

    Returns:
        FixSettings:
            Engine-mode settings matching ``--engine --min-confidence 0.5``.

    """
    return FixSettings(
        ceiling=FixSafety.guarded,
        min_confidence=0.5,
        annotate_variables=True,
        engine=True,
        checker=checker,
    )


def _job(*, checker: Checker | None) -> Job:
    """Build the runner job matching one gated ``fix_source`` call.

    Args:
        checker (Checker | None): External checker, or ``None``.

    Returns:
        Job: The job.

    """
    registries: Registries = default_registries()
    return Job(
        filename=Constants.filename,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=_settings(checker=checker),
        cache=HintCache(),
    )


def _find_pair(
    *,
    job: Job,
    source: str,
    fix_key: str,
    subject_path: str,
) -> tuple[Finding, Fix] | None:
    """Locate one fix offer in the original findings.

    Args:
        job (Job): The runner job.
        source (str): The original untyped source.
        fix_key (str): Fix key of the skipped fix.
        subject_path (str): Subject the fix would have edited.

    Returns:
        tuple[Finding, Fix] | None:
            The ``(finding, fix)`` pair, or ``None`` when it no longer offers.

    """
    catalog: Catalog = job.catalog
    found: CheckResult = check(
        source=source,
        filename=job.filename,
        catalog=catalog,
        registries=job.registries,
        options=options(job=job),
    )
    pairs: list[tuple[Finding, Fix]] = eligible(
        findings=found.findings,
        catalog=catalog,
        ceiling=job.settings.ceiling,
        minimum=job.settings.min_confidence,
        excluded=job.settings.excluded_prefixes,
    )
    for finding, fix in pairs:
        if fix.key == fix_key and finding.subject_path == subject_path:
            return finding, fix
    return None


def _probe_single_fix(
    *,
    checker: Checker,
    job: Job,
    source: str,
    fix_key: str,
    subject_path: str,
) -> None:
    """Apply one skipped fix alone and print the checker's verdict.

    Args:
        checker (Checker): The real checker.
        job (Job): The runner job.
        source (str): The original untyped source.
        fix_key (str): Fix key of the skipped fix.
        subject_path (str): Subject the fix would have edited.

    """
    if not isinstance(checker, (PyrightChecker, MypyChecker)):
        _ = stdout.write("""single fix probe needs a command checker
""")
        return
    pair: tuple[Finding, Fix] | None = _find_pair(
        job=job,
        source=source,
        fix_key=fix_key,
        subject_path=subject_path,
    )
    if pair is None:
        _ = stdout.write(
            f"single fix {fix_key} on {subject_path}: not offered\n",
        )
        return
    permissive: Job = Job(
        filename=job.filename,
        catalog=job.catalog,
        registries=job.registries,
        settings=_settings(checker=_PermissiveChecker()),
        cache=job.cache,
    )
    _attempt: Round | SkipCode = attempt(
        source=source,
        pairs=[pair],
        job=permissive,
    )
    if not isinstance(_attempt, Round):
        _ = stdout.write(
            f"single fix {fix_key} on {subject_path}: "
            f"could not apply ({_attempt.value})\n",
        )
        return
    delta: int | None = checker.new_errors(
        filename=job.filename,
        before=source,
        after=_attempt.source,
    )
    _ = stdout.write(
        f"single fix {fix_key} on {subject_path}: "
        f"new_errors={delta} applied={len(_attempt.applied)}\n",
    )
    if delta:
        diagnostics: Callable[..., Counter[Diagnostic] | None] | None = (
            getattr(
                checker,
                "_diagnostics",
                None,
            )
        )
        if callable(diagnostics):
            before_errors: Counter[Diagnostic] | None = diagnostics(
                filename=job.filename,
                text=source,
            )
            after_errors: Counter[Diagnostic] | None = diagnostics(
                filename=job.filename,
                text=_attempt.source,
            )
            if isinstance(before_errors, Counter) and isinstance(
                after_errors,
                Counter,
            ):
                for diagnostic, count in sorted(
                    (after_errors - before_errors).items(),
                    key=lambda item: item[0].rule,
                ):
                    _ = stdout.write(
                        (
                            f"  +{count} {diagnostic.rule}: "
                            f"{diagnostic.message}\n"
                        ),
                    )


def main() -> int:
    """Run the gated conversion and print the skip-code breakdown.

    Returns:
        int: Zero.

    """
    parser: ArgumentParser = ArgumentParser(prog="gated_conversion")
    parser.add_argument(
        "--untyped",
        type=Path,
        default=Constants.untyped,
    )
    parser.add_argument(
        "--fix",
        type=int,
        default=Constants.sample_fixes,
        help="single-fix probes to run",
    )
    args: Namespace = parser.parse_args()
    source: str = args.untyped.read_text(encoding="utf-8")
    checker: Checker | None = build_checker(root=Path.cwd())
    _ = stdout.write(f"checker: {type(checker).__name__}\n")
    registries: Registries = default_registries()
    started: float = perf_counter()
    result: FixResult = fix_source(
        source=source,
        filename=Constants.filename,
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=_settings(checker=checker),
    )
    seconds: float = perf_counter() - started
    _ = stdout.write(
        f"seconds={seconds:.1f} rounds={result.rounds} "
        f"applied={len(result.applied)} skipped={len(result.skipped)}\n",
    )
    codes: Counter[str] = Counter(skip.code.value for skip in result.skipped)
    for code, count in codes.most_common():
        _ = stdout.write(f"  {code}: {count}\n")
    if checker is None or "checker_rejected" not in codes:
        return 0
    job: Job = _job(checker=checker)
    probed: int = 0
    for skip in result.skipped:
        if skip.code is not SkipCode.checker_rejected:
            continue
        if probed >= args.fix:
            break
        _probe_single_fix(
            checker=checker,
            job=job,
            source=source,
            fix_key=skip.fix_key,
            subject_path=skip.subject_path,
        )
        probed += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
