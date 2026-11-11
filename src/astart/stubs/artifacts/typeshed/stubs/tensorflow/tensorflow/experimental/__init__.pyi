from abc import ABC

from _typeshed import Incomplete

class Optional[T_co](ABC):
    def __getattr__(self, name: str) -> Incomplete: ...

def __getattr__(name: str): ...
