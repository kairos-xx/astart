from typing import Any

from _typeshed import StrOrBytesPath

from .exceptions import TrashPermissionError as TrashPermissionError

def send2trash(paths: list[Any] | StrOrBytesPath) -> None: ...
