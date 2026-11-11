from collections.abc import Callable
from typing import Any, ClassVar

from _typeshed import Incomplete
from setuptools.dist import Distribution

from .._distutils.command import install as orig

class install(orig.install):
    distribution: Distribution
    user_options: ClassVar[list[tuple[str, str | None, str]]]
    boolean_options: ClassVar[list[str]]
    new_commands: ClassVar[list[tuple[str, Callable[[Any], bool]] | None]]
    old_and_unmanageable: Incomplete
    single_version_externally_managed: bool | None
    def initialize_options(self) -> None: ...
    def finalize_options(self) -> None: ...
    path_file: Incomplete
    extra_dirs: str
    def handle_extra_path(self): ...
