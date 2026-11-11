from collections.abc import Iterable, Sequence
from typing import Final, TypeVar

_T = TypeVar("_T")
_K = TypeVar("_K")
_V = TypeVar("_V")
__all__ = [
    "compiler_fixup",
    "customize_compiler",
    "customize_config_vars",
    "get_platform_osx",
]
_UNIVERSAL_CONFIG_VARS: Final[tuple[str, ...]]
_COMPILER_CONFIG_VARS: Final[tuple[str, ...]]
_INITPRE: Final[str]

def _find_executable(
    executable: str,
    path: str | None = None,
) -> str | None: ...
def _read_output(
    commandstring: str,
    capture_stderr: bool = False,
) -> str | None: ...
def _find_build_tool(toolname: str) -> str: ...

_SYSTEM_VERSION: Final[str | None]

def _get_system_version() -> str: ...
def _remove_original_values(_config_vars: dict[str, str]) -> None: ...
def _save_modified_value(
    _config_vars: dict[str, str],
    cv: str,
    newvalue: str,
) -> None: ...
def _supports_universal_builds() -> bool: ...
def _find_appropriate_compiler(
    _config_vars: dict[str, str],
) -> dict[str, str]: ...
def _remove_universal_flags(
    _config_vars: dict[str, str],
) -> dict[str, str]: ...
def _remove_unsupported_archs(
    _config_vars: dict[str, str],
) -> dict[str, str]: ...
def _override_all_archs(_config_vars: dict[str, str]) -> dict[str, str]: ...
def _check_for_unavailable_sdk(
    _config_vars: dict[str, str],
) -> dict[str, str]: ...
def compiler_fixup(
    compiler_so: Iterable[str],
    cc_args: Sequence[str],
) -> list[str]: ...
def customize_config_vars(_config_vars: dict[str, str]) -> dict[str, str]: ...
def customize_compiler(_config_vars: dict[str, str]) -> dict[str, str]: ...
def get_platform_osx[T, K, V](
    _config_vars: dict[str, str],
    osname: _T,
    release: _K,
    machine: _V,
) -> tuple[str | _T, str | _K, str | _V]: ...
