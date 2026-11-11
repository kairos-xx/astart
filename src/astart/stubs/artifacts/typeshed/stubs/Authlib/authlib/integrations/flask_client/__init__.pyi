from _typeshed import Incomplete

from ..base_client import BaseOAuth
from ..base_client import OAuthError as OAuthError
from .apps import FlaskOAuth1App as FlaskOAuth1App
from .apps import FlaskOAuth2App as FlaskOAuth2App
from .integration import FlaskIntegration as FlaskIntegration
from .integration import token_update as token_update

class OAuth(BaseOAuth):
    oauth1_client_cls = FlaskOAuth1App
    oauth2_client_cls = FlaskOAuth2App
    framework_integration_cls = FlaskIntegration
    app: Incomplete
    def __init__(
        self,
        app=None,
        cache=None,
        fetch_token=None,
        update_token=None,
    ) -> None: ...
    cache: Incomplete
    fetch_token: Incomplete
    update_token: Incomplete
    def init_app(
        self,
        app,
        cache=None,
        fetch_token=None,
        update_token=None,
    ): ...
    def create_client(self, name): ...
    def register(self, name, overwrite=False, **kwargs): ...

__all__ = [
    "FlaskIntegration",
    "FlaskOAuth1App",
    "FlaskOAuth2App",
    "OAuth",
    "OAuthError",
    "token_update",
]
