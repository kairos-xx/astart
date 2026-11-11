from .errors import InsufficientScopeError as InsufficientScopeError
from .errors import InvalidTokenError as InvalidTokenError
from .parameters import add_bearer_token as add_bearer_token
from .token import BearerTokenGenerator as BearerTokenGenerator
from .validator import BearerTokenValidator as BearerTokenValidator

__all__ = [
    "BearerToken",
    "BearerTokenGenerator",
    "BearerTokenValidator",
    "InsufficientScopeError",
    "InvalidTokenError",
    "add_bearer_token",
]
BearerToken = BearerTokenGenerator
