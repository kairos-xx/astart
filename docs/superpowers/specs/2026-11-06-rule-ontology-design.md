# astart rule ontology — design

Status: **draft for approval** (nothing is built until this is approved).
Date: 2026-11-06.

## 1. Intent

astart becomes an independent check-and-fix tool for Python. It parses each file once into its lossless tree, checks it, applies fixes (including auto type hints and auto keyword arguments), and then runs ruff once as the formatter.

Every check and every fix must be described by **data first**: a rule ontology that is independent of
Exactus, independent of the AST classes, and independent of how a rule is executed. The engine, the CLI, the reports and the docs are all derived from this one model.

Why data first:

- one place defines what a rule means, how severe it is, what it needs, what fixes it, and in which order fixes run;
- the scheduler can read each rule's cost and prerequisites to parse once and compute shared facts once (the speed goal);
- examples in the catalog double as the rule's tests;
- reports can be compared with Exactus through aliases without copying Exactus's design.

## 2. Goals, non-goals, anti-goals

Goals
- A closed, validated vocabulary: domains, severities, fix safety, phases, subjects, facts.
- Rules, fixes, findings, profiles and relations as typed, serializable entities.
- An initial catalog covering everything Exactus checks on Python source today, plus auto type hint and auto keyword fixes.
- Load-time validation of the whole catalog (section 8).

Non-goals
- JS, CSS and HTML rules.
- Replacing ruff formatting, or basedpyright/pyrefly type checking.
- Writing the engine. That is the next document.

Anti-goals (a failure even if it "works")
- Rules that exist only as code with no catalog entry.
- A catalog that imports Exactus or depends on astart's AST classes.
- A fix that can change behaviour but is labelled safe.

## 3. Layers of the model

```
Vocabulary ──► Subjects & Facts ──► Predicates ──► Rule ──► Fix
                                                     │        │
                                                     ▼        ▼
                                                 Finding   Edit plan
                                       Profile ─► selects/parameterises Rules
                                       Relation ─► links Rules/Fixes to each other
```

### 3.1 Vocabulary (closed enums)

| Enum | Members |
| --- | --- |
| `Domain` | `parsing`, `suppression`, `typing`, `calls`, `imports`, `docs`, `oop`, `naming`, `simplification`, `whitespace`, `structure`, `config` |
| `Severity` | `error`, `warning`, `info` |
| `Phase` | `facts` → `check` → `fix` → `format` (ruff) |
| `FixSafety` | `proven` (semantics preserved by construction), `guarded` (applies only above a confidence threshold from inference), `suggest` (shown, never auto-applied), `none` |
| `Owner` | `astart`, `ruff` (recorded so the boundary is explicit) |
| `Maturity` | `experimental`, `stable`, `deprecated` |
| `Cost` | `syntactic`, `scope`, `semantic`, `project` (what a rule needs; drives scheduling) |

### 3.2 Subjects and facts

A **Subject** is what a rule looks at: an AST node kind (`FunctionDef`, `ClassDef`, `Call`, `Assign`, `Import`, `Docstring`, `Comment`, `Shebang`, `BlankLines`, `Module`) or a non-AST subject (`ProjectConfig`).
Node kinds are plain strings validated against a registry at load time, so the model does not import the AST classes.

A **Fact** is a named, typed value a predicate can read, with a provider and a cost. Examples:

| Fact | Type | Cost |
| --- | --- | --- |
| `node.has_annotation` | bool | syntactic |
| `symbol.is_final` / `symbol.scope` | bool / enum | scope |
| `call.resolved_signature` | Signature or none | semantic |
| `call.resolution_confidence` | enum | semantic |
| `type.inferred` + `type.confidence` | type expr + float | semantic |
| `docstring.sections` / `docstring.style` | structured | syntactic |
| `comment.is_suppression` | bool | syntactic |
| `module.parse_ok` | bool | syntactic |
| `class.method_uses_self` / `uses_class` | bool | scope |

### 3.3 Predicates

A predicate is a small expression tree stored as data: `all`, `any`, `not`, `compare(fact, op, value)`, `exists(selector, predicate)`.
This is the "logic-based" part: a rule's trigger can be read, validated, diffed and optimised without running code.

Escape hatch: some rules (docstring validation, call resolution) are too rich for pure predicates.
Such a rule sets `expressible = procedural` and names a `Procedure` key that the engine registers.
The catalog still carries everything else about the rule. Procedural rules are listed so they can be reduced over time.

### 3.4 Rule

```
Rule
  key            stable slug, never reused            e.g. "typing.no-any"
  code           short display id, unique             e.g. "TYP001"
  title, rationale
  domain, severity (default), maturity, owner
  subject        node kind(s) / selector
  when           Predicate | Procedure key
  requires       facts needed (derives the rule's Cost)
  message        template with named evidence slots
  evidence       typed slots the finding must fill
  fixes          Fix keys offered for this rule
  examples       >= 1 bad and >= 1 good snippet (also the rule's tests)
  aliases        external ids, e.g. {"exactus": "CMP002"}
  params         typed, defaulted parameters a profile may override
```

### 3.5 Fix

```
Fix
  key, rules (the rules it resolves)
  safety         FixSafety
  min_confidence for guarded fixes
  edits          ordered edit operations on the tree
  preconditions  Predicate that must still hold when applied
  idempotent     must be true (validated by re-running on the output)
  order          before/after constraints against other fixes
```

Edit operations are tree-level, never text-level: `set_annotation`, `set_keyword`, `insert_node`, `replace_node`, `remove_node`, `move_into_class`, `rewrite_trivia`, `set_docstring`, `remove_blank_lines`.
The lossless tree turns each edit into a minimal source change.

### 3.6 Finding

```
Finding
  rule_key, severity, span (file, start, end), subject ref
  evidence       values for the rule's evidence slots
  fix_offers     [{fix_key, safety, confidence}]
  fingerprint    stable hash of (rule_key, normalized subject path, evidence)
```

The fingerprint is what makes before/after comparison and baselines stable across line moves.

### 3.7 Profile and Relation

- **Profile**: a named set of rule keys with severity overrides, parameter overrides and a fix-safety ceiling (`check`, `fix-safe`, `fix-guarded`). Profiles are data too.
- **Relation** (typed edges): `implies`, `supersedes`, `conflicts_with`, `requires_fact`, `ordered_before`, `delegates_to` (for ruff), `equivalent_to` (for aliases).

## 4. Independence rules

- The ontology package imports nothing from `astart.ast`, `astart.semantic` or `_graph`. It only knows strings for node kinds and fact names, checked against registries the engine supplies at load time.
- Exactus appears only as `aliases` data, never as code.
- Serialization is canonical JSON with a generated JSON Schema, so other tools can read the catalog.

## 5. Initial catalog (mapped from Exactus)

Codes are astart's own. The Exactus id is kept as an alias for report comparison.
"Fix" shows what astart can do beyond reporting.

### Parsing and suppression
| Code | Key | Exactus alias | Cost | Fix |
| --- | --- | --- | --- | --- |
| PRS001 | `parsing.module-does-not-parse` | CMP000, KWARGS parse-failure | syntactic | none |
| SUP001 | `suppression.marker-comment` (noqa, type: ignore, pyright, pyrefly) | CMP001 | syntactic | none (root cause must be fixed) |
| SUP002 | `suppression.lint-ignore-config` | CMP004 | project | none |
| SUP003 | `suppression.type-check-config` | CMP005 | project | none |
| CFG001 | `config.pyproject-missing` | CMP006 | project | suggest |

### Typing
| Code | Key | Exactus alias | Cost | Fix |
| --- | --- | --- | --- | --- |
| TYP001 | `typing.no-any` | CMP002 | syntactic | suggest |
| TYP002 | `typing.no-object-annotation` | CMP003 | syntactic | suggest |
| TYP003 | `typing.missing-annotation` (parameter, return, variable) | KWARGS missing-hint | semantic | **guarded: auto type hint** |
| TYP004 | `typing.uppercase-global-not-final` | PY002 | scope | proven: add `Final` where value is immutable |
| STR001 | `structure.group-constants` (the `@final class Constants`) | group_final | project | proven: group and rewrite references |

### Calls and imports
| Code | Key | Exactus alias | Cost | Fix |
| --- | --- | --- | --- | --- |
| CAL001 | `calls.missing-keyword` | KWARGS missing-kwargs | semantic | **guarded: auto kwargs** (proven when the signature is resolved from the project) |
| CAL002 | `calls.ambiguous-callee` | KWARGS ambiguous-call | semantic | none |
| CAL003 | `calls.unresolved-callee` | KWARGS unresolved-callee | semantic | none |
| IMP001 | `imports.bare-import` | PY001, KWARGS bare-import | scope | proven: explicit import, collision-safe |

### Object-oriented structure and naming
| Code | Key | Exactus alias | Cost | Fix |
| --- | --- | --- | --- | --- |
| OOP001 | `oop.method-should-be-classmethod` | PY004 | scope | guarded |
| OOP002 | `oop.method-should-be-static` | PY005 | scope | guarded |
| OOP003 | `oop.classmethod-should-be-static` | PY006 | scope | guarded |
| OOP004 | `oop.staticmethod-uses-class` | PY007 | scope | guarded |
| NAM001 | `naming.exception-message-variable` (`msg`) | PY003 | scope | proven when control flow is safe |

### Simplification (names are my reading of `python_simplify.py`)
| Code | Key | Exactus alias | Fix |
| --- | --- | --- | --- |
| SIM001 | `simplification.inline-return` | PYS001 | proven |
| SIM002 | `simplification.walrus-in-condition` | PYS002 | proven |
| SIM003 | `simplification.inline-single-use` | PYS003 | proven |
| SIM004 | `simplification.dead-constant-store` | PYS004 | proven |
| SIM005 | `simplification.inline-in-return` | PYS005 | proven |
| SIM006 | `simplification.inline-via-conditional` | PYS006 | proven |

Exactus emits these with "skip" reasons when inlining could reorder evaluation. In the ontology the skip reasons become the fix's `preconditions`.

### Docstrings
| Code | Key | Exactus alias |
| --- | --- | --- |
| DOC001 | `docs.missing-docstring` | DOC001 |
| DOC002 | `docs.missing-parameter` | DOC002 |
| DOC003 | `docs.stale-parameter` | DOC003 |
| DOC004 | `docs.missing-returns` | DOC004 |
| DOC005 | `docs.return-yield-mismatch` | DOC005 |
| DOC006 | `docs.missing-raises` | DOC006 |
| DOC007 | `docs.missing-attribute` | DOC007 |
| DOC008 | `docs.malformed-docstring` | DOC008 |
| DOC009 | `docs.analysis-failure` | DOC009 |
| DOC010 | `docs.missing-description` | DOC010 |
| DOC011 | `docs.stale-raises` | DOC011 |
| DOC012 | `docs.stale-attribute` | DOC012 |
| DOC013 | `docs.format-style` (new: normalise content to Google style) | none |

Fixes: the missing-section rules offer `set_docstring` with a generated entry (guarded by inference confidence); the stale-section rules offer removal (suggest).

### Whitespace and shebang (names are my reading; not verified in Exactus source)
| Code | Key | Fix |
| --- | --- | --- |
| WSP001 | `whitespace.blank-lines` (empty-line normalisation) | proven via `rewrite_trivia`, `remove_blank_lines` |
| WSP002 | `whitespace.trailing-space` | proven |
| SHB001 | `structure.shebang` (missing, malformed, wrong interpreter) | guarded |
| FMT001 | `format.line-length` | `delegates_to` ruff, `Owner = ruff` |

## 6. Phases and ordering

1. **facts**: parse once, compute only the facts that enabled rules require, grouped by `Cost`.
2. **check**: evaluate predicates and procedures; emit findings.
3. **fix** (only in fix mode): apply edit plans ordered by `order` relations, then re-check only the touched nodes, so there is no whole-file loop.
4. **format**: ruff formats the final text once.

The ordering relations the catalog must express include: type hints before docstring generation, `Final` before group-constants, group-constants before bare-import rewriting, and every tree fix before format.

## 7. Questions answered by the model

- "Which rules need project-wide facts?" is a query over `Cost`.
- "What can `fix` change without asking?" is a query over `FixSafety` and the profile ceiling.
- "Which Exactus findings have no astart equivalent?" is a query over aliases.
- "Which rules are still procedural?" is a query over `expressible`.

## 8. Load-time invariants

The loader rejects the catalog when any of these fail:

1. keys and codes are unique; keys never change once released;
2. every referenced node kind, fact, fix, procedure and profile exists;
3. `ordered_before` has no cycles; `conflicts_with` pairs are never in one profile;
4. every rule has at least one bad and one good example, and the bad example triggers exactly that rule;
5. every fix is idempotent when run on its own output;
6. a `proven` fix declares no inference-dependent fact;
7. a rule's `Cost` equals the highest cost among its `requires`;
8. every alias is unique per external system.

## 9. Decisions

Mine (please check):
- Codes are astart's own, with Exactus ids as aliases. This was your open question and is my call.
- Dataclass-style frozen records as the model, canonical JSON as the catalog, JSON Schema generated.
- The catalog lives in its own package (`astart.rules`) and the engine depends on it, never the reverse.
- SIM and WSP/SHB names are inferred from reading Exactus code, not from its docs.

Left to the builder
- Predicate operator set details and the fact registry's exact types.
- The edit-operation catalog's final shape.
- Parameters per rule.

Next after approval: this document is the input to the plan (`writing-plans`). The first slice would be the model and loader with a handful of rules (TYP001, TYP004, CAL001, DOC002) end to end.
