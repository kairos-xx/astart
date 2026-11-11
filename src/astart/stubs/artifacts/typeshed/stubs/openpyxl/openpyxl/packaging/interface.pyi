from abc import ABC, abstractmethod

class ISerialisableFile(ABC):
    @property
    @abstractmethod
    def id(self) -> str | int | None: ...
