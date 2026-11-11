# `astart.rules`

A rule ontology: rules, fixes, profiles and relations as typed, serializable
data, plus a small reference engine that evaluates the catalog against Python
source parsed once with astart.

Design: `docs/planning/TODO.md` chapter 8 (M8); the ontology spec was merged there and retired.

## Layers

| Module | Role | Depends on the AST? |
| --- | --- | --- |
| `vocabulary` | Closed enums (domain, severity, phase, fix safety, cost, ...) | no |
| `jsonvalue` | `JsonValue` and canonical serialization | no |
| `predicate` | Predicate algebra stored as data | no |
| `model` | `Rule`, `Fix`, `Profile`, `Relation`, `Finding`, `Catalog` | no |
| `registry` | Declared node kinds, facts, procedures, appliers | no |
| `catalog` | Load, dump and validate catalogs (data invariants) | no |
| `schema` | JSON Schema generated from the model (`artifacts/schema.json`) | no |
| `facts`, `appliers`, `engine` | Reference implementation | yes |

`python -m astart.rules.schema` regenerates `artifacts/schema.json`; a test fails when
the committed file is out of date.

## Seeded rules

| Code | Key | Exactus alias | Fix |
| --- | --- | --- | --- |
| TYP001 | `typing.no-any` | CMP002 | none |
| TYP004 | `typing.uppercase-global-not-final` | PY002 | proven: `typing.add-final` |
| CAL001 | `calls.missing-keyword` | KWARGS missing-kwargs | guarded: `calls.add-keywords` |
| DOC002 | `docs.missing-parameter` | DOC002 | none |

## Use

```python
from astart.rules import check, default_registries, load_default_catalog

registries = default_registries()
catalog = load_default_catalog(registries=registries)
result = check(
    source=source,
    filename="module.py",
    catalog=catalog,
    registries=registries,
)
```

`verify_catalog` enforces all eight catalog invariants: the data checks of
`validate_catalog` (uniqueness, references, ordering, conflicts, proven-fix
purity, declared requirements, aliases, both kinds of example) and the
behavioural checks of `validate_behavior` (each bad example triggers exactly
its rule; every offered fix is idempotent). The behavioural half needs the
engine, so plain `load_catalog` / `load_default_catalog` run only the data
checks.

`apply_fix` returns the source unchanged when an edit cannot be written back
without disturbing formatting or comments, and `check` reports parser limits
(for example very deep expressions) through `CheckResult.parse_error`.

## Fixing

```python
from astart.rules import (
    FixSettings, FormatTarget, default_registries, fix_and_format,
    load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

registries = default_registries()
catalog = load_default_catalog(registries=registries)
fixed, formatted = fix_and_format(
    source=source,
    target=FormatTarget(filename="module.py", cwd=project_root),
    catalog=catalog,
    registries=registries,
    settings=FixSettings(ceiling=FixSafety.guarded),
)
```

`fix_source` parses once per pass, applies every selected fix to one tree and
writes once through the format-preserving writer. `FixSafety.proven` applies
only fixes that preserve behaviour by construction; `FixSafety.guarded` also
applies fixes backed by corroborated evidence. Anything skipped is reported
with a reason (`conflict`, `preconditions no longer hold`,
`cannot write back without changing formatting`, an applier error). When a
combined write-back fails, the runner halves the set of fixes and keeps every
one that can be written. Checker failures use `ddmin` instead: test function
groups, then individual edits against the same original source, caching each
subset by stable fix IDs. Minimal failing cores are removed until the
remaining batch passes; removed edits retain explicit refusal codes.
This finds a 1-minimal failure, not a globally smallest failure or the largest
possible accepted batch. `format_source` then runs `ruff format` once.

### Type hints (TYP003)

| Target | Written when |
| --- | --- |
| `-> None` | The body provably returns nothing (not a generator, overload, abstract method or stub) |
| Parameter | Its default literal has that type, or every in-module call site passes that one type, and the inference agrees |
| Return | The syntax proves the type, the inference agrees, and no returned value depends on an untyped parameter |

Never written: anything containing `object` or `Any`, names that are neither
builtins, already imported, nor on the automatic-import list
(`astart.rules.imports`), `*args` / `**kwargs`, `self` / `cls`, a `None`
default, or call sites that disagree.

### Synthesized types and imports

When no concrete hint is corroborated, two further guarded fixes can type a
parameter:

| Fix | Written when |
| --- | --- |
| `typing.synthesize-protocol` | Every use of the parameter is `p.attr` or `p.attr(...)`. A `Protocol` with those members is inserted before the enclosing top-level statement, reused when an identical one exists |
| `typing.synthesize-typevar` | Every use of the parameter is as (an element of) a returned value. `T = TypeVar("T")` is inserted (or reused) and the parameter and return become `T` |

Both refuse rebinding, defaults, attribute writes, `await` through the
parameter, star arguments, dunder attributes and generators. Protocol members
are typed only where the call arguments prove a type; the rest stay
unannotated. Needed imports are added by `insert_import`, merging into an
existing `from typing import ...` line when there is one.

### Command line

`astart check` and `astart fix` (package `astart.cli`) run this engine over
files and directories; see the project README for the flags and exit codes.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Rule ontology: a typed, serializable catalog of checks and fixes.
- [`alias_declarations.py`](alias_declarations.py) — Recognize annotation-only legacy aliases using the native lexical graph.
- [`appliers.py`](appliers.py) — Edit appliers: tree-level rewrites that fixes are made of.
- [`attributes.py`](attributes.py) — Prove the type of ``self.attr`` from every write to it in a class.
- [`call_problems.py`](call_problems.py) — M6-05…M6-08 call-shape detectors.
- [`catalog.py`](catalog.py) — Load, dump and validate rule catalogs.
- [`checker.py`](checker.py) — External type-checker gate: reject fixes that make the checker unhappy.
- [`confidence.py`](confidence.py) — How sure the engine is about each offered fix.
- [`constants_grouping.py`](constants_grouping.py) — M8-09 ``structure.constants-grouping``: loose module constants.
- [`ddmin.py`](ddmin.py) — Deterministic delta debugging over stable change identifiers.
- [`engine.py`](engine.py) — Reference engine: parse once, evaluate rules, report findings.
- [`engine_hints.py`](engine_hints.py) — Annotations from the inference engine, for conversion mode.
- [`environment.py`](environment.py) — Detect where a file lives so a checker can resolve its imports.
- [`facts.py`](facts.py) — Subjects, fact providers and registries for the reference engine.
- [`formatter.py`](formatter.py) — Formatter phase: run ruff once on the final text.
- [`fstring_normalize.py`](fstring_normalize.py) — M8-25 fixer: normalise f-string replacement-field interiors.
- [`grouping.py`](grouping.py) — Place a new ``Final`` constant inside an existing ``Constants`` class.
- [`hints.py`](hints.py) — Corroborated type hints: candidates are accepted only with evidence.
- [`imports.py`](imports.py) — Add the imports a synthesized annotation needs.
- [`imports_bare.py`](imports_bare.py) — IMP001 ``imports.bare-import``: plain ``import mod`` used as ``mod.attr``.
- [`imports_bare_fix.py`](imports_bare_fix.py) — IMP001 fixer: rewrite ``import a`` attribute uses into ``from`` imports.
- [`jsonvalue.py`](jsonvalue.py) — JSON value type and canonical serialization for the rule catalog.
- [`libkw.py`](libkw.py) — Provide libkw py content.
- [`library_calls.py`](library_calls.py) — Bind calls to curated library signatures from ``libkw``.
- [`methods.py`](methods.py) — Resolve method calls that the analyzer does not bind, or binds loosely.
- [`model.py`](model.py) — Entities of the rule ontology and their JSON conversion.
- [`object_annotations.py`](object_annotations.py) — TYP002 ``typing.no-object-annotation``: annotations spelled ``object``.
- [`parse_module.py`](parse_module.py) — PRS001 ``parsing.module-does-not-parse``: a file Python rejects.
- [`predicate.py`](predicate.py) — Predicate algebra: rule triggers expressed as data.
- [`procedural.py`](procedural.py) — Shared shape for standalone rule detectors.
- [`process.py`](process.py) — Run an external command and capture its output.
- [`project_bridge.py`](project_bridge.py) — Feed project-wide call evidence into per-module hint judging.
- [`protocol_verify.py`](protocol_verify.py) — Check a synthesized Protocol against the arguments callers really pass.
- [`protocols.py`](protocols.py) — Derive a structural ``Protocol`` from how a parameter is used.
- [`provable.py`](provable.py) — Return types that follow from the syntax alone.
- [`reasons.py`](reasons.py) — Closed vocabulary of the reasons a fix or hint is not applied.
- [`recovery.py`](recovery.py) — Annotation-recovery benchmark: strip a typed module, fix it, compare.
- [`registry.py`](registry.py) — Registries of node kinds, facts, procedures and appliers.
- [`resolve.py`](resolve.py) — Shared name-binding and call-resolution helpers for rules and hints.
- [`runner.py`](runner.py) — Fix runner: parse once, apply many fixes, write once.
- [`schema.py`](schema.py) — Generate the JSON Schema of the rule catalog from the entity model.
- [`scopes.py`](scopes.py) — Which names a syntax node binds.
- [`slots.py`](slots.py) — Evidence slots: named buckets where sources deposit type claims.
- [`strings_normalize.py`](strings_normalize.py) — String literal normalisation fixer (M8-24, wired by WSP003).
- [`suppressions.py`](suppressions.py) — SUP001 ``suppression.marker-comment``: checker suppression comments.
- [`type_mismatch.py`](type_mismatch.py) — M8-06 detectors: return-type mismatches and incompatible defaults.
- [`typevars.py`](typevars.py) — Detect parameters that only flow through to the return value.
- [`variable_annotations.py`](variable_annotations.py) — TYP005 ``typing.missing-variable-annotation`` detector.
- [`vocabulary.py`](vocabulary.py) — Closed vocabulary of the rule ontology.
- [`whitespace_rules.py`](whitespace_rules.py) — Whitespace rules: WSP001 blank runs through WSP005 string literals.

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Provide schema json content.
- [`negotiation/`](negotiation/README.md) — Two-way type negotiation over a graph of contracts.

<!-- exactus:inventory:end -->

## Native alias declarations

`TYP008` / `typing.use-type-statement` migrates proven module-level legacy
aliases to PEP 695 on targets supporting Python 3.12. It preserves the author's
name and RHS, adds no variable annotation, and consumes unused `TypeAlias`
imports. The per-module cache reuses the native lexical graph; no source
reparse or runtime import is used to detect an alias. Runtime uses, rebinding,
wildcard ambiguity and metadata object uses block migration, including through
dependent aliases. Supported unconstrained legacy generic binders become
explicit native alias parameters. Unsupported type expressions stay unchanged.

Generator result documentation is now a registered rule:
`DOC004` (`docs.missing-generator-results`) and the proven
`docs.add-generator-results` fix. It retains TODO placeholders, distinguishes
yielded values from non-None terminal returns, and preserves supported
structured documentation styles. General non-generator return documentation
remains available through the standalone detector.
