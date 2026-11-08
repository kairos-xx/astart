# `project/`

Whole-project analysis: imports, call graph, libraries and versions.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Whole-project analysis: imports, call graph, libraries and versions.
- [`builder.py`](builder.py) — Build a :class:`ProjectIndex` from source files.
- [`index.py`](index.py) — Whole-project index: definitions, call graph, escapes and exports.
- [`libraries.py`](libraries.py) — External signatures from typeshed, ``py.typed`` and stub packages.
- [`naming.py`](naming.py) — Map filesystem paths to dotted Python module names.
- [`scan.py`](scan.py) — Extract one module's definitions, imports, exports and call records.
- [`table.py`](table.py) — Resolve names across a project's modules.
- [`versions.py`](versions.py) — Python-version awareness for emitted syntax.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
