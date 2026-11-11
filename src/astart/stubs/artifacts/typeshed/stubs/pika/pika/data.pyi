from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

type _Value = (
    str
    | bytes
    | bool
    | int
    | Decimal
    | datetime
    | _ArgumentMapping
    | list[_Value]
    | None
)
type _ArgumentMapping = Mapping[str, _Value]

def encode_short_string(pieces: list[bytes], value: str | bytes) -> int: ...
def decode_short_string(encoded: bytes, offset: int) -> tuple[str, int]: ...
def encode_table(pieces: list[bytes], table: _ArgumentMapping) -> int: ...
def encode_value(pieces: list[bytes], value: _Value) -> int: ...
def decode_table(
    encoded: bytes,
    offset: int,
) -> tuple[dict[str, _Value], int]: ...
def decode_value(encoded: bytes, offset: int) -> tuple[_Value, int]: ...
