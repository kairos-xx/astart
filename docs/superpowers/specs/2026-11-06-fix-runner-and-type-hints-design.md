# Fix runner and gated type hints — design addendum

Status: approved in conversation (direction and scope), 2026-11-06.
Extends: `2026-11-06-rule-ontology-design.md` (sections 3.5 Fix, 6 Phases).
Builds on: `astart.rules` (first slice) and the annotation write-back added to
`astart.formatting`.

## 1. Intent

Make `fix` real: apply many fixes to a file in one pass, safely, and add the
fix Exactus cannot offer at all, **automatic type hints**, without ever writing
a hint the evidence does not support.

## 2. Findings that shape the design

- The inference pipeline proposes annotations (`module.convert(apply=False)`)
  but exposes **no usable per-hint evidence**: `infer_type` reports only
  `graph-inference`, and the explanation report was empty on a real run.
- Hints are reliable when a call site supplies evidence and are guesses when
  only an operator does: `x * 2` became `int`, `seq[0]` became `Sequence[int]`,
  `"hi " + name` with no call became `int`, `items` became `Sequence[object]`.
- `convert(apply=True)` also injects imports and class-level declarations, which
  the format-preserving writer cannot place. Applying only parameter and return
  proposals writes back cleanly on all 20 vendored modules.

Consequence: **do not trust the proposals; corroborate them.** The proposal
supplies a candidate. The fix layer accepts it only when independent evidence
that astart can verify agrees.

## 3. Hint acceptance policy (TYP003)

A hint is a candidate type source plus the basis that justified it.

| Target | Basis | Safety | Accepted when |
| --- | --- | --- | --- |
| Return | `proven_none` | proven | No `return <value>`, no `yield`, no `await`-less generator forms, body is not just `...` / `pass` / `raise NotImplementedError` |
| Parameter | `default_literal` | guarded | Default is a scalar literal (`int`, `str`, `float`, `bool`, `bytes`) and the candidate equals its type |
| Parameter | `call_sites` | guarded | At least one resolved in-module call site; every call site's argument for that parameter has one definite type; it equals the candidate |
| Return | `derived_return` | guarded | The syntax proves the type (literals, operators, comparisons, builtin constructors, typed parameters and single-assignment locals, paths that fall off the end add `None`), the inference proposes the same type, and no return expression depends on an untyped parameter (taint analysis) |

Call-site evidence is only trusted when it is complete. A function whose
name is read anywhere other than as a direct callee (aliased, `map`ped,
`partial`'d, passed as a callback, stored in a container) gets no call-site
hint (`escapes as a value`); a direct call whose arguments cannot be typed
(loop, `with` and comprehension variables) counts as *unknown* evidence, never
as absent; and the analyzer's argument types are cross-checked against what
the argument expression's syntax proves (`True + True` is `int`, not `bool`).
Names rebound through `global` / `nonlocal` are never typed as single-assignment
locals.

Always rejected, with a reason: candidates containing `object`, `Any` or an
unresolved name; names that are neither builtins nor already imported (adding
imports is a later slice); `*args` / `**kwargs`; `self` / `cls`; lambda
parameters; a `None` default (would need `Optional`); candidates where call
sites disagree.

Taint analysis: parameters without an accepted or declared type are tainted;
a local assigned from an expression that mentions a tainted name is tainted
(to a fixpoint); a derived return hint is rejected when any return expression
mentions a tainted name.

**Correction found while building the gold set:** trusting the inference's
expression typing even for typed parameters is not enough. `def keys(d):
return list(d)` called with a `dict[str, int]` was given
`-> list[tuple[str, int]]` (it is a list of keys). A derived return hint is
therefore accepted only when the syntax *proves* the type and the inference
agrees; either source alone is refused. This also refuses some correct hints
(f-string returns, `if a: return 1` falling off the end, which the inference
types as `int`); precision is preferred over recall.

Fixing the underlying inference (`"hi " + name`) is out of scope. The gate
makes it harmless; improving inference is a separate project.

## 4. Fix runner

`fix_source` parses once, collects findings, selects fix offers whose safety is
at or below the requested ceiling, applies them to the one tree in dependency
order, and writes once.

- **Ceiling:** `FixSafety.proven` (safe only), `FixSafety.guarded`
  (safe and guarded). `suggest` and `none` are never applied.
- **Order:** fixes by `before`/`after` relations (topological, ties broken by
  fix key), then subjects in source order. Imports a fix needs are inserted by
  that fix, never by the runner.
- **Conflicts:** an offer whose subject node was already edited in this run is
  skipped with reason `conflict`.
- **Failure isolation:** an applier that raises is skipped with its reason; the
  tree is not left half-edited (appliers mutate only after validating).
- **Write-back:** one `unparse(preserve_formatting=True)`. If it raises
  `FormatPreservationError`, or the result does not parse, degrade to applying
  the fixes one at a time from the current text, keeping each that writes back.
- **Convergence:** up to three rounds, stopping when a round applies nothing or
  leaves the text unchanged; fixes can unlock others (a parameter hint can make
  a derived return hint acceptable).
- **Result:** `FixResult` lists applied fixes, skipped fixes with reasons, the
  findings that remain, and the final text. Never raises on bad input.

## 5. Formatter phase

`format_source` runs `ruff format` once on the final text through stdin, using
the project's configuration. A missing ruff is reported, not fatal.
`fix_and_format` composes the two. astart's output must already be stable, so
ruff makes no semantic change.

## 6. Goals, non-goals, anti-goals

Goals: precise hints, a single-pass runner, comment-preserving output, every
skipped fix explained.

Non-goals: variable annotations, adding imports, fixing the inference engine,
a CLI (shipped in `docs/superpowers/plans/2026-11-07-check-fix-cli.md`), docstring/blank-line/Constants fixers (later slices).

Anti-goals: writing a hint on a guess; a fix that changes behaviour; output that
fails to parse; losing comments.

## 7. Decisions

Mine (please check):
- Two fixes under one rule: `typing.add-none-return` (proven) and
  `typing.add-inferred-annotation` (guarded).
- Rule `TYP003` `typing.missing-annotation` covers parameters and returns only,
  through a new `Parameter` subject kind.
- Candidates from `module.convert(stubs_path=..., apply=False)`; when no stub
  path is given an empty temporary directory is used.
- Equality of types, not subtyping, decides call-site agreement (`int` vs
  `float` disagree), trading recall for precision.

Left to the builder: the exact taint-analysis structure, the degraded-mode
bookkeeping, and ruff invocation details.

## 8. Performance findings (recorded during implementation)

- `module.bind_call` reconciles the whole tree on every call, twice, so binding
  every call of a 2,400-line module took 61 s. Added
  `CommentedModule.bind_calls` / `SemanticAnalyzer.bind_calls` (one
  reconciliation per batch); the rules layer caches one binding map per module.
- A run infers at most once per distinct source text: hints are keyed by source
  position, shared through a per-run `HintCache`, and a stable round's own
  findings are reused as the final report.

## 9. Known limitations

- **Large files are slow.** Time grows faster than linearly: a synthetic
  12,000-line module with 3,000 functions takes about 47 s per run, a typical
  2,400-line module about 3 s. The remaining cost is astart's own semantic
  worklist and repeated tree walks, not the fix layer; it is a core
  inference-performance task for a later slice.
- `self.method(...)` and `Class.method(...)` call sites are not resolved, so
  methods get hints only from default literals and provable returns.
- Recall is deliberately low: negative or computed defaults (`x=-1`,
  `x=1+2`), `try` / `finally` returns, f-string returns, and returns that
  fall off the end where the inference disagrees are all refused.

## 10. Addendum: synthesized types and imports (2026-11-07)

- `typing.synthesize-protocol` (guarded): see `astart.rules.protocols`.
- `typing.synthesize-typevar` (guarded, runs before `add-inferred-annotation`
  so a pass-through parameter is generic rather than pinned to its call
  sites): see `astart.rules.typevars`. Classic `TypeVar` is used, not PEP 695
  syntax, so the output runs on every supported Python.
- `astart.rules.imports` adds missing imports for synthesized annotations and
  allows a fixed list of standard-library names in hints.
- Ordering semantics: `Fix.before` lists fixes *this* fix runs before; the
  `Fix` docstring said the opposite and was corrected.
