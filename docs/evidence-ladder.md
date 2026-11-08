# The evidence ladder — how `astart` decides a fix is safe

Every fix `astart` offers is backed by a level of evidence, and every
guarded fix requires a *combination* of levels — never inference alone.
The ladder is defined in `docs/TODO.md` §2 and enforced by
`src/astart/rules/hints.py` + `src/astart/rules/confidence.py`.

## The levels

| Level | Name | What it is | Can it apply a fix alone? |
| --- | --- | --- | --- |
| **E0** | syntax-proves | The type is provable from the syntax itself: a literal default, an explicit `return None`, a `+`/`/` operator on known operands. | Yes — `proven` fixes, confidence 1.0. |
| **E1** | declared-elsewhere | A stub (`.pyi`), base-class signature, `@overload`, or implemented ABC already declares the type. | Yes — also `proven`. |
| **E2** | closed-world usage | Every call site in the module agrees, and the function cannot escape (not assigned, returned, decorated, passed). | Only with E5/E0/E6 — corroborates a candidate. |
| **E3** | cross-module call sites | Call sites in *other* modules agree on the type. | Only with E5/E0/E6. |
| **E4** | library signature flow | A stdlib/typed-library signature (typeshed, `libkw` table) flows the type in. | Only with E5/E0/E6. |
| **E5** | inference proposal | The `_graph`/`semantic` engine *proposes* a candidate. | **Never alone** — it only corroborates. |
| **E6** | checker does not object | pyright/basedpyright reports no new error after the fix. | Final gate — veto only. |

## The acceptance rule

A **guarded** fix needs **(E2 ∨ E3 ∨ E4) ∧ (E5 agrees ∨ E0 proves) ∧
E6 does not object**.

In words: real usage must exist, that usage must agree with either the
inference engine or a syntax proof, and an independent checker must not
complain. Inference can never act alone — this is what prevents the
`Sequence[int]`-for-`str`-parameter class of wrong annotation.

A **`proven`** fix needs only E0 or E1; it is applied at confidence 1.0
and is what the default profile accepts.

## Confidence values

`src/astart/rules/confidence.py` maps evidence to a number:

| Basis | Confidence |
| --- | --- |
| `proven` (E0/E1) | 1.0 |
| `proven_none` return | 1.0 |
| `default_literal` | 0.99 |
| `call_sites` | 0.95 |
| `derived_return` | 0.90 |
| `calls.add-keywords` | 0.95 |
| `typing.synthesize-*` | 0.90 |
| unlisted guarded fix | 0.90 (fallback) |

`--min-confidence` filters offered fixes; it can never promote an
E5-only candidate or bypass the E6 checker gate.

## What this means for you

- **`astart` is conservative by design.** Low recall is expected —
  preferring a correct `T` for a few parameters over a wrong `Sequence`
  for all of them.
- **Unannotated ≠ broken.** Each unannotated subject carries a
  `Rejection` reason (see `docs/refusals.md`) explaining which rung of
  the ladder was missing.
- **To raise recall**, enable the union policy, annotate callers first
  (so call sites become typed), or install a checker so E6 can confirm
  guarded fixes.
