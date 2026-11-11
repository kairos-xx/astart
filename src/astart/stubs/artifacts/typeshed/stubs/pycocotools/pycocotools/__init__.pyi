from typing import TypedDict, type_check_only

@type_check_only
class _EncodedRLE(TypedDict):
    size: list[int]
    counts: str | bytes
