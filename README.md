# astart

`astart` is a single Python 3.13+ package for mutable Python ASTs, complete
lexical token snapshots, loss-aware source rewriting, and dependency-driven
static type and value inference. It has no third-party runtime dependencies.
[`docs/architecture.md`](docs/architecture.md) maps every module under
`src/astart/rules/` to its documented role.

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
astart fix src/ [--safe-only] [--diff | --check] [--no-format] \
    [--checker auto|off] [--min-confidence 0.95] [--source-root DIR ...] \
    [--create-constants-class] [--stub-docstrings] [--project] \
    [--annotate-variables] [--engine] [--no-negotiate] [--closed-world] [--target-version VER] [--cache] \
    [--exclude GLOB ...] [--no-docs]
```

`astart fix` adds missing keyword arguments and type hints by default,
synthesizes `Protocol` classes and `TypeVar` declarations where a parameter's
type is structural or generic, adds the imports they need, and then runs
`ruff format` once. `--safe-only` limits it to provably safe fixes, `--diff`
prints the change instead of writing, and `--check` only reports whether
changes are pending. With `--checker auto` (the default) an installed
`basedpyright`/`pyright` must not report a new error for guarded fixes; a
rejected fix is skipped with the code `checker-rejected`. The checker runs
on a scratch copy in a temp directory; imports resolve as for the real file
(its package, a `src/` layout, the project root and `PYTHONPATH` are detected,
and `--source-root` adds more). `--min-confidence`
drops fixes whose evidence is weaker than the given confidence. 
Docstrings are healed too (Google style, triple-quoted only): missing
parameters get a stub entry, entries for parameters that no longer exist are
removed, and trailing space, blank-line runs and misaligned lines are tidied.
`--stub-docstrings` goes further and adds a stub docstring to undocumented
public definitions, and `--no-docs` skips every `docs.*` fix for typing-only
runs. `--annotate-variables` annotates function-local variables whose type
the evidence proves (`count: int = 0`, `h: int = helper()`); modules that
already annotate some locals get the rest without the flag. The contract negotiator
(see `docs/benchmarks.md`) adds parameter and return annotations the hint
index has no hint for; `--no-negotiate` turns it off. `--engine` is the conversion mode: it also
takes the annotations of the inference engine (the descendant of the author's
earlier converter) for everything the evidence-based pipeline left undecided,
at confidence 0.55 (the default floor drops to 0.5 with it); the type checker
gate still vetoes any of them that introduces an error, so use it with a
checker installed. `--exclude` skips discovery paths matching a glob (repeatable, on both
`check` and `fix`). `--project` analyses the discovered files as one project
so cross-module evidence can feed the hints; `--closed-world` then assumes
all callers are inside that file set. `--target-version` sets the oldest
Python version the emitted code must run on.
Exit status: `0` clean, `1` findings or changes, `2`
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

- recall is low where callers are not visible (about 11% on the
  stripped-annotation benchmark) and precision is the priority;
- cross-module call sites and typeshed stubs are not used yet;
- Protocol and `TypeVar` synthesis covers common shapes only;
- keyword fixes for constructors, overrides and callbacks are partial;
- large files are slow (no cache or parallelism yet).

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

- [`AGENTS.md`](AGENTS.md) — Provide AGENTS md content.
- [`CHANGELOG.md`](CHANGELOG.md) — Provide CHANGELOG md content.
- [`LICENSE`](LICENSE) — Provide LICENSE project content.
- [`MANIFEST.in`](MANIFEST.in) — Provide MANIFEST in content.
- [`pyproject.toml`](pyproject.toml) — Provide pyproject toml content.

### Subdirectories

- [`benchmarks/`](benchmarks/README.md) — Benchmarks for the annotation fixer.
- [`dev/`](dev/README.md) — Contain dev resources and their directory inventory.
- [`docs/`](docs/README.md) — Use `from astart import ...`. The `astart.semantic` and `astart._graph` trees are implementation modules; the latter is not a separate distribution.
- [`scripts/`](scripts/README.md) — Maintenance scripts for astart.
- [`src/`](src/README.md) — Astart: mutable Python AST, preserved source, semantic analysis and typing.
- [`tests/`](tests/README.md) — Tests for source-preserving comment AST nodes and safe AST rewrites.

<!-- exactus:inventory:end -->
