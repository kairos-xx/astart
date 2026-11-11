import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.duration_pb2
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.compiler.xla.service.hlo_pb2
import tensorflow.tsl.protobuf.status_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class CompilerPerfStats(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    INIT_DURATION_FIELD_NUMBER: builtins.int
    HLO_VERIFICATION_DURATION_FIELD_NUMBER: builtins.int
    COMPILATION_PROLOGUE_DURATION_FIELD_NUMBER: builtins.int
    COMPILATION_DURATION_FIELD_NUMBER: builtins.int
    TOTAL_DURATION_FIELD_NUMBER: builtins.int
    @property
    def init_duration(self) -> google.protobuf.duration_pb2.Duration: ...
    @property
    def hlo_verification_duration(
        self,
    ) -> google.protobuf.duration_pb2.Duration: ...
    @property
    def compilation_prologue_duration(
        self,
    ) -> google.protobuf.duration_pb2.Duration: ...
    @property
    def compilation_duration(
        self,
    ) -> google.protobuf.duration_pb2.Duration: ...
    @property
    def total_duration(self) -> google.protobuf.duration_pb2.Duration: ...
    def __init__(
        self,
        *,
        init_duration: google.protobuf.duration_pb2.Duration | None = ...,
        hlo_verification_duration: google.protobuf.duration_pb2.Duration
        | None = ...,
        compilation_prologue_duration: google.protobuf.duration_pb2.Duration
        | None = ...,
        compilation_duration: google.protobuf.duration_pb2.Duration
        | None = ...,
        total_duration: google.protobuf.duration_pb2.Duration | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "compilation_duration",
            b"compilation_duration",
            "compilation_prologue_duration",
            b"compilation_prologue_duration",
            "hlo_verification_duration",
            b"hlo_verification_duration",
            "init_duration",
            b"init_duration",
            "total_duration",
            b"total_duration",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "compilation_duration",
            b"compilation_duration",
            "compilation_prologue_duration",
            b"compilation_prologue_duration",
            "hlo_verification_duration",
            b"hlo_verification_duration",
            "init_duration",
            b"init_duration",
            "total_duration",
            b"total_duration",
        ],
    ) -> None: ...

global___CompilerPerfStats = CompilerPerfStats

@typing.final
class CompilationResult(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class CountersEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.int
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: builtins.int | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    HLO_MODULE_FIELD_NUMBER: builtins.int
    PERF_STATS_FIELD_NUMBER: builtins.int
    STATUS_FIELD_NUMBER: builtins.int
    COUNTERS_FIELD_NUMBER: builtins.int
    @property
    def hlo_module(
        self,
    ) -> tensorflow.compiler.xla.service.hlo_pb2.HloModuleProto: ...
    @property
    def perf_stats(self) -> global___CompilerPerfStats: ...
    @property
    def status(self) -> tensorflow.tsl.protobuf.status_pb2.StatusProto: ...
    @property
    def counters(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.str,
        builtins.int,
    ]: ...
    def __init__(
        self,
        *,
        hlo_module: tensorflow.compiler.xla.service.hlo_pb2.HloModuleProto
        | None = ...,
        perf_stats: global___CompilerPerfStats | None = ...,
        status: tensorflow.tsl.protobuf.status_pb2.StatusProto | None = ...,
        counters: collections.abc.Mapping[builtins.str, builtins.int]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "hlo_module",
            b"hlo_module",
            "perf_stats",
            b"perf_stats",
            "status",
            b"status",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "counters",
            b"counters",
            "hlo_module",
            b"hlo_module",
            "perf_stats",
            b"perf_stats",
            "status",
            b"status",
        ],
    ) -> None: ...

global___CompilationResult = CompilationResult
