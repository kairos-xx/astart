# `rules/`

Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Tests mirroring the corresponding project subsystem.
- [`test_alias_declarations.py`](test_alias_declarations.py) — Legacy aliases become native declarations without variable annotations.
- [`test_annotation_preservation.py`](test_annotation_preservation.py) — User-written annotations are never overwritten by ``fix`` (AF-19).
- [`test_api_wrappers.py`](test_api_wrappers.py) — Public one-call ``check_source``/``fix_source`` wrappers (API-02).
- [`test_catalog_gate.py`](test_catalog_gate.py) — M8-21: rule catalog exit-gate invariants and CLI rule surface.
- [`test_engine_hints.py`](test_engine_hints.py) — Engine-sourced hints: lazy conversion, variable scan, hint gating.
- [`test_gold_expansion.py`](test_gold_expansion.py) — Expanded gold set: evidence-ladder expectations over 500 typed cases.
- [`test_opacity_owners.py`](test_opacity_owners.py) — G-03: every opacity reason reported on the pairs has a documented owner.
- [`test_protocol_typevar_danger.py`](test_protocol_typevar_danger.py) — M5-25: protocol and TypeVar synthesis danger-corpus gate.
- [`test_recovery_aliases.py`](test_recovery_aliases.py) — Keep generic alias and variadic tuple report comparisons accurate.
- [`test_rules_attribute_reads.py`](test_rules_attribute_reads.py) — ``return self.x`` is typed from the class's agreed attribute table.
- [`test_rules_attributes.py`](test_rules_attributes.py) — ``self.x = value`` assignments get an annotation when all writes agree.
- [`test_rules_calibrated_candidates.py`](test_rules_calibrated_candidates.py) — The one inference-engine candidate category measured as reliable.
- [`test_rules_call_problems.py`](test_rules_call_problems.py) — Tests for the M6-05…M6-08 call-shape detectors.
- [`test_rules_call_site_scope.py`](test_rules_call_site_scope.py) — Call-site arguments that are variables are typed from their scope.
- [`test_rules_catalog.py`](test_rules_catalog.py) — Verify catalog loading and the data invariants.
- [`test_rules_checker.py`](test_rules_checker.py) — Verify the external type-checker gate.
- [`test_rules_checker_fallback.py`](test_rules_checker_fallback.py) — mypy support and the floor that applies when no checker is installed.
- [`test_rules_comprehension_types.py`](test_rules_comprehension_types.py) — Comprehension displays are typed when their element types are provable.
- [`test_rules_confidence.py`](test_rules_confidence.py) — Verify offer confidence and the minimum-confidence gate.
- [`test_rules_constants_group.py`](test_rules_constants_group.py) — New Final constants join an existing ``Constants`` class.
- [`test_rules_constructors.py`](test_rules_constructors.py) — Verify that imported constructors type their calls.
- [`test_rules_constructors_kw.py`](test_rules_constructors_kw.py) — Verify keyword fixes on constructor calls (M2-03).
- [`test_rules_ddmin.py`](test_rules_ddmin.py) — Verify minimal checker failures and original-source batch recovery.
- [`test_rules_default_confidence.py`](test_rules_default_confidence.py) — A literal default is only as trustworthy as its measured exactness.
- [`test_rules_default_expression_edges.py`](test_rules_default_expression_edges.py) — Default-expression hints refuse contradictory or unprovable types.
- [`test_rules_determinism.py`](test_rules_determinism.py) — ``fix_source`` output does not depend on ``PYTHONHASHSEED``.
- [`test_rules_dunder_results.py`](test_rules_dunder_results.py) — Protocol dunders take their declared result, not the body-derived one.
- [`test_rules_end_to_end.py`](test_rules_end_to_end.py) — Exercise the seeded rule catalog end to end.
- [`test_rules_engine.py`](test_rules_engine.py) — Verify the reference engine and the syntactic and scope facts.
- [`test_rules_engine_mode.py`](test_rules_engine_mode.py) — Conversion mode: the inference engine fills what nothing else decided.
- [`test_rules_environment.py`](test_rules_environment.py) — The checker environment is detected from where the file lives.
- [`test_rules_exists_guard.py`](test_rules_exists_guard.py) — Verify that unsupported predicates fail at validation, not at check time.
- [`test_rules_expression_defaults.py`](test_rules_expression_defaults.py) — Non-literal defaults (``-1``, ``LIMIT``) corroborate a parameter's type.
- [`test_rules_facts_semantic.py`](test_rules_facts_semantic.py) — Verify the call and docstring facts of the reference engine.
- [`test_rules_fixes.py`](test_rules_fixes.py) — Verify the fixes and the behavioural catalog invariants.
- [`test_rules_flow_narrowing.py`](test_rules_flow_narrowing.py) — ``is None`` guards narrow an Optional parameter for return typing.
- [`test_rules_formatter.py`](test_rules_formatter.py) — Verify the one-shot ruff formatting phase.
- [`test_rules_fstring_normalize.py`](test_rules_fstring_normalize.py) — Tests for the M8-25 f-string interior normalisation fixer.
- [`test_rules_hint_cache.py`](test_rules_hint_cache.py) — Repeated ``fix_source`` calls on identical text give identical output.
- [`test_rules_hints.py`](test_rules_hints.py) — Verify the corroborated type-hint engine.
- [`test_rules_hostile_inputs.py`](test_rules_hostile_inputs.py) — ``fix_source`` survives hostile inputs without raising.
- [`test_rules_idempotence.py`](test_rules_idempotence.py) — M1-11: ``fix_source`` is idempotent across the whole replay corpus.
- [`test_rules_imports.py`](test_rules_imports.py) — Verify automatic import insertion.
- [`test_rules_imports_bare_fix.py`](test_rules_imports_bare_fix.py) — Danger-matrix tests for the IMP001 bare-import fixer.
- [`test_rules_kwargs_danger.py`](test_rules_kwargs_danger.py) — Danger matrix for the keyword fixer: unsafe calls must stay positional.
- [`test_rules_libkw.py`](test_rules_libkw.py) — Tests for the typeshed-generated library keyword-safety table.
- [`test_rules_library_calls.py`](test_rules_library_calls.py) — End-to-end tests for keywording calls via the ``libkw`` table.
- [`test_rules_line_endings.py`](test_rules_line_endings.py) — Fixed sources keep the input's CRLF line endings.
- [`test_rules_methods.py`](test_rules_methods.py) — Verify call-site resolution of methods (D4, D5).
- [`test_rules_model.py`](test_rules_model.py) — Verify the entity model of the rule ontology.
- [`test_rules_multi_binding_locals.py`](test_rules_multi_binding_locals.py) — Locals bound several times are typed when every binding agrees.
- [`test_rules_negotiated_fix.py`](test_rules_negotiated_fix.py) — Negotiated annotations written by the fixer must be valid when evaluated.
- [`test_rules_never_returns.py`](test_rules_never_returns.py) — Verify NoReturn for functions that always raise.
- [`test_rules_noreturn_calls.py`](test_rules_noreturn_calls.py) — ``NoReturn`` follows tail calls to in-module helpers that never return.
- [`test_rules_optional_defaults.py`](test_rules_optional_defaults.py) — A ``None`` default becomes ``T | None`` when call sites prove ``T``.
- [`test_rules_pair_contradictions.py`](test_rules_pair_contradictions.py) — G-04: every remaining dev-pair contradiction is root-caused and guarded.
- [`test_rules_param_matrix.py`](test_rules_param_matrix.py) — Characterize parameter-hint synthesis through the fixer.
- [`test_rules_predicate.py`](test_rules_predicate.py) — Verify the predicate algebra of the rule ontology.
- [`test_rules_procedural.py`](test_rules_procedural.py) — Tests for the standalone IMP001/SUP001/PRS001/TYP002 detectors.
- [`test_rules_protocol_fix.py`](test_rules_protocol_fix.py) — Verify Protocol synthesis through the fix runner.
- [`test_rules_protocol_verify.py`](test_rules_protocol_verify.py) — A synthesized Protocol is dropped when a call site provably objects.
- [`test_rules_protocols.py`](test_rules_protocols.py) — Verify structural-usage analysis and Protocol rendering.
- [`test_rules_recovery.py`](test_rules_recovery.py) — Verify the annotation-recovery benchmark.
- [`test_rules_recovery_relation.py`](test_rules_recovery_relation.py) — Recovery scoring tells contradictions from compatible differences.
- [`test_rules_registry.py`](test_rules_registry.py) — Verify the registries of node kinds, facts and procedures.
- [`test_rules_return_matrix.py`](test_rules_return_matrix.py) — Characterize return-type synthesis through the fixer.
- [`test_rules_return_proofs.py`](test_rules_return_proofs.py) — Language-guaranteed return proofs and exit-path analysis.
- [`test_rules_review2_fixes.py`](test_rules_review2_fixes.py) — Regression tests for wrong hints found by the second whole-branch review.
- [`test_rules_review_fixes.py`](test_rules_review_fixes.py) — Regression tests for defects found by the whole-branch review.
- [`test_rules_rounds.py`](test_rules_rounds.py) — ``FixResult`` reports how many rounds a run needed.
- [`test_rules_runner.py`](test_rules_runner.py) — Verify the single-pass fix runner.
- [`test_rules_runner_corpus.py`](test_rules_runner_corpus.py) — Precision and acceptance tests for the gated type-hint fixer.
- [`test_rules_schema.py`](test_rules_schema.py) — Verify the generated JSON Schema of the rule catalog.
- [`test_rules_skip_codes.py`](test_rules_skip_codes.py) — Verify the closed vocabulary of skip and rejection reasons.
- [`test_rules_slots.py`](test_rules_slots.py) — ``SlotTable`` settles only when every claim names one kind.
- [`test_rules_starred_calls.py`](test_rules_starred_calls.py) — ``*args`` in a call is never turned into a keyword.
- [`test_rules_strings_normalize.py`](test_rules_strings_normalize.py) — Tests for the M8-24 string literal normalisation fixer.
- [`test_rules_synthesis_corpus.py`](test_rules_synthesis_corpus.py) — Run every synthesizing fix over real modules.
- [`test_rules_type_checks.py`](test_rules_type_checks.py) — Tests for the M8-02 TYP005 and M8-06 mismatch detectors.
- [`test_rules_typer_binop.py`](test_rules_typer_binop.py) — ``%`` formatting and ``+`` on lists type when provable.
- [`test_rules_typer_builtins.py`](test_rules_typer_builtins.py) — ``abs``/``round``/``min``/``max``/``sorted`` and container constructors.
- [`test_rules_typer_matrix.py`](test_rules_typer_matrix.py) — Pin every verified ``expression_type`` row as a regression matrix.
- [`test_rules_typer_negatives.py`](test_rules_typer_negatives.py) — The typer never guesses: unprovable expressions give ``None``.
- [`test_rules_typer_positives.py`](test_rules_typer_positives.py) — Provable expressions give their exact type.
- [`test_rules_typer_pow.py`](test_rules_typer_pow.py) — ``**`` types to ``int``/``float`` only when no ``complex`` is possible.
- [`test_rules_typer_str_methods.py`](test_rules_typer_str_methods.py) — ``str`` method calls type by method name.
- [`test_rules_typer_subscript.py`](test_rules_typer_subscript.py) — Subscripts type through ``list``/``str``/``dict`` element rules.
- [`test_rules_typevar_fix.py`](test_rules_typevar_fix.py) — Verify TypeVar synthesis through the fix runner.
- [`test_rules_typevar_units.py`](test_rules_typevar_units.py) — Unit coverage for the pure helpers of ``rules.typevars``.
- [`test_rules_typing_fixes.py`](test_rules_typing_fixes.py) — Verify the TYP003 rule and its two gated fixes.
- [`test_rules_union_sites.py`](test_rules_union_sites.py) — Disagreeing call sites become a union when the engine corroborates it.
- [`test_rules_variable_annotations_fix.py`](test_rules_variable_annotations_fix.py) — Function-local variables get the annotation the evidence proves.
- [`test_rules_variadic_hints.py`](test_rules_variadic_hints.py) — ``*args`` and ``**kwargs`` are typed only when every call proves it.
- [`test_rules_variadic_methods.py`](test_rules_variadic_methods.py) — ``*args``/``**kwargs`` hints on methods via ``self`` and instances.
- [`test_rules_vocabulary.py`](test_rules_vocabulary.py) — Verify the closed vocabulary of the rule ontology.
- [`test_rules_whitespace_fixes.py`](test_rules_whitespace_fixes.py) — Tests for the WSP catalog rules and their text-level fixes.
- [`test_rules_writer_fuzz.py`](test_rules_writer_fuzz.py) — Fuzz the writer: any subset of fixes must still yield valid code.
- [`test_skip_docs.py`](test_skip_docs.py) — The skip-reason docs cover every enum member value.
- [`test_type_mismatch.py`](test_type_mismatch.py) — M8-06 detectors: return-type mismatches and incompatible defaults.

### Subdirectories

- [`negotiation/`](negotiation/README.md) — Tests mirroring the corresponding project subsystem.

<!-- exactus:inventory:end -->
