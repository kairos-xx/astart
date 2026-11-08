# `stubs/`

Read typeshed-style stubs: locate, parse and resolve names.

<!-- exactus:inventory:start -->
## Directory contents

### Files

- [`__init__.py`](__init__.py) — Read typeshed-style stubs: locate, parse and resolve names.
- [`conditions.py`](conditions.py) — Evaluate the ``if`` tests that stub files use to branch by environment.
- [`locate.py`](locate.py) — Find a copy of typeshed on this machine.
- [`parser.py`](parser.py) — Read one stub file into the names it defines.
- [`resolver.py`](resolver.py) — Resolve a qualified name to its definition across stub files.
- [`returns.py`](returns.py) — Return types that typeshed states plainly enough to rely on.
- [`versions.py`](versions.py) — Which stdlib modules exist in which Python versions (``VERSIONS``).

### Subdirectories

No subdirectories.

<!-- exactus:inventory:end -->
