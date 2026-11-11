from abc import abstractmethod
from collections.abc import Collection, Iterable, Sequence
from typing import Any, Literal, NamedTuple, overload

from _typeshed import Incomplete
from reportlab.lib.colors import Color
from reportlab.lib.styles import PropertySet
from reportlab.lib.utils import _UNSET_
from reportlab.platypus.flowables import Flowable, _HAlignment, _VAlignment

__all__ = ("CellStyle", "LongTable", "Table", "TableStyle")
type _Color = (
    Color
    | list[float]
    | tuple[float, float, float, float]
    | tuple[float, float, float]
    | str
    | int
)
type _SpecialRow = Literal[
    "splitfirst",
    "splitlast",
    "inrowsplitstart",
    "inrowsplitend",
]
type _TableSectionCommand = tuple[
    str,
    tuple[int | _SpecialRow, int],
    tuple[int, int],
    *tuple[Any, ...],
]
type _CornerRadii = tuple[float, float, float, float] | list[float]
type _RoundedCornersTableCommand = tuple[
    Literal["ROUNDEDCORNERS"],
    _CornerRadii | None,
]
type _TableCommand = _TableSectionCommand | _RoundedCornersTableCommand

class CellStyle(PropertySet):
    name: str
    fontname: str
    fontsize: float
    leading: float
    leftPadding: float
    rightPadding: float
    topPadding: float
    bottomPadding: float
    firstLineIndent: float
    color: _Color
    alignment: Literal["LEFT", "CENTER", "CENTRE", "RIGHT", "DECIMAL"]
    background: _Color
    valign: Literal["TOP", "MIDDLE", "BOTTOM"]
    href: str | None
    direction: str | None
    shaping: Incomplete | None
    destination: Incomplete | None
    def __init__(self, name: str, parent: CellStyle | None = None) -> None: ...
    def copy(self, result: CellStyle | None = None) -> CellStyle: ...

class TableStyle:
    def __init__(
        self,
        cmds: Iterable[_TableCommand] | None = None,
        parent: TableStyle | None = None,
        **kw,
    ) -> None: ...
    @overload
    def add(self, *cmd: *_TableSectionCommand) -> None: ...
    @overload
    def add(self, *cmd: *_RoundedCornersTableCommand) -> None: ...
    def getCommands(self) -> list[_TableCommand]: ...

class ShadowStyle(NamedTuple):
    dx: int | Incomplete = 10
    dy: int | Incomplete = -10
    color0: _Color = "grey"
    color1: _Color = "white"
    nshades: int = 30

class Table(Flowable):
    ident: str | None
    repeatRows: int
    repeatCols: int
    splitByRow: int
    splitInRow: int
    spaceBefore: float
    spaceAfter: float
    def __init__(
        self,
        data: Sequence[list[Any] | tuple[Any, ...]],
        colWidths: Sequence[float | str | None] | float | str | None = None,
        rowHeights: Sequence[float | None] | float | None = None,
        style: TableStyle | Iterable[_TableCommand] | None = None,
        repeatRows: int | Collection[int] = 0,
        repeatCols: int | Collection[int] = 0,
        splitByRow: int = 1,
        splitInRow: int = 0,
        emptyTableAction: Literal["error", "indicate", "ignore"] | None = None,
        ident: str | None = None,
        hAlign: _HAlignment | None = None,
        vAlign: _VAlignment | None = None,
        normalizedData: int = 0,
        cellStyles: Sequence[Sequence[CellStyle]] | None = None,
        rowSplitRange: tuple[int, int] | None = None,
        spaceBefore: float | None = None,
        spaceAfter: float | None = None,
        longTableOptimize=None,
        minRowHeights: Sequence[float] | None = None,
        cornerRadii: _CornerRadii | _UNSET_ | None = ...,
        renderCB: TableRenderCB | None = None,
        shadow: ShadowStyle | None = None,
    ) -> None: ...
    def identity(self, maxLen: int | None = 30) -> str: ...
    def normalizeData(
        self,
        data: Iterable[Iterable[Any]],
    ) -> list[list[Any]]: ...
    def minWidth(self) -> float: ...
    def setStyle(
        self,
        tblstyle: TableStyle | Iterable[_TableCommand],
    ) -> None: ...
    def normCellRange(
        self,
        sc: int,
        ec: int,
        sr: int,
        er: int,
    ) -> tuple[int, int, int, int]: ...
    def onSplit(self, T: Table, byRow: int = 1) -> None: ...
    def draw(self) -> None: ...

class LongTable(Table): ...

class TableRenderCB:
    def __call__(self, T: Table, cmd: str, *args: Any) -> None: ...
    @abstractmethod
    def startTable(self, T: Table) -> None: ...
    @abstractmethod
    def startBG(self, T: Table) -> None: ...
    @abstractmethod
    def endBG(self, T: Table) -> None: ...
    @abstractmethod
    def startRow(self, T: Table, rowNo: int) -> None: ...
    @abstractmethod
    def startCell(
        self,
        T: Table,
        rowNo: int,
        colNo: int,
        cellval: Any,
        cellstyle: CellStyle,
        pos: tuple[int, int],
        size: tuple[int, int],
    ) -> None: ...
    @abstractmethod
    def endCell(self, T: Table) -> None: ...
    @abstractmethod
    def endRow(self, T: Table) -> None: ...
    @abstractmethod
    def startLines(self, T: Table) -> None: ...
    @abstractmethod
    def endLines(self, T: Table) -> None: ...
    @abstractmethod
    def endTable(self, T: Table) -> None: ...
