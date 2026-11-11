from asyncio.events import AbstractEventLoop
from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from typing import ParamSpec, TypeVar

from .case import TestCase

_T = TypeVar("_T")
_P = ParamSpec("_P")

class IsolatedAsyncioTestCase(TestCase):
    loop_factory: Callable[[], AbstractEventLoop] | None = None
    async def asyncSetUp(self) -> None: ...
    async def asyncTearDown(self) -> None: ...
    def addAsyncCleanup(
        self,
        func: Callable[_P, Awaitable[object]],
        /,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> None: ...
    async def enterAsyncContext(
        self,
        cm: AbstractAsyncContextManager[_T],
    ) -> _T: ...
    def __del__(self) -> None: ...
