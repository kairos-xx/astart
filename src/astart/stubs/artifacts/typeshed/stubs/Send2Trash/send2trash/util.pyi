from typing import Any

from _typeshed import StrOrBytesPath

def preprocess_paths(
    paths: list[Any] | StrOrBytesPath,
) -> list[str | bytes]: ...
