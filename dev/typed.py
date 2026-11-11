"""Typed test file for resolver inference with merged edge cases.

This implementation supplies explicit types and keyword-capable calls while
retaining the executable scenarios of the original untyped corpus.

"""

# Copyright (c) 2026 Contributors

from __future__ import annotations

from abc import ABC, abstractmethod
from asyncio import run, sleep
from collections import ChainMap, Counter, OrderedDict, defaultdict, deque
from collections.abc import (
    AsyncGenerator,
    AsyncIterator,
    Awaitable,
    Buffer,
    Callable,
    Generator,
    Hashable,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
)
from contextlib import asynccontextmanager, contextmanager, suppress
from contextvars import ContextVar, Token
from dataclasses import dataclass
from enum import Enum, auto
from functools import (
    cached_property,
    lru_cache,
    partial,
    reduce,
    singledispatch,
    wraps,
)
from importlib import import_module
from itertools import (
    accumulate,
    chain,
    combinations,
    compress,
    dropwhile,
    groupby,
    islice,
    permutations,
    product,
    takewhile,
    zip_longest,
)
from json import dumps, loads
from math import nan
from operator import add, mul
from pathlib import Path
from re import search, split
from tempfile import NamedTemporaryFile, gettempdir
from typing import (
    IO,
    TYPE_CHECKING,
    ClassVar,
    Final,
    Literal,
    Never,
    Protocol,
    ReadOnly,
    Self,
    SupportsIndex,
    SupportsInt,
    TypedDict,
    cast,
    final,
    overload,
    override,
)
from uuid import NAMESPACE_DNS, UUID, uuid5
from weakref import ReferenceType, WeakKeyDictionary, ref

if TYPE_CHECKING:
    from types import ModuleType, TracebackType


type StrOrBufferOrSupportsIntOrSupportsIndex = (
    str | Buffer | SupportsInt | SupportsIndex
)
type ListInt = list[int]
type ListIntOrNone = ListInt | None
type ListFloatOrStr = list[float | str]
type JSONScalar = str | int | float | bool | None
type JSONValue = JSONScalar | list[JSONValue] | dict[str, JSONValue]
type DictInt = dict[str, int]
type DictBool = dict[str, bool]
type ListIntOrDictIntOrStrOrInt = ListInt | DictInt | str | int
type DictObject = dict[str, object]
type RegistryField = str | int | bool | ListStr | DictBool
type TupleExtendedResultListIntStrIntBool = tuple[
    "ExtendedResult[ListInt]",
    str,
    int,
    bool,
]
type ListStr = list[str]
type SetInt = set[int]
type SetBool = set[bool]
type TypeObject = type[object]
type TupleTypeObjectVariadic = tuple[TypeObject, ...]
type ObserverClassPair = tuple[
    type[SupportsNotify],
    type[SupportsMethodUpdate],
]
type StrategyClassPair = tuple[
    type[SupportsMethodExecuteIntInt],
    type[SupportsMethodExecuteIntInt],
]
type CommandClassPair = tuple[
    type[SupportsCommandExecute],
    type[SupportsReceiverAction],
]
type IntOrStr = int | str
type IntOrNone = int | None
type StrOrNone = str | None
type IntOrStrOrNone = IntOrStr | None
type StrOrBoolOrListInt = str | bool | ListInt
type TupleIntVariadic = tuple[int, ...]
type TupleIntStr = tuple[int, str]
type TupleStrInt = tuple[str, int]
type TupleStrVariadic = tuple[str, ...]
type TupleIntVariadicStr = tuple[*TupleIntVariadic, str]
type TupleBoolVariadic = tuple[bool, ...]
type TupleIntOrNoneVariadic = tuple[IntOrNone, ...]
type TupleIntOrNoneStrOrNone = tuple[IntOrNone, StrOrNone]
type ListTupleIntVariadic = list[TupleIntVariadic]
type ListTupleIntStr = list[TupleIntStr]
type ListTupleIntOrNoneStrOrNone = list[TupleIntOrNoneStrOrNone]
type TupleListIntVariadic = tuple[ListInt, ...]
type TupleDictIntVariadic = tuple[DictInt, ...]
type TupleListStrVariadic = tuple[ListStr, ...]
type TupleSetIntVariadic = tuple[SetInt, ...]
type DictListInt = dict[str, ListInt]
type DictIntInt = dict[int, int]
type DictStr = dict[str, str]
type DictTupleIntVariadic = dict[str, TupleIntVariadic]
type DictDictTupleIntVariadic = dict[str, DictTupleIntVariadic]
type SequenceInt = Sequence[int]
type SequenceStr = Sequence[str]
type SequenceSequenceInt = Sequence[SequenceInt]
type CallableIntInt = Callable[[int], int]
type CallableIntIntInt = Callable[[int, int], int]
type CallableVariadicInt = Callable[..., int]
type CallableStr = Callable[[], str]
type CallableNone = Callable[[], None]
type AwaitableInt = Awaitable[int]
type GeneratorInt = Generator[int]
type GeneratorIntIntOrStrOrNoneInt = Generator[
    int, int | Literal["stop"] | None, IntOrNone
]
type DequeInt = deque[int]
type CounterInt = Counter[int]
type OrderedDictStrInt = OrderedDict[str, int]
type DefaultdictStrInt = defaultdict[str, int]
type DefaultdictStrListInt = defaultdict[str, ListInt]
type DefaultdictStrDefaultdictStrListInt = defaultdict[
    str,
    DefaultdictStrListInt,
]
type CallableParametersToResult[**Parameters, Result] = Callable[
    Parameters,
    Result,
]
type CallableParametersToInt[**Parameters] = CallableParametersToResult[
    Parameters,
    int,
]
type CallableValueToResult[Value, Result] = Callable[[Value], Result]
type ListValue[Value] = list[Value]
type HybridMergeInput[ItemT, NamedT] = (
    HybridContainer[ItemT, NamedT] | MappingValueToResult[str, NamedT]
)
type SequenceValue[Value] = Sequence[Value]
type MappingValueToResult[Value, Result] = Mapping[Value, Result]
type TypeValue[Value] = type[Value]
type TupleValueVariadic[Value] = tuple[Value, ...]
type ValueOrNone[Value] = Value | None
type ValueOrInt[Value] = Value | int
type ValueOrIntOrStr[Value] = Value | IntOrStr
type StrOrValue[Value] = str | Value
type StrOrValueOrDictBool[Value] = StrOrValue[Value] | DictBool
type ValueOrOther[Value, Other] = Value | Other
type ValueOrOtherOrNone[Value, Other] = ValueOrOther[Value, Other] | None
type TupleStrValue[Value] = tuple[str, Value]
type DictBoolOrNone = DictBool | None
type DictRegistryMeta = dict[str, RegistryMeta]
type StrOrBuilderStructured = str | BuilderStructured
type StrOrDictStr = str | DictStr
type ListRecursiveChild = list[RecursiveChild]
type ListNormalizedRow = list[NormalizedRow]
type ListException = list[Exception]
type ListListInt = list[ListInt]
type DescriptorWithOwnerCacheInt = DescriptorWithOwnerCache[int]
type TypeAbstractBase = type[AbstractBase]
type TypeSupportsValue = type[SupportsValue]
type TypeSupportsClassMethods = type[
    SupportsClassMethodAndInstanceMethodAndStaticMethod
]
type CallableIntOrStrToIntOrStr = Callable[[IntOrStr], IntOrStr]
type CallablePayloadInt = CallablePayload[int]
type CallablePayloadStr = CallablePayload[str]
type IntOrStrOrCallablePayloadInt = IntOrStr | CallablePayloadInt
type IntOrStrOrCallablePayloadStr = IntOrStr | CallablePayloadStr
type HybridContainerNumericStrOrBoolOrListInt = HybridContainer[
    float,
    StrOrBoolOrListInt,
]
type TupleListTupleIntVariadicVariadic = tuple[ListTupleIntVariadic, ...]
type TupleAsyncPayloadListInt = tuple[AsyncPayload, ListInt]
type TupleListIntListStr = tuple[ListInt, ListStr]
type TupleListIntIntVariadic = tuple[ListInt, *TupleIntVariadic]
type TupleDefaultdictStrIntListStr = tuple[DefaultdictStrInt, ListStr]
type TupleListIntDictIntIntGeneratorInt = tuple[
    ListInt,
    DictIntInt,
    GeneratorInt,
]
type TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic = tuple[
    DefaultdictStrDefaultdictStrListInt,
    DictDictTupleIntVariadic,
]
type TupleListNormalizedRowDictListInt = tuple[ListNormalizedRow, DictListInt]
type TupleBuilderStructuredStr = tuple[BuilderStructured, str]
type TupleDescriptorSummaryIntStr = tuple[DescriptorSummary, int, str]
type TupleRegistryItemVariadicListStr = tuple[
    *TupleValueVariadic[RegistryItem],
    ListStr,
]
type TupleIntFloatVariadicListInt = tuple[
    int,
    *TupleValueVariadic[float],
    ListInt,
]
type TupleIntVariadicGeneratorIntIntOrStrOrNoneInt = tuple[
    *TupleIntVariadic,
    GeneratorIntIntOrStrOrNoneInt,
]
type TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt = tuple[
    BuiltinMethodList,
    BuiltinMethodDict,
    CustomAddSet,
    int,
]
type TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt = tuple[
    HybridContainerNumericStrOrBoolOrListInt,
    bool,
    StrOrBoolOrListInt,
]
type CallablePayloadResults = tuple[
    IntOrStrOrCallablePayloadInt,
    *TupleValueVariadic[IntOrStrOrCallablePayloadStr],
]
type TupleSupportsMetadataAndNameVariadicNodeMetadata = tuple[
    *TupleValueVariadic[SupportsMetadataAndName],
    NodeMetadata,
]
type TupleBytearrayMemoryviewBytesInt = tuple[
    bytearray,
    memoryview,
    bytes,
    int,
]
type UnpackingStressResult = tuple[
    int,
    ListInt,
    int,
    *TupleListTupleIntVariadicVariadic,
]
type CallableExamples = tuple[CallableVariadicInt, ...]
type PatternInput = (
    PointPattern
    | LinePattern
    | Mapping[str, IntOrStr | Sequence[IntOrStr]]
    | Sequence[IntOrStr]
    | None
)
type CallableIntIntSupportsVector = Callable[[int, int], SupportsVectorLike]


class NodeMetadata(TypedDict, total=False):
    """Optional depth and ancestry stored on an internal tree node.

    Attributes:
        depth (int): TODO.
        path (ListStr): TODO.

    """

    depth: int
    path: ListStr


class SupportsMetadataAndName(Protocol):
    """Public, recursively mutable node-attribute contract.

    Attributes:
        name (str): TODO.
        metadata (NodeMetadata): TODO.

    """

    name: str
    metadata: NodeMetadata


class AmountRecord(TypedDict, total=False):
    """Optional record fields accepted by the name/amount accumulator.

    Attributes:
        name (str | int | None): TODO.
        amount (str | int | float | None): TODO.

    """

    name: str | int | None
    amount: str | int | float | None


class RecursiveRoot(TypedDict):
    """A root holding children that reference their parent.

    Attributes:
        seed (int): TODO.
        children (ListRecursiveChild): TODO.

    """

    seed: int
    children: ListRecursiveChild


class RecursiveChild(TypedDict):
    """Child of a recursive root with a mutable integer payload.

    Attributes:
        parent (RecursiveRoot): TODO.
        values (ListInt): TODO.

    """

    parent: RecursiveRoot
    values: ListInt


class GroupInput(TypedDict):
    """Required fields in a groupable input record.

    Attributes:
        name (str): TODO.
        score (IntOrStr): TODO.

    """

    name: str
    score: IntOrStr


class NormalizedRow(TypedDict):
    """Normalized group name and validated numeric score.

    Attributes:
        name (str): TODO.
        score (int): TODO.

    """

    name: str
    score: int


class BuilderStructured(TypedDict):
    """Structured result produced by a noncompact builder.

    Attributes:
        parts (ListStr): TODO.
        options (DictBool): TODO.

    """

    parts: ListStr
    options: DictBool


class SingleDispatchDefault[T](TypedDict):
    """Preserve the input type of the fallback dispatch branch.

    Attributes:
        type (str): TODO.
        value (T): TODO.

    """

    type: str
    value: T


type DispatchOutcome[T] = IntOrStr | SingleDispatchDefault[T]


class ReflectionResult(TypedDict):
    """Names and metadata retrieved from a dynamic module attribute.

    Attributes:
        module (str): TODO.
        attr (ReadOnly[object]): TODO.
        attr_type (str): TODO.
        has_doc (bool): TODO.

    """

    module: str
    attr: ReadOnly[object]
    attr_type: str
    has_doc: bool


class PathReflectionResult(ReflectionResult):
    """A statically identified pathlib.Path reflection result.

    Attributes:
        attr (ReadOnly[type[Path]]): TODO.

    """

    attr: ReadOnly[type[Path]]


class JSONRoundtrip(TypedDict):
    """Round-tripped JSON record with statically known fields.

    Attributes:
        id (str): TODO.
        parts (ListStr): TODO.
        exists (bool): TODO.

    """

    id: str
    parts: ListStr
    exists: bool


class SyncContext(TypedDict):
    """Mutable synchronous context with typed event history.

    Attributes:
        seed (int): TODO.
        events (ListStr): TODO.

    """

    seed: int
    events: ListStr


class AsyncPayload(TypedDict):
    """Named asynchronous fetch result.

    Attributes:
        resource (str): TODO.
        value (int): TODO.

    """

    resource: str
    value: int


class CallablePayload[T](TypedDict):
    """Fallback result of a stateful callable.

    Attributes:
        value (T): TODO.
        scale (int): TODO.

    """

    value: T
    scale: int


class TestCallsPart1(TypedDict):
    """Typed output keys from test_function_calls_part1.

    Attributes:
        result1 (int): TODO.
        result2 (int): TODO.
        result3 (int): TODO.
        result4 (int): TODO.
        result5 (int): TODO.
        result6 (SequenceInt): TODO.
        result7 (SequenceInt): TODO.
        result8 (TupleListIntDictIntIntGeneratorInt): TODO.
        result9 (TupleListStrVariadic): TODO.
        result10 (int): TODO.
        result11 (int): TODO.
        result12 (int): TODO.
        result13 (ListInt): TODO.
        result14 (TypeSupportsClassMethods): TODO.
        result15 (TypeSupportsValue): TODO.
        result16 (CallableIntIntSupportsVector): TODO.
        result17 (object): TODO.
        result18 (type[SupportsCombinedMethod]): TODO.
        result19 (TypeAbstractBase): TODO.
        result20 (TupleIntVariadicStr): TODO.
        result21 (CallableIntOrStrToIntOrStr): TODO.
        result22 (SupportsCall2): TODO.

    """

    result1: int
    result2: int
    result3: int
    result4: int
    result5: int
    result6: SequenceInt
    result7: SequenceInt
    result8: TupleListIntDictIntIntGeneratorInt
    result9: TupleListStrVariadic
    result10: int
    result11: int
    result12: int
    result13: ListInt
    result14: TypeSupportsClassMethods
    result15: TypeSupportsValue
    result16: CallableIntIntSupportsVector
    result17: object
    result18: type[SupportsCombinedMethod]
    result19: TypeAbstractBase
    result20: TupleIntVariadicStr
    result21: CallableIntOrStrToIntOrStr
    result22: SupportsCall2


class TestCallsPart2(TypedDict):
    """Typed output keys from test_function_calls_part2.

    Attributes:
        result23 (TupleIntVariadic): TODO.
        result24 (TupleDictIntVariadic): TODO.
        result25 (TupleSetIntVariadic): TODO.
        result26 (TupleIntVariadic): TODO.
        result27 (int): TODO.
        result28 (TupleIntVariadic): TODO.
        result29 (TupleBoolVariadic): TODO.
        result30 (TupleBoolVariadic): TODO.
        result31 (TupleIntOrNoneVariadic): TODO.
        result32 (ListInt): TODO.
        result33 (DictInt): TODO.
        result34 (CallableExamples): TODO.
        result35 (int): TODO.
        result36 (ListInt): TODO.
        result37 (type[SupportsSlottedFields]): TODO.
        result38 (type[SupportsInjectedMethod]): TODO.
        result39 (TypeObject): TODO.
        result40 (type[SupportsMethodCreate]): TODO.
        result41 (type[SupportsBuilderMethods]): TODO.
        result42 (ObserverClassPair): TODO.
        result43 (StrategyClassPair): TODO.
        result44 (CommandClassPair): TODO.

    """

    result23: TupleIntVariadic
    result24: TupleDictIntVariadic
    result25: TupleSetIntVariadic
    result26: TupleIntVariadic
    result27: int
    result28: TupleIntVariadic
    result29: TupleBoolVariadic
    result30: TupleBoolVariadic
    result31: TupleIntOrNoneVariadic
    result32: ListInt
    result33: DictInt
    result34: CallableExamples
    result35: int
    result36: ListInt
    result37: type[SupportsSlottedFields]
    result38: type[SupportsInjectedMethod]
    result39: TypeObject
    result40: type[SupportsMethodCreate]
    result41: type[SupportsBuilderMethods]
    result42: ObserverClassPair
    result43: StrategyClassPair
    result44: CommandClassPair


class TestCallsPart3(TypedDict):
    """Typed output keys from test_function_calls_part3.

    Attributes:
        result45 (type[SupportsHandle]): TODO.
        result46 (CallableStr): TODO.
        result47 (CallableIntInt): TODO.
        result48 (int): TODO.
        result49 (DictListInt): TODO.
        result50 (TupleListTupleIntVariadicVariadic): TODO.
        result51 (DefaultdictStrInt): TODO.
        result52 (CounterInt): TODO.
        result53 (DequeInt): TODO.
        result54 (OrderedDictStrInt): TODO.
        result55 (Point): TODO.
        result56 (ListInt): TODO.
        result57 (ListInt): TODO.
        result58 (TupleListIntVariadic): TODO.
        result59 (ListTupleIntOrNoneStrOrNone): TODO.
        result60 (ListTupleIntStr): TODO.
        result61 (ListInt): TODO.
        result62 (ListInt): TODO.
        result63 (ListIntOrDictIntOrStrOrInt): TODO.
        result64 (ListIntOrDictIntOrStrOrInt): TODO.
        result65 (ListIntOrDictIntOrStrOrInt): TODO.
        result66 (ListIntOrDictIntOrStrOrInt): TODO.

    """

    result45: type[SupportsHandle]
    result46: CallableStr
    result47: CallableIntInt
    result48: int
    result49: DictListInt
    result50: TupleListTupleIntVariadicVariadic
    result51: DefaultdictStrInt
    result52: CounterInt
    result53: DequeInt
    result54: OrderedDictStrInt
    result55: Point
    result56: ListInt
    result57: ListInt
    result58: TupleListIntVariadic
    result59: ListTupleIntOrNoneStrOrNone
    result60: ListTupleIntStr
    result61: ListInt
    result62: ListInt
    result63: ListIntOrDictIntOrStrOrInt
    result64: ListIntOrDictIntOrStrOrInt
    result65: ListIntOrDictIntOrStrOrInt
    result66: ListIntOrDictIntOrStrOrInt


class ClassInstantiationResults(TypedDict):
    """Typed output keys from test_class_instantiations.

    Attributes:
        obj1 (BaseClass): TODO.
        obj2 (BaseClass): TODO.
        obj3 (DerivedClass): TODO.
        obj4 (MetaDecoratedClass): TODO.
        obj5 (DataClassExample): TODO.
        obj6 (DecoratedClass): TODO.

    """

    obj1: BaseClass
    obj2: BaseClass
    obj3: DerivedClass
    obj4: MetaDecoratedClass
    obj5: DataClassExample
    obj6: DecoratedClass


class OtherOperationResults(TypedDict):
    """Typed output keys from test_other_operations.

    Attributes:
        enum_val (EnumClass): TODO.
        closure_result (int): TODO.
        context_result (str): TODO.
        vec_sum (SupportsVectorLike): TODO.

    """

    enum_val: EnumClass
    closure_result: int
    context_result: str
    vec_sum: SupportsVectorLike


class NewInferenceResults(TypedDict):
    """Typed output keys from test_new_inference_edge_cases.

    Attributes:
        slices (SliceExampleResult): TODO.
            builtin_name_collisions
            (TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt): TODO.
        imports (ImportExampleResult): TODO.
        redefinitions (RedefinitionResult): TODO.
        scope_resolution (ScopeResolutionResult): TODO.
        positional_and_keyword_only (ListInt): TODO.
        builtin_name_collisions (TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt): TODO.

    """

    slices: SliceExampleResult
    builtin_name_collisions: (
        TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt
    )
    imports: ImportExampleResult
    redefinitions: RedefinitionResult
    scope_resolution: ScopeResolutionResult
    positional_and_keyword_only: ListInt


class PointPattern(TypedDict):
    """Valid two-dimensional pattern.

    Attributes:
        kind (Literal['point']): TODO.
        x (int): TODO.
        y (int): TODO.

    """

    kind: Literal["point"]
    x: int
    y: int


class LinePattern(TypedDict):
    """Valid line pattern whose points are integers.

    Attributes:
        kind (Literal['line']): TODO.
        points (ListInt): TODO.

    """

    kind: Literal["line"]
    points: ListInt


class ExtendedResultsPart1(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part1.

    Attributes:
        pattern_point (tuple[int, int]): TODO.
        pattern_line (ListInt): TODO.
        walrus (TupleDefaultdictStrIntListStr): TODO.
        recursive (RecursiveRoot): TODO.
        numeric (TupleIntFloatVariadicListInt): TODO.
        reassignment_int (int): TODO.
        reassignment_callable (tuple[str, str]): TODO.
        exceptions (StrOrDictStr): TODO.
        exception_group (TupleListIntListStr): TODO.
        reflection (PathReflectionResult): TODO.

    """

    pattern_point: tuple[int, int]
    pattern_line: ListInt
    walrus: TupleDefaultdictStrIntListStr
    recursive: RecursiveRoot
    numeric: TupleIntFloatVariadicListInt
    reassignment_int: int
    reassignment_callable: tuple[str, str]
    exceptions: StrOrDictStr
    exception_group: TupleListIntListStr
    reflection: PathReflectionResult


class ExtendedResultsPart2(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part2.

    Attributes:
        json_uuid_path (JSONRoundtrip): TODO.
        contextvars (Mapping[str, int]): TODO.
        unpacking (UnpackingStressResult): TODO.
        generator_control (TupleIntVariadicGeneratorIntIntOrStrOrNoneInt): TODO.
        descriptor (TupleDescriptorSummaryIntStr): TODO.
        metaclass_registry (TupleRegistryItemVariadicListStr): TODO.
        builder (TupleBuilderStructuredStr): TODO.
            container
            (TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt):
            TODO.
            callable_object
            (CallablePayloadResults):
            TODO.
        grouping (TupleListNormalizedRowDictListInt): TODO.
        container (TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt): TODO.
        callable_object (CallablePayloadResults): TODO.

    """

    json_uuid_path: JSONRoundtrip
    contextvars: Mapping[str, int]
    unpacking: UnpackingStressResult
    generator_control: TupleIntVariadicGeneratorIntIntOrStrOrNoneInt
    descriptor: TupleDescriptorSummaryIntStr
    metaclass_registry: TupleRegistryItemVariadicListStr
    builder: TupleBuilderStructuredStr
    container: TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt
    callable_object: CallablePayloadResults
    grouping: TupleListNormalizedRowDictListInt


class ExtendedResultsPart3(TypedDict):
    """Typed output keys from test_extended_inference_edge_cases_part3.

    Attributes:
        local_class (int): TODO.
            nested_defaultdict
            (TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic):
            TODO.
        partial_reduce (TupleListIntIntVariadic): TODO.
        runtime_protocol_update (None): TODO.
        runtime_protocol_callable (IntOrStrOrCallablePayloadStr | None): TODO.
        deep_attributes (TupleSupportsMetadataAndNameVariadicNodeMetadata): TODO.
        bytes_memoryview (TupleBytearrayMemoryviewBytesInt): TODO.
        map_filter_zip (ListTupleIntVariadic): TODO.
        composed_inner (DictInt): TODO.
        mutable_store (tuple[ListStr, TupleStrVariadic, set[str]]): TODO.
        literal_dispatch (str): TODO.
        boolean_narrowing (IntOrNone): TODO.
        extended_result (TupleExtendedResultListIntStrIntBool): TODO.
        decorated_pipeline (str | ListValue[str]): TODO.
        singledispatch_int (DispatchOutcome[int]): TODO.
        singledispatch_str (DispatchOutcome[str]): TODO.
        singledispatch_default (DispatchOutcome[ListInt]): TODO.
        cached_recursive (TupleIntVariadic): TODO.
        async_result (TupleAsyncPayloadListInt): TODO.
        nested_defaultdict (TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic): TODO.

    """

    local_class: int
    nested_defaultdict: (
        TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic
    )
    partial_reduce: TupleListIntIntVariadic
    runtime_protocol_update: None
    runtime_protocol_callable: IntOrStrOrCallablePayloadStr | None
    deep_attributes: TupleSupportsMetadataAndNameVariadicNodeMetadata
    bytes_memoryview: TupleBytearrayMemoryviewBytesInt
    map_filter_zip: ListTupleIntVariadic
    composed_inner: DictInt
    mutable_store: tuple[ListStr, TupleStrVariadic, set[str]]
    literal_dispatch: str
    boolean_narrowing: IntOrNone
    extended_result: TupleExtendedResultListIntStrIntBool
    decorated_pipeline: str | ListValue[str]
    singledispatch_int: DispatchOutcome[int]
    singledispatch_str: DispatchOutcome[str]
    singledispatch_default: DispatchOutcome[ListInt]
    cached_recursive: TupleIntVariadic
    async_result: TupleAsyncPayloadListInt


class SupportsClassMethodAndInstanceMethodAndStaticMethod(Protocol):
    """Common interface of the nested class-method example."""

    @classmethod
    def class_method(cls) -> str:
        """Return the class name.

        Returns:
            str: TODO.

        """
        ...

    @staticmethod
    def static_method() -> str:
        """Return the static marker.

        Returns:
            str: TODO.

        """
        ...

    def instance_method(self) -> str:
        """Return the instance marker.

        Returns:
            str: TODO.

        """
        ...


class SupportsValue(Protocol):
    """An instance carrying a writable integer property."""

    @property
    def value(self) -> int:
        """Read the integer value.

        Returns:
            int: TODO.

        """
        ...

    @value.setter
    def value(self, val: int) -> None:
        """Write the integer value.

        Args:
            val (int): TODO.

        """
        ...


class SupportsMatrixMultiplicationAndData(Protocol):
    """An integer matrix supporting matrix multiplication.

    Attributes:
        data (ListListInt): TODO.

    """

    data: ListListInt

    def __matmul__(self, other: Self) -> Self:
        """Return the product of two matrices.

        Args:
            other (Self): TODO.

        Returns:
            Self: TODO.

        """
        ...


class SupportsInstance[**P, ValueT](Protocol):
    """Wrapper holding a precisely typed original instance.

    Attributes:
        instance (ValueT): TODO.

    """

    instance: ValueT

    def __init__(self, *args: P.args, **kwargs: P.kwargs) -> None:
        """Initialize a wrapped value.

        Args:
            args (P.args): TODO.
            kwargs (P.kwargs): TODO.

        """
        ...


class SupportsJoin(Protocol):
    """Subset of os.path whose join operation produces a string."""

    def join(self, path: str, *paths: str) -> str:
        """Join path components.

        Args:
            path (str): TODO.
            paths (str): TODO.

        Returns:
            str: TODO.

        """
        ...


class SupportsNameAndPath(Protocol):
    """Features of the os module returned by __import__('os.path').

    Attributes:
        path (SupportsJoin): TODO.
        __name__ (str): TODO.

    """

    __name__: str
    path: SupportsJoin


class SupportsStringConversion(Protocol):
    """Contract for values accepted by string conversion."""

    @override
    def __str__(self) -> str:
        """Convert the instance into its string representation.

        Returns:
            str: TODO.

        """
        ...


class SupportsCall(Protocol):
    """Invoke any unary callable without erasing its argument/return types."""

    def __call__[InputT, OutputT](
        self,
        func: CallableValueToResult[InputT, OutputT],
        arg: InputT,
    ) -> OutputT:
        """Apply a unary callable to its correctly typed argument.

        Args:
            func (CallableValueToResult[InputT, OutputT]): TODO.
            arg (InputT): TODO.

        Returns:
            OutputT: TODO.

        """
        ...


class SupportsCall2(Protocol):
    """Preserve a provided value or produce the default string."""

    @overload
    def __call__(self, value: None = None) -> str: ...

    @overload
    def __call__[ValueT](self, value: ValueT) -> StrOrValue[ValueT]: ...


class DescriptorSummary(TypedDict):
    """Cached descriptor value snapshot.

    Attributes:
        score (int): TODO.
        label (str): TODO.

    """

    score: int
    label: str


class SupportsApplyAndOffset(Protocol):
    """Protocol for local multiplier instances.

    Attributes:
        offset (int): TODO.

    """

    offset: int

    def apply(self, value: int) -> int:
        """Apply multiplier.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        ...


class SupportsCallAndFromValues(Protocol):
    """Protocol for local multiplier classes."""

    def __call__(self, offset: int = 0) -> SupportsApplyAndOffset:
        """Create a local multiplier.

        Args:
            offset (int): TODO.

        Returns:
            SupportsApplyAndOffset: TODO.

        """
        ...

    def from_values(self, values: SequenceInt) -> SupportsApplyAndOffset:
        """Create from values.

        Args:
            values (SequenceInt): TODO.

        Returns:
            SupportsApplyAndOffset: TODO.

        """
        ...


class SupportsComplexFunc(Protocol):
    """Call a three-argument conditional computation by keyword."""

    def __call__(self, x: int, y: int, z: int) -> int:
        """Compute the signed combination.

        Args:
            x (int): TODO.
            y (int): TODO.
            z (int): TODO.

        Returns:
            int: TODO.

        """
        ...


class SupportsNestedLoop(Protocol):
    """Call the nested aggregation with its named matrix input."""

    def __call__(self, matrix: SequenceSequenceInt) -> ListInt:
        """Aggregate the rows.

        Args:
            matrix (SequenceSequenceInt): TODO.

        Returns:
            ListInt: TODO.

        """
        ...


class SupportsIntegerDescriptor(Protocol):
    """Integer-valued data descriptor with mutable local storage.

    Attributes:
        _value (int): TODO.

    """

    _value: int

    def __get__[OwnerT](self, obj: OwnerT, objtype: type[OwnerT]) -> int:
        """Read the current integer.

        Args:
            obj (OwnerT): TODO.
            objtype (type[OwnerT]): TODO.

        Returns:
            int: TODO.

        """
        ...


class SupportsMethodCreate(Protocol):
    """Factory class exposing a static constructor."""

    @staticmethod
    def create(type_name: str) -> object | None:
        """Create a source-local product or return no product.

        Args:
            type_name (str): TODO.

        Returns:
            object | None: TODO.

        """
        ...


class SupportsInjectedMethod(Protocol):
    """Instance supporting a dynamically injected string method."""

    def new_method(self) -> str:
        """Return the new string method result.

        Returns:
            str: TODO.

        """
        ...


class SupportsCombinedMethod(Protocol):
    """Class instance exposing the combined inherited operation."""

    def combined_method(self) -> str:
        """Return the combined text result."""
        ...


class SupportsProtocolMethod(Protocol):
    """Class instance implementing the numeric protocol operation."""

    def protocol_method(self, x: int) -> int:
        """Double a supplied integer.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        ...


class SupportsSlottedFields(Protocol):
    """Class instance with two integer-valued slots.

    Attributes:
        x (int): TODO.
        y (int): TODO.

    """

    x: int
    y: int


class SupportsBuiltParts(Protocol):
    """Product exposing accumulated string parts.

    Attributes:
        parts (ListStr): TODO.

    """

    parts: ListStr


class SupportsBuilderMethods(Protocol):
    """Builder with a fluent append and product construction API."""

    def add_part(self, part: str) -> Self:
        """Append a part and return the builder.

        Args:
            part (str): TODO.

        Returns:
            Self: TODO.

        """
        ...

    def build(self) -> SupportsBuiltParts:
        """Build the accumulated product.

        Returns:
            SupportsBuiltParts: TODO.

        """
        ...


class SupportsHandle(Protocol):
    """Chain handler accepting a textual request."""

    def handle(self, request: str) -> StrOrNone:
        """Handle a request.

        Args:
            request (str): TODO.

        Returns:
            StrOrNone: TODO.

        """
        ...


class SupportsNotify(Protocol):
    """Observer subject capable of broadcasting messages."""

    def notify(self, message: str) -> None:
        """Notify observers.

        Args:
            message (str): TODO.

        """
        ...


class SupportsMethodUpdate(Protocol):
    """Observer capable of receiving textual updates."""

    def update(self, message: str) -> None:
        """Receive an update.

        Args:
            message (str): TODO.

        """
        ...


class SupportsMethodExecuteIntInt(Protocol):
    """Strategy returning an integer from two integers."""

    def execute(self, a: int, b: int) -> int:
        """Execute the strategy.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        ...


class SupportsCommandExecute(Protocol):
    """Command executing without a return value."""

    def execute(self) -> None:
        """Execute the command."""
        ...


class SupportsReceiverAction(Protocol):
    """Receiver returning a textual action result."""

    def action(self) -> str:
        """Perform the action.

        Returns:
            str: TODO.

        """
        ...


class TestCallsResult(TestCallsPart1, TestCallsPart2, TestCallsPart3):
    """All result fields of the call-inference suite."""


class ExtendedTestResult(
    ExtendedResultsPart1,
    ExtendedResultsPart2,
    ExtendedResultsPart3,
):
    """Complete extended inference results with field-specific types."""


@final
class Constants:
    """Immutable configuration and shared sentinel/context bindings.

    Attributes:
        threshold (Final[int]): TODO.
        max_value (Final[int]): TODO.
        min_length (Final[int]): TODO.
        extended_sentinel (Final[object]): TODO.
        extended_context (Final[ContextVar[DictBoolOrNone]]): TODO.

    """

    threshold: Final[int] = 5
    max_value: Final[int] = 10
    min_length: Final[int] = 3
    extended_sentinel: Final[object] = object()
    extended_context: Final[ContextVar[DictBoolOrNone]] = ContextVar(
        "extended_context",
        default=None,
    )


class SupportsUpdate:
    """Protocol for observer-like objects."""

    def update(self, message: str) -> None:
        """Receive an update message.

        Args:
            message (str): TODO.

        """
        _: str = message


class SupportsExecuteInt:
    """Protocol for integer strategies."""

    def execute(self, a: int, b: int) -> None:
        """Execute with two integer inputs.

        Args:
            a (int): TODO.
            b (int): TODO.

        """
        _: tuple[int, int] = (a, b)


class SupportsAction:
    """Protocol for receiver objects."""

    def action(self) -> None:
        """Perform the action."""


class SupportsAttributeInitializedByMeta(Protocol):
    """Expose the writable flag that metaclass construction injects.

    Attributes:
        initialized_by_meta (bool): TODO.

    """

    initialized_by_meta: bool


class SupportsInitializedByMeta:
    """Protocol for objects initialized by metaclass.

    Attributes:
        initialized_by_meta (bool | None): TODO.

    """

    initialized_by_meta: bool | None = None


class SupportsNewMethod:
    """Protocol for objects with new_method."""

    def new_method(self) -> None:
        """Return new method for testing."""


class SupportsVectorLike(Protocol):
    """Contract observed in the vector implementation.

    Attributes:
        x (int): TODO.
        y (int): TODO.

    """

    x: int
    y: int

    def __add__(self, other: SupportsVectorLike) -> SupportsVectorLike:
        """Add vector-like values.

        Args:
            other (SupportsVectorLike): TODO.

        Returns:
            SupportsVectorLike: TODO.

        """
        ...


class SupportsVector:
    """Protocol for vector-like objects.

    Attributes:
        x (None): TODO.
        y (None): TODO.

    """

    x: None = None
    y: None = None

    def __add__(self, other: SupportsVector) -> None:
        """Add vectors.

        Args:
            other (SupportsVector): TODO.

        """


class MetaClass(type):
    """Metaclass for testing type inference."""

    def __new__(
        mcs: TypeValue[MetaClass],
        name: str,
        bases: TupleTypeObjectVariadic,
        namespace: DictObject,
        **_kwargs: object,
    ) -> MetaClass:
        """Create a new class with ``meta_added``.

        Args:
            mcs (TypeValue[MetaClass]): TODO.
            name (str): TODO.
            bases (TupleTypeObjectVariadic): TODO.
            namespace (DictObject): TODO.
            _kwargs (object): TODO.

        Returns:
            MetaClass: TODO.

        """
        namespace["meta_added"] = True
        return super().__new__(mcs, name, bases, namespace)

    @override
    def __call__(
        cls,
        *args: object,
        **kwargs: object,
    ) -> SupportsAttributeInitializedByMeta:
        """Create instance with ``initialized_by_meta``.

        Args:
            args (object): TODO.
            kwargs (object): TODO.

        Returns:
            SupportsAttributeInitializedByMeta: TODO.

        """
        instance: SupportsAttributeInitializedByMeta = cast(
            typ="SupportsAttributeInitializedByMeta",
            val=super().__call__(*args, **kwargs),
        )
        initialized: SupportsAttributeInitializedByMeta = instance
        initialized.initialized_by_meta = True
        return initialized


class AbstractBase(ABC):
    """Abstract base class for testing type inference."""

    @abstractmethod
    def abstract_method(self, value: int) -> int:
        """Abstract method for testing.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """

    @classmethod
    @abstractmethod
    def class_method(cls) -> None:
        """Abstract class method for testing."""

    @staticmethod
    @abstractmethod
    def static_method() -> None:
        """Abstract static method for testing."""


class BaseClass:
    """Base class for testing type inference.

    Attributes:
        x (int): TODO.
        y (IntOrNone): TODO.

    """

    def __init__(self, x: int, y: IntOrNone = None) -> None:
        """Initialize base class.

        Args:
            x (int): TODO.
            y (IntOrNone): TODO.

        """
        self.x: int = x
        self.y: IntOrNone = y

    def base_method(self, a: int, b: int = 10) -> int:
        """Test base method.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a + b

    @property
    def base_property(self) -> int:
        """Base property getter.

        Returns:
            int: TODO.

        """
        return self.x

    @base_property.setter
    def base_property(self, value: int) -> None:
        """Set base property.

        Args:
            value (int): TODO.

        """
        self.x = value


class DerivedClass(BaseClass, AbstractBase):
    """Derived class for testing type inference.

    Attributes:
        z (int): TODO.

    """

    def __init__(self, x: int, y: IntOrNone = None, z: int = 0) -> None:
        """Initialize derived class.

        Args:
            x (int): TODO.
            y (IntOrNone): TODO.
            z (int): TODO.

        """
        super().__init__(x=x, y=y)
        self.z: int = z

    @override
    def abstract_method(self, value: int) -> int:
        """Implement abstract method.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        return value * 2

    @classmethod
    @override
    def class_method(cls) -> None:
        """Implement class method."""

    @staticmethod
    @override
    def static_method() -> None:
        """Implement static method."""

    def derived_method(self, a: int, b: int, c: int = 5, d: int = 10) -> int:
        """Test derived method.

        Args:
            a (int): TODO.
            b (int): TODO.
            c (int): TODO.
            d (int): TODO.

        Returns:
            int: TODO.

        """
        if a > b:
            return a - b
        if a < b:
            return b - a
        return c + d


class MetaDecoratedClass:
    """Class with metaclass for testing.

    Attributes:
        value (int): TODO.

    """

    def __init__(self, value: int) -> None:
        """Initialize meta decorated class.

        Args:
            value (int): TODO.

        """
        self.value: int = value


def decorator[**P](
    func: CallableParametersToInt[P],
) -> CallableParametersToInt[P]:
    """Multiply result by 2.

    Args:
        func (CallableParametersToInt[P]): TODO.

    Returns:
        CallableParametersToInt[P]: TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
        """Invoke the wrapped function with forwarded arguments.

        Args:
            args (P.args): TODO.
            kwargs (P.kwargs): TODO.

        Returns:
            int: TODO.

        """
        result: int = func(*args, **kwargs)
        return result * 2

    return wrapper


def decorator_with_args[**P](
    multiplier: int = 2,
) -> CallableValueToResult[
    CallableParametersToInt[P],
    CallableParametersToInt[P],
]:
    """Create decorator with configurable multiplier.

    Args:
        multiplier (int): TODO.

    Returns:
        CallableValueToResult[CallableParametersToInt[P],
            CallableParametersToInt[P]]: TODO.

    """

    def actual_decorator(
        func: CallableParametersToInt[P],
    ) -> CallableParametersToInt[P]:
        """Construct a decorator applying the chosen multiplier.

        Args:
            func (CallableParametersToInt[P]): TODO.

        Returns:
            CallableParametersToInt[P]: TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> int:
            """Invoke the wrapped function with forwarded arguments.

            Args:
                args (P.args): TODO.
                kwargs (P.kwargs): TODO.

            Returns:
                int: TODO.

            """
            result: int = func(*args, **kwargs)
            return result * multiplier

        return wrapper

    return actual_decorator


def decorator_with_class[**P, T](
    cls: CallableParametersToResult[P, T],
) -> type[SupportsInstance[P, T]]:
    """Wrap class in a proxy class.

    Returns:
        type[SupportsInstance[P, T]]: TODO.

    """

    class Wrapper:
        """Proxy wrapper created by a class decorator.

        Attributes:
            instance (T): TODO.

        """

        def __init__(self, *args: P.args, **kwargs: P.kwargs) -> None:
            """Initialize instance state from the supplied arguments.

            Args:
                args (P.args): TODO.
                kwargs (P.kwargs): TODO.

            """
            self.instance: T = cls(*args, **kwargs)

        def __getattr__(self, name: str) -> object:
            """Forward missing attribute lookups to the wrapped instance.

            Args:
                name (str): TODO.

            Returns:
                object: TODO.

            """
            return cast(typ="object", val=getattr(self.instance, name))

    return Wrapper


@decorator
def simple_function(x: int) -> int:
    """Test simple function.

    Args:
        x (int): TODO.

    Returns:
        int: TODO.

    """
    return x + 1


@decorator_with_args(multiplier=3)
def function_with_args(x: int, y: int = 5) -> int:
    """Test function with args.

    Args:
        x (int): TODO.
        y (int): TODO.

    Returns:
        int: TODO.

    """
    return x + y


@decorator_with_class
class DecoratedClass:
    """Class decorated with class decorator.

    Attributes:
        value (int): TODO.

    """

    def __init__(self, value: int) -> None:
        """Initialize decorated class.

        Args:
            value (int): TODO.

        """
        self.value: int = value

    def method(self) -> int:
        """Test method.

        Returns:
            int: TODO.

        """
        return self.value


@dataclass(init=False)
class DataClassExample:
    """Dataclass-like class for testing type inference.

    Attributes:
        x (IntOrNone): TODO.
        y (str): TODO.
        z (ListIntOrNone): TODO.

    """

    x: IntOrNone = None
    y: str = "default"
    z: ListIntOrNone = None

    def __init__(
        self,
        x: int,
        y: str = "default",
        z: ListIntOrNone = None,
    ) -> None:
        """Initialize dataclass-like example.

        Args:
            x (int): TODO.
            y (str): TODO.
            z (ListIntOrNone): TODO.

        """
        self.x = x
        self.y = y
        self.z = [] if z is None else z


class EnumClass(Enum):
    """Enum class for testing type inference."""

    VALUE_A = auto()
    VALUE_B = auto()
    VALUE_C = auto()


def function_without_hints(
    a: int,
    b: int,
    c: IntOrNone = None,
    d: int = 10,
    e: int = 20,
) -> int:
    """Test function without missing type hints.

    Args:
        a (int): TODO.
        b (int): TODO.
        c (IntOrNone): TODO.
        d (int): TODO.
        e (int): TODO.

    Returns:
        int: TODO.

    """
    resolved_c: int = a + b if c is None else c
    return resolved_c + d + e


def function_with_kwargs(a: int, b: int = 5, *args: int, **kwargs: int) -> int:
    """Test function with kwargs.

    Args:
        a (int): TODO.
        b (int): TODO.
        args (int): TODO.
        kwargs (int): TODO.

    Returns:
        int: TODO.

    """
    result: int = a + b
    value: int
    for value in args:
        result += value
    for value in kwargs.values():
        result += value
    return result


def function_with_args_kwargs(*args: int, **kwargs: int) -> int:
    """Test function with args and kwargs.

    Args:
        args (int): TODO.
        kwargs (int): TODO.

    Returns:
        int: TODO.

    """
    total: int = sum(args)
    value: int
    for value in kwargs.values():
        total += value
    return total


def nested_function(x: int, y: int, z: int) -> int:
    """Test nested function.

    Args:
        x (int): TODO.
        y (int): TODO.
        z (int): TODO.

    Returns:
        int: TODO.

    """

    def inner(a: int, b: int) -> int:
        """Inner function for testing.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """

        def deeper(c: int, d: int) -> int:
            """Deeper function for testing.

            Args:
                c (int): TODO.
                d (int): TODO.

            Returns:
                int: TODO.

            """
            return c * d

        return deeper(c=a, d=b) + a

    return inner(a=x, b=y) + z


def closure_function(x: int) -> CallableIntInt:
    """Test closure function.

    Args:
        x (int): TODO.

    Returns:
        CallableIntInt: TODO.

    """

    def inner(y: int) -> int:
        """Inner closure for testing.

        Args:
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x + y

    return inner


def function_with_slices[T](
    data: SequenceValue[T],
    start: int,
    end: int,
    step: IntOrNone = None,
) -> SequenceValue[T]:
    """Test function with slices.

    Args:
        data (SequenceValue[T]): TODO.
        start (int): TODO.
        end (int): TODO.
        step (IntOrNone): TODO.

    Returns:
        SequenceValue[T]: TODO.

    """
    if step is None:
        return data[start:end]
    return data[start:end:step]


def function_with_comprehensions(
    items: SequenceInt,
) -> TupleListIntDictIntIntGeneratorInt:
    """Test function with comprehensions.

    Args:
        items (SequenceInt): TODO.

    Returns:
        TupleListIntDictIntIntGeneratorInt: TODO.

    """
    squared: ListInt = [x**2 for x in items if x > 0]
    filtered: DictIntInt = {
        k: v for k, v in enumerate(iterable=items) if v % 2 == 0
    }
    generator: GeneratorInt = (x * 3 for x in items if x < Constants.max_value)
    return (squared, filtered, generator)


def function_with_lambdas(items: SequenceStr) -> TupleListStrVariadic:
    """Test function with lambdas.

    Args:
        items (SequenceStr): TODO.

    Returns:
        TupleListStrVariadic: TODO.

    """
    sorted_items: ListStr = sorted(items, key=lambda x: x.lower())
    mapped: ListStr = [x.upper() for x in items]
    filtered: ListStr = [x for x in items if len(x) > Constants.min_length]
    return (sorted_items, mapped, filtered)


def function_with_recursion(n: int) -> int:
    """Test function with recursion.

    Args:
        n (int): TODO.

    Returns:
        int: TODO.

    """
    if n <= 1:
        return 1
    return n * function_with_recursion(n=n - 1)


def function_with_try_except(value: str) -> int:
    """Test function with try except.

    Args:
        value (str): TODO.

    Returns:
        int: TODO.

    """
    try:
        result: int = int(value)
    except ValueError:
        result = 0
    except TypeError:
        result = -1
    else:
        result *= 2
    finally:
        pass
    return result


def function_with_context() -> bool:
    """Test function with context.

    Returns:
        bool: TODO.

    """
    f: IO[str]
    with NamedTemporaryFile(mode="w", delete=False) as f:
        _: int = f.write("test")
        temp_path: str = f.name
    Path(temp_path).unlink()
    return True


@contextmanager
def custom_context() -> Generator[str]:
    """Create custom context manager.

    Yields:
        str: TODO.

    """
    resource: str = acquire_resource()
    try:
        yield resource
    finally:
        release_resource(resource=resource)


def acquire_resource() -> str:
    """Acquire resource.

    Returns:
        str: TODO.

    """
    return "resource"


def release_resource(resource: str) -> None:
    """Release resource.

    Args:
        resource (str): TODO.

    """
    resource = resource * 3


def function_with_generators() -> ListInt:
    """Test function with generators.

    Returns:
        ListInt: TODO.

    """

    def generator() -> GeneratorInt:
        """Generate values.

        Yields:
            GeneratorInt: TODO.

        """
        yield from range(10)

    return list(generator())


def function_with_coroutines() -> CallableValueToResult[int, AwaitableInt]:
    """Test function with coroutines.

    Returns:
        CallableValueToResult[int, AwaitableInt]: TODO.

    """

    async def async_function(x: int) -> int:
        """Test async function.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        await sleep(delay=1)
        return x * 2

    return async_function


def function_with_class_methods() -> TypeSupportsClassMethods:
    """Test function with class methods.

    Returns:
        TypeSupportsClassMethods: TODO.

    """

    class InnerClass:
        """Inner class for testing."""

        @classmethod
        def class_method(cls) -> str:
            """Implement class method.

            Returns:
                str: TODO.

            """
            return cls.__name__

        @staticmethod
        def static_method() -> str:
            """Implement static method.

            Returns:
                str: TODO.

            """
            return "static"

        def instance_method(self) -> str:
            """Test instance method.

            Returns:
                str: TODO.

            """
            return "instance"

    return InnerClass


def function_with_property() -> TypeSupportsValue:
    """Test function with property.

    Returns:
        TypeSupportsValue: TODO.

    """

    class PropertyClass:
        """Test property class.

        Attributes:
            _value (int): TODO.

        """

        def __init__(self) -> None:
            """Initialize property class."""
            self._value: int = 0

        @property
        def value(self) -> int:
            """Get value property.

            Returns:
                int: TODO.

            """
            return self._value

        @value.setter
        def value(self, val: int) -> None:
            """Set value property.

            Args:
                val (int): TODO.

            """
            self._value = val

        @value.deleter
        def value(self) -> None:
            """Delete value property."""
            del self._value

    return PropertyClass


def function_with_descriptor() -> type[SupportsIntegerDescriptor]:
    """Test function with descriptor.

    Returns:
        type[SupportsIntegerDescriptor]: TODO.

    """

    class Descriptor:
        """Test descriptor class.

        Attributes:
            _value (int): TODO.

        """

        def __init__(self) -> None:
            """Initialize instance state from the supplied arguments."""
            self._value: int = 0

        def __get__[OwnerT](self, obj: OwnerT, objtype: type[OwnerT]) -> int:
            """Get descriptor value.

            Args:
                obj (OwnerT): TODO.
                objtype (type[OwnerT]): TODO.

            Returns:
                int: TODO.

            """
            return self._value

        def __set__(self, obj: object, value: int) -> None:
            """Set descriptor value.

            Args:
                obj (object): TODO.
                value (int): TODO.

            """
            self._value = value

        def __delete__(self, obj: object) -> None:
            """Delete descriptor value.

            Args:
                obj (object): TODO.

            """
            del self._value

    return Descriptor


def function_with_operator_overloading() -> CallableIntIntSupportsVector:
    """Test function with operator overloading.

    Returns:
        CallableIntIntSupportsVector: TODO.

    """

    class Vector:
        """Test vector class.

        Attributes:
            x (int): TODO.
            y (int): TODO.

        """

        def __init__(self, x: int, y: int) -> None:
            """Initialize vector.

            Args:
                x (int): TODO.
                y (int): TODO.

            """
            self.x: int = x
            self.y: int = y

        def __add__(self, other: SupportsVectorLike) -> Vector:
            """Add vectors.

            Args:
                other (SupportsVectorLike): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x + other.x, y=self.y + other.y)

        def __sub__(self, other: Vector) -> Vector:
            """Subtract vectors.

            Args:
                other (Vector): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x - other.x, y=self.y - other.y)

        def __mul__(self, scalar: int) -> Vector:
            """Multiply vector by scalar.

            Args:
                scalar (int): TODO.

            Returns:
                Vector: TODO.

            """
            return Vector(x=self.x * scalar, y=self.y * scalar)

        @override
        def __eq__(self, other: object) -> bool:
            """Check vector equality.

            Args:
                other (object): TODO.

            Returns:
                bool: TODO.

            """
            if not isinstance(other, Vector):
                return False
            return self.x == other.x and self.y == other.y

        @override
        def __hash__(self) -> int:
            """Return hash of vector.

            Returns:
                int: TODO.

            """
            return hash((self.x, self.y))

        def __lt__(self, other: Vector) -> bool:
            """Check if vector is less than other.

            Args:
                other (Vector): TODO.

            Returns:
                bool: TODO.

            """
            return self.x < other.x

        @override
        def __repr__(self) -> str:
            """Return vector representation.

            Returns:
                str: TODO.

            """
            return f"Vector({self.x}, {self.y})"

    return Vector


def function_with_metaclass_usage() -> object:
    """Test function with metaclass usage.

    Returns:
        object: TODO.

    """

    class MetaInstance:
        """Test meta instance class."""

    return MetaInstance()


def function_with_multiple_inheritance() -> type[SupportsCombinedMethod]:
    """Test function with multiple inheritance.

    Returns:
        type[SupportsCombinedMethod]: TODO.

    """

    class MixinA:
        """Test mixin A class."""

        def method_a(self) -> str:
            """Test method A.

            Returns:
                str: TODO.

            """
            return "A"

    class MixinB:
        """Test mixin B class."""

        def method_b(self) -> str:
            """Test method B.

            Returns:
                str: TODO.

            """
            return "B"

    class Combined(MixinA, MixinB):
        """Test combined class."""

        def combined_method(self) -> str:
            """Test combined method.

            Returns:
                str: TODO.

            """
            return self.method_a() + self.method_b()

    return Combined


def function_with_abstract_methods() -> TypeAbstractBase:
    """Test function with abstract methods.

    Returns:
        TypeAbstractBase: TODO.

    """

    class AbstractImplementation(AbstractBase):
        """Test abstract implementation class."""

        @override
        def abstract_method(self, value: int) -> int:
            """Test abstract method.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.

            """
            return value + 10

        @classmethod
        @override
        def class_method(cls) -> None:
            """Implement class method."""

        @staticmethod
        @override
        def static_method() -> None:
            """Implement static method."""

    return AbstractImplementation


def function_with_protocol() -> type[SupportsProtocolMethod]:
    """Test function with protocol.

    Returns:
        type[SupportsProtocolMethod]: TODO.

    """

    class ProtocolImplementation:
        """Test protocol implementation class."""

        def protocol_method(self, x: int) -> int:
            """Test protocol method.

            Args:
                x (int): TODO.

            Returns:
                int: TODO.

            """
            return x * 2

    return ProtocolImplementation


def function_with_generic_types() -> TupleIntVariadicStr:
    """Test function with generic types.

    Returns:
        TupleIntVariadicStr: TODO.

    """

    def generic_function[ValueT](
        container: Sequence[ValueT] | Mapping[str, ValueT],
    ) -> ValueT:
        """Test generic function.

        Args:
            container (Sequence[ValueT] | Mapping[str, ValueT]): TODO.

        Returns:
            ValueT: TODO.

        """
        if isinstance(container, Mapping):
            return next(iter(container.values()))
        return container[0]

    result1: int = generic_function(container=[1, 2, 3])
    result2: int = generic_function(container={"a": 1, "b": 2})
    result3: str = generic_function(container="hello")
    return (int(result1), int(result2), str(object=result3))


def function_with_union_types() -> CallableIntOrStrToIntOrStr:
    """Test function with union types.

    Returns:
        CallableIntOrStrToIntOrStr: TODO.

    """

    def union_function(value: SupportsStringConversion) -> IntOrStr:
        """Test union function.

        Args:
            value (SupportsStringConversion): TODO.

        Returns:
            IntOrStr: TODO.

        """
        if isinstance(value, int):
            return value * 2
        if isinstance(value, str):
            return value.upper()
        return str(object=value)

    return union_function


def function_with_optional_types() -> SupportsCall2:
    """Test function with optional types.

    Returns:
        SupportsCall2: TODO.

    """

    @overload
    def optional_function(value: None = None) -> str: ...

    @overload
    def optional_function[ValueT](value: ValueT) -> StrOrValue[ValueT]: ...

    def optional_function[ValueT](
        value: ValueT | None = None,
    ) -> StrOrValue[ValueT]:
        """Test optional function.

        Args:
            value (ValueT | None): TODO.

        Returns:
            StrOrValue[ValueT]: TODO.

        """
        if value is None:
            return "default"
        return value

    return optional_function


def function_with_callable() -> SupportsCall:
    """Test function with callable.

    Returns:
        SupportsCall: TODO.

    """

    def callable_function[InputT, OutputT](
        func: CallableValueToResult[InputT, OutputT],
        arg: InputT,
    ) -> OutputT:
        """Test callable function.

        Args:
            func (CallableValueToResult[InputT, OutputT]): TODO.
            arg (InputT): TODO.

        Returns:
            OutputT: TODO.

        """
        return func(arg)

    return callable_function


def function_with_tuple_unpacking() -> TupleIntVariadic:
    """Test function with tuple unpacking.

    Returns:
        TupleIntVariadic: TODO.

    """
    data: TupleIntVariadic = (1, 2, 3, 4, 5)
    a: int
    b: int
    rest: list[Literal[3, 4, 5]]
    a, b, *rest = data
    c: int
    d: int
    e: int
    c, d, e = rest
    return (a, b, c, d, e)


def function_with_dict_operations() -> TupleDictIntVariadic:
    """Test function with dict operations.

    Returns:
        TupleDictIntVariadic: TODO.

    """
    d1: DictInt = {"a": 1, "b": 2}
    d2: DictInt = {"c": 3, "d": 4}
    merged: DictInt = {**d1, **d2}
    filtered: DictInt = {k: v for k, v in merged.items() if v > 1}
    return (merged, filtered)


def function_with_set_operations() -> TupleSetIntVariadic:
    """Test function with set operations.

    Returns:
        TupleSetIntVariadic: TODO.

    """
    s1: SetInt = {1, 2, 3, 4}
    s2: SetInt = {3, 4, 5, 6}
    union: SetInt = s1 | s2
    intersection: SetInt = s1 & s2
    difference: SetInt = s1 - s2
    return (union, intersection, difference)


def function_with_bitwise_operations() -> TupleIntVariadic:
    """Test function with bitwise operations.

    Returns:
        TupleIntVariadic: TODO.

    """
    a: int = 10
    b: int = 12
    and_result: int = a & b
    or_result: int = a | b
    xor_result: int = a ^ b
    not_result: int = ~a
    shift_left: int = a << 2
    shift_right: int = a >> 2
    return (
        and_result,
        or_result,
        xor_result,
        not_result,
        shift_left,
        shift_right,
    )


def function_with_augmented_assignment() -> int:
    """Test function with augmented assignment.

    Returns:
        int: TODO.

    """
    x: int = 10
    x += 5
    x -= 3
    x *= 2
    x = int(x / 4)
    x //= 2
    x %= 3
    x **= 2
    x &= 15
    x |= 8
    x ^= 5
    x <<= 1
    x >>= 1
    return x


def function_with_ternary() -> TupleIntVariadic:
    """Test function with ternary.

    Returns:
        TupleIntVariadic: TODO.

    """
    x: int = 10
    y: int = 20
    max_val: int = max(y, x)
    min_val: int = min(y, x)
    return (max_val, min_val)


def function_with_chained_comparisons() -> TupleBoolVariadic:
    """Test function with chained comparisons.

    Returns:
        TupleBoolVariadic: TODO.

    """
    x: int = Constants.threshold
    result1: bool = 1 < x < Constants.max_value
    result2: bool = Constants.max_value > x > 0
    result3: bool = x == Constants.threshold or x != Constants.max_value
    return (result1, result2, result3)


def function_with_boolean_logic() -> TupleBoolVariadic:
    """Test function with boolean logic.

    Returns:
        TupleBoolVariadic: TODO.

    """
    a: bool = True
    b: bool = False
    c: bool = True
    result1: bool = a and b
    result2: bool = a or b
    result3: bool = not a
    result4: bool = (a and b) or c
    result5: bool = (a or b) and c
    return (result1, result2, result3, result4, result5)


def function_with_none_handling() -> TupleIntOrNoneVariadic:
    """Test function with none handling.

    Returns:
        TupleIntOrNoneVariadic: TODO.

    """

    def maybe_none(value: IntOrNone) -> IntOrNone:
        """Maybe none function for testing.

        Args:
            value (IntOrNone): TODO.

        Returns:
            IntOrNone: TODO.

        """
        if value is None:
            return None
        return value * 2

    result1: IntOrNone = maybe_none(value=5)
    result2: IntOrNone = maybe_none(value=None)
    return (result1, result2)


def function_with_ellipsis() -> CallableIntIntInt:
    """Test function with ellipsis.

    Returns:
        CallableIntIntInt: TODO.

    """

    def ellipsis_function(a: int, b: int) -> int:
        """Ellipsis function for testing.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a + b

    return ellipsis_function


def function_with_star_expressions() -> ListInt:
    """Test function with star expressions.

    Returns:
        ListInt: TODO.

    """
    data: ListInt = [1, 2, 3]
    return [*data, 4, 5]


def function_with_double_star_expressions() -> DictInt:
    """Test function with double star expressions.

    Returns:
        DictInt: TODO.

    """
    d1: DictInt = {"a": 1}
    d2: DictInt = {"b": 2}
    return {**d1, **d2, "c": 3}


def function_with_matrix_multiplication() -> TypeValue[
    SupportsMatrixMultiplicationAndData
]:
    """Test function with matrix multiplication.

    Returns:
        TypeValue[SupportsMatrixMultiplicationAndData]: TODO.

    """

    class Matrix:
        """Test matrix class.

        Attributes:
            data (ListListInt): TODO.

        """

        def __init__(self, data: ListListInt) -> None:
            """Initialize matrix with data.

            Args:
                data (ListListInt): TODO.

            """
            self.data: ListListInt = data

        def __matmul__(self, other: Matrix) -> Matrix:
            """Matrix multiplication operator.

            Args:
                other (Matrix): TODO.

            Returns:
                Matrix: TODO.

            """
            return Matrix(
                data=[
                    [
                        sum((a * b for a, b in zip(row, col, strict=False)))
                        for col in cast(
                            typ="Iterator[tuple[int, ...]]",
                            val=zip(*other.data, strict=False),
                        )
                    ]
                    for row in self.data
                ],
            )

    return Matrix


def function_with_async_await() -> Callable[[], AwaitableInt]:
    """Test function with async await.

    Returns:
        Callable[[], AwaitableInt]: TODO.

    """

    async def async_func() -> int:
        """Async function for testing.

        Returns:
            int: TODO.

        """
        await sleep(delay=0.1)
        return 42

    return async_func


def function_with_type_annotations_missing() -> CallableExamples:
    """Test formerly missing type annotations.

    Returns:
        CallableExamples: TODO.

    """

    def func1(x: int) -> int:
        """Func1 for testing.

        Args:
            x (int): TODO.

        Returns:
            int: TODO.

        """
        return x + 1

    def func2(x: int, y: int) -> int:
        """Func2 for testing.

        Args:
            x (int): TODO.
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x + y

    def func3(x: int, y: int = 10) -> int:
        """Func3 for testing.

        Args:
            x (int): TODO.
            y (int): TODO.

        Returns:
            int: TODO.

        """
        return x * y

    def func4(*args: int) -> int:
        """Func4 for testing.

        Args:
            args (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(args)

    def func5(**kwargs: int) -> int:
        """Func5 for testing.

        Args:
            kwargs (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(kwargs.values())

    def func6(*args: int, **kwargs: int) -> int:
        """Func6 for testing.

        Args:
            args (int): TODO.
            kwargs (int): TODO.

        Returns:
            int: TODO.

        """
        return sum(args) + sum(kwargs.values())

    return (func1, func2, func3, func4, func5, func6)


def function_with_complex_conditionals() -> SupportsComplexFunc:
    """Test function with complex conditionals.

    Returns:
        SupportsComplexFunc: TODO.

    """

    def complex_func(x: int, y: int, z: int) -> int:
        """Complex function for testing.

        Args:
            x (int): TODO.
            y (int): TODO.
            z (int): TODO.

        Returns:
            int: TODO.

        """
        x_sign: int = 1 if x > 0 else -1
        y_sign: int = 1 if y > 0 else -1
        z_sign: int = 1 if z > 0 else -1
        return x_sign * x + y_sign * y + z_sign * z

    return complex_func


def function_with_nested_loops() -> SupportsNestedLoop:
    """Test function with nested loops.

    Returns:
        SupportsNestedLoop: TODO.

    """

    def nested_loop_func(matrix: SequenceSequenceInt) -> ListInt:
        """Nested loop function for testing.

        Args:
            matrix (SequenceSequenceInt): TODO.

        Returns:
            ListInt: TODO.

        """
        result: ListInt = []
        row: SequenceInt
        for row in matrix:
            row_sum: int = 0
            element: int
            for element in row:
                row_sum += element
            result.append(row_sum)
        return result

    return nested_loop_func


def function_with_exception_chaining() -> CallableNone:
    """Test function with exception chaining.

    Returns:
        CallableNone: TODO.

    """

    def exception_chain_func() -> None:
        """Exception chain function for testing."""

        def raise_first_error() -> Never:
            """Raise the first error in an exception chain.

            Raises:
                ValueError: TODO.

            """
            msg: str = "First error"
            raise ValueError(msg)

        def raise_second_error(original_error: ValueError) -> Never:
            """Raise an exception linked to its original cause.

            Args:
                original_error (ValueError): TODO.

            Raises:
                TypeError: TODO.

            """
            msg: str = "Second error"
            raise TypeError(msg) from original_error

        try:
            raise_first_error()
        except ValueError as e:
            e: ValueError
            raise_second_error(original_error=e)

    return exception_chain_func


def function_with_custom_exceptions() -> CallableNone:
    """Test function with custom exceptions.

    Returns:
        CallableNone: TODO.

    """

    class CustomError(Exception):
        """Custom error for testing."""

    class AnotherCustomError(CustomError):
        """Another custom error for testing."""

    def raise_custom() -> Never:
        """Raise custom function for testing.

        Raises:
            AnotherCustomError: TODO.

        """
        msg: str = "Custom error occurred"
        raise AnotherCustomError(msg)

    return raise_custom


def function_with_weak_refs() -> ReferenceType[object]:
    """Test function with weak refs.

    Returns:
        ReferenceType[object]: TODO.

    """

    class RefClass:
        """Ref class for testing."""

    obj: RefClass = RefClass()
    return ref(obj)


def function_with_slots() -> type[SupportsSlottedFields]:
    """Test function with slots.

    Returns:
        type[SupportsSlottedFields]: TODO.

    """

    class SlottedClass:
        """Slotted class for testing.

        Attributes:
            x (int): TODO.
            y (int): TODO.
            __slots__ (ClassVar[TupleStrVariadic]): TODO.

        """

        __slots__: ClassVar[TupleStrVariadic] = ("x", "y")

        def __init__(self, x: int, y: int) -> None:
            """Initialize instance state from the supplied arguments.

            Args:
                x (int): TODO.
                y (int): TODO.

            """
            self.x: int = x
            self.y: int = y

    return SlottedClass


def function_with_class_decorator() -> type[SupportsInjectedMethod]:
    """Test function with class decorator.

    Returns:
        type[SupportsInjectedMethod]: TODO.

    """

    def add_method[T](cls: type[T]) -> type[T]:
        """Add method for testing.

        Returns:
            type[T]: TODO.

        """

        def new_method(self: DecoratedByClass) -> str:
            """Add new method.

            Returns:
                str: TODO.

            """
            _: DecoratedByClass = self
            return "added method"

        dynamic_cls: type[T] = cls
        type.__setattr__(dynamic_cls, "new_method", new_method)
        return cls

    @add_method
    class DecoratedByClass:
        """Test decorated by class."""

        if TYPE_CHECKING:

            def new_method(self) -> str:
                """Return the dynamically injected method text.

                Returns:
                    str: TODO.

                """
                ...

    return DecoratedByClass


def function_with_singleton() -> TypeObject:
    """Test function with singleton.

    Returns:
        TypeObject: TODO.

    """

    class Singleton:
        """Test singleton class.

        Attributes:
            _instance (ClassVar[Singleton | None]): TODO.

        """

        _instance: ClassVar[Singleton | None] = None

        def __new__(cls) -> Self:
            """Create singleton instance.

            Returns:
                Self: TODO.

            """
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cast(typ="Self", val=cls._instance)

    return Singleton


def function_with_factory() -> type[SupportsMethodCreate]:
    """Test function with factory.

    Returns:
        type[SupportsMethodCreate]: TODO.

    """

    class TypeA:
        """Type A for testing."""

    class TypeB:
        """Type B for testing."""

    class Factory:
        """Test factory class."""

        @staticmethod
        def create(type_name: str) -> TypeA | TypeB | None:
            """Create type for testing.

            Args:
                type_name (str): TODO.

            Returns:
                TypeA | TypeB | None: TODO.

            """
            if type_name == "a":
                return TypeA()
            if type_name == "b":
                return TypeB()
            return None

    return Factory


def function_with_builder() -> type[SupportsBuilderMethods]:
    """Test function with builder.

    Returns:
        type[SupportsBuilderMethods]: TODO.

    """

    class Product:
        """Product class for testing.

        Attributes:
            parts (ListStr): TODO.

        """

        def __init__(self, parts: SequenceStr) -> None:
            """Initialize product with parts.

            Args:
                parts (SequenceStr): TODO.

            """
            self.parts: ListStr = list(parts)

    class Builder:
        """Test builder class.

        Attributes:
            parts (ListStr): TODO.

        """

        def __init__(self) -> None:
            """Initialize instance state from the supplied arguments."""
            self.parts: ListStr = []

        def add_part(self, part: str) -> Self:
            """Append a part and return the builder.

            Args:
                part (str): TODO.

            Returns:
                Self: TODO.

            """
            self.parts.append(part)
            return self

        def build(self) -> Product:
            """Build a result from the currently accumulated parts.

            Returns:
                Product: TODO.

            """
            return Product(parts=self.parts)

    return Builder


def function_with_observer() -> ObserverClassPair:
    """Test function with observer.

    Returns:
        ObserverClassPair: TODO.

    """

    class Observer:
        """Test observer class."""

        def update(self, message: str) -> None:
            """Update observer with message.

            Args:
                message (str): TODO.

            """
            _: str = message

    class Subject:
        """Test subject class.

        Attributes:
            observers (ListValue[SupportsUpdate]): TODO.

        """

        def __init__(self) -> None:
            """Initialize subject."""
            self.observers: ListValue[SupportsUpdate] = []

        def attach(self, observer: SupportsUpdate) -> None:
            """Attach observer to subject.

            Args:
                observer (SupportsUpdate): TODO.

            """
            self.observers.append(observer)

        def notify(self, message: str) -> None:
            """Notify all observers with message.

            Args:
                message (str): TODO.

            """
            observer: SupportsUpdate
            for observer in self.observers:
                observer.update(message)

    return (Subject, Observer)


def function_with_strategy() -> StrategyClassPair:
    """Test function with strategy.

    Returns:
        StrategyClassPair: TODO.

    """

    class Strategy:
        """Test strategy class."""

        def execute(self, a: int, b: int) -> int:
            """Execute strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            _: tuple[int, int] = (a, b)
            return 0

    class AddStrategy(Strategy):
        """Test add strategy."""

        @override
        def execute(self, a: int, b: int) -> int:
            """Execute add strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            return a + b

    class MultiplyStrategy(Strategy):
        """Test multiply strategy."""

        @override
        def execute(self, a: int, b: int) -> int:
            """Execute multiply strategy.

            Args:
                a (int): TODO.
                b (int): TODO.

            Returns:
                int: TODO.

            """
            return a * b

    return (AddStrategy, MultiplyStrategy)


def function_with_command() -> CommandClassPair:
    """Test function with command.

    Returns:
        CommandClassPair: TODO.

    """

    class Command:
        """Test command class."""

        def execute(self) -> None:
            """Execute command."""

    class Receiver:
        """Test receiver class."""

        def action(self) -> str:
            """Perform action.

            Returns:
                str: TODO.

            """
            return "Action performed"

    class ConcreteCommand(Command):
        """Test concrete command.

        Attributes:
            receiver (SupportsAction): TODO.

        """

        def __init__(self, receiver: SupportsAction) -> None:
            """Initialize instance state from the supplied arguments.

            Args:
                receiver (SupportsAction): TODO.

            """
            self.receiver: SupportsAction = receiver

        @override
        def execute(self) -> None:
            """Execute the configured strategy."""
            self.receiver.action()

    return (ConcreteCommand, Receiver)


def function_with_chain_of_responsibility() -> type[SupportsHandle]:
    """Test function with chain of responsibility.

    Returns:
        type[SupportsHandle]: TODO.

    """

    class Handler:
        """Test handler class.

        Attributes:
            next (Handler | None): TODO.

        """

        def __init__(self) -> None:
            """Initialize handler."""
            self.next: Handler | None = None

        def set_next(self, handler: Handler) -> Handler:
            """Set next handler.

            Args:
                handler (Handler): TODO.

            Returns:
                Handler: TODO.

            """
            self.next = handler
            return handler

        def handle(self, request: str) -> StrOrNone:
            """Handle request.

            Args:
                request (str): TODO.

            Returns:
                StrOrNone: TODO.

            """
            if self.next is not None:
                return self.next.handle(request)
            return None

    return Handler


def function_with_decorator_stack() -> CallableStr:
    """Test function with decorator stack.

    Returns:
        CallableStr: TODO.

    """

    def decorator1[**P, R](
        func: CallableParametersToResult[P, R],
    ) -> CallableParametersToResult[P, R]:
        """Test decorator 1.

        Args:
            func (CallableParametersToResult[P, R]): TODO.

        Returns:
            CallableParametersToResult[P, R]: TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Wrap decorator 1.

            Args:
                args (P.args): TODO.
                kwargs (P.kwargs): TODO.

            Returns:
                R: TODO.

            """
            return func(*args, **kwargs)

        return wrapper

    def decorator2[**P, R](
        func: CallableParametersToResult[P, R],
    ) -> CallableParametersToResult[P, R]:
        """Test decorator 2.

        Args:
            func (CallableParametersToResult[P, R]): TODO.

        Returns:
            CallableParametersToResult[P, R]: TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """Wrap decorator 2.

            Args:
                args (P.args): TODO.
                kwargs (P.kwargs): TODO.

            Returns:
                R: TODO.

            """
            return func(*args, **kwargs)

        return wrapper

    @decorator1
    @decorator2
    def stacked_func() -> str:
        """Test stacked function.

        Returns:
            str: TODO.

        """
        return "stacked"

    return stacked_func


def function_with_partial() -> CallableIntInt:
    """Test function with partial.

    Returns:
        CallableIntInt: TODO.

    """

    def multiply(a: int, b: int) -> int:
        """Test multiply function.

        Args:
            a (int): TODO.
            b (int): TODO.

        Returns:
            int: TODO.

        """
        return a * b

    return partial(multiply, 2)


def function_with_reduce() -> int:
    """Test function with reduce.

    Returns:
        int: TODO.

    """
    numbers: ListInt = [1, 2, 3, 4, 5]
    return reduce(lambda x, y: x + y, numbers)


def function_with_groupby() -> DictListInt:
    """Test function with groupby.

    Returns:
        DictListInt: TODO.

    """
    data: ListValue[TupleStrInt] = [("a", 1), ("b", 2), ("a", 3), ("b", 4)]
    return {
        k: [v for _, v in g]
        for k, g in groupby(iterable=sorted(data), key=lambda x: x[0])
    }


def function_with_permutations_combinations() -> (
    TupleListTupleIntVariadicVariadic
):
    """Test function with permutations and combinations.

    Returns:
        TupleListTupleIntVariadicVariadic: TODO.

    """
    items: ListInt = [1, 2, 3]
    perms: ListTupleIntVariadic = list(permutations(iterable=items, r=2))
    combs: ListTupleIntVariadic = list(combinations(iterable=items, r=2))
    return (perms, combs)


def function_with_defaultdict() -> DefaultdictStrInt:
    """Test function with defaultdict.

    Returns:
        DefaultdictStrInt: TODO.

    """
    d: DefaultdictStrInt = defaultdict(int)
    d["a"] += 1
    d["b"] += 2
    return d


def function_with_counter() -> CounterInt:
    """Test function with counter.

    Returns:
        CounterInt: TODO.

    """
    return Counter([1, 2, 2, 3, 3, 3])


def function_with_deque() -> DequeInt:
    """Test function with deque.

    Returns:
        DequeInt: TODO.

    """
    d: DequeInt = deque(iterable=[1, 2, 3])
    d.append(4)
    d.appendleft(0)
    _ = d.pop()
    _ = d.popleft()
    return d


def function_with_ordereddict() -> OrderedDictStrInt:
    """Test function with ordereddict.

    Returns:
        OrderedDictStrInt: TODO.

    """
    return OrderedDict([("a", 1), ("b", 2), ("c", 3)])


def function_with_namedtuple() -> Point:
    """Test function with namedtuple.

    Returns:
        Point: TODO.

    """
    return Point(x=1, y=2)


class Point:
    """Test point.

    Attributes:
        x (int): TODO.
        y (int): TODO.

    """

    def __init__(self, x: int, y: int) -> None:
        """Initialize point.

        Args:
            x (int): TODO.
            y (int): TODO.

        """
        self.x: int = x
        self.y: int = y


def function_with_chain() -> ListInt:
    """Test function with chain.

    Returns:
        ListInt: TODO.

    """
    list1: ListInt = [1, 2, 3]
    list2: ListInt = [4, 5, 6]
    return list(chain(list1, list2))


def function_with_islice() -> ListInt:
    """Test function with islice.

    Returns:
        ListInt: TODO.

    """
    data: range = range(10)
    return list(islice(data, 2, 8, 2))


def function_with_takewhile_dropwhile() -> TupleListIntVariadic:
    """Test function with takewhile and dropwhile.

    Returns:
        TupleListIntVariadic: TODO.

    """
    data: ListInt = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    taken: ListInt = list(takewhile(lambda x: x < Constants.threshold, data))
    dropped: ListInt = list(dropwhile(lambda x: x < Constants.threshold, data))
    return (taken, dropped)


def function_with_zip_longest() -> ListTupleIntOrNoneStrOrNone:
    """Test function with zip longest.

    Returns:
        ListTupleIntOrNoneStrOrNone: TODO.

    """
    list1: ListInt = [1, 2, 3]
    list2: ListStr = ["a", "b"]
    return list(zip_longest(list1, list2))


def function_with_product() -> ListTupleIntStr:
    """Test function with product.

    Returns:
        ListTupleIntStr: TODO.

    """
    list1: ListInt = [1, 2]
    list2: ListStr = ["a", "b"]
    return list(product(list1, list2))


def function_with_compress() -> ListInt:
    """Test function with compress.

    Returns:
        ListInt: TODO.

    """
    data: ListInt = [1, 2, 3, 4, 5]
    selectors: ListValue[bool] = [True, False, True, False, True]
    return list(compress(data=data, selectors=selectors))


def function_with_accumulate() -> ListInt:
    """Test function with accumulate.

    Returns:
        ListInt: TODO.

    """
    data: ListInt = [1, 2, 3, 4, 5]
    return list(accumulate(iterable=data))


def function_with_conditional_output(
    value: int,
    mode: str,
) -> ListIntOrDictIntOrStrOrInt:
    """Test function with conditions, globals, and conditional output type.

    Args:
        value (int): TODO.
        mode (str): TODO.

    Returns:
        ListIntOrDictIntOrStrOrInt: TODO.

    """
    if value > Constants.threshold and mode == "list":
        return [value * 2 for _ in range(Constants.max_value)]
    if value < Constants.threshold and mode == "dict":
        return {str(object=i): i * value for i in range(Constants.min_length)}
    if value == Constants.threshold and mode == "str":
        return str(object=value) * Constants.max_value
    return value + Constants.max_value


def test_function_calls_part1() -> TestCallsPart1:
    """Test basic function calls with kwargs where possible.

    Returns:
        TestCallsPart1: TODO.

    """
    result1: int = function_without_hints(a=1, b=2)
    result2: int = function_without_hints(a=1, b=2, c=3, d=4, e=5)
    result3: int = function_with_kwargs(10, 20, 30, 40)
    result4: int = function_with_args_kwargs(1, 2, 3, 4, 5)
    result5: int = nested_function(x=1, y=2, z=3)
    result6: SequenceInt = function_with_slices(
        data=[1, 2, 3, 4, 5],
        start=1,
        end=4,
    )
    result7: SequenceInt = function_with_slices(
        data=[1, 2, 3, 4, 5],
        start=0,
        end=5,
        step=2,
    )
    result8: TupleListIntDictIntIntGeneratorInt = function_with_comprehensions(
        items=[1, 2, 3, 4, 5],
    )
    result9: TupleListStrVariadic = function_with_lambdas(
        items=["apple", "banana", "cherry"],
    )
    result10: int = function_with_recursion(n=5)
    result11: int = function_with_try_except(value="123")
    result12: int = function_with_try_except(value="abc")
    result13: ListInt = function_with_generators()
    result14: TypeSupportsClassMethods = function_with_class_methods()
    result15: TypeSupportsValue = function_with_property()
    result16: CallableIntIntSupportsVector = (
        function_with_operator_overloading()
    )
    result17: object = function_with_metaclass_usage()
    result18: type[SupportsCombinedMethod] = (
        function_with_multiple_inheritance()
    )
    result19: TypeAbstractBase = function_with_abstract_methods()
    result20: TupleIntVariadicStr = function_with_generic_types()
    result21: CallableIntOrStrToIntOrStr = function_with_union_types()
    result22: SupportsCall2 = function_with_optional_types()
    return {
        "result1": result1,
        "result2": result2,
        "result3": result3,
        "result4": result4,
        "result5": result5,
        "result6": result6,
        "result7": result7,
        "result8": result8,
        "result9": result9,
        "result10": result10,
        "result11": result11,
        "result12": result12,
        "result13": result13,
        "result14": result14,
        "result15": result15,
        "result16": result16,
        "result17": result17,
        "result18": result18,
        "result19": result19,
        "result20": result20,
        "result21": result21,
        "result22": result22,
    }


def test_function_calls_part2() -> TestCallsPart2:
    """Test intermediate function calls with kwargs where possible.

    Returns:
        TestCallsPart2: TODO.

    """
    result23: TupleIntVariadic = function_with_tuple_unpacking()
    result24: TupleDictIntVariadic = function_with_dict_operations()
    result25: TupleSetIntVariadic = function_with_set_operations()
    result26: TupleIntVariadic = function_with_bitwise_operations()
    result27: int = function_with_augmented_assignment()
    result28: TupleIntVariadic = function_with_ternary()
    result29: TupleBoolVariadic = function_with_chained_comparisons()
    result30: TupleBoolVariadic = function_with_boolean_logic()
    result31: TupleIntOrNoneVariadic = function_with_none_handling()
    result32: ListInt = function_with_star_expressions()
    result33: DictInt = function_with_double_star_expressions()
    result34: CallableExamples = function_with_type_annotations_missing()
    result35: int = function_with_complex_conditionals()(x=1, y=2, z=3)
    nested_loop: SupportsNestedLoop = function_with_nested_loops()
    result36: ListInt = nested_loop(matrix=[[1, 2], [3, 4], [5, 6]])
    result37: type[SupportsSlottedFields] = function_with_slots()
    result38: type[SupportsInjectedMethod] = function_with_class_decorator()
    result39: TypeObject = function_with_singleton()
    result40: type[SupportsMethodCreate] = function_with_factory()
    result41: type[SupportsBuilderMethods] = function_with_builder()
    result42: ObserverClassPair = function_with_observer()
    result43: StrategyClassPair = function_with_strategy()
    result44: CommandClassPair = function_with_command()
    return {
        "result23": result23,
        "result24": result24,
        "result25": result25,
        "result26": result26,
        "result27": result27,
        "result28": result28,
        "result29": result29,
        "result30": result30,
        "result31": result31,
        "result32": result32,
        "result33": result33,
        "result34": result34,
        "result35": result35,
        "result36": result36,
        "result37": result37,
        "result38": result38,
        "result39": result39,
        "result40": result40,
        "result41": result41,
        "result42": result42,
        "result43": result43,
        "result44": result44,
    }


def test_function_calls_part3() -> TestCallsPart3:
    """Test advanced function calls with kwargs where possible.

    Returns:
        TestCallsPart3: TODO.

    """
    result45: type[SupportsHandle] = function_with_chain_of_responsibility()
    result46: CallableStr = function_with_decorator_stack()
    result47: CallableIntInt = function_with_partial()
    result48: int = function_with_reduce()
    result49: DictListInt = function_with_groupby()
    result50: TupleListTupleIntVariadicVariadic = (
        function_with_permutations_combinations()
    )
    result51: DefaultdictStrInt = function_with_defaultdict()
    result52: CounterInt = function_with_counter()
    result53: DequeInt = function_with_deque()
    result54: OrderedDictStrInt = function_with_ordereddict()
    result55: Point = function_with_namedtuple()
    result56: ListInt = function_with_chain()
    result57: ListInt = function_with_islice()
    result58: TupleListIntVariadic = function_with_takewhile_dropwhile()
    result59: ListTupleIntOrNoneStrOrNone = function_with_zip_longest()
    result60: ListTupleIntStr = function_with_product()
    result61: ListInt = function_with_compress()
    result62: ListInt = function_with_accumulate()
    result63: ListIntOrDictIntOrStrOrInt = function_with_conditional_output(
        value=10,
        mode="list",
    )
    result64: ListIntOrDictIntOrStrOrInt = function_with_conditional_output(
        value=3,
        mode="dict",
    )
    result65: ListIntOrDictIntOrStrOrInt = function_with_conditional_output(
        value=5,
        mode="str",
    )
    result66: ListIntOrDictIntOrStrOrInt = function_with_conditional_output(
        value=7,
        mode="other",
    )
    return {
        "result45": result45,
        "result46": result46,
        "result47": result47,
        "result48": result48,
        "result49": result49,
        "result50": result50,
        "result51": result51,
        "result52": result52,
        "result53": result53,
        "result54": result54,
        "result55": result55,
        "result56": result56,
        "result57": result57,
        "result58": result58,
        "result59": result59,
        "result60": result60,
        "result61": result61,
        "result62": result62,
        "result63": result63,
        "result64": result64,
        "result65": result65,
        "result66": result66,
    }


def test_function_calls() -> TestCallsResult:
    """Test various function calls with kwargs where possible.

    Returns:
        TestCallsResult: TODO.

    """
    return {
        **test_function_calls_part1(),
        **test_function_calls_part2(),
        **test_function_calls_part3(),
    }


def test_class_instantiations() -> ClassInstantiationResults:
    """Test class instantiations with kwargs where possible.

    Returns:
        ClassInstantiationResults: TODO.

    """
    return {
        "obj1": BaseClass(x=10),
        "obj2": BaseClass(x=10, y=20),
        "obj3": DerivedClass(x=10, y=20, z=30),
        "obj4": MetaDecoratedClass(value=100),
        "obj5": DataClassExample(x=1, y="test"),
        "obj6": DecoratedClass(value=50),
    }


def test_other_operations() -> OtherOperationResults:
    """Test enum, closure, context, and vector operations.

    Returns:
        OtherOperationResults: TODO.

    """
    enum_val: EnumClass = EnumClass.VALUE_A
    closure: CallableIntInt = closure_function(x=10)
    closure_result: int = closure(5)
    resource: str
    with custom_context() as resource:
        context_result: str = resource
    vector: CallableIntIntSupportsVector = function_with_operator_overloading()
    vec: SupportsVectorLike = vector(1, 2)
    vec2: SupportsVectorLike = vector(3, 4)
    vec_sum: SupportsVectorLike = vec + vec2
    return {
        "enum_val": enum_val,
        "closure_result": closure_result,
        "context_result": context_result,
        "vec_sum": vec_sum,
    }


class SliceExampleResult:
    """Result for list and dictionary slice inference examples.

    Attributes:
        list_slice (ListInt): TODO.
        list_stride_slice (ListInt): TODO.
        dict_slice (DictInt): TODO.
        dict_key_slice (ListStr): TODO.
        dict_value_slice (ListInt): TODO.

    """

    def __init__(
        self,
        list_slice: ListInt,
        list_stride_slice: ListInt,
        dict_slice: DictInt,
        dict_key_slice: ListStr,
        dict_value_slice: ListInt,
    ) -> None:
        """Initialize slice example result.

        Args:
            list_slice (ListInt): TODO.
            list_stride_slice (ListInt): TODO.
            dict_slice (DictInt): TODO.
            dict_key_slice (ListStr): TODO.
            dict_value_slice (ListInt): TODO.

        """
        self.list_slice: ListInt = list_slice
        self.list_stride_slice: ListInt = list_stride_slice
        self.dict_slice: DictInt = dict_slice
        self.dict_key_slice: ListStr = dict_key_slice
        self.dict_value_slice: ListInt = dict_value_slice


class BuiltinMethodList(list[int]):
    """List subclass whose method names intentionally shadow builtins."""

    @override
    def append(self, value: int) -> None:
        """Append a doubled integer, unlike ``list.append`` semantics.

        Args:
            value (int): TODO.

        """
        super().append(value * 2)

    @override
    def count(self, value: int) -> int:
        """Return the normal list count plus one for disambiguation.

        Args:
            value (int): TODO.

        Returns:
            int: TODO.

        """
        return super().count(value) + 1


class SupportsIntMappingKeys(Protocol):
    """Mapping-like protocol with an integer item getter."""

    def keys(self) -> Iterable[str]:
        """Return iterable keys."""
        ...

    def __getitem__(self, key: str, /) -> int:
        """Read a mapped integer.

        Args:
            key (str): TODO.

        """
        ...


class BuiltinMethodDict(dict[str, int]):
    """Dict subclass with names shared by built-in dict methods."""

    @overload
    def get(self, key: str, default: None = None) -> int: ...

    @overload
    def get(self, key: str, default: int) -> int: ...

    @overload
    def get[DefaultT](
        self,
        key: str,
        default: DefaultT,
    ) -> ValueOrInt[DefaultT]: ...

    @override
    def get[DefaultT](
        self,
        key: str,
        default: DefaultT | None = None,
    ) -> ValueOrInt[DefaultT]:
        """Return a stored value or a narrowed integer default.

        Args:
            key (str): TODO.
            default (DefaultT | None): TODO.

        Returns:
            ValueOrInt[DefaultT]: TODO.

        """
        fallback: ValueOrInt[DefaultT] = -1 if default is None else default
        return super().get(key, fallback)

    @override
    def update(
        self,
        other: SupportsIntMappingKeys | Iterable[TupleStrInt] = (),
        *values: int,
        **kwargs: int,
    ) -> None:
        """Update values while multiplying every incoming integer.

        Args:
            other (SupportsIntMappingKeys | Iterable[TupleStrInt]): TODO.
            values (int): TODO.
            kwargs (int): TODO.

        """
        incoming: DictInt = dict(other)
        index: int
        value: int
        for index, value in enumerate(iterable=values):
            incoming[str(object=index)] = value
        incoming.update(kwargs)
        multiplied: DictInt = {
            key: value * 10 for key, value in incoming.items()
        }
        super().update(multiplied)


class CustomAddSet(set[int]):
    """Set subclass with the same method name as a custom class below."""

    @override
    def add(self, element: int) -> None:
        """Add a shifted element.

        Args:
            element (int): TODO.

        """
        super().add(element + 100)


class CustomAdder:
    """Plain custom class with ``add`` sharing a name with ``set.add``.

    Attributes:
        seed (int): TODO.

    """

    def __init__(self, seed: int) -> None:
        """Initialize custom adder.

        Args:
            seed (int): TODO.

        """
        self.seed: int = seed

    def add(self, element: int) -> int:
        """Return an arithmetic result instead of mutating a set.

        Args:
            element (int): TODO.

        Returns:
            int: TODO.

        """
        return self.seed + element


class ImportExampleResult:
    """Result for importlib and ``__import__`` inference examples.

    Attributes:
        importlib_module_name (str): TODO.
        dunder_module_name (str): TODO.
        imported_join_result (str): TODO.

    """

    def __init__(
        self,
        importlib_module_name: str,
        dunder_module_name: str,
        imported_join_result: str,
    ) -> None:
        """Initialize import example result.

        Args:
            importlib_module_name (str): TODO.
            dunder_module_name (str): TODO.
            imported_join_result (str): TODO.

        """
        self.importlib_module_name: str = importlib_module_name
        self.dunder_module_name: str = dunder_module_name
        self.imported_join_result: str = imported_join_result


class RedefinitionResult:
    """Result for variable type redefinition examples.

    Attributes:
        first_type_value (int): TODO.
        second_type_value (str): TODO.
        third_type_value (ListInt): TODO.
        union_final_value (DictInt): TODO.

    """

    def __init__(
        self,
        first_type_value: int,
        second_type_value: str,
        third_type_value: ListInt,
        union_final_value: DictInt,
    ) -> None:
        """Initialize redefinition result.

        Args:
            first_type_value (int): TODO.
            second_type_value (str): TODO.
            third_type_value (ListInt): TODO.
            union_final_value (DictInt): TODO.

        """
        self.first_type_value: int = first_type_value
        self.second_type_value: str = second_type_value
        self.third_type_value: ListInt = third_type_value
        self.union_final_value: DictInt = union_final_value


class ScopeResolutionResult:
    """Result for same names in nested, class, and module scopes.

    Attributes:
        module_value (str): TODO.
        outer_value (int): TODO.
        inner_value (ListInt): TODO.
        class_value (str): TODO.
        method_and_nested_results (ListFloatOrStr): TODO.

    """

    def __init__(
        self,
        module_value: str,
        outer_value: int,
        inner_value: ListInt,
        class_value: str,
        method_and_nested_results: ListFloatOrStr,
    ) -> None:
        """Initialize scope resolution result.

        Args:
            module_value (str): TODO.
            outer_value (int): TODO.
            inner_value (ListInt): TODO.
            class_value (str): TODO.
            method_and_nested_results (ListFloatOrStr): TODO.

        """
        self.module_value: str = module_value
        self.outer_value: int = outer_value
        self.inner_value: ListInt = inner_value
        self.class_value: str = class_value
        self.method_and_nested_results: ListFloatOrStr = (
            method_and_nested_results
        )


def duplicate_scope_name(value: str) -> str:
    """Module-scope function intentionally reused in inner scopes.

    Args:
        value (str): TODO.

    Returns:
        str: TODO.

    """
    return f"module:{value}"


def function_with_list_and_dict_slices() -> SliceExampleResult:
    """Assign variables from slices of lists and dictionary views.

    Returns:
        SliceExampleResult: TODO.

    """
    numbers: ListInt = [10, 20, 30, 40, 50, 60]
    mapping: DictInt = {"alpha": 1, "beta": 2, "gamma": 3, "delta": 4}
    list_slice: ListInt = numbers[1:4]
    list_stride_slice: ListInt = numbers[::2]
    dict_slice: DictInt = dict(islice(mapping.items(), 1, 3))
    dict_key_slice: ListStr = list(mapping.keys())[1:]
    dict_value_slice: ListInt = list(mapping.values())[:3]
    return SliceExampleResult(
        list_slice=list_slice,
        list_stride_slice=list_stride_slice,
        dict_slice=dict_slice,
        dict_key_slice=dict_key_slice,
        dict_value_slice=dict_value_slice,
    )


def function_with_builtin_name_collisions() -> (
    TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt
):
    """Disambiguate builtin method names from custom method names.

    Returns:
        TupleBuiltinMethodListBuiltinMethodDictCustomAddSetInt: TODO.

    """
    custom_list: BuiltinMethodList = BuiltinMethodList([1, 2, 2])
    builtin_list: ListInt = [1, 2, 2]
    custom_list.append(value=3)
    builtin_list.append(3)
    custom_count: int = custom_list.count(value=2)
    builtin_count: int = builtin_list.count(2)
    custom_dict: BuiltinMethodDict = BuiltinMethodDict({"a": 1})
    builtin_dict: DictInt = {"a": 1}
    custom_dict.update({"b": 2}, 3)
    builtin_dict.update({"b": 2})
    custom_set: CustomAddSet = CustomAddSet({1, 2})
    builtin_set: SetInt = {1, 2}
    custom_set.add(element=5)
    builtin_set.add(5)
    adder: CustomAdder = CustomAdder(seed=40)
    adder_result: int = adder.add(element=2)
    collision_score: int = custom_count + builtin_count + adder_result
    return (custom_list, custom_dict, custom_set, collision_score)


def function_with_importlib_and_dunder_import() -> ImportExampleResult:
    """Use both importlib and ``__import__`` in resolvable examples.

    Returns:
        ImportExampleResult: TODO.

    """
    pathlib_module: ModuleType = import_module(name="pathlib")
    os_path_module: SupportsNameAndPath = cast(
        typ="SupportsNameAndPath",
        val=__import__(name="os.path"),
    )
    imported_join_result: str = os_path_module.path.join("a", "b")
    return ImportExampleResult(
        importlib_module_name=pathlib_module.__name__,
        dunder_module_name=os_path_module.__name__,
        imported_join_result=imported_join_result,
    )


def function_with_variable_type_redefinition() -> RedefinitionResult:
    """Redefine variable types in a deliberate linear flow.

    Returns:
        RedefinitionResult: TODO.

    """
    evolving_value: IntOrStr | ListInt | DictInt | None = None
    evolving_value = 10
    first_type_value: int = evolving_value
    evolving_value = "ten"
    second_type_value: str = evolving_value
    evolving_value = [1, 2, 3]
    third_type_value: ListInt = evolving_value
    evolving_value = {"ten": 10}
    union_final_value: DictInt = evolving_value
    return RedefinitionResult(
        first_type_value=first_type_value,
        second_type_value=second_type_value,
        third_type_value=third_type_value,
        union_final_value=union_final_value,
    )


def function_with_scope_resolution() -> ScopeResolutionResult:
    """Use identical names in module, function, nested, and class scopes.

    Returns:
        ScopeResolutionResult: TODO.

    """
    duplicated_name: int = 7

    def duplicate_scope_name(value: int) -> str:
        """Inner function that shadows the module-level function.

        Args:
            value (int): TODO.

        Returns:
            str: TODO.

        """
        duplicated_name: ListInt = [value, value + 1]

        def deepest() -> ListInt:
            """Return the innermost variable with the reused name.

            Returns:
                ListInt: TODO.

            """
            return duplicated_name

        return f"inner:{sum(deepest())}"

    class DuplicateScopeNameClass:
        """Class with same conceptual name family as outer symbols.

        Attributes:
            duplicated_name (str): TODO.

        """

        duplicated_name: str = "class"

        def method(self) -> float:
            """Return a method-local value with a reused variable name.

            Returns:
                float: TODO.

            """
            return 3.5

    instance: DuplicateScopeNameClass = DuplicateScopeNameClass()
    nested_function_result: str = duplicate_scope_name(value=duplicated_name)
    module_value: str = cast(
        typ="Callable[[str], str]",
        val=globals()["duplicate_scope_name"],
    )(
        "root",
    )
    return ScopeResolutionResult(
        module_value=module_value,
        outer_value=duplicated_name,
        inner_value=[duplicated_name, duplicated_name + 1],
        class_value=instance.duplicated_name,
        method_and_nested_results=[instance.method(), nested_function_result],
    )


def function_with_positional_and_keyword_only(
    pos_only: int,
    /,
    normal: int,
    *,
    kw_only: int,
) -> int:
    """Test function with positional-only and keyword-only arguments.

    Args:
        pos_only (int): TODO.
        normal (int): TODO.
        kw_only (int): TODO.

    Returns:
        int: TODO.

    """
    return pos_only + normal + kw_only


def test_new_inference_edge_cases() -> NewInferenceResults:
    """Run extra tests for slices, builtins, imports, and scoping.

    Returns:
        NewInferenceResults: TODO.

    """
    return {
        "slices": function_with_list_and_dict_slices(),
        "builtin_name_collisions": function_with_builtin_name_collisions(),
        "imports": function_with_importlib_and_dunder_import(),
        "redefinitions": function_with_variable_type_redefinition(),
        "scope_resolution": function_with_scope_resolution(),
        "positional_and_keyword_only": [
            function_with_positional_and_keyword_only(1, normal=2, kw_only=3),
        ],
    }


class ExtendedResult[PayloadT]:
    """Tiny tuple-like result container intentionally left untyped.

    Attributes:
        name (str): TODO.
        payload (PayloadT): TODO.
        metadata (DictBool): TODO.

    """

    def __init__(
        self,
        name: str,
        payload: PayloadT,
        metadata: DictBoolOrNone = None,
    ) -> None:
        """Store a name, payload, and metadata mapping.

        Args:
            name (str): TODO.
            payload (PayloadT): TODO.
            metadata (DictBoolOrNone): TODO.

        """
        self.name: str = name
        self.payload: PayloadT = payload
        self.metadata: DictBool = {} if metadata is None else metadata

    def __iter__(self) -> Iterator[StrOrValueOrDictBool[PayloadT]]:
        """Iterate over stored fields.

        Yields:
            StrOrValueOrDictBool[PayloadT]: TODO.

        """
        yield self.name
        yield self.payload
        yield self.metadata

    def __len__(self) -> int:
        """Return tuple-like field count.

        Returns:
            int: TODO.

        """
        return 3

    @overload
    def __getitem__(self, index: Literal[0, "name"]) -> str: ...

    @overload
    def __getitem__(self, index: Literal[1, "payload"]) -> PayloadT: ...

    @overload
    def __getitem__(self, index: Literal[2, "metadata"]) -> DictBool: ...

    @overload
    def __getitem__(
        self,
        index: IntOrStr,
    ) -> StrOrValueOrDictBool[PayloadT]: ...

    def __getitem__(
        self,
        index: IntOrStr,
    ) -> StrOrValueOrDictBool[PayloadT]:
        """Return one field by index or name.

        Args:
            index (IntOrStr): TODO.

        Returns:
            StrOrValueOrDictBool[PayloadT]: TODO.

        Raises:
            IndexError: TODO.

        """
        if index in {0, "name"}:
            return self.name
        if index in {1, "payload"}:
            return self.payload
        metadata_indexes: set[IntOrStr] = {2, "metadata"}
        if index in metadata_indexes:
            return self.metadata
        raise IndexError(index)


class ExtendedDataclassStress:
    """Dataclass-like class with factory-style defaults.

    Attributes:
        name (str): TODO.
        values (ListInt): TODO.
        lookup (DictInt): TODO.
        flags (SetBool): TODO.
        normalized (TupleValueVariadic[TupleStrInt]): TODO.

    """

    def __init__(
        self,
        name: str = "anonymous",
        values: ListIntOrNone = None,
        lookup: DictInt | None = None,
        flags: SetBool | None = None,
    ) -> None:
        """Initialize values without leaking mutable defaults.

        Args:
            name (str): TODO.
            values (ListIntOrNone): TODO.
            lookup (DictInt | None): TODO.
            flags (SetBool | None): TODO.

        """
        self.name: str = name
        self.values: ListInt = [] if values is None else values
        self.lookup: DictInt = {} if lookup is None else lookup
        self.flags: SetBool = set() if flags is None else flags
        _ = self.lookup.setdefault(self.name, len(self.values))
        self.flags.add(self.name in self.lookup)
        self.normalized: TupleValueVariadic[TupleStrInt] = tuple(
            sorted(self.lookup.items()),
        )


class DescriptorWithOwnerCache[ValueT]:
    """Descriptor using WeakKeyDictionary to stress descriptor inference.

    Attributes:
        default (ValueT): TODO.
        storage (WeakKeyDictionary[DescriptorStressOwner, ValueT]): TODO.
        owner (type[DescriptorStressOwner] | None): TODO.
        name (str): TODO.

    """

    def __init__(self, default: ValueT) -> None:
        """Initialize descriptor storage.

        Args:
            default (ValueT): TODO.

        """
        self.default: ValueT = default
        self.storage: WeakKeyDictionary[DescriptorStressOwner, ValueT] = (
            WeakKeyDictionary()
        )
        self.owner: type[DescriptorStressOwner] | None = None
        self.name: str = ""

    def __set_name__(
        self,
        owner: type[DescriptorStressOwner],
        name: str,
    ) -> None:
        """Store the owner/name pair.

        Args:
            owner (type[DescriptorStressOwner]): TODO.
            name (str): TODO.

        """
        self.owner = owner
        self.name = name

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[DescriptorStressOwner] | None = None,
    ) -> Self: ...

    @overload
    def __get__(
        self,
        instance: DescriptorStressOwner,
        owner: type[DescriptorStressOwner] | None = None,
    ) -> ValueT: ...

    def __get__(
        self,
        instance: DescriptorStressOwner | None,
        owner: type[DescriptorStressOwner] | None = None,
    ) -> ValueT | Self:
        """Return descriptor or stored instance value.

        Args:
            instance (DescriptorStressOwner | None): TODO.
            owner (type[DescriptorStressOwner] | None): TODO.

        Returns:
            ValueT | Self: TODO.

        """
        if instance is None:
            return self
        return self.storage.get(instance, self.default)

    def __set__(self, instance: DescriptorStressOwner, value: ValueT) -> None:
        """Set a value in weak storage.

        Args:
            instance (DescriptorStressOwner): TODO.
            value (ValueT): TODO.

        """
        self.storage[instance] = value

    def __delete__(self, instance: DescriptorStressOwner) -> None:
        """Delete value if present.

        Args:
            instance (DescriptorStressOwner): TODO.

        """
        with suppress(KeyError):
            del self.storage[instance]


class DescriptorStressOwner:
    """Owner class for descriptor stress.

    Attributes:
        score (DescriptorWithOwnerCacheInt): TODO.
        label (DescriptorWithOwnerCache[str]): TODO.

    """

    score: DescriptorWithOwnerCacheInt = DescriptorWithOwnerCache(default=0)
    label: DescriptorWithOwnerCache[str] = DescriptorWithOwnerCache(
        default="unset",
    )

    def __init__(self, score: int, label: str) -> None:
        """Initialize descriptor-backed fields.

        Args:
            score (int): TODO.
            label (str): TODO.

        """
        self.score = score
        self.label = label

    @cached_property
    def summary(self) -> DescriptorSummary:
        """Return cached mixed summary.

        Returns:
            DescriptorSummary: TODO.

        """
        return {"score": self.score, "label": self.label}


class RegistryMeta(type):
    """Metaclass that registers subclasses and injects attributes.

    Attributes:
        registry (ClassVar[DictRegistryMeta | None]): TODO.

    """

    registry: ClassVar[DictRegistryMeta | None] = None

    def __new__(
        mcls: TypeValue[RegistryMeta],
        name: str,
        bases: TupleTypeObjectVariadic,
        namespace: DictObject,
        **_kwargs: object,
    ) -> RegistryMeta:
        """Create class and register it by lower-case name.

        Args:
            mcls (TypeValue[RegistryMeta]): TODO.
            name (str): TODO.
            bases (TupleTypeObjectVariadic): TODO.
            namespace (DictObject): TODO.
            _kwargs (object): TODO.

        Returns:
            RegistryMeta: TODO.

        """
        _ = namespace.setdefault("created_by_registry_meta", True)
        cls: RegistryMeta = super().__new__(mcls, name, bases, namespace)
        if mcls.registry is None:
            mcls.registry = {}
        if not name.startswith("Abstract"):
            mcls.registry[name.lower()] = cls
        return cls

    @overload
    def __call__[T: RegistryBase](
        cls: type[T],
        *args: object,
        **_kwargs: object,
    ) -> T: ...

    @overload
    def __call__(
        cls,
        *args: object,
        **_kwargs: object,
    ) -> RegistryBase: ...

    @override
    def __call__(
        cls,
        *args: object,
        **_kwargs: object,
    ) -> RegistryBase:
        """Create instance and mark it.

        Args:
            args (object): TODO.
            _kwargs (object): TODO.

        Returns:
            RegistryBase: TODO.

        """
        instance: RegistryBase = cast(
            typ="RegistryBase",
            val=super().__call__(*args, **_kwargs),
        )
        instance.registry_key = cls.__name__.lower()
        return instance


class RegistryBase(metaclass=RegistryMeta):
    """Base class using RegistryMeta.

    Attributes:
        registry_key (str): TODO.

    """

    registry_key: str = ""

    def clone(self, **overrides: RegistryField) -> Self:
        """Clone using the current instance dictionary.

        Args:
            overrides (RegistryField): TODO.

        Returns:
            Self: TODO.

        """
        data: dict[str, RegistryField] = dict(self.__dict__)
        data.update(overrides)
        return self.__class__(**data)


class RegistryItem(RegistryBase):
    """Concrete registry item.

    Attributes:
        name (str): TODO.
        count (int): TODO.
        tags (ListStr): TODO.
        extras (DictBool): TODO.

    """

    def __init__(
        self,
        name: str,
        count: int = 0,
        tags: ListStr | None = None,
        **extras: bool,
    ) -> None:
        """Initialize with optional tags and arbitrary extras.

        Args:
            name (str): TODO.
            count (int): TODO.
            tags (ListStr | None): TODO.
            extras (bool): TODO.

        """
        self.name: str = name
        self.count: int = count
        self.tags: ListStr = [] if tags is None else tags
        self.extras: DictBool = extras

    def bump(self, amount: int = 1) -> Self:
        """Increment count and return self for chaining.

        Args:
            amount (int): TODO.

        Returns:
            Self: TODO.

        """
        self.count += amount
        return self


class FluentBuilder:
    """Builder with fluent methods and conditional finalization.

    Attributes:
        parts (ListStr): TODO.
        options (DictBool): TODO.

    """

    def __init__(self) -> None:
        """Initialize builder state."""
        self.parts: ListStr = []
        self.options: DictBool = {}

    def add(self, part: str, *, repeat: int = 1) -> Self:
        """Add repeated parts and return self.

        Args:
            part (str): TODO.
            repeat (int): TODO.

        Returns:
            Self: TODO.

        """
        for _ in range(repeat):
            self.parts.append(part)
        return self

    def configure(self, **options: bool) -> Self:
        """Merge options and return self.

        Args:
            options (bool): TODO.

        Returns:
            Self: TODO.

        """
        self.options.update(options)
        return self

    @overload
    def build(self, *, compact: Literal[True]) -> str: ...

    @overload
    def build(
        self,
        *,
        compact: Literal[False] = False,
    ) -> BuilderStructured: ...

    @overload
    def build(self, *, compact: bool) -> StrOrBuilderStructured: ...

    def build(self, *, compact: bool = False) -> StrOrBuilderStructured:
        """Return a compact string or a structured result.

        Args:
            compact (bool): TODO.

        Returns:
            StrOrBuilderStructured: TODO.

        """
        if compact:
            return ":".join(self.parts)
        return {"parts": list(self.parts), "options": dict(self.options)}


class HybridContainer[ItemT, NamedT]:
    """Container exposing list-like and dict-like operations.

    Attributes:
        items (ListValue[ItemT]): TODO.
        named (dict[str, NamedT]): TODO.

    """

    def __init__(self, *items: ItemT, **named: NamedT) -> None:
        """Initialize mixed storage.

        Args:
            items (ItemT): TODO.
            named (NamedT): TODO.

        """
        self.items: ListValue[ItemT] = list(items)
        self.named: dict[str, NamedT] = dict(named)

    def __iter__(self) -> Iterator[ItemT]:
        """Iterate over positional items.

        Returns:
            Iterator[ItemT]: TODO.

        """
        return iter(self.items)

    def __contains__(self, item: object) -> bool:
        """Check both positional and named storage.

        Args:
            item (object): TODO.

        Returns:
            bool: TODO.

        """
        return item in self.items or item in self.named

    @overload
    def __getitem__(self, key: int) -> ItemT: ...

    @overload
    def __getitem__(self, key: str) -> NamedT: ...

    def __getitem__(self, key: IntOrStr) -> ValueOrOther[ItemT, NamedT]:
        """Return item by int index or dict key.

        Args:
            key (IntOrStr): TODO.

        Returns:
            ValueOrOther[ItemT, NamedT]: TODO.

        """
        if isinstance(key, int):
            return self.items[key]
        return self.named[key]

    @overload
    def __setitem__(self, key: int, value: ItemT) -> None: ...

    @overload
    def __setitem__(self, key: str, value: NamedT) -> None: ...

    def __setitem__(
        self,
        key: IntOrStr,
        value: ValueOrOther[ItemT, NamedT],
    ) -> None:
        """Set item by int index or dict key.

        Args:
            key (IntOrStr): TODO.
            value (ValueOrOther[ItemT, NamedT]): TODO.

        """
        if isinstance(key, int):
            self.items[key] = cast(typ="ItemT", val=value)
        else:
            self.named[key] = cast(typ="NamedT", val=value)

    def __or__(
        self,
        other: HybridMergeInput[ItemT, NamedT],
    ) -> HybridContainer[ItemT, NamedT]:
        """Merge with another container or mapping.

        Args:
            other (HybridMergeInput[ItemT, NamedT]): TODO.

        Returns:
            HybridContainer[ItemT, NamedT]: TODO.

        """
        merged: HybridContainer[ItemT, NamedT] = HybridContainer(
            *self.items,
            **self.named,
        )
        if isinstance(other, HybridContainer):
            merged.items.extend(other.items)
            merged.named.update(other.named)
        else:
            merged.named.update(other)
        return merged


class CallableObject:
    """Callable object with state-dependent returns.

    Attributes:
        mode (str): TODO.

    """

    def __init__(self, mode: str) -> None:
        """Store call mode.

        Args:
            mode (str): TODO.

        """
        self.mode: str = mode

    def __call__[ValueT: int | str](
        self,
        value: ValueT,
        *,
        scale: int = 1,
    ) -> IntOrStr | CallablePayload[ValueT]:
        """Return different types based on mode.

        Args:
            value (ValueT): TODO.
            scale (int): TODO.

        Returns:
            IntOrStr | CallablePayload[ValueT]: TODO.

        """
        if self.mode == "number":
            return value * scale
        if self.mode == "text":
            return str(object=value) * scale
        return {"value": value, "scale": scale}


class AsyncResource:
    """Async resource with enter/exit methods.

    Attributes:
        name (str): TODO.
        events (ListStr): TODO.

    """

    def __init__(self, name: str) -> None:
        """Initialize resource.

        Args:
            name (str): TODO.

        """
        self.name: str = name
        self.events: ListStr = []

    async def __aenter__(self) -> Self:
        """Enter async context.

        Returns:
            Self: TODO.

        """
        self.events.append("enter")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        """Exit async context.

        Args:
            exc_type (type[BaseException] | None): TODO.
            exc (BaseException | None): TODO.
            tb (TracebackType | None): TODO.

        Returns:
            bool: TODO.

        """
        self.events.append("exit")
        return exc_type is None

    async def fetch(self, value: int) -> AsyncPayload:
        """Return async payload.

        Args:
            value (int): TODO.

        Returns:
            AsyncPayload: TODO.

        """
        await sleep(delay=0)
        return {"resource": self.name, "value": value}


@contextmanager
def extended_sync_context(seed: int) -> Generator[SyncContext]:
    """Yield a mutable context dictionary.

    Args:
        seed (int): TODO.

    Yields:
        SyncContext: TODO.

    """
    context: SyncContext = {"seed": seed, "events": []}
    context["events"].append("enter")
    try:
        yield context
    finally:
        context["events"].append("exit")


@asynccontextmanager
async def extended_async_context(seed: int) -> AsyncGenerator[AsyncResource]:
    """Yield an async resource and mutate its events.

    Args:
        seed (int): TODO.

    Yields:
        AsyncResource: TODO.

    """
    resource: AsyncResource = AsyncResource(name=f"resource-{seed}")
    opened: AsyncResource
    async with resource as opened:
        yield opened


@overload
def preserve_signature_decorator[**P](
    func: CallableParametersToResult[P, str],
) -> CallableParametersToResult[P, str]: ...


@overload
def preserve_signature_decorator[**P, T](
    func: CallableParametersToResult[P, tuple[T, ...]],
) -> CallableParametersToResult[P, list[T]]: ...


@overload
def preserve_signature_decorator[**P, R](
    func: CallableParametersToResult[P, R],
) -> CallableParametersToResult[P, R | Sequence[object]]: ...


def preserve_signature_decorator[**P, R](
    func: CallableParametersToResult[P, R],
) -> CallableParametersToResult[P, R | Sequence[object]]:
    """Preserve arbitrary args and kwargs through a decorator.

    Args:
        func (CallableParametersToResult[P, R]): TODO.

    Returns:
        CallableParametersToResult[P, R | Sequence[object]]: TODO.

    """

    @wraps(wrapped=func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | Sequence[object]:
        """Invoke the wrapped function with forwarded arguments.

        Args:
            args (P.args): TODO.
            kwargs (P.kwargs): TODO.

        Returns:
            R | Sequence[object]: TODO.

        """
        result: R = func(*args, **kwargs)
        if isinstance(result, tuple):
            return list(cast(typ="tuple[object, ...]", val=result))
        return result

    return wrapper


def decorator_factory[**P, R](
    prefix: str,
    *,
    uppercase: bool = False,
) -> CallableValueToResult[
    CallableParametersToResult[P, R],
    CallableParametersToResult[P, str],
]:
    """Create a decorator factory changing string outputs.

    Args:
        prefix (str): TODO.
        uppercase (bool): TODO.

    Returns:
        CallableValueToResult[CallableParametersToResult[P, R],
            CallableParametersToResult[P, str]]: TODO.

    """

    def decorate(
        func: CallableParametersToResult[P, R],
    ) -> CallableParametersToResult[P, str]:
        """Apply the configured transformation to a callable.

        Args:
            func (CallableParametersToResult[P, R]): TODO.

        Returns:
            CallableParametersToResult[P, str]: TODO.

        """

        @wraps(wrapped=func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> str:
            """Invoke the wrapped function with forwarded arguments.

            Args:
                args (P.args): TODO.
                kwargs (P.kwargs): TODO.

            Returns:
                str: TODO.

            """
            result: R = func(*args, **kwargs)
            text: str = f"{prefix}:{result}"
            if uppercase:
                return text.upper()
            return text

        return wrapper

    return decorate


@preserve_signature_decorator
@decorator_factory(prefix="tag", uppercase=True)
def decorated_pipeline_value(value: str, suffix: str = "end") -> str:
    """Return decorated text.

    Args:
        value (str): TODO.
        suffix (str): TODO.

    Returns:
        str: TODO.

    """
    return f"{value}-{suffix}"


@singledispatch
def singledispatch_stress[T](value: T) -> DispatchOutcome[T]:
    """Return the default singledispatch branch.

    Args:
        value (T): TODO.

    Returns:
        DispatchOutcome[T]: TODO.

    """
    return {"type": type(value).__name__, "value": value}


@singledispatch_stress.register(int)
def _(value: int) -> int:
    """Integer branch.

    Args:
        value (int): TODO.

    Returns:
        int: TODO.

    """
    return value * 10


@singledispatch_stress.register(str)
def _(value: str) -> str:
    """Return the string branch.

    Args:
        value (str): TODO.

    Returns:
        str: TODO.

    """
    return value.upper()


@lru_cache(maxsize=16)
def cached_recursive_pair(n: int) -> TupleIntVariadic:
    """Return Fibonacci-like pair with recursion and cache.

    Args:
        n (int): TODO.

    Returns:
        TupleIntVariadic: TODO.

    """
    if n <= 1:
        return (n, 1)
    left: TupleIntVariadic = cached_recursive_pair(n=n - 1)
    right: TupleIntVariadic = cached_recursive_pair(n=n - 2)
    return (left[0] + right[0], left[1] + right[1])


@overload
def function_with_pattern_matching_stress(
    value: PointPattern,
) -> tuple[int, int]: ...


@overload
def function_with_pattern_matching_stress(
    value: LinePattern,
) -> ListInt: ...


@overload
def function_with_pattern_matching_stress(
    value: PatternInput,
) -> object: ...


def function_with_pattern_matching_stress(
    value: PatternInput,
) -> object:
    """Exercise match/case inference across structural patterns.

    Args:
        value (PatternInput): TODO.

    Returns:
        object: TODO.

    """
    match value:
        case {"kind": "point", "x": int(x), "y": int(y)}:
            return (x, y)
        case {"kind": "line", "points": [first, *rest]}:
            return [first, *rest]
        case [name, count] if isinstance(name, str):
            return {name: count}
        case [left, right]:
            return {"left": left, "right": right}
        case None:
            return Constants.extended_sentinel
        case _:
            return str(object=value)


def function_with_walrus_and_narrowing(
    records: SequenceValue[AmountRecord],
) -> TupleDefaultdictStrIntListStr:
    """Use walrus, truthiness, regex, and narrowing.

    Args:
        records (SequenceValue[AmountRecord]): TODO.

    Returns:
        TupleDefaultdictStrIntListStr: TODO.

    """
    totals: DefaultdictStrInt = defaultdict(int)
    matched: ListStr = []
    record: AmountRecord
    for record in records:
        if (raw_name := record.get("name")) and isinstance(raw_name, str):
            name: str = raw_name.strip().lower()
        else:
            name = "unknown"
        if (raw_amount := record.get("amount")) is None:
            amount: int = 0
        elif isinstance(raw_amount, str):
            amount = int(raw_amount) if raw_amount.isnumeric() else 0
        elif isinstance(raw_amount, int):
            amount = raw_amount
        else:
            amount = 0
        totals[name] += amount
        if found := search(pattern="[a-z]+", string=name):
            matched.append(found.group(0))
    return (totals, matched)


def function_with_recursive_containers(seed: int) -> RecursiveRoot:
    """Create recursive containers and aliased references.

    Args:
        seed (int): TODO.

    Returns:
        RecursiveRoot: TODO.

    """
    root: RecursiveRoot = {"seed": seed, "children": []}
    child: RecursiveChild = {"parent": root, "values": [seed]}
    root["children"].append(child)
    alias: RecursiveChild = root["children"][0]
    alias["values"].extend([seed + 1, seed + 2])
    return root


def function_with_numeric_tower(
    values: SequenceValue[float | str],
) -> TupleIntFloatVariadicListInt:
    """Mix int, float, complex, bool, and math/operator functions.

    Args:
        values (SequenceValue[float | str]): TODO.

    Returns:
        TupleIntFloatVariadicListInt: TODO.

    """
    total: int = 0
    products: ListInt = []
    index: int
    value: float | str
    for index, value in enumerate(iterable=values):
        adjusted: int = index if isinstance(value, str) else int(value) + index
        total += adjusted
        products.append(adjusted * 2)
    mean: float = total / len(values) if values else nan
    magnitude: float = abs(complex(real=mean, imag=total))
    return (total, mean, magnitude, products)


type ReassignmentOutcome[T] = (
    int | list[T | str] | dict[str, T | bool] | tuple[str, T] | str | None
)


@overload
def function_with_type_reassignment_maze(
    flag: Literal["none"],
    payload: object,
) -> None: ...


@overload
def function_with_type_reassignment_maze(
    flag: Literal["int"],
    payload: object,
) -> int: ...


@overload
def function_with_type_reassignment_maze[T](
    flag: Literal["list"],
    payload: T,
) -> list[T | str]: ...


@overload
def function_with_type_reassignment_maze[T](
    flag: Literal["dict"],
    payload: T,
) -> dict[str, T | bool]: ...


@overload
def function_with_type_reassignment_maze[T](
    flag: Literal["callable"],
    payload: T,
) -> tuple[str, T]: ...


@overload
def function_with_type_reassignment_maze[T](
    flag: str,
    payload: T,
) -> ReassignmentOutcome[T]: ...


def function_with_type_reassignment_maze[PayloadT](
    flag: str,
    payload: PayloadT,
) -> ReassignmentOutcome[PayloadT]:
    """Stress linear reassignment across unrelated runtime shapes.

    Args:
        flag (str): TODO.
        payload (PayloadT): TODO.

    Returns:
        ReassignmentOutcome[PayloadT]: TODO.

    """
    if flag == "none":
        return None
    if flag == "int":
        return 1
    if flag == "list":
        value: list[PayloadT] = [payload]
        return [*value, "extra"]
    if flag == "dict":
        mapping: dict[str, PayloadT] = {"payload": payload}
        return {**mapping, "seen": True}
    if flag == "callable":

        def callback(item: str) -> TupleStrValue[PayloadT]:
            """Return a label paired with the captured payload.

            Args:
                item (str): TODO.

            Returns:
                TupleStrValue[PayloadT]: TODO.

            """
            return (item, payload)

        return callback(item="called")
    return str(object=payload)


class LocalExtendedError(Exception):
    """Local exception for inference."""


def raise_value_error() -> Never:
    """Raise ValueError with message.

    Raises:
        ValueError: TODO.

    """
    msg: str = "bad value"
    raise ValueError(msg)


def raise_type_error() -> Never:
    """Raise TypeError with message.

    Raises:
        TypeError: TODO.

    """
    msg: str = "bad type"
    raise TypeError(msg)


def raise_local_error() -> Never:
    """Raise LocalExtendedError with message.

    Raises:
        LocalExtendedError: TODO.

    """
    msg: str = "local"
    raise LocalExtendedError(msg)


def function_with_chained_exceptions(mode: str) -> StrOrDictStr:
    """Exercise exception value types and chained exceptions.

    Args:
        mode (str): TODO.

    Returns:
        StrOrDictStr: TODO.

    Raises:
        RuntimeError: TODO.

    """
    try:
        if mode == "value":
            raise_value_error()
        if mode == "type":
            raise_type_error()
        if mode == "local":
            raise_local_error()
    except ValueError as error:
        return str(object=error)
    except TypeError as error:
        msg: str = "wrapped"
        raise RuntimeError(msg) from error
    except LocalExtendedError as error:
        return {"local": str(object=error)}
    else:
        return "ok"


def function_with_exception_group_stress(
    values: SequenceValue[IntOrNone],
) -> TupleListIntListStr:
    """Exercise except* branches and collected errors.

    Args:
        values (SequenceValue[IntOrNone]): TODO.

    Returns:
        TupleListIntListStr: TODO.

    """

    def raise_error_group(errors: ListException) -> Never:
        """Raise the accumulated exceptions as one group.

        Args:
            errors (ListException): TODO.

        Raises:
            ExceptionGroup: TODO.

        """
        msg: str = "extended"
        raise ExceptionGroup(msg, errors)

    errors: ListException = []
    value_errors: ListInt = []
    type_errors: ListStr = []
    value: IntOrNone
    for value in values:
        if isinstance(value, int) and value < 0:
            errors.append(ValueError(value))
        elif value is None:
            msg: str = "missing"
            errors.append(TypeError(msg))
    try:
        if errors:
            raise_error_group(errors=errors)
    except* ValueError as group:
        group: ExceptionGroup[ValueError | TypeError]
        value_errors = [error.args[0] for error in group.exceptions]
    except* TypeError as group:
        type_errors = [str(object=error) for error in group.exceptions]
    return (value_errors, type_errors)


@overload
def function_with_import_and_reflection_stress(
    module_name: Literal["pathlib"],
    attr_name: Literal["Path"],
) -> PathReflectionResult: ...


@overload
def function_with_import_and_reflection_stress(
    module_name: str,
    attr_name: str,
) -> ReflectionResult: ...


def function_with_import_and_reflection_stress(
    module_name: str,
    attr_name: str,
) -> ReflectionResult:
    """Import module dynamically and inspect attributes.

    Args:
        module_name (str): TODO.
        attr_name (str): TODO.

    Returns:
        ReflectionResult: TODO.

    """
    module: ModuleType = import_module(name=module_name)
    attr: object = cast(typ="object", val=getattr(module, attr_name))
    attr_type: TypeObject = type(attr)
    return {
        "module": module.__name__,
        "attr": attr,
        "attr_type": attr_type.__name__,
        "has_doc": bool(getattr(attr, "__doc__", None)),
    }


def function_with_json_uuid_and_path_stress(tmp_name: str) -> JSONRoundtrip:
    """Exercise JSON, UUID, Path, and text round-tripping.

    Args:
        tmp_name (str): TODO.

    Returns:
        JSONRoundtrip: TODO.

    """
    identifier: UUID = uuid5(namespace=NAMESPACE_DNS, name=tmp_name)
    path: Path = Path(gettempdir()) / f"{identifier}.json"
    payload: JSONRoundtrip = {
        "id": str(object=identifier),
        "parts": path.stem.split(sep="-"),
        "exists": path.exists(),
    }
    _ = path.write_text(data=dumps(obj=payload), encoding="utf-8")
    loaded: JSONRoundtrip = cast(
        typ="JSONRoundtrip",
        val=loads(s=path.read_text(encoding="utf-8")),
    )
    path.unlink(missing_ok=True)
    return loaded


def function_with_contextvars_and_chainmap(
    configs: SequenceValue[MutableMapping[str, int]],
) -> Mapping[str, int]:
    """Use ContextVar and ChainMap layered lookup.

    Args:
        configs (SequenceValue[MutableMapping[str, int]]): TODO.

    Returns:
        Mapping[str, int]: TODO.

    """
    token: Token[DictBoolOrNone] = Constants.extended_context.set(None)
    try:
        current_map: DictInt = {"seed": len(configs)}
        chain_map: ChainMap[str, int] = ChainMap(current_map, *configs)
        resolved: DictInt = {key: chain_map[key] for key in chain_map}
    finally:
        Constants.extended_context.reset(token)
    return resolved


def function_with_iterable_unpacking_stress(
    data: SequenceInt,
) -> UnpackingStressResult:
    """Mix star-unpacking, zip, enumerate, and heterogeneous outputs.

    Args:
        data (SequenceInt): TODO.

    Returns:
        UnpackingStressResult: TODO.

    """
    head: int
    tail: int
    middle: ListInt
    head, *middle, tail = data
    pairs: ListTupleIntVariadic = [
        (index, value) for index, value in enumerate(iterable=middle)
    ]
    zipped: ListTupleIntVariadic = list(zip([head], [tail], strict=False))
    return (head, middle, tail, pairs, zipped)


def function_with_generator_send_throw_close(
    limit: int,
) -> TupleIntVariadicGeneratorIntIntOrStrOrNoneInt:
    """Return a generator supporting send/throw/close interactions.

    Args:
        limit (int): TODO.

    Returns:
        TupleIntVariadicGeneratorIntIntOrStrOrNoneInt: TODO.

    """

    def controlled_generator() -> GeneratorIntIntOrStrOrNoneInt:
        """Generate integers and accept control values.

        Yields:
            GeneratorIntIntOrStrOrNoneInt: TODO.

        Returns:
            TODO.

        """
        current: int = 0
        while current < limit:
            received: int | Literal["stop"] | None = yield current
            if received is None:
                current += 1
            elif received == "stop":
                return current
            else:
                current += received

    generator: GeneratorIntIntOrStrOrNoneInt = controlled_generator()
    first: int = next(generator)
    second: int = generator.send(2)
    _ = generator.close()
    return (first, second, generator)


def function_with_property_and_descriptor_interaction() -> (
    TupleDescriptorSummaryIntStr
):
    """Use descriptor owner, cached property, deletion, and reset.

    Returns:
        TupleDescriptorSummaryIntStr: TODO.

    """
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=10,
        label="alpha",
    )
    before: DescriptorSummary = owner.summary
    current_score: int = owner.score
    owner.score = current_score + 5
    del owner.label
    after_delete: str = owner.label
    return (before, owner.score, after_delete)


def function_with_metaclass_registry_stress() -> (
    TupleRegistryItemVariadicListStr
):
    """Create registry instances and clone them.

    Returns:
        TupleRegistryItemVariadicListStr: TODO.

    """
    item: RegistryItem = RegistryItem(
        name="alpha",
        count=1,
        tags=["x"],
        extra=True,
    )
    clone: RegistryItem = item.bump(amount=2).clone(name="beta")
    registry: DictRegistryMeta | None = RegistryMeta.registry
    registry_names: ListStr = sorted(registry) if registry else []
    return (item, clone, registry_names)


def function_with_fluent_builder_stress() -> TupleBuilderStructuredStr:
    """Use fluent builder and mixed finalization modes.

    Returns:
        TupleBuilderStructuredStr: TODO.

    """
    builder: FluentBuilder = FluentBuilder()
    structured: BuilderStructured = (
        builder.add(part="a").add("b", repeat=2).configure(debug=True).build()
    )
    compact: str = builder.build(compact=True)
    return (structured, compact)


def function_with_hybrid_container_stress() -> (
    TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt
):
    """Stress custom container protocols and operator overloads.

    Returns:
        TupleHybridContainerNumericStrOrBoolOrListIntBoolListInt: TODO.

    """
    left: HybridContainerNumericStrOrBoolOrListInt = HybridContainer(
        1,
        2,
        name="left",
    )
    right: HybridContainerNumericStrOrBoolOrListInt = HybridContainer(
        3,
        4,
        name="right",
        enabled=True,
    )
    merged: HybridContainerNumericStrOrBoolOrListInt = left | right
    merged[0] = merged[0] + 10
    merged["extra"] = [value for value in merged if isinstance(value, int)]
    return (merged, "name" in merged, merged["extra"])


def function_with_callable_object_stress() -> CallablePayloadResults:
    """Call stateful callable objects with keyword-only args.

    Returns:
        CallablePayloadResults:
            TODO.

    """
    number_call: CallableObject = CallableObject(mode="number")
    text_call: CallableObject = CallableObject(mode="text")
    dict_call: CallableObject = CallableObject(mode="dict")
    return (
        number_call(value=4, scale=3),
        text_call(value="ha", scale=2),
        dict_call(value="payload", scale=5),
    )


async def function_with_async_comprehension_stress(
    values: SequenceInt,
) -> TupleAsyncPayloadListInt:
    """Use async context, async helper, and async comprehension.

    Args:
        values (SequenceInt): TODO.

    Returns:
        TupleAsyncPayloadListInt: TODO.

    """

    async def produce() -> AsyncIterator[int]:
        """Produce an asynchronous value for the resource.

        Yields:
            int: TODO.

        """
        value: int
        for value in values:
            await sleep(delay=0)
            yield (value * 2)

    resource: AsyncResource
    async with extended_async_context(seed=len(values)) as resource:
        fetched: AsyncPayload = await resource.fetch(sum(values))
        doubled: ListInt = [value async for value in produce()]
    return (fetched, doubled)


def function_with_local_class_closure_stress(
    multiplier: int,
) -> SupportsCallAndFromValues:
    """Return a local class capturing outer state.

    Args:
        multiplier (int): TODO.

    Returns:
        SupportsCallAndFromValues: TODO.

    """

    class LocalMultiplier:
        """Local class closing over multiplier.

        Attributes:
            offset (int): TODO.

        """

        def __init__(self, offset: int = 0) -> None:
            """Initialize instance state from the supplied arguments.

            Args:
                offset (int): TODO.

            """
            self.offset: int = offset

        def apply(self, value: int) -> int:
            """Apply the captured multiplier to the supplied value.

            Args:
                value (int): TODO.

            Returns:
                int: TODO.

            """
            return value * multiplier + self.offset

        @classmethod
        def from_values(cls, values: SequenceInt) -> Self:
            """Construct an instance from a sequence of values.

            Args:
                values (SequenceInt): TODO.

            Returns:
                Self: TODO.

            """
            return cls(offset=sum(values))

    return LocalMultiplier


def function_with_nested_default_factories() -> (
    TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic
):
    """Build nested defaultdict structures.

    Returns:
        TupleDefaultdictStrDefaultdictStrListIntDictDictTupleIntVariadic: TODO.

    """
    tree: DefaultdictStrDefaultdictStrListInt = defaultdict(
        lambda: defaultdict(list),
    )
    section: str
    key: str
    value: int
    for section, key, value in [
        ("a", "x", 1),
        ("a", "x", 2),
        ("a", "y", 3),
        ("b", "z", 4),
    ]:
        tree[section][key].append(value)
    frozen: DictDictTupleIntVariadic = {
        section: {key: tuple(values) for key, values in group.items()}
        for section, group in tree.items()
    }
    return (tree, frozen)


def function_with_sort_key_and_grouping_stress(
    rows: SequenceValue[GroupInput],
) -> TupleListNormalizedRowDictListInt:
    """Sort/group by computed keys and return nested groups.

    Args:
        rows (SequenceValue[GroupInput]): TODO.

    Returns:
        TupleListNormalizedRowDictListInt: TODO.

    """
    normalized: ListNormalizedRow = [
        {"name": row["name"].strip().lower(), "score": int(row["score"])}
        for row in rows
    ]
    normalized.sort(key=lambda row: (row["name"], -row["score"]))
    grouped: DictListInt = {
        name: [item["score"] for item in group]
        for name, group in groupby(
            iterable=normalized,
            key=lambda row: row["name"],
        )
    }
    return (normalized, grouped)


def function_with_partial_reduce_and_operator_stress(
    numbers: SequenceInt,
) -> TupleListIntIntVariadic:
    """Mix partial, reduce, and operator functions.

    Args:
        numbers (SequenceInt): TODO.

    Returns:
        TupleListIntIntVariadic: TODO.

    """
    add_five: CallableIntInt = partial(add, 5)
    transformed: ListInt = [add_five(number) for number in numbers]
    total: int = reduce(add, transformed, 0)
    product_value: int = reduce(mul, transformed, 1)
    return (transformed, total, product_value)


type RuntimeCandidate = (
    SupportsMethodUpdate
    | SupportsMethodExecuteIntInt
    | CallableValueToResult[str, IntOrStr | CallablePayloadStr]
    | DescriptorStressOwner
)
type RuntimeOutcome = IntOrStrOrCallablePayloadStr | None


@overload
def function_with_protocol_like_runtime_checks(
    candidate: DescriptorStressOwner,
) -> None: ...


@overload
def function_with_protocol_like_runtime_checks(
    candidate: CallableObject,
) -> RuntimeOutcome: ...


@overload
def function_with_protocol_like_runtime_checks(
    candidate: RuntimeCandidate,
) -> RuntimeOutcome: ...


def function_with_protocol_like_runtime_checks(
    candidate: RuntimeCandidate,
) -> RuntimeOutcome:
    """Infer from hasattr/callable runtime protocol checks.

    Args:
        candidate (RuntimeCandidate): TODO.

    Returns:
        RuntimeOutcome: TODO.

    """
    updater: SupportsMethodUpdate
    if hasattr(candidate, "update") and callable(
        (updater := cast(typ="SupportsMethodUpdate", val=candidate)).update,
    ):
        updater.update("message")
        return "updated"
    strategy: SupportsMethodExecuteIntInt
    if hasattr(candidate, "execute") and callable(
        (
            strategy := cast(typ="SupportsMethodExecuteIntInt", val=candidate)
        ).execute,
    ):
        return strategy.execute(2, 3)
    if callable(candidate):
        return candidate("value")
    return None


def function_with_deep_attribute_assignment() -> (
    TupleSupportsMetadataAndNameVariadicNodeMetadata
):
    """Assign attributes at several depths and return snapshots.

    Returns:
        TupleSupportsMetadataAndNameVariadicNodeMetadata: TODO.

    """

    class Node:
        """Mutable tree node with parent, children, and metadata.

        Attributes:
            parent (Node | None): TODO.
            name (str): TODO.
            children (ListValue[Node]): TODO.
            metadata (NodeMetadata): TODO.

        """

        parent: Node | None

        def __init__(self, name: str) -> None:
            """Initialize instance state from the supplied arguments.

            Args:
                name (str): TODO.

            """
            self.name: str = name
            self.parent = None
            self.children: ListValue[Node] = []
            self.metadata: NodeMetadata = {}

        def add(self, child: Node) -> Node:
            """Attach a child node to this node.

            Args:
                child (Node): TODO.

            Returns:
                Node: TODO.

            """
            self.children.append(child)
            child.parent = self
            return child

    root: Node = Node(name="root")
    child: Node = root.add(child=Node(name="child"))
    leaf: Node = child.add(child=Node(name="leaf"))
    leaf.metadata = {"depth": 2, "path": [root.name, child.name, leaf.name]}
    return (root, child, leaf.metadata)


def function_with_bytes_memoryview_and_slices(
    data: bytes,
) -> TupleBytearrayMemoryviewBytesInt:
    """Exercise bytes, bytearray, memoryview, and slice inference.

    Args:
        data (bytes): TODO.

    Returns:
        TupleBytearrayMemoryviewBytesInt: TODO.

    """
    raw: bytearray = bytearray(data)
    raw.extend(b"!")
    view: memoryview[int] = memoryview(raw)
    prefix: bytes = bytes(view[:2])
    ordinal_sum: int = sum(view)
    return (raw, view, prefix, ordinal_sum)


def function_with_map_filter_zip_stress(
    values: SequenceInt,
) -> ListTupleIntVariadic:
    """Use map/filter/zip pipelines with lambdas.

    Args:
        values (SequenceInt): TODO.

    Returns:
        ListTupleIntVariadic: TODO.

    """
    mapped: GeneratorInt = (value * 2 for value in values)
    filtered: GeneratorInt = (value for value in mapped if value % 3 != 0)
    paired: zip[TupleIntVariadic] = zip(values, filtered, strict=False)
    return list(paired)


def function_with_composed_inner_functions(seed: int) -> DictInt:
    """Compose inner functions where each narrows a value.

    Args:
        seed (int): TODO.

    Returns:
        DictInt: TODO.

    """

    def normalize(value: SupportsStringConversion | bytes) -> str:
        """Normalize text-like input to a lowercase string.

        Args:
            value (SupportsStringConversion | bytes): TODO.

        Returns:
            str: TODO.

        """
        if isinstance(value, str):
            return value.strip().lower()
        if isinstance(value, bytes):
            return value.decode().strip().lower()
        return str(object=value)

    def tokenize(value: str | bytes) -> ListStr:
        """Split normalized text into nonempty tokens.

        Args:
            value (str | bytes): TODO.

        Returns:
            ListStr: TODO.

        """
        return [
            part
            for part in split(pattern="\\W+", string=normalize(value=value))
            if part
        ]

    def score(tokens: SequenceStr) -> DictInt:
        """Assign each token a score relative to the seed.

        Args:
            tokens (SequenceStr): TODO.

        Returns:
            DictInt: TODO.

        """
        return {
            token: index + seed for index, token in enumerate(iterable=tokens)
        }

    return score(tokens=tokenize(value="Alpha beta alpha"))


def function_with_mutable_default_like_pattern[ItemT: Hashable](
    value: ItemT,
    store: ValueOrNone[ListValue[ItemT]] = None,
) -> tuple[ListValue[ItemT], TupleValueVariadic[ItemT], set[ItemT]]:
    """Avoid mutable defaults while preserving accumulator type.

    Args:
        value (ItemT): TODO.
        store (ValueOrNone[ListValue[ItemT]]): TODO.

    Returns:
        tuple[ListValue[ItemT], TupleValueVariadic[ItemT], set[ItemT]]: TODO.

    """
    if store is None:
        store = []
    store.append(value)
    return (store, tuple(store), set(store))


@overload
def function_with_literal_mode_dispatch(
    mode: Literal["json"],
    value: JSONValue,
) -> str: ...


@overload
def function_with_literal_mode_dispatch[T](
    mode: str,
    value: T,
) -> ValueOrIntOrStr[T]: ...


def function_with_literal_mode_dispatch[T](
    mode: str,
    value: T,
) -> ValueOrIntOrStr[T]:
    """Dispatch by string literal-like mode.

    Args:
        mode (str): TODO.
        value (T): TODO.

    Returns:
        ValueOrIntOrStr[T]: TODO.

    """
    handlers: dict[
        str,
        Callable[[str | int | float | bool], int] | Callable[[JSONValue], str],
    ] = {
        "int": int,
        "str": str,
        "repr": repr,
        "json": dumps,
    }
    if mode not in handlers:
        return value
    handler: Callable[[T], IntOrStr] = cast(
        typ="Callable[[T], int | str]",
        val=handlers[mode],
    )
    return handler(value)


type NarrowableInput[T] = dict[str, T] | list[T] | tuple[T, ...] | str | None


@overload
def function_with_complex_boolean_narrowing(
    value: DictInt,
    *,
    fallback: bool,
) -> int: ...


@overload
def function_with_complex_boolean_narrowing[ValueT, FallbackT](
    value: NarrowableInput[ValueT],
    fallback: FallbackT,
) -> ValueT | FallbackT | str: ...


def function_with_complex_boolean_narrowing[ValueT, FallbackT](
    value: NarrowableInput[ValueT],
    fallback: FallbackT,
) -> ValueT | FallbackT | str:
    """Exercise branch-sensitive dictionary, sequence, and string inference.

    Args:
        value (NarrowableInput[ValueT]): TODO.
        fallback (FallbackT): TODO.

    Returns:
        ValueT | FallbackT | str: TODO.

    """
    if isinstance(value, dict):
        if "result" in value:
            return value["result"]
        return fallback
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    if isinstance(value, str) and value.strip():
        return value.strip().upper()
    return fallback


def function_with_extended_named_results() -> (
    TupleExtendedResultListIntStrIntBool
):
    """Return custom result objects and tuple-unpacking behavior.

    Returns:
        TupleExtendedResultListIntStrIntBool: TODO.

    """
    result: ExtendedResult[ListInt] = ExtendedResult(
        name="alpha",
        payload=[1, 2, 3],
        metadata={"ok": True},
    )
    name: str = result.name
    payload: ListInt = result.payload
    metadata: DictBool = result.metadata
    return (result, name, payload[-1], bool(metadata["ok"]))


def test_extended_inference_edge_cases_part1() -> ExtendedResultsPart1:
    """Run extended stress cases part 1.

    Returns:
        ExtendedResultsPart1: TODO.

    """
    records: ListValue[AmountRecord] = [
        {"name": " Alpha ", "amount": "10"},
        {"name": "beta", "amount": 5},
        {"name": None, "amount": None},
    ]
    return {
        "pattern_point": function_with_pattern_matching_stress(
            value={"kind": "point", "x": 1, "y": 2},
        ),
        "pattern_line": function_with_pattern_matching_stress(
            value={"kind": "line", "points": [1, 2, 3]},
        ),
        "walrus": function_with_walrus_and_narrowing(records=records),
        "recursive": function_with_recursive_containers(seed=5),
        "numeric": function_with_numeric_tower(values=[1, 2.5, 3]),
        "reassignment_int": function_with_type_reassignment_maze(
            flag="int",
            payload=10,
        ),
        "reassignment_callable": function_with_type_reassignment_maze(
            flag="callable",
            payload="x",
        ),
        "exceptions": function_with_chained_exceptions(mode="value"),
        "exception_group": function_with_exception_group_stress(
            values=[-1, None, 2],
        ),
        "reflection": function_with_import_and_reflection_stress(
            module_name="pathlib",
            attr_name="Path",
        ),
    }


def test_extended_inference_edge_cases_part2() -> ExtendedResultsPart2:
    """Run extended stress cases part 2.

    Returns:
        ExtendedResultsPart2: TODO.

    """
    rows: ListValue[GroupInput] = [
        {"name": " Alpha", "score": "10"},
        {"name": "alpha", "score": 7},
        {"name": "Beta", "score": 3},
    ]
    return {
        "json_uuid_path": function_with_json_uuid_and_path_stress(
            tmp_name="demo",
        ),
        "contextvars": function_with_contextvars_and_chainmap(
            configs=[{"fallback": 2}, {"seed": 99, "other": 3}],
        ),
        "unpacking": function_with_iterable_unpacking_stress(
            data=[1, 2, 3, 4],
        ),
        "generator_control": function_with_generator_send_throw_close(
            limit=10,
        ),
        "descriptor": function_with_property_and_descriptor_interaction(),
        "metaclass_registry": function_with_metaclass_registry_stress(),
        "builder": function_with_fluent_builder_stress(),
        "container": function_with_hybrid_container_stress(),
        "callable_object": function_with_callable_object_stress(),
        "grouping": function_with_sort_key_and_grouping_stress(rows=rows),
    }


def test_extended_inference_edge_cases_part3() -> ExtendedResultsPart3:
    """Run extended stress cases part 3.

    Returns:
        ExtendedResultsPart3: TODO.

    """
    local_multiplier: SupportsCallAndFromValues = (
        function_with_local_class_closure_stress(multiplier=10)
    )
    local_instance: SupportsApplyAndOffset = local_multiplier.from_values(
        values=[1, 2, 3],
    )
    owner: DescriptorStressOwner = DescriptorStressOwner(
        score=3,
        label="candidate",
    )
    async_result: TupleAsyncPayloadListInt = run(
        main=function_with_async_comprehension_stress(values=[1, 2, 3]),
    )
    return {
        "local_class": local_instance.apply(value=5),
        "nested_defaultdict": function_with_nested_default_factories(),
        "partial_reduce": function_with_partial_reduce_and_operator_stress(
            numbers=[1, 2, 3],
        ),
        "runtime_protocol_update": function_with_protocol_like_runtime_checks(
            candidate=owner,
        ),
        "runtime_protocol_callable": (
            function_with_protocol_like_runtime_checks(
                candidate=CallableObject(mode="text"),
            )
        ),
        "deep_attributes": function_with_deep_attribute_assignment(),
        "bytes_memoryview": function_with_bytes_memoryview_and_slices(
            data=b"abc",
        ),
        "map_filter_zip": function_with_map_filter_zip_stress(
            values=[1, 2, 3, 4],
        ),
        "composed_inner": function_with_composed_inner_functions(seed=100),
        "mutable_store": function_with_mutable_default_like_pattern(value="x"),
        "literal_dispatch": function_with_literal_mode_dispatch(
            mode="json",
            value={"a": 1},
        ),
        "boolean_narrowing": function_with_complex_boolean_narrowing(
            value={"result": 42},
            fallback=False,
        ),
        "extended_result": function_with_extended_named_results(),
        "decorated_pipeline": decorated_pipeline_value(value="start"),
        "singledispatch_int": singledispatch_stress(3),
        "singledispatch_str": singledispatch_stress("hello"),
        "singledispatch_default": singledispatch_stress([1, 2]),
        "cached_recursive": cached_recursive_pair(n=6),
        "async_result": async_result,
    }


def test_extended_inference_edge_cases() -> ExtendedTestResult:
    """Run all extended inference stress cases.

    Returns:
        ExtendedTestResult: TODO.

    """
    return {
        **test_extended_inference_edge_cases_part1(),
        **test_extended_inference_edge_cases_part2(),
        **test_extended_inference_edge_cases_part3(),
    }


def main() -> None:
    """Test main function."""
    _ = test_function_calls()
    _ = test_class_instantiations()
    _ = test_other_operations()
    _ = test_new_inference_edge_cases()
    _ = test_extended_inference_edge_cases()


if __name__ == "__main__":
    main()
