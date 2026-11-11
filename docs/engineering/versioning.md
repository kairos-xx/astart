# Versioning policy

`astart` is at `0.1.x`: the public surface is stabilising but not yet
frozen. This document records what is public and how changes to it are
handled before 1.0.

## What is public

- **The `astart` package API** — the names in `astart.__all__`
  (`parse`, `unparse`, `convert`, the AST/docstring/semantic types and
  the `Module` alias). `tests/astart/test_api_surface.py` pins the sorted list;
  adding, removing or renaming a public name fails the suite until the
  snapshot is updated deliberately. Every name in `docs/guides/API.md` must
  resolve — the same test enforces that documentation and code cannot
  drift apart.
- **The `astart` command line** — the subcommands and flags documented
  in [`cli.md`](../guides/cli.md) (`check`, `fix`, `transform`, `convert`,
  `rules`, `explain`, `undo`). `tests/astart/test_readme_flags.py` keeps the
  README and `cli.md` in sync with `--help` output.
- **Machine-readable outputs** — the JSON report shape is defined by
  [`schema/report.json`](../schema/report.json) and
  [`schema/finding.json`](../schema/finding.json); the rules listing by
  [`schema/rules.json`](../schema/rules.json). These schemas are the
  contract for `--format json`, `rules --json` and SARIF consumers.
- **The rule catalog** — rule codes (`TYP001`, …), fix safety levels and
  the `[tool.astart]` configuration keys are user-visible; renaming them
  is a breaking change.

## What is not public

Everything else: `astart._*` modules, `astart.cli.*` internals,
`astart.rules.*` implementation details, `benchmarks/`, `scripts/`, and
any name absent from `__all__`. The negotiation engine, inference
internals and transaction APIs may change without notice.

## Changes before 1.0

- **Additive changes** (new public names, new optional flags, new rule
  codes) ship in minor releases and are documented in `CHANGELOG.md`.
- **Breaking changes** (removed or renamed public names, changed CLI
  semantics, schema-incompatible output) are allowed before 1.0 but must
  be listed under a `Breaking` heading in `CHANGELOG.md` and called out
  in the release notes.
- **Deprecations** — a public name scheduled for removal is kept for at
  least one minor release, documented here and in `CHANGELOG.md`, and
  emits a `DeprecationWarning` where the runtime allows it. After 1.0,
  removals follow the same one-release deprecation window.

## After 1.0

Semantic versioning applies: patch releases fix bugs without changing
the public surface; minor releases add to it; major releases may break
it, with the deprecation window above still applying where practical.
