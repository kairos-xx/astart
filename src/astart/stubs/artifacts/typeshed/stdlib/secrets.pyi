from hmac import compare_digest as compare_digest
from random import SystemRandom as SystemRandom
from typing import Final, TypeVar

from _typeshed import SupportsLenAndGetItem

__all__ = [
    "SystemRandom",
    "choice",
    "compare_digest",
    "randbelow",
    "randbits",
    "token_bytes",
    "token_hex",
    "token_urlsafe",
]
_T = TypeVar("_T")
DEFAULT_ENTROPY: Final[int]

def randbelow(exclusive_upper_bound: int) -> int: ...
def randbits(k: int) -> int: ...
def choice[T](seq: SupportsLenAndGetItem[_T]) -> _T: ...
def token_bytes(nbytes: int | None = None) -> bytes: ...
def token_hex(nbytes: int | None = None) -> str: ...
def token_urlsafe(nbytes: int | None = None) -> str: ...
