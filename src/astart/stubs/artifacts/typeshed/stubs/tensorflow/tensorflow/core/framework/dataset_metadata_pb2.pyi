import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Metadata(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    name: builtins.bytes
    def __init__(self, *, name: builtins.bytes | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name"],
    ) -> None: ...

global___Metadata = Metadata
