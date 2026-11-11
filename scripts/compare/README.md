# Integrated comparison

Run from the repository root:

```sh
python scripts/compare
python scripts/compare --reuse
```

The equivalent module command is `python -m scripts.compare`. The default
reference is the manually curated `fixtures/typed.py`; the input is
`fixtures/untyped.py`. `--reuse` explicitly reuses the saved conversion output.
Run `python scripts/compare --help` for alternate inputs and settings.

One run produces one report pair:

- [artifacts/results/conversion-report.md](artifacts/results/conversion-report.md)
- [artifacts/results/conversion-report.json](artifacts/results/conversion-report.json)

The saved `result.py` is raw source evidence, not another
report. JSON includes source hashes, annotation and artifact findings,
structured docstring fields, source locations, opacity explanations and an
`agent_summary` suitable for automated handoff. The generated conversion block
in `docs/planning/TODO.md` receives the same annotation and artifact counts. No task
is automatically marked done merely because a count improves.

The package is one in-process pipeline, not a launcher for several comparing
scripts. `ComparisonSession` parses the input, reference and output once each.
Annotation scoring, class/alias/type-parameter comparisons, source locations,
documentation, evidence collection and opacity analysis share those three
native modules and their semantic graphs. A regression rejects whole-module
reparses in reporting helpers. The existing type scorer can parse isolated
annotation expressions; the separate conversion engine retains its own
existing parsing lifecycle.

Comparisons cover parameters, returns, variables, docstring sections, explicit
and inferred legacy aliases, Protocols, ordinary classes, TypeVar, ParamSpec,
TypeVarTuple and native PEP 695 parameters. Class comparison includes bases,
decorators, generic parameters, member signatures and declared fields; method
implementations are not scored for behavioral equivalence. Classes absent
from the input are labeled output-only candidates for synthesis, rather than
claiming unproven creation history. Structural matches and changed prose are
kept separate from semantic annotation accuracy.

Supporting modules live here for maintenance and optional forensic analysis;
they do not generate separate report pairs or repeat conversions during the
integrated run. The former annotated-copy report is retired because the
canonical Markdown/JSON already retain both sides and their source evidence.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Unified source-conversion comparison and evidence reporting.
- [`__main__.py`](__main__.py) — Run all source-conversion comparisons and publish one report pair.
- [`annotated.py`](annotated.py) — Build an annotated copy of a converted module, for line-by-line review.
- [`conversion_report.py`](conversion_report.py) — Convert an untyped module with astart and report how it differs, in meaning.
- [`conversion_structure.py`](conversion_structure.py) — AST-based comparison of generated documentation and declarations.
- [`evidence.py`](evidence.py) — Collect, from an untyped module, the evidence that leads to a type.
- [`gated_conversion.py`](gated_conversion.py) — W-02: why the checker gate keeps only a few resolver-pair annotations.
- [`opacity_report.py`](opacity_report.py) — Explain why nodes of a module stay unknown to the contract negotiator.
- [`pair.py`](pair.py) — Measure how far ``astart fix`` turns an untyped module into its typed twin.
- [`pair_wrong.py`](pair_wrong.py) — List the annotations that contradict (or only narrow) the typed twin.
- [`recovery_report.py`](recovery_report.py) — Print annotation-recovery precision and recall for a set of modules.
- [`report_layout.py`](report_layout.py) — Layout of the conversion report: standard case blocks, groups, hierarchy.
- [`session.py`](session.py) — Own the three shared source trees of one integrated comparison run.

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Provide conversion report json content.

<!-- exactus:inventory:end -->
