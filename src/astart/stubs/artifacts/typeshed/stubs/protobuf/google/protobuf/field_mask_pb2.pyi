import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.well_known_types
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class FieldMask(
    google.protobuf.message.Message,
    google.protobuf.internal.well_known_types.FieldMask,
):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    PATHS_FIELD_NUMBER: builtins.int
    @property
    def paths(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        paths: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["paths", b"paths"],
    ) -> None: ...

global___FieldMask = FieldMask
