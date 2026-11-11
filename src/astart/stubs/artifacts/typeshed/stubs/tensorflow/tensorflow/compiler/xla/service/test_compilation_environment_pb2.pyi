import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class TestCompilationEnvironment1(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SOME_FLAG_FIELD_NUMBER: builtins.int
    some_flag: builtins.int
    def __init__(self, *, some_flag: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["some_flag", b"some_flag"],
    ) -> None: ...

global___TestCompilationEnvironment1 = TestCompilationEnvironment1

@typing.final
class TestCompilationEnvironment2(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SOME_OTHER_FLAG_FIELD_NUMBER: builtins.int
    some_other_flag: builtins.int
    def __init__(
        self,
        *,
        some_other_flag: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["some_other_flag", b"some_other_flag"],
    ) -> None: ...

global___TestCompilationEnvironment2 = TestCompilationEnvironment2

@typing.final
class TestCompilationEnvironment3(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    A_THIRD_FLAG_FIELD_NUMBER: builtins.int
    a_third_flag: builtins.int
    def __init__(self, *, a_third_flag: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["a_third_flag", b"a_third_flag"],
    ) -> None: ...

global___TestCompilationEnvironment3 = TestCompilationEnvironment3
