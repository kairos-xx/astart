from _typeshed import Incomplete

from ..base_client import BaseOAuth
from ..base_client import OAuthError as OAuthError
from .apps import StarletteOAuth1App as StarletteOAuth1App
from .apps import StarletteOAuth2App as StarletteOAuth2App
from .integration import StarletteIntegration as StarletteIntegration

class OAuth(BaseOAuth):
    oauth1_client_cls = StarletteOAuth1App
    oauth2_client_cls = StarletteOAuth2App
    framework_integration_cls = StarletteIntegration
    config: Incomplete
    def __init__(
        self,
        config=None,
        cache=None,
        fetch_token=None,
        update_token=None,
    ) -> None: ...

__all__ = [
    "OAuth",
    "OAuthError",
    "StarletteIntegration",
    "StarletteOAuth1App",
    "StarletteOAuth2App",
]
