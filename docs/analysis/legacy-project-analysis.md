# Legacy inference and transformation analysis

The reusable mechanisms are indexed semantic queries, typed evidence,
explicit synthesis decisions, stub projection and structured AST editing.
They should extend Astart's existing components. Importing the old application
or copying its independent parse/graph/formatting stacks would undermine the
requested single-AST architecture.

## Scope and evidence

[The machine-readable inventory](legacy-project-analysis.json) covers every
Python implementation module in the four requested roots: 45 contract-farm
modules, 101 farm `perfectionist` modules, 15 external autowrap modules and
7 external autoinsert modules: **168 modules, 73,082 source lines**.
Each has a SHA-256 digest, definition positions, imports, module/API
explanations, syntax metrics and structural call sites. Syntax parsing and
compilation succeeded for all 168. Environments, caches, images and generated
stress outputs are excluded. No legacy application, import hook or test suite
was executed. This is exhaustive structural coverage, with targeted semantic
inspection of the mechanisms below; it is not exhaustive behavioral proof.

Structural call-site counts include 20 `parse`, 6 `parse_module`, 2
`parse_file`, 38 `unparse`, 19 `deepcopy`, 19 `walk`, 5 `generate_tokens`,
5 `ThreadPoolExecutor` and 30 `suppress` occurrences. These are syntactic
labels, not resolved call targets or runtime frequency measurements.

## Mechanisms to adopt and improve

| Legacy subsystem | Current destination | Concrete adoption and acceptance |
| --- | --- | --- |
| `indexed_graph`, `traceable_paths`, `ant_farm_views`, `graph` | `semantic/identities.py`, `semantic/scopes.py`, `delta.py` | Keep identity/parent/reference indexes and chainable queries over the same nodes. Preserve deletion ancestry; invalidate reverse dependents once. CC-10/CC-13 and F-27 require bounded dirty work and identity parity. |
| `contracts`, `swarm`, `swarm_inference`, `evidence_algebra` | `rules/negotiation` | Retain typed contributions, union/intersection distinctions, explanations and deterministic worklists. Carry evidence-origin IDs and retract unsupported consequences. Count dequeued events separately from changed beliefs. F-17/CC-13. |
| `objective`, `annotator`, `conversion` | `rules/recovery.py`, negotiation policy and runner | Separate candidate generation from acceptance. Preserve current proof/checker gates; do not let a confidence score authorize a contradictory annotation. Validate against `typed.py` and report exact/equivalent/wrong/missing separately. |
| `typeshed_inference`, `stub_integration` | `stubs/parser.py`, `resolver.py`, project library index | Resolve target versions, overloads, receiver substitutions, aliases and constructors through existing stub contracts. Keep missing/malformed stub outcomes inspectable; never silently turn malformed stubs into proof. T-08/I-21. |
| `type_expressions`, `type_catalogs`, `type_aliases`, generic/type parameters | Negotiation algebra and semantic typing contracts | Reuse normalized type relations and declarations. Preserve parameter identity, bounds, variance and defaults; instantiate per call. Avoid parallel string-only type catalogs. |
| `protocol_generation`, `protocols`, import management/generation | Current protocol/import planners | Generate owned AST nodes with binding/collision checks. Check complete synthesized contracts against all uses before commitment; use existing imports rather than duplicate alias logic. |
| `tokenized_ast`, `comment_preservation`, `easy_editors`, `formatter` | `CommentedModule`, `SourceTokenizer`, `FormatPreserver`, doc AST | Keep native comments, structured doc sections and lexical ownership. Emit edits from node changes. Replace repeated module parsing with transaction locations; parse only external formatter islands. CC-09–CC-12. |
| autowrap | `autowrap.py`, `wrapping.py` | Native `wrap_tree` edits actual doc/comment/statement nodes. Balanced line breaks retain each fitness state, protect examples and directives, preserve TODOs and use shared source anchors. Tests verify no parsing during the pass. |
| autoinsert | `autoinsert.py`, `magic_values.py` | Native helper/constant construction, lexical print resolution, collision checks and module/function/class numeric scopes. Default off; refuse ambiguous bindings and unsafe class construction. Runtime fixtures cover semantics and composition. |
| `eta`, `diff`, `rruff` | Existing sensors, reports and formatter process boundary | Adopt only measured observability/diagnostics needs. Do not transplant an 8,107-line ETA engine or add another Ruff distribution/runtime. Cancellation and resource ownership remain explicit. |

## Confirmed legacy risks not copied

1. `swarm.py:88–96,177–210` increments `processed_events` by **changed
   beliefs**. Messages discarded by `_should_process` still consume work but
   do not advance that counter. The nominal event budget therefore does not
   bound dequeued work. Count events, changed beliefs and queue size separately.
2. `swarm.py:213–237` keys best messages by path, type and polarity;
   `contracts.py:52–58` candidates have confidence, distance and explanation,
   but no structured evidence-origin identity. This does not establish
   independent support. Do not add probabilistic evidence fusion until
   origin/correlation handling and retraction tests exist.
3. `stub_integration.py:120–183` marks missing or malformed modules loaded,
   silently ignores syntax errors and uses broad `suppress(Exception)` for
   class-return creation. Preserve structured refusal reasons and distinguish
   not-found, malformed and unsupported target syntax.
4. `stub_integration.py:408–430` scans the entire graph to identify whether
   each attribute is a call target. Across many attributes this is quadratic.
   Use the retained parent/field index instead.
5. Legacy print replacement selects names by spelling without lexical scope
   resolution. It can rewrite a parameter/local/import named `print`.
   The native implementation consults the existing scope graph and preserves
   unresolved wildcard cases.
6. Legacy `aprint` selects `file or stdout` and writes a joined string itself.
   A falsey supplied stream is lost, stdout can be captured too early and
   partial-write/exception behavior can differ. The native helper delegates
   printing and current-stream selection to builtin print and owns only
   explicit path file handles.
7. The old wrapping DP stores one best state at each break while applying
   fitness-transition penalties. Discarding other fitness states can discard
   the globally best continuation. The native breaker retains all three
   fitness states per endpoint.
8. A naive native class-constant port would introduce `__class__` reads in
   eager lambdas/comprehensions or methods called during class construction.
   The cell is uninitialized there. Native extraction refuses these cases;
   it also refuses explicit `__class__` bindings and construction hooks.
9. A module helper beginning `__name` would be mangled when referenced by a
   method. Native insertion rejects private-mangled helper names before any
   mutation and reserves generated names across all lexical scopes.

## Delivered changes and remaining work

Delivered native passes manipulate the caller's `CommentedModule`; no old
project, LibCST or pyposast import is required. The explicit `transform`
command composes them on one module and uses the existing emitter. The
print helper uses structural protocols, with one cast for builtin print's
conditional flushing overload; emitted helper syntax is separately checked
with BasedPyright. Runtime insertion is separate from annotation defaults.

Typeshed discovery now falls back to installed editor Pyright/BasedPyright
bundles when explicit, environment and installed package choices fail.
The requested Devin extension's `typeshed-fallback` is a useful stub source;
its username/version are not hardcoded. Discovery ordering is tested with
injected temporary homes and numeric extension versions.

**Still open:** removing full-module parsing from shared emission and token
refresh; fully tracked mutable child lists; lexical island convergence;
complete node-aware punctuation/trivia ownership; incremental fact/evidence
retraction; measured deterministic parallel inference. These are explicit
CC-09–CC-13 tasks, not completed by adding snapshots or workers. The current
legacy analysis does not demonstrate that any legacy heuristic improves
annotation accuracy; new inference mechanisms need controlled ablations and
reference comparison before adoption.

## Complete contract-farm module inventory

The following descriptions are extracted from source module docstrings;
claims in those docstrings are descriptions, not independent validation.

| Module | Lines | Source description |
| --- | ---: | --- |
| `__init__.py` | 6 | Semantic Contract Farm package. |
| `_types.py` | 13 | Shared type aliases for semantic contract farm. |
| `advanced_features.py` | 924 | Catalogue of advanced Python constructs and graph seeding helpers. |
| `advanced_usage.py` | 939 | Advanced usage records and analyzer. |
| `analyzer.py` | 255 | High-level analyzer facade for contract ant-farm inference. |
| `annotator.py` | 695 | Automatic annotation synthesis from contract inference results. |
| `ant_farm_views.py` | 521 | Ant-farm symbol and AST views, collections, and toolkit. |
| `base.py` | 341 | Base type aliases, constants, and exceptions for semantic contract farm. |
| `code_composition.py` | 247 | Semantic declaration blocks, module composition, and codegen collection. |
| `comment_preservation.py` | 784 | Comment metadata, comment-aware parsing, and transformations. |
| `contracts.py` | 255 | Contract and belief algebra for ant-farm type inference. |
| `conversion.py` | 832 | Agnostic untyped-to-typed conversion pipeline. |
| `data_model.py` | 134 | Shared data models for semantic entities and graph nodes. |
| `diff.py` | 439 | Diff viewer utilities extracted from format_final_restore_updated(1).py. |
| `easy_editors.py` | 869 | Docstring, function, class, and module editors. |
| `eta.py` | 8107 | Threaded ETA (Estimated Time of Arrival) engine. |
| `evidence_algebra.py` | 730 | Evidence containers, type-expression algebra, and solvers. |
| `exceptions.py` | 22 | Shared exceptions and utilities for semantic contract farm. |
| `formatter.py` | 4831 | Format Python files, including snippets inside docstrings and f-strings. |
| `generic_parameters.py` | 332 | Generic type parameter models, factories, and editor. |
| `graph.py` | 2074 | Traceable graph model for type-inference contracts. |
| `identifiers.py` | 58 | Identifier validation utilities for the Semantic Contract Farm. |
| `import_generation.py` | 707 | Import generation infrastructure for semantic code generation. |
| `import_management.py` | 674 | Import usage modelling, requirements, grouping, and placement. |
| `imports.py` | 248 | Import-related data models for semantic code generation. |
| `indexed_graph.py` | 1516 | Indexed semantic graph model, builder, and query API. |
| `local_import_inspection.py` | 834 | Local import resolution, inspection, and symbol catalogs. |
| `objective.py` | 553 | Objective model for collective type-hint synthesis. |
| `parameters.py` | 424 | Semantic argument and parameter utilities. |
| `paths.py` | 121 | Stable path identities for semantic AST analysis. |
| `protocol_generation.py` | 1333 | Generated top blocks, protocol grammar, and cast factories. |
| `protocols.py` | 239 | Protocol specification and indexing utilities. |
| `rruff.py` | 181 | Build/use a maximum-compressed offline Ruff bundle. |
| `semantic_graph.py` | 1812 | Semantic graph nodes, scopes, symbols, evidence, and builders. |
| `semantic_model_parser.py` | 737 | Parsed semantic model dataclasses and parsers. |
| `stub_integration.py` | 616 | Typeshed stub integration for the contract graph. |
| `swarm.py` | 335 | Ant-farm contract negotiation engine. |
| `swarm_inference.py` | 1180 | Swarm evidence, propagation graph, builders, and inference engine. |
| `tokenized_ast.py` | 681 | Source positions, token metadata, and tokenized parsing. |
| `traceable_paths.py` | 914 | Traceable qualified paths, symbol records, and path index. |
| `type_aliases.py` | 429 | Utilities for Python 3.13 type aliases. |
| `type_catalogs.py` | 1164 | Direct type references and catalogs for builtin and typing hints. |
| `type_expressions.py` | 1251 | Type expression models, references, and rendering. |
| `type_parameters.py` | 222 | Specifications and registries for type parameters. |
| `typeshed_inference.py` | 1492 | Typeshed models, stub parser, signature catalog, and swarm inference. |
