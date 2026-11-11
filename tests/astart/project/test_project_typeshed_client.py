"""Verify the optional ``typeshed_client`` project-mode backend."""

from __future__ import annotations

from sys import modules
from types import SimpleNamespace
from typing import TYPE_CHECKING, Final

from astart.project.libraries import LibraryIndex
from astart.project.typeshed_client import (
    ClientConfig,
    TypeshedClientIndex,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from astart.semantic.stubs import StubSignature

_STUB: Final[str] = """\
def send(url: str) -> int: ...
class Session:
    def send(self, url: str) -> int: ...
"""


def _fake_client(*, monkeypatch: pytest.MonkeyPatch, stub: Path) -> None:
    """Install a fake ``typeshed_client`` module.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.
        stub (Path): Stub file the fake resolves ``fakelib`` to.

    """
    module: SimpleNamespace = SimpleNamespace()

    def get_search_context(**_kwargs: object) -> object:
        """Return an opaque context for the fake client.

        Args:
            _kwargs (object): Search settings forwarded by the adapter.

        Returns:
            object: A fresh opaque context object.

        """
        return object()

    def get_stub_file(
        module_name: str,
        *,
        search_context: object,
    ) -> Path | None:
        """Resolve ``fakelib`` to the fixture stub path.

        Args:
            module_name (str): Dotted module name requested.
            search_context (object): Context returned by ``get_search_context``
                .

        Returns:
            Path | None: The fixture stub path for ``fakelib``, else ``None``.

        """
        _ = search_context
        return stub if module_name == "fakelib" else None

    module.get_search_context = get_search_context
    module.get_stub_file = get_stub_file
    monkeypatch.setitem(dic=modules, name="typeshed_client", value=module)


def test_lookup_resolves_stub_names(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check dotted names resolve through the fake client.

    Args:
        tmp_path (Path): Scratch directory.
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    stub: Path = tmp_path / "fakelib.pyi"
    stub.write_text(data=_STUB, encoding="utf-8")
    _fake_client(monkeypatch=monkeypatch, stub=stub)
    index: TypeshedClientIndex = TypeshedClientIndex()
    expect_true(condition=index.available())
    signatures: tuple[StubSignature, ...] = index.lookup(
        qualified_name="fakelib.send",
    )
    expect_equal(actual=len(signatures), expected=1)
    expect_equal(
        actual=signatures[0].qualified_name,
        expected="fakelib.send",
    )
    method: tuple[StubSignature, ...] = index.lookup(
        qualified_name="fakelib.Session.send",
    )
    expect_equal(actual=len(method), expected=1)
    expect_equal(
        actual=index.lookup(qualified_name="fakelib.missing"),
        expected=(),
    )
    expect_equal(actual=index.lookup(qualified_name="other.mod"), expected=())


def test_lookup_is_empty_without_the_package(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check the index reports unavailable and answers empty.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    monkeypatch.setitem(dic=modules, name="typeshed_client", value=None)
    index: TypeshedClientIndex = TypeshedClientIndex()
    expect_false(condition=index.available())
    expect_equal(
        actual=index.lookup(qualified_name="fakelib.send"),
        expected=(),
    )


def test_lookup_survives_client_errors(
    *,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check client failures degrade to empty results.

    Args:
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    module: SimpleNamespace = SimpleNamespace()

    def get_search_context(**_kwargs: object) -> object:
        """Raise to exercise the adapter's client-error fallback.

        Args:
            _kwargs (object): Search settings forwarded by the adapter.

        Returns:
            Never returns; always raises ``OSError``.

        Raises:
            OSError: Always, to exercise the fallback path.

        """
        raise OSError

    module.get_search_context = get_search_context
    monkeypatch.setitem(dic=modules, name="typeshed_client", value=module)
    index: TypeshedClientIndex = TypeshedClientIndex()
    expect_true(condition=index.available())
    expect_equal(
        actual=index.lookup(qualified_name="fakelib.send"),
        expected=(),
    )


def test_library_index_consults_client_first(
    *,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Check ``LibraryIndex`` prefers the client and falls back.

    Args:
        tmp_path (Path): Scratch directory.
        monkeypatch (pytest.MonkeyPatch): Pytest monkeypatch fixture.

    """
    stub: Path = tmp_path / "fakelib.pyi"
    stub.write_text(data=_STUB, encoding="utf-8")
    _fake_client(monkeypatch=monkeypatch, stub=stub)
    client: TypeshedClientIndex = TypeshedClientIndex()
    index: LibraryIndex = LibraryIndex(client=client)
    expect_equal(
        actual=len(index.lookup(qualified_name="fakelib.send")),
        expected=1,
    )
    expect_equal(actual=index.lookup(qualified_name="os.getcwd"), expected=())
    config_index: TypeshedClientIndex = TypeshedClientIndex(
        config=ClientConfig(version=(3, 12), platform="linux"),
    )
    expect_true(condition=config_index.available())
