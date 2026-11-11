import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.attr_value_pb2
import tensorflow.core.framework.full_type_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class NodeDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class AttrEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(
            self,
        ) -> tensorflow.core.framework.attr_value_pb2.AttrValue: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: tensorflow.core.framework.attr_value_pb2.AttrValue
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    @typing.final
    class ExperimentalDebugInfo(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ORIGINAL_NODE_NAMES_FIELD_NUMBER: builtins.int
        ORIGINAL_FUNC_NAMES_FIELD_NUMBER: builtins.int
        @property
        def original_node_names(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.str
        ]: ...
        @property
        def original_func_names(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.str
        ]: ...
        def __init__(
            self,
            *,
            original_node_names: collections.abc.Iterable[builtins.str]
            | None = ...,
            original_func_names: collections.abc.Iterable[builtins.str]
            | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "original_func_names",
                b"original_func_names",
                "original_node_names",
                b"original_node_names",
            ],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    OP_FIELD_NUMBER: builtins.int
    INPUT_FIELD_NUMBER: builtins.int
    DEVICE_FIELD_NUMBER: builtins.int
    ATTR_FIELD_NUMBER: builtins.int
    EXPERIMENTAL_DEBUG_INFO_FIELD_NUMBER: builtins.int
    EXPERIMENTAL_TYPE_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The name given to this operator. Used for naming inputs,
    logging, visualization, etc.  Unique within a single GraphDef.
    Must match the regexp "[A-Za-z0-9.][A-Za-z0-9_>./]*".
    """
    op: builtins.str
    """The operation name.  There may be custom parameters in attrs.
    Op names starting with an underscore are reserved for internal use.
    """
    device: builtins.str
    """A (possibly partial) specification for the device on which this
    node should be placed.
    The expected syntax for this string is as follows:

    DEVICE_SPEC ::= PARTIAL_SPEC

    PARTIAL_SPEC ::= ("/" CONSTRAINT) *
    CONSTRAINT ::= ("job:" JOB_NAME)
                 | ("replica:" [1-9][0-9]*)
                 | ("task:" [1-9][0-9]*)
                 | ("device:" [A-Za-z]* ":" ([1-9][0-9]* | "*") )

    Valid values for this string include:
    * "/job:worker/replica:0/task:1/device:GPU:3"  (full specification)
    * "/job:worker/device:GPU:3"                   (partial specification)
    * ""                                    (no specification)

    If the constraints do not resolve to a single device (or if this
    field is empty or not present), the runtime will attempt to
    choose a device automatically.
    """
    @property
    def input(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    @property
    def attr(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        tensorflow.core.framework.attr_value_pb2.AttrValue,
    ]: ...
    @property
    def experimental_debug_info(
        self,
    ) -> global___NodeDef.ExperimentalDebugInfo: ...
    @property
    def experimental_type(
        self,
    ) -> tensorflow.core.framework.full_type_pb2.FullTypeDef: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        op: builtins.str | None = ...,
        input: collections.abc.Iterable[builtins.str] | None = ...,
        device: builtins.str | None = ...,
        attr: collections.abc.Mapping[
            builtins.str,
            tensorflow.core.framework.attr_value_pb2.AttrValue,
        ]
        | None = ...,
        experimental_debug_info: global___NodeDef.ExperimentalDebugInfo
        | None = ...,
        experimental_type: tensorflow.core.framework.full_type_pb2.FullTypeDef
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "experimental_debug_info",
            b"experimental_debug_info",
            "experimental_type",
            b"experimental_type",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "attr",
            b"attr",
            "device",
            b"device",
            "experimental_debug_info",
            b"experimental_debug_info",
            "experimental_type",
            b"experimental_type",
            "input",
            b"input",
            "name",
            b"name",
            "op",
            b"op",
        ],
    ) -> None: ...

global___NodeDef = NodeDef
