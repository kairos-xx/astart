# Rule Ontology First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `astart.rules` package (typed model, vocabulary, predicate algebra, JSON catalog loader with the eight invariants, generated JSON Schema) and seed it with four rules that run end to end: TYP001, TYP004, CAL001, DOC002.

**Architecture:** A model layer that imports nothing from `astart.ast`, `astart.semantic` or `_graph` (rules and node kinds are strings). A separate small reference engine in the same package supplies fact providers backed by `astart.parse` and `module.bind_call`, checks the examples, and applies the two fixes. The catalog is canonical JSON under `src/astart/rules/catalog/`.

**Tech Stack:** Python 3.13, frozen `slots` dataclasses, PEP 695 `type` aliases, stdlib `json`/`hashlib`, pytest, existing `tests.expectations` helpers.

**Spec:** `docs/superpowers/specs/2026-11-06-rule-ontology-design.md`

## Global Constraints

- `requires-python >=3.13`; `from __future__ import annotations` in every module.
- Keyword-only calls everywhere (`def f(*, a: int)`); callers always pass keywords.
- Google-style docstrings with Args/Returns/Raises/Attributes.
- Module-level constants live in a `@final class Constants` with `Final` attributes.
- No `Any`, no `object` annotations, no suppression comments (`noqa`, `type: ignore`, pyright/pyrefly pragmas).
- Everything under `astart.rules.model`, `vocabulary`, `predicate`, `registry`, `catalog`, `schema` must not import `astart.ast`, `astart.semantic` or `astart._graph`. Only `astart.rules.engine` and `astart.rules.facts` may.
- Codes and keys are astart's own; Exactus ids appear only as `aliases` data.
- Coverage gates: at least 90% total and 80% per file. Branch coverage is on.
- Do not run Exactus. Validate with `python -m pytest`, `ruff check`, `ruff format --check` and `basedpyright`.
- The repo is not under version control, so each task ends with a checkpoint run instead of a commit.

## Review Focus

1. A catalog with zero rules, or rules with no fixes, loads and round-trips (`dump(load(text)) == text`).
2. Source that does not parse: `check` returns a result with `parse_error` set and no findings; it never raises.
3. Fingerprints survive code moving (blank lines added above) and differ for different evidence.
4. Aliased imports: `import typing as t` / `from typing import Any as A` count for TYP001; an existing `Final` alias is reused by the TYP004 fix.
5. CAL001 never proposes keywords for positional-only parameters or for arguments absorbed by `*args`; DOC002 ignores `self`/`cls` and accepts `*args`/`**kwargs` entries.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `src/astart/rules/__init__.py` | Public re-exports only |
| `src/astart/rules/vocabulary.py` | Closed enums |
| `src/astart/rules/jsonvalue.py` | `JsonValue` alias and canonical `dumps` |
| `src/astart/rules/predicate.py` | Predicate algebra, JSON round trip, evaluation over a fact mapping |
| `src/astart/rules/model.py` | `Rule`, `Fix`, `Example`, `EvidenceSlot`, `Profile`, `Relation`, `Span`, `Finding`, `Catalog` |
| `src/astart/rules/registry.py` | `FactSpec`, `Registries` (node kinds, facts, procedures, appliers) |
| `src/astart/rules/catalog.py` | `load_catalog`, `dump_catalog`, `validate_catalog`, `CatalogError` |
| `src/astart/rules/schema.py` | `catalog_schema()` generated from the model |
| `src/astart/rules/facts.py` | Fact providers and default `Registries` for this slice |
| `src/astart/rules/engine.py` | `check`, `CheckResult`, `apply_fix`, `validate_behavior` |
| `src/astart/rules/catalog/*.json`, `schema.json` | Seed data and committed schema |
| `tests/test_rules_*.py` | One test module per source module |

---

### Task 1: Vocabulary and package skeleton

**Files:**
- Create: `src/astart/rules/__init__.py`, `vocabulary.py`, `jsonvalue.py`
- Modify: `pyproject.toml` (`package-data`: add `rules/catalog/*.json`, `rules/schema.json`)
- Test: `tests/test_rules_vocabulary.py`

**Interfaces:**
- Produces: `StrEnum`s `Domain`, `Severity`, `Phase`, `FixSafety`, `Owner`, `Maturity`, `Cost`, `Expressible` with exactly the members in spec section 3.1 (`Expressible`: `declarative`, `procedural`). `Cost` is ordered: `Cost.rank(self) -> int` (syntactic 0, scope 1, semantic 2, project 3). `type JsonValue`; `def canonical_dumps(*, value: JsonValue) -> str` (sorted keys, 2-space indent, trailing newline, `ensure_ascii=False`).

- [ ] **Step 1: Write failing tests** `test_cost_rank_orders_levels` (syntactic < scope < semantic < project), `test_enum_members_match_spec` (member value sets equal the spec table), `test_canonical_dumps_sorts_keys_and_ends_with_newline`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_vocabulary.py -v`. Expected: FAIL (import error).
- [ ] **Step 3: Implement** the three modules with the signatures above; `Phase` members `facts, check, fix, format`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q` still green.

### Task 2: Predicate algebra

**Files:**
- Create: `src/astart/rules/predicate.py`
- Test: `tests/test_rules_predicate.py`

**Interfaces:**
- Consumes: `JsonValue` (Task 1).
- Produces: frozen dataclasses `AllOf(items: tuple[Predicate, ...])`, `AnyOf(items)`, `Not(item)`, `Compare(fact: str, op: CompareOp, value: FactValue)`, `Exists(selector: str, where: Predicate)`; `type Predicate = AllOf | AnyOf | Not | Compare | Exists`; `type FactValue = str | int | float | bool | None`; `CompareOp` StrEnum `eq, ne, lt, le, gt, ge`.
  `def predicate_to_json(*, predicate: Predicate) -> JsonValue`, `def predicate_from_json(*, value: JsonValue) -> Predicate` (shape `{"op":"all","of":[...]}`, `{"op":"compare","fact":..,"cmp":..,"value":..}`, `{"op":"exists","selector":..,"where":..}`; raises `ValueError` naming the bad key), `def predicate_facts(*, predicate: Predicate) -> frozenset[str]`, `def evaluate(*, predicate: Predicate, facts: Mapping[str, FactValue]) -> bool` (missing fact raises `KeyError`; `Exists` is not evaluable here and raises `NotImplementedError` with the selector in the message, the engine handles it).

- [ ] **Step 1: Write failing tests** `test_round_trip_every_node_kind`, `test_evaluate_all_any_not_compare` (a truth table over two bool facts), `test_ordering_ops_on_ints`, `test_missing_fact_raises_key_error`, `test_from_json_rejects_unknown_op`, `test_predicate_facts_collects_nested_names`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_predicate.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the signatures above.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 3: Entity model with JSON round trip

**Files:**
- Create: `src/astart/rules/model.py`
- Test: `tests/test_rules_model.py`

**Interfaces:**
- Consumes: vocabulary enums, `Predicate`, `predicate_to_json/from_json`, `JsonValue`.
- Produces (all frozen `slots` dataclasses, tuples not lists):
  - `EvidenceSlot(name: str, type: str)`
  - `Example(source: str, triggers: bool, note: str = "")`
  - `Rule(key, code, title, rationale, domain, severity, maturity, owner, subject: tuple[str, ...], when: Predicate | None, procedure: str | None, requires: tuple[str, ...], message: str, evidence: tuple[EvidenceSlot, ...], fixes: tuple[str, ...], examples: tuple[Example, ...], aliases: Mapping[str, str], params: Mapping[str, FactValue])` with `expressible` derived (`procedural` iff `procedure` is set); exactly one of `when`/`procedure` must be set (`ValueError` in `__post_init__`).
  - `Fix(key, rules: tuple[str, ...], safety: FixSafety, min_confidence: float, edits: tuple[str, ...], preconditions: Predicate | None, idempotent: bool, before: tuple[str, ...], after: tuple[str, ...])`
  - `Profile(key, rules: tuple[str, ...], severities: Mapping[str, Severity], params: Mapping[str, FactValue], safety_ceiling: FixSafety)`
  - `Relation(kind: RelationKind, source: str, target: str)` with `RelationKind` StrEnum `implies, supersedes, conflicts_with, requires_fact, ordered_before, delegates_to, equivalent_to`
  - `Span(file: str, start_line: int, start_column: int, end_line: int, end_column: int)`
  - `Finding(rule_key, severity, span, subject_path: str, evidence: Mapping[str, JsonValue], fix_offers: tuple[FixOffer, ...], fingerprint: str)` and `FixOffer(fix_key: str, safety: FixSafety, confidence: float)`
  - `Catalog(rules, fixes, profiles, relations)` (tuples) with `rule(key: str) -> Rule`, `fix(key: str) -> Fix` raising `KeyError`.
  - `def to_json(*, item: Rule | Fix | Profile | Relation | Catalog) -> JsonValue` and `def from_json(*, kind: type[T], value: JsonValue) -> T` (generic `T`), `def make_fingerprint(*, rule_key: str, subject_path: str, evidence: Mapping[str, JsonValue]) -> str` = first 16 hex chars of sha256 over the canonical JSON of the three inputs.

- [ ] **Step 1: Write failing tests** `test_rule_requires_exactly_one_trigger`, `test_rule_expressible_is_derived`, `test_catalog_round_trip_every_entity`, `test_catalog_lookup_unknown_key_raises`, `test_fingerprint_is_stable_and_evidence_sensitive` (same inputs equal; different evidence differs; line numbers are not an input).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_model.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the entities and converters; key order in JSON is fixed by `canonical_dumps`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 4: Registries

**Files:**
- Create: `src/astart/rules/registry.py`
- Test: `tests/test_rules_registry.py`

**Interfaces:**
- Consumes: `Cost`, `FactValue`.
- Produces: `FactSpec(name: str, value_type: str, cost: Cost)` (`value_type` one of `bool, int, float, str`); `Registries(node_kinds: frozenset[str], facts: Mapping[str, FactSpec], procedures: frozenset[str], appliers: frozenset[str])` with `fact(name: str) -> FactSpec` (`KeyError` message lists known names) and `def rule_cost(*, registries: Registries, requires: Iterable[str]) -> Cost` (highest rank, `Cost.syntactic` for empty).

- [ ] **Step 1: Write failing tests** `test_rule_cost_is_highest_required_fact`, `test_rule_cost_defaults_to_syntactic`, `test_unknown_fact_lists_known_names`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_registry.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** per the signatures.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 5: Catalog loader and data invariants

**Files:**
- Create: `src/astart/rules/catalog.py`
- Test: `tests/test_rules_catalog.py`

**Interfaces:**
- Consumes: `Catalog` and entities (Task 3), `Registries` and `rule_cost` (Task 4), `predicate_facts`.
- Produces: `class CatalogError(ValueError)` carrying `problems: tuple[str, ...]`; `def load_catalog(*, text: str, registries: Registries) -> Catalog` (parse, build, then `validate_catalog`); `def dump_catalog(*, catalog: Catalog) -> str` (canonical); `def validate_catalog(*, catalog: Catalog, registries: Registries) -> None` enforcing spec section 8 invariants 1, 2, 3, 6, 7, 8 and collecting all problems before raising. (Invariants 4 and 5 are Task 9.)
  Invariant details: (1) keys and codes unique across rules; fix keys unique. (2) every subject in `registries.node_kinds`, every fact in `requires` and in predicates in `registries.facts`, every `procedure` in `registries.procedures`, every fix named by a rule in the catalog, every `edits` entry in `registries.appliers`, every profile rule exists. (3) `ordered_before` relations acyclic; no profile contains both ends of a `conflicts_with`. (6) a fix with `safety == proven` has no precondition fact above `Cost.scope`. (7) for a declarative rule, `requires` must equal `predicate_facts(when)`, so its cost (`rule_cost(requires)`) is the highest cost among the facts it reads; procedural rules are exempt. (8) aliases unique per external system.

- [ ] **Step 1: Write failing tests** one per invariant using a small in-memory `Registries`: `test_duplicate_code_is_reported`, `test_unknown_subject_is_reported`, `test_unknown_fact_is_reported`, `test_ordered_before_cycle_is_reported`, `test_conflicting_rules_in_one_profile_are_reported`, `test_proven_fix_cannot_need_semantic_fact`, `test_declared_cost_must_match_predicate_facts`, `test_duplicate_alias_per_system_is_reported`, `test_all_problems_are_collected_in_one_error`, `test_empty_catalog_round_trips` (Review Focus 1), `test_dump_load_is_idempotent`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_catalog.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the four functions. Cycle detection: depth-first search over `ordered_before` edges.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 6: Generated JSON Schema

**Files:**
- Create: `src/astart/rules/schema.py`, `src/astart/rules/schema.json` (generated)
- Test: `tests/test_rules_schema.py`

**Interfaces:**
- Produces: `def catalog_schema() -> JsonValue` (draft 2020-12 object describing `Catalog`, built by walking the dataclass fields of Task 3, not hand-written) and `def schema_text() -> str` (canonical dumps). `python -m astart.rules.schema` writes `schema.json`.

- [ ] **Step 1: Write failing tests** `test_schema_lists_every_entity_field` (each dataclass field name appears in the matching definition), `test_committed_schema_matches_generated` (reads `schema.json` through `importlib.resources`, compares to `schema_text()`), `test_rule_requires_documented_enums` (the `severity` property enumerates the `Severity` values).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_schema.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** field-walking via `dataclasses.fields` and `typing.get_type_hints`, mapping enums to `enum`, tuples to `array`, mappings to `object`.
- [ ] **Step 4: Generate** `schema.json` with `python -m astart.rules.schema`, then run the test command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 7: Reference engine and the syntactic and scope facts

**Files:**
- Create: `src/astart/rules/facts.py`, `src/astart/rules/engine.py`
- Test: `tests/test_rules_engine.py`

**Interfaces:**
- Consumes: model, registry, `evaluate`, `astart.parse(*, source, filename)`.
- Produces:
  - `facts.py`: `def default_registries() -> Registries` declaring node kinds `Module, FunctionDef, AsyncFunctionDef, ClassDef, Assign, AnnAssign, Call, Annotation` (`Annotation` is the virtual kind for every annotation expression of arguments, returns and `AnnAssign`) and these facts (name: type, cost): `annotation.uses_typing_any`: bool, scope; `binding.is_module_global`: bool, syntactic; `binding.name_is_uppercase`: bool, syntactic; `binding.is_final`: bool, scope; `binding.value_is_immutable_literal`: bool, syntactic; `call.positional_keyword_candidates`: int, semantic; `call.is_resolved_in_module`: bool, semantic; `function.has_docstring`: bool, syntactic; `function.undocumented_parameter_count`: int, syntactic.
  - `engine.py`: `CheckResult(findings: tuple[Finding, ...], parse_error: str | None)`; `def check(*, source: str, filename: str, catalog: Catalog, registries: Registries) -> CheckResult` (parse once, for each rule iterate subjects of its `subject` kinds, compute only the facts in `predicate_facts(rule.when)`, evaluate, build `Finding` with message-free evidence, span from node positions, `subject_path` = dotted qualified name such as `module.Class.func`, severity from the rule, `fix_offers` from rule fixes whose preconditions hold).
  - Fact providers for the syntactic and scope facts above are implemented in this task; the two `call.*` facts and the two `function.*` facts are registered here as stubs raising `NotImplementedError` and replaced in Task 8.

- [ ] **Step 1: Write failing tests** with a synthetic catalog (one hand-built rule per test): `test_unparsable_source_returns_parse_error` (Review Focus 2), `test_finding_span_and_subject_path`, `test_only_required_facts_are_computed` (a counting provider proves facts outside the predicate are never called), `test_fingerprint_survives_leading_blank_lines` (Review Focus 3), `test_typing_any_detected_through_aliases` (`import typing as t; x: t.Any`, `from typing import Any as A`, plain `Any`; Review Focus 4), `test_uppercase_global_without_final_detected`, `test_final_annotated_global_is_ignored`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_engine.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the signatures above. Use the single `astart.parse` tree for all rules; resolve `Any` aliases from the module's own `Import`/`ImportFrom` statements.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 8: Semantic and docstring facts

**Files:**
- Modify: `src/astart/rules/facts.py`
- Test: `tests/test_rules_facts_semantic.py`

**Interfaces:**
- Consumes: `module.bind_call(node=...)`, `module.docstrings` (read their field names in `src/astart/semantic` and `src/astart/docstrings.py` before coding).
- Produces: real providers for `call.positional_keyword_candidates` (count of positionally passed arguments whose parameter kind is `POSITIONAL_OR_KEYWORD`; positional-only and arguments absorbed by `*args` do not count), `call.is_resolved_in_module` (callee resolves to a function or class defined in the same source), `function.has_docstring`, `function.undocumented_parameter_count` (parameters other than `self`/`cls` absent from the Google `Args:` section; `*args` and `**kwargs` are matched by their starred names).

- [ ] **Step 1: Write failing tests** `test_candidates_count_only_keyword_capable_parameters` (positional-only and `*args` excluded; Review Focus 5), `test_unresolved_callee_is_not_resolved`, `test_undocumented_parameters_ignore_self_and_cls`, `test_starred_parameters_match_their_entries`, `test_function_without_docstring_has_no_docstring_fact`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_facts_semantic.py -v`. Expected: FAIL (`NotImplementedError`).
- [ ] **Step 3: Implement** the four providers, replacing the stubs.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 9: Fixes and behavioural invariants 4 and 5

**Files:**
- Modify: `src/astart/rules/engine.py`, `src/astart/rules/facts.py` (register appliers `typing.add-final`, `calls.add-keywords`)
- Test: `tests/test_rules_fixes.py`

**Interfaces:**
- Produces: `def apply_fix(*, source: str, filename: str, finding: Finding, fix: Fix, registries: Registries) -> str` (parse, mutate the astart tree, return `astart.unparse(tree=..., preserve_formatting=True)`; returns `source` unchanged when preconditions do not hold). Appliers: `typing.add-final` turns `NAME = <int|str|float|bool|bytes literal>` into `NAME: Final[<type>] = ...` and adds `from typing import Final` only when no `Final` binding (including aliases) exists; `calls.add-keywords` rewrites each counted positional argument to `name=value` using `bind_call`. `def validate_behavior(*, catalog: Catalog, registries: Registries) -> None` raising `CatalogError`: invariant 4 (every example with `triggers=True` yields exactly one finding for its rule and none for other rules; `triggers=False` yields none) and invariant 5 (applying each fix a second time to its own output changes nothing).

- [ ] **Step 1: Write failing tests** `test_add_final_rewrites_literal_global`, `test_add_final_reuses_existing_final_alias` (Review Focus 4), `test_add_final_skips_non_literal_value`, `test_add_keywords_rewrites_resolved_call`, `test_add_keywords_leaves_positional_only_calls`, `test_fixes_are_idempotent`, `test_validate_behavior_reports_wrong_example`, `test_validate_behavior_reports_non_idempotent_fix`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_fixes.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `apply_fix`, the two appliers and `validate_behavior`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** full `python -m pytest -q`.

### Task 10: Seed catalog and end-to-end test

**Files:**
- Create: `src/astart/rules/catalog/typing.json`, `calls.json`, `docs.json`; `src/astart/rules/__init__.py` exports
- Modify: `src/astart/rules/catalog.py` (add `def load_default_catalog(*, registries: Registries) -> Catalog` reading the three files through `importlib.resources`), `README.md` (one paragraph and the rule table for the four rules)
- Test: `tests/test_rules_end_to_end.py`

**Interfaces:**
- Produces: the four rules, with values from spec section 5:
  - `typing.no-any` / `TYP001`, domain typing, severity error, subject `Annotation`, alias `{"exactus": "CMP002"}`, no fixes.
  - `typing.uppercase-global-not-final` / `TYP004`, alias `{"exactus": "PY002"}`, fix `typing.add-final` (`proven`, precondition `binding.value_is_immutable_literal == true`).
  - `calls.missing-keyword` / `CAL001`, alias `{"exactus": "KWARGS:missing-kwargs"}`, fix `calls.add-keywords` (`guarded`, `min_confidence` 0.9).
  - `docs.missing-parameter` / `DOC002`, alias `{"exactus": "DOC002"}`, no fixes in this slice.
  Each rule has at least one bad and one good example, and `requires` equal to the facts its predicate reads. Exports in `astart.rules`: `Catalog`, `Rule`, `Fix`, `Finding`, `CheckResult`, `check`, `apply_fix`, `load_default_catalog`, `default_registries`, `validate_behavior`, `CatalogError`.

- [ ] **Step 1: Write failing tests** `test_default_catalog_loads_and_validates` (load plus `validate_behavior`), `test_default_catalog_dump_is_canonical`, `test_check_reports_all_four_rules_on_one_module`, `test_fix_then_check_clears_fixable_findings` (apply TYP004 and CAL001 fixes, re-check, those findings are gone and DOC002 remains), `test_aliases_map_back_to_exactus_ids`, `test_package_data_ships_catalog_files` (resources resolve for all four JSON files).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_end_to_end.py -v`. Expected: FAIL.
- [ ] **Step 3: Write** the three JSON files by hand in canonical form (generate once with `dump_catalog`, then review), add exports and `load_default_catalog`.
- [ ] **Step 4: Run** `python -m pytest -q`, then `python -m coverage run -m pytest -q && python -m coverage report --include='src/astart/rules/*'`. Expected: all tests PASS; every `astart/rules` file at or above 80%, total at or above 90%.
- [ ] **Step 5: Final validation:** `ruff check src tests`, `ruff format --check src tests`, `basedpyright src/astart/rules tests/test_rules_*.py`. Expected: no findings. Hand back to the user to run Exactus.

---

## Self-review notes

- Spec coverage: sections 3.1–3.7 map to Tasks 1–3 and 10; section 4 (independence) is a Global Constraint and import-checked in Task 7's engine split; section 5 rows for the four rules are Task 10; sections 6–7 are not in this slice (phases and queries come with the full engine); section 8 invariants: 1, 2, 3, 6, 7, 8 in Task 5, 4 and 5 in Task 9.
- Not in this slice: profiles beyond the model, relations beyond the loader checks, the other catalog rules, ruff phase, CLI.
- Names used across tasks: `Registries`, `FactSpec`, `rule_cost`, `CatalogError`, `check`, `apply_fix`, `validate_behavior`, `load_default_catalog`, `default_registries` — each defined once above.
