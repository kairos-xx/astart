import sys
from _ctypes import (
    RTLD_GLOBAL as RTLD_GLOBAL,
)
from _ctypes import (
    RTLD_LOCAL as RTLD_LOCAL,
)
from _ctypes import (
    Array as Array,
)
from _ctypes import (
    CFuncPtr as _CFuncPtr,
)
from _ctypes import (
    Structure as Structure,
)
from _ctypes import (
    Union as Union,
)
from _ctypes import (
    _CanCastTo as _CanCastTo,
)
from _ctypes import (
    _CArgObject as _CArgObject,
)
from _ctypes import (
    _CData as _CData,
)
from _ctypes import (
    _CDataType as _CDataType,
)
from _ctypes import (
    _CField as _CField,
)
from _ctypes import (
    _CTypeBaseType,
)
from _ctypes import (
    _Pointer as _Pointer,
)
from _ctypes import (
    _PointerLike as _PointerLike,
)
from _ctypes import (
    _SimpleCData as _SimpleCData,
)
from _ctypes import (
    addressof as addressof,
)
from _ctypes import (
    alignment as alignment,
)
from _ctypes import (
    byref as byref,
)
from _ctypes import (
    get_errno as get_errno,
)
from _ctypes import (
    resize as resize,
)
from _ctypes import (
    set_errno as set_errno,
)
from _ctypes import (
    sizeof as sizeof,
)
from ctypes._endian import (
    BigEndianStructure as BigEndianStructure,
)
from ctypes._endian import (
    LittleEndianStructure as LittleEndianStructure,
)
from types import GenericAlias
from typing import (
    Any,
    ClassVar,
    Final,
    Literal,
    Self,
    TypeVar,
    overload,
    type_check_only,
)
from warnings import deprecated

from _typeshed import StrPath, SupportsBool, SupportsLen

if sys.platform == "win32":
    from _ctypes import (
        FormatError as FormatError,
    )
    from _ctypes import (
        get_last_error as get_last_error,
    )
    from _ctypes import (
        set_last_error as set_last_error,
    )

    if sys.version_info >= (3, 14):
        from _ctypes import (
            COMError as COMError,
        )
        from _ctypes import (
            CopyComPointer as CopyComPointer,
        )
from ctypes._endian import (
    BigEndianUnion as BigEndianUnion,
)
from ctypes._endian import (
    LittleEndianUnion as LittleEndianUnion,
)

_CT = TypeVar("_CT", bound=_CData)
_T = TypeVar("_T", default=Any)
_DLLT = TypeVar("_DLLT", bound=CDLL)
if sys.version_info >= (3, 14):
    @overload
    @deprecated("ctypes.POINTER with string")
    def POINTER(cls: str) -> type[Any]: ...
    @overload
    def POINTER(cls: None) -> type[c_void_p]: ...
    @overload
    def POINTER[CT: _CData](cls: type[_CT]) -> type[_Pointer[_CT]]: ...
    def pointer[CT: _CData](obj: _CT) -> _Pointer[_CT]: ...
else:
    from _ctypes import POINTER as POINTER
    from _ctypes import pointer as pointer
if sys.version_info >= (3, 14):
    CField = _CField
DEFAULT_MODE: Final[int]

class ArgumentError(Exception): ...

@type_check_only
class _CDLLFuncPointer(_CFuncPtr):
    _flags_: ClassVar[int]
    _restype_: ClassVar[type[_CDataType]]

@type_check_only
class _NamedFuncPointer(_CDLLFuncPointer):
    __name__: str

type _NameTypes = StrPath | None

class CDLL:
    _func_flags_: ClassVar[int]
    _func_restype_: ClassVar[type[_CDataType]]
    _name: str
    _handle: int
    _FuncPtr: type[_CDLLFuncPointer]
    def __init__(
        self,
        name: _NameTypes,
        mode: int = ...,
        handle: int | None = None,
        use_errno: bool = False,
        use_last_error: bool = False,
        winmode: int | None = None,
    ) -> None: ...
    def __getattr__(self, name: str) -> _NamedFuncPointer: ...
    def __getitem__(self, name_or_ordinal: str) -> _NamedFuncPointer: ...

if sys.platform == "win32":
    class OleDLL(CDLL): ...
    class WinDLL(CDLL): ...

class PyDLL(CDLL): ...

class LibraryLoader[DLLT: CDLL]:
    def __init__(self, dlltype: type[_DLLT]) -> None: ...
    def __getattr__(self, name: str) -> _DLLT: ...
    def __getitem__(self, name: str) -> _DLLT: ...
    def LoadLibrary(self, name: str) -> _DLLT: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

cdll: LibraryLoader[CDLL]
if sys.platform == "win32":
    windll: LibraryLoader[WinDLL]
    oledll: LibraryLoader[OleDLL]
pydll: LibraryLoader[PyDLL]
pythonapi: PyDLL

@type_check_only
class _CFunctionType(_CFuncPtr):
    _argtypes_: ClassVar[list[type[_CData | _CDataType]]]
    _restype_: ClassVar[type[_CData | _CDataType] | None]
    _flags_: ClassVar[int]

type _FuncPointer = _CDLLFuncPointer | _CFunctionType  # not used here

def CFUNCTYPE(
    restype: type[_CData | _CDataType] | None,
    *argtypes: type[_CData | _CDataType],
    use_errno: bool = False,
    use_last_error: bool = False,
) -> type[_CFunctionType]: ...

if sys.platform == "win32":
    def WINFUNCTYPE(
        restype: type[_CData | _CDataType] | None,
        *argtypes: type[_CData | _CDataType],
        use_errno: bool = False,
        use_last_error: bool = False,
    ) -> type[_CFunctionType]: ...

def PYFUNCTYPE(
    restype: type[_CData | _CDataType] | None,
    *argtypes: type[_CData | _CDataType],
) -> type[_CFunctionType]: ...

type _CVoidPLike = _PointerLike | Array[Any] | _CArgObject | int
type _CVoidConstPLike = _CVoidPLike | bytes
_CastT = TypeVar("_CastT", bound=_CanCastTo)

def cast[CastT: _CanCastTo](
    obj: _CData | _CDataType | _CArgObject | int,
    typ: type[_CastT],
) -> _CastT: ...
def create_string_buffer(
    init: int | bytes,
    size: int | None = None,
) -> Array[c_char]: ...

c_buffer = create_string_buffer

def create_unicode_buffer(
    init: int | str,
    size: int | None = None,
) -> Array[c_wchar]: ...

if sys.version_info < (3, 15):
    @deprecated(
        "Deprecated since Python 3.13; will be removed in Python 3.15.",
    )
    def SetPointerType(
        pointer: type[_Pointer[Any]],
        cls: _CTypeBaseType,
    ) -> None: ...

@deprecated("Soft deprecated since Python 3.13. Use multiplication instead.")
def ARRAY[CT: _CData](typ: _CT, len: int) -> Array[_CT]: ...

if sys.platform == "win32":
    def DllCanUnloadNow() -> int: ...
    def DllGetClassObject(rclsid: Any, riid: Any, ppv: Any) -> int: ...
    @type_check_only
    class _GetLastErrorFunctionType(_NamedFuncPointer):
        def __call__(self) -> int: ...

    GetLastError: _GetLastErrorFunctionType

@type_check_only
class _MemmoveFunctionType(_CFunctionType):
    def __call__(
        self,
        dst: _CVoidPLike,
        src: _CVoidConstPLike,
        count: int,
    ) -> int: ...

memmove: _MemmoveFunctionType

@type_check_only
class _MemsetFunctionType(_CFunctionType):
    def __call__(self, dst: _CVoidPLike, c: int, count: int) -> int: ...

memset: _MemsetFunctionType

def string_at(ptr: _CVoidConstPLike, size: int = -1) -> bytes: ...

if sys.platform == "win32":
    def WinError(
        code: int | None = None,
        descr: str | None = None,
    ) -> OSError: ...

def wstring_at(ptr: _CVoidConstPLike, size: int = -1) -> str: ...

if sys.version_info >= (3, 14):
    def memoryview_at(
        ptr: _CVoidConstPLike,
        size: int,
        readonly: bool = False,
    ) -> memoryview: ...

class py_object(_CanCastTo, _SimpleCData[_T]):
    _type_: ClassVar[Literal["O"]]
    if sys.version_info >= (3, 14):
        def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...

class c_bool(_SimpleCData[bool]):
    _type_: ClassVar[Literal["?"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]
    def __init__(
        self,
        value: SupportsBool | SupportsLen | None = ...,
    ) -> None: ...

class c_byte(_SimpleCData[int]):
    _type_: ClassVar[Literal["b"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_ubyte(_SimpleCData[int]):
    _type_: ClassVar[Literal["B"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_short(_SimpleCData[int]):
    _type_: ClassVar[Literal["h"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_ushort(_SimpleCData[int]):
    _type_: ClassVar[Literal["H"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_long(_SimpleCData[int]):
    _type_: ClassVar[Literal["l"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_ulong(_SimpleCData[int]):
    _type_: ClassVar[Literal["L"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_int(_SimpleCData[int]):
    _type_: ClassVar[Literal["i", "l"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_uint(_SimpleCData[int]):
    _type_: ClassVar[Literal["I", "L"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_longlong(_SimpleCData[int]):
    _type_: ClassVar[Literal["q", "l"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_ulonglong(_SimpleCData[int]):
    _type_: ClassVar[Literal["Q", "L"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

c_int8 = c_byte
c_uint8 = c_ubyte

class c_int16(_SimpleCData[int]):
    _type_: ClassVar[Literal["h", "i"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_uint16(_SimpleCData[int]):
    _type_: ClassVar[Literal["H", "I"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_int32(_SimpleCData[int]):
    _type_: ClassVar[Literal["i", "l"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_uint32(_SimpleCData[int]):
    _type_: ClassVar[Literal["I", "L"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_int64(_SimpleCData[int]):
    _type_: ClassVar[Literal["l", "q"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_uint64(_SimpleCData[int]):
    _type_: ClassVar[Literal["L", "Q"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_ssize_t(_SimpleCData[int]):
    _type_: ClassVar[Literal["i", "l", "q"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_size_t(_SimpleCData[int]):
    _type_: ClassVar[Literal["I", "L", "Q"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_float(_SimpleCData[float]):
    _type_: ClassVar[Literal["f"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_double(_SimpleCData[float]):
    _type_: ClassVar[Literal["d"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]

class c_longdouble(_SimpleCData[float]):
    _type_: ClassVar[Literal["d", "g"]]

if sys.version_info >= (3, 14) and sys.platform != "win32":
    class c_double_complex(_SimpleCData[complex]):
        if sys.version_info >= (3, 15):
            _type_: ClassVar[Literal["Zd"]]
        else:
            _type_: ClassVar[Literal["D"]]
        __ctype_be__: ClassVar[type[Self]]
        __ctype_le__: ClassVar[type[Self]]

    class c_float_complex(_SimpleCData[complex]):
        if sys.version_info >= (3, 15):
            _type_: ClassVar[Literal["Zf"]]
        else:
            _type_: ClassVar[Literal["F"]]
        __ctype_be__: ClassVar[type[Self]]
        __ctype_le__: ClassVar[type[Self]]

    class c_longdouble_complex(_SimpleCData[complex]):
        if sys.version_info >= (3, 15):
            _type_: ClassVar[Literal["Zg"]]
        else:
            _type_: ClassVar[Literal["G"]]

class c_char(_SimpleCData[bytes]):
    _type_: ClassVar[Literal["c"]]
    __ctype_be__: ClassVar[type[Self]]
    __ctype_le__: ClassVar[type[Self]]
    def __init__(self, value: int | bytes | bytearray = ...) -> None: ...

class c_char_p(_PointerLike, _SimpleCData[bytes | None]):
    _type_: ClassVar[Literal["z"]]
    def __init__(self, value: int | bytes | None = ...) -> None: ...
    @classmethod
    def from_param(cls, value: Any, /) -> Self | _CArgObject: ...

class c_void_p(_PointerLike, _SimpleCData[int | None]):
    _type_: ClassVar[Literal["P"]]
    @classmethod
    def from_param(cls, value: Any, /) -> Self | _CArgObject: ...

c_voidp = c_void_p

class c_wchar(_SimpleCData[str]):
    _type_: ClassVar[Literal["u"]]

class c_wchar_p(_PointerLike, _SimpleCData[str | None]):
    _type_: ClassVar[Literal["Z"]]
    def __init__(self, value: int | str | None = ...) -> None: ...
    @classmethod
    def from_param(cls, value: Any, /) -> Self | _CArgObject: ...

if sys.platform == "win32":
    class HRESULT(_SimpleCData[int]):
        _type_: ClassVar[Literal["l"]]

c_time_t: type[c_int32 | c_int64 | c_int | c_long | c_longlong]
