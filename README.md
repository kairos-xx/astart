# astart

`astart` is a single Python 3.13+ package for mutable Python ASTs, complete
lexical token snapshots, loss-aware source rewriting, and dependency-driven
static type and value inference. It has no third-party runtime dependencies.
[`docs/architecture/architecture.md`](docs/architecture/architecture.md) maps every module under
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
from astart.stubs import bundled_typeshed

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

# Opt-in conversion uses the same original mutable AST and the bundled
# typeshed snapshot; an explicit typeshed root overrides it.
module.configure_graph(stubs_path=bundled_typeshed())
# module.convert(apply=True)

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

`module.convert(apply=False)` returns graph proposals and
stage diagnostics without modifying the AST; `apply=True` applies supported
annotation updates in place. Both default to the typeshed snapshot bundled
inside the package — pass `stubs_path` or set `ASTART_TYPESHED` to use a
different root. `module.configure_graph(stubs_path=...)` enables
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
astart check src/ [--format text|json|sarif|junit|github] \
    [--fail-on error|warning|info]
astart fix src/ [--safe-only] [--diff | --check] [--no-format] \
    [--checker auto|off] [--min-confidence 0.95] [--source-root DIR ...] \
    [--create-constants-class] [--stub-docstrings] [--project] \
    [--annotate-variables] [--engine] [--no-negotiate] [--closed-world] [--target-version VER] [--cache] \
    [--exclude GLOB ...] [--no-docs] [--runtime-protocols] [--accept-general] \
    [--protocol-placement module|function|type-checking] [--backup]
```

The `--format json` report is an array with one entry per file; its shape is
described by the JSON Schemas in [`docs/schema/`](docs/schema/report.json)
(`report.json` for the document, `finding.json` for each finding).
`--format sarif` emits a SARIF 2.1.0 document, `--format junit` a JUnit XML
document, and `--format github` GitHub Actions workflow-command lines.
`--write-baseline FILE` records the current findings and `--baseline FILE`
suppresses them on later runs, so only new findings change the exit status.

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
Parameter and whitespace docstring repairs use Google-style triple quotes:
missing parameters get a stub entry, entries for parameters that no longer exist are
removed, and trailing space, blank-line runs and misaligned lines are tidied.
Generator documentation is repaired across Google, NumPy, reStructuredText
and Epytext styles. `DOC004` adds `Yields: TODO.` (or the matching directive),
keeps terminal return values separate, and preserves existing descriptions.
Nested generator bodies do not turn their enclosing functions into generators.
Mixed documentation styles are diagnosed without implicit conversion.

`--stub-docstrings` goes further and adds a stub docstring to undocumented
public definitions, and `--no-docs` skips every `docs.*` fix for typing-only
runs. `--annotate-variables` annotates function-local variables whose type
the evidence proves (`count: int = 0`, `h: int = helper()`); modules that
already annotate some locals get the rest without the flag. The contract negotiator
(see `docs/analysis/scripts.benchmark.md`) adds parameter and return annotations the hint
index has no hint for; `--no-negotiate` turns it off. `--engine` is the conversion mode: it also
takes the annotations of the inference engine (the descendant of the author's
earlier converter) for everything the evidence-based pipeline left undecided,
at confidence 0.55 (the default floor drops to 0.5 with it); the type checker
gate still vetoes any of them that introduces an error, so use it with a
checker installed. `--exclude` skips discovery paths matching a glob (repeatable, on both
`check` and `fix`). `--project` analyses the discovered files as one project
so cross-module evidence can feed the hints; `--closed-world` then assumes
all callers are inside that file set. `--target-version` sets the oldest
Python version the emitted code must run on. Parameters used only
structurally get a synthesized `Protocol` (or a reused standard one);
`--accept-general` prefers abstract collection spellings for read-only
container parameters, `--protocol-placement` chooses where the class
lands (`module`, `function` or `type-checking`), and
`--runtime-protocols` emits `@runtime_checkable` when the protocol is
used under `isinstance`.
Exit status: `0` clean, `1` findings or changes, `2`
unreadable input or a missing path. Pre-commit hooks and CI examples live
in [`docs/engineering/ci.md`](docs/engineering/ci.md).

```console
python -m astart convert --source example.py \
  --output example.annotated.py --report inference.json
```

`convert` reads the typeshed snapshot bundled inside the package;
`--stubs PATH` (or `ASTART_TYPESHED`) overrides it.

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
- `--project` analyses discovered files as one project so cross-module call
  sites count as evidence, and `astart.stubs` resolves signatures against
  the bundled typeshed snapshot — both are opt-in and closed-world
  assumptions still apply;
- Protocol and `TypeVar` synthesis covers common shapes only;
- keyword fixes for constructors, overrides and callbacks are partial;
- `fix --cache` reuses results for unchanged files, but there is no
  parallelism yet.

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

Commits are one finished slice each (a milestone step, a rule, a fixture
batch), with the suite and `ruff check src tests benchmarks scripts` green
before each commit. Never commit generated output: `__pycache__/`,
`.coverage`, `.ruff_cache/`, `.pytest_cache/`, `EXACTUS_RESULTS/`,
`.remember/`, `.history/` and `dist/` stay untracked —
`tests/astart/test_repo_hygiene.py` enforces this. Agent-authored commits carry
the agent's standard attribution trailer, for example:

```text
Generated with [Devin](https://devin.ai)

Co-Authored-By: Devin <158243242+devin-ai-integration[bot]@users.noreply.github.com>
```

Optional external tools — none are required to install or run the fast
test tier (`pytest -m "not slow"` passes with only `astart` + `pytest`
present):

- `ruff` — source-format normalization inside graph conversion degrades
  to a no-op when absent; it is also the lint/format gate for development.
- `basedpyright`, `pyright` or `mypy` — consulted only by the opt-in
  checker gates (`fix` guarded-fix validation when a checker is
  configured, `benchmarks pair --checker`, `--checker-delta`,
  `--checker-gate`, `scripts/compare/gated_conversion.py`); every caller skips
  cleanly when no checker is installed.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`AGENTS.md`](AGENTS.md) — Provide AGENTS md content.
- [`CHANGELOG.md`](CHANGELOG.md) — Provide CHANGELOG md content.
- [`LICENSE`](LICENSE) — Provide LICENSE project content.
- [`LICENSES.md`](LICENSES.md) — `astart` itself is MIT licensed (see `LICENSE`). This file records the third-party material the project uses or is inspired by.
- [`MANIFEST.in`](MANIFEST.in) — Provide MANIFEST in content.
- [`astart_ast_dump_delta.zip`](astart_ast_dump_delta.zip) — Provide astart ast dump delta zip content.
- [`pyproject.toml`](pyproject.toml) — Provide pyproject toml content.
- [`uv.lock`](uv.lock) — Provide uv lock content.

### Subdirectories

- [`artifacts/`](artifacts/README.md) — Contain artifacts resources and their directory inventory.
- [`benchmarks/`](benchmarks/README.md) — No direct files besides this README.
- [`dev/`](dev/README.md) — Contain dev resources and their directory inventory.
- [`docs/`](docs/README.md) — Use `from astart import ...` for the supported public API. Internal semantic and graph modules are implementation details.
- [`fixtures/`](fixtures/README.md) — Comparison tools use this single pair. Generated code is written to \[result.py\](../scripts/compare/artifacts/results/result.py), alongside the Markdown and JSON comparison reports; it is not a curated fixture.
- [`scripts/`](scripts/README.md) — Maintenance scripts for astart.
- [`src/`](src/README.md) — Astart: mutable Python AST, preserved source, semantic analysis and typing.
- [`tests/`](tests/README.md) — Tests for source-preserving comment AST nodes and safe AST rewrites.

<!-- exactus:inventory:end -->

### Explicit AST wrapping and insertion

These passes operate on one existing `CommentedModule` and are separate from
annotation conversion. Runtime insertion stays off unless selected:

```sh
astart transform input.py --wrap --line-length 79 --diff
astart transform input.py --replace-print --magic-scope function -o output.py --report changes.json
astart transform input.py --wrap --check
```

With no output option, source is written to stdout. `--diff` and `--check`
never write source; check exits 1 when edits are pending and 0 otherwise.
`--output`, `--diff` and `--check` are mutually exclusive. Explicit output
and JSON report writes are atomic and preserve an existing file's mode.
Source encodings and untouched lexical slices are retained by the native
emitter. `--doc-style`, `--strip-sections`, `--boilerplate`, `--remove-pass`
and `--add-return-none` select additional explicit documentation/AST changes.

The print helper delegates to builtin print, preserves falsey supplied
streams and opens path output in an owned UTF-8 context. Its one protocol
cast expresses builtin print's conditional flushing requirement; it performs
no runtime check or stream substitution. Numeric extraction preserves signed
int/float values, ignores bool/unit sentinels/nonfinite values, and refuses
unsafe class-construction cells. Preservation reasons appear in JSON reports.
The remaining single-AST emission migration is specified in
[the architecture decision](docs/architecture/single-ast-architecture.md) and
[CC-09 through CC-13](docs/planning/TODO.md#cc-09--verify-declared-ast-mutations-before-committing-edits).

Typed documentation is enabled by default with `--docstring-types`; use
`--no-docstring-types` to retain untyped entries. Add `--stub-docstrings` to
create missing public docstrings. The Python API exposes the same preference
as `Settings(docstring_types=True)`.
