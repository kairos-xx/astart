# Narrowest-typing program — umbrella design

Status: draft for approval, 2026-11-11.

This document covers the whole program. Each of the seven projects listed
below gets its own design document, brainstormed and approved one at a
time, before it is planned or built. This umbrella fixes what they share:
the objective, the yardstick, the rules every project obeys, and the order.

Statements marked **(builder's call)** were proposed by the assistant and
not decided by the owner. The owner may still override them.

## 1. Intent

`astart fix` should turn an untyped module into the module a careful human
would write by hand. The hand-typed references are `fixtures/typed.py` and
`fixtures/v2/typedv2.py`, produced from `fixtures/untyped.py` and
`fixtures/v2/untypedv2.py`.

Today the output falls well short. Measured on v2 (2026-11-11):

| Measure | `resultv2.py` | `typedv2.py` |
|---|---|---|
| Parameters annotated | 211 / 304 | 315 / 315 |
| Return types | 198 / 280 | 281 / 281 |
| Annotated locals (`AnnAssign`) | 88 | 275 |
| Docstrings | 61 | 275 |
| Type aliases | 6 | 45 |

Of the parameters present in both files, 145 match the reference exactly
and 141 differ. The gap falls into four kinds:

1. **Types written in docstrings are ignored.** 86 parameters and 80
   returns are missing; many of these are stated in `Args:`/`Returns:`
   sections (`google_style`, `numpy_style`, `rest_style`, `github_style`).
2. **Over-abstract protocols.** The output uses `SupportsSplit` where the
   reference uses `str`, `SupportsGe` where it uses `int`, and
   `T2`/`SupportsRadd` where it uses `float`. The engine stops at the first
   capability it sees instead of combining all the evidence.
3. **Alias naming and reuse.** The output writes `ListStr` where the
   reference uses `StringList`, and `int | None` where it uses
   `OptionalInt`. It also misses generic aliases such as `dict[K, V]`.
4. **Coverage.** Locals and docstrings are mostly missing, and the v1 run
   (`fixtures/result.py`) is byte-identical to its input.

The owner has an older 23k-line script, `src/astart/semantic_core_original.py`,
which they are reformatting to current conventions without changing its
logic. **Everything in it is to be implemented in the project, spread
across existing or new modules, with improvements on top.** The script
itself is not a project file. It is a source of ideas and will be removed
once its content has been absorbed.

## 2. Objective (owner's definition)

Besides formatting, docstrings, import conversion, `aprint` and the
pipeline's other existing steps:

- **Every variable, argument and return is type hinted** in the narrowest
  way the observable static evidence allows.
- **The output has zero basedpyright (strict) and Ruff diagnostics**, with
  no suppressions. **(builder's call)** The check is basedpyright strict
  plus Ruff, using this repository's `pyproject.toml` configuration, run
  on the generated module. The rest of the `exactus` gate (README
  inventories, coverage) applies to astart's own code, not to converted
  output.

### 2.1 Fallback order (owner's rules)

When the evidence does not yield a single concrete type, try these in
order and stop at the first that is sound for every observed use:

1. a concrete nominal type (`str`, `float`, `TreeNode`)
2. a union of concrete types
3. a generic: a synthesised `TypeVar` or `ParamSpec`
4. a synthesised `Protocol`
5. `object`, only when narrowing is genuinely impossible
6. `cast`, only as a last resort

`typing.Any` is strictly forbidden. It may never be emitted, at any stage
of the pipeline.

**Narrowest** means: for a return, the most specific type of everything
that flows out. For an argument, the most specific type that still accepts
every observed caller, default and internal use. A protocol is only earned
when the uses span unrelated types. One capability seen once does not earn
a protocol.

### 2.2 Evidence

The evidence is everything statically observable:

- assignments and defaults
- use sites and operators
- callers, including callers in other files
- stubs (typeshed and project stubs)
- `isinstance` and other narrowing
- docstring type fields
- existing annotations

No code is executed.

### 2.3 Synthetic type aliases (owner's rules, from `typedv2.py`)

- A type expression that repeats gets a synthetic `type` alias.
- **The number of aliases is minimised by nesting.** Aliases are expressed
  in terms of other aliases, as in `StringCountPairs = list[StringIntPair]`
  and `JSONObject = dict[str, JSONValue]`. A sub-type shared by several
  aliases is aliased once, and they all reuse it. The selection is global
  per module: it is an optimisation over all hints at once, not a decision
  made one hint at a time.
- **(builder's call)** The threshold is 3 occurrences, counted directly
  or through the aliases built on the sub-type. This matches every alias
  in `typedv2.py`: `TupleIntStrSet` has 2 direct uses and is the building
  block of an alias used 3 times.
- Recursive aliases (`JSONValue`) and generic aliases (`KToTListMap =
  dict[K, list[T]]`, `PToRCallable = Callable[P, R]`) are allowed.
- Names:
  - Use a meaning-based name when the code reveals one (`JSONValue`,
    `ParsedIntegers`, `StrCounter`).
  - Otherwise use a structural name from a fixed grammar:

    | Pattern | Example |
    |---|---|
    | `Optional<X>` | `OptionalInt` |
    | `<X>List` | `FloatList` |
    | `<K>To<V>` or `<K>To<V>Map` | `StringToInt` |
    | `Tuple<A><B>…` | `TupleIntStrSet` |
    | `<A>Or<B>` | `FloatOrStr` |
    | `<Arg>To<Ret>Callable` | `IntToIntCallable` |

  - Nested aliases keep their names inside the outer name
    (`StrToOptionalStringMap`).
- An alias that already exists in the module or project is reused, never
  duplicated.

## 3. Yardstick

`scripts/compare` already scores `astart fix` output against
`fixtures/typed.py` in one in-process session, producing
`conversion-report.{md,json}`.

- Every project ends by running it on **both** fixture pairs (v1 and v2).
  It records annotation agreement, alias agreement, docstring agreement
  and the zero-diagnostics result.
- **(builder's call)** A project is accepted only if its run shows no
  regression on either pair and moves its own target metric:

  | Project | Target metric |
  |---|---|
  | 1 One tree | remaining emit/re-parse sites; losslessness tests |
  | 2 Identity | unresolved-name count |
  | 3 Semantic graph | edge coverage |
  | 4 Docstrings | docstring agreement |
  | 5 Inference | annotation agreement |
  | 6 Synthesis | alias agreement |
  | 7 Query | query coverage |

  Projects 1, 2, 3 and 7 are infrastructure. They are not expected to
  change the conversion report.
- **(builder's call)** The baseline is recorded at the start of project 1
  from a committed source state, with the exact `scripts/compare`
  invocation, for both pairs. The compare tool defaults to v1 only today.
  Making v2 a first-class default is part of project 1.
- **(builder's call)** Both fixture pairs are single modules, so they
  cannot measure cross-file evidence. Project 2 adds a small multi-module
  fixture package for that.
- Two equally narrow spellings, for example `int | None` and
  `OptionalInt`, are decided by the alias rules in §2.3. The comparison
  should report them as alias disagreements, not as type errors.
- The v1 no-op run (`result.py` identical to `untyped.py`) must be
  explained and fixed before project 1 is accepted, because a pipeline
  that silently emits its input invalidates the yardstick.

## 4. Rules shared by every project

- **One tree.** Source is parsed once into astart's custom mutable AST.
  After that there is only tree manipulation, and one final emit produces
  the code string.
- **Fragment reformatting is the only round-trip.** External tools such as
  `ruff format` may format fragments, for example code inside f-strings.
  The re-parsed fragment must keep the original nodes' identities and
  custom properties. If the tool changes meaning or structure, the
  minimum region is re-analysed to keep the tree coherent, and what was
  recomputed is recorded. This is never a silent failure.
- **Losslessness.** A region nobody edited emits byte for byte as it was
  read.
- **Cross-file identity.** A symbol id is shared by every node that refers
  to the same object, across modules. That includes the definition, its
  uses, import aliases, re-exports, docstring entries and type hints that
  name it.
- **Merge, don't add.** The project already has overlapping stacks:
  - `semantic/` (identities, scopes, type inference, stubs)
  - `graph/` (backend, inference, conversion)
  - `rules/negotiation/` (beliefs, algebra, negotiator)
  - `stubs/`

  For each idea taken from `semantic_core_original.py`, the project design
  names the single module that ends up owning it. The overlapping
  implementation is removed in the same project. No project may leave a
  fourth parallel stack.

  **(builder's call)** The same rule covers the other overlaps: the
  `docstrings/` package (project 4), `transforms/aliases.py` and
  `alias_patterns.py` (project 6), `graph/stubs` and `graph/inference`
  (projects 2 and 5), and the parse paths beside `source/ast.py`
  (project 1). The end state is one home per concern.
- **Script inventory.** **(builder's call)** The script has about 380
  classes, and the table in §5 names only the main ones. Each project's
  design lists every script class it absorbs. A class that no project
  takes is listed as dropped, and a drop needs the owner's approval. The
  script is cited by class name, not line number, because it is still
  being reformatted.
- **Project standards apply in full** (`AGENTS.md`): strict typing, no
  `Any`, no suppressions, keyword arguments, Google docstrings, README
  inventories, coverage ≥ 90% total and ≥ 80% per file, and a passing
  `exactus` gate.

## 5. Projects and order

The order follows dependencies: each project needs the one before it.

| # | Project | Delivers | Script material absorbed |
|---|---|---|---|
| 1 | **One tree** | One parse into the custom AST; formatting held as nodes (quotes, parentheses, comments, blank lines); per-node token view; the ~135 mid-pipeline emit/re-parse sites removed; fragment reformat with identity reconciliation | `TokenizedAstParser`, `QuotedConstantNode`, `ParenthesizedExpressionNode`, comment preservation, `TokenAwareUnparser` |
| 2 | **Identity** | Path-based symbol ids (`astart.source.ast.CommentedModule.emit.source`, with sibling ordinals for rebinding); import, relative-import, re-export and stub resolution across files; unresolved names marked with a reason | `TraceableQualifiedPath`, `TraceableSiblingOrdinalState`, `LocalImportInspector`, `UnifiedSymbolCatalog` |
| 3 | **Semantic graph** | Typed edges on the tree: defines, uses, assigns-from, returns, has-type-hint, argument-to, narrowed-by; usage kinds; value flow through containers and attributes | `SemanticEdgeKind`, `SemanticUsageKind`, `TraceableValueRelation`, `AdvancedSemanticUsageAnalyzer` |
| 4 | **Docstrings** | Docstrings decomposed into nested nodes: sections, entries, paragraphs, nested lists keeping their marker kind, inline code, code examples, doctests, titles, citations, and URLs with their own sub-tree. Entry names and types are linked by id to the real arguments, returns, raises and classes | `ExistingDocstringParser`, `DocstringEditor` |
| 5 | **Inference** | One engine combining all evidence: propagation forwards and backwards, typeshed seeding, contract negotiation and belief algebra, and explanations for every decision. Applies the fallback order in §2.1 | Swarm propagation, Markov explanations, `TypeBelief`, `ContractNegotiator`, `TypeEvidenceSolver`, typeshed catalog |
| 6 | **Synthesis** | Protocol, `TypeVar`, `ParamSpec` and alias synthesis, with the global alias minimisation from §2.3; import placement; `cast` only as a last resort; editing helpers | `ProtocolGrammar`, `TypeAliasManager`, `CollectiveTypeHintObjectiveSolver`, `UsageAwareImportCollector`, easy editors, comparison-int constants |
| 7 | **Query** | A chainable navigation surface over the tree, ids and edges | AntFarm query/collections |

The inference ideas in the script also cover advanced features: TypedDict,
NamedTuple, `match`, walrus, comprehensions and async protocols. Each one
lands in project 3 (recognising it) and project 5 (typing it).

## 6. Non-goals

- Running code to infer types.
- Keeping `semantic_core_original.py` as a module, or importing from it.
- Preserving today's internal APIs when merging stacks. **(builder's
  call)** The public CLI (`astart fix`) and its flags stay stable. Internal
  module boundaries may change.

## 7. Anti-goals (would be a failure even if the output type-checks)

- Any `Any`.
- A hint wider than the evidence: `object` when narrowing was possible, or
  a one-use protocol where a concrete type fits.
- A hint the evidence doesn't support, so the output type-checks only by
  luck.
- A `cast` or suppression used only to silence the checker.
- A fourth inference stack beside the existing ones.
- A pipeline that silently emits its input unchanged.

## 8. Left to each project's design and builder

- Exact node classes, module placement, and which existing module absorbs
  each script idea.
- The cost function behind alias minimisation and fallback choice.
- Performance budgets, measured against today's run on the fixtures.
