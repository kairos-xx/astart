from collections.abc import Iterable

from _typeshed import SupportsKeysAndGetItem

type _PyIConfig = (
    SupportsKeysAndGetItem[str, bool | str | list[str] | None]
    | Iterable[tuple[str, bool | str | list[str] | None]]
)

def run(
    pyi_args: Iterable[str] | None = None,
    pyi_config: _PyIConfig | None = None,
) -> None: ...
def check_unsafe_privileges() -> None: ...
