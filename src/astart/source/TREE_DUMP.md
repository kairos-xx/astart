# Custom AST JSON dump

From a complete installed astart project:

```bash
python -m astart.source.tree_dump path/to/input.py
python -m astart.source.tree_dump path/to/input.py --output path/to/tree.json
```

The default output is `input.ast.json`. JSON includes recursively expanded
AST fields, custom comment and docstring nodes, AST attributes, per-node token
snapshots, complete lexical token stream, and source. Semantic references
(`owner`, `expression`, `target`) are encoded as node IDs to avoid cycles.

This is a diagnostic export, not a deserialization format. Token snapshot
errors are propagated rather than silently hidden.
