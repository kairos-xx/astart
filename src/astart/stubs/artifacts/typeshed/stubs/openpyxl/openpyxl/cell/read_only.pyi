from typing import Final

from _typeshed import Incomplete
from openpyxl.cell import _CellGetValue
from openpyxl.styles.alignment import Alignment
from openpyxl.styles.borders import Border
from openpyxl.styles.cell_style import StyleArray
from openpyxl.styles.fills import Fill
from openpyxl.styles.fonts import Font
from openpyxl.styles.protection import Protection
from openpyxl.workbook.child import _WorkbookChild
from openpyxl.worksheet._read_only import ReadOnlyWorksheet

class ReadOnlyCell:
    __slots__ = ("_style_id", "_value", "column", "data_type", "parent", "row")
    parent: _WorkbookChild | ReadOnlyWorksheet
    row: Incomplete
    column: Incomplete
    data_type: Incomplete
    def __init__(
        self,
        sheet: _WorkbookChild | ReadOnlyWorksheet,
        row,
        column,
        value,
        data_type: str = "n",
        style_id: int = 0,
    ) -> None: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    @property
    def coordinate(self) -> str: ...
    @property
    def column_letter(self) -> str: ...
    @property
    def style_array(self) -> StyleArray: ...
    @property
    def has_style(self) -> bool: ...
    @property
    def number_format(self) -> str: ...
    @property
    def font(self) -> Font: ...
    @property
    def fill(self) -> Fill: ...
    @property
    def border(self) -> Border: ...
    @property
    def alignment(self) -> Alignment: ...
    @property
    def protection(self) -> Protection: ...
    @property
    def is_date(self) -> bool: ...
    @property
    def internal_value(self) -> _CellGetValue: ...
    @property
    def value(self) -> _CellGetValue: ...
    @value.setter
    def value(self, value: None) -> None: ...

class EmptyCell:
    __slots__ = ()
    value: Incomplete
    is_date: bool
    font: Incomplete
    border: Incomplete
    fill: Incomplete
    number_format: Incomplete
    alignment: Incomplete
    data_type: str

EMPTY_CELL: Final[EmptyCell]
