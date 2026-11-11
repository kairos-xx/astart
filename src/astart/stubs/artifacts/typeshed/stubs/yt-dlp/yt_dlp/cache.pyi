from typing import Any, Literal

from .YoutubeDL import YoutubeDL

class Cache:
    def __init__(self, ydl: YoutubeDL) -> None: ...
    @property
    def enabled(self) -> bool: ...
    def store(
        self,
        section: str,
        key: str,
        data: Any,
        dtype: Literal["json"] = "json",
    ) -> None: ...
    def load(
        self,
        section: str,
        key: str,
        dtype: Literal["json"] = "json",
        default: Any = None,
        *,
        min_ver: str | None = None,
    ) -> Any: ...
    def remove(self) -> None: ...
