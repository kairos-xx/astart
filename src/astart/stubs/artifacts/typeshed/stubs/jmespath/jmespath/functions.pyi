from collections.abc import Callable, Iterable
from typing import Any, NotRequired, TypedDict, TypeVar, type_check_only

TYPES_MAP: dict[str, str]
REVERSE_TYPES_MAP: dict[str, tuple[str, ...]]

@type_check_only
class _Signature(TypedDict):
    types: list[str]
    variadic: NotRequired[bool]

_F = TypeVar("_F", bound=Callable[..., Any])

def signature(*arguments: _Signature) -> Callable[[_F], _F]: ...

class FunctionRegistry(type):
    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
    ) -> None: ...

class Functions(metaclass=FunctionRegistry):
    FUNCTION_TABLE: Any
    def call_function(
        self,
        function_name: str,
        resolved_args: Iterable[Any],
    ) -> Any: ...
