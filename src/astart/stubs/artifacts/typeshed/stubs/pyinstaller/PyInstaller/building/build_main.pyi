from collections.abc import Iterable
from typing import Any, Literal

from _typeshed import StrPath
from PyInstaller.building import _PyiBlockCipher
from PyInstaller.building.datastruct import Target, _TOCTuple

class Analysis(Target):
    hooksconfig: dict[str, dict[str, object]]
    pure: list[_TOCTuple]
    zipped_data: list[_TOCTuple]
    scripts: list[_TOCTuple]
    binaries: list[_TOCTuple]
    zipfiles: list[_TOCTuple]
    datas: list[_TOCTuple]
    inputs: list[str]
    dependencies: list[_TOCTuple]
    noarchive: bool
    optimize: int
    pathex: list[StrPath]
    hiddenimports: list[str]
    hookspath: list[tuple[StrPath, int]]
    excludes: list[str]
    custom_runtime_hooks: list[StrPath]
    module_collection_mode: dict[str, str]
    def __init__(
        self,
        scripts: Iterable[StrPath],
        pathex: Iterable[StrPath] | None = None,
        binaries: Iterable[tuple[StrPath, StrPath]] | None = None,
        datas: Iterable[tuple[StrPath, StrPath]] | None = None,
        hiddenimports: Iterable[str] | None = None,
        hookspath: Iterable[StrPath] | None = None,
        hooksconfig: dict[str, dict[str, Any]] | None = None,
        excludes: Iterable[str] | None = None,
        runtime_hooks: Iterable[StrPath] | None = None,
        cipher: _PyiBlockCipher = None,
        win_no_prefer_redirects: bool = False,
        win_private_assemblies: bool = False,
        noarchive: bool = False,
        module_collection_mode: dict[str, str] | None = None,
        optimize: Literal[-1, 0, 1, 2] | None = -1,
    ) -> None: ...
