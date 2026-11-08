# `scripts/`

Maintenance scripts for astart.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Maintenance scripts for astart.
- [`annotated.py`](annotated.py) — Build an annotated copy of a converted module, for line-by-line review.
- [`conversion_report.py`](conversion_report.py) — Convert an untyped module with astart and report how it differs, in meaning.
- [`evidence.py`](evidence.py) — Collect, from an untyped module, the evidence that leads to a type.
- [`generate_libkw.py`](generate_libkw.py) — Generate ``src/astart/rules/libkw.py`` from typeshed stubs.
- [`generate_rule_docs.py`](generate_rule_docs.py) — Generate ``docs/rules.md`` from the rule catalog.
- [`opacity_report.py`](opacity_report.py) — Explain why nodes of a module stay unknown to the contract negotiator.
- [`pair_wrong.py`](pair_wrong.py) — List the annotations that contradict (or only narrow) the typed twin.
- [`report_layout.py`](report_layout.py) — Layout of the conversion report: standard case blocks, groups, hierarchy.
- [`status_update.py`](status_update.py) — Keep the status ledger in docs/TODO.md up to date.
- [`todo_index.py`](todo_index.py) — Regenerate the dashboard block of ``docs/TODO.md``.
- [`todo_lint.py`](todo_lint.py) — Audit docs/TODO.md: structure, task format, references and generated blocks.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
