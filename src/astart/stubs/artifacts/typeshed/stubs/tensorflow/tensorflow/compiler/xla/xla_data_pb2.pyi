import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _PrimitiveType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _PrimitiveTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _PrimitiveType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    PRIMITIVE_TYPE_INVALID: _PrimitiveType.ValueType
    """Invalid primitive type to serve as default."""
    PRED: _PrimitiveType.ValueType
    """Predicates are two-state booleans."""
    S2: _PrimitiveType.ValueType
    """Signed integral values of fixed width."""
    S4: _PrimitiveType.ValueType
    S8: _PrimitiveType.ValueType
    S16: _PrimitiveType.ValueType
    S32: _PrimitiveType.ValueType
    S64: _PrimitiveType.ValueType
    U2: _PrimitiveType.ValueType
    """Unsigned integral values of fixed width."""
    U4: _PrimitiveType.ValueType
    U8: _PrimitiveType.ValueType
    U16: _PrimitiveType.ValueType
    U32: _PrimitiveType.ValueType
    U64: _PrimitiveType.ValueType
    F16: _PrimitiveType.ValueType
    """Floating-point values of fixed width.

    Note: if f16s are not natively supported on the device, they will be
    converted to f16 from f32 at arbirary points in the computation.
    """
    F32: _PrimitiveType.ValueType
    BF16: _PrimitiveType.ValueType
    """Truncated 16 bit floating-point format. This is similar to IEEE's 16 bit
    floating-point format, but uses 1 bit for the sign, 8 bits for the exponent
    and 7 bits for the mantissa.
    """
    F64: _PrimitiveType.ValueType
    F8E5M2: _PrimitiveType.ValueType
    """FP8 dtypes, as described in this paper: https://arxiv.org/abs/2209.05433

    F8E5M2 has 5 exponent bits and 2 mantissa bits, and is similar to the
    existing IEEE types.

    F8E4M3FN has 4 exponent bits and 3 mantissa bits. The "FN" means only
    Finite and NaN values are supported. Unlike IEEE types, infinities are not
    supported.  NaN is represented when the exponent and mantissa bits are all
    1s. All other values are finite.

    F8E4M3B11FNUZ has 4 exponent bits and 3 mantissa bits and a bias of 11. The
    "FNUZ" means only Finite and NaN values are supported; zero is unsigned.
    Unlike IEEE types, infinities are not supported.  NaN is represented when
    the exponent and mantissa bits are all 0s with a sign bit of 1. All other
    values are finite.

    Support for these dtypes is under development. They do not yet work
    properly in most cases.
    TODO(b/259609697): Fully support FP8.
    """
    F8E4M3FN: _PrimitiveType.ValueType
    F8E4M3B11FNUZ: _PrimitiveType.ValueType
    F8E5M2FNUZ: _PrimitiveType.ValueType
    """FP8 dtypes, as described in this paper: https://arxiv.org/abs/2206.02915

    F8E5M2FNUZ has 5 exponent bits and 2 mantissa bits.
    F8E4M3FNUZ has 4 exponent bits and 3 mantissa bits.

    The "FNUZ" means only Finite and NaN values are supported; zero is
    unsigned. Unlike IEEE types, infinities are not supported.  NaN is
    represented when the exponent and mantissa bits are all 0s with a sign bit
    of 1. All other values are finite.

    These differences mean there's an additional exponent value available. To
    keep the same dynamic range as an IEEE-like FP8 type, the exponent is
    biased one more than would be expected given the number of exponent bits
    (8 for Float8E4M3FNUZ and 16 for Float8E5M2FNUZ).
    """
    F8E4M3FNUZ: _PrimitiveType.ValueType
    C64: _PrimitiveType.ValueType
    """Complex values of fixed width.
    Paired F32 (real, imag), as in std::complex<float>.
    """
    C128: _PrimitiveType.ValueType
    """Paired F64 (real, imag), as in std::complex<double>."""
    TUPLE: _PrimitiveType.ValueType
    """A tuple is a polymorphic sequence; e.g. a shape that holds different
    sub-shapes. They are used for things like returning multiple values from a
    computation; e.g. a computation that returns weights and biases may have a
    signature that results in a tuple like (f32[784x2000], f32[2000])

    If a shape proto has the tuple element type, it may not have any entries
    in the dimensions field.
    """
    OPAQUE_TYPE: _PrimitiveType.ValueType
    """An opaque type used for passing context-specific data to a custom
    operation. Shapes of this primitive type will have empty dimensions and
    tuple_shapes fields.

    (OPAQUE would be a better name for this identifier, but that conflicts with
    a macro defined in windows.h.)
    """
    TOKEN: _PrimitiveType.ValueType
    """A token type threaded between side-effecting operations. Shapes of this
    primitive type will have empty dimensions and tuple_shapes fields.
    """

class PrimitiveType(
    _PrimitiveType,
    metaclass=_PrimitiveTypeEnumTypeWrapper,
): ...

PRIMITIVE_TYPE_INVALID: PrimitiveType.ValueType
"""Invalid primitive type to serve as default."""
PRED: PrimitiveType.ValueType
"""Predicates are two-state booleans."""
S2: PrimitiveType.ValueType
"""Signed integral values of fixed width."""
S4: PrimitiveType.ValueType
S8: PrimitiveType.ValueType
S16: PrimitiveType.ValueType
S32: PrimitiveType.ValueType
S64: PrimitiveType.ValueType
U2: PrimitiveType.ValueType
"""Unsigned integral values of fixed width."""
U4: PrimitiveType.ValueType
U8: PrimitiveType.ValueType
U16: PrimitiveType.ValueType
U32: PrimitiveType.ValueType
U64: PrimitiveType.ValueType
F16: PrimitiveType.ValueType
"""Floating-point values of fixed width.

Note: if f16s are not natively supported on the device, they will be
converted to f16 from f32 at arbirary points in the computation.
"""
F32: PrimitiveType.ValueType
BF16: PrimitiveType.ValueType
"""Truncated 16 bit floating-point format. This is similar to IEEE's 16 bit
floating-point format, but uses 1 bit for the sign, 8 bits for the exponent
and 7 bits for the mantissa.
"""
F64: PrimitiveType.ValueType
F8E5M2: PrimitiveType.ValueType
"""FP8 dtypes, as described in this paper: https://arxiv.org/abs/2209.05433

F8E5M2 has 5 exponent bits and 2 mantissa bits, and is similar to the
existing IEEE types.

F8E4M3FN has 4 exponent bits and 3 mantissa bits. The "FN" means only
Finite and NaN values are supported. Unlike IEEE types, infinities are not
supported.  NaN is represented when the exponent and mantissa bits are all
1s. All other values are finite.

F8E4M3B11FNUZ has 4 exponent bits and 3 mantissa bits and a bias of 11. The
"FNUZ" means only Finite and NaN values are supported; zero is unsigned.
Unlike IEEE types, infinities are not supported.  NaN is represented when
the exponent and mantissa bits are all 0s with a sign bit of 1. All other
values are finite.

Support for these dtypes is under development. They do not yet work
properly in most cases.
TODO(b/259609697): Fully support FP8.
"""
F8E4M3FN: PrimitiveType.ValueType
F8E4M3B11FNUZ: PrimitiveType.ValueType
F8E5M2FNUZ: PrimitiveType.ValueType
"""FP8 dtypes, as described in this paper: https://arxiv.org/abs/2206.02915

F8E5M2FNUZ has 5 exponent bits and 2 mantissa bits.
F8E4M3FNUZ has 4 exponent bits and 3 mantissa bits.

The "FNUZ" means only Finite and NaN values are supported; zero is
unsigned. Unlike IEEE types, infinities are not supported.  NaN is
represented when the exponent and mantissa bits are all 0s with a sign bit
of 1. All other values are finite.

These differences mean there's an additional exponent value available. To
keep the same dynamic range as an IEEE-like FP8 type, the exponent is
biased one more than would be expected given the number of exponent bits
(8 for Float8E4M3FNUZ and 16 for Float8E5M2FNUZ).
"""
F8E4M3FNUZ: PrimitiveType.ValueType
C64: PrimitiveType.ValueType
"""Complex values of fixed width.
Paired F32 (real, imag), as in std::complex<float>.
"""
C128: PrimitiveType.ValueType
"""Paired F64 (real, imag), as in std::complex<double>."""
TUPLE: PrimitiveType.ValueType
"""A tuple is a polymorphic sequence; e.g. a shape that holds different
sub-shapes. They are used for things like returning multiple values from a
computation; e.g. a computation that returns weights and biases may have a
signature that results in a tuple like (f32[784x2000], f32[2000])

If a shape proto has the tuple element type, it may not have any entries
in the dimensions field.
"""
OPAQUE_TYPE: PrimitiveType.ValueType
"""An opaque type used for passing context-specific data to a custom
operation. Shapes of this primitive type will have empty dimensions and
tuple_shapes fields.

(OPAQUE would be a better name for this identifier, but that conflicts with
a macro defined in windows.h.)
"""
TOKEN: PrimitiveType.ValueType
"""A token type threaded between side-effecting operations. Shapes of this
primitive type will have empty dimensions and tuple_shapes fields.
"""
global___PrimitiveType = PrimitiveType

class _DimLevelType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _DimLevelTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _DimLevelType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    DIM_DENSE: _DimLevelType.ValueType
    """The corresponding dimension is Dense, every entry is stored."""
    DIM_COMPRESSED: _DimLevelType.ValueType
    """The corresponding dimension is Compressed, only nonzeros are stored."""
    DIM_SINGLETON: _DimLevelType.ValueType
    """The corresponding dimension contains a single coordinate, no sibling
    elements for each parent.
    """
    DIM_LOOSE_COMPRESSED: _DimLevelType.ValueType
    """The corresponding dimension is Compressed, but with potential trailing
    zeros, thus an extra upper bound (high) is used to exclude those zeros.
    E.g., indices = [1, 2, 0, 0, 3, 4, 0, 0], position = [(0, 2), (4, 6)].
    """

class DimLevelType(_DimLevelType, metaclass=_DimLevelTypeEnumTypeWrapper): ...

DIM_DENSE: DimLevelType.ValueType
"""The corresponding dimension is Dense, every entry is stored."""
DIM_COMPRESSED: DimLevelType.ValueType
"""The corresponding dimension is Compressed, only nonzeros are stored."""
DIM_SINGLETON: DimLevelType.ValueType
"""The corresponding dimension contains a single coordinate, no sibling
elements for each parent.
"""
DIM_LOOSE_COMPRESSED: DimLevelType.ValueType
"""The corresponding dimension is Compressed, but with potential trailing
zeros, thus an extra upper bound (high) is used to exclude those zeros.
E.g., indices = [1, 2, 0, 0, 3, 4, 0, 0], position = [(0, 2), (4, 6)].
"""
global___DimLevelType = DimLevelType

class _ProfileType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _ProfileTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _ProfileType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    INVALID: _ProfileType.ValueType
    WINDOW: _ProfileType.ValueType
    FLAG: _ProfileType.ValueType
    INTEGER: _ProfileType.ValueType

class ProfileType(_ProfileType, metaclass=_ProfileTypeEnumTypeWrapper): ...

INVALID: ProfileType.ValueType
WINDOW: ProfileType.ValueType
FLAG: ProfileType.ValueType
INTEGER: ProfileType.ValueType
global___ProfileType = ProfileType

class _ProfileSource:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _ProfileSourceEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _ProfileSource.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    PROFILE_SOURCE_UNKNOWN_SOURCE: _ProfileSource.ValueType
    PROFILE_SOURCE_EMBEDDED: _ProfileSource.ValueType
    PROFILE_SOURCE_REMOTE: _ProfileSource.ValueType

class ProfileSource(
    _ProfileSource,
    metaclass=_ProfileSourceEnumTypeWrapper,
): ...

PROFILE_SOURCE_UNKNOWN_SOURCE: ProfileSource.ValueType
PROFILE_SOURCE_EMBEDDED: ProfileSource.ValueType
PROFILE_SOURCE_REMOTE: ProfileSource.ValueType
global___ProfileSource = ProfileSource

class _CompilationEvent:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _CompilationEventEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _CompilationEvent.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    COMPILATION_EVENT_UNKNOWN_EVENT: _CompilationEvent.ValueType
    COMPILATION_EVENT_FIRST_COMPILATION: _CompilationEvent.ValueType
    COMPILATION_EVENT_RECOMPILATION: _CompilationEvent.ValueType

class CompilationEvent(
    _CompilationEvent,
    metaclass=_CompilationEventEnumTypeWrapper,
): ...

COMPILATION_EVENT_UNKNOWN_EVENT: CompilationEvent.ValueType
COMPILATION_EVENT_FIRST_COMPILATION: CompilationEvent.ValueType
COMPILATION_EVENT_RECOMPILATION: CompilationEvent.ValueType
global___CompilationEvent = CompilationEvent

class _PaddingType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _PaddingTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _PaddingType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    PADDING_INVALID: _PaddingType.ValueType
    PADDING_VALID: _PaddingType.ValueType
    """Only valid portion of the base are covered."""
    PADDING_SAME: _PaddingType.ValueType
    """Extra is added to produce same output size as the input."""

class PaddingType(_PaddingType, metaclass=_PaddingTypeEnumTypeWrapper): ...

PADDING_INVALID: PaddingType.ValueType
PADDING_VALID: PaddingType.ValueType
"""Only valid portion of the base are covered."""
PADDING_SAME: PaddingType.ValueType
"""Extra is added to produce same output size as the input."""
global___PaddingType = PaddingType

class _FftType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _FftTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _FftType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    FFT: _FftType.ValueType
    """Forward FFT; complex in, complex out."""
    IFFT: _FftType.ValueType
    """Inverse FFT; complex in, complex out."""
    RFFT: _FftType.ValueType
    """Forward real FFT; real in, fft_length / 2 + 1 complex out"""
    IRFFT: _FftType.ValueType
    """Inverse real FFT; fft_length / 2 + 1 complex in,"""

class FftType(_FftType, metaclass=_FftTypeEnumTypeWrapper): ...

FFT: FftType.ValueType
"""Forward FFT; complex in, complex out."""
IFFT: FftType.ValueType
"""Inverse FFT; complex in, complex out."""
RFFT: FftType.ValueType
"""Forward real FFT; real in, fft_length / 2 + 1 complex out"""
IRFFT: FftType.ValueType
"""Inverse real FFT; fft_length / 2 + 1 complex in,"""
global___FftType = FftType

class _SparsityType:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _SparsityTypeEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _SparsityType.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    SPARSITY_INVALID: _SparsityType.ValueType
    SPARSITY_STRUCTURED_N_M: _SparsityType.ValueType
    """Structured N:M sparsity."""

class SparsityType(_SparsityType, metaclass=_SparsityTypeEnumTypeWrapper): ...

SPARSITY_INVALID: SparsityType.ValueType
SPARSITY_STRUCTURED_N_M: SparsityType.ValueType
"""Structured N:M sparsity."""
global___SparsityType = SparsityType

class _RandomDistribution:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _RandomDistributionEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _RandomDistribution.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    RNG_INVALID: _RandomDistribution.ValueType
    RNG_UNIFORM: _RandomDistribution.ValueType
    """Creates a uniform-distribution-generated random number on the semi-open
    interval [parameter[0], parameter[1]).
    """
    RNG_NORMAL: _RandomDistribution.ValueType
    """Creates a normal-distribution-generated random number with mean
    parameter[0] and standard deviation parameter[1].
    """

class RandomDistribution(
    _RandomDistribution,
    metaclass=_RandomDistributionEnumTypeWrapper,
): ...

RNG_INVALID: RandomDistribution.ValueType
RNG_UNIFORM: RandomDistribution.ValueType
"""Creates a uniform-distribution-generated random number on the semi-open
interval [parameter[0], parameter[1]).
"""
RNG_NORMAL: RandomDistribution.ValueType
"""Creates a normal-distribution-generated random number with mean
parameter[0] and standard deviation parameter[1].
"""
global___RandomDistribution = RandomDistribution

class _RandomAlgorithm:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _RandomAlgorithmEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _RandomAlgorithm.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    RNG_DEFAULT: _RandomAlgorithm.ValueType
    """Backend dependent default algorithm."""
    RNG_THREE_FRY: _RandomAlgorithm.ValueType
    RNG_PHILOX: _RandomAlgorithm.ValueType
    """Next: 2"""

class RandomAlgorithm(
    _RandomAlgorithm,
    metaclass=_RandomAlgorithmEnumTypeWrapper,
): ...

RNG_DEFAULT: RandomAlgorithm.ValueType
"""Backend dependent default algorithm."""
RNG_THREE_FRY: RandomAlgorithm.ValueType
RNG_PHILOX: RandomAlgorithm.ValueType
"""Next: 2"""
global___RandomAlgorithm = RandomAlgorithm

@typing.final
class PaddingConfig(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class PaddingConfigDimension(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        EDGE_PADDING_LOW_FIELD_NUMBER: builtins.int
        EDGE_PADDING_HIGH_FIELD_NUMBER: builtins.int
        INTERIOR_PADDING_FIELD_NUMBER: builtins.int
        edge_padding_low: builtins.int
        """Padding amount on the low-end (next to the index 0). May be negative."""
        edge_padding_high: builtins.int
        """Padding amount on the high-end (next to the highest index). May be
        negative.
        """
        interior_padding: builtins.int
        """Padding amount between the elements. May not be negative."""
        def __init__(
            self,
            *,
            edge_padding_low: builtins.int | None = ...,
            edge_padding_high: builtins.int | None = ...,
            interior_padding: builtins.int | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "edge_padding_high",
                b"edge_padding_high",
                "edge_padding_low",
                b"edge_padding_low",
                "interior_padding",
                b"interior_padding",
            ],
        ) -> None: ...

    DIMENSIONS_FIELD_NUMBER: builtins.int
    @property
    def dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___PaddingConfig.PaddingConfigDimension
    ]: ...
    def __init__(
        self,
        *,
        dimensions: collections.abc.Iterable[
            global___PaddingConfig.PaddingConfigDimension
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["dimensions", b"dimensions"],
    ) -> None: ...

global___PaddingConfig = PaddingConfig

@typing.final
class TileProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DIMENSIONS_FIELD_NUMBER: builtins.int
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
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["dimensions", b"dimensions"],
    ) -> None: ...

global___TileProto = TileProto

@typing.final
class SplitConfigProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DIMENSION_FIELD_NUMBER: builtins.int
    SPLIT_INDICES_FIELD_NUMBER: builtins.int
    dimension: builtins.int
    """The dimension that is split."""
    @property
    def split_indices(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        dimension: builtins.int | None = ...,
        split_indices: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dimension",
            b"dimension",
            "split_indices",
            b"split_indices",
        ],
    ) -> None: ...

global___SplitConfigProto = SplitConfigProto

@typing.final
class LayoutProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DIM_LEVEL_TYPES_FIELD_NUMBER: builtins.int
    DIM_UNIQUE_FIELD_NUMBER: builtins.int
    DIM_ORDERED_FIELD_NUMBER: builtins.int
    MINOR_TO_MAJOR_FIELD_NUMBER: builtins.int
    TILES_FIELD_NUMBER: builtins.int
    TAIL_PADDING_ALIGNMENT_IN_ELEMENTS_FIELD_NUMBER: builtins.int
    ELEMENT_SIZE_IN_BITS_FIELD_NUMBER: builtins.int
    MEMORY_SPACE_FIELD_NUMBER: builtins.int
    INDEX_PRIMITIVE_TYPE_FIELD_NUMBER: builtins.int
    POINTER_PRIMITIVE_TYPE_FIELD_NUMBER: builtins.int
    PHYSICAL_SHAPE_FIELD_NUMBER: builtins.int
    DYNAMIC_SHAPE_METADATA_PREFIX_BYTES_FIELD_NUMBER: builtins.int
    SPLIT_CONFIGS_FIELD_NUMBER: builtins.int
    tail_padding_alignment_in_elements: builtins.int
    """The shape is padded at the end to multiple of, in terms of number of
    elements. This is useful when tiling does not bring the shape to certain
    desired granules. Tiling effectively pads/reshapes/transposes the shape
    to another shape. This field pads the total number of elements of that
    new shape to a multiple of certain number of elements. This is useful such
    as we want a layout which does not tile the data but still requires it to
    be padded to certain number of elements.
    """
    element_size_in_bits: builtins.int
    """(Optional) Bit size of each element. When unspecified or being 0, default
    to ShapeUtil::ByteSizeOfPrimitiveType.
    """
    memory_space: builtins.int
    """Memory space where this array resides. The integer field is interpreted in
    a backend-specific manner.
    """
    index_primitive_type: global___PrimitiveType.ValueType
    """The integer types to be used for indices and pointers.  These fields must
    not be used unless the layout represents a sparse array.  The PrimitiveType
    must correspond to an unsigned integer (U8, U16, U32, or U64).
    If not provided, the compiler will use the largest unsigned integer
    that is naturally supported by the target device (U32 or U64 in currently
    supported devices).
    """
    pointer_primitive_type: global___PrimitiveType.ValueType
    dynamic_shape_metadata_prefix_bytes: builtins.int
    """The dynamic shape metadata size in bytes in front of the shape data. The
    field may be non-zero for a static shape whose associated buffer is for a
    dynamic shape, e.g. a result of SliceToDynamic.
    """
    @property
    def dim_level_types(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        global___DimLevelType.ValueType
    ]: ...
    @property
    def dim_unique(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    @property
    def dim_ordered(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    @property
    def minor_to_major(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def tiles(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___TileProto
    ]: ...
    @property
    def physical_shape(self) -> global___ShapeProto: ...
    @property
    def split_configs(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___SplitConfigProto
    ]: ...
    def __init__(
        self,
        *,
        dim_level_types: collections.abc.Iterable[
            global___DimLevelType.ValueType
        ]
        | None = ...,
        dim_unique: collections.abc.Iterable[builtins.bool] | None = ...,
        dim_ordered: collections.abc.Iterable[builtins.bool] | None = ...,
        minor_to_major: collections.abc.Iterable[builtins.int] | None = ...,
        tiles: collections.abc.Iterable[global___TileProto] | None = ...,
        tail_padding_alignment_in_elements: builtins.int | None = ...,
        element_size_in_bits: builtins.int | None = ...,
        memory_space: builtins.int | None = ...,
        index_primitive_type: global___PrimitiveType.ValueType | None = ...,
        pointer_primitive_type: global___PrimitiveType.ValueType | None = ...,
        physical_shape: global___ShapeProto | None = ...,
        dynamic_shape_metadata_prefix_bytes: builtins.int | None = ...,
        split_configs: collections.abc.Iterable[global___SplitConfigProto]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["physical_shape", b"physical_shape"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dim_level_types",
            b"dim_level_types",
            "dim_ordered",
            b"dim_ordered",
            "dim_unique",
            b"dim_unique",
            "dynamic_shape_metadata_prefix_bytes",
            b"dynamic_shape_metadata_prefix_bytes",
            "element_size_in_bits",
            b"element_size_in_bits",
            "index_primitive_type",
            b"index_primitive_type",
            "memory_space",
            b"memory_space",
            "minor_to_major",
            b"minor_to_major",
            "physical_shape",
            b"physical_shape",
            "pointer_primitive_type",
            b"pointer_primitive_type",
            "split_configs",
            b"split_configs",
            "tail_padding_alignment_in_elements",
            b"tail_padding_alignment_in_elements",
            "tiles",
            b"tiles",
        ],
    ) -> None: ...

global___LayoutProto = LayoutProto

@typing.final
class ShapeProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    ELEMENT_TYPE_FIELD_NUMBER: builtins.int
    DIMENSIONS_FIELD_NUMBER: builtins.int
    TUPLE_SHAPES_FIELD_NUMBER: builtins.int
    LAYOUT_FIELD_NUMBER: builtins.int
    IS_DYNAMIC_DIMENSION_FIELD_NUMBER: builtins.int
    element_type: global___PrimitiveType.ValueType
    """The element type for this shape."""
    @property
    def dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def tuple_shapes(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ShapeProto
    ]: ...
    @property
    def layout(self) -> global___LayoutProto: ...
    @property
    def is_dynamic_dimension(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    def __init__(
        self,
        *,
        element_type: global___PrimitiveType.ValueType | None = ...,
        dimensions: collections.abc.Iterable[builtins.int] | None = ...,
        tuple_shapes: collections.abc.Iterable[global___ShapeProto]
        | None = ...,
        layout: global___LayoutProto | None = ...,
        is_dynamic_dimension: collections.abc.Iterable[builtins.bool]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["layout", b"layout"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dimensions",
            b"dimensions",
            "element_type",
            b"element_type",
            "is_dynamic_dimension",
            b"is_dynamic_dimension",
            "layout",
            b"layout",
            "tuple_shapes",
            b"tuple_shapes",
        ],
    ) -> None: ...

global___ShapeProto = ShapeProto

@typing.final
class ProgramShapeProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    PARAMETERS_FIELD_NUMBER: builtins.int
    RESULT_FIELD_NUMBER: builtins.int
    PARAMETER_NAMES_FIELD_NUMBER: builtins.int
    @property
    def parameters(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ShapeProto
    ]: ...
    @property
    def result(self) -> global___ShapeProto: ...
    @property
    def parameter_names(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        parameters: collections.abc.Iterable[global___ShapeProto] | None = ...,
        result: global___ShapeProto | None = ...,
        parameter_names: collections.abc.Iterable[builtins.str] | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["result", b"result"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "parameter_names",
            b"parameter_names",
            "parameters",
            b"parameters",
            "result",
            b"result",
        ],
    ) -> None: ...

global___ProgramShapeProto = ProgramShapeProto

@typing.final
class ComputationStats(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FLOP_COUNT_FIELD_NUMBER: builtins.int
    TRANSCENDENTAL_COUNT_FIELD_NUMBER: builtins.int
    flop_count: builtins.float
    """The number of floating point operations in the computation."""
    transcendental_count: builtins.float
    """The number of transcendental operations (e.g., exp) in the computation."""
    def __init__(
        self,
        *,
        flop_count: builtins.float | None = ...,
        transcendental_count: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "flop_count",
            b"flop_count",
            "transcendental_count",
            b"transcendental_count",
        ],
    ) -> None: ...

global___ComputationStats = ComputationStats

@typing.final
class OpMetadata(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class ProfileInfo(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        PROFILE_TYPE_FIELD_NUMBER: builtins.int
        RELATIVE_SPEEDUP_FIELD_NUMBER: builtins.int
        PROFILE_SOURCE_FIELD_NUMBER: builtins.int
        COMPILATION_EVENT_FIELD_NUMBER: builtins.int
        relative_speedup: builtins.float
        """Speedup of tuned config compared to default config.
        TODO(b/203817882) Set the relative_speedup.
        """
        profile_source: global___ProfileSource.ValueType
        """The source of the optimization profiles that this operation contains."""
        compilation_event: global___CompilationEvent.ValueType
        """The compilation event that triggered the use of the profiles."""
        @property
        def profile_type(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            global___ProfileType.ValueType
        ]: ...
        def __init__(
            self,
            *,
            profile_type: collections.abc.Iterable[
                global___ProfileType.ValueType
            ]
            | None = ...,
            relative_speedup: builtins.float | None = ...,
            profile_source: global___ProfileSource.ValueType | None = ...,
            compilation_event: global___CompilationEvent.ValueType
            | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "compilation_event",
                b"compilation_event",
                "profile_source",
                b"profile_source",
                "profile_type",
                b"profile_type",
                "relative_speedup",
                b"relative_speedup",
            ],
        ) -> None: ...

    OP_TYPE_FIELD_NUMBER: builtins.int
    OP_NAME_FIELD_NUMBER: builtins.int
    SOURCE_FILE_FIELD_NUMBER: builtins.int
    SOURCE_LINE_FIELD_NUMBER: builtins.int
    PROFILE_TYPE_FIELD_NUMBER: builtins.int
    SIZE_OF_GENERATED_CODE_IN_BYTES_FIELD_NUMBER: builtins.int
    SIZE_OF_MEMORY_WORKING_SET_IN_BYTES_FIELD_NUMBER: builtins.int
    PROFILE_INFO_FIELD_NUMBER: builtins.int
    DEDUPLICATED_NAME_FIELD_NUMBER: builtins.int
    PRESERVE_LAYOUT_FIELD_NUMBER: builtins.int
    STACK_FRAME_ID_FIELD_NUMBER: builtins.int
    SCHEDULING_NAME_FIELD_NUMBER: builtins.int
    op_type: builtins.str
    """The framework op name that generated this XLA op.

    Frameworks that build on top of XLA should mirror the names of their ops
    back to users by specifying the op_type. In this way, even if the
    framework's "ops" are implemented as multiple XLA HLO Ops, they can be
    grouped appropriately. (e.g. if a SoftMax layer is emitted into XLA as
    multiple ops, then each op should have the op_type be "SoftMax".)
    """
    op_name: builtins.str
    """The user-specified name of the op.

    This name is often unique within a computation. Note: some frameworks
    add auto-generated names if the user does not provide one.
    """
    source_file: builtins.str
    """Indicate a file and line that this op is associated to in a user's program.

    e.g. it could be the file and line of user code that generated the op.
    """
    source_line: builtins.int
    size_of_generated_code_in_bytes: builtins.int
    """The footprint of the generated code for the instruction."""
    size_of_memory_working_set_in_bytes: builtins.int
    """The size of the working set, i.e., the amount of memory, used by the
    instruction in a compiler-managed fast device memory.
    """
    deduplicated_name: builtins.str
    """Deduplicated HLO name for this op. In some cases, we can have multiple
    instructions (e.g. fusions) that are considered duplicates. We want to
    group them together under the same name so that we can group them together
    during analysis (e.g. HLO Op Profile tool in Xprof).
    E.g. If we have fusion.1, fusion.2, and fusion.3 marked as duplicates,
    fusion.2 and fusion.3 will have deduplicated_name = fusion.1
    """
    preserve_layout: builtins.bool
    """Whether to preserve the layout of the HLO op."""
    stack_frame_id: builtins.int
    """1-based position of the frame in frames flat array.
    Ids are 1-based to keep 0 value as representation of non-set property.
    """
    scheduling_name: builtins.str
    """Instruction name available upon scheduling."""
    @property
    def profile_type(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        global___ProfileType.ValueType
    ]: ...
    @property
    def profile_info(self) -> global___OpMetadata.ProfileInfo: ...
    def __init__(
        self,
        *,
        op_type: builtins.str | None = ...,
        op_name: builtins.str | None = ...,
        source_file: builtins.str | None = ...,
        source_line: builtins.int | None = ...,
        profile_type: collections.abc.Iterable[global___ProfileType.ValueType]
        | None = ...,
        size_of_generated_code_in_bytes: builtins.int | None = ...,
        size_of_memory_working_set_in_bytes: builtins.int | None = ...,
        profile_info: global___OpMetadata.ProfileInfo | None = ...,
        deduplicated_name: builtins.str | None = ...,
        preserve_layout: builtins.bool | None = ...,
        stack_frame_id: builtins.int | None = ...,
        scheduling_name: builtins.str | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["profile_info", b"profile_info"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "deduplicated_name",
            b"deduplicated_name",
            "op_name",
            b"op_name",
            "op_type",
            b"op_type",
            "preserve_layout",
            b"preserve_layout",
            "profile_info",
            b"profile_info",
            "profile_type",
            b"profile_type",
            "scheduling_name",
            b"scheduling_name",
            "size_of_generated_code_in_bytes",
            b"size_of_generated_code_in_bytes",
            "size_of_memory_working_set_in_bytes",
            b"size_of_memory_working_set_in_bytes",
            "source_file",
            b"source_file",
            "source_line",
            b"source_line",
            "stack_frame_id",
            b"stack_frame_id",
        ],
    ) -> None: ...

global___OpMetadata = OpMetadata

@typing.final
class ExecutionProfile(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    COMPILATION_CACHE_HIT_FIELD_NUMBER: builtins.int
    COMPILE_TIME_MS_FIELD_NUMBER: builtins.int
    COMPUTE_CYCLE_COUNT_FIELD_NUMBER: builtins.int
    COMPUTE_TIME_NS_FIELD_NUMBER: builtins.int
    COMPUTE_AND_TRANSFER_TIME_NS_FIELD_NUMBER: builtins.int
    EXECUTABLE_SIZE_IN_BYTES_FIELD_NUMBER: builtins.int
    PROFILE_CACHE_HIT_FIELD_NUMBER: builtins.int
    WARMUP_RUN_EXECUTED_FIELD_NUMBER: builtins.int
    compilation_cache_hit: builtins.bool
    """Whether the executable was read from the compilation cache."""
    compile_time_ms: builtins.int
    """The time in milliseconds spent to compile the computation. This only set if
    the executable was not read from the compilation cache
    (compilation_cache_hit == false).
    """
    compute_cycle_count: builtins.int
    """The number of cycles spent for the computation. This does not include the
    time taken for the data transfers between the host and the device. This is
    a target-dependent field and only used for debugging purposes.
    """
    compute_time_ns: builtins.int
    """The time in nanoseconds spent for the computation, without data transfer."""
    compute_and_transfer_time_ns: builtins.int
    """The time in nanoseconds spent for the entire computation, including the
    result data transfer time. Current implementation does not spend any cycles
    for the input data transfer since the memory is initialized with the proper
    values before the execution.
    """
    executable_size_in_bytes: builtins.int
    """The size of the binary code in the executable."""
    profile_cache_hit: builtins.bool
    """Whether this profile was drawn from a cache of profiles instead of from
    execution on the hardware.
    """
    warmup_run_executed: builtins.bool
    """Whether a warm-up run of the computation was executed before the
    measured execution.
    """
    def __init__(
        self,
        *,
        compilation_cache_hit: builtins.bool | None = ...,
        compile_time_ms: builtins.int | None = ...,
        compute_cycle_count: builtins.int | None = ...,
        compute_time_ns: builtins.int | None = ...,
        compute_and_transfer_time_ns: builtins.int | None = ...,
        executable_size_in_bytes: builtins.int | None = ...,
        profile_cache_hit: builtins.bool | None = ...,
        warmup_run_executed: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "compilation_cache_hit",
            b"compilation_cache_hit",
            "compile_time_ms",
            b"compile_time_ms",
            "compute_and_transfer_time_ns",
            b"compute_and_transfer_time_ns",
            "compute_cycle_count",
            b"compute_cycle_count",
            "compute_time_ns",
            b"compute_time_ns",
            "executable_size_in_bytes",
            b"executable_size_in_bytes",
            "profile_cache_hit",
            b"profile_cache_hit",
            "warmup_run_executed",
            b"warmup_run_executed",
        ],
    ) -> None: ...

global___ExecutionProfile = ExecutionProfile

@typing.final
class ExecutionHandle(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    HANDLE_FIELD_NUMBER: builtins.int
    handle: builtins.int
    def __init__(self, *, handle: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["handle", b"handle"],
    ) -> None: ...

global___ExecutionHandle = ExecutionHandle

@typing.final
class GlobalDataHandle(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    HANDLE_FIELD_NUMBER: builtins.int
    handle: builtins.int
    def __init__(self, *, handle: builtins.int | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["handle", b"handle"],
    ) -> None: ...

global___GlobalDataHandle = GlobalDataHandle

@typing.final
class DeviceHandle(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    HANDLE_FIELD_NUMBER: builtins.int
    DEVICE_COUNT_FIELD_NUMBER: builtins.int
    handle: builtins.int
    device_count: builtins.int
    """The number of model-parallel virtual devices that communicate via XLA
    Send/Recv instructions.
    """
    def __init__(
        self,
        *,
        handle: builtins.int | None = ...,
        device_count: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "device_count",
            b"device_count",
            "handle",
            b"handle",
        ],
    ) -> None: ...

global___DeviceHandle = DeviceHandle

@typing.final
class ChannelHandle(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _ChannelType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ChannelTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            ChannelHandle._ChannelType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        CHANNEL_TYPE_INVALID: ChannelHandle._ChannelType.ValueType
        """Invalid primitive type to serve as default."""
        DEVICE_TO_DEVICE: ChannelHandle._ChannelType.ValueType
        """A channel for sending data between devices."""
        DEVICE_TO_HOST: ChannelHandle._ChannelType.ValueType
        """A channel for sending data from the device to the host. Can only be used
        with a Send operation.
        """
        HOST_TO_DEVICE: ChannelHandle._ChannelType.ValueType
        """A channel for sending data from the host to the device. Can only be used
        with a Recv operation.
        """

    class ChannelType(_ChannelType, metaclass=_ChannelTypeEnumTypeWrapper): ...
    CHANNEL_TYPE_INVALID: ChannelHandle.ChannelType.ValueType
    """Invalid primitive type to serve as default."""
    DEVICE_TO_DEVICE: ChannelHandle.ChannelType.ValueType
    """A channel for sending data between devices."""
    DEVICE_TO_HOST: ChannelHandle.ChannelType.ValueType
    """A channel for sending data from the device to the host. Can only be used
    with a Send operation.
    """
    HOST_TO_DEVICE: ChannelHandle.ChannelType.ValueType
    """A channel for sending data from the host to the device. Can only be used
    with a Recv operation.
    """
    HANDLE_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    handle: builtins.int
    type: global___ChannelHandle.ChannelType.ValueType
    def __init__(
        self,
        *,
        handle: builtins.int | None = ...,
        type: global___ChannelHandle.ChannelType.ValueType | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["handle", b"handle", "type", b"type"],
    ) -> None: ...

global___ChannelHandle = ChannelHandle

@typing.final
class DeviceAssignmentProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class ComputationDevice(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        REPLICA_DEVICE_IDS_FIELD_NUMBER: builtins.int
        @property
        def replica_device_ids(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        def __init__(
            self,
            *,
            replica_device_ids: collections.abc.Iterable[builtins.int]
            | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "replica_device_ids",
                b"replica_device_ids",
            ],
        ) -> None: ...

    REPLICA_COUNT_FIELD_NUMBER: builtins.int
    COMPUTATION_COUNT_FIELD_NUMBER: builtins.int
    COMPUTATION_DEVICES_FIELD_NUMBER: builtins.int
    replica_count: builtins.int
    computation_count: builtins.int
    @property
    def computation_devices(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___DeviceAssignmentProto.ComputationDevice
    ]: ...
    def __init__(
        self,
        *,
        replica_count: builtins.int | None = ...,
        computation_count: builtins.int | None = ...,
        computation_devices: collections.abc.Iterable[
            global___DeviceAssignmentProto.ComputationDevice
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "computation_count",
            b"computation_count",
            "computation_devices",
            b"computation_devices",
            "replica_count",
            b"replica_count",
        ],
    ) -> None: ...

global___DeviceAssignmentProto = DeviceAssignmentProto

@typing.final
class LiteralProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SHAPE_FIELD_NUMBER: builtins.int
    PREDS_FIELD_NUMBER: builtins.int
    S2S_FIELD_NUMBER: builtins.int
    S4S_FIELD_NUMBER: builtins.int
    S8S_FIELD_NUMBER: builtins.int
    U2S_FIELD_NUMBER: builtins.int
    U4S_FIELD_NUMBER: builtins.int
    U8S_FIELD_NUMBER: builtins.int
    S32S_FIELD_NUMBER: builtins.int
    S64S_FIELD_NUMBER: builtins.int
    U32S_FIELD_NUMBER: builtins.int
    U64S_FIELD_NUMBER: builtins.int
    F32S_FIELD_NUMBER: builtins.int
    F64S_FIELD_NUMBER: builtins.int
    C64S_FIELD_NUMBER: builtins.int
    C128S_FIELD_NUMBER: builtins.int
    TUPLE_LITERALS_FIELD_NUMBER: builtins.int
    F16S_FIELD_NUMBER: builtins.int
    BF16S_FIELD_NUMBER: builtins.int
    U16S_FIELD_NUMBER: builtins.int
    S16S_FIELD_NUMBER: builtins.int
    F8E5M2S_FIELD_NUMBER: builtins.int
    F8E4M3FNS_FIELD_NUMBER: builtins.int
    F8E4M3B11FNUZS_FIELD_NUMBER: builtins.int
    F8E5M2FNUZS_FIELD_NUMBER: builtins.int
    F8E4M3FNUZS_FIELD_NUMBER: builtins.int
    SPARSE_INDICES_FIELD_NUMBER: builtins.int
    s2s: builtins.bytes
    s4s: builtins.bytes
    s8s: builtins.bytes
    u2s: builtins.bytes
    u4s: builtins.bytes
    u8s: builtins.bytes
    f16s: builtins.bytes
    """The F16s, BF16s, U16s and S16s are encoded in little endian byte order"""
    bf16s: builtins.bytes
    u16s: builtins.bytes
    s16s: builtins.bytes
    f8e5m2s: builtins.bytes
    f8e4m3fns: builtins.bytes
    f8e4m3b11fnuzs: builtins.bytes
    f8e5m2fnuzs: builtins.bytes
    f8e4m3fnuzs: builtins.bytes
    @property
    def shape(self) -> global___ShapeProto: ...
    @property
    def preds(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    @property
    def s32s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def s64s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def u32s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def u64s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def f32s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def f64s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def c64s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def c128s(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.float
    ]: ...
    @property
    def tuple_literals(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___LiteralProto
    ]: ...
    @property
    def sparse_indices(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        shape: global___ShapeProto | None = ...,
        preds: collections.abc.Iterable[builtins.bool] | None = ...,
        s2s: builtins.bytes | None = ...,
        s4s: builtins.bytes | None = ...,
        s8s: builtins.bytes | None = ...,
        u2s: builtins.bytes | None = ...,
        u4s: builtins.bytes | None = ...,
        u8s: builtins.bytes | None = ...,
        s32s: collections.abc.Iterable[builtins.int] | None = ...,
        s64s: collections.abc.Iterable[builtins.int] | None = ...,
        u32s: collections.abc.Iterable[builtins.int] | None = ...,
        u64s: collections.abc.Iterable[builtins.int] | None = ...,
        f32s: collections.abc.Iterable[builtins.float] | None = ...,
        f64s: collections.abc.Iterable[builtins.float] | None = ...,
        c64s: collections.abc.Iterable[builtins.float] | None = ...,
        c128s: collections.abc.Iterable[builtins.float] | None = ...,
        tuple_literals: collections.abc.Iterable[global___LiteralProto]
        | None = ...,
        f16s: builtins.bytes | None = ...,
        bf16s: builtins.bytes | None = ...,
        u16s: builtins.bytes | None = ...,
        s16s: builtins.bytes | None = ...,
        f8e5m2s: builtins.bytes | None = ...,
        f8e4m3fns: builtins.bytes | None = ...,
        f8e4m3b11fnuzs: builtins.bytes | None = ...,
        f8e5m2fnuzs: builtins.bytes | None = ...,
        f8e4m3fnuzs: builtins.bytes | None = ...,
        sparse_indices: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["shape", b"shape"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "bf16s",
            b"bf16s",
            "c128s",
            b"c128s",
            "c64s",
            b"c64s",
            "f16s",
            b"f16s",
            "f32s",
            b"f32s",
            "f64s",
            b"f64s",
            "f8e4m3b11fnuzs",
            b"f8e4m3b11fnuzs",
            "f8e4m3fns",
            b"f8e4m3fns",
            "f8e4m3fnuzs",
            b"f8e4m3fnuzs",
            "f8e5m2fnuzs",
            b"f8e5m2fnuzs",
            "f8e5m2s",
            b"f8e5m2s",
            "preds",
            b"preds",
            "s16s",
            b"s16s",
            "s2s",
            b"s2s",
            "s32s",
            b"s32s",
            "s4s",
            b"s4s",
            "s64s",
            b"s64s",
            "s8s",
            b"s8s",
            "shape",
            b"shape",
            "sparse_indices",
            b"sparse_indices",
            "tuple_literals",
            b"tuple_literals",
            "u16s",
            b"u16s",
            "u2s",
            b"u2s",
            "u32s",
            b"u32s",
            "u4s",
            b"u4s",
            "u64s",
            b"u64s",
            "u8s",
            b"u8s",
        ],
    ) -> None: ...

global___LiteralProto = LiteralProto

@typing.final
class WindowDimension(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SIZE_FIELD_NUMBER: builtins.int
    STRIDE_FIELD_NUMBER: builtins.int
    PADDING_LOW_FIELD_NUMBER: builtins.int
    PADDING_HIGH_FIELD_NUMBER: builtins.int
    WINDOW_DILATION_FIELD_NUMBER: builtins.int
    BASE_DILATION_FIELD_NUMBER: builtins.int
    WINDOW_REVERSAL_FIELD_NUMBER: builtins.int
    size: builtins.int
    """The size of the window in this dimension. For a rectangle, this would be
    the width or height.
    """
    stride: builtins.int
    """The stride at which the window moves across the base area in this
    dimension. In other words, this is the spacing between different
    positions of the window in this dimension.
    """
    padding_low: builtins.int
    """If positive, means the amount of padding to add to the base area at the low
    end of this dimension; if negative, its negative means the number of
    elements removed from the low end of this dimension. For example, in the
    horizontal dimension of a rectangle, this would be the number of padding
    values to pad on the left, given that indices increase when going right.
    The actual padding value depends upon the context. Convolution pads with
    zeros. ReduceWindow and SelectAndScatter pads with the reduce function's
    init value.
    """
    padding_high: builtins.int
    """As padding_low, but on the high end of this dimension. For example, in the
    horizontal dimension of a rectangle, this would be the number of values to
    pad on the right, given that indices increase when going right.
    """
    window_dilation: builtins.int
    """Dilation factor of the sliding window in this dimension. A dilation factor
    of 1 means no dilation. window_dilation - 1 no-op entries ("holes") are
    implicitly placed between each kernel element. This value may not be less
    than 1. See documentation for convolution.
    """
    base_dilation: builtins.int
    """Dilation factor of the base area in this dimension. A dilation factor of 1
    means no dilation. base_dilation - 1 no-op entries ("holes") are implicitly
    placed between each base area element. This value may not be less than 1.
    See documentation for convolution.
    """
    window_reversal: builtins.bool
    """Window reversal means that this dimension was logically reversed before the
    operation.
    """
    def __init__(
        self,
        *,
        size: builtins.int | None = ...,
        stride: builtins.int | None = ...,
        padding_low: builtins.int | None = ...,
        padding_high: builtins.int | None = ...,
        window_dilation: builtins.int | None = ...,
        base_dilation: builtins.int | None = ...,
        window_reversal: builtins.bool | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "base_dilation",
            b"base_dilation",
            "padding_high",
            b"padding_high",
            "padding_low",
            b"padding_low",
            "size",
            b"size",
            "stride",
            b"stride",
            "window_dilation",
            b"window_dilation",
            "window_reversal",
            b"window_reversal",
        ],
    ) -> None: ...

global___WindowDimension = WindowDimension

@typing.final
class Window(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DIMENSIONS_FIELD_NUMBER: builtins.int
    @property
    def dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___WindowDimension
    ]: ...
    def __init__(
        self,
        *,
        dimensions: collections.abc.Iterable[global___WindowDimension]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["dimensions", b"dimensions"],
    ) -> None: ...

global___Window = Window

@typing.final
class GatherDimensionNumbers(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    OFFSET_DIMS_FIELD_NUMBER: builtins.int
    COLLAPSED_SLICE_DIMS_FIELD_NUMBER: builtins.int
    START_INDEX_MAP_FIELD_NUMBER: builtins.int
    INDEX_VECTOR_DIM_FIELD_NUMBER: builtins.int
    OPERAND_BATCHING_DIMS_FIELD_NUMBER: builtins.int
    START_INDICES_BATCHING_DIMS_FIELD_NUMBER: builtins.int
    index_vector_dim: builtins.int
    """The dimension in the start_indices input that contains the starting
    indices.
    """
    @property
    def offset_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def collapsed_slice_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def start_index_map(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def operand_batching_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def start_indices_batching_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        offset_dims: collections.abc.Iterable[builtins.int] | None = ...,
        collapsed_slice_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        start_index_map: collections.abc.Iterable[builtins.int] | None = ...,
        index_vector_dim: builtins.int | None = ...,
        operand_batching_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        start_indices_batching_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "collapsed_slice_dims",
            b"collapsed_slice_dims",
            "index_vector_dim",
            b"index_vector_dim",
            "offset_dims",
            b"offset_dims",
            "operand_batching_dims",
            b"operand_batching_dims",
            "start_index_map",
            b"start_index_map",
            "start_indices_batching_dims",
            b"start_indices_batching_dims",
        ],
    ) -> None: ...

global___GatherDimensionNumbers = GatherDimensionNumbers

@typing.final
class ScatterDimensionNumbers(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    UPDATE_WINDOW_DIMS_FIELD_NUMBER: builtins.int
    INSERTED_WINDOW_DIMS_FIELD_NUMBER: builtins.int
    SCATTER_DIMS_TO_OPERAND_DIMS_FIELD_NUMBER: builtins.int
    INDEX_VECTOR_DIM_FIELD_NUMBER: builtins.int
    INPUT_BATCHING_DIMS_FIELD_NUMBER: builtins.int
    SCATTER_INDICES_BATCHING_DIMS_FIELD_NUMBER: builtins.int
    index_vector_dim: builtins.int
    @property
    def update_window_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def inserted_window_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def scatter_dims_to_operand_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def input_batching_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def scatter_indices_batching_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        update_window_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        inserted_window_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        scatter_dims_to_operand_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        index_vector_dim: builtins.int | None = ...,
        input_batching_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
        scatter_indices_batching_dims: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "index_vector_dim",
            b"index_vector_dim",
            "input_batching_dims",
            b"input_batching_dims",
            "inserted_window_dims",
            b"inserted_window_dims",
            "scatter_dims_to_operand_dims",
            b"scatter_dims_to_operand_dims",
            "scatter_indices_batching_dims",
            b"scatter_indices_batching_dims",
            "update_window_dims",
            b"update_window_dims",
        ],
    ) -> None: ...

global___ScatterDimensionNumbers = ScatterDimensionNumbers

@typing.final
class ConvolutionDimensionNumbers(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    INPUT_BATCH_DIMENSION_FIELD_NUMBER: builtins.int
    INPUT_FEATURE_DIMENSION_FIELD_NUMBER: builtins.int
    INPUT_SPATIAL_DIMENSIONS_FIELD_NUMBER: builtins.int
    KERNEL_INPUT_FEATURE_DIMENSION_FIELD_NUMBER: builtins.int
    KERNEL_OUTPUT_FEATURE_DIMENSION_FIELD_NUMBER: builtins.int
    KERNEL_SPATIAL_DIMENSIONS_FIELD_NUMBER: builtins.int
    OUTPUT_BATCH_DIMENSION_FIELD_NUMBER: builtins.int
    OUTPUT_FEATURE_DIMENSION_FIELD_NUMBER: builtins.int
    OUTPUT_SPATIAL_DIMENSIONS_FIELD_NUMBER: builtins.int
    input_batch_dimension: builtins.int
    """The number of the dimension that represents batch in the input."""
    input_feature_dimension: builtins.int
    """The number of the dimension that represents features in the input."""
    kernel_input_feature_dimension: builtins.int
    """The number of the dimension that represents input features in the
    convolutional kernel (rhs).
    """
    kernel_output_feature_dimension: builtins.int
    """The number of the dimension that represents output features in
    the convolutional kernel (rhs).
    """
    output_batch_dimension: builtins.int
    """The number of the dimension that represents batch in the output."""
    output_feature_dimension: builtins.int
    """The number of the dimension that represents features in the output."""
    @property
    def input_spatial_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def kernel_spatial_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def output_spatial_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        input_batch_dimension: builtins.int | None = ...,
        input_feature_dimension: builtins.int | None = ...,
        input_spatial_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        kernel_input_feature_dimension: builtins.int | None = ...,
        kernel_output_feature_dimension: builtins.int | None = ...,
        kernel_spatial_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        output_batch_dimension: builtins.int | None = ...,
        output_feature_dimension: builtins.int | None = ...,
        output_spatial_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "input_batch_dimension",
            b"input_batch_dimension",
            "input_feature_dimension",
            b"input_feature_dimension",
            "input_spatial_dimensions",
            b"input_spatial_dimensions",
            "kernel_input_feature_dimension",
            b"kernel_input_feature_dimension",
            "kernel_output_feature_dimension",
            b"kernel_output_feature_dimension",
            "kernel_spatial_dimensions",
            b"kernel_spatial_dimensions",
            "output_batch_dimension",
            b"output_batch_dimension",
            "output_feature_dimension",
            b"output_feature_dimension",
            "output_spatial_dimensions",
            b"output_spatial_dimensions",
        ],
    ) -> None: ...

global___ConvolutionDimensionNumbers = ConvolutionDimensionNumbers

@typing.final
class DotDimensionNumbers(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LHS_CONTRACTING_DIMENSIONS_FIELD_NUMBER: builtins.int
    RHS_CONTRACTING_DIMENSIONS_FIELD_NUMBER: builtins.int
    LHS_BATCH_DIMENSIONS_FIELD_NUMBER: builtins.int
    RHS_BATCH_DIMENSIONS_FIELD_NUMBER: builtins.int
    @property
    def lhs_contracting_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def rhs_contracting_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def lhs_batch_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def rhs_batch_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        lhs_contracting_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        rhs_contracting_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        lhs_batch_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        rhs_batch_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "lhs_batch_dimensions",
            b"lhs_batch_dimensions",
            "lhs_contracting_dimensions",
            b"lhs_contracting_dimensions",
            "rhs_batch_dimensions",
            b"rhs_batch_dimensions",
            "rhs_contracting_dimensions",
            b"rhs_contracting_dimensions",
        ],
    ) -> None: ...

global___DotDimensionNumbers = DotDimensionNumbers

@typing.final
class SparsityDescriptor(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TYPE_FIELD_NUMBER: builtins.int
    INDEX_FIELD_NUMBER: builtins.int
    DIMENSION_FIELD_NUMBER: builtins.int
    N_FIELD_NUMBER: builtins.int
    M_FIELD_NUMBER: builtins.int
    type: global___SparsityType.ValueType
    index: builtins.int
    """Sparse operand index (0 or 1)."""
    dimension: builtins.int
    """Sparse dimension number."""
    n: builtins.int
    """Structured N:M sparsity (N < M)."""
    m: builtins.int
    def __init__(
        self,
        *,
        type: global___SparsityType.ValueType | None = ...,
        index: builtins.int | None = ...,
        dimension: builtins.int | None = ...,
        n: builtins.int | None = ...,
        m: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dimension",
            b"dimension",
            "index",
            b"index",
            "m",
            b"m",
            "n",
            b"n",
            "type",
            b"type",
        ],
    ) -> None: ...

global___SparsityDescriptor = SparsityDescriptor

@typing.final
class TriangularSolveOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Transpose:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _TransposeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            TriangularSolveOptions._Transpose.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        TRANSPOSE_INVALID: TriangularSolveOptions._Transpose.ValueType
        NO_TRANSPOSE: TriangularSolveOptions._Transpose.ValueType
        """Don't transpose 'a'."""
        TRANSPOSE: TriangularSolveOptions._Transpose.ValueType
        """Transpose 'a'."""
        ADJOINT: TriangularSolveOptions._Transpose.ValueType
        """Complex conjugate and transpose 'a'."""

    class Transpose(_Transpose, metaclass=_TransposeEnumTypeWrapper): ...
    TRANSPOSE_INVALID: TriangularSolveOptions.Transpose.ValueType
    NO_TRANSPOSE: TriangularSolveOptions.Transpose.ValueType
    """Don't transpose 'a'."""
    TRANSPOSE: TriangularSolveOptions.Transpose.ValueType
    """Transpose 'a'."""
    ADJOINT: TriangularSolveOptions.Transpose.ValueType
    """Complex conjugate and transpose 'a'."""
    LEFT_SIDE_FIELD_NUMBER: builtins.int
    LOWER_FIELD_NUMBER: builtins.int
    UNIT_DIAGONAL_FIELD_NUMBER: builtins.int
    TRANSPOSE_A_FIELD_NUMBER: builtins.int
    left_side: builtins.bool
    """If true, solves ax = b. If false, solves xa = b."""
    lower: builtins.bool
    """If true, 'a' is lower triangular. If false, 'a' is upper triangular."""
    unit_diagonal: builtins.bool
    """If true, the diagonal elements of 'a' are assumed to be 1 and not accessed."""
    transpose_a: global___TriangularSolveOptions.Transpose.ValueType
    def __init__(
        self,
        *,
        left_side: builtins.bool | None = ...,
        lower: builtins.bool | None = ...,
        unit_diagonal: builtins.bool | None = ...,
        transpose_a: global___TriangularSolveOptions.Transpose.ValueType
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "left_side",
            b"left_side",
            "lower",
            b"lower",
            "transpose_a",
            b"transpose_a",
            "unit_diagonal",
            b"unit_diagonal",
        ],
    ) -> None: ...

global___TriangularSolveOptions = TriangularSolveOptions

@typing.final
class CholeskyOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LOWER_FIELD_NUMBER: builtins.int
    lower: builtins.bool
    """If true, uses the lower triangle of `a`. If false, uses the upper triangle
    of `a`.
    """
    def __init__(self, *, lower: builtins.bool | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["lower", b"lower"],
    ) -> None: ...

global___CholeskyOptions = CholeskyOptions

@typing.final
class SortOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DESCENDING_FIELD_NUMBER: builtins.int
    descending: builtins.bool
    def __init__(self, *, descending: builtins.bool | None = ...) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["descending", b"descending"],
    ) -> None: ...

global___SortOptions = SortOptions

@typing.final
class FrontendAttributes(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class MapEntry(google.protobuf.message.Message):
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

    MAP_FIELD_NUMBER: builtins.int
    @property
    def map(
        self,
    ) -> google.protobuf.internal.containers.ScalarMap[
        builtins.str,
        builtins.str,
    ]: ...
    def __init__(
        self,
        *,
        map: collections.abc.Mapping[builtins.str, builtins.str] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["map", b"map"],
    ) -> None: ...

global___FrontendAttributes = FrontendAttributes

@typing.final
class Statistic(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    STAT_NAME_FIELD_NUMBER: builtins.int
    STAT_VAL_FIELD_NUMBER: builtins.int
    stat_name: builtins.str
    """Must be a single word consisting of any alphanumeric characters"""
    stat_val: builtins.float
    """Must be within a range of [0, 100], in order for the graph dumper to
    properly render the statistic onto the graph.
    """
    def __init__(
        self,
        *,
        stat_name: builtins.str | None = ...,
        stat_val: builtins.float | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "stat_name",
            b"stat_name",
            "stat_val",
            b"stat_val",
        ],
    ) -> None: ...

global___Statistic = Statistic

@typing.final
class StatisticsViz(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    STAT_INDEX_TO_VISUALIZE_FIELD_NUMBER: builtins.int
    STATISTICS_FIELD_NUMBER: builtins.int
    stat_index_to_visualize: builtins.int
    @property
    def statistics(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___Statistic
    ]: ...
    def __init__(
        self,
        *,
        stat_index_to_visualize: builtins.int | None = ...,
        statistics: collections.abc.Iterable[global___Statistic] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "stat_index_to_visualize",
            b"stat_index_to_visualize",
            "statistics",
            b"statistics",
        ],
    ) -> None: ...

global___StatisticsViz = StatisticsViz

@typing.final
class OpSharding(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Type:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _TypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            OpSharding._Type.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        REPLICATED: OpSharding._Type.ValueType
        """This sharding is replicated across all devices (implies maximal,
        all other fields are unused).
        """
        MAXIMAL: OpSharding._Type.ValueType
        """This sharding is maximal - one device runs the entire operation."""
        TUPLE: OpSharding._Type.ValueType
        """This sharding is a tuple - only the tuple_shardings field is valid."""
        OTHER: OpSharding._Type.ValueType
        """None of the above; tile_shape and tile_assignment are both used."""
        MANUAL: OpSharding._Type.ValueType
        """This op is manually sharded: the shapes are already partitioned and the
        partitioner should not change this op.
        """
        UNKNOWN: OpSharding._Type.ValueType
        """This sharding is a placeholder sharding with lowest precedence, it can be
        overwriten by any other shardings.
        """

    class Type(_Type, metaclass=_TypeEnumTypeWrapper): ...
    REPLICATED: OpSharding.Type.ValueType
    """This sharding is replicated across all devices (implies maximal,
    all other fields are unused).
    """
    MAXIMAL: OpSharding.Type.ValueType
    """This sharding is maximal - one device runs the entire operation."""
    TUPLE: OpSharding.Type.ValueType
    """This sharding is a tuple - only the tuple_shardings field is valid."""
    OTHER: OpSharding.Type.ValueType
    """None of the above; tile_shape and tile_assignment are both used."""
    MANUAL: OpSharding.Type.ValueType
    """This op is manually sharded: the shapes are already partitioned and the
    partitioner should not change this op.
    """
    UNKNOWN: OpSharding.Type.ValueType
    """This sharding is a placeholder sharding with lowest precedence, it can be
    overwriten by any other shardings.
    """
    class _ShardGroupType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ShardGroupTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            OpSharding._ShardGroupType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        AS: OpSharding._ShardGroupType.ValueType
        """This op will be sharded exactly the same as the other op. (hard
        restriction)
        """
        LIKE: OpSharding._ShardGroupType.ValueType
        """This op will try to allow sharding propagation within the same group even
        there is no data dependencies among them, but there is no guarantee that
        the final shardings within the same group will be exactly the same. (soft
        restriction)
        """

    class ShardGroupType(
        _ShardGroupType,
        metaclass=_ShardGroupTypeEnumTypeWrapper,
    ): ...
    AS: OpSharding.ShardGroupType.ValueType
    """This op will be sharded exactly the same as the other op. (hard
    restriction)
    """
    LIKE: OpSharding.ShardGroupType.ValueType
    """This op will try to allow sharding propagation within the same group even
    there is no data dependencies among them, but there is no guarantee that
    the final shardings within the same group will be exactly the same. (soft
    restriction)
    """
    TYPE_FIELD_NUMBER: builtins.int
    TILE_SHAPE_FIELD_NUMBER: builtins.int
    TILE_ASSIGNMENT_DIMENSIONS_FIELD_NUMBER: builtins.int
    TILE_ASSIGNMENT_DEVICES_FIELD_NUMBER: builtins.int
    TUPLE_SHARDINGS_FIELD_NUMBER: builtins.int
    REPLICATE_ON_LAST_TILE_DIM_FIELD_NUMBER: builtins.int
    METADATA_FIELD_NUMBER: builtins.int
    LAST_TILE_DIMS_FIELD_NUMBER: builtins.int
    IOTA_RESHAPE_DIMS_FIELD_NUMBER: builtins.int
    IOTA_TRANSPOSE_PERM_FIELD_NUMBER: builtins.int
    IS_SHARD_GROUP_FIELD_NUMBER: builtins.int
    SHARD_GROUP_ID_FIELD_NUMBER: builtins.int
    SHARD_GROUP_TYPE_FIELD_NUMBER: builtins.int
    type: global___OpSharding.Type.ValueType
    replicate_on_last_tile_dim: builtins.bool
    """Only used for OTHER type. If true, data is sharded according to other
    dimensions of tile_assignment(), but replicated across devices along the
    last dimension. (Experimental)
    """
    is_shard_group: builtins.bool
    """This field decides whether this op is in a shard group."""
    shard_group_id: builtins.int
    """This field is used to store the unique id of the shard group."""
    shard_group_type: global___OpSharding.ShardGroupType.ValueType
    @property
    def tile_shape(self) -> global___ShapeProto: ...
    @property
    def tile_assignment_dimensions(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def tile_assignment_devices(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def tuple_shardings(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___OpSharding
    ]: ...
    @property
    def metadata(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___OpMetadata
    ]: ...
    @property
    def last_tile_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        global___OpSharding.Type.ValueType
    ]: ...
    @property
    def iota_reshape_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def iota_transpose_perm(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        type: global___OpSharding.Type.ValueType | None = ...,
        tile_shape: global___ShapeProto | None = ...,
        tile_assignment_dimensions: collections.abc.Iterable[builtins.int]
        | None = ...,
        tile_assignment_devices: collections.abc.Iterable[builtins.int]
        | None = ...,
        tuple_shardings: collections.abc.Iterable[global___OpSharding]
        | None = ...,
        replicate_on_last_tile_dim: builtins.bool | None = ...,
        metadata: collections.abc.Iterable[global___OpMetadata] | None = ...,
        last_tile_dims: collections.abc.Iterable[
            global___OpSharding.Type.ValueType
        ]
        | None = ...,
        iota_reshape_dims: collections.abc.Iterable[builtins.int] | None = ...,
        iota_transpose_perm: collections.abc.Iterable[builtins.int]
        | None = ...,
        is_shard_group: builtins.bool | None = ...,
        shard_group_id: builtins.int | None = ...,
        shard_group_type: global___OpSharding.ShardGroupType.ValueType
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["tile_shape", b"tile_shape"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "iota_reshape_dims",
            b"iota_reshape_dims",
            "iota_transpose_perm",
            b"iota_transpose_perm",
            "is_shard_group",
            b"is_shard_group",
            "last_tile_dims",
            b"last_tile_dims",
            "metadata",
            b"metadata",
            "replicate_on_last_tile_dim",
            b"replicate_on_last_tile_dim",
            "shard_group_id",
            b"shard_group_id",
            "shard_group_type",
            b"shard_group_type",
            "tile_assignment_devices",
            b"tile_assignment_devices",
            "tile_assignment_dimensions",
            b"tile_assignment_dimensions",
            "tile_shape",
            b"tile_shape",
            "tuple_shardings",
            b"tuple_shardings",
            "type",
            b"type",
        ],
    ) -> None: ...

global___OpSharding = OpSharding

@typing.final
class ReplicaGroup(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    REPLICA_IDS_FIELD_NUMBER: builtins.int
    @property
    def replica_ids(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        replica_ids: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["replica_ids", b"replica_ids"],
    ) -> None: ...

global___ReplicaGroup = ReplicaGroup

@typing.final
class IotaReplicaGroupListProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NUM_REPLICA_GROUPS_FIELD_NUMBER: builtins.int
    NUM_DEVICES_PER_GROUP_FIELD_NUMBER: builtins.int
    IOTA_RESHAPE_DIMS_FIELD_NUMBER: builtins.int
    IOTA_TRANSPOSE_PERM_FIELD_NUMBER: builtins.int
    num_replica_groups: builtins.int
    """Number of replica groups."""
    num_devices_per_group: builtins.int
    """Number of devices per group."""
    @property
    def iota_reshape_dims(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def iota_transpose_perm(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        num_replica_groups: builtins.int | None = ...,
        num_devices_per_group: builtins.int | None = ...,
        iota_reshape_dims: collections.abc.Iterable[builtins.int] | None = ...,
        iota_transpose_perm: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "iota_reshape_dims",
            b"iota_reshape_dims",
            "iota_transpose_perm",
            b"iota_transpose_perm",
            "num_devices_per_group",
            b"num_devices_per_group",
            "num_replica_groups",
            b"num_replica_groups",
        ],
    ) -> None: ...

global___IotaReplicaGroupListProto = IotaReplicaGroupListProto

@typing.final
class CollectiveDeviceListProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    REPLICA_GROUPS_FIELD_NUMBER: builtins.int
    IOTA_REPLICA_GROUP_LIST_FIELD_NUMBER: builtins.int
    @property
    def replica_groups(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ReplicaGroup
    ]: ...
    @property
    def iota_replica_group_list(
        self,
    ) -> global___IotaReplicaGroupListProto: ...
    def __init__(
        self,
        *,
        replica_groups: collections.abc.Iterable[global___ReplicaGroup]
        | None = ...,
        iota_replica_group_list: global___IotaReplicaGroupListProto
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "iota_replica_group_list",
            b"iota_replica_group_list",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "iota_replica_group_list",
            b"iota_replica_group_list",
            "replica_groups",
            b"replica_groups",
        ],
    ) -> None: ...

global___CollectiveDeviceListProto = CollectiveDeviceListProto

@typing.final
class SourceTarget(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    SOURCE_FIELD_NUMBER: builtins.int
    TARGET_FIELD_NUMBER: builtins.int
    source: builtins.int
    target: builtins.int
    def __init__(
        self,
        *,
        source: builtins.int | None = ...,
        target: builtins.int | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["source", b"source", "target", b"target"],
    ) -> None: ...

global___SourceTarget = SourceTarget

@typing.final
class PrecisionConfig(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Precision:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _PrecisionEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            PrecisionConfig._Precision.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        DEFAULT: PrecisionConfig._Precision.ValueType
        HIGH: PrecisionConfig._Precision.ValueType
        HIGHEST: PrecisionConfig._Precision.ValueType
        PACKED_NIBBLE: PrecisionConfig._Precision.ValueType
        """Each U8/S8 value in a tensor actually represents 2 nibble values."""

    class Precision(_Precision, metaclass=_PrecisionEnumTypeWrapper): ...
    DEFAULT: PrecisionConfig.Precision.ValueType
    HIGH: PrecisionConfig.Precision.ValueType
    HIGHEST: PrecisionConfig.Precision.ValueType
    PACKED_NIBBLE: PrecisionConfig.Precision.ValueType
    """Each U8/S8 value in a tensor actually represents 2 nibble values."""
    class _Algorithm:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _AlgorithmEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            PrecisionConfig._Algorithm.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        ALG_UNSET: PrecisionConfig._Algorithm.ValueType
        """If the algorithm is `ALG_UNSET`, we will decide the algorithm based on
        the operand_precision values (for now).
        """
        ALG_DOT_ANY_F8_ANY_F8_F32: PrecisionConfig._Algorithm.ValueType
        """The storage type can be any 8-bit floating point type."""
        ALG_DOT_ANY_F8_ANY_F8_F32_FAST_ACCUM: (
            PrecisionConfig._Algorithm.ValueType
        )
        """The storage type can be any 8-bit floating point type. Intermediate
        results will not periodically be promoted to a higher precision. This
        corresponds to CUBLASLT_MATMUL_DESC_FAST_ACCUM. Triton's
        maxNumImpreciseAcc=32 setting may be similar.
        """
        ALG_DOT_F16_F16_F16: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_F16_F16_F32: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_BF16_BF16_BF16: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_BF16_BF16_F32: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_BF16_BF16_F32_X3: PrecisionConfig._Algorithm.ValueType
        """An algorithm which uses 3 BF16_BF16_F32 matmuls to achieve better
        precision.
        """
        ALG_DOT_BF16_BF16_F32_X6: PrecisionConfig._Algorithm.ValueType
        """An algorithm which uses 6 BF16_BF16_F32 matmuls to achieve better
        precision (similar to F32).
        """
        ALG_DOT_TF32_TF32_F32: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_TF32_TF32_F32_X3: PrecisionConfig._Algorithm.ValueType
        """An algorithm which uses 3 TF32_TF32_F32 matmuls to achieve better
        precision (similar to F32).
        """
        ALG_DOT_F32_F32_F32: PrecisionConfig._Algorithm.ValueType
        ALG_DOT_F64_F64_F64: PrecisionConfig._Algorithm.ValueType

    class Algorithm(_Algorithm, metaclass=_AlgorithmEnumTypeWrapper): ...
    ALG_UNSET: PrecisionConfig.Algorithm.ValueType
    """If the algorithm is `ALG_UNSET`, we will decide the algorithm based on
    the operand_precision values (for now).
    """
    ALG_DOT_ANY_F8_ANY_F8_F32: PrecisionConfig.Algorithm.ValueType
    """The storage type can be any 8-bit floating point type."""
    ALG_DOT_ANY_F8_ANY_F8_F32_FAST_ACCUM: PrecisionConfig.Algorithm.ValueType
    """The storage type can be any 8-bit floating point type. Intermediate
    results will not periodically be promoted to a higher precision. This
    corresponds to CUBLASLT_MATMUL_DESC_FAST_ACCUM. Triton's
    maxNumImpreciseAcc=32 setting may be similar.
    """
    ALG_DOT_F16_F16_F16: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_F16_F16_F32: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_BF16_BF16_BF16: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_BF16_BF16_F32: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_BF16_BF16_F32_X3: PrecisionConfig.Algorithm.ValueType
    """An algorithm which uses 3 BF16_BF16_F32 matmuls to achieve better
    precision.
    """
    ALG_DOT_BF16_BF16_F32_X6: PrecisionConfig.Algorithm.ValueType
    """An algorithm which uses 6 BF16_BF16_F32 matmuls to achieve better
    precision (similar to F32).
    """
    ALG_DOT_TF32_TF32_F32: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_TF32_TF32_F32_X3: PrecisionConfig.Algorithm.ValueType
    """An algorithm which uses 3 TF32_TF32_F32 matmuls to achieve better
    precision (similar to F32).
    """
    ALG_DOT_F32_F32_F32: PrecisionConfig.Algorithm.ValueType
    ALG_DOT_F64_F64_F64: PrecisionConfig.Algorithm.ValueType
    OPERAND_PRECISION_FIELD_NUMBER: builtins.int
    ALGORITHM_FIELD_NUMBER: builtins.int
    algorithm: global___PrecisionConfig.Algorithm.ValueType
    """Currently doesn't do anything, but we plan to support it for dot and
    possibly more instructions.

    TODO(b/316147294): Support this on GPU and add this to StableHLO as well.

    If this is set, then `operand_precision` should be set to DEFAULT and it
    will be ignored.
    """
    @property
    def operand_precision(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        global___PrecisionConfig.Precision.ValueType
    ]: ...
    def __init__(
        self,
        *,
        operand_precision: collections.abc.Iterable[
            global___PrecisionConfig.Precision.ValueType
        ]
        | None = ...,
        algorithm: global___PrecisionConfig.Algorithm.ValueType | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "algorithm",
            b"algorithm",
            "operand_precision",
            b"operand_precision",
        ],
    ) -> None: ...

global___PrecisionConfig = PrecisionConfig

@typing.final
class ParameterReplication(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    REPLICATED_AT_LEAF_BUFFERS_FIELD_NUMBER: builtins.int
    @property
    def replicated_at_leaf_buffers(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.bool
    ]: ...
    def __init__(
        self,
        *,
        replicated_at_leaf_buffers: collections.abc.Iterable[builtins.bool]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "replicated_at_leaf_buffers",
            b"replicated_at_leaf_buffers",
        ],
    ) -> None: ...

global___ParameterReplication = ParameterReplication

@typing.final
class WhileLoopBackendConfig(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class KnownTripCount(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        N_FIELD_NUMBER: builtins.int
        n: builtins.int
        def __init__(self, *, n: builtins.int | None = ...) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["n", b"n"],
        ) -> None: ...

    KNOWN_TRIP_COUNT_FIELD_NUMBER: builtins.int
    @property
    def known_trip_count(
        self,
    ) -> global___WhileLoopBackendConfig.KnownTripCount: ...
    def __init__(
        self,
        *,
        known_trip_count: global___WhileLoopBackendConfig.KnownTripCount
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["known_trip_count", b"known_trip_count"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["known_trip_count", b"known_trip_count"],
    ) -> None: ...

global___WhileLoopBackendConfig = WhileLoopBackendConfig

@typing.final
class OutputOperandAliasing(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    OUTPUT_SHAPE_INDEX_FIELD_NUMBER: builtins.int
    OPERAND_INDEX_FIELD_NUMBER: builtins.int
    OPERAND_SHAPE_INDEX_FIELD_NUMBER: builtins.int
    operand_index: builtins.int
    @property
    def output_shape_index(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def operand_shape_index(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        output_shape_index: collections.abc.Iterable[builtins.int]
        | None = ...,
        operand_index: builtins.int | None = ...,
        operand_shape_index: collections.abc.Iterable[builtins.int]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "operand_index",
            b"operand_index",
            "operand_shape_index",
            b"operand_shape_index",
            "output_shape_index",
            b"output_shape_index",
        ],
    ) -> None: ...

global___OutputOperandAliasing = OutputOperandAliasing

@typing.final
class OriginalArrayProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LEAF_SHAPE_INDEX_FIELD_NUMBER: builtins.int
    INSTRUCTION_NAME_FIELD_NUMBER: builtins.int
    SHAPE_INDEX_FIELD_NUMBER: builtins.int
    instruction_name: builtins.str
    @property
    def leaf_shape_index(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def shape_index(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    def __init__(
        self,
        *,
        leaf_shape_index: collections.abc.Iterable[builtins.int] | None = ...,
        instruction_name: builtins.str | None = ...,
        shape_index: collections.abc.Iterable[builtins.int] | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "instruction_name",
            b"instruction_name",
            "leaf_shape_index",
            b"leaf_shape_index",
            "shape_index",
            b"shape_index",
        ],
    ) -> None: ...

global___OriginalArrayProto = OriginalArrayProto

@typing.final
class OriginalValueProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    LEAVES_FIELD_NUMBER: builtins.int
    @property
    def leaves(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___OriginalArrayProto
    ]: ...
    def __init__(
        self,
        *,
        leaves: collections.abc.Iterable[global___OriginalArrayProto]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["leaves", b"leaves"],
    ) -> None: ...

global___OriginalValueProto = OriginalValueProto
