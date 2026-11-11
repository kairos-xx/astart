import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.internal.enum_type_wrapper
import google.protobuf.message

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

class _Edition:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _EditionEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _Edition.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    EDITION_UNKNOWN: _Edition.ValueType
    """A placeholder for an unknown edition value."""
    EDITION_LEGACY: _Edition.ValueType
    """A placeholder edition for specifying default behaviors *before* a feature
    was first introduced.  This is effectively an "infinite past".
    """
    EDITION_PROTO2: _Edition.ValueType
    """Legacy syntax "editions".  These pre-date editions, but behave much like
    distinct editions.  These can't be used to specify the edition of proto
    files, but feature definitions must supply proto2/proto3 defaults for
    backwards compatibility.
    """
    EDITION_PROTO3: _Edition.ValueType
    EDITION_2023: _Edition.ValueType
    """Editions that have been released.  The specific values are arbitrary and
    should not be depended on, but they will always be time-ordered for easy
    comparison.
    """
    EDITION_2024: _Edition.ValueType
    EDITION_1_TEST_ONLY: _Edition.ValueType
    """Placeholder editions for testing feature resolution.  These should not be
    used or relied on outside of tests.
    """
    EDITION_2_TEST_ONLY: _Edition.ValueType
    EDITION_99997_TEST_ONLY: _Edition.ValueType
    EDITION_99998_TEST_ONLY: _Edition.ValueType
    EDITION_99999_TEST_ONLY: _Edition.ValueType
    EDITION_MAX: _Edition.ValueType
    """Placeholder for specifying unbounded edition support.  This should only
    ever be used by plugins that can expect to never require any changes to
    support a new edition.
    """

class Edition(_Edition, metaclass=_EditionEnumTypeWrapper): ...

EDITION_UNKNOWN: Edition.ValueType
"""A placeholder for an unknown edition value."""
EDITION_LEGACY: Edition.ValueType
"""A placeholder edition for specifying default behaviors *before* a feature
was first introduced.  This is effectively an "infinite past".
"""
EDITION_PROTO2: Edition.ValueType
"""Legacy syntax "editions".  These pre-date editions, but behave much like
distinct editions.  These can't be used to specify the edition of proto
files, but feature definitions must supply proto2/proto3 defaults for
backwards compatibility.
"""
EDITION_PROTO3: Edition.ValueType
EDITION_2023: Edition.ValueType
"""Editions that have been released.  The specific values are arbitrary and
should not be depended on, but they will always be time-ordered for easy
comparison.
"""
EDITION_2024: Edition.ValueType
EDITION_1_TEST_ONLY: Edition.ValueType
"""Placeholder editions for testing feature resolution.  These should not be
used or relied on outside of tests.
"""
EDITION_2_TEST_ONLY: Edition.ValueType
EDITION_99997_TEST_ONLY: Edition.ValueType
EDITION_99998_TEST_ONLY: Edition.ValueType
EDITION_99999_TEST_ONLY: Edition.ValueType
EDITION_MAX: Edition.ValueType
"""Placeholder for specifying unbounded edition support.  This should only
ever be used by plugins that can expect to never require any changes to
support a new edition.
"""
global___Edition = Edition

class _SymbolVisibility:
    ValueType = typing.NewType("ValueType", builtins.int)
    type V = ValueType

class _SymbolVisibilityEnumTypeWrapper(
    google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
        _SymbolVisibility.ValueType
    ],
    builtins.type,
):
    DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
    VISIBILITY_UNSET: _SymbolVisibility.ValueType
    VISIBILITY_LOCAL: _SymbolVisibility.ValueType
    VISIBILITY_EXPORT: _SymbolVisibility.ValueType

class SymbolVisibility(
    _SymbolVisibility,
    metaclass=_SymbolVisibilityEnumTypeWrapper,
): ...

VISIBILITY_UNSET: SymbolVisibility.ValueType
VISIBILITY_LOCAL: SymbolVisibility.ValueType
VISIBILITY_EXPORT: SymbolVisibility.ValueType
global___SymbolVisibility = SymbolVisibility

@typing.final
class FileDescriptorSet(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FILE_FIELD_NUMBER: builtins.int
    @property
    def file(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FileDescriptorProto
    ]: ...
    def __init__(
        self,
        *,
        file: collections.abc.Iterable[global___FileDescriptorProto]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["file", b"file"],
    ) -> None: ...

global___FileDescriptorSet = FileDescriptorSet

@typing.final
class FileDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    PACKAGE_FIELD_NUMBER: builtins.int
    DEPENDENCY_FIELD_NUMBER: builtins.int
    PUBLIC_DEPENDENCY_FIELD_NUMBER: builtins.int
    WEAK_DEPENDENCY_FIELD_NUMBER: builtins.int
    OPTION_DEPENDENCY_FIELD_NUMBER: builtins.int
    MESSAGE_TYPE_FIELD_NUMBER: builtins.int
    ENUM_TYPE_FIELD_NUMBER: builtins.int
    SERVICE_FIELD_NUMBER: builtins.int
    EXTENSION_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    SOURCE_CODE_INFO_FIELD_NUMBER: builtins.int
    SYNTAX_FIELD_NUMBER: builtins.int
    EDITION_FIELD_NUMBER: builtins.int
    name: builtins.str
    """file name, relative to root of source tree"""
    package: builtins.str
    """e.g. "foo", "foo.bar", etc."""
    syntax: builtins.str
    """The syntax of the proto file.
    The supported values are "proto2", "proto3", and "editions".

    If `edition` is present, this value must be "editions".
    WARNING: This field should only be used by protobuf plugins or special
    cases like the proto compiler. Other uses are discouraged and
    developers should rely on the protoreflect APIs for their client language.
    """
    edition: global___Edition.ValueType
    """The edition of the proto file.
    WARNING: This field should only be used by protobuf plugins or special
    cases like the proto compiler. Other uses are discouraged and
    developers should rely on the protoreflect APIs for their client language.
    """
    @property
    def dependency(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    @property
    def public_dependency(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def weak_dependency(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.int
    ]: ...
    @property
    def option_dependency(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    @property
    def message_type(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___DescriptorProto
    ]: ...
    @property
    def enum_type(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___EnumDescriptorProto
    ]: ...
    @property
    def service(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ServiceDescriptorProto
    ]: ...
    @property
    def extension(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FieldDescriptorProto
    ]: ...
    @property
    def options(self) -> global___FileOptions: ...
    @property
    def source_code_info(self) -> global___SourceCodeInfo: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        package: builtins.str | None = ...,
        dependency: collections.abc.Iterable[builtins.str] | None = ...,
        public_dependency: collections.abc.Iterable[builtins.int] | None = ...,
        weak_dependency: collections.abc.Iterable[builtins.int] | None = ...,
        option_dependency: collections.abc.Iterable[builtins.str] | None = ...,
        message_type: collections.abc.Iterable[global___DescriptorProto]
        | None = ...,
        enum_type: collections.abc.Iterable[global___EnumDescriptorProto]
        | None = ...,
        service: collections.abc.Iterable[global___ServiceDescriptorProto]
        | None = ...,
        extension: collections.abc.Iterable[global___FieldDescriptorProto]
        | None = ...,
        options: global___FileOptions | None = ...,
        source_code_info: global___SourceCodeInfo | None = ...,
        syntax: builtins.str | None = ...,
        edition: global___Edition.ValueType | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "edition",
            b"edition",
            "name",
            b"name",
            "options",
            b"options",
            "package",
            b"package",
            "source_code_info",
            b"source_code_info",
            "syntax",
            b"syntax",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "dependency",
            b"dependency",
            "edition",
            b"edition",
            "enum_type",
            b"enum_type",
            "extension",
            b"extension",
            "message_type",
            b"message_type",
            "name",
            b"name",
            "option_dependency",
            b"option_dependency",
            "options",
            b"options",
            "package",
            b"package",
            "public_dependency",
            b"public_dependency",
            "service",
            b"service",
            "source_code_info",
            b"source_code_info",
            "syntax",
            b"syntax",
            "weak_dependency",
            b"weak_dependency",
        ],
    ) -> None: ...

global___FileDescriptorProto = FileDescriptorProto

@typing.final
class DescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class ExtensionRange(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        START_FIELD_NUMBER: builtins.int
        END_FIELD_NUMBER: builtins.int
        OPTIONS_FIELD_NUMBER: builtins.int
        start: builtins.int
        """Inclusive."""
        end: builtins.int
        """Exclusive."""
        @property
        def options(self) -> global___ExtensionRangeOptions: ...
        def __init__(
            self,
            *,
            start: builtins.int | None = ...,
            end: builtins.int | None = ...,
            options: global___ExtensionRangeOptions | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "end",
                b"end",
                "options",
                b"options",
                "start",
                b"start",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "end",
                b"end",
                "options",
                b"options",
                "start",
                b"start",
            ],
        ) -> None: ...

    @typing.final
    class ReservedRange(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        START_FIELD_NUMBER: builtins.int
        END_FIELD_NUMBER: builtins.int
        start: builtins.int
        """Inclusive."""
        end: builtins.int
        """Exclusive."""
        def __init__(
            self,
            *,
            start: builtins.int | None = ...,
            end: builtins.int | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["end", b"end", "start", b"start"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["end", b"end", "start", b"start"],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    FIELD_FIELD_NUMBER: builtins.int
    EXTENSION_FIELD_NUMBER: builtins.int
    NESTED_TYPE_FIELD_NUMBER: builtins.int
    ENUM_TYPE_FIELD_NUMBER: builtins.int
    EXTENSION_RANGE_FIELD_NUMBER: builtins.int
    ONEOF_DECL_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    RESERVED_RANGE_FIELD_NUMBER: builtins.int
    RESERVED_NAME_FIELD_NUMBER: builtins.int
    VISIBILITY_FIELD_NUMBER: builtins.int
    name: builtins.str
    visibility: global___SymbolVisibility.ValueType
    """Support for `export` and `local` keywords on enums."""
    @property
    def field(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FieldDescriptorProto
    ]: ...
    @property
    def extension(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FieldDescriptorProto
    ]: ...
    @property
    def nested_type(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___DescriptorProto
    ]: ...
    @property
    def enum_type(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___EnumDescriptorProto
    ]: ...
    @property
    def extension_range(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___DescriptorProto.ExtensionRange
    ]: ...
    @property
    def oneof_decl(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___OneofDescriptorProto
    ]: ...
    @property
    def options(self) -> global___MessageOptions: ...
    @property
    def reserved_range(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___DescriptorProto.ReservedRange
    ]: ...
    @property
    def reserved_name(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        field: collections.abc.Iterable[global___FieldDescriptorProto]
        | None = ...,
        extension: collections.abc.Iterable[global___FieldDescriptorProto]
        | None = ...,
        nested_type: collections.abc.Iterable[global___DescriptorProto]
        | None = ...,
        enum_type: collections.abc.Iterable[global___EnumDescriptorProto]
        | None = ...,
        extension_range: collections.abc.Iterable[
            global___DescriptorProto.ExtensionRange
        ]
        | None = ...,
        oneof_decl: collections.abc.Iterable[global___OneofDescriptorProto]
        | None = ...,
        options: global___MessageOptions | None = ...,
        reserved_range: collections.abc.Iterable[
            global___DescriptorProto.ReservedRange
        ]
        | None = ...,
        reserved_name: collections.abc.Iterable[builtins.str] | None = ...,
        visibility: global___SymbolVisibility.ValueType | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "options",
            b"options",
            "visibility",
            b"visibility",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "enum_type",
            b"enum_type",
            "extension",
            b"extension",
            "extension_range",
            b"extension_range",
            "field",
            b"field",
            "name",
            b"name",
            "nested_type",
            b"nested_type",
            "oneof_decl",
            b"oneof_decl",
            "options",
            b"options",
            "reserved_name",
            b"reserved_name",
            "reserved_range",
            b"reserved_range",
            "visibility",
            b"visibility",
        ],
    ) -> None: ...

global___DescriptorProto = DescriptorProto

@typing.final
class ExtensionRangeOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _VerificationState:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _VerificationStateEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            ExtensionRangeOptions._VerificationState.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        DECLARATION: ExtensionRangeOptions._VerificationState.ValueType
        """All the extensions of the range must be declared."""
        UNVERIFIED: ExtensionRangeOptions._VerificationState.ValueType

    class VerificationState(
        _VerificationState,
        metaclass=_VerificationStateEnumTypeWrapper,
    ): ...
    DECLARATION: ExtensionRangeOptions.VerificationState.ValueType
    """All the extensions of the range must be declared."""
    UNVERIFIED: ExtensionRangeOptions.VerificationState.ValueType
    @typing.final
    class Declaration(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NUMBER_FIELD_NUMBER: builtins.int
        FULL_NAME_FIELD_NUMBER: builtins.int
        TYPE_FIELD_NUMBER: builtins.int
        RESERVED_FIELD_NUMBER: builtins.int
        REPEATED_FIELD_NUMBER: builtins.int
        number: builtins.int
        """The extension number declared within the extension range."""
        full_name: builtins.str
        """The fully-qualified name of the extension field. There must be a leading
        dot in front of the full name.
        """
        type: builtins.str
        """The fully-qualified type name of the extension field. Unlike
        Metadata.type, Declaration.type must have a leading dot for messages
        and enums.
        """
        reserved: builtins.bool
        """If true, indicates that the number is reserved in the extension range,
        and any extension field with the number will fail to compile. Set this
        when a declared extension field is deleted.
        """
        repeated: builtins.bool
        """If true, indicates that the extension must be defined as repeated.
        Otherwise the extension must be defined as optional.
        """
        def __init__(
            self,
            *,
            number: builtins.int | None = ...,
            full_name: builtins.str | None = ...,
            type: builtins.str | None = ...,
            reserved: builtins.bool | None = ...,
            repeated: builtins.bool | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "full_name",
                b"full_name",
                "number",
                b"number",
                "repeated",
                b"repeated",
                "reserved",
                b"reserved",
                "type",
                b"type",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "full_name",
                b"full_name",
                "number",
                b"number",
                "repeated",
                b"repeated",
                "reserved",
                b"reserved",
                "type",
                b"type",
            ],
        ) -> None: ...

    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    DECLARATION_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    VERIFICATION_FIELD_NUMBER: builtins.int
    verification: global___ExtensionRangeOptions.VerificationState.ValueType
    """The verification state of the range.
    TODO: flip the default to DECLARATION once all empty ranges
    are marked as UNVERIFIED.
    """
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    @property
    def declaration(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___ExtensionRangeOptions.Declaration
    ]: ...
    @property
    def features(self) -> global___FeatureSet: ...
    def __init__(
        self,
        *,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
        declaration: collections.abc.Iterable[
            global___ExtensionRangeOptions.Declaration
        ]
        | None = ...,
        features: global___FeatureSet | None = ...,
        verification: global___ExtensionRangeOptions.VerificationState.ValueType
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "features",
            b"features",
            "verification",
            b"verification",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "declaration",
            b"declaration",
            "features",
            b"features",
            "uninterpreted_option",
            b"uninterpreted_option",
            "verification",
            b"verification",
        ],
    ) -> None: ...

global___ExtensionRangeOptions = ExtensionRangeOptions

@typing.final
class FieldDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _Type:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _TypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldDescriptorProto._Type.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        TYPE_DOUBLE: FieldDescriptorProto._Type.ValueType
        """0 is reserved for errors.
        Order is weird for historical reasons.
        """
        TYPE_FLOAT: FieldDescriptorProto._Type.ValueType
        TYPE_INT64: FieldDescriptorProto._Type.ValueType
        """Not ZigZag encoded.  Negative numbers take 10 bytes.  Use TYPE_SINT64 if
        negative values are likely.
        """
        TYPE_UINT64: FieldDescriptorProto._Type.ValueType
        TYPE_INT32: FieldDescriptorProto._Type.ValueType
        """Not ZigZag encoded.  Negative numbers take 10 bytes.  Use TYPE_SINT32 if
        negative values are likely.
        """
        TYPE_FIXED64: FieldDescriptorProto._Type.ValueType
        TYPE_FIXED32: FieldDescriptorProto._Type.ValueType
        TYPE_BOOL: FieldDescriptorProto._Type.ValueType
        TYPE_STRING: FieldDescriptorProto._Type.ValueType
        TYPE_GROUP: FieldDescriptorProto._Type.ValueType
        """Tag-delimited aggregate.
        Group type is deprecated and not supported after google.protobuf. However, Proto3
        implementations should still be able to parse the group wire format and
        treat group fields as unknown fields.  In Editions, the group wire format
        can be enabled via the `message_encoding` feature.
        """
        TYPE_MESSAGE: FieldDescriptorProto._Type.ValueType
        """Length-delimited aggregate."""
        TYPE_BYTES: FieldDescriptorProto._Type.ValueType
        """New in version 2."""
        TYPE_UINT32: FieldDescriptorProto._Type.ValueType
        TYPE_ENUM: FieldDescriptorProto._Type.ValueType
        TYPE_SFIXED32: FieldDescriptorProto._Type.ValueType
        TYPE_SFIXED64: FieldDescriptorProto._Type.ValueType
        TYPE_SINT32: FieldDescriptorProto._Type.ValueType
        """Uses ZigZag encoding."""
        TYPE_SINT64: FieldDescriptorProto._Type.ValueType
        """Uses ZigZag encoding."""

    class Type(_Type, metaclass=_TypeEnumTypeWrapper): ...
    TYPE_DOUBLE: FieldDescriptorProto.Type.ValueType
    """0 is reserved for errors.
    Order is weird for historical reasons.
    """
    TYPE_FLOAT: FieldDescriptorProto.Type.ValueType
    TYPE_INT64: FieldDescriptorProto.Type.ValueType
    """Not ZigZag encoded.  Negative numbers take 10 bytes.  Use TYPE_SINT64 if
    negative values are likely.
    """
    TYPE_UINT64: FieldDescriptorProto.Type.ValueType
    TYPE_INT32: FieldDescriptorProto.Type.ValueType
    """Not ZigZag encoded.  Negative numbers take 10 bytes.  Use TYPE_SINT32 if
    negative values are likely.
    """
    TYPE_FIXED64: FieldDescriptorProto.Type.ValueType
    TYPE_FIXED32: FieldDescriptorProto.Type.ValueType
    TYPE_BOOL: FieldDescriptorProto.Type.ValueType
    TYPE_STRING: FieldDescriptorProto.Type.ValueType
    TYPE_GROUP: FieldDescriptorProto.Type.ValueType
    """Tag-delimited aggregate.
    Group type is deprecated and not supported after google.protobuf. However, Proto3
    implementations should still be able to parse the group wire format and
    treat group fields as unknown fields.  In Editions, the group wire format
    can be enabled via the `message_encoding` feature.
    """
    TYPE_MESSAGE: FieldDescriptorProto.Type.ValueType
    """Length-delimited aggregate."""
    TYPE_BYTES: FieldDescriptorProto.Type.ValueType
    """New in version 2."""
    TYPE_UINT32: FieldDescriptorProto.Type.ValueType
    TYPE_ENUM: FieldDescriptorProto.Type.ValueType
    TYPE_SFIXED32: FieldDescriptorProto.Type.ValueType
    TYPE_SFIXED64: FieldDescriptorProto.Type.ValueType
    TYPE_SINT32: FieldDescriptorProto.Type.ValueType
    """Uses ZigZag encoding."""
    TYPE_SINT64: FieldDescriptorProto.Type.ValueType
    """Uses ZigZag encoding."""
    class _Label:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _LabelEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldDescriptorProto._Label.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        LABEL_OPTIONAL: FieldDescriptorProto._Label.ValueType
        """0 is reserved for errors"""
        LABEL_REPEATED: FieldDescriptorProto._Label.ValueType
        LABEL_REQUIRED: FieldDescriptorProto._Label.ValueType
        """The required label is only allowed in google.protobuf.  In proto3 and Editions
        it's explicitly prohibited.  In Editions, the `field_presence` feature
        can be used to get this behavior.
        """

    class Label(_Label, metaclass=_LabelEnumTypeWrapper): ...
    LABEL_OPTIONAL: FieldDescriptorProto.Label.ValueType
    """0 is reserved for errors"""
    LABEL_REPEATED: FieldDescriptorProto.Label.ValueType
    LABEL_REQUIRED: FieldDescriptorProto.Label.ValueType
    """The required label is only allowed in google.protobuf.  In proto3 and Editions
    it's explicitly prohibited.  In Editions, the `field_presence` feature
    can be used to get this behavior.
    """
    NAME_FIELD_NUMBER: builtins.int
    NUMBER_FIELD_NUMBER: builtins.int
    LABEL_FIELD_NUMBER: builtins.int
    TYPE_FIELD_NUMBER: builtins.int
    TYPE_NAME_FIELD_NUMBER: builtins.int
    EXTENDEE_FIELD_NUMBER: builtins.int
    DEFAULT_VALUE_FIELD_NUMBER: builtins.int
    ONEOF_INDEX_FIELD_NUMBER: builtins.int
    JSON_NAME_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    PROTO3_OPTIONAL_FIELD_NUMBER: builtins.int
    name: builtins.str
    number: builtins.int
    label: global___FieldDescriptorProto.Label.ValueType
    type: global___FieldDescriptorProto.Type.ValueType
    """If type_name is set, this need not be set.  If both this and type_name
    are set, this must be one of TYPE_ENUM, TYPE_MESSAGE or TYPE_GROUP.
    """
    type_name: builtins.str
    """For message and enum types, this is the name of the type.  If the name
    starts with a '.', it is fully-qualified.  Otherwise, C++-like scoping
    rules are used to find the type (i.e. first the nested types within this
    message are searched, then within the parent, on up to the root
    namespace).
    """
    extendee: builtins.str
    """For extensions, this is the name of the type being extended.  It is
    resolved in the same manner as type_name.
    """
    default_value: builtins.str
    """For numeric types, contains the original text representation of the value.
    For booleans, "true" or "false".
    For strings, contains the default text contents (not escaped in any way).
    For bytes, contains the C escaped value.  All bytes >= 128 are escaped.
    """
    oneof_index: builtins.int
    """If set, gives the index of a oneof in the containing type's oneof_decl
    list.  This field is a member of that oneof.
    """
    json_name: builtins.str
    """JSON name of this field. The value is set by protocol compiler. If the
    user has set a "json_name" option on this field, that option's value
    will be used. Otherwise, it's deduced from the field's name by converting
    it to camelCase.
    """
    proto3_optional: builtins.bool
    """If true, this is a proto3 "optional". When a proto3 field is optional, it
    tracks presence regardless of field type.

    When proto3_optional is true, this field must belong to a oneof to signal
    to old proto3 clients that presence is tracked for this field. This oneof
    is known as a "synthetic" oneof, and this field must be its sole member
    (each proto3 optional field gets its own synthetic oneof). Synthetic oneofs
    exist in the descriptor only, and do not generate any API. Synthetic oneofs
    must be ordered after all "real" oneofs.

    For message fields, proto3_optional doesn't create any semantic change,
    since non-repeated message fields always track presence. However it still
    indicates the semantic detail of whether the user wrote "optional" or not.
    This can be useful for round-tripping the .proto file. For consistency we
    give message fields a synthetic oneof also, even though it is not required
    to track presence. This is especially important because the parser can't
    tell if a field is a message or an enum, so it must always create a
    synthetic oneof.

    Proto2 optional fields do not set this flag, because they already indicate
    optional with `LABEL_OPTIONAL`.
    """
    @property
    def options(self) -> global___FieldOptions: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        number: builtins.int | None = ...,
        label: global___FieldDescriptorProto.Label.ValueType | None = ...,
        type: global___FieldDescriptorProto.Type.ValueType | None = ...,
        type_name: builtins.str | None = ...,
        extendee: builtins.str | None = ...,
        default_value: builtins.str | None = ...,
        oneof_index: builtins.int | None = ...,
        json_name: builtins.str | None = ...,
        options: global___FieldOptions | None = ...,
        proto3_optional: builtins.bool | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "default_value",
            b"default_value",
            "extendee",
            b"extendee",
            "json_name",
            b"json_name",
            "label",
            b"label",
            "name",
            b"name",
            "number",
            b"number",
            "oneof_index",
            b"oneof_index",
            "options",
            b"options",
            "proto3_optional",
            b"proto3_optional",
            "type",
            b"type",
            "type_name",
            b"type_name",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "default_value",
            b"default_value",
            "extendee",
            b"extendee",
            "json_name",
            b"json_name",
            "label",
            b"label",
            "name",
            b"name",
            "number",
            b"number",
            "oneof_index",
            b"oneof_index",
            "options",
            b"options",
            "proto3_optional",
            b"proto3_optional",
            "type",
            b"type",
            "type_name",
            b"type_name",
        ],
    ) -> None: ...

global___FieldDescriptorProto = FieldDescriptorProto

@typing.final
class OneofDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    name: builtins.str
    @property
    def options(self) -> global___OneofOptions: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        options: global___OneofOptions | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["name", b"name", "options", b"options"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal["name", b"name", "options", b"options"],
    ) -> None: ...

global___OneofDescriptorProto = OneofDescriptorProto

@typing.final
class EnumDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class EnumReservedRange(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        START_FIELD_NUMBER: builtins.int
        END_FIELD_NUMBER: builtins.int
        start: builtins.int
        """Inclusive."""
        end: builtins.int
        """Inclusive."""
        def __init__(
            self,
            *,
            start: builtins.int | None = ...,
            end: builtins.int | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["end", b"end", "start", b"start"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["end", b"end", "start", b"start"],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    VALUE_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    RESERVED_RANGE_FIELD_NUMBER: builtins.int
    RESERVED_NAME_FIELD_NUMBER: builtins.int
    VISIBILITY_FIELD_NUMBER: builtins.int
    name: builtins.str
    visibility: global___SymbolVisibility.ValueType
    """Support for `export` and `local` keywords on enums."""
    @property
    def value(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___EnumValueDescriptorProto
    ]: ...
    @property
    def options(self) -> global___EnumOptions: ...
    @property
    def reserved_range(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___EnumDescriptorProto.EnumReservedRange
    ]: ...
    @property
    def reserved_name(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        builtins.str
    ]: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        value: collections.abc.Iterable[global___EnumValueDescriptorProto]
        | None = ...,
        options: global___EnumOptions | None = ...,
        reserved_range: collections.abc.Iterable[
            global___EnumDescriptorProto.EnumReservedRange
        ]
        | None = ...,
        reserved_name: collections.abc.Iterable[builtins.str] | None = ...,
        visibility: global___SymbolVisibility.ValueType | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "options",
            b"options",
            "visibility",
            b"visibility",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "options",
            b"options",
            "reserved_name",
            b"reserved_name",
            "reserved_range",
            b"reserved_range",
            "value",
            b"value",
            "visibility",
            b"visibility",
        ],
    ) -> None: ...

global___EnumDescriptorProto = EnumDescriptorProto

@typing.final
class EnumValueDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    NUMBER_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    name: builtins.str
    number: builtins.int
    @property
    def options(self) -> global___EnumValueOptions: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        number: builtins.int | None = ...,
        options: global___EnumValueOptions | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "number",
            b"number",
            "options",
            b"options",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "name",
            b"name",
            "number",
            b"number",
            "options",
            b"options",
        ],
    ) -> None: ...

global___EnumValueDescriptorProto = EnumValueDescriptorProto

@typing.final
class ServiceDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    METHOD_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    name: builtins.str
    @property
    def method(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___MethodDescriptorProto
    ]: ...
    @property
    def options(self) -> global___ServiceOptions: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        method: collections.abc.Iterable[global___MethodDescriptorProto]
        | None = ...,
        options: global___ServiceOptions | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["name", b"name", "options", b"options"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "method",
            b"method",
            "name",
            b"name",
            "options",
            b"options",
        ],
    ) -> None: ...

global___ServiceDescriptorProto = ServiceDescriptorProto

@typing.final
class MethodDescriptorProto(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NAME_FIELD_NUMBER: builtins.int
    INPUT_TYPE_FIELD_NUMBER: builtins.int
    OUTPUT_TYPE_FIELD_NUMBER: builtins.int
    OPTIONS_FIELD_NUMBER: builtins.int
    CLIENT_STREAMING_FIELD_NUMBER: builtins.int
    SERVER_STREAMING_FIELD_NUMBER: builtins.int
    name: builtins.str
    input_type: builtins.str
    """Input and output type names.  These are resolved in the same way as
    FieldDescriptorProto.type_name, but must refer to a message type.
    """
    output_type: builtins.str
    client_streaming: builtins.bool
    """Identifies if client streams multiple client messages"""
    server_streaming: builtins.bool
    """Identifies if server streams multiple server messages"""
    @property
    def options(self) -> global___MethodOptions: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        input_type: builtins.str | None = ...,
        output_type: builtins.str | None = ...,
        options: global___MethodOptions | None = ...,
        client_streaming: builtins.bool | None = ...,
        server_streaming: builtins.bool | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "client_streaming",
            b"client_streaming",
            "input_type",
            b"input_type",
            "name",
            b"name",
            "options",
            b"options",
            "output_type",
            b"output_type",
            "server_streaming",
            b"server_streaming",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "client_streaming",
            b"client_streaming",
            "input_type",
            b"input_type",
            "name",
            b"name",
            "options",
            b"options",
            "output_type",
            b"output_type",
            "server_streaming",
            b"server_streaming",
        ],
    ) -> None: ...

global___MethodDescriptorProto = MethodDescriptorProto

@typing.final
class FileOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _OptimizeMode:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _OptimizeModeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FileOptions._OptimizeMode.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        SPEED: FileOptions._OptimizeMode.ValueType
        """Generate complete code for parsing, serialization,"""
        CODE_SIZE: FileOptions._OptimizeMode.ValueType
        """etc.
        Use ReflectionOps to implement these methods.
        """
        LITE_RUNTIME: FileOptions._OptimizeMode.ValueType
        """Generate code using MessageLite and the lite runtime."""

    class OptimizeMode(
        _OptimizeMode,
        metaclass=_OptimizeModeEnumTypeWrapper,
    ): ...
    SPEED: FileOptions.OptimizeMode.ValueType
    """Generate complete code for parsing, serialization,"""
    CODE_SIZE: FileOptions.OptimizeMode.ValueType
    """etc.
    Use ReflectionOps to implement these methods.
    """
    LITE_RUNTIME: FileOptions.OptimizeMode.ValueType
    """Generate code using MessageLite and the lite runtime."""
    JAVA_PACKAGE_FIELD_NUMBER: builtins.int
    JAVA_OUTER_CLASSNAME_FIELD_NUMBER: builtins.int
    JAVA_MULTIPLE_FILES_FIELD_NUMBER: builtins.int
    JAVA_GENERATE_EQUALS_AND_HASH_FIELD_NUMBER: builtins.int
    JAVA_STRING_CHECK_UTF8_FIELD_NUMBER: builtins.int
    OPTIMIZE_FOR_FIELD_NUMBER: builtins.int
    GO_PACKAGE_FIELD_NUMBER: builtins.int
    CC_GENERIC_SERVICES_FIELD_NUMBER: builtins.int
    JAVA_GENERIC_SERVICES_FIELD_NUMBER: builtins.int
    PY_GENERIC_SERVICES_FIELD_NUMBER: builtins.int
    DEPRECATED_FIELD_NUMBER: builtins.int
    CC_ENABLE_ARENAS_FIELD_NUMBER: builtins.int
    OBJC_CLASS_PREFIX_FIELD_NUMBER: builtins.int
    CSHARP_NAMESPACE_FIELD_NUMBER: builtins.int
    SWIFT_PREFIX_FIELD_NUMBER: builtins.int
    PHP_CLASS_PREFIX_FIELD_NUMBER: builtins.int
    PHP_NAMESPACE_FIELD_NUMBER: builtins.int
    PHP_METADATA_NAMESPACE_FIELD_NUMBER: builtins.int
    RUBY_PACKAGE_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    java_package: builtins.str
    """Sets the Java package where classes generated from this .proto will be
    placed.  By default, the proto package is used, but this is often
    inappropriate because proto packages do not normally start with backwards
    domain names.
    """
    java_outer_classname: builtins.str
    """Controls the name of the wrapper Java class generated for the .proto file.
    That class will always contain the .proto file's getDescriptor() method as
    well as any top-level extensions defined in the .proto file.
    If java_multiple_files is disabled, then all the other classes from the
    .proto file will be nested inside the single wrapper outer class.
    """
    java_multiple_files: builtins.bool
    """If enabled, then the Java code generator will generate a separate .java
    file for each top-level message, enum, and service defined in the .proto
    file.  Thus, these types will *not* be nested inside the wrapper class
    named by java_outer_classname.  However, the wrapper class will still be
    generated to contain the file's getDescriptor() method as well as any
    top-level extensions defined in the file.
    """
    java_generate_equals_and_hash: builtins.bool
    """This option does nothing."""
    java_string_check_utf8: builtins.bool
    """A proto2 file can set this to true to opt in to UTF-8 checking for Java,
    which will throw an exception if invalid UTF-8 is parsed from the wire or
    assigned to a string field.

    TODO: clarify exactly what kinds of field types this option
    applies to, and update these docs accordingly.

    Proto3 files already perform these checks. Setting the option explicitly to
    false has no effect: it cannot be used to opt proto3 files out of UTF-8
    checks.
    """
    optimize_for: global___FileOptions.OptimizeMode.ValueType
    go_package: builtins.str
    """Sets the Go package where structs generated from this .proto will be
    placed. If omitted, the Go package will be derived from the following:
      - The basename of the package import path, if provided.
      - Otherwise, the package statement in the .proto file, if present.
      - Otherwise, the basename of the .proto file, without extension.
    """
    cc_generic_services: builtins.bool
    """Should generic services be generated in each language?  "Generic" services
    are not specific to any particular RPC system.  They are generated by the
    main code generators in each language (without additional plugins).
    Generic services were the only kind of service generation supported by
    early versions of google.protobuf.

    Generic services are now considered deprecated in favor of using plugins
    that generate code specific to your particular RPC system.  Therefore,
    these default to false.  Old code which depends on generic services should
    explicitly set them to true.
    """
    java_generic_services: builtins.bool
    py_generic_services: builtins.bool
    deprecated: builtins.bool
    """Is this file deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for everything in the file, or it will be completely ignored; in the very
    least, this is a formalization for deprecating files.
    """
    cc_enable_arenas: builtins.bool
    """Enables the use of arenas for the proto messages in this file. This applies
    only to generated classes for C++.
    """
    objc_class_prefix: builtins.str
    """Sets the objective c class prefix which is prepended to all objective c
    generated classes from this .proto. There is no default.
    """
    csharp_namespace: builtins.str
    """Namespace for generated classes; defaults to the package."""
    swift_prefix: builtins.str
    """By default Swift generators will take the proto package and CamelCase it
    replacing '.' with underscore and use that to prefix the types/symbols
    defined. When this options is provided, they will use this value instead
    to prefix the types/symbols defined.
    """
    php_class_prefix: builtins.str
    """Sets the php class prefix which is prepended to all php generated classes
    from this .proto. Default is empty.
    """
    php_namespace: builtins.str
    """Use this option to change the namespace of php generated classes. Default
    is empty. When this option is empty, the package name will be used for
    determining the namespace.
    """
    php_metadata_namespace: builtins.str
    """Use this option to change the namespace of php generated metadata classes.
    Default is empty. When this option is empty, the proto file name will be
    used for determining the namespace.
    """
    ruby_package: builtins.str
    """Use this option to change the package of ruby generated classes. Default
    is empty. When this option is not set, the package name will be used for
    determining the ruby package.
    """
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        java_package: builtins.str | None = ...,
        java_outer_classname: builtins.str | None = ...,
        java_multiple_files: builtins.bool | None = ...,
        java_generate_equals_and_hash: builtins.bool | None = ...,
        java_string_check_utf8: builtins.bool | None = ...,
        optimize_for: global___FileOptions.OptimizeMode.ValueType | None = ...,
        go_package: builtins.str | None = ...,
        cc_generic_services: builtins.bool | None = ...,
        java_generic_services: builtins.bool | None = ...,
        py_generic_services: builtins.bool | None = ...,
        deprecated: builtins.bool | None = ...,
        cc_enable_arenas: builtins.bool | None = ...,
        objc_class_prefix: builtins.str | None = ...,
        csharp_namespace: builtins.str | None = ...,
        swift_prefix: builtins.str | None = ...,
        php_class_prefix: builtins.str | None = ...,
        php_namespace: builtins.str | None = ...,
        php_metadata_namespace: builtins.str | None = ...,
        ruby_package: builtins.str | None = ...,
        features: global___FeatureSet | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "cc_enable_arenas",
            b"cc_enable_arenas",
            "cc_generic_services",
            b"cc_generic_services",
            "csharp_namespace",
            b"csharp_namespace",
            "deprecated",
            b"deprecated",
            "features",
            b"features",
            "go_package",
            b"go_package",
            "java_generate_equals_and_hash",
            b"java_generate_equals_and_hash",
            "java_generic_services",
            b"java_generic_services",
            "java_multiple_files",
            b"java_multiple_files",
            "java_outer_classname",
            b"java_outer_classname",
            "java_package",
            b"java_package",
            "java_string_check_utf8",
            b"java_string_check_utf8",
            "objc_class_prefix",
            b"objc_class_prefix",
            "optimize_for",
            b"optimize_for",
            "php_class_prefix",
            b"php_class_prefix",
            "php_metadata_namespace",
            b"php_metadata_namespace",
            "php_namespace",
            b"php_namespace",
            "py_generic_services",
            b"py_generic_services",
            "ruby_package",
            b"ruby_package",
            "swift_prefix",
            b"swift_prefix",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "cc_enable_arenas",
            b"cc_enable_arenas",
            "cc_generic_services",
            b"cc_generic_services",
            "csharp_namespace",
            b"csharp_namespace",
            "deprecated",
            b"deprecated",
            "features",
            b"features",
            "go_package",
            b"go_package",
            "java_generate_equals_and_hash",
            b"java_generate_equals_and_hash",
            "java_generic_services",
            b"java_generic_services",
            "java_multiple_files",
            b"java_multiple_files",
            "java_outer_classname",
            b"java_outer_classname",
            "java_package",
            b"java_package",
            "java_string_check_utf8",
            b"java_string_check_utf8",
            "objc_class_prefix",
            b"objc_class_prefix",
            "optimize_for",
            b"optimize_for",
            "php_class_prefix",
            b"php_class_prefix",
            "php_metadata_namespace",
            b"php_metadata_namespace",
            "php_namespace",
            b"php_namespace",
            "py_generic_services",
            b"py_generic_services",
            "ruby_package",
            b"ruby_package",
            "swift_prefix",
            b"swift_prefix",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___FileOptions = FileOptions

@typing.final
class MessageOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    MESSAGE_SET_WIRE_FORMAT_FIELD_NUMBER: builtins.int
    NO_STANDARD_DESCRIPTOR_ACCESSOR_FIELD_NUMBER: builtins.int
    DEPRECATED_FIELD_NUMBER: builtins.int
    MAP_ENTRY_FIELD_NUMBER: builtins.int
    DEPRECATED_LEGACY_JSON_FIELD_CONFLICTS_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    message_set_wire_format: builtins.bool
    """Set true to use the old proto1 MessageSet wire format for extensions.
    This is provided for backwards-compatibility with the MessageSet wire
    format.  You should not use this for any other reason:  It's less
    efficient, has fewer features, and is more complicated.

    The message must be defined exactly as follows:
      message Foo {
        option message_set_wire_format = true;
        extensions 4 to max;
      }
    Note that the message cannot have any defined fields; MessageSets only
    have extensions.

    All extensions of your type must be singular messages; e.g. they cannot
    be int32s, enums, or repeated messages.

    Because this is an option, the above two restrictions are not enforced by
    the protocol compiler.
    """
    no_standard_descriptor_accessor: builtins.bool
    """Disables the generation of the standard "descriptor()" accessor, which can
    conflict with a field of the same name.  This is meant to make migration
    from proto1 easier; new code should avoid fields named "descriptor".
    """
    deprecated: builtins.bool
    """Is this message deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for the message, or it will be completely ignored; in the very least,
    this is a formalization for deprecating messages.
    """
    map_entry: builtins.bool
    """Whether the message is an automatically generated map entry type for the
    maps field.

    For maps fields:
        map<KeyType, ValueType> map_field = 1;
    The parsed descriptor looks like:
        message MapFieldEntry {
            option map_entry = true;
            optional KeyType key = 1;
            optional ValueType value = 2;
        }
        repeated MapFieldEntry map_field = 1;

    Implementations may choose not to generate the map_entry=true message, but
    use a native map in the target language to hold the keys and values.
    The reflection APIs in such implementations still need to work as
    if the field is a repeated message field.

    NOTE: Do not set the option in .proto files. Always use the maps syntax
    instead. The option should only be implicitly set by the proto compiler
    parser.
    """
    deprecated_legacy_json_field_conflicts: builtins.bool
    """Enable the legacy handling of JSON field name conflicts.  This lowercases
    and strips underscored from the fields before comparison in proto3 only.
    The new behavior takes `json_name` into account and applies to proto2 as
    well.

    This should only be used as a temporary measure against broken builds due
    to the change in behavior for JSON field name conflicts.

    TODO This is legacy behavior we plan to remove once downstream
    teams have had time to migrate.
    """
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        message_set_wire_format: builtins.bool | None = ...,
        no_standard_descriptor_accessor: builtins.bool | None = ...,
        deprecated: builtins.bool | None = ...,
        map_entry: builtins.bool | None = ...,
        deprecated_legacy_json_field_conflicts: builtins.bool | None = ...,
        features: global___FeatureSet | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "deprecated_legacy_json_field_conflicts",
            b"deprecated_legacy_json_field_conflicts",
            "features",
            b"features",
            "map_entry",
            b"map_entry",
            "message_set_wire_format",
            b"message_set_wire_format",
            "no_standard_descriptor_accessor",
            b"no_standard_descriptor_accessor",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "deprecated_legacy_json_field_conflicts",
            b"deprecated_legacy_json_field_conflicts",
            "features",
            b"features",
            "map_entry",
            b"map_entry",
            "message_set_wire_format",
            b"message_set_wire_format",
            "no_standard_descriptor_accessor",
            b"no_standard_descriptor_accessor",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___MessageOptions = MessageOptions

@typing.final
class FieldOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _CType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _CTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldOptions._CType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        STRING: FieldOptions._CType.ValueType
        """Default mode."""
        CORD: FieldOptions._CType.ValueType
        """The option [ctype=CORD] may be applied to a non-repeated field of type
        "bytes". It indicates that in C++, the data should be stored in a Cord
        instead of a string.  For very large strings, this may reduce memory
        fragmentation. It may also allow better performance when parsing from a
        Cord, or when parsing with aliasing enabled, as the parsed Cord may then
        alias the original buffer.
        """
        STRING_PIECE: FieldOptions._CType.ValueType

    class CType(_CType, metaclass=_CTypeEnumTypeWrapper): ...
    STRING: FieldOptions.CType.ValueType
    """Default mode."""
    CORD: FieldOptions.CType.ValueType
    """The option [ctype=CORD] may be applied to a non-repeated field of type
    "bytes". It indicates that in C++, the data should be stored in a Cord
    instead of a string.  For very large strings, this may reduce memory
    fragmentation. It may also allow better performance when parsing from a
    Cord, or when parsing with aliasing enabled, as the parsed Cord may then
    alias the original buffer.
    """
    STRING_PIECE: FieldOptions.CType.ValueType
    class _JSType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _JSTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldOptions._JSType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        JS_NORMAL: FieldOptions._JSType.ValueType
        """Use the default type."""
        JS_STRING: FieldOptions._JSType.ValueType
        """Use JavaScript strings."""
        JS_NUMBER: FieldOptions._JSType.ValueType
        """Use JavaScript numbers."""

    class JSType(_JSType, metaclass=_JSTypeEnumTypeWrapper): ...
    JS_NORMAL: FieldOptions.JSType.ValueType
    """Use the default type."""
    JS_STRING: FieldOptions.JSType.ValueType
    """Use JavaScript strings."""
    JS_NUMBER: FieldOptions.JSType.ValueType
    """Use JavaScript numbers."""
    class _OptionRetention:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _OptionRetentionEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldOptions._OptionRetention.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        RETENTION_UNKNOWN: FieldOptions._OptionRetention.ValueType
        RETENTION_RUNTIME: FieldOptions._OptionRetention.ValueType
        RETENTION_SOURCE: FieldOptions._OptionRetention.ValueType

    class OptionRetention(
        _OptionRetention,
        metaclass=_OptionRetentionEnumTypeWrapper,
    ): ...
    RETENTION_UNKNOWN: FieldOptions.OptionRetention.ValueType
    RETENTION_RUNTIME: FieldOptions.OptionRetention.ValueType
    RETENTION_SOURCE: FieldOptions.OptionRetention.ValueType
    class _OptionTargetType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _OptionTargetTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FieldOptions._OptionTargetType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        TARGET_TYPE_UNKNOWN: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_FILE: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_EXTENSION_RANGE: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_MESSAGE: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_FIELD: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_ONEOF: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_ENUM: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_ENUM_ENTRY: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_SERVICE: FieldOptions._OptionTargetType.ValueType
        TARGET_TYPE_METHOD: FieldOptions._OptionTargetType.ValueType

    class OptionTargetType(
        _OptionTargetType,
        metaclass=_OptionTargetTypeEnumTypeWrapper,
    ): ...
    TARGET_TYPE_UNKNOWN: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_FILE: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_EXTENSION_RANGE: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_MESSAGE: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_FIELD: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_ONEOF: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_ENUM: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_ENUM_ENTRY: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_SERVICE: FieldOptions.OptionTargetType.ValueType
    TARGET_TYPE_METHOD: FieldOptions.OptionTargetType.ValueType
    @typing.final
    class EditionDefault(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        EDITION_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        edition: global___Edition.ValueType
        value: builtins.str
        """Textproto value."""
        def __init__(
            self,
            *,
            edition: global___Edition.ValueType | None = ...,
            value: builtins.str | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "edition",
                b"edition",
                "value",
                b"value",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "edition",
                b"edition",
                "value",
                b"value",
            ],
        ) -> None: ...

    @typing.final
    class FeatureSupport(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        EDITION_INTRODUCED_FIELD_NUMBER: builtins.int
        EDITION_DEPRECATED_FIELD_NUMBER: builtins.int
        DEPRECATION_WARNING_FIELD_NUMBER: builtins.int
        EDITION_REMOVED_FIELD_NUMBER: builtins.int
        edition_introduced: global___Edition.ValueType
        """The edition that this feature was first available in.  In editions
        earlier than this one, the default assigned to EDITION_LEGACY will be
        used, and proto files will not be able to override it.
        """
        edition_deprecated: global___Edition.ValueType
        """The edition this feature becomes deprecated in.  Using this after this
        edition may trigger warnings.
        """
        deprecation_warning: builtins.str
        """The deprecation warning text if this feature is used after the edition it
        was marked deprecated in.
        """
        edition_removed: global___Edition.ValueType
        """The edition this feature is no longer available in.  In editions after
        this one, the last default assigned will be used, and proto files will
        not be able to override it.
        """
        def __init__(
            self,
            *,
            edition_introduced: global___Edition.ValueType | None = ...,
            edition_deprecated: global___Edition.ValueType | None = ...,
            deprecation_warning: builtins.str | None = ...,
            edition_removed: global___Edition.ValueType | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "deprecation_warning",
                b"deprecation_warning",
                "edition_deprecated",
                b"edition_deprecated",
                "edition_introduced",
                b"edition_introduced",
                "edition_removed",
                b"edition_removed",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "deprecation_warning",
                b"deprecation_warning",
                "edition_deprecated",
                b"edition_deprecated",
                "edition_introduced",
                b"edition_introduced",
                "edition_removed",
                b"edition_removed",
            ],
        ) -> None: ...

    CTYPE_FIELD_NUMBER: builtins.int
    PACKED_FIELD_NUMBER: builtins.int
    JSTYPE_FIELD_NUMBER: builtins.int
    LAZY_FIELD_NUMBER: builtins.int
    UNVERIFIED_LAZY_FIELD_NUMBER: builtins.int
    DEPRECATED_FIELD_NUMBER: builtins.int
    WEAK_FIELD_NUMBER: builtins.int
    DEBUG_REDACT_FIELD_NUMBER: builtins.int
    RETENTION_FIELD_NUMBER: builtins.int
    TARGETS_FIELD_NUMBER: builtins.int
    EDITION_DEFAULTS_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    FEATURE_SUPPORT_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    ctype: global___FieldOptions.CType.ValueType
    """NOTE: ctype is deprecated. Use `features.(pb.cpp).string_type` instead.
    The ctype option instructs the C++ code generator to use a different
    representation of the field than it normally would.  See the specific
    options below.  This option is only implemented to support use of
    [ctype=CORD] and [ctype=STRING] (the default) on non-repeated fields of
    type "bytes" in the open source release.
    TODO: make ctype actually deprecated.
    """
    packed: builtins.bool
    """The packed option can be enabled for repeated primitive fields to enable
    a more efficient representation on the wire. Rather than repeatedly
    writing the tag and type for each element, the entire array is encoded as
    a single length-delimited blob. In proto3, only explicit setting it to
    false will avoid using packed encoding.  This option is prohibited in
    Editions, but the `repeated_field_encoding` feature can be used to control
    the behavior.
    """
    jstype: global___FieldOptions.JSType.ValueType
    """The jstype option determines the JavaScript type used for values of the
    field.  The option is permitted only for 64 bit integral and fixed types
    (int64, uint64, sint64, fixed64, sfixed64).  A field with jstype JS_STRING
    is represented as JavaScript string, which avoids loss of precision that
    can happen when a large value is converted to a floating point JavaScript.
    Specifying JS_NUMBER for the jstype causes the generated JavaScript code to
    use the JavaScript "number" type.  The behavior of the default option
    JS_NORMAL is implementation dependent.

    This option is an enum to permit additional types to be added, e.g.
    goog.math.Integer.
    """
    lazy: builtins.bool
    """Should this field be parsed lazily?  Lazy applies only to message-type
    fields.  It means that when the outer message is initially parsed, the
    inner message's contents will not be parsed but instead stored in encoded
    form.  The inner message will actually be parsed when it is first accessed.

    This is only a hint.  Implementations are free to choose whether to use
    eager or lazy parsing regardless of the value of this option.  However,
    setting this option true suggests that the protocol author believes that
    using lazy parsing on this field is worth the additional bookkeeping
    overhead typically needed to implement it.

    This option does not affect the public interface of any generated code;
    all method signatures remain the same.  Furthermore, thread-safety of the
    interface is not affected by this option; const methods remain safe to
    call from multiple threads concurrently, while non-const methods continue
    to require exclusive access.

    Note that lazy message fields are still eagerly verified to check
    ill-formed wireformat or missing required fields. Calling IsInitialized()
    on the outer message would fail if the inner message has missing required
    fields. Failed verification would result in parsing failure (except when
    uninitialized messages are acceptable).
    """
    unverified_lazy: builtins.bool
    """unverified_lazy does no correctness checks on the byte stream. This should
    only be used where lazy with verification is prohibitive for performance
    reasons.
    """
    deprecated: builtins.bool
    """Is this field deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for accessors, or it will be completely ignored; in the very least, this
    is a formalization for deprecating fields.
    """
    weak: builtins.bool
    """DEPRECATED. DO NOT USE!
    For Google-internal migration only. Do not use.
    """
    debug_redact: builtins.bool
    """Indicate that the field value should not be printed out when using debug
    formats, e.g. when the field contains sensitive credentials.
    """
    retention: global___FieldOptions.OptionRetention.ValueType
    @property
    def targets(
        self,
    ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
        global___FieldOptions.OptionTargetType.ValueType
    ]: ...
    @property
    def edition_defaults(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FieldOptions.EditionDefault
    ]: ...
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def feature_support(self) -> global___FieldOptions.FeatureSupport: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        ctype: global___FieldOptions.CType.ValueType | None = ...,
        packed: builtins.bool | None = ...,
        jstype: global___FieldOptions.JSType.ValueType | None = ...,
        lazy: builtins.bool | None = ...,
        unverified_lazy: builtins.bool | None = ...,
        deprecated: builtins.bool | None = ...,
        weak: builtins.bool | None = ...,
        debug_redact: builtins.bool | None = ...,
        retention: global___FieldOptions.OptionRetention.ValueType
        | None = ...,
        targets: collections.abc.Iterable[
            global___FieldOptions.OptionTargetType.ValueType
        ]
        | None = ...,
        edition_defaults: collections.abc.Iterable[
            global___FieldOptions.EditionDefault
        ]
        | None = ...,
        features: global___FeatureSet | None = ...,
        feature_support: global___FieldOptions.FeatureSupport | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "ctype",
            b"ctype",
            "debug_redact",
            b"debug_redact",
            "deprecated",
            b"deprecated",
            "feature_support",
            b"feature_support",
            "features",
            b"features",
            "jstype",
            b"jstype",
            "lazy",
            b"lazy",
            "packed",
            b"packed",
            "retention",
            b"retention",
            "unverified_lazy",
            b"unverified_lazy",
            "weak",
            b"weak",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "ctype",
            b"ctype",
            "debug_redact",
            b"debug_redact",
            "deprecated",
            b"deprecated",
            "edition_defaults",
            b"edition_defaults",
            "feature_support",
            b"feature_support",
            "features",
            b"features",
            "jstype",
            b"jstype",
            "lazy",
            b"lazy",
            "packed",
            b"packed",
            "retention",
            b"retention",
            "targets",
            b"targets",
            "uninterpreted_option",
            b"uninterpreted_option",
            "unverified_lazy",
            b"unverified_lazy",
            "weak",
            b"weak",
        ],
    ) -> None: ...

global___FieldOptions = FieldOptions

@typing.final
class OneofOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FEATURES_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        features: global___FeatureSet | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["features", b"features"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "features",
            b"features",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___OneofOptions = OneofOptions

@typing.final
class EnumOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    ALLOW_ALIAS_FIELD_NUMBER: builtins.int
    DEPRECATED_FIELD_NUMBER: builtins.int
    DEPRECATED_LEGACY_JSON_FIELD_CONFLICTS_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    allow_alias: builtins.bool
    """Set this option to true to allow mapping different tag names to the same
    value.
    """
    deprecated: builtins.bool
    """Is this enum deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for the enum, or it will be completely ignored; in the very least, this
    is a formalization for deprecating enums.
    """
    deprecated_legacy_json_field_conflicts: builtins.bool
    """Enable the legacy handling of JSON field name conflicts.  This lowercases
    and strips underscored from the fields before comparison in proto3 only.
    The new behavior takes `json_name` into account and applies to proto2 as
    well.
    TODO Remove this legacy behavior once downstream teams have
    had time to migrate.
    """
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        allow_alias: builtins.bool | None = ...,
        deprecated: builtins.bool | None = ...,
        deprecated_legacy_json_field_conflicts: builtins.bool | None = ...,
        features: global___FeatureSet | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "allow_alias",
            b"allow_alias",
            "deprecated",
            b"deprecated",
            "deprecated_legacy_json_field_conflicts",
            b"deprecated_legacy_json_field_conflicts",
            "features",
            b"features",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "allow_alias",
            b"allow_alias",
            "deprecated",
            b"deprecated",
            "deprecated_legacy_json_field_conflicts",
            b"deprecated_legacy_json_field_conflicts",
            "features",
            b"features",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___EnumOptions = EnumOptions

@typing.final
class EnumValueOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    DEPRECATED_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    DEBUG_REDACT_FIELD_NUMBER: builtins.int
    FEATURE_SUPPORT_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    deprecated: builtins.bool
    """Is this enum value deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for the enum value, or it will be completely ignored; in the very least,
    this is a formalization for deprecating enum values.
    """
    debug_redact: builtins.bool
    """Indicate that fields annotated with this enum value should not be printed
    out when using debug formats, e.g. when the field contains sensitive
    credentials.
    """
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def feature_support(self) -> global___FieldOptions.FeatureSupport: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        deprecated: builtins.bool | None = ...,
        features: global___FeatureSet | None = ...,
        debug_redact: builtins.bool | None = ...,
        feature_support: global___FieldOptions.FeatureSupport | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "debug_redact",
            b"debug_redact",
            "deprecated",
            b"deprecated",
            "feature_support",
            b"feature_support",
            "features",
            b"features",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "debug_redact",
            b"debug_redact",
            "deprecated",
            b"deprecated",
            "feature_support",
            b"feature_support",
            "features",
            b"features",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___EnumValueOptions = EnumValueOptions

@typing.final
class ServiceOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    FEATURES_FIELD_NUMBER: builtins.int
    DEPRECATED_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    deprecated: builtins.bool
    """Note:  Field numbers 1 through 32 are reserved for Google's internal RPC
      framework.  We apologize for hoarding these numbers to ourselves, but
      we were already using them long before we decided to release Protocol
      Buffers.

    Is this service deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for the service, or it will be completely ignored; in the very least,
    this is a formalization for deprecating services.
    """
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        features: global___FeatureSet | None = ...,
        deprecated: builtins.bool | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "features",
            b"features",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "features",
            b"features",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___ServiceOptions = ServiceOptions

@typing.final
class MethodOptions(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _IdempotencyLevel:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _IdempotencyLevelEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            MethodOptions._IdempotencyLevel.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        IDEMPOTENCY_UNKNOWN: MethodOptions._IdempotencyLevel.ValueType
        NO_SIDE_EFFECTS: MethodOptions._IdempotencyLevel.ValueType
        """implies idempotent"""
        IDEMPOTENT: MethodOptions._IdempotencyLevel.ValueType
        """idempotent, but may have side effects"""

    class IdempotencyLevel(
        _IdempotencyLevel,
        metaclass=_IdempotencyLevelEnumTypeWrapper,
    ): ...
    IDEMPOTENCY_UNKNOWN: MethodOptions.IdempotencyLevel.ValueType
    NO_SIDE_EFFECTS: MethodOptions.IdempotencyLevel.ValueType
    """implies idempotent"""
    IDEMPOTENT: MethodOptions.IdempotencyLevel.ValueType
    """idempotent, but may have side effects"""
    DEPRECATED_FIELD_NUMBER: builtins.int
    IDEMPOTENCY_LEVEL_FIELD_NUMBER: builtins.int
    FEATURES_FIELD_NUMBER: builtins.int
    UNINTERPRETED_OPTION_FIELD_NUMBER: builtins.int
    deprecated: builtins.bool
    """Note:  Field numbers 1 through 32 are reserved for Google's internal RPC
      framework.  We apologize for hoarding these numbers to ourselves, but
      we were already using them long before we decided to release Protocol
      Buffers.

    Is this method deprecated?
    Depending on the target platform, this can emit Deprecated annotations
    for the method, or it will be completely ignored; in the very least,
    this is a formalization for deprecating methods.
    """
    idempotency_level: global___MethodOptions.IdempotencyLevel.ValueType
    @property
    def features(self) -> global___FeatureSet: ...
    @property
    def uninterpreted_option(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption
    ]: ...
    def __init__(
        self,
        *,
        deprecated: builtins.bool | None = ...,
        idempotency_level: global___MethodOptions.IdempotencyLevel.ValueType
        | None = ...,
        features: global___FeatureSet | None = ...,
        uninterpreted_option: collections.abc.Iterable[
            global___UninterpretedOption
        ]
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "features",
            b"features",
            "idempotency_level",
            b"idempotency_level",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "deprecated",
            b"deprecated",
            "features",
            b"features",
            "idempotency_level",
            b"idempotency_level",
            "uninterpreted_option",
            b"uninterpreted_option",
        ],
    ) -> None: ...

global___MethodOptions = MethodOptions

@typing.final
class UninterpretedOption(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class NamePart(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        NAME_PART_FIELD_NUMBER: builtins.int
        IS_EXTENSION_FIELD_NUMBER: builtins.int
        name_part: builtins.str
        is_extension: builtins.bool
        def __init__(
            self,
            *,
            name_part: builtins.str | None = ...,
            is_extension: builtins.bool | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "is_extension",
                b"is_extension",
                "name_part",
                b"name_part",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "is_extension",
                b"is_extension",
                "name_part",
                b"name_part",
            ],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    IDENTIFIER_VALUE_FIELD_NUMBER: builtins.int
    POSITIVE_INT_VALUE_FIELD_NUMBER: builtins.int
    NEGATIVE_INT_VALUE_FIELD_NUMBER: builtins.int
    DOUBLE_VALUE_FIELD_NUMBER: builtins.int
    STRING_VALUE_FIELD_NUMBER: builtins.int
    AGGREGATE_VALUE_FIELD_NUMBER: builtins.int
    identifier_value: builtins.str
    """The value of the uninterpreted option, in whatever type the tokenizer
    identified it as during parsing. Exactly one of these should be set.
    """
    positive_int_value: builtins.int
    negative_int_value: builtins.int
    double_value: builtins.float
    string_value: builtins.bytes
    aggregate_value: builtins.str
    @property
    def name(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___UninterpretedOption.NamePart
    ]: ...
    def __init__(
        self,
        *,
        name: collections.abc.Iterable[global___UninterpretedOption.NamePart]
        | None = ...,
        identifier_value: builtins.str | None = ...,
        positive_int_value: builtins.int | None = ...,
        negative_int_value: builtins.int | None = ...,
        double_value: builtins.float | None = ...,
        string_value: builtins.bytes | None = ...,
        aggregate_value: builtins.str | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "aggregate_value",
            b"aggregate_value",
            "double_value",
            b"double_value",
            "identifier_value",
            b"identifier_value",
            "negative_int_value",
            b"negative_int_value",
            "positive_int_value",
            b"positive_int_value",
            "string_value",
            b"string_value",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "aggregate_value",
            b"aggregate_value",
            "double_value",
            b"double_value",
            "identifier_value",
            b"identifier_value",
            "name",
            b"name",
            "negative_int_value",
            b"negative_int_value",
            "positive_int_value",
            b"positive_int_value",
            "string_value",
            b"string_value",
        ],
    ) -> None: ...

global___UninterpretedOption = UninterpretedOption

@typing.final
class FeatureSet(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    class _FieldPresence:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _FieldPresenceEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._FieldPresence.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        FIELD_PRESENCE_UNKNOWN: FeatureSet._FieldPresence.ValueType
        EXPLICIT: FeatureSet._FieldPresence.ValueType
        IMPLICIT: FeatureSet._FieldPresence.ValueType
        LEGACY_REQUIRED: FeatureSet._FieldPresence.ValueType

    class FieldPresence(
        _FieldPresence,
        metaclass=_FieldPresenceEnumTypeWrapper,
    ): ...
    FIELD_PRESENCE_UNKNOWN: FeatureSet.FieldPresence.ValueType
    EXPLICIT: FeatureSet.FieldPresence.ValueType
    IMPLICIT: FeatureSet.FieldPresence.ValueType
    LEGACY_REQUIRED: FeatureSet.FieldPresence.ValueType
    class _EnumType:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _EnumTypeEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._EnumType.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        ENUM_TYPE_UNKNOWN: FeatureSet._EnumType.ValueType
        OPEN: FeatureSet._EnumType.ValueType
        CLOSED: FeatureSet._EnumType.ValueType

    class EnumType(_EnumType, metaclass=_EnumTypeEnumTypeWrapper): ...
    ENUM_TYPE_UNKNOWN: FeatureSet.EnumType.ValueType
    OPEN: FeatureSet.EnumType.ValueType
    CLOSED: FeatureSet.EnumType.ValueType
    class _RepeatedFieldEncoding:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _RepeatedFieldEncodingEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._RepeatedFieldEncoding.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        REPEATED_FIELD_ENCODING_UNKNOWN: (
            FeatureSet._RepeatedFieldEncoding.ValueType
        )
        PACKED: FeatureSet._RepeatedFieldEncoding.ValueType
        EXPANDED: FeatureSet._RepeatedFieldEncoding.ValueType

    class RepeatedFieldEncoding(
        _RepeatedFieldEncoding,
        metaclass=_RepeatedFieldEncodingEnumTypeWrapper,
    ): ...
    REPEATED_FIELD_ENCODING_UNKNOWN: FeatureSet.RepeatedFieldEncoding.ValueType
    PACKED: FeatureSet.RepeatedFieldEncoding.ValueType
    EXPANDED: FeatureSet.RepeatedFieldEncoding.ValueType
    class _Utf8Validation:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _Utf8ValidationEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._Utf8Validation.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        UTF8_VALIDATION_UNKNOWN: FeatureSet._Utf8Validation.ValueType
        VERIFY: FeatureSet._Utf8Validation.ValueType
        NONE: FeatureSet._Utf8Validation.ValueType

    class Utf8Validation(
        _Utf8Validation,
        metaclass=_Utf8ValidationEnumTypeWrapper,
    ): ...
    UTF8_VALIDATION_UNKNOWN: FeatureSet.Utf8Validation.ValueType
    VERIFY: FeatureSet.Utf8Validation.ValueType
    NONE: FeatureSet.Utf8Validation.ValueType
    class _MessageEncoding:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _MessageEncodingEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._MessageEncoding.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        MESSAGE_ENCODING_UNKNOWN: FeatureSet._MessageEncoding.ValueType
        LENGTH_PREFIXED: FeatureSet._MessageEncoding.ValueType
        DELIMITED: FeatureSet._MessageEncoding.ValueType

    class MessageEncoding(
        _MessageEncoding,
        metaclass=_MessageEncodingEnumTypeWrapper,
    ): ...
    MESSAGE_ENCODING_UNKNOWN: FeatureSet.MessageEncoding.ValueType
    LENGTH_PREFIXED: FeatureSet.MessageEncoding.ValueType
    DELIMITED: FeatureSet.MessageEncoding.ValueType
    class _JsonFormat:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _JsonFormatEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._JsonFormat.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        JSON_FORMAT_UNKNOWN: FeatureSet._JsonFormat.ValueType
        ALLOW: FeatureSet._JsonFormat.ValueType
        LEGACY_BEST_EFFORT: FeatureSet._JsonFormat.ValueType

    class JsonFormat(_JsonFormat, metaclass=_JsonFormatEnumTypeWrapper): ...
    JSON_FORMAT_UNKNOWN: FeatureSet.JsonFormat.ValueType
    ALLOW: FeatureSet.JsonFormat.ValueType
    LEGACY_BEST_EFFORT: FeatureSet.JsonFormat.ValueType
    class _EnforceNamingStyle:
        ValueType = typing.NewType("ValueType", builtins.int)
        type V = ValueType

    class _EnforceNamingStyleEnumTypeWrapper(
        google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
            FeatureSet._EnforceNamingStyle.ValueType
        ],
        builtins.type,
    ):
        DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
        ENFORCE_NAMING_STYLE_UNKNOWN: FeatureSet._EnforceNamingStyle.ValueType
        STYLE2024: FeatureSet._EnforceNamingStyle.ValueType
        STYLE_LEGACY: FeatureSet._EnforceNamingStyle.ValueType

    class EnforceNamingStyle(
        _EnforceNamingStyle,
        metaclass=_EnforceNamingStyleEnumTypeWrapper,
    ): ...
    ENFORCE_NAMING_STYLE_UNKNOWN: FeatureSet.EnforceNamingStyle.ValueType
    STYLE2024: FeatureSet.EnforceNamingStyle.ValueType
    STYLE_LEGACY: FeatureSet.EnforceNamingStyle.ValueType
    @typing.final
    class VisibilityFeature(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        class _DefaultSymbolVisibility:
            ValueType = typing.NewType("ValueType", builtins.int)
            type V = ValueType

        class _DefaultSymbolVisibilityEnumTypeWrapper(
            google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            ],
            builtins.type,
        ):
            DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
            DEFAULT_SYMBOL_VISIBILITY_UNKNOWN: (
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            )
            EXPORT_ALL: (
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            )
            """Default pre-EDITION_2024, all UNSET visibility are export."""
            EXPORT_TOP_LEVEL: (
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            )
            """All top-level symbols default to export, nested default to local."""
            LOCAL_ALL: (
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            )
            """All symbols default to local."""
            STRICT: (
                FeatureSet.VisibilityFeature._DefaultSymbolVisibility.ValueType
            )
            """All symbols local by default. Nested types cannot be exported.
            With special case caveat for message { enum {} reserved 1 to max; }
            This is the recommended setting for new protos.
            """

        class DefaultSymbolVisibility(
            _DefaultSymbolVisibility,
            metaclass=_DefaultSymbolVisibilityEnumTypeWrapper,
        ): ...
        DEFAULT_SYMBOL_VISIBILITY_UNKNOWN: (
            FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        )
        EXPORT_ALL: (
            FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        )
        """Default pre-EDITION_2024, all UNSET visibility are export."""
        EXPORT_TOP_LEVEL: (
            FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        )
        """All top-level symbols default to export, nested default to local."""
        LOCAL_ALL: (
            FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        )
        """All symbols default to local."""
        STRICT: FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        """All symbols local by default. Nested types cannot be exported.
        With special case caveat for message { enum {} reserved 1 to max; }
        This is the recommended setting for new protos.
        """
        def __init__(self) -> None: ...

    FIELD_PRESENCE_FIELD_NUMBER: builtins.int
    ENUM_TYPE_FIELD_NUMBER: builtins.int
    REPEATED_FIELD_ENCODING_FIELD_NUMBER: builtins.int
    UTF8_VALIDATION_FIELD_NUMBER: builtins.int
    MESSAGE_ENCODING_FIELD_NUMBER: builtins.int
    JSON_FORMAT_FIELD_NUMBER: builtins.int
    ENFORCE_NAMING_STYLE_FIELD_NUMBER: builtins.int
    DEFAULT_SYMBOL_VISIBILITY_FIELD_NUMBER: builtins.int
    field_presence: global___FeatureSet.FieldPresence.ValueType
    enum_type: global___FeatureSet.EnumType.ValueType
    repeated_field_encoding: (
        global___FeatureSet.RepeatedFieldEncoding.ValueType
    )
    utf8_validation: global___FeatureSet.Utf8Validation.ValueType
    message_encoding: global___FeatureSet.MessageEncoding.ValueType
    json_format: global___FeatureSet.JsonFormat.ValueType
    enforce_naming_style: global___FeatureSet.EnforceNamingStyle.ValueType
    default_symbol_visibility: (
        global___FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
    )
    def __init__(
        self,
        *,
        field_presence: global___FeatureSet.FieldPresence.ValueType
        | None = ...,
        enum_type: global___FeatureSet.EnumType.ValueType | None = ...,
        repeated_field_encoding: global___FeatureSet.RepeatedFieldEncoding.ValueType
        | None = ...,
        utf8_validation: global___FeatureSet.Utf8Validation.ValueType
        | None = ...,
        message_encoding: global___FeatureSet.MessageEncoding.ValueType
        | None = ...,
        json_format: global___FeatureSet.JsonFormat.ValueType | None = ...,
        enforce_naming_style: global___FeatureSet.EnforceNamingStyle.ValueType
        | None = ...,
        default_symbol_visibility: global___FeatureSet.VisibilityFeature.DefaultSymbolVisibility.ValueType
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "default_symbol_visibility",
            b"default_symbol_visibility",
            "enforce_naming_style",
            b"enforce_naming_style",
            "enum_type",
            b"enum_type",
            "field_presence",
            b"field_presence",
            "json_format",
            b"json_format",
            "message_encoding",
            b"message_encoding",
            "repeated_field_encoding",
            b"repeated_field_encoding",
            "utf8_validation",
            b"utf8_validation",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "default_symbol_visibility",
            b"default_symbol_visibility",
            "enforce_naming_style",
            b"enforce_naming_style",
            "enum_type",
            b"enum_type",
            "field_presence",
            b"field_presence",
            "json_format",
            b"json_format",
            "message_encoding",
            b"message_encoding",
            "repeated_field_encoding",
            b"repeated_field_encoding",
            "utf8_validation",
            b"utf8_validation",
        ],
    ) -> None: ...

global___FeatureSet = FeatureSet

@typing.final
class FeatureSetDefaults(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class FeatureSetEditionDefault(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        EDITION_FIELD_NUMBER: builtins.int
        OVERRIDABLE_FEATURES_FIELD_NUMBER: builtins.int
        FIXED_FEATURES_FIELD_NUMBER: builtins.int
        edition: global___Edition.ValueType
        @property
        def overridable_features(self) -> global___FeatureSet: ...
        @property
        def fixed_features(self) -> global___FeatureSet: ...
        def __init__(
            self,
            *,
            edition: global___Edition.ValueType | None = ...,
            overridable_features: global___FeatureSet | None = ...,
            fixed_features: global___FeatureSet | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "edition",
                b"edition",
                "fixed_features",
                b"fixed_features",
                "overridable_features",
                b"overridable_features",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "edition",
                b"edition",
                "fixed_features",
                b"fixed_features",
                "overridable_features",
                b"overridable_features",
            ],
        ) -> None: ...

    DEFAULTS_FIELD_NUMBER: builtins.int
    MINIMUM_EDITION_FIELD_NUMBER: builtins.int
    MAXIMUM_EDITION_FIELD_NUMBER: builtins.int
    minimum_edition: global___Edition.ValueType
    """The minimum supported edition (inclusive) when this was constructed.
    Editions before this will not have defaults.
    """
    maximum_edition: global___Edition.ValueType
    """The maximum known edition (inclusive) when this was constructed. Editions
    after this will not have reliable defaults.
    """
    @property
    def defaults(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___FeatureSetDefaults.FeatureSetEditionDefault
    ]: ...
    def __init__(
        self,
        *,
        defaults: collections.abc.Iterable[
            global___FeatureSetDefaults.FeatureSetEditionDefault
        ]
        | None = ...,
        minimum_edition: global___Edition.ValueType | None = ...,
        maximum_edition: global___Edition.ValueType | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "maximum_edition",
            b"maximum_edition",
            "minimum_edition",
            b"minimum_edition",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "defaults",
            b"defaults",
            "maximum_edition",
            b"maximum_edition",
            "minimum_edition",
            b"minimum_edition",
        ],
    ) -> None: ...

global___FeatureSetDefaults = FeatureSetDefaults

@typing.final
class SourceCodeInfo(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class Location(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        PATH_FIELD_NUMBER: builtins.int
        SPAN_FIELD_NUMBER: builtins.int
        LEADING_COMMENTS_FIELD_NUMBER: builtins.int
        TRAILING_COMMENTS_FIELD_NUMBER: builtins.int
        LEADING_DETACHED_COMMENTS_FIELD_NUMBER: builtins.int
        leading_comments: builtins.str
        """If this SourceCodeInfo represents a complete declaration, these are any
        comments appearing before and after the declaration which appear to be
        attached to the declaration.

        A series of line comments appearing on consecutive lines, with no other
        tokens appearing on those lines, will be treated as a single comment.

        leading_detached_comments will keep paragraphs of comments that appear
        before (but not connected to) the current element. Each paragraph,
        separated by empty lines, will be one comment element in the repeated
        field.

        Only the comment content is provided; comment markers (e.g. //) are
        stripped out.  For block comments, leading whitespace and an asterisk
        will be stripped from the beginning of each line other than the first.
        Newlines are included in the output.

        Examples:

          optional int32 foo = 1;  // Comment attached to foo.
          // Comment attached to bar.
          optional int32 bar = 2;

          optional string baz = 3;
          // Comment attached to baz.
          // Another line attached to baz.

          // Comment attached to moo.
          //
          // Another line attached to moo.
          optional double moo = 4;

          // Detached comment for corge. This is not leading or trailing comments
          // to moo or corge because there are blank lines separating it from
          // both.

          // Detached comment for corge paragraph 2.

          optional string corge = 5;
          /* Block comment attached
           * to corge.  Leading asterisks
           * will be removed. */
          /* Block comment attached to
           * grault. */
          optional int32 grault = 6;

          // ignored detached comments.
        """
        trailing_comments: builtins.str
        @property
        def path(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        @property
        def span(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        @property
        def leading_detached_comments(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.str
        ]: ...
        def __init__(
            self,
            *,
            path: collections.abc.Iterable[builtins.int] | None = ...,
            span: collections.abc.Iterable[builtins.int] | None = ...,
            leading_comments: builtins.str | None = ...,
            trailing_comments: builtins.str | None = ...,
            leading_detached_comments: collections.abc.Iterable[builtins.str]
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "leading_comments",
                b"leading_comments",
                "trailing_comments",
                b"trailing_comments",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "leading_comments",
                b"leading_comments",
                "leading_detached_comments",
                b"leading_detached_comments",
                "path",
                b"path",
                "span",
                b"span",
                "trailing_comments",
                b"trailing_comments",
            ],
        ) -> None: ...

    LOCATION_FIELD_NUMBER: builtins.int
    @property
    def location(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___SourceCodeInfo.Location
    ]: ...
    def __init__(
        self,
        *,
        location: collections.abc.Iterable[global___SourceCodeInfo.Location]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["location", b"location"],
    ) -> None: ...

global___SourceCodeInfo = SourceCodeInfo

@typing.final
class GeneratedCodeInfo(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class Annotation(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        class _Semantic:
            ValueType = typing.NewType("ValueType", builtins.int)
            type V = ValueType

        class _SemanticEnumTypeWrapper(
            google.protobuf.internal.enum_type_wrapper._EnumTypeWrapper[
                GeneratedCodeInfo.Annotation._Semantic.ValueType
            ],
            builtins.type,
        ):
            DESCRIPTOR: google.protobuf.descriptor.EnumDescriptor
            NONE: GeneratedCodeInfo.Annotation._Semantic.ValueType
            """There is no effect or the effect is indescribable."""
            SET: GeneratedCodeInfo.Annotation._Semantic.ValueType
            """The element is set or otherwise mutated."""
            ALIAS: GeneratedCodeInfo.Annotation._Semantic.ValueType
            """An alias to the element is returned."""

        class Semantic(_Semantic, metaclass=_SemanticEnumTypeWrapper): ...
        NONE: GeneratedCodeInfo.Annotation.Semantic.ValueType
        """There is no effect or the effect is indescribable."""
        SET: GeneratedCodeInfo.Annotation.Semantic.ValueType
        """The element is set or otherwise mutated."""
        ALIAS: GeneratedCodeInfo.Annotation.Semantic.ValueType
        """An alias to the element is returned."""
        PATH_FIELD_NUMBER: builtins.int
        SOURCE_FILE_FIELD_NUMBER: builtins.int
        BEGIN_FIELD_NUMBER: builtins.int
        END_FIELD_NUMBER: builtins.int
        SEMANTIC_FIELD_NUMBER: builtins.int
        source_file: builtins.str
        """Identifies the filesystem path to the original source .proto."""
        begin: builtins.int
        """Identifies the starting offset in bytes in the generated code
        that relates to the identified object.
        """
        end: builtins.int
        """Identifies the ending offset in bytes in the generated code that
        relates to the identified object. The end offset should be one past
        the last relevant byte (so the length of the text = end - begin).
        """
        semantic: global___GeneratedCodeInfo.Annotation.Semantic.ValueType
        @property
        def path(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        def __init__(
            self,
            *,
            path: collections.abc.Iterable[builtins.int] | None = ...,
            source_file: builtins.str | None = ...,
            begin: builtins.int | None = ...,
            end: builtins.int | None = ...,
            semantic: global___GeneratedCodeInfo.Annotation.Semantic.ValueType
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "begin",
                b"begin",
                "end",
                b"end",
                "semantic",
                b"semantic",
                "source_file",
                b"source_file",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "begin",
                b"begin",
                "end",
                b"end",
                "path",
                b"path",
                "semantic",
                b"semantic",
                "source_file",
                b"source_file",
            ],
        ) -> None: ...

    ANNOTATION_FIELD_NUMBER: builtins.int
    @property
    def annotation(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___GeneratedCodeInfo.Annotation
    ]: ...
    def __init__(
        self,
        *,
        annotation: collections.abc.Iterable[
            global___GeneratedCodeInfo.Annotation
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal["annotation", b"annotation"],
    ) -> None: ...

global___GeneratedCodeInfo = GeneratedCodeInfo
