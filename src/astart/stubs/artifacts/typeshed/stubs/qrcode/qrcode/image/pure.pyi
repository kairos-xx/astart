from collections.abc import Generator
from typing import Any, Literal

from _typeshed import SupportsWrite

from . import base

type _Writer = Any

class PyPNGImage(base.BaseImage):
    kind: str
    allowed_kinds: tuple[Literal["PNG"]]
    def new_image(self, **kwargs: Any) -> _Writer: ...
    def get_image(self, **kwargs: Any) -> _Writer: ...
    def drawrect(self, row: int, col: int) -> None: ...
    def save(
        self,
        stream: SupportsWrite[bytes],
        kind: str | None = None,
    ) -> None: ...
    def rows_iter(self) -> Generator[list[int], Any]: ...
    def border_rows_iter(self) -> Generator[list[int], Any]: ...

PymagingImage = PyPNGImage
