from typing import Any

from _typeshed import Incomplete

from ..base_client import FrameworkIntegration

class StarletteIntegration(FrameworkIntegration):
    async def get_state_data(
        self,
        session: dict[str, Any] | None,
        state: str,
    ) -> dict[str, Any]: ...
    async def set_state_data(
        self,
        session: dict[str, Any] | None,
        state: str,
        data: Any,
    ) -> None: ...
    async def clear_state_data(
        self,
        session: dict[str, Any] | None,
        state: str,
    ) -> None: ...
    def update_token(
        self,
        token,
        refresh_token=None,
        access_token=None,
    ) -> None: ...
    @staticmethod
    def load_config(oauth, name, params) -> dict[Incomplete, Incomplete]: ...
