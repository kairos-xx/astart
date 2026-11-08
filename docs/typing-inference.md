# Typing inference

What `_Typer` in `src/astart/rules/provable.py` can prove from an
expression's syntax alone, and which evidence classes a written
annotation must pass through before it is applied.

## Expression → type table

Produced by running `expression_type(node=parse(source=t,
mode="eval").body, counts={})` on each text. "gap" rows are the known
holes and name the task that closes them.

| Expression | Type today | Status |
| --- | --- | --- |
| `1 + 2`, `7 // 2`, `7 % 2`, `-1`, `True + True` | `int` | ok |
| `1 + 2.0`, `1 / 2` | `float` | ok |
| `'a' + 'b'`, `'a' * 3` | `str` | ok |
| `1 < 2`, `'a' in 'b'`, `not 1` | `bool` | ok |
| `1 if True else 2`, `1 and 2` | `int` | ok |
| `str(1)`, `chr(97)`, `repr(1)` | `str` | ok |
| `int('1')`, `ord('a')` | `int` | ok |
| `float(1)` / `bool(0)` / `isinstance(1, int)` | `float` / `bool` / `bool` | ok |
| `{1, 2}` / `(1, 'a')` / `b'x'` | `set[int]` / `tuple[int, str]` / `bytes` | ok |
| `[i for i in range(3)]` | `list[int]` | ok |
| `1 if True else 'a'`, `1 or 'a'`, `[1, 'a']` | none | correct refusal (mixed types) |
| `2 ** 3` | none | gap → Q-55 |
| `'a'.upper()` | none | gap → Q-01 |
| `[1][0]` | none | gap → Q-05 |
| `abs(-1)` | none | gap → Q-06 |
| `f(1)` (unknown `f`) | none | correct refusal |

## Evidence classes

- **E0 syntax-proves** — The type is provable from the syntax itself: a literal default, an explicit `return None`, a `+`/`/` operator on known operands.
- **E1 declared-elsewhere** — A stub (`.pyi`), base-class signature, `@overload`, or implemented ABC already declares the type.
- **E2 closed-world usage** — Every call site in the module agrees, and the function cannot escape (not assigned, returned, decorated, passed).
- **E3 cross-module call sites** — Call sites in *other* modules agree on the type.
- **E4 library signature flow** — A stdlib/typed-library signature (typeshed, `libkw` table) flows the type in.
- **E5 inference proposal** — The `_graph`/`semantic` engine *proposes* a candidate.
- **E6 checker does not object** — pyright/basedpyright reports no new error after the fix.

See `docs/evidence-ladder.md` for the acceptance rule these classes
combine under.

## How to add a typer rule

1. Add a handler in `_Typer.__init__`'s `_handlers` dict
   (`NodeClass: self._method`).
2. Implement the method returning `str | None` — the provable
   annotation source, or `None` to refuse.
3. Add a row to the Q-54 matrix (`tests/test_rules_typer_matrix.py`).
4. Add a row to the Q-57 matrix (`tests/test_rules_return_matrix.py`).
5. Run the fast tier (`pytest -m "not slow"`).
