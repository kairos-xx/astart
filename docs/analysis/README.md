# Analysis and benchmarks

Measured conversion behavior, inference gaps and legacy-project assessments.

[Documentation index](../README.md)

| Document | Title |
| --- | --- |
| [scripts.benchmark.md](benchmarks.md) | Benchmarks |
| [contradictions.md](contradictions.md) | Dev-Pair Contradiction Root-Cause Analysis |
| [conversion-gap-insights.md](conversion-gap-insights.md) | Conversion gap analysis: untyped.py → typed.py |
| [legacy-project-analysis.json](legacy-project-analysis.json) | Machine-readable legacy project analysis |
| [legacy-project-analysis.md](legacy-project-analysis.md) | Legacy inference and transformation analysis |
| [opacity-owners.md](opacity-owners.md) | Opacity Owners |

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`benchmarks.md`](benchmarks.md) — `astart.rules.recovery` strips the parameter and return annotations from a well-typed module, runs the guarded fixer, and compares what it wrote with the original. Run it with
- [`contradictions.md`](contradictions.md) — Root-cause table for every contradiction produced by `scripts/compare/pair_wrong.py` on `fixtures/untyped.py` against `fixtures/typed_author.py` (`--engine --min-confidence 0.5`), per task G-04.
- [`conversion-gap-insights.md`](conversion-gap-insights.md) — Date: 2026-11-15. Tree: working tree at analysis time (TODO generated block reports reference `79ce83548ccf`).
- [`legacy-project-analysis.json`](legacy-project-analysis.json) — Provide legacy project analysis json content.
- [`legacy-project-analysis.md`](legacy-project-analysis.md) — The reusable mechanisms are indexed semantic queries, typed evidence, explicit synthesis decisions, stub projection and structured AST editing. They should extend Astart's existing components. Importing the old application or copying its independent parse/graph/formatting stacks would undermine the requested single-AST architecture.
- [`opacity-owners.md`](opacity-owners.md) — Every reason string reported by `scripts/compare/opacity_report.py` on `fixtures/untyped.py`, `fixtures/*_untyped.py.txt` and `tests/corpus/extended` is assigned an owning backlog task in `docs/planning/TODO.md` (task G-03). No reason is left unowned.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
