from types import FrameType
from typing import Any

from _typeshed import StrOrBytesPath

from .tasks import Task

def _task_repr_info(task: Task[Any]) -> list[str]: ...
def _task_repr(task: Task[Any]) -> str: ...
def _task_get_stack(task: Task[Any], limit: int | None) -> list[FrameType]: ...
def _task_print_stack(
    task: Task[Any],
    limit: int | None,
    file: StrOrBytesPath,
) -> None: ...
