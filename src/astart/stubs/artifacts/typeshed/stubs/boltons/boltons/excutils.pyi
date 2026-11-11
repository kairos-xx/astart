from typing import Any, Self

class ExceptionCauseMixin(Exception):
    cause: Any
    def __new__(cls, *args, **kw) -> Self: ...
    def get_str(self) -> str: ...

class MathError(ExceptionCauseMixin, ValueError): ...

__all__ = ["ExceptionCauseMixin"]
