import sys
from _ctypes import _CArgObject, _CField
from ctypes import (
    Array,
    Structure,
    _Pointer,
    _SimpleCData,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_long,
    c_longlong,
    c_short,
    c_ubyte,
    c_uint,
    c_ulong,
    c_ulonglong,
    c_ushort,
    c_void_p,
    c_wchar,
    c_wchar_p,
)
from typing import Any, Final, Self

BYTE = c_ubyte
WORD = c_ushort
DWORD = c_ulong
CHAR = c_char
WCHAR = c_wchar
UINT = c_uint
INT = c_int
DOUBLE = c_double
FLOAT = c_float
BOOLEAN = BYTE
BOOL = c_long

class VARIANT_BOOL(_SimpleCData[bool]): ...

ULONG = c_ulong
LONG = c_long
USHORT = c_ushort
SHORT = c_short
LARGE_INTEGER = c_longlong
_LARGE_INTEGER = c_longlong
ULARGE_INTEGER = c_ulonglong
_ULARGE_INTEGER = c_ulonglong
OLESTR = c_wchar_p
LPOLESTR = c_wchar_p
LPCOLESTR = c_wchar_p
LPWSTR = c_wchar_p
LPCWSTR = c_wchar_p
LPSTR = c_char_p
LPCSTR = c_char_p
LPVOID = c_void_p
LPCVOID = c_void_p

class WPARAM(_SimpleCData[int]): ...
class LPARAM(_SimpleCData[int]): ...

ATOM = WORD
LANGID = WORD
COLORREF = DWORD
LGRPID = DWORD
LCTYPE = DWORD
LCID = DWORD
HANDLE = c_void_p
HACCEL = HANDLE
HBITMAP = HANDLE
HBRUSH = HANDLE
HCOLORSPACE = HANDLE
if sys.version_info >= (3, 14):
    HCONV = HANDLE
    HCONVLIST = HANDLE
    HCURSOR = HANDLE
    HDDEDATA = HANDLE
    HDROP = HANDLE
    HFILE = INT
    HRESULT = LONG
    HSZ = HANDLE
HDC = HANDLE
HDESK = HANDLE
HDWP = HANDLE
HENHMETAFILE = HANDLE
HFONT = HANDLE
HGDIOBJ = HANDLE
HGLOBAL = HANDLE
HHOOK = HANDLE
HICON = HANDLE
HINSTANCE = HANDLE
HKEY = HANDLE
HKL = HANDLE
HLOCAL = HANDLE
HMENU = HANDLE
HMETAFILE = HANDLE
HMODULE = HANDLE
HMONITOR = HANDLE
HPALETTE = HANDLE
HPEN = HANDLE
HRGN = HANDLE
HRSRC = HANDLE
HSTR = HANDLE
HTASK = HANDLE
HWINSTA = HANDLE
HWND = HANDLE
SC_HANDLE = HANDLE
SERVICE_STATUS_HANDLE = HANDLE
type _CIntLikeField[_CIntLikeT: _SimpleCData[int]] = _CField[
    _CIntLikeT,
    int,
    _CIntLikeT | int,
]

class RECT(Structure):
    left: _CIntLikeField[LONG]
    top: _CIntLikeField[LONG]
    right: _CIntLikeField[LONG]
    bottom: _CIntLikeField[LONG]

RECTL = RECT
_RECTL = RECT
tagRECT = RECT

class _SMALL_RECT(Structure):
    Left: _CIntLikeField[SHORT]
    Top: _CIntLikeField[SHORT]
    Right: _CIntLikeField[SHORT]
    Bottom: _CIntLikeField[SHORT]

SMALL_RECT = _SMALL_RECT

class _COORD(Structure):
    X: _CIntLikeField[SHORT]
    Y: _CIntLikeField[SHORT]

class POINT(Structure):
    x: _CIntLikeField[LONG]
    y: _CIntLikeField[LONG]

POINTL = POINT
_POINTL = POINT
tagPOINT = POINT

class SIZE(Structure):
    cx: _CIntLikeField[LONG]
    cy: _CIntLikeField[LONG]

SIZEL = SIZE
tagSIZE = SIZE

def RGB(red: int, green: int, blue: int) -> int: ...

class FILETIME(Structure):
    dwLowDateTime: _CIntLikeField[DWORD]
    dwHighDateTime: _CIntLikeField[DWORD]

_FILETIME = FILETIME

class MSG(Structure):
    hWnd: _CField[HWND, int | None, HWND | int | None]
    message: _CIntLikeField[UINT]
    wParam: _CIntLikeField[WPARAM]
    lParam: _CIntLikeField[LPARAM]
    time: _CIntLikeField[DWORD]
    pt: _CField[POINT, POINT, POINT]

tagMSG = MSG
MAX_PATH: Final = 260

class WIN32_FIND_DATAA(Structure):
    dwFileAttributes: _CIntLikeField[DWORD]
    ftCreationTime: _CField[FILETIME, FILETIME, FILETIME]
    ftLastAccessTime: _CField[FILETIME, FILETIME, FILETIME]
    ftLastWriteTime: _CField[FILETIME, FILETIME, FILETIME]
    nFileSizeHigh: _CIntLikeField[DWORD]
    nFileSizeLow: _CIntLikeField[DWORD]
    dwReserved0: _CIntLikeField[DWORD]
    dwReserved1: _CIntLikeField[DWORD]
    cFileName: _CField[Array[CHAR], bytes, bytes]
    cAlternateFileName: _CField[Array[CHAR], bytes, bytes]

class WIN32_FIND_DATAW(Structure):
    dwFileAttributes: _CIntLikeField[DWORD]
    ftCreationTime: _CField[FILETIME, FILETIME, FILETIME]
    ftLastAccessTime: _CField[FILETIME, FILETIME, FILETIME]
    ftLastWriteTime: _CField[FILETIME, FILETIME, FILETIME]
    nFileSizeHigh: _CIntLikeField[DWORD]
    nFileSizeLow: _CIntLikeField[DWORD]
    dwReserved0: _CIntLikeField[DWORD]
    dwReserved1: _CIntLikeField[DWORD]
    cFileName: _CField[Array[WCHAR], str, str]
    cAlternateFileName: _CField[Array[WCHAR], str, str]

class PSHORT(_Pointer[SHORT]): ...
class PUSHORT(_Pointer[USHORT]): ...

PWORD = PUSHORT
LPWORD = PUSHORT

class PLONG(_Pointer[LONG]): ...

LPLONG = PLONG
PBOOL = PLONG
LPBOOL = PLONG

class PULONG(_Pointer[ULONG]): ...

PDWORD = PULONG
LPDWORD = PDWORD
LPCOLORREF = PDWORD
PLCID = PDWORD

class PINT(_Pointer[INT]): ...

LPINT = PINT

class PUINT(_Pointer[UINT]): ...

LPUINT = PUINT

class PFLOAT(_Pointer[FLOAT]): ...
class PLARGE_INTEGER(_Pointer[LARGE_INTEGER]): ...
class PULARGE_INTEGER(_Pointer[ULARGE_INTEGER]): ...
class PBYTE(_Pointer[BYTE]): ...

LPBYTE = PBYTE
PBOOLEAN = PBYTE

class PCHAR(_Pointer[CHAR]):
    @classmethod
    def from_param(cls, value: Any, /) -> Self | _CArgObject: ...

class PWCHAR(_Pointer[WCHAR]):
    @classmethod
    def from_param(cls, value: Any, /) -> Self | _CArgObject: ...

class PHANDLE(_Pointer[HANDLE]): ...

LPHANDLE = PHANDLE
PHKEY = PHANDLE
LPHKL = PHANDLE
LPSC_HANDLE = PHANDLE

class PFILETIME(_Pointer[FILETIME]): ...

LPFILETIME = PFILETIME

class PMSG(_Pointer[MSG]): ...

LPMSG = PMSG

class PPOINT(_Pointer[POINT]): ...

LPPOINT = PPOINT
PPOINTL = PPOINT

class PRECT(_Pointer[RECT]): ...

LPRECT = PRECT
PRECTL = PRECT
LPRECTL = PRECT

class PSIZE(_Pointer[SIZE]): ...

LPSIZE = PSIZE
PSIZEL = PSIZE
LPSIZEL = PSIZE

class PSMALL_RECT(_Pointer[SMALL_RECT]): ...
class PWIN32_FIND_DATAA(_Pointer[WIN32_FIND_DATAA]): ...

LPWIN32_FIND_DATAA = PWIN32_FIND_DATAA

class PWIN32_FIND_DATAW(_Pointer[WIN32_FIND_DATAW]): ...

LPWIN32_FIND_DATAW = PWIN32_FIND_DATAW
