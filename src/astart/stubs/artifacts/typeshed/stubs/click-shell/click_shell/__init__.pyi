from typing import Final

from .core import Shell as Shell
from .core import make_click_shell as make_click_shell
from .decorators import shell as shell

__all__ = ["Shell", "__version__", "make_click_shell", "shell"]
__version__: Final[str]
