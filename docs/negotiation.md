# Contract negotiation

`astart.rules.negotiation` types a module by letting evidence travel along a
graph, in both directions, until nothing changes. It supplements the older
hint index (`rules/hints.py`) and is on by default (`--no-negotiate` turns it
off). The idea comes from the author's earlier Semantic Contract Farm project;
this page records how it was adapted for a tool whose rule is *zero wrong
annotations*.

## The model

- A **node** is something that has a type: a parameter (`f.x`), a return
  (`f->`), a local variable, an instance attribute (`C.attr`), an element held
  by a container (`xs[]`), the value of an expression (`f.<BinOp@12:4>`), or
  the narrowed view of a name inside a branch (`f.x#12t`).
- A **contract** is a directed fact between two nodes (`assigns`, `returns`,
  `argument`, `call_result`, `element`, `item`, `instance_field`, `narrows`,
  `list_of`, …) with a polarity: `union` (the type joins), `intersection`
  (narrows), `declaration` (a written annotation, hard), `capability`.
- A **candidate** is a type proposal carrying its **origins** (`syntax`,
  `declared`, `protocol`, `call_sites`, `default`, `calibrated`, `inferred`).
- A **derived node** is an expression over other nodes. Its template has each
  operand replaced by a placeholder, and the syntax typer
  (`provable.expression_type`) evaluates it as soon as every operand has
  settled, so arithmetic, comparisons, f-strings, tuple and list displays and
  builtin calls share one set of rules with the rest of the tool.
- A **belief** is what a node currently holds: candidates (joined as a union),
  constraints from narrowing (applied when the belief settles, so arrival order
  does not matter), a declaration, and conflicts.

The negotiator (`negotiator.py`) is the ant farm: messages move forward over
contracts and backward over declaration and narrowing contracts, decay with
distance, are memoised against wormholes, and stop on no change, an event
cap or an iteration cap.

## The adaptation rule

Confidence only orders and prunes candidates. **Acceptance is decided by
evidence class** (`policy.accept`): every member of the settled type needs a
proof (`syntax`, `declared`, `protocol`), or two different soft signals (call
sites and a default), or one soft signal plus the inference engine proposing
the same type. The engine is corroboration, never a source of types, and a
`None`-only result needs a proof. Nothing opaque is ever accepted, and opacity
spreads to everything downstream.

## Soundness rules (each one was a bug found by a test)

1. **Missing evidence is not absence.** A node that feeds another but has no
   seed and no incoming contract is *opaque* (`_starved`); a transfer that
   yields nothing for a union contract marks its target *lost*
   (`Negotiation.lost`). Otherwise the one `None` among three writes would
   settle an attribute.
2. **Single binding only.** A name bound twice, by `global`/`nonlocal` (also in
   a nested function), `del`, an import, a handler, a rebound parameter or a
   rebound `self` gets no node, and its readers are unaccounted.
3. **Containers are typed only while every use is understood.** `append`,
   `insert` and `add` join the element type; `extend`, passing the container
   on, a closure or a dict store make it opaque. A mutable container held in an
   attribute that some method uses in an unknown way is opaque.
4. **Join, then wrap.** A container's type is the union of its elements,
   computed first and wrapped second; the wrapper replaces its earlier value
   (a candidate `slot`), or `[1]` plus `append("s")` would be
   `list[int] | list[str]`.
5. **Stubs, abstract bodies, generators, `NoReturn` and constructors** are not
   body-derived: a constructor call is the class (never a generic class), an
   un-awaited coroutine is not its awaited type, a protocol dunder takes the
   protocol's declared result when its body fits.
6. **Binding trust.** A *read* of `globals()` does not rebind names; a store,
   `update`, an alias, `exec` or `eval` does (`MethodIndex._only_reads`).

## Using it

| Where | What |
| --- | --- |
| `astart fix` | parameter and return hints supplement the hint index (`--no-negotiate` off); `--annotate-variables` writes `name: T = value` for locals (automatic in modules that already annotate some) |
| `python -m benchmarks.shadow DIR` | runs both approaches on stripped modules and scores each against the originals |
| `python -m benchmarks.pair UNTYPED TYPED` | converts an untyped module and scores it against its typed twin |
| `tests/test_gold_expansion.py` | `test_gold_negotiation_is_a_reviewed_superset`: negotiation never changes what the hint index writes, and every addition is listed |

## Extending it

- **A new contract builder** goes in `builders.py`: turn the syntax into
  `Contract`s and seeds, and call `_block(path=…, why=…)` for anything you
  cannot account for. Prefer a derived node over a new relation when the
  syntax typer already knows the rule.
- **A new transfer rule** goes in `transfer.py` (`forward`/`backward`). A
  relation with no sound reverse returns `None`; do not guess. A forward
  `None` marks the target lost.
- **A new origin or acceptance rule** goes in `model.py` and `policy.py`, with
  a test in `tests/test_negotiation_module.py` that fails without it.
- Run `python -m benchmarks.shadow tests/corpus_ext --jobs 8`; the negotiation-
  only group must keep **0 wrong**, and the gates in `docs/benchmarks.md`
  must pass.
