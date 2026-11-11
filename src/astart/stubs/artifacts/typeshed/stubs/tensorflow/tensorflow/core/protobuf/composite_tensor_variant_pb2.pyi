import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message
import tensorflow.core.protobuf.struct_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class CompositeTensorVariantMetadata(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TYPE_SPEC_PROTO_FIELD_NUMBER: builtins.int
    @property
    def type_spec_proto(
        self,
    ) -> tensorflow.core.protobuf.struct_pb2.TypeSpecProto: ...
    def __init__(
        self,
        *,
        type_spec_proto: tensorflow.core.protobuf.struct_pb2.TypeSpecProto
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["type_spec_proto", b"type_spec_proto"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["type_spec_proto", b"type_spec_proto"],
    ) -> None: ...

global___CompositeTensorVariantMetadata = CompositeTensorVariantMetadata
