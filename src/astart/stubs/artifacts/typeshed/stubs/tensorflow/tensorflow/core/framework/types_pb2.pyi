import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

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
    DT_INVALID: _DataType.ValueType
    """Not a legal value for DataType.  Used to indicate a DataType field
    has not been set.
    """
    DT_FLOAT: _DataType.ValueType
    """Data types that all computation devices are expected to be
    capable to support.
    """
    DT_DOUBLE: _DataType.ValueType
    DT_INT32: _DataType.ValueType
    DT_UINT8: _DataType.ValueType
    DT_INT16: _DataType.ValueType
    DT_INT8: _DataType.ValueType
    DT_STRING: _DataType.ValueType
    DT_COMPLEX64: _DataType.ValueType
    """Single-precision complex"""
    DT_INT64: _DataType.ValueType
    DT_BOOL: _DataType.ValueType
    DT_QINT8: _DataType.ValueType
    """Quantized int8"""
    DT_QUINT8: _DataType.ValueType
    """Quantized uint8"""
    DT_QINT32: _DataType.ValueType
    """Quantized int32"""
    DT_BFLOAT16: _DataType.ValueType
    """Float32 truncated to 16 bits."""
    DT_QINT16: _DataType.ValueType
    """Quantized int16"""
    DT_QUINT16: _DataType.ValueType
    """Quantized uint16"""
    DT_UINT16: _DataType.ValueType
    DT_COMPLEX128: _DataType.ValueType
    """Double-precision complex"""
    DT_HALF: _DataType.ValueType
    DT_RESOURCE: _DataType.ValueType
    DT_VARIANT: _DataType.ValueType
    """Arbitrary C++ data types"""
    DT_UINT32: _DataType.ValueType
    DT_UINT64: _DataType.ValueType
    DT_FLOAT8_E5M2: _DataType.ValueType
    """5 exponent bits, 2 mantissa bits."""
    DT_FLOAT8_E4M3FN: _DataType.ValueType
    """4 exponent bits, 3 mantissa bits, finite-only, with"""
    DT_INT4: _DataType.ValueType
    """2 NaNs (0bS1111111).
    TODO - b/299182407: Leaving room for remaining float8 types.
    DT_FLOAT8_E4M3FNUZ = 26;
    DT_FLOAT8_E4M3B11FNUZ = 27;
    DT_FLOAT8_E5M2FNUZ = 28;
    """
    DT_UINT4: _DataType.ValueType
    DT_FLOAT_REF: _DataType.ValueType
    """Do not use!  These are only for TF1's obsolete reference Variables.
    Every enum above should have a corresponding value below (verified by
    types_test).
    """
    DT_DOUBLE_REF: _DataType.ValueType
    DT_INT32_REF: _DataType.ValueType
    DT_UINT8_REF: _DataType.ValueType
    DT_INT16_REF: _DataType.ValueType
    DT_INT8_REF: _DataType.ValueType
    DT_STRING_REF: _DataType.ValueType
    DT_COMPLEX64_REF: _DataType.ValueType
    DT_INT64_REF: _DataType.ValueType
    DT_BOOL_REF: _DataType.ValueType
    DT_QINT8_REF: _DataType.ValueType
    DT_QUINT8_REF: _DataType.ValueType
    DT_QINT32_REF: _DataType.ValueType
    DT_BFLOAT16_REF: _DataType.ValueType
    DT_QINT16_REF: _DataType.ValueType
    DT_QUINT16_REF: _DataType.ValueType
    DT_UINT16_REF: _DataType.ValueType
    DT_COMPLEX128_REF: _DataType.ValueType
    DT_HALF_REF: _DataType.ValueType
    DT_RESOURCE_REF: _DataType.ValueType
    DT_VARIANT_REF: _DataType.ValueType
    DT_UINT32_REF: _DataType.ValueType
    DT_UINT64_REF: _DataType.ValueType
    DT_FLOAT8_E5M2_REF: _DataType.ValueType
    DT_FLOAT8_E4M3FN_REF: _DataType.ValueType
    DT_INT4_REF: _DataType.ValueType
    """TODO - b/299182407: Leaving room for remaining float8 types.
    DT_FLOAT8_E4M3FNUZ_REF = 126;
    DT_FLOAT8_E4M3B11FNUZ_REF = 127;
    DT_FLOAT8_E5M2FNUZ_REF = 128;
    """
    DT_UINT4_REF: _DataType.ValueType

class DataType(_DataType, metaclass=_DataTypeEnumTypeWrapper): ...

DT_INVALID: DataType.ValueType
"""Not a legal value for DataType.  Used to indicate a DataType field
has not been set.
"""
DT_FLOAT: DataType.ValueType
"""Data types that all computation devices are expected to be
capable to support.
"""
DT_DOUBLE: DataType.ValueType
DT_INT32: DataType.ValueType
DT_UINT8: DataType.ValueType
DT_INT16: DataType.ValueType
DT_INT8: DataType.ValueType
DT_STRING: DataType.ValueType
DT_COMPLEX64: DataType.ValueType
"""Single-precision complex"""
DT_INT64: DataType.ValueType
DT_BOOL: DataType.ValueType
DT_QINT8: DataType.ValueType
"""Quantized int8"""
DT_QUINT8: DataType.ValueType
"""Quantized uint8"""
DT_QINT32: DataType.ValueType
"""Quantized int32"""
DT_BFLOAT16: DataType.ValueType
"""Float32 truncated to 16 bits."""
DT_QINT16: DataType.ValueType
"""Quantized int16"""
DT_QUINT16: DataType.ValueType
"""Quantized uint16"""
DT_UINT16: DataType.ValueType
DT_COMPLEX128: DataType.ValueType
"""Double-precision complex"""
DT_HALF: DataType.ValueType
DT_RESOURCE: DataType.ValueType
DT_VARIANT: DataType.ValueType
"""Arbitrary C++ data types"""
DT_UINT32: DataType.ValueType
DT_UINT64: DataType.ValueType
DT_FLOAT8_E5M2: DataType.ValueType
"""5 exponent bits, 2 mantissa bits."""
DT_FLOAT8_E4M3FN: DataType.ValueType
"""4 exponent bits, 3 mantissa bits, finite-only, with"""
DT_INT4: DataType.ValueType
"""2 NaNs (0bS1111111).
TODO - b/299182407: Leaving room for remaining float8 types.
DT_FLOAT8_E4M3FNUZ = 26;
DT_FLOAT8_E4M3B11FNUZ = 27;
DT_FLOAT8_E5M2FNUZ = 28;
"""
DT_UINT4: DataType.ValueType
DT_FLOAT_REF: DataType.ValueType
"""Do not use!  These are only for TF1's obsolete reference Variables.
Every enum above should have a corresponding value below (verified by
types_test).
"""
DT_DOUBLE_REF: DataType.ValueType
DT_INT32_REF: DataType.ValueType
DT_UINT8_REF: DataType.ValueType
DT_INT16_REF: DataType.ValueType
DT_INT8_REF: DataType.ValueType
DT_STRING_REF: DataType.ValueType
DT_COMPLEX64_REF: DataType.ValueType
DT_INT64_REF: DataType.ValueType
DT_BOOL_REF: DataType.ValueType
DT_QINT8_REF: DataType.ValueType
DT_QUINT8_REF: DataType.ValueType
DT_QINT32_REF: DataType.ValueType
DT_BFLOAT16_REF: DataType.ValueType
DT_QINT16_REF: DataType.ValueType
DT_QUINT16_REF: DataType.ValueType
DT_UINT16_REF: DataType.ValueType
DT_COMPLEX128_REF: DataType.ValueType
DT_HALF_REF: DataType.ValueType
DT_RESOURCE_REF: DataType.ValueType
DT_VARIANT_REF: DataType.ValueType
DT_UINT32_REF: DataType.ValueType
DT_UINT64_REF: DataType.ValueType
DT_FLOAT8_E5M2_REF: DataType.ValueType
DT_FLOAT8_E4M3FN_REF: DataType.ValueType
DT_INT4_REF: DataType.ValueType
"""TODO - b/299182407: Leaving room for remaining float8 types.
DT_FLOAT8_E4M3FNUZ_REF = 126;
DT_FLOAT8_E4M3B11FNUZ_REF = 127;
DT_FLOAT8_E5M2FNUZ_REF = 128;
"""
DT_UINT4_REF: DataType.ValueType
global___DataType = DataType

@typing.final
class SerializedDType(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DATATYPE_FIELD_NUMBER: builtins.int
    datatype: global___DataType.ValueType
    def __init__(
        self,
        *,
        datatype: global___DataType.ValueType | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["datatype", b"datatype"],
    ) -> None: ...

global___SerializedDType = SerializedDType
