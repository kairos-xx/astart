from typing import Any, ClassVar, Literal, Self, TypeVar, overload

from _typeshed import Incomplete
from reportlab.lib.colors import Color

type _AlignmentEnum = Literal[0, 1, 2, 4]
type _AlignmentStr = Literal["left", "center", "centre", "right", "justify"]
type _Alignment = _AlignmentEnum | _AlignmentStr
_T = TypeVar("_T")

class PropertySet:
    defaults: ClassVar[dict[str, Any]]
    name: str
    parent: PropertySet | None
    def __init__(
        self,
        name: str,
        parent: PropertySet | None = None,
        **kw: Any,
    ) -> None: ...
    def refresh(self) -> None: ...
    def listAttrs(self, indent: str = "") -> None: ...
    def clone(
        self,
        name: str,
        parent: PropertySet | None = None,
        **kwds: Any,
    ) -> Self: ...
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...

class ParagraphStyle(PropertySet):
    fontName: str
    fontSize: float
    leading: float
    leftIndent: float
    rightIndent: float
    firstLineIndent: float
    alignment: _Alignment
    spaceBefore: float
    spaceAfter: float
    bulletFontName: str
    bulletFontSize: float
    bulletIndent: float
    textColor: Color
    backColor: Color | None
    wordWrap: Incomplete | None
    borderWidth: float
    borderPadding: float
    borderColor: Color | None
    borderRadius: float | None
    allowWidows: Incomplete
    allowOrphans: Incomplete
    textTransform: Incomplete | None
    endDots: Incomplete | None
    splitLongWords: Incomplete
    underlineWidth: float
    bulletAnchor: Literal["start", "middle", "end"] | float
    justifyLastLine: Incomplete
    justifyBreaks: Incomplete
    spaceShrinkage: float
    strikeWidth: float
    underlineOffset: float
    underlineGap: float
    strikeOffset: float
    strikeGap: float
    linkUnderline: Incomplete
    underlineColor: Color | None
    strikeColor: Color | None
    hyphenationLang: str
    embeddedHyphenation: Incomplete
    uriWasteReduce: float
    def __init__(
        self,
        name: str,
        parent: PropertySet | None = None,
        *,
        fontName: str = ...,
        fontSize: float = ...,
        leading: float = ...,
        leftIndent: float = ...,
        rightIndent: float = ...,
        firstLineIndent: float = ...,
        alignment: _Alignment = ...,
        spaceBefore: float = ...,
        spaceAfter: float = ...,
        bulletFontName: str = ...,
        bulletFontSize: float = ...,
        bulletIndent: float = ...,
        textColor: Color = ...,
        backColor: Color | None = ...,
        wordWrap: Incomplete | None = ...,
        borderWidth: float = ...,
        borderPadding: float = ...,
        borderColor: Color | None = ...,
        borderRadius: float | None = ...,
        allowWidows=...,
        allowOrphans=...,
        textTransform: Incomplete | None = ...,
        endDots: Incomplete | None = ...,
        splitLongWords=...,
        underlineWidth: float = ...,
        bulletAnchor: Literal["start", "middle", "end"] | float = ...,
        justifyLastLine=...,
        justifyBreaks=...,
        spaceShrinkage: float = ...,
        strikeWidth: float = ...,
        underlineOffset: float = ...,
        underlineGap: float = ...,
        strikeOffset: float = ...,
        strikeGap: float = ...,
        linkUnderline=...,
        underlineColor: Color | None = ...,
        strikeColor: Color | None = ...,
        hyphenationLang: str = ...,
        embeddedHyphenation=...,
        uriWasteReduce: float = ...,
        **kw: Any,
    ) -> None: ...

def str2alignment(
    v: _AlignmentStr,
    __map__: dict[_AlignmentStr, _AlignmentEnum] = {
        "centre": 1,
        "center": 1,
        "left": 0,
        "right": 2,
        "justify": 4,
    },
) -> _AlignmentEnum: ...

class LineStyle(PropertySet):
    width: float
    color: Color
    def prepareCanvas(self, canvas) -> None: ...
    def __init__(
        self,
        name: str,
        parent: PropertySet | None = None,
        *,
        width: float = ...,
        color: Color = ...,
        **kw: Any,
    ) -> None: ...

class ListStyle(PropertySet):
    leftIndent: float
    rightIndent: float
    bulletAlign: _Alignment
    bulletType: str
    bulletColor: Color
    bulletFontName: str
    bulletFontSize: float
    bulletOffsetY: float
    bulletDedent: Incomplete
    bulletDir: Incomplete
    bulletFormat: Incomplete | None
    start: Incomplete | None
    def __init__(
        self,
        name: str,
        parent: PropertySet | None = None,
        *,
        leftIndent: float = ...,
        rightIndent: float = ...,
        bulletAlign: _Alignment = ...,
        bulletType: str = ...,
        bulletColor: Color = ...,
        bulletFontName: str = ...,
        bulletFontSize: float = ...,
        bulletOffsetY: float = ...,
        bulletDedent=...,
        bulletDir=...,
        bulletFormat: Incomplete | None = ...,
        start: Incomplete | None = ...,
        **kw: Any,
    ) -> None: ...

class StyleSheet1:
    byName: dict[str, PropertySet]
    byAlias: dict[str, PropertySet]
    def __init__(self) -> None: ...
    def __getitem__(self, key: str) -> PropertySet: ...
    @overload
    def get(self, key: str) -> PropertySet: ...
    @overload
    def get(self, key: str, default: _T) -> PropertySet | _T: ...
    def __contains__(self, key: str) -> bool: ...
    def has_key(self, key: str) -> bool: ...
    def add(self, style: PropertySet, alias: str | None = None) -> None: ...
    def list(self) -> None: ...

def getSampleStyleSheet() -> StyleSheet1: ...

__all__ = (
    "LineStyle",
    "ListStyle",
    "ParagraphStyle",
    "PropertySet",
    "StyleSheet1",
    "getSampleStyleSheet",
    "str2alignment",
)
