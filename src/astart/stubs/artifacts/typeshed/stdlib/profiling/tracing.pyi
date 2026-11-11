from cProfile import Profile as Profile
from cProfile import run as run
from cProfile import runctx as runctx
from types import CodeType

__all__ = ("Profile", "run", "runctx")
type _Label = tuple[str, int, str]

def label(code: str | CodeType) -> _Label: ...
