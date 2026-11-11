# `project/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_project_bridge.py`](test_project_bridge.py) — Verify cross-module evidence flowing into the hint engine.
- [`test_project_builder.py`](test_project_builder.py) — Verify project builds: naming, collisions and skipped files.
- [`test_project_index.py`](test_project_index.py) — Verify the whole-project index: call graph, escapes and refresh.
- [`test_project_libraries.py`](test_project_libraries.py) — Verify external signature loading: typeshed, ``py.typed``, stubs.
- [`test_project_m3.py`](test_project_m3.py) — M3 exit gate: whole-project analysis end to end.
- [`test_project_naming.py`](test_project_naming.py) — Verify filesystem-to-module-name mapping.
- [`test_project_scan.py`](test_project_scan.py) — Verify per-module scanning: imports, ``__all__`` and bound names.
- [`test_project_table.py`](test_project_table.py) — Verify cross-module symbol resolution.
- [`test_project_typeshed_client.py`](test_project_typeshed_client.py) — Verify the optional ``typeshed_client`` project-mode backend.
- [`test_project_versions.py`](test_project_versions.py) — Verify Python-version target resolution and syntax gates.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
