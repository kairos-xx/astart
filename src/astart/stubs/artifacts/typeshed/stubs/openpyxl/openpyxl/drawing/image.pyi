from pathlib import Path
from types import ModuleType
from typing import Any, Literal

from _typeshed import SupportsRead
from openpyxl.drawing.spreadsheet_drawing import _AnchorBase

type _PILImageImage = Any
type _PILImageFilePath = str | bytes | Path | SupportsRead[bytes]
PILImage: ModuleType | Literal[False]

class Image:
    anchor: str | _AnchorBase
    ref: _PILImageImage | _PILImageFilePath
    width: int
    height: int
    format: str
    def __init__(self, img: _PILImageImage | _PILImageFilePath) -> None: ...
    @property
    def path(self) -> str: ...
