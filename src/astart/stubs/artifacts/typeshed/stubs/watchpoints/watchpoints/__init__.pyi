from collections.abc import Callable
from typing import Final, LiteralString, Unpack

from .watch import Watch

__version__: Final[LiteralString]
watch: Watch
unwatch: Final[Callable[[Unpack[tuple[object, ...]]], None]]
