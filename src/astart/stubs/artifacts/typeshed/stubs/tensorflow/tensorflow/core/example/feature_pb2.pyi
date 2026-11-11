import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class BytesList(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    @property
    def value(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bytes
    ]: ...
    def __init__(
        self,
        *,
        value: collections.abc.Iterable[builtins.bytes] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___BytesList = BytesList

@typing.final
class FloatList(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    @property
    def value(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    def __init__(
        self,
        *,
        value: collections.abc.Iterable[builtins.float] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___FloatList = FloatList

@typing.final
class Int64List(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    VALUE_FIELD_NUMBER: builtins.int
    @property
    def value(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        value: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["value", b"value"],
    ) -> None: ...

global___Int64List = Int64List

@typing.final
class Feature(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    BYTES_LIST_FIELD_NUMBER: builtins.int
    FLOAT_LIST_FIELD_NUMBER: builtins.int
    INT64_LIST_FIELD_NUMBER: builtins.int
    @property
    def bytes_list(self) -> global___BytesList: ...
    @property
    def float_list(self) -> global___FloatList: ...
    @property
    def int64_list(self) -> global___Int64List: ...
    def __init__(
        self,
        *,
        bytes_list: global___BytesList | None = ...,
        float_list: global___FloatList | None = ...,
        int64_list: global___Int64List | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "bytes_list",
            b"bytes_list",
            "float_list",
            b"float_list",
            "int64_list",
            b"int64_list",
            "kind",
            b"kind",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "bytes_list",
            b"bytes_list",
            "float_list",
            b"float_list",
            "int64_list",
            b"int64_list",
            "kind",
            b"kind",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["kind", b"kind"],
    ) -> typing.Literal["bytes_list", "float_list", "int64_list"] | None: ...

global___Feature = Feature

@typing.final
class Features(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class FeatureEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___Feature: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___Feature | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    FEATURE_FIELD_NUMBER: builtins.int
    @property
    def feature(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___Feature,
    ]: ...
    def __init__(
        self,
        *,
        feature: collections.abc.Mapping[builtins.str, global___Feature]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["feature", b"feature"],
    ) -> None: ...

global___Features = Features

@typing.final
class FeatureList(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FEATURE_FIELD_NUMBER: builtins.int
    @property
    def feature(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___Feature
    ]: ...
    def __init__(
        self,
        *,
        feature: collections.abc.Iterable[global___Feature] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["feature", b"feature"],
    ) -> None: ...

global___FeatureList = FeatureList

@typing.final
class FeatureLists(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class FeatureListEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___FeatureList: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___FeatureList | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    FEATURE_LIST_FIELD_NUMBER: builtins.int
    @property
    def feature_list(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___FeatureList,
    ]: ...
    def __init__(
        self,
        *,
        feature_list: collections.abc.Mapping[
            builtins.str,
            global___FeatureList,
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["feature_list", b"feature_list"],
    ) -> None: ...

global___FeatureLists = FeatureLists
