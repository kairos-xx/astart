# Fix Runner and Gated Type Hints Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a single-pass fix runner and the TYP003 rule with two gated fixes (proven `-> None`, guarded inferred hints), plus a one-shot ruff formatting phase.

**Architecture:** A hint engine turns `module.convert(apply=False)` proposals into corroborated hints (default literal, call-site agreement, taint-checked returns). TYP003 is a normal catalog rule whose facts read that engine. `fix_source` parses once, applies the selected fixes to one tree, writes once through the format-preserving writer, degrades to one-at-a-time on failure, and re-checks until stable.

**Tech Stack:** Python 3.13, `astart.rules` (first slice), `astart.formatting` annotation write-back, `module.convert`, `module.bind_call`, `subprocess` for ruff, pytest with `tests.expectations`.

**Spec:** `docs/superpowers/specs/2026-11-06-fix-runner-and-type-hints-design.md` (extends `2026-11-06-rule-ontology-design.md`).

## Global Constraints

- `requires-python >=3.13`; `from __future__ import annotations` in every module.
- Keyword-only calls everywhere; callers always pass keywords.
- Google-style docstrings with Args/Returns/Raises/Attributes.
- Module-level constants live in a `@final class Constants` with `Final` attributes.
- No `Any`, no `object` annotations, no suppression comments (`noqa`, `type: ignore`, pyright/pyrefly pragmas).
- Model modules (`vocabulary`, `jsonvalue`, `predicate`, `model`, `registry`, `catalog`, `schema`) stay free of `astart.ast`, `astart.semantic`, `astart._graph` and top-level `astart` imports. New hint, runner and ruff modules may import them.
- Never write a hint containing `object`, `Any`, an unresolved name or a name that is neither a builtin nor already imported in the module.
- Coverage gates: at least 90% total, 80% per file, branch coverage on.
- Do not run Exactus. Validate with `python -m pytest`, `ruff check`, `ruff format --check` and `basedpyright`.
- The repo is not under version control: each task ends with a full `python -m pytest -q` checkpoint, not a commit.

## Review Focus

1. Mixed returns: `return` and `return 1` in one function, early returns, and `yield` / `async` generators must never get `-> None`; `@overload`, `@abstractmethod` and bodies of only `...` / `pass` / `raise NotImplementedError` get no proven `None`.
2. Shadowed or redefined functions and calls through unresolved names must not feed call-site evidence; two call sites that disagree (`int` vs `str`) give no hint.
3. A second `fix_source` run on its own output changes nothing; comments, blank lines and quote style survive; the result always parses.
4. When one edit cannot be written back, the other fixes in the file are still applied and the failure is reported with a reason, never raised.
5. Methods: `self` / `cls`, `*args`, `**kwargs`, keyword-only and positional-only parameters, nested functions, lambdas, and a `None` default behave as specified.

---

## File Structure

| File | Responsibility |
| --- | --- |
| `src/astart/rules/hints.py` | `Hint`, `HintBasis`, `HintIndex`: candidates from `convert`, corroboration, taint analysis |
| `src/astart/rules/facts.py` (modify) | `Parameter` subject, new facts and evidence, `ModuleFacts.hints`, `module_facts(stubs_path=...)` |
| `src/astart/rules/appliers.py` (modify) | `typing.add-none-return`, `typing.add-inferred-annotation` |
| `src/astart/rules/engine.py` (modify) | `stubs_path` on `check`; shared selection helpers |
| `src/astart/rules/runner.py` | `fix_source`, `FixResult`, `AppliedFix`, `SkippedFix` |
| `src/astart/rules/formatter.py` | `format_source`, `fix_and_format`, `FormatOutcome` |
| `src/astart/rules/catalog/typing.json` (modify) | TYP003 and its two fixes |
| `tests/test_rules_hints.py`, `test_rules_typing_fixes.py`, `test_rules_runner.py`, `test_rules_formatter.py`, `test_rules_runner_corpus.py` | One module per source module plus a corpus acceptance test |

---

### Task 1: Parameter hints from default literals and call sites

**Files:**
- Create: `src/astart/rules/hints.py`
- Test: `tests/test_rules_hints.py`

**Interfaces:**
- Consumes: `CommentedModule` (`astart.parse`), `module.convert(stubs_path=..., apply=False)` proposals (`GraphAnnotation` with `.target`, `.source`, `.role`), `facts.bound_call(subject, facts)` semantics (resolved, single-binding, undecorated callees).
- Produces:
  - `class HintBasis(StrEnum)`: `proven_none`, `default_literal`, `call_sites`, `derived_return`.
  - `@dataclass(frozen=True, slots=True) class Hint(source: str, basis: HintBasis)`.
  - `class HintIndex`: `HintIndex.create(*, module: CommentedModule, stubs_path: Path | None) -> HintIndex`; `hint_for(self, *, node: AST) -> Hint | None`; `rejection_for(self, *, node: AST) -> str | None` (reason a candidate was refused, e.g. `"contains object"`, `"uncorroborated"`, `"needs import"`, `"call sites disagree"`).
  - `def is_allowed_source(*, source: str, known_names: frozenset[str]) -> bool` (true only when every `Name` in the parsed expression is a builtin type name or in `known_names`, and `object` / `Any` are absent).

- [ ] **Step 1: Write failing tests** in `tests/test_rules_hints.py`: `test_default_literal_corroborates_parameter` (`def f(sep=" ")` → hint `str`, basis `default_literal`); `test_call_sites_corroborate_parameter` (`def scale(x): ...` + `scale(3)` → `int`, basis `call_sites`); `test_uncorroborated_candidate_is_refused` (`def greet(name): return "hi " + name` with no call → no hint, rejection `"uncorroborated"`); `test_disagreeing_call_sites_give_no_hint` (`f(1)` and `f("a")` → rejection `"call sites disagree"`); `test_candidates_with_object_or_unknown_names_are_refused` (`def count(items): return len(items)` + `count([1])` → no hint because the candidate is `Sequence[object]`); `test_shadowed_callee_calls_are_ignored` (def `f` then `def g(f): f(1)` gives no call-site evidence for `f`'s parameter); `test_self_cls_varargs_and_none_default_are_never_hinted`; `test_is_allowed_source_accepts_builtins_and_imported_names` (`list[int]`, `dict[str, int] | None` allowed; `Sequence[int]` allowed only when `Sequence` is in `known_names`).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_hints.py -v`. Expected: FAIL (import error).
- [ ] **Step 3: Implement** the interfaces above. Candidate lookup keys on `id(arg_node)`; call-site argument types come from `BoundArgument.types` when `definite` and exactly one `TypeShape` renders as a name in `{int, str, float, bool, bytes}` or a builtin generic; known names are the module's import-bound names.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q` is green.

### Task 2: Return hints (`proven_none` and taint-checked `derived_return`)

**Files:**
- Modify: `src/astart/rules/hints.py`
- Test: `tests/test_rules_hints.py`

**Interfaces:**
- Consumes: Task 1's `HintIndex`, `Hint`, `HintBasis`.
- Produces: `HintIndex.hint_for` also answers for `FunctionDef` / `AsyncFunctionDef` nodes. `def returns_nothing(*, function: FunctionDef | AsyncFunctionDef) -> bool` (true only when there is no `return <value>`, no `yield` / `yield from`, the function is not decorated with `overload` or `abstractmethod`, and the body is not only `...`, `pass`, a docstring or `raise NotImplementedError`). `def tainted_names(*, function: FunctionDef | AsyncFunctionDef, accepted: frozenset[str]) -> frozenset[str]`.

- [ ] **Step 1: Write failing tests**: `test_function_without_return_value_gets_proven_none` (async included); `test_mixed_returns_and_generators_never_get_none` (Review Focus 1); `test_overload_abstract_and_stub_bodies_get_no_none`; `test_derived_return_requires_untainted_returns` (`def f(x): return x * 2` with no call → refused `"tainted by parameter x"`; with `f(3)` → `int`, basis `derived_return`); `test_taint_flows_through_locals` (`y = x * 2; return y` still refused); `test_return_not_depending_on_parameters_is_accepted` (`def one(): return 1` → `int`).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_hints.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `returns_nothing`, `tainted_names` (fixpoint over assignments in the function body, nested functions excluded) and extend `hint_for` / `rejection_for`. A derived return is accepted only when its candidate passes `is_allowed_source` and no `Return` expression mentions a tainted name; parameters count as accepted when declared or when they have a hint.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q`.

### Task 3: TYP003 rule, facts, evidence and appliers

**Files:**
- Modify: `src/astart/rules/facts.py`, `src/astart/rules/appliers.py`, `src/astart/rules/engine.py`, `src/astart/rules/catalog/typing.json`
- Test: `tests/test_rules_typing_fixes.py`

**Interfaces:**
- Consumes: `HintIndex` (Tasks 1–2), the first-slice `Subject`, `ModuleFacts`, `Registry`, `Appliers`.
- Produces:
  - New subject kind `Parameter` (every `ast.arg` of a `FunctionDef` / `AsyncFunctionDef`, path `function.param`), added to `Constants.node_kinds`; lambdas excluded.
  - `module_facts(*, module: CommentedModule, stubs_path: Path | None = None) -> ModuleFacts` with new field `hints: HintIndex`; `check(..., stubs_path: Path | None = None)` forwards it.
  - Facts (name, type, cost): `node.annotation_missing` bool syntactic (parameter has no annotation and is not `self` / `cls` / `*args` / `**kwargs`; function has no `returns`); `function.returns_nothing` bool syntactic; `annotation.has_accepted_hint` bool semantic.
  - Evidence providers `proposed` (hint source or `""`) and `basis` (basis value or rejection reason).
  - Appliers `typing.add-none-return` (sets `returns` to `None`) and `typing.add-inferred-annotation` (sets the parameter or return annotation from the hint); both validate before mutating and never replace an existing annotation.
  - Catalog: rule `typing.missing-annotation` (`TYP003`, subjects `Parameter`, `FunctionDef`, `AsyncFunctionDef`, `when` `node.annotation_missing == true`, alias `{"exactus": "KWARGS:missing-hint"}`, fixes both below, one bad and one good example); fix `typing.add-none-return` (`proven`, precondition `function.returns_nothing`); fix `typing.add-inferred-annotation` (`guarded`, `min_confidence` 0.9, precondition `annotation.has_accepted_hint`). Invariant 6 must still hold: the proven fix reads only syntactic facts.

- [ ] **Step 1: Write failing tests** in `tests/test_rules_typing_fixes.py` against the real catalog: `test_missing_annotation_reports_parameters_and_returns` (paths `f.a`, `f` for `def f(a): ...`); `test_self_cls_and_variadics_are_not_reported`; `test_none_return_fix_is_offered_only_when_provable`; `test_inferred_fix_is_offered_only_for_accepted_hints` (offer present for `scale(x)` with `scale(3)` call, absent for the uncalled `greet`); `test_apply_adds_none_return_in_place` and `test_apply_adds_parameter_annotation_in_place` (comments kept); `test_appliers_never_replace_existing_annotations`; `test_catalog_still_verifies` (`verify_catalog` on the default catalog passes, including idempotence of both fixes).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_typing_fixes.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the facts, subject enumeration, evidence, appliers and catalog edits; regenerate `schema.json` only if the model changed (it should not). Update the first-slice end-to-end sample test expectations if TYP003 now also reports on `sample` (list the new findings explicitly).
- [ ] **Step 4: Run** `python -m pytest tests/test_rules_typing_fixes.py tests/test_rules_end_to_end.py -v`. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q`.

### Task 4: Fix runner core

**Files:**
- Create: `src/astart/rules/runner.py`
- Test: `tests/test_rules_runner.py`

**Interfaces:**
- Consumes: `check`, `Finding`, `Fix`, `Catalog`, `Registries`, `Appliers`, `locate`-style subject lookup from `engine.py` (expose a public `locate_subject(*, module, finding) -> Subject | None`).
- Produces:
  - `@dataclass(frozen=True, slots=True) class AppliedFix(fix_key: str, rule_key: str, subject_path: str)` and `SkippedFix(fix_key: str, rule_key: str, subject_path: str, reason: str)`.
  - `@dataclass(frozen=True, slots=True) class FixResult(source: str, applied: tuple[AppliedFix, ...], skipped: tuple[SkippedFix, ...], remaining: tuple[Finding, ...], parse_error: str | None)`.
  - `def fix_source(*, source: str, filename: str, catalog: Catalog, registries: Registries, ceiling: FixSafety, stubs_path: Path | None = None, max_rounds: int = 3) -> FixResult`. In this task: one round, one parse, one write.

- [ ] **Step 1: Write failing tests**: `test_ceiling_selects_fixes` (`proven` applies only `add-final` / `add-none-return`; `guarded` also applies keywords and inferred hints; `suggest` is rejected with `ValueError`); `test_all_fixes_apply_in_one_pass` (a module needing Final, keywords, `-> None` and a hint ends with all four edits and every comment intact); `test_conflicting_offers_on_one_node_are_skipped` (reason `"conflict"`); `test_failing_applier_is_skipped_with_reason` (using the `appliers=` seam, the tree is untouched by the failing applier); `test_unparsable_source_returns_parse_error_without_raising`; `test_fix_order_follows_before_after_relations`; `test_nothing_to_fix_returns_source_unchanged`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_runner.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** `fix_source` for one round: collect findings with `check`, keep offers with `safety` rank at or below `ceiling`, order by fix relations (topological over `Fix.before` / `Fix.after`, ties by fix key) then source position, track edited node ids for conflicts, apply appliers, one `unparse(preserve_formatting=True)`, verify with `ast.parse`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q`.

### Task 5: Degraded mode and convergence

**Files:**
- Modify: `src/astart/rules/runner.py`
- Test: `tests/test_rules_runner.py`

**Interfaces:**
- Consumes: Task 4's `fix_source` internals.
- Produces: `fix_source` now (a) on `FormatPreservationError` or a non-parsing result applies the selected fixes one at a time, each from the current text, keeping those that write back and reporting the others as skipped with reason `"cannot write back without changing formatting"`; (b) repeats up to `max_rounds` until a round applies nothing or leaves the text unchanged, and `remaining` reflects a final re-check.

- [ ] **Step 1: Write failing tests**: `test_unwritable_edit_does_not_block_other_fixes` (a call with comments between its arguments plus a fixable Final: Final applied, keywords skipped with the reason; Review Focus 4); `test_second_round_unlocks_derived_return` (`def f(x): return x * 2` + `f(3)`: round one adds the parameter hint, round two adds `-> int`); `test_second_run_changes_nothing` (Review Focus 3); `test_max_rounds_bounds_the_loop`; `test_remaining_lists_unfixed_findings`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_runner.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** the degraded path and the round loop; the per-round bookkeeping merges `applied` / `skipped` across rounds without duplicates.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q`.

### Task 6: Formatter phase

**Files:**
- Create: `src/astart/rules/formatter.py`
- Test: `tests/test_rules_formatter.py`

**Interfaces:**
- Consumes: `FixResult` (Task 4).
- Produces: `@dataclass(frozen=True, slots=True) class FormatOutcome(source: str, formatted: bool, note: str)`; `def format_source(*, source: str, filename: str, cwd: Path) -> FormatOutcome` (runs `ruff format --stdin-filename <filename> -` once with `cwd` for configuration; returns the original source with `formatted=False` and a note when ruff is missing, exits non-zero, or times out after 30 seconds); `def fix_and_format(*, source: str, filename: str, catalog: Catalog, registries: Registries, ceiling: FixSafety, cwd: Path, stubs_path: Path | None = None) -> tuple[FixResult, FormatOutcome]`.

- [ ] **Step 1: Write failing tests**: `test_format_source_runs_ruff_once` (messy spacing is normalised); `test_missing_ruff_is_reported_not_fatal` (using a `PATH` without ruff via `monkeypatch`); `test_ruff_error_keeps_original_source`; `test_fix_and_format_output_is_stable` (running `ruff format --check` on the result passes, and a second `fix_and_format` returns identical text).
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_formatter.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** with `subprocess.run(..., input=source, capture_output=True, text=True, timeout=30, check=False)`; resolve ruff with `shutil.which("ruff")` and fall back to `sys.executable -m ruff`.
- [ ] **Step 4: Run** the same command. Expected: PASS.
- [ ] **Step 5: Checkpoint:** `python -m pytest -q`.

### Task 7: Gold-set precision and corpus acceptance

**Files:**
- Create: `tests/test_rules_runner_corpus.py`
- Modify: `src/astart/rules/README.md`, `src/astart/rules/__init__.py` (export `fix_source`, `FixResult`, `format_source`, `fix_and_format`)

**Interfaces:**
- Consumes: everything above.
- Produces: public exports; README section "Fixing" (ceilings, acceptance policy table from the spec, degraded mode).

- [ ] **Step 1: Write failing tests**: `test_gold_set_has_no_wrong_hints` (a table of at least 25 `(source, expected_hints)` cases drawn from the spec's acceptance table and Review Focus, each asserting both accepted hints and refusals, including the `greet`, `scale`, `count`, `seq[0]` and `label` cases from the probe); `test_corpus_fixes_parse_keep_comments_and_are_stable` (parametrised over the vendored corpus: after `fix_source(ceiling=guarded)` the output parses, every comment is present, stripping annotations gives the original tree, and a second run changes nothing); `test_corpus_never_gains_object_or_any` (no `object` / `Any` appears in added annotations); `test_runner_reports_skips_with_reasons`.
- [ ] **Step 2: Run** `python -m pytest tests/test_rules_runner_corpus.py -v`. Expected: FAIL.
- [ ] **Step 3: Implement** exports and README; if the corpus run exposes a wrong hint, tighten the policy in `hints.py` and add the case to the gold set.
- [ ] **Step 4: Run** `python -m pytest -q`, then `python -m coverage run -m pytest -q && python -m coverage report --include='src/astart/rules/*'`. Expected: all PASS; every `astart/rules` file at or above 80%, total at or above 90%.
- [ ] **Step 5: Final validation:** `ruff check src tests`, `ruff format --check src/astart/rules tests/test_rules_*.py`, `basedpyright src/astart/rules tests/test_rules_*.py`. Expected: no findings (ignore `pytest`-resolution noise if the shell cannot import it). Hand back to the user to run Exactus.

---

## Self-review notes

- Spec coverage: section 3 policy → Tasks 1–3; section 4 runner (ceiling, order, conflicts, isolation, write-back, convergence, result) → Tasks 4–5; section 5 formatter → Task 6; section 2 findings and non-goals → gold set and corpus checks in Task 7. Not in this slice: CLI, variable annotations, imports, docstring/whitespace/Constants fixers.
- Names used across tasks: `Hint`, `HintBasis`, `HintIndex`, `is_allowed_source`, `returns_nothing`, `tainted_names`, `FixResult`, `AppliedFix`, `SkippedFix`, `fix_source`, `locate_subject`, `FormatOutcome`, `format_source`, `fix_and_format` — each defined once above.
- Proportion: the spec is about 120 lines; this plan is about 200, with signatures and test names rather than bodies.
