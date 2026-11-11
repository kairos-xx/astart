import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.tensor_pb2
import tensorflow.core.framework.tensor_shape_pb2
import tensorflow.core.framework.tensor_slice_pb2
import tensorflow.core.framework.types_pb2
import tensorflow.core.framework.versions_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class SavedSliceMeta(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    SHAPE_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    SLICE_FIELD_NUMBER: builtins.int
    name: builtins.str
    """Name of the tensor."""
    type: tensorflow.core.framework.types_pb2.DataType.ValueType
    """Type of the tensor"""
    @property
    def shape(
        self,
    ) -> tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto: ...
    @property
    def slice(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        tensorflow.core.framework.tensor_slice_pb2.TensorSliceProto
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        shape: tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto
        | None = ...,
        type: tensorflow.core.framework.types_pb2.DataType.ValueType
        | None = ...,
        slice: collections.abc.Iterable[
            tensorflow.core.framework.tensor_slice_pb2.TensorSliceProto
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["shape", b"shape"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "shape",
            b"shape",
            "slice",
            b"slice",
            "type",
            b"type",
        ],
    ) -> None: ...

global___SavedSliceMeta = SavedSliceMeta

@typing.final
class SavedTensorSliceMeta(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TENSOR_FIELD_NUMBER: builtins.int
    VERSIONS_FIELD_NUMBER: builtins.int
    @property
    def tensor(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___SavedSliceMeta
    ]: ...
    @property
    def versions(
        self,
    ) -> tensorflow.core.framework.versions_pb2.VersionDef: ...
    def __init__(
        self,
        *,
        tensor: collections.abc.Iterable[global___SavedSliceMeta] | None = ...,
        versions: tensorflow.core.framework.versions_pb2.VersionDef
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["versions", b"versions"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "tensor",
            b"tensor",
            "versions",
            b"versions",
        ],
    ) -> None: ...

global___SavedTensorSliceMeta = SavedTensorSliceMeta

@typing.final
class SavedSlice(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    SLICE_FIELD_NUMBER: builtins.int
    DATA_FIELD_NUMBER: builtins.int
    name: builtins.str
    """Name of the tensor that this slice belongs to. This must be identical to
    the name used to encode the key for this record.
    """
    @property
    def slice(
        self,
    ) -> tensorflow.core.framework.tensor_slice_pb2.TensorSliceProto: ...
    @property
    def data(self) -> tensorflow.core.framework.tensor_pb2.TensorProto: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        slice: tensorflow.core.framework.tensor_slice_pb2.TensorSliceProto
        | None = ...,
        data: tensorflow.core.framework.tensor_pb2.TensorProto | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["data", b"data", "slice", b"slice"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "data",
            b"data",
            "name",
            b"name",
            "slice",
            b"slice",
        ],
    ) -> None: ...

global___SavedSlice = SavedSlice

@typing.final
class SavedTensorSlices(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    META_FIELD_NUMBER: builtins.int
    DATA_FIELD_NUMBER: builtins.int
    @property
    def meta(self) -> global___SavedTensorSliceMeta: ...
    @property
    def data(self) -> global___SavedSlice: ...
    def __init__(
        self,
        *,
        meta: global___SavedTensorSliceMeta | None = ...,
        data: global___SavedSlice | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["data", b"data", "meta", b"meta"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["data", b"data", "meta", b"meta"],
    ) -> None: ...

global___SavedTensorSlices = SavedTensorSlices
