# Conversion report: [`dev/untyped.py`](../dev/untyped.py) to [`dev/typed.py`](../dev/typed.py)

*Generated Sun 08 Nov 2026, 19:12 WET by [`scripts/conversion_report.py`](../scripts/conversion_report.py). Do not edit; run the script again.*

In every code example `-` is how the converted code is ([conversion-output.py.txt](conversion-output.py.txt)) and `+` is how it should be (the author's `dev/typed.py`); the links go to the exact lines.

| Field | Value |
| --- | --- |
| files | [dev/untyped.py](../dev/untyped.py) · [dev/typed.py](../dev/typed.py) · [conversion-output.py.txt](conversion-output.py.txt) |
| tree | 816607625e67 |
| converted in | saved output reused |
| untyped / typed | 2725 / 5124 lines |
| settings | conversion mode (engine), negotiation on, variables on, minimum confidence 0.5, checker off |
| command | python scripts/conversion_report.py --min-confidence 0.5 |

## Summary

| Scope | To recover | Exact | Narrower | Looser | Unresolved | Wrong | Missing | Extra |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Parameters and returns | 482 | 221 (45.9 %) | 38 | 0 | 13 | 13 | 197 | 6 |
| Variables | 335 | 163 (48.7 %) | 3 | 4 | 15 | 13 | 137 | 14 |

```text
Parameters and returns   exact █████████░░░░░░░░░░░  45.9 %   wrong █░░░░░░░░░░░░░░░░░░░   2.7 %
Variables                exact ██████████░░░░░░░░░░  48.7 %   wrong █░░░░░░░░░░░░░░░░░░░   3.9 %
```

## Where the gap is, by the author's annotation

Compatible means valid but not identical (narrower or looser). Hard families are partly author choices or policy and bound the 90 % target.

| Author's annotation | Total | Exact | Compatible | Wrong | Missing | Share of gap | Hard | Tasks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | --- |
| Top type (object) | 137 | 0 | 23 | 9 | 105 | 29 % | yes | policy: astart never writes object; [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower |
| Scalar | 290 | 231 | 4 | 2 | 53 | 14 % |  | [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](TODO.md#f-37--default-literal-parameters-in-the-negotiator) |
| Builtin container | 111 | 75 | 0 | 0 | 36 | 9 % |  | [I-05](TODO.md#i-05--type-for-targets-from-common-iterables), [I-09](TODO.md#i-09--defaultdict-counter-deque-element-types-from-mutation), [I-17](TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](TODO.md#f-40--comprehensions-as-derived-nodes), [AL-07](TODO.md#al-07--bidirectional-expected-type-inference) |
| Type alias | 33 | 0 | 0 | 0 | 14 | 9 % | yes | [S-03](TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names) |
| Module class | 64 | 34 | 1 | 3 | 24 | 7 % |  | [M2-02](TODO.md#m2-02--constructorattribute-resolution), [W-12](TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](TODO.md#w-14--annotate-class-level-and-module-level-variables) |
| Callable | 37 | 12 | 0 | 5 | 19 | 6 % | yes | [M4-17](TODO.md#m4-17--callable-r-params), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding) |
| TypeVar | 25 | 0 | 0 | 0 | 23 | 6 % | yes | [M5-16](TODO.md#m5-16--multi-variable-relations), [I-18](TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding) |
| Library class | 32 | 8 | 0 | 1 | 20 | 6 % |  | [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](TODO.md#t-08--library-return-types-from-typeshed) |
| Generator/Iterator | 15 | 3 | 0 | 4 | 8 | 3 % | yes | [W-13](TODO.md#w-13--type-generators-as-iterator), [G-05](TODO.md#g-05--normalise-generator-defaults-and-subtype-spelling-in-the-scorer) |
| Optional | 24 | 11 | 2 | 0 | 11 | 3 % |  | [I-01](TODO.md#i-01--narrow-the-else-branch-by-complement), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [AL-01](TODO.md#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling) |
| Abstract collection | 23 | 1 | 15 | 2 | 5 | 2 % | yes | [M4-16](TODO.md#m4-16--accept-generalreturn-specific), [AL-13](TODO.md#al-13--mutation-summaries-decide-sequence-versus-list), [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) |
| ClassVar/Final | 7 | 0 | 0 | 0 | 7 | 2 % | yes | [AF-05](TODO.md#af-05--classvar-and-final-inference), [G-06](TODO.md#g-06--never-type-a-descriptor-attribute-as-its-value) |
| Union | 10 | 4 | 0 | 0 | 5 | 2 % |  | [AL-05](TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [I-19](TODO.md#i-19--join-and-simplify-unions-deterministically) |
| Self | 8 | 5 | 0 | 0 | 3 | 1 % | yes | [W-11](TODO.md#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name), [AF-02](TODO.md#af-02--annotate-selfcls-only-when-the-style-asks), [F-43](TODO.md#f-43--quote-instead-of-refusing) |
| Other | 1 | 0 | 0 | 0 | 1 | 0 % |  | [G-04](TODO.md#g-04--root-cause-every-remaining-contradiction) |

## Annotated copy of the converted code

[conversion-annotated.py.txt](conversion-annotated.py.txt) is the converted module with a bespoke comment on every line that differs from the author's: `# [FIX]` says what the line should be and the evidence in the untyped source that leads there, `# [ADD]` lists imports and definitions the author's file has and the converted one lacks. 353 commented lines; the first 40:

```python
# [ADD] from asyncio import run, sleep - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from collections.abc import AsyncGenerator, AsyncIterator, Iterator, MutableMapping - used in the author's annotations (first at typed.py:3276)
# [ADD] from contextvars import Token - used in the author's annotations (first at typed.py:4319)
# [ADD] from dataclasses import field - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from importlib import import_module - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from json import dumps, loads - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from math import nan - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from operator import add, mul - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from re import search, split - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from tempfile import NamedTemporaryFile, gettempdir - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from types import ModuleType - used in the author's annotations (first at typed.py:3130)
# [ADD] from typing import ClassVar, NamedTuple, NoReturn - used in the author's annotations (first at typed.py:2507)
# [ADD] from typing import ParamSpec, TYPE_CHECKING, TypeVar, cast, final - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from uuid import UUID - used in the author's annotations (first at typed.py:4294)
# [ADD] from uuid import NAMESPACE_DNS, uuid5 - the author's file imports these for code, not for annotations (its from-import style; see M8-27)
# [ADD] from weakref import ReferenceType - used in the author's annotations (first at typed.py:1898)
# [ADD] P = ParamSpec(name='P') - defined at typed.py:72; first used at typed.py:409
# [ADD] R = TypeVar(name='R') - defined at typed.py:73; first used at typed.py:409
# [ADD] T = TypeVar(name='T') - defined at typed.py:74; first used at typed.py:486
# [ADD] U = TypeVar(name='U') - defined at typed.py:75; first used at typed.py:1303
# [ADD] V = TypeVar(name='V') - defined at typed.py:76; not used later
# [ADD] W = TypeVar(name='W') - defined at typed.py:77; not used later
# [ADD] K = TypeVar(name='K') - defined at typed.py:78; not used later
# [ADD] N = TypeVar('N', int, float, complex) - defined at typed.py:79; not used later
# [ADD] class Constants: ... - defined at typed.py:83; first used at typed.py:776
# [ADD] type IntList = list[int] - defined at typed.py:105; not used later
# [ADD] type IntDict = dict[str, int] - defined at typed.py:106; first used at typed.py:108
# [ADD] type TestResult = dict[str, object] - defined at typed.py:107; first used at typed.py:2649
# [ADD] type ConditionalResult = list[int] | IntDict | str | int - defined at typed.py:108; first used at typed.py:2813
# [ADD] type NestedLoopFunc = Callable[[Sequence[Sequence[int]]], list[int]] - defined at typed.py:109; first used at typed.py:1800
# [ADD] type ExtendedPayload = object - defined at typed.py:110; not used later
# [ADD] type ExtendedMetadata = dict[str, object] - defined at typed.py:111; first used at typed.py:3262
# [ADD] type ExtendedContextMap = dict[str, object] - defined at typed.py:112; not used later
# [ADD] type ExtendedResultTuple = tuple['ExtendedResult', str, object, object] - defined at typed.py:113; first used at typed.py:4946
# [ADD] type ExtendedTestResult = dict[str, object] - defined at typed.py:114; first used at typed.py:4965
# [ADD] type PatternStressInput = Mapping[str, object] | Sequence[object] | None - defined at typed.py:115; first used at typed.py:3984
# [ADD] type PatternStressResult = tuple[int, int] | list[object] | dict[str, object] | object | str - defined at typed.py:116; first used at typed.py:3985
# [ADD] type ConfigMapping = MutableMapping[str, object] - defined at typed.py:119; not used later
# [ADD] type VectorFactory = Callable[[int, int], SupportsVector] - defined at typed.py:214; first used at typed.py:1069
# [ADD] class LocalMultiplierProtocol(Protocol): ... - defined at typed.py:4523; first used at typed.py:4549
```

## Wrong annotations (26), with code

Each one is a bug or a scoring difference (G-02, G-05, P-07, G-04).

how it is [conversion-output.py.txt:103](conversion-output.py.txt#L103) · should be [typed.py:201](../dev/typed.py#L201) · input [untyped.py:94](../dev/untyped.py#L94)

```diff
@@ SupportsVector.__add__.other · wrong · Module class @@
-    def __add__(self, other: int) -> int | Self:
+    def __add__(self, other: SupportsVector) -> SupportsVector:
```

**Why the author's type is `SupportsVector`** (reading `dev/untyped.py` only):

1. [untyped.py:513](../dev/untyped.py#L513) same-named method in Vector: `function_with_operator_overloading.Vector.__add__(self, other)` *(matched by name only)*

*Reading:* No source in this file shows the type; `SupportsVector` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `int`:** it differs from the author's `SupportsVector` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2704](conversion-output.py.txt#L2704) · should be [typed.py:3952](../dev/typed.py#L3952) · input [untyped.py:2099](../dev/untyped.py#L2099)

```diff
@@ _.value · wrong · Scalar @@
-def _(value: ValueProtocol):
+def _(value: str) -> str:
```

**Why the author's type is `str`** (reading `dev/untyped.py` only):

1. [untyped.py:2101](../dev/untyped.py#L2101) body calls a method: `value.upper()` → `is a str`

*Reading:* The sources show `isastr`, which does not add up to `str`: either a rule is missing or the author knew something this file does not say.

**Why astart wrote `ValueProtocol`:** it differs from the author's `str` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:543](conversion-output.py.txt#L543) · should be [typed.py:852](../dev/typed.py#L852) · input [untyped.py:384](../dev/untyped.py#L384)

```diff
@@ custom_context-> · wrong · Generator/Iterator @@
-def custom_context() -> Generator[str, None, None]:
+def custom_context() -> Generator[str]:
```

**Why the author's type is `Generator[str]`** (reading `dev/untyped.py` only):

1. [untyped.py:384](../dev/untyped.py#L384) generator: `the body contains 'yield'`
2. [untyped.py:390](../dev/untyped.py#L390) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`, which does not add up to `Generator[str]`: either a rule is missing or the author knew something this file does not say.

**Why astart wrote `Generator[str, None, None]`:** it differs from the author's `Generator[str]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2066](conversion-output.py.txt#L2066) · should be [typed.py:3047](../dev/typed.py#L3047) · input [untyped.py:1641](../dev/untyped.py#L1641)

```diff
@@ duplicate_scope_name.value · wrong · Scalar @@
-def duplicate_scope_name(value: int) -> str:
+def duplicate_scope_name(value: str) -> str:
```

**Why the author's type is `str`** (reading `dev/untyped.py` only):

1. [untyped.py:1741](../dev/untyped.py#L1741) call site passes: `duplicate_scope_name(value=duplicated_name)  ->  duplicated_name` *(matched by name only)*

*Reading:* No source in this file shows the type; `str` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `int`:** it differs from the author's `str` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2941](conversion-output.py.txt#L2941) · should be [typed.py:4308](../dev/typed.py#L4308) · input [untyped.py:2294](../dev/untyped.py#L2294)

```diff
@@ function_with_contextvars_and_chainmap.configs · wrong · Abstract collection @@
-def function_with_contextvars_and_chainmap(configs: list[dict[str, int]]):
+    configs: Sequence[MutableMapping[str, object]],
```

**Why the author's type is `Sequence[MutableMapping[str, object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2298](../dev/untyped.py#L2298) body calls len: `len(configs)`
2. [untyped.py:2639](../dev/untyped.py#L2639) call site passes: `function_with_contextvars_and_chainmap(configs=[{'fallback': 2}, {'seed': 99, 'other': 3}…  ->  [{'fallback': 2}, {'seed': 99, 'other': 3}]` → `list[dict[str, int]]`

*Reading:* The sources show `list[dict[str, int]]`; the author widened to the top type (`Sequence[MutableMapping[str, object]]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `list[dict[str, int]]`:** it is narrower than the author's `Sequence[MutableMapping[str, object]]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:2976](conversion-output.py.txt#L2976) · should be [typed.py:4366](../dev/typed.py#L4366) · input [untyped.py:2317](../dev/untyped.py#L2317)

```diff
@@ function_with_generator_send_throw_close.controlled_generator-> · wrong · Generator/Iterator @@
-    def controlled_generator() -> Generator[int, None, None]:
+    def controlled_generator() -> Generator[int, int | str | None, int]:
```

**Why the author's type is `Generator[int, int | str | None, int]`** (reading `dev/untyped.py` only):

1. [untyped.py:2317](../dev/untyped.py#L2317) generator: `the body contains 'yield'`
2. [untyped.py:2324](../dev/untyped.py#L2324) return: `current`
3. [untyped.py:2326](../dev/untyped.py#L2326) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`, which does not add up to `Generator[int, int | str | None, int]`: either a rule is missing or the author knew something this file does not say.

**Why astart wrote `Generator[int, None, None]`:** it differs from the author's `Generator[int, int | str | None, int]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:569](conversion-output.py.txt#L569) · should be [typed.py:894](../dev/typed.py#L894) · input [untyped.py:406](../dev/untyped.py#L406)

```diff
@@ function_with_generators.generator-> · wrong · Generator/Iterator @@
-    def generator() -> Generator[int, None, None]:
+    def generator() -> Generator[int]:
```

**Why the author's type is `Generator[int]`** (reading `dev/untyped.py` only):

1. [untyped.py:406](../dev/untyped.py#L406) generator: `the body contains 'yield'`
2. [untyped.py:408](../dev/untyped.py#L408) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`, which does not add up to `Generator[int]`: either a rule is missing or the author knew something this file does not say.

**Why astart wrote `Generator[int, None, None]`:** it differs from the author's `Generator[int]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:837](conversion-output.py.txt#L837) · should be [typed.py:1303](../dev/typed.py#L1303) · input [untyped.py:619](../dev/untyped.py#L619)

```diff
@@ function_with_generic_types.generic_function.container · wrong · Abstract collection @@
-    def generic_function(container: str | dict[str, int] | list[int]) -> int | str:
+    def generic_function(container: Sequence[T] | Mapping[T, U]) -> T | U:
```

**Why the author's type is `Mapping[T, U] | Sequence[T]`** (reading `dev/untyped.py` only):

1. [untyped.py:621](../dev/untyped.py#L621) body calls isinstance: `isinstance(container, Mapping)`
2. [untyped.py:622](../dev/untyped.py#L622) body calls a method: `container.values()` → `is a dict`
3. [untyped.py:623](../dev/untyped.py#L623) body indexes it: `container[0]`
4. [untyped.py:625](../dev/untyped.py#L625) call site passes: `generic_function(container=[1, 2, 3])  ->  [1, 2, 3]` → `list[int]`
5. [untyped.py:626](../dev/untyped.py#L626) call site passes: `generic_function(container={'a': 1, 'b': 2})  ->  {'a': 1, 'b': 2}` → `dict[str, int]`
6. [untyped.py:627](../dev/untyped.py#L627) call site passes: `generic_function(container='hello')  ->  'hello'` → `str`

*Reading:* The sources show `dict[str, int] | isadict | list[int] | str`, which does not add up to `Mapping[T, U] | Sequence[T]`: either a rule is missing or the author knew something this file does not say.

**Why astart wrote `dict[str, int] | list[int] | str`:** it differs from the author's `Mapping[T, U] | Sequence[T]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2908](conversion-output.py.txt#L2908) · should be [typed.py:4262](../dev/typed.py#L4262) · input [untyped.py:2266](../dev/untyped.py#L2266)

```diff
@@ function_with_import_and_reflection_stress-> · wrong · Top type (object) @@
-def function_with_import_and_reflection_stress(module_name: str, attr_name: str) -> dict[str, bool | str]:
+) -> dict[str, object]:
```

**Why the author's type is `dict[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:2271](../dev/untyped.py#L2271) return: `{'module': module.__name__, 'attr': attr, 'attr_type': attr_type.__name__, 'has_doc': boo…`

*Reading:* No source in this file shows the type; `dict[str, object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `dict[str, bool | str]`:** it is narrower than the author's `dict[str, object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:3232](conversion-output.py.txt#L3232) · should be [typed.py:4881](../dev/typed.py#L4881) · input [untyped.py:2544](../dev/untyped.py#L2544)

```diff
@@ function_with_mutable_default_like_pattern.store · wrong · Top type (object) @@
-def function_with_mutable_default_like_pattern(value: str, store: int | None = None):
+    store: list[object] | None = None,
```

**Why the author's type is `list[object] | None`** (reading `dev/untyped.py` only):

1. [untyped.py:2544](../dev/untyped.py#L2544) default value: `None` → `None`
2. [untyped.py:2546](../dev/untyped.py#L2546) body compares it with None: `store is None`
3. [untyped.py:2548](../dev/untyped.py#L2548) body calls a method: `store.append(value)` → `is a list`

*Reading:* The sources show `None | isalist`; the author widened to the top type (`list[object] | None`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `int | None`:** it is narrower than the author's `list[object] | None`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:703](conversion-output.py.txt#L703) · should be [typed.py:1091](../dev/typed.py#L1091) · input [untyped.py:513](../dev/untyped.py#L513)

```diff
@@ function_with_operator_overloading.Vector.__add__.other · wrong · Module class @@
-        def __add__(self, other: Vector) -> Vector:
+        def __add__(self, other: SupportsVector) -> Vector:
```

**Why the author's type is `SupportsVector`** (reading `dev/untyped.py` only):

1. [untyped.py:94](../dev/untyped.py#L94) same-named method in SupportsVector: `SupportsVector.__add__(self, other)` *(matched by name only)*

*Reading:* No source in this file shows the type; `SupportsVector` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `Vector`:** it differs from the author's `SupportsVector` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:871](conversion-output.py.txt#L871) · should be [typed.py:1350](../dev/typed.py#L1350) · input [untyped.py:645](../dev/untyped.py#L645)

```diff
@@ function_with_optional_types-> · wrong · Callable @@
-def function_with_optional_types() -> Callable[[None | int], int | str]:
+def function_with_optional_types() -> Callable[[object], object]:
```

**Why the author's type is `Callable[[object], object]`** (reading `dev/untyped.py` only):

1. [untyped.py:651](../dev/untyped.py#L651) return: `'default'` → `str`
2. [untyped.py:652](../dev/untyped.py#L652) return: `value`
3. [untyped.py:654](../dev/untyped.py#L654) return: `optional_function`

*Reading:* The sources show `str`; the author widened to the top type (`Callable[[object], object]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `Callable[[None | int], int | str]`:** it is narrower than the author's `Callable[[object], object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:1095](conversion-output.py.txt#L1095) · should be [typed.py:1679](../dev/typed.py#L1679) · input [untyped.py:838](../dev/untyped.py#L838)

```diff
@@ function_with_type_annotations_missing-> · wrong · Callable @@
-def function_with_type_annotations_missing() -> tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[[], int], Callable[[], int], Callable[[], int]]:
+def function_with_type_annotations_missing() -> tuple[
```

**Why the author's type is `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]`** (reading `dev/untyped.py` only):

1. [untyped.py:843](../dev/untyped.py#L843) return: `x + 1`
2. [untyped.py:847](../dev/untyped.py#L847) return: `x + y`
3. [untyped.py:851](../dev/untyped.py#L851) return: `x * y`
4. [untyped.py:855](../dev/untyped.py#L855) return: `sum(args)`
5. [untyped.py:859](../dev/untyped.py#L859) return: `sum(kwargs.values())`
6. [untyped.py:863](../dev/untyped.py#L863) return: `sum(args) + sum(kwargs.values())`
7. [untyped.py:865](../dev/untyped.py#L865) return: `(func1, func2, func3, func4, func5, func6)`

*Reading:* No source in this file shows the type; `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[[], int], Callable[[], int], Callable[[], int]]`:** it differs from the author's `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2404](conversion-output.py.txt#L2404) · should be [typed.py:3519](../dev/typed.py#L3519) · input [untyped.py:1903](../dev/untyped.py#L1903)

```diff
@@ RegistryBase.clone.data · wrong · Top type (object) @@
-        data: dict[str, int] = dict(self.__dict__)
+        data: dict[str, object] = dict(self.__dict__)
```

**Why the author's type is `dict[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:1903](../dev/untyped.py#L1903) assignment: `data = dict(self.__dict__)` → `dict[?, ?]`
2. [untyped.py:1904](../dev/untyped.py#L1904) adds elements: `data.update(overrides)`

*Reading:* The sources show a container but not its element type, so nothing here fixes `dict[str, object]`; the author's choice adds knowledge from outside this file.

**Why astart wrote `dict[str, int]`:** it is narrower than the author's `dict[str, object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:2949](conversion-output.py.txt#L2949) · should be [typed.py:4323](../dev/typed.py#L4323) · input [untyped.py:2298](../dev/untyped.py#L2298)

```diff
@@ function_with_contextvars_and_chainmap.current_map · wrong · Top type (object) @@
-        current_map: dict[str, int] = {'seed': len(configs)}
+        current_map: dict[str, object] = {"seed": len(configs)}
```

**Why the author's type is `dict[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:2298](../dev/untyped.py#L2298) assignment: `current_map = {'seed': len(configs)}` → `dict[str, int]`

*Reading:* The sources show `dict[str, int]`; the author widened to the top type (`dict[str, object]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `dict[str, int]`:** it is narrower than the author's `dict[str, object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:2987](conversion-output.py.txt#L2987) · should be [typed.py:4384](../dev/typed.py#L4384) · input [untyped.py:2328](../dev/untyped.py#L2328)

```diff
@@ function_with_generator_send_throw_close.generator · wrong · Generator/Iterator @@
-    generator: Generator[int, None, None] = controlled_generator()
+    generator: Generator[int, int | str | None, int] = controlled_generator()
```

**Why the author's type is `Generator[int, int | str | None, int]`** (reading `dev/untyped.py` only):

1. [untyped.py:2328](../dev/untyped.py#L2328) assignment: `generator = controlled_generator()`

*Reading:* No source in this file shows the type; `Generator[int, int | str | None, int]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `Generator[int, None, None]`:** it differs from the author's `Generator[int, int | str | None, int]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:3033](conversion-output.py.txt#L3033) · should be [typed.py:4469](../dev/typed.py#L4469) · input [untyped.py:2374](../dev/untyped.py#L2374)

```diff
@@ function_with_hybrid_container_stress.merged · wrong · Module class @@
-    merged: int = left | right
+    merged: HybridContainer = left | right
```

**Why the author's type is `HybridContainer`** (reading `dev/untyped.py` only):

1. [untyped.py:2374](../dev/untyped.py#L2374) assignment: `merged = left | right`

*Reading:* No source in this file shows the type; `HybridContainer` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `int`:** it differs from the author's `HybridContainer` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:2934](conversion-output.py.txt#L2934) · should be [typed.py:4296](../dev/typed.py#L4296) · input [untyped.py:2283](../dev/untyped.py#L2283)

```diff
@@ function_with_json_uuid_and_path_stress.payload · wrong · Top type (object) @@
-    payload: dict[str, str] = {'id': str(object=identifier), 'parts': path.stem.split(sep='-'), 'exists': path.exists()}
+    payload: dict[str, object] = {
```

**Why the author's type is `dict[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:2283](../dev/untyped.py#L2283) assignment: `payload = {'id': str(object=identifier), 'parts': path.stem.split(sep='-'), 'exists': path.exists()}`

*Reading:* No source in this file shows the type; `dict[str, object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `dict[str, str]`:** it is narrower than the author's `dict[str, object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:3014](conversion-output.py.txt#L3014) · should be [typed.py:4433](../dev/typed.py#L4433) · input [untyped.py:2355](../dev/untyped.py#L2355)

```diff
@@ function_with_metaclass_registry_stress.registry · wrong · Top type (object) @@
-    registry: None = RegistryMeta.registry
+    registry: dict[str, type[object]] = RegistryMeta.registry or {}
```

**Why the author's type is `dict[str, type[object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2355](../dev/untyped.py#L2355) assignment: `registry = RegistryMeta.registry`

*Reading:* No source in this file shows the type; `dict[str, type[object]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `None`:** it is narrower than the author's `dict[str, type[object]]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:3094](conversion-output.py.txt#L3094) · should be [typed.py:4640](../dev/typed.py#L4640) · input [untyped.py:2427](../dev/untyped.py#L2427)

```diff
@@ function_with_nested_default_factories.tree · wrong · Library class @@
-    tree: defaultdict[str, int] = defaultdict(lambda: defaultdict(list))
+    tree: defaultdict[str, defaultdict[str, list[int]]] = defaultdict(
```

**Why the author's type is `defaultdict[str, defaultdict[str, list[int]]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2427](../dev/untyped.py#L2427) assignment: `tree = defaultdict(lambda: defaultdict(list))`

*Reading:* No source in this file shows the type; `defaultdict[str, defaultdict[str, list[int]]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `defaultdict[str, int]`:** it differs from the author's `defaultdict[str, defaultdict[str, list[int]]]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:3133](conversion-output.py.txt#L3133) · should be [typed.py:4704](../dev/typed.py#L4704) · input [untyped.py:2461](../dev/untyped.py#L2461)

```diff
@@ function_with_partial_reduce_and_operator_stress.add_five · wrong · Callable @@
-    add_five: int = partial(operator.add, 5)
+    add_five: Callable[[int], int] = partial(add, 5)
```

**Why the author's type is `Callable[[int], int]`** (reading `dev/untyped.py` only):

1. [untyped.py:2461](../dev/untyped.py#L2461) assignment: `add_five = partial(operator.add, 5)`

*Reading:* No source in this file shows the type; `Callable[[int], int]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `int`:** it differs from the author's `Callable[[int], int]` (wrong); compare the sources above to see which of them it followed.

how it is [conversion-output.py.txt:3115](conversion-output.py.txt#L3115) · should be [typed.py:4669](../dev/typed.py#L4669) · input [untyped.py:2444](../dev/untyped.py#L2444)

```diff
@@ function_with_sort_key_and_grouping_stress.normalized · wrong · Top type (object) @@
-    normalized: list[dict[str, int | str]] = [{'name': row['name'].strip().lower(), 'score': int(row['score'])} for row in rows]
+    normalized: list[dict[str, object]] = [
```

**Why the author's type is `list[dict[str, object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2444](../dev/untyped.py#L2444) assignment: `normalized = [{'name': row['name'].strip().lower(), 'score': int(row['score'])} for row in rows]` → `list[?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `list[dict[str, object]]`; the author's choice adds knowledge from outside this file.

**Why astart wrote `list[dict[str, int | str]]`:** it is narrower than the author's `list[dict[str, object]]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:3293](conversion-output.py.txt#L3293) · should be [typed.py:4972](../dev/typed.py#L4972) · input [untyped.py:2594](../dev/untyped.py#L2594)

```diff
@@ test_extended_inference_edge_cases_part1.records · wrong · Top type (object) @@
-    records: list[dict[str, None | int | str]] = [{'name': ' Alpha ', 'amount': '10'}, {'name': 'beta', 'amount': 5}, {'name': None, 'amount': None}]
+    records: list[dict[str, object]] = [
```

**Why the author's type is `list[dict[str, object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2594](../dev/untyped.py#L2594) assignment: `records = [{'name': ' Alpha ', 'amount': '10'}, {'name': 'beta', 'amount': 5}, {'name': None, 'amou…` → `list[dict[str, str] | dict[str, str | int] | dict[str, None]]`

*Reading:* The sources show `list[dict[str, str] | dict[str, str | int] | dict[str, None]]`; the author widened to the top type (`list[dict[str, object]]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `list[dict[str, int | str | None]]`:** it is narrower than the author's `list[dict[str, object]]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:3325](conversion-output.py.txt#L3325) · should be [typed.py:5013](../dev/typed.py#L5013) · input [untyped.py:2630](../dev/untyped.py#L2630)

```diff
@@ test_extended_inference_edge_cases_part2.rows · wrong · Top type (object) @@
-    rows: list[dict[str, int | str]] = [{'name': ' Alpha', 'score': '10'}, {'name': 'alpha', 'score': 7}, {'name': 'Beta', 'score': 3}]
+    rows: list[dict[str, object]] = [
```

**Why the author's type is `list[dict[str, object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2630](../dev/untyped.py#L2630) assignment: `rows = [{'name': ' Alpha', 'score': '10'}, {'name': 'alpha', 'score': 7}, {'name': 'Beta', 'scor…` → `list[dict[str, str] | dict[str, str | int]]`

*Reading:* The sources show `list[dict[str, str] | dict[str, str | int]]`; the author widened to the top type (`list[dict[str, object]]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart wrote `list[dict[str, int | str]]`:** it is narrower than the author's `list[dict[str, object]]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:1718](conversion-output.py.txt#L1718) · should be [typed.py:2690](../dev/typed.py#L2690) · input [untyped.py:1353](../dev/untyped.py#L1353)

```diff
@@ test_function_calls_part1.result22 · wrong · Callable @@
-    result22: Callable[[None | int], int | str] = function_with_optional_types()
+    result22: Callable[[object], object] = function_with_optional_types()
```

**Why the author's type is `Callable[[object], object]`** (reading `dev/untyped.py` only):

1. [untyped.py:1353](../dev/untyped.py#L1353) assignment: `result22 = function_with_optional_types()`

*Reading:* No source in this file shows the type; `Callable[[object], object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `Callable[[None | int], int | str]`:** it is narrower than the author's `Callable[[object], object]`, which uses the top type `object`. astart never writes `object`, and the narrower type is valid for every caller in this file (scoring task G-02).

how it is [conversion-output.py.txt:1758](conversion-output.py.txt#L1758) · should be [typed.py:2741](../dev/typed.py#L2741) · input [untyped.py:1393](../dev/untyped.py#L1393)

```diff
@@ test_function_calls_part2.result34 · wrong · Callable @@
-    result34: tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[[], int], Callable[[], int], Callable[[], int]] = function_with_type_annotations_missing()
+    result34: tuple[
```

**Why the author's type is `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]`** (reading `dev/untyped.py` only):

1. [untyped.py:1393](../dev/untyped.py#L1393) assignment: `result34 = function_with_type_annotations_missing()`

*Reading:* No source in this file shows the type; `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart wrote `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[[], int], Callable[[], int], Callable[[], int]]`:** it differs from the author's `tuple[Callable[[int], int], Callable[[int, int], int], Callable[[int, int], int], Callable[Ellipsis, int], Callable[Ellipsis, int], Callable[Ellipsis, int]]` (wrong); compare the sources above to see which of them it followed.

## Gap by owner (most missing or wrong first)

| Owner | Gap |
| --- | ---: |
| `test_function_calls_part2` ([untyped.py:1380](../dev/untyped.py#L1380)) | 13 |
| `test_function_calls_part3` ([untyped.py:1431](../dev/untyped.py#L1431)) | 12 |
| `test_function_calls_part1` ([untyped.py:1325](../dev/untyped.py#L1325)) | 11 |
| `MetaClass.__new__` ([untyped.py:101](../dev/untyped.py#L101)) | 6 |
| `RegistryMeta.__new__` ([untyped.py:1881](../dev/untyped.py#L1881)) | 6 |
| `function_with_recursive_containers` ([untyped.py:2154](../dev/untyped.py#L2154)) | 6 |
| `function_with_contextvars_and_chainmap` ([untyped.py:2294](../dev/untyped.py#L2294)) | 6 |
| `function_with_dict_operations` ([untyped.py:675](../dev/untyped.py#L675)) | 5 |
| `test_other_operations` ([untyped.py:1502](../dev/untyped.py#L1502)) | 5 |
| `preserve_signature_decorator.wrapper` ([untyped.py:2053](../dev/untyped.py#L2053)) | 5 |
| `function_with_exception_group_stress` ([untyped.py:2240](../dev/untyped.py#L2240)) | 5 |
| `Constants` | 5 |
| `SliceExampleResult` | 5 |
| `ScopeResolutionResult` | 5 |
| `MetaClass.__call__` ([untyped.py:106](../dev/untyped.py#L106)) | 4 |

## Missing annotations by family, with code

### Top type (object): 105 missing

Tasks: policy: astart never writes object; [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong) scores narrower

how it is [conversion-output.py.txt:114](conversion-output.py.txt#L114) · should be [typed.py:223](../dev/typed.py#L223) · input [untyped.py:101](../dev/untyped.py#L101)

```diff
@@ MetaClass.__new__.bases · missing · Top type (object) @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        bases: tuple[type[object], ...],
```

**Why the author's type is `tuple[type[object], Ellipsis]`** (reading `dev/untyped.py` only):

1. [untyped.py:104](../dev/untyped.py#L104) call site passes: `super().__new__(mcs, name, bases, namespace)  ->  name` *(matched by name only)*
2. [untyped.py:991](../dev/untyped.py#L991) same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` *(matched by name only)*
3. [untyped.py:1881](../dev/untyped.py#L1881) same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` *(matched by name only)*
4. [untyped.py:1884](../dev/untyped.py#L1884) call site passes: `super().__new__(mcls, name, bases, namespace)  ->  name` *(matched by name only)*

*Reading:* No source in this file shows the type; `tuple[type[object], Ellipsis]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:114](conversion-output.py.txt#L114) · should be [typed.py:224](../dev/typed.py#L224) · input [untyped.py:101](../dev/untyped.py#L101)

```diff
@@ MetaClass.__new__.namespace · missing · Top type (object) @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        namespace: dict[str, object],
```

**Why the author's type is `dict[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:103](../dev/untyped.py#L103) body indexes it: `namespace['meta_added']`
2. [untyped.py:104](../dev/untyped.py#L104) call site passes: `super().__new__(mcs, name, bases, namespace)  ->  bases` *(matched by name only)*
3. [untyped.py:991](../dev/untyped.py#L991) same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` *(matched by name only)*
4. [untyped.py:1881](../dev/untyped.py#L1881) same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` *(matched by name only)*
5. [untyped.py:1884](../dev/untyped.py#L1884) call site passes: `super().__new__(mcls, name, bases, namespace)  ->  bases` *(matched by name only)*

*Reading:* No source in this file shows the type; `dict[str, object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:114](conversion-output.py.txt#L114) · should be [typed.py:225](../dev/typed.py#L225) · input [untyped.py:101](../dev/untyped.py#L101)

```diff
@@ MetaClass.__new__._kwargs · missing · Top type (object) @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        **_kwargs: object,
```

**Why the author's type is `object`** (reading `dev/untyped.py` only):

1. [untyped.py:991](../dev/untyped.py#L991) same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` *(matched by name only)*
2. [untyped.py:1881](../dev/untyped.py#L1881) same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` *(matched by name only)*

*Reading:* No source in this file shows the type; `object` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:127](conversion-output.py.txt#L127) · should be [typed.py:248](../dev/typed.py#L248) · input [untyped.py:106](../dev/untyped.py#L106)

```diff
@@ MetaClass.__call__-> · missing · Top type (object) @@
-    def __call__(cls, *args, **kwargs):
+    ) -> object:
```

**Why the author's type is `object`** (reading `dev/untyped.py` only):

1. [untyped.py:111](../dev/untyped.py#L111) return: `initialized`

*Reading:* No source in this file shows the type; `object` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:127](conversion-output.py.txt#L127) · should be [typed.py:246](../dev/typed.py#L246) · input [untyped.py:106](../dev/untyped.py#L106)

```diff
@@ MetaClass.__call__.args · missing · Top type (object) @@
-    def __call__(cls, *args, **kwargs):
+        *args: object,
```

**Why the author's type is `object`** (reading `dev/untyped.py` only):

1. [untyped.py:1891](../dev/untyped.py#L1891) same-named method in RegistryMeta: `RegistryMeta.__call__(cls, *args, **_kwargs)` *(matched by name only)*
2. [untyped.py:1997](../dev/untyped.py#L1997) same-named method in CallableObject: `CallableObject.__call__(self, value, *, scale=1)` *(matched by name only)*

*Reading:* No source in this file shows the type; `object` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 105 (first 30, with links to the author's line)</summary>

- `MetaClass.__new__.bases` ([typed.py:223](../dev/typed.py#L223)): `tuple[type[object], Ellipsis]`
- `MetaClass.__new__.namespace` ([typed.py:224](../dev/typed.py#L224)): `dict[str, object]`
- `MetaClass.__new__._kwargs` ([typed.py:225](../dev/typed.py#L225)): `object`
- `MetaClass.__call__->` ([typed.py:248](../dev/typed.py#L248)): `object`
- `MetaClass.__call__.args` ([typed.py:246](../dev/typed.py#L246)): `object`
- `MetaClass.__call__.kwargs` ([typed.py:247](../dev/typed.py#L247)): `object`
- `decorator_with_class.Wrapper.__init__.args` ([typed.py:500](../dev/typed.py#L500)): `object`
- `decorator_with_class.Wrapper.__init__._kwargs` ([typed.py:500](../dev/typed.py#L500)): `object`
- `decorator_with_class.Wrapper.__getattr__->` ([typed.py:510](../dev/typed.py#L510)): `object`
- `function_with_class_methods->` ([typed.py:930](../dev/typed.py#L930)): `type[object]`
- `function_with_property->` ([typed.py:973](../dev/typed.py#L973)): `type[object]`
- `function_with_descriptor->` ([typed.py:1016](../dev/typed.py#L1016)): `type[object]`
- `function_with_descriptor.Descriptor.__get__.obj` ([typed.py:1031](../dev/typed.py#L1031)): `object`
- `function_with_descriptor.Descriptor.__get__.objtype` ([typed.py:1031](../dev/typed.py#L1031)): `type[object]`
- `function_with_descriptor.Descriptor.__set__.obj` ([typed.py:1045](../dev/typed.py#L1045)): `object`
- `function_with_descriptor.Descriptor.__delete__.obj` ([typed.py:1056](../dev/typed.py#L1056)): `object`
- `function_with_operator_overloading.Vector.__eq__.other` ([typed.py:1127](../dev/typed.py#L1127)): `object`
- `function_with_metaclass_usage->` ([typed.py:1174](../dev/typed.py#L1174)): `object`
- `function_with_multiple_inheritance->` ([typed.py:1188](../dev/typed.py#L1188)): `type[object]`
- `function_with_protocol->` ([typed.py:1269](../dev/typed.py#L1269)): `type[object]`
- `function_with_callable.callable_function->` ([typed.py:1389](../dev/typed.py#L1389)): `object`
- `function_with_callable.callable_function.arg` ([typed.py:1388](../dev/typed.py#L1388)): `object`
- `function_with_matrix_multiplication->` ([typed.py:1615](../dev/typed.py#L1615)): `type[object]`
- `function_with_weak_refs->` ([typed.py:1898](../dev/typed.py#L1898)): `ReferenceType[object]`
- `function_with_slots->` ([typed.py:1913](../dev/typed.py#L1913)): `type[object]`
- `function_with_class_decorator->` ([typed.py:1945](../dev/typed.py#L1945)): `type[object]`
- `function_with_singleton->` ([typed.py:1988](../dev/typed.py#L1988)): `type[object]`
- `function_with_factory->` ([typed.py:2020](../dev/typed.py#L2020)): `type[object]`
- `function_with_builder->` ([typed.py:2057](../dev/typed.py#L2057)): `type[object]`
- `function_with_observer->` ([typed.py:2109](../dev/typed.py#L2109)): `tuple[type[object], type[object]]`

</details>

### Scalar: 53 missing

Tasks: [W-06](TODO.md#w-06--burn-down-unprovable-calls-in-the-negotiator), [W-08](TODO.md#w-08--let-the-negotiator-write-default-literal-parameters-f-37), [I-10](TODO.md#i-10--numeric-tower-and-operator-result-rules), [F-37](TODO.md#f-37--default-literal-parameters-in-the-negotiator)

how it is [conversion-output.py.txt:57](conversion-output.py.txt#L57) · should be [typed.py:125](../dev/typed.py#L125) · input [untyped.py:57](../dev/untyped.py#L57)

```diff
@@ SupportsUpdate.update.message · missing · Scalar @@
-    def update(self, message) -> None:
+    def update(self, message: str) -> None:
```

**Why the author's type is `str`** (reading `dev/untyped.py` only):

1. [untyped.py:1056](../dev/untyped.py#L1056) same-named method in Observer: `function_with_observer.Observer.update(self, message)` *(matched by name only)*
2. [untyped.py:1560](../dev/untyped.py#L1560) same-named method in BuiltinMethodDict: `BuiltinMethodDict.update(self, other=(), *values, **kwargs)` *(matched by name only)*
3. [untyped.py:1674](../dev/untyped.py#L1674) call site passes: `custom_dict.update({'b': 2}, 3)  ->  {'b': 2}` *(matched by name only)*
4. [untyped.py:1675](../dev/untyped.py#L1675) call site passes: `builtin_dict.update({'b': 2})  ->  {'b': 2}` *(matched by name only)*

*Reading:* No source in this file shows the type; `str` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:68](conversion-output.py.txt#L68) · should be [typed.py:138](../dev/typed.py#L138) · input [untyped.py:64](../dev/untyped.py#L64)

```diff
@@ SupportsExecuteInt.execute.a · missing · Scalar @@
-    def execute(self, a, b) -> None:
+    def execute(self, a: int, b: int) -> int:
```

**Why the author's type is `int`** (reading `dev/untyped.py` only):

1. [untyped.py:1085](../dev/untyped.py#L1085) same-named method in Strategy: `function_with_strategy.Strategy.execute(self, a, b)` *(matched by name only)*
2. [untyped.py:1093](../dev/untyped.py#L1093) same-named method in AddStrategy: `function_with_strategy.AddStrategy.execute(self, a, b)` *(matched by name only)*
3. [untyped.py:1100](../dev/untyped.py#L1100) same-named method in MultiplyStrategy: `function_with_strategy.MultiplyStrategy.execute(self, a, b)` *(matched by name only)*

*Reading:* No source in this file shows the type; `int` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:68](conversion-output.py.txt#L68) · should be [typed.py:138](../dev/typed.py#L138) · input [untyped.py:64](../dev/untyped.py#L64)

```diff
@@ SupportsExecuteInt.execute.b · missing · Scalar @@
-    def execute(self, a, b) -> None:
+    def execute(self, a: int, b: int) -> int:
```

**Why the author's type is `int`** (reading `dev/untyped.py` only):

1. [untyped.py:1085](../dev/untyped.py#L1085) same-named method in Strategy: `function_with_strategy.Strategy.execute(self, a, b)` *(matched by name only)*
2. [untyped.py:1093](../dev/untyped.py#L1093) same-named method in AddStrategy: `function_with_strategy.AddStrategy.execute(self, a, b)` *(matched by name only)*
3. [untyped.py:1100](../dev/untyped.py#L1100) same-named method in MultiplyStrategy: `function_with_strategy.MultiplyStrategy.execute(self, a, b)` *(matched by name only)*

*Reading:* No source in this file shows the type; `int` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:190](conversion-output.py.txt#L190) · should be [typed.py:331](../dev/typed.py#L331) · input [untyped.py:150](../dev/untyped.py#L150)

```diff
@@ BaseClass.base_property.value · missing · Scalar @@
-    def base_property(self, value) -> None:
+    def base_property(self, value: int) -> None:
```

**Why the author's type is `int`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:248](conversion-output.py.txt#L248) · should be [typed.py:399](../dev/typed.py#L399) · input [untyped.py:187](../dev/untyped.py#L187)

```diff
@@ MetaDecoratedClass.__init__.value · missing · Scalar @@
-    def __init__(self, value) -> None:
+    def __init__(self, value: int) -> None:
```

**Why the author's type is `int`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:223](../dev/untyped.py#L223) same-named method in Wrapper: `decorator_with_class.Wrapper.__init__(self, *args, **kwargs)` *(matched by name only)*
4. [untyped.py:1496](../dev/untyped.py#L1496) call site passes: `MetaDecoratedClass(value=100)  ->  100` → `int`

*Reading:* Joining what the 1 typed source(s) show (`int`) gives exactly the author's `int`.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 53 (first 30, with links to the author's line)</summary>

- `SupportsUpdate.update.message` ([typed.py:125](../dev/typed.py#L125)): `str`
- `SupportsExecuteInt.execute.a` ([typed.py:138](../dev/typed.py#L138)): `int`
- `SupportsExecuteInt.execute.b` ([typed.py:138](../dev/typed.py#L138)): `int`
- `BaseClass.base_property.value` ([typed.py:331](../dev/typed.py#L331)): `int`
- `MetaDecoratedClass.__init__.value` ([typed.py:399](../dev/typed.py#L399)): `int`
- `function_with_property.PropertyClass.value.val` ([typed.py:999](../dev/typed.py#L999)): `int`
- `function_with_slots.SlottedClass.__init__.x` ([typed.py:1931](../dev/typed.py#L1931)): `int`
- `function_with_slots.SlottedClass.__init__.y` ([typed.py:1931](../dev/typed.py#L1931)): `int`
- `function_with_factory.Factory.create.type_name` ([typed.py:2038](../dev/typed.py#L2038)): `str`
- `function_with_builder.Builder.add_part.part` ([typed.py:2084](../dev/typed.py#L2084)): `str`
- `function_with_observer.Observer.update.message` ([typed.py:2120](../dev/typed.py#L2120)): `str`
- `function_with_observer.Subject.notify.message` ([typed.py:2145](../dev/typed.py#L2145)): `str`
- `function_with_chain_of_responsibility.Handler.handle.request` ([typed.py:2291](../dev/typed.py#L2291)): `str`
- `AsyncResource.__init__.name` ([typed.py:3727](../dev/typed.py#L3727)): `str`
- `AsyncResource.__aexit__->` ([typed.py:3752](../dev/typed.py#L3752)): `bool`
- `AsyncResource.fetch.value` ([typed.py:3768](../dev/typed.py#L3768)): `int`
- `extended_sync_context.seed` ([typed.py:3783](../dev/typed.py#L3783)): `int`
- `_->` ([typed.py:3952](../dev/typed.py#L3952)): `str`
- `LocalMultiplierProtocol.apply->` ([typed.py:4533](../dev/typed.py#L4533)): `int`
- `LocalMultiplierProtocol.apply.value` ([typed.py:4533](../dev/typed.py#L4533)): `int`
- `LocalMultiplierFactory.__call__.offset` ([typed.py:4549](../dev/typed.py#L4549)): `int`
- `function_with_deep_attribute_assignment.Node.__init__.name` ([typed.py:4748](../dev/typed.py#L4748)): `str`
- `SupportsInitializedByMeta.initialized_by_meta` ([typed.py:173](../dev/typed.py#L173)): `bool`
- `SupportsVector.x` ([typed.py:198](../dev/typed.py#L198)): `int`
- `SupportsVector.y` ([typed.py:199](../dev/typed.py#L199)): `int`
- `DataClassExample.x` ([typed.py:588](../dev/typed.py#L588)): `int`
- `DataClassExample.y` ([typed.py:589](../dev/typed.py#L589)): `str`
- `function_with_chained_comparisons.x` ([typed.py:1516](../dev/typed.py#L1516)): `int`
- `function_with_custom_exceptions.raise_custom.msg` ([typed.py:1892](../dev/typed.py#L1892)): `str`
- `function_with_class_decorator.add_method.method_name` ([typed.py:1977](../dev/typed.py#L1977)): `str`

</details>

### Builtin container: 36 missing

Tasks: [I-05](TODO.md#i-05--type-for-targets-from-common-iterables), [I-09](TODO.md#i-09--defaultdict-counter-deque-element-types-from-mutation), [I-17](TODO.md#i-17--tuple-star-unpack-slice-and-operator-results-on-containers), [F-40](TODO.md#f-40--comprehensions-as-derived-nodes), [AL-07](TODO.md#al-07--bidirectional-expected-type-inference)

how it is [conversion-output.py.txt:566](conversion-output.py.txt#L566) · should be [typed.py:886](../dev/typed.py#L886) · input [untyped.py:403](../dev/untyped.py#L403)

```diff
@@ function_with_generators-> · missing · Builtin container @@
-def function_with_generators():
+def function_with_generators() -> list[int]:
```

**Why the author's type is `list[int]`** (reading `dev/untyped.py` only):

1. [untyped.py:403](../dev/untyped.py#L403) generator: `the body contains 'yield'`
2. [untyped.py:410](../dev/untyped.py#L410) return: `list(generator())` → `list[?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `list[int]`; the author's choice adds knowledge from outside this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1567](conversion-output.py.txt#L1567) · should be [typed.py:2419](../dev/typed.py#L2419) · input [untyped.py:1207](../dev/untyped.py#L1207)

```diff
@@ function_with_groupby-> · missing · Builtin container @@
-def function_with_groupby():
+def function_with_groupby() -> dict[str, list[int]]:
```

**Why the author's type is `dict[str, list[int]]`** (reading `dev/untyped.py` only):

1. [untyped.py:1210](../dev/untyped.py#L1210) return: `{k: [v for _, v in g] for k, g in groupby(iterable=sorted(data), key=lambda x: x[0])}` → `dict[?, ?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `dict[str, list[int]]`; the author's choice adds knowledge from outside this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1666](conversion-output.py.txt#L1666) · should be [typed.py:2603](../dev/typed.py#L2603) · input [untyped.py:1301](../dev/untyped.py#L1301)

```diff
@@ function_with_compress-> · missing · Builtin container @@
-def function_with_compress():
+def function_with_compress() -> list[int]:
```

**Why the author's type is `list[int]`** (reading `dev/untyped.py` only):

1. [untyped.py:1305](../dev/untyped.py#L1305) return: `list(compress(data=data, selectors=selectors))` → `list[?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `list[int]`; the author's choice adds knowledge from outside this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1673](conversion-output.py.txt#L1673) · should be [typed.py:2615](../dev/typed.py#L2615) · input [untyped.py:1308](../dev/untyped.py#L1308)

```diff
@@ function_with_accumulate-> · missing · Builtin container @@
-def function_with_accumulate():
+def function_with_accumulate() -> list[int]:
```

**Why the author's type is `list[int]`** (reading `dev/untyped.py` only):

1. [untyped.py:1311](../dev/untyped.py#L1311) return: `list(accumulate(iterable=data))` → `list[?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `list[int]`; the author's choice adds knowledge from outside this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2158](conversion-output.py.txt#L2158) · should be [typed.py:3185](../dev/typed.py#L3185) · input [untyped.py:1725](../dev/untyped.py#L1725)

```diff
@@ function_with_scope_resolution.duplicate_scope_name.deepest-> · missing · Builtin container @@
-        def deepest():
+        def deepest() -> list[int]:
```

**Why the author's type is `list[int]`** (reading `dev/untyped.py` only):

1. [untyped.py:1727](../dev/untyped.py#L1727) return: `duplicated_name`

*Reading:* No source in this file shows the type; `list[int]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 36 (first 30, with links to the author's line)</summary>

- `function_with_generators->` ([typed.py:886](../dev/typed.py#L886)): `list[int]`
- `function_with_groupby->` ([typed.py:2419](../dev/typed.py#L2419)): `dict[str, list[int]]`
- `function_with_compress->` ([typed.py:2603](../dev/typed.py#L2603)): `list[int]`
- `function_with_accumulate->` ([typed.py:2615](../dev/typed.py#L2615)): `list[int]`
- `function_with_scope_resolution.duplicate_scope_name.deepest->` ([typed.py:3185](../dev/typed.py#L3185)): `list[int]`
- `function_with_numeric_tower->` ([typed.py:4151](../dev/typed.py#L4151)): `tuple[int, float, float, list[int]]`
- `function_with_iterable_unpacking_stress->` ([typed.py:4335](../dev/typed.py#L4335)): `tuple[int, list[int], int, list[tuple[int, int]], list[tuple[int, int]]]`
- `function_with_map_filter_zip_stress->` ([typed.py:4803](../dev/typed.py#L4803)): `list[tuple[int, int]]`
- `function_with_composed_inner_functions->` ([typed.py:4819](../dev/typed.py#L4819)): `dict[str, int]`
- `function_with_composed_inner_functions.tokenize->` ([typed.py:4846](../dev/typed.py#L4846)): `list[str]`
- `function_with_composed_inner_functions.score->` ([typed.py:4862](../dev/typed.py#L4862)): `dict[str, int]`
- `DataClassExample.z` ([typed.py:590](../dev/typed.py#L590)): `list[int]`
- `function_with_comprehensions.filtered` ([typed.py:772](../dev/typed.py#L772)): `dict[int, int]`
- `test_function_calls_part1.result13` ([typed.py:2681](../dev/typed.py#L2681)): `list[int]`
- `test_function_calls_part3.result49` ([typed.py:2797](../dev/typed.py#L2797)): `dict[str, list[int]]`
- `test_function_calls_part3.result61` ([typed.py:2811](../dev/typed.py#L2811)): `list[int]`
- `test_function_calls_part3.result62` ([typed.py:2812](../dev/typed.py#L2812)): `list[int]`
- `SliceExampleResult.list_slice` ([typed.py:2922](../dev/typed.py#L2922)): `list[int]`
- `SliceExampleResult.list_stride_slice` ([typed.py:2923](../dev/typed.py#L2923)): `list[int]`
- `SliceExampleResult.dict_slice` ([typed.py:2924](../dev/typed.py#L2924)): `dict[str, int]`
- `SliceExampleResult.dict_key_slice` ([typed.py:2925](../dev/typed.py#L2925)): `list[str]`
- `SliceExampleResult.dict_value_slice` ([typed.py:2926](../dev/typed.py#L2926)): `list[int]`
- `RedefinitionResult.third_type_value` ([typed.py:3024](../dev/typed.py#L3024)): `list[int]`
- `RedefinitionResult.union_final_value` ([typed.py:3025](../dev/typed.py#L3025)): `dict[str, int]`
- `ScopeResolutionResult.inner_value` ([typed.py:3042](../dev/typed.py#L3042)): `list[int]`
- `extended_sync_context.events` ([typed.py:3793](../dev/typed.py#L3793)): `list[str]`
- `cached_recursive_pair.left` ([typed.py:3978](../dev/typed.py#L3978)): `tuple[int, int]`
- `cached_recursive_pair.right` ([typed.py:3979](../dev/typed.py#L3979)): `tuple[int, int]`
- `function_with_walrus_and_narrowing.matched` ([typed.py:4106](../dev/typed.py#L4106)): `list[str]`
- `function_with_recursive_containers.values` ([typed.py:4144](../dev/typed.py#L4144)): `list[int]`

</details>

### Type alias: 14 missing

Tasks: [S-03](TODO.md#s-03--use-type-x---for-type-aliases), [AL-14](TODO.md#al-14--finite-domain-values-to-literal-and-enum-suggestions) (author-defined names)

how it is [conversion-output.py.txt:687](conversion-output.py.txt#L687) · should be [typed.py:1069](../dev/typed.py#L1069) · input [untyped.py:502](../dev/untyped.py#L502)

```diff
@@ function_with_operator_overloading-> · missing · Type alias @@
-def function_with_operator_overloading():
+def function_with_operator_overloading() -> VectorFactory:
```

**Why the author's type is `VectorFactory`** (reading `dev/untyped.py` only):

1. [untyped.py:543](../dev/untyped.py#L543) return: `Vector`

*Reading:* No source in this file shows the type; `VectorFactory` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:915](conversion-output.py.txt#L915) · should be [typed.py:1418](../dev/typed.py#L1418) · input [untyped.py:675](../dev/untyped.py#L675)

```diff
@@ function_with_dict_operations-> · missing · Type alias @@
-def function_with_dict_operations():
+def function_with_dict_operations() -> tuple[IntDict, IntDict]:
```

**Why the author's type is `tuple[IntDict, IntDict]`** (reading `dev/untyped.py` only):

1. [untyped.py:681](../dev/untyped.py#L681) return: `(merged, filtered)`

*Reading:* No source in this file shows the type; `tuple[IntDict, IntDict]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1695](conversion-output.py.txt#L1695) · should be [typed.py:2649](../dev/typed.py#L2649) · input [untyped.py:1325](../dev/untyped.py#L1325)

```diff
@@ test_function_calls_part1-> · missing · Type alias @@
-def test_function_calls_part1():
+def test_function_calls_part1() -> TestResult:
```

**Why the author's type is `TestResult`** (reading `dev/untyped.py` only):

1. [untyped.py:1354](../dev/untyped.py#L1354) return: `{'result1': result1, 'result2': result2, 'result3': result3, 'result4': result4, 'result5…`

*Reading:* No source in this file shows the type; `TestResult` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1745](conversion-output.py.txt#L1745) · should be [typed.py:2717](../dev/typed.py#L2717) · input [untyped.py:1380](../dev/untyped.py#L1380)

```diff
@@ test_function_calls_part2-> · missing · Type alias @@
-def test_function_calls_part2():
+def test_function_calls_part2() -> TestResult:
```

**Why the author's type is `TestResult`** (reading `dev/untyped.py` only):

1. [untyped.py:1405](../dev/untyped.py#L1405) return: `{'result23': result23, 'result24': result24, 'result25': result25, 'result26': result26, …`

*Reading:* No source in this file shows the type; `TestResult` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1796](conversion-output.py.txt#L1796) · should be [typed.py:2786](../dev/typed.py#L2786) · input [untyped.py:1431](../dev/untyped.py#L1431)

```diff
@@ test_function_calls_part3-> · missing · Type alias @@
-def test_function_calls_part3():
+def test_function_calls_part3() -> TestResult:
```

**Why the author's type is `TestResult`** (reading `dev/untyped.py` only):

1. [untyped.py:1455](../dev/untyped.py#L1455) return: `{'result45': result45, 'result46': result46, 'result47': result47, 'result48': result48, …`

*Reading:* No source in this file shows the type; `TestResult` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 14 (first 30, with links to the author's line)</summary>

- `function_with_operator_overloading->` ([typed.py:1069](../dev/typed.py#L1069)): `VectorFactory`
- `function_with_dict_operations->` ([typed.py:1418](../dev/typed.py#L1418)): `tuple[IntDict, IntDict]`
- `test_function_calls_part1->` ([typed.py:2649](../dev/typed.py#L2649)): `TestResult`
- `test_function_calls_part2->` ([typed.py:2717](../dev/typed.py#L2717)): `TestResult`
- `test_function_calls_part3->` ([typed.py:2786](../dev/typed.py#L2786)): `TestResult`
- `test_function_calls->` ([typed.py:2855](../dev/typed.py#L2855)): `TestResult`
- `function_with_pattern_matching_stress->` ([typed.py:3985](../dev/typed.py#L3985)): `PatternStressResult`
- `function_with_extended_named_results->` ([typed.py:4946](../dev/typed.py#L4946)): `ExtendedResultTuple`
- `test_extended_inference_edge_cases_part1->` ([typed.py:4965](../dev/typed.py#L4965)): `ExtendedTestResult`
- `test_extended_inference_edge_cases_part2->` ([typed.py:5006](../dev/typed.py#L5006)): `ExtendedTestResult`
- `function_with_dict_operations.filtered` ([typed.py:1428](../dev/typed.py#L1428)): `IntDict`
- `test_function_calls_part1.result16` ([typed.py:2684](../dev/typed.py#L2684)): `VectorFactory`
- `test_function_calls_part2.result24` ([typed.py:2725](../dev/typed.py#L2725)): `tuple[IntDict, IntDict]`
- `test_other_operations.vector` ([typed.py:2898](../dev/typed.py#L2898)): `VectorFactory`

</details>

### Module class: 24 missing

Tasks: [M2-02](TODO.md#m2-02--constructorattribute-resolution), [W-12](TODO.md#w-12--annotate-instance-attributes-from-negotiation), [I-11](TODO.md#i-11--attribute-chains-and-dataclassnamedtupletypeddict-fields), [W-14](TODO.md#w-14--annotate-class-level-and-module-level-variables)

how it is [conversion-output.py.txt:114](conversion-output.py.txt#L114) · should be [typed.py:226](../dev/typed.py#L226) · input [untyped.py:101](../dev/untyped.py#L101)

```diff
@@ MetaClass.__new__-> · missing · Module class @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+    ) -> MetaClass:
```

**Why the author's type is `MetaClass`** (reading `dev/untyped.py` only):

1. [untyped.py:104](../dev/untyped.py#L104) return: `super().__new__(mcs, name, bases, namespace)`

*Reading:* No source in this file shows the type; `MetaClass` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:114](conversion-output.py.txt#L114) · should be [typed.py:221](../dev/typed.py#L221) · input [untyped.py:101](../dev/untyped.py#L101)

```diff
@@ MetaClass.__new__.mcs · missing · Module class @@
-    def __new__(mcs, name: str, bases, namespace, **_kwargs):
+        mcs: type[MetaClass],
```

**Why the author's type is `type[MetaClass]`** (reading `dev/untyped.py` only):

1. [untyped.py:991](../dev/untyped.py#L991) same-named method in Singleton: `function_with_singleton.Singleton.__new__(cls)` *(matched by name only)*
2. [untyped.py:1881](../dev/untyped.py#L1881) same-named method in RegistryMeta: `RegistryMeta.__new__(mcls, name, bases, namespace, **_kwargs)` *(matched by name only)*

*Reading:* No source in this file shows the type; `type[MetaClass]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1373](conversion-output.py.txt#L1373) · should be [typed.py:2136](../dev/typed.py#L2136) · input [untyped.py:1067](../dev/untyped.py#L1067)

```diff
@@ function_with_observer.Subject.attach.observer · missing · Module class @@
-        def attach(self, observer) -> None:
+        def attach(self, observer: SupportsUpdate) -> None:
```

**Why the author's type is `SupportsUpdate`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1455](conversion-output.py.txt#L1455) · should be [typed.py:2247](../dev/typed.py#L2247) · input [untyped.py:1126](../dev/untyped.py#L1126)

```diff
@@ function_with_command.ConcreteCommand.__init__.receiver · missing · Module class @@
-        def __init__(self, receiver) -> None:
+        def __init__(self, receiver: SupportsAction) -> None:
```

**Why the author's type is `SupportsAction`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*

*Reading:* No source in this file shows the type; `SupportsAction` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1474](conversion-output.py.txt#L1474) · should be [typed.py:2278](../dev/typed.py#L2278) · input [untyped.py:1145](../dev/untyped.py#L1145)

```diff
@@ function_with_chain_of_responsibility.Handler.set_next-> · missing · Module class @@
-        def set_next(self, handler):
+        def set_next(self, handler: Handler) -> Handler:
```

**Why the author's type is `Handler`** (reading `dev/untyped.py` only):

1. [untyped.py:1148](../dev/untyped.py#L1148) return: `handler`

*Reading:* No source in this file shows the type; `Handler` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 24 (first 30, with links to the author's line)</summary>

- `MetaClass.__new__->` ([typed.py:226](../dev/typed.py#L226)): `MetaClass`
- `MetaClass.__new__.mcs` ([typed.py:221](../dev/typed.py#L221)): `type[MetaClass]`
- `function_with_observer.Subject.attach.observer` ([typed.py:2136](../dev/typed.py#L2136)): `SupportsUpdate`
- `function_with_command.ConcreteCommand.__init__.receiver` ([typed.py:2247](../dev/typed.py#L2247)): `SupportsAction`
- `function_with_chain_of_responsibility.Handler.set_next->` ([typed.py:2278](../dev/typed.py#L2278)): `Handler`
- `function_with_chain_of_responsibility.Handler.set_next.handler` ([typed.py:2278](../dev/typed.py#L2278)): `Handler`
- `function_with_namedtuple->` ([typed.py:2497](../dev/typed.py#L2497)): `Point`
- `RegistryMeta.__new__->` ([typed.py:3470](../dev/typed.py#L3470)): `RegistryMeta`
- `RegistryMeta.__new__.mcls` ([typed.py:3465](../dev/typed.py#L3465)): `type[RegistryMeta]`
- `LocalMultiplierFactory.__call__->` ([typed.py:4549](../dev/typed.py#L4549)): `LocalMultiplierProtocol`
- `LocalMultiplierFactory.from_values->` ([typed.py:4564](../dev/typed.py#L4564)): `LocalMultiplierProtocol`
- `function_with_local_class_closure_stress->` ([typed.py:4579](../dev/typed.py#L4579)): `LocalMultiplierFactory`
- `function_with_deep_attribute_assignment.Node.add->` ([typed.py:4760](../dev/typed.py#L4760)): `Node`
- `function_with_deep_attribute_assignment.Node.add.child` ([typed.py:4760](../dev/typed.py#L4760)): `Node`
- `MetaClass.__new__.created` ([typed.py:241](../dev/typed.py#L241)): `MetaClass`
- `MetaClass.__call__.instance` ([typed.py:259](../dev/typed.py#L259)): `SupportsInitializedByMeta`
- `test_function_calls_part1.result19` ([typed.py:2687](../dev/typed.py#L2687)): `type[AbstractBase]`
- `test_other_operations.vec` ([typed.py:2899](../dev/typed.py#L2899)): `SupportsVector`
- `test_other_operations.vec2` ([typed.py:2900](../dev/typed.py#L2900)): `SupportsVector`
- `test_other_operations.vec_sum` ([typed.py:2901](../dev/typed.py#L2901)): `SupportsVector`
- `RegistryMeta.__new__.cls` ([typed.py:3485](../dev/typed.py#L3485)): `RegistryMeta`
- `function_with_metaclass_registry_stress.clone` ([typed.py:4429](../dev/typed.py#L4429)): `RegistryItem`
- `test_extended_inference_edge_cases_part3.local_multiplier` ([typed.py:5047](../dev/typed.py#L5047)): `LocalMultiplierFactory`
- `test_extended_inference_edge_cases_part3.local_instance` ([typed.py:5050](../dev/typed.py#L5050)): `LocalMultiplierProtocol`

</details>

### Callable: 19 missing

Tasks: [M4-17](TODO.md#m4-17--callable-r-params), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding)

how it is [conversion-output.py.txt:257](conversion-output.py.txt#L257) · should be [typed.py:409](../dev/typed.py#L409) · input [untyped.py:192](../dev/untyped.py#L192)

```diff
@@ decorator-> · missing · Callable @@
-def decorator(func):
+def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
```

**Why the author's type is `Callable[P, R]`** (reading `dev/untyped.py` only):

1. [untyped.py:198](../dev/untyped.py#L198) return: `result * 2`
2. [untyped.py:200](../dev/untyped.py#L200) return: `wrapper`

*Reading:* No source in this file shows the type; `Callable[P, R]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:257](conversion-output.py.txt#L257) · should be [typed.py:409](../dev/typed.py#L409) · input [untyped.py:192](../dev/untyped.py#L192)

```diff
@@ decorator.func · missing · Callable @@
-def decorator(func):
+def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
```

**Why the author's type is `Callable[P, R]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:272](conversion-output.py.txt#L272) · should be [typed.py:442](../dev/typed.py#L442) · input [untyped.py:203](../dev/untyped.py#L203)

```diff
@@ decorator_with_args-> · missing · Callable @@
-def decorator_with_args(multiplier: int = 2):
+) -> Callable[[Callable[P, R]], Callable[P, R]]:
```

**Why the author's type is `Callable[[Callable[P, R]], Callable[P, R]]`** (reading `dev/untyped.py` only):

1. [untyped.py:212](../dev/untyped.py#L212) return: `wrapper`
2. [untyped.py:214](../dev/untyped.py#L214) return: `actual_decorator`

*Reading:* No source in this file shows the type; `Callable[[Callable[P, R]], Callable[P, R]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:279](conversion-output.py.txt#L279) · should be [typed.py:453](../dev/typed.py#L453) · input [untyped.py:206](../dev/untyped.py#L206)

```diff
@@ decorator_with_args.actual_decorator-> · missing · Callable @@
-    def actual_decorator(func):
+    def actual_decorator(func: Callable[P, R]) -> Callable[P, R]:
```

**Why the author's type is `Callable[P, R]`** (reading `dev/untyped.py` only):

1. [untyped.py:210](../dev/untyped.py#L210) return: `result * multiplier`
2. [untyped.py:212](../dev/untyped.py#L212) return: `wrapper`

*Reading:* No source in this file shows the type; `Callable[P, R]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:279](conversion-output.py.txt#L279) · should be [typed.py:453](../dev/typed.py#L453) · input [untyped.py:206](../dev/untyped.py#L206)

```diff
@@ decorator_with_args.actual_decorator.func · missing · Callable @@
-    def actual_decorator(func):
+    def actual_decorator(func: Callable[P, R]) -> Callable[P, R]:
```

**Why the author's type is `Callable[P, R]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 19 (first 30, with links to the author's line)</summary>

- `decorator->` ([typed.py:409](../dev/typed.py#L409)): `Callable[P, R]`
- `decorator.func` ([typed.py:409](../dev/typed.py#L409)): `Callable[P, R]`
- `decorator_with_args->` ([typed.py:442](../dev/typed.py#L442)): `Callable[[Callable[P, R]], Callable[P, R]]`
- `decorator_with_args.actual_decorator->` ([typed.py:453](../dev/typed.py#L453)): `Callable[P, R]`
- `decorator_with_args.actual_decorator.func` ([typed.py:453](../dev/typed.py#L453)): `Callable[P, R]`
- `function_with_union_types->` ([typed.py:1323](../dev/typed.py#L1323)): `Callable[[int | str], int | str]`
- `function_with_callable->` ([typed.py:1375](../dev/typed.py#L1375)): `Callable[[Callable[[object], object], object], object]`
- `function_with_decorator_stack.decorator1->` ([typed.py:2316](../dev/typed.py#L2316)): `Callable[P, R]`
- `function_with_decorator_stack.decorator1.func` ([typed.py:2316](../dev/typed.py#L2316)): `Callable[P, R]`
- `function_with_decorator_stack.decorator2->` ([typed.py:2343](../dev/typed.py#L2343)): `Callable[P, R]`
- `function_with_decorator_stack.decorator2.func` ([typed.py:2343](../dev/typed.py#L2343)): `Callable[P, R]`
- `preserve_signature_decorator->` ([typed.py:3820](../dev/typed.py#L3820)): `Callable[P, R | list[object]]`
- `preserve_signature_decorator.func` ([typed.py:3819](../dev/typed.py#L3819)): `Callable[P, R]`
- `decorator_factory->` ([typed.py:3861](../dev/typed.py#L3861)): `Callable[[Callable[P, object]], Callable[P, str]]`
- `decorator_factory.decorate->` ([typed.py:3873](../dev/typed.py#L3873)): `Callable[P, str]`
- `decorator_factory.decorate.func` ([typed.py:3873](../dev/typed.py#L3873)): `Callable[P, object]`
- `test_function_calls_part1.result21` ([typed.py:2689](../dev/typed.py#L2689)): `Callable[[int | str], int | str]`
- `function_with_protocol_like_runtime_checks.update` ([typed.py:4721](../dev/typed.py#L4721)): `Callable[Ellipsis, str] | None`
- `function_with_protocol_like_runtime_checks.execute` ([typed.py:4725](../dev/typed.py#L4725)): `Callable[Ellipsis, tuple[int, int]] | None`

</details>

### TypeVar: 23 missing

Tasks: [M5-16](TODO.md#m5-16--multi-variable-relations), [I-18](TODO.md#i-18--typevar-solving-from-call-arguments), [M5-19](TODO.md#m5-19--t5-paramspec-decorator-forwarding)

how it is [conversion-output.py.txt:265](conversion-output.py.txt#L265) · should be [typed.py:421](../dev/typed.py#L421) · input [untyped.py:196](../dev/untyped.py#L196)

```diff
@@ decorator.wrapper.args · missing · TypeVar @@
-    def wrapper(*args, **kwargs) -> int:
+    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Why the author's type is `args`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:265](conversion-output.py.txt#L265) · should be [typed.py:421](../dev/typed.py#L421) · input [untyped.py:196](../dev/untyped.py#L196)

```diff
@@ decorator.wrapper.kwargs · missing · TypeVar @@
-    def wrapper(*args, **kwargs) -> int:
+    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Why the author's type is `kwargs`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:281](conversion-output.py.txt#L281) · should be [typed.py:465](../dev/typed.py#L465) · input [untyped.py:208](../dev/untyped.py#L208)

```diff
@@ decorator_with_args.actual_decorator.wrapper-> · missing · TypeVar @@
-        def wrapper(*args, **kwargs):
+        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Why the author's type is `R`** (reading `dev/untyped.py` only):

1. [untyped.py:210](../dev/untyped.py#L210) return: `result * multiplier`

*Reading:* No source in this file shows the type; `R` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:281](conversion-output.py.txt#L281) · should be [typed.py:465](../dev/typed.py#L465) · input [untyped.py:208](../dev/untyped.py#L208)

```diff
@@ decorator_with_args.actual_decorator.wrapper.args · missing · TypeVar @@
-        def wrapper(*args, **kwargs):
+        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Why the author's type is `args`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:281](conversion-output.py.txt#L281) · should be [typed.py:465](../dev/typed.py#L465) · input [untyped.py:208](../dev/untyped.py#L208)

```diff
@@ decorator_with_args.actual_decorator.wrapper.kwargs · missing · TypeVar @@
-        def wrapper(*args, **kwargs):
+        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Why the author's type is `kwargs`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 23 (first 30, with links to the author's line)</summary>

- `decorator.wrapper.args` ([typed.py:421](../dev/typed.py#L421)): `args`
- `decorator.wrapper.kwargs` ([typed.py:421](../dev/typed.py#L421)): `kwargs`
- `decorator_with_args.actual_decorator.wrapper->` ([typed.py:465](../dev/typed.py#L465)): `R`
- `decorator_with_args.actual_decorator.wrapper.args` ([typed.py:465](../dev/typed.py#L465)): `args`
- `decorator_with_args.actual_decorator.wrapper.kwargs` ([typed.py:465](../dev/typed.py#L465)): `kwargs`
- `decorator_with_class.cls` ([typed.py:486](../dev/typed.py#L486)): `type[T]`
- `function_with_class_decorator.add_method->` ([typed.py:1953](../dev/typed.py#L1953)): `type[T]`
- `function_with_class_decorator.add_method.cls` ([typed.py:1953](../dev/typed.py#L1953)): `type[T]`
- `function_with_class_decorator.add_method.new_method.self` ([typed.py:1964](../dev/typed.py#L1964)): `T`
- `function_with_decorator_stack.decorator1.wrapper->` ([typed.py:2328](../dev/typed.py#L2328)): `R`
- `function_with_decorator_stack.decorator1.wrapper.args` ([typed.py:2328](../dev/typed.py#L2328)): `args`
- `function_with_decorator_stack.decorator1.wrapper.kwargs` ([typed.py:2328](../dev/typed.py#L2328)): `kwargs`
- `function_with_decorator_stack.decorator2.wrapper->` ([typed.py:2355](../dev/typed.py#L2355)): `R`
- `function_with_decorator_stack.decorator2.wrapper.args` ([typed.py:2355](../dev/typed.py#L2355)): `args`
- `function_with_decorator_stack.decorator2.wrapper.kwargs` ([typed.py:2355](../dev/typed.py#L2355)): `kwargs`
- `preserve_signature_decorator.wrapper->` ([typed.py:3832](../dev/typed.py#L3832)): `R | list[object]`
- `preserve_signature_decorator.wrapper.args` ([typed.py:3832](../dev/typed.py#L3832)): `args`
- `preserve_signature_decorator.wrapper.kwargs` ([typed.py:3832](../dev/typed.py#L3832)): `kwargs`
- `decorator_factory.decorate.wrapper.args` ([typed.py:3885](../dev/typed.py#L3885)): `args`
- `decorator_factory.decorate.wrapper.kwargs` ([typed.py:3885](../dev/typed.py#L3885)): `kwargs`
- `decorator.wrapper.result` ([typed.py:432](../dev/typed.py#L432)): `R`
- `decorator_with_args.actual_decorator.wrapper.result` ([typed.py:476](../dev/typed.py#L476)): `R`
- `preserve_signature_decorator.wrapper.result` ([typed.py:3843](../dev/typed.py#L3843)): `R | list[object]`

</details>

### Library class: 20 missing

Tasks: [I-21](TODO.md#i-21--library-method-returns-on-stub-classes), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [T-08](TODO.md#t-08--library-return-types-from-typeshed)

how it is [conversion-output.py.txt:1201](conversion-output.py.txt#L1201) · should be [typed.py:1850](../dev/typed.py#L1850) · input [untyped.py:907](../dev/untyped.py#L907)

```diff
@@ function_with_exception_chaining.exception_chain_func.raise_second_error.original_error · missing · Library class @@
-        def raise_second_error(original_error) -> Never:
+        def raise_second_error(original_error: ValueError) -> None:
```

**Why the author's type is `ValueError`** (reading `dev/untyped.py` only):

1. [untyped.py:914](../dev/untyped.py#L914) call site passes: `raise_second_error(original_error=e)  ->  e`

*Reading:* No source in this file shows the type; `ValueError` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:1576](conversion-output.py.txt#L1576) · should be [typed.py:2433](../dev/typed.py#L2433) · input [untyped.py:1216](../dev/untyped.py#L1216)

```diff
@@ function_with_permutations_combinations-> · missing · Library class @@
-def function_with_permutations_combinations():
+def function_with_permutations_combinations() -> tuple[
```

**Why the author's type is `tuple[list[tuple[int, Ellipsis]], list[tuple[int, Ellipsis]]]`** (reading `dev/untyped.py` only):

1. [untyped.py:1221](../dev/untyped.py#L1221) return: `(perms, combs)`

*Reading:* No source in this file shows the type; `tuple[list[tuple[int, Ellipsis]], list[tuple[int, Ellipsis]]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2748](conversion-output.py.txt#L2748) · should be [typed.py:4095](../dev/typed.py#L4095) · input [untyped.py:2131](../dev/untyped.py#L2131)

```diff
@@ function_with_walrus_and_narrowing-> · missing · Library class @@
-def function_with_walrus_and_narrowing(records: list[dict[str, None | int | str]]):
+) -> tuple[defaultdict[str, int], list[str]]:
```

**Why the author's type is `tuple[defaultdict[str, int], list[str]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2151](../dev/untyped.py#L2151) return: `(totals, matched)`

*Reading:* No source in this file shows the type; `tuple[defaultdict[str, int], list[str]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2885](conversion-output.py.txt#L2885) · should be [typed.py:4227](../dev/typed.py#L4227) · input [untyped.py:2243](../dev/untyped.py#L2243)

```diff
@@ function_with_exception_group_stress.raise_error_group.errors · missing · Library class @@
-    def raise_error_group(errors) -> Never:
+    def raise_error_group(errors: list[Exception]) -> None:
```

**Why the author's type is `list[Exception]`** (reading `dev/untyped.py` only):

1. [untyped.py:2258](../dev/untyped.py#L2258) call site passes: `raise_error_group(errors=errors)  ->  errors`

*Reading:* No source in this file shows the type; `list[Exception]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:3092](conversion-output.py.txt#L3092) · should be [typed.py:4630](../dev/typed.py#L4630) · input [untyped.py:2425](../dev/untyped.py#L2425)

```diff
@@ function_with_nested_default_factories-> · missing · Library class @@
-def function_with_nested_default_factories():
+def function_with_nested_default_factories() -> tuple[
```

**Why the author's type is `tuple[defaultdict[str, defaultdict[str, list[int]]], dict[str, dict[str, tuple[int, Ellipsis]]]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2439](../dev/untyped.py#L2439) return: `(tree, frozen)`

*Reading:* No source in this file shows the type; `tuple[defaultdict[str, defaultdict[str, list[int]]], dict[str, dict[str, tuple[int, Ellipsis]]]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 20 (first 30, with links to the author's line)</summary>

- `function_with_exception_chaining.exception_chain_func.raise_second_error.original_error` ([typed.py:1850](../dev/typed.py#L1850)): `ValueError`
- `function_with_permutations_combinations->` ([typed.py:2433](../dev/typed.py#L2433)): `tuple[list[tuple[int, Ellipsis]], list[tuple[int, Ellipsis]]]`
- `function_with_walrus_and_narrowing->` ([typed.py:4095](../dev/typed.py#L4095)): `tuple[defaultdict[str, int], list[str]]`
- `function_with_exception_group_stress.raise_error_group.errors` ([typed.py:4227](../dev/typed.py#L4227)): `list[Exception]`
- `function_with_nested_default_factories->` ([typed.py:4630](../dev/typed.py#L4630)): `tuple[defaultdict[str, defaultdict[str, list[int]]], dict[str, dict[str, tuple[int, Ellipsis]]]]`
- `function_with_bytes_memoryview_and_slices->` ([typed.py:4783](../dev/typed.py#L4783)): `tuple[bytearray, memoryview, bytes, int]`
- `function_with_permutations_combinations.perms` ([typed.py:2444](../dev/typed.py#L2444)): `list[tuple[int, Ellipsis]]`
- `function_with_permutations_combinations.combs` ([typed.py:2445](../dev/typed.py#L2445)): `list[tuple[int, Ellipsis]]`
- `function_with_deque.d` ([typed.py:2479](../dev/typed.py#L2479)): `deque[int]`
- `function_with_islice.data` ([typed.py:2539](../dev/typed.py#L2539)): `range`
- `test_function_calls_part3.result50` ([typed.py:2798](../dev/typed.py#L2798)): `tuple[list[tuple[int, Ellipsis]], list[tuple[int, Ellipsis]]]`
- `function_with_importlib_and_dunder_import.pathlib_module` ([typed.py:3130](../dev/typed.py#L3130)): `ModuleType`
- `function_with_importlib_and_dunder_import.os_path_module` ([typed.py:3131](../dev/typed.py#L3131)): `ModuleType`
- `function_with_exception_group_stress.errors` ([typed.py:4240](../dev/typed.py#L4240)): `list[Exception]`
- `function_with_import_and_reflection_stress.module` ([typed.py:4273](../dev/typed.py#L4273)): `ModuleType`
- `function_with_json_uuid_and_path_stress.identifier` ([typed.py:4294](../dev/typed.py#L4294)): `UUID`
- `function_with_nested_default_factories.frozen` ([typed.py:4650](../dev/typed.py#L4650)): `dict[str, dict[str, tuple[int, Ellipsis]]]`
- `function_with_bytes_memoryview_and_slices.raw` ([typed.py:4793](../dev/typed.py#L4793)): `bytearray`
- `function_with_bytes_memoryview_and_slices.view` ([typed.py:4795](../dev/typed.py#L4795)): `memoryview[int]`
- `function_with_map_filter_zip_stress.paired` ([typed.py:4815](../dev/typed.py#L4815)): `zip[tuple[int, int]]`

</details>

### Generator/Iterator: 8 missing

Tasks: [W-13](TODO.md#w-13--type-generators-as-iterator), [G-05](TODO.md#g-05--normalise-generator-defaults-and-subtype-spelling-in-the-scorer)

how it is [conversion-output.py.txt:479](conversion-output.py.txt#L479) · should be [typed.py:761](../dev/typed.py#L761) · input [untyped.py:336](../dev/untyped.py#L336)

```diff
@@ function_with_comprehensions-> · missing · Generator/Iterator @@
-def function_with_comprehensions(items: list[int]):
+) -> tuple[list[int], dict[int, int], Generator[int]]:
```

**Why the author's type is `tuple[list[int], dict[int, int], Generator[int]]`** (reading `dev/untyped.py` only):

1. [untyped.py:341](../dev/untyped.py#L341) return: `(squared, filtered, generator)`

*Reading:* No source in this file shows the type; `tuple[list[int], dict[int, int], Generator[int]]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2233](conversion-output.py.txt#L2233) · should be [typed.py:3276](../dev/typed.py#L3276) · input [untyped.py:1788](../dev/untyped.py#L1788)

```diff
@@ ExtendedResult.__iter__-> · missing · Generator/Iterator @@
-    def __iter__(self):
+    def __iter__(self) -> Iterator[object]:
```

**Why the author's type is `Iterator[object]`** (reading `dev/untyped.py` only):

1. [untyped.py:1788](../dev/untyped.py#L1788) generator: `the body contains 'yield'`
2. [untyped.py:1792](../dev/untyped.py#L1792) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`; the author widened to the top type (`Iterator[object]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2488](conversion-output.py.txt#L2488) · should be [typed.py:3627](../dev/typed.py#L3627) · input [untyped.py:1958](../dev/untyped.py#L1958)

```diff
@@ HybridContainer.__iter__-> · missing · Generator/Iterator @@
-    def __iter__(self):
+    def __iter__(self) -> Iterator[object]:
```

**Why the author's type is `Iterator[object]`** (reading `dev/untyped.py` only):

1. [untyped.py:1960](../dev/untyped.py#L1960) return: `iter(self.items)`

*Reading:* No source in this file shows the type; `Iterator[object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2601](conversion-output.py.txt#L2601) · should be [typed.py:3783](../dev/typed.py#L3783) · input [untyped.py:2031](../dev/untyped.py#L2031)

```diff
@@ extended_sync_context-> · missing · Generator/Iterator @@
-def extended_sync_context(seed):
+def extended_sync_context(seed: int) -> Generator[dict[str, object]]:
```

**Why the author's type is `Generator[dict[str, object]]`** (reading `dev/untyped.py` only):

1. [untyped.py:2031](../dev/untyped.py#L2031) generator: `the body contains 'yield'`
2. [untyped.py:2038](../dev/untyped.py#L2038) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`; the author widened to the top type (`Generator[dict[str, object]]`). A narrower type that the evidence supports is valid for every caller in this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2616](conversion-output.py.txt#L2616) · should be [typed.py:3803](../dev/typed.py#L3803) · input [untyped.py:2042](../dev/untyped.py#L2042)

```diff
@@ extended_async_context-> · missing · Generator/Iterator @@
-async def extended_async_context(seed: int):
+async def extended_async_context(seed: int) -> AsyncGenerator[AsyncResource]:
```

**Why the author's type is `AsyncGenerator[AsyncResource]`** (reading `dev/untyped.py` only):

1. [untyped.py:2042](../dev/untyped.py#L2042) generator: `the body contains 'yield'`
2. [untyped.py:2046](../dev/untyped.py#L2046) falls off the end: `some path ends without 'return', so it returns None` → `None`

*Reading:* The sources show `None`, which does not add up to `AsyncGenerator[AsyncResource]`: either a rule is missing or the author knew something this file does not say.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 8 (first 30, with links to the author's line)</summary>

- `function_with_comprehensions->` ([typed.py:761](../dev/typed.py#L761)): `tuple[list[int], dict[int, int], Generator[int]]`
- `ExtendedResult.__iter__->` ([typed.py:3276](../dev/typed.py#L3276)): `Iterator[object]`
- `HybridContainer.__iter__->` ([typed.py:3627](../dev/typed.py#L3627)): `Iterator[object]`
- `extended_sync_context->` ([typed.py:3783](../dev/typed.py#L3783)): `Generator[dict[str, object]]`
- `extended_async_context->` ([typed.py:3803](../dev/typed.py#L3803)): `AsyncGenerator[AsyncResource]`
- `function_with_generator_send_throw_close->` ([typed.py:4355](../dev/typed.py#L4355)): `tuple[int, int, Generator[int, int | str | None, int]]`
- `function_with_async_comprehension_stress.produce->` ([typed.py:4506](../dev/typed.py#L4506)): `AsyncIterator[int]`
- `test_function_calls_part1.result8` ([typed.py:2672](../dev/typed.py#L2672)): `tuple[list[int], dict[int, int], Generator[int]]`

</details>

### Optional: 11 missing

Tasks: [I-01](TODO.md#i-01--narrow-the-else-branch-by-complement), [I-08](TODO.md#i-08--optional-results-of-stdlib-lookups), [AL-01](TODO.md#al-01--control-flow-graph-and-per-block-narrowing-replaces-ad-hoc-if-handling)

how it is [conversion-output.py.txt:1652](conversion-output.py.txt#L1652) · should be [typed.py:2558](../dev/typed.py#L2558) · input [untyped.py:1287](../dev/untyped.py#L1287)

```diff
@@ function_with_zip_longest-> · missing · Optional @@
-def function_with_zip_longest():
+def function_with_zip_longest() -> list[tuple[int | None, str | None]]:
```

**Why the author's type is `list[tuple[int | None, str | None]]`** (reading `dev/untyped.py` only):

1. [untyped.py:1291](../dev/untyped.py#L1291) return: `list(zip_longest(list1, list2))` → `list[?]`

*Reading:* The sources show a container but not its element type, so nothing here fixes `list[tuple[int | None, str | None]]`; the author's choice adds knowledge from outside this file.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2221](conversion-output.py.txt#L2221) · should be [typed.py:3262](../dev/typed.py#L3262) · input [untyped.py:1782](../dev/untyped.py#L1782)

```diff
@@ ExtendedResult.__init__.metadata · missing · Optional @@
-    def __init__(self, name: str, payload: list[int], metadata=None) -> None:
+        metadata: ExtendedMetadata | None = None,
```

**Why the author's type is `ExtendedMetadata | None`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*
4. [untyped.py:1782](../dev/untyped.py#L1782) default value: `None` → `None`
5. [untyped.py:1786](../dev/untyped.py#L1786) body compares it with None: `metadata is None`
6. [untyped.py:2581](../dev/untyped.py#L2581) call site passes: `ExtendedResult(name='alpha', payload=[1, 2, 3], metadata={'ok': True})  ->  {'ok': True}` → `dict[str, bool]`

*Reading:* The sources show `None | dict[str, bool]`, which does not add up to `ExtendedMetadata | None`: either a rule is missing or the author knew something this file does not say.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2265](conversion-output.py.txt#L2265) · should be [typed.py:3325](../dev/typed.py#L3325) · input [untyped.py:1816](../dev/untyped.py#L1816)

```diff
@@ ExtendedDataclassStress.__init__.values · missing · Optional @@
-        values=None,
+        values: list[int] | None = None,
```

**Why the author's type is `list[int] | None`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*
4. [untyped.py:1816](../dev/untyped.py#L1816) default value: `None` → `None`
5. [untyped.py:1822](../dev/untyped.py#L1822) body compares it with None: `values is None`

*Reading:* The typed source(s) explain `None`; nothing in this file shows `list[int]`, the part the author adds to reach `list[int] | None`.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2266](conversion-output.py.txt#L2266) · should be [typed.py:3326](../dev/typed.py#L3326) · input [untyped.py:1817](../dev/untyped.py#L1817)

```diff
@@ ExtendedDataclassStress.__init__.lookup · missing · Optional @@
-        lookup=None,
+        lookup: dict[str, int] | None = None,
```

**Why the author's type is `dict[str, int] | None`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*
4. [untyped.py:1817](../dev/untyped.py#L1817) default value: `None` → `None`
5. [untyped.py:1823](../dev/untyped.py#L1823) body compares it with None: `lookup is None`

*Reading:* The typed source(s) explain `None`; nothing in this file shows `dict[str, int]`, the part the author adds to reach `dict[str, int] | None`.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2412](conversion-output.py.txt#L2412) · should be [typed.py:3531](../dev/typed.py#L3531) · input [untyped.py:1911](../dev/untyped.py#L1911)

```diff
@@ RegistryItem.__init__.tags · missing · Optional @@
-    def __init__(self, name: str, count: int = 0, tags=None, **extras) -> None:
+        tags: list[str] | None = None,
```

**Why the author's type is `list[str] | None`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*
4. [untyped.py:1911](../dev/untyped.py#L1911) default value: `None` → `None`
5. [untyped.py:1915](../dev/untyped.py#L1915) body compares it with None: `tags is None`
6. [untyped.py:2353](../dev/untyped.py#L2353) call site passes: `RegistryItem(name='alpha', count=1, tags=['x'], extra=True)  ->  ['x']` → `list[str]`

*Reading:* Joining what the 2 typed source(s) show (`None | list[str]`) gives exactly the author's `list[str] | None`.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 11 (first 30, with links to the author's line)</summary>

- `function_with_zip_longest->` ([typed.py:2558](../dev/typed.py#L2558)): `list[tuple[int | None, str | None]]`
- `ExtendedResult.__init__.metadata` ([typed.py:3262](../dev/typed.py#L3262)): `ExtendedMetadata | None`
- `ExtendedDataclassStress.__init__.values` ([typed.py:3325](../dev/typed.py#L3325)): `list[int] | None`
- `ExtendedDataclassStress.__init__.lookup` ([typed.py:3326](../dev/typed.py#L3326)): `dict[str, int] | None`
- `RegistryItem.__init__.tags` ([typed.py:3531](../dev/typed.py#L3531)): `list[str] | None`
- `AsyncResource.__aexit__.exc_type` ([typed.py:3749](../dev/typed.py#L3749)): `type[BaseException] | None`
- `AsyncResource.__aexit__.exc` ([typed.py:3750](../dev/typed.py#L3750)): `BaseException | None`
- `Constants.extended_context` ([typed.py:99](../dev/typed.py#L99)): `ContextVar[ExtendedContextMap | None]`
- `function_with_singleton.Singleton._instance` ([typed.py:2004](../dev/typed.py#L2004)): `Singleton | None`
- `test_function_calls_part3.result59` ([typed.py:2809](../dev/typed.py#L2809)): `list[tuple[int | None, str | None]]`
- `function_with_generator_send_throw_close.controlled_generator.received` ([typed.py:4375](../dev/typed.py#L4375)): `int | str | None`

</details>

### Abstract collection: 5 missing

Tasks: [M4-16](TODO.md#m4-16--accept-generalreturn-specific), [AL-13](TODO.md#al-13--mutation-summaries-decide-sequence-versus-list), [G-02](TODO.md#g-02--score-valid-narrowing-as-narrower-not-wrong)

how it is [conversion-output.py.txt:1328](conversion-output.py.txt#L1328) · should be [typed.py:2068](../dev/typed.py#L2068) · input [untyped.py:1030](../dev/untyped.py#L1030)

```diff
@@ function_with_builder.Product.__init__.parts · missing · Abstract collection @@
-        def __init__(self, parts) -> None:
+        def __init__(self, parts: Sequence[str]) -> None:
```

**Why the author's type is `Sequence[str]`** (reading `dev/untyped.py` only):

1. [untyped.py:135](../dev/untyped.py#L135) same-named method in BaseClass: `BaseClass.__init__(self, x, y=None)` *(matched by name only)*
2. [untyped.py:158](../dev/untyped.py#L158) same-named method in DerivedClass: `DerivedClass.__init__(self, x, y=None, z=0)` *(matched by name only)*
3. [untyped.py:187](../dev/untyped.py#L187) same-named method in MetaDecoratedClass: `MetaDecoratedClass.__init__(self, value)` *(matched by name only)*
4. [untyped.py:1045](../dev/untyped.py#L1045) call site passes: `Product(parts=self.parts)  ->  self.parts`

*Reading:* No source in this file shows the type; `Sequence[str]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2522](conversion-output.py.txt#L2522) · should be [typed.py:3675](../dev/typed.py#L3675) · input [untyped.py:1979](../dev/untyped.py#L1979)

```diff
@@ HybridContainer.__or__.other · missing · Abstract collection @@
-    def __or__(self, other):
+    def __or__(self, other: HybridContainer | Mapping[str, object]) -> Self:
```

**Why the author's type is `HybridContainer | Mapping[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:1982](../dev/untyped.py#L1982) body calls isinstance: `isinstance(other, HybridContainer)`

*Reading:* No source in this file shows the type; `HybridContainer | Mapping[str, object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2941](conversion-output.py.txt#L2941) · should be [typed.py:4309](../dev/typed.py#L4309) · input [untyped.py:2294](../dev/untyped.py#L2294)

```diff
@@ function_with_contextvars_and_chainmap-> · missing · Abstract collection @@
-def function_with_contextvars_and_chainmap(configs: list[dict[str, int]]):
+) -> Mapping[str, object]:
```

**Why the author's type is `Mapping[str, object]`** (reading `dev/untyped.py` only):

1. [untyped.py:2303](../dev/untyped.py#L2303) return: `resolved`

*Reading:* No source in this file shows the type; `Mapping[str, object]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is n/a · should be [typed.py:4563](../dev/typed.py#L4563) · input n/a

```diff
@@ LocalMultiplierFactory.from_values.values · missing · Abstract collection @@
+        values: Sequence[int],
```

**Why the author's type is `Sequence[int]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:3224](conversion-output.py.txt#L3224) · should be [typed.py:4862](../dev/typed.py#L4862) · input [untyped.py:2536](../dev/untyped.py#L2536)

```diff
@@ function_with_composed_inner_functions.score.tokens · missing · Abstract collection @@
-    def score(tokens):
+    def score(tokens: Sequence[str]) -> dict[str, int]:
```

**Why the author's type is `Sequence[str]`** (reading `dev/untyped.py` only):

1. [untyped.py:2541](../dev/untyped.py#L2541) call site passes: `score(tokens=tokenize(value='Alpha beta alpha'))  ->  tokenize(value='Alpha beta alpha')`

*Reading:* No source in this file shows the type; `Sequence[str]` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 5 (first 30, with links to the author's line)</summary>

- `function_with_builder.Product.__init__.parts` ([typed.py:2068](../dev/typed.py#L2068)): `Sequence[str]`
- `HybridContainer.__or__.other` ([typed.py:3675](../dev/typed.py#L3675)): `HybridContainer | Mapping[str, object]`
- `function_with_contextvars_and_chainmap->` ([typed.py:4309](../dev/typed.py#L4309)): `Mapping[str, object]`
- `LocalMultiplierFactory.from_values.values` ([typed.py:4563](../dev/typed.py#L4563)): `Sequence[int]`
- `function_with_composed_inner_functions.score.tokens` ([typed.py:4862](../dev/typed.py#L4862)): `Sequence[str]`

</details>

### ClassVar/Final: 7 missing

Tasks: [AF-05](TODO.md#af-05--classvar-and-final-inference), [G-06](TODO.md#g-06--never-type-a-descriptor-attribute-as-its-value)

how it is n/a · should be [typed.py:95](../dev/typed.py#L95) · input n/a

```diff
@@ Constants.threshold · missing · ClassVar/Final @@
+    threshold: Final[int] = 5
```

**Why the author's type is `Final[int]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is n/a · should be [typed.py:96](../dev/typed.py#L96) · input n/a

```diff
@@ Constants.max_value · missing · ClassVar/Final @@
+    max_value: Final[int] = 10
```

**Why the author's type is `Final[int]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is n/a · should be [typed.py:97](../dev/typed.py#L97) · input n/a

```diff
@@ Constants.min_length · missing · ClassVar/Final @@
+    min_length: Final[int] = 3
```

**Why the author's type is `Final[int]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is n/a · should be [typed.py:98](../dev/typed.py#L98) · input n/a

```diff
@@ Constants.extended_sentinel · missing · ClassVar/Final @@
+    extended_sentinel: Final[object] = object()
```

**Why the author's type is `Final[object]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2341](conversion-output.py.txt#L2341) · should be [typed.py:3425](../dev/typed.py#L3425) · input [untyped.py:1862](../dev/untyped.py#L1862)

```diff
@@ DescriptorStressOwner.score · missing · ClassVar/Final @@
-    score = DescriptorWithOwnerCache(default=0)
+    score: ClassVar[DescriptorWithOwnerCache] = DescriptorWithOwnerCache(
```

**Why the author's type is `ClassVar[DescriptorWithOwnerCache]`** (reading `dev/untyped.py` only):

1. [untyped.py:1862](../dev/untyped.py#L1862) assignment: `score = DescriptorWithOwnerCache(default=0)` → `DescriptorWithOwnerCache`

*Reading:* The sources show `DescriptorWithOwnerCache`, which does not add up to `ClassVar[DescriptorWithOwnerCache]`: either a rule is missing or the author knew something this file does not say.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 7 (first 30, with links to the author's line)</summary>

- `Constants.threshold` ([typed.py:95](../dev/typed.py#L95)): `Final[int]`
- `Constants.max_value` ([typed.py:96](../dev/typed.py#L96)): `Final[int]`
- `Constants.min_length` ([typed.py:97](../dev/typed.py#L97)): `Final[int]`
- `Constants.extended_sentinel` ([typed.py:98](../dev/typed.py#L98)): `Final[object]`
- `DescriptorStressOwner.score` ([typed.py:3425](../dev/typed.py#L3425)): `ClassVar[DescriptorWithOwnerCache]`
- `DescriptorStressOwner.label` ([typed.py:3428](../dev/typed.py#L3428)): `ClassVar[DescriptorWithOwnerCache]`
- `RegistryMeta.registry` ([typed.py:3462](../dev/typed.py#L3462)): `ClassVar[dict[str, type[object]]]`

</details>

### Union: 5 missing

Tasks: [AL-05](TODO.md#al-05--probabilistic-fusion-of-evidence-log-odds-instead-of-hand-tiers), [I-19](TODO.md#i-19--join-and-simplify-unions-deterministically)

how it is [conversion-output.py.txt:856](conversion-output.py.txt#L856) · should be [typed.py:1331](../dev/typed.py#L1331) · input [untyped.py:634](../dev/untyped.py#L634)

```diff
@@ function_with_union_types.union_function.value · missing · Union @@
-    def union_function(value) -> int | str:
+    def union_function(value: int | str) -> int | str:
```

**Why the author's type is `int | str`** (reading `dev/untyped.py` only):

1. [untyped.py:636](../dev/untyped.py#L636) body calls isinstance: `isinstance(value, int)`
2. [untyped.py:637](../dev/untyped.py#L637) body uses it in arithmetic: `value * 2` → `int`
3. [untyped.py:638](../dev/untyped.py#L638) body calls isinstance: `isinstance(value, str)`
4. [untyped.py:639](../dev/untyped.py#L639) body calls a method: `value.upper()` → `is a str`

*Reading:* The sources show `int | isastr`, which does not add up to `int | str`: either a rule is missing or the author knew something this file does not say.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2243](conversion-output.py.txt#L2243) · should be [typed.py:3296](../dev/typed.py#L3296) · input [untyped.py:1798](../dev/untyped.py#L1798)

```diff
@@ ExtendedResult.__getitem__.index · missing · Union @@
-    def __getitem__(self, index):
+    def __getitem__(self, index: int | str) -> object:
```

**Why the author's type is `int | str`** (reading `dev/untyped.py` only):

1. [untyped.py:1966](../dev/untyped.py#L1966) same-named method in HybridContainer: `HybridContainer.__getitem__(self, key)` *(matched by name only)*

*Reading:* No source in this file shows the type; `int | str` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2500](conversion-output.py.txt#L2500) · should be [typed.py:3648](../dev/typed.py#L3648) · input [untyped.py:1966](../dev/untyped.py#L1966)

```diff
@@ HybridContainer.__getitem__.key · missing · Union @@
-    def __getitem__(self, key) -> int:
+    def __getitem__(self, key: int | str) -> object:
```

**Why the author's type is `int | str`** (reading `dev/untyped.py` only):

1. [untyped.py:1798](../dev/untyped.py#L1798) same-named method in ExtendedResult: `ExtendedResult.__getitem__(self, index)` *(matched by name only)*
2. [untyped.py:1968](../dev/untyped.py#L1968) body calls isinstance: `isinstance(key, int)`

*Reading:* No source in this file shows the type; `int | str` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2510](conversion-output.py.txt#L2510) · should be [typed.py:3662](../dev/typed.py#L3662) · input [untyped.py:1972](../dev/untyped.py#L1972)

```diff
@@ HybridContainer.__setitem__.key · missing · Union @@
-    def __setitem__(self, key, value) -> None:
+    def __setitem__(self, key: int | str, value: object) -> None:
```

**Why the author's type is `int | str`** (reading `dev/untyped.py` only):

1. [untyped.py:1974](../dev/untyped.py#L1974) body calls isinstance: `isinstance(key, int)`

*Reading:* No source in this file shows the type; `int | str` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is n/a · should be [typed.py:3044](../dev/typed.py#L3044) · input n/a

```diff
@@ ScopeResolutionResult.method_and_nested_results · missing · Union @@
+    method_and_nested_results: list[float | str]
```

**Why the author's type is `list[float | str]`** (reading `dev/untyped.py` only):

No evidence was found for this node in the untyped source.

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 5 (first 30, with links to the author's line)</summary>

- `function_with_union_types.union_function.value` ([typed.py:1331](../dev/typed.py#L1331)): `int | str`
- `ExtendedResult.__getitem__.index` ([typed.py:3296](../dev/typed.py#L3296)): `int | str`
- `HybridContainer.__getitem__.key` ([typed.py:3648](../dev/typed.py#L3648)): `int | str`
- `HybridContainer.__setitem__.key` ([typed.py:3662](../dev/typed.py#L3662)): `int | str`
- `ScopeResolutionResult.method_and_nested_results` ([typed.py:3044](../dev/typed.py#L3044)): `list[float | str]`

</details>

### Self: 3 missing

Tasks: [W-11](TODO.md#w-11--annotate-a-method-that-returns-its-own-class-self-or-quoted-name), [AF-02](TODO.md#af-02--annotate-selfcls-only-when-the-style-asks), [F-43](TODO.md#f-43--quote-instead-of-refusing)

how it is [conversion-output.py.txt:2522](conversion-output.py.txt#L2522) · should be [typed.py:3675](../dev/typed.py#L3675) · input [untyped.py:1979](../dev/untyped.py#L1979)

```diff
@@ HybridContainer.__or__-> · missing · Self @@
-    def __or__(self, other):
+    def __or__(self, other: HybridContainer | Mapping[str, object]) -> Self:
```

**Why the author's type is `Self`** (reading `dev/untyped.py` only):

1. [untyped.py:1987](../dev/untyped.py#L1987) return: `merged`

*Reading:* No source in this file shows the type; `Self` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:2574](conversion-output.py.txt#L2574) · should be [typed.py:3737](../dev/typed.py#L3737) · input [untyped.py:2014](../dev/untyped.py#L2014)

```diff
@@ AsyncResource.__aenter__-> · missing · Self @@
-    async def __aenter__(self):
+    async def __aenter__(self) -> Self:
```

**Why the author's type is `Self`** (reading `dev/untyped.py` only):

1. [untyped.py:2017](../dev/untyped.py#L2017) return: `self`

*Reading:* No source in this file shows the type; `Self` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

how it is [conversion-output.py.txt:3086](conversion-output.py.txt#L3086) · should be [typed.py:4615](../dev/typed.py#L4615) · input [untyped.py:2419](../dev/untyped.py#L2419)

```diff
@@ function_with_local_class_closure_stress.LocalMultiplier.from_values-> · missing · Self @@
-        def from_values(cls, values: list[int]):
+        def from_values(cls, values: Sequence[int]) -> Self:
```

**Why the author's type is `Self`** (reading `dev/untyped.py` only):

1. [untyped.py:2420](../dev/untyped.py#L2420) return: `cls(offset=sum(values))`

*Reading:* No source in this file shows the type; `Self` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 3 (first 30, with links to the author's line)</summary>

- `HybridContainer.__or__->` ([typed.py:3675](../dev/typed.py#L3675)): `Self`
- `AsyncResource.__aenter__->` ([typed.py:3737](../dev/typed.py#L3737)): `Self`
- `function_with_local_class_closure_stress.LocalMultiplier.from_values->` ([typed.py:4615](../dev/typed.py#L4615)): `Self`

</details>

### Other: 1 missing

Tasks: [G-04](TODO.md#g-04--root-cause-every-remaining-contradiction)

how it is [conversion-output.py.txt:290](conversion-output.py.txt#L290) · should be [typed.py:486](../dev/typed.py#L486) · input [untyped.py:217](../dev/untyped.py#L217)

```diff
@@ decorator_with_class-> · missing · Other @@
-def decorator_with_class(cls):
+def decorator_with_class(cls: type[T]) -> type:
```

**Why the author's type is `type`** (reading `dev/untyped.py` only):

1. [untyped.py:229](../dev/untyped.py#L229) return: `Wrapper`

*Reading:* No source in this file shows the type; `type` is the author's intent (naming, documentation or use elsewhere).

**Why astart left it unannotated:** its contract graph has no node for this path, so no rule looked at it.

<details><summary>All 1 (first 30, with links to the author's line)</summary>

- `decorator_with_class->` ([typed.py:486](../dev/typed.py#L486)): `type`

</details>

## Why nodes stay unannotated

From [`scripts/opacity_report.py`](../scripts/opacity_report.py) on the untyped input. A node is something that has a type: a parameter, a return value or a local variable. A *direct* reason blocks a node by itself; the other labels describe nodes that are typed, declared, or blocked only because of another node.

The opacity analysis was skipped or could not run.

## Reproduce

`python scripts/conversion_report.py --min-confidence 0.5`
