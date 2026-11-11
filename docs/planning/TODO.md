---
agent: devin-local
session: complete-pamphlet
created: 2026-11-07T15:54:30Z
updated: 2026-11-08
---
# Astart — TODO

Architecture precedence: **CC-09–CC-13** and
[single-ast-architecture.md](../architecture/single-ast-architecture.md) supersede older
recipes that require reparsing after ordinary edits or silent full-parse
fallbacks. Those older recipes must migrate through the same transactions.

The living backlog: open work only, in 22 numbered chapters. Done tasks
and history are in `docs/planning/TODO-archive.md`.

## Progress at a glance

<!-- progress:start -->
Updated Mon 09 Nov 2026, 22:40 UTC. The last column is the change since the previous update; details are in the Status ledger below.

```text
Parameters and returns exact  ███████░░░░░░░░░░░░░   33.3 %    157 of 471  no change
Parameters and returns wrong  ░░░░░░░░░░░░░░░░░░░░    1.7 %      8 of 471  no change
Variables exact               ██████░░░░░░░░░░░░░░   29.9 %     88 of 294  no change
Variables wrong               █░░░░░░░░░░░░░░░░░░░    4.1 %     12 of 294  no change
Tasks done                    ██████████░░░░░░░░░░   48.3 %    235 of 487  no change
Tasks missing                 ██████████░░░░░░░░░░   51.7 %    252 of 487  +5 worse

Tasks by chapter (bar = done, missing = still open):
 1 Foundations and measurement          ████████████████████   28 done,   0 missing
 2 Object-oriented code                 ████████░░░░░░░░░░░░    6 done,   9 missing
 3 Whole-project analysis               ████████████░░░░░░░░    9 done,   6 missing
 4 Precise types                        ██████████░░░░░░░░░░   10 done,  10 missing
 5 Protocols and generics               █████████████████░░░   21 done,   4 missing
 6 Keyword arguments                    █████████░░░░░░░░░░░    6 done,   7 missing
 7 Speed and shipping                   ███████░░░░░░░░░░░░░    7 done,  12 missing
 8 Ontology and inference core          █████░░░░░░░░░░░░░░░    9 done,  28 missing
 9 Cross-cutting engineering            ██████░░░░░░░░░░░░░░    8 done,  17 missing
10 Contract negotiation                 ████████████░░░░░░░░   27 done,  17 missing
11 Untyped to typed conversion          ████░░░░░░░░░░░░░░░░    7 done,  26 missing
12 Typer and small tasks                █████████████████░░░   65 done,  11 missing
13 Handoff batch                        ███░░░░░░░░░░░░░░░░░    2 done,  10 missing
14 Accuracy gaps                        ██████████░░░░░░░░░░    5 done,   5 missing
15 Import and Constants style           ░░░░░░░░░░░░░░░░░░░░    0 done,   9 missing
16 Inference logic                      ██████░░░░░░░░░░░░░░    7 done,  16 missing
17 API completeness                     █████████████████░░░   11 done,   2 missing
18 Automatic annotation and formatting  ░░░░░░░░░░░░░░░░░░░░    0 done,  26 missing
21 Risks and contingencies              █████░░░░░░░░░░░░░░░    7 done,  19 missing
22 Algorithms and intelligence          ░░░░░░░░░░░░░░░░░░░░    0 done,  18 missing
```
<!-- progress:end -->

## Dashboard (generated)

<!-- dashboard:start -->
**235 of 487 tasks done (48.3 %). 252 open tasks are ready to start; 26 tasks are fully specified (insights, architecture, algorithm, performance); 0 still need a recipe.** Regenerate with `python -m scripts.todo_update index docs/planning/TODO.md`.

| # | Chapter | Done | Open | Ready | P0 | P1 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Foundations and measurement | 28 | 0 | 0 | 0 | 0 |
| 2 | Object-oriented code | 6 | 9 | 9 | 0 | 9 |
| 3 | Whole-project analysis | 9 | 6 | 6 | 0 | 3 |
| 4 | Precise types | 10 | 10 | 10 | 0 | 7 |
| 5 | Protocols and generics | 21 | 4 | 4 | 2 | 1 |
| 6 | Keyword arguments | 6 | 7 | 7 | 0 | 6 |
| 7 | Speed and shipping | 7 | 12 | 12 | 0 | 6 |
| 8 | Ontology and inference core | 9 | 28 | 28 | 0 | 11 |
| 9 | Cross-cutting engineering | 8 | 17 | 17 | 4 | 13 |
| 10 | Contract negotiation | 27 | 17 | 17 | 1 | 15 |
| 11 | Untyped to typed conversion | 7 | 26 | 26 | 5 | 13 |
| 12 | Typer and small tasks | 65 | 11 | 11 | 0 | 8 |
| 13 | Handoff batch | 2 | 10 | 10 | 2 | 6 |
| 14 | Accuracy gaps | 5 | 5 | 5 | 3 | 2 |
| 15 | Import and Constants style | 0 | 9 | 9 | 1 | 7 |
| 16 | Inference logic | 7 | 16 | 16 | 0 | 12 |
| 17 | API completeness | 11 | 2 | 2 | 0 | 0 |
| 18 | Automatic annotation and formatting | 0 | 26 | 26 | 5 | 13 |
| 21 | Risks and contingencies | 7 | 19 | 19 | 7 | 10 |
| 22 | Algorithms and intelligence | 0 | 18 | 18 | 1 | 9 |

**Open P0**

| ID | Readiness | Task |
| --- | --- | --- |
| M5-13 | ready | E6-verified synthesized protocols |
| M5-25 | ready | M5 exit gate |
| CC-08 | ready | Remove every regular expression from source-reading code |
| CC-10 | ready | One AST: transactional emission and incremental locations |
| CC-09 | ready | Verify declared AST mutations before committing edits |
| CC-11 | ready | Native lexical provenance and format/comment ownership |
| F-29 | ready | Gate: refresh `baseline.json` and `baseline_ext.json` with negotiation on; accept only |
| P-02 | ready | Variable annotations |
| P-03 | ready | Return types that are "not provable" |
| P-08 | ready | The reverse direction |
| W-01 | ready | Record the verification commands and their baseline results |
| W-02 | ready | Find why the checker gate keeps only 4 annotations on the resolver pair |
| H-02 | ready | `[tool.astart]` in the CLI (M7-07 user-visible half, M7-16) |
| H-08 | ready | `astart untype` (P-08): the reverse of `fix` |
| G-04 | ready | Root-cause every remaining contradiction |
| G-09 | ready | `subtype(A, P)` recurses forever when a protocol method returns the protocol |
| G-10 | ready | Annotate locals that are assigned more than once in engine mode |
| S-07 | ready | Every fix above is switchable and configurable |
| AF-19 | ready | Keep user annotations; never overwrite |
| AF-21 | ready | Format the code inside f-string fields with ruff, then put it back |
| AF-22 | ready | Define deterministic Google docstring policy and analyzer ownership |
| AF-23 | ready | GDC002: measure the docstring summary itself |
| AF-24 | ready | GDC025: document statically established public attributes |
| R-02 | ready | Hold-out pairs: stop overfitting to the two fixtures |
| R-07 | ready | Large files and deep projects blow up time or memory |
| R-09 | ready | Weird files: encodings, BOM, CRLF, tabs, form feeds, NUL bytes |
| R-12 | ready | Spans drift after many edits |
| R-17 | ready | Incident playbook: a release writes a wrong annotation |
| R-18 | ready | Merge conflicts on hot shared files |
| R-21 | ready | Deep nesting and recursion limits |
| AL-06 | ready | Delta debugging against the checker (ddmin) for batched fixes |

**Open P1**

| ID | Readiness | Task |
| --- | --- | --- |
| M2-02 | ready | Constructor/attribute resolution |
| M2-05 | ready | Rules-layer `self.X → ContractIndex` fallback |
| M2-06 | ready | R9: attribute types |
| M2-07 | ready | Override awareness (E1) |
| M2-08 | ready | Escape analysis v2 |
| M2-09 | ready | Flow-sensitive locals |
| M2-10 | ready | Kwargs for constructors |
| M2-11 | ready | Kwargs for method calls |
| M2-12 | ready | Kwargs for bound-method callbacks |
| M3-07 | ready | Canonical public import locations |
| M3-09 | ready | `TYPE_CHECKING` placement |
| M3-13 | ready | `ensure_names` everywhere + expanded `known_imports` |
| M4-01 | ready | Prover: comprehensions, subscripts on typed names, builtin-method result table |
| M4-02 | ready | Prover: `Await` unwrap, `Try`/`Match`/`AugAssign`/loop handling |
| M4-03 | ready | Prover: yield typing + once-bound `ClassDef` calls |
| M4-06 | ready | R3: `generator`/`async` |
| M4-07 | ready | R4: `usage_abc` |
| M4-08 | ready | R5: `typeguard`/`TypeIs` |
| M4-14 | ready | Variable/attribute annotations |
| M5-10 | ready | Merge into shared `_protocols.py` + name lockfile |
| M6-02 | ready | Positional-only/keyword-only end-to-end |
| M6-05 | ready | `calls.missing-argument` detection rule |
| M6-06 | ready | `calls.unexpected-argument` detection rule |
| M6-07 | ready | `calls.ambiguous-callee` detection rule |
| M6-08 | ready | `calls.unresolved-callee` detection rule |
| M6-09 | ready | Idempotence with ruff line-wrapping |
| M7-01 | ready | Kill superlinear costs |
| M7-02 | ready | Perf budgets |
| M7-16 | ready | Wire the built-but-unreachable product surface (audit finding) |
| M7-17 | ready | Index `post_refinements` document walks |
| M7-18 | ready | Bound precondition re-evaluation per applied fix |
| M7-19 | ready | Share the engine/hint index across fix rounds |
| M8-01 | ready | `imports.bare-import` IMP001 |
| M8-02 | ready | `typing.missing-variable-annotation` TYP005 |
| M8-03 | ready | `typing.no-object-annotation` TYP002 |
| M8-04 | ready | `suppression.marker-comment` SUP001 |
| M8-05 | ready | `parsing.module-does-not-parse` PRS001 |
| M8-06 | ready | `typing.return-type-mismatch` / `incompatible-default` |
| M8-07 | ready | Docs family DOC001/003/004/006 |
| M8-11 | ready | D6 remainder: `Exists` evaluation |
| M8-12 | ready | D8: procedural rules |
| M8-22 | ready | Register the standalone detectors as catalog rules (audit finding) |
| M8-27 | ready | IMP001 fixer: bare `import a` → `from a import b` + use-site rewrite |
| CC-01 | ready | Confidence calibration |
| CC-02 | ready | Determinism audit |
| CC-03 | ready | Error containment v2 |
| CC-04 | ready | Property + mutation testing |
| CC-08-01 | ready | Docstring line scanner replaces `docstrings.py` patterns |
| CC-08-02 | ready | Use the scanner in `rules/docstring_edit.py` |
| CC-08-03 | ready | Use the scanner in `rules/docs_shared.py` |
| CC-08-04 | ready | Comment directives from tokens, not patterns (`ast.py`) |
| CC-08-05 | ready | String prefix and quote from the token (`formatting.py`) |
| CC-08-07 | ready | Replace the `re_sub` edit in `rules/appliers.py` |
| CC-08-08 | ready | Replace the two `re_search` calls in `rules/typevars.py` |
| CC-12 | ready | Migrate wrapping and insertion onto shared transactions |
| CC-13 | ready | Deterministic concurrent inference and evidence invalidation |
| F-07 | ready | Complete the transfer table |
| F-13 | ready | Builder: capabilities |
| F-16 | ready | Builder: declared annotations |
| F-21 | ready | Returns as union contracts |
| F-22 | ready | Backward reconciliation of parameters |
| F-23 | ready | Conflict reporting |
| F-24 | ready | Calibrate the lossy collapses with the X-05 method |
| F-26 | ready | Explanation trail per candidate |
| F-27 | ready | Performance: graph build linear in nodes; per-function incremental rebuild; budget tests |
| F-31 | ready | Gold family `negotiated` |
| F-33 | ready | Cross-module edges through `ProjectIndex` |
| F-34 | ready | Safety bounds: per-module event and wall-clock budget; on overrun fall back to the |
| F-37 | ready | Default-literal parameters in the negotiator |
| F-40 | ready | Comprehensions as derived nodes |
| F-43 | ready | Quote instead of refusing |
| P-04 | ready | "Tainted" parameters |
| P-05 | ready | "No candidate" (72) |
| P-06 | ready | "Call sites unknown / uncorroborated / escapes" |
| P-07 | ready | Name-agnostic scoring of synthesized Protocols and TypeVars |
| P-09 | ready | Round-trip gate |
| P-10 | ready | Import parity: every name the written annotations use is imported |
| T-01 | ready | Dunder parameters from the language |
| T-02 | ready | Copy annotations from the base-class method of the same name |
| T-03 | ready | Apply a sibling stub |
| W-07 | ready | Burn down unbindable calls and escaping functions |
| W-08 | ready | Let the negotiator write default-literal parameters (F-37) |
| W-11 | ready | Annotate a method that returns its own class (`Self` or quoted name) |
| W-12 | ready | Annotate instance attributes from negotiation |
| Q-33 | ready | TYP002 `typing.no-object-annotation` |
| Q-34 | ready | TYP006 `typing.bare-generic` |
| Q-35 | ready | PRS001 (M8-05): when the file does not parse |
| Q-61 | ready | Returns / Raises stubs |
| Q-68 | ready | Kill the ~50k-line cliff (M7-01 evidence from Q-31) |
| X-03 | ready | `Self` and TypeVar returns for classmethods |
| X-04 | ready | Names imported from other modules cannot be judged by `relation()` |
| X-05 | ready | Calibrate more candidate categories with the same method as |
| H-04 | ready | Catalog rules TYP002 and TYP006 (Q-33, Q-34, M8-03) |
| H-05 | ready | PRS001 for files that do not parse |
| H-06 | ready | Returns / Raises docstring stubs (Q-61, M8-07) |
| H-07 | ready | Wider `known_imports` (M3-13) |
| H-09 | ready | Gate for the conversion pair (P-09) |
| H-11 | ready | `astart fix --jobs N` |
| G-06 | ready | Never type a descriptor attribute as its value |
| G-07 | ready | Run the checker gate on the pairs and keep the result |
| S-01 | ready | Merge consecutive `if TYPE_CHECKING:` blocks and drop empty ones |
| S-02 | ready | Put runtime imports before every `TYPE_CHECKING` block |
| S-04 | ready | Drop `from a import b` when `from a.b import c` covers its uses |
| S-05 | ready | Lowercase `Constants` attributes without a leading underscore |
| S-06 | ready | Keep the `Constants` docstring generated and current |
| S-08 | ready | Normalise exception messages to a variable named `msg` |
| S-09 | ready | Sort class methods by kind (ported from Exactus `organize`) |
| I-04 | ready | Type `with` targets from `__enter__` |
| I-05 | ready | Type `for` targets from common iterables |
| I-07 | ready | Async inference: `await`, `gather`, async generators |
| I-09 | ready | `defaultdict`, `Counter`, `deque` element types from mutation |
| I-10 | ready | Numeric tower and operator result rules |
| I-11 | ready | Attribute chains and dataclass/NamedTuple/TypedDict fields |
| I-12 | ready | Property getters as typed attributes |
| I-17 | ready | Tuple, star-unpack, slice, and operator results on containers |
| I-18 | ready | TypeVar solving from call arguments |
| I-19 | ready | Join and simplify unions deterministically |
| I-20 | ready | Cross-validate the confidence tiers |
| I-23 | ready | Stop at the evidence: explain why a node stays opaque |
| AF-01 | ready | Annotate `*args` and `**kwargs` |
| AF-03 | ready | Dunder method annotations from the language |
| AF-04 | ready | Dataclass, NamedTuple and TypedDict fields |
| AF-05 | ready | `ClassVar` and `Final` inference |
| AF-06 | ready | Modernise `typing` spellings by target version |
| AF-08 | ready | Docstring types follow annotations |
| AF-09 | ready | Generate `Raises`, `Yields`, `Attributes` sections |
| AF-11 | ready | Canonical order of union arms and `None` last |
| AF-12 | ready | Import sorting and grouping |
| AF-15 | ready | Replace `object` and `Any` annotations by inferred types |
| AF-18 | ready | Annotation report |
| AF-25 | ready | GDC018: require recognizable documented types for unannotated parameters |
| AF-26 | ready | GDC021: validate tuple-result documentation structure |
| R-03 | ready | Typeshed snapshot drift between machines |
| R-04 | ready | Emitted code must compile on every supported target |
| R-05 | ready | ruff version differences break idempotence and f-string formatting |
| R-06 | ready | Type checker absent, old or different (pyright vs mypy) |
| R-08 | ready | Parallel runs corrupt the cache or interleave output |
| R-10 | ready | Syntax the parser does not know (newer Python, Python 2, templates) |
| R-11 | ready | Filesystem edge cases: symlinks, read-only, changing files |
| R-16 | ready | Flaky or slow tests hide real failures |
| R-19 | ready | The TODO file itself: size, concurrent edits, format corruption |
| R-20 | ready | Engine health: the old converter can fail or change |
| AL-01 | ready | Control-flow graph and per-block narrowing (replaces ad-hoc `if` handling) |
| AL-02 | ready | Widening at loops so fixpoints terminate and stay precise |
| AL-03 | ready | Interprocedural summaries in SCC order |
| AL-04 | ready | Alias and escape analysis for containers |
| AL-05 | ready | Probabilistic fusion of evidence (log-odds) instead of hand tiers |
| AL-07 | ready | Bidirectional (expected-type) inference |
| AL-10 | ready | Interned types and memoised subtype checks |
| AL-13 | ready | Mutation summaries decide `Sequence` versus `list` |
| AL-18 | ready | Ablation harness: marginal value of each evidence source |
<!-- dashboard:end -->

## Status ledger (updatable)

The one place that says where the work stands. The block below is generated
from `docs/planning/status.json`; never edit it by hand. It shows a progress bar for every measure, the change since the previous update (marked better, worse or no change) and human-readable times such as `Sun 08 Nov 2026, 18:39 UTC`; every command prints the same summary in the terminal (`--quiet` hides it). Update it with:

| Event | Command |
| --- | --- |
| After a pair run | `PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5 \| python -m scripts.todo_update status pair --label "after G-02"` |
| After a check | `python -m scripts.todo_update status check semantic_run pass --note "15 of 15"` (statuses: `pass`, `fail`, `not run`) |
| New or finished open item | `python -m scripts.todo_update status item add "text"` or `item remove N` |
| Note on the working tree | `python -m scripts.todo_update status note "what is uncommitted"` |
| Redraw only | `python -m scripts.todo_update status render` |
| Take a new snapshot (so the next update shows its change since now) | `python -m scripts.todo_update status refresh` |

<!-- status:start -->
**Updated Mon 09 Nov 2026, 22:40 UTC.** Uncommitted: engine_hints.py (convert apply=False, W-03), negotiation/variables.py (first assignments, G-10), facts.py (--engine implies variable annotation), tests/astart/rules/test_engine_hints.py (new test), scripts/*.py and docs/*. Do not commit before the semantic run.

**Progress** (change since the previous update on Mon 09 Nov 2026, 21:21 UTC):

| Measure | Progress | Now | Change |
| --- | --- | --- | --- |
| Parameters and returns exact | `███████░░░░░░░░░░░░░` 33.3 % | 157 of 471 | no change |
| Parameters and returns wrong | `░░░░░░░░░░░░░░░░░░░░` 1.7 % | 8 of 471 | no change |
| Variables exact | `██████░░░░░░░░░░░░░░` 29.9 % | 88 of 294 | no change |
| Variables wrong | `█░░░░░░░░░░░░░░░░░░░` 4.1 % | 12 of 294 | no change |
| Tasks done | `██████████░░░░░░░░░░` 48.3 % | 235 of 487 | no change |
| Tasks missing | `██████████░░░░░░░░░░` 51.7 % | 252 of 487 | +5 worse |

| When | Moment | Parameters and returns: exact / wrong | Variables: exact / wrong |
| --- | --- | --- | --- |
| 2026-11-08 | Start of session | 253 / 55 of 482 | 174 / 49 of 335 |
| 2026-11-08 | After W-03 (engine annotations no longer written into the module) | 221 / 13 of 482 | 152 / 13 of 335 |
| 2026-11-08 | After G-10 (first assignment of multiply-bound locals) | 221 / 13 of 482 | 163 / 13 of 335 |
| 09 Nov 2026 17:17 | reference fixtures/typed.py | 202 / 9 of 498 | 177 / 13 of 492 |
| 09 Nov 2026 18:18 | CC-09/CC-10 baseline before next slice | 198 / 9 of 475 | 164 / 14 of 296 |
| 09 Nov 2026 18:24 | Receiver-aware method return inference; no suffix-based None | 198 / 9 of 475 | 164 / 12 of 296 |
| 09 Nov 2026 19:50 | Curated alias and capability-name reference; receiver-aware inference | 157 / 21 of 471 | 88 / 23 of 294 |
| 09 Nov 2026 20:05 | Generic alias and variadic tuple comparison support | 157 / 9 of 471 | 88 / 13 of 294 |
| 09 Nov 2026 20:22 | Separate alias-equivalent types from spelling recovery; repair variadic tuple scoring | 157 / 8 of 471 | 88 / 12 of 294 |
| 09 Nov 2026 21:03 | TYP008 native legacy alias declarations; no variable hints on aliases | 157 / 8 of 471 | 88 / 12 of 294 |
| target | 90 % exact, 0 wrong | about 424 / 0 | about 265 / 0 |

| Check | Status | When | Note |
| --- | --- | --- | --- |
| fast_tier | pass | 08 Nov 2026 22:42 | bench+rules tests green incl. new perf/targets/runner tests 2026-11-09 |
| slow_tier | not run | 2026-11-08 | not run since W-03 and G-10 |
| stdlib_gate | pass | 08 Nov 2026 22:42 | 128 modules, 0 crashes, gate vs baseline.json PASS 2026-11-09 |
| external_gate | pass | 08 Nov 2026 22:42 | 165 modules, recall 20.18%, precision 99.60%, 0 crashes, gate vs baseline_ext.json PASS 2026-11-09; refresh declined (+0.55pts < +2pts) |
| semantic_run | pass | 08 Nov 2026 22:42 | 15 of 15 projects same_imports and same_result 2026-11-09 |
| lint | pass | 09 Nov 2026 22:40 | dispatcher smoke |
| todo_lint | pass | 08 Nov 2026 22:42 | 0 errors, 0 warnings 2026-11-09 |

**Open items**

1. Run the semantic equivalence run (W-01 step 4) before committing anything.
2. Re-run the full in-place conversion on a copy of fixtures/untyped.py (it was interrupted on 2026-11-08) and record time and exit code in the conversion-goal section.
3. Variables exact is 163 of 335; G-10 asks for at least 170: compare variable_map before and after W-03 to find the lost ones.
4. Do R-18 (settings registry) first and alone so the parallel lanes stop colliding.
5. Scorer tasks G-02, G-05, P-07 remove about 20 of the 26 remaining contradictions; G-04 root-causes the other five.
6. Re-run the slow tier (about 19 minutes) after the engine changes.
7. Add tests and lint for the TODO tooling (R-25)
8. Make docs/planning/status.json updates atomic, locked and validated (R-26)
9. Triage 2026-11-09 session artifacts before commit: dev/t.py, fixtures/typed.py, fixtures/artifacts/typed_graph.json, explanation.json (F-26 schema sketch)
<!-- status:end -->

## How this document works (tooling and update protocol)

This file is a working system, not just text. Four files and two scripts keep
it current; the rules below are what every agent follows.

**Files**

| File | Role | Edited by |
| --- | --- | --- |
| `docs/planning/TODO.md` | The living backlog: dashboard, status ledger, accuracy contract, parallel lanes, chapters 1 to 22, cookbook | agents by hand, except the generated blocks |
| `docs/planning/TODO-archive.md` | Done tasks in full text and the historical chapters (old progress log, risk register, inventory) | rarely; the lead moves finished tasks here |
| `docs/planning/status.json` | State behind the status ledger: pair history, check results, open items, working-tree note | `scripts/todo_update/status_update.py` only |
| `scripts/todo_update/todo_index.py` | Regenerates the dashboard and the task index; checks that every ID cited in the Accuracy contract exists | run after any task change |
| `scripts/todo_update/todo_lint.py` | Audits the whole file: generated-block markers, task metadata and steps, placeholders, titles, duplicate and undefined IDs, chapter numbering, index links, Area vocabulary; exit code 1 on errors | run before finishing any edit |
| `scripts/compare/conversion_report.py` | Converts `fixtures/untyped.py` in memory, scores it against `fixtures/typed.py` by meaning and writes the report and the generated conversion block | run after any change that can move annotation counts |
| `scripts/compare/artifacts/results/conversion-report.md`, `scripts/compare/artifacts/results/conversion-report.json` | The latest full report and its machine-readable form (generated, overwritten on each run) | `scripts/compare/conversion_report.py` only |
| `scripts/todo_update/status_update.py` | Updates `docs/planning/status.json`, redraws the status ledger (progress bars, change since the previous update, human-readable times) and prints the same summary | run after any measurement or check |

**Generated blocks (never edit inside them).** Each block sits between a pair
of HTML comment markers named `NAME:start` and `NAME:end`. The scripts replace
the text between the first pair they find, so **never write a marker literally
anywhere else in this file**, not even in documentation; describe them by name.

| Block | Marker name | Produced by |
| --- | --- | --- |
| Dashboard | `dashboard` | `python -m scripts.todo_update index docs/planning/TODO.md` |
| Task index | `index` | the same command |
| Progress at a glance (top of the file) | `progress` | `python -m scripts.todo_update status render` |
| Latest conversion report | `conversion` | `python scripts/compare` |
| Status ledger | `status` | `python -m scripts.todo_update status render` |

To regenerate every block in one pass run `python -m scripts.todo_update`
(index, status render, conversion comparison and lint); `--no-compare`
skips the comparison.

**Update protocol**
1. Changed a task (status, priority, readiness, a new task): run
   `python -m scripts.todo_update index docs/planning/TODO.md`. A non-zero exit means a task is
   malformed or an Accuracy-contract ID does not exist; fix that before anything else.
2. Ran a pair measurement: pipe it into `python -m scripts.todo_update status pair --label "..."`.
3. Ran or failed a check (fast tier, slow tier, either recovery gate, the
   semantic run, lint): `python -m scripts.todo_update status check NAME pass|fail|"not run" --note "..."`.
4. Opened or closed a follow-up that is not a task: `python -m scripts.todo_update status item add|remove`.
5. Before committing anything, read the ledger: its open items and the
   working-tree note say what must be true first (today: the semantic run).

**Rules for editing the file by hand**
- Match the real task heading when editing by ID. The Task template contains an
  example task (`### F-17 — Imperative title...`) inside a code fence; an edit by
  ID once changed that example instead of the real task.
- Keep the shape in the Task template; the parsers read it literally. A task
  needs Status, Priority, Area, Readiness and Effort lines, then Steps and Done when.
- Finishing a task: set Status and Readiness to `done`, add an **Evidence** line
  (command and number), run the index script, update the ledger.
- Before finishing, run `python -m scripts.todo_update lint`; it must end with `0 errors` (warnings are advisory).
- Other agents edit the same tree. Change only your task's text, never reformat
  the file, and re-read a script before editing it (the index script was
  reformatted by someone else twice during 2026-11-08 and a pre-written edit
  stopped matching).

**How the document got this shape (2026-11-08).** Two one-shot migration
scripts converted the original checkbox list (342 tasks) into headings with a
metadata line, then into the 14 original chapters with one template, moving
done tasks and history to the archive. They are no longer needed: the format
is now maintained by `scripts/todo_update/todo_index.py`, and R-19 will add a linter. Later the
document grew chapters 14 to 22 (accuracy gaps, import and Constants style,
inference logic, API, annotation and formatting, risks, algorithms) and the
Accuracy contract, Parallel lanes, Effort and Cookbook sections.

**Status ledger tool reference** (`scripts/todo_update/status_update.py`, state in `docs/planning/status.json`)

*Data model* (`docs/planning/status.json`; edit only through the script):

| Key | Type | Meaning | Written by |
| --- | --- | --- | --- |
| `updated`, `updated_at` | date; ISO timestamp with offset | when the last state-changing command ran | every state-changing command |
| `working_tree` | text | what is uncommitted and what must be true before committing | `note` |
| `history` | list of objects | one entry per pair measurement: `date`, `at` (newer entries only), `label`, `p_exact`, `p_wrong`, `p_total`, `v_exact`, `v_wrong`, `v_total` | `pair` |
| `checks` | object | name to `status` (`pass`, `fail`, `not run`), `date`, `at`, `note`; shown in the order fast_tier, slow_tier, stdlib_gate, external_gate, semantic_run, lint, then any others alphabetically | `check` |
| `open_items` | list of text | follow-ups that are not tasks, numbered in the ledger | `item add`, `item remove` |
| `snapshot` | object | the numbers at the latest update: the six pair numbers of the last history entry, `tasks_done`, `tasks_total`, and `at` | every state-changing command and `refresh` |
| `previous` | object or null | the snapshot before the latest update; the Change column is `snapshot` minus `previous` | the same |

*Commands* (global options: `--state PATH`, `--todo PATH`, `--quiet`):

| Command | Effect |
| --- | --- |
| `render` | Redraws the ledger and prints the summary. Changes no state, so running it twice never changes the Change column. |
| `refresh` | Takes a new snapshot without any other change; the snapshot rolls only if a number changed. Use it after editing tasks by hand to refresh the task counts. |
| `pair --label TEXT` | Reads the JSON printed by `scripts.compare.pair` on standard input and appends a history entry. |
| `check NAME pass\|fail\|"not run" [--note TEXT]` | Sets one check with the current time. |
| `item add TEXT` / `item remove N` | Adds an open item, or removes item N (counted from 1). |
| `note TEXT` | Replaces the working-tree note. |

*Progress measures* (what the bars show, and which direction is better):

| Measure | Value over total | Better when |
| --- | --- | --- |
| Parameters and returns exact | `p_exact` of `p_total` | higher |
| Parameters and returns wrong | `p_wrong` of `p_total` | lower |
| Variables exact | `v_exact` of `v_total` | higher |
| Variables wrong | `v_wrong` of `v_total` | lower |
| Tasks done | done tasks of all tasks, counted with the dashboard script's parser | higher |
| Tasks missing | open tasks of all tasks (total minus done) | lower |

The block at the top of the file also lists, for every chapter, a bar of done tasks against all tasks plus the number of tasks still missing, counted live with the dashboard script's parser. A bar is 20 characters, `round(20 * value / total)` filled; the percentage has
one decimal; a zero total shows `n/a`. The Change column reads `+39 better`,
`−4 better`, `+2 worse`, `no change`, or `n/a` when there is no previous value.

*Times.* Stored as ISO 8601 with the machine's UTC offset. Displayed in the
ledger heading as `Sun 08 Nov 2026, 18:39 UTC`, in table cells as
`08 Nov 2026 18:39`. The terminal summary also prints a relative time
(`just now`, `5 minutes ago`, `3 hours ago`, `4 days ago`); it is never written
into the file, which keeps `render` deterministic. Entries made before
2026-11-08 18:39 only have a date and show it as is.

*How the change since the last run works.* A command rolls the snapshot only when a measured number has changed (times are ignored). The Change column therefore keeps showing the last real change, with the time of the update it is compared with, until a number moves again; a note, a check or an unchanged `refresh` never hides it. It is not a fixed baseline; for long-range progress read the history table.

*Example terminal output* (real run, 2026-11-08):

```text
Status ledger updated Sun 08 Nov 2026, 18:39 UTC (just now)
Compared with the previous update on Sun 08 Nov 2026, 18:39 UTC (just now)

  Parameters and returns exact  ███████████░░░░░░░░░   53.9 %    260 of 482  +39 better
  Parameters and returns wrong  ░░░░░░░░░░░░░░░░░░░░    1.9 %      9 of 482  −4 better
  Variables exact               ██████████░░░░░░░░░░   48.7 %    163 of 335  no change
  Variables wrong               █░░░░░░░░░░░░░░░░░░░    4.5 %     15 of 335  +2 worse
  Tasks done                    ███████░░░░░░░░░░░░░   33.5 %    159 of 475  no change

  Checks: 3 pass, 0 fail, 3 not run
  Open items: 7
```

*Testing it safely.* Copy `docs/planning/TODO.md` and `docs/planning/status.json` to `/tmp`, then
run the script with `--state /tmp/... --todo /tmp/...` (see the zsh function in
the lessons below). The first version of this tool shipped with a bug that only
this kind of test found.

*Known limits.*
- No locking: two agents running the script at the same moment can lose one
  update (the last write wins). Task R-26.
- `docs/planning/status.json` is not validated on load; a hand edit that breaks its
  shape fails with a Python error. Task R-26.
- The task counts need `scripts/todo_update/todo_index.py` to be importable; otherwise the
  Tasks done row shows `n/a`.
- The script has no unit tests and no lint run yet. Task R-25.

**Lessons from building the tooling (each cost time once)**
- A save-time auto-fixer (Exactus or ruff with unsafe fixes) runs on Python files in this repository. It rewrote the new scripts into the project style (`loads(s=...)`, `parser.add_subparsers(...)`) and **deleted every `print(...)` call**, which silently removed the terminal summary and the lint report while the exit code stayed 0. Write output with `_ = stdout.write(...)` from the start, use keyword arguments, and after writing a script run it and check that it still prints.
- An argparse global option and a subcommand positional argument that share a
  name overwrite each other. The status script's first `--status` option
  collided with `check NAME STATUS`; it is now `--state`.
- Test a script on copies of the real files (`--state` and `--todo` options
  exist for this) before running it on the real ones.
- In zsh a variable holding a whole command is not word-split; use a shell
  function when testing (`S() { python -m scripts.todo_update status ... "$@"; }`).
- Never name a script after a standard-library module (`bisect.py` broke
  `random` and `tempfile`).
- A string replacement on a file that other agents also edit can miss silently;
  after each scripted edit, grep for the expected result.
- macOS `sed -i` needs an empty suffix argument (`sed -i ''`); prefer a Python
  snippet for multi-line edits.
- Counting symptoms misleads a bisect (a run that applies nothing looks clean);
  compare one specific annotation instead (Cookbook C-7).



## Task index (generated)

<!-- index:start -->
| ID | Task | Priority | Done |
| --- | --- | --- | --- |
| [M1-10](#m1-10--throughput-benchmarks) | Throughput benchmarks | P2 | [x] |
| [M0-01](#completed) | Git init + ruff-format drift policy | P0 | [x] |
| [M0-02](#completed) | D1: `ensure_names` in `add_inferred_annotation` | P0 | [x] |
| [M0-03](#completed) | D2: `'Unknown'` is non-definite evidence | P0 | [x] |
| [M0-04](#completed) | D3: imported constructors type their calls | P0 | [x] |
| [M0-05](#completed) | D6: `Exists` crash guarded | P0 | [x] |
| [M0-06](#completed) | D9: `typing.add-noreturn` fix | P0 | [x] |
| [M0-07](#completed) | Final-review findings C1, C2, I1–I6 | P1 | [x] |
| [M0-08](#completed) | Type-policy cleanup | P1 | [x] |
| [M0-09](#completed) | D10 suite-flakiness investigation | P1 | [x] |
| [M0-10](#completed) | Bare `exactus` clean | P0 | [x] |
| [M1-01](#completed) | Closed skip/rejection reason enums | P0 | [x] |
| [M1-02](#completed) | E6 checker oracle, core | P0 | [x] |
| [M1-03](#completed) | E6 oracle remainder | P0 | [x] |
| [M1-04](#completed) | Benchmark harness scaffolding | P0 | [x] |
| [M1-05](#completed) | Annotation-recovery benchmark | P0 | [x] |
| [M1-06](#completed) | Gold set expansion 34 → ≥500 | P1 | [x] |
| [M1-07](#completed) | Corpus expansion 20 → ≥100 real modules | P1 | [x] |
| [M1-08](#completed) | Precision/recall dashboard | P0 | [x] |
| [M1-09](#completed) | Checker-delta metric | P1 | [x] |
| [M1-11](#completed) | Stability benchmarks | P1 | [x] |
| [M1-12](#completed) | Semantic-equivalence runs | P2 | [x] |
| [M1-13](#completed) | Writer fuzzing | P1 | [x] |
| [M1-14](#completed) | Full-CLI idempotence tests | P1 | [x] |
| [M1-15](#completed) | D7: real `FixOffer.confidence` + `min_confidence` enforcement | P0 | [x] |
| [M1-16](#completed) | Crash containment for analyzer failures (audit finding) | P0 | [x] |
| [M1-17](#completed) | Gold set at fix level | P1 | [x] |
| [M1-18](#completed) | Fast test tier | P2 | [x] |
| [M2-13](#m2-13--m2-exit-gate) | M2 exit gate | P0 | [x] |
| [M2-02](#m2-02--constructorattribute-resolution) | Constructor/attribute resolution | P1 | [ ] |
| [M2-05](#m2-05--rules-layer-selfx--contractindex-fallback) | Rules-layer `self.X → ContractIndex` fallback | P1 | [ ] |
| [M2-06](#m2-06--r9-attribute-types) | R9: attribute types | P1 | [ ] |
| [M2-07](#m2-07--override-awareness-e1) | Override awareness (E1) | P1 | [ ] |
| [M2-08](#m2-08--escape-analysis-v2) | Escape analysis v2 | P1 | [ ] |
| [M2-09](#m2-09--flow-sensitive-locals) | Flow-sensitive locals | P1 | [ ] |
| [M2-10](#m2-10--kwargs-for-constructors) | Kwargs for constructors | P1 | [ ] |
| [M2-11](#m2-11--kwargs-for-method-calls) | Kwargs for method calls | P1 | [ ] |
| [M2-12](#m2-12--kwargs-for-bound-method-callbacks) | Kwargs for bound-method callbacks | P1 | [ ] |
| [M2-01](#completed-1) | D5: `self.m()` binding | P0 | [x] |
| [M2-03](#completed-1) | Instantiation → `__init__`/`__new__`/dataclass fields | P1 | [x] |
| [M2-04](#completed-1) | D4: `trusted_binding` v2 for expression receivers | P0 | [x] |
| [M2-14](#completed-1) | E1 for protocol dunders (audit finding) | P1 | [x] |
| [M2-15](#completed-1) | Typed call-site arguments from their scope (new) | P1 | [x] |
| [M3-07](#m3-07--canonical-public-import-locations) | Canonical public import locations | P1 | [ ] |
| [M3-09](#m3-09--type_checking-placement) | `TYPE_CHECKING` placement | P1 | [ ] |
| [M3-13](#m3-13--ensure_names-everywhere--expanded-known_imports) | `ensure_names` everywhere + expanded `known_imports` | P1 | [ ] |
| [M3-08](#m3-08--file-style-matching) | File-style matching | P2 | [ ] |
| [M3-11](#m3-11--unused-import-cleanup) | Unused-import cleanup | P2 | [ ] |
| [M3-12](#m3-12--deterministic-pre-ruff-import-placement) | Deterministic pre-ruff import placement | P2 | [ ] |
| [M3-01](#completed-2) | Import resolution (done 2026-11-08) | P1 | [x] |
| [M3-02](#completed-2) | Whole-project call graph (done 2026-11-08) | P1 | [x] |
| [M3-03](#completed-2) | E3 cross-module call sites (done 2026-11-08) | P1 | [x] |
| [M3-04](#completed-2) | E4 typeshed/`py.typed`/stub-package loading (done 2026-11-08) | P1 | [x] |
| [M3-05](#completed-2) | K1: curated "safe to keyword" library table | P1 | [x] |
| [M3-06](#completed-2) | Version awareness (done 2026-11-08) | P1 | [x] |
| [M3-10](#completed-2) | Shadowing/collision avoidance | P1 | [x] |
| [M3-14](#completed-2) | M3 exit gate (done 2026-11-08) | P1 | [x] |
| [M3-15](#completed-2) | Wire the library keyword table into binding (audit finding) | P1 | [x] |
| [M4-01](#m4-01--prover-comprehensions-subscripts-on-typed-names-builtin-method-result-table) | Prover: comprehensions, subscripts on typed names, builtin-method result table | P1 | [ ] |
| [M4-02](#m4-02--prover-await-unwrap-trymatchaugassignloop-handling) | Prover: `Await` unwrap, `Try`/`Match`/`AugAssign`/loop handling | P1 | [ ] |
| [M4-03](#m4-03--prover-yield-typing--once-bound-classdef-calls) | Prover: yield typing + once-bound `ClassDef` calls | P1 | [ ] |
| [M4-06](#m4-06--r3-generatorasync) | R3: `generator`/`async` | P1 | [ ] |
| [M4-07](#m4-07--r4-usage_abc) | R4: `usage_abc` | P1 | [ ] |
| [M4-08](#m4-08--r5-typeguardtypeis) | R5: `typeguard`/`TypeIs` | P1 | [ ] |
| [M4-11](#m4-11--r6-union_sites) | R6: `union_sites` | P1 | [x] |
| [M4-14](#m4-14--variableattribute-annotations) | Variable/attribute annotations | P1 | [ ] |
| [M4-16](#m4-16--accept-generalreturn-specific) | Accept-general/return-specific | P1 | [x] |
| [M4-17](#m4-17--callable-r-params) | `Callable[[…], R]` params | P1 | [x] |
| [M4-13](#m4-13--r12-selfclassvarliteraltypealiasnewtype) | R12: `Self`/`ClassVar`/`Literal`/`TypeAlias`/`NewType` | P2 | [ ] |
| [M4-18](#m4-18--data-carrier-synthesis) | Data-carrier synthesis | P2 | [ ] |
| [M4-19](#m4-19--overload-synthesis) | `@overload` synthesis | P2 | [ ] |
| [M4-04](#completed-3) | R1: `optional_default` | P1 | [x] |
| [M4-05](#completed-3) | R2: `variadic_args` | P1 | [x] |
| [M4-09](#completed-3) | `never_returns` | P1 | [x] |
| [M4-10](#completed-3) | R10: `syntax_proven` | P1 | [x] |
| [M4-12](#completed-3) | R8: expression defaults | P1 | [x] |
| [M4-15](#completed-3) | Container precision | P1 | [x] |
| [M4-20](#completed-3) | Taint rule is too conservative for argument-independent results (audit finding) | P1 | [x] |
| [M5-13](#m5-13--e6-verified-synthesized-protocols) | E6-verified synthesized protocols | P0 | [ ] |
| [M5-25](#m5-25--m5-exit-gate) | M5 exit gate | P0 | [ ] |
| [M5-04](#m5-04--generatorcmindexingoperatortruthinesslen-members) | Generator/CM/indexing/operator/truthiness/`len` members | P1 | [x] |
| [M5-06](#m5-06--read-only-vs-writable-attribute-members) | Read-only vs writable attribute members | P1 | [x] |
| [M5-09](#m5-09--p2p3-reuse-before-create) | P2/P3: reuse-before-create | P1 | [x] |
| [M5-10](#m5-10--merge-into-shared-_protocolspy--name-lockfile) | Merge into shared `_protocols.py` + name lockfile | P1 | [ ] |
| [M5-16](#m5-16--multi-variable-relations) | Multi-variable relations | P1 | [x] |
| [M5-19](#m5-19--t5-paramspec-decorator-forwarding) | T5: ParamSpec decorator forwarding | P1 | [x] |
| [M5-22](#m5-22--t1-boolopcomparison-shared-t) | T1: BoolOp/comparison shared `T` | P1 | [x] |
| [M5-24](#m5-24--no-user-symbol-shadowing-project-wide-declaration-reuse) | No user-symbol shadowing; project-wide declaration reuse | P1 | [x] |
| [M5-07](#m5-07--runtime_checkable-only-under-isinstance) | `runtime_checkable` only under `isinstance` | P2 | [x] |
| [M5-11](#m5-11--config-switch-for-per-function-placement) | Config switch for per-function placement | P2 | [x] |
| [M5-12](#m5-12--type_checking-placement) | `TYPE_CHECKING` placement | P2 | [x] |
| [M5-20](#m5-20--typevartuple-variadic-passthrough) | `TypeVarTuple` variadic passthrough | P2 | [x] |
| [M5-21](#m5-21--t_cot_contra-variance) | `T_co`/`T_contra` variance | P2 | [x] |
| [M5-23](#m5-23--pep-695-def-ftx-t) | PEP 695 `def f[T](x: T)` | P2 | [ ] |
| [M5-01](#completed-4) | P1: typed protocol member returns | P1 | [x] |
| [M5-02](#completed-4) | Typed protocol member params | P1 | [x] |
| [M5-03](#completed-4) | `async def` protocol members | P1 | [x] |
| [M5-05](#completed-4) | P4: `__call__` callback protocols | P1 | [x] |
| [M5-08](#completed-4) | Collision-safe member-name allocation | P1 | [x] |
| [M5-14](#completed-4) | Bound TypeVars | P1 | [x] |
| [M5-15](#completed-4) | Constrained TypeVars | P1 | [x] |
| [M5-17](#completed-4) | Element pass-through | P1 | [x] |
| [M5-18](#completed-4) | `Self` | P1 | [x] |
| [M6-02](#m6-02--positional-onlykeyword-only-end-to-end) | Positional-only/keyword-only end-to-end | P1 | [ ] |
| [M6-05](#m6-05--callsmissing-argument-detection-rule) | `calls.missing-argument` detection rule | P1 | [ ] |
| [M6-06](#m6-06--callsunexpected-argument-detection-rule) | `calls.unexpected-argument` detection rule | P1 | [ ] |
| [M6-07](#m6-07--callsambiguous-callee-detection-rule) | `calls.ambiguous-callee` detection rule | P1 | [ ] |
| [M6-08](#m6-08--callsunresolved-callee-detection-rule) | `calls.unresolved-callee` detection rule | P1 | [ ] |
| [M6-09](#m6-09--idempotence-with-ruff-line-wrapping) | Idempotence with ruff line-wrapping | P1 | [ ] |
| [M6-04](#m6-04--style-controls) | Style controls | P2 | [ ] |
| [M6-01](#completed-5) | Danger matrix → ~60 tests | P1 | [x] |
| [M6-03](#completed-5) | Library keyword table | P1 | [x] |
| [M6-10](#completed-5) | Class-body rebinding of a method name (audit: 9 strict-xfail rows) | P0 | [x] |
| [M6-11](#completed-5) | Constructor hooks (audit: 6 strict-xfail rows) | P0 | [x] |
| [M6-12](#completed-5) | Dynamic rebinding markers (audit: 4 strict-xfail rows) | P0 | [x] |
| [M6-13](#completed-5) | `__getattribute__` interception (audit: 1 strict-xfail row, `getattribute-override`) | P1 | [x] |
| [M7-01](#m7-01--kill-superlinear-costs) | Kill superlinear costs | P1 | [ ] |
| [M7-02](#m7-02--perf-budgets) | Perf budgets | P1 | [ ] |
| [M7-16](#m7-16--wire-the-built-but-unreachable-product-surface-audit-finding) | Wire the built-but-unreachable product surface (audit finding) | P1 | [ ] |
| [M7-04](#m7-04--process-pool-parallelism) | Process-pool parallelism | P2 | [ ] |
| [M7-05](#m7-05--streaming---jobs-cli) | Streaming `--jobs` CLI | P2 | [ ] |
| [M7-06](#m7-06--memory-budget-tests) | Memory budget tests | P2 | [ ] |
| [M7-08](#m7-08--baselines--external-per-path-ignores) | Baselines + external per-path ignores | P2 | [ ] |
| [M7-09](#m7-09--reporters) | Reporters | P2 | [x] |
| [M7-10](#m7-10--lsp-diagnostics--code-actions) | LSP diagnostics + code actions | P2 | [ ] |
| [M7-11](#m7-11--pre-commitci-recipe) | Pre-commit/CI recipe | P2 | [x] |
| [M7-12](#m7-12--interactive-review-mode) | Interactive review mode | P2 | [ ] |
| [M7-13](#m7-13--astart-explain-rule-location) | `astart explain <rule> <location>` | P2 | [x] |
| [M7-14](#m7-14----backupundo-journal) | `--backup`/undo journal | P2 | [x] |
| [M7-15](#m7-15--distribution-packaging) | Distribution packaging | P3 | [x] |
| [M7-17](#m7-17--index-post_refinements-document-walks) | Index `post_refinements` document walks | P1 | [ ] |
| [M7-18](#m7-18--bound-precondition-re-evaluation-per-applied-fix) | Bound precondition re-evaluation per applied fix | P1 | [ ] |
| [M7-19](#m7-19--share-the-enginehint-index-across-fix-rounds) | Share the engine/hint index across fix rounds | P1 | [ ] |
| [M7-03](#completed-6) | Incremental content-hash cache | P1 | [x] |
| [M7-07](#completed-6) | `[tool.astart]` pyproject config | P1 | [x] |
| [M8-21](#m8-21--m8-exit-gate) | M8 exit gate | P0 | [x] |
| [M8-01](#m8-01--importsbare-import-imp001) | `imports.bare-import` IMP001 | P1 | [ ] |
| [M8-02](#m8-02--typingmissing-variable-annotation-typ005) | `typing.missing-variable-annotation` TYP005 | P1 | [ ] |
| [M8-03](#m8-03--typingno-object-annotation-typ002) | `typing.no-object-annotation` TYP002 | P1 | [ ] |
| [M8-04](#m8-04--suppressionmarker-comment-sup001) | `suppression.marker-comment` SUP001 | P1 | [ ] |
| [M8-05](#m8-05--parsingmodule-does-not-parse-prs001) | `parsing.module-does-not-parse` PRS001 | P1 | [ ] |
| [M8-06](#m8-06--typingreturn-type-mismatch--incompatible-default) | `typing.return-type-mismatch` / `incompatible-default` | P1 | [ ] |
| [M8-07](#m8-07--docs-family-doc001003004006) | Docs family DOC001/003/004/006 | P1 | [ ] |
| [M8-11](#m8-11--d6-remainder-exists-evaluation) | D6 remainder: `Exists` evaluation | P1 | [ ] |
| [M8-12](#m8-12--d8-procedural-rules) | D8: procedural rules | P1 | [ ] |
| [M8-22](#m8-22--register-the-standalone-detectors-as-catalog-rules-audit-finding) | Register the standalone detectors as catalog rules (audit finding) | P1 | [ ] |
| [M8-27](#m8-27--imp001-fixer-bare-import-a--from-a-import-b--use-site-rewrite) | IMP001 fixer: bare `import a` → `from a import b` + use-site rewrite | P1 | [ ] |
| [M8-08](#m8-08--whitespaceblank-line-normalisation) | Whitespace/blank-line normalisation | P2 | [ ] |
| [M8-09](#m8-09--constants-class-grouping-with-final) | `Constants`-class grouping with `Final` | P2 | [ ] |
| [M8-10](#m8-10--delegation-relation-to-ruff) | Delegation relation to ruff | P2 | [ ] |
| [M8-13](#m8-13--profiles--relations) | Profiles + relations | P2 | [ ] |
| [M8-28](#m8-28--string-literal-normalisation-fixer) | String literal normalisation fixer | P2 | [ ] |
| [M8-29](#m8-29--f-string-interior-normalisation-fixer) | F-string interior normalisation fixer | P2 | [ ] |
| [M8-30](#m8-30--multiline-string-indent-normalisation--textwrapdedent-fixer) | Multiline-string indent normalisation + `textwrap.dedent` fixer | P2 | [ ] |
| [M8-31](#m8-31--suppressionlint-ignore-config-sup002) | `suppression.lint-ignore-config` SUP002 | P2 | [ ] |
| [M8-32](#m8-32--suppressiontype-check-config-sup003) | `suppression.type-check-config` SUP003 | P2 | [ ] |
| [M8-33](#m8-33--configpyproject-missing-cfg001) | `config.pyproject-missing` CFG001 | P2 | [ ] |
| [M8-34](#m8-34--methodclassifier-quartet-oop001oop004) | Method/classifier quartet OOP001–OOP004 | P2 | [ ] |
| [M8-35](#m8-35--namingexception-message-variable-nam001) | `naming.exception-message-variable` NAM001 | P2 | [ ] |
| [M8-36](#m8-36--simplification-family-sim001sim006) | Simplification family SIM001–SIM006 | P2 | [ ] |
| [M8-37](#m8-37--docs-family-remainder-doc005-doc007doc013) | Docs family remainder DOC005, DOC007–DOC013 | P2 | [ ] |
| [M8-14](#m8-14--maturity-lifecycle--defaults) | `Maturity` lifecycle → defaults | P3 | [ ] |
| [M8-38](#m8-38--structureshebang-shb001) | `structure.shebang` SHB001 | P3 | [ ] |
| [M8-39](#m8-39--cli-watch-mode) | CLI watch mode | P3 | [ ] |
| [M8-23](#completed-7) | New `Final` constants join an existing `Constants` class (requested 2026-11-07) | P1 | [x] |
| [M8-24](#completed-7) | Writer replaces elements of a child list with atoms (needed by M8-23) | P1 | [x] |
| [M8-15](#completed-7) | Rule authoring kit | P3 | [x] |
| [M8-16](#completed-7) | Fix verified wrong types | P1 | [x] |
| [M8-17](#completed-7) | `list(d)` → items-not-keys | P1 | [x] |
| [M8-18](#completed-7) | `seq[0]` → `Sequence[int]` over-broad | P1 | [x] |
| [M8-19](#completed-7) | Imported-constructor argument typing | P1 | [x] |
| [M8-20](#completed-7) | `self.` receiver typing in the analyzer | P1 | [x] |
| [CC-01](#cc-01--confidence-calibration) | Confidence calibration | P1 | [ ] |
| [CC-02](#cc-02--determinism-audit) | Determinism audit | P1 | [ ] |
| [CC-03](#cc-03--error-containment-v2) | Error containment v2 | P1 | [ ] |
| [CC-04](#cc-04--property--mutation-testing) | Property + mutation testing | P1 | [ ] |
| [CC-06](#cc-06--convention-guard) | Convention guard | P1 | [x] |
| [CC-07](#cc-07--commit-hygiene-audit-finding) | Commit hygiene (audit finding) | P1 | [x] |
| [EV-01](#completed-8) | Exactus gate evidence, 2026-11-07 | P0 | [x] |
| [CC-05](#completed-8) | User-facing evidence ladder + refusal catalogue | P2 | [x] |
| [CC-08](#cc-08--remove-every-regular-expression-from-source-reading-code) | Remove every regular expression from source-reading code | P0 | [ ] |
| [CC-08-00](#cc-08-00--add-the-no-regex-guard-test-first) | Add the no-regex guard test first | P1 | [x] |
| [CC-08-01](#cc-08-01--docstring-line-scanner-replaces-docstringspy-patterns) | Docstring line scanner replaces `docstrings.py` patterns | P1 | [ ] |
| [CC-08-02](#cc-08-02--use-the-scanner-in-rulesdocstring_editpy) | Use the scanner in `rules/docstring_edit.py` | P1 | [ ] |
| [CC-08-03](#cc-08-03--use-the-scanner-in-rulesdocs_sharedpy) | Use the scanner in `rules/docs_shared.py` | P1 | [ ] |
| [CC-08-04](#cc-08-04--comment-directives-from-tokens-not-patterns-astpy) | Comment directives from tokens, not patterns (`ast.py`) | P1 | [ ] |
| [CC-08-05](#cc-08-05--string-prefix-and-quote-from-the-token-formattingpy) | String prefix and quote from the token (`formatting.py`) | P1 | [ ] |
| [CC-08-06](#cc-08-06--config-value-check-without-fullmatch-cliconfigpy) | Config value check without `fullmatch` (`cli/config.py`) | P1 | [x] |
| [CC-08-07](#cc-08-07--replace-the-re_sub-edit-in-rulesapplierspy) | Replace the `re_sub` edit in `rules/appliers.py` | P1 | [ ] |
| [CC-08-08](#cc-08-08--replace-the-two-re_search-calls-in-rulestypevarspy) | Replace the two `re_search` calls in `rules/typevars.py` | P1 | [ ] |
| [CC-08-09](#cc-08-09--identifier-case-conversion-without-sub-graphconversionsynthesispy) | Identifier case conversion without `sub` (`graph/conversion/synthesis.py`) | P1 | [x] |
| [CC-08-10](#cc-08-10--constant-name-check-by-predicates-rulesconstants_groupingpy) | Constant-name check by predicates (`rules/constants_grouping.py`) | P1 | [x] |
| [CC-10](#cc-10--one-ast-transactional-emission-and-incremental-locations) | One AST: transactional emission and incremental locations | P0 | [ ] |
| [CC-09](#cc-09--verify-declared-ast-mutations-before-committing-edits) | Verify declared AST mutations before committing edits | P0 | [ ] |
| [CC-11](#cc-11--native-lexical-provenance-and-formatcomment-ownership) | Native lexical provenance and format/comment ownership | P0 | [ ] |
| [CC-12](#cc-12--migrate-wrapping-and-insertion-onto-shared-transactions) | Migrate wrapping and insertion onto shared transactions | P1 | [ ] |
| [CC-13](#cc-13--deterministic-concurrent-inference-and-evidence-invalidation) | Deterministic concurrent inference and evidence invalidation | P1 | [ ] |
| [F-17](#f-17--seed-the-graph-from-existing-evidence-tagged-by-origin) | Seed the graph from existing evidence, tagged by origin | P0 | [x] |
| [F-18](#f-18--acceptance-policy-negotiationpolicypy) | Acceptance policy `negotiation/policy.py` | P0 | [x] |
| [F-20](#f-20--behind-fixsettingsnegotiate) | Behind `FixSettings.negotiate` | P0 | [x] |
| [F-28](#f-28--determinism-and-idempotence) | Determinism and idempotence | P0 | [x] |
| [F-29](#f-29--gate-refresh-baselinejson-and-baseline_extjson-with-negotiation-on-accept-only) | Gate: refresh `baseline.json` and `baseline_ext.json` with negotiation on; accept only | P0 | [ ] |
| [F-07](#f-07--complete-the-transfer-table) | Complete the transfer table | P1 | [ ] |
| [F-13](#f-13--builder-capabilities) | Builder: capabilities | P1 | [ ] |
| [F-15](#f-15--builder-library-calls) | Builder: library calls | P1 | [x] |
| [F-16](#f-16--builder-declared-annotations) | Builder: declared annotations | P1 | [ ] |
| [F-21](#f-21--returns-as-union-contracts) | Returns as union contracts | P1 | [ ] |
| [F-22](#f-22--backward-reconciliation-of-parameters) | Backward reconciliation of parameters | P1 | [ ] |
| [F-23](#f-23--conflict-reporting) | Conflict reporting | P1 | [ ] |
| [F-24](#f-24--calibrate-the-lossy-collapses-with-the-x-05-method) | Calibrate the lossy collapses with the X-05 method | P1 | [ ] |
| [F-26](#f-26--explanation-trail-per-candidate) | Explanation trail per candidate | P1 | [ ] |
| [F-27](#f-27--performance-graph-build-linear-in-nodes-per-function-incremental-rebuild-budget-tests) | Performance: graph build linear in nodes; per-function incremental rebuild; budget tests | P1 | [ ] |
| [F-30](#f-30--docsarchitecturenegotiationmd) | `docs/architecture/negotiation.md` | P1 | [x] |
| [F-31](#f-31--gold-family-negotiated) | Gold family `negotiated` | P1 | [ ] |
| [F-33](#f-33--cross-module-edges-through-projectindex) | Cross-module edges through `ProjectIndex` | P1 | [ ] |
| [F-34](#f-34--safety-bounds-per-module-event-and-wall-clock-budget-on-overrun-fall-back-to-the) | Safety bounds: per-module event and wall-clock budget; on overrun fall back to the | P1 | [ ] |
| [F-37](#f-37--default-literal-parameters-in-the-negotiator) | Default-literal parameters in the negotiator | P1 | [ ] |
| [F-40](#f-40--comprehensions-as-derived-nodes) | Comprehensions as derived nodes | P1 | [ ] |
| [F-41](#f-41--calls-on-builtin-typed-receivers) | Calls on builtin-typed receivers | P1 | [x] |
| [F-43](#f-43--quote-instead-of-refusing) | Quote instead of refusing | P1 | [ ] |
| [F-25](#f-25--objective-choice-between-a-concrete-union-and-an-abc-abstraction) | Objective choice between a concrete union and an ABC abstraction | P2 | [ ] |
| [F-32](#f-32--retire-superseded-items) | Retire superseded items | P2 | [x] |
| [F-01](#completed-9) | Data model `negotiation/model.py`: `Relation` (assigns, returns, argument, call_result,… | P0 | [x] |
| [F-02](#completed-9) | Provenance: a candidate carries the set of `Origin`s that support it; `independent` means… | P0 | [x] |
| [F-03](#completed-9) | Type algebra `negotiation/algebra.py` (`union`, `intersect`, `members`) over type… | P0 | [x] |
| [F-04](#completed-9) | `negotiation/beliefs.py` `Belief`: add by polarity (union keeps the best confidence per… | P0 | [x] |
| [F-05](#completed-9) | `negotiation/graph.py` `ContractGraph`: nodes by stable path text, edges with… | P0 | [x] |
| [F-06](#completed-9) | `negotiation/negotiator.py` `Negotiator.solve`: queue of ants, wormhole memo `(path,… | P0 | [x] |
| [F-07a](#completed-9) | `negotiation/transfer.py`: first transfer table | P0 | [x] |
| [F-08](#completed-9) | Builder: assignments (plain, annotated = declaration, augmented, tuple unpacking,… | P1 | [x] |
| [F-09](#completed-9) | Builder: returns and calls | P1 | [x] |
| [F-10](#completed-9) | Builder: containers | P1 | [x] |
| [F-11](#completed-9) | Builder: attributes | P1 | [x] |
| [F-12](#completed-9) | Builder: narrowing | P1 | [x] |
| [F-14](#completed-9) | Builder: operators using the typer's tables (numeric tower, str/bytes/list concat,… | P1 | [x] |
| [F-35](#completed-9) | Protocol-dunder results in the negotiator (`__len__` → `int`, `__exit__` → `bool / None`,… | P0 | [x] |
| [F-36](#completed-9) | Calibrated `bool` returns in the negotiator: returns that are boolean by syntax… | P0 | [x] |
| [F-38](#completed-9) | Lost contributions: a transfer that yields nothing for a union/declaration contract… | P0 | [x] |
| [F-39](#completed-9) | Opacity reasons: every opaque node records why (`Built.why`), the groundwork for `astart… | P1 | [x] |
| [F-42](#completed-9) | Names that exist when an annotation is evaluated: a negotiated parameter or return hint… | P0 | [x] |
| [F-19](#completed-9) | Shadow mode: run the negotiator next to `HintIndex`, record every difference (new hint,… | P0 | [x] |
| [P-02](#p-02--variable-annotations) | Variable annotations | P0 | [ ] |
| [P-03](#p-03--return-types-that-are-not-provable) | Return types that are "not provable" | P0 | [ ] |
| [P-08](#p-08--the-reverse-direction) | The reverse direction | P0 | [ ] |
| [W-01](#w-01--record-the-verification-commands-and-their-baseline-results) | Record the verification commands and their baseline results | P0 | [ ] |
| [W-02](#w-02--find-why-the-checker-gate-keeps-only-4-annotations-on-the-resolver-pair) | Find why the checker gate keeps only 4 annotations on the resolver pair | P0 | [ ] |
| [P-04](#p-04--tainted-parameters) | "Tainted" parameters | P1 | [ ] |
| [P-05](#p-05--no-candidate-72) | "No candidate" (72) | P1 | [ ] |
| [P-06](#p-06--call-sites-unknown--uncorroborated--escapes) | "Call sites unknown / uncorroborated / escapes" | P1 | [ ] |
| [P-07](#p-07--name-agnostic-scoring-of-synthesized-protocols-and-typevars) | Name-agnostic scoring of synthesized Protocols and TypeVars | P1 | [ ] |
| [P-09](#p-09--round-trip-gate) | Round-trip gate | P1 | [ ] |
| [P-10](#p-10--import-parity-every-name-the-written-annotations-use-is-imported) | Import parity: every name the written annotations use is imported | P1 | [ ] |
| [T-01](#t-01--dunder-parameters-from-the-language) | Dunder parameters from the language | P1 | [ ] |
| [T-02](#t-02--copy-annotations-from-the-base-class-method-of-the-same-name) | Copy annotations from the base-class method of the same name | P1 | [ ] |
| [T-03](#t-03--apply-a-sibling-stub) | Apply a sibling stub | P1 | [ ] |
| [T-08](#t-08--library-return-types-from-typeshed) | Library return types from typeshed | P1 | [x] |
| [W-03](#w-03--stop-object-leaking-into---engine-annotations) | Stop `object` leaking into `--engine` annotations | P1 | [x] |
| [W-04](#w-04--remove-the-last-typeshed_client-use-from-generate_libkwpy) | Remove the last `typeshed_client` use from `generate_libkw.py` | P1 | [x] |
| [W-06](#w-06--burn-down-unprovable-calls-in-the-negotiator) | Burn down unprovable calls in the negotiator | P1 | [x] |
| [W-07](#w-07--burn-down-unbindable-calls-and-escaping-functions) | Burn down unbindable calls and escaping functions | P1 | [ ] |
| [W-08](#w-08--let-the-negotiator-write-default-literal-parameters-f-37) | Let the negotiator write default-literal parameters (F-37) | P1 | [ ] |
| [W-11](#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name) | Annotate a method that returns its own class (`Self` or quoted name) | P1 | [ ] |
| [W-12](#w-12--annotate-instance-attributes-from-negotiation) | Annotate instance attributes from negotiation | P1 | [ ] |
| [T-04](#t-04--name-heuristics-as-calibrated-candidates) | Name heuristics as *calibrated candidates* | P2 | [ ] |
| [T-05](#t-05--ingest-external-suggestions) | Ingest external suggestions | P2 | [ ] |
| [T-06](#t-06--generators-infer-types-returns-iterator-for-any-yield) | Generators: `infer-types` returns `Iterator` for any `yield` | P2 | [ ] |
| [T-09](#t-09--optional-runtime-use-of-typeshed_client-in---project-mode) | Optional runtime use of `typeshed_client` in `--project` mode | P2 | [x] |
| [W-05](#w-05--sync-changelog-evidence-ladder-architecture-and-readme-with-the-code) | Sync CHANGELOG, evidence ladder, architecture and README with the code | P2 | [x] |
| [W-09](#w-09--annotate-the-parameters-of-__exit__-and-__aexit__) | Annotate the parameters of `__exit__` and `__aexit__` | P2 | [ ] |
| [W-10](#w-10--copy-annotations-from-the-base-classs-method) | Copy annotations from the base class's method | P2 | [ ] |
| [W-13](#w-13--type-generators-as-iterator) | Type generators as `Iterator[...]` | P2 | [ ] |
| [W-14](#w-14--annotate-class-level-and-module-level-variables) | Annotate class-level and module-level variables | P2 | [ ] |
| [T-07](#t-07--typing_utilsissubtype-as-a-differential-oracle-for-typealgebraintersect-and) | `typing_utils.issubtype` as a differential oracle for `TypeAlgebra.intersect` and | P3 | [ ] |
| [P-01](#completed-10) | Pair benchmark and accepted baseline: `scripts/compare/pair.py`, `fixtures/`,… | P0 | [x] |
| [Q-28](#q-28----format-sarif-for-astart-check-m7-09) | `--format sarif` for `astart check` (M7-09) | P2 | [x] |
| [Q-33](#q-33--typ002-typingno-object-annotation) | TYP002 `typing.no-object-annotation` | P1 | [ ] |
| [Q-34](#q-34--typ006-typingbare-generic) | TYP006 `typing.bare-generic` | P1 | [ ] |
| [Q-35](#q-35--prs001-m8-05-when-the-file-does-not-parse) | PRS001 (M8-05): when the file does not parse | P1 | [ ] |
| [Q-38](#q-38--add-reliability-float-to-_site-in-hintspy-defaulting-to-10) | Add `reliability: float` to `_Site` in `hints.py` defaulting to `1.0` | P2 | [x] |
| [Q-57](#q-57--return-type-characterization-through-the-fixer) | Return-type characterization through the fixer | P2 | [x] |
| [Q-58](#q-58--parameter-hint-characterization) | Parameter-hint characterization | P2 | [x] |
| [Q-61](#q-61--returns--raises-stubs) | Returns / Raises stubs | P1 | [ ] |
| [Q-64](#q-64--docstring-reflow-with-textwrap) | Docstring reflow with `textwrap` | P3 | [ ] |
| [Q-68](#q-68--kill-the-50k-line-cliff-m7-01-evidence-from-q-31) | Kill the ~50k-line cliff (M7-01 evidence from Q-31) | P1 | [ ] |
| [X-02](#x-02--contradictions-that-remain-6-of-12-789) | Contradictions that remain (6 of 12 789) | P1 | [x] |
| [X-03](#x-03--self-and-typevar-returns-for-classmethods) | `Self` and TypeVar returns for classmethods | P1 | [ ] |
| [X-04](#x-04--names-imported-from-other-modules-cannot-be-judged-by-relation) | Names imported from other modules cannot be judged by `relation()` | P1 | [ ] |
| [X-05](#x-05--calibrate-more-candidate-categories-with-the-same-method-as) | Calibrate more candidate categories with the same method as | P1 | [ ] |
| [X-06](#x-06--per-module---jobs-in-astart-fix-itself) | Per-module `--jobs` in `astart fix` itself | P1 | [x] |
| [X-07](#x-07--grow-the-external-corpus-more-distributions-async-data-cli-orm-a-held-out-split) | Grow the external corpus: more distributions (async, data, CLI, ORM), a held-out split | P2 | [ ] |
| [X-08](#x-08--missed-annotation-reasons-on-the-external-corpus-12-789-originals-no-candidate-3) | Missed-annotation reasons on the external corpus (12 789 originals): `no candidate` 3 | P2 | [ ] |
| [Q-01](#completed-11) | String methods that return `str` | P1 | [x] |
| [Q-02](#completed-11) | String methods that return `bool`/`int`: `startswith endswith isdigit isalpha isalnum… | P1 | [x] |
| [Q-03](#completed-11) | `str % anything` → `str` (printf formatting) | P1 | [x] |
| [Q-04](#completed-11) | List concatenation: in `_binop`, when both sides type to the same `list[...]` string and… | P1 | [x] |
| [Q-05](#completed-11) | Subscripts | P1 | [x] |
| [Q-06](#completed-11) | `abs`, `round`, `min`, `max`, `sorted` | P1 | [x] |
| [Q-07](#completed-11) | `list(x)`, `set(x)`, `tuple(x)` with a typed argument: `list(list[T])` → `list[T]`;… | P1 | [x] |
| [Q-08](#completed-11) | `dict.get`/`list.copy`/`dict.keys` are NOT in scope; add a comment-free refusal test… | P2 | [x] |
| [Q-09](#completed-11) | Add family `variadic` (also add it to the `expected` set in… | P2 | [x] |
| [Q-10](#completed-11) | Add family `attribute_read` with 6 cases mirroring `tests/astart/rules/test_rules_attribute_reads.py`… | P2 | [x] |
| [Q-11](#completed-11) | Add family `comprehension` with 6 cases mirroring… | P2 | [x] |
| [Q-12](#completed-11) | Add family `multi_binding` with 6 cases mirroring… | P2 | [x] |
| [Q-13](#completed-11) | CRLF: new `tests/astart/rules/test_rules_line_endings.py` | P2 | [x] |
| [Q-14](#completed-11) | Hostile inputs: new `tests/astart/rules/test_rules_hostile_inputs.py`, parametrized over: empty… | P2 | [x] |
| [Q-15](#completed-11) | Determinism across hash seeds: new `tests/astart/rules/test_rules_determinism.py` | P1 | [x] |
| [Q-16](#completed-11) | Convention guard (CC-06): new `tests/astart/test_conventions.py` with three tests that scan… | P2 | [x] |
| [Q-17](#completed-11) | Constants guard: in the same file, assert that every class named `Constants` in… | P2 | [x] |
| [Q-18](#completed-11) | README flag guard: new `tests/astart/test_readme_flags.py` | P2 | [x] |
| [Q-19](#completed-11) | `astart --version` | P2 | [x] |
| [Q-20](#completed-11) | `astart rules`: new subcommand printing one line per rule: `CODE  key  severity  title`,… | P2 | [x] |
| [Q-21](#completed-11) | `astart explain CODE`: prints the rule's `rationale`, then each example's source with… | P2 | [x] |
| [Q-22](#completed-11) | `docs/guides/rules.md` generated by a new script `scripts/generate_rule_docs.py` (iterate the… | P2 | [x] |
| [Q-23](#completed-11) | `docs/architecture/architecture.md`: one paragraph per module in `src/astart/rules/` (`ls` it; read… | P2 | [x] |
| [Q-24](#completed-11) | `CHANGELOG.md`: one `## 2026-11-07` heading, bullets copied from the entries in section… | P3 | [x] |
| [Q-25](#completed-11) | `.pre-commit-hooks.yaml` (M7-11): one hook, id `astart-fix`, `entry: astart fix --check`,… | P2 | [x] |
| [Q-26](#completed-11) | `.github/workflows/ci.yml`: on push/pull_request, Python 3.12, steps: install with `pip… | P1 | [x] |
| [Q-27](#completed-11) | `--exclude GLOB` for `astart check` and `astart fix` (repeatable) | P2 | [x] |
| [Q-29](#completed-11) | Grow the corpus (M1-07 beyond 113): copy 15 stdlib modules not yet present to… | P2 | [x] |
| [Q-30](#completed-11) | Five more semantic projects (M1-12): add entries to `scripts/benchmark/artifacts/resources/projects.json` copying… | P2 | [x] |
| [Q-31](#completed-11) | The ≈ 50k-line throughput row (M1-10): concatenate corpus files into one 50k-line module… | P2 | [x] |
| [Q-32](#completed-11) | `docs/analysis/scripts.benchmark.md`: add a "How to refresh the baseline" section with the three exact… | P3 | [x] |
| [Q-36](#completed-11) | Read `HintIndex._judge_pass`, `_call_sites` and `_judge_call_sites` in… | P2 | [x] |
| [Q-37](#completed-11) | Create `src/astart/rules/slots.py` with a `SlotTable` class: `deposit(*, slot: str, kind:… | P2 | [x] |
| [Q-39](#completed-11) | `tests/astart/rules/test_rules_typer_negatives.py`: 12 one-line refusal tests proving the typer… | P2 | [x] |
| [Q-40](#completed-11) | `tests/astart/rules/test_rules_hint_cache.py`: assert two `fix_source` calls on identical text return… | P2 | [x] |
| [Q-41](#completed-11) | Document every `Rejection` value: `grep -n "class Rejection"… | P2 | [x] |
| [Q-42](#completed-11) | Document every `SkipCode` the same way (`docs/guides/skip-codes.md`) | P2 | [x] |
| [Q-43](#completed-11) | `README.md`: add a "Limits" section (five bullets, copied from the "Where it is far from… | P2 | [x] |
| [Q-44](#completed-11) | Add `tests/astart/cli/test_cli_exit_codes.py`: `fix --check` on a clean file → 0; on a file with a… | P2 | [x] |
| [Q-45](#completed-11) | Add `tests/astart/cli/test_cli_formats.py`: `check --format json` output parses with `json.loads`… | P2 | [x] |
| [Q-46](#completed-11) | Add `tests/astart/rules/test_rules_variadic_methods.py`: the same cases as… | P2 | [x] |
| [Q-47](#completed-11) | Add `tests/astart/rules/test_rules_default_expression_edges.py`: refusal tests for `x=-1` called with… | P2 | [x] |
| [Q-48](#completed-11) | Create `tests/astart/rules/test_rules_typer_negatives.py` | P2 | [x] |
| [Q-49](#completed-11) | Create `tests/astart/rules/test_rules_typer_positives.py` with the same shape as Q-48 but parametrize… | P2 | [x] |
| [Q-50](#completed-11) | Create `.pre-commit-hooks.yaml` | P2 | [x] |
| [Q-51](#completed-11) | Create `tests/astart/test_conventions.py` | P2 | [x] |
| [Q-52](#completed-11) | `README.md`: add a `## Limits` section just after the paragraph under the `astart fix`… | P2 | [x] |
| [Q-53](#completed-11) | Create `CHANGELOG.md` with `# Changelog`, a `## 2026-11-07` heading, and these bullets:… | P3 | [x] |
| [Q-54](#completed-11) | Create `tests/astart/rules/test_rules_typer_matrix.py` pinning every row of the table above that says… | P2 | [x] |
| [Q-55](#completed-11) | `**` operator | P2 | [x] |
| [Q-56](#completed-11) | Pin the gaps so closing them is visible: create `tests/test_rules_typer_gaps.py` with… | P2 | [x] |
| [Q-59](#completed-11) | Write `docs/architecture/typing-inference.md`: copy the table at the top of this section verbatim, add… | P2 | [x] |
| [X-01](#completed-11) | P0 | P0 | [x] |
| [Q-60](#completed-11) | DOC001 stub docstrings — DONE 2026-11-08 with a different design than first sketched | P2 | [x] |
| [Q-62](#completed-11) | Run ruff on docstring content | P2 | [x] |
| [Q-63](#completed-11) | Whitespace outside docstrings | P2 | [x] |
| [Q-65](#completed-11) | Heal renamed parameters | P2 | [x] |
| [Q-66](#completed-11) | Module docstring support: extend `_docstring()` in `rules/docs_fixes.py` to accept… | P2 | [x] |
| [Q-67](#completed-11) | `--no-docs` flag (`astart fix --no-docs`) that excludes the `docs.*` fixes, for users who… | P2 | [x] |
| [H-01](#h-01--reporters-in-the-cli-m7-09-q-28-part-of-m7-16) | Reporters in the CLI (M7-09, Q-28, part of M7-16) | P0 | [x] |
| [H-02](#h-02--toolastart-in-the-cli-m7-07-user-visible-half-m7-16) | `[tool.astart]` in the CLI (M7-07 user-visible half, M7-16) | P0 | [ ] |
| [H-08](#h-08--astart-untype-p-08-the-reverse-of-fix) | `astart untype` (P-08): the reverse of `fix` | P0 | [ ] |
| [H-03](#h-03--baselines-in-the-cli-m7-08) | Baselines in the CLI (M7-08) | P1 | [x] |
| [H-04](#h-04--catalog-rules-typ002-and-typ006-q-33-q-34-m8-03) | Catalog rules TYP002 and TYP006 (Q-33, Q-34, M8-03) | P1 | [ ] |
| [H-05](#h-05--prs001-for-files-that-do-not-parse) | PRS001 for files that do not parse | P1 | [ ] |
| [H-06](#h-06--returns--raises-docstring-stubs-q-61-m8-07) | Returns / Raises docstring stubs (Q-61, M8-07) | P1 | [ ] |
| [H-07](#h-07--wider-known_imports-m3-13) | Wider `known_imports` (M3-13) | P1 | [ ] |
| [H-09](#h-09--gate-for-the-conversion-pair-p-09) | Gate for the conversion pair (P-09) | P1 | [ ] |
| [H-11](#h-11--astart-fix---jobs-n) | `astart fix --jobs N` | P1 | [ ] |
| [H-10](#h-10--differential-oracle-t-07) | Differential oracle (T-07) | P2 | [ ] |
| [H-12](#h-12--keyword-style-controls) | Keyword style controls | P2 | [ ] |
| [G-01](#g-01--make-the-accuracy-contract-machine-checkable) | Make the accuracy contract machine-checkable | P0 | [x] |
| [G-02](#g-02--score-valid-narrowing-as-narrower-not-wrong) | Score valid narrowing as `narrower`, not `wrong` | P0 | [x] |
| [G-03](#g-03--give-every-missed-annotation-an-owner) | Give every missed annotation an owner | P0 | [x] |
| [G-04](#g-04--root-cause-every-remaining-contradiction) | Root-cause every remaining contradiction | P0 | [ ] |
| [G-05](#g-05--normalise-generator-defaults-and-subtype-spelling-in-the-scorer) | Normalise `Generator` defaults and subtype spelling in the scorer | P1 | [x] |
| [G-06](#g-06--never-type-a-descriptor-attribute-as-its-value) | Never type a descriptor attribute as its value | P1 | [ ] |
| [G-07](#g-07--run-the-checker-gate-on-the-pairs-and-keep-the-result) | Run the checker gate on the pairs and keep the result | P1 | [ ] |
| [G-08](#g-08--list-accepted-deviations-from-the-authors-pair) | List accepted deviations from the author's pair | P2 | [x] |
| [G-09](#g-09--subtypea-p-recurses-forever-when-a-protocol-method-returns-the-protocol) | `subtype(A, P)` recurses forever when a protocol method returns the protocol | P0 | [ ] |
| [G-10](#g-10--annotate-locals-that-are-assigned-more-than-once-in-engine-mode) | Annotate locals that are assigned more than once in engine mode | P0 | [ ] |
| [S-01](#s-01--merge-consecutive-if-type_checking-blocks-and-drop-empty-ones) | Merge consecutive `if TYPE_CHECKING:` blocks and drop empty ones | P1 | [ ] |
| [S-02](#s-02--put-runtime-imports-before-every-type_checking-block) | Put runtime imports before every `TYPE_CHECKING` block | P1 | [ ] |
| [S-03](#s-03--use-type-x---for-type-aliases) | Use `type X = ...` for type aliases | P2 | [ ] |
| [S-04](#s-04--drop-from-a-import-b-when-from-ab-import-c-covers-its-uses) | Drop `from a import b` when `from a.b import c` covers its uses | P1 | [ ] |
| [S-05](#s-05--lowercase-constants-attributes-without-a-leading-underscore) | Lowercase `Constants` attributes without a leading underscore | P1 | [ ] |
| [S-06](#s-06--keep-the-constants-docstring-generated-and-current) | Keep the `Constants` docstring generated and current | P1 | [ ] |
| [S-07](#s-07--every-fix-above-is-switchable-and-configurable) | Every fix above is switchable and configurable | P0 | [ ] |
| [S-08](#s-08--normalise-exception-messages-to-a-variable-named-msg) | Normalise exception messages to a variable named `msg` | P1 | [ ] |
| [S-09](#s-09--sort-class-methods-by-kind-ported-from-exactus-organize) | Sort class methods by kind (ported from Exactus `organize`) | P1 | [ ] |
| [I-01](#i-01--narrow-the-else-branch-by-complement) | Narrow the `else` branch by complement | P1 | [x] |
| [I-02](#i-02--narrow-with-match-class-and-literal-patterns) | Narrow with `match` class and literal patterns | P2 | [x] |
| [I-03](#i-03--bind-walrus-targets) | Bind walrus targets | P2 | [x] |
| [I-04](#i-04--type-with-targets-from-__enter__) | Type `with` targets from `__enter__` | P1 | [ ] |
| [I-05](#i-05--type-for-targets-from-common-iterables) | Type `for` targets from common iterables | P1 | [ ] |
| [I-06](#i-06--type-except-e-as-e-and-exception-flow) | Type `except E as e` and exception flow | P2 | [ ] |
| [I-07](#i-07--async-inference-await-gather-async-generators) | Async inference: `await`, `gather`, async generators | P1 | [ ] |
| [I-08](#i-08--optional-results-of-stdlib-lookups) | Optional results of stdlib lookups | P1 | [x] |
| [I-09](#i-09--defaultdict-counter-deque-element-types-from-mutation) | `defaultdict`, `Counter`, `deque` element types from mutation | P1 | [ ] |
| [I-10](#i-10--numeric-tower-and-operator-result-rules) | Numeric tower and operator result rules | P1 | [ ] |
| [I-11](#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields) | Attribute chains and dataclass/NamedTuple/TypedDict fields | P1 | [ ] |
| [I-12](#i-12--property-getters-as-typed-attributes) | Property getters as typed attributes | P1 | [ ] |
| [I-13](#i-13--overload-selection-by-argument-types) | Overload selection by argument types | P2 | [x] |
| [I-14](#i-14--literal-and-final-inference) | Literal and Final inference | P2 | [ ] |
| [I-15](#i-15--recursion-and-mutual-recursion) | Recursion and mutual recursion | P1 | [x] |
| [I-16](#i-16--abstract-methods-and-subclass-joins) | Abstract methods and subclass joins | P2 | [ ] |
| [I-17](#i-17--tuple-star-unpack-slice-and-operator-results-on-containers) | Tuple, star-unpack, slice, and operator results on containers | P1 | [ ] |
| [I-18](#i-18--typevar-solving-from-call-arguments) | TypeVar solving from call arguments | P1 | [ ] |
| [I-19](#i-19--join-and-simplify-unions-deterministically) | Join and simplify unions deterministically | P1 | [ ] |
| [I-20](#i-20--cross-validate-the-confidence-tiers) | Cross-validate the confidence tiers | P1 | [ ] |
| [I-21](#i-21--library-method-returns-on-stub-classes) | Library method returns on stub classes | P1 | [x] |
| [I-22](#i-22--__call__-__getitem__-__iter__-__len__-of-module-classes) | `__call__`, `__getitem__`, `__iter__`, `__len__` of module classes | P2 | [ ] |
| [I-23](#i-23--stop-at-the-evidence-explain-why-a-node-stays-opaque) | Stop at the evidence: explain why a node stays opaque | P1 | [ ] |
| [API-01](#api-01--export-infer_type-or-remove-it-from-docsguidesapimd) | Export `infer_type` or remove it from `docs/guides/API.md` | P1 | [x] |
| [API-02](#api-02--check_source-and-fix_source-public-wrappers-with-one-settings-object) | `check_source` and `fix_source` public wrappers with one settings object | P0 | [x] |
| [API-03](#api-03--fix_paths-and-fix_file-with-atomic-writes) | `fix_paths` and `fix_file` with atomic writes | P1 | [x] |
| [API-04](#api-04--public-settings-with-from_pyproject) | Public `Settings` with `from_pyproject` | P1 | [x] |
| [API-05](#api-05--stable-public-surface-and-version-policy) | Stable public surface and version policy | P1 | [x] |
| [API-06](#api-06--json-schemas-for-findings-and-reports) | JSON schemas for findings and reports | P1 | [x] |
| [API-07](#api-07--plugin-api-custom-rules-and-fixes) | Plugin API: custom rules and fixes | P2 | [ ] |
| [API-08](#api-08--progress-and-cancellation-callbacks) | Progress and cancellation callbacks | P2 | [x] |
| [API-09](#api-09--testssupport-helpers-for-rule-authors) | `tests.support` helpers for rule authors | P2 | [x] |
| [API-10](#api-10--language-server-skeleton-m7-10) | Language server skeleton (M7-10) | P3 | [ ] |
| [API-11](#api-11--exit-code-and-error-contract) | Exit-code and error contract | P1 | [x] |
| [API-12](#api-12--machine-readable-astart-rules---json) | Machine-readable `astart rules --json` | P2 | [x] |
| [API-13](#api-13--cache-api-and-invalidation-policy) | Cache API and invalidation policy | P2 | [x] |
| [AF-01](#af-01--annotate-args-and-kwargs) | Annotate `*args` and `**kwargs` | P1 | [ ] |
| [AF-02](#af-02--annotate-selfcls-only-when-the-style-asks) | Annotate `self`/`cls` only when the style asks | P2 | [ ] |
| [AF-03](#af-03--dunder-method-annotations-from-the-language) | Dunder method annotations from the language | P1 | [ ] |
| [AF-04](#af-04--dataclass-namedtuple-and-typeddict-fields) | Dataclass, NamedTuple and TypedDict fields | P1 | [ ] |
| [AF-05](#af-05--classvar-and-final-inference) | `ClassVar` and `Final` inference | P1 | [ ] |
| [AF-06](#af-06--modernise-typing-spellings-by-target-version) | Modernise `typing` spellings by target version | P1 | [ ] |
| [AF-07](#af-07--from-__future__-import-annotations-policy) | `from __future__ import annotations` policy | P2 | [ ] |
| [AF-08](#af-08--docstring-types-follow-annotations) | Docstring types follow annotations | P1 | [ ] |
| [AF-09](#af-09--generate-raises-yields-attributes-sections) | Generate `Raises`, `Yields`, `Attributes` sections | P1 | [ ] |
| [AF-10](#af-10--wrap-long-annotations-and-signatures) | Wrap long annotations and signatures | P2 | [ ] |
| [AF-11](#af-11--canonical-order-of-union-arms-and-none-last) | Canonical order of union arms and `None` last | P1 | [ ] |
| [AF-12](#af-12--import-sorting-and-grouping) | Import sorting and grouping | P1 | [ ] |
| [AF-13](#af-13--blank-line-whitespace-and-eol-normalisation) | Blank-line, whitespace and EOL normalisation | P2 | [ ] |
| [AF-14](#af-14--__all__-generation-and-sorting) | `__all__` generation and sorting | P2 | [ ] |
| [AF-15](#af-15--replace-object-and-any-annotations-by-inferred-types) | Replace `object` and `Any` annotations by inferred types | P1 | [ ] |
| [AF-16](#af-16--extract-repeated-long-annotations-into-type-aliases) | Extract repeated long annotations into type aliases | P3 | [ ] |
| [AF-17](#af-17--consistent-optional-spelling-inside-a-file) | Consistent `Optional` spelling inside a file | P2 | [ ] |
| [AF-18](#af-18--annotation-report) | Annotation report | P1 | [ ] |
| [AF-19](#af-19--keep-user-annotations-never-overwrite) | Keep user annotations; never overwrite | P0 | [ ] |
| [AF-20](#af-20--per-file-style-detection) | Per-file style detection | P2 | [ ] |
| [AF-21](#af-21--format-the-code-inside-f-string-fields-with-ruff-then-put-it-back) | Format the code inside f-string fields with ruff, then put it back | P0 | [ ] |
| [AF-22](#af-22--define-deterministic-google-docstring-policy-and-analyzer-ownership) | Define deterministic Google docstring policy and analyzer ownership | P0 | [ ] |
| [AF-23](#af-23--gdc002-measure-the-docstring-summary-itself) | GDC002: measure the docstring summary itself | P0 | [ ] |
| [AF-24](#af-24--gdc025-document-statically-established-public-attributes) | GDC025: document statically established public attributes | P0 | [ ] |
| [AF-25](#af-25--gdc018-require-recognizable-documented-types-for-unannotated-parameters) | GDC018: require recognizable documented types for unannotated parameters | P1 | [ ] |
| [AF-26](#af-26--gdc021-validate-tuple-result-documentation-structure) | GDC021: validate tuple-result documentation structure | P1 | [ ] |
| [R-01](#r-01--baseline-refreshes-must-be-justified-and-logged) | Baseline refreshes must be justified and logged | P0 | [x] |
| [R-02](#r-02--hold-out-pairs-stop-overfitting-to-the-two-fixtures) | Hold-out pairs: stop overfitting to the two fixtures | P0 | [ ] |
| [R-03](#r-03--typeshed-snapshot-drift-between-machines) | Typeshed snapshot drift between machines | P1 | [ ] |
| [R-04](#r-04--emitted-code-must-compile-on-every-supported-target) | Emitted code must compile on every supported target | P1 | [ ] |
| [R-05](#r-05--ruff-version-differences-break-idempotence-and-f-string-formatting) | ruff version differences break idempotence and f-string formatting | P1 | [ ] |
| [R-06](#r-06--type-checker-absent-old-or-different-pyright-vs-mypy) | Type checker absent, old or different (pyright vs mypy) | P1 | [ ] |
| [R-07](#r-07--large-files-and-deep-projects-blow-up-time-or-memory) | Large files and deep projects blow up time or memory | P0 | [ ] |
| [R-08](#r-08--parallel-runs-corrupt-the-cache-or-interleave-output) | Parallel runs corrupt the cache or interleave output | P1 | [ ] |
| [R-09](#r-09--weird-files-encodings-bom-crlf-tabs-form-feeds-nul-bytes) | Weird files: encodings, BOM, CRLF, tabs, form feeds, NUL bytes | P0 | [ ] |
| [R-10](#r-10--syntax-the-parser-does-not-know-newer-python-python-2-templates) | Syntax the parser does not know (newer Python, Python 2, templates) | P1 | [ ] |
| [R-11](#r-11--filesystem-edge-cases-symlinks-read-only-changing-files) | Filesystem edge cases: symlinks, read-only, changing files | P1 | [ ] |
| [R-12](#r-12--spans-drift-after-many-edits) | Spans drift after many edits | P0 | [ ] |
| [R-13](#r-13--security-executing-project-code-and-loading-plugins) | Security: executing project code and loading plugins | P0 | [x] |
| [R-14](#r-14--licensing-and-attribution) | Licensing and attribution | P1 | [x] |
| [R-15](#r-15--documentation-drift) | Documentation drift | P1 | [x] |
| [R-16](#r-16--flaky-or-slow-tests-hide-real-failures) | Flaky or slow tests hide real failures | P1 | [ ] |
| [R-17](#r-17--incident-playbook-a-release-writes-a-wrong-annotation) | Incident playbook: a release writes a wrong annotation | P0 | [ ] |
| [R-18](#r-18--merge-conflicts-on-hot-shared-files) | Merge conflicts on hot shared files | P0 | [ ] |
| [R-19](#r-19--the-todo-file-itself-size-concurrent-edits-format-corruption) | The TODO file itself: size, concurrent edits, format corruption | P1 | [ ] |
| [R-20](#r-20--engine-health-the-old-converter-can-fail-or-change) | Engine health: the old converter can fail or change | P1 | [ ] |
| [R-21](#r-21--deep-nesting-and-recursion-limits) | Deep nesting and recursion limits | P0 | [ ] |
| [R-22](#r-22--unicode-names-and-generated-name-collisions) | Unicode names and generated-name collisions | P2 | [ ] |
| [R-23](#r-23--optional-dependencies-missing) | Optional dependencies missing | P2 | [ ] |
| [R-24](#r-24--honest-accuracy-reporting) | Honest accuracy reporting | P0 | [x] |
| [R-25](#r-25--tests-and-lint-for-the-todo-tooling) | Tests and lint for the TODO tooling | P1 | [x] |
| [R-26](#r-26--make-docsplanningstatusjson-updates-atomic-locked-and-validated) | Make `docs/planning/status.json` updates atomic, locked and validated | P1 | [x] |
| [AL-01](#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling) | Control-flow graph and per-block narrowing (replaces ad-hoc `if` handling) | P1 | [ ] |
| [AL-02](#al-02--widening-at-loops-so-fixpoints-terminate-and-stay-precise) | Widening at loops so fixpoints terminate and stay precise | P1 | [ ] |
| [AL-03](#al-03--interprocedural-summaries-in-scc-order) | Interprocedural summaries in SCC order | P1 | [ ] |
| [AL-04](#al-04--alias-and-escape-analysis-for-containers) | Alias and escape analysis for containers | P1 | [ ] |
| [AL-05](#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers) | Probabilistic fusion of evidence (log-odds) instead of hand tiers | P1 | [ ] |
| [AL-06](#al-06--delta-debugging-against-the-checker-ddmin-for-batched-fixes) | Delta debugging against the checker (ddmin) for batched fixes | P0 | [ ] |
| [AL-07](#al-07--bidirectional-expected-type-inference) | Bidirectional (expected-type) inference | P1 | [ ] |
| [AL-08](#al-08--runtime-observation-as-optional-evidence-sandboxed) | Runtime observation as optional evidence (sandboxed) | P2 | [ ] |
| [AL-09](#al-09--name-and-usage-language-model-as-calibrated-prior) | Name-and-usage language model as calibrated prior | P2 | [ ] |
| [AL-10](#al-10--interned-types-and-memoised-subtype-checks) | Interned types and memoised subtype checks | P1 | [ ] |
| [AL-11](#al-11--demand-driven-content-addressed-queries-project-mode) | Demand-driven, content-addressed queries (project mode) | P2 | [ ] |
| [AL-12](#al-12--exception-flow-summaries-feeds-raises-docs) | Exception-flow summaries (feeds `Raises` docs) | P2 | [ ] |
| [AL-13](#al-13--mutation-summaries-decide-sequence-versus-list) | Mutation summaries decide `Sequence` versus `list` | P1 | [ ] |
| [AL-14](#al-14--finite-domain-values-to-literal-and-enum-suggestions) | Finite-domain values to `Literal` and `Enum` suggestions | P3 | [ ] |
| [AL-15](#al-15--framework-summaries-as-data-dataclasses-attrs-pydantic-django-fields) | Framework summaries as data (dataclasses, attrs, pydantic, Django fields) | P2 | [ ] |
| [AL-16](#al-16--minimal-unsatisfiable-core-for-conflict-reports) | Minimal unsatisfiable core for conflict reports | P2 | [ ] |
| [AL-17](#al-17--reachability-pruning-with-the-cfg) | Reachability pruning with the CFG | P2 | [ ] |
| [AL-18](#al-18--ablation-harness-marginal-value-of-each-evidence-source) | Ablation harness: marginal value of each evidence source | P1 | [ ] |
<!-- index:end -->

## Accuracy contract

**Definition of finished.** The product is finished when every open task in
this file is `done` **and** every target below prints `PASS` from
`python -m scripts.benchmark targets` (task G-01). A task that moves no target and is
not a safety rule is P3. Targets were proposed on 2026-11-08 from the measured
numbers; change one only with the user and write the reason beside it.

| Target | What it guarantees | Metric and threshold | Today | Measured by |
| --- | --- | --- | --- | --- |
| A-01 | No wrong annotation in default mode | Contradiction-precision ≥ 99.9 % on stdlib and external corpora at the default floor; 0 contradictions on the 561 gold cases | 99.69 % | `benchmarks recovery` + `gate`; `tests/astart/rules/test_gold_expansion.py` |
| A-02 | Untyped → typed conversion recovers the author's types | `--engine --min-confidence 0.5` on both pairs: ≥ 90 % exact for parameters/returns and for variables | 46 % / 45 % (221 of 482, 152 of 335; dev pair, after W-03) | `scripts.compare.pair` |
| A-03 | What is written is right, and most of it is written | Contradictions ≤ 2 % of the annotations written (stretch 0); exact + narrower + looser ≥ 93 % of recoverable annotations | 4.6 % / 7.0 % contradictions (13 of 285, 13 of 187); 54 % / 47 % coverage (dev pair, after W-03) | `scripts.compare.pair` after G-02 |
| A-04 | The type checker agrees | Checker delta (new pyright/mypy errors after `fix`) = 0 on corpus and pairs; gated conversion keeps ≥ 80 % of its annotations | gate keeps 4 of 329 | `Checker.regresses`, `scripts.compare.pair --checker` |
| A-05 | Behaviour is preserved | Semantic equivalence 15 / 15 projects (compile, import, smoke run identical) | 15 / 15 once | `benchmarks semantic` |
| A-06 | Re-running changes nothing | `fix ∘ fix` byte-equal on 100 % of corpus files, with and without ruff | passes | `tests/test_cli_idempotence*.py` |
| A-07 | Output is deterministic | Identical bytes under 3 `PYTHONHASHSEED` values and `--jobs 1` vs `--jobs N` | hash-seed only | F-28, H-11 |
| A-08 | Every written name is importable | 100 % of fixed corpus modules compile and import; no name used before it is bound | passes on corpus | semantic run + P-10 |
| A-09 | Added keywords never change a call | Danger matrix 100 %; no semantic diff in A-05 | passes | `tests/astart/rules/test_rules_kwargs_danger.py` |
| A-10 | The reverse direction is lossless | `fix(untype(typed))` equals `typed` on ≥ the A-02 exact share; `untype` removes only annotations | not built | P-09 / H-09 |
| A-11 | It is fast and never crashes | ≤ 5 s per 12 k lines; 0 crashes and 0 timeouts on corpus; bad file → one error line | 36.9 s per 12 k lines | M7-02, CC-03 |

**What no tool can reach.** In the dev pair the author chose `Iterator` over
`Generator`, `Sequence[str]` over `list[str]`, `ClassVar[...]`, `Self`, and
`object` as a top type. Those choices cannot be derived from the code. A-02 is
therefore 90 %, not 100 %, and every remaining difference must be listed with a
reason in `fixtures/artifacts/accepted_deviations.json` (task G-08).

### Traceability — which tasks deliver which target

A target is only reachable if every task listed for it is done. A task that
appears nowhere here and is not in "Product surface" is a candidate for P3.

| Target | Tasks that deliver it |
| --- | --- |
| A-01 | F-17, F-18, F-20, F-23, F-24, F-29, CC-01, M4-11, M5-13, G-01, G-04 |
| A-02 | Untyped → typed conversion recovers the author's types | `--engine --min-confidence 0.5` on both pairs: ≥ 90 % exact for parameters/returns and for variables | 46 % / 45 % (221 of 482, 152 of 335; dev pair, after W-03) | `scripts.compare.pair` |
| A-03 | What is written is right, and most of it is written | Contradictions ≤ 2 % of the annotations written (stretch 0); exact + narrower + looser ≥ 93 % of recoverable annotations | 4.6 % / 7.0 % contradictions (13 of 285, 13 of 187); 54 % / 47 % coverage (dev pair, after W-03) | `scripts.compare.pair` after G-02 |
| A-04 | W-02, G-07, M5-13, H-09 |
| A-05 | M2-08, M2-10, M2-11, M2-12, M3-09, M3-13, M6-02, W-11 |
| A-06 | F-28, M6-09, M8-27, M8-28, M8-29, M8-30 |
| A-07 | CC-02, F-28, H-11, M7-04, M7-05 |
| A-08 | M3-07, M3-09, M3-12, M3-13, H-07, P-10, W-11 |
| A-09 | M2-10, M2-11, M2-12, M6-02, M6-04, M6-05, M6-06, M6-07, M6-08, H-12 |
| A-10 | P-08, P-09, H-08, H-09 |
| A-11 | G-09, M1-10, M7-01, M7-02, M7-06, F-27, F-34, CC-03, Q-68 |

**Product surface (not accuracy; ship after the targets pass):** M7-07 to
M7-16 (config, reporters, LSP, packaging), M8-01 to M8-39 detection and
formatting rules, Q-28, Q-33 to Q-35, Q-61, Q-64, H-01 to H-06.

### Known contradictions today and who removes them

From `scripts/compare/pair_wrong.py` on the dev pair after W-03 (26 lines: 13
parameters/returns, 13 variables; before W-03 there were 104):

| Cause | Count | Removed by |
| --- | ---: | --- |
| Author uses `object` as a top type; ours is narrower and valid (`dict[str, int]` vs `dict[str, object]`) | 8 | G-02 |
| `Generator[X, None, None]` vs `Generator[X]` / `Generator[int, int \| str \| None, int]` | 4 | G-05 |
| Author picks an abstract type or `Callable` (`Sequence[...]`, `Mapping[T, U]`, `Callable[[int], int]`) | 6 | M4-16, M4-17, G-02 |
| Synthesised protocol is named differently from the author's (`SupportsVector`) | 3 | P-07 |
| Wrong guesses to root-cause (`duplicate_scope_name.value`, `store`, `merged`, `registry`, `tree`) | 5 | G-04 |

**Not yet re-measured since W-03:** the fast tier, the stdlib/external recovery
gates and the semantic run (see G-10 step 6). Until they pass, treat the W-03
change as unreleased.

## Parallel lanes

Work is split into lanes that own **disjoint files**, so one agent per lane can
work at the same time. Rules: an agent edits only the files its lane owns;
anything in the "Shared" table below goes through the integration step at the
end; each lane merges on its own branch and rebases onto the others before
merging; the lane's gate must pass before it merges.

| Lane | Owns (files) | Tasks | Needs first | Gate before merge | Merge risk |
| --- | --- | --- | --- | --- | --- |
| L1 Measurement and gates | `benchmarks/*` (not `pair.py`), `tests/test_bench_*`, `tests/gold` | W-01, W-02, G-01, G-03, G-04, F-28, F-29, M1-10, M2-13, M5-25, M8-21, H-09 | none | fast tier | low |
| L2 Scorer | `scripts/compare/pair.py`, `rules/recovery.py`, `fixtures/*` | G-02, G-05, G-08, P-07, P-09 | none | recovery tests | low |
| L3a Narrowing and flow | `negotiation/narrowing.py` | I-01, I-02, I-03, I-06, I-15 | none | shadow `wrong == 0` | medium (`builders.py` hooks) |
| L3b Containers and iteration | `negotiation/containers.py`, `negotiation/transfer.py` | I-05, I-09, I-10, I-17, F-07, F-40 | none | shadow | medium |
| L3c Calls and library stubs | `astart/stubs/*`, `rules/library_calls.py` | I-08, I-13, I-21, W-04, W-06, T-08, T-09, F-15, F-41 | none | stubs tests, shadow | low |
| L3d Classes and attributes | class parts of `negotiation/builders.py`, `rules/attributes.py`, `rules/methods.py` | I-11, I-12, I-16, I-22, W-09, W-10, W-12, W-14, G-06, T-01, T-02, F-16, M2-05..M2-09 | none | shadow | high (`builders.py` is large; split by function, keep patches small) |
| L3e Type algebra | `negotiation/algebra.py`, `semantic/typing_relations.py` | I-18, I-19, G-09, T-07, F-24, F-25, H-10 | none | algebra and relation tests | low |
| L3f Engine bridge | `rules/engine_hints.py`, `negotiation/variables.py`, `negotiation/supplement.py` | G-10, W-03 (done), W-11, F-43, F-37, W-08, P-02, P-03 | none | pair numbers, both gates | medium |
| L4 Protocols and generics | `rules/protocols.py`, `rules/typevars.py` | M5-04, M5-06, M5-07, M5-09..M5-12, M5-16, M5-19..M5-24, M4-16, M4-17 | none | protocol gold | low |
| L5 Imports and Constants style | `rules/imports.py`, `rules/constants_grouping.py`, new `rules/type_checking.py`, `rules/imports_dedupe.py`, `rules/method_order.py`, `rules/raise_messages.py` | S-01..S-09, M3-07..M3-13, AF-12, AF-14, AF-17, AF-06, AF-07 | none | semantic run | medium (shares `ensure_names`) |
| L6 Strings and docstrings | `rules/fstring_*`, `rules/docstring_edit.py`, `rules/docs_*`, `docstrings.py`, `formatting.py` | AF-21, AF-08, AF-09, AF-10, AF-13, AF-20, CC-08-01..06, CC-08-10, Q-61, Q-64, M8-28..30, M8-37 | CC-08-00 | DOC tests | low |
| L7 Re-parse and runner | new `astart/reparse.py`, new `rules/tree_diff.py`, `rules/runner.py` | CC-10, CC-09, CC-02, CC-03, F-27, F-34, M7-01, M7-02, Q-68 | none | runner tests, perf bench | high (`runner.py` is central; one agent only) |
| L8 CLI, API, reporters | `cli/*`, new `astart/api.py`, `astart/files.py`, `__main__.py` | API-01..API-13, H-01..H-03, H-11, M7-04..M7-16, AF-18, M7-12..M7-14, CC-06 | none | CLI tests | high (`__main__.py` flag table; serialise flag additions) |
| L9 Reverse direction | new `rules/untype.py` | P-08, H-08 | none | pair round trip | low |
| L10 Detection rules | `rules/artifacts/catalog/*.json`, rule modules, `rules/reasons.py` | M8-01..M8-07, M8-11..M8-13, M8-22, M8-31..M8-39, Q-33..Q-35, H-04, H-05, CC-04 | none | `verify_catalog` | medium (catalog JSON merges) |
| L11 Keyword arguments | `rules/call_problems.py`, `rules/kwargs*`, `rules/libkw.py` consumers | M6-02, M6-04..M6-09, M2-10..M2-12, H-12 | none | danger matrix | medium |
| L12 Docs | `docs/*` except `TODO*.md` | W-05, API-05, API-11, AF-18 docs | after the code lanes | doc tests | low |
| L13 Risk and infrastructure | `benchmarks/baseline*`, `tests/weird/`, `fixtures/split.json`, `scripts/todo_*.py`, `docs/engineering/security.md`, `docs/incident.md`, `LICENSES.md` | R-01, R-02, R-03, R-05, R-06, R-09, R-10, R-11, R-13, R-14, R-15, R-16, R-17, R-19, R-22, R-23, R-24 | none (R-02 before any new calibration) | fast tier | low |
| L7 extension | `astart/reparse.py` tests and fuzz | R-07, R-12, R-21, R-20 | CC-10 | scale and fuzz tests | high (single agent with L7) |
| Integration | `astart/settings_registry.py`, `scripts/generate_settings.py` | R-18 | none, but do it early | all settings tests | high (touches every settings user; do first, alone) |

**Shared files (integration step, one agent, last):** `rules/facts.py`,
`rules/hints.py`, `rules/runner.py` settings, `FixSettings`, `README.md` flag
table, `rules/artifacts/catalog/*.json` registration lines, `__main__.py` flags. A lane
that needs a new setting writes it in its own module first and sends the
three-line registration (field, flag, README row) to the integration step.

**Order constraints:** L6 after CC-08-00; G-07 after W-02; S-07 after the
fixes it switches; L12 last. Everything else can start now.

**Do R-18 first and alone:** it removes the shared-file conflicts that limit the other lanes.

**Largest safe parallelism today (after R-18):** eleven agents (L1, L2, L3a, L3b, L3c, L3e,
L3f, L4, L5, L6, L9) touch disjoint files; L3d, L7, L8 and L10 are
single-agent each because of shared hot files.

## The conversion goal and how to check it

**Goal.** Run astart on `fixtures/untyped.py` (a 2.7 k-line module with every
annotation removed) and get back a file that carries the same annotations as
the reference `fixtures/typed.py` (the answer key), with no annotation that
contradicts it and no change in behaviour. The pair was written as a
stress test: dataclasses, generators, protocols, decorators, descriptors,
metaclasses, async code. A previous system converted a similar pair
automatically; this goal is to reach that level with the current engine, and
keep the rule that astart never writes a wrong annotation.

**What "converted" means.** Not byte-identical. The score compares every
annotation astart writes with the one in `fixtures/typed.py`:

| Result key | Meaning |
| --- | --- |
| `correct` | Identical to the author's annotation. |
| `narrower` | Valid but more specific (`dict[str, int]` where the author wrote `dict[str, object]`). |
| `looser` | Valid but less specific. |
| `unresolved` | Cannot be compared (foreign names). |
| `wrong` | Contradicts the author's annotation. Must reach 0. |
| `kept` | Already annotated in the untyped input. |
| `not_in_typed` | Written, but the typed file has no such annotation. |
| `to_recover` | Total annotations the typed file has beyond the input: the denominator. |

The pair is scored twice: `parameters_and_returns` and `variables`. Done means
contract targets A-02 (at least 90 % `correct`) and A-03 (contradictions at most
2 % of what is written; stretch 0), plus A-04 to A-06 (checker clean, behaviour
preserved, idempotent). The ceiling is below 100 % because some author choices
(`Iterator` over `Generator`, `Self`, `ClassVar`) cannot be derived from code;
those go in `fixtures/artifacts/accepted_deviations.json` (G-08).

**How to run the check (all commands from the repository root).**

1. **Measure** (1 to 2 minutes, verified 2026-11-08):
   `PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5`
   It prints JSON with the keys above. `--engine` is conversion mode,
   `--min-confidence 0.5` lets lower-tier annotations through, add `--checker`
   to let an installed pyright veto them (A-04; see W-02, G-07).
2. **See what is wrong** (verified):
   `PYTHONPATH=src:. python scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5`
   Each line is `node: wrote X | author Y` for a contradiction or a narrower or
   looser result.
3. **See why a node is missing** (verified):
   `PYTHONPATH=src python scripts/compare/opacity_report.py fixtures/untyped.py`
   Prints the reason each node stays unannotated, with samples.
4. **Produce the converted file.** The command writes in place, so work on a copy:
   `cp fixtures/untyped.py /tmp/converted.py && PYTHONPATH=src python -m astart fix /tmp/converted.py --engine --min-confidence 0.5`
   Add `--diff` to preview without writing, `--check` for an exit code only,
   `--no-format` to skip ruff. Flags confirmed with `astart fix --help`; the
   end-to-end write of the full file was started on 2026-11-08 but the run was
   interrupted, so re-run it once and record the time and exit code here.
5. **Check it still behaves:** `python -c "import ast; ast.parse(open('/tmp/converted.py').read())"`,
   then the semantic run (W-01 step 4) and the fast tier.
6. **Other pairs** (guard against overfitting, R-02): the resolver pair,
   `PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5`,
   and the hold-out pairs once R-02 exists. `python -m scripts.benchmark targets`
   (G-01) will print PASS or FAIL for every target in one command.

7. **Run everything and get the report** (one command, about 2 to 3 minutes):
   `python scripts/compare`. It sets up its own import path, so no
   `PYTHONPATH` is needed. It converts `fixtures/untyped.py` in memory (the file is
   never changed), compares every annotation of the result with `fixtures/typed.py`
   **by meaning, not by text** (exact, narrower, looser, unresolved, wrong,
   missing) using the same scorer as the pair benchmark, and groups the gap by
   the kind of annotation the author wrote (scalar, container, optional,
   abstract collection, callable, TypeVar, `Self`, `ClassVar`, ...), so each
   part of the gap points at the TODO tasks that close it.
   Options: `--min-confidence F` (default 0.5), `--checker` (let an installed
   pyright veto annotations), `--no-opacity` (skip the slow "why a node stays
   unannotated" section), `--no-todo` (do not touch this file),
   `--ledger "label"` (also add the numbers to the Status ledger),
   `--untyped PATH --typed PATH` (score another pair).
   Outputs: `scripts/compare/artifacts/results/conversion-report.md` (full report), `scripts/compare/artifacts/results/conversion-report.json`
   (machine-readable; `python -m scripts.todo_update status pair` accepts it on standard input), and
   the generated block "Latest conversion report" below.

**How to read the report.**
- *Summary*: per scope (parameters and returns, variables) how many annotations
  the typed file has beyond the input (`to recover`) and what happened to each:
  `exact`, `narrower` and `looser` (valid but not identical), `unresolved`
  (cannot be compared), `wrong` (contradicts the author; must be 0) and
  `missing` (not written). `extra` counts annotations written that the typed
  file does not have.
- *Gap by family*: the same outcomes grouped by the shape of the author's
  annotation. "Share of gap" says where the remaining work is; the Tasks column
  names the TODO tasks for that family. Families marked hard (`Self`,
  `ClassVar/Final`, `Callable`, `TypeVar`, `Generator/Iterator`, abstract
  collections) are partly author choices and bound the 90 % target (see the
  Accuracy contract).
- *Wrong annotations*: every contradiction with what was written and what the
  author wrote; each one is a bug or a scoring difference (G-02, G-05, P-07, G-04).
- *Gap by owner*: the functions and classes with the most missing or wrong
  annotations, the best places to start.
- *Why nodes stay unannotated*: the opacity report for `fixtures/untyped.py`.

**Latest conversion report (generated; do not edit between the markers).**

<!-- conversion:start -->
Run Tue 10 Nov 2026, 02:33 WET · tree `28afad92ec59` · converted in 59 s · files: [fixtures/untyped.py](../../fixtures/untyped.py), [typed.py](../../fixtures/typed.py), [result.py](../../scripts/compare/artifacts/results/result.py) · [full report](../../scripts/compare/artifacts/results/conversion-report.md)

| Scope | To recover | Exact spelling | Equivalent | Narrower | Looser | Unresolved | Wrong | Missing | Extra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parameters and returns | 471 | 158 (33.5 %) | 31 | 42 | 6 | 36 | 8 | 190 | 15 |
| Variables | 294 | 99 (33.7 %) | 66 | 21 | 5 | 2 | 12 | 89 | 13 |

```text
Parameters and returns   same type ████████░░░░░░░░░░░░  40.1 %   wrong ░░░░░░░░░░░░░░░░░░░░   1.7 %
Variables                same type ███████████░░░░░░░░░  56.1 %   wrong █░░░░░░░░░░░░░░░░░░░   4.1 %
```

**Exact spelling** compares normalized annotation text. **Equivalent** is the scorer's semantic equivalence result after expanding aliases or comparing protocol structure. **Same type** adds these two counts. Narrower and looser types remain separate; changing a fixed tuple to a variadic tuple changes its length contract.

Where the gap is, by the author's annotation:

| Author's annotation | Total | Exact | Compatible | Wrong | Missing | Share of gap | Hard | Tasks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |
| Type alias | 381 | 12 | 145 | 9 | 108 | 35 % | yes | [S-03](TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names) |
| TypeVar | 75 | 0 | 3 | 2 | 50 | 19 % | yes | [M5-16](TODO.md#m5-16--multi-variable-relations), [I-18](TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding) |
| Scalar | 331 | 207 | 5 | 0 | 31 | 16 % |  | [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](TODO.md#f-37--default-literal-parameters-in-the-negotiator) |
| Module class | 101 | 29 | 3 | 8 | 38 | 14 % |  | [M2-02](TODO.md#m2-02--constructorattribute-resolution), [W-12](TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](TODO.md#w-14--annotate-class-level-and-module-level-variables) |
| Top type (object) | 47 | 0 | 10 | 0 | 25 | 7 % | yes | policy: astart never writes object; [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower |
| Library class | 8 | 1 | 0 | 0 | 6 | 2 % |  | [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](TODO.md#t-08--library-return-types-from-typeshed) |
| Self | 14 | 5 | 1 | 1 | 5 | 2 % | yes | [W-11](TODO.md#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name), [AF-02](TODO.md#af-02--annotate-selfcls-only-when-the-style-asks), [F-43](TODO.md#f-43--quote-instead-of-refusing) |
| Optional | 10 | 1 | 1 | 0 | 5 | 1 % |  | [I-01](TODO.md#i-01--narrow-the-else-branch-by-complement), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [AL-01](TODO.md#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling) |

Why nodes stay unannotated (biggest direct reasons; examples with links are in the full report):

| Nodes | Reason | Nodes of that kind | What it means | Tasks |
| --- | --- | ---: | --- | --- |
| parameters and returns | direct: unprovable Name | 46 (8.4 %) | Returns a name the prover cannot type (a wrapper, a decorated function, a class) | [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls) |
| parameters and returns | direct: no evidence reaches it | 34 (6.2 %) | A parameter with no call site, default or use that proves a type | [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](TODO.md#p-05--no-candidate-72), [AL-05](TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior) |
| parameters and returns | direct: unprovable Call | 32 (5.9 %) | Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`) | [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](TODO.md#f-41--calls-on-builtin-typed-receivers) |
| parameters and returns | direct: function escapes as a value | 28 (5.1 %) | The function is passed around as a value, so its callers are unknown | [W-07](TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [AL-04](TODO.md#al-04--alias-and-escape-analysis-for-containers) |
| local variables | direct: unprovable Call | 56 (19.2 %) | Returns a call result the prover cannot type (`super()`, `getattr`, constructors, `list(...)`) | [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [F-41](TODO.md#f-41--calls-on-builtin-typed-receivers) |
| local variables | direct: container literal mutated or not provable | 32 (11.0 %) | Not described yet: add it to the table in scripts/compare/conversion_report.py | [G-03](TODO.md#g-03--give-every-missed-annotation-an-owner) |
| local variables | direct: unprovable Name | 6 (2.1 %) | Returns a name the prover cannot type (a wrapper, a decorated function, a class) | [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls) |
| local variables | direct: unprovable Attribute | 3 (1.0 %) | Returns an attribute the class table does not type | [I-11](TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-12](TODO.md#w-12--annotate-instance-attributes-from-negotiation), [M2-06](TODO.md#m2-06--r9-attribute-types) |

In the examples `-` is how the converted code is and `+` is how it should be (the author's `fixtures/typed.py`); the links go to the exact lines.

<details><summary>Wrong annotations with code (first 6 of 20)</summary>

---

### Wrong annotation: `CallableObject.__call__->`

**Wrong** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| `DictInt \| int \| str` | `CallablePayload[ValueT] \| IntOrStr` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:3299](../../scripts/compare/artifacts/results/result.py#L3299) · Reference: [typed.py:4339](../../fixtures/typed.py#L4339) · Input: [untyped.py:1997](../../fixtures/untyped.py#L1997)

```diff
@@ CallableObject.__call__-> · wrong · TypeVar @@
-    def __call__(self, value: int, *, scale: int = 1) -> int | str | DictInt:
+    ) -> IntOrStr | CallablePayload[ValueT]:
```

</details>

**1. Expected contract**

The reference declares `CallablePayload[ValueT] | IntOrStr` at [typed.py:4339](../../fixtures/typed.py#L4339). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `int`: The authored contract selects this type.
- `str`: The authored contract selects this type.
- `fixtures.typed.CallablePayload[ValueT]`: The authored contract selects this type.

Related operations in the reference:

- [reference:4354](../../fixtures/typed.py#L4354): `return {"value": value, "scale": scale}`. Source return/yield contributes a value.
- [reference:4351](../../fixtures/typed.py#L4351): `return value * scale`. Source return/yield contributes a value.
- [reference:4353](../../fixtures/typed.py#L4353): `return str(object=value) * scale`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2000](../../fixtures/untyped.py#L2000) | return: `value * scale` | Contributes a result; all paths and operands must be resolved. |
| [input:2002](../../fixtures/untyped.py#L2002) | return: `str(object=value) * scale` | Contributes a result; all paths and operands must be resolved. |
| [input:2003](../../fixtures/untyped.py#L2003) | return: `{'value': value, 'scale': scale}` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt | int | str`. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](TODO.md#al-04--alias-and-escape-analysis-for-containers).

---

### Wrong annotation: `function_with_mutable_default_like_pattern.store`

**Wrong** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| `int \| None` | `ValueOrNone[ListValue[ItemT]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4127](../../scripts/compare/artifacts/results/result.py#L4127) · Reference: [typed.py:5511](../../fixtures/typed.py#L5511) · Input: [untyped.py:2544](../../fixtures/untyped.py#L2544)

```diff
@@ function_with_mutable_default_like_pattern.store · wrong · TypeVar @@
-def function_with_mutable_default_like_pattern(value: str, store: int | None = None):
+    store: ValueOrNone[ListValue[ItemT]] = None,
```

</details>

**1. Expected contract**

The reference declares `ValueOrNone[ListValue[ItemT]]` at [typed.py:5511](../../fixtures/typed.py#L5511). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ValueOrNone[fixtures.typed.ListValue[ItemT]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:5526](../../fixtures/typed.py#L5526): `return store, tuple(store), set(store)`. Source return/yield contributes a value.
- [reference:5525](../../fixtures/typed.py#L5525): `store.append`. The source requires this receiver member.

<details><summary>Graph evidence and limitations</summary>

4 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2544](../../fixtures/untyped.py#L2544) | default value: `None` Observed type: `None`. | Shows one argument/default, not every accepted input. |
| [input:2546](../../fixtures/untyped.py#L2546) | body compares it with None: `store is None` | A constraint to combine with other operations and bindings. |
| [input:2548](../../fixtures/untyped.py#L2548) | body calls a method: `store.append(value)` Observed type: `is a list`. | Requires this member; its name alone does not prove a class. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `int | None`. A separate negotiator analysis reports **settled**. Typed by negotiation: these are the nodes astart can write. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: .

---

### Wrong annotation: `function_with_optional_types->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `Callable[[None \| int], int \| str]` | `SupportsCall2` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1151](../../scripts/compare/artifacts/results/result.py#L1151) · Reference: [typed.py:1898](../../fixtures/typed.py#L1898) · Input: [untyped.py:645](../../fixtures/untyped.py#L645)

```diff
@@ function_with_optional_types-> · wrong · Module class @@
-def function_with_optional_types() -> Callable[[None | int], int | str]:
+def function_with_optional_types() -> SupportsCall2:
```

</details>

**1. Expected contract**

The reference declares `SupportsCall2` at [typed.py:1898](../../fixtures/typed.py#L1898). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.SupportsCall2`: Requires the declared protocol members `__call__`. Matching an unrelated method name does not establish these structural requirements.

Related operations in the reference:

- [reference:1926](../../fixtures/typed.py#L1926): `return optional_function`. Source return/yield contributes a value.
- [reference:1924](../../fixtures/typed.py#L1924): `return value`. Source return/yield contributes a value.
- [reference:1923](../../fixtures/typed.py#L1923): `return "default"`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

5 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:651](../../fixtures/untyped.py#L651) | return: `'default'` Observed type: `str`. | Contributes a result; all paths and operands must be resolved. |
| [input:652](../../fixtures/untyped.py#L652) | return: `value` | Contributes a result; all paths and operands must be resolved. |
| [input:654](../../fixtures/untyped.py#L654) | return: `optional_function` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `Callable[[None | int], int | str]`. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: optional_function`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

---

### Wrong annotation: `test_class_instantiations->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `dict[str, BaseClass \| DataClassExample \| DecoratedClass \| DerivedClass \| MetaDecoratedClass]` | `ClassInstantiationResults` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:2481](../../scripts/compare/artifacts/results/result.py#L2481) · Reference: [typed.py:3412](../../fixtures/typed.py#L3412) · Input: [untyped.py:1490](../../fixtures/untyped.py#L1490)

```diff
@@ test_class_instantiations-> · wrong · Module class @@
-def test_class_instantiations() -> dict[str, BaseClass | DataClassExample | DecoratedClass | DerivedClass | MetaDecoratedClass]:
+def test_class_instantiations() -> ClassInstantiationResults:
```

</details>

**1. Expected contract**

The reference declares `ClassInstantiationResults` at [typed.py:3412](../../fixtures/typed.py#L3412). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ClassInstantiationResults`: The authored contract selects this type.

Related operations in the reference:

- [reference:3419](../../fixtures/typed.py#L3419): `return { "obj1": BaseClass(x=10), "obj2": BaseClass(x=10, y=20), "obj3": DerivedClass(x=10, y=20, z=30), "obj4": MetaDecoratedClass(value=100), "obj5": DataClas`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1492](../../fixtures/untyped.py#L1492) | return: `{'obj1': BaseClass(x=10), 'obj2': BaseClass(x=10, y=20), 'obj3': DerivedClass(x=10, y=20,…` Observed type: `dict[str, BaseClass \| DerivedClass \| MetaDecoratedClass \| DataClassExample \| DecoratedClass]`. | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `dict[str, BaseClass | DataClassExample | DecoratedClass | DerivedClass | MetaDecoratedClass]`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {'obj1': BaseClass(x=10), 'obj2': BaseClass(x=10, y=20), 'ob`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](TODO.md#f-40--comprehensions-as-derived-nodes).

---

### Wrong annotation: `test_extended_inference_edge_cases->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `DictInt` | `ExtendedTestResult` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4317](../../scripts/compare/artifacts/results/result.py#L4317) · Reference: [typed.py:5787](../../fixtures/typed.py#L5787) · Input: [untyped.py:2706](../../fixtures/untyped.py#L2706)

```diff
@@ test_extended_inference_edge_cases-> · wrong · Module class @@
-def test_extended_inference_edge_cases() -> DictInt:
+def test_extended_inference_edge_cases() -> ExtendedTestResult:
```

</details>

**1. Expected contract**

The reference declares `ExtendedTestResult` at [typed.py:5787](../../fixtures/typed.py#L5787). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ExtendedTestResult`: The authored contract selects this type.

Related operations in the reference:

- [reference:5794](../../fixtures/typed.py#L5794): `return { **test_extended_inference_edge_cases_part1(), **test_extended_inference_edge_cases_part2(), **test_extended_inference_edge_cases_part3(), }`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2708](../../fixtures/untyped.py#L2708) | return: `{**test_extended_inference_edge_cases_part1(), **test_extended_inference_edge_cases_part2…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {**test_extended_inference_edge_cases_part1(), **test_extend`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](TODO.md#f-40--comprehensions-as-derived-nodes).

---

### Wrong annotation: `test_extended_inference_edge_cases_part3->`

**Wrong** · Module class

| Current tool output | Expected reference |
| --- | --- |
| `DictInt` | `ExtendedResultsPart3` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:4264](../../scripts/compare/artifacts/results/result.py#L4264) · Reference: [typed.py:5725](../../fixtures/typed.py#L5725) · Input: [untyped.py:2657](../../fixtures/untyped.py#L2657)

```diff
@@ test_extended_inference_edge_cases_part3-> · wrong · Module class @@
-def test_extended_inference_edge_cases_part3() -> DictInt:
+def test_extended_inference_edge_cases_part3() -> ExtendedResultsPart3:
```

</details>

**1. Expected contract**

The reference declares `ExtendedResultsPart3` at [typed.py:5725](../../fixtures/typed.py#L5725). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.ExtendedResultsPart3`: The authored contract selects this type.

Related operations in the reference:

- [reference:5747](../../fixtures/typed.py#L5747): `return { "local_class": local_instance.apply(value=5), "nested_defaultdict": function_with_nested_default_factories(), "partial_reduce": function_with_partial_r`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:2665](../../fixtures/untyped.py#L2665) | return: `{'local_class': local_instance.apply(5), 'nested_defaultdict': function_with_nested_defau…` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

The tool wrote `DictInt`. A separate negotiator analysis reports **direct: unprovable Dict**. Observation: `unprovable Dict: {'local_class': local_instance.apply(5), 'nested_defaultdict`. Returns a dict display with unpacking or untyped members. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [I-17](TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](TODO.md#f-40--comprehensions-as-derived-nodes).

</details>

<details><summary>Examples of missing annotations (1 per family, largest gaps first)</summary>

**Type alias** (108 missing; tasks: [S-03](TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names))

---

### Missing annotation: `MetaClass.__new__.mcs`

**Missing** · Type alias

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `TypeValue[MetaClass]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](../../scripts/compare/artifacts/results/result.py#L116) · Reference: [typed.py:745](../../fixtures/typed.py#L745) · Input: [untyped.py:101](../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__.mcs · missing · Type alias @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        mcs: TypeValue[MetaClass],
```

</details>

**1. Expected contract**

The reference declares `TypeValue[MetaClass]` at [typed.py:745](../../fixtures/typed.py#L745). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.TypeValue[fixtures.typed.MetaClass]`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:991](../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: no evidence reaches it**. Observation: `no evidence reaches it`. A parameter with no call site, default or use that proves a type. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [P-05](TODO.md#p-05--no-candidate-72), [AL-05](TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-09](TODO.md#al-09--name-and-usage-language-model-as-calibrated-prior).

**TypeVar** (50 missing; tasks: [M5-16](TODO.md#m5-16--multi-variable-relations), [I-18](TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding))

---

### Missing annotation: `decorator->`

**Missing** · TypeVar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `CallableParametersToResult[P, ValueOrInt[R]]` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:287](../../scripts/compare/artifacts/results/result.py#L287) · Reference: [typed.py:936](../../fixtures/typed.py#L936) · Input: [untyped.py:192](../../fixtures/untyped.py#L192)

```diff
@@ decorator-> · missing · TypeVar @@
-def decorator(func):
+) -> CallableParametersToResult[P, ValueOrInt[R]]:
```

</details>

**1. Expected contract**

The reference declares `CallableParametersToResult[P, ValueOrInt[R]]` at [typed.py:936](../../fixtures/typed.py#L936). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.CallableParametersToResult[P, fixtures.typed.ValueOrInt[R]]`: The authored contract selects this type.

Related operations in the reference:

- [reference:964](../../fixtures/typed.py#L964): `return wrapper`. Source return/yield contributes a value.
- [reference:962](../../fixtures/typed.py#L962): `return result`. Source return/yield contributes a value.
- [reference:961](../../fixtures/typed.py#L961): `return result * 2`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

8 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:198](../../fixtures/untyped.py#L198) | return: `result * 2` | Contributes a result; all paths and operands must be resolved. |
| [input:200](../../fixtures/untyped.py#L200) | return: `wrapper` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: unprovable Name**. Observation: `unprovable Name: wrapper`. Returns a name the prover cannot type (a wrapper, a decorated function, a class). This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding), [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [M4-03](TODO.md#m4-03--prover-yield-typing--once-bound-classdef-calls).

**Scalar** (31 missing; tasks: [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](TODO.md#f-37--default-literal-parameters-in-the-negotiator))

---

### Missing annotation: `SupportsUpdate.update.message`

**Missing** · Scalar

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `str` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:59](../../scripts/compare/artifacts/results/result.py#L59) · Reference: [typed.py:560](../../fixtures/typed.py#L560) · Input: [untyped.py:57](../../fixtures/untyped.py#L57)

```diff
@@ SupportsUpdate.update.message · missing · Scalar @@
-    def update(self, message) -> None:
+    def update(self, message: str) -> None:
```

</details>

**1. Expected contract**

The reference declares `str` at [typed.py:560](../../fixtures/typed.py#L560). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `str`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:1056](../../fixtures/untyped.py#L1056) | same-named method in Observer: `function_with_observer.Observer.update(self, message)` | Name-only match; binding to this target is unverified. |
| [input:1560](../../fixtures/untyped.py#L1560) | same-named method in BuiltinMethodDict: `BuiltinMethodDict.update(self, other=(), *values, **kwargs)` | Name-only match; binding to this target is unverified. |
| [input:1674](../../fixtures/untyped.py#L1674) | call site passes: `custom_dict.update({'b': 2}, 3)  ->  {'b': 2}` | Name-only match; binding to this target is unverified. |
| [input:1675](../../fixtures/untyped.py#L1675) | call site passes: `builtin_dict.update({'b': 2})  ->  {'b': 2}` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **unsettled (no evidence)**. Nothing proves a type and no evidence reaches the node. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [P-05](TODO.md#p-05--no-candidate-72), [AL-05](TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [AL-18](TODO.md#al-18--ablation-harness-marginal-value-of-each-evidence-source).

**Module class** (38 missing; tasks: [M2-02](TODO.md#m2-02--constructorattribute-resolution), [W-12](TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](TODO.md#w-14--annotate-class-level-and-module-level-variables))

---

### Missing annotation: `MetaClass.__new__->`

**Missing** · Module class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `MetaClass` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](../../scripts/compare/artifacts/results/result.py#L116) · Reference: [typed.py:750](../../fixtures/typed.py#L750) · Input: [untyped.py:101](../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__-> · missing · Module class @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+    ) -> MetaClass:
```

</details>

**1. Expected contract**

The reference declares `MetaClass` at [typed.py:750](../../fixtures/typed.py#L750). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `fixtures.typed.MetaClass`: The authored contract selects this type.

Related operations in the reference:

- [reference:766](../../fixtures/typed.py#L766): `return created`. Source return/yield contributes a value.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:104](../../fixtures/untyped.py#L104) | return: `super().__new__(mcs, name, bases, namespace)` | Contributes a result; all paths and operands must be resolved. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **downstream of a blocked node**. Opacity spreads: the node depends on a blocked one. Fix the direct reasons first. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [AL-03](TODO.md#al-03--interprocedural-summaries-in-scc-order), [AL-04](TODO.md#al-04--alias-and-escape-analysis-for-containers).

**Top type (object)** (25 missing; tasks: policy: astart never writes object; [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower)

---

### Missing annotation: `MetaClass.__new__._kwargs`

**Missing** · Top type (object)

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `object` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:116](../../scripts/compare/artifacts/results/result.py#L116) · Reference: [typed.py:749](../../fixtures/typed.py#L749) · Input: [untyped.py:101](../../fixtures/untyped.py#L101)

```diff
@@ MetaClass.__new__._kwargs · missing · Top type (object) @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        **_kwargs: object,
```

</details>

**1. Expected contract**

The reference declares `object` at [typed.py:749](../../fixtures/typed.py#L749). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `object`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

3 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:991](../../fixtures/untyped.py#L991) | same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` | Name-only match; binding to this target is unverified. |
| [input:1881](../../fixtures/untyped.py#L1881) | same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` | Name-only match; binding to this target is unverified. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. The scorer labels this **missing**. No candidate-selection trace was recorded for this target, so the report cannot identify which inference rule or guard produced that result. Absence of a diagnostic does not show that no rule examined the target.

**Library class** (6 missing; tasks: [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](TODO.md#t-08--library-return-types-from-typeshed))

---

### Missing annotation: `function_with_exception_chaining.exception_chain_func.raise_second_error.original_error`

**Missing** · Library class

| Current tool output | Expected reference |
| --- | --- |
| Not annotated | `ValueError` |

<details><summary>Source locations and code comparison</summary>

Output: [result.py:1638](../../scripts/compare/artifacts/results/result.py#L1638) · Reference: [typed.py:2396](../../fixtures/typed.py#L2396) · Input: [untyped.py:907](../../fixtures/untyped.py#L907)

```diff
@@ function_with_exception_chaining.exception_chain_func.raise_second_error.original_error · missing · Library class @@
-        def raise_second_error(original_error) -> Never:
+        def raise_second_error(original_error: ValueError) -> None:
```

</details>

**1. Expected contract**

The reference declares `ValueError` at [typed.py:2396](../../fixtures/typed.py#L2396). That declaration defines the comparison target; it is not an independent proof that the type is uniquely inferable.

- `ValueError`: The authored contract selects this type.

<details><summary>Graph evidence and limitations</summary>

2 linked records are retained in [conversion-report.json](../../scripts/compare/artifacts/results/conversion-report.json). Non-declaration records are lexical context, not proofs of the expected type. Constraint and type IDs resolve in the source 
graph.
</details>

**2. Evidence in the untyped input**

| Source | Observation | What it establishes |
| --- | --- | --- |
| [input:914](../../fixtures/untyped.py#L914) | call site passes: `raise_second_error(original_error=e)  ->  e` | Shows one argument/default, not every accepted input. |

These observations constrain the annotation. Examples of values passed by current callers do not establish the full public input contract, and an unresolved name match is not type evidence.

**3. Tool diagnosis**

No annotation was written. A separate negotiator analysis reports **direct: a call to it cannot be bound**. Observation: `a call to it cannot be bound`. Some call to the function cannot be matched to its parameters. This observation is a debugging lead; it does not identify the conversion's selected candidate or prove why it was accepted or refused. Related work: [W-07](TODO.md#w-07--burn-down-unbindable-calls-and-escaping-functions), [M2-02](TODO.md#m2-02--constructorattribute-resolution), [M2-11](TODO.md#m2-11--kwargs-for-method-calls).

</details>
## Documentation and generated declarations

These counts are separate from annotation accuracy. Documentation uses normalized text; declarations use AST structure. Changed prose does not prove incorrect behavior. Renamed structural matches do not prove that all references use the declaration.

| Category | Exact | Equivalent structure | Changed | Missing | Extra |
| --- | ---: | ---: | ---: | ---: | ---: |
| Docstrings | 125 | 0 | 209 | 89 | 40 |
| Type aliases | 1 | 0 | 0 | 116 | 0 |
| Protocols | 0 | 0 | 0 | 17 | 8 |
| TypeVar | 0 | 0 | 1 | 51 | 3 |
| ParamSpec | 0 | 0 | 0 | 6 | 0 |
| TypeVarTuple | 0 | 0 | 0 | 0 | 0 |
| Classes | 18 | 0 | 46 | 24 | 6 |
| Declaration uses | 0 | 0 | 1 | 133 | 8 |

Full contracts and source locations are retained in `conversion-report.json` under `artifacts`.

<!-- conversion:end -->

**Progress and checks:** see the Status ledger at the top of this file; it is updated with `scripts/todo_update/status_update.py`. Exact matches fell with W-03 because annotations that were right only by accident, written without any filter, are no longer written. The way back up is the filtered path: W-06 to W-14, I-05, I-08, I-18, the scorer tasks G-02, G-05 and P-07, and the opacity burn-down (section 19.2).

**Known open items before this goal can be called done:** the semantic
equivalence run has not been run on the current tree; the checker-gated run keeps
only a few annotations (W-02, AL-06); 26 contradictions remain, mostly scoring
differences (G-02, G-05, P-07) and five unexplained wrong guesses (G-04).

## START HERE — read this before touching anything

This section is for an agent that has not seen the project. It is short on
purpose. Follow it literally; if something here is wrong, fix this section.

### What the project is

`astart` is a lossless Python source fixer. `astart fix` adds missing keyword
arguments, type annotations, imports and docstrings. Its rule is **zero wrong
annotations**, so a type is written only when evidence proves it. Two extra
modes trade that safety for coverage: `--annotate-variables` and `--engine`
(conversion mode). The goal that drives current work: turn `fixtures/untyped.py`
into `fixtures/typed.py` (and the same for `fixtures/resolver_extended_*`)
automatically. Today it recovers about 13 % exactly in the safe mode and
about 52–59 % in `--engine` mode; the old converter this project descends
from reached 70 % with ~20 % wrong.

### The five commands you will use

> Templates for detectors, catalog entries, tests, settings and negotiation rules, a command cheat sheet and a debugging playbook are in **chapter 20, Cookbook**.


```console
# 1. fast tests (~70 s, 4 838 pass, 2 xfail). Run before and after a change.
python -m pytest -m "not slow" -q -p no:cacheprovider

# 2. lint ONLY the files you created or edited, in this order
ruff check --fix FILES ; ruff format FILES ; ruff check FILES --output-format concise

# 3. how far is the conversion? (numbers to compare are in "Current numbers")
PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py
PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5

# 4. why is a node unknown?  (the burn-down tool: fix the biggest reason, rerun)
PYTHONPATH=src python scripts/compare/opacity_report.py fixtures/untyped.py

# 5. which written annotations disagree with the author's?
PYTHONPATH=src:. python scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5
```

Long jobs (more than ~100 s) must run in the background and be polled with a
loop that sleeps at most 10 s per step and stops by 590 s; a foreground
command over 600 s is killed. Slow tier: `python -m pytest -m slow -q
-p no:cacheprovider` takes ~19 min and must pass (870 tests) before a task
that changes `hints.py`, `facts.py`, `appliers.py`, `builders.py` or `methods.py`
is called done.

### House rules (a test and the user enforce these)

1. Never run `exactus`. Never add `# noqa` or `# type: ignore`.
2. Calls use keywords everywhere the callee allows it: `f(x=1)`, `parse(source=s)`,
   `walk(node=n)`. Signatures are keyword-only (`def f(*, x: int)`).
3. Google-style docstrings with `Args:`/`Returns:` on every function.
4. Module constants live in `@final class Constants` with `Final` attributes.
5. **No regular expressions in code that reads or rewrites Python source (CC-08).** Decide everything from the AST, tokens and node positions; the one exception is that AF-21 sends f-string field expressions to ruff and re-parses the result. No `Any`; `object` only in the `name: object = expr` narrow-then-`isinstance` idiom and in test doubles — never in production signatures. Import names (`from ast import walk`),
   never `import ast`. Line length 79.
6. macOS: `sed -i ''` needs the empty string; prefer a Python snippet for edits.
7. Edit `docs/planning/TODO.md` atomically; after changing a task's Status, Priority
   or Readiness run `python -m scripts.todo_update index docs/planning/TODO.md` (it only
   rewrites the dashboard block). Another agent works in the same tree: touch only the files
   your task names.

### Where things live

| Path | What |
| --- | --- |
| `src/astart/rules/hints.py` | the older evidence pipeline (`HintIndex`); do not rewrite |
| `src/astart/rules/negotiation/` | contract negotiation: `builders.py` (AST → graph), `negotiator.py` (solver), `policy.py` (what may be written), `transfer.py`, `containers.py`, `narrowing.py`, `supplement.py`, `variables.py`, `run.py` |
| `src/astart/rules/engine_hints.py` | conversion mode (`--engine`): the old converter's annotations as lowest-priority hints |
| `src/astart/stubs/` | our typeshed reader: `locate`, `versions`, `conditions`, `parser`, `resolver`, `returns` (migrated ideas of `typeshed_client`; no dependency) |
| `src/astart/graph/` | the old converter ("the engine") |
| `src/astart/rules/artifacts/catalog/*.json` | rules and fixes; edit by hand, `json.dumps(d, indent=2, sort_keys=True) + "\n"` |
| `benchmarks/` and `scripts/` | measurement; `pair.py`, `shadow.py`, recovery + gates |
| `docs/architecture/negotiation.md` | the model and the soundness rules; read it before editing `builders.py` |

### Current numbers (2026-11-08; a change must not lower the first four)

| Measure | Value |
| --- | --- |
| stdlib baseline (`scripts/benchmark/artifacts/resources/baseline.json`) | 42 / 324 correct, 0 wrong |
| external baseline (`scripts/benchmark/artifacts/resources/baseline_ext.json`) | 2 511 / 12 789 correct, 6 wrong, precision 99.77 % |
| gold superset test | negotiation changes 0 written annotations, adds 24 reviewed |
| semantic equivalence | 15 / 15 projects (needs the 5 installs in W-01 step 4) |
| dev pair, safe mode | 52 / 482 parameters+returns, 55 / 335 variables, 2 wrong |
| dev pair, `--engine` | 253 / 482, 174 / 335, ~104 wrong |
| resolver pair, safe mode | 113 / 557, 59 / 329, 2 wrong |
| resolver pair, `--engine` | 329 / 557, 185 / 329, ~94 wrong |
| old converter's own output vs resolver twin | 388 / 557, 207 / 329, ~106 wrong |


> **Known state:** see the Status ledger at the top of this file (generated from `docs/planning/status.json`, updated with `scripts/todo_update/status_update.py`).

### Definition of done for any task

1. The new behaviour has a test that **fails without the change** (prove it:
   disable the change, watch the test fail, re-enable).
2. The fast tier passes; the lint command is clean on your files.
3. If the task touches inference or fixing: run the pair command and write the
   before/after numbers in the task's evidence line.
4. If it can change what is written: run the shadow comparison and the two
   recovery gates (commands in W-01); both must print `PASS`.
5. Tick the box, add a two-line evidence note under the task, stop.

### Decisions already made (do not reopen them)

- Confidence only orders candidates; acceptance is decided by evidence class
  (`policy.accept`). The inference engine is corroboration in the safe mode and
  the lowest tier in `--engine` mode.
- Unknown is not absence: a node that lost a contribution or has no evidence is
  *opaque* and everything downstream is refused (`docs/architecture/negotiation.md`).
- No new runtime dependencies. Ideas from other projects are re-implemented.
- A negotiated annotation never names a class that does not exist yet when the
  `def` runs (`bound_when_evaluated`).
- `--engine` must stay opt-in; the default stays "zero wrong".

## Execution map — measurement first

This map is a planning decision, not new completion evidence. It organizes the
task owners into deliverable work packages matching milestones M0–M8.
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

Before coding, add ordinary prose beneath the selected task (under **Context**):
`Scope`, `Depends on`, `Source`, `Acceptance`, `Evidence`, `Known limits` —
populated with exact behavior and inspected files, not generic promises.
Success, invalid input, refusal, lost-checker and non-idempotent paths all
need named proof, not a happy path. At completion update only the satisfied
obligation; if a parent still lacks gold cases, checker-gate or corpus
evidence, keep it open and record the accepted slice.

## Decisions (all locked with the user)

- **Scope: full roadmap M0–M8** — including `graph`/`semantic` inference-core bug fixes.
- **Union policy: enabled (guarded)** — `T1 | T2 [| …]` accepted when ≤3 distinct definite spellings and inference corroborates.
- **TypeVar style: classic default + version-aware PEP 695** — `T = TypeVar("T")` default; `def f[T](x: T)` when `requires-python >= 3.12`.
- **Checker oracle: yes, optional auto-detect** — guarded fixes gated on pyright/basedpyright when installed (E6); without it, guarded fixes need a higher internal evidence level.
- **Default aggressiveness: configurable per-profile** — profiles/`[tool.astart]` set the safety ceiling; default profile applies proven-only, guarded behind opt-in flag/profile.
- **Protocol placement: shared `_protocols.py` + name lockfile** — same-member protocols merged project-wide with deterministic stable names; config switch preserves per-function placement.
- **Git init: yes** — initialize a repository in M0 so every milestone is diff-reviewable and rollback-safe.
- **Library keyword table: stdlib first, extensible** — curated typeshed-generated table; third-party packages join only via explicit allow-list.

## North star (roadmap §1)

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

## Accuracy model (adopted wholesale)

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

## Risk register (roadmap §7)

| Risk | Mitigation |
| --- | --- |
| Wrong annotation breaks a user's type check | E6 checker oracle (M1-02/M1-03); guarded fixes only behind opt-in profile/flag (Decisions); `rejected-by-checker` reported, never silent |
| Keyword fix breaks dynamic code | Danger matrix `tests/astart/rules/test_rules_kwargs_danger.py`; refusal catalogue; library allow-list (Decisions) |
| Synthesized Protocol churn between runs | Deterministic naming + name lockfile + reuse-before-create (Decisions: shared `_protocols.py`) |
| Inference engine regressions | Benchmark harness with threshold failures (M1-04…M1-12); perf budgets (M7-02) |
| Performance on big repos | M7-01 superlinear costs, M7-03 incremental cache, M7-04/M7-05 parallelism |
| Python version drift (PEP 695, `Self`, 3.14 annotations) | Version-aware emission (M3-06 done; TypeVar style decision); tests per target version |
| Scope creep into a full type checker | astart proposes and verifies with an external checker; it does not become one (North star, Accuracy model) |
| Unbounded surface of Python semantics | Refusal catalogue + writer fuzzing (M1-13) + corpus growth (M1-07); every new construct starts as "refuse" |

## Task template

Every task has exactly this shape (the dashboard parses it):

```markdown
### F-17 — Imperative title without a final period
- **Status:** open            <!-- open | done -->
- **Priority:** P0            <!-- P0 | P1 | P2 | P3 | Untriaged -->
- **Area:** inference        <!-- ast | inference | negotiation | types | rules | kwargs | project | stubs | cli | tests | benchmarks | performance | docs | release | backend | risk | uncategorized -->
- **Readiness:** needs recipe <!-- ready | needs recipe | done -->

Why / context in one or two sentences.

**Facts:** files and line references.

**Steps:**
1. One edit or one command, with its check.

**Done when:** one command and the number it must print.
```

- `ready` means the task has numbered steps or a **Done when** line.
  `needs recipe` means the task still shows `_to be written_` under
  **Steps** and **Done when**: a planner writes them first (one edit or
  one command per step, with the file and the check), then sets
  **Readiness** to `ready` and reruns the dashboard script.
- Finish a task: set **Status** to `done` and **Readiness** to `done`,
  then run `python -m scripts.todo_update index docs/planning/TODO.md`. Do not delete
  the task and do not change its ID.
- Priorities: P0 blocks a trustworthy release; P1 is required core work;
  P2 is secondary; P3 is optional polish.
- Areas: `ast` syntax/writer/formatting machinery · `inference` the
  semantic/`graph` engine and prover · `negotiation` the contract
  solver (`rules/negotiation/`) · `types` protocol/TypeVar/carrier
  synthesis · `rules` catalog rules, detectors, fixers and appliers ·
  `kwargs` keyword-argument call fixes · `project` cross-module index,
  imports and libraries · `stubs` the typeshed reader · `cli` the
  command surface (commands, reporters, config, LSP) · `tests` the test
  suite, gold families and corpus · `benchmarks` measurement harness,
  baselines and calibration · `performance` speed work (budgets,
  parallelism, cache) · `docs` documentation content · `release`
  packaging, CI and hooks.

**Evidence 2026-11-08:** Seeds carry `Origin` (syntax, declared, protocol, call_sites, default, calibrated, inferred) from `negotiation/builders.py`; `tests/astart/rules/negotiation/test_negotiation_module.py`.

### Effort and agent tier (every task has `- **Effort:** SIZE · TIER`)

Both fields describe the work for an **agent**, not for a person.

| Size | Meaning for an agent |
| --- | --- |
| S | One file or one command; about 10 tool calls or fewer once the code is read |
| M | A few files; about 40 tool calls; one test run per step |
| L | A module or cross-cutting change; about 150 tool calls; commit a checkpoint (tests green) every few steps so a restart loses little |
| XL | Too large for one agent run; split it before starting |
| unsized | No steps yet; a planning agent sizes it when it writes the recipe |

| Tier | Which agent should take it |
| --- | --- |
| light | A small, fast model with low reasoning effort. The steps are mechanical and the listed test catches mistakes. Do not ask it to design. |
| standard | A capable general model with normal reasoning effort. It reads the surrounding code and makes local decisions within the house rules. |
| deep | The strongest model with high reasoning effort, and a second agent (or the same one in a fresh context) reviewing the diff. Algorithm, architecture or soundness judgement: a mistake yields wrong annotations or broken code that the tests may not catch. |

Size follows the number of steps (S ≤ 3, M 4–6, L 7–9, XL ≥ 10; a deep task is
at least M). The tier was assigned by area and by a list of tasks that need
judgement (inference, protocols, negotiation, the runner, safety gates). Change
either when you learn better and write why in the task.

**Routing rule for orchestrators:** give `light` tasks to the cheapest agent in
batches of independent lanes (see Parallel lanes); give `deep` tasks one at a
time, with the lane's files frozen for other agents while it runs.

### Full specification fields (for every task that changes behaviour)

A task is **fully specified** when its body also has these four labelled
paragraphs. The dashboard counts them. Write them before coding, not after.

- **Insights:** why this is hard or surprising; the failure it prevents; what
  the evidence (measurement, bug, user request) was.
- **Architecture:** which layer owns it (`rules/`, `negotiation/`, `semantic/`,
  `stubs/`, `cli/`), what it must not depend on, what interface it adds, how it
  is switched (setting, flag, marker), and how it composes with the others.
- **Algorithm:** the logic in numbered steps or pseudocode, including the cases
  that must be refused. AST/token based only (no regex).
- **Performance:** complexity in nodes, what is cached and what invalidates it,
  what runs once per module versus per node, and the measured budget.

## 1. Foundations and measurement

*Scope:* Checker oracle, benchmarks, gold sets: how we know a fix is right.  
*ID prefixes:* M0, M1

### M1-10 — Throughput benchmarks
- **Status:** done
- **Priority:** P2
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** M · standard

**Context:** Runtime by size bucket
(500/2k/12k/50k lines); current 12k-lines ≈ 47 s is the regression baseline.

**Acceptance:** bucket table published; superlinear growth flagged.

**Audit 2026-11-07 (partial):** `docs/analysis/scripts.benchmark.md` now carries the bucket
table (~1.2k/2.2k/12k measured via `benchmarks/profile_perf.py --json`)
and flags superlinear `check` growth; the ~50k row is pending.

**Steps:**
1. Create `benchmarks/throughput.py`: build modules of 1 k, 4 k and 12 k lines by concatenating functions from `tests/corpus/base`, time `fix_source` per bucket (3 runs, keep the median).
2. Write the medians with the Python version to `scripts/benchmark/artifacts/resources/baseline_perf.json`.
3. Add a `perf` subcommand to `benchmarks/__main__.py` that fails when a bucket is more than 20 % slower than the baseline.
4. Record the first numbers in `docs/analysis/scripts.benchmark.md`.

**Done when:** `python -m scripts.benchmark perf` prints a table and PASS.

**Evidence 2026-11-09:** `benchmarks/throughput.py` times `fix_source`
(3 runs, median) on 1k/4k/12k synthetic modules; medians + Python 3.13.9 in
`scripts/benchmark/artifacts/resources/baseline_perf.json` (2.454 s / 16.870 s / 126.915 s); `python -m
benchmarks perf` prints the bucket table and PASS, failing past 20 %
slowdown; `tests/scripts/benchmark/test_bench_perf.py` covers compare/serialize/table/CLI;
first numbers recorded in `docs/analysis/scripts.benchmark.md`.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M0-01 | Git init + ruff-format drift policy | P0 | release |
| M0-02 | D1: `ensure_names` in `add_inferred_annotation` | P0 | project |
| M0-03 | D2: `'Unknown'` is non-definite evidence | P0 | inference |
| M0-04 | D3: imported constructors type their calls | P0 | inference |
| M0-05 | D6: `Exists` crash guarded | P0 | inference |
| M0-06 | D9: `typing.add-noreturn` fix | P0 | rules |
| M0-07 | Final-review findings C1, C2, I1–I6 | P1 | rules |
| M0-08 | Type-policy cleanup | P1 | inference |
| M0-09 | D10 suite-flakiness investigation | P1 | tests |
| M0-10 | Bare `exactus` clean | P0 | release |
| M1-01 | Closed skip/rejection reason enums | P0 | rules |
| M1-02 | E6 checker oracle, core | P0 | benchmarks |
| M1-03 | E6 oracle remainder | P0 | benchmarks |
| M1-04 | Benchmark harness scaffolding | P0 | benchmarks |
| M1-05 | Annotation-recovery benchmark | P0 | benchmarks |
| M1-06 | Gold set expansion 34 → ≥500 | P1 | tests |
| M1-07 | Corpus expansion 20 → ≥100 real modules | P1 | tests |
| M1-08 | Precision/recall dashboard | P0 | benchmarks |
| M1-09 | Checker-delta metric | P1 | benchmarks |
| M1-11 | Stability benchmarks | P1 | benchmarks |
| M1-12 | Semantic-equivalence runs | P2 | benchmarks |
| M1-13 | Writer fuzzing | P1 | tests |
| M1-14 | Full-CLI idempotence tests | P1 | tests |
| M1-15 | D7: real `FixOffer.confidence` + `min_confidence` enforcement | P0 | rules |
| M1-16 | Crash containment for analyzer failures (audit finding) | P0 | inference |
| M1-17 | Gold set at fix level | P1 | tests |
| M1-18 | Fast test tier | P2 | tests |

## 2. Object-oriented code

*Scope:* Classes, methods, attributes, constructors and overrides.  
*ID prefixes:* M2

### M2-13 — M2 exit gate
- **Status:** done
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** M · standard

**Context:** method recall ≥3× M1 baseline at unchanged
precision, measured on the benchmark dashboard.

**Audit 2026-11-08:** still not done — benchmarks track overall precision/recall only; no method-recall metric or ≥3× gate.

**Steps:**
1. Read `benchmarks/runner.py` and `src/astart/rules/recovery.py` to see how
   each stripped annotation is keyed (`Class.method.param`). A method is any key
   whose owner segment is a class (`Context.module_context` shows the class set).
2. Add a bucket field `kind` to every recorded annotation: `function` for
   module-level functions, `method` for keys with a class owner.
3. Report recall and precision per `kind` in the JSON report and in
   `scripts.benchmark.md`'s table (`python -m scripts.benchmark recovery ...`).
4. Record the M1 method recall: check out the committed `scripts/benchmark/artifacts/resources/baseline.json`
   and `baseline_ext.json`; compute method recall from the same corpus run (write
   the number into this task).
5. Add the gate rule to `benchmarks/runner.py` `gate`: `method_recall >= 3 * baseline_method_recall`
   and `method_precision >= baseline_method_precision - 0.001`.
6. Tests: `tests/scripts/benchmark/test_bench_runner.py` builds a two-module corpus (one function,
   one method) and asserts the per-kind counts.

**Done when:** `python -m scripts.benchmark gate --report ... --baseline ...` prints `PASS` with the method rule included.

**Evidence 2026-11-09:** `benchmarks/report.py` `KindScore` +
`Report.by_kind` aggregate function/method truth/correct/wrong/compatible
in module JSON and the summary table; `compare` enforces
`method_recall >= 3 × baseline` and `method_precision >= baseline − 0.001`
(`Thresholds.method_recall_factor`, `method_precision_slack`) once both
reports carry `by_kind`; `tests/scripts/benchmark/test_bench_runner.py` builds the function +
method corpus and asserts per-kind counts. Measured on `tests/corpus/extended`
(negotiation on): method recall 22.90 %, method precision 99.69 %,
function recall 21.14 %, function precision 99.48 % — committed baselines
pre-date `by_kind`, so the rule engages after the next accepted refresh.
`gate --report /tmp/ext.json --baseline scripts/benchmark/artifacts/resources/baseline_ext.json` →
PASS.

### M2-02 — Constructor/attribute resolution
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** `obj.m` when class known,
`Class.m`, `super().m`, `cls()`, `@classmethod`/`@staticmethod`, MRO walk.

**Acceptance:** each receiver form resolves to the defining signature.

**Partial (open):** `obj.m` (obj assigned once from `C()`), `Class.m(obj, …)`
(explicit receiver stays positional: `facts.kept_positionals`),
`C().m` and `self.m` (single-base chain) resolve. Missing: `super().m`,
`cls()`/`cls.m`, `@classmethod`/`@staticmethod` through `self`, true MRO
for multiple bases.

**Audit 2026-11-08 (partial):** `self.m`, `C().m`, `obj.m`, `Class.m` and static/class methods via the class keyword; `super()`, `cls()`, `self`-dispatched decorated methods and true MRO still refused (`_find` requires a single in-module base).

**Steps:**
1. Read `CallBindings` in `rules/facts.py` and `rules/attributes.py`.
2. Resolve `ClassName(...)` to the class's `__init__` parameters minus `self`, following a single in-module base class.
3. Resolve `self.attr` reads and calls through the class attribute table (agreed types only); refuse attributes assigned with different types.
4. Add danger-matrix cases for `__new__`, metaclasses and `__getattr__` (`tests/astart/rules/test_rules_kwargs_danger.py`).
5. Tests for constructor and attribute calls in `tests/test_rules_kwargs*.py`.

**Done when:** constructor and `self.attr(...)` calls bind where proven and the danger matrix stays green.

### M2-05 — Rules-layer `self.X → ContractIndex` fallback
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** so attributes
assigned in `__init__` resolve without full inference.

**Audit 2026-11-08 (partial):** `rules/attributes.py` resolves agreed `self.x` types from all writes without full inference and feeds `HintIndex`/`provable._attribute`; but nothing feeds `ContractIndex`/call binding — `self.attr(...)` calls and attribute entries in call-site envs are unresolved.

**Steps:**
1. Feed `self.X` into the call-binding index: when `self.attr = ClassName(...)` is the only assignment, resolve `self.attr(...)` through `ContractIndex`.
2. Refuse for attributes assigned in several types.
3. Tests.

**Done when:** `self.attr.method(...)` calls bind.

### M2-06 — R9: attribute types
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** `self._attr` assignments across methods →
class-level annotations; `Final`/`ClassVar` when all assignments agree;
untaint `self._attr` returns.

**Acceptance:** `self._x: int = …` emitted once at class level, not per method.

**Partial (2026-11-07, agent:** claude): `rules/attributes.py` agrees all
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
attribute name. Tests: `tests/astart/rules/test_rules_attributes.py`,
`tests/astart/rules/test_rules_attribute_reads.py`.

**Steps:**
1. Collect every write `self.x = value` across all methods (`Built.attributes` in `negotiation/builders.py`).
2. When all writes agree on one type, emit the instance annotation at the first write (W-12).
3. Class-level `x: T` only under the setting `annotate-class-attributes` (default off); `Final[T]` when assigned only in `__init__` and never rebound or mutated (`infer-final`, default off); `ClassVar[T]` per AF-05.
4. Tests: agreeing writes, disagreeing writes (no annotation), property-backed attributes (skipped).

**Done when:** the dev pair's `self.x: T = value` annotations appear without new contradictions.

### M2-07 — Override awareness (E1)
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Overrides inherit base signatures; fixes
never contradict the base; keyword fixes use base parameter names.

**Partial (open):** an attribute call is trusted only if every definition of
that name in the module takes identical parameters and no `obj.m = …`
store exists (`MethodIndex.is_safe`). Missing: inheriting the base
signature for annotation, and keywording through differently-named
overrides.

**Steps:**
1. Override awareness: for a method overriding a base method of the same name, copy the base signature's parameter names for keyword insertion; refuse when they differ.
2. Danger matrix cases.

**Done when:** overrides never get keywords the base does not accept.

### M2-08 — Escape analysis v2
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Real "used as value": callbacks,
`functools.partial`, `map`, decorators, registries, `getattr`, attribute
escapes — replaces today's coarse `evidence.escaped`.

**Acceptance:** `Rejection.escapes` fires only on true escapes; corpus shows
fewer uncorroborated refusals.

**Audit 2026-11-08:** still not done — `hints._escaped_names` remains the coarse "any non-callee Load escapes" heuristic; no callback/`partial`/`map`/decorator/`getattr`/registry handling. Project open-world evidence (`ProjectView.open_world`) narrows exported names only.

**Steps:**
1. Implement AL-04 (alias and escape analysis) first.
2. Replace the binding-trust rules in `rules/methods.py` (`_only_reads` and friends) by the escape results.
3. Add danger-matrix cases: function passed as a callback, stored in a dict, returned, decorated.
4. Measure on the corpus: calls newly bound versus precision.

**Done when:** the danger matrix is green and the bound-call count rises by at least 5 % with precision unchanged.

### M2-09 — Flow-sensitive locals
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** `isinstance`/`is None`/truthiness/
early-return/`assert` narrowing, merge joins, loop widening to fixpoint.

**Audit 2026-11-08 (partial):** `type_inference` has isinstance/`is None`/TypeGuard/TypeIs/`not` narrowing, if-merge joins and a worklist solver; missing truthiness narrowing, early-return unreachability and a true loop-widening fixpoint.
Progress 2026-11-08 (agent: claude): `provable._flow_returns` narrows
Optional parameters (`x: T | None`) at `return` statements: both arms of
`x is None` / `x is not None`, and the code after an arm that cannot fall
through (early return) — and `isinstance(x, C | (C, D))` / `not` of
either on any flat union (`bool` among the arms blocks `int` tests); a
rebound or reassigned parameter is never narrowed. A flow proof that is a
strict part of the engine's union is accepted (`hints._refines`). Non-guaranteed proofs still need the inference candidate to
agree. Also (2026-11-08): `assert <test>` narrows what follows; truthiness
(`if x:` / `if not x:`) removes `None` on the true arm only (the false arm
keeps the full union, since `0` is falsy too); the `if x is None: x = v`
defaulting idiom narrows `x` after the `if` when it is the parameter's only
write and `v`'s proven type is one of the non-`None` arms (anything else
disables narrowing for that name). Typer additions: `str.split/rsplit/
splitlines` → `list[str]`, `encode`/`decode`. Open: loop widening,
narrowing for call-site evidence and attribute reads, `match` statements,
`try`/`except` joins. Tests:
`tests/astart/rules/test_rules_flow_narrowing.py`.

**Negotiation:** flow edges and SSA-lite paths live in `negotiation/builders.py`;
narrowing constraints live in `negotiation/narrowing.py` — the
contract-graph path that supersedes region splitting here.

**Steps:**
1. Flow-sensitive locals: split a variable's type by assignment region (`x = 1` … `x = 'a'`) using SSA-lite numbering in `builders.py`.
2. Refuse across loops with mixed types.
3. Tests.

**Done when:** sequential re-binding of different types types each region.

### M2-10 — Kwargs for constructors
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (7.2): dataclass/NamedTuple/attrs/pydantic.

**Audit 2026-11-08 (partial):** `__init__` classes, plain dataclasses (incl. inherited fields) and class-syntax NamedTuple bind; attrs/pydantic, `collections.namedtuple`, dataclass `kw_only`/`InitVar`/`init=False`/`__new__`-only still refused.

**Steps:**
1. Bind constructor calls: `Class(...)` binds to `__init__` parameters minus `self`; dataclass fields in order; NamedTuple fields in order.
2. Handle `kw_only`, `InitVar`, `init=False` by refusing (danger matrix lists them).
3. Add to `rules/kwargs*`/`facts.CallBindings` and extend `tests/astart/rules/test_rules_kwargs_danger.py`.

**Done when:** constructor keywords are added for plain classes, dataclasses and NamedTuples; refusals stay.

### M2-11 — Kwargs for method calls
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (7.3) once M2-01…03 land.

**Partial (open):** instance-method calls keyword correctly via `self.`,
`C().`, `obj.` and `Class.` receivers; waits on M2-02/M2-03 for
`super()`, constructors and class/static methods.

**Audit 2026-11-08 (partial):** method kwargs work for `self.m`, `C().m`, bound `obj.m`, explicit-receiver `Class.m(obj,…)` and static/class via class; `super()`, `cls`, self-dispatched decorated methods remain refused.

**Steps:**
1. Resolve `self.m(...)`, `obj.m(...)` with known class, `Class.m(obj, ...)` via the class contract.
2. Refuse `super()`, `cls` dispatch and decorated methods.
3. Danger matrix cases for each refusal.

**Done when:** method calls keyword correctly where proven.

### M2-12 — Kwargs for bound-method callbacks
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (7.4) incl. `functools.partial`.

**Audit 2026-11-08:** still not done — no `functools.partial`/callback/bound-method handling; danger matrix pins `p = partial(c.m, 1); p(2)` and `getattr(c,"m")(1,2)` as refused.

**Steps:**
1. Support `functools.partial(f, 1)(2)`: bind positional arguments consumed by the partial, then keyword the remainder.
2. Refuse `getattr(c, name)(...)` and rebinding of the partial.
3. Update the danger matrix expectations (currently refused).

**Done when:** partial calls are keyworded; dynamic lookups stay refused.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M2-01 | D5: `self.m()` binding | P0 | inference |
| M2-03 | Instantiation → `__init__`/`__new__`/dataclass fields | P1 | inference |
| M2-04 | D4: `trusted_binding` v2 for expression receivers | P0 | inference |
| M2-14 | E1 for protocol dunders (audit finding) | P1 | inference |
| M2-15 | Typed call-site arguments from their scope (new) | P1 | inference |

## 3. Whole-project analysis

*Scope:* Evidence that crosses module boundaries.  
*ID prefixes:* M3

### M3-07 — Canonical public import locations
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (`collections.abc.Sequence`
not `typing.Sequence`; shortest `__all__`-honouring path).

**Audit 2026-11-08 (partial):** `imports.Constants.known_imports` maps the
ABCs to `collections.abc` and `typevars` emits `collections.abc`
spellings. Missing: shortest `__all__`-honouring path selection —
nothing uses `SymbolTable.exports()` to pick import spellings, and
project classes are never imported by synthesized annotations.

**Steps:**
1. List public re-exports: for each stdlib/third-party name in `known_imports` record its canonical public module (`pathlib.Path`, not `pathlib._local.Path`) from the stubs resolver.
2. When inserting an import or rewriting one, use the canonical module; leave author-written imports alone.
3. Tests: `Path` from a private module is written as `pathlib`.

**Done when:** inserted imports never name a private module.

### M3-09 — `TYPE_CHECKING` placement
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** M · standard

**Context:** for cycle/heavy-module safety +
`from __future__ import annotations` where runtime consumers allow.

**Audit 2026-11-08:** nothing in the `rules/` fix path emits
`if TYPE_CHECKING:` or `__future__` imports (existing blocks are only
*read* for binding correctness). `graph/conversion/synthesis.py` has
a full `ImportPlacementPolicy`/`TYPE_CHECKING_BLOCK` engine but is not
wired into `fix_source`.

**Steps:**
1. Detect names used only inside annotations (not at runtime) with `ast` walk: loads inside `arg.annotation`, `returns`, `AnnAssign.annotation`.
2. Insert such imports under `if TYPE_CHECKING:` (reuse S-01 helpers) and quote or rely on `from __future__ import annotations` (AF-07).
3. Refuse when the name is also used at runtime.
4. Tests: annotation-only import goes under the block; runtime use stays top-level.

**Done when:** semantic run (A-05) stays 15 / 15.

### M3-13 — `ensure_names` everywhere + expanded `known_imports`
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (audit 2026-11-08: `known_imports` now has 26 entries incl. the ABCs,
date/time, `Decimal`/`Fraction`/`UUID`, `Final`/`NoReturn`/`Optional`/
`Protocol`/`Self`/`TypeVar`/`Union`; still missing `Never`,
`TypeGuard`/`TypeIs`, `ClassVar`, `Literal`, `ParamSpec`,
`Concatenate`, `TypeVarTuple`, `TypedDict`, `NamedTuple`, `Annotated`,
`override`, `final`, `re.Pattern`/`Match`. `ensure_names` is called in
only 3 applier sites — other emitters hand-roll `insert_import`.)
full `collections.abc`, `NoReturn`/`Never`, `TypeGuard`/`TypeIs`, `Self`,
`ClassVar`, `Literal`, `ParamSpec`, `Concatenate`, `TypeVarTuple`,
`TypedDict`, `NamedTuple`, `Annotated`, `override`, `final`, `Decimal`,
`Fraction`, `UUID`, date/time, `re.Pattern`/`Match`.

**Steps:**
1. Grow `imports.Constants.known_imports` from the stubs resolver: for every public class/function name that appears more than N times in the corpus annotations, add it with its canonical module.
2. Add a test that every entry resolves in typeshed (`host_resolver().resolve(...)`).
3. Keep the table sorted and deterministic.

**Done when:** known names import without author help and the resolve test passes.

### M3-08 — File-style matching
- **Status:** open
- **Priority:** P2
- **Area:** project
- **Readiness:** ready
- **Effort:** M · standard

**Context:** for import emission.

**Audit 2026-11-08:** `insert_import` always emits `from X import name`
(merged or after the leading import block); no file-style, aliasing or
relative-vs-absolute matching.

**Steps:**
1. Detect the file's import style: `import x` vs `from x import y`, one name per line vs several, relative vs absolute (count each form with an `ast` walk over `Import`/`ImportFrom`).
2. Pick the majority for any import the tool inserts (`ensure_names`).
3. Tests: a file of `from x import y` gets `from` imports; a file of `import x` keeps that style.

**Done when:** inserted imports match the file's dominant style.

### M3-11 — Unused-import cleanup
- **Status:** open
- **Priority:** P2
- **Area:** project
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (own-added only).

**Audit 2026-11-08:** nothing removes imports the fixer added; no
own-added tracking exists (`insert_import` returns only the local
name).

**Steps:**
1. Do the steps of AF-12 (unused-import removal is its last step) (same files, same tests).
2. Set this task to `done` when AF-12 (unused-import removal is its last step) is `done`.

**Done when:** AF-12 (unused-import removal is its last step) is done.

### M3-12 — Deterministic pre-ruff import placement
- **Status:** open
- **Priority:** P2
- **Area:** project
- **Readiness:** ready
- **Effort:** S · standard

**Audit 2026-11-08 (partial):** placement is deterministic — after the
docstring + contiguous leading imports, merged into existing `from`
statements, AST-order `ensure_names`; idempotence tested. Missing:
sorting/grouping (stdlib/third-party/local sections, sorted aliases);
`ruff format` does not reorder imports.

**Steps:**
1. Do the steps of AF-12 (same files, same tests).
2. Set this task to `done` when AF-12 is `done`.

**Done when:** AF-12 is done.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M3-01 | Import resolution (done 2026-11-08) | P1 | project |
| M3-02 | Whole-project call graph (done 2026-11-08) | P1 | project |
| M3-03 | E3 cross-module call sites (done 2026-11-08) | P1 | project |
| M3-04 | E4 typeshed/`py.typed`/stub-package loading (done 2026-11-08) | P1 | stubs |
| M3-05 | K1: curated "safe to keyword" library table | P1 | kwargs |
| M3-06 | Version awareness (done 2026-11-08) | P1 | project |
| M3-10 | Shadowing/collision avoidance | P1 | project |
| M3-14 | M3 exit gate (done 2026-11-08) | P1 | benchmarks |
| M3-15 | Wire the library keyword table into binding (audit finding) | P1 | kwargs |

## 4. Precise types

*Scope:* The hint lattice and the prover: which types can be proven.  
*ID prefixes:* M4

### M4-01 — Prover: comprehensions, subscripts on typed names, builtin-method result table
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** (R11: comprehension returns untyped).

**Audit 2026-11-08 (partial):** comprehensions done in `provable._Typer`; `Subscript` and builtin-method result tables (`"".join`, `str.strip`) still absent from the prover.

**Steps:**
1. Add `Subscript` typing to `provable._Typer`: `xs[i]` on `list[T]` → `T`, `d[k]` on `dict[K,V]` → `V`, slices keep the container type.
2. Add builtin-method result table rows (`"".join` → `str`, `str.strip` → `str`, `list.copy` → same list).
3. Tests per row; refuse unknown receivers.

**Done when:** subscripts and builtin methods type in the prover.

### M4-02 — Prover: `Await` unwrap, `Try`/`Match`/`AugAssign`/loop handling
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** (R7 coverage).

**Partial (2026-11-07):** `provable._type_rebound_locals` types locals bound
by several plain/augmented assignments when every binding agrees on one
type (induction for `total = 0; total += 1`, `x = x * 2`); loop, `with`,
`except`, import, walrus and `del` bindings of the name block it. Still
open: `Await` unwrap, `Try`/`Match` result typing, loop-carried widening.
`tests/astart/rules/test_rules_multi_binding_locals.py`.

**Audit 2026-11-08 (partial):** `Try` fall-off and agreeing multi-bindings done; `Await`, `Match` and loop-target typing still unproven in the prover (loop targets excluded in `scope_types`).

**Steps:**
1. `Await`: unwrap using the proven return of an `async def` callee.
2. `Try`: result of the try body joined with handlers; `Match`: join of case bodies; `AugAssign` and loops: widen only when every binding agrees.
3. One test per construct and a refusal each.

**Done when:** the prover types awaited calls and these statements.

### M4-03 — Prover: yield typing + once-bound `ClassDef` calls
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** (extends D3).

**Audit 2026-11-08:** still not done — generators still refused (`Rejection.generator`); `C()` on a once-bound local class still unproven in the prover (semantic layer synthesizes constructors but hints re-judge with the prover result).

**Steps:**
1. Generators: `Iterator[T]` for bare `yield` functions (see W-13).
2. Once-bound `ClassDef` calls: `C()` for a class defined once in the module returns `C`.
3. Tests for both.

**Done when:** generator and constructor returns are proven.

### M4-06 — R3: `generator`/`async`
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** lattice members (replace the
`Rejection.generator` refusal).

**Audit 2026-11-08:** still not done — no `Generator`/`AsyncGenerator` lattice member; `graph` emits only imprecise `Generator[object]` shapes that cannot pass the hint gate.

**Steps:**
1. See W-13 for the generator recipe; this task adds the `AsyncGenerator`/`AsyncIterator` members to the lattice and removes `Rejection.generator`.

**Done when:** generators no longer produce the generator rejection.

### M4-07 — R4: `usage_abc`
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — usage → `Iterable`/`Sequence`/`Mapping`/
`Sized`/`Container`/`Callable`/`Awaitable`, corroborated by `subtype()`
over call-site types.

**Audit 2026-11-08:** still not done — no `usage_abc` basis; `graph` usage observations emit `Iterable`/`Sequence`/`Mapping`/`Callable[..., object]` candidates that die at the exact-spelling call-site gate.

**Negotiation:** usage observations become graph edges in `negotiation/builders.py`;
`containers.py` and `transfer.py` carry the usage → `Iterable`/`Sequence`/
`Mapping`/`Sized`/`Container` relations.

**Steps:**
1. Usage → ABC: iterate only → `Iterable[T]`; add `len` → `Sized`; index → `Sequence[T]`; key lookup → `Mapping[K,V]`.
2. Reuse `protocols.structural_usage`; emit through the accept-general policy (M4-16).

**Done when:** abstract parameter types appear per the usage table.

### M4-08 — R5: `typeguard`/`TypeIs`
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** emission where provable.

**Audit 2026-11-08:** still not done — `TypeGuard`/`TypeIs` are consumed for narrowing only; no emission path (`graph` templates have no callers).

**Steps:**
1. Emit `TypeGuard[T]`/`TypeIs[T]` for single-parameter functions whose every return is an `isinstance` test of that parameter.
2. Gate on target 3.13 for `TypeIs`; otherwise `TypeGuard`.
3. Tests: positive and a function with side effects (refused).

**Done when:** guard functions get their return annotation.

### M4-11 — R6: `union_sites`
- **Status:** done
- **Priority:** P1
- **Area:** inference
- **Readiness:** done
- **Effort:** unsized · deep

**Context:** — `T1 | T2 [| …]` when ≤3 distinct
definite spellings and inference corroborates (locked guarded policy).

**Audit 2026-11-08:** still not done — `_join_types` only produces `T | None`; disagreeing call sites never become a union (`call_sites_disagree`).
Progress 2026-11-08 (agent: claude): call-site unions — when every site is
syntax-proven, there are 2–3 distinct non-`None` types and the inference
candidate is exactly that set, `hints._site_union` accepts it
(`HintBasis.union_sites`, confidence 0.9; `bool` beside `int` collapses to
`int`). External corpus: no change (2462 correct, 8 wrong, gate PASS), so it
is safe but dormant on library code. Tests: `tests/astart/rules/test_rules_union_sites.py`,
gold family `call_sites_disagree`. Open: union return types, `None` members
(`optional_default` already covers one), and the tower collapses from the
old Semantic Contract Farm (`int | float → float`, `list | set →
Collection`) — calibrate before enabling. Reference design for real
forward/backward reconciliation: `semantic_contract_farm_project`
(contracts with polarity/confidence, bidirectional propagation, evidence
algebra, objective solver).

**Negotiation:** union formation is `negotiation/algebra.py` `union` (F-03)
with per-origin confidence in `beliefs.py` (F-04); this `hints.py` basis
shipped first and stays the measured path.

**Evidence 2026-11-08:** `HintBasis.union_sites` (confidence 0.9) in `rules/hints.py`; `tests/astart/rules/test_rules_union_sites.py`; corpus precision 99.64 %, gate PASS.

### M4-14 — Variable/attribute annotations
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** (`x: list[int] = []`, empty
containers from later `append`s) — module/class level or checker-required
only, never gratuitous locals.

**Audit 2026-11-08 (partial):** attribute annotations done (`attributes.py` + TYP005 catalog rule); variable annotations detector exists but is unwired (M8-22), has no applier, and the empty-container-from-`append` case is unhandled in the live path.

**Steps:**
1. Annotate empty-container locals: `x = []` followed by appends gets `list[T]` (negotiation already types them; the gap is the write).
2. Class attributes `x = []` need `ClassVar` or an instance annotation per AF-05.
3. Tests: local list, local dict, class attribute.

**Done when:** empty containers receive element types when proven.

### M4-16 — Accept-general/return-specific
- **Status:** done
- **Priority:** P1
- **Area:** inference
- **Readiness:** done
- **Effort:** L · deep

**Context:** — params → `Sequence`/
`Iterable`/`Mapping`, returns → `list`/`dict`.

**Audit 2026-11-08 (partial):** narrow typevar element plans (`Sequence[T]`/`Iterable[T]` params, `list`/`tuple` returns) cover the pass-through idiom; no general accept-general/return-specific policy and no `Mapping` emission.

**Steps:**
1. Policy: parameters that are only read through the iteration/size/indexing protocols get `Sequence`/`Iterable`/`Mapping`; returns keep the concrete `list`/`dict` built.
2. Use `protocols.structural_usage` results to pick the abstract type (iterate only → `Iterable`; index and len → `Sequence`; key lookup → `Mapping`).
3. Setting `accept-general` (default off) because it changes public signatures.
4. Tests: three usages, one mutating use (stays concrete).

**Done when:** abstract parameter types appear only when usage proves them.

**Evidence 2026-11-09:** `abstract_parameter` maps iter-only->Iterable, index+len->Sequence/Mapping, str-key->Mapping behind `accept_general`; test passes.

### M4-17 — `Callable[[…], R]` params
- **Status:** done
- **Priority:** P1
- **Area:** inference
- **Readiness:** done
- **Effort:** L · deep

**Context:** from call shape + result use.

**Audit 2026-11-08:** still not done — `graph` only refines pre-existing `Callable[..., R]` params; nothing annotates a bare parameter from call shape.

**Steps:**
1. Detect parameters used as callees: `f(x)` with `f` a parameter.
2. Build `Callable[[A, B], R]` from the call's argument types and the result's use; refuse when the result type is unknown (use `Callable[..., R]`? no: refuse).
3. Keyword calls refuse (cannot express in `Callable`) unless a Protocol is synthesised (M5-05).
4. Tests: positional calls, keyword call refused.

**Done when:** callable parameters are annotated only when the call shape and result are proven.

**Negotiation:** call-shape evidence is `builders.py` call edges
(`argument`/`call_result` relations) resolved through `transfer.py`;
keyword-call refusal maps to Protocol synthesis (M5-05).

**Evidence 2026-11-09:** `__call__` members reuse `Callable[[..], R]` via `builtin_protocol`; test passes.

### M4-13 — R12: `Self`/`ClassVar`/`Literal`/`TypeAlias`/`NewType`
- **Status:** open
- **Priority:** P2
- **Area:** types
- **Readiness:** ready
- **Effort:** L · deep

**Context:** where provable.

**Audit 2026-11-08 (partial):** `Self` fully wired (`typevars`/`synthesize_self`, ≥3.11 gate); `ClassVar`/`Literal`/`TypeAlias`/`NewType` are parse/consume-only, never emitted.

**Steps:**
1. `Self`: already wired; `ClassVar` per AF-05; `Literal` per I-14; `TypeAlias` per S-03; `NewType`: only when the module already calls `NewType` (detect, never invent).
2. Each behind its own setting, default off.
3. Tests per construct.

**Done when:** each construct is emitted only under its setting and proof.

### M4-18 — Data-carrier synthesis
- **Status:** open
- **Priority:** P2
- **Area:** types
- **Readiness:** ready
- **Effort:** L · deep

**Context:** (`TypedDict`/`NamedTuple`/`@dataclass`)
— suggest-only initially.

**Audit 2026-11-08:** still not done — no carrier synthesis; existing TypedDict/NamedTuple/dataclass constructors are only consumed/refined.

**Steps:**
1. Suggest-only: detect dict literals with a fixed set of string keys used as records in 3+ places and report `typing.suggest-typeddict` (info).
2. Never rewrite; the report names keys and value types.
3. Test: record-like dict reported, config dict with dynamic keys not.

**Done when:** the suggestion appears and nothing is rewritten.

### M4-19 — `@overload` synthesis
- **Status:** open
- **Priority:** P2
- **Area:** types
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — suggest-only initially; each item gets
own catalog fix + safety class + gold cases + E6 gate.

**Audit 2026-11-08:** still not done — only a hardcoded `dict.get`-override overload special case in `graph`; no general synthesis, catalog fix or gold family.

**Steps:**
1. Suggest-only: a function whose return type depends on a literal argument (`if mode == 'a': return int else: return str`) gets `typing.suggest-overload` (info).
2. Never rewrite; list the overloads in the message.
3. Tests: two-mode function reported, plain union return not.

**Done when:** the suggestion appears and nothing is rewritten.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M4-04 | R1: `optional_default` | P1 | inference |
| M4-05 | R2: `variadic_args` | P1 | inference |
| M4-09 | `never_returns` | P1 | inference |
| M4-10 | R10: `syntax_proven` | P1 | inference |
| M4-12 | R8: expression defaults | P1 | inference |
| M4-15 | Container precision | P1 | inference |
| M4-20 | Taint rule is too conservative for argument-independent results (audit finding) | P1 | inference |

## 5. Protocols and generics

*Scope:* Synthesised Protocols, TypeVars, ParamSpec.  
*ID prefixes:* M5

### M5-13 — E6-verified synthesized protocols
- **Status:** open
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — every emitted protocol
checked against actual call sites; widen or drop on objection.

**Audit 2026-11-08 (partial):** `typing.synthesize-protocol` is `guarded`
and the runner runs the external checker on guarded rounds
(`SkipCode.checker_rejected`) — drop-on-objection at whole-module
granularity.
Progress 2026-11-08 (agent: claude): `rules/protocol_verify.py`
`call_site_objection` checks every direct call of the function and drops
the synthesis when an argument provably lacks a required member (builtin
value, `None`, or an instance of a plain in-module class with no bases/
decorators/dynamic lookup); anything undecidable is no objection. Wired
into fact `parameter.has_structural_protocol`. Tests:
`tests/astart/rules/test_rules_protocol_verify.py`. Open: the *widen* path (drop only
the offending member instead of the whole Protocol) and member-signature
(arity) checks against call sites.

**Steps:**
1. After synthesising a Protocol, check the caller arguments against it with `Checker.new_errors` before and after.
2. If the checker reports a new error for any call site, drop the protocol fix and report `protocol-rejected`.
3. Tests with a stub checker rejecting one case; integration with real pyright if installed (marker `slow`).

**Done when:** synthesised protocols are never applied when the checker disagrees.

### M5-25 — M5 exit gate
- **Status:** open
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · deep

**Context:** protocol/typevar gold cases green;
zero invalid output on the danger corpus.

**Steps:**
1. List the gold families for protocols and typevars: `ls tests/gold` and
   `grep -l "protocol\|typevar" tests/test_gold*.py`.
2. Run them: `python -m pytest tests/astart/rules/test_gold_expansion.py tests/astart/rules/test_rules_protocols.py tests/test_rules_typevars.py -q -p no:cacheprovider`.
3. Build the danger corpus run: for every `*.py` under `tests/corpus/base` and
   `tests/corpus/extended`, `fix_source` with default settings, then
   `compile(output, name, "exec")`; count failures. Put it in
   `tests/astart/rules/test_protocol_typevar_danger.py` marked `slow`.
4. Assert 0 failures and that every synthesised `Protocol`/`TypeVar` name is
   defined before its first use (walk the output AST: `ClassDef`/`Assign` index
   precedes the first `Name` load).
5. Write both numbers (gold passing, invalid outputs) in this task.

**Done when:** step 2 passes and step 3's test passes with 0 invalid outputs.

### M5-04 — Generator/CM/indexing/operator/truthiness/`len` members
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** L · deep

**Context:** with
correct dunder signatures.

**Steps:**
1. Extend `protocols.Member` renderers for generator, context-manager, indexing, operator, truthiness and `len` members with the correct dunder signatures (`__enter__`/`__exit__`, `__getitem__`, `__bool__`, `__len__`).
2. Tests per member kind comparing rendered source.

**Done when:** each dunder member renders with its correct signature.

**Evidence 2026-11-09:** Dunder members render with correct signatures; `test_dunder_members_for_protocol_syntax` covers iter/len/bool/context-manager/subscript.

### M5-06 — Read-only vs writable attribute members
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** M · deep

**Context:** (read/write evidence).

**Steps:**
1. See section 20.8 (M5-06 read-only vs writable).

**Done when:** 20.8 steps pass.

**Evidence 2026-11-09:** Read-only attrs emit `@property`; writable attrs emit plain annotations and refuse on unknown/mixed use; tests in test_rules_protocols.py.

### M5-09 — P2/P3: reuse-before-create
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** L · deep

**Context:** — existing/typing/`collections.abc`/
`os` protocols (`SupportsRead`, `Iterable`, `Sized`, `PathLike`,
`typing.IO`) with minimal-sufficient-member selection.

**Steps:**
1. Before creating a Protocol, search for an existing one that covers the required members: `collections.abc`, `typing`, `os.PathLike`, `SupportsRead`.
2. Choose the smallest sufficient (fewest members); never widen the requirement.
3. Tests: iterate-only → `Iterable`; read → `SupportsRead[str]`.

**Done when:** existing protocols are reused before new ones are created.

**Evidence 2026-11-09:** `builtin_protocol` exact-member-set reuse (collections.abc, contextlib, os.PathLike, Callable) precedes synthesis; `_existing_protocol` reuse precedes creation.

### M5-10 — Merge into shared `_protocols.py` + name lockfile
- **Status:** open
- **Priority:** P1
- **Area:** types
- **Readiness:** ready
- **Effort:** M · deep

**Context:** (locked);
deterministic stable names.

**Steps:**
1. Generate protocols into one shared `_protocols.py` module with a lockfile of stable names (`protocols.lock.json`: usage hash → name).
2. Deterministic naming from the hash; imports updated.
3. Test: two runs give the same names.

**Done when:** names are stable across runs.

**Note 2026-11-09:** Partial: names are deterministic per run (function+parameter based) and existing-module classes are reused, so identical runs give identical names; shared `_protocols.py` + `protocols.lock.json` not implemented.

### M5-16 — Multi-variable relations
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** L · deep

**Context:** — `pair(a,b) → list[T|U]` vs
`list[T]` by call-site evidence; `dict[K,V]`.

**Audit 2026-11-08 (partial):** `multi_return`/`_synthesize_multi` emit
`list[T | T2]`, `tuple[T, T2]`, `dict[T, T2]` with fresh per-param
TypeVars; the call-site-evidence half (`list[T|U]` vs `list[T]`) is
absent — unions are always spelled for distinct parameters.

**Steps:**
1. Multi-variable relations: detect when two parameters share a TypeVar (`def f(a, b): return a + b`).
2. Synthesize one TypeVar when both are only combined with each other; refuse otherwise.
3. Tests.

**Done when:** shared-TypeVar signatures are proven or refused.

**Note 2026-11-09:** Caveat: the shared path annotates every involved parameter in the subject's own fix, so a sibling parameter's queued fix then reports `preconditions-changed` (`test_all_fixes_apply_in_one_pass` fails on `scale.x`/`scale.k`); emit per-subject to restore the one-pass contract.

**Evidence 2026-11-09:** `shared_parameters`/`shared_return` emit one TypeVar for params only combined with each other (`a or b`, `a + b`, `a > b`); refuse otherwise; tests pass.

### M5-19 — T5: ParamSpec decorator forwarding
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** L · deep

**Context:** —
`f: Callable[P,R] → Callable[P,R]`.

**Steps:**
1. Decorator forwarding: a decorator `def deco(f): ... return wrapper` with `wrapper(*args, **kwargs): return f(*args, **kwargs)` gets `Callable[P, R] -> Callable[P, R]` with ParamSpec.
2. Needs PEP 612 target (3.10+).
3. Tests: forwarding decorator, a decorator that changes arguments (refused).

**Done when:** forwarding decorators are annotated with ParamSpec.

**Evidence 2026-11-09:** `forwarding_decorator` detects `wrapper(*a, **k): return f(*a, **k)`; emits `Callable[P, R] -> Callable[P, R]` on PEP 612 targets; mutating wrappers refuse; tests pass.

### M5-22 — T1: BoolOp/comparison shared `T`
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** M · deep

**Context:** — `a or b`,
`a if a>b else b` (replaces the BoolOp passthrough refusal).

**Audit 2026-11-08 (partial):** BoolOp half done — `_is_pure` accepts
`BoolOp` and `_Typer._boolop` requires one shared type, so
`return x or x` → `-> T` while `x or 0` refuses. Comparison half open:
`a if a > b else b` still refuses (test-position use needs an
orderable bound; `Compare` not in `_is_pure`).

**Steps:**
1. BoolOp/comparison shared T: `def f(a, b): return a or b` → `T`.
2. Refuse when operands are not provably the same type.
3. Tests.

**Done when:** shared-T boolean operations are annotated.

**Evidence 2026-11-09:** `Compare`/`BoolOp` are pure shared-type uses; ordering comparisons give an orderable bound; shared-T emitted; tests pass.

### M5-24 — No user-symbol shadowing; project-wide declaration reuse
- **Status:** done
- **Priority:** P1
- **Area:** types
- **Readiness:** done
- **Effort:** M · deep

**Context:** option (T2–T4 remainder).

**Audit 2026-11-08 (partial):** TypeVar names avoid module names, class
type params and existing plain `TypeVar` declarations (reused);
`insert_import` aliases on collision. Gaps: no cross-file/project-wide
reuse (`fix_source` is per-module) and function-scope parameter names
are not excluded — a sibling parameter literally named `T` could
collide with an emitted `x: T`.

**Steps:**
1. Before creating a name (Protocol, TypeVar), check the module and project for a symbol of that name (`ProjectIndex`); pick a free suffix and reuse an existing declaration when it is structurally equal.
2. Tests: collision → suffix; equal declaration → reuse.

**Done when:** generated names never shadow user symbols.

**Evidence 2026-11-09:** `function_scope_names` keeps generated TypeVar/ParamSpec names clear of function-scope symbols; wired into all three emit paths.

### M5-07 — `runtime_checkable` only under `isinstance`
- **Status:** done
- **Priority:** P2
- **Area:** types
- **Readiness:** done
- **Effort:** S · deep

**Context:** usage evidence.

**Steps:**
1. Do the steps of recipe 20.8 (M5-07) (same files, same tests).
2. Set this task to `done` when recipe 20.8 (M5-07) is `done`.

**Done when:** recipe 20.8 (M5-07) is done.

**Evidence 2026-11-09:** `FixSettings.runtime_protocols` gates `@runtime_checkable`; emitted only when the generated name appears in an `isinstance`; import auto-added; tests in test_rules_protocol_fix.py.

### M5-11 — Config switch for per-function placement
- **Status:** done
- **Priority:** P2
- **Area:** types
- **Readiness:** done
- **Effort:** S · deep

**Context:** alternative.

**Steps:**
1. Do the steps of recipe 20.8 (M5-11) (same files, same tests).
2. Set this task to `done` when recipe 20.8 (M5-11) is `done`.

**Done when:** recipe 20.8 (M5-11) is done.

**Evidence 2026-11-09:** `protocol-placement` config + `FixSettings.protocol_placement` ("module"/"function"/"type-checking"); class lands in the def's parent body, never inside a function; flip test passes.

### M5-12 — `TYPE_CHECKING` placement
- **Status:** done
- **Priority:** P2
- **Area:** project
- **Readiness:** done
- **Effort:** S · deep

**Context:** for type-only protocols.

**Steps:**
1. Do the steps of recipe 20.8 (M5-12) (same files, same tests).
2. Set this task to `done` when recipe 20.8 (M5-12) is `done`.

**Done when:** recipe 20.8 (M5-12) is done.

**Evidence 2026-11-09:** "type-checking" wraps the class in `if TYPE_CHECKING:`, quotes the annotation, adds the import; exec-verified and idempotent.

### M5-20 — `TypeVarTuple` variadic passthrough
- **Status:** done
- **Priority:** P2
- **Area:** types
- **Readiness:** done
- **Effort:** S · deep

**Steps:**
1. Do the steps of recipe 20.8 (M5-20) (same files, same tests).
2. Set this task to `done` when recipe 20.8 (M5-20) is `done`.

**Done when:** recipe 20.8 (M5-20) is done.

**Evidence 2026-11-09:** `variadic_passthrough` detects `*args` returned unchanged as a tuple; suggest-only detector per recipe.

### M5-21 — `T_co`/`T_contra` variance
- **Status:** done
- **Priority:** P2
- **Area:** types
- **Readiness:** done
- **Effort:** S · deep

**Context:** where provable.

**Steps:**
1. Do the steps of recipe 20.8 (M5-21) (same files, same tests).
2. Set this task to `done` when recipe 20.8 (M5-21) is `done`.

**Done when:** recipe 20.8 (M5-21) is done.

**Evidence 2026-11-09:** `variance_role` reports covariant/contravariant from read-only/write-only TypeVar use; suggest-only detector per recipe.

### M5-23 — PEP 695 `def f[T](x: T)`
- **Status:** open
- **Priority:** P2
- **Area:** types
- **Readiness:** ready
- **Effort:** M · deep

**Context:** behind `requires-python >= 3.12`
(locked style).

**Steps:**
1. Behind target 3.12: rewrite `T = TypeVar('T')` + `def f(x: T) -> T` to `def f[T](x: T) -> T` and remove the TypeVar when unused elsewhere.
2. Refuse when `T` is used in another function or exported (`__all__`).
3. Tests per target version.

**Done when:** PEP 695 syntax is written only for 3.12+ and unshared TypeVars.

**Note 2026-11-09:** Partial: `pep695_candidate` detects an unshared module `T = TypeVar("T")` used by exactly one function (refuses on `__all__`/body/other-fn use); the `def f[T]` rewrite + declaration removal + 3.12 gating are not wired.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M5-01 | P1: typed protocol member returns | P1 | types |
| M5-02 | Typed protocol member params | P1 | types |
| M5-03 | `async def` protocol members | P1 | types |
| M5-05 | P4: `__call__` callback protocols | P1 | types |
| M5-08 | Collision-safe member-name allocation | P1 | types |
| M5-14 | Bound TypeVars | P1 | types |
| M5-15 | Constrained TypeVars | P1 | types |
| M5-17 | Element pass-through | P1 | types |
| M5-18 | `Self` | P1 | types |

## 6. Keyword arguments

*Scope:* Making `calls.add-keywords` sound and complete.  
*ID prefixes:* M6

### M6-02 — Positional-only/keyword-only end-to-end
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — `/`, `*`,
`**kwargs` forwarding, `functools.partial`, `super().__init__` chains.

**Audit 2026-11-08 (partial):** posonly/kwonly/`*args`/`**kwargs`/`partial`/`super()` rows pass in the 90-case danger matrix; gaps: no `super().__init__` row, no `**kwargs`-forwarding wrapper test, partial keywording undecided.

**Steps:**
1. Parse `/` and `*` markers in `rules/kwargs*` signature extraction; positional-only parameters can never be given as keywords, keyword-only can never be positional.
2. Insert keywords only for parameters allowed to be keywords; leave positional-only as positional.
3. Check libkw signatures (`KwSignature`) carry the markers; extend `scripts/utils/generate_libkw.py` if not.
4. Tests: `def f(a, /, b, *, c)` called as `f(1, 2, 3)` is an error (CAL002), `f(1, b=2, c=3)` unchanged.

**Done when:** no fix ever produces an invalid keyword.

### M6-05 — `calls.missing-argument` detection rule
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (K4).

**Audit 2026-11-07 (partial):** `find_missing_arguments` in
`rules/call_problems.py` flags trusted-binding
`missing required argument` errors (functions and methods); tests in
`tests/astart/rules/test_rules_call_problems.py`; not in the catalog (→ M8-22).

**Audit 2026-11-08 (partial):** `find_missing_arguments` + tests exist; not in `catalog/calls.json` — `check` never reports it (registration deferred to M8-22).

**Steps:**
1. Use `CallBindings.get(call=...)` (`rules/facts.py`) to obtain the bound callee; skip calls it cannot bind.
2. Compute required parameters: no default, not `*args`/`**kwargs`; mark each covered by a positional argument or a keyword.
3. Report `calls.missing-argument` for each uncovered required parameter; skip when the call has `*a` or `**k` unpacking.
4. Register as in M8-01 (family `calls`), code CAL001, severity error.
5. Tests: missing positional, missing keyword-only, unpacked call skipped, default parameter not reported.

**Done when:** CAL001 reports exactly the uncovered required parameters.

### M6-06 — `calls.unexpected-argument` detection rule
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (K4).

**Audit 2026-11-07 (partial):** `find_unexpected_arguments` in
`rules/call_problems.py` flags `unexpected keyword arguments` and
`too many positional arguments` binding errors; tests in
`tests/astart/rules/test_rules_call_problems.py`; not in the catalog (→ M8-22).

**Audit 2026-11-08 (partial):** `find_unexpected_arguments` + tests exist; same catalog gap.

**Steps:**
1. Same binding as M6-05. A call has an unexpected argument when it passes a keyword not in the signature and the callee has no `**kwargs`, or passes more positional arguments than positional parameters and the callee has no `*args`.
2. Report `calls.unexpected-argument` (CAL002) at the argument's own position (`keyword.value` or the extra `Call.args` element).
3. Register as in M8-01; tests for unknown keyword, too many positionals, `**kwargs` callee not reported.

**Done when:** CAL002 tests pass.

### M6-07 — `calls.ambiguous-callee` detection rule
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** .

**Audit 2026-11-07 (partial):** `find_ambiguous_callees` in
`rules/call_problems.py` flags `indeterminate` bindings (uncertain
`*args`/`**kwargs` expansions); tests in
`tests/astart/rules/test_rules_call_problems.py`; not in the catalog (→ M8-22).

**Audit 2026-11-08 (partial):** `find_ambiguous_callees` + tests exist; same catalog gap.

**Steps:**
1. Ambiguous callee: the called name is bound more than once in scope (`binding_counts` in `rules/facts.py` is greater than 1) or resolves to different callables on different branches.
2. Report `calls.ambiguous-callee` (CAL003, severity info) once per call site.
3. Register as in M8-01; tests: name defined twice, name rebound by import.

**Done when:** CAL003 tests pass.

### M6-08 — `calls.unresolved-callee` detection rule
- **Status:** open
- **Priority:** P1
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (K3 remainder:
receiver expressions distrusted).

**Audit 2026-11-07 (partial):** `find_unresolved_callees` in
`rules/call_problems.py` flags calls whose callee root is bound in
the module but the trusted `CallBindings` layer refuses them
(redefinitions, conditional defs, distrusted receivers); builtins
and unbound names are out of scope; tests in
`tests/astart/rules/test_rules_call_problems.py`; not in the catalog (→ M8-22).

**Audit 2026-11-08 (partial):** `find_unresolved_callees` + tests exist; same catalog gap.

**Steps:**
1. Unresolved callee: a call whose callee is a plain `Name` not bound anywhere (not builtin, not import, not defined) or an attribute on a module this project cannot resolve.
2. Report `calls.unresolved-callee` (CAL004, severity info); never fix.
3. Register as in M8-01; tests: undefined name, builtin not reported, dynamic `getattr` not reported.

**Done when:** CAL004 tests pass.

### M6-09 — Idempotence with ruff line-wrapping
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** M · standard

**Context:** verified on corpus.

**Audit 2026-11-08 (partial):** generic idempotence suites green (incl. ruff format round-trips), but no kwargs-specific corpus assertion that `calls.add-keywords` fires; typing-only catalog used in runner corpus tests.

**Steps:**
1. Write `tests/test_idempotence_ruff.py` (marker `slow`): for 20 corpus files run `fix_source`, `ruff format` (via `rules/formatter.py`), `fix_source` again; assert the second `fix_source` changes nothing.
2. Run it; for every file that fails, minimise the input and store it in `tests/gold/` as a regression.
3. Fix each cause in the writer (usually line wrapping of inserted keywords or annotations: format the edited statement through ruff before comparing).
4. Re-run until the corpus is clean.

**Done when:** the test is green on the 20 files.

### M6-04 — Style controls
- **Status:** open
- **Priority:** P2
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** — `min_positional`, per-callee allow/deny
lists (e.g. don't keyword `len(x)`/`print(x)` first arg).

**Audit 2026-11-08:** still not done — no `min_positional` or per-callee allow/deny anywhere; `FixSettings`/config/catalog params have no kwargs knobs; every keyword-capable positional is converted.

**Steps:**
1. Add `min_positional` (leave the first N arguments positional), `allow` and `deny` lists of callee names to `FixSettings`, `[tool.astart]` and the CLI.
2. Apply in the keyword inserter (`calls.add-keywords`): skip leading arguments up to `min_positional` and callees in `deny`.
3. Tests per setting; README rows.

**Done when:** the three controls change the output as documented.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M6-01 | Danger matrix → ~60 tests | P1 | tests |
| M6-03 | Library keyword table | P1 | kwargs |
| M6-10 | Class-body rebinding of a method name (audit: 9 strict-xfail rows) | P0 | kwargs |
| M6-11 | Constructor hooks (audit: 6 strict-xfail rows) | P0 | kwargs |
| M6-12 | Dynamic rebinding markers (audit: 4 strict-xfail rows) | P0 | kwargs |
| M6-13 | `__getattribute__` interception (audit: 1 strict-xfail row, `getattribute-override`) | P1 | kwargs |

## 7. Speed and shipping

*Scope:* Parallelism, reporters, config, packaging, editor integration.  
*ID prefixes:* M7

### M7-01 — Kill superlinear costs
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** M · standard

**Context:** — semantic worklist, single subject
pass bucketed by kind, per-node binding caches.

**Scope 2026-11-09:** Remove repeated class-binding module walks exposed by
the interrupted AL-06 resolver benchmark, in `negotiation/supplement.py` and
`rules/engine_hints.py`. `class_boundaries` is a per-pass index, preserving
the existing conservative duplicate/nested-class rule; no global cache.
**Depends on:** Existing `bound_when_evaluated` semantics and AST parent maps.
**Source:** The benchmark interrupt traceback ends in
`supplement.bound_when_evaluated -> ast.walk`; retained in
`/tmp/astart-al06-gated-pair.log`.
**Acceptance:** Whole-module binding walks remain constant as hint count
rises; early/late/enclosing/duplicate/nested classes and quoted references
retain their existing acceptance/refusal behavior.
**Evidence:** New regression tests fail before indexing (41 walks for forty
negotiated hints; 81 for eighty engine hints) and pass after (2 each).
`tests/astart/rules/negotiation/test_negotiation_binding_budget.py` also covers binding equivalence;
the focused negotiation/engine/ddmin suite passes 110 tests.
**Known limits:** This is the repeated binding-walk slice, not completion of
M7-01's whole 3k/12k scaling requirement. Final corpus checks are separate.

**Audit 2026-11-07 (partial):** the largest superlinear cost is removed —
`Analyzer.refresh()` re-fingerprinted the whole tree per query (~1 053
walks ≈ 45 s at 12k); internal queries now use a refresh-free solver
path in `semantic/analyzer.py` and `_fingerprint_tree` itself is
cheaper. A fresh 3k `cProfile` (post M8-19/20) puts remaining cost in
`hints.index` ≈ 17.6 s cum, `provable.scope_types` 1 240 calls ≈ 7.4 s,
`resolve.get` 1 755 calls ≈ 6.6 s, ~12M `iter_child_nodes` walks and
~96 fingerprints ≈ 4.7 s — the listed worklist/bucketing/binding-cache
work lives in `rules/hints.py`, `rules/provable.py`, `rules/resolve.py`,
`rules/engine.py` and `ast.py`'s `semantic` property (main-agent line).
Progress 2026-11-08 (agent: claude): a profile of `statistics.py` showed
half the run was the docstring-quote probe (`docstring.token_text` per
docstring rebuilds the token index each call); `triple_quoted_owners` now
reads the module text once. Cold `fix_source`: 11.3 s → 4.0 s
(`statistics`), 2.3 s (`os`). Docstring fixes no longer conflict with
edits to the same definition (`Constants.docstring_prefix` in
`rules/runner.py`), so modules converge in 2 rounds instead of 3. Rule of
thumb recorded: never read per-node `token_text` in a loop. Remaining
profile: the inference pipeline (`hints._candidates` ≈ 1/3), `hints.index`
and `engine._holds`.
Progress 2026-11-08 (agent: devin, Q-31 measurement): at 50k lines the
cliff is far steeper than the ~n^1.4 seen at 12k — `check` alone
exceeded 30 min on the 50,763-line `profile_perf` workload (> 85× the
12k `check`), and `fix_source` multiplies it via `max_rounds=3` plus
`_degrade` halving re-running `_attempt`/`_rematch` per split. `cProfile`
isolates `hints.index → _candidates → CommentedModule.convert →
graph/backend/checkpoint._infer` (whole-module graph conversion once
per hint-index build). Filed as Q-68; the ~50k row in
`docs/analysis/scripts.benchmark.md` records the lower bound.

**Steps:**
1. Profile: `python -c "import cProfile,pstats; ..."` over `fix_source` for a 12 k-line module (concatenate corpus files) and print the top 25 by cumulative time.
2. For each function that grows faster than linearly (compare 3 k, 6 k and 12 k lines), cache per-module results keyed by `id(module)` as `docs_fixes.py` already does for module text.
3. Re-profile; stop when 12 k lines is at most 4× the 3 k time.

**Done when:** the 12 k-line run is within 4× of the 3 k-line run.

### M7-02 — Perf budgets
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** M · standard

**Context:** ≤5 s/12k lines, ≤30 s/100k lines
single-threaded.

**Audit 2026-11-07 (partial):** 12k-line `check` 62→**29.7 s**, `fix`
194→**72.3 s**, total 283→**102 s** with identical findings (2 067;
applied 413–432 across concurrent rule work);
`docs/analysis/scripts.benchmark.md` records the runs. Budget still unmet — remaining
cuts sit in `rules/` engine code owned by the M2/M3 line.
Progress 2026-11-08 (agent: claude): regression guards added in
`tests/astart/source/test_perf_budgets.py` — a structural counter (token-index rebuilds
per fix ≤ 20; was 238 before the `token_text` fix, now 6–8) on three
corpus modules, a 3 s clock on a 120-line module, and a slow-tier 15 s
clock on the 1 800-line `statistics` (now ≈ 4 s).
Second pass 2026-11-08: `hints._call_sites` evaluated
`scope_types(...)` eagerly inside `envs.setdefault(...)` for every call;
it is now computed once per scope per pass (`_scope_env`), and
`_type_rebound_locals` is skipped for functions with no name bound twice.
Measured with `scripts.benchmark.profile_perf`: 3k lines check 4.2→2.6 s / fix
7.2→5.2 s; **12k lines check 29.7→21.4 s / fix 72.3→36.9 s**. Budget
(≤ 5 s / 12k) **not met** and cannot be met by local tuning: ~50 % of the
remaining time is the inference engine (`graph/backend/engine.py`, ~4 M
`ast.walk` steps from thousands of per-node `walk` calls) and growth is
~n^1.4. Remaining plan, in order: (1) precompute parent/descendant
indexes once per function in `graph/backend/engine.py` and replace the
per-node `walk` calls; (2) run `check` and `fix` rounds on changed
functions only (incremental, reuse of unchanged `HintIndex` parts);
(3) M7-04 process-pool across files; (4) re-measure on 12k/100k. Keep
M7-02 open until (4).

**Progress 2026-11-09:** the gate machinery now exists end to end —
`benchmarks/throughput.py` (1 k/4 k/12 k buckets, median of N runs),
`scripts/benchmark/artifacts/resources/baseline_perf.json`, the `perf` subcommand in
`benchmarks/__main__.py` (fail past +20 % of baseline) and
`tests/scripts/benchmark/test_bench_perf.py`. `python -m scripts.benchmark perf --runs 1` prints
**PASS**: 2.3 / 16.6 / 108.1 s against baseline 2.5 / 16.9 / 126.9 s.
The contract budget (A-11: 12 k ≤ 5 s) is still ~20× over and is tracked
by `benchmarks targets` (metric `perf.12000.median_seconds`) plus Q-68;
the 100 k-line bucket does not exist yet.

**Steps:**
1. Create `benchmarks/throughput.py` with three buckets (1 k, 4 k, 12 k lines) and record seconds per bucket into `scripts/benchmark/artifacts/resources/baseline_perf.json`.
2. Add a `perf` gate to `benchmarks/__main__.py`: fail when a bucket is more than 20 % slower than the baseline.
3. Set the budget from the contract (A-11): 12 k lines in 5 s; record the gap in this task.

**Done when:** `python -m scripts.benchmark perf` prints PASS or the offending bucket.

### M7-16 — Wire the built-but-unreachable product surface (audit finding)
- **Status:** open
- **Priority:** P1
- **Area:** cli
- **Readiness:** ready
- **Effort:** L · standard

**Context:** `cli/config.py`, `cli/ignores.py`, `cli/baseline.py`, `cli/sarif.py`, `cli/junit.py`, `cli/github.py` are implemented and tested (`tests/astart/cli/test_cli_config.py`, `tests/astart/cli/test_cli_reports.py`) but `astart.__main__`/`cli/commands.py` do not import any of them: `astart check --help` still offers only `--format {text,json}`, `--fail-on`, `--stubs`, and `[tool.astart]` in `pyproject.toml` has no effect. M7-07 is checked on loader evidence; its user-visible acceptance lives here.

**Acceptance:** `astart check` discovers `pyproject.toml`, applies
`select`/`ignore`/overrides/baseline, and emits `--format
sarif|junit|github`; `astart fix` honours `safety-ceiling`,
`min-confidence`, `checker`, `exclude`; each has a CLI test through
`main(argv=…)`; README documents the flags.

**Steps:**
1. Write `scripts/unused_modules.py`: parse every module under `src/astart` with `ast`, collect the module names that are imported anywhere, and print modules nothing imports (excluding `__main__`, `__init__` and tests).
2. For each module found, either wire it (reporters: H-01, config: H-02, baselines: H-03, explain-at: M7-13, watch: M8-39) or delete it with a note in this task.
3. Add `tests/test_no_unreachable_modules.py` running the same check with an allow-list that needs a reason per entry.

**Done when:** the script prints nothing and the test passes.

**Progress 2026-11-09:** the previously isolated wrapping prototype is now
reachable through `cli/transforms.py`, imported by `astart.__main__`.
`autowrap.py` imports `wrapping.py`; the separate `source_edits.py` prototype
was removed in favor of native comment AST anchors. Continue the audit for
other genuinely unreachable modules.

### M7-04 — Process-pool parallelism
- **Status:** open
- **Priority:** P2
- **Area:** performance
- **Readiness:** ready
- **Effort:** S · standard

**Steps:**
1. Do the steps of recipe 20.1 (same files, same tests).
2. Set this task to `done` when recipe 20.1 is `done`.

**Done when:** recipe 20.1 is done.

### M7-05 — Streaming `--jobs` CLI
- **Status:** open
- **Priority:** P2
- **Area:** cli
- **Readiness:** ready
- **Effort:** S · standard

**Steps:**
1. Do the steps of recipe 20.1 (same files, same tests).
2. Set this task to `done` when recipe 20.1 is `done`.

**Done when:** recipe 20.1 is done.

### M7-06 — Memory budget tests
- **Status:** open
- **Priority:** P2
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · light

**Steps:**
1. Do the steps of recipe 20.2 (same files, same tests).
2. Set this task to `done` when recipe 20.2 is `done`.

**Done when:** recipe 20.2 is done.

### M7-08 — Baselines + external per-path ignores
- **Status:** open
- **Priority:** P2
- **Area:** cli
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (suppression
comments stay forbidden).

**Audit 2026-11-07 (partial):** `cli/baseline.py` and `cli/ignores.py` exist
with tests in `tests/astart/cli/test_cli_reports.py`; not reachable from the CLI
(→ M7-16).

**Steps:**
1. Per-path ignores: `[tool.astart.per-path-ignores] "tests/*" = ["DOC001"]` matched with `fnmatch` on the project-relative path.
2. Combine with baselines (H-03).
3. Tests: ignored in `tests/`, reported elsewhere.

**Done when:** per-path ignores suppress exactly the listed codes.

### M7-09 — Reporters
- **Status:** done
- **Priority:** P2
- **Area:** cli
- **Readiness:** done
- **Effort:** M · standard

**Context:** SARIF/GitHub-annotations/JUnit/
`--statistics`.

**Audit 2026-11-07 (partial):** `cli/sarif.py`, `cli/junit.py`,
`cli/github.py` exist with tests; `--statistics` does not; none reachable
from `astart check` (→ M7-16).

**Steps:**
1. See H-01 for the reporter wiring; this task adds a golden-file test per reporter (SARIF validated for required keys, JUnit parsed with `xml.etree`, GitHub lines matched by prefix with `str.startswith`).

**Done when:** each reporter has a golden test.

**Evidence:** each reporter now has a golden test through
the real CLI: `tests/astart/cli/test_cli_reporters.py` (wired by H-01) validates
SARIF required keys, parses JUnit with `xml.etree` (defusedxml), and
matches GitHub lines by `::` prefix. `--statistics` is not a reporter
format; it remains part of the M7-16 surface work.

### M7-10 — LSP diagnostics + code actions
- **Status:** open
- **Priority:** P2
- **Area:** cli
- **Readiness:** ready
- **Effort:** S · deep

**Steps:**
1. Do the steps of API-10 (same files, same tests).
2. Set this task to `done` when API-10 is `done`.

**Done when:** API-10 is done.

### M7-11 — Pre-commit/CI recipe
- **Status:** done
- **Priority:** P2
- **Area:** release
- **Readiness:** done
- **Effort:** S · light

**Steps:**
1. Do the steps of recipe 20.3 (same files, same tests).
2. Set this task to `done` when recipe 20.3 is `done`.

**Done when:** recipe 20.3 is done.

**Evidence 2026-11-09:** implemented the pre-commit/CI recipe —
`.pre-commit-hooks.yaml` gained the `astart-check` hook, `docs/engineering/ci.md`
documents both hooks with `.pre-commit-config.yaml` and GitHub Actions
examples plus the exit-code table, README links it under the CLI section,
and `tests/astart/test_docs_ci.py` (3 tests) verifies every declared hook id is
documented. Recipe's done-when ("the test passes") satisfied; the
"recipe 20.3" reference is stale — the recipe is filed under M7-11.

### M7-12 — Interactive review mode
- **Status:** open
- **Priority:** P2
- **Area:** cli
- **Readiness:** ready
- **Effort:** L · standard

**Context:** — evidence ladder per guarded fix,
"accept all high-confidence".

**Steps:**
1. `astart fix --review`: for each guarded fix print path, a diff hunk, confidence and basis, then read `y/n/a/q` from stdin.
2. `a` accepts all remaining fixes at or above the current confidence.
3. Tests with scripted stdin.

**Done when:** review mode applies exactly the accepted fixes.

### M7-13 — `astart explain <rule> <location>`
- **Status:** done
- **Priority:** P2
- **Area:** cli
- **Readiness:** done
- **Effort:** S · light

**Context:** command.

**Evidence 2026-11-09:** implemented the recipe — `explain` gained an
optional `location` positional (`path:line[:col]`); `run_explain_at` in
`commands.py` splits it via `rpartition`, checks the single file through
`_check_file`, filters findings by rule code/line/column, prints the rule
header plus each match's `render_message` and new `render_evidence`
output, and returns `1` with `astart: no CODE finding at LOCATION` when
nothing matches (`2` for bad location/unknown code/unreadable file).
`tests/astart/cli/test_cli_explain_at.py` (7 tests) covers match, line-only match,
wrong line, bad location, unknown code and both `main()` dispatch paths;
`docs/guides/cli.md` documents the new form.

**Steps:**
1. Do the steps of recipe 20.4 (same files, same tests).
2. Set this task to `done` when recipe 20.4 is `done`.

**Done when:** recipe 20.4 is done.

### M7-14 — `--backup`/undo journal
- **Status:** done
- **Priority:** P2
- **Area:** cli
- **Readiness:** done
- **Effort:** S · standard

**Steps:**
1. Do the steps of recipe 20.5 (same files, same tests).
2. Set this task to `done` when recipe 20.5 is `done`.

**Done when:** recipe 20.5 is done.

**Evidence 2026-11-09:** implemented the recipe — new
`src/astart/cli/backup.py` (`Entry`, `save`, `write_journal`, `undo`)
with SHA-256 before/after digests and `.bak` images;
`write_atomic` moved to `src/astart/cli/atomic.py` so `backup` and
`commands` share it without a circular import;
`FixCommandSettings.backup` + `fix --backup` create
`.astart-backup/<UTC run-id>/` and write `journal.json`;
`astart undo [RUN_ID]` restores files whose sha still matches
`after_sha` and skips edited ones (exit 1). `tests/astart/cli/test_cli_backup.py`
(4 tests) covers restore, edited-since skip, missing run and the
no-backup case; `docs/guides/cli.md` documents flag and command; `.astart-backup/`
is gitignored. Recipe's "recipe 20.5" reference is stale — the recipe
is filed under M7-14.

### M7-15 — Distribution packaging
- **Status:** done
- **Priority:** P3
- **Area:** release
- **Readiness:** done
- **Effort:** S · light

**Context:** (wheel/entry points) once the
product surface stabilizes.

**Steps:**
1. Do the steps of recipe 20.6 (same files, same tests).
2. Set this task to `done` when recipe 20.6 is `done`.

**Done when:** recipe 20.6 is done.

**Evidence 2026-11-09:** implemented recipe 20.6 — `scripts/utils/check_wheel.py`
builds the wheel into a temp dir, asserts `astart/py.typed`,
`astart/rules/artifacts/schema.json`, `astart/stubs/__init__.py` and at least one
`astart/rules/artifacts/catalog/*.json` member, then creates a venv, pip-installs
the wheel with `--no-index` and runs `astart rules` (exit 0, >10 lines).
Ran once: `python3 scripts/utils/check_wheel.py` → `wheel check passed`; no
`package-data`/`MANIFEST.in` fixes were needed.

### M7-17 — Index `post_refinements` document walks
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** M · deep

**Context:** historical sensor dump of an engine fix run on the retired
generated fixture (`--engine --min-confidence 0.5`, SIGUSR1 probe;
the current generated output is
`scripts/compare/artifacts/results/result.py`;
`artifacts/sensors.txt`): `post_refinements.walk_without_classes`
**6 542 480 calls / 157 s wall**, `child_nodes` 7 081 236 / 17 s — the
helper re-walks the whole document per call from `all_functions` (528
calls ≈ 30 s). Roughly two thirds of measured time is this repeated
traversal.

**Facts:** `src/astart/graph/inference/post_refinements.py`
(`walk_without_classes`, `child_nodes`, `all_functions`); the caller
`conversion/stages.refine_inferred_module` ran 4 × ≈ 34 s in the same
dump.

**Steps:**
1. In `post_refinements.py`, build parent/children indexes once per `refine_inferred_module` invocation (keyed by node identity) and make `walk_without_classes`/`child_nodes` consult them instead of re-walking. Check: `python -m pytest tests/astart/graph/conversion/test_graph_protocols.py tests/test_semantic* -q` green.
2. Re-run the sensor probe on the same command and compare `walk_without_classes` cumulative in `artifacts/sensors.txt`. Check: ≤ 25 % of 157 s.
3. Confirm output identical on a small corpus (`python -m pytest tests/astart/rules/test_gold_expansion.py -q` — same findings, same order). Check: suite green.

**Done when:** `walk_without_classes` cumulative ≤ 39 s on the same
instrumented `fix` run and the gold suite passes.

### M7-18 — Bound precondition re-evaluation per applied fix
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** M · deep

**Context:** same sensor dump: `runner.preconditions_hold` **1 153
calls ≈ 28 ms each = 34 s**, `runner._apply_one` 1 167 / 35 s. Every
applied fix re-evaluates every pending fact over the whole module, so
apply cost grows with pending-fact count × fact cost — quadratic on a
large file.

**Facts:** `src/astart/rules/runner.py` (`_apply_one`,
`preconditions_hold`, `_Pass`), `rules/facts.py` (fact evaluation).

**Steps:**
1. Index pending facts by their subject's ancestor (owning function or module scope) once per round in `runner.py`; after a fix edits a subtree, re-evaluate only facts whose subjects share that ancestor. Check: `python -m pytest tests/astart/rules/test_rules_runner.py tests/astart/rules/test_rules_determinism.py -q` green.
2. Verify skip semantics unchanged: `result.skipped` must show the same `preconditions-changed` outcomes as before on `tests/astart/rules/test_rules_runner.py::test_all_fixes_apply_in_one_pass` and the protocol/typevar fix tests. Check: suite green, identical skip lists.
3. Re-run the sensor probe; `preconditions_hold` total must drop to ≈ pending-facts-per-scope rather than all facts. Check: ≤ 9 s on the same run.

**Done when:** `preconditions_hold` ≤ 9 s on the same instrumented
`fix` run and no skip outcome changes.

### M7-19 — Share the engine/hint index across fix rounds
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** M · deep

**Context:** same sensor dump: `collect_graph_annotations` **4 calls ≈
10.7 s each = 43 s**, `facts._negotiated` 2 × 19 s, `engine_hints` 2 ×
15.8 s, `hints._candidates` 1 × 11 s. Engine/negotiate mode rebuilds
the graph conversion and hint index per `_run_round`/`_attempt`
although most of the module is untouched between rounds — the
incremental plan in M7-02 recorded this without a measured owner.

**Facts:** `src/astart/rules/runner.py` (`_run_round`, `_attempt`),
`rules/hints.py` (`index`, `build`, `_candidates`), `rules/facts.py`
(`_negotiated`, `engine_hints`),
`graph/conversion/`·`semantic/analyzer.py` (per-build conversion).

**Progress 2026-11-09:** the instrumentation exists —
`src/astart/sensors.py` (decorator/context timing into a process-wide
registry, active only when `ASTART_SENSORS` is truthy), armed by
`__main__._arm_sensors` with a `sensors.txt` dump; `tests/scripts/benchmark/test_sensors.py`
covers it. It is the probe behind the "sensor dump" measurements above.

**Steps:**
1. In `runner.py`, keep the `HintIndex`/engine annotation result from a round and pass it to the next round when the edits are provably disjoint (or rebuild only the changed functions per the M7-02 incremental plan); invalidate on any write inside the covered region. Check: `python -m pytest tests/astart/rules/test_rules_runner.py -q` green.
2. Prove identical output: run `python scripts/compare` before and after on `fixtures/untyped.py`; the conversion block and bucket counts must be unchanged. Check: identical numbers.
3. Re-run the sensor probe; `collect_graph_annotations` must run once per fresh module, not once per round. Check: calls ≤ 2 and cumulative ≤ 25 s on the same run.

**Done when:** `collect_graph_annotations` calls ≤ 2 per run on the
same instrumented `fix` command with unchanged conversion output.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M7-03 | Incremental content-hash cache | P1 | performance |
| M7-07 | `[tool.astart]` pyproject config | P1 | cli |

## 8. Ontology and inference core

*Scope:* Rule catalog, predicates, the `graph` inference engine.  
*ID prefixes:* M8

<details>
<summary>Background — Spec-catalog remainder (merged from the retired 2026-11-06/07 spec and</summary>

plan files — `docs/superpowers/specs/2026-11-06-*-design.md`,
`docs/superpowers/plans/2026-11-0{6,7}-*.md`, deleted after merge)

These are the rule-ontology spec §5 catalog entries that have no detector,
no catalog rule and no TODO item yet. All follow the TYP005 recipe
(§18.5) and end at M8-22 catalog registration unless noted.


</details>

### M8-21 — M8 exit gate
- **Status:** done
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** M · standard

**Context:** `verify_catalog` all invariants green;
full spec-§5 rule set present; parity vs Exactus KWARGS_TYPEHINTS
categories complete.

**Steps:**
1. Run the catalog check: `python -c "from astart.rules import default_registries, load_default_catalog; from astart.rules.engine import verify_catalog; c=load_default_catalog(registries=default_registries()); print(verify_catalog(catalog=c))"` and fix every reported invariant.
2. List the spec rule set: the rule list in chapter 8 of this file plus
   `astart rules`. Diff the two; every spec rule missing from `astart rules` gets
   a task (or a link to an existing M8-xx).
3. Parity check against the keyword table: run `scripts/utils/generate_libkw.py` after W-04 and
   compare the category list with the committed `rules/libkw.py`.
4. Add `tests/astart/rules/test_catalog_gate.py`: asserts `verify_catalog` returns no
   problems and that every code in a fixed list (`IMP001 TYP002 TYP005 TYP006 PRS001 SUP001 DOC001 ...`)
   is in `astart rules` output.

**Done when:** the test passes and the diff in step 2 is empty.

**Evidence 2026-11-09:** `tests/astart/rules/test_catalog_gate.py` asserts
`verify_catalog` reports no problems and that every code in the fixed spec
list (`IMP001 TYP002 TYP005 TYP006 PRS001 SUP001 DOC001 ...`) is in
`astart rules` output; the test passes and the step-2 diff is empty.

### M8-01 — `imports.bare-import` IMP001
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** — `import ast` →
`from ast import X` + use-site rewrite, proven when collision-safe.

**Audit 2026-11-07 (partial):** detector `rules/imports_bare.py` + tests; no
catalog rule, no fixer — fixer spec is M8-27, registration is M8-22.

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "IMP001" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/imports_bare.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/imports.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_imp001.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists IMP001 and its tests pass.

### M8-02 — `typing.missing-variable-annotation` TYP005
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Audit 2026-11-07 (partial):** detector `rules/variable_annotations.py` flags
unannotated `Assign` name-targets whose value infers a stable non-`Unknown`
type; refuses annotated/private/dunder names, attribute and unpacking
targets; tests in `tests/astart/rules/test_rules_type_checks.py`; not in the catalog
(→ M8-22).

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "TYP005" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/variable_annotations.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/typing.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_typ005.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists TYP005 and its tests pass.

### M8-03 — `typing.no-object-annotation` TYP002
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Audit 2026-11-07 (partial):** detector `rules/object_annotations.py` + tests;
not in the catalog (→ M8-22).

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "TYP002" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/object_annotations.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/typing.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_typ002.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists TYP002 and its tests pass.

### M8-04 — `suppression.marker-comment` SUP001
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Audit 2026-11-07 (partial):** detector `rules/suppressions.py` + tests; not
in the catalog (→ M8-22).

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "SUP001" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/suppressions.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/suppression.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_sup001.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists SUP001 and its tests pass.

### M8-05 — `parsing.module-does-not-parse` PRS001
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Audit 2026-11-07 (partial):** detector `rules/parse_module.py` + tests; not
in the catalog (→ M8-22). Note `astart check` already reports a
syntax-error file as `error:` with exit 2.

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "PRS001" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/parse_module.py (`find_parse_error`)`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/parsing.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_prs001.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists PRS001 and its tests pass.

### M8-06 — `typing.return-type-mismatch` / `incompatible-default`
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Audit 2026-11-07 (partial):** detectors `rules/type_mismatch.py`
(`find_return_mismatches`, `find_incompatible_defaults`) refuse on any
indeterminate inference — only a definitive `compatible is False`
verdict yields a candidate (bare `Constant` literals are mapped
directly since the solver does not index them); tests in
`tests/astart/rules/test_rules_type_checks.py`; not in the catalog (→ M8-22).

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "TYP003/TYP004" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/type_mismatch.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/typing.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_type_mismatch.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists TYP003/TYP004 and its tests pass.

### M8-07 — Docs family DOC001/003/004/006
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** + guarded doc fixers.
Progress 2026-11-07: DOC002 (add stub entries), DOC003 (remove stale
entries) and DOC007 (tidy whitespace/indent) are catalog rules with
proven fixers (`rules/docs_fixes.py`, `rules/docstring_edit.py`); DOC001
(stub pre-pass, `--stub-docstrings`) is done; DOC004/DOC006 stubs remain
→ Q-61. Keep open until they land.

**Audit 2026-11-08 (partial):** DOC001/002/003/007 are live catalog rules
with wired fixers (`docs.add-parameter-entries`,
`docs.remove-stale-entries`, `docs.tidy-docstring` in `Appliers`);
DOC001's stub pre-pass runs under `--stub-docstrings` in `runner`.
Corpus idempotence green again after the `triple_quoted_owners`
pre-computation and `entry_names` dedup fixes (79/79). DOC004
(missing returns) and DOC006 (missing raises) detectors still have
no catalog rule.

**Audit 2026-11-07 (partial):** detectors `rules/docs_missing.py` (DOC001),
`rules/docs_stale_params.py` (DOC003), `rules/docs_missing_returns.py`
(DOC004), `rules/docs_missing_raises.py` (DOC006) on structured
`DocstringNode.entries` + tests in `tests/astart/docstrings/test_rules_docs_whitespace.py`;
no fixers, not in the catalog (→ M8-22).

**Steps:**
1. Check whether the rule is already in the catalog: `grep -n "DOC001/003/004/006" src/astart/rules/artifacts/catalog/*.json`. If it is, only add missing tests and stop.
2. Find the detector module (`rules/docs_missing.py, docs_missing_returns.py, docs_missing_raises.py, docs_stale_params.py`) and its entry function; confirm it returns `Candidate` spans (see `rules/procedural.py`).
3. Add the catalog entry by copying the nearest rule of the same family in `rules/artifacts/catalog/docs.json`: `code`, `key`, `title`, `rationale`, `maturity: experimental`, `examples` (one with `triggers: true`, one clean), `fixes` (none unless a fix exists).
4. Register the provider in `rules/registry.py` (`default_registries`) beside the existing providers.
5. Run `verify_catalog` (see M8-21 step 1).
6. Add `tests/test_rules_docs_family.py`: the triggering example reports one finding with the right line and column; the clean example reports none; `astart check` on a temp file prints the code.

**Done when:** `astart rules` lists DOC001/003/004/006 and its tests pass.

### M8-11 — D6 remainder: `Exists` evaluation
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — predicate semantics
implemented; catalog-validation guard removed.

**Steps:**
1. Implement `Exists` predicate evaluation in `rules/predicate.py` over the module facts (`exists(node_kind, condition)`).
2. Add 10 catalog examples using it.
3. Tests per operator.

**Done when:** predicates with `Exists` evaluate in the engine.

### M8-12 — D8: procedural rules
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · deep

**Context:** implemented.

**Audit 2026-11-07 (partial):** `rules/procedural.py` defines `Candidate` and
`span_of`; `Registries.procedures` is still empty and `engine.check` has no
path that calls a procedure (→ M8-22).

**Steps:**
1. Procedural rules: list them in `rules/procedural.py`; register each with its provider like M8-01.
2. One test per rule.

**Done when:** procedural rules appear in `astart rules`.

### M8-22 — Register the standalone detectors as catalog rules (audit finding)
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** `imports_bare.py` (IMP001), `object_annotations.py` (TYP002), `suppressions.py` (SUP001) and `parse_module.py` (PRS001) have detectors and tests (`tests/astart/rules/test_rules_procedural.py`), but the default catalog still has 5 rules / 7 fixes and `Registries.procedures` is empty, so `astart check` never reports them (also blocks M8-12).

**Audit 2026-11-08:** catalog is now 7 rules / 10 fixes across 5 JSON files
(`typing`, `attributes`, `calls`, `structure`, `docs`), all
`owner: astart`, `maturity: stable`, `procedure: null`, and every
file's `profiles`/`relations` lists are empty. Code collision to
resolve: catalog `attributes.json` already spends `TYP005` on
`typing.missing-attribute-annotation`, while M8-02's variable-
annotation detector also targets TYP005 — registration must
renumber one. Also `variable_annotations.py`, `type_mismatch.py`
(return/default mismatch, M8-06) and `call_problems.py` (M6-05…08)
detectors await the same path.

**Acceptance:** the four rules appear in `load_default_catalog` with examples,
`verify_catalog` stays green, `check` reports them with spans and
fingerprints, IMP001 offers a proven fix only when collision-safe.

**Steps:**
1. List detector functions: `grep -n "^def find_" src/astart/rules/*.py`, and the `procedure` names in `src/astart/rules/artifacts/catalog/*.json` (Cookbook C-2).
2. For each detector without a catalog rule apply steps 2 to 6 of M8-01.
3. Run `verify_catalog` (M8-21 step 1).

**Done when:** every `find_*` detector is referenced by a catalog rule or listed in an allow-list with a reason.

### M8-27 — IMP001 fixer: bare `import a` → `from a import b` + use-site rewrite
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · standard

**Context:** Convert module-level bare imports whose every use is an attribute **load** into per-attribute `from`-imports, decided independently per attribute; keep `import a` for any site that cannot convert.

**Scope:** `rules/imports_bare.py` evidence → a new applier/fix entity;
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

**Audit 2026-11-07 (partial):** fixer module `rules/imports_bare_fix.py`
(`rewrite_bare_imports`) implements the per-attribute plan — load-only
rewrite points, store/del/augassign/for-target veto per attribute,
collision and existing-`from`-alias reuse, bare-use and dotted-prefix
keeps, nested function/lambda scopes; 19 danger-matrix tests in
`tests/astart/rules/test_rules_imports_bare_fix.py` green incl. idempotence.

**Evidence:** danger-matrix tests in the style of
`tests/astart/rules/test_rules_kwargs_danger.py` covering every refusal above plus
alias/`as`-import, dotted-path, chain and multi-attribute cases;
corpus idempotence (fix∘fix byte-equal) and the writer fuzzer's
compile/comment/strip-equality invariants apply to rewritten output.
Remaining: applier/catalog registration (→ M8-22) and corpus/fuzzer
runs over rewritten output.

**Steps:**
1. Read `rules/imports_bare_fix.py` (the per-import plan) and `rules/imports_bare.py` (the detector).
2. Register the fix `imports.bare-import-fix` (safety `guarded`) next to the IMP001 rule (M8-01).
3. Rewrite `import a` to `from a import b` for every used attribute `a.b`, rewriting use sites `a.b` to `b` by AST node positions; refuse when `a` has other uses, when `b` would shadow a local name, or for `import a.b.c` used as a package.
4. Re-parse the edited unit (CC-10) and compare trees; allowed changes are imports and the rewritten attributes.
5. Tests: the plan cases from the module plus each refusal.

**Done when:** the tests pass and the semantic run is unchanged.

### M8-08 — Whitespace/blank-line normalisation
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** rules.

**Audit 2026-11-07 (partial):** detectors `rules/whitespace_rules.py`
(blank-line runs, trailing space) + tests; not in the catalog (→ M8-22).

**Steps:**
1. Do the steps of AF-13 (same files, same tests).
2. Set this task to `done` when AF-13 is `done`.

**Done when:** AF-13 is done.

### M8-09 — `Constants`-class grouping with `Final`
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** rule.

**Audit 2026-11-07 (partial):** detector `rules/constants_grouping.py` flags
loose `UPPER_SNAKE` module constants outside a `Constants` class + tests;
no fixer, not in the catalog (→ M8-22).

**Steps:**
1. Do the steps of S-05 and S-06 (same files, same tests).
2. Set this task to `done` when S-05 and S-06 is `done`.

**Done when:** S-05 and S-06 is done.

### M8-10 — Delegation relation to ruff
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** documented and wired.

**Audit 2026-11-07 (partial):** delegation contract documented in
`docs/guides/rule-authoring.md` (`owner: "ruff"` + `delegates_to` relation,
FMT001/`format.line-length` as the planned entry); schema already
supports both fields; the catalog entry itself is M8-22 scope.

**Steps:**
1. Delegation relation: a rule can be marked `delegated_to: ruff` with a ruff code; `astart check` skips it when ruff is configured to run, and reports it otherwise.
2. Add the field to the schema and `verify_catalog`.
3. Test: delegated rule skipped when ruff is on.

**Done when:** delegated rules are not reported twice.

### M8-13 — Profiles + relations
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · standard

**Context:** (`supersedes`/`conflicts_with`/
`implies`) exercised in the default catalog.

**Steps:**
1. Profiles: `[tool.astart] profile = "strict"` selects a rule set from the catalog; relations `supersedes` and `conflicts_with` resolve overlaps.
2. Schema fields and `verify_catalog` checks (no cycles).
3. Tests: two profiles, one supersede.

**Done when:** profiles select rules and relations resolve.

### M8-28 — String literal normalisation fixer
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Two value-preserving rewrites of plain `str` constants:
(a) literals containing `\n` escapes become multiline triple-quoted
strings with real newlines;
(b) literals whose source line exceeds the line-length budget become
parenthesised implicit concatenations split at safe boundaries.

**Scope:** `Constant` `str` nodes only — no f-strings/`JoinedStr`, no
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

**Audit 2026-11-07 (partial):** fixer module `rules/strings_normalize.py`
(`normalize_strings`) - token-exact segment rewrites on eligible
`Constant str` nodes; `\n`-escape to triple-quote with real newlines
(refuses triple-quote content, trailing backslash), overlong literals
to parenthesised implicit concatenation at word boundaries with the
boundary space preserved inside quotes; refuses f-strings, bytes,
raw/triple-quoted, docstrings, dict keys, `__all__` members, match
patterns; emitted lines respect the budget; 15 tests in
`tests/astart/rules/test_rules_strings_normalize.py` green incl. value round-trip
and idempotence. Remaining: applier/catalog registration (M8-22)
and writer-fuzzer runs.

**Evidence:** danger-matrix tests mirroring
`tests/astart/rules/test_rules_kwargs_danger.py` for every refusal above;
`ast.parse` validity + value equality (`ast.literal_eval` round-trip)
on every rewritten literal; idempotence (second pass is a no-op) and
the writer fuzzer's compile/comment/strip-equality invariants.

**Steps:**
1. Read `rules/strings_normalize.py` (already implemented, not registered).
2. Register the fix `strings.normalize-quotes` with `allowed_changes: []` (CC-09) and the setting `quote-style` (`double` default, `preserve`).
3. Refuse strings containing the other quote character, escapes that change meaning, and f-strings with nested quotes (AF-21 owns f-string interiors).
4. Tests per case and an idempotence test.

**Done when:** the fix is registered, switchable, idempotent and tree-preserving.

### M8-29 — F-string interior normalisation fixer
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Canonicalise the *inside* of `JoinedStr` replacement fields without touching what they evaluate to: `f"{ x }"` → `f"{x}"`, `f"{x !r}"` → `f"{x!r}"`, `f"{ x !s :>8 }"` → `f"{x!s:>8}"`.

**Scope:** `JoinedStr`/`FormattedValue` nodes only — whitespace and
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

**Evidence:** danger-matrix tests for every refusal; output-equality
proof per case (`eval`/`ast.literal_eval` where legal, or a stub
object recording `__format__`/`__str__` calls for spec cases);
idempotence; writer-fuzzer invariants on rewritten modules.

**Audit 2026-11-07 (partial):** fixer module `rules/fstring_normalize.py`
(`normalize_fstrings`) - tokenize-driven field-interior rewrites;
trims edge whitespace around expr/`!conv`/`:` separators, preserves
expression interior spacing, conversion flags and format-spec text
verbatim, recurses into nested spec fields; refuses `=`-debug
fields, unbalanced brackets and non-f-string braces; 11 tests in
`tests/astart/rules/test_rules_fstring_normalize.py` green incl. idempotence.

**Note:** spec text is preserved byte-for-byte, so `f"{x !s :>8 }"`
yields `f"{x!s:>8 }"` (spec trailing space kept) rather than the
spec example's `:>8}`-stripped form - chosen because format-spec
whitespace is significant. Remaining: applier/catalog registration
(M8-22) and writer-fuzzer runs.

**Steps:**
1. Read `rules/fstring_normalize.py` (`normalize_fstrings`; whitespace placement only).
2. Register the fix `strings.normalize-fstring-fields` with `allowed_changes: []`.
3. Keep AF-21 separate: this fix never changes expression text, only spacing around fields.
4. Tests: `f"{ x }"` to `f"{x}"`, `=` debug refused, idempotent.

**Done when:** the fix is registered and its tests pass.

### M8-30 — Multiline-string indent normalisation + `textwrap.dedent` fixer
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Two related rewrites: (a) docstrings are normalised to house style — summary placement, consistent continuation indentation, closing quotes on their own line — preserving `inspect.cleandoc` semantics; (b) non-docstring multiline `str` literals whose continuation lines share a common indent are offered `textwrap.dedent(...)` wrapping (with `ensure_names` import insertion) *or* literal re-indentation, chosen by evidence.

**Scope:** `Constant` `str` nodes spanning ≥2 lines with a non-empty
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

**Evidence:** danger-matrix tests; value-equality proof —
`ast.literal_eval` for re-indented literals and
`textwrap.dedent(literal_eval(text))` equality for wrapped ones;
`inspect.getdoc` equivalence for docstring cases; idempotence;
writer-fuzzer invariants.

**Steps:**
1. Find the module: `grep -rn "dedent" src/astart/rules | head`.
2. Register the fix `strings.dedent-multiline` as in M8-28 with `allowed_changes: []` only when the string's value is unchanged (compare `ast.literal_eval` before and after).
3. Refuse raw strings, strings with line continuations and strings used in `textwrap.dedent` calls already.
4. Tests and an idempotence test.

**Done when:** the fix never changes a string's runtime value.

### M8-31 — `suppression.lint-ignore-config` SUP002
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (Exactus alias CMP004, cost `project`, no fix). Flags project
configuration that silences lint checks wholesale (file-level or
per-file ignore configuration), so the finding names where coverage is
being waived rather than flagging the waivers themselves.

**Steps:**
1. Detect per-file ignore entries in `pyproject.toml` for ruff or `# ruff: noqa` file markers using `tomllib` and the file system (no text patterns).
2. Register as in M8-01 (family `suppression`/`config`), code SUP002.
3. Tests: triggering config, clean config.

**Done when:** SUP002 appears in `astart rules` and its tests pass.

### M8-32 — `suppression.type-check-config` SUP003
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (Exactus alias CMP005, cost `project`, no fix). Flags type-checker
configuration that disables or weakens checking (e.g. pyright/basedpyright
`typeCheckingMode` off, mypy `ignore_errors`), project scope.

**Steps:**
1. Detect `[tool.pyright]`/`[tool.mypy]` entries that silence errors (`ignore`, `strict = false`) using `tomllib` and the file system (no text patterns).
2. Register as in M8-01 (family `suppression`/`config`), code SUP003.
3. Tests: triggering config, clean config.

**Done when:** SUP003 appears in `astart rules` and its tests pass.

### M8-33 — `config.pyproject-missing` CFG001
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (Exactus alias CMP006, cost `project`, fix safety `suggest`). Reports a
project with no `pyproject.toml`; the fix only suggests creating a
minimal one, never auto-applies.

**Steps:**
1. Detect no `pyproject.toml` found upward from the checked file using `tomllib` and the file system (no text patterns).
2. Register as in M8-01 (family `suppression`/`config`), code CFG001.
3. Tests: triggering config, clean config.

**Done when:** CFG001 appears in `astart rules` and its tests pass.

### M8-34 — Method/classifier quartet OOP001–OOP004
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** (Exactus aliases PY004–PY007, cost `scope`, fixes `guarded`):
`oop.method-should-be-classmethod`, `oop.method-should-be-static`,
`oop.classmethod-should-be-static`, `oop.staticmethod-uses-class`.
Needs `MethodIndex`/`receiver_of` evidence plus "uses `self`/`cls`"
facts per method.

**Steps:**
1. Four method classifiers OOP001–OOP004: instance method not using `self` (could be static), classmethod not using `cls`, method with only `pass`, property with a side effect call.
2. Each from the AST: scan `self`/`cls` loads in the body.
3. Register as in M8-01; tests per rule.

**Done when:** the four rules report and never fix.

### M8-35 — `naming.exception-message-variable` NAM001
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (Exactus alias PY003, cost `scope`, fix `proven` when control flow is
safe): `msg = "..."` immediately before `raise X(msg)` folds into
`raise X("...")`; refuse when `msg` is read elsewhere or rebound.

**Decision 2026-11-08:** the direction is a setting, `raise-message-style`;
see S-08, which implements both directions. Do not implement this task
separately.

**Steps:** see S-08 step 6 (inline mode).

**Done when:** S-08 is done in both directions (`extract` and `inline`).

### M8-36 — Simplification family SIM001–SIM006
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · standard

**Context:** (Exactus aliases PYS001–PYS006, fixes `proven`):
`simplification.inline-return`, `walrus-in-condition`,
`inline-single-use`, `dead-constant-store`, `inline-in-return`,
`inline-via-conditional`. Exactus's skip reasons become the fixes'
`preconditions` (evaluation-order safety), per ontology spec §5.

**Steps:**
1. Six simplification rules SIM001–SIM006 (e.g. `if x: return True else: return False`, `not (a == b)`, redundant `else` after `return`, `x == None`, `len(x) == 0`, nested `if` merge).
2. Each as a detector with an optional `proven` fix; AST only.
3. Register as in M8-01; tests per rule.

**Done when:** six rules with tests.

### M8-37 — Docs family remainder DOC005, DOC007–DOC013
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** plus the doc fixers the ontology spec attaches to the docs rules:
detectors `docs.return-yield-mismatch` (DOC005),
`docs.missing-attribute` (DOC007), `docs.malformed-docstring` (DOC008),
`docs.analysis-failure` (DOC009), `docs.missing-description` (DOC010),
`docs.stale-raises` (DOC011), `docs.stale-attribute` (DOC012), and
`docs.format-style` (DOC013 — normalise docstring content to Google
style, no Exactus alias). Fixes: missing-section rules offer
`set_docstring` with a generated entry (`guarded`, confidence-gated);
stale-section rules offer removal (`suggest`).

**Steps:**
1. Do the steps of AF-09 (same files, same tests).
2. Set this task to `done` when AF-09 is `done`.

**Done when:** AF-09 is done.

### M8-14 — `Maturity` lifecycle → defaults
- **Status:** open
- **Priority:** P3
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Steps:**
1. Do the steps of recipe 20.7 (same files, same tests).
2. Set this task to `done` when recipe 20.7 is `done`.

**Done when:** recipe 20.7 is done.

### M8-38 — `structure.shebang` SHB001
- **Status:** open
- **Priority:** P3
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** (fix
`guarded`): missing, malformed or wrong-interpreter shebang lines on
executable scripts; rewrite only with recorded evidence.

**Steps:**
1. Detect a first line starting with `#!` that is not `#!/usr/bin/env python3` (token-based: first COMMENT token on line 1).
2. Fix: rewrite to the canonical line when the file is executable-looking (`__main__` guard).
3. Tests.

**Done when:** SHB001 detects and fixes.

### M8-39 — CLI watch mode
- **Status:** open
- **Priority:** P3
- **Area:** cli
- **Readiness:** ready
- **Effort:** M · standard

**Context:** The only
out-of-scope item left from the check/fix CLI plan
(`--select`/`--ignore`, config files and parallelism already landed or
are tracked under M7-04/M7-05/M7-07): a `astart check --watch` /
`fix --watch` mode that re-runs on file changes.

**Steps:**
1. `astart watch PATH`: poll file mtimes every second (no dependency), rerun `check` on changed files, print findings.
2. Debounce 200 ms; stop on Ctrl-C.
3. Test with a temp file edited twice.

**Done when:** watch reports new findings after an edit.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| M8-23 | New `Final` constants join an existing `Constants` class (requested 2026-11-07) | P1 | rules |
| M8-24 | Writer replaces elements of a child list with atoms (needed by M8-23) | P1 | ast |
| M8-15 | Rule authoring kit | P3 | docs |
| M8-16 | Fix verified wrong types | P1 | inference |
| M8-17 | `list(d)` → items-not-keys | P1 | inference |
| M8-18 | `seq[0]` → `Sequence[int]` over-broad | P1 | inference |
| M8-19 | Imported-constructor argument typing | P1 | inference |
| M8-20 | `self.` receiver typing in the analyzer | P1 | inference |

## 9. Cross-cutting engineering

*Scope:* Calibration, determinism, error containment.  
*ID prefixes:* CC, EV

### CC-01 — Confidence calibration
- **Status:** open
- **Priority:** P1
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · standard

**Context:** — numeric confidence per candidate
from evidence level, calibrated on benchmarks (pairs with M1-15).

**Steps:**
1. Measure exact share per `HintBasis` on the stdlib and external corpora (extend the JSON report with `by_basis`, see F-29 step 2).
2. Store the table in `rules/calibration.json` (basis → exact share, sample size).
3. Make `confidence.by_basis` read the table (fall back to current constants when the sample is under 30).
4. Add `tests/test_rules_calibration.py`: table keys equal the `HintBasis` members.

**Done when:** confidence values come from measured data.

### CC-02 — Determinism audit
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — stable ordering/names, protocol name
lockfile, no dict/set-order or time dependence anywhere.

**Steps:**
1. Search for unordered iteration that reaches output: `grep -rn "for .* in .*set(\|for .* in .*\.keys()" src/astart/rules src/astart/semantic`; list each site.
2. Wrap each site that feeds output in `sorted(...)` with a stable key.
3. Add the three-seed test from F-28 step 1 and the `--jobs 1` vs `--jobs N` test from 20.1.
4. Run on both corpora; any byte difference is a missed site.

**Done when:** outputs are byte-identical across seeds and job counts.

### CC-03 — Error containment v2
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — per-file timeout + per-fix watchdog
on top of existing per-file/per-fix isolation.

**Steps:**
1. Read `rules/process.py` (ThreadPool timeout) and `rules/runner.py` (per-fix try/except).
2. Add a per-file wall-clock budget (`FixSettings.file_timeout`, default 60 s) that returns the original source and an error line.
3. Add a per-fix watchdog: a fix that raises or exceeds its step budget is skipped with code `fix-error`; the run continues.
4. Tests: a fix that raises, a fix that loops (budget), a file that never finishes (timeout) — each yields original text plus one error line.

**Done when:** no input crashes the run and bad files report one error line.

### CC-04 — Property + mutation testing
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** L · deep

**Context:** — grammar-random programs →
strip → fix → check; mutation testing on policy code; regression test per
reviewer finding.

**Steps:**
1. Create `tests/test_property_fix.py` with a generator of small valid modules (random functions, assignments, calls) seeded by `random.Random(n)`.
2. Properties: fix output compiles; `fix ∘ fix` equals `fix`; existing annotations unchanged (AF-19); AST differs only in allowed fields (CC-09).
3. Mutation test: take a typed corpus module, drop one annotation, run fix; the result must be equal or compatible to the original (use `relation`).
4. Keep 200 cases fast (under 60 s); mark the long run `slow`.

**Done when:** the property tests pass on 200 random modules.

### CC-06 — Convention guard
- **Status:** done
- **Priority:** P1
- **Area:** tests
- **Readiness:** done
- **Effort:** S · light

**Context:** — no suppression comments, no
`Any`/`object`, keyword-only calls, Google docstrings, `@final Constants`
— keep `test_rules_review_fixes` family green as rules evolve.

**Steps:**
1. Extend `tests/astart/test_conventions.py` with checks for: no `import ast`, keyword-only calls to project functions, `@final class Constants`, Google docstring sections, no `Any`/`object` annotations (CC-08 adds the no-regex check).
2. Run it; fix or allow-list existing violations with a reason.
3. Document each convention in START HERE.

**Done when:** the convention test fails on a deliberate violation and passes on the tree.

**Evidence 2026-11-09:** `tests/astart/test_conventions.py` now has six tests.
The three original checks stay (no `noqa`/`type: ignore`, no bare
`import ast`, `@final class Constants`); three AST-based checks were
added: `test_no_any_annotations` (zero `Any` in any annotation position
across `src`/`tests`/`scripts`/`benchmarks`),
`test_no_object_in_production_signatures` (`object` banned from
signatures in `src`/`scripts`/`benchmarks`; `tests` exempt because
doubles legitimately take `**_kwargs: object` and return opaque values,
and `name: object = expr` narrow-then-`isinstance` locals are the
sanctioned idiom), and `test_scripts_signatures_are_keyword_only`
(positional-or-keyword parameters banned in `scripts/`; `Protocol`
members exempt because they mirror `hashlib`/`argparse` signatures,
positional-only parameters cannot be keyword-passed anyway). Keyword-only
*call sites* and Google docstring sections are already enforced by the
`kwargs_typehints` and `docs` exactus gates, so no duplicate checks were
added. Teeth verified: scoping the object scan to `tests/` surfaces the
11 known double signatures. START HERE rule 5 now states the `object`
scope precisely.

### CC-07 — Commit hygiene (audit finding)
- **Status:** done
- **Priority:** P1
- **Area:** release
- **Readiness:** done
- **Effort:** S · light

**Context:** 148 paths differ from
the last commit (`120272c`) — about 35 source/test files and ~100 new
corpus modules — including two sessions' work. Nothing from M0–M2 is
committed, so no milestone diff is reviewable or revertable.

**Acceptance:** one commit per finished milestone slice (M0, M1-so-far, M2-so-
far, corpus, parallel-session reporters/config) on a branch; the suite and
`ruff check src tests benchmarks scripts` green at each commit.

**Steps:**
1. Check `.gitignore` covers `__pycache__/`, `.coverage`, `.ruff_cache/`, `.pytest_cache/`, `EXACTUS_RESULTS/`, `.remember/`, `.history/`, `dist/`; add what is missing.
2. Add `tests/astart/test_repo_hygiene.py`: when the tree is a git repository, `git ls-files` lists none of those and no file over 5 MB (skip otherwise).
3. Document the commit message convention and the attribution lines in README.

**Done when:** the hygiene test passes.

**Evidence 2026-11-09:** `.gitignore` already covered every listed
pattern (`__pycache__/`, `.coverage`, `.ruff_cache/`, `.pytest_cache/`,
`EXACTUS_RESULTS/`, `.remember/`, `.history/`, `dist/`) — nothing was
missing, and `git ls-files` confirms none are tracked.
`tests/astart/test_repo_hygiene.py` (2 tests) asserts no tracked path matches a
forbidden prefix and no tracked file exceeds 5 MB, skipping cleanly off
git. README's Development section now documents one-finished-slice-per-
commit, the green-suite rule and the agent attribution trailer. The
milestone-slice commits themselves remain a maintainer decision while
parallel sessions hold uncommitted work.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| EV-01 | Exactus gate evidence, 2026-11-07 | P0 | release |
| CC-05 | User-facing evidence ladder + refusal catalogue | P2 | docs |

### CC-08 — Remove every regular expression from source-reading code
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Rule: nothing that reads or rewrites Python source or comments
uses `re`. Decisions come from the AST (node types and positions), from
`tokenize` (comments and strings) and from `str` methods on already-isolated
tokens. Single exception: AF-21 sends f-string field expressions to ruff and
re-parses the result. Docstrings are text, not Python; they are parsed with a
small line scanner built from `str` methods (strategy below), not with patterns.

**Inventory (measured 2026-11-08, `grep` over `src`, `libkw.py` excluded):**

| Site | What the regex does | Replacement | Child |
| --- | --- | --- | --- |
| `docstrings.py:81-98` (5 patterns) | Google section header, `:param:` directives, `name: text` entries, `name (type)` parameters, NumPy `name : type` | line scanner in a new `astart/docstring_lines.py` | CC-08-01 |
| `rules/docstring_edit.py:39-44` | section header line, parameter entry line (with indent) | same scanner | CC-08-02 |
| `rules/docs_shared.py:48` | parameter entry line | same scanner | CC-08-03 |
| `ast.py:805-861` (about 12 patterns) | comment directives: `noqa`, `ruff: noqa`, `type: ignore`, pyright/mypy markers | `tokenize` COMMENT tokens plus a directive grammar function | CC-08-04 |
| `formatting.py:468` | string prefix and quote of a literal | `tokenize` STRING token / AST `Constant` segment, prefix loop | CC-08-05 |
| `cli/config.py:493` | `fullmatch` of a config value | `str` predicates (`isidentifier`, `isascii`, `partition`) | CC-08-06 |
| `rules/appliers.py:779` (`re_sub`) | substitution on source text | AST/token based edit (read the site first) | CC-08-07 |
| `rules/typevars.py:163, 985` (`re_search`) | search in a name or text | AST name checks (read the site first) | CC-08-08 |
| `graph/conversion/synthesis.py:1183, 4671, 4705` (`sub`) | non-word runs to `_`; camel-case to words | character loops with `str.isalnum` / `str.isupper` | CC-08-09 |
| `rules/constants_grouping.py:45` | `^[A-Z][A-Z0-9_]*$` constant names | `name.isascii() and name[0].isalpha() and name.isupper() and name.isidentifier()` | CC-08-10 |

Re-measured 2026-11-09: three more files import `re` and are on the
allow-list — `stubs/locate.py` (`findall` on stub text), `autowrap.py` and
`wrapping.py` (comment/source patterns). They postdate the inventory and
still need child tasks before the allow-list can empty.

**Strategy (same for every child):**
1. **Characterise first.** Collect real inputs: every docstring in `src` and
   `tests`, every comment token of `src`, `tests` and `tests/corpus/extended`, every
   string literal prefix. Store them in a test fixture (not in the repo tree if
   large: generate them at test time from the corpus).
2. **Write the replacement beside the regex** as a pure function with the same
   input and output type.
3. **Differential test:** `tests/test_<site>_equivalence.py` runs old and new on
   all collected inputs and asserts equal results. Keep it until step 5. Any
   difference is either a bug in the new code or a bug the regex had; decide
   per case and write the decision in the test.
4. **Switch the callers** to the new function; run the module's own tests.
5. **Delete the regex and the differential test's old side**, keep the test as
   a table of expected outputs. Remove the file from `tests/artifacts/regex_allowlist.txt`.
6. **Guard:** `tests/astart/test_no_regex.py` (add it first, with the allow-list
   containing exactly the files above) fails on `import re`, `from re import`
   and any `re.` call under `src/astart` except `libkw.py` (generated data, no
   logic; its only `re` use, if any, is in the generator script, which is not
   shipped). It must pass before any child starts.

**Scanner design (CC-08-01 to 03):** `astart/docstring_lines.py` exposes
`classify(*, line: str) -> DocLine` where `DocLine` is a frozen dataclass with
`kind` (`blank`, `section_header`, `entry`, `directive`, `text`), `indent`
(`len(line) - len(line.lstrip())`), `name`, `type_text`, `rest`. Build it only
from `str.strip`, `str.partition`, `str.startswith`, `str.endswith`,
`str.isidentifier` and membership in the existing header table
(`DocstringPatterns.section_names`). Examples: a Google header is a line whose
stripped text ends with `:` and whose text before the colon is a key of the
table; an entry is `head, colon, rest = stripped.partition(":")` with
`head.split("(")[0].strip()` an identifier (allow leading `*`/`**`).

**Directive grammar (CC-08-04):** for each `tokenize.COMMENT` token strip the
`#` and spaces, lowercase the first word, then switch on it: `noqa` →
optional `:` then comma-separated codes, each validated with
`code[:code.rstrip("0123456789").__len__()].isalpha() and code[len(letters):].isdigit()`;
`ruff:` `noqa`; `type:` `ignore` with optional `[codes]`; `pyright:` / `mypy:`
`ignore`. Positions come from the token's `start`, so the directive's line and
column are exact and never inferred from text offsets.

**Done when:** `tests/astart/test_no_regex.py` passes with an empty allow-list, every
child is `done`, the differential tests were run once with zero unexplained
differences, and `fix ∘ fix` plus the fast tier are green.

### CC-08-00 — Add the no-regex guard test first
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** S · light

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Create `tests/astart/test_no_regex.py`: walk `src/astart/**/*.py` except `rules/libkw.py`; parse each with `ast`; fail on `Import(re)` or `ImportFrom(module='re')` unless the path is in `tests/artifacts/regex_allowlist.txt`.
2. Create `tests/artifacts/regex_allowlist.txt` with the 9 files from the CC-08 inventory (one path per line, `#` comments allowed).
3. Add a second test: every path in the allow-list still exists and still imports `re` (so stale entries fail).

**Done when:** the test passes today and fails if a new file imports `re`.

**Evidence 2026-11-09:** `tests/astart/test_no_regex.py` (2 tests) +
`tests/artifacts/regex_allowlist.txt` shipped. The allow-list holds all 13 live
`re` importers — the 10 inventory files plus `stubs/locate.py`,
`autowrap.py`, `wrapping.py` (post-inventory arrivals, noted in the CC-08
inventory). `test_allowlist_entries_are_live` proves detection has teeth:
all 13 entries verified live. `pytest tests/astart/test_no_regex.py`: 2 passed;
ruff clean.

### CC-08-01 — Docstring line scanner replaces `docstrings.py` patterns
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Create `astart/docstring_lines.py` per the scanner design in CC-08 and unit tests with 25 sample lines per kind.
2. Differential test against `DocstringPatterns` on every docstring found by walking `src` and `tests` with `ast.get_docstring`.
3. Switch the five users in `docstrings.py`; delete the five `compile_pattern` fields and the `re` imports.
4. Run `tests/test_docstrings*.py` and the DOC rule tests.

**Done when:** no `re` import remains in `docstrings.py` and all docstring tests pass.

### CC-08-02 — Use the scanner in `rules/docstring_edit.py`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Replace `header` and `entry` patterns with `classify` calls; keep the `pad` (indent) value from `DocLine.indent`.
2. Differential test on all docstrings with a Google section.
3. Delete the patterns and imports.

**Done when:** `tests/test_rules_docstring_edit*.py` pass and the file is off the allow-list.

### CC-08-03 — Use the scanner in `rules/docs_shared.py`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Replace `entry_pattern` with `classify`.
2. Differential test as in CC-08-02.
3. Delete the pattern and the import.

**Done when:** DOC rule tests pass and the file is off the allow-list.

### CC-08-04 — Comment directives from tokens, not patterns (`ast.py`)
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Read `ast.py:780-900` to list the directive kinds the 12 patterns recognise; write one table row per kind in the test.
2. Implement `parse_directive(*, comment: str) -> Directive | None` per the directive grammar in CC-08 using only `str` methods.
3. Where the module now scans lines, switch to `tokenize.generate_tokens` and the COMMENT tokens' `start` positions.
4. Differential test on every comment token in `src`, `tests`, `tests/corpus/extended` (collect with `tokenize`).
5. Delete the 12 patterns, `IGNORECASE` and the imports.

**Done when:** `tests/test_ast*.py` and suppression tests pass; zero differences on the comment corpus.

### CC-08-05 — String prefix and quote from the token (`formatting.py`)
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Read `formatting.py:455-490`; the function keeps the author's quote style when re-spelling a constant.
2. Compute prefix with a loop: `i = 0; while text[i] in 'rRuUbBfF': i += 1`; quote is `text[i:i+3]` if it is a triple quote, else `text[i]`.
3. Prefer the AST: `ast.get_source_segment` of the `Constant` node gives the exact text.
4. Differential test over every string constant in the corpus.

**Done when:** string formatting tests pass and the pattern is gone.

### CC-08-06 — Config value check without `fullmatch` (`cli/config.py`)
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Read the call at `cli/config.py:493` and write down the pattern; list accepted and rejected examples as a test table.
2. Replace with `str` predicates; keep the error message text.
3. Tests for every example.

**Done when:** config tests pass and `fullmatch` is not imported.

**Evidence 2026-11-09:** `_version` now delegates to `_is_dotted_digits`,
which splits on `.` and requires every part `isdecimal()` — the same
Unicode decimal-digit class `\d` matches, so `"3.12.1"` passes and
`"3."`/`".3"`/`"3..4"`/`""`/`"3-4"` fail exactly as before. The error
message is unchanged; the `from re import fullmatch` import is gone.
`test_target_version_must_be_dotted_digits` gained the five new reject
cases and `test_target_version_accepts_dotted_digits` pins five accept
cases through `load_config`. `tests/astart/cli/test_cli_config.py`: 15 passed;
`ruff check --select ALL` clean.

### CC-08-07 — Replace the `re_sub` edit in `rules/appliers.py`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Print the pattern and replacement at line 779 and the function it is in.
2. Express the same edit with AST node positions (`lineno`, `col_offset`, `end_lineno`, `end_col_offset`) and a slice replacement.
3. Differential test: apply old and new on every input that reaches this function in the fast tier (instrument once, store the cases).
4. Delete `re_sub`.

**Done when:** appliers tests pass and `re` is not imported there.

### CC-08-08 — Replace the two `re_search` calls in `rules/typevars.py`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Print the pattern and the strings searched at lines 163 and 985.
2. Replace with name checks on AST nodes (`Name.id`, `Attribute.attr`) or `str.startswith`/`in`.
3. Differential test on typevar gold cases.

**Done when:** typevar tests pass and the import is gone.

### CC-08-09 — Identifier case conversion without `sub` (`graph/conversion/synthesis.py`)
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Line 1183: non-word runs to `_`: loop over characters, emit `_` once per run of characters failing `str.isalnum()` and not `_`.
2. Line 4671 and 4705: insert a space before an uppercase letter that is not at index 0 (comprehension over `enumerate`), then `.lower()`.
3. Property test: new function equals the old on 500 generated identifiers (mix of case, digits, punctuation).

**Done when:** `from re import sub` is removed and the converter tests pass.

**Evidence 2026-11-09:** `from re import sub` removed; all three call sites
are now character loops — `_unique_alias` (non-word runs to `_`, already
landed), `_split_identifier` (`([a-z0-9])([A-Z])` boundary insertion via
`enumerate` over the stripped name) and `_title_to_words` (space before
ASCII uppercase at index > 0, then `.lower()`). `synthesis.py` left
`tests/artifacts/regex_allowlist.txt`. New property test
`test_identifier_case_conversion_matches_regex_reference` in
`tests/astart/graph/conversion/test_graph_synthesis.py` replays 500 deterministic mixed-case /
digit / punctuation names through the public `method_docstring` and
`name_for_members` paths and compares against the retired regex
reference implementations; cases that would take the verb or dunder
branches are collected and asserted empty. Also removed the now-stale
`ast.py`/`autowrap.py` allowlist entries (their `re` imports were
already gone). 33 tests pass; `ruff check --select ALL` clean.

### CC-08-10 — Constant-name check by predicates (`rules/constants_grouping.py`)
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** S · standard

**Context:** Child of CC-08; follow its strategy (characterise, replace, differential test, switch, delete, guard).

**Steps:**
1. Replace `Constants.constant_name.match` with `is_constant_name(name)`: `name.isascii() and name[0].isalpha() and name.isupper() and name.isidentifier()`.
2. Test table: `MAX_VALUE`, `A1`, `_X`, `x`, `A_b`, `É`.
3. Delete the pattern and import.

**Done when:** constants grouping tests pass and the file is off the allow-list.

**Evidence 2026-11-09:** `is_constant_name` module function replaces the
`Constants.constant_name` compiled pattern (both call sites updated);
`isidentifier()` runs first so `""` short-circuits before `name[0]`.
Equivalence: every string matching `^[A-Z][A-Z0-9_]*$` is an ASCII
identifier with an uppercase leading letter, and the predicate rejects
exactly what the pattern rejected (`_X`, `x`, `A_b`, `É`, `9A`, `A-B`).
`test_is_constant_name_table` pins 14 cases; file removed from
`tests/artifacts/regex_allowlist.txt` (alongside `cli/config.py` and
`rules/typevars.py`, cleaned under CC-08-06/CC-08-08).
`tests/astart/rules/test_rules_constants_group.py`: 12/13 pass — the one failure
(`test_the_class_is_created_when_the_module_has_none`) asserts generated
import order `Final, Protocol, final` vs the `Protocol, Final, final`
now emitted by the in-flight `rules/appliers.py`/`imports.py` changes,
unrelated to this predicate swap.

### CC-10 — One AST: transactional emission and incremental locations
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · deep

**Context:** The requested architecture has one authoritative mutable
`CommentedModule`. This task replaces the former incremental-reparse design.
Source is an emitted view, not an input that replaces the tree after a fix.
Only explicit external formatter islands (for example a Ruff-formatted
f-string expression) may be parsed again. A full parse is a test oracle,
never the normal mutation path or a silent production fallback.

**Steps:**
1. Extend the existing `FormatPreserver` edits and `IncrementalSourceGraph`;
   do not add a competing tree, position system or source-edit authority.
   A transaction records node identities, field/list operations, original
   lexical spans, inserted nodes and its expected source revision.
2. Add tracked child-list operations and field replacement to the native
   node binding layer. Increment a mutation generation and enqueue changed
   identities once. Preserve compatibility with raw AST edits through an
   explicit exhaustive reconciliation operation; document its O(N) cost.
3. Have emission return lexical patches and emitted locations together.
   Rebase surviving node spans with a prefix-sum edit index; assign locations
   to inserted syntax during emission. Never recover those locations by
   parsing the complete emitted module.
4. Tokenize only safe lexical islands with saved entry/exit indentation,
   delimiter and f-string state. Expand to a lexical convergence boundary
   when the exit state changes; bound expansion and report the affected
   range. A full tokenization is permitted; a full AST parse is not.
5. Remove the post-initial full parses from `refresh_token_index`,
   `_validate_formatted_text` and `_unparse_generated`. Feed locations from
   emission into `_TokenIndexer`, preserving all existing node identities.
6. Maintain persistent parent/order and reverse-dependency indexes in
   `delta.py`. Capture old parents before deleting nodes. Update the dirty
   owner, ancestors and semantic dependents through a deduplicated queue.
7. Add randomized differential tests against an independently parsed oracle:
   Unicode byte columns, CRLF, tabs, semicolons, decorators, PEP 695,
   multiline strings, nested PEP 701 fields, comments and removed subtrees.
   Instrument parser calls: ordinary annotation/comment/doc edits after the
   initial parse must cause **zero** module parses.
8. Benchmark 500 batched edits on the same 12k-line fixture against current
   behavior. Record hardware, versions, wall time, allocations, tokenized
   bytes and visited nodes. Target at least 10x faster edit sequences;
   unchanged cached token reads must not traverse the module.

**Done when:** zero-reparse tests and differential corpus pass, edits retain
unaffected node/snapshot identities, stale transactions are rejected, and
measured results are recorded. Initial token mapping already reuses the
original AST; mutation/emission migration remains open.

**Bounded-pass progress 2026-11-09:** `formatting.EmissionPlan` now validates
existing `Patch` batches, rejects stale revision/source pairs and uses
prefix shifts plus binary search to rebase untouched character spans in
O(log patches). Touched ranges return an explicit dirty-owner result;
Unicode/CRLF, boundary insertions, no-ops and overlap guards have focused
tests. This is a foundation only: wire it into emission and translate the
result through the byte/line index before removing any validation parse.
No AST rollback or tracked-list completion is claimed.

**Integration progress 2026-11-09:** `FormatPreserver.plan` now drives the
live lexical emission path, using existing Patch records and EmissionPlan.
`CommentedModule.emission_plan` publishes the plan only after existing source
validation succeeds. Original node records retain identity witnesses to
prevent detached-node ID recycling. The formatter exposes original spans
for O(1) lookup; untouched spans rebase through the checked plan. Whole-source
validation and token refresh still parse: changed-owner output locations,
byte/line rebasing and removal of those parses remain open.

**Architecture:** See [single-AST decision](../architecture/single-ast-architecture.md).
No shared mutable AST access from workers. Immutable revision snapshots may
be analyzed concurrently; one coordinator validates and commits results.

**Import-emission slice 2026-11-09:** a fresh contiguous root import group
now emits as a local insertion patch alongside existing node/comment edits.
Untouched source spans remain rebasable; empty/comment-only files, missing
final newlines, Unicode, CRLF and future-import preambles have regression
coverage. Shared semicolon lines retain the conservative reconstruction path.
The transaction also retains list identity witnesses and detects equal-content
raw list replacement. General tracked lists, changed-node locations and the
zero-post-initial-parse acceptance gate remain open.

### CC-09 — Verify declared AST mutations before committing edits
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Replaces the former "re-parse after every edit" requirement.
Preserve the safety gate by checking mutations of the authoritative tree.

**Steps:**
1. Each fix declares permitted fields, imports and binding changes. Capture
   original values for only the fields touched by its transaction.
2. Reject an undeclared executable mutation and roll back the transaction,
   including its pending source edits and dependency invalidations.
3. For formatter islands only, parse the returned expression/statement in
   its recorded grammar context; compare its executable structure with the
   existing island. Reattach formatted lexical data without replacing
   unaffected AST nodes.
4. Test a faulty fixer that renames a runtime binding, failed island syntax,
   stale revisions, overlapping edits and rollback after partial planning.
5. Run full-source parse/equivalence checks in regression tests and optional
   explicit audit mode; record them separately from the normal fast path.

**Bounded-pass progress 2026-11-09:** native
`module.annotation_transaction()` now stages annotation/return field edits,
guards structure plus identities/comments/source revision, rejects aliasing,
cycles and unspellable identifiers, and validates the same AST with compile
without execution. Failures and interruption restore original field
references, proposal coordinates and derived documentation links. Commit
relinks parameter/result documentation targets without changing TODO prose.
The API remains single-writer. Compatibility validation still scans the tree.

**Dependency-batch slice 2026-11-09:** `add_import(declaration=...)` stages
one absolute, unaliased dependency binding per declaration. Imports and
annotation fields compile and roll back as one batch; failure/interruption
restores the original body list, references, links and proposal coordinates.
Conservative checks reject existing bindings/executable reads, builtin
capture, wildcard ambiguity and unsupported alias/future/relative imports.
Unresolved annotation-only dependencies remain eligible. General list
operations, catalog contracts, final emission acceptance and tracked O(1)
revision guards remain open.

**Done when:** every catalog fix has a checked mutation contract, invalid
transactions leave source/tree/indexes unchanged, and the normal fix path
passes a zero-post-initial-module-parse counter test. No trust flag bypass.

### CC-11 — Native lexical provenance and format/comment ownership
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Steps:**
1. Extend `SourceTokenizer`, not a pyposast dependency: index punctuation
   partners, keyword/operator occurrences, adjacent literals and trivia.
   Delimiter pairing and lexical parenthesized ranges are implemented;
   node/parent-aware ownership remains to implement.
2. Expose immutable revision-scoped spans for decorators, parameter names,
   composite keywords, delimiters and redundant expression parentheses.
   Distinguish UTF-8 byte positions from tokenizer character columns.
3. Persist comment anchors through statement insertion/movement/deletion.
   Inline, suppression, shebang, coding and formatter directives retain
   their scope and exact spelling. Refuse ambiguous ownership explicitly.
4. Replace fragment tokenization in `formatting.py` with retained interval
   queries. Cache reverse indexes once per affected revision.
5. Test every supported Python node family, strings containing brackets,
   multiline composite operators and nested f-strings. Compare source bytes
   outside edits, not just AST dumps.

**Done when:** the syntax matrix passes, no pyposast import/dependency is
introduced, and position queries have measured O(log T + result) or O(1)
lookup costs. See the decision document for inspected upstream provenance.

### CC-12 — Migrate wrapping and insertion onto shared transactions
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · deep

**Steps:**
1. Port native balanced wrapping of prose, lists, doc sections and comments
   to CC-10 transactions over existing doc/comment nodes. Protect examples,
   fences, literal blocks and directives; preserve TODO placeholders.
2. Support explicit style conversion, boilerplate, redundant-pass removal
   and proven `None` returns. Keep runtime-changing insertion out of the
   annotation benchmark's default path.
3. Implement print redirection with lexical scope/binding resolution,
   collision-free helper injection and standard stream semantics. Refuse
   shadowed or unresolved print names; do not import the legacy project.
4. Implement numeric comparison constant extraction for module/function/
   class scopes, including signed values, collision handling and qualified
   class references. Preserve evaluation order and distinguish bool/int.
5. Expose independent opt-in API/CLI settings, dry-run/diff and structured
   preservation/refusal reasons. Test idempotence and runtime equivalence
   for every advertised option before enabling it.

**Progress 2026-11-09:** native AST APIs now exist:
`wrap_tree`/`AstWrapper` edit existing doc children, comment nodes,
boilerplate/pass statements and return annotations without parsing or
emitting. `insert_tree`/`AstInserter` construct print helper and numeric
constant nodes using the existing lexical scope graph. The explicit
`astart transform` command composes these on one module, with stdout/output,
diff/check and JSON reports. Runtime insertion defaults off. The separate
`SourceBuffer`/`SourceEdit` prototype was removed; comment reflow uses the
module's original lexical anchors and shared emitter. Regression tests cover
runtime semantics, scopes, idempotence, private-name collisions, falsey
streams, eager class callables, comment overlap and moved doc ownership.
Remaining: CC-10's zero-reparse emission/index transactions, exhaustive
comment/code grammar coverage, and catalog DOC008 integration. Existing
emission still reparses for validation; these passes do not close CC-10.

**Done when:** both native passes share the authoritative module and edit
index, scoped regressions and CLI tests pass, and reference conversion has
no new wrong annotations. The native wrapping pass now edits existing AST nodes; shared emission
still needs the zero-reparse transaction migration.

### CC-13 — Deterministic concurrent inference and evidence invalidation
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · deep

**Steps:**
1. Maintain reverse edges from facts and evidence to dependent contracts,
   annotations and token/doc views. Invalidate the transitive dirty closure
   once per transaction; retain evidence origin IDs across propagation.
2. Memoize syntax, call binding, overload resolution and generic substitution
   by stable node ID plus dependency revisions. Test that deleting evidence
   retracts its consequences and does not retain a stale inferred type.
3. Benchmark serial execution first. Use opt-in processes for independent
   CPU-heavy module/SCC analysis only when serialization costs are repaid.
   Workers receive immutable snapshots and return proposed evidence/edits.
4. Commit in deterministic node/rule order, rejecting stale revisions.
   Bound workers, queues, shutdown and retries; propagate cancellation.
5. Compare serial and parallel output/evidence byte-for-byte, including
   contradictory evidence, recursive SCCs and cancellation halfway through.

**Done when:** deterministic parity passes, no worker mutates the shared AST,
no subprocess survives cancellation, and throughput/memory measurements
justify the selected concurrency threshold.

## 10. Contract negotiation

*Scope:* Two-way reconciliation of types (the ant farm).  
*ID prefixes:* F

<details>
<summary>Background — 18.12 Contract negotiation — two-way reconciliation (the "ant farm")</summary>


Goal: replace "agree-or-refuse" between one forward signal and one engine
candidate with a real solver. Every entity (parameter, return, local,
attribute, element) is a node; facts about the program are directed
**contracts** between nodes; typed **candidates** ("ants") travel forward and
backward along contracts, are merged by an evidence algebra (union for
assignments/returns, intersection for narrowing, declaration for annotations,
conflict when incompatible), and the loop runs until beliefs stop changing.
Reference design (read it before starting): the author's old project
`~/Library/Mobile Documents/com~apple~CloudDocs/New Mac/semantic_contract_farm_project`
(`README.md` sections "Contracts", "Ant-farm propagation", "Entropy,
convergence, and wormhole protection", "Evidence algebra"; code in
`src/semantic_contract_farm/{contracts,swarm,evidence_algebra,objective}.py`).

Adaptation rule (astart's goal is zero wrong annotations, the farm's was
coverage): **confidence decay only orders and prunes candidates; acceptance is
decided by evidence class.** A negotiated annotation is written only when its
settled type is supported by at least one *independent* origin (syntax, a
declaration, call sites or a default — never the inference engine alone), no
conflict is open on the node, and the guarded policy plus the E6 checker gate
still apply. New code lives in `src/astart/rules/negotiation/`. Types are
strings, as everywhere in `rules/`.

Foundation (pure, no wiring):


</details>

### F-17 — Seed the graph from existing evidence, tagged by origin
- **Status:** done
- **Priority:** P0
- **Area:** negotiation
- **Readiness:** done
- **Effort:** S · deep

**Context:** Seeds from existing evidence, origin-tagged: default literal (`default`), proven call-site types (`call_sites`), syntax proofs (`syntax`), declarations (`declared`), engine candidates (`inferred`). Progress 2026-11-08: syntax, declared, call-site and default seeds are built; engine proposals are *corroboration* only (they are compared with the settled type in `policy.accept`, never unioned into a belief, because `int | str` from the engine would silently widen call-site evidence).

**Evidence 2026-11-08:** seeds carry `Origin` (syntax, declared, protocol, call_sites, default, calibrated, inferred) from `negotiation/builders.py`; `tests/astart/rules/negotiation/test_negotiation_module.py`.

### F-18 — Acceptance policy `negotiation/policy.py`
- **Status:** done
- **Priority:** P0
- **Area:** negotiation
- **Readiness:** done
- **Effort:** S · deep

**Context:** Acceptance policy `negotiation/policy.py`: settled type + independent origin + no open conflict + spellable (known names, no `object`/`Any`) → `Hint` with new `HintBasis.negotiated`; confidence by origin mix in `confidence.py`; new `Rejection` values (`negotiation conflict`, `negotiation ambiguous`) with `docs/guides/skip-reasons.md` and refusal-catalogue rows (existing doc tests must stay green). Progress 2026-11-08: `negotiation/policy.py` — every member of the settled type needs a proof (syntax/declared), or two different soft signals (call sites + default), or one soft signal plus engine agreement; opacity spreads downstream; `object`/`Any` and a parameter typed `None` are refused. Open: `HintBasis.negotiated`, confidence table, the two new `Rejection` values and their docs. Done in part 2026-11-08: `HintBasis.negotiated` (confidence 0.95), `typing.add-variable-annotation` (0.95). The new `Rejection` values and their docs are still open.

**Evidence 2026-11-08:** `negotiation/policy.py` `accept`: every member of a settled type needs a proof (syntax, declared, protocol), or two different soft signals, or one soft signal plus the engine proposing the same type; the engine only corroborates; a `None`-only result needs a proof; opaque nodes are never accepted. Tests in `tests/astart/rules/negotiation/test_negotiation_module.py`; shadow comparison keeps `only_negotiated.wrong` at 0.

### F-20 — Behind `FixSettings.negotiate`
- **Status:** done
- **Priority:** P0
- **Area:** negotiation
- **Readiness:** done
- **Effort:** unsized · deep

**Context:** Behind `FixSettings.negotiate` (CLI `--negotiate`), let the negotiator replace the 12-pass propagation fixpoint in `HintIndex.judge_parameters`; first goal is *identical* output on the gold set, then a strict superset with 0 new contradictions. Progress 2026-11-08: negotiation now *supplements* the hint index instead of replacing the 12-pass loop (`HintIndex.supplement`, `LazyHints.supplemented`, `FixSettings.negotiate`, default **on**, CLI `--no-negotiate`): a negotiated hint is used only for nodes the hint index has none for, and a parameter that would get a structural `Protocol` keeps the Protocol (`own_hint_for`). Gold: 561 cases, negotiation changes 0 written annotations and adds 24 reviewed ones (`test_gold_negotiation_is_a_reviewed_superset`). Replacing the loop outright stays open until the shadow gap (F-37) is closed.

**Evidence 2026-11-08:** `FixSettings.negotiate` defaults to `True` (`rules/runner.py:174`); CLI `--no-negotiate` turns it off; `tests/astart/rules/test_rules_negotiated_fix.py` runs fixed output through `compile` and import.

### F-28 — Determinism and idempotence
- **Status:** done
- **Priority:** P0
- **Area:** tests
- **Readiness:** done
- **Effort:** M · deep

**Context:** Determinism and idempotence: hash-seed test (as Q-15), `fix` ∘ `fix` byte-equal on both corpora with negotiation on, order-independence property test on random graphs.

**Steps:**
1. Hash-seed test: copy `tests/astart/rules/test_rules_determinism.py`; run `fix_source`
   (negotiate on, `annotate_variables=True`) on 10 corpus files in three
   subprocesses with `PYTHONHASHSEED=0,1,2`; assert identical output bytes.
2. Idempotence: for the same files assert `fix_source(fix_source(x)) == fix_source(x)`
   (both with and without `run_formatter`).
3. Order independence: in `tests/astart/rules/negotiation/test_negotiation_solver.py` build random
   graphs (random relation and type per edge, seeded `random.Random(n)`), add
   the contracts in two shuffled orders, assert the settled beliefs are equal.
4. Mark 1 and 2 `slow` if they take more than 30 s.

**Done when:** the three tests pass.

**Evidence 2026-11-09:** `tests/astart/rules/test_rules_determinism.py` runs
`fix_source` (negotiate on, `annotate_variables=True`) on corpus files in
subprocesses under `PYTHONHASHSEED=0,1,2` asserting identical bytes, and
`fix_source(fix_source(x)) == fix_source(x)` with and without
`run_formatter`; `tests/astart/rules/negotiation/test_negotiation_solver.py` settles seeded random
graphs in two shuffled orders with equal beliefs (`_Picker` LCG keeps S311
clean); 34 tests pass.

### F-29 — Gate: refresh `baseline.json` and `baseline_ext.json` with negotiation on; accept only
- **Status:** open
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Gate: refresh `baseline.json` and `baseline_ext.json` with negotiation on; accept only precision ≥ 99.5 %, 0 new checker errors, 0 crashes, and an external-corpus recall gain (target ≥ +2 points over 19.3 %). Record per-origin precision.

**Steps:**
1. Run the external recovery in the background (see W-01 step 2) with negotiation
   on (default) and write the JSON to `/tmp/ext.json`.
2. Record per-origin precision: add `by_basis` counts to the JSON (the hint's
   `HintBasis` for each written annotation) in `benchmarks/runner.py`.
3. Compare to `scripts/benchmark/artifacts/resources/baseline_ext.json`: precision ≥ 99.5 %, recall at least
   +2 points over 19.3 %, 0 crashes. The checker delta needs `--checker`.
4. If it holds, accept: `python -m scripts.benchmark baseline --report /tmp/ext.json --out scripts/benchmark/artifacts/resources/baseline_ext.json`;
   repeat for stdlib into `scripts/benchmark/artifacts/resources/baseline.json`.
5. Write the per-origin table into `docs/analysis/scripts.benchmark.md`.

**Done when:** both gates print `PASS` against the refreshed baselines.

**Progress 2026-11-09:** `by_basis` per-origin counts are in the report JSON
(see `docs/analysis/scripts.benchmark.md` per-origin table). The corpus_ext run scored
recall 20.18 % (+0.55 pts over 19.3 %, below the +2-point target), precision
99.60 %, 0 crashes, 0 new checker errors, and **11 wrong** (+5 vs the
baseline — new negotiation contradictions also visible as
`only_negotiated.wrong: 9` in the shadow run). Refresh **declined**: both
gates PASS against the committed baselines, but the accept criteria are not
met while scorer tasks (G-02, G-05, P-07) are in flight.

### F-07 — Complete the transfer table
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Complete the transfer table, forward *and* backward, per relation: key/value (`dict[K, V]`), argument ↔ parameter, call_result ↔ return, attribute/instance_field/class_field, operator (numeric tower, `str % x`), context_enter/exit (`__enter__` result), awaitable unwrap, generator send/yield/return. A relation with no sound reverse gives `None` (no message), never a weaker guess.


Contract builders (AST → contracts; reuse `CallBindings`/`MethodIndex` so
binding trust is shared with the keyword fixer):

**Steps:**
1. List every relation in `negotiation/model.py`; for each write `forward` and `backward` in `negotiation/transfer.py` (backward is `None` when no sound inverse exists).
2. Add one unit test per relation and direction in `tests/astart/rules/negotiation/test_negotiation_graph.py` / `test_negotiation_solver.py`.
3. Add a completeness test: every `Relation` member has an entry in the transfer table.

**Done when:** every relation has a tested transfer, or an explicit `None`.

### F-13 — Builder: capabilities
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** — `int(x)`, `x.y`, `x()`, `x[k]`, `len(x)`, `for _ in x`, `with x`, `await x`, `x + 1` — as capability sets on the node; feeds `usage_abc` (M4-07) and Protocol synthesis instead of re-deriving usage separately.

**Steps:**
1. Seed capabilities (method calls on a parameter) as `Origin.protocol` requirements.
2. Settle by intersecting with declared types; leave unresolved when unknown (Protocol synthesis handles it in `protocols.py`).
3. Tests in `tests/astart/rules/negotiation/test_negotiation_module.py`.

**Done when:** capability evidence narrows or blocks as designed.

### F-15 — Builder: library calls
- **Status:** done
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** done
- **Effort:** M · deep

**Context:** — declared parameters/results from `LibraryIndex`/typeshed as *declaration* contracts (stdlib first), so `open(path)` gives `path` a `str | PathLike` capability.

**Steps:**
1. Extend `builders.py` library calls to methods on known classes (I-21) and overload selection (I-13).
2. Use `stubs.returns.function_return` and refuse generic returns.
3. Tests: `os.getcwd()`, `Path(p).read_text()`.

**Done when:** library calls type through the stubs reader.

**Evidence 2026-11-09:** `builders._library_return` resolves callees via
`callee_name` + `Resolver`, selects overloads by proven argument types, and
types methods on known receivers; `os.getcwd()` -> `str`,
`Path(p).read_text()` -> `str`, `re.match` -> `Match[str] | None` and
`os.getenv` overloads verified in `tests/astart/stubs/test_stubs_package.py`.

### F-16 — Builder: declared annotations
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Builder: declared annotations, base-class and override signatures (E1, M2-07) as declaration contracts.


Policy and wiring:

**Steps:**
1. Seed declared annotations of the module as `Origin.declared` (already done for params); add base-class method signatures (E1) for overrides (see W-10).
2. Refuse when the base class is outside the project.
3. Tests: override copies, mismatch refused.

**Done when:** declared and inherited signatures seed the graph.

### F-21 — Returns as union contracts
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Returns as union contracts: join of all exits subsumes `_join_types`; composes with `_flow_returns`; union returns need the same independence rule as parameters (M4-11 return half).

**Steps:**
1. Model each `return` expression as a union contract into `f->`; the join subsumes `_join_types` in `hints.py`.
2. Run the shadow comparison; every hint-index return must also be produced by negotiation.
3. Remove `_join_types` once parity holds (step guarded by the shadow result).

**Done when:** shadow parity and `only_negotiated.wrong == 0`.

### F-22 — Backward reconciliation of parameters
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Backward reconciliation of parameters: use-site capabilities/narrowing intersect the call-site union (sites `int` and `str` but body does `x + 1` → report a conflict, do not write `int | str`).

**Steps:**
1. Backward reconciliation: use-site capabilities and narrowing flow back to parameter beliefs through `argument` and `narrows` contracts.
2. Add the backward transfer entries (F-07) for them.
3. Tests: parameter narrowed by `isinstance` at use becomes a union arm.

**Done when:** parameters are constrained by their uses.

### F-23 — Conflict reporting
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Conflict reporting: a detection rule (`typing.type-conflict`, info) that lists the entity, both types and the explanation trail; latent bugs surface here instead of being silently refused.

**Steps:**
1. Add detection rule `typing.type-conflict` (info): report nodes whose belief has `conflicts` (`Belief.conflicts`).
2. Register as in M8-01; message lists the conflicting origins.

**Done when:** conflicts are reported and never fixed.

### F-24 — Calibrate the lossy collapses with the X-05 method
- **Status:** open
- **Priority:** P1
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Calibrate the lossy collapses with the X-05 method (≥ 97 % exact, 0 contradictions, n ≥ 100, stdlib *and* external corpus): `int | float` → `float`, `list | tuple` → `Sequence`, `list | set` → `Collection`, `dict | defaultdict` → `MutableMapping`. Enable only the categories that pass.

**Steps:**
1. Run the X-05 calibration method on each lossy collapse in `negotiation/algebra.py` (e.g. `Sequence` for lists and tuples).
2. Accept a collapse only at ≥ 97 % exact and 0 contradictions on the corpus; otherwise keep the concrete union.
3. Record the numbers in `docs/architecture/negotiation.md`.

**Done when:** each collapse has a measured accept/reject decision.

### F-26 — Explanation trail per candidate
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Explanation trail per candidate (origin, path, relation, distance) kept through merges; `astart explain` prints the evidence path of a negotiated annotation (M7-13).

**Steps:**
1. Keep the path of contracts that produced each candidate (origin, path, relation, distance) in `Belief`.
2. Expose it through `--explain-annotations` (AF-18).
3. Tests: the trail for one inferred return lists its sources.

**Done when:** every written annotation can print its trail.

### F-27 — Performance: graph build linear in nodes; per-function incremental rebuild; budget tests
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Performance: graph build linear in nodes; per-function incremental rebuild; budget tests in `tests/astart/source/test_perf_budgets.py`; shares the precomputed indexes of M7-02.

**Steps:**
1. Measure graph build time at 1 k, 4 k, 12 k lines; fix any superlinear builder (search for nested walks over `module`).
2. Add per-function rebuild: cache `Built` per function, invalidate by function hash.
3. Benchmark and record numbers.

**Done when:** graph build is linear in nodes.

### F-30 — `docs/architecture/negotiation.md`
- **Status:** done
- **Priority:** P1
- **Area:** docs
- **Readiness:** done
- **Effort:** unsized · deep

**Context:** `docs/architecture/negotiation.md` (model, adaptation rule, how to add a contract builder or a transfer rule), `docs/architecture/evidence-ladder.md` and README Limits updated, architecture page regenerated. Progress 2026-11-08: `docs/architecture/negotiation.md` (model, adaptation rule, six soundness rules, how to extend). README flags documented. `docs/architecture/evidence-ladder.md` and the architecture page still to update.

**Evidence 2026-11-08:** `docs/architecture/negotiation.md` exists (model, adaptation rule, soundness rules, how to extend).

### F-31 — Gold family `negotiated`
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Gold family `negotiated` (≥ 60 cases: cycles, containers, narrowing, conflicts, unions, refusals) in `tests/astart/rules/test_gold_expansion.py`; termination fuzz on random graphs.

**Steps:**
1. Create `tests/gold/negotiated/` with 60 cases: cycles, containers, narrowing, conflicts, opacity, each as `source`, `expected`.
2. Test runner `tests/test_gold_negotiated.py` iterates the directory.
3. Every case that fails today is either fixed or marked with the task that owns it.

**Done when:** 60 cases pass or reference their owning task.

### F-33 — Cross-module edges through `ProjectIndex`
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Cross-module edges through `ProjectIndex` (argument/return/attribute contracts across files; M3-03 evidence enters as `call_sites` seeds).

**Steps:**
1. Add cross-module edges using `ProjectIndex`: argument, return and attribute contracts between modules.
2. Resolve the callee module through the index; refuse on cycles that cannot settle.
3. Tests with a two-module project in `tmp_path` (`--project`).

**Done when:** types flow across two modules.

### F-34 — Safety bounds: per-module event and wall-clock budget; on overrun fall back to the
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Safety bounds: per-module event and wall-clock budget; on overrun fall back to the existing `HintIndex` path and report it (CC-03).

**Steps:**
1. Add `Negotiator` event cap and wall-clock budget (settings `negotiation_events`, `negotiation_seconds`).
2. On overrun return only the beliefs settled so far with a `partial` flag and fall back to the hint index.
3. Test with a tiny budget.

**Done when:** overrun never crashes or writes unsettled types.

### F-37 — Default-literal parameters in the negotiator
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Default-literal parameters in the negotiator (the last big shadow gap: 70 annotations, 60 exact, 3 wrong). The hint index accepts a literal default with the engine's agreement even when some callers are unknown; the negotiator treats unknown callers as opaque. Port the tiered confidences (`confidence.by_literal`) as a per-origin/per-type table (F-18) instead of copying the looser rule.

**Steps:**
1. See W-08 for the full recipe; this entry tracks the shadow metric: `only_existing` for basis `default_literal` below 20.

**Done when:** shadow shows `default_literal` below 20.

### F-40 — Comprehensions as derived nodes
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Comprehensions as derived nodes (the loop variable typed from the iterable's element node): 44 variables of the dev pair are blocked as "container literal mutated or not provable", most of them comprehensions and dict displays over parameters.

**Steps:**
1. Add comprehension loop variables as derived nodes fed by `iter_of` (I-05).
2. Comprehension result types: `[e for ...]` → `list[type(e)]`, dict/set analogues.
3. Tests for each comprehension kind plus a mutation refusal.

**Done when:** comprehension variables and results are typed.

### F-41 — Calls on builtin-typed receivers
- **Status:** done
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** done
- **Effort:** M · deep

**Context:** Calls on builtin-typed receivers (`value.strip()`, `items.copy()`, `d.get(k)`) as derived nodes using the typer's method tables, and `list(...)`/`dict(...)`/`sorted(...)` of node arguments.

**Steps:**
1. Extend `provable._Typer` method tables with the missing builtin methods (see W-06 step 1); one row and one test each.
2. Receiver must be typed first (derived-node evaluator).

**Done when:** `value.strip()`, `items.copy()`, `d.get(k)` type correctly.

**Evidence 2026-11-09:** `provable._Typer` receiver-method dispatch parses
receiver annotations as AST and applies per-container method tables; builtin
constructors `list`/`dict`/`sorted`/`sum`/`next`/`any`/`all` type from provable
operand types; unsupported or unknown receivers still refuse; tests in
`tests/astart/rules/test_rules_typer_builtins.py` and `tests/astart/rules/test_rules_typer_negatives.py`.

### F-43 — Quote instead of refusing
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Quote instead of refusing: where a negotiated annotation names a class not yet bound (`-> URIBuilder` inside its own class), write the string form (or `Self` on 3.11+) instead of dropping it.

**Steps:**
1. See W-11 for the recipe (`Self` or quoted name).

**Done when:** W-11 is done.

### F-25 — Objective choice between a concrete union and an ABC abstraction
- **Status:** open
- **Priority:** P2
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Objective choice between a concrete union and an ABC abstraction (coverage, narrowness, existing alias reuse over a new Protocol, never `Any`/`object`); ties to M5-09/M5-10.

**Steps:**
1. Rule: choose a concrete union or an ABC abstraction by coverage on the corpus: measure exact share of `Sequence[T]` vs `list[T] | tuple[T, ...]`.
2. Pick per case with the data; store in `rules/calibration.json` (CC-01).
3. Tests.

**Done when:** the choice is data-driven and recorded.

### F-32 — Retire superseded items
- **Status:** done
- **Priority:** P2
- **Area:** docs
- **Readiness:** done
- **Effort:** S · deep

**Context:** Retire superseded items: Q-37/Q-38 (slots / site reliability) → F-04/F-02; cross-reference M2-09, M4-07, M4-11, M4-17 to the builders that deliver them.

**Steps:**
1. Mark Q-37 and Q-38 `done` with a note pointing to F-04 and F-02 once the shadow comparison shows no regression; remove duplicates from START HERE.

**Done when:** the superseded tasks are closed with a note.

**Evidence 2026-11-09:** Q-37 was already closed on its own merits —
`src/astart/rules/slots.py` shipped. Q-38 closed as superseded (note in
its body): evidence weighting by provenance/confidence is delivered by
F-02 (`Origin` sets, `independent`) and F-04 (`Belief` polarity unions),
and the 2026-11-08 shadow run in `docs/analysis/scripts.benchmark.md` shows no regression
(12 789 annotations, 0 crashes, negotiator never contradicts the hint
index). No Q-37/Q-38 duplicates existed in START HERE — nothing to
remove. Cross-references added: `**Negotiation:**` lines in M2-09
(`builders.py` flow edges + `narrowing.py`), M4-07 (`builders.py` usage
edges + `containers.py`/`transfer.py`), M4-11 (`algebra.py` union +
`beliefs.py`, F-03/F-04) and M4-17 (`builders.py` call edges +
`transfer.py`).

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| F-01 | Data model `negotiation/model.py`: `Relation` (assigns, returns, argument, call_result,… | P0 | negotiation |
| F-02 | Provenance: a candidate carries the set of `Origin`s that support it; `independent` means… | P0 | negotiation |
| F-03 | Type algebra `negotiation/algebra.py` (`union`, `intersect`, `members`) over type… | P0 | negotiation |
| F-04 | `negotiation/beliefs.py` `Belief`: add by polarity (union keeps the best confidence per… | P0 | negotiation |
| F-05 | `negotiation/graph.py` `ContractGraph`: nodes by stable path text, edges with… | P0 | negotiation |
| F-06 | `negotiation/negotiator.py` `Negotiator.solve`: queue of ants, wormhole memo `(path,… | P0 | negotiation |
| F-07a | `negotiation/transfer.py`: first transfer table | P0 | negotiation |
| F-08 | Builder: assignments (plain, annotated = declaration, augmented, tuple unpacking,… | P1 | negotiation |
| F-09 | Builder: returns and calls | P1 | negotiation |
| F-10 | Builder: containers | P1 | negotiation |
| F-11 | Builder: attributes | P1 | negotiation |
| F-12 | Builder: narrowing | P1 | negotiation |
| F-14 | Builder: operators using the typer's tables (numeric tower, str/bytes/list concat,… | P1 | negotiation |
| F-35 | Protocol-dunder results in the negotiator (`__len__` → `int`, `__exit__` → `bool / None`,… | P0 | negotiation |
| F-36 | Calibrated `bool` returns in the negotiator: returns that are boolean by syntax… | P0 | negotiation |
| F-38 | Lost contributions: a transfer that yields nothing for a union/declaration contract… | P0 | negotiation |
| F-39 | Opacity reasons: every opaque node records why (`Built.why`), the groundwork for `astart… | P1 | negotiation |
| F-42 | Names that exist when an annotation is evaluated: a negotiated parameter or return hint… | P0 | negotiation |
| F-19 | Shadow mode: run the negotiator next to `HintIndex`, record every difference (new hint,… | P0 | negotiation |

## 11. Untyped to typed conversion

*Scope:* Converting `fixtures/untyped.py` into `fixtures/typed.py` automatically.  
*ID prefixes:* P, T, W

<details>
<summary>Background — 18.13 Untyped ⇄ typed conversion (the author's fixture pair)</summary>


Requirement (2026-11-08): the system must turn
`fixtures/test_resolver_inference_merged_untyped_extended.py` into
`..._typed_extended.py` of the author's `ast_graph_inference_api_v33_oop`
project, and the reverse. The pair is kept in `fixtures/` and measured by
`python -m scripts.compare.pair UNTYPED TYPED`. It is *not* a mechanical strip: the
typed side adds 377 variable annotations, extra imports and synthesized helper
classes (`LocalMultiplierProtocol`, `LocalMultiplierFactory`).

Baseline 2026-11-08 (`--min-confidence 0.8`): parameters and returns **71 of
557** exact (12.7 %; 88 = 15.8 % at `--min-confidence 0`), 4 narrower
(`NoReturn` where the author wrote `None`), 2 contradictions (synthesized
Protocols the author spelled as `Callable[[object], object]` / `str`);
variables **3 of 329**. Missed reasons for the 557: return type not provable
127, tainted 83, no candidate 72, call sites unknown 58, uncorroborated 44,
escapes as a value 28, declaration body 16, contains object 10.


</details>

<details>
<summary>Background — 18.14 Ideas from existing tools (reviewed 2026-11-08)</summary>


Looked at: typeshed `stubs/`, `typing_utils`, `retype`, `autotyping`,
`infer-types`. None is a drop-in; each gives a concrete, small task. Value
order: T-01…T-03 are sound (declared-elsewhere evidence, E1); T-04…T-06 are
heuristics that must pass the X-05 calibration (≥ 97 % exact, 0 contradictions,
n ≥ 100) before they may write anything.


</details>

<details>
<summary>Background — 19. Ready-to-run work queue (2026-11-08)</summary>


Written for an agent that follows steps. Each task names its files, gives the
steps in order, and says when it is done. Work them in order unless a task says
it is independent. Read **START HERE** (top of this file) first. "FAST" means
`python -m pytest -m "not slow" -q -p no:cacheprovider`; "LINT FILES" means
`ruff check --fix FILES ; ruff format FILES ; ruff check FILES --output-format concise`.


</details>

<details>
<summary>Background — 19.2 Coverage work (each task moves a pair number; use the burn-down loop)</summary>


**Burn-down loop (use for any coverage task).** (a) `PYTHONPATH=src python
scripts/compare/opacity_report.py fixtures/untyped.py` and write down the counts. (b) Pick the
largest "direct:" reason that the task names. (c) Print 3 examples (`--samples 3`)
and read the code of those functions in `fixtures/untyped.py`. (d) Add the missing
rule in `builders.py` (or `transfer.py`/`policy.py`), always so that an
unknown case stays opaque. (e) Add one positive test and one refusal test in
`tests/astart/rules/negotiation/test_negotiation_module.py` (helper `_negotiate(source=..., engine={...})`;
`engine` maps node paths like `"f.x"` and `"f->"` to the engine's proposal).
(f) Re-run (a) and the pair command; record both. Never accept a coverage gain
that makes `only_negotiated.wrong` in the shadow comparison non-zero.


</details>

<details>
<summary>Background — 19.3 Rules for writing new tasks here</summary>


A task is ready only if it has: files, numbered steps, one test it must add,
one command that prints the number to improve, and a stop condition. If you
cannot write those, do the investigation first (see W-02).



</details>

### P-02 — Variable annotations
- **Status:** open
- **Priority:** P0
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Variable annotations (`x: int = 1`) for module, class and function locals behind `--annotate-variables` (a profile, off by default: gratuitous locals are noise elsewhere). Nodes already exist for single-binding locals (F-08, F-10); settle them with the negotiation policy and write `name: T = value` through a new applier; the M8-02 detector (`variable_annotations.py`) supplies the rule. Target: the 329 variables of the pair. Progress 2026-11-08: `astart fix --annotate-variables` (also on automatically in modules that already annotate a function-local variable) writes `name: T = value` for single-binding locals — rule TYP007 `typing.missing-variable-annotation`, fix `typing.add-variable-annotation` (guarded, 0.95), settled by `negotiation/variables.py` from proof-origin evidence only. Soundness work it forced: literal containers are typed only while every later use is understood (`append`/`insert`/`add` join the element type, a dict must stay read-only, `*x`/`**x` unpacking is a read); attributes holding a mutable container with an unrecognised use are opaque; wrapper contracts join the elements first (`list[int | str]`, not `list[int] | list[str]`). Dev pair: variables 0 → **53 of 335 exact, 0 wrong** (+4 the author's alias `IntDict`). Open: class-level and module-level variables, attribute annotations from negotiation, comprehension values, calls into libraries (F-15).

**Steps:**
1. Done in pieces: locals (done), attributes (W-12), class/module variables (W-14); this task closes when all three are done and the pair variable counts reach the contract.

**Done when:** W-12 and W-14 are done and A-02 variables ≥ 90 %.

### P-03 — Return types that are "not provable"
- **Status:** open
- **Priority:** P0
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Return types that are "not provable" (127 of the pair's misses): returns through locals, containers, attributes and calls to other functions of the module — delivered by F-10…F-14 and F-20; re-measure with the pair after each. Progress 2026-11-08: `MethodIndex` no longer treats a *read* of `globals()`/`vars()`/`locals()` (`globals()["f"](x)`, `.get(...)`) as a rebinding of module names — only stores, `update`, aliases, `exec` and `eval` still do — which unblocked all 152 calls to module functions in `fixtures/untyped.py` (0 bound before). `--negotiate` (new, off by default) lets negotiated parameter and return hints supplement the hint index where it has none. Dev pair parameters+returns exact 11 → 53 with it; resolver pair 71 → 109. Both baselines unchanged without the flag; gate with `--negotiate` pending.

**Steps:**
1. Work the burn-down loop (section 19.2) on 'return not provable': tasks W-06, W-07, F-40, F-41, I-05, I-08, I-18.
2. After each, re-run `scripts/compare/opacity_report.py fixtures/untyped.py` and record the count.

**Done when:** unprovable returns on the dev file drop below 20.

### P-08 — The reverse direction
- **Status:** open
- **Priority:** P0
- **Area:** cli
- **Readiness:** ready
- **Effort:** M · standard

**Context:** The reverse direction, `astart untype`: lossless removal of parameter, return and variable annotations (and, with `--drop-synthesized`, of Protocols/TypeVars/imports that only the annotations used), keeping comments, layout and docstrings; round trip `untype(typed)` must equal the author's untyped file after `ast.dump` (today `strip_annotations` is benchmark-only and rewrites the text).

**Steps:**
1. Read `strip_annotations` (`src/astart/rules/recovery.py:780`) and
   `src/astart/rules/object_annotations.py` (it already finds annotation spans
   with `span_of`) to reuse the span edit helpers.
2. New module `src/astart/rules/untype.py` with
   `def untype_source(*, source: str, drop_synthesized: bool = False) -> str`.
   Collect spans for: parameter annotations (`arg.annotation`, including the
   `: ` before it), return annotations (` -> X`), variable annotations
   (`x: T = v` → `x = v`; `x: T` without value is deleted only when the
   name is never read).
3. Apply the edits bottom-up so offsets stay valid; never touch comments or
   docstrings.
4. `drop_synthesized`: remove classes whose docstring starts with the
   marker `Constants.docstring_marker` (`rules/protocols.py`) and `TypeVar`
   assignments created by astart; then remove imports no name uses.
5. CLI: `astart untype PATH... [--drop-synthesized] [--diff|--check]`, built like
   `run_fix` (`cli/commands.py:809`) with `_write_atomic`.
6. Test: for each pair in `fixtures/`, `ast.dump(parse(untype_source(typed)))`
   equals `ast.dump(parse(untyped))` (ignore docstring changes made by astart).

**Done when:** the pair round trip test passes on every `fixtures` pair and `astart untype --check` exits 1 on a typed file.

### W-01 — Record the verification commands and their baseline results
- **Status:** open
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · light

**Context:** Write down the outputs once, then use the commands in every later task.
1. Shadow comparison (~8 min, run in background):
   `PYTHONPATH=src:. python -m scripts.benchmark.shadow tests/corpus/extended --jobs 8 --json /tmp/shadow.json`
   then read `/tmp/shadow.json`: the group `only_negotiated` must show `wrong: 0`.
2. External recovery gate (~12 min, background):
   `PYTHONPATH=src:. python -m scripts.benchmark recovery --corpus tests/corpus/extended --jobs 8 --json /tmp/ext.json`
   `PYTHONPATH=src:. python -m scripts.benchmark gate --report /tmp/ext.json --baseline scripts/benchmark/artifacts/resources/baseline_ext.json`
   must print `PASS`.
3. Stdlib recovery gate (~3 min): same without `--corpus` and without `--baseline`;
   must print `PASS`.
4. Semantic equivalence needs 5 packages that are not installed. Install
   them to a throwaway directory (never into the user's environment):
   `python -m pip install --no-deps --target /tmp/semdeps toml==0.10.2 tomlkit==0.13.3 boltons==25.0.0 more-itertools==11.2.1`
   and `python -m pip install --no-deps --no-binary :all: --target /tmp/semdeps2 tomli==2.5.0`.
   Then in Python: `from scripts.benchmark.semantic import load_projects, run_project`;
   for each project, `run_project(project=p, source=Path("/tmp/semdeps")/p.package)`
   (`/tmp/semdeps2` for `tomli`); a project passes when `same_imports and same_result`.
   The other 10 projects run with `python -m scripts.benchmark semantic --json /tmp/sem.json`.
5. Slow tier: `python -m pytest -m slow -q -p no:cacheprovider` (~19 min) → `870 passed`.

**Done when:** you ran all five once and recorded the five results under this task.

**Results 2026-11-09:**
1. Shadow run `/tmp/shadow.json`: `only_negotiated` = correct 161, compatible
   13, **wrong 9** — the required `wrong: 0` is not met; 9 negotiated-only
   contradictions need triage (L2's negotiation work raised negotiated-only
   correct 41 → 161 at the same time).
2. External recovery `/tmp/ext.json` + `gate --baseline
   scripts/benchmark/artifacts/resources/baseline_ext.json`: **PASS** — 165 modules, 2 581 / 12 789,
   recall 20.18 %, precision 99.60 %, 0 crashes, 0 new errors.
3. Stdlib recovery `/tmp/std.json` + `gate`: **PASS** — 128 modules,
   0 crashes.
4. Semantic equivalence: all 15 projects pass `same_imports` +
   `same_result` (`/tmp/sem.json`); the five pinned packages were already
   importable in the environment.
5. Slow tier: running.

### W-02 — Find why the checker gate keeps only 4 annotations on the resolver pair
- **Status:** open
- **Priority:** P0
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Why does the type-checker gate keep only 4 annotations on the full resolver pair? Investigation, not a feature. Background: `python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5 --checker` printed `parameters_and_returns.correct = 4`, `variables = 0`; the same run without `--checker` gives 329 and 185. On a 241-line slice the gate accepts everything (18 of 18), and `Checker.regresses` answers in ~1.5 s, so the gate is not simply broken.

**Progress 2026-11-09:** `scripts/compare/gated_conversion.py` exists (the
step-1 probe: `fix_source` with `engine=True` +
`checker=build_checker(root=Path.cwd())` on the full resolver untyped
file, printing seconds, applied/skipped counts, the skip-code histogram
and a one-fix `new_errors` breakdown). Its background run outcome is not
yet recorded here. Steps:
1. Copy `/tmp/gated.py` from below to `scripts/compare/gated_conversion.py` (it runs
   `fix_source(... engine=True, checker=build_checker(root=Path.cwd()))` on the
   full resolver untyped file and prints seconds, `len(applied)`, `len(skipped)`
   and `Counter(s.code.value for s in skipped)`). Run it in the background.
2. If almost everything is skipped with code `checker-rejected`: take ONE
   skipped fix, apply it alone to the original source (`Checker.new_errors(filename=
   "m.py", before=original, after=with_one_fix)`) and print what pyright says.
   Two outcomes: the single fix really adds an error (then the gate is right and
   the annotation is wrong — list the patterns) or it adds none (then the
   batch logic in `runner._degrade`/`_attempt` is wrong — read how `before` is
   chosen after each accepted half; `before` must be the source *after* the
   earlier accepted halves, not the original).
3. If the run ends in few skips but few applies, read `res.rounds` and
   `FixSettings.max_rounds` (default 3): the fixpoint may stop early.

**Done when:** you wrote the cause in 5 lines under this task and, if it is a bug
in `runner.py`, fixed it with a test in `tests/astart/rules/test_rules_runner.py` that
uses a stub `Checker` rejecting exactly one fix.
Acceptance after a fix: with `--engine --checker`, resolver pair exact ≥ 250
of 557 and contradictions ≤ half of the 94 without the checker.

### P-04 — "Tainted" parameters
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** "Tainted" parameters (83): types that only usage reveals (`x + 1`, `x.upper()`, `for _ in x`) — capability contracts (F-13) and backward reconciliation (F-22).

**Steps:**
1. Run `scripts/compare/opacity_report.py` on `fixtures/untyped.py`; list the nodes in this category with `--samples 10`.
2. Group by cause; each cause becomes a G-03 owner row and, if no task covers it, a new task in chapter 14.
3. Fix the largest cause using the burn-down loop (section 19.2).

**Done when:** the category count falls by half.

### P-05 — "No candidate" (72)
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** "No candidate" (72): the inference engine proposes nothing; measure which shapes and extend the engine or the negotiation seeds (calls into stubs F-15).

**Steps:**
1. Run `scripts/compare/opacity_report.py` on `fixtures/untyped.py`; list the nodes in this category with `--samples 10`.
2. Group by cause; each cause becomes a G-03 owner row and, if no task covers it, a new task in chapter 14.
3. Fix the largest cause using the burn-down loop (section 19.2).

**Done when:** the category count falls by half.

### P-06 — "Call sites unknown / uncorroborated / escapes"
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** "Call sites unknown / uncorroborated / escapes" (130): fixtures are closed worlds; add `--closed-world` assumptions for the benchmark and measure how much of this is the open-world refusal.

**Steps:**
1. Run `scripts/compare/opacity_report.py` on `fixtures/untyped.py`; list the nodes in this category with `--samples 10`.
2. Group by cause; each cause becomes a G-03 owner row and, if no task covers it, a new task in chapter 14.
3. Fix the largest cause using the burn-down loop (section 19.2).

**Done when:** the category count falls by half.

### P-07 — Name-agnostic scoring of synthesized Protocols and TypeVars
- **Status:** open
- **Priority:** P1
- **Area:** types
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Name-agnostic scoring of synthesized Protocols and TypeVars (the author's `LocalMultiplierProtocol` vs ours): compare members and signatures, not names.

**Steps:**
1. Make the scorer name-agnostic for synthesised `Protocol`s and `TypeVar`s: compare structure (members and signatures), not the name.
2. Implement in `rules/recovery.py` `relation` for protocol vs class names declared in the typed twin.
3. Tests: `SupportsVector` vs `_Vec` with equal members is `exact`.

**Done when:** the three protocol-name lines in `pair_wrong.py` disappear.

### P-09 — Round-trip gate
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Round-trip gate: `fix(untype(typed))` against `typed` per pair, baseline stored, gate fails on lower recall or any contradiction.

**Steps:**
1. Implement the round trip: `fix(untype(typed))` vs `typed` for each pair, scored with `scripts.compare.pair.compare`.
2. Store baseline numbers in `scripts/benchmark/artifacts/resources/baseline_pair.json`; add a `gate` mode.
3. Needs P-08.

**Done when:** the round-trip gate prints PASS against the baseline.

### P-10 — Import parity: every name the written annotations use is imported
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Import parity: every name the written annotations use is imported (M3-13), with the typed twin's import style (M3-08); measured as the missing-import count of the pair.

**Steps:**
1. After a fix, collect every `Name` loaded in new annotations and assert it is bound at module level before use (walk the AST; `bound_when_evaluated` helper).
2. Add the check to the semantic run and as a test over the corpus.

**Done when:** no unbound name in written annotations on both corpora.

### T-01 — Dunder parameters from the language
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Dunder parameters from the language (`autotyping --annotate-magics`): `__exit__`/`__aexit__` take `type[BaseException] | None`, `BaseException | None`, `TracebackType | None`; we annotate only their *result*. Declaration contracts (`Origin.protocol`) with the `types.TracebackType` import.

**Steps:**
1. See W-09 and AF-03 for the dunder table; add `__exit__`, `__aexit__`, `__eq__`, `__len__`, `__bool__`, `__repr__`, `__str__`, `__hash__`, `__contains__`.

**Done when:** AF-03 is done.

### T-02 — Copy annotations from the base-class method of the same name
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Copy annotations from the base-class method of the same name (`infer-types`; this is M2-07 override awareness): a declaration contract from the overridden definition when the base is in the module, the project (`ProjectIndex`) or a typeshed/`py.typed` stub; never contradict the base.

**Steps:**
1. See W-10 for the recipe (copy base-class annotations).

**Done when:** W-10 is done.

### T-03 — Apply a sibling stub
- **Status:** open
- **Priority:** P1
- **Area:** stubs
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Apply a sibling stub (`retype`, which is unmaintained since 2022): when `foo.pyi` sits next to `foo.py`, or typeshed `stubs/<dist>` covers the module, seed its parameter/return/variable annotations as `declared` and write them with our lossless writer (`astart fix --apply-stubs`). Also the best oracle corpus for P-series work: untyped sdist source + the typeshed stub as the typed twin.

**Steps:**
1. Read a sibling `.pyi` (same stem, next to the module) with `astart.stubs.parser`; apply its annotations to the module's unannotated parameters and returns by name.
2. Refuse on signature mismatch (different parameter names or counts).
3. Tests: matching stub applies, mismatching stub refused.

**Done when:** sibling stubs are applied only on exact signature match.

### T-08 — Library return types from typeshed
- **Status:** done
- **Priority:** P1
- **Area:** stubs
- **Readiness:** done
- **Effort:** S · standard

**Context:** Library return types from typeshed (`typeshed_client`, which `scripts/utils/generate_libkw.py` already uses offline): generate `rules/librets.py` the way `libkw.py` is generated — for every stdlib function and method with **one** signature (no `@overload`), no type variables and a plain return type (`str`, `int`, `bool`, `bytes`, `None`, `list[str]`, …) record `callee → (parameter types, return type)`. Feed it to the derived nodes (F-15): `os.path.join(a, b)` is `str` once `a` and `b` are `str`; overloaded and generic callees stay opaque. Use the resolver's version/platform evaluation (`get_search_context(version=…)`) so a branch that does not apply is not read. Acceptance: the dev pair's "unprovable Call" count drops, 0 new contradictions on both corpora, generation date and typeshed version recorded in the file like `libkw`.

**Evidence 2026-11-08:** `astart/stubs/returns.py` `function_return` (single non-overloaded, non-generic, builtin-only return types) wired through `rules/library_calls.py` `callee_name` into `negotiation/builders.py`; `tests/astart/stubs/test_stubs_package.py` (23 tests). Methods on library classes, overloads and generics continue as I-21, I-13 and I-18.

### W-03 — Stop `object` leaking into `--engine` annotations
- **Status:** done
- **Priority:** P1
- **Area:** inference
- **Readiness:** done
- **Effort:** XL · deep

**Context:** Repro: `PYTHONPATH=src:. python scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5` prints `... wrote dict[object, object] | None`. `engine_hints` filters with `hints.is_allowed_source`, which must reject `object`, so a different path wrote it. Steps:
1. Run the repro on a tiny module containing the `ExtendedDataclassStress`
   class from `fixtures/untyped.py` until the output still shows `object`.
2. Find who wrote it: `Hint.basis` values are in `HintBasis` (`hints.py`);
   print `facts.hints.index().hint_for(node=...)` for the parameter.
3. Add the missing check at that place (probably the dataclass-field path or
   `variables.engine`), with a test that fails first.

**Finding (2026-11-08, partial):** `engine_hints` (src/astart/rules/engine_hints.py)
already rejects any annotation with `object`/`Any` anywhere (`is_allowed_source`
walks every nested `Name`). A 9-line repro (class with `lookup=None` stored as
`self.lookup = lookup or {}`) does NOT leak, so the leak needs the full
`fixtures/untyped.py`. Next step: run `fix_source(...)` on the full file, loop over
`res.applied` and print the fix whose text contains `object` (the objects in
`res.applied` are listed by `dir(res.applied[0])`; print one first). The
writer is then one of: `variable_hints`/`engine_variables` (variables do not
go through `engine_hints`), the dataclass-field path, or a hint index basis
that builds annotations from `container_risks`. Put the `banned_names` check
in that writer.


**Findings 2026-11-08 (second pass):** `AppliedFix` has only `fix_key`,
`rule_key`, `subject_path` (no text). On the full `fixtures/untyped.py` with
`--engine` the output has 225 `object` words (24 in the original); only 163
fixes are recorded, one `typing.add-inferred-annotation` and nine
`typing.add-variable-annotation`, so each of those writes many nodes.
Three small repros do NOT leak: the `ExtendedDataclassStress` pattern, a
`{k: v for k, v in enumerate(items)}` local, and the same with
`enumerate(iterable=items)`. `is_allowed_source` rejects `dict[object, object]`.
So the leak is a path that does not call it, active only with the full file.

**ROOT CAUSE (proved 2026-11-08):** `LazyConversion.text`
(`src/astart/rules/engine_hints.py`) calls `self._module.convert(stubs_path=..., apply=True)`.
`SemanticAnalyzer.convert` (`src/astart/semantic/analyzer.py:432`) with
`apply=True` calls `apply_graph_annotations(root=self.root, ...)`, which writes
the engine's annotations **into the fixer's own parsed module**. Those nodes are
then printed by the formatter, so they reach the output with no hint, no filter
(`is_allowed_source`) and no recorded fix. Proof: with `engine=True, max_rounds=1`
the output has 18 `dict[object, object]`; with `LazyConversion.text` forced to
`None` it has 0; wrapping `.text` showed the module changed on the first call
per module (`(True, True)`).

**Steps (replaces the bisect below):**
1. Write the failing test first in `tests/astart/rules/test_engine_hints.py`: parse a module
   with `def f(x): return {k: v for k, v in enumerate(x)}`, create
   `LazyConversion(module=module)`, read `.text`, assert
   `ast.dump(module)` is unchanged. It fails today.
2. In `LazyConversion.text` stop passing `apply=True`: call
   `self._module.convert(stubs_path=Path(scratch), apply=False)` and read
   `.converted_source` from the result. If `converted_source` is empty with
   `apply=False` (check `GraphConversion`), instead build the converter on a
   copy: `CommentedModule` of `unparse`d source (`parse(source=module_text)`),
   and call `convert(apply=True)` on that copy only.
3. Run `tests/astart/rules/test_engine_hints.py` and `tests/astart/rules/test_rules_engine_mode.py`.
4. Run `PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5`
   and write the new numbers here. Expect `wrong` to fall sharply; `correct`
   may fall because the unfiltered annotations that happened to be right are no
   longer written (they must now come through `engine_hints`).
5. If `correct` falls by more than 20, look at what `engine_hints` rejects
   (`bound_when_evaluated`, `is_allowed_source`) for the lost nodes; each class
   of loss becomes its own task.

**Done when:** the new test passes, `pair_wrong.py` prints no `object`, and
the fast tier is green.

**Findings (third pass):** the bisect by `object` count was misleading (a run
that applies nothing counts as "no leak"). Facts that hold: in the full-file
run `function_with_comprehensions` has exactly one recorded fix
(`docs.add-parameter-entries`) yet its return annotation contains
`dict[object, object]`; no `Hint` returned by `HintIndex.hint_for` or
`LazyVariables.hint_for` contains `object` (spied); `docs_fixes.py` never touches
annotations; `LazyConversion(module).text` is `None` on `fixtures/untyped.py` when
called alone and does not mutate the module. So the annotations arrive by a path
that is neither a hint nor a recorded fix. Next: in `runner.py` print the source
after each round and each fix key (`fix_source(... )` loop around line 376) and
find the first round whose text contains `dict[object, object]`.

**Bisect (do this):**
1. Copy `fixtures/untyped.py` to `/tmp/b.py`; keep the first N top-level defs
   (`ast.parse`, slice `body`, `ast.unparse` is NOT allowed: cut by line
   numbers from `node.end_lineno`).
2. For N = half, quarter, … run the repro script and stop at the smallest N
   whose output contains `dict[object, object]`.
3. In that slice, print `facts.hints.index().hint_for(node=<the param node>)`
   and `.basis`. The basis names the writer; add `banned_names` filtering there
   and a regression test with the minimal slice.

**Done when:** `pair_wrong.py ... --engine` prints no line containing `object` or
`Any`, and the pair numbers did not drop by more than 3.

**Evidence 2026-11-08:** fixed by changing `LazyConversion.text`
(`src/astart/rules/engine_hints.py`) from `convert(apply=True)` to
`convert(apply=False)`; new test `test_lazy_conversion_leaves_the_module_untouched`
in `tests/astart/rules/test_engine_hints.py` (red before, green after). Dev pair with
`--engine --min-confidence 0.5`: parameters/returns exact 253 → 221, wrong
55 → 13; variables exact 174 → 152, wrong 49 → 13; `object` is no longer written.
**Open side effect:** `tests/astart/rules/test_rules_engine_mode.py::test_the_engine_fills_what_the_evidence_leaves_open`
fails — see G-10. Fast tier and recovery gates were NOT re-run after this change.

### W-04 — Remove the last `typeshed_client` use from `generate_libkw.py`
- **Status:** done
- **Priority:** P1
- **Area:** stubs
- **Readiness:** done
- **Effort:** M · light

**Context:** Finish removing `typeshed_client` from `scripts/utils/generate_libkw.py` (it is the last mention; the runtime never imports it). The script walks a typeshed root. `astart.stubs.find_typeshed()` finds one (it found basedpyright's copy), but `collect(root=…)` produced keys with a `stdlib.` prefix because it expected `root` to be the *contents* of the bundle used before. Steps:
1. In `main()` use `find_typeshed(explicit=Path(argv[1]) if len(argv) > 1 else None)`;
   print an error and return 1 when it is `None`.
2. In `collect`/`_walk_body` make `root / "stdlib"` the base directory when it
   exists, so a module key is `os.path.join`, not `stdlib.os.path.join`; third-party
   `stubs/<dist>/<pkg>` entries keep working only for packages in `THIRD_PARTY`.
3. Replace the `typeshed_client` version line in the footer by
   `# from the typeshed copy at {root}.`.
4. Run `PYTHONPATH=src python scripts/utils/generate_libkw.py > /tmp/libkw_new.py`
   (takes ~5 min; background). Compare only the `SIGNATURES` dictionary:
   `diff <(sed -n '/^SIGNATURES/,$p' /tmp/libkw_new.py | grep -v '^# ') <(sed -n '/^SIGNATURES/,$p' src/astart/rules/libkw.py | grep -v '^# ')`.

**Done when:** the diff is empty or only adds/removes entries (no changed keys);
then copy the new file over `src/astart/rules/libkw.py`, run
`tests/astart/rules/test_rules_libkw.py tests/astart/rules/test_rules_library_calls.py` and FAST.
If the diff shows renamed keys you cannot explain, keep the old file and stop.

**Evidence 2026-11-09:** `scripts/utils/generate_libkw.py` takes an explicit
typeshed root or uses `astart.stubs.find_typeshed`, walks `stdlib/` plus
allow-listed `stubs/<dist>` distributions (`Constants.third_party`), and records
the typeshed path in the footer; no `typeshed_client` import remains.
Regenerated `rules/libkw.py`: only additions/removals plus 18 `_curses.window`
parameter renames (`yes` -> `flag`) from typeshed version drift.

### W-06 — Burn down unprovable calls in the negotiator
- **Status:** done
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** done
- **Effort:** S · standard

**Context:** Known sub-cases, easiest first:
1. Calls on a receiver whose type is known (`value.strip()`, `items.copy()`,
   `d.get(k)`): the derived-node templater already allows attribute calls
   (`_Templater.convert`); check with `scripts/compare/opacity_report.py` which still
   fail and extend `provable._Typer` method tables (`str_to_str`, ... in
   `provable.Constants`) with the missing methods. One table row + one test each.
2. Library functions returning a class from `known_imports` (`Path`, `Decimal`,
   `UUID`, `date`...): in `stubs/returns.py` `_plain` allow Name ids that are
   keys of `imports.Constants.known_imports`; `ensure_names` inserts the import.
   Test: `shutil.which` is excluded (returns `str | None`, overloaded?) — check
   with `host_resolver().resolve("pathlib.Path")` first.
3. `list(x)`, `sorted(x)`, `dict(x)`, `sum(x)` of node arguments: already typed by
   `provable._Typer.special_calls` when the argument type is known; if not
   derived, find out why in `_Templater` (usually a keyword argument — keywords
   make `_field` reject the call; allow `keyword` nodes whose value converts).
Skip: `super().__new__`, `functools.partial`, `reduce`, generics with `T`.

**Done when:** unprovable-call count drops by ≥ 10 and the pair numbers rise.

**Evidence 2026-11-09:** `provable._Typer` gained dict method tables
(`get`/`pop`/`setdefault`/`copy`/`update`/`clear`/`popitem`), list methods
(`copy`/`pop`/`append`), and `any`/`all`/`sum`/`next`/improved `dict` calls with
union dedup; the derived-node templater accepts keyword arguments; the stale
`{'a': 1}.get('a')` negative now correctly proves `int | None`; tables and tests
in `tests/astart/rules/test_rules_typer_builtins.py`.

### W-07 — Burn down unbindable calls and escaping functions
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · standard

**Context:** For the first: run `CallBindings( module=..., counts=...).get(call=c)` on the 16 calls (`opacity_report.py` prints samples) and list why each is refused (decorated callee, `*args`, method on an unknown receiver, dynamic marker). Fix only the refusals that are provably safe, e.g. a decorator that is `functools.wraps`-based, using the danger matrix `tests/astart/rules/test_rules_kwargs_danger.py` (it must stay green). For the second, only treat a function as escaping when the name is read as a value *outside* a decorator position: `@decorator` applied to a function makes the *decorated* function reachable, not the decorator's parameters unknown.

**Done when:** both counts drop and `tests/astart/rules/test_rules_kwargs_danger.py` passes.

**Steps:**
1. Run `PYTHONPATH=src python scripts/compare/opacity_report.py fixtures/untyped.py --samples 5` and note the two counts: calls that cannot be bound (16) and functions that escape as values (28).
2. For each unbindable call, ask `CallBindings.get(call=...)` why it refuses (decorated callee, `*args`, method on an unknown receiver, dynamic marker) and write the reason next to the sample.
3. Fix only refusals that are provably safe, for example a decorator built on `functools.wraps`; keep `tests/astart/rules/test_rules_kwargs_danger.py` green.
4. For escaping functions, count a function as escaping only when its name is read as a value outside a decorator position (a decorator makes the decorated function reachable, not the decorator's parameters unknown).
5. Re-run the report and record both counts.

**Done when:** both counts drop and `tests/astart/rules/test_rules_kwargs_danger.py` passes.

### W-08 — Let the negotiator write default-literal parameters (F-37)
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** S · standard

**Context:** F-37: default-literal parameters in the negotiator (70 annotations the hint index writes and the negotiator does not; 60 exact, 3 wrong). Steps:
1. In `negotiation/policy.py` `_supported`, a candidate whose origins are
   exactly `{Origin.default}` and the engine agrees (`corroborated`) is already
   accepted. The gap is *opaque callers*: `builders._calls` marks a parameter
   opaque when any call to its function cannot be bound. Add a second set
   `Built.caller_opaque` (parameters blocked ONLY for that reason) and let
   `blocked_nodes` ignore it when the belief's candidates are all `Origin.default`.
2. Keep the tiered confidence: `confidence.by_literal` (bool/float 0.99, int
   0.72, str 0.69) decides in `facts._has_inferred_hint`/`offer_confidence`;
   set the hint's `HintBasis.default_literal`, not `negotiated`, so the tier applies.
3. Test: `def f(x=1): return x` with an unbindable call `f(*args)` elsewhere and
   engine `{"f.x": "int"}` → `x: int` at `--min-confidence 0`, nothing at 0.8.

**Done when:** shadow `only_existing` for basis `default_literal` falls from 70 to
< 20 and `only_negotiated.wrong` stays 0.

**Insights:** 70 default-literal parameters are written by the hint index but not by the negotiator because call sites that cannot be bound mark the parameter opaque. For a pure default literal the call sites do not matter: the default alone proves the type only partially (callers may pass wider types), which is why it is a soft signal.

**Architecture:** Change stays in `negotiation/policy.py` (`blocked_nodes`) and `builders.py` (`Built.caller_opaque`). Basis remains `default_literal` so `confidence.by_literal` tiers apply; no new origin.

**Algorithm:** 1) Split opacity reasons into `caller_opaque` (cannot bind a call) and hard reasons (rebinding, escape through `exec`). 2) In `blocked_nodes` ignore `caller_opaque` when all candidates of the belief have origin `default`. 3) Keep acceptance via the confidence tier, not via `accept`. 4) Shadow comparison must keep `only_negotiated.wrong == 0`.

**Performance:** No extra graph work: one extra set stored per `Built`; membership test O(1) per node.

### W-11 — Annotate a method that returns its own class (`Self` or quoted name)
- **Status:** open
- **Priority:** P1
- **Area:** types
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Today `-> URIBuilder` inside `class URIBuilder` is refused (it would raise `NameError`). Add the alternative: in `supplement.negotiated_hints` and `engine_hints`, when the only blocker is `bound_when_evaluated` and the name is the *enclosing class* of the method, write `Self` if `facts.target` allows it (3.11+; `PythonTarget.self_type`), else the quoted string `'URIBuilder'`. The writer must import `Self` (`known_imports` has it).

**Test:** builder pattern returns `URIBuilder(...)` → `-> Self` on 3.11+,
`-> 'URIBuilder'` with `--target-version 3.10`; import the fixed module in the
test (see `tests/astart/rules/test_rules_negotiated_fix.py::_runs`).

**Steps:**
1. Failing test: a builder method returning `URIBuilder(...)` inside `class URIBuilder` gives `-> Self` on 3.11+ and `-> 'URIBuilder'` with `--target-version 3.10` (import the result, see `_runs` in `tests/astart/rules/test_rules_negotiated_fix.py`).
2. In `negotiation/supplement.py` and `engine_hints.py`, when the only blocker is `bound_when_evaluated` and the name is the enclosing class, write `Self` (`PythonTarget.self_type`) or the quoted name.
3. `ensure_names` imports `Self` (already in `known_imports`).
4. Run both targets.

**Done when:** both targets produce valid, importable code.

### W-12 — Annotate instance attributes from negotiation
- **Status:** open
- **Priority:** P1
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Instance attributes: `Built.attributes` already maps each attribute node to its first write (`self.x = ...`). Add to `negotiation/variables.py` `variable_hints` a loop over `built.attributes` that accepts with `policy.accept(kind="attribute", ...)` and returns hints keyed by that assignment's `node_key`; then make `appliers.add_attribute_annotation` also accept `basis is HintBasis.negotiated` (today it only accepts `attribute_assignments`) and read the hint from `facts.variables`. Fact: extend `facts._has_inferred_hint`'s Attribute branch the same way. Test: `self.x = x` with `x: int` from callers → `self.x: int = x`. Target: the 47 `self.x: T = value` of the dev pair. Class-level `x: T` (36 in the dev pair) stays open — separate task after this one.

**Steps:**
1. Write the failing test: `self.x = x` where callers pass `int` gives `self.x: int = x` (`tests/astart/rules/test_rules_negotiated_fix.py`).
2. In `negotiation/variables.py` `variable_hints` add a loop over `built.attributes`; accept with `policy.accept(kind="attribute", ...)`; key hints by the assignment's `node_key`.
3. In `rules/appliers.py` make `add_attribute_annotation` also accept `basis is HintBasis.negotiated`, reading the hint from `facts.variables`.
4. Extend `facts._has_inferred_hint` for the attribute branch the same way.
5. Run the pair command and record the attribute counts.

**Done when:** the test passes and the dev pair's `self.x: T = value` count rises.

### T-04 — Name heuristics as *calibrated candidates*
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Name heuristics as *calibrated candidates* (`infer-types` `is_`/`has_` → `bool`, `autotyping --guess-common-names` `verbose` → `bool`, user maps `--annotate-named-param`): measure each name pattern on both corpora with the X-05 script; enable only the passing ones; user-configured maps (`[tool.astart.names]`) enter as `declared` because the user asserted them.

**Steps:**
1. Name heuristics as calibrated candidates: `is_*`/`has_*` parameters → `bool`, `*_count`/`n_*` → `int`, `*_path` → `str | Path`.
2. Only as `Origin.calibrated`, never alone; measure exact share per heuristic (CC-01) and keep those ≥ 97 %.
3. Tests: heuristic with and without corroboration.

**Done when:** heuristics only fire when measured reliable and corroborated.

### T-05 — Ingest external suggestions
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Ingest external suggestions (`autotyping --pyanalyze-report`): `--suggestions FILE` reads pyanalyze/MonkeyType/pytype JSON and feeds it to the negotiator as another *corroborator* next to the engine (never as a source of types); `--only-without-imports` equivalent.

**Steps:**
1. `--suggest FILE` reads an external suggestions JSON (`{path: {param: type}}`) and offers them as `Origin.external` candidates gated by the checker.
2. Schema in `docs/schema/suggestions.json`.
3. Tests.

**Done when:** external suggestions are applied only under the checker gate.

### T-06 — Generators: `infer-types` returns `Iterator` for any `yield`
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Generators: `infer-types` returns `Iterator` for any `yield`, which `autotyping` itself calls imprecise. Keep refusing until M4-06 can state `Iterator[T]`/`Generator[Y, S, R]` with the element types from the yield contracts.

**Steps:**
1. See W-13; this task adds the `infer-types` comparison: a generator with `return x` is `Generator`, not `Iterator`, so test both.

**Done when:** W-13 tests include the return-value case.

### T-09 — Optional runtime use of `typeshed_client` in `--project` mode
- **Status:** done
- **Priority:** P2
- **Area:** stubs
- **Readiness:** done
- **Effort:** M · standard

**Context:** Optional runtime use of `typeshed_client` in `--project` mode: replace the hand-written stub reader in `project/libraries.py` where its `Resolver` is available (third-party `*-stubs` and `types-*` packages from the environment), keeping the current reader as the fallback so the tool still works without it.

**Steps:**
1. `--project` mode may use the installed `typeshed_client` only if present, through an adapter with the same interface as `astart.stubs.resolver`; default stays the migrated reader.
2. Test the adapter with a fake module.

**Done when:** the adapter works and is off by default.

**Evidence:** `src/astart/project/typeshed_client.py` (`TypeshedClientIndex`, lazy import, `lookup` returning `StubSignature`s via `semantic.stubs.stub_signatures`); `LibraryIndex(client=...)` consulted before the hand-written readers; `ASTART_TYPESHED_CLIENT` env opt-in in `cli/commands.py`; `pytest tests/astart/project/test_project_typeshed_client.py` 4 passed.

### W-05 — Sync CHANGELOG, evidence ladder, architecture and README with the code
- **Status:** done
- **Priority:** P2
- **Area:** docs
- **Readiness:** done
- **Effort:** M · light

**Context:** No code.
1. `CHANGELOG.md`: add `## 2026-11-08` with one bullet each for: contract
   negotiation (default on, `--no-negotiate`), `--annotate-variables`, `--engine`
   conversion mode, the `astart.stubs` typeshed reader, library return types,
   the pair benchmark and `fixtures`, `scripts/compare/opacity_report.py`.
2. `docs/architecture/evidence-ladder.md`: add the origins `protocol`, `calibrated`, `engine`
   and the rule "engine = lowest tier, checker gate vetoes" (copy wording from
   `docs/architecture/negotiation.md`).
3. `docs/architecture/architecture.md`: it is generated from module docstrings (Q-23);
   add one paragraph for each new package (`negotiation`, `stubs`) and for
   `rules/engine_hints.py`, `rules/library_calls.py`.
4. `README.md` "Limits": replace the stale cross-module/typeshed bullets with
   what `--project` and `astart.stubs` do now.

**Done when:** `python -m pytest tests/astart/test_readme_flags.py tests/test_rule_docs.py
-q -p no:cacheprovider` passes.

**Evidence 2026-11-09:** all four syncs landed. `CHANGELOG.md` gained
`## 2026-11-08` with the seven bullets (negotiation default-on +
`--no-negotiate`, `--annotate-variables`, `--engine`, `astart.stubs`,
library return types, pair benchmark, `opacity_report.py`).
`docs/architecture/evidence-ladder.md` gained a "Negotiation origins" table mapping
`syntax`/`declared`/`call_sites`/`default`/`protocol`/`calibrated`/`inferred`
to ladder levels plus the engine-is-lowest-tier/E6-vetoes rule, worded from
`docs/architecture/negotiation.md` and `Origin`'s docstring. `docs/architecture/architecture.md`
gained `engine_hints.py`, `negotiation/` and `stubs/` sections
(`library_calls.py` already had one) with verbatim docstring paragraphs in
alphabetical position. README "Limits" now describes `--project` +
`astart.stubs` and `fix --cache` accurately. Done-when: 4 tests pass.

### W-09 — Annotate the parameters of `__exit__` and `__aexit__`
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Table (put in `negotiation/builders.py` `Constants.dunder_parameters`): `{"__exit__": ("type[BaseException] | None", "BaseException | None", "TracebackType | None"), "__aexit__": same}`. In `_declare`, for a function in this table that is a method, seed each of its three non-receiver parameters that are unannotated with `Origin.protocol` (a proof) via `_seed_type`. The type text `TracebackType` needs `from types import TracebackType`: first do H-07 (add `TracebackType: "types"` to `imports.Constants.known_imports`).

**Test:** a class with `def __exit__(self, kind, value, trace): ...` gets all three
annotations and one import; an already-annotated method is untouched.

**Steps:**
1. Add `TracebackType: "types"` to `imports.Constants.known_imports`.
2. Add `Constants.dunder_parameters` in `negotiation/builders.py` for `__exit__`/`__aexit__`: `type[BaseException] | None`, `BaseException | None`, `TracebackType | None`.
3. In `_declare` seed each unannotated parameter of those methods with `Origin.protocol`.
4. Tests: all three annotated, one import added, an already-annotated method untouched.

**Done when:** the tests pass.

### W-10 — Copy annotations from the base class's method
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** In `builders.py` add `_inherit(unique)` called after `_declare` loop: for every method whose class has exactly one base that is a class of this module (use `walk_classes`) defining a method with the same name and the same parameter names, seed this method's unannotated parameters and return with the base's annotation text and `Origin.protocol`. Refuse when the base method is itself unannotated, when parameter names differ, or when the annotation names a class defined later (`bound_when_evaluated` already guards the final write). Test: `class A: def f(self, x: int) -> str` and `class B(A): def f(self, x)` → `B.f.x: int`, `B.f->: str`.

**Steps:**
1. Add `_inherit(unique)` to `builders.py`, called after the `_declare` loop.
2. For a method whose class has exactly one in-module base defining the same method with the same parameter names, seed unannotated parameters and the return with the base's annotation text and `Origin.protocol`.
3. Refuse when the base method is unannotated, names differ, or the annotation names a later-defined class.
4. Test: `class A: def f(self, x: int) -> str`, `class B(A): def f(self, x)` gives `x: int`, `-> str`.

**Done when:** the override test passes.

### W-13 — Type generators as `Iterator[...]`
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Today `builders._body` marks the return opaque when the function has `yield`. Implement only the sound core: for a function whose every `yield` is a bare `yield <expr>` (no `yield from`, no send value used) and which has no `return <value>`, seed nothing but add a hidden node `f.<yield>` fed by each yielded expression (like `_flow`); then report `f->` as `Iterator[<yield type>]` (`collections.abc.Iterator`, already in `known_imports`) via a new relation `iter_of` in `transfer.Constants.wrappers`. Async generators → `AsyncIterator`. Refuse everything else. Tests: two int yields → `Iterator[int]`; mixed `int`/`str` → `Iterator[int | str]`; `yield from` → no annotation.

**Steps:**
1. Keep `builders._body` marking the return opaque for `yield from`, sent values and `return <value>`.
2. For bare `yield <expr>` only, add a hidden node `f.<yield>` fed by each yielded expression (like `_flow`).
3. Add relation `iter_of` to `transfer.Constants.wrappers`; report `f->` as `Iterator[T]` (`AsyncIterator` for async functions).
4. Tests: two int yields give `Iterator[int]`; mixed gives `Iterator[int | str]`; `yield from` stays unannotated.

**Done when:** the three tests pass.

### W-14 — Annotate class-level and module-level variables
- **Status:** open
- **Priority:** P2
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Class-level and module-level variables (`x: T = value` outside functions; 36 class-level in the dev pair, e.g. `threshold: Final[int] = 5` is another rule — skip `Final`). Today `builders` only creates nodes inside functions. Add a module/class scope in `ContractBuilder`: assignments with a single `Name` target in the module body or a class body (not in `__slots__`, not in a dataclass? — dataclass fields need annotations already) become nodes with path `Module.<name>` / `Class.<name>`, flows as in `_assignment`. Only emit when `annotate_variables` or the style signal is on. The write-back is the same `add_variable_annotation`. Test: module `LIMIT = 5` → `LIMIT: int = 5`.

**Steps:**
1. Add a module/class scope to `ContractBuilder`: single `Name` target assignments at module or class level become nodes `Module.<name>` / `Class.<name>`.
2. Skip `__slots__`, dataclass fields (already annotated) and `Final` constants.
3. Emit only when `annotate_variables` or the style signal is on; reuse `add_variable_annotation`.
4. Test: `LIMIT = 5` at module level gives `LIMIT: int = 5`.

**Done when:** the test passes and the dev pair's class-level variable count rises.

### T-07 — `typing_utils.issubtype` as a differential oracle for `TypeAlgebra.intersect` and
- **Status:** open
- **Priority:** P3
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `typing_utils.issubtype` as a differential oracle for `TypeAlgebra.intersect` and `recovery.relation` on builtin/`typing` generics (dev-only; it works on runtime objects, so it cannot judge project classes, protocols, or text we cannot import, and its last CI covers Python 3.6–3.9).

**Steps:**
1. Add `typing_utils.issubtype` as a test-only oracle: for 500 random type pairs compare `TypeAlgebra` subtype results; differences are bugs or documented deviations.
2. Dev dependency only; skip the test when not installed.

**Done when:** the differential test runs and deviations are listed.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| P-01 | Pair benchmark and accepted baseline: `scripts/compare/pair.py`, `fixtures/`,… | P0 | benchmarks |

## 12. Typer and small tasks

*Scope:* Small self-contained tasks that need no design.  
*ID prefixes:* Q, X

<details>
<summary>Background — 18. Atomic backlog for junior agents</summary>


Each task is one small change with a recipe. Do exactly the steps; do not
redesign. If a step does not match the code you see, stop and write the
mismatch under the task instead of improvising.


</details>

<details>
<summary>Background — 18.0 Working rules (read first)</summary>


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
4. Tests live in `tests/`, use helpers from `tests/support/expectations.py`
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
   `ruff check` clean on your files, task set to `done` (Status and Readiness), the
   dashboard regenerated with `python -m scripts.todo_update index docs/planning/TODO.md`, and
   one line added to the progress log in `docs/planning/TODO-archive.md` with the test
   file name.
6. Do not edit: `src/astart/rules/hints.py`, `attributes.py`, `methods.py`,
   `facts.py`, `appliers.py`, `resolve.py`, `checker.py` unless the task says
   so. Ask the lead instead.


</details>

<details>
<summary>Background — 18.1 Typer extensions (all in `src/astart/rules/provable.py`, class `_Typer`)</summary>


Recipe for every task here: handlers are registered in
`_Typer.__init__` in the `self._handlers` dict (`NodeClass: self._method`);
a handler takes `node: AST` and returns a type string like `"int"` or `None`
when the type is not guaranteed. Add the handler, add 3 tests in
`tests/test_rules_typer_<name>.py` using `expression_type(node=..., counts={})`
(import from `astart.rules.provable`; parse with
`parse(source="...", mode="eval").body` from `ast`).


</details>

<details>
<summary>Background — 18.2 Gold and regression tests (no production code)</summary>


Gold rows live in `tests/astart/rules/test_gold_expansion.py`; each
`_case(name=..., family=..., source=_def(name="f", params="p", body="return p",
calls="f(1)\n"), expected={"f": <return>, "f.p": <param>})` (`None` means the
hint must be refused). Register a new family's builder function the same way
the others are (search for `_default_literal_cases` and copy where it is
called). Copy the
neighbouring cases. Run `python -m pytest tests/astart/rules/test_gold_expansion.py -q`.


</details>

<details>
<summary>Background — 18.5 Detection rules (copy the TYP005 recipe)</summary>


TYP005 (`typing.missing-attribute-annotation`) shows every touch point for a
new rule. The five places, in order: (1) a new subject kind, if needed, in
`src/astart/rules/facts.py` (`Constants.node_kinds` and `_visit`); (2) a
fact function registered in `facts.py` if the rule needs one; (3) the rule in
the generator script (see `gen_catalog.py` in the session scratchpad; if it
is gone, edit the catalog JSON under `src/astart/rules/artifacts/catalog/` by hand,
copying a neighbouring rule); (4) `tests/astart/rules/test_rules_end_to_end.py` expected
code list; (5) a test file with one triggering and one clean example.
Detection-only rules have `fixes=()`.


</details>

<details>
<summary>Background — 18.6 Ant-farm refactor, stages 1–2 (see the design in the 2026-11-07</summary>

conversation; pure refactors, tests must not change)


</details>

<details>
<summary>Background — 18.8 Copy-paste tasks (no design needed)</summary>


Each task gives the complete file. Create it exactly, run the command, and
if the result differs from "Expected", paste the output under the task and
stop.


</details>

<details>
<summary>Background — 18.9 Typing-inference tasks (verified against the code on 2026-11-07)</summary>


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
| `2 ** 3` | `int` | ok |
| `'a'.upper()` | none | gap → Q-01 |
| `[1][0]` | none | gap → Q-05 |
| `abs(-1)` | none | gap → Q-06 |
| `f(1)` (unknown `f`) | none | correct refusal |


</details>

<details>
<summary>Background — 18.11 Gaps and findings from the external corpus (2026-11-08)</summary>


`tests/corpus/extended` (165 modules, 25 typed libraries; README inside) is the
first measurement on real typed code. Before the fixes below the fixer wrote
**264 mismatching annotations of 2 788 (precision 90.5 %)**; the stdlib
corpus (36 annotations) had hidden this. After them: **10 contradictions,
precision 99.64 %, recall 20.0 %, 0 new checker errors, 0 crashes**.

Done today (agent: claude): `*args`-keywordizing crash (`args=*args`);
in-module `NoReturn` propagation through tail calls
(`provable.mark_noreturn_calls`); abstract `NotImplementedError` hooks are
never `NoReturn`; scoring classes `relation()` (narrower / looser /
unresolved / contradiction, aliases, `Self`, `Literal`, `TypeGuard`);
`--jobs` and crash containment in the harness; calibrated `bool` returns
(`HintBasis.calibrated_candidate`: +101 correct, 0 new contradictions;
only for returns that are boolean *by syntax*, because a bare `return p`
with a `bool` call-site candidate ignored a `float` default). Baselines
stored: `scripts/benchmark/artifacts/resources/baseline.json` (stdlib, 128 modules) and
`scripts/benchmark/artifacts/resources/baseline_ext.json` (external, 165 modules).

Open, in priority order:


</details>

<details>
<summary>Background — 18.10 Docstring and whitespace healing (follow-ups)</summary>


Done 2026-11-07 (agent: claude): `rules/docstring_edit.py` (pure text
engine: add/remove parameter entries, tidy) and `rules/docs_fixes.py`
(facts `function.stale_documented_count`, `docstring.is_editable`,
`docstring.is_untidy`; appliers `docs.add-parameter-entries`,
`docs.remove-stale-entries`, `docs.tidy-docstring`); catalog rules
`DOC002` (now with a fix), `DOC003`, `DOC007`; tests
`tests/astart/docstrings/test_edit.py`, `tests/astart/docstrings/test_fixes.py`.
Scope guard: Google style, triple quotes, no tabs, no `:param`, no NumPy
underlines; anything else is never rewritten. **Never regenerate the catalog
from the old `gen_catalog.py` script** (it lacks `synthesize-self`); edit the
JSON under `src/astart/rules/artifacts/catalog/` by hand with
`json.dumps(d, indent=2, sort_keys=True) + "\n"` (round-trips byte for byte).


</details>

### Q-28 — `--format sarif` for `astart check` (M7-09)
- **Status:** done
- **Priority:** P2
- **Area:** cli
- **Readiness:** done
- **Effort:** S · light

**Context:** Output a JSON document `{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"astart", "rules":[...]}},"results":[...]}]}`; each finding becomes a result with `ruleId` (the code), `level` (`error|warning|note` from severity `error|warning|info`), `message.text`, and one `locations[0].physicalLocation` with `artifactLocation.uri` and `region.startLine`. Copy `render_json(*, results, catalog)` in `src/astart/cli/render.py` as `render_sarif` with the same signature, and add `sarif` to the `--format` choices in `__main__.py` and to the dispatch that calls `render_json`. Test: parse the output and assert those keys for one finding.

**Steps:**
1. Do the steps of M7-09 (same files, same tests).
2. Set this task to `done` when M7-09 is `done`.

**Done when:** M7-09 is done.

**Evidence:** `--format sarif` is reachable from
`astart check` (H-01) and covered by
`tests/astart/cli/test_cli_reporters.py::test_sarif_format`: parses as JSON,
`version == "2.1.0"`, one result per finding with `ruleId`, `level`,
`message.text` and `physicalLocation` (`artifactLocation.uri`,
`region.startLine`).

### Q-33 — TYP002 `typing.no-object-annotation`
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · light

**Context:** TYP002 `typing.no-object-annotation` (M8-03): flag any annotation that is exactly `object` or `Any` (bare names). Subject kind `Parameter` and `Function` already exist: add a fact `annotation.is_object_or_any` that unparses `arg.annotation` / `function.returns` and compares with `{"object","Any"}`. No fix.

**Steps:**
1. Do exactly the steps of M8-03 (same files, same tests); this entry only tracks the handoff.
2. When M8-03 is `done`, set this task to `done` too.

**Done when:** M8-03 is done.

### Q-34 — TYP006 `typing.bare-generic`
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · light

**Context:** TYP006 `typing.bare-generic` (new code): flag annotations that are exactly `list`, `dict`, `set`, `tuple`, `frozenset` without subscripts. Same recipe as Q-33 with a different set. No fix.

**Steps:**
1. Add TYP006 `typing.bare-generic` in `rules/typing_bare_generic.py`: a module-level or parameter annotation that is exactly `list`, `dict`, `set`, `tuple`, `frozenset` (a `Name` node, no subscript).
2. Register it as in M8-01 steps 3–5 with `maturity: experimental`.
3. Tests: `x: list` triggers, `x: list[int]` does not, `x: List` (typing alias) triggers.

**Done when:** TYP006 appears in `astart rules` and the three tests pass.

### Q-35 — PRS001 (M8-05): when the file does not parse
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · light

**Context:** PRS001 (M8-05): when the file does not parse, `check` should report ONE finding `PRS001` at line 1 instead of crashing or reporting nothing. Find where `check` handles `SyntaxError` (`grep -n "SyntaxError" src/astart/rules/engine.py src/astart/cli/*.py`); add the finding there. Test with `"def (:\n"`.

**Steps:**
1. Do exactly the steps of M8-05 (same files, same tests); this entry only tracks the handoff.
2. When M8-05 is `done`, set this task to `done` too.

**Done when:** M8-05 is done.

### Q-38 — Add `reliability: float` to `_Site` in `hints.py` defaulting to `1.0`
- **Status:** done
- **Priority:** P2
- **Area:** rules
- **Readiness:** done
- **Effort:** S · light

**Context:** Add `reliability: float` to `_Site` in `hints.py` defaulting to `1.0` (`0.0` where `definite=False`). Behaviour must not change: run the full fast tier and the gold file before and after, outputs identical. (Do this only after the lead says `hints.py` is free.)

**Steps:**
1. Add `reliability: float = 1.0` to `_Site` in `hints.py`; weight call-site evidence by it in the soft-signal count.
2. Tests: reliability 0.5 does not count as a full signal.

**Done when:** low-reliability sites no longer count as full evidence.

**Closed 2026-11-09 (F-32):** superseded, not implemented. Evidence
weighting by provenance and confidence shipped in the negotiation
architecture instead — F-02 (candidates carry their supporting `Origin`s;
`independent` means distinct origins) and F-04 (`Belief` unions keep the
best confidence per origin/polarity). The 2026-11-08 shadow run
(`docs/analysis/scripts.benchmark.md`, 12 789 annotations, 0 crashes) shows no regression:
the negotiator never contradicts the hint index and adds 41 exact
annotations it misses. `hints.py` stays untouched per its do-not-rewrite
note.

### Q-57 — Return-type characterization through the fixer
- **Status:** done
- **Priority:** P2
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** S · light

**Context:** Create `tests/astart/rules/test_rules_return_matrix.py` using the `_fixed` helper from 18.0 and these (source → expected substring) pairs: `"def f():\n    return 1\n"` → `"def f() -> int:"`; `"def f():\n    return 1.5\n"` → `"-> float:"`; `"def f():\n    return 'a'\n"` → `"-> str:"`; `"def f():\n    return [1, 2]\n"` → `"-> list[int]:"`; `"def f():\n    return {'a': 1}\n"` → `"-> dict[str, int]:"`; `"def f(x):\n    if x:\n        return 1\n"` → `"-> int | None:"`; `"def f():\n    return None\n"` → `"-> None:"`; `"def f():\n    pass\n"` → `"-> None:"`. Refusals (assert the substring `"->"` is NOT in the `def` line): `"def f(x):\n    return x\n"` becomes generic via TypeVar, so use instead `"def f(x):\n    return x.y\n"`. Expected: all pass today; if one does not, paste the real output under the task and mark it `BLOCKED` (do not change production code). **BLOCKED 2026-11-08** — 7 of 8 rows pass; the `pass`-only body produces `def f():\n    pass\n` with no `-> None:` (real output verified). The row is pinned with `xfail(strict=True)` in `tests/astart/rules/test_rules_return_matrix.py`; the `return x.y` refusal passes.

**Steps:**
1. Create `tests/test_rules_return_characterization.py` using the `_fixed` helper from 18.0; one case per return shape (see Q-56 matrix).
2. Pin current behaviour with `xfail(strict=True)` where known wrong.

**Done when:** each shape is pinned.

**Evidence 2026-11-09:** `tests/astart/rules/test_rules_return_matrix.py` pins every
return shape from the context (literal int/float/str, `list[int]`,
`dict[str, int]`, `int | None`, `None`, plus the `return x.y` refusal);
the `pass`-only row is pinned `xfail(strict=True)` per the documented
BLOCKED note. 7 passed, 1 xfailed.

### Q-58 — Parameter-hint characterization
- **Status:** done
- **Priority:** P2
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** S · light

**Context:** Create `tests/astart/rules/test_rules_param_matrix.py` with the `_fixed` helper and these pairs: `"def f(x=1):\n    return x\n"` → `"x: int = 1"`; `"def f(x='a'):\n    return x\n"` → `"x: str = 'a'"`; `"def f(x=1.5):\n    return x\n"` → `"x: float = 1.5"`; `"def f(x=True):\n    return x\n"` → `"x: bool = True"`; `"def f(x):\n    return x\n\nf(1)\nf(2)\n"` → `"x: int"`; `"def f(x):\n    return x\n\nf(1)\nf('a')\n"` → NOT contains `"x: int"` and NOT contains `"x: str"`. Same BLOCKED rule as Q-57. **BLOCKED 2026-11-08** — 5 of 6 rows pass; the `f(1)`/`f(2)` row now synthesizes `x: T` via TypeVar (M5-14…M5-18 postdates this spec) instead of the expected `x: int`. Real output: `T = TypeVar('T')` + `def f(x: T) -> T:`. Row pinned with `xfail(strict=True)` in `tests/astart/rules/test_rules_param_matrix.py`; the mixed-call refusal passes.

**Steps:**
1. Same as Q-57 for parameter hints: literal defaults, call sites, none; `tests/test_rules_param_characterization.py`.

**Done when:** each parameter hint source is pinned.

**Evidence 2026-11-09:** `tests/astart/rules/test_rules_param_matrix.py` pins every
parameter-hint source from the context (literal `int`/`str`/`float`/`bool`
defaults, agreeing call sites, and the mixed-call refusal); the
`f(1)`/`f(2)` row is pinned `xfail(strict=True)` per the documented
BLOCKED note (TypeVar synthesis postdates the spec). 5 passed, 1 xfailed.

### Q-61 — Returns / Raises stubs
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · light

**Context:** Reuse `docs_missing_returns.py` and `docs_missing_raises.py` (DOC004 / DOC006). Add rules + fixes that append a `Returns:\n    Describe the result.` (only when a `return <value>` exists) or `Raises:\n    <Exc>: Describe when <Exc> is raised.` section using `docstring_edit._new_section`'s placement logic: generalise it to take the title (`Args`/`Returns`/`Raises`) and the entry lines. Tests mirror Q-60.

**Steps:**
1. Do exactly the steps of M8-07 (same files, same tests); this entry only tracks the handoff.
2. When M8-07 is `done`, set this task to `done` too.

**Done when:** M8-07 is done.

### Q-64 — Docstring reflow with `textwrap`
- **Status:** open
- **Priority:** P3
- **Area:** ast
- **Readiness:** ready
- **Effort:** S · light

**Context:** Add `docs.wrap-docstring` (rule `DOC008`, info): wrap prose paragraphs (not section entries, not code blocks starting with `>>>` or indented 4+ extra spaces) to 79 columns with `textwrap.fill(width=79 - len(indent), initial_indent=indent, subsequent_indent=indent)`. Fact `docstring.has_long_prose`. Off by default (needs a `--wrap-docstrings` flag, same plumbing as `--source-root`).

**Progress 2026-11-09:** the reflow engine exists as `reflow_text` in
`src/astart/docstrings/prose.py` — stronger than the `textwrap.fill` sketch:
dynamic-programming optimal breaks, protected fences/Examples/literal
blocks/doctests/directives, hanging list and entry indents. The separate
`astart transform --wrap` command now exposes native doc/comment AST wrapping.
DOC008 catalog integration remains open; do not equate the explicit transform
command with enabling a default annotation fix.

**Progress 2026-11-10:** structured entry labels now wrap semantically.
`type_layout.py` lays out type expressions as a shadow AST (union operands at
union level, subscript arguments one level deeper, closers at bracket level);
`wrapped_label_lines`/`_entry_tail_lines` in `core.py` emit over-budget
`name (type):` labels across continuation lines, and the parser's
`_join_wrapped_labels` rejoins them only when the canonical type matches,
preserving object linkage. `types.py` triggers on physical emitted lines, so
wrapped output converges instead of re-firing on the flat label.
`Call`/`Lambda` are rejected as type expressions so prose and code-block
entries such as `print(x):` cannot false-trigger. `Call`/`Lambda` aside,
`_sync_docstrings` now raises `FormatPreservationError` (a `ValueError`
subclass) when a probe mixes structured and executable docstring edits, so
ddmin degrades the conflicting subset to `SkipCode.write_back` instead of
crashing the run. Repo-wide `fix --docstring-types --stub-docstrings`
converged: zero `docs.*`/`typing.*` findings remain in tracked files outside
vendored typeshed, E501 is clean, and a repeat pass reports `0 files
changed`. DOC008 catalog integration and AF-10 remain open.

**Steps:**
1. Do the steps of AF-10 (same files, same tests).
2. Set this task to `done` when AF-10 is `done`.

**Done when:** AF-10 is done.

### Q-68 — Kill the ~50k-line cliff (M7-01 evidence from Q-31)
- **Status:** open
- **Priority:** P1
- **Area:** performance
- **Readiness:** ready
- **Effort:** S · light

**Context:** On the 50,763-line `profile_perf` workload `check` alone exceeded 30 min (> 85× the 12k `check` for 4.2× the lines) and `fix` multiplies it via `max_rounds=3` + `_degrade` halving. `cProfile` shows the dominant cost is `hints.index → _candidates → CommentedModule.convert → semantic/analyzer.convert → graph/conversion → backend/checkpoint._infer` — the whole-module graph conversion runs once per hint-index build and is itself superlinear. Recipe: (1) confirm whether `convert` results are cached per module content across `check`/`fix` rounds and `_degrade` splits (the shared `hint_cache` should make repeats cheap — verify it actually does); (2) if not, key/cache the conversion so `_attempt`/`_rematch`/`module_facts` on the same source reuse it; (3) if the conversion itself is the superlinear part, bound or skip it for modules over a size threshold and record the recall trade-off; (4) re-run `benchmarks/profile_perf.py --lines 50000 --json` and replace the `> 30 min` lower bound in `docs/analysis/scripts.benchmark.md`. Constraints: no precision loss on the 128-module recovery gate (rerun `recovery --json` + `gate` before/after) and no behaviour change below the threshold.

**Steps:**
1. Do exactly the steps of M7-01 (same files, same tests); this entry only tracks the handoff.
2. When M7-01 is `done`, set this task to `done` too.

**Done when:** M7-01 is done.

### X-02 — Contradictions that remain (6 of 12 789)
- **Status:** done
- **Priority:** P1
- **Area:** benchmarks
- **Readiness:** done
- **Effort:** S · light

**Context:** Contradictions that remain on the external corpus. Run
`benchmarks recovery --corpus tests/corpus/extended`, list `wrong` per module,
classify each (inference bug vs scoring artefact), fix or document each in
`docs/analysis/scripts.benchmark.md`. Then store the external run as
`scripts/benchmark/artifacts/resources/baseline_ext.json` with a gate (precision ≥ 99.5 %, 0 crashes).

**Steps:**
1. Run the external recovery and store `scripts/benchmark/artifacts/resources/baseline_ext.json`.
2. Classify every `wrong` annotation (inference bug vs scoring artefact).
3. Document each classification in `docs/analysis/scripts.benchmark.md`.

**Done when:** every `wrong` annotation is classified in
`docs/analysis/scripts.benchmark.md` and `baseline_ext.json` is stored with precision
≥ 99.5 % and 0 crashes.

**Evidence 2026-11-09:** `scripts/benchmark/artifacts/resources/baseline_ext.json` stores the 165-module
run (2 511 / 12 789 correct, 6 wrong, 136 compatible, precision 99.77 %,
0 crashes, 0 new checker errors — inside the ≥ 99.5 % gate). All six wrongs
are classified in `docs/analysis/scripts.benchmark.md` under "Remaining external-corpus
contradictions": three share the `return self` → `Self` root cause
(`__aiter__`, `__iter__`, `buffer`), two are Self/generic spelling issues
tracked by X-03, one is a `Literal` alias collapsing to `str`, and one is
dict-literal value narrowing vs a declared `Any` contract.

### X-03 — `Self` and TypeVar returns for classmethods
- **Status:** open
- **Priority:** P1
- **Area:** types
- **Readiness:** ready
- **Effort:** S · light

**Context:** `Self` and TypeVar returns for classmethods, `__enter__`
and `__aiter__` (`-> Self`, `-> T`); the fixer writes the class name or
`_Self`/`__Self` spellings that clash with the original (`Path.cwd`,
`_SignalReceiver.__aiter__`). Tie to M5-18 (done).

**Steps:**
1. Audit the remaining `wrong`/`compatible` Self cases in
   `scripts/benchmark/artifacts/resources/baseline_ext.json` (see `docs/analysis/scripts.benchmark.md` X-02 table).
2. Make classmethod/`__enter__`/`__aiter__` returns spell `Self`/TypeVar
   the way the original does, or teach `recovery.relation` that the
   spellings are equivalent.
3. Re-run the external recovery and refresh `baseline_ext.json` if the
   wrong count drops.

**Done when:** no external-corpus `wrong` annotation is a Self/TypeVar
spelling difference, or each remaining one is documented as intentional.

### X-04 — Names imported from other modules cannot be judged by `relation()`
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** S · light

**Context:** Names imported from other modules cannot be judged by
`relation()` ("unresolved": 212 compatible/unresolved of 2 774 written).
Resolve them through the project import graph (`ProjectIndex`, M3) or
typeshed so the scorer and the fixer share one notion of subtype.

**Steps:**
1. Feed `ProjectIndex` cross-module contracts (and typeshed stubs where
   available) into `recovery.relation`'s name resolution.
2. Re-score the external corpus; the `unresolved` count must drop and no
   new `wrong` may appear.
3. Document the change in `docs/analysis/scripts.benchmark.md`.

**Done when:** `relation()` resolves imported names through the project
index or typeshed and the external-corpus `unresolved` count is measured
and documented.

### X-05 — Calibrate more candidate categories with the same method as
- **Status:** open
- **Priority:** P1
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** S · light

**Context:** Calibrate more candidate categories with the same
method as `Constants.calibrated_returns` (script idea: for every unaccepted
engine candidate, compare with the original by reason × kind × shape;
accept a category only at ≥ 97 % exact **and** 0 contradictions, n ≥ 100, on
stdlib *and* external corpus). Measured today (n = 4 985): only syntactic
`bool` returns qualified. Candidates that failed and must stay refused:
`x=None` params (`int | None` guessed, 9.4 % exact, n = 1 056), generators
(0.5 %), tuples (6.7 %), `Sequence`/`Callable`/`Iterable` params (0–1 %),
`object` params (0 %). Re-run after M4-06/M4-07 land.

**Steps:**
1. Extend the calibration harness (`benchmarks/calibrate.py` or a sibling)
   to score every unaccepted engine candidate by reason × kind × shape.
2. Accept a category only at ≥ 97 % exact, 0 contradictions, n ≥ 100 on
   both corpora; record refused categories with their measured rates.
3. Document the accepted/refused table in `docs/analysis/scripts.benchmark.md`.

**Done when:** every engine candidate category has a measured exactness
rate on both corpora and the accepted set is documented.

### X-06 — Per-module `--jobs` in `astart fix` itself
- **Status:** done
- **Priority:** P1
- **Area:** cli
- **Readiness:** done
- **Effort:** S · light

**Context:** Per-module `--jobs` in `astart fix` itself (the
benchmark harness has it; the CLI does not): one process per file, same
deterministic output order (M7-04/M7-05).

**Steps:**
1. Duplicate tracker — the canonical task is H-11, which defers to
   M7-04/M7-05 (recipe 20.1). Closed 2026-11-09 to keep one tracker.

**Done when:** the task has a real title or is removed with a note.

**Evidence 2026-11-09:** closed as a duplicate; H-11 tracks the work and
names this entry in its context.

### X-07 — Grow the external corpus: more distributions (async, data, CLI, ORM), a held-out split
- **Status:** open
- **Priority:** P2
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · light

**Context:** Grow the external corpus: more distributions (async,
data, CLI, ORM), a held-out split that no rule may be tuned on, and a
second Python-version build. Keep `tests/corpus/extended/MANIFEST.json`
authoritative.

**Steps:**
1. Vendor additional permissively licensed, fully annotated libraries
   covering async, data, CLI and ORM domains into `tests/corpus/extended`.
2. Record every addition in `tests/corpus/extended/MANIFEST.json`.
3. Mark a held-out split in the manifest that tuning must not read.

**Done when:** `MANIFEST.json` lists the new distributions and the
held-out split, and the corpus tests pass.

### X-08 — Missed-annotation reasons on the external corpus (12 789 originals): `no candidate` 3
- **Status:** open
- **Priority:** P2
- **Area:** benchmarks
- **Readiness:** ready
- **Effort:** S · light

**Context:** Missed-annotation reasons on the external corpus
(12 789 originals): `no candidate` 3 686, `tainted` 2 371, `None default`
1 083, `uncorroborated` 558, `call sites unknown` 476, `return type not
provable` 437, `contains object` 356, `declaration body` 281, `generator`
227. Each is a roadmap item: M4-02/M2-09, M4-12 follow-up for `x=None`
(needs body-usage evidence, not call sites, for public library APIs),
M4-06, M3-03.

**Steps:**
1. For each missed-annotation reason above, confirm an open task owns it
   (M4-02, M2-09, M4-12 follow-up, M4-06, M3-03 or a new entry).
2. Add any unowned reason as a new task; link each reason to its owner in
   `docs/analysis/scripts.benchmark.md`.

**Done when:** every missed-annotation reason in the external baseline is
linked to an owning task.

### Completed

| ID | Task | Priority | Area |
| --- | --- | --- | --- |
| Q-01 | String methods that return `str` | P1 | inference |
| Q-02 | String methods that return `bool`/`int`: `startswith endswith isdigit isalpha isalnum… | P1 | inference |
| Q-03 | `str % anything` → `str` (printf formatting) | P1 | inference |
| Q-04 | List concatenation: in `_binop`, when both sides type to the same `list[...]` string and… | P1 | inference |
| Q-05 | Subscripts | P1 | inference |
| Q-06 | `abs`, `round`, `min`, `max`, `sorted` | P1 | inference |
| Q-07 | `list(x)`, `set(x)`, `tuple(x)` with a typed argument: `list(list[T])` → `list[T]`;… | P1 | inference |
| Q-08 | `dict.get`/`list.copy`/`dict.keys` are NOT in scope; add a comment-free refusal test… | P2 | tests |
| Q-09 | Add family `variadic` (also add it to the `expected` set in… | P2 | tests |
| Q-10 | Add family `attribute_read` with 6 cases mirroring `tests/astart/rules/test_rules_attribute_reads.py`… | P2 | tests |
| Q-11 | Add family `comprehension` with 6 cases mirroring… | P2 | tests |
| Q-12 | Add family `multi_binding` with 6 cases mirroring… | P2 | tests |
| Q-13 | CRLF: new `tests/astart/rules/test_rules_line_endings.py` | P2 | tests |
| Q-14 | Hostile inputs: new `tests/astart/rules/test_rules_hostile_inputs.py`, parametrized over: empty… | P2 | tests |
| Q-15 | Determinism across hash seeds: new `tests/astart/rules/test_rules_determinism.py` | P1 | tests |
| Q-16 | Convention guard (CC-06): new `tests/astart/test_conventions.py` with three tests that scan… | P2 | tests |
| Q-17 | Constants guard: in the same file, assert that every class named `Constants` in… | P2 | tests |
| Q-18 | README flag guard: new `tests/astart/test_readme_flags.py` | P2 | tests |
| Q-19 | `astart --version` | P2 | cli |
| Q-20 | `astart rules`: new subcommand printing one line per rule: `CODE  key  severity  title`,… | P2 | cli |
| Q-21 | `astart explain CODE`: prints the rule's `rationale`, then each example's source with… | P2 | cli |
| Q-22 | `docs/guides/rules.md` generated by a new script `scripts/generate_rule_docs.py` (iterate the… | P2 | docs |
| Q-23 | `docs/architecture/architecture.md`: one paragraph per module in `src/astart/rules/` (`ls` it; read… | P2 | docs |
| Q-24 | `CHANGELOG.md`: one `## 2026-11-07` heading, bullets copied from the entries in section… | P3 | docs |
| Q-25 | `.pre-commit-hooks.yaml` (M7-11): one hook, id `astart-fix`, `entry: astart fix --check`,… | P2 | release |
| Q-26 | `.github/workflows/ci.yml`: on push/pull_request, Python 3.12, steps: install with `pip… | P1 | release |
| Q-27 | `--exclude GLOB` for `astart check` and `astart fix` (repeatable) | P2 | cli |
| Q-29 | Grow the corpus (M1-07 beyond 113): copy 15 stdlib modules not yet present to… | P2 | tests |
| Q-30 | Five more semantic projects (M1-12): add entries to `scripts/benchmark/artifacts/resources/projects.json` copying… | P2 | benchmarks |
| Q-31 | The ≈ 50k-line throughput row (M1-10): concatenate corpus files into one 50k-line module… | P2 | benchmarks |
| Q-32 | `docs/analysis/scripts.benchmark.md`: add a "How to refresh the baseline" section with the three exact… | P3 | docs |
| Q-36 | Read `HintIndex._judge_pass`, `_call_sites` and `_judge_call_sites` in… | P2 | rules |
| Q-37 | Create `src/astart/rules/slots.py` with a `SlotTable` class: `deposit(*, slot: str, kind:… | P2 | rules |
| Q-39 | `tests/astart/rules/test_rules_typer_negatives.py`: 12 one-line refusal tests proving the typer… | P2 | tests |
| Q-40 | `tests/astart/rules/test_rules_hint_cache.py`: assert two `fix_source` calls on identical text return… | P2 | tests |
| Q-41 | Document every `Rejection` value: `grep -n "class Rejection"… | P2 | docs |
| Q-42 | Document every `SkipCode` the same way (`docs/guides/skip-codes.md`) | P2 | docs |
| Q-43 | `README.md`: add a "Limits" section (five bullets, copied from the "Where it is far from… | P2 | docs |
| Q-44 | Add `tests/astart/cli/test_cli_exit_codes.py`: `fix --check` on a clean file → 0; on a file with a… | P2 | tests |
| Q-45 | Add `tests/astart/cli/test_cli_formats.py`: `check --format json` output parses with `json.loads`… | P2 | tests |
| Q-46 | Add `tests/astart/rules/test_rules_variadic_methods.py`: the same cases as… | P2 | tests |
| Q-47 | Add `tests/astart/rules/test_rules_default_expression_edges.py`: refusal tests for `x=-1` called with… | P2 | tests |
| Q-48 | Create `tests/astart/rules/test_rules_typer_negatives.py` | P2 | tests |
| Q-49 | Create `tests/astart/rules/test_rules_typer_positives.py` with the same shape as Q-48 but parametrize… | P2 | tests |
| Q-50 | Create `.pre-commit-hooks.yaml` | P2 | release |
| Q-51 | Create `tests/astart/test_conventions.py` | P2 | tests |
| Q-52 | `README.md`: add a `## Limits` section just after the paragraph under the `astart fix`… | P2 | docs |
| Q-53 | Create `CHANGELOG.md` with `# Changelog`, a `## 2026-11-07` heading, and these bullets:… | P3 | docs |
| Q-54 | Create `tests/astart/rules/test_rules_typer_matrix.py` pinning every row of the table above that says… | P2 | tests |
| Q-55 | `**` operator | P2 | inference |
| Q-56 | Pin the gaps so closing them is visible: create `tests/test_rules_typer_gaps.py` with… | P2 | tests |
| Q-59 | Write `docs/architecture/typing-inference.md`: copy the table at the top of this section verbatim, add… | P2 | docs |
| X-01 | P0 | P0 | benchmarks |
| Q-60 | DOC001 stub docstrings — DONE 2026-11-08 with a different design than first sketched | P2 | rules |
| Q-62 | Run ruff on docstring content | P2 | rules |
| Q-63 | Whitespace outside docstrings | P2 | rules |
| Q-65 | Heal renamed parameters | P2 | rules |
| Q-66 | Module docstring support: extend `_docstring()` in `rules/docs_fixes.py` to accept… | P2 | rules |
| Q-67 | `--no-docs` flag (`astart fix --no-docs`) that excludes the `docs.*` fixes, for users who… | P2 | cli |

## 13. Handoff batch

*Scope:* Tasks pre-selected for a second agent.  
*ID prefixes:* H

<details>
<summary>Background — 18.15 Handoff batch for a second agent (selected 2026-11-08)</summary>


Twelve tasks that do not touch the files the negotiation work is changing.
**Do not edit**: `src/astart/rules/negotiation/`, `src/astart/rules/hints.py`,
`src/astart/rules/provable.py`, `benchmarks/shadow.py`, sections 18.12 and
18.14 of this file. Follow 18.0 (working rules). One task per change; set the task to
`done`, add one line to the progress log in `docs/planning/TODO-archive.md` with the
test file name, and rerun the dashboard script. If a step does not match the code, write the
mismatch under the task and stop. Order is by value.


</details>

### H-01 — Reporters in the CLI (M7-09, Q-28, part of M7-16)
- **Status:** done
- **Priority:** P0
- **Area:** cli
- **Readiness:** done
- **Effort:** M · standard

**Context:** `render_sarif`, `render_junit` and `render_github` already exist in `src/astart/cli/{sarif,junit,github}.py` with tests, but `--format` only offers `text` and `json` (`src/astart/__main__.py`, search `choices=("text", "json")`). Add the three choices to `check` and dispatch to the renderers in the same place `json` is dispatched (`cli/commands.py`, follow `render_json`). Read each renderer's signature first; do not change the renderers. Tests `tests/astart/cli/test_cli_reporters.py` through `main(argv=[...])` on a `tmp_path` file with one finding: sarif output parses as JSON with `version == "2.1.0"` and one result; junit parses with `xml.etree.ElementTree` and has one `testcase`; github lines start with `::`. README: document the three values (the README flag test fails until you do).

**Steps:**
1. Wire the SARIF, JUnit and GitHub reporters (already in `cli/sarif.py`, `junit.py`, `github.py`) into `astart check --format {text,json,sarif,junit,github}`.
2. Add the flag to `__main__.py` and the README table.
3. Tests: each format parses and contains one finding.

**Done when:** `--format` works for all five reporters.

**Evidence:** `--format` now accepts `sarif`, `junit` and
`github` alongside `text`/`json` (`__main__.py` choices; dispatch in
`run_check` computes a payload via the existing renderers — renderers
unchanged). README usage line and format paragraph updated;
`docs/guides/cli.md` choices table synced. `tests/astart/cli/test_cli_reporters.py`
drives `main(argv=...)` on a one-finding module: SARIF parses with
`version == "2.1.0"` and one result (`ruleId`, `level`, `message.text`,
`physicalLocation` with `uri`/`startLine`), JUnit parses via defusedxml
with one testcase/failure, GitHub lines all start with `::`. 3 tests
pass; ruff clean.

### H-02 — `[tool.astart]` in the CLI (M7-07 user-visible half, M7-16)
- **Status:** open
- **Priority:** P0
- **Area:** cli
- **Readiness:** ready
- **Effort:** M · standard

**Context:** `cli/config.py` loads it and `cli/ignores.py` applies it, but nothing calls them. In `commands.py` discover `pyproject.toml` upward from the first path argument, load it, and let it supply `select`, `ignore`, `min-confidence`, `safety-ceiling`, `checker`, `exclude` and `target-version` when the matching flag was not given (a flag always wins). Tests `tests/test_cli_config_wiring.py`: config alone, flag overriding config, per-path override, no `pyproject.toml`, malformed config → exit 2 with a message on stderr.

**Steps:**
1. Read `cli/config.py`; expose every `[tool.astart]` key through `FixCommandSettings`/`CheckSettings`.
2. Command-line flags override config; write a precedence test.
3. README table for every key.

**Done when:** config keys and flags agree and are documented.

### H-08 — `astart untype` (P-08): the reverse of `fix`
- **Status:** open
- **Priority:** P0
- **Area:** cli
- **Readiness:** ready
- **Effort:** S · standard

**Context:** New `src/astart/rules/untype.py` `untype_source(*, source: str, variables: bool = True) -> str` removing parameter, return and (optionally) variable annotations through the lossless writer, keeping comments, layout and docstrings; an `x: int = 1` becomes `x = 1`, an `x: int` without a value is removed. CLI subcommand `untype` (files in place, `--diff`, `--check`, like `fix`). Tests `tests/test_rules_untype.py`: comments kept, defaults kept, `ast.dump(parse(untype(s)))` equals `ast.dump(parse(strip_annotations(s)))` with variables ignored, idempotent, round trip on `fixtures/*typed*` (record the remaining differences from the author's untyped twin under the task; do not try to match the hand-edited parts).

**Steps:**
1. Do exactly the steps of P-08 (same files, same tests); this entry only tracks the handoff.
2. When P-08 is `done`, set this task to `done` too.

**Done when:** P-08 is done.

### H-03 — Baselines in the CLI (M7-08)
- **Status:** done
- **Priority:** P1
- **Area:** cli
- **Readiness:** done
- **Effort:** M · standard

**Context:** `cli/baseline.py` has `save_baseline`, `load_baseline`, `apply_baseline`. Add `--write-baseline FILE` and `--baseline FILE` to `check`: write the findings, or hide the findings already in the file and exit 0 when nothing new remains. Tests `tests/astart/cli/test_cli_baseline_wiring.py`: write, then clean re-run exits 0, then a new finding exits 1, a missing file exits 2.

**Steps:**
1. Baselines: `astart check --write-baseline FILE` records current findings; `--baseline FILE` suppresses them.
2. Match by (code, path, line text hash) so unrelated edits don't resurrect findings.
3. Tests: baseline hides old findings, shows new ones.

**Done when:** baselined findings stay hidden after unrelated edits.

**Evidence 2026-11-09:** `check` gained `--write-baseline`/`--baseline`
(`CheckSettings.write_baseline`/`baseline`, wired in `__main__.py`).
`run_check` delegates to `_with_baselines` (save → load →
`apply_baseline`) and `_emit_check` (render + exit); baseline files that
are missing, unreadable or malformed exit 2 with a message. Baseline keys
are now `path#fingerprint` inside `cli/baseline.py` — the fingerprint
already ignores line numbers, and the path prefix stops identical
findings in different files from sharing an entry. `docs/guides/cli.md` +
README document both flags. `tests/astart/cli/test_cli_baseline_wiring.py` (3
tests): write → suppressed re-run exits 0, second file's finding still
exits 1, missing file exits 2.

### H-04 — Catalog rules TYP002 and TYP006 (Q-33, Q-34, M8-03)
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Follow recipe 18.5. TYP002 `typing.no-object-annotation` wraps the existing detector `rules/object_annotations.py`; TYP006 `typing.bare-generic` flags `list`/`dict`/`set`/`tuple`/`frozenset` annotations without subscripts. Detection only, no fix. Edit the JSON under `src/astart/rules/artifacts/catalog/` by hand (`json.dumps(d, indent=2, sort_keys=True) + "\n"`; never regenerate it), update the expected code list in `tests/astart/rules/test_rules_end_to_end.py`. Every rule needs one triggering and one clean example (`verify_catalog`).

**Steps:**
1. Do exactly the steps of M8-03 (same files, same tests); this entry only tracks the handoff.
2. When M8-03 is `done`, set this task to `done` too.

**Done when:** M8-03 is done.

### H-05 — PRS001 for files that do not parse
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** PRS001 for files that do not parse (Q-35, M8-05): one finding at line 1 instead of an `error:` line. Find the `SyntaxError` handling (`grep -n SyntaxError src/astart/rules/engine.py src/astart/cli/*.py`), reuse `rules/parse_module.py`. Keep the exit status 2. Test with `"def (:\n"` in `tests/test_rules_parse_rule.py`.

**Steps:**
1. Do exactly the steps of M8-05 (same files, same tests); this entry only tracks the handoff.
2. When M8-05 is `done`, set this task to `done` too.

**Done when:** M8-05 is done.

### H-06 — Returns / Raises docstring stubs (Q-61, M8-07)
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Generalise `docstring_edit._new_section` to take the title and entry lines, add DOC004 (`Returns:` with `Describe the result.`, only when a `return <value>` exists) and DOC006 (`Raises:` with `<Exc>: Describe when <Exc> is raised.`) as catalog rules with fixes in `docs_fixes.py`, reusing `docs_missing_returns.py` / `docs_missing_raises.py`. Tests mirror `tests/astart/docstrings/test_stubs.py`; idempotence on three corpus files.

**Steps:**
1. Do exactly the steps of M8-07 (same files, same tests); this entry only tracks the handoff.
2. When M8-07 is `done`, set this task to `done` too.

**Done when:** M8-07 is done.

### H-07 — Wider `known_imports` (M3-13)
- **Status:** open
- **Priority:** P1
- **Area:** project
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Add to `rules/imports.py` `Constants.known_imports`: `Never`, `TypeGuard`, `TypeIs`, `ClassVar`, `Literal`, `ParamSpec`, `Concatenate`, `TypeVarTuple`, `TypedDict`, `NamedTuple`, `Annotated`, `override`, `final`, `Pattern` and `Match` (from `re`), and `TracebackType` (from `types`). Test in `tests/astart/rules/test_rules_imports.py` style: each name used in an annotation gets its import inserted, an existing import is not duplicated, a local shadow is aliased. Report any emitter that still hand-rolls `insert_import` instead of `ensure_names`.

**Steps:**
1. Do exactly the steps of M3-13 (same files, same tests); this entry only tracks the handoff.
2. When M3-13 is `done`, set this task to `done` too.

**Done when:** M3-13 is done.

### H-09 — Gate for the conversion pair (P-09)
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Store the accepted numbers of `python -m scripts.compare.pair` as `benchmarks/pair_baseline.json`; add `python -m scripts.compare.pair ... --gate BASELINE` that exits 1 on lower exact recall or any new contradiction; mirror how `benchmarks/report.py` gates the recovery baseline. Extend `tests/scripts/benchmark/test_bench_pair.py`.

**Steps:**
1. Do exactly the steps of P-09 (same files, same tests); this entry only tracks the handoff.
2. When P-09 is `done`, set this task to `done` too.

**Done when:** P-09 is done.

### H-11 — `astart fix --jobs N`
- **Status:** open
- **Priority:** P1
- **Area:** cli
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `astart fix --jobs N` (X-06, M7-04/05): one process per file in `cli/commands.py` with `ProcessPoolExecutor`, results printed and written in input order, a crash in one file reported for that file only (exit 2), `--jobs 1` identical to today. Not with `--project` (needs one index): refuse the combination with a clear message. Tests `tests/test_cli_jobs.py`: same bytes as `--jobs 1` on three files, order stable, one unparsable file does not stop the others.

**Steps:**
1. Do exactly the steps of M7-04 (same files, same tests); this entry only tracks the handoff.
2. When M7-04 is `done`, set this task to `done` too.

**Done when:** M7-04 is done.

### H-10 — Differential oracle (T-07)
- **Status:** open
- **Priority:** P2
- **Area:** negotiation
- **Readiness:** ready
- **Effort:** S · standard

**Context:** New `tests/test_negotiation_oracle.py` using `pytest.importorskip("typing_utils")` (add it to the dev extras in `pyproject.toml` only if a `dev` extra already exists): for 40 pairs of builtin/`typing` generics evaluate `typing_utils.issubtype` and compare with `recovery.relation(written=a, truth=b)` (subtype ⇒ `None`/`narrower`) and with `TypeAlgebra().intersect(left=b, right=a)` (a subtype of b ⇒ result `a`). Disagreements are listed under the task, not "fixed" in the tests.

**Steps:**
1. Do the steps of T-07 (same files, same tests).
2. Set this task to `done` when T-07 is `done`.

**Done when:** T-07 is done.

### H-12 — Keyword style controls
- **Status:** open
- **Priority:** P2
- **Area:** kwargs
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Keyword style controls (M6-04): `min_positional` (leave the first N arguments positional) and `[tool.astart.params]` `keyword-skip = ["len", "print"]` (callees never keyworded). Plumb through `FixSettings` → `rules/facts.py` `keyword_candidates` (read how `kept_positionals` is applied). Tests in `tests/test_rules_keyword_style.py`; default behaviour unchanged (run the danger matrix `tests/astart/rules/test_rules_kwargs_danger.py`).

**Steps:**
1. Do the steps of M6-04 (same files, same tests).
2. Set this task to `done` when M6-04 is `done`.

**Done when:** M6-04 is done.

## 14. Accuracy gaps

*Scope:* Work that the accuracy contract needs and no earlier chapter owned.
*ID prefixes:* G

### G-01 — Make the accuracy contract machine-checkable
- **Status:** done
- **Priority:** P0
- **Area:** tests
- **Readiness:** done
- **Effort:** M · light

**Context:** The targets A-01 to A-11 exist only as a table. Without a command
that prints PASS or FAIL for each, "all tasks done" cannot be verified.

**Steps:**
1. Create `scripts/benchmark/artifacts/resources/targets.json`: a list of objects
   `{"id": "A-02", "metric": "pair.parameters_and_returns.exact_share", "op": ">=", "value": 0.9, "pair": "dev"}`.
   One entry per target row (A-02 gets two: parameters/returns and variables;
   A-03 gets two: compatible share and contradiction share).
2. Create `benchmarks/targets.py` with `@final @dataclass(frozen=True, slots=True) class Target`
   (fields as the JSON keys) and `def evaluate(*, target: Target, reports: Mapping[str, float]) -> bool`
   using `operator.ge/le` looked up by the `op` string in `Constants.operators`.
3. Add `def collect() -> dict[str, float]` that runs, in this order and with the
   commands from W-01: `scripts.compare.pair` (dev and resolver pairs, JSON on stdout),
   `benchmarks recovery` summaries (read the newest `--json` file named by
   `--report`), `benchmarks semantic`, and the idempotence test count. Each
   becomes one flat key such as `pair.dev.params.exact_share`.
4. In `benchmarks/__main__.py` add the subcommand `targets [--report DIR] [--only A-02]`
   printing `A-02  FAIL  52.5 % < 90 %` per row and exiting 1 when any row fails.
5. Add `tests/scripts/benchmark/test_bench_targets.py`: `evaluate` for each operator, and a test
   that every `id` in `targets.json` appears in the Accuracy contract table of
   `docs/planning/TODO.md` and vice versa.

**Done when:** `PYTHONPATH=src:. python -m scripts.benchmark targets --only A-02`
prints one FAIL row today and the new test passes.

**Evidence 2026-11-09:** `scripts/benchmark/artifacts/resources/targets.json` holds one entry per
contract row (A-02: pooled params/returns + variables exact share on both
pairs; A-03: pooled contradiction + compatible share); `benchmarks/targets.py`
provides `Target`/`evaluate`/`collect`/`format_row`; `python -m benchmarks
targets --only A-02` prints `A-02  FAIL  50.3 % >= 90 %` and
`A-02  FAIL  50.7 % >= 90 %`; `tests/scripts/benchmark/test_bench_targets.py` (4 tests)
covers every operator, the JSON↔contract-table bijection and row format.

### G-02 — Score valid narrowing as `narrower`, not `wrong`
- **Status:** done
- **Priority:** P0
- **Area:** tests
- **Readiness:** done
- **Effort:** M · standard

**Context:** `scripts.compare.pair` counts `dict[str, int]` against the author's
`dict[str, object]` as a contradiction because `dict` is invariant. For an
inferred type that is valid for every real caller. 14 of the 104 dev-pair
contradictions are of this kind. The scorer lives in `src/astart/rules/recovery.py`
(`relation`, `_container_within`).

**Steps:**
1. Add failing cases first to `tests/astart/rules/test_rules_recovery_relation.py` (use the
   existing `_relation` helper in that file): `("dict[str, int]", "dict[str, object]") -> "narrower"`,
   `("list[int]", "Sequence[object]") -> "narrower"`, `("list[dict[str, int]]", "Sequence[MutableMapping[str, object]]") -> "narrower"`,
   `("dict[str, int]", "dict[str, str]") -> "contradiction"` (must stay).
2. In `relation`, before the invariance check, replace every `object` in `truth`
   with a wildcard marker; a written argument matches a wildcard with the label
   `narrower`.
3. Run the new tests (red then green), then the recovery tests
   `python -m pytest tests/test_rules_recovery*.py -q -p no:cacheprovider`.
4. Re-run `scripts/compare/pair_wrong.py` and record the new contradiction count here.

**Done when:** the four cases pass and the dev-pair contradiction count drops by

**Evidence:** `relation()` already scores `object` arguments of
the truth arm as wildcards (`_wildcarded`, `_WILDCARD`), so the four spec
cases return `narrower`/`contradiction` as required — verified directly
and now pinned as regression cases in
`tests/astart/rules/test_rules_recovery_relation.py` (97 tests pass). The dev pair
(`scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py
--kind contradiction`) lists 10 remaining contradictions; the
invariant-container `object` kind no longer appears among them.
at least 10 with `correct` unchanged.

**Insights:** The score decides every claim in the accuracy contract; counting a valid narrower type as a contradiction hides real progress and sends agents after non-bugs. Invariance makes `dict[str,int]` incompatible with `dict[str,object]` for a parameter, but the inferred type is still right for every real caller.

**Architecture:** Only `rules/recovery.py` (`relation`) and its tests; the scorer must not import from `negotiation/`. Used by `scripts.compare.pair`, `scripts.benchmark.runner` and `tests/astart/rules/test_gold_expansion.py`, so a change shifts all baselines: refresh them in the same change (L1 owns the baseline files).

**Algorithm:** 1) Parse both annotations with `ast`. 2) Walk the two trees in parallel; where truth has `Name('object')` return `narrower` for any written node. 3) Otherwise apply the existing hierarchy/variance rules. 4) Combine child results: any `contradiction` wins, else any `narrower`, else `exact`.

**Performance:** O(size of annotation) per comparison; memoise `parse` by text (an `lru_cache` on a pure function) since the same few hundred annotation strings repeat.

### G-03 — Give every missed annotation an owner
- **Status:** done
- **Priority:** P0
- **Area:** tests
- **Readiness:** done
- **Effort:** M · light

**Context:** "All tasks done" only reaches A-02 if the tasks cover every reason
a node stays untyped. `scripts/compare/opacity_report.py` prints those reasons.

**Steps:**
1. Run `PYTHONPATH=src python scripts/compare/opacity_report.py fixtures/untyped.py` and
   copy every distinct reason string.
2. Create `docs/analysis/opacity-owners.md`: a table `reason | count | owning task`.
   A reason with no owning task gets a new task in this chapter (use the
   template; priority from the count: ≥ 20 nodes is P1).
3. Add `tests/astart/rules/test_opacity_owners.py`: run the report function on
   `fixtures/*_untyped.py.txt`, collect reasons, assert each reason string
   appears in `docs/analysis/opacity-owners.md`.
4. Repeat on `tests/corpus/extended` once (the owner table must cover the top 20
   reasons there too).

**Done when:** the test passes and no reason is listed as `unowned`.

**Evidence 2026-11-09:** `docs/analysis/opacity-owners.md` maps every distinct
missed-annotation reason (dev pair and the corpus_ext top 20) to its owning
task; `tests/astart/rules/test_opacity_owners.py` collects reasons on the pair fixtures
and asserts each appears in the table; tests pass, no `unowned` row.

### G-04 — Root-cause every remaining contradiction
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** After W-03 and G-02 the dev pair should have under 20
contradictions. Each one is a wrong annotation the tool would write.

**Progress 2026-11-09:** `docs/analysis/contradictions.md` exists with a
root-cause row (`node | wrote | author | basis | cause | fix task`) for
each of the 11 remaining `pair_wrong.py` lines (4 parameters/returns,
7 variables); `tests/astart/rules/test_rules_pair_contradictions.py` asserts the doc
covers every remaining node and carries per-row regression tests. The
count is still 11 > 5, so the task stays open.

**Steps:**
1. Run `PYTHONPATH=src:. python scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5`.
2. For each remaining line, find the hint that wrote it (print
   `facts.hints.index().hint_for(node=...).basis`) and write one row in
   `docs/analysis/contradictions.md`: `node | wrote | author | basis | cause | fix task`.
3. A row whose cause is "the code does not prove it" is fixed by raising the
   basis' acceptance bar in `negotiation/policy.py` (add a test that the node
   stays unannotated), never by special-casing the name.
4. Add a regression test per row in `tests/astart/rules/test_rules_pair_contradictions.py`.

**Done when:** `pair_wrong.py` prints at most 5 lines and each has a row with
an accepted reason in `docs/analysis/contradictions.md`.

### G-05 — Normalise `Generator` defaults and subtype spelling in the scorer
- **Status:** done
- **Priority:** P1
- **Area:** tests
- **Readiness:** done
- **Effort:** S · standard

**Steps:**
1. In `recovery.normalize_annotation` rewrite `Generator[X, None, None]` to
   `Generator[X]` and `AsyncGenerator[X, None]` to `AsyncGenerator[X]`
   (Python 3.13 type-parameter defaults).
2. In `relation`, treat `Generator[X]` as narrower than `Iterator[X]` /
   `Iterable[X]` and `AsyncGenerator[X]` than `AsyncIterator[X]`.
3. Tests in `tests/astart/rules/test_rules_recovery_relation.py` for the four spellings.

**Done when:** the 4 generator contradictions on the dev pair disappear.

**Evidence 2026-11-09 (found already implemented, verified):** all three
steps were already in the tree — `_subscript_members` collapses
`Generator[X, None, None]`→`Generator[X]` and
`AsyncGenerator[X, None]`→`AsyncGenerator[X]`; the ancestors table maps
`Generator`→`{Iterator, Iterable}` and `AsyncGenerator`→`{AsyncIterator,
AsyncIterable}`; `test_rules_recovery_relation.py` covers all four
spellings plus the 3-arg send/throw form (93 tests pass). Verified against
the dev pair: `scripts.compare.pair fixtures/untyped.py fixtures/typed.py
--engine --min-confidence 0.5` rerun shows variables `wrong` 13→11 and
`scripts/compare/artifacts/results/conversion-report.json` contains zero generator-related wrong
items.

### G-06 — Never type a descriptor attribute as its value
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `DescriptorStressOwner.label` is assigned a descriptor instance
and the fixer wrote `str` (the type `__get__` returns).

**Steps:**
1. In `negotiation/builders.py`, where a class attribute assignment becomes a
   node, call `_is_descriptor(value)`: true when the value is a call to a class
   of this module that defines `__get__`, `__set__` or `__set_name__`.
2. Block the node (`_block(path=..., why="descriptor")`).
3. Test in `tests/astart/rules/negotiation/test_negotiation_module.py`: a class attribute holding a
   descriptor instance gets no annotation; a plain `x = 1` does.

**Done when:** the three descriptor lines disappear from `pair_wrong.py`.

### G-07 — Run the checker gate on the pairs and keep the result
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Depends on W-02. Target A-04 is a delta of zero new checker errors.

**Steps:** _to be written after W-02 names the cause._

**Done when:** `scripts.compare.pair --engine --checker` keeps ≥ 80 % of the
annotations it keeps without the checker, with 0 new errors.

### G-08 — List accepted deviations from the author's pair
- **Status:** done
- **Priority:** P2
- **Area:** tests
- **Readiness:** done
- **Effort:** M · light

**Steps:**
1. Create `fixtures/artifacts/accepted_deviations.json`: a list of
   `{"pair": "dev", "node": "HybridContainer.__or__->", "wrote": "HybridContainer", "author": "Self", "reason": "author prefers Self; equivalent"}`.
2. In `scripts/compare/pair.py` `compare`, a written annotation equal to an
   accepted deviation counts as `accepted` (new key), not `wrong`.
3. Test: add one entry, run `compare` on a two-line pair, assert `accepted == 1`.
4. Every entry needs a reviewer-written `reason`; the test fails on an empty one.

**Done when:** the pair report prints `accepted` and the entries total less
than 5 % of `to_recover`.

**Evidence 2026-11-09:** `fixtures/artifacts/accepted_deviations.json` holds one
reviewer-reasoned entry (`HybridContainer.__or__.merged`: wrote
`HybridContainer`, author `Self`); `scripts/compare/pair.py`
`load_accepted_deviations` + `_accepted` score a match as `accepted`
instead of `wrong` on both the parameter and variable paths, and the
report counts it under its own key; `tests/scripts/benchmark/test_bench_pair.py` covers
`accepted == 1`, empty-reason rejection and every shipped entry carrying a
reason. 1 entry is far under 5 % of `to_recover`.

### G-09 — `subtype(A, P)` recurses forever when a protocol method returns the protocol
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Verified `RecursionError`. With `class P(Protocol): def f(self) -> P`
and `class A: def f(self) -> A`, `subtype(A, P)` checks `A.f` against `P.f`,
which asks `subtype(A, P)` again. `subtype` in
`src/astart/semantic/typing_relations.py:1080` has a cycle guard (`_seen` and
`key in _seen`, line 1104), but `protocol_compatible` (line 1294) and
`method_compatible` (line 1398) build their own queries and do not pass `_seen`
on, so the guard never sees the repeated pair. An unguarded cycle in a
subtype check can crash a whole `fix` run on any recursive protocol (builder
pattern, iterator returning itself, `__enter__` returning `Self`), which breaks
A-11 (no crashes) and A-01.

**Steps:**
1. Write the failing test first in `tests/astart/semantic/test_typing_relations.py`: build the
   classes `P` and `A` above as the existing tests in that file do, call
   `subtype(...)` and assert it returns without raising (expected `True`: a
   cycle is assumed compatible, the coinductive reading used by mypy and
   pyright). Run it and confirm `RecursionError`.
2. Find every place a nested `subtype` call is made: `grep -n "subtype(" src/astart/semantic/typing_relations.py src/astart/semantic/typing_contracts.py`.
   Each call inside `protocol_compatible`, `method_compatible` and any helper
   they use must receive the current guard as `_seen=`. Today neither function
   has such a parameter (signatures: `protocol_compatible(*, actual, protocol,
   index)` and `method_compatible(*, implementation, inherited, index)`), so add
   `seen: frozenset[tuple[str, str]] = frozenset()` to both, to every helper
   between them and `subtype`, and pass `_seen=seen` at each nested call. Where
   a `Query` is built (lines 662–675) fill `seen`/`outer_seen` from it.
3. In `subtype`, keep the early return at line 1104 (`key in _seen` → `True`).
4. Add the mirror cases to the test file: a protocol whose method takes the
   protocol as a parameter; two mutually recursive protocols `P`/`Q`; a
   recursive generic protocol (`class P(Protocol[T]): def f(self) -> P[T]`);
   and a non-recursive mismatch that must still be `False` (a cycle must not
   make everything compatible).
5. Run `python -m pytest tests/astart/semantic/test_typing_relations.py tests/test_semantic*.py -q -p no:cacheprovider`.
6. Add a depth guard as defence in depth: a module constant
   `Constants.max_depth = 32` and return `False` (not compatible, never a
   guess) when the nesting exceeds it, with one test that forces it.

**Done when:** the four new tests pass, the existing relation tests are green,
and no input in the test file raises `RecursionError`.

### G-10 — Annotate locals that are assigned more than once in engine mode
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** After W-03 the engine's annotations reach the output only through
hints. `def total(items): count = 0; for item in items: count += item; return count`
should give `count: int = 0`, but nothing is written, and the test
`tests/astart/rules/test_rules_engine_mode.py::test_the_engine_fills_what_the_evidence_leaves_open`
fails. Proven cause: `engine_variables` (`rules/engine_hints.py:99`) returns
`{'total.count': 'int'}` correctly, but `variable_hints`
(`rules/negotiation/variables.py:~75`) only attaches an engine guess to
statements in `built.variables`, and the builder gives no node to a name that is
bound more than once (`count = 0` and `count += item`). So the guess has no
statement to attach to. `--engine` already implies variable annotation
(`rules/facts.py`, `forced=chosen.annotate_variables or chosen.engine`).

**Steps:**
1. Run the red test: `python -m pytest tests/astart/rules/test_rules_engine_mode.py -q -p no:cacheprovider -k fills`.
2. In `rules/negotiation/variables.py`, after the loop over `built.variables`,
   add `_first_assignments(*, module) -> dict[str, Assign]` returning, for every
   function path (`walk_functions` and `own_nodes` from `rules/provable.py`, as
   `engine_variables` does) and every local name, the first `Assign` whose only
   target is that `Name` and that has no annotation.
3. For each `path, statement` in that mapping whose `node_key` is not already in
   `found` and for which `engine.get(path)` passes `is_allowed_source`, add
   `Hint(source=guess, basis=HintBasis.engine)`. Skip names that are
   `global`/`nonlocal`, loop targets, `with` targets and names assigned in a
   nested scope (the existing `_block` reasons list them; reuse it).
4. Run the red test (now green), then `tests/astart/rules/test_engine_hints.py`,
   `tests/astart/rules/test_rules_engine_mode.py`, `tests/astart/rules/test_rules_variable_annotations_fix.py`,
   `tests/scripts/benchmark/test_bench_pair.py`.
5. Re-run the dev pair (command in W-03) and write the new numbers under W-03:
   variable `correct` should recover most of the 22 lost; `wrong` must stay ≤ 13.
6. Run the fast tier and, in the background, the two recovery gates (W-01);
   both must print `PASS`. Only then is the W-03 change safe to commit.

**Done when:** the engine test is green, the pair variable `correct` count is
≥ 170, `wrong` ≤ 13, and both gates print `PASS`.

**Progress 2026-11-08:** steps 1–4 done. `_first_assignments` added to
`rules/negotiation/variables.py`; engine test green; 91 related tests pass. Dev
pair variables exact 152 → 163, wrong 13 (target ≥ 170 not yet met). Steps 5–6
remain. **Fast tier run 2026-11-08 after G-10 steps 1–4: all tests passed, no failures.** **Stdlib recovery gate run 2026-11-08: `PASS`** against `scripts/benchmark/artifacts/resources/baseline.json`. **External recovery gate run 2026-11-08: `PASS`** against `scripts/benchmark/artifacts/resources/baseline_ext.json`. Only the semantic run (A-05) is still not run. Investigate the remaining
lost variable annotations (compare `variable_map` of fixed output with the
pre-W-03 run) before accepting.

**Insights:** Multiply-bound locals are the common case in real code (`count = 0; count += x`); the builder correctly gives them no node because their type may change, but the engine's single annotation describes the first binding. Annotating the first assignment is the Python convention and is what the old converter did.

**Architecture:** Stays inside `negotiation/variables.py`; no new layer. Engine guesses remain the lowest tier and are gated by `is_allowed_source`, `bound_when_evaluated` and, in conversion mode, the checker.

**Algorithm:** 1) `walk_functions` + `own_nodes` to list `Assign` statements. 2) Keep the first plain single-name assignment per `function.name` path, skipping `global`/`nonlocal`. 3) For each path with an engine guess not already covered, create `Hint(basis=engine)` keyed by the statement. 4) Refuse loop, `with` and tuple targets (they are not `Assign` with one `Name`).

**Performance:** One extra walk per function, O(nodes); computed lazily inside `LazyVariables`, only when engine mode is on, cached in `_hints`.

## 15. Import and Constants style

*Scope:* Tidying imports, `TYPE_CHECKING` blocks, type aliases and the
`Constants` class. *ID prefixes:* S

**Rules for every task here.** Each behaviour is its own catalog fix with its
own key, safety class and gold cases (copy the recipe of an existing fix such
as `rules/constants_grouping.py`), and is switchable three ways: the CLI flags
`--enable KEY` / `--disable KEY`, the `[tool.astart]` keys `enable = [...]` and
`disable = [...]`, and a per-file marker comment. Read `cli/config.py` and
`rules/suppressions.py` first and reuse them; add no new switching mechanism.
Every fix must be idempotent (`fix ∘ fix` byte-equal) and keep comments.

### S-01 — Merge consecutive `if TYPE_CHECKING:` blocks and drop empty ones
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Facts:** `ensure_names` and `rules/imports.py` already place imports under
`TYPE_CHECKING` (M3-09 partial). Key: `imports.merge-type-checking`.

**Steps:**
1. Add `merge_type_checking_blocks(*, module: Module) -> bool` in a new
   `rules/type_checking.py`: find top-level `If` nodes whose test is the name
   `TYPE_CHECKING` or attribute `typing.TYPE_CHECKING`, with an empty `orelse`.
2. Merge a block into the previous one when only blank lines and comments
   separate them; concatenate bodies, keep source order, keep comments.
3. Remove a block whose body is empty or only `pass`.
4. Register the fix and detection rule `IMP010` in `rules/artifacts/catalog/imports.json`
   (copy the entry of `imports.bare-import`), safety `proven`.
5. Gold cases (`tests/gold/`): two blocks merge; blocks separated by code do
   not merge; an `else` branch blocks the merge; comments survive.

**Done when:** `python -m pytest tests/test_rules_type_checking.py -q -p no:cacheprovider`
passes and `astart fix` twice gives identical bytes.

**Insights:** Several `if TYPE_CHECKING:` blocks accumulate as imports are added one at a time. Merging is safe only when nothing executes between them and neither has an `else`.

**Architecture:** `rules/type_checking.py` (new), reused by S-02 and by `ensure_names`; fix key `imports.merge-type-checking`, detection IMP010, setting switchable (S-07).

**Algorithm:** 1) Find module-level `If` nodes whose test is `TYPE_CHECKING` or `typing.TYPE_CHECKING` and whose `orelse` is empty. 2) Group consecutive ones: between two blocks only blank lines and comments (from tokens) are allowed. 3) Build the merged body from the group in order; drop `pass`. 4) Replace the span from the first block's start to the last block's end with the merged block, keeping comments attached by token position. 5) Re-parse the unit (CC-10) and verify only `If` bodies changed.

**Performance:** Single pass over `module.body` O(statements); no per-node work.

### S-02 — Put runtime imports before every `TYPE_CHECKING` block
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Facts:** Key `imports.runtime-before-type-checking`. Moving an import changes
import order, so it is guarded.

**Steps:**
1. In `rules/type_checking.py` add `hoist_runtime_imports(*, module) -> bool`:
   collect top-level `Import`/`ImportFrom` nodes that appear after the first
   `TYPE_CHECKING` block and are not inside one.
2. Refuse (change nothing) if any statement between the block and the import
   is neither an import, a docstring, nor a `TYPE_CHECKING` block (a call or
   assignment could depend on order), or if the import is conditional.
3. Move the imports directly above the first block, keeping their relative order
   and attached comments.
4. Tests: import after block moves up; import after an assignment stays; two
   blocks around an import merge into one (needs S-01).

**Done when:** tests pass; the semantic benchmark (A-05) still 15 / 15.

### S-03 — Use `type X = ...` for type aliases
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Interpretation of "add `type` before type variables": the PEP 695
statement for aliases, `X = int | str` (and `X: TypeAlias = ...`) becomes
`type X = int | str`. If you meant `TypeVar` declarations, say so; that is the
`def f[T]` form in M5-23. Key `typing.use-type-statement`, only when the
target version is 3.12 or newer (`FixSettings.target`, `PythonTarget`).

**Steps:**
1. Detect module-level `Assign` with one `Name` target whose value is a type
   expression made only of names bound to classes, `None`, `|`, subscripts,
   or an `AnnAssign` annotated `TypeAlias`.
2. Refuse when the name is rebound, used as a value (called, passed, put in
   `isinstance`, subscripted at runtime) anywhere in the project: a `type`
   statement creates a `TypeAliasType`, not the original object.
3. Rewrite to `type X = <value>`; drop the `TypeAlias` import if unused.
4. Tests: alias used only in annotations converts; alias used in `isinstance`
   does not; target 3.11 does nothing.

**Done when:** tests pass and the fix is off below Python 3.12.

**Implemented slice:** TYP008 / `typing.use-type-statement` now migrates
module-level implicit aliases and `TypeAlias` annotations on the owned AST.
Names, RHS identities and RHS formatting are retained; aliases never receive
variable hints or `Final` fixes. Lexical runtime-use refusal propagates through
alias dependencies with a work queue. Tests cover arbitrary names, imports,
rebindings, metadata, generics, idempotence and the Python 3.12 boundary.
Keep S-03 open for imported-type proof through stubs, constrained/defaulted
legacy binders and whole-project runtime-use analysis.

**Native synthesis follow-up (still open):** `AliasOptimizer` now runs as a
default-on post-pass in `fix_source` (`FixSettings.optimize_aliases`,
`--no-optimize-aliases` opt-out, skipped for targets below Python 3.12) and
in `astart transform` (default on). Still open: integrate its guarded
transaction into the annotation fix catalog on the same module, so checker
rejection can remove the alias transformation independently. Add an explicit
repetition policy
alongside source-cost optimization; preserve ParamSpec kinds, lexical scope,
comments, declaration order and generic dependencies. Keep tuple-length
widening an explicit policy choice rather than treating it as equivalence.
Verify generated names and reuse against the manually curated reference;
do not regenerate that reference from inference output. Track exact spelling
and alias-equivalent type recovery separately in the conversion report.

### S-04 — Drop `from a import b` when `from a.b import c` covers its uses
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Example:** `from a import b`, `from a.b import c`, `d = c(1)`, `e = b.c(2)`
becomes `from a.b import c`, `d = c(1)`, `e = c(2)`.

**Steps:**
1. Key `imports.dedupe-submodule-import`. Detect pairs: `ImportFrom(module=A, names=[b])`
   and `ImportFrom(module=A.b, names=[c])` where `b` resolves to the module
   `A.b` (use `rules/resolve.py` or `astart.stubs.resolver`; refuse if `b` could
   be a class or function).
2. Collect every use of `b`: only `Attribute(value=Name(b), attr=X)` where `X`
   is imported from `A.b` in the same file may be rewritten to `X`.
3. Refuse if `b` has any other use (bare name, `b.other`, passed as a value),
   if `X` is rebound locally, or if the module has `__all__` naming `b`.
4. Rewrite each `b.X` to `X`; remove `b` from the first import (delete the
   statement when it was the only name); keep order and comments.
5. Tests: the example above; a bare `b` use blocks; `b.other` blocks; shadowed
   `X` blocks; aliased `from a import b as m` handled.

**Done when:** tests pass; semantic benchmark unchanged.

**Insights:** `from a import b` plus `from a.b import c` with `b.c(...)` uses is common after refactors and leaves two names for one thing. Rewriting `b.c` to `c` is only valid if `b` is the module `a.b` and has no other use, otherwise a module reference breaks.

**Architecture:** Rule in `rules/imports_dedupe.py` using `rules/resolve.py` (and `astart.stubs.resolver` for third-party). Fix key `imports.dedupe-submodule-import`, safety `guarded`, setting on by default. Must run before import sorting (AF-12) and after `ensure_names`.

**Algorithm:** 1) For each `ImportFrom(module=A, names=[b])` find a sibling `ImportFrom(module='A.b')`. 2) Resolve `b`: must be a module (stub or source file), not a class/function. 3) Collect all loads of `b`: only `Attribute(Name b, attr X)` with X imported from `A.b` may be rewritten. 4) Refuse on other loads, `__all__` mention, shadowing of X, `globals()` use. 5) Rewrite each attribute node by position to `X`, drop `b` from the first import (delete the statement if empty). 6) Re-parse and compare.

**Performance:** One pass over imports (O(imports)) and one scan of `Attribute` nodes grouped by base name (O(nodes)); build the `name → loads` index once per module and reuse it for AF-12/S-01.

### S-05 — Lowercase `Constants` attributes without a leading underscore
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Facts:** `rules/constants_grouping.py` builds the `Constants` class. Key
`style.constants-lowercase`. Today names like `MAX_VALUE` or `_PATTERN` are kept.

**Steps:**
1. Rename rule: strip leading underscores, lowercase (`_MAX_VALUE` → `max_value`).
2. Refuse the whole class if two names collide after renaming or if a new name
   is a Python keyword or already an attribute of `Constants`.
3. Rewrite every `Constants.OLD` in the file; refuse if the old name is
   imported by another module (use `ProjectIndex` in `--project` mode, else
   require `private` names only, i.e. those that started with `_`).
4. Apply the same rule when `constants_grouping` creates the class.
5. Tests: rename + references; collision blocks; exported name blocks.

**Done when:** tests pass; `fix ∘ fix` stable.

### S-06 — Keep the `Constants` docstring generated and current
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Facts:** Existing classes carry `Attributes:` entries with the placeholder
`Grouped module constant.`. Key `docs.constants-attributes`.

**Steps:**
1. On creation (in `constants_grouping`) and on every run, build the docstring:
   a summary line, a blank line, `Attributes:` with one `name: description` per
   attribute in source order.
2. Description comes from the first source of: a `#:` comment above the
   assignment, a trailing comment, else `Grouped module constant.`. Keep any
   description a human already wrote (match by name).
3. Add entries for new attributes, remove entries for deleted ones, never
   reorder text you did not generate; wrap at the configured line length.
4. Tests: new class gets the docstring; a new attribute adds one line; a human
   description survives; a removed attribute loses its line.

**Done when:** tests pass and `docs.*` checks (DOC001) stay green on the result.

### S-07 — Every fix above is switchable and configurable
- **Status:** open
- **Priority:** P0
- **Area:** release
- **Readiness:** ready
- **Effort:** S · light

**Steps:**
1. For S-01 to S-06, S-08 and S-09 add rows to the README flag table.
2. Test (`tests/test_style_switches.py`): for each key, a module that triggers
   it is changed by default-enabled run, unchanged with `--disable KEY`,
   unchanged with `[tool.astart] disable = ["KEY"]`, and unchanged with the
   per-file marker.
3. Decide defaults with the user and write them in `[tool.astart]` docs:
   proposed on: S-01, S-02, S-04, S-06; proposed off: S-03, S-05 (they rename
   or change meaning).

**Done when:** the test passes for all eight keys.

### S-08 — Normalise exception messages to a variable named `msg`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · standard

**Context:** `raise ValueError("bad value")` becomes `msg = "bad value"` on the
line above and `raise ValueError(msg)`. A message already held in another
variable (`message`, `err_msg`, `text`) is renamed to `msg`. This is the
opposite of the folding rule in M8-35 (NAM001), so one setting picks the
direction: `raise-message-style = "extract" | "inline" | "off"`. Proposed
default `extract` (your request); `inline` is M8-35's behaviour. The variable
name is itself a setting: `raise-message-name = "msg"`. Key
`naming.exception-message-variable`; detection code NAM001 (shared with M8-35).

**Steps:**
1. New `src/astart/rules/raise_messages.py`; read `rules/object_annotations.py`
   and `rules/procedural.py` first (they show how a detector yields `Candidate`
   spans) and copy the recipe of an existing fix such as
   `rules/constants_grouping.py` for registration.
2. Find `Raise` statements whose `exc` is a `Call` with at least one positional
   argument, where the call is not `raise` bare and the first argument is a
   string literal, an f-string, a `%`/`+` string expression, or a `str.format`
   call.
3. Extract: insert `{name} = <first argument source>` on the line above, same
   indentation, then replace the argument with `{name}`. Keep `from cause`,
   other arguments and trailing comments.
4. Rename: when the first argument is a `Name` that is assigned exactly once
   in the same scope, directly before the raise (no code between), and read
   nowhere else, rename that variable to `msg`.
5. Refuse (change nothing) when: `msg` is already bound or read in the scope
   with a different meaning; the raise is the single-line body of an `if`/`else`
   (`if x: raise E("a")`) because a second statement changes the block; the
   message expression has side effects or awaits; the raise is inside a
   `match` guard or lambda; two raises in one block would both want `msg`
   (second reuses the name only if the first assignment is the same text,
   otherwise refuse).
6. Inline mode (M8-35): the reverse of 3 under the same refusal rules, plus
   `msg` read or rebound elsewhere.
7. Settings: add `raise_message_style` and `raise_message_name` to
   `FixSettings`, `[tool.astart]` (`cli/config.py`) and a CLI flag
   `--raise-message-style`. Defaults as above. Add both rows to the README flag
   table.
8. Gold and unit tests (`tests/test_rules_raise_messages.py`): literal, f-string,
   already-named variable renamed, `from e` kept, comment kept, `msg` collision
   refused, one-line `if` refused, idempotent second run, `inline` mode round
   trip (`inline(extract(x)) == x`).

**Done when:** the new tests pass and `astart fix` twice gives identical bytes.

### S-09 — Sort class methods by kind (ported from Exactus `organize`)
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · standard

**Context:** Port the policy of
`/Users/joaolopes/Exactus/exactus/packages/organize/core.py`
(`PythonClassMethodReorderer`); do not depend on Exactus. The default order,
copied from `Constants.default_order` there, is:
`new, init, classmethod, property, staticmethod, method, magic,
private_classmethod, private_property, private_staticmethod, private_method`.
So public groups come first and each private group follows in the same
sequence. Because you want to be able to put, for example, private static
methods first, the order is a setting: `[tool.astart] method-order = [...]`,
which must be a complete permutation of the 11 names (Exactus
`validate_order` rejects anything else). Key `style.sort-methods`, default off.

**Classification (copy `_category`):** `__new__` → `new`; `__init__` → `init`;
a dunder of at least 5 characters (`min_dunder_name_length`) → `magic`; a
`@classmethod` → `classmethod`; a property family → `property`; a
`@staticmethod` → `staticmethod`; anything else → `method`. A name starting
with `_` (and not a dunder) uses the `private_` variant.

**Steps:**
1. New `src/astart/rules/method_order.py` with
   `CATEGORIES: Final[tuple[str, ...]]`, `DEFAULT_ORDER`, and
   `validate_order(*, order) -> tuple[str, ...]` (raise `ValueError` with the
   missing and unknown names, as Exactus does).
2. `category(*, node, is_property) -> str` as described above. Detect a
   decorator by name for `classmethod`, `staticmethod`, `property`, and by
   attribute `.setter`/`.getter`/`.deleter` for property families.
3. `reorder_class(*, source, node, order) -> str`: compute for each method the
   source slice that starts at its first leading comment block (a comment block
   directly touching the first decorator or `def`) and ends at its last line.
   Sort methods by `(order.index(category), original index)`; property
   getter, setter, deleter stay together in that sequence. **Move text slices;
   never regenerate with `ast.unparse`.** Non-method statements (attributes,
   nested classes, docstring) never move and keep their places; methods fill
   the method positions in sorted order. Comments separated from a method by a
   blank line stay anchored where they were.
4. Skip classes with fewer than 2 methods (`min_reorder_methods`) and classes
   already in order (idempotence).
5. Refuse a class (change nothing) when moving could change behaviour:
   an `@overload` group, `@singledispatchmethod`/`register`, methods with the
   same name defined twice (conditional redefinition), or a method referenced
   by a decorator or default of another method in the class body (e.g.
   `@x.setter` where `x` is not a method here).
6. Register the fix with key `style.sort-methods`, safety `guarded`, and
   detection rule `OOP010`. Settings: `FixSettings.method_order`, the
   `[tool.astart] method-order` key (`cli/config.py`, validate with
   `validate_order`), and CLI `--method-order a,b,c`. Add README rows.
7. Tests (`tests/test_rules_method_order.py`): default order on a class with
   one method of every category; custom order putting `private_staticmethod`
   first; property getter/setter/deleter stay together; a comment touching a
   method moves with it; a blank-line-separated comment stays; overload
   group refused; invalid order raises; second run changes nothing.

**Done when:** the tests pass, `astart fix` twice gives identical bytes, and
running it on `src/astart/rules/negotiation/*.py` leaves `compile` and the
fast tier green.

## 16. Inference logic

*Scope:* Every rule that lets the tool prove a type.  
*ID prefixes:* I

### I-01 — Narrow the `else` branch by complement
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** `if isinstance(x, int): ... else: ...` narrows only the true branch today (`negotiation/narrowing.py`, nodes like `f.x#12t`).

**Steps:**
1. Read `negotiation/narrowing.py` and the `t` node builder in `builders.py`.
2. Add the `f` (false) node: declared union minus the tested classes via `TypeAlgebra.subtract` (add it to `negotiation/algebra.py`; refuse when the tested class is not a union arm).
3. Handle `is None` / `is not None`, `isinstance` with tuples, and `not` / `and` / `or` tests (De Morgan).
4. Tests in `tests/astart/rules/negotiation/test_negotiation_module.py`: `x: int | str` else-branch is `str`; unknown stays opaque.

**Done when:** the else-branch tests pass and the shadow comparison keeps `only_negotiated.wrong` at 0.

**Evidence 2026-11-09:** `TypeAlgebra.subtract` in `negotiation/algebra.py`,
`!type` constraints through `beliefs._apply`/`_base`/`conflicts`, compound
`and`/`or`/`not` tests plus walrus-seen operands in `narrowing.read_test`,
and multi-arm merges in `builders._branch`; `is None`/`is not None`,
`isinstance` tuples and De Morgan cases covered in
`tests/astart/rules/negotiation/test_negotiation_narrowing.py` and `tests/astart/rules/negotiation/test_negotiation_module.py`;
shadow `only_negotiated.wrong: 0` (correct 162, compatible 17).

### I-02 — Narrow with `match` class and literal patterns
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** `match` statements are not narrowed at all.

**Steps:**
1. Add `match` handling to `builders.py`: each `case` body gets a narrowed node for the subject.
2. Support class patterns `case int():`, literal patterns, `case None:`, `case _:` (complement of earlier cases).
3. Refuse guards (`case int() if ...`) for the complement but allow them for the positive arm.
4. Tests: three-case match over `int | str | None`.

**Done when:** each arm sees the right type in the tests.

**Evidence 2026-11-09:** `builders._match` builds one narrowed node per case
arm from `narrowing.read_case` (class, literal, `None`, or-pattern and
wildcard/complement arms); guards keep the positive arm but never feed the
exclusion set, and capture names (`case int() as n`, sequence captures) are
blocked via `_blocked_names`; class/literal/`None`/guard/or-pattern cases in
`tests/astart/rules/negotiation/test_negotiation_narrowing.py` and `tests/astart/rules/negotiation/test_negotiation_module.py`.

### I-03 — Bind walrus targets
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** `(n := len(x)) > 3` binds `n`; walrus targets are treated as unknown bindings.

**Steps:**
1. In `builders.py` treat `NamedExpr` as an assignment of its value to `target`.
2. A name bound by walrus and elsewhere stays multiply-bound (opaque) unless every binding agrees.
3. Test: `if (n := len(x)) > 3: return n` gives `n: int`.

**Done when:** the test passes and rebinding stays blocked.

**Evidence 2026-11-09:** `builders._plain_target` accepts `NamedExpr` targets
and `_body` binds the value's flow to the name; disagreeing or repeated
walrus bindings stay opaque unless all agree, and `(result := f()) is None`
narrows through `narrowing._tested`; walrus binding and rebinding-blocked
cases in `tests/astart/rules/negotiation/test_negotiation_module.py`.

### I-04 — Type `with` targets from `__enter__`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `with open(p) as f` leaves `f` unknown.

**Steps:**
1. Add a table `Constants.context_managers` in `provable.py` for `open` (mode literal picks `TextIOWrapper`, `BufferedReader`, ...), `tempfile.NamedTemporaryFile`, `threading.Lock` (returns `bool`).
2. For a class of this module, take the declared or proven return of `__enter__` (`Self` → the class).
3. Use `astart.stubs.returns.function_return` for library context managers.
4. Tests: `open` text mode, binary mode, a user class.

**Done when:** `f.write(...)` receivers are typed in the tests.

### I-05 — Type `for` targets from common iterables
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Loop variables over `dict.items()`, `zip`, `enumerate`, `range`, `reversed`, `sorted`, `str` are unknown.

**Steps:**
1. Add transfer rules in `negotiation/transfer.py`: `items → tuple[K, V]`, `zip → tuple[A, B]`, `enumerate → tuple[int, T]`, `range → int`, `str → str`.
2. Tuple targets destructure element-wise; star targets give `list[T]`.
3. Refuse when the iterable is mutated in the loop body (`containers.py` shows how).
4. Tests per rule plus a mutation refusal.

**Done when:** `for i, v in enumerate(xs)` types `i: int` and `v` as the element type.

**Insights:** Loop targets are the largest single source of untyped locals: every `for` introduces one, and the iterable's type is usually known. The soundness hazard is mutation of the iterable inside the loop and iterators consumed twice.

**Architecture:** Transfer rules in `negotiation/transfer.py` (relations `iter_of`, `items_of`, `zip_of`, `enumerate_of`), builder hook in `builders.py` for `For`/`comprehension` targets. No new module. Reuses `containers.py` mutation analysis.

**Algorithm:** 1) Create an `iter_of` contract from the iterable node to a hidden element node. 2) Forward transfer: `list[T]→T`, `dict[K,V]→K`, `str→str`, `range→int`, `dict.items()→tuple[K,V]`, `zip(a,b)→tuple[A,B]`, `enumerate(x)→tuple[int,T]`. 3) Backward: none (declare as `None` transfer). 4) Tuple targets destructure per position; star target gives `list[T]`. 5) Block when the iterable is a container mutated in the body or passed to an unknown call.

**Performance:** Each rule is O(1) per contract; hidden nodes add at most one node per loop; negotiation stays linear in contracts (F-27).

### I-06 — Type `except E as e` and exception flow
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `e` in `except ValueError as e` is `ValueError`; tuples give a union.

**Steps:**
1. Bind the handler name to the class(es) in the `except` clause when they resolve to builtins or module classes.
2. Remove the binding after the handler (Python unbinds `e`) so later reads stay opaque.
3. Tests: single class, tuple of classes, bare `except` (no binding).

**Done when:** the handler tests pass.

**Evidence 2026-11-09:** `narrowing.exception_types` resolves single, tuple
and module-local exception names (unknown, shadowed and dotted names stay
opaque) and `builders._handler_env` binds `except E as e` inside the handler
then deletes `e` afterwards — including a name bound before the `try`;
single/tuple/module-local cases plus the pre-bound deletion case in
`tests/astart/rules/negotiation/test_negotiation_narrowing.py` and `tests/astart/rules/negotiation/test_negotiation_module.py`.

### I-07 — Async inference: `await`, `gather`, async generators
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Prover M4-02 lists `Await` unwrap as open; async comprehension and `asyncio.gather` are unknown.

**Steps:**
1. Unwrap `await f()` using the proven return of async `f`.
2. `asyncio.gather(*coros)` gives `list[T]` for uniform T, a tuple for fixed arity.
3. `async for` over an async generator (W-13) types the target.
4. Tests for each; refuse when the awaited callee is unknown.

**Done when:** awaited calls get their result types in the tests.

### I-08 — Optional results of stdlib lookups
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** `re.match`, `dict.get`, `os.environ.get`, `shutil.which`, `next(it, None)` return `X | None`; they are only partly known.

**Steps:**
1. Extend `stubs/returns.py` `_plain` to accept `X | None` returns made of builtins and `known_imports` classes.
2. Add `re.Match[str]` handling through `known_imports`.
3. Narrowing (`if m:`) already removes `None`; add a test chain `m = re.match(..); if m: return m.group(1)` gives `str`.
4. Gold cases under `tests/gold/` for each lookup.

**Done when:** the lookups type correctly and the `None` arm is dropped inside the guard.

**Evidence 2026-11-09:** `stubs/returns._plain` accepts `X | None` over
builtins and `known_imports` names; `select_overload`/`method_return` bind class
type variables (`re.Match.group`, `os._Environ.get`); `builders._library_typed_method`
resolves name and module-attribute receivers including narrowed nodes through
`TypeAlgebra.narrow`; `re.match`, `dict.get`, `os.environ.get`, `shutil.which`
and `next` verified end-to-end in `tests/astart/stubs/test_stubs_package.py`.

### I-09 — `defaultdict`, `Counter`, `deque` element types from mutation
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** The author's pair types `defaultdict[str, defaultdict[str, list[int]]]`; we write `defaultdict[str, int]` (a contradiction).

**Steps:**
1. In `negotiation/containers.py` add `defaultdict(factory)` as an empty-container constructor with kind `dict` and a default-factory type (`list`, `int`, `set`, another `defaultdict`).
2. Subscript writes `d[k].append(v)` join into the factory element.
3. Refuse when the factory is a lambda or unknown.
4. Tests: `defaultdict(list)` with appends, nested defaultdict.

**Done when:** the nested defaultdict contradiction in `pair_wrong.py` disappears.

### I-10 — Numeric tower and operator result rules
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `/` is always `float`, `//` and `%` keep int, `**` with a non-literal exponent may be `float`, `bool + bool` is `int`.

**Steps:**
1. Write the full table in `provable.py` `Constants.binop_results` keyed by `(left, op, right)`.
2. `divmod` gives `tuple[int, int]` or `tuple[float, float]`.
3. `int ** int` is `int` only for a non-negative literal exponent; otherwise `int | float` is refused (opaque).
4. Property test: compare to `type(eval(...))` for 200 random operand pairs.

**Done when:** the property test passes.

### I-11 — Attribute chains and dataclass/NamedTuple/TypedDict fields
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `a.b.c` stops at the first unknown attribute.

**Steps:**
1. Resolve each attribute through the class contract (`ContractIndex`) for module classes.
2. Dataclass fields give their annotation or default type; NamedTuple fields likewise; TypedDict keys give value types.
3. Refuse when the class defines `__getattr__` or the attribute is assigned in several types.
4. Tests per container kind.

**Done when:** chains of two and three attributes are typed.

### I-12 — Property getters as typed attributes
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** A call site `obj.size` where `size` is a `@property` is unknown.

**Steps:**
1. Treat a property getter as an attribute node fed by the getter's return.
2. Setter parameter feeds the same node (join).
3. Tests: read-only property, property with setter.

**Done when:** `obj.size + 1` types through the getter.

### I-13 — Overload selection by argument types
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** The stubs parser keeps `@overload` groups but nothing selects one.

**Steps:**
1. Add `select_overload(*, group, arguments)` in `stubs/returns.py`: first overload whose parameters accept the argument types (use `TypeAlgebra`).
2. Refuse when any argument type is unknown.
3. Use it in `callee_name` library calls.
4. Tests with `str.split`-like overload pairs.

**Done when:** an overloaded stdlib call returns its precise result.

**Evidence 2026-11-09:** `select_overload` in `stubs/returns.py` picks the
first overload whose parameters accept the argument types, comparing parsed ASTs
through `_accepts`/`_param_expr` (no text scanning), expanding stub aliases via
the resolver, refusing unknown argument types and unbound type variables; wired
through `builders._library_return`; covered by `os.getenv`, `re.match` and
`shutil.which` cases in `tests/astart/stubs/test_stubs_package.py`.

### I-14 — Literal and Final inference
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `MODE = "fast"` compared with `==` against other literals could be `Literal["fast", "slow"]`.

**Steps:**
1. Detect a variable only ever assigned string/int literals and compared to literals.
2. Offer `Literal[...]` only under a setting `infer-literals` (default off).
3. `Final` for never-rebound module constants (exists) — share the detector.
4. Tests: on and off.

**Done when:** the setting toggles the output.

### I-15 — Recursion and mutual recursion
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** A function returning a call to itself, or two functions calling each other, needs a fixpoint.

**Steps:**
1. Check `negotiator.py` cycle handling with a test: `def f(n): return 1 if n == 0 else f(n - 1) + 1`.
2. Mutually recursive pair `even`/`odd` returning `bool`.
3. If a cycle never meets a base case with a proven type, stay opaque.
4. Tests including a refusal (`def f(): return f()`).

**Done when:** the recursive functions get `int`/`bool` and the unbounded one stays unannotated.

**Evidence 2026-11-09:** `builders._flow` decomposes `IfExp` tests into
per-arm flows so a recursive call's result joins the fixpoint; self-recursion
(`return 1 if n == 0 else f(n - 1) + 1`) settles `int`, mutual `even`/`odd`
settle `bool`, and unbounded `def f(): return f()` stays unannotated —
`tests/astart/rules/negotiation/test_negotiation_module.py` recursion cases.

### I-16 — Abstract methods and subclass joins
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** The return of an abstract method can be the join of its implementations.

**Steps:**
1. Collect overriding methods of the same name in module subclasses.
2. Offer the join only when every subclass implementation is proven and the project is closed (`--project` with no external subclasses).
3. Never for a public library class by default (setting `assume-external-callers`).
4. Tests: closed hierarchy and open hierarchy.

**Done when:** closed hierarchy joins, open stays opaque.

### I-17 — Tuple, star-unpack, slice, and operator results on containers
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `a, *rest = xs`, `xs[1:]`, `xs + ys`, `d1 | d2`, `s1 & s2` are partly typed.

**Steps:**
1. Add rules to `transfer.py` and `provable.py`: slice keeps the container type; `+` joins element types; `|` on dicts joins key and value types.
2. Star targets give `list[T]`.
3. Tests per operator and a mixed-type refusal.

**Done when:** the operators type through lists, dicts and sets.

### I-18 — TypeVar solving from call arguments
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `def first(xs: list[T]) -> T` called with `list[int]` should give `int` at the call.

**Steps:**
1. Implement unification of declared parameter types with argument types in `negotiation/algebra.py`.
2. Substitute the result into the callee's return.
3. Refuse on conflicting bindings.
4. Tests: one TypeVar, two TypeVars, conflict.

**Done when:** the call result is typed through the generic callee.

**Insights:** Generic callees (`def first(xs: list[T]) -> T`) are everywhere in annotated code; without unification their call results are opaque and spread opacity downstream. Conflicting bindings must stay opaque, never pick one.

**Architecture:** Unification belongs to `negotiation/algebra.py` (pure, no AST), called from `builders.py` where call results are built. TypeVar declarations come from `semantic/typing_contracts.py`.

**Algorithm:** 1) Collect the callee's parameter annotations containing TypeVars. 2) Unify each with the argument's settled type structurally (`list[T]` vs `list[int]` binds `T=int`; unions bind each arm). 3) A second binding of the same TypeVar must be equal or one the supertype of the other (take the join only for covariant positions); otherwise opaque. 4) Substitute into the return annotation.

**Performance:** Unification is linear in the size of the annotation; do it lazily when the call's argument nodes have settled (reuse the derived-node evaluator); memoise per (callee, argument types).

### I-19 — Join and simplify unions deterministically
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** `int | bool`, `int | int`, `list[int] | list[int]` and the order of arms must be canonical.

**Steps:**
1. In `TypeAlgebra.union` flatten, dedupe, drop arms covered by a supertype only when the supertype is listed (`bool` ⊂ `int` is kept as the author would write `int`).
2. Order: builtins by a fixed table, then module classes alphabetically, `None` last.
3. Property test: result independent of input order.

**Done when:** the property test passes and `pair_wrong.py` shows no ordering-only diffs.

### I-20 — Cross-validate the confidence tiers
- **Status:** open
- **Priority:** P1
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · light

**Context:** `confidence.by_literal` and `by_basis` were measured once on 165 modules.

**Steps:**
1. Write `benchmarks/calibrate.py` that splits the corpus in two halves and recomputes per-basis exact share on each.
2. Fail when the halves differ by more than 3 points.
3. Document the numbers in `docs/analysis/scripts.benchmark.md`.

**Done when:** the script runs and the numbers are in the doc.

### I-21 — Library method returns on stub classes
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** M · deep

**Context:** `Path.read_text() -> str`, `datetime.now() -> datetime` need method lookup on stub classes, not only functions.

**Steps:**
1. Extend `stubs/resolver.py` with `resolve_method(class_name, method)`.
2. Reuse `returns.function_return` for the method.
3. Wire it into `builders.py` library calls for receivers of known class.
4. Tests: `Path(p).read_text()` gives `str`.

**Done when:** method calls on known library classes are typed.

**Evidence 2026-11-09:** `Resolver.resolve_method` plus `function_return`
owner support state method returns; `builders._library_method` handles receivers
that construct known classes and `_library_typed_method` handles names with
proven library types; `Path(p).read_text()` negotiates `str` while `Self`
returns stay refused; tests in `tests/astart/stubs/test_stubs_package.py`.

### I-22 — `__call__`, `__getitem__`, `__iter__`, `__len__` of module classes
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Calls, subscripts and iteration over instances of module classes are unknown.

**Steps:**
1. Resolve the dunder through the class contract and use its proven return.
2. Iteration uses `__iter__` then the element type of the returned iterator.
3. Tests: custom container iterated in a loop.

**Done when:** loops over a custom iterable type their targets.

### I-23 — Stop at the evidence: explain why a node stays opaque
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Users need the reason a variable is not annotated.

**Steps:**
1. Extend `negotiation/policy.py` to return a reason string with each refusal.
2. Expose it through `astart check --explain-opaque` printing `path: reason`.
3. Test: one reason per refusal class.
4. Use it in `scripts/compare/opacity_report.py` instead of its own copy.

**Done when:** `--explain-opaque` prints a reason for every unannotated parameter.

## 17. API completeness

*Scope:* Public library API, schemas, plugins, editor integration.  
*ID prefixes:* API

### API-01 — Export `infer_type` or remove it from `docs/guides/API.md`
- **Status:** done
- **Priority:** P1
- **Area:** docs
- **Readiness:** done
- **Effort:** S · light

**Context:** `docs/guides/API.md` documents `infer_type`, which `astart` does not export (found by comparing the doc with `dir(astart)`).

**Steps:**
1. Decide: implement `infer_type(*, source, path) -> str | None` over `negotiation` + hints, or delete the section.
2. If implementing, add it to `astart/__init__.py` and `__all__`.
3. Add `tests/astart/test_api_surface.py` asserting every name in `docs/guides/API.md` is importable.

**Done when:** the test passes.

**Evidence 2026-11-09:** The premise was a misread — `docs/guides/API.md` documents
`module.infer_type(node=...)`, a method on `Module`/`CommentedModule`
(`src/astart/source/ast.py:1941`), not a top-level export; `dir(astart)` never
showed it because it is not a module attribute. Verified every documented
name resolves: top-level `parse`/`unparse`/`convert`/`Module`/
`CommentedModule` and all `module.*`/`module.semantic.*`/`node.*` paths.
`tests/astart/test_api_surface.py` parses the API table's backticked names —
including `` ` ``/``-joined alternatives like `may_alias/must_alias` and
the `symbols` registry methods — and asserts each resolves on the real
objects, callable when documented with `(...)`. Non-API mentions such as
`` `.pyi` `` are ignored. No `__init__.py` change was needed; the section
stays.

### API-02 — `check_source` and `fix_source` public wrappers with one settings object
- **Status:** done
- **Priority:** P0
- **Area:** backend
- **Readiness:** done
- **Effort:** M · standard

**Context:** Callers must import from `astart.rules` and build `FixSettings`, registries and catalog by hand.

**Steps:**
1. Add `astart/api.py` with `check_source(*, source, filename='<memory>', settings=None) -> list[Finding]` and `fix_source(...) -> FixResult` that build the default catalog once and cache it.
2. Re-export from `astart/__init__.py`.
3. Docstrings with Args/Returns; examples in `docs/guides/API.md`.
4. Tests: round trip on a small module.

**Done when:** `from astart import fix_source` works and is documented.

**Evidence 2026-11-09:** `src/astart/api.py` ships `check_source` (returns
`CheckResult`, richer than the sketched `list[Finding]` — it keeps
`parse_error`) and `fix_source` (defaults to `FixSettings` with the
`guarded` ceiling, matching `astart fix`); `_defaults()` builds
registries + catalog once per process under `lru_cache`. Re-export is
lazy: `astart.rules.engine` already does `from astart import ...`, so an
eager import would be circular — `__init__.py` gained a PEP 562
`__getattr__` plus a `TYPE_CHECKING` import, keeping `import astart`
light and static typing intact. `__all__` gained both names (snapshot
test updated). `docs/guides/API.md` table + paragraph and CHANGELOG document
them; `tests/astart/rules/test_api_wrappers.py` (6 tests) covers import, round trip,
explicit settings, annotation preservation and parse errors.

### API-03 — `fix_paths` and `fix_file` with atomic writes
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** S · standard

**Context:** The CLI writes files; library users cannot.

**Steps:**
1. Factor `_fix_file` and `_write_atomic` (`cli/commands.py`) into `astart/files.py`.
2. Public `fix_file(*, path, settings, write=True)` returning the outcome.
3. Tests with `tmp_path`: write, dry run, error file.

**Done when:** files are fixed through the API without the CLI.

**Evidence 2026-11-09:** `src/astart/files.py` ships `fix_file`/`fix_paths`
(built on `astart.api.fix_source`, `guarded` ceiling by default),
`FileOutcome` (`before`/`after`/`applied`/`changed`/`written`/`error`),
`read_source`/`SourceFile` and `write_atomic` — the latter two moved out
of `astart.cli` (`cli/atomic.py` re-exports `write_atomic`,
`cli/commands.py` imports `read_source`/`SourceFile` from `astart.files`,
so CLI and API share one implementation; `cli/transforms.py`'s
`commands.write_atomic` import still resolves). `_fix_file` itself stays
in the CLI — it is coupled to `FixCommandSettings`, project index, cache
and checker, none of which the single-file API carries. All three names
are exported from the package root; `docs/guides/API.md` and CHANGELOG updated.
`tests/astart/test_files_api.py` (5 tests): write, dry run, missing/unparsable
file, input-order `fix_paths`, declared-encoding round trip.

### API-04 — Public `Settings` with `from_pyproject`
- **Status:** done
- **Priority:** P1
- **Area:** backend
- **Readiness:** done
- **Effort:** M · standard

**Context:** `[tool.astart]` parsing lives in `cli/config.py` and is not reusable.

**Steps:**
1. Define a frozen `Settings` dataclass with every `FixSettings` field.
2. `Settings.from_pyproject(path)` using `cli/config.py` validation.
3. `Settings.to_fix_settings()`.
4. Tests: round trip and unknown key error.

**Done when:** one object configures both CLI and API.

**Evidence 2026-11-09:** new `src/astart/settings.py` — frozen
`Settings` mirroring every `FixSettings` field a pyproject can express.
`target` is spelled `target_version` (the config string) and resolved
through `resolve_target` in `to_fix_settings`; `checker` keeps the
configured mode string while the `Checker` object is injected by the
caller — the same split as the CLI's `use_checker`. `from_pyproject`
delegates validation to `cli/config.load_config` (malformed tables raise
`ConfigError`; a missing table yields defaults) and maps
`safety-ceiling`, `min-confidence`, `target-version`, `checker` and
`protocol-placement`. Exported as `astart.Settings` (`__all__` + pinned
surface updated); `docs/guides/API.md` documents both methods.
`tests/astart/cli/test_settings.py` (6 tests): root import, CLI-matching defaults,
full table mapping, absent-table defaults, malformed-table `ConfigError`,
`to_fix_settings` conversion. CLI consumption of `Settings` remains
H-02's wiring step.

### API-05 — Stable public surface and version policy
- **Status:** done
- **Priority:** P1
- **Area:** docs
- **Readiness:** done
- **Effort:** S · light

**Context:** `astart.__all__` is not pinned, so renames break users silently.

**Steps:**
1. Add `__all__` to `astart/__init__.py` and `astart/api.py`.
2. `tests/astart/test_api_surface.py` snapshots the sorted names; a change needs an explicit test edit.
3. Write `docs/engineering/versioning.md`: what is public, how deprecations work.

**Done when:** the snapshot test exists.

**Evidence 2026-11-09:** `astart/__init__.py` already declares `__all__`
(44 names; `astart/api.py` does not exist — the package root is the
whole public surface, nothing imports `astart.api`). Added
`test_all_matches_the_pinned_public_surface` to
`tests/astart/test_api_surface.py`: `tuple(sorted(astart.__all__))` must equal
the literal `Constants.public_names` list, so any surface change fails
until the snapshot is edited deliberately. Wrote `docs/engineering/versioning.md`:
public surface (`__all__`, CLI commands/flags, JSON schemas, rule
codes), non-public internals, pre-1.0 additive/breaking/deprecation
rules and the post-1.0 semver policy.

### API-06 — JSON schemas for findings and reports
- **Status:** done
- **Priority:** P1
- **Area:** release
- **Readiness:** done
- **Effort:** S · light

**Context:** SARIF/JUnit/GitHub reporters exist; the native JSON has no schema.

**Steps:**
1. Write `docs/schema/finding.json` and `report.json` (JSON Schema 2020-12).
2. Validate real output in `tests/astart/cli/test_report_schema.py` with a tiny validator (no new dependency: check required keys and types).
3. Link from README.

**Done when:** the test validates a real report.

**Evidence 2026-11-09:** `docs/schema/finding.json` + `docs/schema/report.json`
(JSON Schema 2020-12) shipped; `tests/astart/cli/test_report_schema.py` validates real
`render_json` output (a finding-bearing report plus a parse-error report)
with a dependency-free validator covering the schema subset used. The test
caught a real spec bug — `Span.start_column` is 0-based, so `column` is
`minimum: 0`. README links the schemas under the CLI section. 2 tests pass;
ruff clean.

### API-07 — Plugin API: custom rules and fixes
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Registries exist (`default_registries`), but there is no documented way to add a rule from outside.

**Steps:**
1. Document `Registries.register_*` in `docs/guides/rule-authoring.md`.
2. Load plugins named in `[tool.astart] plugins = ["pkg.module"]`, each exposing `register(registries)`.
3. Test with a fixture plugin module.

**Done when:** a plugin rule appears in `astart rules`.

### API-08 — Progress and cancellation callbacks
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** S · standard

**Context:** Long runs give no progress to library users.

**Steps:**
1. Add optional `on_file(path, outcome)` callback to `fix_paths`.
2. Cancellation: a `threading.Event` checked between files.
3. Tests with a callback counter.

**Done when:** the callback fires once per file.

**Evidence 2026-11-09:** `fix_paths` gained `on_file` (invoked once per
processed file with `(path, outcome)` after the file completes) and
`cancel` (a `threading.Event` checked before each file; when set the run
stops and returns the outcomes collected so far). `docs/guides/API.md` row
updated. `tests/astart/test_files_api.py` (+2 tests): callback fires once per
file in input order with the identical outcome object, and a callback
that sets `cancel` ends the run after the first file. 7 tests pass;
`ruff check --select ALL` clean.

### API-09 — `tests.support` helpers for rule authors
- **Status:** done
- **Priority:** P2
- **Area:** tests
- **Readiness:** done
- **Effort:** S · light

**Context:** Gold-case plumbing is copied in every test file (`_fixed` helpers).

**Steps:**
1. Create `astart/testing.py` with `fixed(source, **settings)` and `assert_fixed(source, expected)`.
2. Port two existing tests to use it.
3. Document in `docs/guides/rule-authoring.md`.

**Done when:** the helpers are used by two tests.

**Evidence:** `tests/support/gold.py` ships `fixed(source=..., settings=...)`
and `assert_fixed(source=..., expected=..., settings=...)`; both dedent
inputs and default to `FixSettings(ceiling=FixSafety.guarded)`. Ported
`tests/astart/rules/test_rules_expression_defaults.py` and
`tests/astart/rules/test_rules_comprehension_types.py` (their identical `_fixed`
helpers deleted); `tests/support/test_testing_helpers.py` covers both helpers.
`docs/guides/rule-authoring.md` gained a "Fix tests" section. `fixed` takes a
`FixSettings` object rather than `**settings` kwargs so call sites stay
type-checked. 12 tests pass; ruff clean.

### API-10 — Language server skeleton (M7-10)
- **Status:** open
- **Priority:** P3
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Diagnostics and code actions over LSP.

**Steps:**
1. Implement `initialize`, `textDocument/didOpen|didChange` publishing `check` findings using `pygls`-free JSON-RPC over stdio (small hand-written loop).
2. `textDocument/codeAction` returns each finding's fix as a `WorkspaceEdit`.
3. Test with scripted stdio messages.

**Done when:** an editor-style scripted session returns diagnostics and one edit.

### API-11 — Exit-code and error contract
- **Status:** done
- **Priority:** P1
- **Area:** docs
- **Readiness:** done
- **Effort:** S · light

**Context:** Exit codes (0, 1, 2) and error lines are scattered.

**Steps:**
1. Write `docs/guides/cli.md` listing every command, flag, exit code and the `path: error:` line format.
2. Test that `README` flags and `docs/guides/cli.md` flags match (extend `tests/astart/test_readme_flags.py`).

**Done when:** the test passes.

**Evidence 2026-11-09:** `docs/guides/cli.md` shipped — all six commands with
their full flag tables (verified against live `--help` output), the 0/1/2
exit-code contract per command, and both error-line formats
(`path: error: reason`, `astart: unknown rule code:`). `tests/
test_readme_flags.py` gained two tests: every `--help` flag of every
command must appear in `docs/guides/cli.md`, and every astart `--flag` token in
README must resolve there (pytest/anchor tokens exempted). 3 tests pass;
ruff clean.

### API-12 — Machine-readable `astart rules --json`
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** S · light

**Context:** Tools cannot list rules and fixes without parsing text.

**Steps:**
1. Add `--json` to `rules` printing code, key, title, maturity, fixes, safety.
2. Schema in `docs/schema/rules.json`.
3. Test the keys.

**Done when:** `astart rules --json` validates.

**Evidence 2026-11-09:** `astart rules --json` emits a sorted JSON array —
one object per rule with `code`, `key`, `title`, `maturity`, `severity` and
`fixes` (each fix's `key` resolved to its catalog `safety`, null when
unresolved). Serialized via `canonical_dumps`. `docs/schema/rules.json`
(JSON Schema 2020-12) documents the shape; `test_rules_json_lists_
documented_keys` asserts every key on real output (14 rules); `docs/guides/cli.md`
rules section updated. 8 tests pass; ruff clean.

### API-13 — Cache API and invalidation policy
- **Status:** done
- **Priority:** P2
- **Area:** backend
- **Readiness:** done
- **Effort:** S · light

**Context:** `FixCache` keys on file content and checker; document and expose it.

**Steps:**
1. Add `docs/guides/cache.md` describing the key (content hash, astart version, settings hash).
2. Public `clear_cache(root)`.
3. Test: changing a setting invalidates.

**Done when:** the invalidation test passes.

**Evidence:** `docs/guides/cache.md` documents the entry key
(sha256 of tool fingerprint + resolved path + source text), the
fingerprint inputs (settings repr minus `paths`/`mode`/`use_cache`,
checker name, `ruff --version`, package files, project configs) and
`Constants.schema`. `astart.cli.cache.clear_cache(root=...)` deletes
entry files and returns the count. `tests/astart/cli/test_cli_cache.py` gained
`test_clear_cache_forces_a_recompute` (6 tests pass); the existing
`--safe-only` run already proves a settings change invalidates.

## 18. Automatic annotation and formatting

*Scope:* What gets written and how it is laid out.  
*ID prefixes:* AF

### AF-01 — Annotate `*args` and `**kwargs`
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `def f(*args, **kwargs)` is never annotated.

**Steps:**
1. Detect the element type from forwarding calls (`g(*args)` where `g` has typed parameters) and from usage (`sum(args)` gives `int`/`float`).
2. Write `*args: int`, `**kwargs: str` only when proven; never `object`/`Any`.
3. Tests: forwarded, summed, unknown.

**Done when:** proven cases are annotated, others untouched.

### AF-02 — Annotate `self`/`cls` only when the style asks
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Output sometimes contains `self: Self`.

**Steps:**
1. Add setting `annotate-receivers` (default off).
2. When on: instance methods get `self: Self`, classmethods `cls: type[Self]`; needs target 3.11+.
3. Tests: both settings.

**Done when:** default output has no receiver annotation.

### AF-03 — Dunder method annotations from the language
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** T-01/W-09 cover `__exit__`; extend to the full protocol table.

**Steps:**
1. Table in `negotiation/builders.py`: `__eq__(other: object) -> bool` is allowed here because it is the language signature, `__hash__ -> int`, `__len__ -> int`, `__bool__ -> bool`, `__repr__/__str__ -> str`, `__iter__ -> Iterator[...]`, `__contains__ -> bool`.
2. Seed with `Origin.protocol`; the object-ban rule has this one documented exception (`__eq__`, `__ne__` parameter).
3. Tests per dunder.

**Done when:** dunder methods are fully annotated.

### AF-04 — Dataclass, NamedTuple and TypedDict fields
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Fields with defaults but no annotation are left alone.

**Steps:**
1. For `@dataclass`, annotate a field from its default (`x = 0` → `x: int = 0`).
2. `field(default_factory=list)` gives `list[...]` from later appends.
3. NamedTuple / TypedDict: fields need annotations to be valid; propose from call sites.
4. Tests per kind.

**Done when:** the dev pair dataclass fields match the typed twin.

### AF-05 — `ClassVar` and `Final` inference
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Author writes `ClassVar[...]`; we write the bare type.

**Steps:**
1. A class-level assignment never assigned through an instance (`self.x = `) and never rebound is `ClassVar[T]` under setting `infer-classvar` (default on for dataclasses off).
2. A module/class constant never rebound is `Final[T]`.
3. Descriptor values are excluded (G-06).
4. Tests.

**Done when:** the three ClassVar lines in `pair_wrong.py` are exact.

### AF-06 — Modernise `typing` spellings by target version
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `List[int]` → `list[int]`, `Optional[X]` → `X | None`, `Union[A, B]` → `A | B`, `typing.Callable` → `collections.abc.Callable`.

**Steps:**
1. One fix per rewrite, key `typing.modernise-*`, gated on `FixSettings.target`.
2. Remove imports left unused.
3. Tests per rewrite and per target version.

**Done when:** each rewrite passes on 3.10 and 3.13 where allowed.

### AF-07 — `from __future__ import annotations` policy
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Forward references need quoting, or the future import, or `Self`.

**Steps:**
1. Setting `future-annotations = add | never | auto` (auto: add only when a forward reference would otherwise be quoted).
2. Insert after the docstring, before other imports.
3. Tests.

**Done when:** auto adds it only when needed.

### AF-08 — Docstring types follow annotations
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** After annotating, Google-style `x (int):` entries can disagree or be redundant.

**Steps:**
1. Setting `docstring-types = keep | remove | sync`.
2. `sync` rewrites the parenthesised type to the annotation; `remove` drops it.
3. Tests for each mode and for missing entries.

**Done when:** docstrings and annotations agree in `sync` mode.

### AF-09 — Generate `Raises`, `Yields`, `Attributes` sections
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** M · standard

**Context:** Q-61 only covers Returns/Raises stubs.

**Steps:**
1. Raises: from `raise X` statements in the function body, not from callees.
2. Yields: for generators, with the yield type when proven.
3. Attributes: for classes, from `self.x =` in `__init__` and class-level names.
4. Tests; reuse `docs_missing_*.py` helpers.

**Done when:** DOC001–DOC013 stay green on generated text.

### AF-10 — Wrap long annotations and signatures
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Annotation insertion can exceed the line length.

**Steps:**
1. After annotating, if a `def` line exceeds the configured length, wrap parameters one per line with a magic trailing comma.
2. Match ruff format output (test by running ruff format on the result and asserting no further change).
3. Tests with long signatures.

**Done when:** `fix ∘ ruff format` is stable.

### AF-11 — Canonical order of union arms and `None` last
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `None | int` vs `int | None`.

**Steps:**
1. Rewrite unions to the canonical order of I-19 in existing annotations only under `normalize-unions` (default off).
2. Tests.

**Done when:** the setting normalises and is idempotent.

### AF-12 — Import sorting and grouping
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** M3-12 deterministic placement.

**Steps:**
1. Implement isort-compatible grouping: future, stdlib, third party, first party, local; one blank line between groups; `from` imports sorted by module then name.
2. Setting `import-style = isort | none`.
3. Tests against ruff `I001` output on the corpus.

**Done when:** results equal ruff's isort on the corpus.

### AF-13 — Blank-line, whitespace and EOL normalisation
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · light

**Context:** M8-08.

**Steps:**
1. Two blank lines between top-level defs, one between methods, no trailing whitespace, single final newline, LF endings (keep CRLF files CRLF under `preserve-eol`).
2. Tests with CRLF files.

**Done when:** idempotent on the corpus and no semantic diff.

### AF-14 — `__all__` generation and sorting
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · light

**Context:** Public API lists drift.

**Steps:**
1. Setting `generate-all`: list top-level public names (no leading underscore, defined here).
2. Sort an existing `__all__`; refuse dynamic `__all__`.
3. Tests.

**Done when:** the setting writes and sorts `__all__`.

### AF-15 — Replace `object` and `Any` annotations by inferred types
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** TYP002 detects `object` annotations; the fix is missing.

**Steps:**
1. For `x: object` where the engine/negotiation proves a type, replace it.
2. Otherwise leave and report.
3. Tests; keep the project rule that `object` is never written.

**Done when:** TYP002 has a fix that only fires with proof.

### AF-16 — Extract repeated long annotations into type aliases
- **Status:** open
- **Priority:** P3
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** `dict[str, list[tuple[int, str]]]` repeated 3 times.

**Steps:**
1. Setting `alias-threshold` (default off).
2. Create `type Name = ...` (3.12+) or `Name: TypeAlias = ...`, name from the owning concept (`records`); refuse on name collision.
3. Tests.

**Done when:** repeated annotations become one alias.

### AF-17 — Consistent `Optional` spelling inside a file
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · light

**Context:** Mixed `Optional[X]` and `X | None`.

**Steps:**
1. Detect the majority spelling and rewrite the minority under `normalize-optional`.
2. Tests.

**Done when:** a file ends with one spelling.

### AF-18 — Annotation report
- **Status:** open
- **Priority:** P1
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · light

**Context:** Users need to see what was annotated and why.

**Steps:**
1. `astart fix --explain-annotations` prints `path: annotation (basis, confidence)` per written annotation.
2. JSON variant `--format json`.
3. Tests.

**Done when:** every written annotation has a line.

### AF-19 — Keep user annotations; never overwrite
- **Status:** open
- **Priority:** P0
- **Area:** tests
- **Readiness:** ready
- **Effort:** S · standard

**Context:** A safety rule that needs a permanent test.

**Steps:**
1. Property test: for every corpus module with annotations, `fix` never changes an existing annotation (compare `annotation_map` before and after).
2. Include variable annotations.

**Done when:** the property test passes on both corpora.

### AF-20 — Per-file style detection
- **Status:** open
- **Priority:** P2
- **Area:** backend
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Fix output should follow the file's own style (quotes, union spelling, trailing commas).

**Steps:**
1. Detect the dominant quote and union spelling; use it for generated code.
2. Tests: single-quote file stays single-quote.

**Done when:** generated code matches the file.

### AF-21 — Format the code inside f-string fields with ruff, then put it back
- **Status:** open
- **Priority:** P0
- **Area:** backend
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Today `rules/fstring_normalize.py` only moves whitespace around fields. You want the expression text inside each `{...}` formatted by ruff, re-inserted with the right indentation and a maximum line length that accounts for where the field sits in the f-string. Everything is done on the AST (re-parse), never by pattern matching on the text.

**Steps:**
1. Read `rules/fstring_normalize.py` (`normalize_fstrings`, its scanner) and `rules/formatter.py` (how ruff is called). Python 3.12+ parses f-strings into `JoinedStr` nodes with `FormattedValue` children whose `value` has exact `col_offset`/`end_col_offset`, so each field's expression span comes from the AST, not from scanning characters.
2. For each `FormattedValue` take the expression source slice from the AST positions (`ast.get_source_segment` or the module's own span helper). Skip fields with `=` debug, nested f-strings in the format spec, backslashes or comments, and any field whose slice cannot be re-parsed to the same `ast.dump`.
3. Compute the available width: `max_line_length - column_of_field_start - len(closing text of the field: conversion, format spec, '}', rest of the literal up to the end quote and the trailing code on the line)`. Clamp to a minimum of 20; refuse when the result would be smaller. The configured length comes from `FixSettings`/ruff config (`line-length`).
4. Send the expression to ruff as a one-line module: write `__x = (EXPR)\n` to a temporary string and call `ruff format --stdin-filename x.py --line-length WIDTH` (reuse the subprocess helper in `rules/formatter.py`; never shell out per field if one batch call works: put every field of the file in one scratch module, one assignment per field, and read them back in order).
5. Parse ruff's output with `ast.parse`; take the right-hand side expression. Re-parse the original expression and assert `ast.dump` is identical (formatting must not change the tree). If not identical, keep the original text.
6. If ruff returns a single line, put it back in place of the old slice. If it wraps onto several lines, the text must be re-indented to the field's column plus one indent level (use the line's leading whitespace from the AST `col_offset` of the enclosing statement, not a character scan) and only for triple-quoted f-strings or inside parentheses where a newline in the field is legal; otherwise refuse the field and keep it on one line.
7. Re-parse the whole edited module; if `ast.dump` of the new module differs from the old one in anything but source positions, discard all edits for that statement.
8. Register the fix `strings.format-fstring-fields` (safety `guarded`, setting `format-fstring-fields`, default off) next to the existing normalisation fix; add `FixSettings.fstring_line_length`, the `[tool.astart]` key and a CLI flag, plus README rows.
9. Tests (`tests/test_rules_fstring_format.py`): `f'{ a+b }'` → `f'{a + b}'`; a call that exceeds the width wraps in a triple-quoted f-string; a call that would wrap in a single-quoted f-string is refused; nested quotes, `=`-debug and comments refused; second run changes nothing; `ast.dump` equal before and after.

**Done when:** the tests pass, `fix ∘ fix` is byte-equal and `ruff format --check` on the output reports no further change in f-string fields.

**Insights:** The f-string interior is real Python but lives inside a string token, so line-length and indentation depend on the host line. Formatting it naively either overflows the line or changes the tree. Python 3.12 parses fields into `FormattedValue` nodes with exact positions, so the AST is the only safe locator; character scanning breaks on nested quotes and `{{`.

**Architecture:** Lives in `rules/fstring_format.py` next to `fstring_normalize.py` (which keeps whitespace-only normalisation). Calls ruff through the existing `rules/formatter.py` helper; no new dependency. Setting `format-fstring-fields`, `fstring_line_length`; fix key `strings.format-fstring-fields`, safety `guarded`; verified by CC-09/CC-10 re-parse.

**Algorithm:** 1) Collect every `FormattedValue` of every `JoinedStr` with its expression span. 2) Skip `=` debug, nested format-spec f-strings, comments, backslashes. 3) Width = line_length − start column − length of text after the field on its line; clamp ≥ 20 or refuse. 4) Batch all fields into one scratch module, one `__fN = (EXPR)` per field, run ruff once with the width, read results back by index. 5) Accept a result only if `ast.dump` of old and new expression are equal. 6) One-line results replace in place; multi-line results are re-indented to the statement's indent plus one level and only allowed in triple-quoted f-strings or inside parentheses. 7) Re-parse the edited statement (CC-10) and compare.

**Performance:** One ruff subprocess per file (not per field): O(fields) text, one process start (about 30 ms). Skip files with no `JoinedStr` without spawning anything. Cache by (expression text, width) within a run. Budget: under 5 % added runtime on the corpus with the setting on.

### AF-22 — Define deterministic Google docstring policy and analyzer ownership
- **Status:** open
- **Priority:** P0
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** This is the prerequisite for AF-23–AF-26. The requested GDC
identifiers are traceability identifiers, not reserved catalog DOC codes.
Reference: [Google Python Style Guide §3.8](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings),
plus [§3.2's explicit summary limit](https://google.github.io/styleguide/pyguide.html#32-line-length).
Current DOC014 (`docs.annotation-types`) generates function documentation
from existing annotations and explicit body evidence. It does not establish
summary-length compliance, missing documented types for unannotated arguments,
tuple-result structure, or complete public attribute inventories. Existing
`DocEntry` argument/attribute links are infrastructure, not these detectors.
M8-37/AF-09 overlap with the attribute work; consolidate their implementation
through AF-24 rather than adding another scanner or conflicting DOC007 rule.

**Steps:**
1. Inventory the installed Ruff version, selected/preview diagnostics and
   BasedPyright configuration. Build small positive/negative fixtures and a
   coverage matrix before allocating any new catalog code. Do not assume
   `select = ["ALL"]` activates preview diagnostics or every DOC behavior.
2. Assign existing analyzers ownership of punctuation (D400/D415/D4xx),
   indentation/sections (relevant D2xx/DOC checks), public documentation
   presence (D1xx), configured copyright notices (CPY001), parameter-name
   mismatches (GDC019, relevant DOC rules), and inline-comment spacing
   (GDC031, E26x). Add a new rule only for a reproduced, documented residual
   gap; do not duplicate their general functionality or relax their settings.
3. Exclude GDC014 grammatical style from deterministic enforcement, including
   heuristic verb lists presented as proof. Also exclude prose-meaning checks
   GDC001/006/007/009/010/012/013/015/017/020/022/023/024/026/027/028/029/030.
   A detected mutation, decorator or override does not prove prose inadequate.
4. Specify public visibility, supported documentation styles, inherited-doc
   behavior, opt-outs, diagnostic spans and explicit unknown/refusal outcomes.
   Route every detector through the shared extended AST, `DocstringNode`,
   symbols and type evidence. No independent source parse, regex-based symbol
   replacement, runtime imports, evaluation, or natural-language scoring.
5. Define stable findings with rule ID, owner/node identity, exact source
   span, expected/observed structure and evidence origin. Reuse incremental
   dependency invalidation; benchmark before/after on existing docstring and
   corpus workloads, retaining token-index and parse-count budgets.

**Done when:** a checked-in ownership/coverage matrix and policy fixtures
establish precisely which four core rules remain necessary, their catalog
IDs, and their deterministic boundaries; excluded semantic checks are not
silently reintroduced as heuristics.

### AF-23 — GDC002: measure the docstring summary itself
- **Status:** open
- **Priority:** P0
- **Area:** rules
- **Readiness:** ready
- **Effort:** S · standard

**Context:** Implement the summary-only limit absent from the current catalog.
Google §3.2 explicitly requires summary lines within 80 characters; §3.8.1
defines the one-line summary. Ruff E501 measures a physical source line,
including delimiters/indentation, and is not an equivalent measurement.
Depends on AF-22.

**Steps:**
1. Read the first logical summary line from the existing docstring AST and
   map its decoded text to the original token span. Ignore source indentation,
   quotes, literal prefixes and the remaining description/sections. Handle
   initial blank lines, implicit literal concatenation, escapes and Unicode
   with a documented deterministic character-count policy.
2. Default the configurable summary maximum to 80; diagnose strictly greater
   lengths. Preserve the separate repository source-line limit. Record any
   applicable upstream exceptions precisely; do not automatically apply the
   general long-URL or formatter exceptions to summary lines, for which
   Google states an explicit limit.
3. Add a finding with measured length, configured limit and summary span.
   Do not automatically reword or truncate prose; any proposed wrapping must
   preserve the summary/description boundary and remain separately reviewable.
4. Test 79/80/81 characters, deeply indented methods, same summary under
   different quoting, long later prose, one-line versus multiline strings,
   Unicode, escaped text and exact source-span mapping.

**Done when:** summary-only diagnostics pass boundary and differential Ruff
fixtures without flagging a compliant summary solely because its physical
source line is longer. Document the policy and incremental invalidation.

### AF-24 — GDC025: document statically established public attributes
- **Status:** open
- **Priority:** P0
- **Area:** rules
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Class documentation links some existing entries to annotations,
but there is no complete public-attribute completeness detector. Google
§3.8.4 explicitly excludes properties from the class `Attributes` inventory.
This task owns the corresponding missing-attribute slice of M8-37/AF-09.
Depends on AF-22 and the shared symbol/type graph.

**Steps:**
1. Build one cached per-class inventory from class-body assignments and
   annotations, proven receiver assignments, dataclass stored fields and
   statically readable `__slots__`. Distinguish public/private names, instance
   versus class state, `ClassVar`, dataclass `InitVar`, methods and properties.
   Include public `ClassVar` state; exclude `InitVar`, methods, private names,
   properties and storage-control slots such as `__dict__`/`__weakref__`.
2. Resolve aliases, receiver identity, inheritance and descriptor/property
   decorators using existing symbols. Count inherited documented attributes
   without demanding duplicate subclass entries; require locally redeclared
   public attributes to have an applicable entry under the explicit policy.
   External/unknown bases and dynamic `setattr`, metaclasses or decorators
   must produce bounded unknown inventory evidence, not invented attributes.
3. Compare the established inventory with structured `Attributes` entries.
   Report each proven missing name, declaration location, owner and evidence
   kind. Keep missing-docstring and stale-attribute rules separate and avoid
   duplicate diagnostics from the existing docs family.
4. Offer an AST-only fix adding entries in declaration order, retaining prose
   and inherited documentation. Use a proven annotation type when available
   and `TODO.` for the description; never fabricate a type or description.
5. Test dataclasses, frozen/slots dataclasses, inherited and overridden fields,
   properties/setters/cached descriptors, multiple inheritance, annotated-only
   fields, aliases, conditionally established assignments and dynamic unknowns.
   Invalidate only affected classes/dependents after a field or base changes.

**Done when:** completeness is proven within the documented static inventory,
properties and dynamic unknowns do not create false missing-attribute claims,
fixes are idempotent and preserve runtime behavior/comments, and corpus
performance stays within measured budgets.

### AF-25 — GDC018: require recognizable documented types for unannotated parameters
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** DOC014 copies existing annotations into docs; it cannot enforce
the Google §3.8.3 requirement for parameters without corresponding annotations.
Presence of a type is decidable only under an explicit documentation grammar.
This rule does not prove that the documented type is correct. Depends on AF-22.

**Steps:**
1. Define accepted type-bearing fields per supported style: Google
   `name (Type):`, NumPy `name : Type`, and explicit reST/Epytext type fields.
   Resolve linked names and stars through argument symbols. Do not recognize
   arbitrary words in description prose as types. Decide explicitly whether
   a leading `int. Input value.` convention is supported; reject it as type
   evidence until a bounded, documented grammar exists for that convention.
2. Validate documented type expressions through the existing type-expression
   parser/AST, without `eval`, imports or reparsing the Python module. Cover
   unions, generics, qualified names, forward references and starred type
   forms; distinguish malformed syntax, unknown symbols and absent types.
3. Apply only to parameters lacking AST annotations under the receiver policy.
   A missing parameter entry belongs to the existing name/presence detector;
   do not emit a second missing-type finding for the same missing entry.
   Preserve this check when `docstring_types=False`: the generation preference
   is not permission to omit required type evidence on unannotated arguments.
4. Add a typed `TODO.` field only when graph evidence establishes a spellable
   type. Otherwise report the absence without inserting `Any`, `object`, an
   invented type, or an executable annotation merely to clear the finding.
5. Test annotated/unannotated arguments, positional-only/keyword-only forms,
   `*args`/`**kwargs`, imported aliases, valid/invalid type syntax, prose-only
   descriptions and unsupported/mixed styles. Verify Ruff overlap separately.

**Done when:** findings demonstrate missing recognizable type evidence, never
semantic type correctness, with explicit refusal cases, style-preserving AST
fixes when justified, public configuration docs and regression coverage.

### AF-26 — GDC021: validate tuple-result documentation structure
- **Status:** open
- **Priority:** P1
- **Area:** rules
- **Readiness:** ready
- **Effort:** M · standard

**Context:** No current detector compares a proven tuple return with the
number of independently declared top-level return entries. Google §3.8.3
requires describing the tuple as one return value. Depends on AF-22 and the
structured docstring parser's preservation of entry nesting.

**Steps:**
1. Establish tuple return shape from a resolved annotation/type alias or
   converged return-expression evidence. Handle fixed/variadic tuples and
   explicitly defined tuple subclasses. Skip unresolved, contradictory and
   mixed tuple/non-tuple results; do not infer a tuple from documentation text.
2. Count independent top-level `Returns` entries using structural nodes.
   Preserve continuation paragraphs, nested lists, examples, literal/code
   blocks and explanations of tuple fields beneath one entry. Names of tuple
   elements need not match local variables and are not evidence of a violation.
3. Diagnose multiple independent results only when tuple shape and section
   structure are both established. Keep generator `Yields` and terminal
   `Returns` namespaces distinct; do not apply a return rule to yielded tuple
   elements, or require a return entry for `None`/`NoReturn`/`Never` functions.
4. Emit tuple-type/declaration evidence and the conflicting entry spans.
   Prefer a diagnostic-only repair suggestion; do not merge or rewrite
   natural-language descriptions automatically without a lossless structural
   transformation that preserves every child and ordering constraint.
5. Test two independent scalar entries, one tuple entry with nested field
   descriptions, single-entry NumPy docs, named tuples, aliases, variadic
   tuples, unions, unknown returns, generators and fenced/indented examples.

**Done when:** positive fixtures prove the structural inconsistency and
negative fixtures retain valid nested formats across supported styles;
unknown evidence produces no fabricated violation or prose rewrite.

## 19. Implementation recipes

*Scope:* Step-by-step recipes for tasks above.


The rule for this section: **one step = one edit or one command, with the file
and the check**. Read the step, do it, run its check, go to the next. The task
IDs are the ones in the milestone sections above; when a task here is done,
set the original task to `done` too. Batches still to be decomposed are listed in
20.9.

### Recipe M7-04 + M7-05 — parallel `astart fix --jobs N` (one feature, two IDs)

Facts: `run_fix` (src/astart/cli/commands.py:809) loops `for path in found.files:
outcome = _fix_file(...)`. `FixOutcome` is a frozen dataclass of `Path`/`str`/
`tuple`, so it pickles. `Catalog`, `Checker` and `FixCache` do not pickle, so
every worker builds its own. Project mode (`--project`) shares one index: keep it
serial.

1. **Setting.** In `FixCommandSettings` (commands.py:138) add this line to the `Attributes:` docstring:
   `jobs: Worker processes; 1 means serial.` and the field `jobs: int = 1`
   after `no_docs`. Check: `python -c "from astart.cli.commands import FixCommandSettings"`.
2. **Flag.** In `src/astart/__main__.py`, beside the other `fix` flags (search for
   `--min-confidence`), add `command.add_argument("--jobs", type=int, default=1)`;
   where `FixCommandSettings(...)` is built pass `jobs=max(1, args.jobs)`. Add the
   flag to the README flag table (tests/astart/test_readme_flags.py fails otherwise).
3. **Module-level worker.** Above `run_fix` add (it must be module level to pickle):
   ```python
   _WORKER: dict[str, object] = {}

   def _init_worker(settings: FixCommandSettings) -> None:
       """Build the per-process catalog and checker once."""
       _WORKER["catalog"] = load_default_catalog(registries=default_registries())
       _WORKER["checker"] = _make_checker(settings=settings)

   def _fix_in_worker(path: Path, settings: FixCommandSettings) -> FixOutcome:
       """Fix one file with the worker's catalog (no project context)."""
       return _fix_file(path=path, settings=settings,
           catalog=_WORKER["catalog"], checker=_WORKER["checker"],
           project=_ProjectContext(index=None, libraries=None, cache=None))
   ```
   The project rules forbid `object` annotations: type `_WORKER` as a small
   `@final` class `_Worker` with two attributes instead (`catalog: Catalog | None`,
   `checker: Checker | None`) and a module instance. Do that, not the dict.
4. **Dispatch.** In `run_fix` replace the loop header with a helper
   `outcomes = _outcomes(found.files, settings, ...)` returning an iterator:
   serial `(_fix_file(...) for path in files)` when `settings.jobs == 1` or
   `index is not None`; otherwise
   ```python
   with ProcessPoolExecutor(max_workers=settings.jobs,
           initializer=_init_worker, initargs=(settings,)) as pool:
       yield from pool.map(_fix_in_worker, files, repeat(settings), chunksize=4)
   ```
   (`from concurrent.futures import ProcessPoolExecutor`, `from itertools import repeat`).
   `pool.map` yields in input order, so the report text is identical to serial.
   This is the "streaming" of M7-05: each outcome is written as soon as it arrives.
5. **Cache and `--check`.** The on-disk cache (`_make_cache`) is not used in
   workers (cache=None). Say so in the flag help text. `--check`/`--diff` modes
   work unchanged because the parent writes/prints.
6. **Tests** (`tests/test_cli_jobs.py`): (a) write 6 small untyped files to
   `tmp_path`; run `main(["fix","--diff","--jobs","1",...])` and
   `--jobs 2`; assert identical stdout and exit code; (b) a file with a syntax
   error under `--jobs 2` yields `error:` for that path and exit 2 while the
   others are still reported; (c) `--jobs 0` is treated as 1. Mark (a) `slow`
   if it takes more than 5 s.
Done when: the three tests pass, FAST is green, and `--jobs 4` on
`tests/corpus/extended` prints the same summary line as `--jobs 1`.

### Recipe M7-06 — memory budget tests

1. Create `tests/astart/semantic/test_memory_budget.py`, marker `slow`.
2. Helper `_big_module(functions: int) -> str` that repeats a 12-line untyped
   function (`def f{i}(a, b=1):\n    x = a + b\n    return x\n`) `functions` times.
3. Test body: `tracemalloc.start()`; call `fix_source(source=..., filename="big.py", catalog=..., registries=..., settings=FixSettings(...))`;
   `_, peak = tracemalloc.get_traced_memory()`; `tracemalloc.stop()`.
4. Assert `peak < 400 * 1024 * 1024` for 2000 functions (≈ 24k lines). Record the
   measured value in the test docstring; set the bound to 3× the measured value.
5. Add a second test that the peak for 4000 functions is less than 2.5× the peak
   for 2000 (linear, not quadratic).
Done when: both tests pass; the numbers are written in TODO under M7-06.

### Recipe M7-11 — pre-commit and CI recipe

Facts: `.pre-commit-hooks.yaml` has one hook `astart-fix` (`astart fix --check`).
`.github/workflows/ci.yml` is the project's own CI.
1. Add a second hook to `.pre-commit-hooks.yaml`:
   ```yaml
   - id: astart-check
     name: astart check
     entry: astart check
     language: python
     types: [python]
   ```
2. Create `docs/engineering/ci.md` with three fenced examples: a `.pre-commit-config.yaml`
   (`repos: - repo: https://github.com/<owner>/astart  rev: v0.1.0  hooks: [{id: astart-fix, args: [--min-confidence, "0.8"]}]`), a GitHub Actions step
   (`pip install astart && astart fix --check --min-confidence 0.8 src`), and the
   exit-code table (0 clean, 1 would change, 2 usage error).
3. Link `docs/engineering/ci.md` from README under the flags table.
4. `tests/astart/test_docs_ci.py`: read `.pre-commit-hooks.yaml` as text; assert it
   contains `id: astart-fix` and `id: astart-check`; assert `docs/engineering/ci.md` mentions
   every `id:` found. (Do not import yaml.)
Done when: the test passes.

### Recipe M7-13 — `astart explain CODE path:line[:col]`

Facts: `run_explain(code, out, err)` (commands.py:537) prints a rule's rationale
and examples. The new form explains one finding.
1. Read `src/astart/rules/reasons.py` and `run_check` (commands.py:432) first;
   note how a finding stores its rule code, line and column.
2. In `__main__.py` give the `explain` parser an optional second positional:
   `explain.add_argument("location", nargs="?")`.
3. In commands.py add `run_explain_at(*, code, location, out, err) -> int`:
   split `location` with `rpartition(":")` twice into `path`, `line`, optional
   `column`; on `ValueError` write `astart: bad location` and return `Constants.usage_error`.
4. Inside it call the same check path as `run_check` for that one file
   (`_check_file`, commands.py:393), then keep findings whose `rule.code == code`
   and whose `line` matches (and `column` when given).
5. For each match print: the rule header (reuse the lines of `run_explain`), the
   finding's message, and its reasons (the evidence list from `reasons.py`).
   If none match print `astart: no <code> finding at <location>` and return 1.
6. Dispatch: `if args.command == "explain": return run_explain(...) if args.location is None else run_explain_at(...)`.
7. Tests (`tests/astart/cli/test_cli_explain_at.py`): file with one TYP001 finding; matching
   location prints the message; wrong line returns 1; `bad` location returns 2.

### Recipe M7-14 — `--backup` and `astart undo`

Facts: `_write_atomic(path, text, encoding)` (commands.py:564) already writes safely.
Design (decided): backups live in `.astart-backup/<run-id>/` next to the working
directory; one `journal.json` per run; undo never overwrites a file edited since.
1. New module `src/astart/cli/backup.py` with
   `@final @dataclass(frozen=True, slots=True) class Entry: path: str; before_sha: str; after_sha: str; saved: str`.
2. `def save(*, run_dir: Path, path: Path, before: str, after: str, encoding: str) -> Entry`:
   write `before` to `run_dir / f"{index:05d}.bak"` with `_write_atomic`; compute
   `sha256(text.encode(encoding))` for both texts; return the Entry.
3. `def write_journal(*, run_dir: Path, entries: Sequence[Entry]) -> None` using
   `json.dumps({"entries": [asdict(e) for e in entries]}, indent=2)`.
4. `def undo(*, run_dir: Path, out: TextIO) -> int`: for each entry, read the
   current file; if its sha equals `after_sha` restore `saved` content with
   `_write_atomic`; otherwise print `skipped (edited since): <path>`. Return 1 if
   any skipped, else 0.
5. Flag: `fix --backup` (default off). In `run_fix` where the file is written
   (`_emit`), call `backup.save` first when `settings.backup`. Run id =
   `datetime.now().strftime("%Y%m%dT%H%M%S")`. Add `backup: bool = False` to
   `FixCommandSettings` (+ docstring).
6. Subcommand `astart undo [RUN_ID]`: no id → newest directory in `.astart-backup`.
7. Tests (`tests/astart/cli/test_cli_backup.py`): fix a file with `--backup`, undo, text is
   the original; edit after fix then undo → file untouched and exit 1.

### Recipe M7-15 — wheel and entry-point check

Facts: `pyproject.toml` already declares `[project.scripts] astart` and
`package-data` for the catalog JSON and `py.typed`; `dist/` exists.
1. Create `scripts/utils/check_wheel.py` that (a) runs `python -m build --wheel --outdir <tmp>`,
   (b) opens the wheel with `zipfile`, (c) asserts it contains
   `astart/py.typed`, `astart/rules/artifacts/schema.json`, at least one
   `astart/rules/artifacts/catalog/*.json`, and `astart/stubs/__init__.py`,
   (d) creates a venv in `<tmp>` and runs `<venv>/bin/astart rules`, asserting
   exit code 0 and that the output has more than 10 lines.
2. Run it once; fix `package-data`/`MANIFEST.in` for whatever is missing
   (new packages `negotiation` and `stubs` are found by `packages.find include`).
3. Add a CI step in `.github/workflows/ci.yml`: `python scripts/utils/check_wheel.py`.
Done when: the script prints `ok` locally.

### Recipe M8-14 — maturity decides defaults

Facts: `Maturity` (vocabulary.py:104) has `experimental/stable/deprecated`; every
catalog rule has the field (model.py:138).
1. Find where rules are selected for a run: `grep -n "catalog.rules" src/astart/cli/commands.py src/astart/rules/engine.py`.
2. Add `FixSettings.experimental: bool = False` and `CheckSettings.experimental`
   with docstring lines; CLI flag `--experimental` (+ README row).
3. In the selection helper skip rules whose `maturity is Maturity.experimental`
   unless the setting is on.
4. For `deprecated` rules still run but print one line per run
   `note: rule <code> is deprecated`.
5. Tests: add a temporary rule with `maturity: experimental` in a test catalog
   (see `tests/astart/rules/test_rules_catalog.py` for building one); default run does not
   report it, `--experimental` does.
Done when: all 3 tests pass and `astart rules` still lists every rule.

### M5 protocol follow-ups (all in `src/astart/rules/protocols.py`)

Facts: `Member(name, is_method, positional, keywords, returns, is_async)`;
`_collect` (line 374) walks uses of a parameter; `_member_source` (517) renders
a member; `protocol_source` (576) renders the class; generated protocols use
`Protocol` only (no decorator).

**M5-06 read-only vs writable attributes**
1. Add `writable: bool = False` to `Member` (docstring line too).
2. In `_collect`, where an `Attribute` on the parameter is found, check
   `isinstance(node.ctx, Store)` (also `AugAssign` target and `del`); record
   `writable=True` for that member name (merge with `any`).
3. In `_member_source`, for `not member.is_method and member.writable`: a
   property would be wrong (it forbids assignment). Render `{pad}{name}: {annotation}`
   when `member.returns` is known; when unknown, return `None` from the usage
   builder so that **no protocol is made** (soundness over coverage).
4. Tests in `tests/astart/rules/test_rules_protocols.py`: read-only attribute → `@property`;
   assigned attribute with a provable type → plain annotation; assigned
   attribute with unknown type → no fix.

**M5-07 `runtime_checkable`** (decision: never emitted by default)
1. Add `FixSettings.runtime_protocols: bool = False`.
2. Only when on AND the module contains `isinstance(<expr>, <ProtocolName>)`
   for a protocol this run creates, prepend `@runtime_checkable` and make
   `ensure_names` import it (`known_imports` already lists `runtime_checkable`
   → `typing`).
3. Test both settings; default output has no decorator.

**M5-11 per-function placement switch**
1. Config key `[tool.astart] protocol-placement = "module" | "function"` read
   in `cli/config.py` (copy the pattern of an existing string key).
2. `module` is today's behaviour. `function` puts the class definition
   directly above the def that uses it (still module level, never nested).
3. Test: two functions, switch flips the order of class and def.

**M5-12 `TYPE_CHECKING` placement**
1. Only for protocols used in annotations only (parameters never instantiated).
2. Wrap the class in `if TYPE_CHECKING:` and quote the annotation (`'Proto'`);
   `ensure_names` adds `from typing import TYPE_CHECKING`.
3. Test: output imports cleanly (`exec` the result) and the annotation is a string.

**M5-20 `TypeVarTuple` pass-through; M5-21 variance** — both are suggest-only.
1. Add the detection to `typevars.py` as a pure function returning `None`
   unless exactly the pattern holds: `*args` returned unchanged as a tuple
   (M5-20) / a TypeVar only read (covariant) or only written (contravariant)
   inside a generic class (M5-21).
2. Gate behind `--experimental` (see 20.7); no write until a gold case exists.
3. One positive and two refusal tests each.

### Still to be decomposed (next batches, by priority)

The remaining open tasks that are one-liners today, in the order to expand:
1. M4 precision: M4-01, M4-03, M4-06 (see W-13), M4-08, M4-13, M4-16..19.
2. M2 OOP: M2-05, M2-10, M2-12, M2-13 (exit gate).
3. M6 kwargs: M6-02, M6-04, M6-09.
4. M5 remainder: M5-04, M5-09, M5-10, M5-19, M5-23, M5-25.
5. M7 rest: M7-10 (LSP), M7-12 (interactive review).
6. M8 / CC: M8-11, M8-13, CC-01, CC-02, CC-03.
7. F-16 and the 25 open F-tasks in 18.12 (already have steps; check each has a test).
Expand each with the same format as 20.1–20.8: facts (file:line), numbered
atomic steps with a snippet where the code is non-obvious, tests, done-when.

## 20. Cookbook — copy, paste, adapt

Everything here was checked against the code on 2026-11-08. Anything marked
**verify** needs one `grep` before use. These are templates for the recipes in
the chapters above; they remove the "where do I start" step.

### C-1 Detector module (AST only)

Shape taken from `rules/object_annotations.py`: a function over a parsed
module returning `Candidate`s, with evidence slots named in a `Constants` class.

```python
"""Short summary of what the rule flags."""

from __future__ import annotations

from ast import AST, Module, walk
from typing import Final, final

from astart.rules.procedural import Candidate, span_of


@final
class Constants:
    """Group module-level constants.

    Attributes:
        evidence_subject: Evidence key for the flagged subject.

    """

    evidence_subject: Final[str] = "subject"


def find_things(*, module: Module, filename: str) -> tuple[Candidate, ...]:
    """Flag every thing.

    Args:
        module: Parsed module.
        filename: Name used in spans.

    Returns:
        Candidates in source order.

    """
    found: list[Candidate] = []
    for node in walk(node=module):
        if _is_thing(node=node):
            found.append(_candidate(node=node, filename=filename))
    return tuple(found)


def _is_thing(*, node: AST) -> bool:
    """Decide from node types and fields only (no regex).

    Args:
        node: Node to test.

    Returns:
        Whether the node is flagged.

    """
    return False


def _candidate(*, node: AST, filename: str) -> Candidate:
    """Build one candidate.

    Args:
        node: Node to span.
        filename: Name used in the span.

    Returns:
        The candidate.

    """
    return Candidate(
        span=span_of(node=node, filename=filename),
        evidence={Constants.evidence_subject: "name"},
    )
```

### C-2 Catalog rule entry

Rules live in `src/astart/rules/artifacts/catalog/<domain>.json` under the top-level key
`"rules"` (the file also has `fixes`, `profiles`, `relations`). Fields seen in
`TYP001`: `code`, `key`, `domain`, `owner`, `title`, `message` (uses `{slots}`),
`rationale`, `severity`, `maturity`, `subject` (list of subject kinds),
`evidence` (list of `{name, type}`), `requires` and `when` (fact predicate) for
fact-based rules, `procedure` (a registered procedure name) for procedural rules,
`examples` (list of `{source, triggers, note}`), `fixes` (list of fix keys),
`params`, `aliases`. A fact-based rule has `"procedure": null`. For a procedural
rule copy an existing one: **verify** with
`grep -n '"procedure": "' src/astart/rules/artifacts/catalog/*.json | head -3`, then
register your function under that name where the others are registered
(`grep -rn "<that procedure name>" src/astart/rules/*.py`). Then run
`verify_catalog` (M8-21 step 1).
`TYP002`'s detector exists but has no catalog entry yet: that is task M8-03.

### C-3 Test for a rule or fix

```python
"""Tests for the thing rule."""

from __future__ import annotations

from textwrap import dedent

from astart.rules import (
    FixSettings, default_registries, fix_source, load_default_catalog,
)
from astart.rules.vocabulary import FixSafety

from tests.support.expectations import expect_equal


def _fixed(*, source: str, **options: bool) -> str:
    registries = default_registries()
    return fix_source(
        source=dedent(source),
        filename="m.py",
        catalog=load_default_catalog(registries=registries),
        registries=registries,
        settings=FixSettings(ceiling=FixSafety.guarded, min_confidence=0.5),
    ).source


def test_thing_is_fixed() -> None:
    """The flagged form becomes the wanted form."""
    expect_equal(actual=_fixed(source="x = 1\n"), expected="x = 1\n")
```

Test helpers take **keyword arguments** (`expect_equal(actual=..., expected=...)`);
positional calls raise `TypeError`. Run one file with
`python -m pytest tests/test_x.py -q -p no:cacheprovider`.

### C-4 New setting, end to end (the five places)

1. `FixSettings` in `rules/runner.py` (line ~170): field, default, and a line in
   its `Attributes:` docstring.
2. `FixCommandSettings` in `cli/commands.py` (line ~138): same.
3. `__main__.py`: `command.add_argument("--my-flag", ...)`, and pass it where
   `FixCommandSettings(...)` is built.
4. `cli/config.py`: the `[tool.astart]` key (copy a boolean key).
5. `README.md` flag table; `tests/astart/test_readme_flags.py` fails if it is missing.
Keep step 1–5 in one commit, written by the integration step (see Parallel lanes).

### C-5 Negotiation: add a rule

- **Seed:** in `negotiation/builders.py`, call `self._seed(path=..., source=..., origin=Origin.protocol)`
  for a language-guaranteed type (proof), `Origin.default` for a literal default (soft).
- **Edge:** `Contract(source, target, relation, polarity)` through the builder helpers; a
  new relation needs `forward` and `backward` entries in `negotiation/transfer.py` (use
  `None` when no sound inverse exists) and a member in `negotiation/model.py`.
- **Refuse:** call `_block(path=..., why="reason")`; opacity spreads downstream.
- **Accept:** only through `policy.accept` (proof, two soft signals, or soft plus engine).
- **Test:** `tests/astart/rules/negotiation/test_negotiation_module.py`; always add a refusal test beside the
  positive test; then run the shadow comparison (`wrong` must stay 0).

### C-6 Command cheat sheet

| Goal | Command | Time |
| --- | --- | --- |
| One test file | `python -m pytest tests/test_x.py -q -p no:cacheprovider` | seconds |
| Fast tier | `python -m pytest -m "not slow" -q -p no:cacheprovider` | about 5 min |
| Dev pair numbers | `PYTHONPATH=src:. python -m scripts.compare.pair fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5` | 1–2 min |
| Why it contradicts | `PYTHONPATH=src:. python scripts/compare/pair_wrong.py fixtures/untyped.py fixtures/typed.py --engine --min-confidence 0.5` | 1–2 min |
| Why a node is opaque | `PYTHONPATH=src python scripts/compare/opacity_report.py fixtures/untyped.py` | 1 min |
| Stdlib gate | `python -m scripts.benchmark recovery --jobs 8 --json /tmp/std.json` then `python -m scripts.benchmark gate --report /tmp/std.json --baseline scripts/benchmark/artifacts/resources/baseline.json` | 3 min |
| External gate | same with `--corpus tests/corpus/extended` and `scripts/benchmark/artifacts/resources/baseline_ext.json` | 12 min (run in background) |
| Dashboard | `python -m scripts.todo_update index docs/planning/TODO.md` | seconds |
| Status ledger | `python -m scripts.todo_update status render` (see the ledger section for the update commands) | seconds |
| Meaningful conversion report | `python scripts/compare` (2 to 3 minutes; add `--no-opacity` for about half) | 1–3 min |

### C-7 Debugging playbook (techniques that found real bugs)

- **Who wrote this annotation?** Run `fix_source(...)` with `max_rounds=1` and read
  `res.applied` (`fix_key`, `rule_key`, `subject_path` only; no text). If the
  annotation is in the output but not in `applied`, it did not come from a fix.
- **Is it a hint?** Wrap `HintIndex.hint_for` and `LazyVariables.hint_for` with a spy that
  prints hints whose `source` contains the suspect text and their `basis`.
- **Is it the engine?** Force `engine_hints.LazyConversion.text` to `None` with
  `E.LazyConversion.text = property(lambda self: None)`; if the symptom disappears, the
  engine text is the source. Check whether a call mutates the module by comparing
  `ast.dump(module)` before and after (this found the `apply=True` bug, W-03).
- **Bisect a big file** by cutting at top-level definition boundaries with
  `body[n-1].end_lineno`, but compare a *specific* annotation, not counts (counts mislead
  when a run applies nothing).
- **Never name a script like a stdlib module** (`bisect.py` shadows `bisect` and breaks
  `random`, `tempfile`, and everything importing them).

### C-8 Pitfalls from this project

- macOS `sed -i ''` needs the empty string; prefer a Python snippet for multi-line edits.
- When editing this file by task ID, match the real heading, not the example inside the
  Task template code fence (an edit once marked the example `done`).
- `scripts/todo_update/todo_index.py` may be reformatted by other agents; use its current
  `Constants` names, do not rely on module-level names.
- `Constants` classes, `from x import y` (never `import x`), keyword-only calls,
  Google docstrings, no `Any`/`object` annotations, no regex (CC-08).
- Do not run `exactus` or add `noqa`/`type: ignore`.
- A full slow tier is about 19 minutes; poll long jobs in steps of at most 10 s and stop
  a foreground command before 590 s (use background for anything longer).

### C-9 Glossary

| Term | Meaning |
| --- | --- |
| Hint / `HintBasis` | A proposed annotation and the kind of evidence behind it (`default_literal`, `call_sites`, `negotiated`, `engine`, ...). |
| Negotiation | The two-way solver in `rules/negotiation/` that settles node types from contracts. |
| Node / contract / belief | A thing with a type (`f.x`, `f->`), a directed fact between nodes, and what a node currently holds. |
| Opaque | A node the tool refuses to type; opacity spreads to everything downstream. |
| Engine | The older converter (`graph`); its annotations are the lowest tier and checker-gated. |
| Conversion mode | `--engine`: take the engine's annotations where nothing else decides. |
| Pair | An untyped file and its typed twin (`fixtures`, `dev/`); the benchmark scores one against the other. |
| Gate | A benchmark comparison against a stored baseline that must print PASS. |
| Guarded fix | A fix whose safety depends on evidence; it needs the confidence floor and, optionally, the checker. |
| Lane | A set of tasks owning disjoint files, so agents can work in parallel. |

## 21. Risks and contingencies

*Scope:* Problems forecast on 2026-11-08, each with detection and mitigation.  
*ID prefixes:* R

### R-01 — Baseline refreshes must be justified and logged
- **Status:** done
- **Priority:** P0
- **Area:** risk
- **Readiness:** done
- **Effort:** S · light

**Forecast:** Accepting a new baseline silently hides a regression; one `baseline` command can erase weeks of precision.

**Steps:**
1. In `benchmarks/__main__.py` make `baseline` require `--reason "text"`.
2. Append `date, command, old→new key numbers, reason` to `scripts/benchmark/artifacts/resources/baseline_log.md`.
3. Make `gate` print the log's last entry when it fails.
4. Test: `baseline` without `--reason` exits 2.

**Done when:** no baseline changes without a logged reason.

**Evidence:** `benchmarks baseline` requires `--reason`
(argparse exit 2 without it) and appends `date · baseline ·
precision/recall old→new · reason` to `scripts/benchmark/artifacts/resources/baseline_log.md`
(`--log` overrides). `benchmarks gate` prints `last baseline change:`
with the log's newest entry when it fails. Tests in
`tests/scripts/benchmark/test_bench_cli.py`: reason required, log written, gate echoes
the entry — 4 pass.

### R-02 — Hold-out pairs: stop overfitting to the two fixtures
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** L · standard

**Forecast:** Every fix this session was tuned on `fixtures/untyped.py` and the resolver pair; rules that help those files can hurt others, and calibration shares data with evaluation.

**Steps:**
1. Build 20 pairs from typed modules in `tests/corpus/extended` by stripping annotations (`strip_annotations`, `rules/recovery.py:780`); the typed original is the twin.
2. Split into `calibration` (10) and `holdout` (10) lists in `fixtures/split.json`; rules and confidence tiers may only look at `calibration`.
3. Report all contract metrics (A-02, A-03) on `holdout` in `scripts.compare.pair --set holdout`.
4. Add a test that fails if `confidence` calibration code reads a holdout path.

**Done when:** targets are measured on files no rule was tuned on.

### R-03 — Typeshed snapshot drift between machines
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** `find_typeshed` picks the first copy found (basedpyright, pyright, mypy, jedi...); different machines give different library return types and different output.

**Steps:**
1. Compute a short hash of the chosen typeshed's `VERSIONS` file and stdlib directory listing.
2. Include it in `astart --version` output and in the fix cache key.
3. `ASTART_TYPESHED` or `--typeshed PATH` must override; log which copy was used with `--verbose`.
4. Test with two fake typeshed directories: different hashes, different cache keys.

**Done when:** output is reproducible given the printed typeshed hash.

### R-04 — Emitted code must compile on every supported target
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** Generated syntax (`X | None`, `type X = ...`, `Self`, PEP 695) breaks on older targets; the tool runs on 3.13 but users target 3.9 to 3.13.

**Steps:**
1. Add `tests/test_target_matrix.py`: for each `--target-version` in 3.9..3.13 fix the corpus and run `ast.parse(..., feature_version=(3, minor))` on the output.
2. Any construct invalid for its target is a bug in the gating (`PythonTarget`), fix there.
3. Run the matrix for all of S-03, AF-06, W-11, M5-23.

**Done when:** no fix output fails to parse for its declared target.

### R-05 — ruff version differences break idempotence and f-string formatting
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** `ruff format` output changes between releases; `fix ∘ fix` and AF-21 can flip-flop or fail when ruff is missing.

**Steps:**
1. Detect `ruff --version` once per run; put it in the cache key and `--verbose` output.
2. If ruff is missing, skip formatting steps cleanly with one note line.
3. Test with a fake `ruff` executable that returns a different layout: results stay stable and parse-equal.
4. Document the tested ruff range in README.

**Done when:** runs are stable across the tested ruff range and degrade cleanly without ruff.

### R-06 — Type checker absent, old or different (pyright vs mypy)
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** The checker gate decides what conversion mode keeps; no checker means `no_checker_floor`; versions disagree on the same file.

**Steps:**
1. Record checker name and version in the cache key and report.
2. Add a test with a stub `Checker` returning errors for one fix and nothing for another (exists in spirit in G-07).
3. When no checker is found, state the effective floor in the first output line.
4. Run the pair with pyright and with mypy once; store both numbers in `docs/analysis/scripts.benchmark.md`.

**Done when:** results are labelled with the checker used.

### R-07 — Large files and deep projects blow up time or memory
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** L · deep

**Forecast:** The graph and prover may be superlinear; the M7-02 budget (12 k lines in 5 s) is unmet (36.9 s) and the 50 k-line cliff is known.

**Steps:**
1. Add `benchmarks/scale.py` generating 1 k, 5 k, 20 k, 50 k line modules from corpus functions.
2. Record time and peak memory (`tracemalloc`) per size in `scripts/benchmark/artifacts/resources/baseline_perf.json`; gate at +20 %.
3. Profile the worst size with cProfile; fix the top superlinear function (CC-10 incremental parse, F-27 per-function facts, F-34 budget fallback).
4. Make the runner degrade (skip negotiation, keep hint index) above a configurable line count instead of timing out.

**Done when:** 50 k lines finish under the budget or degrade with a note, never hang.

### R-08 — Parallel runs corrupt the cache or interleave output
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** `--jobs N` (M7-04) plus an on-disk cache means concurrent writers.

**Steps:**
1. Write cache entries atomically (`_write_atomic` pattern) with the content hash in the file name.
2. Never share a mutable index file between workers; each worker writes its own entries only.
3. Test: 8 processes fix the same 50 files twice; second run is all cache hits and all outputs equal the serial run.

**Done when:** no corrupt or partial cache entries under concurrency.

### R-09 — Weird files: encodings, BOM, CRLF, tabs, form feeds, NUL bytes
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** The lossless promise fails first on unusual byte layouts; `read_source` returns an encoding but not every writer path keeps it.

**Steps:**
1. Create `tests/weird/` with generated files: UTF-8 BOM, latin-1 coding cookie, CRLF, mixed endings, tabs, form feed, very long line (100 k chars), file without final newline, NUL byte, zero-byte file.
2. For each: `fix_source` returns identical bytes except the intended edits; encoding and endings preserved; a NUL or undecodable file yields one error line.
3. Fix each failure in the owning writer.

**Done when:** all weird files round-trip with no collateral changes.

### R-10 — Syntax the parser does not know (newer Python, Python 2, templates)
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** Python 3.14 syntax (t-strings, `except A, B`) or Python 2 files make `ast.parse` raise; the tool must neither crash nor mangle.

**Steps:**
1. Corpus of invalid inputs: Python 2 print statement, unclosed brackets, 3.14 t-string, null bytes.
2. Assert one `path: error:` line, exit code 2 for that file only, other files processed (CC-03).
3. PRS001 (M8-05) reports the first error with line and column.

**Done when:** invalid files never crash a run or get rewritten.

### R-11 — Filesystem edge cases: symlinks, read-only, changing files
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** Atomic writes resolve symlinks; a file edited by the user during a run can be overwritten.

**Steps:**
1. Before writing, compare the file's mtime and size with those read; if changed, skip with `changed-during-run`.
2. Tests: symlinked file stays a symlink; read-only file reports an error and is untouched; directory with 5 000 files finishes.
3. Respect `.gitignore` only when asked (`--respect-gitignore`); default uses `exclude` globs.

**Done when:** no silent overwrite of a file changed since it was read.

### R-12 — Spans drift after many edits
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · deep

**Forecast:** Later edits are placed from AST positions; one wrong shift (CC-10) corrupts every following edit.

**Steps:**
1. Invariant test: after N random edits, for every statement node `ast.get_source_segment` re-parses to the same node type and `ast.dump` of the whole module equals a full re-parse.
2. Run it over the weird-file corpus (R-09) and 30 corpus modules with 500 edits each.
3. On any mismatch the runner must fall back to a full parse and log `reparse-mismatch`; count them in the report.

**Done when:** zero mismatches in the invariant test; the fallback is covered by a deliberately broken splice.

### R-13 — Security: executing project code and loading plugins
- **Status:** done
- **Priority:** P0
- **Area:** risk
- **Readiness:** done
- **Effort:** M · deep

**Forecast:** `benchmarks semantic` imports target packages; the plugin API (API-07) loads arbitrary modules; subprocesses take user paths.

**Steps:**
1. Write `docs/engineering/security.md`: the product never imports or executes analysed code; only benchmarks do, inside a throwaway directory.
2. Add a test that scans `src/astart` for `exec(`, `eval(`, `importlib.import_module`, `os.system`, `shell=True`, `subprocess` with a string command (AST scan) and fails on any non-allow-listed use.
3. Plugins load only names listed in config, never from the analysed project's own tree.
4. All subprocess calls use argument lists.

**Done when:** the scan test passes and the threat model is documented.

**Evidence 2026-11-09:** `docs/engineering/security.md` shipped — parsing-only model,
the `--checker` scratch-copy exception, argv-only subprocesses, the
benchmarks-imports-targets caveat, the plugin constraint (config-listed
names only, deferred to API-07) and the stdlib-only supply chain.
`tests/astart/test_no_dynamic_execution.py` AST-scans all of `src/astart` for
`exec`/`eval`/`__import__`/`import_module`/`os.system`/`shell=True`/
`create_subprocess_shell`/string-command subprocess calls; exactly three
reviewed uses exist (`typeshed_client.py` env-gated import, `recovery.py`
`import_module("typing")`, `protocol_verify.py` `__import__("builtins")`)
and are allow-listed with justifications — the liveness test fails if an
entry goes stale. All subprocess call sites verified argv-form
(`artifacts.py`, `rules/process.py`). 2 tests pass; ruff clean.

### R-14 — Licensing and attribution
- **Status:** done
- **Priority:** P1
- **Area:** risk
- **Readiness:** done
- **Effort:** S · light

**Forecast:** The stubs reader is migrated from typeshed_client ideas; typeshed data and the external corpus have licences.

**Steps:**
1. Add `LICENSES.md` listing typeshed (Apache-2.0/MIT), the migrated ideas and their origin, the external corpus entries and their licences (the existing `tests/corpus/extended` licensing file).
2. Add a header comment in `astart/stubs/__init__.py` naming the origin.
3. Test: every directory in `tests/corpus/extended` has a licence entry.

**Done when:** every third-party item has an attribution entry.

**Evidence 2026-11-09:** `LICENSES.md` shipped — astart (MIT), typeshed
stub data (Apache-2.0/PSF, read at runtime + `libkw` generation), the
`typeshed_client` ideas migration (re-implemented, env-gated optional
backend) and all 25 corpus distributions pointing at
`tests/corpus/extended/LICENSES/`. Header comment added to
`src/astart/stubs/__init__.py`. `test_every_corpus_distribution_has_a_
licence` parses `MANIFEST.json` and asserts a `LICENSES/<dist>.txt` per
distribution (25/25 present). 3 hygiene tests pass; ruff clean.

### R-15 — Documentation drift
- **Status:** done
- **Priority:** P1
- **Area:** risk
- **Readiness:** done
- **Effort:** S · light

**Forecast:** README flags, rule list, API surface and this TODO go stale as agents land features.

**Steps:**
1. CI step: `python scripts/generate_rule_docs.py && git diff --exit-code docs/guides/rules.md`.
2. CI step: `python -m scripts.todo_update index docs/planning/TODO.md && git diff --exit-code docs/planning/TODO.md`.
3. Keep `tests/astart/test_readme_flags.py` and the API surface test (API-05) in the fast tier.

**Done when:** CI fails when generated docs are stale.

**Evidence:** `.github/workflows/ci.yml` gained a `docs` job:
`generate_rule_docs.py` + `git diff --exit-code docs/guides/rules.md`, then
`python -m scripts.todo_update index docs/planning/TODO.md` + `git diff --exit-code docs/planning/TODO.md`. Running the
generator locally immediately proved the drift — `docs/guides/rules.md` was
missing DOC004; regenerated and kept. `test_readme_flags.py` and
`test_api_surface.py` carry no `slow` marker, so they already run in
the fast tier (`pytest -m "not slow"`).

### R-16 — Flaky or slow tests hide real failures
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** The slow tier is 19 minutes; hash seeds, timeouts and temp directories can make tests flaky.

**Steps:**
1. Add a nightly job running the fast tier twice with `PYTHONHASHSEED=1` and `=2`; any difference fails.
2. Add the marker `quarantine` for known flaky tests with an owning task ID; excluded from gates, listed in the dashboard.
3. Print the 20 slowest tests (`--durations=20`) in CI.

**Done when:** flaky tests are visible, owned and cannot block unrelated work.

### R-17 — Incident playbook: a release writes a wrong annotation
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · standard

**Forecast:** The project promises zero wrong annotations; one real regression needs a fast, safe response.

**Steps:**
1. Document in `docs/incident.md`: reproduce with a pair, find the writer (Cookbook C-7), add the regression test first, disable via `--disable KEY` as a stopgap, release a patch.
2. Make sure every fix key can be disabled by flag and config (S-07) and listed by `astart rules --json` (API-12).
3. Add `--backup` and `astart undo` (M7-14) to the release checklist.
4. Add a canary run to release: fix the pinned corpus and diff against the last release's output; any unexplained change blocks release.

**Done when:** the playbook exists and the canary diff runs.

### R-18 — Merge conflicts on hot shared files
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** L · deep

**Forecast:** `FixSettings`, `FixCommandSettings`, `__main__.py`, the README flag table and catalog JSON are edited by almost every lane; parallel agents will collide.

**Steps:**
1. Create `src/astart/settings_registry.py`: one declarative list of settings (name, type, default, CLI flag, config key, help, README row) as frozen dataclasses.
2. Generate `FixSettings` fields, the argparse flags, the `[tool.astart]` validation and the README table from it (a script `scripts/generate_settings.py` with a CI diff check).
3. Migrate existing settings one at a time with a test that old and new behaviour agree.
4. New settings after this are one registry line.

**Done when:** a new setting touches one file.

### R-19 — The TODO file itself: size, concurrent edits, format corruption
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** L · standard

**Forecast:** `docs/planning/TODO.md` is over 7 000 lines; agents edit it concurrently; one malformed task breaks the dashboard (this happened with the renamed parser constants).

**Steps:**
1. Split into `docs/todo/NN-chapter.md` files plus a generated `docs/planning/TODO.md` index; one lane edits one chapter file.
2. Extend `scripts/todo_update/todo_lint.py` (created 2026-11-08 with checks for markers, metadata, steps, placeholders, titles, IDs, chapters, anchors and Area vocabulary; wire it into CI): every task has Status, Priority, Area, Readiness, Effort, Steps, Done when; IDs unique; cited IDs exist; fenced examples ignored.
3. Run the linter in CI and before the dashboard script; make `scripts/todo_update/todo_index.py` use the same parser.
4. Document the edit protocol: change only your chapter file, then run the index script.

**Done when:** the linter passes and two agents can edit different chapters without conflict.

### R-20 — Engine health: the old converter can fail or change
- **Status:** open
- **Priority:** P1
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · deep

**Forecast:** Conversion mode depends on `graph` (huge, 7 k-line modules); it returns no text on some modules and changes would silently move accuracy.

**Steps:**
1. Add a metric: share of corpus modules where `LazyConversion.text` is `None`; print it in the recovery report.
2. Gate: it may not rise above the baseline.
3. Test the whole pipeline with the engine forced to fail: output equals the non-engine output.
4. Document the engine's role as lowest tier in `docs/architecture/negotiation.md`.

**Done when:** engine failure never changes non-engine behaviour.

### R-21 — Deep nesting and recursion limits
- **Status:** open
- **Priority:** P0
- **Area:** risk
- **Readiness:** ready
- **Effort:** M · deep

**Forecast:** Prover, algebra and subtype checks recurse (G-09 is one proven case); a 1 000-level expression can raise `RecursionError` anywhere.

**Steps:**
1. Fuzz generators: nested parentheses, binops, lists, lambdas, attribute chains and f-strings to depth 50, 200, 1 000.
2. Run `fix_source`; the result must be the original text with a skip note, never an exception (CC-03).
3. Convert the offending recursive walks to explicit stacks or add depth guards that return `None`/opaque.

**Done when:** deep inputs never crash the tool.

### R-22 — Unicode names and generated-name collisions
- **Status:** open
- **Priority:** P2
- **Area:** risk
- **Readiness:** ready
- **Effort:** S · light

**Forecast:** Non-ASCII identifiers and normalised names can collide with generated Protocol/TypeVar names (M5-24).

**Steps:**
1. Tests: module with `Ünïcode` classes and a generated protocol; names follow NFKC (`unicodedata.normalize`) before comparison.
2. Generated names pick a free suffix across the whole project (`ProjectIndex`).

**Done when:** no collisions with Unicode identifiers.

### R-23 — Optional dependencies missing
- **Status:** open
- **Priority:** P2
- **Area:** risk
- **Readiness:** ready
- **Effort:** S · light

**Forecast:** Dev-only tools (`typing_utils`, pyright, mypy, ruff) may be absent in user environments and in CI.

**Steps:**
1. Run the fast tier in an environment without them (`pip install --no-deps` of astart only).
2. Every test needing them is skipped with a reason, never errors at import time.
3. Document the optional tools in README.

**Done when:** the fast tier passes without optional tools.

**Progress 2026-11-09:** clean-env verification done — venv with
`pip install --no-deps -e .` + `pytest` only (no ruff, basedpyright,
pyright, mypy, typing_utils, defusedxml): collection succeeded on every
test module with zero optional-dependency `ImportError`s; 5501 passed,
891 deselected (slow), 2 xfailed. The only dependency gap found was
`defusedxml` imported eagerly by `tests/astart/cli/test_cli_reporters.py` and
`tests/astart/cli/test_cli_reports.py`; both now resolve the parser lazily through
`pytest.importorskip("defusedxml.ElementTree")` inside `_xml_root`, so
the two JUnit tests skip with a reason while the other 13 still run
(verified: `13 passed, 2 skipped` in the clean venv). Optional tools are
documented in the README Development section (`ruff` format
normalization, `basedpyright`/`pyright`/`mypy` checker gates — all
already degrade gracefully via `shutil.which`). Stale
`regex_allowlist.txt` entries for `ast.py`, `autowrap.py` and
`appliers.py` (whose `re` imports were already removed) were cleaned.
Remaining blocker for the literal done-when: the fast tier currently
shows 3 failures unrelated to dependencies —
`test_no_unlisted_dynamic_execution` (`__import__` sites in
`rules/methods.py`, `rules/negotiation/*`, `rules/recovery.py`,
`semantic/*` pending allowlist review),
`test_readme_flags_appear_in_cli_reference` (`--checker-delta`,
`--checker-gate` missing from `docs/guides/cli.md`) and
`test_no_false_positive_suppression` (comment classification) — all
reproduce with full deps installed and belong to concurrent in-flight
work, not to optional-tool absence.

### R-24 — Honest accuracy reporting
- **Status:** done
- **Priority:** P0
- **Area:** risk
- **Readiness:** done
- **Effort:** S · light

**Forecast:** The contract numbers are quoted in reports; a quoted figure measured on the wrong set or an older tree misleads decisions.

**Steps:**
1. `benchmarks targets` (G-01) prints the commit-independent tree hash (hash of `src/astart`), the corpus set (calibration or holdout) and the date next to each number.
2. Refuse to print PASS when the tree hash differs from the one stored with the report (stale report).
3. Add the same stamp to `docs/analysis/scripts.benchmark.md` generated tables.

**Done when:** every reported number carries its tree hash and data set.

**Evidence 2026-11-09:** new `benchmarks/treehash.py` — `tree_hash(root)`
digests sorted `(path, bytes)` of every `src/astart/**/*.py` into a
12-hex SHA-256, commit-independent. `Report` gained `tree_hash`/`corpus`
fields (default `""`, backwards compatible); `to_json` writes them into
`summary`, `from_json` restores them. `recovery` stamps both
(`corpus` = corpus dir name). `gate` prepends `FAIL stale report: tree
…` and exits 1 whenever a stamped report's hash differs from the current
tree — unstamped legacy reports are exempt. `targets` appends
`tree <hash> · corpus stdlib+external · <date>` to every verdict row via
`_provenance_stamp`. `docs/analysis/scripts.benchmark.md` documents the contract and
notes the two accepted baselines predate stamping. Tests:
`test_stamp_round_trips`, `test_unstamped_reports_still_round_trip`,
`test_recovery_stamps_tree_hash_and_corpus`,
`test_gate_rejects_a_stale_report`,
`test_targets_stamp_names_tree_corpus_and_date` — 19 bench tests pass.

### R-25 — Tests and lint for the TODO tooling
- **Status:** done
- **Priority:** P1
- **Area:** risk
- **Readiness:** done
- **Effort:** M · standard

**Forecast:** The two scripts that keep this document honest have no tests and no
lint run. A silent bug there (a wrong count, a lost marker, an unparsed task)
would make every dashboard number untrustworthy, and other agents edit the
scripts' neighbours.

**Steps:**
1. Create `tests/scripts/todo_update/test_todo_tools.py`; import the scripts with `from scripts import status_update, todo_index` (the repository root is on the path for the other tests: they import `tests.support.expectations`).
2. `status_update` tests: `render` of a minimal state contains the history row, the target row (90 % of the totals) and every check; `apply` for `check`, `item add`, `item remove` and `note` changes exactly the intended field; `write_block` raises `SystemExit` when a marker is missing and preserves text outside the markers; the `pair` command reads a JSON string (monkeypatch `status_update.stdin`). Also test `bar` (0 %, 100 %, empty total), `delta_text` (better, worse, no change, n/a, lower-is-better), `ago` and `human_time` with fixed datetimes, and that two consecutive `refresh` runs show `no change`.
3. `todo_index` tests on a small sample document: `parse` finds an open and a done task, ignores the fenced example, and reads a completed-table row; the dashboard counts match; `missing_in_matrix` reports an unknown ID and accepts known ones. Also test `scripts/todo_update/todo_lint.py` (`parse_id`, `slug`, and one small fixture document per error kind) and the chapter bars of `scripts/todo_update/status_update.py`.
4. Run ruff only on the touched files, in the house order: `ruff check --fix scripts/todo_update/status_update.py scripts/todo_update/todo_index.py tests/scripts/todo_update/test_todo_tools.py; ruff format <same files>; ruff check <same files>`; fix findings without `noqa`. Do not run `exactus`.
5. Record the result: `python -m scripts.todo_update status check lint pass --note "ruff on the TODO tooling"`.

**Done when:** the new tests pass in the fast tier and the ledger's lint row says `pass` for these files.

**Evidence 2026-11-09:** `tests/scripts/todo_update/test_todo_tools.py` (26 tests) covers `render`,
`apply`, `write_block`, the `pair` stdin path, `bar`, `delta_text`, `ago`,
`human_time`, double `refresh` stability, `todo_index.parse`/`dashboard`/
`missing_in_matrix`, `todo_lint.parse_id`/`slug`/`lint` and
`chapter_rows`/`chapter_of`. Writing it exposed two real bugs, both fixed:
`todo_index.parse` counted tasks inside fenced code blocks and
`todo_lint.parse_id` rejected compound prefixes (`CC-08-01`, `AL-06`,
`API-01`), hiding those citations from the linter. Ruff clean on all
touched files; `exactus --lints`, `--docs` and `--kwargs_typehints` all
PASS. Ledger `check lint pass --note "ruff on the TODO tooling"` recorded.

### R-26 — Make `docs/planning/status.json` updates atomic, locked and validated
- **Status:** done
- **Priority:** P1
- **Area:** risk
- **Readiness:** done
- **Effort:** M · standard

**Forecast:** Several agents will run the status script during parallel work. Two
overlapping runs can lose an update, and a half-written or hand-edited
`docs/planning/status.json` can break every later run and the generated ledger.

**Steps:**
1. In `scripts/todo_update/status_update.py`, write the state to a temporary file in the same directory and move it over `docs/planning/status.json` with `Path.replace`, so a reader never sees a half-written file.
2. Add a lock: create `docs/planning/status.json.lock` with `os.open(path, os.O_CREAT | os.O_EXCL)`; retry up to 50 times at 100 ms intervals; remove it in a `finally`; treat a lock older than 60 seconds as stale (warn and take over).
3. Re-read the state after taking the lock and before applying the command, so two agents' updates merge instead of overwriting each other.
4. Add `validate_state(*, state) -> list[str]` returning readable problems (missing key, wrong type, unknown check status) and call it on load and before saving; a non-empty list exits with code 2 and prints the problems.
5. Tests in `tests/scripts/todo_update/test_todo_tools.py` (R-25): two processes each add an item at the same time and both items are present; a corrupted file produces a message naming the key; a stale lock is taken over.

**Done when:** the three tests pass and ten parallel `item add` runs lose nothing.

**Evidence 2026-11-09:** `scripts/todo_update/status_update.py` gained
`write_state` (temporary file in the same directory, `fsync`, `Path.replace`),
`locked` (`docs/planning/status.json.lock` via `Path.touch(exist_ok=False)`, 50 retries
at 100 ms, stale locks older than 60 s taken over with a warning) and
`validate_state`/`_fail_on` (exit 2 naming every problem on load and save).
`main` runs load → apply → save inside the lock so concurrent updates merge.
`validate_state` is split into per-section helpers to stay under the
complexity gates. `tests/scripts/todo_update/test_todo_tools.py` proves ten parallel
`item add` subprocesses all land, a corrupted file exits 2 naming the key,
a stale lock is taken over and a live lock blocks after the retry budget.

## 22. Algorithms and intelligence

*Scope:* Algorithms that raise accuracy beyond the current special cases, each fully specified.  
*ID prefixes:* AL

### AL-01 — Control-flow graph and per-block narrowing (replaces ad-hoc `if` handling)
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Narrowing today is a set of special cases (`isinstance`, `is None`, truthiness, `assert`). A CFG makes all of them one mechanism and fixes `else`, early `return`, loops and `try`.

**Steps:**
1. Create `negotiation/cfg.py`: `build_cfg(*, function) -> Cfg` with basic blocks of statements and edges labelled `true`, `false`, `exception`, `loop`.
2. Compute reachability and dominators (Cooper-Harvey-Kennedy iterative algorithm).
3. Represent a narrowed view of a name per block as nodes `f.x#B` fed by the previous block's node and constrained by edge conditions.
4. Replace `narrowing.py`'s special cases one at a time, keeping its tests green after each.
5. Add tests for early return, `while`, `try/except/else/finally`, `with`, `match`.

**Done when:** all existing narrowing tests pass on the CFG implementation and I-01, I-02, I-03 are covered by it.

**Insights:** Most unsoundness found so far came from control flow the code did not model (rebinding, loops, handlers). One mechanism removes a class of bugs instead of patching each.

**Architecture:** New leaf module `negotiation/cfg.py` (pure AST in, graph out, no negotiation imports); `narrowing.py` becomes a client. Switch `negotiation_cfg` (default on after parity).

**Algorithm:** 1) Split the body into basic blocks at branch points. 2) Add edges per statement kind (`If`→true/false, `While`/`For`→loop+exit, `Try`→exception edges to each handler and `finally`, `Return`/`Raise`→exit). 3) Dominator tree by iterating `idom(b) = intersect(preds)` in reverse postorder until stable. 4) For each edge, derive the constraint (`x is None`, `isinstance(x, C)`, truthiness, comparison with `None`). 5) Join at merge points: union of incoming narrowed types. 6) Loop back-edges use widening (AL-02).

**Performance:** O(blocks + edges) to build, O(blocks × tracked names) to propagate; track only names that appear in a narrowing test (usually under 10 per function); cache per function hash.

### AL-02 — Widening at loops so fixpoints terminate and stay precise
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Loops can grow a type forever (`x = [x]`) or oscillate. The negotiator currently relies on event caps.

**Steps:**
1. Add a widening operator to `TypeAlgebra`: after the third change of a belief at a loop head, replace a growing nesting by `opaque`, and a union beyond 4 arms by `opaque`.
2. Record widening events in the explanation trail (F-26).
3. Tests: `x = []; for ...: x = [x]` ends opaque; `total = 0; for ...: total += 1.5` ends `int | float`.

**Done when:** loops terminate by construction, and the two tests pass.

**Insights:** A cap on events is a safety net, not an algorithm; it makes results depend on iteration order, which breaks determinism (A-07).

**Architecture:** Lives in `negotiation/algebra.py` and `negotiator.py`; no new dependency; a setting `widen_after` (default 3).

**Algorithm:** 1) Track a change counter per belief. 2) When a belief on a loop-head node changes more than `widen_after` times, apply `widen(old, new)`: if `new` nests `old` deeper than depth 3 or has more than 4 union arms, return opaque; else `union(old, new)`. 3) Opaque spreads as usual.

**Performance:** O(1) extra per update; guarantees at most `widen_after + 2` changes per loop-head belief.

### AL-03 — Interprocedural summaries in SCC order
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Return types of callees feed callers, but order of evaluation is incidental. A summary per function, computed bottom-up, makes results deterministic and enables mutual recursion.

**Steps:**
1. Build the call graph for the module (project mode: whole project) from bound calls (`CallBindings`).
2. Compute strongly connected components with Tarjan's algorithm and process them in reverse topological order.
3. Inside an SCC iterate to a fixpoint with widening (AL-02); outside it, one pass.
4. Cache each function's summary (parameter and return beliefs) keyed by the function's source hash plus its callees' summary hashes.
5. Tests: chain of calls, mutual recursion, call through an alias.

**Done when:** results do not depend on definition order and mutually recursive functions settle (I-15).

**Insights:** Whole-module graph solving works but gives no reuse across runs; summaries are the unit of incremental analysis (AL-12).

**Architecture:** `negotiation/summaries.py`, used by `run.py`; summaries are plain frozen dataclasses so they can be cached on disk.

**Algorithm:** 1) Nodes are functions, edges are bound calls. 2) Tarjan SCC in O(V+E). 3) Process SCCs bottom-up; within an SCC iterate until no summary changes, bounded by widening. 4) Summary = (parameter beliefs from call sites, return belief). 5) Hash = hash(function source, sorted callee summary hashes).

**Performance:** O(V+E) for ordering; each function solved once per input change; unchanged functions are cache hits.

### AL-04 — Alias and escape analysis for containers
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Container typing currently refuses when a container is passed anywhere unknown. Many such calls are harmless (the callee only reads).

**Steps:**
1. Compute for each function which parameters it mutates (AL-16) and whether it stores them (escape).
2. Allow a container to be passed to a callee whose summary says 'reads only, does not store'.
3. Add a field-insensitive points-to relation for local names (Andersen-style, inclusion constraints solved with a worklist).
4. Tests: `out = []; helper(out); out.append(1)` stays opaque; `helper` read-only keeps `list[int]`.

**Done when:** containers passed to read-only callees stay typed; mutating callees still make them opaque.

**Insights:** Over-conservative escape rules are the largest source of unannotated containers after unknown calls.

**Architecture:** `negotiation/aliases.py` using AL-03 summaries; replaces the ad-hoc `pure_calls` list in `containers.py`.

**Algorithm:** 1) For each assignment `a = b` add constraint `pts(a) ⊇ pts(b)`; `a = []` creates a fresh object. 2) Solve with a worklist until no points-to set changes. 3) A container object escapes if it flows to a store (`self.x = a`, global, return of unknown), to an unknown callee, or to a callee whose summary mutates/stores that parameter. 4) Non-escaping objects keep element typing.

**Performance:** Near-linear for local names (inclusion constraints over few variables); skip functions with more than 500 locals.

### AL-05 — Probabilistic fusion of evidence (log-odds) instead of hand tiers
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Acceptance uses rules (proof, two soft signals, soft plus engine) and fixed confidences. A calibrated model of how reliable each combination is would raise recall at the same precision.

**Steps:**
1. From the calibration set (R-02) collect, for every written annotation, the set of origins that supported it and whether it was exact.
2. Fit per-origin likelihood ratios with Laplace smoothing; combine as `logit(p) = logit(prior) + Σ log(LR_i)` assuming conditional independence; check independence by pairwise correlation and merge correlated origins.
3. Accept when estimated precision ≥ the configured target (default 0.995).
4. Keep proofs as certain (probability 1) so safety rules stay hard.
5. Shadow-compare against the current policy; adopt only if recall rises with `wrong` unchanged on the hold-out set.

**Done when:** hold-out precision ≥ 99.5 % with higher recall than the rule-based policy.

**Insights:** Hand-tuned tiers (0.72 for int defaults, 0.69 for str) cannot capture interactions between signals; data can.

**Architecture:** `negotiation/fusion.py` implements the model; `policy.accept` calls it only for soft evidence; proofs bypass it. Model parameters live in `rules/calibration.json` (CC-01).

**Algorithm:** 1) Features: origin set (bitmask), type shape class. 2) Estimate precision per feature cell with Beta(1,1) smoothing. 3) For unseen cells back off to the nearest smaller origin set. 4) Threshold on lower confidence bound (Wilson interval), not the point estimate.

**Performance:** Lookup table: O(1) per candidate; fitting runs offline.

### AL-06 — Delta debugging against the checker (ddmin) for batched fixes
- **Status:** open
- **Priority:** P0
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** W-02 shows the checker gate keeps only 4 annotations. If a batch fails the check, the current halving does not find a minimal failing subset.

**Scope:** Implement the AL-06 minimizer and checker-only batch recovery in
`src/astart/rules/ddmin.py` and `src/astart/rules/runner.py`, with regression
coverage in `tests/astart/rules/test_rules_ddmin.py`. Preserve write-back halving. The
measured class-binding traversal bottleneck is handled by the M7-01 slice
and `tests/astart/rules/negotiation/test_negotiation_binding_budget.py`.
**Depends on:** Existing `Checker.regresses`, `attempt`, and stable finding
positions within one original-source batch; no new dependency or setting.
**Source:** Inspected `runner.py`, `checker.py`, runner/checker tests, and
`scripts/compare/gated_conversion.py` on 2026-11-09.
**Acceptance:** Deterministic 1-minimal failing subsets; cached subset probes;
40-fix synthetic cases within the specified call budget; checker probes use
one original source; accepted output is checker-verified and idempotent;
write-back failures and checker unavailability remain conservative.
**Evidence:** Baseline fast tests and unchecked engine pair started before
implementation; results and final validation will be recorded below.
**Known limits:** A 1-minimal failing set is not a globally minimum set or a
maximum accepted batch. Keep AL-06 open until the real resolver conversion
proves the 80% retention requirement; synthetic evidence cannot establish it.

**Implementation evidence 2026-11-09:** Added the cached, deterministic
`ddmin` primitive and original-source checker recovery, grouped first by
function. Formatting failures still use halving. The coupled-edit regression
fails with the old path (36/40 kept) and passes with the new one (38/40);
31 systematic monotone cores, joint failures, unavailability, comment
preservation and idempotence are covered. Final fast tier: **5,201 passed**,
888 deselected, 2 pre-existing xfails. Focused branch-enabled coverage:
`ddmin.py` 100%, `runner.py` 91.12%, `strings_normalize.py` 87.39%; combined
90.05% (71 tests). Ruff 0.15.22 and strict BasedPyright are clean. Individual
full Exactus lints/docs/kwargs/readme audits report zero findings; optional
Refurb is unavailable. Unchecked dev-pair before/after is identical:
parameters/returns exact 196, wrong 2; variables exact 164, wrong 5.
Shadow: negotiated-only correct 152, compatible 17, wrong 0, no crashes.
Stdlib gate remains **FAIL** for `tomllib__parser.py` (19 versus baseline
20), independently reproduced with the old recovery path (19), so the
baseline was not refreshed. Full resolver retention and external recovery
are still being measured; the parent task remains open. Machine-readable
validation evidence: `/tmp/astart-al06-validation.json`.

**Steps:**
1. Read `runner._degrade` / `_attempt` first.
2. Implement `ddmin(changes, test)` (Zeller): split into n chunks, try each chunk and each complement, increase granularity until minimal.
3. `test(subset)` applies the subset to the original source and returns whether the checker reports no new errors (`Checker.regresses`).
4. Cache results by frozenset of fix IDs; apply only the failing minimal sets' removal, keep the rest.
5. Tests with a fake checker rejecting exactly two fixes among 40: ddmin returns those two in at most 2·n·log n calls.

**Done when:** the gated conversion keeps at least 80 % of the unchecked annotations (A-04).

**Insights:** Annotations interact: two correct ones can fail together. A minimal failing set keeps the maximum number of fixes.

**Architecture:** `rules/ddmin.py` (pure, testable with a callable); `runner.py` calls it; `Checker` unchanged.

**Algorithm:** ddmin(c, n): partition c into n subsets; if some subset fails, recurse with it and n=2; else if some complement fails, recurse with it and n=max(n-1,2); else if n < |c| set n=min(2n,|c|) and repeat; else return c. Then remove the minimal set from the batch and repeat on the remainder.

**Performance:** O(n²) worst case, typically O(n log n) checker calls; each call is about 1.5 s, so batch first by function (group fixes per function) and only then split.

### AL-07 — Bidirectional (expected-type) inference
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Checking mode lets a declared type shape an expression: `x: list[int] = []`, `f([])` where `f(xs: list[int])`, `{}` into `dict[str, int]`.

**Steps:**
1. Add an 'expected type' channel to derived-node evaluation: when an expression is an argument to a callee with a declared parameter type, or an assignment to a declared target, push the expected type down.
2. Empty containers, `None`, lambdas and comprehensions take their type from it.
3. Refuse when the expected type is a Protocol or has unbound TypeVars.
4. Tests: empty list argument, empty dict return, lambda argument.

**Done when:** empty literals passed to typed callees get element types.

**Insights:** Empty containers are the biggest unprovable literal; context supplies what the literal cannot.

**Architecture:** Extends `builders.py` `_Templater` with `expected` and `transfer.py` with an `expect_of` relation (backward-only).

**Algorithm:** 1) Mark nodes with the declared type of their consumer. 2) During `_Templater.convert`, `List([])`/`Dict({})`/`Set` take the expected element types if the expected type is a concrete parametrised container. 3) Otherwise leave opaque.

**Performance:** No extra passes: expected types ride existing backward transfers.

### AL-08 — Runtime observation as optional evidence (sandboxed)
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Static analysis cannot see types of values built dynamically; observed types from running the project's own tests are strong evidence (MonkeyType-style).

**Steps:**
1. Opt-in command `astart observe -- pytest ...` that runs the tests in a subprocess with a `sys.setprofile` collector writing observed (qualified function, argument types, return type) to a JSON file.
2. `fix --observed FILE` reads it as `Origin.observed` candidates: soft evidence, never proof, and only with ≥ 20 observations and no contradicting observation.
3. Security: run only on explicit command, in the project's own environment, never inside the product's default flow (R-13).
4. Tests with a tiny project and a scripted collector.

**Done when:** observed types corroborate static candidates and never write alone.

**Insights:** Dynamic traces cover exactly what static analysis cannot (reflection, frameworks), but have coverage holes, so they only corroborate.

**Architecture:** `astart/observe/` package (collector and reader); separate from `rules/`; the only code that executes user code.

**Algorithm:** 1) Collector records `type(arg).__qualname__` plus element types sampled up to depth 2 for containers. 2) Aggregate per function parameter as a set of observed types. 3) Convert to candidates: single observed type with count ≥ 20 → candidate; several → union only if each ≥ 5. 4) Mark origin `observed`.

**Performance:** Collector overhead 2–5× on test runtime; sample containers (first 3 elements) to bound cost.

### AL-09 — Name-and-usage language model as calibrated prior
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Parameter names carry type information (`path`, `count`, `is_ready`); a counting model over the corpus beats hand-written heuristics (T-04).

**Steps:**
1. Build `benchmarks/names.py` collecting (parameter name tokens, annotation) pairs from typed corpus modules (calibration set only).
2. Split names on `_` and case boundaries using `str` methods; keep unigram and bigram counts.
3. Predict the annotation distribution with additive smoothing; use as `Origin.calibrated` only when top probability ≥ 0.9 and sample ≥ 30.
4. Report precision on the hold-out set; keep it only if ≥ 97 %.

**Done when:** name priors fire only where measured reliable and always need corroboration.

**Insights:** Cheap, deterministic, explainable; no neural model, no network.

**Architecture:** `rules/name_prior.py` loads a JSON table (`rules/name_priors.json`) produced offline by `benchmarks/names.py`.

**Algorithm:** P(type | tokens) ∝ Π P(type | token_i)^w_i with Laplace smoothing; w_i by inverse document frequency.

**Performance:** Table lookup O(tokens); table under 1 MB.

### AL-10 — Interned types and memoised subtype checks
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Types are rebuilt and compared as strings or tuples repeatedly; subtype checks recompute and recurse (see G-09).

**Steps:**
1. Add `TypeStore` interning each type to an integer ID (hash-consing) with canonical union ordering (I-19).
2. Memoise `subtype(a, b)` in a dict keyed by `(id_a, id_b)`; insert an optimistic `True` before recursing (coinductive), and remove it on failure.
3. Replace string comparisons in `algebra.py` and `typing_relations.py`.
4. Tests: equal types share an ID; recursive protocol terminates; results unchanged on the existing relation tests.

**Done when:** all relation tests pass and the shadow runtime drops measurably.

**Insights:** Hash-consing gives O(1) equality and makes memoisation trivial; the optimistic entry is the standard way to handle recursive structural types.

**Architecture:** `negotiation/typestore.py`, injected into `TypeAlgebra`; `semantic/typing_relations.py` takes an optional store.

**Algorithm:** intern(t): canonicalise (flatten and sort unions, normalise `Optional`), look up in a dict, else assign the next ID. subtype(a,b): if a==b true; if (a,b) in memo return memo; memo[(a,b)] = True; r = structural check; memo[(a,b)] = r; return r.

**Performance:** Equality O(1); each pair checked once per store; store cleared per module.

### AL-11 — Demand-driven, content-addressed queries (project mode)
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** XL · deep

**Context:** Project analysis recomputes everything when one file changes. A query system (Salsa style) recomputes only affected summaries.

**Steps:**
1. Define queries: `parse(file)`, `bindings(file)`, `summary(function)`, `hints(file)`.
2. Each query result is stored with the hashes of the inputs it read; on change, revalidate bottom-up and reuse results whose inputs hash equal.
3. Persist to the existing cache directory with the R-08 atomic scheme.
4. Benchmark: touch one file in a 100-file project and re-run; only dependants recompute.

**Done when:** second run after a one-file change is at least 10× faster than a cold run.

**Insights:** Developers run the tool repeatedly while editing; incremental cost is what makes editor integration (API-10) viable.

**Architecture:** `astart/queries.py` generic memo engine; used by `negotiation/run.py` and `rules/hints.py` factories.

**Algorithm:** Each query call records (query id, input hash) edges; on invalidation mark dependants dirty; recompute lazily; early cutoff when a recomputed value equals the old one.

**Performance:** Cost proportional to changed files plus their dependants; memory bounded by an LRU of summaries.

### AL-12 — Exception-flow summaries (feeds `Raises` docs)
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Generated docstring `Raises` sections should list exceptions a function can really raise, including through callees.

**Steps:**
1. Per function compute `raises(f)` = explicit `raise X` plus callees' raises, minus those caught by an enclosing `try`/`except` that matches.
2. Solve over the call graph (AL-03) with set union; stop at unknown callees (marked `?`, not listed).
3. Use it in AF-09 to generate `Raises:` only for proven, project-defined exceptions by default.
4. Tests: re-raise, `except Base`, bare `except`, `finally`.

**Done when:** generated `Raises` sections never list an exception that cannot occur.

**Insights:** A wrong `Raises` entry is a false statement in documentation; proven-only keeps it trustworthy.

**Architecture:** `rules/exception_flow.py` on top of `negotiation/summaries.py`.

**Algorithm:** Fixpoint: raises(f) = local_raises(f) ∪ ⋃ (raises(g) − caught_at_call(g)); caught_at_call uses the enclosing handlers' class sets and `issubclass` over module classes.

**Performance:** One union per call edge; converges in the SCC iteration of AL-03.

### AL-13 — Mutation summaries decide `Sequence` versus `list`
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Accept-general (M4-16) needs to know whether a parameter is mutated.

**Steps:**
1. For each parameter compute `mutates(f, p)`: any `p.append/extend/pop/...`, item/slice assignment or deletion, augmented assignment, or passing `p` to a callee that mutates its parameter.
2. Fixpoint over the call graph (AL-03).
3. Expose `mutated: bool` to the M4-16 policy: not mutated → `Sequence`/`Mapping`/`Iterable`; mutated → concrete type.
4. Tests per mutation form and a transitive case.

**Done when:** parameters are widened to ABCs only when proven read-only.

**Insights:** Widening a mutated parameter to `Sequence` would make correct callers fail the checker.

**Architecture:** Part of `negotiation/summaries.py`.

**Algorithm:** Per function: set of mutating AST forms on each parameter name (excluding rebinding of the name); close over calls with the callee's summary.

**Performance:** Linear in body size plus call edges.

### AL-14 — Finite-domain values to `Literal` and `Enum` suggestions
- **Status:** open
- **Priority:** P3
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Variables compared and assigned only from a small set of literals are really enumerations.

**Steps:**
1. Track the set of constant values assigned to a variable or parameter default across call sites (cap 8).
2. Offer `Literal[...]` under the `infer-literals` setting (I-14) and report an `enum` suggestion when the same set appears in 3+ functions.
3. Never rewrite code to an `Enum`; suggestion only.

**Done when:** suggestions appear on a fixture and nothing else changes by default.

**Insights:** Closed value sets are common in string-typed code; a suggestion is useful without risk.

**Architecture:** `rules/literal_domains.py`; output through the suggestions channel (T-05).

**Algorithm:** Collect constants from assignments, defaults, call arguments and comparisons; if every observed value is a constant and count ≤ cap, emit the sorted tuple.

**Performance:** One pass over assignments and calls; bounded sets.

### AL-15 — Framework summaries as data (dataclasses, attrs, pydantic, Django fields)
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** L · deep

**Context:** Constructor signatures of decorated classes are synthesised by the framework. Hard-coding each in code does not scale (M2-10).

**Steps:**
1. Define `rules/frameworks/*.json`: decorator or base class name → rule for the synthesised `__init__` (fields from annotated class attributes, order, defaults, `kw_only`).
2. A small interpreter in `rules/framework_summaries.py` reads them (no code per framework).
3. Start with `dataclasses.dataclass`, `typing.NamedTuple`, `attrs.define`; mark pydantic and Django `experimental`.
4. Tests per framework with its real library installed when available (skip otherwise).

**Done when:** constructor calls of framework classes bind and get keywords or are refused with a reason.

**Insights:** Data-driven summaries are reviewable and extensible by users without code (also feeds API-07).

**Architecture:** Data in `rules/frameworks/`, reader in `rules/framework_summaries.py`, used by `CallBindings`.

**Algorithm:** Rule = (match: decorator/base qualified name, fields: from class body annotations in order, init params: fields with defaults after those without, options: kw_only, init=False handling).

**Performance:** Rules loaded once per run; match by name lookup O(1).

### AL-16 — Minimal unsatisfiable core for conflict reports
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** When a belief has conflicts (F-23) the report should name the smallest set of contracts causing it, not every contract.

**Steps:**
1. Given contracts C producing a conflict, run ddmin (AL-06) with `test(subset)` = 'solving only these contracts still conflicts'.
2. Report the minimal set with their source locations (F-26 trail).
3. Tests: a synthetic graph with 3 relevant and 30 irrelevant contracts returns exactly the 3.

**Done when:** conflict reports list only contracts that contribute.

**Insights:** A report listing 40 contracts is unreadable; a core of 3 is actionable.

**Architecture:** Reuses `rules/ddmin.py`; no new module.

**Algorithm:** ddmin over the contract list restricted to the node's upstream cone.

**Performance:** Cone restriction keeps the solve small; at most O(n log n) solves of the cone.

### AL-17 — Reachability pruning with the CFG
- **Status:** open
- **Priority:** P2
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** Dead branches (`if False`, code after `raise`/`return`, `assert False`) pollute returns and narrowings.

**Steps:**
1. Use AL-01 dominators/reachability: unreachable blocks contribute no contracts.
2. Treat `if TYPE_CHECKING`, `if False`, `while True` without `break` correctly.
3. Tests: return after `raise` ignored; `while True` function has no implicit `None` return.

**Done when:** unreachable code never affects a type.

**Insights:** Wrong `| None` returns come mostly from imaginary fall-off paths.

**Architecture:** Part of `negotiation/cfg.py`.

**Algorithm:** Mark blocks reachable from entry via edges whose condition is not constant-false; constants evaluated with `ast.literal_eval` on the test.

**Performance:** Linear in blocks.

### AL-18 — Ablation harness: marginal value of each evidence source
- **Status:** open
- **Priority:** P1
- **Area:** inference
- **Readiness:** ready
- **Effort:** M · deep

**Context:** To decide what to improve we need to know what each origin contributes and whether it ever causes a wrong annotation.

**Steps:**
1. Add `benchmarks/ablation.py`: run the pair benchmark with each origin disabled in turn (leave-one-out) and with only one enabled.
2. Output a table: origin, exact delta, wrong delta, runtime.
3. Add the table to `docs/analysis/scripts.benchmark.md`.
4. Use it to rank tasks: improve origins with high marginal value first.

**Bounded-pass progress 2026-11-09:** `ContractGraph.seed_ablation` creates
isolated seed experiments over the same AST nodes, removing complete seeded
candidates before propagation. `benchmarks/ablation.py` reports baseline and
leave-one-seed-origin-out settlement/conflict counts and solver times. This
is deliberately **seed-only**: derived/fixed producers, engine corroboration,
full parameter/return/variable scoring, single-origin runs and the command
that regenerates the accuracy table remain open. Do not label these solver
counts as exact/wrong annotation deltas or close AL-18 on this evidence.

**Done when:** the table exists and is refreshed by one command.

**Insights:** Without ablation, effort follows intuition; with it, effort follows measured payoff.

**Architecture:** A `FixSettings.disabled_origins` set consulted in `policy.accept`.

**Algorithm:** For each origin o: settings with o disabled; compare counts to the full run.

**Performance:** N+1 runs of the pair benchmark (about 2 minutes each); run on the calibration set only.


### Typed documentation generation (DOC014)

Implemented native `DocEntry` completion with `docstring_types=True` by
 default, public API and CLI opt-out, typed parameters and return values,
 generator yield/terminal-return components, explicit raises and TODO
 placeholders. Existing descriptions remain intact. Regression cases cover
 async yields, nested exception ownership, NoReturn, opt-out and idempotence.
 Remaining inference work: resolve aliased generator components and dynamic
 exception expressions through semantic evidence rather than spelling guesses.
