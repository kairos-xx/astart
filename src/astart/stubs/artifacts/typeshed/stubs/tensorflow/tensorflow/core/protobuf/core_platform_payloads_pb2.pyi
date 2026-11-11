import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class ErrorSourceProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _ErrorSource:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ErrorSourceEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            ErrorSourceProto._ErrorSource.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UNKNOWN: ErrorSourceProto._ErrorSource.ValueType
        TPU_COMPILE_OP: ErrorSourceProto._ErrorSource.ValueType
        TF_XLA_BRIDGE: ErrorSourceProto._ErrorSource.ValueType
        """Old bridge."""
        MLIR_BRIDGE_PHASE_1: ErrorSourceProto._ErrorSource.ValueType
        """TPUBridge."""
        MLIR_BRIDGE_PHASE_2: ErrorSourceProto._ErrorSource.ValueType
        """LegalizeToHlo."""
        EAGER_REMOTE_MGR: ErrorSourceProto._ErrorSource.ValueType
        """eager::RemoteMgr."""

    class ErrorSource(_ErrorSource, metaclass=_ErrorSourceEnumTypeWrapper): ...
    UNKNOWN: ErrorSourceProto.ErrorSource.ValueType
    TPU_COMPILE_OP: ErrorSourceProto.ErrorSource.ValueType
    TF_XLA_BRIDGE: ErrorSourceProto.ErrorSource.ValueType
    """Old bridge."""
    MLIR_BRIDGE_PHASE_1: ErrorSourceProto.ErrorSource.ValueType
    """TPUBridge."""
    MLIR_BRIDGE_PHASE_2: ErrorSourceProto.ErrorSource.ValueType
    """LegalizeToHlo."""
    EAGER_REMOTE_MGR: ErrorSourceProto.ErrorSource.ValueType
    """eager::RemoteMgr."""
    ERROR_SOURCE_FIELD_NUMBER: builtins.int
    error_source: global___ErrorSourceProto.ErrorSource.ValueType
    def __init__(
        self,
        *,
        error_source: global___ErrorSourceProto.ErrorSource.ValueType
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["error_source", b"error_source"],
    ) -> None: ...

global___ErrorSourceProto = ErrorSourceProto
