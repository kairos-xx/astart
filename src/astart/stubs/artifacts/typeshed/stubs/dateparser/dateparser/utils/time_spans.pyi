import datetime
from typing import NotRequired, TypedDict, TypeVar, type_check_only

from dateparser.conf import Settings

_DateT = TypeVar("_DateT", bound=datetime.date)

@type_check_only
class _SpanInformation(TypedDict):
    type: str
    direction: str
    matched_text: str
    start_pos: int
    end_pos: int
    number: NotRequired[int]

def get_week_start[DateT: datetime.date](
    date: _DateT,
    start_of_week: str = "monday",
) -> _DateT: ...
def get_week_end[DateT: datetime.date](
    date: _DateT,
    start_of_week: str = "monday",
) -> _DateT: ...
def detect_time_span(text: str) -> _SpanInformation | None: ...
def generate_time_span[DateT: datetime.date](
    span_info: _SpanInformation,
    base_date: _DateT | None = None,
    settings: Settings | None = None,
) -> tuple[_DateT, _DateT]: ...
