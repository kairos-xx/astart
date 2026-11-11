# Security model

`astart` analyses Python source. It is a static tool: it parses files,
builds evidence and rewrites text. It never runs the code it analyses.

## What the product does with your code

- **Parsing only.** `astart check`, `astart fix`, `astart transform` and
  `astart convert` read source bytes, decode them (PEP 263 encodings are
  honoured), parse them with the stdlib `ast` module and rewrite the text.
  No analysed module is imported, compiled to bytecode for execution, or
  evaluated.
- **One opt-in exception.** `astart fix --checker auto` may run an
  installed `basedpyright`/`pyright` on a *scratch copy* of the file in a
  temp directory to veto guarded fixes. The checker is an external
  read-only analyser; astart passes it file paths, never executes project
  code itself. `--checker off` disables this entirely.
- **Subprocesses use argument vectors.** The only subprocess calls are
  `ruff format` (via `subprocess.run(args=[...])` in
  `graph/conversion/artifacts.py`) and the checker runner
  (`rules/process.py`, `asyncio.create_subprocess_exec` with an argument
  tuple). No shell is involved; `shell=True` is forbidden and guarded by
  `tests/astart/test_no_dynamic_execution.py`.

## What is forbidden (and tested)

`tests/astart/test_no_dynamic_execution.py` AST-scans every module under
`src/astart` and fails on:

- `exec(...)`, `eval(...)`, `__import__(...)`,
  `importlib.import_module(...)` — dynamic code loading/execution;
- `os.system(...)`, `shell=True` keywords, `create_subprocess_shell` —
  shell interpretation of commands;
- subprocess calls whose command is a plain string instead of an
  argument vector.

Reviewed exceptions are listed in the test's `_ALLOWED` table with their
justification (today: `typeshed_client.py`'s env-gated package import,
`recovery.py`'s `import_module("typing")` and `protocol_verify.py`'s
`__import__("builtins")` — all fixed or configured names, never names
derived from analysed source).

## Benchmarks are different

The benchmark harness (`benchmarks/`, not shipped as the product) *does*
import target packages for the semantic-equivalence measurements. Those
runs are explicit developer actions on trusted corpora, not part of
`astart check`/`fix`.

## Plugins

The plugin API (API-07) is not yet public. When it lands, plugins load
only module names listed in `[tool.astart] plugins = [...]` — never names
discovered inside the analysed project's own tree — so analysing an
untrusted repository cannot make astart import attacker-chosen code.

## Supply chain

- No runtime dependencies: the package is stdlib-only (`py.typed` ships
  types inline).
- `libkw.SIGNATURES` is generated offline by `scripts/utils/generate_libkw.py`
  from typeshed data; it is data, not executable code.
- The typeshed reader (`astart.stubs`) parses `.pyi` text itself and does
  not execute stubs. Its corpus is vendored inside the wheel
  (`astart/stubs/artifacts/typeshed/`, Apache-2.0 with the licence file), reviewed
  at release time rather than fetched or discovered from the user's
  machine at runtime; `ASTART_TYPESHED`/an explicit root remain the only
  overrides.
