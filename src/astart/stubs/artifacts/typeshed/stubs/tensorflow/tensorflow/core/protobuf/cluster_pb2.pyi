import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class JobDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class TasksEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.int
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.int | None = ...,
            value: builtins.str | None = ...,
        ) -> None: ...
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
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.int,
        builtins.str,
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        tasks: collections.abc.Mapping[builtins.int, builtins.str]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name", "tasks", b"tasks"],
    ) -> None: ...

global___JobDef = JobDef

@typing.final
class ClusterDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    JOB_FIELD_NUMBER: builtins.int
    @property
    def job(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___JobDef
    ]: ...
    def __init__(
        self,
        *,
        job: collections.abc.Iterable[global___JobDef] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["job", b"job"],
    ) -> None: ...

global___ClusterDef = ClusterDef
