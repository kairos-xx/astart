# `scripts/`

Maintenance scripts for astart.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Maintenance scripts for astart.

### Subdirectories

- [`benchmark/`](benchmark/README.md) — Benchmarks for the annotation fixer.
- [`compare/`](compare/README.md) — Run from the repository root:
- [`todo_update/`](todo_update/README.md) — TODO dashboard, lint and status ledger tooling for docs/planning/TODO.md.
- [`utils/`](utils/README.md) — Utility entry points that run outside the package.

<!-- exactus:inventory:end -->

## Conversion reference evidence

`python scripts/compare --no-todo` compares the current conversion
with `fixtures/typed.py` and loads `fixtures/artifacts/typed_graph.json`. The graph
must match the authored source digest. Use `--reference-graph PATH` to select
another graph alongside `--typed PATH`; custom typed files otherwise retain
source-only reporting.

The Markdown explains differences with declared annotations and contextual
source observations. JSON retains all annotation targets, evidence records,
and per-item links, including overloads. Constraint and type IDs resolve in the
source graph. Contextual observations are not proofs of expected types, and
saved graph comparison verdicts are never reused to score a new conversion.
Reference-only definitions are reported separately from missing annotations.

The summary separates exact normalized spelling from scorer-equivalent types.
`ListInt` and `list[int]` can be equivalent while alias synthesis still needs
work. JSON preserves `correct` for spelling matches and adds `equivalent` and
`semantic_exact` (`correct + equivalent`); `looser` counts only wider types.
Narrower types are counted separately, including fixed tuples compared with
variadic reference tuples. Source digests identify the compared artifacts.

Use `--reuse --no-todo --out-dir PATH` to inspect a saved
`PATH/result.py` without rerunning conversion or updating TODO.

The conversion report compares generated documentation and declarations as well
as annotations. `artifacts` in `scripts/compare/artifacts/results/conversion-report.json` retains the full
expected/actual contracts, qualified identities, source lines and structured
docstring fields. Markdown provides category totals and collapsible evidence.
Annotation scores remain separate. Structural equivalence is not a proof of
semantic equivalence; documentation prose is not judged for meaning.
Run `python scripts/compare` for a fresh conversion, or add
`--reuse` to compare the explicitly recorded saved output.

The integrated comparison entry point is `python scripts/compare` (equivalently
`python -m scripts.compare`). See [compare/README.md](compare/README.md).
