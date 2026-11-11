from warnings import deprecated

from _typeshed import Incomplete

@deprecated("Please use `JsonWebKey` directly.")
def loads(obj, kid=None): ...
@deprecated("Please use `JsonWebKey` directly.")
def dumps(key, kty=None, **params) -> dict[Incomplete, Incomplete]: ...
