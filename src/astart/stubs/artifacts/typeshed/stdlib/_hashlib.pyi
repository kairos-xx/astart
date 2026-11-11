from collections.abc import Callable
from types import ModuleType
from typing import (
    AnyStr,
    Protocol,
    Self,
    final,
    overload,
    type_check_only,
)

from _typeshed import ReadableBuffer
from typing_extensions import disjoint_base

type _DigestMod = str | Callable[[], _HashObject] | ModuleType | None
openssl_md_meth_names: frozenset[str]

@type_check_only
class _HashObject(Protocol):
    @property
    def digest_size(self) -> int: ...
    @property
    def block_size(self) -> int: ...
    @property
    def name(self) -> str: ...
    def copy(self) -> Self: ...
    def digest(self) -> bytes: ...
    def hexdigest(self) -> str: ...
    def update(self, obj: ReadableBuffer, /) -> None: ...

@disjoint_base
class HASH:
    @property
    def digest_size(self) -> int: ...
    @property
    def block_size(self) -> int: ...
    @property
    def name(self) -> str: ...
    def copy(self) -> Self: ...
    def digest(self) -> bytes: ...
    def hexdigest(self) -> str: ...
    def update(self, obj: ReadableBuffer, /) -> None: ...

class UnsupportedDigestmodError(ValueError): ...

class HASHXOF(HASH):
    def digest(self, length: int) -> bytes: ...
    def hexdigest(self, length: int) -> str: ...

@final
class HMAC:
    @property
    def digest_size(self) -> int: ...
    @property
    def block_size(self) -> int: ...
    @property
    def name(self) -> str: ...
    def copy(self) -> Self: ...
    def digest(self) -> bytes: ...
    def hexdigest(self) -> str: ...
    def update(self, msg: ReadableBuffer) -> None: ...

@overload
def compare_digest(a: ReadableBuffer, b: ReadableBuffer, /) -> bool: ...
@overload
def compare_digest(a: AnyStr, b: AnyStr, /) -> bool: ...
def get_fips_mode() -> int: ...
def hmac_new(
    key: ReadableBuffer,
    msg: ReadableBuffer = b"",
    digestmod: _DigestMod = None,
) -> HMAC: ...
def new(
    name: str,
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_md5(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha1(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha224(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha256(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha384(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha512(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha3_224(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha3_256(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha3_384(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_sha3_512(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASH: ...
def openssl_shake_128(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASHXOF: ...
def openssl_shake_256(
    data: ReadableBuffer = b"",
    *,
    usedforsecurity: bool = True,
    string: ReadableBuffer | None = None,
) -> HASHXOF: ...
def hmac_digest(
    key: ReadableBuffer,
    msg: ReadableBuffer,
    digest: str,
) -> bytes: ...
def pbkdf2_hmac(
    hash_name: str,
    password: ReadableBuffer,
    salt: ReadableBuffer,
    iterations: int,
    dklen: int | None = None,
) -> bytes: ...
def scrypt(
    password: ReadableBuffer,
    *,
    salt: ReadableBuffer,
    n: int,
    r: int,
    p: int,
    maxmem: int = 0,
    dklen: int = 64,
) -> bytes: ...
