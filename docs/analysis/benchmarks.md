# Benchmarks

## Annotation recovery

`astart.rules.recovery` strips the parameter and return annotations from a
well-typed module, runs the guarded fixer, and compares what it wrote with
the original. Run it with

```console
PYTHONPATH=src python scripts/compare/recovery_report.py tests/corpus/base/*.py
```

- **Precision** = recovered annotations equal to the original ÷ annotations
  written (Protocols and type variables the fixer invented are counted
  separately; the external checker judges those).
- **Recall** = recovered annotations ÷ annotations the original had.

### Baseline (2026-11-07, 20 vendored stdlib modules)

| Metric | Value |
| --- | --- |
| Precision | 16 / 16 (100%) |
| Recall | 16 / 144 (11%) |
| Synthesized (Protocol / TypeVar) | ~560 across the corpus |

Only six of the twenty modules carry annotations; `tomllib/_parser.py` holds
116 of the 144. Recall is low by design: methods, containers, `None`-able
parameters and unions are refused until later milestones (see `TODO.md`).

### What the first run found

The first run scored 21 / 22. The wrong hint was `parse_hex_char(src)` →
`Sequence[int]` (truth: `str`). Call-site evidence was accepted from the same
inference engine that proposed the candidate, so it was not independent.
Call-site types now count only when the argument expression's syntax proves
them; precision is 100% on this corpus and locked by
`tests/astart/rules/test_rules_recovery.py`.

### External corpus (2026-11-08)

`tests/corpus/extended` (165 modules, ~101k lines, 25 pinned permissively licensed
libraries that are already fully annotated; see its README). The harness
strips every annotation, fixes, and scores against the original. Each
mismatch is classified by `recovery.relation`:

* **correct** — the same annotation;
* **narrower** / **looser** — a subtype / supertype of the original
  (`str` for `str | None`, `bool | None` for `None`, `int` for `float`,
  `NoReturn` for `None`); not a contradiction, reported separately;
* **unresolved** — the original names an alias imported from another module
  that cannot be judged from the file alone;
* **wrong** — contradicts the original; this is what the precision gate
  counts.

Run with `python -m scripts.benchmark recovery --corpus tests/corpus/extended
--checker-delta --checker-gate --jobs 14 --json report.json`.

### Accepted baselines (2026-11-08)

| Corpus | Modules | Correct | Wrong | Compatible | Precision | Recall | New checker errors | Crashes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stdlib (`scripts/benchmark/artifacts/resources/baseline.json`) | 128 | 42 / 324 | 0 | 0 | 100 % | 13.0 % | 0 | 0 |
| external (`scripts/benchmark/artifacts/resources/baseline_ext.json`) | 165 | 2 511 / 12 789 | 6 | 136 | 99.77 % | 19.6 % | 0 | 0 |

The external row went 90.5 % → 99.64 % precision (264 → 10 mismatches) by
fixing the `args=*args` keywordizer bug, in-module `NoReturn` propagation,
abstract `NotImplementedError` hooks, and by scoring compatible differences
separately (`recovery.relation`); it then gained 101 correct annotations
(+0.8 points of recall) from the calibrated `bool` return rule, which was
chosen by measuring every refused engine candidate against the originals
(see TODO X-05).

**Provenance (R-24):** every `recovery --json` report now stores
`summary.tree_hash` — a SHA-256 digest of the `src/astart` tree, stable
across commits — and `summary.corpus`. `benchmarks gate` refuses to print
PASS when the report's stamp differs from the current tree (exit 1,
`FAIL stale report`), so a number can never be quoted against the wrong
code. `benchmarks targets` appends `tree <hash> · corpus <set> · <date>`
to every verdict row. The two accepted baselines above predate stamping
(`tree_hash` empty) and are exempt until re-accepted.

### Remaining external-corpus contradictions (X-02, 2026-11-09)

`scripts/benchmark/artifacts/resources/baseline_ext.json` stores 6 `wrong` annotations out of 12 789
originals (precision 99.77 %, gate ≥ 99.5 %, 0 crashes). Each is classified
below; none is a scorer artefact — all are inference limitations or
Self-spelling variants tracked by other tasks:

| Module | Annotation | Wrote | Original | Class |
| --- | --- | --- | --- | --- |
| `anyio___backends___trio` | `_SignalReceiver.__aiter__->` | `_Self` | `_SignalReceiver` | Self-spelling variant (X-03) |
| `fastapi__datastructures` | `UploadFile.__get_pydantic_json_schema__->` | `dict[str, str]` | `dict[str, Any]` | Dict literal narrows the value type to `str`; the declared contract `Any` is invisible once annotations are stripped |
| `filelock___strict` | `_describe_soft_marker->` | `tuple[str, str]` | `tuple[_OccupantState, str]` | `_OccupantState` is a `Literal[...]` alias; returned literals collapse to `str` |
| `pluggy___result` | `Result.from_call->` | `Self` | `Result[ResultType]` | Bare `Self` loses the generic parameter (X-03) |
| `pytest___capture` | `DontReadFromInput.__iter__->` | `Self` | `Iterator[str]` | `return self` collapses to `Self`; the declared `Iterator[str]` contract is not reconstructed |
| `pytest___capture` | `DontReadFromInput.buffer->` | `Self` | `BinaryIO` | Same `return self` → `Self` shortcut on a property whose author annotated the wider `BinaryIO` (with `type: ignore`) |

The last three share one root cause — `return self` is typed `Self` without
checking whether a wider declared contract exists — and the first two are
Self/generic spelling issues owned by X-03. Re-run the gate with
`python -m scripts.benchmark gate --report <new.json> --baseline
scripts/benchmark/artifacts/resources/baseline_ext.json`.

### Per-kind and per-origin metrics (2026-11-09, M2-13 / F-29)

`benchmarks/runner.py` now classifies every written or missed annotation by
*kind* (the owning function's `in_class` flag — `method` when the path is
class-owned, else `function`) and by *basis* (the `HintBasis` behind the
written annotation, resolved index → negotiated → engine). Both are in the
JSON summary (`by_kind`, `by_basis`) and per module, and old reports without
them still load. The `gate` additionally enforces
`method_recall >= 3 × baseline` and `method_precision >= baseline − 0.001`
once the stored baseline carries `by_kind`.

External corpus (`tests/corpus/extended`, 165 modules, negotiation on):

| Kind | Truth | Correct | Wrong | Compatible | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| function | 3 500 | 740 | 4 | 24 | 99.48 % | 21.14 % |
| method | 9 289 | 2 127 | 7 | 119 | 99.69 % | 22.90 % |

Per-origin written-annotation counts (`by_basis`): proven_none 1 402,
default_literal 388, synthesized 332, syntax_proven 297, protocol_result
193, unattributed 192, negotiated 137, calibrated_candidate 101, call_sites
80, derived_return 6, optional_default 2.

The run scored 2 581 / 12 789 correct (recall 20.18 %, +0.55 pts over the
accepted baseline), 11 wrong, precision 99.60 %, 0 crashes, 0 new checker
errors — `gate` prints PASS. It was **not** accepted as a new baseline:
F-29 requires a ≥ +2-point recall gain over 19.3 % and the +5 new wrong
annotations (negotiation, see `docs/analysis/contradictions.md`) argue against
refreshing while the scorer work lands.

**Literal-default policy (2026-11-08, X-01).** A literal default is only as
good as its measured exactness against 165 typed libraries: `bool` 95 %,
`float` 100 %, `int` 73 %, `str` 69 %, `bytes` 14 %. Annotations taken from
a default alone now carry that confidence (`confidence.Constants.by_literal`)
and `astart fix` skips anything below 0.8 by default, so `int`/`str`
defaults are written only with independent evidence (in-module call sites
that all agree) or with `--min-confidence 0`. Effect on the external corpus:
narrower parameter annotations 74 → 21, precision 99.65 → 99.69 %, recall
20.8 → 19.3 % (the 201 held-back annotations, about 30 % of which would have
rejected valid callers). The baselines above were refreshed for this change.

### Accepted gated baseline (2026-11-07)

Stored in `scripts/benchmark/artifacts/resources/baseline.json`; produced with
`python -m scripts.benchmark recovery --checker-delta --checker-gate --delta-limit 25`
and accepted with `python -m scripts.benchmark baseline --report <file>`.

| Measure | Value |
| --- | --- |
| Modules | 113, 0 crashes |
| Precision (correct / judged) | 36 / 36 (100%), 0 wrong |
| Recall (correct / stripped annotations) | 36 / 317 (11.4%) |
| New pyright errors (25 annotated modules) | 0 |
| Rounds to fixed point | 1 round: 5 modules, 2: 106, 3: 2 |
| Wall time | 287 s |

Top reasons for the 281 missed annotations: parameter-tainted returns 81,
no inference candidate 58, call sites unknown 55, declaration bodies 31.
The recall gap is evidence-limited (untyped stdlib parameters), which is
what cross-module call sites (M3-03) and typeshed loading (M3-04) address.
Gate the working tree with
`python -m scripts.benchmark gate --report <new.json>`; it fails on any wrong
annotation, new checker error, crash, or recall drop beyond 0.5 points.

### How to refresh the baseline

Run the gated recovery, compare the report with the stored baseline, then
accept it:

```console
PYTHONPATH=src:. python -m scripts.benchmark recovery --checker-delta --checker-gate --delta-limit 25 --json report.json
python -m scripts.benchmark gate --report report.json
python -m scripts.benchmark baseline --report report.json
```

Only accept a baseline with `0 crashes, 0 wrong, 0 new errors` — the same
fields the table above reports: `Modules` (with its crash count),
`Precision (correct / judged)` (with its wrong count) and `New pyright
errors`. `gate` enforces the rule mechanically; `baseline` then stores
`report.json` as `scripts/benchmark/artifacts/resources/baseline.json`.

### 113-module baseline (2026-11-07, audit)

`PYTHONPATH=src python scripts/compare/recovery_report.py tests/corpus/base/*.py`
(guarded ceiling, checker off, no formatter):

| Metric | Value |
| --- | --- |
| Modules | 113 (111 scored, 2 crashed) |
| Annotations in the originals | 317 |
| Recovered and equal to the original | 27 (recall 8.5%) |
| Written and different from the original | 1 (precision 27 / 28 = 96.4%) |
| Total time | 80.7 s; slowest module `configparser` 5.7 s |

Annotated modules: `tomllib._parser` 116, `importlib.metadata.__init__` 69,
`importlib.resources.abc` 26, `importlib.metadata._meta` 21,
`asyncio.timeouts` 19, `statistics` 13, `importlib.resources._common` 12,
`tomllib._re` 11; the rest are unannotated stdlib code, which only contributes
synthesized Protocols/TypeVars (judged by the external checker, not by this
score).

Findings that came out of the run (tracked in `docs/planning/TODO.md`):

- **Wrong annotation:** `asyncio.timeouts.Timeout.__aexit__` was given
  `-> None`; the original is `Optional[bool]`. The body returns nothing, but
  `__aexit__` is a protocol method (M2-14). Precision is therefore below the
  99.5% guarded gate until that is fixed.
- **Crashes:** `_strptime` and `stringprep`, after annotation stripping, raise
  `IndexError` from `graph/conversion/stages.py::_find_opening_paren_pos`
  (M1-16).

## Planned

Checker delta, throughput by size bucket, semantic-equivalence runs.

## Gold set and corpus (M1)

The replay corpus grew from 20 to **113** vendored modules and the gold
set from 34 to **530** cases (`tests/astart/rules/test_gold_expansion.py`), generated
in families — parameters, returns, defaults, call sites, conversions,
unions, escapes, provable-None, stale-doc and refused cases — each
grounded in typed code, not current tool output. All 530 pass.

## Runtime performance (M7-PERF)

Synthetic 12,000-line module, `astart` check + fix, before → after the
analyzer optimization (`semantic/analyzer.py` internal solver path that
avoids re-fingerprinting the whole tree on every query):

| Phase | Before | After refresh fix | After M8-19/20 + concurrent work |
| --- | --- | --- | --- |
| `check` | ~62–88 s | 40 s | **29.7 s** |
| `fix` | ~194 s | 104 s | **72.3 s** |
| total | ~283 s | 144 s | **102.0 s** |

Root cause of the first cut: `Analyzer.refresh()` re-fingerprinted the
entire tree on *every* query (~1,053 whole-tree walks, ~45 s of
fingerprinting at 12k). Internal query methods now use a refresh-free
solver path; the public `types` contract (reconcile once, then query)
is unchanged. Semantic tests stay green and finding counts are identical
(2,067 findings; applied count varies 413–432 with concurrent rule work).

**The < 5 s target is still not met.** A fresh 3k-line `cProfile` shows
the remaining cost is diffuse AST traversal across the rule engine's
fact computation (`hints.index` ≈ 17.6 s cumulative), `provable.scope_types`
(1,240 calls ≈ 7.4 s), `resolve.get` (1,755 calls ≈ 6.6 s), ~12M
`iter_child_nodes` walks, and ~96 whole-tree fingerprints ≈ 4.7 s —
all in `rules/hints.py`, `rules/provable.py`, `rules/resolve.py`,
`rules/engine.py` and `ast.py`'s `semantic` property. The semantic
solver itself is no longer a hotspot.

### Throughput by size bucket (M1-10)

`benchmarks/profile_perf.py --lines N --json` on the concatenated-corpus
workload (line counts are approximate — whole modules are appended):

| Lines | `check` | `fix` | Total |
| --- | --- | --- | --- |
| ~1.2k | 0.75 s | 1.01 s | 1.76 s |
| ~2.2k | 2.10 s | 2.45 s | 4.55 s |
| ~12k | 29.7 s | 72.3 s | 102.0 s |
| ~12k (2026-11-08, after token-index and scope-env fixes) | 21.4 s | 36.9 s | 58.3 s |
| ~50k | > 30 min | — | infeasible in practice |

**Superlinear growth is flagged**: `check` scales worse than linearly
(1.2k→0.75 s, 2.2k→2.1 s, 12k→30 s — roughly quadratic in this range),
and the ~50k bucket is far worse still: `check` alone exceeded 30 minutes
on the 50,763-line workload (> 85× the 12k `check` for 4.2× the lines),
so `fix` — up to `max_rounds=3` passes each containing a `check` plus
`module_facts`/hint-index work, with `_degrade` halving re-running
`_attempt`/`_rematch` per split — pushes the full `profile_perf` run into
multi-hour territory. Two earlier attempts were interrupted after ~9 h of
CPU each; a 2026-11-08 run was still in `fix` after ~2 h. `cProfile` on
`check` shows the dominant cost is `hints.index → _candidates →
CommentedModule.convert → semantic/analyzer.convert →
graph/conversion → backend/checkpoint._infer` (~135 s+ cumulative inside
a single 200 s window, ~975 M calls), i.e. the whole-module graph
conversion invoked once per hint-index build.

### `fix_source` throughput gate (M1-10)

`python -m scripts.benchmark perf` (implementation: `benchmarks/throughput.py`)
synthesizes an annotated module per size bucket, strips it, times
`fix_source` three times and records the median of the actual line count.
`scripts/benchmark/artifacts/resources/baseline_perf.json` stores the accepted medians; `perf` fails
when a bucket regresses more than 20 %. First numbers (2026-11-09,
Python 3.13.9, median of 3):

| Target lines | Actual lines | Median `fix_source` |
| ---: | ---: | ---: |
| 1 000 | 1 184 | 2.45 s |
| 4 000 | 4 106 | 16.87 s |
| 12 000 | 11 983 | 126.92 s |

The curve is superlinear (4× the lines costs ~7× the time), consistent
with the `profile_perf` profile above; the A-11 bound of 5 s per 12k
lines is not met and stays open.

## Negotiation shadow run (2026-11-08)

`python -m scripts.benchmark.shadow tests/corpus/extended --jobs 8 --json out.json`
strips the annotations from every external-corpus module and runs both the
hint index and the contract negotiator (`astart.rules.negotiation`) on the
same text, scoring each written annotation against the original. Nothing is
written back; this is the F-19 measurement that gates replacing the
propagation loop (F-20). The JSON also lists, per hint basis, what the hint
index writes and the negotiator does not.

| Group (12 789 original annotations, 0 crashes) | Correct | Compatible | Wrong |
| --- | ---: | ---: | ---: |
| Written by both, identical text | 2 400 | 185 | 2 |
| Negotiation only | 41 | 7 | 0 |
| Hint index only | 76 | 11 | 4 |
| Written by both, different text (hint index / negotiation) | 0 / 1 | 1 / 0 | 0 / 0 |

How it got there (hint index only, exact): 338 with the first builders (single
assignments, calls, returns); 76 after containers (F-10), attributes (F-11),
narrowing (F-12), protocol-dunder results (F-35, 193 closed) and calibrated
`bool` returns (F-36, 101 closed). What is left in the hint-index column is
default-literal parameters (70, of which 60 exact and 3 wrong), call-site
hints (10) and syntax-proven returns (8): the hint index accepts a literal
default even when some callers are unknown, the negotiator does not (F-37).

Never contradicted: where both approaches write, the negotiator agrees with
the hint index except one case, which it gets right. Soundness bugs the run
exposed and that are now pinned in `tests/astart/rules/negotiation/test_negotiation_module.py`: stub
and abstract bodies and `__exit__` written as `None`; constructor calls typed
as `__init__`'s return; un-awaited coroutines; a rebound parameter still
feeding later reads; a source node with no evidence letting the one `None`
among several writes settle an attribute.

Eight conflicts are reported over the corpus (a declaration or constraint
that the evidence cannot satisfy); they are candidates for the future
`typing.type-conflict` rule (F-23) and have not been triaged.

## Conversion pairs (2026-11-08)

`python -m scripts.compare.pair UNTYPED TYPED [--no-negotiate]` fixes the untyped
module (variables on, negotiation on) and scores the result against its typed
twin. Pairs: `fixtures/resolver_extended_*` (the author's fixture) and
`fixtures/untyped.py` -> `fixtures/typed_author.py`.

| Pair | Parameters + returns exact | Variables exact | Contradictions |
| --- | ---: | ---: | ---: |
| Resolver, start of day | 71 / 557 | 3 / 329 | 2 |
| Resolver, now | 113 / 557 | 57 / 329 | 2 |
| Dev, start of day | 11 / 482 | 0 / 335 | 2 |
| Dev, now | 52 / 482 | 53 / 335 | 2 |

The two contradictions left are synthesized Protocols judged by the type
checker. A further 13 (dev) and 17 (resolver) are *narrower* than the
author's annotation (`list[int]` where the author wrote `Sequence[int]`);
the scorer now knows the `collections.abc` hierarchy and its variance, and a
name it cannot see through an import or a foreign base is *unresolved*, not
wrong. Three rules produced most of the jump: a *read* of `globals()` no
longer makes every bare-name call untrusted (0 of 152 calls to module
functions bound before, all bound now); negotiated hints supplement the hint
index; and expressions over operands (arithmetic, tuples, comparisons,
f-strings, builtin calls) are typed once their operands settle.

Why the rest is missing (dev pair, the reason each node is opaque):
unprovable calls 46, unknown names 46, functions that escape as values 28,
parameters nobody calls and that have no default 24, stub or abstract bodies
20, calls the binder refuses 16, tuples 14, generators 7; for variables,
unprovable calls 87 and container literals that are mutated or built by a
comprehension 44. These are the tasks F-40, F-41, F-15 and M4-06.

## Negotiation as the default (2026-11-08)

`FixSettings.negotiate` is on (`--no-negotiate` turns it off). Gates with it
on: gold fix-level 561 cases, negotiation changes 0 written annotations and
adds 24 reviewed ones; 15 of 15 semantic-equivalence projects import and run
identically after `fix` (five of them were checked from throwaway installs
of the pinned versions because they are not installed here); stdlib baseline
37 -> 42 correct, 0 wrong; external baseline 2 462 -> 2 511 correct and 8 -> 6
wrong (both baselines were refreshed with negotiation on; an earlier run that
reached 2 531 correct was rejected: it carried 6 new contradictions, generic
classes named bare, and failed the 99.5 % precision gate). The
semantic run caught two bugs before they shipped, both now regression tests:
`-> URIBuilder` inside `class URIBuilder` (a signature annotation is
evaluated when its `def` runs, so it may only name module classes defined
before it and not the class it sits in), and a junk `from uuid import UUID
as _UUID` inside `uuid.py` (a negotiated annotation naming the module's own
class must not be imported over).
