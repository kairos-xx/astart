# Benchmark artifacts

- [results/](results/): the consolidated `report.json`/`report.md` pair, run
  lifecycle (`@activity.json`) and historical sensor captures.
- [resources/](resources/): input manifests, target definitions and accepted baselines.

Accepted baselines are inputs. Report generation never replaces them unless
an explicit baseline acceptance or update command is used.

<!-- exactus:inventory:start -->
## Directory contents

### Files

No direct files besides this README.

### Subdirectories

- [`resources/`](resources/README.md) — Provide baseline json content.
- [`results/`](results/README.md) — `report.json` and `report.md` are the single consolidated report pair. Every benchmark invocation merges its payload into them: a bare `python -m scripts.benchmark` run records every self-contained tool (`recovery`, `semantic`, `perf`, `targets`), and each named tool replaces or adds its own `tool\[.variant\]` section. The JSON carries the complete machine-readable payload per tool plus shared sensor evidence; the Markdown renders the same data for reading. Sections accumulate across runs until a tool is measured again.

<!-- exactus:inventory:end -->
