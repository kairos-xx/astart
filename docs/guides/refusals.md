# Refusal catalogue — "why wasn't X annotated?"

`astart` refuses rather than guesses. Every skip or refusal uses a
closed vocabulary defined in `src/astart/rules/reasons.py`; no fix is
ever silently dropped. This catalogue explains each reason, what it
means, and what you can do about it.

There are two families:

- **`Rejection`** — the hint engine examined a subject and declined to
  offer an annotation. Reported per subject.
- **`SkipCode`** — a fix was offered and selected, but the runner could
  not safely apply it. Reported per fix.

## `Rejection` — no annotation was offered

| Reason | Meaning | What you can do |
| --- | --- | --- |
| `no candidate` | Nothing in the module proposed a type for the subject — no call sites, no default, no inference signal. | Annotate it by hand; `astart` will not invent a type. |
| `contains object` | The only candidate is or contains `object`/`Any`, which carries no information. | Narrow the type yourself, or leave it unannotated. |
| `uncorroborated` | A candidate exists (inference or default) but no call site confirms it. | Add a typed usage, or raise `--min-confidence`-independent evidence. |
| `call sites disagree` | Different call sites pass different types and no union is allowed. | Enable the union policy, or pick the intended type. |
| `call sites unknown` | A call site's argument type cannot be determined, so it cannot corroborate. | Annotate the *caller* first; then re-run. |
| `default disagrees` | The default value's type differs from the candidate (e.g. default `-2` while calls pass `int` is refused because the default is a `UnaryOp`, not a literal). | Fix the default or annotate explicitly. |
| `None default` | The parameter defaults to `None`; the correct annotation is `Optional[T]`/`T \| None`, which requires the union policy. | Enable unions, or write `T \| None` yourself. |
| `escapes as a value` | The function is used as a value (assigned, returned, decorated, passed), so its callers are unknowable and closed-world evidence does not hold. | Nothing — this is a sound refusal. |
| `generator` | The function yields; the correct annotation is `Iterator[T]`/`Generator[...]`, not `T`. | Write the generator annotation yourself. |
| `declaration body` | The body is `...`/`pass`-style — a stub or overload, not an implementation to annotate. | Keep declarations as-is. |
| `needs import or unknown name` | The candidate needs an import the fixer cannot safely add, or references an unresolvable name. | Add the import; the annotation follows next run. |
| `return type not provable` | Return expressions are too dynamic (f-strings, `.format`, `repr`, `abs`, `**`, empty containers, callee-propagation like `return f(x)`, `is None` widening, `try`/`except` merges) to prove a type from syntax alone. | Annotate the return yourself. |
| `engine disagrees` | The inference engine's proposal contradicts the syntax-level proof; syntax wins and the hint is refused rather than trusting inference alone (E5 never applies alone). | Investigate which is right — usually the syntax. |
| `tainted by parameter` | The returned value depends on an unannotated parameter, so the return type cannot be proven independent of it. | Annotate the parameter first. |

## `SkipCode` — a selected fix was not applied

| Code | Meaning |
| --- | --- |
| `subject-missing` | The node the fix targeted could not be found in the final tree — an earlier round already changed it. |
| `conflict` | Another fix in the same round already edited the node; the loser is skipped. |
| `preconditions-changed` | Facts the fix was offered on no longer hold after earlier edits in the round. |
| `applier-failed` | The fix's applier raised an exception; the fix is skipped, not half-applied. |
| `write-back` | Writing the tree would reformat unrelated code; the whole round is refused to protect formatting. |
| `checker-rejected` | The external checker (pyright/basedpyright, E6) reported a new error after applying; the change is rolled back and reported, never silent. |

## Reading output

- `astart check` reports each `Rejection` in the finding's evidence so
  the unannotated subject is explainable, not silent.
- `astart fix` prints each `SkippedFix` with its code; `checker-rejected`
  is the only reason the whole round is undone.
- To accept more risk, lower `--min-confidence`; to accept fewer kinds
  of fixes, select/ignore rules via the profile. Neither setting ever
  bypasses `checker-rejected` or `write-back` — those are
  non-negotiable correctness guards.
