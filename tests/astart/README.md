# `astart/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_api_surface.py`](test_api_surface.py) — Every name documented in ``docs/guides/API.md`` must resolve.
- [`test_ast_comments.py`](test_ast_comments.py) — Tests for source-preserving comment AST nodes and safe AST rewrites.
- [`test_astart_api.py`](test_astart_api.py) — Validate astart's sole supported public package API.
- [`test_conventions.py`](test_conventions.py) — House rules that must never regress.
- [`test_docs_ci.py`](test_docs_ci.py) — Check the documented pre-commit hooks stay in sync with ci.md.
- [`test_files_api.py`](test_files_api.py) — File-level fix API: ``fix_file``/``fix_paths`` (API-03).
- [`test_no_dynamic_execution.py`](test_no_dynamic_execution.py) — Guard: ``src/astart`` never executes or dynamically loads project code.
- [`test_no_regex.py`](test_no_regex.py) — Guard: no new ``re`` imports in source-reading code (CC-08).
- [`test_readme_flags.py`](test_readme_flags.py) — Check ``astart`` flags are documented in the README and CLI guide.
- [`test_repo_hygiene.py`](test_repo_hygiene.py) — Repository hygiene: no generated paths or oversized files are tracked.

### Subdirectories

- [`cli/`](cli/README.md) — Tests mirroring the corresponding project subsystem.
- [`docstrings/`](docstrings/README.md) — Tests mirroring the corresponding project subsystem.
- [`graph/`](graph/README.md) — Tests mirroring the corresponding project subsystem.
- [`project/`](project/README.md) — Tests mirroring the corresponding project subsystem.
- [`rules/`](rules/README.md) — Tests mirroring the corresponding project subsystem.
- [`semantic/`](semantic/README.md) — Tests mirroring the corresponding project subsystem.
- [`source/`](source/README.md) — Tests mirroring the corresponding project subsystem.
- [`stubs/`](stubs/README.md) — Tests mirroring the corresponding project subsystem.
- [`transforms/`](transforms/README.md) — Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:end -->
