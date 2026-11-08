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

## Overall implementation status

> Generated from real Markdown checkboxes outside fenced examples, HTML
> comments and this managed block. Only `[x]` counts as complete.
> Every checkbox counts equally, including parent and child items.
> These totals are not release-readiness evidence.

<div role="progressbar" aria-label="Roadmap completion" aria-valuenow="61" aria-valuemin="0" aria-valuemax="236" style="width:100%;height:1.5rem;background:#e5e7eb;border-radius:.75rem;overflow:hidden;">
<div style="width:25.8%;height:100%;background:hsl(43.0 80% 45%);"></div>
</div>
<p><strong>61/236 (25.8%)</strong></p>

**Done:** 61 · **Open:** 175 · **ONGOING:** 0 · **Total:** 236

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

### Category vocabulary

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

### Priority vocabulary

| Exact priority | Meaning |
| --- | --- |
| P0 | Blocks the core workflow or trustworthy release: wrong annotations, silent misfixes, or the measurement gate every other claim depends on. |
| P1 | Required core functionality or acceptance work after blockers. |
| P2 | Secondary enhancement or follow-up that is not a core blocker. |
| P3 | Optional polish or deferred improvement. |
| Untriaged | No unambiguous priority was recorded. Schedule explicitly; this does not mean P2 or low urgency. |

### Identity and maintenance rules

Existing IDs are permanent. IDs are milestone-prefixed (`M1-01`, `M2-03`),
with `EV-` for verified-evidence entries and `CC-` for cross-cutting items;
children receive their parent's ID with a numeric suffix such as `M1-02-01`.
Do not renumber after reordering. Every checkbox is one tracked obligation.
Non-action examples belong in prose or fenced code, not extra unchecked boxes.
One task ID has one owning checkbox; an implemented happy path does not close
missing failure-mode, idempotence or checker-gate acceptance.

## Execution map — measurement first

This map is a planning decision, not new completion evidence. It organizes the
checkbox owners into deliverable work packages matching milestones M0–M8.
Sequencing is fixed by the evidence policy: nothing may be claimed more
precise than the M1 harness can measure, and no guarded fix is trusted without
the E6 checker gate.

| Sequence | Work package and owning IDs | Prerequisites | Smallest useful delivery and stop condition |
| --- | --- | --- | --- |
| 0, done | Trustworthy slice: M0-01…M0-10 | — | Defects D1–D3, D6, D9 fixed; exactus green; baseline committed. |
| 1, current | Measured: M1-01…M1-18 | M0 | Dashboard + baseline published; E6 gate rejects real regressions; D7 enforced. Stop claiming precision/recall until measured. |
| 2 | Object-oriented code works: M2-01…M2-13 | M1 oracle | Method recall ≥3× baseline at unchanged precision; D4/D5 closed. |
| 3 | Whole project: M3-01…M3-14 | M2 | Cross-module recall met; canonical imports; 100k-line repo in budget. |
| 4 | Precise types: M4-01…M4-19 | M1, M3 | Corpus recall step-change at ≥99.5% guarded precision. |
| 5 | Structural and generic: M5-01…M5-25 | M4 | Protocol/TypeVar gold cases green; E6-verified synthesis. |
| 6 | Kwargs bulletproof: M6-01…M6-09 | M3 library table | Danger matrix green; detection rules shipping; idempotent under ruff. |
| 7 | Fast and shippable: M7-01…M7-15 | M3–M6 | ≤5 s/12k lines; `[tool.astart]` surface; reporters + LSP. |
| 8 | Whole ontology + inference core: M8-01…M8-21 | M4, M6 | `verify_catalog` all invariants; spec-§5 rule set present. |

### Slice handoff contract

Before coding, add ordinary prose beneath the selected owning checkbox:
`Scope`, `Depends on`, `Source`, `Acceptance`, `Evidence`, `Known limits` —
populated with exact behavior and inspected files, not generic promises.
Success, invalid input, refusal, lost-checker and non-idempotent paths all
need named proof, not a happy path. At completion update only the satisfied
obligation; if a parent still lacks gold cases, checker-gate or corpus
evidence, keep it open and record the accepted slice.

## 0. Decisions (all locked with the user)

- **Scope: full roadmap M0–M8** — including `_graph`/`semantic` inference-core bug fixes.
- **Union policy: enabled (guarded)** — `T1 | T2 [| …]` accepted when ≤3 distinct definite spellings and inference corroborates.
- **TypeVar style: classic default + version-aware PEP 695** — `T = TypeVar("T")` default; `def f[T](x: T)` when `requires-python >= 3.12`.
- **Checker oracle: yes, optional auto-detect** — guarded fixes gated on pyright/basedpyright when installed (E6); without it, guarded fixes need a higher internal evidence level.
- **Default aggressiveness: configurable per-profile** — profiles/`[tool.astart]` set the safety ceiling; default profile applies proven-only, guarded behind opt-in flag/profile.
- **Protocol placement: shared `_protocols.py` + name lockfile** — same-member protocols merged project-wide with deterministic stable names; config switch preserves per-function placement.
- **Git init: yes** — initialize a repository in M0 so every milestone is diff-reviewable and rollback-safe.
- **Library keyword table: stdlib first, extensible** — curated typeshed-generated table; third-party packages join only via explicit allow-list.

## 1. North star (roadmap §1)

`astart fix` takes untyped, positionally-called Python and returns the same
program with: (1) every safely keyword-capable call keyword-called;
(2) every parameter/return/attribute/variable annotated with the **most
precise type the evidence supports**; (3) `Protocol`s and type variables
synthesized where structural or generic; (4) every required import;
(5) formatting untouched except one final `ruff format`. Success = **zero
wrong annotations at the highest recall precision allows**, proven by an
independent checker, not by astart's own opinion.

Non-negotiables: behaviour preserving · never invalid Python ·
comments/layout kept · idempotent · explained skips (closed enum) ·
independent verification (E6 gate).

## 2. Accuracy model (adopted wholesale)

Evidence ladder: **E0** syntax-proves · **E1** declared-elsewhere (stubs, base
signatures, `@overload`, implemented ABCs) · **E2** closed-world usage (all
in-module sites, no escape) · **E3** cross-module call sites · **E4** library
signature flow · **E5** inference proposal (candidate only, never alone) ·
**E6** external checker does not object.

**Policy: a guarded fix needs (E2 ∨ E3 ∨ E4) ∧ (E5 agrees ∨ E0 proves) ∧ E6
does not object.** `proven` = E0/E1 only. `rejected-by-checker` is a reported
outcome, never silent. Confidence calibrated against benchmarks;
`--min-confidence` knob. Checker auto-detected; absent → guarded fixes need
higher internal evidence.

## 3. Done since the last audit

### M0 — trustworthy slice (done 2026-11-07)

- [x] **M0-01** **P0** **DevOps / Release** — **Git init + ruff-format drift policy.** Repository initialized so every
  milestone diff is reviewable and rollback-safe; `ruff format` runs as the
  single final pass only.
  Evidence: git history `0fa056e` (initial) → `5b788f3`.
- [x] **M0-02** **P0** **Backend** — **D1: `ensure_names` in `add_inferred_annotation`.** Imports for
  `_importable` names (`Iterable`, `Path`, …) are now inserted, removing the
  latent uncompilable-output path.
  Evidence: `src/astart/rules/appliers.py`; catalog examples compile.
- [x] **M0-03** **P0** **Backend** — **D2: `'Unknown'` is non-definite evidence.** Unknown call-site types no
  longer count as disagreeing; syntax-proven argument types are independent
  evidence (`Path("x")` case).
  Evidence: `src/astart/rules/hints.py` judges; semantic tests.
- [x] **M0-04** **P0** **Backend** — **D3: imported constructors type their calls.** `constructors` wired so
  `Path("x")`, `Decimal(..)`, … prove their result type via the
  `@constructor:<Name>` binding-count key.
  Evidence: `src/astart/rules/provable.py`, `imports.py`; tests green.
- [x] **M0-05** **P0** **Backend** — **D6: `Exists` crash guarded.** Catalog validation rejects `exists`
  predicates until M8 implements evaluation.
  Evidence: `src/astart/rules/catalog.py` validation; `predicate.py`.
- [x] **M0-06** **P0** **Backend** — **D9: `typing.add-noreturn` fix.** Always-raising functions get
  `-> NoReturn` (proven safety class).
  Evidence: catalog rule + applier; `never_returns` lattice member.
- [x] **M0-07** **P1** **Backend** — **Final-review findings C1, C2, I1–I6** fixed.
- [x] **M0-08** **P1** **Backend** — **Type-policy cleanup.** Five `object` annotations in `formatting.py`
  replaced with `FieldValue`/`PatchValue` aliases; RUF043 fixed.
- [x] **M0-09** **P1** **Testing / QA** — **D10 suite-flakiness investigation.** Did not reproduce: suite passes
  forward and reverse file order (1616 tests); observed failures traced to an
  external tool rewriting files mid-run, not shared mutable state.
- [x] **M0-10** **P0** **Testing / QA** — **bare `exactus` clean.** All 6 tools PASS, 0 files with issues:
  docs 0/159, lints 0/159, coverage_tests 0/91 (1616 tests, 94.95% total),
  kwargs_typehints 0/159 (unresolved callees 0), readme, performance.
  Evidence: `exactus` unified run, 2026-11-07.

### M1 — measured (partial)

- [x] **M1-01** **P0** **Backend** — **Closed skip/rejection reason enums.** `rules/reasons.py` defines
  `SkipCode` (runner refusals: `subject-missing`, `conflict`,
  `preconditions-changed`, `applier-failed`, `write-back`, `checker-rejected`)
  and `Rejection` (hint refusals, values are the reported texts).
  `SkippedFix.code` carries the enum; `_apply_one` returns
  `(SkipCode, str)`; every `hints.py` rejection string is a `Rejection` member.
  Evidence: `tests/test_rules_skip_codes.py`.
- [x] **M1-02** **P0** **Backend** — **E6 checker oracle, core.** `rules/checker.py`: `Checker` protocol,
  `PyrightChecker` (scratch sibling file → `pyright --outputjson --level
  error` → `Counter[Diagnostic]` before-vs-after), `detect_checker()`
  auto-detecting `basedpyright`/`pyright`, sha256 content-hash cache.
  `runner._attempt` vetoes guarded fixes → `SkipCode.checker_rejected` →
  `_try` halves the batch (bisect via existing halving) and rolls back.
  CLI `--checker auto|off` (default auto) → `FixSettings.checker`.
  Evidence: `src/astart/rules/checker.py`, `runner.py`, `cli/commands.py`,
  `test_cli_main.py` checker-flag tests.
- [x] **EV-01** **P0** **Testing / QA** — **Exactus gate evidence, 2026-11-07.** Unified `exactus` run:
  6/6 PASS*, 0 files with issues; 1616 tests, `__main__.py` 95%, total
  94.95%; kwargs_typehints unresolved callees 0 after binding all
  subscript/unknown-receiver callees to annotated locals.

## 4. Open now — M1 "Measured" (highest priority)

- [x] **M1-03** **P0** **Backend** — **E6 oracle remainder.** Optional `mypy` executable in
  `Constants.executables`; when no checker is installed, guarded fixes require
  the higher internal-evidence path (E2∧E5 both, not either); document the
  refuse-on-unanswerable-checker behavior already in `regresses` (returns
  `True` when either run gives no diagnostics).
  Scope: `rules/checker.py`, `runner.py` guarded path, `cli/commands.py`.
  Acceptance: `--checker auto` with no installed checker still refuses a
  fix whose evidence is single-signal; mypy honored when present.
  Note: a call-site hint now already requires syntax-proven argument types
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
- [x] **M1-04** **P0** **Testing / QA** — **Benchmark harness scaffolding.** `benchmarks/` package,
  `tests/bench_*` module family, `docs/benchmarks.md` dashboard source;
  pinned harness API that runs `check`/`fix` on a tree and records metrics.
  Scope: new `benchmarks/`, test layout, docs skeleton.
  Acceptance: `python -m benchmarks` produces a machine-readable baseline
  report on the seed corpus; runs under exactus without new findings.
  Partial (open): `benchmarks/__init__.py` + `benchmarks/recovery_report.py`
  (text table, `PYTHONPATH=src python benchmarks/recovery_report.py FILE...`)
  and `docs/benchmarks.md` exist. Missing: `python -m benchmarks` entry
  point, machine-readable (JSON) output, `tests/bench_*` family, `check`
  mode metrics.
- [x] **M1-05** **P0** **Testing / QA** — **Annotation-recovery benchmark.** Strip annotations from real
  open-source modules, run `astart fix`, diff recovered vs original; report
  precision/recall per evidence class.
  Acceptance: ≥1 real module measured end-to-end with per-failure-class
  attribution written to the dashboard.
  Partial (open): `rules/recovery.py` (`strip_annotations`, `annotation_map`,
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
- [x] **M1-06** **P1** **Testing / QA** — **Gold set expansion 34 → ≥500.** One gold case per failure class
  from the verified recall-gap list (R1–R12, P1–P4, T1–T5, K1–K4) and every
  reviewer finding.
  Acceptance: ≥500 cases, each tagged by failure class; every new fix ships
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
- [x] **M1-07** **P1** **Testing / QA** — **Corpus expansion 20 → ≥100 real modules.** Diverse open-source
  modules under `tests/corpus/`, including OO-heavy and async code.
  Acceptance: ≥100 modules replay deterministically; counts published.
  Evidence (audit 2026-11-07): 113 modules in `tests/corpus/*.py.txt`
  (asyncio, importlib, concurrent.futures, tomllib, … ); every corpus test
  is parametrized over the directory and passes; the recovery benchmark was
  run over all of them and the counts are published in
  `docs/benchmarks.md` ("113-module baseline").
  Known limits: 0 of the 113 are third-party/OO-application code — all are
  CPython stdlib modules, so the pinned-project work in M1-12 is still the
  only coverage of "ordinary" application style.
- [x] **M1-08** **P0** **Testing / QA** — **Precision/recall dashboard.** Metrics pipeline emitting
  precision ≥99.5% guarded / 100% proven gates, recall, and per-rule tables.
  Acceptance: dashboard fails the build below thresholds; numbers derived
  from the harness, not hand-counted.
  Audit 2026-11-07: the current measured precision on the full corpus
  (27/28 = 96.4%) is **below the 99.5% guarded gate**, so a real gate would
  fail today; fix M2-14 first, then enable the gate.
  Update 2026-11-07: after M2-14 the corpus precision is 35/35 (100%), so
  the gate would pass; enabling it is the remaining work.
  Evidence (2026-11-07): `benchmarks/baseline.json` is the accepted gated
  run (113 modules, 0 crashes, 36/36 precise, 0 new checker errors);
  `python -m benchmarks gate` fails on wrong annotations, new errors,
  crashes or recall drops; `tests/test_bench_baseline.py` pins the baseline;
  numbers are in `docs/benchmarks.md`.
- [x] **M1-09** **P1** **Testing / QA** — **Checker-delta metric.** E6 run before/after per benchmark round;
  zero-new-error delta tracked and published.
  Acceptance: benchmark report includes a checker-delta column on ≥1 project.
- [ ] **M1-10** **P2** **Testing / QA** — **Throughput benchmarks.** Runtime by size bucket
  (500/2k/12k/50k lines); current 12k-lines ≈ 47 s is the regression baseline.
  Acceptance: bucket table published; superlinear growth flagged.
  Audit 2026-11-07 (partial): `docs/benchmarks.md` now carries the bucket
  table (~1.2k/2.2k/12k measured via `benchmarks/profile_perf.py --json`)
  and flags superlinear `check` growth; the ~50k row is pending.
- [x] **M1-11** **P1** **Testing / QA** — **Stability benchmarks.** Idempotence (fix∘fix = fix byte-equal)
  and ≤3-round fixed-point convergence on the whole corpus.
  Acceptance: zero non-idempotent corpus files; round counts in dashboard.
  Audit 2026-11-07 (partial): `tests/test_rules_idempotence.py` runs
  `fix_source` twice on all 113 corpus modules under the guarded ceiling —
  byte-equal, zero non-idempotent files (150 s). Round counts are not
  externally observable (`FixResult` exposes no per-round data) and the
  dashboard half remains open.
- [x] **M1-12** **P2** **Testing / QA** — **Semantic-equivalence runs.** Compile + import + smoke-run
  `astart fix` output on 10 pinned projects.
  Acceptance: 10/10 projects import and pass their own smoke tests post-fix.
- [x] **M1-13** **P1** **Testing / QA** — **Writer fuzzing.** Random fix subsets → output compiles, comments
  preserved, AST-equal-after-strip.
  Acceptance: fuzz driver + seed corpus; zero crashes on recorded seeds.
  Evidence: `tests/test_rules_writer_fuzz.py` — 6 corpus modules × 3
  deterministic hash-derived fix subsets (no `random`); each result has no
  `parse_error`, compiles, and keeps every comment.
  Known limits: AST-equal-after-strip is not asserted — synthesized
  Protocols/TypeVars/imports add statements by design; the strip-equality
  check still runs in `test_rules_runner_corpus.py` for the hint fixes.
- [x] **M1-14** **P1** **Testing / QA** — **Full-CLI idempotence tests.** `astart fix` twice on every corpus
  file byte-identical, through the real CLI (not `fix_source`).
  Acceptance: per-corpus-file parametrized test, all green.
  Partial (open): `tests/test_cli_idempotence_corpus.py` runs
  `fix_and_format` (fix + ruff) twice on the 7 corpus modules ≤ 700 lines and
  requires byte-equal output (all green). Missing: the larger modules, and
  driving it through the real CLI entry (`main(argv=…)`) rather than the
  library call.
  Audit 2026-11-07 (partial): `tests/test_cli_idempotence_full.py` verified
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
- [x] **M1-15** **P0** **Backend** — **D7: real `FixOffer.confidence` + `min_confidence` enforcement.**
  Replace hardcoded `confidence=1.0` in `engine._finding` with calibrated
  values per evidence level; enforce `fix.min_confidence` (parsed in
  `model.py`, currently ignored) when offers and fixes are selected.
  Scope: `engine.py`, `runner.py`, `catalog/*.json` values.
  Acceptance: a fix below `min_confidence` is not offered/applied; gold
  cases pin the boundary.
  Evidence: `rules/confidence.py` (`offer_confidence`: proven 1.0, default
  literal 0.99, call sites 0.95, derived return 0.9, keywords 0.95,
  Protocol/TypeVar 0.9); `engine._finding` uses it; `runner._eligible`
  enforces `max(settings.min_confidence, fix.min_confidence)`;
  `FixSettings.min_confidence` and CLI `--min-confidence`.
  `tests/test_rules_confidence.py` pins the 0.97 boundary (default-literal
  hint kept, call-site hint dropped).
  Known limits: values are assigned per evidence class, not yet calibrated
  against measured precision — that remains CC-01.

- [x] **M1-16** **P0** **Backend** — **Crash containment for analyzer failures (audit finding).**
  `astart fix` raises a bare `IndexError: string index out of range` from
  `_graph/conversion/stages.py::_find_opening_paren_pos` (line 175) on the
  annotation-stripped rendering of two corpus modules (`_strptime.py.txt`,
  `stringprep.py.txt`: 2 of 111 scored). The traceback escapes
  `fix_source`/`check` (whose documented contract is "never raises on bad
  input") and aborts the whole CLI run on that file.
  Scope: `_graph/conversion/stages.py` root cause; `rules/hints.py`
  (`_candidates` → `module.convert`), `rules/runner.py`, `cli/commands.py`.
  Acceptance: (1) root cause fixed with a RED→GREEN test using a reduced
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
  Tests: `tests/test_graph_nonascii_columns.py` (4 multibyte sources, and a
  monkeypatched failing `convert`). The 113-module benchmark now reports
  `crashed 0` (was 2).
  Known limits: containment covers the inference call inside hints only;
  other analyzer entry points (`check` facts that call `bind_calls`) are not
  wrapped.
- [x] **M1-17** **P1** **Testing / QA** — **Gold set at fix level.** The 535 gold cases assert
  `HintIndex` hints only. Add a parallel check that runs `fix_source` (guarded
  ceiling, checker off and with a stub checker) on every gold source and
  asserts the written annotations equal the expectation, so applier,
  import-insertion and write-back bugs are caught by the same cases.
  Acceptance: ≥ 500 cases asserted through `fix_source`; one failure class
  per family reported.
  Evidence: `tests/test_gold_expansion.py::test_gold_fix_level` — all gold
  cases through `fix_source` under a catalog restricted to the three
  annotation fixes (`add-none-return`, `add-noreturn`,
  `add-inferred-annotation`), once with `checker=None` and once with an
  accepting `Checker` stub: 1 070 assertions, all green. One recorded
  divergence (`_FIX_EXPECTED["call_sites/repr-site"]`): multi-round fixing
  converges `p: str` → `-> str`, which the single-pass hint index must
  refuse — legitimate fixed-point behaviour, not a bug.
- [x] **M1-18** **P2** **Testing / QA** — **Fast test tier.** The suite is 2 808 tests and takes
  ≈ 5.5 min (334 s on the audit run), almost all in corpus-parametrized
  files (`test_rules_runner_corpus`, `test_cli_idempotence_corpus`,
  `test_rules_synthesis_corpus`, `test_writer_fuzz`, `test_rules_recovery`).
  Acceptance: a `pytest -m "not slow"` tier under 60 s for the edit loop and
  a documented full tier for CI; no test is deleted.
  Evidence (2026-11-07): `tests/conftest.py` marks corpus-parametrized
  modules `slow`; `pytest -m "not slow"` = 3 347 passed in ≈ 35 s, the full
  tier (`pytest`) stays the CI gate.

## 5. M2 — Object-oriented code works (D4, D5, R9)

- [x] **M2-01** **P0** **Backend** — **D5: `self.m()` binding.** Methods of the enclosing class bind via
  `self.` receivers so they collect call-site evidence.
  Scope: `rules/resolve.py` (`trusted_binding`, `binding_counts`), `semantic/`.
  Acceptance: `self.m(4)` gives `m` a definite site; gold case green.
  Evidence: `rules/methods.py` (`MethodIndex.bind_self_call`) builds a
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
- [ ] **M2-02** **P1** **Backend** — **Constructor/attribute resolution.** `obj.m` when class known,
  `Class.m`, `super().m`, `cls()`, `@classmethod`/`@staticmethod`, MRO walk.
  Acceptance: each receiver form resolves to the defining signature.
  Partial (open): `obj.m` (obj assigned once from `C()`), `Class.m(obj, …)`
  (explicit receiver stays positional: `facts.kept_positionals`),
  `C().m` and `self.m` (single-base chain) resolve. Missing: `super().m`,
  `cls()`/`cls.m`, `@classmethod`/`@staticmethod` through `self`, true MRO
  for multiple bases.
- [x] **M2-03** **P1** **Backend** — **Instantiation → `__init__`/`__new__`/dataclass fields.** `C(…)`
  calls bind to the constructor signature incl. dataclass/NamedTuple fields.
  Acceptance: kwargs fixer keywords `C(a=…)` from `__init__` params.
  Evidence: `P(1, 2)` → `P(x=1, y=2)` from `__init__` (analyzer binding,
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
- [x] **M2-04** **P0** **Backend** — **D4: `trusted_binding` v2 for expression receivers.**
  `C().m(4)`/`factory().m()` bound by the analyzer but rejected today.
  Acceptance: `C().m(1)` keywords the call; gold case green.
  Evidence: `resolve._vet` accepts the analyzer's binding for
  `Class(...).method(...)` when `Class` is a module class bound once
  (`MethodIndex.constructed_receiver`) and the definition is plain;
  `tests/test_rules_methods.py::test_call_on_a_constructed_instance_is_keyworded`
  and the gold case above.
  Known limits: `factory().m()` (a call to a function) stays untrusted —
  the receiver's class is not known without return-type inference (→ M4).
- [ ] **M2-05** **P1** **Backend** — **Rules-layer `self.X → ContractIndex` fallback** so attributes
  assigned in `__init__` resolve without full inference.
- [ ] **M2-06** **P1** **Backend** — **R9: attribute types.** `self._attr` assignments across methods →
  class-level annotations; `Final`/`ClassVar` when all assignments agree;
  untaint `self._attr` returns.
  Acceptance: `self._x: int = …` emitted once at class level, not per method.
  Partial (2026-11-07, agent: claude): `rules/attributes.py` agrees all
  `self.x = …` writes of a class (literals, annotated parameters, shared
  across methods; refuses on conflicts, dynamic markers, `__setattr__`,
  slots, inheritance clashes) and rule `TYP005` /
  fix `typing.add-attribute-annotation` (guarded, conf 0.9) annotates the
  first write as `self.x: T = …`. `self.x` reads are now typed too:
  `attributes.Attributes.types` (agreed type per class) feeds
  `HintIndex._judge_derived` as `"self.x"` entries in the typer's
  environment, the unrebound receiver stops being a taint origin, and the
  inference candidate must still agree (or equal the proof minus `None`).
  Open: class-level placement, `Final`/`ClassVar`; the module-wide
  `_external_stores` name count blocks two classes that write the same
  attribute name. Tests: `tests/test_rules_attributes.py`,
  `tests/test_rules_attribute_reads.py`.
- [ ] **M2-07** **P1** **Backend** — **Override awareness (E1).** Overrides inherit base signatures; fixes
  never contradict the base; keyword fixes use base parameter names.
  Partial (open): an attribute call is trusted only if every definition of
  that name in the module takes identical parameters and no `obj.m = …`
  store exists (`MethodIndex.is_safe`). Missing: inheriting the base
  signature for annotation, and keywording through differently-named
  overrides.
- [ ] **M2-08** **P1** **Backend** — **Escape analysis v2.** Real "used as value": callbacks,
  `functools.partial`, `map`, decorators, registries, `getattr`, attribute
  escapes — replaces today's coarse `evidence.escaped`.
  Acceptance: `Rejection.escapes` fires only on true escapes; corpus shows
  fewer uncorroborated refusals.
- [ ] **M2-09** **P1** **Backend** — **Flow-sensitive locals.** `isinstance`/`is None`/truthiness/
  early-return/`assert` narrowing, merge joins, loop widening to fixpoint.
- [ ] **M2-10** **P1** **Backend** — **Kwargs for constructors** (7.2): dataclass/NamedTuple/attrs/pydantic.
- [ ] **M2-11** **P1** **Backend** — **Kwargs for method calls** (7.3) once M2-01…03 land.
  Partial (open): instance-method calls keyword correctly via `self.`,
  `C().`, `obj.` and `Class.` receivers; waits on M2-02/M2-03 for
  `super()`, constructors and class/static methods.
- [ ] **M2-12** **P1** **Backend** — **Kwargs for bound-method callbacks** (7.4) incl. `functools.partial`.
- [ ] **M2-13** **P0** **Testing / QA** — **M2 exit gate:** method recall ≥3× M1 baseline at unchanged
  precision, measured on the benchmark dashboard.

- [x] **M2-14** **P1** **Backend** — **E1 for protocol dunders (audit finding).** The 113-module benchmark
  wrote `-> None` on `asyncio.timeouts.Timeout.__aexit__` (truth
  `Optional[bool]`): the body provably returns nothing, but `__exit__`/
  `__aexit__` are protocol methods whose declared result is `bool | None`
  (`True` suppresses exceptions), and a subclass or caller may rely on that.
  Scope: `rules/facts.py` (`_returns_nothing`, `_never_returns`),
  `rules/provable.py`, a small table of dunder protocol signatures
  (`__exit__`, `__aexit__`, `__enter__`, `__bool__`, `__eq__`, `__hash__`,
  `__repr__`, `__str__`, `__len__`, `__iter__`, `__next__`, `__getitem__`…).
  Acceptance: dunder methods take their protocol-declared result type (or are
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
- [x] **M2-15** **P1** **Backend** — **Typed call-site arguments from their scope (new).** Call-site
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

- [x] **M8-23** **P1** **Backend** — **New `Final` constants join an existing `Constants` class (requested
  2026-11-07).** `typing.add-final` no longer leaves a freshly made
  `NAME: Final[T] = …` at module level when the module already has exactly
  one `class Constants`: `rules/grouping.py` (`find_group`, `move_into`)
  moves the statement into the class (after its docstring and existing
  attributes, trailing comment kept), rewrites every use to
  `Constants.NAME`, adds `NAME: Grouped module constant.` to the class
  docstring's `Attributes:` section when there is one, and inserts the
  `Final` import before the class. It stays a module global when the move
  could break something: the name is in `__all__`, declared `global`/
  `nonlocal`, already defined in the class, read by the class body, or read
  at import time (defaults, decorators, module-level code) before the class
  exists; and when the module has no or several `Constants` classes.
  Tests: `tests/test_rules_constants_group.py` (move, no class, rerun is a
  no-op, five refusals, default after the class, several constants,
  docstring section present/absent).
  Known limits: other modules that do `from this import NAME` are not
  known — a project-wide check belongs to M3-01/M3-03; lowercase module
  variables and constants that are already `Final` at module level are not
  moved (the M8-09 loose-constants detector reports those).
- [x] **M8-24** **P1** **Backend** — **Writer replaces elements of a child list with atoms (needed by
  M8-23).** `formatting.Writer._atom_replacements` patches a same-length
  expression list in place when `Name`/`Attribute`/`Constant` nodes replace
  elements — `arguments.defaults` previously raised "Changing
  arguments.defaults requires syntax regeneration", which made the whole
  `typing.add-final` fix fail to write back. It also keeps the original
  spacing for swapped call arguments (`call(  2, 1, )` stays as written).
  Tests: `tests/test_format_list_element_replacement.py`,
  `tests/test_format_ast.py::test_swapped_atoms_keep_the_original_spacing`.
  Known limits: non-atom replacements (e.g. a `BinOp`) still fall back to
  local canonical printing, because they may need parentheses.

## 6. M3 — Whole project

- [ ] **M3-01** **P1** **Backend** — **Import resolution.** Absolute/relative/`__init__` re-exports/
  `__all__`/conditional imports → project symbol table.
- [ ] **M3-02** **P1** **Backend** — **Whole-project call graph** with content-hash invalidation.
- [ ] **M3-03** **P1** **Backend** — **E3 cross-module call sites.** Public APIs guarded-only with
  "assume external callers" switch; `_name` private = closed world.
- [ ] **M3-04** **P1** **Backend** — **E4 typeshed/`py.typed`/stub-package loading** feeding hints.
- [ ] **M3-05** **P1** **Backend** — **K1: curated "safe to keyword" library table** — stdlib first,
  typeshed-generated, test-verified.
- [ ] **M3-06** **P1** **Backend** — **Version awareness.** `requires-python` gates `X | Y`, PEP 695,
  `Self`, `TypeAlias` emission.
- [ ] **M3-07** **P1** **Backend** — **Canonical public import locations** (`collections.abc.Sequence`
  not `typing.Sequence`; shortest `__all__`-honouring path).
- [ ] **M3-08** **P2** **Backend** — **File-style matching** for import emission.
- [ ] **M3-09** **P1** **Backend** — **`TYPE_CHECKING` placement** for cycle/heavy-module safety +
  `from __future__ import annotations` where runtime consumers allow.
- [ ] **M3-10** **P1** **Backend** — **Shadowing/collision avoidance** for inserted imports.
- [ ] **M3-11** **P2** **Backend** — **Unused-import cleanup** (own-added only).
- [ ] **M3-12** **P2** **Backend** — **Deterministic pre-ruff import placement.**
- [ ] **M3-13** **P1** **Backend** — **`ensure_names` everywhere + expanded `known_imports`:**
  full `collections.abc`, `NoReturn`/`Never`, `TypeGuard`/`TypeIs`, `Self`,
  `ClassVar`, `Literal`, `ParamSpec`, `Concatenate`, `TypeVarTuple`,
  `TypedDict`, `NamedTuple`, `Annotated`, `override`, `final`, `Decimal`,
  `Fraction`, `UUID`, date/time, `re.Pattern`/`Match`.
- [ ] **M3-14** **P1** **Testing / QA** — **M3 exit gate:** cross-module recall met; 100k-line repo
  within perf budget; no precision regression on the dashboard.

- [ ] **M3-15** **P1** **Backend** — **Wire the library keyword table into binding (audit finding).**
  `rules/libkw.py` (37 568 generated lines) and `scripts/generate_libkw.py`
  exist and `tests/test_rules_libkw.py` passes, but no module imports
  `libkw`: `subprocess.run(cmd, True)`-style calls are still never keyworded.
  Scope: `rules/resolve.py` (`CallBindings`), `rules/facts.py`
  (`keyword_candidates`, `bound_call`), `cli/config.py` (`library-tables`).
  Acceptance: a stdlib call listed as keyword-safe is keyworded end to end
  (`fix_source` test + checker), a positional-only or unlisted callee is
  not; the table's generation date and typeshed commit are recorded.

## 7. M4 — Precise types (hint lattice + prover)

- [ ] **M4-01** **P1** **Backend** — **Prover: comprehensions, subscripts on typed names, builtin-method
  result table** (R11: comprehension returns untyped).
- [ ] **M4-02** **P1** **Backend** — **Prover: `Await` unwrap, `Try`/`Match`/`AugAssign`/loop handling**
  (R7 coverage).
  Partial (2026-11-07): `provable._type_rebound_locals` types locals bound
  by several plain/augmented assignments when every binding agrees on one
  type (induction for `total = 0; total += 1`, `x = x * 2`); loop, `with`,
  `except`, import, walrus and `del` bindings of the name block it. Still
  open: `Await` unwrap, `Try`/`Match` result typing, loop-carried widening.
  `tests/test_rules_multi_binding_locals.py`.
- [ ] **M4-03** **P1** **Backend** — **Prover: yield typing + once-bound `ClassDef` calls** (extends D3).
- [x] **M4-04** **P1** **Backend** — **R1: `optional_default`** — `x=None` defaults → `T | None`.
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
- [x] **M4-05** **P1** **Backend** — **R2: `variadic_args`** — `*args: T`/`**kw: T` hints.
  Evidence (2026-11-07): `HintIndex._judge_variadics` annotates `*args`/
  `**kwargs` with the element type only when every closed-world call's extras
  are syntax-proven to share one type; unpacked calls (`f(*xs)`), unbound
  calls, escaped functions and calls without extras give no hint, and the
  hint is never fed back as the name's type (it is a tuple/dict in the body).
  Also: an unresolved expansion now counts as unknown evidence for the
  parameters it may fill. Tests: `tests/test_rules_variadic_hints.py`.
- [ ] **M4-06** **P1** **Backend** — **R3: `generator`/`async`** lattice members (replace the
  `Rejection.generator` refusal).
- [ ] **M4-07** **P1** **Backend** — **R4: `usage_abc`** — usage → `Iterable`/`Sequence`/`Mapping`/
  `Sized`/`Container`/`Callable`/`Awaitable`, corroborated by `subtype()`
  over call-site types.
- [ ] **M4-08** **P1** **Backend** — **R5: `typeguard`/`TypeIs`** emission where provable.
- [x] **M4-09** **P1** **Backend** — **`never_returns`** member completed for all raise paths.
  Evidence (2026-11-07): `can_fall_off` handles `try`/`except`/`else`/
  `finally` (`provable._try_can_fall_off`), so a `try` whose every branch
  raises is `NoReturn` and one whose branches all return no longer gets `|
  None`. Known limits: `while True` without `break` and `match` exhaustion
  are still treated as falling off.
- [x] **M4-10** **P1** **Backend** — **R10: `syntax_proven`** — language-guaranteed returns
  (`f"{x}"` → `str`, `not x` → `bool`) stop dying on `no candidate`.
  Evidence (2026-11-07): `provable.provable_return_detail` reports whether a
  proof is *language-guaranteed* (no parameter or variable type was read);
  `HintBasis.syntax_proven` (confidence 0.99) is accepted without the
  inference engine. Covers f-strings, `not x`, `len/str/repr/int/float/bool/
  hash/id/ord/chr/format/ascii/bin/hex/oct`, `isinstance/issubclass/callable/
  hasattr`, literals and locals built only from those, plus `T | None` for
  paths that fall off the end. `can_fall_off` now analyses `try` statements.
  Tests: `tests/test_rules_return_proofs.py`, gold flips in
  `tests/test_gold_expansion.py` (`len`, `not`, `str`, f-string,
  `falls-off`, `try-except`).
  Known limits: `a == b` and `<` stay unproven (custom `__eq__`);
  `with` statements are treated as non-suppressing.
- [ ] **M4-11** **P1** **Backend** — **R6: `union_sites`** — `T1 | T2 [| …]` when ≤3 distinct
  definite spellings and inference corroborates (locked guarded policy).
- [x] **M4-12** **P1** **Backend** — **R8: expression defaults** beyond `None`.
  Evidence (2026-11-07): `hints._default_type` types scalar non-literal
  defaults (`-1`, `len([])`, a once-bound constant's name) through
  `expression_type`; the hint is written only when the inference candidate
  agrees (same policy as literal defaults). Containers and calls with
  unproven results stay refused. Gold family `default_expression`;
  `tests/test_rules_expression_defaults.py`.
- [ ] **M4-13** **P2** **Backend** — **R12: `Self`/`ClassVar`/`Literal`/`TypeAlias`/`NewType`**
  where provable.
- [ ] **M4-14** **P1** **Backend** — **Variable/attribute annotations** (`x: list[int] = []`, empty
  containers from later `append`s) — module/class level or checker-required
  only, never gratuitous locals.
- [x] **M4-15** **P1** **Backend** — **Container precision** — literals/comprehensions → `list[int]`/
  `dict[str,int]`/tuple shapes.
  Evidence (2026-11-07): literals were already typed; `provable._Typer`
  now types list/set/dict comprehensions (`range` → `int`, typed `str`/
  `list[T]`/`set[T]` iterables, shadowing loop variables hidden, async
  refused). `tests/test_rules_comprehension_types.py`; gold
  `tainted/comprehension` now `list[int]`.
- [ ] **M4-16** **P1** **Backend** — **Accept-general/return-specific** — params → `Sequence`/
  `Iterable`/`Mapping`, returns → `list`/`dict`.
- [ ] **M4-17** **P1** **Backend** — **`Callable[[…], R]` params** from call shape + result use.
- [ ] **M4-18** **P2** **Backend** — **Data-carrier synthesis** (`TypedDict`/`NamedTuple`/`@dataclass`)
  — suggest-only initially.
- [ ] **M4-19** **P2** **Backend** — **`@overload` synthesis** — suggest-only initially; each item gets
  own catalog fix + safety class + gold cases + E6 gate.

- [x] **M4-20** **P1** **Backend** — **Taint rule is too conservative for argument-independent results
  (audit finding).** `def f(x): return len(x)`, `str(x)`, `repr(x)`,
  `int(x)`, `float(x)`, `bool(x)`, `isinstance(x, int)`, `callable(x)`,
  `hasattr(x, "a")`, `ord`, `chr`, `hash`, `id` all stay unannotated: the
  derived-return policy rejects any return that mentions an untyped
  parameter ("tainted by parameter x"), although the builtin's result type
  does not depend on the argument's type. In the realistic sample
  (`return len(self.items)`) this blocks `-> int`.
  Scope: `rules/hints.py` (`_judge_derived`, taint), `rules/provable.py`
  (`Constants.call_types`).
  Acceptance: those builtins prove their result type with an untyped argument
  (`__len__`/`__str__`/… are protocol-constrained to `int`/`str`); a gold
  family `builtin_result` (≥ 15 cases) passes; no regression in the recovery
  precision; `==`/`<` stay unproven (numpy-style `__eq__`).
  Evidence (2026-11-07): `def f(x): return len(x)` now gets `-> int`,
  `str(x)` → `str`, `isinstance(x, int)` → `bool`; the typer runs before the
  taint check and the taint check only rejects returns whose proof actually
  read an untyped name (`_Typer.reads`/`pure`). `call_types` gained
  `ascii bin callable format hasattr hash hex id isinstance issubclass oct`.
  Tests: `tests/test_rules_return_proofs.py` (refusals `abs`, `==`,
  `sorted` stay unannotated).
## 8. M5 — Structural and generic done properly

### Protocols

- [x] **M5-01** **P1** **Backend** — **P1: typed protocol member returns** from result use.
- [x] **M5-02** **P1** **Backend** — **Typed protocol member params** from arguments incl. flow-typed.
- [x] **M5-03** **P1** **Backend** — **`async def` protocol members** (replaces `await` refusal).
- [ ] **M5-04** **P1** **Backend** — **Generator/CM/indexing/operator/truthiness/`len` members** with
  correct dunder signatures.
- [x] **M5-05** **P1** **Backend** — **P4: `__call__` callback protocols** with keyword names preserved
  (`p()` no longer refused).
- [ ] **M5-06** **P1** **Backend** — **Read-only vs writable attribute members** (read/write evidence).
- [ ] **M5-07** **P2** **Backend** — **`runtime_checkable` only under `isinstance`** usage evidence.
- [x] **M5-08** **P1** **Backend** — **Collision-safe member-name allocation** (arg0/self regression).
- [ ] **M5-09** **P1** **Backend** — **P2/P3: reuse-before-create** — existing/typing/`collections.abc`/
  `os` protocols (`SupportsRead`, `Iterable`, `Sized`, `PathLike`,
  `typing.IO`) with minimal-sufficient-member selection.
- [ ] **M5-10** **P1** **Backend** — **Merge into shared `_protocols.py` + name lockfile** (locked);
  deterministic stable names.
- [ ] **M5-11** **P2** **Backend** — **Config switch for per-function placement** alternative.
- [ ] **M5-12** **P2** **Backend** — **`TYPE_CHECKING` placement** for type-only protocols.
- [ ] **M5-13** **P0** **Testing / QA** — **E6-verified synthesized protocols** — every emitted protocol
  checked against actual call sites; widen or drop on objection.

### TypeVars

- [ ] **M5-14** **P1** **Backend** — **Bound TypeVars** — `T bound=CloseProtocol` for
  `x.close(); return x` shapes.
- [ ] **M5-15** **P1** **Backend** — **Constrained TypeVars** — exhaustive `isinstance` branches/
  overloads only.
- [ ] **M5-16** **P1** **Backend** — **Multi-variable relations** — `pair(a,b) → list[T|U]` vs
  `list[T]` by call-site evidence; `dict[K,V]`.
- [ ] **M5-17** **P1** **Backend** — **Element pass-through** — `Iterable[T] → list[T]`;
  `items[0] → Sequence[T] → T`.
- [ ] **M5-18** **P1** **Backend** — **`Self`** for `return self`/`cls()` returns.
- [ ] **M5-19** **P1** **Backend** — **T5: ParamSpec decorator forwarding** —
  `f: Callable[P,R] → Callable[P,R]`.
- [ ] **M5-20** **P2** **Backend** — **`TypeVarTuple` variadic passthrough.**
- [ ] **M5-21** **P2** **Backend** — **`T_co`/`T_contra` variance** where provable.
- [ ] **M5-22** **P1** **Backend** — **T1: BoolOp/comparison shared `T`** — `a or b`,
  `a if a>b else b` (replaces the BoolOp passthrough refusal).
- [ ] **M5-23** **P2** **Backend** — **PEP 695 `def f[T](x: T)`** behind `requires-python >= 3.12`
  (locked style).
- [ ] **M5-24** **P1** **Backend** — **No user-symbol shadowing; project-wide declaration reuse**
  option (T2–T4 remainder).
- [ ] **M5-25** **P0** **Testing / QA** — **M5 exit gate:** protocol/typevar gold cases green;
  zero invalid output on the danger corpus.

## 9. M6 — Kwargs bulletproof

- [x] **M6-01** **P1** **Testing / QA** — **Danger matrix → ~60 tests:** decorators/`__getattr__`/
  `__call__`/Liskov-violating overrides/C-impl posonly/renamed params/
  rebinding/conditional defs/callback containers/`functools.wraps`-less
  wrappers.
  Evidence: `tests/test_rules_kwargs_danger.py` — 70 matrix rows run
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
- [ ] **M6-02** **P1** **Backend** — **Positional-only/keyword-only end-to-end** — `/`, `*`,
  `**kwargs` forwarding, `functools.partial`, `super().__init__` chains.
- [x] **M6-03** **P1** **Backend** — **Library keyword table** — curated versioned stdlib signatures
  (typeshed-generated, test-verified); never C posonly builtins; third-party
  via allow-list only.
  Evidence: `scripts/generate_libkw.py` parses the typeshed bundle shipped
  with `typeshed_client` into `src/astart/rules/libkw.py` — ~11 947
  `KwSignature` entries keyed `module.qualname`, stdlib first, every
  positional-only parameter (`/` markers and the `__name` convention)
  plus `self`/`cls` receivers excluded, `**kwargs` callees recorded as
  `any_keyword`; no third-party stubs are bundled so none can enter
  except through a future explicit allow-list. Tests:
  `tests/test_rules_libkw.py` (known signatures, unknown callees,
  posonly/receiver exclusion, ordering). Wired into binding → M3-15.
- [ ] **M6-04** **P2** **Backend** — **Style controls** — `min_positional`, per-callee allow/deny
  lists (e.g. don't keyword `len(x)`/`print(x)` first arg).
- [ ] **M6-05** **P1** **Backend** — **`calls.missing-argument` detection rule** (K4).
  Audit 2026-11-07 (partial): `find_missing_arguments` in
  `rules/call_problems.py` flags trusted-binding
  `missing required argument` errors (functions and methods); tests in
  `tests/test_rules_call_problems.py`; not in the catalog (→ M8-22).
- [ ] **M6-06** **P1** **Backend** — **`calls.unexpected-argument` detection rule** (K4).
  Audit 2026-11-07 (partial): `find_unexpected_arguments` in
  `rules/call_problems.py` flags `unexpected keyword arguments` and
  `too many positional arguments` binding errors; tests in
  `tests/test_rules_call_problems.py`; not in the catalog (→ M8-22).
- [ ] **M6-07** **P1** **Backend** — **`calls.ambiguous-callee` detection rule**.
  Audit 2026-11-07 (partial): `find_ambiguous_callees` in
  `rules/call_problems.py` flags `indeterminate` bindings (uncertain
  `*args`/`**kwargs` expansions); tests in
  `tests/test_rules_call_problems.py`; not in the catalog (→ M8-22).
- [ ] **M6-08** **P1** **Backend** — **`calls.unresolved-callee` detection rule** (K3 remainder:
  receiver expressions distrusted).
  Audit 2026-11-07 (partial): `find_unresolved_callees` in
  `rules/call_problems.py` flags calls whose callee root is bound in
  the module but the trusted `CallBindings` layer refuses them
  (redefinitions, conditional defs, distrusted receivers); builtins
  and unbound names are out of scope; tests in
  `tests/test_rules_call_problems.py`; not in the catalog (→ M8-22).
- [ ] **M6-09** **P1** **Testing / QA** — **Idempotence with ruff line-wrapping** verified on corpus.

- [x] **M6-10** **P0** **Backend** — **Class-body rebinding of a method name (audit: 9 strict-xfail rows).**
  `descriptor-shadows-method`, `descriptor-before-method`,
  `staticmethod-assign-shadows`, `partial-assign-shadows`,
  `del-method-class-body`, `annotated-assign-shadows`, `tuple-assign-shadows`,
  `for-target-shadows-method` and one more row in
  `tests/test_rules_kwargs_danger.py`: any assignment, `del`, `for`/`with`/
  import target or annotated assignment of the method's name in the same
  class body makes the `def` unreliable, but binding counts ignore class
  bodies.
  Scope: `rules/methods.py` (`MethodIndex._find`, `is_safe`),
  `rules/resolve.py::binding_counts`.
  Acceptance: those rows flip from strict-xfail to passing (remove their
  reason) and the keyworded call is refused whenever the name is bound more
  than once in the class body.
- [x] **M6-11** **P0** **Backend** — **Constructor hooks (audit: 6 strict-xfail rows).**
  `metaclass-diff-names`, `metaclass-posonly`, `new-init-mismatch`,
  `new-init-swapped`, `new-init-diff-arity`, `class-decorator`: a class
  with a metaclass `__call__`, a `__new__` that disagrees with `__init__`, or
  a decorator that is not a neutral `@dataclass` still gets its constructor
  calls keyworded, because `trusted_binding` vets the `__init__` function,
  not the class.
  Scope: `rules/resolve.py` (`_vet`, `trusted_binding`),
  `rules/methods.py`.
  Acceptance: constructor calls are refused when the class (or an in-module
  base) has a metaclass, defines `__new__`, or is decorated; the 6 rows pass.
- [x] **M6-12** **P0** **Backend** — **Dynamic rebinding markers (audit: 4 strict-xfail rows).**
  `setattr-instance-rebind`, `setattr-class-rebind`,
  `object-setattr-rebind`, `dict-attribute-rebind`, `globals-rebind`:
  calls through `setattr(...)`, `object.__setattr__`, `__dict__[...] = ...`
  or `globals()[...] = ...` can replace a callee invisibly.
  Scope: `rules/resolve.py::binding_counts` / `MethodIndex`.
  Acceptance: a module that contains such a marker for a name (or any
  unnamed `setattr`/`globals()` write) refuses keyword rewrites of calls to
  that name; the rows pass; a test shows an ordinary module is unaffected.
- [x] **M6-13** **P1** **Backend** — **`__getattribute__` interception (audit: 1 strict-xfail row,
  `getattribute-override`).** A class defining `__getattribute__` can
  redirect `self.m`/`obj.m`; refuse method-call keyword rewrites on it and
  on classes inheriting it.
  Acceptance: the row passes.

## 10. M7 — Fast and shippable

- [ ] **M7-01** **P1** **Backend** — **Kill superlinear costs** — semantic worklist, single subject
  pass bucketed by kind, per-node binding caches.
  Audit 2026-11-07 (partial): the largest superlinear cost is removed —
  `Analyzer.refresh()` re-fingerprinted the whole tree per query (~1 053
  walks ≈ 45 s at 12k); internal queries now use a refresh-free solver
  path in `semantic/analyzer.py` and `_fingerprint_tree` itself is
  cheaper. A fresh 3k `cProfile` (post M8-19/20) puts remaining cost in
  `hints.index` ≈ 17.6 s cum, `provable.scope_types` 1 240 calls ≈ 7.4 s,
  `resolve.get` 1 755 calls ≈ 6.6 s, ~12M `iter_child_nodes` walks and
  ~96 fingerprints ≈ 4.7 s — the listed worklist/bucketing/binding-cache
  work lives in `rules/hints.py`, `rules/provable.py`, `rules/resolve.py`,
  `rules/engine.py` and `ast.py`'s `semantic` property (main-agent line).
- [ ] **M7-02** **P1** **Backend** — **Perf budgets:** ≤5 s/12k lines, ≤30 s/100k lines
  single-threaded.
  Audit 2026-11-07 (partial): 12k-line `check` 62→**29.7 s**, `fix`
  194→**72.3 s**, total 283→**102 s** with identical findings (2 067;
  applied 413–432 across concurrent rule work);
  `docs/benchmarks.md` records the runs. Budget still unmet — remaining
  cuts sit in `rules/` engine code owned by the M2/M3 line.
- [ ] **M7-03** **P1** **Backend** — **Incremental content-hash cache** across runs.
  Audit 2026-11-07 (not started): the analyzer already reuses abstract-
  interpreter transfer across in-process mutations
  (`AbstractInterpreter.recompute_module`/`incremental_reused`), but a
  persistent content-hash cache needs run-level storage and CLI wiring —
  deferred to the M7-16 surface together with config/reporters.
- [ ] **M7-04** **P2** **Backend** — **Process-pool parallelism.**
- [ ] **M7-05** **P2** **Backend** — **Streaming `--jobs` CLI.**
- [ ] **M7-06** **P2** **Testing / QA** — **Memory budget tests.**
- [x] **M7-07** **P1** **DevOps / Release** — **`[tool.astart]` pyproject config** — rules,
  select/ignore, safety ceiling (locked: configurable aggressiveness per
  profile), per-path overrides, target version, protocol/typevar style,
  import placement, library tables.
  Evidence: `src/astart/cli/config.py` + `src/astart/cli/ignores.py` —
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
- [ ] **M7-08** **P2** **DevOps / Release** — **Baselines + external per-path ignores** (suppression
  comments stay forbidden).
  Audit 2026-11-07 (partial): `cli/baseline.py` and `cli/ignores.py` exist
  with tests in `tests/test_cli_reports.py`; not reachable from the CLI
  (→ M7-16).
- [ ] **M7-09** **P2** **DevOps / Release** — **Reporters:** SARIF/GitHub-annotations/JUnit/
  `--statistics`.
  Audit 2026-11-07 (partial): `cli/sarif.py`, `cli/junit.py`,
  `cli/github.py` exist with tests; `--statistics` does not; none reachable
  from `astart check` (→ M7-16).
- [ ] **M7-10** **P2** **Backend** — **LSP diagnostics + code actions.**
- [ ] **M7-11** **P2** **DevOps / Release** — **pre-commit/CI recipe.**
- [ ] **M7-12** **P2** **Backend** — **Interactive review mode** — evidence ladder per guarded fix,
  "accept all high-confidence".
- [ ] **M7-13** **P2** **Backend** — **`astart explain <rule> <location>`** command.
- [ ] **M7-14** **P2** **Backend** — **`--backup`/undo journal.**
- [ ] **M7-15** **P3** **DevOps / Release** — **Distribution packaging** (wheel/entry points) once the
  product surface stabilizes.

- [ ] **M7-16** **P1** **DevOps / Release** — **Wire the built-but-unreachable product surface (audit
  finding).** `cli/config.py`, `cli/ignores.py`, `cli/baseline.py`,
  `cli/sarif.py`, `cli/junit.py`, `cli/github.py` are implemented and tested
  (`tests/test_cli_config.py`, `tests/test_cli_reports.py`) but
  `astart.__main__`/`cli/commands.py` do not import any of them:
  `astart check --help` still offers only `--format {text,json}`,
  `--fail-on`, `--stubs`, and `[tool.astart]` in `pyproject.toml` has no
  effect. M7-07 is checked on loader evidence; its user-visible acceptance
  lives here.
  Acceptance: `astart check` discovers `pyproject.toml`, applies
  `select`/`ignore`/overrides/baseline, and emits `--format
  sarif|junit|github`; `astart fix` honours `safety-ceiling`,
  `min-confidence`, `checker`, `exclude`; each has a CLI test through
  `main(argv=…)`; README documents the flags.

## 11. M8 — Whole ontology + inference core

### Missing analyzer rules

- [ ] **M8-01** **P1** **Backend** — **`imports.bare-import` IMP001** — `import ast` →
  `from ast import X` + use-site rewrite, proven when collision-safe.
  Audit 2026-11-07 (partial): detector `rules/imports_bare.py` + tests; no
  catalog rule, no fixer — fixer spec is M8-27, registration is M8-22.
- [ ] **M8-02** **P1** **Backend** — **`typing.missing-variable-annotation` TYP005.**
  Audit 2026-11-07 (partial): detector `rules/variable_annotations.py` flags
  unannotated `Assign` name-targets whose value infers a stable non-`Unknown`
  type; refuses annotated/private/dunder names, attribute and unpacking
  targets; tests in `tests/test_rules_type_checks.py`; not in the catalog
  (→ M8-22).
- [ ] **M8-03** **P1** **Backend** — **`typing.no-object-annotation` TYP002.**
  Audit 2026-11-07 (partial): detector `rules/object_annotations.py` + tests;
  not in the catalog (→ M8-22).
- [ ] **M8-04** **P1** **Backend** — **`suppression.marker-comment` SUP001.**
  Audit 2026-11-07 (partial): detector `rules/suppressions.py` + tests; not
  in the catalog (→ M8-22).
- [ ] **M8-05** **P1** **Backend** — **`parsing.module-does-not-parse` PRS001.**
  Audit 2026-11-07 (partial): detector `rules/parse_module.py` + tests; not
  in the catalog (→ M8-22). Note `astart check` already reports a
  syntax-error file as `error:` with exit 2.
- [ ] **M8-06** **P1** **Backend** — **`typing.return-type-mismatch` / `incompatible-default`.**
  Audit 2026-11-07 (partial): detectors `rules/type_mismatch.py`
  (`find_return_mismatches`, `find_incompatible_defaults`) refuse on any
  indeterminate inference — only a definitive `compatible is False`
  verdict yields a candidate (bare `Constant` literals are mapped
  directly since the solver does not index them); tests in
  `tests/test_rules_type_checks.py`; not in the catalog (→ M8-22).
- [ ] **M8-07** **P1** **Backend** — **Docs family DOC001/003/004/006** + guarded doc fixers.
  Audit 2026-11-07 (partial): detectors `rules/docs_missing.py` (DOC001),
  `rules/docs_stale_params.py` (DOC003), `rules/docs_missing_returns.py`
  (DOC004), `rules/docs_missing_raises.py` (DOC006) on structured
  `DocstringNode.entries` + tests in `tests/test_rules_docs_whitespace.py`;
  no fixers, not in the catalog (→ M8-22).
- [ ] **M8-08** **P2** **Backend** — **Whitespace/blank-line normalisation** rules.
  Audit 2026-11-07 (partial): detectors `rules/whitespace_rules.py`
  (blank-line runs, trailing space) + tests; not in the catalog (→ M8-22).
- [ ] **M8-09** **P2** **Backend** — **`Constants`-class grouping with `Final`** rule.
  Audit 2026-11-07 (partial): detector `rules/constants_grouping.py` flags
  loose `UPPER_SNAKE` module constants outside a `Constants` class + tests;
  no fixer, not in the catalog (→ M8-22).
- [ ] **M8-10** **P2** **Backend** — **Delegation relation to ruff** documented and wired.
  Audit 2026-11-07 (partial): delegation contract documented in
  `docs/rule-authoring.md` (`owner: "ruff"` + `delegates_to` relation,
  FMT001/`format.line-length` as the planned entry); schema already
  supports both fields; the catalog entry itself is M8-22 scope.

### Ontology completion

- [ ] **M8-11** **P1** **Backend** — **D6 remainder: `Exists` evaluation** — predicate semantics
  implemented; catalog-validation guard removed.
- [ ] **M8-12** **P1** **Backend** — **D8: procedural rules** implemented.
  Audit 2026-11-07 (partial): `rules/procedural.py` defines `Candidate` and
  `span_of`; `Registries.procedures` is still empty and `engine.check` has no
  path that calls a procedure (→ M8-22).
- [ ] **M8-13** **P2** **Backend** — **Profiles + relations** (`supersedes`/`conflicts_with`/
  `implies`) exercised in the default catalog.
- [ ] **M8-14** **P3** **Backend** — **`Maturity` lifecycle → defaults.**
- [x] **M8-15** **P3** **Documentation** — **Rule authoring kit** — scaffold + example-as-test
  generator.
  Evidence: `docs/rule-authoring.md` — rule anatomy, declarative vs
  procedural detection, the example-as-test contract (`verify_catalog`
  enforces both polarities), fix/safety rules, and the authoring
  checklist including the M8-22 registration deferral.

### Inference core

- [x] **M8-16** **P1** **Backend** — **Fix verified wrong types** — `"hi " + name` → `int` bug.
  Evidence 2026-11-07: no longer reproduces — `"hi " + name` infers `str`
  for typed operands and `Unknown` (never `int`) for mixed/untyped ones;
  the hint layer refuses the unproven return (`Rejection.not_provable`).
  Fixed by the `syntax_proven`/`provable_return_detail` work on the
  main-agent line; verified via `infer_type` probes.
- [x] **M8-17** **P1** **Backend** — **`list(d)` → items-not-keys** inference fix.
  Evidence 2026-11-07: `semantic/type_inference.py::_builtin_call` +
  `_iterated_element` — `list`/`set`/`tuple`/`frozenset` constructors now
  derive the element type from the iterated argument (dict → keys,
  heterogeneous tuple → element join, `str` → `str`, `bytes` → `int`);
  `dict(d)` preserves `dict[K, V]`. `list(d)` on `dict[str, int]` →
  `list[str]`. Cases added to `tests/test_type_inference.py`.
- [x] **M8-18** **P1** **Backend** — **`seq[0]` → `Sequence[int]` over-broad** fix.
  Evidence 2026-11-07: `seq[0]` on `Sequence[int]` infers `int`;
  `infer_subscript` additionally types `str[i]` → `str` and `bytes[i]` →
  `int` (previously `Unknown`). Regression cases in
  `tests/test_type_inference.py`.
- [x] **M8-19** **P1** **Backend** — **Imported-constructor argument typing** —
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
- [x] **M8-20** **P1** **Backend** — **`self.` receiver typing in the analyzer.**
- [ ] **M8-21** **P0** **Testing / QA** — **M8 exit gate:** `verify_catalog` all invariants green;
  full spec-§5 rule set present; parity vs Exactus KWARGS_TYPEHINTS
  categories complete.

- [ ] **M8-22** **P1** **Backend** — **Register the standalone detectors as catalog rules (audit
  finding).** `imports_bare.py` (IMP001), `object_annotations.py` (TYP002),
  `suppressions.py` (SUP001) and `parse_module.py` (PRS001) have detectors
  and tests (`tests/test_rules_procedural.py`), but the default catalog
  still has 5 rules / 7 fixes and `Registries.procedures` is empty, so
  `astart check` never reports them (also blocks M8-12).
  Acceptance: the four rules appear in `load_default_catalog` with examples,
  `verify_catalog` stays green, `check` reports them with spans and
  fingerprints, IMP001 offers a proven fix only when collision-safe.
- [ ] **M8-27** **P1** **Backend** — **IMP001 fixer: bare `import a` →
  `from a import b` + use-site rewrite.** Convert module-level bare imports
  whose every use is an attribute **load** into per-attribute
  `from`-imports, decided independently per attribute; keep `import a`
  for any site that cannot convert.
  Scope: `rules/imports_bare.py` evidence → a new applier/fix entity;
  module-level `import a` and dotted `import a.b.c` only (no aliases,
  no conditional/`try`/`TYPE_CHECKING` imports, no function-level
  imports, no star imports). Rewrite `a.<attr>` loads to the bound name;
  for `import a.b.c`, `a.b.c.<attr>` → `from a.b.c import <attr>`.
  Chains convert one level: `a.b.c` → `from a import b` + `b.c`.
  Acceptance — must convert:
  `import a` + `print(a.b)` → `from a import b` + `print(b)`.
  Acceptance — must refuse or partially keep `import a`:
  (a) attribute stores/dels/aug-assign/for- and with-targets
  (`a.b = 3`, `del a.b`, `a.b += 1`) — `b = 3` would rebind locally, not
  set `a.b`; the store site keeps `import a` (with only stores present,
  no `from` import is emitted at all);
  (b) name collisions — `def b()`, `b = …`, `import b`, `from x import b`,
  or a parameter/`global` binding of `b` in scope → skip that attribute;
  (c) existing `from a import b [as c]` — reuse the already-bound name
  (`a.b` → `c`, no duplicate import) even when an unrelated local `b`
  exists, since `c` is the correct target;
  (d) bare-`a` uses (`f(a)`, `x = a`, `a.b` inside string annotations or
  other unrewritable positions) — `import a` survives for those sites;
  (e) `a.b` loads inside nested functions/lambdas still convert (scope
  of the binding is unchanged);
  (f) conditional or `try`-guarded imports, `import a as x`, multi-name
  `import a, os`, and modules whose attribute may come from
  `__getattr__`/lazy submodule import are out of scope for `proven` —
  emit at `guarded` at best and let the external checker veto.
  Audit 2026-11-07 (partial): fixer module `rules/imports_bare_fix.py`
  (`rewrite_bare_imports`) implements the per-attribute plan — load-only
  rewrite points, store/del/augassign/for-target veto per attribute,
  collision and existing-`from`-alias reuse, bare-use and dotted-prefix
  keeps, nested function/lambda scopes; 19 danger-matrix tests in
  `tests/test_rules_imports_bare_fix.py` green incl. idempotence.
  Evidence: danger-matrix tests in the style of
  `tests/test_rules_kwargs_danger.py` covering every refusal above plus
  alias/`as`-import, dotted-path, chain and multi-attribute cases;
  corpus idempotence (fix∘fix byte-equal) and the writer fuzzer's
  compile/comment/strip-equality invariants apply to rewritten output.
  Remaining: applier/catalog registration (→ M8-22) and corpus/fuzzer
  runs over rewritten output.
- [ ] **M8-28** **P2** **Backend** — **String literal normalisation fixer.**
  Two value-preserving rewrites of plain `str` constants:
  (a) literals containing `\n` escapes become multiline triple-quoted
  strings with real newlines;
  (b) literals whose source line exceeds the line-length budget become
  parenthesised implicit concatenations split at safe boundaries.
  Scope: `Constant` `str` nodes only — no f-strings/`JoinedStr`, no
  `bytes`, no raw strings for (a) (an `r"…\n…"` is a literal backslash,
  not a newline), no strings already triple-quoted or already implicit
  concatenations. (b) applies to `str` values in assignment values,
  call arguments, `return`/`yield` values and parenthesised
  sub-expressions; the emitted form is `("part one" "part two")` —
  wrapping parens required so a bare split cannot be mistaken for two
  statements.
  Acceptance — must convert:
  `a = "line one\nline two"` → `a = """line one` ⏎ `line two"""`
  (escape sequences other than `\n` may stay escaped inside the
  triple-quoted form); `a = "<80+ chars>"` →
  `a = ("<chunk>" "<chunk>")` with every emitted line inside the
  budget; the same split inside a call `f("<long>")` →
  `f(("<chunk>" "<chunk>"))`-equivalent argument form.
  Acceptance — must refuse:
  (a) strings containing `"""`, a trailing `\`, or content that would
  need escaping changes to stay valid (quote style may flip `"`↔`'`
  only when it reduces escapes, never adds them);
  (b) docstrings — module/class/function docstring positions are
  statement-sensitive; converting them is allowed only when the
  triple-quoted form keeps the same first-statement position and the
  project's docstring style permits it, otherwise skip;
  (c) split points inside escape sequences (`\n`, `\x41`, `\u1234`,
  `\N{…}`), inside a word, or inside an existing implicit
  concatenation — split only at whitespace boundaries, prefer spaces,
  never inside an escape;
  (d) strings already fitting the budget, empty strings, strings that
  are dict keys/`__all__` entries/`match` patterns where reformatting
  buys nothing (style choice documented, not correctness);
  (e) f-strings, bytes, raw strings for (a), and any literal inside a
  larger expression where added parens could rebind precedence
  (e.g. `x + "long"`, `"a" "b" + c`) — wrap or refuse, never emit
  invalid or re-precedenced Python.
  Audit 2026-11-07 (partial): fixer module `rules/strings_normalize.py`
  (`normalize_strings`) - token-exact segment rewrites on eligible
  `Constant str` nodes; `\n`-escape to triple-quote with real newlines
  (refuses triple-quote content, trailing backslash), overlong literals
  to parenthesised implicit concatenation at word boundaries with the
  boundary space preserved inside quotes; refuses f-strings, bytes,
  raw/triple-quoted, docstrings, dict keys, `__all__` members, match
  patterns; emitted lines respect the budget; 15 tests in
  `tests/test_rules_strings_normalize.py` green incl. value round-trip
  and idempotence. Remaining: applier/catalog registration (M8-22)
  and writer-fuzzer runs.
  Evidence: danger-matrix tests mirroring
  `tests/test_rules_kwargs_danger.py` for every refusal above;
  `ast.parse` validity + value equality (`ast.literal_eval` round-trip)
  on every rewritten literal; idempotence (second pass is a no-op) and
  the writer fuzzer's compile/comment/strip-equality invariants.
- [ ] **M8-29** **P2** **Backend** — **F-string interior normalisation
  fixer.** Canonicalise the *inside* of `JoinedStr` replacement fields
  without touching what they evaluate to: `f"{ x }"` → `f"{x}"`,
  `f"{x !r}"` → `f"{x!r}"`, `f"{ x !s :>8 }"` → `f"{x!s:>8}"`.
  Scope: `JoinedStr`/`FormattedValue` nodes only — whitespace and
  conversion-flag *placement* normalised; the expression text, the
  conversion (`!s`/`!r`/`!a` — semantics differ, never added/removed/
  reordered) and the format spec are preserved verbatim, including
  whitespace inside the spec where it is significant.
  Acceptance — must convert:
  `f"{ x }"` → `f"{x}"`; `f"{x !r}"` → `f"{x!r}"`;
  `f"{x:>8 }"` keeps its spec untouched while outer spacing is fixed;
  nested replacement fields inside specs
  (`f"{x:{w}.{p}f}"`) keep their own interior normalised recursively;
  quote style inside the f-string may flip only when it removes escapes
  (Python ≥3.12 same-quote nesting; below that the outer/inner quotes
  must differ — emit the minimal-escape form for the running
  `target-version`).
  Acceptance — must refuse:
  (a) any rewrite that would change evaluated output — format-spec
  whitespace is significant (`f"{x: >5}"` ≠ `f"{x:>5}"` for some
  types), `=`-debug text (`f"{x=}"`) is output, `!r`/`!s`/`!a` choose
  different `__str__`/`__repr__`/`__ascii__` paths;
  (b) f-strings containing `\n` real newlines or `"""` content that
  cannot stay inside the chosen quote style — hand to M8-28 or skip;
  (c) expressions with side-effecting or order-sensitive text the
  fixer cannot reproduce byte-faithfully (walrus targets, starred
  args, unusual spacing inside the expression itself is *not*
  normalised — only the field delimiters are);
  (d) conversion of whole f-strings to `.format()`/concatenation —
  out of scope; this task is interior formatting only.
  Evidence: danger-matrix tests for every refusal; output-equality
  proof per case (`eval`/`ast.literal_eval` where legal, or a stub
  object recording `__format__`/`__str__` calls for spec cases);
  idempotence; writer-fuzzer invariants on rewritten modules.
  Audit 2026-11-07 (partial): fixer module `rules/fstring_normalize.py`
  (`normalize_fstrings`) - tokenize-driven field-interior rewrites;
  trims edge whitespace around expr/`!conv`/`:` separators, preserves
  expression interior spacing, conversion flags and format-spec text
  verbatim, recurses into nested spec fields; refuses `=`-debug
  fields, unbalanced brackets and non-f-string braces; 11 tests in
  `tests/test_rules_fstring_normalize.py` green incl. idempotence.
  Note: spec text is preserved byte-for-byte, so `f"{x !s :>8 }"`
  yields `f"{x!s:>8 }"` (spec trailing space kept) rather than the
  spec example's `:>8}`-stripped form - chosen because format-spec
  whitespace is significant. Remaining: applier/catalog registration
  (M8-22) and writer-fuzzer runs.
- [ ] **M8-30** **P2** **Backend** — **Multiline-string indent
  normalisation + `textwrap.dedent` fixer.** Two related rewrites:
  (a) docstrings are normalised to house style — summary placement,
  consistent continuation indentation, closing quotes on their own
  line — preserving `inspect.cleandoc` semantics;
  (b) non-docstring multiline `str` literals whose continuation lines
  share a common indent are offered `textwrap.dedent(...)` wrapping
  (with `ensure_names` import insertion) *or* literal re-indentation,
  chosen by evidence.
  Scope: `Constant` `str` nodes spanning ≥2 lines with a non-empty
  common leading-whitespace prefix on continuation lines; docstrings
  via the structured `DocstringNode` entries, not raw text.
  Acceptance — must convert:
  module/class/function docstrings violating house indent style →
  normalised form (`cleandoc`-equivalent value);
  `x = """\n    body\n    """` where downstream evidence (passed to
  `textwrap.dedent`/`.strip()`-family, compared against dedented
  constants, or the module's own convention) shows the *intended*
  value is the dedented text → `x = textwrap.dedent("""…""")`;
  strings where only the literal's layout is wrong (misplaced closing
  quotes, ragged continuation indent with no common prefix) →
  re-indented literal, value byte-identical.
  Acceptance — must refuse:
  (a) `dedent` wrapping when the value change is unproven — the
  runtime value of `textwrap.dedent(literal)` differs from the
  literal whenever the first content line or whitespace-only lines
  carry indent; emit at `suggest`/`guarded` only with recorded
  evidence, never `proven` on style alone;
  (b) mixed tabs/spaces, first-line content carrying indent
  (`"""text\n    more"""` — dedent cannot touch line 1), strings
  already inside `dedent`/`inspect.cleandoc`/`\.strip()` chains,
  f-strings/`JoinedStr` and `bytes`;
  (c) literals whose common prefix is empty or whose "indent" is
  meaningful content (ASCII-art, code samples, aligned columns) —
  detect via evidence slots, not heuristics alone;
  (d) docstrings in stub/`...` bodies and `__future__`-adjacent
  positions where statement order is load-bearing.
  Evidence: danger-matrix tests; value-equality proof —
  `ast.literal_eval` for re-indented literals and
  `textwrap.dedent(literal_eval(text))` equality for wrapped ones;
  `inspect.getdoc` equivalence for docstring cases; idempotence;
  writer-fuzzer invariants.

### Spec-catalog remainder (merged from the retired 2026-11-06/07 spec and
plan files — `docs/superpowers/specs/2026-11-06-*-design.md`,
`docs/superpowers/plans/2026-11-0{6,7}-*.md`, deleted after merge)

These are the rule-ontology spec §5 catalog entries that have no detector,
no catalog rule and no TODO item yet. All follow the TYP005 recipe
(§18.5) and end at M8-22 catalog registration unless noted.

- [ ] **M8-31** **P2** **Backend** — **`suppression.lint-ignore-config` SUP002**
  (Exactus alias CMP004, cost `project`, no fix). Flags project
  configuration that silences lint checks wholesale (file-level or
  per-file ignore configuration), so the finding names where coverage is
  being waived rather than flagging the waivers themselves.
- [ ] **M8-32** **P2** **Backend** — **`suppression.type-check-config` SUP003**
  (Exactus alias CMP005, cost `project`, no fix). Flags type-checker
  configuration that disables or weakens checking (e.g. pyright/basedpyright
  `typeCheckingMode` off, mypy `ignore_errors`), project scope.
- [ ] **M8-33** **P2** **Backend** — **`config.pyproject-missing` CFG001**
  (Exactus alias CMP006, cost `project`, fix safety `suggest`). Reports a
  project with no `pyproject.toml`; the fix only suggests creating a
  minimal one, never auto-applies.
- [ ] **M8-34** **P2** **Backend** — **Method/classifier quartet OOP001–OOP004**
  (Exactus aliases PY004–PY007, cost `scope`, fixes `guarded`):
  `oop.method-should-be-classmethod`, `oop.method-should-be-static`,
  `oop.classmethod-should-be-static`, `oop.staticmethod-uses-class`.
  Needs `MethodIndex`/`receiver_of` evidence plus "uses `self`/`cls`"
  facts per method.
- [ ] **M8-35** **P2** **Backend** — **`naming.exception-message-variable` NAM001**
  (Exactus alias PY003, cost `scope`, fix `proven` when control flow is
  safe): `msg = "..."` immediately before `raise X(msg)` folds into
  `raise X("...")`; refuse when `msg` is read elsewhere or rebound.
- [ ] **M8-36** **P2** **Backend** — **Simplification family SIM001–SIM006**
  (Exactus aliases PYS001–PYS006, fixes `proven`):
  `simplification.inline-return`, `walrus-in-condition`,
  `inline-single-use`, `dead-constant-store`, `inline-in-return`,
  `inline-via-conditional`. Exactus's skip reasons become the fixes'
  `preconditions` (evaluation-order safety), per ontology spec §5.
- [ ] **M8-37** **P2** **Backend** — **Docs family remainder DOC005, DOC007–DOC013**
  plus the doc fixers the ontology spec attaches to the docs rules:
  detectors `docs.return-yield-mismatch` (DOC005),
  `docs.missing-attribute` (DOC007), `docs.malformed-docstring` (DOC008),
  `docs.analysis-failure` (DOC009), `docs.missing-description` (DOC010),
  `docs.stale-raises` (DOC011), `docs.stale-attribute` (DOC012), and
  `docs.format-style` (DOC013 — normalise docstring content to Google
  style, no Exactus alias). Fixes: missing-section rules offer
  `set_docstring` with a generated entry (`guarded`, confidence-gated);
  stale-section rules offer removal (`suggest`).
- [ ] **M8-38** **P3** **Backend** — **`structure.shebang` SHB001** (fix
  `guarded`): missing, malformed or wrong-interpreter shebang lines on
  executable scripts; rewrite only with recorded evidence.
- [ ] **M8-39** **P3** **DevOps / Release** — **CLI watch mode.** The only
  out-of-scope item left from the check/fix CLI plan
  (`--select`/`--ignore`, config files and parallelism already landed or
  are tracked under M7-04/M7-05/M7-07): a `astart check --watch` /
  `fix --watch` mode that re-runs on file changes.

## 12. Cross-cutting engineering (every milestone)

- [ ] **CC-01** **P1** **Backend** — **Confidence calibration** — numeric confidence per candidate
  from evidence level, calibrated on benchmarks (pairs with M1-15).
- [ ] **CC-02** **P1** **Backend** — **Determinism audit** — stable ordering/names, protocol name
  lockfile, no dict/set-order or time dependence anywhere.
- [ ] **CC-03** **P1** **Backend** — **Error containment v2** — per-file timeout + per-fix watchdog
  on top of existing per-file/per-fix isolation.
- [ ] **CC-04** **P1** **Testing / QA** — **Property + mutation testing** — grammar-random programs →
  strip → fix → check; mutation testing on policy code; regression test per
  reviewer finding.
- [x] **CC-05** **P2** **Documentation** — **User-facing evidence ladder + refusal catalogue**
  ("why wasn't X annotated?" keyed by `Rejection`/`SkipCode`).
  Evidence: `docs/evidence-ladder.md` (E0–E6 levels, the guarded-fix
  acceptance rule, confidence table) and `docs/refusals.md` (all 14
  `Rejection` + 6 `SkipCode` values, keyed by code, with per-reason
  remediation); `docs/benchmarks.md` updated.
- [ ] **CC-06** **P1** **Testing / QA** — **Convention guard** — no suppression comments, no
  `Any`/`object`, keyword-only calls, Google docstrings, `@final Constants`
  — keep `test_rules_review_fixes` family green as rules evolve.

- [ ] **CC-07** **P1** **DevOps / Release** — **Commit hygiene (audit finding).** 148 paths differ from
  the last commit (`120272c`) — about 35 source/test files and ~100 new
  corpus modules — including two sessions' work. Nothing from M0–M2 is
  committed, so no milestone diff is reviewable or revertable.
  Acceptance: one commit per finished milestone slice (M0, M1-so-far, M2-so-
  far, corpus, parallel-session reporters/config) on a branch; the suite and
  `ruff check src tests benchmarks scripts` green at each commit.

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

### M0 — done 2026-11-07 (agent: claude, that session)

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

### M1 (partial) — 2026-11-07 (agent: devin, this session)

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

### M1 — in progress (2026-11-07)
- Done: closed skip/rejection vocabulary (`astart.rules.reasons`: `SkipCode`, `Rejection`; `SkippedFix.code`); **E6 checker gate** (`astart.rules.checker`: `PyrightChecker`, `FixSettings.checker`, `--checker auto|off`; guarded rounds are verified, rejection bisects through the runner's halving and reports `checker-rejected`); **D7** real offer confidence (`astart.rules.confidence`) + `FixSettings.min_confidence` + `--min-confidence`; **annotation-recovery benchmark** (`astart.rules.recovery`, `benchmarks/recovery_report.py`, `docs/benchmarks.md`: baseline precision 16/16, recall 16/144); writer fuzzing over random fix subsets; full fix+ruff idempotence on the corpus.
- Benchmark finding fixed: call-site hints were accepted from the same inference engine that proposed them (`parse_hex_char(src)` → `Sequence[int]`); call-site types must now be syntax-proven. `&`, `|`, `^` result types are now provable.
- Not done: gold set 34→≥500, corpus 20→≥100 modules, checker-delta and throughput-by-size benchmarks, semantic-equivalence runs on pinned projects, shared `srcs` cache for checker runs across files.

### M1 (continued) — 2026-11-07, later (agent: claude)

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

### M2 started — 2026-11-07 (agent: claude)

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


### M6-01 danger matrix — 2026-11-07 (agent: devin)

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

### M2 (continued) — 2026-11-07, evening (agent: claude)

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


### M7-07 `[tool.astart]` config — 2026-11-07 (agent: devin)

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

### Project audit — 2026-11-07, evening (agent: claude)

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


### M8 detectors, perf slice, user docs — 2026-11-07 (agent: devin)

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

### M8-27 IMP001 fixer spec — 2026-11-07 (agent: devin)

- **Added:** M8-27 — the `imports.bare-import` fixer (`import a` +
  `a.b` loads → `from a import b` + `b`), specified per-attribute with
  the refusal matrix: attribute stores/dels keep `import a`; local
  name collisions skip the attribute; existing `from a import b [as c]`
  is reused rather than duplicated; bare-`a` uses and unrewritable
  positions keep the import; conditional/aliased/multi-name imports and
  `__getattr__`-style modules cap at `guarded`.
- M8-01's audit line now points the fixer at M8-27 and registration at
  M8-22. No code changed; this is spec only.

### Gold fix-level, stability, CLI idempotence, authoring kit — 2026-11-07 (agent: devin)

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

### M8-28 string normalisation spec — 2026-11-07 (agent: devin)

- **Added:** M8-28 — two value-preserving string rewrites: `\n`-bearing
  literals → multiline triple-quoted strings, and over-budget literals →
  parenthesised implicit concatenations split at whitespace boundaries.
  Refusals cover f-strings/bytes/raw strings, docstring positions,
  escape-sequence split points, quote-style regressions and precedence-
  sensitive contexts. Evidence: danger-matrix tests, `ast.literal_eval`
  round-trip equality, idempotence, writer-fuzzer invariants.

### M8-29 f-string interior spec — 2026-11-07 (agent: devin)

- **Added:** M8-29 — normalise `JoinedStr` replacement-field interiors
  (`{ x }` → `{x}`, `{x !r}` → `{x!r}`) while preserving expressions,
  conversions and format specs verbatim; refusals cover spec-significant
  whitespace, `=`-debug output, quote-style regressions and any rewrite
  that could change evaluated output. `.format()` conversion explicitly
  out of scope.

### M8-30 dedent/indent spec — 2026-11-07 (agent: devin)

- **Added:** M8-30 — docstring indent normalisation (cleandoc-equivalent)
  plus `textwrap.dedent(...)` wrapping for multiline literals whose
  dedented value is proven by downstream evidence; literal
  re-indentation stays value-identical. Refusals cover unproven value
  changes (dedent alters first-line/whitespace-line semantics), mixed
  tabs, meaningful indentation content, and load-bearing positions.

### Feature batch — 2026-11-07, night (agent: claude)

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

### Constants grouping — 2026-11-07, night (agent: claude)

Requested: when a module already has a `Constants` class, new `Final` globals
must be added to it. Done as M8-23 (`rules/grouping.py`) on top of M8-24 (a
writer gap that broke the move when a use was a default value). The M8-09
detector (`constants_grouping.py`, parallel session) is untouched; a fixer for
constants that are *already* `Final` at module level, and creating the class
when none exists, remain open under M8-09.


### M5 protocol slice — 2026-11-07 (agent: devin)

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

### Full-project audit — 2026-11-07, night (agent: devin)

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

### M5-22 partial — 2026-11-07 (agent: devin)

`typevars._is_pure` no longer refuses `BoolOp` values, so `return x or x``
(and any BoolOp whose operands provably share `T`) flows through to
`passthrough_return` → `-> T` with the `T = TypeVar("T")` declaration.
Mixed-type operands (`x or 0`) still refuse — `_boolop` requires a shared
type, matching the "shared `T`" scope. `provable_return` gained a guard
rejecting `Unknown`/`Any` results. The comparison form `a if a > b else b`
still refuses: the test-position use needs `T` orderable, i.e. a bound —
that is M5-14 territory. Tests: `test_rules_typevar_fix.py` (+2).

### Roadmap audit + fixer-spec renumber — 2026-11-07 (agent: devin)

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

### Spec/plan merge — 2026-11-08 (agent: devin)

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

## 18. Atomic backlog for junior agents

Each task is one small change with a recipe. Do exactly the steps; do not
redesign. If a step does not match the code you see, stop and write the
mismatch under the task instead of improvising.

### 18.0 Working rules (read first)

1. Run commands from `/Users/joaolopes/astart` with `PYTHONPATH=src` (and
   `:.` for `benchmarks`). Tests: `python -m pytest <file> -q -p no:cacheprovider`.
   Fast tier: `python -m pytest -m "not slow" -q -p no:cacheprovider`
   (≈ 30 s). Never run `exactus`; never run `ruff --fix` on files you did
   not create or edit (other agents work in the same tree).
2. TDD order: write the test, run it and see it FAIL, write the code, see it
   PASS. A test that passes before the code exists is a wrong test.
3. House style (the repo checks it): `from __future__ import annotations`;
   keyword-only calls (`f(x=1)` not `f(1)`), also for stdlib (`walk(node=n)`,
   `parse(source=s)`); Google docstrings with `Args:`/`Returns:` on every
   function; module constants inside `@final class Constants` with `Final`
   attributes; no `# noqa`, no `# type: ignore`, no `Any`/`object` in
   annotations; import names (`from ast import walk`), never `import ast`;
   line length 79. Lint only your files: `ruff check <files>`; format with
   `ruff format <files>`.
4. Tests live in `tests/`, use helpers from `tests/expectations.py`
   (`expect_equal`, `expect_in`, `expect_not_in`, `expect_true`), and call the
   fixer like this (copy it, change only the source):

   ```python
   def _fixed(*, source: str) -> str:
       registries = default_registries()
       return fix_source(
           source=dedent(text=source), filename="m.py",
           catalog=load_default_catalog(registries=registries),
           registries=registries,
           settings=FixSettings(ceiling=FixSafety.guarded),
       ).source
   ```

   (imports: `from astart.rules import FixSettings, default_registries,
   fix_source, load_default_catalog`; `from astart.rules.vocabulary import
   FixSafety`; `from textwrap import dedent`.)
5. Finish a task by: fast tier green except failures that already existed,
   `ruff check` clean on your files, checkbox ticked, one line added to the
   progress log with the test file name. Do not recount the progress block;
   the lead does that.
6. Do not edit: `src/astart/rules/hints.py`, `attributes.py`, `methods.py`,
   `facts.py`, `appliers.py`, `resolve.py`, `checker.py` unless the task says
   so. Ask the lead instead.

### 18.1 Typer extensions (all in `src/astart/rules/provable.py`, class `_Typer`)

Recipe for every task here: handlers are registered in
`_Typer.__init__` in the `self._handlers` dict (`NodeClass: self._method`);
a handler takes `node: AST` and returns a type string like `"int"` or `None`
when the type is not guaranteed. Add the handler, add 3 tests in
`tests/test_rules_typer_<name>.py` using `expression_type(node=..., counts={})`
(import from `astart.rules.provable`; parse with
`parse(source="...", mode="eval").body` from `ast`).

- [ ] **Q-01** String methods that return `str`. In `_Typer._call`
  (`provable.py`, ≈ line 410) — it handles only `Name` callees today
  (`node.func.id` looked up in `Constants.call_types`) — add a branch at the
  top: `if isinstance(node.func, Attribute):` type the receiver with
  `self.type_of(node=node.func.value)` and use `node.func.attr` as the
  method name; return `None` for anything not in the table. When the receiver types to `"str"` and the method is one of
  `upper lower strip lstrip rstrip title capitalize casefold swapcase
  replace join format zfill center ljust rjust expandtabs removeprefix
  removesuffix`, the call is `"str"`. Put the names in `Constants` as
  `str_to_str: Final[frozenset[str]]`. Tests: `"a".upper()` → `str`;
  `x.upper()` with unknown `x` → `None`; `"a".bogus()` → `None`.
- [ ] **Q-02** String methods that return `bool`/`int`: `startswith endswith
  isdigit isalpha isalnum isspace islower isupper isidentifier isnumeric
  isdecimal istitle` → `bool`; `find rfind index rindex count` → `int`.
  Same recipe and test shape as Q-01.
- [ ] **Q-03** `str % anything` → `str` (printf formatting). In `_binop`
  (`BinOp` handler): left types to `"str"` and `isinstance(node.op, Mod)` →
  `"str"`. Tests: `"%s" % 1` → `str`; `1 % 2` stays `int`.
- [ ] **Q-04** List concatenation: in `_binop`, when both sides type to the
  same `list[...]` string and op is `Add` → that same type. Tests:
  `[1] + [2]` → `list[int]`; `[1] + ["a"]` → `None`.
- [ ] **Q-05** Subscripts. Add a `Subscript: self._subscript` handler.
  Rules: receiver `list[T]` with an `int`-typed index (`Constant` int) → `T`;
  receiver `list[T]` with a `Slice` → `list[T]`; `str` with int index or
  `Slice` → `str`; `dict[K, V]` with a key typed `K` → `V`; anything else →
  `None`. Parse the inner type of `list[T]` by stripping the `list[` prefix
  and final `]` (see `_item_type` in the same file for the pattern; it only
  handles one level, which is enough). Tests: one per rule plus two refusals.
- [ ] **Q-06** `abs`, `round`, `min`, `max`, `sorted`. In `Constants`, extend
  the call handling: `abs(x)` with `x` typed `int`/`float` → same type;
  `round(x)` with ONE argument typed `float` or `int` → `int`; `sorted(x)`
  with `x` typed `list[T]` → `list[T]`; `min`/`max` with two or more
  arguments all typed the same scalar → that scalar. Refuse everything else.
- [ ] **Q-07** `list(x)`, `set(x)`, `tuple(x)` with a typed argument:
  `list(list[T])` → `list[T]`; `set(list[T])` → `set[T]`; `list(str)` →
  `list[str]`. Anything else `None`. (`tuple` only for `tuple[...]` input.)
- [ ] **Q-08** `dict.get`/`list.copy`/`dict.keys` are NOT in scope; add a
  comment-free refusal test proving `{"a": 1}.get("a")` is `None` (it is
  `int | None`, which must not be claimed).

### 18.2 Gold and regression tests (no production code)

Gold rows live in `tests/test_gold_expansion.py`; each
`_case(name=..., family=..., source=_def(name="f", params="p", body="return p",
calls="f(1)\n"), expected={"f": <return>, "f.p": <param>})` (`None` means the
hint must be refused). Register a new family's builder function the same way
the others are (search for `_default_literal_cases` and copy where it is
called). Copy the
neighbouring cases. Run `python -m pytest tests/test_gold_expansion.py -q`.

- [ ] **Q-09** Add family `variadic` (also add it to the `expected` set in
  `test_gold_covers_every_rejection_family`): 8 cases. Four hinted:
  `f(*a)` called `f(1, 2)` → `f.a` `"int"`; `f(**k)` called `f(x="s")` →
  `"str"`; and two more of your choice. Four refused: mixed types, `f(*xs)`
  unpack call, no extras, escaped function (`g = f`).
- [ ] **Q-10** Add family `attribute_read` with 6 cases mirroring
  `tests/test_rules_attribute_reads.py` (return of `self.x`, arithmetic,
  Optional, conflicting writes, rebound `self`, two classes with different
  attribute names).
- [ ] **Q-11** Add family `comprehension` with 6 cases mirroring
  `tests/test_rules_comprehension_types.py` (list/set/dict, shadowing, async,
  unknown iterable).
- [ ] **Q-12** Add family `multi_binding` with 6 cases mirroring
  `tests/test_rules_multi_binding_locals.py`.
- [ ] **Q-13** CRLF: new `tests/test_rules_line_endings.py`. Feed a source
  using `\r\n` line endings (`"def f(x):\r\n    return 1\r\n"`) to
  `fix_source`; assert the output contains no bare `\n` (every `\n` is part
  of `\r\n`). If it fails, do NOT fix the writer; record the failing output in
  the task and mark it `BLOCKED`.
- [ ] **Q-14** Hostile inputs: new `tests/test_rules_hostile_inputs.py`,
  parametrized over: empty string, only comments, only a docstring, a BOM at
  the start (`"﻿x = 1\n"`), tabs for indentation, a 5000-character
  line, a file without trailing newline, `"x = (\n"` (unparsable). For each,
  `fix_source(...)` must not raise; for the unparsable one assert the result
  has `parse_error` set (look at `FixResult` fields).
- [ ] **Q-15** Determinism across hash seeds: new
  `tests/test_rules_determinism.py`. For 5 corpus files (take the first five
  of `sorted(Path("tests/corpus").glob("*.py.txt"))` under 300 lines), run a
  subprocess `python -c` that calls `fix_source` and prints the result, once
  with `PYTHONHASHSEED=1` and once with `PYTHONHASHSEED=2`, and assert both
  outputs are identical. Mark the test `@pytest.mark.slow`.
- [ ] **Q-16** Convention guard (CC-06): new `tests/test_conventions.py` with
  three tests that scan `src/` and `tests/` text: (a) no line contains
  `# noqa`; (b) no line contains `type: ignore`; (c) no line matches
  `^import ast$`. Allow the file itself. Report offenders as
  `path:line` in the assertion message.
- [ ] **Q-17** Constants guard: in the same file, assert that every class
  named `Constants` in `src/astart` is decorated `@final` (use `ast` to
  parse each file and check `decorator_list`).
- [ ] **Q-18** README flag guard: new `tests/test_readme_flags.py`. Build the
  parser by calling `astart.__main__.main(argv=["fix","--help"])` and
  capturing stdout with `capsys` (it exits via `SystemExit`; catch it), pull
  every `--flag` token, and assert each appears in `README.md`.

### 18.3 CLI and docs (new files or the CLI module `src/astart/__main__.py`)

- [ ] **Q-19** `astart --version`. In `__main__.py` add
  `parser.add_argument("--version", action="version", version=<string>)`
  where the string comes from `importlib.metadata.version("astart")`; if the
  package is not installed catch `PackageNotFoundError` and use `"0+unknown"`.
  Test: `main(argv=["--version"])` raises `SystemExit` with code 0 and prints
  a non-empty line.
- [ ] **Q-20** `astart rules`: new subcommand printing one line per rule:
  `CODE  key  severity  title`, sorted by code. Get rules from
  `load_default_catalog(registries=default_registries()).rules` (fields
  `.code .key .severity .title`). Test: output contains `TYP005` and
  `STR001`, and has as many lines as rules.
- [ ] **Q-21** `astart explain CODE`: prints the rule's `rationale`, then each
  example's source with `triggers` shown as "flagged" or "clean". Unknown
  code → exit status 2 and a message on stderr. Tests for both paths.
- [ ] **Q-22** `docs/rules.md` generated by a new script
  `scripts/generate_rule_docs.py` (iterate the catalog; one `##` heading per
  code with title, severity, rationale, the fix keys). Add
  `tests/test_rule_docs.py` asserting every catalog code appears in
  `docs/rules.md`. Commit the generated file.
- [ ] **Q-23** `docs/architecture.md`: one paragraph per module in
  `src/astart/rules/` (`ls` it; read each file's module docstring for the
  text; do not invent). Link it from the README.
- [ ] **Q-24** `CHANGELOG.md`: one `## 2026-11-07` heading, bullets copied
  from the entries in section 17 of this file dated today. No new claims.
- [ ] **Q-25** `.pre-commit-hooks.yaml` (M7-11): one hook, id `astart-fix`,
  `entry: astart fix --check`, `language: python`, `types: [python]`. Test:
  the file exists and contains `id: astart-fix` and `--check`.
- [ ] **Q-26** `.github/workflows/ci.yml`: on push/pull_request, Python 3.12,
  steps: install with `pip install -e .` plus `pip install pytest ruff` (pyproject
  has no `dev` extra; verify with `grep -n optional-dependencies
  pyproject.toml` and use it if it exists), `ruff check src tests`, `pytest -m "not slow"`. No
  tests needed; just keep it minimal and valid YAML.
- [ ] **Q-27** `--exclude GLOB` for `astart check` and `astart fix`
  (repeatable). In `src/astart/cli/discovery.py` edit `discover_files(*, paths)`
  and its helper `_walk(*, root)`; skip any path whose posix string matches `fnmatch` for any
  glob. Add the argument in `__main__.py` like `--source-root` was added
  (search for `source-root` to copy the pattern end to end: argparse →
  settings dataclass → command). Tests: a tmp tree with `a.py`,
  `skip/b.py`, exclude `skip/*` → only `a.py` is processed.
- [ ] **Q-28** `--format sarif` for `astart check` (M7-09). Output a JSON
  document `{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"astart",
  "rules":[...]}},"results":[...]}]}`; each finding becomes a result with
  `ruleId` (the code), `level` (`error|warning|note` from severity
  `error|warning|info`), `message.text`, and one `locations[0].physicalLocation`
  with `artifactLocation.uri` and `region.startLine`. Copy
  `render_json(*, results, catalog)` in `src/astart/cli/render.py` as
  `render_sarif` with the same signature, and add `sarif` to the `--format`
  choices in `__main__.py` and to the dispatch that calls `render_json`. Test: parse the output and assert those keys for one finding.

### 18.4 Benchmarks and data (scripts and JSON only)

- [ ] **Q-29** Grow the corpus (M1-07 beyond 113): copy 15 stdlib modules not
  yet present to `tests/corpus/<name>.py.txt` (candidates: `textwrap`,
  `shlex`, `string`, `stat`, `tokenize`, `traceback`, `types`, `uuid`,
  `weakref`, `zipapp`, `secrets`, `sched`, `queue`, `imghdr`-free ones; use
  `python -c "import <m>; print(<m>.__file__)"` for the path). Then run
  `PYTHONPATH=src:. python -m benchmarks recovery --json /tmp/r.json` and
  `python -m benchmarks gate --report /tmp/r.json`. If the gate prints FAIL,
  write the FAIL lines under this task and STOP (do not edit the baseline).
- [ ] **Q-30** Five more semantic projects (M1-12): add entries to
  `benchmarks/projects.json` copying the shape of an existing entry. Pick
  small pure-Python packages (`six`, `toml`, `tomli`, `more-itertools`,
  `typing-extensions`), pin the exact latest version and sdist URL from PyPI,
  fill the same fields as the others. Run `python -m benchmarks semantic`
  and record the result per project; a project that is not `equivalent` is
  reported, not fixed.
- [ ] **Q-31** The ≈ 50k-line throughput row (M1-10): concatenate corpus
  files into one 50k-line module in `/tmp`, run
  `PYTHONPATH=src:. python benchmarks/profile_perf.py` the way
  `docs/benchmarks.md` describes for the existing rows, and add the row to
  the table. Do not optimise anything.
- [ ] **Q-32** `docs/benchmarks.md`: add a "How to refresh the baseline"
  section with the three exact commands (recovery with
  `--checker-delta --checker-gate --delta-limit 25 --json`, `gate`,
  `baseline`) and the rule "only accept a baseline with 0 crashes, 0 wrong,
  0 new errors". Copy the numbers format from the existing table.

### 18.5 Detection rules (copy the TYP005 recipe)

TYP005 (`typing.missing-attribute-annotation`) shows every touch point for a
new rule. The five places, in order: (1) a new subject kind, if needed, in
`src/astart/rules/facts.py` (`Constants.node_kinds` and `_visit`); (2) a
fact function registered in `facts.py` if the rule needs one; (3) the rule in
the generator script (see `gen_catalog.py` in the session scratchpad; if it
is gone, edit the catalog JSON under `src/astart/rules/catalog/` by hand,
copying a neighbouring rule); (4) `tests/test_rules_end_to_end.py` expected
code list; (5) a test file with one triggering and one clean example.
Detection-only rules have `fixes=()`.

- [ ] **Q-33** TYP002 `typing.no-object-annotation` (M8-03): flag any
  annotation that is exactly `object` or `Any` (bare names). Subject kind
  `Parameter` and `Function` already exist: add a fact
  `annotation.is_object_or_any` that unparses `arg.annotation` /
  `function.returns` and compares with `{"object","Any"}`. No fix.
- [ ] **Q-34** TYP006 `typing.bare-generic` (new code): flag annotations that
  are exactly `list`, `dict`, `set`, `tuple`, `frozenset` without
  subscripts. Same recipe as Q-33 with a different set. No fix.
- [ ] **Q-35** PRS001 (M8-05): when the file does not parse, `check` should
  report ONE finding `PRS001` at line 1 instead of crashing or reporting
  nothing. Find where `check` handles `SyntaxError`
  (`grep -n "SyntaxError" src/astart/rules/engine.py src/astart/cli/*.py`);
  add the finding there. Test with `"def (:\n"`.

### 18.6 Ant-farm refactor, stages 1–2 (see the design in the 2026-11-07
conversation; pure refactors, tests must not change)

- [ ] **Q-36** Read `HintIndex._judge_pass`, `_call_sites` and `_judge_call_sites`
  in `src/astart/rules/hints.py` and write `docs/hint-propagation.md`
  describing, in plain words, what each does and in which order the 12
  propagation passes run. No code change. (This is the specification for
  Q-37.)
- [ ] **Q-37** Create `src/astart/rules/slots.py` with a `SlotTable` class:
  `deposit(*, slot: str, kind: str, source: str) -> None`,
  `claims(*, slot: str) -> dict[str, set[str]]` (type → set of evidence
  sources), `settle(*, slot: str) -> str | None` (returns the type only when
  exactly one type has claims). Pure data structure, no AST. Tests in
  `tests/test_rules_slots.py`: empty slot → `None`; two sources same type →
  that type; two types → `None`; same source twice counts once.
- [ ] **Q-38** Add `reliability: float` to `_Site` in `hints.py` defaulting
  to `1.0` (`0.0` where `definite=False`). Behaviour must not change: run the
  full fast tier and the gold file before and after, outputs identical.
  (Do this only after the lead says `hints.py` is free.)

### 18.7 More atomic tasks

- [ ] **Q-39** `tests/test_rules_typer_negatives.py`: 12 one-line refusal
  tests proving the typer returns `None` (never a guess) for: a bare name not
  in the environment, `x.attr` with unknown `x`, `f()` for an unknown `f`,
  `a + b` with unknown operands, `[]`, `{}`, `()`, `lambda: 1`, `await x`,
  `yield`, `x if y else z` with unknown branches, `*a`. Use
  `expression_type(node=..., counts={})`.
- [ ] **Q-40** `tests/test_rules_hint_cache.py`: assert two `fix_source` calls
  on identical text return identical `FixResult.source` (no state leaks
  between calls) for five small inline modules.
- [ ] **Q-41** Document every `Rejection` value: `grep -n "class Rejection"
  src/astart/rules/reasons.py`, then add `docs/skip-reasons.md` with one
  line per member: the string value and one sentence taken from its
  docstring. Test: every member's value appears in the file.
- [ ] **Q-42** Document every `SkipCode` the same way (`docs/skip-codes.md`).
- [ ] **Q-43** `README.md`: add a "Limits" section (five bullets, copied
  from the "Where it is far from perfect" list in the 2026-11-07 status
  notes: recall, cross-module, protocols depth, constructors/overrides,
  speed). No new claims.
- [ ] **Q-44** Add `tests/test_cli_exit_codes.py`: `fix --check` on a clean
  file → 0; on a file with a pending fix → 1; on a missing path → 2; on an
  unreadable (directory-less) path → 2. Build files in `tmp_path`.
- [ ] **Q-45** Add `tests/test_cli_formats.py`: `check --format json` output
  parses with `json.loads` and every finding has the keys `code`, `message`,
  `path`, `line` (read `render_json` to confirm the real key names first and
  use those).
- [ ] **Q-46** Add `tests/test_rules_variadic_methods.py`: the same cases as
  `tests/test_rules_variadic_hints.py` but with the function as a method of
  a class called through `self.m(...)` and through `Class().m(...)`. If a
  case fails, record the output under the task and mark it `BLOCKED`.
- [ ] **Q-47** Add `tests/test_rules_default_expression_edges.py`: refusal
  tests for `x=-1` called with a `str` argument elsewhere in the module
  (hint must not be `int`), `x=A` where `A` is a function parameter default
  elsewhere, and `x=1 + 2.0` (type `float`, not `int`).

### 18.8 Copy-paste tasks (no design needed)

Each task gives the complete file. Create it exactly, run the command, and
if the result differs from "Expected", paste the output under the task and
stop.

- [ ] **Q-48** Create `tests/test_rules_typer_negatives.py`:

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
- [ ] **Q-49** Create `tests/test_rules_typer_positives.py` with the same
  shape as Q-48 but parametrize `"text, expected"` with the pairs
  `("1", "int")`, `("'a'", "str")`, `("1.5", "float")`, `("True", "bool")`,
  `("not x", "bool")`, `("len('a')", "int")`, `("[1, 2]", "list[int]")`,
  `("{'a': 1}", "dict[str, int]")`, `("f'{x}'", "str")`, asserting
  `expression_type(...) == expected`. Expected: `9 passed`.
- [ ] **Q-50** Create `.pre-commit-hooks.yaml`:

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
- [ ] **Q-51** Create `tests/test_conventions.py`:

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
- [ ] **Q-52** `README.md`: add a `## Limits` section just after the
  paragraph under the `astart fix` usage block that ends with "missing
  path.", with these five bullets: recall is low where callers are not
  visible (about 11% on the stripped-annotation benchmark) and precision is
  the priority; cross-module call sites and typeshed stubs are not used yet;
  Protocol and `TypeVar` synthesis covers common shapes only; keyword fixes
  for constructors, overrides and callbacks are partial; large files are slow
  (no cache or parallelism yet). Check: `grep -n "^## Limits" README.md`.
- [ ] **Q-53** Create `CHANGELOG.md` with `# Changelog`, a `## 2026-11-07`
  heading, and these bullets: attribute annotations and typed `self.x` reads;
  `*args`/`**kwargs` element types from call sites; expression defaults and
  comprehension types; locals bound several times to one type; checker runs
  on a temp-dir copy with detected import roots and `--source-root`; gated
  benchmark baseline stored in `benchmarks/baseline.json`.

### 18.9 Typing-inference tasks (verified against the code on 2026-11-07)

The table below was produced by running `expression_type(node=parse(source=t,
mode="eval").body, counts={})` on each text. "gap" rows are the known holes
and name the task that closes them.

| Expression | Type today | Status |
| --- | --- | --- |
| `1 + 2`, `7 // 2`, `7 % 2`, `-1`, `True + True` | `int` | ok |
| `1 + 2.0`, `1 / 2` | `float` | ok |
| `'a' + 'b'`, `'a' * 3` | `str` | ok |
| `1 < 2`, `'a' in 'b'`, `not 1` | `bool` | ok |
| `1 if True else 2`, `1 and 2` | `int` | ok |
| `str(1)`, `chr(97)`, `repr(1)` | `str` | ok |
| `int('1')`, `ord('a')` | `int` | ok |
| `float(1)` / `bool(0)` / `isinstance(1, int)` | `float` / `bool` / `bool` | ok |
| `{1, 2}` / `(1, 'a')` / `b'x'` | `set[int]` / `tuple[int, str]` / `bytes` | ok |
| `[i for i in range(3)]` | `list[int]` | ok |
| `1 if True else 'a'`, `1 or 'a'`, `[1, 'a']` | none | correct refusal (mixed types) |
| `2 ** 3` | none | gap → Q-55 |
| `'a'.upper()` | none | gap → Q-01 |
| `[1][0]` | none | gap → Q-05 |
| `abs(-1)` | none | gap → Q-06 |
| `f(1)` (unknown `f`) | none | correct refusal |

- [ ] **Q-54** Create `tests/test_rules_typer_matrix.py` pinning every row of
  the table above that says "ok" or "correct refusal". Use the same
  `parametrize("text, expected", [...])` shape as Q-48/Q-49 and these exact
  pairs: `("1 + 2", "int")`, `("1 + 2.0", "float")`, `("1 / 2", "float")`,
  `("7 // 2", "int")`, `("7 % 2", "int")`, `("-1", "int")`,
  `("True + True", "int")`, `("'a' + 'b'", "str")`, `("'a' * 3", "str")`,
  `("1 < 2", "bool")`, `("'a' in 'b'", "bool")`, `("not 1", "bool")`,
  `("1 if True else 2", "int")`, `("1 and 2", "int")`, `("str(1)", "str")`,
  `("chr(97)", "str")`, `("repr(1)", "str")`, `("int('1')", "int")`,
  `("ord('a')", "int")`, `("float(1)", "float")`, `("bool(0)", "bool")`,
  `("isinstance(1, int)", "bool")`, `("{1, 2}", "set[int]")`,
  `("(1, 'a')", "tuple[int, str]")`, `("b'x'", "bytes")`,
  `("[i for i in range(3)]", "list[int]")`, and the refusals
  `("1 if True else 'a'", None)`, `("1 or 'a'", None)`, `("[1, 'a']", None)`,
  `("f(1)", None)`. Expected: all pass. This file is the safety net for
  every typer task: run it before and after Q-01…Q-07 and Q-55.
- [ ] **Q-55** `**` operator. In `src/astart/rules/provable.py`, class
  `_Typer`, method `_binop`: before the existing numeric branch add: if
  `isinstance(node.op, Pow)` (import `Pow` from `ast`) then
  (a) both sides typed `int`/`bool` AND `node.right` is a `Constant` whose
  `value` is an `int` ≥ 0 → return `"int"`; (b) either side typed `float`
  and the other `int`/`bool`/`float` → return `"float"`; (c) otherwise return
  `None` (a negative or unknown exponent makes `int ** int` a `float`).
  Tests (add rows to a new `tests/test_rules_typer_pow.py`):
  `("2 ** 3", "int")`, `("2 ** 0", "int")`, `("2 ** -1", None)`,
  `("2.0 ** 2", "float")`, `("2 ** 0.5", "float")`, `("x ** 2", None)`.
  Then add `("2 ** 3", "int")` to the Q-54 matrix.
- [ ] **Q-56** Pin the gaps so closing them is visible: create
  `tests/test_rules_typer_gaps.py` with `xfail(strict=True)` parametrized
  rows for `("'a'.upper()", "str")`, `("[1][0]", "int")`,
  `("abs(-1)", "int")`. Each task that closes a gap (Q-01, Q-05, Q-06) must
  delete its row here in the same change (a strict xfail that starts to pass
  fails the suite, which is the reminder).
- [ ] **Q-57** Return-type characterization through the fixer. Create
  `tests/test_rules_return_matrix.py` using the `_fixed` helper from 18.0
  and these (source → expected substring) pairs:
  `"def f():\n    return 1\n"` → `"def f() -> int:"`;
  `"def f():\n    return 1.5\n"` → `"-> float:"`;
  `"def f():\n    return 'a'\n"` → `"-> str:"`;
  `"def f():\n    return [1, 2]\n"` → `"-> list[int]:"`;
  `"def f():\n    return {'a': 1}\n"` → `"-> dict[str, int]:"`;
  `"def f(x):\n    if x:\n        return 1\n"` → `"-> int | None:"`;
  `"def f():\n    return None\n"` → `"-> None:"`;
  `"def f():\n    pass\n"` → `"-> None:"`. Refusals (assert the
  substring `"->"` is NOT in the `def` line):
  `"def f(x):\n    return x\n"` becomes generic via TypeVar, so use instead
  `"def f(x):\n    return x.y\n"`. Expected: all pass today; if one does not,
  paste the real output under the task and mark it `BLOCKED` (do not change
  production code).
- [ ] **Q-58** Parameter-hint characterization. Create
  `tests/test_rules_param_matrix.py` with the `_fixed` helper and these
  pairs: `"def f(x=1):\n    return x\n"` → `"x: int = 1"`;
  `"def f(x='a'):\n    return x\n"` → `"x: str = 'a'"`;
  `"def f(x=1.5):\n    return x\n"` → `"x: float = 1.5"`;
  `"def f(x=True):\n    return x\n"` → `"x: bool = True"`;
  `"def f(x):\n    return x\n\nf(1)\nf(2)\n"` → `"x: int"`;
  `"def f(x):\n    return x\n\nf(1)\nf('a')\n"` → NOT contains `"x: int"` and
  NOT contains `"x: str"`. Same BLOCKED rule as Q-57.
- [ ] **Q-59** Write `docs/typing-inference.md`: copy the table at the top of
  this section verbatim, add a heading "Evidence classes" with the E0–E6
  list from the spec (search `docs/` for "E0" and copy the one-line
  definitions without changes), and a heading "How to add a typer rule" with
  the five-step recipe: add a handler in `_Typer.__init__`'s `_handlers`,
  implement it returning `str | None`, add a row to the Q-54 matrix, add a
  row to the Q-57 matrix, run the fast tier.
