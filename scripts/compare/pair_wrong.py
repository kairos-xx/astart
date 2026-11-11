"""List the annotations that contradict (or only narrow) the typed twin.

Usage:

    PYTHONPATH=src:. python scripts/compare/pair_wrong.py UNTYPED TYPED
        [--engine] [--min-confidence 0.5] [--kind contradiction|narrower]

Converts the untyped module the way ``python -m scripts.compare.pair`` does and
prints every written annotation of the chosen kind next to the author's, so
patterns can be found and a filter or rule written for them.

"""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import stdout
from typing import TYPE_CHECKING

from astart.rules import (
    FixSettings,
    default_registries,
    fix_source,
    load_default_catalog,
)
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

if TYPE_CHECKING:
    from astart.rules.recovery import Context
    from astart.rules.registry import Registries


def main() -> int:
    """Print the mismatching annotations.

    Returns:
        int: Zero.

    """
    parser: ArgumentParser = ArgumentParser(prog="pair_wrong")
    parser.add_argument("untyped")
    parser.add_argument("typed")
    parser.add_argument("--engine", action="store_true")
    parser.add_argument("--min-confidence", type=float, default=0.8)
    parser.add_argument("--kind", default="contradiction")
    options: Namespace = parser.parse_args()
    untyped: str = Path(options.untyped).read_text(encoding="utf-8")
    typed: str = Path(options.typed).read_text(encoding="utf-8")
    registries: Registries = default_registries()
    fixed: str = fix_source(
        source=untyped,
        filename="untyped.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(
            ceiling=FixSafety.guarded,
            min_confidence=options.min_confidence,
            annotate_variables=True,
            engine=options.engine,
        ),
    ).source
    context: Context = merge_contexts(
        primary=module_context(source=typed),
        extra=module_context(source=fixed),
    )
    start: dict[str, str] = annotation_map(source=untyped)
    for label, written, truth in (
        (
            "param/return",
            annotation_map(source=fixed),
            annotation_map(source=typed),
        ),
        ("variable", variable_map(source=fixed), variable_map(source=typed)),
    ):
        for key in sorted(written):
            if key in start or key not in truth:
                continue
            mine: str = normalize_annotation(text=written[key])
            if mine == truth[key]:
                continue
            kind: str | None = relation(
                written=mine,
                truth=truth[key],
                context=context,
            )
            if kind == options.kind:
                _ = stdout.write(
                    f"{label:12} {key}: wrote {mine} | author {truth[key]}\n",
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
