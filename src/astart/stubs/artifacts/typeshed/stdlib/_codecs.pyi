import codecs
import sys
from collections.abc import Callable
from typing import Literal, final, overload, type_check_only

from _typeshed import ReadableBuffer

@final
@type_check_only
class _EncodingMap:
    def size(self) -> int: ...

type _CharMap = dict[int, int] | _EncodingMap
type _Handler = Callable[[UnicodeError], tuple[str | bytes, int]]
type _SearchFunction = Callable[[str], codecs.CodecInfo | None]

def register(search_function: _SearchFunction, /) -> None: ...
def unregister(search_function: _SearchFunction, /) -> None: ...
def register_error(errors: str, handler: _Handler, /) -> None: ...
def lookup_error(name: str, /) -> _Handler: ...

type _BytesToBytesEncoding = Literal[
    "base64",
    "base_64",
    "base64_codec",
    "bz2",
    "bz2_codec",
    "hex",
    "hex_codec",
    "quopri",
    "quotedprintable",
    "quoted_printable",
    "quopri_codec",
    "uu",
    "uu_codec",
    "zip",
    "zlib",
    "zlib_codec",
]
type _StrToStrEncoding = Literal["rot13", "rot_13"]

@overload
def encode(
    obj: ReadableBuffer,
    encoding: _BytesToBytesEncoding,
    errors: str = "strict",
) -> bytes: ...
@overload
def encode(
    obj: str,
    encoding: _StrToStrEncoding,
    errors: str = "strict",
) -> str: ...
@overload
def encode(
    obj: str,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> bytes: ...
@overload
def decode(
    obj: ReadableBuffer,
    encoding: _BytesToBytesEncoding,
    errors: str = "strict",
) -> bytes: ...
@overload
def decode(
    obj: str,
    encoding: _StrToStrEncoding,
    errors: str = "strict",
) -> str: ...
@overload
def decode(
    obj: str,
    encoding: Literal[
        "unicode_escape",
        "unicode-escape",
        "raw_unicode_escape",
        "raw-unicode-escape",
    ],
    errors: str = "strict",
) -> str: ...
@overload
def decode(
    obj: str,
    encoding: Literal["hex", "hex_codec"],
    errors: str = "strict",
) -> bytes: ...
@overload
def decode(
    obj: ReadableBuffer,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> str: ...
def lookup(encoding: str, /) -> codecs.CodecInfo: ...
def charmap_build(map: str, /) -> _CharMap: ...
def ascii_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    /,
) -> tuple[str, int]: ...
def ascii_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def charmap_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    mapping: _CharMap | None = None,
    /,
) -> tuple[str, int]: ...
def charmap_encode(
    str: str,
    errors: str | None = None,
    mapping: _CharMap | None = None,
    /,
) -> tuple[bytes, int]: ...
def escape_decode(
    data: str | ReadableBuffer,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def escape_encode(
    data: bytes,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def latin_1_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    /,
) -> tuple[str, int]: ...
def latin_1_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def raw_unicode_escape_decode(
    data: str | ReadableBuffer,
    errors: str | None = None,
    final: bool = True,
    /,
) -> tuple[str, int]: ...
def raw_unicode_escape_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def readbuffer_encode(
    data: str | ReadableBuffer,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def unicode_escape_decode(
    data: str | ReadableBuffer,
    errors: str | None = None,
    final: bool = True,
    /,
) -> tuple[str, int]: ...
def unicode_escape_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_16_be_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_16_be_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_16_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_16_encode(
    str: str,
    errors: str | None = None,
    byteorder: int = 0,
    /,
) -> tuple[bytes, int]: ...
def utf_16_ex_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    byteorder: int = 0,
    final: bool = False,
    /,
) -> tuple[str, int, int]: ...
def utf_16_le_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_16_le_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_32_be_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_32_be_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_32_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_32_encode(
    str: str,
    errors: str | None = None,
    byteorder: int = 0,
    /,
) -> tuple[bytes, int]: ...
def utf_32_ex_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    byteorder: int = 0,
    final: bool = False,
    /,
) -> tuple[str, int, int]: ...
def utf_32_le_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_32_le_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_7_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_7_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...
def utf_8_decode(
    data: ReadableBuffer,
    errors: str | None = None,
    final: bool = False,
    /,
) -> tuple[str, int]: ...
def utf_8_encode(
    str: str,
    errors: str | None = None,
    /,
) -> tuple[bytes, int]: ...

if sys.platform == "win32":
    def mbcs_decode(
        data: ReadableBuffer,
        errors: str | None = None,
        final: bool = False,
        /,
    ) -> tuple[str, int]: ...
    def mbcs_encode(
        str: str,
        errors: str | None = None,
        /,
    ) -> tuple[bytes, int]: ...
    def code_page_decode(
        codepage: int,
        data: ReadableBuffer,
        errors: str | None = None,
        final: bool = False,
        /,
    ) -> tuple[str, int]: ...
    def code_page_encode(
        code_page: int,
        str: str,
        errors: str | None = None,
        /,
    ) -> tuple[bytes, int]: ...
    def oem_decode(
        data: ReadableBuffer,
        errors: str | None = None,
        final: bool = False,
        /,
    ) -> tuple[str, int]: ...
    def oem_encode(
        str: str,
        errors: str | None = None,
        /,
    ) -> tuple[bytes, int]: ...
