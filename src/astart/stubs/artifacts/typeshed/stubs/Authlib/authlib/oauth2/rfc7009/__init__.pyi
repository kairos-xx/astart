from .parameters import (
    prepare_revoke_token_request as prepare_revoke_token_request,
)
from .revocation import RevocationEndpoint as RevocationEndpoint

__all__ = ["RevocationEndpoint", "prepare_revoke_token_request"]
