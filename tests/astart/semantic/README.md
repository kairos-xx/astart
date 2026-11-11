# `semantic/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_memory_budget.py`](test_memory_budget.py) — Peak-memory budgets for ``fix_source`` on large modules (M7-06).
- [`test_native_symbol_edits.py`](test_native_symbol_edits.py) — Native symbol edits share one graph and preserve reference scopes.
- [`test_semantic_advanced.py`](test_semantic_advanced.py) — Advanced semantic regression tests for statements, scopes and fallbacks.
- [`test_semantic_ast.py`](test_semantic_ast.py) — Semantic integration, identity, CFG, aliasing, and safe inference tests.
- [`test_semantic_bind_calls.py`](test_semantic_bind_calls.py) — Bind many calls with one revision check.
- [`test_semantic_corpus.py`](test_semantic_corpus.py) — Run the semantic analyzer over real-world modules from the corpus.
- [`test_semantic_mutations.py`](test_semantic_mutations.py) — Differential mutation checks against fresh full static analysis.
- [`test_semantic_revisions.py`](test_semantic_revisions.py) — Revision-aware semantic features: roles, edges, provenance and reuse.
- [`test_semantic_worklist.py`](test_semantic_worklist.py) — Differential and deletion-sensitive worklist/regression tests.
- [`test_type_inference.py`](test_type_inference.py) — Regression tests for bidirectional, provenance-carrying type inference.
- [`test_typing_contracts.py`](test_typing_contracts.py) — Regression tests for signatures, overloads, generics and class types.
- [`test_typing_relations.py`](test_typing_relations.py) — Direct, conservative generic/ABC/protocol compatibility regressions.
- [`test_typing_spec_extended.py`](test_typing_spec_extended.py) — Python typing specification refinements for the unified semantic engine.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
