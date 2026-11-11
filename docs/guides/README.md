# Usage and reference

Public APIs, command-line usage, rule authoring and diagnostic reference.

[Documentation index](../README.md)

| Document | Title |
| --- | --- |
| [API.md](API.md) | astart API reference |
| [cache.md](cache.md) | Fix cache |
| [cli.md](cli.md) | CLI reference |
| [refusals.md](refusals.md) | Refusal catalogue — "why wasn't X annotated?" |
| [rule-authoring.md](rule-authoring.md) | Rule authoring kit |
| [skip-codes.md](skip-codes.md) | Skip codes — `SkipCode` |
| [skip-reasons.md](skip-reasons.md) | Skip reasons — `Rejection` |

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`API.md`](API.md) — Use `from astart import ...`. The `astart.semantic` and `astart.graph` trees are implementation modules; the latter is not a separate distribution.
- [`cache.md`](cache.md) — `astart fix --cache` stores each file's fix result on disk so an unchanged file is not fixed twice. Entries live in `.astart_cache/` under the working directory as small JSON files; corrupt or unreadable entries are treated as misses.
- [`cli.md`](cli.md) — `astart` is the command-line entry point (`python -m astart` or the `astart` script). Every command prints help with `-h`/`--help`; the top-level `--version` prints the package version.
- [`refusals.md`](refusals.md) — `astart` refuses rather than guesses. Every skip or refusal uses a closed vocabulary defined in `src/astart/rules/reasons.py`; no fix is ever silently dropped. This catalogue explains each reason, what it means, and what you can do about it.
- [`rule-authoring.md`](rule-authoring.md) — How to add a rule to `astart`. The ontology is declarative: a rule is data (`Rule`, `Fix`, `Profile`, `Relation`) validated by `verify_catalog`, evaluated by `rules/engine.py`, applied by `rules/runner.py`. Design spec: `docs/planning/TODO.md` §11 (M8) and `src/astart/rules/model.py`.
- [`skip-codes.md`](skip-codes.md) — Every value of `SkipCode` in `src/astart/rules/reasons.py` — why the runner did not apply a selected fix. Each line gives the string value and the sentence from the member's docstring.
- [`skip-reasons.md`](skip-reasons.md) — Every value of `Rejection` in `src/astart/rules/reasons.py` — why a type hint was refused. Each line gives the string value and the sentence from the member's docstring.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
