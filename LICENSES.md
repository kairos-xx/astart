# Licences and attribution

`astart` itself is MIT licensed (see `LICENSE`). This file records the
third-party material the project uses or is inspired by.

## typeshed stub data

- **Source:** [python/typeshed](https://github.com/python/typeshed) —
  Apache License 2.0 (CPython-derived portions under the PSF license);
  the licence text ships at `astart/stubs/artifacts/typeshed/LICENSE`.
- **Used by:** astart vendors a typeshed snapshot as package data under
  `astart/stubs/artifacts/typeshed/` (`stdlib/`, `stubs/`, `stdlib/VERSIONS`).
  `astart.stubs` reads it by default — `find_typeshed` honours an
  explicit directory and `ASTART_TYPESHED` first, then falls back to the
  bundled copy; it never scans other installed packages or editor
  extensions, so every machine resolves the same stubs. The
  `stdlib/VERSIONS` module-lifetime table is taken from the typeshed
  snapshot bundled with basedpyright (commit `a564787`).
  `scripts/utils/generate_libkw.py` generates the `rules/libkw.py`
  `SIGNATURES` table from typeshed data at development time.

## `typeshed_client` (third-party package)

- `astart.stubs` re-implements the *ideas* of the `typeshed_client` stub
  finder — stub lookup, version and platform conditions, overload groups,
  `__all__`, re-exports and name resolution across files — in original
  code, so astart needs no such dependency. Each `stubs/` module docstring
  names the origin.
- `astart.project.typeshed_client` optionally delegates to the real
  `typeshed_client` package *when the user has it installed*, gated by the
  `ASTART_TYPESHED_CLIENT` environment variable; it is imported lazily and
  is never required.

## External benchmark corpus (`tests/corpus/extended`)

- 25 PyPI distributions pinned by SHA-256 in `MANIFEST.json`; each
  distribution's licence text lives in `tests/corpus/extended/LICENSES/<name>.txt`
  (mostly MIT, Apache-2.0 and BSD — see each file for terms).
- Distributions: anyio, arrow, cattrs, click, fastapi, filelock, flask,
  h11, httpcore, httpx, humanize, itsdangerous, jinja2, markdown-it-py,
  packaging, platformdirs, pluggy, pytest, rich, starlette, structlog,
  tenacity, tomli, tomlkit, werkzeug.
- The corpus is test data for the recovery benchmarks; it is not shipped
  as part of the astart package.
