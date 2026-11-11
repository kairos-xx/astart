# Canonical conversion fixtures

- [untyped.py](untyped.py): conversion input.
- [typed.py](typed.py): manually curated annotation and documentation reference.
- [artifacts/typed_graph.json](artifacts/typed_graph.json): evidence graph for
  the curated reference; its source digest must match `typed.py`.
- [artifacts/accepted_deviations.json](artifacts/accepted_deviations.json):
  reviewed semantic equivalences used by the pair scorer.

Comparison tools use this single pair. Generated code is written to
[result.py](../scripts/compare/artifacts/results/result.py), alongside the
Markdown and JSON comparison reports; it is not a curated fixture.
