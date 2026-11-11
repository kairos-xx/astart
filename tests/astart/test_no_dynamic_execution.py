"""Guard: ``src/astart`` never executes or dynamically loads project code.

The product analyses source; it must not run it. This test walks every
module under ``src/astart`` and fails on ``exec``, ``eval``, ``__import__``,
``importlib.import_module``, ``os.system``, ``shell=True`` and subprocess
calls whose command is a plain string rather than an argument vector.
``_ALLOWED`` lists the reviewed exceptions — each entry names the pattern
and why it is safe.

"""

from ast import (
    Attribute,
    Call,
    Constant,
    Import,
    ImportFrom,
    Module,
    Name,
    expr,
    parse,
    walk,
)
from pathlib import Path
from typing import Final, final

from tests.support.expectations import expect_equal
from tests.support.paths import Paths

REPO_ROOT: Final[Path] = Paths.root


@final
class Constants:
    """Group module-level constants.

    Attributes:
        allowed (Final[dict[str, frozenset[str]]]): Reviewed exceptions,
            ``path -> pattern tags``. Each tag is
            one of ``exec``, ``eval``, ``__import__``, ``import_module``
            , ``os.system``, ``shell=True``, ``subprocess-string``.
        source_root (Final[Path]): Grouped module constant.
        subprocess_names (Final[frozenset[str]]): Grouped module constant.
        asyncio_shell (Final[str]): Grouped module constant.
        dynamic_module_loaders (Final[frozenset[str]]): Grouped module
            constant.

    """

    allowed: Final[dict[str, frozenset[str]]] = {
        # Opt-in typeshed_client backend (ASTART_TYPESHED_CLIENT); the
        # module name comes from configuration, never from analysed code.
        "src/astart/project/typeshed_client.py": frozenset({"import_module"}),
        # Introspects stdlib ``typing`` members by a fixed literal name.
        "src/astart/rules/recovery.py": frozenset({"import_module"}),
        # Imports ``builtins`` by a fixed literal name for protocol checks.
        "src/astart/rules/protocol_verify.py": frozenset({"__import__"}),
    }
    source_root: Final[Path] = REPO_ROOT / "src" / "astart"

    subprocess_names: Final[frozenset[str]] = frozenset(
        {"run", "Popen", "call", "check_call", "check_output"},
    )
    asyncio_shell: Final[str] = "create_subprocess_shell"
    dynamic_module_loaders: Final[frozenset[str]] = frozenset(
        {"__import__", "import_module"},
    )


def _subprocess_binds(tree: Module) -> tuple[set[str], set[str]]:
    """Collect names bound to subprocess functions in one module.

    Args:
        tree (Module): Parsed module.

    Returns:
        tuple[set[str], set[str]]: ``(bare_names, module_aliases)`` — functions
            imported by
            name and aliases of the ``subprocess`` module itself.

    """
    bare: set[str] = set()
    modules: set[str] = set()
    for node in walk(node=tree):
        if isinstance(node, ImportFrom) and node.module == "subprocess":
            bare.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name in Constants.subprocess_names
            )
        elif isinstance(node, Import):
            modules.update(
                (alias.asname or alias.name).split(sep=".")[0]
                for alias in node.names
                if alias.name == "subprocess"
                or alias.name.startswith("subprocess.")
            )
    return bare, modules


def _string_command(call: Call) -> bool:
    """Tell whether a subprocess-style call passes a plain string command.

    Args:
        call (Call): The call node.

    Returns:
        bool: ``True`` when the first positional argument — or the ``args``
            keyword — is a string constant.

    """
    command: expr | None = call.args[0] if call.args else None
    for keyword in call.keywords:
        if keyword.arg == "args":
            command = keyword.value
    return isinstance(command, Constant) and isinstance(command.value, str)


def _call_parts(func: expr) -> tuple[str, str]:
    """Split a call target into its attribute name and receiver name.

    Args:
        func (expr): The ``func`` expression of a call.

    Returns:
        tuple[str, str]: ``(name, receiver)`` — ``name`` is the called
            attribute or
            bare name, ``receiver`` the bare name it hangs off, if any.

    """
    if isinstance(func, Name):
        return func.id, ""
    if isinstance(func, Attribute):
        receiver: str = func.value.id if isinstance(func.value, Name) else ""
        return func.attr, receiver
    return "", ""


def _call_tag(
    *,
    node: Call,
    bare_subprocess: set[str],
    module_aliases: set[str],
) -> str | None:
    """Classify one call's dangerous pattern, if it has one.

    Args:
        node (Call): The call node.
        bare_subprocess (set[str]): Names bound to subprocess functions.
        module_aliases (set[str]): Aliases of the ``subprocess`` module.

    Returns:
        str | None: The pattern tag, or ``None`` for an ordinary call.

    """
    name, receiver = _call_parts(func=node.func)
    if name in {"exec", "eval"} and isinstance(node.func, Name):
        return name
    if name in Constants.dynamic_module_loaders:
        return name
    if name == "system" and receiver == "os":
        return "os.system"
    if name == Constants.asyncio_shell:
        return "shell=True"
    is_string_command: bool = _string_command(call=node)
    if is_string_command and (
        (isinstance(node.func, Name) and name in bare_subprocess)
        or (
            isinstance(node.func, Attribute)
            and name in Constants.subprocess_names
            and receiver in module_aliases
        )
    ):
        return "subprocess-string"
    return None


def _offenders(path: Path) -> set[str]:
    """Return the dangerous-call pattern tags found in one module.

    Args:
        path (Path): Python source file to scan.

    Returns:
        set[str]: Pattern tags: ``exec``, ``eval``, ``__import__``,
            ``import_module``, ``os.system``, ``shell=True``,
            ``subprocess-string``.

    """
    tree: Module = parse(source=path.read_text(encoding="utf-8"))
    bare_subprocess, module_aliases = _subprocess_binds(tree=tree)
    found: set[str] = set()
    for node in walk(node=tree):
        if not isinstance(node, Call):
            continue
        tag: str | None = _call_tag(
            node=node,
            bare_subprocess=bare_subprocess,
            module_aliases=module_aliases,
        )
        if tag is not None:
            found.add(tag)
        for keyword in node.keywords:
            if (
                keyword.arg == "shell"
                and isinstance(keyword.value, Constant)
                and keyword.value.value is True
            ):
                found.add("shell=True")
    return found


def test_no_unlisted_dynamic_execution() -> None:
    """Every dangerous call under ``src/astart`` is reviewed and listed."""
    violations: list[str] = []
    for path in sorted(Constants.source_root.rglob(pattern="*.py")):
        relative: str = path.relative_to(REPO_ROOT).as_posix()
        tags: set[str] = _offenders(path=path)
        allowed: frozenset[str] = Constants.allowed.get(
            relative,
            frozenset(),
        )
        violations.extend(
            f"{relative}:{tag}" for tag in sorted(tags - allowed)
        )
    expect_equal(actual=violations, expected=[])


def test_allowlist_entries_are_live() -> None:
    """Every allowed entry still exists and still uses its pattern."""
    stale: list[str] = []
    for entry, tags in sorted(Constants.allowed.items()):
        path: Path = REPO_ROOT / entry
        if not path.is_file():
            stale.append(f"{entry}:missing")
            continue
        found: set[str] = _offenders(path=path)
        stale.extend(f"{entry}:{tag}" for tag in sorted(tags - found))
    expect_equal(actual=stale, expected=[])
