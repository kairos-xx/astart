import abc

from _typeshed import Incomplete

class AbstractType(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def encode(self, value): ...
    @abc.abstractmethod
    def decode(self, data): ...
    repr: Incomplete
