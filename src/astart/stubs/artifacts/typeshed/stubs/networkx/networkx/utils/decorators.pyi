from collections.abc import Callable
from typing import NamedTuple

from _typeshed import Incomplete

__all__ = [
    "argmap",
    "nodes_or_number",
    "not_implemented_for",
    "np_random_state",
    "open_file",
    "py_random_state",
]

def not_implemented_for(*graph_types): ...
def open_file(path_arg, mode: str = "r"): ...
def nodes_or_number(which_args): ...
def np_random_state(random_state_argument): ...
def py_random_state(random_state_argument): ...

class argmap:
    def __init__(self, func, *args, try_finally: bool = False) -> None: ...
    def __call__(self, f) -> Callable[..., Incomplete]: ...
    def compile(self, f) -> Callable[..., Incomplete]: ...
    def assemble(self, f): ...
    @classmethod
    def signature(cls, f): ...
    class Signature(NamedTuple):
        name: Incomplete
        signature: Incomplete
        def_sig: Incomplete
        call_sig: Incomplete
        names: Incomplete
        n_positional: Incomplete
        args: Incomplete
        kwargs: Incomplete
