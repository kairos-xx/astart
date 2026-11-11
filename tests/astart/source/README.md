# `source/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_comment_directives.py`](test_comment_directives.py) — Directive syntax becomes native comment metadata at token construction.
- [`test_format_annotations.py`](test_format_annotations.py) — Add and remove annotations while preserving the surrounding source.
- [`test_format_annotations_corpus.py`](test_format_annotations_corpus.py) — Write inferred annotations back into real modules without losing source.
- [`test_format_ast.py`](test_format_ast.py) — Regression tests for exact and conservative syntax-preserving AST edits.
- [`test_format_edits.py`](test_format_edits.py) — Apply many small AST edits and check source preservation fails closed.
- [`test_format_inline_bodies.py`](test_format_inline_bodies.py) — Inline bodies belong to their statement; real semicolons stay ambiguous.
- [`test_format_list_element_replacement.py`](test_format_list_element_replacement.py) — The writer can swap one element of a child list for an atom.
- [`test_incremental_ast.py`](test_incremental_ast.py) — Regression tests for incremental coordinates and PEP 701 f-string edits.
- [`test_lexical_ast.py`](test_lexical_ast.py) — Regression tests for semantic shebangs and immutable synchronized tokens.
- [`test_perf_budgets.py`](test_perf_budgets.py) — Performance budgets: structural counters first, generous clocks second.
- [`test_structured_nodes.py`](test_structured_nodes.py) — Exercise docstring AST nodes, suppression rules and comment blocks.
- [`test_transactions.py`](test_transactions.py) — Check annotation transaction identity and rollback safety.
- [`test_tree_dump.py`](test_tree_dump.py) — Regression tests for the custom AST JSON exporter.
- [`test_writer_fuzz.py`](test_writer_fuzz.py) — Writer fuzzer: random fix subsets must keep every writer invariant.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
