from typing import Literal, TypedDict, type_check_only

from _typeshed import Unused

@type_check_only
class _ContinueRequestResult(TypedDict):
    allThreadsContinued: bool

type _Granularity = Literal["statement", "instruction"]

def next(
    *,
    threadId: int,
    singleThread: bool = False,
    granularity: _Granularity = "statement",
    **args: Unused,
) -> None: ...
def step_in(
    *,
    threadId: int,
    singleThread: bool = False,
    granularity: _Granularity = "statement",
    **args: Unused,
) -> None: ...
def step_out(*, threadId: int, singleThread: bool = False, **args: Unused): ...
def continue_request(
    *,
    threadId: int,
    singleThread: bool = False,
    **args: Unused,
) -> _ContinueRequestResult: ...
