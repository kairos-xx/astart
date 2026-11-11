"""Publish benchmark measurements and live sensor evidence together."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from io import StringIO
from json import dumps, loads
from typing import TYPE_CHECKING, Final, cast, final

from astart.source.metrics import Stat, enabled, metrics, trace_report

from scripts.benchmark.paths import Paths, write_artifact
from scripts.benchmark.treehash import tree_hash

type DictJsonValue = dict[str, JsonValue]

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


type JsonValue = (
    None | bool | int | float | str | list[JsonValue] | DictJsonValue
)


@final
class Constants:
    """Consolidated report file names, schema and section order.

    Attributes:
        json_name (Final[str]): Single machine-readable report in ``results``.
        markdown_name (Final[str]): Single human-readable report in ``results``
            .
        schema_version (Final[int]): Document layout version.
        tool_order (Final[tuple[str, ...]]): Preferred tool order in the
            Markdown report.

    """

    json_name: Final[str] = "report.json"
    markdown_name: Final[str] = "report.md"
    schema_version: Final[int] = 1
    tool_order: Final[tuple[str, ...]] = (
        "recovery",
        "semantic",
        "perf",
        "targets",
        "gate",
        "profile",
    )


def _cell(*, value: JsonValue) -> str:
    """Escape a measurement for a Markdown table cell.

    Args:
        value (JsonValue): JSON measurement.

    Returns:
        str: Single-line, pipe-safe text.

    """
    text: str = value if isinstance(value, str) else dumps(obj=value)
    return text.replace("|", "\\|").replace(
        "\n",
        "<br>",
    )


def _sections(*, value: JsonValue, title: str, depth: int = 2) -> list[str]:
    """Render nested measurements without collapsing evidence into one line.

    Args:
        value (JsonValue): Structured benchmark measurements.
        title (str): Section title.
        depth (int): Markdown heading level.

    Returns:
        list[str]: Spaced Markdown blocks.

    """
    heading: str = title.replace("_", " ").title()
    lines: list[str] = [f"{'#' * min(depth, 6)} {heading}", ""]
    if isinstance(value, dict):
        scalars: DictJsonValue = {
            key: item
            for key, item in value.items()
            if not isinstance(item, (dict, list))
        }
        if scalars:
            lines.extend(("| Measurement | Value |", "| --- | --- |"))
            lines.extend(
                f"| {_cell(value=key)} | {_cell(value=item)} |"
                for key, item in scalars.items()
            )
            lines.append("")
        for key, item in value.items():
            if isinstance(item, (dict, list)) and item:
                lines.extend(_sections(value=item, title=key, depth=depth + 1))
    elif isinstance(value, list):
        for index, item in enumerate(iterable=value):
            if isinstance(item, (dict, list)):
                lines.extend(
                    _sections(
                        value=item,
                        title=f"Item {index + 1}",
                        depth=depth + 1,
                    ),
                )
            else:
                lines.append(f"- {_cell(value=item)}")
        lines.append("")
    else:
        lines.extend((_cell(value=value), ""))
    return lines


def publish(
    *,
    name: str,
    text: str,
    output: Path | None = None,
    tool: str | None = None,
    variant: str | None = None,
) -> str:
    """Write matching JSON and Markdown with current-process sensor evidence.

    Args:
        name (str): Default JSON artifact filename for explicit destinations.
        text (str): Serialized benchmark result.
        output (Path | None): Explicit JSON destination, when supplied.
        tool (str | None): Benchmark command name for the consolidated report.
        variant (str | None): Corpus or run variant under the tool, when
            present.

    Returns:
        str: Enriched JSON, also suitable for the existing stdout contract.

    """
    result: JsonValue = cast(typ="JsonValue", val=loads(s=text))
    data: DictJsonValue = (
        result
        if isinstance(result, dict)
        else {
            "results": result,
        }
    )
    snapshot: Mapping[str, Stat] = metrics.snapshot()
    stats: DictJsonValue = {
        label: cast(typ="JsonValue", val=asdict(obj=stat))
        for label, stat in snapshot.items()
    }
    data["sensors"] = {
        "enabled": enabled(),
        "scope": "parent and completed worker processes",
        "timing": "inclusive nanoseconds; nested timings overlap",
        "stats": stats,
        "trace": cast(typ="JsonValue", val=asdict(obj=metrics.root)),
    }
    rendered: str = dumps(obj=data, indent=2) + "\n"
    if output is None and tool is not None:
        record(tool=tool, variant=variant, payload=data)
        return rendered
    destination: Path = write_artifact(name=name, text=rendered, output=output)
    lines: list[str] = [
        f"# Benchmark: {destination.stem}",
        "",
        f"[Complete JSON evidence]({destination.name})",
        "",
    ]
    for key, value in data.items():
        if key != "sensors":
            lines.extend(_sections(value=value, title=key))
    lines.extend(
        (
            "## Sensor bottlenecks",
            "",
            "Timings include the parent and completed worker processes. "
            "Parallel worker totals can exceed elapsed wall time.",
            (
                "Inclusive wall times overlap across nested calls; do "
                "not add them."
            ),
            "",
        ),
    )
    if snapshot:
        lines.extend(
            (
                (
                    "| Sensor | Calls | Wall ms | CPU ms | Mean ms | "
                    "Max ms | Errors |"
                ),
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ),
        )
        for label, stat in list(snapshot.items())[:25]:
            lines.append(
                f"| {_cell(value=label)} | {stat.calls} | "
                f"{stat.wall_ns / 1e6:.3f} | {stat.cpu_ns / 1e6:.3f} | "
                f"{stat.wall_ns / max(1, stat.calls) / 1e6:.3f} | "
                f"{stat.max_wall_ns / 1e6:.3f} | {stat.errors} |",
            )
        lines.extend(
            (
                "",
                "Top 25 sensors by inclusive wall time. "
                "All sensors and the complete call tree are in the JSON.",
                "",
            ),
        )
    else:
        lines.extend(
            (
                "No sensor samples were collected. "
                "Instrumentation may be disabled or the command "
                "may not perform measured work.",
                "",
            ),
        )
    if snapshot:
        trace: StringIO = StringIO()
        _ = trace_report(stream=trace, min_wall_ns=1_000_000, max_rows=40)
        lines.extend(
            (
                "## Measured call paths",
                "",
                "Self time excludes traced children. "
                "Paths below 1 ms are hidden; "
                "this preview is limited to 40 rows.",
                "",
                "```text",
                trace.getvalue().rstrip(),
                "```",
                "",
            ),
        )
    _ = write_artifact(
        name=destination.with_suffix(suffix=".md").name,
        text="\n".join(lines),
        output=destination.with_suffix(suffix=".md"),
    )
    return rendered


def _skeleton() -> DictJsonValue:
    """Return an empty consolidated report document.

    Returns:
        DictJsonValue: Fresh document skeleton.

    """
    return {
        "schema_version": Constants.schema_version,
        "generated": "",
        "tree": "",
        "tools": {},
        "sensors": None,
    }


def _load_document() -> DictJsonValue:
    """Read the consolidated report, tolerating a missing or stale file.

    Returns:
        DictJsonValue: Existing document, or a fresh skeleton.

    """
    path: Path = Paths.results / Constants.json_name
    try:
        data: JsonValue = loads(s=path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return _skeleton()
    return data if isinstance(data, dict) else _skeleton()


def _write_document(*, document: DictJsonValue) -> None:
    """Atomically replace ``report.json`` with the current document.

    Args:
        document (DictJsonValue): Consolidated report payload.

    """
    path: Path = Paths.results / Constants.json_name
    path.parent.mkdir(parents=True, exist_ok=True)
    staging: Path = path.with_name(name=path.stem + ".tmp")
    _ = staging.write_text(
        data=dumps(obj=document, indent=2) + "\n",
        encoding="utf-8",
    )
    staging.replace(target=path)


def record(
    *,
    tool: str,
    variant: str | None,
    payload: DictJsonValue,
) -> None:
    """Merge one tool payload into ``report.json`` and re-render ``report.md``.

    Args:
        tool (str): Benchmark command name, such as ``"recovery"``.
        variant (str | None): Corpus or run variant, stored as ``tool.variant``
            .
        payload (DictJsonValue): Sensor-enriched JSON payload for the run.

    """
    document: DictJsonValue = _load_document()
    raw_tools: JsonValue = document.get("tools")
    tools: DictJsonValue = raw_tools if isinstance(raw_tools, dict) else {}
    document["tools"] = tools
    key: str = f"{tool}.{variant}" if variant else tool
    tools[key] = payload
    document["generated"] = datetime.now(tz=UTC).isoformat(timespec="seconds")
    document["tree"] = tree_hash(root=Paths.root)
    document["sensors"] = payload.get("sensors")
    _write_document(document=document)
    _ = write_artifact(
        name=Constants.markdown_name,
        text=render_report(document=document),
    )


def _ordered_tools(*, tools: DictJsonValue) -> list[str]:
    """Order report tool keys by the preferred sequence, then alphabetically.

    Args:
        tools (DictJsonValue): ``tool[.variant]`` payload map.

    Returns:
        list[str]: Sorted tool keys.

    """
    rank: dict[str, int] = {
        name: index for index, name in enumerate(iterable=Constants.tool_order)
    }
    return sorted(
        tools,
        key=lambda key: (
            rank.get(key.split(sep=".", maxsplit=1)[0], len(rank)),
            key,
        ),
    )


def _tool_title(*, key: str) -> str:
    """Human-readable heading for one ``tool[.variant]`` key.

    Args:
        key (str): Report tool key.

    Returns:
        str: Title-cased tool and variant names.

    """
    parts: tuple[str, str, str] = key.partition(".")
    tool: str = parts[0].replace("_", " ").title()
    return f"{tool} — {parts[2]}" if parts[2] else tool


def _num(*, value: JsonValue) -> int:
    """Coerce a JSON scalar to an integer count or nanosecond total.

    Args:
        value (JsonValue): JSON measurement.

    Returns:
        int: Integer value, ``0`` for non-numeric entries.

    """
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def _trace_lines(*, node: DictJsonValue, depth: int = 0) -> list[str]:
    """Render stored call-tree nodes as bounded indented text rows.

    Args:
        node (DictJsonValue): ``asdict`` form of one ``TraceNode``.
        depth (int): Current indentation depth.

    Returns:
        list[str]: Markdown code-block rows, deepest wall time first.

    """
    rows: list[str] = []
    children: JsonValue = node.get("children")
    ordered: list[DictJsonValue] = (
        sorted(
            (item for item in children.values() if isinstance(item, dict)),
            key=lambda item: -_num(value=item.get("wall_ns", 0)),
        )
        if isinstance(children, dict)
        else []
    )
    min_depth: int = 5
    for child in ordered[:12]:
        label: JsonValue = child.get("label", "")
        wall: JsonValue = child.get("wall_ns", 0)
        calls: JsonValue = child.get("calls", 0)
        rows.append(
            (
                f"{'  ' * depth}{label}  calls={calls} wall="
                f"{_num(value=wall) / 1e6:.1f}ms"
            ),
        )
        if depth < min_depth:
            rows.extend(_trace_lines(node=child, depth=depth + 1))
    return rows[:60]


def _sensors_lines(*, sensors: JsonValue) -> list[str]:
    """Render the latest run's stored sensor evidence for Markdown.

    Args:
        sensors (JsonValue): ``sensors`` object stored in the report document.

    Returns:
        list[str]: Markdown lines for the sensor section.

    """
    if not isinstance(sensors, dict):
        return []
    stats: JsonValue = sensors.get("stats")
    lines: list[str] = [
        "## Sensor evidence — latest run",
        "",
        "Timings include the parent and completed worker processes. "
        "Parallel worker totals can exceed elapsed wall time. "
        "Inclusive wall times overlap across nested calls; do not add them.",
        "",
    ]
    if isinstance(stats, dict) and stats:
        ranked: list[tuple[str, DictJsonValue]] = sorted(
            (
                (label, item)
                for label, item in stats.items()
                if isinstance(item, dict)
            ),
            key=lambda pair: -_num(value=pair[1].get("wall_ns", 0)),
        )
        lines.extend(
            (
                (
                    "| Sensor | Calls | Wall ms | CPU ms | Mean ms | "
                    "Max ms | Errors |"
                ),
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ),
        )
        for label, stat in ranked[:25]:
            calls: int = _num(value=stat.get("calls", 0))
            wall: int = _num(value=stat.get("wall_ns", 0))
            cpu: int = _num(value=stat.get("cpu_ns", 0))
            peak: int = _num(value=stat.get("max_wall_ns", 0))
            lines.append(
                f"| {_cell(value=label)} | {calls} | {wall / 1e6:.3f} | "
                f"{cpu / 1e6:.3f} | "
                f"{wall / max(1, calls) / 1e6:.3f} | "
                f"{peak / 1e6:.3f} | {_num(value=stat.get('errors', 0))} |",
            )
        lines.extend(
            (
                "",
                "Top 25 sensors by inclusive wall time. "
                "All sensors and the complete call tree are in the JSON.",
                "",
            ),
        )
    trace: JsonValue = sensors.get("trace")
    if isinstance(trace, dict):
        tree: list[str] = _trace_lines(node=trace)
        if tree:
            lines.extend(
                (
                    "### Measured call paths",
                    "",
                    "Inclusive wall times per call path, deepest first.",
                    "",
                    "```text",
                    *tree,
                    "```",
                    "",
                ),
            )
    return lines


def render_report(*, document: DictJsonValue) -> str:
    """Render the consolidated Markdown report from the JSON document.

    Args:
        document (DictJsonValue): Consolidated report payload.

    Returns:
        str: Markdown text for ``report.md``.

    """
    lines: list[str] = [
        "# Benchmark report",
        "",
        f"Generated {document.get('generated') or 'never'} · "
        f"tree `{document.get('tree') or 'unknown'}` · "
        f"schema v{document.get('schema_version')}",
        "",
        (
            f"Machine-readable evidence: [{Constants.json_name}]("
            f"{Constants.json_name})"
        ),
        "",
    ]
    raw_tools: JsonValue = document.get("tools")
    tools: DictJsonValue = raw_tools if isinstance(raw_tools, dict) else {}
    if not tools:
        lines.extend(
            (
                "No benchmark sections recorded yet. Run "
                "`python -m scripts.benchmark` to populate this report.",
                "",
            ),
        )
        return "\n".join(lines)
    for key in _ordered_tools(tools=tools):
        payload: JsonValue = tools[key]
        lines.extend((f"## {_tool_title(key=key)}", ""))
        if isinstance(payload, dict):
            for name, value in payload.items():
                if name != "sensors":
                    lines.extend(_sections(value=value, title=name, depth=3))
        else:
            lines.extend(_sections(value=payload, title="Result", depth=3))
    lines.extend(_sensors_lines(sensors=document.get("sensors")))
    return "\n".join(lines) + "\n"
