# astart check / fix CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the rule engine, fix runner and ruff phase usable on a real project through `astart check PATH...` and `astart fix PATH...`.

**Architecture:** Four small modules under `src/astart/cli/` (discovery, rendering, commands, wiring). They only call the public `astart.rules` API (`check`, `fix_and_format`, `load_default_catalog`, `default_registries`). `__main__.py` keeps `convert` and delegates the two new subcommands.

**Tech Stack:** argparse (already used), `difflib`, `astart.rules`, pytest with `tmp_path`.

**Spec:** `docs/superpowers/specs/2026-11-06-fix-runner-and-type-hints-design.md` (sections 4, 5, 6: "a CLI (next slice)") and `docs/superpowers/specs/2026-11-06-rule-ontology-design.md`.

## Global Constraints

- Python >= 3.13, `from __future__ import annotations`, Google docstrings, keyword-only calls.
- `@final class Constants` with `Final` attributes for module constants; no `Any`/`object` annotations; no suppression comments (`noqa`, `type: ignore`).
- Tests live under `tests/`; do not run Exactus (the user runs it).
- `pyproject.toml` entry point stays `astart = "astart.__main__:main"`; the `convert` subcommand and its tests keep working unchanged.
- ruff is the formatter and runs once, after astart's fixes (`fix_and_format`).

## Review Focus

1. A file that does not parse: reported with its error, other files still processed, exit code 2, never a traceback.
2. Non-UTF-8 source (declared `# coding: latin-1`): round-trips with the same encoding on write.
3. A fix run interrupted or failing must never leave a half-written file: writes are atomic (temp file + replace) and a file is written only if its text changed.
4. Directory walks skip `.git`, `.venv`, `venv`, `__pycache__`, `node_modules`, `build`, `dist`; explicit file arguments are always honoured; missing paths exit 2.
5. `fix --check` and `fix --diff` never modify files; exit status says whether changes are pending.

---

### Task 1: File discovery

**Files:**
- Create: `src/astart/cli/__init__.py` (docstring only), `src/astart/cli/discovery.py`
- Test: `tests/test_cli_discovery.py`

**Interfaces:**
- Produces: `discover_files(*, paths: Sequence[Path]) -> DiscoveryResult` where `DiscoveryResult` is a frozen `@final` dataclass `(files: tuple[Path, ...], missing: tuple[Path, ...])`. `files` sorted, de-duplicated, only `*.py`.

- [ ] **Step 1: Write failing tests** `test_directory_walk_finds_python_files_sorted`, `test_skips_virtualenv_and_cache_directories` (`.venv/x.py`, `__pycache__/y.py`, `node_modules/z.py` absent), `test_explicit_file_honoured_even_in_skipped_dir`, `test_missing_path_reported_not_raised`, `test_duplicate_arguments_collapse`.
- [ ] **Step 2: Run** `pytest tests/test_cli_discovery.py -v`. Expected: FAIL (module missing).
- [ ] **Step 3: Implement** `discover_files` and `Constants.skipped_directories: Final[frozenset[str]]` in `discovery.py`; prune directories while walking (`os.walk` with in-place `dirnames` filtering).
- [ ] **Step 4: Run** the same command. Expected: PASS.

### Task 2: Rendering findings

**Files:**
- Create: `src/astart/cli/render.py`
- Test: `tests/test_cli_render.py`

**Interfaces:**
- Consumes: `Finding`, `Catalog` (`catalog.rules` lookup by key, `Rule.code`, `Rule.message`, `Finding.evidence`, `Finding.span`).
- Produces: `render_message(*, rule: Rule, finding: Finding) -> str` (fills the rule's message template from evidence; the builder checks the template slot syntax in `catalog/*.json` and `engine.py` first); `render_text(*, finding: Finding, catalog: Catalog) -> str` giving `path:line:col: CODE severity message`; `render_json(*, results: Sequence[FileReport]) -> str` (canonical, sorted keys, includes rule key, code, severity, span, message, fingerprint, fix keys); `FileReport` frozen dataclass `(path: str, findings: tuple[Finding, ...], error: str | None)`.

- [ ] **Step 1: Write failing tests** with real findings from `check()` on `def f(x: Any): ...` (TYP001): `test_text_line_has_location_code_and_message`, `test_json_round_trips_and_lists_fix_keys`, `test_json_reports_parse_error_per_file`.
- [ ] **Step 2: Run** `pytest tests/test_cli_render.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the three functions in `render.py`.
- [ ] **Step 4: Run** the same command. Expected: PASS.

### Task 3: `check` command

**Files:**
- Create: `src/astart/cli/commands.py`
- Test: `tests/test_cli_check.py`

**Interfaces:**
- Consumes: Task 1 `discover_files`, Task 2 `render_text`/`render_json`/`FileReport`.
- Produces: `CheckSettings` frozen dataclass `(paths: tuple[Path, ...], output_format: str, fail_on: Severity, stubs_path: Path | None)`; `run_check(*, settings: CheckSettings, out: TextIO) -> int` returning `0` clean, `1` findings at or above `fail_on`, `2` missing path or parse error. Reads files with `tokenize.detect_encoding`. Catalog and registries are loaded once per run.

- [ ] **Step 1: Write failing tests** using `tmp_path` and `io.StringIO`: `test_clean_file_exits_zero`, `test_finding_exits_one_and_prints_location`, `test_fail_on_error_ignores_warnings` (pick a catalog rule whose severity is warning), `test_syntax_error_exits_two_and_continues_with_other_files`, `test_missing_path_exits_two`, `test_latin1_source_is_decoded`, `test_json_format_is_valid_json`.
- [ ] **Step 2: Run** `pytest tests/test_cli_check.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `run_check`; exit code = max over files (2 beats 1 beats 0).
- [ ] **Step 4: Run** the same command. Expected: PASS.

### Task 4: `fix` command

**Files:**
- Modify: `src/astart/cli/commands.py`
- Test: `tests/test_cli_fix.py`

**Interfaces:**
- Consumes: `fix_and_format(source=, target=FormatTarget(filename=, cwd=), catalog=, registries=, settings=FixSettings(ceiling=, stubs_path=))`.
- Produces: `FixCommandSettings` frozen dataclass `(paths, ceiling: FixSafety, stubs_path: Path | None, mode: FixMode, run_formatter: bool)` with `FixMode` a `StrEnum` (`write`, `diff`, `check`); `run_fix(*, settings: FixCommandSettings, out: TextIO) -> int` returning `0` nothing (left) to change, `1` changes written (mode `write`) or pending (`diff`/`check`), `2` errors. Output ends with a summary line `N files changed, M fixes applied, K skipped` and lists skipped fixes with reasons.
- Writes are atomic: write `<name>.astart-tmp` beside the file with the original encoding, then `Path.replace`; skip files whose text is unchanged.

- [ ] **Step 1: Write failing tests**: `test_write_mode_adds_none_return_and_final` (proven ceiling), `test_default_ceiling_does_not_apply_guarded_hints`, `test_guarded_ceiling_adds_inferred_parameter_hint`, `test_diff_mode_prints_unified_diff_and_leaves_file`, `test_check_mode_exits_one_without_writing`, `test_unchanged_file_not_rewritten` (mtime equal), `test_comments_preserved`, `test_latin1_file_keeps_encoding`, `test_unparsable_file_untouched_exit_two`, `test_no_format_flag_skips_ruff` (with `run_formatter=False` output equals astart-only text), `test_second_run_is_noop`.
- [ ] **Step 2: Run** `pytest tests/test_cli_fix.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `run_fix`; `diff` via `difflib.unified_diff`; formatter note (ruff missing) goes to the summary, not a failure.
- [ ] **Step 4: Run** the same command. Expected: PASS.

### Task 5: Wire into `astart`

**Files:**
- Modify: `src/astart/__main__.py`
- Test: `tests/test_cli_main.py`

**Interfaces:**
- Consumes: `run_check`, `run_fix` and their settings.
- Produces: `astart check PATH... [--format text|json] [--fail-on error|warning|info] [--stubs DIR]` and `astart fix PATH... [--guarded] [--diff | --check] [--no-format] [--stubs DIR]`. `convert` unchanged. `main(argv=...)` returns the command's exit code.

- [ ] **Step 1: Write failing tests** calling `main(argv=[...])`: `test_check_subcommand_exit_codes`, `test_fix_subcommand_writes_file`, `test_fix_guarded_flag_raises_ceiling`, `test_diff_and_check_are_mutually_exclusive` (argparse exit 2), `test_convert_still_works` (reuse an existing convert invocation), `test_no_command_prints_help_exit_zero`.
- [ ] **Step 2: Run** `pytest tests/test_cli_main.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the two subparsers and dispatch; keep `_Arguments` typed per command (separate Protocols).
- [ ] **Step 4: Run** `pytest tests/test_cli_main.py tests -q -x` (whole suite). Expected: all pass.

### Task 6: Docs and final validation

**Files:**
- Modify: `src/astart/rules/README.md` (new "Command line" section), `README.md` (usage), spec addendum note in `docs/superpowers/specs/2026-11-06-fix-runner-and-type-hints-design.md` section 6 ("CLI shipped").
- [ ] **Step 1:** Document commands, exit codes, safety ceiling default (`proven`; `--guarded` opt in).
- [ ] **Step 2:** Run `pytest -q` and `ruff check src tests`; Expected: all pass, clean. Smoke-test `python -m astart check src/astart/rules` and `python -m astart fix --diff tests/` on a copy; Expected: no tracebacks.
- [ ] **Step 3:** Hand back to the user to run Exactus.

---

## Self-review

- Spec coverage: the specs list "a CLI" as the next slice; tasks 1-5 cover discovery, check, fix, diff/check modes and the ruff phase; formatter flag covered in Task 4.
- Types: `FileReport`, `CheckSettings`, `FixCommandSettings`, `FixMode` are defined once (Tasks 2-4) and reused in Task 5.
- Proportion: the plan only fixes names, signatures, exit codes and tests.

## Rulings I made (please check)

- Default fix ceiling is `proven`; `--guarded` is the opt-in for inferred hints and added keywords (same convention as ruff's unsafe fixes). Cost if wrong: one flag to flip.
- Exit codes: `0` clean, `1` findings or changes, `2` usage or parse errors.
- `--select/--ignore`, config files, parallelism and watch mode are out of scope (listed for a later slice).
- The CLI package is `astart.cli`, keeping `__main__.py` thin.
