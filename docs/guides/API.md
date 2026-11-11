# astart API reference

## One import surface

Use `from astart import ...`. The `astart.semantic` and `astart.graph` trees
are implementation modules; the latter is not a separate distribution.

| Public API | Responsibility |
| --- | --- |
| `parse(source=..., filename=...)` | Creates mutable, comment- and token-aware `Module` |
| `unparse(tree=..., preserve_formatting=True)` | Regenerates source with localized patches when safe |
| `check_source(source=..., filename=..., options=...)` | Checks source against the default rule catalog ([astart.api](../../src/astart/api.py)) |
| `fix_source(source=..., filename=..., settings=...)` | Applies safe fixes with the default catalog and guarded ceiling ([astart.api](../../src/astart/api.py)) |
| `fix_file(path=..., settings=..., write=...)` | Fixes one file on disk with an atomic write ([astart.files](../../src/astart/files.py)) |
| `fix_paths(paths=..., settings=..., write=..., on_file=..., cancel=...)` | Fixes many files, one `FileOutcome` per path, in order; optional per-file callback and cancellation event ([astart.files](../../src/astart/files.py)) |
| `Settings.from_pyproject(path=...)` | Builds fix settings from a pyproject.toml astart table ([astart.settings](../../src/astart/settings.py)) |
| `Settings.to_fix_settings(checker=...)` | Converts Settings to FixSettings, resolving target_version ([astart.settings](../../src/astart/settings.py)) |
| `convert(tree=..., stubs_path=..., apply=False)` | Runs the integrated graph conversion and merges type evidence |
| `Module` / `CommentedModule` | Mutable Python AST retaining custom metadata |
| `module.semantic` | Persistent semantic analysis, scopes, abstract values and dependencies |
| `module.infer(node=...)` | Conservative abstract value of a symbol or expression |
| `module.infer_type(node=...)` | Type conclusion including annotations, conflicts and evidence |
| `module.signature(name=...)` | Callable contracts for known module functions or methods |
| `module.bind_call(node=...)` | All effective arguments by declared parameter name and kind |
| `module.types` | The single native type solver, with graph evidence incorporated |
| `module.typing_diagnostics` | Known typing contract/override problems |
| `module.configure_stubs(root=...)` | Optional lazy `.pyi` lookup |
| `module.configure_graph(stubs_path=...)` | Optional lazy graph-based type refinement |
| `module.convert(stubs_path=..., apply=...)` | Propose or apply verified annotation edits |
| `module.graph_document(filename=...)` | Inspect current graph representation when needed |
| `module.token_stream` | Complete tokenizer sequence |
| `node.token_info` | Frozen snapshot with UTF-8 locations, tokens and source revision |
| `module.token_changes` | Identity-aware change and invalidation records |
| `module.docstrings` | Structured docstring nodes, including summaries/descriptions |
| `module.comments` | Semantic comment nodes, lint directives and shebang metadata |
| `module.semantic.symbols` | Persistent symbol registry: `get`, `resolve`, `references`, `definitions`, `bindings`, `rename`, `bind_references`, `rebind`, `invalidate` |
| `module.semantic.call_contexts(node=...)` | Analysis context identities allocated for a call site |
| `module.semantic.points_to(node=...)` | Abstract object identities an expression may reference |
| `module.semantic.may_alias/must_alias` | Alias queries over the abstract heap |
| `module.semantic.allocation_site(object_id=...)` | Syntax node that allocated an abstract object |
| `module.semantic.heap_readers/heap_writers(object_id=...)` | Node identities recorded against an abstract object |
| `module.semantic.symbol_origin(symbol_id=...)` | Predecessor symbol after a cross-scope relocation |
| `module.semantic.invalidate(symbol_id=...)` | Drop cached inference for a symbol and its dependents |

`check_source` and `fix_source` are thin wrappers over `astart.rules`:
they build the default catalog and registries once per process and cache
them, so callers never assemble `Catalog`/`Registries`/`FixSettings` by
hand. `fix_source` defaults to the `guarded` safety ceiling, matching
`astart fix`; pass `settings=FixSettings(...)` to change it. Both names
are exported from the package root. Core source operations are initialized
before the rule API, so imports need no dynamic loader or circular fallback.

`fix_file`/`fix_paths` (`astart.files`) operate on files: they decode
with the declared PEP 263 encoding, fix through `fix_source` and replace
the file atomically (`write=False` is a dry run). `FileOutcome` reports
`before`/`after`/`applied`/`changed`/`written`/`error`; a bad file never
stops the others in `fix_paths`. `read_source`/`write_atomic` moved here
from `astart.cli` so the CLI and the API share one implementation.

`Settings` (`astart.settings`) is the public configuration object: a
frozen dataclass mirroring every `FixSettings` field a
`pyproject.toml` can express. `Settings.from_pyproject(path)` validates
through `cli/config.py` (malformed tables raise `ConfigError`) and maps
`safety-ceiling`, `min-confidence`, `target-version`, `checker` and
`protocol-placement`; `to_fix_settings(checker=...)` resolves
`target_version` via `resolve_target` and leaves the `Checker` object to
the caller, the same split the CLI uses.

## Source graph and typing graph

Symbol edits operate on identities and native reference nodes. Use
`module.semantic.symbols.rename(symbol_id=..., new_name=...)` to update a
binding and its resolved reads. Parameter renames also update keyword labels
whose call contracts point to that exact parameter declaration.
`rebind(symbol_id=..., target_id=..., within=...)` redirects resolved reads to
an existing symbol; `within` optionally selects an owned subtree.
`bind_references(bindings={name_node: target_symbol_id})` binds a batch of
owned or freshly constructed read nodes before attachment. Capture and target
checks run before mutations; node identities are retained and the shared
semantic index invalidates dependent conclusions. Unrelated shadowed names,
attribute labels, literal values and prose are never renamed by spelling.

Comment controls are parsed at the COMMENT-token boundary into suppression
fields, selector children and optional native control nodes. Wrapping consumes
these nodes directly. Directive text is not scanned again by the wrapper.

The mutable Python AST remains the canonical syntax ownership graph.
The semantic layer owns lexical identities, bindings, expression dependencies,
abstract values, contracts, and evidence. Its internal graph-conversion
pipeline supplies additional annotations to the **same** native solver rather
than creating a second, user-facing inference API.

The graph-conversion path is intentionally opt-in; calling `infer_type()`
without it does not require a stubs directory. With `apply=False`, conversion
conclusions are virtual and can be inspected as `TypeEvidence` records.
`apply=True` writes verified annotation changes to the original AST.

Call bindings expose the five Python `inspect.Parameter` kinds:
`POSITIONAL_ONLY`, `POSITIONAL_OR_KEYWORD`, `VAR_POSITIONAL`, `KEYWORD_ONLY`,
and `VAR_KEYWORD`, including omitted parameters with defaults.

## Revisions and snapshots

- Normal Python AST edits remain mutable.
- Exposed token snapshots are immutable records associated with a revision.
- Moves, insertions, and nested edits trigger dependency-sensitive token
  changes; unsupported source patches fail rather than silently corrupting
  the program when preservation is strict.
- Inference may return an explicit unknown instead of an unjustified exact
  value. Its explanations, type evidence, and contract conflicts remain
  inspectable.
- `module.semantic.refresh()` re-indexes incrementally: lexical subtrees
  untouched by a revision keep their symbols, bindings, occurrences and
  dependency edges, unchanged control-flow graphs only re-solve their
  affected blocks, and cross-scope symbol relocations keep lineage through
  `Symbol.origin_id`.
- Occurrence roles distinguish reads (`READ`), writes (`WRITE`), closure
  captures (`CAPTURE`), and type expressions (`ANNOTATION`); dependency
  edges cover symbol flow (`READS_SYMBOL`, `CAPTURES_SYMBOL`,
  `REACHES_DEFINITION`), scope lookups (`DEPENDS_ON_SCOPE`), abstract heap
  access (`REFERENCES_OBJECT`, `READS_HEAP_LOCATION`,
  `WRITES_HEAP_LOCATION`), and control dependence.
- `AnalysisBudgets` bounds the abstract interpreter by recursion depth,
  call contexts (`context_sensitivity`: `full`, `caller`, `none`), union
  size, iterations, operations, symbolic expressions, heap objects, and an
  optional wall-clock deadline; exhausted budgets yield `UnknownValue`,
  never execution of analyzed code.

## Distribution and verification

Build with `python -m pip wheel --no-deps --no-build-isolation .` or install the
prebuilt wheel. Run `python -m pytest -q` from the source directory. The
combined package includes a large specialized graph backend; its total
coverage is measured in full, not hidden by coverage exclusions.

The interpreter does not evaluate arbitrary submitted Python code. Python's
entire dynamic runtime behavior and typing specification are not fully
represented, and some transformations intentionally require safe fallback.

Typed documentation generation is enabled by default through
`Settings(docstring_types=True)` and `FixSettings(docstring_types=True)`.
Set the field to `False` to retain untyped documentation. This option acts on
existing docstrings; `stub_docstrings=True` also creates missing public stubs.
Native `DocEntry` fields receive annotation types without replacing existing
prose. New fields use `TODO.`. Generator yield and terminal return components
remain separate, and explicit exceptions are collected from the owning
function body. Mixed-style documents remain untouched; unknown generator
aliases do not receive guessed element types.
