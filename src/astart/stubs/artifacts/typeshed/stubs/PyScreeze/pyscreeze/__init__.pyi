import sys
from collections.abc import Callable, Generator
from typing import Final, NamedTuple, ParamSpec, TypeVar, overload

from _typeshed import ConvertibleToFloat, Incomplete, StrOrBytesPath, Unused
from PIL import Image

_P = ParamSpec("_P")
_R = TypeVar("_R")
type _MatLike = Incomplete
PILLOW_VERSION: Final[tuple[int, int, int]]
RUNNING_PYTHON_2: Final = False
SCROT_EXISTS: Final[bool]
GNOMESCREENSHOT_EXISTS: Final[bool]
if sys.platform == "linux":
    RUNNING_X11: Final[bool]
    RUNNING_WAYLAND: Final[bool]
GRAYSCALE_DEFAULT: bool
USE_IMAGE_NOT_FOUND_EXCEPTION: bool

class Box(NamedTuple):
    left: int
    top: int
    width: int
    height: int

class Point(NamedTuple):
    x: int
    y: int

class RGB(NamedTuple):
    red: int
    green: int
    blue: int

class PyScreezeException(Exception): ...
class ImageNotFoundException(PyScreezeException): ...

def requiresPyGetWindow[**P, R](
    wrappedFunction: Callable[_P, _R],
) -> Callable[_P, _R]: ...
@overload
def locate(
    needleImage: str | Image.Image | _MatLike,
    haystackImage: str | Image.Image | _MatLike,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Box | None: ...
@overload
def locate(
    needleImage: str | Image.Image,
    haystackImage: str | Image.Image,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: None = None,
) -> Box | None: ...
@overload
def locateOnScreen(
    image: str | Image.Image | _MatLike,
    minSearchTime: float = 0,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Box | None: ...
@overload
def locateOnScreen(
    image: str | Image.Image,
    minSearchTime: float = 0,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: None = None,
) -> Box | None: ...
@overload
def locateAllOnScreen(
    image: str | Image.Image | _MatLike,
    *,
    grayscale: bool | None = None,
    limit: int = 1000,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Generator[Box]: ...
@overload
def locateAllOnScreen(
    image: str | Image.Image,
    *,
    grayscale: bool | None = None,
    limit: int | None = None,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: None = None,
) -> Generator[Box]: ...
@overload
def locateCenterOnScreen(
    image: str | Image.Image | _MatLike,
    *,
    minSearchTime: float = 0,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Point | None: ...
@overload
def locateCenterOnScreen(
    image: str | Image.Image,
    *,
    minSearchTime: float = 0,
    grayscale: bool | None = None,
    limit: Unused = 1,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: None = None,
) -> Point | None: ...
def locateOnScreenNear(
    image: str | Image.Image | _MatLike,
    x: int,
    y: int,
) -> Box: ...
def locateCenterOnScreenNear(
    image: str | Image.Image | _MatLike,
    x: int,
    y: int,
) -> Point | None: ...
@overload
def locateOnWindow(
    image: str | Image.Image | _MatLike,
    title: str,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Box | None: ...
@overload
def locateOnWindow(
    image: str | Image.Image,
    title: str,
    *,
    grayscale: bool | None = None,
    limit: Unused = 1,
    step: int = 1,
    confidence: None = None,
) -> Box | None: ...
def showRegionOnScreen(
    region: tuple[int, int, int, int],
    outlineColor: str = "red",
    filename: str = "_showRegionOnScreen.png",
) -> None: ...
def center(coords: tuple[int, int, int, int]) -> Point: ...
def pixelMatchesColor(
    x: int,
    y: int,
    expectedRGBColor: tuple[int, int, int] | tuple[int, int, int, int],
    tolerance: int = 0,
) -> bool: ...
def pixel(x: int, y: int) -> tuple[int, int, int]: ...

if sys.platform == "win32":
    def screenshot(
        imageFilename: StrOrBytesPath | None = None,
        region: tuple[int, int, int, int] | None = None,
        allScreens: bool = False,
    ) -> Image.Image: ...
else:
    def screenshot(
        imageFilename: StrOrBytesPath | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> Image.Image: ...

@overload
def locateAll(
    needleImage: str | Image.Image | _MatLike,
    haystackImage: str | Image.Image | _MatLike,
    grayscale: bool | None = None,
    limit: int = 1000,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: ConvertibleToFloat = 0.999,
) -> Generator[Box]: ...
@overload
def locateAll(
    needleImage: str | Image.Image,
    haystackImage: str | Image.Image,
    grayscale: bool | None = None,
    limit: int | None = None,
    region: tuple[int, int, int, int] | None = None,
    step: int = 1,
    confidence: None = None,
) -> Generator[Box]: ...
