# `tests/`

Tests for source-preserving comment AST nodes and safe AST rewrites.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Astart regression tests and typed expectation helpers.
- [`expectations.py`](expectations.py) — Typed, keyword-only expectation helpers used by the test-suite.
- [`test_ast_comments.py`](test_ast_comments.py) — Tests for source-preserving comment AST nodes and safe AST rewrites.
- [`test_astart_api.py`](test_astart_api.py) — Validate astart's sole supported public package API.
- [`test_cli_check.py`](test_cli_check.py) — Verify the check command.
- [`test_cli_discovery.py`](test_cli_discovery.py) — Verify file discovery for the command line.
- [`test_cli_fix.py`](test_cli_fix.py) — Verify the fix command.
- [`test_cli_main.py`](test_cli_main.py) — Verify command-line wiring.
- [`test_cli_render.py`](test_cli_render.py) — Verify text and JSON rendering of findings.
- [`test_format_annotations.py`](test_format_annotations.py) — Add and remove annotations while preserving the surrounding source.
- [`test_format_annotations_corpus.py`](test_format_annotations_corpus.py) — Write inferred annotations back into real modules without losing source.
- [`test_format_ast.py`](test_format_ast.py) — Regression tests for exact and conservative syntax-preserving AST edits.
- [`test_format_edits.py`](test_format_edits.py) — Apply many small AST edits and check source preservation fails closed.
- [`test_format_inline_bodies.py`](test_format_inline_bodies.py) — Inline bodies belong to their statement; real semicolons stay ambiguous.
- [`test_graph_application.py`](test_graph_application.py) — Exercise the graph command-line application and conversion artifacts.
- [`test_graph_compatibility.py`](test_graph_compatibility.py) — Verify graph type synthesis without executing source code.
- [`test_graph_context.py`](test_graph_context.py) — Exercise conversion contexts, pipeline order and the checkpoint backend.
- [`test_graph_corpus.py`](test_graph_corpus.py) — Convert a corpus of real-world modules through the full graph pipeline.
- [`test_graph_document.py`](test_graph_document.py) — Exercise graph documents, positions, usage graphs and the resolver.
- [`test_graph_engine.py`](test_graph_engine.py) — Exercise the from-scratch engine's type helpers and inferer classes.
- [`test_graph_integration.py`](test_graph_integration.py) — Tests adapted from the Astart project's structured-annotation design.
- [`test_graph_post_refinements.py`](test_graph_post_refinements.py) — Drive the generic post-refinement passes with pre-annotated modules.
- [`test_graph_protocols.py`](test_graph_protocols.py) — Exercise the conversion protocols and the print-like helper.
- [`test_graph_refinements.py`](test_graph_refinements.py) — Exercise the document-based refiner and the refinement service.
- [`test_graph_stub_index.py`](test_graph_stub_index.py) — Exercise lazy stub lookup against directory and archive roots.
- [`test_graph_synthesis.py`](test_graph_synthesis.py) — Exercise the semantic type-hint synthesis API end to end.
- [`test_graph_type_expressions.py`](test_graph_type_expressions.py) — Exercise the graph type-expression codec and annotation grammar.
- [`test_graph_unified.py`](test_graph_unified.py) — Regression tests for the integrated annotation conversion pipeline.
- [`test_incremental_ast.py`](test_incremental_ast.py) — Regression tests for incremental coordinates and PEP 701 f-string edits.
- [`test_lexical_ast.py`](test_lexical_ast.py) — Regression tests for semantic shebangs and immutable synchronized tokens.
- [`test_review3_fixes.py`](test_review3_fixes.py) — Regression tests for the final review of the check/fix work.
- [`test_rules_catalog.py`](test_rules_catalog.py) — Verify catalog loading and the data invariants.
- [`test_rules_constructors.py`](test_rules_constructors.py) — Verify that imported constructors type their calls.
- [`test_rules_end_to_end.py`](test_rules_end_to_end.py) — Exercise the seeded rule catalog end to end.
- [`test_rules_engine.py`](test_rules_engine.py) — Verify the reference engine and the syntactic and scope facts.
- [`test_rules_exists_guard.py`](test_rules_exists_guard.py) — Verify that unsupported predicates fail at validation, not at check time.
- [`test_rules_facts_semantic.py`](test_rules_facts_semantic.py) — Verify the call and docstring facts of the reference engine.
- [`test_rules_fixes.py`](test_rules_fixes.py) — Verify the fixes and the behavioural catalog invariants.
- [`test_rules_formatter.py`](test_rules_formatter.py) — Verify the one-shot ruff formatting phase.
- [`test_rules_hints.py`](test_rules_hints.py) — Verify the corroborated type-hint engine.
- [`test_rules_imports.py`](test_rules_imports.py) — Verify automatic import insertion.
- [`test_rules_model.py`](test_rules_model.py) — Verify the entity model of the rule ontology.
- [`test_rules_never_returns.py`](test_rules_never_returns.py) — Verify NoReturn for functions that always raise.
- [`test_rules_predicate.py`](test_rules_predicate.py) — Verify the predicate algebra of the rule ontology.
- [`test_rules_protocol_fix.py`](test_rules_protocol_fix.py) — Verify Protocol synthesis through the fix runner.
- [`test_rules_protocols.py`](test_rules_protocols.py) — Verify structural-usage analysis and Protocol rendering.
- [`test_rules_registry.py`](test_rules_registry.py) — Verify the registries of node kinds, facts and procedures.
- [`test_rules_review2_fixes.py`](test_rules_review2_fixes.py) — Regression tests for wrong hints found by the second whole-branch review.
- [`test_rules_review_fixes.py`](test_rules_review_fixes.py) — Regression tests for defects found by the whole-branch review.
- [`test_rules_runner.py`](test_rules_runner.py) — Verify the single-pass fix runner.
- [`test_rules_runner_corpus.py`](test_rules_runner_corpus.py) — Precision and acceptance tests for the gated type-hint fixer.
- [`test_rules_schema.py`](test_rules_schema.py) — Verify the generated JSON Schema of the rule catalog.
- [`test_rules_synthesis_corpus.py`](test_rules_synthesis_corpus.py) — Run every synthesizing fix over real modules.
- [`test_rules_typevar_fix.py`](test_rules_typevar_fix.py) — Verify TypeVar synthesis through the fix runner.
- [`test_rules_typing_fixes.py`](test_rules_typing_fixes.py) — Verify the TYP003 rule and its two gated fixes.
- [`test_rules_vocabulary.py`](test_rules_vocabulary.py) — Verify the closed vocabulary of the rule ontology.
- [`test_semantic_advanced.py`](test_semantic_advanced.py) — Advanced semantic regression tests for statements, scopes and fallbacks.
- [`test_semantic_ast.py`](test_semantic_ast.py) — Semantic integration, identity, CFG, aliasing, and safe inference tests.
- [`test_semantic_bind_calls.py`](test_semantic_bind_calls.py) — Bind many calls with one revision check.
- [`test_semantic_corpus.py`](test_semantic_corpus.py) — Run the semantic analyzer over real-world modules from the corpus.
- [`test_semantic_mutations.py`](test_semantic_mutations.py) — Differential mutation checks against fresh full static analysis.
- [`test_semantic_revisions.py`](test_semantic_revisions.py) — Revision-aware semantic features: roles, edges, provenance and reuse.
- [`test_semantic_worklist.py`](test_semantic_worklist.py) — Differential and deletion-sensitive worklist/regression tests.
- [`test_structured_nodes.py`](test_structured_nodes.py) — Exercise docstring AST nodes, suppression rules and comment blocks.
- [`test_type_inference.py`](test_type_inference.py) — Regression tests for bidirectional, provenance-carrying type inference.
- [`test_typing_contracts.py`](test_typing_contracts.py) — Regression tests for signatures, overloads, generics and class types.
- [`test_typing_relations.py`](test_typing_relations.py) — Direct, conservative generic/ABC/protocol compatibility regressions.
- [`test_typing_spec_extended.py`](test_typing_spec_extended.py) — Python typing specification refinements for the unified semantic engine.

### Subdirectories

- [`corpus/`](corpus/README.md) — Provide abc.py txt content.

<!-- exactus:inventory:end -->
