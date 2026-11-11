from collections.abc import Mapping
from typing import Any, Final

__version__: Final[str]

def dictformat(
    _format: str,
    L: Mapping[str, object] | None = {},
    G: dict[str, Any] | None = {},
) -> str: ...
def magicformat(format: str) -> str: ...
