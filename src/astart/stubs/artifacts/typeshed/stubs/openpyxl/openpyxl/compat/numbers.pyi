from decimal import Decimal
from typing import Final

type _NumericTypes = int | float | Decimal
NUMERIC_TYPES: Final[tuple[type[_NumericTypes], ...]]
NUMPY: Final[bool]
