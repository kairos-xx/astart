from collections.abc import Container, Iterable, Mapping
from typing import Any

from .backends.base import Key

def sign(
    payload: bytes | Mapping[str, Any],
    key: str | bytes | dict[str, Any] | Key,
    headers: Mapping[str, Any] | None = None,
    algorithm: str = "HS256",
) -> str: ...
def verify(
    token: str | bytes,
    key: str | bytes | Mapping[str, Any] | Key | Iterable[str],
    algorithms: str | Container[str] | None,
    verify: bool = True,
) -> bytes: ...
def get_unverified_header(token: str | bytes) -> dict[str, Any]: ...
def get_unverified_headers(token: str | bytes) -> dict[str, Any]: ...
def get_unverified_claims(token: str | bytes) -> bytes: ...
