from collections.abc import Callable

from _typeshed import Incomplete

def register_temporary_credential_hooks(
    authorization_server,
    cache,
    key_prefix: str = "temporary_credential:",
) -> None: ...
def create_exists_nonce_func(
    cache,
    key_prefix="nonce:",
    expires=86400,
) -> Callable[
    [Incomplete, Incomplete, Incomplete, Incomplete],
    Incomplete,
]: ...
def register_nonce_hooks(
    authorization_server,
    cache,
    key_prefix: str = "nonce:",
    expires=86400,
) -> None: ...
