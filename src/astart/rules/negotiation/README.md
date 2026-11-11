# `negotiation/`

Two-way type negotiation over a graph of contracts.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Two-way type negotiation over a graph of contracts.
- [`algebra.py`](algebra.py) — Union and intersection of type annotations written as source text.
- [`beliefs.py`](beliefs.py) — What is currently believed about one node.
- [`builders.py`](builders.py) — Turn a parsed module into a graph of contracts.
- [`containers.py`](containers.py) — Find what is put into a local container that starts out empty.
- [`graph.py`](graph.py) — The graph of contracts between nodes.
- [`model.py`](model.py) — Data model of the contract graph: relations, candidates, contracts.
- [`narrowing.py`](narrowing.py) — Read what tests, patterns and handlers say about names on each arm.
- [`negotiator.py`](negotiator.py) — Propagate candidates through the contract graph until beliefs settle.
- [`policy.py`](policy.py) — When a settled belief is good enough to write as an annotation.
- [`run.py`](run.py) — Negotiate the annotations of a whole module.
- [`supplement.py`](supplement.py) — Negotiated parameter and return annotations for the hint index.
- [`transfer.py`](transfer.py) — How a type changes when it crosses a contract.
- [`variables.py`](variables.py) — Annotations for local variables, settled by negotiation.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
