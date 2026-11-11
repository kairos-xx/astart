from typing import Any, overload

import numpy as np
import numpy.typing as npt

from . import _EncodedRLE

type _NPUInt32 = np.uint32
type _NDArrayUInt8 = npt.NDArray[np.uint8]
type _NDArrayUInt32 = npt.NDArray[np.uint32]
type _NDArrayFloat64 = npt.NDArray[np.float64]

def iou(
    dt: _NDArrayUInt32 | list[float] | list[_EncodedRLE],
    gt: _NDArrayUInt32 | list[float] | list[_EncodedRLE],
    pyiscrowd: list[int] | _NDArrayUInt8,
) -> list[Any] | _NDArrayFloat64: ...
def merge(rleObjs: list[_EncodedRLE], intersect: int = 0) -> _EncodedRLE: ...
@overload
def frPyObjects(
    pyobj: _NDArrayUInt32 | list[list[int]] | list[_EncodedRLE],
    h: int,
    w: int,
) -> list[_EncodedRLE]: ...
@overload
def frPyObjects(
    pyobj: list[int] | _EncodedRLE,
    h: int,
    w: int,
) -> _EncodedRLE: ...
def encode(bimask: _NDArrayUInt8) -> _EncodedRLE: ...
def decode(rleObjs: _EncodedRLE) -> _NDArrayUInt8: ...
def area(rleObjs: _EncodedRLE) -> _NPUInt32: ...
def toBbox(rleObjs: _EncodedRLE) -> _NDArrayFloat64: ...
