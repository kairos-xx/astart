from typing import ClassVar, Literal

from _typeshed import ConvertibleToFloat, Unused
from openpyxl.chart.data_source import NumDataSource
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.descriptors.base import Alias, Typed, _ConvertibleToBool
from openpyxl.descriptors.excel import ExtensionList
from openpyxl.descriptors.nested import (
    NestedBool,
    NestedFloat,
    NestedNoneSet,
    NestedSet,
    _NestedNoneSetParam,
)
from openpyxl.descriptors.serialisable import Serialisable

from ..xml._functions_overloads import _HasTagAndGet

type _ErrorBarsErrBarType = Literal["both", "minus", "plus"]
type _ErrorBarsErrValType = Literal[
    "cust",
    "fixedVal",
    "percentage",
    "stdDev",
    "stdErr",
]
type _ErrorBarsErrDir = Literal["x", "y"]

class ErrorBars(Serialisable):
    tagname: ClassVar[str]
    errDir: NestedNoneSet[_ErrorBarsErrDir]
    direction: Alias
    errBarType: NestedSet[_ErrorBarsErrBarType]
    style: Alias
    errValType: NestedSet[_ErrorBarsErrValType]
    size: Alias
    noEndCap: NestedBool[Literal[True]]
    plus: Typed[NumDataSource, Literal[True]]
    minus: Typed[NumDataSource, Literal[True]]
    val: NestedFloat[Literal[True]]
    spPr: Typed[GraphicalProperties, Literal[True]]
    graphicalProperties: Alias
    extLst: Typed[ExtensionList, Literal[True]]
    __elements__: ClassVar[tuple[str, ...]]
    def __init__(
        self,
        errDir: _NestedNoneSetParam[_ErrorBarsErrDir] = None,
        errBarType: _HasTagAndGet[_ErrorBarsErrBarType]
        | _ErrorBarsErrBarType = "both",
        errValType: _HasTagAndGet[_ErrorBarsErrValType]
        | _ErrorBarsErrValType = "fixedVal",
        noEndCap: _HasTagAndGet[_ConvertibleToBool | None]
        | _ConvertibleToBool
        | None = None,
        plus: NumDataSource | None = None,
        minus: NumDataSource | None = None,
        val: _HasTagAndGet[ConvertibleToFloat | None]
        | ConvertibleToFloat
        | None = None,
        spPr: GraphicalProperties | None = None,
        extLst: Unused = None,
    ) -> None: ...
