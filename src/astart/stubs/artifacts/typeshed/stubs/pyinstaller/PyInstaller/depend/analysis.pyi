from collections.abc import Iterable

from _typeshed import Incomplete, StrPath, SupportsKeysAndGetItem
from PyInstaller.lib.modulegraph.modulegraph import Alias, Node

type _LazyNode = Iterable[Node] | Iterable[str] | Alias | None
type _Graph = Incomplete

class PyiModuleGraph:
    def __init__(
        self,
        pyi_homepath: str,
        user_hook_dirs: Iterable[StrPath] = (),
        excludes: Iterable[str] = (),
        *,
        path: Iterable[str] | None = None,
        replace_paths: Iterable[tuple[StrPath, StrPath]] = ...,
        implies: SupportsKeysAndGetItem[str, _LazyNode]
        | Iterable[tuple[str, _LazyNode]] = ...,
        graph: _Graph | None = None,
        debug: bool = False,
    ) -> None: ...
