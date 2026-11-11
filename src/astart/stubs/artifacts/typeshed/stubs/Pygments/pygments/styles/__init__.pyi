from collections.abc import Iterator, Mapping

from pygments.style import Style
from pygments.util import ClassNotFound as ClassNotFound

STYLE_MAP: Mapping[str, str]

def get_style_by_name(name) -> type[Style]: ...
def get_all_styles() -> Iterator[str]: ...
def __getattr__(name: str): ...
