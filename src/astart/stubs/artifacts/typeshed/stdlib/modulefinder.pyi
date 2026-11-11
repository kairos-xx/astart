from collections.abc import Container, Iterable, Iterator, Sequence
from types import CodeType
from typing import IO, Any

packagePathMap: dict[str, list[str]]

def AddPackagePath(packagename: str, path: str) -> None: ...

replacePackageMap: dict[str, str]

def ReplacePackage(oldname: str, newname: str) -> None: ...

class Module:
    def __init__(
        self,
        name: str,
        file: str | None = None,
        path: str | None = None,
    ) -> None: ...

class ModuleFinder:
    modules: dict[str, Module]
    path: list[str]
    badmodules: dict[str, dict[str, int]]
    debug: int
    indent: int
    excludes: Container[str]
    replace_paths: Sequence[tuple[str, str]]
    def __init__(
        self,
        path: list[str] | None = None,
        debug: int = 0,
        excludes: Container[str] | None = None,
        replace_paths: Sequence[tuple[str, str]] | None = None,
    ) -> None: ...
    def msg(self, level: int, str: str, *args: Any) -> None: ...
    def msgin(self, *args: Any) -> None: ...
    def msgout(self, *args: Any) -> None: ...
    def run_script(self, pathname: str) -> None: ...
    def load_file(self, pathname: str) -> None: ...
    def import_hook(
        self,
        name: str,
        caller: Module | None = None,
        fromlist: list[str] | None = None,
        level: int = -1,
    ) -> Module | None: ...
    def determine_parent(
        self,
        caller: Module | None,
        level: int = -1,
    ) -> Module | None: ...
    def find_head_package(
        self,
        parent: Module,
        name: str,
    ) -> tuple[Module, str]: ...
    def load_tail(self, q: Module, tail: str) -> Module: ...
    def ensure_fromlist(
        self,
        m: Module,
        fromlist: Iterable[str],
        recursive: int = 0,
    ) -> None: ...
    def find_all_submodules(self, m: Module) -> Iterable[str]: ...
    def import_module(
        self,
        partname: str,
        fqname: str,
        parent: Module,
    ) -> Module | None: ...
    def load_module(
        self,
        fqname: str,
        fp: IO[str],
        pathname: str,
        file_info: tuple[str, str, str],
    ) -> Module: ...
    def scan_opcodes(
        self,
        co: CodeType,
    ) -> Iterator[tuple[str, tuple[Any, ...]]]: ...
    def scan_code(self, co: CodeType, m: Module) -> None: ...
    def load_package(self, fqname: str, pathname: str) -> Module: ...
    def add_module(self, fqname: str) -> Module: ...
    def find_module(
        self,
        name: str,
        path: str | None,
        parent: Module | None = None,
    ) -> tuple[IO[Any] | None, str | None, tuple[str, str, int]]: ...
    def report(self) -> None: ...
    def any_missing(self) -> list[str]: ...
    def any_missing_maybe(self) -> tuple[list[str], list[str]]: ...
    def replace_paths_in_code(self, co: CodeType) -> CodeType: ...

def test() -> ModuleFinder | None: ...
