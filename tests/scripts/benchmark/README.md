# `benchmark/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_activity.py`](test_activity.py) — Heartbeat lifecycle, idle liveness and CPU-default benchmark execution.
- [`test_bench_baseline.py`](test_bench_baseline.py) — The accepted benchmark baseline is well formed and clean.
- [`test_bench_calibrate.py`](test_bench_calibrate.py) — Unit tests for ``scripts.benchmark.calibrate`` split and share math.
- [`test_bench_cli.py`](test_bench_cli.py) — The benchmark harness end to end on a tiny corpus.
- [`test_bench_pair.py`](test_bench_pair.py) — The untyped-to-typed conversion benchmark keeps its accepted baseline.
- [`test_bench_perf.py`](test_bench_perf.py) — The ``perf`` throughput gate: comparison, serialization and CLI wiring.
- [`test_bench_report.py`](test_bench_report.py) — The benchmark report, its JSON form and the regression gate.
- [`test_bench_runner.py`](test_bench_runner.py) — The benchmark runner's per-kind and per-basis attribution (M2-13, F-29).
- [`test_bench_semantic.py`](test_bench_semantic.py) — Semantic-equivalence runs on a synthetic package.
- [`test_bench_targets.py`](test_bench_targets.py) — The accuracy-contract targets: evaluation, collection and table coverage.
- [`test_layout.py`](test_layout.py) — Benchmark ownership, artifact defaults and shared instrumentation.
- [`test_presentation.py`](test_presentation.py) — Readable benchmark reports retain measurements and sensor evidence.
- [`test_sensors.py`](test_sensors.py) — Verify the decorator-based execution sensors.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
