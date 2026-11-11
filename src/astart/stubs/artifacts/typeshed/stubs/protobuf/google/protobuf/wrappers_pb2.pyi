import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class DoubleValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.float
    """The double value."""
    def __init__(self, *, value: builtins.float | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___DoubleValue = DoubleValue

@typing.final
class FloatValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.float
    """The float value."""
    def __init__(self, *, value: builtins.float | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___FloatValue = FloatValue

@typing.final
class Int64Value(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.int
    """The int64 value."""
    def __init__(self, *, value: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___Int64Value = Int64Value

@typing.final
class UInt64Value(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.int
    """The uint64 value."""
    def __init__(self, *, value: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___UInt64Value = UInt64Value

@typing.final
class Int32Value(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.int
    """The int32 value."""
    def __init__(self, *, value: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___Int32Value = Int32Value

@typing.final
class UInt32Value(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.int
    """The uint32 value."""
    def __init__(self, *, value: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___UInt32Value = UInt32Value

@typing.final
class BoolValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.bool
    """The bool value."""
    def __init__(self, *, value: builtins.bool | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___BoolValue = BoolValue

@typing.final
class StringValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.str
    """The string value."""
    def __init__(self, *, value: builtins.str | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___StringValue = StringValue

@typing.final
class BytesValue(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    value: builtins.bytes
    """The bytes value."""
    def __init__(self, *, value: builtins.bytes | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___BytesValue = BytesValue
