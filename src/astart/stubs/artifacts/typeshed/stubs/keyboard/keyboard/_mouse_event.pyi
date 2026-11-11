import sys
from typing import Literal, NamedTuple

type _MouseEvent = ButtonEvent | WheelEvent | MoveEvent  # Used outside
LEFT: Literal["left"]
RIGHT: Literal["right"]
MIDDLE: Literal["middle"]
X: Literal["x"]
X2: Literal["x2"]
UP: Literal["up"]
DOWN: Literal["down"]
DOUBLE: Literal["double"]
WHEEL: Literal["wheel"]
VERTICAL: Literal["vertical"]
HORIZONTAL: Literal["horizontal"]
if sys.platform == "linux" or sys.platform == "win32":
    type _MouseButton = Literal["left", "right", "middle", "x", "x2"]
else:
    type _MouseButton = Literal["left", "right", "middle"]
if sys.platform == "win32":
    type _MouseEventType = Literal["up", "down", "double", "wheel"]
else:
    type _MouseEventType = Literal["up", "down"]

class ButtonEvent(NamedTuple):
    event_type: _MouseEventType
    button: _MouseButton
    time: float

class WheelEvent(NamedTuple):
    delta: int
    time: float

class MoveEvent(NamedTuple):
    x: int
    y: int
    time: float
