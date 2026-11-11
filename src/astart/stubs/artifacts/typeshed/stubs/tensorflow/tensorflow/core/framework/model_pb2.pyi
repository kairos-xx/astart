import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _NodeClass:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _NodeClassEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _NodeClass.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    UNKNOWN: _NodeClass.ValueType
    INTERLEAVE_MANY: _NodeClass.ValueType
    ASYNC_INTERLEAVE_MANY: _NodeClass.ValueType
    KNOWN_RATIO: _NodeClass.ValueType
    ASYNC_KNOWN_RATIO: _NodeClass.ValueType
    UNKNOWN_RATIO: _NodeClass.ValueType
    ASYNC_UNKNOWN_RATIO: _NodeClass.ValueType

class NodeClass(_NodeClass, metaclass=_NodeClassEnumTypeWrapper): ...

UNKNOWN: NodeClass.ValueType
INTERLEAVE_MANY: NodeClass.ValueType
ASYNC_INTERLEAVE_MANY: NodeClass.ValueType
KNOWN_RATIO: NodeClass.ValueType
ASYNC_KNOWN_RATIO: NodeClass.ValueType
UNKNOWN_RATIO: NodeClass.ValueType
ASYNC_UNKNOWN_RATIO: NodeClass.ValueType
global___NodeClass = NodeClass

class _AutotuneAlgorithm:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _AutotuneAlgorithmEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _AutotuneAlgorithm.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    DEFAULT: _AutotuneAlgorithm.ValueType
    HILL_CLIMB: _AutotuneAlgorithm.ValueType
    GRADIENT_DESCENT: _AutotuneAlgorithm.ValueType
    MAX_PARALLELISM: _AutotuneAlgorithm.ValueType
    STAGE_BASED: _AutotuneAlgorithm.ValueType

class AutotuneAlgorithm(
    _AutotuneAlgorithm,
    metaclass=_AutotuneAlgorithmEnumTypeWrapper,
): ...

DEFAULT: AutotuneAlgorithm.ValueType
HILL_CLIMB: AutotuneAlgorithm.ValueType
GRADIENT_DESCENT: AutotuneAlgorithm.ValueType
MAX_PARALLELISM: AutotuneAlgorithm.ValueType
STAGE_BASED: AutotuneAlgorithm.ValueType
global___AutotuneAlgorithm = AutotuneAlgorithm

@typing.final
class ModelProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class Node(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        @typing.final
        class Parameter(google.protobuf.message.Message):
            DESCRIPTOR: google.protobuf.descriptor.Descriptor
            NAME_FIELD_NUMBER: builtins.int
            VALUE_FIELD_NUMBER: builtins.int
            STATE_VALUE_FIELD_NUMBER: builtins.int
            MIN_FIELD_NUMBER: builtins.int
            MAX_FIELD_NUMBER: builtins.int
            TUNABLE_FIELD_NUMBER: builtins.int
            name: builtins.str
            """Human-readable name of the parameter."""
            value: builtins.float
            """Identifies the model value of the parameter. This can be different from
            the actual value (e.g. during optimization search).
            """
            state_value: builtins.float
            """The actual value of the parameter."""
            min: builtins.float
            """Minimum value of the parameter."""
            max: builtins.float
            """Maximum value of the parameter."""
            tunable: builtins.bool
            """Identifies whether the parameter should participate in autotuning."""
            def __init__(
                self,
                *,
                name: builtins.str | None = ...,
                value: builtins.float | None = ...,
                state_value: builtins.float | None = ...,
                min: builtins.float | None = ...,
                max: builtins.float | None = ...,
                tunable: builtins.bool | None = ...,
            ) -> None: ...
            def ClearField(
                self,
                field_name: typing.Literal[
                    "max",
                    b"max",
                    "min",
                    b"min",
                    "name",
                    b"name",
                    "state_value",
                    b"state_value",
                    "tunable",
                    b"tunable",
                    "value",
                    b"value",
                ],
            ) -> None: ...

        ID_FIELD_NUMBER: builtins.int
        NAME_FIELD_NUMBER: builtins.int
        AUTOTUNE_FIELD_NUMBER: builtins.int
        BUFFERED_BYTES_FIELD_NUMBER: builtins.int
        BUFFERED_ELEMENTS_FIELD_NUMBER: builtins.int
        BYTES_CONSUMED_FIELD_NUMBER: builtins.int
        BYTES_PRODUCED_FIELD_NUMBER: builtins.int
        NUM_ELEMENTS_FIELD_NUMBER: builtins.int
        PROCESSING_TIME_FIELD_NUMBER: builtins.int
        RECORD_METRICS_FIELD_NUMBER: builtins.int
        PARAMETERS_FIELD_NUMBER: builtins.int
        INPUT_PROCESSING_TIME_SUM_FIELD_NUMBER: builtins.int
        INPUT_PROCESSING_TIME_COUNT_FIELD_NUMBER: builtins.int
        INPUTS_FIELD_NUMBER: builtins.int
        NODE_CLASS_FIELD_NUMBER: builtins.int
        RATIO_FIELD_NUMBER: builtins.int
        MEMORY_RATIO_FIELD_NUMBER: builtins.int
        id: builtins.int
        """Unique node ID."""
        name: builtins.str
        """Human-readable name of the node."""
        autotune: builtins.bool
        """An indication whether autotuning is enabled for this node."""
        buffered_bytes: builtins.int
        """The number of bytes stored in this node's buffer."""
        buffered_elements: builtins.int
        """The number of elements stored in this node's buffer."""
        bytes_consumed: builtins.int
        """The number of bytes consumed by the node."""
        bytes_produced: builtins.int
        """The number of bytes produced by the node."""
        num_elements: builtins.int
        """The number of elements produced by the node."""
        processing_time: builtins.int
        """The aggregate processing time spent in this node in nanoseconds."""
        record_metrics: builtins.bool
        """An indication whether this node records metrics about produced and
        consumed elements.
        """
        input_processing_time_sum: builtins.float
        """Statistic of inputs processing time history."""
        input_processing_time_count: builtins.int
        node_class: global___NodeClass.ValueType
        """Class of this node."""
        ratio: builtins.float
        """Ratio of input to output elements. This is only used by KNOWN_RATIO and
        ASYNC_KNOWN_RATIO nodes.
        """
        memory_ratio: builtins.float
        """Ratio identifies how many parallelism calls are introduced by one
        buffered element. This is only used by ASYNC_KNOWN_RATIO nodes.
        """
        @property
        def parameters(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            global___ModelProto.Node.Parameter
        ]: ...
        @property
        def inputs(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        def __init__(
            self,
            *,
            id: builtins.int | None = ...,
            name: builtins.str | None = ...,
            autotune: builtins.bool | None = ...,
            buffered_bytes: builtins.int | None = ...,
            buffered_elements: builtins.int | None = ...,
            bytes_consumed: builtins.int | None = ...,
            bytes_produced: builtins.int | None = ...,
            num_elements: builtins.int | None = ...,
            processing_time: builtins.int | None = ...,
            record_metrics: builtins.bool | None = ...,
            parameters: collections.abc.Iterable[
                global___ModelProto.Node.Parameter
            ]
            | None = ...,
            input_processing_time_sum: builtins.float | None = ...,
            input_processing_time_count: builtins.int | None = ...,
            inputs: collections.abc.Iterable[builtins.int] | None = ...,
            node_class: global___NodeClass.ValueType | None = ...,
            ratio: builtins.float | None = ...,
            memory_ratio: builtins.float | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "autotune",
                b"autotune",
                "buffered_bytes",
                b"buffered_bytes",
                "buffered_elements",
                b"buffered_elements",
                "bytes_consumed",
                b"bytes_consumed",
                "bytes_produced",
                b"bytes_produced",
                "id",
                b"id",
                "input_processing_time_count",
                b"input_processing_time_count",
                "input_processing_time_sum",
                b"input_processing_time_sum",
                "inputs",
                b"inputs",
                "memory_ratio",
                b"memory_ratio",
                "name",
                b"name",
                "node_class",
                b"node_class",
                "num_elements",
                b"num_elements",
                "parameters",
                b"parameters",
                "processing_time",
                b"processing_time",
                "ratio",
                b"ratio",
                "record_metrics",
                b"record_metrics",
            ],
        ) -> None: ...

    @typing.final
    class NodesEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.int
        @property
        def value(self) -> global___ModelProto.Node: ...
        def __init__(
            self,
            *,
            key: builtins.int | None = ...,
            value: global___ModelProto.Node | None = ...,
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
    class OptimizationParams(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ALGORITHM_FIELD_NUMBER: builtins.int
        CPU_BUDGET_FIELD_NUMBER: builtins.int
        RAM_BUDGET_FIELD_NUMBER: builtins.int
        MODEL_INPUT_TIME_FIELD_NUMBER: builtins.int
        algorithm: global___AutotuneAlgorithm.ValueType
        """Algorithm used for autotuning optimization."""
        cpu_budget: builtins.int
        """Number of available logical threads."""
        ram_budget: builtins.int
        """Amount of available memory in bytes."""
        model_input_time: builtins.float
        """Time between two consecutive `GetNext` calls to the iterator represented
        by the output node.
        """
        def __init__(
            self,
            *,
            algorithm: global___AutotuneAlgorithm.ValueType | None = ...,
            cpu_budget: builtins.int | None = ...,
            ram_budget: builtins.int | None = ...,
            model_input_time: builtins.float | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "algorithm",
                b"algorithm",
                "cpu_budget",
                b"cpu_budget",
                "model_input_time",
                b"model_input_time",
                "ram_budget",
                b"ram_budget",
            ],
        ) -> None: ...

    DATASET_NAME_FIELD_NUMBER: builtins.int
    NODES_FIELD_NUMBER: builtins.int
    OUTPUT_FIELD_NUMBER: builtins.int
    ID_COUNTER_FIELD_NUMBER: builtins.int
    OPTIMIZATION_PARAMS_FIELD_NUMBER: builtins.int
    GAP_TIMES_FIELD_NUMBER: builtins.int
    dataset_name: builtins.str
    """User-defined name for the dataset. Empty if no name was set."""
    output: builtins.int
    """ID of the output node of this model."""
    id_counter: builtins.int
    """Counter for node IDs of this model."""
    @property
    def nodes(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.int,
        global___ModelProto.Node,
    ]: ...
    @property
    def optimization_params(
        self,
    ) -> global___ModelProto.OptimizationParams: ...
    @property
    def gap_times(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        dataset_name: builtins.str | None = ...,
        nodes: collections.abc.Mapping[builtins.int, global___ModelProto.Node]
        | None = ...,
        output: builtins.int | None = ...,
        id_counter: builtins.int | None = ...,
        optimization_params: global___ModelProto.OptimizationParams
        | None = ...,
        gap_times: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "optimization_params",
            b"optimization_params",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dataset_name",
            b"dataset_name",
            "gap_times",
            b"gap_times",
            "id_counter",
            b"id_counter",
            "nodes",
            b"nodes",
            "optimization_params",
            b"optimization_params",
            "output",
            b"output",
        ],
    ) -> None: ...

global___ModelProto = ModelProto
