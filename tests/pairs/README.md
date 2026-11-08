# Conversion pairs

Each pair is one module in two forms: fully annotated (`*_typed.py.txt`) and
unannotated (`*_untyped.py.txt`). The goal is that `astart fix` turns the
untyped form into the typed one; `python -m benchmarks.pair` measures how far
it gets.

| Pair | Origin |
| --- | --- |
| `resolver_extended` | `fixtures/test_resolver_inference_merged_{typed,untyped}_extended.py` of the author's `ast_graph_inference_api_v33_oop` project (the author's own files). |

The pair is not a mechanical strip of one into the other: the typed form adds
variable annotations, imports and synthesized helper classes.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`resolver_extended_typed.py.txt`](resolver_extended_typed.py.txt) — Provide resolver extended typed.py txt content.
- [`resolver_extended_untyped.py.txt`](resolver_extended_untyped.py.txt) — Provide resolver extended untyped.py txt content.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
