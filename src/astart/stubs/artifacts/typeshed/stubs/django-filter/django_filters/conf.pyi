from typing import Any

from _typeshed import Unused

DEFAULTS: dict[str, Any]
DEPRECATED_SETTINGS: list[str]

def is_callable(value: Any) -> bool: ...

class Settings:
    def __getattr__(self, name: str) -> Any: ...
    def get_setting(self, setting: str) -> Any: ...
    def change_setting(
        self,
        setting: str,
        value: Any,
        enter: bool,
        **kwargs: Unused,
    ) -> None: ...

settings: Settings
