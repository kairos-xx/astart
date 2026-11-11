# Changelog

## Unreleased

- bundled typeshed: astart vendors a typeshed snapshot as package data
  (`astart/stubs/artifacts/typeshed/`, Apache-2.0, licence included);
  `astart.stubs.find_typeshed` no longer scans installed packages or editor
  extensions — an explicit root or `ASTART_TYPESHED` wins, otherwise the
  bundled copy is used, so every machine resolves the same stubs;
  `astart.stubs.bundled_typeshed()` exposes the bundled root;
  `module.convert()`/`astart.convert()` and `astart convert` default to it
  (`--stubs` is now optional), and `--project` mode indexes it automatically;
- `from astart import Settings`: public frozen configuration object with
  `Settings.from_pyproject(path)` (`[tool.astart]` validation via
  `cli/config.py`) and `Settings.to_fix_settings(checker=...)`
  (`astart.settings`);
- `from astart import check_source, fix_source`: public one-call wrappers
  over the rules engine with a process-wide cached catalog (`astart.api`);
- `from astart import fix_file, fix_paths`: file-level fixing API with
  atomic writes and dry-run mode (`astart.files`); `read_source` and
  `write_atomic` moved from `astart.cli` to be shared;
- `astart check --format` accepts `sarif`, `junit` and `github` in
  addition to `text` and `json`;
- `astart fix --backup` journals before-images under
  `.astart-backup/`; `astart undo [RUN_ID]` restores them, skipping files
  edited since the fix;
- `tests.support` provides `fixed`/`assert_fixed` helpers for rule
  authors;
- `astart rules --json` prints the rule catalog as structured JSON
  (`docs/schema/rules.json`);
- `astart explain CODE path:line[:col]` explains the finding at a
  location;
- `docs/engineering/ci.md` documents the pre-commit hooks (`astart-fix`,
  `astart-check`) and CI usage; `.pre-commit-hooks.yaml` gained the
  `astart-check` hook;
- `docs/engineering/security.md` records the threat model; JSON Schemas for the
  check report (`docs/schema/report.json`, `finding.json`) and the rules
  listing (`rules.json`).

## 2026-11-08

- contract negotiation: parameter and return hints are negotiated over a
  graph of contracts by default; `--no-negotiate` turns it off;
- `--annotate-variables` annotates function-local variables whose type the
  evidence proves;
- `--engine` conversion mode takes the inference engine's annotations where
  nothing else decided, still gated by the type checker;
- `astart.stubs`: a typeshed-style stub reader (locate, parse, resolve
  names, version/platform conditions, overload groups);
- library return types flow from curated `libkw` signatures;
- the pair benchmark (`scripts/compare/pair.py`, `fixtures/`) scores the tool
  against author-typed references;
- `scripts/opacity_report.py` reports why nodes stay unannotated.

## 2026-11-07

- attribute annotations and typed `self.x` reads;
- `*args`/`**kwargs` element types from call sites;
- expression defaults and comprehension types;
- locals bound several times to one type;
- checker runs on a temp-dir copy with detected import roots and `--source-root`;
- gated benchmark baseline stored in `scripts/benchmark/artifacts/resources/baseline.json`.
