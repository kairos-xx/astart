from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from openpyxl.cell.rich_text import CellRichText
from openpyxl.worksheet.formula import ArrayFormula, DataTableFormula

from .cell import Cell as Cell
from .cell import MergedCell as MergedCell
from .cell import WriteOnlyCell as WriteOnlyCell
from .read_only import ReadOnlyCell as ReadOnlyCell

type _TimeTypes = datetime | date | time | timedelta
type _CellGetValue = (  # Used in other modules
    # if numpy is installed also numpy bool and number types
    bool
    | float
    | Decimal
    | str
    | CellRichText
    | _TimeTypes
    | DataTableFormula
    | ArrayFormula
    | None
)
type _AnyCellValue = Any  # AnyOf _CellGetValue # Used in other modules
type _CellSetValue = _CellGetValue | bytes  # Used in other modules

type _CellOrMergedCell = Cell | MergedCell  # Used in other modules
