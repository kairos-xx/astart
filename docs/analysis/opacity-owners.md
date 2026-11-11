# Opacity Owners

Every reason string reported by `scripts/compare/opacity_report.py` on `fixtures/untyped.py`,
`fixtures/*_untyped.py.txt` and `tests/corpus/extended` is assigned an owning
backlog task in `docs/planning/TODO.md` (task G-03). No reason is left unowned.

| reason | count (`fixtures/untyped.py`) | count (`tests/corpus/extended`) | owning task |
| --- | ---: | ---: | --- |
| `settled` | 162 | 570 | F-20 (settled nodes; no action needed) |
| `downstream of a blocked node` | 158 | 1256 | P-03, W-06, W-07, I-23 |
| `direct: unprovable Call` | 109 | 2192 | W-06, F-15, F-41, I-08, I-21 |
| `unsettled (no evidence)` | 96 | 14 | P-04, P-05, F-13, F-22 |
| `declared` | 63 | 7308 | F-16 (already annotated in input) |
| `direct: unprovable Name` | 51 | 566 | P-03, M4-17, G-10, I-15 |
| `direct: container literal mutated or not provable` | 36 | 129 | I-09, F-40, AL-04, AL-13 |
| `direct: function escapes as a value` | 28 | 259 | W-07, M2-08, P-06 |
| `direct: no evidence reaches it` | 24 | 0 | P-04, F-13, F-22, T-01, T-02 |
| `direct: stub, abstract or never returns` | 20 | 306 | T-02, M4-09, AF-03 |
| `direct: a call to it cannot be bound` | 16 | 526 | W-07, M2-02, M6-02 |
| `direct: unprovable Tuple` | 13 | 170 | I-17 |
| `direct: unprovable Dict` | 11 | 47 | F-07, I-17 |
| `direct: unprovable BinOp` | 11 | 107 | I-10, I-17 |
| `direct: unprovable Attribute` | 8 | 444 | I-11, I-12, M2-06, W-12 |
| `direct: generator` | 7 | 217 | M4-06, M4-03 |
| `direct: unprovable Subscript` | 5 | 175 | M4-01, I-17 |
| `direct: unprovable List` | 4 | 29 | I-17, F-07 |
| `direct: unprovable GeneratorExp` | 3 | 10 | F-40, M4-01 |
| `direct: unprovable IfExp` | 3 | 138 | I-01, I-19 |
| `direct: unprovable DictComp` | 2 | 7 | F-40, M4-01 |
| `direct: unprovable ListComp` | 2 | 33 | F-40, M4-01 |
| `direct: protocol result does not fit` | 2 | 61 | T-01, AF-03 |
| `direct: default or value not provable` | 1 | 252 | F-37, W-08, M4-12 |
| `direct: container used in an unknown way` | 1 | 31 | AL-04, I-09 |
| `direct: unprovable Yield` | 1 | 10 | M4-03, M4-06 |
| `direct: unprovable Await` | 1 | 114 | M4-02, I-07 |
| `direct: unprovable BoolOp` | 0 | 102 | M5-22, I-01, I-19 |
| `direct: unprovable Compare` | 0 | 22 | I-10 |
| `lost a contribution` | 0 | 5 | F-24 |
| `direct: unprovable SetComp` | 0 | 3 | F-40, M4-01 |
| `direct: argument unknown (star or many)` | 0 | 3 | AF-01, M4-05 |
| `direct: unprovable Lambda` | 0 | 2 | M4-17 |
| `direct: unprovable NamedExpr` | 0 | 1 | I-01 |
| `direct: unprovable Set` | 0 | 1 | I-17, F-07 |
