from typing import Any

from _typeshed import Incomplete

from ..xml._functions_overloads import _lxml_Element, _ParentElement

type _RootElement = _ParentElement[Any] | _lxml_Element
vmlns: str
officens: str
excelns: str

class ShapeWriter:
    vml: Incomplete
    vml_path: Incomplete
    comments: Incomplete
    def __init__(self, comments) -> None: ...
    def add_comment_shapetype(self, root: _RootElement) -> None: ...
    def add_comment_shape(
        self,
        root: _RootElement,
        idx,
        coord,
        height,
        width,
    ) -> None: ...
    def write(self, root: _RootElement | None) -> str: ...
