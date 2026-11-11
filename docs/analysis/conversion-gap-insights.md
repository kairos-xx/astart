# Conversion gap analysis: `fixtures/untyped.py` → `fixtures/typed.py`

Date: 2026-11-15. Tree: working tree at analysis time (TODO generated block
reports reference `79ce83548ccf`).

This document is complementary to `docs/planning/TODO.md`. The TODO lists *what*
to build; this document records *what is actually missing*, measured against the
three real artifacts, and maps each gap to the code that would have to change.
Every number below was recomputed from
`scripts/compare/artifacts/results/conversion-report.json` or from a fresh AST
diff of the three files — not copied from the generated report prose.

Artifacts compared:

| File | Lines | Role |
| --- | ---: | --- |
| `fixtures/untyped.py` | 2,725 | input |
| `fixtures/typed.py` | 5,811 | hand-curated reference |
| `scripts/compare/artifacts/results/result.py` | 4,320 | current engine output |

The compare run used `rules.fix_source` with
`FixSettings(ceiling=guarded, min_confidence=0.5, annotate_variables=True,
negotiate=True, engine=True)` and **no checker**
(`scripts/compare/conversion_report.py:2718-2732`). Everything the reference has
that this settings object does not request — `create_constants`,
`stub_docstrings`, `accept_general`, `runtime_protocols`, PEP 695 emission,
alias optimization — is off by construction in the measured run.

---

## 0. TL;DR

The gap to `typed.py` is not "more inference". It is four missing layers plus a
set of concrete defects:

1. **A declaration layer.** `typed.py` is 34% larger than `result.py` almost
   entirely because it declares 117 type aliases, 21 `TypedDict`s, 5
   `NamedTuple`s, 17 real `Protocol`s, a `Constants` class, and a canonical
   TypeVar/ParamSpec block — and then *spells every annotation with those
   names*. `result.py` emits zero aliases, zero TypedDicts, zero NamedTuples,
   promotes zero stub classes to `Protocol`, groups zero constants, and emits
   four ad-hoc per-function `TypeVar`s instead of the shared binder block.
   `transforms/aliases.py` (`AliasOptimizer`) previously ran only under the
   opt-in `astart transform --optimize-aliases` path; it is now wired into
   `fix_source` as a default-on post-pass (`FixSettings.optimize_aliases`,
   `--no-optimize-aliases` opt-out, skipped below Python 3.12 targets).

2. **Contract-first annotation policy.** Where the author could not name a
   type (function-local classes, heterogeneous dict returns, callable
   objects), `typed.py` synthesizes a *named contract* — a `Protocol`, a
   `TypedDict`, a `type`-alias, a generic alias — and annotates with the name.
   The engine instead spells the concrete shape (`dict[str, int]`,
   `HybridContainer`, `Callable[[int], Awaitable[int]]`). Roughly 60% of the
   "missing" and a large share of the "wrong"/"narrower"/"unresolved" verdicts
   are downstream of this one policy difference, not of missing evidence.

3. **Style/idiom migration that is currently unscored.** `typed.py` rewrites
   nine bare `import x` modules into usage-driven `from x import name` form
   (IMP001, M8-27), keyword-ifies call sites, normalizes raise messages to
   `msg` (S-08), adds `_ =` discards, inserts `cast(...)` where the declared
   contract needs it, converts `@dataclass(init=False)`+manual `__init__` into
   a real dataclass, and promotes four `Supports*` stub classes to `Protocol`.
   None of this is measured by the conversion report, so progress on it is
   invisible today.

4. **Writer hygiene defects in `result.py` itself.** Synthesized protocols are
   glued to the preceding function with no blank lines (8 sites),
   `T = TypeVar('T')` statements are glued after function bodies with single
   quotes and positional args (4 sites, vs the house `TypeVar(name="T")`
   double-quote kwargs style), 51 lines exceed 79 columns (max 213), five
   docstrings close glued to text, and variable annotation re-annotates the
   same name up to three times in one function (8 functions) where the
   reference declares the union once and then assigns bare.

On top of that sit the inference gaps the TODO already tracks (unprovable
calls, escaping functions, container element-vs-parameter confusion,
interprocedural summaries). Those remain necessary — but they are the *smaller*
half of the distance to `typed.py`.

---

## 1. Measured baseline

### 1.1 Annotation verdicts (`conversion-report.json`, `to_recover` scope)

Parameters + returns — 471 recoverable targets:

| Exact | Compatible | Narrower | Looser | Unresolved | Wrong | Missing | Extra | Ref-only |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 157 (33.3%) | 32 | 42 | 6 | 36 | 8 | 190 | 15 | 28 |

Variables — 294 recoverable targets:

| Exact | Compatible | Narrower | Looser | Unresolved | Wrong | Missing | Extra | Ref-only |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 88 (29.9%) | 77 | 21 | 5 | 2 | 12 | 89 | 13 | 198 |

"Same type" (exact + compatible) is 40.1% params / 56.1% variables. Exact
spelling is what the 90% goal measures.

### 1.2 Declaration/artifact verdicts

| Kind | Exact | Changed | Missing | Extra |
| --- | ---: | ---: | ---: | ---: |
| docstrings | 125 | 209 | 89 | 40 |
| type aliases | — | — | **117** | 0 |
| protocols | — | — | 17 | 8 |
| typevars | — | 1 | 51 | 3 |
| paramspecs | — | — | 6 | 0 |
| typevartuples | — | — | 0 | 0 |
| classes | 18 | 46 | 24 | 6 |
| declaration uses | — | — | 134 | 8 |

`output_only_classes` = the eight shape-fragmented dunder protocols the engine
invented: `SupportsAddition`, `SupportsAddition2`, `SupportsRadd`,
`SupportsLeAndMultiplicationAndSub`, `SupportsMultiplication`,
`SupportsMultiplication2`, `SupportsGtAndRmul`, `SupportsUpper`.

### 1.3 Opacity (report's own section)

Parameters + returns, 546 nodes: settled 92, unsettled/no-evidence 87,
downstream-of-blocked 76, declared 63, unprovable Name 46, no-evidence-reaches
34, unprovable Call 32, escapes-as-value 28, stub/abstract/never 20,
unbindable call 16, unprovable Tuple 11, Dict 9, BinOp 8, generator 7,
Attribute 5, List 4, Subscript 2, DictComp 2, protocol-fit 2, default 1,
ListComp 1.

Local variables, 292 nodes: downstream-of-blocked 99, settled 84, unprovable
Call 56, container-mutated 32, Name 6, unsettled 4, Attribute 3, Tuple 2,
BinOp 2, container-unknown-way 1, Yield 1, List 1, Await 1.

Reading: ~40% of parameter/return nodes are already *settled* or *declared* —
the engine knows the type but cannot express it in the author's vocabulary
(alias/protocol/carrier names), or the node sits downstream of one blocked
producer. The direct-evidence gaps (Call 32, Name 46, escapes 28, no-evidence
34) are the inference burn-down the TODO already schedules.

### 1.4 AST feature census (all defs/classes incl. nested)

| Feature | untyped | result | typed |
| --- | ---: | ---: | ---: |
| `AnnAssign` total | 0 | 231 | 540 |
| bare declarations (`x: T`, no value) | 0 | 0 | 177 |
| `self.x: T = ...` in methods | 0 | 0 | 47 |
| unannotated args | 283 | 127 | 8 |
| defs without return annotation | 231 | 111 | 0 |
| `@overload` | 0 | 0 | 26 |
| `@override` | 0 | 0 | 17 |
| PEP 695 type params (`def f[T]`, `class C[T]`) | 0 | 0 | 21 |
| `class ...(Protocol)` | 0 | 8 | 17 |
| `class ...(TypedDict)` | 0 | 0 | 21 |
| `class ...(NamedTuple)` | 0 | 0 | 5 |
| `type X = ...` alias statements | 0 | 0 | 117 |
| `TypeVar(...)` calls | 0 | 4 | 7 |
| `ParamSpec(...)` calls | 0 | 0 | 1 |
| `cast(...)` calls | 0 | 0 | 12 |
| `Constants.x` attribute uses | 0 | 0 | 19 |
| docstrings with `Args:`/`Returns:`/`Yields:`/`Raises:`/`Attributes:` | 0 | 162/221/5/6/0 | 172/242/7/9/16 |

Top-level shape: untyped has 8 bare `import` + 13 `from` imports, 5 assigns,
35 classes, 140+2 functions. typed has 22 `from` imports (0 bare), a
`TYPE_CHECKING` block, 8 assigns, **117 `TypeAlias` statements**, 70 classes,
147+2 functions. result has 14 `from` + **all 8 bare imports retained**, 3
`AnnAssign` module constants, 6 assigns, 43 classes, 140+2 functions.

---

## 2. What `typed.py` actually is

`typed.py` is not "untyped.py plus annotations". It is a differently organized
file that shares most function bodies. Its added structure, in canonical order:

1. **Module docstring** rewritten (author prose — unrecoverable, accepted
   deviation).
2. **Import normalization**: every bare `import asyncio/json/math/operator/re/
   tempfile/uuid/importlib` became `from x import <used names>`; `weakref`
   gained `ReferenceType`; a redundant `if TYPE_CHECKING: from types import
   ModuleType` block exists (deliberate, exercises M3-09/S-01/S-02).
3. **TypeVar/ParamSpec binder block** (typed.py:79-86): `P`, `R`, `T`, `U`,
   `V`, `W`, `K`, `N` — classic `TypeVar(name="T")` kwargs style, declared
   once, shared module-wide; `N` is constrained `(int, float, complex)`.
4. **117 `type X = ...` aliases** (typed.py:89-256) with a bespoke naming
   grammar: container+args PascalCase (`ListInt`, `DictIntInt`,
   `SequenceValue[T]`), `|`→`Or` (`IntOrStr`, `ValueOrNone[X]`,
   `ValueOrOther[A,B]`), `None`→`None` (`IntOrNone`), variadic→`Variadic`
   (`TupleIntVariadic`, `TupleValueVariadic[X]`), `type[X]`→`TypeValue[X]`/
   `TypeObject`, `Callable` special forms (`CallableParametersToResult[**P,R]`,
   `CallableValueToResult[V,R]`, `CallableIntInt`, `CallableStr`), and `str`
   keys **elided** in dict aliases (`DictInt` = `dict[str,int]`, but
   `DictIntInt` = `dict[int,int]` keeps the non-str key).
5. **21 `TypedDict`s** (typed.py:258-455): one per fixed-key dict shape —
   including generic `CallablePayload[T]`, recursive `RecursiveRoot`/
   `RecursiveChild` (mutually referential — needs forward refs), and the
   remarkable `TestCallsPart1/2/3` + `TestCallsResult` / `ExtendedResultsPart1/
   2/3` + `ExtendedTestResult` decomposition, where `{**part1(), **part2(),
   **part3()}` return dicts became per-function TypedDicts joined by
   multiple-inheritance TypedDicts.
6. **`@final class Constants`** (typed.py:535-553): groups all five module
   constants (`threshold`, `max_value`, `min_length`, `extended_sentinel`,
   `extended_context`) as lowercase `Final` attributes and rewrites 19 use
   sites (`Constants.max_value`).
7. **17 `Protocol`s** (typed.py:557-736): semantic, role-named contracts —
   `SupportsCall`, `SupportsCall2` (overloaded `__call__`),
   `SupportsCallAndFromValues` (bundles `__call__` + classmethod
   `from_values`), `SupportsApplyAndOffset`, `SupportsNameAndPath` (a *module*
   shape for `os.path`!), `SupportsJoin`, `SupportsInstance[ValueT]`,
   `SupportsValue` (property), `SupportsMatrixMultiplicationAndData`,
   `SupportsAdditionAndXAndY`, `SupportsMetadataAndName`, `SupportsExecute`,
   `SupportsAction`, `SupportsUpdate`, `SupportsInitializedByMeta`,
   `SupportsNewMethod`, `SupportsClassMethodAndInstanceMethodAndStaticMethod`.
   Four of these are promotions of untyped's `Supports*` stub classes; two
   renamed stubs (`SupportsExecuteInt`→`SupportsExecute`, `SupportsVector`→
   `SupportsAdditionAndXAndY`).
8. **Classes with real generics**: `class ExtendedResult[PayloadT]`,
   `class DescriptorWithOwnerCache[ValueT]`, `class HybridContainer[ItemT,
   NamedT]`, `class CallableObject` with `def __call__[ValueT]`,
   `RegistryMeta.__call__[InstanceT: RegistryBase]` (PEP 695 bound),
   `function_with_mutable_default_like_pattern[ItemT: Hashable]`,
   `function_with_type_reassignment_maze[PayloadT]`, `function_with_literal_
   mode_dispatch`/`complex_boolean_narrowing` with `@overload` sets.
9. **Decorators**: 26 `@overload` (descriptor `__get__`/`__getitem__`/
   `__setitem__`, `FluentBuilder.build`, `function_with_generic_types`,
   `optional_function`, `literal_mode_dispatch`, `boolean_narrowing`),
   17 `@override` (every override incl. dunders), `@dataclass(slots=True)`
   replacing `init=False`+manual init, `field(default_factory=list)`.
10. **Docstrings** in Google style with `(type)` after each parameter name, a
    blank line before closing `"""`, `TODO.` placeholder summaries on
    undocumented synthesized defs, and `Attributes:`/`Raises:`/`Yields:`
    sections.
11. **Idioms**: `cast(typ=..., val=...)` kwargs-style (12×), `_ =` discards for
    unused results (~15 sites), `msg` raise-message variable (S-08, ~1 site),
    keyword-ified call sites where provable (`run(main=...)`,
    `observer.update(message=message)`, `apply(value=5)`), selective refusal
    where not (`add_five(number)` stays positional — partial's signature is
    unknown).

---

## 3. Layer coverage: what `result.py` produces today

| Layer | typed.py | result.py | Coverage |
| --- | --- | --- | --- |
| imports normalized to from-imports | 22 from, 0 bare | 14 from, **8 bare kept** + redundant `from uuid import UUID` | ~25% |
| type aliases (`type X =`) | 117 | **0** | 0% |
| TypedDicts | 21 | 0 | 0% |
| NamedTuples | 5 | 0 | 0% |
| Constants class + use rewrite | 1 class, 19 uses | 3 `Final` module assigns, 0 uses rewritten | ~0% |
| Protocols (semantic) | 17 | 0 (8 shape-fragmented dunders instead) | 0% |
| Protocol promotion of stubs | 4 promoted + 2 renamed | 0 (kept as plain classes *and* added 8 new) | 0% |
| TypeVar/ParamSpec block | 8 shared binders | 4 per-function `T/T2/T3/T4` | wrong shape |
| PEP 695 type params | 21 | 0 | 0% |
| `@overload` / `@override` | 26 / 17 | 0 / 0 | 0% |
| `cast(...)` | 12 | 0 | 0% |
| `self.x: T` attribute annotations | 47 | 0 | 0% |
| bare union declarations for redefinitions | 177 total bare decls | 0 | 0% |
| docstring `(type)` in Args/Returns | yes | no | 0% |
| `Attributes:`/`Raises:`/`Yields:` sections | 16/9/7 | 0/6/5 | partial Raises/Yields |
| kwargs call repair | several sites | 1 (`__import__(name=...)`) | ~10% |
| `_ =` discards | ~15 | 0 new | 0% |

Bottom line: `result.py` is a competent *annotator* — it fills signatures and
local variables with concrete types and writes Args/Returns docstrings. It has
no *declaration synthesis* and no *contract layer*, which is where most of
`typed.py`'s mass and most of the exact-spelling gap live.

---

## 4. The body-divergence finding

Normalizing away annotations, docstrings, `Constants.x`→`X`, and bare-module
attribute access (`json.dumps`→`dumps` etc.), then diffing function bodies:

- 372 definitions common to untyped and typed; **68 have real body differences**.
- `result.py` differs from `untyped.py` in **exactly one** body:
  `__import__('os.path')` → `__import__(name='os.path')`. Everything else in
  `result.py` is untyped verbatim plus annotations/docstrings.

The 68 diffs split into:

**Recoverable-by-annotation (~10):** typed introduces named locals that carry
the new types — `children: ListRecursiveChild`, `values: ListInt`,
`first: IntOrFloat`, `events: ListStr`, `name/amount` walrus locals, bare
`evolving_value: IntOrStr | ListInt | DictInt` union declaration. These are
exactly W-12/W-14/G-10 territory and mostly *are* scored (they show up as
missing/wrong variables).

**Author idiom — not recoverable from untyped (~25), candidates for
`accepted_deviations.json` (G-08):**

- `function_with_kwargs`: `*args` param **deleted** + its loop removed + call
  site rewritten to all-keyword. A signature *narrowing* no evidence supports.
- `BuiltinMethodDict.get`/`update` methods **deleted** (typed's class is
  empty); consequently `custom_dict.update({'b': 2}, c=3)` call sites changed.
- `function_with_literal_mode_dispatch`: `handlers` dict dispatch **replaced**
  by an if-chain (which then received 3 `@overload`s).
- `union_function`: `isinstance(value, str)` → `if value:` truthiness check.
- `decorator.wrapper` / `CallableObject.__call__` / `preserve_signature_
  decorator.wrapper` / `complex_boolean_narrowing`: `isinstance`/`cast`
  guards **added** so the ambitious declared types stay honest.
- `error_message` → `msg` rename (S-08, ~1 site); `Node(offset=...)` →
  `Node(name=...)` **parameter rename** on a function-local class (the
  fixtures genuinely diverge — untyped's `Node.__init__` takes `offset`).
- `10` → `0b1010`, `20` → `0b1100` binary-literal style (2 sites).
- `evolving_value = None` initializer deleted; `initialized = instance`
  temp inlined; `dynamic_cls` temp replaced by `setattr(cls, 'new_method', ...)`.
- Module docstring rewritten; `supports*` stub classes promoted/renamed.

**Kwargs-style normalization (~15):** `run(args=...)` → `run(main=...)`
(**wrong keyword repaired** — `args` is not an `asyncio.run` parameter; a
planted bug astart missed), `apply(5)`→`apply(value=5)`,
`fetch(sum(values))`→`fetch(value=sum(values))`,
`update(message)`→`update(message=message)`, `handle(request)`→
`handle(request=request)`, `add(child=...)`, `super().__new__(cls=cls)`,
`__import__(name='os.path')`. Typed refuses exactly where the callee is
unknowable (`add_five(number)` on `functools.partial`, `d.append(4)` on deque
is kept positional in typed too — wait, `d.append(4)` stays positional in
typed; the rule is "keyword only when the signature is known and the
parameter is positional-or-keyword").

Implication for the 90% target: even a *perfect* inference engine cannot
recover the author-idiom diffs. They must be enumerated in
`fixtures/artifacts/accepted_deviations.json` (G-08) or they permanently cap
the exact score below the stated goal. The recoverable-by-annotation subset
is already counted in the missing/wrong variable verdicts.

---

## 5. Gap clusters

Each cluster: measured evidence → what exists in `src/` → what is missing →
implementation notes → owning TODO tasks → expected effect on the score.

### A. The declaration layer (largest gap, ~1,500 missing lines)

**Evidence.** 117 missing aliases; 21 TypedDicts; 5 NamedTuples; 17 missing +
8 extra protocols; 51 missing TypeVars + 6 ParamSpecs; 24 missing classes
(all of them carriers/Constants); 134 missing declaration uses; plus the
scoring shadow: 104 of the 198 `reference_only` *variables* are alias-typed
annotations inside synthesized declarations, and ~60% of "missing" params
(65 alias-family + 46 TypeVar-family + 21 module-class + 21 object-family)
plus ~43 alias-family + 17 module-class + 10 scalar + 5 library + 4
ClassVar/Final variable misses name declarations that do not exist.

**What exists.**

- `src/astart/transforms/aliases.py` — `AliasOptimizer` with site collection,
  pattern mining (`_composites`, `_represent`), candidate evaluation,
  `optimize()`. Reachable via `astart transform` and, since the default-on
  wiring, as a `fix_source` post-pass (per the S-03 "native synthesis
  follow-up" note).
- `src/astart/transforms/alias_patterns.py` — `alias_name()`, `_pascal()`,
  `_constant_name()`, `Pattern`, `AntiUnifier`: a naming grammar that already
  produces `Dict…`/`…Or…`/`Variadic`/`Type` shapes similar to the author's.
  **Alignment audit needed**: does it elide `str` dict keys (`DictInt` not
  `DictStrInt`), emit `ValueOrNone[X]` parameterized aliases, and order
  `TupleStrInt` vs `TupleIntStr` correctly?
- `src/astart/rules/typevars.py` (1,993 lines), `rules/protocols.py` (1,716),
  `rules/protocol_verify.py`, `docstrings/core.py` + `docstrings/types.py`.
- `graph/conversion/stages.py:581-816` — `_add_missing_type_params` /
  `_collect_type_vars_from_params/return`: the *old* engine already has
  TypeVar analysis; the new path emits nothing PEP 695.
- `Settings.create_constants` (`settings.py`, `runner.py:190`,
  `facts.py:1048`) and `rules/constants_grouping.py` — the Constants grouping
  machinery exists but defaults off and is not enabled by the compare
  settings.

**What is missing.**

1. **~~Wire `AliasOptimizer` into the fix pipeline~~ Done (default-on
   post-pass).** Remaining from the original item: integrate its guarded
   transaction into the annotation fix catalog on the same module so checker
   rejection can remove the alias transformation independently; collect
   candidate alias sites from *emitted annotations*, cluster by structural
   equality,
   name via `alias_name`, emit `type X = ...` (S-03, ≥3.12) or `X = ...`
   legacy, then rewrite annotation sites to the alias name. Reuse-before-
   create + project lockfile (M5-10) so names are stable across runs.
2. **Prefer-alias spelling at emission time** (AF-16): once an alias exists,
   the annotation writer must look up "is there a declared name for this
   type" before spelling structurally. Today there is no name→type index
   consulted by `rules/` emitters — negotiation builders produce structural
   types only.
3. **Data-carrier synthesis as a real transform** (M4-18 is suggest-only):
   - dict literal with fixed string keys, used as a record ≥3× or returned →
     `TypedDict`; compose `{**a(), **b()}` returns into per-function
     TypedDicts + a joining TypedDict (the Part1/2/3 pattern);
   - mutual recursion (`RecursiveRoot`/`RecursiveChild`) needs forward
     references inside the TypedDict bodies;
   - generic carriers (`CallablePayload[T]`);
   - `__init__`-only classes with simple field assignments → `NamedTuple`
     (Point, SliceExampleResult, ImportExampleResult, RedefinitionResult,
     ScopeResolutionResult — 5 sites);
   - `@dataclass(init=False)` + manual `__init__` + class-attr defaults →
     `@dataclass(slots=True)` + fields + `field(default_factory=...)`
     (DataClassExample, ExtendedDataclassStress).
4. **Constants grouping enabled + lowercase**: flip `create_constants` in the
   pair harness (or promote the detector), apply S-05 rename
   (`MAX_VALUE`→`max_value` — note `is_constant_name` only matches
   UPPER_SNAKE *module* constants, which is correct for detection, but the
   *emitted* attribute names must be lowercase to match the reference),
   rewrite the 19 use sites, generate the docstring (S-06), and cover the
   `extended_*` module assigns (W-14 — currently unannotated in result).
5. **Protocol consolidation**: see cluster B — the 8 invented dunder protocols
   must be replaced by role-named contracts; requires semantic naming
   (M5-09 reuse-before-create, M5-24 no-shadowing, M5-10 lockfile) and
   name-agnostic scoring (P-07) so `SupportsAddition2`-style fragments
   collapse.
6. **Canonical binder block**: hoist all TypeVar/ParamSpec emissions to a
   single top-of-file section in a deterministic order, share binders across
   functions (fix the `T/T2/T3/T4` proliferation first — see defect D2),
   emit `name=` kwargs + double quotes, then migrate hot generics to PEP 695
   (M5-23) where the target allows.

**Expected effect.** Alias-family items alone: params 65 missing + 31
compatible + 26 narrower + 5 looser + 1 unresolved + 9 wrong ≈ 137 of 471;
variables 43 missing + 76 compatible + 19 narrower + 9 wrong + 1 unresolved ≈
148 of 294. Even partial success (say 60% of alias-family spellings matched)
moves exact recovery by tens of points — larger than every inference task
combined. It also removes most of the "unresolved" verdicts (36) caused by
`SupportsAddition2`-style names that cannot be matched to author names.

### B. Contract-first annotation policy (the "module class"/"object" families)

**Evidence.** Missing-by-family: `par/Module class` 21 + `var/Module class`
17; `par/Top type (object)` 21 + `var/Top type` 4; `par/Type alias` 65 +
`var/Type alias` 43 (covered in A); `par/TypeVar` 46 + `var/TypeVar` 4;
`par/Generator` 5; `par/Self` 4 + `var/Self` 1; `par/Callable` 1; library
class 22. The 98 missing *returns* are dominated by "returns a class or
callable" (`-> TypeObject`, `-> CallableIntInt`, `-> SupportsCall2`,
`-> TypeSupportsClassMethods`, `-> Point`, `-> ReferenceType[object]`, …) —
see the missing-returns histogram in §1/json2 output.

**The core insight.** Most of these returns hand back a *function-local*
class (`return InnerClass`, `return Vector`, `return Combined`,
`return LocalMultiplier`). A function-local class **cannot be named in a
module-level annotation** — `-> type[InnerClass]` is a `NameError` for any
reader and meaningless to a checker. The author's answer is always a
*structural contract*: `TypeObject`, `TypeSupportsClassMethods`,
`TypeSupportsValue`, `SupportsCallAndFromValues`, `Callable[..., Supports-
Instance[T]]`. The engine's correct move is therefore not "infer
`type[LocalClass]`" (impossible) but "infer the *interface the callers
actually use* and emit a protocol/alias for it" — i.e., demand-driven contract
synthesis (F-13 builder capabilities, P-07 name-agnostic scoring,
M5-09/M5-24/M5-10 reuse+lockfile). This single policy explains:

- the 8 extra `Supports*` protocols (engine synthesized *some* contract but
  per-signature-shape, fragmented, counter-suffixed);
- the 17 missing protocols (author consolidated by *role*, engine by shape);
- `function_with_optional_types->` written `Callable[[None | int], int |
  str]` vs author `SupportsCall2` — the engine spelled the shape, the author
  named the contract (and got it *wrong* per the checker? no — it's a real
  protocol with overloaded `__call__`);
- `SupportsNameAndPath` — a protocol for a *module* (`os.path`), i.e.,
  contracts are not limited to classes;
- unresolved verdicts on `SupportsAddition`/`SupportsRadd`/`T2`/`T3`/`T4`
  (names that can't be matched);
- wrong `function_with_metaclass_registry_stress.registry`: wrote `None`,
  author `DictRegistryMeta` — metaclass-populated attribute (I-11, M2-06);
- wrong `HybridContainer.__or__.merged`: wrote `HybridContainer` (bare, no
  type args — also a TYP bare-generic defect, Q-34) vs author `Self`
  (W-11/X-03: prefer `Self` for `self.__class__(...)` returns);
- `Self` misses: `RegistryBase.clone`, `RegistryItem.bump`, `FluentBuilder.
  add/configure/build`, `LocalMultiplier.from_values`, `AsyncResource.
  __aenter__`, `HybridContainer.__or__` — all `return self`/`cls(...)`/
  `self.__class__(...)` patterns; X-03 + W-11 + M5-23.

**What exists.** `rules/protocols.py` + `protocol_verify.py` synthesize
Protocols today (the 8 dunders prove it); `rules/negotiation/builders/` has
capability builders; `semantic/` has the class/attribute model.

**What is missing.**

1. **Usage-driven contract selection**: for each "returns local class"
   site, compute the *minimal member set exercised by callers* (F-13), then
   name the protocol semantically (from the role: callable? iterable?
   context-manager? mapping?) rather than by member shape. typed's names
   (`SupportsCallAndFromValues`, `SupportsApplyAndOffset`) encode role +
   member summary.
2. **Stub-class promotion**: untyped's `class SupportsUpdate:` (docstring
   "Protocol for ...", docstring-only method bodies, used only in
   annotations) should become `class SupportsUpdate(Protocol)` with `...`
   bodies — detect name prefix + all-empty bodies + annotation-only uses.
   Same for `SupportsExecuteInt`→rename, `SupportsVector`→rename+reshape.
   Result currently keeps them as plain classes *and* emits 8 extra
   protocols — double pollution (6 extra classes + 8 extra protocols).
3. **`type[X]`/`Callable[..., X]` emission for class returns**: where a
   module-level class IS returnable (`Point`, `Singleton`, `Factory`,
   `Builder`, `Handler`, nested `Matrix` inside function — still
   unnameable!), prefer `type[Point]`-style aliases (`TypeObject` family)
   over `object` and over bare `type`. `bound_when_evaluated` +
   `from __future__ import annotations` makes forward refs safe, but
   function-local classes remain unnameable — protocol is the only sound
   answer.
4. **Dunder signature tables** (T-01, W-09, AF-03): `__get__`/`__set__`/
   `__delete__`/`__aexit__`/`__exit__`/`__matmul__`/`__call__`/`__init__`/
   `__new__`/`__iter__`/`__getitem__`/`__setitem__`/`__contains__` have
   language-given parameter contracts; typed's `DescriptorWithOwnerCache.
   __get__` has the full `@overload` triple (`instance: None → Self`,
   `instance: object → ValueT`, impl `ValueT | Self`) — this is a data table
   + synthesis rule, not inference.
5. **Attribute-carrying protocols**: typed protocols declare attributes
   (`offset: int`, `data: ListListInt`, `instance: ValueT`, `metadata:
   NodeMetadata`) — protocol *data* members from `self.x` assignments
   (M5-06 read-only-vs-writable, M2-06).
6. **`Self` preference policy** in negotiation/policy + builders: return
   `self`, `cls(...)`, `self.__class__(...)`, or `super().__new__(cls)` in a
   method → `Self`, not the concrete class (W-11/X-03).
7. **Overload synthesis** (M4-19 is suggest-only; typed has 26): literal-
   dispatch (`mode == "int"`), key-type dispatch (`__getitem__` int vs str),
   optional-first-arg (`value: None = None`), bool-flag (`compact: Literal
   [True]/[False]`). Each overload set needs an *implementation signature*
   (broad params + `cast` inside) — pair with the `cast()` emitter.
8. **`cast()` emission** (12 sites in typed, 0 in result): needed where the
   declared contract is wider than local evidence — TypedDict field
   extraction (`name_obj, payload_obj, metadata_obj = result` + 3 casts),
   `cast(typ="ItemT", val=value)` in overload impls, `cast(typ="ListInt",
   val=merged["extra"])`. House style is kwargs `cast(typ=..., val=...)`.
   This is a negotiation "widen-with-cast" rule, not an inference rule.

**Expected effect.** Converts most of the 36 unresolved + 8 protocol-extra +
17 protocol-missing + ~40 module-class/object returns + the `Self` family +
several wrongs. Also the *visual* gap: `result.py`'s 8 invented protocols
scattered through the file vs typed's 17 curated ones in the header.

### C. Docstrings

**Evidence.** 209 changed / 89 missing / 40 extra / 125 exact. Changed-field
histogram: `returns` 142, `parameters` 114, `attributes` missing 32,
`summary` 7, `yields` 3, `description` 1. Result docstrings have Args/Returns
sections but **without `(type)` after names**; 5 docstrings close glued to
text (`"""` on the last text line, no blank line); typed has a blank line
before every multiline close (292 defs) and `TODO.` placeholder summaries on
28 undocumented defs + 1 class.

**What exists.** `docstrings/core.py` (1,871 lines) + `docstrings/types.py` —
the section machinery works; AF-08 ("docstring types follow annotations") is
the open task for the `(type)` insertion; AF-09 for Raises/Yields/Attributes;
AF-22 for the deterministic policy; AF-23..26 for GDC metrics.

**What is missing.**

1. AF-08: emit `name (type):` in Args/Returns/Yields — mechanical once the
   annotation is known; ~256 field insertions available.
2. AF-09 + AL-12: `Raises:` from exception-flow summaries (9 in typed),
   `Yields:` from generator/async-generator inference (7), `Attributes:`
   from class-level annotations (16 — depends on W-12/W-14 class attrs).
3. Closing-format rule: blank line before `"""` on multiline docstrings (5
   violations in result).
4. `TODO.` summary policy for undocumented defs the tool touches (28 in
   typed) — decide whether astart should *add* placeholder summaries or leave
   prose alone (AF-22).
5. Docstring sync when declarations are synthesized (TypedDict/NamedTuple/
   Protocol/Constants classes each need their own docstring + Attributes).

### D. Imports and module style

**Evidence.** typed adds 47 from-imports, drops 9 bare imports; result adds
10, drops 0, and now has both `import uuid` and `from uuid import UUID`.
Result also imports `Iterable` (used only in the 6 looser `Iterable`
annotations) and keeps `Never` (likely unused — M3-11).

**What exists.** IMP001 fixer is M8-27 (open, P1, recipe written);
`rules/imports*` family; P-10 import parity (open, P1).

**What is missing.**

1. M8-27 implementation: `import asyncio` → `from asyncio import run,
   sleep` **and rewrite use sites** (`asyncio.sleep` → `sleep`), importing
   exactly the used names. Nine modules affected; ~30 use-site rewrites.
   Must run before/with annotation emission so new annotations reuse the
   same import names.
2. Unused-import cleanup (M3-11): `Never`, possibly others.
3. TYPE_CHECKING placement (S-01/S-02, M3-09): typed has one deliberate
   `if TYPE_CHECKING:` block; astart emits none.
4. Import sorting/grouping parity (AF-12) — typed's import block is sorted;
   result's is insertion-ordered.
5. Redundancy rule: when both `import uuid` and `from uuid import UUID`
   exist after annotation emission, prefer the from-import and drop the bare
   import if all uses are rewritten (or keep bare only if `uuid.` attribute
   uses remain).

### E. Call/kwargs repair and idioms

**Evidence.** Only 1 body diff between untyped and result
(`__import__(name='os.path')` — which *was* repaired). typed repairs/changes
~15 call sites; the planted bug `run(args=...)` → `run(main=...)` was
**missed** — `args` is not an `asyncio.run` parameter, so this is a
wrong-keyword repair (M6-05/06 territory), not a style choice.

**Hypotheses to verify (cheap experiments, not yet run):**

- The call is `asyncio.run(args=...)` — an *attribute* call on a module.
  If the kwargs fixer only handles bare-name callees, module-attribute
  callees are a blind spot.
- `custom_dict.update({'b': 2}, 3)`: `dict.update` is
  `update(m, /, **kwargs)` — the positional `3` is actually a **runtime
  TypeError** in untyped; typed's class-body deletion made it valid again.
  astart correctly refused (callee signature unprovable for the *custom*
  class) — but should it have flagged the latent bug? That's M6
  call-problem detection, not a fix.
- `apply(5)`, `fetch(sum(values))`, `update(message)`, `handle(request)`:
  callees are function-local classes — signatures unprovable until W-12/
  class-attr inference lands. Expected to unlock downstream.

**Idiom gaps (mostly accepted-deviation candidates):** `_ =` discards (~10
new sites in typed), `msg` normalization (S-08 implemented-slice pending;
only ~1 site here), binary-literal style, `setattr(cls, 'new_method', ...)`
vs `cls.new_method = ...`, `self.__class__` vs concrete class in
`HybridContainer.__or__`.

### F. Writer/formatting hygiene (defects in `result.py` itself)

Measured on `result.py` (4,320 lines):

| Defect | Count | Example |
| --- | ---: | --- |
| lines > 79 cols | 51 (max 213) | `result.py:431` one-line 7-arg signature; `:1157` `def function_with_optional_types() -> Callable[[None \| int], int \| str]:` |
| synthesized Protocol glued to previous def (no blank lines) | 8 | `result.py:167, 342, 523, 603, 730, 1451, 1540, 3461` |
| `T = TypeVar('T')` glued after a function body | 4 | `result.py:482, 1346, 1460, 2074` |
| docstring close glued to text | 5 | e.g. `result.py:61-63` |
| same name `AnnAssign`ed >1× in one function | 8 functions | `function_with_try_except.result` ×3 (try/except/else branches), `evolving_value` ×3, `x` ×2, `amount` ×3, `name` ×2, `value` ×2, `current_score` ×2, `main._` ×3 |
| single-quoted `TypeVar('T')` positional | 4 | typed uses `TypeVar(name="T")` kwargs + double quotes |

**Missing rules:**

1. **Annotate-first-binding-only**: for multiply-bound locals, emit one
   annotation at first binding; for type-*changing* rebinds emit a bare
   union declaration up front (`evolving_value: IntOrStr | ListInt |
   DictInt` then bare assigns — typed.py:3692-3700) — this is the G-10/I-19
   pattern but the *declaration-hoisting* aspect is not implemented (result
   annotates each branch → duplicates + narrower unions).
2. **Blank-line placement for synthesized declarations**: protocols/typevars
   inserted adjacent to functions need PEP 8 spacing (E302/E303) — likely the
   same transactional-emission gap as CC-10/CC-11.
3. **TypeVar emission style + placement**: `TypeVar(name="T")` kwargs,
   double quotes, top-of-file canonical block, shared binders (defect D2
   below).
4. **Long-line wrapping**: AF-10 (open) — or confirm whether the compare
   artifact is pre-`format_source`; `graph/conversion/artifacts.py:17`
   defines `format_source` (ruff format) and `:198` applies it on write, but
   the measured `result.py` still has 51 >79 lines, so either ruff was absent
   or the wrapping task is genuinely needed. **Verify before scheduling.**
5. **Annotation insertion should splice, not re-render**: `x**2` →
   `x ** 2` drift (result.py:584) shows AnnAssign values go through
   `ast.unparse`; ruff format would restore `x**2`, but textual splice
   (CC-11 lexical provenance) avoids the drift class entirely.
6. **Canonical declaration ordering**: typed's order is imports →
   TYPE_CHECKING → typevars → aliases → TypedDicts → Constants → protocols →
   classes → functions → `if __name__`. result interleaves synthesized
   protocols at first-use position. A "declaration layout" pass (module-level
   analogue of S-09 method ordering) is missing.

### G. Scoring/measurement blind spots

1. **Unscored surfaces**: imports, Constants grouping, call kwargs, `_ =`
   discards, casts, literal style, `@overload`/`@override` presence,
   blank-line/formatting — none appear in `conversion-report.json`
   `artifacts`. Progress on clusters D/E/F is invisible. Extend
   `conversion_structure.py` artifact kinds (it already compares
   declarations) with `imports`, `constants`, `decorators`, `casts`,
   `call_style`.
2. **`reference_only` = 198 variables + 28 params**: annotations that exist
   only in typed — mostly inside synthesized declarations. Correctly
   excluded from `to_recover`, but they are ~40% of typed's annotation
   surface; once carriers exist they should be re-scored (the scorer keys on
   untyped positions today).
3. **`compatible` → `exact` path**: 32 params + 77 vars are semantically
   right but spelled concretely. Once aliases exist *and* the writer prefers
   them, most become exact — this is the single biggest exact-% lever and it
   is a *naming* problem, not an inference problem.
4. **`accepted_deviations.json` (G-08)**: enumerate the §4 author-idiom diffs
   (~25 sites) so the 90% goal measures engine capability, not author whim.
5. **Docstring `changed` conflation**: 209 changed mixes mechanical
   `(type)`-missing (AF-08, ~256 fields) with prose rewrites — split the
   verdict so AF-08 progress is measurable.
6. **Protocol name matching**: `unresolved` on `SupportsAddition2` etc. is a
   scorer artifact (P-07 name-agnostic scoring); structural member-set
   matching would already collapse most.

---

## 6. Concrete defect list (new, not in TODO)

| # | Defect | Evidence | Likely owner |
| --- | --- | --- | --- |
| D1 | Synthesized protocols/typevars inserted without surrounding blank lines | result.py:167,342,523,603,730,1451,1540,3461; :482,1346,1460,2074 | writer/transaction layer (CC-10/CC-11) |
| D2 | Per-function `TypeVar`s `T/T2/T3/T4` proliferate instead of shared module binders; emitted mid-file, positional args, single quotes | result.py:482,1346,1460,2074 vs typed.py:79-86 | `rules/typevars.py` emission + binder registry (M5-23 adjacent) |
| D3 | Same local annotated once per binding site (≤3×) instead of first-binding + bare reassign / hoisted union decl | 8 functions incl. try/except `result` ×3, `evolving_value` ×3 | `rules/negotiation/variables.py` + G-10/I-19 |
| D4 | `import uuid` + `from uuid import UUID` coexist; bare module imports never rewritten | result.py:19,46 vs typed import block | M8-27 + P-10 |
| D5 | `run(args=...)` wrong-keyword not repaired (`args` isn't an `asyncio.run` param) | untyped→typed body diff; result kept `args=` | M6-05/06 call-problem detection — **verify callee form (attribute vs bare)** |
| D6 | Function-local classes returned but annotated with nothing/protocol-shape only; no role-named contract synthesis | 98 missing returns histogram | cluster B (new task?) |
| D7 | Stub `Supports*` classes kept as plain classes *and* 8 extra shape-fragmented protocols emitted — double pollution | artifacts: 6 extra classes + 8 extra protocols | cluster B.2 |
| D8 | `Self` never preferred for `return self`/`self.__class__(...)`/`cls(...)` | 5 Self misses + HybridContainer.__or__ wrong | W-11/X-03 policy in negotiation/policy.py |
| D9 | Bare generic `HybridContainer` emitted without type args where `Self`/parameterized expected | wrong verdict `function_with_hybrid_container_stress.left/right` | Q-34/TYP bare-generic |
| D10 | `AnnAssign` values re-rendered via `ast.unparse` → spacing drift (`x ** 2`) | result.py:584 | CC-11 lexical provenance / text splice |
| D11 | Docstring close glued to text (no blank line) ×5 | result.py:61-63 etc. | docstrings/core.py layout rule |
| D12 | `Iterable`/`Never` imported but unused or never chosen by author | result.py:19,46 | M3-11 + abstraction-choice policy (M4-16/accept_general) |
| D13 | Long signatures/annotations emitted unwrapped (51 lines >79, max 213) | result.py:431 etc. | AF-10 — **first verify whether compare artifact bypasses `format_source`** |
| D14 | Module-level `Final` constants annotated but not grouped into `Constants`; use sites unrevised | result.py:50-52 vs typed.py:535-553 | `create_constants` enable + S-05/S-06 + W-14 |
| D15 | 4 `Supports*` stub classes not promoted to `Protocol`; bodies keep implicit-`None` docstring-only shape | artifacts extra/missing protocols | cluster B.2 (new transform) |

---

## 7. Suggested sequencing (dependency order, not TODO order)

1. **Verify-first (hours)**: does the compare path apply `format_source`?
   Why was `run(args=)` not repaired — bare vs attribute callee? Does
   `alias_name()` already produce `DictInt`-style elided names? These decide
   whether D13/D5 are bugs or missing features.
2. **Writer hygiene batch** (D1, D2-style placement, D3, D10, D11, D13):
   makes output *look* like typed.py even where types are unchanged; several
   are small rules in the transaction/emission layer; unblocks readable
   diffs for everything after.
3. **Alias layer** (A.1/A.2 + S-03 + AF-16 + M5-10): ~~wire `AliasOptimizer`
   into `fix_source`~~ done (default-on post-pass); still open: align naming,
   prefer-alias spelling, checker-rejection integration. Largest exact-%
   lever; also prerequisite for readable TypedDict/protocol annotations.
4. **Data carriers** (A.3, M4-18→transform): TypedDicts (incl. `**`-merge
   composition + recursion), NamedTuples, dataclass rewrite. Fixes ~14 of
   20 wrong verdicts and dozens of missing returns/vars.
5. **Contract layer** (B): stub promotion, role-named protocols,
   module-shape protocols, `type[X]` returns, dunder tables, Self policy,
   overload+cast synthesis. Converts unresolved/extra/missing families.
6. **Constants + imports + docstrings** (A.4, D, C): cheap, visible;
   `create_constants` flip + S-05/S-06, M8-27, AF-08/AF-09/AF-22.
7. **Inference burn-down** per the opacity table (already TODO'd): unprovable
   Call 109 total nodes, Name 51, container-mutated 32, escapes 28 —
   W-06/W-07/I-09/I-11/I-17/AL-03/AL-04.
8. **Measurement** (G): accepted_deviations enumeration, artifact-kind
   extensions, compatible→exact tracking, docstring verdict split.

Rough impact ordering by recoverable verdicts: alias layer (~137 param +
~148 var alias-family items touched) > carriers (~14 wrong + ~50 missing
returns/vars + enables Part-TypedDicts) > contracts (~36 unresolved + 25
protocol artifacts + ~45 class/object returns) > inference burn-down
(~190 param + ~89 var missing minus downstream-of-above) > hygiene/style.

---

## 8. What this document deliberately does not claim

- No implementation was changed; all findings are from the committed
  artifacts + fresh AST diffs.
- `alias_name()`'s exact output grammar was not fully audited against the
  author's convention — flagged as an audit item, not asserted.
- Whether `format_source` runs in the compare path is unverified — D13 is
  conditioned on it.
- The 68-body-diff classification is heuristic (normalization-based); the
  ~25 "author idiom" sites are candidates for `accepted_deviations.json`,
  pending G-08 review.
- `dev/typed.py` (open in the IDE) was not compared; assumed scratch.
