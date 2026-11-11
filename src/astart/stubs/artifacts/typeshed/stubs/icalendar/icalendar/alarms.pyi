import datetime

from .cal import Alarm, Event, Todo
from .error import (
    ComponentEndMissing as ComponentEndMissing,
)
from .error import (
    ComponentStartMissing as ComponentStartMissing,
)
from .error import (
    IncompleteAlarmInformation as IncompleteAlarmInformation,
)
from .error import (
    LocalTimezoneMissing as LocalTimezoneMissing,
)

__all__ = [
    "AlarmTime",
    "Alarms",
    "ComponentEndMissing",
    "ComponentStartMissing",
    "IncompleteAlarmInformation",
]
type Parent = Event | Todo

class AlarmTime:
    def __init__(
        self,
        alarm: Alarm,
        trigger: datetime.datetime,
        acknowledged_until: datetime.datetime | None = None,
        snoozed_until: datetime.datetime | None = None,
        parent: Parent | None = None,
    ) -> None: ...
    @property
    def acknowledged(self) -> datetime.datetime | None: ...
    @property
    def alarm(self) -> Alarm: ...
    @property
    def parent(self) -> Parent | None: ...
    def is_active(self) -> bool: ...
    @property
    def trigger(self) -> datetime.date: ...

class Alarms:
    def __init__(
        self,
        component: Alarm | Event | Todo | None = None,
    ) -> None: ...
    def add_component(self, component: Alarm | Parent) -> None: ...
    def set_parent(self, parent: Parent) -> None: ...
    def add_alarm(self, alarm: Alarm) -> None: ...
    def set_start(self, dt: datetime.date | None) -> None: ...
    def set_end(self, dt: datetime.date | None) -> None: ...
    def acknowledge_until(self, dt: datetime.date | None) -> None: ...
    def snooze_until(self, dt: datetime.date | None) -> None: ...
    def set_local_timezone(
        self,
        tzinfo: datetime.tzinfo | str | None,
    ) -> None: ...
    @property
    def times(self) -> list[AlarmTime]: ...
    @property
    def active(self) -> list[AlarmTime]: ...
