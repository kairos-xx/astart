import builtins
import collections.abc
import typing

import google.protobuf.any_pb2
import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.graph_pb2
import tensorflow.core.framework.op_def_pb2
import tensorflow.core.framework.tensor_pb2
import tensorflow.core.framework.tensor_shape_pb2
import tensorflow.core.framework.types_pb2
import tensorflow.core.protobuf.saved_object_graph_pb2
import tensorflow.core.protobuf.saver_pb2
import tensorflow.core.protobuf.struct_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class MetaGraphDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class MetaInfoDef(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        @typing.final
        class FunctionAliasesEntry(google.protobuf.message.Message):
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

        META_GRAPH_VERSION_FIELD_NUMBER: builtins.int
        STRIPPED_OP_LIST_FIELD_NUMBER: builtins.int
        ANY_INFO_FIELD_NUMBER: builtins.int
        TAGS_FIELD_NUMBER: builtins.int
        TENSORFLOW_VERSION_FIELD_NUMBER: builtins.int
        TENSORFLOW_GIT_VERSION_FIELD_NUMBER: builtins.int
        STRIPPED_DEFAULT_ATTRS_FIELD_NUMBER: builtins.int
        FUNCTION_ALIASES_FIELD_NUMBER: builtins.int
        meta_graph_version: builtins.str
        """User specified Version string. Can be the name of the model and revision,
        steps this model has been trained to, etc.
        """
        tensorflow_version: builtins.str
        """The __version__ string of the tensorflow build used to write this graph.
        This will be populated by the framework, which will overwrite any user
        supplied value.
        """
        tensorflow_git_version: builtins.str
        """The __git_version__ string of the tensorflow build used to write this
        graph. This will be populated by the framework, which will overwrite any
        user supplied value.
        """
        stripped_default_attrs: builtins.bool
        """A flag to denote whether default-valued attrs have been stripped from
        the nodes in this graph_def.
        """
        @property
        def stripped_op_list(
            self,
        ) -> tensorflow.core.framework.op_def_pb2.OpList: ...
        @property
        def any_info(self) -> google.protobuf.any_pb2.Any: ...
        @property
        def tags(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.str
        ]: ...
        @property
        def function_aliases(
            self,
        ) -> google.protobuf.internal.containers.ScalarMap[
            builtins.str,
            builtins.str,
        ]: ...
        def __init__(
            self,
            *,
            meta_graph_version: builtins.str | None = ...,
            stripped_op_list: tensorflow.core.framework.op_def_pb2.OpList
            | None = ...,
            any_info: google.protobuf.any_pb2.Any | None = ...,
            tags: collections.abc.Iterable[builtins.str] | None = ...,
            tensorflow_version: builtins.str | None = ...,
            tensorflow_git_version: builtins.str | None = ...,
            stripped_default_attrs: builtins.bool | None = ...,
            function_aliases: collections.abc.Mapping[
                builtins.str,
                builtins.str,
            ]
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal[
                "any_info",
                b"any_info",
                "stripped_op_list",
                b"stripped_op_list",
            ],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "any_info",
                b"any_info",
                "function_aliases",
                b"function_aliases",
                "meta_graph_version",
                b"meta_graph_version",
                "stripped_default_attrs",
                b"stripped_default_attrs",
                "stripped_op_list",
                b"stripped_op_list",
                "tags",
                b"tags",
                "tensorflow_git_version",
                b"tensorflow_git_version",
                "tensorflow_version",
                b"tensorflow_version",
            ],
        ) -> None: ...

    @typing.final
    class CollectionDefEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___CollectionDef: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___CollectionDef | None = ...,
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
    class SignatureDefEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___SignatureDef: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___SignatureDef | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    META_INFO_DEF_FIELD_NUMBER: builtins.int
    GRAPH_DEF_FIELD_NUMBER: builtins.int
    SAVER_DEF_FIELD_NUMBER: builtins.int
    COLLECTION_DEF_FIELD_NUMBER: builtins.int
    SIGNATURE_DEF_FIELD_NUMBER: builtins.int
    ASSET_FILE_DEF_FIELD_NUMBER: builtins.int
    OBJECT_GRAPH_DEF_FIELD_NUMBER: builtins.int
    @property
    def meta_info_def(self) -> global___MetaGraphDef.MetaInfoDef: ...
    @property
    def graph_def(self) -> tensorflow.core.framework.graph_pb2.GraphDef: ...
    @property
    def saver_def(self) -> tensorflow.core.protobuf.saver_pb2.SaverDef: ...
    @property
    def collection_def(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___CollectionDef,
    ]: ...
    @property
    def signature_def(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___SignatureDef,
    ]: ...
    @property
    def asset_file_def(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        global___AssetFileDef
    ]: ...
    @property
    def object_graph_def(
        self,
    ) -> tensorflow.core.protobuf.saved_object_graph_pb2.SavedObjectGraph: ...
    def __init__(
        self,
        *,
        meta_info_def: global___MetaGraphDef.MetaInfoDef | None = ...,
        graph_def: tensorflow.core.framework.graph_pb2.GraphDef | None = ...,
        saver_def: tensorflow.core.protobuf.saver_pb2.SaverDef | None = ...,
        collection_def: collections.abc.Mapping[
            builtins.str,
            global___CollectionDef,
        ]
        | None = ...,
        signature_def: collections.abc.Mapping[
            builtins.str,
            global___SignatureDef,
        ]
        | None = ...,
        asset_file_def: collections.abc.Iterable[global___AssetFileDef]
        | None = ...,
        object_graph_def: tensorflow.core.protobuf.saved_object_graph_pb2.SavedObjectGraph
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "graph_def",
            b"graph_def",
            "meta_info_def",
            b"meta_info_def",
            "object_graph_def",
            b"object_graph_def",
            "saver_def",
            b"saver_def",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "asset_file_def",
            b"asset_file_def",
            "collection_def",
            b"collection_def",
            "graph_def",
            b"graph_def",
            "meta_info_def",
            b"meta_info_def",
            "object_graph_def",
            b"object_graph_def",
            "saver_def",
            b"saver_def",
            "signature_def",
            b"signature_def",
        ],
    ) -> None: ...

global___MetaGraphDef = MetaGraphDef

@typing.final
class CollectionDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class NodeList(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        @property
        def value(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.str
        ]: ...
        def __init__(
            self,
            *,
            value: collections.abc.Iterable[builtins.str] | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> None: ...

    @typing.final
    class BytesList(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        @property
        def value(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.bytes
        ]: ...
        def __init__(
            self,
            *,
            value: collections.abc.Iterable[builtins.bytes] | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> None: ...

    @typing.final
    class Int64List(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        @property
        def value(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.int
        ]: ...
        def __init__(
            self,
            *,
            value: collections.abc.Iterable[builtins.int] | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> None: ...

    @typing.final
    class FloatList(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        @property
        def value(
            self,
        ) -> google.protobuf.internal.containers.RepeatedScalarFieldContainer[
            builtins.float
        ]: ...
        def __init__(
            self,
            *,
            value: collections.abc.Iterable[builtins.float] | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> None: ...

    @typing.final
    class AnyList(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUE_FIELD_NUMBER: builtins.int
        @property
        def value(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            google.protobuf.any_pb2.Any
        ]: ...
        def __init__(
            self,
            *,
            value: collections.abc.Iterable[google.protobuf.any_pb2.Any]
            | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> None: ...

    NODE_LIST_FIELD_NUMBER: builtins.int
    BYTES_LIST_FIELD_NUMBER: builtins.int
    INT64_LIST_FIELD_NUMBER: builtins.int
    FLOAT_LIST_FIELD_NUMBER: builtins.int
    ANY_LIST_FIELD_NUMBER: builtins.int
    @property
    def node_list(self) -> global___CollectionDef.NodeList: ...
    @property
    def bytes_list(self) -> global___CollectionDef.BytesList: ...
    @property
    def int64_list(self) -> global___CollectionDef.Int64List: ...
    @property
    def float_list(self) -> global___CollectionDef.FloatList: ...
    @property
    def any_list(self) -> global___CollectionDef.AnyList: ...
    def __init__(
        self,
        *,
        node_list: global___CollectionDef.NodeList | None = ...,
        bytes_list: global___CollectionDef.BytesList | None = ...,
        int64_list: global___CollectionDef.Int64List | None = ...,
        float_list: global___CollectionDef.FloatList | None = ...,
        any_list: global___CollectionDef.AnyList | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "any_list",
            b"any_list",
            "bytes_list",
            b"bytes_list",
            "float_list",
            b"float_list",
            "int64_list",
            b"int64_list",
            "kind",
            b"kind",
            "node_list",
            b"node_list",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "any_list",
            b"any_list",
            "bytes_list",
            b"bytes_list",
            "float_list",
            b"float_list",
            "int64_list",
            b"int64_list",
            "kind",
            b"kind",
            "node_list",
            b"node_list",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["kind", b"kind"],
    ) -> (
        typing.Literal[
            "node_list",
            "bytes_list",
            "int64_list",
            "float_list",
            "any_list",
        ]
        | None
    ): ...

global___CollectionDef = CollectionDef

@typing.final
class TensorInfo(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class CooSparse(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        VALUES_TENSOR_NAME_FIELD_NUMBER: builtins.int
        INDICES_TENSOR_NAME_FIELD_NUMBER: builtins.int
        DENSE_SHAPE_TENSOR_NAME_FIELD_NUMBER: builtins.int
        values_tensor_name: builtins.str
        """The shape of the values Tensor is [?].  Its dtype must be the dtype of
        the SparseTensor as a whole, given in the enclosing TensorInfo.
        """
        indices_tensor_name: builtins.str
        """The indices Tensor must have dtype int64 and shape [?, ?]."""
        dense_shape_tensor_name: builtins.str
        """The dynamic logical shape represented by the SparseTensor is recorded in
        the Tensor referenced here.  It must have dtype int64 and shape [?].
        """
        def __init__(
            self,
            *,
            values_tensor_name: builtins.str | None = ...,
            indices_tensor_name: builtins.str | None = ...,
            dense_shape_tensor_name: builtins.str | None = ...,
        ) -> None: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "dense_shape_tensor_name",
                b"dense_shape_tensor_name",
                "indices_tensor_name",
                b"indices_tensor_name",
                "values_tensor_name",
                b"values_tensor_name",
            ],
        ) -> None: ...

    @typing.final
    class CompositeTensor(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        TYPE_SPEC_FIELD_NUMBER: builtins.int
        COMPONENTS_FIELD_NUMBER: builtins.int
        @property
        def type_spec(
            self,
        ) -> tensorflow.core.protobuf.struct_pb2.TypeSpecProto: ...
        @property
        def components(
            self,
        ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
            global___TensorInfo
        ]: ...
        def __init__(
            self,
            *,
            type_spec: tensorflow.core.protobuf.struct_pb2.TypeSpecProto
            | None = ...,
            components: collections.abc.Iterable[global___TensorInfo]
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["type_spec", b"type_spec"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal[
                "components",
                b"components",
                "type_spec",
                b"type_spec",
            ],
        ) -> None: ...

    NAME_FIELD_NUMBER: builtins.int
    COO_SPARSE_FIELD_NUMBER: builtins.int
    COMPOSITE_TENSOR_FIELD_NUMBER: builtins.int
    DTYPE_FIELD_NUMBER: builtins.int
    TENSOR_SHAPE_FIELD_NUMBER: builtins.int
    name: builtins.str
    """For dense `Tensor`s, the name of the tensor in the graph."""
    dtype: tensorflow.core.framework.types_pb2.DataType.ValueType
    @property
    def coo_sparse(self) -> global___TensorInfo.CooSparse: ...
    @property
    def composite_tensor(self) -> global___TensorInfo.CompositeTensor: ...
    @property
    def tensor_shape(
        self,
    ) -> tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto: ...
    def __init__(
        self,
        *,
        name: builtins.str | None = ...,
        coo_sparse: global___TensorInfo.CooSparse | None = ...,
        composite_tensor: global___TensorInfo.CompositeTensor | None = ...,
        dtype: tensorflow.core.framework.types_pb2.DataType.ValueType
        | None = ...,
        tensor_shape: tensorflow.core.framework.tensor_shape_pb2.TensorShapeProto
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "composite_tensor",
            b"composite_tensor",
            "coo_sparse",
            b"coo_sparse",
            "encoding",
            b"encoding",
            "name",
            b"name",
            "tensor_shape",
            b"tensor_shape",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "composite_tensor",
            b"composite_tensor",
            "coo_sparse",
            b"coo_sparse",
            "dtype",
            b"dtype",
            "encoding",
            b"encoding",
            "name",
            b"name",
            "tensor_shape",
            b"tensor_shape",
        ],
    ) -> None: ...
    def WhichOneof(
        self,
        oneof_group: typing.Literal["encoding", b"encoding"],
    ) -> typing.Literal["name", "coo_sparse", "composite_tensor"] | None: ...

global___TensorInfo = TensorInfo

@typing.final
class SignatureDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    @typing.final
    class InputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___TensorInfo: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___TensorInfo | None = ...,
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
    class OutputsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(self) -> global___TensorInfo: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: global___TensorInfo | None = ...,
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
    class DefaultsEntry(google.protobuf.message.Message):
        DESCRIPTOR: google.protobuf.descriptor.Descriptor
        KEY_FIELD_NUMBER: builtins.int
        VALUE_FIELD_NUMBER: builtins.int
        key: builtins.str
        @property
        def value(
            self,
        ) -> tensorflow.core.framework.tensor_pb2.TensorProto: ...
        def __init__(
            self,
            *,
            key: builtins.str | None = ...,
            value: tensorflow.core.framework.tensor_pb2.TensorProto
            | None = ...,
        ) -> None: ...
        def HasField(
            self,
            field_name: typing.Literal["value", b"value"],
        ) -> builtins.bool: ...
        def ClearField(
            self,
            field_name: typing.Literal["key", b"key", "value", b"value"],
        ) -> None: ...

    INPUTS_FIELD_NUMBER: builtins.int
    OUTPUTS_FIELD_NUMBER: builtins.int
    METHOD_NAME_FIELD_NUMBER: builtins.int
    DEFAULTS_FIELD_NUMBER: builtins.int
    method_name: builtins.str
    """Deprecated: TensorFlow 2 always sets this to a fixed value;
    open-source TF Serving stopped checking by default since release 2.4.

    In TensorFlow 1, the method_name enabled users to mark a SignatureDef as
    supporting a particular method. Multiple SignatureDefs in a single
    MetaGraphDef could have the same method_name (e.g., to support multi-headed
    computation).
    """
    @property
    def inputs(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___TensorInfo,
    ]: ...
    @property
    def outputs(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        global___TensorInfo,
    ]: ...
    @property
    def defaults(
        self,
    ) -> google.protobuf.internal.containers.MessageMap[
        builtins.str,
        tensorflow.core.framework.tensor_pb2.TensorProto,
    ]: ...
    def __init__(
        self,
        *,
        inputs: collections.abc.Mapping[builtins.str, global___TensorInfo]
        | None = ...,
        outputs: collections.abc.Mapping[builtins.str, global___TensorInfo]
        | None = ...,
        method_name: builtins.str | None = ...,
        defaults: collections.abc.Mapping[
            builtins.str,
            tensorflow.core.framework.tensor_pb2.TensorProto,
        ]
        | None = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "defaults",
            b"defaults",
            "inputs",
            b"inputs",
            "method_name",
            b"method_name",
            "outputs",
            b"outputs",
        ],
    ) -> None: ...

global___SignatureDef = SignatureDef

@typing.final
class AssetFileDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    TENSOR_INFO_FIELD_NUMBER: builtins.int
    FILENAME_FIELD_NUMBER: builtins.int
    filename: builtins.str
    """The filename within an assets directory. Note: does not include the path
    prefix, i.e. directories. For an asset at /tmp/path/vocab.txt, the filename
    would be "vocab.txt".
    """
    @property
    def tensor_info(self) -> global___TensorInfo: ...
    def __init__(
        self,
        *,
        tensor_info: global___TensorInfo | None = ...,
        filename: builtins.str | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal["tensor_info", b"tensor_info"],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "filename",
            b"filename",
            "tensor_info",
            b"tensor_info",
        ],
    ) -> None: ...

global___AssetFileDef = AssetFileDef
