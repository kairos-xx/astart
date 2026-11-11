from pathlib import Path
from typing import NotRequired, TypedDict, type_check_only

type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None

@type_check_only
class ContainerWeightDevice(TypedDict):
    Path: Path
    Weight: int

@type_check_only
class _WaitErrorDetails(TypedDict):
    Message: str

@type_check_only
class WaitContainerResponse(TypedDict):
    StatusCode: int
    Error: NotRequired[_WaitErrorDetails]
