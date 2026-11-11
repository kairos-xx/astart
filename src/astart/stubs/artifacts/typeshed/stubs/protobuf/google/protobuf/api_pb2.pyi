import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.source_context_pb2
import google.protobuf.type_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class Api(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    METHODS_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    VERSION_FIELD_NUMBER: builtins.int
    SOURCE_CONTEXT_FIELD_NUMBER: builtins.int
    MIXINS_FIELD_NUMBER: builtins.int
    SYNTAX_FIELD_NUMBER: builtins.int
    EDITION_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The fully qualified name of this interface, including package name
    followed by the interface's simple name.
    """
    version: builtins.str
    """A version string for this interface. If specified, must have the form
    `major-version.minor-version`, as in `1.10`. If the minor version is
    omitted, it defaults to zero. If the entire version field is empty, the
    major version is derived from the package name, as outlined below. If the
    field is not empty, the version in the package name will be verified to be
    consistent with what is provided here.

    The versioning schema uses [semantic
    versioning](http://semver.org) where the major version number
    indicates a breaking change and the minor version an additive,
    non-breaking change. Both version numbers are signals to users
    what to expect from different versions, and should be carefully
    chosen based on the product plan.

    The major version is also reflected in the package name of the
    interface, which must end in `v<major-version>`, as in
    `google.feature.v1`. For major versions 0 and 1, the suffix can
    be omitted. Zero major versions must only be used for
    experimental, non-GA interfaces.
    """
    syntax: google.protobuf.type_pb2.Syntax.ValueType
    """The source syntax of the service."""
    edition: builtins.str
    """The source edition string, only valid when syntax is SYNTAX_EDITIONS."""
    @property
    def methods(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___Method
    ]: ...
    @property
    def options(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        google.protobuf.type_pb2.Option
    ]: ...
    @property
    def source_context(
        self,
    ) -> google.protobuf.source_context_pb2.SourceContext: ...
    @property
    def mixins(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___Mixin
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        methods: collections.abc.Iterable[global___Method] | None = ...,
        options: collections.abc.Iterable[google.protobuf.type_pb2.Option]
        | None = ...,
        version: builtins.str | None = ...,
        source_context: google.protobuf.source_context_pb2.SourceContext
        | None = ...,
        mixins: collections.abc.Iterable[global___Mixin] | None = ...,
        syntax: google.protobuf.type_pb2.Syntax.ValueType | None = ...,
        edition: builtins.str | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["source_context", b"source_context"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "edition",
            b"edition",
            "methods",
            b"methods",
            "mixins",
            b"mixins",
            "name",
            b"name",
            "options",
            b"options",
            "source_context",
            b"source_context",
            "syntax",
            b"syntax",
            "version",
            b"version",
        ],
    ) -> None: ...

global___Api = Api

@typing.final
class Method(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    REQUEST_TYPE_URL_FIELD_NUMBER: builtins.int
    REQUEST_STREAMING_FIELD_NUMBER: builtins.int
    RESPONSE_TYPE_URL_FIELD_NUMBER: builtins.int
    RESPONSE_STREAMING_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    SYNTAX_FIELD_NUMBER: builtins.int
    EDITION_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The simple name of this method."""
    request_type_url: builtins.str
    """A URL of the input message type."""
    request_streaming: builtins.bool
    """If true, the request is streamed."""
    response_type_url: builtins.str
    """The URL of the output message type."""
    response_streaming: builtins.bool
    """If true, the response is streamed."""
    syntax: google.protobuf.type_pb2.Syntax.ValueType
    """The source syntax of this method.

    This field should be ignored, instead the syntax should be inherited from
    Api. This is similar to Field and EnumValue.
    """
    edition: builtins.str
    """The source edition string, only valid when syntax is SYNTAX_EDITIONS.

    This field should be ignored, instead the edition should be inherited from
    Api. This is similar to Field and EnumValue.
    """
    @property
    def options(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        google.protobuf.type_pb2.Option
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        request_type_url: builtins.str | None = ...,
        request_streaming: builtins.bool | None = ...,
        response_type_url: builtins.str | None = ...,
        response_streaming: builtins.bool | None = ...,
        options: collections.abc.Iterable[google.protobuf.type_pb2.Option]
        | None = ...,
        syntax: google.protobuf.type_pb2.Syntax.ValueType | None = ...,
        edition: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "edition",
            b"edition",
            "name",
            b"name",
            "options",
            b"options",
            "request_streaming",
            b"request_streaming",
            "request_type_url",
            b"request_type_url",
            "response_streaming",
            b"response_streaming",
            "response_type_url",
            b"response_type_url",
            "syntax",
            b"syntax",
        ],
    ) -> None: ...

global___Method = Method

@typing.final
class Mixin(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    ROOT_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The fully qualified name of the interface which is included."""
    root: builtins.str
    """If non-empty specifies a path under which inherited HTTP paths
    are rooted.
    """
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        root: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name", "root", b"root"],
    ) -> None: ...

global___Mixin = Mixin
