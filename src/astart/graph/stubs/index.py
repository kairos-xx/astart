"""Lazy stub/import graph index API."""

from __future__ import annotations

from ast import (
    AnnAssign,
    AsyncFunctionDef,
    ClassDef,
    FunctionDef,
    ImportFrom,
    Module,
    Name,
    alias,
    arg,
    parse,
    stmt,
    unparse,
)
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from zipfile import ZipFile


class StubMemberKind(StrEnum):
    """Kinds of members parsed from stub files.

    Attributes:
        ATTRIBUTE: Attribute associated with this instance.
        CLASS: Class associated with this instance.
        FUNCTION: Function associated with this instance.
        IMPORT: Import associated with this instance.
        METHOD: Method associated with this instance.

    """

    ATTRIBUTE = "attribute"
    CLASS = "class"
    FUNCTION = "function"
    IMPORT = "import"
    METHOD = "method"


@dataclass(frozen=True, slots=True)
class StubLookupResult:
    """Result of looking up a name in bundled stubs.

    Attributes:
        found (bool): Found retained as bool by this instance.
        qualified_name (str): Identifier used to refer to the qualified.
        source_path (str): Path to the source used by this instance.

    """

    qualified_name: str
    source_path: str
    found: bool


@dataclass(frozen=True, slots=True)
class StubParameter:
    """A parameter parsed from a stub callable.

    Attributes:
        annotation (str | None): Annotation retained as str | None by this
            instance.
        has_default (bool): Has default retained as bool by this instance.
        name (str): Identifier used to refer to the name.

    """

    name: str
    annotation: str | None
    has_default: bool


@dataclass(frozen=True, slots=True)
class StubMember:
    """A class/function/attribute fact parsed lazily from stubs.

    Attributes:
        bases (tuple[str, ...]): Bases retained as tuple[str, ...] by this
            instance.
        kind (StubMemberKind): Kind retained as StubMemberKind by this
            instance.
        parameters (tuple[StubParameter, ...]): Parameters retained as
            tuple[StubParameter, ...] by this instance.
        qualified_name (str): Identifier used to refer to the qualified.
        returns (str | None): Returns retained as str | None by this instance.
        source_path (str): Path to the source used by this instance.

    """

    qualified_name: str
    kind: StubMemberKind
    source_path: str
    parameters: tuple[StubParameter, ...] = ()
    returns: str | None = None
    bases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StubModule:
    """Parsed stub module facts.

    Attributes:
        members (tuple[StubMember, ...]): Members retained as tuple[StubMember,
            ...] by this instance.
        module_name (str): Identifier used to refer to the module.
        source_path (str): Path to the source used by this instance.

    """

    module_name: str
    source_path: str
    members: tuple[StubMember, ...]

    def members_named(self, *, name: str) -> tuple[StubMember, ...]:
        """Return members with a matching final component.

        Args:
            name (str): Identifier of the name being resolved.

        Returns:
            tuple[StubMember, ...]: tuple[StubMember, ...] produced by this
                operation.

        """
        suffix: str = f".{name}"
        return tuple(
            member
            for member in self.members
            if member.qualified_name == name
            or member.qualified_name.endswith(suffix)
        )


@dataclass(slots=True)
class LazyStubIndex:
    """Lazy index over a typeshed folder or archive.

    Attributes:
        lookup_cache (dict[str, StubLookupResult]): Lookup results already
            resolved by qualified name.
        root (Path): Path to the root used by this instance.
        _module_cache (dict[str, StubModule | None]): TODO.
        _archive_names (frozenset[str] | None): TODO.

    """

    root: Path
    lookup_cache: dict[str, StubLookupResult] = field(default_factory=dict)
    _module_cache: dict[str, StubModule | None] = field(default_factory=dict)
    _archive_names: frozenset[str] | None = None

    @classmethod
    def from_path(cls, *, path: Path) -> LazyStubIndex:
        """Create a lazy stub index from a path.

        Args:
            path (Path): Filesystem path identifying the path.

        Returns:
            LazyStubIndex: LazyStubIndex produced by this operation.

        """
        return cls(root=path)

    def lookup(self, *, qualified_name: str) -> StubLookupResult:
        """Look up a qualified name without eagerly parsing all stubs.

        Args:
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            StubLookupResult: StubLookupResult produced by this operation.

        """
        cached: StubLookupResult | None = self.lookup_cache.get(
            qualified_name,
        )
        if cached is not None:
            return cached
        result: StubLookupResult = self._lookup_uncached(
            qualified_name=qualified_name,
        )
        self.lookup_cache[qualified_name] = result
        return result

    def load_module(self, *, module_name: str) -> StubModule | None:
        """Parse and cache a stub module on demand.

        Args:
            module_name (str): Identifier of the module being resolved.

        Returns:
            StubModule | None: StubModule | None produced by this operation.

        """
        cached: StubModule | None
        cached = self._module_cache.get(module_name)
        if cached is not None or module_name in self._module_cache:
            return cached
        lookup: StubLookupResult = self.lookup(qualified_name=module_name)
        if not lookup.found:
            self._module_cache[module_name] = None
            return None
        source: str | None = self.read_stub_source(path=lookup.source_path)
        if source is None:
            self._module_cache[module_name] = None
            return None
        parsed: Module = parse(source=source, filename=lookup.source_path)
        module: StubModule = StubModule(
            module_name=module_name,
            source_path=lookup.source_path,
            members=tuple(
                _members_from_module(
                    module=parsed,
                    module_name=module_name,
                    source_path=lookup.source_path,
                ),
            ),
        )
        self._module_cache[module_name] = module
        return module

    def lookup_member(self, *, qualified_name: str) -> tuple[StubMember, ...]:
        """Look up parsed members for a qualified symbol.

        Args:
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            tuple[StubMember, ...]: tuple[StubMember, ...] produced by this
                operation.

        """
        module_name: str = qualified_name.split(sep=".", maxsplit=1)[0]
        module: StubModule | None = self.load_module(module_name=module_name)
        if module is None:
            return ()
        return tuple(
            member
            for member in module.members
            if member.qualified_name == qualified_name
        )

    def read_stub_source(self, *, path: str) -> str | None:
        """Read stub source from a directory or archive.

        Args:
            path (str): Filesystem path identifying the path.

        Returns:
            str | None: str | None produced by this operation.

        """
        if self.root.is_file():
            with ZipFile(file=self.root, mode="r") as archive:
                if path not in archive.namelist():
                    return None
                return archive.read(name=path).decode(encoding="utf-8")
        candidate: Path = Path(path)
        if not candidate.exists():
            return None
        return candidate.read_text(encoding="utf-8")

    def _lookup_uncached(self, *, qualified_name: str) -> StubLookupResult:
        """Look up a qualified name without consulting the cache.

        Args:
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            StubLookupResult: StubLookupResult produced by this operation.

        """
        module_name: str = qualified_name.split(sep=".", maxsplit=1)[0]
        if self.root.is_file():
            return self._lookup_archive(
                module_name=module_name,
                qualified_name=qualified_name,
            )
        return self._lookup_directory(
            module_name=module_name,
            qualified_name=qualified_name,
        )

    def _lookup_directory(
        self,
        *,
        module_name: str,
        qualified_name: str,
    ) -> StubLookupResult:
        """Look up a module or package stub in a directory.

        Args:
            module_name (str): Identifier of the module being resolved.
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            StubLookupResult: StubLookupResult produced by this operation.

        """
        module_stub: Path = self.root / "stdlib" / f"{module_name}.pyi"
        package_stub: Path = (
            self.root / "stdlib" / module_name / "__init__.pyi"
        )
        if module_stub.exists():
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path=str(object=module_stub),
                found=True,
            )
        if package_stub.exists():
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path=str(object=package_stub),
                found=True,
            )
        return self._lookup_third_party(
            module_name=module_name,
            qualified_name=qualified_name,
        )

    def _lookup_archive(
        self,
        *,
        module_name: str,
        qualified_name: str,
    ) -> StubLookupResult:
        """Look up a module or package stub in a zip archive.

        Args:
            module_name (str): Identifier of the module being resolved.
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            StubLookupResult: StubLookupResult produced by this operation.

        """
        module_candidate: str = f"typeshed/stdlib/{module_name}.pyi"
        package_candidate: str = f"typeshed/stdlib/{module_name}/__init__.pyi"
        names: frozenset[str] = self._archive_name_set()
        if module_candidate in names:
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path=module_candidate,
                found=True,
            )
        if package_candidate in names:
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path=package_candidate,
                found=True,
            )
        for candidate in sorted(names):
            if not candidate.startswith("typeshed/stubs/"):
                continue
            if candidate.endswith(
                (f"/{module_name}/__init__.pyi", f"/{module_name}.pyi"),
            ):
                return StubLookupResult(
                    qualified_name=qualified_name,
                    source_path=candidate,
                    found=True,
                )
        return StubLookupResult(
            qualified_name=qualified_name,
            source_path=package_candidate,
            found=False,
        )

    def _lookup_third_party(
        self,
        *,
        module_name: str,
        qualified_name: str,
    ) -> StubLookupResult:
        """Look up a module inside ``stubs/<dist>/`` directories.

        Args:
            module_name (str): Identifier of the module being resolved.
            qualified_name (str): Identifier of the qualified being resolved.

        Returns:
            StubLookupResult: StubLookupResult produced by this operation.

        """
        stubs: Path = self.root / "stubs"
        if not stubs.is_dir():
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path="",
                found=False,
            )
        try:
            distributions: list[Path] = sorted(stubs.iterdir())
        except OSError:
            return StubLookupResult(
                qualified_name=qualified_name,
                source_path="",
                found=False,
            )
        for distribution in distributions:
            if not distribution.is_dir():
                continue
            for candidate in (
                distribution / f"{module_name}.pyi",
                distribution / module_name / "__init__.pyi",
            ):
                if candidate.is_file():
                    return StubLookupResult(
                        qualified_name=qualified_name,
                        source_path=str(object=candidate),
                        found=True,
                    )
        return StubLookupResult(
            qualified_name=qualified_name,
            source_path="",
            found=False,
        )

    def _archive_name_set(self) -> frozenset[str]:
        """Return cached archive member names.

        Returns:
            frozenset[str]: frozenset[str] produced by this operation.

        """
        if self._archive_names is None:
            with ZipFile(file=self.root, mode="r") as archive:
                self._archive_names = frozenset(archive.namelist())
        return self._archive_names


def _members_from_module(
    *,
    module: Module,
    module_name: str,
    source_path: str,
) -> tuple[StubMember, ...]:
    """Extract module-level and class-level members from a stub AST.

    Args:
        module (Module): The module examined while extract module-level
            and class-level members from a stub AST.
        module_name (str): Identifier of the module being resolved.
        source_path (str): Filesystem path identifying the source.

    Returns:
        tuple[StubMember, ...]: tuple[StubMember, ...] produced by this
            operation.

    """
    members: list[StubMember] = []
    node: stmt | None = None
    for node in module.body:
        if isinstance(node, (FunctionDef, AsyncFunctionDef)):
            members.append(
                _callable_member(
                    node=node,
                    qualified_name=f"{module_name}.{node.name}",
                    kind=StubMemberKind.FUNCTION,
                    source_path=source_path,
                ),
            )
        elif isinstance(node, ClassDef):
            members.extend(
                _class_members(
                    node=node,
                    module_name=module_name,
                    source_path=source_path,
                ),
            )
        elif isinstance(node, AnnAssign) and isinstance(node.target, Name):
            members.append(
                StubMember(
                    qualified_name=f"{module_name}.{node.target.id}",
                    kind=StubMemberKind.ATTRIBUTE,
                    source_path=source_path,
                    returns=unparse(ast_obj=node.annotation),
                ),
            )
        elif isinstance(node, ImportFrom):
            import_alias: alias | None = None
            for import_alias in node.names:
                imported_name: str = import_alias.asname or import_alias.name
                members.append(
                    StubMember(
                        qualified_name=f"{module_name}.{imported_name}",
                        kind=StubMemberKind.IMPORT,
                        source_path=source_path,
                        returns=node.module,
                    ),
                )
    return tuple(members)


def _class_members(
    *,
    node: ClassDef,
    module_name: str,
    source_path: str,
) -> tuple[StubMember, ...]:
    """Extract a class and its immediate method/attribute members.

    Args:
        module_name (str): Identifier of the module being resolved.
        node (ClassDef): The node examined while extract a class and
            its immediate method/attribute members.
        source_path (str): Filesystem path identifying the source.

    Returns:
        tuple[StubMember, ...]: tuple[StubMember, ...] produced by this
            operation.

    """
    class_name: str = f"{module_name}.{node.name}"
    members: list[StubMember] = [
        StubMember(
            qualified_name=class_name,
            kind=StubMemberKind.CLASS,
            source_path=source_path,
            bases=tuple(unparse(ast_obj=base) for base in node.bases),
        ),
    ]
    child: stmt | None = None
    for child in node.body:
        if isinstance(child, (FunctionDef, AsyncFunctionDef)):
            members.append(
                _callable_member(
                    node=child,
                    qualified_name=f"{class_name}.{child.name}",
                    kind=StubMemberKind.METHOD,
                    source_path=source_path,
                ),
            )
        elif isinstance(child, AnnAssign) and isinstance(child.target, Name):
            members.append(
                StubMember(
                    qualified_name=f"{class_name}.{child.target.id}",
                    kind=StubMemberKind.ATTRIBUTE,
                    source_path=source_path,
                    returns=unparse(ast_obj=child.annotation),
                ),
            )
    return tuple(members)


def _callable_member(
    *,
    node: FunctionDef | AsyncFunctionDef,
    qualified_name: str,
    kind: StubMemberKind,
    source_path: str,
) -> StubMember:
    """Create a callable stub member.

    Args:
        kind (StubMemberKind): Kind supplied as StubMemberKind for this
            operation.
        node (FunctionDef | AsyncFunctionDef): The node examined while create a
            callable stub member.
        qualified_name (str): Identifier of the qualified being resolved.
        source_path (str): Filesystem path identifying the source.

    Returns:
        StubMember: StubMember produced by this operation.

    """
    parameters: list[StubParameter] = [
        _parameter_from_arg(parameter=parameter)
        for parameter in (*node.args.posonlyargs, *node.args.args)
    ]
    if node.args.vararg is not None:
        parameters.append(_parameter_from_arg(parameter=node.args.vararg))
    parameters.extend(
        _parameter_from_arg(parameter=parameter)
        for parameter in node.args.kwonlyargs
    )
    if node.args.kwarg is not None:
        parameters.append(_parameter_from_arg(parameter=node.args.kwarg))
    return StubMember(
        qualified_name=qualified_name,
        kind=kind,
        source_path=source_path,
        parameters=tuple(parameters),
        returns=(
            unparse(ast_obj=node.returns) if node.returns is not None else None
        ),
    )


def _parameter_from_arg(*, parameter: arg) -> StubParameter:
    """Create a stub parameter from an AST argument.

    Args:
        parameter (arg): Parameter supplied as arg for this operation.

    Returns:
        StubParameter: StubParameter produced by this operation.

    """
    return StubParameter(
        name=parameter.arg,
        annotation=(
            unparse(ast_obj=parameter.annotation)
            if parameter.annotation is not None
            else None
        ),
        has_default=False,
    )
