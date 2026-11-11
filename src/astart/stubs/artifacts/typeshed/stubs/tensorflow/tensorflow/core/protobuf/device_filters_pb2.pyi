import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class TaskDeviceFilters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DEVICE_FILTERS_FIELD_NUMBER: builtins.int
    @property
    def device_filters(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        device_filters: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["device_filters", b"device_filters"],
    ) -> None: ...

global___TaskDeviceFilters = TaskDeviceFilters

@typing.final
class JobDeviceFilters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class TasksEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.int
        @property
        def value(self) -> global___TaskDeviceFilters: ...
        def __init__(
            self,
            *,
            key: builtins.int | None = ...,
            value: global___TaskDeviceFilters | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    TASKS_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The name of this job."""
    @property
    def tasks(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.int,
        global___TaskDeviceFilters,
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        tasks: collections.abc.Mapping[
            builtins.int,
            global___TaskDeviceFilters,
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name", "tasks", b"tasks"],
    ) -> None: ...

global___JobDeviceFilters = JobDeviceFilters

@typing.final
class ClusterDeviceFilters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    JOBS_FIELD_NUMBER: builtins.int
    @property
    def jobs(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___JobDeviceFilters
    ]: ...
    def __init__(
        self,
        *,
        jobs: collections.abc.Iterable[global___JobDeviceFilters] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["jobs", b"jobs"],
    ) -> None: ...

global___ClusterDeviceFilters = ClusterDeviceFilters
