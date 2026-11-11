from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol, type_check_only

import numpy as np
import numpy.typing as npt
import tensorflow as tf
from tensorflow.dtypes import DType
from tensorflow.keras.layers import InputSpec

type ContainerGeneric[_T] = (
    Mapping[str, ContainerGeneric[_T]] | Sequence[ContainerGeneric[_T]] | _T
)
type TensorLike = tf.Tensor | tf.RaggedTensor | tf.SparseTensor
type SparseTensorLike = tf.Tensor | tf.SparseTensor
type RaggedTensorLike = tf.Tensor | tf.RaggedTensor
type Gradients = tf.Tensor | tf.IndexedSlices

@type_check_only
class KerasSerializable1(Protocol):
    def get_config(self) -> dict[str, Any]: ...

@type_check_only
class KerasSerializable2(Protocol):
    __name__: str

type KerasSerializable = KerasSerializable1 | KerasSerializable2
type TensorValue = tf.Tensor
type Integer = TensorValue | int | IntArray | np.number[Any]
type Float = Integer | float | FloatArray
type Slice = tf.Tensor | tf.RaggedTensor | int | slice | None
type FloatDataSequence = Sequence[float] | Sequence[FloatDataSequence]
type IntDataSequence = Sequence[int] | Sequence[IntDataSequence]
type StrDataSequence = Sequence[str] | Sequence[StrDataSequence]
type DataSequence = FloatDataSequence | StrDataSequence | IntDataSequence
type ScalarTensorCompatible = (
    tf.Tensor | str | float | np.ndarray[Any, Any] | np.number[Any]
)
type UIntTensorCompatible = tf.Tensor | int | UIntArray
type FloatTensorCompatible = (
    tf.Tensor | int | IntArray | float | FloatArray | np.number[Any]
)
type StringTensorCompatible = (
    tf.Tensor | str | npt.NDArray[np.str_] | Sequence[StringTensorCompatible]
)
type TensorCompatible = ScalarTensorCompatible | Sequence[TensorCompatible]
type SparseTensorCompatible = TensorCompatible | tf.SparseTensor
type TensorOrArray = tf.Tensor | AnyArray
type ShapeLike = (
    tf.TensorShape | Iterable[ScalarTensorCompatible | None] | int | tf.Tensor
)
type DTypeLike = DType | str | np.dtype[Any] | int
type ContainerTensors = ContainerGeneric[tf.Tensor]
type ContainerTensorsLike = ContainerGeneric[TensorLike]
type ContainerTensorCompatible = ContainerGeneric[TensorCompatible]
type ContainerGradients = ContainerGeneric[Gradients]
type ContainerTensorShape = ContainerGeneric[tf.TensorShape]
type ContainerInputSpec = ContainerGeneric[InputSpec]
type AnyArray = npt.NDArray[Any]
type FloatArray = npt.NDArray[np.float16 | np.float32 | np.float64]
type UIntArray = npt.NDArray[
    np.uint | np.uint8 | np.uint16 | np.uint32 | np.uint64
]
type SignedIntArray = npt.NDArray[
    np.int_ | np.int8 | np.int16 | np.int32 | np.int64
]
type IntArray = UIntArray | SignedIntArray
