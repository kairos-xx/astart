import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.well_known_types
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Timestamp(
    google.protobuf.message.Message,
    google.protobuf.internal.well_known_types.Timestamp,
):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SECONDS_FIELD_NUMBER: builtins.int
    NANOS_FIELD_NUMBER: builtins.int
    seconds: builtins.int
    """Represents seconds of UTC time since Unix epoch
    1970-01-01T00:00:00Z. Must be from 0001-01-01T00:00:00Z to
    9999-12-31T23:59:59Z inclusive.
    """
    nanos: builtins.int
    """Non-negative fractions of a second at nanosecond resolution. Negative
    second values with fractions must still have non-negative nanos values
    that count forward in time. Must be from 0 to 999,999,999
    inclusive.
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

global___Timestamp = Timestamp
