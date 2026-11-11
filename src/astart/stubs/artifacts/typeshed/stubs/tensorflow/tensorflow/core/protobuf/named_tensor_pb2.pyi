import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message
import tensorflow.core.framework.tensor_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class NamedTensorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    TENSOR_FIELD_NUMBER: builtins.int
    name: builtins.str
    """Name of the tensor."""
    @property
    def tensor(self) -> tensorflow.core.framework.tensor_pb2.TensorProto: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        tensor: tensorflow.core.framework.tensor_pb2.TensorProto | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["tensor", b"tensor"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name", "tensor", b"tensor"],
    ) -> None: ...

global___NamedTensorProto = NamedTensorProto
