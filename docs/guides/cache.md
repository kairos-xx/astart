# Fix cache

`astart fix --cache` stores each file's fix result on disk so an
unchanged file is not fixed twice. Entries live in `.astart_cache/`
under the working directory as small JSON files; corrupt or unreadable
entries are treated as misses.

## What a cache entry is keyed on

An entry's filename is `sha256` over three inputs:

1. **The tool fingerprint** — a `sha256` over:
   - the *environment string*: every `FixCommandSettings` field except
     `paths`, `mode` and `use_cache` (repr'd, so any settings change
     counts), the checker class name, and `ruff --version`;
   - every `*.py` and `*.json` file inside the `astart` package (the
     code and rule catalog), and
   - the project configuration files `pyproject.toml`, `ruff.toml`,
     `.ruff.toml`, `pyrightconfig.json` and `mypy.ini` found at the
     working directory.
2. **The resolved file path.**
3. **The file's current text.**

Because the fingerprint already contains the astart version's code and
the settings, upgrading the tool, editing the catalog, changing a flag
or touching a config file all invalidate entries automatically — old
keys simply never match again. `Constants.schema` in
`src/astart/cli/cache.py` is an extra layout version; bumping it
invalidates everything at once.

## Clearing the cache

`astart.cli.cache.clear_cache(root=...)` deletes every entry under
`root/.astart_cache/` and returns how many were removed (`0` when no
cache exists). The directory itself is left in place and recreated on
the next store.
