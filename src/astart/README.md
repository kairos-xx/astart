# `astart/`

Astart: mutable Python AST, preserved source, semantic analysis and typing.

## Implementation packages

| Package | Ownership |
| --- | --- |
| [docstrings](docstrings/README.md) | Documentation AST, parsing, generation, rules, layout and prose wrapping. |
| [source](source/README.md) | Authoritative module, lexical tokens, comments, transactions and format preservation. |
| [transforms](transforms/README.md) | Native alias extraction, insertion and constant transformations. |
| [semantic](semantic/README.md) | Symbols, shared graph, abstract values and inference. |
| [rules](rules/README.md) | Generic catalog, facts, checking and fix execution. |
| [project](project/README.md) | Project and library indexing. |
| [stubs](stubs/README.md) | Static stub resolution. |
| [cli](cli/README.md) | Command-line configuration and execution. |
| [graph](graph/README.md) | Internal graph conversion backend. |

The root package retains the supported public API, settings, file APIs and
entry point. Implementation imports use their owning package; no duplicate
flat implementation modules are retained.


## Native AST wrapping

`astart.docstrings.wrapping.wrap_tree(tree=module, settings=WrapSettings(...))` mutates
an existing `CommentedModule`. It edits semantic doc children, comment nodes,
optional boilerplate/pass nodes and proven `None` return annotations. It
never reparses or emits the module. Call the existing `module.unparse` when
ready to emit; `wrap_source` is only a convenience adapter.

`module.token_snapshots(nodes=...)` reconciles once for a whole read batch.
Lexical delimiter partners and parenthesized ranges are available through
`SourceTokenizer`; parenthesized ranges alone do not imply redundancy.
See [the migration decision](../../docs/architecture/single-ast-architecture.md) for the
remaining emission and incremental invalidation work.

`astart.transforms.insertion.insert_tree(tree=module, settings=InsertSettings(...))`
constructs native AST nodes for opt-in print helpers and comparison constants.
Print names resolve through the existing lexical scope graph; shadowed and
wildcard-ambiguous calls stay unchanged. Module/function/class extraction
uses typed constants and refuses unsafe class-construction cells. Both
features default off. No legacy project or pyposast dependency is imported.

`module.annotation_transaction()` stages fresh `annotation`/`returns` fields.
`replace(owner=..., field=..., value=...)` changes nothing until `commit()`.
`add_import(declaration=ImportFrom(...))` stages an absolute, unaliased,
single-name dependency in the same batch. Existing bindings, executable
reads, builtins and wildcard ambiguity are protected from capture. Commit
guards raw external edits and node/list identities, validates the native AST
without executing it, relinks documentation targets, and rolls back failures
or interruption. Imports preserve the original body list and follow the
module docstring/future/import preamble. It is a single-writer API with O(N)
compatibility checks; catalog-wide contracts and general list edits remain
CC-09 work.

`FormatPreserver.plan(..., revision=...)` now drives lexical emission.
After successful format-preserving emission, `module.emission_plan` exposes
its checked patch/rebase plan without refreshing indexes. A contiguous group
of fresh imports uses local insertion patches, preserving untouched spans.
Changed-node output
locations and removal of full-module parse validation remain CC-10 work.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Astart: mutable Python AST, preserved source, semantic analysis and typing.
- [`__main__.py`](__main__.py) — Single command-line entry point using the astart Python API.
- [`api.py`](api.py) — Public one-call API for checking and fixing Python source (API-02).
- [`files.py`](files.py) — Fix Python files on disk through the public API (API-03).
- [`py.typed`](py.typed) — Provide py typed content.
- [`settings.py`](settings.py) — Public ``Settings`` object shared by the CLI and the API (API-04).

### Subdirectories

- [`cli/`](cli/README.md) — Command-line layer over the rule engine and fix runner.
- [`docstrings/`](docstrings/README.md) — This package owns structured documentation behavior:
- [`graph/`](graph/README.md) — API-first AST graph inference package.
- [`project/`](project/README.md) — Whole-project analysis: imports, call graph, libraries and versions.
- [`rules/`](rules/README.md) — A rule ontology: rules, fixes, profiles and relations as typed, serializable data, plus a small reference engine that evaluates the catalog against Python source parsed once with astart.
- [`semantic/`](semantic/README.md) — Dependency-free semantic graph and safe abstract evaluation for Python ASTs.
- [`source/`](source/README.md) — The source package owns the authoritative extended AST and lexical state:
- [`stubs/`](stubs/README.md) — Read typeshed-style stubs: locate, parse and resolve names.
- [`transforms/`](transforms/README.md) — Documentation wrapping belongs to `astart.docstrings.wrapping`. Source/token ownership belongs to `astart.source`; transformations do not own another parser or semantic graph.

<!-- exactus:inventory:end -->
