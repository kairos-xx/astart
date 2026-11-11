import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.attr_value_pb2
import tensorflow.core.framework.node_def_pb2
import tensorflow.core.framework.op_def_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class FunctionDefLibrary(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FUNCTION_FIELD_NUMBER: builtins.int
    GRADIENT_FIELD_NUMBER: builtins.int
    REGISTERED_GRADIENTS_FIELD_NUMBER: builtins.int
    @property
    def function(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FunctionDef
    ]: ...
    @property
    def gradient(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___GradientDef
    ]: ...
    @property
    def registered_gradients(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___RegisteredGradient
    ]: ...
    def __init__(
        self,
        *,
        function: collections.abc.Iterable[global___FunctionDef] | None = ...,
        gradient: collections.abc.Iterable[global___GradientDef] | None = ...,
        registered_gradients: collections.abc.Iterable[
            global___RegisteredGradient
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "function",
            b"function",
            "gradient",
            b"gradient",
            "registered_gradients",
            b"registered_gradients",
        ],
    ) -> None: ...

global___FunctionDefLibrary = FunctionDefLibrary

@typing.final
class FunctionDef(google.protobuf.message.Message):
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
    class ArgAttrs(google.protobuf.message.Message):
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

        ATTR_FIELD_NUMBER: builtins.int
        @property
        def attr(
            self,
        ) -> google.protobuf.internal.containers.MessageMap[
            builtins.str,
            tensorflow.core.framework.attr_value_pb2.AttrValue,
        ]: ...
        def __init__(
            self,
            *,
            attr: collections.abc.Mapping[
                builtins.str,
                tensorflow.core.framework.attr_value_pb2.AttrValue,
            ]
            | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["attr", b"attr"],
        ) -> None: ...

    @typing.final
    class ArgAttrEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.int
        @property
        def value(self) -> global___FunctionDef.ArgAttrs: ...
        def __init__(
            self,
            *,
            key: builtins.int | None = ...,
            value: global___FunctionDef.ArgAttrs | None = ...,
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
    class ResourceArgUniqueIdEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.int
        value: builtins.int
        def __init__(
            self,
            *,
            key: builtins.int | None = ...,
            value: builtins.int | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    @typing.final
    class RetEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: builtins.str | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    @typing.final
    class ControlRetEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        value: builtins.str
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: builtins.str | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    SIGNATURE_FIELD_NUMBER: builtins.int
    ATTR_FIELD_NUMBER: builtins.int
    ARG_ATTR_FIELD_NUMBER: builtins.int
    RESOURCE_ARG_UNIQUE_ID_FIELD_NUMBER: builtins.int
    NODE_DEF_FIELD_NUMBER: builtins.int
    RET_FIELD_NUMBER: builtins.int
    CONTROL_RET_FIELD_NUMBER: builtins.int
    @property
    def signature(self) -> tensorflow.core.framework.op_def_pb2.OpDef: ...
    @property
    def attr(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        tensorflow.core.framework.attr_value_pb2.AttrValue,
    ]: ...
    @property
    def arg_attr(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.int,
        global___FunctionDef.ArgAttrs,
    ]: ...
    @property
    def resource_arg_unique_id(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.int,
        builtins.int,
    ]: ...
    @property
    def node_def(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        tensorflow.core.framework.node_def_pb2.NodeDef
    ]: ...
    @property
    def ret(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.str,
        builtins.str,
    ]: ...
    @property
    def control_ret(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.str,
        builtins.str,
    ]: ...
    def __init__(
        self,
        *,
        signature: tensorflow.core.framework.op_def_pb2.OpDef | None = ...,
        attr: collections.abc.Mapping[
            builtins.str,
            tensorflow.core.framework.attr_value_pb2.AttrValue,
        ]
        | None = ...,
        arg_attr: collections.abc.Mapping[
            builtins.int,
            global___FunctionDef.ArgAttrs,
        ]
        | None = ...,
        resource_arg_unique_id: collections.abc.Mapping[
            builtins.int,
            builtins.int,
        ]
        | None = ...,
        node_def: collections.abc.Iterable[
            tensorflow.core.framework.node_def_pb2.NodeDef
        ]
        | None = ...,
        ret: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
        control_ret: collections.abc.Mapping[builtins.str, builtins.str]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["signature", b"signature"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "arg_attr",
            b"arg_attr",
            "attr",
            b"attr",
            "control_ret",
            b"control_ret",
            "node_def",
            b"node_def",
            "resource_arg_unique_id",
            b"resource_arg_unique_id",
            "ret",
            b"ret",
            "signature",
            b"signature",
        ],
    ) -> None: ...

global___FunctionDef = FunctionDef

@typing.final
class GradientDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FUNCTION_NAME_FIELD_NUMBER: builtins.int
    GRADIENT_FUNC_FIELD_NUMBER: builtins.int
    function_name: builtins.str
    """The function name."""
    gradient_func: builtins.str
    """The gradient function's name."""
    def __init__(
        self,
        *,
        function_name: builtins.str | None = ...,
        gradient_func: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "function_name",
            b"function_name",
            "gradient_func",
            b"gradient_func",
        ],
    ) -> None: ...

global___GradientDef = GradientDef

@typing.final
class RegisteredGradient(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    GRADIENT_FUNC_FIELD_NUMBER: builtins.int
    REGISTERED_OP_TYPE_FIELD_NUMBER: builtins.int
    gradient_func: builtins.str
    """The gradient function's name."""
    registered_op_type: builtins.str
    """The gradient function's registered op type."""
    def __init__(
        self,
        *,
        gradient_func: builtins.str | None = ...,
        registered_op_type: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "gradient_func",
            b"gradient_func",
            "registered_op_type",
            b"registered_op_type",
        ],
    ) -> None: ...

global___RegisteredGradient = RegisteredGradient
