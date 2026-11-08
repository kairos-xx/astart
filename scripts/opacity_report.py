"""Explain why nodes of a module stay unknown to the contract negotiator.

Usage::

    PYTHONPATH=src python scripts/opacity_report.py FILE [--samples 4]

Prints, for the reportable nodes (parameters and returns) and for the local
variables, how many are declared, settled, blocked by a direct reason, or
blocked because something they depend on is. Direct reasons come with a few
sample expressions. Fix the biggest reason, run it again, repeat.

``collect`` returns the same data as objects, for the conversion report.
"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from sys import stdout
from typing import TYPE_CHECKING, final

from astart import parse
from astart.rules.hints import escaped_function_names
from astart.rules.negotiation.builders import Built, build_contracts
from astart.rules.negotiation.negotiator import Negotiation, Negotiator
from astart.rules.negotiation.policy import blocked_nodes
from astart.stubs import host_resolver

if TYPE_CHECKING:
    from astart.ast import CommentedModule
    from astart.rules.negotiation.beliefs import Belief


@final
@dataclass(frozen=True, slots=True)
class Row:
    """One reason and how many nodes it affects.

    Attributes:
        label: Short reason label.
        count: Number of nodes with that reason.
        samples: Up to a few ``(node path, evidence)`` pairs (direct reasons).

    """

    label: str
    count: int
    samples: list[tuple[str, str]]


@final
@dataclass(frozen=True, slots=True)
class Section:
    """The nodes of one kind (parameters and returns, or variables).

    Attributes:
        title: Kind of node.
        total: Number of nodes of this kind.
        rows: Reasons, most frequent first.
        nodes: Label and evidence of every node, by node path.

    """

    title: str
    total: int
    rows: list[Row]
    nodes: dict[str, tuple[str, str]]


def classify(
    *,
    path: str,
    built: Built,
    result: Negotiation,
    blocked: frozenset[str],
) -> str:
    """Say what happened to one node.

    Args:
        path: Node path.
        built: The module's contract graph.
        result: The solved negotiation.
        blocked: Nodes whose evidence is incomplete.

    Returns:
        A short label.

    """
    if path in built.opaque:
        return "direct: " + built.why.get(path, "?").split(sep=":")[0]
    if path in result.lost:
        return "lost a contribution"
    if path in blocked:
        return "downstream of a blocked node"
    belief: Belief = result.beliefs[path]
    if belief.declared is not None:
        return "declared"
    return "unsettled (no evidence)" if belief.settle() is None else "settled"


def collect(*, source: str, samples: int = 4) -> list[Section]:
    """Analyse a module and group its nodes by reason.

    Args:
        source: Python source of the module.
        samples: Examples kept per direct reason.

    Returns:
        One section for parameters and returns and one for local variables.

    """
    module: CommentedModule = parse(source=source)
    built: Built = build_contracts(
        module=module,
        escaped=escaped_function_names(module=module),
        library=host_resolver(),
    )
    result: Negotiation = Negotiator().solve(graph=built.graph)
    blocked: frozenset[str] = blocked_nodes(built=built, result=result)
    sections: list[Section] = []
    for title, paths in (
        ("parameters and returns", list(built.kinds)),
        ("local variables", list(built.variables)),
    ):
        counts: Counter[str] = Counter()
        found: dict[str, list[tuple[str, str]]] = defaultdict(list)
        nodes: dict[str, tuple[str, str]] = {}
        for path in paths:
            label: str = classify(
                path=path,
                built=built,
                result=result,
                blocked=blocked,
            )
            counts[label] += 1
            nodes[path] = (label, built.why.get(path, ""))
            if label.startswith("direct") and len(found[label]) < samples:
                found[label].append((path, built.why.get(path, "")))
        rows: list[Row] = [
            Row(label=label, count=count, samples=found.get(label, []))
            for label, count in counts.most_common()
        ]
        sections.append(
            Section(title=title, total=len(paths), rows=rows, nodes=nodes),
        )
    return sections


def main() -> int:
    """Print the report for one file.

    Returns:
        Zero.

    """
    parser: ArgumentParser = ArgumentParser(prog="opacity_report")
    parser.add_argument("file")
    parser.add_argument("--samples", type=int, default=4)
    options: Namespace = parser.parse_args()
    sections: list[Section] = collect(
        source=Path(options.file).read_text(encoding="utf-8"),
        samples=options.samples,
    )
    for section in sections:
        _ = stdout.write(f"== {section.title}: {section.total}\n")
        for row in section.rows:
            _ = stdout.write(f"  {row.count:4} {row.label}\n")
            for node, why in row.samples:
                _ = stdout.write(f"         e.g. {node} <- {why}"[:119] + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
