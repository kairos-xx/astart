import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.well_known_types
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Duration(
    google.protobuf.message.Message,
    google.protobuf.internal.well_known_types.Duration,
):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SECONDS_FIELD_NUMBER: builtins.int
    NANOS_FIELD_NUMBER: builtins.int
    seconds: builtins.int
    """Signed seconds of the span of time. Must be from -315,576,000,000
    to +315,576,000,000 inclusive. Note: these bounds are computed from:
    60 sec/min * 60 min/hr * 24 hr/day * 365.25 days/year * 10000 years
    """
    nanos: builtins.int
    """Signed fractions of a second at nanosecond resolution of the span
    of time. Durations less than one second are represented with a 0
    `seconds` field and a positive or negative `nanos` field. For durations
    of one second or more, a non-zero value for the `nanos` field must be
    of the same sign as the `seconds` field. Must be from -999,999,999
    to +999,999,999 inclusive.
    """
    def __init__(
        self,
        *,
        seconds: builtins.int | None = ...,
        nanos: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["nanos", b"nanos", "seconds", b"seconds"],
    ) -> None: ...

global___Duration = Duration
