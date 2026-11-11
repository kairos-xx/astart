# Rule authoring kit

How to add a rule to `astart`. The ontology is declarative: a rule is
data (`Rule`, `Fix`, `Profile`, `Relation`) validated by
`verify_catalog`, evaluated by `rules/engine.py`, applied by
`rules/runner.py`. Design spec:
`docs/planning/TODO.md` §11 (M8) and `src/astart/rules/model.py`.

## Anatomy of a rule

`src/astart/rules/model.py::Rule` fields that matter when authoring:

| Field | Purpose |
| --- | --- |
| `key` | Stable slug (`imports.bare-import`), never reused. |
| `code` | Short display id (`IMP001`). |
| `title`, `rationale` | One-line name and the "why". |
| `domain`, `severity`, `maturity`, `owner` | Classification enums in `vocabulary.py`. |
| `subject` | Node kinds the rule inspects (registry-declared). |
| `message` | Template with named `{evidence}` slots. |
| `when` | Declarative `Predicate`, or `None` for procedural. |
| `procedure` | Registered procedure key when `when` is `None`. |
| `requires` | Facts the engine must compute first. |
| `evidence` | `EvidenceSlot`s every finding must provide. |
| `fixes` | `Fix` keys the rule offers. |
| `examples` | Snippets that **are** the rule's tests. |
| `aliases`, `params` | External ids; profile-overridable parameters. |

## Two ways to detect

1. **Declarative** — set `when` to a predicate tree over facts
   (`facts.py` providers compute them lazily). No Python detector needed.
2. **Procedural** — set `procedure` to a key registered in
   `Registries.procedures`, implemented in a standalone module (see
   `rules/procedural.py`, `imports_bare.py`, `docs_missing.py` for the
   `Candidate` shape). **Not yet wired:** `Registries.procedures` is
   empty in the default catalog and `engine.check` never invokes
   `rule.procedure` — see TODO M8-12/M8-22. Until then detectors are
   exercised only by their unit tests.

## Example-as-test

Every `Example(source=..., triggers=...)` is verified by
`verify_catalog`: a `triggers=True` example must produce a finding, a
`False` one must not. Write at least one of each — they run in the
normal suite, so a rule can never ship without coverage.

```python
Example(
    source="import os\n",
    triggers=True,
    note="bare stdlib import",
),
Example(
    source="from os import path\n",
    triggers=False,
    note="already from-imported",
),
```

## Fixes

A `Fix` names an applier key (`appliers.py`) plus `safety`
(`proven`/`guarded`), `min_confidence`, and preconditions. Proven fixes
need no inference; guarded fixes must satisfy the evidence ladder
(`docs/architecture/evidence-ladder.md`) and survive the E6 checker gate. Fixes must
be idempotent — `verify_catalog` checks examples round-trip.

## Fix tests

`tests.support` provides two helpers for gold-case tests:

- `fixed(source=..., settings=...)` runs the guarded fix pipeline on a
  dedented source string and returns the rewritten module.
- `assert_fixed(source=..., expected=..., settings=...)` asserts that a
  dedented fragment appears in that output, raising `AssertionError`
  with the fixed source on failure.

```python
from astart.rules import FixSettings
from astart.rules.vocabulary import FixSafety
from tests.support import assert_fixed

assert_fixed(
    source="def size():\n    return 3\n",
    expected="-> int",
    settings=FixSettings(ceiling=FixSafety.guarded, negotiate=False),
)
```

## Checklist for a new rule

1. Detector: predicate tree or procedure module + unit tests.
2. `Rule` entry in the catalog JSON (`rules/artifacts/catalog/*.json`) with
   examples of both polarities.
3. Optional `Fix` + applier if the rule offers one.
4. `python -m astart.rules.schema` if the model changed (it shouldn't).
5. `verify_catalog` green; `exactus` clean.

Current deferral: the standalone detectors (`IMP001`, `TYP002`,
`SUP001`, `PRS001`, docs/whitespace/constants families) exist with tests
but are **not yet registered** — registration is tracked as M8-22 and
is coordinated with the catalog owner.

## Delegation to ruff (M8-10)

Rules astart must not re-implement — formatting, line length, import
sorting, lint-style rewrites — are declared, not duplicated:

- The rule's `owner` is `"ruff"` (`vocabulary.Owner`); astart reports
  the finding but never applies its own fix for it.
- A `Relation(kind="delegates_to", source=<astart rule>,
  target=<ruff rule>)` records the hand-off, e.g. the planned
  `format.line-length` (FMT001) entry delegates to ruff's line-length
  rules. `verify_catalog` validates that both endpoints exist.
- astart-owned rules keep `owner: "astart"`; `conflicts_with` pairs are
  never enabled in one profile, so a delegated rule and its ruff twin
  cannot double-report under the same profile.

Catalog wiring (the FMT001 entry itself) is part of M8-22 and is
coordinated with the catalog owner; this section is the contract it
implements.
