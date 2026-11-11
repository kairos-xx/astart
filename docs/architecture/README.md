# Architecture and inference

System structure, the shared AST, inference evidence and generated naming contracts.

[Documentation index](../README.md)

| Document | Title |
| --- | --- |
| [CONSOLIDATION.md](CONSOLIDATION.md) | Consolidation design |
| [architecture.md](architecture.md) | `astart.rules` architecture |
| [evidence-ladder.md](evidence-ladder.md) | The evidence ladder — how `astart` decides a fix is safe |
| [hint-propagation.md](hint-propagation.md) | Hint propagation |
| [negotiation.md](negotiation.md) | Contract negotiation |
| [single-ast-architecture.md](single-ast-architecture.md) | Single AST architecture decision |
| [synthetic-names.json](synthetic-names.json) | Machine-readable synthetic names |
| [typing-inference.md](typing-inference.md) | Typing inference |

See [Package ownership decision](package-layout.md) for source, documentation
and transformation boundaries.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`CONSOLIDATION.md`](CONSOLIDATION.md) — All code now lives under `src/astart/`, with one installable package and one supported top-level import API. The lexical AST, source editor, semantic solver, and graph converter are components of this distribution. The graph converter is internal to `astart.graph` and contributes verified annotation candidates to `astart.semantic` through `semantic.graph_conversion`.
- [`architecture.md`](architecture.md) — One paragraph per module, taken verbatim from each module's docstring.
- [`evidence-ladder.md`](evidence-ladder.md) — Every fix `astart` offers is backed by a level of evidence, and every guarded fix requires a *combination* of levels — never inference alone. The ladder is defined in `docs/planning/TODO.md` §2 and enforced by `src/astart/rules/hints.py` + `src/astart/rules/confidence.py`.
- [`hint-propagation.md`](hint-propagation.md) — How `HintIndex` decides which annotations `astart fix` may write. The machinery lives in `src/astart/rules/hints.py`; this page describes what the three core methods do and the order the propagation passes run in. It is a specification, not a change log.
- [`negotiation.md`](negotiation.md) — `astart.rules.negotiation` types a module by letting evidence travel along a graph, in both directions, until nothing changes. It supplements the older hint index (`rules/hints.py`) and is on by default (`--no-negotiate` turns it off). The idea comes from the author's earlier Semantic Contract Farm project; this page records how it was adapted for a tool whose rule is *zero wrong annotations*.
- [`package-layout.md`](package-layout.md) — The former flat implementation modules mixed documentation, source machinery and transformations. Documentation rules were also separated from their model, renderer and synthesis helpers.
- [`single-ast-architecture.md`](single-ast-architecture.md) — Status: accepted direction; migration in progress. Date: 2026-11-09. The task acceptance is zero post-initial full-module parses for ordinary annotation, comment and documentation edits, with exact untouched source. This document does not claim the current implementation meets that target.
- [`synthetic-names.json`](synthetic-names.json) — Provide synthetic names json content.
- [`typing-inference.md`](typing-inference.md) — What `_Typer` in `src/astart/rules/provable.py` can prove from an expression's syntax alone, and which evidence classes a written annotation must pass through before it is applied.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
