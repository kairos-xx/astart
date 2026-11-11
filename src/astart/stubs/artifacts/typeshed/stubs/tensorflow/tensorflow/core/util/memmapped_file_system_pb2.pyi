import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class MemmappedFileSystemDirectoryElement(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    OFFSET_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    LENGTH_FIELD_NUMBER: builtins.int
    offset: builtins.int
    name: builtins.str
    length: builtins.int
    def __init__(
        self,
        *,
        offset: builtins.int | None = ...,
        name: builtins.str | None = ...,
        length: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "length",
            b"length",
            "name",
            b"name",
            "offset",
            b"offset",
        ],
    ) -> None: ...

global___MemmappedFileSystemDirectoryElement = (
    MemmappedFileSystemDirectoryElement
)

@typing.final
class MemmappedFileSystemDirectory(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    ELEMENT_FIELD_NUMBER: builtins.int
    @property
    def element(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___MemmappedFileSystemDirectoryElement
    ]: ...
    def __init__(
        self,
        *,
        element: collections.abc.Iterable[
            global___MemmappedFileSystemDirectoryElement
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["element", b"element"],
    ) -> None: ...

global___MemmappedFileSystemDirectory = MemmappedFileSystemDirectory
