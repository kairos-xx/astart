"""Exercise lazy stub lookup against directory and archive roots."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, final
from zipfile import ZipFile

from astart.graph.stubs.index import (
    LazyStubIndex,
    StubLookupResult,
    StubMember,
    StubMemberKind,
    StubModule,
)

from tests.support.expectations import (
    expect_equal,
    expect_false,
    expect_in,
    expect_is,
    expect_not_none,
    expect_true,
)

if TYPE_CHECKING:
    from pathlib import Path


@final
class Constants:
    """Group module-level constants.

    Attributes:
        stub_source (Final[str]): Grouped module constant.

    """

    stub_source: Final[str] = """\
from os import path as p, sep
from typing import Any

version: str

def top(a: int, /, b: str, *args: float, c: bytes, **kw: Any) -> bool: ...
async def go(x) -> None: ...

class Thing(Base, Mixin):
    attr: int
    def method(self, value: int) -> str: ...
    async def amethod(self) -> None: ...
    other = 3
"""


def _write_directory_stubs(*, root: Path) -> None:
    """Create a directory-layout stub tree.

    Args:
        root (Path): Directory receiving the stubs.

    """
    stdlib: Path = root / "stdlib"
    (stdlib / "pkg").mkdir(parents=True)
    (stdlib / "demo.pyi").write_text(
        data=Constants.stub_source,
        encoding="utf-8",
    )
    (stdlib / "pkg" / "__init__.pyi").write_text(
        data="""\
value: int
""",
        encoding="utf-8",
    )


def test_directory_lookup_finds_modules_and_packages(
    *,
    tmp_path: Path,
) -> None:
    """Resolve module and package stubs and cache each answer.

    Args:
        tmp_path (Path): Temporary directory for the stub tree.

    """
    _write_directory_stubs(root=tmp_path)
    index: LazyStubIndex = LazyStubIndex.from_path(path=tmp_path)
    module: StubLookupResult = index.lookup(qualified_name="demo.top")
    package: StubLookupResult = index.lookup(qualified_name="pkg.value")
    missing: StubLookupResult = index.lookup(qualified_name="absent.name")
    expect_true(condition=module.found)
    expect_true(condition=package.found)
    expect_false(condition=missing.found)
    expect_is(actual=index.lookup(qualified_name="demo.top"), expected=module)


def test_load_module_extracts_members(*, tmp_path: Path) -> None:
    """Extract functions, classes, attributes and imports from a stub.

    Args:
        tmp_path (Path): Temporary directory for the stub tree.

    """
    _write_directory_stubs(root=tmp_path)
    index: LazyStubIndex = LazyStubIndex.from_path(path=tmp_path)
    module: StubModule = expect_not_none(
        value=index.load_module(module_name="demo"),
    )
    expect_is(actual=index.load_module(module_name="demo"), expected=module)
    kinds: dict[str, StubMemberKind] = {
        member.qualified_name: member.kind for member in module.members
    }
    expect_equal(actual=kinds["demo.top"], expected=StubMemberKind.FUNCTION)
    expect_equal(actual=kinds["demo.go"], expected=StubMemberKind.FUNCTION)
    expect_equal(actual=kinds["demo.Thing"], expected=StubMemberKind.CLASS)
    expect_equal(
        actual=kinds["demo.Thing.method"],
        expected=StubMemberKind.METHOD,
    )
    expect_equal(
        actual=kinds["demo.Thing.attr"],
        expected=StubMemberKind.ATTRIBUTE,
    )
    expect_equal(
        actual=kinds["demo.version"],
        expected=StubMemberKind.ATTRIBUTE,
    )
    expect_equal(actual=kinds["demo.p"], expected=StubMemberKind.IMPORT)
    expect_equal(actual=kinds["demo.sep"], expected=StubMemberKind.IMPORT)
    top: StubMember = module.members_named(name="top")[0]
    expect_equal(
        actual=tuple(parameter.name for parameter in top.parameters),
        expected=("a", "b", "args", "c", "kw"),
    )
    expect_equal(actual=top.returns, expected="bool")
    thing: StubMember = module.members_named(name="demo.Thing")[0]
    expect_equal(actual=thing.bases, expected=("Base", "Mixin"))
    expect_in(
        item="demo.Thing.method",
        container=[
            m.qualified_name for m in module.members_named(name="method")
        ],
    )


def test_load_module_reports_missing_stub(*, tmp_path: Path) -> None:
    """Cache a missing result for modules without stubs.

    Args:
        tmp_path (Path): Temporary directory for the stub tree.

    """
    _write_directory_stubs(root=tmp_path)
    index: LazyStubIndex = LazyStubIndex.from_path(path=tmp_path)
    expect_is(actual=index.load_module(module_name="absent"), expected=None)
    expect_is(actual=index.load_module(module_name="absent"), expected=None)
    expect_equal(
        actual=index.lookup_member(qualified_name="absent.x"),
        expected=(),
    )
    members: tuple[StubMember, ...] = index.lookup_member(
        qualified_name="demo.top",
    )
    expect_equal(actual=len(members), expected=1)


def test_load_module_handles_vanished_directory_source(
    *,
    tmp_path: Path,
) -> None:
    """Return no module when a found stub disappears before it is read.

    Args:
        tmp_path (Path): Temporary directory for the stub tree.

    """
    _write_directory_stubs(root=tmp_path)
    index: LazyStubIndex = LazyStubIndex.from_path(path=tmp_path)
    expect_true(condition=index.lookup(qualified_name="demo").found)
    (tmp_path / "stdlib" / "demo.pyi").unlink()
    expect_is(actual=index.load_module(module_name="demo"), expected=None)


def test_archive_lookup_reads_zip_roots(*, tmp_path: Path) -> None:
    """Resolve stubs stored inside a typeshed-style zip archive.

    Args:
        tmp_path (Path): Temporary directory for the archive.

    """
    archive: Path = tmp_path / "typeshed.zip"
    with ZipFile(file=archive, mode="w") as handle:
        handle.writestr(
            zinfo_or_arcname="typeshed/stdlib/demo.pyi",
            data=Constants.stub_source,
        )
        handle.writestr(
            zinfo_or_arcname="typeshed/stdlib/pkg/__init__.pyi",
            data="""\
value: int
""",
        )
    index: LazyStubIndex = LazyStubIndex.from_path(path=archive)
    expect_true(condition=index.lookup(qualified_name="demo.top").found)
    expect_true(condition=index.lookup(qualified_name="pkg.value").found)
    expect_false(condition=index.lookup(qualified_name="absent.x").found)
    module: StubModule = expect_not_none(
        value=index.load_module(module_name="pkg"),
    )
    expect_equal(actual=module.members[0].qualified_name, expected="pkg.value")
    expect_is(actual=index.load_module(module_name="absent"), expected=None)
    index.lookup_cache.clear()
    result: StubLookupResult = index.lookup(qualified_name="demo")
    expect_is(
        actual=index.read_stub_source(path="typeshed/stdlib/none.pyi"),
        expected=None,
    )
    expect_true(condition=result.found)
