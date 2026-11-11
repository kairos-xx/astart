from typing import Any, overload

import numpy as np
import tensorflow as tf
from tensorflow._aliases import FloatArray, IntArray

type _BitwiseCompatible = (
    tf.Tensor | int | FloatArray | IntArray | np.number[Any]
)

@overload
def bitwise_and(
    x: _BitwiseCompatible,
    y: _BitwiseCompatible,
    name: str | None = None,
) -> tf.Tensor: ...
@overload
def bitwise_and(
    x: tf.RaggedTensor,
    y: tf.RaggedTensor,
    name: str | None = None,
) -> tf.RaggedTensor: ...
@overload
def bitwise_or(
    x: _BitwiseCompatible,
    y: _BitwiseCompatible,
    name: str | None = None,
) -> tf.Tensor: ...
@overload
def bitwise_or(
    x: tf.RaggedTensor,
    y: tf.RaggedTensor,
    name: str | None = None,
) -> tf.RaggedTensor: ...
@overload
def bitwise_xor(
    x: _BitwiseCompatible,
    y: _BitwiseCompatible,
    name: str | None = None,
) -> tf.Tensor: ...
@overload
def bitwise_xor(
    x: tf.RaggedTensor,
    y: tf.RaggedTensor,
    name: str | None = None,
) -> tf.RaggedTensor: ...
@overload
def invert(x: _BitwiseCompatible, name: str | None = None) -> tf.Tensor: ...
@overload
def invert(x: tf.RaggedTensor, name: str | None = None) -> tf.RaggedTensor: ...
@overload
def left_shift(
    x: _BitwiseCompatible,
    y: _BitwiseCompatible,
    name: str | None = None,
) -> tf.Tensor: ...
@overload
def left_shift(
    x: tf.RaggedTensor,
    y: tf.RaggedTensor,
    name: str | None = None,
) -> tf.RaggedTensor: ...
@overload
def right_shift(
    x: _BitwiseCompatible,
    y: _BitwiseCompatible,
    name: str | None = None,
) -> tf.Tensor: ...
@overload
def right_shift(
    x: tf.RaggedTensor,
    y: tf.RaggedTensor,
    name: str | None = None,
) -> tf.RaggedTensor: ...
