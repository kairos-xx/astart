# astart roadmap: the most accurate static analyser and fixer for keywords and types

Status: proposal for review, 2026-11-07. Nothing here is approved or built unless it says "shipped".
Companion documents: `specs/2026-11-06-rule-ontology-design.md`, `specs/2026-11-06-fix-runner-and-type-hints-design.md` (sections 9 and 10), `plans/2026-11-07-check-fix-cli.md`.

## 1. North star

`astart fix` takes an untyped, positionally-called Python codebase and returns the same program with:

1. every call that can be keyword-called, keyword-called;
2. every parameter, return, attribute and variable annotated with the **most precise type the evidence supports**;
3. `Protocol`s and type variables synthesized where the type is structural or generic;
4. every import those annotations need;
5. formatting untouched except for one final `ruff format`.

Success is not "adds many annotations". It is **zero wrong annotations at the highest recall precision allows**, proven by an independent checker, not by astart's own opinion.

### Non-negotiable properties

| Property | Meaning | How it is enforced today | Gap |
| --- | --- | --- | --- |
| Behaviour preserving | Fixed program runs identically | Only annotations, keywords, definitions of new names | Keyword fix can change behaviour with decorators/`__getattr__`/dynamic callees (see 3.3) |
| Never invalid Python | Output always compiles | Corpus compile test | Only 20 files; no fuzzing |
| Comments and layout kept | Lossless writer | Corpus comment test | New nodes render via `ast.unparse` until ruff runs |
| Idempotent | Second run changes nothing | Rerun test on small corpus files | Not checked on large files, nor with the CLI + ruff path |
| Explained | Every skip has a reason | `SkippedFix.reason` | Reasons are free text, not a closed enum |
| Independent verification | An external checker agrees | **Not built** | Largest single gap (phase 1) |

## 2. Where the project stands (honest inventory)

Shipped:
- Lossless mutable AST, format-preserving writer with annotation patching.
- Rule ontology (closed vocabulary, predicate algebra, canonical JSON catalog, schema, load-time invariants).
- Reference engine, fix runner (parse once, one write, degraded halving mode, conflict handling, ordering).
- TYP003 hints with corroboration policy (default literal, call sites, provable returns, `-> None`), gold set of 34 cases, 20-module corpus.
- Protocol synthesis (attribute/method-only parameters), TypeVar synthesis (pass-through parameters), automatic import insertion, importable-name allow-list.
- `astart check` / `astart fix` CLI (text/JSON output, `--diff`, `--check`, `--safe-only`, atomic writes, encodings).
- Probe on the corpus: 316 `-> None`, 200 inferred hints, 63 Protocols, 8 TypeVars, 174 keyword calls.

Known weaknesses (all observed, none hypothetical):
- **Recall is low by design.** Refused today: `x=-1`, `x=1+2`, `try/finally` returns, f-string returns, falling-off-the-end where inference disagrees, methods' call sites.
- **Methods are second-class.** `self.method(...)` and `Class.method(...)` call sites are not resolved, so methods get hints only from defaults and provable returns.
- **Large files are slow and superlinear** (12,000-line file ~47 s; 2,400-line ~3 s). Cost is the semantic worklist plus repeated tree walks.
- **Protocol members are untyped** unless call arguments are literals. Return types of members are always missing. Output therefore still triggers TYP003 on the Protocol's own methods.
- **Single-module world.** No cross-module call sites, no imported types, no third-party signatures.
- **Inference is a hint source, not a prover.** Its output is only accepted when syntax independently agrees; it knows `x * 2 -> int`, `seq[0] -> Sequence[int]` mistakes exist.
- **Two `object` annotations** in `formatting.py` predate this work and break the project's own rule.
- **Final review of the synthesis work is still in progress**; findings will be triaged before anything below is built on it.

## 3. The accuracy model

Everything in the roadmap hangs on one idea: **a fix is applied only when two independent sources agree, and a third (an external type checker) does not object.**

### 3.1 Evidence ladder (strongest first)

| Level | Evidence | Example | Use |
| --- | --- | --- | --- |
| E0 | Syntax proves it | `-> None` with no `return value`; literal default | proven |
| E1 | Declared elsewhere | Existing stub, base-class signature, `@overload`, protocol/ABC being implemented | proven when exact |
| E2 | Closed-world usage | All in-module call sites agree and the function does not escape | guarded |
| E3 | Open-world usage | Call sites across the project (cross-module) | guarded, needs project graph |
| E4 | Library signature | Argument flows into a typeshed-typed call (`open(path)`) | guarded |
| E5 | Inference engine | Graph inference proposal | candidate only, never alone |
| E6 | External checker | pyright/mypy accepts the result and reports no new error | **gate** for every guarded fix |

Policy to implement: a guarded fix needs (E2 or E3 or E4) AND (E5 agrees OR E0 proves) AND E6 does not object.

### 3.2 Metrics and benchmarks (build before anything else)

Without numbers every improvement is an argument. Required harness, `benchmarks/` + `tests/bench_*`:

- **Precision**: fraction of written annotations that a held-out ground truth considers correct. Target ≥ 99.5% guarded, 100% proven.
- **Recall**: fraction of ground-truth annotations recovered.
- **Ground truth sources**: (a) take well-typed open-source code, **strip** its annotations, run `fix`, compare (the standard "annotation recovery" benchmark; the corpus tests already do half of it); (b) typeshed stubs for stdlib modules; (c) hand-verified gold set (extend from 34 to ≥ 500 cases, grouped by failure class).
- **Semantic-equivalence check**: compile + run the project's own tests before and after on 10 pinned open-source projects; outputs identical.
- **Checker delta**: pyright/mypy error count before vs after; fixes that add errors are bugs.
- **Throughput**: lines/second and peak memory per size bucket (500, 2k, 12k, 50k lines).
- **Stability**: idempotence and "fixed point in ≤ 3 rounds" on every benchmark file.

Exit criterion for every later phase: the dashboard did not regress on precision and the phase's target metric moved.

### 3.3 Why keyword fixes need the same rigour

`f(1, 2)` → `f(a=1, b=2)` is not always safe. Refuse or prove for: decorated callees that change signature, `__getattr__`/`__call__` indirection, callees overridden in subclasses with different parameter names (Liskov-violating but real), C-implemented or positional-only parameters (`/`), parameters renamed across versions, callee rebinding (`f = other`), conditional definitions, callbacks stored and called through containers, `functools.wraps`-less wrappers. Today `calls.add-keywords` binds through the analyser and refuses unresolved callees; the matrix above is not yet exhaustively tested.

## 4. Roadmap

Phases are ordered by dependency and by value per risk. Each lists deliverables, tests, and an exit criterion. Estimates are relative effort (S ≤ 1 week, M ≈ 2–3 weeks, L ≈ 1–2 months), single developer.

### Phase 0 — Close out the current slice (S)

- Triage final-review findings; fix Critical/Important with RED→GREEN tests.
- Replace the two `object` annotations in `formatting.py`.
- `tests/test_graph_document.py` RUF043 lint item.
- Decide whether `ruff format` drift in pre-existing files is accepted; initialise git so diffs are reviewable.
- Run Exactus (owner) and clear findings.

Exit: reviewer clean, `ruff check` clean on the whole repo, suite green.

### Phase 1 — Measurement and the external-checker gate (M) — **highest priority**

1.1 Benchmark harness (section 3.2) and a published `docs/benchmarks.md` with the first baseline.
1.2 **Checker oracle**: run `basedpyright`/`pyright` (and optionally `mypy`) on the file before and after; compute new diagnostics; a fix whose application introduces a new error in the same file is rolled back and reported `rejected-by-checker`. Implementation: run once per round on the whole file (batch), bisect on failure using the runner's existing halving machinery. Cache by content hash.
1.3 Fuzz the writer: take each corpus module, apply random subsets of fixes, require compile + comment preservation + AST-equal-after-annotation-strip.
1.4 Closed enum for skip reasons (`conflict`, `escapes`, `disagree`, `checker-rejected`, `unresolved-callee`, …) so reports can be aggregated.
1.5 Idempotence test through the full CLI (astart + ruff) on all corpus files, not only ≤ 700-line ones.

Exit: dashboard exists; checker gate on by default for guarded fixes; zero checker regressions on the benchmark.

### Phase 2 — Resolution core: methods, classes, attributes (L)

The biggest recall unlock, because most real code is object-oriented.

2.1 **Method and constructor call resolution**: `self.m(...)`, `obj.m(...)` when `obj`'s class is known (assigned from `Class(...)`, annotated, or `self`), `Class.m`, `super().m`, `cls(...)`, `@classmethod`/`@staticmethod`, inherited methods via the MRO, class instantiation to `__init__`/`__new__`/dataclass fields.
2.2 **Attribute types**: infer `self.x` from `__init__` assignments and every assignment in the class; emit class-level annotations and `Final`/`ClassVar` only when all assignments agree.
2.3 **Override awareness**: a method that overrides a base method inherits the base signature (E1); never contradict it; keyword fixes use the base parameter names when they differ.
2.4 **Escape analysis v2**: replace the name-read heuristic with a proper "function used as a value" analysis (callbacks, `functools.partial`, `map`, decorators, registries, `getattr`), including attribute escapes.
2.5 **Flow-sensitive local typing**: narrowing by `isinstance`, `is None`, truthiness, early return, `assert`; join at merge points; loop-carried types with widening to a fixpoint.

Exit: method recall on the benchmark ≥ 3× the Phase 1 baseline at unchanged precision.

### Phase 3 — Project-wide and library knowledge (L)

3.1 **Project graph**: resolve imports across modules (absolute, relative, `__init__` re-exports, `__all__`, conditional imports), build a whole-project call graph with incremental invalidation by content hash.
3.2 **Cross-module call sites** (E3) for hints and keyword fixes. A function in a package is only "closed world" if it is private (`_name`) or not exported; public APIs get guarded-only hints with a configurable "assume external callers" switch.
3.3 **Typeshed / library signatures** (E4): load typeshed stubs and installed packages' `py.typed` / stub packages so argument flow into library calls proves types (`os.path.join(p, ...)` → `p: str | PathLike[str]` is *not* a hint; only exact, single-type flows qualify) and so keyword binding works for library callees (`subprocess.run(cmd, True)` → `check=True` is risky; allow-list only, with a curated "safe to keyword" table first).
3.4 **Third-party typing information**: reuse inferred return types of called library functions when the stub gives a single concrete type.
3.5 **Version awareness**: target Python version from `requires-python`, so features (`X | Y`, PEP 695, `Self`, `TypeAlias`) are emitted only when supported.

Exit: cross-module recall target met; no regression in precision; project-wide run on a 100k-line repo within the performance budget (phase 8).

### Phase 4 — Richer annotations (L)

Ordered by value/risk:

4.1 **Variable and attribute annotations** (`x: list[int] = []`, empty containers from later `append`s, `dict` value types, `defaultdict`), only for module/class level or when a checker needs them (empty-container cases), never gratuitous local annotations.
4.2 **Optional and unions**: `None` defaults → `T | None` where the body or call sites prove the type (today refused); union returns where every branch is provable.
4.3 **Containers and element types**: `list[int]` from literals and comprehensions, `dict[str, int]`, tuple shapes, `set`, `frozenset`, iteration targets; narrow to protocols (`Sequence[int]` vs `list[int]`) based on the *parameter* use (read-only → `Sequence`/`Iterable`/`Mapping`, mutated → `list`/`dict`): the "accept general, return specific" rule.
4.4 **Callable types**: parameters called as functions → `Callable[[int], str]` from call arguments and result use; `ParamSpec` for decorators and wrappers.
4.5 **`Self`, `ClassVar`, `Final`, `Literal`, `TypeAlias`, `NewType`** where syntax proves them.
4.6 **Generators and async**: `Iterator[T]`/`Generator[...]`/`AsyncIterator[...]`/`Awaitable[...]` returns, `__aiter__`/`__iter__` protocols.
4.7 **Data-carrier synthesis**: `TypedDict`/`NamedTuple`/`@dataclass` from dict-literal and tuple-return usage (a *suggest* fix first; guarded only with the checker gate).
4.8 **`@overload` synthesis** for functions with provably distinct argument-type-to-return-type behaviours (suggest-only until proven).

Each item ships behind its own catalog fix with safety class, gold cases, and checker gate.

### Phase 5 — Protocol and TypeVar synthesis, advanced (L)

Protocol (today: attribute/method-only parameters):

5.1 **Typed members**: member return types from how the result is used or from known-source calls; parameter types from arguments (variables via flow typing, not just literals); async methods (`await p.m()` → `async def m`), generator members, context-manager members (`__enter__`/`__exit__` from `with p:`), iteration (`for x in p` → `__iter__`), indexing (`p[k]` → `__getitem__`), operators, truthiness/`len(p)`. Today these uses *refuse*; each becomes a supported member kind with its own tests.
5.2 **Reuse before create**: match against existing Protocols, ABCs and `typing`/`collections.abc`/`os` protocols (`SupportsRead`, `Iterable`, `Sized`, `PathLike`, `typing.IO`) — prefer a standard library protocol over a synthesized one when the member set matches exactly or is a subset; subsumption (if `P1 ⊂ P2` members, reuse `P2` only when every user can satisfy it, otherwise keep minimal).
5.3 **Merge across functions**: unify near-identical Protocols (same members) project-wide into one generated module `_protocols.py` (config switch) instead of per-function classes; stable naming from members (`SupportsReadWrite`) with collision handling and a rename map recorded in a lockfile so names do not churn between runs.
5.4 **Placement and exports**: module-level Protocols for private functions, shared module for public APIs; `__all__` and circular-import safe placement (`TYPE_CHECKING` block when an annotation is only needed for typing).
5.5 **`runtime_checkable`** only when `isinstance` is applied to the parameter.
5.6 **Callback protocols** (`__call__`) for parameters that are called, with keyword names preserved.
5.7 **Attribute members**: distinguish read-only properties from writable attributes (writes currently refuse); `ClassVar` vs instance.
5.8 **Verification**: every synthesized Protocol is checked against the *actual* call sites by the external checker (E6); if a call site argument does not satisfy it, widen the Protocol or drop it.

TypeVar (today: pass-through to return, classic `TypeVar`):

5.9 **Bound TypeVars**: `x.close(); return x` → `T = TypeVar("T", bound=CloseProtocol)` (combine with the Protocol machinery).
5.10 **Constrained TypeVars** only from `isinstance` exhaustive branches or overloads.
5.11 **Multiple variables** and relations: `def pair(a, b): return [a, b]` → `list[T | U]` vs `list[T]` decided by call-site evidence; `dict[K, V]` keys/values; `Iterable[T] -> list[T]` for element pass-through (`def first(items): return items[0]` → `Sequence[T] -> T`).
5.12 **`Self`** instead of a TypeVar for methods returning `self`/`cls()`.
5.13 **Target-version switch**: PEP 695 `def f[T](x: T) -> T` when `requires-python >= 3.12`, classic `TypeVar` otherwise; `ParamSpec`/`TypeVarTuple` for variadic pass-through.
5.14 **Variance and naming**: `T_co`/`T_contra` when usage proves it; avoid names that shadow user symbols; one declaration reused across a module (done) and optionally project-wide.

### Phase 6 — Imports as a first-class subsystem (M)

Today: a fixed allow-list (`known_imports`), merge into existing `from m import ...`, place after the leading import block.

6.1 **Name resolver**: a real symbol table of the project and installed packages so any type that appears in a synthesized annotation can be imported from its **canonical public** location (`collections.abc.Sequence`, not `typing.Sequence`; `pathlib.Path`; project classes via the shortest valid import path honouring `__all__`).
6.2 **Import style**: follow the file's existing style (`import x` vs `from x import y`, aliases, relative vs absolute, one-per-line vs grouped), and the project's isort/ruff-isort configuration.
6.3 **Circular-import and runtime-cost safety**: place type-only imports under `if TYPE_CHECKING:` when importing at runtime could create a cycle or load heavy modules; use `from __future__ import annotations` or string annotations accordingly (only when version/semantics allow; check `@dataclass`/pydantic runtime annotation consumers and refuse for them).
6.4 **Shadowing and collisions**: never bind a name that something else already uses; use qualified module access (`pathlib.Path`) or an alias when needed.
6.5 **Unused-import cleanup** for imports the fix made redundant (and only those).
6.6 **Order**: let ruff's import sorting run in the final format phase, but make astart's own placement deterministic and conflict-free beforehand.

### Phase 7 — Soundness of keyword fixes (M)

7.1 The danger matrix of section 3.3 turned into ~60 tests.
7.2 **Positional-only / keyword-only awareness** end to end, including `/`, `*`, `**kwargs` forwarding, `functools.partial`, `super().__init__(...)` chains.
7.3 **Constructor and dataclass calls** (`Point(1, 2)` → fields by name; `NamedTuple`, `attrs`, pydantic models with their own rules).
7.4 **Method calls** (needs Phase 2), **bound-method callbacks**, `staticmethod`/`classmethod`.
7.5 **Library keyword table**: curated, versioned table of stdlib/third-party signatures where positional-to-keyword is safe, generated from typeshed and verified by tests; never for C builtins that are positional-only.
7.6 **Style controls**: threshold (e.g. do not keyword the first argument of obvious single-arg calls, `len(x)`, `print(x)`), configurable allow/deny lists by callee, `min_positional` setting. Today every keyword-capable argument is converted.
7.7 **Idempotence with autoformat**: line wrapping decisions are left to ruff; verify calls stay valid after wrapping.

### Phase 8 — Performance and scale (M–L)

8.1 Profile and remove the superlinear costs (semantic worklist, repeated tree walks, per-node binding). Target: ≤ 5 s for 12k lines, ≤ 30 s for 100k lines single-threaded.
8.2 **Incremental / cached runs**: content-hash cache of per-file facts and hints; only re-analyse files whose dependencies changed.
8.3 **Parallelism**: process pool per file for independent files; project-graph build once, shared read-only.
8.4 **Streaming CLI**: results as files finish; `--jobs`.
8.5 **Memory budget** tests on the largest benchmark.

### Phase 9 — Product surface (M)

9.1 **Configuration**: `[tool.astart]` in `pyproject.toml` (rules, select/ignore, safety ceiling, per-path overrides, target version, protocol/typevar style, import placement, library tables). The ontology's `Profile` entity already models this; wire it.
9.2 **Baselines and suppression**: fingerprint-stable baseline file; inline suppressions are a rule of this project *not to write*, so provide external per-path ignores instead.
9.3 **Reporters**: SARIF, GitHub annotations, JUnit, `--statistics`.
9.4 **Editor/LSP**: diagnostics + code actions ("add type hint", "synthesize Protocol") over the same engine.
9.5 **Pre-commit hook and CI recipe**; `--check` as the CI gate.
9.6 **Interactive review mode**: show each guarded fix with its evidence ladder and ask; "accept all high-confidence".
9.7 **Explain**: `astart explain TYP003 <location>` prints the evidence behind a hint or the reason for a skip.
9.8 **Safe rollback**: `--backup`/undo journal (writes are already atomic).

### Phase 10 — Ontology completion and the rest of the rule set (L)

From the ontology spec, still unbuilt:
- Docs: DOC fixers (missing docstrings, parameter sections from signatures + inferred types, `Raises`, `Returns`).
- Whitespace/blank-line normalisation, `Constants`-class grouping with `Final`, bare-import rewriting (ordering relations already specified).
- Delegation relation to ruff for rules ruff already fixes.
- Profiles, relations (`supersedes`, `conflicts_with`, `implies`) exercised by real data.
- `Maturity` lifecycle (experimental → stable) driving defaults.
- Rule authoring kit: scaffold + example-as-test generator, so a new rule is a JSON entry + a provider + an applier + examples.

## 5. Cross-cutting engineering

| Concern | Plan |
| --- | --- |
| Confidence calibration | Attach a numeric confidence to every candidate from the evidence ladder; calibrate against the benchmark so "0.9" means 90% observed precision; expose a `--min-confidence` knob |
| Safety classes | Keep `proven / guarded / suggest / none`; add `rejected-by-checker` as a reported outcome, never silent |
| Determinism | Stable ordering, stable synthesized names (lockfile for Protocol names), no dict-order or set-order dependence, no time/random |
| Error containment | Per-file and per-fix isolation already exists; add a per-file timeout and per-fix watchdog |
| Test strategy | Gold sets by failure class; property tests (random programs from a grammar → strip → fix → type-check); mutation testing on the policy code; corpus growth to ≥ 100 real modules; regression test per reviewer finding |
| Documentation | Evidence ladder and refusal catalogue as user-facing docs ("why wasn't X annotated?") |
| Convention compliance | Keep: no suppression comments, no `Any`/`object` annotations, keyword-only calls, Google docstrings, `@final Constants` |

## 6. Suggested order and milestones

| Milestone | Phases | Outcome |
| --- | --- | --- |
| M0 "Trustworthy slice" | 0 | Current work reviewed and clean |
| M1 "Measured" | 1 | Numbers, checker gate, fuzzing; every later claim is testable |
| M2 "Object-oriented code works" | 2, 7.2–7.4 | Methods, attributes, constructors resolved; biggest recall jump |
| M3 "Whole project" | 3, 6 | Cross-module evidence, canonical imports, version awareness |
| M4 "Precise types" | 4 | Optionals, containers, callables, variables |
| M5 "Structural and generic done properly" | 5 | Typed Protocols, reuse of stdlib protocols, bound TypeVars, `Self`, PEP 695 |
| M6 "Fast and shippable" | 8, 9 | Scale, config, CI/editor integration |
| M7 "Whole ontology" | 10 | Docs, whitespace, constants, delegation |

If only one thing is built next: **Phase 1** (checker oracle + benchmark). It converts "we think it is precise" into a measured claim and makes every later phase safe to attempt.

## 7. Risk register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Wrong annotation breaks a user's type check | Loss of trust | Checker gate, guarded ceiling by default only where precision ≥ target, `--safe-only` |
| Keyword fix breaks dynamic code | Runtime bug | Danger matrix tests, refuse on any uncertainty, library allow-list |
| Synthesized Protocol churn between runs | Noisy diffs | Deterministic naming, name lockfile, reuse-before-create |
| Inference engine regressions | Accuracy drops silently | Benchmarks in CI with threshold failures |
| Performance on big repos | Unusable | Phase 8, incremental cache, parallelism |
| Python version drift (PEP 695, `Self`, 3.14 annotations) | Invalid output on older targets | Version-aware emission, tests per target version |
| Scope creep into a full type checker | Never ships | Rule: astart proposes and verifies with an external checker; it does not become one |
| Unbounded surface of Python semantics | Missed edge cases | Refusal catalogue + fuzzing + corpus growth; every new construct starts as "refuse" |

## 8. Decisions needed from you

1. **Checker oracle**: is it acceptable to depend on `pyright`/`basedpyright` (and optionally `mypy`) being installed for guarded fixes? (Recommended: yes, optional, auto-detected; without it guarded fixes need a higher evidence level.)
2. **Default aggressiveness**: guarded by default for `fix` (current behaviour) or proven-only by default with `--guarded` opt-in?
3. **Python target**: classic `TypeVar` only (current) or version-aware PEP 695?
4. **Protocol placement**: per-function Protocols next to the code (current) or a generated shared module, and who owns its name stability?
5. **Scope of the library table** for keyword fixes: stdlib only, or also named third-party packages?
6. **Git**: initialise a repository now so reviews and rollbacks are diff-based (strongly recommended).

## 9. Immediate next actions (after the pending review)

1. Triage the final-review findings (Phase 0).
2. Build the benchmark harness and take the baseline (Phase 1.1).
3. Prototype the pyright oracle on the corpus to measure how many current fixes it would reject (Phase 1.2) — this answers decision 1 with data.
4. Plan Phase 2 in detail (method resolution is the largest recall item and has the most design risk).
