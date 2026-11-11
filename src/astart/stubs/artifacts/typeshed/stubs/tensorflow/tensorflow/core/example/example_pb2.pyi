import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message
import tensorflow.core.example.feature_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Example(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FEATURES_FIELD_NUMBER: builtins.int
    @property
    def features(self) -> tensorflow.core.example.feature_pb2.Features: ...
    def __init__(
        self,
        *,
        features: tensorflow.core.example.feature_pb2.Features | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["features", b"features"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["features", b"features"],
    ) -> None: ...

global___Example = Example

@typing.final
class SequenceExample(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    CONTEXT_FIELD_NUMBER: builtins.int
    FEATURE_LISTS_FIELD_NUMBER: builtins.int
    @property
    def context(self) -> tensorflow.core.example.feature_pb2.Features: ...
    @property
    def feature_lists(
        self,
    ) -> tensorflow.core.example.feature_pb2.FeatureLists: ...
    def __init__(
        self,
        *,
        context: tensorflow.core.example.feature_pb2.Features | None = ...,
        feature_lists: tensorflow.core.example.feature_pb2.FeatureLists
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "context",
            b"context",
            "feature_lists",
            b"feature_lists",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "context",
            b"context",
            "feature_lists",
            b"feature_lists",
        ],
    ) -> None: ...

global___SequenceExample = SequenceExample
