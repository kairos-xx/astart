# Source infrastructure

The source package owns the authoritative extended AST and lexical state:

- `api.py`: parsing and emission behind the public `astart` facade.
- `ast.py`: comment-aware modules and integrated documentation attachment.
- `tokens.py`: immutable token snapshots and native node spans.
- `formatting.py`: bounded lexical emission and source preservation.
- `errors.py`: shared source-preservation failures.
- `delta.py`: incremental reconciliation.
- `transactions.py`: staged edits and rollback.
- `node_attributes.py`: typed native metadata access.
- `comment_directives.py`: structured comment controls and suppressions.

Moving these implementations does not change node identity, traversal,
transactions or parsing policy. Domain operations consume these same nodes.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`TREE_DUMP.md`](TREE_DUMP.md) — From a complete installed astart project:
- [`__init__.py`](__init__.py) — Authoritative source AST, tokens, transactions and lexical emission.
- [`api.py`](api.py) — Core source operations independent of the rule-catalog API.
- [`ast.py`](ast.py) — Python AST extensions that preserve tokenizer comments across edits.
- [`comment_directives.py`](comment_directives.py) — Parse comment-token directives into native suppression rule nodes.
- [`delta.py`](delta.py) — Identity-aware incremental source-map reconciliation for Python ASTs.
- [`errors.py`](errors.py) — Shared failures at the source-preservation boundary.
- [`formatting.py`](formatting.py) — Conservative, source-slice-preserving editor for mutable Python ASTs.
- [`metrics.py`](metrics.py) — Execution sensors: decorator-based timing for the conversion pipeline.
- [`node_attributes.py`](node_attributes.py) — Typed access to attributes that Astart attaches to ``ast`` nodes.
- [`tokens.py`](tokens.py) — Immutable lexical snapshots for mutable, comment-aware Python AST nodes.
- [`transactions.py`](transactions.py) — Staged annotation and import edits with guarded in-place rollback.
- [`tree_dump.py`](tree_dump.py) — Export the complete comment-aware AST as deterministic JSON.
- [`typeuniondict.py`](typeuniondict.py) — Resolve registered Python type expressions without evaluating source.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
