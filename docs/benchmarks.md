# Benchmarks

## Annotation recovery

`astart.rules.recovery` strips the parameter and return annotations from a
well-typed module, runs the guarded fixer, and compares what it wrote with
the original. Run it with

```console
PYTHONPATH=src python benchmarks/recovery_report.py tests/corpus/*.py.txt
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
`tests/test_rules_recovery.py`.

### Accepted gated baseline (2026-11-07)

Stored in `benchmarks/baseline.json`; produced with
`python -m benchmarks recovery --checker-delta --checker-gate --delta-limit 25`
and accepted with `python -m benchmarks baseline --report <file>`.

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
`python -m benchmarks gate --report <new.json>`; it fails on any wrong
annotation, new checker error, crash, or recall drop beyond 0.5 points.

### 113-module baseline (2026-11-07, audit)

`PYTHONPATH=src python benchmarks/recovery_report.py tests/corpus/*.py.txt`
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

Findings that came out of the run (tracked in `docs/TODO.md`):

- **Wrong annotation:** `asyncio.timeouts.Timeout.__aexit__` was given
  `-> None`; the original is `Optional[bool]`. The body returns nothing, but
  `__aexit__` is a protocol method (M2-14). Precision is therefore below the
  99.5% guarded gate until that is fixed.
- **Crashes:** `_strptime` and `stringprep`, after annotation stripping, raise
  `IndexError` from `_graph/conversion/stages.py::_find_opening_paren_pos`
  (M1-16).

## Planned

Checker delta, throughput by size bucket, semantic-equivalence runs.

## Gold set and corpus (M1)

The replay corpus grew from 20 to **113** vendored modules and the gold
set from 34 to **530** cases (`tests/test_gold_expansion.py`), generated
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
| ~50k | — | — | pending (run interrupted) |

**Superlinear growth is flagged**: `check` scales worse than linearly
(1.2k→0.75 s, 2.2k→2.1 s, 12k→30 s — roughly quadratic in this range),
consistent with the remaining per-query tree traversals noted above.
The 50k bucket completes the table once the in-flight `_graph`/engine
work lands.
