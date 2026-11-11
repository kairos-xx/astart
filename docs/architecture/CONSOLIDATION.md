# Consolidation design

All code now lives under `src/astart/`, with one installable package and one
supported top-level import API. The lexical AST, source editor, semantic
solver, and graph converter are components of this distribution. The graph
converter is internal to `astart.graph` and contributes verified annotation
candidates to `astart.semantic` through `semantic.graph_conversion`.

1. `astart.source.ast` owns Python AST nodes, source comments, shebangs and docstrings.
2. `astart.source.tokens` owns immutable token snapshots and location information.
3. `astart.source.delta` detects source and node-position changes.
4. `astart.source.formatting` preserves original formatting where patches are safe.
5. `astart.docstrings` owns structured documentation AST nodes.
6. `astart.semantic` owns scopes, graph evidence, call contracts, the type
   lattice, abstract values, inference worklists, and mutation invalidation.
7. `astart.graph` supplies deep graph-based annotation inference privately;
   its results do not replace the source AST, public type representation,
   or existing caller-side node identities.

Top-level `Module`, `parse()`, `unparse()` and `convert()` are the supported
entry points. The class also exposes infer/infer_type/signature/bind_call,
without requiring users to import from private graph packages.

No legacy distribution/package names or parallel standalone API entry points
are shipped. Existing functionality is retained through the new namespace,
while legacy import paths are deliberately not provided as aliases.

The graph engine remains a separate **internal algorithmic subsystem**, not
a second public package. Combining all its source code into one giant module
would reduce maintainability and risk breaking stable source or semantic
identities; the shared ABI and type evidence are the consolidation boundary.
