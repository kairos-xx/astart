# Dev-Pair Contradiction Root-Cause Analysis

Root-cause table for every contradiction produced by `scripts/compare/pair_wrong.py` on
`fixtures/untyped.py` against `fixtures/typed_author.py` (`--engine --min-confidence 0.5`), per
task G-04.

After L2 scorer updates (G-02 `object` wildcard narrowing, G-05 `Generator`
normalisation, protocol structural relation), 11 lines remain from
`pair_wrong.py` (4 parameters/returns, 7 variables):

| node | wrote | author | basis | cause | fix task |
| --- | --- | --- | --- | --- | --- |
| `SupportsVector.__add__.other` | `int` | `SupportsVector` | `engine` | Engine types stub protocol binary dunder parameter from arithmetic calls elsewhere in the module instead of keeping the self/protocol type | P-07, AF-03 |
| `duplicate_scope_name.value` | `int` | `str` | `engine` | Inner function `duplicate_scope_name(value)` shadows the module-level function; engine merges call-site evidence across the shadowed name | X-02, M2-09 |
| `function_with_generic_types.generic_function.container` | `dict[str, int] \| list[int] \| str` | `Mapping[T, U] \| Sequence[T]` | `engine` | Author uses generic abstract protocols (`Mapping[T, U] \| Sequence[T]`) with type variables; engine unions concrete call-site container types | M4-16, P-07 |
| `function_with_mutable_default_like_pattern.store` | `int \| None` | `list[object] \| None` | `engine` | Parameter `store=None` reassigned to `[]` and mutated via `store.append(value)`; engine conflates element type `int` with container parameter type | I-09, M2-09 |
| `HybridContainer.__or__.merged` | `HybridContainer` | `Self` | `negotiated` | Local variable initialized from `HybridContainer(...)` inside `__or__`; author writes `Self` while negotiator writes concrete class name `HybridContainer` | G-08, W-11 |
| `function_with_deep_attribute_assignment.child` | `None` | `Node` | `engine` | `child = root.add(Node(...))` where `add` returns its argument on a function-local class; engine resolves the call return to `None` | I-10, M2-02 |
| `function_with_deep_attribute_assignment.leaf` | `None` | `Node` | `engine` | Same as `child`: `leaf = child.add(Node(...))` on the nested `Node` class resolves to `None` instead of the returned argument type | I-10, M2-02 |
| `function_with_hybrid_container_stress.merged` | `int` | `HybridContainer` | `engine` | `merged = left \| right` uses custom `HybridContainer.__or__`; engine applies numeric bitwise-or rule (`int`) instead of custom `__or__` return | I-10, M2-02 |
| `function_with_metaclass_registry_stress.registry` | `None` | `dict[str, type[object]]` | `engine` | `registry = RegistryMeta.registry` reads a metaclass attribute initialized on class creation; engine sees default `None` or unresolved class attribute | I-11, M2-06 |
| `function_with_nested_default_factories.tree` | `defaultdict[str, int]` | `defaultdict[str, defaultdict[str, list[int]]]` | `engine` | Nested `defaultdict(lambda: defaultdict(list))` factory; engine flattens inner lambda factory value type to `int` | I-09 |
| `function_with_partial_reduce_and_operator_stress.add_five` | `int` | `Callable[[int], int]` | `engine` | `add_five = partial(operator.add, 5)` returns a `functools.partial` callable, but engine unwraps the underlying `operator.add` return type `int` | I-21, M4-17 |

Resolved since the first audit: `_.value` (synthesised `ValueProtocol` vs
`str` now reads as looser) and `Vector.__add__.other` (`Vector` vs
`SupportsVector` now reads as narrower) after protocol structural relation
landed in `recovery.relation`.
