# `astart/`

Astart: mutable Python AST, preserved source, semantic analysis and typing.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Astart: mutable Python AST, preserved source, semantic analysis and typing.
- [`__main__.py`](__main__.py) — Single command-line entry point using the astart Python API.
- [`ast.py`](ast.py) — Python AST extensions that preserve tokenizer comments across edits.
- [`delta.py`](delta.py) — Identity-aware incremental source-map reconciliation for Python ASTs.
- [`docstrings.py`](docstrings.py) — Structured, style-agnostic AST nodes for Python docstrings.
- [`formatting.py`](formatting.py) — Conservative, source-slice-preserving editor for mutable Python ASTs.
- [`node_attributes.py`](node_attributes.py) — Typed access to attributes that Astart attaches to ``ast`` nodes.
- [`py.typed`](py.typed) — Provide py typed content.
- [`tokens.py`](tokens.py) — Immutable lexical snapshots for mutable, comment-aware Python AST nodes.

### Subdirectories

- [`_graph/`](_graph/README.md) — API-first AST graph inference package.
- [`cli/`](cli/README.md) — Command-line layer over the rule engine and fix runner.
- [`rules/`](rules/README.md) — A rule ontology: rules, fixes, profiles and relations as typed, serializable data, plus a small reference engine that evaluates the catalog against Python source parsed once with astart.
- [`semantic/`](semantic/README.md) — Dependency-free semantic graph and safe abstract evaluation for Python ASTs.

<!-- exactus:inventory:end -->
