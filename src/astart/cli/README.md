# `cli/`

Command-line layer over the rule engine and fix runner.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Command-line layer over the rule engine and fix runner.
- [`baseline.py`](baseline.py) — Persist and apply finding baselines.
- [`cache.py`](cache.py) — Persistent content-hash cache for ``astart fix``.
- [`commands.py`](commands.py) — Implement the ``check`` and ``fix`` commands.
- [`config.py`](config.py) — Load the ``\[tool.astart\]`` table of a ``pyproject.toml``.
- [`discovery.py`](discovery.py) — Find the Python files a command should process.
- [`github.py`](github.py) — Render findings as GitHub Actions workflow annotations.
- [`ignores.py`](ignores.py) — Apply a config's per-path selections to reports.
- [`junit.py`](junit.py) — Render findings as a JUnit XML document.
- [`render.py`](render.py) — Render findings as text lines or a JSON document.
- [`sarif.py`](sarif.py) — Render findings as a SARIF 2.1.0 document.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
