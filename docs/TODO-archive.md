# Astart — TODO archive

Done tasks in full and the historical chapters of the old TODO.
The living backlog is `docs/TODO.md`.


## Completed tasks (full text)

### Chapter 1. Foundations and measurement

#### M0-01 — Git init + ruff-format drift policy
- **Status:** done
- **Priority:** P0
- **Area:** DevOps / Release
- **Readiness:** done

**Context:** Repository initialized so every
milestone diff is reviewable and rollback-safe; `ruff format` runs as the
single final pass only.

**Evidence:** git history `0fa056e` (initial) → `5b788f3`.

#### M0-02 — D1: `ensure_names` in `add_inferred_annotation`
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Imports for
`_importable` names (`Iterable`, `Path`, …) are now inserted, removing the
latent uncompilable-output path.

**Evidence:** `src/astart/rules/appliers.py`; catalog examples compile.

#### M0-03 — D2: `'Unknown'` is non-definite evidence
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Unknown call-site types no
longer count as disagreeing; syntax-proven argument types are independent
evidence (`Path("x")` case).

**Evidence:** `src/astart/rules/hints.py` judges; semantic tests.

#### M0-04 — D3: imported constructors type their calls
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `constructors` wired so
`Path("x")`, `Decimal(..)`, … prove their result type via the
`@constructor:<Name>` binding-count key.

**Evidence:** `src/astart/rules/provable.py`, `imports.py`; tests green.

#### M0-05 — D6: `Exists` crash guarded
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Catalog validation rejects `exists`
predicates until M8 implements evaluation.

**Evidence:** `src/astart/rules/catalog.py` validation; `predicate.py`.

#### M0-06 — D9: `typing.add-noreturn` fix
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Always-raising functions get
`-> NoReturn` (proven safety class).

**Evidence:** catalog rule + applier; `never_returns` lattice member.

#### M0-07 — Final-review findings C1, C2, I1–I6
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** fixed.

#### M0-08 — Type-policy cleanup
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Five `object` annotations in `formatting.py`
replaced with `FieldValue`/`PatchValue` aliases; RUF043 fixed.

#### M0-09 — D10 suite-flakiness investigation
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Did not reproduce: suite passes
forward and reverse file order (1616 tests); observed failures traced to an
external tool rewriting files mid-run, not shared mutable state.

#### M0-10 — Bare `exactus` clean
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** All 6 tools PASS, 0 files with issues:
docs 0/159, lints 0/159, coverage_tests 0/91 (1616 tests, 94.95% total),
kwargs_typehints 0/159 (unresolved callees 0), readme, performance.

**Evidence:** `exactus` unified run, 2026-11-07.

#### M1-01 — Closed skip/rejection reason enums
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `rules/reasons.py` defines
`SkipCode` (runner refusals: `subject-missing`, `conflict`,
`preconditions-changed`, `applier-failed`, `write-back`, `checker-rejected`)
and `Rejection` (hint refusals, values are the reported texts).
`SkippedFix.code` carries the enum; `_apply_one` returns
`(SkipCode, str)`; every `hints.py` rejection string is a `Rejection` member.

**Evidence:** `tests/test_rules_skip_codes.py`.

#### M1-02 — E6 checker oracle, core
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `rules/checker.py`: `Checker` protocol,
`PyrightChecker` (scratch sibling file → `pyright --outputjson --level
error` → `Counter[Diagnostic]` before-vs-after), `detect_checker()`
auto-detecting `basedpyright`/`pyright`, sha256 content-hash cache.
`runner._attempt` vetoes guarded fixes → `SkipCode.checker_rejected` →
`_try` halves the batch (bisect via existing halving) and rolls back.
CLI `--checker auto|off` (default auto) → `FixSettings.checker`.

**Evidence:** `src/astart/rules/checker.py`, `runner.py`, `cli/commands.py`,
`test_cli_main.py` checker-flag tests.

#### M1-03 — E6 oracle remainder
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Optional `mypy` executable in
`Constants.executables`; when no checker is installed, guarded fixes require
the higher internal-evidence path (E2∧E5 both, not either); document the
refuse-on-unanswerable-checker behavior already in `regresses` (returns
`True` when either run gives no diagnostics).

**Scope:** `rules/checker.py`, `runner.py` guarded path, `cli/commands.py`.

**Acceptance:** `--checker auto` with no installed checker still refuses a
fix whose evidence is single-signal; mypy honored when present.

**Note:** a call-site hint now already requires syntax-proven argument types
(see the progress log), which covers part of the "higher internal
evidence" path; the checker-absent switch itself is still open.
Closed 2026-11-07: `MypyChecker`/`build_checker` fallback +
`test_rules_checker_fallback.py` prove the refuse-on-no-checker floor.
Update (2026-11-07): checker scratch files now live in a temp directory;
`rules/environment.py` detects the file's package (`__init__.py` chain),
source roots (package parent, `src/`, project root) and rewrites relative
imports against the package, so pyright (`--project` with `extraPaths`,
project settings kept) and mypy (`MYPYPATH`) resolve imports as for the
real file. `tests/test_rules_environment.py`.

#### M1-04 — Benchmark harness scaffolding
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** `benchmarks/` package,
`tests/bench_*` module family, `docs/benchmarks.md` dashboard source;
pinned harness API that runs `check`/`fix` on a tree and records metrics.

**Scope:** new `benchmarks/`, test layout, docs skeleton.

**Acceptance:** `python -m benchmarks` produces a machine-readable baseline
report on the seed corpus; runs under exactus without new findings.

**Partial (open):** `benchmarks/__init__.py` + `benchmarks/recovery_report.py`
(text table, `PYTHONPATH=src python benchmarks/recovery_report.py FILE...`)
and `docs/benchmarks.md` exist. Missing: `python -m benchmarks` entry
point, machine-readable (JSON) output, `tests/bench_*` family, `check`
mode metrics.

#### M1-05 — Annotation-recovery benchmark
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Strip annotations from real
open-source modules, run `astart fix`, diff recovered vs original; report
precision/recall per evidence class.

**Acceptance:** ≥1 real module measured end-to-end with per-failure-class
attribution written to the dashboard.

**Partial (open):** `rules/recovery.py` (`strip_annotations`, `annotation_map`,
`recover` → `RecoveryScore`: truth/correct/wrong/missed/synthesized/
seconds). Run over all 113 corpus modules after the 2026-11-07 feature
batch: **precision 35/35 (100%), recall 35/317 (11.0%), 0 crashes**, 92 s
total (audit baseline before the batch: 27/28, 27/317, 2 crashes); 80.7 s total,
slowest `configparser` 5.7 s. Typed modules: `tomllib/_parser` 116 truths,
`importlib.metadata.__init__` 69, `importlib.resources.abc` 26,
`importlib.metadata._meta` 21, `asyncio.timeouts` 19. The one wrong
annotation is `asyncio.timeouts.Timeout.__aexit__` → wrote `None`, truth
`Optional[bool]` (→ M2-14). Locked on 6 modules by
`tests/test_rules_recovery.py`. Missing: per-failure-class attribution
(group `missed` by `Rejection`/`SkipCode`), per-evidence-class precision,
and a test that covers the 107 other modules.

#### M1-06 — Gold set expansion 34 → ≥500
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** One gold case per failure class
from the verified recall-gap list (R1–R12, P1–P4, T1–T5, K1–K4) and every
reviewer finding.

**Acceptance:** ≥500 cases, each tagged by failure class; every new fix ships
with its gold case.
Evidence (audit 2026-11-07): `tests/test_gold_expansion.py` — 535 cases in
20 families (`call_sites` 227, `default_literal` 114, `proven_return` 44,
`call_sites_disagree` 21, `typed_flow` 18, `uncorroborated` 12,
`escape` 11, `proven_none` 11, `control_flow` 10, … `method_binding` 5);
`test_gold_case_count` enforces ≥ 500; 537 tests pass in 3 s.
Known limits: cases assert the `HintIndex` outcome, not the full
`fix_source` result or the checker gate (→ M1-17); R1–R12 / P / T / K
families appear only as required refusals because those features do not
exist yet.

#### M1-07 — Corpus expansion 20 → ≥100 real modules
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Diverse open-source
modules under `tests/corpus/`, including OO-heavy and async code.

**Acceptance:** ≥100 modules replay deterministically; counts published.
Evidence (audit 2026-11-07): 113 modules in `tests/corpus/*.py.txt`
(asyncio, importlib, concurrent.futures, tomllib, … ); every corpus test
is parametrized over the directory and passes; the recovery benchmark was
run over all of them and the counts are published in
`docs/benchmarks.md` ("113-module baseline").
Known limits: 0 of the 113 are third-party/OO-application code — all are
CPython stdlib modules, so the pinned-project work in M1-12 is still the
only coverage of "ordinary" application style.

#### M1-08 — Precision/recall dashboard
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Metrics pipeline emitting
precision ≥99.5% guarded / 100% proven gates, recall, and per-rule tables.

**Acceptance:** dashboard fails the build below thresholds; numbers derived
from the harness, not hand-counted.

**Audit 2026-11-07:** the current measured precision on the full corpus
(27/28 = 96.4%) is **below the 99.5% guarded gate**, so a real gate would
fail today; fix M2-14 first, then enable the gate.
Update 2026-11-07: after M2-14 the corpus precision is 35/35 (100%), so
the gate would pass; enabling it is the remaining work.
Evidence (2026-11-07): `benchmarks/baseline.json` is the accepted gated
run (113 modules, 0 crashes, 36/36 precise, 0 new checker errors);
`python -m benchmarks gate` fails on wrong annotations, new errors,
crashes or recall drops; `tests/test_bench_baseline.py` pins the baseline;
numbers are in `docs/benchmarks.md`.

#### M1-09 — Checker-delta metric
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** E6 run before/after per benchmark round;
zero-new-error delta tracked and published.

**Acceptance:** benchmark report includes a checker-delta column on ≥1 project.

#### M1-11 — Stability benchmarks
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Idempotence (fix∘fix = fix byte-equal)
and ≤3-round fixed-point convergence on the whole corpus.

**Acceptance:** zero non-idempotent corpus files; round counts in dashboard.

**Audit 2026-11-07 (partial):** `tests/test_rules_idempotence.py` runs
`fix_source` twice on all 113 corpus modules under the guarded ceiling —
byte-equal, zero non-idempotent files (150 s). Round counts are not
externally observable (`FixResult` exposes no per-round data) and the
dashboard half remains open.

#### M1-12 — Semantic-equivalence runs
- **Status:** done
- **Priority:** P2
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Compile + import + smoke-run
`astart fix` output on 10 pinned projects.

**Acceptance:** 10/10 projects import and pass their own smoke tests post-fix.

#### M1-13 — Writer fuzzing
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Random fix subsets → output compiles, comments
preserved, AST-equal-after-strip.

**Acceptance:** fuzz driver + seed corpus; zero crashes on recorded seeds.

**Evidence:** `tests/test_rules_writer_fuzz.py` — 6 corpus modules × 3
deterministic hash-derived fix subsets (no `random`); each result has no
`parse_error`, compiles, and keeps every comment.
Known limits: AST-equal-after-strip is not asserted — synthesized
Protocols/TypeVars/imports add statements by design; the strip-equality
check still runs in `test_rules_runner_corpus.py` for the hint fixes.

#### M1-14 — Full-CLI idempotence tests
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** `astart fix` twice on every corpus
file byte-identical, through the real CLI (not `fix_source`).

**Acceptance:** per-corpus-file parametrized test, all green.

**Partial (open):** `tests/test_cli_idempotence_corpus.py` runs
`fix_and_format` (fix + ruff) twice on the 7 corpus modules ≤ 700 lines and
requires byte-equal output (all green). Missing: the larger modules, and
driving it through the real CLI entry (`main(argv=…)`) rather than the
library call.

**Audit 2026-11-07 (partial):** `tests/test_cli_idempotence_full.py` verified
green — `fix_and_format` twice on all 35 modules > 700 lines (31 pass,
3 strict-xfail) and three modules (1.2k/1.8k/2.4k lines) driven through
`main(["fix", ...])` twice: first run exits 1 (changed), second exits 0
with byte-identical files. Every corpus file is now covered; driving
*all* of them through the CLI entry remains the open slice. The 3
xfails pin a real defect: `fix_and_format` does not reach a fixed
point on `dataclasses`, `re___compiler`, `webbrowser` — pass 2 annotates
parameters (`autoraise: bool`, `flags: int`, `init/repr/compare: bool`)
that pass 1 left alone because the formatted text gives the next fix
pass call-site evidence it lacked (`fix_source` alone IS idempotent on
all 113). Owner: hint/call-site binding (M1-11/M2 line).

#### M1-15 — D7: real `FixOffer.confidence` + `min_confidence` enforcement
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Replace hardcoded `confidence=1.0` in `engine._finding` with calibrated
values per evidence level; enforce `fix.min_confidence` (parsed in
`model.py`, currently ignored) when offers and fixes are selected.

**Scope:** `engine.py`, `runner.py`, `catalog/*.json` values.

**Acceptance:** a fix below `min_confidence` is not offered/applied; gold
cases pin the boundary.

**Evidence:** `rules/confidence.py` (`offer_confidence`: proven 1.0, default
literal 0.99, call sites 0.95, derived return 0.9, keywords 0.95,
Protocol/TypeVar 0.9); `engine._finding` uses it; `runner._eligible`
enforces `max(settings.min_confidence, fix.min_confidence)`;
`FixSettings.min_confidence` and CLI `--min-confidence`.
`tests/test_rules_confidence.py` pins the 0.97 boundary (default-literal
hint kept, call-site hint dropped).
Known limits: values are assigned per evidence class, not yet calibrated
against measured precision — that remains CC-01.

#### M1-16 — Crash containment for analyzer failures (audit finding)
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `astart fix` raises a bare `IndexError: string index out of range` from
`_graph/conversion/stages.py::_find_opening_paren_pos` (line 175) on the
annotation-stripped rendering of two corpus modules (`_strptime.py.txt`,
`stringprep.py.txt`: 2 of 111 scored). The traceback escapes
`fix_source`/`check` (whose documented contract is "never raises on bad
input") and aborts the whole CLI run on that file.

**Scope:** `_graph/conversion/stages.py` root cause; `rules/hints.py`
(`_candidates` → `module.convert`), `rules/runner.py`, `cli/commands.py`.

**Acceptance:** (1) root cause fixed with a RED→GREEN test using a reduced
reproduction of the stripped `_strptime`; (2) any exception from the
inference layer becomes a per-file result (no hints for that file, a
`parse_error`-style note, exit status 2) instead of a traceback, with a test
that injects a failing `convert`; (3) the recovery benchmark reports 0
crashes over the 113-module corpus.
Evidence (2026-11-07): root cause was a unit mix-up — `ast` columns are
UTF-8 *byte* offsets while `tokenize` and string indexing use characters,
so `_find_opening_paren_pos`/`_find_closing_paren_pos` indexed past the end
of any line with multibyte text before a parenthesis;
`stages._character_column` converts. Containment: `hints._candidates`
catches `Constants.inference_errors` and returns no candidates, so a failing
analyzer degrades to the syntax-only hints instead of raising.

**Tests:** `tests/test_graph_nonascii_columns.py` (4 multibyte sources, and a
monkeypatched failing `convert`). The 113-module benchmark now reports
`crashed 0` (was 2).
Known limits: containment covers the inference call inside hints only;
other analyzer entry points (`check` facts that call `bind_calls`) are not
wrapped.

#### M1-17 — Gold set at fix level
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** The 535 gold cases assert
`HintIndex` hints only. Add a parallel check that runs `fix_source` (guarded
ceiling, checker off and with a stub checker) on every gold source and
asserts the written annotations equal the expectation, so applier,
import-insertion and write-back bugs are caught by the same cases.

**Acceptance:** ≥ 500 cases asserted through `fix_source`; one failure class
per family reported.

**Evidence:** `tests/test_gold_expansion.py::test_gold_fix_level` — all gold
cases through `fix_source` under a catalog restricted to the three
annotation fixes (`add-none-return`, `add-noreturn`,
`add-inferred-annotation`), once with `checker=None` and once with an
accepting `Checker` stub: 1 070 assertions, all green. One recorded
divergence (`_FIX_EXPECTED["call_sites/repr-site"]`): multi-round fixing
converges `p: str` → `-> str`, which the single-pass hint index must
refuse — legitimate fixed-point behaviour, not a bug.

#### M1-18 — Fast test tier
- **Status:** done
- **Priority:** P2
- **Area:** Testing / QA
- **Readiness:** done

**Context:** The suite is 2 808 tests and takes
≈ 5.5 min (334 s on the audit run), almost all in corpus-parametrized
files (`test_rules_runner_corpus`, `test_cli_idempotence_corpus`,
`test_rules_synthesis_corpus`, `test_writer_fuzz`, `test_rules_recovery`).

**Acceptance:** a `pytest -m "not slow"` tier under 60 s for the edit loop and
a documented full tier for CI; no test is deleted.
Evidence (2026-11-07): `tests/conftest.py` marks corpus-parametrized
modules `slow`; `pytest -m "not slow"` = 3 347 passed in ≈ 35 s, the full
tier (`pytest`) stays the CI gate.

### Chapter 2. Object-oriented code

#### M2-01 — D5: `self.m()` binding
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Methods of the enclosing class bind via
`self.` receivers so they collect call-site evidence.

**Scope:** `rules/resolve.py` (`trusted_binding`, `binding_counts`), `semantic/`.

**Acceptance:** `self.m(4)` gives `m` a definite site; gold case green.

**Evidence:** `rules/methods.py` (`MethodIndex.bind_self_call`) builds a
`BoundCall` from `module.signature("Class.method")`; the receiver must be
the method's first parameter, never rebound; the method must be undecorated,
defined once (searching a single in-module base chain), and `is_safe`.
Sites carry syntax-proven argument types (`definite=False`, so
`hints._argument_evidence` uses the syntax proof). Tests:
`tests/test_rules_methods.py` (keywording, hints from `self.m(1, 2)`,
inherited method, rebinding / static / class / override / attribute-store
refusals) and gold cases "method call on a constructed instance is
resolved" and "overridden method gives no call-site evidence".
Known limits: `super().m`, `cls.m`, multiple inheritance and unresolved
bases give no binding (→ M2-02).

#### M2-03 — Instantiation → `__init__`/`__new__`/dataclass fields
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `C(…)`
calls bind to the constructor signature incl. dataclass/NamedTuple fields.

**Acceptance:** kwargs fixer keywords `C(a=…)` from `__init__` params.

**Evidence:** `P(1, 2)` → `P(x=1, y=2)` from `__init__` (analyzer binding,
already trusted); simple dataclasses are now trusted through
`methods.dataclass_init_names` + `resolve._is_plain_dataclass_call`: the
generated field list must equal the analyzer's parameters, so
`D(1, "t")` → `D(a=1, b='t')` and a `field(init=False)` field is skipped
without misaligning later arguments. NamedTuple classes bind through the
analyzer. Tests: `tests/test_rules_constructors_kw.py` (init, dataclass,
skipped field, and five refusals: `init=False`, `kw_only=True`, base class,
extra decorator, `KW_ONLY`).
Known limits: `__new__`-only classes, dataclass inheritance, `attrs`/
pydantic models and `InitVar` ordering are not trusted (→ M2-10).

#### M2-04 — D4: `trusted_binding` v2 for expression receivers
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `C().m(4)`/`factory().m()` bound by the analyzer but rejected today.

**Acceptance:** `C().m(1)` keywords the call; gold case green.

**Evidence:** `resolve._vet` accepts the analyzer's binding for
`Class(...).method(...)` when `Class` is a module class bound once
(`MethodIndex.constructed_receiver`) and the definition is plain;
`tests/test_rules_methods.py::test_call_on_a_constructed_instance_is_keyworded`
and the gold case above.
Known limits: `factory().m()` (a call to a function) stays untrusted —
the receiver's class is not known without return-type inference (→ M4).

#### M2-14 — E1 for protocol dunders (audit finding)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** The 113-module benchmark
wrote `-> None` on `asyncio.timeouts.Timeout.__aexit__` (truth
`Optional[bool]`): the body provably returns nothing, but `__exit__`/
`__aexit__` are protocol methods whose declared result is `bool | None`
(`True` suppresses exceptions), and a subclass or caller may rely on that.

**Scope:** `rules/facts.py` (`_returns_nothing`, `_never_returns`),
`rules/provable.py`, a small table of dunder protocol signatures
(`__exit__`, `__aexit__`, `__enter__`, `__bool__`, `__eq__`, `__hash__`,
`__repr__`, `__str__`, `__len__`, `__iter__`, `__next__`, `__getitem__`…).

**Acceptance:** dunder methods take their protocol-declared result type (or are
skipped) instead of the body-derived one; the recovery benchmark reaches
precision 100% on `asyncio.timeouts`; gold cases pin `__exit__`,
`__aexit__`, `__bool__`.
Evidence (2026-11-07): `hints.Constants.protocol_results` +
`HintBasis.protocol_result` (confidence 0.97): `__exit__`/`__aexit__` →
`bool | None`, `__bool__`/`__contains__` → `bool`, `__len__`/`__hash__`/
`__index__`/`__int__` → `int`, `__str__`/`__repr__`/`__format__` → `str`,
`__float__` → `float`, only when the body fits (otherwise
`Rejection.protocol_mismatch`). `returns_nothing` excludes them, so the
proven `-> None` fix no longer narrows `__exit__`. Tests:
`tests/test_rules_dunder_results.py`. The benchmark's only wrong
annotation (`Timeout.__aexit__`) is resolved; the scorer now compares
`Optional[X]`/`Union`/`typing.List` forms semantically
(`recovery.normalize_annotation`).

#### M2-15 — Typed call-site arguments from their scope (new)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Call-site
hints now see through variables: `provable.scope_types` types locals
assigned exactly once from a provable value, parameters annotated with a
builtin scalar, and hints already accepted for the enclosing function's own
parameters; `provable.module_constants` types uppercase module constants
that are never rebound (also `Final[...]`-annotated ones). Accepted hints
are propagated to a fixpoint inside `HintIndex.judge_parameters`
(`Constants.propagation_passes`), which also removes the multi-round
non-idempotence of `fix` (the three modules pinned as strict-xfail in
`tests/test_cli_idempotence_full.py` now converge; the marks are removed).
Call-site evidence is now *only* what the argument's syntax proves — the
analyzer's own argument types are no longer consulted, and tuple-literal
shapes count as unknown. Tests: `tests/test_rules_call_site_scope.py`
(4 positive, 7 refusals: reassigned, loop variable, augmented, lowercase
module variable, unknown call result, `global`/`nonlocal` rebinding).
Known limits: attributes (`self.x`), call results and containers other
than literals are not typed (→ M2-06, M4-01, M4-15).

### Chapter 3. Whole-project analysis

#### M3-01 — Import resolution (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `project/` package: `naming.py` maps files to dotted names (source roots
first, `__init__` chain fallback), `scan.py` extracts definitions,
absolute/relative/conditional imports, literal and dynamic `__all__` and
star imports per module, and `table.py` resolves names across modules —
local definitions first, then imports in document order (try/except
semantics), `__init__` re-export chains, star-imported exports and
sibling submodules, with cycle protection and `external` marking for
names outside the scan set. Tests: `test_project_naming.py`,
`test_project_scan.py`, `test_project_table.py`.

#### M3-02 — Whole-project call graph (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `project/index.py` `ProjectIndex`: definitions, per-module call records and escaped-load sets over the symbol table, keyed by SHA-256 content hash — `refresh` of unchanged files is free, changed files drop and re-index only their own records while retained records re-resolve against the rebuilt table; `version` increments feed `HintCache` keys. `C().m()`/`C.m()`/constructor shapes resolve.

**Tests:** `test_project_index.py`.

#### M3-03 — E3 cross-module call sites (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `rules/project_bridge.py` `ProjectView` binds calls in other modules through the callee's `CallableContract` and produces the same `_Site` evidence the local layer uses — only caller-scope syntax counts, unknown expansions are unknown evidence, and unbindable callees give `None`. `open_world`: escaped names always, exported names under `assume_external_callers` (default on; `--closed-world` opts out). `_name` private functions are closed-world. Class callees bind their `__init__`/`__new__` or dataclass-generated signature; decorated classes and inherited constructors stay unbound. Wired through `CheckOptions`/`FixSettings`/`ModuleFacts`/`LazyHints` and the CLI (`--project`). Tests: `test_project_bridge.py`, `test_project_m3.py`.

#### M3-04 — E4 typeshed/`py.typed`/stub-package loading (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `project/libraries.py` `LibraryIndex`: typeshed `stdlib/` plus `stubs/<dist>/<pkg>` roots, `*-stubs` packages before `py.typed` inline packages per PEP 561, `.pyi` before `.py`, size-capped lazy parsing into `StubSignature`/`CallableContract`. `_graph/stubs` `LazyStubIndex` also falls back to `stubs/<dist>` after `stdlib/` misses. `ProjectView.binding` binds external calls via `LibraryIndex.contract`, so `calls.add-keywords` works on project and stub-backed callees; the CLI builds the index over the environment's site-packages when `--project` is on. Tests: `test_project_libraries.py`, `test_project_bridge.py`.

#### M3-05 — K1: curated "safe to keyword" library table
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — stdlib first,
typeshed-generated, test-verified.
Evidence (2026-11-08 audit): `rules/libkw.py` (~37.5k lines,
`SIGNATURES`/`KwSignature`, positional-only and `self`/`cls` excluded)
generated by `scripts/generate_libkw.py` from the bundled typeshed;
`tests/test_rules_libkw.py` (8 tests). Consuming the table in binding
is M3-15.

#### M3-06 — Version awareness (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `project/versions.py` `PythonTarget` resolves the floor from `--target-version`, then `pyproject.toml` `requires-python`, then the interpreter; capability flags cover `X | Y` (3.10), `Self` (3.11), PEP 695 generics/`type` (3.12) and `TypeAlias` (3.10). Emission respects the floor: `add_inferred_annotation`/`add_attribute_annotation`/ `_synthesize_multi` respell `X | Y` as `Union[X, Y]` and `T | None` as `Optional[T]` below 3.10 (`Union`/`Optional`/`Self` added to `known_imports`), and `function.self_return`/`synthesize_self` are gated below 3.11. The fix engine never emits PEP 695 or `type X =` syntax, so those gates are declarative only for now. Tests: `test_project_versions.py`, `test_project_m3.py`.

#### M3-10 — Shadowing/collision avoidance
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** for inserted imports.
Evidence (2026-11-08 audit): `insert_import` computes runtime bindings
before the use site and imports under a `_name` alias (with a `while`
loop for repeated collisions); `_localize` rewrites the annotation to
the alias. Conservative over-approximation of prior bindings.

**Tests:** `test_rules_imports.py`,
`test_review3_fixes.py::test_c2_imports_stay_runtime_correct`.

#### M3-14 — M3 exit gate (done 2026-11-08)
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** `tests/test_project_m3.py`: CLI end-to-end coverage of cross-module annotation inference, exported-API guarding vs `--closed-world`, `__init__` re-export chains, cross-module keyword rewrites, precision (untyped callers supply no invented type), single-file-mode invariance, idempotence, check-mode findings, a 40-module recall sweep, and a ~100k-line/200-module index build plus sampled evidence checks marked `slow`. Plus ~120 focused tests across `test_project_*.py` for naming, scanning, resolution, the call graph, escapes, refresh invalidation, stub loading, version gates, project builds and the evidence bridge.

#### M3-15 — Wire the library keyword table into binding (audit finding)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Evidence (2026-11-08): `rules/library_calls.py::library_binding` is the
`bound_call` fallback after local and project bindings; it resolves
callees through module import aliases (`import json` → `json.dumps`,
`from os import replace` → `os.replace`) or the `builtins.` prefix,
refuses shadowed/rebound roots via `binding_counts`, `*`/`**`
expansions, duplicate keywords, over-long positional lists and calls
containing inner comments (writer safety), and synthesizes a
`BoundCall` so `calls.add-keywords` rewrites
`json.dumps(x)` → `json.dumps(obj=x)`, `re.sub(a,b,s,1)` → keywords,
`pow(2,3)` → `pow(base=2, exp=3)`. `KwSignature` gained `positional`
(positional-fillable names in order) and `var_positional`; the
generator records typeshed path, `typeshed_client` version and
generation date. Positional-only builtins (`getattr`, `isinstance`,
`posixpath.join`'s `*p`) stay positional — verified end to end.

**Tests:** `tests/test_rules_library_calls.py` (14 cases).
`rules/libkw.py` (37 568 generated lines) and `scripts/generate_libkw.py`
exist and `tests/test_rules_libkw.py` passes, but no module imports
`libkw`: `subprocess.run(cmd, True)`-style calls are still never keyworded.

**Scope:** `rules/resolve.py` (`CallBindings`), `rules/facts.py`
(`keyword_candidates`, `bound_call`), `cli/config.py` (`library-tables`).

**Acceptance:** a stdlib call listed as keyword-safe is keyworded end to end
(`fix_source` test + checker), a positional-only or unlisted callee is
not; the table's generation date and typeshed commit are recorded.

**Audit 2026-11-08:** still dead code — `libkw` is imported nowhere in
`src/`; `ProjectView.binding` resolves externals via typeshed stub
contracts (`LibraryIndex`), a different mechanism. `library-tables`
config is parsed but never consumed; no generation provenance in
`libkw.py`.

### Chapter 4. Precise types

#### M4-04 — R1: `optional_default`
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `x=None` defaults → `T | None`.
Evidence (2026-11-07): `hints._judge_optional` + `HintBasis.optional_default`
(confidence 0.95): `def f(x=None)` becomes `x: T | None = None` when every
call site that passes a value proves the same `T` from the argument's
syntax, at least one site passes a value, and the function does not
escape; sites that pass `None` add nothing. Works through `self.m(...)`
and `C().m(...)` sites. Tests: `tests/test_rules_optional_defaults.py`
(value sites, keyword sites, method sites, five refusals); gold family
`none_default` updated.
Known limits: no hint from the body alone (`if x is None`), and none when
no caller passes a value.

#### M4-05 — R2: `variadic_args`
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `*args: T`/`**kw: T` hints.
Evidence (2026-11-07): `HintIndex._judge_variadics` annotates `*args`/
`**kwargs` with the element type only when every closed-world call's extras
are syntax-proven to share one type; unpacked calls (`f(*xs)`), unbound
calls, escaped functions and calls without extras give no hint, and the
hint is never fed back as the name's type (it is a tuple/dict in the body).
Also: an unresolved expansion now counts as unknown evidence for the
parameters it may fill. Tests: `tests/test_rules_variadic_hints.py`.

#### M4-09 — `never_returns`
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** member completed for all raise paths.
Evidence (2026-11-07): `can_fall_off` handles `try`/`except`/`else`/
`finally` (`provable._try_can_fall_off`), so a `try` whose every branch
raises is `NoReturn` and one whose branches all return no longer gets `|
None`. Known limits: `while True` without `break` and `match` exhaustion
are still treated as falling off.

#### M4-10 — R10: `syntax_proven`
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — language-guaranteed returns
(`f"{x}"` → `str`, `not x` → `bool`) stop dying on `no candidate`.
Evidence (2026-11-07): `provable.provable_return_detail` reports whether a
proof is *language-guaranteed* (no parameter or variable type was read);
`HintBasis.syntax_proven` (confidence 0.99) is accepted without the
inference engine. Covers f-strings, `not x`, `len/str/repr/int/float/bool/
hash/id/ord/chr/format/ascii/bin/hex/oct`, `isinstance/issubclass/callable/
hasattr`, literals and locals built only from those, plus `T | None` for
paths that fall off the end. `can_fall_off` now analyses `try` statements.

**Tests:** `tests/test_rules_return_proofs.py`, gold flips in
`tests/test_gold_expansion.py` (`len`, `not`, `str`, f-string,
`falls-off`, `try-except`).
Known limits: `a == b` and `<` stay unproven (custom `__eq__`);
`with` statements are treated as non-suppressing.

#### M4-12 — R8: expression defaults
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** beyond `None`.
Evidence (2026-11-07): `hints._default_type` types scalar non-literal
defaults (`-1`, `len([])`, a once-bound constant's name) through
`expression_type`; the hint is written only when the inference candidate
agrees (same policy as literal defaults). Containers and calls with
unproven results stay refused. Gold family `default_expression`;
`tests/test_rules_expression_defaults.py`.

#### M4-15 — Container precision
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — literals/comprehensions → `list[int]`/
`dict[str,int]`/tuple shapes.
Evidence (2026-11-07): literals were already typed; `provable._Typer`
now types list/set/dict comprehensions (`range` → `int`, typed `str`/
`list[T]`/`set[T]` iterables, shadowing loop variables hidden, async
refused). `tests/test_rules_comprehension_types.py`; gold
`tainted/comprehension` now `list[int]`.

#### M4-20 — Taint rule is too conservative for argument-independent results (audit finding)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `def f(x): return len(x)`, `str(x)`, `repr(x)`, `int(x)`, `float(x)`, `bool(x)`, `isinstance(x, int)`, `callable(x)`, `hasattr(x, "a")`, `ord`, `chr`, `hash`, `id` all stay unannotated: the derived-return policy rejects any return that mentions an untyped parameter ("tainted by parameter x"), although the builtin's result type does not depend on the argument's type. In the realistic sample (`return len(self.items)`) this blocks `-> int`.

**Scope:** `rules/hints.py` (`_judge_derived`, taint), `rules/provable.py`
(`Constants.call_types`).

**Acceptance:** those builtins prove their result type with an untyped argument
(`__len__`/`__str__`/… are protocol-constrained to `int`/`str`); a gold
family `builtin_result` (≥ 15 cases) passes; no regression in the recovery
precision; `==`/`<` stay unproven (numpy-style `__eq__`).
Evidence (2026-11-07): `def f(x): return len(x)` now gets `-> int`,
`str(x)` → `str`, `isinstance(x, int)` → `bool`; the typer runs before the
taint check and the taint check only rejects returns whose proof actually
read an untyped name (`_Typer.reads`/`pure`). `call_types` gained
`ascii bin callable format hasattr hash hex id isinstance issubclass oct`.

**Tests:** `tests/test_rules_return_proofs.py` (refusals `abs`, `==`,
`sorted` stay unannotated).

### Chapter 5. Protocols and generics

#### M5-01 — P1: typed protocol member returns
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** from result use.

#### M5-02 — Typed protocol member params
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** from arguments incl. flow-typed.

#### M5-03 — `async def` protocol members
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** (replaces `await` refusal).

#### M5-05 — P4: `__call__` callback protocols
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** with keyword names preserved
(`p()` no longer refused).

#### M5-08 — Collision-safe member-name allocation
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** (arg0/self regression).

#### M5-14 — Bound TypeVars
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `T bound=CloseProtocol` for
`x.close(); return x` shapes.
Evidence (2026-11-08 audit): `_bound_plan`/`_bound_members` in
`rules/typevars.py` prove uniform member-call signatures;
`typing.synthesize-typevar` emits `T = TypeVar("T", bound=Proto)` via
`_insert_bound_protocol`; catalog fix registered; tests
`test_bound_typevar_for_member_use_and_return` and
`..._refuses_ambiguous_member_arity` in `test_rules_typevar_fix.py`.

#### M5-15 — Constrained TypeVars
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — exhaustive `isinstance` branches/
overloads only.
Evidence (2026-11-08 audit): `_constrained_plan`/`_isinstance_guard` emit
`TypeVar("T", int, str)` only when every return is a bare `return x`
inside isinstance-guarded `if` bodies (≥2 constraints); overloads and
fallthrough refused. Tests `test_constrained_typevar_*` in
`test_rules_typevar_fix.py`.

#### M5-17 — Element pass-through
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `Iterable[T] → list[T]`;
`items[0] → Sequence[T] → T`.
Evidence (2026-11-08 audit): `_element_plan`/`_return_shape` emit
`Sequence[T] -> T` for subscripts and `Iterable[T] -> list[T]`/
`tuple[T, ...]` for constructors, with `collections.abc` imports;
string subscripts refused. Tests `test_element_*` in
`test_rules_typevar_fix.py`.

#### M5-18 — `Self`
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** for `return self`/`cls()` returns.
Evidence (2026-11-08 audit): `_receiver_return` proves every return is
`return self`/`return cls()`; `typing.synthesize-self` emits `-> Self`
gated on `facts.target.self_type` (≥3.11). Tests
`test_self_return_gets_self_annotation`,
`test_classmethod_constructor_gets_self_annotation`,
`test_self_refuses_other_receiver_uses`.

### Chapter 6. Keyword arguments

#### M6-01 — Danger matrix → ~60 tests
- **Status:** done
- **Priority:** P1
- **Area:** Testing / QA
- **Readiness:** done

**Context:** decorators/`__getattr__`/
`__call__`/Liskov-violating overrides/C-impl posonly/renamed params/
rebinding/conditional defs/callback containers/`functools.wraps`-less
wrappers.

**Evidence:** `tests/test_rules_kwargs_danger.py` — 70 matrix rows run
through `fix_source` at `FixSafety.guarded`: 50 pass, 20 strict-xfail.
Coverage: decorator/factory/`wraps`-less wrappers on functions and
methods, `__getattr__`/`__getattribute__`/`__call__`/`getattr`
dispatch, `/` `*` `**` end-to-end, `functools.partial`, overrides with
renamed/added/posonly params and instance-attribute stores, diamonds,
`super()`, rebinding (`global`/`nonlocal`/lambda/shadowing/conditional
defs/`del`), callback containers, builtins/C-impl callees, dataclass/
NamedTuple/attrs/enum/TypedDict receivers, and proven-safe baselines.
The 20 strict xfails pin real unsound fixes for M6-02+: `setattr`/
`__dict__`/`globals()` rebinding invisible to `binding_counts`,
`__getattribute__` interception of `self.m`, class-body rebinding of a
method name not tracked by `MethodIndex._find`, metaclass `__call__`
vs `__init__` signature disagreement, `__new__`/`__init__` mismatch,
and unchecked class decorators.

#### M6-03 — Library keyword table
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — curated versioned stdlib signatures
(typeshed-generated, test-verified); never C posonly builtins; third-party
via allow-list only.

**Evidence:** `scripts/generate_libkw.py` parses the typeshed bundle shipped
with `typeshed_client` into `src/astart/rules/libkw.py` — ~11 947
`KwSignature` entries keyed `module.qualname`, stdlib first, every
positional-only parameter (`/` markers and the `__name` convention)
plus `self`/`cls` receivers excluded, `**kwargs` callees recorded as
`any_keyword`; no third-party stubs are bundled so none can enter
except through a future explicit allow-list. Tests:
`tests/test_rules_libkw.py` (known signatures, unknown callees,
posonly/receiver exclusion, ordering). Wired into binding → M3-15.

#### M6-10 — Class-body rebinding of a method name (audit: 9 strict-xfail rows)
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `descriptor-shadows-method`, `descriptor-before-method`,
`staticmethod-assign-shadows`, `partial-assign-shadows`,
`del-method-class-body`, `annotated-assign-shadows`, `tuple-assign-shadows`,
`for-target-shadows-method` and one more row in
`tests/test_rules_kwargs_danger.py`: any assignment, `del`, `for`/`with`/
import target or annotated assignment of the method's name in the same
class body makes the `def` unreliable, but binding counts ignore class
bodies.

**Scope:** `rules/methods.py` (`MethodIndex._find`, `is_safe`),
`rules/resolve.py::binding_counts`.

**Acceptance:** those rows flip from strict-xfail to passing (remove their
reason) and the keyworded call is refused whenever the name is bound more
than once in the class body.

#### M6-11 — Constructor hooks (audit: 6 strict-xfail rows)
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `metaclass-diff-names`, `metaclass-posonly`, `new-init-mismatch`,
`new-init-swapped`, `new-init-diff-arity`, `class-decorator`: a class
with a metaclass `__call__`, a `__new__` that disagrees with `__init__`, or
a decorator that is not a neutral `@dataclass` still gets its constructor
calls keyworded, because `trusted_binding` vets the `__init__` function,
not the class.

**Scope:** `rules/resolve.py` (`_vet`, `trusted_binding`),
`rules/methods.py`.

**Acceptance:** constructor calls are refused when the class (or an in-module
base) has a metaclass, defines `__new__`, or is decorated; the 6 rows pass.

#### M6-12 — Dynamic rebinding markers (audit: 4 strict-xfail rows)
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `setattr-instance-rebind`, `setattr-class-rebind`,
`object-setattr-rebind`, `dict-attribute-rebind`, `globals-rebind`:
calls through `setattr(...)`, `object.__setattr__`, `__dict__[...] = ...`
or `globals()[...] = ...` can replace a callee invisibly.

**Scope:** `rules/resolve.py::binding_counts` / `MethodIndex`.

**Acceptance:** a module that contains such a marker for a name (or any
unnamed `setattr`/`globals()` write) refuses keyword rewrites of calls to
that name; the rows pass; a test shows an ordinary module is unaffected.

#### M6-13 — `__getattribute__` interception (audit: 1 strict-xfail row, `getattribute-override`)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** A class defining `__getattribute__` can redirect `self.m`/`obj.m`; refuse method-call keyword rewrites on it and on classes inheriting it.

**Acceptance:** the row passes.

### Chapter 7. Speed and shipping

#### M7-03 — Incremental content-hash cache
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** across runs.

**Audit 2026-11-07 (not started):** the analyzer already reuses abstract-
interpreter transfer across in-process mutations
(`AbstractInterpreter.recompute_module`/`incremental_reused`), but a
persistent content-hash cache needs run-level storage and CLI wiring —
deferred to the M7-16 surface together with config/reporters.
Done 2026-11-08 (agent: claude): `astart fix --cache` (opt-in, single-file
mode) stores each file's result in `.astart_cache/<sha256>.json`, keyed on
the file text and path plus a fingerprint of the run options, the checker,
`ruff --version`, the project's ruff/pyright/mypy/pyproject config and the
tool's own `.py`/`.json` files (so any code or rule change invalidates it).
Corrupt or old-schema entries are misses; writes are atomic. Measured on
`statistics.py`: 11.3 s cold, 0.34 s cached. Project mode is excluded (a
file's result depends on other files). Open: a project-aware key (hash of
the callee modules a file's result read) and cache pruning. Code:
`cli/cache.py`; tests: `tests/test_cli_cache.py`.

#### M7-07 — `[tool.astart]` pyproject config
- **Status:** done
- **Priority:** P1
- **Area:** DevOps / Release
- **Readiness:** done

**Context:** — rules,
select/ignore, safety ceiling (locked: configurable aggressiveness per
profile), per-path overrides, target version, protocol/typevar style,
import placement, library tables.

**Evidence:** `src/astart/cli/config.py` + `src/astart/cli/ignores.py` —
unwired loader covering `profile`, `select`/`ignore`, `min-confidence`,
`safety-ceiling` (`FixSafety`), `target-version`, `checker`,
`exclude`, `library-tables`, a `[tool.astart.params]` scalar table
(protocol/typevar style, import placement and other rule params ride
it) and `[tool.astart.overrides."<glob>"]` per-path tables that merge
select/ignore/profile/confidence/ceiling/version/params in file
order. `ignores.resolve` expands a selection through catalog
`Profile`s (rule set, severity overrides, param layering
rule < profile < selection, ceiling fallback) and
`apply_ignores`/`selected_rules` enforce it; unknown profile keys
raise `ConfigError`. Tests: `tests/test_cli_config.py`,
`tests/test_cli_reports.py`.

### Chapter 8. Ontology and inference core

#### M8-23 — New `Final` constants join an existing `Constants` class (requested 2026-11-07)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `typing.add-final` no longer leaves a freshly made `NAME: Final[T] = …` at module level when the module already has exactly one `class Constants`: `rules/grouping.py` (`find_group`, `move_into`) moves the statement into the class (after its docstring and existing attributes, trailing comment kept), rewrites every use to `Constants.NAME`, adds `NAME: Grouped module constant.` to the class docstring's `Attributes:` section when there is one, and inserts the `Final` import before the class. It stays a module global when the move could break something: the name is in `__all__`, declared `global`/ `nonlocal`, already defined in the class, read by the class body, or read at import time (defaults, decorators, module-level code) before the class exists; and when the module has no or several `Constants` classes.

**Tests:** `tests/test_rules_constants_group.py` (move, no class, rerun is a
no-op, five refusals, default after the class, several constants,
docstring section present/absent).
Known limits: other modules that do `from this import NAME` are not
known — a project-wide check belongs to M3-01/M3-03; lowercase module
variables and constants that are already `Final` at module level are not
moved (the M8-09 loose-constants detector reports those).

#### M8-24 — Writer replaces elements of a child list with atoms (needed by M8-23)
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** `formatting.Writer._atom_replacements` patches a same-length expression list in place when `Name`/`Attribute`/`Constant` nodes replace elements — `arguments.defaults` previously raised "Changing arguments.defaults requires syntax regeneration", which made the whole `typing.add-final` fix fail to write back. It also keeps the original spacing for swapped call arguments (`call(  2, 1, )` stays as written).

**Tests:** `tests/test_format_list_element_replacement.py`,
`tests/test_format_ast.py::test_swapped_atoms_keep_the_original_spacing`.
Known limits: non-atom replacements (e.g. a `BinOp`) still fall back to
local canonical printing, because they may need parentheses.

#### M8-15 — Rule authoring kit
- **Status:** done
- **Priority:** P3
- **Area:** Documentation
- **Readiness:** done

**Context:** — scaffold + example-as-test
generator.

**Evidence:** `docs/rule-authoring.md` — rule anatomy, declarative vs
procedural detection, the example-as-test contract (`verify_catalog`
enforces both polarities), fix/safety rules, and the authoring
checklist including the M8-22 registration deferral.

#### M8-16 — Fix verified wrong types
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `"hi " + name` → `int` bug.
Evidence 2026-11-07: no longer reproduces — `"hi " + name` infers `str`
for typed operands and `Unknown` (never `int`) for mixed/untyped ones;
the hint layer refuses the unproven return (`Rejection.not_provable`).
Fixed by the `syntax_proven`/`provable_return_detail` work on the
main-agent line; verified via `infer_type` probes.

#### M8-17 — `list(d)` → items-not-keys
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** inference fix.
Evidence 2026-11-07: `semantic/type_inference.py::_builtin_call` +
`_iterated_element` — `list`/`set`/`tuple`/`frozenset` constructors now
derive the element type from the iterated argument (dict → keys,
heterogeneous tuple → element join, `str` → `str`, `bytes` → `int`);
`dict(d)` preserves `dict[K, V]`. `list(d)` on `dict[str, int]` →
`list[str]`. Cases added to `tests/test_type_inference.py`.

#### M8-18 — `seq[0]` → `Sequence[int]` over-broad
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** fix.
Evidence 2026-11-07: `seq[0]` on `Sequence[int]` infers `int`;
`infer_subscript` additionally types `str[i]` → `str` and `bytes[i]` →
`int` (previously `Unknown`). Regression cases in
`tests/test_type_inference.py`.

#### M8-19 — Imported-constructor argument typing
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** —
`Path("x")` args typed from the constructor signature (beyond the D3
result-type fix).
Evidence 2026-11-07: `_IMPORTED_CONSTRUCTOR_PARAMS` +
`_resolve_imported_constructor` in `semantic/type_inference.py` give
`datetime.date/datetime/time/timedelta`, `decimal.Decimal`,
`fractions.Fraction`, `pathlib.Path/PurePath` and `uuid.UUID` curated
`CallableContract`s resolved through `_contract_call`, so calls yield
the constructor type and arguments pick up declared parameter types
via the existing `_annotate_argument_source`/`_backward` flow
(`Path(p)` → `p: PathLike[str] | str`, `UUID(hex=u)` → `u: str | None`).
Rebound imports and local shadows stay `Unknown`; regression tests in
`tests/test_type_inference.py`.

#### M8-20 — `self.` receiver typing in the analyzer
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

### Chapter 9. Cross-cutting engineering

#### EV-01 — Exactus gate evidence, 2026-11-07
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Unified `exactus` run:
6/6 PASS*, 0 files with issues; 1616 tests, `__main__.py` 95%, total
94.95%; kwargs_typehints unresolved callees 0 after binding all
subscript/unknown-receiver callees to annotated locals.

#### CC-05 — User-facing evidence ladder + refusal catalogue
- **Status:** done
- **Priority:** P2
- **Area:** Documentation
- **Readiness:** done

**Context:** ("why wasn't X annotated?" keyed by `Rejection`/`SkipCode`).

**Evidence:** `docs/evidence-ladder.md` (E0–E6 levels, the guarded-fix
acceptance rule, confidence table) and `docs/refusals.md` (all 14
`Rejection` + 6 `SkipCode` values, keyed by code, with per-reason
remediation); `docs/benchmarks.md` updated.

### Chapter 10. Contract negotiation

#### F-01 — Data model `negotiation/model.py`: `Relation` (assigns, returns, argument, call_result,…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Data model `negotiation/model.py`: `Relation` (assigns, returns, argument, call_result, element, key, value, attribute, instance_field, class_field, narrows, requires, operator, context_enter, context_exit), `Polarity` (union, intersection, declaration, capability, conflict), `Origin` (syntax, declared, call_sites, default, inferred), frozen `Candidate`, `Contract`, `Conflict`.

**Evidence:** `tests/test_negotiation_model.py`.

#### F-02 — Provenance: a candidate carries the set of `Origin`s that support it; `independent` means…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Provenance: a candidate carries the set of `Origin`s that support it; `independent` means "has an origin other than `inferred`"; merging equal types unions their origins. Evidence: `tests/test_negotiation_model.py`.

#### F-03 — Type algebra `negotiation/algebra.py` (`union`, `intersect`, `members`) over type…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Type algebra `negotiation/algebra.py` (`union`, `intersect`, `members`) over type strings, deterministic and insertion-order independent: flatten, dedupe, `Never` absorbed, `bool | int` → `int`, covered `Literal[...]` dropped, `None` last, member limit (3) → refuse, `object` kept visible so policy can refuse it. Intersection: numeric tower, `None`, generics argument-wise, unrelated builtins empty, unknown class relations *undecided* (never guessed). Lossy collapses (`int | float` → `float`, `list | set` → `Collection`) are NOT here → F-24.

**Evidence:** `tests/test_negotiation_algebra.py` (farm normalization table).

#### F-04 — `negotiation/beliefs.py` `Belief`: add by polarity (union keeps the best confidence per…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `negotiation/beliefs.py` `Belief`: add by polarity (union keeps the best confidence per type and merges origins; intersection narrows every candidate and records a conflict on empty; declaration is hard — later disagreeing candidates become conflicts; conflict polarity records), `entropy()`, `settle()` → one type or `None` (open conflict, empty belief, or over the member limit give `None`). Supersedes Q-37's `SlotTable`. Evidence: `tests/test_negotiation_beliefs.py`.

#### F-05 — `negotiation/graph.py` `ContractGraph`: nodes by stable path text, edges with…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `negotiation/graph.py` `ContractGraph`: nodes by stable path text, edges with deterministic outgoing/incoming indexes (sorted, insertion-order independent), seeds. Evidence: `tests/test_negotiation_graph.py`.

#### F-06 — `negotiation/negotiator.py` `Negotiator.solve`: queue of ants, wormhole memo `(path,…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** `negotiation/negotiator.py` `Negotiator.solve`: queue of ants, wormhole memo `(path, type, polarity)`, forward/backward decay, minimum confidence, iteration and event caps, entropy/no-change stabilisation, deterministic order, result with beliefs, snapshots and conflicts. Evidence: `tests/test_negotiation_solver.py` (cycles `x = y; y = x`, `x = []; x.append(x)`, order independence).

#### F-07a — `negotiation/transfer.py`: first transfer table
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** — identity relations, `element` forward (`list[T]` → `T`), no backward element guess. Evidence: `tests/test_negotiation_solver.py`.

#### F-08 — Builder: assignments (plain, annotated = declaration, augmented, tuple unpacking,…
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Builder: assignments (plain, annotated = declaration, augmented, tuple unpacking, walrus), one node per binding with scope-qualified paths (`mod.f.x`). Done 2026-11-08: `negotiation/builders.py` — single-binding locals (`x = e`, `for x in e`) get scope-qualified nodes; names bound twice, by `global`/`nonlocal`, imports, nested defs, handlers, annotated or augmented assignments get none and mark dependants opaque. Not covered (left opaque, never guessed): tuple unpacking, walrus, augmented assignment.

#### F-09 — Builder: returns and calls
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `return e` → `returns`; a bound call links argument → parameter and return → call result; unbound/dynamic callees add no edge. Done 2026-11-08: returns, falls-off-the-end (`None`), bare `return`, bound calls (argument→parameter via `CallBindings`, return→call result). Refusals found by the shadow run and pinned in `tests/test_negotiation_module.py`: stub/abstract bodies, protocol dunders, `NoReturn`, generators, constructor calls (the class, not `__init__`'s `None`), un-awaited coroutines.

#### F-10 — Builder: containers
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — literals, comprehensions, `append/extend/add/update/insert/setdefault`, subscript stores, `for x in xs` (`element`), `dict` key/value. Progress 2026-11-08: `for x in xs` (`element`) and `xs[i]` (`item`, list/dict/str/bytes) done; `append/extend/add/update/setdefault`, subscript stores and comprehensions still open. Done 2026-11-08: `negotiation/containers.py` — an empty `[]`/`list()`/`set()` local is typed from what is `append`ed/`insert`ed/`add`ed (relations `list_of`/`set_of`), only while every use of it is understood; `extend`/`update`, passing it to a function, closures and any unknown use make it opaque. Dict stores and comprehensions stay open (→ F-10b).

#### F-11 — Builder: attributes
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `self.x` writes and reads (`instance_field`, using `Attributes` agreement), class fields, properties; refuse on the same conditions as `attributes.py`. Done 2026-11-08: instance attributes become nodes `Class.attr` when every write to that name in the module is a plain `self.attr = value` in one safe class (no dynamic access, inheritance clash, class-level binding, external write or rebound receiver); writes flow from their values (so `self.x = x` carries the parameter's call-site evidence) and `self.attr` reads link to the node.

#### F-12 — Builder: narrowing
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** — `isinstance`, `is None`, truthiness, `assert`, early return — as intersection contracts scoped to the branch (branch-suffixed paths), reusing `provable._flow_returns` ideas (M2-09). Done 2026-11-08: `negotiation/narrowing.py` + builder — `is None`/`is not None`/`isinstance`/truthiness/`not` tests narrow a name on each arm and past an `if` whose other arm cannot fall through; narrowing is a lazily applied *constraint* on the belief (so the result does not depend on arrival order) and values leaving a narrowed node are narrowed. Closures and comprehensions never inherit it.

#### F-14 — Builder: operators using the typer's tables (numeric tower, str/bytes/list concat,…
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Builder: operators using the typer's tables (numeric tower, str/bytes/list concat, comparisons → `bool`). Done 2026-11-08 as *derived nodes* (`graph.Derived`, `negotiator._derive`): any expression over operand nodes — arithmetic, comparisons, `not`/`and`/`or`, conditional expressions, f-strings, tuple/list/set/dict displays, builtin calls — becomes a template whose operands are placeholders; the existing syntax typer (`provable.expression_type`) evaluates it as soon as every operand has settled, so one set of operator rules serves both layers. Unsettled or mixed-type operands (`int | float`) give no type and mark the node lost. Tests: `test_negotiation_module.py` (arithmetic, mixed, tuple, comparison/f-string, unknown name, chain).

#### F-35 — Protocol-dunder results in the negotiator (`__len__` → `int`, `__exit__` → `bool | None`,…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Protocol-dunder results in the negotiator (`__len__` → `int`, `__exit__` → `bool | None`, …): `Origin.protocol`, one rule shared with the hint index (`hints.protocol_result_for`). Shadow gap closed: 193 annotations (158 exact) that the first builders blocked.

#### F-36 — Calibrated `bool` returns in the negotiator: returns that are boolean by syntax…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Calibrated `bool` returns in the negotiator: returns that are boolean by syntax (`hints.boolean_returns`) seed `bool` with `Origin.calibrated`, accepted only when the engine proposes the same type. Shadow gap closed: 101 annotations.

#### F-38 — Lost contributions: a transfer that yields nothing for a union/declaration contract…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Lost contributions: a transfer that yields nothing for a union/declaration contract (iterating a user class, an unrecognised container) no longer vanishes silently — the target is recorded in `Negotiation.lost` and treated as opaque with everything downstream (`policy.blocked_nodes`). Test fails without the change (`test_a_dropped_contribution_makes_the_node_unknown`).

#### F-39 — Opacity reasons: every opaque node records why (`Built.why`), the groundwork for `astart…
- **Status:** done
- **Priority:** P1
- **Area:** Backend
- **Readiness:** done

**Context:** Opacity reasons: every opaque node records why (`Built.why`), the groundwork for `astart explain` (F-26) and the to-do list for coverage: on `dev/untyped.py` the direct causes of the reportable nodes are unprovable calls (46), unknown names (46), functions that escape as values (28), starved parameters (24), stub bodies (20), calls the binder refuses (16), tuples (14), generators (7).

#### F-42 — Names that exist when an annotation is evaluated: a negotiated parameter or return hint…
- **Status:** done
- **Priority:** P0
- **Area:** Backend
- **Readiness:** done

**Context:** Names that exist when an annotation is evaluated: a negotiated parameter or return hint may name a module class only if that class is completely defined before the `def` runs and does not contain it (functions nested in function bodies are exempt); a negotiated hint naming the module's own class is never imported over (`imports.ensure_names(skip=…)`). Found by the semantic-equivalence run on `rfc3986` (`NameError` on import) and by `uuid.py` in the runner corpus.

**Tests:** `tests/test_rules_negotiated_fix.py`.

#### F-19 — Shadow mode: run the negotiator next to `HintIndex`, record every difference (new hint,…
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Shadow mode: run the negotiator next to `HintIndex`, record every difference (new hint, dropped hint, different type) and score it against the originals with `recovery`; flag `benchmarks recovery --negotiate shadow`. No behaviour change. Done 2026-11-08: `python -m benchmarks.shadow DIR --jobs N [--json FILE]` runs the hint index and the negotiator on the same stripped source and scores both against the originals. External corpus (165 modules, 12 789 truths, 0 crashes): written by both and identical 2 138 correct / 150 compatible / 2 wrong; negotiation only 32 correct / 10 compatible / **0 wrong**; hint index only 338 correct / 46 compatible / 4 wrong (attributes, default-only tiers, `x=None` bodies are not built yet). Never contradicts the hint index where both write. See `docs/benchmarks.md`.

### Chapter 11. Untyped to typed conversion

#### P-01 — Pair benchmark and accepted baseline: `benchmarks/pair.py`, `tests/pairs/`,…
- **Status:** done
- **Priority:** P0
- **Area:** Testing / QA
- **Readiness:** done

**Context:** Pair benchmark and accepted baseline: `benchmarks/pair.py`, `tests/pairs/`, `tests/test_bench_pair.py` (slow).

### Chapter 12. Typer and small tasks

#### Q-01 — String methods that return `str`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `_Typer._call` (`provable.py`, ≈ line 410) — it handles only `Name` callees today (`node.func.id` looked up in `Constants.call_types`) — add a branch at the top: `if isinstance(node.func, Attribute):` type the receiver with `self.type_of(node=node.func.value)` and use `node.func.attr` as the method name; return `None` for anything not in the table. When the receiver types to `"str"` and the method is one of `upper lower strip lstrip rstrip title capitalize casefold swapcase replace join format zfill center ljust rjust expandtabs removeprefix removesuffix`, the call is `"str"`. Put the names in `Constants` as `str_to_str: Final[frozenset[str]]`. Tests: `"a".upper()` → `str`; `x.upper()` with unknown `x` → `None`; `"a".bogus()` → `None`.

#### Q-02 — String methods that return `bool`/`int`: `startswith endswith isdigit isalpha isalnum…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** String methods that return `bool`/`int`: `startswith endswith isdigit isalpha isalnum isspace islower isupper isidentifier isnumeric isdecimal istitle` → `bool`; `find rfind index rindex count` → `int`. Same recipe and test shape as Q-01.

#### Q-03 — `str % anything` → `str` (printf formatting)
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `_binop` (`BinOp` handler): left types to `"str"` and `isinstance(node.op, Mod)` → `"str"`. Tests: `"%s" % 1` → `str`; `1 % 2` stays `int`.

#### Q-04 — List concatenation: in `_binop`, when both sides type to the same `list[...]` string and…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** List concatenation: in `_binop`, when both sides type to the same `list[...]` string and op is `Add` → that same type. Tests: `[1] + [2]` → `list[int]`; `[1] + ["a"]` → `None`.

#### Q-05 — Subscripts
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add a `Subscript: self._subscript` handler. Rules: receiver `list[T]` with an `int`-typed index (`Constant` int) → `T`; receiver `list[T]` with a `Slice` → `list[T]`; `str` with int index or `Slice` → `str`; `dict[K, V]` with a key typed `K` → `V`; anything else → `None`. Parse the inner type of `list[T]` by stripping the `list[` prefix and final `]` (see `_item_type` in the same file for the pattern; it only handles one level, which is enough). Tests: one per rule plus two refusals.

#### Q-06 — `abs`, `round`, `min`, `max`, `sorted`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `Constants`, extend the call handling: `abs(x)` with `x` typed `int`/`float` → same type; `round(x)` with ONE argument typed `float` or `int` → `int`; `sorted(x)` with `x` typed `list[T]` → `list[T]`; `min`/`max` with two or more arguments all typed the same scalar → that scalar. Refuse everything else.

#### Q-07 — `list(x)`, `set(x)`, `tuple(x)` with a typed argument: `list(list[T])` → `list[T]`;…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `list(x)`, `set(x)`, `tuple(x)` with a typed argument: `list(list[T])` → `list[T]`; `set(list[T])` → `set[T]`; `list(str)` → `list[str]`. Anything else `None`. (`tuple` only for `tuple[...]` input.)

#### Q-08 — `dict.get`/`list.copy`/`dict.keys` are NOT in scope; add a comment-free refusal test…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `dict.get`/`list.copy`/`dict.keys` are NOT in scope; add a comment-free refusal test proving `{"a": 1}.get("a")` is `None` (it is `int | None`, which must not be claimed).

#### Q-09 — Add family `variadic` (also add it to the `expected` set in…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add family `variadic` (also add it to the `expected` set in `test_gold_covers_every_rejection_family`): 8 cases. Four hinted: `f(*a)` called `f(1, 2)` → `f.a` `"int"`; `f(**k)` called `f(x="s")` → `"str"`; and two more of your choice. Four refused: mixed types, `f(*xs)` unpack call, no extras, escaped function (`g = f`).

#### Q-10 — Add family `attribute_read` with 6 cases mirroring `tests/test_rules_attribute_reads.py`…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add family `attribute_read` with 6 cases mirroring `tests/test_rules_attribute_reads.py` (return of `self.x`, arithmetic, Optional, conflicting writes, rebound `self`, two classes with different attribute names).

#### Q-11 — Add family `comprehension` with 6 cases mirroring…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add family `comprehension` with 6 cases mirroring `tests/test_rules_comprehension_types.py` (list/set/dict, shadowing, async, unknown iterable).

#### Q-12 — Add family `multi_binding` with 6 cases mirroring…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add family `multi_binding` with 6 cases mirroring `tests/test_rules_multi_binding_locals.py`.

#### Q-13 — CRLF: new `tests/test_rules_line_endings.py`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Feed a source using `\r\n` line endings (`"def f(x):\r\n    return 1\r\n"`) to `fix_source`; assert the output contains no bare `\n` (every `\n` is part of `\r\n`). If it fails, do NOT fix the writer; record the failing output in the task and mark it `BLOCKED`.

#### Q-14 — Hostile inputs: new `tests/test_rules_hostile_inputs.py`, parametrized over: empty…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Hostile inputs: new `tests/test_rules_hostile_inputs.py`, parametrized over: empty string, only comments, only a docstring, a BOM at the start (`"﻿x = 1\n"`), tabs for indentation, a 5000-character line, a file without trailing newline, `"x = (\n"` (unparsable). For each, `fix_source(...)` must not raise; for the unparsable one assert the result has `parse_error` set (look at `FixResult` fields).

#### Q-15 — Determinism across hash seeds: new `tests/test_rules_determinism.py`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** For 5 corpus files (take the first five of `sorted(Path("tests/corpus").glob("*.py.txt"))` under 300 lines), run a subprocess `python -c` that calls `fix_source` and prints the result, once with `PYTHONHASHSEED=1` and once with `PYTHONHASHSEED=2`, and assert both outputs are identical. Mark the test `@pytest.mark.slow`.

#### Q-16 — Convention guard (CC-06): new `tests/test_conventions.py` with three tests that scan…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Convention guard (CC-06): new `tests/test_conventions.py` with three tests that scan `src/` and `tests/` text: (a) no line contains `# noqa`; (b) no line contains `type: ignore`; (c) no line matches `^import ast$`. Allow the file itself. Report offenders as `path:line` in the assertion message. Done inside `tests/test_conventions.py` together with Q-51 and Q-17: `test_no_suppression_comments` covers (a)+(b) and `test_no_bare_ast_import` covers (c). The needles are regexes anchored on `#` (`#\s*noqa\b`, `#\s*type:\s*ignore\b`) because a bare substring scan flags the detector's own vocabulary in `src/astart/ast.py`, `rules/suppressions.py` and the procedural fixture — string literals, not suppression comments.

#### Q-17 — Constants guard: in the same file, assert that every class named `Constants` in…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Constants guard: in the same file, assert that every class named `Constants` in `src/astart` is decorated `@final` (use `ast` to parse each file and check `decorator_list`).

#### Q-18 — README flag guard: new `tests/test_readme_flags.py`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Build the parser by calling `astart.__main__.main(argv=["fix","--help"])` and capturing stdout with `capsys` (it exits via `SystemExit`; catch it), pull every `--flag` token, and assert each appears in `README.md`.

#### Q-19 — `astart --version`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `__main__.py` add `parser.add_argument("--version", action="version", version=<string>)` where the string comes from `importlib.metadata.version("astart")`; if the package is not installed catch `PackageNotFoundError` and use `"0+unknown"`.

**Test:** `main(argv=["--version"])` raises `SystemExit` with code 0 and prints
a non-empty line.

#### Q-20 — `astart rules`: new subcommand printing one line per rule: `CODE  key  severity  title`,…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `astart rules`: new subcommand printing one line per rule: `CODE  key  severity  title`, sorted by code. Get rules from `load_default_catalog(registries=default_registries()).rules` (fields `.code .key .severity .title`). Test: output contains `TYP005` and `STR001`, and has as many lines as rules.

#### Q-21 — `astart explain CODE`: prints the rule's `rationale`, then each example's source with…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `astart explain CODE`: prints the rule's `rationale`, then each example's source with `triggers` shown as "flagged" or "clean". Unknown code → exit status 2 and a message on stderr. Tests for both paths.

#### Q-22 — `docs/rules.md` generated by a new script `scripts/generate_rule_docs.py` (iterate the…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `docs/rules.md` generated by a new script `scripts/generate_rule_docs.py` (iterate the catalog; one `##` heading per code with title, severity, rationale, the fix keys). Add `tests/test_rule_docs.py` asserting every catalog code appears in `docs/rules.md`. Commit the generated file. Done: `PYTHONPATH=src python scripts/generate_rule_docs.py` writes `docs/rules.md` (10 rules, sorted by code); `tests/test_rule_docs.py` passes.

#### Q-23 — `docs/architecture.md`: one paragraph per module in `src/astart/rules/` (`ls` it; read…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `docs/architecture.md`: one paragraph per module in `src/astart/rules/` (`ls` it; read each file's module docstring for the text; do not invent). Link it from the README. Done: 53 modules, docstring text verbatim under `## \`name.py\`` headings; linked from the README intro.

#### Q-24 — `CHANGELOG.md`: one `## 2026-11-07` heading, bullets copied from the entries in section…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `CHANGELOG.md`: one `## 2026-11-07` heading, bullets copied from the entries in section 17 of this file dated today. No new claims. Done with Q-53: one `CHANGELOG.md` carries the `## 2026-11-07` bullets.

#### Q-25 — `.pre-commit-hooks.yaml` (M7-11): one hook, id `astart-fix`, `entry: astart fix --check`,…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `.pre-commit-hooks.yaml` (M7-11): one hook, id `astart-fix`, `entry: astart fix --check`, `language: python`, `types: [python]`. Test: the file exists and contains `id: astart-fix` and `--check`.

#### Q-26 — `.github/workflows/ci.yml`: on push/pull_request, Python 3.12, steps: install with `pip…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `.github/workflows/ci.yml`: on push/pull_request, Python 3.12, steps: install with `pip install -e .` plus `pip install pytest ruff` (pyproject has no `dev` extra; verify with `grep -n optional-dependencies pyproject.toml` and use it if it exists), `ruff check src tests`, `pytest -m "not slow"`. No tests needed; just keep it minimal and valid YAML.

#### Q-27 — `--exclude GLOB` for `astart check` and `astart fix` (repeatable)
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `src/astart/cli/discovery.py` edit `discover_files(*, paths)` and its helper `_walk(*, root)`; skip any path whose posix string matches `fnmatch` for any glob. Add the argument in `__main__.py` like `--source-root` was added (search for `source-root` to copy the pattern end to end: argparse → settings dataclass → command). Tests: a tmp tree with `a.py`, `skip/b.py`, exclude `skip/*` → only `a.py` is processed. Done: `discover_files(*, paths, exclude=())` matches `fnmatch` globs against absolute and root-relative posix paths; explicit files are kept unless a glob matches; directory walks skip excluded entries. Wired through `FixCommandSettings`/`CheckCommandSettings` → `__main__` for both subcommands. Tests in `tests/test_cli_discovery.py` and `tests/test_cli_check.py`.

#### Q-29 — Grow the corpus (M1-07 beyond 113): copy 15 stdlib modules not yet present to…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Grow the corpus (M1-07 beyond 113): copy 15 stdlib modules not yet present to `tests/corpus/<name>.py.txt` (candidates: `textwrap`, `shlex`, `string`, `stat`, `tokenize`, `traceback`, `types`, `uuid`, `weakref`, `zipapp`, `secrets`, `sched`, `queue`, `imghdr`-free ones; use `python -c "import <m>; print(<m>.__file__)"` for the path). Then run `PYTHONPATH=src:. python -m benchmarks recovery --json /tmp/r.json` and `python -m benchmarks gate --report /tmp/r.json`. If the gate prints FAIL, write the FAIL lines under this task and STOP (do not edit the baseline). Done: added `copy`, `codeop`, `getopt`, `hashlib`, `hmac`, `genericpath`, `pyclbr`, `pprint`, `plistlib`, `random`, `runpy`, `site`, `symtable`, `tracemalloc`, `warnings` (corpus 113 → 128). Recovery: 324 truth, 38 correct, **0 wrong, 0 crashes, 0 new errors**, precision 100%, recall 11.7%, 156.9 s; `gate` printed **PASS** — baseline untouched.

#### Q-30 — Five more semantic projects (M1-12): add entries to `benchmarks/projects.json` copying…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Five more semantic projects (M1-12): add entries to `benchmarks/projects.json` copying the shape of an existing entry. Pick small pure-Python packages (`six`, `toml`, `tomli`, `more-itertools`, `typing-extensions`), pin the exact latest version and sdist URL from PyPI, fill the same fields as the others. Run `python -m benchmarks semantic` and record the result per project; a project that is not `equivalent` is reported, not fixed. Done: added `toml` 0.10.2, `tomli` 2.5.0, `more-itertools` 11.2.1, `tomlkit` 0.13.3, `boltons` 25.0.0 (smoke snippets verified against the pinned sdists before pinning). `python -m benchmarks semantic`: all 15 projects **PASS** — identical imports and smoke results after `fix`, including the five new ones (fixes applied: toml 66, tomli 67, more-itertools 321, tomlkit 130, boltons 1049).

#### Q-31 — The ≈ 50k-line throughput row (M1-10): concatenate corpus files into one 50k-line module…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** The ≈ 50k-line throughput row (M1-10): concatenate corpus files into one 50k-line module in `/tmp`, run `PYTHONPATH=src:. python benchmarks/profile_perf.py` the way `docs/benchmarks.md` describes for the existing rows, and add the row to the table. Do not optimise anything. Done (measured, not optimised): the ~50k row is **infeasible in practice**. `check` alone on the 50,763-line workload exceeded 30 min (> 85× the 12k `check` for 4.2× the lines); `fix` multiplies that via `max_rounds=3` plus `_degrade` halving. Two prior attempts ran ~9 h CPU each without finishing; a fresh run was still in `fix` after ~2 h. `cProfile` puts the cost in `hints.index → _candidates → CommentedModule.convert → _graph/backend/checkpoint._infer` (whole-module graph conversion per hint-index build). Row added to `docs/benchmarks.md` as `> 30 min / — / infeasible in practice` with the evidence; background runs were left in flight writing `/tmp/bench_50k.json` / `/tmp/bench_25k.json` in case they complete.

#### Q-32 — `docs/benchmarks.md`: add a "How to refresh the baseline" section with the three exact…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `docs/benchmarks.md`: add a "How to refresh the baseline" section with the three exact commands (recovery with `--checker-delta --checker-gate --delta-limit 25 --json`, `gate`, `baseline`) and the rule "only accept a baseline with 0 crashes, 0 wrong, 0 new errors". Copy the numbers format from the existing table. Done: section sits under "Accepted gated baseline"; commands use `PYTHONPATH=src:. python -m benchmarks …` per the harness convention.

#### Q-36 — Read `HintIndex._judge_pass`, `_call_sites` and `_judge_call_sites` in…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Read `HintIndex._judge_pass`, `_call_sites` and `_judge_call_sites` in `src/astart/rules/hints.py` and write `docs/hint-propagation.md` describing, in plain words, what each does and in which order the 12 propagation passes run. No code change. (This is the specification for Q-37.) Done: documents `HintIndex.create`'s four stages, the 12-pass fixpoint (`_call_sites` then `_judge_pass`, early exit on no gain), and the three named methods.

#### Q-37 — Create `src/astart/rules/slots.py` with a `SlotTable` class: `deposit(*, slot: str, kind:…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Create `src/astart/rules/slots.py` with a `SlotTable` class: `deposit(*, slot: str, kind: str, source: str) -> None`, `claims(*, slot: str) -> dict[str, set[str]]` (type → set of evidence sources), `settle(*, slot: str) -> str | None` (returns the type only when exactly one type has claims). Pure data structure, no AST. Tests in `tests/test_rules_slots.py`: empty slot → `None`; two sources same type → that type; two types → `None`; same source twice counts once. Done: `SlotTable` keeps `slot → kind → set[sources]`; `claims` returns a defensive copy, `settle` answers only on exactly one kind. Five tests cover all four spec cases plus slot isolation.

#### Q-39 — `tests/test_rules_typer_negatives.py`: 12 one-line refusal tests proving the typer…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `tests/test_rules_typer_negatives.py`: 12 one-line refusal tests proving the typer returns `None` (never a guess) for: a bare name not in the environment, `x.attr` with unknown `x`, `f()` for an unknown `f`, `a + b` with unknown operands, `[]`, `{}`, `()`, `lambda: 1`, `await x`, `yield`, `x if y else z` with unknown branches, `*a`. Use `expression_type(node=..., counts={})`. Done with Q-48: `tests/test_rules_typer_negatives.py` covers all 12 refusals — the 8 eval-mode cases plus `await x`, `yield`, `*a` and `x if y else z` via `_special_node`.

#### Q-40 — `tests/test_rules_hint_cache.py`: assert two `fix_source` calls on identical text return…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `tests/test_rules_hint_cache.py`: assert two `fix_source` calls on identical text return identical `FixResult.source` (no state leaks between calls) for five small inline modules.

#### Q-41 — Document every `Rejection` value: `grep -n "class Rejection"…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Document every `Rejection` value: `grep -n "class Rejection" src/astart/rules/reasons.py`, then add `docs/skip-reasons.md` with one line per member: the string value and one sentence taken from its docstring. Test: every member's value appears in the file. Done: `docs/skip-reasons.md` lists all 15 members verbatim; `tests/test_skip_docs.py` asserts coverage.

#### Q-42 — Document every `SkipCode` the same way (`docs/skip-codes.md`)
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Done: `docs/skip-codes.md` lists all 6 members verbatim; same test file.

#### Q-43 — `README.md`: add a "Limits" section (five bullets, copied from the "Where it is far from…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `README.md`: add a "Limits" section (five bullets, copied from the "Where it is far from perfect" list in the 2026-11-07 status notes: recall, cross-module, protocols depth, constructors/overrides, speed). No new claims. Done with Q-52: the existing `## Limits` section now leads with the five bullets; the conservative-editor paragraph stays as a second paragraph. Note: two bullets predate M3 (`--project`, typeshed loading) and `--cache`, so they read stale — kept verbatim per spec.

#### Q-44 — Add `tests/test_cli_exit_codes.py`: `fix --check` on a clean file → 0; on a file with a…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add `tests/test_cli_exit_codes.py`: `fix --check` on a clean file → 0; on a file with a pending fix → 1; on a missing path → 2; on an unreadable (directory-less) path → 2. Build files in `tmp_path`.

#### Q-45 — Add `tests/test_cli_formats.py`: `check --format json` output parses with `json.loads`…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add `tests/test_cli_formats.py`: `check --format json` output parses with `json.loads` and every finding has the keys `code`, `message`, `path`, `line` (read `render_json` to confirm the real key names first and use those).

#### Q-46 — Add `tests/test_rules_variadic_methods.py`: the same cases as…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add `tests/test_rules_variadic_methods.py`: the same cases as `tests/test_rules_variadic_hints.py` but with the function as a method of a class called through `self.m(...)` and through `Class().m(...)`. If a case fails, record the output under the task and mark it `BLOCKED`. Done: all six mirrored cases pass — method calls via `self.m(...)`, `instance.m(...)` and `Class().m(...)` already feed variadic evidence, so `*args`/`**kwargs` get the same shared-type hints as module-level functions. No BLOCKED cases.

#### Q-47 — Add `tests/test_rules_default_expression_edges.py`: refusal tests for `x=-1` called with…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Add `tests/test_rules_default_expression_edges.py`: refusal tests for `x=-1` called with a `str` argument elsewhere in the module (hint must not be `int`), `x=A` where `A` is a function parameter default elsewhere, and `x=1 + 2.0` (type `float`, not `int`).

#### Q-48 — Create `tests/test_rules_typer_negatives.py`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

```python
"""The typer never guesses: unprovable expressions give ``None``."""

from __future__ import annotations

from ast import parse

import pytest
from astart.rules.provable import expression_type

from tests.expectations import expect_equal


@pytest.mark.parametrize(
    "text",
    ["x", "x.attr", "f()", "a + b", "[]", "{}", "()", "lambda: 1"],
)
def test_unprovable_expressions_give_none(*, text: str) -> None:
    """Check that ``text`` has no provable type.

    Args:
        text: Expression source.

    """
    node = parse(source=text, mode="eval").body
    expect_equal(actual=expression_type(node=node, counts={}), expected=None)
```

Run: `python -m pytest tests/test_rules_typer_negatives.py -q`.
Expected: `8 passed`.
Done with Q-39: the file also carries the four special forms
(`await`, `yield`, `*a`, `x if y else z`), so it runs 12 cases.

#### Q-49 — Create `tests/test_rules_typer_positives.py` with the same shape as Q-48 but parametrize…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Create `tests/test_rules_typer_positives.py` with the same shape as Q-48 but parametrize `"text, expected"` with the pairs `("1", "int")`, `("'a'", "str")`, `("1.5", "float")`, `("True", "bool")`, `("not x", "bool")`, `("len('a')", "int")`, `("[1, 2]", "list[int]")`, `("{'a': 1}", "dict[str, int]")`, `("f'{x}'", "str")`, asserting `expression_type(...) == expected`. Expected: `9 passed`.

#### Q-50 — Create `.pre-commit-hooks.yaml`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

```yaml
- id: astart-fix
  name: astart fix
  entry: astart fix --check
  language: python
  types: [python]
```

Create `tests/test_precommit_hook.py`:

```python
"""The pre-commit hook definition exists."""

from __future__ import annotations

from pathlib import Path

from tests.expectations import expect_in

HOOK = Path(__file__).parent.parent / ".pre-commit-hooks.yaml"


def test_hook_definition_names_the_check_mode() -> None:
    """Check the hook runs ``astart fix --check``."""
    text = HOOK.read_text(encoding="utf-8")
    expect_in(item="id: astart-fix", container=text)
    expect_in(item="astart fix --check", container=text)
```

Expected: `1 passed`.

#### Q-51 — Create `tests/test_conventions.py`
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

```python
"""House rules that must never regress."""

from __future__ import annotations

from pathlib import Path

from tests.expectations import expect_equal

ROOT = Path(__file__).parent.parent
FORBIDDEN = ("# no" + "qa", "type: " + "ignore")


def _offenders(*, needle: str) -> list[str]:
    found: list[str] = []
    for folder in ("src", "tests"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            if path.name == Path(__file__).name:
                continue
            lines = path.read_text(encoding="utf-8").splitlines()
            found.extend(
                f"{path.relative_to(ROOT)}:{number}"
                for number, line in enumerate(lines, start=1)
                if needle in line
            )
    return found


def test_no_suppression_comments() -> None:
    """Check that no source or test file silences a tool."""
    for needle in FORBIDDEN:
        expect_equal(actual=_offenders(needle=needle), expected=[])
```

Expected: `1 passed`. If it lists offenders in files you did not create,
paste the list under the task and stop (do not edit those files).
Done in the shared `tests/test_conventions.py`. The substring scan
listed three false positives (string literals mentioning
`type: ignore` in `src/astart/ast.py:2618`,
`src/astart/rules/suppressions.py:5` and the fixture in
`tests/test_rules_procedural.py:48`), so the guard matches real
`#`-comments only; zero offenders. Q-17 also required adding the
missing `@final` on `Constants` in
`src/astart/semantic/typing_relations.py`.

#### Q-52 — `README.md`: add a `## Limits` section just after the paragraph under the `astart fix`…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `README.md`: add a `## Limits` section just after the paragraph under the `astart fix` usage block that ends with "missing path.", with these five bullets: recall is low where callers are not visible (about 11% on the stripped-annotation benchmark) and precision is the priority; cross-module call sites and typeshed stubs are not used yet; Protocol and `TypeVar` synthesis covers common shapes only; keyword fixes for constructors, overrides and callbacks are partial; large files are slow (no cache or parallelism yet). Check: `grep -n "^## Limits" README.md`. Done with Q-43: one `## Limits` (README.md:136), five bullets verbatim, existing paragraph retained.

#### Q-53 — Create `CHANGELOG.md` with `# Changelog`, a `## 2026-11-07` heading, and these bullets:…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Create `CHANGELOG.md` with `# Changelog`, a `## 2026-11-07` heading, and these bullets: attribute annotations and typed `self.x` reads; `*args`/`**kwargs` element types from call sites; expression defaults and comprehension types; locals bound several times to one type; checker runs on a temp-dir copy with detected import roots and `--source-root`; gated benchmark baseline stored in `benchmarks/baseline.json`. Done: `CHANGELOG.md` created with all six bullets (shared with Q-24).

#### Q-54 — Create `tests/test_rules_typer_matrix.py` pinning every row of the table above that says…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Create `tests/test_rules_typer_matrix.py` pinning every row of the table above that says "ok" or "correct refusal". Use the same `parametrize("text, expected", [...])` shape as Q-48/Q-49 and these exact pairs: `("1 + 2", "int")`, `("1 + 2.0", "float")`, `("1 / 2", "float")`, `("7 // 2", "int")`, `("7 % 2", "int")`, `("-1", "int")`, `("True + True", "int")`, `("'a' + 'b'", "str")`, `("'a' * 3", "str")`, `("1 < 2", "bool")`, `("'a' in 'b'", "bool")`, `("not 1", "bool")`, `("1 if True else 2", "int")`, `("1 and 2", "int")`, `("str(1)", "str")`, `("chr(97)", "str")`, `("repr(1)", "str")`, `("int('1')", "int")`, `("ord('a')", "int")`, `("float(1)", "float")`, `("bool(0)", "bool")`, `("isinstance(1, int)", "bool")`, `("{1, 2}", "set[int]")`, `("(1, 'a')", "tuple[int, str]")`, `("b'x'", "bytes")`, `("[i for i in range(3)]", "list[int]")`, and the refusals `("1 if True else 'a'", None)`, `("1 or 'a'", None)`, `("[1, 'a']", None)`, `("f(1)", None)`. Expected: all pass. This file is the safety net for every typer task: run it before and after Q-01…Q-07 and Q-55.

#### Q-55 — `**` operator
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** In `src/astart/rules/provable.py`, class `_Typer`, method `_binop`: before the existing numeric branch add: if `isinstance(node.op, Pow)` (import `Pow` from `ast`) then (a) both sides typed `int`/`bool` AND `node.right` is a `Constant` whose `value` is an `int` ≥ 0 → return `"int"`; (b) either side typed `float` and the other `int`/`bool`/`float` → return `"float"`; (c) otherwise return `None` (a negative or unknown exponent makes `int ** int` a `float`). Tests (add rows to a new `tests/test_rules_typer_pow.py`): `("2 ** 3", "int")`, `("2 ** 0", "int")`, `("2 ** -1", None)`, `("2.0 ** 2", "float")`, `("2 ** 0.5", "float")`, `("x ** 2", None)`. Then add `("2 ** 3", "int")` to the Q-54 matrix. Done (verified already implemented): `_Typer._pow` dispatches `Pow` before the numeric branch — `int`/`bool` base + non-negative `int` constant exponent → `int`; `float` cases → `float` only when no `complex` is possible (non-negative literal base guard); else `None`. `tests/test_rules_typer_pow.py` covers all six spec rows plus `True ** 2`, `2.0 ** 0.5`, `(-2) ** 0.5`, `2 ** x`, `'a' ** 2`; `("2 ** 3", "int")` is in the matrix. 42 tests pass.

#### Q-56 — Pin the gaps so closing them is visible: create `tests/test_rules_typer_gaps.py` with…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Pin the gaps so closing them is visible: create `tests/test_rules_typer_gaps.py` with `xfail(strict=True)` parametrized rows for `("'a'.upper()", "str")`, `("[1][0]", "int")`, `("abs(-1)", "int")`. Each task that closes a gap (Q-01, Q-05, Q-06) must delete its row here in the same change (a strict xfail that starts to pass fails the suite, which is the reminder).

#### Q-59 — Write `docs/typing-inference.md`: copy the table at the top of this section verbatim, add…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Write `docs/typing-inference.md`: copy the table at the top of this section verbatim, add a heading "Evidence classes" with the E0–E6 list from the spec (search `docs/` for "E0" and copy the one-line definitions without changes), and a heading "How to add a typer rule" with the five-step recipe: add a handler in `_Typer.__init__`'s `_handlers`, implement it returning `str | None`, add a row to the Q-54 matrix, add a row to the Q-57 matrix, run the fast tier. Done: table copied verbatim (gap rows kept as historical record), E0–E6 one-liners from `docs/evidence-ladder.md`, recipe names the real matrix files (`test_rules_typer_matrix.py`, `test_rules_return_matrix.py`).

#### X-01 — P0
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Narrower parameter annotations. A literal default
fixes the annotation (`timeout=5` → `int`, `errors="strict"` → `str`), but
real code writes the wider type (`float`, `str | None`): measured 128
"narrower" mismatches, mostly parameters. A too-narrow parameter type
rejects valid callers. Decide a policy per literal type (e.g. `int` default
→ `float` when the body only does arithmetic that `float` also accepts, or
leave unannotated) and measure it with `relation()` on both corpora; target
≤ 5 % narrower parameters. Files: `rules/hints.py` (`default_literal`),
`rules/confidence.py`.
Done 2026-11-08: literal-default confidence is calibrated by type
(`confidence.by_literal`: bool/float 0.99, int 0.72, str 0.69; call-site
agreement lifts a default to `call_sites` 0.95), the CLI floor is
`confidence.default_minimum` = 0.8 (`--min-confidence 0` opts into the
riskier tier), and the fix's own catalog minimum is 0.5 so the user floor
decides. External corpus: narrower parameters 74 → 21 (≈ 1.4 % of written
parameters, target ≤ 5 %), recall 20.8 → 19.3 %. Tests:
`tests/test_rules_default_confidence.py`. Remaining 21: `bool` defaults whose
originals are `bool | None`/`bool | str`, and call-site-corroborated `int`
where the original says `float` (follow-up: X-01b, check `float` call
sites and `| None` defaults).

#### Q-60 — DOC001 stub docstrings — DONE 2026-11-08 with a different design than first sketched
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** The writer renders an inserted docstring statement with `repr` (single quotes, `\n` escapes) and validates output with `ast.dump`, so a synthesized `Expr(Constant(...))` cannot be made triple-quoted. Instead `docs_fixes.stub_missing_docstrings(source=...)` is a *text pre-pass* run by `fix_source` before parsing when `FixSettings.stub_docstrings` is set (CLI `--stub-docstrings`): it inserts a one-line `"""Describe <name>."""` above the first body statement of each public, non-overload, non-`...`-bodied definition; `DOC002`'s fixer then expands it with an `Args:` section. Rule `DOC001` is detection-only and gated by fact `docs.stubs_wanted` (option set, or the module already has docstrings), so docstring-free scripts and every other rule's catalog examples stay quiet. Tests: `tests/test_rules_docstring_stubs.py`.

#### Q-62 — Run ruff on docstring content
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** After the fixer writes the file, `ruff format` already normalises docstring indentation and trailing space. Enable code-example formatting: in `pyproject.toml` under `[tool.ruff.format]` add `docstring-code-format = true` and `docstring-code-line-length = "dynamic"`. Check that the CLI's final formatting pass (`src/astart/cli/commands.py`, look for the `ruff format` call) uses the project's `pyproject.toml` (it runs with `cwd=Path.cwd()`). Done: `docstring-code-format = true` and `docstring-code-line-length = "dynamic"` added under `[tool.ruff.format]`; the formatter resolves config through the target path's ancestors. Regression test in `tests/test_rules_formatter.py` (`>>> x = [1,2]` → `>>> x = [1, 2]`).

#### Q-63 — Whitespace outside docstrings
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Wire the existing detectors `find_blank_line_runs` and `find_trailing_space` (`rules/whitespace_rules.py`) as catalog rules `WSP001`/`WSP002` with module-level subjects, and fixes `whitespace.collapse-blank-lines` (3+ blank lines → 2 at module level, 1 inside functions) and `whitespace.strip-trailing-space`. These are text-level edits, so apply them in a pre-pass on the source string in `rules/runner.py` before parsing, not as AST appliers. Test: idempotence on three corpus files. Done: `whitespace.json` catalog adds WSP001/WSP002 on `Module` subjects via new `whitespace.*_count` facts; fixes `whitespace.collapse-blank-lines` and `whitespace.strip-trailing-space` are guarded text transforms applied inside `_attempt` before parsing (registered in runner `_TEXT_FIXES`), skipping rows inside multi-line string literals. `ModuleFacts` gained a `source` field and `_visit` now emits `Module` subjects (named `<module>`). Tests: `tests/test_rules_whitespace_fixes.py`.

#### Q-65 — Heal renamed parameters
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** When a function has exactly one stale entry and exactly one undocumented parameter in the same position, rename the entry instead of removing and re-adding (keeps the user's description). Extend `remove_parameter_entries`/`add_parameter_entries` with a `rename_parameter_entry(doc, old, new)` and a combined applier; tests: rename keeps the text, two stale + one missing falls back to remove+add. Done: `rename_parameter_entry`/`parameter_entry_names` in `docstring_edit.py`; `heal_rename` applier fires only for exactly one stale entry and one undocumented parameter at the same doc/signature position; fix `docs.heal-parameter-rename` (proven, runs before the add/remove fixes) is offered by `docs.stale-parameter`. Tests in `tests/test_rules_docs_fixes.py`.

#### Q-66 — Module docstring support: extend `_docstring()` in `rules/docs_fixes.py` to accept…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** Module docstring support: extend `_docstring()` in `rules/docs_fixes.py` to accept `Module` and let `DOC007` apply to it (indent `""`). Add `Module` to the DOC007 rule's subject list in `docs.json`. Test with a module docstring that has trailing spaces. Done: `_docstring()` accepts `Module`, `triple_quoted_owners` maps ownerless (module) docstrings to the module node, `_call_name` names the subject `<module>`, DOC007 lists `Module` first with a module example.

**Test:** `test_a_module_docstring_is_tidied`.

#### Q-67 — `--no-docs` flag (`astart fix --no-docs`) that excludes the `docs.*` fixes, for users who…
- **Status:** done
- **Priority:** Untriaged
- **Area:** Uncategorized
- **Readiness:** done

**Context:** `--no-docs` flag (`astart fix --no-docs`) that excludes the `docs.*` fixes, for users who want typing fixes only. Pass the excluded prefix list through `FixSettings` (see how `ceiling` filters fixes in `rules/runner.py`) and add a CLI test. Done: `FixSettings.excluded_prefixes` filters offers in `_eligible` (`str.startswith` tuple); `FixCommandSettings.no_docs` maps to `("docs.",)`; `--no-docs` wired in `__main__.py`. CLI test `test_no_docs_skips_docstring_fixes`.


## Overall implementation status


> Generated from real Markdown checkboxes outside fenced examples, HTML
> comments and this managed block. Only `[x]` counts as complete.
> Every checkbox counts equally, including parent and child items.
> These totals are not release-readiness evidence.

<div role="progressbar" aria-label="Roadmap completion" aria-valuenow="154" aria-valuemin="0" aria-valuemax="326" style="width:100%;height:1.5rem;background:#e5e7eb;border-radius:.75rem;overflow:hidden;">
<div style="width:47.2%;height:100%;background:hsl(56.6 80% 45%);"></div>
</div>
<p><strong>154/326 (47.2%)</strong></p>

**Done:** 154 · **Open:** 172 · **ONGOING:** 0 · **Total:** 326

<!-- ROADMAP_PROGRESS_SUMMARY_END -->

Start with [task fields and categories](#task-schema-and-category-definitions)
and the [execution map](#execution-map--measurement-first), then use the owning
checkbox and its acceptance evidence. The [progress log](#11-progress-log) is
append-only history; a checked historical item is not a release pass if later
source changes invalidate it.

## Task schema and category definitions


Every actionable checkbox uses this header, including nested subtasks:

```markdown
- [ ] **M1-01** **P0** **Testing / QA** — Implement a specific observable behavior.
  Scope: identify the owning module, affected rules and exclusions.
  Acceptance: describe the observable result and evidence required to check off.
```

Fields: **stable ID**, **priority**, **category**, then the description.
Use `- [x]` only when acceptance evidence exists. Preserve detailed
specifications and evidence beneath their owning task; historical completion
is not current release readiness.


Assign one category by primary deliverable. Workstreams are surrounding
headings, independent of categories. Split independent deliverables into
subtasks.

| Exact category | Definition and assignment boundary |
| --- | --- |
| Backend | Engine, appliers, facts, hints, resolve, inference, imports, protocols, typevars, checker, runner, model/schema, CLI commands and persistence. Their acceptance tests belong in Testing / QA. |
| Testing / QA | Automated tests, benchmarks, gold sets, corpus, coverage, exactus gate evidence, fuzzing and catalog verification. Implementation remains a separate obligation. |
| Documentation | Specifications, references, user docs, refusal catalogue, evidence ladder docs and ADRs. Documenting code changes does not complete their implementation. |
| DevOps / Release | Packaging, distribution, configuration surface, CI/pre-commit recipes, reporters and release infrastructure. |
| Uncategorized | Ownership is unresolved. Review and classify before implementation; this is not a miscellaneous implementation category. |


| Exact priority | Meaning |
| --- | --- |
| P0 | Blocks the core workflow or trustworthy release: wrong annotations, silent misfixes, or the measurement gate every other claim depends on. |
| P1 | Required core functionality or acceptance work after blockers. |
| P2 | Secondary enhancement or follow-up that is not a core blocker. |
| P3 | Optional polish or deferred improvement. |
| Untriaged | No unambiguous priority was recorded. Schedule explicitly; this does not mean P2 or low urgency. |


Existing IDs are permanent. IDs are milestone-prefixed (`M1-01`, `M2-03`),
with `EV-` for verified-evidence entries and `CC-` for cross-cutting items;
children receive their parent's ID with a numeric suffix such as `M1-02-01`.
Do not renumber after reordering. Every checkbox is one tracked obligation.
Non-action examples belong in prose or fenced code, not extra unchecked boxes.
One task ID has one owning checkbox; an implemented happy path does not close
missing failure-mode, idempotence or checker-gate acceptance.

## 3. Done since the last audit

## 13. Verified inventory and defects (reference)


**Working today** (verified by running the engine): `calls.add-keywords`
(guarded, trusted in-module callees), `typing.add-none-return` (proven),
`typing.add-inferred-annotation` (two-signal corroboration: default literal /
agreeing call sites / provable return + inference),
`typing.synthesize-protocol` (attribute/method-only params, dedupe),
`typing.synthesize-typevar` (pass-through, classic TypeVar, auto-import),
`typing.add-final`, `typing.add-noreturn` (proven), fix-runner
ordering/conflict/halving, corpus probe numbers (316 `-> None`, 200 inferred,
63 Protocols, 8 TypeVars, 174 keyword calls).

**Verified defects** (owners in task IDs above):
- D1 ✅ `add_inferred_annotation` called no `ensure_names` → fixed (M0-02).
- D2 ✅ `'Unknown'` counted as disagreeing evidence → fixed (M0-03).
- D3 ✅ `imports.Constants.constructors` dead → result-type half fixed (M0-04);
  argument-typing half remains → M8-19.
- D4 `C().m(4)`/`factory().m()` bound by analyzer but `trusted_binding`
  rejects non-Name receivers → M2-04.
- D5 `self.m()` never binds → methods get zero call-site evidence → M2-01.
- D6 `Exists` predicate crashed engine → guarded (M0-05); evaluation → M8-11.
- D7 ✅ `min_confidence` never enforced (`FixOffer.confidence` hardcoded 1.0)
  → fixed (M1-15); calibration → CC-01.
- D8 procedural rules unimplemented → M8-12.
- D9 ✅ `raise`-only functions get `-> None` → `typing.add-noreturn` (M0-06).
- D10 ✅ order-dependent flakiness — not reproduced; traced to external file
  rewriting (M0-09).
- Roadmap inventory: methods second-class → M2; single-module world → M3;
  superlinear perf (12k lines ≈ 47 s) → M1-10/M7-01; protocol members untyped
  → M5-01/02.

**Verified recall gaps** (owners): R1 `x=None` → M4-04 · R2 `*args`/`**kw` →
M4-05 · R3 generators → M4-06 · R4 usage→ABC → M4-07 · R5 `TypeGuard` → M4-08
· R6 unions → M4-11 · R7 `Await`/`Try`/`Match`/`AugAssign` → M4-02 · R8
expression defaults → M4-12 · R9 `self._attr` tainted → M2-06 · R10
language-guaranteed returns → M4-10 · R11 comprehension returns → M4-01 · R12
`Self`/`ClassVar`/property → M4-13 · P1–P4 protocol gaps → M5-01…M5-09 ·
T1–T5 typevar gaps → M5-14…M5-24 · K1–K4 kwargs gaps → M3-05/M6-05…M6-08.

## 14. Risk register


Wrong annotation → checker gate + profile-controlled ceilings + `--safe-only`
· keyword fix on dynamic code → danger matrix + refuse-on-uncertainty +
library allow-list · Protocol name churn → deterministic naming + lockfile +
reuse-before-create · inference regressions → benchmark thresholds in CI ·
performance → M7 phase + incremental cache · version drift →
`requires-python` gating · scope creep → astart proposes, external checker
verifies, never becomes a checker · unbounded semantics → refusal catalogue +
fuzzing, new constructs start as "refuse" · suite pollution (D10) →
investigate shared mutable trees before more import-writing appliers ·
checker flakiness → scratch-file isolation + timeout + refuse-on-no-answer.

## 15. Files touched per layer


`rules/provable.py` (Typer/can_fall_off) · `rules/hints.py`
(HintBasis/judges/evidence/confidence) · `rules/protocols.py` (typed
members/ABC lowering/merge) · `rules/typevars.py` (bounds/constraints/
ParamSpec/PEP695) · `rules/imports.py` (resolver/TYPE_CHECKING/canonical
locations) · `rules/resolve.py` (trusted_binding v2/self./stubs) ·
`rules/facts.py`+`rules/registry.py` (new facts/procedures) ·
`rules/engine.py` (Exists/procedures/confidence/subject index) ·
`rules/runner.py` (E6 gate bisection/min_confidence) · `rules/checker.py`
(E6 oracle) · `rules/model.py`+`schema.json`+`catalog/*.json` (new
rules/fixes/profiles) · `cli/commands.py` (config/profiles/jobs/reporters/
explain) · `semantic/*`+`_graph/*` (resolution/inference fixes — prefer
rules-layer where cheaper) · `benchmarks/`+`tests/bench_*` (harness) ·
`docs/benchmarks.md`, refusal catalogue.

## 16. Verification (every milestone)


- `python -m pytest -q` green; benchmark dashboard shows precision ≥99.5%
  guarded / 100% proven with no regression.
- Bare `exactus` from repo root as single lint/check gate; pytest for tests
  while iterating.
- Dogfood `astart check`/`fix --diff` on `src/astart/` — findings shrink per
  milestone; output always compiles.
- E6 checker delta = 0 new errors on benchmarks; corpus replay measures
  accepted-hint coverage before/after.
- `verify_catalog` 8 invariants + per-fix idempotence on every catalog
  example.

## 17. Progress log


- Fixed: D1 (`ensure_names` now runs in `add_inferred_annotation`), D2
  (`Unknown` call-site types are non-definite; syntax-proven argument types
  are independent evidence), D3 (imported constructors `Path("x")`,
  `Decimal(..)`, … type their calls via the `@constructor:<Name>`
  binding-count key), D6 (catalog validation rejects `exists` until M8
  evaluates it), D9 (`typing.add-noreturn`, proven: always-raising functions
  get `-> NoReturn`), plus the review findings C1, C2, I1–I6.
- Replaced the five `object` annotations in `formatting.py` (typed
  `FieldValue` / `PatchValue` aliases); fixed RUF043.
- D10 (suite flakiness) did not reproduce: the suite passes in forward and
  reverse file order (1616 tests). The only order-like failures seen were
  from files being rewritten on disk by another tool during editing
  (bare-import conversion); no shared mutable state was found.
- D4, D5, D7, D8 are not M0 items (M2, M2, M1, M8).
- Not done at the time: bare `exactus` run, baseline commit — both closed in
  the M1 entry below.


- **Closed skip-reason enum** (M1-01): `rules/reasons.py` defines `SkipCode`
  and `Rejection`; `SkippedFix.code` carries the enum; every `hints.py`
  rejection string is a `Rejection` member. `tests/test_rules_skip_codes.py`.
- **E6 checker oracle** (M1-02): `rules/checker.py` (`Checker` protocol,
  `PyrightChecker`, `detect_checker`, content-hash cache); runner vetoes
  guarded fixes via `SkipCode.checker_rejected` with halving bisect;
  `--checker auto|off` CLI flag.
- **bare `exactus` clean** (M0-10): 6/6 tools PASS, 0 files with issues —
  docs 0/159, lints 0/159, coverage_tests 0/91 (1616 tests, 94.95% total),
  kwargs_typehints 0/159 (unresolved callees 0 — subscript-lookup and
  unknown-receiver callees bound to annotated locals), readme, performance.
- **Baseline committed**: work landed through `5b788f3`; `reasons.py`,
  `checker.py`, runner/CLI wiring and their tests are the current uncommitted
  set.
- Still open in M1: benchmark harness + gold sets, optional mypy,
  checker-absent internal-evidence fallback, writer fuzzing, D7 real
  `FixOffer.confidence` + `min_confidence` (still `1.0` in `engine.py`),
  full-CLI idempotence suite.

- Done: closed skip/rejection vocabulary (`astart.rules.reasons`: `SkipCode`, `Rejection`; `SkippedFix.code`); **E6 checker gate** (`astart.rules.checker`: `PyrightChecker`, `FixSettings.checker`, `--checker auto|off`; guarded rounds are verified, rejection bisects through the runner's halving and reports `checker-rejected`); **D7** real offer confidence (`astart.rules.confidence`) + `FixSettings.min_confidence` + `--min-confidence`; **annotation-recovery benchmark** (`astart.rules.recovery`, `benchmarks/recovery_report.py`, `docs/benchmarks.md`: baseline precision 16/16, recall 16/144); writer fuzzing over random fix subsets; full fix+ruff idempotence on the corpus.
- Benchmark finding fixed: call-site hints were accepted from the same inference engine that proposed them (`parse_hex_char(src)` → `Sequence[int]`); call-site types must now be syntax-proven. `&`, `|`, `^` result types are now provable.
- Not done: gold set 34→≥500, corpus 20→≥100 modules, checker-delta and throughput-by-size benchmarks, semantic-equivalence runs on pinned projects, shared `srcs` cache for checker runs across files.


State of the tree at this entry: `python -m pytest -q` → **1648 passed**;
`ruff check src tests benchmarks` clean. Exactus was last audited by this
agent in report-only mode (`--lints --no-fix`, `--docs`, `--kwargs_typehints`,
`--readme` with `--dry-run`: all 0 issues / 159 files) before the confidence,
recovery, fuzz and idempotence additions below; the owner states Exactus
reports 0 issues on all tools, so it was not re-run.

- **Checked off:** M1-13 (writer fuzzing), M1-15 (D7). Totals 13 → 15 of 148.
- **Added beyond the checklist:** `rules/process.py` (shared subprocess helper
  now used by `formatter.py` and `checker.py`; `asyncio.timeout`, no
  `subprocess` import, no suppressions); `--min-confidence` CLI flag.
- **Benchmark finding fixed (precision):** the first recovery run scored
  21/22. `parse_hex_char(src)` was hinted `Sequence[int]` (truth `str`)
  because call-site evidence came from the same inference engine that
  proposed the candidate. Call-site types now count only when the argument
  expression's syntax proves them (`hints._argument_evidence`/`_Site.proven`);
  the typer now also proves `& | ^` result types. Precision 16/16 afterwards.
  Recall cost: a few call-site hints that were correct are now refused.
- **Gold-test note:** `test_bool_arithmetic_at_a_call_site_is_not_bool` still
  holds (`True & False` → `bool` is now syntax-proven).
- **Partial, still open:** M1-04, M1-05, M1-14 (see the notes under each).
- **Not started in M1:** M1-03 (mypy / checker-absent fallback), M1-06
  (gold set 34 → ≥500), M1-07 (corpus 20 → ≥100), M1-08 (dashboard gates),
  M1-09 (checker-delta), M1-10 (throughput buckets), M1-11 (stability
  convergence counts), M1-12 (semantic-equivalence runs).
- **Operational notes:** the checker writes a transient `astart_check_*.py`
  beside the file under test (name must not start with `.`: pyright skips
  hidden files) and deletes it in `finally`; `basedpyright` prints its JSON on
  stderr in this install, so `checker._run` falls back to stderr when stdout
  is not parseable. Each checker run costs ~1–2 s (Node start-up), so large
  trees should use `--checker off` or wait for the M7 cache.


- **Checked off:** M2-01 (D5, `self.m()`), M2-04 (D4, `C().m()`).
- New: `rules/methods.py` (`MethodIndex`), `rules/scopes.py`
  (`names_bound_by`, moved out of `protocols.py` to break an import cycle),
  `resolve._vet`, `facts.kept_positionals` (an explicit receiver in
  `C.m(obj, …)` stays positional; before this it was keyworded as `self=obj`).
- Behaviour change that is a precision gain: attribute calls now need
  *uniform* definitions (all `def m` in the module share parameter names) and
  no `x.m = …` store, which also tightens the pre-existing `obj.m(…)` path.
- Tests: suite without `tests/test_gold_expansion.py` → **2132 passed**; the
  gold case "method call sites are not resolved" was replaced by two cases
  (resolved on a constructed instance; no evidence when overridden).
- Observed, not mine: a parallel session is adding `tests/test_gold_expansion.py`
  (63 failing cases at the time of writing), `src/astart/rules/libkw.py`
  (≈7 000 ruff findings) and `src/astart/cli/config.py` (1). Those files are
  in progress and are the only reason `ruff check src tests` is not clean now.



- **Checked off:** M6-01. New file only: `tests/test_rules_kwargs_danger.py`
  (70 rows: 50 pass, 20 strict-xfail through `fix_source` at
  `FixSafety.guarded`).
- The strict xfails document live unsound keyword fixes for M6-02+:
  `setattr`/`object.__setattr__`/`c.__dict__`/`globals()` rebinding is
  invisible to `binding_counts`; `__getattribute__` intercepts `self.m`;
  class-body rebinding of a method name (`m = Descriptor()`,
  `staticmethod`, `del`, annotated/tuple/for-target assigns) is not seen
  by `MethodIndex._find`; metaclass `__call__` and `__new__` disagreeing
  with `__init__` still keyword `C(...)`; class decorators are not vetted.
- When M6-02+ fixes land, the strict xfails flip to XPASS failures,
  forcing marker cleanup.


- **Checked off:** M2-03 (constructor keywords incl. simple dataclasses).
- New in `rules/methods.py`: `dataclass_init_names` (generated `__init__`
  parameters of a plain `@dataclass`), with neutral-option whitelist
  (`frozen`, `order`, `eq`, `slots`, `repr`, `unsafe_hash`, `match_args`);
  `resolve._is_plain_dataclass_call` trusts the analyzer binding only when its
  parameter list equals that field list.
- Owner confirmation recorded: Exactus reports 0 issues on every tool; the
  final `--coverage_tests` run was in progress; this agent does not re-run
  Exactus.
- Open M2 items still ahead: M2-02 remainder (`super().m`, `cls`), M2-05,
  M2-06, M2-07 remainder, M2-08, M2-09, M2-10, M2-11, M2-12, M2-13.



- **Checked off:** M7-07. `src/astart/cli/config.py` is the unwired
  loader; `src/astart/cli/ignores.py` resolves selections through catalog
  profiles. No wiring into `__main__.py`/`cli/commands.py`, per spec.
- Surface: `profile`, `select`/`ignore` (prefix semantics),
  `min-confidence`, `safety-ceiling` (`FixSafety`), `target-version`
  (`major[.minor…]`), `checker`, `exclude`, `library-tables`,
  `[tool.astart.params]` (scalar rule params — protocol/typevar style,
  import placement and friends), and
  `[tool.astart.overrides."<glob>"]` per-path tables merged in file
  order (select replaces, ignore accumulates, scalars override-if-set,
  params merge per key).
- `ignores.resolve` maps a `Selection` to `ResolvedSelection`:
  `enabled` (profile rule set ∩ select/ignore), `severity` (profile
  overrides), `params` (rule < profile < selection), `ceiling`
  (explicit > profile). Unknown profile keys raise `ConfigError`.
  `apply_ignores` now rewrites finding severities through profile
  overrides; `selected_rules` takes the catalog and honors profiles.
- Tests: `tests/test_cli_config.py` (new-key parsing, override merging,
  malformed-value `ConfigError`s) and `tests/test_cli_reports.py`
  (profile filtering + severity rewrite, unknown-profile error,
  params/ceiling layering). 26 tests pass.
- Lints: the Exactus lints gate is clean for every file this change
  touched; it still FAILs on `semantic/analyzer.py`,
  `rules/docs_missing_raises.py` and `rules/docs_stale_params.py`,
  which are concurrent edits outside this task.


Method: read-only inventory, a full test run, behavioural probes with tiny
programs, the recovery benchmark over all 113 corpus modules, a realistic
end-to-end `astart fix` on a hand-written untyped app, and a review of the
parallel session's new files. Exactus was not run (owner reports 0 issues on
every tool).

**Measured**
- Tests: 2 808 collected; last full run 2 779 passed, 20 strict-xfail, 2
  failed; both failures were mine and are fixed (`object` annotations in
  `methods.py`; danger-matrix row `dataclass-constructor` now expects the
  keyworded form). Wall time 334 s.
- Lint: `ruff check src tests benchmarks scripts` → 6 findings, all in the
  in-progress `tests/test_cli_reports.py`.
- Catalog: 5 rules (CAL001, DOC002, TYP001, TYP003, TYP004), 7 fixes,
  0 profiles, 0 relations, 18 facts, 7 appliers, **0 procedures**;
  `verify_catalog` OK.
- Recovery benchmark, 113 modules (111 scored): precision **27/28 = 96.4%**,
  recall **27/317 = 8.5%**, 2 crashes, 80.7 s total (≤ 5.7 s per module).
- Realistic sample (`Store`/`Item`/`describe`/`main`/`helper`, 13 fixes):
  compiles, second run is a no-op, correct hints for `helper`, `describe`,
  `main`, `total(discount=0)` and a synthesized `Protocol` for `store`;
  unannotated afterwards: `path`, `load`, `total` return, `find`, `name`,
  `argv` (recall gaps below).
- Unwired code: `libkw.py`, `config.py`, `ignores.py`, `baseline.py`,
  `sarif.py`, `junit.py`, `github.py` and the four procedural detectors are
  not imported by `__main__`, `commands` or the catalog.
- Uncommitted: 148 paths versus commit `120272c`.

**Recall gaps re-verified by probe (all still open)**: R1 `x=None`, R2
`*args/**kw`, R3 generators, R4 usage→ABC, R6 union call sites, R8 `x=-1`,
R9 `self._a` returns, R10 `f"{x}"`/`not x`, R11 comprehension returns,
P `await p.m()` and `p()`, T1 `a or b`, K stdlib keywording, variable
annotations. New finding M4-20: `len(x)`/`str(x)`/`isinstance(x, int)`
returns are blocked by the taint rule.

**New defects found** (owner IDs): M1-16 analyzer `IndexError` crash escapes
the fixer (P0); M2-14 dunder protocol results (`__aexit__` → `None`); M4-20
taint over-conservatism; 20 strict-xfail danger rows now owned by M6-10…13.

**Documentation corrected**: spec §9/§11 and the roadmap no longer say that
method call sites are unresolved.

**New tasks**: M1-16, M1-17, M1-18, M2-14, M3-15, M4-20, M6-10, M6-11,
M6-12, M6-13, M7-16, M8-22, CC-07. **Checked off**: M1-06, M1-07.



- **Checked off:** M6-03 (library keyword table, 11 947 typeshed entries,
  posonly/receiver-free, stdlib first) and CC-05 (`docs/evidence-ladder.md`
  + `docs/refusals.md`, keyed by `Rejection`/`SkipCode`).
- **Partial, still open:** M7-01 (analyzer refresh superlinearity removed;
  12k `check` 62→40 s, `fix` 194→104 s, findings identical), M7-02
  (budget still unmet; remaining cost is `_graph`/engine traversal),
  M8-07/08/09 (detectors + `tests/test_rules_docs_whitespace.py`, 8 tests;
  no fixers, not in the catalog → M8-22).
- **Unchanged deferrals:** M7-08/09 reporters/baselines stay built but
  unwired → M7-16; all standalone detectors → M8-22.
- Suite: 2 795 passed, 20 xfailed; Exactus gate clean.


- **Added:** M8-27 — the `imports.bare-import` fixer (`import a` +
  `a.b` loads → `from a import b` + `b`), specified per-attribute with
  the refusal matrix: attribute stores/dels keep `import a`; local
  name collisions skip the attribute; existing `from a import b [as c]`
  is reused rather than duplicated; bare-`a` uses and unrewritable
  positions keep the import; conditional/aliased/multi-name imports and
  `__getattr__`-style modules cap at `guarded`.
- M8-01's audit line now points the fixer at M8-27 and registration at
  M8-22. No code changed; this is spec only.


- **Checked off:** M1-17 (`test_gold_fix_level`: 535 cases × checker
  off/stub through `fix_source`, annotation-fix catalog only, 1 070
  assertions green; one recorded multi-round convergence override) and
  M8-15 (`docs/rule-authoring.md`).
- **Partial, still open:** M1-10 (bucket table published ~1.2k/2.2k/12k,
  superlinear `check` flagged, ~50k row pending), M1-11 (`fix_source`
  idempotent on all 113 corpus modules; round counts not observable),
  M1-14 (every corpus file now covered — ≤700 existing + >700 new —
  and 3 modules through real `main()`; full-corpus CLI drive open).
- **New defect found** (owner: M1-11/M2 line): `fix_and_format` is not
  idempotent on `dataclasses`, `re___compiler`, `webbrowser` — pass 2
  annotates parameters pass 1 skipped because ruff-formatted text gives
  the next fix pass call-site evidence it lacked. Pinned as 3 strict
  xfails in `tests/test_cli_idempotence_full.py`; `fix_source` alone is
  idempotent on all 113.
- Suite additions: `test_gold_fix_level` (+1 070), `test_rules_idempotence`
  (113), `test_cli_idempotence_full` (35). Gold suite re-verified green
  after the main agent's `syntax_proven`/`optional_default` hint work.


- **Added:** M8-28 — two value-preserving string rewrites: `\n`-bearing
  literals → multiline triple-quoted strings, and over-budget literals →
  parenthesised implicit concatenations split at whitespace boundaries.
  Refusals cover f-strings/bytes/raw strings, docstring positions,
  escape-sequence split points, quote-style regressions and precedence-
  sensitive contexts. Evidence: danger-matrix tests, `ast.literal_eval`
  round-trip equality, idempotence, writer-fuzzer invariants.


- **Added:** M8-29 — normalise `JoinedStr` replacement-field interiors
  (`{ x }` → `{x}`, `{x !r}` → `{x!r}`) while preserving expressions,
  conversions and format specs verbatim; refusals cover spec-significant
  whitespace, `=`-debug output, quote-style regressions and any rewrite
  that could change evaluated output. `.format()` conversion explicitly
  out of scope.


- **Added:** M8-30 — docstring indent normalisation (cleandoc-equivalent)
  plus `textwrap.dedent(...)` wrapping for multiline literals whose
  dedented value is proven by downstream evidence; literal
  re-indentation stays value-identical. Refusals cover unproven value
  changes (dedent alters first-line/whitespace-line semantics), mixed
  tabs, meaningful indentation content, and load-bearing positions.


Focus: features that raise what `astart fix` writes. Verified by
`python -m pytest tests -q` → **4039 passed, 20 xfailed** (the documented
danger rows), `ruff check src tests benchmarks scripts` clean except one
E501 in the in-progress `tests/test_rules_protocols.py`, and the 113-module
recovery benchmark (precision 35/35, recall 35/317, 0 crashes).

- **Checked off:** M1-16, M2-14, M2-15 (new), M4-04, M4-09, M4-10, M4-20.
- **Precision finding fixed on the way:** the first run after M4-04/M4-10
  exposed that `x: bool = ...`-style cascades needed several rounds
  (`queue.py`, `wave.py` not idempotent); the in-index propagation fixpoint
  fixed it at the source instead of raising `max_rounds`.
- **Behaviour changes to know about:** (1) call-site hints no longer trust the
  analyzer's argument types — fewer, safer hints; (2) `-> None` is no longer
  written for `__exit__`/`__aexit__`/other protocol dunders; (3) `try`
  statements are analysed for exits; (4) tuple-literal arguments are not
  evidence.
- **Expectations flipped deliberately** (gold/hint tests): `len(p)` → `int`,
  `not p` → `bool`, `str(p)` → `str`, f-string → `str`, `if p: return 1` →
  `int | None`, `try/except` returns → `int`, `p=None` with an `int` caller →
  `int | None`, `-True`/`~True` → `int`, danger row `dataclass-constructor`
  keyworded.
- **Next (my queue):** M4-01 comprehension returns, M2-06 attribute types,
  M4-05 `*args`, M6-10…M6-13, then M3-15. Parallel-safe tracks are listed in
  the assistant's partition note (CLI wiring, benchmarks, Protocol/TypeVar
  track, docs, inference core).


Requested: when a module already has a `Constants` class, new `Final` globals
must be added to it. Done as M8-23 (`rules/grouping.py`) on top of M8-24 (a
writer gap that broke the move when a use was a default value). The M8-09
detector (`constants_grouping.py`, parallel session) is untouched; a fixer for
constants that are *already* `Final` at module level, and creating the class
when none exists, remain open under M8-09.



Implemented in `rules/protocols.py` (+ `env` wiring in `facts.py`/`appliers.py`):

- **M5-01** member returns typed from result use: when every call result (or
  property read) is directly `return`ed and the function has a declared return
  annotation, the member gets `-> <that type>`; mixed/other uses stay
  unannotated. Async members annotate the awaited type.
- **M5-02** member params typed from arguments incl. flow-typed names:
  `structural_usage` accepts `env`; both call sites pass
  `scope_types(module_constants(module))`, so annotated params, constants and
  single-assignment locals type call arguments.
- **M5-03** `await x.m()` / `await x()` produce `async def` members instead of
  refusing; mixed awaited/non-awaited calls still refuse.
- **M5-05** `p(...)` direct calls produce a `__call__` member with positional
  and keyword shapes preserved.
- **M5-08** collision-safe member-name allocation: keywords named `argN` no
  longer refuse — positional slots are renamed (`arg0_1`) around keyword names
  and `self`; a literal `self=` keyword still refuses (unrepresentable).

Evidence: `tests/test_rules_protocols.py` (10 tests incl. async/`__call__`/
flow-env/return-use cases), `tests/test_review3_fixes.py` collision tests.
Open: M5-04, 06, 07, 09–13 (protocol placement/reuse/E6) and M5-14…24
(TypeVars). M5-01 currently covers direct-return result use only; richer
result-shape typing (attribute chains, indexing) remains.


Re-verified unchecked items against the tree; checkboxes updated where
evidence is solid:

- **M1-03** checked: `rules/checker.py` ships `MypyChecker` + `parse_mypy`;
  `build_checker` prefers a pyright-compatible checker then mypy;
  `tests/test_rules_checker_fallback.py` proves the no-checker floor refuses
  single-signal guarded fixes and is bypassed only with `--no-checker`.
- **M1-04** checked: `benchmarks/` package (`runner`, `report`, `semantic`,
  `recovery_report`, `profile_perf`) with `python -m benchmarks
  {recovery,gate,semantic,baseline}` CLI + `test_bench_*.py`.
- **M1-14** checked: `test_cli_idempotence_full.py` +
  `test_cli_idempotence_corpus.py` — 37 tests green this run.
- **M8-20** checked: `semantic/type_inference.py` indexes `self.` writes per
  method (`_instance_attributes`, `_instance_annotations`,
  `_method_receivers`) and resolves `_self_attribute_type` with a recursion
  guard; `tests/test_type_inference.py` 46 green.
- **M2-06** stays open: inference exists, but nothing yet *emits* the
  class-level `self._x: int` annotation the acceptance requires.
- **M3-05/M3-15** stay open: `rules/libkw.py` is generated
  (`scripts/generate_libkw.py`) but imported nowhere — the table is built,
  not wired into binding.
- **M8-01…M8-12 detectors** stay open as before: modules + tests exist,
  catalog registration is M8-22; `Registries.procedures` still empty.
- **M5**: M5-01/02/03/05/08 checked earlier today; M5-04/06/07/09–25 open.


`typevars._is_pure` no longer refuses `BoolOp` values, so `return x or x``
(and any BoolOp whose operands provably share `T`) flows through to
`passthrough_return` → `-> T` with the `T = TypeVar("T")` declaration.
Mixed-type operands (`x or 0`) still refuse — `_boolop` requires a shared
type, matching the "shared `T`" scope. `provable_return` gained a guard
rejecting `Unknown`/`Any` results. The comparison form `a if a > b else b`
still refuses: the test-position use needs `T` orderable, i.e. a bound —
that is M5-14 territory. Tests: `test_rules_typevar_fix.py` (+2).


- **ID collision fixed:** the four fixer specs added earlier today were
  numbered M8-23…M8-26, colliding with the completed M8-23/M8-24
  (Constants-class grouping, writer element replacement). Renumbered:
  IMP001 fixer → **M8-27**, string normalisation → **M8-28**,
  f-string interior → **M8-29**, dedent/indent → **M8-30**; all audit
  lines and progress-log references updated.
- **M8-06** audit note added: `rules/type_mismatch.py` implements
  `find_return_mismatches` + `find_incompatible_defaults` (definitive
  `compatible is False` only), tests in `tests/test_rules_type_checks.py`;
  stays open pending catalog registration (M8-22).
- **M8-27/M8-28** stay open: `imports_bare_fix.py` (19 danger-matrix
  tests) and `strings_normalize.py` (15 tests) are implemented
  standalone with audit notes; acceptance still requires corpus
  idempotence / writer-fuzzer evidence and catalog wiring (M8-22).
- **Progress block regenerated:** 57/169 (33.7%) — the previous 38/168
  figure predated today's checkbox updates (M1-05/09/11/12/18,
  M6-10…M6-13, M8-23/M8-24 and others).


Merged the still-unimplemented tasks from the five retired
`docs/superpowers/{specs,plans}/2026-11-0{6,7}-*.md` files into M8 and
deleted the files. Everything else in them was already shipped:
`astart.rules` model/loader/engine, `hints.py`, `runner.py`,
`formatter.py`, `astart.cli` (`check`/`fix`), the seeded catalog, and
the README "Fixing"/"Command line" sections all exist with tests. The
large-file inference-performance limitation is already tracked by
M1-10/M7-01/M7-02; CLI `--select`/`--ignore`/config/parallelism by
M7-04/M7-05/M7-07.

New items: **M8-31** SUP002, **M8-32** SUP003, **M8-33** CFG001,
**M8-34** OOP001–004, **M8-35** NAM001, **M8-36** SIM001–006,
**M8-37** DOC005/007–013 + doc fixers, **M8-38** SHB001, **M8-39** CLI
watch mode. Progress block regenerated: 61/236 (25.8%).


Implemented and gated M3-01, M3-02, M3-03, M3-04, M3-06 and M3-14:

- New `astart.project` package: `naming` (path → dotted module),
  `scan` (per-module imports/`__all__`/defs), `table` (cross-module
  resolution with re-exports, star imports, cycles, externals),
  `index` (`ProjectIndex`: definitions, call graph, escapes,
  open-world classification, content-hash `refresh`/`remove`),
  `builder` (`build_index` with skipped/collision reporting),
  `libraries` (`LibraryIndex`: typeshed `stdlib/` + `stubs/<dist>`,
  PEP 561 `*-stubs` > `py.typed`, `.pyi` > `.py`), `versions`
  (`PythonTarget` floor from `--target-version` → `requires-python` →
  interpreter).
- `rules/project_bridge.py` `ProjectView` feeds cross-module call
  sites into the hint lattice as `_Site` evidence and binds project /
  library callees for `calls.add-keywords`; only caller-scope syntax
  counts — inference results are never recycled as evidence.
- `LazyStubIndex` gained the `stubs/<dist>` fallback; `Union`,
  `Optional`, `Self` joined `known_imports`; `X | Y` respells to
  `Union[...]`/`Optional[...]` below 3.10 and `Self` is suppressed
  below 3.11.
- CLI: `--project`, `--closed-world`, `--source-root` (check),
  `--target-version` on both `check` and `fix`.
- Notable fix during gating: `definition_is_plain` rejected every
  decorated class, leaving the dataclass-constructor path dead —
  `_find_callable` now admits `@dataclass` classes whose generated
  `__init__` `dataclass_init_names` can spell.
- Gates: `exactus --lints --no-fix` PASS (267 files),
  `--kwargs_typehints` PASS, `--docs` PASS; pytest 4423 green
  (773 slow incl. the ~100k-line index test). First
  `--coverage_tests` run flagged 4 new files under the 80% per-file
  minimum plus one flaky checker test (`README.md` in `tmp_path`,
  fixed by filtering it in `test_rules_checker.py`); dedicated tests
  brought every `astart.project`/`project_bridge` file to ≥84% and
  the coverage rerun was in flight at write time.
- Progress block regenerated: 67/236 (28.4%).


Audited every unchecked task M0–M8 against source, tests, catalog and
CLI wiring (parallel per-milestone audits). Checkbox changes:

- **Checked (6):** M3-05 (`libkw` table generated from typeshed +
  tested; binding is M3-15), M3-10 (import collision avoidance verified
  incl. `_name` aliasing and runtime-binding over-approximation),
  M5-14 (bound TypeVars), M5-15 (constrained TypeVars), M5-17 (element
  pass-through), M5-18 (`Self`).
- **Annotated partial (22):** M2-02/05/06/07/09/10/11, M3-07/12/13,
  M4-01/02/13/14/16, M5-13/16/22/24, M6-02/05/06/07/08/09 — each now
  carries an "Audit 2026-11-08" note with what exists vs. what is
  missing.
- **Confirmed not done:** M2-08 (coarse escape heuristic unchanged),
  M2-12 (no `partial`/callback kwargs), M2-13 (no method-recall gate),
  M3-08/09/11/15 (no file-style matching, no `TYPE_CHECKING` emission,
  no own-added-import cleanup, `libkw` still dead code), M4-03/06/07/
  08/11/17/18/19, M5-04/06/07/09/10/11/12/19/20/21/23, M6-04, M8-11
  (`Exists` still raises `NotImplementedError`), M8-12 (procedures
  never invoked), M8-13/14 (catalog has zero profiles/relations; all
  rules `stable`), M8-30–39.
- **M8-22 note corrected:** catalog is 7 rules / 10 fixes (was "5/7");
  flagged the `TYP005` code collision (`missing-attribute-annotation`
  vs planned variable-annotation rule) and the additional unwired
  detectors (`variable_annotations`, `type_mismatch`, `call_problems`).
- **Docs fix:** `docs/rule-authoring.md` falsely claimed the engine
  calls `rule.procedure`; corrected to state procedures are not yet
  wired (M8-12/M8-22).
- Progress block regenerated: 74/238 (31.1%).
- **M3-15 done:** `libkw` wired into `bound_call` via new
  `rules/library_calls.py` — stdlib/builtin calls keyword end to end
  (`json.dumps(obj=…)`, `re.sub(pattern=…)`, `pow(base=…)`); the
  generator now records `positional`/`var_positional` and provenance
  (date + typeshed_client version). Positional-only callees
  (`getattr`, `isinstance`, `posixpath.join`) verified refused.
  Progress block regenerated: 75/238 (31.5%).
- **Docs-rule workstream landed (audit):** `catalog/docs.json` grew to
  4 rules (DOC001/002/003/007) with 3 wired fixers; `docs_fixes.py`,
  `docstring_edit.py`, `docs_shared.py` and the `--stub-docstrings`
  pre-pass are live. Two corpus bugs found during M3-15 verification
  (comment re-emission AST change; duplicate `Args` entries on second
  pass) were fixed by pre-computing `triple_quoted_owners` and unioning
  `entry_names` — `test_cli_idempotence_corpus` 79/79 green. DOC004/
  DOC006 remain unregistered (M8-07 stays open). New tasks added by the
  workstream raised the denominator; progress block stands at
  75/244 (30.7%).
- **Q-batch done (agent: devin):** Q-13…Q-18, Q-39, Q-40, Q-44, Q-45,
  Q-47…Q-51, Q-54, Q-56 — 17 tasks ticked. New tests:
  `test_rules_typer_negatives.py` (Q-39+Q-48 merged, 12 refusals),
  `test_rules_typer_positives.py`, `test_rules_typer_matrix.py` (31
  rows), `test_rules_typer_gaps.py` (3 strict-xfail gaps),
  `test_conventions.py` (Q-16+Q-51+Q-17 merged; regex-anchored needles
  after the substring scan flagged the detector's own `type: ignore`
  vocabulary; added missing `@final` on `semantic/typing_relations.py`),
  `test_rules_line_endings.py` (CRLF preserved),
  `test_rules_hostile_inputs.py`, `test_rules_determinism.py` (slow,
  PYTHONHASHSEED 1 vs 2 on 5 corpus files), `test_readme_flags.py`
  (README gained `--project`/`--closed-world`/`--stub-docstrings`/
  `--target-version` docs), `test_rules_hint_cache.py`,
  `test_cli_exit_codes.py`, `test_cli_formats.py` (calls `run_check`
  directly — `main` writes to import-time `sys.stdout`),
  `test_rules_default_expression_edges.py`, plus
  `.pre-commit-hooks.yaml` + `test_precommit_hook.py` (Q-50).
  Q-57/Q-58 **BLOCKED** per spec: `pass`-only bodies get no `-> None:`
  and call-site hints now synthesize `TypeVar` (post-spec M5 work);
  failing rows pinned with strict xfail. Fast tier: 3821 passed,
  5 xfailed.
- **Q-batch done (agent: devin):** Q-01…Q-12, Q-19…Q-21, Q-25, Q-26 —
  17 tasks ticked. `_Typer` gained `str_to_str`/`str_to_bool`/`str_to_int`
  method tables behind an `Attribute`-callee branch, `str % x`, list
  `+` concat, a `Subscript` handler (`list[T]`/`str`/`dict[K, V]` +
  `_dict_item` top-level comma split), `special_calls` for
  `abs`/`round`/`min`/`max`/`sorted` and `list`/`set`/`tuple`
  constructors, and `Pow` — which refuses a possibly-negative base
  with a float exponent rather than claim `float` for a `complex`
  result (all six spec rows still pass). `test_rules_typer_gaps.py`
  deleted (all strict xfails closed); matrix gained the `2 ** 3`
  row; negatives gained the `{"a": 1}.get("a")` refusal (Q-08). New
  files: `test_rules_typer_{str_methods,binop,subscript,builtins,pow}.py`.
  Gold: families `variadic` (8), `attribute_read` (6),
  `comprehension` (6), `multi_binding` (6); `_hints`/`_written`
  collect `*args`/`**kwargs`; four `call_sites_unknown` rows updated
  for the new precision (`abs(1)`, `list([1])`, `sorted([1])`,
  `'a'.upper()` args now prove) plus one `_FIX_EXPECTED` override.
  `test_rules_hints.py` moved `list('ab')` to the provable list.
  CLI: `--version` via `importlib.metadata` (`0+unknown` fallback),
  `rules` and `explain CODE` subcommands backed by `run_rules`/
  `run_explain` in `cli/commands.py`. Q-26 deviation: spec said
  Python 3.12 but `requires-python >= 3.13` makes install impossible
  there — workflow pins 3.13. Q-25 needed no change (hook file and
  test already existed). Fast tier: 3977 passed; gold: 1685.
  Progress block regenerated: 110/244 (45.1%).
- **Docs batch done (agent: devin):** Q-22…Q-24, Q-32, Q-36, Q-41…Q-43,
  Q-52, Q-53, Q-59 — 11 tasks ticked, docs-only plus two test files.
  New: `scripts/generate_rule_docs.py` + generated `docs/rules.md`
  (10 catalog rules) + `tests/test_rule_docs.py`;
  `docs/architecture.md` (53 `astart.rules` modules, docstring text
  verbatim) linked from the README intro; `CHANGELOG.md` (`##
  2026-11-07`, shared by Q-24/Q-53); `docs/benchmarks.md` "How to
  refresh the baseline" (recovery `--checker-delta --checker-gate
  --delta-limit 25 --json` → `gate` → `baseline`, accept only on 0
  crashes / 0 wrong / 0 new errors); `docs/hint-propagation.md`
  (Q-36 spec for the slots refactor: `HintIndex.create` stages, the
  12-pass `_call_sites`/`_judge_pass` fixpoint, `_judge_call_sites`
  decision order); `docs/skip-reasons.md` + `docs/skip-codes.md`
  (every `Rejection`/`SkipCode` value verbatim) +
  `tests/test_skip_docs.py`; README `## Limits` reconciled Q-43/Q-52
  into one section with the five spec bullets (two bullets predate
  M3/`--cache` — kept verbatim, flagged); `docs/typing-inference.md`
  (verbatim §18.9 table, E0–E6 one-liners, typer-rule recipe).
  `exactus --readme` regenerated the `docs/`+`scripts/` inventories.
  Gates: lints/kwargs/docs/readme PASS (0 issues), fast tier 3992
  passed; `--coverage_tests` running at journal time.
  Progress block regenerated: 122/245 (49.8%).
- **Benchmarks batch done (agent: devin):** Q-29…Q-31 — corpus grew
  113 → 128 (`copy`, `codeop`, `getopt`, `hashlib`, `hmac`,
  `genericpath`, `pyclbr`, `pprint`, `plistlib`, `random`, `runpy`,
  `site`, `symtable`, `tracemalloc`, `warnings`); recovery 324 truth /
  38 correct / **0 wrong / 0 crashes / 0 new errors**, precision 100%,
  recall 11.7%, 156.9 s, `gate` **PASS** — baseline untouched.
  `benchmarks/projects.json` 10 → 15 (`toml` 0.10.2, `tomli` 2.5.0,
  `more-itertools` 11.2.1, `tomlkit` 0.13.3, `boltons` 25.0.0; smoke
  snippets verified pre-pinning, `PINNED` count bumped 10 → 15);
  `python -m benchmarks semantic` — all 15 projects PASS (identical
  imports + smoke results). Q-31 measured, not optimised: the ~50k row
  is **infeasible in practice** — `check` alone on the 50,763-line
  workload exceeded 30 min (> 85× the 12k `check`), `fix` multiplies it
  via `max_rounds=3` + `_degrade` halving; prior attempts ran ~9 h CPU
  each. `cProfile` puts the cost in `hints.index → _candidates →
  CommentedModule.convert → _graph/backend/checkpoint._infer`
  (whole-module graph conversion per hint-index build). Row recorded in
  `docs/benchmarks.md` as a lower bound; runs left in flight →
  `/tmp/bench_50k.json`, `/tmp/bench_25k.json`. Also killed two stale
  ~9 h `profile_perf --lines 50000` orphans from a prior session that
  were contending for CPU.
  Fast tier: 4035 passed. Progress block regenerated: 125/252 (49.6%).


## Old preamble

---
agent: devin-local
session: complete-pamphlet
created: 2026-11-07T15:54:30Z
updated: 2026-11-07
---
# Astart — unified TODO

Unified execution plan merging the project precision roadmap
(docs/superpowers/roadmaps/2026-11-07-precision-roadmap.md, Phases 0–10) with
the verified defect/gap analysis: measurement + external-checker gate first,
then OO resolution, project-wide evidence, precise types, advanced
Protocol/TypeVar synthesis, first-class imports, kwargs soundness, scale, and
ontology completion.

<!-- ROADMAP_PROGRESS_SUMMARY_START -->

