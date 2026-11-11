"""Print annotation-recovery precision and recall for a set of modules.

Usage: ``python scripts/compare/recovery_report.py FILE...``

"""

from __future__ import annotations

from pathlib import Path
from sys import argv, stdout
from typing import Final, final

from astart.rules.recovery import RecoveryScore, recover


@final
class Constants:
    """Group module-level constants.

    Attributes:
        crashes (Final[tuple[type[Exception], ...]]): Exception types reported
            as a crash of one
            module instead of ending the whole run.

    """

    crashes: Final[tuple[type[Exception], ...]] = (
        AttributeError,
        IndexError,
        KeyError,
        RecursionError,
        TypeError,
        ValueError,
    )


def main() -> int:
    """Score every file named on the command line and print a table.

    Returns:
        int: Zero.

    """
    total_truth: int = 0
    total_correct: int = 0
    total_wrong: int = 0
    crashed: list[str] = []
    _ = stdout.write(
        (
            f"{'file':34} {'truth':>6} {'ok':>5} {'wrong':>5} {'synth':>5} "
            f"{'sec':>6}\n"
        ),
    )
    for name in argv[1:]:
        path: Path = Path(name)
        try:
            score: RecoveryScore = recover(
                source=path.read_text(encoding="utf-8"),
                filename=path.name,
            )
        except Constants.crashes as error:
            crashed.append(path.name)
            _ = stdout.write(
                f"{path.name:34} CRASH {type(error).__name__}: {error}\n",
            )
            continue
        total_truth += score.truth
        total_correct += score.correct
        total_wrong += len(score.wrong)
        _ = stdout.write(
            f"{path.name:34} {score.truth:6} {score.correct:5} "
            f"{len(score.wrong):5} {len(score.synthesized):5} "
            f"{score.seconds:6.1f}\n",
        )
        for line in score.wrong:
            _ = stdout.write(f"    WRONG {line}\n")
    written: int = total_correct + total_wrong
    _ = stdout.write(
        f"precision {total_correct}/{written} "
        f"recall {total_correct}/{total_truth} "
        f"crashed {len(crashed)}\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
