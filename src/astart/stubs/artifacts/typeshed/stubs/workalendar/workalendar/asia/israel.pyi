import datetime
from typing import Any

from ..core import Calendar

type _HebrewDate = Any | datetime.date

class Israel(Calendar):
    def get_hebrew_independence_day(
        self,
        jewish_year: int,
    ) -> list[tuple[_HebrewDate, str]]: ...
