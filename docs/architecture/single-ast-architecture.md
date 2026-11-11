# Single AST architecture decision

Status: accepted direction; migration in progress. Date: 2026-11-09.
The task acceptance is zero post-initial full-module parses for ordinary
annotation, comment and documentation edits, with exact untouched source.
This document does not claim the current implementation meets that target.

## Authority and boundaries

`CommentedModule` owns executable nodes, comment/doc views and stable node
identities. `SourceTokenizer` owns revision-scoped lexical records.
`IncrementalSourceGraph` owns source/node changes and dependency propagation.
`FormatPreserver` emits source edits. Extend these existing components rather
than maintaining a second inferred AST or adding a CST dependency.

The original decoded text and immutable token snapshots are views of a
revision. They must not become competing mutation authorities. AST byte
columns and tokenizer character columns are distinct coordinate systems.
All transactions use one explicit original coordinate space and reject
stale revisions, overlaps and ambiguous ownership before commit.

Ordinary fixes mutate the existing nodes. The emitter records output spans
while emitting replacements and rebases untouched spans through ordered
edits. It must not parse its emitted module to recover positions. Parsing
is allowed for a bounded piece of syntax returned by an external formatter,
such as a Ruff-formatted f-string expression. The island's grammar context,
parent identity, old structure and byte range are recorded before dispatch.
An independent full parse remains a test oracle or explicit audit operation.

## Invalidation and execution

Track field replacement and child-list mutations with a generation counter
and deduplicated dirty queue. Preserve old parent paths for deletions.
Update parent/order, binding, token and reverse evidence indexes through the
same transaction. Invalidate dependent facts and annotations transitively,
including retraction when supporting evidence disappears.

The existing unrestricted mutable AST API must remain compatible. Until all
mutations are tracked, explicit exhaustive reconciliation remains necessary
and costs O(N). The current lazy per-node token reads perform that check;
`token_snapshots(nodes=...)` performs it once for an entire read batch.
Changing those reads to trust stale caches would be a correctness regression.

Parallelism is opt-in and follows measurement. CPU workers receive immutable
module/SCC snapshots; only the coordinator changes the tree. Proposals carry
source and dependency revisions and commit in deterministic rule/node order.
Bound process counts, queues and cancellation waits. Never share one mutable
AST among concurrent writers. Keep serial execution when transfer/startup
cost exceeds the measured gain.

## Native token provenance and pyposast study

Inspected upstream [pyposast](https://github.com/JoaoFelipe/pyposast), revision
`ffc249c` (downloaded GitHub archive SHA-256
`aa4060c5747177e07b3aae5c02f80c16b060a7100ffce47d79a271ef417c8d19`).
Read `parser.py`, the visitor's initialization and position helpers, public
entry points and MIT license. This is a source inspection, not execution of
upstream tests or a complete behavioral compatibility claim.

Useful mechanisms include balanced delimiter stacks, bisected position
indexes, composite keyword locations, Unicode coordinate conversion and
parenthesis provenance. Its parser accepts an existing tree; copying the
whole visitor would retain many old-version branches and a separate mutable
position model. No upstream code is imported or vendored here.

The native implementation now extends `SourceTokenizer` with one-pass
punctuation pairing, constant-time partner queries and bisected lexical
parenthesized spans. Strings and comments cannot contribute punctuation.
The lexical enclosing range does not assert that parentheses are redundant;
AST parent-aware ownership must distinguish call and tuple syntax before
using such ranges for edits. Existing operator spans now skip continuation
newlines/comments when matching composite operators.

Remaining work includes complete keyword/delimiter ownership across node
families, adjacent literal provenance, trivia anchors and incremental token
state convergence. Python 3.13+ tokenization handles f-string boundaries;
there is no legacy string-content scanner or pyposast runtime dependency.

## Legacy features and compatibility

Native prose wrapping keeps a fitness state per line break and protects code
examples/directives. `wrap_tree` edits existing semantic documentation and
comment nodes without parsing or emitting source. Comment replacements use
the module's original lexical anchors; optional structural changes edit real
statement and annotation nodes. The source adapter delegates all emission to
the existing module infrastructure, whose validation still reparses emitted
source. Removing that emission reparse remains CC-10 work.

Print rewriting and numeric extraction now construct native AST nodes through
`insert_tree` and the explicit `transform` command. They remain outside the
annotation benchmark defaults. Binding/collision checks protect print calls;
scoped typed constants refuse unsafe class construction. See the
[legacy analysis](../analysis/legacy-project-analysis.md) for the source mapping,
confirmed legacy risks and exhaustive structural inventory.

Explicit and environment typeshed choices retain precedence. When neither
names a valid typeshed root, `find_typeshed` falls back to the typeshed
snapshot bundled inside the package (`astart/stubs/artifacts/typeshed/`). No
user-specific path or installed-package location is scanned, so every
machine resolves the same stubs.

## Verification, risks and rollback

Use `docs/planning/TODO.md` CC-09 through CC-13 as the dependency-ordered implementation
checklist. Tests must instrument parser calls, compare emitted source with an
independent oracle, and cover Unicode, CRLF, nested f-strings, comments,
PEP 695, decorators, moves/deletions and failed transaction rollback.
Benchmark 500 edits on a fixed 12k-line module; report actual timing, memory,
visited nodes and tokenized bytes. A 10x sequence improvement is a target,
not a measurement or a current claim.

The main risks are untracked list mutations, stale revisions, incorrect
trivia ownership and lost evidence retractions. Migrate subsystem by
subsystem behind tested internal interfaces. Keep compatibility paths until
parity is proven, but never silently claim a fallback satisfies the
zero-reparse mode. No public API removal, dependency addition or persisted
schema migration is authorized by this internal refactor.

## Bounded implementation handoff

### Symbol and directive ownership decision

Source-spelling substitution cannot distinguish a resolved reference from a
shadowed identifier, string value, attribute label or annotation metadata.
The chosen replacement uses the existing symbol registry and original AST
objects: batch binding, identity-based reference redirection and scope-checked
renaming. It adds no module parse, replacement tree or source-search pass.
Fresh annotation construction remains a separate boundary; binding accepts
the already constructed expression, preserves it and invalidates conclusions
through the shared analyzer. Legacy producers that still describe fresh type
expressions as strings remain candidates for native-constructor migration.

Suppression grammar now runs only when a COMMENT token is classified. Its
native selector nodes and semantic fields belong to that comment; encoding
and region controls are child nodes of ordinary comment tokens. Wrapping reads
the established fields instead of guessing controls from source text.
The parser never evaluates input. Moving the grammar retains existing
SuppressionRule/Spec import paths through re-exports. These APIs are additive;
rollback can remove callers of the new binding operations without changing
module ownership or introducing a second syntax representation. Whole-source
emission validation remains the explicitly open CC-10 boundary below.

`formatting.EmissionPlan` is the revision-checked lexical patch foundation.
It uses existing native `Patch` records and the shared formatter, indexes
cumulative shifts and returns None for spans requiring changed-node emission.
It drives lexical module emission. Next: emit changed
node locations, convert/rebase untouched UTF-8 spans, then remove module
reparses only after differential parity. CC-09 rollback remains separate.

`ContractGraph.seed_ablation` and `scripts.benchmark.ablation.measure_seed_origins`
provide a non-mutating seed-sensitivity baseline over the original AST.
Complete producer/acceptance accuracy ablation is still AL-18 work.

The native formatter now uses `FormatPreserver.plan` for its live lexical
path and exposes the validated plan through `CommentedModule.emission_plan`.
`AnnotationTransaction` supplies staged annotation-field ownership checks,
compile-only validation, documentation relinking and failure/interruption
rollback. Dependency imports now share the annotation batch: one absolute,
unaliased binding per declaration, conservative capture checks, original
body-list identity and in-place rollback. Equal-content raw list replacement
invalidates a pending transaction; retained container witnesses prevent ID
reuse. The emitter localizes a fresh contiguous import group as an insertion
patch, so original spans remain rebasable across it. Semicolon-line and
other root mutations keep the existing reconstruction path.

These are real integration steps, not completion of CC-09/CC-10:
compiler validation is not final source-equivalence proof, shared emission
still retains its parse validator, and general list/catalog operations plus
tracked mutation generations remain future work. Proposed annotation
locations are restored after validation; emission owns final coordinates.
