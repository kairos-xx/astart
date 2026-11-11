import re
from datetime import datetime
from typing import Final
from zoneinfo import ZoneInfo

from _typeshed import Incomplete
from dateparser.conf import Settings
from dateparser.date import DateData

PATTERN: Final[re.Pattern[str]]

class FreshnessDateDataParser:
    def get_local_tz(self) -> ZoneInfo: ...
    def parse(
        self,
        date_string: str,
        settings: Settings,
    ) -> tuple[datetime | None, str | None]: ...
    def get_kwargs(
        self,
        date_string: str,
    ) -> tuple[dict[str, float], dict[str, Incomplete]] | dict[None, None]: ...
    def get_date_data(
        self,
        date_string: str,
        settings: Settings | None = None,
    ) -> DateData: ...

freshness_date_parser: FreshnessDateDataParser
