# `scripts/benchmark/`

Benchmarks for the annotation fixer.

## Reports and sensor evidence

Run `python -m scripts.benchmark recovery --limit 1` for a small recovery run.
Every recovery, semantic, throughput, gate, targets, and profile report writes
matching Markdown and JSON files. Recovery keeps its existing JSON stdout
contract; `--json PATH` places both files beside that explicit destination.

- `artifacts/results/`: generated report pairs, sensor dumps, profiling output.
- `artifacts/resources/`: corpus/project manifests, targets and accepted baselines.

Benchmark commands enable sensors by default. Use `ASTART_SENSORS=0` to measure
without instrumentation overhead. Timings collected with sensors enabled
include instrumentation overhead and should only be compared with similarly
instrumented runs. JSON includes all sensor statistics and the complete call
tree; Markdown shows the 25 largest inclusive timings and a bounded call tree.
Nested inclusive times overlap. Parent and worker sensor statistics are merged;
worker call trees remain separated by module. Parallel totals can exceed elapsed
wall time. Existing accuracy
fields remain at their original JSON paths for baseline and target consumers.
Each CLI invocation resets the recorder to avoid leaking earlier measurements.

Recovery defaults to the available CPU count (`os.process_cpu_count()`), with
`--jobs N` overriding it; `--jobs 1` runs serially. Results retain input order
regardless of worker completion order. Worker processes do not write shared
sensor files; the parent merges their measurements and publishes the reports.

`artifacts/results/@activity.json` updates atomically every second, even while
a module is still processing. It records PID, run identity, UTC timestamps,
elapsed time, configured jobs, completed/total modules, current module and
final lifecycle status. A stopped heartbeat indicates a stale run after a
hard kill; `alive` describes the state at the last recorded beat. Normal exit,
failures and keyboard interruption close the heartbeat thread and record the
final state. Each new command replaces the activity document for the latest run.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Benchmarks for the annotation fixer.
- [`__main__.py`](__main__.py) — Run the integrated benchmark harness: ``python -m scripts.benchmark``.
- [`ablation.py`](ablation.py) — Measure seed-origin sensitivity without reparsing or editing source.
- [`activity.py`](activity.py) — Atomic benchmark activity snapshots with an independent live heartbeat.
- [`build_corpus.py`](build_corpus.py) — Build the external annotation-recovery corpus from pinned wheels.
- [`calibrate.py`](calibrate.py) — Cross-validate per-basis confidence on two corpus halves (I-20).
- [`cli.py`](cli.py) — Command line of the benchmark harness.
- [`paths.py`](paths.py) — Canonical benchmark input and output locations.
- [`presentation.py`](presentation.py) — Publish benchmark measurements and live sensor evidence together.
- [`profile_perf.py`](profile_perf.py) — Profile the analysis pipeline on a large synthetic workload.
- [`report.py`](report.py) — Benchmark report: per-module results, totals, JSON form and the gate.
- [`runner.py`](runner.py) — Run the annotation-recovery benchmark over files and build a report.
- [`semantic.py`](semantic.py) — Semantic-equivalence runs: fixing a package must not change what it does.
- [`sensors.py`](sensors.py) — Benchmark profiling over the same recorder used by the installed CLI.
- [`shadow.py`](shadow.py) — Compare the negotiator with the hint index on stripped, typed modules.
- [`targets.py`](targets.py) — Machine-checkable accuracy contract: targets A-01 to A-11 (task G-01).
- [`throughput.py`](throughput.py) — Measure ``fix_source`` throughput across workload size buckets.
- [`treehash.py`](treehash.py) — Commit-independent hash of the ``astart`` source tree (task R-24).

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Accepted baselines are inputs. Report generation never replaces them unless an explicit baseline acceptance or update command is used.

<!-- exactus:inventory:end -->

`ablation.measure_seed_origins(graph=...)` measures isolated solver runs
with all seeds and each seed origin excluded in turn. It reuses the existing
AST and does not mutate the input graph. These are seed-sensitivity counts,
not full annotation-accuracy ablations: derived/fixed producers and the
engine corroboration channel still require AL-18 instrumentation.
