import sys
from collections.abc import Iterable, Mapping, Sequence
from types import CodeType
from typing import ClassVar, Final, Literal

from _typeshed import FileDescriptorOrPath, StrOrBytesPath, StrPath, Unused
from PyInstaller.building import _PyiBlockCipher
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import Target, _TOCTuple
from PyInstaller.building.splash import Splash
from PyInstaller.utils.win32.versioninfo import VSVersionInfo

if sys.platform == "darwin":
    type _TargetArch = Literal["x86_64", "arm64", "universal2"]
    type _SupportedTargetArchParam = _TargetArch | None
    type _CodesignIdentity = str | None
    type _CodesignIdentityParam = str | None
else:
    type _TargetArch = None
    type _SupportedTargetArchParam = Unused
    type _CodesignIdentity = None
    type _CodesignIdentityParam = Unused
if sys.platform == "win32":
    type _Icon = list[StrPath] | str
    type _IconParam = StrPath | list[StrPath] | None
elif sys.platform == "darwin":
    type _Icon = list[StrPath] | None
    type _IconParam = StrPath | list[StrPath] | None
else:
    type _Icon = None
    type _IconParam = Unused
if sys.platform == "win32":
    type _VersionSrc = VSVersionInfo | None
    type _VersionParam = VSVersionInfo | StrOrBytesPath | None
    type _Manifest = bytes
    type _ManifestParam = str | None
else:
    type _VersionSrc = None
    type _VersionParam = Unused
    type _Manifest = None
    type _ManifestParam = Unused
type _HideConsole = (
    Literal["hide-early", "minimize-early", "hide-late", "minimize-late"]
    | None
)

class PYZ(Target):
    name: str
    cipher: _PyiBlockCipher
    dependencies: list[_TOCTuple]
    toc: list[_TOCTuple]
    code_dict: dict[str, CodeType]
    def __init__(
        self,
        *tocs: Iterable[_TOCTuple],
        name: str | None = None,
        cipher: _PyiBlockCipher = None,
    ) -> None: ...
    def assemble(self) -> None: ...

class PKG(Target):
    xformdict: ClassVar[dict[str, str]]
    toc: list[_TOCTuple]
    cdict: Mapping[str, bool]
    python_lib_name: str
    name: str
    exclude_binaries: bool
    strip_binaries: bool
    upx_binaries: bool
    upx_exclude: Iterable[str]
    target_arch: _TargetArch | None
    codesign_identity: _CodesignIdentity
    entitlements_file: FileDescriptorOrPath | None
    def __init__(
        self,
        toc: Iterable[_TOCTuple],
        python_lib_name: str,
        name: str | None = None,
        cdict: Mapping[str, bool] | None = None,
        exclude_binaries: bool = False,
        strip_binaries: bool = False,
        upx_binaries: bool = False,
        upx_exclude: Iterable[str] | None = None,
        target_arch: _SupportedTargetArchParam = None,
        codesign_identity: _CodesignIdentityParam = None,
        entitlements_file: FileDescriptorOrPath | None = None,
    ) -> None: ...
    def assemble(self) -> None: ...

class EXE(Target):
    exclude_binaries: bool
    bootloader_ignore_signals: bool
    console: bool
    hide_console: _HideConsole
    disable_windowed_traceback: bool
    debug: bool
    name: str
    icon: _Icon
    versrsrc: _VersionSrc
    manifest: _Manifest
    embed_manifest: bool
    resources: Sequence[str]
    strip: bool
    upx_exclude: Iterable[str]
    runtime_tmpdir: str | None
    contents_directory: str | None
    append_pkg: bool
    uac_admin: bool
    uac_uiaccess: bool
    argv_emulation: bool
    target_arch: _TargetArch
    codesign_identity: _CodesignIdentity
    entitlements_file: FileDescriptorOrPath | None
    upx: bool
    pkgname: str
    toc: list[_TOCTuple]
    pkg: PKG
    dependencies: list[_TOCTuple]
    exefiles: list[_TOCTuple]
    def __init__(
        self,
        *args: Iterable[_TOCTuple] | PYZ | Splash,
        exclude_binaries: bool = False,
        bootloader_ignore_signals: bool = False,
        console: bool = True,
        hide_console: _HideConsole = None,
        disable_windowed_traceback: bool = False,
        debug: bool = False,
        name: str | None = None,
        icon: _IconParam = None,
        version: _VersionParam = None,
        manifest: _ManifestParam = None,
        embed_manifest: Literal[True] = True,
        resources: Sequence[str] = ...,
        strip: bool = False,
        upx_exclude: Iterable[str] = ...,
        runtime_tmpdir: str | None = None,
        contents_directory: str = "_internal",
        append_pkg: bool = True,
        uac_admin: bool = False,
        uac_uiaccess: bool = False,
        argv_emulation: bool = False,
        target_arch: _SupportedTargetArchParam = None,
        codesign_identity: _CodesignIdentityParam = None,
        entitlements_file: FileDescriptorOrPath | None = None,
        upx: bool = False,
        cdict: Mapping[str, bool] | None = None,
    ) -> None: ...
    mtm: float
    def assemble(self) -> None: ...

class COLLECT(Target):
    strip_binaries: bool
    upx_exclude: Iterable[str]
    console: bool
    target_arch: _TargetArch | None
    codesign_identity: _CodesignIdentity
    entitlements_file: FileDescriptorOrPath | None
    upx_binaries: bool
    name: str
    toc: list[_TOCTuple]
    def __init__(
        self,
        *args: Iterable[_TOCTuple] | EXE,
        strip: bool = False,
        upx_exclude: Iterable[str] = ...,
        upx: bool = False,
        name: str,
    ) -> None: ...
    def assemble(self) -> None: ...

class MERGE:
    def __init__(self, *args: tuple[Analysis, Unused, str]) -> None: ...

UNCOMPRESSED: Final = False
COMPRESSED: Final = True
