from typing import Any

from .backends.base import Key

def encrypt(
    plaintext: str | bytes,
    key: str | bytes | dict[str, Any] | Key,
    encryption: str = "A256GCM",
    algorithm: str = "dir",
    zip: str | None = None,
    cty: str | None = None,
    kid: str | None = None,
) -> bytes: ...
def decrypt(
    jwe_str: str | bytes,
    key: str | bytes | dict[str, Any] | Key,
) -> bytes | None: ...
def get_unverified_header(jwe_str: str | bytes | None) -> dict[str, Any]: ...
