# `cli/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_cli_backup.py`](test_cli_backup.py) — Verify ``fix --backup`` and ``astart undo``.
- [`test_cli_baseline_wiring.py`](test_cli_baseline_wiring.py) — ``astart check --write-baseline``/``--baseline`` wiring (H-03).
- [`test_cli_cache.py`](test_cli_cache.py) — ``astart fix --cache`` skips files whose inputs have not changed.
- [`test_cli_catalog.py`](test_cli_catalog.py) — Verify the ``--version``, ``rules`` and ``explain`` commands.
- [`test_cli_check.py`](test_cli_check.py) — Verify the check command.
- [`test_cli_config.py`](test_cli_config.py) — Tests for the ``\[tool.astart\]`` configuration loader.
- [`test_cli_discovery.py`](test_cli_discovery.py) — Verify file discovery for the command line.
- [`test_cli_exit_codes.py`](test_cli_exit_codes.py) — ``astart fix --check`` reports clean, pending and missing inputs.
- [`test_cli_explain_at.py`](test_cli_explain_at.py) — Verify ``astart explain CODE path:line\[:col\]``.
- [`test_cli_fix.py`](test_cli_fix.py) — Verify the fix command.
- [`test_cli_formats.py`](test_cli_formats.py) — ``check --format json`` emits parseable JSON findings.
- [`test_cli_idempotence_corpus.py`](test_cli_idempotence_corpus.py) — A full fix-and-format run must reach a fixed point on real modules.
- [`test_cli_idempotence_full.py`](test_cli_idempotence_full.py) — M1-14: full-run idempotence beyond the small-file test.
- [`test_cli_main.py`](test_cli_main.py) — Verify command-line wiring.
- [`test_cli_render.py`](test_cli_render.py) — Verify text and JSON rendering of findings.
- [`test_cli_reporters.py`](test_cli_reporters.py) — Verify ``astart check --format`` reaches every reporter.
- [`test_cli_reports.py`](test_cli_reports.py) — Tests for the SARIF, JUnit, GitHub, baseline and ignore reporters.
- [`test_cli_source_root.py`](test_cli_source_root.py) — ``astart fix --source-root`` reaches the type checker.
- [`test_precommit_hook.py`](test_precommit_hook.py) — The pre-commit hook definition exists.
- [`test_report_schema.py`](test_report_schema.py) — Validate real ``astart check --format json`` output against the schemas.
- [`test_review3_fixes.py`](test_review3_fixes.py) — Regression tests for the final review of the check/fix work.
- [`test_settings.py`](test_settings.py) — Public ``Settings``: ``from_pyproject`` and ``to_fix_settings`` (API-04).

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
