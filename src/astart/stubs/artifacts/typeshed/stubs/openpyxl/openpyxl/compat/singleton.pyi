from typing import Any, overload

class Singleton(type):
    @overload
    def __init__(cls, o: object, /) -> None: ...
    @overload
    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        dict: dict[str, Any],
        /,
        **kwds: Any,
    ) -> None: ...
    def __call__(cls, *args: Any, **kwds: Any) -> Any: ...

class Cached(type):
    @overload
    def __init__(cls, o: object, /) -> None: ...
    @overload
    def __init__(
        cls,
        name: str,
        bases: tuple[type, ...],
        dict: dict[str, Any],
        /,
        **kwds: Any,
    ) -> None: ...
    def __call__(cls, *args: Any) -> Any: ...
