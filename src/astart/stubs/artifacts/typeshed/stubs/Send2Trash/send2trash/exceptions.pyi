from typing import Any

class TrashPermissionError(PermissionError):
    def __init__(self, filename: Any) -> None: ...
