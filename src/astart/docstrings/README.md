# Docstrings

This package owns structured documentation behavior:

- `core.py`: documentation nodes, parsing, rendering and symbol links.
- `layout.py`: exact prose preservation around edits.
- `prose.py` and `wrapping.py`: paragraph layout and explicit AST wrapping.
- `protocols.py`: documentation for synthesized structural contracts.
- `types.py`: typed parameter/result/exception field completion.
- `fixes.py`, `edit.py`, `shared.py`: native fixes and legacy field editing.
- `missing*.py`, `stale_params.py`: documentation diagnostics.
- `catalog.json`: documentation rules and fix declarations.

`astart.docstrings` continues exporting the documentation model and parser.
The source module owns attachment/index lifecycle because documentation nodes
are children of its authoritative tree. It calls this package's model and
layout code; there is no separate documentation source tree.

The rule engine loads this package's catalog alongside the generic catalogs,
preserving the previous merge order. Domain fixes do not get imported through
the package facade, which keeps source parsing independent of rule execution.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Structured documentation nodes, parsing, generation and native AST fixes.
- [`core.py`](core.py) — Structured, style-agnostic AST nodes for Python docstrings.
- [`edit.py`](edit.py) — Pure text edits for Google-style docstrings.
- [`fixes.py`](fixes.py) — Docstring facts and fixes: parameters, generator results and whitespace.
- [`layout.py`](layout.py) — Preserve exact documentation prose around native field edits.
- [`missing.py`](missing.py) — DOC001 ``docs.missing-docstring``: definitions without docstrings.
- [`missing_raises.py`](missing_raises.py) — DOC006 ``docs.missing-raises``: raised exception not documented.
- [`missing_returns.py`](missing_returns.py) — DOC004 ``docs.missing-returns``: value-returning function, no section.
- [`prose.py`](prose.py) — Balanced paragraph wrapping with protected documentation and list layout.
- [`protocols.py`](protocols.py) — Describe synthesized structural contracts without inventing behavior.
- [`shared.py`](shared.py) — Shared docstring helpers for the DOC rule family.
- [`stale_params.py`](stale_params.py) — DOC003 ``docs.stale-parameter``: documented name with no parameter.
- [`type_layout.py`](type_layout.py) — Width-aware layout for type expressions inside docstring labels.
- [`types.py`](types.py) — Complete structured documentation from native function annotations.
- [`wrapping.py`](wrapping.py) — Opt-in wrapping through native comment and documentation AST mutations.

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Provide catalog json content.

<!-- exactus:inventory:end -->
