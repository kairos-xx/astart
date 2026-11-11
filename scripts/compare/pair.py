"""Measure how far ``astart fix`` turns an untyped module into its typed twin.

Usage::

    PYTHONPATH=src:. python -m scripts.compare.pair UNTYPED TYPED

Parameter and return annotations are scored exactly as in the recovery
benchmark; variable annotations (``x: int = 1``) are counted separately
because the fixer does not write them yet (``docs/planning/TODO.md`` P-02).

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from dataclasses import dataclass
from importlib import import_module
from json import dumps, loads
from pathlib import Path
from sys import stdout
from typing import TYPE_CHECKING, Final, final

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
    merge_contexts,
    module_context,
    normalize_annotation,
    relation,
    variable_map,
)
from astart.rules.vocabulary import FixSafety

type DictStr = dict[str, str]
type DictDictInt = dict[str, dict[str, int]]

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Mapping
    from types import ModuleType

    from astart.rules.registry import Registries

ACCEPTED_DEVIATIONS_PATH: Final[Path] = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "artifacts"
    / "accepted_deviations.json"
)


@final
@dataclass(frozen=True, slots=True)
class Mode:
    """How the untyped module is converted.

    Attributes:
        floor (float): Least confidence a fix needs.
        negotiate (bool): Whether negotiated hints supplement the hint index.
        engine (bool): Conversion mode (the inference engine's own
            annotations).
        checker (Checker | None): Type checker that vetoes guarded fixes, or
            ``None``.

    """

    floor: float = 0.8
    negotiate: bool = True
    engine: bool = False
    checker: Checker | None = None


def load_accepted_deviations(*, path: Path) -> list[DictStr]:
    """Load reviewer-approved annotation deviations.

    Args:
        path (Path): JSON file with ``pair`` , ``node`` , ``wrote``
            , ``author`` and ``reason`` entries.

    Returns:
        list[DictStr]: Entries with normalized ``wrote`` /``author``
            annotations.

    Raises:
        ValueError: When an entry lacks a non-empty ``reason``.

    """
    entries: list[DictStr] = []
    for entry in loads(s=path.read_text(encoding="utf-8")):
        reason: str = str(object=entry.get("reason", ""))
        if not reason.strip():
            msg: str = f"accepted deviation {entry!r} has an empty reason"
            raise ValueError(
                msg,
            )
        entries.append(
            {
                "pair": str(object=entry.get("pair", "")),
                "node": str(object=entry["node"]),
                "wrote": normalize_annotation(text=str(object=entry["wrote"])),
                "author": normalize_annotation(
                    text=str(object=entry["author"]),
                ),
                "reason": reason,
            },
        )
    return entries


def _accepted(
    *,
    node: str,
    wrote: str,
    author: str,
    deviations: Collection[Mapping[str, str]],
) -> bool:
    """Tell whether a written annotation is a reviewer-approved deviation.

    Args:
        node (str): Annotation key (for example ``Class.method.param``).
        wrote (str): What the fixer wrote, normalized.
        author (str): The original annotation, normalized.
        deviations (Collection[Mapping[str, str]]): Accepted-deviation entries.

    Returns:
        bool: ``True`` when a deviation entry matches all three fields.

    """
    return any(
        entry["node"] == node
        and entry["wrote"] == wrote
        and entry["author"] == author
        for entry in deviations
    )


def compare(
    *,
    untyped: str,
    typed: str,
    mode: Mode,
    accepted: Collection[Mapping[str, str]] = (),
) -> DictDictInt:
    """Fix the untyped module and score it against the typed one.

    Args:
        untyped (str): Source without annotations.
        typed (str): Source with annotations.
        mode (Mode): How to convert.
        accepted (Collection[Mapping[str, str]]): Reviewer-approved deviations;
            a matching written
            annotation counts as ``accepted`` instead of its relation.

    Returns:
        DictDictInt:
            Counts of recovered, wrong, accepted and missed annotations.

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
    truth: DictStr = annotation_map(source=typed)
    start: DictStr = annotation_map(source=untyped)
    written: DictStr = annotation_map(source=fixed)
    context: Context = merge_contexts(
        primary=module_context(source=typed),
        extra=module_context(source=fixed),
    )
    counts: Counter[str] = Counter()
    for key, text in written.items():
        if key in start or key not in truth:
            counts["not_in_typed" if key not in truth else "kept"] += 1
            continue
        mine: str = normalize_annotation(text=text)
        author: str = normalize_annotation(text=truth[key])
        if mine == author:
            counts["correct"] += 1
            continue
        if _accepted(
            node=key,
            wrote=mine,
            author=author,
            deviations=accepted,
        ):
            counts["accepted"] += 1
            continue
        kind: str | None = relation(
            written=mine,
            truth=author,
            context=context,
        )
        counts[
            "correct"
            if kind is None
            else "wrong"
            if kind == "contradiction"
            else str(object=kind)
        ] += 1
    variables: DictStr = variable_map(source=typed)
    done: DictStr = variable_map(source=fixed)
    scored: Counter[str] = Counter()
    for key, text in done.items():
        expected: str | None = variables.get(key)
        if expected is None:
            scored["not_in_typed"] += 1
        elif text == expected:
            scored["correct"] += 1
        elif _accepted(
            node=key,
            wrote=normalize_annotation(text=text),
            author=normalize_annotation(text=expected),
            deviations=accepted,
        ):
            scored["accepted"] += 1
        else:
            kind = relation(written=text, truth=expected, context=context)
            scored[
                "correct"
                if kind is None
                else "wrong"
                if kind == "contradiction"
                else str(object=kind)
            ] += 1
    return {
        "parameters_and_returns": {
            "to_recover": sum(1 for key in truth if key not in start),
            **dict(counts),
        },
        "variables": {"to_recover": len(variables), **dict(scored)},
    }


def gate(*, baseline: Path, mode: Mode) -> int:
    """Run the round-trip gate: ``fix(untype(typed))`` versus ``typed``.

    The curated ``fixtures/typed.py`` reference is stripped of
    annotations, fixed again, and scored with :func:`compare`. Numbers are
    checked against
    ``scripts/benchmark/artifacts/resources/baseline_pair.json``;
    a missing or empty baseline is written first so later runs enforce it.

    Args:
        baseline (Path): JSON file holding per-pair score baselines.
        mode (Mode): Conversion mode for the round trip.

    Returns:
        int: Zero on ``PASS`` , one on ``FAIL`` or when
            ``untype`` is unavailable (``docs/planning/TODO.md``
            P-08 supplies ``astart.rules.untype``).

    """
    try:
        untype_module: ModuleType = import_module(name="astart.rules.untype")
    except ImportError:
        _ = stdout.write(
            """\
SKIP: astart.rules.untype is unavailable (P-08 not landed)
""",
        )
        return 1
    untype_source_name: str = "untype_source"
    untype_source: Callable[..., str] = getattr(
        untype_module,
        untype_source_name,
    )
    pairs: DictStr = {}
    dev_typed: Path = (
        Path(__file__).resolve().parents[2] / "fixtures" / "typed.py"
    )
    if dev_typed.is_file():
        pairs["dev"] = dev_typed.read_text(encoding="utf-8")
    deviations: list[DictStr] = (
        load_accepted_deviations(path=ACCEPTED_DEVIATIONS_PATH)
        if ACCEPTED_DEVIATIONS_PATH.is_file()
        else []
    )
    results: dict[str, DictDictInt] = {
        name: compare(
            untyped=untype_source(source=typed),
            typed=typed,
            mode=mode,
            accepted=deviations,
        )
        for name, typed in pairs.items()
    }
    stored: dict[str, DictDictInt] = {}
    if baseline.is_file():
        raw: str = baseline.read_text(encoding="utf-8").strip()
        if raw not in {"", "{}"}:
            stored = loads(s=raw)
    if not stored:
        baseline.write_text(
            data=dumps(obj=results, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _ = stdout.write(f"WROTE baseline {baseline}\nPASS\n")
        return 0
    failed: bool = baseline_drift(results=results, stored=stored)
    _ = stdout.write(
        """\
FAIL
"""
        if failed
        else """\
PASS
""",
    )
    return 1 if failed else 0


def baseline_drift(
    *,
    results: dict[str, DictDictInt],
    stored: dict[str, DictDictInt],
) -> bool:
    """Print every score bucket that drifted from the stored baseline.

    Args:
        results (dict[str, DictDictInt]): Fresh per-pair scores.
        stored (dict[str, DictDictInt]): Baseline per-pair scores.

    Returns:
        bool: ``True`` when any bucket differs or is missing on either side.

    """
    failed: bool = False
    for name, sections in results.items():
        expected: DictDictInt = stored.get(name, {})
        for section, counts in sections.items():
            want: dict[str, int] = expected.get(section, {})
            for bucket, value in counts.items():
                if want.get(bucket, 0) != value:
                    failed = True
                    _ = stdout.write(
                        f"FAIL {name}.{section}.{bucket}: "
                        f"{value} != baseline {want.get(bucket, 0)}\n",
                    )
            for bucket, value in want.items():
                if bucket not in counts:
                    failed = True
                    _ = stdout.write(
                        f"FAIL {name}.{section}.{bucket}: "
                        f"missing != baseline {value}\n",
                    )
    return failed


def main() -> int:
    """Run the comparison or the round-trip gate.

    Returns:
        int: Zero on success, one on gate failure.

    """
    parser: ArgumentParser = ArgumentParser(
        prog="python -m scripts.compare.pair",
    )
    parser.add_argument("untyped", nargs="?")
    parser.add_argument("typed", nargs="?")
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--engine", action="store_true")
    parser.add_argument("--checker", action="store_true")
    parser.add_argument("--gate", action="store_true")
    parser.add_argument(
        "--baseline",
        type=Path,
        default=(
            Path(__file__).resolve().parents[2]
            / "scripts"
            / "benchmark"
            / "artifacts"
            / "resources"
            / "baseline_pair.json"
        ),
    )
    parser.add_argument(
        "--no-negotiate",
        dest="negotiate",
        action="store_false",
    )
    options: Namespace = parser.parse_args()
    mode: Mode = Mode(
        floor=options.min_confidence,
        negotiate=options.negotiate,
        engine=options.engine,
        checker=(build_checker(root=Path.cwd()) if options.checker else None),
    )
    if options.gate:
        return gate(baseline=options.baseline, mode=mode)
    if options.untyped is None or options.typed is None:
        parser.error(message="untyped and typed are required without --gate")
    deviations: list[DictStr] = (
        load_accepted_deviations(path=ACCEPTED_DEVIATIONS_PATH)
        if ACCEPTED_DEVIATIONS_PATH.is_file()
        else []
    )
    result: DictDictInt = compare(
        untyped=Path(options.untyped).read_text(encoding="utf-8"),
        typed=Path(options.typed).read_text(encoding="utf-8"),
        mode=mode,
        accepted=deviations,
    )
    _ = stdout.write(
        dumps(obj=result, indent=2, sort_keys=True) + "\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
