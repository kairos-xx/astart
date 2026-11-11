import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class HistogramProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    MIN_FIELD_NUMBER: builtins.int
    MAX_FIELD_NUMBER: builtins.int
    NUM_FIELD_NUMBER: builtins.int
    SUM_FIELD_NUMBER: builtins.int
    SUM_SQUARES_FIELD_NUMBER: builtins.int
    BUCKET_LIMIT_FIELD_NUMBER: builtins.int
    BUCKET_FIELD_NUMBER: builtins.int
    min: builtins.float
    max: builtins.float
    num: builtins.float
    sum: builtins.float
    sum_squares: builtins.float
    @property
    def bucket_limit(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def bucket(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    def __init__(
        self,
        *,
        min: builtins.float | None = ...,
        max: builtins.float | None = ...,
        num: builtins.float | None = ...,
        sum: builtins.float | None = ...,
        sum_squares: builtins.float | None = ...,
        bucket_limit: collections.abc.Iterable[builtins.float] | None = ...,
        bucket: collections.abc.Iterable[builtins.float] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "bucket",
            b"bucket",
            "bucket_limit",
            b"bucket_limit",
            "max",
            b"max",
            "min",
            b"min",
            "num",
            b"num",
            "sum",
            b"sum",
            "sum_squares",
            b"sum_squares",
        ],
    ) -> None: ...

global___HistogramProto = HistogramProto
