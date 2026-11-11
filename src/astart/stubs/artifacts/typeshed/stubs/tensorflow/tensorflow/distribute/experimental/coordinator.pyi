from typing import TypeVar

from tensorflow._aliases import AnyArray

_Value_co = TypeVar("_Value_co", covariant=True)

class RemoteValue[Value_co]:
    def fetch(self) -> AnyArray: ...
    def get(self) -> _Value_co: ...

def __getattr__(name: str): ...
