from ..base_client import BaseOAuth
from ..base_client import OAuthError as OAuthError
from .apps import DjangoOAuth1App as DjangoOAuth1App
from .apps import DjangoOAuth2App as DjangoOAuth2App
from .integration import DjangoIntegration as DjangoIntegration
from .integration import token_update as token_update

class OAuth(BaseOAuth):
    oauth1_client_cls = DjangoOAuth1App
    oauth2_client_cls = DjangoOAuth2App
    framework_integration_cls = DjangoIntegration

__all__ = [
    "DjangoIntegration",
    "DjangoOAuth1App",
    "DjangoOAuth2App",
    "OAuth",
    "OAuthError",
    "token_update",
]
