"""Measure how far ``astart fix`` turns an untyped module into its typed twin.

Usage::

    PYTHONPATH=src:. python -m benchmarks.pair UNTYPED TYPED

Parameter and return annotations are scored exactly as in the recovery
benchmark; variable annotations (``x: int = 1``) are counted separately
because the fixer does not write them yet (``docs/TODO.md`` P-02).
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from dataclasses import dataclass
from json import dumps
from pathlib import Path
from sys import stdout
from typing import TYPE_CHECKING, final

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
from astart.rules.checker import Checker, build_checker
from astart.rules.recovery import (
    Context,
    annotation_map,
    module_context,
    normalize_annotation,
    relation,
    variable_map,
)
from astart.rules.vocabulary import FixSafety

if TYPE_CHECKING:
    from astart.rules.registry import Registries


@final
@dataclass(frozen=True, slots=True)
class Mode:
    """How the untyped module is converted.

    Attributes:
        floor: Least confidence a fix needs.
        negotiate: Whether negotiated hints supplement the hint index.
        engine: Conversion mode (the inference engine's own annotations).
        checker: Type checker that vetoes guarded fixes, or ``None``.

    """

    floor: float = 0.8
    negotiate: bool = True
    engine: bool = False
    checker: Checker | None = None


def compare(
    *,
    untyped: str,
    typed: str,
    mode: Mode,
) -> dict[str, dict[str, int]]:
    """Fix the untyped module and score it against the typed one.

    Args:
        untyped: Source without annotations.
        typed: Source with annotations.
        mode: How to convert.

    Returns:
        Counts of recovered, wrong and missed annotations.

    """
    registries: Registries = default_registries()
    fixed: str = fix_source(
        source=untyped,
        filename="untyped.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            min_confidence=mode.floor,
            annotate_variables=True,
            negotiate=mode.negotiate,
            engine=mode.engine,
            checker=mode.checker,
        ),
    ).source
    truth: dict[str, str] = annotation_map(source=typed)
    start: dict[str, str] = annotation_map(source=untyped)
    written: dict[str, str] = annotation_map(source=fixed)
    context: Context = module_context(source=typed)
    counts: Counter[str] = Counter()
    for key, text in written.items():
        if key in start or key not in truth:
            counts["not_in_typed" if key not in truth else "kept"] += 1
            continue
        mine: str = normalize_annotation(text=text)
        if mine == truth[key]:
            counts["correct"] += 1
            continue
        kind: str | None = relation(
            written=mine,
            truth=truth[key],
            context=context,
        )
        counts["wrong" if kind == "contradiction" else str(object=kind)] += 1
    variables: dict[str, str] = variable_map(source=typed)
    done: dict[str, str] = variable_map(source=fixed)
    scored: Counter[str] = Counter()
    for key, text in done.items():
        expected: str | None = variables.get(key)
        if expected is None:
            scored["not_in_typed"] += 1
        elif text == expected:
            scored["correct"] += 1
        else:
            kind = relation(written=text, truth=expected, context=context)
            scored[
                "wrong" if kind == "contradiction" else str(object=kind)
            ] += 1
    return {
        "parameters_and_returns": {
            "to_recover": sum(1 for key in truth if key not in start),
            **dict(counts),
        },
        "variables": {"to_recover": len(variables), **dict(scored)},
    }


def main() -> int:
    """Run the comparison.

    Returns:
        Zero.

    """
    parser: ArgumentParser = ArgumentParser(prog="python -m benchmarks.pair")
    parser.add_argument("untyped")
    parser.add_argument("typed")
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--engine", action="store_true")
    parser.add_argument("--checker", action="store_true")
    parser.add_argument(
        "--no-negotiate",
        dest="negotiate",
        action="store_false",
    )
    options: Namespace = parser.parse_args()
    result: dict[str, dict[str, int]] = compare(
        untyped=Path(options.untyped).read_text(encoding="utf-8"),
        typed=Path(options.typed).read_text(encoding="utf-8"),
        mode=Mode(
            floor=options.min_confidence,
            negotiate=options.negotiate,
            engine=options.engine,
            checker=(
                build_checker(root=Path.cwd()) if options.checker else None
            ),
        ),
    )
    _ = stdout.write(dumps(obj=result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
