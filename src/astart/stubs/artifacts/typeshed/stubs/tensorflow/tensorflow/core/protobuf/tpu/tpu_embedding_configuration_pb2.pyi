import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import tensorflow.core.protobuf.tpu.optimization_parameters_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class TPUEmbeddingConfiguration(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Mode:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ModeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            TPUEmbeddingConfiguration._Mode.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNSPECIFIED: TPUEmbeddingConfiguration._Mode.ValueType
        INFERENCE: TPUEmbeddingConfiguration._Mode.ValueType
        TRAINING: TPUEmbeddingConfiguration._Mode.ValueType
        BACKWARD_PASS_ONLY: TPUEmbeddingConfiguration._Mode.ValueType

    class Mode(_Mode, metaclass=_ModeEnumTypeWrapper): ...
    UNSPECIFIED: TPUEmbeddingConfiguration.Mode.ValueType
    INFERENCE: TPUEmbeddingConfiguration.Mode.ValueType
    TRAINING: TPUEmbeddingConfiguration.Mode.ValueType
    BACKWARD_PASS_ONLY: TPUEmbeddingConfiguration.Mode.ValueType
    class _ShardingStrategy:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ShardingStrategyEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            TPUEmbeddingConfiguration._ShardingStrategy.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        DIV_DEFAULT: TPUEmbeddingConfiguration._ShardingStrategy.ValueType
        MOD: TPUEmbeddingConfiguration._ShardingStrategy.ValueType

    class ShardingStrategy(
        _ShardingStrategy,
        metaclass=_ShardingStrategyEnumTypeWrapper,
    ): ...
    DIV_DEFAULT: TPUEmbeddingConfiguration.ShardingStrategy.ValueType
    MOD: TPUEmbeddingConfiguration.ShardingStrategy.ValueType
    @typing.final
    class TableDescriptor(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_FIELD_NUMBER: builtins.int
        VOCABULARY_SIZE_FIELD_NUMBER: builtins.int
        DIMENSION_FIELD_NUMBER: builtins.int
        NUM_FEATURES_FIELD_NUMBER: builtins.int
        OPTIMIZATION_PARAMETERS_FIELD_NUMBER: builtins.int
        name: builtins.str
        """Name of the table."""
        vocabulary_size: builtins.int
        """Size of the vocabulary (i.e., number of rows) in the table."""
        dimension: builtins.int
        """The embedding dimension (i.e., the width of the embedding table)."""
        num_features: builtins.int
        """Number of features mapped to this table."""
        @property
        def optimization_parameters(
            self,
        ) -> tensorflow.core.protobuf.tpu.optimization_parameters_pb2.OptimizationParameters: ...
        def __init__(
            self,
            *,
            name: builtins.str | None = ...,
            vocabulary_size: builtins.int | None = ...,
            dimension: builtins.int | None = ...,
            num_features: builtins.int | None = ...,
            optimization_parameters: tensorflow.core.protobuf.tpu.optimization_parameters_pb2.OptimizationParameters
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "optimization_parameters",
                b"optimization_parameters",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "dimension",
                b"dimension",
                "name",
                b"name",
                "num_features",
                b"num_features",
                "optimization_parameters",
                b"optimization_parameters",
                "vocabulary_size",
                b"vocabulary_size",
            ],
        ) -> None: ...

    @typing.final
    class FeatureDescriptor(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_FIELD_NUMBER: builtins.int
        TABLE_ID_FIELD_NUMBER: builtins.int
        INPUT_SHAPE_FIELD_NUMBER: builtins.int
        name: builtins.str
        """Name of the input feature."""
        table_id: builtins.int
        """Index of the corresponding table in the TableDescriptor list."""
        @property
        def input_shape(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        def __init__(
            self,
            *,
            name: builtins.str | None = ...,
            table_id: builtins.int | None = ...,
            input_shape: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "input_shape",
                b"input_shape",
                "name",
                b"name",
                "table_id",
                b"table_id",
            ],
        ) -> None: ...

    @typing.final
    class SpmdSharding(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        ENABLED_FIELD_NUMBER: builtins.int
        NUM_CORES_PER_REPLICA_FIELD_NUMBER: builtins.int
        enabled: builtins.bool
        """Whether SPMD sharding is enabled."""
        num_cores_per_replica: builtins.int
        """Number of cores per replica."""
        def __init__(
            self,
            *,
            enabled: builtins.bool | None = ...,
            num_cores_per_replica: builtins.int | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "enabled",
                b"enabled",
                "num_cores_per_replica",
                b"num_cores_per_replica",
            ],
        ) -> None: ...

    TABLE_DESCRIPTOR_FIELD_NUMBER: builtins.int
    MODE_FIELD_NUMBER: builtins.int
    BATCH_SIZE_PER_TENSOR_CORE_FIELD_NUMBER: builtins.int
    NUM_HOSTS_FIELD_NUMBER: builtins.int
    NUM_TENSOR_CORES_FIELD_NUMBER: builtins.int
    SHARDING_STRATEGY_FIELD_NUMBER: builtins.int
    PIPELINE_EXECUTION_WITH_TENSOR_CORE_FIELD_NUMBER: builtins.int
    PROFILE_DATA_DIRECTORY_FIELD_NUMBER: builtins.int
    FEATURE_DESCRIPTOR_FIELD_NUMBER: builtins.int
    SPMD_SHARDING_FIELD_NUMBER: builtins.int
    mode: global___TPUEmbeddingConfiguration.Mode.ValueType
    batch_size_per_tensor_core: builtins.int
    """Number of samples in each batch of embedding layer activations sent to
    the TensorCore.
    """
    num_hosts: builtins.int
    """Number of TPU hosts used for inference/training."""
    num_tensor_cores: builtins.int
    """Number of TensorCore used for inference/training."""
    sharding_strategy: (
        global___TPUEmbeddingConfiguration.ShardingStrategy.ValueType
    )
    pipeline_execution_with_tensor_core: builtins.bool
    """This parameter determines if the execution of the sparse core will be
    pipelined with that of the TensorCore. This parameter only affects results
    when mode=TRAINING. If mode=INFERENCE or BACKWARD_PASS_ONLY, this parameter
    does not affect execution and hence, is a don't care value.

    false: The execution of the sparse core is not pipelined with that of the
    TensorCore. The forward pass of every step on the sparse core is executed
    only after the backward pass of the previous step is complete. And the
    backward pass on the sparse core is executed only after the embedding
    gradients have been computed on the TensorCore on every step. This ensures
    that the activations on every step observe the gradient updates from the
    previous step on both the sparse core and the TensorCore.

    true: The execution of the sparse core is pipelined with that of the
    TensorCore. The forward pass of every step on the sparse core can be
    executed after the forward pass of the previous step is complete without
    waiting for the backward pass. This improves the utilization of the sparse
    core allowing it to process step N+1 while the embedding gradients for step
    N are computed on the TensorCore. The backward pass of every step on the
    sparse core is executed directly after the forward pass for the next step
    is complete. The drawback is that embedding activations for step N+1 do not
    observe the embedding gradient updates from step N. This could affect model
    quality if step N and N+1 involve the same set of embedding IDs. However,
    since the embedding updates are sparse, this is generally not considered a
    problem.
    """
    profile_data_directory: builtins.str
    """Directory where embedding lookup statistics are stored. These statistics
    summarize information about the inputs to the embedding lookup
    operation, in particular, the average number of embedding IDs per example
    and how well the embedding IDs are load balanced across the system. The
    lookup statistics are used during TPU initialization for embedding table
    partitioning. Collection of lookup statistics is done at runtime by
    profiling the embedding inputs: only 3% of input samples are profiled to
    minimize host CPU overhead. Once a suitable number of samples are
    profiled, the lookup statistics are saved to table-specific files in the
    profile data directory generally at the end of a TPU training loop. The
    filename corresponding to each table is obtained by hashing table specific
    parameters (e.g., table name and number of features) and global
    configuration parameters (e.g., sharding strategy and TPU worker task
    count). The same profile data directory can be shared amongst several
    models to reuse embedding lookup statistics.
    """
    @property
    def table_descriptor(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___TPUEmbeddingConfiguration.TableDescriptor
    ]: ...
    @property
    def feature_descriptor(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___TPUEmbeddingConfiguration.FeatureDescriptor
    ]: ...
    @property
    def spmd_sharding(
        self,
    ) -> global___TPUEmbeddingConfiguration.SpmdSharding: ...
    def __init__(
        self,
        *,
        table_descriptor: collections.abc.Iterable[
            global___TPUEmbeddingConfiguration.TableDescriptor
        ]
        | None = ...,
        mode: global___TPUEmbeddingConfiguration.Mode.ValueType | None = ...,
        batch_size_per_tensor_core: builtins.int | None = ...,
        num_hosts: builtins.int | None = ...,
        num_tensor_cores: builtins.int | None = ...,
        sharding_strategy: global___TPUEmbeddingConfiguration.ShardingStrategy.ValueType
        | None = ...,
        pipeline_execution_with_tensor_core: builtins.bool | None = ...,
        profile_data_directory: builtins.str | None = ...,
        feature_descriptor: collections.abc.Iterable[
            global___TPUEmbeddingConfiguration.FeatureDescriptor
        ]
        | None = ...,
        spmd_sharding: global___TPUEmbeddingConfiguration.SpmdSharding
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["spmd_sharding", b"spmd_sharding"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "batch_size_per_tensor_core",
            b"batch_size_per_tensor_core",
            "feature_descriptor",
            b"feature_descriptor",
            "mode",
            b"mode",
            "num_hosts",
            b"num_hosts",
            "num_tensor_cores",
            b"num_tensor_cores",
            "pipeline_execution_with_tensor_core",
            b"pipeline_execution_with_tensor_core",
            "profile_data_directory",
            b"profile_data_directory",
            "sharding_strategy",
            b"sharding_strategy",
            "spmd_sharding",
            b"spmd_sharding",
            "table_descriptor",
            b"table_descriptor",
        ],
    ) -> None: ...

global___TPUEmbeddingConfiguration = TPUEmbeddingConfiguration

@typing.final
class TPUEmbeddingError(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    def __init__(self) -> None: ...

global___TPUEmbeddingError = TPUEmbeddingError
