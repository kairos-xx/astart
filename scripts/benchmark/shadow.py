"""Compare the negotiator with the hint index on stripped, typed modules.

Both approaches see the same annotation-free source; their annotations are
scored against the original ones. Nothing is written back: this measures
what negotiation would add or take away before it is allowed to change any
output (``docs/planning/TODO.md`` F-19).

Usage::

    PYTHONPATH=src:. python -m scripts.benchmark.shadow
        tests/corpus/extended --jobs 8

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from json import dumps
from pathlib import Path
from sys import stdout
from typing import Final, final

from astart import CommentedModule
from astart import parse as parse_module
from astart.rules.hints import (
    Hint,
    HintIndex,
    Key,
    engine_proposals,
    escaped_function_names,
)
from astart.rules.negotiation.run import (
    Verdicts,
    function_nodes,
    function_paths,
    negotiate_module,
)
from astart.rules.recovery import (
    annotation_map,
    module_context,
    normalize_annotation,
    relation,
    strip_annotations,
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        verdicts (Final[tuple[str, ...]]): Outcome classes of one written
            annotation.
        crashes (Final[tuple[type[Exception], ...]]): Exception types reported
            as one module's
            crash instead of ending the whole run.
        examples (Final[int]): Most example notes kept per group.

    """

    verdicts: Final[tuple[str, ...]] = (
        "correct",
        "compatible",
        "wrong",
        "invented",
    )
    crashes: Final[tuple[type[Exception], ...]] = (Exception,)
    examples: Final[int] = 25


@final
@dataclass(slots=True)
class Tally:
    """Counts of one group of written annotations.

    Attributes:
        correct (int): Equal to the original.
        compatible (int): A subtype or supertype of the original.
        wrong (int): Contradicting the original.
        invented (int): Having no original (a synthesized name).
        examples (list[str]): A few ``wrong`` or ``compatible`` cases for
            inspection.
        bases (Counter[str]): Verdict counts keyed by ``basis:verdict``.

    """

    correct: int = 0
    compatible: int = 0
    wrong: int = 0
    invented: int = 0
    examples: list[str] = field(default_factory=list)
    bases: Counter[str] = field(default_factory=Counter)

    def add(self, *, verdict: str, note: str, basis: str = "") -> None:
        """Count one annotation.

        Args:
            verdict (str): One of ``Constants.verdicts``.
            note (str): Description kept for non-exact verdicts.
            basis (str): The hint basis behind the annotation, when known.

        """
        setattr(self, verdict, getattr(self, verdict) + 1)
        if basis:
            self.bases[f"{basis}:{verdict}"] += 1
        if (
            verdict in ("wrong", "compatible")
            and len(self.examples) < Constants.examples
        ):
            self.examples.append(note)

    def merge(self, *, other: Tally) -> None:
        """Add another tally into this one.

        Args:
            other (Tally): The tally to absorb.

        """
        self.correct += other.correct
        self.compatible += other.compatible
        self.wrong += other.wrong
        self.invented += other.invented
        self.bases.update(other.bases)
        self.examples.extend(
            other.examples[: Constants.examples - len(self.examples)],
        )


@final
@dataclass(slots=True)
class Comparison:
    """Existing versus negotiated annotations over some modules.

    Attributes:
        truth (int): Original annotations seen.
        both (Tally): Written by both and identical.
        differ_existing (Tally): Written by both, scored on the hint index's
            text.
        differ_negotiated (Tally): Written by both, scored on the negotiator's
            text.
        only_existing (Tally): Written by the hint index alone.
        only_negotiated (Tally): Written by the negotiator alone.
        crashed (list[str]): Modules that raised.
        conflicts (int): Conflicts negotiation reported.

    """

    truth: int = 0
    both: Tally = field(default_factory=Tally)
    differ_existing: Tally = field(default_factory=Tally)
    differ_negotiated: Tally = field(default_factory=Tally)
    only_existing: Tally = field(default_factory=Tally)
    only_negotiated: Tally = field(default_factory=Tally)
    crashed: list[str] = field(default_factory=list)
    conflicts: int = 0


def _verdict(*, written: str, truth: str | None, context_source: str) -> str:
    """Classify one written annotation against the original.

    Args:
        written (str): The annotation text.
        truth (str | None): The original annotation, or ``None`` when there is
            none.
        context_source (str): The original module's source, for alias lookup.

    Returns:
        str: One of ``Constants.verdicts``.

    """
    if truth is None:
        return "invented"
    text: str = normalize_annotation(text=written)
    if text == truth:
        return "correct"
    kind: str | None = relation(
        written=text,
        truth=truth,
        context=module_context(source=context_source),
    )
    return "wrong" if kind == "contradiction" else "compatible"


def _compare_module(*, source: str, name: str) -> Comparison:
    """Compare both approaches on one module.

    Args:
        source (str): Original (annotated) source.
        name (str): Label used in examples.

    Returns:
        Comparison: The comparison for this module.

    """
    truth: dict[str, str] = annotation_map(source=source)
    module: CommentedModule = parse_module(
        source=strip_annotations(source=source),
    )
    paths: dict[Key, str] = function_paths(module=module)
    proposals: dict[Key, str] = engine_proposals(module=module)
    corroboration: dict[str, str] = {
        paths[key]: text for key, text in proposals.items() if key in paths
    }
    index: HintIndex = HintIndex.create(module=module, stubs_path=None)
    existing: dict[str, str] = {}
    bases: dict[str, str] = {}
    for path, node in function_nodes(module=module).items():
        hint: Hint | None = index.hint_for(node=node)
        if hint is not None:
            existing[path] = hint.source
            bases[path] = hint.basis.value
    verdicts: Verdicts = negotiate_module(
        module=module,
        corroboration=corroboration,
        escaped=escaped_function_names(module=module),
    )
    result: Comparison = Comparison(
        truth=len(truth),
        conflicts=len(verdicts.conflicts),
    )
    for path in sorted(existing.keys() | verdicts.accepted.keys()):
        old, new = existing.get(path), verdicts.accepted.get(path)
        original: str | None = truth.get(path)
        if old is not None and new is not None and old == new:
            result.both.add(
                verdict=_verdict(
                    written=new,
                    truth=original,
                    context_source=source,
                ),
                note=f"{name}:{path} wrote {new!r} expected {original!r}",
            )
            continue
        if old is not None:
            target: Tally = (
                result.differ_existing if new else result.only_existing
            )
            target.add(
                verdict=_verdict(
                    written=old,
                    truth=original,
                    context_source=source,
                ),
                note=f"{name}:{path} existing {old!r} expected {original!r}",
                basis=bases[path],
            )
        if new is not None:
            target = (
                result.differ_negotiated if old else result.only_negotiated
            )
            target.add(
                verdict=_verdict(
                    written=new,
                    truth=original,
                    context_source=source,
                ),
                note=f"{name}:{path} negotiated {new!r} expected {original!r}",
            )
    return result


def _task(*, path: Path) -> Comparison:
    """Compare one file, containing any crash.

    Args:
        path (Path): A ``.py`` or ``.py`` module.

    Returns:
        Comparison: The comparison; a crashed one records the file name.

    """
    try:
        return _compare_module(
            source=path.read_text(encoding="utf-8"),
            name=path.name.split(sep=".py")[0],
        )
    except Constants.crashes as error:
        crashed: Comparison = Comparison()
        crashed.crashed.append(f"{path.name}: {type(error).__name__}: {error}")
        return crashed


def _run_one(path: str, /) -> Comparison:
    """Pool entry point.

    Args:
        path (str): File path.

    Returns:
        Comparison: The comparison.

    """
    return _task(path=Path(path))


def _summary(
    *,
    total: Comparison,
) -> dict[str, int | list[str] | dict[str, int] | dict[str, list[str]]]:
    """Reduce a comparison to printable numbers.

    Args:
        total (Comparison): The merged comparison.

    Returns:
        dict[str, int | list[str] | dict[str, int] | dict[str, list[str]]]: A
            JSON-compatible summary.

    """
    groups: dict[str, Tally] = {
        "both": total.both,
        "differ_existing": total.differ_existing,
        "differ_negotiated": total.differ_negotiated,
        "only_existing": total.only_existing,
        "only_negotiated": total.only_negotiated,
    }
    return {
        "truth": total.truth,
        "conflicts": total.conflicts,
        "crashed": total.crashed,
        **{
            name: {key: getattr(tally, key) for key in Constants.verdicts}
            for name, tally in groups.items()
        },
        "only_existing_bases": dict(total.only_existing.bases.most_common()),
        "examples": {
            name: tally.examples
            for name, tally in groups.items()
            if tally.examples
        },
    }


def main() -> int:
    """Run the comparison over a directory.

    Returns:
        int: Zero.

    """
    parser: ArgumentParser = ArgumentParser(
        prog="python -m scripts.benchmark.shadow",
    )
    parser.add_argument("corpus")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--json", dest="output", default="")
    options: Namespace = parser.parse_args()
    files: list[Path] = sorted(
        Path(options.corpus).glob(pattern="*.py*"),
    )
    if options.limit:
        files = files[: options.limit]
    total: Comparison = Comparison()
    pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=options.jobs)
    with pool:
        for part in pool.map(_run_one, [str(object=item) for item in files]):
            total.truth += part.truth
            total.conflicts += part.conflicts
            total.crashed.extend(part.crashed)
            total.both.merge(other=part.both)
            total.differ_existing.merge(other=part.differ_existing)
            total.differ_negotiated.merge(other=part.differ_negotiated)
            total.only_existing.merge(other=part.only_existing)
            total.only_negotiated.merge(other=part.only_negotiated)
    text: str = (
        dumps(obj=_summary(total=total), indent=2, sort_keys=True) + "\n"
    )
    if options.output:
        Path(options.output).write_text(data=text, encoding="utf-8")
    _ = stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
