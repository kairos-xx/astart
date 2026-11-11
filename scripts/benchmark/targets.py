"""Machine-checkable accuracy contract: targets A-01 to A-11 (task G-01).

Each contract row of ``docs/planning/TODO.md`` maps to one or more measurable
``Target`` entries in ``scripts/benchmark/artifacts/resources/targets.json``.
``collect``
gathers the metrics a selection of targets needs — running the pair
comparison, reading recovery report JSONs, running the semantic suite and
the pytest gates — and ``evaluate`` judges one target against the
collected numbers.

"""

from __future__ import annotations

from dataclasses import dataclass
from json import loads
from operator import eq, ge, gt, le, lt, ne
from os import environ
from pathlib import Path
from subprocess import CompletedProcess, run
from sys import executable
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, Final, final

type DictFloat = dict[str, float]
type DictDictInt = dict[str, dict[str, int]]

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Mapping


type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | dict[str, JsonValue]
)


@final
class Constants:
    """Group module-level constants.

    Attributes:
        root (Final[Path]): Repository root directory.
        targets_file (Final[Path]): Default target list.
        operators: Comparison functions by ``op`` string.
        pairs: ``(label, untyped, typed)`` conversion pairs measured.
        pytest_families: Final[
                Mapping[str, tuple[str, tuple[tuple[str, ...], ...]]]
            ]: Metric-prefix to ``(metric name, pytest argv)``.
        pair_timeout (Final[int]): Most seconds one pair conversion may take.
        pytest_timeout (Final[int]): Most seconds one pytest gate may take.
        result_words (Final[int]): Words in one ``NN passed`` summary fragment.

    """

    root: Final[Path] = Path(__file__).resolve().parents[2]
    targets_file: Final[Path] = (
        Path(__file__).parent / "artifacts" / "resources" / "targets.json"
    )
    operators: Final[Mapping[str, Callable[[float, float], bool]]] = {
        ">=": ge,
        "<=": le,
        "==": eq,
        "!=": ne,
        ">": gt,
        "<": lt,
    }
    pairs: Final[tuple[tuple[str, str, str], ...]] = (
        ("dev", "fixtures/untyped.py", "fixtures/typed.py"),
    )
    pytest_families: Final[
        Mapping[str, tuple[str, tuple[tuple[str, ...], ...]]]
    ] = {
        "idempotence": (
            "idempotence.share",
            (
                ("tests/astart/cli/test_cli_idempotence_corpus.py",),
                (
                    "tests/astart/rules/test_rules_determinism.py",
                    "-k",
                    "idempotent",
                ),
            ),
        ),
        "determinism": (
            "determinism.share",
            (
                (
                    "tests/astart/rules/test_rules_determinism.py",
                    "-k",
                    "seed_deterministic",
                ),
            ),
        ),
        "compile": (
            "compile.share",
            (("tests/astart/rules/test_protocol_typevar_danger.py",),),
        ),
        "kwargs_danger": (
            "kwargs_danger.share",
            (("tests/astart/rules/test_rules_kwargs_danger.py",),),
        ),
        "gold": (
            "gold.pass_share",
            (
                (
                    "tests/astart/rules/test_gold_expansion.py",
                    "-k",
                    "test_gold",
                ),
            ),
        ),
    }
    pair_timeout: Final[int] = 3600
    pytest_timeout: Final[int] = 3600
    result_words: Final[int] = 2


@final
@dataclass(frozen=True, slots=True)
class Target:
    """One measurable row of the accuracy contract.

    Attributes:
        id (str): Contract row (``A-01`` … ``A-11``).
        metric (str): Flat collected key, for example
            ``pair.dev.params.exact_share``.
        op (str): Comparison operator string.
        value (float): Threshold the metric is compared to.
        unit (str): Display unit: ``share``, ``count`` or ``seconds``.
        description (str): What the row measures.

    """

    id: str
    metric: str
    op: str
    value: float
    unit: str = "share"
    description: str = ""


def load_targets(*, path: Path) -> tuple[Target, ...]:
    """Read the target list from JSON.

    Args:
        path (Path): ``targets.json`` file.

    Returns:
        tuple[Target, ...]: The targets, in file order.

    """
    entries: list[dict[str, str | float]] = loads(
        s=path.read_text(encoding="utf-8"),
    )
    return tuple(
        Target(
            id=str(object=entry["id"]),
            metric=str(object=entry["metric"]),
            op=str(object=entry["op"]),
            value=float(entry["value"]),
            unit=str(object=entry.get("unit", "share")),
            description=str(object=entry.get("description", "")),
        )
        for entry in entries
    )


def evaluate(*, target: Target, reports: Mapping[str, float]) -> bool:
    """Judge one target against collected metrics.

    Args:
        target (Target): The contract row under test.
        reports (Mapping[str, float]): Collected metrics by flat key.

    Returns:
        bool: ``True`` when the measured value satisfies the operator;
            ``False`` when it fails or the metric was never collected.

    """
    measured: float | None = reports.get(target.metric)
    if measured is None:
        return False
    check: Callable[[float, float], bool] = Constants.operators[target.op]
    return check(measured, target.value)


def _subprocess_env() -> dict[str, str]:
    """Build the environment for benchmark and pytest subprocesses.

    Returns:
        dict[str, str]: The process environment with ``src:.`` on
            ``PYTHONPATH``.

    """
    env: dict[str, str] = dict(environ)
    source_paths: str = f"{Constants.root / 'src'}:{Constants.root}"
    current: str = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{source_paths}:{current}" if current else source_paths
    )
    return env


def _pair_report(
    *,
    untyped: Path,
    typed: Path,
    checker: bool,
) -> DictDictInt:
    """Run ``scripts.compare.pair`` on one conversion pair.

    Args:
        untyped (Path): Annotation-free source path.
        typed (Path): Author-annotated source path.
        checker (bool): Whether to pass ``--checker``.

    Returns:
        DictDictInt: The JSON score the command prints.

    """
    command: list[str] = [
        executable,
        "-m",
        "scripts.compare.pair",
        str(object=untyped),
        str(object=typed),
        "--engine",
        "--min-confidence",
        "0.5",
    ]
    if checker:
        command.append("--checker")
    proc: CompletedProcess[str] = run(
        args=command,
        cwd=Constants.root,
        env=_subprocess_env(),
        capture_output=True,
        text=True,
        check=False,
        timeout=Constants.pair_timeout,
    )
    if proc.returncode != 0:
        return {}
    report: DictDictInt = loads(s=proc.stdout)
    return report


def _pair_metrics(
    *,
    label: str,
    report: Mapping[str, Mapping[str, int]],
) -> DictFloat:
    """Flatten one pair score into contract metrics.

    Args:
        label (str): ``dev`` or ``resolver``.
        report (Mapping[str, Mapping[str, int]]): The ``scripts.compare.pair``
            JSON mapping.

    Returns:
        DictFloat: Flat metric keys for parameters/returns and variables.

    """
    found: DictFloat = {}
    for group_key, group_name in (
        ("parameters_and_returns", "params"),
        ("variables", "variables"),
    ):
        group: Mapping[str, int] = report.get(group_key, {})
        recoverable: int = group.get("to_recover", 0)
        correct: int = group.get("correct", 0)
        written: int = sum(
            count for name, count in group.items() if name != "to_recover"
        )
        base: str = f"pair.{label}.{group_name}"
        if recoverable:
            found[f"{base}.exact_share"] = correct / recoverable
            compatible: int = (
                correct
                + group.get("narrower", 0)
                + group.get("looser", 0)
                + group.get("accepted", 0)
            )
            found[f"{base}.compatible_share"] = compatible / recoverable
        if written:
            found[f"{base}.contradiction_share"] = (
                group.get("wrong", 0) / written
            )
    return found


def _pooled_pair_metrics(
    *,
    reports: Collection[Mapping[str, Mapping[str, int]]],
) -> DictFloat:
    """Pool exact, compatible and contradiction shares across pairs.

    Args:
        reports (Collection[Mapping[str, Mapping[str, int]]]): The
            ``scripts.compare.pair`` JSON mappings of every pair.

    Returns:
        DictFloat: ``pair.both.*`` pooled over pairs and
            ``pair.all.*`` pooled over pairs and groups.

    """
    found: DictFloat = {}
    all_written: int = 0
    all_wrong: int = 0
    all_recoverable: int = 0
    all_compatible: int = 0
    for group_key, group_name in (
        ("parameters_and_returns", "params"),
        ("variables", "variables"),
    ):
        recoverable: int = 0
        correct: int = 0
        compatible: int = 0
        written: int = 0
        wrong: int = 0
        for report in reports:
            group: Mapping[str, int] = report.get(group_key, {})
            recoverable += group.get("to_recover", 0)
            correct += group.get("correct", 0)
            compatible += (
                group.get("correct", 0)
                + group.get("narrower", 0)
                + group.get("looser", 0)
                + group.get("accepted", 0)
            )
            wrong += group.get("wrong", 0)
            written += sum(
                count for name, count in group.items() if name != "to_recover"
            )
        if recoverable:
            found[f"pair.both.{group_name}.exact_share"] = (
                correct / recoverable
            )
            found[f"pair.both.{group_name}.compatible_share"] = (
                compatible / recoverable
            )
        if written:
            found[f"pair.both.{group_name}.contradiction_share"] = (
                wrong / written
            )
        all_recoverable += recoverable
        all_compatible += compatible
        all_written += written
        all_wrong += wrong
    if all_recoverable:
        found["pair.all.compatible_share"] = all_compatible / all_recoverable
    if all_written:
        found["pair.all.contradiction_share"] = all_wrong / all_written
    return found


def _collect_pairs(*, gated: bool) -> DictFloat:
    """Measure the dev and resolver conversion pairs.

    Args:
        gated (bool): Whether the gated-kept share is needed (one extra,
            ``--checker`` conversion per pair).

    Returns:
        DictFloat: Flat ``pair.*`` metrics.

    """
    found: DictFloat = {}
    reports: list[DictDictInt] = []
    gated_written_total: int = 0
    written_total: int = 0
    for label, untyped, typed in Constants.pairs:
        report: DictDictInt = _pair_report(
            untyped=Constants.root / untyped,
            typed=Constants.root / typed,
            checker=False,
        )
        reports.append(report)
        found.update(_pair_metrics(label=label, report=report))
        written: int = sum(
            sum(count for name, count in group.items() if name != "to_recover")
            for group in report.values()
        )
        written_total += written
        if gated:
            kept: DictDictInt = _pair_report(
                untyped=Constants.root / untyped,
                typed=Constants.root / typed,
                checker=True,
            )
            gated_written: int = sum(
                sum(
                    count
                    for name, count in group.items()
                    if name != "to_recover"
                )
                for group in kept.values()
            )
            gated_written_total += gated_written
            if written:
                found[f"pair.{label}.gated.kept_share"] = (
                    gated_written / written
                )
    found.update(_pooled_pair_metrics(reports=reports))
    if written_total and gated:
        found["pair.both.gated.kept_share"] = (
            gated_written_total / written_total
        )
    return found


def _newest_report(*, directory: Path, needle: str) -> Path | None:
    """Find the newest recovery report JSON under a directory.

    Args:
        directory (Path): Directory of ``--json`` report files.
        needle (str): Substring the file name must contain (``std`` or ``ext``
            ).

    Returns:
        Path | None: The newest matching file, or ``None``.

    """
    if not directory.is_dir():
        return None
    candidates: list[Path] = [
        path
        for path in directory.glob(pattern="recovery*.json")
        if needle in path.name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _aggregate_recovery(
    *,
    report_dir: Path,
) -> dict[str, dict[str, JsonValue]]:
    """Read consolidated ``recovery.*`` summaries from ``report.json``.

    Args:
        report_dir (Path): Directory containing the consolidated report.

    Returns:
        dict[str, dict[str, JsonValue]]: ``std`` /``ext`` label to summary
            mapping.

    """
    path: Path = report_dir / "report.json"
    if not path.is_file():
        return {}
    try:
        document: JsonValue = loads(s=path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    tools: JsonValue = (
        document.get("tools") if isinstance(document, dict) else None
    )
    found: dict[str, dict[str, JsonValue]] = {}
    if not isinstance(tools, dict):
        return found
    for key, payload in tools.items():
        if not key.startswith("recovery."):
            continue
        variant: str = key.removeprefix("recovery.")
        summary: JsonValue = (
            payload.get("summary") if isinstance(payload, dict) else None
        )
        if not isinstance(summary, dict):
            continue
        for label, needle in (("std", "std"), ("ext", "ext")):
            if needle in variant and label not in found:
                found[label] = summary
    return found


def _summary_metrics(
    *,
    label: str,
    summary: dict[str, JsonValue],
    found: DictFloat,
) -> None:
    """Fold one recovery summary into flat target metrics.

    Args:
        label (str): Corpus label, ``std`` or ``ext``.
        summary (dict[str, JsonValue]): Report ``summary`` object.
        found (DictFloat): Metric map being filled.

    """
    for key, metric in (
        ("precision", "precision"),
        ("recall", "recall"),
        ("new_errors", "new_errors"),
    ):
        value: JsonValue = summary.get(key)
        if isinstance(value, (int, float)):
            found[f"recovery.{label}.{metric}"] = float(value)
    crashed: JsonValue = summary.get("crashed")
    if isinstance(crashed, list):
        found[f"recovery.{label}.crashes"] = float(len(crashed))


def _collect_recovery(*, report_dir: Path) -> DictFloat:
    """Read precision, crashes and checker errors from recovery reports.

    Args:
        report_dir (Path): Directory the ``--json`` reports were written to.

    Returns:
        DictFloat: Flat ``recovery.std.*`` and ``recovery.ext.*`` metrics.

    """
    found: DictFloat = {}
    aggregate: dict[str, dict[str, JsonValue]] = _aggregate_recovery(
        report_dir=report_dir,
    )
    for label, needle in (("std", "std"), ("ext", "ext")):
        summary: dict[str, JsonValue] | None = aggregate.get(label)
        if summary is None:
            path: Path | None = _newest_report(
                directory=report_dir,
                needle=needle,
            )
            if path is None:
                continue
            raw: JsonValue = loads(s=path.read_text(encoding="utf-8"))
            candidate: JsonValue = (
                raw.get("summary") if isinstance(raw, dict) else None
            )
            summary = candidate if isinstance(candidate, dict) else None
        if summary is None:
            continue
        _summary_metrics(label=label, summary=summary, found=found)
    return found


def _collect_semantic() -> DictFloat:
    """Run the semantic-equivalence projects and flatten the outcome.

    Returns:
        DictFloat: ``semantic.passed_share`` when the command ran.

    """
    with TemporaryDirectory() as directory:
        out: Path = Path(directory) / "semantic.json"
        run(
            args=[
                executable,
                "-m",
                "scripts.benchmark",
                "semantic",
                "--json",
                str(object=out),
            ],
            cwd=Constants.root,
            env=_subprocess_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=Constants.pytest_timeout,
        )
        if not out.is_file():
            return {}
        results: list[dict[str, object]] = loads(
            s=out.read_text(encoding="utf-8"),
        )
        if not results:
            return {}
        passed: int = sum(1 for item in results if item.get("passed"))
        return {"semantic.passed_share": passed / len(results)}


def _pytest_share(*, selections: tuple[tuple[str, ...], ...]) -> float | None:
    """Run pytest files and return the pass share.

    Args:
        selections (tuple[tuple[str, ...], ...]): ``(path, [-k, filter]…)``
            argv tails.

    Returns:
        float | None:
            ``passed / (passed + failed)``, or ``None`` when nothing ran.

    """
    passed: int = 0
    failed: int = 0
    for selection in selections:
        proc: CompletedProcess[str] = run(
            args=[
                executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                *selection,
            ],
            cwd=Constants.root,
            env=_subprocess_env(),
            capture_output=True,
            text=True,
            check=False,
            timeout=Constants.pytest_timeout,
        )
        tail: str = proc.stdout.strip().splitlines()[-1] if proc.stdout else ""
        for part in tail.split(sep=","):
            words: list[str] = part.strip().split()
            if len(words) != Constants.result_words or not words[0].isdigit():
                continue
            if words[1] == "passed":
                passed += int(words[0])
            elif words[1] in ("failed", "error", "errors"):
                failed += int(words[0])
    total: int = passed + failed
    return None if total == 0 else passed / total


def _collect_perf() -> DictFloat:
    """Read the accepted throughput baseline as the perf metrics.

    Returns:
        DictFloat: ``perf.<lines>.median_seconds`` per bucket.

    """
    path: Path = (
        Constants.root
        / "scripts"
        / "benchmark"
        / "artifacts"
        / "resources"
        / "baseline_perf.json"
    )
    if not path.is_file():
        return {}
    buckets: dict[str, DictFloat] = loads(
        s=path.read_text(encoding="utf-8"),
    ).get("buckets", {})
    return {
        f"perf.{size}.median_seconds": entry["median_seconds"]
        for size, entry in buckets.items()
    }


def collect(
    *,
    report_dir: Path,
    metrics: Collection[str],
) -> DictFloat:
    """Gather the metrics a set of targets needs.

    Only the families present in ``metrics`` are computed, so
    ``--only A-02`` measures just the conversion pairs.

    Args:
        report_dir (Path): Directory recovery ``--json`` reports were written
            to.
        metrics (Collection[str]): Metric keys of the selected targets.

    Returns:
        DictFloat: ``metric: value`` for every key that could be measured.

    """
    families: set[str] = {metric.split(sep=".")[0] for metric in metrics}
    found: DictFloat = {}
    if "pair" in families:
        found.update(
            _collect_pairs(
                gated=any(".gated." in metric for metric in metrics),
            ),
        )
    if "recovery" in families or "checker" in families:
        found.update(_collect_recovery(report_dir=report_dir))
    if "semantic" in families:
        found.update(_collect_semantic())
    for family, (metric_name, selections) in Constants.pytest_families.items():
        if family in families:
            share: float | None = _pytest_share(selections=selections)
            if share is not None:
                found[metric_name] = share
    if "perf" in families:
        found.update(_collect_perf())
    return found


def format_row(*, target: Target, reports: Mapping[str, float]) -> str:
    """Render one target row like ``A-02  FAIL  52.5 % < 90 %``.

    Args:
        target (Target): The contract row.
        reports (Mapping[str, float]): Collected metrics.

    Returns:
        str: The formatted verdict line.

    """
    measured: float | None = reports.get(target.metric)
    verdict: str = (
        "PASS" if evaluate(target=target, reports=reports) else "FAIL"
    )
    actual: str = (
        "n/a"
        if measured is None
        else f"{measured * 100:.1f} %"
        if target.unit == "share"
        else f"{measured:g}"
    )
    wanted: str = (
        f"{target.value * 100:g} %"
        if target.unit == "share"
        else f"{target.value:g}"
    )
    return f"{target.id}  {verdict}  {actual} {target.op} {wanted}"
