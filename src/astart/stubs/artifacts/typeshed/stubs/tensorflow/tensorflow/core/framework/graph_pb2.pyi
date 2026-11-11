import builtins
import collections.abc
import typing

import google.protobuf.descriptor
import google.protobuf.internal.containers
import google.protobuf.message
import tensorflow.core.framework.function_pb2
import tensorflow.core.framework.graph_debug_info_pb2
import tensorflow.core.framework.node_def_pb2
import tensorflow.core.framework.versions_pb2

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor

@typing.final
class GraphDef(google.protobuf.message.Message):
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
    NODE_FIELD_NUMBER: builtins.int
    VERSIONS_FIELD_NUMBER: builtins.int
    VERSION_FIELD_NUMBER: builtins.int
    LIBRARY_FIELD_NUMBER: builtins.int
    DEBUG_INFO_FIELD_NUMBER: builtins.int
    version: builtins.int
    """Deprecated single version field; use versions above instead.  Since all
    GraphDef changes before "versions" was introduced were forward
    compatible, this field is entirely ignored.
    """
    @property
    def node(
        self,
    ) -> google.protobuf.internal.containers.RepeatedCompositeFieldContainer[
        tensorflow.core.framework.node_def_pb2.NodeDef
    ]: ...
    @property
    def versions(
        self,
    ) -> tensorflow.core.framework.versions_pb2.VersionDef: ...
    @property
    def library(
        self,
    ) -> tensorflow.core.framework.function_pb2.FunctionDefLibrary: ...
    @property
    def debug_info(
        self,
    ) -> tensorflow.core.framework.graph_debug_info_pb2.GraphDebugInfo: ...
    def __init__(
        self,
        *,
        node: collections.abc.Iterable[
            tensorflow.core.framework.node_def_pb2.NodeDef
        ]
        | None = ...,
        versions: tensorflow.core.framework.versions_pb2.VersionDef
        | None = ...,
        version: builtins.int | None = ...,
        library: tensorflow.core.framework.function_pb2.FunctionDefLibrary
        | None = ...,
        debug_info: tensorflow.core.framework.graph_debug_info_pb2.GraphDebugInfo
        | None = ...,
    ) -> None: ...
    def HasField(
        self,
        field_name: typing.Literal[
            "debug_info",
            b"debug_info",
            "library",
            b"library",
            "versions",
            b"versions",
        ],
    ) -> builtins.bool: ...
    def ClearField(
        self,
        field_name: typing.Literal[
            "debug_info",
            b"debug_info",
            "library",
            b"library",
            "node",
            b"node",
            "version",
            b"version",
            "versions",
            b"versions",
        ],
    ) -> None: ...

global___GraphDef = GraphDef
