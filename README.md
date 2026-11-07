# astart

`astart` is a single Python 3.13+ package for mutable Python ASTs, complete
lexical token snapshots, loss-aware source rewriting, and dependency-driven
static type and value inference. It has no third-party runtime dependencies.

## Installation

```console
python -m pip install astart
```

The package is ready to build locally; this command obtains a published release
only after you publish the distribution to PyPI.

## Unified Python API

```python
from pathlib import Path
from astart import Module, parse, unparse

source = """#!/usr/bin/env python3
# noqa: E501

def double(value: int) -> int:
    return value * 2
result = double(4)
"""

module: Module = parse(source=source)
assert str(module.infer_type(node="result").inferred) == "int"
assert module.infer(node="result").value == 8

# Every native AST node has immutable lexical snapshots.
function = module.body[0]
assert function.token_info.source_text.startswith("def double")

# One set of semantic interfaces: symbols, contracts, evidence and conversion.
contracts = module.signature(name="double")
call = module.body[1].value
bound = module.bind_call(node=call)
assert bound is not None

# Opt-in conversion uses the same original mutable AST.
module.configure_graph(stubs_path=Path("stubs"))
# module.convert(stubs_path=Path("stubs"), apply=True)

function.body[0].value.right.value = 3
assert module.infer(node="result").value == 12
result_source = unparse(tree=module, preserve_formatting=True)
```

`Module` and `CommentedModule` refer to the same mutable `ast.Module`
subclass. Its `body` and normal executable children remain compatible with
Python's `ast.walk()` and `compile()`.

`parse()`, `unparse()`, `convert()`, `TypeShape`, `TypeInference`,
`TypeEvidence`, `Types`, `TypeExpressionCodec`, `ParameterKind`,
`CallableContract`, `BoundCall` and `DocstringNode` are all accessed through
`astart`. Annotations proposed by the internal graph pipeline are validated
against current declarations and fed into the same semantic type solver.

`module.convert(stubs_path=..., apply=False)` returns graph proposals and
stage diagnostics without modifying the AST; `apply=True` applies supported
annotation updates in place. `module.configure_graph(stubs_path=...)` enables
lazy reanalysis on revisions. `module.graph_document()` exposes the detailed
graph view of current source when needed.

## What is retained

- Python AST editing, immutable token snapshots, selective location updates,
  and source-aware incremental change records.
- Format-preserving source patches, including supported f-string expression
  transformations, quote and trailing comma preservation.
- Semantic shebang, comment, lint-suppression and grouped-comment nodes.
- Structured function/class/module docstrings in Google, NumPy, reST,
  Epytext and PEP 257 styles, with separate summary and description nodes.
- Scope/symbol identity, control-flow worklists, reaching definitions,
  abstract values, heap aliases, forward/backward type constraints, evidence.
- Incremental revision reuse: clean lexical subtrees keep their symbol
  index, unchanged control-flow graphs re-solve only affected blocks, and
  relocated declarations keep symbol lineage through origin identities.
- Typed call binding, overloads, generics, dataclass/enums, structural
  protocols, annotation stubs, and graph-derived type refinement.

## CLI

Report rule violations, or fix them automatically:

```console
astart check src/ [--format text|json] [--fail-on error|warning|info]
astart fix src/ [--safe-only] [--diff | --check] [--no-format]
```

`astart fix` adds missing keyword arguments and type hints by default,
synthesizes `Protocol` classes and `TypeVar` declarations where a parameter's
type is structural or generic, adds the imports they need, and then runs
`ruff format` once. `--safe-only` limits it to provably safe fixes, `--diff`
prints the change instead of writing, and `--check` only reports whether
changes are pending. Exit status: `0` clean, `1` findings or changes, `2`
unreadable input or a missing path.

```console
python -m astart convert --source example.py --stubs stubs/ \
  --output example.annotated.py --report inference.json
```

The CLI uses the same safe AST conversion as `module.convert(..., apply=True)`,
not a second converter that replaces the entire source with an independently
formatted draft. Use `--dry-run` to collect proposals without writing code and
`--strict-formatting` to reject edits that would require canonical
formatting. The CLI permits canonical fallback by default for generated
annotations that cannot be inserted through lexical patches.
PEP 263 source encodings and existing newline sequences are retained.

## Limits

The source editor deliberately rejects transformations that cannot be safely
preserved instead of silently rewriting unrelated code. The static interpreter
never executes analyzed source; unsupported dynamic Python effects remain
conservative. A complete static model of every Python runtime behavior and
full typing-spec conformance is not certified. The internal graph and native
constraint engines share one supported API and are not independently installed.

## Development

```console
python -m pytest -q
python -m pytest -q --cov=astart --cov-branch --cov-report=term-missing
```

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`LICENSE`](LICENSE) — Provide LICENSE project content.
- [`MANIFEST.in`](MANIFEST.in) — Provide MANIFEST in content.
- [`pyproject.toml`](pyproject.toml) — Provide pyproject toml content.

### Subdirectories

- [`docs/`](docs/README.md) — Use `from astart import ...`. The `astart.semantic` and `astart._graph` trees are implementation modules; the latter is not a separate distribution.
- [`src/`](src/README.md) — Astart: mutable Python AST, preserved source, semantic analysis and typing.
- [`tests/`](tests/README.md) — Tests for source-preserving comment AST nodes and safe AST rewrites.

<!-- exactus:inventory:end -->
