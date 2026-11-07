# `semantic/`

Dependency-free semantic graph and safe abstract evaluation for Python ASTs.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Dependency-free semantic graph and abstract evaluation for ASTs.
- [`analyzer.py`](analyzer.py) — Public orchestrator for persistent symbols and bounded static semantics.
- [`control_flow.py`](control_flow.py) — Inspectible Python control-flow graphs and reaching-definition dataflow.
- [`evaluator.py`](evaluator.py) — Bounded, side-effect-aware abstract interpreter for mutable Python ASTs.
- [`functions.py`](functions.py) — Soundly keyed abstract call summaries with explicit observable effects.
- [`graph_bridge.py`](graph_bridge.py) — Loss-aware conversion between the internal graph engine and native types.
- [`graph_conversion.py`](graph_conversion.py) — Execute Astart's graph conversion and merge safe conclusions into ASTs.
- [`heap.py`](heap.py) — Abstract allocation sites, mutable storage and alias relations.
- [`identities.py`](identities.py) — Stable semantic identifiers, symbols, references, and dependency indexes.
- [`parameter_kinds.py`](parameter_kinds.py) — Callable parameter kinds shared by contract and relation analysis.
- [`scopes.py`](scopes.py) — Python lexical scope graph: symbols, bindings and occurrences.
- [`stubs.py`](stubs.py) — Lazy, nonexecuting Python stub lookup adapted from Astart.
- [`type_expressions.py`](type_expressions.py) — Dependency-free, loss-aware parsing of structured Python type expressions.
- [`type_inference.py`](type_inference.py) — Bounded bidirectional type inference with immutable provenance records.
- [`type_shapes.py`](type_shapes.py) — Immutable, normalized type shapes and their join operations.
- [`typing_contracts.py`](typing_contracts.py) — Pure-AST callable signatures, generic contracts, class and protocol indexes.
- [`typing_relations.py`](typing_relations.py) — Conservative structural and nominal type-contract relationships.
- [`values.py`](values.py) — Immutable abstract values, proof states, and bounded lattice operations.
- [`worklist.py`](worklist.py) — Incremental, deletion-safe, deterministic forward dataflow solver.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
