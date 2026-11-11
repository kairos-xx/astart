# CI and pre-commit

`astart` ships two pre-commit hooks and documents the CI steps projects
should run.

## Pre-commit hooks

`.pre-commit-hooks.yaml` defines two hooks for downstream projects:

- `astart-fix` — runs `astart fix --check`; fails the commit when fixes
  are pending.
- `astart-check` — runs `astart check`; fails on findings at or above the
  `--fail-on` threshold.

A consuming `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/<owner>/astart
    rev: v0.1.0
    hooks:
      - id: astart-fix
        args: [--min-confidence, "0.8"]
```

## CI step

Install the package and run the check in CI:

```yaml
- run: pip install astart
- run: astart fix --check --min-confidence 0.8 src
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Clean — nothing to report or change. |
| `1` | `check` found findings at or above `--fail-on`, or `fix --check` would change files. |
| `2` | Usage error — bad arguments, missing paths, or files that cannot be analysed. |
