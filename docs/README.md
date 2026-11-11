# Documentation

Use `from astart import ...` for the supported public API. Internal semantic
and graph modules are implementation details.

| Topic | Contents |
| --- | --- |
| [Planning and status](planning/README.md) | Active tasks, completed work and the machine-readable progress ledger. |
| [Architecture and inference](architecture/README.md) | System structure, the shared AST, inference evidence and generated naming contracts. |
| [Usage and reference](guides/README.md) | Public APIs, command-line usage, rule authoring and diagnostic reference. |
| [Engineering](engineering/README.md) | Continuous integration, security and compatibility policies. |
| [Analysis and benchmarks](analysis/README.md) | Measured conversion behavior, inference gaps and legacy-project assessments. |
| [JSON schemas](schema/README.md) | Finding, report and rule schemas. |
| [Design plans](superpowers/README.md) | Existing specifications, plans and roadmaps. |

Start with the [API guide](guides/API.md), [CLI guide](guides/cli.md), or
[active backlog](planning/TODO.md).

Generated conversion evidence is maintained by `python -m scripts.compare`:

- [Comparison report](../scripts/compare/artifacts/results/conversion-report.md)
- [Machine-readable comparison](../scripts/compare/artifacts/results/conversion-report.json)

<!-- exactus:inventory:start -->
## Directory contents

### Files

No direct files besides this README.

### Subdirectories

- [`analysis/`](analysis/README.md) — Measured conversion behavior, inference gaps and legacy-project assessments.
- [`architecture/`](architecture/README.md) — System structure, the shared AST, inference evidence and generated naming contracts.
- [`engineering/`](engineering/README.md) — Continuous integration, security and compatibility policies.
- [`guides/`](guides/README.md) — Public APIs, command-line usage, rule authoring and diagnostic reference.
- [`planning/`](planning/README.md) — Active tasks, completed work and the machine-readable progress ledger.
- [`schema/`](schema/README.md) — Provide finding json content.
- [`superpowers/`](superpowers/README.md) — > **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- \\\[ \\\]`) syntax for tracking.

<!-- exactus:inventory:end -->
