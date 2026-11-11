import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class SourceContext(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FILE_NAME_FIELD_NUMBER: builtins.int
    file_name: builtins.str
    """The path-qualified name of the .proto file that contained the associated
    protobuf element.  For example: `"google/protobuf/source_context.proto"`.
    """
    def __init__(self, *, file_name: builtins.str | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["file_name", b"file_name"],
    ) -> None: ...

global___SourceContext = SourceContext
