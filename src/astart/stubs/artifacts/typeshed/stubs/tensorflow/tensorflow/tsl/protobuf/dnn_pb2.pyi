import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message
import google.protobuf.wrappers_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _DataType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _DataTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _DataType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    kFloat: _DataType.ValueType
    kDouble: _DataType.ValueType
    kHalf: _DataType.ValueType
    kInt8: _DataType.ValueType
    kInt32: _DataType.ValueType
    kComplexFloat: _DataType.ValueType
    kComplexDouble: _DataType.ValueType
    kBF16: _DataType.ValueType
    kF8E5M2: _DataType.ValueType
    kF8E4M3FN: _DataType.ValueType
    kF8E5M2FNUZ: _DataType.ValueType
    kF8E4M3FNUZ: _DataType.ValueType
    kInt64: _DataType.ValueType

class DataType(_DataType, metaclass=_DataTypeEnumTypeWrapper): ...

kFloat: DataType.ValueType
kDouble: DataType.ValueType
kHalf: DataType.ValueType
kInt8: DataType.ValueType
kInt32: DataType.ValueType
kComplexFloat: DataType.ValueType
kComplexDouble: DataType.ValueType
kBF16: DataType.ValueType
kF8E5M2: DataType.ValueType
kF8E4M3FN: DataType.ValueType
kF8E5M2FNUZ: DataType.ValueType
kF8E4M3FNUZ: DataType.ValueType
kInt64: DataType.ValueType
global___DataType = DataType

class _DataLayout:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _DataLayoutEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _DataLayout.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    kYXDepthBatch: _DataLayout.ValueType
    """Naming convention:
    Y <-> row or height
    X <-> column or width
    Batch <-> batch, or N
    Depth <-> feature, or channel
    TODO(timshen): turn them into cuDNN names, e.g. kNCHW.

    Note: In cudnn, kBatchDepthYX4 and kBatchDepthYX32 are the same layout
    (namely, NCHW_VECT_C).  It differentiates between these two by using a
    different data type (int8x4 vs int8x32).  In StreamExecutor we use
    different layouts for these, because we don't usually pass an explicit data
    type to StreamExecutor functions.
    """
    kYXBatchDepth: _DataLayout.ValueType
    kBatchYXDepth: _DataLayout.ValueType
    """cuDNN's NHWC layout"""
    kBatchDepthYX: _DataLayout.ValueType
    """cuDNN's NCHW layout"""
    kBatchDepthYX4: _DataLayout.ValueType
    """cuDNN's NCHW_VECT_C with 4-elem vectors (e.g. int8x4)"""
    kBatchDepthYX32: _DataLayout.ValueType
    """cuDNN's NCHW_VECT_C with 32-elem vects (e.g. int8x32)"""

class DataLayout(_DataLayout, metaclass=_DataLayoutEnumTypeWrapper): ...

kYXDepthBatch: DataLayout.ValueType
"""Naming convention:
Y <-> row or height
X <-> column or width
Batch <-> batch, or N
Depth <-> feature, or channel
TODO(timshen): turn them into cuDNN names, e.g. kNCHW.

Note: In cudnn, kBatchDepthYX4 and kBatchDepthYX32 are the same layout
(namely, NCHW_VECT_C).  It differentiates between these two by using a
different data type (int8x4 vs int8x32).  In StreamExecutor we use
different layouts for these, because we don't usually pass an explicit data
type to StreamExecutor functions.
"""
kYXBatchDepth: DataLayout.ValueType
kBatchYXDepth: DataLayout.ValueType
"""cuDNN's NHWC layout"""
kBatchDepthYX: DataLayout.ValueType
"""cuDNN's NCHW layout"""
kBatchDepthYX4: DataLayout.ValueType
"""cuDNN's NCHW_VECT_C with 4-elem vectors (e.g. int8x4)"""
kBatchDepthYX32: DataLayout.ValueType
"""cuDNN's NCHW_VECT_C with 32-elem vects (e.g. int8x32)"""
global___DataLayout = DataLayout

class _FilterLayout:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _FilterLayoutEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _FilterLayout.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    kOutputInputYX: _FilterLayout.ValueType
    """Naming convention:
    Y <-> row or height
    X <-> column or width
    Output <-> output feature, or N
    Input <-> input feature, or N
    TODO(timshen): turn them into cuDNN names, e.g. kNCHW.
    cuDNN's NCHW layout
    """
    kOutputYXInput: _FilterLayout.ValueType
    """cuDNN's NHWC layout"""
    kOutputInputYX4: _FilterLayout.ValueType
    """cuDNN's NCHW_VECT_C layout with 4-elem vectors"""
    kOutputInputYX32: _FilterLayout.ValueType
    """cuDNN's NCHW_VECT_C layout with 32-elem vectors"""
    kOutputInputYX32_CudnnReordered: _FilterLayout.ValueType
    """cuDNN-specific filter reordering (using `cudnnReorderFilterAndBias`)
    When the filter is reordered, so is the bias (if present).
    """
    kInputYXOutput: _FilterLayout.ValueType
    kYXInputOutput: _FilterLayout.ValueType

class FilterLayout(_FilterLayout, metaclass=_FilterLayoutEnumTypeWrapper): ...

kOutputInputYX: FilterLayout.ValueType
"""Naming convention:
Y <-> row or height
X <-> column or width
Output <-> output feature, or N
Input <-> input feature, or N
TODO(timshen): turn them into cuDNN names, e.g. kNCHW.
cuDNN's NCHW layout
"""
kOutputYXInput: FilterLayout.ValueType
"""cuDNN's NHWC layout"""
kOutputInputYX4: FilterLayout.ValueType
"""cuDNN's NCHW_VECT_C layout with 4-elem vectors"""
kOutputInputYX32: FilterLayout.ValueType
"""cuDNN's NCHW_VECT_C layout with 32-elem vectors"""
kOutputInputYX32_CudnnReordered: FilterLayout.ValueType
"""cuDNN-specific filter reordering (using `cudnnReorderFilterAndBias`)
When the filter is reordered, so is the bias (if present).
"""
kInputYXOutput: FilterLayout.ValueType
kYXInputOutput: FilterLayout.ValueType
global___FilterLayout = FilterLayout

class _ActivationMode:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _ActivationModeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _ActivationMode.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    kNone: _ActivationMode.ValueType
    kSigmoid: _ActivationMode.ValueType
    kRelu: _ActivationMode.ValueType
    """Rectified linear activation: f(x) = x < 0 ? 0 : x"""
    kRelu6: _ActivationMode.ValueType
    """Rectified linear activation; where upper maximum is 6.0."""
    kReluX: _ActivationMode.ValueType
    """Rectified linear activation; where upper maximum specified by
    BatchDescriptor::value_max().
    """
    kTanh: _ActivationMode.ValueType
    kBandPass: _ActivationMode.ValueType
    """Like ReluX; but passes all values in the range [-X,X]."""
    kElu: _ActivationMode.ValueType
    """Exponential linear activation: f(x) = x < 0 ? e^x - 1 : x"""
    kLeakyRelu: _ActivationMode.ValueType
    """Leaky Rectified linear activation: f(x) = x < 0 ? alpha * x : x"""
    kGeluExact: _ActivationMode.ValueType
    """Gaussian Error linear unit activation:
      x * P(X <= x) = 0.5 * x * (1 + erf(x / sqrt(2))), where P(X) ~ N(0, 1).
    """

class ActivationMode(
    _ActivationMode,
    metaclass=_ActivationModeEnumTypeWrapper,
): ...

kNone: ActivationMode.ValueType
kSigmoid: ActivationMode.ValueType
kRelu: ActivationMode.ValueType
"""Rectified linear activation: f(x) = x < 0 ? 0 : x"""
kRelu6: ActivationMode.ValueType
"""Rectified linear activation; where upper maximum is 6.0."""
kReluX: ActivationMode.ValueType
"""Rectified linear activation; where upper maximum specified by
BatchDescriptor::value_max().
"""
kTanh: ActivationMode.ValueType
kBandPass: ActivationMode.ValueType
"""Like ReluX; but passes all values in the range [-X,X]."""
kElu: ActivationMode.ValueType
"""Exponential linear activation: f(x) = x < 0 ? e^x - 1 : x"""
kLeakyRelu: ActivationMode.ValueType
"""Leaky Rectified linear activation: f(x) = x < 0 ? alpha * x : x"""
kGeluExact: ActivationMode.ValueType
"""Gaussian Error linear unit activation:
  x * P(X <= x) = 0.5 * x * (1 + erf(x / sqrt(2))), where P(X) ~ N(0, 1).
"""
global___ActivationMode = ActivationMode

class _ConvolutionMode:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _ConvolutionModeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _ConvolutionMode.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    CROSS_CORRELATION: _ConvolutionMode.ValueType
    CONVOLUTION: _ConvolutionMode.ValueType

class ConvolutionMode(
    _ConvolutionMode,
    metaclass=_ConvolutionModeEnumTypeWrapper,
): ...

CROSS_CORRELATION: ConvolutionMode.ValueType
CONVOLUTION: ConvolutionMode.ValueType
global___ConvolutionMode = ConvolutionMode

class _ConvolutionKind:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _ConvolutionKindEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _ConvolutionKind.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    INVALID: _ConvolutionKind.ValueType
    FORWARD: _ConvolutionKind.ValueType
    BACKWARD_FILTER: _ConvolutionKind.ValueType
    BACKWARD_DATA: _ConvolutionKind.ValueType
    FORWARD_BIAS_ACTIVATION: _ConvolutionKind.ValueType
    FORWARD_GRAPH: _ConvolutionKind.ValueType

class ConvolutionKind(
    _ConvolutionKind,
    metaclass=_ConvolutionKindEnumTypeWrapper,
): ...

INVALID: ConvolutionKind.ValueType
FORWARD: ConvolutionKind.ValueType
BACKWARD_FILTER: ConvolutionKind.ValueType
BACKWARD_DATA: ConvolutionKind.ValueType
FORWARD_BIAS_ACTIVATION: ConvolutionKind.ValueType
FORWARD_GRAPH: ConvolutionKind.ValueType
global___ConvolutionKind = ConvolutionKind

class _NormKind:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _NormKindEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _NormKind.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    LAYER_FWD_INFER: _NormKind.ValueType
    LAYER_FWD_TRAIN: _NormKind.ValueType
    LAYER_BWD: _NormKind.ValueType

class NormKind(_NormKind, metaclass=_NormKindEnumTypeWrapper): ...

LAYER_FWD_INFER: NormKind.ValueType
LAYER_FWD_TRAIN: NormKind.ValueType
LAYER_BWD: NormKind.ValueType
global___NormKind = NormKind

class _FusedMHAKind:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _FusedMHAKindEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _FusedMHAKind.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    BMM1_OUTPUT_UNKNOWN: _FusedMHAKind.ValueType
    BMM1_OUTPUT_INPUT_TYPE: _FusedMHAKind.ValueType
    BMM1_OUTPUT_FLOAT: _FusedMHAKind.ValueType

class FusedMHAKind(_FusedMHAKind, metaclass=_FusedMHAKindEnumTypeWrapper): ...

BMM1_OUTPUT_UNKNOWN: FusedMHAKind.ValueType
BMM1_OUTPUT_INPUT_TYPE: FusedMHAKind.ValueType
BMM1_OUTPUT_FLOAT: FusedMHAKind.ValueType
global___FusedMHAKind = FusedMHAKind

class _FMHAMaskKind:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _FMHAMaskKindEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _FMHAMaskKind.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    NO_MASK: _FMHAMaskKind.ValueType
    PADDING: _FMHAMaskKind.ValueType
    CAUSAL: _FMHAMaskKind.ValueType
    PADDING_CAUSAL: _FMHAMaskKind.ValueType
    ALIBI: _FMHAMaskKind.ValueType

class FMHAMaskKind(_FMHAMaskKind, metaclass=_FMHAMaskKindEnumTypeWrapper): ...

NO_MASK: FMHAMaskKind.ValueType
PADDING: FMHAMaskKind.ValueType
CAUSAL: FMHAMaskKind.ValueType
PADDING_CAUSAL: FMHAMaskKind.ValueType
ALIBI: FMHAMaskKind.ValueType
global___FMHAMaskKind = FMHAMaskKind

@typing.final
class TensorDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DIMENSIONS_FIELD_NUMBER: builtins.int
    DATA_TYPE_FIELD_NUMBER: builtins.int
    DATA_LAYOUT_FIELD_NUMBER: builtins.int
    FILTER_LAYOUT_FIELD_NUMBER: builtins.int
    data_type: global___DataType.ValueType
    data_layout: global___DataLayout.ValueType
    filter_layout: global___FilterLayout.ValueType
    @property
    def dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        dimensions: collections.abc.Iterable[builtins.int] | None = ...,
        data_type: global___DataType.ValueType | None = ...,
        data_layout: global___DataLayout.ValueType | None = ...,
        filter_layout: global___FilterLayout.ValueType | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "data_layout",
            b"data_layout",
            "filter_layout",
            b"filter_layout",
            "layout_oneof",
            b"layout_oneof",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "data_layout",
            b"data_layout",
            "data_type",
            b"data_type",
            "dimensions",
            b"dimensions",
            "filter_layout",
            b"filter_layout",
            "layout_oneof",
            b"layout_oneof",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["layout_oneof", b"layout_oneof"],
    ) -> typing.Literal["data_layout", "filter_layout"] | None: ...

global___TensorDescriptorProto = TensorDescriptorProto

@typing.final
class AlgorithmProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _MathType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _MathTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            AlgorithmProto._MathType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        DEFAULT_MATH: AlgorithmProto._MathType.ValueType
        TENSOR_OP_MATH: AlgorithmProto._MathType.ValueType
        """The GPU may operate 4x4 matrix FMA.
        See cuDNN's documentation for CUDNN_TENSOR_OP_MATH.
        """

    class MathType(_MathType, metaclass=_MathTypeEnumTypeWrapper): ...
    DEFAULT_MATH: AlgorithmProto.MathType.ValueType
    TENSOR_OP_MATH: AlgorithmProto.MathType.ValueType
    """The GPU may operate 4x4 matrix FMA.
    See cuDNN's documentation for CUDNN_TENSOR_OP_MATH.
    """
    @typing.final
    class TuningKnobsEntry(google.protobuf.message.Message):
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

    ALGO_ID_FIELD_NUMBER: builtins.int
    MATH_TYPE_FIELD_NUMBER: builtins.int
    TUNING_KNOBS_FIELD_NUMBER: builtins.int
    IS_CUDNN_FRONTEND_FIELD_NUMBER: builtins.int
    WORKSPACE_SIZE_FIELD_NUMBER: builtins.int
    algo_id: builtins.int
    math_type: global___AlgorithmProto.MathType.ValueType
    is_cudnn_frontend: builtins.bool
    """Legacy algorithm enums and cuDNN Frontend engine numbers need to coexist in
    the same proto medium-term, until we can be confident of no longer needing
    the legacy cuDNN convolution API.  Once the migration is complete, we can
    stop producing legacy algorithm enums and remove this field.
    """
    @property
    def tuning_knobs(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.int,
        builtins.int,
    ]: ...
    @property
    def workspace_size(self) -> google.protobuf.wrappers_pb2.UInt64Value: ...
    def __init__(
        self,
        *,
        algo_id: builtins.int | None = ...,
        math_type: global___AlgorithmProto.MathType.ValueType | None = ...,
        tuning_knobs: collections.abc.Mapping[builtins.int, builtins.int]
        | None = ...,
        is_cudnn_frontend: builtins.bool | None = ...,
        workspace_size: google.protobuf.wrappers_pb2.UInt64Value | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["workspace_size", b"workspace_size"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "algo_id",
            b"algo_id",
            "is_cudnn_frontend",
            b"is_cudnn_frontend",
            "math_type",
            b"math_type",
            "tuning_knobs",
            b"tuning_knobs",
            "workspace_size",
            b"workspace_size",
        ],
    ) -> None: ...

global___AlgorithmProto = AlgorithmProto

@typing.final
class AlgorithmConfigProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    ALGORITHM_FIELD_NUMBER: builtins.int
    ALGORITHM_NO_SCRATCH_FIELD_NUMBER: builtins.int
    SCRATCH_SIZE_FIELD_NUMBER: builtins.int
    scratch_size: builtins.int
    @property
    def algorithm(self) -> global___AlgorithmProto: ...
    @property
    def algorithm_no_scratch(self) -> global___AlgorithmProto: ...
    def __init__(
        self,
        *,
        algorithm: global___AlgorithmProto | None = ...,
        algorithm_no_scratch: global___AlgorithmProto | None = ...,
        scratch_size: builtins.int | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "algorithm",
            b"algorithm",
            "algorithm_no_scratch",
            b"algorithm_no_scratch",
            "optional_algorithm",
            b"optional_algorithm",
            "optional_algorithm_no_scratch",
            b"optional_algorithm_no_scratch",
            "optional_scratch_size",
            b"optional_scratch_size",
            "scratch_size",
            b"scratch_size",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "algorithm",
            b"algorithm",
            "algorithm_no_scratch",
            b"algorithm_no_scratch",
            "optional_algorithm",
            b"optional_algorithm",
            "optional_algorithm_no_scratch",
            b"optional_algorithm_no_scratch",
            "optional_scratch_size",
            b"optional_scratch_size",
            "scratch_size",
            b"scratch_size",
        ],
    ) -> None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal[
            "optional_algorithm",
            b"optional_algorithm",
        ],
    ) -> typing.Literal["algorithm"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal[
            "optional_algorithm_no_scratch",
            b"optional_algorithm_no_scratch",
        ],
    ) -> typing.Literal["algorithm_no_scratch"] | None: ...
    @typing.overload
    def WhichOneof(
        self,
        oneof_group: typing.Literal[
            "optional_scratch_size",
            b"optional_scratch_size",
        ],
    ) -> typing.Literal["scratch_size"] | None: ...

global___AlgorithmConfigProto = AlgorithmConfigProto

@typing.final
class ConvolutionDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    PADDINGS_FIELD_NUMBER: builtins.int
    STRIDES_FIELD_NUMBER: builtins.int
    DILATIONS_FIELD_NUMBER: builtins.int
    COMPUTE_MODE_FIELD_NUMBER: builtins.int
    GROUP_COUNT_FIELD_NUMBER: builtins.int
    CONVOLUTION_MODE_FIELD_NUMBER: builtins.int
    NAME_FIELD_NUMBER: builtins.int
    compute_mode: global___DataType.ValueType
    """The "accumulator" type. For example, use F32 as an accumulator for F16
    convolutions.
    See cuDNN's cudnnConvolutionMode_t.
    """
    group_count: builtins.int
    """See cuDNN's group count."""
    convolution_mode: global___ConvolutionMode.ValueType
    name: builtins.str
    """Tensorflow node name, same as in NodeDef, for debugging purposes."""
    @property
    def paddings(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def strides(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def dilations(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        paddings: collections.abc.Iterable[builtins.int] | None = ...,
        strides: collections.abc.Iterable[builtins.int] | None = ...,
        dilations: collections.abc.Iterable[builtins.int] | None = ...,
        compute_mode: global___DataType.ValueType | None = ...,
        group_count: builtins.int | None = ...,
        convolution_mode: global___ConvolutionMode.ValueType | None = ...,
        name: builtins.str | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "compute_mode",
            b"compute_mode",
            "convolution_mode",
            b"convolution_mode",
            "dilations",
            b"dilations",
            "group_count",
            b"group_count",
            "name",
            b"name",
            "paddings",
            b"paddings",
            "strides",
            b"strides",
        ],
    ) -> None: ...

global___ConvolutionDescriptorProto = ConvolutionDescriptorProto
