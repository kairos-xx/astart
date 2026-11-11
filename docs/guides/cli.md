# CLI reference

`astart` is the command-line entry point (`python -m astart` or the
`astart` script). Every command prints help with `-h`/`--help`; the
top-level `--version` prints the package version.

## Commands

| Command | Purpose |
| --- | --- |
| `check` | Report rule violations without changing files. |
| `fix` | Apply fixes, then run `ruff format` once. |
| `transform` | Explicit native AST wrapping and runtime insertion. |
| `convert` | Infer and safely apply source annotations (engine conversion). |
| `rules` | List every catalog rule, sorted by code. |
| `explain` | Explain a rule code: rationale and examples. |
| `undo` | Restore the files of a `fix --backup` run. |

## `astart check`

```console
astart check [-h] [--format {text,json,sarif,junit,github}] \
    [--fail-on {error,warning,info}]
    [--stubs STUBS_DIR] [--project] [--closed-world]
    [--source-root SOURCE_ROOT] [--target-version TARGET_VERSION]
    [--exclude EXCLUDE] [--write-baseline BASELINE]
    [--baseline BASELINE] paths [paths ...]
```

| Flag | Meaning |
| --- | --- |
| `--format {text,json,sarif,junit,github}` | Output format; default `text`. `json` emits the report described in [`schema/report.json`](../schema/report.json); `sarif` a SARIF 2.1.0 document; `junit` a JUnit XML document; `github` GitHub Actions annotation lines. |
| `--fail-on {error,warning,info}` | Least severe finding that makes the exit status non-zero; default `error`. |
| `--stubs STUBS_DIR` | Directory of stub files used as evidence. |
| `--project` | Analyse the discovered files as one project. |
| `--closed-world` | With `--project`, assume all callers are in the file set. |
| `--source-root SOURCE_ROOT` | Directory absolute imports resolve from (repeatable). |
| `--target-version TARGET_VERSION` | Oldest Python version emitted code must run on. |
| `--exclude EXCLUDE` | Skip paths matching this glob during discovery (repeatable). |
| `--write-baseline BASELINE` | Record every current finding (keyed by path and fingerprint) in a JSON baseline file. |
| `--baseline BASELINE` | Suppress findings already recorded in the baseline; exit 0 when nothing new remains. A missing or malformed file exits 2. |

Text output is one line per finding:
`path:line:column: CODE severity message` (columns are 0-based). A file
that cannot be analysed produces `path: error: reason` instead.

## `astart fix`

```console
astart fix [-h] [--safe-only] [--diff | --check] [--no-format]
    [--checker {auto,off}] [--stubs STUBS_DIR]
    [--min-confidence MIN_CONFIDENCE] [--create-constants-class]
    [--stub-docstrings] [--annotate-variables] [--engine] [--no-negotiate]
    [--cache] [--source-root SOURCE_ROOT] [--project] [--closed-world]
    [--target-version TARGET_VERSION] [--exclude EXCLUDE] [--no-docs]
    [--runtime-protocols] [--accept-general]
    [--protocol-placement {module,function,type-checking}] [--backup]
    paths [paths ...]
```

| Flag | Meaning |
| --- | --- |
| `--safe-only` | Apply only provably safe fixes. |
| `--diff` | Print the change instead of writing it. |
| `--check` | Report whether changes are pending without writing. |
| `--no-format` | Skip the final `ruff format` pass. |
| `--checker {auto,off}` | Let an installed pyright veto guarded fixes; default `auto`. |
| `--stubs STUBS_DIR` | Directory of stub files used as evidence. |
| `--min-confidence MIN_CONFIDENCE` | Skip fixes below this confidence (default 0.8, or 0.5 with `--engine`; 0 also writes int/str annotations taken from a literal default alone). |
| `--create-constants-class` | Create a `Constants` class when a module has none. |
| `--stub-docstrings` | Add a stub docstring to undocumented public definitions. |
| `--annotate-variables` | Annotate function-local variables the evidence proves. |
| `--engine` | Conversion mode: also take the inference engine's own annotations where nothing else decided. |
| `--no-negotiate` | Do not use contract negotiation for parameter and return hints. |
| `--cache` | Reuse results for unchanged files (stored in `.astart_cache`). |
| `--source-root SOURCE_ROOT` | Directory the type checker resolves imports from (repeatable). |
| `--project` | Analyse the discovered files as one project. |
| `--closed-world` | With `--project`, assume all callers are in the file set. |
| `--target-version TARGET_VERSION` | Oldest Python version emitted code must run on. |
| `--exclude EXCLUDE` | Skip paths matching this glob during discovery (repeatable). |
| `--no-docs` | Skip `docs.*` fixes, applying typing and structure fixes only. |
| `--runtime-protocols` | Emit `@runtime_checkable` on synthesized protocols used under `isinstance`. |
| `--accept-general` | Prefer abstract collection types over synthesized protocols for read-only container parameters. |
| `--protocol-placement {module,function,type-checking}` | Where synthesized protocols land; default `module`. |
| `--optimize-aliases` / `--no-optimize-aliases` | Extract repeated type patterns as PEP 695 `type` aliases after the fixes settle; default enabled, skipped for targets below Python 3.12. |
| `--backup` | Save before-images under `.astart-backup/<run-id>/` for `astart undo`. |

Per-file failures print `path: error: reason`; the run ends with a
summary line `N files changed, M fixes applied, K skipped`.

## `astart transform`

```console
astart transform [-h] [-o TRANSFORM_OUTPUT | --diff | --check]
    [--report TRANSFORM_REPORT] [--wrap] [--replace-print]
    [--optimize-aliases] [--alias-min-savings N] [--alias-max-plans N]
    [--magic-scope {off,module,function,class}]
    [--doc-style {preserve,google,numpy,rest,epytext}]
    [--line-length LINE_LENGTH] [--boilerplate] [--remove-pass]
    [--add-return-none] [--strip-sections] SOURCE
```

| Flag | Meaning |
| --- | --- |
| `-o`, `--output TRANSFORM_OUTPUT` | Write the transformed source here; default stdout. Mutually exclusive with `--diff`/`--check`. |
| `--diff` | Print the change instead of writing. |
| `--check` | Report whether edits are pending; exit 1 when they are. |
| `--report TRANSFORM_REPORT` | Write a JSON change report to this path. |
| `--wrap` | Reflow native documentation and comment nodes. |
| `--replace-print` | Inject a native helper for builtin `print` calls. |
| `--optimize-aliases` / `--no-optimize-aliases` | Extract and reuse type aliases on the native AST; on by default. |
| `--alias-min-savings N` | Minimum canonical source characters saved, including declaration overhead; default 8. |
| `--alias-max-plans N` | Maximum complete alias plans evaluated; default 512. |
| `--magic-scope {off,module,function,class}` | Scope for magic-value extraction. |
| `--doc-style {preserve,google,numpy,rest,epytext}` | Docstring style to emit. |
| `--line-length LINE_LENGTH` | Target line length for reflowed text. |
| `--boilerplate` | Add boilerplate sections. |
| `--remove-pass` | Remove `pass` statements made redundant. |
| `--add-return-none` | Add explicit `-> None` where inferred. |
| `--strip-sections` | Strip docstring sections. |

## `astart convert`

```console
astart convert [-h] --source SOURCE --stubs STUBS --output OUTPUT
    [--report REPORT] [--dry-run] [--strict-formatting]
```

| Flag | Meaning |
| --- | --- |
| `--source SOURCE` | Input Python file. |
| `--stubs STUBS` | Stubs directory used as inference evidence. |
| `--output OUTPUT` | Destination for the converted source. |
| `--report REPORT` | Write a JSON report of proposals, stages, skips and warnings. |
| `--dry-run` | Compute proposals without writing `--output`. |
| `--strict-formatting` | Raise on formatting conflicts instead of falling back. |

## `astart rules`

```console
astart rules [-h] [--json]
```

Prints every catalog rule as `CODE  key  severity  title`, sorted by code.
`--json` emits the machine-readable listing described in
[`schema/rules.json`](../schema/rules.json) instead: one object per rule with
`code`, `key`, `title`, `maturity`, `severity` and `fixes` (each fix's
`key` and `safety`). Always exits 0.

## `astart explain`

```console
astart explain [-h] code [location]
```

Without `location`, prints the rule's code, key, title, rationale and
flagged/clean examples. With `location` (`path:line[:col]`), checks that
one file and prints the rule header plus each matching finding's message
and evidence; exits `1` when nothing matches there. An unknown code
prints `astart: unknown rule code: CODE` on stderr; a malformed location
prints `astart: bad location`.

## `astart undo`

```console
astart undo [-h] [run_id]
```

Restores every file recorded by a `fix --backup` run. With no `run_id`
the newest directory under `.astart-backup/` is used. A file edited
after the fix is skipped (`skipped (edited since): path`) and the command
exits `1`; exit `2` when no matching run exists.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success: no findings at or above `--fail-on` (`check`), nothing to change (`fix`, `transform`), or the command completed (`convert`, `rules`, `explain`). |
| `1` | Findings reached the threshold (`check`), or changes were applied or are pending (`fix`, `transform --check`). |
| `2` | Usage error: argparse rejected the invocation, a path is missing or a file cannot be analysed (`check`, `fix`), or `explain` got an unknown rule code. |

## Error line formats

- Per-file analysis failure: `path: error: reason` on stdout (`check`,
  `fix`); the same entry appears as `"error"` in the JSON report.
- Unknown explain code: `astart: unknown rule code: CODE` on stderr.
- Argparse errors (unknown command or flag, missing required option):
  usage on stderr, exit 2.

### Typed docstrings

`astart fix --docstring-types` is enabled by default. It completes existing
structured docstrings from function annotations, retaining descriptions and
using `TODO.` for new entries. `--no-docstring-types` retains the previous
untyped documentation policy. `--stub-docstrings` separately enables creation
of docstrings for undocumented public definitions.

Parameters use `name (Type): description`. Generator and async generator
`Yields` entries use the yielded element type, while a generator's terminal
`Returns` entry uses its return component. Explicit raised exceptions appear
under `Raises`; a function annotated `NoReturn` that only raises has no
`Returns` entry. Nested definitions own their exceptions and yielded values.

The pair benchmark also supports `--checker-delta` and `--checker-gate`;
these are benchmark options, documented in [benchmarks](../analysis/benchmarks.md).
