from networkx.utils.backends import _dispatchable

__all__ = ["parse_leda", "read_leda"]

@_dispatchable
def read_leda(path, encoding: str = "UTF-8"): ...
@_dispatchable
def parse_leda(lines): ...
