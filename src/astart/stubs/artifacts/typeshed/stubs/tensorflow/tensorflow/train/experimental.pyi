import abc
from typing import Self

from tensorflow.python.trackable.base import Trackable

class PythonState(Trackable, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def serialize(self) -> str: ...
    @abc.abstractmethod
    def deserialize(self, string_value: str) -> Self: ...

def __getattr__(name: str): ...
