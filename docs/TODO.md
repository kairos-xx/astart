---
agent: devin-local
session: complete-pamphlet
created: 2026-11-07T15:54:30Z
---
# Astart: Most Accurate Static Analyzer &amp; Fixer — Unified Precision Roadmap

Unified execution plan merging the project precision roadmap (docs/superpowers/roadmaps/2026-11-07-precision-roadmap.md, Phases 0–10) with the verified defect/gap analysis: measurement + external-checker gate first, then OO resolution, project-wide evidence, precise types, advanced Protocol/TypeVar synthesis, first-class imports, kwargs soundness, scale, and ontology completion.

## 0. Decisions (all locked with the user)

- **Scope: full roadmap M0–M8** — including `_graph`/`semantic` inference-core bug fixes.
- **Union policy: enabled (guarded)** — `T1 | T2 [| …]` accepted when ≤3 distinct definite spellings and inference corroborates.
- **TypeVar style: classic default + version-aware PEP 695** — `T = TypeVar("T")` default; `def f[T](x: T)` when `requires-python >= 3.12`.
- **Checker oracle: yes, optional auto-detect** — guarded fixes gated on pyright/basedpyright when installed (E6); without it, guarded fixes need a higher internal evidence level.
- **Default aggressiveness: configurable per-profile** — profiles/`[tool.astart]` set the safety ceiling; default profile applies proven-only, guarded behind opt-in flag/profile.
- **Protocol placement: shared `_protocols.py` + name lockfile** — same-member protocols merged project-wide with deterministic stable names; config switch preserves per-function placement.
- **Git init: yes** — initialize a repository in M0 so every milestone is diff-reviewable and rollback-safe.
- **Library keyword table: stdlib first, extensible** — curated typeshed-generated table; third-party packages join only via explicit allow-list.

## 1. North star (roadmap §1)

`astart fix` takes untyped, positionally-called Python and returns the same program with: (1) every safely keyword-capable call keyword-called; (2) every parameter/return/attribute/variable annotated with the **most precise type the evidence supports**; (3) `Protocol`s and type variables synthesized where structural or generic; (4) every required import; (5) formatting untouched except one final `ruff format`. Success = **zero wrong annotations at the highest recall precision allows**, proven by an independent checker, not by astart's own opinion.

Non-negotiables: behaviour preserving · never invalid Python · comments/layout kept · idempotent · explained skips (closed enum) · independent verification (E6 gate).

## 2. Verified inventory

**Working today** (verified by running the engine): `calls.add-keywords` (guarded, trusted in-module callees), `typing.add-none-return` (proven), `typing.add-inferred-annotation` (two-signal corroboration: default literal / agreeing call sites / provable return + inference), `typing.synthesize-protocol` (attribute/method-only params, dedupe), `typing.synthesize-typevar` (pass-through, classic TypeVar, auto-import), `typing.add-final`, `DOC002`, fix-runner ordering/conflict/halving, corpus probe numbers (316 `-> None`, 200 inferred, 63 Protocols, 8 TypeVars, 174 keyword calls).

**Verified defects** (each reproduced — feed M0):
- D1 `add_inferred_annotation` never calls `ensure_names` → latent uncompilable output for `_importable` names (`Iterable`, `Path`, …).
- D2 `'Unknown'` spellings counted as disagreeing call-site evidence (`Path("x")` case).
- D3 `imports.Constants.constructors` dead — syntax prover can't type `Path("x")`.
- D4 `C().m(4)`/`factory().m()` bound by analyzer but `trusted_binding` rejects non-Name receivers.
- D5 `self.m()` never binds → methods get zero call-site evidence.
- D6 `Exists` predicate crashes engine; D7 `min_confidence` never enforced (`FixOffer.confidence` hardcoded 1.0); D8 procedural rules unimplemented.
- D9 `raise`-only functions get `-> None` (should be `NoReturn`/`Never`).
- D10 order-dependent suite flakiness (`test_review3_fixes.py` — suspected shared mutable state).
- Roadmap inventory items: two `object` annotations in `formatting.py` predate policy; `test_graph_document.py` RUF043; methods second-class; single-module world; superlinear perf (12k lines ≈ 47 s); protocol members untyped.

**Verified recall gaps** (feed M4/M5): `x=None` defaults refused (R1); `*args`/`**kw` never hinted (R2); generators refused (R3); usage→ABC (`Iterable`/`Sequence`/`Mapping`/`Sized`/`Container`/`Callable`/`Awaitable`) absent (R4); `TypeGuard[X]` absent (R5); unions refused (R6 — enabled guarded); `Await`/`Try`/`Match`/`AugAssign` uncovered (R7); expression defaults refused (R8); `self._attr` returns tainted (R9); language-guaranteed returns (`f"{x}"`, `not x`) die on `no candidate` (R10); comprehension returns untyped (R11); `Self`/`ClassVar`/property conventions (R12); protocol member returns untyped + `await` refused + no ABC lowering + `p()` refused (P1–P4); BoolOp passthrough refused, no constrained/bound TypeVars, no ParamSpec (T1–T5); stub-resolved calls never keyworded, receiver expressions distrusted, missing/unexpected-argument detection absent (K1–K4).

## 3. Accuracy model (adopted wholesale)

Evidence ladder: **E0** syntax-proves · **E1** declared-elsewhere (stubs, base signatures, `@overload`, implemented ABCs) · **E2** closed-world usage (all in-module sites, no escape) · **E3** cross-module call sites · **E4** library signature flow · **E5** inference proposal (candidate only, never alone) · **E6** external checker does not object.

**Policy: a guarded fix needs (E2 ∨ E3 ∨ E4) ∧ (E5 agrees ∨ E0 proves) ∧ E6 does not object.** `proven` = E0/E1 only. `rejected-by-checker` is a reported outcome, never silent. Confidence calibrated against benchmarks; `--min-confidence` knob. Checker auto-detected; absent → guarded fixes need higher internal evidence.

## 4. Unified milestones

### M0 — "Trustworthy slice" (roadmap Phase 0 + defects)
- **Git init** (locked) so every later diff is reviewable; decide `ruff format` drift policy.
- Triage final-review findings; fix Critical/Important RED→GREEN.
- Fix D1–D10: `ensure_names` in `add_inferred_annotation`; `Unknown` → non-definite; wire `constructors`; `NoReturn`/`Never` for never-returns; guard Exists crash; suite pollution root cause; protocol `arg0`/`self` collision refusal (existing test).
- Replace two `object` annotations in `formatting.py`; fix RUF043.
- Exit: reviewer clean, suite green deterministically, bare `exactus` clean.

### M1 — "Measured" (roadmap Phase 1 — highest priority)
- **Benchmark harness** (`benchmarks/`, `tests/bench_*`, `docs/benchmarks.md`): annotation-recovery on stripped open-source code; gold set 34→≥500 by failure class; corpus 20→≥100 real modules; precision ≥99.5% guarded / 100% proven targets; recall; checker delta; throughput by size bucket (500/2k/12k/50k); stability (idempotence, ≤3-round fixed point); semantic-equivalence runs on 10 pinned projects.
- **Checker oracle (E6, locked: optional auto-detect)**: basedpyright/pyright (+optionally mypy) before+after per round on whole file (batched); new diagnostics → bisect via runner's existing halving → roll back `rejected-by-checker`; content-hash cache.
- Writer fuzzing: random fix subsets → compile + comments preserved + AST-equal-after-strip.
- Closed skip-reason enum (`conflict`, `escapes`, `disagree`, `checker-rejected`, `unresolved-callee`, …).
- Full-CLI idempotence tests on all corpus files; real `FixOffer.confidence` + `min_confidence` enforcement (D7).
- Exit: dashboard + baseline published; E6 gate active for guarded fixes; zero checker regressions.

### M2 — "Object-oriented code works" (roadmap Phase 2 + kwargs 7.2–7.4 + D4/D5/R9)
- Method/constructor resolution: `self.m`, `obj.m` (class known), `Class.m`, `super().m`, `cls()`, `@classmethod`/`@staticmethod`, MRO inheritance, instantiation → `__init__`/`__new__`/dataclass fields. Fixes D5.
- `trusted_binding` v2 for expression receivers (D4) + rules-layer `self.X → ContractIndex` fallback.
- Attribute types from `__init__`/all class assignments → class-level annotations, `Final`/`ClassVar` when all agree (R9).
- Override awareness (E1): overriding methods inherit base signature; never contradict; keyword fixes use base param names.
- Escape analysis v2: real "used as value" analysis (callbacks, `functools.partial`, `map`, decorators, registries, `getattr`, attribute escapes).
- Flow-sensitive locals: `isinstance`/`is None`/truthiness/early-return/`assert` narrowing, merge joins, loop widening to fixpoint.
- Kwargs for constructors/dataclass/NamedTuple/attrs/pydantic + method calls + bound-method callbacks (7.2–7.4).
- Exit: method recall ≥3× M1 baseline at unchanged precision.

### M3 — "Whole project" (roadmap Phases 3 + 6)
- Project graph: import resolution (absolute/relative/`__init__` re-exports/`__all__`/conditional), whole-project call graph, content-hash invalidation.
- Cross-module call sites (E3); public APIs guarded-only with "assume external callers" switch; private (`_name`) = closed world.
- Typeshed/`py.typed`/stub-package loading (E4): library signature flow for hints + curated "safe to keyword" table for library callees (K1; stdlib first).
- Version awareness: `requires-python` gates `X | Y`, PEP 695, `Self`, `TypeAlias` emission.
- **Imports subsystem**: canonical public locations (`collections.abc.Sequence` not `typing.Sequence`; `pathlib.Path`; shortest `__all__`-honouring path), file-style matching, `TYPE_CHECKING` placement for cycle/heavy-module safety (+ `from __future__ import annotations` where runtime annotation consumers don't forbid), shadowing/collision avoidance, unused-import cleanup (own-added only), deterministic pre-ruff placement. Includes `ensure_names` everywhere + expanded `known_imports` (full `collections.abc`, `NoReturn`/`Never`, `TypeGuard`/`TypeIs`, `Self`, `ClassVar`, `Literal`, `ParamSpec`, `Concatenate`, `TypeVarTuple`, `TypedDict`, `NamedTuple`, `Annotated`, `override`, `final`, `Decimal`, `Fraction`, `UUID`, date/time, `re.Pattern`/`Match`).
- Exit: cross-module recall met; 100k-line repo within perf budget; no precision regression.

### M4 — "Precise types" (roadmap Phase 4 + hint-lattice/prover work)
- Prover depth: comprehensions, subscripts on typed names, builtin-method result table, `Await` unwrap, `Try`/`Match`/`AugAssign`/loop handling, yield typing, `constructors` + once-bound ClassDef calls (D3).
- Hint lattice: `optional_default` (`T | None`), `variadic_args` (`*args: T`/`**kw: T`), `generator`/`async`, `usage_abc` (corroborated by `subtype()` over call-site types), `typeguard`/`TypeIs`, `never_returns`, `syntax_proven` (language-guaranteed), `union_sites` (≤3 spellings, locked), expression defaults, `Self`/`ClassVar`/`Literal`/`TypeAlias`/`NewType` where provable.
- Variable/attribute annotations (`x: list[int] = []`, empty containers from later `append`s) — module/class level or checker-required only, never gratuitous locals.
- Container precision: literals/comprehensions → `list[int]`/`dict[str,int]`/tuple shapes; "accept general, return specific" (params → `Sequence`/`Iterable`/`Mapping`, returns → `list`/`dict`).
- `Callable[[…], R]` params from call shape + result use.
- Data-carrier synthesis (`TypedDict`/`NamedTuple`/`@dataclass`) and `@overload` synthesis — **suggest-only** initially.
- Each item: own catalog fix + safety class + gold cases + E6 gate.
- Exit: corpus recall step-change at ≥99.5% guarded precision.

### M5 — "Structural and generic done properly" (roadmap Phase 5)
- **Protocols**: typed members (returns from result use; params from arguments incl. flow-typed), `async def` members, generator/context-manager/indexing/operator/truthiness/`len` members, `__call__` callback protocols (keyword names preserved), read-only vs writable attribute members, `runtime_checkable` only under `isinstance`, collision-safe member-name allocation (D-regression), **reuse-before-create** against existing/typing/`collections.abc`/`os` protocols (`SupportsRead`, `Iterable`, `Sized`, `PathLike`, `typing.IO`) with minimal-sufficient-member selection, **merge into shared `_protocols.py` + name lockfile** (locked; config switch for per-function), `TYPE_CHECKING` placement for type-only protocols, E6 verification against actual call sites (widen or drop).
- **TypeVars**: bound (`T bound=CloseProtocol` for `x.close(); return x`), constrained (exhaustive `isinstance` branches/overloads only), multi-variable relations (`pair(a,b) → list[T|U]` vs `list[T]` by call-site evidence; `dict[K,V]`; `Iterable[T] → list[T]` element pass-through; `items[0] → Sequence[T] → T`), `Self` for `return self`/`cls()`, ParamSpec decorator forwarding (`f: Callable[P,R] → Callable[P,R]`), `TypeVarTuple` variadic passthrough, `T_co`/`T_contra` variance, BoolOp/comparison shared `T` (`a or b`, `a if a>b else b`), PEP 695 behind version flag, no user-symbol shadowing, project-wide declaration reuse option.
- Exit: protocol/typevar gold cases green; E6-verified synthesized protocols; zero invalid output on the danger corpus.

### M6 — "Kwargs bulletproof" (roadmap Phase 7 remainder)
- Danger matrix → ~60 tests: decorators/`__getattr__`/`__call__`/Liskov-violating overrides/C-impl posonly/renamed params/rebinding/conditional defs/callback containers/`functools.wraps`-less wrappers.
- Positional-only/keyword-only end-to-end (`/`, `*`, `**kwargs` forwarding, `functools.partial`, `super().__init__` chains).
- Library keyword table: curated versioned stdlib signatures (typeshed-generated, test-verified); never C posonly builtins; third-party via allow-list only.
- Style controls: `min_positional`, per-callee allow/deny lists (e.g. don't keyword `len(x)`/`print(x)` first arg).
- Detection rules: `calls.missing-argument`, `calls.unexpected-argument`, `calls.ambiguous-callee`, `calls.unresolved-callee`.
- Idempotence with ruff line-wrapping verified.

### M7 — "Fast and shippable" (roadmap Phases 8 + 9)
- Performance: kill superlinear costs (semantic worklist, repeated tree walks — single subject pass bucketed by kind, per-node binding caches); ≤5 s/12k lines, ≤30 s/100k lines single-threaded; incremental content-hash cache; process-pool parallelism; streaming `--jobs` CLI; memory budget tests.
- Product surface: `[tool.astart]` pyproject config (rules, select/ignore, safety ceiling — **configurable aggressiveness per profile, locked** — per-path overrides, target version, protocol/typevar style, import placement, library tables); baselines + external per-path ignores (suppression comments stay forbidden); SARIF/GitHub-annotations/JUnit/`--statistics` reporters; LSP diagnostics + code actions; pre-commit/CI recipe; interactive review mode (evidence ladder per guarded fix, "accept all high-confidence"); `astart explain <rule> <location>`; `--backup`/undo journal.

### M8 — "Whole ontology + inference core" (roadmap Phase 10 + inference fixes)
- Missing analyzer rules: `imports.bare-import` IMP001 (`import ast` → `from ast import X` + use-site rewrite, proven when collision-safe); `typing.missing-variable-annotation` TYP005; `typing.no-object-annotation` TYP002; `suppression.marker-comment` SUP001; `parsing.module-does-not-parse` PRS001; `typing.return-type-mismatch`/`incompatible-default`; docs family DOC001/003/004/006 (+guarded doc fixers); whitespace/blank-line normalisation; `Constants`-class grouping with `Final`; delegation relation to ruff.
- Ontology completion: `Exists` evaluation (D6), procedural rules (D8), profiles + relations (`supersedes`/`conflicts_with`/`implies`) exercised, `Maturity` lifecycle → defaults, rule authoring kit (scaffold + example-as-test generator).
- Inference core: fix verified wrong types (`"hi " + name` → `int`, `list(d)` → items-not-keys, `seq[0]` → `Sequence[int]` over-broad); imported-constructor argument typing (`Path("x")` → `Path`); `self.` receiver typing in analyzer.
- Exit: `verify_catalog` all invariants green; full spec-§5 rule set present; parity vs Exactus KWARGS_TYPEHINTS categories complete.

## 5. Cross-cutting engineering (every milestone)

- **Confidence calibration**: numeric confidence per candidate from evidence level; calibrated on benchmarks; `--min-confidence`.
- **Determinism**: stable ordering/names; Protocol name lockfile; no dict/set-order or time dependence.
- **Error containment**: per-file + per-fix isolation (exists) + per-file timeout + per-fix watchdog.
- **Test strategy**: gold sets by failure class; property tests (grammar-random programs → strip → fix → check); mutation testing on policy code; corpus ≥100; regression test per reviewer finding.
- **Docs**: evidence ladder + refusal catalogue ("why wasn't X annotated?") user-facing.
- **Conventions**: no suppression comments, no `Any`/`object`, keyword-only calls, Google docstrings, `@final Constants`.

## 6. Files touched per layer

`rules/provable.py` (Typer/can_fall_off) · `rules/hints.py` (HintBasis/judges/evidence/confidence) · `rules/protocols.py` (typed members/ABC lowering/merge) · `rules/typevars.py` (bounds/constraints/ParamSpec/PEP695) · `rules/imports.py` (resolver/TYPE_CHECKING/canonical locations) · `rules/resolve.py` (trusted_binding v2/self./stubs) · `rules/facts.py`+`rules/registry.py` (new facts/procedures) · `rules/engine.py` (Exists/procedures/confidence/subject index) · `rules/runner.py` (E6 gate bisection/min_confidence) · `rules/model.py`+`schema.json`+`catalog/*.json` (new rules/fixes/profiles) · `cli/commands.py` (config/profiles/jobs/reporters/explain) · `semantic/*`+`_graph/*` (resolution/inference fixes — prefer rules-layer where cheaper) · `benchmarks/`+`tests/bench_*` (harness) · `docs/benchmarks.md`, refusal catalogue.

## 7. Verification (every milestone)

- `python -m pytest -q` green; benchmark dashboard shows precision ≥99.5% guarded / 100% proven with no regression.
- Bare `exactus` from repo root as single lint/check gate; pytest for tests while iterating.
- Dogfood `astart check`/`fix --diff` on `src/astart/` — findings shrink per milestone; output always compiles.
- E6 checker delta = 0 new errors on benchmarks; corpus replay measures accepted-hint coverage before/after.
- `verify_catalog` 8 invariants + per-fix idempotence on every catalog example.

## 8. Risk register

Wrong annotation → checker gate + profile-controlled ceilings + `--safe-only` · keyword fix on dynamic code → danger matrix + refuse-on-uncertainty + library allow-list · Protocol name churn → deterministic naming + lockfile + reuse-before-create · inference regressions → benchmark thresholds in CI · performance → M7 phase + incremental cache · version drift → `requires-python` gating · scope creep → astart proposes, external checker verifies, never becomes a checker · unbounded semantics → refusal catalogue + fuzzing, new constructs start as "refuse" · suite pollution (D10) → investigate shared mutable trees before more import-writing appliers.

## 9. Progress log

### M0 — done 2026-11-07 (agent: claude, this session)
- Fixed: D1 (`ensure_names` now runs in `add_inferred_annotation`), D2 (`Unknown` call-site types are non-definite; syntax-proven argument types are independent evidence), D3 (imported constructors `Path("x")`, `Decimal(..)`, … type their calls via the `@constructor:<Name>` binding-count key), D6 (catalog validation rejects `exists` until M8 evaluates it), D9 (`typing.add-noreturn`, proven: always-raising functions get `-> NoReturn`), plus the review findings C1, C2, I1–I6.
- Replaced the five `object` annotations in `formatting.py` (typed `FieldValue` / `PatchValue` aliases); fixed RUF043.
- D10 (suite flakiness) did not reproduce: the suite passes in forward and reverse file order (1616 tests). The only order-like failures seen were from files being rewritten on disk by another tool during editing (bare-import conversion); no shared mutable state was found.
- D4, D5, D7, D8 are not M0 items (M2, M2, M1, M8).
- Not done: bare `exactus` run (owner runs it), baseline commit (repo exists; nothing committed by this session).
