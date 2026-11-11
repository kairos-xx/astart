import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.resource_handle_pb2
import tensorflow.core.framework.tensor_shape_pb2
import tensorflow.core.framework.types_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class TensorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DTYPE_FIELD_NUMBER: builtins.int
    TENSOR_SHAPE_FIELD_NUMBER: builtins.int
    VERSION_NUMBER_FIELD_NUMBER: builtins.int
    TENSOR_CONTENT_FIELD_NUMBER: builtins.int
    HALF_VAL_FIELD_NUMBER: builtins.int
    FLOAT_VAL_FIELD_NUMBER: builtins.int
    DOUBLE_VAL_FIELD_NUMBER: builtins.int
    INT_VAL_FIELD_NUMBER: builtins.int
    STRING_VAL_FIELD_NUMBER: builtins.int
    SCOMPLEX_VAL_FIELD_NUMBER: builtins.int
    INT64_VAL_FIELD_NUMBER: builtins.int
    BOOL_VAL_FIELD_NUMBER: builtins.int
    DCOMPLEX_VAL_FIELD_NUMBER: builtins.int
    RESOURCE_HANDLE_VAL_FIELD_NUMBER: builtins.int
    VARIANT_VAL_FIELD_NUMBER: builtins.int
    UINT32_VAL_FIELD_NUMBER: builtins.int
    UINT64_VAL_FIELD_NUMBER: builtins.int
    FLOAT8_VAL_FIELD_NUMBER: builtins.int
    dtype: tensorflow.core.framework.types_pb2.DataType.ValueType
    """Data type of the tensor."""
    version_number: builtins.int
    """Only one of the representations below is set, one of "tensor_contents" and
    the "xxx_val" attributes.  We are not using oneof because as oneofs cannot
    contain repeated fields it would require another extra set of messages.

    Version number.

    In version 0, if the "repeated xxx" representations contain only one
    element, that element is repeated to fill the shape.  This makes it easy
    to represent a constant Tensor with a single value.
    """
    tensor_content: builtins.bytes
    """Serialized raw tensor content from either Tensor::AsProtoTensorContent or
    memcpy in tensorflow::grpc::EncodeTensorToByteBuffer. This representation
    can be used for all tensor types. The purpose of this representation is to
    reduce serialization overhead during RPC call by avoiding serialization of
    many repeated small items.
    """
    float8_val: builtins.bytes
    """DT_FLOAT8_*, use variable-sized set of bytes
    (i.e. the equivalent of repeated uint8, if such a thing existed).
    """
    @property
    def tensor_shape(
        self,
    ) -> tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto: ...
    @property
    def half_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def float_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def double_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def int_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def string_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bytes
    ]: ...
    @property
    def scomplex_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def int64_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def bool_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    @property
    def dcomplex_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def resource_handle_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        tensorflow.core.framework.resource_handle_pb2.ResourceHandleProto
    ]: ...
    @property
    def variant_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___VariantTensorDataProto
    ]: ...
    @property
    def uint32_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def uint64_val(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        dtype: tensorflow.core.framework.types_pb2.DataType.ValueType
        | None = ...,
        tensor_shape: tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto
        | None = ...,
        version_number: builtins.int | None = ...,
        tensor_content: builtins.bytes | None = ...,
        half_val: collections.abc.Iterable[builtins.int] | None = ...,
        float_val: collections.abc.Iterable[builtins.float] | None = ...,
        double_val: collections.abc.Iterable[builtins.float] | None = ...,
        int_val: collections.abc.Iterable[builtins.int] | None = ...,
        string_val: collections.abc.Iterable[builtins.bytes] | None = ...,
        scomplex_val: collections.abc.Iterable[builtins.float] | None = ...,
        int64_val: collections.abc.Iterable[builtins.int] | None = ...,
        bool_val: collections.abc.Iterable[builtins.bool] | None = ...,
        dcomplex_val: collections.abc.Iterable[builtins.float] | None = ...,
        resource_handle_val: (
            collections.abc.Iterable[
                tensorflow.core.framework.resource_handle_pb2.ResourceHandleProto
            ]
            | None
        ) = ...,
        variant_val: collections.abc.Iterable[global___VariantTensorDataProto]
        | None = ...,
        uint32_val: collections.abc.Iterable[builtins.int] | None = ...,
        uint64_val: collections.abc.Iterable[builtins.int] | None = ...,
        float8_val: builtins.bytes | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["tensor_shape", b"tensor_shape"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "bool_val",
            b"bool_val",
            "dcomplex_val",
            b"dcomplex_val",
            "double_val",
            b"double_val",
            "dtype",
            b"dtype",
            "float8_val",
            b"float8_val",
            "float_val",
            b"float_val",
            "half_val",
            b"half_val",
            "int64_val",
            b"int64_val",
            "int_val",
            b"int_val",
            "resource_handle_val",
            b"resource_handle_val",
            "scomplex_val",
            b"scomplex_val",
            "string_val",
            b"string_val",
            "tensor_content",
            b"tensor_content",
            "tensor_shape",
            b"tensor_shape",
            "uint32_val",
            b"uint32_val",
            "uint64_val",
            b"uint64_val",
            "variant_val",
            b"variant_val",
            "version_number",
            b"version_number",
        ],
    ) -> None: ...

global___TensorProto = TensorProto

@typing.final
class VariantTensorDataProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TYPE_NAME_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    TENSORS_FIELD_NUMBER: builtins.int
    type_name: builtins.str
    """Name of the type of objects being serialized."""
    metadata: builtins.bytes
    """Portions of the object that are not Tensors."""
    @property
    def tensors(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___TensorProto
    ]: ...
    def __init__(
        self,
        *,
        type_name: builtins.str | None = ...,
        metadata: builtins.bytes | None = ...,
        tensors: collections.abc.Iterable[global___TensorProto] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "metadata",
            b"metadata",
            "tensors",
            b"tensors",
            "type_name",
            b"type_name",
        ],
    ) -> None: ...

global___VariantTensorDataProto = VariantTensorDataProto
