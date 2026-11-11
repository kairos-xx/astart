from collections.abc import Mapping, Sequence

type _Cap = dict[str, str | int]
__all__ = ["findmatch", "getcaps"]

def findmatch(
    caps: Mapping[str, list[_Cap]],
    MIMEtype: str,
    key: str = "view",
    filename: str = "/dev/null",
    plist: Sequence[str] = [],
) -> tuple[str | None, _Cap | None]: ...
def getcaps() -> dict[str, list[_Cap]]: ...
