from ..timezone.tzp import TZP as TZP
from .tzid import tzid_from_dt as tzid_from_dt
from .tzid import tzid_from_tzinfo as tzid_from_tzinfo
from .tzid import tzids_from_tzinfo as tzids_from_tzinfo

__all__ = [
    "TZP",
    "tzid_from_dt",
    "tzid_from_tzinfo",
    "tzids_from_tzinfo",
    "tzp",
    "use_pytz",
    "use_zoneinfo",
]
tzp: TZP

def use_pytz() -> None: ...
def use_zoneinfo() -> None: ...
