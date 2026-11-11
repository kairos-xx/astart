import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.internal.well_known_types
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _NullValue:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _NullValueEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _NullValue.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    NULL_VALUE: _NullValue.ValueType
    """Null value."""

class NullValue(_NullValue, metaclass=_NullValueEnumTypeWrapper): ...

NULL_VALUE: NullValue.ValueType
"""Null value."""
global___NullValue = NullValue

@typing.final
class Struct(
    google.protobuf.message.Message,
    google.protobuf.internal.well_known_types.Struct,
):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class FieldsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___Value: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___Value | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    FIELDS_FIELD_NUMBER: builtins.int
    @property
    def fields(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___Value,
    ]: ...
    def __init__(
        self,
        *,
        fields: collections.abc.Mapping[builtins.str, global___Value]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["fields", b"fields"],
    ) -> None: ...

global___Struct = Struct

@typing.final
class Value(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NULL_VALUE_FIELD_NUMBER: builtins.int
    NUMBER_VALUE_FIELD_NUMBER: builtins.int
    STRING_VALUE_FIELD_NUMBER: builtins.int
    BOOL_VALUE_FIELD_NUMBER: builtins.int
    STRUCT_VALUE_FIELD_NUMBER: builtins.int
    LIST_VALUE_FIELD_NUMBER: builtins.int
    null_value: global___NullValue.ValueType
    """Represents a null value."""
    number_value: builtins.float
    """Represents a double value."""
    string_value: builtins.str
    """Represents a string value."""
    bool_value: builtins.bool
    """Represents a boolean value."""
    @property
    def struct_value(self) -> global___Struct: ...
    @property
    def list_value(self) -> global___ListValue: ...
    def __init__(
        self,
        *,
        null_value: global___NullValue.ValueType | None = ...,
        number_value: builtins.float | None = ...,
        string_value: builtins.str | None = ...,
        bool_value: builtins.bool | None = ...,
        struct_value: global___Struct | None = ...,
        list_value: global___ListValue | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "bool_value",
            b"bool_value",
            "kind",
            b"kind",
            "list_value",
            b"list_value",
            "null_value",
            b"null_value",
            "number_value",
            b"number_value",
            "string_value",
            b"string_value",
            "struct_value",
            b"struct_value",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "bool_value",
            b"bool_value",
            "kind",
            b"kind",
            "list_value",
            b"list_value",
            "null_value",
            b"null_value",
            "number_value",
            b"number_value",
            "string_value",
            b"string_value",
            "struct_value",
            b"struct_value",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["kind", b"kind"],
    ) -> (
        typing.Literal[
            "null_value",
            "number_value",
            "string_value",
            "bool_value",
            "struct_value",
            "list_value",
        ]
        | None
    ): ...

global___Value = Value

@typing.final
class ListValue(
    google.protobuf.message.Message,
    google.protobuf.internal.well_known_types.ListValue,
):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUES_FIELD_NUMBER: builtins.int
    @property
    def values(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___Value
    ]: ...
    def __init__(
        self,
        *,
        values: collections.abc.Iterable[global___Value] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["values", b"values"],
    ) -> None: ...

global___ListValue = ListValue
