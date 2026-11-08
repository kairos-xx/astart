# `benchmarks/`

Benchmarks for the annotation fixer.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Benchmarks for the annotation fixer.
- [`__main__.py`](__main__.py) — Command line of the benchmark harness.
- [`baseline.json`](baseline.json) — Provide baseline json content.
- [`baseline_ext.json`](baseline_ext.json) — Provide baseline ext json content.
- [`build_corpus.py`](build_corpus.py) — Build the external annotation-recovery corpus from pinned wheels.
- [`external_corpus.json`](external_corpus.json) — Provide external corpus json content.
- [`pair.py`](pair.py) — Measure how far ``astart fix`` turns an untyped module into its typed twin.
- [`profile_perf.py`](profile_perf.py) — Profile the analysis pipeline on a large synthetic workload.
- [`projects.json`](projects.json) — Provide projects json content.
- [`recovery_report.py`](recovery_report.py) — Print annotation-recovery precision and recall for a set of modules.
- [`report.py`](report.py) — Benchmark report: per-module results, totals, JSON form and the gate.
- [`runner.py`](runner.py) — Run the annotation-recovery benchmark over files and build a report.
- [`semantic.py`](semantic.py) — Semantic-equivalence runs: fixing a package must not change what it does.
- [`shadow.py`](shadow.py) — Compare the negotiator with the hint index on stripped, typed modules.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
