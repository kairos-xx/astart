from typing import Literal

from _typeshed import Incomplete

def fp_str(*a) -> str: ...
def unicode2T1(utext, fonts) -> list[tuple[Incomplete, Incomplete]]: ...
def instanceStringWidthT1(
    self,
    text: str,
    size: float,
    encoding: str = "utf8",
) -> float: ...
def instanceStringWidthTTF(
    self,
    text: str,
    size: float,
    encoding: str = "utf8",
) -> float: ...
def hex32(i) -> str: ...
def add32(x: int, y: int) -> int: ...
def calcChecksum(data: str | bytes) -> int: ...
def escapePDF(s) -> str: ...
def asciiBase85Encode(input: str) -> str: ...
def asciiBase85Decode(input) -> bytes: ...
def sameFrag(f, g) -> bool | Literal[0]: ...

__all__ = [
    "add32",
    "asciiBase85Decode",
    "asciiBase85Encode",
    "calcChecksum",
    "escapePDF",
    "fp_str",
    "hex32",
    "instanceStringWidthT1",
    "instanceStringWidthTTF",
    "sameFrag",
    "unicode2T1",
]
