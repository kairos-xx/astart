"""External signatures from typeshed, ``py.typed`` and stub packages.

Three sources answer "what does this library call look like" without
executing anything:

- a typeshed root (``stdlib/`` plus ``stubs/<dist>/`` packages),
- installed packages that ship a ``py.typed`` marker (``.pyi`` files win,
  annotated ``.py`` files fall back per PEP 561),
- stub-only ``*-stubs`` packages, which take precedence over the inline
  package per PEP 561.

Lookups are lazy: a module file is parsed at most once, and misses are
cached as empty results.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Protocol, final

from astart.semantic.stubs import StubIndex, StubSignature, stub_signatures

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from astart.semantic.typing_contracts import CallableContract


class _ClientLookup(Protocol):
    """An optional external stub backend such as ``typeshed_client``."""

    def lookup(self, *, qualified_name: str) -> tuple[StubSignature, ...]:
        """Resolve a dotted name to matching stub signatures.

        Args:
            qualified_name (str): Dotted name such as ``"os.getcwd"``.

        Returns:
            Matching signatures, empty when undeclared.

        """
        ...


@final
class Constants:
    """Group module-level constants.

    Attributes:
        stub_suffix (Final[str]): Package-directory suffix naming a stub-only
            package.
        marker (Final[str]): File marking a package as inline-typed.
        stubs_dir (Final[str]): Typeshed subdirectory holding third-party
            stubs.
        init_file (Final[str]): Package-initializer stub filename.
        init_source (Final[str]): Package-initializer source filename.
        pyi (Final[str]): Stub extension.
        py (Final[str]): Source extension.
        max_stub_bytes (Final[int]): Cap on parsed stub size.

    """

    stub_suffix: Final[str] = "-stubs"
    marker: Final[str] = "py.typed"
    stubs_dir: Final[str] = "stubs"
    init_file: Final[str] = "__init__.pyi"
    init_source: Final[str] = "__init__.py"
    pyi: Final[str] = ".pyi"
    py: Final[str] = ".py"
    max_stub_bytes: Final[int] = 1_000_000


@final
@dataclass(frozen=True, slots=True)
class PackageRoot:
    """Where one import package's signatures live.

    Attributes:
        package (str): Top-level import name the root provides.
        directory (Path | None): The package directory itself (contains
            ``__init__``
            and submodules), or ``None`` for single-module stubs.
        module_file (Path | None): A lone ``foo.pyi`` module file, or ``None``.
        allow_source (bool): Whether annotated ``.py`` files may be read when
            no ``.pyi``
            exists — true for inline ``py.typed`` packages only.

    """

    package: str
    directory: Path | None = None
    module_file: Path | None = None
    allow_source: bool = False


def _package_roots(*, site: Path) -> list[PackageRoot]:
    """Find package signature roots inside one site directory.

    Args:
        site (Path): A ``site-packages``-like directory or a typeshed
            ``stubs/<dist>/`` directory.

    Returns:
        list[PackageRoot]: Roots for stub-only and ``py.typed`` packages found
            there.

    """
    roots: list[PackageRoot] = []
    try:
        entries: list[Path] = sorted(site.iterdir())
    except OSError:
        return roots
    for entry in entries:
        if entry.is_dir() and entry.name.endswith(Constants.stub_suffix):
            package: str = entry.name.removesuffix(Constants.stub_suffix)
            inner: Path = entry / package
            if inner.is_dir():
                roots.append(
                    PackageRoot(package=package, directory=inner),
                )
            elif (entry / Constants.init_file).is_file():
                roots.append(
                    PackageRoot(package=package, directory=entry),
                )
        elif entry.is_dir() and (entry / Constants.marker).is_file():
            roots.append(
                PackageRoot(
                    package=entry.name,
                    directory=entry,
                    allow_source=True,
                ),
            )
        elif entry.is_file() and entry.suffix == Constants.pyi:
            roots.append(
                PackageRoot(package=entry.stem, module_file=entry),
            )
    return roots


def _typeshed_roots(*, stubs: Path) -> list[PackageRoot]:
    """Find package roots inside a typeshed ``stubs/`` directory.

    Each ``stubs/<dist>/`` directory holds the distribution's packages
    and module stubs directly, so every package directory and ``.pyi``
    file inside it is a root.

    Args:
        stubs (Path): The typeshed ``stubs/`` directory.

    Returns:
        list[PackageRoot]: One root per declared package or module stub.

    """
    roots: list[PackageRoot] = []
    try:
        distributions: list[Path] = sorted(stubs.iterdir())
    except OSError:
        return roots
    for distribution in distributions:
        if not distribution.is_dir():
            continue
        try:
            entries: list[Path] = sorted(distribution.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir():
                roots.append(
                    PackageRoot(package=entry.name, directory=entry),
                )
            elif entry.is_file() and entry.suffix == Constants.pyi:
                roots.append(
                    PackageRoot(package=entry.stem, module_file=entry),
                )
    return roots


def find_library_roots(
    *,
    site_packages: Iterable[Path] = (),
    typeshed: Path | None = None,
) -> tuple[PackageRoot, ...]:
    """Discover package signature roots.

    Args:
        site_packages (Iterable[Path]): ``site-packages`` -like directories to
            inspect.
        typeshed (Path | None): A typeshed root; its ``stubs/<dist>/`` packages
            count as package roots too (``stdlib/`` itself
            is handled by the separate typeshed index).

    Returns:
        tuple[PackageRoot, ...]: Roots, stub-only packages before inline ones
            for each name.

    """
    roots: list[PackageRoot] = []
    if typeshed is not None:
        stubs: Path = typeshed / Constants.stubs_dir
        if stubs.is_dir():
            roots.extend(_typeshed_roots(stubs=stubs))
    for site in site_packages:
        roots.extend(_package_roots(site=site))
    stubs_first: list[PackageRoot] = sorted(
        roots,
        key=lambda root: (root.package, root.allow_source),
    )
    return tuple(stubs_first)


@final
class LibraryIndex:
    """External signature lookup across all configured roots.

    Attributes:
        typeshed: Typeshed index for stdlib names, or ``None``.

    """

    def __init__(
        self,
        *,
        typeshed: Path | None = None,
        roots: Iterable[PackageRoot] = (),
        client: _ClientLookup | None = None,
    ) -> None:
        """Build the index over a typeshed root and package roots.

        Args:
            typeshed (Path | None): Typeshed root (``stdlib/`` layout), or
                ``None``.
            roots (Iterable[PackageRoot]): Package roots, earliest winning on
                name collisions.
            client (_ClientLookup | None): Optional external backend consulted
                before
                the hand-written readers, or ``None``.

        """
        self.typeshed: StubIndex | None = (
            StubIndex(root=typeshed) if typeshed is not None else None
        )
        self._client: _ClientLookup | None = client
        self._roots: dict[str, list[PackageRoot]] = {}
        for root in roots:
            self._roots.setdefault(root.package, []).append(root)
        self._modules: dict[tuple[str, Path], tuple[StubSignature, ...]] = {}
        self._misses: set[tuple[str, Path]] = set()

    def lookup(self, *, qualified_name: str) -> tuple[StubSignature, ...]:
        """Resolve a dotted name against external signatures.

        An optional client answers first; then typeshed; then each
        package root claiming the leading package name, earliest root
        first.

        Args:
            qualified_name (str): Dotted name such as
                ``"requests.sessions.Session.send"``.

        Returns:
            tuple[StubSignature, ...]: Matching signatures, empty when nothing
                declares the name.

        """
        if self._client is not None:
            found_client: tuple[StubSignature, ...] = self._client.lookup(
                qualified_name=qualified_name,
            )
            if found_client:
                return found_client
        if self.typeshed is not None:
            found: tuple[StubSignature, ...] = self.typeshed.lookup(
                qualified_name=qualified_name,
            )
            if found:
                return found
        pieces: list[str] = qualified_name.split(sep=".")
        if not pieces:
            return ()
        for root in self._roots.get(pieces[0], ()):
            matched: tuple[StubSignature, ...] = self._lookup_root(
                root=root,
                pieces=pieces,
            )
            if matched:
                return matched
        return ()

    def contract(self, *, qualified_name: str) -> CallableContract | None:
        """Return the binding contract of an external callable.

        Args:
            qualified_name (str): Dotted name such as ``"requests.get"``.

        Returns:
            CallableContract | None: The first declared contract, or ``None``.

        """
        for signature in self.lookup(qualified_name=qualified_name):
            if signature.contract is not None:
                return signature.contract
        return None

    def _lookup_root(
        self,
        *,
        root: PackageRoot,
        pieces: list[str],
    ) -> tuple[StubSignature, ...]:
        """Try one package root for a dotted name.

        Args:
            root (PackageRoot): The package's signature root.
            pieces (list[str]): The dotted name split on dots.

        Returns:
            tuple[StubSignature, ...]: Matching signatures.

        """
        for length in range(len(pieces), 0, -1):
            module_name: str = ".".join(pieces[:length])
            file: Path | None = self._module_file(
                root=root,
                relative=pieces[1:length],
            )
            if file is None:
                continue
            key: tuple[str, Path] = (module_name, file)
            if key in self._misses:
                continue
            if key not in self._modules:
                self._modules[key] = self._parse(
                    file=file,
                    module_name=module_name,
                )
            signatures: tuple[StubSignature, ...] = self._modules[key]
            if not signatures:
                self._misses.add(key)
                continue
            qualified: str = ".".join(pieces)
            matched: tuple[StubSignature, ...] = tuple(
                signature
                for signature in signatures
                if signature.qualified_name == qualified
            )
            if matched:
                return matched
        return ()

    @staticmethod
    def _module_file(
        *,
        root: PackageRoot,
        relative: list[str],
    ) -> Path | None:
        """Locate the file providing one module of a package.

        ``.pyi`` always wins over ``.py``; a package's ``__init__`` answers
        both the package name and its own submodules' parents.

        Args:
            root (PackageRoot): The package's signature root.
            relative (list[str]): Module path below the package name —
                empty means the package module itself.

        Returns:
            Path | None: The file, or ``None``.

        """
        if root.module_file is not None:
            return root.module_file if not relative else None
        if root.directory is None:
            return None
        if not relative:
            for name in (Constants.init_file, Constants.init_source):
                candidate: Path = root.directory / name
                if (
                    name.endswith(Constants.pyi) or root.allow_source
                ) and candidate.is_file():
                    return candidate
            return None
        stem: Path = root.directory.joinpath(*relative)
        candidates: list[Path] = [
            stem.with_suffix(suffix=Constants.pyi),
            stem / Constants.init_file,
        ]
        if root.allow_source:
            candidates.extend(
                (
                    stem.with_suffix(suffix=Constants.py),
                    stem / Constants.init_source,
                ),
            )
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def _parse(
        *,
        file: Path,
        module_name: str,
    ) -> tuple[StubSignature, ...]:
        """Parse one signature file with a size cap.

        Args:
            file (Path): The ``.pyi``/``.py`` file.
            module_name (str): Dotted name it provides.

        Returns:
            tuple[StubSignature, ...]: Its declared signatures, empty when
                unreadable or oversized.

        """
        try:
            if file.stat().st_size > Constants.max_stub_bytes:
                return ()
            source: str = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ()
        return stub_signatures(
            source=source,
            module_name=module_name,
            chosen=str(object=file),
        )
