# `astart.rules` architecture

One paragraph per module, taken verbatim from each module's docstring.

## `__init__.py`

Rule ontology: a typed, serializable catalog of checks and fixes.

The model modules (``vocabulary``, ``predicate``, ``model``, ``registry``,
``catalog`` and ``schema``) do not depend on the AST packages. ``engine``,
``facts`` and ``appliers`` are the reference implementation that evaluates
the catalog against Python source.

## `appliers.py`

Edit appliers: tree-level rewrites that fixes are made of.

## `attributes.py`

Prove the type of ``self.attr`` from every write to it in a class.

An instance attribute is annotated only when each assignment to it, in every
method of the class, has a type the syntax proves, they all agree (``None``
plus one other type gives ``T | None``), and nothing else in the module can
write it: no other receiver, no class-level binding, no base class that
declares it, no dynamic ``setattr``.

## `call_problems.py`

M6-05…M6-08 call-shape detectors.

Four standalone detectors over the trusted :class:`CallBindings` layer:

- ``find_missing_arguments`` — required parameters with no effective
  argument (``missing required argument`` binding errors);
- ``find_unexpected_arguments`` — keyword arguments no parameter
  accepts, or surplus positional arguments;
- ``find_ambiguous_callees`` — bindings marked ``indeterminate``
  (uncertain ``*args``/``**kwargs`` expansions);
- ``find_unresolved_callees`` — calls whose callee root is bound in the
  module yet the trusted binding refuses it (distrusted receivers,
  unsafe methods, redefinitions).

Builtins and unbound names are out of scope: project binding only
covers module-level definitions, so ``print``/``len``/unknown externals
are never flagged.  Catalog wiring is deferred (M8-22).

## `catalog.py`

Load, dump and validate rule catalogs.

## `checker.py`

External type-checker gate: reject fixes that make the checker unhappy.

## `confidence.py`

How sure the engine is about each offered fix.

## `constants_grouping.py`

M8-09 ``structure.constants-grouping``: loose module constants.

The house convention groups module constants in a ``@final class
Constants`` with ``Final`` annotations.  The detector flags top-level
``UPPER_SNAKE`` assignments and annotated constants that sit outside
such a class; dunder names, ``TYPE_CHECKING`` aliases and ``__all__``
are exempt.

## `docs_fixes.py`

Docstring facts and fixes: parameter entries and whitespace.

Three fixes edit a function's or class's docstring in place:

* ``docs.add-parameter-entries`` writes a stub entry for each parameter the
  docstring does not mention (DOC002);
* ``docs.remove-stale-entries`` drops entries for parameters the function no
  longer takes (DOC003);
* ``docs.tidy-docstring`` strips trailing space, collapses blank runs and
  aligns the body (DOC007).

They only touch Google-style docstrings written with triple quotes and no
tabs, because anything else cannot be rewritten without changing its style.

## `docs_missing.py`

DOC001 ``docs.missing-docstring``: definitions without docstrings.

Flags modules, classes and functions whose first statement is not a
docstring.  Private names (``_leading``) are exempt, matching the
convention that internal helpers do not owe prose.

## `docs_missing_raises.py`

DOC006 ``docs.missing-raises``: raised exception not documented.

A documented function should name the exceptions callers can see.  The
detector flags ``raise X`` statements whose exception is absent from the
docstring's ``raises`` entries; undocumented functions are DOC001's job.

## `docs_missing_returns.py`

DOC004 ``docs.missing-returns``: value-returning function, no section.

A function that returns a value (or yields) should say what comes back.
The detector flags documented functions that produce values but have no
``returns``/``yields`` entries; undocumented functions are DOC001's job.

## `docs_shared.py`

Shared docstring helpers for the DOC rule family.

The detectors prefer the structured ``module.docstrings`` a
``CommentedModule`` carries; on a plain ``ast.Module`` they fall back to
a minimal Google-style section parse, so the rules run on either AST.

## `docs_stale_params.py`

DOC003 ``docs.stale-parameter``: documented name with no parameter.

A docstring that names a parameter the signature no longer has is worse
than none: it misleads readers.  The detector compares documented
``parameters`` entries against the declared signature.

## `docstring_edit.py`

Pure text edits for Google-style docstrings.

The functions work on the docstring *value* as the parser stores it: the
text between the quotes, with the body indented like the code around it and
the closing quotes on a line of their own. They add missing parameter
entries, remove entries for parameters that no longer exist, and tidy
whitespace. Nothing here touches the AST.

## `engine.py`

Reference engine: parse once, evaluate rules, report findings.

## `engine_hints.py`

Annotations from the inference engine, for conversion mode.

The engine (``astart.graph``, descended from the author's earlier converter)
annotates far more than the evidence-based pipeline will accept: it needs no
second signal. Conversion mode (``--engine``) takes its result for the nodes
nothing else decided, at the lowest confidence tier, and leaves it to the
type checker's gate to veto the ones that cause new errors.

## `environment.py`

Detect where a file lives so a checker can resolve its imports.

The external checker runs on a scratch copy kept outside the project. For it
to see what the real file sees, three things are derived from the file's
location: the package it belongs to (the chain of ``__init__.py`` files), the
directories absolute imports start from (the package's parent, a ``src``
layout, the project root), and its relative imports, which are rewritten
against the package because the scratch copy is not inside it.

## `facts.py`

Subjects, fact providers and registries for the reference engine.

## `formatter.py`

Formatter phase: run ruff once on the final text.

## `fstring_normalize.py`

M8-25 fixer: normalise f-string replacement-field interiors.

Rewrites whitespace *placement* inside ``JoinedStr`` fields —
``f"{ x }"`` → ``f"{x}"``, ``f"{x !r}"`` → ``f"{x!r}"`` — while
preserving the expression text, conversion flags and format-spec text
verbatim.  ``=``-debug fields, unusual expression spacing and anything
the scanner cannot prove safe are refused.  Standalone module;
catalog/applier wiring is deferred (M8-22).

## `grouping.py`

Place a new ``Final`` constant inside an existing ``Constants`` class.

The house convention keeps module constants in ``@final class Constants``.
When ``typing.add-final`` makes a module global ``Final`` and such a class
already exists, the constant joins that class and the module's uses become
``Constants.NAME``. Anything that could break stays a plain module global:
exported names, names reached by ``global``, names the class body or the
module's import-time code reads before the class exists, and name clashes.

## `hints.py`

Corroborated type hints: candidates are accepted only with evidence.

## `imports.py`

Add the imports a synthesized annotation needs.

## `imports_bare.py`

IMP001 ``imports.bare-import``: plain ``import mod`` used as ``mod.attr``.

A bare ``import ast`` that only ever appears as ``ast.walk`` can become
``from ast import walk`` plus rewritten use sites — proven safe when the
imported attributes collide with nothing already bound.  This module
detects rewrite candidates; collision checks and the edit live in the
fix.

## `imports_bare_fix.py`

IMP001 fixer: rewrite ``import a`` attribute uses into ``from`` imports.

``rewrite_bare_imports`` converts module-level ``import a[.b...]``
statements whose attribute uses are all safe loads into per-attribute
``from`` imports plus rewritten use sites.  Each attribute is decided
independently: unsafe sites keep ``import a`` alive for them.

Standalone module — catalog/applier wiring is deferred (M8-22).

## `jsonvalue.py`

JSON value type and canonical serialization for the rule catalog.

## `libkw.py`

Typeshed-generated library keyword-safety table.

``SIGNATURES`` maps ``"module.qualname"`` to the parameter names a call
may pass by keyword.  ``names`` lists keyword-passable parameters
(positional-or-keyword and keyword-only); positional-only parameters
never appear there: ``/`` markers and the ``__name`` convention are
excluded, as are ``self`` and ``cls`` receivers.  ``positional`` lists
every parameter a positional argument can fill, in order (positional-only
included).  ``ANY_KEYWORD``/``var_positional`` mark ``**kwargs``/``*args``.

Stdlib entries come first; third-party modules join only through an
explicit allow-list.  Regenerate with ``scripts/utils/generate_libkw.py``.

## `library_calls.py`

Bind calls to curated library signatures from ``libkw``.

``libkw.SIGNATURES`` is a typeshed-generated table of callees whose
parameters may be passed by keyword.  This module resolves a call's
callee to a ``module.qualname`` key — through the module's own import
aliases or the ``builtins`` fallback — and synthesizes a ``BoundCall``
so ``calls.add-keywords`` can rewrite positional arguments.

Only syntactically certain bindings are produced: ``*args``/``**kwargs``
expansions, attribute chains on non-imported roots, shadowed import
roots and already-keyworded duplicates all refuse.

## `methods.py`

Resolve method calls that the analyzer does not bind, or binds loosely.

A call is only trusted when nothing in the module can make it reach another
signature: the method is defined once, every definition of that name takes the
same parameters, and no instance attribute of that name is ever assigned.

## `model.py`

Entities of the rule ontology and their JSON conversion.

## `negotiation/`

Two-way type negotiation over a graph of contracts.

Entities are nodes, facts about the program are directed contracts between
them, and typed candidates travel forward and backward along the contracts
until every belief stops changing. See ``docs/planning/TODO.md`` chapter 10
(contract negotiation).

## `object_annotations.py`

TYP002 ``typing.no-object-annotation``: annotations spelled ``object``.

``x: object`` says nothing — any value fits — so astart treats it as a
missing annotation.  The detector flags ``object`` (and
``builtins.object``) wherever it appears as a parameter, return or
variable annotation, including inside string annotations.

## `parse_module.py`

PRS001 ``parsing.module-does-not-parse``: a file Python rejects.

No other rule can run when the module does not parse, so this detector
stands alone: it takes raw source and returns one candidate carrying the
syntax diagnostic, or nothing when the source parses cleanly.

## `predicate.py`

Predicate algebra: rule triggers expressed as data.

## `procedural.py`

Shared shape for standalone rule detectors.

Detectors in this package inspect a parsed module and yield
:class:`Candidate` records — a span plus evidence — without being wired
into a catalog or registry yet.  Registry and catalog entries adapt each
``find_*`` function to the engine's procedure calling convention.

## `process.py`

Run an external command and capture its output.

## `project_bridge.py`

Feed project-wide call evidence into per-module hint judging.

The project index knows calls in every file; :class:`ProjectView` turns
one module's slice of them into the same kind of per-site evidence the
local call machinery produces. Only what the argument's syntax proves in
the *caller's* scope counts — the inference engine's own types are not
independent evidence. Unresolvable expansions and ambiguous callees
produce unknown evidence, never evidence of absence.

## `protocol_verify.py`

Check a synthesized Protocol against the arguments callers really pass.

A Protocol built from how a function *uses* a parameter is only worth writing
if the module's own callers can satisfy it. This module looks at every direct
call of the function and reports the first argument whose type is provable
and provably lacks a required member: a builtin value (``"abc"`` has no
``read``), ``None``, or an instance of a plain class defined in the module.
Anything it cannot decide counts as no objection.

## `protocols.py`

Derive a structural ``Protocol`` from how a parameter is used.

A parameter that is only ever accessed as ``name.attr`` or called as
``name.attr(...)`` is used structurally: any object with those members would
do. :func:`structural_usage` proves that, member by member, and refuses on any
other use. :func:`protocol_source` renders the matching ``Protocol`` class.

## `provable.py`

Return types that follow from the syntax alone.

## `reasons.py`

Closed vocabulary of the reasons a fix or hint is not applied.

## `recovery.py`

Annotation-recovery benchmark: strip a typed module, fix it, compare.

Well-typed code is the ground truth. Removing its parameter and return
annotations and running the fixer shows how many annotations it recovers
(recall) and how many of the ones it writes match the original (precision).

## `registry.py`

Registries of node kinds, facts, procedures and appliers.

## `resolve.py`

Shared name-binding and call-resolution helpers for rules and hints.

## `runner.py`

Fix runner: parse once, apply many fixes, write once.

## `schema.py`

Generate the JSON Schema of the rule catalog from the entity model.

## `scopes.py`

Which names a syntax node binds.

## `strings_normalize.py`

String literal normalisation fixer (standalone, M8-24).

``normalize_strings`` rewrites plain single-line string constants:

- literals containing ``\\n`` escapes become triple-quoted strings with
  real newlines when the result cannot contain the closing delimiter;
- literals that overflow the line budget become parenthesised implicit
  concatenations split at whitespace boundaries.

f-strings, bytes, raw strings, triple-quoted strings, docstrings,
dict keys, ``__all__`` members, match patterns and strings already part
of an implicit concatenation are refused.  Catalog/applier wiring is
deferred (M8-22).

## `stubs/`

Read typeshed-style stubs: locate, parse and resolve names. A typeshed
snapshot is vendored as package data under `astart/stubs/artifacts/typeshed/`;
`find_typeshed` honours an explicit root and `ASTART_TYPESHED` first, then
falls back to the bundled copy — it never scans other installed packages
or editor extensions, so every machine resolves the same stubs.

The ideas come from ``typeshed_client`` (stub lookup, version and platform
conditions, overload groups, ``__all__``, re-exports and name resolution
across files), re-implemented here so astart needs no such dependency.

## `suppressions.py`

SUP001 ``suppression.marker-comment``: checker suppression comments.

Suppression comments are forbidden: a finding is fixed, not silenced.
The detector flags every comment the tokenizer recognized as a
suppression directive — ``noqa``, ``type: ignore``, ``pylint:
disable`` and friends — keeping ``enable``/``on`` reversals quiet.

## `type_mismatch.py`

M8-06 detectors: return-type mismatches and incompatible defaults.

``find_return_mismatches`` flags ``return`` expressions whose inferred
type is provably incompatible with the declared return annotation.
``find_incompatible_defaults`` flags parameter defaults whose inferred
type is provably incompatible with the parameter annotation.

Both refuse whenever inference is indeterminate — only a definitive
``compatible is False`` verdict from :func:`subtype` produces a
candidate.  Standalone detectors; catalog wiring is deferred (M8-22).

## `typevars.py`

Detect parameters that only flow through to the return value.

A parameter whose every use is as (an element of) a returned value is generic:
its type is whatever the caller passes. :func:`passthrough_return` proves
that and spells the return annotation in terms of a type variable.

## `variable_annotations.py`

TYP005 ``typing.missing-variable-annotation`` detector.

Flags simple-name assignments whose value has a stable, known inferred
type but which carry no annotation — candidates for an annotation the
tool could propose.  Refuses whenever inference is ``Unknown``,
unstable, or the name is already annotated, private, or a dunder.

Standalone detector; catalog wiring is deferred (M8-22).

## `vocabulary.py`

Closed vocabulary of the rule ontology.

## `whitespace_rules.py`

Whitespace rules: WSP001 blank-line runs and WSP002 trailing space.

Both rules read raw source lines: more than two consecutive blank lines
inside code, and trailing spaces or tabs on any line.  Docstring bodies
are source text too — the WSP002 fix trims them like any other line,
so the detectors report spans and leave rewrite policy to the fix.
