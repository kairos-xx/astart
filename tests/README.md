# `tests/`

Tests for source-preserving comment AST nodes and safe AST rewrites.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Astart regression tests and typed expectation helpers.
- [`conftest.py`](conftest.py) — Pytest hooks shared by the whole suite.

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Provide regex allowlist txt content.
- [`astart/`](astart/README.md) — Tests mirroring the corresponding project subsystem.
- [`corpus/`](corpus/README.md) — These `.py` files are test data, not imported application modules. Lint and Exactus exclusions apply to this entire directory.
- [`scripts/`](scripts/README.md) — Tests mirroring the corresponding project subsystem.
- [`support/`](support/README.md) — Shared test-authoring support, outside the installed runtime package.

<!-- exactus:inventory:end -->
