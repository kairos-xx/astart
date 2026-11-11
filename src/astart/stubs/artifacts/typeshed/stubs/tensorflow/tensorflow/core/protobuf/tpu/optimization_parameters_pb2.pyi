import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.wrappers_pb2
import tensorflow.compiler.xla.service.hlo_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class ClippingLimits(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LOWER_FIELD_NUMBER: builtins.int
    UPPER_FIELD_NUMBER: builtins.int
    @property
    def lower(self) -> google.protobuf.wrappers_pb2.FloatValue: ...
    @property
    def upper(self) -> google.protobuf.wrappers_pb2.FloatValue: ...
    def __init__(
        self,
        *,
        lower: google.protobuf.wrappers_pb2.FloatValue | None = ...,
        upper: google.protobuf.wrappers_pb2.FloatValue | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["lower", b"lower", "upper", b"upper"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["lower", b"lower", "upper", b"upper"],
    ) -> None: ...

global___ClippingLimits = ClippingLimits

@typing.final
class SimulatedQuantization(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    ENABLED_FIELD_NUMBER: builtins.int
    CLIPPING_LIMITS_FIELD_NUMBER: builtins.int
    NUM_BUCKETS_FIELD_NUMBER: builtins.int
    enabled: builtins.bool
    """Whether simulated quantization is enabled."""
    num_buckets: builtins.int
    """Number of possible quantized values."""
    @property
    def clipping_limits(self) -> global___ClippingLimits: ...
    def __init__(
        self,
        *,
        enabled: builtins.bool | None = ...,
        clipping_limits: global___ClippingLimits | None = ...,
        num_buckets: builtins.int | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["clipping_limits", b"clipping_limits"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "clipping_limits",
            b"clipping_limits",
            "enabled",
            b"enabled",
            "num_buckets",
            b"num_buckets",
        ],
    ) -> None: ...

global___SimulatedQuantization = SimulatedQuantization

@typing.final
class DynamicLearningRate(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TAG_FIELD_NUMBER: builtins.int
    tag: builtins.int
    """For tables where learning rates are dynamically computed and communicated
    to the TPU embedding program, a tag must be specified for the learning
    rate.

    The tag must be a non-negative  integer. The total number of unique tags
    must be less than or equal to the number of tables in the TPU embedding
    configuration (a table does not specify any tag if it uses a constant
    learning rate, and specifies exactly one tag if it uses dynamic learning
    rates).

    All tags in the range [0, number_of_unique_tags) must be present in the TPU
    embedding configuration, i.e. a tag cannot be skipped if a different tag
    numerically greater than it is used in the configuration.

    If multiple tables specify the same tag, they *MUST* have
    the same dynamic learning rate, for example, their dynamic learning rate
    could be computed by the same TensorFlow sub-graph. The partitioning of the
    embedding layer would be more optimal if the number_of_unique_tags is as
    *LOW* as possible, i.e., if many tables share the same tag.

    The learning_rate input of the SendTPUEmbeddingGradients op is used to
    communicate dynamic learning rates to the TPU embedding program.
    The learning_rate input is a list of scalars where the size of the list is
    equal to the number of unique tags. The learning rate associated with a
    particular tag is specified by populating its corresponding index in the
    list of learning_rate scalars.
    """
    def __init__(self, *, tag: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["tag", b"tag"],
    ) -> None: ...

global___DynamicLearningRate = DynamicLearningRate

@typing.final
class LearningRate(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    CONSTANT_FIELD_NUMBER: builtins.int
    DYNAMIC_FIELD_NUMBER: builtins.int
    constant: builtins.float
    @property
    def dynamic(self) -> global___DynamicLearningRate: ...
    def __init__(
        self,
        *,
        constant: builtins.float | None = ...,
        dynamic: global___DynamicLearningRate | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "constant",
            b"constant",
            "dynamic",
            b"dynamic",
            "learning_rate",
            b"learning_rate",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "constant",
            b"constant",
            "dynamic",
            b"dynamic",
            "learning_rate",
            b"learning_rate",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["learning_rate", b"learning_rate"],
    ) -> typing.Literal["constant", "dynamic"] | None: ...

global___LearningRate = LearningRate

@typing.final
class AdagradParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    def __init__(self) -> None: ...

global___AdagradParameters = AdagradParameters

@typing.final
class AdagradMomentumParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    MOMENTUM_FIELD_NUMBER: builtins.int
    USE_NESTEROV_FIELD_NUMBER: builtins.int
    EXPONENT_FIELD_NUMBER: builtins.int
    BETA2_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    momentum: builtins.float
    """Moving average parameter for the momentum accumulator."""
    use_nesterov: builtins.bool
    """Whether to use the Nesterov variant of momentum."""
    exponent: builtins.float
    """Exponent for the gradient^2 accumulator."""
    beta2: builtins.float
    """Moving average parameter for the gradient^2 accumulator."""
    epsilon: builtins.float
    """Offset added to the Adagrad accumulator."""
    def __init__(
        self,
        *,
        momentum: builtins.float | None = ...,
        use_nesterov: builtins.bool | None = ...,
        exponent: builtins.float | None = ...,
        beta2: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "beta2",
            b"beta2",
            "epsilon",
            b"epsilon",
            "exponent",
            b"exponent",
            "momentum",
            b"momentum",
            "use_nesterov",
            b"use_nesterov",
        ],
    ) -> None: ...

global___AdagradMomentumParameters = AdagradMomentumParameters

@typing.final
class BoundedAdagradParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    UPDATE_ACCUMULATOR_FIRST_FIELD_NUMBER: builtins.int
    MAX_VAR_UPDATE_FIELD_NUMBER: builtins.int
    MAX_ACCUMULATOR_FIELD_NUMBER: builtins.int
    update_accumulator_first: builtins.bool
    """Whether to use the updated or the old value of the accumulator when
    computing the effective learning rate. When update_accumulator_first is set
    to True, the updated value of the accumulator is used.
    """
    max_var_update: builtins.float
    """The max_var_update value to use. Set value to 0 (default) to disable using
    max_var_update to clip the gradient.
    """
    max_accumulator: builtins.float
    """The maximum value of the accumulator. Set max_accumulator to 0 (default)
    to disable using max_accumulator to clip the accumulator.
    """
    def __init__(
        self,
        *,
        update_accumulator_first: builtins.bool | None = ...,
        max_var_update: builtins.float | None = ...,
        max_accumulator: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "max_accumulator",
            b"max_accumulator",
            "max_var_update",
            b"max_var_update",
            "update_accumulator_first",
            b"update_accumulator_first",
        ],
    ) -> None: ...

global___BoundedAdagradParameters = BoundedAdagradParameters

@typing.final
class StochasticGradientDescentParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    def __init__(self) -> None: ...

global___StochasticGradientDescentParameters = (
    StochasticGradientDescentParameters
)

@typing.final
class FtrlParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    L1_FIELD_NUMBER: builtins.int
    L2_FIELD_NUMBER: builtins.int
    LR_POWER_FIELD_NUMBER: builtins.int
    BETA_FIELD_NUMBER: builtins.int
    MULTIPLY_LINEAR_BY_LR_FIELD_NUMBER: builtins.int
    ALLOW_ZERO_ACCUMULATOR_FIELD_NUMBER: builtins.int
    l1: builtins.float
    l2: builtins.float
    lr_power: builtins.float
    beta: builtins.float
    multiply_linear_by_lr: builtins.bool
    allow_zero_accumulator: builtins.bool
    """Previously, allow_zero_accumulator parameter changed some internal formulas
    to allow zero and near-zero accumulator values at the cost of some
    performance. The current implementation ignores this parameter; zero or
    near-zero accumulator values are now always supported.
    """
    def __init__(
        self,
        *,
        l1: builtins.float | None = ...,
        l2: builtins.float | None = ...,
        lr_power: builtins.float | None = ...,
        beta: builtins.float | None = ...,
        multiply_linear_by_lr: builtins.bool | None = ...,
        allow_zero_accumulator: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "allow_zero_accumulator",
            b"allow_zero_accumulator",
            "beta",
            b"beta",
            "l1",
            b"l1",
            "l2",
            b"l2",
            "lr_power",
            b"lr_power",
            "multiply_linear_by_lr",
            b"multiply_linear_by_lr",
        ],
    ) -> None: ...

global___FtrlParameters = FtrlParameters

@typing.final
class AdamParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    BETA1_FIELD_NUMBER: builtins.int
    BETA2_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    USE_NON_LAZY_ADAM_FIELD_NUMBER: builtins.int
    USE_SUM_INSIDE_SQRT_FIELD_NUMBER: builtins.int
    beta1: builtins.float
    beta2: builtins.float
    epsilon: builtins.float
    use_non_lazy_adam: builtins.bool
    use_sum_inside_sqrt: builtins.bool
    def __init__(
        self,
        *,
        beta1: builtins.float | None = ...,
        beta2: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
        use_non_lazy_adam: builtins.bool | None = ...,
        use_sum_inside_sqrt: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "beta1",
            b"beta1",
            "beta2",
            b"beta2",
            "epsilon",
            b"epsilon",
            "use_non_lazy_adam",
            b"use_non_lazy_adam",
            "use_sum_inside_sqrt",
            b"use_sum_inside_sqrt",
        ],
    ) -> None: ...

global___AdamParameters = AdamParameters

@typing.final
class MomentumParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    MOMENTUM_FIELD_NUMBER: builtins.int
    USE_NESTEROV_FIELD_NUMBER: builtins.int
    momentum: builtins.float
    use_nesterov: builtins.bool
    def __init__(
        self,
        *,
        momentum: builtins.float | None = ...,
        use_nesterov: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "momentum",
            b"momentum",
            "use_nesterov",
            b"use_nesterov",
        ],
    ) -> None: ...

global___MomentumParameters = MomentumParameters

@typing.final
class LionParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    BETA1_FIELD_NUMBER: builtins.int
    BETA2_FIELD_NUMBER: builtins.int
    USE_NON_LAZY_LION_FIELD_NUMBER: builtins.int
    beta1: builtins.float
    beta2: builtins.float
    use_non_lazy_lion: builtins.bool
    def __init__(
        self,
        *,
        beta1: builtins.float | None = ...,
        beta2: builtins.float | None = ...,
        use_non_lazy_lion: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "beta1",
            b"beta1",
            "beta2",
            b"beta2",
            "use_non_lazy_lion",
            b"use_non_lazy_lion",
        ],
    ) -> None: ...

global___LionParameters = LionParameters

@typing.final
class RmsPropParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    RHO_FIELD_NUMBER: builtins.int
    MOMENTUM_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    rho: builtins.float
    momentum: builtins.float
    epsilon: builtins.float
    def __init__(
        self,
        *,
        rho: builtins.float | None = ...,
        momentum: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "epsilon",
            b"epsilon",
            "momentum",
            b"momentum",
            "rho",
            b"rho",
        ],
    ) -> None: ...

global___RmsPropParameters = RmsPropParameters

@typing.final
class CenteredRmsPropParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    RHO_FIELD_NUMBER: builtins.int
    MOMENTUM_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    rho: builtins.float
    momentum: builtins.float
    epsilon: builtins.float
    def __init__(
        self,
        *,
        rho: builtins.float | None = ...,
        momentum: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "epsilon",
            b"epsilon",
            "momentum",
            b"momentum",
            "rho",
            b"rho",
        ],
    ) -> None: ...

global___CenteredRmsPropParameters = CenteredRmsPropParameters

@typing.final
class MdlAdagradLightParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    L2_FIELD_NUMBER: builtins.int
    LR_POWER_FIELD_NUMBER: builtins.int
    MIN_SERVABLE_MDL_BENEFIT_FIELD_NUMBER: builtins.int
    MDL_MIX_IN_MARGIN_FIELD_NUMBER: builtins.int
    MDL_BENEFIT_RAMPUP_COEFF_FIELD_NUMBER: builtins.int
    MDL_MIN_WEIGHT_FIELD_NUMBER: builtins.int
    BENEFIT_REVISIT_SCALE_FIELD_NUMBER: builtins.int
    MAX_EVENT_BENEFIT_FIELD_NUMBER: builtins.int
    MAX_TOTAL_BENEFIT_FIELD_NUMBER: builtins.int
    MDL_HARD_LIMIT_FIELD_NUMBER: builtins.int
    HARD_LIMIT_MIN_BENEFIT_FIELD_NUMBER: builtins.int
    MDL_REGULARIZE_FIELD_NUMBER: builtins.int
    l2: builtins.float
    lr_power: builtins.float
    min_servable_mdl_benefit: builtins.float
    mdl_mix_in_margin: builtins.float
    mdl_benefit_rampup_coeff: builtins.float
    mdl_min_weight: builtins.float
    benefit_revisit_scale: builtins.float
    max_event_benefit: builtins.float
    max_total_benefit: builtins.float
    mdl_hard_limit: builtins.float
    hard_limit_min_benefit: builtins.bool
    mdl_regularize: builtins.bool
    def __init__(
        self,
        *,
        l2: builtins.float | None = ...,
        lr_power: builtins.float | None = ...,
        min_servable_mdl_benefit: builtins.float | None = ...,
        mdl_mix_in_margin: builtins.float | None = ...,
        mdl_benefit_rampup_coeff: builtins.float | None = ...,
        mdl_min_weight: builtins.float | None = ...,
        benefit_revisit_scale: builtins.float | None = ...,
        max_event_benefit: builtins.float | None = ...,
        max_total_benefit: builtins.float | None = ...,
        mdl_hard_limit: builtins.float | None = ...,
        hard_limit_min_benefit: builtins.bool | None = ...,
        mdl_regularize: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "benefit_revisit_scale",
            b"benefit_revisit_scale",
            "hard_limit_min_benefit",
            b"hard_limit_min_benefit",
            "l2",
            b"l2",
            "lr_power",
            b"lr_power",
            "max_event_benefit",
            b"max_event_benefit",
            "max_total_benefit",
            b"max_total_benefit",
            "mdl_benefit_rampup_coeff",
            b"mdl_benefit_rampup_coeff",
            "mdl_hard_limit",
            b"mdl_hard_limit",
            "mdl_min_weight",
            b"mdl_min_weight",
            "mdl_mix_in_margin",
            b"mdl_mix_in_margin",
            "mdl_regularize",
            b"mdl_regularize",
            "min_servable_mdl_benefit",
            b"min_servable_mdl_benefit",
        ],
    ) -> None: ...

global___MdlAdagradLightParameters = MdlAdagradLightParameters

@typing.final
class AdadeltaParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    RHO_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    rho: builtins.float
    epsilon: builtins.float
    def __init__(
        self,
        *,
        rho: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["epsilon", b"epsilon", "rho", b"rho"],
    ) -> None: ...

global___AdadeltaParameters = AdadeltaParameters

@typing.final
class ProximalAdagradParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    L1_FIELD_NUMBER: builtins.int
    L2_FIELD_NUMBER: builtins.int
    l1: builtins.float
    l2: builtins.float
    def __init__(
        self,
        *,
        l1: builtins.float | None = ...,
        l2: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["l1", b"l1", "l2", b"l2"],
    ) -> None: ...

global___ProximalAdagradParameters = ProximalAdagradParameters

@typing.final
class OnlineYogiParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    L1_FIELD_NUMBER: builtins.int
    L2_FIELD_NUMBER: builtins.int
    BETA2_FIELD_NUMBER: builtins.int
    l1: builtins.float
    """The L1 regularization parameter (used analogously to the one in FTRL)."""
    l2: builtins.float
    """The L2 regularization parameter (used analogously to the one in FTRL)."""
    beta2: builtins.float
    """\\beta_2 from Algorithm 2 in the paper."""
    def __init__(
        self,
        *,
        l1: builtins.float | None = ...,
        l2: builtins.float | None = ...,
        beta2: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "beta2",
            b"beta2",
            "l1",
            b"l1",
            "l2",
            b"l2",
        ],
    ) -> None: ...

global___OnlineYogiParameters = OnlineYogiParameters

@typing.final
class ProximalYogiParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    L1_FIELD_NUMBER: builtins.int
    L2_FIELD_NUMBER: builtins.int
    BETA1_FIELD_NUMBER: builtins.int
    BETA2_FIELD_NUMBER: builtins.int
    EPSILON_FIELD_NUMBER: builtins.int
    l1: builtins.float
    """The L1 regularization parameter."""
    l2: builtins.float
    """The L2 regularization parameter."""
    beta1: builtins.float
    """The exponential decay rate for the 1st moment estimates."""
    beta2: builtins.float
    """The exponential decay rate for the 2nd moment estimates."""
    epsilon: builtins.float
    """A constant trading off adaptivity and noise."""
    def __init__(
        self,
        *,
        l1: builtins.float | None = ...,
        l2: builtins.float | None = ...,
        beta1: builtins.float | None = ...,
        beta2: builtins.float | None = ...,
        epsilon: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "beta1",
            b"beta1",
            "beta2",
            b"beta2",
            "epsilon",
            b"epsilon",
            "l1",
            b"l1",
            "l2",
            b"l2",
        ],
    ) -> None: ...

global___ProximalYogiParameters = ProximalYogiParameters

@typing.final
class FrequencyEstimatorParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TAU_FIELD_NUMBER: builtins.int
    MAX_DELTA_FIELD_NUMBER: builtins.int
    OUTLIER_THRESHOLD_FIELD_NUMBER: builtins.int
    WEIGHT_EXPONENT_FIELD_NUMBER: builtins.int
    tau: builtins.float
    """Learning rate between (0, 1) that is used to update the array D."""
    max_delta: builtins.float
    """Maximum value of delta: difference between the current global step and the
    last global step at which the row was sampled.
    """
    outlier_threshold: builtins.float
    """Threshold used to determine whether the current update is an outlier."""
    weight_exponent: builtins.float
    """The weight exponent used to transform the estimated delta into weights.
    The transformation function is: (delta / max_delta) ^ (weight_exponent)
    """
    def __init__(
        self,
        *,
        tau: builtins.float | None = ...,
        max_delta: builtins.float | None = ...,
        outlier_threshold: builtins.float | None = ...,
        weight_exponent: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "max_delta",
            b"max_delta",
            "outlier_threshold",
            b"outlier_threshold",
            "tau",
            b"tau",
            "weight_exponent",
            b"weight_exponent",
        ],
    ) -> None: ...

global___FrequencyEstimatorParameters = FrequencyEstimatorParameters

@typing.final
class UserDefinedProgramParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    PROGRAM_FIELD_NUMBER: builtins.int
    @property
    def program(
        self,
    ) -> tensorflow.compiler.xla.service.hlo_pb2.HloModuleProto: ...
    def __init__(
        self,
        *,
        program: tensorflow.compiler.xla.service.hlo_pb2.HloModuleProto
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["program", b"program"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["program", b"program"],
    ) -> None: ...

global___UserDefinedProgramParameters = UserDefinedProgramParameters

@typing.final
class AssignParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    def __init__(self) -> None: ...

global___AssignParameters = AssignParameters

@typing.final
class GradientAccumulationStatus(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Status:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _StatusEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            GradientAccumulationStatus._Status.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNSPECIFIED: GradientAccumulationStatus._Status.ValueType
        ENABLED: GradientAccumulationStatus._Status.ValueType
        DISABLED: GradientAccumulationStatus._Status.ValueType

    class Status(_Status, metaclass=_StatusEnumTypeWrapper): ...
    UNSPECIFIED: GradientAccumulationStatus.Status.ValueType
    ENABLED: GradientAccumulationStatus.Status.ValueType
    DISABLED: GradientAccumulationStatus.Status.ValueType
    def __init__(self) -> None: ...

global___GradientAccumulationStatus = GradientAccumulationStatus

@typing.final
class LowDimensionalPackingStatus(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Status:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _StatusEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            LowDimensionalPackingStatus._Status.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNSPECIFIED: LowDimensionalPackingStatus._Status.ValueType
        ENABLED: LowDimensionalPackingStatus._Status.ValueType
        DISABLED: LowDimensionalPackingStatus._Status.ValueType

    class Status(_Status, metaclass=_StatusEnumTypeWrapper): ...
    UNSPECIFIED: LowDimensionalPackingStatus.Status.ValueType
    ENABLED: LowDimensionalPackingStatus.Status.ValueType
    DISABLED: LowDimensionalPackingStatus.Status.ValueType
    def __init__(self) -> None: ...

global___LowDimensionalPackingStatus = LowDimensionalPackingStatus

@typing.final
class HotIdReplicationConfiguration(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Status:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _StatusEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            HotIdReplicationConfiguration._Status.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNSPECIFIED: HotIdReplicationConfiguration._Status.ValueType
        ENABLED: HotIdReplicationConfiguration._Status.ValueType
        DISABLED: HotIdReplicationConfiguration._Status.ValueType
        MIGRATION_ONLY: HotIdReplicationConfiguration._Status.ValueType

    class Status(_Status, metaclass=_StatusEnumTypeWrapper): ...
    UNSPECIFIED: HotIdReplicationConfiguration.Status.ValueType
    ENABLED: HotIdReplicationConfiguration.Status.ValueType
    DISABLED: HotIdReplicationConfiguration.Status.ValueType
    MIGRATION_ONLY: HotIdReplicationConfiguration.Status.ValueType
    STATUS_FIELD_NUMBER: builtins.int
    status: global___HotIdReplicationConfiguration.Status.ValueType
    def __init__(
        self,
        *,
        status: global___HotIdReplicationConfiguration.Status.ValueType
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["status", b"status"],
    ) -> None: ...

global___HotIdReplicationConfiguration = HotIdReplicationConfiguration

@typing.final
class OptimizationParameters(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LEARNING_RATE_FIELD_NUMBER: builtins.int
    CLIPPING_LIMITS_FIELD_NUMBER: builtins.int
    GRADIENT_CLIPPING_LIMITS_FIELD_NUMBER: builtins.int
    WEIGHT_DECAY_FACTOR_FIELD_NUMBER: builtins.int
    MULTIPLY_WEIGHT_DECAY_FACTOR_BY_LEARNING_RATE_FIELD_NUMBER: builtins.int
    SIMULATED_QUANTIZATION_FIELD_NUMBER: builtins.int
    GRADIENT_ACCUMULATION_STATUS_FIELD_NUMBER: builtins.int
    LOW_DIMENSIONAL_PACKING_STATUS_FIELD_NUMBER: builtins.int
    HOT_ID_REPLICATION_CONFIGURATION_FIELD_NUMBER: builtins.int
    ADAGRAD_FIELD_NUMBER: builtins.int
    ADAGRAD_MOMENTUM_FIELD_NUMBER: builtins.int
    BOUNDED_ADAGRAD_FIELD_NUMBER: builtins.int
    STOCHASTIC_GRADIENT_DESCENT_FIELD_NUMBER: builtins.int
    FTRL_FIELD_NUMBER: builtins.int
    ADAM_FIELD_NUMBER: builtins.int
    MOMENTUM_FIELD_NUMBER: builtins.int
    LION_FIELD_NUMBER: builtins.int
    RMS_PROP_FIELD_NUMBER: builtins.int
    CENTERED_RMS_PROP_FIELD_NUMBER: builtins.int
    MDL_ADAGRAD_LIGHT_FIELD_NUMBER: builtins.int
    ADADELTA_FIELD_NUMBER: builtins.int
    PROXIMAL_ADAGRAD_FIELD_NUMBER: builtins.int
    ONLINE_YOGI_FIELD_NUMBER: builtins.int
    PROXIMAL_YOGI_FIELD_NUMBER: builtins.int
    FREQUENCY_ESTIMATOR_FIELD_NUMBER: builtins.int
    USER_DEFINED_PROGRAM_FIELD_NUMBER: builtins.int
    ASSIGN_FIELD_NUMBER: builtins.int
    weight_decay_factor: builtins.float
    """Amount of weight decay to apply; see weight_decay_optimizers.py for
    details. All optimizers except MDL Adagrad Light are supported with this
    option. Although there is no check, users who want weight decay will also
    want to ensure that gradient accumulation is enabled so that the decay will
    happen once per global batch.
    """
    multiply_weight_decay_factor_by_learning_rate: builtins.bool
    """If true, the weight decay factor is multiplied by the current learning rate
    before use; this is to match the note in DecoupledWeightDecayExtension in
    weight_decay_optimizers.py.
    """
    gradient_accumulation_status: (
        global___GradientAccumulationStatus.Status.ValueType
    )
    """Status of using gradient accumulation (doing two passes over the input
    gradients: one to accumulate them into a temporary array and another to
    apply them using the actual optimization algorithm).
    """
    low_dimensional_packing_status: (
        global___LowDimensionalPackingStatus.Status.ValueType
    )
    """Status of the low-dimensional embedding packing optimization. This controls
    whether to optimize the packing of 1-dimensional, 2-dimensional, and
    4-dimensional embedding tables in memory.
    """
    @property
    def learning_rate(self) -> global___LearningRate: ...
    @property
    def clipping_limits(self) -> global___ClippingLimits: ...
    @property
    def gradient_clipping_limits(self) -> global___ClippingLimits: ...
    @property
    def simulated_quantization(self) -> global___SimulatedQuantization: ...
    @property
    def hot_id_replication_configuration(
        self,
    ) -> global___HotIdReplicationConfiguration: ...
    @property
    def adagrad(self) -> global___AdagradParameters: ...
    @property
    def adagrad_momentum(self) -> global___AdagradMomentumParameters: ...
    @property
    def bounded_adagrad(self) -> global___BoundedAdagradParameters: ...
    @property
    def stochastic_gradient_descent(
        self,
    ) -> global___StochasticGradientDescentParameters: ...
    @property
    def ftrl(self) -> global___FtrlParameters: ...
    @property
    def adam(self) -> global___AdamParameters: ...
    @property
    def momentum(self) -> global___MomentumParameters: ...
    @property
    def lion(self) -> global___LionParameters: ...
    @property
    def rms_prop(self) -> global___RmsPropParameters: ...
    @property
    def centered_rms_prop(self) -> global___CenteredRmsPropParameters: ...
    @property
    def mdl_adagrad_light(self) -> global___MdlAdagradLightParameters: ...
    @property
    def adadelta(self) -> global___AdadeltaParameters: ...
    @property
    def proximal_adagrad(self) -> global___ProximalAdagradParameters: ...
    @property
    def online_yogi(self) -> global___OnlineYogiParameters: ...
    @property
    def proximal_yogi(self) -> global___ProximalYogiParameters: ...
    @property
    def frequency_estimator(self) -> global___FrequencyEstimatorParameters: ...
    @property
    def user_defined_program(
        self,
    ) -> global___UserDefinedProgramParameters: ...
    @property
    def assign(self) -> global___AssignParameters: ...
    def __init__(
        self,
        *,
        learning_rate: global___LearningRate | None = ...,
        clipping_limits: global___ClippingLimits | None = ...,
        gradient_clipping_limits: global___ClippingLimits | None = ...,
        weight_decay_factor: builtins.float | None = ...,
        multiply_weight_decay_factor_by_learning_rate: builtins.bool
        | None = ...,
        simulated_quantization: global___SimulatedQuantization | None = ...,
        gradient_accumulation_status: global___GradientAccumulationStatus.Status.ValueType
        | None = ...,
        low_dimensional_packing_status: global___LowDimensionalPackingStatus.Status.ValueType
        | None = ...,
        hot_id_replication_configuration: global___HotIdReplicationConfiguration
        | None = ...,
        adagrad: global___AdagradParameters | None = ...,
        adagrad_momentum: global___AdagradMomentumParameters | None = ...,
        bounded_adagrad: global___BoundedAdagradParameters | None = ...,
        stochastic_gradient_descent: global___StochasticGradientDescentParameters
        | None = ...,
        ftrl: global___FtrlParameters | None = ...,
        adam: global___AdamParameters | None = ...,
        momentum: global___MomentumParameters | None = ...,
        lion: global___LionParameters | None = ...,
        rms_prop: global___RmsPropParameters | None = ...,
        centered_rms_prop: global___CenteredRmsPropParameters | None = ...,
        mdl_adagrad_light: global___MdlAdagradLightParameters | None = ...,
        adadelta: global___AdadeltaParameters | None = ...,
        proximal_adagrad: global___ProximalAdagradParameters | None = ...,
        online_yogi: global___OnlineYogiParameters | None = ...,
        proximal_yogi: global___ProximalYogiParameters | None = ...,
        frequency_estimator: global___FrequencyEstimatorParameters
        | None = ...,
        user_defined_program: global___UserDefinedProgramParameters
        | None = ...,
        assign: global___AssignParameters | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "adadelta",
            b"adadelta",
            "adagrad",
            b"adagrad",
            "adagrad_momentum",
            b"adagrad_momentum",
            "adam",
            b"adam",
            "assign",
            b"assign",
            "bounded_adagrad",
            b"bounded_adagrad",
            "centered_rms_prop",
            b"centered_rms_prop",
            "clipping_limits",
            b"clipping_limits",
            "frequency_estimator",
            b"frequency_estimator",
            "ftrl",
            b"ftrl",
            "gradient_clipping_limits",
            b"gradient_clipping_limits",
            "hot_id_replication_configuration",
            b"hot_id_replication_configuration",
            "learning_rate",
            b"learning_rate",
            "lion",
            b"lion",
            "mdl_adagrad_light",
            b"mdl_adagrad_light",
            "momentum",
            b"momentum",
            "online_yogi",
            b"online_yogi",
            "parameters",
            b"parameters",
            "proximal_adagrad",
            b"proximal_adagrad",
            "proximal_yogi",
            b"proximal_yogi",
            "rms_prop",
            b"rms_prop",
            "simulated_quantization",
            b"simulated_quantization",
            "stochastic_gradient_descent",
            b"stochastic_gradient_descent",
            "user_defined_program",
            b"user_defined_program",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "adadelta",
            b"adadelta",
            "adagrad",
            b"adagrad",
            "adagrad_momentum",
            b"adagrad_momentum",
            "adam",
            b"adam",
            "assign",
            b"assign",
            "bounded_adagrad",
            b"bounded_adagrad",
            "centered_rms_prop",
            b"centered_rms_prop",
            "clipping_limits",
            b"clipping_limits",
            "frequency_estimator",
            b"frequency_estimator",
            "ftrl",
            b"ftrl",
            "gradient_accumulation_status",
            b"gradient_accumulation_status",
            "gradient_clipping_limits",
            b"gradient_clipping_limits",
            "hot_id_replication_configuration",
            b"hot_id_replication_configuration",
            "learning_rate",
            b"learning_rate",
            "lion",
            b"lion",
            "low_dimensional_packing_status",
            b"low_dimensional_packing_status",
            "mdl_adagrad_light",
            b"mdl_adagrad_light",
            "momentum",
            b"momentum",
            "multiply_weight_decay_factor_by_learning_rate",
            b"multiply_weight_decay_factor_by_learning_rate",
            "online_yogi",
            b"online_yogi",
            "parameters",
            b"parameters",
            "proximal_adagrad",
            b"proximal_adagrad",
            "proximal_yogi",
            b"proximal_yogi",
            "rms_prop",
            b"rms_prop",
            "simulated_quantization",
            b"simulated_quantization",
            "stochastic_gradient_descent",
            b"stochastic_gradient_descent",
            "user_defined_program",
            b"user_defined_program",
            "weight_decay_factor",
            b"weight_decay_factor",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["parameters", b"parameters"],
    ) -> (
        typing.Literal[
            "adagrad",
            "adagrad_momentum",
            "bounded_adagrad",
            "stochastic_gradient_descent",
            "ftrl",
            "adam",
            "momentum",
            "lion",
            "rms_prop",
            "centered_rms_prop",
            "mdl_adagrad_light",
            "adadelta",
            "proximal_adagrad",
            "online_yogi",
            "proximal_yogi",
            "frequency_estimator",
            "user_defined_program",
            "assign",
        ]
        | None
    ): ...

global___OptimizationParameters = OptimizationParameters

@typing.final
class StateVariableSpecification(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class UserDefined(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        def __init__(self) -> None: ...

    @typing.final
    class FillWithConstant(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        INITIAL_VALUE_FIELD_NUMBER: builtins.int
        initial_value: builtins.float
        def __init__(
            self,
            *,
            initial_value: builtins.float | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["initial_value", b"initial_value"],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    USER_DEFINED_FIELD_NUMBER: builtins.int
    FILL_WITH_CONSTANT_FIELD_NUMBER: builtins.int
    name: builtins.str
    """Parameter name for the state variable."""
    @property
    def user_defined(
        self,
    ) -> global___StateVariableSpecification.UserDefined: ...
    @property
    def fill_with_constant(
        self,
    ) -> global___StateVariableSpecification.FillWithConstant: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        user_defined: global___StateVariableSpecification.UserDefined
        | None = ...,
        fill_with_constant: global___StateVariableSpecification.FillWithConstant
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "fill_with_constant",
            b"fill_with_constant",
            "usage",
            b"usage",
            "user_defined",
            b"user_defined",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "fill_with_constant",
            b"fill_with_constant",
            "name",
            b"name",
            "usage",
            b"usage",
            "user_defined",
            b"user_defined",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["usage", b"usage"],
    ) -> typing.Literal["user_defined", "fill_with_constant"] | None: ...

global___StateVariableSpecification = StateVariableSpecification
