import builtins
import typing

import google.protobuf.descriptor
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class VerifierConfig(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Toggle:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _ToggleEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            VerifierConfig._Toggle.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        DEFAULT: VerifierConfig._Toggle.ValueType
        ON: VerifierConfig._Toggle.ValueType
        OFF: VerifierConfig._Toggle.ValueType

    class Toggle(_Toggle, metaclass=_ToggleEnumTypeWrapper): ...
    DEFAULT: VerifierConfig.Toggle.ValueType
    ON: VerifierConfig.Toggle.ValueType
    OFF: VerifierConfig.Toggle.ValueType
    VERIFICATION_TIMEOUT_IN_MS_FIELD_NUMBER: builtins.int
    STRUCTURE_VERIFIER_FIELD_NUMBER: builtins.int
    verification_timeout_in_ms: builtins.int
    """Deadline for completion of all verification i.e. all the Toggle ON
    verifiers must complete execution within this time.
    """
    structure_verifier: global___VerifierConfig.Toggle.ValueType
    """Perform structural validation on a tensorflow graph. Default is OFF."""
    def __init__(
        self,
        *,
        verification_timeout_in_ms: builtins.int | None = ...,
        structure_verifier: global___VerifierConfig.Toggle.ValueType
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "structure_verifier",
            b"structure_verifier",
            "verification_timeout_in_ms",
            b"verification_timeout_in_ms",
        ],
    ) -> None: ...

global___VerifierConfig = VerifierConfig
