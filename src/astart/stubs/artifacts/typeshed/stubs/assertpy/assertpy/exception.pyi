from typing import Any, Self

__tracebackhide__: bool

class ExceptionMixin:
    def raises(self, ex: type[BaseException] | BaseException) -> Self: ...
    def when_called_with(
        self,
        *some_args: Any,
        **some_kwargs: Any,
    ) -> Self: ...
