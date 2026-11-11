"""Optional ``typeshed_client`` backend for external stub lookup.

``typeshed_client`` is a third-party stub finder. When it is installed,
:class:`TypeshedClientIndex` answers ``lookup`` queries through it and
the hand-written readers in :mod:`astart.project.libraries` stay the
default and the fallback. The package is imported lazily, so astart
works identically without it.

"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from sys import platform, version_info
from typing import TYPE_CHECKING, Final, Protocol, cast, final

from astart.semantic.stubs import StubSignature, stub_signatures

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        max_stub_bytes (Final[int]): Cap on parsed stub size.
        package (Final[str]): Module name of the optional dependency.
        client_errors (Final[tuple[type[Exception], ...]]): Exception types a
            client call may raise.

    """

    max_stub_bytes: Final[int] = 1_000_000
    package: Final[str] = "typeshed_client"
    client_errors: Final[tuple[type[Exception], ...]] = (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    )


class _OpaqueContext(Protocol):
    """Opaque search context ``typeshed_client`` returns and accepts."""


class _ClientModule(Protocol):
    """The two ``typeshed_client`` functions the adapter calls."""

    def get_search_context(
        self,
        *,
        typeshed: Path | None,
        search_path: tuple[Path, ...] | None,
        version: tuple[int, int],
        platform: str,
    ) -> _OpaqueContext:
        """Build the search context for stub lookups.

        Args:
            typeshed (Path | None): Typeshed root overriding the bundled copy.
            search_path (tuple[Path, ...] | None): Directories searched for
                stubs.
            version (tuple[int, int]): Python ``(major, minor)`` to read stubs
                for.
            platform (str): ``sys.platform`` value the stubs target.

        Returns:
            The opaque context later passed to ``get_stub_file``.

        """
        ...

    def get_stub_file(
        self,
        module_name: str,
        *,
        search_context: _OpaqueContext | None,
    ) -> Path | None:
        """Locate the stub file declaring ``module_name``.

        Args:
            module_name (str): Dotted module name.
            search_context (_OpaqueContext | None): Context from
                ``get_search_context``.

        Returns:
            The stub file path, or ``None`` when undeclared.

        """
        ...


@final
@dataclass(frozen=True, slots=True)
class ClientConfig:
    """Search settings forwarded to ``typeshed_client``.

    Attributes:
        typeshed (Path | None): Typeshed root overriding the bundled copy.
        search_path (tuple[Path, ...] | None): Directories searched for stubs.
        version (tuple[int, int] | None): Python ``(major, minor)`` to read
            stubs for.
        platform (str | None): ``sys.platform`` value the stubs target.

    """

    typeshed: Path | None = None
    search_path: tuple[Path, ...] | None = None
    version: tuple[int, int] | None = None
    platform: str | None = None


@final
class TypeshedClientIndex:
    """Answer dotted-name lookups through ``typeshed_client``.

    The adapter reuses :func:`astart.semantic.stubs.stub_signatures` to
    extract signatures, so results carry the same ``StubSignature``
    shape as the hand-written readers. Every failure — missing package,
    missing stub, oversized or unparsable file — resolves to ``()``.

    """

    def __init__(self, *, config: ClientConfig | None = None) -> None:
        """Prepare a lazily-bound client index.

        Args:
            config (ClientConfig | None): Search settings, or ``None`` for host
                defaults.

        """
        self._config: ClientConfig = config or ClientConfig()
        self._context: _OpaqueContext | None = None
        self._unavailable: bool = False
        self._modules: dict[str, tuple[StubSignature, ...]] = {}

    def available(self) -> bool:
        """Report whether ``typeshed_client`` can be imported.

        Returns:
            bool: ``True`` when the optional dependency is present.

        """
        return self._client() is not None

    def lookup(self, *, qualified_name: str) -> tuple[StubSignature, ...]:
        """Resolve a dotted name against ``typeshed_client`` stubs.

        Args:
            qualified_name (str): Dotted name such as
                ``"requests.sessions.Session.send"``.

        Returns:
            tuple[StubSignature, ...]: Matching signatures, empty when the
                client
                is unavailable or nothing declares the name.

        """
        client: _ClientModule | None = self._client()
        if client is None:
            return ()
        pieces: list[str] = qualified_name.split(sep=".")
        for end in range(len(pieces), 0, -1):
            module_name: str = ".".join(pieces[:end])
            signatures: tuple[StubSignature, ...] = self._module(
                client=client,
                module_name=module_name,
            )
            matched: tuple[StubSignature, ...] = tuple(
                item
                for item in signatures
                if item.qualified_name == qualified_name
            )
            if matched:
                return matched
        return ()

    def _client(self) -> _ClientModule | None:
        """Import ``typeshed_client`` once, or mark it unavailable.

        Returns:
            _ClientModule | None: The imported module, or ``None`` when absent.

        """
        if self._unavailable:
            return None
        try:
            return cast(
                typ="_ClientModule",
                val=import_module(name=Constants.package),
            )
        except ImportError:
            self._unavailable = True
            return None

    def _context_for(self, *, client: _ClientModule) -> _OpaqueContext | None:
        """Build the search context once.

        Args:
            client (_ClientModule): The imported ``typeshed_client`` module.

        Returns:
            _OpaqueContext | None: The search context, or ``None`` on failure.

        """
        if self._context is not None:
            return self._context
        config: ClientConfig = self._config
        try:
            self._context = client.get_search_context(
                typeshed=config.typeshed,
                search_path=config.search_path,
                version=config.version
                or (version_info.major, version_info.minor),
                platform=config.platform or platform,
            )
        except Constants.client_errors:
            self._unavailable = True
            return None
        return self._context

    def _module(
        self,
        *,
        client: _ClientModule,
        module_name: str,
    ) -> tuple[StubSignature, ...]:
        """Load one module's signatures through the client.

        Args:
            client (_ClientModule): The imported ``typeshed_client`` module.
            module_name (str): Dotted module name.

        Returns:
            tuple[StubSignature, ...]: Its signatures, cached; empty on any
                failure.

        """
        if module_name in self._modules:
            return self._modules[module_name]
        signatures: tuple[StubSignature, ...] = ()
        context: _OpaqueContext | None = self._context_for(client=client)
        if context is not None:
            try:
                path: Path | None = client.get_stub_file(
                    module_name=module_name,
                    search_context=context,
                )
            except Constants.client_errors:
                path = None
            if path is not None and path.is_file():
                signatures = TypeshedClientIndex._parse(
                    path=path,
                    module_name=module_name,
                )
        self._modules[module_name] = signatures
        return signatures

    @staticmethod
    def _parse(
        *,
        path: Path,
        module_name: str,
    ) -> tuple[StubSignature, ...]:
        """Read and extract signatures from one stub file.

        Args:
            path (Path): Stub file path.
            module_name (str): Dotted module name it provides.

        Returns:
            tuple[StubSignature, ...]: The declared signatures, empty when
                unreadable.

        """
        try:
            data: bytes = path.read_bytes()
        except OSError:
            return ()
        if len(data) > Constants.max_stub_bytes:
            return ()
        return stub_signatures(
            source=data.decode(encoding="utf-8", errors="replace"),
            module_name=module_name,
            chosen=str(object=path),
        )
