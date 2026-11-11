import datetime
from typing import Any

from .core import UnitedStates

type _HebrewDate = Any

class HebrewHolidays:
    hebrew_calendars: dict[int, list[tuple[_HebrewDate | None, datetime.date]]]
    @classmethod
    def get_hebrew_calendar(
        cls,
        gregorian_year: int,
    ) -> list[tuple[_HebrewDate | None, datetime.date]]: ...
    @classmethod
    def search_hebrew_calendar(
        cls,
        gregorian_year: int,
        hebrew_month: int,
        hebrew_day: int,
    ) -> datetime.date: ...
    @classmethod
    def get_rosh_hashanah(cls, year: int) -> datetime.date: ...
    @classmethod
    def get_yom_kippur(cls, year: int) -> datetime.date: ...

class Florida(UnitedStates): ...

class FloridaLegal(Florida):
    def __init__(self, *args, **kwargs) -> None: ...

class FloridaCircuitCourts(HebrewHolidays, Florida): ...
class FloridaMiamiDade(Florida): ...
