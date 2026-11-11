from _typeshed import StrOrBytesPath

__all__ = ["NetrcParseError", "netrc"]

class NetrcParseError(Exception):
    filename: str | None
    lineno: int | None
    msg: str
    def __init__(
        self,
        msg: str,
        filename: StrOrBytesPath | None = None,
        lineno: int | None = None,
    ) -> None: ...

type _NetrcTuple = tuple[str, str, str]

class netrc:
    hosts: dict[str, _NetrcTuple]
    macros: dict[str, list[str]]
    def __init__(self, file: StrOrBytesPath | None = None) -> None: ...
    def authenticators(self, host: str) -> _NetrcTuple | None: ...
