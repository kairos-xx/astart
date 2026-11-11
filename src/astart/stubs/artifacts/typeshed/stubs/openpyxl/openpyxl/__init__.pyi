from typing import IO, Literal, Protocol, type_check_only

from _typeshed import StrPath, SupportsRead, SupportsWrite
from openpyxl.compat.numbers import NUMPY as NUMPY
from openpyxl.reader.excel import load_workbook as load_workbook
from openpyxl.workbook import Workbook as Workbook
from openpyxl.xml import DEFUSEDXML as DEFUSEDXML
from openpyxl.xml import LXML as LXML

from ._constants import (
    __author__ as __author__,
)
from ._constants import (
    __author_email__ as __author_email__,
)
from ._constants import (
    __license__ as __license__,
)
from ._constants import (
    __maintainer_email__ as __maintainer_email__,
)
from ._constants import (
    __url__ as __url__,
)
from ._constants import (
    __version__ as __version__,
)

DEBUG: bool
open = load_workbook
type _VisibilityType = Literal["visible", "hidden", "veryHidden"]
type _ZipFileFileProtocol = StrPath | IO[bytes] | SupportsRead[bytes]
type _ZipFileFileWriteProtocol = StrPath | IO[bytes] | SupportsWrite[bytes]

@type_check_only
class _Decodable(Protocol):
    def decode(self, encoding: str, /) -> str: ...
