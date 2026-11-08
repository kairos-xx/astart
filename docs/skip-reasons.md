# Skip reasons — `Rejection`

Every value of `Rejection` in `src/astart/rules/reasons.py` — why a type
hint was refused. Each line gives the string value and the sentence from
the member's docstring.

- `contains object` — The candidate mentions ``object`` or ``Any``.
- `None default` — The parameter defaults to ``None``.
- `call sites disagree` — Call sites pass different types.
- `call sites unknown` — A call site's argument type is unknown.
- `declaration body` — The function is a declaration, not an implementation.
- `default disagrees` — The default's type differs from the candidate.
- `engine disagrees` — The inference differs from the syntax proof.
- `escapes as a value` — The function is used as a value, so callers are unknown.
- `generator` — The function is a generator.
- `needs import or unknown name` — The annotation needs an import that cannot be added.
- `no candidate` — Nothing proposed a type.
- `protocol result differs` — A protocol dunder's body contradicts the type the protocol declares.
- `return type not provable` — The return type is not provable from the syntax.
- `uncorroborated` — No call site corroborates the candidate.
- `tainted by parameter` — A returned value depends on an unannotated parameter.
