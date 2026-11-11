import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import google.protobuf.wrappers_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class TrackableObjectGraph(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class TrackableObject(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        @typing.final
        class ObjectReference(google.protobuf.message.Message):
            DESCRIPTOR: google.protobuf.descriptor.Descriptor
            NODE_ID_FIELD_NUMBER: builtins.int
            LOCAL_NAME_FIELD_NUMBER: builtins.int
            node_id: builtins.int
            """An index into `TrackableObjectGraph.nodes`, indicating the object
            being referenced.
            """
            local_name: builtins.str
            """A user-provided name for the edge."""
            def __init__(
                self,
                *,
                node_id: builtins.int | None = ...,
                local_name: builtins.str | None = ...,
            ) -> None: ...
            def ClearField(
                self,
                field_name: typing.Literal[
                    "local_name",
                    b"local_name",
                    "node_id",
                    b"node_id",
                ],
            ) -> None: ...

        @typing.final
        class SerializedTensor(google.protobuf.message.Message):
            DESCRIPTOR: google.protobuf.descriptor.Descriptor
            NAME_FIELD_NUMBER: builtins.int
            FULL_NAME_FIELD_NUMBER: builtins.int
            CHECKPOINT_KEY_FIELD_NUMBER: builtins.int
            name: builtins.str
            """A name for the Tensor. Simple variables have only one
            `SerializedTensor` named "VARIABLE_VALUE" by convention. This value may
            be restored on object creation as an optimization.
            """
            full_name: builtins.str
            """The full name of the variable/tensor, if applicable. Used to allow
            name-based loading of checkpoints which were saved using an
            object-based API. Should match the checkpoint key which would have been
            assigned by tf.train.Saver.
            """
            checkpoint_key: builtins.str
            """The generated name of the Tensor in the checkpoint."""
            def __init__(
                self,
                *,
                name: builtins.str | None = ...,
                full_name: builtins.str | None = ...,
                checkpoint_key: builtins.str | None = ...,
            ) -> None: ...
            def ClearField(
                self,
                field_name: typing.Literal[
                    "checkpoint_key",
                    b"checkpoint_key",
                    "full_name",
                    b"full_name",
                    "name",
                    b"name",
                ],
            ) -> None: ...

        @typing.final
        class SlotVariableReference(google.protobuf.message.Message):
            DESCRIPTOR: google.protobuf.descriptor.Descriptor
            ORIGINAL_VARIABLE_NODE_ID_FIELD_NUMBER: builtins.int
            SLOT_NAME_FIELD_NUMBER: builtins.int
            SLOT_VARIABLE_NODE_ID_FIELD_NUMBER: builtins.int
            original_variable_node_id: builtins.int
            """An index into `TrackableObjectGraph.nodes`, indicating the
            variable object this slot was created for.
            """
            slot_name: builtins.str
            """The name of the slot (e.g. "m"/"v")."""
            slot_variable_node_id: builtins.int
            """An index into `TrackableObjectGraph.nodes`, indicating the
            `Object` with the value of the slot variable.
            """
            def __init__(
                self,
                *,
                original_variable_node_id: builtins.int | None = ...,
                slot_name: builtins.str | None = ...,
                slot_variable_node_id: builtins.int | None = ...,
            ) -> None: ...
            def ClearField(
                self,
                field_name: typing.Literal[
                    "original_variable_node_id",
                    b"original_variable_node_id",
                    "slot_name",
                    b"slot_name",
                    "slot_variable_node_id",
                    b"slot_variable_node_id",
                ],
            ) -> None: ...

        CHILDREN_FIELD_NUMBER: builtins.int
        ATTRIBUTES_FIELD_NUMBER: builtins.int
        SLOT_VARIABLES_FIELD_NUMBER: builtins.int
        REGISTERED_SAVER_FIELD_NUMBER: builtins.int
        HAS_CHECKPOINT_VALUES_FIELD_NUMBER: builtins.int
        @property
        def children(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            global___TrackableObjectGraph.TrackableObject.ObjectReference
        ]: ...
        @property
        def attributes(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            global___TrackableObjectGraph.TrackableObject.SerializedTensor
        ]: ...
        @property
        def slot_variables(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            global___TrackableObjectGraph.TrackableObject.SlotVariableReference
        ]: ...
        @property
        def registered_saver(self) -> global___RegisteredSaver: ...
        @property
        def has_checkpoint_values(
            self,
        ) -> google.protobuf.wrappers_pb2.BoolValue: ...
        def __init__(
            self,
            *,
            children: collections.abc.Iterable[
                global___TrackableObjectGraph.TrackableObject.ObjectReference
            ]
            | None = ...,
            attributes: collections.abc.Iterable[
                global___TrackableObjectGraph.TrackableObject.SerializedTensor
            ]
            | None = ...,
            slot_variables: (
                collections.abc.Iterable[
                    global___TrackableObjectGraph.TrackableObject.SlotVariableReference
                ]
                | None
            ) = ...,
            registered_saver: global___RegisteredSaver | None = ...,
            has_checkpoint_values: google.protobuf.wrappers_pb2.BoolValue
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "has_checkpoint_values",
                b"has_checkpoint_values",
                "registered_saver",
                b"registered_saver",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "attributes",
                b"attributes",
                "children",
                b"children",
                "has_checkpoint_values",
                b"has_checkpoint_values",
                "registered_saver",
                b"registered_saver",
                "slot_variables",
                b"slot_variables",
            ],
        ) -> None: ...

    NODES_FIELD_NUMBER: builtins.int
    @property
    def nodes(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___TrackableObjectGraph.TrackableObject
    ]: ...
    def __init__(
        self,
        *,
        nodes: collections.abc.Iterable[
            global___TrackableObjectGraph.TrackableObject
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["nodes", b"nodes"],
    ) -> None: ...

global___TrackableObjectGraph = TrackableObjectGraph

@typing.final
class RegisteredSaver(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    OBJECT_NAME_FIELD_NUMBER: builtins.int
    name: builtins.str
    """The name of the registered saver/restore function."""
    object_name: builtins.str
    """Unique auto-generated name of the object."""
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        object_name: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "object_name",
            b"object_name",
        ],
    ) -> None: ...

global___RegisteredSaver = RegisteredSaver
