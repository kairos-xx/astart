"""Resolve a qualified name to its definition across stub files."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from sys import platform, version_info
from typing import TYPE_CHECKING, Final, final

from astart.stubs.conditions import Target
from astart.stubs.locate import find_typeshed
from astart.stubs.parser import ImportedName, StubModule, StubName, parse_stub
from astart.stubs.versions import Span, module_available, parse_versions

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        stdlib (Final[str]): Directory of the standard-library stubs.
        stubs (Final[str]): Directory of the third-party stub distributions.
        init (Final[str]): File that makes a stub directory a package.
        suffix (Final[str]): Extension of a stub file.
        depth (Final[int]): Longest import or alias chain that is followed.

    """

    stdlib: Final[str] = "stdlib"
    stubs: Final[str] = "stubs"
    init: Final[str] = "__init__.pyi"
    suffix: Final[str] = ".pyi"
    depth: Final[int] = 16


@final
@dataclass(frozen=True, slots=True)
class Resolved:
    """A name found, with the module that defines it.

    Attributes:
        name (StubName): The definition.
        module (StubModule): The stub module it lives in.
        owner (StubName | None): The class it is a member of, when it is a
            method.

    """

    name: StubName
    module: StubModule
    owner: StubName | None = None


@final
class Resolver:
    """Read stub files lazily and follow names between them."""

    def __init__(self, *, typeshed: Path, target: Target) -> None:
        """Index the layout of a typeshed copy.

        Args:
            typeshed (Path): A typeshed root (``stdlib/`` and ``stubs/``).
            target (Target): The Python version and platform to read the stubs
                for.

        """
        self._root: Path = typeshed
        self._target: Target = target
        versions: Path = typeshed / Constants.stdlib / "VERSIONS"
        self._versions: dict[str, Span] = (
            parse_versions(text=versions.read_text(encoding="utf-8"))
            if versions.is_file()
            else {}
        )
        self._modules: dict[str, StubModule | None] = {}
        self._distributions: dict[str, Path] | None = None

    def module(self, name: str) -> StubModule | None:
        """Read a module's stub, once.

        Args:
            name (str): Dotted module name.

        Returns:
            StubModule | None:
                Its names, or ``None`` when there is no stub or the
                module does not exist in the target Python version.

        """
        if name not in self._modules:
            self._modules[name] = self._load(name=name)
        return self._modules[name]

    def _packages(self) -> dict[str, Path]:
        """Map each top-level third-party package to its stub directory.

        Returns:
            dict[str, Path]: Package name to the ``stubs/<dist>`` directory
                holding it.

        """
        if self._distributions is None:
            found: dict[str, Path] = {}
            base: Path = self._root / Constants.stubs
            if base.is_dir():
                for dist in sorted(base.iterdir()):
                    if not dist.is_dir():
                        continue
                    for entry in sorted(dist.iterdir()):
                        top: str = entry.name.removesuffix(Constants.suffix)
                        if entry.is_dir() or entry.suffix == Constants.suffix:
                            _ = found.setdefault(top, dist)
            self._distributions = found
        return self._distributions

    def _file(self, *, name: str) -> tuple[Path, bool] | None:
        """Find the stub file of a module.

        Args:
            name (str): Dotted module name.

        Returns:
            tuple[Path, bool] | None: The path and whether it is a
                package ``__init__``, or ``None``.

        """
        parts: list[str] = name.split(sep=".")
        roots: list[Path] = [self._root / Constants.stdlib]
        distribution: Path | None = self._packages().get(parts[0])
        if distribution is not None:
            roots.append(distribution)
        for root in roots:
            package: Path = root.joinpath(*parts) / Constants.init
            if package.is_file():
                return package, True
            module: Path = root.joinpath(*parts).with_suffix(
                suffix=Constants.suffix,
            )
            if module.is_file():
                return module, False
        return None

    def _load(self, *, name: str) -> StubModule | None:
        """Parse a module's stub file.

        Args:
            name (str): Dotted module name.

        Returns:
            StubModule | None: The parsed module, or ``None``.

        """
        if not module_available(
            table=self._versions,
            module=name,
            version=self._target.version,
        ):
            return None
        located: tuple[Path, bool] | None = self._file(name=name)
        if located is None:
            return None
        path, package = located
        try:
            source: str = path.read_text(encoding="utf-8")
            return parse_stub(
                source=source,
                module=name,
                package=package,
                target=self._target,
            )
        except (SyntaxError, UnicodeDecodeError, OSError):
            return None

    def resolve(self, qualified: str) -> Resolved | None:
        """Find the definition a dotted name refers to.

        Imports, re-exports, star imports, plain aliases (``X = Y``) and
        class members are followed.

        Args:
            qualified (str): A dotted name such as ``os.path.join``.

        Returns:
            Resolved | None: The definition, or ``None`` when it is not found.

        """
        return self._walk(qualified=qualified, hops=0)

    def resolve_method(
        self,
        *,
        class_name: str,
        method: str,
    ) -> Resolved | None:
        """Find a method on a stub class.

        Args:
            class_name (str): Qualified class name such as ``pathlib.Path``.
            method (str): Method name.

        Returns:
            Resolved | None: The method with its owner set, or ``None``.

        """
        found: Resolved | None = self.resolve(
            qualified=f"{class_name}.{method}",
        )
        return found if found is not None and found.owner is not None else None

    def _walk(self, *, qualified: str, hops: int) -> Resolved | None:
        """Resolve a dotted name, bounded against import cycles.

        Args:
            qualified (str): A dotted name.
            hops (int): Links followed so far.

        Returns:
            Resolved | None: The definition, or ``None``.

        """
        if hops > Constants.depth:
            return None
        parts: list[str] = qualified.split(sep=".")
        for end in range(len(parts), 0, -1):
            module: StubModule | None = self.module(name=".".join(parts[:end]))
            if module is None:
                continue
            if end == len(parts):
                return None
            return self._member(
                module=module,
                path=parts[end:],
                hops=hops,
            )
        return None

    def _member(
        self,
        *,
        module: StubModule,
        path: list[str],
        hops: int,
    ) -> Resolved | None:
        """Walk names inside a module, through classes and imports.

        Args:
            module (StubModule): The module the walk starts in.
            path (list[str]): Remaining names.
            hops (int): Links followed so far.

        Returns:
            Resolved | None: The definition, or ``None``.

        """
        scope: dict[str, StubName] = module.names
        owner: StubName | None = None
        current: StubName | None = None
        home: StubModule = module
        for index, part in enumerate(iterable=path):
            current = scope.get(part)
            if current is None:
                starred: tuple[StubName, StubModule] | None = self._starred(
                    module=module,
                    part=part,
                )
                if starred is None:
                    return None
                current, home = starred
            if current.kind == "import" or current.alias_of is not None:
                return self._follow(
                    current=current,
                    module=home,
                    rest=path[index + 1 :],
                    hops=hops,
                )
            if index == len(path) - 1:
                return Resolved(name=current, module=home, owner=owner)
            if current.kind != "class":
                return None
            owner, scope = current, current.children
        return None

    def _starred(
        self,
        *,
        module: StubModule,
        part: str,
    ) -> tuple[StubName, StubModule] | None:
        """Look a name up in the modules a stub star-imports.

        Args:
            module (StubModule): The importing module.
            part (str): The name.

        Returns:
            tuple[StubName, StubModule] | None: The exported definition and the
                module that defines it, or ``None``.

        """
        for star in module.stars:
            other: StubModule | None = self.module(name=star)
            if other is None:
                continue
            found: StubName | None = other.names.get(part)
            if found is not None and found.exported:
                return found, other
        return None

    def _follow(
        self,
        *,
        current: StubName,
        module: StubModule,
        rest: list[str],
        hops: int,
    ) -> Resolved | None:
        """Follow an import or alias to the name it stands for.

        Args:
            current (StubName): The import or alias entry.
            module (StubModule): The module it appears in.
            rest (list[str]): Names still to walk after it.
            hops (int): Links followed so far.

        Returns:
            Resolved | None: The definition, or ``None``.

        """
        target: str | None
        if current.imported is not None:
            target = _qualified(imported=current.imported)
        elif current.alias_of is not None:
            target = _alias(module=module, text=current.alias_of)
        else:
            target = None
        if target is None:
            return None
        return self._walk(qualified=".".join([target, *rest]), hops=hops + 1)


def _qualified(*, imported: ImportedName) -> str:
    """Spell what an import refers to.

    Args:
        imported (ImportedName): The import record.

    Returns:
        str: ``module`` or ``module.name``.

    """
    return (
        imported.module
        if imported.name is None
        else f"{imported.module}.{imported.name}"
    )


def _alias(*, module: StubModule, text: str) -> str:
    """Spell the target of an ``X = Y`` alias.

    Args:
        module (StubModule): The module with the assignment.
        text (str): The right-hand side as dotted text.

    Returns:
        str: A qualified name: the module's own name for a bare name, or the
            name as written for a dotted one (resolved from the root).

    """
    head, _, tail = text.partition(".")
    entry: StubName | None = module.names.get(head)
    if entry is not None and entry.imported is not None:
        base: str = _qualified(imported=entry.imported)
        return base if not tail else f"{base}.{tail}"
    return f"{module.name}.{text}"


@cache
def default_resolver(
    version: tuple[int, int],
    platform: str,
) -> Resolver | None:
    """Build the process-wide resolver for a target, once.

    Args:
        version (tuple[int, int]): Python ``(major, minor)``.
        platform (str): ``sys.platform`` value.

    Returns:
        Resolver | None: A resolver over the typeshed copy found on
            this machine, or ``None`` when there is none.

    """
    root: Path | None = find_typeshed()
    if root is None:
        return None
    return Resolver(
        typeshed=root,
        target=Target(version=version, platform=platform),
    )


def host_resolver() -> Resolver | None:
    """Give the resolver for the running Python and platform.

    Returns:
        Resolver | None:
            The process-wide resolver, or ``None`` without a typeshed copy.

    """
    return default_resolver(
        version=(version_info.major, version_info.minor),
        platform=platform,
    )
