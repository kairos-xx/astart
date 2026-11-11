# Native transformations

- `aliases.py`: bounded PEP 695 alias optimization on existing AST nodes.
- `alias_patterns.py`: type-pattern matching and anti-unification.
- `insertion.py`: explicit insertion with lexical collision checks.
- `constants.py`: literal extraction through existing scope evidence.

Documentation wrapping belongs to `astart.docstrings.wrapping`. Source/token
ownership belongs to `astart.source`; transformations do not own another
parser or semantic graph.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Native AST insertion, alias extraction and constant transformations.
- [`alias_patterns.py`](alias_patterns.py) — Match type-only AST patterns without interpreting annotation metadata.
- [`aliases.py`](aliases.py) — Plan bounded PEP 695 alias extraction on the authoritative native AST.
- [`constants.py`](constants.py) — Extract comparison literals using native nodes and lexical scopes.
- [`insertion.py`](insertion.py) — Explicit native AST insertion with lexical binding and collision checks.

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
