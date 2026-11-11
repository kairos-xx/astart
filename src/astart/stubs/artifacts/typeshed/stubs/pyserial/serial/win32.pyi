import sys
from ctypes import (
    Structure,
    Union,
    _CField,
    _NamedFuncPointer,
    _Pointer,
    c_int64,
    c_ulong,
    c_void_p,
)
from ctypes.wintypes import DWORD

from _typeshed import Incomplete

if sys.platform == "win32":
    def is_64bit() -> bool: ...
    ULONG_PTR: type[c_int64 | c_ulong]
    class _SECURITY_ATTRIBUTES(Structure):
        nLength: _CField[Incomplete, Incomplete, Incomplete]
        lpSecurityDescriptor: _CField[Incomplete, Incomplete, Incomplete]
        bInheritHandle: _CField[Incomplete, Incomplete, Incomplete]

    LPSECURITY_ATTRIBUTES: type[_Pointer[_SECURITY_ATTRIBUTES]]
    CreateEvent: _NamedFuncPointer
    CreateFile: _NamedFuncPointer
    CreateEventW: _NamedFuncPointer
    CreateFileW: _NamedFuncPointer
    class _OVERLAPPED(Structure):
        Internal: _CField[Incomplete, Incomplete, Incomplete]
        InternalHigh: _CField[Incomplete, Incomplete, Incomplete]
        Offset: _CField[Incomplete, Incomplete, Incomplete]
        OffsetHigh: _CField[Incomplete, Incomplete, Incomplete]
        Pointer: _CField[Incomplete, Incomplete, Incomplete]
        hEvent: _CField[Incomplete, Incomplete, Incomplete]

    type OVERLAPPED = _OVERLAPPED
    class _COMSTAT(Structure):
        fCtsHold: _CField[Incomplete, Incomplete, Incomplete]
        fDsrHold: _CField[Incomplete, Incomplete, Incomplete]
        fRlsdHold: _CField[Incomplete, Incomplete, Incomplete]
        fXoffHold: _CField[Incomplete, Incomplete, Incomplete]
        fXoffSent: _CField[Incomplete, Incomplete, Incomplete]
        fEof: _CField[Incomplete, Incomplete, Incomplete]
        fTxim: _CField[Incomplete, Incomplete, Incomplete]
        fReserved: _CField[Incomplete, Incomplete, Incomplete]
        cbInQue: _CField[Incomplete, Incomplete, Incomplete]
        cbOutQue: _CField[Incomplete, Incomplete, Incomplete]

    type COMSTAT = _COMSTAT
    class _DCB(Structure):
        DCBlength: _CField[Incomplete, Incomplete, Incomplete]
        BaudRate: _CField[Incomplete, Incomplete, Incomplete]
        fBinary: _CField[Incomplete, Incomplete, Incomplete]
        fParity: _CField[Incomplete, Incomplete, Incomplete]
        fOutxCtsFlow: _CField[Incomplete, Incomplete, Incomplete]
        fOutxDsrFlow: _CField[Incomplete, Incomplete, Incomplete]
        fDtrControl: _CField[Incomplete, Incomplete, Incomplete]
        fDsrSensitivity: _CField[Incomplete, Incomplete, Incomplete]
        fTXContinueOnXoff: _CField[Incomplete, Incomplete, Incomplete]
        fOutX: _CField[Incomplete, Incomplete, Incomplete]
        fInX: _CField[Incomplete, Incomplete, Incomplete]
        fErrorChar: _CField[Incomplete, Incomplete, Incomplete]
        fNull: _CField[Incomplete, Incomplete, Incomplete]
        fRtsControl: _CField[Incomplete, Incomplete, Incomplete]
        fAbortOnError: _CField[Incomplete, Incomplete, Incomplete]
        fDummy2: _CField[Incomplete, Incomplete, Incomplete]
        wReserved: _CField[Incomplete, Incomplete, Incomplete]
        XonLim: _CField[Incomplete, Incomplete, Incomplete]
        XoffLim: _CField[Incomplete, Incomplete, Incomplete]
        ByteSize: _CField[Incomplete, Incomplete, Incomplete]
        Parity: _CField[Incomplete, Incomplete, Incomplete]
        StopBits: _CField[Incomplete, Incomplete, Incomplete]
        XonChar: _CField[Incomplete, Incomplete, Incomplete]
        XoffChar: _CField[Incomplete, Incomplete, Incomplete]
        ErrorChar: _CField[Incomplete, Incomplete, Incomplete]
        EofChar: _CField[Incomplete, Incomplete, Incomplete]
        EvtChar: _CField[Incomplete, Incomplete, Incomplete]
        wReserved1: _CField[Incomplete, Incomplete, Incomplete]

    type DCB = _DCB
    class _COMMTIMEOUTS(Structure):
        ReadIntervalTimeout: _CField[Incomplete, Incomplete, Incomplete]
        ReadTotalTimeoutMultiplier: _CField[Incomplete, Incomplete, Incomplete]
        ReadTotalTimeoutConstant: _CField[Incomplete, Incomplete, Incomplete]
        WriteTotalTimeoutMultiplier: _CField[
            Incomplete,
            Incomplete,
            Incomplete,
        ]
        WriteTotalTimeoutConstant: _CField[Incomplete, Incomplete, Incomplete]

    type COMMTIMEOUTS = _COMMTIMEOUTS
    GetLastError: _NamedFuncPointer
    LPOVERLAPPED: type[_Pointer[_OVERLAPPED]]
    LPDWORD: type[_Pointer[DWORD]]
    GetOverlappedResult: _NamedFuncPointer
    ResetEvent: _NamedFuncPointer
    LPCVOID = c_void_p
    WriteFile: _NamedFuncPointer
    LPVOID = c_void_p
    ReadFile: _NamedFuncPointer
    CloseHandle: _NamedFuncPointer
    ClearCommBreak: _NamedFuncPointer
    LPCOMSTAT: type[_Pointer[_COMSTAT]]
    ClearCommError: _NamedFuncPointer
    SetupComm: _NamedFuncPointer
    EscapeCommFunction: _NamedFuncPointer
    GetCommModemStatus: _NamedFuncPointer
    LPDCB: type[_Pointer[_DCB]]
    GetCommState: _NamedFuncPointer
    LPCOMMTIMEOUTS: type[_Pointer[_COMMTIMEOUTS]]
    GetCommTimeouts: _NamedFuncPointer
    PurgeComm: _NamedFuncPointer
    SetCommBreak: _NamedFuncPointer
    SetCommMask: _NamedFuncPointer
    SetCommState: _NamedFuncPointer
    SetCommTimeouts: _NamedFuncPointer
    WaitForSingleObject: _NamedFuncPointer
    WaitCommEvent: _NamedFuncPointer
    CancelIoEx: _NamedFuncPointer
    ONESTOPBIT: int
    TWOSTOPBITS: int
    NOPARITY: int
    ODDPARITY: int
    EVENPARITY: int
    RTS_CONTROL_HANDSHAKE: int
    RTS_CONTROL_ENABLE: int
    DTR_CONTROL_HANDSHAKE: int
    DTR_CONTROL_ENABLE: int
    MS_DSR_ON: int
    EV_RING: int
    EV_PERR: int
    EV_ERR: int
    SETXOFF: int
    EV_RXCHAR: int
    GENERIC_WRITE: int
    PURGE_TXCLEAR: int
    FILE_FLAG_OVERLAPPED: int
    EV_DSR: int
    MAXDWORD: int
    EV_RLSD: int
    ERROR_IO_PENDING: int
    MS_CTS_ON: int
    EV_EVENT1: int
    EV_RX80FULL: int
    PURGE_RXABORT: int
    FILE_ATTRIBUTE_NORMAL: int
    PURGE_TXABORT: int
    SETXON: int
    OPEN_EXISTING: int
    MS_RING_ON: int
    EV_TXEMPTY: int
    EV_RXFLAG: int
    MS_RLSD_ON: int
    GENERIC_READ: int
    EV_EVENT2: int
    EV_CTS: int
    EV_BREAK: int
    PURGE_RXCLEAR: int
    class N11_OVERLAPPED4DOLLAR_48E(Union):
        Offset: _CField[Incomplete, Incomplete, Incomplete]
        OffsetHigh: _CField[Incomplete, Incomplete, Incomplete]
        Pointer: _CField[Incomplete, Incomplete, Incomplete]

    class N11_OVERLAPPED4DOLLAR_484DOLLAR_49E(Structure):
        Offset: _CField[Incomplete, Incomplete, Incomplete]
        OffsetHigh: _CField[Incomplete, Incomplete, Incomplete]

    type PVOID = c_void_p
    __all__ = [
        "COMMTIMEOUTS",
        "COMSTAT",
        "DCB",
        "DTR_CONTROL_ENABLE",
        "DTR_CONTROL_HANDSHAKE",
        "ERROR_IO_PENDING",
        "EVENPARITY",
        "EV_BREAK",
        "EV_CTS",
        "EV_DSR",
        "EV_ERR",
        "EV_EVENT1",
        "EV_EVENT2",
        "EV_PERR",
        "EV_RING",
        "EV_RLSD",
        "EV_RX80FULL",
        "EV_RXCHAR",
        "EV_RXFLAG",
        "EV_TXEMPTY",
        "FILE_ATTRIBUTE_NORMAL",
        "FILE_FLAG_OVERLAPPED",
        "GENERIC_READ",
        "GENERIC_WRITE",
        "LPCOMMTIMEOUTS",
        "LPCOMSTAT",
        "LPCVOID",
        "LPDCB",
        "LPDWORD",
        "LPOVERLAPPED",
        "LPSECURITY_ATTRIBUTES",
        "LPVOID",
        "MAXDWORD",
        "MS_CTS_ON",
        "MS_DSR_ON",
        "MS_RING_ON",
        "MS_RLSD_ON",
        "N11_OVERLAPPED4DOLLAR_48E",
        "N11_OVERLAPPED4DOLLAR_484DOLLAR_49E",
        "NOPARITY",
        "ODDPARITY",
        "ONESTOPBIT",
        "OPEN_EXISTING",
        "OVERLAPPED",
        "PURGE_RXABORT",
        "PURGE_RXCLEAR",
        "PURGE_TXABORT",
        "PURGE_TXCLEAR",
        "PVOID",
        "RTS_CONTROL_ENABLE",
        "RTS_CONTROL_HANDSHAKE",
        "SETXOFF",
        "SETXON",
        "TWOSTOPBITS",
        "ULONG_PTR",
        "_COMMTIMEOUTS",
        "_COMSTAT",
        "_DCB",
        "_OVERLAPPED",
        "_SECURITY_ATTRIBUTES",
        "ClearCommBreak",
        "ClearCommError",
        "CloseHandle",
        "CreateEvent",
        "CreateEventW",
        "CreateFile",
        "CreateFileW",
        "EscapeCommFunction",
        "GetCommModemStatus",
        "GetCommState",
        "GetCommTimeouts",
        "GetLastError",
        "GetOverlappedResult",
        "PurgeComm",
        "ReadFile",
        "ResetEvent",
        "SetCommBreak",
        "SetCommMask",
        "SetCommState",
        "SetCommTimeouts",
        "SetupComm",
        "WriteFile",
    ]
