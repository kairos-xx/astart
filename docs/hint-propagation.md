# Hint propagation

How `HintIndex` decides which annotations `astart fix` may write. The
machinery lives in `src/astart/rules/hints.py`; this page describes what
the three core methods do and the order the propagation passes run in.
It is a specification, not a change log.

## The pipeline

`HintIndex.create` builds one index per module in four stages:

1. `_candidates` runs the inference pipeline once (`module.convert`) and
   collects the annotation sources it proposes, keyed by node identity.
2. `judge_parameters` accepts or refuses a hint for every unannotated
   parameter — this is where the propagation passes run (below).
3. `judge_attributes` accepts an annotation for each instance attribute
   whose writes all prove the same type, and records the per-class
   attribute types that return judging later trusts for `self.x` reads.
4. `judge_returns` accepts or refuses a return hint for every
   unannotated function: protocol dunders get their declared result when
   the body fits, functions that provably return nothing get `-> None`,
   declarations and generators are refused, and everything else goes
   through `_judge_derived`, which requires the syntax proof, the
   inference candidate and the taint rules to agree.

## The propagation passes

Parameter hints feed each other: once `f(g)`'s parameter is accepted,
the type callers pass to `g` becomes evidence for `g`'s own parameters.
`judge_parameters` therefore loops — at most
`Constants.propagation_passes` (**12**) times — and each pass runs the
same two steps in order:

1. `_call_sites(...)` rebuilds the call-site evidence index. It sees the
   hints accepted so far (`accepted`), so evidence discovered in pass *n*
   is visible to pass *n+1*.
2. `_judge_pass(...)` judges every parameter that does not yet have a
   hint. If at least one parameter gained a hint the loop continues;
   a pass that gains nothing ends the index early (fixpoint), so the 12
   is a cap, not a fixed count.

### `_call_sites`

Builds `dict[(function identity, parameter name), list[_Site]]` — what
each direct call in the module shows about each parameter.

- A call the binder trusts (`BoundCall` with a declaration) contributes
  one `_Site` per bound argument via `_bound_evidence`. An argument the
  binder cannot resolve (`f(*xs)`, `**` expansions) records *unknown*
  evidence — never evidence of absence. A variadic parameter that
  received nothing records nothing.
- A direct `name(...)` call to a function bound exactly once in the
  module but not bindable records an indefinite `_Site` for every one
  of its parameters, so the call counts as unknown rather than missing.
- When a `ProjectView` is present, `_merge_project_sites` appends the
  cross-module call sites the project index recorded for the function's
  qualified name (and for a class, its `__init__`/`__new__` call
  evidence). Ambiguous qualified names contribute nothing.

Each `_Site` carries `definite` (is the argument type trustworthy),
`types` (rendered spellings) and `proven` (does the argument's syntax
alone prove the type, independent of the inference engine).

### `_judge_pass`

One sweep over every function in the module. For each parameter that is
unannotated, not already hinted and not a skipped first parameter
(`self`/`cls`/`mcs`/`metacls`), it calls `_judge` with the inference
candidate, the call-site evidence for `(function, parameter)` and the
default's provable type. Afterwards it calls `_judge_variadics`, which
judges `*args`/`**kwargs` from call-site evidence alone — an inferred
candidate describes the tuple or dict the name is bound to, not the
element type the annotation needs.

Every accepted hint is recorded in `accepted[function][parameter]`,
which is exactly the map `_call_sites` reads on the next pass. The
method returns whether anything was gained, which is the loop's
stop signal.

### `_judge_call_sites`

The last step of `_judge` for a parameter with no literal default. Given
the candidate and the collected evidence it decides:

- the function escapes (used as a value, or open-world in project mode)
  → refuse `escapes as a value`;
- no call sites at all → refuse `uncorroborated`;
- any site is indefinite or proves more than one type → refuse
  `call sites unknown`;
- every site proves exactly the candidate → accept a `call_sites` hint;
- the proven types differ from the candidate → refuse
  `call sites disagree`.

Parameters whose default is `None` take the sibling path
`_judge_optional` instead: every site that passes a value must prove the
same `T`, producing `T | None`.
